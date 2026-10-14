"""The whole dome, every triangle filled -- in every way this repository knows how to fill one.

Nothing is modelled for the film. The dome is the Triangle Infill tool's own dome
(:func:`infill.frame.solve` on its default :class:`~infill.frame.Spec`: 72 in longest
finished member, frame members split eight ways from 12 in logs), its forty panels placed
where :func:`two_v_demo.wedge_geometry.pinwheel_panels` puts them. Each panel's frame and
infill are the tool's solids (:mod:`infill.solids`), meshed by the tool's mesher
(:func:`infill.app3d.solid_tris`), so every piece is trimmed to the opening's walls with
the same compound cuts the cut list gives -- flush, cut neatly, as built.

Two families of fill:

* **the tool's patterns** (:func:`infill.patterns.layout`): every arrangement (rings,
  parallel, across, chevron, louvers) with every lay of eighth-log wedges (flip-flop, same
  hand, shimmed, standing, comb), filling the frame or covering it;
* **the owner's pairs** -- two wedges, points facing each other down the triangle, nested
  to bowtie (:func:`two_v_demo.triangle_fill.pair`) -- laid course by course from each
  triangle's top corner, every pair cut to the walls and planed flush with the frame's two
  faces. What the planing takes off is measured here and said on screen.

The dome sits on the Cabin World's deck in place of the world's own dome layer (hide
``"dome"`` when drawing it). Inches become metres here and nowhere else.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import cabin_stage
from .render_kit import TriangleBatch

IN = 0.0254
SEAM_IN = 0.18                      # each piece drawn this much in from its neighbours: a hairline
A_COL = (1.00, 0.80, 0.50, 1.0)     # the pair's two wedges, as in the close-ups
B_COL = (0.78, 0.40, 0.22, 1.0)
LAY_NAMES = {"flipflop": "flip-flop", "samehand": "same hand", "shim": "shimmed", "standing": "standing",
             "comb": "comb", "": "louvered"}
ARR_NAMES = {"rings": "rings", "parallel": "parallel", "across": "across", "chevron": "chevron",
             "louvers": "louvers"}


# ----------------------------------------------------------------------
# The dome and where each panel sits
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def spec():
    from infill.frame import Spec
    return Spec()


@lru_cache(maxsize=1)
def types():
    from infill.frame import solve
    return tuple(solve(spec())["types"])


@lru_cache(maxsize=1)
def radius_in() -> float:
    from infill.frame import solve
    return float(solve(spec())["radius_in"])


@dataclass(frozen=True)
class Seat:
    """One panel on the dome: which type it is, and its local inches -> dome inches map."""

    kind: int
    origin: np.ndarray
    basis: np.ndarray          # columns: local x, local y, local z (into the dome)


@lru_cache(maxsize=1)
def seats() -> tuple[Seat, ...]:
    from infill.frame import _flatten
    from two_v_demo import wedge_geometry as wg
    s = spec()
    names = [t.name for t in types()]
    out = []
    for p in wg.pinwheel_panels(radius_in(), s.radius_in, s.gasket_in):
        classes = [m.edge_class for m in p.members]
        name = "".join(c[0] for c in sorted(classes, key=lambda c: (classes.count(c), c)))
        base = next((i for i, c in enumerate(classes) if classes.count(c) == 1), 0)
        tri, order = _flatten(np.asarray(p.corners, float), base)
        name = "".join(classes[i][0] for i in order)
        kind = names.index(name)
        c = np.asarray(p.corners, float)[order]
        u = (c[1] - c[0]) / tri[1, 0]
        v = (c[2] - c[0] - u * tri[2, 0]) / tri[2, 1]
        n = np.asarray(p.normal, float)
        # z = 0 is the frame's sawn face, in the plane of the corners, outside; z runs inward
        out.append(Seat(kind, c[0], np.column_stack([u, v, -n])))
    return tuple(out)


def counts() -> list[int]:
    return [sum(1 for s in seats() if s.kind == k) for k in range(len(types()))]


def world_origin() -> np.ndarray:
    """The dome's equator centre: the Cabin World deck."""
    from . import cabin_world as cw
    return np.asarray(cw.landmarks().deck_centre, float)


# ----------------------------------------------------------------------
# One panel's pieces, in its own inches
# ----------------------------------------------------------------------

def _shrink(rows: np.ndarray, seam: float) -> np.ndarray:
    if seam <= 0 or not len(rows):
        return rows
    c = rows[:, 0:2].mean(axis=0)
    d = rows[:, 0:2] - c
    span = np.maximum(np.abs(d).max(axis=0), 1e-6)
    rows = rows.copy()
    rows[:, 0:2] = c + d * np.maximum(0.0, 1.0 - seam / span)
    return rows


def _solid_rows(solid, colour, seam: float = SEAM_IN) -> np.ndarray:
    from infill.app3d import solid_tris
    if solid is None or not solid.faces:
        return np.zeros((0, 10), "f4")
    return _shrink(solid_tris(solid, colour).astype(np.float64), seam)


@lru_cache(maxsize=None)
def frame_rows(kind: int) -> np.ndarray:
    """The panel's three frame members, as the tool draws them."""
    from infill import geom2d as g2
    from infill import section as sec
    from infill import solids as so
    from infill.app3d import rgb
    from infill.draw import PALETTE
    p = types()[kind]
    wall = sec.frame_section(p.spec.radius_in, p.spec.wall_deg)
    rows = []
    for k, poly in enumerate(p.members()):
        a, b = p.edge(k)
        d = g2.unit(b - a)
        m = p.inward(k)
        org = a + m * p.inset_at(0.0)
        s = so.prism(wall, ["frame"] * len(wall), org, d, m, 0.0)
        proj = (poly - org) @ d
        s = so.clip(s, so.Plane(s.along, float(s.along @ s.origin) + float(proj.min()), "frame end"))
        s = so.clip(s, so.Plane(-s.along, -(float(s.along @ s.origin) + float(proj.max())), "frame end"))
        rows.append(_solid_rows(s, rgb(PALETTE["frame"]), seam=0.0))
    return np.concatenate(rows)


@lru_cache(maxsize=None)
def pattern_layout(kind: int, arrangement: str, lay: str, mode: str = "fill"):
    from infill.patterns import Options, layout, valid
    return layout(types()[kind], valid(Options("w8", arrangement, lay or "flipflop", mode)))


def _piece_colour(piece):
    from .infill_scene import piece_colour
    return piece_colour(piece)


@lru_cache(maxsize=None)
def pattern_rows(kind: int, arrangement: str, lay: str, mode: str = "fill") -> np.ndarray:
    L = pattern_layout(kind, arrangement, lay, mode)
    rows = []
    for i, piece in enumerate(L.pieces):
        col = _piece_colour(piece)
        shade = 1.0 if i % 2 == 0 else 0.86
        rows.append(_solid_rows(piece.solid, (col[0] * shade, col[1] * shade, col[2] * shade, col[3])))
    return np.concatenate(rows) if rows else np.zeros((0, 10))


def _dial(t: float) -> float:
    """The dial across one triangle, top corner (t = 0) to base (t = 1): nested at the two
    ends where the frame's loads gather, opening to a bowtie through the middle."""
    return 1.0 - math.sin(math.pi * min(1.0, max(0.0, t)))


@lru_cache(maxsize=None)
def pair_solids(kind: int, p: float | str) -> tuple:
    """Every pair in one panel, courses running along its base from the top corner down,
    each wedge cut to the opening's walls and planed flush with the frame's faces.
    ``p`` is an overlap (1 nested, 0 bowtie) or ``"dial"``."""
    from infill import solids as so
    from infill.patterns import Options
    from two_v_demo import triangle_fill as tf
    panel = types()[kind]
    T = panel.spec.thickness_in
    walls = so.bounds(panel, Options(mode="fill"))
    top = panel.opening(T)
    y_hi, y_lo = float(top[:, 1].max()), float(top[:, 1].min())
    cx = float(panel.tri[:, 0].mean())
    w = tf.wedge()
    out, y0 = [], y_hi
    while y0 > y_lo + 1e-6:
        q = _dial((y_hi - y0) / (y_hi - y_lo)) if p == "dial" else float(p)
        pr = tf.pair(q)
        mid = (w["face_in"] + q * w["face_in"] / 2) / 2 - w["face_in"] / 2     # the pair's through-middle
        for sec, col in ((pr["a"], A_COL), (pr["b"], B_COL)):
            # section (down, through) -> prism section (x across = -down along y, z = through)
            pts = np.array([(-dn, T / 2 + (ac - mid)) for dn, ac in sec])
            s = so.prism(pts, ["slant", "face", "slant"], (cx, y0), (1.0, 0.0), (0.0, 1.0), 0.0)
            for pl in walls:
                s = so.clip(s, pl)
            s = so.clip(s, so.Plane(np.array([0.0, 0.0, 1.0]), 0.0, "planed flush"))
            s = so.clip(s, so.Plane(np.array([0.0, 0.0, -1.0]), -T, "planed flush"))
            if s.faces and len(s.faces) >= 4:
                out.append((s, col, q))
        y0 -= pr["span_in"]
    return tuple(out)


def _poly_area(p) -> float:
    p = np.asarray(p, float)
    return 0.5 * abs(float(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1))))


def _clip_band(poly, lo: float, hi: float) -> np.ndarray:
    """A 2-D section clipped to lo <= y <= hi (Sutherland-Hodgman, two edges)."""
    def cut(pts, keep, edge):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            ka, kb = keep(a), keep(b)
            if ka:
                out.append(a)
            if ka != kb:
                t = (edge - a[1]) / (b[1] - a[1])
                out.append(a + (b - a) * t)
        return out
    pts = [np.asarray(q, float) for q in poly]
    pts = cut(pts, lambda q: q[1] >= lo - 1e-12, lo)
    pts = cut(pts, lambda q: q[1] <= hi + 1e-12, hi) if pts else pts
    return np.array(pts) if len(pts) >= 3 else np.zeros((0, 2))


def planed_off(p: float) -> float:
    """What planing a pair flush with the frame's two faces takes off its section, 0 to 1."""
    from two_v_demo import triangle_fill as tf
    T = spec().thickness_in
    w = tf.wedge()
    pr = tf.pair(p)
    mid = (w["face_in"] + p * w["face_in"] / 2) / 2 - w["face_in"] / 2
    full = kept = 0.0
    for sec in (pr["a"], pr["b"]):
        pts = np.array([(dn, T / 2 + (ac - mid)) for dn, ac in sec])
        full += _poly_area(pts)
        band = _clip_band(pts, 0.0, T)
        kept += _poly_area(band) if len(band) else 0.0
    return 1.0 - kept / full


@lru_cache(maxsize=None)
def pair_rows(kind: int, p: float | str) -> np.ndarray:
    rows = []
    for s, col, _q in pair_solids(kind, p):
        rows.append(_solid_rows(s, col))
    return np.concatenate(rows) if rows else np.zeros((0, 10))


# ----------------------------------------------------------------------
# Variants: what a dome can wear
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Variant:
    key: str
    title: str
    family: str          # "pairs" or "pattern"
    p: float | str = 1.0
    arrangement: str = ""
    lay: str = ""
    mode: str = "fill"


PAIRS = (Variant("pairs-nested", "pairs, nested", "pairs", 1.0),
         Variant("pairs-half", "pairs, half slid", "pairs", 0.5),
         Variant("pairs-bowtie", "pairs, bowtie", "pairs", 0.0),
         Variant("pairs-dial", "pairs, dialled", "pairs", "dial"))


def pattern_variants(mode: str = "fill") -> tuple[Variant, ...]:
    from infill.patterns import OPTIONS
    out = []
    for arr in OPTIONS["log"]["arrangements"]:
        if arr == "rings" and mode == "cover":
            continue                    # the tool lays parallel runs for it: not a pattern of its own
        lays = OPTIONS["log"]["lays"] if arr != "louvers" else [""]
        for lay in lays:
            title = f"{ARR_NAMES[arr]}, {LAY_NAMES[lay]}" if lay else ARR_NAMES[arr]
            out.append(Variant(f"{mode}-{arr}-{lay or 'slats'}", title, "pattern", arrangement=arr, lay=lay, mode=mode))
    return tuple(out)


def variants() -> tuple[Variant, ...]:
    return PAIRS + pattern_variants("fill") + pattern_variants("cover")


def by_key(key: str) -> Variant:
    return next(v for v in variants() if v.key == key)


def panel_rows(kind: int, v: Variant | None) -> np.ndarray:
    if v is None:
        return np.zeros((0, 10))
    if v.family == "pairs":
        return pair_rows(kind, v.p)
    return pattern_rows(kind, v.arrangement, v.lay, v.mode)


@lru_cache(maxsize=None)
def facts(key: str) -> dict:
    """What one variant takes for the whole dome: pieces and wedge feet, counted from the
    solids (pairs) or the tool's own piece lengths (patterns)."""
    from two_v_demo import triangle_fill as tf
    v = by_key(key)
    n = counts()
    pieces = feet = left = solid_w = area_w = 0.0
    for kind, c in enumerate(n):
        area = c * float(types()[kind].opening(0.0).shape[0] and _poly_area(types()[kind].opening(0.0)))
        if v.family == "pairs":
            ss = pair_solids(kind, v.p)
            pieces += c * len(ss)
            for s, _col, q in ss:
                x = s.vertices()[:, 0]
                feet += c * float(x.max() - x.min()) / 12
            qs = [q for _s, _c, q in ss]
            solid_w += area * float(np.mean([tf.pair(q)["solid"] for q in qs]))
        else:
            L = pattern_layout(kind, v.arrangement, v.lay, v.mode)
            pieces += c * len(L.pieces)
            feet += c * sum(float(pc.long) for pc in L.pieces) / 12
            left += c * float(L.metrics.get("remainder_in2", 0.0) or 0.0)
            solid_w += area * float(L.metrics.get("solid", 1.0))
        area_w += area
    return {"pieces": int(round(pieces)), "feet": feet, "title": v.title,
            "solid": solid_w / area_w, "left_sqft": left / 144}


# ----------------------------------------------------------------------
# To the world
# ----------------------------------------------------------------------

def _place(rows: np.ndarray, seat: Seat, origin: np.ndarray, scale: float = IN) -> np.ndarray:
    out = rows.copy()
    out[:, 0:3] = (rows[:, 0:3] @ seat.basis.T + seat.origin) * scale + origin
    nn = rows[:, 3:6] @ seat.basis.T
    out[:, 3:6] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    return out


def dome_batch(key: str | None = None, frame: bool = True, show: float = 1.0) -> TriangleBatch:
    """The whole dome: every panel's frame, and ``key``'s fill in the first ``show`` of the
    panels (in order up from the ground, so a dome can fill as it goes)."""
    v = by_key(key) if key else None
    origin = world_origin()
    order = sorted(range(len(seats())), key=lambda i: float(seats()[i].origin[2] + seats()[i].basis[2, 2]))
    upto = int(math.ceil(len(order) * max(0.0, min(1.0, show))))
    filled = set(order[:upto])
    parts = []
    for i, seat in enumerate(seats()):
        if frame:
            parts.append(_place(frame_rows(seat.kind), seat, origin))
        if v is not None and i in filled:
            r = panel_rows(seat.kind, v)
            if len(r):
                parts.append(_place(r, seat, origin))
    b = TriangleBatch()
    if parts:
        b.vertices.extend(np.concatenate(parts).astype(np.float64).ravel().tolist())
    return b


def dome_points() -> list[np.ndarray]:
    """A few points round the dome, for framing a phone cut on it."""
    o, r = world_origin(), radius_in() * IN
    return [o + [r, 0, 0], o + [-r, 0, 0], o + [0, r, 0], o + [0, -r, 0], o + [0, 0, r]]


def dome_radius_m() -> float:
    return radius_in() * IN


# ----------------------------------------------------------------------
# The gallery: one quarter-scale triangle per variant, on the exhibit platform
# ----------------------------------------------------------------------

GALLERY_SCALE = 0.25
GALLERY_TILT = math.radians(55.0)       # stood up toward the camera on the south side


def gallery_slots(keys: tuple[str, ...]) -> dict[str, np.ndarray]:
    """Where each model stands: rows across the platform, centre of each triangle."""
    cols = 6
    rows = math.ceil(len(keys) / cols)
    t = types()[0]
    w = float(np.ptp(t.tri[:, 0])) * IN * GALLERY_SCALE * 1.22
    h = float(np.ptp(t.tri[:, 1])) * IN * GALLERY_SCALE * math.cos(GALLERY_TILT) * 1.9
    c = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
    out = {}
    for i, k in enumerate(keys):
        r, q = divmod(i, cols)
        out[k] = c + np.array([(q - (cols - 1) / 2) * w, (r - (rows - 1) / 2) * h, 0.0])
    return out


def _gallery_seat(at: np.ndarray) -> tuple[Seat, np.ndarray]:
    t = types()[0]
    cx, cy = float(t.tri[:, 0].mean()), float(t.tri[:, 1].mean())
    ct, st = math.cos(GALLERY_TILT), math.sin(GALLERY_TILT)
    # local x -> world x; local y (toward the top corner) -> up and away (north, +y);
    # local z (into the dome) -> toward the viewer standing south... the outside faces south
    basis = np.column_stack([[1.0, 0.0, 0.0], [0.0, ct, st], [0.0, st, -ct]])
    basis[:, 2] = np.cross(basis[:, 0], basis[:, 1]) * -1.0
    lift = np.array([0.0, 0.0, 0.05 + float(np.ptp(t.tri[:, 1])) * IN * GALLERY_SCALE * st / 2])
    origin_in = -(basis @ np.array([cx, cy, 0.0]))
    return Seat(0, origin_in, basis), at + lift


def gallery_batch(keys: tuple[str, ...]) -> TriangleBatch:
    slots = gallery_slots(keys)
    parts = []
    for k in keys:
        seat, at = _gallery_seat(slots[k])
        parts.append(_place(frame_rows(0), seat, at, IN * GALLERY_SCALE))
        r = panel_rows(0, by_key(k))
        if len(r):
            parts.append(_place(r, seat, at, IN * GALLERY_SCALE))
    b = TriangleBatch()
    b.vertices.extend(np.concatenate(parts).astype(np.float64).ravel().tolist())
    return b


def gallery_label_point(key: str, keys: tuple[str, ...]) -> np.ndarray:
    t = types()[0]
    seat, at = _gallery_seat(gallery_slots(keys)[key])
    top = float(np.ptp(t.tri[:, 1])) * IN * GALLERY_SCALE * math.sin(GALLERY_TILT)
    return at + np.array([0.0, 0.0, top / 2 + 0.06])


# ----------------------------------------------------------------------

def validate_infill_dome() -> None:
    assert len(seats()) == 40 and sorted(counts()) == sorted(t.count for t in types())
    for s in seats():
        assert abs(abs(np.linalg.det(s.basis)) - 1.0) < 1e-6
    # every panel's flattened corners land back on the dome's corners
    from two_v_demo import wedge_geometry as wg
    T = spec().thickness_in
    for kind in range(len(types())):
        for p in (1.0, 0.0, "dial"):
            ss = pair_solids(kind, p)
            assert ss, (kind, p)
            for s, _c, _q in ss:
                z = s.vertices()[:, 2]
                assert z.min() >= -1e-6 and z.max() <= T + 1e-6, "pairs are planed flush with the frame"
    for v in variants():
        f = facts(v.key)
        assert f["pieces"] > 0 and f["feet"] > 0, v.key
        if v.mode == "fill" and v.family == "pattern":
            for kind in range(len(types())):
                for pc in pattern_layout(kind, v.arrangement, v.lay, v.mode).pieces:
                    if pc.solid is not None and pc.solid.faces:
                        z = pc.solid.vertices()[:, 2]
                        assert z.min() >= -1e-3 and z.max() <= T + 1e-3, (v.key, "fill sits flush")
    assert 0.0 <= planed_off(0.0) < planed_off(1.0) < 1.0
    b = dome_batch("pairs-nested")
    v = np.asarray(b.vertices).reshape(-1, 10)
    assert np.all(np.isfinite(v))
    r = np.linalg.norm(v[:, 0:3] - world_origin(), axis=1)
    assert r.max() <= dome_radius_m() * 1.01 and r.min() > dome_radius_m() * 0.85, "every piece is in the shell"
    g = gallery_batch(tuple(x.key for x in variants()[:6]))
    assert len(g.vertices)


if __name__ == "__main__":
    validate_infill_dome()
    T = spec().thickness_in
    print(f"dome radius {radius_in():.1f} in, frame {T:.2f} in thick, panels {counts()}")
    print(f"planed flush: nested {planed_off(1.0):.0%}, half {planed_off(0.5):.0%}, bowtie {planed_off(0.0):.0%}")
    for v in variants():
        f = facts(v.key)
        print(f"{v.key:28s} {f['pieces']:5d} pieces {f['feet']:8,.0f} ft")
