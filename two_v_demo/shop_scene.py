"""The shop in the Cabin World: the 10 x 5 ft plasma table, its sheet, the
steel vessel it cuts, a 3V dome in plate, and the router head.

Every dimension comes from :mod:`cnc_table` (frame, gantry, rails, racks,
slats, motors) or :mod:`plate_nesting` (the sheet's forty parts, where the
nest put them; the vessel's faceted shell) or :mod:`panel_method` (the 3V
dome) -- drawn, never retyped. Sites stand on the hill's flat top in the
clear corridor north of the wedge dome.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cnc_table as ct
from . import panel_method as pm
from . import panel_scene as ps
from . import plate_nesting as pn
from .geometry import normalize
from .render_kit import TriangleBatch

MM, IN = 0.001, 0.0254

TABLE = np.array([0.9, 6.0])          # centre of the table's frame, on the ground
FRAME_TOP = 0.80                       # the guide's 700 mm legs on feet
VESSEL = np.array([-2.0, 6.6])
STEEL_DOME = np.array([0.9, 6.3])
PERSON_H = 1.75                        # a person for scale, declared: 5 ft 9 in

TUBE = (0.32, 0.34, 0.37, 1.0)
RAIL = (0.70, 0.73, 0.76, 1.0)
RACK = (0.45, 0.46, 0.48, 1.0)
PLATE = (0.55, 0.57, 0.60, 1.0)
CUT = (0.82, 0.84, 0.86, 1.0)
WATER = (0.25, 0.45, 0.60, 0.55)
MOTOR = (0.10, 0.10, 0.11, 1.0)
TORCH = (0.85, 0.20, 0.15, 1.0)
WELD = (0.30, 0.24, 0.18, 1.0)
MDF = (0.70, 0.58, 0.40, 1.0)
PLY = ps.PLY


def box_between(b: TriangleBatch, a, c, w: float, h: float, colour, up=(0, 0, 1.0)) -> None:
    """A rectangular bar from a to c, w wide and h tall."""
    a, c = np.asarray(a, float), np.asarray(c, float)
    d = normalize(c - a)
    upv = np.asarray(up, float)
    if abs(np.dot(d, upv)) > 0.95:
        upv = np.array([1.0, 0, 0])
    side = normalize(np.cross(upv, d)) * w / 2
    lift = normalize(np.cross(d, side)) * h / 2
    top = [a - side + lift, c - side + lift, c + side + lift, a + side + lift]
    ps.prism(b, top, -2 * lift, colour)


# ----------------------------------------------------------------------
# The table
# ----------------------------------------------------------------------

def frame_size() -> tuple[float, float]:
    L, W = ct.frame_mm()
    return L * MM, W * MM


def at_table(x: float, y: float, z: float) -> np.ndarray:
    """Table coordinates: x along the long axis from the frame's centre."""
    return np.array([TABLE[0] + x, TABLE[1] + y, z])


def sheet_origin() -> np.ndarray:
    """Corner of the sheet on the slats (the nest's (0, 0))."""
    return at_table(-ct.SHEET_X_MM * MM / 2, -ct.SHEET_Y_MM * MM / 2, FRAME_TOP + 0.012)


@lru_cache(maxsize=1)
def table_static(bed: str = "slats") -> TriangleBatch:
    """Frame, legs, water pan, bed, long-axis rails and racks."""
    b = TriangleBatch()
    L, W = frame_size()
    t = 0.05
    zt, zb = FRAME_TOP - t / 2, 0.15
    legs = ct.legs_per_side()
    for y in (-W / 2 + t / 2, W / 2 - t / 2):
        for z in (zt, zb):
            box_between(b, at_table(-L / 2, y, z), at_table(L / 2, y, z), t, t, TUBE)
        for k in range(legs):
            x = -L / 2 + t / 2 + (L - t) * k / (legs - 1)
            box_between(b, at_table(x, y, 0.0), at_table(x, y, FRAME_TOP - t), t, t, TUBE, up=(1, 0, 0))
            b.box(at_table(x, y, 0.015), (0.12, 0.12, 0.03), (0.2, 0.2, 0.2, 1))
    for k in range(legs):
        x = -L / 2 + t / 2 + (L - t) * k / (legs - 1)
        box_between(b, at_table(x, -W / 2 + t, zt), at_table(x, W / 2 - t, zt), t, t, TUBE)
    # water pan: walls 120 mm, a tray of water
    pan_z = FRAME_TOP - 0.12
    b.box(at_table(0, 0, pan_z), (L - 2 * t, W - 2 * t, 0.004), (0.25, 0.25, 0.27, 1))
    for y in (-(W / 2 - t - 0.003), W / 2 - t - 0.003):
        b.box(at_table(0, y, pan_z + 0.06), (L - 2 * t, 0.005, 0.12), TUBE)
    for x in (-(L / 2 - t - 0.003), L / 2 - t - 0.003):
        b.box(at_table(x, 0, pan_z + 0.06), (0.005, W - 2 * t, 0.12), TUBE)
    if bed == "slats":
        n = ct.counts()["slats"]
        for k in range(n):
            x = -L / 2 + t + (k + 1) * (L - 2 * t) / (n + 1)
            b.box(at_table(x, 0, FRAME_TOP - 0.02), (0.005, W - 2 * t - 0.01, 0.05), (0.40, 0.38, 0.36, 1))
    else:
        b.box(at_table(0, 0, FRAME_TOP + 0.006), (L - 2 * t, W - 2 * t, 0.019), MDF)
    # long-axis rails on the frame's top, racks on its outer faces; joins marked
    r = ct.rails_per_side()
    for side in (-1, 1):
        y = side * (W / 2 - t / 2)
        box_between(b, at_table(-L / 2, y, FRAME_TOP + 0.009), at_table(L / 2, y, FRAME_TOP + 0.009), 0.02, 0.018, RAIL)
        for j in range(1, r["x_rails_per_line"]):
            x = -L / 2 + j * ct.RAIL_LENGTH_MM * MM
            if x < L / 2:
                b.box(at_table(x, y, FRAME_TOP + 0.0185), (0.004, 0.022, 0.002), (0.9, 0.3, 0.2, 1))
        yr = side * (W / 2 + 0.008)
        x0 = -L / 2 + ct.RACK_SET_IN_MM * MM
        x1 = L / 2 - ct.RACK_SET_IN_MM * MM
        box_between(b, at_table(x0, yr, FRAME_TOP - 0.015), at_table(x1, yr, FRAME_TOP - 0.015), 0.015, 0.015, RACK)
        for j in range(1, r["x_racks"]):
            x = x0 + j * ct.RACK_LENGTH_MM * MM
            if x < x1:
                b.box(at_table(x, yr + side * 0.0076, FRAME_TOP - 0.015), (0.004, 0.002, 0.016), (0.95, 0.8, 0.2, 1))
    return b


def gantry_x(p: float) -> float:
    """Where the gantry stands along the long axis for a progress 0..1."""
    L, _ = frame_size()
    return -L / 2 + 0.25 + (L - 0.5) * p


def gantry(b: TriangleBatch, x: float, y_head: float, head: str = "torch", z_down: float = 0.0) -> np.ndarray:
    """The gantry at x, its carriage at y_head; returns the tool point."""
    L, W = frame_size()
    span = ct.gantry_tube_mm() * MM
    z_beam = FRAME_TOP + 0.20
    box_between(b, at_table(x, -span / 2, z_beam), at_table(x, span / 2, z_beam), 0.05, 0.10, TUBE, up=(0, 0, 1))
    for side in (-1, 1):
        y = side * (W / 2 - 0.025)
        b.box(at_table(x, y, FRAME_TOP + 0.12), (0.35, 0.005, 0.20), PLATE)
        b.box(at_table(x + 0.13, y + side * 0.06, FRAME_TOP + 0.09), (0.057, 0.057, 0.113), MOTOR)
    # gantry rails on the front face
    for dz in (0.03, -0.03):
        box_between(b, at_table(x - 0.034, -span / 2, z_beam + dz), at_table(x - 0.034, span / 2, z_beam + dz),
                    0.018, 0.02, RAIL)
    c = at_table(x - 0.06, y_head, z_beam)
    b.box(c, (0.006, 0.14, 0.18), PLATE)
    b.box(c + [0.02, 0, 0.14], (0.057, 0.057, 0.113), MOTOR)
    tip = at_table(x - 0.09, y_head, FRAME_TOP + 0.025 + z_down)
    if head == "torch":
        ps_cyl(b, tip + [0, 0, 0.20], tip, 0.016, TORCH)
        ps_cyl(b, tip + [0, 0, 0.42], tip + [0, 0, 0.20], 0.022, MOTOR)
    else:
        ps_cyl(b, tip + [0, 0, 0.32], tip + [0, 0, 0.06], 0.040, (0.85, 0.86, 0.88, 1))
        ps_cyl(b, tip + [0, 0, 0.06], tip, 0.004, (0.7, 0.7, 0.7, 1))
    return tip


def ps_cyl(b, top, bottom, r, colour):
    from .lesson_cabin_linseed_oil import solid_cylinder
    solid_cylinder(b, bottom, top, r, colour, 14)


# ----------------------------------------------------------------------
# The sheet and its forty parts
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def nest():
    return pn.max_radius("strict")


def part_world(poly) -> list[np.ndarray]:
    o = sheet_origin()
    return [o + np.array([x * IN, y * IN, 0.0]) for x, y in poly]


def sheet_batch(cut_upto: int = 0, lift: list[int] = ()) -> TriangleBatch:
    """The plate, with parts already cut drawn bright and parts still to come
    scribed; ``lift`` raises chosen parts off the sheet."""
    b = TriangleBatch()
    o = sheet_origin()
    sw, sh = ct.SHEET_X_MM * MM, ct.SHEET_Y_MM * MM
    b.box(o + [sw / 2, sh / 2, -0.0015], (sw, sh, 0.003), PLATE)
    _r, lay = nest()
    for i, part in enumerate(lay.parts):
        pts = part_world(part.polygon)
        z = 0.002 + (0.08 if i in lift else 0.0)
        if i < cut_upto:
            ps.slab(b, [p + [0, 0, z + 0.003] for p in pts], 0.003, CUT)
        else:
            for k in range(len(pts)):
                box_between(b, pts[k] + [0, 0, 0.0016], pts[(k + 1) % len(pts)] + [0, 0, 0.0016], 0.004, 0.0012,
                            (0.15, 0.15, 0.16, 1))
    return b


def torch_point(p: float) -> tuple[int, np.ndarray]:
    """Which part the torch is on and where, for cutting progress 0..1."""
    _r, lay = nest()
    n = len(lay.parts)
    k = min(n - 1, int(p * n))
    f = p * n - k
    pts = part_world(lay.parts[k].polygon)
    perim = [math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    s = f * sum(perim)
    for i, seg in enumerate(perim):
        if s <= seg:
            a, c = pts[i], pts[(i + 1) % len(pts)]
            return k, a + (c - a) * (s / seg)
        s -= seg
    return k, pts[0]


# ----------------------------------------------------------------------
# The vessel: the 2V shell welded from the sheet
# ----------------------------------------------------------------------

def vessel_batch(at: np.ndarray, bowl: bool = False, lift: float = 0.0) -> TriangleBatch:
    """The forty panels as 3 mm plate, seams darkened; ``bowl`` turns it over
    on three short legs."""
    radius, _ = nest()
    v, faces = pn._mesh(radius * IN)
    g = pn._two_v()
    b = TriangleBatch()
    sign = -1.0 if bowl else 1.0
    base_z = (radius * IN + 0.15) if bowl else 0.0
    place = lambda q: np.array([at[0] + q[0], at[1] + q[1] * sign, base_z + sign * q[2] + lift])
    centre = place(np.zeros(3))
    for f in faces:
        pts = [place(v[k]) for k in f]
        n = normalize(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        if np.dot(n, np.mean(pts, axis=0) - centre) < 0:
            n = -n
        ps.prism(b, pts, -n * 0.003, PLATE)
    edges: dict[tuple[int, int], int] = {}
    for f in faces:
        for k in range(3):
            e = tuple(sorted((f[k], f[(k + 1) % 3])))
            edges[e] = edges.get(e, 0) + 1
    for (a, c), n in edges.items():
        if n == 2:
            ps_cyl(b, place(v[a]), place(v[c]), 0.004, WELD)
    if bowl:
        R = radius * IN
        rho = 0.45 * R
        reach = base_z - math.sqrt(R * R - rho * rho) + 0.01     # up to the bowl's own skin
        for k in range(3):
            ang = math.tau * k / 3
            foot = at + rho * np.array([math.cos(ang), math.sin(ang)])
            box_between(b, [foot[0], foot[1], 0.0], [foot[0], foot[1], reach], 0.03, 0.03, TUBE, up=(1, 0, 0))
    return b


def person(b: TriangleBatch, at, colour=(0.25, 0.35, 0.55, 1)) -> None:
    """A plain standing figure, for scale."""
    at = np.asarray(at, float)
    ps_cyl(b, at + [0, 0, PERSON_H * 0.52], at, 0.07, colour)
    ps_cyl(b, at + [0, 0, PERSON_H * 0.86], at + [0, 0, PERSON_H * 0.52], 0.15, colour)
    b.sphere(at + [0, 0, PERSON_H * 0.93], 0.10, (0.85, 0.70, 0.55, 1), 6, 10)


# ----------------------------------------------------------------------
# A 3V dome in plate, at the size that nests well
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def sweet_spot() -> dict:
    s = pn.three_v_sweet_spot(8, 16)
    good = [t for t in s if t["used_pct"] >= 60]
    return max(good, key=lambda t: t["base_ft"])


@lru_cache(maxsize=1)
def steel_dome_batch() -> TriangleBatch:
    ref = pm.reference()
    base_ft = sweet_spot()["base_ft"]
    d = pm.PanelDome(base_ft * 0.3048 / 2 / ref.cut.base_radius, ref.stick_width_m, ref.stick_depth_m, ref.cut)
    b = TriangleBatch()
    centre = np.array([STEEL_DOME[0], STEEL_DOME[1], 0.0])
    low = d.cut.cut_level

    def place(v):
        return np.array([STEEL_DOME[0] + v[0] * d.radius_m, STEEL_DOME[1] + v[1] * d.radius_m,
                         0.12 + (v[2] - low) * d.radius_m])
    mid = place(np.zeros(3))
    for i in d.cut.faces:
        pts = [place(d.sphere.vertices[k]) for k in d.sphere.faces[i]]
        n = normalize(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        if np.dot(n, np.mean(pts, axis=0) - mid) < 0:
            n = -n
        ps.prism(b, pts, -n * 0.004, PLATE if not d.sphere.is_pentagon_face(i) else (0.62, 0.60, 0.56, 1))
    for e in d.cut.base:
        a, c = place(d.sphere.vertices[e.a]), place(d.sphere.vertices[e.b])
        quad = [np.array([a[0], a[1], 0.0]), np.array([c[0], c[1], 0.0]), c, a]
        inward = normalize(np.array([STEEL_DOME[0] - (a[0] + c[0]) / 2, STEEL_DOME[1] - (a[1] + c[1]) / 2, 0.0]))
        ps.prism(b, quad, inward * 0.006, TUBE)
    return b


def steel_dome_top() -> np.ndarray:
    ref = pm.reference()
    base_ft = sweet_spot()["base_ft"]
    r = base_ft * 0.3048 / 2 / ref.cut.base_radius
    return np.array([STEEL_DOME[0], STEEL_DOME[1], 0.12 + (1 - ref.cut.cut_level) * r])


# ----------------------------------------------------------------------
# The router's work: a panel jig being cut
# ----------------------------------------------------------------------

def router_work(b: TriangleBatch, p: float) -> np.ndarray:
    """A plywood sheet on the spoilboard and a hexagon panel's jig outline
    routed into it, the cutter where the cut has reached."""
    sheet_c = at_table(0.0, 0.0, FRAME_TOP + 0.0165 + 0.0095)
    b.box(sheet_c, (2.44, 1.22, 0.019), PLY)
    hexa = pm.reference().panel_classes()[1]
    ax, ay = pm.trammel_apex(*hexa.sides)
    o = sheet_c + [-hexa.base / 2, -hexa.height / 2, 0.0096]
    pts = [o, o + [hexa.base, 0, 0], o + [ax, ay, 0]]
    perim = [math.dist(pts[i], pts[(i + 1) % 3]) for i in range(3)]
    s = p * sum(perim)
    tip = pts[0]
    for i, seg in enumerate(perim):
        a, c = pts[i], pts[(i + 1) % 3]
        if s >= seg:
            box_between(b, a, c, 0.006, 0.002, (0.25, 0.18, 0.10, 1))
            s -= seg
        else:
            tip = a + (c - a) * (s / seg)
            box_between(b, a, tip, 0.006, 0.002, (0.25, 0.18, 0.10, 1))
            break
    return tip


def validate_shop_scene() -> None:
    ct.validate_cnc_table()
    L, W = frame_size()
    corners = [TABLE + [sx * L / 2, sy * W / 2] for sx in (-1, 1) for sy in (-1, 1)]
    assert max(float(np.linalg.norm(c)) for c in corners) < 9.0, "the table stands on the hill's flat top"
    from . import cabin_world as cw
    assert min(float(np.linalg.norm(c)) for c in corners) > cw.landmarks().deck_r
    radius, lay = nest()
    assert len(lay.parts) == 40 and not pn.verify(lay)
    o = sheet_origin()
    for part in lay.parts:
        for p in part_world(part.polygon):
            assert -1e-9 <= p[0] - o[0] <= ct.SHEET_X_MM * MM + 1e-9
    for batch in (table_static(), sheet_batch(10, [3]), vessel_batch(VESSEL), vessel_batch(VESSEL, True),
                  steel_dome_batch()):
        assert np.all(np.isfinite(batch.vertices)) and batch.vertices
    b = TriangleBatch()
    tip = gantry(b, gantry_x(0.5), 0.1)
    assert np.all(np.isfinite(tip))
