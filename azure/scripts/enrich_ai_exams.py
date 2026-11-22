#!/usr/bin/env python3
"""Enrich AI-103, AI-300, and AI-500 datasets with official Microsoft Learn
skill areas, case-study group identifiers, HTML-entity cleanup, and curated
community notes for remaining non-MCQ threads.

Historical DP-600 and DP-700 datasets are intentionally never modified by this
script (see F-01 / F-02 BR-01).

Usage (from azure/ or repo root):
    python3 azure/scripts/enrich_ai_exams.py           # dry-run summary
    python3 azure/scripts/enrich_ai_exams.py --apply   # write updates to data/ai-*.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_AZURE = SCRIPTS_DIR.parent
DATA_DIR = REPO_AZURE / "data"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_study_guide as bsg  # noqa: E402
import backfill_missing_answers as bma  # noqa: E402

AI_103_SKILL_AREAS: dict[int, str] = {
    1: "Plan and manage an Azure AI solution",
    2: "Implement generative AI and agentic solutions",
    3: "Implement computer vision solutions",
    4: "Implement text analysis solutions",
    5: "Implement information extraction solutions",
}

AI_300_SKILL_AREAS: dict[int, str] = {
    2: "Design and implement an MLOps infrastructure",
    3: "Implement machine learning model lifecycle and operations",
    4: "Design and implement a GenAIOps infrastructure",
    5: "Implement generative AI quality assurance and observability",
    6: "Optimize generative AI systems and model performance",
}

AI_500_SKILL_AREAS: dict[int, str] = {
    1: "Architect multi-agent solutions",
    2: "Develop multi-agent solutions in Azure",
    3: "Evaluate, optimize, and monitor multi-agent solutions",
    4: "Secure, govern, and deploy multi-agent solutions",
}

DP_800_SKILL_AREAS: dict[int, str] = {
    1: "Design and develop database solutions",
    2: "Secure, optimize, and deploy database solutions",
    3: "Implement AI capabilities in database solutions",
}

META_CHATTER_RE = re.compile(
    r"(?:\bfound\s+in\s+exam\b|\bin\s+exam\s+today\b|\bhow\s+many\s+questions\b|"
    r"\bpassed\s+the\s+exam\b|\banyone\s+know\b|\bplease\s+share\b|"
    r"\banswer\s+of\s+examtopics\s+is\s+(?:correct|right|wrong)\b)",
    re.IGNORECASE,
)

STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "your", "you", "need",
    "must", "use", "using", "should", "which", "what", "how", "each", "select",
    "answer", "correct", "solution", "following", "requirements", "configured",
    "configure", "project", "project1", "agent", "agent1", "azure", "microsoft",
    "foundry", "model", "models", "data", "into", "when", "have", "will", "are",
}


def classify_ai_103_skill_area(q: dict[str, Any]) -> tuple[int, str]:
    """Deterministically map an AI-103 question to one of Microsoft's 5
    official AI-103 skill areas, weighting the specific prompt & choices
    heavily so case-study wrappers do not drown out question intent.
    """
    _, preamble, prompt = bsg.split_question_text(q.get("question_text", ""))
    choices_txt = " ".join(
        (c.get("text") or "") + " " + re.sub(r"<[^>]+>", " ", c.get("text_html") or "")
        for c in (q.get("choices") or [])
    )
    mv_txt = str(q.get("most_voted_answer") or "")
    comments_txt = " ".join((c.get("text") or "") for c in (q.get("comments") or [])[:2])
    primary = f"{prompt} {choices_txt} {mv_txt}".lower()
    secondary = f"{comments_txt}".lower()
    if not preamble:
        primary = f"{q.get('question_text', '')} {choices_txt} {mv_txt}".lower()

    scores: dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

    def _add(area: int, patterns: list[tuple[str, float]]) -> None:
        for pat, weight in patterns:
            if re.search(pat, primary, flags=re.IGNORECASE):
                scores[area] += weight
            elif re.search(pat, secondary, flags=re.IGNORECASE):
                scores[area] += weight * 0.35

    # Area 5: Implement information extraction solutions
    _add(
        5,
        [
            (r"content\s+understanding", 7.0),
            (r"document\s+intelligence", 7.0),
            (r"\bfield\s+(?:value\s+type|method|schema)\b", 6.0),
            (r"\b(?:invoice|invoices|receipt|receipts|procurement\s+documents|contract\s+terms|tax\s+form|w-2|id\s+document)\b", 5.0),
            (r"\b(?:prebuilt-invoice|prebuilt-layout|prebuilt-receipt|document\s+analyzer|custom\s+analyzer)\b", 6.5),
            (r"\bextract\s+structured\b|\binformation\s+extraction\b|\bform\s+recognizer\b", 5.5),
        ],
    )

    # Area 3: Implement computer vision solutions
    _add(
        3,
        [
            (r"azure\s+vision|ai\s+vision|computer\s+vision|custom\s+vision", 7.0),
            (r"\bvideo\s+generation\b|\bgenerate\s+videos?\b|client\.videos\.|\bsora\b", 7.0),
            (r"\bimage\s+generation\b|\bdall-e\b|\bgpt-image\b", 6.5),
            (r"\b(?:object\s+detection|image\s+classification|face\s+api|face\s+detection|liveness|spatial\s+analysis|optical\s+character\s+recognition|\bocr\b|read\s+api)\b", 6.0),
            (r"\bimage\s+analysis\b|\banalyze\s+images?\b|\bbounding\s+box\b", 5.5),
        ],
    )

    # Area 4: Implement text analysis solutions
    _add(
        4,
        [
            (r"analyzetext|analyze_text|textanalyticsclient|azure\s+ai\s+language|language\s+service|\bin\s+language\s+studio\b", 7.0),
            (r"\b(?:sentiment\s+analysis|opinion\s+mining|key\s+phrase|named\s+entity\s+recognition|\bner\b|entity\s+linking|language\s+detection)\b", 6.5),
            (r"\b(?:custom\s+text\s+classification|custom\s+question\s+answering|conversational\s+language\s+understanding|\bclu\b)\b", 7.0),
            (r"\b(?:translator|text\s+translation|document\s+translation|speech\s+to\s+text|text\s+to\s+speech|speech\s+service|ssml)\b", 6.5),
            (r"personally\s+identifiable\s+information\s*\(pii\)\s*detection\s+in\s+text|redact\s+pii", 4.5),
        ],
    )

    # Area 1: Plan and manage an Azure AI solution (infra, auth/RBAC, deployments/PTU, CI/CD, Responsible AI/guardrails, containers)
    _add(
        1,
        [
            (r"\b(?:prompt\s+shields?|spotlighting|content\s+filter|content\s+safety|harmful\s+content|jailbreak|indirect\s+attack|image\s+moderation|self-harm|violence\s+content)\b", 5.5),
            (r"\b(?:rbac|role-based\s+access|managed\s+identity|defaultazurecredential|entra\s+id|least\s+privilege|key-based\s+access|api\s+keys?\s+must\s+not|private\s+endpoint|virtual\s+network|customer-managed\s+key|cmk)\b", 5.0),
            (r"\b(?:provisioned\s+throughput|\bptu\b|global\s+standard|data\s+zone|standard\s+deployment|quota|rate\s+limit|tokens\s+per\s+minute|\btpm\b|cost\s+footprint|billing\s+org|disconnected\s+container|docker\s+run)\b", 5.5),
            (r"\b(?:github\s+actions|azure\s+devops|ci/cd|oidc|federated\s+credential|bicep|arm\s+template)\b", 4.5),
            (r"\bcentrally\s+manage\b.*\bcredentials\b|\bproject\s+connection\b", 4.5),
        ],
    )

    # Area 2: Implement generative AI and agentic solutions (agents, workflows, tools, memory, RAG, tracing, evals, prompt tuning)
    _add(
        2,
        [
            (r"\b(?:agent\s+service|multi-agent|orchestrat|subagent|workflow|power\s+fx|ask_question|human\s+approval|human-in-the-loop)\b", 5.0),
            (r"\b(?:tool_choice|tool\s+_choice|function\s+calling|openapi\s+tool|mcp\b|model\s+context\s+protocol|code\s+interpreter|bing\s+search|file\s+search)\b", 5.5),
            (r"\b(?:conversation\s+history|agent\s+memory|memory_tool|thread|threads|session\s+state)\b", 5.0),
            (r"\b(?:retrieval-augmented|\brag\b|vector\s+search|semantic\s+ranker|hybrid\s+search|groundedness|reflection\s+pass|temperature|top_p)\b", 4.8),
            (r"\b(?:opentelemetry|application\s+insights|traces\s+tab|latency\s+breakdown|span\s+attributes|hierarchical\s+spans|observability)\b", 4.8),
        ],
    )

    best_area = max(scores, key=lambda k: (scores[k], k == 2))
    if scores[best_area] == 0.0:
        best_area = 2
    return best_area, AI_103_SKILL_AREAS[best_area]


def classify_dp_800_skill_area(q: dict[str, Any]) -> tuple[int, str]:
    """Deterministically map a DP-800 question to one of Microsoft's 3 official
    DP-800 skill areas when ExamTopics places it in a flat or case-study topic.
    """
    _, preamble, prompt = bsg.split_question_text(q.get("question_text", ""))
    choices_txt = " ".join(
        (c.get("text") or "") + " " + re.sub(r"<[^>]+>", " ", c.get("text_html") or "")
        for c in (q.get("choices") or [])
    )
    mv_txt = str(q.get("most_voted_answer") or "")
    comments_txt = " ".join((c.get("text") or "") for c in (q.get("comments") or [])[:2])
    primary = f"{prompt} {choices_txt} {mv_txt}".lower()
    secondary = comments_txt.lower()
    if not preamble:
        primary = f"{q.get('question_text', '')} {choices_txt} {mv_txt}".lower()

    scores: dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0}

    def _add(area: int, patterns: list[tuple[str, float]]) -> None:
        for pat, weight in patterns:
            if re.search(pat, primary, flags=re.IGNORECASE):
                scores[area] += weight
            elif re.search(pat, secondary, flags=re.IGNORECASE):
                scores[area] += weight * 0.35

    # Area 3: Implement AI capabilities in database solutions
    _add(
        3,
        [
            (r"\b(?:vector_distance|vector_search|vector_normalize|vectorproperty|ai_generate_embeddings|ai_generate_chunks)\b", 8.0),
            (r"\b(?:external\s+model|create\s+external\s+model|alter\s+external\s+model|sp_invoke_external_rest_endpoint)\b", 7.5),
            (r"\b(?:embedding|embeddings|vector\s+index|vector\s+data\s+type|\bvector\s*\(\s*\d+\s*\)|diskann|\bann\b|\benn\b)\b", 6.5),
            (r"\b(?:hybrid\s+search|reciprocal\s+rank\s+fusion|\brrf\b|full-text\s+search|semantic\s+search|retrieval-augmented|\brag\b|chunking)\b", 6.0),
        ],
    )

    # Area 2: Secure, optimize, and deploy database solutions
    _add(
        2,
        [
            (r"\b(?:always\s+encrypted|dynamic\s+data\s+masking|masked\s+with|row-level\s+security|\brls\b|security\s+policy|ledger\s+digest|auditing)\b", 7.0),
            (r"\b(?:managed\s+identity|passwordless|database\s+scoped\s+credential|grant\s+|deny\s+|revoke\s+|least\s+privilege)\b", 5.5),
            (r"\b(?:query\s+store|execution\s+plan|deadlock|blocking|isolation\s+level|read\s+committed|snapshot\s+isolation|\bdmv\b|sys\.dm_)\b", 6.5),
            (r"\b(?:sql\s+database\s+project|dacpac|sqlproj|sqlpackage|schema\s+drift|ci/cd|github\s+actions)\b", 6.5),
            (r"\b(?:data\s+api\s+builder|\bdab\b|dab-config|graphql|change\s+event\s+streaming|\bces\b|change\s+data\s+capture|\bcdc\b|change\s+tracking|sql\s+trigger\s+binding|application\s+insights|log\s+analytics)\b", 6.5),
        ],
    )

    # Area 1: Design and develop database solutions
    _add(
        1,
        [
            (r"\b(?:json_object|json_array|json_arrayagg|json_objectagg|json_contains|openjson|json_value|json_query|json_path_exists|json\s+index)\b", 7.0),
            (r"\b(?:regexp_like|regexp_replace|regexp_substr|regexp_instr|regexp_count|regexp_matches|regexp_split_to_table)\b", 7.0),
            (r"\b(?:edit_distance|edit_distance_similarity|jaro_winkler|soundex)\b", 7.0),
            (r"\b(?:columnstore|temporal\s+table|system_versioning|in-memory\s+oltp|memory_optimized|graph\s+table|\bmatch\s*\(|create\s+sequence|partition\s+function|partition\s+scheme)\b", 6.5),
            (r"\b(?:window\s+function|over\s*\(|row_number|rank\s*\(|dense_rank|lag\s*\(|lead\s*\(|common\s+table\s+expression|\bcte\b|stored\s+procedure|table-valued\s+function|scalar\s+function|try\s*\.\.\.\s*catch|begin\s+try|xact_abort)\b", 5.5),
            (r"\b(?:github\s+copilot|copilot\s+in\s+fabric|instruction\s+file|\.instructions\.md|copilot-instructions|mcp\s+server)\b", 6.0),
        ],
    )

    best_area = max(scores, key=lambda k: (scores[k], k == 1))
    if scores[best_area] == 0.0:
        best_area = 1
    return best_area, DP_800_SKILL_AREAS[best_area]


def detect_case_study_group(q: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return ``(case_study_id, case_study_title)`` if ``q`` is a case study."""
    _, preamble, _ = bsg.split_question_text(q.get("question_text", ""))
    if not preamble:
        return None, None
    exam = (q.get("exam") or "").lower()
    m = re.search(
        r"\b(Contoso(?:,\s*Ltd\.?)?|Fabrikam(?:\s+Inc\.?)?|Litware(?:,\s*Inc\.?)?|Tailspin\s+Toys|Northwind\s+Traders|Wide\s+World\s+Importers|Adatum(?:\s+Corporation)?|Relecloud)\b",
        preamble,
    )
    if m:
        raw_company = m.group(1).rstrip(".")
        if "Contoso" in raw_company and "health provider" in preamble.lower():
            return f"{exam}-contoso-health", "Contoso Health"
        slug = re.sub(r"[^a-z0-9]+", "-", raw_company.lower()).strip("-")
        return f"{exam}-{slug}", raw_company
    return f"{exam}-case-study-{q.get('topic', 1)}", "Case Study"


def _extract_community_note(q: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    """Select the strongest relevant community answer/note for a non-MCQ question."""
    comments = q.get("comments") or []
    if not comments:
        return None, None

    _, _, prompt = bsg.split_question_text(q.get("question_text", ""))
    q_tokens = {
        tok
        for tok in re.findall(r"[a-z0-9_]{4,}", (prompt + " " + q.get("question_text", "")).lower())
        if tok not in STOPWORDS
    }

    best_comment: dict[str, Any] | None = None
    best_score = -1.0
    best_confidence = "community_note"

    for c in comments:
        raw_text = html.unescape(c.get("text") or "").strip()
        if len(raw_text) < 8:
            continue
        low = raw_text.lower()
        if META_CHATTER_RE.search(low):
            continue
        if low in {"correct", "agree", "thanks", "thank you", "yes", "no"}:
            continue
        if raw_text.endswith("?") and "→" not in raw_text and "=>" not in raw_text and ":" not in raw_text:
            continue

        upvotes = int(c.get("upvotes") or 0)
        hv = "Highly Voted" in (c.get("badges") or [])
        c_tokens = set(re.findall(r"[a-z0-9_]{4,}", low)) - STOPWORDS
        overlap = len(q_tokens & c_tokens)

        has_structure = bool(
            re.search(
                r"(?:→|=>|->|\b(?:box|statement|pipeline|slot|step)\s*\d+\s*:|^\s*\d+[.)]\s+|^\s*[YN]{3,5}\b|\banswer\s*:?)",
                raw_text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
        )

        # Reject off-topic comments that have zero domain overlap AND no structured slot mapping
        if overlap == 0 and not has_structure:
            continue

        score = upvotes * 3.0 + (20.0 if hv else 0.0) + (12.0 if has_structure else 0.0) + min(overlap * 2.5, 20.0)
        if low.startswith("i think"):
            score -= 6.0

        if score > best_score:
            best_score = score
            best_comment = c
            best_confidence = "consensus" if (upvotes >= 2 or hv) else "community_note"

    if best_comment is None or best_score <= 0:
        return None, None

    formatted = bma._format_answer(best_comment.get("text") or "")
    if not formatted:
        return None, None
    meta = {
        "comment_id": best_comment.get("comment_id"),
        "upvotes": int(best_comment.get("upvotes") or 0),
        "confidence": best_confidence,
        "pattern": "ai_community_enrichment",
    }
    return formatted, meta


def enrich_exam_records(exam: str, records: list[dict[str, Any]]) -> dict[str, int]:
    stats = Counter()
    dp800_distinct_topics = (
        {int(q.get("topic") or 0) for q in records} if exam == "dp-800" else set()
    )
    dp800_has_multi_domain_topics = bool(dp800_distinct_topics & {2, 3})
    for q in records:
        # 1. Unescape HTML entities in existing most_voted_answer
        mv = q.get("most_voted_answer")
        if isinstance(mv, str) and ("&" in mv):
            unescaped = bma.unescape_clean(mv)
            if unescaped != mv:
                q["most_voted_answer"] = unescaped
                stats["unescaped_answers"] += 1

        # 2. Skill area classification
        if exam == "ai-103":
            area_id, area_label = classify_ai_103_skill_area(q)
        elif exam == "ai-300":
            t = int(q.get("topic") or 2)
            area_id = t if t in AI_300_SKILL_AREAS else 2
            area_label = AI_300_SKILL_AREAS[area_id]
        elif exam == "ai-500":
            t = int(q.get("topic") or 1)
            area_id = t if t in AI_500_SKILL_AREAS else 1
            area_label = AI_500_SKILL_AREAS[area_id]
        elif exam == "dp-800":
            t = int(q.get("topic") or 0)
            if dp800_has_multi_domain_topics and t in DP_800_SKILL_AREAS:
                area_id, area_label = t, DP_800_SKILL_AREAS[t]
            else:
                area_id, area_label = classify_dp_800_skill_area(q)
        else:
            continue

        q["skill_area"] = area_id
        q["skill_area_label"] = area_label
        stats[f"skill_{area_id}"] += 1

        # 3. Case study group metadata
        cs_id, cs_title = detect_case_study_group(q)
        if cs_id and cs_title:
            q["case_study_id"] = cs_id
            q["case_study_title"] = cs_title
            stats["case_studies"] += 1

        # 4. Backfill remaining non-MCQ answers from substantive comments
        if not q.get("choices") and not q.get("most_voted_answer"):
            note, meta = _extract_community_note(q)
            if note and meta:
                q["most_voted_answer"] = note
                q["_backfill_source"] = meta
                stats["backfilled_non_mcq"] += 1
            else:
                stats["still_missing_non_mcq"] += 1

    return dict(stats)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write enriched records back to data/*.json")
    parser.add_argument(
        "--exams",
        nargs="+",
        default=["ai-103", "ai-300", "ai-500", "dp-800"],
        help="Exam slugs to enrich (default: ai-103 ai-300 ai-500 dp-800)",
    )
    args = parser.parse_args()

    for exam in [e.lower() for e in args.exams]:
        path = DATA_DIR / f"{exam}.json"
        if not path.exists():
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        stats = enrich_exam_records(exam, records)
        print(f"{exam.upper()}: {stats}")
        if args.apply:
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
            jsonl_path = path.with_suffix(".jsonl")
            jsonl_tmp = path.with_suffix(".jsonl.tmp")
            jsonl_tmp.write_text(
                "\n".join(json.dumps(rec, ensure_ascii=False) for rec in records) + "\n",
                encoding="utf-8",
            )
            jsonl_tmp.replace(jsonl_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
