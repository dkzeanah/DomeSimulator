"""The Wedge Method, laid out as a PDF Amazon KDP will accept.

KDP rejects interiors for a small number of boring, specific reasons, and
every one of them is a measurement. So they are constants at the top of this
module with the rule each one satisfies, and :func:`validate_kdp` checks the
finished file against them rather than trusting that the layout code meant
well.

The four that actually catch people:

* **Trim size.** The page must be one of KDP's sizes, exactly. 8.5 x 11 in
  is what this book's metadata asks for.
* **Gutter.** The inside margin grows with page count, because a thick book
  swallows more of the inside edge in the spine. Under 828 pages the largest
  requirement is 0.875 in, and this module uses it at every length rather
  than computing a tighter one -- the saving is a quarter inch of text width
  and the cost of getting it wrong is a rejected file.
* **Outside margins.** At least 0.25 in on the other three edges for a book
  with no bleed. This uses 0.5, because 0.25 puts text uncomfortably close
  to a trimmed edge even when it passes.
* **Fonts embedded.** Every glyph, no exceptions. reportlab's built-in
  Type 1 faces are *not* embedded -- they are the standard fourteen, which a
  reader is expected to substitute -- so this registers real TrueType files
  and refuses to build with the built-ins.

The text is the book's own Markdown, straight out of
:mod:`wedge_book.store`, so the PDF cannot drift from the folder tree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)

from . import mathtext, store

# ----------------------------------------------------------------------
# What KDP requires
# ----------------------------------------------------------------------

#: KDP's trim, in points. 8.5 x 11 inches, which is what the book asks for.
TRIM = (8.5 * inch, 11.0 * inch)

#: The inside margin. KDP's table tops out at 0.875 in below 828 pages, and
#: this book will not reach that, so the largest value is used everywhere.
GUTTER = 0.875 * inch

#: The other three. KDP's minimum is 0.25 in without bleed; 0.5 is used
#: because a quarter inch looks like a mistake even when it is legal.
MARGIN = 0.5 * inch

#: Where the folio sits, measured from the trimmed edge.
FOLIO_UP = 0.30 * inch

#: The largest page count this gutter is valid for.
GUTTER_GOOD_TO = 828

OUT_DIR = store.ROOT / "deliverables" / "book"

#: Faces to try, in order. All must be real files that can be embedded --
#: reportlab's own Helvetica and Times are the standard fourteen and are NOT
#: embedded in the output, which fails KDP's font check.
FONT_CANDIDATES = (
    ("Georgia", "georgia.ttf", "georgiab.ttf", "georgiai.ttf"),
    ("BookAntiqua", "BKANT.TTF", "ANTQUAB.TTF", "ANTQUAI.TTF"),
    ("Cambria", "cambria.ttc", "cambriab.ttf", "cambriai.ttf"),
    ("DejaVuSerif", "DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf",
     "DejaVuSerif-Italic.ttf"),
    ("TimesNewRoman", "times.ttf", "timesbd.ttf", "timesi.ttf"),
)

FONT_DIRS = (
    Path("C:/Windows/Fonts"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype"),
    Path("/Library/Fonts"),
)

MONO_CANDIDATES = (
    ("ConsolasBook", "consola.ttf"),
    ("DejaVuMono", "DejaVuSansMono.ttf"),
    ("CourierNewBook", "cour.ttf"),
)


@dataclass(frozen=True)
class Faces:
    """The embedded family this build is using."""

    body: str
    bold: str
    italic: str
    mono: str


def _find(name: str) -> Path | None:
    for folder in FONT_DIRS:
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return None


def register_fonts() -> Faces:
    """Embed a real serif family, or refuse to build.

    Falling back to reportlab's built-in Times would produce a PDF that
    looks right and fails KDP's preflight, which is the worst of both, so
    there is no fallback.
    """
    body = bold = italic = None
    for family, regular, bold_file, italic_file in FONT_CANDIDATES:
        found = _find(regular)
        if found is None or found.suffix.lower() == ".ttc":
            continue
        pdfmetrics.registerFont(TTFont(family, str(found)))
        body = family
        for suffix, filename in (("-Bold", bold_file),
                                 ("-Italic", italic_file)):
            path = _find(filename)
            if path is not None and path.suffix.lower() != ".ttc":
                pdfmetrics.registerFont(TTFont(family + suffix, str(path)))
                if suffix == "-Bold":
                    bold = family + suffix
                else:
                    italic = family + suffix
        break
    if body is None:
        raise RuntimeError(
            "no embeddable serif font found; KDP requires every font to be "
            f"embedded and reportlab's built-ins are not. Looked in "
            f"{[str(d) for d in FONT_DIRS]}")

    mono = None
    for family, filename in MONO_CANDIDATES:
        path = _find(filename)
        if path is not None:
            pdfmetrics.registerFont(TTFont(family, str(path)))
            mono = family
            break
    if mono is None:
        raise RuntimeError("no embeddable monospaced font found; the "
                           "builder's tables need one")

    return Faces(body=body, bold=bold or body, italic=italic or body,
                 mono=mono)


# ----------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------

def styles(faces: Faces) -> dict[str, ParagraphStyle]:
    # bulletFontName has to be set explicitly. It defaults to Helvetica --
    # one of reportlab's built-in Type 1 faces, which are *not* embedded --
    # so a single bullet glyph anywhere in the book is enough to fail KDP's
    # font check on a file that otherwise looks perfect.
    base = ParagraphStyle(
        "body", fontName=faces.body, fontSize=11, leading=15.5,
        alignment=TA_JUSTIFY, spaceAfter=0, firstLineIndent=0,
        bulletFontName=faces.body, bulletFontSize=11)
    return {
        "body": base,
        # A run of paragraphs indents after the first, which is how a book
        # sets prose and how a web page does not.
        "body_run": ParagraphStyle("body_run", parent=base,
                                   firstLineIndent=14),
        "part": ParagraphStyle(
            "part", parent=base, fontName=faces.bold, fontSize=26,
            leading=32, alignment=TA_LEFT, spaceBefore=0, spaceAfter=24),
        "chapter": ParagraphStyle(
            "chapter", parent=base, fontName=faces.bold, fontSize=20,
            leading=25, alignment=TA_LEFT, spaceBefore=0, spaceAfter=16),
        "section": ParagraphStyle(
            "section", parent=base, fontName=faces.bold, fontSize=13,
            leading=17, alignment=TA_LEFT, spaceBefore=16, spaceAfter=7),
        # The small capitalised headings inside a section, which this book
        # uses constantly and which are not Markdown headings.
        "shout": ParagraphStyle(
            "shout", parent=base, fontName=faces.bold, fontSize=9.5,
            leading=13, alignment=TA_LEFT, spaceBefore=13, spaceAfter=5),
        "bullet": ParagraphStyle(
            "bullet", parent=base, leftIndent=16, bulletIndent=4,
            spaceAfter=3),
        "toc": ParagraphStyle(
            "toc", parent=base, alignment=TA_LEFT, spaceAfter=2),
        "toc_part": ParagraphStyle(
            "toc_part", parent=base, fontName=faces.bold, alignment=TA_LEFT,
            spaceBefore=11, spaceAfter=4),
        "title": ParagraphStyle(
            "title", parent=base, fontName=faces.bold, fontSize=34,
            leading=40, alignment=TA_LEFT, spaceAfter=10),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base, fontSize=15, leading=20,
            alignment=TA_LEFT, spaceAfter=40),
        "author": ParagraphStyle(
            "author", parent=base, fontSize=13, leading=18, alignment=TA_LEFT),
        "formula": ParagraphStyle(
            "formula", parent=base, alignment=TA_CENTER, fontSize=11.5,
            leading=16, spaceBefore=0, spaceAfter=0),
        "credit": ParagraphStyle(
            "credit", parent=base, fontSize=8.5, leading=12,
            alignment=TA_LEFT),
        # A figure caption is set smaller than the body and ragged right,
        # because it is read beside a picture rather than in a column.
        "caption": ParagraphStyle(
            "caption", parent=base, fontSize=8.8, leading=11.6,
            alignment=TA_LEFT, spaceBefore=4, spaceAfter=0),
        "figure_number": ParagraphStyle(
            "figure_number", parent=base, fontName=faces.bold, fontSize=8.8,
            leading=11.6, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0),
    }


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------

#: The width of the text column, which is what a figure is set to.
COLUMN = TRIM[0] - GUTTER - MARGIN


def figure_index() -> dict[int, list[dict]]:
    """Every picture the book has, by chapter, in the order it prints.

    Two sources and the book says which is which. A *figure* is the
    raw-wedge solver operated with the settings that make one idea visible.
    A *plate* is a frame of one of this project's films, taken at a named
    chapter of it -- which is how the book shows a doorway, a foundation or
    a utility column, none of which the solver models.
    """
    from . import figures as solver_figures

    index: dict[int, list[dict]] = {}
    for figure in solver_figures.catalogue():
        if not figure.path.is_file():
            continue
        index.setdefault(figure.chapter, []).append({
            "path": figure.path,
            "title": figure.title,
            "caption": figure.full_caption(),
            "kind": "figure",
        })
    try:
        from . import plates as film_plates

        lessons = film_plates.lessons()
        for plate in film_plates.PLATES:
            if not plate.path.is_file():
                continue
            lesson = lessons.get(plate.lesson)
            title = plate.title
            if not title and lesson is not None:
                title = film_plates.find_chapter(lesson, plate.chapter).title
            index.setdefault(plate.book_chapter, []).append({
                "path": plate.path,
                "title": title or plate.key,
                "caption": plate.full_caption(lesson),
                "kind": "plate",
            })
    except Exception as exc:          # a book without films still builds
        print(f"  plates unavailable: {exc}")
    return index


def figure_flowables(entry: dict, number: str, faces: Faces,
                     sheet: dict) -> list:
    """One picture, its number and its caption, as one unbreakable block.

    Unbreakable matters: a caption on the page after its picture is worse
    than no caption, and reportlab will do that happily.
    """
    from PIL import Image as PILImage

    with PILImage.open(entry["path"]) as opened:
        width, height = opened.size
    draw_width = COLUMN
    draw_height = draw_width * height / float(width)
    # Nothing taller than half the text block, so two figures can share a
    # page and a figure never arrives alone on one.
    limit = (TRIM[1] - 2 * MARGIN - 0.30 * inch) * 0.50
    if draw_height > limit:
        draw_height = limit
        draw_width = draw_height * width / float(height)
    return [KeepTogether([
        Spacer(1, 9),
        Image(str(entry["path"]), width=draw_width, height=draw_height),
        Spacer(1, 3),
        Paragraph(f"{number}  {escape(entry['title'])}",
                  sheet["figure_number"]),
        Paragraph(escape(entry["caption"]), sheet["caption"]),
        Spacer(1, 11),
    ])]


# ----------------------------------------------------------------------
# Markdown, lightly
# ----------------------------------------------------------------------

SHOUT = re.compile(r"^[A-Z0-9][A-Z0-9 ,.'\-/()&]{3,}$")


def escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def inline(text: str, faces: Faces) -> str:
    """The three inline marks this book actually uses, plus its maths.

    The maths is pulled out and converted *before* the text is escaped, and
    put back afterwards, because the converter's own output contains
    reportlab markup that escaping would turn into visible angle brackets.
    """
    spans: list[str] = []

    def stash(match: re.Match) -> str:
        spans.append(mathtext.convert(match.group(1)))
        return f"\x00{len(spans) - 1}\x00"

    text = mathtext.INLINE.sub(stash, text)
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"``(.+?)``",
                  rf'<font face="{faces.mono}">\1</font>', text)
    text = re.sub(r"`([^`\n]+?)`", rf'<font face="{faces.mono}">\1</font>',
                  text)
    # An em dash, because "--" in a proportional face reads as a typo.
    text = text.replace(" -- ", " \u2014 ")
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f"<i>{spans[int(m.group(1))]}</i>", text)


def is_table(block: str) -> bool:
    """A block laid out with spaces, which has to be set monospaced.

    The builder's reference is full of these and they are the one thing in
    the book that a proportional font destroys silently: the columns simply
    stop lining up and nothing errors.
    """
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    indented = sum(1 for ln in lines if ln.startswith("    "))
    return indented >= max(2, len(lines) - 1)


def flow(text: str, faces: Faces, sheet: dict) -> list:
    """One section's Markdown as a list of platypus flowables."""
    out: list = []
    run = 0
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.rstrip()
        if not block:
            continue
        if mathtext.is_display(block):
            # A display formula gets its own centred line, which is what
            # "$$" means and what a reader expects to be able to find again.
            for formula in mathtext.display_blocks(block):
                out.append(Spacer(1, 5))
                out.append(Paragraph(f"<i>{formula}</i>", sheet["formula"]))
                out.append(Spacer(1, 7))
            run = 0
            continue
        if is_table(block):
            body = "\n".join(ln[4:] if ln.startswith("    ") else ln
                             for ln in block.splitlines())
            out.append(Spacer(1, 7))
            out.append(Preformatted(body, ParagraphStyle(
                "table", fontName=faces.mono, fontSize=7.6, leading=10.2)))
            out.append(Spacer(1, 9))
            run = 0
            continue
        lines = block.splitlines()
        if all(ln.lstrip().startswith(("* ", "- ")) for ln in lines):
            for line in lines:
                out.append(Paragraph(inline(line.lstrip()[2:], faces),
                                     sheet["bullet"], bulletText="\u2022"))
            out.append(Spacer(1, 6))
            run = 0
            continue
        if len(lines) == 1 and SHOUT.match(lines[0].strip()):
            out.append(Paragraph(inline(lines[0].strip(), faces),
                                 sheet["shout"]))
            run = 0
            continue
        style = sheet["body_run"] if run else sheet["body"]
        out.append(Paragraph(inline(" ".join(lines), faces), style))
        out.append(Spacer(1, 6))
        run += 1
    return out


# ----------------------------------------------------------------------
# The document
# ----------------------------------------------------------------------

class Interior(BaseDocTemplate):
    """A book whose inside margin swaps sides on facing pages."""

    def __init__(self, path: Path, faces: Faces, title: str, author: str):
        # initialFontName matters more than it looks. A reportlab canvas
        # starts on Helvetica, and that puts Helvetica in every page's
        # resource dictionary even when not one glyph of it is drawn --
        # which fails KDP's "all fonts embedded" check on a file that is
        # otherwise entirely set in an embedded face.
        super().__init__(
            str(path), pagesize=TRIM, title=title, author=author,
            leftMargin=GUTTER, rightMargin=MARGIN,
            topMargin=MARGIN, bottomMargin=MARGIN,
            allowSplitting=1,
            initialFontName=faces.body, initialFontSize=11)
        self.faces = faces
        self.book_title = title
        width = TRIM[0] - GUTTER - MARGIN
        height = TRIM[1] - 2 * MARGIN - 0.30 * inch
        odd = Frame(GUTTER, MARGIN + 0.30 * inch, width, height, id="odd",
                    leftPadding=0, rightPadding=0, topPadding=0,
                    bottomPadding=0)
        even = Frame(MARGIN, MARGIN + 0.30 * inch, width, height, id="even",
                     leftPadding=0, rightPadding=0, topPadding=0,
                     bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="front", frames=[odd], onPage=self._blank),
            PageTemplate(id="odd", frames=[odd], onPage=self._folio),
            PageTemplate(id="even", frames=[even], onPage=self._folio),
        ])

    # Front matter carries no folio, which is how books are set.
    def _blank(self, canvas, _doc) -> None:
        canvas.saveState()
        canvas.restoreState()

    def _folio(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont(self.faces.body, 9)
        page = doc.page
        if page % 2:
            x, align = TRIM[0] - MARGIN, "right"
        else:
            x, align = MARGIN, "left"
        text = str(page)
        if align == "right":
            canvas.drawRightString(x, FOLIO_UP, text)
        else:
            canvas.drawString(x, FOLIO_UP, text)
        canvas.restoreState()

    def handle_pageEnd(self):  # noqa: N802 - reportlab's spelling
        # Recto and verso alternate, so the gutter is always the inside.
        nxt = "even" if (self.page + 1) % 2 == 0 else "odd"
        if self.pageTemplate.id in ("odd", "even"):
            self._handle_nextPageTemplate(nxt)
        return super().handle_pageEnd()


def chapter_number(book: store.Book, chapter) -> int:
    """A chapter's number through the whole book, counting across parts.

    The figure catalogues key on this -- chapter 14 is Environmental
    Control, wherever Part IV starts -- while the store numbers chapters
    inside their own part.
    """
    seen = 0
    for part in book.parts:
        for found in part.chapters:
            seen += 1
            if found is chapter:
                return seen
    return 0


def _spread(count: int, sections: int) -> dict[int, list[int]]:
    """Which figure goes after which section.

    Evenly, with the first under the chapter opening (key ``-1``), because a
    chapter that opens with a picture tells the reader what it is about
    before it starts explaining.
    """
    places: dict[int, list[int]] = {}
    if count <= 0:
        return places
    if sections <= 0:
        places[-1] = list(range(count))
        return places
    places.setdefault(-1, []).append(0)
    remaining = list(range(1, count))
    if not remaining:
        return places
    step = max(1, sections // max(1, len(remaining)))
    slot = 0
    for figure in remaining:
        places.setdefault(min(slot, sections - 1), []).append(figure)
        slot += step
    return places


def build(path: Path | None = None, book: store.Book | None = None) -> Path:
    """Lay the whole book out and write the PDF."""
    book = book or store.load_json()
    faces = register_fonts()
    sheet = styles(faces)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(path) if path else (OUT_DIR / "the-wedge-method-kdp.pdf")

    title = book.metadata.get("title", "Untitled")
    subtitle = book.metadata.get("subtitle", "")
    author = book.metadata.get("author", "")

    story: list = []

    # -- title page -------------------------------------------------
    story.append(Spacer(1, 2.4 * inch))
    story.append(Paragraph(escape(title), sheet["title"]))
    if subtitle:
        story.append(Paragraph(escape(subtitle), sheet["subtitle"]))
    story.append(Paragraph(escape(author), sheet["author"]))
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph(escape(store.CREDIT), sheet["credit"]))
    story.append(PageBreak())

    # -- front matter -----------------------------------------------
    for key in ("disclaimer", "introduction"):
        text = (book.front_matter or {}).get(key)
        if not text:
            continue
        story.append(Paragraph(key.title(), sheet["chapter"]))
        story.extend(flow(text, faces, sheet))
        story.append(PageBreak())

    # -- contents ---------------------------------------------------
    story.append(Paragraph("Contents", sheet["chapter"]))
    for part in book.parts:
        story.append(Paragraph(escape(part.title), sheet["toc_part"]))
        for chapter in part.chapters:
            story.append(Paragraph(escape(chapter.title), sheet["toc"]))
    story.append(NextPageTemplate("odd"))
    story.append(PageBreak())

    # -- a list of what is in the pictures ---------------------------
    counted = figure_index()
    if counted:
        story.append(Paragraph("Figures", sheet["chapter"]))
        story.extend(flow(
            "Every picture in this book was made by running one of this "
            "project's own tools and photographing the result. A **figure** "
            "is the raw-wedge solver, operated with the settings that make "
            "one idea visible -- the frame opened far enough to see into a "
            "seam, the wireframe switched off, the camera stood off the "
            "shell at a stated distance. A **plate** is a frame of one of "
            "the project's films, taken at a named chapter of it, and is "
            "how the book shows the things the solver does not model: a "
            "doorway, a foundation, the utility column, a 3V dome.\n\n"
            "Nothing here was drawn by hand, and every one can be made "
            "again from the recipe stored beside it.",
            faces, sheet))
        for chapter_index in sorted(counted):
            entries = counted[chapter_index]
            kinds = sum(1 for e in entries if e["kind"] == "plate")
            story.append(Paragraph(
                f"Chapter {chapter_index}: {len(entries)} "
                f"({len(entries) - kinds} figures, {kinds} plates)",
                sheet["toc"]))
        story.append(PageBreak())

    # -- the book ---------------------------------------------------
    pictures = figure_index()
    printed: list[tuple[str, str, int]] = []
    number = 0
    for part in book.parts:
        story.append(Paragraph(escape(part.title), sheet["part"]))
        if part.body:
            story.extend(flow(part.body, faces, sheet))
        story.append(PageBreak())
        for chapter in part.chapters:
            story.append(Paragraph(escape(chapter.title), sheet["chapter"]))
            if chapter.body:
                story.extend(flow(chapter.body, faces, sheet))
            # This chapter's pictures, spread through its sections rather
            # than banked at the end, so one lands near the prose that
            # wants it. The first goes under the chapter opening.
            queue = list(pictures.get(chapter_number(book, chapter), []))
            sections = list(chapter.sections)
            places = _spread(len(queue), len(sections))
            if places.get(-1):
                for entry in places[-1]:
                    number += 1
                    label = f"Figure {number}."
                    story.extend(figure_flowables(queue[entry], label,
                                                  faces, sheet))
                    printed.append((label, queue[entry]["title"],
                                    chapter_number(book, chapter)))
            for index, section in enumerate(sections):
                story.append(Paragraph(escape(section.title),
                                       sheet["section"]))
                if section.body:
                    story.extend(flow(section.body, faces, sheet))
                for entry in places.get(index, ()):
                    number += 1
                    label = f"Figure {number}."
                    story.extend(figure_flowables(queue[entry], label,
                                                  faces, sheet))
                    printed.append((label, queue[entry]["title"],
                                    chapter_number(book, chapter)))
            story.append(PageBreak())

    Interior(path, faces, title, author).build(story)
    return path


# ----------------------------------------------------------------------
# Checking the file, not the intention
# ----------------------------------------------------------------------

def inspect(path: Path) -> dict:
    """Read the finished PDF back and report what KDP will measure."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    sizes = set()
    for page in reader.pages:
        box = page.mediabox
        sizes.add((round(float(box.width), 2), round(float(box.height), 2)))

    embedded, not_embedded = set(), set()
    for page in reader.pages:
        fonts = (page.get("/Resources") or {}).get("/Font") or {}
        for ref in fonts.values():
            font = ref.get_object()
            base = str(font.get("/BaseFont", "?")).lstrip("/")
            descendants = font.get("/DescendantFonts")
            targets = ([d.get_object() for d in descendants]
                       if descendants else [font])
            found = False
            for target in targets:
                descriptor = target.get("/FontDescriptor")
                if descriptor is None:
                    continue
                descriptor = descriptor.get_object()
                if any(descriptor.get(k) is not None
                       for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                    found = True
            (embedded if found else not_embedded).add(base)

    return {
        "pages": len(reader.pages),
        "sizes": sorted(sizes),
        "embedded": sorted(embedded),
        "not_embedded": sorted(not_embedded),
        "bytes": path.stat().st_size,
    }


def validate_kdp(path: Path | None = None) -> dict:
    """Build the interior and check the *file* against KDP's rules.

    Checking the file rather than the layout code is the point. A margin
    constant can be right while the frame that uses it is wrong, and the
    thing Amazon reads is the PDF.
    """
    # A path that does not exist yet means "build it here and check that",
    # which is what --out is for. Reading it and failing on a missing file
    # is a trap the caller falls into once each time.
    path = Path(path) if path else build()
    if not path.is_file():
        path = build(path)
    report = inspect(path)

    assert len(report["sizes"]) == 1, (
        f"pages are not all one size: {report['sizes']}")
    width, height = report["sizes"][0]
    want = (round(TRIM[0], 2), round(TRIM[1], 2))
    assert (width, height) == want, (
        f"trim is {width} x {height} pt; KDP was asked for {want}")

    assert not report["not_embedded"], (
        "KDP requires every font embedded; these are not: "
        f"{report['not_embedded']}")
    assert report["embedded"], "no embedded fonts found at all"

    assert report["pages"] >= 24, (
        f"{report['pages']} pages; KDP's minimum for a paperback is 24")
    assert report["pages"] <= GUTTER_GOOD_TO, (
        f"{report['pages']} pages needs a wider gutter than the "
        f"{GUTTER / inch:.3f} in this module uses")

    # An odd final page means the last leaf is printed on one side. KDP
    # accepts it and pads; a book that ends on a verso looks deliberate.
    report["ends_on_recto"] = bool(report["pages"] % 2)

    report["unrendered"] = check_rendered(path)
    return report


#: Things that must never reach a printed page. Each one has been on one.
UNRENDERED = {
    "raw display math": r"\$\$",
    "raw inline math": r"\\\(",
    "latex command": r"\\[a-zA-Z]{2,}",
    "escaped tag": r"&lt;|&gt;|&amp;",
    "literal tag": r"<super>|<sub>|</i>|</b>",
    "markdown bold": r"\*\*",
    "stash marker": chr(0),
}


def check_rendered(path: Path) -> dict[str, list[int]]:
    """Read the finished pages back and look for unrendered source.

    Measuring the layout code is not enough. A display formula joined into
    a paragraph is valid Markdown, passes every structural check, and
    prints its own LaTeX in the middle of a sentence -- which it did, on 24
    pages, and nothing failed until somebody read the text back out.
    """
    import pymupdf

    document = pymupdf.open(str(path))
    found: dict[str, list[int]] = {}
    for index in range(document.page_count):
        text = document[index].get_text()
        for name, pattern in UNRENDERED.items():
            if re.search(pattern, text):
                found.setdefault(name, []).append(index + 1)
    document.close()
    assert not found, (
        "the PDF has unrendered source on its pages: "
        + "; ".join(f"{name} on {len(pages)} pages, first at {pages[0]}"
                    for name, pages in found.items()))
    return found


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None,
                        help="where to write the interior PDF")
    parser.add_argument("--check", action="store_true",
                        help="build, then measure the file against KDP")
    args = parser.parse_args(argv)

    if args.check:
        report = validate_kdp(args.out)
        print(f"  pages      {report['pages']}")
        print(f"  trim       {report['sizes'][0]} pt "
              f"({TRIM[0] / inch:.2f} x {TRIM[1] / inch:.2f} in)")
        print(f"  gutter     {GUTTER / inch:.3f} in")
        print(f"  margins    {MARGIN / inch:.3f} in")
        print(f"  embedded   {', '.join(report['embedded'])}")
        print(f"  size       {report['bytes'] / 1e6:.2f} MB")
        print("  KDP CHECKS PASSED")
        return 0

    path = build(args.out)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
