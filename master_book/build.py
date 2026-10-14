"""Build the Master Edition: one document, printed until its page numbers settle.

The pieces come from three places and are dressed alike:

* rungs one to three, the map, the paths and the back matter are this
  edition's own manuscript (``books/master-edition/manuscript``), filled from
  :mod:`master_book.tokens`;
* Volume A is the Complete Edition exactly as :mod:`wedge_book.print_edition`
  takes it from the shared engine, with its paper figures;
* Volume B is the paperback exactly as :func:`two_v_demo.book_export.book_html`
  builds it from :mod:`two_v_demo.book`.

All three use the engine's stylesheet and the print edition's page rules, so
the volumes look like what they are -- the same project -- and the whole thing
is numbered straight through. Every anchor a reader can be sent to is linked
from somewhere; Chrome turns each link into a named destination, so after each
printing the finished pages say where every anchor landed, those page numbers
are written into the map, the paths, the contents and the thread pages, and
the book is printed again until nothing moves -- the same loop as
:func:`wedge_book.print_edition.build`.

    py -3.12 -m master_book.build            # build (never overwrites)
    py -3.12 -m master_book.build --html     # write the assembled HTML only
"""

from __future__ import annotations

import html as html_escape
import math
import re
import time
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from two_v_demo import book_export
from two_v_demo.deliverables import next_version_path

from . import outline, tokens
from .outline import CELLS, PATHS, RUNG, RUNGS, THREAD, THREADS

E = html_escape.escape
PLACEHOLDER = "000"

# ----------------------------------------------------------------------
# Names of this edition's own pages
# ----------------------------------------------------------------------

NAMED = {
    "letter": "To whoever is holding this copy",
    "how": "How this book works",
    "map": "The map",
    "paths": "Reading paths",
    "contents": "Contents",
    "vol-a": "Volume A",
    "vol-b": "Volume B",
    "threads": "Every thread, everywhere",
    "ladder": "The milestone ladder",
    "two-domes": "Two books, two domes",
    "what-to-check": "What to check",
    "feedback": "The feedback sheet",
    "glossary": "Glossary",
    "about": "About the author",
    "index": "Index",
    "colophon": "How this copy was made",
}

# ----------------------------------------------------------------------
# The stylesheet laid over the engine's and the print edition's
# ----------------------------------------------------------------------

RUNG_COLOURS = {1: "#b0601e", 2: "#2f7d4f", 3: "#2f5d7c",
                4: "#6a3d7c", 5: "#8a6508", 6: "#8c2f1f"}

MASTER_CSS = """
@page title { margin: 0.45in; @bottom-center { content: none; } }
.mb-title { page: title; text-align: center; }
.mb-title img { height: 9.1in; width: auto; max-width: none; display: block; margin: 0 auto; }
.mb-title .line { font: 9pt Georgia, serif; color: #444; margin: .12in 0 0; text-align: center; }
.mb-proof { padding-top: 3.2in; font-size: 9pt; line-height: 1.5; }
.mb-proof p { text-align: left; margin: 0 0 .1in; }
.mb-proof .stamp { font: 700 15pt "Segoe UI", sans-serif; letter-spacing: .12em;
  text-transform: uppercase; color: #8c2f1f; border: 2px solid #8c2f1f;
  display: inline-block; padding: .05in .18in; margin-bottom: .25in; }

.mb-front h1, .mb-back h1 { font-size: 22pt; margin: 0 0 .25in; }
.mb-front, .mb-back { break-before: page; }
.mb-front h2 { margin-top: .3in; }
.mb-front p, .mb-back p { text-align: left; }

/* The map */
table.map { font: 7.6pt/1.25 "Segoe UI", sans-serif; table-layout: fixed; margin: .1in 0; }
table.map th { font-size: 7.4pt; vertical-align: bottom; text-align: center; border-bottom: 1.5px solid #111; }
table.map th.thread, table.map td.thread { width: 1.25in; text-align: left; }
table.map td.thread b { display: block; font-size: 8.2pt; }
table.map td.thread span { color: #666; }
table.map td { padding: .05in .04in; border-bottom: .5px solid #ccc; vertical-align: top; }
table.map td a { color: #111; text-decoration: none; display: block; }
table.map td a .pg { display: block; font-weight: 700; color: var(--rc); font-size: 8.4pt; }
table.map td.r1, table.map th.r1 { --rc: #b0601e; }
table.map td.r2, table.map th.r2 { --rc: #2f7d4f; }
table.map td.r3, table.map th.r3 { --rc: #2f5d7c; }
table.map td.r4, table.map th.r4 { --rc: #6a3d7c; }
table.map td.r5, table.map th.r5 { --rc: #8a6508; }
table.map td.r6, table.map th.r6 { --rc: #8c2f1f; }
table.map th span { display: block; font-weight: 400; color: var(--rc); letter-spacing: .08em;
  text-transform: uppercase; font-size: 6.6pt; }

/* Lists with page numbers: contents, paths, routes, threads */
ol.pages { list-style: none; margin: .05in 0 .15in; padding: 0; }
ol.pages li { margin: 0; }
ol.pages a { display: flex; align-items: baseline; gap: .07in; color: #111; text-decoration: none;
  font: 9.4pt/1.55 Georgia, serif; }
ol.pages a .dots { flex: 1; border-bottom: 1px dotted #999; transform: translateY(-.28em); }
ol.pages a .pg { min-width: .34in; text-align: right; font-variant-numeric: tabular-nums; }
ol.pages a .tag { font: 700 7pt "Segoe UI", sans-serif; letter-spacing: .08em; color: #777;
  text-transform: uppercase; min-width: .62in; }
ol.pages li.head a { font: 700 9pt/1.3 "Segoe UI", sans-serif; letter-spacing: .05em;
  text-transform: uppercase; margin-top: .13in; }
ol.pages.small a { font-size: 8.4pt; line-height: 1.42; }
/* The contents is the longest list in the book and must close on its second page. */
#contents ol.pages a { line-height: 1.42; }
#contents ol.pages li.head a { margin-top: .1in; }
.path { break-inside: avoid; margin-bottom: .2in; }
.path h3 { margin: .15in 0 .02in; }
.path .who { font-size: 9pt; color: #666; font-style: italic; margin: 0 0 .04in; }
.cols2 { columns: 2; column-gap: .3in; }
.cols2 li { break-inside: avoid; }

/* Rung openers */
section.rung { break-before: page; border-top: 7px solid var(--rc); padding-top: .18in; }
section.rung .rung-no { font: 800 46pt/1 "Segoe UI", sans-serif; color: var(--rc); margin: 0; }
section.rung .rung-verb { font: 700 9pt "Segoe UI", sans-serif; letter-spacing: .3em;
  text-transform: uppercase; color: var(--rc); margin: .04in 0 0; }
section.rung h1 { font-size: 26pt; margin: .06in 0 .2in; }
section.rung table.facts { font-size: 9.4pt; margin: .1in 0 .2in; }
section.rung table.facts th { width: 1.35in; color: var(--rc); font-size: 8pt; letter-spacing: .06em;
  text-transform: uppercase; }
section.rung .milestones { border: 1px solid var(--rc); border-radius: 3px; padding: .08in .14in .02in;
  margin: .16in 0; break-inside: avoid; }
section.rung .milestones h3 { margin: 0 0 .06in; color: var(--rc); font-size: 10pt; }
section.rung .milestones p { font-size: 9pt; margin: 0 0 .08in; text-align: left; }
/* The rung's chapter list is read as one thing: it moves to the next page whole. */
section.rung .in-rung { break-inside: avoid; }

/* Chapters and cards */
article.cell { break-before: page; }
article.cell .chapter-eyebrow { color: var(--rc); margin-top: 0; }
article.cell .thread-tag { font: 700 7.4pt "Segoe UI", sans-serif; letter-spacing: .14em;
  text-transform: uppercase; color: #777; margin: .05in 0 0; }
article.cell h1 { margin-top: .1in; }
.rung-1 { --rc: #b0601e; } .rung-2 { --rc: #2f7d4f; } .rung-3 { --rc: #2f5d7c; }
.rung-4 { --rc: #6a3d7c; } .rung-5 { --rc: #8a6508; } .rung-6 { --rc: #8c2f1f; }
article.rung-1 p { font-size: 12.2pt; line-height: 1.6; }
article.rung-1 aside.box p, article.rung-1 aside.box li { font-size: 10.2pt; }

aside.box-do { border-left-color: #2f7d4f; background: #eef6f0; }
aside.box-do .box-label { color: #2f7d4f; }
aside.box-why { border-left-color: #2f5d7c; background: #eef3f7; }
aside.box-why .box-label { color: #2f5d7c; }
aside.box-wonder { border-left-color: #7b4ea3; background: #f4eff8; }
aside.box-wonder .box-label { color: #7b4ea3; }
aside.box-done { border-left-color: #b8860b; background: #faf5e8; }
aside.box-done .box-label { color: #8a6508; }
aside.box-watch { border-left-color: #8c2f1f; background: #f8efec; }
aside.box-watch .box-label { color: #8c2f1f; }
aside.box-check { border-left-color: #555; background: #f2f2f2; }
aside.box-check .box-label { color: #444; }
aside.box table { font-size: 8.6pt; margin: .06in 0 .1in; }
aside.box th, aside.box td { padding: .04in .05in; }
aside.box li { text-align: left; }
.blank { display: inline-block; min-width: .85in; height: 1.05em; border-bottom: 1px solid #444;
  vertical-align: bottom; }

section.route { margin: .2in 0; break-inside: avoid; }
section.route h2 { margin-top: .1in; font-size: 11pt; letter-spacing: .06em; text-transform: uppercase;
  color: var(--rc); }

/* The thread's links end the chapter, and never on a page of their own: they
   keep with the box before them, and they are set compactly so they rarely have to. */
nav.thread-nav { margin: .16in 0 0; padding: .07in .12in; border-top: 2px solid var(--rc);
  background: #faf8f4; font: 8.2pt/1.45 "Segoe UI", sans-serif; break-inside: avoid; break-before: avoid; }
nav.thread-nav .t { font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--rc);
  font-size: 7.4pt; display: block; margin-bottom: .02in; }
nav.thread-nav a { color: #111; text-decoration: none; }
nav.thread-nav a + a::before { content: "\\00a0\\00a0\\00b7\\00a0\\00a0"; color: #999; }
nav.thread-nav a b { color: #666; font-weight: 700; }

/* The paper template */
section.template-page { break-before: page; break-after: page; }
section.template-page h3 { margin: 0 0 .05in; }
section.template-page p { font: 8.4pt/1.4 "Segoe UI", sans-serif; margin: 0 0 .06in; text-align: left; }
section.template-page svg { display: block; margin: .05in auto 0; }

/* Volume openers */
section.vol-open { break-before: page; border-top: 7px solid #111; padding-top: .2in; }
section.vol-open .vol-no { font: 800 13pt "Segoe UI", sans-serif; letter-spacing: .3em; text-transform: uppercase;
  color: #555; margin: 0; }
section.vol-open h1 { font-size: 26pt; margin: .05in 0 .02in; }
section.vol-open .vol-sub { font: italic 14pt Georgia, serif; color: #444; margin: 0 0 .22in; }
section.vol-open p { text-align: left; }
.vol-front { break-before: page; }

/* Back matter */
.thread-block { break-inside: avoid; margin: 0 0 .18in; }
.thread-block h2 { margin: .12in 0 .02in; font-size: 12pt; }
.thread-block .idea { font-style: italic; color: #666; margin: 0 0 .04in; font-size: 9.4pt; }
table.ladder { break-inside: auto; }
table.ladder tr { break-inside: avoid; }
table.ladder td { font-size: 8.8pt; }
table.ladder td.box { width: .25in; font-size: 13pt; text-align: center; }
table.feedback td { height: .36in; border-bottom: 1px solid #999; }
table.feedback th { font-size: 8pt; }
.question { margin: .16in 0 .04in; font: 700 10pt "Segoe UI", sans-serif; }
.lines { border-bottom: 1px solid #999; height: .32in; }
p.checkq { margin: 0 0 .09in; text-align: left; font-size: 9.4pt; }
p.checkq a { color: #111; text-decoration: none; }
p.checkq .where { display: block; font: 700 7.4pt "Segoe UI", sans-serif; letter-spacing: .08em;
  text-transform: uppercase; color: #777; }
"""

# ----------------------------------------------------------------------
# The manuscript
# ----------------------------------------------------------------------


def _read(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text


def manuscript_files() -> dict[str, Path]:
    md = outline.MANUSCRIPT_DIR
    files: dict[str, Path] = {}
    for name in outline.FRONT_FILES:
        files[f"front:{name}"] = md / "front" / f"{name}.md"
    for rung in RUNGS:
        files[f"intro:{rung.number}"] = md / f"rung{rung.number}" / "00-intro.md"
    for c in CELLS:
        files[c.anchor] = c.path
    for name in outline.BACK_FILES:
        files[f"back:{name}"] = md / "back" / f"{name}.md"
    return files


_SPLIT = "\n\n<<<MB-SPLIT {}>>>\n\n"
_SPLIT_RE = re.compile(r"\n\n<<<MB-SPLIT (\S+)>>>\n\n")


def resolved_texts(strict: bool = True) -> dict[str, str]:
    """Every manuscript file, its tokens filled -- in one pass, because the
    Complete Edition's token table is expensive to build."""
    files = manuscript_files()
    missing = [str(p) for p in files.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} manuscript files are missing: {missing[:5]}")
    joined = "".join(_SPLIT.format(key) + _read(path) for key, path in files.items())
    filled = tokens.resolve(joined, strict=strict)
    pieces = _SPLIT_RE.split(filled)
    return {pieces[i]: pieces[i + 1] for i in range(1, len(pieces), 2)}


_BLANK = re.compile(r"\[\[blank(?::(\w+))?\]\]")
_TEMPLATE = re.compile(r"^\[\[template:([a-z-]+)\]\]\s*$", re.M)


def md_to_html(text: str) -> str:
    """The engine's Markdown, boxes and typeset tables, plus this edition's
    two markers: ``[[blank]]`` (a line to write on) and ``[[template:…]]``."""
    from wedge_book.print_edition import typeset_preformatted

    text = _BLANK.sub(lambda m: f'<span class="blank {m.group(1) or ""}"></span>', text)
    held: dict[str, str] = {}

    def hold(match: re.Match) -> str:
        key = f"MBTEMPLATE{len(held)}X"
        held[key] = TEMPLATES[match.group(1)]()
        return f"\n\n{key}\n\n"

    text = _TEMPLATE.sub(hold, text)
    html = book_export._markdown_to_html(book_export._boxes(text))
    for key, value in held.items():
        html = html.replace(f"<p>{key}</p>", value)
    return typeset_preformatted(html)


def _split_title(html: str) -> tuple[str, str]:
    """A front or back page's own H1, and the rest."""
    match = re.match(r"\s*<h1[^>]*>(.*?)</h1>", html, re.S)
    if not match:
        return "", html
    return match.group(1), html[match.end():]


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _figure_dirs() -> dict[str, list[Path]]:
    from two_v_demo.book_figures import FIGURE_DIR as B_DIR
    from wedge_book import outline as volume_a
    from wedge_book import paper

    return {"A": [paper.PRINT_DIR, volume_a.FIGURE_DIR], "B": [B_DIR]}


@lru_cache(maxsize=1)
def _captions() -> dict[tuple[str, str], str]:
    from two_v_demo import book as volume_b
    from wedge_book import outline as volume_a

    out: dict[tuple[str, str], str] = {}
    for fig in volume_a.BOOK.figures:
        out.setdefault(("A", fig.key), fig.caption)
    for fig in volume_b.BOOK.figures:
        out.setdefault(("B", fig.key), fig.caption)
    return out


def figure_path(spec: str) -> Path:
    vol, key = spec.split(":", 1) if ":" in spec else ("A", spec)
    for directory in _figure_dirs()[vol]:
        found = book_export.latest_figure(key, directory)
        if found is not None:
            return found
    raise FileNotFoundError(f"figure {spec} is not rendered")


def figure_html(spec: str, fallback: str) -> str:
    if not spec:
        return ""
    spec, _, caption = spec.partition("|")
    vol, key = spec.split(":", 1) if ":" in spec else ("A", spec)
    path = figure_path(spec)
    caption = caption or _captions().get((vol, key)) or fallback
    if "{{" in caption:
        # A borrowed caption carries its own book's tokens.
        if vol == "B":
            from two_v_demo import book_tokens
            caption = book_tokens.resolve(caption)
        else:
            caption = tokens.resolve(caption)
    return (f'<figure><img src="{path.resolve().as_uri()}" alt="{E(caption)}">'
            f"<figcaption>{E(caption)}</figcaption></figure>")


# ----------------------------------------------------------------------
# The paper dome template, drawn from the solved geometry at true size
# ----------------------------------------------------------------------

def _cap_svg(cx: float, cy: float, label: str, long_mm: float, short_mm: float) -> str:
    """One cap: five short-sided triangles round a point, with the gap that
    makes it curve. Solid lines are cut, dashed lines are folds."""
    apex = 2 * math.asin((long_mm / 2) / short_mm)
    gap = 2 * math.pi - 5 * apex
    start = math.pi / 2 + gap / 2          # the gap points down the page
    pts = []
    for i in range(6):
        a = start + i * apex
        pts.append((cx + short_mm * math.cos(a), cy + short_mm * math.sin(a)))
    outline = (f'<path d="M {cx:.2f} {cy:.2f} '
               + " ".join(f"L {x:.2f} {y:.2f}" for x, y in pts)
               + ' Z" fill="#fbf7ef" stroke="#111" stroke-width="0.35"/>')
    folds = "".join(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x:.2f}" y2="{y:.2f}" '
                    'stroke="#555" stroke-width="0.25" stroke-dasharray="1.6 1.2"/>'
                    for x, y in pts[1:-1])
    # The gap, shown so nobody cuts it shut by mistake.
    g0, g1 = pts[0], pts[-1]
    gap_fill = (f'<path d="M {cx:.2f} {cy:.2f} L {g1[0]:.2f} {g1[1]:.2f} L {g0[0]:.2f} {g0[1]:.2f} Z" '
                'fill="#e9e2d6" stroke="none"/>')
    mid = ((g0[0] + g1[0]) / 2, (g0[1] + g1[1]) / 2)
    text = (f'<text x="{cx:.2f}" y="{cy - 4:.2f}" font-family="Segoe UI, Arial" font-size="5" '
            f'text-anchor="middle" fill="#8c2f1f" font-weight="700">{E(label)}</text>'
            f'<text x="{mid[0]:.2f}" y="{mid[1] - 1.5:.2f}" font-family="Segoe UI, Arial" '
            'font-size="2.6" text-anchor="middle" fill="#666">tape closed</text>')
    return gap_fill + outline + folds + text


def _tri_svg(points, label: str) -> str:
    d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in points) + " Z"
    cx = sum(p[0] for p in points) / 3
    cy = sum(p[1] for p in points) / 3
    return (f'<path d="{d}" fill="#fbf7ef" stroke="#111" stroke-width="0.35"/>'
            f'<text x="{cx:.2f}" y="{cy + 1.6:.2f}" font-family="Segoe UI, Arial" font-size="4" '
            f'text-anchor="middle" fill="#2f5d7c" font-weight="700">{E(label)}</text>')


def _check_bar(x: float, y: float) -> str:
    return (f'<line x1="{x}" y1="{y}" x2="{x + 50}" y2="{y}" stroke="#111" stroke-width="0.6"/>'
            f'<line x1="{x}" y1="{y - 2}" x2="{x}" y2="{y + 2}" stroke="#111" stroke-width="0.4"/>'
            f'<line x1="{x + 50}" y1="{y - 2}" x2="{x + 50}" y2="{y + 2}" stroke="#111" stroke-width="0.4"/>'
            f'<text x="{x + 25}" y="{y - 2.5}" font-family="Segoe UI, Arial" font-size="3.4" '
            'text-anchor="middle" fill="#111">this bar must measure 50 mm</text>')


def paper_template_html() -> str:
    t = tokens.tokens()
    long_mm = float(t["mb.paper_long_mm"].value())
    short_mm = float(t["mb.paper_short_mm"].value())
    caps = int(t["mb.paper_caps"].value())
    equi = int(t["mb.paper_equi"].value())
    r = short_mm
    cell = 2 * r + 6
    width = 2 * cell
    # Page one: four caps.
    page1 = []
    for i in range(4):
        cx = cell / 2 + (i % 2) * cell
        cy = cell / 2 + (i // 2) * cell + 8
        page1.append(_cap_svg(cx, cy, f"CAP {i + 1}", long_mm, short_mm))
    h1 = 2 * cell + 14
    svg1 = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}mm" height="{h1:.1f}mm" '
            f'viewBox="0 0 {width:.1f} {h1:.1f}">{"".join(page1)}{_check_bar(width / 2 - 25, 5)}</svg>')
    # Page two: the last caps, then the equal-sided triangles in two strips.
    page2 = []
    rest = caps - 4
    for i in range(rest):
        cx = cell / 2 + i * cell
        cy = cell / 2 + 8
        page2.append(_cap_svg(cx, cy, f"CAP {5 + i}", long_mm, short_mm))
    h = long_mm * math.sqrt(3) / 2
    per_strip = math.ceil(equi / 2)
    strip_w = (per_strip + 1) / 2 * long_mm
    x0 = (width - strip_w) / 2
    y0 = cell + 16
    n = 0
    for strip in range(2):
        top = y0 + strip * (h + 8)
        for k in range(per_strip):
            if n >= equi:
                break
            left = x0 + k * long_mm / 2
            if k % 2 == 0:      # pointing up
                pts = ((left, top + h), (left + long_mm, top + h), (left + long_mm / 2, top))
            else:               # pointing down
                pts = ((left, top), (left + long_mm, top), (left + long_mm / 2, top + h))
            page2.append(_tri_svg(pts, f"E{n + 1}"))
            n += 1
    h2 = y0 + 2 * (h + 8) + 4
    svg2 = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}mm" height="{h2:.1f}mm" '
            f'viewBox="0 0 {width:.1f} {h2:.1f}">{"".join(page2)}{_check_bar(width / 2 - 25, 5)}</svg>')
    note = ("Print this page at <b>100 per cent (actual size)</b>. Solid lines are cut lines; "
            "dashed lines are folds; the shaded slice in each cap is the gap you tape closed. "
            f"Every long side is {long_mm:.0f} mm and every short side {short_mm:.1f} mm.")
    return (f'<section class="template-page"><h3>The paper dome &mdash; template, page 1 of 2</h3>'
            f"<p>{note}</p>{svg1}</section>"
            f'<section class="template-page"><h3>The paper dome &mdash; template, page 2 of 2</h3>'
            f"<p>The last {rest} caps, and the {equi} equal-sided triangles. Cut the triangles apart "
            "along every solid line.</p>"
            f"{svg2}</section>")


TEMPLATES = {"paper-dome": paper_template_html}


# ----------------------------------------------------------------------
# The two volumes, from the shared engine
# ----------------------------------------------------------------------

def _inner(document: str) -> str:
    return document.split('<div class="wrap">', 1)[1].rsplit("</div>", 1)[0]


def _strip_strands(body: str) -> str:
    return re.sub(r'(<div class="chapter-eyebrow">Chapter \d+) &middot; [^<]*</div>', r"\1</div>", body)


def _prefix_volume(body: str, prefix: str, name: str) -> tuple[str, list[tuple[int, str]]]:
    """Give the volume's anchors a prefix so two books can share one document,
    and say which volume each heading belongs to."""
    parts: list[tuple[int, str]] = []
    body = re.sub(r'id="ch(\d+)"', rf'id="{prefix}-ch\1"', body)
    body = re.sub(r'href="#ch(\d+)"', rf'href="#{prefix}-ch\1"', body)

    def part(match: re.Match) -> str:
        section = match.group(0)
        number = int(re.search(r'<div class="part-eyebrow">Part (\d+)</div>', section).group(1))
        title = re.search(r'<div class="part-title">(.*?)</div>', section, re.S)
        parts.append((number, html_escape.unescape(title.group(1)) if title else f"Part {number}"))
        section = re.sub(r'<section class="part"[^>]*>', f'<section class="part" id="{prefix}-part{number}">',
                         section, count=1)
        return section.replace(f'<div class="part-eyebrow">Part {number}</div>',
                               f'<div class="part-eyebrow">{name} &middot; Part {number}</div>', 1)

    body = re.sub(r'<section class="part"[^>]*>.*?</section>', part, body, flags=re.S)
    body = re.sub(r'<div class="chapter-eyebrow">Chapter (\d+)</div>',
                  rf'<div class="chapter-eyebrow">{name} &middot; Chapter \1</div>', body)
    return body, parts


@dataclass
class Volume:
    key: str
    name: str
    title: str
    subtitle: str
    about: str
    front: str
    body: str
    back: str
    parts: list[tuple[int, str]]
    chapters: list[tuple[int, str, int]]       # (number, title, part number)
    frontispiece: str = ""


def _strip_matter_wrappers(html: str) -> str:
    html = re.sub(r'<section class="matter[^"]*">', "", html)
    return html.replace("</section>", "")


def volume_a() -> Volume:
    from wedge_book import outline as volume
    from wedge_book import print_edition as pe

    document = pe._engine_html(pe._print_figures())
    inner = _inner(document)
    first_part = inner.index('<section class="part">')
    front, body = inner[:first_part], inner[first_part:]
    front = _strip_matter_wrappers(front)
    sections = [s.strip() for s in re.split(r"<hr\s*/?>", front) if s.strip()]
    title_block, rest = sections[0], sections[1:]
    figure = re.search(r"<figure>.*?</figure>", title_block, re.S)
    claim = re.search(r"<p><em>.*?</em></p>", title_block, re.S)
    front_html = []
    for section in rest:
        heading = re.search(r"<h1[^>]*>(.*?)</h1>", section, re.S)
        text = html_escape.unescape(re.sub(r"<[^>]+>", "", heading.group(1))) if heading else "front"
        anchor = "a-front-engineer" if "Engineer" in text else "a-front-" + re.sub(r"[^a-z0-9]+", "-",
                                                                                 text.lower()).strip("-")
        front_html.append(f'<section class="vol-front" id="{anchor}">{section}</section>')
    body = pe.typeset_preformatted(_strip_strands(body))
    body, parts = _prefix_volume(body, "a", "Volume A")
    chapters = []
    for part_obj in volume.BOOK.parts:
        for chapter in part_obj.chapters:
            if f'id="a-ch{chapter.number}"' in body:
                chapters.append((chapter.number, chapter.title, part_obj.number))
    return Volume(
        key="a", name="Volume A", title=volume.TITLE, subtitle=volume.SUBTITLE,
        about=("The owner's own dome, computed end to end: why the frame may be rough and the "
               "skin may not, the geometry from one number, the stick, the panel, the skin and the "
               "seam, the ground, the money, the network, other shapes, the catalogue, the stem cell, "
               "the variations, every way to style it, and the tools that computed all of it. "
               "This is the Complete Edition sold on the project's website."),
        front="".join(front_html), body=body, back="", parts=parts, chapters=chapters,
        frontispiece=(figure.group(0) if figure else "") + (claim.group(0) if claim else ""))


def volume_b() -> Volume:
    from two_v_demo import book as volume
    from two_v_demo import book_tokens
    from wedge_book import print_edition as pe

    document, report = book_export.book_html(
        root=volume.MANUSCRIPT_DIR, book=volume.BOOK, embed_images=False, strict=True,
        contents=False, tokens=book_tokens.resolve)
    if report.figures_missing:
        raise RuntimeError(f"Volume B is missing figures: {list(report.figures_missing)[:5]}")
    inner = _inner(document)
    first_part = inner.index('<section class="part">')
    last_article = inner.rindex("</article>") + len("</article>")
    front, body, tail = inner[:first_part], inner[first_part:last_article], inner[last_article:]
    # The volume opener prints the title; the manuscript's own title lines go.
    front = re.sub(r"^\s*<section class=\"matter matter-title\">\s*<h1>.*?</h1>\s*<h2>.*?</h2>",
                   '<section class="matter matter-title">', front, count=1, flags=re.S)
    tables = re.search(r'<section class="matter matter-tables">.*?</section>', tail, re.S)
    body = pe.typeset_preformatted(_strip_strands(body))
    body, parts = _prefix_volume(body, "b", "Volume B")
    chapters = []
    for part_obj in volume.BOOK.parts:
        for chapter in part_obj.chapters:
            if f'id="b-ch{chapter.number}"' in body:
                chapters.append((chapter.number, chapter.title, part_obj.number))
    back = ""
    if tables:
        back = tables.group(0).replace('<section class="matter matter-tables">',
                                       '<section class="matter matter-tables vol-front" id="b-tables">', 1)
        back = pe.typeset_preformatted(back)
    return Volume(
        key="b", name="Volume B", title=volume.TITLE, subtitle=volume.SUBTITLE,
        about=("The same method told as a fortnight from one measured tree: three trees, one "
               "small chainsaw, the build day by day, the cuts and the jig in reference form, the "
               "shell and the money -- and four chapters on why the shape is worth it. This is the "
               "paperback, revised for Amazon."),
        front=f'<section class="vol-front" id="b-front">{front}</section>', body=body, back=back,
        parts=parts, chapters=chapters)


# ----------------------------------------------------------------------
# Layout: what the last printing learned
# ----------------------------------------------------------------------

@dataclass
class Layout:
    pages: dict[str, int] = field(default_factory=dict)
    index: dict[str, list[int]] = field(default_factory=dict)
    #: Every anchor a page number was printed for, so the build can refuse
    #: to print one that nothing measures.
    asked: set[str] = field(default_factory=set)

    def pg(self, anchor: str) -> str:
        self.asked.add(anchor)
        page = self.pages.get(anchor)
        return str(page) if page else PLACEHOLDER


def _vol_lookup(vol: str, ref: str) -> tuple[str, str, str]:
    """(anchor, tag, label) for a volume chapter named by ref."""
    from two_v_demo import book as volume_b
    from wedge_book import outline as volume_a

    if ref == "front:engineer":
        return "a-front-engineer", "Vol A", "The Engineer's Note"
    book = volume_a.BOOK if vol == "A" else volume_b.BOOK
    chapter = book.by_ref(ref)
    return f"{vol.lower()}-ch{chapter.number}", f"Vol {vol} &middot; {chapter.number}", chapter.title


def _stop(stop: str) -> tuple[str, str, str]:
    """(anchor, tag, label) for any stop on a path."""
    if stop.startswith("a:"):
        return _vol_lookup("A", stop[2:])
    if stop.startswith("b:"):
        return _vol_lookup("B", stop[2:])
    if stop in outline.CELL:
        c = outline.CELL[stop]
        return stop, f"Rung {c.rung}", c.title
    return stop, "", NAMED[stop]


def page_row(anchor: str, label: str, layout: Layout, tag: str = "", cls: str = "") -> str:
    tag_html = f'<span class="tag">{tag}</span>' if tag else ""
    return (f'<li class="{cls}"><a href="#{anchor}">{tag_html}<span>{E(html_escape.unescape(label))}</span>'
            f'<span class="dots"></span><span class="pg">{layout.pg(anchor)}</span></a></li>')


# ----------------------------------------------------------------------
# The pages this edition generates
# ----------------------------------------------------------------------

COVER_PATH = outline.COVER_DIR / "master-front.png"


def make_cover() -> Path:
    """The rendered cover scene, lettered MASTER EDITION."""
    from PIL import Image

    from wedge_book import cover_scene, cover_type

    scene = Image.open(cover_scene.OUT_DIR / "scene.png")
    img = cover_type.compose(scene, subtitle=outline.SUBTITLE.upper())
    COVER_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(COVER_PATH)
    return COVER_PATH


def title_page() -> str:
    import base64

    # Embedded rather than linked: the figure cap that keeps every linked
    # picture at 300 DPI would otherwise squeeze the full-page cover.
    data = base64.b64encode(COVER_PATH.read_bytes()).decode("ascii")
    return (f'<section class="mb-title"><img src="data:image/png;base64,{data}" '
            f'alt="{E(outline.TITLE)}: {E(outline.SUBTITLE)}">'
            f'<p class="line">{E(outline.TITLE)} &middot; {E(outline.SUBTITLE)} &middot; '
            f"{E(outline.AUTHOR)} &middot; reader&rsquo;s proof</p></section>")


def proof_page(texts: dict[str, str]) -> str:
    import json

    from wedge_book import print_edition as pe

    site = json.loads((outline.ROOT / "web" / "site.config.json").read_text(encoding="utf-8"))
    contacts = " &middot; ".join(f"{E(k)} {E(v)}" for k, v in pe.CONTACTS)
    built = tokens.tokens()["mb.built"].value()
    lines = [
        '<span class="stamp">Reader&rsquo;s proof &mdash; not for sale</span>',
        f"<strong>{E(outline.TITLE)}: {E(outline.SUBTITLE)}</strong>",
        f"Copyright &copy; {date.today().year} {E(outline.AUTHOR)}. All rights reserved. "
        "This copy is for review by friends of the project; please do not share or sell it.",
        f"Built {E(built)} from the live manuscripts of <em>The 40 Hour Cabin: Complete Edition</em> "
        "and <em>The 40 Hour Cabin: 2V Geodesic Dome Wedge Method</em>, which are bound in whole as "
        "Volumes A and B, and from this edition's own rungs. Every figure was computed that day by "
        "the DomeSim project's software.",
        "This book describes methods, not rated structures. Nothing in it is a structural rating, a "
        "permit or a substitute for a licensed engineer, electrician or plumber. Read the safety "
        "thread -- the last chapter of every rung -- and Volume A's Engineer's Note before building "
        "anything from it.",
        f"{E(site.get('url', ''))} &middot; {contacts}",
    ]
    return '<section class="front-page mb-proof">' + "".join(f"<p>{x}</p>" for x in lines) + "</section>"


def front_page(key: str, anchor: str, texts: dict[str, str], extra: str = "") -> str:
    title, rest = _split_title(md_to_html(texts[f"front:{key}"]))
    return (f'<section class="mb-front" id="{anchor}"><h1>{title}</h1>{rest}{extra}</section>')


def map_html(layout: Layout) -> str:
    head = "".join(f'<th class="r{r.number}">Rung {r.number}<span>{E(r.verb)}</span></th>' for r in RUNGS)
    rows = []
    for t in THREADS:
        cells = []
        for r in RUNGS:
            c = outline.cell(r.number, t.key)
            cells.append(f'<td class="r{r.number}"><a href="#{c.anchor}">{E(c.short)}'
                         f'<span class="pg">{layout.pg(c.anchor)}</span></a></td>')
        rows.append(f'<tr><td class="thread"><a href="#thread-{t.key}"><b>{t.number}. {E(t.name)}</b>'
                    f'<span>{E(t.idea)}</span></a></td>{"".join(cells)}</tr>')
    return (f'<section class="mb-front" id="map"><h1>The Map</h1>'
            "<p>Twelve ideas down the side, six rungs across the top. Every cell is a chapter, and "
            "its page. Read down a column for one rung's whole story; read along a row to climb one "
            "idea; start anywhere.</p>"
            f'<table class="map"><thead><tr><th class="thread">Thread</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></section>')


def paths_html(layout: Layout) -> str:
    blocks = []
    for path in PATHS:
        items = []
        for stop in path.stops:
            anchor, tag, label = _stop(stop)
            items.append(page_row(anchor, label, layout, tag))
        blocks.append(f'<div class="path"><h3>{E(path.title)}</h3><p class="who">{E(path.who)}</p>'
                      f'<ol class="pages small">{"".join(items)}</ol></div>')
    return (f'<section class="mb-front" id="paths"><h1>Reading Paths</h1>'
            f"<p>Nobody needs to read this book in order. Here are {len(PATHS)} ways through it, each "
            "for a different reader with a different amount of time. Follow one, or make your own "
            "from the map.</p>" + "".join(blocks)
            + f'<p>Everything else is in the <a href="#contents">contents, page '
            f"{layout.pg('contents')}</a>.</p></section>")


def contents_html(layout: Layout, vols: list[Volume]) -> str:
    rows = [page_row(a, NAMED[a], layout) for a in ("letter", "how", "map", "paths")]
    for r in RUNGS:
        rows.append(page_row(r.anchor, f"Rung {r.number} &middot; {r.title}", layout, cls="head"))
        for c in outline.cells_in_rung(r.number):
            rows.append(page_row(c.anchor, c.title, layout, f"{THREAD[c.thread].number:02d}"))
    for v in vols:
        rows.append(page_row(f"vol-{v.key}", f"{v.name} &middot; {v.title}: {v.subtitle}", layout, cls="head"))
        for number, title in v.parts:
            rows.append(page_row(f"{v.key}-part{number}", title, layout, f"Part {number}"))
    rows.append(page_row("threads", "At the back", layout, cls="head"))
    for a in ("threads", "ladder", "two-domes", "what-to-check", "feedback", "glossary", "about",
              "index", "colophon"):
        rows.append(page_row(a, NAMED[a], layout))
    return (f'<section class="mb-front" id="contents"><h1>Contents</h1>'
            f'<ol class="pages">{"".join(rows)}</ol></section>')


def rung_html(rung, texts: dict[str, str], layout: Layout) -> str:
    facts = (("For", rung.who), ("Time", rung.time), ("You need", rung.need),
             ("You will be able to", rung.promise), ("You are ready when", rung.ready))
    table = "".join(f"<tr><th>{E(k)}</th><td>{E(v)}</td></tr>" for k, v in facts)
    stones = "".join(
        f"<p><b>&#9744; {E(m.title)}</b> &mdash; {E(m.who)}, {E(m.time.lower())}. "
        f"<i>Done when:</i> {E(m.done_when)}</p>" for m in rung.milestones)
    listing = "".join(page_row(c.anchor, c.title, layout, f"{THREAD[c.thread].number:02d}")
                      for c in outline.cells_in_rung(rung.number))
    intro = md_to_html(texts[f"intro:{rung.number}"])
    return (f'<section class="rung rung-{rung.number}" id="{rung.anchor}" '
            f'style="--rc:{RUNG_COLOURS[rung.number]}">'
            f'<p class="rung-no">Rung {rung.number}</p><p class="rung-verb">{E(rung.verb)}</p>'
            f"<h1>{E(rung.title)}</h1>"
            f'<table class="facts">{table}</table>{intro}'
            f'<div class="milestones"><h3>Milestones on this rung</h3>{stones}</div>'
            f'<div class="in-rung"><h3>In this rung</h3><ol class="pages small cols2">{listing}</ol>'
            "</div></section>")


def _nav(c, layout: Layout) -> str:
    t = THREAD[c.thread]
    links = []
    if c.rung > 1:
        below = outline.cell(c.rung - 1, c.thread)
        links.append(f'<a href="#{below.anchor}"><b>&darr; Simpler</b> Rung {below.rung} &middot; '
                     f"{E(below.title)} &middot; p.&nbsp;{layout.pg(below.anchor)}</a>")
    if c.rung < len(RUNGS):
        above = outline.cell(c.rung + 1, c.thread)
        links.append(f'<a href="#{above.anchor}"><b>&uarr; Deeper</b> Rung {above.rung} &middot; '
                     f"{E(above.title)} &middot; p.&nbsp;{layout.pg(above.anchor)}</a>")
    links.append(f'<a href="#thread-{t.key}"><b>&rarr; All of it</b> every page on this thread, '
                 f"both volumes &middot; p.&nbsp;{layout.pg('thread-' + t.key)}</a>")
    return (f'<nav class="thread-nav"><span class="t">Thread {t.number} &middot; {E(t.name)} &mdash; '
            f'{E(t.idea)}</span>{"".join(links)}</nav>')


def _route(c, layout: Layout) -> str:
    rows = []
    for ref in c.vol_a:
        anchor, tag, label = _vol_lookup("A", ref)
        rows.append(page_row(anchor, label, layout, tag))
    for ref in c.vol_b:
        anchor, tag, label = _vol_lookup("B", ref)
        rows.append(page_row(anchor, label, layout, tag))
    return (f'<section class="route"><h2>Read, in order</h2><ol class="pages">{"".join(rows)}</ol>'
            "</section>")


def cell_html(c, texts: dict[str, str], layout: Layout) -> str:
    rung = RUNG[c.rung]
    t = THREAD[c.thread]
    body = md_to_html(texts[c.anchor])
    route = "" if rung.written else _route(c, layout)
    if not rung.written:
        # The route goes after the card's opening paragraph and before its boxes.
        cut = body.find("<aside")
        body = body[:cut] + route + body[cut:] if cut != -1 else body + route
    nav = _nav(c, layout)
    # A cut-out template ends the chapter on pages of its own, so the thread's
    # links close the reading part rather than strand on a page after it.
    cut = body.find('<section class="template-page"')
    if cut != -1:
        body, nav = body[:cut] + nav + body[cut:], ""
    return (f'<article class="chapter cell rung-{c.rung}" id="{c.anchor}" '
            f'style="--rc:{RUNG_COLOURS[c.rung]}">'
            f'<div class="chapter-eyebrow">Rung {c.rung} &middot; {E(rung.title)}</div>'
            f'<p class="thread-tag">Thread {t.number} of {len(THREADS)} &middot; {E(t.name)}</p>'
            f"<h1>{E(c.title)}</h1>"
            f'<p class="deck">{E(c.deck)}</p>'
            f"{figure_html(c.figure, c.deck)}{body}{nav}</article>")


def volume_open_html(v: Volume, layout: Layout) -> str:
    rows = []
    by_part: dict[int, list] = {}
    for number, title, part in v.chapters:
        by_part.setdefault(part, []).append((number, title))
    for number, title in v.parts:
        rows.append(page_row(f"{v.key}-part{number}", title, layout, f"Part {number}", cls="head"))
        for ch_number, ch_title in by_part.get(number, []):
            rows.append(page_row(f"{v.key}-ch{ch_number}", ch_title, layout, f"{ch_number}"))
    if v.key == "a":
        rows.insert(0, page_row("a-front-engineer", "The Engineer's Note", layout))
    if v.back:
        rows.append(page_row(f"{v.key}-tables", "The Master Tables", layout, cls="head"))
    return (f'<section class="vol-open" id="vol-{v.key}"><p class="vol-no">{E(v.name)}</p>'
            f"<h1>{E(v.title)}</h1><p class=\"vol-sub\">{E(v.subtitle)}</p>"
            f"<p>{E(v.about)}</p>"
            "<p>It is bound here whole, exactly as its own build produced it on the day this copy was "
            "made. Its chapters keep their own numbers; the page numbers are this book's.</p>"
            f"{v.frontispiece}"
            f'<ol class="pages small cols2">{"".join(rows)}</ol></section>')


def threads_html(layout: Layout) -> str:
    blocks = []
    for t in THREADS:
        rows = [page_row(c.anchor, c.title, layout, f"Rung {c.rung}") for c in outline.cells_in_thread(t.key)]
        seen: list[tuple[str, str]] = []
        for c in outline.cells_in_thread(t.key):
            for ref in c.vol_a:
                if ("A", ref) not in seen:
                    seen.append(("A", ref))
            for ref in c.vol_b:
                if ("B", ref) not in seen:
                    seen.append(("B", ref))
        vol_rows = []
        for vol, ref in sorted(seen, key=lambda s: (s[0], 0 if s[1].startswith("front")
                                                    else _vol_number(*s))):
            anchor, tag, label = _vol_lookup(vol, ref)
            vol_rows.append(page_row(anchor, label, layout, tag))
        blocks.append(f'<div class="thread-block" id="thread-{t.key}"><h2>{t.number}. {E(t.name)}</h2>'
                      f'<p class="idea">{E(t.idea)}</p><ol class="pages small">{"".join(rows)}</ol>'
                      f'<ol class="pages small cols2">{"".join(vol_rows)}</ol></div>')
    return (f'<section class="mb-back" id="threads"><h1>Every Thread, Everywhere</h1>'
            "<p>Each idea, with every page in this book where it appears: its six rungs first, then "
            "the chapters of both volumes it runs through.</p>" + "".join(blocks) + "</section>")


def _vol_number(vol: str, ref: str) -> int:
    from two_v_demo import book as volume_b
    from wedge_book import outline as volume_a

    return (volume_a.BOOK if vol == "A" else volume_b.BOOK).by_ref(ref).number


def ladder_html(layout: Layout) -> str:
    rows = []
    for r in RUNGS:
        for m in r.milestones:
            rows.append(f'<tr><td class="box">&#9744;</td><td><b>Rung {r.number}: {E(m.title)}</b><br>'
                        f"{E(m.who)} &middot; {E(m.time)} &middot; you need: {E(m.need)}</td>"
                        f"<td>{E(m.done_when)}</td>"
                        f'<td><a href="#{r.anchor}">p.&nbsp;{layout.pg(r.anchor)}</a></td></tr>')
    return (f'<section class="mb-back" id="ladder"><h1>The Milestone Ladder</h1>'
            "<p>Tick them off as a family. A milestone is something you did, not something you read; "
            "the next rung makes the most sense once the one below it is ticked.</p>"
            '<table class="ladder"><thead><tr><th></th><th>Milestone</th><th>Done when</th>'
            f'<th>Rung</th></tr></thead><tbody>{"".join(rows)}</tbody></table></section>')


def back_page(key: str, anchor: str, texts: dict[str, str], extra: str = "") -> str:
    title, rest = _split_title(md_to_html(texts[f"back:{key}"]))
    return f'<section class="mb-back" id="{anchor}"><h1>{title}</h1>{rest}{extra}</section>'


def checker_questions(texts: dict[str, str]) -> list[tuple[str, str]]:
    """Every "For checkers" question on the route cards, with its card."""
    out = []
    pattern = re.compile(r':::box check[^\n]*\n(?P<body>.*?)^:::', re.S | re.M)
    for c in CELLS:
        if RUNG[c.rung].written:
            continue
        match = pattern.search(texts[c.anchor])
        if match:
            out.append((c.anchor, " ".join(match.group("body").split())))
    return out


def what_to_check_extra(texts: dict[str, str], layout: Layout) -> str:
    items = []
    for anchor, question in checker_questions(texts):
        c = outline.CELL[anchor]
        items.append(f'<p class="checkq"><span class="where">Rung {c.rung} &middot; {E(c.title)} &middot; '
                     f'<a href="#{anchor}">p.&nbsp;{layout.pg(anchor)}</a></span>{E(question)}</p>')
    return "<h2>Every question for checkers</h2>" + "".join(items)


#: Note lines on the feedback sheet: as many as leave it one page to tear out.
FEEDBACK_ROWS = 9


def feedback_html() -> str:
    rows = "".join("<tr><td></td><td></td><td></td></tr>" for _ in range(FEEDBACK_ROWS))
    questions = ("Where did you get lost, bored or confused?",
                 "Which number, claim or instruction do you think is wrong?",
                 "What would you not want a first-time builder to do exactly as written?",
                 "Would you build one -- or back one? What would change your mind?")
    qs = "".join(f'<p class="question">{E(q)}</p><div class="lines"></div><div class="lines"></div>'
                 for q in questions)
    return (f'<section class="mb-back" id="feedback"><h1>The Feedback Sheet</h1>'
            "<p>Tear this out, photograph it, or copy it into an email. Marks: "
            "<b>&#10007;</b> wrong &middot; <b>?</b> unclear &middot; <b>!</b> unsafe &middot; "
            "<b>&#9733;</b> keep.</p>"
            '<table class="feedback"><thead><tr><th style="width:.8in">Page</th>'
            '<th style="width:.6in">Mark</th><th>Note</th></tr></thead>'
            f"<tbody>{rows}</tbody></table>{qs}"
            '<p class="question">Your name, and how to reach you (optional)</p><div class="lines"></div>'
            "</section>")


def index_html(layout: Layout) -> str:
    from wedge_book import glossary
    from wedge_book.print_edition import page_ranges

    rows = []
    for term in sorted(glossary.TERMS, key=lambda t: t.term.lower()):
        pages = layout.index.get(term.term)
        if pages:
            rows.append(f"<p>{E(term.term)}, {page_ranges(pages)}</p>")
    return ('<section class="back front-page" id="index"><h1>Index</h1>'
            f'<div class="index-list">{"".join(rows)}</div></section>')


# ----------------------------------------------------------------------
# Assembly
# ----------------------------------------------------------------------

@dataclass
class Sources:
    texts: dict[str, str]
    vols: list[Volume]


def gather(strict: bool = True) -> Sources:
    started = time.time()
    texts = resolved_texts(strict=strict)
    print(f"  manuscript resolved ({time.time() - started:.0f} s)")
    started = time.time()
    vols = [volume_a(), volume_b()]
    print(f"  volumes assembled ({time.time() - started:.0f} s): "
          + ", ".join(f"{v.name} {len(v.chapters)} chapters" for v in vols))
    return Sources(texts, vols)


def assemble(sources: Sources, layout: Layout) -> str:
    from wedge_book import print_edition as pe

    texts, vols = sources.texts, sources.vols
    sections = [
        title_page(),
        proof_page(texts),
        front_page("letter", "letter", texts),
        front_page("how-to-read", "how", texts),
        map_html(layout),
        paths_html(layout),
        contents_html(layout, vols),
    ]
    for rung in RUNGS:
        sections.append(rung_html(rung, texts, layout))
        for c in outline.cells_in_rung(rung.number):
            sections.append(cell_html(c, texts, layout))
    for v in vols:
        sections.append(volume_open_html(v, layout))
        sections.append(v.front)
        sections.append(v.body)
        if v.back:
            sections.append(v.back)
    sections += [
        threads_html(layout),
        ladder_html(layout),
        back_page("two-domes", "two-domes", texts),
        back_page("what-to-check", "what-to-check", texts, what_to_check_extra(texts, layout)),
        feedback_html(),
        pe.glossary_section(),
        pe.about_section(),
        index_html(layout),
        back_page("colophon", "colophon", texts),
    ]
    title = f"{outline.TITLE}: {outline.SUBTITLE}"
    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="author" content="{E(outline.AUTHOR)}"><title>{E(title)}</title>'
            f"<style>{book_export.BOOK_CSS}{pe.PRINT_CSS}{MASTER_CSS}</style></head><body>")
    document = head + '<div class="wrap">' + "\n".join(sections) + "</div></body></html>"
    return pe.cap_figures(document)


# ----------------------------------------------------------------------
# Printing, measuring, printing again
# ----------------------------------------------------------------------

def required_anchors(sources: Sources) -> list[str]:
    anchors = ["letter", "how", "map", "paths", "contents"]
    for r in RUNGS:
        anchors.append(r.anchor)
        anchors += [c.anchor for c in outline.cells_in_rung(r.number)]
    for v in sources.vols:
        anchors.append(f"vol-{v.key}")
        anchors += [f"{v.key}-part{n}" for n, _ in v.parts]
        anchors += [f"{v.key}-ch{n}" for n, _, _ in v.chapters]
        if v.back:
            anchors.append(f"{v.key}-tables")
    anchors += ["a-front-engineer", "threads"] + [f"thread-{t.key}" for t in THREADS]
    anchors += ["ladder", "two-domes", "what-to-check", "feedback", "glossary", "about", "index",
                "colophon"]
    return anchors


def measure(path: Path) -> dict[str, int]:
    import pymupdf

    doc = pymupdf.open(path)
    landed: dict[str, int] = {}
    for page in doc:
        for link in page.get_links():
            name = link.get("nameddest")
            if name and link.get("kind") in (pymupdf.LINK_NAMED, pymupdf.LINK_GOTO) and link.get("page", -1) >= 0:
                landed.setdefault(name, link["page"] + 1)
    doc.close()
    return landed


MAX_INDEX_PAGES = 8


def build_index(path: Path, pages: dict[str, int]) -> dict[str, list[int]]:
    import pymupdf

    from wedge_book import glossary

    first, last = pages["rung1"], pages["threads"] - 1
    doc = pymupdf.open(path)
    texts = {n: doc[n - 1].get_text() for n in range(first, last + 1)}
    doc.close()
    found: dict[str, list[int]] = {}
    for term in glossary.TERMS:
        rx = glossary.pattern(term)
        hits = [n for n, text in texts.items() if rx.search(text)]
        if not hits:
            continue
        if len(hits) > MAX_INDEX_PAGES:
            weight = {n: len(rx.findall(texts[n])) for n in hits}
            hits = sorted(sorted(hits, key=lambda n: -weight[n])[:MAX_INDEX_PAGES])
        found[term.term] = hits
    return found


def _print(document: str, path: Path) -> None:
    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the Master Edition needs Chrome or Edge to print with")
    if path.exists():
        path.unlink()
    book_export._pdf_via_chrome(document, path, chrome)


def build(max_passes: int = 6, html_only: bool = False, draft: Path | None = None) -> Path:
    import tempfile

    make_cover()
    sources = gather()
    layout = Layout()
    scratch = Path(tempfile.mkdtemp(prefix="master-edition-"))
    if html_only:
        out = scratch / "master.html"
        out.write_text(assemble(sources, layout), encoding="utf-8")
        return out
    working = scratch / "pass.pdf"
    need = required_anchors(sources)
    for attempt in range(1, max_passes + 1):
        started = time.time()
        document = assemble(sources, layout)
        unmeasured = sorted(layout.asked - set(need))
        if unmeasured:
            raise RuntimeError(f"page numbers printed for anchors nothing measures: {unmeasured[:10]}")
        _print(document, working)
        pages = measure(working)
        missing = [a for a in need if a not in pages]
        if missing:
            raise RuntimeError(f"anchors with no link in the PDF: {missing[:10]}")
        pages = {a: pages[a] for a in need}
        index = build_index(working, pages)
        settled = pages == layout.pages and index == layout.index
        moved = sum(1 for a in pages if layout.pages.get(a) != pages[a])
        import pymupdf
        count = len(pymupdf.open(working))
        print(f"  pass {attempt}: {count} pages, {moved} anchors moved "
              f"({time.time() - started:.0f} s)" + (" -- settled" if settled else ""))
        if settled:
            break
        layout = Layout(pages=pages, index=index)
    else:
        raise RuntimeError("the page numbers did not settle")
    # A draft is a proof for looking at, printed outside deliverables/; the
    # real copy is a new numbered file there, never a replacement.
    out = draft or next_version_path(outline.EXPORT_DIR / f"{outline.STEM}.pdf")
    finish(working, out, sources, layout)
    return out


def bookmarks(sources: Sources, layout: Layout) -> list[list]:
    p = layout.pages
    toc = [[1, NAMED[a], p[a]] for a in ("letter", "how", "map", "paths", "contents")]
    for r in RUNGS:
        toc.append([1, f"Rung {r.number} - {r.title}", p[r.anchor]])
        for c in outline.cells_in_rung(r.number):
            toc.append([2, c.title, p[c.anchor]])
    for v in sources.vols:
        toc.append([1, f"{v.name} - {v.title}: {v.subtitle}", p[f"vol-{v.key}"]])
        chapters_by_part: dict[int, list] = {}
        for number, title, part in v.chapters:
            chapters_by_part.setdefault(part, []).append((number, title))
        for number, title in v.parts:
            toc.append([2, f"Part {number}: {title}", p[f"{v.key}-part{number}"]])
            for ch, ch_title in chapters_by_part.get(number, []):
                toc.append([3, f"{ch}. {ch_title}", p[f"{v.key}-ch{ch}"]])
        if v.back:
            toc.append([2, "The Master Tables", p[f"{v.key}-tables"]])
    for a in ("threads", "ladder", "two-domes", "what-to-check", "feedback", "glossary", "about",
              "index", "colophon"):
        toc.append([1, NAMED[a], p[a]])
    return toc


def finish(source: Path, out: Path, sources: Sources, layout: Layout) -> None:
    import pymupdf

    doc = pymupdf.open(source)
    doc.set_metadata({
        "title": f"{outline.TITLE}: {outline.SUBTITLE}",
        "author": outline.AUTHOR,
        "subject": "Reader's proof: six rungs of the wedge-dome method, with both books inside",
        "keywords": "geodesic dome, timber frame, split log, family, education, owner-builder",
        "creator": "DomeSim master_book.build",
        "producer": "Chrome + PyMuPDF",
    })
    doc.set_toc(bookmarks(sources, layout))
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    doc.close()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--html", action="store_true", help="write the assembled HTML only")
    parser.add_argument("--draft", type=Path, metavar="PDF",
                        help="print a proof to this path instead of a new copy in deliverables/")
    args = parser.parse_args(argv)
    if args.draft and outline.EXPORT_DIR.resolve() in args.draft.resolve().parents:
        parser.error("a draft goes outside deliverables/; the copies there are numbered, not overwritten")
    outline.validate_outline()
    tokens.validate_tokens()
    path = build(html_only=args.html, draft=args.draft)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
