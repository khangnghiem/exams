#!/usr/bin/env python3
"""
Build student-friendly study guides from crawled exam JSON.

Usage (from repo root):
    python scripts/build_study_guide.py data/dp-600.json --out-dir guides
    python scripts/build_study_guide.py data/dp-600.json data/dp-700.json --out-dir guides --format html
    python scripts/build_study_guide.py data/dp-600.json --out-dir guides --format markdown
    python scripts/build_study_guide.py data/dp-600.json --out-dir guides --format both
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

# Graceful import of the exhibit HTML sanitizer. The script lives next to
# sanitize_exhibit_html.py, so when invoked with ``python scripts/build_study_guide.py``
# Python prepends the ``scripts/`` directory to sys.path and the bare import works.
# Fall back to ``clean_html`` if BeautifulSoup isn't installed.
try:
    from sanitize_exhibit_html import sanitize_exhibit_html  # type: ignore
    SANITIZER_AVAILABLE = True
except Exception:  # pragma: no cover - defensive
    sanitize_exhibit_html = None  # type: ignore[assignment]
    SANITIZER_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MULTI_SELECT_PROMPT_RE = re.compile(
    r"\b(?:select\s+(?:two|three|four|five|\d+)|"
    r"which\s+(?:two|three|four|five|\d+)|"
    r"choose\s+(?:two|three|four|five|\d+)|"
    r"each\s+correct\s+answer\s+presents\s+part\s+of\s+the\s+solution|"
    r"more\s+than\s+one\s+answer\s+choice\s+may\s+achieve\s+the\s+goal)\b",
    re.IGNORECASE,
)


def _exhibit_exists(local: str) -> bool:
    """Return True if ``local`` exists directly or relative to ``PROJECT_ROOT``."""
    if not local:
        return False
    p = Path(local)
    if p.exists():
        return True
    marker = "assets/exhibits/"
    norm = local.replace("\\", "/")
    idx = norm.find(marker)
    if idx >= 0:
        return (PROJECT_ROOT / norm[idx:]).exists()
    return (PROJECT_ROOT / local.lstrip("/")).exists()


def _extract_code_text(exhibit: dict[str, Any]) -> str:
    """Extract plain code text from ``code``, ``text``, or ``html`` exhibit fields."""
    raw_code = exhibit.get("code") or exhibit.get("text") or ""
    if raw_code:
        return str(raw_code)
    raw_html = exhibit.get("html") or exhibit.get("raw_html") or ""
    if not raw_html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", str(raw_html), flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


# Official Microsoft certification exam names keyed by lowercase exam slug.
EXAM_TITLES: dict[str, str] = {
    "dp-600": "Implementing Analytics Solutions Using Microsoft Fabric",
    "dp-700": "Implementing Data Engineering Solutions Using Microsoft Fabric",
    "ai-103": "Developing AI Apps and Agents on Azure",
    "ai-300": "Operationalizing Machine Learning and Generative AI Solutions",
    "ai-500": "Designing and Implementing Multi-Agent AI Solutions",
}


def format_study_guide_title(exam: str) -> str:
    """Return the human-readable study guide title for ``exam``."""
    code = exam.strip().upper()
    exam_title = EXAM_TITLES.get(exam.strip().lower())
    if exam_title:
        return f"{code} {exam_title} Study Guide"
    return f"{code} Study Guide"


# Map each exam's numeric topic tags to Microsoft official skill area names.
# Update these if the source data's topic ordering changes.
TOPIC_LABELS: dict[str, dict[int, str]] = {
    # DP-600 classified into Microsoft's official skill areas.
    "dp-600": {
        1: "Maintain a data analytics solution",
        2: "Prepare data",
        3: "Implement and manage semantic models",
    },
    # DP-700 source data has three topic tags that align with Microsoft's official skill areas.
    "dp-700": {
        1: "Implement and manage an analytics solution",
        2: "Ingest and transform data",
        3: "Monitor and optimize an analytics solution",
    },
    # AI-103: Developing AI Apps and Agents on Azure
    "ai-103": {
        1: "Exam A — Developing AI Apps and Agents on Azure",
        2: "Implement generative AI and agentic solutions",
        3: "Implement computer vision solutions",
        4: "Implement text analysis solutions",
        5: "Implement information extraction solutions",
    },
    # AI-300: Operationalizing Machine Learning and Generative AI Solutions
    "ai-300": {
        1: "Case Studies & End-to-End Scenarios",
        2: "Design and implement an MLOps infrastructure",
        3: "Implement machine learning model lifecycle and operations",
        4: "Design and implement a GenAIOps infrastructure",
        5: "Implement generative AI quality assurance and observability",
        6: "Optimize generative AI systems and model performance",
    },
    # AI-500: Designing and Implementing Multi-Agent AI Solutions
    "ai-500": {
        1: "Architect multi-agent solutions",
        2: "Develop multi-agent solutions in Azure",
        3: "Evaluate, optimize, and monitor multi-agent solutions",
        4: "Secure, govern, and deploy multi-agent solutions",
    },
}


SKILL_AREA_LABELS: dict[str, dict[int, str]] = {
    "dp-600": TOPIC_LABELS["dp-600"],
    "dp-700": TOPIC_LABELS["dp-700"],
    "ai-103": {
        1: "Plan and manage an Azure AI solution",
        2: "Implement generative AI and agentic solutions",
        3: "Implement computer vision solutions",
        4: "Implement text analysis solutions",
        5: "Implement information extraction solutions",
    },
    "ai-300": TOPIC_LABELS["ai-300"],
    "ai-500": TOPIC_LABELS["ai-500"],
}


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title</title>
  <style>
    :root {
      color-scheme: light;
      --font-display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
      --bg: #f4efe7;
      --bg-rgb: 244 239 231;
      --surface: #fffdf8;
      --surface-rgb: 255 253 248;
      --surface-2: #f8f1e5;
      --text: #211f1b;
      --text-secondary: #625a50;
      --muted: #877d70;
      --accent: #175cd3;
      --accent-ink: #0f3f92;
      --accent-soft: #dbeafe;
      --accent-contrast: #fff;
      --success: #147a46;
      --success-bg: #dcfce7;
      --success-ink: #145236;
      --success-contrast: #fff;
      --warning: #b45309;
      --warning-bg: #fef3c7;
      --warning-ink: #78350f;
      --danger: #b42318;
      --danger-bg: #fee2e2;
      --danger-ink: #7f1d1d;
      --border: #e0d4c3;
      --border-strong: #c8b89f;
      --shadow: 0 18px 55px rgba(52, 38, 20, 0.11), 0 2px 8px rgba(52, 38, 20, 0.06);
      --shadow-soft: 0 10px 30px rgba(52, 38, 20, 0.08);
      --radius: 20px;
      --radius-sm: 12px;
      --content-width: 1120px;
      --rail-width: 286px;
      --header-height: 3.85rem;
    }

    :root[data-theme="dark"] {
      color-scheme: dark;
      --bg: #10141f;
      --bg-rgb: 16 20 31;
      --surface: #171d2b;
      --surface-rgb: 23 29 43;
      --surface-2: #20283a;
      --text: #f5efe7;
      --text-secondary: #b7ad9d;
      --muted: #8c8479;
      --accent: #8ab4ff;
      --accent-ink: #d7e6ff;
      --accent-soft: #19345f;
      --accent-contrast: #10141f;
      --success: #62d393;
      --success-bg: #173c2a;
      --success-ink: #bbf7d0;
      --success-contrast: #10141f;
      --warning: #fbbf24;
      --warning-bg: #3a2a0d;
      --warning-ink: #fde68a;
      --danger: #ff8a80;
      --danger-bg: #3f1c1c;
      --danger-ink: #fecaca;
      --border: #333b4d;
      --border-strong: #4a556f;
      --shadow: 0 22px 70px rgba(0, 0, 0, 0.42), 0 2px 10px rgba(0, 0, 0, 0.25);
      --shadow-soft: 0 12px 36px rgba(0, 0, 0, 0.28);
    }

    * { box-sizing: border-box; }
    html {
      scroll-behavior: smooth;
      scroll-padding-top: calc(var(--header-height) + 1rem);
    }
    body {
      margin: 0;
      min-height: 100vh;
      padding-bottom: calc(5rem + env(safe-area-inset-bottom));
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 1.0625rem;
      line-height: 1.62;
      text-align: start;
      overflow-wrap: break-word;
      background:
        radial-gradient(circle at top left, rgb(23 92 211 / 0.14), transparent 34rem),
        radial-gradient(circle at top right, rgb(180 83 9 / 0.1), transparent 32rem),
        linear-gradient(180deg, rgb(var(--bg-rgb)) 0%, var(--bg) 48%, color-mix(in srgb, var(--bg) 90%, #000 10%) 100%);
    }
    a { color: inherit; }
    img { max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--border); }
    pre { background: var(--surface-2); padding: 0.9rem 1rem; border-radius: 12px; overflow-x: auto; border: 1px solid var(--border); }
    code {
      font-family: var(--font-mono);
      font-size: 0.88em;
      padding: 0.1rem 0.36rem;
      border-radius: 6px;
      background: color-mix(in srgb, var(--surface-2) 86%, var(--accent-soft) 14%);
      border: 1px solid color-mix(in srgb, var(--border) 78%, transparent);
    }
    pre code { padding: 0; border: 0; background: transparent; font-size: 0.9em; }

    button, .btn {
      appearance: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      min-block-size: 2.35rem;
      border: 1px solid transparent;
      border-radius: 999px;
      padding: 0.45rem 0.9rem;
      background: var(--accent);
      color: var(--accent-contrast);
      cursor: pointer;
      font-family: var(--font-sans);
      font-weight: 700;
      font-size: 0.86rem;
      line-height: 1.2;
      text-decoration: none;
      transition: transform 150ms ease, background 150ms ease, border-color 150ms ease, box-shadow 150ms ease, opacity 150ms ease;
    }
    button:hover, .btn:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgb(23 92 211 / 0.16); }
    button:active, .btn:active { transform: translateY(0); }
    button.secondary, .btn.secondary {
      background: rgb(var(--surface-rgb) / 0.78);
      color: var(--text);
      border-color: var(--border);
      box-shadow: none;
    }
    button.ghost, .btn.ghost {
      background: transparent;
      color: var(--text-secondary);
      border-color: transparent;
      box-shadow: none;
    }
    button.active, .btn.active {
      background: var(--success);
      color: var(--success-contrast);
      border-color: var(--success);
    }
    button.bookmarked {
      background: var(--warning-bg);
      color: var(--warning-ink);
      border-color: color-mix(in srgb, var(--warning) 45%, var(--border));
    }
    button:focus-visible, a:focus-visible, summary:focus-visible, input:focus-visible {
      outline: 3px solid color-mix(in srgb, var(--accent) 72%, white 28%);
      outline-offset: 2px;
    }

    #progress-bar {
      position: fixed;
      inset: 0 auto auto 0;
      block-size: 4px;
      inline-size: 0%;
      z-index: 200;
      background: linear-gradient(90deg, var(--accent), #22c55e);
      transition: inline-size 200ms ease, width 200ms ease;
    }
    .skip-link {
      position: fixed;
      left: 1rem;
      top: 0.75rem;
      z-index: 300;
      transform: translateY(-180%);
    }
    .skip-link:focus { transform: translateY(0); }

    header.app-header {
      position: sticky;
      top: 0;
      z-index: 120;
      border-bottom: 1px solid color-mix(in srgb, var(--border) 80%, transparent);
      background: rgb(var(--surface-rgb) / 0.88);
      backdrop-filter: blur(16px) saturate(140%);
    }
    .header-inner {
      max-inline-size: calc(var(--content-width) + var(--rail-width) + 3.5rem);
      min-block-size: var(--header-height);
      margin: 0 auto;
      padding: 0.45rem 1.15rem;
      display: flex;
      gap: 0.85rem;
      align-items: center;
      justify-content: space-between;
    }
    .brand { min-inline-size: 0; flex: 1; }
    .brand-row { display: flex; align-items: center; gap: 0.55rem; flex-wrap: wrap; }
    .brand h1 {
      margin: 0;
      font-family: var(--font-display);
      font-size: clamp(1.02rem, 0.9rem + 0.55vw, 1.4rem);
      line-height: 1.15;
      letter-spacing: -0.02em;
    }
    .brand .stats {
      color: var(--text-secondary);
      font-size: 0.82rem;
      margin-top: 0.1rem;
    }
    .controls { display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center; justify-content: flex-end; }
    .controls button, .controls .btn { min-block-size: 2.2rem; padding-inline: 0.72rem; font-size: 0.82rem; }

    #exam-switcher-menu {
      margin: 0.4rem auto auto 1rem;
      padding: 0.55rem;
      border: 1px solid var(--border-strong);
      border-radius: 16px;
      background: var(--surface);
      color: var(--text);
      box-shadow: var(--shadow);
      min-inline-size: 260px;
    }
    #exam-switcher-menu:is(:popover-open, .\\:popover-open) { display: grid; gap: 0.25rem; }
    #exam-switcher-menu a {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem 0.7rem;
      border-radius: 10px;
      text-decoration: none;
      font-size: 0.86rem;
      font-weight: 600;
    }
    #exam-switcher-menu a:hover, #exam-switcher-menu a[aria-current="page"] {
      background: var(--accent-soft);
      color: var(--accent-ink);
    }

    main {
      position: relative;
      max-inline-size: calc(var(--content-width) + var(--rail-width) + 3.5rem);
      margin: 0 auto;
      padding: 1rem 1.15rem 6rem;
    }

    /* Compact collapsible overview strip (content-first noise reduction) */
    .overview-banner {
      scroll-margin-top: calc(var(--header-height) + 0.75rem);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgb(var(--surface-rgb) / 0.86);
      box-shadow: var(--shadow-soft);
      margin-bottom: 0.9rem;
      padding: 0.65rem 1rem;
    }
    .overview-banner > summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      font-size: 0.88rem;
    }
    .overview-banner > summary::-webkit-details-marker { display: none; }
    .overview-summary-left { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
    .overview-summary-left::before {
      content: "▸";
      display: inline-block;
      color: var(--accent-ink);
      font-weight: 900;
      transition: rotate 160ms ease;
    }
    .overview-banner[open] > summary .overview-summary-left::before { rotate: 90deg; }
    .overview-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.18rem 0.6rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-ink);
      font-weight: 800;
      font-size: 0.78rem;
    }
    .overview-metrics {
      display: flex;
      gap: 0.55rem;
      flex-wrap: wrap;
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }
    .metric {
      flex: 1 1 110px;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 0.55rem 0.75rem;
      background: rgb(var(--surface-rgb) / 0.65);
    }
    .metric strong { display: block; font-size: 1.15rem; line-height: 1.1; }
    .metric span { color: var(--text-secondary); font-size: 0.78rem; }
    .kbd-bar {
      margin-top: 0.6rem;
      color: var(--text-secondary);
      font-size: 0.8rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
    }
    kbd {
      font-family: var(--font-mono);
      font-size: 0.76rem;
      padding: 0.08rem 0.36rem;
      border-radius: 5px;
      border: 1px solid var(--border-strong);
      background: var(--surface-2);
    }

    /* Search & Filter Toolbar */
    .study-toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.55rem;
      align-items: center;
      margin-bottom: 1rem;
      padding: 0.6rem 0.8rem;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgb(var(--surface-rgb) / 0.86);
      box-shadow: var(--shadow-soft);
    }
    .search-box {
      position: relative;
      flex: 1 1 220px;
      min-inline-size: 190px;
    }
    .search-box input {
      inline-size: 100%;
      min-block-size: 2.25rem;
      padding: 0.4rem 0.8rem;
      border: 1px solid var(--border-strong);
      border-radius: 999px;
      background: var(--surface);
      color: var(--text);
      font: inherit;
      font-size: 0.88rem;
    }
    .filter-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center; }
    .filter-chip {
      min-block-size: 2rem;
      padding: 0.28rem 0.68rem;
      font-size: 0.79rem;
      background: var(--surface-2);
      color: var(--text-secondary);
      border: 1px solid var(--border);
      box-shadow: none;
    }
    .filter-chip[aria-pressed="true"] {
      background: var(--accent);
      color: var(--accent-contrast);
      border-color: var(--accent);
    }
    .filter-count {
      margin-inline-start: auto;
      color: var(--text-secondary);
      font-size: 0.8rem;
      font-weight: 700;
    }
    .filter-empty {
      border: 1px dashed var(--border-strong);
      border-radius: var(--radius);
      padding: 2rem 1.25rem;
      text-align: center;
      background: rgb(var(--surface-rgb) / 0.8);
    }

    .study-layout {
      display: grid;
      grid-template-columns: var(--rail-width) minmax(0, 1fr);
      gap: 1.2rem;
      align-items: start;
    }
    .study-map {
      position: sticky;
      top: calc(var(--header-height) + 0.75rem);
      scroll-margin-top: calc(var(--header-height) + 0.75rem);
      max-block-size: calc(100vh - var(--header-height) - 1.5rem);
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 0.85rem;
      background: rgb(var(--surface-rgb) / 0.88);
      box-shadow: var(--shadow-soft);
    }
    .nav-sidebar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.35rem;
      margin-bottom: 0.7rem;
      padding: 0.3rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.72);
    }
    .nav-sidebar button { min-inline-size: 2.5rem; min-block-size: 2.15rem; padding: 0 0.7rem; }
    .nav-sidebar .nav-status { text-align: center; color: var(--text-secondary); font-size: 0.82rem; font-weight: 800; }
    .nav-sidebar button:disabled, .nav-floating button:disabled { opacity: 0.4; cursor: not-allowed; }

    .map-mode-switch {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.3rem;
      padding: 0.24rem;
      border-radius: 999px;
      background: var(--surface-2);
      border: 1px solid var(--border);
      margin-bottom: 0.65rem;
    }
    .map-mode-btn {
      min-block-size: 1.85rem;
      padding: 0.2rem 0.5rem;
      font-size: 0.76rem;
      background: transparent;
      color: var(--text-secondary);
      border-color: transparent;
      box-shadow: none;
    }
    .map-mode-btn[aria-pressed="true"] {
      background: var(--surface);
      color: var(--accent-ink);
      border-color: var(--border);
    }

    .study-map h2 { margin: 0 0 0.2rem; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-secondary); }
    .map-note { margin: 0 0 0.65rem; color: var(--muted); font-size: 0.78rem; }

    .toc-topic { border-top: 1px solid var(--border); padding-top: 0.55rem; margin-top: 0.55rem; }
    .toc-topic:first-of-type { border-top: 0; padding-top: 0; margin-top: 0; }
    .toc-topic > summary, .toc-chunk > summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.45ch;
      font-weight: 700;
      font-size: 0.84rem;
      color: var(--text);
      text-align: start;
    }
    .toc-topic > summary::-webkit-details-marker, .toc-chunk > summary::-webkit-details-marker { display: none; }
    .toc-topic > summary::before, .toc-chunk > summary::before {
      content: "▸";
      flex-shrink: 0;
      color: var(--muted);
      transition: rotate 150ms ease;
    }
    .toc-topic[open] > summary::before, .toc-chunk[open] > summary::before { rotate: 90deg; }
    .toc-chunk { margin-top: 0.45rem; padding-inline-start: 0.35rem; }
    .toc-chunk > summary { color: var(--text-secondary); font-size: 0.79rem; font-weight: 600; }

    .toc-links {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0.34rem;
      list-style: none;
      margin: 0.45rem 0 0;
      padding: 0;
    }
    .toc-links a {
      display: grid;
      place-items: center;
      min-block-size: 2rem;
      padding: 0.15rem 0.25rem;
      border-radius: 9px;
      border: 1px solid var(--border);
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.75rem;
      font-weight: 800;
      background: rgb(var(--surface-rgb) / 0.55);
      transition: background 140ms ease, color 140ms ease, border-color 140ms ease;
    }
    .toc-links a:hover, .toc-links a.current {
      color: var(--accent-ink);
      border-color: color-mix(in srgb, var(--accent) 50%, var(--border));
      background: var(--accent-soft);
    }
    .toc-links a.reviewed {
      color: var(--success-ink);
      background: var(--success-bg);
      border-color: color-mix(in srgb, var(--success) 42%, var(--border));
    }
    .toc-links a.bookmarked {
      box-shadow: inset 0 -3px 0 var(--warning);
    }
    .toc-links a.filtered-out { opacity: 0.25; }
    .toc-links a.current.reviewed {
      color: var(--accent-ink);
      background: linear-gradient(135deg, var(--accent-soft), var(--success-bg));
      border-color: var(--accent);
    }

    /* Question Card */
    .question {
      position: relative;
      scroll-margin-top: calc(var(--header-height) + 0.85rem);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: linear-gradient(180deg, rgb(var(--surface-rgb) / 0.98), rgb(var(--surface-rgb) / 0.92));
      box-shadow: var(--shadow);
      padding: clamp(1rem, 0.8rem + 1.2vw, 1.5rem);
      margin-bottom: 1rem;
      display: none;
    }
    .question.active { display: block; animation: fadeIn 180ms ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    .question.current { border-color: color-mix(in srgb, var(--accent) 48%, var(--border)); }
    .question.reviewed { border-inline-start: 6px solid var(--success); }

    .q-header {
      display: flex;
      gap: 0.75rem;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.85rem;
    }
    .q-title { display: flex; gap: 0.45rem; align-items: center; flex-wrap: wrap; }
    .q-num {
      font-family: var(--font-display);
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1.1;
    }
    .q-id, .q-badge {
      display: inline-flex;
      align-items: center;
      min-block-size: 1.6rem;
      padding: 0.16rem 0.52rem;
      border-radius: 999px;
      background: var(--surface-2);
      color: var(--text-secondary);
      border: 1px solid var(--border);
      font-size: 0.74rem;
      font-weight: 700;
    }
    .q-badge { color: var(--warning-ink); background: var(--warning-bg); border-color: color-mix(in srgb, var(--warning) 30%, var(--border)); }
    .q-badge.skill-badge { color: var(--accent-ink); background: var(--accent-soft); border-color: color-mix(in srgb, var(--accent) 28%, var(--border)); }
    .q-badge.contested-badge { color: var(--danger-ink); background: var(--danger-bg); border-color: color-mix(in srgb, var(--danger) 35%, var(--border)); }
    .q-actions { display: flex; gap: 0.4rem; flex-wrap: wrap; justify-content: flex-end; }
    .q-actions button { min-block-size: 2.15rem; padding-inline: 0.72rem; }

    /* Case Study Sibling Jumper & 2-Column Split-Pane Inspector */
    .cs-jumper {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.85rem;
      padding: 0.5rem 0.75rem;
      border-radius: 14px;
      background: color-mix(in srgb, var(--accent-soft) 42%, var(--surface-2) 58%);
      border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--border));
      font-size: 0.82rem;
    }
    .cs-jumper-title { font-weight: 800; color: var(--accent-ink); }
    .cs-jumper-links { display: flex; flex-wrap: wrap; gap: 0.3rem; }
    .cs-jumper-links a {
      display: inline-flex;
      align-items: center;
      padding: 0.15rem 0.5rem;
      border-radius: 999px;
      text-decoration: none;
      font-size: 0.76rem;
      font-weight: 700;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text-secondary);
    }
    .cs-jumper-links a[aria-current="true"] {
      background: var(--accent);
      color: var(--accent-contrast);
      border-color: var(--accent);
    }

    .q-case-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1rem;
      align-items: start;
    }
    @media (min-width: 1160px) {
      .q-case-grid {
        grid-template-columns: minmax(0, 1.08fr) minmax(300px, 0.92fr);
      }
      .q-case-grid .case-study-panel {
        position: sticky;
        top: calc(var(--header-height) + 0.85rem);
        max-block-size: calc(100vh - var(--header-height) - 1.7rem);
        overflow-y: auto;
      }
    }

    .case-study-panel {
      border: 1px solid var(--border-strong);
      border-radius: 16px;
      padding: 0.75rem;
      background: color-mix(in srgb, var(--surface-2) 72%, var(--surface) 28%);
    }
    .cs-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.55rem;
      padding-bottom: 0.45rem;
      border-bottom: 1px solid var(--border);
    }
    .cs-panel-label {
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-secondary);
    }
    .cs-toggle-all {
      min-block-size: 1.8rem;
      padding: 0.2rem 0.6rem;
      font-size: 0.75rem;
    }

    /* Native <details> Case Study Accordion (modern-web-guidance: accordion) */
    .cs-section {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: rgb(var(--surface-rgb) / 0.86);
      margin-top: 0.45rem;
    }
    .cs-section:first-of-type { margin-top: 0; }
    .cs-section.relevant {
      border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
      background: color-mix(in srgb, var(--accent-soft) 24%, var(--surface) 76%);
    }
    .cs-section > summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5ch;
      padding: 0.55rem 0.75rem;
      font-weight: 700;
      font-size: 0.88rem;
      color: var(--text);
    }
    .cs-section > summary::-webkit-details-marker { display: none; }
    .cs-section > summary::before {
      content: "▾";
      display: inline-block;
      flex-shrink: 0;
      color: var(--accent-ink);
      rotate: -90deg;
    }
    .cs-section > summary:dir(rtl)::before { rotate: 90deg; }
    .cs-section[open] > summary::before { rotate: 0deg; }
    .cs-relevant-pill {
      margin-inline-start: auto;
      padding: 0.1rem 0.45rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-ink);
      font-size: 0.7rem;
      font-weight: 800;
    }
    .cs-section::details-content {
      interpolate-size: allow-keywords;
      overflow: clip;
      contain: layout;
    }
    .cs-section:not([open])::details-content { block-size: 0; }
    @media (prefers-reduced-motion: no-preference) {
      .cs-section > summary::before { transition: rotate 0.18s ease; }
      .cs-section::details-content {
        transition: block-size 0.24s ease-in-out, content-visibility 0.24s ease-in-out, display 0.24s ease-in-out;
        transition-behavior: allow-discrete;
      }
    }
    .cs-section-body {
      padding: 0.15rem 0.8rem 0.75rem;
      font-size: 0.93rem;
      line-height: 1.58;
      color: var(--text);
      max-inline-size: 70ch;
    }
    .cs-section-body p, .q-prompt p, .comment-body { text-wrap: pretty; }
    .cs-section-body p { margin: 0.45rem 0; }
    .cs-subheading {
      margin: 0.7rem 0 0.25rem;
      font-weight: 800;
      font-size: 0.84rem;
      color: var(--accent-ink);
    }

    /* Prompt & Smart Stem Typography */
    .prompt-card {
      position: relative;
      border: 1px solid color-mix(in srgb, var(--accent) 32%, var(--border));
      border-radius: 18px;
      padding: clamp(0.95rem, 0.8rem + 0.8vw, 1.3rem);
      background: linear-gradient(135deg, color-mix(in srgb, var(--accent-soft) 52%, var(--surface) 48%), rgb(var(--surface-rgb) / 0.9));
    }
    .prompt-label {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      margin-bottom: 0.45rem;
      color: var(--accent-ink);
      font-size: 0.74rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .q-prompt {
      max-inline-size: 72ch;
      font-size: 1rem;
      line-height: 1.62;
      font-weight: 400;
      color: var(--text);
    }
    .q-prompt p { margin: 0.55rem 0; }
    .q-prompt p:first-child { margin-top: 0; }
    .q-prompt p:last-child { margin-bottom: 0; }
    .q-prompt .prompt-lead {
      font-size: clamp(1.05rem, 0.96rem + 0.32vw, 1.2rem);
      line-height: 1.52;
      font-weight: 700;
      color: var(--text);
      margin-top: 0.75rem;
    }
    .q-prompt .prompt-lead:first-child { margin-top: 0; }
    .stem-list {
      margin: 0.45rem 0 0.7rem;
      padding-inline-start: 1.35rem;
      max-inline-size: 70ch;
    }
    .stem-list li { margin-bottom: 0.32rem; line-height: 1.55; }
    .proposed-solution {
      margin: 0.7rem 0;
      padding: 0.65rem 0.85rem;
      border-radius: 12px;
      border-inline-start: 4px solid var(--accent);
      background: rgb(var(--surface-rgb) / 0.9);
      border-top: 1px solid var(--border);
      border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }
    .proposed-solution .solution-label {
      display: block;
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: var(--accent-ink);
      margin-bottom: 0.2rem;
    }
    .proposed-solution p { margin: 0; font-weight: 600; }
    .exam-instruction-note {
      font-size: 0.84rem;
      color: var(--text-secondary);
      font-weight: 400;
      margin-top: 0.55rem !important;
    }
    .section-title {
      display: block;
      margin: 0.85rem 0 0.2rem;
      color: var(--accent-ink);
      font-size: 0.78rem;
      font-weight: 800;
    }

    /* Choices */
    .choices {
      list-style: none;
      padding: 0;
      margin: 0.95rem 0 0;
      display: grid;
      gap: 0.58rem;
    }
    .choices li {
      position: relative;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgb(var(--surface-rgb) / 0.8);
      transition: background 150ms ease, border-color 150ms ease, transform 150ms ease;
      overflow: hidden;
    }
    .choices li:hover { transform: translateX(2px); border-color: var(--border-strong); }
    .choices input { position: absolute; opacity: 0; inline-size: 1px; block-size: 1px; }
    .choices label {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.75rem;
      align-items: start;
      padding: 0.78rem 0.95rem;
      cursor: pointer;
    }
    .choices .letter {
      display: inline-grid;
      place-items: center;
      min-inline-size: 1.95rem;
      min-block-size: 1.95rem;
      border-radius: 50%;
      background: var(--surface-2);
      color: var(--accent-ink);
      border: 1px solid var(--border);
      font-weight: 800;
      line-height: 1;
    }
    .choices input:focus-visible + label { outline: 3px solid var(--accent); outline-offset: -3px; border-radius: 14px; }
    .choices input:checked + label { background: color-mix(in srgb, var(--accent-soft) 55%, transparent); border-color: var(--accent); }
    .choices input:checked + label .letter { color: var(--accent-soft); background: var(--accent-ink); border-color: var(--accent-ink); }

    .question.revealed .choices label { padding-inline-end: 8.5rem; }
    .choice-option {
      display: inline-block;
      padding: 0.18rem 0.55rem;
      border-radius: 999px;
      background: var(--surface-2);
      color: var(--text-secondary);
      border: 1px solid var(--border);
      font-weight: 700;
      font-size: 0.86rem;
    }
    .question.revealed .choices li.correct {
      background: color-mix(in srgb, var(--success-bg) 88%, var(--surface) 12%);
      border-color: var(--success);
    }
    .question.revealed .choices li.correct .letter { color: var(--success-bg); background: var(--success-ink); border-color: var(--success-ink); }
    .question.revealed .choices li.incorrect {
      background: linear-gradient(90deg, color-mix(in srgb, var(--danger-bg) 92%, var(--surface) 8%), color-mix(in srgb, var(--danger-bg) 76%, transparent));
      border-color: var(--danger);
      box-shadow: inset 4px 0 0 var(--danger);
    }
    .question.revealed .choices li.incorrect .letter { color: var(--danger-bg); background: var(--danger-ink); border-color: var(--danger-ink); }
    .question.revealed .choices li.incorrect label > span:last-child {
      text-decoration: line-through;
      text-decoration-thickness: 2px;
      text-decoration-color: color-mix(in srgb, var(--danger) 70%, transparent);
    }
    .question.revealed .choices li.correct.missed {
      background: linear-gradient(90deg, color-mix(in srgb, var(--success-bg) 82%, var(--surface) 18%), color-mix(in srgb, var(--warning-bg) 28%, var(--success-bg) 72%));
      border-color: var(--success);
      box-shadow: inset 4px 0 0 var(--success);
    }
    .question.revealed .choices li.correct.missed .letter { color: var(--success-bg); background: var(--success-ink); border-color: var(--success-ink); }
    .question.revealed .choices li::after {
      position: absolute;
      top: 50%;
      right: 0.8rem;
      transform: translateY(-50%);
      padding: 0.24rem 0.54rem;
      border-radius: 999px;
      font-size: 0.74rem;
      font-weight: 800;
    }
    .question.revealed .choices li.incorrect::after {
      content: "✕ Your answer";
      color: var(--danger-ink);
      background: color-mix(in srgb, var(--danger-bg) 84%, var(--surface) 16%);
      border: 1px solid color-mix(in srgb, var(--danger) 55%, var(--border));
    }
    .question.revealed .choices li.correct:not(.missed)::after {
      content: "✓ Correct";
      color: var(--success-ink);
      background: color-mix(in srgb, var(--success-bg) 84%, var(--surface) 16%);
      border: 1px solid color-mix(in srgb, var(--success) 55%, var(--border));
    }
    .question.revealed .choices li.correct.missed::after {
      content: "✓ Correct answer";
      color: var(--success-ink);
      background: color-mix(in srgb, var(--success-bg) 84%, var(--surface) 16%);
      border: 1px solid color-mix(in srgb, var(--success) 55%, var(--border));
    }

    .answer-status {
      margin-top: 0.7rem;
      padding: 0.6rem 0.85rem;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.9rem;
      min-block-size: 2.35rem;
    }
    .answer-status.empty { color: var(--muted); font-weight: 500; }
    .answer-status.correct, .answer-status.incorrect, .answer-status.partial {
      display: grid;
      grid-template-columns: auto 1fr;
      align-items: center;
      gap: 0.6rem;
      border: 1px solid transparent;
    }
    .answer-status.correct::before, .answer-status.incorrect::before, .answer-status.partial::before {
      display: inline-grid;
      place-items: center;
      min-inline-size: 1.6rem;
      min-block-size: 1.6rem;
      border-radius: 50%;
      font-weight: 900;
      line-height: 1;
    }
    .answer-status.correct { color: var(--success-ink); background: var(--success-bg); border-color: var(--success); }
    .answer-status.correct::before { content: "✓"; color: var(--success-bg); background: var(--success-ink); }
    .answer-status.incorrect { color: var(--danger-ink); background: var(--danger-bg); border-color: var(--danger); }
    .answer-status.incorrect::before { content: "✕"; color: var(--danger-bg); background: var(--danger-ink); }
    .answer-status.partial { color: var(--warning-ink); background: var(--warning-bg); border-color: var(--warning); }
    .answer-status.partial::before { content: "◐"; color: var(--warning-bg); background: var(--warning-ink); }

    /* Answer Shell, Vote Distribution, Self-Grade & Comments */
    .answer-shell { margin-top: 0.95rem; }
    .answer-locked {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.9rem;
      border: 1px dashed var(--border-strong);
      border-radius: 16px;
      padding: 0.75rem 0.9rem;
      background: color-mix(in srgb, var(--surface-2) 62%, transparent);
      color: var(--text-secondary);
      font-size: 0.9rem;
    }
    .answer-locked strong { color: var(--text); }
    .answer-revealed {
      display: none;
      border: 1px solid color-mix(in srgb, var(--success) 36%, var(--border));
      border-radius: 16px;
      padding: 0.95rem;
      background: color-mix(in srgb, var(--success-bg) 72%, var(--surface) 28%);
      color: var(--text);
    }
    .question.revealed .answer-locked { display: none; }
    .question.revealed .answer-revealed { display: block; animation: reveal 200ms ease-out; }
    @keyframes reveal { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .answer-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }
    .answer-card {
      border: 1px solid color-mix(in srgb, var(--success) 28%, var(--border));
      border-radius: 12px;
      padding: 0.7rem 0.8rem;
      background: rgb(var(--surface-rgb) / 0.84);
    }
    .answer-card .label-row { display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; margin-bottom: 0.25rem; }
    .answer-card .label { color: var(--success-ink); font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .answer-card strong { font-size: 1.02rem; }
    .mv-lines { font-size: 0.92rem; line-height: 1.5; }
    .mv-lines div + div { margin-top: 0.25rem; padding-top: 0.25rem; border-top: 1px dashed var(--border); }
    .confidence-badge {
      padding: 0.08rem 0.45rem;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 800;
      background: var(--warning-bg);
      color: var(--warning-ink);
      border: 1px solid color-mix(in srgb, var(--warning) 35%, var(--border));
    }
    .answer-card.answer-missing { background: var(--warning-bg); border-color: color-mix(in srgb, var(--warning) 30%, var(--border)); }
    .answer-card.answer-missing .label { color: var(--warning-ink); }

    .vote-bars {
      margin-top: 0.7rem;
      padding: 0.65rem 0.8rem;
      border-radius: 12px;
      background: rgb(var(--surface-rgb) / 0.82);
      border: 1px solid var(--border);
    }
    .vote-bars-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-secondary);
      margin-bottom: 0.4rem;
    }
    .vote-bar-row {
      display: grid;
      grid-template-columns: minmax(2.5rem, auto) 1fr auto;
      gap: 0.55rem;
      align-items: center;
      font-size: 0.82rem;
      margin-top: 0.28rem;
    }
    .vote-bar-track {
      block-size: 0.55rem;
      border-radius: 999px;
      background: var(--surface-2);
      overflow: hidden;
    }
    .vote-bar-fill {
      block-size: 100%;
      border-radius: 999px;
      background: var(--accent);
    }

    .self-grade-controls {
      margin-top: 0.75rem;
      padding: 0.6rem 0.8rem;
      border-radius: 12px;
      background: rgb(var(--surface-rgb) / 0.84);
      border: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
    }
    .self-grade-prompt { font-size: 0.84rem; font-weight: 700; color: var(--text-secondary); margin-inline-end: auto; }
    .btn-self-grade[aria-pressed="true"][data-self-grade="correct"] {
      background: var(--success);
      color: var(--success-contrast);
      border-color: var(--success);
    }
    .btn-self-grade[aria-pressed="true"][data-self-grade="incorrect"] {
      background: var(--danger);
      color: #fff;
      border-color: var(--danger);
    }

    .comments { margin-top: 0.8rem; border-top: 1px solid color-mix(in srgb, var(--success) 24%, var(--border)); padding-top: 0.75rem; }
    .comments > summary, .comments-more > summary {
      cursor: pointer;
      font-weight: 800;
      font-size: 0.88rem;
      color: var(--text);
    }
    .comments-more { margin-top: 0.5rem; padding-top: 0.45rem; border-top: 1px dashed var(--border); }
    .comment { padding: 0.65rem 0; border-top: 1px solid color-mix(in srgb, var(--success) 18%, var(--border)); }
    .comment:first-of-type { border-top: 0; }
    .comment-meta { color: var(--text-secondary); font-size: 0.82rem; margin-bottom: 0.22rem; }
    .comment .badge {
      display: inline-block;
      margin-inline-start: 0.35rem;
      padding: 0.1rem 0.42rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-ink);
      font-size: 0.7rem;
      font-weight: 800;
    }
    .answer-tools {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.75rem;
    }
    .thread-link {
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--accent-ink);
      text-decoration: underline;
    }

    /* Exhibits & Zoom Trigger */
    .exhibits { margin-top: 0.9rem; display: grid; gap: 0.85rem; }
    .exhibit { margin: 0; border: 1px solid var(--border); border-radius: 16px; padding: 0.7rem; background: rgb(var(--surface-rgb) / 0.75); }
    .exhibit-zoom-btn {
      display: block;
      inline-size: 100%;
      padding: 0;
      border: 0;
      border-radius: 12px;
      background: transparent;
      cursor: zoom-in;
      box-shadow: none;
    }
    .exhibit-zoom-btn:hover { transform: none; box-shadow: 0 0 0 2px var(--accent); }
    .exhibit img { display: block; margin: 0 auto; max-inline-size: 100%; height: auto; border-radius: 10px; border: 1px solid var(--border); }
    .exhibit figcaption { margin-top: 0.45rem; text-align: center; color: var(--text-secondary); font-size: 0.8rem; font-weight: 700; }
    .exhibit pre { margin: 0; }
    .exhibit table { border-collapse: collapse; inline-size: 100%; font-size: 0.9rem; }
    .exhibit table th, .exhibit table td { border: 1px solid var(--border); padding: 0.4rem 0.6rem; }
    .exhibit-missing { padding: 0.9rem; text-align: center; background: var(--warning-bg); color: var(--warning-ink); }
    .exhibit-missing-title { font-weight: 800; margin-bottom: 0.3rem; }
    .exhibit-missing a { color: var(--accent-ink); text-decoration: underline; }

    /* Native Modal <dialog> (modern-web-guidance: dialog & light-dismiss-a-dialog) */
    dialog.app-dialog {
      border: 1px solid var(--border-strong);
      border-radius: var(--radius);
      padding: 1.15rem;
      background: var(--surface);
      color: var(--text);
      box-shadow: var(--shadow);
      max-inline-size: min(94vw, 520px);
    }
    dialog.lightbox-dialog {
      max-inline-size: min(96vw, 1280px);
      max-block-size: 92vh;
      padding: 0.9rem;
    }
    dialog.lightbox-dialog[open] {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      gap: 0.65rem;
    }
    dialog:modal {
      overscroll-behavior: contain;
    }
    dialog::backdrop {
      overflow: hidden;
      overscroll-behavior: contain;
      background: rgba(8, 12, 22, 0.72);
      backdrop-filter: blur(3px);
    }
    .dialog-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }
    .dialog-header h2 { margin: 0; font-size: 1rem; }
    .lightbox-stage { overflow: auto; display: grid; place-items: center; }
    .lightbox-stage img { max-inline-size: 100%; max-block-size: 80vh; width: auto; height: auto; }
    .dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }

    /* Drag-drop & other widgets */
    .dragdrop-widget, .other-widget {
      margin-top: 0.9rem;
      padding: 0.9rem;
      border: 1px dashed var(--border-strong);
      border-radius: 16px;
      background: color-mix(in srgb, var(--surface-2) 60%, transparent);
    }
    .widget-note { color: var(--text-secondary); font-size: 0.88rem; margin: 0 0 0.65rem; }
    .dragdrop-board { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 0.9rem; margin-top: 0.65rem; }
    .dragdrop-column { border: 1px solid var(--border); border-radius: 12px; padding: 0.75rem; background: rgb(var(--surface-rgb) / 0.68); }
    .dragdrop-column-title { margin: 0 0 0.5rem; font-size: 0.76rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); font-weight: 800; }
    .dragdrop-chips { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 0.45rem; min-block-size: 2.6rem; }
    .dragdrop-targets { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.45rem; }
    .dragdrop-chip {
      cursor: grab;
      user-select: none;
      padding: 0.38rem 0.7rem;
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.88);
      border: 1px solid var(--border);
      font-weight: 700;
      font-size: 0.84rem;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }
    .dragdrop-chip.selected { background: var(--accent-soft); color: var(--accent-ink); border-color: var(--accent); }
    .dragdrop-chip.placed { opacity: 0.55; cursor: default; background: var(--surface-2); color: var(--text-secondary); border-style: dashed; }
    .dragdrop-target {
      position: relative;
      padding: 0.55rem 2.1rem 0.55rem 0.8rem;
      border-radius: 10px;
      border: 1px dashed var(--border-strong);
      background: rgb(var(--surface-rgb) / 0.85);
      color: var(--text-secondary);
      min-block-size: 2.3rem;
      font-size: 0.88rem;
    }
    .dragdrop-target.drop-hover { border-color: var(--accent); background: var(--accent-soft); }
    .dragdrop-target.filled { color: var(--text); border-style: solid; background: rgb(var(--surface-rgb)); font-weight: 700; }
    .dragdrop-target .dragdrop-clear {
      position: absolute;
      top: 50%;
      right: 0.45rem;
      transform: translateY(-50%);
      min-inline-size: 1.55rem;
      min-block-size: 1.55rem;
      padding: 0;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--surface-2);
      color: var(--text-secondary);
      display: none;
    }
    .dragdrop-target.filled .dragdrop-clear { display: inline-flex; }

    .nav-floating {
      position: fixed;
      left: 50%;
      bottom: max(0.85rem, env(safe-area-inset-bottom));
      z-index: 110;
      transform: translateX(-50%);
      display: flex;
      gap: 0.45rem;
      align-items: center;
      padding: 0.4rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.9);
      backdrop-filter: blur(16px);
      box-shadow: var(--shadow);
    }
    .nav-floating button { min-inline-size: 2.8rem; min-block-size: 2.65rem; padding: 0 0.95rem; }
    .nav-floating .nav-status { min-inline-size: 92px; text-align: center; color: var(--text-secondary); font-size: 0.84rem; font-weight: 800; }

    .mobile-only { display: none !important; }
    .desktop-only { display: inline-flex !important; }

    @media (max-width: 1060px) {
      .study-layout { grid-template-columns: 1fr; }
      .study-map { position: relative; top: auto; max-block-size: none; }
      .study-map.collapsed { display: none; }
      .toc-links { grid-template-columns: repeat(auto-fill, minmax(58px, 1fr)); }
      .mobile-only { display: inline-flex !important; }
      .desktop-only { display: none !important; }
      .nav-floating { display: flex; }
    }
    @media (min-width: 1061px) {
      .nav-floating { display: none !important; }
    }
    @media (max-width: 720px) {
      .header-inner { flex-direction: column; align-items: stretch; gap: 0.45rem; }
      .controls { justify-content: flex-start; }
      main { padding: 0.85rem 0.7rem 6rem; }
      .q-header { flex-direction: column; }
      .q-actions { inline-size: 100%; justify-content: stretch; }
      .q-actions button { flex: 1; }
      .answer-grid, .dragdrop-board { grid-template-columns: 1fr; }
      .answer-locked { align-items: stretch; flex-direction: column; }
      .nav-floating { left: 0.75rem; right: 0.75rem; transform: none; justify-content: space-between; }
      .nav-floating button { flex: 1; }
    }
    @media (max-width: 560px) {
      .question.revealed .choices label { padding-inline-end: 0.95rem; padding-bottom: 2.25rem; }
      .question.revealed .choices li::after { top: auto; right: auto; bottom: 0.55rem; left: 3.4rem; transform: none; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { scroll-behavior: auto !important; animation: none !important; transition: none !important; }
    }
    @media (prefers-reduced-motion: no-preference) {
      .question.shake-incorrect .answer-status.incorrect { animation: answerShake 340ms ease-out; }
      @keyframes answerShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        50% { transform: translateX(4px); }
        75% { transform: translateX(-2px); }
      }
    }
    @media print {
      header, .study-map, .controls, .study-toolbar, .nav-floating, #progress-bar, .skip-link, .answer-locked, .answer-tools { display: none !important; }
      body { background: #fff; color: #000; font-size: 11pt; padding-bottom: 0; }
      .overview-banner { display: none; }
      main { padding: 0; max-inline-size: none; }
      .study-layout, .q-case-grid { display: block; }
      .question { display: block !important; box-shadow: none; border: 1px solid #bbb; page-break-inside: avoid; }
      .answer-revealed { display: block !important; }
    }
  </style>
</head>
<body data-exam="$exam">
  <a class="skip-link btn" href="#main-content">Skip to questions</a>
  <div id="progress-bar" role="progressbar" aria-label="Study progress"></div>
  <header class="app-header">
    <div class="header-inner">
      <div class="brand">
        <div class="brand-row">
          <button type="button" class="secondary" popovertarget="exam-switcher-menu" aria-label="Switch study guide">Exams ▾</button>
          <h1>$title</h1>
        </div>
        <div class="stats">$stats · <span id="progress-text">0 reviewed</span></div>
      </div>
      <div class="controls" aria-label="Study controls">
        <button id="resume-unreviewed" class="secondary" type="button" title="Jump to first unreviewed question">Resume</button>
        <button id="show-all-answers" class="secondary" type="button" title="Show or hide all answers">Show answers</button>
        <button id="reset-progress-btn" class="ghost" type="button" title="Reset progress for this exam">Reset</button>
        <button id="theme-toggle" class="secondary" type="button" title="Toggle dark mode">🌙</button>
        <button id="toggle-map" class="ghost mobile-only" type="button" title="Toggle question map">Map</button>
      </div>
    </div>
  </header>
  $exam_switcher
  <main id="main-content">
"""

HTML_TAIL = """
  </main>
  <dialog id="exhibit-lightbox" class="app-dialog lightbox-dialog" closedby="any" aria-labelledby="lightbox-title">
    <div class="dialog-header">
      <h2 id="lightbox-title">Exhibit preview</h2>
      <form method="dialog"><button type="submit" class="secondary" autofocus>Close</button></form>
    </div>
    <div class="lightbox-stage">
      <img id="lightbox-img" src="" alt="">
    </div>
  </dialog>
  <dialog id="reset-dialog" class="app-dialog" closedby="any" aria-labelledby="reset-dialog-title">
    <h2 id="reset-dialog-title">Reset study progress?</h2>
    <p>This clears saved answers, bookmarks, self-grades, and reviewed status for this exam only.</p>
    <form method="dialog" class="dialog-actions">
      <button type="submit" value="cancel" class="secondary" autofocus>Cancel</button>
      <button type="submit" value="reset" id="confirm-reset-btn">Reset progress</button>
    </form>
  </dialog>
  <div class="nav-floating" aria-label="Question navigation">
    <button class="secondary nav-prev-btn" type="button" title="Previous question (←)" aria-label="Previous question">←</button>
    <div class="nav-status" aria-live="polite">Q 1</div>
    <button class="secondary nav-next-btn" type="button" title="Next question (→)" aria-label="Next question">→</button>
  </div>
  <script>
    const EXAM_SLUG = document.body.dataset.exam || '$exam';
    const STORAGE_PREFIX = 'examguide-v2-$exam';
    const appHeader = document.querySelector('header.app-header');
    if (appHeader && 'ResizeObserver' in window) {
      new ResizeObserver(() => {
        document.documentElement.style.setProperty('--header-height', `${appHeader.offsetHeight}px`);
      }).observe(appHeader);
    }
    const STORAGE_KEY = `${STORAGE_PREFIX}-reviewed`;
    const SELECTIONS_KEY = `${STORAGE_PREFIX}-selections`;
    const BOOKMARKS_KEY = `${STORAGE_PREFIX}-bookmarks`;
    const SELFGRADE_KEY = `${STORAGE_PREFIX}-selfgrade`;
    const DRAGDROP_KEY = `${STORAGE_PREFIX}-dragdrop`;

    // One-time migration from legacy location.pathname keys so existing progress carries over
    function migrateLegacyStorage(v2Key, legacySuffix) {
      if (localStorage.getItem(v2Key) !== null) return;
      const legacyVal = localStorage.getItem(location.pathname + legacySuffix);
      if (legacyVal !== null) localStorage.setItem(v2Key, legacyVal);
    }
    migrateLegacyStorage(STORAGE_KEY, '-reviewed');
    migrateLegacyStorage(SELECTIONS_KEY, '-selections');
    migrateLegacyStorage(DRAGDROP_KEY, '-dragdrop');

    // Light-dismiss fallback for browsers without native HTMLDialogElement.prototype.closedBy
    if (!('closedBy' in HTMLDialogElement.prototype)) {
      const outsideDialog = (e, dialog) => {
        const r = dialog.getBoundingClientRect();
        return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      };
      for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {
        let pressedOutside = false;
        dialog.addEventListener('pointerdown', (e) => { pressedOutside = outsideDialog(e, dialog); });
        dialog.addEventListener('pointerup', (e) => { if (pressedOutside && outsideDialog(e, dialog)) dialog.close(); });
      }
    }

    const questions = Array.from(document.querySelectorAll('.question'));
    const ids = questions.map(q => q.id);
    let visibleIds = [...ids];
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const heroPct = document.getElementById('hero-pct');
    const heroAttempted = document.getElementById('hero-attempted');
    const heroCorrect = document.getElementById('hero-correct');
    const heroReviewed = document.getElementById('hero-reviewed');
    const heroRemaining = document.getElementById('hero-remaining');
    const navStatuses = document.querySelectorAll('.nav-status');
    progressBar.setAttribute('aria-valuemin', '0');
    progressBar.setAttribute('aria-valuemax', String(ids.length));

    const themeBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('examguide-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', savedTheme || (prefersDark ? 'dark' : 'light'));
    function syncThemeButton() {
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      themeBtn.textContent = dark ? '☀️' : '🌙';
      themeBtn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    }
    themeBtn.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('examguide-theme', next);
      syncThemeButton();
    });
    syncThemeButton();

    let selections = {};
    let reviewed = new Set();
    let bookmarks = new Set();
    let selfGrades = {};
    let dragdropSelections = {};
    try { selections = JSON.parse(localStorage.getItem(SELECTIONS_KEY) || '{}'); } catch (e) { selections = {}; }
    try { reviewed = new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')); } catch (e) { reviewed = new Set(); }
    try { bookmarks = new Set(JSON.parse(localStorage.getItem(BOOKMARKS_KEY) || '[]')); } catch (e) { bookmarks = new Set(); }
    try { selfGrades = JSON.parse(localStorage.getItem(SELFGRADE_KEY) || '{}'); } catch (e) { selfGrades = {}; }
    try { dragdropSelections = JSON.parse(localStorage.getItem(DRAGDROP_KEY) || '{}'); } catch (e) { dragdropSelections = {}; }

    function saveSelections() { localStorage.setItem(SELECTIONS_KEY, JSON.stringify(selections)); updateProgress(); }
    function saveReviewed() { localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(reviewed))); updateProgress(); }
    function saveBookmarks() { localStorage.setItem(BOOKMARKS_KEY, JSON.stringify(Array.from(bookmarks))); updateProgress(); }
    function saveSelfGrades() { localStorage.setItem(SELFGRADE_KEY, JSON.stringify(selfGrades)); updateProgress(); }
    function saveDragdrop() { localStorage.setItem(DRAGDROP_KEY, JSON.stringify(dragdropSelections)); }

    function getSelected(q) { return new Set(selections[q.id] || []); }
    function setSelected(q, letters) {
      if (letters.size === 0) delete selections[q.id];
      else selections[q.id] = Array.from(letters);
      saveSelections();
    }
    function getCorrect(q) {
      return new Set(Array.from(q.querySelectorAll('.choices li.correct')).map(li => li.dataset.letter).filter(Boolean));
    }
    function isQuestionAttempted(q) {
      if (!q) return false;
      if (q.querySelector('.choices')) return Boolean(selections[q.id] && selections[q.id].length > 0);
      return Boolean(selfGrades[q.id]);
    }
    function isCorrect(q) {
      if (!q) return false;
      if (!q.querySelector('.choices')) return selfGrades[q.id] === 'correct';
      const selected = getSelected(q);
      const correct = getCorrect(q);
      if (correct.size === 0) return false;
      return selected.size > 0 && selected.size === correct.size && [...selected].every(x => correct.has(x));
    }
    function isNeedsWork(q) {
      if (!q) return false;
      if (!q.querySelector('.choices')) return selfGrades[q.id] === 'incorrect';
      return isQuestionAttempted(q) && !isCorrect(q);
    }

    const showAllBtn = document.getElementById('show-all-answers');
    function syncAnswerButtons() {
      document.querySelectorAll('.btn-toggle-answer').forEach(btn => {
        const q = btn.closest('.question');
        const revealed = q.classList.contains('revealed');
        btn.textContent = revealed ? 'Hide answer' : 'Reveal answer';
        btn.setAttribute('aria-pressed', String(revealed));
      });
      const allRevealed = questions.length > 0 && questions.every(q => q.classList.contains('revealed'));
      showAllBtn.textContent = allRevealed ? 'Hide answers' : 'Show answers';
      showAllBtn.setAttribute('aria-pressed', String(allRevealed));
    }
    function toggleQuestionReveal(q) {
      if (!q) return;
      const wasHidden = !q.classList.contains('revealed');
      q.classList.toggle('revealed');
      updateAnswerFeedback(q);
      if (wasHidden && q.dataset.result === 'incorrect') {
        q.classList.remove('shake-incorrect');
        void q.offsetWidth;
        q.classList.add('shake-incorrect');
        setTimeout(() => q.classList.remove('shake-incorrect'), 420);
      }
      syncAnswerButtons();
    }
    function setAllRevealed(revealed) {
      questions.forEach(q => {
        q.classList.toggle('revealed', revealed);
        updateAnswerFeedback(q);
      });
      syncAnswerButtons();
    }
    showAllBtn.addEventListener('click', () => {
      const anyHidden = questions.some(q => !q.classList.contains('revealed'));
      if (anyHidden && !confirm('Reveal answers for every question?')) return;
      setAllRevealed(anyHidden);
    });
    document.querySelectorAll('.btn-toggle-answer').forEach(btn => {
      btn.addEventListener('click', () => toggleQuestionReveal(btn.closest('.question')));
    });

    function updateAnswerFeedback(q) {
      const revealed = q.classList.contains('revealed');
      const selected = getSelected(q);
      const correct = getCorrect(q);
      const hasChoices = !!q.querySelector('.choices');
      q.querySelectorAll('.choices li').forEach(li => {
        const letter = li.dataset.letter;
        li.classList.remove('incorrect', 'missed');
        if (revealed) {
          if (selected.has(letter) && !correct.has(letter)) li.classList.add('incorrect');
          if (!selected.has(letter) && correct.has(letter)) li.classList.add('missed');
        }
      });
      q.querySelectorAll('.btn-self-grade').forEach(btn => {
        btn.setAttribute('aria-pressed', String(selfGrades[q.id] === btn.dataset.selfGrade));
      });
      const status = q.querySelector('.answer-status');
      if (!status) return;
      delete q.dataset.result;
      if (!hasChoices) {
        const sg = selfGrades[q.id];
        if (q.dataset.qtype === 'hotspot') {
          const mostVoted = q.dataset.mostVoted || '';
          if (!revealed) {
            status.className = 'answer-status empty';
            status.textContent = 'Review the exhibits above and reason about which options to select.';
          } else if (sg === 'correct') {
            status.className = 'answer-status correct';
            status.textContent = 'Self-graded: Got it right!';
          } else if (sg === 'incorrect') {
            q.dataset.result = 'incorrect';
            status.className = 'answer-status incorrect';
            status.textContent = 'Self-graded: Flagged for more practice.';
          } else if (mostVoted) {
            status.className = 'answer-status';
            status.textContent = `Community answer: ${mostVoted}`;
          } else {
            status.className = 'answer-status empty';
            status.textContent = 'HOTSPOT answer not available from ExamTopics.';
          }
        } else if (q.querySelector('.dragdrop-widget')) {
          const mostVoted = q.dataset.mostVoted || '';
          if (!revealed) {
            status.className = 'answer-status empty';
            status.textContent = 'Reason about the placements above, then reveal to compare against the community answer.';
          } else if (sg === 'correct') {
            status.className = 'answer-status correct';
            status.textContent = 'Self-graded: Got it right!';
          } else if (sg === 'incorrect') {
            q.dataset.result = 'incorrect';
            status.className = 'answer-status incorrect';
            status.textContent = 'Self-graded: Flagged for more practice.';
          } else if (mostVoted) {
            status.className = 'answer-status';
            status.textContent = `Community answer: ${mostVoted}`;
          } else {
            status.className = 'answer-status empty';
            status.textContent = 'DRAG DROP answer not available from ExamTopics.';
          }
        } else {
          status.className = 'answer-status empty';
          status.textContent = revealed ? 'Answer not provided by ExamTopics for this question type.' : 'This question type is not interactive.';
        }
        return;
      }
      if (!revealed) {
        if (selected.size === 0) { status.className = 'answer-status empty'; status.textContent = 'Select your answer (or press 1–9), then reveal (A).'; }
        else { status.className = 'answer-status'; status.textContent = `${selected.size} selected. Ready to reveal (A).`; }
        return;
      }
      const missed = [...correct].filter(x => !selected.has(x));
      const wrong = [...selected].filter(x => !correct.has(x));
      if (correct.size === 0) {
        status.className = 'answer-status empty';
        status.textContent = 'Answer not provided by ExamTopics.';
        return;
      }
      if (selected.size === 0) {
        q.dataset.result = 'incorrect';
        status.className = 'answer-status incorrect';
        status.textContent = `No answer selected. Correct: ${[...correct].sort().join(', ')}`;
      } else if (isCorrect(q)) {
        q.dataset.result = 'correct';
        status.className = 'answer-status correct';
        status.textContent = 'Correct!';
      } else {
        const choiceList = q.querySelector('.choices');
        const isMulti = choiceList && choiceList.dataset.multiple === 'true';
        if (isMulti && wrong.length === 0 && missed.length > 0 && selected.size > 0) {
          status.className = 'answer-status partial';
          status.textContent = `Partially correct — ${selected.size} of ${correct.size} correct. Missing: ${[...missed].sort().join(', ')}`;
        } else {
          q.dataset.result = 'incorrect';
          status.className = 'answer-status incorrect';
          status.textContent = `Incorrect. You chose ${[...selected].sort().join(', ')}; correct: ${[...correct].sort().join(', ')}`;
        }
      }
    }

    questions.forEach(q => {
      q.querySelectorAll('.btn-self-grade').forEach(btn => {
        btn.addEventListener('click', () => {
          const val = btn.dataset.selfGrade;
          if (selfGrades[q.id] === val) delete selfGrades[q.id];
          else selfGrades[q.id] = val;
          saveSelfGrades();
          updateAnswerFeedback(q);
        });
      });
      const choiceList = q.querySelector('.choices');
      if (!choiceList) {
        updateAnswerFeedback(q);
        return;
      }
      const saved = getSelected(q);
      choiceList.querySelectorAll('input').forEach(input => {
        if (saved.has(input.value)) input.checked = true;
        input.addEventListener('change', () => {
          if (q.classList.contains('revealed')) return;
          const selected = new Set();
          choiceList.querySelectorAll('input:checked').forEach(inp => selected.add(inp.value));
          setSelected(q, selected);
          updateAnswerFeedback(q);
        });
      });
      updateAnswerFeedback(q);
    });

    function updateReviewButton(btn, id) {
      const isReviewed = reviewed.has(id);
      btn.setAttribute('aria-pressed', String(isReviewed));
      btn.textContent = isReviewed ? 'Reviewed ✓' : 'Mark reviewed';
      btn.classList.toggle('active', isReviewed);
    }
    function updateBookmarkButton(btn, id) {
      const isBm = bookmarks.has(id);
      btn.setAttribute('aria-pressed', String(isBm));
      btn.textContent = isBm ? '★ Saved' : '☆ Save';
      btn.classList.toggle('bookmarked', isBm);
    }

    let activeFilter = 'all';
    let searchQuery = '';

    function matchesFilter(q) {
      if (activeFilter === 'unreviewed' && reviewed.has(q.id)) return false;
      if (activeFilter === 'incorrect' && !isNeedsWork(q)) return false;
      if (activeFilter === 'bookmarked' && !bookmarks.has(q.id)) return false;
      if (activeFilter === 'casestudy' && !q.classList.contains('is-case-study')) return false;
      if (activeFilter === 'nonmcq' && q.querySelector('.choices')) return false;
      if (activeFilter === 'contested' && q.dataset.contested !== 'true') return false;
      if (searchQuery) {
        const hay = (q.dataset.search || q.textContent || '').toLowerCase();
        if (!hay.includes(searchQuery)) return false;
      }
      return true;
    }

    function applyFilters(opts = {}) {
      visibleIds = questions.filter(matchesFilter).map(q => q.id);
      const visibleSet = new Set(visibleIds);
      document.querySelectorAll('.toc-links a').forEach(a => {
        const href = a.getAttribute('href') || '';
        const id = href.startsWith('#') ? href.slice(1) : '';
        a.classList.toggle('filtered-out', Boolean(id) && !visibleSet.has(id));
      });
      const countEl = document.getElementById('filter-match-count');
      if (countEl) countEl.textContent = `${visibleIds.length} of ${ids.length} shown`;
      const emptyEl = document.getElementById('filter-empty-state');
      if (emptyEl) emptyEl.hidden = visibleIds.length > 0;

      if (visibleIds.length === 0) {
        questions.forEach(q => q.classList.remove('active', 'current'));
        syncNavButtons();
        return;
      }
      const curId = ids[currentIndex];
      if (!visibleSet.has(curId)) {
        const nextIdx = ids.indexOf(visibleIds[0]);
        if (nextIdx >= 0) syncCurrent(nextIdx, { replaceOnly: true, noScroll: opts.noScroll });
      } else {
        syncNavButtons();
      }
    }

    function updateProgress() {
      const total = ids.length || 1;
      const attempted = questions.filter(isQuestionAttempted).length;
      const correctCount = questions.filter(q => isQuestionAttempted(q) && isCorrect(q)).length;
      const pct = Math.round((reviewed.size / total) * 100);
      progressBar.style.width = pct + '%';
      progressBar.style.inlineSize = pct + '%';
      progressBar.setAttribute('aria-valuenow', String(reviewed.size));
      progressText.textContent = `${reviewed.size}/${ids.length} reviewed · ${attempted} attempted · ${correctCount} correct`;
      if (heroPct) heroPct.textContent = `${pct}%`;
      if (heroAttempted) heroAttempted.textContent = String(attempted);
      if (heroCorrect) heroCorrect.textContent = String(correctCount);
      if (heroReviewed) heroReviewed.textContent = String(reviewed.size);
      if (heroRemaining) heroRemaining.textContent = String(Math.max(ids.length - reviewed.size, 0));
      ids.forEach(id => {
        const q = document.getElementById(id);
        const isRev = reviewed.has(id);
        const isBm = bookmarks.has(id);
        if (q) q.classList.toggle('reviewed', isRev);
        document.querySelectorAll(`.toc-links a[href="#${id}"]`).forEach(link => {
          link.classList.toggle('reviewed', isRev);
          link.classList.toggle('bookmarked', isBm);
        });
      });
      document.querySelectorAll('.btn-review').forEach(btn => updateReviewButton(btn, btn.closest('.question').id));
      document.querySelectorAll('.btn-bookmark').forEach(btn => updateBookmarkButton(btn, btn.closest('.question').id));
      applyFilters({ noScroll: true });
    }

    document.querySelectorAll('.btn-review').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.question').id;
        reviewed.has(id) ? reviewed.delete(id) : reviewed.add(id);
        saveReviewed();
      });
    });
    document.querySelectorAll('.btn-bookmark').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.question').id;
        bookmarks.has(id) ? bookmarks.delete(id) : bookmarks.add(id);
        saveBookmarks();
      });
    });

    /* Search & filter controls */
    const searchInput = document.getElementById('question-search');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        searchQuery = searchInput.value.trim().toLowerCase();
        applyFilters({ noScroll: true });
      });
    }
    document.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        activeFilter = chip.dataset.filter || 'all';
        document.querySelectorAll('.filter-chip').forEach(c => c.setAttribute('aria-pressed', String(c === chip)));
        applyFilters();
      });
    });
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener('click', () => {
        activeFilter = 'all';
        searchQuery = '';
        if (searchInput) searchInput.value = '';
        document.querySelectorAll('.filter-chip').forEach(c => c.setAttribute('aria-pressed', String(c.dataset.filter === 'all')));
        applyFilters();
      });
    }

    /* Sidebar map mode switcher (By Skill Area vs By Question #) */
    document.querySelectorAll('.map-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mapMode;
        document.querySelectorAll('.map-mode-btn').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
        const bySkill = document.getElementById('toc-by-skill');
        const byNum = document.getElementById('toc-by-number');
        if (bySkill && byNum) {
          bySkill.hidden = mode !== 'skill';
          byNum.hidden = mode !== 'number';
        }
      });
    });

    /* Case study Expand all / Collapse all */
    document.querySelectorAll('.cs-toggle-all').forEach(btn => {
      btn.addEventListener('click', () => {
        const panel = btn.closest('.case-study-panel');
        if (!panel) return;
        const expand = btn.getAttribute('aria-expanded') !== 'true';
        panel.querySelectorAll('details.cs-section').forEach(d => { d.open = expand; });
        btn.setAttribute('aria-expanded', String(expand));
        btn.textContent = expand ? 'Collapse all' : 'Expand all';
      });
    });
    document.addEventListener('toggle', (ev) => {
      if (!(ev.target instanceof HTMLDetailsElement) || !ev.target.classList.contains('cs-section')) return;
      const panel = ev.target.closest('.case-study-panel');
      if (!panel) return;
      const btn = panel.querySelector('.cs-toggle-all');
      if (!btn) return;
      const allOpen = Array.from(panel.querySelectorAll('details.cs-section')).every(d => d.open);
      btn.setAttribute('aria-expanded', String(allOpen));
      btn.textContent = allOpen ? 'Collapse all' : 'Expand all';
    }, { capture: true });

    /* Exhibit Zoom Lightbox & Reset Progress Dialog */
    const lightbox = document.getElementById('exhibit-lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxTitle = document.getElementById('lightbox-title');
    document.querySelectorAll('.exhibit-zoom-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!lightbox || !lightboxImg) return;
        lightboxImg.src = btn.dataset.zoomSrc || '';
        lightboxImg.alt = btn.dataset.zoomCaption || 'Exhibit';
        if (lightboxTitle) lightboxTitle.textContent = btn.dataset.zoomCaption || 'Exhibit preview';
        lightbox.showModal();
      });
    });

    const resetDialog = document.getElementById('reset-dialog');
    const resetBtn = document.getElementById('reset-progress-btn');
    if (resetBtn && resetDialog) {
      resetBtn.addEventListener('click', () => {
        resetDialog.returnValue = '';
        resetDialog.showModal();
      });
      resetDialog.addEventListener('close', () => {
        if (resetDialog.returnValue === 'reset') {
          selections = {};
          reviewed = new Set();
          bookmarks = new Set();
          selfGrades = {};
          dragdropSelections = {};
          [STORAGE_KEY, SELECTIONS_KEY, BOOKMARKS_KEY, SELFGRADE_KEY, DRAGDROP_KEY].forEach(k => localStorage.removeItem(k));
          questions.forEach(q => {
            q.classList.remove('revealed');
            q.querySelectorAll('.choices input').forEach(inp => { inp.checked = false; });
            updateAnswerFeedback(q);
          });
          syncAnswerButtons();
          updateProgress();
        }
        resetDialog.returnValue = '';
      });
    }

    /* ----- Drag-drop interactivity ----- */
    function attachDragdropWidget(q) {
      const widget = q.querySelector('.dragdrop-widget');
      if (!widget || !widget.classList.contains('dragdrop-widget-interactive')) return;
      const chipsContainer = widget.querySelector('.dragdrop-source .dragdrop-chips');
      const targetsContainer = widget.querySelector('.dragdrop-targets');
      const chips = chipsContainer ? Array.from(chipsContainer.querySelectorAll('.dragdrop-chip')) : [];
      const targets = targetsContainer ? Array.from(targetsContainer.querySelectorAll('.dragdrop-target')) : [];
      if (!chips.length || !targets.length) return;

      const saved = dragdropSelections[q.id] || {};
      let activeChip = null;
      function persist() { dragdropSelections[q.id] = saved; saveDragdrop(); }
      function placedChipIdx(targetIdx) {
        return Object.prototype.hasOwnProperty.call(saved, String(targetIdx)) ? saved[String(targetIdx)] : undefined;
      }
      function placeChip(targetIdx, chipIdx) {
        if (placedChipIdx(targetIdx) === chipIdx) return;
        for (const [tIdx, cIdx] of Object.entries(saved)) {
          if (Number(cIdx) === Number(chipIdx)) delete saved[tIdx];
        }
        saved[String(targetIdx)] = Number(chipIdx);
        render();
        persist();
      }
      function clearTarget(targetIdx) {
        if (placedChipIdx(targetIdx) === undefined) return;
        delete saved[String(targetIdx)];
        render();
        persist();
      }
      function clearAll() {
        for (const k of Object.keys(saved)) delete saved[k];
        render();
        persist();
      }
      function render() {
        chips.forEach(chip => chip.classList.remove('placed', 'selected', 'dragging'));
        const placedChipIdxs = new Set(Object.values(saved).map(Number));
        chips.forEach(chip => {
          if (placedChipIdxs.has(Number(chip.dataset.value))) chip.classList.add('placed');
        });
        targets.forEach(target => {
          const tIdx = Number(target.dataset.target);
          const labelEl = target.querySelector('.dragdrop-target-label');
          const chipIdx = placedChipIdx(tIdx);
          if (chipIdx !== undefined) {
            const chip = chips.find(c => Number(c.dataset.value) === Number(chipIdx));
            if (chip) {
              labelEl.textContent = chip.dataset.label || chip.textContent.trim();
              target.classList.add('filled');
            }
          } else {
            labelEl.textContent = target.dataset.placeholder || '';
            target.classList.remove('filled');
          }
        });
      }
      render();
      chips.forEach(chip => {
        const chipIdx = Number(chip.dataset.value);
        chip.addEventListener('click', () => {
          if (q.classList.contains('revealed')) return;
          if (chip.classList.contains('placed')) {
            for (const [tIdx, cIdx] of Object.entries(saved)) {
              if (Number(cIdx) === chipIdx) delete saved[tIdx];
            }
            render(); persist(); return;
          }
          if (activeChip === chip) { activeChip = null; chip.classList.remove('selected'); }
          else { chips.forEach(c => c.classList.remove('selected')); activeChip = chip; chip.classList.add('selected'); }
        });
        chip.addEventListener('dragstart', (e) => {
          if (q.classList.contains('revealed')) return;
          e.dataTransfer.setData('text/plain', String(chipIdx));
          e.dataTransfer.effectAllowed = 'move';
        });
        chip.addEventListener('keydown', (e) => {
          if (q.classList.contains('revealed')) return;
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); chip.click(); }
        });
      });
      targets.forEach(target => {
        const tIdx = Number(target.dataset.target);
        target.addEventListener('click', (ev) => {
          if (q.classList.contains('revealed') || ev.target.closest('.dragdrop-clear')) return;
          if (activeChip) {
            placeChip(tIdx, Number(activeChip.dataset.value));
            activeChip.classList.remove('selected');
            activeChip = null;
          } else if (placedChipIdx(tIdx) !== undefined) clearTarget(tIdx);
        });
        target.addEventListener('dragover', (e) => {
          if (q.classList.contains('revealed')) return;
          e.preventDefault();
          target.classList.add('drop-hover');
        });
        target.addEventListener('dragleave', () => target.classList.remove('drop-hover'));
        target.addEventListener('drop', (e) => {
          if (q.classList.contains('revealed')) return;
          e.preventDefault();
          target.classList.remove('drop-hover');
          const chipIdx = Number(e.dataTransfer.getData('text/plain'));
          if (Number.isFinite(chipIdx)) placeChip(tIdx, chipIdx);
        });
        const clearBtn = target.querySelector('.dragdrop-clear');
        if (clearBtn) {
          clearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!q.classList.contains('revealed')) clearTarget(Number(clearBtn.dataset.target));
          });
        }
      });
      let resetDdBtn = widget.querySelector('.dragdrop-reset');
      if (!resetDdBtn) {
        resetDdBtn = document.createElement('button');
        resetDdBtn.type = 'button';
        resetDdBtn.className = 'secondary dragdrop-reset';
        resetDdBtn.textContent = 'Reset placements';
        widget.appendChild(resetDdBtn);
      }
      resetDdBtn.addEventListener('click', () => { if (!q.classList.contains('revealed')) clearAll(); });
    }
    questions.forEach(attachDragdropWidget);

    let currentIndex = 0;
    function syncCurrent(index, opts = {}) {
      if (!ids.length) return;
      currentIndex = Math.max(0, Math.min(index, ids.length - 1));
      const activeId = ids[currentIndex];
      questions.forEach((q, i) => {
        const isActive = i === currentIndex;
        q.classList.toggle('active', isActive);
        q.classList.toggle('current', isActive);
      });
      document.querySelectorAll('.toc-links a.current').forEach(a => a.classList.remove('current'));
      document.querySelectorAll(`.toc-links a[href="#${activeId}"]`).forEach(link => {
        link.classList.add('current');
        const parentChunk = link.closest('details.toc-chunk');
        if (parentChunk) parentChunk.open = true;
        if (!opts.noScroll && link.offsetParent !== null) link.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      const q = questions[currentIndex];
      const visPos = visibleIds.indexOf(activeId);
      const posStr = visPos >= 0 ? `${visPos + 1}/${visibleIds.length}` : `${currentIndex + 1}/${ids.length}`;
      navStatuses.forEach(el => { if (el && q) el.textContent = `${q.dataset.label || 'Q'} · ${posStr}`; });
      syncNavButtons();
      if (!opts.replaceOnly) history.pushState(null, '', `#${activeId}`);
    }
    function syncNavButtons() {
      const activeId = ids[currentIndex];
      const visIdx = visibleIds.indexOf(activeId);
      const atStart = visibleIds.length <= 1 || visIdx <= 0;
      const atEnd = visibleIds.length <= 1 || visIdx < 0 || visIdx >= visibleIds.length - 1;
      document.querySelectorAll('.nav-prev-btn').forEach(btn => {
        btn.disabled = atStart;
        btn.setAttribute('aria-disabled', String(atStart));
      });
      document.querySelectorAll('.nav-next-btn').forEach(btn => {
        btn.disabled = atEnd;
        btn.setAttribute('aria-disabled', String(atEnd));
      });
    }
    function goToQuestion(index) {
      if (!ids.length) return;
      index = Math.max(0, Math.min(index, ids.length - 1));
      syncCurrent(index);
      questions[currentIndex]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    function stepVisible(delta) {
      if (!visibleIds.length) return;
      const curVis = visibleIds.indexOf(ids[currentIndex]);
      const nextVis = Math.max(0, Math.min((curVis >= 0 ? curVis : 0) + delta, visibleIds.length - 1));
      const targetIdx = ids.indexOf(visibleIds[nextVis]);
      if (targetIdx >= 0) goToQuestion(targetIdx);
    }

    document.querySelectorAll('.nav-prev-btn').forEach(btn => btn.addEventListener('click', () => stepVisible(-1)));
    document.querySelectorAll('.nav-next-btn').forEach(btn => btn.addEventListener('click', () => stepVisible(1)));
    document.getElementById('resume-unreviewed').addEventListener('click', () => {
      const pool = visibleIds.length ? visibleIds : ids;
      const firstUnreviewed = pool.find(id => !reviewed.has(id));
      goToQuestion(firstUnreviewed ? ids.indexOf(firstUnreviewed) : ids.indexOf(pool[0]));
    });

    const studyMap = document.getElementById('study-map');
    const toggleMapBtn = document.getElementById('toggle-map');
    function setMapCollapsed(collapsed, opts = {}) {
      if (!studyMap) return;
      studyMap.classList.toggle('collapsed', collapsed);
      if (toggleMapBtn) {
        toggleMapBtn.textContent = collapsed ? 'Map' : 'Hide map';
        toggleMapBtn.setAttribute('aria-pressed', String(!collapsed));
        toggleMapBtn.setAttribute('aria-expanded', String(!collapsed));
        toggleMapBtn.setAttribute('aria-controls', 'study-map');
      }
      if (!collapsed && opts.scroll) studyMap.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (toggleMapBtn) {
      toggleMapBtn.addEventListener('click', () => setMapCollapsed(!studyMap.classList.contains('collapsed'), { scroll: true }));
    }

    document.querySelectorAll('.toc-links a, .cs-jumper-links a').forEach(a => {
      a.addEventListener('click', e => {
        const href = a.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        e.preventDefault();
        const idx = ids.indexOf(href.slice(1));
        if (idx >= 0) {
          if (!visibleIds.includes(ids[idx])) {
            activeFilter = 'all';
            searchQuery = '';
            if (searchInput) searchInput.value = '';
            document.querySelectorAll('.filter-chip').forEach(c => c.setAttribute('aria-pressed', String(c.dataset.filter === 'all')));
            applyFilters({ noScroll: true });
          }
          goToQuestion(idx);
          if (window.innerWidth <= 1060) setMapCollapsed(true);
        }
      });
    });

    document.addEventListener('keydown', e => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      if (document.querySelector('dialog[open]')) return;
      if (e.key === '/' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        searchInput?.focus();
        searchInput?.select();
        return;
      }
      if (e.target.matches('input, textarea, select, button, summary')) return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); stepVisible(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); stepVisible(1); }
      else if (e.key.toLowerCase() === 'a') {
        e.preventDefault();
        toggleQuestionReveal(questions[currentIndex]);
      } else if (e.key.toLowerCase() === 'r') {
        const id = ids[currentIndex];
        if (!id) return;
        reviewed.has(id) ? reviewed.delete(id) : reviewed.add(id);
        saveReviewed();
      } else if (e.key.toLowerCase() === 'b') {
        const id = ids[currentIndex];
        if (!id) return;
        bookmarks.has(id) ? bookmarks.delete(id) : bookmarks.add(id);
        saveBookmarks();
      } else if (/^[1-9]$/.test(e.key)) {
        const q = questions[currentIndex];
        if (!q || q.classList.contains('revealed')) return;
        const inputs = Array.from(q.querySelectorAll('.choices input'));
        const target = inputs[Number(e.key) - 1];
        if (target) {
          target.checked = target.type === 'checkbox' ? !target.checked : true;
          target.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });

    window.addEventListener('popstate', () => {
      const id = location.hash ? location.hash.slice(1) : ids[0];
      const idx = ids.indexOf(id);
      if (idx >= 0) syncCurrent(idx, { replaceOnly: true, noScroll: true });
    });

    updateProgress();
    syncAnswerButtons();
    if (window.innerWidth <= 1060) setMapCollapsed(true);
    const startId = location.hash ? location.hash.slice(1) : ids[0];
    syncCurrent(Math.max(0, ids.indexOf(startId)), { replaceOnly: true, noScroll: true });
  </script>
</body>
</html>
"""


def clean_html(text: str) -> str:
    """Preserve simple formatting while stripping risky tags."""
    if not text:
        return ""
    # Remove script/style tags and their contents.
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    return text


def render_choice_content(choice: dict[str, Any]) -> str:
    """Return sanitized HTML for a single choice's body.

    The crawler stores ``text`` (plain text) and ``text_html`` (raw HTML inside
    the ``<li>`` with the letter chip removed). For image- and code-based
    choices the plain ``text`` is empty but ``text_html`` carries the visual
    content, so we prefer ``text_html`` whenever it's non-empty. Image
    ``src`` attributes are rewritten so they resolve from ``guides/``.

    ExamTopics dropdown questions store the option index in both ``text`` and
    ``text_html`` (e.g. ``"1"``, ``"2"`` ...) without any human-readable label,
    so we render those rows as ``Option N`` rather than the bare digit. The
    actual option text would require context from the surrounding ``<option>``
    tags, which the dataset doesn't carry.
    """
    text_html = (choice.get("text_html") or "").strip()
    plain_text = (choice.get("text") or "").strip()
    letter = (choice.get("letter") or "").strip().upper()

    # Bare-digit dropdown fallback: render "Option N" when the dataset only
    # captured the option index.
    if (
        plain_text
        and text_html == plain_text
        and re.fullmatch(r"[1-9]", plain_text)
        and re.fullmatch(r"[A-J]", letter)
    ):
        return f'<span class="choice-option">Option {html.escape(plain_text)}</span>'

    if text_html:
        if SANITIZER_AVAILABLE and sanitize_exhibit_html is not None:
            cleaned = sanitize_exhibit_html(text_html)
        else:
            cleaned = clean_html(text_html)

        # Rewrite any local ``assets/...`` image src to a guides/ relative path.
        def _rewrite_img_src(match: re.Match[str]) -> str:
            prefix, src, suffix = match.group(1), match.group(2), match.group(3)
            if not src:
                return match.group(0)
            if src.startswith(("http://", "https://", "//", "data:")):
                return match.group(0)
            # The exhibit backfill stores paths like
            # ``assets/exhibits/dp-600/936848_A.png`` (relative to repo root).
            # The HTML file lives in ``guides/`` so we add ``../``.
            stripped = src.lstrip("/")
            return f'{prefix}../{stripped}{suffix}'

        cleaned = re.sub(
            r'(<img[^>]*\ssrc=")([^"]+)(")',
            _rewrite_img_src,
            cleaned,
            flags=re.IGNORECASE,
        )

        if not plain_text:
            return cleaned
        # Avoid duplicating text when ``cleaned`` already renders the choice body
        # (e.g. plain text or ``<code>``). Only prepend ``plain_text`` when the
        # HTML is purely an ``<img>`` whose alt/caption differs from ``plain_text``.
        cleaned_text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cleaned))).strip()
        if cleaned_text == re.sub(r"\s+", " ", plain_text).strip():
            return cleaned
        if "<img" in cleaned.lower() and not cleaned_text:
            return f"{html.escape(plain_text)}<br>{cleaned}"
        return cleaned

    if plain_text:
        return clean_html(plain_text).replace("\n", "<br>")

    return '<span class="choice-blank">_(image choice)_</span>'


def exhibit_rel_path(local_path: str) -> str:
    """Convert an exhibit path (relative or absolute) into the path used in
    HTML files, which live in ``guides/``.

    The exhibit manifest stores paths like ``assets/exhibits/dp-600/911291_0.png``
    (relative to the repo root) or absolute paths that contain the same tail.
    Since the generated HTML sits one directory below the repo root (in
    ``guides/``), we prefix the relative form with ``../`` so the browser can
    resolve it from ``guides/``.

    Raises ``ValueError`` if the path doesn't look like an exhibit path —
    callers should treat that as a data error rather than silently guessing.
    """
    if not local_path:
        return ""
    p = local_path.replace("\\", "/")
    # Strip any absolute prefix (e.g. /Users/.../azure/) — we just need the
    # path relative to the repo root.
    marker = "assets/exhibits/"
    idx = p.find(marker)
    if idx < 0:
        raise ValueError(
            f"exhibit_rel_path: expected path containing {marker!r}, got {local_path!r}"
        )
    p = p[idx:]
    # Normalize URL escaping for spaces etc.
    safe = urllib.parse.quote(p, safe="/-_.")
    return f"../{safe}"


def render_exhibit(exhibit: dict, idx: int, q_label: str) -> str:
    """Render a single exhibit (image/table/code) for HTML embedding."""
    kind = (exhibit.get("kind") or "").strip().lower()
    alt = html.escape(exhibit.get("alt") or "")
    original = html.escape(exhibit.get("original_url") or "#")
    caption_label = f"Exhibit {idx + 1}"
    alt_text = f" — {alt}" if alt else ""

    if kind == "image":
        local = exhibit.get("local_path") or exhibit.get("src") or ""
        rel = exhibit_rel_path(local) if local else ""
        if not rel:
            src_fallback = exhibit.get("src") or ""
            if src_fallback and not src_fallback.startswith("http"):
                rel = f"../{src_fallback.lstrip('/')}"
        if local and _exhibit_exists(local) and rel:
            rel_esc = html.escape(rel, quote=True)
            zoom_cap = html.escape(f"{q_label} · {caption_label}{alt_text}", quote=True)
            return (
                f'<figure class="exhibit exhibit-image">'
                f'<button type="button" class="exhibit-zoom-btn" data-zoom-src="{rel_esc}" '
                f'data-zoom-caption="{zoom_cap}" aria-label="Zoom {html.escape(caption_label)}">'
                f'<img src="{rel_esc}" alt="{alt}" loading="lazy">'
                f'</button>'
                f'<figcaption class="exhibit-caption">{caption_label}{alt_text} · <span>Click image to zoom</span></figcaption>'
                f'</figure>'
            )
        return (
            f'<div class="exhibit exhibit-missing">'
            f'<div class="exhibit-missing-title">Exhibit image not available offline</div>'
            f'<a href="{original}" target="_blank" rel="noopener">View original on ExamTopics</a>'
            f'</div>'
        )

    if kind == "table":
        raw = exhibit.get("html") or exhibit.get("raw_html") or ""
        if SANITIZER_AVAILABLE and sanitize_exhibit_html is not None:
            cleaned = sanitize_exhibit_html(raw)
        else:
            cleaned = clean_html(raw)
        return (
            f'<figure class="exhibit exhibit-table">'
            f'{cleaned}'
            f'<figcaption class="exhibit-caption">{caption_label}</figcaption>'
            f'</figure>'
        )

    if kind == "code":
        code = _extract_code_text(exhibit)
        return (
            f'<figure class="exhibit exhibit-code">'
            f'<pre><code>{html.escape(code)}</code></pre>'
            f'<figcaption class="exhibit-caption">{caption_label}</figcaption>'
            f'</figure>'
        )

    # Unknown kind — render a graceful placeholder.
    return (
        f'<div class="exhibit exhibit-missing">'
        f'<div class="exhibit-missing-title">Exhibit unavailable ({html.escape(kind or "unknown")})</div>'
        f'<a href="{original}" target="_blank" rel="noopener">View original on ExamTopics</a>'
        f'</div>'
    )


def render_exhibits_block(question: dict, q_label: str) -> str:
    """Render the ``<div class="exhibits">`` block listing every exhibit for a
    question. Returns an empty string if the question has no exhibits.
    """
    exhibits = question.get("exhibits") or []
    if not exhibits:
        return ""
    parts: list[str] = ['<div class="exhibits">']
    for idx, ex in enumerate(exhibits):
        parts.append(render_exhibit(ex, idx, q_label))
    parts.append("</div>")
    return "\n".join(parts)


def render_dragdrop_widget(question: dict, q_label: str) -> str:
    """Render the DRAG DROP practice widget.

    When ``drag_drop_items`` and ``drag_drop_targets`` are populated in the
    question data (the backfill extracted them from the live page), we render
    a functional two-column widget: a source pool of draggable chips and a
    column of drop targets. JS (see ``HTML_TAIL``) makes the chips draggable
    / click-to-place and persists placements in localStorage.

    When those fields are missing or empty, we fall back to a display-only
    note pointing the learner at the exhibit above.
    """
    items = question.get("drag_drop_items") or []
    targets = question.get("drag_drop_targets") or []
    error = question.get("drag_drop_error") or ""
    interactive = bool(items) and bool(targets)

    if not interactive:
        note = (
            "DRAG DROP — use the exhibit above to reason about the correct "
            "order/assignment. Interactive drag-and-drop grading is not "
            "available for this question."
        )
        if error:
            note += f" ({error})"
        return (
            '<div class="dragdrop-widget dragdrop-widget-display">'
            f'<p class="widget-note">{html.escape(note)}</p>'
            '<div class="answer-status" aria-live="polite"></div>'
            '</div>'
        )

    # Functional widget: sources on the left, targets on the right.
    source_chips: list[str] = []
    for idx, it in enumerate(items):
        # Accept either {"label": ..., "html": ...} or a plain string.
        if isinstance(it, dict):
            label = str(it.get("label") or it.get("text") or it.get("html") or "")
            label = label.strip()
            display = html.escape(label) if label else f"Item {idx + 1}"
        else:
            display = html.escape(str(it).strip())
        source_chips.append(
            f'<li class="dragdrop-chip" draggable="true" tabindex="0" '
            f'data-value="{html.escape(str(idx), quote=True)}" '
            f'data-label="{html.escape(display, quote=True)}">'
            f'<span class="dragdrop-chip-label">{display}</span></li>'
        )
    target_zones: list[str] = []
    for tidx, target in enumerate(targets):
        if isinstance(target, dict):
            placeholder = str(
                target.get("placeholder")
                or target.get("label")
                or target.get("text")
                or target.get("html")
                or f"Drop here {tidx + 1}"
            ).strip()
        else:
            placeholder = str(target).strip() or f"Drop here {tidx + 1}"
        target_zones.append(
            f'<li class="dragdrop-target" data-target="{tidx}" '
            f'data-placeholder="{html.escape(placeholder, quote=True)}">'
            f'<span class="dragdrop-target-label">{html.escape(placeholder)}</span>'
            f'<button type="button" class="dragdrop-clear" '
            f'data-target="{tidx}" aria-label="Clear drop {tidx + 1}">×</button>'
            f'</li>'
        )

    note = (
        "DRAG DROP — drag each item from the source pool onto a target slot, "
        "or click an item then click a target. ExamTopics does not publish the "
        "correct mapping, so this is practice-only and not graded."
    )
    return (
        '<div class="dragdrop-widget dragdrop-widget-interactive" '
        'data-dragdrop-interactive="true">'
        f'<p class="widget-note">{html.escape(note)}</p>'
        '<div class="dragdrop-board">'
        '<div class="dragdrop-column dragdrop-source">'
        '<h4 class="dragdrop-column-title">Source items</h4>'
        f'<ul class="dragdrop-chips" data-dragdrop-chips>{"".join(source_chips)}</ul>'
        '</div>'
        '<div class="dragdrop-column dragdrop-targets">'
        '<h4 class="dragdrop-column-title">Target slots</h4>'
        f'<ul class="dragdrop-targets" data-dragdrop-targets>{"".join(target_zones)}</ul>'
        '</div>'
        '</div>'
        '<div class="answer-status" aria-live="polite"></div>'
        '</div>'
    )


def render_other_widget(question: dict, q_label: str) -> str:
    """Fallback widget for questions whose type isn't interactive (no choices
    and no hotspot/drag-drop handler)."""
    qtype = question.get("question_type") or "unknown"
    note = (
        "This question type is not available as a multiple-choice exercise. "
        "Use the exhibit to reason about the answer."
    )
    return (
        '<div class="other-widget">'
        f'<p class="widget-note">{html.escape(note)} <span class="q-badge">{html.escape(str(qtype))}</span></p>'
        '<div class="answer-status" aria-live="polite"></div>'
        + '</div>'
    )


def slug_id(value: Any) -> str:
    """Create a URL-safe slug from a value."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value)).strip("-").lower()


CASE_STUDY_BOILERPLATE_RE = re.compile(
    r"^(?:"
    r"Case\s+Study(?:\s*-\s*)?$|"
    r"This\s+is\s+a\s+case\s+study\..*|"
    r"To\s+answer\s+(?:the\s+)?(?:case\s+study\s+questions|questions\s+included\s+in\s+a\s+case\s+study)\b.*|"
    r"(?:A\s+Review\s+Screen|At\s+the\s+end\s+of\s+this\s+case\s+study,\s+a\s+review\s+screen)\b.*|"
    r"To\s+start(?:\s+the\s+case\s+study)?(?:\s*-\s*)?$|"
    r"To\s+display\s+the\s+first\s+question\s+in\s+this\s+case\s+study\b.*"
    r")$",
    re.IGNORECASE,
)

CASE_STUDY_TOP_HEADING_RE = re.compile(
    r"^(?:"
    r"Overview(?:\.\s+[^:\n]{1,50})?|"
    r"Background|"
    r"Existing\s+Environment(?:\.\s+[^:\n]{1,50})?|"
    r"Current\s+Environment|"
    r"Available\s+Data|"
    r"Knowledge\s+Base|"
    r"Consultant\s+Proposal|"
    r"Problem\s+Statements?|"
    r"Issues\s+and\s+Constraints|"
    r"Planned\s+Changes|"
    r"Requirements(?:\.\s+[^:\n]{1,50})?|"
    r"(?:Technical|Security(?:\s+and\s+Compliance)?|Safety|Business|Performance|"
    r"Data\s+Analytics|Data\s+Preparation|Semantic\s+Model|Report|General)\s+Requirements?"
    r")(?:\s*-\s*)?$",
    re.IGNORECASE,
)

CASE_STUDY_SUBHEADING_RE = re.compile(
    r"^(?:"
    r"Company\s+Information|"
    r"(?:Identity|Generative|Data|Fabric|Foundry)\s+Environment|"
    r"Microsoft\s+Foundry|"
    r"Project[1-9]|"
    r"Claim\s+(?:Project|Approval)|"
    r"A\s+(?:custom|default)\s+semantic\s+model|"
    r"Interactive\s+reports"
    r")(?:\s*-\s*)?$",
    re.IGNORECASE,
)

COLON_LIST_INTRO_RE = re.compile(
    r"(?:\bfollowing\b[^:\n]{0,65}|\bconfigurations|\brequirements|\bissues|\bactions|\bchanges|\bcolumns|\bresources|\bsubscriptions|\bagents):\s*$",
    re.IGNORECASE,
)

TASK_CUE_RE = re.compile(
    r"^(?:Question\s*-\s*|You\s+need\s+to\b|For\s+each\s+of\s+the\s+following\b|"
    r"Which\b|What\b|How\b|Where\b|Why\b|Select\b|Use\s+the\s+drop-down\b|"
    r"Drag\b|In\s+which\b|To\s+answer\b|Does\s+this\s+meet\s+the\s+goal\b)",
    re.IGNORECASE,
)

INSTRUCTION_NOTE_RE = re.compile(
    r"^(?:To\s+answer,\s+|NOTE:\s*Each\s+correct\s+selection|"
    r"Each\s+(?:correct\s+selection|configuration|item|option|value)\s+(?:is\s+worth|may\s+be\s+used)|"
    r"You\s+may\s+need\s+to\s+drag\s+the\s+split\s+bar)",
    re.IGNORECASE,
)


def _plain_line(line: str) -> str:
    return re.sub(r"<[^>]+>", "", line).strip()


def strip_case_study_boilerplate(text: str) -> str:
    """Remove Pearson VUE case-study UI instructions while keeping scenario text."""
    if not text:
        return ""
    out: list[str] = []
    for raw_line in text.splitlines():
        plain = _plain_line(raw_line)
        if not plain or plain == "-":
            continue
        if CASE_STUDY_BOILERPLATE_RE.match(plain):
            continue
        out.append(raw_line.strip())
    return "\n".join(out)


def _format_inline_code_tokens(escaped_text: str) -> str:
    """Wrap SDK calls, key=value params, CLI flags, and snake_case IDs in <code>."""
    # Protect any existing tags or entities by splitting on HTML tags first.
    chunks = re.split(r"(<[^>]+>)", escaped_text)
    in_code = 0
    for idx, ch in enumerate(chunks):
        if ch.startswith("<"):
            low = ch.lower()
            if low.startswith("<code"):
                in_code += 1
            elif low.startswith("</code"):
                in_code = max(0, in_code - 1)
            continue
        if in_code > 0 or not ch:
            continue

        placeholders: list[str] = []

        def _stash(m: re.Match[str]) -> str:
            token = m.group(0)
            # Never wrap plural markers like agent(s), row(s), time(s)
            if re.fullmatch(r"[A-Za-z]+\([sS]\)", token):
                return token
            key = f"\x00CODE{len(placeholders)}\x00"
            placeholders.append(f"<code>{token}</code>")
            return key

        # Normalize common ExamTopics OCR spacing inside snake_case parameter names
        ch = re.sub(r"\b(tool|max|top|enable|api|model|project)\s+_([a-z][a-z0-9_]*)\b", r"\1_\2", ch)
        # 1. key=value assignments (including quoted/&quot; values or booleans/dicts)
        ch = re.sub(
            r"\b[A-Za-z_][\w.]*\s*=\s*(?:True|False|None|\d+(?:\.\d+)?|"
            r"&quot;[^&]*&quot;|&#x27;[^&]*&#x27;|“[^”]*”|"
            r"\[[^\]\n]{0,80}\]|\{[^{}\n]{0,80}\}|\.\.\.|[A-Za-z_][\w.-]*)",
            _stash,
            ch,
        )
        # 2. Method/function calls without space before '('
        ch = re.sub(r"\b[A-Za-z_][\w.]*\([^()\n]{0,90}\)", _stash, ch)
        # 3. snake_case identifiers & CLI flags & dotfile paths
        ch = re.sub(r"(?:~\/\.[\w./-]+|--[a-z0-9][a-z0-9-]*|\b[A-Za-z]+(?:_[A-Za-z0-9]+)+\b)", _stash, ch)

        for p_idx, replacement in enumerate(placeholders):
            ch = ch.replace(f"\x00CODE{p_idx}\x00", replacement)
        chunks[idx] = ch
    return "".join(chunks)


def _safe_line_html(line: str) -> str:
    """Sanitize or escape a single line and highlight inline code tokens."""
    stripped = line.strip()
    if "<" in stripped and ">" in stripped:
        cleaned = (
            sanitize_exhibit_html(stripped)
            if (SANITIZER_AVAILABLE and sanitize_exhibit_html is not None)
            else clean_html(stripped)
        )
        return _format_inline_code_tokens(cleaned)
    return _format_inline_code_tokens(html.escape(html.unescape(stripped)))


def format_stem_html(text: str, *, emphasize_question: bool = False) -> str:
    """Format question or section text into semantic paragraphs, <ul> lists,
    <code> pills, .proposed-solution callouts, and muted exam notes.
    """
    if not text:
        return ""
    raw_lines = [ln.strip() for ln in clean_html(text).splitlines() if ln.strip()]
    if not raw_lines:
        return ""

    blocks: list[str] = []
    list_items: list[str] = []
    in_colon_list = False

    def _flush_list() -> None:
        nonlocal list_items, in_colon_list
        if list_items:
            items_html = "".join(f"<li>{item}</li>" for item in list_items)
            blocks.append(f'<ul class="stem-list">{items_html}</ul>')
            list_items = []
        in_colon_list = False

    # Identify which trailing lines represent the core question when requested.
    question_start = len(raw_lines)
    if emphasize_question:
        for i in range(len(raw_lines) - 1, -1, -1):
            pl = _plain_line(raw_lines[i])
            if INSTRUCTION_NOTE_RE.match(pl):
                continue
            if pl.endswith("?") or TASK_CUE_RE.match(pl):
                question_start = i
            else:
                if question_start < len(raw_lines):
                    break

    for idx, line in enumerate(raw_lines):
        plain = _plain_line(line)
        if not plain or plain == "-":
            continue

        # Subheading inside a case-study section
        if CASE_STUDY_SUBHEADING_RE.match(plain):
            _flush_list()
            label = re.sub(r"\s*-\s*$", "", plain).strip()
            blocks.append(f'<div class="cs-subheading">{html.escape(label)}</div>')
            continue

        # Inline legacy hyphenated heading fallback
        m_legacy = re.match(
            r"^(Overview|Existing Environment|Planned Changes|Requirements|"
            r"Data Analytics Requirements|Data Preparation Requirements|"
            r"Semantic Model Requirements|Report Requirements|General Requirements)\s*-\s*(.+)$",
            plain,
            flags=re.IGNORECASE,
        )
        if m_legacy:
            _flush_list()
            blocks.append(f'<span class="section-title">{html.escape(m_legacy.group(1))}</span>')
            blocks.append(f"<p>{_safe_line_html(m_legacy.group(2))}</p>")
            continue

        # Proposed solution callout ("Does this meet the goal?" series)
        m_sol = re.match(r"^Solution:\s*(.+)$", plain, flags=re.IGNORECASE)
        if m_sol:
            _flush_list()
            blocks.append(
                '<div class="proposed-solution">'
                '<span class="solution-label">Proposed solution</span>'
                f"<p>{_safe_line_html(m_sol.group(1))}</p>"
                "</div>"
            )
            continue

        # Trailing Pearson VUE instructions ("To answer, ...", "NOTE: Each correct selection...")
        if INSTRUCTION_NOTE_RE.match(plain):
            _flush_list()
            blocks.append(f'<p class="exam-instruction-note">{_safe_line_html(line)}</p>')
            continue

        # Explicit bullet character
        m_bullet = re.match(r"^[•●▪]\s*(.+)$", line)
        if m_bullet:
            list_items.append(_safe_line_html(m_bullet.group(1)))
            continue

        # If currently collecting an unbulleted post-colon list, check whether this line continues it
        if in_colon_list:
            if (
                idx >= question_start
                or TASK_CUE_RE.match(plain)
                or CASE_STUDY_TOP_HEADING_RE.match(plain)
                or COLON_LIST_INTRO_RE.search(plain)
                or len(list_items) >= 8
            ):
                _flush_list()
            else:
                list_items.append(_safe_line_html(line))
                continue

        # Check if this line introduces a list on subsequent lines
        if COLON_LIST_INTRO_RE.search(plain) and idx + 1 < len(raw_lines):
            _flush_list()
            cls = ' class="prompt-lead"' if idx >= question_start else ""
            blocks.append(f"<p{cls}>{_safe_line_html(line)}</p>")
            in_colon_list = True
            continue

        # Split inline "...? To answer, select..." on a single line cleanly
        m_inline_instr = re.match(r"^(.+?\?)\s+(To\s+answer,\s+.+)$", plain, flags=re.IGNORECASE)
        if m_inline_instr:
            _flush_list()
            q_cls = ' class="prompt-lead"' if emphasize_question else ""
            blocks.append(f"<p{q_cls}>{_safe_line_html(m_inline_instr.group(1))}</p>")
            blocks.append(f'<p class="exam-instruction-note">{_safe_line_html(m_inline_instr.group(2))}</p>')
            continue

        _flush_list()
        if emphasize_question and idx >= question_start:
            blocks.append(f'<p class="prompt-lead">{_safe_line_html(line)}</p>')
        else:
            blocks.append(f"<p>{_safe_line_html(line)}</p>")

    _flush_list()
    return "\n".join(blocks)


def format_case_study_sections(text: str) -> str:
    """Backwards-compatible wrapper formatting rich stem & section HTML."""
    return format_stem_html(text)


def html_text(text: str) -> str:
    """Format question text for HTML with semantic paragraphs, lists, and code pills."""
    return format_stem_html(text)


def _is_case_study(cleaned: str, lines: list[str], labels: list[str]) -> bool:
    if "Case study" in labels:
        return True
    if "this is a case study" in cleaned.lower():
        return True
    if len(cleaned) >= 1800:
        return True
    heading_hits = sum(1 for ln in lines if CASE_STUDY_TOP_HEADING_RE.match(_plain_line(ln)))
    return heading_hits >= 2


def split_question_text(text: str) -> tuple[list[str], str, str]:
    """Separate genuine multi-section case studies from the exam task while
    keeping regular non-case-study stems unified.
    """
    cleaned = clean_html(text).strip()
    if not cleaned:
        return [], "", ""

    lines = [line.strip() for line in re.split(r"\n+", cleaned) if line.strip()]
    labels: list[str] = []
    lead_label_map = {
        "HOTSPOT": "Hotspot",
        "DRAG DROP": "Drag drop",
        "ORDERLIST": "Order list",
        "CASE STUDY": "Case study",
        "SIMULATION": "Simulation",
    }
    while lines:
        lead_raw = _plain_line(lines[0])
        if lead_raw == "-":
            lines.pop(0)
            continue
        lead = re.sub(r"\s*-\s*$", "", lead_raw).strip().upper()
        if lead in lead_label_map:
            if lead_label_map[lead] not in labels:
                labels.append(lead_label_map[lead])
            lines.pop(0)
        else:
            break

    if not lines:
        return labels, "", ""

    if not _is_case_study(cleaned, lines, labels):
        return labels, "", "\n".join(lines).strip()

    if "Case study" not in labels:
        labels.append("Case study")

    # Strip Pearson VUE case-study UI boilerplate before segmenting
    filtered_lines = [
        ln for ln in lines
        if _plain_line(ln) and _plain_line(ln) != "-" and not CASE_STUDY_BOILERPLATE_RE.match(_plain_line(ln))
    ]
    if not filtered_lines:
        return labels, "", ""

    # Locate the last case-study top heading so mid-scenario sentences (e.g.
    # "When testing Claim Approval...") never get mistaken for the exam task.
    last_heading_idx = -1
    for i, ln in enumerate(filtered_lines):
        if CASE_STUDY_TOP_HEADING_RE.match(_plain_line(ln)):
            last_heading_idx = i

    search_floor = max(last_heading_idx + 1, len(filtered_lines) - 8)

    # Check explicit "Question -" marker first (used in several DP-600 case studies)
    q_marker_idx = next(
        (
            i for i in range(max(0, last_heading_idx), len(filtered_lines))
            if re.match(r"^Question\s*-\s*$", _plain_line(filtered_lines[i]), flags=re.IGNORECASE)
        ),
        None,
    )
    if q_marker_idx is not None and q_marker_idx + 1 < len(filtered_lines):
        preamble = "\n".join(filtered_lines[:q_marker_idx]).strip()
        prompt = "\n".join(filtered_lines[q_marker_idx + 1:]).strip()
        return labels, preamble, prompt

    cue_indices = [
        i
        for i in range(search_floor, len(filtered_lines))
        if TASK_CUE_RE.match(_plain_line(filtered_lines[i]))
        and not INSTRUCTION_NOTE_RE.match(_plain_line(filtered_lines[i]))
    ]
    start = cue_indices[0] if cue_indices else max(last_heading_idx + 1, len(filtered_lines) - 2)

    preamble = "\n".join(filtered_lines[:start]).strip()
    prompt = "\n".join(filtered_lines[start:]).strip()
    if not prompt:
        prompt = preamble
        preamble = ""
    return labels, preamble, prompt


def parse_case_study_sections(preamble: str, prompt: str = "") -> list[dict[str, Any]]:
    """Parse a case-study preamble into structured sections and flag sections
    referenced by ``prompt`` as ``relevant=True``.
    """
    stripped = strip_case_study_boilerplate(preamble)
    if not stripped.strip():
        return []

    raw_sections: list[dict[str, Any]] = []
    current_title = "Overview"
    current_lines: list[str] = []

    for line in stripped.splitlines():
        plain = _plain_line(line)
        if not plain or plain == "-":
            continue
        if CASE_STUDY_TOP_HEADING_RE.match(plain):
            title_clean = re.sub(r"\s*-\s*$", "", plain).strip()
            if current_lines:
                raw_sections.append({"title": current_title, "lines": current_lines})
            current_title = title_clean
            current_lines = []
        else:
            current_lines.append(line.strip())

    if current_lines:
        raw_sections.append({"title": current_title, "lines": current_lines})

    if not raw_sections:
        return []

    prompt_low = (prompt or "").lower()
    stop_words = {
        "overview", "background", "existing", "current", "environment", "requirements",
        "requirement", "general", "company", "information", "the", "and", "for", "data",
    }
    sections: list[dict[str, Any]] = []
    for sec in raw_sections:
        title = sec["title"]
        body_text = "\n".join(sec["lines"])
        title_low = title.lower()
        relevant = False
        # 1. Direct phrase match (e.g. "security and compliance requirements", "technical requirements")
        norm_phrase = re.sub(r"s$", "", title_low)
        if len(norm_phrase) >= 6 and norm_phrase in prompt_low:
            relevant = True
        # 2. Specific domain modifier match
        if not relevant:
            tokens = [t for t in re.findall(r"[a-z0-9]+", title_low) if len(t) >= 4 and t not in stop_words]
            if tokens and any(re.search(rf"\b{re.escape(tok)}", prompt_low) for tok in tokens):
                relevant = True
        # 3. Named entity / subheading inside section referenced by prompt (e.g. Project2, Claim Approval)
        if not relevant:
            for ln in sec["lines"]:
                pl = _plain_line(ln)
                if CASE_STUDY_SUBHEADING_RE.match(pl) and pl.lower() in prompt_low:
                    relevant = True
                    break

        sections.append(
            {
                "title": title,
                "text": body_text,
                "html": format_stem_html(body_text),
                "relevant": relevant,
            }
        )

    return sections


def _question_anchor(q: dict[str, Any]) -> str:
    exam = html.escape(str(q.get("exam", "")).lower())
    topic = q.get("topic", 0)
    num = q.get("question_number", 0)
    qid = q.get("question_id", "")
    return f"q-{exam}-t{topic}-n{num}-{slug_id(qid)}"


def _infer_case_study_meta(q: dict[str, Any], preamble: str) -> tuple[str | None, str | None]:
    if not preamble:
        return None, None
    cs_id = q.get("case_study_id")
    cs_title = q.get("case_study_title")
    if cs_id and cs_title:
        return str(cs_id), str(cs_title)
    exam = (q.get("exam") or "exam").lower()
    m = re.search(
        r"\b(Contoso,\s*Ltd\.?|Fabrikam\s+Inc\.?|Litware,\s*Inc\.?|Tailspin\s+Toys|Northwind\s+Traders|Wide\s+World\s+Importers|Adatum\s+Corporation|Relecloud)\b",
        preamble,
    )
    if m:
        raw_company = m.group(1).rstrip(".")
        if "Contoso" in raw_company and "health provider" in preamble.lower():
            return f"{exam}-contoso-health", "Contoso Health"
        slug = re.sub(r"[^a-z0-9]+", "-", raw_company.lower()).strip("-")
        return f"{exam}-{slug}", raw_company
    return f"{exam}-cs-{q.get('topic', 1)}", "Case Study"


def _compute_vote_summary(q: dict[str, Any]) -> tuple[bool, str]:
    tally = q.get("voted_answers_tally") or []
    rows = [
        (str(t.get("voted_answers") or "").strip(), int(t.get("vote_count") or 0))
        for t in tally
        if str(t.get("voted_answers") or "").strip() and int(t.get("vote_count") or 0) > 0
    ]
    if not rows:
        return False, ""
    rows.sort(key=lambda r: -r[1])
    total = sum(v for _, v in rows) or 1
    is_contested = len(rows) >= 2 and rows[1][1] >= 2 and (rows[1][1] / total) >= 0.30
    parts = ['<div class="vote-bars">']
    status_note = "Contested community split" if is_contested else "Community vote distribution"
    parts.append(f'<div class="vote-bars-title"><span>{status_note}</span><span>{total} vote{"s" if total != 1 else ""}</span></div>')
    for ans, cnt in rows[:4]:
        pct = round((cnt / total) * 100)
        parts.append(
            f'<div class="vote-bar-row">'
            f'<strong>{html.escape(ans)}</strong>'
            f'<div class="vote-bar-track"><div class="vote-bar-fill" style="inline-size:{pct}%"></div></div>'
            f'<span>{pct}% ({cnt})</span>'
            f'</div>'
        )
    parts.append("</div>")
    return is_contested, "\n".join(parts)


def _render_comment_item(c: dict[str, Any]) -> str:
    author = html.escape(str(c.get("author") or "Anonymous"))
    up = int(c.get("upvotes") or 0)
    badges = " ".join(f'<span class="badge">{html.escape(str(b))}</span>' for b in (c.get("badges") or []))
    ctext = format_stem_html(html.unescape(str(c.get("text") or "")))
    return (
        '<div class="comment">'
        f'<div class="comment-meta"><strong>{author}</strong> · {up} upvote{"s" if up != 1 else ""} {badges}</div>'
        f'<div class="comment-body">{ctext}</div>'
        "</div>"
    )


def _format_most_voted_html(raw_mv: str) -> str:
    unescaped = html.unescape(raw_mv).strip()
    if not unescaped:
        return "<strong>Not provided</strong>"
    segments = [seg.strip() for seg in unescaped.split("|") if seg.strip()]
    if len(segments) <= 1 and len(unescaped) <= 40:
        return f"<strong>{html.escape(unescaped)}</strong>"
    items = "".join(f"<div>{_format_inline_code_tokens(html.escape(seg))}</div>" for seg in segments)
    return f'<div class="mv-lines">{items}</div>'


def render_question_html(
    q: dict[str, Any],
    is_active: bool = False,
    case_siblings: list[dict[str, Any]] | None = None,
) -> str:
    parts: list[str] = []
    q_id_raw = q.get("question_id", "")
    q_id = html.escape(str(q_id_raw))
    exam_code = (q.get("exam") or "").strip()
    topic = q.get("topic", 0)
    num = q.get("question_number", 0)
    q_type = (q.get("question_type") or "").strip().lower()
    anchor = _question_anchor(q)

    labels, preamble, prompt = split_question_text(q.get("question_text", ""))
    label_text = f"Q{topic}.{num}"
    is_cs = bool(preamble)
    is_contested, vote_bars_html = _compute_vote_summary(q)

    raw_mv = html.unescape(str(q.get("most_voted_answer") or "")).strip()
    most_voted_attr = html.escape(raw_mv, quote=True)

    # Compact search haystack (label, ID, skill area, prompt, choices)
    skill_label = str(q.get("skill_area_label") or SKILL_AREA_LABELS.get(exam_code.lower(), {}).get(int(q.get("skill_area") or topic), ""))
    choices_search = " ".join((c.get("text") or "") for c in (q.get("choices") or []))
    search_blob = re.sub(r"\s+", " ", f"{label_text} {q_id_raw} {skill_label} {prompt} {choices_search}").strip()[:900]

    cls_list = ["question"]
    if is_active:
        cls_list.append("active")
    if is_cs:
        cls_list.append("is-case-study")

    parts.append(
        f'<article class="{" ".join(cls_list)}" id="{anchor}" '
        f'data-topic="{topic}" data-num="{num}" data-label="{label_text}" '
        f'data-qtype="{html.escape(q_type)}" data-contested="{str(is_contested).lower()}" '
        f'data-most-voted="{most_voted_attr}" data-search="{html.escape(search_blob, quote=True)}">'
    )

    parts.append('<div class="q-header">')
    parts.append('<div class="q-title">')
    parts.append(f'<span class="q-num">{label_text}</span>')
    parts.append(f'<span class="q-id">ID {q_id}</span>')
    badge_labels: list[str] = []
    for lb in labels:
        if lb not in badge_labels:
            badge_labels.append(lb)
    if q_type and q_type not in {"single", "multiple"}:
        pretty_t = q_type.replace("_", " ").title()
        if pretty_t.lower() not in {b.lower() for b in badge_labels}:
            badge_labels.append(pretty_t)
    for label in badge_labels:
        parts.append(f'<span class="q-badge">{html.escape(label)}</span>')
    if skill_label:
        parts.append(f'<span class="q-badge skill-badge">{html.escape(skill_label)}</span>')
    if is_contested:
        parts.append('<span class="q-badge contested-badge">⚠️ Contested vote</span>')
    parts.append("</div>")
    parts.append('<div class="q-actions">')
    parts.append(f'<button class="secondary btn-bookmark" type="button" aria-label="Bookmark {label_text}" aria-pressed="false">☆ Save</button>')
    parts.append(f'<button class="secondary btn-review" type="button" aria-label="Mark {label_text} as reviewed">Mark reviewed</button>')
    parts.append("</div></div>")

    # Case study sibling jumper bar
    if is_cs and case_siblings and len(case_siblings) > 1:
        _, cs_title = _infer_case_study_meta(q, preamble)
        pos = next((idx + 1 for idx, s in enumerate(case_siblings) if _question_anchor(s) == anchor), 1)
        parts.append('<div class="cs-jumper" role="navigation" aria-label="Case study questions">')
        parts.append(f'<span class="cs-jumper-title">Case Study: {html.escape(cs_title or "Scenario")} ({pos} of {len(case_siblings)})</span>')
        parts.append('<div class="cs-jumper-links">')
        for sib in case_siblings:
            s_anc = _question_anchor(sib)
            s_lbl = f"Q{sib.get('topic', 0)}.{sib.get('question_number', 0)}"
            cur_attr = ' aria-current="true"' if s_anc == anchor else ""
            parts.append(f'<a href="#{s_anc}"{cur_attr}>{html.escape(s_lbl)}</a>')
        parts.append("</div></div>")

    if is_cs:
        parts.append('<div class="q-case-grid">')
        parts.append('<div class="q-primary-col">')

    # Primary column (DOM 1st: Prompt -> Exhibits -> Choices/Widget -> Answer Shell)
    parts.append('<section class="prompt-card" aria-label="Question prompt">')
    parts.append('<div class="prompt-label">Exam task</div>')
    parts.append(f'<div class="q-prompt">{format_stem_html(prompt, emphasize_question=True)}</div>')
    parts.append("</section>")

    exhibits_html = render_exhibits_block(q, label_text)
    if exhibits_html:
        parts.append(exhibits_html)

    choices = q.get("choices", [])
    correct = set(q.get("correct_answers", []))
    has_correct_answer = len(correct) > 0

    if choices:
        is_multiple = (
            len(correct) > 1
            or q_type == "multiple"
            or (
                not has_correct_answer
                and bool(MULTI_SELECT_PROMPT_RE.search(q.get("question_text", "") or ""))
            )
        )
        input_type = "checkbox" if is_multiple else "radio"
        input_name = f"choice-{anchor}"
        parts.append(f'<ol class="choices" type="A" data-multiple="{str(is_multiple).lower()}">')
        for ch in choices:
            letter = html.escape(ch.get("letter", ""))
            body = render_choice_content(ch)
            cls = "correct" if letter in correct else ""
            input_id = f"{input_name}-{letter}"
            parts.append(f'<li class="{cls}" data-letter="{letter}">')
            parts.append(f'<input type="{input_type}" name="{input_name}" value="{letter}" id="{input_id}">')
            parts.append(f'<label for="{input_id}"><span class="letter">{letter}</span><span>{body}</span></label>')
            parts.append("</li>")
        parts.append("</ol>")
        parts.append('<div class="answer-status" aria-live="polite"></div>')
    else:
        if q_type == "drag_drop":
            parts.append(render_dragdrop_widget(q, label_text))
        elif q_type == "hotspot":
            parts.append('<div class="answer-status answer-status-hotspot" aria-live="polite"></div>')
        else:
            parts.append(render_other_widget(q, label_text))

    # Answer shell
    if has_correct_answer:
        correct_str = ", ".join(sorted(correct))
        correct_missing_cls = ""
    elif not choices and raw_mv:
        correct_str = "See community answer →"
        correct_missing_cls = ""
    else:
        correct_str = "Not provided"
        correct_missing_cls = " answer-missing"

    mv_missing_cls = "" if raw_mv else " answer-missing"
    backfill_meta = q.get("_backfill_source") or {}
    is_community_note = backfill_meta.get("confidence") == "community_note"
    note_badge = '<span class="confidence-badge" title="Extracted from low-upvote discussion comment">Community note</span>' if is_community_note else ""

    parts.append('<div class="answer-shell">')
    parts.append('<div class="answer-locked">')
    parts.append('<div><strong>Answer hidden</strong><br><span>Commit to your reasoning first, then reveal (or press <kbd>A</kbd>).</span></div>')
    parts.append(f'<button class="btn-toggle-answer" type="button" aria-label="Reveal answer for {label_text}">Reveal answer</button>')
    parts.append("</div>")
    parts.append('<div class="answer-revealed">')
    parts.append('<div class="answer-grid">')
    parts.append(
        f'<div class="answer-card{correct_missing_cls}">'
        '<div class="label-row"><span class="label">Official / Consensus key</span></div>'
        f"<strong>{html.escape(correct_str)}</strong></div>"
    )
    parts.append(
        f'<div class="answer-card{mv_missing_cls}">'
        f'<div class="label-row"><span class="label">Most voted / Community</span>{note_badge}</div>'
        f"{_format_most_voted_html(raw_mv)}</div>"
    )
    parts.append("</div>")

    if vote_bars_html:
        parts.append(vote_bars_html)

    if not choices:
        parts.append(
            '<div class="self-grade-controls" role="group" aria-label="Self-grade your answer">'
            '<span class="self-grade-prompt">Self-check your answer:</span>'
            '<button type="button" class="secondary btn-self-grade" data-self-grade="correct" aria-pressed="false">Got it right ✓</button>'
            '<button type="button" class="secondary btn-self-grade" data-self-grade="incorrect" aria-pressed="false">Needs work ✕</button>'
            "</div>"
        )

    raw_comments = q.get("comments", []) or []
    if raw_comments:
        sorted_comments = sorted(
            enumerate(raw_comments),
            key=lambda pair: (-int(pair[1].get("upvotes") or 0), pair[0]),
        )
        ordered = [c for _, c in sorted_comments]
        top_slice = ordered[:3]
        rest_slice = ordered[3:]
        parts.append('<details class="comments" open>')
        parts.append(f'<summary>Top explanations from discussion ({len(ordered)})</summary>')
        for c in top_slice:
            parts.append(_render_comment_item(c))
        if rest_slice:
            parts.append('<details class="comments-more">')
            parts.append(f'<summary>Show {len(rest_slice)} more comment{"s" if len(rest_slice) != 1 else ""}</summary>')
            for c in rest_slice:
                parts.append(_render_comment_item(c))
            parts.append("</details>")
        parts.append("</details>")

    q_url = str(q.get("url") or "").strip()
    thread_anchor = (
        f'<a class="thread-link" href="{html.escape(q_url, quote=True)}" target="_blank" rel="noopener">Original ExamTopics discussion ↗</a>'
        if q_url
        else '<span></span>'
    )
    parts.append(f'<div class="answer-tools">{thread_anchor}<button class="secondary btn-toggle-answer" type="button">Hide answer</button></div>')
    parts.append("</div></div>")

    if is_cs:
        parts.append("</div>")  # close .q-primary-col
        cs_sections = parse_case_study_sections(preamble, prompt=prompt)
        any_relevant = any(sec.get("relevant") for sec in cs_sections)
        _, cs_title = _infer_case_study_meta(q, preamble)
        all_open = len(cs_sections) > 0 and all(
            (sec.get("relevant") if any_relevant else idx == 0)
            for idx, sec in enumerate(cs_sections)
        )
        parts.append('<section class="case-study-panel" aria-label="Case study reference">')
        parts.append('<div class="cs-toolbar">')
        parts.append(f'<span class="cs-panel-label">Case Study · {html.escape(cs_title or "Scenario")}</span>')
        parts.append(
            f'<button type="button" class="secondary cs-toggle-all" aria-expanded="{str(all_open).lower()}">'
            f'{"Collapse all" if all_open else "Expand all"}</button>'
        )
        parts.append("</div>")
        for idx, sec in enumerate(cs_sections):
            is_rel = bool(sec.get("relevant"))
            should_open = is_rel if any_relevant else (idx == 0)
            rel_cls = " relevant" if is_rel else ""
            open_attr = " open" if should_open else ""
            rel_pill = '<span class="cs-relevant-pill">★ Relevant</span>' if is_rel else ""
            parts.append(f'<details class="cs-section{rel_cls}"{open_attr}>')
            parts.append(f'<summary><span>{html.escape(sec["title"])}</span>{rel_pill}</summary>')
            parts.append(f'<div class="cs-section-body">{sec["html"]}</div>')
            parts.append("</details>")
        parts.append("</section>")
        parts.append("</div>")  # close .q-case-grid

    parts.append("</article>")
    return "\n".join(parts)


def _render_exam_switcher_popover(current_exam: str) -> str:
    links = ['<nav id="exam-switcher-menu" popover aria-label="Switch certification study guide">']
    links.append('<a href="index.html"><strong>All Exams Hub</strong><span>Overview</span></a>')
    for slug, exam_title in EXAM_TITLES.items():
        cur = ' aria-current="page"' if slug == current_exam.lower() else ""
        links.append(
            f'<a href="{slug}-examtopics-study-guide.html"{cur}>'
            f'<strong>{html.escape(slug.upper())}</strong>'
            f'<span>{html.escape(exam_title)}</span></a>'
        )
    links.append("</nav>")
    return "\n".join(links)


def _render_toc_chunks(group_list: list[dict[str, Any]], chunk_size: int = 25) -> list[str]:
    out: list[str] = []
    if len(group_list) <= chunk_size:
        out.append('<ul class="toc-links">')
        for q in group_list:
            t = q.get("topic", 0)
            n = q.get("question_number", 0)
            out.append(f'<li><a href="#{_question_anchor(q)}">Q{t}.{n}</a></li>')
        out.append("</ul>")
        return out
    for i in range(0, len(group_list), chunk_size):
        chunk = group_list[i : i + chunk_size]
        f_lbl = f"Q{chunk[0].get('topic', 0)}.{chunk[0].get('question_number', 0)}"
        l_lbl = f"Q{chunk[-1].get('topic', 0)}.{chunk[-1].get('question_number', 0)}"
        out.append(f'<details class="toc-chunk" {"open" if i == 0 else ""}>')
        out.append(f"<summary>{f_lbl}–{l_lbl}</summary>")
        out.append('<ul class="toc-links">')
        for q in chunk:
            t = q.get("topic", 0)
            n = q.get("question_number", 0)
            out.append(f'<li><a href="#{_question_anchor(q)}">Q{t}.{n}</a></li>')
        out.append("</ul></details>")
    return out


def build_html(exam: str, questions: list[dict[str, Any]]) -> str:
    from collections import defaultdict
    from itertools import groupby

    exam_slug = exam.strip().lower()
    questions = sorted(questions, key=lambda q: (q.get("topic", 0), q.get("question_number", 0)))
    title = format_study_guide_title(exam_slug)

    # Precompute case-study sibling groups across the whole exam
    cs_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    q_to_cs_id: dict[str, str] = {}
    for q in questions:
        _, pre, _ = split_question_text(q.get("question_text", ""))
        cs_id, _ = _infer_case_study_meta(q, pre)
        if cs_id:
            cs_groups[cs_id].append(q)
            q_to_cs_id[_question_anchor(q)] = cs_id

    skill_labels = SKILL_AREA_LABELS.get(exam_slug, TOPIC_LABELS.get(exam_slug, {}))
    topic_labels = TOPIC_LABELS.get(exam_slug, {})
    has_distinct_skill_map = any(
        q.get("skill_area") is not None and int(q.get("skill_area") or 0) != int(q.get("topic") or 0)
        for q in questions
    )
    domain_count = (
        len({int(q.get("skill_area") or q.get("topic") or 0) for q in questions})
        if questions
        else 0
    )
    stats = f"{len(questions)} questions · {domain_count} skill areas"

    head = (
        HTML_HEAD.replace("$title", html.escape(title))
        .replace("$stats", html.escape(stats))
        .replace("$exam_switcher", _render_exam_switcher_popover(exam_slug))
        .replace("$exam", html.escape(exam_slug))
    )
    lines = [head]

    # Compact, non-blocking collapsible overview strip
    lines.append('<details class="overview-banner">')
    lines.append("<summary>")
    lines.append('<span class="overview-summary-left">')
    lines.append(f'<strong>Study Progress &amp; Shortcuts</strong>')
    lines.append(f'<span class="overview-pill"><span id="hero-pct">0%</span> reviewed</span>')
    lines.append("</span>")
    lines.append(f'<span>{len(questions)} questions · {len(cs_groups)} case stud{"y" if len(cs_groups) == 1 else "ies"}</span>')
    lines.append("</summary>")
    lines.append('<div class="overview-metrics">')
    lines.append(f'<div class="metric"><strong>{len(questions)}</strong><span>Total</span></div>')
    lines.append(f'<div class="metric"><strong>{domain_count}</strong><span>Skill areas</span></div>')
    lines.append('<div class="metric"><strong id="hero-attempted">0</strong><span>Attempted</span></div>')
    lines.append('<div class="metric"><strong id="hero-correct">0</strong><span>Correct</span></div>')
    lines.append('<div class="metric"><strong id="hero-reviewed">0</strong><span>Reviewed</span></div>')
    lines.append('<div class="metric"><strong id="hero-remaining">0</strong><span>Remaining</span></div>')
    lines.append("</div>")
    lines.append(
        '<div class="kbd-bar">'
        '<span><kbd>←</kbd> <kbd>→</kbd> Navigate</span>'
        '<span><kbd>1</kbd>–<kbd>9</kbd> Pick choice</span>'
        '<span><kbd>A</kbd> Reveal / hide answer</span>'
        '<span><kbd>R</kbd> Mark reviewed</span>'
        '<span><kbd>B</kbd> Save bookmark</span>'
        '<span><kbd>/</kbd> Search</span>'
        "</div>"
    )
    lines.append("</details>")

    # Search & Filter Toolbar
    lines.append('<section class="study-toolbar" aria-label="Search and filter questions">')
    lines.append('<div class="search-box">')
    lines.append('<input type="search" id="question-search" placeholder="Search questions, Azure services, IDs… (/)" aria-label="Search questions">')
    lines.append("</div>")
    lines.append('<div class="filter-chips" role="group" aria-label="Filter questions">')
    filter_defs = [
        ("all", "All", True),
        ("unreviewed", "Unreviewed", False),
        ("incorrect", "Needs work", False),
        ("bookmarked", "★ Saved", False),
        ("casestudy", "Case Studies", False),
        ("nonmcq", "Hotspot / Drag-Drop", False),
        ("contested", "⚠️ Contested", False),
    ]
    for f_key, f_lbl, pressed in filter_defs:
        lines.append(
            f'<button type="button" class="filter-chip" data-filter="{f_key}" '
            f'aria-pressed="{str(pressed).lower()}">{f_lbl}</button>'
        )
    lines.append("</div>")
    lines.append(f'<span id="filter-match-count" class="filter-count" aria-live="polite">{len(questions)} of {len(questions)} shown</span>')
    lines.append("</section>")

    lines.append('<div class="study-layout">')

    # Question Map Sidebar
    lines.append('<nav id="study-map" class="study-map" aria-label="Question map">')
    lines.append('<div class="nav-sidebar desktop-only" role="group" aria-label="Step controls">')
    lines.append('<button class="secondary nav-prev-btn" type="button" title="Previous question (←)" aria-label="Previous question">←</button>')
    lines.append('<div class="nav-status" aria-live="polite">Q 1</div>')
    lines.append('<button class="secondary nav-next-btn" type="button" title="Next question (→)" aria-label="Next question">→</button>')
    lines.append("</div>")

    if has_distinct_skill_map:
        lines.append('<div class="map-mode-switch" role="group" aria-label="Group question map by">')
        lines.append('<button type="button" class="map-mode-btn" data-map-mode="skill" aria-pressed="true">By Skill Area</button>')
        lines.append('<button type="button" class="map-mode-btn" data-map-mode="number" aria-pressed="false">By Question #</button>')
        lines.append("</div>")

    lines.append('<h2>Question map</h2><p class="map-note">Green = reviewed · Gold bar = saved.</p>')

    if cs_groups:
        lines.append('<details class="toc-topic">')
        total_cs = sum(len(v) for v in cs_groups.values())
        lines.append(f"<summary>Case Studies ({total_cs})</summary>")
        for cs_id, cs_list in cs_groups.items():
            _, cs_title = _infer_case_study_meta(cs_list[0], "case")
            lines.append('<details class="toc-chunk" open>')
            lines.append(f'<summary>{html.escape(cs_title or cs_id)} ({len(cs_list)})</summary>')
            lines.extend(_render_toc_chunks(cs_list, chunk_size=50))
            lines.append("</details>")
        lines.append("</details>")

    if has_distinct_skill_map:
        lines.append('<div id="toc-by-skill">')
        by_skill: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for q in questions:
            by_skill[int(q.get("skill_area") or 1)].append(q)
        for s_id in sorted(by_skill):
            g_list = by_skill[s_id]
            s_label = skill_labels.get(s_id, f"Skill Area {s_id}")
            lines.append('<details class="toc-topic" open>')
            lines.append(f"<summary>{html.escape(s_label)} ({len(g_list)})</summary>")
            lines.extend(_render_toc_chunks(g_list))
            lines.append("</details>")
        lines.append("</div>")

    num_hidden = " hidden" if has_distinct_skill_map else ""
    lines.append(f'<div id="toc-by-number"{num_hidden}>')
    for topic, group in groupby(questions, key=lambda q: q.get("topic", 0)):
        group_list = list(group)
        topic_label = topic_labels.get(topic, f"Topic {topic}")
        lines.append('<details class="toc-topic" open>')
        lines.append(f"<summary>{html.escape(topic_label)} ({len(group_list)})</summary>")
        lines.extend(_render_toc_chunks(group_list))
        lines.append("</details>")
    lines.append("</div>")
    lines.append("</nav>")

    lines.append('<div id="questions" class="question-stack">')
    lines.append(
        '<div id="filter-empty-state" class="filter-empty" hidden>'
        "<p><strong>No questions match the current search or filter.</strong></p>"
        '<button type="button" id="clear-filters-btn" class="secondary">Show all questions</button>'
        "</div>"
    )
    for i, q in enumerate(questions):
        anc = _question_anchor(q)
        cs_sibs = cs_groups.get(q_to_cs_id[anc]) if anc in q_to_cs_id else None
        lines.append(render_question_html(q, is_active=(i == 0), case_siblings=cs_sibs))
    lines.append("</div></div>")

    lines.append(HTML_TAIL.replace("$exam", html.escape(exam_slug)))
    return "\n".join(lines)


def build_index_html(exams_summary: list[dict[str, Any]]) -> str:
    """Build the standalone offline cross-exam study hub (``guides/index.html``)."""
    cards_html: list[str] = []
    for item in exams_summary:
        slug = str(item["exam"]).lower()
        code = slug.upper()
        exam_name = EXAM_TITLES.get(slug, f"{code} Certification")
        q_count = int(item.get("count", 0))
        t_count = int(item.get("topics", 0))
        badge = "2026 Azure AI" if slug.startswith("ai-") else "Microsoft Fabric"
        cards_html.append(
            f'<a class="hub-card" href="{html.escape(slug)}-examtopics-study-guide.html" '
            f'data-exam-card="{html.escape(slug)}" data-total="{q_count}">'
            f'<div class="hub-card-top"><span class="hub-badge">{badge}</span><span class="hub-code">{html.escape(code)}</span></div>'
            f'<h2>{html.escape(exam_name)}</h2>'
            f'<p class="hub-meta">{q_count} questions · {t_count} skill areas</p>'
            f'<div class="hub-bar"><div class="hub-bar-fill" data-fill></div></div>'
            f'<div class="hub-stats" data-stats>0 / {q_count} reviewed (0%)</div>'
            f'</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Azure AI &amp; Microsoft Fabric Certification Study Hub</title>
  <style>
    :root {{
      color-scheme: light;
      --font-display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --bg: #f4efe7;
      --surface: #fffdf8;
      --surface-2: #f8f1e5;
      --text: #211f1b;
      --text-secondary: #625a50;
      --accent: #175cd3;
      --accent-ink: #0f3f92;
      --accent-soft: #dbeafe;
      --success: #147a46;
      --border: #e0d4c3;
      --shadow: 0 16px 44px rgba(52, 38, 20, 0.1);
    }}
    :root[data-theme="dark"] {{
      color-scheme: dark;
      --bg: #10141f;
      --surface: #171d2b;
      --surface-2: #20283a;
      --text: #f5efe7;
      --text-secondary: #b7ad9d;
      --accent: #8ab4ff;
      --accent-ink: #d7e6ff;
      --accent-soft: #19345f;
      --success: #62d393;
      --border: #333b4d;
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.42);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-sans);
      font-size: 1.0625rem;
      line-height: 1.6;
      background: var(--bg);
      color: var(--text);
      padding: 2rem 1.25rem 4rem;
    }}
    .wrap {{ max-inline-size: 1080px; margin: 0 auto; }}
    .top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.75rem; }}
    h1 {{ margin: 0.35rem 0 0; font-family: var(--font-display); font-size: clamp(1.6rem, 1.2rem + 1.8vw, 2.5rem); line-height: 1.12; }}
    .sub {{ margin: 0.5rem 0 0; color: var(--text-secondary); max-inline-size: 64ch; }}
    .theme-btn {{
      min-block-size: 2.35rem;
      padding: 0.45rem 0.9rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      font-weight: 700;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 1rem; }}
    .hub-card {{
      display: flex;
      flex-direction: column;
      padding: 1.25rem;
      border-radius: 20px;
      border: 1px solid var(--border);
      background: var(--surface);
      box-shadow: var(--shadow);
      text-decoration: none;
      color: inherit;
      transition: transform 150ms ease, border-color 150ms ease;
    }}
    .hub-card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
    .hub-card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem; }}
    .hub-badge {{ padding: 0.16rem 0.55rem; border-radius: 999px; background: var(--accent-soft); color: var(--accent-ink); font-size: 0.74rem; font-weight: 800; }}
    .hub-code {{ font-weight: 900; font-size: 0.95rem; color: var(--accent-ink); }}
    .hub-card h2 {{ margin: 0 0 0.4rem; font-size: 1.15rem; line-height: 1.3; }}
    .hub-meta {{ margin: 0 0 1rem; color: var(--text-secondary); font-size: 0.88rem; }}
    .hub-bar {{ margin-top: auto; block-size: 0.5rem; border-radius: 999px; background: var(--surface-2); overflow: hidden; }}
    .hub-bar-fill {{ block-size: 100%; inline-size: 0%; background: linear-gradient(90deg, var(--accent), var(--success)); }}
    .hub-stats {{ margin-top: 0.45rem; font-size: 0.82rem; font-weight: 700; color: var(--text-secondary); }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="top">
      <div>
        <span class="hub-badge">Offline Study Workstation</span>
        <h1>Microsoft Azure AI &amp; Fabric Study Hub</h1>
        <p class="sub">Structured case studies, smart question typography, community vote splits, and persistent offline progress across all five certification guides.</p>
      </div>
      <button type="button" id="hub-theme" class="theme-btn" aria-label="Toggle dark mode">🌙</button>
    </header>
    <section class="grid" aria-label="Available certification study guides">
      {"".join(cards_html)}
    </section>
  </main>
  <script>
    const themeBtn = document.getElementById('hub-theme');
    const saved = localStorage.getItem('examguide-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', saved || (prefersDark ? 'dark' : 'light'));
    function syncTheme() {{
      const dark = document.documentElement.getAttribute('data-theme') === 'dark';
      themeBtn.textContent = dark ? '☀️' : '🌙';
    }}
    themeBtn.addEventListener('click', () => {{
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('examguide-theme', next);
      syncTheme();
    }});
    syncTheme();

    document.querySelectorAll('[data-exam-card]').forEach(card => {{
      const slug = card.dataset.examCard;
      const total = Number(card.dataset.total) || 1;
      let rev = [];
      let bm = [];
      try {{ rev = JSON.parse(localStorage.getItem(`examguide-v2-${{slug}}-reviewed`) || '[]'); }} catch (e) {{}}
      try {{ bm = JSON.parse(localStorage.getItem(`examguide-v2-${{slug}}-bookmarks`) || '[]'); }} catch (e) {{}}
      const pct = Math.min(100, Math.round((rev.length / total) * 100));
      const fill = card.querySelector('[data-fill]');
      const stats = card.querySelector('[data-stats]');
      if (fill) fill.style.inlineSize = `${{pct}}%`;
      if (stats) stats.textContent = `${{rev.length}} / ${{total}} reviewed (${{pct}}%)${{bm.length ? ' · ★ ' + bm.length : ''}}`;
    }});
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def md_escape(text: str) -> str:
    return text.replace("*", "\\*").replace("_", "\\_")


def html_to_md(text: str) -> str:
    """Very lightweight HTML -> Markdown for comments / question snippets."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>\s*<p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def _choice_to_md(choice: dict[str, Any]) -> str:
    """Render a single choice for the markdown guide.

    Falls back to ``choice.text_html`` when ``choice.text`` is empty so image-
    and code-based choices aren't rendered as blank ``A. `` / ``B. `` entries.
    """
    text = (choice.get("text") or "").strip()
    text_html = (choice.get("text_html") or "").strip()
    if text:
        return html_to_md(text)
    if not text_html:
        return ""
    # Quick heuristics: image choices emit a markdown image link; everything
    # else falls through to a placeholder so the row still appears.
    img_match = re.search(r"<img\b[^>]*\ssrc=\"([^\"]+)\"", text_html, flags=re.IGNORECASE)
    if img_match:
        rel_src = img_match.group(1)
        if rel_src and not rel_src.startswith(("http://", "https://", "//")):
            stripped = rel_src.lstrip("/")
            if not stripped.startswith("../") and not stripped.startswith("./"):
                stripped = f"../{stripped}"
            return f"![image choice]({stripped})"
        return f"![image choice]({rel_src})"
    if "<pre" in text_html.lower() or "<code" in text_html.lower():
        return "_(code choice)_"
    return "_(image choice)_"


def build_markdown(exam: str, questions: list[dict[str, Any]]) -> str:
    questions = sorted(questions, key=lambda q: (q.get("topic", 0), q.get("question_number", 0)))
    title = format_study_guide_title(exam)
    lines = [
        f"# {title}",
        "",
        f"_{len(questions)} questions generated from ExamTopics discussions._",
        "",
        "## Table of contents",
        "",
    ]
    for q in questions:
        topic = q.get("topic", 0)
        num = q.get("question_number", 0)
        lines.append(f"- [Q{topic}.{num}](#q{topic}-{num})")
    lines.append("")

    for q in questions:
        topic = q.get("topic", 0)
        num = q.get("question_number", 0)
        qid = q.get("question_id", "")
        q_type = (q.get("question_type") or "").strip().lower()
        lines.append(f'<a id="q{topic}-{num}"></a>')
        lines.append(f"## Q{topic}.{num} (ID {qid})")
        lines.append("")
        lines.append(html_to_md(strip_case_study_boilerplate(q.get("question_text", ""))))
        lines.append("")
        # Exhibits as a markdown section. Use ``../assets/...`` so the file
        # resolves correctly when the guide is consumed from ``guides/``.
        exhibits = q.get("exhibits") or []
        if exhibits:
            lines.append("**Exhibits**")
            for idx, ex in enumerate(exhibits):
                kind = (ex.get("kind") or "").lower()
                if kind == "image":
                    local = ex.get("local_path") or ex.get("src") or ""
                    rel = exhibit_rel_path(local)
                    if not rel and ex.get("src") and not ex["src"].startswith("http"):
                        rel = f"../{ex['src'].lstrip('/')}"
                    if rel and local and _exhibit_exists(local):
                        alt = ex.get("alt") or f"Exhibit {idx + 1}"
                        lines.append(f"- Exhibit {idx + 1}: ![{alt}]({rel})")
                    else:
                        orig = ex.get("original_url") or ""
                        if orig:
                            lines.append(f"- Exhibit {idx + 1}: [View original on ExamTopics]({orig})")
                        else:
                            lines.append(f"- Exhibit {idx + 1}: _(image not available offline)_")
                elif kind == "table":
                    raw = ex.get("html") or ex.get("raw_html") or ""
                    if SANITIZER_AVAILABLE and sanitize_exhibit_html is not None:
                        cleaned = sanitize_exhibit_html(raw)
                    else:
                        cleaned = clean_html(raw)
                    if cleaned:
                        lines.append(f"Exhibit {idx + 1}:")
                        # Force the table onto its own lines for readability.
                        lines.append("")
                        lines.append(cleaned)
                        lines.append("")
                elif kind == "code":
                    code = _extract_code_text(ex)
                    lines.append(f"- Exhibit {idx + 1} (code):")
                    lines.append("")
                    lines.append("```")
                    lines.append(code)
                    lines.append("```")
            lines.append("")
        for ch in q.get("choices", []):
            marker = "✅" if ch.get("correct") else "⭕"
            lines.append(f"{marker} **{ch.get('letter', '')}.** {_choice_to_md(ch)}")
        if not q.get("choices"):
            if q_type == "hotspot":
                lines.append("_HOTSPOT — the original ExamTopics question expects you to mark areas on the exhibit above; the correct hotspot coordinates are not published._")
            elif q_type == "drag_drop":
                lines.append("_DRAG DROP — the original ExamTopics question expects you to drag and drop items; the correct targets are not published._")
            else:
                lines.append("_This question type is not available as a multiple-choice exercise — use the exhibit to reason about the answer._")
        lines.append("")
        correct_answers = q.get("correct_answers", []) or []
        if correct_answers:
            correct = ", ".join(correct_answers)
        else:
            correct = "Not provided by ExamTopics"
        most_voted = html.unescape(str(q.get("most_voted_answer") or "")) or "Not provided"
        lines.append(f"**Correct answer:** {correct}")
        lines.append(f"**Most voted:** {most_voted}")
        lines.append("")
        comments = sorted(q.get("comments", []) or [], key=lambda c: -int(c.get("upvotes") or 0))
        if comments:
            lines.append("### Top explanations")
            for c in comments[:5]:
                badges = ", ".join(c.get("badges", []))
                badge_str = f" [{badges}]" if badges else ""
                lines.append(f"- **{c.get('author', 'Anonymous')}** ({c.get('upvotes', 0)} upvotes{badge_str}): {html_to_md(c.get('text', ''))}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build student-friendly study guides from crawled exam JSON.")
    parser.add_argument("json_files", nargs="+", help="One or more exam JSON files (e.g. dp-600.json).")
    parser.add_argument("--format", choices=["html", "markdown", "both"], default="both",
                        help="Output format (default: both).")

    parser.add_argument("--out-dir", type=Path, default=Path("."),
                        help="Directory for output files (default: current directory).")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    hub_entries: dict[str, dict[str, Any]] = {}

    for path_str in args.json_files:
        path = Path(path_str)
        exam = path.stem.lower()
        with path.open("r", encoding="utf-8") as f:
            questions = json.load(f)

        domains = len({int(q.get("skill_area") or q.get("topic") or 0) for q in questions}) if questions else 0
        hub_entries[exam] = {"exam": exam, "count": len(questions), "topics": domains}

        if args.format in ("html", "both"):
            html_out = args.out_dir / f"{exam}-examtopics-study-guide.html"
            html_out.write_text(build_html(exam, questions), encoding="utf-8")
            print(f"Wrote HTML: {html_out}")

        if args.format in ("markdown", "both"):
            md_out = args.out_dir / f"{exam}-examtopics-study-guide.md"
            md_out.write_text(build_markdown(exam, questions), encoding="utf-8")
            print(f"Wrote Markdown: {md_out}")

    if args.format in ("html", "both"):
        # Include any sibling data/*.json exams so index.html stays complete even on partial rebuilds
        data_dir = PROJECT_ROOT / "data"
        for slug in ("ai-103", "ai-300", "ai-500", "dp-600", "dp-700"):
            if slug not in hub_entries and (data_dir / f"{slug}.json").exists():
                qs = json.loads((data_dir / f"{slug}.json").read_text(encoding="utf-8"))
                domains = len({int(q.get("skill_area") or q.get("topic") or 0) for q in qs}) if qs else 0
                hub_entries[slug] = {"exam": slug, "count": len(qs), "topics": domains}
        ordered_order = ["ai-103", "ai-300", "ai-500", "dp-600", "dp-700"]
        ordered_hub = [hub_entries[s] for s in ordered_order if s in hub_entries] + [
            v for k, v in hub_entries.items() if k not in ordered_order
        ]
        index_out = args.out_dir / "index.html"
        index_out.write_text(build_index_html(ordered_hub), encoding="utf-8")
        print(f"Wrote Hub: {index_out}")


if __name__ == "__main__":
    main()
