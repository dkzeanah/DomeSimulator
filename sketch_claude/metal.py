"""All-steel geodesic domes: a wood stove and a water tank, every plate cut from the sphere.

Each face of the geodesic is one steel plate. Its outer face lies on the face's chord plane and
its inner face one plate thickness in; each edge is bevelled on the plane that halves the fold
to the plate beside it, so two plates meet edge to edge in a V ready to weld (the bevel on each
side is half the fold). Where a cut leaves a stepped base, flat vertical skirt plates close it
down to the floor. A flat cap closes the top round the flue (the stove) or the manway (the tank),
set exactly where the opening fits with a weld land round it.

The stove is sized by its **largest member** -- the longest plate edge, 18 in as asked -- or by
its diameter; the tank by its diameter. Every figure comes from the plates. The inputs that
cannot (plate, flue and pipe sizes, clearances, densities, allowable stress) are in the design's
declared table with their reasons, and the tank's stress figures are labelled as estimates.

Units: metres, z up, the room's floor (or the ground) at z = 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from scipy.spatial import ConvexHull, HalfspaceIntersection

from two_v_demo import panel_method as pm

from . import kinds as K
from . import model as M
from . import solids as S
from .model import FT, IN, Declared, Model, Piece

UP = np.array([0.0, 0.0, 1.0])
CUT_TARGET = {"3/4": 0.75, "1/2": 0.5, "5/8": 0.625}
METAL_CUTS = ((1, "3/4"), (2, "1/2"), (3, "1/2"), (3, "5/8"), (4, "1/2"))

M.MATERIALS.update({
    "steel_plate": {"color": "#6d737b", "label": "Steel plate"},
    "steel_dark": {"color": "#43464b", "label": "Steel"},
    "firebrick": {"color": "#d8b088", "label": "Firebrick"},
    "water": {"color": "#3d8fd1", "opacity": 0.4, "label": "Water"},
    "clearance": {"color": "#e0563a", "opacity": 0.18, "label": "Clearance to combustibles"},
    "gasket": {"color": "#2b2b2b", "label": "Rope gasket"},
    "floorboards": {"color": "#b98b5e", "label": "Wood floor"},
    "wall": {"color": "#efe7d8", "label": "Wall (combustible)"},
    "hearthstone": {"color": "#9a938c", "label": "Hearth"},
})

# Fixed declared inputs: what no geometry supplies. The spec's own choices are added per design.
COMMON = {
    "steel_kg_m3": Declared(7850.0, "kg/m3", "mild steel"),
    "sheet_w_m": Declared(4 * FT, "m", "a plate sheet: 4 ft wide"),
    "sheet_l_m": Declared(8 * FT, "m", "a plate sheet: 8 ft long"),
    "gap_m": Declared(0.25 * IN, "m", "room between parts on a sheet: the plasma kerf and a little more"),
    "land_m": Declared(1.0 * IN, "m", "flat cap plate left round the flue collar or manway, for its weld"),
}
STOVE_FIXED = {
    "collar_m": Declared(3.0 * IN, "m", "flue collar height, to take a crimped stove pipe"),
    "leg_m": Declared(1.5 * IN, "m", "legs: 1-1/2 in square tube"),
    "leg_wall_m": Declared(0.125 * IN, "m", "leg tube wall: 1/8 in"),
    "brick_m": Declared(1.25 * IN, "m", "firebrick splits on the floor plate, so the fire never sits on bare steel"),
    "brick_face_m2": Declared(4.5 * 9 * IN * IN, "m2", "one firebrick split: 4-1/2 x 9 in"),
    "clear_m": Declared(36.0 * IN, "m", "NFPA 211: an unlisted solid-fuel room heater stands 36 in from anything combustible, "
                                        "unless a listed shield reduces it", "rule"),
    "hearth_front_m": Declared(18.0 * IN, "m", "non-combustible hearth in front of the door: a common allowance; your code may differ"),
    "hearth_side_m": Declared(8.0 * IN, "m", "hearth beyond the sides and back: a common allowance; your code may differ"),
    "hearth_t_m": Declared(0.75 * IN, "m", "hearth: stone or tile on cement board"),
    "gasket_m": Declared(0.625 * IN, "m", "rope gasket round the door"),
}
TANK_FIXED = {
    "water_kg_m3": Declared(1000.0, "kg/m3", "fresh water"),
    "g": Declared(9.81, "m/s2", "gravity"),
    "fy_mpa": Declared(250.0, "MPa", "yield of A36 / S275 mild steel plate"),
    "allow_frac": Declared(0.6, "", "working stress as a fraction of yield: a common allowance", "estimate"),
    "weld_eff": Declared(0.7, "", "joint efficiency of single-sided butt welds that are not X-rayed", "estimate"),
    "pad_t_m": Declared(4.0 * IN, "m", "concrete pad under the floor"),
    "pad_margin_m": Declared(6.0 * IN, "m", "pad past the tank's footprint"),
    "overflow_m": Declared(3.0 * IN, "m", "overflow below the cap: the air the full tank keeps"),
    "outlet_m": Declared(4.0 * IN, "m", "outlet above the floor: sediment stays below it"),
    "collar_m": Declared(4.0 * IN, "m", "manway collar height"),
    "inlet_od_m": Declared(1.900 * IN, "m", "inlet: 1-1/2 in pipe (1.900 in outside)"),
    "outlet_od_m": Declared(1.900 * IN, "m", "outlet: 1-1/2 in pipe (1.900 in outside)"),
    "overflow_od_m": Declared(2.375 * IN, "m", "overflow: 2 in pipe (2.375 in outside), bigger than the inlet so it can keep up"),
    "drain_od_m": Declared(1.315 * IN, "m", "drain: 1 in pipe (1.315 in outside)"),
    "stub_m": Declared(6.0 * IN, "m", "pipe stub outside the shell, threaded for a valve"),
}


def D(table: dict, key: str) -> float:
    return float(table[key].value)


# ----------------------------------------------------------------------
# Specs and forms
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class StoveSpec:
    kind: str = "stove"
    frequency: int = 2
    cut: str = "1/2"
    size_by: str = "edge"              # edge: the longest plate edge sets the size | diameter
    edge_m: float = 18 * IN            # the largest member
    diameter_m: float = 34 * IN
    plate_m: float = 0.25 * IN
    flue_m: float = 6 * IN
    legs_m: float = 6 * IN
    hearth: bool = True
    room: bool = True
    people: bool = True

    @property
    def title(self) -> str:
        return f"{self.frequency}V steel dome wood stove"


@dataclass(frozen=True)
class TankSpec:
    kind: str = "tank"
    frequency: int = 2
    cut: str = "1/2"
    diameter_m: float = 8 * FT
    plate_m: float = 0.1875 * IN
    floor_m: float = 0.25 * IN
    manway_m: float = 20 * IN
    water: bool = True
    people: bool = True

    @property
    def title(self) -> str:
        return f"{self.frequency}V steel dome water tank"


STOVE_FORM = [
    {"key": "fc", "label": "Geodesic", "type": "cut", "options": K._cut_options(METAL_CUTS)},
    {"key": "size_by", "label": "Size by", "type": "select", "options": [["edge", "Largest member (longest plate edge)"], ["diameter", "Diameter"]]},
    {"key": "edge_m", "label": "Largest member", "type": "len", "min": 0.15, "max": 1.2, "step": 0.0016},
    {"key": "diameter_m", "label": "Diameter", "type": "len", "min": 0.3, "max": 3.0, "step": 0.01},
    {"key": "plate_m", "label": "Plate", "type": "len", "min": 0.002, "max": 0.02, "step": 0.0005},
    {"key": "flue_m", "label": "Flue", "type": "len", "min": 0.075, "max": 0.25, "step": 0.0127},
    {"key": "legs_m", "label": "Legs", "type": "len", "min": 0.0, "max": 0.6, "step": 0.0127},
    {"key": "hearth", "label": "Hearth pad", "type": "check"}, {"key": "room", "label": "Room", "type": "check"},
    {"key": "people", "label": "Person", "type": "check"},
]
TANK_FORM = [
    {"key": "fc", "label": "Geodesic", "type": "cut", "options": K._cut_options(METAL_CUTS)},
    {"key": "diameter_m", "label": "Diameter", "type": "len", "min": 0.6, "max": 8.0, "step": 0.05},
    {"key": "plate_m", "label": "Shell plate", "type": "len", "min": 0.002, "max": 0.02, "step": 0.0005},
    {"key": "floor_m", "label": "Floor plate", "type": "len", "min": 0.002, "max": 0.025, "step": 0.0005},
    {"key": "manway_m", "label": "Manway", "type": "len", "min": 0.3, "max": 0.8, "step": 0.0127},
    {"key": "water", "label": "Water", "type": "check"}, {"key": "people", "label": "Person", "type": "check"},
]


# ----------------------------------------------------------------------
# The shell: plates, skirts, cap and floor, from one truncated sphere
# ----------------------------------------------------------------------

def truncation(frequency: int, cut: str) -> pm.Truncation:
    """The cut nearest the asked-for height fraction that leaves one closed base loop."""
    target = CUT_TARGET.get(cut, 0.5)
    sp = pm.three_v_sphere(int(frequency))
    best = None
    for lv in sp.levels[1:-1]:
        t = pm.truncate(sp, lv)
        if not t.base:
            continue
        uses: dict[int, int] = {}
        for e in t.base:
            uses[e.a] = uses.get(e.a, 0) + 1
            uses[e.b] = uses.get(e.b, 0) + 1
        if any(v != 2 for v in uses.values()):
            continue
        score = abs(t.height_fraction - target)
        if best is None or score < best[0] - 1e-9:
            best = (score, t)
    if best is None:
        raise ValueError(f"no {frequency}V {cut} cut with one closed base")
    return best[1]


@dataclass
class Plate:
    pid: str
    kind: str                     # shell | skirt | cap | floor
    poly: list                    # the outer outline as cut (3-D)
    normal: np.ndarray
    mesh: S.Mesh
    bevels: list = field(default_factory=list)    # each outline edge's bevel from square, degrees
    ring: int = 0
    face: int = -1
    mark: str = ""
    full: list | None = None      # the uncut chord triangle (for nesting a clipped plate)


def _bevel(normal, a, b, centre, cut_n) -> float:
    e = S.unit(np.asarray(b) - np.asarray(a))
    s = S.unit(np.cross(e, normal))
    if s @ ((np.asarray(a) + np.asarray(b)) / 2 - centre) < 0:
        s = -s
    return math.degrees(math.acos(min(1.0, abs(float(np.asarray(cut_n) @ s)))))


def _orient(n, point, inside):
    """A half-space (n, c) through ``point``, turned so ``inside`` is in it."""
    n = S.unit(n)
    c = float(n @ point)
    if n @ inside > c:
        n, c = -n, -c
    return n, c


def _section(planes, z: float, big: float) -> list[np.ndarray]:
    """The outline of the convex shell where the plane z = const cuts it."""
    poly = [np.array([-big, -big, z]), np.array([big, -big, z]), np.array([big, big, z]), np.array([-big, big, z])]
    sides = [None] * 4
    for n, c in planes:
        if abs(n[0]) < 1e-12 and abs(n[1]) < 1e-12:
            continue
        poly, sides = S.clip(poly, sides, n, c, "s")
        if len(poly) < 3:
            return []
    return poly


def _interior(planes, lo: float, hi: float):
    """The convex room inside the plates between two heights: its volume and its hull."""
    hs = [list(n) + [-c] for n, c in planes] + [[0, 0, -1, lo], [0, 0, 1, -hi]]
    hs = np.array(hs, float)
    point = np.array([0.0, 0.0, (lo + hi) / 2])
    inter = HalfspaceIntersection(hs, point)
    hull = ConvexHull(inter.intersections)
    return float(hull.volume), hull


@dataclass
class Shell:
    trunc: pm.Truncation
    R: float
    z0: float
    z_cap: float
    tp: float
    V: np.ndarray
    plates: list
    skirts: list
    cap: Plate | None
    floor_poly: list
    outer: list                    # every outer plane (n, c)
    inner: list                    # every inner plane (n, c), plate thickness in
    edge_faces: dict
    r_max: float
    r_base: float
    longest: float
    weld_m: float
    apex: np.ndarray
    faces: dict
    normals: dict


def build_shell(frequency: int, cut: str, R: float | None, edge: float | None, diameter: float | None,
                tp: float, z0: float, open_r: float, land: float) -> Shell:
    t = truncation(frequency, cut)
    sp = t.sphere
    kept = list(t.faces)
    F = {f: tuple(int(x) for x in sp.faces[f]) for f in kept}

    def edges_of(tri):
        return [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]

    longest_u = max(float(np.linalg.norm(sp.vertices[a] - sp.vertices[b])) for f in kept for a, b in edges_of(F[f]))
    if R is None:
        R = edge / longest_u if edge else (diameter / 2) / t.base_radius
    V = sp.vertices * R + np.array([0.0, 0.0, z0 - R * t.cut_level])
    nrm = {f: S.unit(np.cross(V[F[f][1]] - V[F[f][0]], V[F[f][2]] - V[F[f][0]])) for f in kept}
    off = {f: float(nrm[f] @ V[F[f][0]]) for f in kept}
    cen = {f: V[list(F[f])].mean(axis=0) for f in kept}
    edge_faces: dict[tuple[int, int], list[int]] = {}
    for f in kept:
        for a, b in edges_of(F[f]):
            edge_faces.setdefault((min(a, b), max(a, b)), []).append(f)
    base_edges = [e for e, fs in edge_faces.items() if len(fs) == 1]

    # skirts: a vertical plate under every base edge that is not on the floor
    skirt_of: dict[tuple[int, int], dict] = {}
    for e in base_edges:
        a, b = e
        if V[a][2] < z0 + 1e-9 and V[b][2] < z0 + 1e-9:
            continue
        mid = (V[a] + V[b]) / 2
        ns = S.unit(np.cross(V[b] - V[a], UP))
        if ns @ np.array([mid[0], mid[1], 0.0]) < 0:
            ns = -ns
        skirt_of[e] = {"n": ns, "c": float(ns @ V[a])}
    skirt_at: dict[int, list] = {}
    for e in skirt_of:
        for v in e:
            skirt_at.setdefault(v, []).append(e)

    outer = [(nrm[f], off[f]) for f in kept] + [(s["n"], s["c"]) for s in skirt_of.values()]
    inner = [(nrm[f], off[f] - tp) for f in kept] + [(s["n"], s["c"] - tp) for s in skirt_of.values()]

    # the cap: as low as the opening needs, never lower
    top = max({v for f in kept for v in F[f]}, key=lambda v: V[v][2])
    apex_faces = [f for f in kept if top in F[f]]
    z_cap = min((off[f] - open_r * math.hypot(nrm[f][0], nrm[f][1])) / nrm[f][2] for f in apex_faces)
    if z_cap < z0 + 0.35 * (V[top][2] - z0):
        raise ValueError("the opening is too big for a dome this size: make it smaller or the dome bigger")

    plates: list[Plate] = []
    weld = 0.0
    for f in kept:
        tri = [V[v] for v in F[f]]
        if min(p[2] for p in tri) >= z_cap - 1e-9:
            continue                                   # wholly above the cap: the cap replaces it
        n_, c_ = nrm[f], off[f]
        H = [(n_, c_), (-n_, -(c_ - tp))]
        cuts = []
        for a, b in edges_of(F[f]):
            key = (min(a, b), max(a, b))
            fs = edge_faces[key]
            if len(fs) == 2:
                other = fs[0] if fs[1] == f else fs[1]
                h = _orient(n_ - nrm[other], V[a], cen[f])
            elif key in skirt_of:
                h = _orient(n_ - skirt_of[key]["n"], V[a], cen[f])
            else:
                h = (-UP, -z0)                         # sits on the floor plate
            H.append(h)
            cuts.append(((a, b), h))
        clipped = max(p[2] for p in tri) > z_cap + 1e-9
        if clipped:
            H.append((UP, z_cap))
        mesh = S.solid(H)
        poly, sides = list(tri), [h for _e, h in cuts]
        if clipped:
            poly, sides = S.clip(poly, sides, UP, z_cap, (UP, z_cap))
        bev = [_bevel(n_, poly[i], poly[(i + 1) % len(poly)], cen[f], sides[i][0]) for i in range(len(poly))]
        plates.append(Plate("", "shell", poly, n_, mesh, bev, face=f, full=tri if clipped else None))

    skirts: list[Plate] = []
    for e, s in skirt_of.items():
        a, b = e
        f0 = edge_faces[e][0]
        pts = [V[a], V[b]]
        bf = np.array([V[b][0], V[b][1], z0])
        af = np.array([V[a][0], V[a][1], z0])
        if V[b][2] > z0 + 1e-9:
            pts.append(bf)
        if V[a][2] > z0 + 1e-9:
            pts.append(af)
        ctr = np.mean(pts, axis=0)
        ns, cs = s["n"], s["c"]
        H = [(ns, cs), (-ns, -(cs - tp)), _orient(ns - nrm[f0], V[a], ctr), (-UP, -z0)]
        sides = [H[2]]
        for v, foot in ((b, bf), (a, af)):
            if V[v][2] <= z0 + 1e-9:
                continue
            nb = [o for o in skirt_at.get(v, []) if o != e]
            h = _orient(ns - skirt_of[nb[0]]["n"], V[v], ctr) if nb else _orient(np.cross(UP, ns), V[v], ctr)
            H.append(h)
        mesh = S.solid(H)
        bev = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            if i == 0:
                cut_n = H[2][0]
            elif abs(p[2] - z0) < 1e-9 and abs(q[2] - z0) < 1e-9:
                cut_n = -UP
            else:
                cut_n = S.unit(np.cross(UP, ns))
            bev.append(_bevel(ns, p, q, ctr, cut_n))
        skirts.append(Plate("", "skirt", pts, ns, mesh, bev))

    big = 3 * R
    cap_poly = _section(outer, z_cap, big)
    floor_poly = _section(outer, z0, big)

    # welds: every seam between two plates once, every plate to the floor, the cap round its edge
    for (a, b), fs in edge_faces.items():
        L = float(np.linalg.norm(V[a] - V[b]))
        lo = min(V[a][2], V[b][2])
        if lo >= z_cap - 1e-9:
            continue
        hi = max(V[a][2], V[b][2])
        if hi > z_cap:                                 # the part below the cap
            L *= (z_cap - lo) / (hi - lo)
        weld += L                                       # plate-plate, plate-skirt or plate-floor
    for e in skirt_of:                                  # each skirt's foot, and its raised sides (shared ones once)
        a, b = e
        weld += math.hypot(V[b][0] - V[a][0], V[b][1] - V[a][1])
        for v in (a, b):
            rise = V[v][2] - z0
            if rise > 1e-9:
                weld += rise / (2 if len(skirt_at.get(v, [])) == 2 else 1)
    weld += sum(float(np.linalg.norm(cap_poly[(i + 1) % len(cap_poly)] - cap_poly[i])) for i in range(len(cap_poly)))

    allv = V[sorted({v for f in kept for v in F[f]})]
    r_max = float(np.max(np.hypot(allv[:, 0], allv[:, 1])))
    base_vs = sorted({v for e in base_edges for v in e})
    r_base = float(np.mean([math.hypot(V[v][0], V[v][1]) for v in base_vs]))
    longest = max(float(np.linalg.norm(V[a] - V[b])) for a, b in edge_faces)
    cap = None
    if cap_poly:
        cap = Plate("CAP", "cap", cap_poly, UP, S.Mesh(np.zeros((0, 3)), np.zeros((0, 3), int), np.zeros((0, 2), int)))
    return Shell(t, R, z0, z_cap, tp, V, plates, skirts, cap, floor_poly, outer, inner, edge_faces, r_max, r_base,
                 longest, weld, V[top], F, nrm)


# ----------------------------------------------------------------------
# Parts: a ring with a hole, tubes, floor pieces, marks
# ----------------------------------------------------------------------

def ring_plate(poly, r_hole: float, z: float, t: float, centre=(0.0, 0.0)) -> S.Mesh:
    """A flat plate with a round hole: one convex sliver per piece of its outline, merged."""
    cx, cy = centre
    parts = []
    k = len(poly)
    for i in range(k):
        p, q = poly[i], poly[(i + 1) % k]
        for j in range(4):
            a = p + (q - p) * (j / 4)
            b = p + (q - p) * ((j + 1) / 4)
            ha = np.array([cx, cy, z]) + r_hole * S.unit(np.array([a[0] - cx, a[1] - cy, 0.0]))
            hb = np.array([cx, cy, z]) + r_hole * S.unit(np.array([b[0] - cx, b[1] - cy, 0.0]))
            quad = [np.array([a[0], a[1], z]), np.array([b[0], b[1], z]), hb, ha]
            parts.append(S.prism(quad, UP, t))
    mm = S.merge(parts)
    # ink the outline and the hole, top and bottom: in every sliver those are its edges 0-1 and 2-3, both faces
    ink = [(k * 8 + a, k * 8 + b) for k in range(len(parts)) for a, b in ((0, 1), (2, 3), (4, 5), (6, 7))]
    return S.Mesh(mm.verts, mm.tris, np.array(ink, dtype=int), mm.polys)


def hull_mesh(hull) -> S.Mesh:
    """A convex hull's triangles, every one wound outward (scipy leaves them either way)."""
    P = hull.points
    tris = hull.simplices.astype(int).copy()
    c = P[hull.vertices].mean(axis=0)
    nrm = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    flip = np.einsum("ij,ij->i", nrm, P[tris[:, 0]] - c) < 0
    tris[flip] = tris[flip][:, ::-1]
    return S.Mesh(P, tris, K.feature_edges(P, tris, 10.0))


def tube(p0, p1, r_out: float, r_in: float, seg: int = 24) -> S.Mesh:
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = S.unit(p1 - p0)
    a = S.unit(np.cross(ax, UP if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])))
    b = np.cross(ax, a)
    ang = [math.tau * i / seg for i in range(seg)]
    ring = lambda c, r: [c + r * (math.cos(t) * a + math.sin(t) * b) for t in ang]
    ob, ot, ib, it = ring(p0, r_out), ring(p1, r_out), ring(p0, r_in), ring(p1, r_in)
    pts = ob + ot + ib + it
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([i, j, seg + j, seg + i])                                  # outside
        faces.append([2 * seg + j, 2 * seg + i, 3 * seg + i, 3 * seg + j])      # bore
        faces.append([seg + i, seg + j, 3 * seg + j, 3 * seg + i])              # top rim
        faces.append([j, i, 2 * seg + i, 2 * seg + j])                          # bottom rim
    ink = [list(range(seg)), list(range(seg, 2 * seg)), list(range(2 * seg, 3 * seg)), list(range(3 * seg, 4 * seg))]
    return S._poly_mesh(pts, faces, ink=ink)


def annulus(r0: float, r1: float, z: float, seg: int = 72) -> S.Mesh:
    pts, faces = [], []
    for i in range(seg):
        t = math.tau * i / seg
        pts += [np.array([r0 * math.cos(t), r0 * math.sin(t), z]), np.array([r1 * math.cos(t), r1 * math.sin(t), z])]
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([2 * i, 2 * j, 2 * j + 1, 2 * i + 1])
    return S._poly_mesh(pts, faces, ink=[[2 * i for i in range(seg)], [2 * i + 1 for i in range(seg)]])


def floor_pieces(poly, sheet_w: float, sheet_l: float) -> list[list[np.ndarray]]:
    """The floor cut into pieces that each fit one sheet: bands across x, then along y."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    nx = max(1, math.ceil((max(xs) - min(xs)) / sheet_w - 1e-9))
    ny = max(1, math.ceil((max(ys) - min(ys)) / sheet_l - 1e-9))
    x0 = (min(xs) + max(xs)) / 2 - nx * sheet_w / 2
    y0 = (min(ys) + max(ys)) / 2 - ny * sheet_l / 2
    out = []
    for i in range(nx):
        for j in range(ny):
            P, sd = list(poly), [None] * len(poly)
            for nvec, c in (((1, 0, 0), x0 + (i + 1) * sheet_w), ((-1, 0, 0), -(x0 + i * sheet_w)),
                            ((0, 1, 0), y0 + (j + 1) * sheet_l), ((0, -1, 0), -(y0 + j * sheet_l))):
                P, sd = S.clip(P, sd, np.array(nvec, float), c, "cut")
                if len(P) < 3:
                    break
            if len(P) >= 3 and S.poly_area(P) > 1e-6:
                out.append(P)
    return out


def mark_classes(plates: list[Plate], prefix: str) -> dict[str, list[Plate]]:
    """Plates with the same outline and the same bevels are one shape: P1 the most common."""
    groups: dict[tuple, list[Plate]] = {}
    for p in plates:
        P = p.poly
        lens = tuple(sorted(round(float(np.linalg.norm(P[(i + 1) % len(P)] - P[i])), 4) for i in range(len(P))))
        bev = tuple(sorted(round(b, 1) for b in p.bevels))
        groups.setdefault((len(P), lens, bev), []).append(p)
    ordered = sorted(groups.values(), key=lambda g: (-len(g), -max(np.linalg.norm(g[0].poly[i] - g[0].poly[i - 1]) for i in range(len(g[0].poly)))))
    out = {}
    for i, g in enumerate(ordered, 1):
        mk = f"{prefix}{i}"
        for p in g:
            p.mark = mk
        out[mk] = g
    return out


def plate_card(mark: str, group: list[Plate], steel: float, note: str = "", title: str | None = None) -> dict:
    p = group[0]
    pts = K.flat(p.poly, p.normal)
    k = len(pts)
    cx, cy = sum(x for x, _ in pts) / k, sum(y for _, y in pts) / k
    size = max(max(x for x, _ in pts) - min(x for x, _ in pts), max(y for _, y in pts) - min(y for _, y in pts))
    # the bevels, in the same order as the flattened outline
    P = p.poly
    i0 = max(range(k), key=lambda i: float(np.linalg.norm(P[(i + 1) % k] - P[i])))
    bev = p.bevels[i0:] + p.bevels[:i0]
    notes = []
    for i in range(k):
        a, b = pts[i], pts[(i + 1) % k]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = mx - cx, my - cy
        ln = math.hypot(dx, dy) or 1.0
        notes.append({"at": [mx + dx / ln * size * 0.16, my + dy / ln * size * 0.16], "text": f"bevel {K.deg(bev[i])}"})
    lens = [math.hypot(pts[(i + 1) % k][0] - pts[i][0], pts[(i + 1) % k][1] - pts[i][1]) for i in range(k)]
    area = S.poly_area(p.poly)
    rows = [["Edges", " / ".join(K.m(x) for x in lens)], ["Corners", " / ".join(K.deg(a) for a in K.corner_angles(pts))],
            ["Weld bevels", " / ".join(K.deg(b) for b in bev)], ["Area", K.m2(area)],
            ["Each", K.kg(S.volume(p.mesh) * steel) if len(p.mesh.tris) else K.kg(0)]]
    if note:
        rows.append(["Note", note])
    return K.card(mark, title or f"Plate {mark}", len(group), rows, K.drawing(pts, notes=notes), [q.pid for q in group],
                  group={"shell": "Shell plates", "skirt": "Skirt plates", "cap": "Cap", "floor": "Floor"}[p.kind], kind="plate")


def nest_plates(plates: list[Plate], sheet_w: float, sheet_l: float, gap: float) -> list[dict]:
    """The shell plates on sheets. Each is nested by its uncut chord triangle, and drawn there as the
    plate it really is (a bottom-ring plate the dome's cut clipped is a four-sided piece inside its
    triangle), with each edge's weld bevel in the same order as its outline."""
    tris, real = [], {}
    for i, p in enumerate(plates):
        P = p.full or p.poly
        if len(P) != 3:
            continue
        a, b, c = (np.asarray(x, float) for x in P)
        sides = [(float(np.linalg.norm(b - a)), a, b, c), (float(np.linalg.norm(c - b)), b, c, a), (float(np.linalg.norm(a - c)), c, a, b)]
        base, p0, p1, p2 = max(sides, key=lambda s: s[0])
        # each corner of the real outline in the triangle's own (barycentric) terms
        T = np.column_stack([p0 - p2, p1 - p2])
        bary = []
        for q in p.poly:
            l01, *_ = np.linalg.lstsq(T, np.asarray(q, float) - p2, rcond=None)
            bary.append((float(l01[0]), float(l01[1]), 1.0 - float(l01[0]) - float(l01[1])))
        real[(p.mark, i)] = (bary, list(p.bevels))
        tris.append(((p.mark, i), base, float(np.linalg.norm(p2 - p0)), float(np.linalg.norm(p2 - p1))))
    tris.sort(key=lambda t: (-t[1], t[0]))
    sheets = M.nest_triangles(tris, sheet_w, sheet_l, gap)
    out = []
    for sh in sheets:
        parts = []
        for (mark, i), pts in sh:
            bary, bev = real[(mark, i)]
            q0, q1, q2 = (np.asarray(x, float) for x in pts)
            poly = [list(l0 * q0 + l1 * q1 + l2 * q2) for l0, l1, l2 in bary]
            parts.append({"mark": mark, "pts": [[float(x), float(y)] for x, y in poly], "bevels": [float(x) for x in bev],
                          "chord": [list(map(float, q)) for q in pts]})
        out.append({"w": sheet_l, "h": sheet_w, "parts": parts})
    return out


def surface_point(planes, z: float, az_deg: float):
    d = np.array([math.cos(math.radians(az_deg)), math.sin(math.radians(az_deg)), 0.0])
    p0 = np.array([0.0, 0.0, z])
    best = math.inf
    for n_, c in planes:
        nd = float(n_ @ d)
        if nd > 1e-9:
            t = (c - float(n_ @ p0)) / nd
            if t > 0:
                best = min(best, t)
    return p0 + d * best, d


def _piece(pid, name, tag, mat, mesh, info=None, group="", explode=(0, 0, 0)) -> Piece:
    return Piece(pid, name, tag, mat, mesh, info or {}, 0, group, tuple(float(x) for x in explode))


def _plate_pieces(sh: Shell, steel: float, exclude: set[int] = frozenset()) -> list[Piece]:
    out = []
    zc = [float(np.mean([q[2] for q in p.poly])) for p in sh.plates]
    rings = K.ring_rank(zc, 3)
    order = sorted(range(len(sh.plates)), key=lambda i: (rings[i], math.atan2(sh.plates[i].poly[0][1], sh.plates[i].poly[0][0])))
    for k, i in enumerate(order):
        p = sh.plates[i]
        p.ring = rings[i]
        p.pid = f"P{k + 1:03d}"
    for k, p in enumerate(sh.skirts):
        p.pid = f"K{k + 1:03d}"
    return out


def _info(p: Plate, steel: float) -> dict:
    P = p.poly
    lens = [float(np.linalg.norm(P[(i + 1) % len(P)] - P[i])) for i in range(len(P))]
    return {"mark": p.mark, "ring": p.ring + 1, "longest_edge_m": max(lens), "shortest_edge_m": min(lens),
            "bevel_lo_deg": min(p.bevels), "bevel_hi_deg": max(p.bevels), "area_m2": S.poly_area(P),
            "mass_kg": S.volume(p.mesh) * steel if len(p.mesh.tris) else 0.0}


def _scenes(extra_off=()) -> list[dict]:
    return [
        {"name": "Exterior", "dir": [0.55, -1, 0.42], "style": "shaded", "off": list(extra_off), "explode": 0, "step": 999, "door": 30},
        {"name": "Plates", "dir": [0.6, -1, 0.5], "style": "sketch", "off": ["site", "person", "fittings", "water", "clear"], "explode": 0, "step": 999, "door": 0, "colour": True},
        {"name": "Exploded", "dir": [0.55, -1, 0.5], "style": "sketch", "off": ["site", "person", "water", "clear"], "explode": 60, "step": 999, "door": 0},
        {"name": "Cut-away", "dir": [0.2, -1, 0.35], "style": "sketch", "off": ["person"], "explode": 0, "step": 999, "door": 0, "section": {"axis": "y", "t": 0.5}},
        {"name": "Top", "dir": [0.0001, -0.0001, 1], "style": "sketch", "off": ["person", "water"], "explode": 0, "step": 999, "door": 0, "colour": True},
        {"name": "Front", "dir": [0, -1, 0.001], "style": "hidden", "off": ["person", "site", "clear", "water"], "explode": 0, "step": 999, "door": 0},
    ]


# ----------------------------------------------------------------------
# The wood stove
# ----------------------------------------------------------------------

@lru_cache(maxsize=16)
def build_stove(spec: StoveSpec) -> Model:
    T = {**COMMON, **STOVE_FIXED}
    steel = D(T, "steel_kg_m3")
    tp = spec.plate_m
    hearth_t = D(T, "hearth_t_m") if spec.hearth else 0.0
    z0 = hearth_t + spec.legs_m + tp
    sh = build_shell(spec.frequency, spec.cut, None, spec.edge_m if spec.size_by == "edge" else None,
                     spec.diameter_m if spec.size_by != "edge" else None, tp, z0, spec.flue_m / 2 + D(T, "land_m"), D(T, "land_m"))
    _plate_pieces(sh, steel)
    classes = mark_classes(sh.plates, "P")
    skirt_classes = mark_classes(sh.skirts, "K") if sh.skirts else {}

    # the door: a plate of the lowest ring that stands on the floor, the one nearest the front (-y)
    low = [p for p in sh.plates if sum(1 for q in p.poly if abs(q[2] - z0) < 1e-9) >= 2]
    pool = low or [p for p in sh.plates if p.ring == 0]
    door = min(pool, key=lambda p: abs(((math.degrees(math.atan2(np.mean([q[1] for q in p.poly]), np.mean([q[0] for q in p.poly]))) + 90 + 180) % 360) - 180))
    pieces: list[Piece] = []
    for p in sh.plates:
        if p is door:
            continue
        pieces.append(_piece(p.pid, f"Plate {p.mark} ({p.pid})", "shell", "steel_plate", p.mesh, _info(p, steel), p.pid, p.normal * 0.6))
    for p in sh.skirts:
        pieces.append(_piece(p.pid, f"Skirt {p.mark} ({p.pid})", "shell", "steel_plate", p.mesh, _info(p, steel), p.pid, p.normal * 0.5))

    # door leaf, hinges, gasket, latch
    P = door.poly
    on_floor = [i for i in range(3) if abs(P[i][2] - z0) < 1e-9]
    sides = [(i, (i + 1) % 3) for i in range(3) if not (i in on_floor and (i + 1) % 3 in on_floor)]
    hinge = min(sides, key=lambda e: (P[e[0]][0] + P[e[1]][0]) / 2)
    ha, hb = P[hinge[0]], P[hinge[1]]
    dc = np.mean(P, axis=0)
    door_parts = [_piece("door-leaf", f"Door (plate {door.mark})", "door", "steel_plate", door.mesh, _info(door, steel) | {"door": True}, "door-leaf", door.normal * 0.8)]
    out_n = door.normal
    for k, f in enumerate((0.22, 0.78)):
        c = ha + (hb - ha) * f + out_n * (tp + 0.25 * IN)
        ax = S.unit(hb - ha)
        door_parts.append(_piece(f"door-hinge-{k}", "Hinge", "door", "steel_dark", S.cylinder(c - ax * IN, c + ax * IN, 0.3 * IN, 12), {}, "door-leaf", out_n * 0.8))
    gk = D(T, "gasket_m")
    for i in range(3):
        a, b = P[i], P[(i + 1) % 3]
        a2 = a + (dc - a) * 0.08 - out_n * (tp + gk / 2)
        b2 = b + (dc - b) * 0.08 - out_n * (tp + gk / 2)
        door_parts.append(_piece(f"door-gasket-{i}", "Rope gasket", "door", "gasket", S.cylinder(a2, b2, gk / 2, 10), {}, "door-leaf", out_n * 0.8))
    free = [q for j, q in enumerate(P) if j not in hinge][0]
    lp = free + (dc - free) * 0.35 + out_n * tp
    door_parts.append(_piece("door-latch", "Latch handle", "door", "steel_dark", S.cylinder(lp, lp + out_n * 2.5 * IN, 0.35 * IN, 12), {}, "door-leaf", out_n * 0.8))
    pieces += door_parts
    base_len = [float(np.linalg.norm(P[(i + 1) % 3] - P[i])) for i in range(3) if i in on_floor and (i + 1) % 3 in on_floor]
    door_w = base_len[0] if base_len else max(float(np.linalg.norm(P[(i + 1) % 3] - P[i])) for i in range(3))
    door_h = 2 * S.poly_area(P) / door_w
    door_perimeter = sum(float(np.linalg.norm(P[(i + 1) % 3] - P[i])) for i in range(3))
    sh.weld_m -= door_perimeter                                                          # the door is hinged, not welded

    # cap with the flue hole, collar, pipe
    cap_mesh = ring_plate(sh.cap.poly, spec.flue_m / 2, sh.z_cap, tp)
    sh.cap.mesh = cap_mesh
    cap_mass = S.poly_area(sh.cap.poly) * tp * steel - math.pi * (spec.flue_m / 2) ** 2 * tp * steel
    pieces.append(_piece("cap", "Top cap", "cap", "steel_plate", cap_mesh, {"mark": "CAP", "area_m2": S.poly_area(sh.cap.poly), "mass_kg": cap_mass}, "cap", (0, 0, 0.8)))
    zc0 = sh.z_cap + tp
    collar_h = D(T, "collar_m")
    pieces.append(_piece("collar", "Flue collar", "cap", "steel_dark", tube((0, 0, zc0), (0, 0, zc0 + collar_h), spec.flue_m / 2, spec.flue_m / 2 - 0.12 * IN), {"diameter_m": spec.flue_m, "height_m": collar_h}, "cap", (0, 0, 1.0)))
    pipe = _piece("pipe", "Stove pipe (to your chimney)", "fittings", "steel", tube((0, 0, zc0 + collar_h * 0.4), (0, 0, zc0 + collar_h + 1.3), spec.flue_m / 2 - 0.02 * IN, spec.flue_m / 2 - 0.06 * IN), {}, "pipe", (0, 0, 1.2))

    # floor plate on legs, firebrick on it
    sw, sl, gap = D(T, "sheet_w_m"), D(T, "sheet_l_m"), D(T, "gap_m")
    fl = floor_pieces(sh.floor_poly, sw, sl)
    floor_plates = []
    for k, poly in enumerate(fl):
        mesh = S.prism(poly, -UP, tp)
        fp = Plate(f"F{k + 1}", "floor", poly, -UP, mesh, [0.0] * len(poly), mark=f"F{k + 1}")
        floor_plates.append(fp)
        pieces.append(_piece(fp.pid, f"Floor plate {fp.pid}", "floor", "steel_plate", mesh, {"mark": fp.mark, "area_m2": S.poly_area(poly), "mass_kg": S.poly_area(poly) * tp * steel}, "floor", (0, 0, -0.5)))
    leg, wall = D(T, "leg_m"), D(T, "leg_wall_m")
    fpoly = sh.floor_poly
    idx = list(range(0, len(fpoly), 2)) if len(fpoly) >= 8 else list(range(len(fpoly)))
    legs = []
    for k, i in enumerate(idx):
        q = fpoly[i]
        r = math.hypot(q[0], q[1])
        x, y = q[0] * (r - 2 * leg) / r, q[1] * (r - 2 * leg) / r
        h0, h1 = hearth_t, z0 - tp
        if h1 - h0 > 1e-3:
            legs.append(_piece(f"leg-{k}", "Leg", "floor", "steel_dark", S.box((x, y, (h0 + h1) / 2), (leg, leg, h1 - h0), math.degrees(math.atan2(y, x))),
                               {"length_m": h1 - h0}, "legs", (x * 0.3, y * 0.3, -0.6)))
    pieces += legs
    brick_t = D(T, "brick_m")
    inner_floor = _section(sh.inner, z0, 3 * sh.R)
    bricks = math.ceil(S.poly_area(inner_floor) / D(T, "brick_face_m2"))
    brick = _piece("firebrick", "Firebrick floor", "brick", "firebrick", S.prism(inner_floor, UP, brick_t), {"area_m2": S.poly_area(inner_floor), "splits": bricks}, "brick", (0, 0, 0.3))
    pieces.append(brick)

    # the room: hearth pad, the clearance on the floor, a wall at the clearance, a person
    clear = D(T, "clear_m")
    ctx = []
    hearth = None
    if spec.hearth:
        fr, sd = D(T, "hearth_front_m"), D(T, "hearth_side_m")
        x0, x1, y0, y1 = -(sh.r_max + sd), sh.r_max + sd, -(sh.r_max + fr), sh.r_max + sd
        hearth = _piece("hearth", "Hearth pad", "floor", "hearthstone", S.box(((x0 + x1) / 2, (y0 + y1) / 2, hearth_t / 2), (x1 - x0, y1 - y0, hearth_t)),
                        {"width_m": x1 - x0, "depth_m": y1 - y0}, "hearth", (0, 0, -0.9))
    zone = _piece("clearance", "Clearance to combustibles", "clear", "clearance", annulus(sh.r_max, sh.r_max + clear, hearth_t + 0.002), {"clearance_m": clear}, "clearance")
    if hearth is not None:
        pieces += [hearth, zone]
    else:
        ctx.append(zone)
    if spec.room:
        size = 2 * (sh.r_max + clear) + 1.6
        ctx.append(_piece("room-floor", "Wood floor", "site", "floorboards", S.box((0, 0.3, -0.01), (size, size, 0.02)), {}, "site"))
        ctx.append(_piece("room-wall", "Wall (combustible), at the clearance", "site", "wall",
                          S.box((0, sh.r_max + clear + 0.06, 1.2), (size, 0.12, 2.4)), {"distance_m": clear}, "site"))
    if spec.people:
        ctx += M._person((-(sh.r_max + 0.6), 0.35, 0.0), -90.0)
    for p in ctx:
        if p.tag == "person":
            p.group = "person"
    K.context(ctx)

    # the build
    book = K.Book()
    shell_pieces = [p for p in pieces if p.tag == "shell"]
    rings = sorted({p.info["ring"] for p in shell_pieces})
    book.prep("Before you start: what this stove is",
              f"This is a home-built, unlisted stove. Many building codes and most insurers want a listed appliance indoors, "
              f"so ask your inspector before it goes in a house. Unlisted, it has to stand {K.m(clear)} from anything that burns, "
              "on a non-combustible hearth, with its pipe to a proper chimney, and with a smoke and carbon monoxide alarm in the room.",
              [], ["Your building inspector", "Smoke and CO alarm"], phase="Plan")
    nsheets = nest_plates(sh.plates, sw, sl, gap)
    book.prep("Cut the plates",
              f"Cut {len(sh.plates)} shell plates in {len(classes)} shapes" + (f", {len(sh.skirts)} skirt plates" if sh.skirts else "")
              + f", the cap and {len(fl)} floor piece(s) from {K.m(tp)} plate. The shell nests on {len(nsheets)} sheet(s) (the nesting is on the "
              f"cut list). The longest edge on the stove is {K.m(sh.longest)}. Scribe each plate's mark on its inside face as it comes off the table.",
              [p for p in pieces if p.tag in ("shell", "cap", "floor") or p.id == "door-leaf"], ["Plasma cutter or oxy-fuel torch", "Straightedge and soapstone", "Grinder"],
              "Lay three plates of one shape on top of each other: their edges agree within 1/32 in.")
    bev = [b for p in sh.plates + sh.skirts for b in p.bevels]
    book.prep("Bevel the edges for welding",
              f"Grind each edge to the bevel on its plate card ({K.deg(min(bev))} to {K.deg(max(bev))} from square). Two plates then "
              "meet in a V that a weld fills from outside. The bottom edges are bevelled to sit flat on the floor plate.",
              shell_pieces, ["Angle grinder with flap disc", "Angle gauge"], "Hold two neighbouring plates together: the outside faces meet at a sharp line.")
    if hearth is not None:
        book.add("Lay the hearth", f"Lay the hearth pad: {K.m(hearth.info['width_m'])} wide, {K.m(hearth.info['depth_m'])} deep, "
                 "stone or tile on cement board, centred where the stove will stand and reaching furthest in front of the door.",
                 [hearth, zone], ["Level", "Trowel", "Tile cutter"], f"The clearance ring ({K.m(clear)}) is clear of everything that burns.")
    book.add("Weld the floor and legs",
             f"Weld the {len(fl)} floor piece(s) into one plate, then weld a leg under every other corner ({len(legs)} legs, {K.m(spec.legs_m)} long).",
             [p for p in pieces if p.group in ("floor", "legs")], ["Welder", "Clamps", "Square"], "The floor plate sits flat on the hearth without rocking.")
    for r in rings:
        ring_ps = [p for p in shell_pieces if p.info["ring"] == r]
        first = r == rings[0]
        book.add(f"Tack ring {r} of {len(rings)}",
                 ("Stand the bottom ring on the floor plate, leaving the door's plate out. " if first else "Set the next ring on the one below. ")
                 + f"Tack each of these {len(ring_ps)} plates at its corners only; do not run beads yet, so the shell can still be nudged true.",
                 ring_ps, ["Welder", "Magnetic squares", "Clamps"],
                 "Measure across the shell in two directions at this height: they agree within 1/16 in.")
    book.add("Fit the cap and flue collar",
             f"The cap closes the top round a {K.m(spec.flue_m)} collar, with {K.m(D(T, 'land_m'))} of flat plate round the hole for the weld. "
             f"Tack it on, then weld the collar ({K.m(collar_h)} tall) into the hole.",
             [p for p in pieces if p.tag == "cap"], ["Welder", "Hole saw or torch"], "The collar stands plumb.")
    book.prep("Weld it out",
              f"Now run the beads: {K.m(sh.weld_m)} of weld in all. Weld short lengths on opposite sides in turn so the shell does not pull. "
              "Grind the outside smooth if you will paint it.", shell_pieces, ["Welder", "Grinder", "Wire brush"],
              "No daylight through any seam when a lamp is inside.")
    book.add("Hang the door",
             f"The door is the plate that was left out: {K.m(door_w)} wide at the floor, {K.m(door_h)} tall. Weld two hinges on its "
             f"left edge, a latch on the other side, and glue the {K.m(gk)} rope gasket round its inside face.",
             door_parts, ["Welder", "Gasket cement"], "Close the door on a strip of paper: it holds the paper all the way round.")
    book.add("Line the floor with firebrick",
             f"Lay about {bricks} firebrick splits ({K.m(brick_t)} thick) on the floor plate, cut to fit round the edge.",
             [brick], ["Brick saw or chisel"], "No steel shows on the floor.")
    book.add("Pipe it to the chimney",
             "Fit the stove pipe into the collar, crimped end down, and run it to a listed chimney. Screw every joint with three sheet-metal screws.",
             [pipe], ["Drill", "Sheet-metal screws"], "The pipe rises the whole way to the chimney: no downhill runs.")
    book.prep("First fires",
              "Burn three or four small fires to cure the paint and drive off oil before a full load. Open a window: the first smoke smells.",
              [], ["Kindling", "Stove paint"], phase="Finish")
    pieces.append(pipe)
    pieces += ctx

    longest_member = max(float(np.linalg.norm(p.poly[(i + 1) % len(p.poly)] - p.poly[i])) for p in sh.plates for i in range(len(p.poly)))
    firebox, _hull = _interior(sh.inner, z0 + brick_t, sh.z_cap)
    mass = sum(S.volume(p.mesh) for p in sh.plates + sh.skirts) * steel + cap_mass + \
        sum(S.poly_area(p) * tp * steel for p in fl) + len(legs) * (z0 - tp - hearth_t) * (leg ** 2 - (leg - 2 * wall) ** 2) * steel
    cards = [plate_card(mk, g, steel, "one of these is the door" if door in g else "") for mk, g in classes.items()]
    cards += [plate_card(mk, g, steel) for mk, g in skirt_classes.items()]
    cap_pts = K.flat(sh.cap.poly, UP, longest_on_x=False)
    cards.append(K.card("CAP", "Top cap", 1, [["Outline", " / ".join(K.m(float(np.linalg.norm(sh.cap.poly[(i + 1) % len(sh.cap.poly)] - sh.cap.poly[i]))) for i in range(len(sh.cap.poly)))],
                                               ["Flue hole", K.m(spec.flue_m)], ["Each", K.kg(cap_mass)]],
                        K.drawing(cap_pts, holes=[{"c": [sum(x for x, _ in cap_pts) / len(cap_pts), sum(y for _, y in cap_pts) / len(cap_pts)], "r": spec.flue_m / 2}]),
                        ["cap"], "Cap", "plate"))
    for fp in floor_plates:
        cards.append(K.card(fp.mark, f"Floor plate {fp.mark}", 1, [["Area", K.m2(S.poly_area(fp.poly))], ["Each", K.kg(S.poly_area(fp.poly) * tp * steel)]],
                            K.drawing([[q[0], q[1]] for q in fp.poly], angles=False), [fp.pid], "Floor", "plate"))
    if legs:
        cards.append(K.card("LEG", "Leg", len(legs), [["Length", K.m(legs[0].info["length_m"])], ["Tube", f"{K.m(leg)} square, {K.m(wall)} wall"]],
                            K.drawing([(0, 0), (legs[0].info["length_m"], 0), (legs[0].info["length_m"], leg), (0, leg)], angles=False), [p.id for p in legs], "Legs", "tube"))
    summary = [
        ["Largest member", K.m(longest_member)], ["Across the floor", K.m(2 * sh.r_base)],
        ["Height to the cap", K.m(sh.z_cap + tp)],
        ["Plates", f"{len(sh.plates)} shell" + (f" + {len(sh.skirts)} skirt" if sh.skirts else "") + f" + cap + {len(fl)} floor"],
        ["Plate shapes", K.n(len(classes) + len(skirt_classes))], ["Steel", K.kg(mass)], ["Weld", K.m(sh.weld_m)],
        ["Firebox", K.litres(firebox * 1000)], ["Door opening", f"{K.m(door_w)} wide, {K.m(door_h)} tall"], ["Flue", K.m(spec.flue_m)],
        ["Keep clear", f"{K.m(clear)} to anything that burns"], ["Sheets of plate", K.n(len(nsheets) + len(fl))],
    ]
    declared = {"edge_m" if spec.size_by == "edge" else "diameter_m": Declared(spec.edge_m if spec.size_by == "edge" else spec.diameter_m, "m",
                "the stove's size, as chosen: " + ("the longest plate edge (its largest member)" if spec.size_by == "edge" else "its diameter")),
                "plate_m": Declared(tp, "m", "firebox plate, as chosen: 1/4 in mild steel resists warping in a hot fire"),
                "flue_m": Declared(spec.flue_m, "m", "flue, as chosen: match your pipe and chimney"),
                "legs_m": Declared(spec.legs_m, "m", "legs under the floor plate, as chosen"), **T}
    warnings = ["Unlisted appliance: check your building code and insurer before installing it indoors.",
                f"Keep {36:.0f} in clear of combustibles all round (NFPA 211 for unlisted heaters) and fit a CO alarm."]
    tables = {
        "title": spec.title, "summary": summary, "cards": cards, "sheets": nsheets, "steps": book.steps,
        "declared": K.declared_rows(declared), "warnings": warnings,
        "tags": [["shell", "Shell plates"], ["cap", "Cap and collar"], ["door", "Door"], ["floor", "Floor, legs, hearth"], ["brick", "Firebrick"],
                 ["fittings", "Stove pipe"], ["clear", "Clearance zone"], ["site", "Room"], ["person", "Person"]],
        "scenes": _scenes(["clear"]) + [{"name": "Clearances", "dir": [0.0001, -0.0001, 1], "style": "sketch", "off": ["person"], "explode": 0, "step": 999, "door": 0}],
        "door": {"hinge_a": ha.tolist(), "hinge_b": hb.tolist(), "max": 110},
        "stove": {"R": sh.R, "z0": z0, "z_cap": sh.z_cap, "r_max": sh.r_max, "longest_m": longest_member, "firebox_l": firebox * 1000,
                  "mass_kg": mass, "weld_m": sh.weld_m, "door_w_m": door_w, "door_h_m": door_h, "plates": len(sh.plates),
                  "classes": len(classes), "bricks": bricks, "plate_m": tp, "shell_sheets": len(nsheets), "floor_pieces": len(fl),
                  "door_perimeter_m": door_perimeter, "hinges": 2},
    }
    model = Model(spec, pieces, tables, {"door": [float(dc[0]), float(dc[1]), float(dc[2])], "centre": [0.0, 0.0, (z0 + sh.z_cap) / 2]})
    return model


# ----------------------------------------------------------------------
# The water tank
# ----------------------------------------------------------------------

@lru_cache(maxsize=16)
def build_tank(spec: TankSpec) -> Model:
    T = {**COMMON, **TANK_FIXED}
    steel, water_d, g = D(T, "steel_kg_m3"), D(T, "water_kg_m3"), D(T, "g")
    tp, tf = spec.plate_m, spec.floor_m
    pad_t = D(T, "pad_t_m")
    z0 = pad_t + tf
    sh = build_shell(spec.frequency, spec.cut, None, None, spec.diameter_m, tp, z0, spec.manway_m / 2 + D(T, "land_m"), D(T, "land_m"))
    _plate_pieces(sh, steel)
    classes = mark_classes(sh.plates, "P")
    skirt_classes = mark_classes(sh.skirts, "K") if sh.skirts else {}
    pieces: list[Piece] = []
    for p in sh.plates:
        pieces.append(_piece(p.pid, f"Plate {p.mark} ({p.pid})", "shell", "steel_plate", p.mesh, _info(p, steel), p.pid, p.normal * 0.8))
    for p in sh.skirts:
        pieces.append(_piece(p.pid, f"Skirt {p.mark} ({p.pid})", "shell", "steel_plate", p.mesh, _info(p, steel), p.pid, p.normal * 0.7))

    cap_mesh = ring_plate(sh.cap.poly, spec.manway_m / 2, sh.z_cap, tp)
    sh.cap.mesh = cap_mesh
    cap_mass = (S.poly_area(sh.cap.poly) - math.pi * (spec.manway_m / 2) ** 2) * tp * steel
    pieces.append(_piece("cap", "Top cap", "cap", "steel_plate", cap_mesh, {"mark": "CAP", "area_m2": S.poly_area(sh.cap.poly), "mass_kg": cap_mass}, "cap", (0, 0, 1.0)))
    zc0 = sh.z_cap + tp
    ch = D(T, "collar_m")
    pieces.append(_piece("manway", "Manway collar", "cap", "steel_dark", tube((0, 0, zc0), (0, 0, zc0 + ch), spec.manway_m / 2, spec.manway_m / 2 - tp), {"diameter_m": spec.manway_m}, "cap", (0, 0, 1.2)))
    lid = _piece("hatch", "Hatch lid", "fittings", "steel_dark", S.cylinder((0, 0, zc0 + ch), (0, 0, zc0 + ch + tp), spec.manway_m / 2 + IN, 32), {"diameter_m": spec.manway_m + 2 * IN}, "hatch", (0, 0, 1.6))

    sw, sl, gap = D(T, "sheet_w_m"), D(T, "sheet_l_m"), D(T, "gap_m")
    fl = floor_pieces(sh.floor_poly, sw, sl)
    floor_plates = []
    for k, poly in enumerate(fl):
        fp = Plate(f"F{k + 1}", "floor", poly, -UP, S.prism(poly, -UP, tf), [0.0] * len(poly), mark=f"F{k + 1}")
        floor_plates.append(fp)
        pieces.append(_piece(fp.pid, f"Floor plate {fp.pid}", "floor", "steel_plate", fp.mesh, {"mark": fp.mark, "area_m2": S.poly_area(poly), "mass_kg": S.poly_area(poly) * tf * steel}, "floor", (0, 0, -0.6)))
    margin = D(T, "pad_margin_m")
    pad_poly = [np.array([q[0] * (sh.r_max + margin) / sh.r_max, q[1] * (sh.r_max + margin) / sh.r_max, 0.0]) for q in sh.floor_poly]
    pad = _piece("pad", "Concrete pad", "base", "concrete", S.prism(pad_poly, UP, pad_t), {"area_m2": S.poly_area(pad_poly), "thickness_m": pad_t}, "pad", (0, 0, -1.0))
    pieces.append(pad)

    # water to the overflow, pipes where the shell is
    level = sh.z_cap - D(T, "overflow_m")
    planes = sh.outer
    pipes = []
    od = {k: D(T, f"{k}_od_m") for k in ("inlet", "outlet", "overflow", "drain")}
    stub = D(T, "stub_m")
    spots = {"inlet": (90.0, sh.z_cap - od["inlet"] * 1.5 - IN), "overflow": (0.0, level + od["overflow"] / 2),
             "outlet": (180.0, z0 + D(T, "outlet_m") + od["outlet"] / 2), "drain": (225.0, z0 + od["drain"] / 2 + 0.5 * IN)}
    for name, (az, z) in spots.items():
        p, d = surface_point(planes, z, az)
        pipes.append(_piece(f"pipe-{name}", f"{name.capitalize()} pipe", "fittings", "steel_dark", tube(p - d * tp * 2, p + d * stub, od[name] / 2, od[name] / 2 - 0.15 * IN),
                            {"diameter_m": od[name], "height_m": z - z0, "az_deg": az}, f"pipe-{name}", d * 0.8))
    cap_l, hull = _interior(sh.inner, z0, level)
    wmesh = hull_mesh(hull)
    water = _piece("water", "Water, to the overflow", "water", "water", wmesh, {"volume_l": cap_l * 1000, "depth_m": level - z0}, "water")
    ctx = []
    if spec.people:
        ctx += M._person((-(sh.r_max + 0.8), 0.4, 0.0), -90.0)
    for p in ctx:
        p.group = "person"
    K.context(ctx)
    ground = _piece("ground", "Ground", "site", "ground", S.box((0, 0, -0.03), (2 * sh.r_max + 5, 2 * sh.r_max + 5, 0.06)), {}, "site")
    K.context([ground])

    # strength: estimates, labelled, against a declared allowable
    depth = level - z0
    p_floor = water_d * g * depth
    t_m = tp
    hoop = p_floor * sh.R / t_m / 1e6
    lowest = [p for p in sh.plates if p.ring == 0]
    r_in = max(2 * S.poly_area(p.poly) / sum(float(np.linalg.norm(p.poly[(i + 1) % len(p.poly)] - p.poly[i])) for i in range(len(p.poly))) for p in lowest)
    bend = 0.75 * p_floor * r_in ** 2 / t_m ** 2 / 1e6
    allow = D(T, "fy_mpa") * D(T, "allow_frac") * D(T, "weld_eff")
    margin_x = allow / max(hoop, bend)
    water_kg = cap_l * water_d
    mass = sum(S.volume(p.mesh) for p in sh.plates + sh.skirts) * steel + cap_mass + sum(S.poly_area(p) * tf * steel for p in fl)

    book = K.Book()
    shell_pieces = [p for p in pieces if p.tag == "shell"]
    rings = sorted({p.info["ring"] for p in shell_pieces})
    book.prep("Before you start: what it will weigh",
              f"Full, this tank holds {K.litres(cap_l * 1000)} and weighs {K.kg(water_kg + mass)}: the pad and the ground under it have to carry that. "
              "Line or coat the inside with a coating rated for drinking water if people will drink from it. Never go inside without a second person outside.",
              [], ["Level site", "Drinking-water coating"], phase="Plan")
    nsheets = nest_plates(sh.plates, sw, sl, gap)
    book.prep("Cut the plates",
              f"Cut {len(sh.plates)} shell plates in {len(classes)} shapes" + (f", {len(sh.skirts)} skirt plates" if sh.skirts else "")
              + f", the cap and {len(fl)} floor pieces. The shell nests on {len(nsheets)} sheet(s) of {K.m(tp)} plate; each floor piece takes a "
              f"sheet of {K.m(tf)} plate. Scribe each mark on the inside face.",
              [p for p in pieces if p.tag in ("shell", "cap", "floor")], ["Plasma cutter", "Straightedge and soapstone"],
              "Stack the plates of one shape: their edges agree within 1/32 in.")
    bev = [b for p in sh.plates + sh.skirts for b in p.bevels]
    book.prep("Bevel the edges",
              f"Grind every edge to the bevel on its plate card ({K.deg(min(bev))} to {K.deg(max(bev))} from square), so neighbours meet in a V for a full weld.",
              shell_pieces, ["Grinder with flap disc", "Angle gauge"])
    book.add("Pour the pad", f"Pour a level concrete pad {K.m(pad_t)} thick, {K.m(margin)} past the tank all round.", [pad],
             ["Forms", "Concrete", "Level"], "Level within 1/8 in across.")
    book.add("Weld the floor", f"Lay the {len(fl)} floor pieces on the pad and weld them into one plate.",
             [p for p in pieces if p.tag == "floor"], ["Welder"], "Every floor seam welded through.")
    for r in rings:
        ring_ps = [p for p in shell_pieces if p.info["ring"] == r]
        book.add(f"Tack ring {r} of {len(rings)}",
                 ("Stand the bottom ring on the floor. " if r == rings[0] else "Set the next ring on the one below. ")
                 + f"Tack these {len(ring_ps)} plates at their corners; leave the beads until the shell is round.",
                 ring_ps, ["Welder", "Clamps", "Magnetic squares"], "Measure across at this height in two directions: they agree within 1/8 in.")
    book.add("Cap and manway", f"Tack the cap on, with its {K.m(spec.manway_m)} manway collar.", [p for p in pieces if p.tag == "cap"], ["Welder"])
    book.prep("Weld it out", f"Run every seam: {K.m(sh.weld_m)} of weld, outside first, then back-weld inside where you can reach.",
              shell_pieces, ["Welder", "Grinder"])
    book.add("Pipes", "Weld in the inlet near the top, the overflow just under the cap, the outlet a little above the floor and the drain at the floor.",
             pipes, ["Welder", "Hole saw"], "Every pipe stub sticks out square to its plate.")
    book.add("Hatch", "Hinge or bolt the hatch lid over the manway, with a screen under it to keep insects out.", [lid], ["Welder"])
    book.prep("Leak test",
              f"Fill it in stages, a quarter at a time, and walk every seam between fills. A full tank presses {K.kpa(p_floor / 1000)} on the floor.",
              shell_pieces, ["Hose", "Chalk"], "No damp spots after a day full.")
    if spec.water:
        book.add("Fill it", f"Fill to the overflow: {K.litres(cap_l * 1000)}, {K.m(depth)} deep.", [water], ["Hose"])
    pieces += pipes + [lid] + ([water] if spec.water else []) + [ground] + ctx

    cards = [plate_card(mk, g_, steel) for mk, g_ in classes.items()] + [plate_card(mk, g_, steel) for mk, g_ in skirt_classes.items()]
    cap_pts = K.flat(sh.cap.poly, UP, longest_on_x=False)
    cards.append(K.card("CAP", "Top cap", 1, [["Manway hole", K.m(spec.manway_m)], ["Each", K.kg(cap_mass)]],
                        K.drawing(cap_pts, holes=[{"c": [sum(x for x, _ in cap_pts) / len(cap_pts), sum(y for _, y in cap_pts) / len(cap_pts)], "r": spec.manway_m / 2}]),
                        ["cap"], "Cap", "plate"))
    for fp in floor_plates:
        cards.append(K.card(fp.mark, f"Floor plate {fp.mark}", 1, [["Area", K.m2(S.poly_area(fp.poly))], ["Each", K.kg(S.poly_area(fp.poly) * tf * steel)]],
                            K.drawing([[q[0], q[1]] for q in fp.poly], angles=False), [fp.pid], "Floor", "plate"))
    for pp in pipes:
        cards.append(K.card(pp.id.upper(), pp.name, 1, [["Pipe", f"{K.m(pp.info['diameter_m'])} outside"], ["Centre above the floor", K.m(pp.info["height_m"])],
                                                          ["Stub outside", K.m(stub)]], None, [pp.id], "Pipes", "pipe"))
    summary = [
        ["Across the floor", K.m(2 * sh.r_base)], ["Height to the cap", K.m(sh.z_cap + tp - pad_t)],
        ["Capacity, to the overflow", K.litres(cap_l * 1000)], ["Water", K.kg(water_kg)], ["Full, on the pad", K.kg(water_kg + mass)],
        ["Pressure at the floor", K.kpa(p_floor / 1000)],
        ["Plates", f"{len(sh.plates)} shell" + (f" + {len(sh.skirts)} skirt" if sh.skirts else "") + f" + cap + {len(fl)} floor"],
        ["Plate shapes", K.n(len(classes) + len(skirt_classes))], ["Steel", K.kg(mass)], ["Weld", K.m(sh.weld_m)],
        ["Shell stress (estimate)", K.mpa(hoop)], ["Plate bending (estimate)", K.mpa(bend)],
        ["Allowed at a weld", K.mpa(allow)], ["Margin (estimate)", f"{margin_x:.1f} x"], ["Sheets of plate", K.n(len(nsheets) + len(fl))],
    ]
    declared = {"diameter_m": Declared(spec.diameter_m, "m", "the tank's size, as chosen: across the floor"),
                "plate_m": Declared(tp, "m", "shell plate, as chosen; the stress estimates say whether it is enough"),
                "floor_m": Declared(tf, "m", "floor plate, as chosen"),
                "manway_m": Declared(spec.manway_m, "m", "manway, as chosen: big enough to climb in to clean"), **T}
    warnings = []
    if margin_x < 2.0:
        warnings.append(f"Thin for its size: the estimated margin is {margin_x:.1f} x. Use thicker plate or a smaller tank.")
    warnings.append("Stress figures are estimates (a cylinder's hoop stress and a clamped round plate in bending), not a design check.")
    tables = {
        "title": spec.title, "summary": summary, "cards": cards, "sheets": nsheets, "steps": book.steps,
        "declared": K.declared_rows(declared), "warnings": warnings,
        "tags": [["shell", "Shell plates"], ["cap", "Cap and manway"], ["floor", "Floor"], ["base", "Pad"], ["fittings", "Pipes and hatch"],
                 ["water", "Water"], ["site", "Ground"], ["person", "Person"]],
        "scenes": _scenes(),
        "tank": {"R": sh.R, "z0": z0, "z_cap": sh.z_cap, "level": level, "capacity_l": cap_l * 1000, "water_kg": water_kg, "mass_kg": mass,
                 "p_floor_kpa": p_floor / 1000, "hoop_mpa": hoop, "bend_mpa": bend, "allow_mpa": allow, "margin": margin_x,
                 "weld_m": sh.weld_m, "plates": len(sh.plates), "classes": len(classes), "water_mesh_l": S.volume(wmesh) * 1000,
                 "plate_m": tp, "floor_m": spec.floor_m, "shell_sheets": len(nsheets), "floor_pieces": len(fl)},
    }
    return Model(spec, pieces, tables, {"centre": [0.0, 0.0, (z0 + sh.z_cap) / 2]})
