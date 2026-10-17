"""Lay out My Own Home, My Own Dome and write the PDF.

An 8.5-inch square picture book: the cover, a title page, one page per stanza
(the picture above, the verse below), and an end page that says where every
number in the book comes from. The verse is read from the manuscript, so the
book and the website's preview (website/scripts/export_facts.py) quote the same
lines. Each picture is also kept in ``assets/images/scenes`` under a name for
what it shows, and the PDF goes into a new numbered folder of the library.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import assetlib
from two_v_demo.deliverables import next_version_path
from wedge_book import outline

from . import pictures as kp

ROOT = Path(__file__).resolve().parent.parent
VERSE = ROOT / "books" / "my-own-home-my-own-dome" / "verse.md"
STEM = "my-own-home-my-own-dome"
EXPORT = ROOT / "deliverables" / "book" / f"{STEM}.pdf"

TRIM_IN = 8.5
DPI = 300
PAGE = int(TRIM_IN * DPI)                    # 2550 px square
PICTURE_H = int(PAGE * 0.69)                 # the picture above, the verse below
MARGIN = int(PAGE * 0.075)

FONT_VERSE = "C:/Windows/Fonts/BOOKOS.TTF"   # Bookman Old Style: the picture-book face
FONT_VERSE_B = "C:/Windows/Fonts/BOOKOSB.TTF"
PAPER = (250, 244, 230)
INK = (44, 30, 20)
ACCENT = (150, 72, 24)

#: What each picture shows -- its name in the asset library.
NAMES = {
    "cover": "pip-and-her-dome-at-sunset",
    "1": "pip-in-the-town-of-boxes",
    "2": "pip-dreams-of-a-round-home",
    "3": "pip-walks-past-the-lumber-yard",
    "4": "pip-meets-the-fallen-pine",
    "5": "pip-and-her-saw-tape-level-and-lunch",
    "6": "the-log-split-into-eight-wedges",
    "7": "pip-and-the-stack-of-wedges",
    "8": "the-longest-strut-in-chalk",
    "9": "the-dome-measured-across-and-tall",
    "10": "wedges-in-pinwheels-of-three",
    "11": "pip-and-the-last-triangles",
    "12": "the-neighbours-come-running",
    "13": "pips-dome-written-down",
    "14": "pip-and-the-boy-with-a-fallen-panel",
    "15": "the-dome-club-trading-panels",
    "16": "domes-on-the-hill-at-night",
}


def stanzas() -> tuple[str, list[str]]:
    text = VERSE.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    verse = text.split("\n---\n", 1)[1]
    return title, [s.strip() for s in verse.strip().split("\n\n") if s.strip()]


def _fit(path: str, lines: list[str], size: int, width: int) -> ImageFont.FreeTypeFont:
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    while size > 20:
        f = ImageFont.truetype(path, size)
        if max(probe.textlength(line, font=f) for line in lines) <= width:
            return f
        size -= 2
    return ImageFont.truetype(path, size)


def _typeset(text: str) -> str:
    """Typewriter dashes and quotes, as the manuscript is typed, set as a book sets them."""
    out, open_ = [], True
    for ch in text.replace(" -- ", " \u2014 ").replace("--", "\u2014"):
        if ch == '"':
            out.append("\u201c" if open_ else "\u201d")
            open_ = not open_
        else:
            out.append(ch)
    text = "".join(out)
    return text.replace(" '", " \u2018").replace("'", "\u2019")


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------

def verse_font() -> ImageFont.FreeTypeFont:
    """One size for the whole book: the largest that fits its longest line."""
    _title, verses = stanzas()
    return _fit(FONT_VERSE, [line for v in verses for line in _typeset(v).splitlines()], 92, PAGE - 2 * MARGIN)


def story_page(picture: Image.Image, stanza: str, number: int) -> Image.Image:
    page = Image.new("RGB", (PAGE, PAGE), PAPER)
    page.paste(picture.resize((PAGE, PICTURE_H), Image.LANCZOS), (0, 0))
    draw = ImageDraw.Draw(page)
    draw.line((0, PICTURE_H, PAGE, PICTURE_H), fill=(120, 82, 46), width=6)
    lines = _typeset(stanza).splitlines()      # whole stanza: a quote may open on one line and close on another
    font = verse_font()
    lead = int(font.size * 1.42)
    top = PICTURE_H + (PAGE - PICTURE_H - lead * len(lines)) // 2 - int(font.size * 0.15)
    for i, line in enumerate(lines):
        draw.text((MARGIN, top + i * lead), line, font=font, fill=INK)
    folio = ImageFont.truetype(FONT_VERSE, 40)
    draw.text((PAGE // 2, PAGE - int(MARGIN * 0.45)), str(number), font=folio, fill=(140, 120, 96), anchor="mm")
    return page


def cover_page(picture: Image.Image, title: str) -> Image.Image:
    page = picture.resize((PAGE, PAGE), Image.LANCZOS).convert("RGBA")
    over = Image.new("RGBA", page.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(over)
    # a soft dark ground behind the title, so it reads over the sky
    for y in range(int(PAGE * 0.36)):
        a = int(150 * (1 - y / (PAGE * 0.36)) ** 1.4)
        draw.line((0, y, PAGE, y), fill=(18, 12, 8, a))
    head, tail = title.split(",", 1) if "," in title else (title, "")
    for text, y, share in ((head + ",", 0.075, 0.105), (tail.strip(), 0.185, 0.105)):
        f = _fit(kp.FONT_TITLE, [text], int(PAGE * share), int(PAGE * 0.88))
        draw.text((PAGE // 2 + 8, int(PAGE * y) + 8), text, font=f, fill=(20, 10, 4, 160), anchor="ma")
        draw.text((PAGE // 2, int(PAGE * y)), text, font=f, fill=(255, 244, 222, 255), anchor="ma")
    sub = ImageFont.truetype(FONT_VERSE_B, int(PAGE * 0.030))
    draw.rectangle((0, int(PAGE * 0.905), PAGE, PAGE), fill=(18, 12, 8, 150))
    draw.text((PAGE // 2, int(PAGE * 0.952)), f"A rhyming picture book  \u00b7  {outline.AUTHOR}", font=sub,
              fill=(255, 236, 200, 255), anchor="mm")
    return Image.alpha_composite(page, over).convert("RGB")


def title_page(title: str) -> Image.Image:
    page = Image.new("RGB", (PAGE, PAGE), PAPER)
    draw = ImageDraw.Draw(page)
    f = _fit(kp.FONT_TITLE, [title], 150, PAGE - 2 * MARGIN)
    draw.text((PAGE // 2, int(PAGE * 0.38)), title, font=f, fill=ACCENT, anchor="mm")
    draw.text((PAGE // 2, int(PAGE * 0.47)), "written by", font=ImageFont.truetype(FONT_VERSE, 56), fill=INK, anchor="mm")
    draw.text((PAGE // 2, int(PAGE * 0.53)), outline.AUTHOR, font=ImageFont.truetype(FONT_VERSE_B, 84), fill=INK, anchor="mm")
    small = ImageFont.truetype(FONT_VERSE, 38)
    for i, line in enumerate((
        "Every picture is drawn in the same world as the grown-ups' book,",
        f"{outline.TITLE}: the same dome, the same log, the same saw.",
        f"Copyright \u00a9 2026 {outline.AUTHOR}.  zeanahlab.com/kids",
    )):
        draw.text((PAGE // 2, int(PAGE * 0.80) + i * 60), line, font=small, fill=(110, 92, 72), anchor="mm")
    return page


def numbers_page() -> Image.Image:
    """For the grown-ups: where the numbers in the pictures come from."""
    from wedge_book import tokens
    import seed_model

    d = kp.sheet()
    page = Image.new("RGB", (PAGE, PAGE), PAPER)
    draw = ImageDraw.Draw(page)
    draw.text((MARGIN, MARGIN), "For the grown-ups: the numbers", font=ImageFont.truetype(kp.FONT_TITLE, 96), fill=ACCENT)
    body = ImageFont.truetype(FONT_VERSE, 60)
    paras = [
        f"Pip's dome is a real one. Every number in the pictures is worked out by the same code that "
        f"designs the dome in {outline.TITLE}, from one measurement: the longest strut, "
        f"{d['longIn']} inches. From it come {d['diameterFt']:g} feet across, {d['heightFt']:g} feet tall, "
        f"{sum(p['count'] for p in d['panels'])} triangles and {d['memberCount']} wedges.",
        f"The frame weight, {d['frameLb']:,} pounds, is the wood alone: {d['woodCuft']:g} cubic feet of "
        f"green pine at {seed_model.declared('pine_green_lb_per_cuft'):g} pounds a cubic foot, a published "
        f"density. The screws and glue are priced in the model, not weighed. The {tokens.resolve('{{hr.total}}')} "
        f"hours of frame work are the book's own count.",
        f"The pictures are drawn in the book's 3-D world, which is built from a heavier "
        f"{kp.cw._scene().COVER_TRUNK_IN:g}-inch log than the {seed_model.SEED_TRUNK_DIAMETER_IN:g}-inch "
        f"log the numbers are for, so the frame reads at picture size. The shape is the same.",
        "Domes with the same longest strut take the same panels. On zeanahlab.com/domes, people "
        "with the same size dome find each other -- just like Pip's club.",
    ]
    y = MARGIN + 230
    for para in paras:
        words, line = _typeset(para).split(), ""
        for w in words:
            trial = (line + " " + w).strip()
            if draw.textlength(trial, font=body) > PAGE - 2 * MARGIN:
                draw.text((MARGIN, y), line, font=body, fill=INK); y += 86; line = w
            else:
                line = trial
        draw.text((MARGIN, y), line, font=body, fill=INK)
        y += 86 + 60
    return page


# ----------------------------------------------------------------------
# Assets and the PDF
# ----------------------------------------------------------------------

def keep_asset(img: Image.Image, key: str) -> Path:
    """Put a picture in assets/images/scenes under its name; a new version only if it changed."""
    name = NAMES[key]
    catalogue = assetlib.load()
    folder = assetlib.folder("scenes")
    folder.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    data = buf.getvalue()
    versions = [e for e in catalogue.values() if e["name"] == name]
    if versions:
        newest = max(versions, key=lambda e: e["version"])
        if (assetlib.ASSETS / newest["file"]).read_bytes() == data:
            return assetlib.ASSETS / newest["file"]
    version = max((e["version"] for e in versions), default=0) + 1
    stem = name if version == 1 else f"{name}-v{version}"
    path = folder / f"{stem}.jpg"
    path.write_bytes(data)
    catalogue[stem] = {
        "name": name, "version": version, "file": path.relative_to(assetlib.ASSETS).as_posix(),
        "category": "scenes", "note": f"{STEM}: picture {key}, rendered in the Cabin World by kids_book.pictures.",
        "origin": "author", "original": None, "copy_of": None, "prompt": None}
    assetlib.save(catalogue)
    return path


def render_pictures(keys: list[str], out_dir: Path | None = None) -> dict[str, Image.Image]:
    shots = kp.shots()
    made = {}
    wide = kp.Painter(PAGE, PICTURE_H)
    for k in keys:
        if k != "cover":
            made[k] = wide.picture(shots[k])
    wide.release()
    if "cover" in keys:
        square = kp.Painter(PAGE, PAGE)
        made["cover"] = square.picture(shots["cover"])
        square.release()
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for k, img in made.items():
            img.save(out_dir / f"{NAMES[k]}.jpg", quality=88)
    return made


def build() -> Path:
    import pymupdf

    title, verses = stanzas()
    if len(verses) != len(NAMES) - 1:
        raise RuntimeError(f"{len(verses)} stanzas but {len(NAMES) - 1} pictures: the manuscript and the pictures disagree")
    pics = render_pictures(list(NAMES))
    for k, img in pics.items():
        keep_asset(img, k)
    pages = [cover_page(pics["cover"], title), title_page(title)]
    pages += [story_page(pics[str(i + 1)], s, i + 1) for i, s in enumerate(verses)]
    pages.append(numbers_page())

    doc = pymupdf.open()
    side = TRIM_IN * 72
    for img in pages:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=86, dpi=(DPI, DPI))
        page = doc.new_page(width=side, height=side)
        page.insert_image(page.rect, stream=buf.getvalue())
    doc.set_metadata({"title": title, "author": outline.AUTHOR, "subject": "A rhyming picture book of the wedge-dome build",
                      "creator": "DomeSim kids_book", "producer": "PyMuPDF"})
    out = next_version_path(EXPORT)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    return out


def validate(path: Path) -> list[str]:
    import pymupdf

    doc = pymupdf.open(path)
    problems = []
    _title, verses = stanzas()
    if len(doc) != len(verses) + 3:
        problems.append(f"{len(doc)} pages, expected {len(verses) + 3}")
    side = round(TRIM_IN * 72)
    if {(round(p.rect.width), round(p.rect.height)) for p in doc} != {(side, side)}:
        problems.append("pages are not all 8.5 in square")
    if any(not p.get_images() for p in doc):
        problems.append("a page has no picture")
    return problems


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Build My Own Home, My Own Dome")
    ap.add_argument("--pictures", nargs="*", help="render just these pictures (cover, 1..16) to --out, to look at")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.pictures is not None:
        out = a.out or (ROOT / ".kids-book-pictures")
        render_pictures(a.pictures or list(NAMES), out)
        print(f"pictures in {out}")
        return 0
    path = build()
    print(f"wrote {path.relative_to(ROOT)}")
    problems = validate(path)
    for p in problems:
        print(f"  PROBLEM: {p}")
    return 1 if problems else 0
