"""The exhibits for *The Staple House*: the two bills, standing on the platform.

Every exhibit is sized by a figure from :mod:`two_v_demo.staple_facts`, never by
hand: a slab's height is its dollars, a row's length is its count. They stand on
the Cabin World's exhibit platform (:mod:`two_v_demo.cabin_stage`), the same one
*Beyond the Dome* uses, so the dome on its pad stays in the back of every shot.
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import staple_facts as sf
from .render_kit import TriangleBatch

PC = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
TALLEST = 1.5                      # metres: the tallest slab in any one exhibit
SPAN = 3.4                         # metres: how wide a row of slabs may stand

PAPER = (0.93, 0.91, 0.86, 1.0)    # a papercut: a fee or a margin line
PAPER_DARK = (0.80, 0.77, 0.71, 1.0)
WOOD = (0.86, 0.66, 0.42, 1.0)     # the staple's own lines
AMBER = (1.0, 0.70, 0.30, 1.0)
STEEL = (0.55, 0.57, 0.60, 1.0)
BLUE = (0.45, 0.62, 0.80, 1.0)
RED = (0.82, 0.36, 0.30, 1.0)


def slabs(values, colours, depth: float = 0.05, width: float | None = None, scale: float | None = None,
          y: float = 0.0, grow: float = 1.0) -> tuple[TriangleBatch, list[np.ndarray]]:
    """A row of upright slabs along x, one per value, heights proportional to the values.
    Returns the batch and the top-centre of each slab (for its label)."""
    values = list(values)
    n = len(values)
    scale = scale or TALLEST / max(values)
    gap = SPAN / n
    width = width or gap * 0.62
    b, tops = TriangleBatch(), []
    for k, (v, c) in enumerate(zip(values, colours)):
        h = max(0.02, v * scale * grow)
        x = PC[0] - SPAN / 2 + gap * (k + 0.5)
        centre = np.array([x, PC[1] + y, PC[2] + h / 2])
        b.box(centre, (width, depth, h), c)
        tops.append(centre + [0, 0, h / 2])
    return b, tops


def papercuts(grow: float = 1.0):
    """The survey house's fee lines and margin lines, one slab each, to one scale."""
    f = sf.facts()
    rows = f["fees"] + f["margins"]
    colours = [PAPER] * len(f["fees"]) + [PAPER_DARK] * len(f["margins"])
    return slabs([v for _, v in rows], colours, grow=grow), [n for n, _ in rows], scale_papercuts()


def scale_papercuts() -> float:
    f = sf.facts()
    return TALLEST / max(v for _, v in f["fees"] + f["margins"])


def invoice(grow: float = 1.0, same_scale: bool = True):
    """The stem cell's invoice, one slab per line -- to the papercuts' scale when asked, so
    the two bills can be compared by eye."""
    f = sf.facts()
    rows = f["invoice"]
    colours = [AMBER if "Margin" in name else WOOD for name, _ in rows]
    scale = scale_papercuts() if same_scale else None
    return slabs([v for _, v in rows], colours, scale=scale, grow=grow), [n for n, _ in rows]


def three_prices(grow: float = 1.0):
    """The same floor three ways: the dome, manufactured, site-built."""
    f = sf.facts()
    vals = [f["dome_price"], f["mhs_same"], f["site_same"]]
    b, tops = slabs(vals, [WOOD, BLUE, STEEL], depth=0.35, width=0.55, grow=grow)
    return b, tops, ["THE DOME", "MANUFACTURED", "SITE-BUILT"], vals


def hands(lit: int | None = None) -> tuple[TriangleBatch, list[np.ndarray]]:
    """The hands in one stud: a post per hand, in an arc from the log to the stud."""
    n = sf.facts()["hands"]
    lit = n if lit is None else lit
    b, points = TriangleBatch(), []
    r = 1.45
    for k in range(n):
        t = math.pi * (0.1 + 0.8 * k / (n - 1))
        p = PC + [r * math.cos(t), -0.2 + r * math.sin(t) * 0.55, 0]
        colour = PAPER_DARK if k < lit else (0.6, 0.6, 0.6, 0.35)
        b.box(p + [0, 0, 0.32], (0.09, 0.09, 0.64), colour)
        b.box(p + [0, 0, 0.70], (0.16, 0.16, 0.12), colour)          # a head
        points.append(p + [0, 0, 0.82])
    # the log at one end, the stud at the other
    left = PC + [r * math.cos(math.pi * 0.1) + 0.35, -0.2, 0.14]
    right = PC + [r * math.cos(math.pi * 0.9) - 0.35, -0.2, 0.0]
    _cylinder(b, left, 0.14, 0.6, WOOD)
    b.box(right + [0, 0, 0.45], (0.038, 0.089, 0.9), WOOD)
    return b, points


def _cylinder(b: TriangleBatch, centre, r: float, length: float, colour, sides: int = 14) -> None:
    """A log lying along y."""
    c = np.asarray(centre, float)
    ring = [(r * math.cos(math.tau * k / sides), r * math.sin(math.tau * k / sides)) for k in range(sides)]
    for k in range(sides):
        (x0, z0), (x1, z1) = ring[k], ring[(k + 1) % sides]
        a0, a1 = c + [x0, -length / 2, z0], c + [x1, -length / 2, z1]
        b0, b1 = c + [x0, length / 2, z0], c + [x1, length / 2, z1]
        b.quad(a0, a1, b1, b0, colour)
        b.triangle(c + [0, -length / 2, 0], a1, a0, (0.94, 0.80, 0.58, 1.0), np.array([0, -1.0, 0]))
        b.triangle(c + [0, length / 2, 0], b0, b1, (0.94, 0.80, 0.58, 1.0), np.array([0, 1.0, 0]))


def dome_icon(b: TriangleBatch, centre, r: float, colour, frac: float = 1.0) -> None:
    """A small faceted hemisphere -- a dome as a counter, cut down to ``frac`` of itself."""
    c = np.asarray(centre, float)
    bands, sides = 4, 10
    top = math.pi / 2 * 1.0
    for i in range(bands):
        a0, a1 = top * i / bands, top * (i + 1) / bands
        for k in range(sides):
            if (k + 0.5) / sides > frac:
                continue
            t0, t1 = math.tau * k / sides, math.tau * (k + 1) / sides
            p = [c + r * np.array([math.cos(a) * math.cos(t), math.cos(a) * math.sin(t), math.sin(a)])
                 for a, t in ((a0, t0), (a0, t1), (a1, t1), (a1, t0))]
            shade = 0.85 + 0.15 * ((i + k) % 2)
            b.quad(p[0], p[1], p[2], p[3], tuple(x * shade for x in colour[:3]) + (1.0,))


def domes(count: float, grow: float = 1.0) -> tuple[TriangleBatch, list[np.ndarray]]:
    """``count`` domes in rows -- the last one cut to its fraction (the interest, in domes)."""
    b, points = TriangleBatch(), []
    shown = count * grow
    whole = int(shown)
    per_row = 6
    for k in range(whole + 1):
        frac = 1.0 if k < whole else shown - whole
        if frac <= 0.02:
            break
        row, col = divmod(k, per_row)
        p = PC + [-1.5 + col * 0.6, -0.4 + row * 0.75, 0]
        dome_icon(b, p, 0.26, AMBER if frac == 1.0 else RED, frac)
        points.append(p + [0, 0, 0.38])
    return b, points


def validate_staple_scene() -> None:
    sf.validate()
    (b, tops), names, scale = papercuts()
    assert len(tops) == len(names) == sf.facts()["papercut_lines"]
    assert max(t[2] for t in tops) <= PC[2] + TALLEST + 1e-6
    (ib, itops), inames = invoice()
    assert len(itops) == sf.facts()["dome_lines"]
    # To the same scale, every line of the staple's bill is shorter than the tallest papercut.
    assert max(t[2] for t in itops) < max(t[2] for t in tops)
    hb, pts = hands()
    assert len(pts) == sf.facts()["hands"]
    db, dpts = domes(sf.facts()["interest_domes"])
    assert len(dpts) == math.ceil(sf.facts()["interest_domes"])
    for batch in (b, ib, hb, db, three_prices()[0]):
        v = np.asarray(batch.vertices, float)
        assert len(v) and np.all(np.isfinite(v))
