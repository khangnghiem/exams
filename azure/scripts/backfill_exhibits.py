#!/usr/bin/env python3
"""
Backfill exhibit metadata (images, tables, code blocks) into existing
``data/dp-600.json`` and ``data/dp-700.json`` JSON files.

For every question that has a ``url`` field we re-fetch the discussion page,
extract ``raw_html``, exhibit metadata (and download images), and write the
updated JSON in place. A ``.bak`` snapshot is created before any mutation so
the operation can be safely re-run or rolled back.

Usage (from repo root):

    # Quick sanity check on 5 questions per exam:
    python scripts/backfill_exhibits.py --sample 5

    # Full run:
    python scripts/backfill_exhibits.py

Politeness is identical to the crawler: honest UA, max-concurrent requests,
jittered delay between page hits, exponential-backoff retries.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import shutil
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

# Allow `python scripts/backfill_exhibits.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_fabric_discussions import (  # noqa: E402
    PROJECT_ROOT,
    _extract_exhibits,
    infer_question_type,
)
from bs4 import BeautifulSoup  # noqa: E402

DEFAULT_DATA_FILES: list[str] = ["dp-600.json", "dp-700.json"]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; FabricExamCrawler/1.0; +https://example.com/bot)"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backfill")


def _backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        logger.info("Created backup: %s", bak)


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    # Write atomically so a crash mid-write doesn't leave a half-written file.
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _parse_discussion_for_exhibits(
    html: str, url: str, qid: str
) -> tuple[str, str, str]:
    """Pull raw HTML, plain question text, and question_type from a discussion page."""
    soup = BeautifulSoup(html, "html.parser")
    q_body = soup.find("div", class_="question-body")
    raw_html = ""
    question_text = ""
    if q_body:
        p = q_body.find("p", class_="card-text")
        if p:
            raw_html = str(p.decode_contents())
            question_text = p.get_text(separator="\n", strip=True)

    has_choices = bool(soup.find("div", class_="question-choices-container"))
    correct_answers: list[str] = []
    container = soup.find("div", class_="question-choices-container")
    if container:
        for li in container.find_all("li", class_="multi-choice-item"):
            if "correct-hidden" in (li.get("class") or []):
                ls = li.find("span", class_="multi-choice-letter")
                if ls:
                    correct_answers.append(str(ls.get("data-choice-letter", "")))

    qtype = infer_question_type(question_text, has_choices, correct_answers)
    return raw_html, question_text, qtype


async def _fetch_with_retries(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    url: str,
    *,
    user_agent: str,
    max_retries: int = 4,
) -> str:
    last_err: Exception | None = None
    for attempt in range(max_retries):
        async with sem:
            await asyncio.sleep(random.uniform(0.8, 1.6))
            try:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "DNT": "1",
                        "Connection": "keep-alive",
                    },
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in (403, 429, 502, 503, 504):
                    logger.warning(
                        "HTTP %d for %s (attempt %d)", resp.status_code, url, attempt + 1
                    )
                    last_err = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                    continue
                resp.raise_for_status()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_err = e
                logger.warning(
                    "Fetch error for %s (attempt %d): %s", url, attempt + 1, e
                )
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
    raise last_err or RuntimeError(f"Failed to fetch {url}")


async def _process_question(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    question: dict[str, Any],
    *,
    user_agent: str,
    exhibits_root: Path,
) -> dict[str, Any]:
    """Fetch + extract exhibits for a single question. Returns a stats dict."""
    url = question.get("url", "")
    stats = {
        "ok": False,
        "fetched": False,
        "skipped": False,
        "error": None,
        "question_type": question.get("question_type", "unknown"),
        "exhibit_kinds": Counter(),
        "n_exhibits": 0,
    }

    if not url:
        stats["skipped"] = True
        stats["error"] = "no url"
        return stats

    try:
        html = await _fetch_with_retries(client, sem, url, user_agent=user_agent)
        stats["fetched"] = True
    except Exception as e:
        stats["error"] = str(e)
        logger.warning("Could not fetch %s: %s", url, e)
        return stats

    try:
        raw_html, question_text, qtype = _parse_discussion_for_exhibits(
            html, url, qid=question.get("question_id", "")
        )
        question["raw_html"] = raw_html
        # Preserve existing question_text if already present and non-empty;
        # otherwise refresh from the live page.
        if not question.get("question_text"):
            question["question_text"] = question_text
        question["question_type"] = qtype

        question_id = (
            question.get("question_id") or question.get("discussion_id") or "unknown"
        )
        exam = question.get("exam", "")
        exhibits = await _extract_exhibits(
            raw_html,
            url,
            exam=exam,
            question_id=question_id,
            client=client,
            sem=sem,
            exhibits_dir=exhibits_root,
        )
        question["exhibits"] = exhibits
        stats["question_type"] = qtype
        stats["n_exhibits"] = len(exhibits)
        for ex in exhibits:
            stats["exhibit_kinds"][ex.get("kind", "unknown")] += 1
        stats["ok"] = True
    except Exception as e:
        stats["error"] = f"parse: {e}"
        logger.warning("Could not parse %s: %s", url, e)
    return stats


async def _backfill_one_file(
    path: Path,
    *,
    sample: int | None,
    max_concurrent: int,
    user_agent: str,
    exhibits_root: Path,
) -> dict[str, Any]:
    logger.info("Loading %s", path)
    questions = _load_json(path)
    total = len(questions)
    if sample is not None:
        questions = questions[:sample]
    logger.info(
        "Processing %s: %d/%d questions", path.name, len(questions), total
    )

    _backup(path)

    sem = asyncio.Semaphore(max_concurrent)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    timeout = httpx.Timeout(45, connect=15)

    qtype_counts: Counter = Counter()
    exhibit_counts: Counter = Counter()
    n_with_exhibits = 0
    n_ok = 0
    n_skipped = 0
    errors: list[str] = []
    started = time.monotonic()

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [
            _process_question(
                client,
                sem,
                q,
                user_agent=user_agent,
                exhibits_root=exhibits_root,
            )
            for q in questions
        ]
        for i, (q, fut) in enumerate(zip(questions, await asyncio.gather(*tasks))):
            stats = fut
            if stats["ok"]:
                n_ok += 1
                qtype_counts[stats["question_type"]] += 1
                if stats["n_exhibits"]:
                    n_with_exhibits += 1
                exhibit_counts.update(stats["exhibit_kinds"])
            elif stats["skipped"]:
                n_skipped += 1
            elif stats["error"]:
                errors.append(f"{q.get('url','?')}: {stats['error']}")
            if (i + 1) % 25 == 0 or (i + 1) == len(questions):
                elapsed = time.monotonic() - started
                rate = (i + 1) / elapsed if elapsed > 0 else 0.0
                logger.info(
                    "  %s %d/%d (ok=%d with_exhibits=%d skipped=%d errors=%d) %.1f q/s",
                    path.name,
                    i + 1,
                    len(questions),
                    n_ok,
                    n_with_exhibits,
                    n_skipped,
                    len(errors),
                    rate,
                )

    _save_json(path, questions)
    elapsed = time.monotonic() - started
    summary = {
        "file": path.name,
        "total_in_file": total,
        "processed": len(questions),
        "ok": n_ok,
        "skipped": n_skipped,
        "errors": len(errors),
        "with_exhibits": n_with_exhibits,
        "elapsed_seconds": round(elapsed, 1),
        "question_types": dict(qtype_counts),
        "exhibits_by_kind": dict(exhibit_counts),
    }
    if errors:
        # Log only the first few errors to keep output tidy.
        for err in errors[:5]:
            logger.warning("  err: %s", err)
    logger.info("Finished %s in %.1fs", path.name, elapsed)
    return summary


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    data_dir = Path(args.data_dir)
    exhibits_root = Path(args.exhibits_dir)

    files = [data_dir / name for name in (args.files or DEFAULT_DATA_FILES)]
    summaries: list[dict[str, Any]] = []
    for path in files:
        if not path.exists():
            logger.warning("Skipping missing file: %s", path)
            continue
        summary = await _backfill_one_file(
            path,
            sample=args.sample,
            max_concurrent=args.max_concurrent,
            user_agent=args.user_agent,
            exhibits_root=exhibits_root,
        )
        summaries.append(summary)
    return {"summaries": summaries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Directory containing the exam JSON files",
    )
    parser.add_argument(
        "--exhibits-dir",
        type=Path,
        default=PROJECT_ROOT / "assets" / "exhibits",
        help="Directory under which per-exam images are saved",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Specific JSON files to process (defaults to dp-600.json + dp-700.json)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Process only the first N questions per file (for quick testing)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Max concurrent in-flight HTTP requests",
    )
    parser.add_argument(
        "--user-agent",
        default=os.environ.get("BACKFILL_USER_AGENT", DEFAULT_USER_AGENT),
        help="HTTP User-Agent string",
    )
    args = parser.parse_args()

    result = asyncio.run(_run(args))
    print("\n===== Backfill Summary =====")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())