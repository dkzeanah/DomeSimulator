"""One picture per spread, rendered in the Cabin World.

Each spread is a camera aimed at the world's landmarks by name
(:func:`two_v_demo.cabin_world.landmarks`), the layers it hides, the story's
own geometry it adds -- the town of boxes, Pip, her friend, a lumber yard --
and, where the verse names a number, an overlay that reads that number from
:func:`seed_model.dome_class`. Then every picture gets the same storybook
finish (:func:`storybook`), so the pages belong to one book.

The world is the cover's, rendered from a heavier log than the reference build
for legibility (``cover_scene.COVER_TRUNK_IN``). Every figure the book prints is
the reference build's, from ``seed_model``; the end page says so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import seed_model
from two_v_demo import cabin_world as cw
from two_v_demo import figure
from two_v_demo.render_kit import TriangleBatch, look_at, perspective

FONT_TITLE = cw.FONT_HEAVY                      # Rockwell Extra Bold, the cover's
FONT_HAND = "C:/Windows/Fonts/BOOKOSB.TTF"      # Bookman bold, for lettering in pictures

# The story's people. Pip wears a green hat, so she can tip it.
PIP = dict(skin=(0.86, 0.64, 0.48, 1.0), hi_vis=(0.96, 0.74, 0.22, 1.0),
           trousers=(0.70, 0.22, 0.17, 1.0), helmet=(0.20, 0.46, 0.30, 1.0))
BOY = dict(skin=(0.62, 0.43, 0.30, 1.0), hi_vis=(0.26, 0.47, 0.78, 1.0),
           trousers=(0.30, 0.30, 0.36, 1.0), helmet=(0.45, 0.30, 0.18, 1.0))
NEIGHBOURS = (
    dict(skin=(0.90, 0.70, 0.56, 1.0), hi_vis=(0.62, 0.30, 0.55, 1.0), trousers=(0.22, 0.24, 0.30, 1.0), helmet=(0.55, 0.52, 0.48, 1.0)),
    dict(skin=(0.50, 0.34, 0.24, 1.0), hi_vis=(0.85, 0.42, 0.20, 1.0), trousers=(0.18, 0.32, 0.36, 1.0), helmet=(0.15, 0.12, 0.10, 1.0)),
    dict(skin=(0.78, 0.58, 0.42, 1.0), hi_vis=(0.40, 0.62, 0.36, 1.0), trousers=(0.40, 0.28, 0.20, 1.0), helmet=(0.80, 0.70, 0.30, 1.0)),
    dict(skin=(0.68, 0.50, 0.36, 1.0), hi_vis=(0.85, 0.85, 0.80, 1.0), trousers=(0.20, 0.20, 0.45, 1.0), helmet=(0.60, 0.15, 0.15, 1.0)),
)
CHILD_M, ADULT_M = 1.15, 1.72


@lru_cache(maxsize=1)
def sheet() -> dict:
    """The book's dome, as figures: the reference build's longest strut."""
    return seed_model.dome_class(seed_model.SEED_LONG_EDGE_IN)


# ----------------------------------------------------------------------
# The story's geometry
# ----------------------------------------------------------------------

def person(at, facing_deg: float, look: dict, stature: float = CHILD_M, pose: str = "stand") -> TriangleBatch:
    """A figure standing at ``at`` (x, y on the ground or a z given), facing a compass angle."""
    batch = TriangleBatch()
    x, y = at[0], at[1]
    z = at[2] if len(at) > 2 else 0.0
    joints = figure.joint_positions(figure.POSES[pose], stature)
    placed = figure.place_figure(joints, (x, y, z), facing_deg)
    figure.draw_figure(batch, placed, **look)
    return batch


def facing(at, toward) -> float:
    return math.degrees(math.atan2(toward[1] - at[1], toward[0] - at[0]))


def town(seed: int = 3, keep_clear: tuple = (0.0, -9.0, 3.2), radius: float = 8.3, avoid: tuple = ()) -> TriangleBatch:
    """A town of boxes, stacked tall: grey and beige blocks with little windows."""
    rng = np.random.default_rng(seed)
    batch = TriangleBatch()
    greys = [(0.62, 0.62, 0.64), (0.70, 0.67, 0.60), (0.55, 0.57, 0.60), (0.74, 0.72, 0.68), (0.60, 0.56, 0.52)]
    cx, cy, clear_r = keep_clear
    for k in range(46):
        a = rng.uniform(0, math.tau)
        r = math.sqrt(rng.uniform(0.04, 1.0)) * radius
        x, y = r * math.cos(a), r * math.sin(a)
        if math.hypot(x - cx, y - cy) < clear_r + 4.5 or math.hypot(x, y) < 1.0:
            continue
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid):
            continue
        w, d = rng.uniform(1.4, 2.4), rng.uniform(1.4, 2.4)
        floors = int(rng.integers(1, 4))
        z = 0.0
        for f in range(floors):
            h = rng.uniform(1.3, 2.0)
            g = greys[int(rng.integers(len(greys)))]
            shade = rng.uniform(0.92, 1.06)
            batch.box((x, y, z + h / 2), (w * (1 - 0.08 * f), d * (1 - 0.08 * f), h),
                      (g[0] * shade, g[1] * shade, g[2] * shade, 1.0))
            # two windows on the side the camera sees
            for wx in (-0.25, 0.25):
                batch.box((x + wx * w, y - d * (1 - 0.08 * f) / 2 - 0.01, z + h * 0.55), (0.32, 0.03, 0.42),
                          (0.30, 0.34, 0.42, 1.0))
            z += h
    return batch


def lumber_yard() -> TriangleBatch:
    """Boards wrapped in plastic, with tags on their sleeves."""
    batch = TriangleBatch()
    rng = np.random.default_rng(7)
    for row in range(3):
        for col in range(2):
            x0, y0 = 1.3 + col * 1.7, -2.6 + row * 1.25
            for layer_ in range(6):
                z = 0.05 + layer_ * 0.16
                batch.box((x0, y0, z + 0.07), (1.4, 0.95, 0.14), (0.86, 0.72, 0.50, 1.0))
            batch.box((x0, y0, 0.55), (1.44, 0.99, 1.0), (0.82, 0.88, 0.92, 0.55))   # the wrap
            batch.box((x0 - 0.5, y0 - 0.5, 0.75), (0.16, 0.02, 0.22), (0.85, 0.20, 0.18, 1.0))   # the tag
            _ = rng
    return batch


def tools(stump_top) -> TriangleBatch:
    """One level, one tape, one chalk line, one lunch box, by the stump."""
    batch = TriangleBatch()
    x, y, z = stump_top
    batch.box((x + 0.55, y - 0.25, 0.04), (0.60, 0.06, 0.07), (0.95, 0.80, 0.15, 1.0))      # level
    batch.cylinder((x + 0.55, y + 0.20, 0.0), (x + 0.55, y + 0.20, 0.06), 0.06, (0.95, 0.76, 0.10, 1.0), 14)  # tape
    batch.box((x + 0.20, y + 0.55, 0.06), (0.14, 0.09, 0.12), (0.20, 0.42, 0.75, 1.0))     # chalk line
    batch.box((x - 0.10, y - 0.55, 0.11), (0.34, 0.20, 0.22), (0.80, 0.18, 0.16, 1.0))     # lunch box
    batch.box((x - 0.10, y - 0.55, 0.235), (0.16, 0.03, 0.03), (0.25, 0.25, 0.25, 1.0))    # its handle
    return batch


def chalkboard(at) -> TriangleBatch:
    """A chalkboard on a post, its face to the south (the camera's side)."""
    batch = TriangleBatch()
    batch.box((at[0], at[1], 1.05), (1.5, 0.06, 1.0), (0.12, 0.22, 0.17, 1.0))
    batch.box((at[0], at[1], 0.28), (0.08, 0.08, 0.56), (0.36, 0.24, 0.14, 1.0))
    return batch


def loose_panel(at) -> TriangleBatch:
    """A triangle panel lying in the grass, fallen from its frame."""
    batch = TriangleBatch()
    s = cw.landmarks().short_member
    p = np.array([at[0], at[1], 0.0])
    a, b, c = p + [-s / 2, 0, 0.03], p + [s / 2, -0.1, 0.06], p + [0.05, s * 0.8, 0.04]
    batch.triangle(a, b, c, (0.86, 0.66, 0.40, 1.0), np.array([0, 0, 1.0]))
    batch.triangle(a, c, b, (0.70, 0.52, 0.32, 1.0), np.array([0, 0, -1.0]))
    return batch


def moved(batch: TriangleBatch, offset) -> TriangleBatch:
    """A copy of a batch, slid across the hill (positions only; normals keep)."""
    v = np.asarray(batch.vertices, dtype=np.float64).reshape(-1, 10).copy()
    v[:, 0:3] += np.asarray(offset, float)
    out = TriangleBatch()
    out.vertices = v.ravel().tolist()
    return out


@lru_cache(maxsize=1)
def whole_dome() -> TriangleBatch:
    """The solver's dome with every triangle up."""
    cs = cw._scene()
    return cs.dome_batch(cs.sizes(), ())[0]


# ----------------------------------------------------------------------
# Overlays: lettering in the picture, from computed numbers
# ----------------------------------------------------------------------

@dataclass
class Shot:
    eye: tuple
    target: tuple
    fov: float
    extra: list = field(default_factory=list)
    hide: tuple = ()
    overlay: Callable | None = None     # (PIL image, project(point) -> (x, y)) -> None
    night: bool = False


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _label(draw: ImageDraw.ImageDraw, xy, text: str, size: int, fill=(255, 246, 228), anchor="mm", shadow=True):
    f = _font(FONT_HAND, size)
    if shadow:
        draw.text((xy[0] + size * 0.05, xy[1] + size * 0.05), text, font=f, fill=(30, 18, 8), anchor=anchor)
    draw.text(xy, text, font=f, fill=fill, anchor=anchor)


def _arrow(draw, a, b, width: int, fill=(255, 246, 228)):
    draw.line([a, b], fill=fill, width=width)
    for end, other in ((a, b), (b, a)):
        d = np.array(other, float) - np.array(end, float)
        d /= max(np.linalg.norm(d), 1e-6)
        n = np.array([-d[1], d[0]])
        tip = np.array(end, float)
        L = width * 4.5
        draw.polygon([tuple(tip), tuple(tip + d * L + n * L * 0.5), tuple(tip + d * L - n * L * 0.5)], fill=fill)


def zzzip(img: Image.Image, project, at) -> None:
    draw = ImageDraw.Draw(img)
    x, y = project(at)
    s = int(img.width * 0.07)
    for i, (dx, dy) in enumerate(((-0.9, -0.55), (0.75, -0.75))):
        _label(draw, (x + dx * img.width * 0.22, y + dy * img.height * 0.3), "Zzzip!", s - i * 10, fill=(255, 228, 120))


def chalk_number(img: Image.Image, project, at) -> None:
    draw = ImageDraw.Draw(img)
    x, y = project(at)
    s = int(img.width * 0.034)
    _label(draw, (x, y - s * 0.7), "longest strut", s, fill=(236, 236, 226), shadow=False)
    _label(draw, (x, y + s * 0.75), f"{sheet()['longIn']} in", int(s * 1.7), fill=(255, 255, 248), shadow=False)


def dimensions(img: Image.Image, project, _at=None) -> None:
    """Across, tall, triangles and weight, read off the reference build."""
    m, d = cw.landmarks(), sheet()
    draw = ImageDraw.Draw(img)
    w = max(3, img.width // 260)
    r, c = m.dome_r, m.dome_centre
    left, right = project(c + [-r, -r * 0.05, 0.05]), project(c + [r, -r * 0.05, 0.05])
    y = max(left[1], right[1]) + img.height * 0.05
    _arrow(draw, (left[0], y), (right[0], y), w)
    s = int(img.width * 0.034)
    _label(draw, ((left[0] + right[0]) / 2, y + s * 0.9), f"{d['diameterFt']:g} feet across", s)
    top, base = project(m.apex), project(c)
    x = left[0] - img.width * 0.04
    _arrow(draw, (x, top[1]), (x, base[1]), w)
    _label(draw, (x - s * 0.4, (top[1] + base[1]) / 2), f"{d['heightFt']:g} feet tall", s, anchor="rm")
    panels = sum(p["count"] for p in d["panels"])
    _label(draw, (img.width * 0.5, img.height * 0.09), f"{panels} triangles", int(s * 1.15))
    _label(draw, (img.width * 0.5, img.height * 0.09 + s * 1.5), f"{d['frameLb']:,} pounds of wood", s)


def ledger(img: Image.Image) -> None:
    """Pip's book, open: the dome written down, every line from the model."""
    from wedge_book import tokens

    d = sheet()
    lines = [
        ("longest strut", f"{d['longIn']} in"),
        ("shortest strut", f"{d['shortIn']:g} in"),
        ("wedges in the frame", f"{d['memberCount']}"),
        ("triangles", f"{sum(p['count'] for p in d['panels'])}"),
        ("wood", f"{d['woodCuft']:g} cu ft"),
        ("frame weight", f"{d['frameLb']:,} lb"),
        ("frame cost", f"${d['cost']['frame']:,.0f}"),
        ("hours of frame work", tokens.resolve("{{hr.total}}")),
    ]
    w, h = img.size
    x0, y0, x1, y1 = int(w * 0.07), int(h * 0.20), int(w * 0.62), int(h * 0.93)
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rounded_rectangle((x0 + 14, y0 + 18, x1 + 14, y1 + 18), radius=18, fill=(20, 10, 4, 110))
    sd.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(250, 243, 226, 255), outline=(120, 82, 46, 255), width=4)
    img.paste(Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB"))
    draw = ImageDraw.Draw(img)
    s = int(h * 0.045)
    title = _font(FONT_HAND, int(s * 1.25))
    draw.text((x0 + s, y0 + s * 0.7), "My dome, written down", font=title, fill=(110, 52, 20))
    f = _font(FONT_HAND, s)
    y = y0 + s * 2.6
    step = (y1 - y - s) / len(lines)
    for k, v in lines:
        draw.line((x0 + s, y + s * 1.25, x1 - s, y + s * 1.25), fill=(196, 176, 150), width=2)
        draw.text((x0 + s, y), k, font=f, fill=(40, 30, 22))
        draw.text((x1 - s, y), v, font=f, fill=(20, 40, 110), anchor="ra")
        y += step


def stars(img: Image.Image, seed: int = 4) -> None:
    rng = np.random.default_rng(seed)
    draw = ImageDraw.Draw(img)
    for _ in range(160):
        x, y = rng.uniform(0, img.width), rng.uniform(0, img.height * 0.45)
        r = rng.uniform(0.6, 2.4) * img.width / 1600
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 250, 225))
    mx, my, mr = img.width * 0.80, img.height * 0.15, img.width * 0.045
    draw.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=(250, 244, 210))


# ----------------------------------------------------------------------
# The sixteen spreads, and the cover
# ----------------------------------------------------------------------

def shots() -> dict[str, Shot]:
    m = cw.landmarks()
    centre, r = m.dome_centre, m.dome_r
    log = m.log_end
    stump = m.stump_top
    stack = m.stack
    hero = np.array(cw.HERO_EYE)
    no_build = ("dome", "deck", "builder", "props")
    pip_front = (0.9, -5.6)
    out: dict[str, Shot] = {}

    out["cover"] = Shot((1.4, -11.6, 1.7), (0.15, 0.0, 2.15), 50,
                        [whole_dome(), person(pip_front, facing(pip_front, (1.4, -11.6)), PIP)],
                        hide=("dome", "builder"))
    # 1. In a town full of boxes ...
    p1 = (0.5, -9.6)
    out["1"] = Shot((0.6, -13.4, 1.25), (0.2, 0.0, 2.0), 50,
                    [town(), person(p1, facing(p1, (0.6, -13.4)), PIP, pose="reach_out")], hide=no_build)
    # 2. "A dome!" Pip decided ...
    p2 = (2.35, -9.7)
    out["2"] = Shot((3.3, -12.6, 1.05), (-0.6, 0.0, 2.0), 50,
                    [whole_dome(), person(p2, facing(p2, centre), PIP, pose="reach_out")], hide=("dome", "builder", "props"))
    # 3. ... past the lumber yard
    p3 = (-0.6, -4.8)
    out["3"] = Shot((-1.0, -10.5, 1.9), (1.2, -2.0, 0.9), 46,
                    [town(seed=8, keep_clear=(1.0, -2.0, 3.0), radius=8.6), lumber_yard(),
                     person(p3, 180.0, PIP, pose="stride")], hide=no_build)
    # 4. At the edge of the forest a fallen pine lay ...
    p4 = tuple(log[:2] + np.array([1.05, -0.35]))
    out["4"] = Shot(tuple(log + [2.9, -3.4, 1.05]), tuple(log + [-0.2, 1.4, 0.2]), 46,
                    [person(p4, facing(p4, log), PIP, pose="reach_out")], hide=("dome", "deck", "builder"))
    # 5. She fetched one good saw and one bright chalky line ...
    p5 = tuple(stump[:2] + np.array([0.95, 0.35]))
    out["5"] = Shot(tuple(stump + [1.7, -2.1, 0.95]), tuple(stump + [0.15, 0.1, -0.15]), 44,
                    [tools(stump), person(p5, facing(p5, (stump[0] + 1.7, stump[1] - 2.1)), PIP)],
                    hide=("dome", "deck", "builder"))
    # 6. Zzzip! went the saw ...
    end_eye = log - m.log_axis * 1.9 + np.array([0.55, 0.0, 0.55])
    out["6"] = Shot(tuple(end_eye), tuple(log + [0, 0, -0.05]), 38, hide=("dome", "deck", "builder"),
                    overlay=lambda img, pr: zzzip(img, pr, log))
    # 7. "A wedge," Pip declared ...
    p7 = tuple(stack[:2] + np.array([-0.55, -0.55]))
    out["7"] = Shot(tuple(stack + [1.8, -2.3, 1.25]), tuple(stack + [-0.1, 0.5, 0.3]), 44,
                    [person(p7, facing(p7, (stack[0] + 1.8, stack[1] - 2.3)), PIP, pose="reach_out")],
                    hide=("dome", "builder"))
    # 8. She measured one strut ... and she wrote it in chalk
    board = (stack[0] - 1.2, stack[1] + 0.9)
    p8 = (board[0] + 1.25, board[1] - 0.8)
    out["8"] = Shot((board[0] + 0.8, board[1] - 4.2, 1.35), (board[0] + 0.1, board[1], 0.95), 44,
                    [chalkboard(board), person(p8, facing(p8, (board[0] + 0.8, board[1] - 4.2)), PIP)],
                    hide=("dome", "builder"),
                    overlay=lambda img, pr: chalk_number(img, pr, np.array([board[0], board[1] - 0.05, 1.08])))
    # 9. How tall? And how wide? And how much will it weigh?
    p9 = (r * 1.25, -r * 1.2)
    out["9"] = Shot((0.0, -12.8, 2.4), (0.0, 0.0, 2.1), 44,
                    [whole_dome(), person(p9, facing(p9, (0, -12.8)), PIP)], hide=("dome", "builder", "props"),
                    overlay=lambda img, pr: dimensions(img, pr))
    # 10. Then wedge after wedge went in pinwheels of three ...
    az, el = math.radians(-100), math.radians(22)
    node = centre + r * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    out["10"] = Shot(tuple(node + (node - centre) / r * 3.1 + [0.45, 0, 0.1]), tuple(node), 38,
                     [whole_dome()], hide=("dome", "builder", "props"))
    # 11. Triangle! Triangle! Up the ring rose ...
    p11 = (0.75, -4.7)
    out["11"] = Shot(tuple(hero), (0.1, 0.0, 2.2), 46,
                     [person(p11, facing(p11, m.gap[:2]), PIP, pose="reach_high")], hide=("builder",))
    # 12. The neighbours came running ...
    folk = [((-2.6, -5.4), NEIGHBOURS[0], ADULT_M, "stride"), ((-1.4, -6.6), NEIGHBOURS[1], CHILD_M, "stride"),
            ((2.7, -5.0), NEIGHBOURS[2], ADULT_M, "reach_out"), ((3.6, -6.2), NEIGHBOURS[3], CHILD_M, "stride")]
    crowd = [person(at, facing(at, centre), look, h, pose) for at, look, h, pose in folk]
    p12 = (0.5, -4.4)
    out["12"] = Shot((0.6, -12.6, 1.6), (0.2, 0.0, 2.0), 50,
                     [whole_dome(), person(p12, facing(p12, (0.6, -12.6)), PIP), *crowd], hide=("dome", "builder", "props"))
    # 13. I can tell you the wood and the screws that it took ...
    out["13"] = Shot((2.6, -9.5, 1.3), (0.0, 0.0, 2.0), 48, [whole_dome()], hide=("dome", "builder", "props"),
                     overlay=lambda img, pr: ledger(img))
    # 14. Then a boy from the boxes came up with a frown ...
    pb, pp = (-1.6, -5.2), (0.9, -5.4)
    out["14"] = Shot((0.0, -11.8, 2.1), (0.0, 0.0, 1.9), 48,
                     [loose_panel((-0.6, -6.6)), person(pb, facing(pb, pp), BOY), person(pp, facing(pp, pb), PIP, pose="reach_out")],
                     hide=("builder", "props"))
    # 15. So the kids with same domes started up a big club ...
    west, east = (-6.6, 3.2, 0.0), (6.4, 2.6, 0.0)
    kids = [person((-1.2, -6.0), 20.0, PIP, pose="carry"), person((-0.4, -6.0), 160.0, BOY, pose="carry"),
            person((2.2, -6.6), 120.0, NEIGHBOURS[1], CHILD_M, "stride"), person((-2.8, -6.4), 60.0, NEIGHBOURS[3], CHILD_M, "stride")]
    deck = cw.layer("deck")
    out["15"] = Shot((0.0, -14.2, 2.5), (0.0, 1.5, 1.4), 54,
                     [whole_dome(), moved(whole_dome(), west), moved(deck, west), moved(whole_dome(), east), moved(deck, east),
                      loose_panel((-0.8, -6.9)), *kids], hide=("dome", "builder", "props"))
    # 16. Now the town full of boxes has domes on the hill ...
    out["16"] = Shot((0.0, -17.5, 4.2), (0.0, 1.5, 1.6), 54,
                     [whole_dome(), moved(whole_dome(), west), moved(deck, west), moved(whole_dome(), east), moved(deck, east),
                      town(seed=11, keep_clear=(0.0, -15.0, 1.0), radius=8.9,
                           avoid=((0.0, 0.0, 4.2), (west[0], west[1], 4.0), (east[0], east[1], 4.0),
                                  (0.0, -6.0, 6.0), (-6.0, -4.0, 4.5), (6.0, -4.0, 4.5)))],
                     hide=("dome", "builder", "props"), night=True,
                     overlay=lambda img, pr: stars(img))
    return out


# ----------------------------------------------------------------------
# Rendering and the storybook finish
# ----------------------------------------------------------------------

def storybook(img: np.ndarray) -> np.ndarray:
    """One finish for every page: soft painted shapes, a warm ink line where
    shapes meet, a touch more colour, and paper grain."""
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    w = pil.width
    soft = pil.filter(ImageFilter.ModeFilter(size=max(3, w // 420) | 1)).filter(ImageFilter.SMOOTH_MORE)
    base = np.asarray(soft, dtype=np.float32) / 255.0
    # ink: edges of the luminance, thickened a little
    lum = Image.fromarray((base.mean(axis=2) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w / 1400))
    edges = np.asarray(lum.filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255.0
    edges = np.clip((edges - 0.035) * 6.0, 0, 1)
    edges = np.asarray(Image.fromarray((edges * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), dtype=np.float32)[..., None] / 255.0
    ink = np.array([0.24, 0.15, 0.09])
    out = base * (1 - 0.55 * edges) + ink * 0.55 * edges
    # colour: a little richer
    grey = out.mean(axis=2, keepdims=True)
    out = grey + (out - grey) * 1.18
    # paper
    rng = np.random.default_rng(1)
    grain = rng.normal(0, 1, (out.shape[0] // 2 + 1, out.shape[1] // 2 + 1)).astype(np.float32)
    grain = np.asarray(Image.fromarray(((grain * 18) + 128).clip(0, 255).astype(np.uint8)).resize((out.shape[1], out.shape[0])), np.float32)[..., None] / 255.0
    out = out * (0.97 + 0.06 * grain) * np.array([1.0, 0.985, 0.95])
    return np.clip(out, 0, 1)


def night(img: np.ndarray) -> np.ndarray:
    """The same hill after sunset: blue, dim, the domes still warm."""
    lum = img.mean(axis=2, keepdims=True)
    blue = lum * np.array([0.22, 0.27, 0.52]) + img * np.array([0.30, 0.24, 0.20])
    return np.clip(blue + np.array([0.02, 0.03, 0.08]), 0, 1)


class Painter:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.studio = cw.Studio(width, height, samples=8)

    def project(self, shot: Shot):
        w, h = self.width, self.height
        mvp = perspective(shot.fov, w / h, 0.05, 400.0) @ look_at(np.array(shot.eye, float), np.array(shot.target, float))

        def pr(p):
            c = np.asarray(mvp, float) @ np.array([*np.asarray(p, float)[:3], 1.0])
            return ((c[0] / c[3] * 0.5 + 0.5) * w, (1 - (c[1] / c[3] * 0.5 + 0.5)) * h)
        return pr

    def picture(self, shot: Shot) -> Image.Image:
        img = self.studio.frame(shot.eye, shot.target, shot.fov, extra=shot.extra, hide=shot.hide)
        if shot.night:
            img = night(img)
        pil = Image.fromarray((storybook(img) * 255).astype(np.uint8))
        if shot.overlay:
            shot.overlay(pil, self.project(shot))
        return pil

    def release(self):
        self.studio.release()
