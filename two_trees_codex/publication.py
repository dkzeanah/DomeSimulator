"""Append-only print editions and silent still-page readthroughs for Codex's book.

The PDF is the layout authority. Reader PNGs and the video use those same physical
pages, including overflow pages. Exports never rewrite the manuscript or assets.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from xml.sax.saxutils import escape

from .storage import BookStore, stamp, words
from .placement import body_segments, figure_groups, prose_paragraph_count

PAGE_SIZE = (432, 648)  # 6 x 9 inch trade paperback
MARGIN = 45
PAPER = "#fffdf5"
INK = "#243f34"


def _notify(callback, message):
    if callback:
        callback(message)


def _folder(base, prefix):
    destination = Path(base).expanduser().resolve() / (prefix + "-" + stamp() + "-" + uuid.uuid4().hex[:8])
    destination.mkdir(parents=True, exist_ok=False)
    return destination


def _write_json(path, payload):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)


def _positive(value, label):
    if isinstance(value, bool):
        raise ValueError(label + " must be a finite positive number.")
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(label + " must be a finite positive number.") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(label + " must be a finite positive number.")
    return value


def _asset_path(home, asset):
    raw = asset.get("path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("Attached figure is missing its local asset path.")
    path = (home / raw).resolve()
    if home not in path.parents:
        raise ValueError("Attached figure path leaves this book workspace.")
    if not path.is_file():
        raise FileNotFoundError("Attached figure is missing: " + str(path))
    return path


def _bundled_python():
    configured = os.environ.get("TWO_TREES_PDF_PYTHON")
    candidates = [Path(configured)] if configured else []
    candidates.append(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe")
    return next((p for p in candidates if p.is_file() and p.resolve() != Path(sys.executable).resolve()), None)


def _pdf_available():
    return all(importlib.util.find_spec(name) is not None for name in ("reportlab", "pypdf", "pypdfium2", "PIL"))


def _pdf_subprocess(book, home, output_dir, progress_callback):
    interpreter = _bundled_python()
    if interpreter is None:
        raise RuntimeError("PDF export needs reportlab, pypdf, pypdfium2 and Pillow. Install these in the launcher Python or set TWO_TREES_PDF_PYTHON to the bundled Python.")
    _notify(progress_callback, "Using bundled PDF runtime...")
    with tempfile.TemporaryDirectory(prefix="codex-book-pdf-") as temporary:
        request = Path(temporary) / "request.json"
        request.write_text(json.dumps({"book": book, "home": str(home), "output_dir": str(output_dir) if output_dir is not None else None}, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([str(interpreter), "-m", "two_trees_codex.publication", "--request", str(request)],
                                cwd=Path(__file__).resolve().parent.parent, capture_output=True, text=True,
                                encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError("Bundled PDF export failed: " + (result.stderr or result.stdout)[-3000:])
        publication = json.loads(result.stdout)
    _notify(progress_callback, f"PDF ready: {len(publication['pages'])} physical pages.")
    return publication


def _fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    files = [("BookSerif", "georgia.ttf"), ("BookSerifBold", "georgiab.ttf"),
             ("BookSerifItalic", "georgiai.ttf"), ("BookSans", "segoeui.ttf"),
             ("BookSansBold", "segoeuib.ttf")]
    if all((windows / filename).is_file() for _, filename in files):
        for name, filename in files:
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(windows / filename)))
        pdfmetrics.registerFontFamily("BookSerif", normal="BookSerif", bold="BookSerifBold", italic="BookSerifItalic", boldItalic="BookSerifBold")
        pdfmetrics.registerFontFamily("BookSans", normal="BookSans", bold="BookSansBold", italic="BookSans", boldItalic="BookSansBold")
        return "BookSerif", "BookSerifBold", "BookSans", "BookSansBold"
    # Common Linux font family also covers the mathematical symbols in the book.
    linux = Path("/usr/share/fonts/truetype/dejavu")
    if (linux / "DejaVuSerif.ttf").is_file():
        for name, filename in [("BookSerif", "DejaVuSerif.ttf"), ("BookSerifBold", "DejaVuSerif-Bold.ttf"), ("BookSans", "DejaVuSans.ttf"), ("BookSansBold", "DejaVuSans-Bold.ttf")]:
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(linux / filename)))
        pdfmetrics.registerFontFamily("BookSerif", normal="BookSerif", bold="BookSerifBold", italic="BookSerif", boldItalic="BookSerifBold")
        pdfmetrics.registerFontFamily("BookSans", normal="BookSans", bold="BookSansBold", italic="BookSans", boldItalic="BookSansBold")
        return "BookSerif", "BookSerifBold", "BookSans", "BookSansBold"
    return "Times-Roman", "Times-Bold", "Helvetica", "Helvetica-Bold"


def _plain(text):
    # Normalize only typography that commonly produces a missing glyph in PDFs.
    return str(text).translate(str.maketrans({"\u2011": "-", "\u2010": "-", "\u2212": "-", "\u2192": " -> ", "\u2190": " <- ", "\u2194": " <-> "}))


def _inline(text):
    value = escape(_plain(text))
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    # Treat links as readable labels and URLs, avoiding external requests.
    value = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1 (\2)", value)
    return value


def _body_flowables(body, styles, width):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    output, paragraph, table, code = [], [], [], None

    def flush():
        if paragraph:
            output.append(Paragraph(_inline(" ".join(paragraph)), styles["body"]))
            paragraph.clear()
        if table:
            rows = [row for row in table if not all(re.fullmatch(r"[: -]+", cell or " ") for cell in row)]
            if rows:
                count = max(len(row) for row in rows)
                cells = [[Paragraph(_inline(cell), styles["cell"]) for cell in row + [""] * (count - len(row))] for row in rows]
                t = Table(cells, colWidths=[width/count] * count, repeatRows=1, hAlign="LEFT", splitByRow=1, splitInRow=1)
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7ecdf")),
                                      ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                      ("LINEBELOW", (0, 0), (-1, -1), .35, colors.HexColor("#c6cebd")),
                                      ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                      ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
                output.extend([t, Spacer(1, 10)])
            table.clear()

    def flush_code(lines):
        # Paragraphs wrap long formulas rather than clipping preformatted lines.
        for line in lines:
            output.append(Paragraph(escape(_plain(line)) or "&#160;", styles["code"]))
        output.append(Spacer(1, 8))

    for line in body.splitlines():
        if line.startswith("```"):
            flush()
            if code is None:
                code = []
            else:
                flush_code(code)
                code = None
        elif code is not None:
            code.append(line)
        elif line.startswith("|"):
            if paragraph:
                flush()
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif not line.strip():
            flush()
        elif line.startswith("#"):
            flush()
            output.append(Paragraph(_inline(line.lstrip("# ")), styles["h2"] if line.startswith("## ") else styles["h3"]))
        elif line.startswith("> "):
            flush()
            output.append(Paragraph(_inline(line[2:]), styles["quote"]))
        elif re.match(r"(?:[-*] |\d+\. )", line):
            flush()
            output.append(Paragraph(_inline(line), styles["list"]))
        else:
            if table:
                flush()
            paragraph.append(line)
    flush()
    if code is not None:
        flush_code(code)
    return output


def export_publication(book: dict, home: Path, output_dir: Path | None = None, progress_callback=None) -> dict:
    """Export selectable-text PDF, matching PNG pages, and a provenance manifest.

    ``output_dir`` is a parent directory. Each invocation allocates a fresh child,
    even when the same book is exported repeatedly. No image is silently skipped.
    """
    book = deepcopy(book)
    BookStore.validate(book)
    home = Path(home).expanduser().resolve()
    for page in book["pages"]:
        for key in page["figures"]:
            if key not in book.get("assets", {}):
                raise ValueError("Missing attached figure record: " + key)
            _asset_path(home, book["assets"][key])
    if not _pdf_available():
        return _pdf_subprocess(book, home, output_dir, progress_callback)

    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import ActionFlowable, BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer
    from reportlab.platypus.tableofcontents import TableOfContents
    from pypdf import PdfReader
    import pypdfium2 as pdfium

    # Validate image data before any document output is created.
    for page in book["pages"]:
        for key in page["figures"]:
            with PILImage.open(_asset_path(home, book["assets"][key])) as im:
                im.verify()
    folder = _folder(output_dir if output_dir is not None else home / "exports", "publication")
    pdf_path = folder / "2-trees-reading-edition.pdf"
    serif, serif_bold, sans, sans_bold = _fonts()
    width = PAGE_SIZE[0] - MARGIN * 2
    styles = {
        "body": ParagraphStyle("BookBody", fontName=serif, fontSize=10.3, leading=15.2, textColor=colors.HexColor(INK), spaceAfter=10, allowWidows=0, allowOrphans=0),
        "title": ParagraphStyle("BookTitle", fontName=serif_bold, fontSize=23, leading=29, textColor=colors.HexColor(INK), spaceAfter=19, keepWithNext=True),
        "cover": ParagraphStyle("CoverTitle", fontName=serif_bold, fontSize=34, leading=41, textColor=colors.HexColor(INK), spaceAfter=24),
        "h2": ParagraphStyle("BookH2", fontName=sans_bold, fontSize=13, leading=17, textColor=colors.HexColor(INK), spaceBefore=12, spaceAfter=7, keepWithNext=True),
        "h3": ParagraphStyle("BookH3", fontName=sans_bold, fontSize=11, leading=15, textColor=colors.HexColor(INK), spaceBefore=10, spaceAfter=6, keepWithNext=True),
        "meta": ParagraphStyle("BookMeta", fontName=sans, fontSize=8, leading=11.5, textColor=colors.HexColor("#667867"), spaceAfter=13),
        "caption": ParagraphStyle("FigureCaption", fontName=sans, fontSize=8.5, leading=12, textColor=colors.HexColor("#4f6354"), spaceAfter=5),
        "figure_source": ParagraphStyle("FigureSource", fontName=sans, fontSize=7.3, leading=10.5, textColor=colors.HexColor("#667867"), spaceAfter=5),
        "cell": ParagraphStyle("TableCell", fontName=sans, fontSize=8.1, leading=11, textColor=colors.HexColor(INK)),
        "code": ParagraphStyle("Formula", fontName=serif, fontSize=9.2, leading=13.5, textColor=colors.HexColor(INK), leftIndent=8, rightIndent=8, backColor=colors.HexColor("#edf0e6"), spaceAfter=3),
        "quote": ParagraphStyle("Quote", fontName=serif, fontSize=10.3, leading=15.2, textColor=colors.HexColor("#576e55"), leftIndent=16, rightIndent=8, spaceAfter=10),
        "list": ParagraphStyle("List", fontName=serif, fontSize=10.3, leading=15.2, textColor=colors.HexColor(INK), leftIndent=10, firstLineIndent=-10, spaceAfter=7),
    }
    page_meta = ParagraphStyle("PageMeta", parent=styles["meta"], keepWithNext=True)
    journal_styles = dict(styles)
    journal_styles["body"] = ParagraphStyle("JournalBody", parent=styles["body"], fontSize=10, leading=14, spaceAfter=7)
    journal_styles["h2"] = ParagraphStyle("JournalH2", parent=styles["h2"], fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=5)

    class SourceMarker(ActionFlowable):
        def __init__(self, record):
            super().__init__(())
            self.record = record

        def apply(self, document):
            # An action updates provenance without consuming layout space or
            # marking a fresh page as already occupied by a zero-height box.
            document.source = self.record

    class BookDocument(BaseDocTemplate):
        def beforeDocument(self):
            self.source = {"id": "publication-cover", "title": book["title"], "kind": "cover"}
            self.physical_sources = {}

        def afterPage(self):
            self.physical_sources[self.page] = dict(self.source)

        def afterFlowable(self, flowable):
            if getattr(flowable, "book_title", None):
                record = flowable.book_title
                key = "source-" + record["id"]
                self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (0 if record["kind"] == "part" else 1, _inline(record["title"]), self.page, key))

    def furniture(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(PAPER))
        canvas.rect(0, 0, *PAGE_SIZE, stroke=0, fill=1)
        if doc.page > 1:
            canvas.setFont(sans, 7)
            canvas.setFillColor(colors.HexColor("#738271"))
            header = _plain(book["title"])
            while canvas.stringWidth(header, sans, 7) > width:
                header = header[:-2]
            canvas.drawString(MARGIN, PAGE_SIZE[1] - 29, header)
            canvas.setStrokeColor(colors.HexColor("#d4dacc"))
            canvas.setLineWidth(.4)
            canvas.line(MARGIN, 35, PAGE_SIZE[0] - MARGIN, 35)
            canvas.drawString(MARGIN, 23, "READING EDITION")
            canvas.drawRightString(PAGE_SIZE[0] - MARGIN, 23, str(doc.page))
        canvas.restoreState()

    doc = BookDocument(str(pdf_path), pagesize=PAGE_SIZE, rightMargin=MARGIN, leftMargin=MARGIN,
                       topMargin=49, bottomMargin=49, title=_plain(book["title"]), author=_plain(book.get("author", "")),
                       subject="Codex book manuscript with programmatic still illustrations", pageCompression=1)
    frame = Frame(MARGIN, 49, width, PAGE_SIZE[1] - 98, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="reading", frames=frame, onPage=furniture))
    story = [SourceMarker({"id": "publication-cover", "title": book["title"], "kind": "cover"}),
             Spacer(1, 83), Paragraph("2 TREES / THE BOOK", styles["meta"]),
             Paragraph(_inline(book["title"]), styles["cover"]),
             HRFlowable(width="25%", thickness=2, color=colors.HexColor("#b2864b"), hAlign="LEFT"), Spacer(1, 25),
             Paragraph(_inline(book.get("author", "")) or "Working manuscript", styles["body"]),
             Paragraph(_inline(book.get("edition", "Codex parallel draft")), styles["meta"]),
             Paragraph("A reading edition of the current editable manuscript. Illustrations retain their captions and source notes.", styles["body"]),
             PageBreak(), SourceMarker({"id": "publication-contents", "title": "Contents", "kind": "contents"}),
             Paragraph("Contents", styles["title"])]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOCPart", fontName=sans_bold, fontSize=10, leading=14, leftIndent=0, firstLineIndent=0, spaceBefore=10, textColor=colors.HexColor(INK)),
                       ParagraphStyle("TOCPage", fontName=serif, fontSize=9.1, leading=13, leftIndent=12, firstLineIndent=0, spaceBefore=4, textColor=colors.HexColor(INK))]
    story.append(toc)
    figure_records = []
    for page in book["pages"]:
        story.extend([PageBreak(), SourceMarker({"id": page["id"], "title": page["title"], "kind": page["kind"]})])
        if page["kind"] == "part":
            story.extend([Spacer(1, 110), HRFlowable(width="18%", thickness=3, color=colors.HexColor("#b2864b"), hAlign="LEFT"), Spacer(1, 24)])
        story.append(Paragraph(_inline(" / ".join((page["kind"].upper(), page["strand"], page["status"]))), page_meta))
        heading = Paragraph(_inline(page["title"]), styles["title"])
        heading.book_title = page
        story.append(heading)
        groups = figure_groups(page, book["assets"])
        paragraph_count = prose_paragraph_count(page["body"])
        figure_number = 0

        def add_figures(anchor):
            nonlocal figure_number
            for key in groups.get(anchor, []):
                figure_number += 1
                asset = book["assets"][key]
                source_path = _asset_path(home, asset)
                with PILImage.open(source_path) as im:
                    original_size = im.size
                    # Normalize formats ReportLab may not decode and honor EXIF orientation.
                    from PIL import ImageOps
                    normalized = ImageOps.exif_transpose(im).convert("RGB")
                    target = folder / ("figure-" + str(len(figure_records) + 1).zfill(4) + ".png")
                    normalized.save(target)
                    iw, ih = normalized.size
                scale = min(width / iw, 315 / ih)
                image = Image(str(target), width=iw*scale, height=ih*scale)
                image.hAlign = "CENTER"
                caption = f"Figure {figure_number}. " + str(asset.get("caption", ""))
                figure_group = [image, Spacer(1, 7), Paragraph(_inline(caption), styles["caption"])]
                if asset.get("provenance"):
                    figure_group.append(Paragraph(_inline("Source: " + str(asset["provenance"])), styles["figure_source"]))
                group_height = sum(flowable.wrap(width, 550)[1] + flowable.getSpaceBefore() + flowable.getSpaceAfter() for flowable in figure_group)
                if group_height <= 530:
                    # A complete illustration moves to the next page when needed;
                    # the image is never cropped to fit the remaining text area.
                    story.extend([Spacer(1, 10), KeepTogether(figure_group), Spacer(1, 8)])
                else:
                    # Long author captions may span pages. Protect the image and
                    # a short figure label, then let caption/source text paginate.
                    label = Paragraph(f"Figure {figure_number}", styles["caption"])
                    story.extend([Spacer(1, 10), KeepTogether([image, Spacer(1, 7), label]),
                                  Paragraph(_inline(str(asset.get("caption", ""))), styles["caption"]),
                                  *figure_group[3:], Spacer(1, 8)])
                figure_records.append({"source_page_id": page["id"], "asset_id": key, "source_path": str(source_path),
                                       "figure_number": figure_number,
                                       "placement": {"after_paragraph": anchor, "prose_paragraph_count": paragraph_count},
                                       "source_size": list(original_size), "draw_size_points": [iw*scale, ih*scale], "metadata": deepcopy(asset)})

        add_figures(0)
        for segment in body_segments(page["body"]):
            story.extend(_body_flowables(segment["markdown"], journal_styles if page["kind"] == "journal" else styles, width))
            if segment["paragraph"] is not None:
                add_figures(segment["paragraph"])
        add_figures(None)
    _notify(progress_callback, "Paginating the manuscript and its contents...")
    doc.multiBuild(story)
    _notify(progress_callback, "Rendering physical PDF pages for the reader...")
    text_reader = PdfReader(str(pdf_path))
    png_dir = folder / "pages"
    png_dir.mkdir()
    pages = []
    with pdfium.PdfDocument(str(pdf_path)) as rendered:
        for i, physical in enumerate(text_reader.pages):
            source = doc.physical_sources[i + 1]
            text = physical.extract_text() or ""
            text = re.sub(r"\nREADING EDITION\s*\n\d+\s*", "\n", text)
            if i:
                text = text.replace(_plain(book["title"]), "", 1).strip()
            target = png_dir / f"page-{i+1:04d}.png"
            raster = rendered[i]
            bitmap = raster.render(scale=200/72)
            bitmap.to_pil().save(target, dpi=(200, 200))
            bitmap.close()
            raster.close()
            pages.append({"path": str(target), "page_number": i+1, "source_page_id": source["id"],
                          "title": source["title"], "kind": source["kind"], "word_count": words(text), "text": text})
            if (i+1) % 10 == 0 or i+1 == len(text_reader.pages):
                _notify(progress_callback, f"Rendered {i+1} / {len(text_reader.pages)} pages.")
    manifest_path = folder / "publication.json"
    from .book_visuals import book_fingerprint
    result = {"schema": "two-trees-publication/v1", "created": stamp(), "title": book["title"], "edition": book.get("edition", ""),
              "pdf": str(pdf_path), "pages": pages, "manifest": str(manifest_path), "output_dir": str(folder),
              "page_size_points": list(PAGE_SIZE), "raster_dpi": 200, "figures": figure_records,
              "source_updated": book.get("updated"), "book_sha256": book_fingerprint(book), "book_source_ids": [p["id"] for p in book["pages"]],
              "layout_authority": "PDF; reader and video use its rendered physical pages"}
    _write_json(manifest_path, result)
    return result


def _ffmpeg():
    explicit = os.environ.get("TWO_TREES_FFMPEG")
    try:
        from two_v_demo.audio import resolve_executable
        return resolve_executable("ffmpeg", explicit)
    except (ImportError, RuntimeError, OSError):
        pass
    candidate = shutil.which(explicit or "ffmpeg")
    if candidate:
        return candidate
    if explicit and Path(explicit).is_file():
        return explicit
    try:
        candidates = list((Path.home() / "AppData/Local/Microsoft/WinGet/Packages").glob("*FFmpeg*/*/bin/ffmpeg.exe"))
    except OSError:
        candidates = []
    candidates += [Path("C:/ffmpeg/bin/ffmpeg.exe"), Path("C:/Tools/ffmpeg/bin/ffmpeg.exe")]
    existing = next((path for path in candidates if path.is_file()), None)
    if existing:
        return str(existing)
    raise RuntimeError("FFmpeg was not found. Set TWO_TREES_FFMPEG to its executable path for silent video export.")


def _metadata_text(value):
    return str(value).replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\r", " ").replace("\n", " ")


def export_readthrough(publication: dict, output_dir=None, words_per_minute=130, minimum_seconds=6,
                       fps=24, size=(1920, 1080), progress_callback=None) -> dict:
    """Encode a silent MP4 holding each complete physical page for reading.

    Timing is a reading estimate, not alignment with speech. Page/chapter timings
    and the exact page text are exported for subsequent narration or AI assembly.
    """
    from PIL import Image, ImageOps
    rate = _positive(words_per_minute, "Words per minute")
    minimum = _positive(minimum_seconds, "Minimum page seconds")
    frame_rate = _positive(fps, "Frame rate")
    if frame_rate != int(frame_rate) or frame_rate > 120:
        raise ValueError("Frame rate must be a whole number between 1 and 120.")
    fps = int(frame_rate)
    if not isinstance(size, (tuple, list)) or len(size) != 2:
        raise ValueError("Video size must be a width and height pair.")
    dimensions = [_positive(n, "Video dimension") for n in size]
    if any(n != int(n) or n % 2 or n < 64 or n > 8192 for n in dimensions):
        raise ValueError("Video dimensions must be even integers between 64 and 8192.")
    size = tuple(int(n) for n in dimensions)
    pages = publication.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Export a publication with physical pages before creating a readthrough.")
    timing, elapsed_frames = [], 0
    for index, page in enumerate(pages):
        path = Path(page.get("path", ""))
        if not path.is_file():
            raise FileNotFoundError("Publication page image is missing: " + str(path))
        count = page.get("word_count", 0)
        try:
            valid_count = not isinstance(count, bool) and isinstance(count, (float, int)) and math.isfinite(count) and count >= 0
        except OverflowError:
            valid_count = False
        if not valid_count:
            raise ValueError("Page word count must be a finite nonnegative number.")
        duration_frames = max(minimum, 60 * count/rate)*fps
        if not math.isfinite(duration_frames):
            raise ValueError("Page reading duration exceeds the supported numeric range.")
        frames = max(1, math.ceil(duration_frames))
        timing.append({"page_number": page.get("page_number", index+1), "source_page_id": page.get("source_page_id", ""),
                       "title": page.get("title", ""), "path": str(path.resolve()), "word_count": count,
                       "start_seconds": elapsed_frames/fps, "duration_seconds": frames/fps,
                       "end_seconds": (elapsed_frames+frames)/fps, "frames": frames, "text": page.get("text", "")})
        elapsed_frames += frames
    ffmpeg = _ffmpeg()
    base = output_dir if output_dir is not None else Path(publication.get("output_dir", Path(publication.get("pdf", ".")).parent))
    folder = _folder(base, "silent-readthrough")
    stills = folder / "stills"
    stills.mkdir()
    margin = max(8, round(size[1]*.025))
    for i, page in enumerate(timing):
        with Image.open(page["path"]) as source:
            contained = ImageOps.contain(source.convert("RGB"), (size[0]-margin*2, size[1]-margin*2), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", size, "#203a30")
            canvas.paste(contained, ((size[0]-contained.width)//2, (size[1]-contained.height)//2))
            canvas.save(stills / f"page-{i+1:04d}.png")
        _notify(progress_callback, f"Preparing still page {i+1} / {len(timing)}.")
    # The concat demuxer reads each PNG once; FFmpeg repeats decoded frames. No
    # Python per-frame loop or directory of duplicate images is necessary.
    concat_path = folder / "pages.ffconcat"
    lines = ["ffconcat version 1.0"]
    for i, page in enumerate(timing):
        lines.extend([f"file 'stills/page-{i+1:04d}.png'", f"option framerate {fps}", f"duration {page['duration_seconds']:.9f}"])
    lines.extend([f"file 'stills/page-{len(timing):04d}.png'", f"option framerate {fps}"])
    concat_path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    chapters = []
    for page in timing:
        if chapters and chapters[-1]["source_page_id"] == page["source_page_id"]:
            chapters[-1]["end_seconds"] = page["end_seconds"]
        else:
            chapters.append({key: page[key] for key in ("source_page_id", "title", "start_seconds", "end_seconds")})
    metadata = [";FFMETADATA1", "title=" + _metadata_text(publication.get("title", "2 trees")), "comment=Silent still-page readthrough; timing estimates reading pace; no narration"]
    for chapter in chapters:
        metadata.extend(["[CHAPTER]", "TIMEBASE=1/1000", "START="+str(round(chapter["start_seconds"]*1000)),
                         "END="+str(round(chapter["end_seconds"]*1000)), "title="+_metadata_text(chapter["title"])])
    metadata_path = folder / "chapters.ffmetadata"
    metadata_path.write_text("\n".join(metadata)+"\n", encoding="utf-8")
    video = folder / "2-trees-silent-readthrough.mp4"
    command = [ffmpeg, "-n", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_path),
               "-f", "ffmetadata", "-i", str(metadata_path), "-map", "0:v:0", "-map_metadata", "1", "-map_chapters", "1",
               "-vf", f"fps={fps}", "-frames:v", str(elapsed_frames), "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
               "-crf", "20", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(video)]
    _notify(progress_callback, f"Encoding silent readthrough ({elapsed_frames/fps:.1f} seconds)...")
    # A file-backed log avoids pipe deadlocks during long book encodes.
    log_path = folder / "ffmpeg.log"
    with log_path.open("x", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, cwd=folder,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        while True:
            try:
                code = process.wait(timeout=15)
                break
            except subprocess.TimeoutExpired:
                _notify(progress_callback, "Encoding the silent page readthrough...")
    if code or not video.is_file() or video.stat().st_size == 0:
        raise RuntimeError("Readthrough export failed: " + log_path.read_text(encoding="utf-8", errors="replace")[-2500:])
    transcript = folder / "page-text.txt"
    transcript.write_text("Silent still-page readthrough. No narration is included.\n\n" + "\n\n".join(
        f"PAGE {p['page_number']} | {p['start_seconds']:.3f}-{p['end_seconds']:.3f} s | {p['title']}\n\n{p['text']}" for p in timing), encoding="utf-8")
    manifest = folder / "readthrough.json"
    result = {"schema": "two-trees-readthrough/v1", "created": stamp(), "video": str(video), "manifest": str(manifest), "output_dir": str(folder),
              "publication_manifest": publication.get("manifest", ""), "source_pdf": publication.get("pdf", ""), "silent": True,
              "narration": None, "timing_basis": "Physical-page word counts and configurable reading pace; no speech synchronization",
              "words_per_minute": rate, "minimum_seconds": minimum, "fps": fps, "size": list(size),
              "duration_seconds": elapsed_frames/fps, "frames": elapsed_frames, "pages": timing, "chapters": chapters,
              "text": str(transcript), "chapter_metadata": str(metadata_path)}
    _write_json(manifest, result)
    _notify(progress_callback, "Silent readthrough ready.")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="Local JSON publication export request")
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    print(json.dumps(export_publication(request["book"], Path(request["home"]), request.get("output_dir")), ensure_ascii=True))
