"""Shared, lossless prose anchors for book illustrations.

An asset may declare ``book_placement: {after_paragraph: N}``. Zero means before
the body; positive integers count ordinary prose paragraphs, excluding headings,
lists, block quotes, tables and fenced code. Missing, invalid and stale anchors
fall back to the end of the body. Manuscript text is never rewritten.
"""
from __future__ import annotations

import re


def _prose_spans(body: str) -> list[tuple[int, int]]:
    spans = []
    offset = 0
    start = None
    fenced = False
    for source_line in body.splitlines(keepends=True):
        line = source_line.rstrip("\r\n")
        fence = line.startswith("```")
        prose = not (fenced or fence or not line.strip() or
                     line.startswith(("#", "|", "> ")) or
                     re.match(r"(?:[-*] |\d+\. )", line))
        if prose and start is None:
            start = offset
        elif not prose and start is not None:
            spans.append((start, offset))
            start = None
        if fence:
            fenced = not fenced
        offset += len(source_line)
    if start is not None:
        spans.append((start, len(body)))
    return spans


def prose_paragraphs(body: str) -> list[str]:
    """Return plain paragraph source slices using the book's Markdown subset."""
    return [body[start:end].rstrip("\r\n") for start, end in _prose_spans(body)]


def prose_paragraph_count(body: str) -> int:
    return len(_prose_spans(body))


def body_segments(body: str) -> list[dict]:
    """Split after each prose paragraph, preserving all input text exactly.

    Each numbered segment retains any headings, lists, tables or code before its
    ending paragraph. A trailing nonprose remainder has ``paragraph=None``.
    Concatenating every segment's ``markdown`` reproduces ``body`` unchanged.
    """
    segments = []
    previous = 0
    for number, (_, end) in enumerate(_prose_spans(body), 1):
        segments.append({"paragraph": number, "markdown": body[previous:end]})
        previous = end
    if previous < len(body):
        segments.append({"paragraph": None, "markdown": body[previous:]})
    return segments


def figure_groups(page: dict, assets: dict) -> dict[int | None, list[str]]:
    """Resolve figure anchors, keeping input order inside each anchor group."""
    count = prose_paragraph_count(page.get("body", ""))
    groups = {}
    for key in page.get("figures", []):
        placement = assets.get(key, {}).get("book_placement")
        anchor = placement.get("after_paragraph") if isinstance(placement, dict) else None
        if isinstance(anchor, bool) or not isinstance(anchor, int) or not 0 <= anchor <= count:
            anchor = None
        groups.setdefault(anchor, []).append(key)
    return groups
