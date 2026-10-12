"""The cell wall, built as objects in the Cabin World.

What :mod:`two_v_demo.lesson_cell_wall` draws on top of the world: the
solver's dome with its skin as a stack of layers -- each layer a sheet of
forty triangular cells, each cell with its own local loop, and the layer's
global runs along the seams between the cells -- and a length of wall on the
sawhorses, in section, with the C-channel in each member's round face. Then
the things the layers serve: the tank, the rim ring, the bladders, the cage,
the plants, the fog, the embers.

The layers sit on the frame the world draws, the cover's solve from a 15 in
log (:data:`wedge_book.cover_scene.COVER_TRUNK_IN`); where each face's
members stand is read off that mesh, not assumed. The arithmetic is
:mod:`two_v_demo.cell_wall`'s, from the reference build's 12 in log, as in
every channel film. Where props stand is scene dressing; nothing drawn here
is a figure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import cabin_world as cw
from . import cell_wall as cwall
from . import channel_scene as sc
from .render_kit import TriangleBatch

M = sc.M                                  # metres per inch

DARK = (0.10, 0.08, 0.07, 1.0)
LOOP = (0.20, 0.85, 1.00, 1.0)            # a local hose: cyan reads against pine
GLOW = (1.00, 0.74, 0.32, 1.0)            # the global channel along the seams
GLUE = (0.98, 0.86, 0.35, 1.0)
FOAM = (0.98, 0.88, 0.45, 1.0)
COPPER = (0.85, 0.50, 0.28, 1.0)
STEEL = (0.62, 0.64, 0.68, 1.0)
LEAF = (0.30, 0.66, 0.26, 1.0)
LEAF_LIGHT = (0.48, 0.80, 0.34, 1.0)
SOIL = (0.32, 0.22, 0.14, 1.0)
WATER = (0.35, 0.65, 1.00, 0.85)
EMBER = (1.00, 0.52, 0.12, 1.0)
HOT = (1.00, 0.36, 0.20, 1.0)
COOL = (0.40, 0.72, 1.00, 1.0)
FOG = (0.92, 0.93, 0.96, 0.22)
TANK = (0.22, 0.30, 0.36, 1.0)
CO2 = (0.30, 0.32, 0.36, 1.0)


def colour(key: str, alpha: float | None = None) -> tuple:
    c = cwall.LAYER[key].colour
    return (c[0], c[1], c[2], c[3] if alpha is None else alpha)


def rgb(key: str) -> tuple[int, int, int]:
    """A layer's colour for a label: lifted toward white so it reads on the sky."""
    c = cwall.LAYER[key].colour
    return tuple(int(255 * (0.35 + 0.65 * v)) for v in c[:3])


# ----------------------------------------------------------------------
# The faces of the world's dome, and where its members stand on them
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Face:
    index: int                 # the solver's face index
    corners: tuple             # three world points: the plane through the vertices
    centre: np.ndarray
    normal: np.ndarray         # outward
    incentre: np.ndarray
    inradius: float
    slope_deg: float           # from level
    top: float                 # the members' round faces, above the plane: where sheathing bears
    bottom: float              # the members' inner side, below the plane
    missing: bool              # one of the crown triangles not yet up
    lower: bool                # where the bladders go


@lru_cache(maxsize=1)
def faces() -> tuple[Face, ...]:
    from wedge_book import cover_scene as cs

    model, scale, shift = sc._world()
    topo = model.topology
    v = np.asarray(topo.vertices, dtype=float) * scale + shift
    missing = set(cw.missing_faces())
    # Every member triangle, by the face that owns it -- cover_scene.dome_batch's own rule.
    tri = cs.dome_triangles(cs.sizes()).astype(np.float64)[:, :, 0:3]
    mids = tri.mean(axis=1) - shift
    face_dirs = np.array([f.center / np.linalg.norm(f.center) for f in topo.faces])
    dirs = mids / np.maximum(np.linalg.norm(mids, axis=1, keepdims=True), 1e-9)
    owner = np.argmax(dirs @ face_dirs.T, axis=1)
    zs = [float(np.mean([v[i][2] for i in f.vertices]) - shift[2]) for f in topo.faces]
    low = set(cwall.lower_of(zs))
    out = []
    for i, f in enumerate(topo.faces):
        a, b, c = (v[k] for k in f.vertices)
        n = np.cross(b - a, c - a)
        n /= np.linalg.norm(n)
        centre = (a + b + c) / 3
        if np.dot(n, centre - shift) < 0:
            n = -n
        la, lb, lc = np.linalg.norm(b - c), np.linalg.norm(c - a), np.linalg.norm(a - b)
        incentre = (la * a + lb * b + lc * c) / (la + lb + lc)
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        mine = tri[owner == i].reshape(-1, 3)
        d = (mine - a) @ n
        out.append(Face(f.index, (a, b, c), centre, n, incentre, float(2 * area / (la + lb + lc)),
                        math.degrees(math.acos(min(1.0, abs(float(n[2]))))),
                        float(d.max()), float(d.min()), f.index in missing, i in low))
    return tuple(out)


def standing() -> list[Face]:
    """The faces that have their frame: everything but the open crown."""
    return [f for f in faces() if not f.missing]


def loop_inset() -> float:
    """How far in from the seam line a member's groove runs, in the world.

    The groove is at the middle of the round face, which is where the panel's
    sheathing bears (the sector's bisector is square to its own panel, because
    fold + V = the sector angle). From the seam line that is r (sin V/2 + sin fold/2)."""
    t = sc.tight()
    r = cw.landmarks().trunk_r
    return r * (math.sin(math.radians(t.gap_deg / 2)) + math.sin(math.radians(t.fold_deg / 2)))


def member_width() -> float:
    """The round face's chord: how far the cavity starts in from the seam line."""
    return 2 * cw.landmarks().trunk_r * math.sin(math.pi / cw.landmarks().splits)


def inset(f: Face, d: float, h: float) -> list[np.ndarray]:
    """The face's corners moved ``d`` in from every edge and ``h`` out along its normal."""
    k = max(0.03, (f.inradius - d) / f.inradius)
    return [f.incentre + (p - f.incentre) * k + f.normal * h for p in f.corners]


def tile(batch: TriangleBatch, f: Face, h: float, colour, d: float = 0.05, both: bool = False) -> None:
    a, b, c = inset(f, d, h)
    batch.triangle(a, b, c, colour, f.normal)
    if both:
        batch.triangle(a, c, b, colour, -f.normal)


def loop(batch: TriangleBatch, f: Face, h: float, colour, r: float = 0.010, sides: int = 6) -> None:
    """One cell's local loop: a closed triangle of hose over the three grooves."""
    pts = inset(f, loop_inset(), h)
    for i in range(3):
        batch.cylinder(pts[i], pts[(i + 1) % 3], r, colour, sides)
    for p in pts:
        batch.sphere(p, r * 1.15, colour, 3, 6)


# ----------------------------------------------------------------------
# Seams, rim and rings
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def edges() -> tuple[tuple, tuple]:
    """Every panel-to-panel seam (both ends, both faces) and every rim edge."""
    model, scale, shift = sc._world()
    topo = model.topology
    v = np.asarray(topo.vertices, dtype=float) * scale + shift
    by_edge: dict[tuple, list[int]] = {}
    for i, f in enumerate(topo.faces):
        vs = f.vertices
        for j in range(3):
            by_edge.setdefault(tuple(sorted((vs[j], vs[(j + 1) % 3]))), []).append(i)
    seams, rim = [], []
    for key, owners in by_edge.items():
        a, b = v[key[0]], v[key[1]]
        (seams if len(owners) == 2 else rim).append((a, b, *owners))
    return tuple(seams), tuple(rim)


def seam_line(a, b, i: int, j: int, h: float) -> tuple[np.ndarray, np.ndarray]:
    fs = faces()
    n = fs[i].normal + fs[j].normal
    n /= np.linalg.norm(n)
    return a + n * h, b + n * h


def seam_runs(batch: TriangleBatch, h: float, colour, r: float = 0.016, sides: int = 6,
              keep=None) -> list[tuple[np.ndarray, np.ndarray]]:
    """A layer's global channel: a run along every seam at the layer's height."""
    out = []
    for a, b, i, j in edges()[0]:
        if keep is not None and not keep(i, j):
            continue
        p, q = seam_line(a, b, i, j, h)
        batch.cylinder(p, q, r, colour, sides)
        out.append((p, q))
    return out


def rim_corners() -> list[np.ndarray]:
    pts = []
    for a, b, _i in edges()[1]:
        for p in (a, b):
            if not any(np.allclose(p, q) for q in pts):
                pts.append(p)
    c = cw.landmarks().dome_centre
    return sorted(pts, key=lambda p: math.atan2(p[1] - c[1], p[0] - c[0]))


def rim_ring(batch: TriangleBatch, out: float, lift: float, colour, r: float = 0.03) -> list[np.ndarray]:
    """A ring round the rim, ``out`` beyond the corners and ``lift`` above them."""
    c = cw.landmarks().dome_centre
    pts = []
    for p in rim_corners():
        d = np.array([p[0] - c[0], p[1] - c[1], 0.0])
        d /= np.linalg.norm(d)
        pts.append(p + d * out + np.array([0.0, 0.0, lift]))
    for k in range(len(pts)):
        batch.cylinder(pts[k], pts[(k + 1) % len(pts)], r, colour, 8)
        batch.sphere(pts[k], r * 1.4, colour, 3, 8)
    return pts


@lru_cache(maxsize=1)
def ring_heights() -> tuple[float, ...]:
    """Heights of the interior vertex rings above the sphere's centre (rim and apex left out)."""
    model, scale, _shift = sc._world()
    zs = sorted({round(float(p[2]) * scale, 3) for p in model.topology.vertices})
    return tuple(zs[1:-1])


def ring(batch: TriangleBatch, z: float, out: float, colour, r: float = 0.022, steps: int = 72) -> list:
    """A horizontal channel round the dome at height ``z``, ``out`` beyond the frame."""
    m = cw.landmarks()
    rad = math.sqrt(max(m.dome_r ** 2 - z * z, 0.0)) + out
    pts = [m.dome_centre + np.array([rad * math.cos(t), rad * math.sin(t), z])
           for t in np.linspace(0, math.tau, steps, endpoint=False)]
    for k in range(steps):
        batch.cylinder(pts[k], pts[(k + 1) % steps], r, colour, 6)
    return pts


# ----------------------------------------------------------------------
# The stack: where each layer is drawn
# ----------------------------------------------------------------------

ROOM = tuple(l.key for l in cwall.LAYERS if l.side == "room")[::-1]     # nearest the core first
WEATHER = tuple(l.key for l in cwall.LAYERS if l.side == "weather")       # nearest the core first


def height(key: str, f: Face, explode: float) -> float:
    """A layer's height above a face's plane, from assembled (0) to exploded (1).

    Assembled spacing is drawn a little thicker than the 8 mm a real layer
    takes, so each can be seen; exploded, they stand well apart."""
    e = max(0.0, min(1.0, explode))
    if key in WEATHER:
        i = WEATHER.index(key)
        return f.top + 0.008 + i * (0.014 + 0.17 * e) + 0.06 * e
    if key in ROOM:
        j = ROOM.index(key)
        return f.bottom - 0.010 - j * (0.014 + 0.16 * e) - 0.06 * e
    return (f.top + f.bottom) / 2


def shell(batch: TriangleBatch, key: str, explode: float, alpha: float | None = None,
          only=None, d: float = 0.05) -> None:
    """One layer, all its cells, as see-through tiles (draw into the transparent batch)."""
    col = colour(key, alpha)
    for f in standing():
        if key == "airbag" and not f.lower:
            continue
        if only is not None and not only(f):
            continue
        tile(batch, f, height(key, f, explode), col, d)


def label_point(key: str, explode: float, toward=None) -> np.ndarray:
    """Where to pin a layer's label: on its cell that faces the camera side best."""
    toward = np.array(cw.HERO_EYE) if toward is None else np.asarray(toward, float)
    cands = [f for f in standing() if (key != "airbag" or f.lower)]
    m = cw.landmarks()
    d = toward - m.dome_centre
    d /= np.linalg.norm(d)
    f = max(cands, key=lambda f: float(np.dot(f.normal, d)) - abs(f.slope_deg - 55) / 400)
    return f.centre + f.normal * height(key, f, explode)


def facing(k: int = 1, toward=None, lower: bool | None = None) -> list[Face]:
    """The standing faces that look most toward ``toward`` (the hero camera by default)."""
    toward = np.array(cw.HERO_EYE) if toward is None else np.asarray(toward, float)
    m = cw.landmarks()
    d = toward - m.dome_centre
    d /= np.linalg.norm(d)
    cands = [f for f in standing() if lower is None or f.lower == lower]
    return sorted(cands, key=lambda f: -float(np.dot(f.normal, d)))[:k]


# ----------------------------------------------------------------------
# Static pieces: built once per process
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def static(name: str) -> TriangleBatch:
    b = TriangleBatch()
    if name == "loops_frame":
        for f in standing():
            loop(b, f, f.top + 0.006, LOOP, 0.013)
    elif name == "seams_frame":
        # The ridge stands about 1.5 cm above the members' tops (r sin(fold/2) x 0.39 r
        # in from the groove line), so the run is lifted clear of it.
        seam_runs(b, float(np.mean([f.top for f in standing()])) + 0.045, GLOW, 0.022)
    elif name == "rings":
        for z in ring_heights():
            ring(b, z, 0.24, (0.95, 0.80, 0.35, 1.0), 0.024)
        rim_ring(b, 0.26, 0.04, (0.95, 0.80, 0.35, 1.0), 0.028)
    elif name == "rim_vacuum":
        rim_ring(b, 0.30, 0.10, colour("vacuum", 1.0), 0.045)
    elif name == "cage":
        _cage(b)
    elif name == "plants":
        _plants(b)
    elif name == "tank":
        _tank(b)
    elif name == "posts":
        m = cw.landmarks()
        for k in range(4):
            a = math.radians(45 + 90 * k)
            out = np.array([math.cos(a), math.sin(a), 0.0])
            p = np.array([m.deck_centre[0], m.deck_centre[1], 0.0]) + out * (m.deck_r + 0.45)
            b.cylinder(p, p + np.array([0.0, 0.0, 4.2]), 0.07, (0.25, 0.25, 0.27, 1.0), 10)
            # A collar that slides on the post, braced to the pad's edge.
            collar = p + np.array([0.0, 0.0, m.deck_centre[2]])
            b.cylinder(collar - np.array([0.0, 0.0, 0.12]), collar + np.array([0.0, 0.0, 0.12]), 0.12,
                       (0.45, 0.45, 0.48, 1.0), 12)
            edge = np.array([m.deck_centre[0], m.deck_centre[1], m.deck_centre[2]]) + out * (m.deck_r - 0.15)
            b.cylinder(collar, edge, 0.05, (0.45, 0.45, 0.48, 1.0), 8)
    elif name == "nodes":
        for f in standing():
            b.box(f.centre + f.normal * (f.bottom - 0.05), (0.07, 0.07, 0.04), colour("bus", 1.0))
    elif name == "valves_every":
        _valves(b, every=True)
    elif name == "valves_band":
        _valves(b, every=False)
    elif name == "bench_grooves":
        _bench_grooves(b)
    else:
        raise KeyError(name)
    return b


def paint_static(app, name: str, subject: bool = False) -> None:
    app.static_layer(f"cellwall:{name}", lambda: static(name), _subject(name) if subject else None)


def _subject(name: str) -> list[np.ndarray]:
    m = cw.landmarks()
    r = m.dome_r + 0.5
    return [m.dome_centre + [x * r, y * r, 0] for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))] + [
        m.apex + [0, 0, 0.5]]


def _cage(b: TriangleBatch, n: int = 4) -> None:
    """Bonded mesh over every cell, drawn as a lattice, and the bond along every seam."""
    for f in standing():
        h = height("cage", f, 0.0) + 0.02
        a, bb, c = inset(f, 0.02, h)
        lines = [(a, bb), (bb, c), (c, a)]
        for k in range(1, n):
            t = k / n
            lines.append((a + (bb - a) * t, a + (c - a) * t))
            lines.append((bb + (a - bb) * t, bb + (c - bb) * t))
            lines.append((c + (a - c) * t, c + (bb - c) * t))
        for p, q in lines:
            b.cylinder(p, q, 0.0065, (0.86, 0.88, 0.93, 1.0), 5)
    level = float(np.mean([height("cage", f, 0.0) for f in standing()]))
    seam_runs(b, level, COPPER, 0.012, 6)


def _plants(b: TriangleBatch) -> None:
    """Soil and plants on the faces flat enough to hold it; felt pockets on the rest."""
    rng = np.random.default_rng(21)
    limit = cwall.C["plant_max_slope_deg"]
    for f in standing():
        h = height("living", f, 0.0)
        if f.slope_deg <= limit:
            tile(b, f, h, SOIL, 0.04, both=True)
            a, bb, c = inset(f, 0.10, h + 0.01)
            for _ in range(70):
                u, w = rng.random(), rng.random()
                if u + w > 1:
                    u, w = 1 - u, 1 - w
                p = a + (bb - a) * u + (c - a) * w
                tall = rng.uniform(0.06, 0.22)
                col = LEAF if rng.random() < 0.6 else LEAF_LIGHT
                b.cone(p, p + f.normal * tall + np.array([0, 0, tall * 0.4]), tall * 0.35, col, 6)
        else:
            a, bb, c = inset(f, 0.14, h)
            for u in np.linspace(0.12, 0.88, 4):
                for w in np.linspace(0.12, 0.88, 4):
                    if u + w > 0.95:
                        continue
                    p = a + (bb - a) * u + (c - a) * w
                    b.sphere(p + f.normal * 0.03, 0.045, LEAF if (u + w) % 0.3 > 0.15 else LEAF_LIGHT, 3, 6)


def tank_spot() -> np.ndarray:
    """On the grass beside the pad, off the hero camera's line to the dome."""
    m = cw.landmarks()
    hero = math.atan2(cw.HERO_EYE[1] - m.dome_centre[1], cw.HERO_EYE[0] - m.dome_centre[0])
    a = hero + math.radians(52)
    r = m.deck_r + 0.75
    return np.array([m.dome_centre[0] + r * math.cos(a), m.dome_centre[1] + r * math.sin(a), 0.0])


TANK_D = 0.75     # scene dressing: the tank's diameter; its height follows from its volume


def tank_height() -> float:
    litres = cwall.borrowed()["tank_gal"] * cwall.L_PER_GAL
    return litres / 1000 / (math.pi * (TANK_D / 2) ** 2)


def _tank(b: TriangleBatch) -> None:
    p = tank_spot()
    h = tank_height()
    b.cylinder(p, p + np.array([0.0, 0.0, h]), TANK_D / 2, TANK, 24)
    b.cylinder(p + np.array([0.0, 0.0, h]), p + np.array([0.0, 0.0, h + 0.04]), TANK_D / 2 * 0.4,
               (0.15, 0.18, 0.2, 1.0), 16)
    co2 = p + np.array([0.0, 0.0, 0.0]) + _sideways(p) * 0.65
    b.cylinder(co2, co2 + np.array([0.0, 0.0, 0.85]), 0.11, CO2, 16)
    b.sphere(co2 + np.array([0.0, 0.0, 0.85]), 0.11, CO2, 4, 12)
    # The feed to the rim: tank to the nearest rim corner.
    q = min(rim_corners(), key=lambda c: np.linalg.norm(c[:2] - p[:2]))
    b.cylinder(p + np.array([0.0, 0.0, 0.25]), q + np.array([0.0, 0.0, 0.02]), 0.03, (0.2, 0.45, 0.8, 1.0), 8)


def _sideways(p: np.ndarray) -> np.ndarray:
    m = cw.landmarks()
    d = np.array([p[0] - m.dome_centre[0], p[1] - m.dome_centre[1], 0.0])
    d /= np.linalg.norm(d)
    return np.array([-d[1], d[0], 0.0])


def co2_top() -> np.ndarray:
    p = tank_spot()
    return p + _sideways(p) * 0.65 + np.array([0.0, 0.0, 0.95])


def tank_top() -> np.ndarray:
    return tank_spot() + np.array([0.0, 0.0, tank_height()])


def _valves(b: TriangleBatch, every: bool) -> None:
    """Every cell's pair of valves -- or one pair per band per layer, at the rim."""
    netted = [l.key for l in cwall.LAYERS if l.kind in ("sheet", "hose")]
    if every:
        for key in netted:
            col = colour(key, 1.0)
            for f in standing():
                if key == "airbag" and not f.lower:
                    continue
                low = min(f.corners, key=lambda p: p[2])
                base = f.incentre + (low - f.incentre) * 0.55 + f.normal * height(key, f, 0.6)
                for s in (-1, 1):
                    side = np.cross(f.normal, low - f.incentre)
                    side /= np.linalg.norm(side)
                    b.box(base + side * 0.07 * s, (0.065, 0.065, 0.065), col)
        return
    comp = cwall.complexity()
    corners = rim_corners()
    m = cw.landmarks()
    total = comp["valves_by_band"]
    for k in range(total):
        p = corners[k % len(corners)]
        d = np.array([p[0] - m.dome_centre[0], p[1] - m.dome_centre[1], 0.0])
        d /= np.linalg.norm(d)
        layer = k // len(corners)
        b.box(p + d * (0.28 + 0.11 * (layer % 3)) + np.array([0.0, 0.0, 0.10 + 0.12 * (layer // 3)]),
              (0.09, 0.09, 0.09), colour(netted[layer % len(netted)], 1.0))


# ----------------------------------------------------------------------
# The bench: a length of wall in section
# ----------------------------------------------------------------------

def bench_frame() -> sc.Frame:
    return sc.Frame(sc.BENCH_A, sc.tight())


def bench_side(side: int) -> dict:
    """One member of the specimen, in section inches: its pith, the outward
    normal of the panel it belongs to, the groove at the middle of its round
    face, and the direction along the panel away from the seam."""
    t = sc.tight()
    r = t.depth_in
    h = math.radians(t.gap_deg / 2)
    f2 = math.radians(t.fold_deg / 2)
    pith = np.array([side * r * math.sin(h), -r * math.cos(h)])
    nrm = np.array([side * math.sin(f2), math.cos(f2)])
    along = np.array([side * math.cos(f2), -math.sin(f2)])
    mid = pith + r * nrm
    # Where the panel plane crosses the seam's centre line, x = 0.
    s0 = -mid[0] / along[0]
    return {"pith": pith, "normal": nrm, "along": along, "groove": mid, "s0": s0, "r": r}


def _bench_grooves(b: TriangleBatch) -> None:
    """The C-channel in both members: a dark slot on the round face, the hose
    in it, and the notch where it meets the end grain at the camera's end."""
    frame = bench_frame()
    w, d = cwall.C["groove_w_in"], cwall.C["groove_d_in"]
    hose_r = (cwall.C["local_hose_id_mm"] / 2 + 1.5) / 25.4
    for side in (-1, 1):
        g = bench_side(side)
        mid, n, t = g["groove"], g["normal"], g["along"]
        p0, p1 = mid - t * w / 2 + n * 0.02, mid + t * w / 2 + n * 0.02
        q0, q1 = p0 - n * d, p1 - n * d
        a0, a1 = 0.004, sc.SPECIMEN_LEN - 0.004
        # The slot's mouth on the round face, dark, a hair proud of the wood.
        b.quad(frame.at(*p0, a0), frame.at(*p1, a0), frame.at(*p1, a1), frame.at(*p0, a1), DARK)
        # The notch in the end grain at the near end, drawn just in front of it.
        for along in (-0.0015, sc.SPECIMEN_LEN + 0.0015):
            b.quad(frame.at(*p0, along), frame.at(*p1, along), frame.at(*q1, along), frame.at(*q0, along), DARK)
        # The hose drawn riding high in its slot, so it reads from outside the wood.
        c = mid - n * 0.15
        b.cylinder(frame.at(*c, -0.004), frame.at(*c, sc.SPECIMEN_LEN + 0.004), hose_r * M, LOOP, 14)


def groove_hose_centre(side: int) -> np.ndarray:
    """The local hose's centre line at the near end, in section inches."""
    g = bench_side(side)
    return g["groove"] - g["normal"] * 0.15


def pack_key(od_in: float, count: int) -> list[np.ndarray]:
    """``count`` round runs of ``od_in`` inside the tight key, widest end first,
    on a hexagonal grid -- for the picture; the count is cell_wall.seam_room's."""
    poly = sc.inner(sc.tight())
    edges = list(zip(poly, poly[1:] + poly[:1]))

    def clearance(x: float, y: float) -> float:
        best = float("inf")
        for (x0, y0), (x1, y1) in edges:
            ex, ey = x1 - x0, y1 - y0
            d = abs(ex * (y - y0) - ey * (x - x0)) / math.hypot(ex, ey)
            best = min(best, d)
        return best

    def inside(x: float, y: float) -> bool:
        sign = None
        for (x0, y0), (x1, y1) in edges:
            s = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
            if sign is None:
                sign = s > 0
            elif (s > 0) != sign:
                return False
        return True

    ys = [p[1] for p in poly]
    xs = sorted(np.arange(-1.6, 1.6 + 1e-9, 0.02), key=abs)
    out: list[np.ndarray] = []
    for y in np.arange(min(ys) + od_in / 2 + 0.02, max(ys), 0.02):
        for x in xs:
            if (inside(x, y) and clearance(x, y) >= od_in / 2 + 0.01
                    and all(math.hypot(x - q[0], y - q[1]) >= od_in + 0.02 for q in out)):
                out.append(np.array([x, y]))
                if len(out) == count:
                    return out
    return out


def bench_slab(batch: TriangleBatch, side: int, off_in: float, thick_in: float, col,
               reach_in: float = 9.0, a0: float = 0.0, a1: float = sc.SPECIMEN_LEN) -> None:
    """A layer over one panel of the specimen: a board parallel to that panel,
    ``off_in`` out from where the sheathing bears (negative is the room side)."""
    frame = bench_frame()
    g = bench_side(side)
    mid, n, t, s0 = g["groove"], g["normal"], g["along"], g["s0"]
    pts = [mid + t * s + n * o for s, o in ((s0, off_in), (s0 + reach_in, off_in),
                                             (s0 + reach_in, off_in + thick_in), (s0, off_in + thick_in))]
    corners = [frame.at(*p, a0) for p in pts] + [frame.at(*p, a1) for p in pts]
    for i, j, k, l in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        batch.quad(corners[i], corners[j], corners[k], corners[l], col)
        batch.quad(corners[i], corners[l], corners[k], corners[j], col)


def bench_point(side: int, off_in: float, s_in: float = 0.0, along: float = 0.0) -> np.ndarray:
    """A point over one panel of the specimen, in the world."""
    g = bench_side(side)
    p = g["groove"] + g["along"] * s_in + g["normal"] * off_in
    return bench_frame().at(*p, along)


def bench_seam_point(off_in: float, along: float = 0.0) -> np.ndarray:
    """A point over the seam line, ``off_in`` above where the two panels' sheathing meets."""
    left, right = bench_side(-1), bench_side(1)
    pl = left["groove"] + left["along"] * left["s0"] + left["normal"] * off_in
    pr = right["groove"] + right["along"] * right["s0"] + right["normal"] * off_in
    return bench_frame().at(*((pl + pr) / 2), along)


def validate_cell_wall_scene() -> None:
    fs = faces()
    assert len(fs) == 40 and len(standing()) == 40 - len(cw.missing_faces())
    for f in fs:
        assert f.top > 0.1 > f.bottom, "members stand out from the face plane by about a radius"
        assert 0 <= f.slope_deg <= 90
    seams, rim = edges()
    assert len(seams) == 55 and len(rim) == 10, (len(seams), len(rim))
    assert len(rim_corners()) == 10 and len(ring_heights()) == 3
    assert sum(f.lower for f in fs) == cwall.complexity()["lower_faces"], "scene and facts pick the same faces"
    # The groove lies under the sheathing: the panel plane touches the round face there.
    for side in (-1, 1):
        g = bench_side(side)
        assert abs(np.linalg.norm(g["groove"] - g["pith"]) - g["r"]) < 1e-9
        assert abs(g["s0"]) < g["r"]
    assert 0.05 < loop_inset() < member_width()
    for key in WEATHER:
        assert height(key, fs[0], 0) > fs[0].top and height(key, fs[0], 1) > height(key, fs[0], 0)
    for key in ROOM:
        assert height(key, fs[0], 0) < fs[0].bottom
    assert tank_height() > 0.5
    for name in ("loops_frame", "rings", "rim_vacuum", "tank", "posts", "nodes", "bench_grooves"):
        assert static(name).vertices, name
