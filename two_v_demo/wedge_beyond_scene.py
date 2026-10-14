"""The exhibits for *Beyond the Dome*: wedge lumber at true size, on the platform.

Every piece is a solid extruded from a cross-section the project computes:
the wedges and pairs from :mod:`square_book.geometry` (the same functions the
book's tables and drawings read), the zome from :mod:`wedge_zome.geometry`.
Builders return :class:`TriangleBatch` es in world metres, standing on the
Cabin World's exhibit platform (:mod:`two_v_demo.cabin_stage`).
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_stage
from .render_kit import TriangleBatch

IN = 0.0254
PC = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
WOOD = (0.86, 0.66, 0.42, 1.0)
WOOD_B = (0.76, 0.53, 0.31, 1.0)
END = (0.94, 0.80, 0.58, 1.0)
BARK = (0.38, 0.28, 0.20, 1.0)
PICK = (1.0, 0.62, 0.22, 1.0)
PLANE = (1.0, 0.82, 0.35, 0.30)
SHIM = (0.98, 0.86, 0.62, 1.0)
WATER = (0.42, 0.70, 0.94, 0.55)
STEEL = (0.55, 0.57, 0.60, 1.0)
TABLE = (0.52, 0.49, 0.45, 1.0)
DARK = (0.50, 0.34, 0.20, 1.0)


def _v(*a) -> np.ndarray:
    return np.array(a, dtype=float)


def solid(batch: TriangleBatch, a_ring, b_ring, colour, side_colours=None, cap=END) -> None:
    """A prism between two matching polygons, every face wound outward."""
    a_ring = [np.asarray(p, float) for p in a_ring]
    b_ring = [np.asarray(p, float) for p in b_ring]
    centre = np.mean(a_ring + b_ring, axis=0)

    def face(pts, col):
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        if np.linalg.norm(n) < 1e-12:
            return
        n = n / np.linalg.norm(n)
        if n @ (np.mean(pts, axis=0) - centre) < 0:
            pts, n = pts[::-1], -n
        for k in range(1, len(pts) - 1):
            batch.triangle(pts[0], pts[k], pts[k + 1], col, n)

    face(a_ring, cap)
    face(b_ring, cap)
    m = len(a_ring)
    for k in range(m):
        col = side_colours[k] if side_colours else colour
        face([a_ring[k], a_ring[(k + 1) % m], b_ring[(k + 1) % m], b_ring[k]], col)


def extrude(batch, section, origin, axis, u, v, length_m, colour, side_colours=None, cap=END) -> None:
    """A section given in (u, v) metres, swept ``length_m`` along ``axis`` from ``origin``."""
    ring = [origin + u * s[0] + v * s[1] for s in section]
    solid(batch, ring, [p + axis * length_m for p in ring], colour, side_colours, cap)


# ----------------------------------------------------------------------
# Wedges and pairs, from square_book.geometry
# ----------------------------------------------------------------------

def _sg():
    from square_book import geometry as sg
    return sg


def _fig():
    from square_book import figures as sf
    return sf


def wedge(diameter: float = None, n: int = 8):
    sg = _sg()
    return sg.Wedge(diameter or sg.D["reference_log_in"], n)


def log_split(spread: float, length_in: float = 72.0) -> TriangleBatch:
    """The reference log, split eight ways, its wedges easing apart."""
    w = wedge()
    r = w.r * IN
    b = TriangleBatch()
    axis = _v(1, 0, 0)
    origin = PC + _v(-length_in * IN / 2, 0.0, r + 0.02)
    seg = 6
    for k in range(w.n):
        a0 = math.tau * k / w.n
        a1 = math.tau * (k + 1) / w.n
        mid = (a0 + a1) / 2
        push = spread * 0.09
        off = _v(0, math.cos(mid) * push, math.sin(mid) * push)
        pts = [(0.0, 0.0)] + [(r * math.cos(a0 + (a1 - a0) * j / seg), r * math.sin(a0 + (a1 - a0) * j / seg))
                              for j in range(seg + 1)]
        cols = [WOOD] + [BARK] * seg + [WOOD_B]
        extrude(b, pts, origin + off, axis, _v(0, 1, 0), _v(0, 0, 1), length_in * IN, WOOD, cols)
    return b


def _tri_section(w, eff=True):
    sf = _fig()
    return [(x * IN, y * IN) for x, y in sf.triangle(w, eff=eff)]


def wedge_single(length_in: float = 40.0) -> TriangleBatch:
    """One trimmed eighth, back down, point up."""
    w = wedge()
    b = TriangleBatch()
    t = _tri_section(w)
    # rotate so the back (points 1-2) lies flat
    (x1, y1), (x2, y2) = t[1], t[2]
    ang = -math.atan2(y2 - y1, x2 - x1)
    ca, sa = math.cos(ang), math.sin(ang)
    rot = [((x - x1) * ca - (y - y1) * sa, (x - x1) * sa + (y - y1) * ca) for x, y in t]
    if rot[0][1] < 0:
        rot = [(x, -y) for x, y in rot]
    minx = min(x for x, _ in rot)
    sec = [(x - minx - (max(x for x, _ in rot) - minx) / 2, y) for x, y in rot]
    origin = PC + _v(-length_in * IN / 2, 0, 0.002)
    extrude(b, sec, origin, _v(1, 0, 0), _v(0, 1, 0), _v(0, 0, 1), length_in * IN, WOOD,
            [WOOD, WOOD_B, WOOD])
    return b


def _upright(w):
    """The slant pair stood on its long side, in metres, and its planed board."""
    sf = _fig()
    t1, t2, rect = sf.upright_pair(w)
    t1 = [(x * IN, y * IN) for x, y in t1]
    t2 = [(x * IN, y * IN) for x, y in t2]
    rect = tuple(v * IN for v in rect)
    width = max(x for x, _ in t1 + t2)
    t1 = [(x - width / 2, y) for x, y in t1]
    t2 = [(x - width / 2, y) for x, y in t2]
    rect = (rect[0] - width / 2, rect[1] - width / 2, rect[2], rect[3])
    return t1, t2, rect


def slant_pair(t: float, length_in: float = 40.0, at=None, n: int = 8, planed: bool = True) -> tuple:
    """Two wedges going together slant to slant; the planed square ghosts in once they meet."""
    w = wedge(n=n)
    t1, t2, (x0, x1, y0, y1) = _upright(w)
    o = (PC if at is None else at) + _v(-length_in * IN / 2, 0, 0.002)
    lift = (1.0 - min(1.0, t)) * 0.35
    b, tr = TriangleBatch(), TriangleBatch()
    U, V = _v(0, 1, 0), _v(0, 0, 1)
    extrude(b, t1, o, _v(1, 0, 0), U, V, length_in * IN, WOOD, [WOOD, WOOD_B, WOOD])
    extrude(b, t2, o + _v(0, lift * 0.4, lift), _v(1, 0, 0), U, V, length_in * IN, WOOD_B,
            [WOOD_B, WOOD, WOOD_B])
    if planed and t >= 1.0:
        extrude(tr, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], o + _v(-0.004, 0, 0), _v(1, 0, 0), U, V,
                length_in * IN + 0.008, PLANE, cap=PLANE)
    return b, tr


def back_pairs(length_in: float = 36.0) -> TriangleBatch:
    """Quarters back to back (a square) and eighths back to back (a diamond), side by side."""
    q = wedge(n=4)
    e = wedge(n=8)
    b = TriangleBatch()
    U, V, A = _v(0, 1, 0), _v(0, 0, 1), _v(1, 0, 0)
    r = q.r_eff * IN
    o = PC + _v(-length_in * IN / 2, -0.25, 0.002)
    extrude(b, [(0, 0), (r, 0), (0, r)], o, A, U, V, length_in * IN, WOOD)
    extrude(b, [(r, 0), (r, r), (0, r)], o, A, U, V, length_in * IN, WOOD_B)
    h = e.depth * IN * e.scale
    half = e.chord_eff * IN / 2
    o2 = PC + _v(-length_in * IN / 2, 0.30, 0.002)
    extrude(b, [(0, half), (h, 0), (h, 2 * half)], o2, A, U, V, length_in * IN, WOOD)
    extrude(b, [(h, 0), (2 * h, half), (h, 2 * half)], o2, A, U, V, length_in * IN, WOOD_B)
    return b


def tradeoff(length_in: float = 30.0) -> tuple:
    b, tr = TriangleBatch(), TriangleBatch()
    for k, n in enumerate((6, 8, 12, 16)):
        at = PC + _v(0, -0.6 + 0.4 * k, 0)
        bb, tt = slant_pair(1.0, length_in, at=at, n=n)
        b.vertices.extend(bb.vertices)
        tr.vertices.extend(tt.vertices)
    return b, tr


def shim(length_in: float = 36.0) -> TriangleBatch:
    sf = _fig()
    w = wedge()
    tri = sf.triangle(w)
    b2, c2 = tri[1], tri[2]
    ang = -math.degrees(math.atan2(c2[1] - b2[1], c2[0] - b2[0]))
    pts = sf._rot(tri, ang)
    if pts[0][1] < pts[1][1]:
        pts = [(x, -y) for x, y in pts]
    miny = min(y for _, y in pts)
    minx = min(x for x, _ in pts)
    pts = [((x - minx) * IN, (y - miny) * IN) for x, y in pts]
    point, p1, p2 = pts
    left = p1 if p1[0] < p2[0] else p2
    sh = [left, (left[0], point[1]), point]
    o = PC + _v(-length_in * IN / 2, -0.06, 0.002)
    b = TriangleBatch()
    U, V, A = _v(0, 1, 0), _v(0, 0, 1), _v(1, 0, 0)
    extrude(b, pts, o, A, U, V, length_in * IN, WOOD)
    extrude(b, sh, o + _v(length_in * IN * 0.35, 0, 0), A, U, V, length_in * IN * 0.3, SHIM)
    # a plumb board standing against the shimmed face
    x = left[0]
    extrude(b, [(x - 0.04, 0), (x, 0), (x, point[1] + 0.12), (x - 0.04, point[1] + 0.12)],
            o + _v(length_in * IN * 0.3, 0, 0), A, U, V, length_in * IN * 0.4, DARK)
    return b


def _place(batch: TriangleBatch, at, yaw_deg: float = 0.0) -> TriangleBatch:
    """Turn a batch about its own platform point and move it to ``at``."""
    out = TriangleBatch()
    a = math.radians(yaw_deg)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
    v = np.asarray(batch.vertices, float).reshape(-1, 10)
    v[:, 0:3] = (v[:, 0:3] - PC) @ R.T + np.asarray(at, float)
    v[:, 3:6] = v[:, 3:6] @ R.T
    out.vertices = v.reshape(-1).tolist()
    return out


def _stick(b, p0, p1, w, colour=WOOD, up=None) -> None:
    """A wedge stick from p0 to p1, back down (point up), w its trimmed wedge."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    d /= L
    up = np.asarray(up if up is not None else (0, 0, 1.0), float)
    side = np.cross(up, d)
    if np.linalg.norm(side) < 1e-6:
        side = np.cross(_v(0, 1, 0), d)
    side /= np.linalg.norm(side)
    up = np.cross(d, side)
    c = w.chord_eff * IN
    h = w.depth * w.scale * IN
    sec = [(-c / 2, 0), (c / 2, 0), (0, h)]
    extrude(b, sec, p0, d, side, up, L, colour, [colour, WOOD_B, colour])


def _post(b, foot, height_m, side_m, colour=WOOD) -> None:
    h = side_m / 2
    ring = [foot + _v(-h, -h, 0), foot + _v(h, -h, 0), foot + _v(h, h, 0), foot + _v(-h, h, 0)]
    solid(b, ring, [p + _v(0, 0, height_m) for p in ring], colour)


def shed(scale: float = 1.0) -> tuple:
    """A small lean-to: square posts of quarters, rafters of wedges at the eighths' own skew."""
    sg = _sg()
    w = wedge()
    post = sg.Pair(wedge(n=4), "back").planed[0] * IN
    b, tr = TriangleBatch(), TriangleBatch()
    span, depth, low = 1.6 * scale, 1.1 * scale, 1.15 * scale
    pitch = math.radians(w.shim_angle)
    high = low + span * math.tan(pitch)
    x0, y0 = PC[0] - span / 2, PC[1] - depth / 2
    corners = [(x0, y0, low), (x0 + span, y0, high), (x0, y0 + depth, low), (x0 + span, y0 + depth, high)]
    for x, y, h in corners:
        _post(b, _v(x, y, PC[2]), h, post)
    for y in np.linspace(y0, y0 + depth, 5):
        _stick(b, _v(x0 - 0.1, y, PC[2] + low - 0.1 * math.tan(pitch)),
               _v(x0 + span + 0.1, y, PC[2] + high + 0.1 * math.tan(pitch)), w)
    roof = [_v(x0 - 0.1, y0 - 0.05, PC[2] + low - 0.1 * math.tan(pitch) + 0.1),
            _v(x0 + span + 0.1, y0 - 0.05, PC[2] + high + 0.1 * math.tan(pitch) + 0.1),
            _v(x0 + span + 0.1, y0 + depth + 0.05, PC[2] + high + 0.1 * math.tan(pitch) + 0.1),
            _v(x0 - 0.1, y0 + depth + 0.05, PC[2] + low - 0.1 * math.tan(pitch) + 0.1)]
    solid(tr, roof, [p + _v(0, 0, 0.012) for p in roof], (0.55, 0.62, 0.66, 0.45), cap=(0.55, 0.62, 0.66, 0.45))
    return b, tr


def octagon(radius_in: float = 52.0) -> TriangleBatch:
    """Eight wedge joists meeting at the middle -- the eighth's point is the octagon's angle --
    and eight wedge rim boards round them."""
    w = wedge()
    b = TriangleBatch()
    r = radius_in * IN
    z = PC[2] + 0.002
    hub = PC.copy()
    hub[2] = z
    for k in range(8):
        a = math.tau * k / 8
        end = hub + _v(r * math.cos(a), r * math.sin(a), 0)
        _stick(b, hub + _v(0.06 * math.cos(a), 0.06 * math.sin(a), 0), end, w, WOOD if k % 2 else WOOD_B)
    for k in range(8):
        a0, a1 = math.tau * (k + 0.0) / 8, math.tau * (k + 1.0) / 8
        p0 = hub + _v(r * math.cos(a0), r * math.sin(a0), 0)
        p1 = hub + _v(r * math.cos(a1), r * math.sin(a1), 0)
        _stick(b, p0, p1, w, DARK)
    return b


def joints() -> TriangleBatch:
    """Three joints wedges make easy: a slant lap, a bird's mouth, a butterfly key."""
    w = wedge()
    b = TriangleBatch()
    # slant lap: two pairs offset along their length
    for k, at in enumerate((PC + _v(0, -0.55, 0), PC + _v(0.45, -0.55, 0))):
        bb, _ = slant_pair(1.0, 36.0, at=at, planed=False)
        b.vertices.extend(bb.vertices)
    # bird's mouth: a square plate with a wedge set point-down across it
    plate = 3.5 * IN
    o = PC + _v(-0.45, 0.05, 0.002)
    ring = [o + _v(0, -plate / 2, 0), o + _v(0.9, -plate / 2, 0), o + _v(0.9, plate / 2, 0), o + _v(0, plate / 2, 0)]
    solid(b, ring, [p + _v(0, 0, plate) for p in ring], DARK)
    c = w.chord_eff * IN
    h = w.depth * w.scale * IN
    top = o + _v(0.45, 0, plate + h - 0.03)
    extrude(b, [(-c / 2, 0), (c / 2, 0), (0, -h)], top + _v(0, -0.5, 0), _v(0, 1, 0), _v(1, 0, 0), _v(0, 0, 1),
            1.0, WOOD)
    # butterfly key across a glued pair
    at = PC + _v(0, 0.6, 0)
    bb, _ = slant_pair(1.0, 36.0, at=at, planed=False)
    b.vertices.extend(bb.vertices)
    t1, t2, rect = _upright(w)
    ztop = max(y for _, y in t1 + t2)
    k0 = at + _v(0, 0, ztop + 0.003)
    bow = [(-0.06, -0.035), (0.0, -0.012), (0.06, -0.035), (0.06, 0.035), (0.0, 0.012), (-0.06, 0.035)]
    ring = [k0 + _v(x, y, 0) for x, y in bow]
    solid(b, ring, [p + _v(0, 0, 0.012) for p in ring], DARK)
    return b


def seam_v(length_in: float = 40.0) -> tuple:
    """Two wedges on their backs a kerf apart: the V between them, filled with water."""
    sf = _fig()
    w = wedge()
    tri = sf.triangle(w)
    b2, c2 = tri[1], tri[2]
    ang = -math.degrees(math.atan2(c2[1] - b2[1], c2[0] - b2[0]))
    pts = sf._rot(tri, ang)
    if pts[0][1] < pts[1][1]:
        pts = [(x, -y) for x, y in pts]
    miny = min(y for _, y in pts)
    minx = min(x for x, _ in pts)
    pts = [((x - minx) * IN, (y - miny) * IN) for x, y in pts]
    width = max(x for x, _ in pts)
    gap = 0.25 * IN
    pts2 = [(x + width + gap, y) for x, y in pts]
    top1 = max(pts, key=lambda p: p[1])
    top2 = max(pts2, key=lambda p: p[1])
    shift = width + gap / 2
    pts = [(x - shift, y) for x, y in pts]
    pts2 = [(x - shift, y) for x, y in pts2]
    top1 = (top1[0] - shift, top1[1])
    top2 = (top2[0] - shift, top2[1])
    o = PC + _v(-length_in * IN / 2, 0, 0.002)
    U, V, A = _v(0, 1, 0), _v(0, 0, 1), _v(1, 0, 0)
    b, tr = TriangleBatch(), TriangleBatch()
    extrude(b, pts, o, A, U, V, length_in * IN, WOOD)
    extrude(b, pts2, o, A, U, V, length_in * IN, WOOD_B)
    water = [top1, (top1[0] + (0 - top1[0]) * 0.9, top1[1] * 0.1), (top2[0] + (0 - top2[0]) * 0.9, top2[1] * 0.1),
             top2]
    extrude(tr, [(x, y * 0.85) for x, y in water], o + _v(0.01, 0, 0), A, U, V, length_in * IN - 0.02, WATER,
            cap=WATER)
    return b, tr


def aframe(scale: float = 1.0) -> TriangleBatch:
    """An A-frame: rafters of wedge sticks meeting at a ridge, collar ties across."""
    w = wedge()
    b = TriangleBatch()
    span, height, depth = 1.6 * scale, 1.5 * scale, 1.2 * scale
    for y in np.linspace(-depth / 2, depth / 2, 4):
        foot_l = PC + _v(-span / 2, y, 0.002)
        foot_r = PC + _v(span / 2, y, 0.002)
        ridge = PC + _v(0, y, height)
        _stick(b, foot_l, ridge, w, up=_v(-1, 0, 1))
        _stick(b, foot_r, ridge, w, WOOD_B, up=_v(1, 0, 1))
        _stick(b, PC + _v(-span * 0.27, y, height * 0.45), PC + _v(span * 0.27, y, height * 0.45), w, DARK)
    _stick(b, PC + _v(0, -depth / 2 - 0.1, height - 0.02), PC + _v(0, depth / 2 + 0.1, height - 0.02), w, DARK)
    return b


# ----------------------------------------------------------------------
# The zome
# ----------------------------------------------------------------------

ZOME_FIT = 0.66
"""The zome is 13.8 ft across; on the platform it is shown at this fraction of
true size, labels and figures unchanged."""


@lru_cache(maxsize=4)
def _zome(method: str):
    from wedge_zome import geometry as zg
    return zg.build(method)


def _zw(p, fit: float = ZOME_FIT) -> np.ndarray:
    return PC + np.asarray(p, float) * IN * fit + _v(0, 0, 3.5 * IN * fit)


def zome(method: str = "wedge", rise: float = 1.0, explode: float = 0.0, highlight: int = 0,
         channels: bool = False, posts: bool = True, fit: float = ZOME_FIT) -> tuple:
    """The wedge zome, rows arriving bottom row first as ``rise`` goes 0 to 1."""
    m = _zome(method)
    b, tr = TriangleBatch(), TriangleBatch()
    order = sorted(m.rows, reverse=True)                # the sill row first
    for p in m.panels:
        k = order.index(p.row)
        arrive = min(1.0, max(0.0, rise * len(order) - k))
        if arrive <= 0.0:
            continue
        drop = (1.0 - arrive) * 0.8 / (IN * fit)
        shift = p.normal * explode + np.array([0, 0, drop])
        col = PICK if (highlight and p.row == highlight) else None
        for j, s in enumerate(p.sticks):
            tails, heads = s.ends
            solid(b, [_zw(t + shift, fit) for t in tails], [_zw(h + shift, fit) for h in heads],
                  col or (WOOD if j % 2 == 0 else WOOD_B))
    if rise >= 1.0 and explode == 0.0:
        for sm in m.seams:
            pa, pb = m.panels[sm.panels[0]], m.panels[sm.panels[1]]
            e0, e1 = m.vertices[sm.a], m.vertices[sm.b]
            from wedge_zome.geometry import stick_on
            sa, sb = stick_on(pa, sm.a, sm.b), stick_on(pb, sm.a, sm.b)
            if method == "wedge" and channels:
                da = sa.v * sa.section[2][0] + sa.n * sa.section[2][1]
                db = sb.v * sb.section[2][0] + sb.n * sb.section[2][1]
                ring = [[_zw(x, fit), _zw(x + da, fit), _zw(x + db, fit)]
                        for x in (e0 + (e1 - e0) * 0.18, e0 + (e1 - e0) * 0.82)]
                solid(tr, ring[0], ring[1], WATER, cap=WATER)
            elif method == "square":
                ring = [[_zw(x, fit), _zw(x + pa.normal * m.stick_h, fit), _zw(x + pb.normal * m.stick_h, fit)]
                        for x in (e0, e1)]
                solid(b, ring[0], ring[1], DARK)
    if posts and rise >= 1.0:
        sg = _sg()
        side = sg.Pair(sg.Wedge(sg.D["reference_log_in"], 4), "back").planed[0]
        for i, height in m.posts:
            top = m.vertices[i]
            foot = top - np.array([0, 0, height + 3.5])
            h = side / 2
            sq = [np.array([-h, -h, 0]), np.array([h, -h, 0]), np.array([h, h, 0]), np.array([-h, h, 0])]
            solid(b, [_zw(foot + q, fit) for q in sq], [_zw(top - np.array([0, 0, 1.0]) + q, fit) for q in sq], DARK)
    return b, tr


def zome_point(name: str, fit: float = ZOME_FIT) -> np.ndarray:
    m = _zome("wedge")
    if name == "apex":
        return _zw(m.vertices[np.argmax(m.vertices[:, 2])], fit)
    if name == "centre":
        return _zw(np.array([0, 0, float(m.vertices[:, 2].max()) * 0.45]), fit)
    if name == "seam":
        sm = max(m.seams, key=lambda s: (m.vertices[s.a][1] + m.vertices[s.b][1]) * -1 + 0 * s.fold)
        return _zw((m.vertices[sm.a] + m.vertices[sm.b]) / 2, fit)
    if name == "rim":
        i = m.posts[0][0]
        return _zw(m.vertices[i], fit)
    raise KeyError(name)


def zome_panel_on_jig(row: int = 2, method: str = "wedge") -> TriangleBatch:
    """One panel of a row, framed flat on a jig table, true size, outside face down."""
    m = _zome(method)
    p = next(q for q in m.panels if q.row == row)
    pts = [m.vertices[k] for k in p.corners]
    x = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
    y = np.cross(p.normal, x)
    centre = np.mean(pts, axis=0)
    table_top = PC + _v(0, 0, 0.75)
    b = TriangleBatch()
    side = float(np.linalg.norm(pts[1] - pts[0])) * IN
    top = [table_top + _v(*c) for c in ((-side, -side * 0.75, 0), (side, -side * 0.75, 0), (side, side * 0.75, 0),
                                         (-side, side * 0.75, 0))]
    solid(b, [t - _v(0, 0, 0.03) for t in top], top, TABLE)
    for cx in (-side * 0.85, side * 0.85):
        for cy in (-side * 0.6, side * 0.6):
            _post(b, PC + _v(cx, cy, 0), 0.72, 0.06, TABLE)

    def flat(q):
        r = q - centre
        return table_top + _v(float(r @ x), float(r @ y), -float(r @ p.normal)) * IN + _v(0, 0, 0.002)

    for j, s in enumerate(p.sticks):
        tails, heads = s.ends
        solid(b, [flat(t) for t in tails], [flat(h) for h in heads], PICK if j == 0 else WOOD)
    return b


def validate_wedge_beyond_scene() -> None:
    for builder in (lambda: log_split(0.5), wedge_single, back_pairs, shim, octagon, joints, aframe,
                    lambda: zome_panel_on_jig(2)):
        batch = builder()
        v = np.asarray(batch.vertices, float)
        assert len(v) > 0 and np.all(np.isfinite(v))
    for builder in (lambda: slant_pair(1.0), tradeoff, shed, seam_v, lambda: zome("wedge", 1.0, channels=True),
                    lambda: zome("square", 1.0), lambda: zome("wedge", 0.5, explode=10.0)):
        opaque, clear = builder()
        assert len(opaque.vertices) > 0
    # the zome stands on the platform and stays inside the fit radius
    v = np.asarray(zome("wedge", 1.0)[0].vertices, float).reshape(-1, 10)[:, :3]
    assert v[:, 2].min() >= PC[2] - 1e-3
    assert np.max(np.hypot(v[:, 0] - PC[0], v[:, 1] - PC[1])) < cabin_stage.FIT_RADIUS + 0.2
