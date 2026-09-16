"""Domology's manuscript format: Markdown, plus what a programmatic book needs.

A chapter is one text file. It opens with a short header::

    ---
    id: sphere
    title: The Shape That Encloses the Most
    deck: Why half a sphere is the cheapest wall there is.
    status: draft
    ---

and then ordinary Markdown: blank lines between paragraphs, ``##`` and ``###``
headings, ``- `` and ``1. `` lists, ``>`` for a pull quote, pipe tables,
``*italic*``, ``**bold**`` and ```code```. On top of that:

``{{group.name}}``
    A live number. It is computed when the book is built, from the same code
    that draws the dome. The Numbers list in the editor shows all of them.
``^[a side note]``
    Printed in the outer margin beside its line.
``[[plate: id]]`` / ``[[plate: id | full]]``
    An illustration, rendered by one of the project's tools. Sizes:
    ``column``, ``full``, ``half`` or ``page`` (a full-page plate with bleed).
``[[math: id]]``
    A worked-math box. Every line of it is computed by code.
``[[table: id]]``
    A table generated from code.
``[[pagebreak]]``
    Start a new page.
``:::sidebar Title`` ... ``:::``
    A boxed aside. ``:::steps`` is a numbered procedure (one ``1.`` line per
    step), ``:::safety`` a warning, ``:::pull`` a larger quotation.
``:::author What only you can add`` ... ``:::``
    A request for the author: a date, a memory, a photograph. Drafts print it
    in a yellow box; a final build refuses to run while any remain.
``<!-- ... -->``
    Never printed.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HEADER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
EMBED = re.compile(
    r"^\[\[\s*(plate|math|table|pagebreak)\s*(?::\s*([^|\]]+?))?\s*"
    r"(?:\|\s*([^\]]*?))?\s*\]\]\s*$")
FENCE = re.compile(r"^:::\s*(sidebar|steps|safety|author|pull)\b[ \t]*(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
NUMBERED = re.compile(r"^(\d+)[.)]\s+(.*)$")
TOKEN = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*(?:\.[a-z0-9_]+)+)\s*\}\}")

BOX_KINDS = ("sidebar", "steps", "safety", "author", "pull")


# ----------------------------------------------------------------------
# The parsed shapes
# ----------------------------------------------------------------------

@dataclass
class Span:
    """A run of text in one style. A token span carries the token's name so
    a reader can ask where the number came from."""

    text: str
    style: str = "r"
    token: str | None = None
    note: list | None = None
    """A side note anchored after this span (a list of spans)."""
    link: str | None = None


@dataclass
class Block:
    kind: str
    spans: list = field(default_factory=list)
    items: list = field(default_factory=list)
    children: list = field(default_factory=list)
    title: str = ""
    ref: str = ""
    options: tuple = ()
    line: int = 0
    bid: str = ""

    def plain(self) -> str:
        """The block's words without styling, for search and annotations."""
        parts = [self.title] if self.title else []
        parts.append(spans_text(self.spans))
        for item in self.items:
            if isinstance(item, list):
                if item and isinstance(item[0], list):
                    parts.extend(spans_text(cell) for cell in item)
                else:
                    parts.append(spans_text(item))
        for child in self.children:
            parts.append(child.plain())
        return " ".join(part for part in parts if part).strip()


@dataclass
class Chapter:
    id: str
    title: str
    deck: str
    status: str
    blocks: list
    meta: dict
    path: Path | None = None
    source: str = ""

    @property
    def words(self) -> int:
        return sum(len(block.plain().split()) for block in self.blocks)

    def author_requests(self) -> list[Block]:
        found = []

        def walk(blocks):
            for block in blocks:
                if block.kind == "author":
                    found.append(block)
                walk(block.children)
        walk(self.blocks)
        return found


def spans_text(spans: list) -> str:
    return "".join(span.text for span in spans if isinstance(span, Span))


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------

class Resolver:
    """Turns ``{{group.name}}`` into its current value, and remembers which
    tokens a chapter used so the book can print where each came from."""

    def __init__(self, extra: dict[str, str] | None = None, strict: bool = False):
        self.extra = dict(extra or {})
        self.strict = strict
        self.used: dict[str, str] = {}
        self.missing: list[str] = []

    @staticmethod
    def table() -> dict:
        return token_table()

    def value(self, name: str) -> str:
        if name in self.extra:
            value = self.extra[name]
        else:
            token = token_table().get(name)
            if token is None:
                if self.strict:
                    raise KeyError(f"unknown token {{{{{name}}}}}")
                self.missing.append(name)
                return f"[[{name}?]]"
            value = token_value(name)
        self.used[name] = value
        return value

    def describe(self, name: str) -> str:
        if name in self.extra:
            return "a chapter number in this book"
        token = token_table().get(name)
        return getattr(token, "describe", "") if token else ""


_TABLE: dict | None = None
_VALUES: dict[str, str] = {}


def token_table() -> dict:
    """Every live figure the manuscript may quote, by name."""
    global _TABLE
    if _TABLE is None:
        from two_v_demo import book_tokens
        _TABLE = dict(book_tokens.token_map())
    return _TABLE


def token_value(name: str) -> str:
    if name not in _VALUES:
        _VALUES[name] = str(token_table()[name].compute())
    return _VALUES[name]


def reset_tokens() -> None:
    """Forget computed values, so a live reader picks up changed code."""
    global _TABLE
    _TABLE = None
    _VALUES.clear()


# ----------------------------------------------------------------------
# Inline text
# ----------------------------------------------------------------------

def _style(bold: bool, italic: bool) -> str:
    if bold and italic:
        return "bi"
    if bold:
        return "b"
    if italic:
        return "i"
    return "r"


def smarten(text: str) -> str:
    """Curly quotes, proper dashes and an ellipsis, as a typesetter would."""
    text = text.replace("---", "—").replace("--", "–").replace("...", "…")
    out = []
    for index, char in enumerate(text):
        before = text[index - 1] if index else " "
        if char == '"':
            out.append("“" if before.isspace() or before in "([{—–" else "”")
        elif char == "'":
            out.append("‘" if before.isspace() or before in "([{—–" else "’")
        else:
            out.append(char)
    return "".join(out)


def _matching(text: str, start: int, open_char: str, close_char: str) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == open_char:
            depth += 1
        elif text[index] == close_char:
            depth -= 1
            if depth == 0:
                return index
    return -1


def parse_inline(text: str, resolver: Resolver) -> list[Span]:
    """Spans for one paragraph of Markdown text."""
    spans: list[Span] = []
    buffer: list[str] = []
    bold = italic = False
    index = 0

    def flush() -> None:
        if buffer:
            spans.append(Span(smarten("".join(buffer)), _style(bold, italic)))
            buffer.clear()

    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            buffer.append(text[index + 1])
            index += 2
            continue
        if text.startswith("{{", index):
            end = text.find("}}", index + 2)
            match = TOKEN.match(text, index)
            if end > 0 and match:
                flush()
                name = match.group(1)
                spans.append(Span(resolver.value(name), _style(bold, italic), token=name))
                index = match.end()
                continue
        if text.startswith("^[", index):
            end = _matching(text, index + 1, "[", "]")
            if end > 0:
                flush()
                note = parse_inline(text[index + 2:end], resolver)
                spans.append(Span("", _style(bold, italic), note=note))
                index = end + 1
                continue
        if char == "`":
            end = text.find("`", index + 1)
            if end > 0:
                flush()
                spans.append(Span(text[index + 1:end], "code"))
                index = end + 1
                continue
        if text.startswith("**", index):
            flush()
            bold = not bold
            index += 2
            continue
        if char == "*":
            nxt = text[index + 1] if index + 1 < len(text) else " "
            prev = text[index - 1] if index else " "
            # An asterisk between spaces is a multiplication sign, not emphasis.
            if not (prev.isspace() and nxt.isspace()):
                flush()
                italic = not italic
                index += 1
                continue
        if char == "[":
            close = _matching(text, index, "[", "]")
            if close > 0 and text.startswith("(", close + 1):
                paren = text.find(")", close + 2)
                if paren > 0:
                    flush()
                    label = parse_inline(text[index + 1:close], resolver)
                    url = text[close + 2:paren].strip()
                    for span in label:
                        span.link = url
                    spans.extend(label)
                    index = paren + 1
                    continue
        buffer.append(char)
        index += 1
    flush()
    return spans


# ----------------------------------------------------------------------
# Blocks
# ----------------------------------------------------------------------

def _strip_comments(text: str) -> str:
    """Drop comments but keep the line count, so line numbers stay true."""
    return COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def parse_header(text: str) -> tuple[dict, str, int]:
    match = HEADER.match(text)
    if not match:
        return {}, text, 0
    meta = {}
    for raw in match.group(1).splitlines():
        if ":" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, text[match.end():], match.group(0).count("\n")


def _table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def parse_blocks(lines: list[str], resolver: Resolver, first_line: int = 1) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    paragraph_line = 0
    index = 0

    def end_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            blocks.append(Block("para", parse_inline(text, resolver),
                                line=paragraph_line))
            paragraph = []

    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()
        number = first_line + index
        stripped = line.strip()
        if not stripped:
            end_paragraph()
            index += 1
            continue
        if stripped.startswith("### "):
            end_paragraph()
            blocks.append(Block("h3", parse_inline(stripped[4:], resolver), line=number))
            index += 1
            continue
        if stripped.startswith("## "):
            end_paragraph()
            blocks.append(Block("h2", parse_inline(stripped[3:], resolver), line=number))
            index += 1
            continue
        embed = EMBED.match(stripped)
        if embed:
            end_paragraph()
            kind, ref, options = embed.group(1), (embed.group(2) or "").strip(), embed.group(3)
            opts = tuple(o.strip() for o in (options or "").split(",") if o.strip())
            blocks.append(Block(kind, ref=ref, options=opts, line=number))
            index += 1
            continue
        fence = FENCE.match(stripped)
        if fence:
            end_paragraph()
            kind, title = fence.group(1), fence.group(2).strip()
            inner: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != ":::":
                inner.append(lines[index])
                index += 1
            index += 1  # the closing :::
            children = parse_blocks(inner, resolver, number + 1)
            block = Block(kind, title=smarten(title), children=children, line=number)
            if kind == "steps":
                block.items = [child.items for child in children if child.kind == "numbers"]
            blocks.append(block)
            continue
        if stripped.startswith(">"):
            end_paragraph()
            quote: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip()[1:].strip())
                index += 1
            blocks.append(Block("quote", parse_inline(" ".join(quote), resolver), line=number))
            continue
        if stripped.startswith("|"):
            end_paragraph()
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = _table_row(lines[index])
                if not all(re.fullmatch(r":?-{2,}:?", cell or "--") for cell in row):
                    rows.append(row)
                index += 1
            parsed = [[parse_inline(cell, resolver) for cell in row] for row in rows]
            blocks.append(Block("table", items=parsed, line=number))
            continue
        bullet, numbered = BULLET.match(stripped), NUMBERED.match(stripped)
        if bullet or numbered:
            end_paragraph()
            kind = "bullets" if bullet else "numbers"
            items: list[list[Span]] = []
            current: list[str] = []
            while index < len(lines):
                here = lines[index].rstrip()
                head = here.strip()
                b, n = BULLET.match(head), NUMBERED.match(head)
                starts = (b if kind == "bullets" else n) if head else None
                if starts and (here[:1] not in (" ", "\t") or not current):
                    if current:
                        items.append(parse_inline(" ".join(current), resolver))
                    current = [starts.group(1) if kind == "bullets" else starts.group(2)]
                elif head and here[:1] in (" ", "\t") and current:
                    current.append(head)
                else:
                    break
                index += 1
            if current:
                items.append(parse_inline(" ".join(current), resolver))
            blocks.append(Block(kind, items=items, line=number))
            continue
        if not paragraph:
            paragraph_line = number
        paragraph.append(stripped)
        index += 1
    end_paragraph()
    return blocks


def _assign_ids(blocks: list[Block], prefix: str) -> None:
    for position, block in enumerate(blocks):
        block.bid = f"{prefix}.{position}"
        _assign_ids(block.children, block.bid)


def parse_chapter(text: str, resolver: Resolver, path: Path | None = None,
                  fallback_id: str = "") -> Chapter:
    text = _strip_comments(text.replace("\r\n", "\n"))
    meta, body, header_lines = parse_header(text)
    cid = meta.get("id") or fallback_id or (path.stem if path else "chapter")
    blocks = parse_blocks(body.split("\n"), resolver, header_lines + 1)
    _assign_ids(blocks, cid)
    return Chapter(
        id=cid,
        title=smarten(meta.get("title", cid)),
        deck=smarten(meta.get("deck", "")),
        status=meta.get("status", "draft"),
        blocks=blocks,
        meta=meta,
        path=path,
        source=text,
    )


def parse_file(path: Path, resolver: Resolver) -> Chapter:
    return parse_chapter(Path(path).read_text(encoding="utf-8"), resolver, Path(path))


def block_hash(block: Block) -> str:
    """A short fingerprint of a block's words, for re-finding an annotation
    after the text around it has been edited."""
    return hashlib.sha1(block.plain().encode("utf-8")).hexdigest()[:10]


def validate_markup() -> None:
    resolver = Resolver({"dmch.test": "7"})
    chapter = parse_chapter(
        "---\nid: t\ntitle: Test\n---\n"
        "## Heading\n\nA *dome* has **{{dmch.test}}** parts.^[A note.]\n\n"
        "- one\n- two\n  continued\n\n1. first\n2. second\n\n"
        "> a quote\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        "[[plate: forge-water | full]]\n\n:::sidebar Aside\nInside.\n:::\n\n"
        ":::author Add the date\nWhen did it start?\n:::\n", resolver)
    kinds = [block.kind for block in chapter.blocks]
    assert kinds == ["h2", "para", "bullets", "numbers", "quote", "table", "plate",
                     "sidebar", "author"], kinds
    para = chapter.blocks[1]
    assert any(span.token == "dmch.test" and span.text == "7" for span in para.spans)
    assert any(span.note for span in para.spans)
    assert chapter.blocks[2].items and len(chapter.blocks[2].items) == 2
    assert chapter.blocks[6].ref == "forge-water" and chapter.blocks[6].options == ("full",)
    assert len(chapter.author_requests()) == 1
    assert smarten('"a" -- it\'s') == "“a” – it’s"
