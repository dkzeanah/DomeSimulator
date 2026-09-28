"""The cover's lettering, set over the rendered scene.

The layout follows the painted cover the author chose: a heavy slab title in
forest green with a geodesic sphere for the O, WEDGE METHOD in wood, the
subtitle between rules, and the author on a board at the foot. The sphere is
drawn from the real 2V mesh seen from above -- the same drawing as the site's
logo -- so even the letter O is the book's own dome.

Everything is placed inside KDP's safe area: 0.3 in inside the trim, where
the trim is 0.125 in inside the top, bottom and outer edges of this front
panel. Its left edge is the spine fold, which has no bleed.

    py -3.12 -m wedge_book.cover_type      # scene.png -> cover-front.png
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

SUBTITLE_WORDS = outline.SUBTITLE.upper()     # THE 40 HOUR CABIN
TITLE_TOP, TITLE_BOTTOM = "GEODESIC DOME", "WEDGE METHOD"


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


def compose(scene: Image.Image) -> Image.Image:
    img = scene.convert("RGB")
    W, H = img.size
    left, right = SAFE, W - BLEED - SAFE          # spine fold on the left
    top, bottom = BLEED + SAFE, H - BLEED - SAFE
    width = right - left
    cx = (left + right) / 2

    # GEODESIC DOME, the O as a sphere.
    font = fit_font(FONT_HEAVY, TITLE_TOP, width)
    before, after = "GEODESIC D", "ME"
    cap = font.getbbox("D")
    cap_h = cap[3] - cap[1]
    o_w = font.getlength("O")
    total = font.getlength(before) + o_w + font.getlength(after)
    x0 = cx - total / 2
    y0 = top + 20 - cap[1]
    mask = _text_mask(img.size, before, font, (x0, y0))
    mask2 = _text_mask(img.size, after, font, (x0 + font.getlength(before) + o_w, y0))
    mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(mask2)))
    img = _shadowed(img, mask, Image.new("RGB", img.size, GREEN), 5, (238, 226, 196), 14)
    badge_size = int(cap_h * 1.04)
    badge = geodesic_badge(badge_size)
    bx = int(x0 + font.getlength(before) + (o_w - badge_size) / 2)
    by = int(top + 20 + (cap_h - badge_size) / 2)
    ring = Image.new("L", img.size, 0)
    ImageDraw.Draw(ring).ellipse((bx - 5, by - 5, bx + badge_size + 5, by + badge_size + 5), fill=255)
    img = Image.composite(Image.new("RGB", img.size, (238, 226, 196)), img, ring)
    img.paste(badge, (bx, by), badge)
    line1_bottom = top + 20 + cap_h

    # WEDGE METHOD, in wood.
    font2 = fit_font(FONT_HEAVY, TITLE_BOTTOM, int(width * 0.86))
    cap2 = font2.getbbox("W")
    y2 = line1_bottom + 40 - cap2[1]
    x2 = cx - font2.getlength(TITLE_BOTTOM) / 2
    mask = _text_mask(img.size, TITLE_BOTTOM, font2, (x2, y2))
    img = _shadowed(img, mask, wood_fill(img.size), 4, (240, 228, 200), 12)
    line2_bottom = line1_bottom + 40 + (cap2[3] - cap2[1])

    # THE 40 HOUR CABIN, between rules.
    font3 = ImageFont.truetype(FONT_BOLD, int(cap_h * 0.54))
    sub_w = font3.getlength(SUBTITLE_WORDS)
    cap3 = font3.getbbox("T")
    y3 = line2_bottom + 46 - cap3[1]
    mask = _text_mask(img.size, SUBTITLE_WORDS, font3, (cx - sub_w / 2, y3))
    img = _shadowed(img, mask, Image.new("RGB", img.size, INK), 3, (246, 232, 204), 8)
    rule_y = line2_bottom + 46 + (cap3[3] - cap3[1]) / 2
    draw = ImageDraw.Draw(img)
    gap, length = 36, min(260, (width - sub_w) / 2 - 60)
    for sign in (-1, 1):
        start = cx + sign * (sub_w / 2 + gap)
        draw.line((start, rule_y, start + sign * length, rule_y), fill=INK, width=6)

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


def main() -> int:
    scene = Image.open(cover_scene.OUT_DIR / "scene.png")
    out = cover_scene.OUT_DIR / "cover-front.png"
    compose(scene).save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
