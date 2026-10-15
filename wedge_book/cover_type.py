"""The cover's lettering, set over the rendered scene.

The layout follows the painted cover the author chose: a heavy slab title in
forest green with a geodesic sphere for its last O, the second line in wood,
the subtitle between rules, and the author on a board at the foot. Since
2026-10-12 this rendered front is the Complete Edition's -- THE 40 HOUR /
CABIN / COMPLETE EDITION, sold on the site -- and the author's painted cover
is the Amazon paperback's: :func:`reletter_painted` fills its old lettering
out of the sky and sets THE 40 HOUR / CABIN / 2V GEODESIC DOME WEDGE METHOD,
the title of :mod:`two_v_demo.book`, in the same style. The sphere is
drawn from the real 2V mesh seen from above -- the same drawing as the site's
logo -- so even the letter O is the book's own dome.

Everything is placed inside KDP's safe area: 0.3 in inside the trim, where
the trim is 0.125 in inside the top, bottom and outer edges of this front
panel. Its left edge is the spine fold, which has no bleed.

    py -3.12 -m wedge_book.cover_type      # scene.png -> cover-front.png,
                                           # and the painted cover re-lettered
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import cover_scene, outline

FONT_HEAVY = "C:/Windows/Fonts/ROCKEB.TTF"   # Rockwell Extra Bold
FONT_BOLD = "C:/Windows/Fonts/ROCKB.TTF"     # Rockwell Bold
DPI = 300
BLEED = round(0.125 * DPI)
SAFE = round(0.30 * DPI)

GREEN = (28, 58, 34)
WOOD_DARK, WOOD_LIGHT = (92, 52, 22), (150, 96, 46)
INK = (24, 22, 20)
CREAM = (246, 234, 206)

SUBTITLE_WORDS = outline.SUBTITLE.upper()     # COMPLETE EDITION
TITLE_TOP, TITLE_BOTTOM = "THE 40 HOUR", "CABIN"
REFERENCE_W = 2588
"""The rendered front's width; every spacing below is in its pixels and is
scaled for art of another size."""
PAINTED = outline.ROOT / "assets/images/covers/wedge-method-cover-v10.png"   # was Book-cover-final4.png
PAINTED_OUT = cover_scene.OUT_DIR / "painted-front.png"
PAINTED_BAND = (40, 396)
"""Rows of the painted art (1024 x 1536) that hold its old lettering:
GEODESIC DOME, WEDGE METHOD and the ribbon under them (which ends at row 352),
measured off the art, with room below it for the fill to fade out."""


def geodesic_badge(size: int) -> Image.Image:
    """The O: the 2V hemisphere from above, white lines on a green disc."""
    from two_v_demo.geometry import build_demo_geometry

    scale = 4
    big = size * scale
    badge = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.ellipse((0, 0, big - 1, big - 1), fill=GREEN + (255,))
    geo = build_demo_geometry()
    v = geo.vertices
    r = big * 0.44
    c = big / 2
    for a, b in geo.hemisphere_edges:
        pa = (c + v[a][0] * r, c - v[a][1] * r)
        pb = (c + v[b][0] * r, c - v[b][1] * r)
        draw.line((pa, pb), fill=(255, 255, 255, 255), width=int(big * 0.022))
    return badge.resize((size, size), Image.LANCZOS)


def _text_mask(size: tuple[int, int], text: str, font: ImageFont.FreeTypeFont,
               xy: tuple[float, float]) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255)
    return mask


def _shadowed(base: Image.Image, mask: Image.Image, fill: Image.Image,
              stroke: int, stroke_colour, shadow: int) -> Image.Image:
    """Letters with a light edge and a soft shadow, so they hold on sky or pine."""
    halo = mask.filter(ImageFilter.MaxFilter(stroke * 2 + 1)) if stroke else mask
    shade = halo.filter(ImageFilter.GaussianBlur(shadow))
    base = Image.composite(Image.new("RGB", base.size, (20, 16, 10)), base,
                           shade.point(lambda p: int(p * 0.55)))
    if stroke:
        base = Image.composite(Image.new("RGB", base.size, stroke_colour), base, halo)
    return Image.composite(fill, base, mask)


def wood_fill(size: tuple[int, int], seed: int = 3) -> Image.Image:
    """Streaky grain, dark to light, for WEDGE METHOD and the author's board."""
    w, h = size
    rng = np.random.default_rng(seed)
    y = np.arange(h)[:, None] / h
    x = np.arange(w)[None, :] / w
    grain = np.zeros((h, w))
    for k in range(12):
        grain += np.sin(y * rng.uniform(40, 140) + np.sin(x * rng.uniform(2, 9) + rng.uniform(0, 6)) * 2.5
                        + rng.uniform(0, 6)) * rng.uniform(0.3, 1.0)
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    t = (grain * 0.65 + (1 - y) * 0.35)[..., None]
    rgb = np.array(WOOD_DARK) * (1 - t) + np.array(WOOD_LIGHT) * t
    return Image.fromarray(rgb.astype(np.uint8))


def fit_font(path: str, text: str, width: int, start: int = 400) -> ImageFont.FreeTypeFont:
    size = start
    while size > 20:
        font = ImageFont.truetype(path, size)
        if font.getlength(text) <= width:
            return font
        size -= 4
    return ImageFont.truetype(path, size)


def title_block(img: Image.Image, left: int, right: int, top: int,
                subtitle: str = SUBTITLE_WORDS) -> tuple[Image.Image, int]:
    """THE 40 HOUR / CABIN / ``subtitle``, set between ``left`` and ``right``
    from ``top`` down. Returns the image and the block's bottom."""
    W = img.width
    k = W / REFERENCE_W
    width = right - left
    cx = (left + right) / 2

    # Line one, its last O a sphere.
    font = fit_font(FONT_HEAVY, TITLE_TOP, width)
    split = TITLE_TOP.rfind("O")
    before, after = TITLE_TOP[:split], TITLE_TOP[split + 1:]
    cap = font.getbbox("D")
    cap_h = cap[3] - cap[1]
    o_w = font.getlength("O")
    total = font.getlength(before) + o_w + font.getlength(after)
    x0 = cx - total / 2
    y0 = top + 20 * k - cap[1]
    mask = _text_mask(img.size, before, font, (x0, y0))
    mask2 = _text_mask(img.size, after, font, (x0 + font.getlength(before) + o_w, y0))
    mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(mask2)))
    img = _shadowed(img, mask, Image.new("RGB", img.size, GREEN), max(2, round(5 * k)), (238, 226, 196),
                    max(4, round(14 * k)))
    badge_size = int(cap_h * 1.04)
    badge = geodesic_badge(badge_size)
    bx = int(x0 + font.getlength(before) + (o_w - badge_size) / 2)
    by = int(top + 20 * k + (cap_h - badge_size) / 2)
    ring = Image.new("L", img.size, 0)
    r = max(2, round(5 * k))
    ImageDraw.Draw(ring).ellipse((bx - r, by - r, bx + badge_size + r, by + badge_size + r), fill=255)
    img = Image.composite(Image.new("RGB", img.size, (238, 226, 196)), img, ring)
    img.paste(badge, (bx, by), badge)
    line1_bottom = top + 20 * k + cap_h

    # Line two, in wood -- a short word, so held to a size beside line one.
    font2 = fit_font(FONT_HEAVY, TITLE_BOTTOM, int(width * 0.86))
    while font2.getbbox("W")[3] - font2.getbbox("W")[1] > cap_h * 1.35 and font2.size > 20:
        font2 = ImageFont.truetype(FONT_HEAVY, font2.size - 4)
    cap2 = font2.getbbox("W")
    y2 = line1_bottom + 40 * k - cap2[1]
    x2 = cx - font2.getlength(TITLE_BOTTOM) / 2
    mask = _text_mask(img.size, TITLE_BOTTOM, font2, (x2, y2))
    img = _shadowed(img, mask, wood_fill(img.size), max(2, round(4 * k)), (240, 228, 200), max(4, round(12 * k)))
    line2_bottom = line1_bottom + 40 * k + (cap2[3] - cap2[1])

    # The subtitle, between rules.
    font3 = ImageFont.truetype(FONT_BOLD, int(cap_h * 0.54))
    while font3.getlength(subtitle) > width * 0.80 and font3.size > 10:
        font3 = ImageFont.truetype(FONT_BOLD, font3.size - 2)   # a long subtitle, held inside the rules
    sub_w = font3.getlength(subtitle)
    cap3 = font3.getbbox("T")
    y3 = line2_bottom + 46 * k - cap3[1]
    mask = _text_mask(img.size, subtitle, font3, (cx - sub_w / 2, y3))
    img = _shadowed(img, mask, Image.new("RGB", img.size, INK), max(1, round(3 * k)), (246, 232, 204),
                    max(3, round(8 * k)))
    rule_y = line2_bottom + 46 * k + (cap3[3] - cap3[1]) / 2
    draw = ImageDraw.Draw(img)
    gap, length = 36 * k, min(260 * k, (width - sub_w) / 2 - 60 * k)
    for sign in (-1, 1):
        start = cx + sign * (sub_w / 2 + gap)
        draw.line((start, rule_y, start + sign * length, rule_y), fill=INK, width=max(2, round(6 * k)))
    return img, int(line2_bottom + 46 * k + (cap3[3] - cap3[1]))


def compose(scene: Image.Image, subtitle: str = SUBTITLE_WORDS) -> Image.Image:
    """The rendered front, lettered. ``subtitle`` defaults to this book's;
    the Master Edition (:mod:`master_book`) letters the same scene with its
    own."""
    img = scene.convert("RGB")
    W, H = img.size
    left, right = SAFE, W - BLEED - SAFE          # spine fold on the left
    top, bottom = BLEED + SAFE, H - BLEED - SAFE
    width = right - left
    cx = (left + right) / 2
    img, _end = title_block(img, left, right, top, subtitle=subtitle)
    font = fit_font(FONT_HEAVY, TITLE_TOP, width)
    cap_h = font.getbbox("D")[3] - font.getbbox("D")[1]

    # The author, on a board.
    font4 = ImageFont.truetype(FONT_BOLD, int(cap_h * 0.62))
    byline = f"by {outline.AUTHOR}"
    text_w = font4.getlength(byline)
    board_h = int(cap_h * 1.25)
    board_w = int(min(width, text_w + 360))
    bx0 = int(cx - board_w / 2)
    by0 = bottom - board_h
    board = wood_fill((board_w, board_h), seed=8).point(lambda p: int(p * 0.55))
    shadow = Image.new("L", img.size, 0)
    ImageDraw.Draw(shadow).rectangle((bx0 + 10, by0 + 16, bx0 + board_w + 10, by0 + board_h + 16), fill=200)
    img = Image.composite(Image.new("RGB", img.size, (10, 8, 6)), img, shadow.filter(ImageFilter.GaussianBlur(18)))
    img.paste(board, (bx0, by0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((bx0, by0, bx0 + board_w - 1, by0 + board_h - 1), outline=(40, 26, 14), width=6)
    for px_, py_ in ((bx0 + 40, by0 + 40), (bx0 + board_w - 40, by0 + 40),
                     (bx0 + 40, by0 + board_h - 40), (bx0 + board_w - 40, by0 + board_h - 40)):
        draw.ellipse((px_ - 12, py_ - 12, px_ + 12, py_ + 12), fill=(58, 58, 60), outline=(20, 20, 20), width=3)
    cap4 = font4.getbbox("D")
    ty = by0 + (board_h - (cap4[3] - cap4[1])) / 2 - cap4[1]
    draw.text((cx - text_w / 2 + 4, ty + 5), byline, font=font4, fill=(15, 10, 6))
    draw.text((cx - text_w / 2, ty), byline, font=font4, fill=CREAM)
    for sign in (-1, 1):
        start = cx + sign * (text_w / 2 + 40)
        draw.line((start, by0 + board_h / 2, start + sign * 120, by0 + board_h / 2), fill=CREAM, width=5)
    return img


def _diffuse(band: np.ndarray, top_row: np.ndarray, bottom_row: np.ndarray, steps: int) -> np.ndarray:
    """Relax ``band`` toward the smooth surface that meets its top and bottom
    rows: each pass, every pixel becomes the mean of its four neighbours."""
    for _ in range(steps):
        padded = np.concatenate([top_row[None], band, bottom_row[None]], axis=0)
        avg = (padded[:-2] + padded[2:] + np.roll(band, 1, axis=1) + np.roll(band, -1, axis=1)) / 4.0
        avg[:, 0] = (padded[:-2, 0] + padded[2:, 0] + band[:, 1] * 2) / 4.0
        avg[:, -1] = (padded[:-2, -1] + padded[2:, -1] + band[:, -2] * 2) / 4.0
        band = avg
    return band


def _fill_band(art: Image.Image, top: int, bottom: int) -> Image.Image:
    """The old lettering painted out: the band is filled with the smooth
    surface that meets the painting above and below it -- worked out at an
    eighth of the size so it can settle across the whole band, then refined
    at full size -- and given back a little grain so it does not read flat.
    The author's file is never written to."""
    px = np.asarray(art.convert("RGB")).astype(np.float32)
    above, below = px[top - 1], px[bottom + 1]
    h, w = bottom - top + 1, px.shape[1]
    f = 8
    small_h, small_w = max(2, h // f), max(2, w // f)
    sa = np.asarray(Image.fromarray(above[None].astype(np.uint8)).resize((small_w, 1), Image.BILINEAR))[0]
    sb = np.asarray(Image.fromarray(below[None].astype(np.uint8)).resize((small_w, 1), Image.BILINEAR))[0]
    t = np.linspace(0.0, 1.0, small_h)[:, None, None]
    small = sa[None].astype(np.float32) * (1 - t) + sb[None].astype(np.float32) * t
    small = _diffuse(small, sa.astype(np.float32), sb.astype(np.float32), 3000)
    band = np.asarray(Image.fromarray(np.clip(small, 0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC))
    band = _diffuse(band.astype(np.float32), above, below, 300)
    rng = np.random.default_rng(12)
    band += rng.normal(0.0, 2.0, band.shape).astype(np.float32)
    px[top:bottom + 1] = band
    filled = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
    mask = Image.new("L", art.size, 0)
    # The lower edge fades over a wider strip, so trees at the sides grow back
    # out of the fill instead of starting at a line.
    ImageDraw.Draw(mask).rectangle((0, top, art.width, bottom - 10), fill=255)
    return Image.composite(filled, art.convert("RGB"), mask.filter(ImageFilter.GaussianBlur(8)))


def reletter_painted(src: Path = PAINTED, out: Path = PAINTED_OUT) -> Path:
    """The author's painted cover, lettered as the Amazon paperback, as a new
    file; also the site's cover image for that book."""
    art = Image.open(src).convert("RGB")
    top, bottom = PAINTED_BAND
    img = _fill_band(art, top, bottom)
    margin = round(art.width * 0.05)
    from two_v_demo import book as amazon_book
    img, _end = title_block(img, margin, art.width - margin, top - round(art.width * 0.012),
                            subtitle=amazon_book.SUBTITLE.upper())
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    site = outline.ROOT / "web" / "client" / "public" / "covers" / "2-trees.jpg"
    if site.parent.is_dir():
        img.resize((720, round(720 * img.height / img.width)), Image.LANCZOS).save(site, quality=90)
    return out


def main() -> int:
    scene = Image.open(cover_scene.OUT_DIR / "scene.png")
    out = cover_scene.OUT_DIR / "cover-front.png"
    compose(scene).save(out)
    print(out)
    print(reletter_painted())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
