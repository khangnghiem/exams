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

## Regenerating guides

Rebuild both HTML and Markdown guides from the current `data/*.json` files:

```bash
python3 scripts/build_study_guide.py data/dp-600.json data/dp-700.json --out-dir guides --format both
```

To produce only one format, swap `--format both` for `--format html` or `--format markdown`.
To rebuild a single exam, pass just that JSON file: `data/dp-600.json`.

After regenerating the JSON, keep `data/*.jsonl` in lock-step (the crawler used
to produce it as a side-effect during a full crawl):

```bash
python3 scripts/sync_jsonl.py
```

## Refresh the crawl

```bash
python3 scripts/crawl_fabric_discussions.py --output-dir data
```

## Validate against the live site

```bash
python3 scripts/compare_with_original.py --json data/dp-600.json --discussion-id <id>
```

## Limitations

These guides are offline study aids derived from public ExamTopics
discussions. Be aware of these caveats before relying on them:

- **HOTSPOT and DRAG DROP questions are display-only.** ExamTopics embeds
  the interactive UI as static images without parseable coordinates or
  draggable items, so the guide shows the exhibits and a community-voted
  answer (when available) but cannot let you actually click or drag to
  practice.
- **~21 questions show "Not provided" for the most-voted answer.** Some
  ExamTopics discussion threads have no consensus comment; the backfill
  script only lifts answers when a comment clearly states the choice(s).
- **The HTML guide requires JavaScript** for navigation (question map,
  prev/next, deep-link scrolling), answer reveal, progress tracking, and
  dark-mode toggle. Without JS, the page renders all questions but you
  can't reveal answers or move between them.
- **`data/*.jsonl` is auto-generated** from `data/*.json` via
  `scripts/sync_jsonl.py`. It mirrors the JSON for tools that want one
  question per line; it is not hand-edited.

## Notes

- The HTML guides support dark mode, progress tracking, answer selection, and reveal-with-feedback.
- Selections and reviewed state are stored in the browser's `localStorage`.
- Data is intended for personal study only; respect examtopics.com's terms of service.
