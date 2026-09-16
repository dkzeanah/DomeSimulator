"""The paginator: manuscript blocks in, fixed pages out.

Pages here are not a browser's guess. Every line break, page break and figure
position is decided in this module, with word widths measured from the fonts
the PDF embeds (:mod:`fonts`), and written down as positioned words, rules,
boxes and pictures. The printed PDF, the live reader, the editor and the
reading video all draw those same items, so a page number in the contents is
the page the reader turns to, the KDP spine is computed from a page count that
is final, and a note left on page 112 in the editor points at exactly the
words it was left on.

The rules it keeps:

* books and chapters open on a right-hand page;
* a paragraph never strands a single line at the foot or the head of a page;
* a heading never ends a page -- it takes three lines of text with it;
* a figure or box that does not fit floats to the top of the next page while
  the text keeps filling this one, and never drifts into the next chapter;
* a side note prints in the outer column beside the line that calls it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import config as C
from . import fonts as F
from .markup import Block, Chapter, Span

T = C.TYPE
PT = C.PT_PER_IN
NUMBER_WORDS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE"}


def roman(number: int) -> str:
    table = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
             (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"))
    out = []
    for value, letters in table:
        while number >= value:
            out.append(letters)
            number -= value
    return "".join(out)


# ----------------------------------------------------------------------
# What a page is made of
# ----------------------------------------------------------------------

@dataclass
class Word:
    x: float
    y: float
    text: str
    family: str
    style: str
    size: float
    color: str
    token: str | None = None
    link: str | None = None
    kind: str = "word"


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: str | None = None
    stroke: str | None = None
    sw: float = 0.0
    r: float = 0.0
    dash: str | None = None
    opacity: float = 1.0
    kind: str = "rect"


@dataclass
class Rule:
    x1: float
    y1: float
    x2: float
    y2: float
    color: str = C.RULE
    w: float = 0.6
    dash: str | None = None
    kind: str = "rule"


@dataclass
class Picture:
    x: float
    y: float
    w: float
    h: float
    src: str | None
    plate: str
    fit: str = "contain"
    opacity: float = 1.0
    label: str = ""
    kind: str = "picture"


ITEM_TYPES = {"word": Word, "rect": Rect, "rule": Rule, "picture": Picture}


def shifted(item, dx: float, dy: float):
    """A copy of an item moved by (dx, dy)."""
    if item.kind == "rule":
        return Rule(item.x1 + dx, item.y1 + dy, item.x2 + dx, item.y2 + dy,
                    item.color, item.w, item.dash)
    values = dict(item.__dict__)
    values["x"] += dx
    values["y"] += dy
    return ITEM_TYPES[item.kind](**values)


def item_from_json(data: dict):
    return ITEM_TYPES[data["kind"]](**data)


@dataclass
class Page:
    index: int
    folio: str
    recto: bool
    kind: str
    chapter: str = ""
    head: str = ""
    items: list = field(default_factory=list)
    anchors: dict = field(default_factory=dict)
    """Block id -> [top, bottom] on this page, for the editor and annotations."""
    background: str | None = None
    show_folio: bool = True

    def to_json(self) -> dict:
        return {"index": self.index, "folio": self.folio, "recto": self.recto,
                "kind": self.kind, "chapter": self.chapter,
                "background": self.background, "anchors": self.anchors,
                "items": [dict(item.__dict__) for item in self.items]}

    @classmethod
    def from_json(cls, data: dict) -> "Page":
        page = cls(data["index"], data["folio"], data["recto"], data["kind"],
                   data.get("chapter", ""), background=data.get("background"))
        page.anchors = data.get("anchors", {})
        page.items = [item_from_json(item) for item in data.get("items", [])]
        return page


# ----------------------------------------------------------------------
# What the paginator is given
# ----------------------------------------------------------------------

@dataclass
class PlateInfo:
    id: str
    title: str
    caption: list
    credit: str
    path: Path | None
    aspect: float = 16 / 10
    number: str = ""


@dataclass
class SheetInfo:
    id: str
    title: str
    rows: tuple
    source: str


@dataclass
class BookInfo:
    number: int
    name: str
    promise: str
    plate: str | None = None
    chapters: tuple = ()


@dataclass
class Entry:
    chapter: Chapter
    number: int | None
    book: BookInfo | None
    kind: str = "chapter"
    label: str = ""


@dataclass
class TocLine:
    kind: str
    label: str
    title: str
    folio: str
    page: int
    chapter: str = ""


@dataclass
class Layout:
    pages: list
    toc: list
    plates: dict
    problems: list
    words: int = 0
    numbers: dict | None = None
    """Plate id -> the number the plate was printed under."""

    def to_json(self) -> dict:
        return {"pages": [page.to_json() for page in self.pages],
                "toc": [line.__dict__ for line in self.toc],
                "plates": self.plates, "numbers": self.numbers or {},
                "problems": self.problems, "words": self.words,
                "canvas": [C.TRIM.canvas_w, C.TRIM.canvas_h]}


# ----------------------------------------------------------------------
# Text: styles, words, lines
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class TextStyle:
    family: str
    style: str
    size: float
    leading: float
    color: str


BODY = TextStyle("serif", "r", T.body, T.leading, C.INK)
SMALL = TextStyle("serif", "r", T.small, T.small_leading, C.INK)
BOX = TextStyle("serif", "r", 9.3, 12.8, C.INK)
CAPTION = TextStyle("serif", "r", T.caption, T.caption_leading, C.INK)
MONO = TextStyle("mono", "r", T.mono, T.mono_leading, C.INK)
H2 = TextStyle("sans", "sb", T.h2, 17.0, C.INK)
H3 = TextStyle("sans", "b", T.h3, 14.0, C.LONG)


def combine(base: str, span: str) -> str:
    """The style of a span set inside text that already has a style."""
    if span in ("r", "code"):
        return base
    bold = "b" in base or "b" in span
    italic = "i" in base or "i" in span
    if base == "sb" and not italic:
        return "sb"
    return "bi" if bold and italic else "b" if bold else "i" if italic else "r"


@dataclass
class Part:
    text: str
    family: str
    style: str
    size: float
    color: str
    token: str | None = None
    link: str | None = None
    rise: float = 0.0

    @property
    def width(self) -> float:
        return F.width(self.text, self.family, self.style, self.size)


@dataclass
class Unit:
    """One unbreakable word, possibly in several styles (``*dome*s``)."""

    parts: list
    notes: list = field(default_factory=list)

    @property
    def width(self) -> float:
        return sum(part.width for part in self.parts)


def space_of(style: TextStyle) -> float:
    return F.width(" ", style.family, style.style, style.size)


def make_units(spans: list, base: TextStyle, note_hook=None) -> list[Unit]:
    units: list[Unit] = []
    current: list[Part] = []
    notes: list = []

    def close() -> None:
        nonlocal current, notes
        if current:
            units.append(Unit(current, notes))
        current, notes = [], []

    for span in spans:
        if not isinstance(span, Span):
            continue
        if span.note is not None:
            if note_hook is None:
                continue
            number = note_hook(span.note)
            marker = Part(str(number), "sans", "b", base.size * 0.62, C.SHORT,
                          rise=base.size * 0.36)
            if current or not units:
                current.append(marker)
                notes.append((number, span.note))
            else:
                units[-1].parts.append(marker)
                units[-1].notes.append((number, span.note))
            continue
        family, size = base.family, base.size
        style = combine(base.style, span.style)
        color = C.SHORT if span.link else base.color
        if span.style == "code":
            family, size, style = "mono", base.size * 0.88, "r"
        if span.token:
            current.append(Part(span.text, family, style, size, color, span.token, span.link))
            continue
        for piece in re.split(r"( +)", span.text):
            if not piece:
                continue
            if piece.isspace():
                close()
                continue
            current.append(Part(piece, family, style, size, color, link=span.link))
    close()
    return units


def fill(units: list[Unit], width: float, first_indent: float, space: float):
    """Greedy line filling: (units on the line, natural width) per line."""
    lines = []
    line: list[Unit] = []
    used = first_indent
    for unit in units:
        w = unit.width
        if line and used + space + w > width + 0.01:
            lines.append((line, used))
            line, used = [unit], w
        else:
            used += (space if line else 0.0) + w
            line.append(unit)
    if line:
        lines.append((line, used))
    return lines


def emit_units(items: list, units: list[Unit], x: float, baseline: float, width: float,
               indent: float, justify: bool, space: float) -> None:
    """Place one line's words. Justified lines share out the slack between
    words, unless that would open gaps wider than 2.8 spaces, in which case
    the line is left ragged rather than rivered."""
    natural = sum(unit.width for unit in units) + space * max(0, len(units) - 1)
    gap = space
    if justify and len(units) > 1:
        slack = width - indent - natural
        if slack > 0:
            per = slack / (len(units) - 1)
            if per <= space * 1.8:
                gap = space + per
    cursor = x + indent
    for unit in units:
        position = cursor
        for part in unit.parts:
            items.append(Word(round(position, 2), round(baseline - part.rise, 2), part.text,
                              part.family, part.style, part.size, part.color,
                              part.token, part.link))
            position += part.width
        cursor += unit.width + gap


def wrap_mono(text: str, per_line: int) -> list[str]:
    if len(text) <= per_line:
        return [text]
    pieces, rest = [], text
    while len(rest) > per_line:
        cut = rest.rfind(" ", 0, per_line)
        if cut < per_line * 0.5:
            cut = per_line
        pieces.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
        per_line_next = per_line - 2
        per_line = max(10, per_line_next)
    if rest:
        pieces.append(rest)
    return pieces


@dataclass
class Measured:
    """A block drawn at the origin, waiting to be put on a page."""

    items: list
    height: float
    width: float
    kind: str
    bid: str
    x_mode: str = "main"
    plate: PlateInfo | None = None
    plate_id: str = ""


BOX_LOOK = {
    "sidebar": (C.SIDEBAR_TINT, None, None, "ASIDE", C.LONG),
    "safety": (C.SAFETY_TINT, None, C.SAFETY, "SAFETY", C.SAFETY),
    "author": (C.AUTHOR_TINT, C.AUTHOR_EDGE, None, "FOR THE AUTHOR", "#7d6300"),
    "steps": (None, C.RULE, C.LONG, "PROCEDURE", C.LONG),
}


# ----------------------------------------------------------------------
# The composer
# ----------------------------------------------------------------------

class Composer:
    def __init__(self, plates: Callable[[str], PlateInfo | None],
                 sheets: Callable[[str], SheetInfo | None],
                 tables: Callable[[str], tuple | None] | None = None,
                 folio: Callable[[int], str] = lambda index: str(index + 1)):
        self.trim, self.grid = C.TRIM, C.GRID
        self.plates, self.sheets = plates, sheets
        self.tables = tables or (lambda key: None)
        self.folio_of = folio
        self.pages: list[Page] = []
        self.toc: list[TocLine] = []
        self.plate_folios: dict[str, str] = {}
        self.plate_numbers: dict[str, str] = {}
        self.problems: list[str] = []
        self.floats: list[Measured] = []
        self.page: Page | None = None
        self.cursor = 0.0
        self.note_floor = 0.0
        self.notes = 0
        self.entry: Entry | None = None
        self.plate_count = 0
        self.after_heading = True
        self.words = 0
        self.space = space_of(BODY)

    # -- geometry -----------------------------------------------------------
    @property
    def top(self) -> float:
        return self.trim.y0 + self.grid.top

    @property
    def bottom(self) -> float:
        return self.trim.y0 + self.trim.height - self.grid.bottom

    @property
    def main_w(self) -> float:
        g = self.grid
        return self.trim.width - g.inside - g.outside - g.side - g.gap

    @property
    def block_w(self) -> float:
        return self.trim.width - self.grid.inside - self.grid.outside

    def block_x(self, recto: bool) -> float:
        return self.trim.x0(recto) + (self.grid.inside if recto else self.grid.outside)

    def main_x(self, recto: bool) -> float:
        if recto:
            return self.block_x(recto)
        return self.block_x(recto) + self.grid.side + self.grid.gap

    def side_x(self, recto: bool) -> float:
        if recto:
            return self.main_x(recto) + self.main_w + self.grid.gap
        return self.block_x(recto)

    # -- pages --------------------------------------------------------------
    def head_text(self, recto: bool) -> str:
        entry = self.entry
        if entry is None:
            return ""
        if recto:
            return entry.chapter.title
        if entry.book is not None:
            return (f"{C.TITLE} · Book {NUMBER_WORDS[entry.book.number].title()} "
                    f"· {entry.book.name}")
        return C.TITLE

    def new_page(self, kind: str = "text", show_folio: bool = True,
                 background: str | None = None) -> Page:
        if self.page is not None:
            self.finish(self.page)
        index = len(self.pages)
        recto = index % 2 == 0
        page = Page(index, self.folio_of(index), recto, kind,
                    chapter=self.entry.chapter.id if self.entry else "",
                    head=self.head_text(recto), background=background,
                    show_folio=show_folio)
        self.pages.append(page)
        self.page = page
        self.cursor = self.top
        self.note_floor = self.top
        return page

    def start_recto(self, kind: str, **options) -> Page:
        if len(self.pages) % 2 == 1:
            self.new_page("blank", show_folio=False)
        return self.new_page(kind, **options)

    def next_page(self) -> None:
        while self.floats and self.floats[0].kind == "page_plate":
            self.plate_page(self.floats.pop(0).plate)
        self.new_page("text")
        self.place_floats()

    def close(self) -> None:
        if self.page is not None:
            self.finish(self.page)
            self.page = None

    def finish(self, page: Page) -> None:
        """Running head and folio."""
        if page.kind in ("part", "plate", "blank") or not page.show_folio:
            return
        left = self.block_x(page.recto)
        right = left + self.block_w
        folio_y = self.trim.y0 + self.trim.height - 0.5 * PT
        width = F.width(page.folio, "sans", "r", T.folio)
        page.items.append(Word(right - width if page.recto else left, folio_y, page.folio,
                               "sans", "r", T.folio, C.MUTED))
        if page.kind in ("opener", "toc", "front") or not page.head:
            return
        head = page.head.upper()
        head_y = self.trim.y0 + 0.46 * PT
        width = F.width(head, "sans", "sb", T.head)
        page.items.append(Word(right - width if page.recto else left, head_y, head,
                               "sans", "sb", T.head, C.MUTED))
        page.items.append(Rule(left, head_y + 5.5, right, head_y + 5.5, C.RULE, 0.35))

    def anchor(self, bid: str, top: float, bottom: float) -> None:
        if not bid or self.page is None:
            return
        span = self.page.anchors.get(bid)
        if span:
            span[0], span[1] = min(span[0], top), max(span[1], bottom)
        else:
            self.page.anchors[bid] = [round(top, 1), round(bottom, 1)]

    def in_text(self) -> bool:
        return self.page is not None and self.page.kind in ("text", "opener")

    # -- floats -------------------------------------------------------------
    def fits(self, height: float) -> bool:
        gap = 0.0 if self.cursor <= self.top + 0.5 else BODY.leading * 0.55
        return self.cursor + gap + height <= self.bottom + 0.5

    def put(self, m: Measured) -> None:
        gap = 0.0 if self.cursor <= self.top + 0.5 else BODY.leading * 0.55
        y = self.cursor + gap
        recto = self.page.recto
        x = self.main_x(recto) if m.x_mode == "main" else self.block_x(recto)
        for item in m.items:
            self.page.items.append(shifted(item, x, y))
        self.anchor(m.bid, y, y + m.height)
        self.cursor = y + m.height + BODY.leading * 0.55
        if m.plate_id:
            self.plate_folios[m.plate_id] = self.page.folio
        if m.height > self.bottom - self.top + 1:
            self.problems.append(f"{m.bid}: this {m.kind} is taller than a page")

    def place_floats(self) -> None:
        while self.floats:
            m = self.floats[0]
            if m.kind == "page_plate":
                return
            if self.fits(m.height) or self.cursor <= self.top + 0.5:
                self.put(self.floats.pop(0))
            else:
                return

    def place_float(self, m: Measured) -> None:
        if not self.in_text():
            self.next_page()
        if m.kind == "page_plate":
            self.floats.append(m)
            return
        if not self.floats and (self.fits(m.height) or self.cursor <= self.top + 0.5):
            self.put(m)
        else:
            self.floats.append(m)

    def place_atomic(self, m: Measured) -> None:
        if not self.in_text():
            self.next_page()
        if not self.fits(m.height) and self.cursor > self.top + 0.5:
            self.next_page()
        self.put(m)

    def flush_floats(self) -> None:
        guard = 0
        while self.floats and guard < 400:
            self.next_page()
            guard += 1

    # -- running text -------------------------------------------------------
    def note_hook(self, spans: list) -> int:
        self.notes += 1
        return self.notes

    def flow(self, lines, style: TextStyle, first_indent: float, justify: bool,
             bid: str, x_off: float = 0.0, width: float | None = None,
             marker=None) -> None:
        width = width or self.main_w
        space = space_of(style)
        total = len(lines)
        index = 0
        while index < total:
            if not self.in_text():
                self.next_page()
            available = int((self.bottom - self.cursor + 0.5) // style.leading)
            if available <= 0:
                self.next_page()
                continue
            remaining = total - index
            take = min(available, remaining)
            if take < remaining:
                if index == 0 and take == 1 and total > 1:
                    self.next_page()
                    continue
                if remaining - take == 1 and take >= 3:
                    take -= 1
            top = self.cursor
            x = self.main_x(self.page.recto) + x_off
            offset = F.baseline_offset(style.family, style.style, style.size, style.leading)
            for line_index in range(index, index + take):
                units, _natural = lines[line_index]
                baseline = self.cursor + offset
                if line_index == 0 and marker is not None:
                    marker(self.page, self.main_x(self.page.recto), baseline)
                last = line_index == total - 1
                emit_units(self.page.items, units, x, baseline, width,
                           first_indent if line_index == 0 else 0.0,
                           justify and not last, space)
                for unit in units:
                    for number, spans in unit.notes:
                        self.side_note(number, spans, self.cursor)
                self.cursor += style.leading
            self.anchor(bid, top, self.cursor)
            index += take
            if index < total:
                self.next_page()

    def side_note(self, number: int, spans: list, line_top: float) -> None:
        recto = self.page.recto
        x, width = self.side_x(recto), self.grid.side
        units = [Unit([Part(str(number), "sans", "b", SMALL.size, C.SHORT)])]
        units += make_units(spans, SMALL)
        lines = fill(units, width, 0.0, space_of(SMALL))
        height = len(lines) * SMALL.leading
        y = max(line_top, self.note_floor + 2.0)
        if y + height > self.bottom:
            y = max(self.note_floor + 2.0, self.bottom - height)
        offset = F.baseline_offset("serif", "r", SMALL.size, SMALL.leading)
        for units_line, _natural in lines:
            emit_units(self.page.items, units_line, x, y + offset, width, 0.0, False,
                       space_of(SMALL))
            y += SMALL.leading
        self.note_floor = y + 3.0

    def paragraph(self, block: Block) -> None:
        indent = 0.0 if self.after_heading else BODY.size * 1.25
        units = make_units(block.spans, BODY, self.note_hook)
        if not units:
            return
        self.words += len(units)
        self.flow(fill(units, self.main_w, indent, self.space), BODY, indent, True, block.bid)

    def heading(self, block: Block) -> None:
        style = H2 if block.kind == "h2" else H3
        before = BODY.leading * (1.0 if block.kind == "h2" else 0.55)
        after = BODY.leading * (0.3 if block.kind == "h2" else 0.12)
        lines = fill(make_units(block.spans, style), self.main_w, 0.0, space_of(style))
        need = before + len(lines) * style.leading + after + BODY.leading * 3
        if not self.in_text() or self.cursor + need > self.bottom:
            self.next_page()
        if self.cursor <= self.top + 0.5:
            before = 0.0
        self.cursor += before
        top = self.cursor
        x = self.main_x(self.page.recto)
        offset = F.baseline_offset(style.family, style.style, style.size, style.leading)
        for units, _natural in lines:
            emit_units(self.page.items, units, x, self.cursor + offset, self.main_w, 0.0,
                       False, space_of(style))
            self.cursor += style.leading
        self.cursor += after
        self.anchor(block.bid, top, self.cursor)

    def list_block(self, block: Block) -> None:
        numbered = block.kind == "numbers"
        hang = 17.0 if numbered else 13.0
        for number, item in enumerate(block.items, 1):
            units = make_units(item, BODY, self.note_hook)
            if not units:
                continue
            self.words += len(units)
            lines = fill(units, self.main_w - hang, 0.0, self.space)

            def marker(page, x, baseline, n=number):
                if numbered:
                    page.items.append(Word(x, baseline, f"{n}.", "sans", "sb",
                                           BODY.size * 0.9, C.SHORT))
                else:
                    page.items.append(Word(x + 2.0, baseline, "•", "serif", "r",
                                           BODY.size, C.LONG))
            self.flow(lines, BODY, 0.0, False, block.bid, x_off=hang,
                      width=self.main_w - hang, marker=marker)
            self.cursor += BODY.leading * 0.1
        self.cursor += BODY.leading * 0.3

    # -- blocks drawn at the origin ------------------------------------------
    def text_block(self, spans: list, style: TextStyle, width: float,
                   justify: bool = False, indent: float = 0.0):
        units = make_units(spans, style)
        lines = fill(units, width, indent, space_of(style))
        items: list = []
        y = 0.0
        offset = F.baseline_offset(style.family, style.style, style.size, style.leading)
        for index, (units_line, _natural) in enumerate(lines):
            emit_units(items, units_line, 0.0, y + offset, width,
                       indent if index == 0 else 0.0,
                       justify and index < len(lines) - 1, space_of(style))
            y += style.leading
        return items, y

    def list_items(self, block: Block, width: float, style: TextStyle = BOX):
        items: list = []
        y = 0.0
        numbered = block.kind == "numbers"
        hang = 15.0 if numbered else 11.0
        offset = F.baseline_offset(style.family, style.style, style.size, style.leading)
        for number, item in enumerate(block.items, 1):
            part, height = self.text_block(item, style, width - hang)
            items.append(Word(0.0, y + offset, f"{number}." if numbered else "•",
                              "sans" if numbered else "serif", "sb" if numbered else "r",
                              style.size * 0.92, C.SHORT if numbered else C.LONG))
            items += [shifted(i, hang, y) for i in part]
            y += height + style.leading * 0.15
        return items, y

    def child_blocks(self, children: list, width: float, style: TextStyle = BOX):
        items: list = []
        y = 0.0
        for child in children:
            if child.kind == "para":
                part, height = self.text_block(child.spans, style, width, justify=True)
            elif child.kind in ("bullets", "numbers"):
                part, height = self.list_items(child, width, style)
            elif child.kind in ("h2", "h3"):
                part, height = self.text_block(
                    child.spans, TextStyle("sans", "sb", 9.4, 12.8, C.INK), width)
            elif child.kind == "quote":
                part, height = self.text_block(
                    child.spans, TextStyle("serif", "i", style.size, style.leading, C.MUTED), width)
            else:
                part, height = [], 0.0
            items += [shifted(i, 0.0, y) for i in part]
            y += height + style.leading * 0.35
        return items, max(0.0, y - style.leading * 0.35)

    def measure_box(self, block: Block) -> Measured:
        kind = block.kind
        if kind == "math":
            return self.measure_math(block)
        if kind == "table":
            return self.measure_table(block)
        if kind in ("pull", "quote"):
            return self.measure_pull(block)
        fill_colour, stroke, bar, eyebrow, eyebrow_colour = BOX_LOOK[kind]
        width = self.main_w
        pad = 9.0
        inset = pad + (4.0 if bar else 0.0)
        inner = width - inset - pad
        items: list = []
        y = pad
        label = eyebrow + (f" · {block.title.upper()}" if block.title else "")
        part, height = self.text_block([Span(label)],
                                       TextStyle("sans", "b", 6.9, 10.0, eyebrow_colour), inner)
        items += [shifted(i, inset, y) for i in part]
        y += height + 3.0
        style = TextStyle("serif", "i", BOX.size, BOX.leading, C.INK) if kind == "author" else BOX
        if kind == "steps":
            steps = [item for numbers in block.items for item in numbers]
            for number, step in enumerate(steps, 1):
                part, height = self.text_block(step, BOX, inner - 20.0)
                items.append(Rect(inset, y + 1.0, 12.5, 12.5, fill=C.LONG, r=6.25))
                label = str(number)
                label_w = F.width(label, "sans", "b", 7.2)
                items.append(Word(inset + 6.25 - label_w / 2, y + 10.1, label, "sans", "b",
                                  7.2, "#ffffff"))
                items += [shifted(i, inset + 20.0, y) for i in part]
                y += max(height, 14.0) + 4.0
            others = [child for child in block.children if child.kind != "numbers"]
            if others:
                part, height = self.child_blocks(others, inner, style)
                items += [shifted(i, inset, y) for i in part]
                y += height
        else:
            part, height = self.child_blocks(block.children, inner, style)
            items += [shifted(i, inset, y) for i in part]
            y += height
        y += pad
        back = [Rect(0.0, 0.0, width, y, fill=fill_colour, stroke=stroke,
                     sw=0.8 if stroke else 0.0, r=3.0,
                     dash="3 2" if kind == "author" else None)]
        if bar:
            back.append(Rect(0.0, 0.0, 3.2, y, fill=bar))
        return Measured(back + items, y, width, kind, block.bid, "main")

    def measure_math(self, block: Block) -> Measured:
        info = self.sheets(block.ref)
        width = self.block_w
        if info is None:
            self.problems.append(f"{block.bid}: unknown math sheet '{block.ref}'")
            return self.missing(block, width, f"math sheet '{block.ref}' is not defined")
        pad = 9.0
        inner = width - 2 * pad
        items: list = []
        y = pad
        part, height = self.text_block([Span("WORKED MATH")],
                                       TextStyle("sans", "b", 6.9, 10.0, C.SHORT), inner)
        items += [shifted(i, pad, y) for i in part]
        y += height
        part, height = self.text_block([Span(info.title)],
                                       TextStyle("sans", "sb", 10.0, 13.6, C.INK), inner)
        items += [shifted(i, pad, y) for i in part]
        y += height + 3.0
        rows = list(info.rows)
        conclusion = rows.pop() if len(rows) > 1 else ""
        char = F.width("0", "mono", "r", MONO.size)
        per_line = max(24, int(inner // char))
        offset = F.baseline_offset("mono", "r", MONO.size, MONO.leading)
        for row in rows:
            for index, piece in enumerate(wrap_mono(row, per_line)):
                items.append(Word(pad + (2 * char if index else 0.0), y + offset, piece,
                                  "mono", "r", MONO.size, C.INK))
                y += MONO.leading
        y += 4.0
        if conclusion:
            part, height = self.text_block([Span(conclusion)],
                                           TextStyle("sans", "sb", 8.6, 11.6, C.INK), inner - 12)
            items.append(Rect(pad - 3.0, y - 2.0, inner + 6.0, height + 8.0,
                              fill=C.CONCLUSION_TINT, r=2.0))
            items += [shifted(i, pad + 3.0, y + 2.0) for i in part]
            y += height + 11.0
        part, height = self.text_block(
            [Span(f"Computed by {info.source}. Every line above is printed by that "
                  "code when the book is built; none of it is typed.")],
            TextStyle("sans", "r", 6.3, 8.6, C.MUTED), inner)
        items += [shifted(i, pad, y) for i in part]
        y += height + pad - 2.0
        return Measured([Rect(0.0, 0.0, width, y, fill=C.MATH_TINT, r=3.0)] + items,
                        y, width, "math", block.bid, "block")

    def measure_table(self, block: Block) -> Measured:
        rows = block.items
        if block.ref:
            generated = self.tables(block.ref)
            if generated is None:
                self.problems.append(f"{block.bid}: unknown table '{block.ref}'")
                return self.missing(block, self.main_w, f"table '{block.ref}' is not defined")
            rows = [[[Span(str(cell))] for cell in row] for row in generated]
        if not rows:
            return self.missing(block, self.main_w, "empty table")
        columns = max(len(row) for row in rows)
        width = self.main_w if columns <= 3 else self.block_w
        pad = 4.0
        head = TextStyle("sans", "sb", 7.6, 10.4, C.INK)
        cell = TextStyle("serif", "r", 8.6, 11.4, C.INK)
        natural = [36.0] * columns
        for number, row in enumerate(rows):
            style = head if number == 0 else cell
            for index, spans in enumerate(row):
                text = "".join(s.text for s in spans if isinstance(s, Span))
                natural[index] = max(natural[index],
                                     F.width(text, style.family, style.style, style.size) + 2 * pad)
        capped = [min(value, width * 0.6) for value in natural]
        scale = width / sum(capped)
        widths = [value * scale for value in capped]
        items: list = []
        y = 0.0
        for number, row in enumerate(rows):
            style = head if number == 0 else cell
            parts, height = [], 0.0
            x = 0.0
            for index in range(columns):
                spans = row[index] if index < len(row) else []
                part, h = self.text_block(spans, style, widths[index] - 2 * pad)
                parts.append((x + pad, part))
                height = max(height, h)
                x += widths[index]
            height += 2 * pad
            if number == 0:
                items.append(Rect(0.0, y, width, height, fill=C.SIDEBAR_TINT))
            for x_cell, part in parts:
                items += [shifted(i, x_cell, y + pad) for i in part]
            y += height
            items.append(Rule(0.0, y, width, y, C.RULE, 0.5))
        return Measured(items, y, width, "table", block.bid,
                        "main" if width == self.main_w else "block")

    def measure_pull(self, block: Block) -> Measured:
        style = TextStyle("serif", "i", T.pull, 17.6, C.SHORT)
        if block.kind == "quote":
            spans = block.spans
        else:
            spans = [span for child in block.children for span in child.spans]
        part, height = self.text_block(spans, style, self.main_w - 16.0)
        items = [Rule(1.0, 3.0, 1.0, height + 1.0, C.SHORT, 2.2)]
        items += [shifted(i, 16.0, 0.0) for i in part]
        y = height + 2.0
        if block.kind == "pull" and block.title:
            part, h = self.text_block([Span("— " + block.title)],
                                      TextStyle("sans", "r", 7.6, 10.0, C.MUTED),
                                      self.main_w - 16.0)
            items += [shifted(i, 16.0, y + 2.0) for i in part]
            y += h + 4.0
        return Measured(items, y, self.main_w, "quote", block.bid, "main")

    def missing(self, block: Block, width: float, text: str) -> Measured:
        part, height = self.text_block([Span(text)], TextStyle("sans", "b", 8.0, 11.0, C.SAFETY), width - 16)
        items = [Rect(0.0, 0.0, width, height + 16, stroke=C.SAFETY, sw=0.8, dash="3 2")]
        items += [shifted(i, 8.0, 8.0) for i in part]
        return Measured(items, height + 16, width, "missing", block.bid, "main")

    # -- plates ---------------------------------------------------------------
    def plate_number(self) -> str:
        self.plate_count += 1
        if self.entry is not None and self.entry.number is not None:
            return f"{self.entry.number}.{self.plate_count}"
        return str(self.plate_count)

    def measure_plate(self, info: PlateInfo, size: str, bid: str) -> Measured:
        self.plate_numbers[info.id] = info.number
        width = self.block_w if size in ("full", "opener") else self.main_w
        limit = {"half": 0.40, "opener": 0.30}.get(size, 0.64)
        max_h = (self.bottom - self.top) * limit
        img_w = width
        img_h = width / max(0.2, info.aspect)
        if img_h > max_h:
            img_h, img_w = max_h, max_h * info.aspect
        items: list = [Picture((width - img_w) / 2, 0.0, img_w, img_h,
                               str(info.path) if info.path else None, info.id, "contain",
                               label=info.title)]
        if info.path is None:
            self.problems.append(f"{bid}: plate '{info.id}' has not been rendered yet")
        y = img_h + 6.0
        label = [Unit([Part(f"PLATE {info.number}", "sans", "b", 6.8, C.LONG)])]
        label += make_units([Span(info.title)], TextStyle("sans", "sb", 8.6, 11.2, C.INK))
        head = TextStyle("sans", "sb", 8.6, 11.2, C.INK)
        offset = F.baseline_offset("sans", "sb", 8.6, 11.2)
        for units, _natural in fill(label, width, 0.0, space_of(head) * 1.6):
            emit_units(items, units, 0.0, y + offset, width, 0.0, False, space_of(head) * 1.6)
            y += head.leading
        if info.caption:
            part, height = self.text_block(info.caption, CAPTION, width, justify=True)
            items += [shifted(i, 0.0, y + 1.0) for i in part]
            y += height + 1.0
        if info.credit:
            part, height = self.text_block([Span(info.credit)],
                                           TextStyle("sans", "r", 6.4, 8.6, C.MUTED), width)
            items += [shifted(i, 0.0, y + 1.5) for i in part]
            y += height + 1.5
        return Measured(items, y, width, "plate", bid,
                        "block" if size in ("full", "opener") else "main", plate_id=info.id)

    def plate_block(self, block: Block) -> None:
        info = self.plates(block.ref)
        size = block.options[0] if block.options else "full"
        if info is None:
            self.problems.append(f"{block.bid}: unknown plate '{block.ref}'")
            info = PlateInfo(block.ref, block.ref, [], "not in the plate catalogue", None)
        info.number = self.plate_number()
        if size == "page":
            if not self.in_text():
                self.next_page()
            self.floats.append(Measured([], 0.0, 0.0, "page_plate", block.bid, plate=info,
                                        plate_id=info.id))
            return
        self.place_float(self.measure_plate(info, size, block.bid))

    def plate_page(self, info: PlateInfo) -> None:
        self.plate_numbers[info.id] = info.number
        page = self.new_page("plate", show_folio=False, background=C.NIGHT)
        width, height = self.trim.canvas_w, self.trim.canvas_h
        page.items.append(Rect(0.0, 0.0, width, height, fill=C.NIGHT))
        page.items.append(Picture(0.0, 0.0, width, height,
                                  str(info.path) if info.path else None, info.id, "cover",
                                  label=info.title))
        inner = self.block_w - 24.0
        x = self.block_x(page.recto)
        parts: list = []
        y = 0.0
        part, h = self.text_block([Span(f"PLATE {info.number}")],
                                  TextStyle("sans", "b", 6.8, 9.6, C.LONG), inner)
        parts += [shifted(i, 0.0, y) for i in part]
        y += h
        part, h = self.text_block([Span(info.title)],
                                  TextStyle("sans", "sb", 10.0, 13.0, "#ffffff"), inner)
        parts += [shifted(i, 0.0, y) for i in part]
        y += h + 2.0
        if info.caption:
            part, h = self.text_block(info.caption, TextStyle("serif", "r", 8.4, 11.0, "#d8e0e8"),
                                      inner, justify=True)
            parts += [shifted(i, 0.0, y) for i in part]
            y += h
        panel_y = self.bottom - y - 12.0
        page.items.append(Rect(x, panel_y, self.block_w, y + 20.0, fill="#0b1422",
                               opacity=0.86, r=3.0))
        page.items += [shifted(i, x + 12.0, panel_y + 10.0) for i in parts]
        self.plate_folios[info.id] = page.folio

    # -- structure -----------------------------------------------------------
    def block(self, block: Block) -> None:
        kind = block.kind
        if kind == "para":
            self.paragraph(block)
        elif kind in ("h2", "h3"):
            self.heading(block)
        elif kind in ("bullets", "numbers"):
            self.list_block(block)
        elif kind in ("quote", "pull"):
            self.place_atomic(self.measure_pull(block))
        elif kind == "pagebreak":
            self.next_page()
        elif kind == "plate":
            self.plate_block(block)
        elif kind in ("math", "table", "sidebar", "steps", "safety", "author"):
            self.place_float(self.measure_box(block))
        self.after_heading = kind in ("h2", "h3")

    def chapter(self, entry: Entry) -> None:
        self.flush_floats()
        self.entry = entry
        self.notes = 0
        self.plate_count = 0
        self.opener(entry)
        self.after_heading = True
        for block in entry.chapter.blocks:
            self.block(block)
        self.flush_floats()

    def opener(self, entry: Entry) -> None:
        page = self.start_recto("opener")
        page.chapter = entry.chapter.id
        x = self.block_x(page.recto)
        y = self.trim.y0 + 1.35 * PT
        top = y - 12.0
        if entry.label:
            kicker = entry.label
        elif entry.book is not None:
            kicker = f"BOOK {NUMBER_WORDS[entry.book.number]} · {entry.book.name.upper()}"
        else:
            kicker = ""
        if kicker:
            page.items.append(Word(x, y, kicker, "sans", "b", 7.2, C.LONG))
            y += 14.0
        if entry.number is not None:
            y += T.chapter_number * 0.80
            page.items.append(Word(x - 2.0, y, str(entry.number), "serif", "r",
                                   T.chapter_number, C.LONG))
            y += 16.0
        part, height = self.text_block([Span(entry.chapter.title)],
                                       TextStyle("sans", "sb", T.chapter_title,
                                                 T.chapter_title * 1.16, C.INK),
                                       self.block_w * 0.86)
        page.items += [shifted(i, x, y) for i in part]
        y += height + 6.0
        if entry.chapter.deck:
            part, height = self.text_block([Span(entry.chapter.deck, "i")],
                                           TextStyle("serif", "i", T.deck, T.deck * 1.34, C.MUTED),
                                           self.block_w * 0.8)
            page.items += [shifted(i, x, y) for i in part]
            y += height + 8.0
        page.items.append(Rule(x, y, x + 1.1 * PT, y, C.SHORT, 1.4))
        y += 18.0
        opener_plate = entry.chapter.meta.get("opener")
        if opener_plate:
            info = self.plates(opener_plate)
            if info is None:
                self.problems.append(f"{entry.chapter.id}: unknown opener plate '{opener_plate}'")
            else:
                info.number = self.plate_number()
                m = self.measure_plate(info, "opener", f"{entry.chapter.id}.opener")
                for item in m.items:
                    page.items.append(shifted(item, x, y))
                self.plate_folios[info.id] = page.folio
                y += m.height + 12.0
        self.cursor = y
        self.anchor(f"{entry.chapter.id}.title", top, y)
        self.toc.append(TocLine(entry.kind, "" if entry.number is None else str(entry.number),
                                entry.chapter.title, page.folio, page.index, entry.chapter.id))

    def book_divider(self, book: BookInfo) -> None:
        self.flush_floats()
        self.entry = None
        page = self.start_recto("part", show_folio=False, background=C.NIGHT)
        width, height = self.trim.canvas_w, self.trim.canvas_h
        page.items.append(Rect(0.0, 0.0, width, height, fill=C.NIGHT))
        if book.plate:
            info = self.plates(book.plate)
            if info is not None and info.path is not None:
                page.items.append(Picture(0.0, 0.0, width, height, str(info.path), info.id,
                                          "cover", opacity=0.5))
        x = self.trim.x0(page.recto) + 0.85 * PT
        y = self.trim.y0 + 5.0 * PT
        page.items.append(Word(x, y, f"BOOK {NUMBER_WORDS[book.number]}", "sans", "b", 11.0, C.LONG))
        y += 60.0
        page.items.append(Word(x - 2.0, y, book.name, "serif", "r", 54.0, "#ffffff"))
        y += 26.0
        part, h = self.text_block([Span(book.promise, "i")],
                                  TextStyle("serif", "i", 15.0, 20.0, "#d5dde6"), 5.6 * PT)
        page.items += [shifted(i, x, y) for i in part]
        y += h + 22.0
        for number, title in book.chapters:
            page.items.append(Word(x, y, str(number), "sans", "sb", 9.0, C.LONG))
            page.items.append(Word(x + 24.0, y, title, "sans", "r", 9.0, "#aebfcf"))
            y += 14.5
        self.toc.append(TocLine("book", f"BOOK {NUMBER_WORDS[book.number]}", book.name,
                                page.folio, page.index))


# ----------------------------------------------------------------------
# Front matter
# ----------------------------------------------------------------------

def _centred(page: Page, text: str, left: float, width: float, y: float,
             family: str, style: str, size: float, colour: str) -> None:
    w = F.width(text, family, style, size)
    page.items.append(Word(left + (width - w) / 2, y, text, family, style, size, colour))


def front_matter(c: Composer, meta: dict, toc: list[TocLine], entries: list[Entry]) -> None:
    trim = c.trim
    # i -- half title
    page = c.new_page("front", show_folio=False)
    x, w = c.block_x(page.recto), c.block_w
    _centred(page, C.TITLE.upper(), x, w, trim.y0 + 3.3 * PT, "sans", "b", 22.0, C.INK)
    _centred(page, C.TAGLINE.upper(), x, w, trim.y0 + 3.3 * PT + 22, "sans", "b", 8.0, C.LONG)
    # ii -- frontispiece
    frontis = c.plates(meta.get("frontispiece", "")) if meta.get("frontispiece") else None
    if frontis is not None:
        frontis.number = "i"
        c.plate_page(frontis)
    else:
        c.new_page("blank", show_folio=False)
    # iii -- title page
    page = c.new_page("front", show_folio=False)
    x = c.block_x(page.recto)
    y = trim.y0 + 2.5 * PT
    page.items.append(Word(x - 3.0, y, C.TITLE, "serif", "r", 62.0, C.INK))
    y += 26.0
    part, h = c.text_block([Span(C.SUBTITLE, "i")],
                           TextStyle("serif", "i", 16.0, 21.0, C.MUTED), c.block_w * 0.85)
    page.items += [shifted(i, x, y) for i in part]
    y += h + 18.0
    page.items.append(Word(x, y, C.TAGLINE.upper(), "sans", "b", 8.4, C.LONG))
    y += 20.0
    for number, name in meta.get("books", ()):
        page.items.append(Word(x, y, f"BOOK {NUMBER_WORDS[number]}", "sans", "b", 7.4, C.SHORT))
        page.items.append(Word(x + 62.0, y, name, "serif", "r", 11.0, C.INK))
        y += 16.0
    page.items.append(Rule(x, trim.y0 + 8.05 * PT, x + 1.1 * PT, trim.y0 + 8.05 * PT, C.SHORT, 1.4))
    page.items.append(Word(x, trim.y0 + 8.45 * PT, meta.get("author", C.AUTHOR), "sans", "sb",
                           14.0, C.INK))
    # iv -- copyright
    page = c.new_page("front", show_folio=False)
    x = c.block_x(page.recto)
    blocks = meta.get("copyright", [])
    items: list = []
    y = 0.0
    for spans in blocks:
        part, h = c.text_block(spans, TextStyle("serif", "r", 7.8, 10.6, C.INK), c.main_w)
        items += [shifted(i, 0.0, y) for i in part]
        y += h + 5.0
    base = c.bottom - y
    page.items += [shifted(i, x, base) for i in items]
    # v -- dedication, vi -- epigraph
    page = c.new_page("front", show_folio=False)
    x = c.block_x(page.recto)
    part, h = c.text_block(meta.get("dedication", [Span("")]),
                           TextStyle("serif", "i", 12.0, 17.0, C.INK), c.main_w)
    page.items += [shifted(i, x, trim.y0 + 3.0 * PT) for i in part]
    page = c.new_page("front", show_folio=False)
    x = c.block_x(page.recto)
    part, h = c.text_block(meta.get("epigraph", [Span("")]),
                           TextStyle("serif", "i", 13.0, 18.0, C.SHORT), c.main_w)
    page.items += [shifted(i, x, trim.y0 + 3.0 * PT) for i in part]
    if meta.get("epigraph_source"):
        page.items.append(Word(x, trim.y0 + 3.0 * PT + h + 14.0, meta["epigraph_source"],
                               "sans", "r", 7.8, C.MUTED))
    # contents
    contents(c, toc)
    # front chapters
    for entry in entries:
        c.chapter(entry)
    c.flush_floats()
    if len(c.pages) % 2 == 1:
        c.new_page("blank", show_folio=False)
    c.close()


def contents(c: Composer, toc: list[TocLine]) -> None:
    page = c.start_recto("toc")
    x, w = c.block_x(page.recto), c.block_w
    y = c.trim.y0 + 1.25 * PT
    page.items.append(Word(x, y, "Contents", "sans", "sb", 24.0, C.INK))
    y += 30.0
    for line in toc:
        need = 44.0 if line.kind == "book" else 16.0
        if y + need > c.bottom:
            page = c.new_page("toc")
            x = c.block_x(page.recto)
            y = c.top + 12.0
        if line.kind == "book":
            y += 12.0
            page.items.append(Word(x, y, line.label, "sans", "b", 7.4, C.LONG))
            y += 17.0
            page.items.append(Word(x, y, line.title, "serif", "r", 15.0, C.INK))
            fw = F.width(line.folio, "sans", "r", 9.0)
            page.items.append(Word(x + w - fw, y, line.folio, "sans", "r", 9.0, C.MUTED))
            y += 19.0
            continue
        if line.label:
            page.items.append(Word(x, y, line.label, "sans", "sb", 9.0, C.SHORT))
        title = line.title
        limit = w - 90.0
        while F.width(title, "serif", "r", 10.4) > limit and " " in title:
            title = title.rsplit(" ", 1)[0] + "…"
        page.items.append(Word(x + 28.0, y, title, "serif", "r", 10.4, C.INK))
        end = x + 28.0 + F.width(title, "serif", "r", 10.4) + 6.0
        fw = F.width(line.folio, "sans", "r", 9.0)
        page.items.append(Rule(end, y, x + w - fw - 6.0, y, C.FAINT, 0.8, "0.6 3.2"))
        page.items.append(Word(x + w - fw, y, line.folio, "sans", "r", 9.0, C.MUTED))
        y += 15.5


# ----------------------------------------------------------------------
# The whole book
# ----------------------------------------------------------------------

def compose_book(parts: list, back: list[Entry], front: list[Entry], meta: dict,
                 plates, sheets, tables=None) -> Layout:
    """Lay out the body, then the front matter twice (so the contents can
    quote the front chapters' own folios), then join them."""
    body = Composer(plates, sheets, tables)
    for book, entries in parts:
        body.book_divider(book)
        for entry in entries:
            body.chapter(entry)
    for entry in back:
        body.chapter(entry)
    body.flush_floats()
    body.close()

    front_lines = [TocLine("front", "", entry.chapter.title, "", 0, entry.chapter.id)
                   for entry in front]
    composer = None
    for _pass in range(2):
        composer = Composer(plates, sheets, tables, folio=lambda index: roman(index + 1))
        front_matter(composer, meta, front_lines + body.toc, front)
        front_lines = [line for line in composer.toc if line.kind == "front"]
    offset = len(composer.pages)
    for page in body.pages:
        page.index += offset
    toc = list(front_lines)
    for line in body.toc:
        line.page += offset
        toc.append(line)
    return Layout(composer.pages + body.pages, toc,
                  {**composer.plate_folios, **body.plate_folios},
                  composer.problems + body.problems, body.words,
                  {**composer.plate_numbers, **body.plate_numbers})
