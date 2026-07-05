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
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,750&family=Source+Sans+3:wght@400;500;600;700&display=swap');

    :root {
      color-scheme: light;
      --bg: #f4efe7;
      --bg-rgb: 244 239 231;
      --surface: #fffdf8;
      --surface-rgb: 255 253 248;
      --surface-2: #f8f1e5;
      --text: #211f1b;
      --text-secondary: #70685d;
      --muted: #9a9082;
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
      --shadow: 0 18px 55px rgba(52, 38, 20, 0.12), 0 2px 8px rgba(52, 38, 20, 0.06);
      --shadow-soft: 0 10px 30px rgba(52, 38, 20, 0.08);
      --radius: 22px;
      --radius-sm: 14px;
      --content-width: 980px;
      --rail-width: 280px;
      --header-height: 74px;
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
      --muted: #827a70;
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
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-height: 100vh;
      padding-bottom: calc(5.5rem + env(safe-area-inset-bottom));
      color: var(--text);
      font: 17px/1.68 "Source Sans 3", "Aptos", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgb(23 92 211 / 0.18), transparent 34rem),
        radial-gradient(circle at top right, rgb(180 83 9 / 0.12), transparent 32rem),
        linear-gradient(180deg, rgb(var(--bg-rgb)) 0%, var(--bg) 44%, color-mix(in srgb, var(--bg) 88%, #000 12%) 100%);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.35;
      background-image: radial-gradient(currentColor 0.7px, transparent 0.7px);
      background-size: 18px 18px;
      color: color-mix(in srgb, var(--text) 10%, transparent);
      mask-image: linear-gradient(to bottom, black, transparent 75%);
    }
    a { color: inherit; }
    img { max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--border); }
    pre { background: var(--surface-2); padding: 1rem; border-radius: 14px; overflow-x: auto; border: 1px solid var(--border); }
    code { font-family: "SFMono-Regular", Consolas, ui-monospace, monospace; font-size: 0.92em; }
    button, .btn {
      appearance: none;
      border: 1px solid transparent;
      border-radius: 999px;
      padding: 0.62rem 0.95rem;
      background: var(--accent);
      color: var(--accent-contrast);
      cursor: pointer;
      font: 700 0.88rem/1 "Source Sans 3", sans-serif;
      letter-spacing: 0.01em;
      transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    }
    button:hover, .btn:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgb(23 92 211 / 0.16); }
    button:active, .btn:active { transform: translateY(0); }
    button.secondary, .btn.secondary {
      background: rgb(var(--surface-rgb) / 0.7);
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
    button:focus-visible, a:focus-visible, summary:focus-visible {
      outline: 3px solid color-mix(in srgb, var(--accent) 70%, white 30%);
      outline-offset: 3px;
    }

    #progress-bar {
      position: fixed;
      inset: 0 auto auto 0;
      height: 4px;
      width: 0%;
      z-index: 200;
      background: linear-gradient(90deg, var(--accent), #22c55e);
      box-shadow: 0 0 24px color-mix(in srgb, var(--accent) 55%, transparent);
      transition: width 220ms ease;
    }
    .skip-link {
      position: fixed;
      left: 1rem;
      top: 1rem;
      z-index: 300;
      transform: translateY(-160%);
    }
    .skip-link:focus { transform: translateY(0); }

    html { scroll-padding-top: calc(var(--header-height) + 1rem); }
    header.app-header {
      position: sticky;
      top: 0;
      z-index: 120;
      border-bottom: 1px solid color-mix(in srgb, var(--border) 76%, transparent);
      background: rgb(var(--surface-rgb) / 0.82);
      backdrop-filter: blur(18px) saturate(140%);
    }
    .header-inner {
      max-width: calc(var(--content-width) + var(--rail-width) + 4rem);
      min-height: var(--header-height);
      margin: 0 auto;
      padding: 0.8rem 1.25rem;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 1rem;
      align-items: center;
    }
    .brand { min-width: 0; }
    .brand h1 {
      margin: 0;
      font-family: "Fraunces", Georgia, serif;
      font-size: clamp(1.15rem, 2vw, 1.7rem);
      line-height: 1.05;
      letter-spacing: -0.03em;
    }
    .brand .stats {
      color: var(--text-secondary);
      font-size: 0.86rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 0.15rem;
    }
    .controls { justify-self: end; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; justify-content: flex-end; }
    .controls button { min-height: 40px; }

    .nav-sidebar {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 0.35rem;
      margin-bottom: 0.85rem;
      padding: 0.35rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.7);
    }
    .nav-sidebar button { min-width: 44px; min-height: 40px; padding: 0 0.85rem; }
    .nav-sidebar .nav-status { min-width: 92px; text-align: center; color: var(--text-secondary); font-size: 0.86rem; font-weight: 800; }
    .nav-sidebar button:disabled, .nav-floating button:disabled { opacity: 0.4; cursor: not-allowed; }
    .kbd-hint { color: var(--muted); font-size: 0.78rem; }

    main {
      position: relative;
      max-width: calc(var(--content-width) + var(--rail-width) + 4rem);
      margin: 0 auto;
      padding: 2rem 1.25rem 7rem;
    }
    .hero {
      overflow: hidden;
      position: relative;
      border: 1px solid var(--border);
      border-radius: calc(var(--radius) + 10px);
      background:
        linear-gradient(135deg, rgb(var(--surface-rgb) / 0.92), rgb(var(--surface-rgb) / 0.72)),
        radial-gradient(circle at 82% 8%, rgb(23 92 211 / 0.18), transparent 19rem);
      box-shadow: var(--shadow);
      padding: clamp(1.3rem, 4vw, 2.4rem);
      margin-bottom: 1.4rem;
    }
    .hero::after {
      content: "";
      position: absolute;
      right: -5rem;
      bottom: -8rem;
      width: 24rem;
      height: 24rem;
      border-radius: 50%;
      border: 1px solid color-mix(in srgb, var(--accent) 26%, transparent);
      background: radial-gradient(circle, color-mix(in srgb, var(--accent) 13%, transparent), transparent 62%);
    }
    .hero-content { position: relative; z-index: 1; display: grid; grid-template-columns: 1fr auto; gap: 1.5rem; align-items: end; }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      color: var(--accent-ink);
      background: var(--accent-soft);
      border: 1px solid color-mix(in srgb, var(--accent) 26%, transparent);
      border-radius: 999px;
      padding: 0.18rem 0.55rem;
      font-weight: 700;
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .hero h2 {
      margin: 0.7rem 0 0;
      max-width: 780px;
      font-family: "Fraunces", Georgia, serif;
      font-size: clamp(2rem, 5vw, 4.6rem);
      line-height: 0.92;
      letter-spacing: -0.06em;
    }
    .hero p { max-width: 62ch; margin: 1rem 0 0; color: var(--text-secondary); font-size: 1.05rem; }
    .progress-orb {
      width: 132px;
      aspect-ratio: 1;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: conic-gradient(var(--success) var(--progress, 0deg), color-mix(in srgb, var(--border) 70%, transparent) 0);
      box-shadow: inset 0 0 0 1px var(--border), var(--shadow-soft);
    }
    .progress-orb-inner {
      width: 98px;
      aspect-ratio: 1;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: var(--surface);
      text-align: center;
      border: 1px solid var(--border);
      font-weight: 800;
    }
    .progress-orb strong { display: block; font-size: 1.55rem; line-height: 1; }
    .progress-orb span { display: block; color: var(--text-secondary); font-size: 0.74rem; margin-top: 0.15rem; }
    .hero-metrics { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1.4rem; }
    .metric {
      min-width: 132px;
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 0.75rem 0.9rem;
      background: rgb(var(--surface-rgb) / 0.62);
    }
    .metric strong { display: block; font-size: 1.35rem; line-height: 1; }
    .metric span { color: var(--text-secondary); font-size: 0.82rem; }

    .study-layout {
      display: grid;
      grid-template-columns: var(--rail-width) minmax(0, var(--content-width));
      gap: 1.35rem;
      align-items: start;
    }
    .study-map {
      position: sticky;
      top: calc(var(--header-height) + 1rem);
      max-height: calc(100vh - var(--header-height) - 2rem);
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem;
      background: rgb(var(--surface-rgb) / 0.86);
      box-shadow: var(--shadow-soft);
      text-align: center;
    }
    .study-map h2 { margin: 0 0 0.25rem; font-size: 0.92rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-secondary); }
    .map-note { margin: 0 0 0.9rem; color: var(--muted); font-size: 0.85rem; }
    .toc-topic { border-top: 1px solid var(--border); padding-top: 0.7rem; margin-top: 0.7rem; }
    .toc-topic:first-of-type { border-top: 0; padding-top: 0; margin-top: 0; }
    .toc-topic > summary {
      cursor: pointer;
      font-weight: 800;
      color: var(--text);
      list-style-position: inside;
      text-align: center;
    }
    .toc-chunk { margin-top: 0.55rem; }
    .toc-chunk summary { cursor: pointer; color: var(--text-secondary); font-size: 0.84rem; list-style-position: inside; text-align: center; }
    .toc-links {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0.38rem;
      list-style: none;
      margin: 0.55rem 0 0;
      padding: 0;
    }
    .toc-links a {
      display: grid;
      place-items: center;
      min-height: 34px;
      border-radius: 10px;
      border: 1px solid var(--border);
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.78rem;
      font-weight: 800;
      background: rgb(var(--surface-rgb) / 0.5);
      transition: background 150ms ease, color 150ms ease, border-color 150ms ease, transform 150ms ease;
    }
    .toc-links a:hover, .toc-links a.current { color: var(--accent-ink); border-color: color-mix(in srgb, var(--accent) 45%, var(--border)); background: var(--accent-soft); transform: translateY(-1px); }
    .toc-links a.reviewed { color: var(--success); background: var(--success-bg); border-color: color-mix(in srgb, var(--success) 42%, var(--border)); }
    .toc-links a.current.reviewed {
      color: var(--accent-ink);
      background: linear-gradient(135deg, var(--accent-soft), var(--success-bg));
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
    }

    .topic { margin-bottom: 2.5rem; }
    .topic-heading {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin: 2rem 0 1rem;
      color: var(--text-secondary);
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-weight: 900;
    }
    .topic-heading::after { content: ""; height: 1px; flex: 1; background: var(--border); }
    .question {
      position: relative;
      scroll-margin-top: calc(var(--header-height) + 1rem);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: linear-gradient(180deg, rgb(var(--surface-rgb) / 0.98), rgb(var(--surface-rgb) / 0.9));
      box-shadow: var(--shadow);
      padding: clamp(1rem, 3vw, 1.55rem);
      margin-bottom: 1.1rem;
      transition: border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease, opacity 220ms ease;
      display: none;
    }
    .question.active {
      display: block;
      animation: fadeIn 220ms ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .question.current {
      border-color: color-mix(in srgb, var(--accent) 52%, var(--border));
      box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 9%, transparent), var(--shadow);
    }
    .question.reviewed { border-left: 6px solid var(--success); }
    .q-header {
      display: flex;
      gap: 0.9rem;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1rem;
    }
    .q-title { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
    .q-num {
      font-family: "Fraunces", Georgia, serif;
      font-size: 1.45rem;
      font-weight: 750;
      letter-spacing: -0.03em;
      line-height: 1;
    }
    .q-id, .q-badge {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 0.22rem 0.55rem;
      border-radius: 999px;
      background: var(--surface-2);
      color: var(--text-secondary);
      border: 1px solid var(--border);
      font-size: 0.74rem;
      font-weight: 800;
      letter-spacing: 0.03em;
    }
    .q-badge { color: var(--warning-ink); background: var(--warning-bg); border-color: color-mix(in srgb, var(--warning) 30%, var(--border)); }
    .q-actions { display: flex; gap: 0.45rem; flex-wrap: wrap; justify-content: flex-end; }
    .q-actions button { min-height: 38px; padding-inline: 0.78rem; }
    .context-panel {
      border: 1px solid var(--border);
      border-radius: 18px;
      margin: 0 0 1rem;
      background: color-mix(in srgb, var(--surface-2) 72%, transparent);
      overflow: hidden;
    }
    .context-panel.visible {
      max-height: min(52vh, 620px);
      overflow: auto;
    }
    .context-label {
      padding: 0.82rem 1rem 0.25rem;
      color: var(--text-secondary);
      font-weight: 800;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .q-context {
      padding: 0 1rem 1rem;
      color: var(--text-secondary);
      font-size: 0.95rem;
      max-width: 78ch;
    }
    .section-title {
      display: block;
      margin: 1rem 0 0.2rem;
      color: var(--accent-ink);
      font-size: 0.78rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    .prompt-card {
      position: relative;
      border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--border));
      border-radius: 20px;
      padding: clamp(1rem, 3vw, 1.35rem);
      background:
        linear-gradient(135deg, color-mix(in srgb, var(--accent-soft) 68%, var(--surface) 32%), rgb(var(--surface-rgb) / 0.82));
      box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.45);
    }
    .prompt-label {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      margin-bottom: 0.5rem;
      color: var(--accent-ink);
      font-size: 0.76rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }
    .q-prompt {
      max-width: 74ch;
      font-size: clamp(1.08rem, 1.45vw, 1.24rem);
      line-height: 1.58;
      font-weight: 600;
      color: var(--text);
    }
    .q-prompt p:first-child, .q-context p:first-child { margin-top: 0; }
    .q-prompt p:last-child, .q-context p:last-child { margin-bottom: 0; }
    .choices {
      list-style: none;
      padding: 0;
      margin: 1rem 0 0;
      display: grid;
      gap: 0.64rem;
    }
    .choices li {
      position: relative;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgb(var(--surface-rgb) / 0.76);
      transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
      overflow: hidden;
    }
    .choices li:hover { transform: translateX(2px); border-color: var(--border-strong); }
    .choices input {
      position: absolute;
      opacity: 0;
      width: 1px;
      height: 1px;
    }
    .choices label {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.8rem;
      align-items: start;
      padding: 0.86rem 1rem;
      cursor: pointer;
    }
    .choices .letter {
      display: inline-grid;
      place-items: center;
      width: 2rem;
      height: 2rem;
      border-radius: 50%;
      background: var(--surface-2);
      color: var(--accent-ink);
      border: 1px solid var(--border);
      font-weight: 900;
      line-height: 1;
      transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
    }
    .choices input:focus-visible + label { outline: 3px solid var(--accent); outline-offset: -3px; border-radius: 16px; }
    .choices input:checked + label { background: color-mix(in srgb, var(--accent-soft) 55%, transparent); border-color: var(--accent); }
    .choices input:checked + label .letter { color: var(--accent-soft); background: var(--accent-ink); border-color: var(--accent-ink); }

    .question.revealed .choices label { padding-right: 8.5rem; }
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
      box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--success) 45%, transparent);
    }
    .question.revealed .choices li.correct .letter { color: var(--success-bg); background: var(--success-ink); border-color: var(--success-ink); }
    .question.revealed .choices li.incorrect {
      background:
        linear-gradient(90deg,
          color-mix(in srgb, var(--danger-bg) 92%, var(--surface) 8%),
          color-mix(in srgb, var(--danger-bg) 76%, transparent)
        );
      border-color: var(--danger);
      box-shadow:
        inset 4px 0 0 var(--danger),
        0 8px 22px color-mix(in srgb, var(--danger) 16%, transparent);
    }
    .question.revealed .choices li.incorrect .letter { color: var(--danger-bg); background: var(--danger-ink); border-color: var(--danger-ink); }
    .question.revealed .choices li.incorrect label > span:last-child {
      text-decoration: line-through;
      text-decoration-thickness: 2px;
      text-decoration-color: color-mix(in srgb, var(--danger) 70%, transparent);
    }
    .question.revealed .choices li.correct.missed {
      background:
        linear-gradient(90deg,
          color-mix(in srgb, var(--success-bg) 82%, var(--surface) 18%),
          color-mix(in srgb, var(--warning-bg) 28%, var(--success-bg) 72%)
        );
      border-color: var(--success);
      box-shadow:
        inset 4px 0 0 var(--success),
        0 8px 22px color-mix(in srgb, var(--success) 14%, transparent);
    }
    .question.revealed .choices li.correct.missed .letter { color: var(--success-bg); background: var(--success-ink); border-color: var(--success-ink); }
    .question.revealed .choices li::after {
      position: absolute;
      top: 50%;
      right: 0.85rem;
      transform: translateY(-50%);
      padding: 0.28rem 0.56rem;
      border-radius: 999px;
      font-size: 0.74rem;
      font-weight: 900;
      letter-spacing: 0.02em;
      white-space: nowrap;
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
      margin-top: 0.75rem;
      padding: 0.65rem 0.9rem;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.92rem;
      min-height: 2.5rem;
    }
    .answer-status.empty { color: var(--muted); }
    .answer-status.correct,
    .answer-status.incorrect,
    .answer-status.partial {
      display: grid;
      grid-template-columns: auto 1fr;
      align-items: center;
      gap: 0.65rem;
      border: 1px solid transparent;
    }
    .answer-status.correct::before,
    .answer-status.incorrect::before,
    .answer-status.partial::before {
      display: inline-grid;
      place-items: center;
      width: 1.65rem;
      height: 1.65rem;
      border-radius: 50%;
      font-weight: 900;
      line-height: 1;
    }
    .answer-status.correct {
      color: var(--success-ink);
      background: var(--success-bg);
      border-color: var(--success);
    }
    .answer-status.correct::before { content: "✓"; color: var(--success-bg); background: var(--success-ink); }
    .answer-status.incorrect {
      color: var(--danger-ink);
      background:
        linear-gradient(135deg,
          color-mix(in srgb, var(--danger-bg) 94%, var(--surface) 6%),
          color-mix(in srgb, var(--danger-bg) 76%, var(--warning-bg) 24%)
        );
      border-color: var(--danger);
      box-shadow: 0 12px 28px color-mix(in srgb, var(--danger) 18%, transparent);
    }
    .answer-status.incorrect::before { content: "✕"; color: var(--danger-bg); background: var(--danger-ink); }
    .answer-status.partial {
      color: var(--warning-ink);
      background:
        linear-gradient(135deg,
          color-mix(in srgb, var(--warning-bg) 94%, var(--surface) 6%),
          color-mix(in srgb, var(--warning-bg) 76%, var(--success-bg) 24%)
        );
      border-color: var(--warning);
      box-shadow: 0 10px 22px color-mix(in srgb, var(--warning) 14%, transparent);
    }
    .answer-status.partial::before { content: "◐"; color: var(--warning-bg); background: var(--warning-ink); }

    .answer-shell { margin-top: 1rem; }
    .answer-locked {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.9rem;
      border: 1px dashed var(--border-strong);
      border-radius: 18px;
      padding: 0.82rem 0.9rem;
      background: color-mix(in srgb, var(--surface-2) 62%, transparent);
      color: var(--text-secondary);
    }
    .answer-locked strong { color: var(--text); }
    .answer-revealed {
      display: none;
      border: 1px solid color-mix(in srgb, var(--success) 36%, var(--border));
      border-radius: 18px;
      padding: 1rem;
      background: var(--success-bg);
      color: var(--text);
    }
    .question.revealed .answer-locked { display: none; }
    .question.revealed .answer-revealed { display: block; animation: reveal 220ms ease-out; }
    @keyframes reveal { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    .answer-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.7rem; }
    .answer-card {
      border: 1px solid color-mix(in srgb, var(--success) 28%, var(--border));
      border-radius: 14px;
      padding: 0.75rem;
      background: rgb(var(--surface-rgb) / 0.72);
    }
    .answer-card .label { display: block; color: var(--success); font-weight: 900; font-size: 0.77rem; text-transform: uppercase; letter-spacing: 0.08em; }
    .answer-card strong { font-size: 1.1rem; }
    .answer-tools { display: flex; justify-content: flex-end; margin-top: 0.75rem; }
    .comments { margin-top: 0.85rem; border-top: 1px solid color-mix(in srgb, var(--success) 24%, var(--border)); padding-top: 0.85rem; }
    .comments summary { cursor: pointer; font-weight: 900; color: var(--text); }
    .comment { padding: 0.75rem 0; border-top: 1px solid color-mix(in srgb, var(--success) 20%, var(--border)); }
    .comment:first-of-type { border-top: 0; }
    .comment-meta { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.25rem; }
    .comment .badge {
      display: inline-block;
      margin-left: 0.35rem;
      padding: 0.1rem 0.42rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-ink);
      font-size: 0.7rem;
      font-weight: 900;
    }

    .nav-floating {
      position: fixed;
      left: 50%;
      bottom: max(1rem, env(safe-area-inset-bottom));
      z-index: 110;
      transform: translateX(-50%);
      display: flex;
      gap: 0.45rem;
      align-items: center;
      padding: 0.45rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.88);
      backdrop-filter: blur(16px);
      box-shadow: var(--shadow);
    }
    .nav-floating button { min-width: 46px; min-height: 46px; padding: 0 1rem; }
    .nav-floating .nav-status { min-width: 92px; text-align: center; color: var(--text-secondary); font-size: 0.86rem; font-weight: 800; }

    .mobile-only { display: none !important; }
    .desktop-only { display: inline-flex !important; }

    @media (max-width: 1060px) {
      .study-layout { grid-template-columns: 1fr; }
      .study-map { position: relative; top: auto; max-height: none; }
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
      body { font-size: 16px; }
      .header-inner { grid-template-columns: 1fr; gap: 0.65rem; }
      .controls { justify-content: stretch; display: grid; grid-template-columns: 1fr 1fr auto auto; }
      .controls button { padding-inline: 0.7rem; }
      .kbd-hint { display: none; }
      main { padding: 1rem 0.75rem 6.5rem; }
      .hero-content { grid-template-columns: 1fr; }
      .progress-orb { width: 104px; }
      .progress-orb-inner { width: 78px; }
      .q-header { flex-direction: column; }
      .q-actions { width: 100%; justify-content: stretch; }
      .q-actions button { flex: 1; }
      .answer-grid { grid-template-columns: 1fr; }
      .answer-locked { align-items: stretch; flex-direction: column; }
      .answer-locked button { width: 100%; min-height: 46px; }
      .nav-floating { left: 0.75rem; right: 0.75rem; transform: none; justify-content: space-between; }
      .nav-floating button { flex: 1; }
      .study-map { padding: 0.75rem; }
      .toc-links { grid-template-columns: repeat(5, minmax(0, 1fr)); }
    }
    @media (max-width: 560px) {
      .question.revealed .choices label { padding-right: 1rem; padding-bottom: 2.35rem; }
      .question.revealed .choices li::after {
        top: auto;
        right: auto;
        bottom: 0.65rem;
        left: 3.75rem;
        transform: none;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { scroll-behavior: auto !important; animation: none !important; transition: none !important; }
    }
    @media (prefers-reduced-motion: no-preference) {
      .question.shake-incorrect .answer-status.incorrect { animation: answerShake 360ms ease-out; }
      @keyframes answerShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        50% { transform: translateX(4px); }
        75% { transform: translateX(-2px); }
      }
    }
    @media print {
      header, .study-map, .controls, .nav-floating, #progress-bar, .skip-link, .answer-locked, .answer-tools { display: none !important; }
      body { background: #fff; color: #000; font-size: 12pt; padding-bottom: 0; }
      body::before, .hero { display: none; }
      main { padding: 0; max-width: none; }
      .study-layout { display: block; }
      .question { display: block !important; box-shadow: none; border: 1px solid #bbb; page-break-inside: avoid; }
      .question.active { display: block !important; }
      .answer-revealed { display: block !important; }
      .exhibit img { box-shadow: none; }
    }

    /* ----- Exhibits & special question-type widgets ----- */
    .exhibits { margin-top: 1rem; display: grid; gap: 1rem; }
    .exhibit { margin: 0; border: 1px solid var(--border); border-radius: 18px; padding: 0.75rem; background: rgb(var(--surface-rgb) / 0.7); }
    .exhibit img { display: block; margin: 0 auto; max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--border); }
    .exhibit figcaption { margin-top: 0.5rem; text-align: center; color: var(--text-secondary); font-size: 0.82rem; font-weight: 700; }
    .exhibit pre { margin: 0; }
    .exhibit table { border-collapse: collapse; width: 100%; }
    .exhibit table th, .exhibit table td { border: 1px solid var(--border); padding: 0.4rem 0.6rem; }
    .exhibit-missing { padding: 1rem; text-align: center; background: var(--warning-bg); color: var(--warning-ink); border-color: color-mix(in srgb, var(--warning) 30%, var(--border)); }
    .exhibit-missing-title { font-weight: 800; margin-bottom: 0.35rem; }
    .exhibit-missing a { color: var(--accent-ink); text-decoration: underline; }

    .dragdrop-widget, .other-widget {
      margin-top: 1rem;
      padding: 1rem;
      border: 1px dashed var(--border-strong);
      border-radius: 18px;
      background: color-mix(in srgb, var(--surface-2) 60%, transparent);
    }
    .widget-note { color: var(--text-secondary); font-size: 0.9rem; margin: 0 0 0.75rem; }
    .dragdrop-board {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
      gap: 1rem;
      margin-top: 0.75rem;
    }
    @media (max-width: 720px) {
      .dragdrop-board { grid-template-columns: 1fr; }
    }
    .dragdrop-column {
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 0.85rem;
      background: rgb(var(--surface-rgb) / 0.65);
    }
    .dragdrop-column-title {
      margin: 0 0 0.6rem;
      font-size: 0.78rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--text-secondary);
      font-weight: 800;
    }
    .dragdrop-chips {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      min-height: 3rem;
    }
    .dragdrop-targets {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .dragdrop-chip {
      cursor: grab;
      user-select: none;
      padding: 0.42rem 0.75rem;
      border-radius: 999px;
      background: rgb(var(--surface-rgb) / 0.85);
      border: 1px solid var(--border);
      font-weight: 700;
      font-size: 0.86rem;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: background-color 120ms ease, border-color 120ms ease, transform 120ms ease;
    }
    .dragdrop-chip:active { cursor: grabbing; }
    .dragdrop-chip.selected {
      background: var(--accent-soft);
      color: var(--accent-ink);
      border-color: var(--accent);
    }
    .dragdrop-chip.placed {
      opacity: 0.55;
      cursor: default;
      background: var(--surface-2);
      color: var(--text-secondary);
      border-style: dashed;
    }
    .dragdrop-chip.dragging { opacity: 0.4; transform: scale(0.97); }

    .dragdrop-target {
      position: relative;
      padding: 0.6rem 2.2rem 0.6rem 0.85rem;
      border-radius: 12px;
      border: 1px dashed var(--border-strong);
      background: rgb(var(--surface-rgb) / 0.85);
      color: var(--text-secondary);
      min-height: 2.4rem;
      font-size: 0.9rem;
      transition: background-color 120ms ease, border-color 120ms ease;
    }
    .dragdrop-target.drop-hover {
      border-color: var(--accent);
      background: var(--accent-soft);
    }
    .dragdrop-target.filled {
      color: var(--text);
      border-style: solid;
      background: rgb(var(--surface-rgb));
      font-weight: 700;
    }
    .dragdrop-target-label { display: inline-block; max-width: 100%; }
    .dragdrop-target .dragdrop-clear {
      position: absolute;
      top: 50%;
      right: 0.5rem;
      transform: translateY(-50%);
      width: 1.6rem;
      height: 1.6rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--surface-2);
      color: var(--text-secondary);
      font-size: 1rem;
      line-height: 1;
      cursor: pointer;
      display: none;
    }
    .dragdrop-target.filled .dragdrop-clear { display: inline-flex; align-items: center; justify-content: center; }
    .dragdrop-target.filled .dragdrop-clear:hover { background: var(--danger-bg); color: var(--danger-ink); border-color: var(--danger); }

    .answer-card.answer-missing { background: var(--warning-bg); border-color: color-mix(in srgb, var(--warning) 30%, var(--border)); }
    .answer-card.answer-missing .label { color: var(--warning-ink); }
  </style>
</head>
<body>
  <a class="skip-link btn" href="#questions">Skip to questions</a>
  <div id="progress-bar" role="progressbar" aria-label="Study progress"></div>
  <header class="app-header">
    <div class="header-inner">
      <div class="brand">
        <h1>$title</h1>
        <div class="stats">$stats · <span id="progress-text">0 reviewed</span></div>
      </div>
      <div class="controls" aria-label="Study controls">
        <button id="resume-unreviewed" class="secondary" type="button" title="Jump to first unreviewed question">Resume</button>
        <button id="show-all-answers" class="secondary" type="button" title="Show all answers">Show answers</button>
        <button id="theme-toggle" class="secondary" type="button" title="Toggle dark mode">🌙</button>
        <button id="toggle-map" class="ghost mobile-only" type="button" title="Toggle question map">Map</button>
        <button id="jump-toc" class="ghost desktop-only" type="button" title="Back to map">Map</button>
      </div>
    </div>
  </header>
  <main id="questions">
"""

HTML_TAIL = """
  </main>
  <div class="nav-floating" aria-label="Question navigation">
    <button class="secondary nav-prev-btn" type="button" title="Previous question (←)" aria-label="Previous question">←</button>
    <div class="nav-status" aria-live="polite">Q 1</div>
    <button class="secondary nav-next-btn" type="button" title="Next question (→)" aria-label="Next question">→</button>
  </div>
  <script>
    const STORAGE_KEY = location.pathname + '-reviewed';
    const SELECTIONS_KEY = location.pathname + '-selections';
    const questions = Array.from(document.querySelectorAll('.question'));
    const ids = questions.map(q => q.id);
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const heroPct = document.getElementById('hero-pct');
    const heroAttempted = document.getElementById('hero-attempted');
    const heroCorrect = document.getElementById('hero-correct');
    const heroReviewed = document.getElementById('hero-reviewed');
    const heroRemaining = document.getElementById('hero-remaining');
    const heroOrb = document.getElementById('hero-progress-orb');
    const navStatuses = document.querySelectorAll('.nav-status');
    progressBar.setAttribute('aria-valuemin', '0');
    progressBar.setAttribute('aria-valuemax', String(ids.length));

    const themeBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('examguide-theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', initialTheme);
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
      btn.addEventListener('click', () => {
        const q = btn.closest('.question');
        const wasHidden = !q.classList.contains('revealed');
        q.classList.toggle('revealed');
        updateAnswerFeedback(q);
        if (wasHidden && q.dataset.result === 'incorrect') {
          q.classList.remove('shake-incorrect');
          void q.offsetWidth;
          q.classList.add('shake-incorrect');
          setTimeout(() => q.classList.remove('shake-incorrect'), 450);
        }
        syncAnswerButtons();
      });
    });

    let selections = {};
    try { selections = JSON.parse(localStorage.getItem(SELECTIONS_KEY) || '{}'); } catch (e) { selections = {}; }
    function saveSelections() {
      localStorage.setItem(SELECTIONS_KEY, JSON.stringify(selections));
      updateProgress();
    }
    function getSelected(q) {
      return new Set(selections[q.id] || []);
    }
    function setSelected(q, letters) {
      if (letters.size === 0) delete selections[q.id];
      else selections[q.id] = Array.from(letters);
      saveSelections();
    }
    function getCorrect(q) {
      return new Set(Array.from(q.querySelectorAll('.choices li.correct')).map(li => li.dataset.letter).filter(Boolean));
    }
    function isCorrect(q) {
      // Questions without a multiple-choice list (hotspot, drag-drop, other)
      // are never "correct" in the multiple-choice sense — they have no defined
      // answer key in the data we captured, so they neither help nor hurt
      // the scored progress counters.
      if (!q.querySelector('.choices')) return false;
      const selected = getSelected(q);
      const correct = getCorrect(q);
      if (correct.size === 0) return false;
      return selected.size > 0 && selected.size === correct.size && [...selected].every(x => correct.has(x));
    }
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
      const status = q.querySelector('.answer-status');
      if (!status) return;
      delete q.dataset.result;
      // Hotspot / drag-drop / other — informational status only.
      if (!hasChoices) {
        if (q.dataset.qtype === 'hotspot') {
          if (!revealed) {
            status.className = 'answer-status empty';
            status.textContent = 'Review the exhibits above and reason about which areas to select.';
          } else {
            status.className = 'answer-status empty';
            status.textContent = 'HOTSPOT answer not available from ExamTopics.';
          }
        } else if (q.querySelector('.dragdrop-widget')) {
          // For drag-drop, surface the most-voted answer text on reveal so the
          // learner can compare their placements to the community consensus.
          const mostVoted = q.dataset.mostVoted || '';
          if (!revealed) {
            status.className = 'answer-status empty';
            status.textContent = 'Drag items onto targets above, then reveal to compare against the community answer.';
          } else if (mostVoted) {
            status.className = 'answer-status';
            status.textContent = `Community answer: ${mostVoted}`;
          } else {
            status.className = 'answer-status empty';
            status.textContent = 'DRAG DROP answer not available from ExamTopics — your placements are practice-only.';
          }
        } else {
          if (!revealed) {
            status.className = 'answer-status empty';
            status.textContent = 'This question type is not interactive.';
          } else {
            status.className = 'answer-status empty';
            status.textContent = 'Answer not provided by ExamTopics for this question type.';
          }
        }
        return;
      }
      if (!revealed) {
        if (selected.size === 0) { status.className = 'answer-status empty'; status.textContent = 'Select your answer, then reveal it.'; }
        else { status.className = 'answer-status'; status.textContent = `${selected.size} selected. Ready to reveal.`; }
        return;
      }
      const missed = [...correct].filter(x => !selected.has(x));
      const wrong = [...selected].filter(x => !correct.has(x));
      if (correct.size === 0) {
        // Multiple-choice question whose answer isn't in the dataset.
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
        // Partial credit: multi-select with no wrong picks and at least one
        // missed correct answer (and at least one correct pick) reads as
        // "partially correct" rather than "incorrect". The binary hero metric
        // behaviour stays the same because isCorrect() / scoring is unchanged.
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
      const choiceList = q.querySelector('.choices');
      if (!choiceList) {
        // Still surface answer feedback (status messages, hotspot reveal, etc.).
        updateAnswerFeedback(q);
        return;
      }
      const saved = getSelected(q);
      choiceList.querySelectorAll('input').forEach(input => {
        if (saved.has(input.value)) input.checked = true;
        input.addEventListener('change', () => {
          if (q.classList.contains('revealed')) return;
          const isMulti = choiceList.dataset.multiple === 'true';
          if (!isMulti) {
            const selected = new Set();
            choiceList.querySelectorAll('input:checked').forEach(inp => selected.add(inp.value));
            setSelected(q, selected);
          } else {
            const selected = new Set();
            choiceList.querySelectorAll('input:checked').forEach(inp => selected.add(inp.value));
            setSelected(q, selected);
          }
          updateAnswerFeedback(q);
        });
      });
      updateAnswerFeedback(q);
    });

    let reviewed = new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'));
    function saveReviewed() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(reviewed)));
      updateProgress();
    }
    function updateReviewButton(btn, id) {
      const isReviewed = reviewed.has(id);
      btn.setAttribute('aria-pressed', String(isReviewed));
      btn.textContent = isReviewed ? 'Reviewed ✓' : 'Mark reviewed';
      btn.classList.toggle('active', isReviewed);
    }
    function updateProgress() {
      const total = ids.length || 1;
      // Only count questions that actually have a multiple-choice list.
      // Hotspot / drag-drop / other questions don't affect "attempted/correct".
      const isMcQuestion = (q) => !!(q && q.querySelector('.choices'));
      const attemptedIds = Object.keys(selections).filter(id => {
        const q = document.getElementById(id);
        return isMcQuestion(q) && selections[id] && selections[id].length > 0;
      });
      const attempted = attemptedIds.length;
      const correctCount = attemptedIds.filter(id => {
        const q = document.getElementById(id);
        return q && isCorrect(q);
      }).length;
      const pct = Math.round((reviewed.size / total) * 100);
      progressBar.style.width = pct + '%';
      progressBar.setAttribute('aria-valuenow', String(reviewed.size));
      progressText.textContent = `${reviewed.size}/${ids.length} reviewed · ${attempted} attempted · ${correctCount} correct`;
      if (heroPct) heroPct.textContent = `${pct}%`;
      if (heroAttempted) heroAttempted.textContent = attempted;
      if (heroCorrect) heroCorrect.textContent = correctCount;
      if (heroReviewed) heroReviewed.textContent = reviewed.size;
      if (heroRemaining) heroRemaining.textContent = Math.max(ids.length - reviewed.size, 0);
      if (heroOrb) heroOrb.style.setProperty('--progress', `${pct * 3.6}deg`);
      ids.forEach(id => {
        const q = document.getElementById(id);
        const tocLink = document.querySelector(`.toc-links a[href="#${id}"]`);
        const isReviewed = reviewed.has(id);
        if (q) q.classList.toggle('reviewed', isReviewed);
        if (tocLink) tocLink.classList.toggle('reviewed', isReviewed);
      });
      document.querySelectorAll('.btn-review').forEach(btn => updateReviewButton(btn, btn.closest('.question').id));
    }
    document.querySelectorAll('.btn-review').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.question').id;
        reviewed.has(id) ? reviewed.delete(id) : reviewed.add(id);
        saveReviewed();
      });
    });

    /* ----- Drag-drop interactivity ----- */
    const DRAGDROP_KEY = location.pathname + '-dragdrop';
    let dragdropSelections = {};
    try { dragdropSelections = JSON.parse(localStorage.getItem(DRAGDROP_KEY) || '{}'); } catch (e) { dragdropSelections = {}; }

    function saveDragdrop() {
      localStorage.setItem(DRAGDROP_KEY, JSON.stringify(dragdropSelections));
    }

    function attachDragdropWidget(q) {
      const widget = q.querySelector('.dragdrop-widget');
      if (!widget) return;
      // Display-only fallback: no interactive widget, nothing to wire up.
      if (!widget.classList.contains('dragdrop-widget-interactive')) return;

      const chipsContainer = widget.querySelector('.dragdrop-source .dragdrop-chips');
      const targetsContainer = widget.querySelector('.dragdrop-targets');
      const chips = chipsContainer ? Array.from(chipsContainer.querySelectorAll('.dragdrop-chip')) : [];
      const targets = targetsContainer ? Array.from(targetsContainer.querySelectorAll('.dragdrop-target')) : [];
      if (!chips.length || !targets.length) return;

      // Load saved placements: { targetIdx: chipIdx }
      const saved = dragdropSelections[q.id] || {};
      let activeChip = null; // for click-to-place

      function persist() {
        dragdropSelections[q.id] = saved;
        saveDragdrop();
      }

      function placedChipIdx(targetIdx) {
        return Object.prototype.hasOwnProperty.call(saved, String(targetIdx))
          ? saved[String(targetIdx)]
          : undefined;
      }

      function placeChip(targetIdx, chipIdx) {
        // If the same chip is already on this target, do nothing.
        if (placedChipIdx(targetIdx) === chipIdx) return;
        // Remove the chip from any other target first.
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
        // Reset chips
        chips.forEach((chip) => {
          chip.classList.remove('placed', 'selected', 'dragging');
          chip.setAttribute('aria-grabbed', 'false');
        });
        // Mark placed chips and update target text
        const placedChipIdxs = new Set(Object.values(saved).map(Number));
        chips.forEach((chip) => {
          if (placedChipIdxs.has(Number(chip.dataset.value))) {
            chip.classList.add('placed');
          }
        });
        targets.forEach((target) => {
          const tIdx = Number(target.dataset.target);
          const labelEl = target.querySelector('.dragdrop-target-label');
          const chipIdx = placedChipIdx(tIdx);
          if (chipIdx !== undefined) {
            const chip = chips.find(c => Number(c.dataset.value) === Number(chipIdx));
            if (chip) {
              labelEl.textContent = chip.dataset.label || chip.textContent.trim();
              target.classList.add('filled');
              target.setAttribute('aria-label', `Target ${tIdx + 1}: ${labelEl.textContent}`);
            }
          } else {
            labelEl.textContent = target.dataset.placeholder || '';
            target.classList.remove('filled');
            target.setAttribute('aria-label', `Target ${tIdx + 1}: empty`);
          }
        });
      }

      // Initial render from saved state
      render();

      // ----- Source chip handlers -----
      chips.forEach((chip) => {
        const chipIdx = Number(chip.dataset.value);

        // Click: toggle "active" then click a target to drop.
        chip.addEventListener('click', (ev) => {
          if (q.classList.contains('revealed')) return;
          if (chip.classList.contains('placed')) {
            // Placed chips: clicking moves them back to the source pool.
            for (const [tIdx, cIdx] of Object.entries(saved)) {
              if (Number(cIdx) === chipIdx) delete saved[tIdx];
            }
            render();
            persist();
            return;
          }
          // Toggle selection
          if (activeChip === chip) {
            activeChip = null;
            chip.classList.remove('selected');
          } else {
            chips.forEach(c => c.classList.remove('selected'));
            activeChip = chip;
            chip.classList.add('selected');
          }
        });

        // HTML5 drag-and-drop
        chip.addEventListener('dragstart', (e) => {
          if (q.classList.contains('revealed')) return;
          e.dataTransfer.setData('text/plain', String(chipIdx));
          e.dataTransfer.effectAllowed = 'move';
          chip.classList.add('dragging');
        });
        chip.addEventListener('dragend', () => {
          chip.classList.remove('dragging');
        });
        chip.addEventListener('keydown', (e) => {
          if (q.classList.contains('revealed')) return;
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            chip.click();
          }
        });
      });

      // ----- Target handlers -----
      targets.forEach((target) => {
        const tIdx = Number(target.dataset.target);

        target.addEventListener('click', (ev) => {
          if (q.classList.contains('revealed')) return;
          // The clear button handles its own click.
          if (ev.target.closest('.dragdrop-clear')) return;
          if (activeChip) {
            placeChip(tIdx, Number(activeChip.dataset.value));
            activeChip.classList.remove('selected');
            activeChip = null;
          } else if (placedChipIdx(tIdx) !== undefined) {
            clearTarget(tIdx);
          }
        });

        target.addEventListener('dragover', (e) => {
          if (q.classList.contains('revealed')) return;
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
          target.classList.add('drop-hover');
        });
        target.addEventListener('dragleave', () => {
          target.classList.remove('drop-hover');
        });
        target.addEventListener('drop', (e) => {
          if (q.classList.contains('revealed')) return;
          e.preventDefault();
          target.classList.remove('drop-hover');
          const data = e.dataTransfer.getData('text/plain');
          const chipIdx = Number(data);
          if (Number.isFinite(chipIdx)) placeChip(tIdx, chipIdx);
        });

        // Clear button
        const clearBtn = target.querySelector('.dragdrop-clear');
        if (clearBtn) {
          clearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (q.classList.contains('revealed')) return;
            clearTarget(Number(clearBtn.dataset.target));
          });
        }
      });

      // Reset button (added dynamically if any chip is placed)
      let resetBtn = widget.querySelector('.dragdrop-reset');
      if (!resetBtn) {
        resetBtn = document.createElement('button');
        resetBtn.type = 'button';
        resetBtn.className = 'secondary dragdrop-reset';
        resetBtn.textContent = 'Reset placements';
        widget.appendChild(resetBtn);
      }
      resetBtn.addEventListener('click', () => {
        if (q.classList.contains('revealed')) return;
        clearAll();
      });
    }

    questions.forEach(q => {
      attachDragdropWidget(q);
    });

    let currentIndex = 0;
    function syncCurrent(index, opts = {}) {
      currentIndex = Math.max(0, Math.min(index, ids.length - 1));
      const activeId = ids[currentIndex];
      questions.forEach((q, i) => {
        const isActive = i === currentIndex;
        q.classList.toggle('active', isActive);
        q.classList.toggle('current', isActive);
      });
      document.querySelectorAll('.toc-links a.current').forEach(a => a.classList.remove('current'));
      const link = document.querySelector(`.toc-links a[href="#${activeId}"]`);
      if (link) {
        link.classList.add('current');
        if (!opts.noScroll) link.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      const q = questions[currentIndex];
      navStatuses.forEach(el => { if (el && q) el.textContent = `${q.dataset.label || 'Q'} · ${currentIndex + 1}/${ids.length}`; });
      syncNavButtons();
      if (!opts.replaceOnly) {
        history.pushState(null, '', `#${activeId}`);
      }
    }
    function syncNavButtons() {
      const atStart = currentIndex === 0;
      const atEnd = currentIndex === ids.length - 1;
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
      index = Math.max(0, Math.min(index, ids.length - 1));
      syncCurrent(index);
      questions[currentIndex]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    document.querySelectorAll('.nav-prev-btn').forEach(btn => btn.addEventListener('click', () => goToQuestion(currentIndex - 1)));
    document.querySelectorAll('.nav-next-btn').forEach(btn => btn.addEventListener('click', () => goToQuestion(currentIndex + 1)));
    document.getElementById('resume-unreviewed').addEventListener('click', () => {
      const firstUnreviewed = ids.find(id => !reviewed.has(id));
      goToQuestion(firstUnreviewed ? ids.indexOf(firstUnreviewed) : 0);
    });
    document.getElementById('jump-toc').addEventListener('click', () => {
      if (window.innerWidth <= 1060) setMapCollapsed(false);
      document.getElementById('study-map')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    const studyMap = document.getElementById('study-map');
    const toggleMapBtn = document.getElementById('toggle-map');
    function isMapCollapsed() {
      return studyMap && studyMap.classList.contains('collapsed');
    }
    function setMapCollapsed(collapsed, opts = {}) {
      if (!studyMap) return;
      studyMap.classList.toggle('collapsed', collapsed);
      if (toggleMapBtn) {
        toggleMapBtn.textContent = collapsed ? 'Map' : 'Hide map';
        toggleMapBtn.setAttribute('aria-pressed', String(!collapsed));
        toggleMapBtn.setAttribute('aria-expanded', String(!collapsed));
        toggleMapBtn.setAttribute('aria-controls', 'study-map');
      }
      if (!collapsed && opts.scroll) {
        studyMap.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
    if (toggleMapBtn) {
      toggleMapBtn.addEventListener('click', () => setMapCollapsed(!isMapCollapsed(), { scroll: true }));
    }
    document.querySelectorAll('.toc-links a').forEach(a => {
      a.addEventListener('click', e => {
        const href = a.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        e.preventDefault();
        const id = href.slice(1);
        const idx = ids.indexOf(id);
        if (idx >= 0) {
          goToQuestion(idx);
          if (window.innerWidth <= 1060) setMapCollapsed(true);
        }
      });
    });
    document.addEventListener('keydown', e => {
      if (e.target.matches('input, textarea, select, button, summary')) return;
      if (e.key === 'ArrowLeft') goToQuestion(currentIndex - 1);
      if (e.key === 'ArrowRight') goToQuestion(currentIndex + 1);
      if (e.key.toLowerCase() === 'a') {
        questions[currentIndex]?.classList.toggle('revealed');
        syncAnswerButtons();
      }
      if (e.key.toLowerCase() === 'r') {
        const id = ids[currentIndex];
        reviewed.has(id) ? reviewed.delete(id) : reviewed.add(id);
        saveReviewed();
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
        # Both plain text and HTML present: render plain text on top of HTML
        # so screen-readers and copy/paste still get something useful.
        return f"{html.escape(plain_text)}<br>{cleaned}"

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
        # Fall back to src as a relative path if local_path missing/malformed.
        if not rel:
            src_fallback = exhibit.get("src") or ""
            if src_fallback and not src_fallback.startswith("http"):
                rel = f"../{src_fallback.lstrip('/')}"
        if local and Path(local).exists() and rel:
            return (
                f'<figure class="exhibit exhibit-image">'
                f'<img src="{html.escape(rel, quote=True)}" alt="{alt}" loading="lazy">'
                f'<figcaption class="exhibit-caption">{caption_label}{alt_text}</figcaption>'
                f'</figure>'
            )
        # Offline fallback banner — link to the upstream image on ExamTopics.
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
        code = exhibit.get("code") or exhibit.get("text") or ""
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


def format_case_study_sections(text: str) -> str:
    """Add visual section labels to common case-study headings."""
    if not text:
        return ""
    section_labels = [
        "Case study",
        "Overview",
        "Existing Environment",
        "Planned Changes",
        "Requirements",
        "Data Analytics Requirements",
        "Data Preparation Requirements",
        "Semantic Model Requirements",
        "General Requirements",
        "To answer",
        "To start",
    ]
    for label in section_labels:
        pattern = re.compile(rf"(^|<br\s*/?>|\n|\s)\s*{re.escape(label)}\s*-\s*", re.IGNORECASE)
        text = pattern.sub(rf'\1<span class="section-title">{label}</span>', text)
    return text


def html_text(text: str) -> str:
    """Format question text for HTML while preserving simple source markup."""
    return format_case_study_sections(clean_html(text)).replace("\n", "<br>")


def split_question_text(text: str) -> tuple[list[str], str, str]:
    """Separate long case-study context from the actual exam task."""
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
        lead = re.sub(r"\s*-\s*$", "", re.sub(r"<[^>]+>", "", lines[0])).strip().upper()
        if lead in lead_label_map:
            labels.append(lead_label_map[lead])
            lines.pop(0)
        else:
            break

    if not lines:
        return labels, "", ""

    # Short questions (≤ 4 lines) don't have a real case-study preamble; keep
    # the entire text as the prompt so the cue-detection heuristic doesn't
    # mis-segment a 2- or 3-sentence question into "context + task" pairs.
    if len(lines) <= 4:
        return labels, "", "\n".join(lines).strip()

    cue = re.compile(
        r"^(You need to|Which\b|What\b|How\b|Where\b|When\b|Why\b|Select\b|Use the drop-down|Drag\b|For each\b|In which\b|To answer\b)",
        re.IGNORECASE,
    )
    cue_indices = [i for i, line in enumerate(lines) if cue.search(re.sub(r"<[^>]+>", "", line).strip())]
    start = 0
    if cue_indices:
        tail_floor = max(0, len(lines) - 10)
        tail_candidates = [i for i in cue_indices if i >= tail_floor or i >= int(len(lines) * 0.55)]
        start = min(tail_candidates) if tail_candidates else (cue_indices[-1] if len(lines) > 4 else min(cue_indices))
    elif len(lines) > 5:
        start = len(lines) - 2

    preamble = "\n".join(lines[:start]).strip()
    prompt = "\n".join(lines[start:]).strip()
    if not prompt:
        prompt = preamble
        preamble = ""
    return labels, preamble, prompt


def render_question_html(q: dict[str, Any], is_active: bool = False) -> str:
    parts = []
    q_id_raw = q.get("question_id", "")
    q_id = html.escape(str(q_id_raw))
    exam = html.escape(q.get("exam", "").upper())
    topic = q.get("topic", 0)
    num = q.get("question_number", 0)
    q_type = (q.get("question_type") or "").strip().lower()
    anchor = f"q-{exam.lower()}-t{topic}-n{num}-{slug_id(q_id_raw)}"

    labels, preamble, prompt = split_question_text(q.get("question_text", ""))
    label_text = f"Q{topic}.{num}"

    active_cls = " active" if is_active else ""
    most_voted_attr = html.escape(str(q.get("most_voted_answer") or ""))
    parts.append(f'<article class="question{active_cls}" id="{anchor}" data-topic="{topic}" data-num="{num}" data-label="{label_text}" data-qtype="{html.escape(q_type)}" data-most-voted="{most_voted_attr}">')
    parts.append('<div class="q-header">')
    parts.append('<div class="q-title">')
    parts.append(f'<span class="q-num">{label_text}</span>')
    parts.append(f'<span class="q-id">ID {q_id}</span>')
    # If the data layer tagged this question with a non-standard type, show a badge.
    badge_labels = list(labels)
    if q_type and q_type not in {"single", "multiple"}:
        badge_labels.append(q_type.replace("_", " ").title())
    for label in badge_labels:
        parts.append(f'<span class="q-badge">{html.escape(label)}</span>')
    parts.append('</div>')
    parts.append('<div class="q-actions">')
    parts.append(f'<button class="secondary btn-review" type="button" aria-label="Mark {label_text} as reviewed">Mark reviewed</button>')
    parts.append('</div></div>')

    if preamble:
        parts.append('<div class="context-panel visible">')
        parts.append('<div class="context-label">Case context</div>')
        parts.append(f'<div class="q-context">{html_text(preamble)}</div>')
        parts.append('</div>')

    parts.append('<section class="prompt-card" aria-label="Question prompt">')
    parts.append('<div class="prompt-label">Exam task</div>')
    parts.append(f'<div class="q-prompt">{html_text(prompt)}</div>')
    parts.append('</section>')

    # Exhibits are rendered after the prompt and before the choices/widget.
    exhibits_html = render_exhibits_block(q, label_text)
    if exhibits_html:
        parts.append(exhibits_html)

    choices = q.get("choices", [])
    correct = set(q.get("correct_answers", []))
    has_correct_answer = len(correct) > 0

    if choices:
        is_multiple = len(correct) > 1
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
            parts.append('</li>')
        parts.append('</ol>')
        parts.append('<div class="answer-status" aria-live="polite"></div>')
    else:
        # Hotspot / drag-drop / unknown — no multiple-choice choices available.
        # The drag-drop and other widgets include their own .answer-status
        # span. HOTSPOT intentionally renders nothing in this slot: the
        # exhibit images are already shown above, and the JS surfaces a
        # status message via the answer-status element we add right below.
        if q_type == "drag_drop":
            parts.append(render_dragdrop_widget(q, label_text))
        elif q_type == "hotspot":
            # HOTSPOT: no practice widget — the exhibits speak for themselves.
            # Add the answer-status span so the JS can still surface the
            # "no answer available from ExamTopics" message after reveal.
            parts.append('<div class="answer-status answer-status-hotspot" aria-live="polite"></div>')
        else:
            parts.append(render_other_widget(q, label_text))

    if has_correct_answer:
        correct_str = ", ".join(sorted(correct))
        missing_cls = ""
    else:
        correct_str = "Not provided"
        missing_cls = " answer-missing"
    most_voted = q.get("most_voted_answer") or "Not provided"
    parts.append('<div class="answer-shell">')
    parts.append('<div class="answer-locked">')
    parts.append('<div><strong>Answer hidden</strong><br><span>Reveal it only after you commit to your choice.</span></div>')
    parts.append(f'<button class="btn-toggle-answer" type="button" aria-label="Reveal answer for {label_text}">Reveal answer</button>')
    parts.append('</div>')
    parts.append('<div class="answer-revealed">')
    parts.append('<div class="answer-grid">')
    parts.append(f'<div class="answer-card{missing_cls}"><span class="label">Correct answer</span><strong>{html.escape(correct_str)}</strong></div>')
    parts.append(f'<div class="answer-card{missing_cls}"><span class="label">Most voted</span><strong>{html.escape(most_voted)}</strong></div>')
    parts.append('</div>')

    comments = q.get("comments", [])
    if comments:
        parts.append('<details class="comments">')
        parts.append(f'<summary>Top explanations from discussion ({len(comments[:3])})</summary>')
        for c in comments[:3]:
            author = html.escape(c.get("author", "Anonymous"))
            up = c.get("upvotes", 0)
            badges = " ".join(f'<span class="badge">{html.escape(b)}</span>' for b in c.get("badges", []))
            ctext = clean_html(c.get("text", "")).replace("\n", "<br>")
            parts.append('<div class="comment">')
            parts.append(f'<div class="comment-meta">{author} · {up} upvote{"s" if up != 1 else ""} {badges}</div>')
            parts.append(f'<div>{ctext}</div>')
            parts.append('</div>')
        parts.append('</details>')

    parts.append('<div class="answer-tools"><button class="secondary btn-toggle-answer" type="button">Hide answer</button></div>')
    parts.append('</div></div>')

    parts.append('</article>')
    return "\n".join(parts)


def build_html(exam: str, questions: list[dict[str, Any]]) -> str:
    # Sort by topic then question number
    questions = sorted(questions, key=lambda q: (q.get("topic", 0), q.get("question_number", 0)))
    title = f"{exam.upper()} ExamTopics Study Guide"
    stats = f"{len(questions)} questions · generated from ExamTopics discussions"
    CHUNK_SIZE = 25

    def question_anchor(q: dict[str, Any]) -> str:
        exam = html.escape(q.get("exam", "").lower())
        topic = q.get("topic", 0)
        num = q.get("question_number", 0)
        qid = q.get("question_id", "")
        return f"q-{exam}-t{topic}-n{num}-{slug_id(qid)}"

    topic_count = len({q.get("topic", 0) for q in questions})
    lines = [HTML_HEAD.replace("$title", title).replace("$stats", stats)]

    lines.append('<section class="hero" aria-labelledby="hero-title">')
    lines.append('<div class="hero-content">')
    lines.append('<div>')
    lines.append(f'<span class="eyebrow">Focused exam prep</span>')
    lines.append(f'<h2 id="hero-title">Train question by question.</h2>')
    lines.append('<p>One question at a time, scenario context visible, and the live map keeps your place during long study sessions.</p>')
    lines.append('<div class="hero-metrics">')
    lines.append(f'<div class="metric"><strong>{len(questions)}</strong><span>Total questions</span></div>')
    lines.append(f'<div class="metric"><strong>{topic_count}</strong><span>Topics</span></div>')
    lines.append('<div class="metric"><strong id="hero-attempted">0</strong><span>Attempted</span></div>')
    lines.append('<div class="metric"><strong id="hero-correct">0</strong><span>Correct</span></div>')
    lines.append('<div class="metric"><strong id="hero-reviewed">0</strong><span>Reviewed</span></div>')
    lines.append('<div class="metric"><strong id="hero-remaining">0</strong><span>Remaining</span></div>')
    lines.append('</div></div>')
    lines.append('<div id="hero-progress-orb" class="progress-orb" aria-hidden="true"><div class="progress-orb-inner"><div><strong id="hero-pct">0%</strong><span>complete</span></div></div></div>')
    lines.append('</div></section>')

    lines.append('<div class="study-layout">')

    # TOC grouped by topic, chunked for readability
    topic_labels = TOPIC_LABELS.get(exam.lower(), {})
    lines.append('<nav id="study-map" class="study-map" aria-label="Question map">')
    lines.append('<div class="nav-sidebar desktop-only" role="group" aria-label="Step controls">')
    lines.append('<button class="secondary nav-prev-btn" type="button" title="Previous question (←)" aria-label="Previous question">←</button>')
    lines.append('<div class="nav-status" aria-live="polite">Q 1</div>')
    lines.append('<button class="secondary nav-next-btn" type="button" title="Next question (→)" aria-label="Next question">→</button>')
    lines.append('</div>')
    lines.append('<h2>Question map</h2><p class="map-note">Reviewed questions turn green. The current question is highlighted.</p>')
    from itertools import groupby
    for topic, group in groupby(questions, key=lambda q: q.get("topic", 0)):
        group_list = list(group)
        topic_label = topic_labels.get(topic, f"Topic {topic}")
        lines.append(f'<details class="toc-topic" open>')
        lines.append(f'<summary>{html.escape(topic_label)} ({len(group_list)} questions)</summary>')
        for i in range(0, len(group_list), CHUNK_SIZE):
            chunk = group_list[i:i + CHUNK_SIZE]
            first_num = chunk[0].get("question_number", 0)
            last_num = chunk[-1].get("question_number", 0)
            lines.append(f'<details class="toc-chunk" {"open" if i == 0 else ""}>')
            lines.append(f'<summary>Q{topic}.{first_num}–Q{topic}.{last_num}</summary>')
            lines.append('<ul class="toc-links">')
            for q in chunk:
                num = q.get("question_number", 0)
                anchor = question_anchor(q)
                lines.append(f'<li><a href="#{anchor}">Q{topic}.{num}</a></li>')
            lines.append('</ul></details>')
        lines.append('</details>')
    lines.append('</nav>')

    lines.append('<div id="questions" class="question-stack">')

    for i, q in enumerate(questions):
        lines.append(render_question_html(q, is_active=(i == 0)))

    lines.append('</div></div>')

    lines.append(HTML_TAIL)
    return "\n".join(lines)


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
    lines = [
        f"# {exam.upper()} ExamTopics Study Guide",
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
        lines.append(html_to_md(q.get("question_text", "")))
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
                    if rel and local and Path(local).exists():
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
                    code = ex.get("code") or ex.get("text") or ""
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
        most_voted = q.get("most_voted_answer") or "Not provided"
        lines.append(f"**Correct answer:** {correct}")
        lines.append(f"**Most voted:** {most_voted}")
        lines.append("")
        comments = q.get("comments", [])
        if comments:
            lines.append("### Top explanations")
            for c in comments[:3]:
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

    for path_str in args.json_files:
        path = Path(path_str)
        exam = path.stem.lower()
        with path.open("r", encoding="utf-8") as f:
            questions = json.load(f)

        if args.format in ("html", "both"):
            html_out = args.out_dir / f"{exam}-examtopics-study-guide.html"
            html_out.write_text(build_html(exam, questions), encoding="utf-8")
            print(f"Wrote HTML: {html_out}")

        if args.format in ("markdown", "both"):
            md_out = args.out_dir / f"{exam}-examtopics-study-guide.md"
            md_out.write_text(build_markdown(exam, questions), encoding="utf-8")
            print(f"Wrote Markdown: {md_out}")


if __name__ == "__main__":
    main()
