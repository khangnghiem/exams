# ExamTopics Azure & Fabric Study Guides

Crawled Microsoft Data & AI certification exam discussion questions from [examtopics.com](https://examtopics.com), converted into standalone offline HTML and Markdown study guides:

| Exam | Title | Crawled Discussions |
|---|---|---:|
| **DP-600** | Implementing Analytics Solutions Using Microsoft Fabric | 199 |
| **DP-700** | Implementing Data Engineering Solutions Using Microsoft Fabric | 139 |
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
│       └── dp-700/
├── data/                    # Crawled datasets (.json + auto-synced .jsonl)
│   ├── ai-103.{json,jsonl}
│   ├── ai-300.{json,jsonl}
│   ├── ai-500.{json,jsonl}
│   ├── dp-600.{json,jsonl}
│   └── dp-700.{json,jsonl}
├── docs/
│   └── specs/               # Feature & architecture specifications
│       └── F-01-ai-103-300-500-study-guides.md
├── guides/                  # Student-facing offline HTML & Markdown study guides
│   ├── ai-103-examtopics-study-guide.{html,md}
│   ├── ai-300-examtopics-study-guide.{html,md}
│   ├── ai-500-examtopics-study-guide.{html,md}
│   ├── dp-600-examtopics-study-guide.{html,md}
│   └── dp-700-examtopics-study-guide.{html,md}
├── references/              # Official Microsoft Learn study guides & posters
│   └── microsoft/
│       ├── ai-103-study-guide.md
│       ├── ai-300-study-guide.md
│       ├── ai-500-study-guide.md
│       ├── dp-600-study-guide.md
│       ├── dp-700-study-guide.md
│       ├── certification-poster.pdf
│       └── choose-your-microsoft-credential.pdf
├── scripts/                 # Python crawler, backfill, sync & guide builder tooling
│   ├── crawl_fabric_discussions.py
│   ├── build_study_guide.py
│   ├── backfill_missing_answers.py
│   ├── backfill_exhibits.py
│   ├── backfill_choice_markup.py
│   ├── backfill_dragdrop.py
│   ├── sanitize_exhibit_html.py
│   ├── sync_jsonl.py
│   └── compare_with_original.py
├── state/                   # Crawler checkpoint / resume state
│   ├── state.json
│   └── ai-exams-state.json
└── tests/                   # Unit test suite
    └── test_crawler_and_builder.py
```

## Quick start

Open any guide directly in your browser (from `azure/`):

```bash
open guides/ai-103-examtopics-study-guide.html
open guides/ai-300-examtopics-study-guide.html
open guides/ai-500-examtopics-study-guide.html
```

Or serve the folder locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/guides/ai-103-examtopics-study-guide.html
```

## Regenerating guides

Rebuild both HTML and Markdown guides from the `data/*.json` files:

```bash
python3 scripts/build_study_guide.py \
  data/dp-600.json data/dp-700.json \
  data/ai-103.json data/ai-300.json data/ai-500.json \
  --out-dir guides --format both
```

To produce only one format, swap `--format both` for `--format html` or `--format markdown`.

After updating any `data/*.json` file via backfill scripts, keep `data/*.jsonl` in lock-step:

```bash
python3 scripts/sync_jsonl.py
```

## Refresh the crawl

Crawl or refresh specific exam slugs (supports checkpoint resume via `--state-file`):

```bash
python3 scripts/crawl_fabric_discussions.py \
  --output-dir data \
  --exams ai-103 ai-300 ai-500 \
  --state-file state/ai-exams-state.json \
  --max-list-pages 260 \
  --stop-after-empty-pages 65
```

Backfill community-voted answers for HOTSPOT and DRAG DROP questions from discussion comments:

```bash
python3 scripts/backfill_missing_answers.py --files ai-103.json ai-300.json ai-500.json --apply
python3 scripts/backfill_missing_answers.py --files ai-103.json ai-300.json ai-500.json --loose --apply
python3 scripts/sync_jsonl.py --files ai-103.json ai-300.json ai-500.json
```

## Running tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

These guides are offline study aids derived from public ExamTopics discussions. Be aware of these caveats before relying on them:

- **Coverage reflects public discussion threads.** ExamTopics only creates a public discussion thread once a user comments on a question, so newer 2026 exams (such as AI-500) include only questions with active community threads so far.
- **HOTSPOT and DRAG DROP questions are display-only.** ExamTopics embeds the interactive UI as static images without parseable coordinates or draggable items, so the guide shows the exhibits and a community-voted answer (when available) rather than graded click/drag regions.
- **Some non-MCQ threads show "Not provided" for the most-voted answer** (~19 in AI-103, ~32 in AI-300, ~4 in AI-500, and ~21 across DP-600/DP-700) when no comment meets the consensus/explicit-pattern threshold. All 179 multiple-choice questions across AI-103, AI-300, and AI-500 have community-verified answers.
- **The HTML guide requires JavaScript** for navigation (question map, prev/next, deep-link scrolling), answer reveal, progress tracking, and dark-mode toggle.
- **`data/*.jsonl` is auto-generated** from `data/*.json` via `scripts/sync_jsonl.py`.

## Notes

- The HTML guides support dark mode, progress tracking, single/multi-select partial-credit grading, and reveal-with-feedback.
- Selections and reviewed state are stored in the browser's `localStorage`.
- Data is intended for personal study only; respect examtopics.com's terms of service.
