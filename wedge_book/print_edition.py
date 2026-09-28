"""The print edition: the book as a finished paperback interior for KDP.

:mod:`wedge_book.build` produces a reader's PDF straight from the shared
engine, which is right for the web and wrong for a shelf: no page numbers, a
contents list with nowhere to turn to, the chapter strands ("explain",
"howto") printed as if they were part of the title, cost tables in a
typewriter face, and no title, copyright or back matter.

This module keeps the engine's HTML -- so the words, the pictures and every
computed figure are exactly the same book -- and dresses it for print:

* a title page, a copyright page and a contents list **with page numbers**;
* folios on every page except the front matter and blank pages, and mirrored
  margins with the gutter on the binding side;
* each Part opening on a right-hand page, padded with blank pages as needed;
* the strands taken out of the contents and the chapter heads;
* aligned plain-text tables turned into real tables, and one-line sums into
  displayed equations;
* figures capped at the width where they print at 300 DPI;
* a glossary, a note about the author, and an index built from the finished
  pages.

Chrome prints it. Chrome cannot put page numbers in a contents list by
itself, so the book is printed more than once: each pass reads where every
contents link actually landed, writes those numbers in, and prints again
until nothing moves. :func:`validate_print_edition` then checks the finished
file against KDP's rules and against itself.

    py -3.12 -m wedge_book.print_edition            # build (never overwrites)
    py -3.12 -m wedge_book.print_edition --check    # validate the newest one
"""

from __future__ import annotations

import html as html_escape
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from two_v_demo import book_export
from two_v_demo.deliverables import next_version_path

from . import glossary, outline, tokens

# ----------------------------------------------------------------------
# What the page must be
# ----------------------------------------------------------------------

#: KDP trim for this book, inches.
TRIM_IN = (8.5, 11.0)
#: Inside margin. KDP asks 0.5 in for 151-300 pages and 0.625 in to 500;
#: 0.875 in is its largest requirement below 828 pages, so it is safe at any
#: length this book will reach.
GUTTER_IN = 0.875
#: Outside, top and bottom. KDP's minimum without bleed is 0.25 in.
OUTSIDE_IN = 0.6
TOP_IN = 0.75
BOTTOM_IN = 0.85
#: Figures are 1600 px wide renders. At 300 DPI that is 5.33 in, which is the
#: widest they may print without KDP's low-resolution warning.
FIGURE_MAX_IN = 1600 / 300
#: KDP's paperback page limits for premium colour at this trim.
MIN_PAGES, MAX_PAGES = 24, 828

PUBLISHER = "Independently published"
YEAR = 2026
PROJECT_URL = "github.com/dkzeanah/DomeSimulator"
#: Where to find the author. From two_v_demo/segments.CONTACTS, the card at
#: the end of every film, so the book and the films say the same thing.
CONTACTS = (("Instagram", "@DonovanZeanah"), ("TikTok", "@shortcircuitr5"),
            ("Facebook", "facebook.com/zeanah"), ("GitHub", "github.com/dkzeanah"))


# ----------------------------------------------------------------------
# The stylesheet laid over the engine's
# ----------------------------------------------------------------------

PRINT_CSS = f"""
@page {{
  size: {TRIM_IN[0]}in {TRIM_IN[1]}in;
  margin: {TOP_IN}in {OUTSIDE_IN}in {BOTTOM_IN}in {GUTTER_IN}in;
  @bottom-center {{
    content: counter(page);
    font: 9.5pt Georgia, "Times New Roman", serif; color: #555;
    vertical-align: top; padding-top: .18in;
  }}
}}
@page :left {{ margin-left: {OUTSIDE_IN}in; margin-right: {GUTTER_IN}in; }}
@page :right {{ margin-left: {GUTTER_IN}in; margin-right: {OUTSIDE_IN}in; }}
@page front {{ @bottom-center {{ content: none; }} }}
@page blank {{ @bottom-center {{ content: none; }} }}

html, body {{ background: #fff; }}
body {{ font: 10.5pt/1.55 Georgia, "Times New Roman", serif; color: #111;
        hyphens: auto; -webkit-hyphens: auto; }}
p {{ text-align: justify; orphans: 3; widows: 3; }}
.wrap {{ max-width: none; padding: 0; }}
h1, h2, h3 {{ break-after: avoid; }}
figure, img, table, .sum {{ break-inside: avoid; }}
img {{ max-width: min(100%, {FIGURE_MAX_IN:.2f}in); }}
figcaption {{ font-size: 8.5pt; }}

.front {{ page: front; }}
.blank {{ page: blank; break-before: page; height: 1px; }}
.front-page {{ break-before: page; }}

/* Title page */
.title-page {{ text-align: center; padding-top: 2.4in; }}
.title-page p, .frontispiece p {{ text-align: center; }}
.title-page .t {{ font: 700 30pt/1.15 "Segoe UI", Helvetica, Arial, sans-serif; margin: 0; }}
.title-page .s {{ font: italic 17pt/1.3 Georgia, serif; color: #444; margin: .25in 0 0; }}
.title-page .rule {{ width: 1.4in; border-top: 1.5px solid #111; margin: .45in auto; }}
.title-page .a {{ font: 700 13pt/1 "Segoe UI", sans-serif; letter-spacing: .22em;
                  text-transform: uppercase; margin: 0; }}
.title-page .p {{ font: 9.5pt Georgia, serif; color: #555; margin-top: 3.4in; }}

/* Copyright page */
.copyright {{ font-size: 8.5pt; line-height: 1.5; color: #333; padding-top: 4.6in; }}
.copyright p {{ text-align: left; margin: 0 0 .09in; }}

/* Contents */
.contents h1 {{ font-size: 20pt; margin: 0 0 .25in; }}
.contents ol {{ list-style: none; margin: 0; padding: 0; }}
.contents li {{ margin: 0; }}
.contents a {{ display: flex; align-items: baseline; gap: .08in; color: #111;
               text-decoration: none; font: 10pt/1.62 Georgia, serif; }}
.contents a .n {{ min-width: .32in; color: #666; }}
.contents a .dots {{ flex: 1; border-bottom: 1px dotted #999; transform: translateY(-.28em); }}
.contents a .pg {{ min-width: .34in; text-align: right; font-variant-numeric: tabular-nums; }}
.contents .part-row a {{ font: 700 9.5pt/1.3 "Segoe UI", sans-serif; letter-spacing: .06em;
                         text-transform: uppercase; margin-top: .16in; }}
.contents .matter-row a {{ font-style: italic; }}

/* Frontispiece */
.frontispiece {{ text-align: center; padding-top: 1.2in; }}
.frontispiece img {{ margin: 0 auto .2in; }}
.frontispiece em {{ font-size: 11pt; }}

/* Tables made from the manuscript's aligned text */
table.bill {{ width: 100%; border-collapse: collapse; margin: .18in 0;
              font: 8.8pt/1.35 "Segoe UI", Helvetica, Arial, sans-serif; }}
table.bill th {{ text-align: left; font-weight: 700; border-bottom: 1.2px solid #111;
                 padding: .04in .06in; }}
table.bill td {{ padding: .03in .06in; border-bottom: .5px solid #ddd; vertical-align: top; }}
table.bill td.num, table.bill th.num {{ text-align: right; white-space: nowrap;
                                        font-variant-numeric: tabular-nums; }}
table.bill tr.total td {{ font-weight: 700; border-top: 1.2px solid #111; border-bottom: 0; }}
table.bill.long {{ break-inside: auto; }}
table.bill thead {{ display: table-header-group; }}
.sum {{ text-align: center; margin: .14in 0; font: italic 10.5pt Georgia, serif; }}
pre {{ font: 8.3pt/1.4 Consolas, monospace; background: #f6f4f0; padding: .1in .14in;
       border-left: 2px solid #c9c1b4; white-space: pre-wrap; break-inside: avoid; }}
code {{ background: none; padding: 0; font-size: .92em; }}

/* Back matter */
.back h1 {{ font-size: 20pt; margin: 0 0 .2in; }}
.glossary dl {{ margin: 0; }}
.glossary dt {{ font: 700 10pt "Segoe UI", sans-serif; margin-top: .1in; break-after: avoid; }}
.glossary dd {{ margin: .02in 0 0 0; }}
.index-list {{ columns: 2; column-gap: .35in; font-size: 9.5pt; line-height: 1.5; }}
.index-list p {{ text-align: left; margin: 0; padding-left: .18in; text-indent: -.18in;
                 break-inside: avoid; }}
.about p {{ text-align: left; }}
"""


# ----------------------------------------------------------------------
# Pieces of the book
# ----------------------------------------------------------------------

@dataclass
class Entry:
    """One line in the contents: where it points and what it says."""
    anchor: str
    label: str
    kind: str          # part | chapter | matter
    number: str = ""


@dataclass
class Layout:
    """What one printing pass learned, fed into the next."""
    pages: dict[str, int] = field(default_factory=dict)   # anchor -> page
    pad_before: set[str] = field(default_factory=set)     # part anchors needing a blank first
    index: dict[str, list[int]] = field(default_factory=dict)


def _engine_html(figure_dir: Path | None = None) -> str:
    """The engine's book. ``figure_dir`` defaults to the screen figures;
    the print edition passes the paper ones (:mod:`wedge_book.paper`)."""
    document, _ = book_export.book_html(
        root=outline.MANUSCRIPT_DIR, book=outline.BOOK, embed_images=False,
        strict=True, contents=False, figure_dir=figure_dir or outline.FIGURE_DIR,
        tokens=tokens.resolve)
    return document


def _print_figures() -> Path:
    """The paper figures, and proof that none of the book's pictures is lost.

    The engine drops a picture it cannot find without a word -- right for a
    reader, wrong here -- so the print set is checked against the screen set
    before it is used.
    """
    from . import paper

    screen = paper.used_keys()
    missing = [k for k in screen if not (paper.PRINT_DIR / f"{k}.png").is_file()]
    if missing:
        raise RuntimeError(f"{len(missing)} figures have no paper version yet "
                           f"(run py -3.12 -m wedge_book.paper): {missing[:5]}")
    return paper.PRINT_DIR


_COLUMN_GAP = re.compile(r"\s{2,}")
_NUMERIC = re.compile(r"^[-+$(]*[\d,.]+[%)]?(\s*(x|in|ft|gal|each|sq ft|ln ft|hours?|kwh|w|lb|"
                      r"mm|m|yr|kWh|W|of 2x6|ln ft of 2x6)\b.*)?$", re.IGNORECASE)


def table_from_text(block: str) -> str | None:
    """An aligned plain-text table as an HTML table, or None if it is not one.

    Columns are found where every row has blank space in the same place, so a
    row that runs its label into a number (or a block that was never a table)
    falls back to the preformatted look rather than being split wrongly.
    """
    lines = [line.rstrip() for line in block.strip("\n").splitlines()]
    lines = [line for line in lines if line.strip()]
    if len(lines) < 2:
        return None
    rule = re.compile(r"^\s*-{3,}\s*$")
    # Columns are read off the ordinary rows. A total row (the one under a
    # rule) often runs a long label across the quantity column, so it is left
    # out here and set as label + amount below.
    after_rule = {i + 1 for i, line in enumerate(lines) if rule.match(line)}
    rows = [line for i, line in enumerate(lines)
            if not rule.match(line) and i not in after_rule]
    if not rows:
        return None
    width = max(len(line) for line in lines)
    padded = [line.ljust(width) for line in rows]
    blank = [all(line[i] == " " for line in padded) for i in range(width)]
    # A column break is a run of at least two blank columns.
    cuts, i = [], 0
    while i < width:
        if blank[i]:
            j = i
            while j < width and blank[j]:
                j += 1
            if j - i >= 2 and i > 0 and j < width:
                cuts.append((i, j))
            i = j
        else:
            i += 1
    if not cuts:
        return None
    edges = [0] + [end for _, end in cuts]
    stops = [start for start, _ in cuts] + [width]

    def cells(line: str) -> list[str]:
        return [line.ljust(width)[a:b].strip() for a, b in zip(edges, stops)]

    table_rows, total_next, header = [], False, None
    for line in lines:
        if rule.match(line):
            total_next = True
            continue
        row = cells(line)
        if total_next:
            # A total is a label and one amount, and the amount is often wider
            # than the column above it: split at the last run of spaces.
            split = re.match(r"^\s*(.*?)\s{2,}(\S+)\s*$", line)
            if split:
                row = [split.group(1)] + [""] * (len(edges) - 2) + [split.group(2)]
        if header is None and not table_rows and not row[0] and any(row[1:]):
            header = row
            continue
        table_rows.append((row, total_next))
        total_next = False
    ncol = len(edges)
    numeric_col = [
        sum(1 for row, _ in table_rows if row[c] and _NUMERIC.match(row[c]))
        >= max(1, len([1 for row, _ in table_rows if row[c]]) * 0.6)
        for c in range(ncol)]
    numeric_col[0] = False

    def td(value: str, c: int, tag: str = "td") -> str:
        cls = ' class="num"' if numeric_col[c] else ""
        return f"<{tag}{cls}>{html_escape.escape(value)}</{tag}>"

    out = [f'<table class="bill{" long" if len(table_rows) > 30 else ""}">']
    if header:
        out.append("<thead><tr>" + "".join(td(v, c, "th") for c, v in enumerate(header))
                   + "</tr></thead>")
    out.append("<tbody>")
    for row, is_total in table_rows:
        out.append(f'<tr{" class=\"total\"" if is_total else ""}>'
                   + "".join(td(v, c) for c, v in enumerate(row)) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def typeset_preformatted(body: str) -> str:
    """Every <pre> block: a table if it is one, a displayed sum if it is one line."""
    def replace(match: re.Match) -> str:
        raw = html_escape.unescape(match.group(1))
        lines = [line for line in raw.strip("\n").splitlines() if line.strip()]
        if len(lines) == 1:
            text = re.sub(r"\s{2,}", "  ", lines[0].strip())
            return f'<p class="sum">{html_escape.escape(text)}</p>'
        table = table_from_text(raw)
        return table if table else match.group(0)
    return re.sub(r"<pre><code>(.*?)</code></pre>", replace, body, flags=re.S)


def split_engine(document: str) -> tuple[list[str], str]:
    """The engine's HTML as (front-matter sections, body from Part 1 on).

    The engine opens with its own title block and then the manuscript's front
    matter, sections divided by horizontal rules, before the first Part.
    """
    inner = document.split('<div class="wrap">', 1)[1].rsplit("</div>", 1)[0]
    inner = re.sub(r'<div class="book-title">.*?</div>\s*', "", inner, count=1, flags=re.S)
    inner = re.sub(r'<div class="book-sub">.*?</div>\s*', "", inner, count=1, flags=re.S)
    inner = re.sub(r'<p class="built">.*?</p>\s*', "", inner, count=1, flags=re.S)
    first_part = inner.index('<section class="part">')
    front, body = inner[:first_part], inner[first_part:]
    sections = [s.strip() for s in re.split(r"<hr\s*/?>", front) if s.strip()]
    # The strand belongs to the author's plan, not to the reader's page.
    body = re.sub(r'(<div class="chapter-eyebrow">Chapter \d+) &middot; [^<]*</div>',
                  r"\1</div>", body)
    return sections, typeset_preformatted(body)


def _heading(section: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", section, re.S)
    return re.sub(r"<[^>]+>", "", html_escape.unescape(match.group(1))).strip() if match else ""


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ----------------------------------------------------------------------
# Assembly
# ----------------------------------------------------------------------

def assemble(layout: Layout) -> tuple[str, list[Entry]]:
    document = _engine_html(_print_figures())
    front_sections, body = split_engine(document)
    book = outline.BOOK
    entries: list[Entry] = []

    # The manuscript's first front section is its own title block: keep the
    # picture and the one-line claim as a frontispiece, drop the rest (the
    # title page and the copyright page say it properly).
    title_block, *front_rest = front_sections
    figure = re.search(r"<figure>.*?</figure>", title_block, re.S)
    claim = re.search(r"<p><em>.*?</em></p>", title_block, re.S)
    frontispiece = (f'<section class="front front-page frontispiece">'
                    f'{figure.group(0) if figure else ""}{claim.group(0) if claim else ""}</section>')

    front_html = []
    for section in front_rest:
        title = _heading(section)
        anchor = f"front-{_slug(title)}"
        entries.append(Entry(anchor, title, "matter"))
        front_html.append(f'<section class="front-matter front-page" id="{anchor}">{section}</section>')

    # Parts and chapters: anchors, padding, contents lines.
    for part in book.parts:
        written = [c for c in part.chapters if f'id="ch{c.number}"' in body]
        if not written:
            continue
        anchor = f"part{part.number}"
        entries.append(Entry(anchor, part.title, "part", f"Part {part.number}"))
        for chapter in sorted(written, key=lambda c: body.index(f'id="ch{c.number}"')):
            entries.append(Entry(f"ch{chapter.number}", chapter.title, "chapter", str(chapter.number)))

    def mark_part(match: re.Match) -> str:
        number = re.search(r'<div class="part-eyebrow">Part (\d+)</div>', match.group(0)).group(1)
        anchor = f"part{number}"
        pad = '<div class="blank"></div>' if anchor in layout.pad_before else ""
        return pad + match.group(0).replace('<section class="part">',
                                            f'<section class="part" id="{anchor}">', 1)
    body = re.sub(r'<section class="part">.*?</section>', mark_part, body, flags=re.S)

    entries += [Entry("glossary", "Glossary", "matter"),
                Entry("about", "About the Author", "matter"),
                Entry("index", "Index", "matter")]

    html_parts = [
        title_page(), copyright_page(), contents(entries, layout),
        frontispiece, *front_html, body,
        glossary_section(), about_section(), index_section(layout),
    ]
    doc = document.split('<div class="wrap">', 1)[0].replace(
        "</style>", PRINT_CSS + "</style>", 1)
    doc = doc.replace(f"<title>{html_escape.escape(book.title)}</title>",
                      f"<title>{html_escape.escape(outline.TITLE)}: "
                      f"{html_escape.escape(outline.SUBTITLE)}</title>")
    doc += '<div class="wrap">' + "\n".join(html_parts) + "</div></body></html>"
    doc = cap_figures(doc)
    return doc, entries


def cap_figures(document: str) -> str:
    """Give every picture its own 300 DPI width limit.

    Most figures are 1600 px renders and :data:`FIGURE_MAX_IN` covers them;
    a smaller one would print soft at that width, so each image is capped at
    its own pixel width over 300.
    """
    from urllib.parse import unquote, urlparse

    from PIL import Image

    def replace(match: re.Match) -> str:
        tag, src = match.group(0), match.group(1)
        try:
            path = unquote(urlparse(src).path).lstrip("/")
            with Image.open(path) as im:
                width_in = im.width / 300
        except (OSError, ValueError):
            return tag
        cap = min(width_in, FIGURE_MAX_IN)
        return tag.replace("<img ", f'<img style="max-width:min(100%,{cap:.3f}in)" ', 1)
    return re.sub(r'<img [^>]*src="(file:[^"]+)"[^>]*>', replace, document)


def title_page() -> str:
    e = html_escape.escape
    return (f'<section class="front title-page">'
            f'<p class="t">{e(outline.TITLE)}</p>'
            f'<p class="s">{e(outline.SUBTITLE)}</p>'
            f'<div class="rule"></div>'
            f'<p class="a">{e(outline.AUTHOR)}</p>'
            f'<p class="p">{e(PUBLISHER)}</p></section>')


def copyright_page() -> str:
    e = html_escape.escape
    built = date.today().strftime("%B %Y")
    lines = [
        f"<strong>{e(outline.TITLE)}: {e(outline.SUBTITLE)}</strong>",
        f"Copyright &copy; {YEAR} {e(outline.AUTHOR)}. All rights reserved.",
        "No part of this book may be reproduced in any form without written "
        "permission from the author, except for brief quotations in reviews "
        "and articles.",
        f"First edition, {YEAR}. {e(PUBLISHER)}.",
        f"Every figure in this book was computed from the geometry in the "
        f"DomeSim project at the time this edition was built ({built}). The "
        f"software is open at {PROJECT_URL}.",
        f"Prices are United States retail as quoted in {built}. They are "
        "there to show proportion -- which parts cost money and which do "
        "not -- and should be checked locally before anything is bought.",
        "The illustrations are rendered by the project's own software.",
        "This book describes methods, not rated structures. Read "
        "<em>The Engineer's Note</em> before building anything from it. The "
        "author and publisher accept no liability for injury, loss or damage "
        "arising from its use.",
        "Product and store names are the trademarks of their owners and are "
        "used for identification only.",
    ]
    return ('<section class="front front-page copyright">'
            + "".join(f"<p>{line}</p>" for line in lines) + "</section>")


def contents(entries: list[Entry], layout: Layout) -> str:
    rows = []
    for entry in entries:
        page = layout.pages.get(entry.anchor)
        # A fixed-width placeholder on the first pass, so the list takes the
        # same room it will take when the real numbers go in.
        shown = str(page) if page else "000"
        label = html_escape.escape(entry.label)
        number = html_escape.escape(entry.number)
        cls = {"part": "part-row", "matter": "matter-row"}.get(entry.kind, "")
        lead = f"{number} &middot; " if entry.kind == "part" else ""
        num_cell = f'<span class="n">{number}</span>' if entry.kind == "chapter" else ""
        rows.append(f'<li class="{cls}"><a href="#{entry.anchor}">{num_cell}'
                    f"<span>{lead}{label}</span><span class=\"dots\"></span>"
                    f'<span class="pg">{shown}</span></a></li>')
    return ('<section class="front front-page contents"><h1>Contents</h1><ol>'
            + "".join(rows) + "</ol></section>")


def glossary_section() -> str:
    e = html_escape.escape
    items = "".join(f"<dt>{e(t.term)}</dt><dd>{e(t.definition)}</dd>"
                    for t in sorted(glossary.TERMS, key=lambda t: t.term.lower()))
    return (f'<section class="back glossary front-page" id="glossary">'
            f"<h1>Glossary</h1><dl>{items}</dl></section>")


def about_section() -> str:
    e = html_escape.escape
    contacts = " &middot; ".join(f"{e(k)} {e(v)}" for k, v in CONTACTS)
    # The author's own account, in the author's own voice (first person, as
    # given). Facts only as stated: nothing here is embellished.
    return (
        '<section class="back about front-page" id="about"><h1>About the Author</h1>'
        f"<p><strong>{e(outline.AUTHOR)}</strong></p>"
        "<p>I joined the U.S. Navy as an undesignated sailor and went on to "
        "serve six years as a Mass Communication Specialist, three of them "
        "living in Japan. Along the way I learned to program computers and "
        "was certified as an avionics bench technician, troubleshooting and "
        "repairing electronics. I am now in school on the G.I. Bill, working "
        "toward my A&amp;P certificate &mdash; and, beyond it, a future as an "
        "aerospace engineer.</p>"
        "<p>To me, a dome is the physical embodiment of the spirit of coding "
        "a home. It is modular and reusable. Its interfaces are decoupled, so "
        "one part can change without disturbing the rest. It is flexible, "
        "hyper-personalized, and built as a framework meant to be extended "
        "rather than a finished product. DomeSim, the open-source software "
        "this book was computed with, is that idea written as code; this book "
        "is the same idea in timber.</p>"
        "<p>This is my passion, and my aim is to change the housing market "
        "for the better.</p>"
        f"<p>The whole project &mdash; the solver, the films and the source of "
        f"this book &mdash; is open at {PROJECT_URL}, and every number in these "
        "pages can be traced back to the line of code that produced it.</p>"
        f"<p>{contacts}</p></section>")


def index_section(layout: Layout) -> str:
    rows = []
    for term in sorted(glossary.TERMS, key=lambda t: t.term.lower()):
        pages = layout.index.get(term.term)
        if not pages:
            continue
        rows.append(f"<p>{html_escape.escape(term.term)}, {page_ranges(pages)}</p>")
    return ('<section class="back front-page" id="index"><h1>Index</h1>'
            f'<div class="index-list">{"".join(rows)}</div></section>')


def page_ranges(pages: list[int]) -> str:
    """[3, 4, 5, 9] -> '3-5, 9', with an en dash."""
    pages = sorted(set(pages))
    runs, start, prev = [], pages[0], pages[0]
    for page in pages[1:] + [None]:
        if page is not None and page == prev + 1:
            prev = page
            continue
        runs.append(str(start) if start == prev else f"{start}&ndash;{prev}")
        if page is not None:
            start = prev = page
    return ", ".join(runs)


# ----------------------------------------------------------------------
# Printing, measuring, printing again
# ----------------------------------------------------------------------

def _print(document: str, path: Path) -> None:
    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the print edition needs Chrome or Edge to print with")
    if path.exists():
        path.unlink()
    book_export._pdf_via_chrome(document, path, chrome)


def measure(path: Path, entries: list[Entry]) -> dict[str, int]:
    """Where each contents link lands, as printed page numbers."""
    import pymupdf

    # Chrome writes each contents link as a named destination -- the anchor's
    # own id -- so every entry is looked up by name, never by position (a
    # line that wraps, or breaks across two pages, makes two link areas).
    doc = pymupdf.open(path)
    landed: dict[str, int] = {}
    for number, page in enumerate(doc):
        if number > 12:
            break
        for link in page.get_links():
            name = link.get("nameddest")
            if link.get("kind") in (pymupdf.LINK_NAMED, pymupdf.LINK_GOTO) and name:
                landed.setdefault(name, link["page"] + 1)
    doc.close()
    missing = [e.anchor for e in entries if e.anchor not in landed]
    if missing:
        raise RuntimeError(f"contents entries with no link in the PDF: {missing[:8]}")
    return {e.anchor: landed[e.anchor] for e in entries}


MAX_INDEX_PAGES = 8


def build_index(path: Path, pages: dict[str, int]) -> dict[str, list[int]]:
    """Every glossary term, found on the finished pages of the body."""
    import pymupdf

    first = min(pages[a] for a in pages if a.startswith("part"))
    last = pages["glossary"] - 1
    doc = pymupdf.open(path)
    found: dict[str, list[int]] = {}
    texts = {n: doc[n - 1].get_text() for n in range(first, last + 1)}
    doc.close()
    for term in glossary.TERMS:
        rx = glossary.pattern(term)
        hits = [n for n, text in texts.items() if rx.search(text)]
        if not hits:
            continue
        if len(hits) > MAX_INDEX_PAGES:
            # A word on every other page is better indexed where it is
            # densest: keep the pages that use it most.
            weight = {n: len(rx.findall(texts[n])) for n in hits}
            hits = sorted(sorted(hits, key=lambda n: -weight[n])[:MAX_INDEX_PAGES])
        found[term.term] = hits
    return found


def recto_pads(entries: list[Entry], pages: dict[str, int], pads: set[str]) -> set[str]:
    """Which Parts need a blank page before them so every Part opens on the right.

    A blank page moves everything after it by exactly one page and reflows
    nothing, so the answer can be worked out in one walk instead of by trial:
    go through the Parts in order carrying the shift the changes so far have
    caused, and give each Part a blank (or take its blank away) whenever it
    would otherwise land on an even page.
    """
    shift, out = 0, set(pads)
    for entry in entries:
        if entry.kind != "part":
            continue
        page = pages[entry.anchor] + shift
        if page % 2 == 0:
            if entry.anchor in out:
                out.discard(entry.anchor)
                shift -= 1
            else:
                out.add(entry.anchor)
                shift += 1
    return out


def build(max_passes: int = 6) -> Path:
    """Print, measure and reprint until the page numbers stop moving."""
    import tempfile

    layout = Layout()
    scratch = Path(tempfile.mkdtemp(prefix="print-edition-"))
    working = scratch / "pass.pdf"
    for attempt in range(1, max_passes + 1):
        document, entries = assemble(layout)
        _print(document, working)
        pages = measure(working, entries)
        index = build_index(working, pages)
        pads = recto_pads(entries, pages, layout.pad_before)
        settled = (pages == layout.pages and pads == layout.pad_before
                   and index == layout.index)
        moved = [a for a in pages if layout.pages.get(a) != pages[a]]
        print(f"  pass {attempt}: {len(pages)} contents lines, "
              + ("settled" if settled else
                 f"{len(moved)} moved, {len(pads ^ layout.pad_before)} blank pages changed"))
        if settled:
            break
        layout = Layout(pages=pages, pad_before=pads, index=index)
    else:
        raise RuntimeError("the page numbers did not settle")

    out = next_version_path(outline.EXPORT_DIR / f"{outline.STEM}.pdf")
    finish(working, out)
    return out


def finish(source: Path, out: Path) -> None:
    """Metadata a store and a reader see, then the file."""
    import pymupdf

    doc = pymupdf.open(source)
    doc.set_metadata({
        "title": f"{outline.TITLE}: {outline.SUBTITLE}",
        "author": outline.AUTHOR,
        "subject": "Building a timber 2V geodesic dome from split-log wedges",
        "keywords": "geodesic dome, timber frame, 2V dome, cabin, wedge, "
                    "split log, owner-builder, off-grid",
        "creator": "DomeSim wedge_book.print_edition",
        "producer": "Chrome + PyMuPDF",
    })
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    doc.close()


# ----------------------------------------------------------------------
# The checks
# ----------------------------------------------------------------------

def latest() -> Path | None:
    candidates = sorted(outline.EXPORT_DIR.glob(f"{outline.STEM}*.pdf"),
                        key=lambda p: p.stat().st_mtime)
    candidates = [p for p in candidates if re.fullmatch(
        rf"{re.escape(outline.STEM)}(-v\d+)?\.pdf", p.name)]
    return candidates[-1] if candidates else None


def _is_part_opener(text: str) -> bool:
    """A Part's opening page: its first line reads PART n, letter-spaced or not."""
    # The folio is extracted first on a numbered page; skip bare numbers.
    lines = [line for line in text.strip().splitlines()
             if line.strip() and not line.strip().isdigit()]
    return bool(lines) and re.fullmatch(r"PART\d+", re.sub(r"\s", "", lines[0]).upper()) is not None


def validate_print_edition(path: Path | None = None) -> dict:
    """The finished interior, checked against KDP and against itself."""
    import pymupdf

    path = path or latest()
    assert path and path.exists(), "no print edition has been built"
    doc = pymupdf.open(path)
    report = {"file": path.name, "pages": len(doc)}
    problems = []

    sizes = {(round(p.rect.width / 72, 3), round(p.rect.height / 72, 3)) for p in doc}
    if sizes != {TRIM_IN}:
        problems.append(f"page sizes {sizes}, want {TRIM_IN}")
    if not MIN_PAGES <= len(doc) <= MAX_PAGES:
        problems.append(f"{len(doc)} pages is outside KDP's {MIN_PAGES}-{MAX_PAGES}")

    unembedded = set()
    for page in doc:
        for xref, ext, kind, name, *_ in page.get_fonts(full=True):
            if not ext or ext == "n/a":
                unembedded.add(name)
    if unembedded:
        problems.append(f"fonts not embedded: {sorted(unembedded)}")

    meta = doc.metadata
    if meta.get("author") != outline.AUTHOR:
        problems.append("author missing from the PDF metadata")
    # Letter-spaced lines extract as "D O N O V A N": compare without spaces.
    first = re.sub(r"\s", "", doc[0].get_text()).lower()
    for must in (outline.TITLE, outline.SUBTITLE, outline.AUTHOR):
        if re.sub(r"\s", "", must).lower() not in first:
            problems.append(f"title page lacks {must!r}")
    if "All rights reserved" not in doc[1].get_text():
        problems.append("page 2 is not the copyright page")

    # The contents: every number it prints is where its link goes.
    toc_text = "".join(doc[i].get_text() for i in range(2, 6))
    for strand in ("explain", "howto", "story", "reference"):
        if re.search(rf"\b{strand}\b", toc_text):
            problems.append(f"a strand ({strand}) is still printed in the contents")
    mismatched = 0
    for number in range(2, 8):
        page = doc[number]
        for link in page.get_links():
            if link.get("kind") not in (pymupdf.LINK_NAMED, pymupdf.LINK_GOTO):
                continue
            words = [w for w in page.get_text("words")
                     if w[1] >= link["from"].y0 - 1 and w[3] <= link["from"].y1 + 1]
            printed = [w[4] for w in words if w[4].isdigit()]
            if printed and int(printed[-1]) != link["page"] + 1:
                mismatched += 1
    if mismatched:
        problems.append(f"{mismatched} contents lines print the wrong page number")

    # Folios: every page from the first Part on carries its own number,
    # except the deliberate blanks.
    part_pages = [i for i in range(len(doc)) if _is_part_opener(doc[i].get_text())]
    body_start = part_pages[0] if part_pages else 0
    missing = []
    for i in range(body_start or 0, len(doc)):
        page = doc[i]
        words = page.get_text("words")
        if not words:
            continue  # a deliberate blank
        footer = [w[4] for w in words if w[1] > page.rect.height - BOTTOM_IN * 72]
        if str(i + 1) not in footer:
            missing.append(i + 1)
    if missing:
        problems.append(f"{len(missing)} body pages without a page number, e.g. {missing[:6]}")

    parts_on_left = [i + 1 for i in part_pages if (i + 1) % 2 == 0]
    if parts_on_left:
        problems.append(f"Parts opening on a left-hand page: {parts_on_left}")

    low = []
    for i, page in enumerate(doc):
        for info in page.get_image_info():
            width_in = (info["bbox"][2] - info["bbox"][0]) / 72
            if width_in > 0.5 and info["width"] / width_in < 295:
                low.append(i + 1)
    if low:
        problems.append(f"{len(low)} figures print under 300 DPI, e.g. pages {low[:6]}")

    report["problems"] = problems
    doc.close()
    return report


def check_print_edition() -> None:
    """For the check suite: the newest print edition passes every rule."""
    report = validate_print_edition()
    assert not report["problems"], f"{report['file']}: {report['problems']}"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate the newest build only")
    args = parser.parse_args(argv)
    if not args.check:
        path = build()
        print(f"wrote {path.relative_to(outline.ROOT)}")
    report = validate_print_edition()
    print(f"{report['file']}: {report['pages']} pages")
    for problem in report["problems"]:
        print(f"  PROBLEM: {problem}")
    if not report["problems"]:
        print("  ok: trim, fonts, title and copyright pages, contents numbers, "
              "folios, Part openings, figure resolution")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
