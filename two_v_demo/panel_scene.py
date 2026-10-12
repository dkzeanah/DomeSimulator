"""The panel method's props in the Cabin World: drawn from :mod:`panel_method`.

Everything here is geometry the solver produced -- the 3V 5/8 dome's
panels, their pinwheeled sticks, the tapered base sections, the radial deck,
the jig with its trammel arcs, the bevel rip, the zome built without a bevel
-- placed in the world at named sites. Nothing is a picture of anybody's
plan: the shapes are computed, then drawn.

Sites (metres, z up), chosen so nothing stands in the trees or off the
hill's flat top:

``SITE``  the 3V panel dome, north of the wedge dome on the open valley side
``JIG``   the shop: a plywood jig on sawhorses, south-east of the wedge dome
``ZOME``  a one-fifth-scale zome model on the second seam bench
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import channel_scene as sc
from . import panel_method as pm
from .geometry import normalize
from .render_kit import TriangleBatch

SITE = np.array([0.9, 6.3])
DECK_TOP = 0.45                     # the 3V deck's walking surface, metres
JIG = np.array([3.7, -2.4])
SHEET = (2.44, 1.22, 0.019)        # a sheet of 3/4-in plywood, long side along x
JIG_TOP = sc.SAWHORSE_TOP + 0.08 + SHEET[2]
ZOME_BENCH = sc.BENCH_B
ZOME_SCALE = 0.2                   # the zome on the bench is a model, and says so

PINE = (0.93, 0.76, 0.50, 1.0)
PINE_DARK = (0.72, 0.53, 0.30, 1.0)
PLY = (0.86, 0.74, 0.55, 1.0)
FILM = (0.92, 0.96, 1.0, 0.30)
LETTER = {"A": (1.00, 0.70, 0.25, 1.0), "B": (0.30, 0.80, 0.90, 1.0), "C": (0.55, 0.88, 0.45, 1.0)}
TAPER = (1.00, 0.62, 0.20, 1.0)
LEVEL = (0.35, 0.78, 0.88, 1.0)
STEEL = (0.58, 0.64, 0.70, 1.0)
LINE = (0.20, 0.16, 0.12, 1.0)
GIRDER = (0.55, 0.40, 0.24, 1.0)


# ----------------------------------------------------------------------
# Solid pieces, wound outward (the renderer culls back faces)
# ----------------------------------------------------------------------

def prism(batch: TriangleBatch, top: list[np.ndarray], down: np.ndarray, colour) -> None:
    """A flat polygon ``top`` swept by ``down`` into a solid, every face outward."""
    top = [np.asarray(p, dtype=float) for p in top]
    bottom = [p + down for p in top]
    centre = np.mean(top + bottom, axis=0)

    def face(points):
        n = np.cross(points[1] - points[0], points[2] - points[0])
        mid = np.mean(points, axis=0)
        if np.dot(n, mid - centre) < 0:
            points = points[::-1]
        for k in range(1, len(points) - 1):
            batch.triangle(points[0], points[k], points[k + 1], colour)

    face(top)
    face(bottom)
    for k in range(len(top)):
        j = (k + 1) % len(top)
        face([top[k], top[j], bottom[j], bottom[k]])


def slab(batch: TriangleBatch, polygon: list[np.ndarray], thickness: float, colour) -> None:
    prism(batch, polygon, np.array([0.0, 0.0, -thickness]), colour)


def _cross(p, d, q, e) -> np.ndarray:
    """Where two coplanar lines p + t d and q + s e meet."""
    a = np.stack([d, -e], axis=1)
    t, _s = np.linalg.lstsq(a, q - p, rcond=None)[0]
    return p + t * d


def pinwheel_sticks(corners: list[np.ndarray], normal: np.ndarray, width: float):
    """The in-plane outline of each stick of a pinwheeled panel.

    Side ``i`` runs corner i -> i+1. Its stick reaches all the way to corner
    i (its head, where the previous stick butts it) and stops at the inside
    face of the next stick (its tail) -- the rule ``panel_method`` sizes.
    Returns one quad per side: head corner, tail on the outline, tail inside,
    head inside.
    """
    n = len(corners)
    centroid = np.mean(corners, axis=0)
    dirs, ins = [], []
    for i in range(n):
        d = normalize(corners[(i + 1) % n] - corners[i])
        u = normalize(np.cross(normal, d))
        if np.dot(u, centroid - corners[i]) < 0:
            u = -u
        dirs.append(d)
        ins.append(u)
    quads = []
    for i in range(n):
        prev, nxt = (i - 1) % n, (i + 1) % n
        p, d, u = corners[i], dirs[i], ins[i]
        head_out = p
        head_in = _cross(p + u * width, d, corners[prev], dirs[prev])
        tail_out = _cross(p, d, corners[nxt] + ins[nxt] * width, dirs[nxt])
        tail_in = _cross(p + u * width, d, corners[nxt] + ins[nxt] * width, dirs[nxt])
        quads.append([head_out, tail_out, tail_in, head_in])
    return quads


def framed_panel(batch: TriangleBatch, corners, outward: np.ndarray, width: float, depth: float,
                 colours=None) -> None:
    """A panel's sticks, pinwheeled, set in from the outline by nothing and
    extruded ``depth`` toward the inside of the building."""
    corners = [np.asarray(c, dtype=float) for c in corners]
    outward = normalize(outward)
    for k, quad in enumerate(pinwheel_sticks(corners, outward, width)):
        prism(batch, quad, -outward * depth, colours[k] if colours else PINE)


def film(batch: TriangleBatch, corners, outward: np.ndarray, colour=FILM, lift: float = 0.004) -> None:
    pts = [np.asarray(c, dtype=float) + normalize(outward) * lift for c in corners]
    for k in range(1, len(pts) - 1):
        batch.triangle(pts[0], pts[k], pts[k + 1], colour, normalize(outward))
        batch.triangle(pts[0], pts[k + 1], pts[k], colour, -normalize(outward))


# ----------------------------------------------------------------------
# The 3V panel dome on its site
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def dome() -> pm.PanelDome:
    return pm.reference()


def to_world(v: np.ndarray) -> np.ndarray:
    """A unit-sphere point of the reference dome, placed on its deck."""
    d = dome()
    return np.array([SITE[0] + v[0] * d.radius_m, SITE[1] + v[1] * d.radius_m,
                     DECK_TOP + base_board() + (v[2] - d.cut.cut_level) * d.radius_m])


def base_board() -> float:
    return pm.CONSTANTS["base_board_in"].value * 0.0254


@lru_cache(maxsize=1)
def panels() -> tuple[tuple[int, tuple[np.ndarray, ...], np.ndarray, float], ...]:
    """(face index, world corners, outward normal, centroid height) per kept face."""
    d = dome()
    out = []
    centre = to_world(np.zeros(3))
    for i in d.cut.faces:
        corners = tuple(to_world(d.sphere.vertices[k]) for k in d.sphere.faces[i])
        n = normalize(np.cross(corners[1] - corners[0], corners[2] - corners[0]))
        mid = np.mean(corners, axis=0)
        if np.dot(n, mid - centre) < 0:
            n = -n
        out.append((int(i), corners, n, float(mid[2])))
    return tuple(out)


def centre_top() -> np.ndarray:
    d = dome()
    return to_world(np.array([0.0, 0.0, 1.0]))


def letters(face_index: int) -> list[str]:
    s = dome().sphere
    t = s.faces[face_index]
    return [s.chord_letter(int(t[k]), int(t[(k + 1) % 3])) for k in range(3)]


def frame_batch(coloured: bool = False, upto: float | None = None, skip=()) -> TriangleBatch:
    """Every panel's sticks. ``coloured`` paints sticks by chord letter;
    ``upto`` keeps only panels whose centre is below that height (raising)."""
    d = dome()
    b = TriangleBatch()
    for i, corners, n, z in panels():
        if (upto is not None and z > upto) or i in skip:
            continue
        cols = [LETTER[x] for x in letters(i)] if coloured else None
        framed_panel(b, corners, n, d.stick_width_m, d.stick_depth_m, cols)
    return b


def base_batch(highlight: bool = False) -> TriangleBatch:
    """The base sections: boards standing on the deck up to each base edge,
    tapered where the edge's two ends sit at different heights."""
    d = dome()
    b = TriangleBatch()
    thick = d.stick_width_m
    centre = np.array([SITE[0], SITE[1], DECK_TOP])
    for e in d.cut.base:
        pa, pb = to_world(d.sphere.vertices[e.a]), to_world(d.sphere.vertices[e.b])
        quad = [np.array([pa[0], pa[1], DECK_TOP]), np.array([pb[0], pb[1], DECK_TOP]), pb, pa]
        inward = normalize(np.array([centre[0] - (pa[0] + pb[0]) / 2, centre[1] - (pa[1] + pb[1]) / 2, 0.0]))
        colour = (TAPER if e.tapered else LEVEL) if highlight else PINE_DARK
        # The base sections are tall only by the taper plus a board: make them
        # a visible band by standing them on a sill one board high.
        prism(b, quad, inward * thick, colour)
    return b


def skin_batch(by_section: bool = False) -> TriangleBatch:
    """Covering film over every panel; ``by_section`` tints whole pentagons
    and hexagons that are skinned in one sheet."""
    d = dome()
    b = TriangleBatch()
    groups = section_groups() if by_section else {}
    tint = {"pentagon": (1.0, 0.75, 0.35, 0.42), "hexagon": (0.40, 0.85, 0.95, 0.38)}
    for i, corners, n, _z in panels():
        kind = groups.get(i)
        film(b, corners, n, tint[kind] if kind else FILM)
    return b


@lru_cache(maxsize=1)
def section_groups() -> dict[int, str]:
    """face index -> 'pentagon' | 'hexagon' for faces in a whole section."""
    d = dome()
    s = d.sphere
    kept = set(d.cut.faces)
    around: dict[int, list[int]] = {}
    for i in kept:
        for v in s.faces[i]:
            around.setdefault(int(v), []).append(i)
    used: dict[int, str] = {}
    for v, fs in sorted(around.items(), key=lambda kv: s.valence[kv[0]]):
        need = int(s.valence[v])
        if len(fs) == need and not set(fs) & set(used):
            for f in fs:
                used[f] = "pentagon" if need == 5 else "hexagon"
    return used


def cut_ghost() -> TriangleBatch:
    """The part of the sphere the 5/8 cut leaves out, as a faint shell."""
    d = dome()
    b = TriangleBatch()
    kept = set(d.cut.faces)
    centre = to_world(np.zeros(3))
    for i, t in enumerate(d.sphere.faces):
        if i in kept:
            continue
        corners = [to_world(d.sphere.vertices[k]) for k in t]
        n = normalize(np.cross(corners[1] - corners[0], corners[2] - corners[0]))
        if np.dot(n, np.mean(corners, axis=0) - centre) < 0:
            n = -n
        film(b, corners, n, (0.75, 0.82, 0.95, 0.10), 0.0)
    return b


# ----------------------------------------------------------------------
# The deck
# ----------------------------------------------------------------------

def deck_corners() -> list[np.ndarray]:
    """The deck follows the base: one corner under each base corner."""
    d = dome()
    vs = []
    for e in d.cut.base:
        for v in (e.a, e.b):
            if v not in vs:
                vs.append(v)
    pts = [to_world(d.sphere.vertices[v]) for v in vs]
    pts.sort(key=lambda p: math.atan2(p[1] - SITE[1], p[0] - SITE[0]))
    return [np.array([p[0], p[1], DECK_TOP]) for p in pts]


def deck_batch(reveal: float = 1.0, floor: bool = True) -> TriangleBatch:
    """Posts, a five-sided girder ring, one joist per corner, the rim, and
    the subfloor, appearing in that order as ``reveal`` runs 0 -> 1."""
    b = TriangleBatch()
    corners = deck_corners()
    n = len(corners)
    joist_h, joist_w = 0.14, 0.038
    girder_h = 0.14
    centre = np.array([SITE[0], SITE[1], DECK_TOP])
    girder_r = 0.62 * float(np.linalg.norm(corners[0][:2] - SITE))
    gz = DECK_TOP - joist_h - girder_h / 2
    ring = [np.array([SITE[0] + girder_r * math.cos(math.tau * k / 5 + math.pi / 2),
                      SITE[1] + girder_r * math.sin(math.tau * k / 5 + math.pi / 2), gz]) for k in range(5)]
    stages = [i / 5 for i in range(5)]
    if reveal > stages[0]:
        for p in ring:
            b.box((p[0], p[1], gz / 2 - 0.03), (0.09, 0.09, gz - 0.06), STEEL)
            b.box((p[0], p[1], 0.06), (0.4, 0.4, 0.12), (0.62, 0.62, 0.60, 1.0))
    if reveal > stages[1]:
        for k in range(5):
            a, c = ring[k], ring[(k + 1) % 5]
            mid, vec = (a + c) / 2, c - a
            ang = math.atan2(vec[1], vec[0])
            _box_along(b, a, c, 0.09, girder_h, GIRDER)
    if reveal > stages[2]:
        for p in corners:
            top_a = np.array([centre[0], centre[1], DECK_TOP - joist_h / 2])
            top_b = np.array([p[0], p[1], DECK_TOP - joist_h / 2])
            _box_along(b, top_a + (top_b - top_a) * 0.06, top_b, joist_w, joist_h, PINE)
    if reveal > stages[3]:
        for k in range(n):
            a, c = corners[k], corners[(k + 1) % n]
            _box_along(b, a - [0, 0, joist_h / 2], c - [0, 0, joist_h / 2], joist_w, joist_h, PINE_DARK)
    if reveal > stages[4] and floor:
        slab(b, [c + [0, 0, 0.0] for c in corners], 0.022, (0.78, 0.66, 0.48, 1.0))
    return b


def _box_along(b: TriangleBatch, a: np.ndarray, c: np.ndarray, width: float, height: float, colour) -> None:
    d = normalize(c - a)
    side = normalize(np.cross(np.array([0.0, 0.0, 1.0]), d))
    w, h = side * width / 2, np.array([0.0, 0.0, height / 2])
    top = [a - w + h, c - w + h, c + w + h, a + w + h]
    prism(b, top, -2 * h, colour)


def brackets() -> TriangleBatch:
    """An angle bracket at every base corner, the base section to the deck."""
    b = TriangleBatch()
    for p in deck_corners():
        inward = normalize(np.array([SITE[0] - p[0], SITE[1] - p[1], 0.0]))
        at = p + inward * 0.06
        b.box(at + [0, 0, 0.004], (0.07, 0.07, 0.008), STEEL)
        b.box(at - inward * 0.02 + [0, 0, 0.035], (0.02, 0.02, 0.06), STEEL)
    return b


# ----------------------------------------------------------------------
# The shop: plywood on sawhorses, the jig drawn, the sticks
# ----------------------------------------------------------------------

def jig_bench() -> TriangleBatch:
    b = TriangleBatch()
    for dx in (-0.8, 0.8):
        sc._sawhorses(b, np.array([JIG[0] + dx, JIG[1]]))
    b.box((JIG[0], JIG[1], JIG_TOP - SHEET[2] / 2), SHEET, PLY)
    return b


def on_jig(x: float, y: float, z: float = 0.0) -> np.ndarray:
    """A point on the jig sheet, metres from its centre (x along the long side)."""
    return np.array([JIG[0] + x, JIG[1] + y, JIG_TOP + z])


def panel_on_jig(pc: pm.PanelClass, x0: float = 0.0) -> list[np.ndarray]:
    """A panel's outline laid on the sheet: base along x, apex toward +y."""
    ax, ay = pm.trammel_apex(*pc.sides)
    y0 = -pc.height / 2
    left = on_jig(x0 - pc.base / 2, y0)
    return [left, left + [pc.base, 0, 0], left + [ax, ay, 0]]


def scribe(b: TriangleBatch, a: np.ndarray, c: np.ndarray, colour=LINE, w: float = 0.004) -> None:
    _box_along(b, a + [0, 0, 0.001], c + [0, 0, 0.001], w, 0.002, colour)


def arc(b: TriangleBatch, centre: np.ndarray, radius: float, start: float, end: float,
        colour=LINE, steps: int = 24) -> None:
    pts = [centre + radius * np.array([math.cos(t), math.sin(t), 0.0])
           for t in np.linspace(start, end, steps)]
    for p, q in zip(pts, pts[1:]):
        scribe(b, p, q, colour, 0.005)


def rails(b: TriangleBatch, outline: list[np.ndarray], stick_w: float) -> None:
    """A rail screwed down inside each line, a stick's width in."""
    n = len(outline)
    centroid = np.mean(outline, axis=0)
    for i in range(n):
        p, q = outline[i], outline[(i + 1) % n]
        d = normalize(q - p)
        u = normalize(np.cross(np.array([0, 0, 1.0]), d))
        if np.dot(u, centroid - p) < 0:
            u = -u
        off = u * (stick_w + 0.019 / 2)
        _box_along(b, p + off + d * 0.12 + [0, 0, 0.0095], q + off - d * 0.12 + [0, 0, 0.0095],
                   0.019, 0.019, (0.62, 0.48, 0.30, 1.0))


def board_halves(at: np.ndarray, length: float, p: float, bevel_deg: float) -> TriangleBatch:
    """A 2x3 ripped down its middle on the bevel, the offcut lifted, turned
    end for end about the board's axis, and laid beside the first half.

    Both halves come out the same because the cut passes through the centre
    of a rectangle -- turned half a turn about that centre, a rectangle is
    itself, so each side of the cut is a copy of the other.
    """
    w = pm.CONSTANTS["stock_w_in"].value * 0.0254       # across the face
    h = pm.CONSTANTS["stock_d_in"].value * 0.0254       # the dimension that is halved
    t = math.tan(math.radians(bevel_deg)) * w / 2
    # Cross-section in (y, z), the cut from (-w/2, -t) to (w/2, +t) through the centre.
    lower = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, t), (-w / 2, -t)]
    upper = [(-w / 2, -t), (w / 2, t), (w / 2, h / 2), (-w / 2, h / 2)]
    b = TriangleBatch()
    x0, x1 = at[0] - length / 2, at[0] + length / 2

    def piece(section, angle, shift):
        c, s = math.cos(angle), math.sin(angle)
        pts = [np.array([x0, at[1] + shift[0] + y * c - z * s, at[2] + shift[1] + y * s + z * c])
               for y, z in section]
        prism(b, pts, np.array([length, 0.0, 0.0]), PINE)

    piece(lower, 0.0, (0.0, h / 2))
    lift = math.sin(math.pi * min(p, 1.0)) * 0.12
    piece(upper, math.pi * min(p, 1.0), (0.10 * min(p, 1.0), h / 2 + lift))
    return b


# ----------------------------------------------------------------------
# The zome model
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def zome_faces():
    from .zome_geometry import polar_zonohedron

    c = pm.CONSTANTS
    z = polar_zonohedron(int(c["zome_n"].value), c["zome_pitch_deg"].value)
    verts = np.asarray(z.vertices, dtype=float)
    scale = c["zome_side_m"].value / z.strut_length * ZOME_SCALE
    rim = z.rim_height
    base = np.array([ZOME_BENCH[0], ZOME_BENCH[1], sc.SAWHORSE_TOP + 0.02])
    faces = []
    for f in z.faces:
        if min(verts[k][2] for k in f) < rim - 1e-9:
            continue
        pts = [base + (verts[k] - [0, 0, rim]) * scale for k in f]
        faces.append(pts)
    return tuple(tuple(f) for f in faces), base, scale


def zome_batch(gap_marks: bool = False) -> TriangleBatch:
    faces, base, scale = zome_faces()
    m = 0.0254 * ZOME_SCALE
    w, depth = pm.CONSTANTS["zome_w_in"].value * m, pm.CONSTANTS["zome_d_in"].value * m
    b = TriangleBatch()
    centre = base + [0, 0, 0.12]
    for pts in faces:
        n = normalize(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        if np.dot(n, np.mean(pts, axis=0) - centre) < 0:
            n = -n
        framed_panel(b, list(pts), n, w, depth)
    b.box((base[0], base[1], base[2] - 0.01), (0.95, sc.SPECIMEN_LEN, 0.02), PLY)
    return b


def zome_panel_on_jig(row: int = 1, x0: float = 0.0) -> list[np.ndarray]:
    """One full-size zome rhombus of a row, flat on the jig sheet."""
    r = pm.reference_zome()[row - 1]
    side = pm.CONSTANTS["zome_side_m"].value
    a = math.radians(r.acute_deg)
    p0 = on_jig(x0 - (side + side * math.cos(a)) / 2, -side * math.sin(a) / 2)
    e1 = np.array([side, 0, 0])
    e2 = np.array([side * math.cos(a), side * math.sin(a), 0])
    return [p0, p0 + e1, p0 + e1 + e2, p0 + e2]


def validate_panel_scene() -> None:
    pm.validate_panel_method()
    corners = [np.zeros(3), np.array([1.0, 0, 0]), np.array([0.4, 0.8, 0])]
    quads = pinwheel_sticks(corners, np.array([0, 0, 1.0]), 0.05)
    d = dome()
    pc = d.panel_classes()[1]
    outline = panel_on_jig(pc)
    sticks = pinwheel_sticks(outline, np.array([0, 0, 1.0]), d.stick_width_m)
    for k, quad in enumerate(sticks):
        drawn = float(np.linalg.norm(quad[1] - quad[0]))
        assert abs(drawn - pc.stick(k, d.stick_width_m).outer_length) < 1e-9, (k, drawn)
    assert len(quads) == 3 and len(panels()) == d.panel_count
    assert min(p[2] for p in deck_corners()) == DECK_TOP
    low = min(to_world(d.sphere.vertices[v])[2] for e in d.cut.base for v in (e.a, e.b))
    assert abs(low - DECK_TOP - base_board()) < 1e-9, "the lowest corner sits one board up"
    # The 3V dome stands on the hill's flat top and clear of the wedge dome's deck.
    from . import cabin_world as cw
    m = cw.landmarks()
    reach = float(np.linalg.norm(SITE)) + d.cut.base_radius * d.radius_m
    assert reach < 9.0, "off the hill's flat top"
    assert float(np.linalg.norm(SITE)) - d.cut.base_radius * d.radius_m > m.deck_r, "into the wedge dome's deck"
    for batch in (frame_batch(), base_batch(True), skin_batch(True), deck_batch(), jig_bench(),
                  zome_batch(), cut_ghost(), brackets(), board_halves(on_jig(0, 0, 0.04), 0.9, 0.5, 6.5)):
        v = np.asarray(batch.vertices)
        assert v.size and np.all(np.isfinite(v))
