#!/usr/bin/env python3
"""
HTML sanitizer for exhibit content (images, tables, code blocks).

The sanitization uses an explicit allowlist of tags and attributes and runs on
``html.parser``/BeautifulSoup. It deliberately does not depend on ``bleach``
so the project has one fewer third-party dep for this small surface area.

Only a handful of tags/attributes are needed for the exam-question exhibits we
care about, but we keep a generous list so future exhibits (figures,
captions, definition lists, details/summary, headings, etc.) render cleanly.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

# Allowed tag names (lowercase, compared against tag.name.lower()).
ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # text
        "p", "br", "hr",
        "strong", "b", "em", "i", "u",
        "sup", "sub",
        "h1", "h2", "h3", "h4", "h5", "h6",
        # inline / block containers
        "div", "span",
        # lists
        "ul", "ol", "li", "dl", "dt", "dd",
        # code
        "code", "pre",
        # tables
        "table", "thead", "tbody", "tfoot",
        "tr", "th", "td",
        "caption", "colgroup", "col",
        # media
        "img", "figure", "figcaption",
        # interactive (read-only)
        "details", "summary",
        # links
        "a",
    }
)

# Tags we explicitly drop wholesale (even if they appear inside an allowed parent).
DROP_TAGS: frozenset[str] = frozenset(
    {"script", "style", "iframe", "form", "input", "button", "object", "embed"}
)

# Attributes allowed on every tag.
COMMON_ALLOWED_ATTRS: frozenset[str] = frozenset({"class"})

# Per-tag extra allowed attributes (merged with COMMON_ALLOWED_ATTRS).
TAG_ATTRS: dict[str, frozenset[str]] = {
    "img": frozenset({"src", "alt", "loading", "width", "height"}),
    "table": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan"}),
    "td": frozenset({"colspan", "rowspan"}),
    "a": frozenset({"href", "title"}),
    "code": frozenset({"class"}),  # class is already in COMMON, but explicit for clarity
}

# Schemes allowed on <a href>.
ALLOWED_URL_SCHEMES: frozenset[str] = frozenset({"http", "https"})


def _is_event_handler(name: str) -> bool:
    """Return True for attributes that are JavaScript event handlers (on*)."""
    return name.startswith("on")


def _safe_url(value: str) -> str | None:
    """Return ``value`` only if it looks like a safe http(s) URL, else None."""
    if not value:
        return None
    v = value.strip()
    if v.startswith("//"):
        # Protocol-relative URL: treat as https to be safe.
        return "https:" + v
    lower = v.lower()
    for scheme in ALLOWED_URL_SCHEMES:
        if lower.startswith(scheme + ":"):
            return v
    # Reject javascript:, data:, vbscript:, file:, mailto:, etc.
    return None


def sanitize_exhibit_html(html: str) -> str:
    """Return a sanitized HTML string safe to embed in study guides.

    Strips disallowed tags, scripts, iframes, and event handlers. Keeps
    formatting/content tags from :data:`ALLOWED_TAGS` and only the attributes
    declared in :data:`TAG_ATTRS` (plus ``class``).
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 1) Drop entire subtrees for clearly dangerous tags.
    for tag in soup.find_all(list(DROP_TAGS)):
        tag.decompose()

    # 2) Walk remaining elements and strip disallowed tags / attributes.
    for tag in soup.find_all(True):
        name = (tag.name or "").lower()
        if not name:
            continue
        if name not in ALLOWED_TAGS:
            # Replace with the element's text content so we don't lose info.
            tag.unwrap()
            continue

        allowed_attrs = COMMON_ALLOWED_ATTRS | TAG_ATTRS.get(name, frozenset())

        new_attrs: dict[str, object] = {}
        for attr, value in list(tag.attrs.items()):
            attr_l = attr.lower()
            if _is_event_handler(attr_l):
                continue
            if attr_l not in allowed_attrs:
                continue
            # Per-attribute value filtering.
            if name == "a" and attr_l == "href":
                safe = _safe_url(str(value))
                if safe is None:
                    continue
                new_attrs[attr_l] = safe
            else:
                # Coerce multi-valued attrs (e.g. class -> list) to string.
                if isinstance(value, list):
                    value = " ".join(str(v) for v in value)
                new_attrs[attr_l] = str(value)

        # Replace attrs wholesale so removed ones don't linger.
        tag.attrs = new_attrs  # type: ignore[assignment]

    return str(soup)


if __name__ == "__main__":
    # Tiny smoke test
    sample = (
        '<p>Hello <script>alert(1)</script> <a href="javascript:alert(1)" '
        'onclick="bad()">link</a> <img src="x.png" onerror="bad()" /></p>'
        '<table><tr><td colspan="2" rowspan="1">cell</td></tr></table>'
    )
    print(sanitize_exhibit_html(sample))