"""Build *'Square' on Demand* -- the small book on building with wedge lumber.

    py -3.12 -m square_book.build              # a new numbered PDF in deliverables/book/
    py -3.12 -m square_book.build --check      # the manuscript guards only
    py -3.12 -m square_book.build --draft X    # a proof, outside deliverables/

The manuscript is ``books/square-on-demand/manuscript/*.md``, one chapter a file, in file
order. Two markers sit on lines of their own:

* ``[[figure:key|caption]]`` -- a drawing from :mod:`square_book.figures`,
  to scale, from the same geometry as the tables;
* ``[[image:file.png|caption]]`` -- a render from the Complete Edition's figures.

Every number is a token (:mod:`square_book.tokens`). The guards refuse an
unresolved token, a digit typed into the prose, a froe, a contents line with no
page number, and a print that Chrome shrank.
"""

from __future__ import annotations

import html as html_escape
import re
import tempfile
from pathlib import Path

from two_v_demo import book_export
from two_v_demo.deliverables import next_version_path

from . import figures, geometry, tokens

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "books/square-on-demand" / "manuscript"
IMAGES = ROOT / "books/the-40-hour-cabin" / "figures"
EXPORT_DIR = ROOT / "deliverables" / "book"
STEM = "square-on-demand"
TITLE = "‘Square’ on Demand"
SUBTITLE = "Building with wedge-shaped lumber"
AUTHOR = "Donovan Zeanah"
E = html_escape.escape
PLACEHOLDER = "000"

MARKER = re.compile(r"^\[\[(figure|image):([^|\]]+)\|([^\]]+)\]\]\s*$", re.M)
#: Digits the prose may carry without a token: lumber's names, not figures.
ALLOWED_DIGITS = re.compile(r"\b\dx\d\b|\b[23]V\b")


def chapters() -> list[Path]:
    return sorted(MANUSCRIPT.glob("*.md"))


def typed_digits(raw: str) -> list[str]:
    """Digits in the prose that no token, marker or code block accounts for."""
    text = re.sub(r"\{\{[a-z_]+\.[a-z_0-9]+\}\}", " ", raw)
    text = MARKER.sub(" ", text)
    text = "\n".join(line for line in text.splitlines() if not line.startswith("    "))
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"^\d+\.\s", " ", text, flags=re.M)          # numbered steps
    text = ALLOWED_DIGITS.sub(" ", text)
    return re.findall(r"\S*\d\S*", text)


def check_manuscript() -> list[str]:
    problems = []
    for path in chapters():
        raw = path.read_text(encoding="utf-8")
        for stray in typed_digits(raw):
            problems.append(f"{path.name}: a typed number, not a token: {stray!r}")
        if re.search(r"\bfroe\b", raw, re.I):
            problems.append(f"{path.name}: names a froe; the split is a chainsaw rip")
        for kind, key, _cap in MARKER.findall(raw):
            if kind == "figure" and key not in figures.FIGURES:
                problems.append(f"{path.name}: no drawing called {key!r}")
            if kind == "image" and not (IMAGES / key).is_file():
                problems.append(f"{path.name}: no image {key}")
        try:
            filled = tokens.resolve(raw, strict=True)
        except KeyError as exc:
            problems.append(f"{path.name}: {exc}")
            continue
        if "{{" in filled:
            problems.append(f"{path.name}: an unresolved token")
    return problems


def _figure(kind: str, key: str, caption: str) -> str:
    if kind == "figure":
        art = figures.FIGURES[key]()
    else:
        art = f'<img src="{(IMAGES / key).resolve().as_uri()}" alt="{E(caption)}">'
    return f"<figure>{art}<figcaption>{E(caption)}</figcaption></figure>"


def chapter_html(number: int, path: Path) -> tuple[str, str]:
    """(title, the chapter as HTML)."""
    from wedge_book import print_edition as pe

    raw = path.read_text(encoding="utf-8")

    # A table token on an indented line is a code block in Markdown only if every
    # line of its value carries the same indent.
    def indent(m: re.Match) -> str:
        pad, name = m.group(1), m.group(2)
        value = tokens.resolve("{{" + name + "}}", strict=True)
        return "\n".join(pad + line for line in value.splitlines())

    raw = re.sub(r"^( {4,})\{\{([a-z_]+\.[a-z_0-9]+)\}\}\s*$", indent, raw, flags=re.M)
    text = tokens.resolve(raw, strict=True)
    held: list[str] = []

    def hold(m: re.Match) -> str:
        held.append(_figure(m.group(1), m.group(2), m.group(3)))
        return f"\n\n@@FIG{len(held) - 1}@@\n\n"

    text = MARKER.sub(hold, text)
    title = re.search(r"^#\s+(.+)$", text, re.M).group(1).strip()
    text = re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M)
    body = book_export._markdown_to_html(book_export._boxes(text))
    body = pe.typeset_preformatted(body)
    for i, fig in enumerate(held):
        body = re.sub(rf"<p>\s*@@FIG{i}@@\s*</p>", fig, body)
    eyebrow = "Before you begin" if number == 0 else ("At the back" if path.stem.startswith("99")
                                                         else f"Chapter {number}")
    return title, (f'<article class="chapter sq" id="ch-{number}">'
                   f'<div class="chapter-eyebrow">{E(eyebrow)}</div><h1>{E(title)}</h1>{body}</article>')


CSS = """
:root { --bark: #8a6a4a; --ink: #1d1d1b; --ink-2: #333333; --paper: #ffffff; --wood-1: #e2b98f;
        --wood-2: #c98a4b; --accent: #b0601e; --accent-soft: #f0cfa8; --water: #8fb8d9; --muted: #9a948a; }
.sq-title { page: front; text-align: center; padding-top: 1.2in; break-after: page; }
.sq-title h1 { font: 800 40pt/1.05 "Segoe UI", sans-serif; margin: 0; letter-spacing: -.01em; }
.sq-title .sub { font: italic 17pt/1.3 Georgia, serif; color: #444; margin: .2in 0 .5in; }
.sq-title .author { font: 700 13pt "Segoe UI", sans-serif; letter-spacing: .22em; text-transform: uppercase;
                    margin-top: .5in; }
.sq-title svg.fig { max-height: 3.6in; }
.sq-proof { page: front; padding-top: 5.6in; font-size: 9pt; line-height: 1.5; break-after: page; }
.sq-proof p { text-align: left; }
.sq-contents { page: front; break-after: page; }
.sq-contents h1 { font-size: 20pt; margin: 0 0 .25in; }
.sq-contents ol { list-style: none; padding: 0; margin: 0; }
.sq-contents a { display: flex; gap: .08in; color: #111; text-decoration: none; font: 11pt/2 Georgia, serif; }
.sq-contents .n { min-width: .5in; font: 700 8pt/2.7 "Segoe UI", sans-serif; letter-spacing: .08em;
                  color: #777; text-transform: uppercase; }
.sq-contents .dots { flex: 1; border-bottom: 1px dotted #999; transform: translateY(-.45em); }
article.sq { break-before: page; }
figure { margin: .14in 0; text-align: center; break-inside: avoid; }
figure img { max-width: 5.3in; }
figcaption { font: italic 8.6pt/1.4 Georgia, serif; color: #555; margin-top: .04in; text-align: center; }
"""


def contents_html(titles: list[tuple[int, str, str]], pages: dict[str, int]) -> str:
    rows = []
    for number, eyebrow, title in titles:
        anchor = f"ch-{number}"
        rows.append(f'<li><a href="#{anchor}"><span class="n">{E(eyebrow)}</span><span>{E(title)}</span>'
                    f'<span class="dots"></span><span>{pages.get(anchor, PLACEHOLDER)}</span></a></li>')
    return f'<section class="sq-contents" id="contents"><h1>Contents</h1><ol>{"".join(rows)}</ol></section>'


def document(pages: dict[str, int]) -> tuple[str, list[tuple[int, str, str]]]:
    from master_book.build import MASTER_CSS
    from master_book.tokens import tokens as mb_tokens
    from wedge_book import print_edition as pe

    built = mb_tokens()["mb.built"].value()
    parts, titles = [], []
    for number, path in enumerate(chapters()):
        title, html = chapter_html(number, path)
        eyebrow = "Front" if number == 0 else ("Back" if path.stem.startswith("99") else f"{number:02d}")
        titles.append((number, eyebrow, title))
        parts.append(html)
    head = (f'<section class="sq-title"><h1>{E(TITLE)}</h1><p class="sub">{E(SUBTITLE)}</p>'
            f"{figures.fig_slant()}<p class=\"author\">{E(AUTHOR)}</p></section>"
            '<section class="sq-proof">'
            f"<p><strong>{E(TITLE)}: {E(SUBTITLE)}</strong></p>"
            f"<p>Copyright &copy; {E(built[-4:])} {E(AUTHOR)}. Draft for review.</p>"
            f"<p>Built {E(built)} by the DomeSim project&rsquo;s own software; every figure is computed "
            "from the geometry of a split log, and the few that are declared are listed at the back.</p>"
            "<p>This book describes methods, not rated structures. Members made from paired wedges are not "
            "graded lumber. Anything that carries people, snow or wind is checked by a licensed engineer "
            "before it is built.</p>"
            f"<p>{E(pe.PROJECT_URL)}</p></section>")
    styles = book_export.BOOK_CSS + pe.PRINT_CSS + MASTER_CSS + figures.CSS + CSS
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{E(TITLE)}</title>'
            f"<style>{styles}</style></head><body><main class=\"wrap\">"
            + head + contents_html(titles, pages) + "".join(parts) + "</main></body></html>")
    return pe.cap_figures(page), titles


def check_pdf(path: Path, titles: list[tuple[int, str, str]]) -> list[str]:
    import pymupdf

    from wedge_book import print_edition as pe

    problems = []
    doc = pymupdf.open(path)
    shrunk = pe.scale_problem(doc)
    if shrunk:
        problems.append(shrunk)
    contents = next((i for i in range(min(6, len(doc))) if "Contents" in doc[i].get_text()), None)
    if contents is not None and re.search(r"(?<![\d,.])000(?![\d,])", doc[contents].get_text()):
        problems.append("the contents still prints a placeholder page number")
    doc.close()
    return problems


def build(draft: Path | None = None) -> Path:
    import pymupdf

    from master_book.build import measure

    geometry.validate()
    found = check_manuscript()
    if found:
        raise RuntimeError("manuscript problems:\n  " + "\n  ".join(found))
    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the book needs Chrome or Edge to print with")
    pages: dict[str, int] = {}
    with tempfile.TemporaryDirectory() as scratch:
        working = Path(scratch) / "pass.pdf"
        for attempt in range(1, 5):
            page, titles = document(pages)
            if working.exists():
                working.unlink()
            book_export._pdf_via_chrome(page, working, chrome)
            landed = measure(working)
            need = [f"ch-{n}" for n, _, _ in titles]
            new = {a: landed[a] for a in need if a in landed}
            missing = [a for a in need if a not in new]
            if missing:
                raise RuntimeError(f"chapters the contents could not find: {missing}")
            print(f"  pass {attempt}: {len(pymupdf.open(working))} pages" + (" -- settled" if new == pages else ""))
            if new == pages:
                break
            pages = new
        problems = check_pdf(working, titles)
        if problems:
            raise RuntimeError("; ".join(problems))
        doc = pymupdf.open(working)
        doc.set_metadata({"title": f"{TITLE}: {SUBTITLE}", "author": AUTHOR,
                          "subject": "Building with wedge-shaped lumber: pairing, squaring, shimming, joints",
                          "keywords": "wedge lumber, split log, chainsaw milling, zome, geodesic, veterans"})
        doc.set_toc([[1, "Contents", 3]] + [[1, t if n else "What this book is", pages[f"ch-{n}"]]
                                             for n, _e, t in titles])
        out = draft or next_version_path(EXPORT_DIR / f"{STEM}.pdf")
        doc.save(out, garbage=3, deflate=True)
        doc.close()
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="the manuscript guards only")
    parser.add_argument("--draft", type=Path, metavar="PDF", help="print a proof here, outside deliverables/")
    args = parser.parse_args(argv)
    if args.check:
        geometry.validate()
        found = check_manuscript()
        for p in found:
            print(f"  PROBLEM: {p}")
        print("ok: geometry, tokens, figures, no typed numbers" if not found else "")
        return 1 if found else 0
    if args.draft and EXPORT_DIR.resolve() in args.draft.resolve().parents:
        parser.error("a draft goes outside deliverables/")
    print(f"wrote {build(args.draft)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
