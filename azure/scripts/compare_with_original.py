#!/usr/bin/env python3
"""Compare a crawled question against the live ExamTopics discussion page.

Usage (from repo root):
    python scripts/compare_with_original.py --json data/dp-600.json --discussion-id <id>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup


@dataclass
class Choice:
    letter: str
    text: str
    correct: bool


@dataclass
class Comment:
    comment_id: str
    author: str
    date_title: str
    text: str
    upvotes: int
    badges: list[str] = field(default_factory=list)


@dataclass
class Question:
    discussion_id: str
    question_id: str
    question_text: str
    choices: list[Choice]
    correct_answers: list[str]
    most_voted_answer: str | None
    comments: list[Comment]


def parse_page(html: str) -> Question:
    soup = BeautifulSoup(html, "html.parser")

    q_body = soup.find("div", class_="question-body")
    question_id = str(q_body.get("data-id", "")) if q_body else ""
    question_text = ""
    if q_body:
        p = q_body.find("p", class_="card-text")
        if p:
            question_text = p.get_text(separator="\n", strip=True)

    choices: list[Choice] = []
    correct_answers: list[str] = []
    choices_container = soup.find("div", class_="question-choices-container")
    if choices_container:
        for li in choices_container.find_all("li", class_="multi-choice-item"):
            letter_span = li.find("span", class_="multi-choice-letter")
            letter = str(letter_span.get("data-choice-letter", "")) if letter_span else ""
            text = li.get_text(strip=True)
            text = re.sub(r"^[A-Z]\.\s*", "", text).strip()
            correct = "correct-hidden" in (li.get("class") or [])
            choices.append(Choice(letter=letter, text=text, correct=correct))
            if correct:
                correct_answers.append(letter)

    most_voted: str | None = None
    tally_div = soup.find("div", class_="voted-answers-tally")
    if tally_div:
        script = tally_div.find("script", type="application/json")
        if script:
            try:
                tally = json.loads(script.string or "[]")
                for item in tally:
                    if item.get("is_most_voted"):
                        most_voted = item.get("voted_answers")
                        break
            except json.JSONDecodeError:
                pass

    comments: list[Comment] = []
    for c in soup.find_all("div", class_="comment-container"):
        comment_id = str(c.get("data-comment-id", ""))
        user_el = c.find("h5", class_="comment-username")
        author = user_el.get_text(strip=True) if user_el else ""
        date_el = c.find("span", class_="comment-date")
        date_title = str(date_el.get("title", "")) if date_el else ""
        content_el = c.find("div", class_="comment-content")
        text = content_el.get_text(separator="\n", strip=True) if content_el else ""
        upvote_el = c.find("span", class_="upvote-count")
        upvotes = 0
        if upvote_el:
            try:
                upvotes = int(upvote_el.get_text(strip=True))
            except ValueError:
                pass
        badges = [b.get_text(strip=True) for b in c.find_all("span", class_="badge")]
        comments.append(Comment(comment_id, author, date_title, text, upvotes, badges))

    return Question(
        discussion_id="",
        question_id=question_id,
        question_text=question_text,
        choices=choices,
        correct_answers=correct_answers,
        most_voted_answer=most_voted,
        comments=comments,
    )


def normalize(text: str) -> str:
    return " ".join(text.split())


def compare_fields(name: str, local: Any, remote: Any) -> bool:
    if local != remote:
        print(f"\n❌ {name} mismatch:")
        print(f"   Local:  {local!r}")
        print(f"   Remote: {remote!r}")
        return False
    print(f"✅ {name} matches")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json", help="Exam JSON file")
    parser.add_argument("url", help="ExamTopics discussion URL")
    args = parser.parse_args()

    # Find discussion_id from URL
    m = re.search(r"/view/(\d+)-", args.url)
    if not m:
        print("Could not extract discussion_id from URL")
        sys.exit(1)
    discussion_id = m.group(1)

    with open(args.json, "r", encoding="utf-8") as f:
        questions = json.load(f)

    local_q = next((q for q in questions if str(q.get("discussion_id")) == discussion_id), None)
    if not local_q:
        print(f"Discussion {discussion_id} not found in {args.json}")
        sys.exit(1)

    print(f"Comparing discussion {discussion_id}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = httpx.get(args.url, headers=headers, timeout=30, follow_redirects=True)
    r.raise_for_status()
    remote_q = parse_page(r.text)

    ok = True
    ok &= compare_fields("Question ID", local_q.get("question_id"), remote_q.question_id)
    ok &= compare_fields(
        "Question text (first 200 chars)",
        normalize(local_q.get("question_text", ""))[:200],
        normalize(remote_q.question_text)[:200],
    )

    local_choices = {c["letter"]: normalize(c["text"]) for c in local_q.get("choices", [])}
    remote_choices = {c.letter: normalize(c.text) for c in remote_q.choices}
    ok &= compare_fields("Choices", local_choices, remote_choices)

    ok &= compare_fields("Correct answers", sorted(local_q.get("correct_answers", [])), sorted(remote_q.correct_answers))
    ok &= compare_fields("Most voted answer", local_q.get("most_voted_answer"), remote_q.most_voted_answer)

    local_comments = [(c["author"], c["upvotes"], normalize(c["text"])[:80]) for c in local_q.get("comments", [])[:3]]
    remote_comments = [(c.author, c.upvotes, normalize(c.text)[:80]) for c in remote_q.comments[:3]]
    ok &= compare_fields("Top 3 comments", local_comments, remote_comments)

    print(f"\n{'All checks passed' if ok else 'Some checks failed'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
