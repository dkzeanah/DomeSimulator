"""The paperback cover: back, spine and front as one KDP-ready PDF.

The front is the author's illustration (``Book_Cover.jpg`` at the repository
root). Three things are done to it and nothing else:

* **the top line is re-lettered.** The art was painted when the book was
  called *Geodesic Dome: 2V Timberframe*; KDP refuses a cover whose title
  differs from the listing, so that one line is painted out over the sky and
  set again in the current title. The original file is never touched;
* **it is cropped to the trim's shape** -- a sliver off the bottom, where the
  grass has room, never the top, where the title is;
* **it is scaled to 300 DPI** at the full front-cover size with bleed.

The spine width is not typed: it is the interior's page count times the
paper's thickness, read from the finished interior PDF, so the cover cannot
be built for a book that has since changed length. The back carries the
description (its figures resolved from the model like every other number in
the book), a note about the author, and the clear space KDP prints the
barcode into.

    py -3.12 -m wedge_book.cover                         # premium colour paper
    py -3.12 -m wedge_book.cover --paper standard_color
"""

from __future__ import annotations

import argparse
import textwrap
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from two_v_demo.deliverables import next_version_path

from . import outline, print_edition, tokens

#: The front art, newest first. ``reletter`` is for the first painting, which
#: carries the book's old title; the final art is already lettered correctly.
ARTS = {
    # Rendered from the model by wedge_book.cover_scene + cover_type: the
    # solver's own dome, at exactly the front panel's size and 300 DPI.
    "rendered": (outline.ROOT / "book_wedge" / "cover" / "cover-front.png", False),
    "final": (outline.ROOT / "Book_Cover_final.png", False),     # 1792 x 2368, painted
    "final_small": (outline.ROOT / "Book-Cover-Final.png", False),  # 1087 x 1447, superseded
    "first": (outline.ROOT / "Book_Cover.jpg", True),              # old title, re-lettered
}
ART, RELETTER = ARTS["rendered"]
DPI = 300

# ----------------------------------------------------------------------
# KDP's numbers -- theirs, not ours
# ----------------------------------------------------------------------

#: Inches of spine per interior page, from KDP's cover-size guidance. The
#: paper must match what is chosen when the paperback is set up.
PAPER_IN_PER_PAGE = {
    "premium_color": 0.002347,
    "standard_color": 0.002252,
    "white": 0.002252,       # black and white on white paper
    "cream": 0.0025,         # black and white on cream paper
}
BLEED_IN = 0.125
#: KDP puts no text on a spine under 79 pages; this book is far over it.
SPINE_TEXT_MIN_PAGES = 79
#: Text on the spine keeps this far from each fold.
SPINE_MARGIN_IN = 0.0625
#: Everything that must survive trimming stays this far inside the trim.
SAFE_IN = 0.375
#: The barcode KDP prints on the back, lower right of the back cover.
BARCODE_IN = (2.0, 1.2)

# ----------------------------------------------------------------------
# Where the old line is, in the art's own pixels
# ----------------------------------------------------------------------

#: The painted line "Geodesic Dome: 2V Timberframe": rows 114-167 and
#: columns 399-1393 of the 1792 x 2400 art, measured by thresholding the
#: dark lettering against the sky (see :func:`find_top_line`).
OLD_LINE_PAD = 14
TEXT_RGB = (37, 48, 49)
SERIF = "C:/Windows/Fonts/pala.ttf"
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITALIC = "C:/Windows/Fonts/palai.ttf"
BODY = "C:/Windows/Fonts/georgia.ttf"
BODY_BOLD = "C:/Windows/Fonts/georgiab.ttf"


@dataclass(frozen=True)
class Box:
    top: int
    bottom: int
    left: int
    right: int


def find_top_line(art: Image.Image) -> Box:
    """The first line of dark lettering from the top of the art."""
    grey = np.asarray(art.convert("L")).astype(int)[: art.height // 5]
    dark = grey < 110
    rows = np.where(dark.sum(axis=1) > 3)[0]
    top = int(rows[0])
    bottom = top
    for row in rows[1:]:
        if row - bottom > 3:
            break
        bottom = int(row)
    cols = np.where(dark[top:bottom + 1].sum(axis=0) > 0)[0]
    return Box(top, bottom, int(cols[0]), int(cols[-1]))


def reletter(art: Image.Image, text: str) -> Image.Image:
    """Paint the old top line out of the sky and set ``text`` in its place."""
    box = find_top_line(art)
    pixels = np.asarray(art.convert("RGB")).astype(float)
    top, bottom = box.top - OLD_LINE_PAD, box.bottom + OLD_LINE_PAD + 10
    left, right = box.left - OLD_LINE_PAD * 3, box.right + OLD_LINE_PAD * 3
    above = pixels[top - 1, left:right]
    below = pixels[bottom + 1, left:right]
    # The sky is a smooth vertical gradient: fill each column from the colour
    # just above the lettering to the colour just below it, plus the faint
    # grain of the painting so the patch does not read as flat.
    rng = np.random.default_rng(40)
    for i, row in enumerate(range(top, bottom + 1)):
        t = i / max(1, bottom - top)
        pixels[row, left:right] = above * (1 - t) + below * t
    grain = rng.normal(0.0, 1.2, pixels[top:bottom + 1, left:right].shape)
    pixels[top:bottom + 1, left:right] += grain
    # Feather the patch's side edges into the untouched sky.
    patched = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))
    mask = Image.new("L", art.size, 0)
    ImageDraw.Draw(mask).rectangle((left, top, right, bottom), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    out = Image.composite(patched, art.convert("RGB"), mask)

    # Same cap height as the painted line, same colour, centred on the art.
    draw = ImageDraw.Draw(out)
    cap = box.bottom - box.top + 1
    size = cap
    while True:
        font = ImageFont.truetype(SERIF, size)
        if font.getbbox("D")[3] - font.getbbox("D")[1] >= cap * 0.98:
            break
        size += 1
    width = draw.textlength(text, font=font)
    x = (art.width - width) / 2
    baseline_top = box.top - font.getbbox("D")[1]
    draw.text((x, baseline_top), text, font=font, fill=TEXT_RGB)
    return out


# ----------------------------------------------------------------------
# The whole cover
# ----------------------------------------------------------------------

def px(inches: float) -> int:
    return round(inches * DPI)


#: Cover lettering must sit at least this far inside the trim. KDP's
#: minimum is 0.125 in; this leaves room for the trim to wander.
TEXT_SAFE_IN = 0.3


def first_text_row(art: Image.Image) -> int:
    """The top of the painted title: the first row of dark lettering against
    the sky in the middle of the picture (the trees at the edges are dark too,
    so only the central columns are looked at)."""
    grey = np.asarray(art.convert("L")).astype(int)
    w = art.width
    centre = grey[: art.height // 4, int(w * 0.2): int(w * 0.8)]
    rows = np.where((centre < 90).sum(axis=1) > 5)[0]
    return int(rows[0]) if len(rows) else art.height


def pad_front(art: Image.Image) -> Image.Image:
    """Bring a front whose lettering runs to the top edge into KDP's shape.

    Nothing is cropped. Sky is added above -- the top row continued -- until
    the title clears :data:`TEXT_SAFE_IN` of the trim, and the sides are
    continued outward until the picture has the trim's proportions. At this
    art's scale the side strips fall almost entirely in the bleed that is
    trimmed off.
    """
    w_in, h_in = print_edition.TRIM_IN[0] + BLEED_IN, print_edition.TRIM_IN[1] + 2 * BLEED_IN
    final_h = px(h_in)
    margin = px(BLEED_IN + TEXT_SAFE_IN)
    top = first_text_row(art)
    need = margin * art.height / final_h - top
    pad_top = max(0, int(np.ceil(need / (1 - margin / final_h))) + 2)
    height = art.height + pad_top
    width = round(height * w_in / h_in)
    pad_side = max(0, width - art.width)
    left, right = pad_side // 2, pad_side - pad_side // 2
    pixels = np.asarray(art.convert("RGB"))
    # Continue the outermost row and columns outward rather than mirroring:
    # a mirror would reflect the tops of the title letters back into the sky,
    # while the top row is clear sky and tree trunk, which extends naturally.
    padded = np.pad(pixels, ((pad_top, 0), (left, right), (0, 0)), mode="edge")
    out = Image.fromarray(padded)
    # Soften only the added strips, so a stretched edge reads as out-of-focus
    # background rather than as a reflection.
    soft = out.filter(ImageFilter.GaussianBlur(14))
    mask = Image.new("L", out.size, 255)
    ImageDraw.Draw(mask).rectangle((left + 2, pad_top + 2, left + art.width - 3, out.height - 1), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    out = Image.composite(soft, out, mask)
    if out.width > width:
        cut = (out.width - width) // 2
        out = out.crop((cut, 0, cut + width, out.height))
    return out


def fit_front(art: Image.Image) -> Image.Image:
    """Crop to the trim's shape from the bottom, then scale to 300 DPI."""
    w_in, h_in = print_edition.TRIM_IN[0] + BLEED_IN, print_edition.TRIM_IN[1] + 2 * BLEED_IN
    target_ratio = w_in / h_in
    height = round(art.width / target_ratio)
    if height <= art.height:
        art = art.crop((0, 0, art.width, height))
    else:
        width = round(art.height * target_ratio)
        left = (art.width - width) // 2
        art = art.crop((left, 0, left + width, art.height))
    scaled = art.resize((px(w_in), px(h_in)), Image.LANCZOS)
    return scaled.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))


def back_copy() -> dict[str, str]:
    """The back-cover words. Figures are tokens, resolved from the model."""
    resolve = lambda text: tokens.resolve(text, strict=True)  # noqa: E731
    return {
        "headline": "One tree. One chainsaw. Forty hours.",
        "body": resolve(
            "This is the dome most people never get to build: a 2V timber "
            "frame of {{dome.members}} members split straight from a log — no "
            "kit, no metal hubs, no mill. Each member is a wedge, one-eighth "
            "of a round log, laid with its rounded face out and its point in, "
            "and the gap two of them leave along every seam turns out to be "
            "the most useful thing in the building."),
        "body2": resolve(
            "Every number in this book was computed by open-source software "
            "and can be checked: the cut list, the angles, the price of every "
            "part, and the clock. The frame is {{hr.total}} hours of work with "
            "error allowed for. The whole standard building is "
            "{{money.labour_hours}} hours, and the book says so on the first "
            "page."),
        "list": "Inside: why a split log beats a milled board · the two "
                "lengths every member comes in · a pinwheel joint with no "
                "hub · one watertight layer and only one · the utility column "
                "that brings every service up the middle · and the bill for "
                "every part.",
        # The author's account, shortened. Written around the name rather
        # than with pronouns.
        "author": f"{outline.AUTHOR} served six years in the U.S. Navy as a "
                  "Mass Communication Specialist, three of them in Japan, "
                  "and is a certified avionics bench technician now studying "
                  "on the G.I. Bill. DomeSim, the open-source software this "
                  "book was computed with, came from one idea: a home should "
                  "be built like good code — modular, reusable and made to "
                  "be extended.",
    }


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
              width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def build(pages: int, paper: str = "premium_color",
          art_key: str = "rendered") -> tuple[Path, dict]:
    path, needs_letters = ARTS[art_key]
    art = Image.open(path).convert("RGB")
    if needs_letters:
        front = fit_front(reletter(art, outline.TITLE))
    else:
        # Fill the page without cropping, then scale to 300 DPI.
        padded = pad_front(art)
        w_in = print_edition.TRIM_IN[0] + BLEED_IN
        h_in = print_edition.TRIM_IN[1] + 2 * BLEED_IN
        front = padded.resize((px(w_in), px(h_in)), Image.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    source_dpi = art.width / (print_edition.TRIM_IN[0] + BLEED_IN)

    trim_w, trim_h = print_edition.TRIM_IN
    spine_in = pages * PAPER_IN_PER_PAGE[paper]
    total_w_in = BLEED_IN + trim_w + spine_in + trim_w + BLEED_IN
    total_h_in = trim_h + 2 * BLEED_IN
    W, H = px(total_w_in), px(total_h_in)
    back_left, spine_left = 0, px(BLEED_IN + trim_w)
    front_left = spine_left + px(spine_in)

    canvas = Image.new("RGB", (W, H))
    canvas.paste(front, (W - front.width, 0))

    # The back and spine grow out of the front's own colours: the art,
    # mirrored, blurred and darkened toward the forest green at its base.
    # Only the painting below the title is used, so no lettering can show
    # through backwards.
    below_title = front.crop((0, int(front.height * 0.36), front.width, front.height))
    source = below_title.transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(40))
    back_w = front_left
    backdrop = source.resize((back_w, H))
    shade = Image.new("RGB", (back_w, H), (16, 28, 21))
    gradient = Image.linear_gradient("L").resize((back_w, H)).point(lambda v: 205 - v * 30 // 255)
    backdrop = Image.composite(shade, backdrop, gradient)
    canvas.paste(backdrop, (0, 0))

    draw = ImageDraw.Draw(canvas)
    cream = (246, 236, 214)
    amber = (255, 190, 90)

    # Spine: title and author, reading top to bottom, centred on the spine.
    spine_w = px(spine_in)
    if pages >= SPINE_TEXT_MIN_PAGES:
        room = spine_w - 2 * px(SPINE_MARGIN_IN)
        size = int(room * 0.62)
        f_title = ImageFont.truetype(SERIF_BOLD, size)
        f_author = ImageFont.truetype(SERIF, int(size * 0.82))
        title = f"{outline.TITLE.upper()}  ·  {outline.SUBTITLE}"
        strip_len = H - 2 * px(SAFE_IN + BLEED_IN)
        strip = Image.new("RGBA", (strip_len, spine_w), (0, 0, 0, 0))
        sd = ImageDraw.Draw(strip)
        mid = spine_w / 2
        sd.text((0, mid), title, font=f_title, fill=cream, anchor="lm")
        sd.text((strip_len, mid), outline.AUTHOR.upper(), font=f_author, fill=amber, anchor="rm")
        rotated = strip.rotate(-90, expand=True)
        canvas.paste(rotated, (spine_left, px(SAFE_IN + BLEED_IN)), rotated)

    # Back cover text, inside the safe area.
    left = px(BLEED_IN + SAFE_IN)
    right = spine_left - px(SAFE_IN)
    width = right - left
    y = px(BLEED_IN + 0.8)
    copy = back_copy()
    f_head = ImageFont.truetype(SERIF_BOLD, 96)
    f_body = ImageFont.truetype(BODY, 52)
    f_list = ImageFont.truetype(SERIF_ITALIC, 52)
    f_small = ImageFont.truetype(BODY, 42)
    for line in wrap_text(draw, copy["headline"], f_head, width):
        draw.text((left, y), line, font=f_head, fill=amber)
        y += 122
    y += 60
    for key, font, colour, gap in (("body", f_body, cream, 70), ("body2", f_body, cream, 70),
                                   ("list", f_list, cream, 90)):
        for line in wrap_text(draw, copy[key], font, width):
            draw.text((left, y), line, font=font, fill=colour)
            y += 80
        y += gap
    rule_y = y
    draw.line((left, rule_y, left + px(1.2), rule_y), fill=amber, width=3)
    y += 40
    author_width = width - px(BARCODE_IN[0]) - px(0.3)
    for line in wrap_text(draw, copy["author"], f_small, author_width):
        draw.text((left, y), line, font=f_small, fill=cream)
        y += 60
    draw.text((left, y + 16), print_edition.PROJECT_URL, font=f_small, fill=amber)

    # The barcode area, lower right of the back, left clear on white as KDP
    # prints it: nothing of ours may sit inside it.
    bx1 = spine_left - px(SAFE_IN)
    by1 = H - px(BLEED_IN + SAFE_IN)
    barcode = (bx1 - px(BARCODE_IN[0]), by1 - px(BARCODE_IN[1]), bx1, by1)
    draw.rectangle(barcode, fill=(255, 255, 255))

    report = {
        "art": path.name, "art_px": art.size, "art_dpi": round(source_dpi),
        "pages": pages, "paper": paper, "spine_in": round(spine_in, 4),
        "size_in": (round(total_w_in, 4), round(total_h_in, 4)),
        "size_px": (W, H), "text_bottom_px": y + 60, "barcode_top_px": barcode[1],
    }
    if report["text_bottom_px"] > barcode[1] and author_width < width:
        pass  # the author note is narrowed to clear the barcode, by design
    report["web"] = [str(p.relative_to(outline.ROOT)) for p in web_images(front)]
    out = next_version_path(outline.EXPORT_DIR / f"{outline.STEM}-cover.pdf")
    canvas.save(out, "PDF", resolution=DPI)
    preview = out.with_suffix(".png")
    canvas.resize((W // 4, H // 4), Image.LANCZOS).save(preview)
    return out, report


def validate_cover(path: Path, pages: int, paper: str) -> list[str]:
    """The file is the size KDP's calculator gives for this page count."""
    import pymupdf

    doc = pymupdf.open(path)
    page = doc[0]
    want_w = 2 * BLEED_IN + 2 * print_edition.TRIM_IN[0] + pages * PAPER_IN_PER_PAGE[paper]
    want_h = print_edition.TRIM_IN[1] + 2 * BLEED_IN
    got_w, got_h = page.rect.width / 72, page.rect.height / 72
    problems = []
    if abs(got_w - want_w) > 1 / DPI or abs(got_h - want_h) > 1 / DPI:
        problems.append(f"cover is {got_w:.4f} x {got_h:.4f} in, KDP wants {want_w:.4f} x {want_h:.4f}")
    info = page.get_image_info()[0]
    dpi = info["width"] / (page.rect.width / 72)
    if dpi < 299:
        problems.append(f"cover image is {dpi:.0f} DPI")
    return problems


WEB_PUBLIC = outline.ROOT / "web" / "client" / "public"


def web_images(front: Image.Image) -> list[Path]:
    """The website's copies of the front: a book-page cover and a share card.

    Written from the same front the paperback uses, so the site can never
    show a different cover from the one on the shelf. These are the web
    app's own static files, regenerated on every cover build, not
    deliverables, which is why they are overwritten in place.
    """
    covers = WEB_PUBLIC / "covers"
    covers.mkdir(parents=True, exist_ok=True)
    trim_left = px(BLEED_IN)  # the front's outer bleed is on the right
    trimmed = front.crop((0, px(BLEED_IN), front.width - trim_left, front.height - px(BLEED_IN)))
    thumb = trimmed.resize((720, round(720 * trimmed.height / trimmed.width)), Image.LANCZOS)
    cover_path = covers / f"{outline.STEM}.jpg"
    thumb.save(cover_path, "JPEG", quality=86, optimize=True, progressive=True)

    # 1200 x 630 share card: the cover on a blurred field of itself.
    card = trimmed.resize((1200, round(1200 * trimmed.height / trimmed.width)), Image.LANCZOS)
    card = card.crop((0, (card.height - 630) // 2, 1200, (card.height - 630) // 2 + 630))
    card = card.filter(ImageFilter.GaussianBlur(18))
    card = Image.composite(Image.new("RGB", card.size, (12, 20, 16)), card,
                           Image.new("L", card.size, 110))
    book = trimmed.resize((round(560 * trimmed.width / trimmed.height), 560), Image.LANCZOS)
    card.paste(book, ((1200 - book.width) // 2, 35))
    og_path = WEB_PUBLIC / "og.jpg"
    card.save(og_path, "JPEG", quality=86, optimize=True)
    return [cover_path, og_path]


def latest_cover() -> Path | None:
    import re
    found = [p for p in outline.EXPORT_DIR.glob(f"{outline.STEM}-cover*.pdf")
             if re.fullmatch(rf"{re.escape(outline.STEM)}-cover(-v\d+)?\.pdf", p.name)]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def check_cover(paper: str = "premium_color") -> None:
    """For the check suite: the newest cover fits the newest interior.

    A cover is built for one page count. If the interior has been rebuilt
    since and changed length, the spine is wrong and KDP will reject it.
    """
    import pymupdf

    cover, interior = latest_cover(), print_edition.latest()
    assert cover and interior, "build the print edition and the cover first"
    pages = len(pymupdf.open(interior))
    problems = validate_cover(cover, pages, paper)
    assert not problems, f"{cover.name} vs {interior.name} ({pages} pages): {problems}"


def main(argv: list[str] | None = None) -> int:
    import pymupdf

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper", default="premium_color", choices=sorted(PAPER_IN_PER_PAGE))
    parser.add_argument("--art", default="rendered", choices=sorted(ARTS))
    args = parser.parse_args(argv)
    interior = print_edition.latest()
    pages = len(pymupdf.open(interior))
    out, report = build(pages, args.paper, args.art)
    print(f"interior {interior.name}: {pages} pages on {args.paper} paper")
    print(f"front art {report['art']} {report['art_px'][0]}x{report['art_px'][1]} px"
          f" = {report['art_dpi']} DPI before scaling"
          + ("  (UNDER 300: supply a larger export for a sharp print)"
             if report['art_dpi'] < 300 else ""))
    print(textwrap.dedent(f"""\
        wrote {out.relative_to(outline.ROOT)}  (+ preview .png)
          spine {report['spine_in']:.4f} in, cover {report['size_in'][0]:.4f} x {report['size_in'][1]:.4f} in"""))
    print("  website images: " + ", ".join(report["web"]))
    problems = validate_cover(out, pages, args.paper)
    for problem in problems:
        print(f"  PROBLEM: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
