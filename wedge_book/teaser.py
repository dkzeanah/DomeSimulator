"""The free sample: a few chapters of the print book, for the website's email form.

The sample is *cut from* the newest print edition (:mod:`wedge_book.print_edition`),
never typeset separately, so a reader gets exactly the pages the paperback
prints -- its folios, figures and tables -- and nothing in the sample can
drift from the book. Around those pages it adds four of its own:

* the rendered cover (:mod:`wedge_book.cover_scene`'s ``cover-front.png``);
* "what this is": the book's headline figures, read from :mod:`wedge_book.tokens`,
  and the sampled chapters with the book's page numbers;
* the whole book's contents, from :mod:`wedge_book.outline`;
* where to get it: the print edition (Amazon), and the digital edition sold on
  the website, at the price in ``web/books.config.json`` -- the same file the
  shop charges from, so the sample and the checkout can never disagree.

    py -3.12 -m wedge_book.teaser            # new deliverables/book/the-40-hour-cabin-sample[-vN].pdf
    py -3.12 -m wedge_book.teaser --check    # validate the newest sample
"""

from __future__ import annotations

import base64
import html as html_escape
import json
import re
from dataclasses import dataclass
from pathlib import Path

from two_v_demo import book_export
from two_v_demo.deliverables import next_version_path

from . import outline, print_edition, tokens

#: The front-matter section the sample opens with (the book's own promise).
FRONT = ("Forty Hours",)
#: The chapters it carries, in book order. All of Part 1's argument for what
#: has to be right, then the chapter that is the method itself.
SAMPLE = (outline.CH_LUMPY, outline.CH_SILENT_KILLER, outline.CH_HOTSWAP, outline.CH_SPLIT)

STEM = f"{outline.STEM}-sample"
COVER_ART = outline.ROOT / "book_wedge" / "cover" / "cover-front.png"
WEB = outline.ROOT / "web"

#: The headline figures on the "what this is" page, each a live token.
HEADLINE = (
    ("{{dome.members}}", "split-log members, cut to two lengths"),
    ("{{dome.panels}}", "triangular panels, built flat on one jig"),
    ("{{dome.floor_sqft}} sq ft", "of floor under a {{dome.diameter_ft}}-ft dome"),
    ("{{hr.total}} h", "of frame work, standing tree to standing frame"),
    ("${{money.frame}}", "for the wedge-cut frame, priced line by line"),
)


# ----------------------------------------------------------------------
# Where things are in the print edition
# ----------------------------------------------------------------------

def _lines(text: str) -> list[str]:
    """A page's text lines, without the bare folio Chrome extracts first."""
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.strip().isdigit()]


def _squash(text: str) -> str:
    """Letter-spaced headings extract as "C H A P T E R": compare without spaces."""
    return re.sub(r"[\s’'`]", "", text).lower()


@dataclass(frozen=True)
class Span:
    label: str
    first: int   # 0-based page index
    last: int    # inclusive


def chapter_starts(doc) -> dict[int, int]:
    """Chapter number -> 0-based page index of its opening page."""
    starts = {}
    for i, page in enumerate(doc):
        lines = _lines(page.get_text())
        if lines:
            match = re.fullmatch(r"chapter(\d+)", _squash(lines[0]))
            if match:
                starts.setdefault(int(match.group(1)), i)
    return starts


def section_breaks(doc) -> list[int]:
    """Every page that opens something: a chapter, a Part, a front or back section."""
    titles = {_squash(t) for t in ("The Engineer's Note", "Forty Hours", "Glossary",
                                   "About the Author", "Index", "Contents")}
    breaks = []
    for i, page in enumerate(doc):
        lines = _lines(page.get_text())
        if not lines:
            continue
        head = _squash(lines[0])
        if re.fullmatch(r"(chapter|part)\d+", head) or head in titles:
            breaks.append(i)
    return breaks


def spans(doc) -> list[Span]:
    """The sample's page ranges, in reading order, each ending before the next
    section opens and without trailing blank pages."""
    breaks = section_breaks(doc)
    starts = chapter_starts(doc)

    def until_next(first: int) -> int:
        later = [b for b in breaks if b > first]
        last = (later[0] if later else len(doc)) - 1
        while last > first and not doc[last].get_text().strip():
            last -= 1
        return last

    found = []
    for title in FRONT:
        first = next((i for i, page in enumerate(doc)
                      if (lines := _lines(page.get_text())) and _squash(lines[0]) == _squash(title)), None)
        if first is None:
            raise RuntimeError(f"the print edition has no {title!r} section")
        found.append(Span(title, first, until_next(first)))
    for chapter in SAMPLE:
        first = starts.get(chapter.number)
        if first is None:
            raise RuntimeError(f"chapter {chapter.number} is not in the print edition -- rebuild it")
        # The opening page must carry this chapter's title: a stale print
        # edition numbered differently would otherwise give the wrong pages.
        if _squash(chapter.title) not in _squash(doc[first].get_text()):
            raise RuntimeError(f"page {first + 1} opens chapter {chapter.number} but not "
                               f"{chapter.title!r}: the print edition is older than the outline")
        found.append(Span(f"{chapter.number}. {chapter.title}", first, until_next(first)))
    return found


# ----------------------------------------------------------------------
# The sample's own pages
# ----------------------------------------------------------------------

def site() -> dict:
    """The website's address and the digital edition's price, from the files the site runs on."""
    site_cfg = json.loads((WEB / "site.config.json").read_text(encoding="utf-8"))
    books = json.loads((WEB / "books.config.json").read_text(encoding="utf-8"))["books"]
    paid = next((b for b in books if b.get("offer") == "paid"), None)
    amazon = next((b for b in books if b.get("offer") == "amazon"), None)
    url = str(site_cfg.get("url", "")).rstrip("/")
    if not url:
        raise RuntimeError('web/site.config.json needs "url" -- the address printed in the sample')
    return {
        "url": url,
        "host": re.sub(r"^https?://", "", url),
        "paid": paid,
        "price": f"${paid['priceCents'] / 100:,.0f}" if paid and paid.get("priceCents") else "",
        "amazon": amazon,
    }


CSS = """
@page { size: 8.5in 11in; margin: 0; }
html, body { margin: 0; background: #fff; }
body { font: 11pt/1.55 Georgia, "Times New Roman", serif; color: #111; }
.page { width: 8.5in; height: 11in; box-sizing: border-box; padding: .9in .85in;
        break-after: page; position: relative; overflow: hidden; }
.page:last-child { break-after: auto; }
.cover { padding: 0; }
.cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.sans { font-family: "Segoe UI", Helvetica, Arial, sans-serif; }
.eyebrow { font: 700 9pt "Segoe UI", sans-serif; letter-spacing: .2em; text-transform: uppercase;
           color: #a5620c; margin: 0 0 .12in; }
h1 { font: 700 26pt/1.12 "Segoe UI", Helvetica, Arial, sans-serif; margin: 0 0 .1in; }
h2 { font: 700 14pt/1.2 "Segoe UI", sans-serif; margin: .3in 0 .1in; }
.sub { font: italic 14pt/1.3 Georgia, serif; color: #444; margin: 0 0 .3in; }
p { margin: 0 0 .12in; }
.figures { display: grid; grid-template-columns: repeat(5, 1fr); gap: .1in; margin: .25in 0; }
.figures div { border-top: 2.5px solid #111; padding-top: .08in; }
.figures b { display: block; font: 700 17pt/1.1 "Segoe UI", sans-serif; }
.figures span { font-size: 8.5pt; line-height: 1.3; color: #444; display: block; margin-top: .04in; }
.inside { list-style: none; padding: 0; margin: .1in 0; }
.inside li { display: flex; gap: .1in; border-bottom: .6px solid #ddd; padding: .05in 0; }
.inside li span:first-child { flex: 1; }
.inside li span:last-child { color: #666; font-variant-numeric: tabular-nums; }
.note { font-size: 9.5pt; color: #555; }
.toc { columns: 2; column-gap: .35in; font-size: 8.6pt; line-height: 1.36; }
.toc .part { font: 700 7.6pt/1.3 "Segoe UI", sans-serif; letter-spacing: .08em; text-transform: uppercase;
             margin: .1in 0 .03in; break-after: avoid; }
.toc .part:first-child { margin-top: 0; }
.toc p { margin: 0; padding-left: .24in; text-indent: -.24in; break-inside: avoid; }
.toc .sampled { font-weight: 700; }
.offer { border: 1.5px solid #111; border-radius: 8px; padding: .22in .26in; margin: .22in 0; }
.offer h2 { margin-top: 0; }
.offer .price { font: 700 22pt "Segoe UI", sans-serif; float: right; margin-left: .2in; }
.offer .url, .offer .url a { font: 700 12pt "Segoe UI", sans-serif; color: #a5620c; text-decoration: none; }
.foot { position: absolute; left: .85in; right: .85in; bottom: .6in; font-size: 8.5pt; color: #666; }
"""


def _page_label(doc, index: int) -> str:
    """The folio printed on a page of the book (the PDF's own page number)."""
    return str(index + 1)


def intro_page(doc, found: list[Span]) -> str:
    e = html_escape.escape
    chapters = sum(len(p.chapters) for p in outline.BOOK.parts)
    pages = len(doc)
    sample_pages = sum(s.last - s.first + 1 for s in found)
    figures = "".join(
        f"<div><b>{e(tokens.resolve(value))}</b><span>{e(tokens.resolve(label))}</span></div>"
        for value, label in HEADLINE)
    rows = "".join(
        f"<li><span>{e(s.label)}</span><span>page {_page_label(doc, s.first)}</span></li>" for s in found)
    return f"""
<section class="page">
  <p class="eyebrow">Free sample</p>
  <h1>{e(outline.TITLE)}</h1>
  <p class="sub">{e(outline.SUBTITLE)} &middot; {e(outline.AUTHOR)}</p>
  <p>A small timber house, framed from trees you split yourself, with a chainsaw and
  a jig on one flat board. This book is how, from the first cut to a dry, raised shell
  -- with every length, angle and price computed from the geometry rather than guessed.</p>
  <div class="figures">{figures}</div>
  <h2>In this sample</h2>
  <p>{sample_pages} of the book's {pages} pages, exactly as they are printed, from
  {len(SAMPLE)} of its {chapters} chapters. The page numbers are the book's own.</p>
  <ul class="inside">{rows}</ul>
  <p class="note">The full contents, and where to get the whole book, are at the end.</p>
</section>"""


def contents_page(found: list[Span]) -> str:
    e = html_escape.escape
    sampled = {c.number for c in SAMPLE}
    blocks = []
    for part in outline.BOOK.parts:
        blocks.append(f'<p class="part">Part {part.number} &middot; {e(part.title)}</p>')
        for c in part.chapters:
            cls = ' class="sampled"' if c.number in sampled else ""
            blocks.append(f"<p{cls}>{c.number}&nbsp;&nbsp;{e(c.title)}</p>")
    return f"""
<section class="page">
  <p class="eyebrow">The whole book</p>
  <h1>{len(outline.BOOK.parts)} Parts, {sum(len(p.chapters) for p in outline.BOOK.parts)} chapters</h1>
  <p class="note">Chapters in bold are in this sample.</p>
  <div class="toc">{''.join(blocks)}</div>
</section>"""


def offer_page(where: dict) -> str:
    e = html_escape.escape
    paid, amazon = where["paid"], where["amazon"]
    digital = ""
    if paid and where["price"]:
        digital = f"""
  <div class="offer">
    <span class="price">{e(where['price'])}</span>
    <h2>Read the digital edition today</h2>
    <p><b>{e(paid['title'])}{((' — ' if ':' in paid['subtitle'] else ': ') + e(paid['subtitle'])) if paid.get('subtitle') else ''}</b>
    -- the long version: the whole build day by day, why it scales, and every variation
    the project has worked out. A PDF, sold only on the website, with every future
    edition included.</p>
    <p class="url"><a href="{e(where['url'])}/{e(paid.get('page') or 'book')}">{e(where['host'])}/{e(paid.get('page') or 'book')}</a></p>
  </div>"""
    kdp = ""
    if amazon:
        status = ("Now on Amazon." if amazon.get("amazonUrl")
                  else "Coming to Amazon as a paperback. Leave your email and you will hear the day it is out.")
        kdp = f"""
  <div class="offer">
    <h2>The paperback</h2>
    <p><b>{e(outline.TITLE)}: {e(outline.SUBTITLE)}</b> -- this book, in print. {e(status)}</p>
    <p class="url"><a href="{amazon.get('amazonUrl') or where['url'] + '/' + (amazon.get('page') or 'paperback')}">{e(where['host'])}/{e(amazon.get('page') or 'paperback')}</a></p>
  </div>"""
    return f"""
<section class="page">
  <p class="eyebrow">Keep reading</p>
  <h1>Where to get the rest</h1>
  <p>You have read the part of the book that says what has to be right. The rest is
  how to make it right: the geometry from one number, the stick, the panel, the skin,
  the seam, the ground it stands on, and what all of it costs, line by line.</p>
  {digital}
  {kdp}
  <p class="foot">{e(outline.TITLE)}: {e(outline.SUBTITLE)} &middot; Copyright &copy;
  {print_edition.YEAR} {e(outline.AUTHOR)}. This sample may be shared freely, whole and unchanged.</p>
</section>"""


def cover_page() -> str:
    if not COVER_ART.is_file():
        raise RuntimeError(f"no cover art at {COVER_ART} (run wedge_book.cover_scene)")
    data = base64.b64encode(COVER_ART.read_bytes()).decode("ascii")
    return (f'<section class="page cover"><img src="data:image/png;base64,{data}" '
            f'alt="{html_escape.escape(outline.TITLE)}"></section>')


def _html(*pages: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html_escape.escape(outline.TITLE)}"
            f" (sample)</title><style>{CSS}</style></head><body>{''.join(pages)}</body></html>")


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------

def build(source: Path | None = None) -> Path:
    import tempfile

    import pymupdf

    source = source or print_edition.latest()
    if not source:
        raise RuntimeError("no print edition yet: py -3.12 -m wedge_book.print_edition")
    book = pymupdf.open(source)
    found = spans(book)
    where = site()

    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the sample needs Chrome or Edge to print its own pages")
    scratch = Path(tempfile.mkdtemp(prefix="sample-"))
    front, back = scratch / "front.pdf", scratch / "back.pdf"
    book_export._pdf_via_chrome(_html(cover_page(), intro_page(book, found)), front, chrome)
    book_export._pdf_via_chrome(_html(contents_page(found), offer_page(where)), back, chrome)

    out_doc = pymupdf.open()
    out_doc.insert_pdf(pymupdf.open(front))
    for span in found:
        out_doc.insert_pdf(book, from_page=span.first, to_page=span.last)
    out_doc.insert_pdf(pymupdf.open(back))
    out_doc.set_metadata({
        "title": f"{outline.TITLE}: {outline.SUBTITLE} (free sample)",
        "author": outline.AUTHOR,
        "subject": f"A free sample of {outline.TITLE}, cut from {source.name}",
        "creator": "DomeSim wedge_book.teaser",
        "producer": "Chrome + PyMuPDF",
    })
    out = next_version_path(outline.EXPORT_DIR / f"{STEM}.pdf")
    out_doc.save(out, garbage=3, deflate=True)
    return out


def latest() -> Path | None:
    candidates = [p for p in outline.EXPORT_DIR.glob(f"{STEM}*.pdf")
                  if re.fullmatch(rf"{re.escape(STEM)}(-v\d+)?\.pdf", p.name)]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def validate(path: Path | None = None) -> dict:
    """The sample is letter-size, opens on the cover, carries every sampled
    chapter's opening page, and ends on the offer."""
    import pymupdf

    path = path or latest()
    assert path and path.exists(), "no sample has been built"
    doc = pymupdf.open(path)
    problems = []
    sizes = {(round(p.rect.width / 72, 2), round(p.rect.height / 72, 2)) for p in doc}
    if sizes != {print_edition.TRIM_IN}:
        problems.append(f"page sizes {sizes}")
    if not doc[0].get_images():
        problems.append("page 1 is not the cover")
    text = _squash("".join(p.get_text() for p in doc))
    for chapter in SAMPLE:
        if _squash(chapter.title) not in text:
            problems.append(f"chapter {chapter.number} ({chapter.title}) is missing")
    if "wheretogettherest" not in _squash(doc[-1].get_text()):
        problems.append("the last page is not the offer")
    return {"file": path.name, "pages": len(doc), "problems": problems}


def check_sample() -> None:
    """For the check suite: the newest sample passes, and was cut from the
    newest print edition (a stale sample would advertise an old book)."""
    import pymupdf

    report = validate()
    assert not report["problems"], f"{report['file']}: {report['problems']}"
    source = print_edition.latest()
    subject = pymupdf.open(latest()).metadata.get("subject", "")
    assert source and source.name in subject, (
        f"{report['file']} was cut from an older print edition than {source.name}: "
        "run py -3.12 -m wedge_book.teaser")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate the newest sample only")
    args = parser.parse_args(argv)
    if not args.check:
        print(f"wrote {build().relative_to(outline.ROOT)}")
    report = validate()
    print(f"{report['file']}: {report['pages']} pages")
    for problem in report["problems"]:
        print(f"  PROBLEM: {problem}")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
