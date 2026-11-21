#!/usr/bin/env python3
"""Backfill and normalize ``most_voted_answer`` for HOTSPOT/DRAG DROP questions.

ExamTopics questions with ``choices == []`` were skipped by the lettered-MCQ
crawler, so the study guide would otherwise render them with a "Not provided"
placeholder. This script scans the discussion comments, decodes any
double-escaped HTML entities (such as ``&quot;`` or ``&gt;``), scores
answer-bearing comments, and extracts concise multi-line slot answers into
``most_voted_answer`` (preserving real ``\\n`` line breaks rather than
pipe-flattening prose into `` | ``).

Usage (from azure/ directory):

    # Preview new fills only (default) — does not mutate JSON:
    python3 scripts/backfill_missing_answers.py

    # Re-evaluate and clean existing non-MCQ backfills as well (preview):
    python3 scripts/backfill_missing_answers.py --reprocess --loose

    # Apply across all target exam datasets:
    python3 scripts/backfill_missing_answers.py --reprocess --loose --apply
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import re
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
    DATA / "ai-103.json",
    DATA / "ai-300.json",
    DATA / "ai-500.json",
]

# Exhibit-verified curated multi-slot answers for questions where top-voted
# comments either debated a single dropdown or used prose without slot labels.
CURATED_ANSWERS: dict[str, str] = {
    # DP-700 Q2.12
    "936013": (
        "First dropdown: o.OrderDate >= c.valid_from_datetime\n"
        "Second dropdown: o.OrderDate < c.valid_to_datetime"
    ),
    # AI-103 Q1.1 (EU data residency -> Standard; consistent model version -> Opt out)
    "412433": (
        "Deployment type: Standard\n"
        "Version update policy: Opt out of automatic model version upgrades"
    ),
    # AI-103 Q1.6 (Managed identity + Responses API send prompt)
    "412438": (
        "credential: DefaultAzureCredential\n"
        "openai_client.responses: create"
    ),
    # AI-103 Q1.8 (Guardrails block all 4 points + system-assigned MI blob access)
    "412440": (
        "Guardrails: Select User input, Output, Tool response, and Tool call and set Action to Block.\n"
        "Storage access: A system-assigned managed identity that is assigned the Storage Blob Data Contributor role"
    ),
    # AI-103 Q1.11 (Foundry human-in-the-loop workflow YAML)
    "412443": (
        "type: ask_question\n"
        'condition: approval == "approved"'
    ),
    # AI-103 Q1.18 (Foundry availability/limit metrics + inference diagnostic log)
    "412450": (
        "Metrics to enable: Model Availability Rate and Provisioned Utilization\n"
        "Diagnostic log to collect: RequestResponse"
    ),
    # AI-103 Q1.103 (az cognitiveservices account create with CMK JSON)
    "421549": (
        "--kind: OpenAI\n"
        "Parameter: --encryption"
    ),
}

BARE_CONFIRMATIONS = {
    "ok",
    "thanks",
    "thank you",
    "agree",
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
    "seems correct",
    "seems correct.",
    "looks correct",
    "looks correct.",
    "yes",
    "no",
    "found in exam today",
}

QUESTION_START_RE = re.compile(
    r"^\s*(?:\?|is\s+this\b|is\s+the\b|are\s+the\b|does\s+anyone\b|can\s+someone\b|"
    r"why\s+(?:is|are|not|do|does|would|did|text=)\b|how\s+(?:many|do|does|can|is|would)\b|"
    r"what\s+is\s+(?:the\s+difference|meant)\b|so\s+what\s+is\b|where\s+does\s+it\b|"
    r"i'?m\s+curious\b|am\s+i\s+missing\b)",
    re.IGNORECASE,
)

BARE_META_RE = re.compile(
    r"^\s*(?:imho[,:\s]*)?(?:just\s+\w+\s+it[.,\s]*)?(?:i\s+tried\s+this.*?so[,:\s]*)?"
    r"(?:seems\s+correct|looks\s+correct|"
    r"(?:the\s+|given\s+|provided\s+)?(?:answer|answers|solution)\s+(?:is|are)\s+"
    r"(?:correct(?:-ish)?|right|wrong|incorrect|good))\b",
    re.IGNORECASE | re.DOTALL,
)

# Detects MCQ explanations pasted onto the wrong (non-MCQ) discussion thread.
WRONG_THREAD_MCQ_RE = re.compile(
    r"correct\s+answer\s*:\s*[A-E]\s*[—–-]\s+.+(?:\([B-E]\)|\n[B-E][.)]\s)",
    re.IGNORECASE | re.DOTALL,
)

EXPLICIT_SLOT_RE = re.compile(
    r"(?:"
    r"\b(?:first|second|third|fourth|1st|2nd|3rd|4th)\s+(?:dropdown|box|select|option|target|slot|part|statement|one)\b|"
    r"\b(?:dropdown|box|slot|target|statement|pipeline|step)\s*[1-5]\s*[:=→>-]|"
    r"(?:^|\n)\s*(?:👉\s*|✅\s*)*(?:\*\*)?(?:final\s+(?:correct\s+)?(?:drag-and-drop\s+)?answers?(?:\s*\([^)]*\))?|"
    r"correct\s+answers?|correct\s+selections?|correct\s+sequence|selected\s+answer|answers?)(?:\*\*)?\s*(?:[:=]\s*\S|\n\s*\S)|"
    r"\b(?:the\s+answer\s+is|correct\s+answers?\s+(?:is|are|should\s+be)|answer\s+should\s+be)\s+(?!correct\b|right\b|wrong\b|incorrect\b)\S|"
    r"\b(?:is|are)\s+the\s+correct\s+answers?\b"
    r")",
    re.IGNORECASE,
)

HEADER_BONUS_RE = re.compile(
    r"^\s*(?:👉\s*|✅\s*)*(?:\*\*)?(?:correct\s+answers?|correct\s+selections?|correct\s+sequence|"
    r"final\s+(?:correct\s+)?(?:drag-and-drop\s+)?answers?|the\s+correct\s+answers?\s+are|"
    r"a?nswer\s+key|answers?)\b",
    re.IGNORECASE,
)

ARROW_RE = re.compile(r"(?:->|=>|-->|==>|→|⟶|⇒|\n\s*↓\s*\n)")

EXPLANATION_SECTION_RE = re.compile(
    r"^\s*(?:#+\s*)?(?:\*\*)?(?:explanations?(?:\s+of\s+steps)?|key\s+reasons?|reasons?|reasoning|"
    r"why(?:\s+not\b.*|\s*\(.*?\))?|short\s+discussion|discussion|references?|refference|sources?|"
    r"microsoft\s+documentation|note|notes|p\.?s\.?|unused|logic|step[- ]by[- ]step(?:\s+analysis)?|"
    r"here\s+is\s+the\s+reasoning|clues?)(?:\*\*)?\s*[:?-]?\s*$",
    re.IGNORECASE,
)

INLINE_EXPLANATION_PREFIX_RE = re.compile(
    r"^\s*(?:\*\*)?(?:explanations?|why\s+not|why|reasoning|key\s+reasons?|references?|refference|"
    r"sources?|microsoft\s+documentation|note|p\.?s\.?|unused|logic|clues?|link|good\s+video)\b\s*[:?-]",
    re.IGNORECASE,
)

HEADER_LINE_RE = re.compile(
    r"^\s*(?:👉\s*|✅\s*)*(?:\*\*)?(?:correct\s+answers?|correct\s+selections?|correct\s+sequence|"
    r"correct\s+metrics|the\s+correct\s+(?:full\s+)?(?:sequence|answers?|values?|order)\s*(?:is|are|should\s+be)?|"
    r"final\s+(?:correct\s+)?(?:drag-and-drop\s+)?answers?(?:\s*\([^)]*\))?|"
    r"a?nswer\s+key|answers?|correct!?|i\s+agree\.?|is\s+ok\.?|should\s+be\s+this\s+a(?:ns|sn)wer|"
    r"according\s+to\s+[\w\s.]+|per\s+[\w\s.]+|"
    r"to\s+run\s+the\s+.*?perform\s+the\s+following\s+actions\s+in\s+sequence)(?:\*\*)?\s*[:=-]?\s*$",
    re.IGNORECASE,
)

FINAL_ANSWER_BLOCK_RE = re.compile(
    r"(?:^|\n)\s*(?:👉\s*|✅\s*)*(?:\*\*)?(?:final\s+(?:correct\s+)?answers?|"
    r"conclusion\s*:\s*the\s+technically\s+correct\s+answers?\s+should\s+be|"
    r"answer|correct\s+answers?\s+(?:then\s+)?(?:should\s+be|is|are)|"
    r"therefore[,:\s]+the\s+answer.*?is|hence\s+the\s+answer)\s*(?:\*\*)?\s*[:=-]\s*(\S.+)$",
    re.IGNORECASE | re.DOTALL,
)

ARROW_PAIR_LINE_RE = re.compile(
    r"^\s*(?:[-•*]\s+|\d+[.)]\s+|\(\d+\)\s*)?"
    r"(.{2,220}?)\s*(?:-->|==>|->|=>|→|⟶|⇒)\s*(\S.{0,240})$"
)

COLON_PAIR_LINE_RE = re.compile(
    r"^\s*(?:[-•*]\s+|\d+[.)]\s+|\(\d+\)\s*)?"
    r"([A-Za-z0-9_`'\"()/.,?%+$#&=@\[\] -]{2,220}?)\s*:(?!//)\s*(\S.{0,340})$"
)

KQL_COL_DEF_RE = re.compile(
    r"^(?:string|int|long|real|bool|boolean|datetime|timespan|dynamic|guid|decimal)\s*,?$",
    re.IGNORECASE,
)

GLOSSARY_RHS_RE = re.compile(
    r"^(?:whether\s+|uses\s+a\s+|categorizes\s+|runs\s+code\s+in\s+|detects?\s+unusual\s+|controls\s+how\s+|represents\s+the\s+)",
    re.IGNORECASE,
)

NUMBERED_ITEM_RE = re.compile(
    r"^\s*(?:\d+[.,):-]\s+|\(\d+\)\s*)(\S.{0,220}?)(?<!:)$"
)

BULLET_ITEM_RE = re.compile(
    r"^\s*(?:[-•*]\s+)(\S.{1,180})$"
)

YES_NO_LIST_RE = re.compile(
    r"^\s*(?:yes|no|y|n)(?:\s*(?:,|/|\.|-\s*|\s+|->|→)\s*(?:yes|no|y|n)){1,5}\b",
    re.IGNORECASE,
)

EXCLUDED_LHS = {
    "http",
    "https",
    "explanation",
    "explanations",
    "why",
    "why not",
    "note",
    "notes",
    "reference",
    "references",
    "refference",
    "source",
    "sources",
    "reasoning",
    "clues",
    "clue",
    "unused",
    "logic",
    "link",
    "good video",
    "primary role",
    "core strength",
    "typical scenario",
    "options",
    "scenario",
}

MIN_ACCEPT_SCORE = 50.0
MAX_ANSWER_LEN = 360

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


def unescape_clean(text: str) -> str:
    """Decode HTML entities (including double-escaped 2026 ExamTopics entities)
    and normalize whitespace artifacts."""
    t = html.unescape(html.unescape(text or ""))
    t = t.replace("\r\n", "\n").replace("\r", "\n").replace("\u200b", "").replace("\xa0", " ")
    t = re.sub(r"\[\s*\[email\s+protected\]\s*\]", "[email protected]", t, flags=re.IGNORECASE)
    # Split inline triple-spaced numbered items like "(1)...   (2)...   (3)..."
    t = re.sub(r"\s{3,}(?=(?:Retrieve\s+information\s+from\s+)?\(\d+\)|\d+[.)]\s)", "\n", t)
    return t.strip()


def _convert_md_tables_and_tabs(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("|") and s.endswith("|") and s.count("|") >= 3:
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r"[-:\s]+", c or "-") for c in cells):
                continue
            if len(cells) == 2:
                c0_low = re.sub(r"[*_`]", "", cells[0]).strip().lower()
                c1_low = re.sub(r"[*_`]", "", cells[1]).strip().lower()
                if c0_low in {"requirement", "step", "item", "target", "metric", "setting", "scenario"} and c1_low in {
                    "configuration",
                    "action",
                    "value",
                    "selection",
                    "answer",
                    "válasz",
                    "option",
                    "use",
                }:
                    continue
                out.append(f"{cells[0]}: {cells[1]}")
                continue
        if "\t" in s:
            parts = [p.strip() for p in s.split("\t") if p.strip()]
            if len(parts) == 2:
                if re.fullmatch(r"(?:\d+[.)]?|[-•*])", parts[0]):
                    p0 = parts[0] if parts[0].endswith((".", ")")) else parts[0] + "."
                    out.append(f"{p0} {parts[1]}")
                else:
                    out.append(f"{parts[0]}: {parts[1]}")
                continue
        out.append(ln)
    return "\n".join(out)


def _strip_md_inline(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s).strip()


def _parse_pair_line(ln: str) -> tuple[str, str, str] | None:
    """Return ``(lhs, sep, rhs)`` if ``ln`` is a clean ``Label: Value`` or ``Label → Value`` pair."""
    # Prefer arrow separator first (handles "Statement 1: ... → Yes")
    m_arr = ARROW_PAIR_LINE_RE.match(ln)
    if m_arr:
        lhs = m_arr.group(1).strip().rstrip(".")
        rhs = m_arr.group(2).strip().rstrip(":")
        if lhs.lower() in EXCLUDED_LHS:
            return None
        return lhs, " → ", rhs

    m_col = COLON_PAIR_LINE_RE.match(ln)
    if not m_col:
        return None
    lhs = m_col.group(1).strip().rstrip(".")
    rhs = m_col.group(2).strip().rstrip(":")
    lhs_low = lhs.lower()
    if lhs_low in EXCLUDED_LHS:
        return None
    if KQL_COL_DEF_RE.match(rhs):
        return None
    if GLOSSARY_RHS_RE.match(rhs) and len(rhs.split()) >= 7:
        return None
    if len(lhs.split()) > 12 and not re.match(r"^(?:yes|no)\b", rhs, re.I):
        return None
    return lhs, ": ", rhs


def _count_structured_lines(text: str) -> tuple[int, int, int, bool]:
    norm = _convert_md_tables_and_tabs(unescape_clean(text))
    lines = [ln.strip() for ln in norm.splitlines() if ln.strip()]
    pairs = 0
    arrow_pairs = 0
    nums = 0
    for ln in lines:
        if EXPLANATION_SECTION_RE.match(ln) or INLINE_EXPLANATION_PREFIX_RE.match(ln):
            continue
        vp = _parse_pair_line(ln)
        if vp:
            pairs += 1
            if vp[1] == " → ":
                arrow_pairs += 1
        if NUMBERED_ITEM_RE.match(ln):
            nums += 1
    has_yn = bool(YES_NO_LIST_RE.match(lines[0])) if lines else False
    return pairs, arrow_pairs, nums, has_yn


def _format_answer(raw_text: str) -> str:
    """Extract a concise, newline-separated answer from a comment body."""
    text = _convert_md_tables_and_tabs(unescape_clean(raw_text))
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not re.match(r"^https?://\S+$", ln, re.I)]
    if not lines:
        return ""

    # Merge "Heading:\nValue" or "1. Heading\n✅ Selection"
    merged_lines: list[str] = []
    idx = 0
    while idx < len(lines):
        cur = lines[idx]
        if idx + 1 < len(lines):
            nxt = lines[idx + 1]
            if nxt.startswith("✅") and not cur.startswith("✅") and ":" not in cur and "→" not in cur:
                merged_lines.append(f"{cur.rstrip('.')}: {nxt}")
                idx += 2
                continue
            if (
                cur.endswith(":")
                and not HEADER_LINE_RE.match(cur)
                and not EXPLANATION_SECTION_RE.match(cur)
                and not INLINE_EXPLANATION_PREFIX_RE.match(cur)
                and not re.match(r"^(?:the\s+|these\s+|this\s+|that\s+|here\s+|again\b)", cur, re.I)
                and len(cur) <= 95
                and len(nxt) <= 95
                and not nxt.endswith(":")
                and not _parse_pair_line(nxt)
            ):
                merged_lines.append(f"{cur} {nxt}")
                idx += 2
                continue
        merged_lines.append(cur)
        idx += 1
    lines = merged_lines

    # Concise first-line Yes/No list ("YES NO NO", "Yes, No, Yes", "NNY")
    if re.fullmatch(
        r"(?:yes|no)(?:\s*(?:,|/|\.|-\s*|\s+|->|→)\s*(?:yes|no)){1,5}[.:!]?",
        lines[0],
        re.I,
    ):
        tokens = [t.capitalize() for t in re.findall(r"(?:yes|no)", lines[0], re.I)]
        return ", ".join(tokens)
    if re.fullmatch(r"[YN]{3,5}\b", lines[0]):
        tokens = ["Yes" if ch == "Y" else "No" for ch in lines[0].strip()]
        return ", ".join(tokens)

    # Repeated per-slot "Answer: X" / "So answer = X" blocks
    joined = "\n".join(lines)
    multi_ans_matches = list(
        re.finditer(r"(?:^|\n)\s*(?:so\s+)?answer\s*[:=]\s*([^\n]+)", joined, re.I)
    )
    if len(multi_ans_matches) >= 2:
        items = [
            f"Slot {i + 1}: {_strip_md_inline(m.group(1).strip().rstrip('.'))}"
            for i, m in enumerate(multi_ans_matches)
        ]
        return "\n".join(items)

    # Explicit trailing "Final Answer: ..." block when prefix is prose
    m_final = FINAL_ANSWER_BLOCK_RE.search(joined)
    if m_final and len(multi_ans_matches) <= 1:
        prefix = joined[: m_final.start()].strip()
        tail = m_final.group(1).strip()
        tail_lines: list[str] = []
        for tl in tail.splitlines():
            tl_s = _strip_md_inline(tl.strip())
            if not tl_s or re.match(r"^https?://\S+$", tl_s, re.I):
                continue
            if EXPLANATION_SECTION_RE.match(tl_s) or INLINE_EXPLANATION_PREFIX_RE.match(tl_s):
                break
            tail_lines.append(tl_s)
        prefix_pairs = [ln for ln in prefix.splitlines() if _parse_pair_line(ln)]
        if tail_lines and len("\n".join(tail_lines)) <= 240 and len(prefix_pairs) < 2:
            return "\n".join(tail_lines)

    while lines and HEADER_LINE_RE.match(lines[0]):
        lines.pop(0)
    if not lines:
        return ""

    kept: list[str] = []
    for ln in lines:
        if EXPLANATION_SECTION_RE.match(ln):
            if kept:
                break
            continue
        if INLINE_EXPLANATION_PREFIX_RE.match(ln):
            if kept:
                continue
        if not kept:
            ln = re.sub(
                r"^(?:👉\s*|✅\s*)*(?:\*\*)?(?:the\s+correct\s+answers?\s+(?:are|is)|"
                r"correct\s+answers?\s*(?:is|are|should\s+be)?|answer\s+should\s+be|"
                r"final\s+answer|answers?)(?:\*\*)?\s*[:=-]\s*",
                "",
                ln,
                flags=re.IGNORECASE,
            ).strip()
            if not ln:
                continue
        kept.append(_strip_md_inline(ln))

    if not kept:
        kept = [_strip_md_inline(ln) for ln in lines]

    # 1) Label: Value / Label → Value pairs
    pair_lines: list[str] = []
    seen_lhs_base: set[str] = set()
    for ln in kept:
        vp = _parse_pair_line(ln)
        if vp:
            lhs, sep, rhs = vp
            lhs_base = re.sub(r"\s*\([^)]*\)\s*$", "", lhs).strip().lower()
            if lhs_base in seen_lhs_base and "(" in lhs and len(rhs) > 55:
                continue
            if (
                pair_lines
                and sep == ": "
                and len(rhs) > 90
                and re.match(r"^(?:Detect|Controls|Represents|Provides|Analyzes|In\s+Azure|The\s+)\b", rhs)
            ):
                continue
            if " | " in rhs and len(rhs.split(" | ")[0]) >= 3:
                rhs = rhs.split(" | ")[0].strip()
            rhs_short = re.sub(r"\s*\([^()]{30,}\)\.?$", "", rhs).strip()
            seen_lhs_base.add(lhs_base)
            pair_lines.append(f"{lhs}{sep}{rhs_short}")
    if len(pair_lines) >= 2:
        return "\n".join(pair_lines)

    # 2) Numbered items
    numbered_idxs = [i for i, ln in enumerate(kept) if NUMBERED_ITEM_RE.match(ln)]
    if len(numbered_idxs) >= 2:
        num_lines = []
        for i in numbered_idxs:
            nl = re.sub(r"^(\d+),(\s+)", r"\1.\2", kept[i])
            nl = re.sub(r"\s*\([^()]{30,}\)\.?$", "", nl).strip()
            num_lines.append(nl)
        if all(len(nl) <= 170 for nl in num_lines):
            return "\n".join(num_lines)

    # 3) Bullet list of steps
    bullet_lines = [ln for ln in kept if BULLET_ITEM_RE.match(ln)]
    if len(bullet_lines) >= 2 and all(len(bl) <= 160 for bl in bullet_lines):
        cleaned_bullets = [
            re.sub(r"\s*\([^()]{30,}\)\.?$", "", bl).strip() for bl in bullet_lines
        ]
        return "\n".join(cleaned_bullets)

    # 4) Vertical arrow flow ("Step 1\n↓\nStep 2")
    if "↓" in kept:
        flow_steps = [ln for ln in kept if ln != "↓" and not ln.endswith(":")]
        if len(flow_steps) >= 2:
            return " → ".join(flow_steps)

    # Strip trailing rhetorical question if preceded by declarative answer
    if len(kept) == 1 and kept[0].endswith("?") and ". " in kept[0]:
        sents = kept[0].split(". ")
        non_q = [s for s in sents if not s.strip().endswith("?")]
        if non_q:
            kept = [". ".join(non_q).strip() + "."]

    result = "\n".join(kept)
    if len(result) > MAX_ANSWER_LEN:
        acc: list[str] = []
        total = 0
        for ln in kept:
            if total + len(ln) > MAX_ANSWER_LEN and acc:
                break
            acc.append(ln)
            total += len(ln) + 1
        result = "\n".join(acc)
        if len(result) > MAX_ANSWER_LEN:
            result = result[: MAX_ANSWER_LEN - 3].rsplit(" ", 1)[0] + "..."
    return result


def _pick_candidate(
    comments: list[dict[str, Any]], *, loose: bool = False
) -> tuple[dict[str, Any] | None, float | None, str]:
    """Return ``(best_comment, score, pattern_label)`` or ``(None, None, '')``."""
    best: dict[str, Any] | None = None
    best_score = -1.0
    best_pattern = ""

    for c in comments:
        raw = c.get("text", "") or ""
        text = unescape_clean(raw)
        if not text:
            continue
        low = text.lower().strip()
        if low in BARE_CONFIRMATIONS:
            continue
        if QUESTION_START_RE.match(text):
            continue
        if text.endswith("?"):
            non_q_sents = [
                s for s in re.split(r"(?<=[.!])\s+", text) if s.strip() and not s.strip().endswith("?")
            ]
            if not non_q_sents:
                continue
        if WRONG_THREAD_MCQ_RE.search(text):
            continue

        pairs, arrow_pairs, nums, has_yn = _count_structured_lines(text)
        has_explicit = bool(EXPLICIT_SLOT_RE.search(text))
        has_arrow = bool(ARROW_RE.search(text))
        has_header = bool(HEADER_BONUS_RE.match(text))
        hv = "Highly Voted" in (c.get("badges") or [])
        upvotes = max(0, int(c.get("upvotes") or 0))

        if BARE_META_RE.match(text) and pairs < 2 and nums < 2 and not has_arrow:
            continue

        first_line = text.splitlines()[0].strip().lower().rstrip(":.")
        if (
            first_line in {"correct answer", "correct answers", "answer"}
            and pairs < 2
            and nums < 2
            and not has_arrow
            and not has_yn
        ):
            continue

        is_structured = (
            has_explicit
            or has_arrow
            or (loose and (pairs >= 2 or nums >= 2 or has_yn))
            or (pairs >= 2 and (hv or upvotes >= 2 or has_header))
            or (nums >= 2 and (hv or upvotes >= 2 or has_header))
        )

        score: float | None = None
        pattern = ""

        if is_structured:
            score = 100.0
            if pairs >= 2:
                score += 12.0 + min(pairs, 4) * 2.0 + (6.0 if arrow_pairs >= 1 else 0.0)
                pattern = "loose:label_pair" if not (has_explicit or has_arrow) else "explicit_pattern"
            elif nums >= 2:
                score += 10.0 + min(nums, 4) * 1.5
                pattern = "loose:numbered_list" if not has_explicit else "explicit_pattern"
            elif has_explicit or has_arrow:
                score += 6.0
                pattern = "explicit_pattern"
            elif has_yn:
                score += 5.0
                pattern = "loose:yes_no_comma_list"

            if has_header:
                score += 8.0
            if hv:
                score += 45.0
            score += min(upvotes, 25) * 4.0

            if not hv and upvotes < 2:
                if low.startswith("i think"):
                    continue
                extracted = _format_answer(text)
                if not has_header and pairs < 2 and not has_arrow and not has_explicit:
                    if any(len(ln) > 95 for ln in extracted.splitlines()):
                        continue
        else:
            if any(joke in low for joke in ("lol", "haha", "curious how", "li mortacci")):
                continue
            lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("http")]
            if loose and not hv and upvotes >= 5 and 2 <= len(lines) <= 5 and all(len(ln) <= 90 for ln in lines):
                score = 85.0 + min(upvotes, 20) * 1.0
                pattern = "loose:short_bullet_list"
            elif hv:
                score = 50.0 + min(upvotes, 20) * 0.5
                pattern = "highly_voted"

        if score is not None and score >= MIN_ACCEPT_SCORE and score > best_score:
            best = c
            best_score = score
            best_pattern = pattern

    if best is None or best_score < MIN_ACCEPT_SCORE:
        return None, None, ""
    return best, best_score, best_pattern


def _snippet(text: str, n: int = 90) -> str:
    flat = text.replace("\n", " / ")
    flat = " ".join(flat.split())
    return flat[:n] + ("..." if len(flat) > n else "")


def process_file(
    path: Path,
    *,
    apply: bool,
    loose: bool = False,
    reprocess: bool = False,
) -> dict[str, Any]:
    data = _load(path)

    # Normalize double-escaped HTML entities inside comment bodies too so
    # rendered discussion blocks never leak ``&quot;`` / ``&gt;``.
    comments_unescaped = 0
    for q in data:
        for c in q.get("comments") or []:
            old_t = c.get("text") or ""
            if "&" in old_t:
                new_t = html.unescape(html.unescape(old_t))
                if new_t != old_t:
                    comments_unescaped += 1
                    if apply:
                        c["text"] = new_t

    eligible = [
        q
        for q in data
        if not q.get("choices")
        and (reprocess or not q.get("most_voted_answer"))
    ]
    logger.info(
        "%s: %d eligible non-MCQ questions (reprocess=%s, comments_unescaped=%d)",
        path.name,
        len(eligible),
        reprocess,
        comments_unescaped,
    )

    updates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    signal_counts: Counter[str] = Counter()

    for q in eligible:
        qid = str(q.get("question_id") or "")
        comments = q.get("comments") or []

        if qid in CURATED_ANSWERS:
            curated = CURATED_ANSWERS[qid]
            if q.get("most_voted_answer") != curated:
                signal_counts["curated"] += 1
                updates.append(
                    {
                        "question_id": qid,
                        "topic": q.get("topic"),
                        "question_number": q.get("question_number"),
                        "comment_id": "curated",
                        "upvotes": 0,
                        "score": 999.0,
                        "pattern": "curated",
                        "highly_voted": True,
                        "answer": curated,
                        "_snippet": _snippet(curated),
                    }
                )
                if apply:
                    q["most_voted_answer"] = curated
                    if not q.get("correct_answers"):
                        q["correct_answers"] = []
                    q["_backfill_source"] = {
                        "comment_id": "curated",
                        "score": 999.0,
                        "pattern": "curated",
                        "upvotes": 0,
                    }
            continue

        candidate, score, pattern_label = _pick_candidate(comments, loose=loose)
        if candidate is None:
            if reprocess and q.get("most_voted_answer"):
                # Clear previously backfilled false positives (e.g. bare questions).
                signal_counts["cleared_noise"] += 1
                updates.append(
                    {
                        "question_id": qid,
                        "topic": q.get("topic"),
                        "question_number": q.get("question_number"),
                        "comment_id": None,
                        "upvotes": 0,
                        "score": 0.0,
                        "pattern": "cleared_noise",
                        "highly_voted": False,
                        "answer": None,
                        "_snippet": "(cleared noisy backfill)",
                    }
                )
                if apply:
                    q["most_voted_answer"] = None
                    q.pop("_backfill_source", None)
            skipped.append(
                {
                    "question_id": qid,
                    "topic": q.get("topic"),
                    "question_number": q.get("question_number"),
                    "comment_count": len(comments),
                }
            )
            continue

        answer_text = candidate.get("text", "")
        new_answer = _format_answer(answer_text)
        if not new_answer:
            skipped.append(
                {
                    "question_id": qid,
                    "topic": q.get("topic"),
                    "question_number": q.get("question_number"),
                    "comment_count": len(comments),
                }
            )
            continue

        if q.get("most_voted_answer") == new_answer:
            continue

        signal_counts[pattern_label] += 1
        update = {
            "question_id": qid,
            "topic": q.get("topic"),
            "question_number": q.get("question_number"),
            "comment_id": candidate.get("comment_id"),
            "upvotes": candidate.get("upvotes"),
            "score": score or 0.0,
            "pattern": pattern_label,
            "highly_voted": "Highly Voted" in (candidate.get("badges") or []),
            "answer": new_answer,
            "_snippet": _snippet(new_answer),
        }
        updates.append(update)

        if apply:
            q["most_voted_answer"] = new_answer
            if not q.get("correct_answers"):
                q["correct_answers"] = []
            q["_backfill_source"] = {
                "comment_id": candidate.get("comment_id"),
                "score": score,
                "pattern": pattern_label,
                "upvotes": candidate.get("upvotes"),
            }

    if apply and (updates or comments_unescaped):
        _save(path, data)

    return {
        "path": path,
        "eligible": len(eligible),
        "updated": len(updates),
        "comments_unescaped": comments_unescaped,
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
        f"comments_unescaped={result['comments_unescaped']}  skipped={result['skipped']}"
    )
    if result["signals"]:
        print("  signals: " + ", ".join(f"{k}={v}" for k, v in result["signals"].most_common()))
    if result["updates"]:
        print("  updates:")
        for u in result["updates"][:15]:
            print(
                f"    - T{u['topic']} Q{u['question_number']} "
                f"(qid={u['question_id']}, cid={u['comment_id']}, "
                f"upvotes={u['upvotes']}, score={u['score']:.1f}, pattern={u['pattern']}) "
                f":: {u['_snippet']}"
            )
        if len(result["updates"]) > 15:
            print(f"    ... and {len(result['updates']) - 15} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes to the JSON files (default: preview only).",
    )
    parser.add_argument(
        "--loose",
        action="store_true",
        help="Also rescue structured label-pair, numbered-list, and Yes/No answers.",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Re-evaluate and clean existing non-MCQ most_voted_answer values.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Specific JSON filenames inside data/ to process (default: all TARGETS).",
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

    targets = [DATA / name for name in args.files] if args.files else TARGETS
    mode = "APPLY" if args.apply else "preview"
    loose_tag = "loose" if args.loose else "safe"
    print(f"\nMode: {mode} ({loose_tag}, reprocess={args.reprocess})")

    total_updated = 0
    total_skipped = 0
    for path in targets:
        if not path.exists():
            logger.warning("Skipping missing file %s", path)
            continue
        result = process_file(
            path, apply=args.apply, loose=args.loose, reprocess=args.reprocess
        )
        _print_report(result)
        total_updated += result["updated"]
        total_skipped += result["skipped"]

    print(
        f"\nSummary: updated={total_updated}  skipped={total_skipped}  "
        f"mode={mode} ({loose_tag})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
