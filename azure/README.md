# ExamTopics Azure & Fabric Study Guides

Crawled Microsoft Data & AI certification exam discussion questions from [examtopics.com](https://examtopics.com), converted into standalone offline HTML and Markdown study guides:

| Exam | Title | Crawled Discussions |
|---|---|---:|
| **DP-600** | Implementing Analytics Solutions Using Microsoft Fabric | 199 |
| **DP-700** | Implementing Data Engineering Solutions Using Microsoft Fabric | 139 |
| **DP-800** | Developing AI-Enabled Database Solutions | 48 |
| **AI-103** | Developing AI Apps and Agents on Azure | 161 |
| **AI-300** | Operationalizing Machine Learning and Generative AI Solutions | 107 |
| **AI-500** | Designing and Implementing Multi-Agent AI Solutions | 18 |

## Folder layout

```
.
├── assets/
│   └── exhibits/            # Downloaded offline exhibit & choice images
│       ├── ai-103/
│       ├── ai-300/
│       ├── ai-500/
│       ├── dp-600/
│       ├── dp-700/
│       └── dp-800/
├── data/                    # Crawled datasets (.json + auto-synced .jsonl)
│   ├── ai-103.{json,jsonl}
│   ├── ai-300.{json,jsonl}
│   ├── ai-500.{json,jsonl}
│   ├── dp-600.{json,jsonl}
│   ├── dp-700.{json,jsonl}
│   └── dp-800.{json,jsonl}
├── docs/
│   └── specs/               # Feature & architecture specifications
│       ├── F-01-ai-103-300-500-study-guides.md
│       ├── F-02-question-readability-and-html-app-v2.md
│       └── F-03-dp-800-study-guide.md
├── guides/                  # Student-facing offline HTML & Markdown study guides
│   ├── index.html           # Cross-exam study hub with live progress across all 6 exams
│   ├── ai-103-examtopics-study-guide.{html,md}
│   ├── ai-300-examtopics-study-guide.{html,md}
│   ├── ai-500-examtopics-study-guide.{html,md}
│   ├── dp-600-examtopics-study-guide.{html,md}
│   ├── dp-700-examtopics-study-guide.{html,md}
│   └── dp-800-examtopics-study-guide.{html,md}
├── references/              # Official Microsoft Learn study guides & posters
│   └── microsoft/
│       ├── ai-103-study-guide.md
│       ├── ai-300-study-guide.md
│       ├── ai-500-study-guide.md
│       ├── dp-600-study-guide.md
│       ├── dp-700-study-guide.md
│       ├── dp-800-study-guide.md
│       ├── certification-poster.pdf
│       └── choose-your-microsoft-credential.pdf
├── scripts/                 # Python crawler, enrichment, backfill, sync & guide builder tooling
│   ├── crawl_fabric_discussions.py
│   ├── build_study_guide.py
│   ├── enrich_ai_exams.py
│   ├── backfill_missing_answers.py
│   ├── backfill_exhibits.py
│   ├── backfill_choice_markup.py
│   ├── backfill_dragdrop.py
│   ├── sanitize_exhibit_html.py
│   ├── sync_jsonl.py
│   └── compare_with_original.py
├── state/                   # Crawler checkpoint / resume state
│   ├── state.json
│   ├── ai-exams-state.json
│   └── dp-800-state.json
└── tests/                   # Unit test suite
    └── test_crawler_and_builder.py
```

## Quick start

Open the unified Exam Hub or any individual guide directly in your browser (from `azure/`):

```bash
open guides/index.html
open guides/dp-800-examtopics-study-guide.html
open guides/ai-103-examtopics-study-guide.html
open guides/ai-300-examtopics-study-guide.html
open guides/ai-500-examtopics-study-guide.html
```

Or serve the folder locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/guides/index.html
```

## Study App v2 features

- **Structured Case Studies**: Strips Pearson VUE exam-screen boilerplate, parses sections into searchable `<details>` accordions with `Expand all / Collapse all`, auto-opens and badges sections relevant to the current prompt, uses a prompt-first 2-column split-pane inspector on wide screens, and provides a sibling jumper bar across all questions in the same case study.
- **Smart Stem Readability**: Automatically formats post-colon requirement blocks into `<ul>` checklists, wraps inline SDK/CLI/parameter identifiers in `<code>` pills, highlights `"Solution:"` variants in `"Does this meet the goal?"` series, and de-emphasizes trailing exam instructions.
- **Microsoft Learn Skill Areas**: Classifies all 161 AI-103 questions (plus AI-300 and AI-500) into official Microsoft Learn skill areas with a sidebar toggle between **Skill Area** and **Question #** views while preserving stable `Q<topic>.<num>` IDs.
- **Community Consensus & Full Explanations**: Displays visual vote-distribution bars from `voted_answers_tally`, flags contested community splits (`Contested`), sorts discussion comments by upvotes with an inline expander for all comments, and links directly to the original ExamTopics thread.
- **Non-MCQ Self-Grading & Exhibit Lightbox**: Provides `Got it right` / `Needs work` self-assessment on HOTSPOT and DRAG DROP questions after reveal, and click-to-zoom modal `<dialog>` inspection on every exhibit image.
- **Search, Filters, Bookmarks & Keyboard Shortcuts**:
  - `/` — Focus instant search
  - `←` / `→` — Previous / next visible question
  - `1`–`9` — Toggle answer choice `A`–`I`
  - `A` — Reveal / hide answer (with live grading feedback)
  - `R` — Mark / unmark reviewed
  - `B` — Toggle bookmark (`★`)
  - Filter chips for `All`, `Unreviewed`, `Needs work`, `Bookmarked`, `Case Studies`, `Hotspot / Drag-Drop`, and `Contested`.

## Regenerating guides

Enrich exam metadata & community notes (`ai-103`, `ai-300`, `ai-500`, `dp-800`), sync JSONL, and rebuild all HTML guides, Markdown guides, and `guides/index.html`:

```bash
python3 scripts/enrich_ai_exams.py --apply
python3 scripts/sync_jsonl.py
python3 scripts/build_study_guide.py \
  data/dp-600.json data/dp-700.json data/dp-800.json \
  data/ai-103.json data/ai-300.json data/ai-500.json \
  --out-dir guides --format both
```

To produce only one format, swap `--format both` for `--format html` or `--format markdown`.

## Refresh the crawl

Crawl or refresh specific exam slugs (supports checkpoint resume via `--state-file`):

```bash
python3 scripts/crawl_fabric_discussions.py \
  --output-dir data \
  --exams dp-800 \
  --state-file state/dp-800-state.json \
  --max-list-pages 320 \
  --stop-after-empty-pages 80
```

Backfill and clean structured community-voted answers for HOTSPOT and DRAG DROP questions from discussion comments:

```bash
python3 scripts/backfill_missing_answers.py --reprocess --loose --apply
python3 scripts/enrich_ai_exams.py --apply
python3 scripts/sync_jsonl.py
```

## Running tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

These guides are offline study aids derived from public ExamTopics discussions. Be aware of these caveats before relying on them:

- **Coverage reflects public discussion threads.** ExamTopics only creates a public discussion thread once a user comments on a question, so newer 2026 exams (such as AI-500) include only questions with active community threads so far.
- **HOTSPOT and DRAG DROP questions use self-grading.** ExamTopics embeds interactive UI as static images without machine-gradable coordinates; the HTML app surfaces community consensus / community notes on reveal and lets you self-grade (`Got it right` / `Needs work`).
- **Low-vote 2026 community notes are explicitly badged.** All 179 multiple-choice questions and all 107 non-MCQ questions across AI-103, AI-300, and AI-500 include community answers or extracted discussion notes; items derived from low-upvote threads display a `Community note` badge so you can verify them against the full discussion.
- **The HTML guide requires JavaScript** for navigation, search/filtering, answer reveal, progress tracking, exhibit lightbox, and dark-mode toggle.
- **`data/*.jsonl` is auto-generated** from `data/*.json` via `scripts/sync_jsonl.py`.

## Notes

- Selections, bookmarks, self-grades, and reviewed state are stored in portable exam-scoped `localStorage` keys (`examguide-v2-<exam>-*`) with automatic migration from legacy path-based keys.
- Data is intended for personal study only; respect examtopics.com's terms of service.
