import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

REPO_AZURE = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_AZURE / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import crawl_fabric_discussions as crawler_mod  # noqa: E402
import build_study_guide as builder_mod  # noqa: E402
import sync_jsonl  # noqa: E402


LIST_PAGE_HTML_ABSOLUTE = """
<html><body>
<span class="discussion-list-page-indicator">Page <strong>1</strong> of <strong>1556</strong></span>
<a href="https://www.examtopics.com/discussions/microsoft/view/435372-exam-ai-103-topic-1-question-172-discussion/">
  Exam AI-103 topic 1 question 172 discussion
</a>
<a href="https://www.examtopics.com/discussions/microsoft/view/404563-exam-ai-300-topic-2-question-15-discussion/">
  Exam AI-300 topic 2 question 15 discussion
</a>
<a href="/discussions/microsoft/view/430659-exam-ai-500-topic-1-question-3-discussion/">
  Exam AI-500 topic 1 question 3 discussion
</a>
</body></html>
"""

DISCUSSION_2026_MCQ_HTML = """
<html><body>
<div class="discussion-header-container">
  <div class="question-body mt-3 pt-3 border-top" data-id="825909">
    <p class="card-text">
      You are building a multi-agent workflow in Microsoft Foundry.<br/>
      Which two components should you configure? Each correct answer presents part of the solution.<br/>
      <br/>A.\r\n\t\t\t\t\tPrompt Shields<br/>
      <br/>B.\r\n\t\t\t\t\tModel Context Protocol (MCP) tool<br/>
      <br/>C.\r\n\t\t\t\t\tAzure Bastion<br/>
      <br/>D.\r\n\t\t\t\t\tFoundry IQ knowledge store<br/>
    </p>
    <a class="btn btn-primary" href="https://www.examtopics.com/exams/microsoft/ai-500/view/">Show Suggested Answer</a>
  </div>
</div>
<div class="comment-container" data-comment-id="101">
  <h5 class="comment-username">alice</h5>
  <span class="badge">Highly Voted</span>
  <span class="badge">Selected Answer: BD</span>
  <div class="comment-content">B and D are required for MCP tools and Foundry IQ grounding.</div>
  <span class="upvote-count">5 times</span>
</div>
<div class="comment-container" data-comment-id="102">
  <h5 class="comment-username">bob</h5>
  <span class="badge">Most Recent</span>
  <span class="badge">Selected Answer: B, D</span>
  <div class="comment-content">Agree with BD.</div>
  <span class="upvote-count">1 time</span>
</div>
<div class="comment-container" data-comment-id="103">
  <h5 class="comment-username">carol</h5>
  <span class="badge">Selected Answer: AB</span>
  <div class="comment-content">Maybe A and B?</div>
  <span class="upvote-count">0 times</span>
</div>
</body></html>
"""

DISCUSSION_2026_TEXT_ANSWER_ONLY_HTML = """
<html><body>
<div class="question-body mt-3 pt-3 border-top" data-id="825909">
  <p class="card-text">
    You have a multimodal generative model. Does this meet the goal?<br/>
    <br/>A.\r\n\t\t\t\t\tYes<br/>
    <br/>B.\r\n\t\t\t\t\tNo<br/>
  </p>
</div>
<div class="comment-container" data-comment-id="201">
  <h5 class="comment-username">CRdumps</h5>
  <div class="comment-content">The answer is B: No. Prompt Shields detect injection attempts.</div>
  <span class="upvote-count">3 times</span>
</div>
</body></html>
"""


class Crawler2026MarkupTests(unittest.TestCase):
    def test_absolute_and_relative_discussion_urls_parsed_for_ai_exams(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            c = crawler_mod.Crawler(
                output_dir=Path(tmp),
                exams={"ai-103", "ai-300", "ai-500"},
            )
            c._fetch = AsyncMock(return_value=LIST_PAGE_HTML_ABSOLUTE)  # type: ignore[method-assign]
            found, last_page = asyncio.run(c._crawl_list_page(1))
            self.assertEqual(last_page, 1556)
            self.assertEqual(len(found["ai-103"]), 1)
            self.assertEqual(len(found["ai-300"]), 1)
            self.assertEqual(len(found["ai-500"]), 1)
            # Stored path MUST be relative (/discussions/...) so BASE_URL + path is valid
            self.assertEqual(
                found["ai-103"][0]["path"],
                "/discussions/microsoft/view/435372-exam-ai-103-topic-1-question-172-discussion/",
            )

    def test_discover_urls_stops_cleanly_on_404_or_empty_streak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            c = crawler_mod.Crawler(
                output_dir=Path(tmp),
                exams={"ai-103"},
                stop_after_empty_pages=2,
            )

            async def fake_list_page(page: int):
                if page == 1:
                    return (
                        {
                            "ai-103": [
                                {
                                    "id": "435372",
                                    "exam": "ai-103",
                                    "topic": 1,
                                    "qnum": 172,
                                    "path": "/discussions/microsoft/view/435372-exam-ai-103-topic-1-question-172-discussion/",
                                    "title": "Q172",
                                }
                            ]
                        },
                        100,
                    )
                return ({"ai-103": []}, 100)

            c._crawl_list_page = fake_list_page  # type: ignore[method-assign]
            total = asyncio.run(c.discover_urls())
            self.assertEqual(total, 1)
            # Stopped after page 1 + 2 empty pages = 3 pages instead of scanning all 100
            self.assertEqual(len(c.state["list_pages_completed"]), 3)

    def test_parse_2026_inline_mcq_placeholder_qid_and_voter_badges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            c = crawler_mod.Crawler(output_dir=Path(tmp), exams={"ai-500"})
            meta = {"id": "430661", "exam": "ai-500", "topic": 2, "qnum": 20, "path": "/x/"}
            q = c._parse_discussion_html(DISCUSSION_2026_MCQ_HTML, "https://www.examtopics.com/x/", meta)
            # Static placeholder 825909 must fall back to unique discussion_id
            self.assertEqual(q.question_id, "430661")
            # Inline choices A-D extracted and stripped from question_text
            self.assertEqual([ch.letter for ch in q.choices], ["A", "B", "C", "D"])
            self.assertEqual(q.choices[1].text, "Model Context Protocol (MCP) tool")
            self.assertNotIn("Azure Bastion", q.question_text)
            # Upvotes parsed from "5 times" / "1 time"
            self.assertEqual(q.comments[0].upvotes, 5)
            self.assertEqual(q.comments[1].upvotes, 1)
            self.assertEqual(q.comments[0].selected_answer, "BD")
            self.assertEqual(q.comments[1].selected_answer, "BD")
            # Consensus resolved to BD -> correct_answers == ["B", "D"], question_type == "multiple"
            self.assertEqual(q.most_voted_answer, "BD")
            self.assertEqual(q.correct_answers, ["B", "D"])
            self.assertEqual(q.question_type, "multiple")
            self.assertTrue(q.choices[1].correct)
            self.assertTrue(q.choices[3].correct)
            self.assertFalse(q.choices[0].correct)

    def test_parse_2026_mcq_with_comment_text_answer_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            c = crawler_mod.Crawler(output_dir=Path(tmp), exams={"ai-103"})
            meta = {"id": "412457", "exam": "ai-103", "topic": 1, "qnum": 25, "path": "/y/"}
            q = c._parse_discussion_html(
                DISCUSSION_2026_TEXT_ANSWER_ONLY_HTML,
                "https://www.examtopics.com/y/",
                meta,
            )
            self.assertEqual([ch.letter for ch in q.choices], ["A", "B"])
            self.assertEqual(q.most_voted_answer, "B")
            self.assertEqual(q.correct_answers, ["B"])
            self.assertEqual(q.question_type, "single")

            # Guard against false positive on lowercase article "a" ("The answer is a service...")
            prose_html = DISCUSSION_2026_TEXT_ANSWER_ONLY_HTML.replace(
                "The answer is B: No. Prompt Shields detect injection attempts.",
                "The answer is a tough call depending on workload.",
            )
            q_false = c._parse_discussion_html(prose_html, "https://www.examtopics.com/z/", meta)
            self.assertIsNone(q_false.most_voted_answer)
            self.assertEqual(q_false.correct_answers, [])

    def test_parse_div_badge_warning_selected_answer(self) -> None:
        html_div_badge = """
        <html><body>
        <div class="question-body" data-id="825909">
          <p class="card-text">
            What should you recommend?<br/>
            <br/>A.\r\n\tEnable RBAC.<br/>
            <br/>B.\r\n\tDisable key auth.<br/>
            <br/>C.\r\n\tAdd a connection to the Azure AI Search resource.<br/>
          </p>
        </div>
        <div class="media comment-container" data-comment-id="1766337">
          <h5 class="comment-username">RICHARDALEX007</h5>
          <span class="badge badge-primary">Most Recent</span>
          <div class="badge badge-warning mt-0.5">
            Selected Answer: <span><strong>C</strong></span>
          </div>
          <div class="comment-content">A project connection centralizes credentials.</div>
          <span class="upvote-count">3 times</span>
        </div>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            c = crawler_mod.Crawler(output_dir=Path(tmp), exams={"ai-103"})
            meta = {"id": "412435", "exam": "ai-103", "topic": 1, "qnum": 3, "path": "/q3/"}
            q = c._parse_discussion_html(html_div_badge, "https://www.examtopics.com/q3/", meta)
            self.assertEqual(q.comments[0].selected_answer, "C")
            self.assertEqual(q.most_voted_answer, "C")
            self.assertEqual(q.correct_answers, ["C"])

    def test_consolidate_deduplicates_same_topic_and_qnum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            c = crawler_mod.Crawler(output_dir=out, exams={"ai-103"})
            recs = [
                {
                    "discussion_id": "400001",
                    "exam": "ai-103",
                    "topic": 1,
                    "question_number": 5,
                    "question_id": "400001",
                    "question_text": "Stem",
                    "choices": [],
                    "correct_answers": [],
                    "most_voted_answer": None,
                    "comments": [{"comment_id": "1", "text": "x", "upvotes": 0}],
                },
                {
                    "discussion_id": "400099",
                    "exam": "ai-103",
                    "topic": 1,
                    "question_number": 5,
                    "question_id": "400099",
                    "question_text": "Stem",
                    "choices": [],
                    "correct_answers": ["A"],
                    "most_voted_answer": "A",
                    "comments": [
                        {"comment_id": "2", "text": "A", "upvotes": 3},
                        {"comment_id": "3", "text": "Agree A", "upvotes": 1},
                    ],
                },
            ]
            c.consolidate_json(results={"ai-103": recs})
            saved = json.loads((out / "ai-103.json").read_text(encoding="utf-8"))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["discussion_id"], "400099")


class StudyGuideBuilderTests(unittest.TestCase):
    def test_topic_labels_defined_for_ai_103_300_500(self) -> None:
        for exam in ("ai-103", "ai-300", "ai-500"):
            self.assertIn(exam, builder_mod.TOPIC_LABELS)
            self.assertTrue(len(builder_mod.TOPIC_LABELS[exam]) >= 1)

    def test_study_guide_titles_include_full_exam_names(self) -> None:
        expected = {
            "dp-600": "DP-600 Implementing Analytics Solutions Using Microsoft Fabric Study Guide",
            "dp-700": "DP-700 Implementing Data Engineering Solutions Using Microsoft Fabric Study Guide",
            "ai-103": "AI-103 Developing AI Apps and Agents on Azure Study Guide",
            "ai-300": "AI-300 Operationalizing Machine Learning and Generative AI Solutions Study Guide",
            "ai-500": "AI-500 Designing and Implementing Multi-Agent AI Solutions Study Guide",
        }
        for exam in builder_mod.TOPIC_LABELS:
            self.assertIn(exam, builder_mod.EXAM_TITLES)
        for exam, title in expected.items():
            self.assertEqual(builder_mod.format_study_guide_title(exam), title)
            html_doc = builder_mod.build_html(exam, [])
            self.assertIn(f"<title>{title}</title>", html_doc)
            self.assertIn(f"<h1>{title}</h1>", html_doc)
            md_doc = builder_mod.build_markdown(exam, [])
            self.assertTrue(md_doc.startswith(f"# {title}\n"))
        self.assertEqual(builder_mod.format_study_guide_title("az-104"), "AZ-104 Study Guide")

    def test_code_exhibit_renders_html_fallback_not_empty(self) -> None:
        ex = {"kind": "code", "html": "<pre><code>print('hello foundry')</code></pre>", "language": "python"}
        rendered_html = builder_mod.render_exhibit(ex, 0, "Q1.1")
        self.assertIn("print(&#x27;hello foundry&#x27;)", rendered_html)
        md = builder_mod.build_markdown(
            "ai-103",
            [
                {
                    "exam": "ai-103",
                    "topic": 1,
                    "question_number": 1,
                    "question_id": "1",
                    "question_text": "Complete the code.",
                    "question_type": "hotspot",
                    "exhibits": [ex],
                    "choices": [],
                    "correct_answers": [],
                    "most_voted_answer": "print('hello foundry')",
                    "comments": [],
                }
            ],
        )
        self.assertIn("print('hello foundry')", md)

    def test_multiselect_checkbox_inferred_from_prompt_even_without_answer(self) -> None:
        q = {
            "exam": "ai-500",
            "topic": 2,
            "question_number": 7,
            "question_id": "500007",
            "question_text": "You need to configure security. Which two actions should you perform? Each correct answer presents part of the solution.",
            "question_type": "multiple",
            "choices": [
                {"letter": "A", "text": "Action 1", "correct": False, "text_html": "Action 1"},
                {"letter": "B", "text": "Action 2", "correct": False, "text_html": "Action 2"},
                {"letter": "C", "text": "Action 3", "correct": False, "text_html": "Action 3"},
            ],
            "correct_answers": [],
            "most_voted_answer": None,
            "comments": [],
        }
        rendered = builder_mod.render_question_html(q)
        self.assertIn('data-multiple="true"', rendered)
        self.assertIn('type="checkbox"', rendered)
        self.assertNotIn("Action 1<br>Action 1", rendered)

        # Single-answer tuple question ("Which three columns...") with 1 correct choice stays radio
        q_single_tuple = {
            **q,
            "question_type": "single",
            "question_text": "Which three columns should you include in DimProduct?",
            "choices": [
                {"letter": "A", "text": "Col1, Col2, and Col3", "correct": True, "text_html": "Col1, Col2, and Col3"},
                {"letter": "B", "text": "Col1, Col2, and Col4", "correct": False, "text_html": "Col1, Col2, and Col4"},
            ],
            "correct_answers": ["A"],
        }
        rendered_single = builder_mod.render_question_html(q_single_tuple)
        self.assertIn('data-multiple="false"', rendered_single)
        self.assertIn('type="radio"', rendered_single)

    def test_hotspot_js_surfaces_community_answer_when_available(self) -> None:
        html_doc = builder_mod.build_html(
            "ai-300",
            [
                {
                    "exam": "ai-300",
                    "topic": 2,
                    "question_number": 15,
                    "question_id": "404563",
                    "question_text": "HOTSPOT\nComplete the SDK v2 snippet.",
                    "question_type": "hotspot",
                    "exhibits": [],
                    "choices": [],
                    "correct_answers": [],
                    "most_voted_answer": "Path: wasbs | Type: URI_FOLDER",
                    "comments": [],
                }
            ],
        )
        self.assertIn("data-most-voted=\"Path: wasbs | Type: URI_FOLDER\"", html_doc)
        # Verify JS branch checks mostVoted for hotspot too
        self.assertRegex(html_doc, r"q\.dataset\.qtype === 'hotspot'[\s\S]{0,450}mostVoted")


class ReadabilityEngineTests(unittest.TestCase):
    def test_strip_case_study_boilerplate_removes_pearson_instructions_only(self) -> None:
        q12_data = json.loads((REPO_AZURE / "data" / "ai-103.json").read_text(encoding="utf-8"))
        q12 = next(q for q in q12_data if q["topic"] == 1 and q["question_number"] == 2)
        stripped = builder_mod.strip_case_study_boilerplate(q12["question_text"])
        self.assertNotIn("Case studies are not timed separately", stripped)
        self.assertNotIn("select the “Question” button to return to the question", stripped)
        self.assertIn("Contoso, Ltd is a multinational retail company", stripped)
        self.assertIn("Security and Compliance Requirements", stripped)

    def test_split_question_text_handles_case_studies_and_short_stems_accurately(self) -> None:
        # AI-500 Q1.3 previously leaked 1,909 chars ("When testing Claim Approval...") into prompt
        ai500 = json.loads((REPO_AZURE / "data" / "ai-500.json").read_text(encoding="utf-8"))
        q13 = next(q for q in ai500 if q["topic"] == 1 and q["question_number"] == 3)
        _, preamble_500, prompt_500 = builder_mod.split_question_text(q13["question_text"])
        self.assertIn("When testing Claim Approval", preamble_500)
        self.assertLess(len(prompt_500), 300)
        self.assertIn("You need to implement the business rule for Claim Approval", prompt_500)

        # DP-700 Q2.22 previously leaked 1,478 chars ("When the authors have new book releases...")
        dp700 = json.loads((REPO_AZURE / "data" / "dp-700.json").read_text(encoding="utf-8"))
        q222 = next(q for q in dp700 if q["topic"] == 2 and q["question_number"] == 22)
        _, preamble_700, prompt_700 = builder_mod.split_question_text(q222["question_text"])
        self.assertIn("When the authors have new book releases", preamble_700)
        self.assertLess(len(prompt_700), 350)

        # Short non-case-study question (AI-103 Q1.5, 796 chars) stays unified (no 1-sentence preamble box)
        ai103 = json.loads((REPO_AZURE / "data" / "ai-103.json").read_text(encoding="utf-8"))
        q15 = next(q for q in ai103 if q["topic"] == 1 and q["question_number"] == 5)
        labels_15, preamble_15, prompt_15 = builder_mod.split_question_text(q15["question_text"])
        self.assertIn("Drag drop", labels_15)
        self.assertEqual(preamble_15, "")
        self.assertIn("procurement documents", prompt_15)

    def test_parse_case_study_sections_and_auto_relevance_on_ai_103_q1_2(self) -> None:
        ai103 = json.loads((REPO_AZURE / "data" / "ai-103.json").read_text(encoding="utf-8"))
        q12 = next(q for q in ai103 if q["topic"] == 1 and q["question_number"] == 2)
        _, preamble, prompt = builder_mod.split_question_text(q12["question_text"])
        sections = builder_mod.parse_case_study_sections(preamble, prompt=prompt)
        titles = [s["title"] for s in sections]
        self.assertGreaterEqual(len(sections), 4)
        self.assertTrue(any("Overview" in t for t in titles))
        self.assertTrue(any("Existing Environment" in t for t in titles))
        self.assertTrue(any("Security and Compliance" in t or "Requirements" in t for t in titles))
        relevant_titles = [s["title"] for s in sections if s.get("relevant")]
        self.assertTrue(
            any("Security" in t for t in relevant_titles),
            f"Expected Security section to be marked relevant, got {relevant_titles}",
        )

    def test_smart_stem_formatting_lists_code_solution_and_notes(self) -> None:
        raw = (
            "Your service calls project_client.telemetry.get_connection_string() with enable_recording=False.\n"
            "The solution must meet the following requirements:\n"
            "Include a pipeline named Pipeline1 for standalone PDFs.\n"
            "Secrets must NOT be stored in span attributes.\n"
            "You need to implement controls to mitigate the risk.\n"
            "Solution: You configure prompt shields for indirect attacks.\n"
            "Does this meet the goal?\n"
            "To answer, select the appropriate options in the answer area.\n"
            "NOTE: Each correct selection is worth one point."
        )
        formatted = builder_mod.format_stem_html(raw)
        self.assertIn("<ul", formatted)
        self.assertIn("<li>Include a pipeline named", formatted)
        self.assertIn("<code>project_client.telemetry.get_connection_string()</code>", formatted)
        self.assertIn("<code>enable_recording=False</code>", formatted)
        self.assertIn('class="proposed-solution"', formatted)
        self.assertIn('class="exam-instruction-note"', formatted)


if __name__ == "__main__":
    unittest.main()
