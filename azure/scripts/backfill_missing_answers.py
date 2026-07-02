#!/usr/bin/env python3
"""Backfill ``most_voted_answer`` for HOTSPOT/DRAG DROP questions.

ExamTopics questions with ``choices == []`` and ``most_voted_answer is None``
were skipped by the lettered-MCQ crawler, so the study guide renders them with
a "Not provided" placeholder. This script scans the discussion comments and
promotes the strongest answer candidate into ``most_voted_answer`` so the
guide can show real answer text.

Candidate scoring (in priority order):

a. Explicit answer-label patterns: ``"First dropdown:"``, ``"Second dropdown:"``,
   ``"First box:"``, ``"Second box:"``, ``"Answer:"``, ``"The answer is:"``,
   ``"Correct answer:"``, ``"Selected Answer:"``, ``"=>"``, ``"->"``.
b. Comments carrying the ``Highly Voted`` badge.
c. Upvote count (tie-breaker).
d. Skip comments that are clearly questions (``"?"``, ``"Is this"``,
   ``"Does anyone"``, ``"Can someone"``, ``"Why"``, ``"How"``).

A comment is only promoted when it scores high enough — either it matches an
explicit answer pattern, or it carries the ``Highly Voted`` badge. This keeps
false positives low: only comments the community already marked as the
consensus answer are used.

Usage (from repo root):

    # Preview changes only (default) — does not mutate the JSON.
    python scripts/backfill_missing_answers.py

    # Apply changes:
    python scripts/backfill_missing_answers.py --apply
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
TARGETS = [
    DATA / "dp-600.json",
    DATA / "dp-700.json",
]

# Explicit answer-label patterns. Matched case-insensitively against the whole
# comment text. Any of these is a strong signal that the comment is stating the
# answer to a HOTSPOT/DRAG DROP slot.
ANSWER_PATTERNS = (
    "first dropdown",
    "second dropdown",
    "first box",
    "second box",
    "first select",
    "second select",
    "first option",
    "second option",
    "answer:",  # matches "Answer:" label
    "the answer is",
    "correct answer",
    "selected answer",
    "answer is",
)

# Arrow separators used heavily in DRAG DROP answer posts.
ARROW_PATTERNS = ("=>", "->")

# Comment prefixes that mean "this is a question, not an answer".
QUESTION_PREFIXES = (
    "?",
    "is this",
    "does anyone",
    "can someone",
    "why",
    "how",
)

# Score thresholds:
#   EXPLICIT_SCORE + upvote nudge ⇒ comment matched an explicit pattern
#   HV_SCORE + upvote nudge ⇒ comment was flagged Highly Voted
EXPLICIT_SCORE = 100
HV_SCORE = 50
UPVOTE_WEIGHT = 0.5

# Comment must have at least one of these signals. Anything lower is too
# speculative to publish as "most voted answer".
MIN_ACCEPT_SCORE = 50

MAX_ANSWER_LEN = 500


logger = logging.getLogger("backfill_answers")


def _backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        logger.info("Created backup %s", bak)


def _load(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _normalized(text: str) -> str:
    return text.strip().lower()


def _looks_like_question(text: str) -> bool:
    n = _normalized(text)
    return any(n.startswith(p) for p in QUESTION_PREFIXES)


def _matches_explicit_pattern(text: str) -> bool:
    n = _normalized(text)
    if any(p in n for p in ANSWER_PATTERNS):
        return True
    if any(p in text for p in ARROW_PATTERNS):
        return True
    return False


def _has_highly_voted(comment: dict[str, Any]) -> bool:
    return "Highly Voted" in (comment.get("badges") or [])


def _score_comment(comment: dict[str, Any]) -> float | None:
    """Return the candidate score, or None if the comment should be skipped."""
    text = comment.get("text", "") or ""
    if not text.strip():
        return None
    if _looks_like_question(text):
        return None
    if text.strip().lower() in {"ok", "thanks", "thank you", "agree", "correct", "yes", "no"}:
        return None
    score = 0.0
    if _matches_explicit_pattern(text):
        score += EXPLICIT_SCORE
    if _has_highly_voted(comment):
        score += HV_SCORE
    score += (comment.get("upvotes") or 0) * UPVOTE_WEIGHT
    return score


def _format_answer(text: str) -> str:
    """Single-line, truncated to MAX_ANSWER_LEN, with newlines collapsed."""
    cleaned = text.replace("\r", " ").replace("\n", " | ")
    cleaned = " ".join(cleaned.split())  # collapse runs of whitespace
    if len(cleaned) > MAX_ANSWER_LEN:
        cleaned = cleaned[: MAX_ANSWER_LEN - 3].rstrip() + "..."
    return cleaned


# Bare confirmation strings — meta-comments that say "the existing answer is
# right" without actually stating the answer. Even when pattern-matched, they
# carry no information for our study guide.
BARE_CONFIRMATIONS = {
    "correct",
    "correct.",
    "correct!",
    "correct :)",
    "all correct",
    "all correct.",
    "all four answers are correct",
    "all four answers are correct.",
    "i agree",
    "i agree.",
    "i agree!",
    "i agree with the answer",
    "i agree with the answer given",
    "i agree with the provided answer",
    "correct answer",
    "answer is correct",
    "answer is correct.",
    "answer is correct :)",
    "the answer is correct",
    "is correct",
}


def _looks_like_bare_confirmation(text: str) -> bool:
    return text.strip().lower() in BARE_CONFIRMATIONS


def _pick_candidate(comments: list[dict[str, Any]]) -> tuple[dict[str, Any], float] | tuple[None, None]:
    best: dict[str, Any] | None = None
    best_score = -1.0
    for c in comments:
        text = c.get("text", "") or ""
        if _looks_like_bare_confirmation(text):
            continue
        s = _score_comment(c)
        if s is None:
            continue
        if s > best_score:
            best = c
            best_score = s
    if best is None or best_score < MIN_ACCEPT_SCORE:
        return None, None
    return best, best_score


def _snippet(text: str, n: int = 90) -> str:
    flat = text.replace("\n", " ").replace("|", "/")
    flat = " ".join(flat.split())
    return flat[:n] + ("..." if len(flat) > n else "")


def process_file(path: Path, *, apply: bool) -> dict[str, Any]:
    data = _load(path)
    eligible = [
        q
        for q in data
        if not q.get("choices")
        and not q.get("most_voted_answer")
    ]
    logger.info(
        "%s: %d eligible questions (no choices, no most_voted_answer)",
        path.name,
        len(eligible),
    )

    updates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    signal_counts: Counter[str] = Counter()

    for q in eligible:
        comments = q.get("comments") or []
        candidate, score = _pick_candidate(comments)
        if candidate is None:
            skipped.append({
                "question_id": q.get("question_id"),
                "topic": q.get("topic"),
                "question_number": q.get("question_number"),
                "comment_count": len(comments),
            })
            continue

        answer_text = candidate.get("text", "")
        new_answer = _format_answer(answer_text)

        update = {
            "question_id": q.get("question_id"),
            "topic": q.get("topic"),
            "question_number": q.get("question_number"),
            "comment_id": candidate.get("comment_id"),
            "upvotes": candidate.get("upvotes"),
            "score": score,
            "explicit_match": _matches_explicit_pattern(answer_text),
            "highly_voted": _has_highly_voted(candidate),
            "answer": new_answer,
            "_snippet": _snippet(answer_text),
        }
        if update["explicit_match"] and update["highly_voted"]:
            signal_counts["explicit+highly_voted"] += 1
        elif update["explicit_match"]:
            signal_counts["explicit_pattern_only"] += 1
        elif update["highly_voted"]:
            signal_counts["highly_voted_only"] += 1
        else:
            signal_counts["other"] += 1
        updates.append(update)

        if apply:
            q["most_voted_answer"] = new_answer
            # Leave correct_answers empty — these are not lettered answers and
            # the renderer falls back to most_voted_answer for the
            # "Most voted" card.
            if not q.get("correct_answers"):
                q["correct_answers"] = []

    if apply and updates:
        _backup(path)
        _save(path, data)

    return {
        "path": path,
        "eligible": len(eligible),
        "updated": len(updates),
        "skipped": len(skipped),
        "updates": updates,
        "skipped_items": skipped,
        "signals": signal_counts,
    }


def _print_report(result: dict[str, Any]) -> None:
    path = result["path"]
    print(f"\n=== {path.name} ===")
    print(
        f"  eligible={result['eligible']}  updated={result['updated']}  "
        f"skipped={result['skipped']}"
    )
    if result["signals"]:
        print("  signals: " + ", ".join(f"{k}={v}" for k, v in result["signals"].most_common()))
    if result["updates"]:
        print("  updates:")
        for u in result["updates"]:
            tag = []
            if u["explicit_match"]:
                tag.append("pattern")
            if u["highly_voted"]:
                tag.append("HV")
            tag_str = "+".join(tag) if tag else "upvotes"
            print(
                f"    - T{u['topic']} Q{u['question_number']} "
                f"(qid={u['question_id']}, cid={u['comment_id']}, "
                f"upvotes={u['upvotes']}, score={u['score']:.1f}, signal={tag_str}) "
                f":: {u['_snippet']}"
            )
    if result["skipped_items"]:
        print(f"  skipped (no strong signal; first 5):")
        for s in result["skipped_items"][:5]:
            print(
                f"    - T{s['topic']} Q{s['question_number']} "
                f"(qid={s['question_id']}, comments={s['comment_count']})"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes to the JSON files (default: preview only).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    mode = "APPLY" if args.apply else "preview"
    print(f"\nMode: {mode}")
    print(f"Targets: {[str(p) for p in TARGETS]}")
    print(f"Min accept score: {MIN_ACCEPT_SCORE}")
    print(f"Heuristic: explicit pattern OR Highly Voted badge, after skipping question-shaped comments")

    total_updated = 0
    total_skipped = 0
    for path in TARGETS:
        if not path.exists():
            logger.warning("Skipping missing file %s", path)
            continue
        result = process_file(path, apply=args.apply)
        _print_report(result)
        total_updated += result["updated"]
        total_skipped += result["skipped"]

    print(
        f"\nSummary: updated={total_updated}  skipped={total_skipped}  "
        f"mode={mode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
