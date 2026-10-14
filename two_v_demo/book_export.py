"""Turning the manuscript of *Geodesic Dome Wedge Method* into something you can actually read.

A folder of Markdown files is a good way to *write* a book and a poor way to
read one.  This module builds the readable forms:

``html``
    One self-contained file. Every figure is embedded in it, so it can be
    mailed, put on a stick or opened on a machine that has none of this
    project on it, and it will still be whole. Opens in any browser, and any
    browser can print it to PDF -- which is the highest-fidelity route to
    paper there is.

``pdf``
    A typeset PDF, made without a browser. Tries the best backend present:
    headless Chrome if this machine has one, otherwise PyMuPDF's own layout
    engine, which is pure Python and always available. The result says which
    was used, because they do not look identical.

``reader``
    :mod:`book_app` renders the same content in a window, so you can read
    what you have written without exporting anything.

All three build from one place -- :func:`book_html` -- so the thing you read
on screen and the thing you send somebody cannot be different books.

Figures and versions
--------------------
Renders are append-only in this repository: fixing a figure writes ``-v2``
beside the original rather than over it.  That is right for a deliverable and
wrong for a reader, which would otherwise show the first draft of every
picture forever.  :func:`latest_figure` resolves a figure key to the newest
version on disk, so the book you read is always illustrated with the current
drawings while the old ones stay where they are.
"""

from __future__ import annotations

import base64
import hashlib
import html as html_escape
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import book_manuscript as manuscript
from . import book_tokens
from .book import (BOOK, EXPORT_DIR, MANUSCRIPT_DIR, Book, Matter,
                   figure_index)


FIGURE_SUFFIXES = (".png", ".svg", ".jpg")

IMAGE_LINK = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)')

MERMAID_FENCE = re.compile(
    r"^[ \t]*```mermaid[ \t]*\r?\n(?P<source>.*?)^[ \t]*```[ \t]*$",
    re.S | re.M)
"""A fenced ```mermaid block in the manuscript.

Chapter and matter files are Markdown, and Markdown's own fence syntax is
where a diagram belongs: the source stays readable in the manuscript,
renders on GitHub, and is turned into a picture here.  The fence is
matched *including* its backticks so the whole block can be replaced by
the drawn diagram before Markdown ever sees it -- Python-Markdown would
otherwise print the fence as literal text.
"""

BOX_FENCE = re.compile(
    r'^:::box[ \t]+(?P<kind>[a-z][a-z0-9-]*)(?:[ \t]+"(?P<label>[^"]*)")?[ \t]*\r?\n'
    r"(?P<body>.*?)^:::[ \t]*$", re.S | re.M)
"""A boxed aside in the manuscript::

    :::box against
    **$16,347 to run $200 of plates.** ...
    :::

The kind picks the box's look and its default label (:data:`BOX_LABELS`); a
quoted label after the kind overrides it. The body is ordinary Markdown."""

BOX_LABELS = {
    "against": "The number that doesn't help",
    "correction": "We got this wrong",
    "clock": "The 40-hour clock",
    "aside": "Aside",
}


def _boxes(text: str) -> str:
    """Replace every ``:::box`` fence with a finished ``<aside>`` block.

    The body is converted here, on its own, and the result is emitted as one
    raw HTML block with no blank line inside it, so Python-Markdown passes it
    through untouched instead of reading the box's contents a second time."""
    def replace(match: re.Match) -> str:
        kind = match.group("kind")
        label = match.group("label") or BOX_LABELS.get(kind, kind.replace("-", " ").title())
        inner = _markdown_to_html(match.group("body")).replace("\n\n", "\n")
        return (f'\n<aside class="box box-{kind}"><div class="box-label">'
                f"{html_escape.escape(label)}</div>{inner}</aside>\n")
    return BOX_FENCE.sub(replace, text)


DIAGRAM_DIR_NAME = "diagrams"
DIAGRAM_TIMEOUT_S = 240
"""Diagrams are rendered to SVG at export time by the ``mmdc`` CLI that
ships in ``node_modules``.  A cache means the second export of the same
diagram is free, and the hash is of the diagram's own source, so editing a
diagram renders a new file rather than trusting a stale one."""



# ----------------------------------------------------------------------
# Finding the current version of a figure
# ----------------------------------------------------------------------

def latest_figure(key: str, directory: Path | None = None) -> Path | None:
    """The newest rendered version of one figure, or None if never drawn.

    ``foo.png``, ``foo-v2.png``, ``foo-v3.png`` are the same figure at three
    ages. A reader wants the newest; the archive keeps the rest.
    """
    from .book_figures import FIGURE_DIR

    directory = directory or FIGURE_DIR
    if not directory.is_dir():
        return None
    candidates: list[Path] = []
    for suffix in FIGURE_SUFFIXES:
        exact = directory / f"{key}{suffix}"
        if exact.exists():
            candidates.append(exact)
        candidates.extend(directory.glob(f"{key}-v*{suffix}"))
    if not candidates:
        return None
    # Newest by version number where there is one, else by write time.
    def version(path: Path) -> tuple[int, float]:
        match = re.search(r"-v(\d+)$", path.stem)
        return (int(match.group(1)) if match else 1,
                path.stat().st_mtime)
    return max(candidates, key=version)


def figure_key_from_src(src: str) -> str:
    """The figure key a manuscript image link points at."""
    return Path(src.split("?")[0]).stem


# ----------------------------------------------------------------------
# The book's look on screen and on paper
# ----------------------------------------------------------------------

BOOK_CSS = """
:root {
  --ink: #1a1a1a; --paper: #fdfcfa; --rule: #c9c1b4; --muted: #6b6359;
  --accent: #2f5d7c; --warn: #8c2f1f; --measure: 34rem;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font: 16px/1.62 Georgia, "Times New Roman", serif;
  -webkit-text-size-adjust: 100%;
}
.wrap { max-width: var(--measure); margin: 0 auto; padding: 3rem 1.25rem 6rem; }
h1, h2, h3, .part-title, .book-title {
  font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-weight: 700;
  line-height: 1.22; text-wrap: balance;
}
h1 { font-size: 1.9rem; margin: 3.5rem 0 .4rem; }
h2 { font-size: 1.25rem; margin: 2.4rem 0 .5rem; }
h3 { font-size: 1.05rem; margin: 1.8rem 0 .4rem; }
p { margin: 0 0 1.05rem; }
em { font-style: italic; }
blockquote {
  margin: 1.4rem 0; padding: .1rem 0 .1rem 1.1rem;
  border-left: 3px solid var(--rule); color: var(--muted); font-style: italic;
}
code { font: .9em/1.4 Consolas, monospace; background: #efece6;
       padding: .1em .3em; border-radius: 3px; }
hr { border: 0; border-top: 1px solid var(--rule); margin: 3rem 0; }
img { max-width: 100%; height: auto; display: block; margin: 1.6rem auto .5rem; }
figure { margin: 2rem 0; }
figure.diagram { margin: 2.2rem 0; padding: 1rem; background: #fff;
  border: 1px solid var(--rule); border-radius: 3px; page-break-inside: avoid; }
figure.diagram img { margin: 0 auto; }
section.cover { margin: 0; padding: 0; page-break-after: always; }
section.cover h1 { display: none; }
section.cover figure { margin: 0; }
section.cover img { width: 100%; height: auto; margin: 0; }
section.cover figcaption { display: none; }
section.cover + .wrap { padding-top: 2rem; }
pre.mermaid { background: #fff; border: 1px solid var(--rule); padding: 1rem;
  font-size: .78rem; overflow-x: auto; }
figcaption { font: italic .85rem/1.5 Georgia, serif; color: var(--muted);
             text-align: center; margin-top: .3rem; }
table { border-collapse: collapse; width: 100%; margin: 1.4rem 0;
        font: .9rem/1.45 Georgia, serif; }
th, td { border-bottom: 1px solid var(--rule); padding: .42rem .5rem;
         text-align: left; vertical-align: top; }
th { font-family: "Segoe UI", sans-serif; font-size: .82rem; }
ul, ol { margin: 0 0 1.05rem 1.3rem; padding: 0; }
li { margin: 0 0 .4rem; }

aside.box { margin: 1.8rem 0; padding: .9rem 1.1rem .4rem; border: 1px solid var(--rule);
  border-left: 5px solid var(--accent); background: #f5f2ec; border-radius: 3px;
  page-break-inside: avoid; break-inside: avoid; }
aside.box .box-label { font: 700 .72rem/1 "Segoe UI", sans-serif; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent); margin-bottom: .55rem; }
aside.box p { text-align: left; }
aside.box pre { overflow-x: auto; font-size: .78rem; }
aside.box-against { border-left-color: var(--warn); background: #f8efec; }
aside.box-against .box-label { color: var(--warn); }
aside.box-correction { border-left-color: #b8860b; background: #faf5e8; }
aside.box-correction .box-label { color: #8a6508; }
aside.box-clock { border-left-color: #2f6b4a; background: #eef5f0; }
aside.box-clock .box-label { color: #2f6b4a; }
.clockbar { display: block; position: relative; height: .7rem; margin: .35rem 0 .7rem;
  background: #d9e6dd; border-radius: 2px; overflow: hidden; }
.clockbar .done { position: absolute; left: 0; top: 0; bottom: 0; background: #9cc2a8; }
.clockbar .now { position: absolute; top: 0; bottom: 0; background: #2f6b4a; }
.clockbar .week { position: absolute; top: -2px; bottom: -2px; width: 2px; background: #111; }

.book-title { font-size: 2.5rem; margin: 6rem 0 .5rem; }
.book-sub { font-size: 1.1rem; color: var(--muted); font-style: italic;
            margin-bottom: 3rem; }
.book-tagline { font-size: .95rem; color: var(--muted); margin: .6rem 0 0;
  max-width: 30rem; }
.built { font-size: .82rem; color: var(--muted); }

.part { margin: 5rem 0 2rem; padding: 2.4rem 0; border-top: 2px solid var(--ink);
        border-bottom: 1px solid var(--rule); page-break-before: always; }
.part-eyebrow { font: 700 .78rem/1 "Segoe UI", sans-serif;
                letter-spacing: .16em; text-transform: uppercase;
                color: var(--muted); }
.part-title { font-size: 2rem; margin: .5rem 0 1rem; }
.part-epigraph { font-style: italic; color: var(--muted); margin: 0 0 .8rem; }
.part-promise { font-size: .93rem; color: var(--muted); }

.chapter { page-break-before: always; }
.chapter-eyebrow { font: 700 .78rem/1 "Segoe UI", sans-serif;
                   letter-spacing: .16em; text-transform: uppercase;
                   color: var(--accent); margin-top: 3.5rem; }
.deck { font-style: italic; color: var(--muted); margin: 0 0 2rem; }

nav.toc { margin: 2rem 0 4rem; font: .92rem/1.6 "Segoe UI", sans-serif; }
nav.toc h2 { font-size: 1.1rem; }
nav.toc ol { list-style: none; margin: 0; padding: 0; }
nav.toc .toc-part { margin: 1.3rem 0 .35rem; font-weight: 700;
                     display: flex; }
nav.toc .toc-part .pg { margin-left: auto; min-width: 2.2rem;
                         text-align: right; font-weight: 400; }
nav.toc a { color: var(--ink); text-decoration: none;
            display: flex; gap: .5rem; padding: .12rem 0; }
nav.toc a:hover { color: var(--accent); text-decoration: underline; }
nav.toc .num { color: var(--muted); min-width: 1.8rem; }
nav.toc .strand { margin-left: auto; color: var(--muted); font-size: .7rem;
                  letter-spacing: .12em; text-transform: uppercase; }
nav.toc .toc-legend { font-size: .8rem; color: var(--muted);
                       margin: .4rem 0 1.2rem; }
nav.toc .pg { min-width: 2.2rem; text-align: right; color: var(--muted);
              margin-left: .8rem; }

figure.illustration-slot { margin: 2rem 0; page-break-inside: avoid; }
figure.illustration-slot .slot-box { border: 1px dashed var(--rule);
  background: #f7f4ee; min-height: 9rem; display: flex; align-items: center;
  justify-content: center; font: .8rem/1.5 "Segoe UI", sans-serif;
  color: var(--muted); padding: 1rem; }

@media print {
  body { background: #fff; font-size: 11pt; }
  .wrap { max-width: none; padding: 0; }
  nav.toc a { color: #000; }
  h1, h2, h3 { page-break-after: avoid; }
  figure, img, table { page-break-inside: avoid; }
  nav.toc { page-break-after: always; }
  section.matter-title { page-break-after: always; }
  section.matter-orientation { page-break-after: avoid; }
  section.matter-software { page-break-after: avoid; }
}
/* The print interior: numbered pages and a gutter. Chrome honours the
   page margin boxes; the PyMuPDF fallback simply ignores them. The
   contents page's numbers come from a two-pass render -- Chrome cannot
   resolve target-counter(), so the first pass drops an invisible marker
   beside every chapter and part, the pages are read back, and the second
   pass prints real numbers into the contents list. */
@page { size: letter; margin: 20mm 18mm 22mm; }
@page :left {
  margin-left: 24mm; margin-right: 18mm;
  @bottom-center { content: counter(page);
                   font: 9pt "Segoe UI", sans-serif; color: #6b6359; }
}
@page :right {
  margin-left: 18mm; margin-right: 24mm;
  @bottom-center { content: counter(page);
                   font: 9pt "Segoe UI", sans-serif; color: #6b6359; }
}
span.pgmark { color: transparent; font-size: 5pt; position: absolute; }
"""


# ----------------------------------------------------------------------
# Building the HTML
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BuildReport:
    """What an export actually managed to include."""

    path: Path
    chapters_written: int
    chapters_total: int
    figures_found: int
    figures_missing: tuple[str, ...]
    backend: str = ""

    @property
    def summary(self) -> str:
        missing = (f", {len(self.figures_missing)} figures not rendered yet"
                   if self.figures_missing else "")
        backend = f" via {self.backend}" if self.backend else ""
        return (f"{self.path.name}{backend}: "
                f"{self.chapters_written}/{self.chapters_total} chapters "
                f"written, {self.figures_found} figures{missing}")


def _markdown_to_html(text: str) -> str:
    """Markdown to HTML, with the extensions a book actually uses."""
    import markdown
    return markdown.markdown(
        text, extensions=["tables", "sane_lists", "smarty"],
        output_format="html5")


def _resolve_images(text: str, embed: bool,
                    found: list[str], missing: list[str],
                    index: dict | None = None,
                    figure_dir: Path | None = None) -> str:
    """Point every image link at the newest render, or drop it silently.

    ``index`` and ``figure_dir`` belong to the book being built. They default
    to *Geodesic Dome Wedge Method*, which is what every caller wanted when this engine held one
    book.

    A reader's book never shows authoring machinery: a figure that has not
    been rendered yet, or a photograph the author has not taken, is simply
    absent from the page. The writing desk (``book_app``) is where a missing
    figure is reported; the export is where it is not.

    With ``embed`` the picture goes into the file as a data URI, which is
    what makes an exported HTML book a single portable object.
    """
    def replace(match: re.Match) -> str:
        alt = match.group("alt")
        key = figure_key_from_src(match.group("src"))
        path = latest_figure(key, figure_dir)
        spec = (index if index is not None else figure_index(BOOK)).get(key)
        if path is None and spec is not None \
                and spec.source == "illustration_slot":
            # A commissioned illustration not yet delivered: the Amazon
            # book prints a captioned slot so the page plan is visible
            # in a proof, and the picture itself drops in under the same
            # key once it exists -- the caption stays, marked as an
            # illustration rather than a photograph.
            caption = html_escape.escape(alt)
            return (f'<figure class="illustration-slot">'
                    f'<div class="slot-box">Illustration &middot; '
                    f"{caption}</div>"
                    f"<figcaption>{caption}</figcaption></figure>")
        if path is None:
            missing.append(key)
            return ""
        if spec is not None and spec.source == "photo_slot":
            # A photograph slot is a shot the author still has to take.
            missing.append(key)
            return ""
        found.append(key)
        if embed:
            mime = ("image/svg+xml" if path.suffix == ".svg"
                    else f"image/{path.suffix.lstrip('.')}")
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            src = f"data:{mime};base64,{data}"
        else:
            src = path.resolve().as_uri()
        caption = html_escape.escape(alt)
        return (f'<figure><img src="{src}" alt="{caption}">'
                f"<figcaption>{caption}</figcaption></figure>")
    return IMAGE_LINK.sub(replace, text)


def _mmdc_command() -> list[str] | None:
    """The mermaid CLI, if this machine can draw a diagram.

    Checked in order: whatever is on PATH, then the copy inside this
    project's own ``node_modules``, which is where the book's build
    expects it because the repository already uses Node for one
    deliverable's build script.
    """
    found = shutil.which("mmdc")
    if found:
        return [found]
    from .book import ROOT

    for name in ("mmdc.cmd", "mmdc"):
        local = ROOT / "node_modules" / ".bin" / name
        if local.is_file():
            return [str(local)]
    return None


def render_diagram(source: str, cache_dir: Path | None = None) -> Path | None:
    """One mermaid diagram, drawn to a cached SVG. ``None`` if it cannot be.

    The cache is keyed on the diagram's own text, so a diagram that has
    not changed is not redrawn, and a diagram that has changed cannot
    silently reuse the old picture.  A failure here is never fatal: the
    caller falls back to the live-rendering path, which is what a machine
    without Node gets.
    """
    command = _mmdc_command()
    if command is None:
        return None
    cache_dir = cache_dir or (EXPORT_DIR / DIAGRAM_DIR_NAME)
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.strip().encode("utf-8")).hexdigest()[:16]
    svg = cache_dir / f"mermaid-{digest}.svg"
    if svg.is_file() and svg.stat().st_size > 200:
        return svg
    seeded = cache_dir / f"mermaid-{digest}.mmd"
    seeded.write_text(source, encoding="utf-8")
    try:
        result = subprocess.run(
            command + ["-i", str(seeded), "-o", str(svg),
                       "-t", "neutral", "-b", "transparent"],
            capture_output=True, text=True, timeout=DIAGRAM_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not svg.is_file():
        return None
    return svg


def _mermaid_blocks(text: str, embed: bool, live: list[str],
                    cache_dir: Path | None = None) -> str:
    """Replace every ```mermaid fence with the drawn diagram.

    With the CLI present each diagram becomes an SVG, embedded as a data
    URI like every other figure in this book, so the exported HTML stays
    one self-contained file and the PDF needs no JavaScript. Without the
    CLI the fence becomes a ``<pre class="mermaid">`` block and the
    runtime is added to the document instead, so the diagram still draws
    in a browser.
    """
    def replace(match: re.Match) -> str:
        source = match.group("source")
        path = render_diagram(source, cache_dir)
        if path is None:
            live.append(source)
            return (f'<pre class="mermaid">'
                    f"{html_escape.escape(source.strip())}</pre>")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        src = (f"data:image/svg+xml;base64,{data}" if embed
               else path.resolve().as_uri())
        return (f'<figure class="diagram">'
                f'<img src="{src}" alt="DomeSim code map diagram">'
                f"</figure>")

    return MERMAID_FENCE.sub(replace, text)


def _mermaid_runtime() -> str:
    """The browser-side fallback: mermaid itself, inlined when present."""
    from .book import ROOT

    script = ROOT / "node_modules" / "mermaid" / "dist" / "mermaid.min.js"
    if script.is_file():
        return (f"<script>{script.read_text(encoding='utf-8')}</script>"
                "<script>mermaid.initialize({startOnLoad: true, "
                "theme: 'neutral'});</script>")
    return ('<script type="module">import mermaid from '
            '"https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
            "mermaid.initialize({startOnLoad: true, theme: 'neutral'});"
            "</script>")


def _strip_leading_heading(body: str, title: str) -> str:
    """Drop the chapter's own H1, since the template already prints one.

    The scaffold also repeats the chapter title as the first section
    heading, so a chapter whose file starts with ``# 9. Title`` /
    ``## Title`` would otherwise print the title twice on its opening
    page. Both are stripped here; the template's H1 and deck are what
    the reader sees."""
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines.pop(0)
        # And the deck immediately under it, which the template also prints.
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and lines[0].startswith("*") and lines[0].endswith("*"):
            lines.pop(0)
    # The repeated title as the first section heading.
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("## "):
        heading = lines[0][3:].strip().lower()
        if heading == title.lower():
            lines.pop(0)
    return "\n".join(lines)


def book_html(root: Path = MANUSCRIPT_DIR, book: Book = BOOK,
              embed_images: bool = True, strict: bool = True,
              include_unwritten: bool = False,
              contents: bool = True,
              figure_dir: Path | None = None,
              tokens=None,
              page_map: dict[str, int] | None = None,
              page_markers: bool = False) -> tuple[str, BuildReport]:
    """The whole book as one HTML document.

    This is the single source the reader, the HTML export and the PDF all
    build from, so they cannot drift into being different books.

    The export is a reader's artifact, not the writing desk: chapters and
    matter with no prose in them are omitted rather than marked, so a
    published copy never shows "(not written yet)" or any other authoring
    trace. ``include_unwritten=True`` restores the working view for the
    desk, and is off by default.
    """
    found: list[str] = []
    missing: list[str] = []
    live_diagrams: list[str] = []
    written = 0
    index = figure_index(book)

    def images(body: str) -> str:
        drawn = _mermaid_blocks(body, embed_images, live_diagrams)
        return _boxes(_resolve_images(drawn, embed_images, found, missing,
                                      index, figure_dir))

    # The cover is the front of the book, so it is assembled first and
    # placed outside the reading column: full width, no page furniture, and
    # a page break after it, so the title page and the contents follow it
    # rather than preceding it.
    cover_html = ""
    cover_matter = next((m for m in book.front if m.key == "cover"), None)
    if cover_matter is not None:
        cover_text = manuscript._matter_markdown(cover_matter, "front", root)
        if cover_text.strip() or include_unwritten:
            cover_html = ('<section class="cover">'
                          f"{_markdown_to_html(images(cover_text))}</section>")

    parts: list[str] = ['<div class="wrap">']

    # The contents list names only what the book actually contains: a
    # reader who follows a link must always land on a written chapter.
    # "Written" is the author's own declaration -- the manuscript file's
    # status, anything beyond the untouched outline scaffold.
    written_chapters = [
        chapter for chapter in book.chapters
        if manuscript.read_chapter(chapter, root).is_started]

    def toc_html() -> str:
        out = ['<nav class="toc"><h2>Contents</h2>',
               '<p class="toc-legend">Reading tracks: '
               '<strong>story</strong> what happened &middot; '
               '<strong>howto</strong> the manual &middot; '
               '<strong>explain</strong> why it works &middot; '
               '<strong>reference</strong> the tables.</p><ol>']
        for part in book.parts:
            listed = [chapter for chapter in part.chapters
                      if chapter in written_chapters]
            if not listed and not include_unwritten:
                continue
            part_page = (page_map or {}).get(f"part{part.number}", "")
            out.append(
                f'<li class="toc-part">Part {part.number} &middot; '
                f"{html_escape.escape(part.title)}"
                f'<span class="pg">{part_page}</span></li>')
            for chapter in listed:
                chapter_page = (page_map or {}).get(f"ch{chapter.number}", "")
                out.append(
                    f'<li><a href="#ch{chapter.number}">'
                    f'<span class="num">{chapter.number}</span>'
                    f"<span>{html_escape.escape(chapter.title)}</span>"
                    f'<span class="strand">{chapter.strand}</span>'
                    f'<span class="pg">{chapter_page}</span></a></li>')
        out.append("</ol></nav>")
        return "\n".join(out)

    def matter_html(matter: Matter, where: str) -> str:
        text = manuscript._matter_markdown(matter, where, root)
        if not text.strip() and not include_unwritten:
            return ""
        return (f'<section class="matter matter-{matter.key}">'
                f"{_markdown_to_html(images(text))}"
                "</section>")

    # The title pages come first -- the Amazon interior has no cover page,
    # and a contents page before a title page is a screen-document habit,
    # not a book. Then the contents, then the orientation pages.
    for matter in book.front:
        if matter.key == "cover":
            continue          # gone from the interior; uploaded separately
        if matter.key == "title":
            parts.append(matter_html(matter, "front"))
            if contents:
                parts.append(toc_html())
        else:
            parts.append(matter_html(matter, "front"))

    for part in book.parts:
        included = [chapter for chapter in part.chapters
                    if chapter in written_chapters]
        if not included and not include_unwritten:
            continue
        parts.append(
            f'<section class="part">'
            f'<div class="part-eyebrow">Part {part.number}</div>'
            f'<div class="part-title">{html_escape.escape(part.title)}</div>'
            f'<p class="part-epigraph">&ldquo;'
            f"{html_escape.escape(part.epigraph)}&rdquo;</p>"
            f'<p class="part-promise">{html_escape.escape(part.promise)}</p>'
            + (f'<span class="pgmark">pgx-part{part.number}</span>'
               if page_markers else "")
            + "</section>")
        for chapter in part.chapters:
            item = manuscript.read_chapter(chapter, root)
            body = _strip_leading_heading(item.body, chapter.title)
            has_prose = item.is_started
            if not has_prose and not include_unwritten:
                continue
            if has_prose:
                written += 1
            parts.append(
                f'<article class="chapter" id="ch{chapter.number}">'
                f'<div class="chapter-eyebrow">Chapter {chapter.number}'
                f" &middot; {html_escape.escape(chapter.strand)}</div>"
                f"<h1>{html_escape.escape(chapter.title)}</h1>"
                f'<p class="deck">{html_escape.escape(chapter.deck)}</p>'
                + (f'<span class="pgmark">pgx-ch{chapter.number}</span>'
                   if page_markers else ""))
            if has_prose:
                # The scaffold's page-plan comments are for the desk, not
                # the reader; a published copy carries prose only.
                parts.append(_markdown_to_html(
                    images(manuscript.HTML_COMMENT.sub("", body))))
            else:
                parts.append(
                    '<p class="unwritten">This chapter is planned but not '
                    "written yet. Its page plan is in the outline.</p>")
                parts.append(_markdown_to_html(images(body)))
            parts.append("</article>")

    for matter in book.back:
        section = matter_html(matter, "back")
        if section:
            parts.append(section)

    parts.append("</div>")

    full_title = (f"{book.title}: {book.subtitle}" if book.subtitle
                  else book.title)
    document = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,"
        "initial-scale=1\">"
        "<meta name=\"author\" content=\"Donovan Zeanah\">"
        "<meta name=\"description\" content=\""
        f"{html_escape.escape(book.tagline or '')}\">"
        f"<title>{html_escape.escape(full_title)}</title>"
        f"<style>{BOOK_CSS}</style></head><body>"
        + cover_html
        + "\n".join(parts)
        + (_mermaid_runtime() if live_diagrams else "")
        + "</body></html>")

    resolve = tokens if tokens is not None else book_tokens.resolve
    document = resolve(document, strict=strict)

    report = BuildReport(
        path=Path(), chapters_written=written,
        chapters_total=len(book.chapters), figures_found=len(set(found)),
        figures_missing=tuple(sorted(set(missing))))
    return document, report


# ----------------------------------------------------------------------
# Export: HTML
# ----------------------------------------------------------------------

def export_html(root: Path = MANUSCRIPT_DIR, out_dir: Path = EXPORT_DIR,
                book: Book = BOOK, strict: bool = True,
                stem: str = "2-trees", figure_dir: Path | None = None,
                tokens=None) -> BuildReport:
    """One self-contained HTML file: the book, pictures and all.

    Never overwrites. Open it in a browser to read; press Ctrl+P and choose
    "Save as PDF" to get the best-looking paper version there is.
    """
    from .deliverables import next_version_path

    document, report = book_html(root, book, embed_images=True,
                                 strict=strict, figure_dir=figure_dir,
                                 tokens=tokens)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.html"
    if path.exists():
        path = next_version_path(path)
    path.write_text(document, encoding="utf-8")
    return BuildReport(path=path, chapters_written=report.chapters_written,
                       chapters_total=report.chapters_total,
                       figures_found=report.figures_found,
                       figures_missing=report.figures_missing,
                       backend="self-contained HTML")


# ----------------------------------------------------------------------
# Export: PDF
# ----------------------------------------------------------------------

def _chrome_path() -> str | None:
    """A headless-capable Chrome, if this machine has one.

    Checked in order: whatever is on PATH, then the path this project's
    puppeteer config already points at, then the usual Windows locations.
    """
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    from .book import ROOT
    config = ROOT / ".puppeteerrc.json"
    if config.is_file():
        import json
        try:
            candidate = json.loads(
                config.read_text(encoding="utf-8")).get("executablePath")
        except (OSError, json.JSONDecodeError):
            candidate = None
        if candidate and Path(candidate).is_file():
            return candidate
    for candidate in (
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if Path(candidate).is_file():
            return candidate
    return None


def _stamp_pdf_metadata(path: Path, book: Book) -> None:
    """Set the PDF's title and author, which Chrome does not carry over
    from the HTML's own meta tags. KDP matches the author on the file to
    the author on the listing, so the interior must say the same name as
    the store page."""
    import os
    import fitz

    full_title = (f"{book.title}: {book.subtitle}" if book.subtitle
                  else book.title)
    document = fitz.open(str(path))
    document.set_metadata({
        "title": full_title,
        "author": "Donovan Zeanah",
        "subject": book.tagline,
        "creator": "DomeSim two_v_demo.book_export",
        "producer": "DomeSim two_v_demo.book_export",
    })
    scratch = path.with_name(path.name + ".meta.tmp")
    document.save(str(scratch), garbage=4, deflate=True)
    document.close()
    os.replace(scratch, path)


def _pdf_via_chrome(document: str, path: Path, chrome: str) -> None:
    """Print the HTML with a real browser engine.

    The best-looking route by a distance: the CSS in this module was written
    for a browser, and a browser is what honours it -- page breaks before
    chapters, balanced headings, the lot.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        source = Path(scratch) / "book.html"
        source.write_text(document, encoding="utf-8")
        profile = Path(scratch) / "profile"
        result = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             f"--user-data-dir={profile}",
             "--no-pdf-header-footer",
             "--print-to-pdf-no-header",
             f"--print-to-pdf={path}", source.as_uri()],
            capture_output=True, text=True, timeout=600)
        if not path.exists():
            raise RuntimeError(
                "Chrome did not produce a PDF. "
                + (result.stderr or result.stdout or "no output")[-500:])


def _pdf_via_pymupdf(document: str, path: Path,
                     archive: Path | None = None) -> None:
    """Lay the book out with PyMuPDF's own engine.

    Pure Python and always available, so this is the fallback that means a
    PDF can always be produced. It understands a useful subset of CSS -- less
    than a browser, so the result is plainer, but it is a real book.
    """
    import fitz
    from .book_figures import FIGURE_DIR

    page = fitz.paper_rect("letter")
    margin = 54  # three quarters of an inch
    frame = page + (margin, margin, -margin, -margin)

    story = fitz.Story(html=document,
                       archive=fitz.Archive(archive or FIGURE_DIR))
    writer = fitz.DocumentWriter(str(path))
    more, pages = 1, 0
    while more:
        device = writer.begin_page(page)
        more, _filled = story.place(frame)
        story.draw(device)
        writer.end_page()
        pages += 1
        if pages > 2000:
            raise RuntimeError(
                "layout did not terminate after 2000 pages; something in "
                "the HTML is not being consumed")
    writer.close()


def _read_page_markers(pdf: Path) -> dict[str, int]:
    """Which PDF page each invisible ``pgx-*`` marker landed on.

    Chrome cannot resolve ``target-counter()``, so the contents list gets
    its page numbers the honest way: a first pass prints an invisible
    marker beside every chapter and part, this reads them back, and the
    second pass sets the numbers for real. Page 1 is the first sheet of
    the PDF, which is what Chrome's own ``counter(page)`` prints.
    """
    import fitz
    document = fitz.open(str(pdf))
    page_map: dict[str, int] = {}
    marker = re.compile(r"pgx-(part\d+|ch\d+)")
    for index in range(len(document)):
        for match in marker.findall(document[index].get_text()):
            page_map.setdefault(match, index + 1)
    document.close()
    return page_map


def export_pdf(root: Path = MANUSCRIPT_DIR, out_dir: Path = EXPORT_DIR,
               book: Book = BOOK, strict: bool = True,
               backend: str = "auto", stem: str = "2-trees",
               figure_dir: Path | None = None, tokens=None) -> BuildReport:
    """A typeset PDF of the whole book.

    ``backend`` is ``auto`` (Chrome if present, else PyMuPDF), ``chrome`` or
    ``pymupdf``. Never overwrites an earlier PDF.
    """
    from .deliverables import next_version_path

    # Chrome reads images from disk perfectly well and a 60-figure book
    # embedded as base64 is enormous; PyMuPDF wants them as files it can
    # find in its archive. Either way, do not embed for PDF.
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.pdf"
    if path.exists():
        path = next_version_path(path)

    chrome = _chrome_path()
    if backend == "auto":
        backend = "chrome" if chrome else "pymupdf"

    if backend == "chrome":
        if not chrome:
            raise RuntimeError(
                "no Chrome or Edge found to print with. Use backend "
                "'pymupdf', or export HTML and print it from your own "
                "browser with Ctrl+P.")
        # Pass one: markers beside every chapter and part, read back into
        # page numbers. Pass two prints the contents list with real
        # numbers beside each title.
        import tempfile
        with tempfile.TemporaryDirectory() as scratch:
            scratch = Path(scratch)
            pass1, _ = book_html(root, book, embed_images=False,
                                 strict=strict, figure_dir=figure_dir,
                                 tokens=tokens, page_markers=True)
            first = scratch / "pass1.pdf"
            _pdf_via_chrome(pass1, first, chrome)
            page_map = _read_page_markers(first)
        document, report = book_html(root, book, embed_images=False,
                                     strict=strict, figure_dir=figure_dir,
                                     tokens=tokens, page_map=page_map)
        _pdf_via_chrome(document, path, chrome)
        _stamp_pdf_metadata(path, book)
        used = f"Chrome ({Path(chrome).name}), "
        used += (f"contents page-numbered ({len(page_map)} entries)"
                 if page_map else "contents without page numbers")
    elif backend == "pymupdf":
        document, report = book_html(root, book, embed_images=False,
                                     strict=strict, figure_dir=figure_dir,
                                     tokens=tokens)
        _pdf_via_pymupdf(document, path, figure_dir)
        used = "PyMuPDF"
    else:
        raise ValueError(f"unknown backend {backend!r}; "
                         "choose auto, chrome or pymupdf")

    return BuildReport(path=path, chapters_written=report.chapters_written,
                       chapters_total=report.chapters_total,
                       figures_found=report.figures_found,
                       figures_missing=report.figures_missing,
                       backend=used)


def available_backends() -> tuple[str, ...]:
    """Which PDF routes this machine can actually take."""
    backends = ["pymupdf"]
    if _chrome_path():
        backends.insert(0, "chrome")
    return tuple(backends)


# ----------------------------------------------------------------------
# The self-test
# ----------------------------------------------------------------------

def validate_export() -> None:
    """Both readable forms build, and both contain the book.

    The exported book is the reader's copy: every chapter with prose appears,
    unwritten chapters are absent rather than marked, and no authoring
    machinery ("not written yet", missing-figure cards) ever reaches it.
    """
    import tempfile

    document, report = book_html(embed_images=False, strict=True)
    assert document.startswith("<!doctype html>"), document[:60]
    assert "{{" not in document, "an unresolved token reached the reader"
    assert BOOK.title in document, "the title is missing"
    assert report.chapters_total == len(BOOK.chapters), report
    assert report.chapters_written >= 1, report

    # Every written chapter appears; every unwritten one is gone, with no
    # authoring-trace banner left behind anywhere.
    written_ids = {f'id="ch{chapter.number}"'
                   for chapter in BOOK.chapters
                   if manuscript.read_chapter(chapter).is_started}
    assert written_ids, "no chapter has prose, so nothing can be checked"
    for chapter in BOOK.chapters:
        marker = f'id="ch{chapter.number}"'
        if marker in written_ids:
            assert marker in document, chapter.number
        else:
            assert marker not in document, (
                f"unwritten chapter {chapter.number} leaked into the export")
    assert document.count('class="chapter"') == len(written_ids), \
        document.count('class="chapter"')
    assert "not written yet" not in document, "an authoring banner leaked"
    assert "has not been rendered" not in document, \
        "a missing-figure card leaked"
    assert "PHOTOGRAPH" not in document, "a photograph slot leaked"

    # Embedding really embeds, and produces a bigger, portable document.
    embedded, _ = book_html(embed_images=True, strict=True)
    assert "data:image/png;base64," in embedded, "nothing was embedded"
    assert len(embedded) > len(document), (len(embedded), len(document))

    # Figures resolve to their newest version rather than the first render.
    from .book_figures import FIGURE_DIR
    if FIGURE_DIR.is_dir():
        for key in ("middlemen-chain", "seam-schedule"):
            newest = latest_figure(key)
            if newest is not None:
                assert newest.exists(), newest

    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch)
        html_report = export_html(out_dir=out)
        assert html_report.path.exists(), html_report
        assert html_report.path.stat().st_size > 200_000, \
            html_report.path.stat().st_size
        # A second export versions rather than replacing.
        again = export_html(out_dir=out)
        assert again.path != html_report.path, again
        assert html_report.path.exists(), "the first HTML export was lost"

    print(f"book_export OK: {report.chapters_written} of "
          f"{report.chapters_total} chapters written, "
          f"{report.figures_found} figures placed, "
          f"{len(report.figures_missing)} not yet rendered; "
          f"PDF backends: {', '.join(available_backends())}")


if __name__ == "__main__":
    validate_export()
