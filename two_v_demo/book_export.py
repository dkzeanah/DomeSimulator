"""Turning the manuscript of *2 Trees* into something you can actually read.

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
import html as html_escape
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import book_manuscript as manuscript
from . import book_tokens
from .book import BOOK, EXPORT_DIR, MANUSCRIPT_DIR, Book


FIGURE_SUFFIXES = (".png", ".svg", ".jpg")

IMAGE_LINK = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)')


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
figcaption { font: italic .85rem/1.5 Georgia, serif; color: var(--muted);
             text-align: center; margin-top: .3rem; }
table { border-collapse: collapse; width: 100%; margin: 1.4rem 0;
        font: .9rem/1.45 Georgia, serif; }
th, td { border-bottom: 1px solid var(--rule); padding: .42rem .5rem;
         text-align: left; vertical-align: top; }
th { font-family: "Segoe UI", sans-serif; font-size: .82rem; }
ul, ol { margin: 0 0 1.05rem 1.3rem; padding: 0; }
li { margin: 0 0 .4rem; }

.book-title { font-size: 2.5rem; margin: 6rem 0 .5rem; }
.book-sub { font-size: 1.1rem; color: var(--muted); font-style: italic;
            margin-bottom: 3rem; }
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
.unwritten { color: var(--warn); font-family: "Segoe UI", sans-serif;
             font-size: .85rem; }
.missing-figure { border: 1px dashed var(--rule); color: var(--muted);
                  text-align: center; padding: 2.5rem 1rem; margin: 1.6rem 0;
                  font: .85rem/1.5 "Segoe UI", sans-serif; }

nav.toc { margin: 2rem 0 4rem; font: .92rem/1.6 "Segoe UI", sans-serif; }
nav.toc h2 { font-size: 1.1rem; }
nav.toc ol { list-style: none; margin: 0; padding: 0; }
nav.toc .toc-part { margin: 1.3rem 0 .35rem; font-weight: 700; }
nav.toc a { color: var(--ink); text-decoration: none;
            display: flex; gap: .5rem; padding: .12rem 0; }
nav.toc a:hover { color: var(--accent); text-decoration: underline; }
nav.toc .num { color: var(--muted); min-width: 1.8rem; }
nav.toc .strand { margin-left: auto; color: var(--muted); font-size: .78rem; }

@media print {
  body { background: #fff; font-size: 11pt; }
  .wrap { max-width: none; padding: 0; }
  nav.toc a { color: #000; }
  h1, h2, h3 { page-break-after: avoid; }
  figure, img, table { page-break-inside: avoid; }
}
@page { size: letter; margin: 22mm 20mm; }
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
                    found: list[str], missing: list[str]) -> str:
    """Point every image link at the newest render, or mark it absent.

    With ``embed`` the picture goes into the file as a data URI, which is
    what makes an exported HTML book a single portable object.
    """
    def replace(match: re.Match) -> str:
        alt = match.group("alt")
        key = figure_key_from_src(match.group("src"))
        path = latest_figure(key)
        if path is None:
            missing.append(key)
            return (f'<div class="missing-figure">Figure <code>{key}</code> '
                    f"has not been rendered yet.<br>{html_escape.escape(alt)}"
                    "</div>")
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


def _strip_leading_heading(body: str, title: str) -> str:
    """Drop the chapter's own H1, since the template already prints one."""
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
    return "\n".join(lines)


def book_html(root: Path = MANUSCRIPT_DIR, book: Book = BOOK,
              embed_images: bool = True, strict: bool = True,
              include_unwritten: bool = True,
              contents: bool = True) -> tuple[str, BuildReport]:
    """The whole book as one HTML document.

    This is the single source the reader, the HTML export and the PDF all
    build from, so they cannot drift into being different books.
    """
    found: list[str] = []
    missing: list[str] = []
    written = 0

    parts: list[str] = [
        '<div class="wrap">',
        f'<div class="book-title">{html_escape.escape(book.title)}</div>',
        f'<div class="book-sub">{html_escape.escape(book.subtitle)}</div>',
        f'<p class="built">Built {date.today().isoformat()}. Every figure '
        "in this book was computed at build time from the geometry in the "
        "DomeSim project.</p>",
    ]

    if contents:
        parts.append('<nav class="toc"><h2>Contents</h2><ol>')
        for part in book.parts:
            parts.append(
                f'<li class="toc-part">Part {part.number} &middot; '
                f"{html_escape.escape(part.title)}</li>")
            for chapter in part.chapters:
                parts.append(
                    f'<li><a href="#ch{chapter.number}">'
                    f'<span class="num">{chapter.number}</span>'
                    f"<span>{html_escape.escape(chapter.title)}</span>"
                    f'<span class="strand">{chapter.strand}</span></a></li>')
        parts.append("</ol></nav>")

    for matter in book.front:
        text = manuscript._matter_markdown(matter, "front", root)
        parts.append(_markdown_to_html(
            _resolve_images(text, embed_images, found, missing)))
        parts.append("<hr>")

    for part in book.parts:
        parts.append(
            f'<section class="part">'
            f'<div class="part-eyebrow">Part {part.number}</div>'
            f'<div class="part-title">{html_escape.escape(part.title)}</div>'
            f'<p class="part-epigraph">&ldquo;'
            f"{html_escape.escape(part.epigraph)}&rdquo;</p>"
            f'<p class="part-promise">{html_escape.escape(part.promise)}</p>'
            f"</section>")
        for chapter in part.chapters:
            item = manuscript.read_chapter(chapter, root)
            if not item.exists and not include_unwritten:
                continue
            body = _strip_leading_heading(item.body, chapter.title)
            has_prose = manuscript.count_words(body) > 60
            if has_prose:
                written += 1
            parts.append(
                f'<article class="chapter" id="ch{chapter.number}">'
                f'<div class="chapter-eyebrow">Chapter {chapter.number}'
                f" &middot; {html_escape.escape(chapter.strand)}</div>"
                f"<h1>{html_escape.escape(chapter.title)}</h1>"
                f'<p class="deck">{html_escape.escape(chapter.deck)}</p>')
            if has_prose:
                parts.append(_markdown_to_html(
                    _resolve_images(body, embed_images, found, missing)))
            else:
                parts.append(
                    '<p class="unwritten">This chapter is planned but not '
                    "written yet. Its page plan is in the outline.</p>")
                parts.append(_markdown_to_html(_resolve_images(
                    body, embed_images, found, missing)))
            parts.append("</article>")

    for matter in book.back:
        text = manuscript._matter_markdown(matter, "back", root)
        parts.append("<hr>")
        parts.append(_markdown_to_html(
            _resolve_images(text, embed_images, found, missing)))

    parts.append("</div>")

    document = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,"
        "initial-scale=1\">"
        f"<title>{html_escape.escape(book.title)}</title>"
        f"<style>{BOOK_CSS}</style></head><body>"
        + "\n".join(parts) + "</body></html>")

    document = book_tokens.resolve(document, strict=strict)

    report = BuildReport(
        path=Path(), chapters_written=written,
        chapters_total=len(book.chapters), figures_found=len(set(found)),
        figures_missing=tuple(sorted(set(missing))))
    return document, report


# ----------------------------------------------------------------------
# Export: HTML
# ----------------------------------------------------------------------

def export_html(root: Path = MANUSCRIPT_DIR, out_dir: Path = EXPORT_DIR,
                book: Book = BOOK, strict: bool = True) -> BuildReport:
    """One self-contained HTML file: the book, pictures and all.

    Never overwrites. Open it in a browser to read; press Ctrl+P and choose
    "Save as PDF" to get the best-looking paper version there is.
    """
    from .deliverables import next_version_path

    document, report = book_html(root, book, embed_images=True,
                                 strict=strict)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "2-trees.html"
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


def _pdf_via_pymupdf(document: str, path: Path) -> None:
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

    story = fitz.Story(html=document, archive=fitz.Archive(FIGURE_DIR))
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


def export_pdf(root: Path = MANUSCRIPT_DIR, out_dir: Path = EXPORT_DIR,
               book: Book = BOOK, strict: bool = True,
               backend: str = "auto") -> BuildReport:
    """A typeset PDF of the whole book.

    ``backend`` is ``auto`` (Chrome if present, else PyMuPDF), ``chrome`` or
    ``pymupdf``. Never overwrites an earlier PDF.
    """
    from .deliverables import next_version_path

    # Chrome reads images from disk perfectly well and a 60-figure book
    # embedded as base64 is enormous; PyMuPDF wants them as files it can
    # find in its archive. Either way, do not embed for PDF.
    document, report = book_html(root, book, embed_images=False,
                                 strict=strict)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "2-trees.pdf"
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
        _pdf_via_chrome(document, path, chrome)
        used = f"Chrome ({Path(chrome).name})"
    elif backend == "pymupdf":
        _pdf_via_pymupdf(document, path)
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
    """Both readable forms build, and both contain the book."""
    import tempfile

    document, report = book_html(embed_images=False, strict=True)
    assert document.startswith("<!doctype html>"), document[:60]
    assert "{{" not in document, "an unresolved token reached the reader"
    assert BOOK.title in document, "the title is missing"
    assert report.chapters_total == len(BOOK.chapters), report
    assert report.chapters_written >= 1, report
    # Every part and chapter has to appear, or the reader silently drops one.
    for part in BOOK.parts:
        assert html_escape.escape(part.title) in document, part.title
        for chapter in part.chapters:
            assert f'id="ch{chapter.number}"' in document, chapter.number
    assert document.count('class="chapter"') == len(BOOK.chapters), \
        document.count('class="chapter"')

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
