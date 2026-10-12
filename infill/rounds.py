"""Filling with rounds: full-trunk slices, laid flat, in layers.

A round is a slice across the whole trunk, end grain up, ``t`` thick. The
frame's thickness takes as many layers as fit (a thinner last layer for the
remainder). Each layer is laid in a pattern:

``hex``     honeycomb: every round touching six others -- the tightest one size gives
``square``  a square grid: simpler to lay out, more gap
``graded``  a square grid of big rounds, then smaller rounds from higher up the trunk
            dropped into every gap big enough, largest first, down to the smallest you'll cut

and the layers are stacked:

``aligned`` every layer the same
``offset``  every other layer shifted onto the gaps of the one below, so no gap
            runs straight through
``rotated`` each layer's rows turned to run along a different edge

What a pattern leaves -- the curved triangles between rounds and the slivers
against the walls -- is **cut to fit** the way you'd do it by hand: lay a
copy of the same pattern over the layer, shifted so its rounds sit over the
gaps, and cut each copied round down to the gap it covers. A second copy,
shifted the other way, catches what the first missed. Rounds that cross the
45° wall are cut along it, bevelled to lie on the slope. All of it is
counted on a quarter-inch grid, so the areas are measured, not assumed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage

from . import geom2d as g2
from .constants import C

RES = 0.25          # inches per grid cell
GAP = 0.0           # rounds laid touching
MIN_PIECE = 0.75    # in^2: smaller than this is not worth cutting; it stays a void
WALL_KEEP = 0.4     # a round crossing the wall is kept (and cut) if this much of it is inside


@dataclass
class Round:
    c: np.ndarray
    r: float
    kind: str                     # full | wall | graded | copy
    area: float                   # the area of wood actually used
    poly: np.ndarray              # what is seen in plan (cut to the wall where it crosses)
    frags: int = 1                # a copied round may be cut into several gap pieces
    shapes: list = field(default_factory=list)   # the gap pieces' outlines, traced


@dataclass
class Layer:
    index: int
    z0: float
    z1: float
    angle: float
    rounds: list[Round] = field(default_factory=list)
    copies: list[Round] = field(default_factory=list)
    open_in2: float = 0.0         # the layer's opening, mid-height
    gaps_in2: float = 0.0         # left by the pattern
    void_in2: float = 0.0         # left after cutting to fit


def circle(c, r, n: int = 48) -> np.ndarray:
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.c_[c[0] + r * np.cos(a), c[1] + r * np.sin(a)]


def sizes(top: float, smallest: float) -> list[float]:
    """Round diameters to hand: the main log, then every inch smaller down
    to the smallest worth cutting -- what a tapering trunk gives."""
    out, d = [], top
    while d >= smallest - 1e-9:
        out.append(round(d, 3))
        d -= 1.0
    return out


def lattice(kind: str, pitch: float, angle: float, origin, bbox) -> np.ndarray:
    a = math.radians(angle)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    if kind == "square":
        b1, b2 = np.array([pitch, 0.0]), np.array([0.0, pitch])
    else:
        b1, b2 = np.array([pitch, 0.0]), np.array([pitch / 2, pitch * math.sqrt(3) / 2])
    b1, b2 = R @ b1, R @ b2
    x0, y0, x1, y1 = bbox
    span = max(x1 - x0, y1 - y0) * 2
    n = int(span / pitch) + 3
    i, j = np.meshgrid(np.arange(-n, n + 1), np.arange(-n, n + 1))
    pts = np.asarray(origin, float) + i.reshape(-1, 1) * b1 + j.reshape(-1, 1) * b2
    keep = (pts[:, 0] > x0 - pitch) & (pts[:, 0] < x1 + pitch) & (pts[:, 1] > y0 - pitch) & (pts[:, 1] < y1 + pitch)
    return pts[keep]


def hole_shift(kind: str, pitch: float, angle: float, which: int = 0) -> np.ndarray:
    """From a round's centre to the middle of a gap in its pattern."""
    a = math.radians(angle)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    if kind == "square":
        v = np.array([pitch / 2, pitch / 2]) if which == 0 else np.array([pitch / 2, 0.0])
    else:
        v = np.array([pitch / 2, pitch * math.sqrt(3) / 6]) if which == 0 else \
            np.array([pitch / 2, -pitch * math.sqrt(3) / 6])
    return R @ v


class Grid:
    """The layer's opening on a quarter-inch grid."""

    def __init__(self, clip):
        lo, hi = clip.min(axis=0) - RES, clip.max(axis=0) + RES
        self.xs = np.arange(lo[0], hi[0], RES)
        self.ys = np.arange(lo[1], hi[1], RES)
        X, Y = np.meshgrid(self.xs, self.ys)
        self.X, self.Y = X, Y
        self.inside = self.within(clip)
        self.cell = RES * RES

    def within(self, poly) -> np.ndarray:
        p = g2.ccw(poly)
        mask = np.ones_like(self.X, dtype=bool)
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            e = b - a
            mask &= (e[0] * (self.Y - a[1]) - e[1] * (self.X - a[0])) >= 0
        return mask

    def window(self, c, r):
        """Row and column slices of the cells within ``r`` of ``c``."""
        i0 = max(0, int((c[1] - r - self.ys[0]) / RES) - 1)
        i1 = min(len(self.ys), int((c[1] + r - self.ys[0]) / RES) + 2)
        j0 = max(0, int((c[0] - r - self.xs[0]) / RES) - 1)
        j1 = min(len(self.xs), int((c[0] + r - self.xs[0]) / RES) + 2)
        return slice(i0, i1), slice(j0, j1)

    def disc(self, c, r) -> np.ndarray:
        """A disc as a full-grid mask (built on its own window)."""
        m = np.zeros_like(self.inside)
        sl = self.window(c, r)
        m[sl] = (self.X[sl] - c[0]) ** 2 + (self.Y[sl] - c[1]) ** 2 <= r * r
        return m

    def stamp(self, mask, c, r, poly=None, value=True) -> None:
        """Mark a disc (or a cut polygon) on ``mask`` in place."""
        sl = self.window(c, r)
        if poly is None:
            mask[sl] |= (self.X[sl] - c[0]) ** 2 + (self.Y[sl] - c[1]) ** 2 <= r * r
            return
        p = g2.ccw(poly)
        sub_ = np.ones_like(self.X[sl], dtype=bool)
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            e = b - a
            sub_ &= (e[0] * (self.Y[sl] - a[1]) - e[1] * (self.X[sl] - a[0])) >= 0
        mask[sl] |= sub_


def _edge_dist(poly, c) -> float:
    """How far a point is inside a convex polygon (negative outside)."""
    p = g2.ccw(poly)
    best = 1e9
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        e = g2.unit(b - a)
        n = np.array([-e[1], e[0]])
        best = min(best, float(np.dot(c - a, n)))
    return best


def _lay(kind: str, D: float, angle: float, origin, clip_lo, clip_hi, grid: Grid) -> list[Round]:
    """One pattern of rounds of diameter ``D``: whole ones inside the
    layer's smallest opening, cut ones across the wall."""
    r = D / 2
    pitch = D + GAP
    bbox = (*clip_hi.min(axis=0), *clip_hi.max(axis=0))
    out = []
    for c in lattice(kind, pitch, angle, origin, bbox):
        d = _edge_dist(clip_lo, c)
        if d >= r - 1e-6:
            out.append(Round(c, r, "full", math.pi * r * r, circle(c, r)))
            continue
        piece = g2.clip_convex(circle(c, r), clip_hi)
        if len(piece) >= 3 and g2.area(piece) >= WALL_KEEP * math.pi * r * r:
            out.append(Round(c, r, "wall", g2.area(piece), piece))
    return out


def _covered(grid: Grid, rounds: list[Round]) -> np.ndarray:
    m = np.zeros_like(grid.inside)
    for rd in rounds:
        grid.stamp(m, rd.c, rd.r, rd.poly if rd.kind == "wall" else None)
    return m & grid.inside


def _best_origin(kind, D, angle, clip_lo, clip_hi, grid, anchor) -> np.ndarray:
    """The pattern slid around inside one cell until it covers the most."""
    pitch = D + GAP
    best, best_o = -1.0, anchor
    for fx in np.linspace(0, 1, 5, endpoint=False):
        for fy in np.linspace(0, 1, 5, endpoint=False):
            o = anchor + np.array([fx * pitch, fy * pitch])
            rs = _lay(kind, D, angle, o, clip_lo, clip_hi, grid)
            full = sum(1 for x in rs if x.kind == "full")
            # One pattern's rounds never overlap, so their areas add up exactly.
            score = full * 1000 + sum(x.area for x in rs)
            if score > best:
                best, best_o = score, o
    return best_o


def _graded(grid: Grid, rounds: list[Round], clip_lo, avail: list[float]) -> list[Round]:
    """Smaller rounds into the gaps, biggest gap first."""
    added = []
    free = grid.inside & ~_covered(grid, rounds)
    lo_mask = grid.within(clip_lo)
    smallest = min(avail) / 2
    for _ in range(400):
        dt = ndimage.distance_transform_edt(free & lo_mask) * RES
        k = int(np.argmax(dt))
        r_fit = float(dt.flat[k])
        fits = [d for d in avail if d / 2 <= r_fit - GAP / 2 - RES]
        if not fits or r_fit < smallest:
            break
        d = max(fits)
        c = np.array([grid.X.flat[k], grid.Y.flat[k]])
        rd = Round(c, d / 2, "graded", math.pi * d * d / 4, circle(c, d / 2))
        added.append(rd)
        sl = grid.window(c, d / 2)
        free[sl] &= ~((grid.X[sl] - c[0]) ** 2 + (grid.Y[sl] - c[1]) ** 2 <= (d / 2) ** 2)
    return added


def trace(mask: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> list[np.ndarray]:
    """Outlines of the pieces in a mask, each big enough to cut."""
    import contourpy
    m = np.pad(mask.astype(float), 1)
    x = np.concatenate([[xs[0] - RES], xs, [xs[-1] + RES]])
    y = np.concatenate([[ys[0] - RES], ys, [ys[-1] + RES]])
    gen = contourpy.contour_generator(x=x, y=y, z=m)
    out = []
    for line in gen.lines(0.5):
        line = np.asarray(line, float)
        if len(line) >= 4 and g2.area(line) >= MIN_PIECE:
            if np.allclose(line[0], line[-1]):
                line = line[:-1]
            out.append(line)
    return out


def _copies(grid: Grid, rounds: list[Round], kind: str, D: float, angle: float, origin,
            clip_hi, cut: bool) -> tuple[list[Round], float, float]:
    """Cut to fit: copies of the pattern laid over the gaps, each copied
    round cut down to the gap pieces it covers."""
    gaps = grid.inside & ~_covered(grid, rounds)
    gap_in2 = float(gaps.sum()) * grid.cell
    if not cut:
        return [], gap_in2, gap_in2
    copies = []
    left = gaps.copy()
    pitch = D + GAP
    bbox = (*clip_hi.min(axis=0), *clip_hi.max(axis=0))
    for which in (0, 1):
        o = np.asarray(origin, float) + hole_shift(kind, pitch, angle, which)
        for c in lattice(kind, pitch, angle, o, bbox):
            sl = grid.window(c, D / 2)
            disc = (grid.X[sl] - c[0]) ** 2 + (grid.Y[sl] - c[1]) ** 2 <= (D / 2) ** 2
            piece = disc & left[sl]
            area = float(piece.sum()) * grid.cell
            if area < MIN_PIECE:
                continue
            labels, n = ndimage.label(piece)
            sizes_ = ndimage.sum(piece, labels, range(1, n + 1)) * grid.cell if n else []
            frags = int(sum(1 for s in np.atleast_1d(sizes_) if s >= MIN_PIECE))
            if frags == 0:
                continue
            copies.append(Round(c, D / 2, "copy", area, circle(c, D / 2), frags,
                                trace(piece, grid.xs[sl[1]], grid.ys[sl[0]])))
            left[sl] &= ~disc
    return copies, gap_in2, float(left.sum()) * grid.cell


def layers(panel, pattern: str, stacking: str, D: float, t: float, smallest: float,
           cut: bool, mode: str) -> list[Layer]:
    T = panel.spec.thickness_in
    n = max(1, int(T / t + 1e-6))
    bands = [(k * t, (k + 1) * t) for k in range(n)]
    rest = T - n * t
    if rest > 0.1 and mode == "fill":
        bands.append((n * t, T))
    avail = sizes(D, smallest)
    out = []
    base_angle = 0.0
    anchor = panel.tri.mean(axis=0)
    origin = None
    for k, (z0, z1) in enumerate(bands):
        if mode == "fill":
            clip_lo, clip_hi = panel.opening(z0), panel.opening(z1)
            clip_mid = panel.opening((z0 + z1) / 2)
        else:
            clip_lo = clip_hi = clip_mid = g2.inset_triangle(panel.tri, panel.spec.gasket_in / 2
                                                             - C["cover_overhang_in"])
        grid = Grid(clip_mid)
        # Graded starts from the square grid: its gaps take rounds 0.41 D across,
        # where a honeycomb's take only 0.15 D.
        lat = "hex" if pattern == "hex" else "square"
        angle = base_angle
        if stacking == "rotated":
            a, b = panel.edge(k % 3)
            angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            origin = _best_origin(lat, D, angle, clip_lo, clip_hi, grid, anchor)
        elif origin is None:
            origin = _best_origin(lat, D, angle, clip_lo, clip_hi, grid, anchor)
        o = origin
        if stacking == "offset" and k % 2 == 1:
            o = origin + hole_shift(lat, D + GAP, angle, 0)
        rs = _lay(lat, D, angle, o, clip_lo, clip_hi, grid)
        if pattern == "graded":
            rs += _graded(grid, rs, clip_lo, avail[1:] or avail)
        copies, gaps, void = _copies(grid, rs, lat, D, angle, o, clip_hi, cut)
        L = Layer(k + 1, z0, z1, angle, rs, copies, float(grid.inside.sum()) * grid.cell, gaps, void)
        out.append(L)
    return out


def summary(ls: list[Layer]) -> dict:
    cnt = {"full": 0, "wall": 0, "graded": 0, "copy": 0}
    by_d: dict[float, int] = {}
    wood = 0.0
    for L in ls:
        th = L.z1 - L.z0
        for rd in L.rounds + L.copies:
            cnt[rd.kind] += 1
            d = round(2 * rd.r, 2)
            by_d[d] = by_d.get(d, 0) + 1
        wood += (sum(rd.area for rd in L.rounds) + (L.gaps_in2 - L.void_in2)) * th
    opening = sum(L.open_in2 * (L.z1 - L.z0) for L in ls)
    gaps = sum(L.gaps_in2 * (L.z1 - L.z0) for L in ls)
    void = sum(L.void_in2 * (L.z1 - L.z0) for L in ls)
    frags = sum(rd.frags for L in ls for rd in L.copies)
    return {"counts": cnt, "by_diameter": by_d, "wood_in3": wood, "pattern_cover": 1 - gaps / opening,
            "final_cover": 1 - void / opening, "frags": frags, "layers": len(ls)}


# ----------------------------------------------------------------------
# Words
# ----------------------------------------------------------------------

def steps(ls: list[Layer], D: float, t: float, cut: bool, pattern: str, stacking: str) -> list[str]:
    s = summary(ls)
    c = s["counts"]
    th = sorted({round(L.z1 - L.z0, 2) for L in ls})
    out = [f"Stock: slice the trunk across into rounds {t:g} in thick ({C['chainsaw_kerf_in']:g} in lost to "
           f"each cut). The frame takes {s['layers']} layer(s)" +
           (f"; the last is {th[0]:g} in -- slice a few thinner for it." if len(th) > 1 else "."),
           "Rounds needed, by diameter: " + ", ".join(f"Ø{d:g} in × {n}" for d, n in
                                                      sorted(s["by_diameter"].items(), reverse=True)) + ".",
           f"Lay each layer: {c['full']} whole rounds"
           + (f", {c['graded']} smaller rounds into the gaps" if c["graded"] else "")
           + f", {c['wall']} rounds cut along the wall (chainsaw or bandsaw the chord, blade tilted 45° "
             f"so the cut face lies on the slope)."]
    if stacking == "offset":
        out.append("Every other layer: slide the pattern half a gap over, so each round sits over a gap in "
                   "the layer below.")
    if stacking == "rotated":
        out.append("Each layer: turn the rows to run along the next edge of the triangle.")
    if cut:
        out.append(f"Cut to fit: lay a copy of the pattern over the gaps -- the same rounds, slid so each "
                   f"sits over a gap -- trace each gap onto the round above it, and cut it out. "
                   f"{c['copy']} copied rounds give {s['frags']} gap pieces; a second copy, slid the other "
                   f"way, catches what the first missed.")
    else:
        out.append("Gaps left open: they are vents, and light shows through where a gap runs through "
                   "every layer.")
    return out


def fitting(ls: list[Layer], cut: bool, stacking: str) -> list[str]:
    s = summary(ls)
    out = [f"The pattern alone covers {100 * s['pattern_cover']:.0f}% of the opening, layer for layer"
           + (f"; cut to fit, {100 * s['final_cover']:.1f}%. What is left are slivers under "
              f"{MIN_PIECE:g} sq in -- caulk them." if cut else "."),
           "Rounds need something to sit on: the opening is open at the flat side. Back the first layer "
           "with a board, mesh or film, or set the rounds in mortar or cob as a cordwood wall is.",
           "End grain faces out: it drinks water. Oil the faces, or keep them under the skin."]
    if stacking == "offset":
        out.append("Offset layers break every gap: no gap in one layer lines up with a gap in the next.")
    if stacking == "aligned" and not cut:
        out.append("Aligned layers with open gaps: the gaps line up and run straight through.")
    return out
