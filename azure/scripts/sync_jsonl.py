#!/usr/bin/env python3
"""
Sync stale ``data/dp-*.jsonl`` files with their corresponding ``.json`` files.

The crawler used to append to ``.jsonl`` during a crawl and rebuild ``.json``
from the JSONL at the end, but several backfills (exhibits, missing answers,
hotspot / drag-drop answers, raw_html) only updated ``.json`` and left the
``.jsonl`` untouched. This script rewrites each ``data/dp-*.jsonl`` as one
JSON object per line from the matching ``.json`` so the two formats stay in
lock-step until the next full crawl regenerates both at once.

Usage (from repo root):

    python scripts/sync_jsonl.py                # sync both dp-600.json and dp-700.json
    python scripts/sync_jsonl.py --data-dir data --files dp-600.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_DATA_FILES: list[str] = ["dp-600.json", "dp-700.json"]


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write ``records`` as one JSON object per line.

    Writes atomically via a sibling ``.tmp`` file so a crash mid-write doesn't
    leave a half-written ``.jsonl`` that downstream tooling would refuse to
    parse.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(path)


def sync_file(json_path: Path) -> dict[str, Any]:
    """Rewrite ``json_path.with_suffix('.jsonl')`` from ``json_path``.

    Returns a small stats dict so callers / tests can verify the work that was
    done without re-reading the files.
    """
    jsonl_path = json_path.with_suffix(".jsonl")
    records = _load_json(json_path)
    # Sort by topic then question number so the JSONL order matches the JSON.
    records.sort(key=lambda r: (r.get("topic", 0), r.get("question_number", 0)))
    _write_jsonl(jsonl_path, records)
    return {
        "json": str(json_path),
        "jsonl": str(jsonl_path),
        "records": len(records),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing the exam JSON files (default: data)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Specific JSON files to sync (defaults to dp-600.json + dp-700.json)",
    )
    args = parser.parse_args()

    file_names = args.files or DEFAULT_DATA_FILES
    summaries: list[dict[str, Any]] = []
    for name in file_names:
        json_path = args.data_dir / name
        if not json_path.exists():
            print(f"skip (missing): {json_path}", file=sys.stderr)
            continue
        summaries.append(sync_file(json_path))

    print(json.dumps({"summaries": summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())