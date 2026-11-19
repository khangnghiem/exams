#!/usr/bin/env python3
"""
Crawl Microsoft certification exam discussion questions from examtopics.com.

Supports DP-600, DP-700, AI-103, AI-300, AI-500 (and any Microsoft exam slug
passed via ``--exams``). Handles both legacy ExamTopics discussion markup
(``div.question-choices-container`` + ``div.voted-answers-tally``) and late-2026
discussion markup (inline ``A. ... B. ...`` choices in ``p.card-text``, static
``data-id="825909"`` placeholder, ``Selected Answer: X`` voter badges, and
``"N times"`` upvote counters).

Outputs (use ``--output-dir`` to set destination):
  - <exam>.jsonl (line-delimited JSON, one question per line)
  - <exam>.json  (consolidated JSON array, sorted by topic & question_number)
  - state file   (checkpoint/resume state)

Usage (from azure/ directory):
    python3 scripts/crawl_fabric_discussions.py --output-dir data --exams ai-103 ai-300 ai-500
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import asdict, dataclass, field
import json
import logging
from mimetypes import guess_extension
from pathlib import Path
import random
import re
import sys
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import httpx

# Local imports (kept absolute to avoid implicit relative-import issues when
# run as a script from the repo root).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitize_exhibit_html import sanitize_exhibit_html  # noqa: E402

BASE_URL = "https://www.examtopics.com"
LIST_URL = BASE_URL + "/discussions/microsoft/{page}/"
EXAM_VIEW_URL = BASE_URL + "/exams/microsoft/{exam}/view/"

# Matches both relative (/discussions/...) and absolute (https://www.examtopics.com/discussions/...) hrefs.
DISCUSSION_RE = re.compile(
    r"^(?:https?://(?:www\.)?examtopics\.com)?"
    r"(?P<path>/discussions/microsoft/view/(?P<id>\d+)-exam-(?P<exam>[a-z0-9-]+)-topic-(?P<topic>\d+)-question-(?P<qnum>\d+)-discussion/?)",
    re.IGNORECASE,
)

DEFAULT_EXAMS = ("dp-600", "dp-700", "ai-103", "ai-300", "ai-500")
TARGET_EXAMS = {"dp-600", "dp-700"}

# Static placeholder data-id emitted by ExamTopics on 2026 discussion pages.
PLACEHOLDER_QUESTION_IDS = {"", "825909"}

MULTI_SELECT_PROMPT_RE = re.compile(
    r"\b(?:select\s+(?:two|three|four|five|\d+)|"
    r"which\s+(?:two|three|four|five|\d+)|"
    r"choose\s+(?:two|three|four|five|\d+)|"
    r"each\s+correct\s+answer\s+presents\s+part\s+of\s+the\s+solution|"
    r"more\s+than\s+one\s+answer\s+choice\s+may\s+achieve\s+the\s+goal)\b",
    re.IGNORECASE,
)

INLINE_CHOICE_MARKER_RE = re.compile(
    r"(?:^|(?:<br\s*/?>[\s\r\n]*)+|\n[\s\r\n]*)(?P<letter>[A-Z])\.\s+",
    re.MULTILINE,
)

RICH_CHOICE_HTML_RE = re.compile(r"<(?:img|pre|code|table)\b", re.IGNORECASE)

# Project root (parent of /scripts -> azure/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXHIBITS_DIR = PROJECT_ROOT / "assets" / "exhibits"

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
    # Raw HTML inside the choice when rich media/code is present. Kept empty for
    # plain-text choices so the study guide doesn't duplicate text + HTML.
    text_html: str = ""


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
    question_type: str = "unknown"
    raw_html: str = ""
    exhibits: list[dict[str, Any]] = field(default_factory=list)
    drag_drop_items: list[Any] = field(default_factory=list)
    drag_drop_targets: list[Any] = field(default_factory=list)
    drag_drop_error: str | None = None

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
            "question_type": self.question_type,
            "raw_html": self.raw_html,
            "exhibits": list(self.exhibits),
            "drag_drop_items": list(self.drag_drop_items),
            "drag_drop_targets": list(self.drag_drop_targets),
            "drag_drop_error": self.drag_drop_error,
        }


def is_multiselect_prompt(question_text: str) -> bool:
    """Return True if the question stem explicitly asks for multiple answers."""
    return bool(MULTI_SELECT_PROMPT_RE.search(question_text or ""))


def _infer_code_language(element: Any) -> str:
    """Look at ``element``'s classes (and a child <code>'s) for a language hint."""
    candidates: list[str] = []
    cls_attr = element.get("class") if element else None
    if cls_attr:
        candidates.extend(cls_attr if isinstance(cls_attr, list) else [str(cls_attr)])
    inner = element.find("code") if element and hasattr(element, "find") else None
    if inner is not None:
        inner_cls = inner.get("class")
        if inner_cls:
            candidates.extend(
                inner_cls if isinstance(inner_cls, list) else [str(inner_cls)]
            )
    for c in candidates:
        mc = re.match(r"^(?:language-|lang-)(.+)$", str(c))
        if mc:
            return mc.group(1)
    return "generic"


def infer_question_type(
    question_text: str, has_choices: bool, correct_answers: list[str]
) -> str:
    """Infer the exam-question type from the plain text + answer structure.

    Returns one of: ``single``, ``multiple``, ``hotspot``, ``drag_drop``,
    ``case_study``, or ``unknown``.
    """
    text = (question_text or "").lstrip().lower()
    if text.startswith("hotspot"):
        return "hotspot"
    if text.startswith("drag drop"):
        return "drag_drop"
    if has_choices:
        if len(correct_answers) > 1 or is_multiselect_prompt(question_text):
            return "multiple"
        if text.startswith("case study") or text.startswith("this is a case study"):
            return "case_study"
        return "single"
    if text.startswith("case study") or text.startswith("this is a case study"):
        return "case_study"
    return "unknown"


def _resolve_url(base_url: str, src: str) -> str:
    """Resolve a possibly-relative ``src`` against the page's base URL."""
    if not src:
        return ""
    return urljoin(base_url, src)


def _guess_image_extension(url: str, content_type: str | None = None) -> str:
    """Return a file extension (with dot, lowercase) for an image URL."""
    path = urlparse(url).path
    if "." in path.rsplit("/", 1)[-1]:
        ext = "." + path.rsplit(".", 1)[-1].lower()
        if len(ext) <= 6:
            return ext
    if content_type:
        ext = guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext.lower()
    return ".png"


async def _download_one_image(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    url: str,
    dest: Path,
) -> bool:
    """Download a single image with retries. Returns True on success."""
    if dest.exists() and dest.stat().st_size > 0:
        return True
    delay_low, delay_high = 0.15, 0.45
    for attempt in range(4):
        try:
            async with sem:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; FabricExamCrawler/1.0; "
                            "+https://example.com/bot)"
                        ),
                        "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8",
                    },
                    follow_redirects=True,
                )
            if resp.status_code == 200 and resp.content:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(resp.content)
                return True
            if resp.status_code in (403, 429, 502, 503, 504):
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            return False
        except (httpx.RequestError, httpx.HTTPStatusError):
            await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
            continue
        await asyncio.sleep(random.uniform(delay_low, delay_high))
    return False


def _extract_drag_drop(html: str, url: str) -> tuple[list[Any], list[Any], str | None]:
    """Best-effort extractor for drag-drop source items and target slots."""
    soup = BeautifulSoup(html or "", "html.parser")

    def _label(el: Any) -> str:
        if el is None:
            return ""
        return el.get_text(" ", strip=True).strip()

    items: list[dict[str, str]] = []
    targets: list[dict[str, str]] = []

    for el in soup.select(".drag-source [data-drag-item], .drag-source li, .drag-source .drag-item"):
        label = _label(el)
        if label:
            items.append({"label": label})

    for el in soup.select(
        ".drag-target [data-drop-target], .drag-target .target-slot, "
        ".drag-target .drop-zone, .drag-target li"
    ):
        label = _label(el)
        targets.append({"placeholder": label or "Drop here"})

    if not items:
        for el in soup.select("[data-drag-item]"):
            label = _label(el)
            items.append({"label": label or str(el.get("data-drag-item") or "")})
    if not targets:
        for el in soup.select("[data-drop-target]"):
            label = _label(el)
            targets.append({"placeholder": label or str(el.get("data-drop-target") or "Drop here")})

    error: str | None = None
    if items and targets:
        error = None
    else:
        has_image = bool(soup.select("p.card-text img"))
        if has_image:
            error = "drag-drop UI is rendered as a single image (see exhibit)"
        elif not (items or targets):
            error = "no drag-drop markup found in discussion HTML"

    return items, targets, error


def _extract_inline_choices(raw_html: str) -> tuple[str, list[Choice]]:
    """Split 2026 ``p.card-text`` HTML into ``(stem_html, choices)``.

    On late-2026 ExamTopics discussion pages, multiple-choice options are
    appended directly inside ``p.card-text`` as ``<br/>A. ... <br/>B. ...``.
    We locate the last ``A.`` marker whose subsequent markers to the end of
    ``raw_html`` form a contiguous ``A, B[, C, D, ...]`` sequence of length >= 2.
    """
    if not raw_html:
        return "", []

    matches = list(INLINE_CHOICE_MARKER_RE.finditer(raw_html))
    if len(matches) < 2:
        return raw_html, []

    chosen_start_idx: int | None = None
    for idx in range(len(matches) - 1, -1, -1):
        if matches[idx].group("letter") != "A":
            continue
        tail = matches[idx:]
        if len(tail) < 2:
            continue
        expected = [chr(ord("A") + offset) for offset in range(len(tail))]
        actual = [m.group("letter") for m in tail]
        if actual == expected:
            chosen_start_idx = idx
            break

    if chosen_start_idx is None:
        return raw_html, []

    tail_matches = matches[chosen_start_idx:]
    stem_html = raw_html[: tail_matches[0].start()].rstrip()
    choices: list[Choice] = []

    for i, m in enumerate(tail_matches):
        letter = m.group("letter")
        seg_start = m.end()
        seg_end = tail_matches[i + 1].start() if i + 1 < len(tail_matches) else len(raw_html)
        seg_html = raw_html[seg_start:seg_end]
        # Trim trailing <br>, </br>, and whitespace artifacts.
        seg_html = re.sub(r"(?:\s|</?br\s*/?>)+$", "", seg_html, flags=re.IGNORECASE).strip()
        seg_soup = BeautifulSoup(seg_html, "html.parser")
        plain = re.sub(r"\s+", " ", seg_soup.get_text(" ", strip=True)).strip()
        text_html = sanitize_exhibit_html(seg_html) if RICH_CHOICE_HTML_RE.search(seg_html) else ""
        choices.append(Choice(letter=letter, text=plain, correct=False, text_html=text_html))

    return stem_html, choices


async def _download_choice_images(
    choices: list[Choice],
    base_url: str,
    exam: str,
    question_id: str,
    *,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    exhibits_dir: Path | None = None,
) -> None:
    """Download any ``<img>`` tags inside ``choice.text_html`` and rewrite ``src``."""
    exhibits_root = exhibits_dir or DEFAULT_EXHIBITS_DIR
    target_dir = exhibits_root / exam
    tasks: list[tuple[Any, str, Path, str]] = []

    choice_soups: list[tuple[Choice, BeautifulSoup]] = []
    for ch in choices:
        if not ch.text_html or "<img" not in ch.text_html.lower():
            continue
        soup = BeautifulSoup(ch.text_html, "html.parser")
        choice_soups.append((ch, soup))
        safe_letter = re.sub(r"[^A-Za-z0-9_-]", "_", ch.letter or "X")
        for idx, img in enumerate(soup.find_all("img")):
            src = str(img.get("src", ""))
            if not src:
                continue
            orig_url = _resolve_url(base_url, src)
            ext = _guess_image_extension(orig_url)
            filename = f"{question_id}_{safe_letter}_{idx}{ext}"
            dest = target_dir / filename
            rel_src = f"assets/exhibits/{exam}/{filename}"
            tasks.append((img, orig_url, dest, rel_src))

    if not tasks:
        return

    results = await asyncio.gather(
        *[_download_one_image(client, sem, orig_url, dest) for _, orig_url, dest, _ in tasks]
    )
    for (img, _, _, rel_src), ok in zip(tasks, results):
        if ok:
            img["src"] = rel_src
            img["loading"] = "lazy"

    for ch, soup in choice_soups:
        ch.text_html = sanitize_exhibit_html(str(soup))


async def _extract_exhibits(
    raw_html: str,
    base_url: str,
    exam: str,
    question_id: str,
    *,
    client: httpx.AsyncClient | None = None,
    sem: asyncio.Semaphore | None = None,
    exhibits_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Extract images, tables, and block code snippets from question stem HTML."""
    exhibits: list[dict[str, Any]] = []
    if not raw_html:
        return exhibits

    soup = BeautifulSoup(raw_html, "html.parser")

    exhibits_root = exhibits_dir or DEFAULT_EXHIBITS_DIR
    target_dir = exhibits_root / exam
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1) Images
    img_index = 0
    img_tasks: list[tuple[dict[str, Any], str, Path]] = []
    for img in list(soup.find_all("img")):
        original_url = _resolve_url(base_url, str(img.get("src", "")))
        alt = str(img.get("alt", "") or "")
        if not original_url:
            img.decompose()
            continue
        ext = _guess_image_extension(original_url)
        filename = f"{question_id}_{img_index}{ext}"
        local_path = target_dir / filename
        rel_src = f"assets/exhibits/{exam}/{filename}"
        exhibit: dict[str, Any] = {
            "kind": "image",
            "src": rel_src,
            "alt": alt,
            "original_url": original_url,
            "local_path": rel_src,
        }
        exhibits.append(exhibit)
        img_tasks.append((exhibit, original_url, local_path))
        img_index += 1
        img.decompose()

    # 2) Tables
    for tbl in list(soup.find_all("table")):
        caption_text = ""
        cap = tbl.find("caption")
        if cap:
            caption_text = cap.get_text(strip=True)
        tbl_html = sanitize_exhibit_html(str(tbl))
        exhibits.append(
            {
                "kind": "table",
                "html": tbl_html,
                "caption": caption_text,
            }
        )
        tbl.decompose()

    # 3) Code blocks (<pre> and multiline standalone <code>).
    handled_pre_ids: set[int] = set()
    for pre in list(soup.find_all("pre")):
        language = _infer_code_language(pre)
        exhibits.append(
            {
                "kind": "code",
                "code": pre.get_text(),
                "html": sanitize_exhibit_html(str(pre)),
                "language": language,
            }
        )
        handled_pre_ids.add(id(pre))
        pre.decompose()

    for code in list(soup.find_all("code")):
        ancestor = code.parent
        inside_handled_pre = False
        while ancestor is not None and ancestor is not soup:
            if id(ancestor) in handled_pre_ids:
                inside_handled_pre = True
                break
            ancestor = ancestor.parent
        if inside_handled_pre:
            continue
        code_text = code.get_text()
        # Keep short single-line inline identifiers inside prose rather than
        # turning every ``<code>foo</code>`` token into a standalone exhibit.
        if "\n" not in code_text and len(code_text.strip()) < 60:
            continue
        language = _infer_code_language(code)
        exhibits.append(
            {
                "kind": "code",
                "code": code_text,
                "html": sanitize_exhibit_html(str(code)),
                "language": language,
            }
        )
        code.decompose()

    if img_tasks and client is not None and sem is not None:
        results = await asyncio.gather(
            *[_download_one_image(client, sem, url, dest) for _, url, dest in img_tasks]
        )
        for (exhibit, _, _), ok in zip(img_tasks, results):
            exhibit["downloaded"] = bool(ok)
    elif img_tasks:
        for exhibit, _, _ in img_tasks:
            exhibit["downloaded"] = False

    return exhibits


def _normalize_selected_letters(raw: str, valid_letters: set[str] | None = None) -> str | None:
    """Normalize ``'B, D'`` or ``'BD'`` into sorted uppercase letters ``'BD'``."""
    if not raw:
        return None
    letters = sorted(set(re.findall(r"[A-Z]", raw.upper())))
    if not letters:
        return None
    if valid_letters is not None and not all(ch in valid_letters for ch in letters):
        return None
    return "".join(letters)


def _infer_mcq_letters_from_comments(
    comments: list[Comment],
    choices: list[Choice],
) -> tuple[list[dict[str, Any]], str | None]:
    """Compute ``(voted_answers_tally, most_voted_answer)`` for an MCQ from comments."""
    valid_letters = {c.letter.upper() for c in choices if c.letter}
    if not valid_letters or not comments:
        return [], None

    # 1) Primary signal: explicit ``Selected Answer: X`` voter badges / declarations.
    vote_counts: Counter[str] = Counter()
    weighted_scores: Counter[str] = Counter()
    for c in comments:
        norm = _normalize_selected_letters(c.selected_answer or "", valid_letters)
        if not norm:
            continue
        vote_counts[norm] += 1
        bonus = 2 if "Highly Voted" in c.badges else 0
        weighted_scores[norm] += 1 + max(c.upvotes, 0) + bonus

    if vote_counts:
        ranked = sorted(
            vote_counts.keys(),
            key=lambda ans: (weighted_scores[ans], vote_counts[ans], -len(ans), ans),
            reverse=True,
        )
        top = ranked[0]
        tally = [
            {
                "voted_answers": ans,
                "vote_count": vote_counts[ans],
                "is_most_voted": ans == top,
            }
            for ans in ranked
        ]
        return tally, top

    # 2) Secondary signal: explicit answer statements in comment bodies
    #    (e.g. "The answer is B: No", "Correct answer: A and C", "B is correct").
    explicit_patterns = (
        # With explicit delimiter (: or =), allow upper or lower letter(s), e.g. "Answer: B" or "Answer: b".
        re.compile(
            r"(?i:(?:the\s+answer\s+is|correct\s+answer\s*(?:is)?|selected\s+answer|answer\s+is|answer))\s*[:=]\s*([A-Za-z](?:\s*(?i:,|and|&|/)\s*[A-Za-z])*)(?![A-Za-z])"
        ),
        # Without delimiter ("The answer is B: No", "correct answer is A and C"), require UPPERCASE letter(s)
        # so English prose like "The answer is a managed identity" never matches lowercase "a".
        re.compile(
            r"(?i:(?:the\s+answer\s+is|correct\s+answer\s+is|selected\s+answer\s+is|answer\s+is))\s+([A-Z](?:\s*(?i:,|and|&|/)\s*[A-Z])*)(?![A-Za-z])"
        ),
        re.compile(
            r"^\s*([A-Z](?:\s*(?i:,|and|&)\s*[A-Z])*)(?![A-Za-z])\s+(?i:(?:is|are)\s+(?:the\s+)?correct)\b",
            re.MULTILINE,
        ),
        re.compile(r"^\s*([A-Z])\s*[:.-]\s+\S", re.MULTILINE),
    )

    best_ans: str | None = None
    best_score = -1.0
    for c in comments:
        body = (c.text or "").strip()
        if not body or body.endswith("?"):
            continue
        matched_ans: str | None = None
        for pat in explicit_patterns:
            m = pat.search(body)
            if m:
                cand = _normalize_selected_letters(m.group(1), valid_letters)
                if cand:
                    matched_ans = cand
                    break
        # 3) Tertiary signal: comment uniquely names the exact text of one choice
        #    (useful for 2026 single-comment explanations like "The Ask a question node...").
        if matched_ans is None:
            matching_letters = []
            body_lower = body.lower()
            for ch in choices:
                ctext = (ch.text or "").strip()
                if len(ctext) < 4 or ctext.lower() in {"yes", "no", "true", "false"}:
                    continue
                if re.search(rf"\b{re.escape(ctext.lower())}\b", body_lower):
                    matching_letters.append(ch.letter.upper())
            if len(matching_letters) == 1:
                matched_ans = matching_letters[0]

        if matched_ans:
            score = 10.0 + max(c.upvotes, 0) * 2.0 + (20.0 if "Highly Voted" in c.badges else 0.0)
            if score > best_score:
                best_score = score
                best_ans = matched_ans

    if best_ans:
        return (
            [{"voted_answers": best_ans, "vote_count": 1, "is_most_voted": True}],
            best_ans,
        )
    return [], None


def _record_richness(rec: dict[str, Any]) -> tuple[int, int, int, int, int]:
    """Ranking key when deduplicating multiple discussions for the same (exam, topic, qnum)."""
    has_correct = int(bool(rec.get("correct_answers")))
    has_most_voted = int(bool(rec.get("most_voted_answer")))
    n_comments = len(rec.get("comments") or [])
    n_exhibits = len(rec.get("exhibits") or [])
    try:
        did = int(rec.get("discussion_id") or 0)
    except (TypeError, ValueError):
        did = 0
    return (has_correct, has_most_voted, n_comments, n_exhibits, did)


def _normalize_stem_key(text: str) -> str:
    """Normalized alphanumeric fingerprint for matching /view/ cards to discussions."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()[:240]


class Crawler:
    def __init__(
        self,
        output_dir: Path,
        max_concurrent: int = 3,
        delay: tuple[float, float] = (1.0, 1.8),
        max_retries: int = 4,
        timeout: int = 45,
        exams: set[str] | list[str] | tuple[str, ...] | None = None,
        state_path: Path | None = None,
        start_page: int = 1,
        stop_after_empty_pages: int | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.exams: set[str] = {e.lower() for e in (exams or TARGET_EXAMS)}
        self.state_path = state_path or (output_dir / "state.json")
        self.start_page = max(1, start_page)
        self.stop_after_empty_pages = stop_after_empty_pages
        self.state: dict[str, Any] = self._load_state()
        self.client: httpx.AsyncClient | None = None
        self.sem = asyncio.Semaphore(max_concurrent)

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                data["list_pages_completed"] = set(data.get("list_pages_completed", []))
                data["urls_processed"] = set(data.get("urls_processed", []))
                return data
            except Exception as e:
                logger.warning("Could not load state file %s: %s", self.state_path, e)
        return {
            "list_pages_completed": set(),
            "urls_collected": {},
            "urls_processed": set(),
            "errors": {},
        }

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
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
                        logger.warning(
                            "HTTP %d for %s (attempt %d)",
                            resp.status_code,
                            url,
                            attempt + 1,
                        )
                        last_err = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code}", request=resp.request, response=resp
                        )
                        await asyncio.sleep(2 ** (attempt + 1) + random.uniform(0.5, 2.0))
                    else:
                        resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if e.response is not None and e.response.status_code == 404:
                        raise
                    last_err = e
                    logger.warning("Fetch error for %s (attempt %d): %s", url, attempt + 1, e)
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                except httpx.RequestError as e:
                    last_err = e
                    logger.warning("Request error for %s (attempt %d): %s", url, attempt + 1, e)
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
        raise last_err or RuntimeError(f"Failed to fetch {url}")

    def _parse_discussion_html(self, html: str, url: str, meta: dict[str, Any]) -> Question:
        soup = BeautifulSoup(html, "html.parser")

        q_body = soup.find("div", class_="question-body")
        raw_qid = str(q_body.get("data-id", "")).strip() if q_body else ""
        question_id = str(meta["id"]) if raw_qid in PLACEHOLDER_QUESTION_IDS else raw_qid

        full_card_html = ""
        if q_body:
            p = q_body.find("p", class_="card-text")
            if p:
                full_card_html = str(p.decode_contents())

        choices: list[Choice] = []
        correct_answers: list[str] = []
        choices_container = soup.find("div", class_="question-choices-container")
        if choices_container:
            stem_html = full_card_html
            for li in choices_container.find_all("li", class_="multi-choice-item"):
                letter_span = li.find("span", class_="multi-choice-letter")
                letter = str(letter_span.get("data-choice-letter", "")) if letter_span else ""
                text = li.get_text(strip=True)
                text = re.sub(r"^[A-Z]\.\s*", "", text).strip()

                text_html = ""
                li_copy = BeautifulSoup(str(li), "html.parser").find("li")
                if li_copy is not None:
                    chip = li_copy.find("span", class_="multi-choice-letter")
                    if chip:
                        chip.decompose()
                    inner_raw = li_copy.decode_contents().strip()
                    if RICH_CHOICE_HTML_RE.search(inner_raw):
                        text_html = sanitize_exhibit_html(inner_raw)

                correct = "correct-hidden" in (li.get("class") or [])
                choices.append(
                    Choice(letter=letter, text=text, correct=correct, text_html=text_html)
                )
                if correct:
                    correct_answers.append(letter)
        else:
            stem_html, choices = _extract_inline_choices(full_card_html)

        question_text = (
            BeautifulSoup(stem_html, "html.parser").get_text(separator="\n", strip=True)
            if stem_html
            else ""
        )

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

        comments = self._parse_comments(soup)
        self._apply_comment_consensus(choices, correct_answers, voted_tally, most_voted, comments)
        if not most_voted and voted_tally:
            for item in voted_tally:
                if item.get("is_most_voted"):
                    most_voted = item.get("voted_answers")
                    break

        question_type = infer_question_type(
            question_text=question_text,
            has_choices=bool(choices),
            correct_answers=correct_answers,
        )

        drag_items: list[Any] = []
        drag_targets: list[Any] = []
        drag_error: str | None = None
        if question_type == "drag_drop":
            try:
                drag_items, drag_targets, drag_error = _extract_drag_drop(html, url)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("Drag-drop parse failed for %s: %s", url, e)
                drag_error = f"parse: {e}"

        return Question(
            discussion_id=str(meta["id"]),
            exam=meta["exam"],
            topic=meta["topic"],
            question_number=meta["qnum"],
            question_id=question_id,
            question_text=question_text,
            choices=choices,
            correct_answers=correct_answers,
            voted_answers_tally=voted_tally,
            most_voted_answer=most_voted,
            comments=comments,
            url=url,
            question_type=question_type,
            raw_html=stem_html,
            exhibits=[],
            drag_drop_items=drag_items,
            drag_drop_targets=drag_targets,
            drag_drop_error=drag_error,
        )

    @staticmethod
    def _apply_comment_consensus(
        choices: list[Choice],
        correct_answers: list[str],
        voted_tally: list[dict[str, Any]],
        most_voted: str | None,
        comments: list[Comment],
    ) -> None:
        """Mutate ``voted_tally`` and ``correct_answers`` from community votes when missing."""
        if not choices:
            return
        valid_letters = {c.letter.upper() for c in choices if c.letter}
        if not voted_tally and most_voted is None:
            inferred_tally, inferred_most = _infer_mcq_letters_from_comments(comments, choices)
            if inferred_tally:
                voted_tally.extend(inferred_tally)
            most_voted = inferred_most

        if not correct_answers and most_voted:
            norm = _normalize_selected_letters(most_voted, valid_letters)
            if norm:
                correct_answers.extend(list(norm))
                for ch in choices:
                    ch.correct = ch.letter.upper() in correct_answers

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
                m_up = re.search(r"(\d+)", upvote_el.get_text(" ", strip=True))
                if m_up:
                    upvotes = int(m_up.group(1))

            raw_badges = [b.get_text(" ", strip=True) for b in c.select(".badge")]
            badges: list[str] = []
            selected_answer: str | None = None

            for btxt in raw_badges:
                m_sel = re.search(r"Selected\s+Answer\s*:\s*([A-Z,\s]+)", btxt, re.IGNORECASE)
                if m_sel:
                    selected_answer = _normalize_selected_letters(m_sel.group(1))
                    badges.append(f"Selected Answer: {selected_answer}" if selected_answer else btxt)
                elif btxt:
                    badges.append(btxt)

            if selected_answer is None:
                selected_match = re.search(
                    r"Selected\s+Answer\s*:\s*([A-Z](?:\s*,\s*[A-Z]|[A-Z])*)",
                    text,
                    re.IGNORECASE,
                )
                if selected_match:
                    selected_answer = _normalize_selected_letters(selected_match.group(1))

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
            question: Question | None = None
            html = ""
            for attempt in range(3):
                html = await self._fetch(url)
                question = self._parse_discussion_html(html, url, meta)
                if question.question_text or question.raw_html or question.choices:
                    break
                logger.warning(
                    "Empty question-body on %s (attempt %d/3); backing off",
                    url,
                    attempt + 1,
                )
                await asyncio.sleep(3 * (attempt + 1) + random.uniform(0.5, 1.5))

            if question is None or not (question.question_text or question.raw_html):
                raise RuntimeError("Empty question-body after retries")

            # Load full discussion if paginated BEFORE computing final consensus!
            load_more = BeautifulSoup(html, "html.parser").find("div", class_="load-more-section")
            if load_more:
                discussion_id = load_more.get("data-discussion-id", meta["id"])
                ajax_url = f"{BASE_URL}/ajax/discussion/load-complete/?discussion-id={discussion_id}"
                try:
                    full_html = await self._fetch(ajax_url)
                    full_soup = BeautifulSoup(full_html, "html.parser")
                    full_comments = self._parse_comments(full_soup)
                    if full_comments:
                        question.comments = full_comments
                        # Recompute consensus over the complete comment thread when needed.
                        if question.choices and not any(
                            "correct-hidden" in str(html) for _ in (1,)
                        ):
                            question.voted_answers_tally = []
                            question.most_voted_answer = None
                            question.correct_answers = []
                            for ch in question.choices:
                                ch.correct = False
                            self._apply_comment_consensus(
                                question.choices,
                                question.correct_answers,
                                question.voted_answers_tally,
                                None,
                                question.comments,
                            )
                            for item in question.voted_answers_tally:
                                if item.get("is_most_voted"):
                                    question.most_voted_answer = item.get("voted_answers")
                                    break
                            question.question_type = infer_question_type(
                                question_text=question.question_text,
                                has_choices=bool(question.choices),
                                correct_answers=question.correct_answers,
                            )
                except Exception as e:
                    logger.warning("Could not load full discussion for %s: %s", url, e)

            # Extract stem exhibits and choice images using active HTTP client.
            if self.client is not None:
                if question.raw_html:
                    try:
                        question.exhibits = await _extract_exhibits(
                            question.raw_html,
                            url,
                            exam=question.exam,
                            question_id=question.question_id or question.discussion_id,
                            client=self.client,
                            sem=self.sem,
                        )
                    except Exception as e:
                        logger.warning("Exhibit extraction failed for %s: %s", url, e)
                if question.choices:
                    try:
                        await _download_choice_images(
                            question.choices,
                            url,
                            exam=question.exam,
                            question_id=question.question_id or question.discussion_id,
                            client=self.client,
                            sem=self.sem,
                        )
                    except Exception as e:
                        logger.warning("Choice image download failed for %s: %s", url, e)

            return question
        except Exception as e:
            logger.error("Error crawling discussion %s: %s", url, e)
            self.state["errors"][url] = str(e)
            return None

    async def _crawl_list_page(self, page: int) -> tuple[dict[str, list[dict[str, Any]]], int | None]:
        url = LIST_URL.format(page=page)
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")

        found: dict[str, list[dict[str, Any]]] = {exam: [] for exam in self.exams}
        for a in soup.find_all("a", href=True):
            href = str(a.get("href", "")).strip()
            m = DISCUSSION_RE.match(href)
            if not m:
                continue
            exam = m.group("exam").lower()
            if exam not in self.exams:
                continue
            norm_path = m.group("path")
            if not norm_path.endswith("/"):
                norm_path += "/"
            meta = {
                "id": m.group("id"),
                "exam": exam,
                "topic": int(m.group("topic")),
                "qnum": int(m.group("qnum")),
                "path": norm_path,
                "title": a.get_text(strip=True),
            }
            found[exam].append(meta)

        last_page = None
        page_indicator = soup.find("span", class_="discussion-list-page-indicator")
        if page_indicator:
            m = re.search(r"of\s+<strong>(\d+)</strong>", str(page_indicator))
            if m:
                last_page = int(m.group(1))

        return found, last_page

    async def discover_urls(self, max_pages: int | None = None) -> int:
        logger.info("Phase 1: Discovering discussion URLs for %s...", sorted(self.exams))
        last_page: int | None = self.state.get("total_list_pages")
        page = self.start_page
        empty_streak = 0
        # Use single-page stepping for tiny test thresholds so streak counts are exact;
        # use bounded concurrent batches for real crawls while respecting self.sem.
        step_size = (
            1
            if (self.stop_after_empty_pages is not None and self.stop_after_empty_pages < 5)
            else max(1, self.max_concurrent)
        )

        stop_discovery = False
        while not stop_discovery:
            batch_pages: list[int] = []
            while len(batch_pages) < step_size:
                if max_pages is not None and page > max_pages:
                    if not batch_pages:
                        logger.info("Reached max_pages limit: %d", max_pages)
                    stop_discovery = True
                    break
                if last_page is not None and page > last_page:
                    stop_discovery = True
                    break
                if page in self.state["list_pages_completed"]:
                    page += 1
                    continue
                batch_pages.append(page)
                page += 1

            if not batch_pages:
                break

            logger.info(
                "Crawling discussion list page(s) %s%s",
                batch_pages[0] if len(batch_pages) == 1 else f"{batch_pages[0]}..{batch_pages[-1]}",
                f"/{last_page}" if last_page else "",
            )
            outcomes = await asyncio.gather(
                *[self._crawl_list_page(p) for p in batch_pages],
                return_exceptions=True,
            )

            for p, outcome in zip(batch_pages, outcomes):
                if isinstance(outcome, BaseException):
                    if (
                        isinstance(outcome, httpx.HTTPStatusError)
                        and outcome.response is not None
                        and outcome.response.status_code == 404
                        and p > 1
                    ):
                        logger.info("Reached HTTP 404 at list page %d; stopping discovery.", p)
                        stop_discovery = True
                        break
                    logger.error("Error on list page %d: %s", p, outcome)
                    self._save_state()
                    raise outcome

                found, detected_last = outcome
                if detected_last and last_page is None:
                    last_page = detected_last
                    self.state["total_list_pages"] = last_page
                    logger.info("Detected total discussion list pages: %d", last_page)

                any_target_hit = False
                for exam, urls in found.items():
                    if urls:
                        any_target_hit = True
                    existing = {u["path"] for u in self.state["urls_collected"].get(exam, [])}
                    new_urls = [u for u in urls if u["path"] not in existing]
                    if new_urls:
                        self.state["urls_collected"].setdefault(exam, []).extend(new_urls)
                        logger.info("Page %d: found %d new %s URLs", p, len(new_urls), exam.upper())

                self.state["list_pages_completed"].add(p)

                if any_target_hit:
                    empty_streak = 0
                else:
                    empty_streak += 1
                    if (
                        self.stop_after_empty_pages is not None
                        and empty_streak >= self.stop_after_empty_pages
                    ):
                        logger.info(
                            "Reached %d consecutive list pages with no %s discussions at page %d; stopping discovery.",
                            empty_streak,
                            "/".join(sorted(self.exams)),
                            p,
                        )
                        stop_discovery = True
                        break

            self._save_state()

        total = sum(
            len(v) for k, v in self.state["urls_collected"].items() if k in self.exams
        )
        logger.info("Discovery complete. Total URLs collected for target exams: %d", total)
        for exam in sorted(self.exams):
            logger.info("  %s: %d", exam.upper(), len(self.state["urls_collected"].get(exam, [])))
        return total

    async def _fetch_exam_view_enrichment(self, exam: str) -> dict[str, dict[str, Any]]:
        """Fetch public page 1 of ``/exams/microsoft/{exam}/view/`` to harvest
        official ``correct_answers`` and ``voted_answers_tally`` for its 10 cards.
        """
        url = EXAM_VIEW_URL.format(exam=exam)
        enrichment: dict[str, dict[str, Any]] = {}
        try:
            html = await self._fetch(url)
        except Exception as e:
            logger.warning("Could not fetch exam view page %s: %s", url, e)
            return enrichment

        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".exam-question-card"):
            q_body = card.find("div", class_="question-body")
            p = q_body.find("p", class_="card-text") if q_body else None
            if not p:
                continue
            stem_text = p.get_text(separator="\n", strip=True)
            key = _normalize_stem_key(stem_text)
            if not key:
                continue

            correct_letters: list[str] = []
            container = card.find("div", class_="question-choices-container")
            if container:
                for li in container.find_all("li", class_="multi-choice-item"):
                    if "correct-hidden" in (li.get("class") or []):
                        ls = li.find("span", class_="multi-choice-letter")
                        if ls and ls.get("data-choice-letter"):
                            correct_letters.append(str(ls.get("data-choice-letter")).strip().upper())

            tally: list[dict[str, Any]] = []
            most_voted: str | None = None
            tally_div = card.find("div", class_="voted-answers-tally")
            if tally_div:
                script = tally_div.find("script", type="application/json")
                if script and script.string:
                    try:
                        tally = json.loads(script.string)
                        for item in tally:
                            if item.get("is_most_voted"):
                                most_voted = item.get("voted_answers")
                                break
                    except json.JSONDecodeError:
                        pass

            if correct_letters or tally or most_voted:
                enrichment[key] = {
                    "correct_answers": sorted(set(correct_letters)),
                    "voted_answers_tally": tally,
                    "most_voted_answer": most_voted,
                }
        return enrichment

    async def crawl_discussions(self) -> dict[str, list[dict[str, Any]]]:
        logger.info("Phase 2: Crawling individual discussions...")
        results: dict[str, list[dict[str, Any]]] = {exam: [] for exam in self.exams}

        tasks: list[tuple[str, dict[str, Any]]] = []
        for exam in sorted(self.exams):
            for meta in self.state["urls_collected"].get(exam, []):
                if meta["path"] in self.state["urls_processed"]:
                    continue
                tasks.append((exam, meta))

        if not tasks:
            logger.info("No new discussions to crawl.")
            return results

        logger.info("Discussions to crawl: %d", len(tasks))

        view_enrichment: dict[str, dict[str, dict[str, Any]]] = {}
        for exam in sorted(self.exams):
            view_enrichment[exam] = await self._fetch_exam_view_enrichment(exam)

        batch_size = 20
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]
            coros = [self._crawl_discussion(meta) for _, meta in batch]
            questions = await asyncio.gather(*coros)

            for (exam, meta), q in zip(batch, questions):
                if q is None:
                    continue
                key = _normalize_stem_key(q.question_text)
                enrich = view_enrichment.get(exam, {}).get(key)
                if enrich and q.choices:
                    valid_letters = {ch.letter.upper() for ch in q.choices}
                    official = [
                        ch for ch in enrich.get("correct_answers", []) if ch in valid_letters
                    ]
                    if official and not q.correct_answers:
                        q.correct_answers = official
                        for ch in q.choices:
                            ch.correct = ch.letter.upper() in official
                    if enrich.get("voted_answers_tally") and not q.voted_answers_tally:
                        q.voted_answers_tally = enrich["voted_answers_tally"]
                    if enrich.get("most_voted_answer") and not q.most_voted_answer:
                        q.most_voted_answer = enrich["most_voted_answer"]
                    q.question_type = infer_question_type(
                        q.question_text, bool(q.choices), q.correct_answers
                    )

                results[exam].append(q.to_dict())
                self.state["urls_processed"].add(meta["path"])

            self._save_state()
            logger.info(
                "Completed batch %d/%d (%d discussions)",
                i // batch_size + 1,
                (len(tasks) + batch_size - 1) // batch_size,
                len(batch),
            )

        return results

    def _load_existing_records(self, exam: str) -> list[dict[str, Any]]:
        json_path = self.output_dir / f"{exam}.json"
        if json_path.exists():
            try:
                return json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Could not parse existing %s; ignoring", json_path)
        jsonl_path = self.output_dir / f"{exam}.jsonl"
        if jsonl_path.exists():
            records: list[dict[str, Any]] = []
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            return records
        return []

    def consolidate_json(
        self,
        results: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        """Write deduplicated ``.json`` and ``.jsonl`` files for each target exam."""
        for exam in sorted(self.exams):
            json_path = self.output_dir / f"{exam}.json"
            jsonl_path = self.output_dir / f"{exam}.jsonl"

            if results is not None and exam in results:
                existing = self._load_existing_records(exam)
                new_records = results[exam]
                by_discussion: dict[str, dict[str, Any]] = {}
                for rec in existing:
                    did = str(rec.get("discussion_id") or "")
                    if did:
                        by_discussion[did] = rec
                for nrec in new_records:
                    did = str(nrec.get("discussion_id") or "")
                    if did:
                        by_discussion[did] = nrec
                candidates = list(by_discussion.values()) if by_discussion else (existing + new_records)
            else:
                candidates = self._load_existing_records(exam)
                if not candidates:
                    continue

            # Deduplicate multiple discussion threads targeting the same (topic, question_number)
            # so question labels (Q1.5) and Markdown anchors (#q1-5) stay 1-to-1.
            by_slot: dict[tuple[int, int], dict[str, Any]] = {}
            for rec in candidates:
                slot = (int(rec.get("topic", 0)), int(rec.get("question_number", 0)))
                prev = by_slot.get(slot)
                if prev is None or _record_richness(rec) >= _record_richness(prev):
                    by_slot[slot] = rec

            records = sorted(
                by_slot.values(),
                key=lambda r: (r.get("topic", 0), r.get("question_number", 0)),
            )
            if not records:
                continue

            json_path.write_text(
                json.dumps(records, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            with jsonl_path.open("w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            logger.info(
                "Wrote %s and %s with %d records",
                json_path.name,
                jsonl_path.name,
                len(records),
            )

    async def run(self, max_list_pages: int | None = None) -> None:
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        timeout = httpx.Timeout(self.timeout, connect=15)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            self.client = client
            await self.discover_urls(max_pages=max_list_pages)
            results = await self.crawl_discussions()
            self.consolidate_json(results=results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Microsoft exam discussions from examtopics.com")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Output directory")
    parser.add_argument(
        "--exams",
        nargs="+",
        default=list(DEFAULT_EXAMS),
        help="Exam slugs to crawl (e.g. ai-103 ai-300 ai-500)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to checkpoint state JSON (defaults to <output-dir>/state.json)",
    )
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent requests")
    parser.add_argument("--delay", type=float, nargs=2, default=[1.0, 1.8], help="Min/max delay seconds")
    parser.add_argument("--start-page", type=int, default=1, help="List page to start discovery from")
    parser.add_argument("--max-list-pages", type=int, default=None, help="Limit list pages")
    parser.add_argument(
        "--stop-after-empty-pages",
        type=int,
        default=None,
        help="Stop list discovery after N consecutive pages without target-exam links",
    )
    parser.add_argument("--max-retries", type=int, default=4, help="Max retries per request")
    parser.add_argument("--reset", action="store_true", help="Delete target state/output files and restart")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    exams = [e.lower() for e in args.exams]
    state_path = args.state_file or (args.output_dir / "state.json")

    if args.reset:
        targets = [state_path]
        for ex in exams:
            targets.append(args.output_dir / f"{ex}.json")
            targets.append(args.output_dir / f"{ex}.jsonl")
        for p in targets:
            if p.exists():
                p.unlink()
                logger.info("Removed %s", p)

    crawler = Crawler(
        output_dir=args.output_dir,
        max_concurrent=args.max_concurrent,
        delay=tuple(args.delay),
        max_retries=args.max_retries,
        exams=exams,
        state_path=state_path,
        start_page=args.start_page,
        stop_after_empty_pages=args.stop_after_empty_pages,
    )
    try:
        asyncio.run(crawler.run(max_list_pages=args.max_list_pages))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. State saved for resume.")
        crawler._save_state()
        raise


if __name__ == "__main__":
    main()
