#!/usr/bin/env python3
"""
Crawl DP-600 and DP-700 exam discussion questions from examtopics.com.

Outputs (default: current working directory; use --output-dir to change):
  - dp-600.jsonl / dp-700.jsonl (line-delimited JSON, one question per line)
  - dp-600.json / dp-700.json (consolidated JSON arrays, written at the end)
  - state.json (checkpoint/resume state)

Usage (from repo root):
    python scripts/crawl_fabric_discussions.py --output-dir data

Politeness:
  - Honest user-agent
  - Max concurrent requests limited
  - Delay between requests
  - Retries with exponential backoff
  - Respects robots.txt (target paths are not disallowed)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.examtopics.com"
LIST_URL = BASE_URL + "/discussions/microsoft/{page}/"
DISCUSSION_RE = re.compile(
    r"/discussions/microsoft/view/(?P<id>\d+)-exam-(?P<exam>dp-[67]00)-topic-(?P<topic>\d+)-question-(?P<qnum>\d+)-discussion/"
)

TARGET_EXAMS = {"dp-600", "dp-700"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("crawler")


@dataclass
class Comment:
    comment_id: str
    author: str
    date_title: str
    text: str
    upvotes: int
    badges: list[str] = field(default_factory=list)
    selected_answer: str | None = None
    is_reply: bool = False
    parent_id: str | None = None


@dataclass
class Choice:
    letter: str
    text: str
    correct: bool = False


@dataclass
class Question:
    discussion_id: str
    exam: str
    topic: int
    question_number: int
    question_id: str
    question_text: str
    choices: list[Choice] = field(default_factory=list)
    correct_answers: list[str] = field(default_factory=list)
    voted_answers_tally: list[dict[str, Any]] = field(default_factory=list)
    most_voted_answer: str | None = None
    comments: list[Comment] = field(default_factory=list)
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "discussion_id": self.discussion_id,
            "exam": self.exam,
            "topic": self.topic,
            "question_number": self.question_number,
            "question_id": self.question_id,
            "question_text": self.question_text,
            "choices": [asdict(c) for c in self.choices],
            "correct_answers": self.correct_answers,
            "voted_answers_tally": self.voted_answers_tally,
            "most_voted_answer": self.most_voted_answer,
            "comments": [asdict(c) for c in self.comments],
            "url": self.url,
        }


class Crawler:
    def __init__(
        self,
        output_dir: Path,
        max_concurrent: int = 3,
        delay: tuple[float, float] = (1.2, 2.0),
        max_retries: int = 4,
        timeout: int = 45,
    ) -> None:
        self.output_dir = output_dir
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.state_path = output_dir / "state.json"
        self.state: dict[str, Any] = self._load_state()
        self.client: httpx.AsyncClient | None = None
        self.sem = asyncio.Semaphore(max_concurrent)

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                # JSON cannot serialize sets; restore them here
                data["list_pages_completed"] = set(data.get("list_pages_completed", []))
                data["urls_processed"] = set(data.get("urls_processed", []))
                return data
            except Exception as e:
                logger.warning("Could not load state file: %s", e)
        return {
            "list_pages_completed": set(),
            "urls_collected": {},  # exam -> list of dicts
            "urls_processed": set(),
            "errors": {},
        }

    def _save_state(self) -> None:
        # Convert sets to lists for JSON serialization
        serializable = {
            "list_pages_completed": sorted(self.state["list_pages_completed"]),
            "urls_collected": {
                exam: sorted(urls, key=lambda x: (x["topic"], x["qnum"], x["id"]))
                for exam, urls in self.state["urls_collected"].items()
            },
            "urls_processed": sorted(self.state["urls_processed"]),
            "errors": self.state["errors"],
        }
        self.state_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    async def _sleep_jitter(self) -> None:
        await asyncio.sleep(random.uniform(self.delay[0], self.delay[1]))

    async def _fetch(self, url: str, retries: int | None = None) -> str:
        if self.client is None:
            raise RuntimeError("HTTP client not initialized")
        retries = retries if retries is not None else self.max_retries
        last_err: Exception | None = None
        for attempt in range(retries):
            async with self.sem:
                await self._sleep_jitter()
                try:
                    resp = await self.client.get(
                        url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (compatible; FabricExamCrawler/1.0; "
                                "+https://example.com/bot)"
                            ),
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.5",
                            "DNT": "1",
                            "Connection": "keep-alive",
                        },
                        follow_redirects=True,
                    )
                    if resp.status_code == 200:
                        return resp.text
                    if resp.status_code in (403, 429, 503, 502, 504):
                        logger.warning("HTTP %d for %s (attempt %d)", resp.status_code, url, attempt + 1)
                        last_err = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code}", request=resp.request, response=resp
                        )
                        await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                    else:
                        resp.raise_for_status()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_err = e
                    logger.warning("Fetch error for %s (attempt %d): %s", url, attempt + 1, e)
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
        raise last_err or RuntimeError(f"Failed to fetch {url}")

    def _parse_discussion_html(self, html: str, url: str, meta: dict[str, Any]) -> Question:
        soup = BeautifulSoup(html, "html.parser")

        q_body = soup.find("div", class_="question-body")
        question_id = str(q_body.get("data-id", "")) if q_body else ""
        question_text = ""
        if q_body:
            p = q_body.find("p", class_="card-text")
            if p:
                question_text = p.get_text(separator="\n", strip=True)

        choices: list[Choice] = []
        correct_answers: list[str] = []
        choices_container = soup.find("div", class_="question-choices-container")
        if choices_container:
            for li in choices_container.find_all("li", class_="multi-choice-item"):
                letter_span = li.find("span", class_="multi-choice-letter")
                letter = str(letter_span.get("data-choice-letter", "")) if letter_span else ""
                text = li.get_text(strip=True)
                # Remove leading letter prefix like "A." from text
                text = re.sub(r"^[A-Z]\.\s*", "", text).strip()
                correct = "correct-hidden" in (li.get("class") or [])
                choices.append(Choice(letter=letter, text=text, correct=correct))
                if correct:
                    correct_answers.append(letter)

        voted_tally: list[dict[str, Any]] = []
        most_voted: str | None = None
        tally_div = soup.find("div", class_="voted-answers-tally")
        if tally_div:
            script = tally_div.find("script", type="application/json")
            if script:
                try:
                    voted_tally = json.loads(script.string or "[]")
                    for item in voted_tally:
                        if item.get("is_most_voted"):
                            most_voted = item.get("voted_answers")
                            break
                except json.JSONDecodeError as e:
                    logger.warning("Could not parse voted answers tally: %s", e)

        question = Question(
            discussion_id=meta["id"],
            exam=meta["exam"],
            topic=meta["topic"],
            question_number=meta["qnum"],
            question_id=question_id,
            question_text=question_text,
            choices=choices,
            correct_answers=correct_answers,
            voted_answers_tally=voted_tally,
            most_voted_answer=most_voted,
            url=url,
        )

        question.comments = self._parse_comments(soup)
        return question

    def _parse_comments(self, soup: BeautifulSoup) -> list[Comment]:
        comments: list[Comment] = []
        for c in soup.find_all("div", class_="comment-container"):
            comment_id = str(c.get("data-comment-id", ""))
            user_el = c.find("h5", class_="comment-username")
            author = user_el.get_text(strip=True) if user_el else ""
            date_el = c.find("span", class_="comment-date")
            date_title = str(date_el.get("title", "")) if date_el else ""
            content_el = c.find("div", class_="comment-content")
            text = content_el.get_text(separator="\n", strip=True) if content_el else ""
            upvote_el = c.find("span", class_="upvote-count")
            upvotes = 0
            if upvote_el:
                try:
                    upvotes = int(upvote_el.get_text(strip=True))
                except ValueError:
                    pass
            badges = [b.get_text(strip=True) for b in c.find_all("span", class_="badge")]

            # Some comments explicitly state "Selected Answer: X"
            selected_answer = None
            selected_match = re.search(r"Selected Answer:\s*([A-Z]+)", text, re.IGNORECASE)
            if selected_match:
                selected_answer = selected_match.group(1)

            comments.append(
                Comment(
                    comment_id=comment_id,
                    author=author,
                    date_title=date_title,
                    text=text,
                    upvotes=upvotes,
                    badges=badges,
                    selected_answer=selected_answer,
                )
            )
        return comments

    async def _crawl_discussion(self, meta: dict[str, Any]) -> Question | None:
        url = f"{BASE_URL}{meta['path']}"
        try:
            html = await self._fetch(url)
            question = self._parse_discussion_html(html, url, meta)

            # Load full discussion if paginated
            load_more = BeautifulSoup(html, "html.parser").find("div", class_="load-more-section")
            if load_more:
                discussion_id = load_more.get("data-discussion-id", meta["id"])
                ajax_url = f"{BASE_URL}/ajax/discussion/load-complete/?discussion-id={discussion_id}"
                try:
                    full_html = await self._fetch(ajax_url)
                    full_soup = BeautifulSoup(full_html, "html.parser")
                    question.comments = self._parse_comments(full_soup)
                except Exception as e:
                    logger.warning("Could not load full discussion for %s: %s", url, e)

            return question
        except Exception as e:
            logger.error("Error crawling discussion %s: %s", url, e)
            self.state["errors"][url] = str(e)
            return None

    async def _crawl_list_page(self, page: int) -> tuple[dict[str, list[dict[str, Any]]], int | None]:
        url = LIST_URL.format(page=page)
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")

        found: dict[str, list[dict[str, Any]]] = {exam: [] for exam in TARGET_EXAMS}
        for a in soup.find_all("a", href=DISCUSSION_RE):
            href = str(a.get("href", ""))
            m = DISCUSSION_RE.match(href)
            if not m:
                continue
            exam = m.group("exam")
            if exam not in TARGET_EXAMS:
                continue
            meta = {
                "id": m.group("id"),
                "exam": exam,
                "topic": int(m.group("topic")),
                "qnum": int(m.group("qnum")),
                "path": href,
                "title": a.get_text(strip=True),
            }
            found[exam].append(meta)

        # Detect last page from pagination indicator
        last_page = None
        page_indicator = soup.find("span", class_="discussion-list-page-indicator")
        if page_indicator:
            m = re.search(r"of\s+<strong>(\d+)</strong>", str(page_indicator))
            if m:
                last_page = int(m.group(1))

        return found, last_page

    async def discover_urls(self, max_pages: int | None = None) -> int:
        logger.info("Phase 1: Discovering discussion URLs...")
        last_page = None
        start_page = 1

        # If we already know total pages from a prior run, respect max_pages override
        if self.state.get("total_list_pages"):
            last_page = self.state["total_list_pages"]

        page = start_page
        while True:
            if max_pages is not None and page > max_pages:
                logger.info("Reached max_pages limit: %d", max_pages)
                break
            if last_page is not None and page > last_page:
                break
            if page in self.state["list_pages_completed"]:
                page += 1
                continue

            logger.info("Crawling discussion list page %d%s", page, f"/{last_page}" if last_page else "")
            try:
                found, detected_last = await self._crawl_list_page(page)
                if detected_last and last_page is None:
                    last_page = detected_last
                    self.state["total_list_pages"] = last_page
                    logger.info("Detected total discussion list pages: %d", last_page)

                for exam, urls in found.items():
                    existing = {u["path"] for u in self.state["urls_collected"].get(exam, [])}
                    new_urls = [u for u in urls if u["path"] not in existing]
                    if new_urls:
                        self.state["urls_collected"].setdefault(exam, []).extend(new_urls)
                        logger.info("Page %d: found %d new %s URLs", page, len(new_urls), exam.upper())

                self.state["list_pages_completed"].add(page)
                self._save_state()
                page += 1
            except Exception as e:
                logger.error("Error on list page %d: %s", page, e)
                self._save_state()
                raise

        total = sum(len(v) for v in self.state["urls_collected"].values())
        logger.info("Discovery complete. Total URLs collected: %d", total)
        for exam, urls in self.state["urls_collected"].items():
            logger.info("  %s: %d", exam.upper(), len(urls))
        return total

    async def crawl_discussions(self) -> dict[str, list[dict[str, Any]]]:
        logger.info("Phase 2: Crawling individual discussions...")
        results: dict[str, list[dict[str, Any]]] = {exam: [] for exam in TARGET_EXAMS}

        tasks = []
        for exam, urls in self.state["urls_collected"].items():
            for meta in urls:
                if meta["path"] in self.state["urls_processed"]:
                    continue
                tasks.append((exam, meta))

        if not tasks:
            logger.info("No new discussions to crawl.")
            return results

        logger.info("Discussions to crawl: %d", len(tasks))

        # Process in batches to allow periodic state saves
        batch_size = 20
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]
            coros = [self._crawl_discussion(meta) for _, meta in batch]
            questions = await asyncio.gather(*coros)

            for (exam, meta), q in zip(batch, questions):
                if q is None:
                    continue
                results[exam].append(q.to_dict())
                self.state["urls_processed"].add(meta["path"])
                # Append to JSONL immediately
                jsonl_path = self.output_dir / f"{exam}.jsonl"
                with jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(q.to_dict(), ensure_ascii=False) + "\n")

            self._save_state()
            logger.info("Completed batch %d/%d (%d discussions)", i // batch_size + 1, (len(tasks) + batch_size - 1) // batch_size, len(batch))

        return results

    def consolidate_json(self) -> None:
        for exam in TARGET_EXAMS:
            jsonl_path = self.output_dir / f"{exam}.jsonl"
            json_path = self.output_dir / f"{exam}.json"
            if not jsonl_path.exists():
                continue
            records = []
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            # Sort by topic then question number for readability
            records.sort(key=lambda r: (r.get("topic", 0), r.get("question_number", 0)))
            json_path.write_text(
                json.dumps(records, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Wrote %s with %d records", json_path.name, len(records))

    async def run(self, max_list_pages: int | None = None) -> None:
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        timeout = httpx.Timeout(self.timeout, connect=15)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            self.client = client
            await self.discover_urls(max_pages=max_list_pages)
            await self.crawl_discussions()
            self.consolidate_json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl DP-600/DP-700 discussions from examtopics.com")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Output directory")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent requests")
    parser.add_argument("--delay", type=float, nargs=2, default=[1.2, 2.0], help="Min/max delay seconds")
    parser.add_argument("--max-list-pages", type=int, default=None, help="Limit list pages for testing")
    parser.add_argument("--max-retries", type=int, default=4, help="Max retries per request")
    parser.add_argument("--reset", action="store_true", help="Delete state and output files and restart")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.reset:
        for p in [
            args.output_dir / "state.json",
            args.output_dir / "dp-600.jsonl",
            args.output_dir / "dp-600.json",
            args.output_dir / "dp-700.jsonl",
            args.output_dir / "dp-700.json",
        ]:
            if p.exists():
                p.unlink()
                logger.info("Removed %s", p)

    crawler = Crawler(
        output_dir=args.output_dir,
        max_concurrent=args.max_concurrent,
        delay=tuple(args.delay),
        max_retries=args.max_retries,
    )
    try:
        asyncio.run(crawler.run(max_list_pages=args.max_list_pages))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. State saved for resume.")
        crawler._save_state()
        raise


if __name__ == "__main__":
    main()
