# ExamTopics Fabric Study Guides

Crawled DP-600 and DP-700 exam discussion questions from [examtopics.com](https://examtopics.com), converted into offline study guides.

## Folder layout

```
.
├── scripts/                 # Python tooling
│   ├── crawl_fabric_discussions.py   # Crawl / refresh exam data
│   ├── build_study_guide.py          # Generate HTML / Markdown guides
│   └── compare_with_original.py      # Validate a question against the live site
├── data/                    # Raw crawled data
│   ├── dp-600.json
│   ├── dp-600.jsonl
│   ├── dp-700.json
│   └── dp-700.jsonl
├── guides/                  # Student-facing study guides
│   ├── dp-600-examtopics-study-guide.html
│   ├── dp-600-examtopics-study-guide.md
│   ├── dp-700-examtopics-study-guide.html
│   └── dp-700-examtopics-study-guide.md
├── references/              # Official Microsoft reference materials
│   └── microsoft/
│       ├── dp-600-study-guide.md
│       ├── dp-700-study-guide.md
│       ├── certification-poster.pdf
│       └── choose-your-microsoft-credential.pdf
└── state/                   # Crawler checkpoint / resume state
    └── state.json
```

## Quick start

Open a guide in your browser:

```bash
open guides/dp-600-examtopics-study-guide.html
```

Or serve the folder locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/guides/dp-600-examtopics-study-guide.html
```

## Regenerate guides

```bash
python3 scripts/build_study_guide.py data/dp-600.json data/dp-700.json --out-dir guides --format html
```

## Refresh the crawl

```bash
python3 scripts/crawl_fabric_discussions.py --output-dir data
```

## Validate against the live site

```bash
python3 scripts/compare_with_original.py --json data/dp-600.json --discussion-id <id>
```

## Notes

- The HTML guides support dark mode, progress tracking, answer selection, and reveal-with-feedback.
- Selections and reviewed state are stored in the browser's `localStorage`.
- Data is intended for personal study only; respect examtopics.com's terms of service.
