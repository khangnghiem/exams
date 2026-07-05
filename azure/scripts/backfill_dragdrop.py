#!/usr/bin/env python3
"""
Backfill drag-drop extraction for every ``drag_drop`` question in
``data/dp-600.json`` and ``data/dp-700.json``.

For each ``question_type == "drag_drop"`` question we re-fetch its discussion
page and walk the HTML looking for drag-drop source items and target drop
zones. ExamTopics currently embeds the drag-drop UI inside a single ``<img>``
exhibit (so the markup itself doesn't expose items / targets), but this
script still:

* re-fetches the page (so any cached exhibits stay in sync),
* runs ``_extract_drag_drop`` to discover any future markup hints,
* downloads any drag-drop exhibit images referenced inside the question
  text into ``assets/exhibits/{exam}/`` if they aren't already present,
* records a short ``drag_drop_error`` reason when extraction is empty.

Usage (from repo root):

    # Quick smoke test on 5 drag-drop questions per exam:
    python scripts/backfill_dragdrop.py --sample 5

    # Full run:
    python scripts/backfill_dragdrop.py
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

# Allow `python scripts/backfill_dragdrop.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_fabric_discussions import (  # noqa: E402
    PROJECT_ROOT,
    DEFAULT_EXHIBITS_DIR,
    _download_one_image,
    _extract_drag_drop,
    _extract_exhibits,
    _resolve_url,
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
logger = logging.getLogger("backfill_dragdrop")


def _backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        logger.info("Created backup: %s", bak)


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    """Atomic write so a crash mid-write doesn't corrupt the data file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


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
    """Re-fetch + extract drag-drop data for one question.

    Returns a small stats dict so the caller can summarise the run.
    """
    url = question.get("url", "")
    stats: dict[str, Any] = {
        "ok": False,
        "fetched": False,
        "skipped": False,
        "error": None,
        "n_items": 0,
        "n_targets": 0,
        "n_image_exhibits_added": 0,
    }

    if not url:
        stats["skipped"] = True
        stats["error"] = "no url"
        return stats

    try:
        html = await _fetch_with_retries(client, sem, url, user_agent=user_agent)
        stats["fetched"] = True
    except Exception as e:
        stats["error"] = f"fetch: {e}"
        logger.warning("Could not fetch %s: %s", url, e)
        return stats

    # 1) Extract drag-drop source items + target slots from the HTML.
    try:
        items, targets, error = _extract_drag_drop(html, url)
    except Exception as e:
        items, targets, error = [], [], f"parse: {e}"
        logger.warning("Drag-drop parse failed for %s: %s", url, e)
    question["drag_drop_items"] = items
    question["drag_drop_targets"] = targets
    question["drag_drop_error"] = error
    stats["n_items"] = len(items)
    stats["n_targets"] = len(targets)

    # 2) Make sure exhibit images are downloaded. Existing exhibit entries
    #    are reused; new image URLs discovered during the re-fetch are added.
    exam = question.get("exam", "") or "unknown"
    qid = (
        question.get("question_id")
        or question.get("discussion_id")
        or "unknown"
    )
    existing = list(question.get("exhibits") or [])
    existing_urls = {
        str(ex.get("original_url") or "") for ex in existing if ex.get("kind") == "image"
    }

    try:
        exhibits = await _extract_exhibits(
            question.get("raw_html", "") or "",
            url,
            exam=exam,
            question_id=qid,
            client=client,
            sem=sem,
            exhibits_dir=exhibits_root,
        )
        # Merge: keep existing exhibits (and their downloaded flags) but add
        # any new image exhibits the re-fetch discovered.
        merged = list(existing)
        merged_urls = set(existing_urls)
        for ex in exhibits:
            if ex.get("kind") != "image":
                continue
            o_url = str(ex.get("original_url") or "")
            if o_url and o_url in merged_urls:
                continue
            merged.append(ex)
            merged_urls.add(o_url)
            stats["n_image_exhibits_added"] += 1
        # Preserve any non-image exhibits (tables / code) that the upstream
        # extractor may have produced this time around.
        for ex in exhibits:
            if ex.get("kind") != "image":
                # Only add a non-image if we don't already have one for this slot.
                if not any(m.get("kind") == ex.get("kind") for m in merged):
                    merged.append(ex)
        question["exhibits"] = merged
    except Exception as e:
        logger.warning("Exhibit re-extraction failed for %s: %s", url, e)

    stats["ok"] = True
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
    # Only operate on drag-drop questions.
    targets = [q for q in questions if (q.get("question_type") or "").strip().lower() == "drag_drop"]
    if sample is not None:
        targets = targets[:sample]
    logger.info(
        "Found %d drag-drop question(s) in %s; processing %d",
        len([q for q in questions if (q.get("question_type") or "").strip().lower() == "drag_drop"]),
        path.name,
        len(targets),
    )

    if not targets:
        return {
            "file": path.name,
            "total_drag_drop": 0,
            "processed": 0,
            "ok": 0,
            "errors": 0,
            "n_items": 0,
            "n_targets": 0,
            "n_image_exhibits_added": 0,
        }

    _backup(path)

    sem = asyncio.Semaphore(max_concurrent)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    timeout = httpx.Timeout(45, connect=15)

    n_ok = 0
    n_err = 0
    n_items = 0
    n_targets = 0
    n_image_exhibits_added = 0
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
            for q in targets
        ]
        for i, (q, fut) in enumerate(zip(targets, await asyncio.gather(*tasks))):
            stats = fut
            if stats["ok"]:
                n_ok += 1
                n_items += stats["n_items"]
                n_targets += stats["n_targets"]
                n_image_exhibits_added += stats["n_image_exhibits_added"]
            elif stats.get("error"):
                n_err += 1
                errors.append(f"{q.get('url', '?')}: {stats['error']}")
            if (i + 1) % 25 == 0 or (i + 1) == len(targets):
                elapsed = time.monotonic() - started
                rate = (i + 1) / elapsed if elapsed > 0 else 0.0
                logger.info(
                    "  %s %d/%d (ok=%d err=%d items=%d targets=%d new_images=%d) %.1f q/s",
                    path.name,
                    i + 1,
                    len(targets),
                    n_ok,
                    n_err,
                    n_items,
                    n_targets,
                    n_image_exhibits_added,
                    rate,
                )

    _save_json(path, questions)
    elapsed = time.monotonic() - started
    summary = {
        "file": path.name,
        "total_drag_drop": sum(
            1 for q in questions if (q.get("question_type") or "").strip().lower() == "drag_drop"
        ),
        "processed": len(targets),
        "ok": n_ok,
        "errors": n_err,
        "n_items": n_items,
        "n_targets": n_targets,
        "n_image_exhibits_added": n_image_exhibits_added,
        "elapsed_seconds": round(elapsed, 1),
    }
    if errors:
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
        default=DEFAULT_EXHIBITS_DIR,
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
        help="Process only the first N drag-drop questions per file (for quick testing)",
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
    print("\n===== Drag-drop Backfill Summary =====")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())