"""The triangle infill and the floor base, placed in the Cabin World.

Nothing here is modelled for the film. The pieces are the 3-D tool's own
solids (:mod:`infill.solids`, :mod:`infill.base`), turned into the renderer's
triangles by the tool's own mesher (:func:`infill.app3d.solid_tris`), and a
cut on the saw is :func:`infill.sawview.parts` and :func:`infill.sawview.moment`
-- exactly what the tool draws. This module only decides *where* in the world
each thing stands:

* a triangle panel lies on the exhibit platform north of the dome
  (:data:`two_v_demo.cabin_stage.CENTRE`), its long base toward the dome;
* the mitre saw stands on the platform, its operator on the north side, so a
  camera behind them looks across the saw at the dome;
* the floor base is laid round the dome's own centre, a flat side of the
  pentagon toward the platform, its top at the deck's height.

Inches become metres here and nowhere else.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from .render_kit import TriangleBatch

IN = 0.0254
PANEL_LIFT = 0.03                      # m: the panel lies on battens on the platform
SAW_TABLE_Z = 0.92                     # m above the platform: a saw on its stand
WOOD = (0.80, 0.62, 0.40, 1.0)


def _rows(solid, colour):
    from infill.app3d import solid_tris
    return solid_tris(solid, colour)


class Xf:
    """Panel or saw inches -> world metres: rotate about z (and tilt), then move."""

    def __init__(self, R: np.ndarray, T: np.ndarray, scale: float = IN):
        self.R, self.T, self.s = np.asarray(R, float), np.asarray(T, float), scale

    def point(self, p) -> np.ndarray:
        return self.R @ (np.asarray(p, float) * self.s) + self.T

    def emit(self, batch: TriangleBatch, solid, colour, offset=(0.0, 0.0, 0.0), shade: float = 1.0,
             seam: float = 0.0) -> None:
        """``seam`` (in) pulls the piece in toward its own middle in plan, so a
        dark line shows between neighbours whose tops are flush."""
        if solid is None or not solid.faces:
            return
        col = (colour[0] * shade, colour[1] * shade, colour[2] * shade, colour[3])
        rows = _rows(solid, col).astype(np.float64)
        if not len(rows):
            return
        if seam > 0:
            c = rows[:, 0:2].mean(axis=0)
            d = rows[:, 0:2] - c
            r = np.abs(d)
            span = np.maximum(r.max(axis=0), 1e-6)
            rows[:, 0:2] = c + d * np.maximum(0.0, 1.0 - seam / span)
        rows[:, 0:3] = ((rows[:, 0:3] + np.asarray(offset, float)) * self.s) @ self.R.T + self.T
        rows[:, 3:6] = rows[:, 3:6] @ self.R.T
        batch.vertices.extend(rows.ravel().tolist())

    def box(self, batch: TriangleBatch, centre, size, colour) -> None:
        """An axis-aligned box in source inches (rotated with the transform)."""
        c = np.asarray(centre, float)
        h = np.asarray(size, float) / 2
        corners = [c + h * np.array(s) for s in
                   [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
        P = [self.point(p) for p in corners]
        for a, b, cc, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            batch.triangle(P[a], P[b], P[cc], colour)
            batch.triangle(P[a], P[cc], P[d], colour)


def _rz(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0.0], [math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]])


def _rx(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[1.0, 0.0, 0.0], [0.0, math.cos(a), -math.sin(a)], [0.0, math.sin(a), math.cos(a)]])


# ----------------------------------------------------------------------
# The triangle panel
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def panel(index: int = 0):
    from infill.frame import Spec, solve
    return solve(Spec())["types"][index]


@lru_cache(maxsize=None)
def layout(material: str, arrangement: str, lay: str, mode: str, index: int = 0):
    from infill.facts import _opts
    from infill.patterns import layout as lay_out
    return lay_out(panel(index), _opts(material, arrangement, lay, mode))


@lru_cache(maxsize=None)
def recipes(material: str, arrangement: str, lay: str, mode: str):
    from infill import recipes as rc
    return tuple(rc.recipes(layout(material, arrangement, lay, mode)))


def panel_xf(index: int = 0, lift: float = PANEL_LIFT, tilt_deg: float = 0.0, raise_m: float = 0.0) -> Xf:
    """The panel on the platform, its long base toward the dome. ``tilt_deg``
    lifts its far (apex) edge, turning the underside toward the north."""
    tri = panel(index).tri
    c = tri.mean(axis=0)
    base_y = float(tri[:, 1].min())
    R = _rx(tilt_deg) if tilt_deg else np.eye(3)
    pivot = np.array([c[0], base_y, 0.0])
    world = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1] - (c[1] - base_y) * IN,
                      cabin_stage.HEIGHT + lift + raise_m])
    return Xf(R, world - R @ (pivot * IN))


def frame_batch(index: int = 0, xf: Xf | None = None) -> TriangleBatch:
    """The triangle's frame: three wedge members on a sawn face, points in."""
    from infill import geom2d as g2
    from infill import section as sec
    from infill import solids as so
    from infill.draw import PALETTE
    from infill.app3d import rgb
    p = panel(index)
    xf = xf or panel_xf(index)
    b = TriangleBatch()
    wall = sec.frame_section(p.spec.radius_in, p.spec.wall_deg)
    for k, poly in enumerate(p.members()):
        a, bb = p.edge(k)
        d = g2.unit(bb - a)
        m = p.inward(k)
        org = a + m * p.inset_at(0.0)
        s = so.prism(wall, ["frame"] * len(wall), org, d, m, 0.0)
        proj = (poly - org) @ d
        s = so.clip(s, so.Plane(s.along, float(s.along @ s.origin) + float(proj.min()), "frame end"))
        s = so.clip(s, so.Plane(-s.along, -(float(s.along @ s.origin) + float(proj.max())), "frame end"))
        xf.emit(b, s, rgb(PALETTE["frame"]))
    return b


def piece_colour(piece) -> tuple:
    from infill.app3d import POSE_COLOR, rgb
    from infill.draw import PALETTE
    col = POSE_COLOR.get(piece.pose, rgb(PALETTE.get(piece.material, PALETTE["sheet"])))
    if piece.material in ("osb", "ply"):
        col = rgb(PALETTE["sheet"])
    elif piece.material in ("metal", "film"):
        col = rgb(PALETTE[piece.material])
    return col


def pieces_batch(material, arrangement, lay, mode, count: int | None = None, xf: Xf | None = None,
                 highlight: int | None = None, drop: float = 0.0, index: int = 0) -> TriangleBatch:
    """The first ``count`` pieces (all by default); piece number ``highlight``
    in amber; the last one ``drop`` (0..1) of the way down from above."""
    L = layout(material, arrangement, lay, mode, index)
    xf = xf or panel_xf(index)
    b = TriangleBatch()
    n = len(L.pieces) if count is None else max(0, min(count, len(L.pieces)))
    for i, p in enumerate(L.pieces[:n]):
        col = (1.0, 0.80, 0.28, 1.0) if highlight == i + 1 else piece_colour(p)
        off = (0.0, 0.0, 30.0 * (1 - drop) ** 2) if (i == n - 1 and drop < 1.0) else (0.0, 0.0, 0.0)
        xf.emit(b, p.solid, col, off, 1.0 if i % 2 == 0 else 0.82, seam=0.35)
    return b


def piece_centre(material, arrangement, lay, mode, number: int, xf: Xf | None = None) -> np.ndarray:
    L = layout(material, arrangement, lay, mode)
    xf = xf or panel_xf()
    v = L.pieces[number - 1].solid.vertices()
    return xf.point(v.mean(axis=0) + [0.0, 0.0, 2.0])


def panel_corner(k: int, xf: Xf | None = None, index: int = 0) -> np.ndarray:
    xf = xf or panel_xf(index)
    p = panel(index).tri[k]
    return xf.point([p[0], p[1], 0.0])


# ----------------------------------------------------------------------
# The saw
# ----------------------------------------------------------------------

def saw_xf() -> Xf:
    """Saw inches -> world: the operator (saw -y) stands north of the platform's
    centre, facing the dome; the fence is on the dome's side."""
    R = _rz(180.0)
    T = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1] + 0.25, cabin_stage.HEIGHT + SAW_TABLE_Z])
    return Xf(R, T)


@lru_cache(maxsize=None)
def cut_parts(material, arrangement, lay, mode, number: int, step: int):
    from infill import sawview
    r = recipes(material, arrangement, lay, mode)[number - 1]
    return sawview.parts(r.steps[step].anim)


def saw_batch(sc: dict, t: float, xf: Xf | None = None, stand: bool = True) -> tuple[TriangleBatch, dict]:
    """The bench, the stick (keeper and offcut where they are at ``t``) and the
    blade. Returns the batch and the moment, for labels."""
    from infill import sawview
    from infill.app3d import rgb
    xf = xf or saw_xf()
    b = TriangleBatch()
    for centre, size, colour in sawview.bench(sc):
        xf.box(b, centre, size, rgb(colour))
    if stand and sc["type"] == "mitre":
        for x in (-30.0, 30.0):
            for y in (-18.0, -2.0):
                xf.box(b, (x, y, -SAW_TABLE_Z / IN / 2 - 0.75), (2.0, 2.0, SAW_TABLE_Z / IN - 1.5),
                       (0.25, 0.27, 0.3, 1.0))
    mo = sawview.moment(sc, t)
    wood = (0.80, 0.62, 0.40, 1.0) if not sc["whole"] else (0.86, 0.74, 0.52, 1.0)
    xf.emit(b, sc["keeper"], wood, mo["offsets"]["keeper"])
    xf.emit(b, sc["offcut"], (0.95, 0.78, 0.30, 1.0), mo["offsets"]["offcut"])
    ns, c, r = mo["blade_axis"], mo["blade_centre"], mo["blade_r"]
    a, bb = xf.point(c - ns * 0.06), xf.point(c + ns * 0.06)
    b.cylinder(a, bb, r * IN, (0.84, 0.87, 0.89, 1.0), 40)
    b.cylinder(xf.point(c - ns * 0.15), xf.point(c + ns * 0.15), 0.9 * IN, (0.22, 0.25, 0.29, 1.0), 12)
    return b, mo


def saw_point(sc: dict, part: str, t: float, xf: Xf | None = None, up: float = 4.0) -> np.ndarray:
    from infill import sawview
    xf = xf or saw_xf()
    mo = sawview.moment(sc, t)
    at = sc.get(part + "_at")
    if at is None:
        at = sc["bp"]
    return xf.point(np.asarray(at, float) + mo["offsets"].get(part, 0.0) + [0.0, 0.0, up])


# ----------------------------------------------------------------------
# The floor base
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def base(pattern: str = "star_joists", prim: str = "half", support: str = "piers", deck: str = "2x6",
         sec_mat: str = "2x8"):
    from infill import base as bs
    from infill.frame import Spec, solve
    deck = "fill" if support == "gravel" else deck
    o = bs.BaseOptions(pattern=pattern, prim_mat=prim, support=support, deck=deck, sec_mat=sec_mat,
                       dome_radius_in=solve(Spec())["radius_in"])
    return bs.build(o)


@lru_cache(maxsize=None)
def base_cut(pattern: str, number: int, kind: str = "mitre"):
    """The first cut of base member ``number`` of the given kind, on the saw."""
    from infill import sawview
    b = base(pattern)
    r = next(rr for rr in b.recipes if rr.number == number)
    an = next(s.anim for s in r.steps if s.anim and s.anim.get("type") == kind)
    return sawview.parts(an)


def base_xf(b) -> Xf:
    """Round the dome's centre, a flat side toward the platform, its top at the
    deck's height (on piers) or on the ground (on gravel)."""
    top = cw.landmarks().deck_centre[2]
    dz = top - b.top * IN if b.opts.support == "piers" else 0.0
    return Xf(_rz(180.0), np.array([0.0, 0.0, dz]))


def base_batch(b, roles=("frame", "primary", "joist"), count: int | None = None, piers: bool = True,
               highlight: int | None = None, drop: float = 1.0) -> TriangleBatch:
    """The base's members (those in ``roles``, the first ``count`` of them) and
    its piers, each pier reaching down to the grass."""
    xf = base_xf(b)
    out = TriangleBatch()
    ms = [m for m in b.members if m.role in roles]
    n = len(ms) if count is None else max(0, min(count, len(ms)))
    for i, m in enumerate(ms[:n]):
        kind = next(p for p in b.pieces if p.ref is m)
        col = (1.0, 0.80, 0.28, 1.0) if highlight == m.number else kind.color
        off = (0.0, 0.0, 60.0 * (1 - drop) ** 2) if (i == n - 1 and drop < 1.0) else (0.0, 0.0, 0.0)
        xf.emit(out, m.solid, col, off, 1.0 if i % 2 == 0 else 0.93)
    if piers:
        for p in b.piers:
            top = xf.point([p.xy[0], p.xy[1], p.top])
            ground = np.array([top[0], top[1], 0.0])
            out.cylinder(ground, top, 0.5 * 12.0 * IN, (0.50, 0.42, 0.34, 1.0), 14)
    return out


def base_point(b, plan_xy, z_in: float | None = None) -> np.ndarray:
    xf = base_xf(b)
    z = b.top + 6.0 if z_in is None else z_in
    return xf.point([plan_xy[0], plan_xy[1], z])


def member_point(b, number: int, along: float = 0.5, up: float = 8.0) -> np.ndarray:
    m = b.members[number - 1]
    p = m.a + (m.b - m.a) * along
    return base_point(b, p, b.top + up)


def corner_cut(b, member: int = 1, t: float = 0.0) -> tuple[TriangleBatch, dict]:
    """The first end of a frame trunk cut where it lies: the keeper in place,
    the offcut falling away from the end as ``t`` runs past halfway."""
    from infill import solids as so
    m = b.members[member - 1]
    r = next(rr for rr in b.recipes if rr.number == m.number)
    an = next(s.anim for s in r.steps if s.anim and s.anim.get("type") in ("mitre", "freehand"))
    xf = base_xf(b)
    out = TriangleBatch()
    away = max(0.0, min(1.0, (t - 0.55) / 0.35))
    xf.emit(out, an["keeper"], (0.42, 0.27, 0.16, 1.0))
    if an["offcut"] is not None and an["offcut"].faces:
        d = -np.array([m.along[0], m.along[1], 0.0]) * 18.0 * away + np.array([0.0, 0.0, -6.0 * away])
        xf.emit(out, an["offcut"], (0.95, 0.78, 0.30, 1.0), d)
    pl = an["plane"]
    info = {"plane": pl, "member": m, "away": away}
    if 0.15 < t < 0.6:
        # The cut line drawn across the top, plumb down both sides.
        n2 = np.array([pl.n[0], pl.n[1]])
        tdir = np.array([-n2[1], n2[0]])
        c = n2 * pl.d
        s0 = float((m.a - c) @ tdir)
        mid = c + tdir * s0
        P = [xf.point([*(mid + tdir * k * 9.0), b.top + 0.3]) for k in (-1, 1)]
        out.cylinder(P[0], P[1], 0.012, (1.0, 0.25, 0.2, 1.0), 6)
        info["mark"] = (P[0] + P[1]) / 2
    del so
    return out, info


def validate_infill_scene() -> None:
    xf = panel_xf()
    b = pieces_batch("w8", "parallel", "flipflop", "fill")
    v = np.asarray(b.vertices).reshape(-1, 10)
    assert len(v) and np.isfinite(v).all()
    # The panel lies on the platform, inside its radius.
    d = np.hypot(v[:, 0] - cabin_stage.CENTRE[0], v[:, 1] - cabin_stage.CENTRE[1])
    assert d.max() < cabin_stage.RADIUS + 0.2, d.max()
    assert v[:, 2].min() >= cabin_stage.HEIGHT - 1e-6
    sc = cut_parts("w8", "parallel", "flipflop", "fill", 5, 1)
    sb, mo = saw_batch(sc, 0.4)
    assert len(sb.vertices) and mo["cutting"]
    bb = base("star_joists")
    fb = base_batch(bb)
    w = np.asarray(fb.vertices).reshape(-1, 10)
    assert np.isfinite(w).all() and np.hypot(w[:, 0], w[:, 1]).max() < 5.3
    top = cw.landmarks().deck_centre[2]
    assert abs(w[:, 2].max() - top) < 0.01, (w[:, 2].max(), top)
    del xf
