#!/usr/bin/env python3
"""
Backfill ``text_html`` for image-/code-based multiple-choice options.

Several ExamTopics questions publish choices as ``<img>`` tags or as inline
``<pre><code>`` snippets. The original crawler used ``li.get_text(strip=True)``
to extract choice text, which collapses those choices to empty strings, so the
study guide renders them as blank A/B/C/D rows.

This script re-fetches the discussion page for every question whose
``choices`` array is non-empty *and* whose ``choice.text`` is shorter than
3 characters for every choice. For each such question it:

  1. Re-parses the ``<li class="multi-choice-item">`` HTML, drops the
     ``<span class="multi-choice-letter">`` chip, and stores the rest as
     ``choice.text_html``.
  2. Downloads every ``<img>`` inside the choice HTML into
     ``assets/exhibits/{exam}/{question_id}_{letter}{ext}`` and rewrites the
     ``src`` to that local relative path so the study guide can render it
     offline.
  3. Leaves ``choice.text`` alone unless it would otherwise be empty *and*
     ``text_html`` has no extractable plain-text content.

A ``.bak`` snapshot of each input file is created on the first write so the
operation can be safely re-run or rolled back.

Usage (from repo root):

    # Full run:
    python scripts/backfill_choice_markup.py

    # Quick sanity check on 5 questions per exam:
    python scripts/backfill_choice_markup.py --sample 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import shutil
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Allow ``python scripts/backfill_choice_markup.py`` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitize_exhibit_html import sanitize_exhibit_html  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILES: list[str] = ["dp-600.json", "dp-700.json"]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; FabricExamCrawler/1.0; +https://example.com/bot)"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("choice-backfill")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        logger.info("Created backup: %s", bak)


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _guess_image_extension(url: str, content_type: str | None = None) -> str:
    """Return a file extension (with dot, lowercase) for an image URL."""
    from mimetypes import guess_extension

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


def _safe_letter(letter: str) -> str:
    """Restrict choice letters to filesystem-friendly characters."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", letter or "X")


def _strip_html_to_text(html: str) -> str:
    """Return a plain-text rendering of ``html`` (no tags, whitespace squashed)."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


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
                        "Accept": (
                            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                        ),
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
                        "HTTP %d for %s (attempt %d)",
                        resp.status_code,
                        url,
                        attempt + 1,
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


async def _download_image(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    url: str,
    dest: Path,
    *,
    user_agent: str,
) -> tuple[bool, str]:
    """Download a single image with retries. Returns (ok, final_extension)."""
    delay_low, delay_high = 0.2, 0.6
    for attempt in range(4):
        try:
            async with sem:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": (
                            "image/avif,image/webp,image/png,image/*,*/*;q=0.8"
                        ),
                    },
                    follow_redirects=True,
                )
            if resp.status_code == 200:
                ct = resp.headers.get("content-type", "")
                ext = _guess_image_extension(url, ct)
                dest.parent.mkdir(parents=True, exist_ok=True)
                # Ensure dest has the resolved extension.
                final_dest = dest.with_suffix(ext)
                if final_dest.exists() and final_dest.stat().st_size > 0:
                    return True, ext
                final_dest.write_bytes(resp.content)
                return True, ext
            if resp.status_code in (403, 429, 502, 503, 504):
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            return False, ".png"
        except (httpx.RequestError, httpx.HTTPStatusError):
            await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
            continue
        await asyncio.sleep(random.uniform(delay_low, delay_high))
    return False, ".png"


# ---------------------------------------------------------------------------
# Question processing
# ---------------------------------------------------------------------------


def _needs_backfill(question: dict[str, Any]) -> bool:
    """True iff every choice has effectively-empty ``text`` (<3 chars)."""
    choices = question.get("choices") or []
    if not choices:
        return False
    # Skip if every choice already has text_html (no work to do).
    if all(c.get("text_html") for c in choices):
        return False
    for c in choices:
        if (c.get("text") or "").strip() and len((c.get("text") or "").strip()) >= 3:
            return False
    return True


async def _backfill_one_question(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    question: dict[str, Any],
    *,
    user_agent: str,
    exhibits_root: Path,
) -> dict[str, Any]:
    """Fetch + repopulate ``text_html`` for one question. Returns stats."""
    url = question.get("url", "")
    stats: dict[str, Any] = {
        "question_id": question.get("question_id", ""),
        "exam": question.get("exam", ""),
        "topic": question.get("topic", 0),
        "question_number": question.get("question_number", 0),
        "url": url,
        "ok": False,
        "skipped": False,
        "error": None,
        "n_choices": 0,
        "n_html_updated": 0,
        "n_text_recovered": 0,
        "images_downloaded": [],
    }

    if not url:
        stats["skipped"] = True
        stats["error"] = "no url"
        return stats

    try:
        html = await _fetch_with_retries(client, sem, url, user_agent=user_agent)
    except Exception as e:
        stats["error"] = str(e)
        logger.warning("Could not fetch %s: %s", url, e)
        return stats

    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_="question-choices-container")
    if not container:
        stats["error"] = "no choices container"
        return stats

    # Build a {letter: <li>} map from the live page.
    live_letters: dict[str, Any] = {}
    for li in container.find_all("li", class_="multi-choice-item"):
        ls = li.find("span", class_="multi-choice-letter")
        if not ls:
            continue
        letter = str(ls.get("data-choice-letter", ""))
        if letter:
            live_letters[letter] = li

    exam = question.get("exam", "")
    question_id = question.get("question_id") or question.get("discussion_id") or "unknown"
    target_dir = exhibits_root / exam
    target_dir.mkdir(parents=True, exist_ok=True)

    # Tasks for parallel image downloads.
    image_tasks: list[tuple[dict[str, Any], str, Path]] = []

    for choice in question.get("choices", []):
        letter = choice.get("letter", "")
        li = live_letters.get(letter)
        if li is None:
            continue

        stats["n_choices"] += 1

        # Clone the <li> so we can mutate it without disturbing other choices.
        clone_root = BeautifulSoup(str(li), "html.parser")
        clone = clone_root.find("li") or clone_root
        chip = clone.find("span", class_="multi-choice-letter")
        if chip:
            chip.decompose()

        # Find all <img> tags first and queue downloads, then rewrite their src.
        for img_idx, img in enumerate(clone.find_all("img")):
            src = str(img.get("src", ""))
            if not src:
                img.decompose()
                continue
            original_url = urljoin(url, src)
            safe_letter = _safe_letter(letter)
            base_name = f"{question_id}_{safe_letter}_{img_idx}"
            dest = target_dir / f"{base_name}.png"  # extension may be refined
            rel_src = f"assets/exhibits/{exam}/{base_name}.png"

            exhibit: dict[str, Any] = {
                "letter": letter,
                "original_url": original_url,
                "local_path": str(target_dir / f"{base_name}.png"),
                "downloaded": False,
            }
            image_tasks.append((exhibit, original_url, dest))
            img["src"] = rel_src
            img["loading"] = "lazy"

        # Sanitize the remaining HTML so we drop scripts/styles/handlers.
        sanitized = sanitize_exhibit_html(clone.decode_contents().strip())
        if sanitized:
            choice["text_html"] = sanitized
            stats["n_html_updated"] += 1

        # If ``text`` is empty but we can extract meaningful plain text from
        # ``text_html`` (e.g. for code snippets), backfill it.
        existing_text = (choice.get("text") or "").strip()
        if not existing_text:
            recovered = _strip_html_to_text(sanitized)
            if recovered and len(recovered) >= 3:
                choice["text"] = recovered
                stats["n_text_recovered"] += 1

    if image_tasks:
        results = await asyncio.gather(
            *[
                _download_image(client, sem, url, dest, user_agent=user_agent)
                for _, url, dest in image_tasks
            ]
        )
        for (exhibit, _url, dest), (ok, ext) in zip(image_tasks, results):
            exhibit["downloaded"] = bool(ok)
            exhibit["local_path"] = str(dest.with_suffix(ext))
            if ok:
                stats["images_downloaded"].append(
                    {"letter": exhibit["letter"], "local_path": exhibit["local_path"]}
                )

    stats["ok"] = True
    return stats


# ---------------------------------------------------------------------------
# File / CLI plumbing
# ---------------------------------------------------------------------------


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

    eligible = [q for q in questions if _needs_backfill(q)]
    logger.info(
        "%s: %d/%d questions eligible for backfill",
        path.name,
        len(eligible),
        total,
    )

    if not eligible:
        return {
            "file": path.name,
            "total_in_file": total,
            "processed": 0,
            "ok": 0,
            "skipped": 0,
            "errors": 0,
            "images_downloaded": 0,
            "questions_updated": [],
        }

    _backup(path)

    sem = asyncio.Semaphore(max_concurrent)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    timeout = httpx.Timeout(45, connect=15)

    n_ok = 0
    n_skipped = 0
    n_err = 0
    images_downloaded = 0
    updated: list[dict[str, Any]] = []
    errors: list[str] = []
    started = time.monotonic()

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [
            _backfill_one_question(
                client,
                sem,
                q,
                user_agent=user_agent,
                exhibits_root=exhibits_root,
            )
            for q in eligible
        ]
        for i, (q, fut) in enumerate(
            zip(eligible, await asyncio.gather(*tasks))
        ):
            stats = fut
            if stats["ok"]:
                n_ok += 1
                if stats["n_html_updated"] > 0:
                    updated.append(
                        {
                            "question_id": stats["question_id"],
                            "exam": stats["exam"],
                            "topic": stats["topic"],
                            "question_number": stats["question_number"],
                            "url": stats["url"],
                            "n_html_updated": stats["n_html_updated"],
                            "n_text_recovered": stats["n_text_recovered"],
                            "images_downloaded": stats["images_downloaded"],
                        }
                    )
                images_downloaded += len(stats["images_downloaded"])
            elif stats["skipped"]:
                n_skipped += 1
            elif stats["error"]:
                n_err += 1
                errors.append(f"{stats.get('url', '?')}: {stats['error']}")

            if (i + 1) % 10 == 0 or (i + 1) == len(eligible):
                elapsed = time.monotonic() - started
                rate = (i + 1) / elapsed if elapsed > 0 else 0.0
                logger.info(
                    "  %s %d/%d (ok=%d err=%d skip=%d images=%d) %.1f q/s",
                    path.name,
                    i + 1,
                    len(eligible),
                    n_ok,
                    n_err,
                    n_skipped,
                    images_downloaded,
                    rate,
                )

    _save_json(path, questions)
    elapsed = time.monotonic() - started
    logger.info(
        "Finished %s in %.1fs (updated %d questions, %d images)",
        path.name,
        elapsed,
        len(updated),
        images_downloaded,
    )
    if errors:
        for err in errors[:5]:
            logger.warning("  err: %s", err)

    return {
        "file": path.name,
        "total_in_file": total,
        "eligible": len(eligible),
        "processed": len(eligible),
        "ok": n_ok,
        "skipped": n_skipped,
        "errors": n_err,
        "images_downloaded": images_downloaded,
        "elapsed_seconds": round(elapsed, 1),
        "questions_updated": updated,
    }


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
    print("\n===== Choice Markup Backfill Summary =====")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())