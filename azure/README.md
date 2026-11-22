# ExamTopics Microsoft Azure AI, Fabric & GitHub Study Guides

Crawled Microsoft Azure AI, Data/Fabric, Agentic Business (`AB-*`), Cloud/AI Security (`SC-500`), GitHub (`GH-*`), and Fundamentals certification exam discussion questions from [examtopics.com](https://examtopics.com), converted into standalone offline HTML and Markdown study guides (**2,243** crawled discussions across **28** certification guides, organized into 4 vertical tiers on the Study Hub):

### 1. Expert Level Certifications
| Exam | Title | Crawled Discussions |
|---|---|---:|
| **AI-500** | Designing and Implementing Multi-Agent AI Solutions | 18 |
| **AB-100** | Agentic AI Business Solutions Architect | 124 |
| **AZ-401** | Designing and Implementing Microsoft Agentic DevOps Solutions | 0 *(awaiting ExamTopics threads)* |

### 2. Intermediate & Associate — Azure, Fabric & Microsoft AI
| Exam | Title | Crawled Discussions |
|---|---|---:|
| **AI-103** | Developing AI Apps and Agents on Azure | 161 |
| **AI-200** | Developing AI Cloud Solutions on Azure | 28 |
| **AI-300** | Operationalizing Machine Learning and Generative AI Solutions | 107 |
| **DP-600** | Implementing Analytics Solutions Using Microsoft Fabric | 199 |
| **DP-700** | Implementing Data Engineering Solutions Using Microsoft Fabric | 139 |
| **DP-750** | Implementing Data Engineering Solutions Using Azure Databricks | 39 |
| **DP-800** | Developing AI-Enabled Database Solutions | 48 |
| **AB-620** | Designing and Building Integrated AI Solutions in Copilot Studio | 55 |
| **AB-410** | Building Intelligent Applications | 156 |
| **AB-400** | Extending Microsoft Power Platform Solutions with Code and AI | 0 *(awaiting ExamTopics threads)* |
| **AB-210** | Accelerating Sales Pipelines with AI in Dynamics 365 | 35 |
| **AB-250** | Transforming Contact Center Experiences with AI in Dynamics 365 | 10 |
| **AB-650** | Administering Microsoft 365 and AI Services | 60 |
| **AB-730** | AI Business Professional | 89 |
| **AB-731** | AI Transformation Leader | 100 |
| **SC-500** | Implementing End-to-End Security Controls for Cloud and AI Workloads | 149 |

### 3. GitHub Certifications
| Exam | Title | Crawled Discussions |
|---|---|---:|
| **GH-300** | GitHub Copilot | 103 |
| **GH-600** | Developing in Agentic AI Systems | 61 |
| **GH-200** | GitHub Actions | 92 |
| **GH-500** | GitHub Advanced Security | 25 |
| **GH-100** | GitHub Enterprise Administrator | 1 |
| **GH-900** | GitHub Foundations | 19 |

### 4. Beginner & Fundamentals Level
| Exam | Title | Crawled Discussions |
|---|---|---:|
| **AI-901** | Microsoft Azure AI Fundamentals | 50 |
| **DP-900** | Microsoft Azure Data Fundamentals | 288 |
| **AB-900** | Microsoft 365 Copilot and Agent Administration Fundamentals | 87 |

## Folder layout

```
.
├── assets/
│   └── exhibits/            # Downloaded offline exhibit & choice images per exam
├── data/                    # Crawled datasets (<exam>.json + auto-synced <exam>.jsonl)
├── docs/
│   └── specs/               # Feature & architecture specifications (F-01 .. F-04)
├── guides/                  # Student-facing offline HTML & Markdown study guides
│   ├── index.html           # 4-tier Study Hub (Expert -> Associate -> GitHub -> Beginner)
│   └── <exam>-examtopics-study-guide.{html,md}
├── references/
│   └── microsoft/           # Official Microsoft Learn study guides (<exam>-study-guide.md) & posters
├── scripts/                 # Python crawler, enrichment, backfill, sync & guide builder tooling
│   ├── crawl_fabric_discussions.py
│   ├── build_study_guide.py
│   ├── enrich_ai_exams.py
│   ├── backfill_missing_answers.py
│   ├── sanitize_exhibit_html.py
│   └── sync_jsonl.py
├── state/
│   └── state.json           # Unified single-file checkpoint state (per-exam page tracking)
└── tests/
    └── test_crawler_and_builder.py
```

## Quick start

Open the unified Exam Hub or any individual guide directly in your browser (from `azure/`):

```bash
open guides/index.html
open guides/ai-500-examtopics-study-guide.html
open guides/dp-750-examtopics-study-guide.html
open guides/gh-300-examtopics-study-guide.html
open guides/dp-900-examtopics-study-guide.html
```

Or serve locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/guides/index.html
```

## Regenerating guides

Enrich metadata & community notes, sync JSONL, and rebuild all 28 HTML/Markdown guides plus `guides/index.html`:

```bash
python3 scripts/backfill_missing_answers.py --reprocess --loose --apply
python3 scripts/enrich_ai_exams.py --apply
python3 scripts/sync_jsonl.py
python3 scripts/build_study_guide.py data/*.json --out-dir guides --format both
```

## Refresh the unified crawl

All 28 Microsoft & GitHub exams share `/discussions/microsoft/{page}/` and use the single unified `state/state.json` checkpoint file:

```bash
# Scan new top pages (e.g. pages 1..30) across all 28 exams in one pass:
python3 scripts/crawl_fabric_discussions.py \
  --output-dir data \
  --state-file state/state.json \
  --rescan-list-pages \
  --max-list-pages 30
```

## Running tests

```bash
python3 -Werror -m unittest discover -s tests -v
```
