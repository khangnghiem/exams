#!/usr/bin/env python3
"""One-shot immediate fix for DP-700 Q2.12 (question_id 936013).

Sets `most_voted_answer` to the answer text from comment 1625942 so the study
guide renders it in the "Most voted" card instead of "Not provided".

Idempotent: safe to run multiple times.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET_QID = "936013"
TARGET_COMMENT_ID = "1625942"
ANSWER_TEXT = (
    "First dropdown: o.OrderDate >= c.valid_from_datetime\n\n"
    "Second dropdown: o.OrderDate < c.valid_to_datetime"
)


def update_json_file(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open() as f:
        data = json.load(f)
    changed = False
    for q in data:
        if str(q.get("question_id")) == TARGET_QID:
            old = q.get("most_voted_answer")
            if old != ANSWER_TEXT:
                q["most_voted_answer"] = ANSWER_TEXT
                # Keep correct_answers empty (this is a HOTSPOT, not lettered)
                if q.get("correct_answers") is None:
                    q["correct_answers"] = []
                changed = True
            break
    if changed:
        with path.open("w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n") if False else None  # no-op; json.dump doesn't write trailing newline
    return changed


def update_jsonl_file(path: Path) -> bool:
    if not path.exists():
        return False
    changed = False
    out_lines = []
    with path.open() as f:
        for line in f:
            stripped = line.rstrip("\n")
            if not stripped:
                out_lines.append(line)
                continue
            try:
                q = json.loads(stripped)
            except json.JSONDecodeError:
                out_lines.append(line)
                continue
            if str(q.get("question_id")) == TARGET_QID:
                if q.get("most_voted_answer") != ANSWER_TEXT:
                    q["most_voted_answer"] = ANSWER_TEXT
                    if q.get("correct_answers") is None:
                        q["correct_answers"] = []
                    changed = True
            out_lines.append(json.dumps(q, ensure_ascii=False) + "\n")
    if changed:
        with path.open("w") as f:
            f.writelines(out_lines)
    return changed


def main() -> None:
    targets = [
        REPO / "data" / "dp-700.json",
        REPO / "data" / "dp-700.jsonl",
    ]
    for path in targets:
        try:
            updater = update_jsonl_file if path.suffix == ".jsonl" else update_json_file
            changed = updater(path)
            print(f"{path}: {'updated' if changed else 'no change'}")
        except Exception as exc:
            print(f"{path}: ERROR {exc}")


if __name__ == "__main__":
    main()
