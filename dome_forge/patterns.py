"""Flat cover patterns: unfold the curved dome into cuttable shapes.

A dome is doubly curved, but it is made of *flat* triangles, so any
connected patch can be laid out flat exactly -- the way a sailmaker or a
stitch-and-glue boatbuilder develops a curved surface into panels you cut
from flat stock. This module does that development and reports whether a
pattern fits on a given sheet, with a seam allowance added for the slack
that wraps around the frame and gets stapled or sewn.

Two developments are used:

* A **strip** unfolds a chain of triangles across their shared edges.
  Because a chain is a tree (no loop around any vertex) it develops with
  no gap -- an exact, seamless flat pattern. Single/double/triple covers
  are strips.

* A **fan** unfolds the ring of triangles around one vertex. Going all
  the way around a vertex meets the *angular deficit*: the flat angles do
  not add to 360 degrees, so the fan leaves an open wedge. That wedge is
  the dart -- close it (sew or lap and staple) and the flat sheet pulls
  up into the dome's curve. Pentagons (five triangles, ~15.7 deg dart)
  and hexagons (six, ~17.7 deg) are fans.

Everything is in inches, computed from two_v_demo's own geometry scaled
so the long strut matches the real dome, so a printed pattern is cut to
the same numbers the frame was built to.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from two_v_demo.geometry import build_demo_geometry


IN_PER_FT = 12.0
# long / short strut ratio for a 2V dome, from the geometry itself.
_RATIO = build_demo_geometry().ratio


@dataclass
class Pattern:
    """A finished flat pattern, ready to lay on a sheet."""

    key: str
    label: str
    # The cut outline (outer boundary including seam allowance), 2D inches.
    outline: list[tuple[float, float]]
    # The net line (the actual panel edge, before allowance) for reference.
    net: list[tuple[float, float]]
    # Fold/score lines between triangles, as (p0, p1) segment pairs.
    folds: list[tuple[tuple[float, float], tuple[float, float]]] = field(
        default_factory=list)
    # The dart: the open wedge left by a fan's angular deficit (or None).
    dart: tuple[tuple[float, float], tuple[float, float],
                tuple[float, float]] | None = None
    dart_angle: float = 0.0
    seam: float = 0.0
    triangles: int = 0
    per_dome: int = 0
    notes: str = ""

    @property
    def net_edges(self) -> list[tuple[float, tuple, tuple]]:
        """The net outline's edges with their lengths, for the cut list."""
        out = []
        for i in range(len(self.net)):
            a = self.net[i]
            b = self.net[(i + 1) % len(self.net)]
            out.append((math.dist(a, b), a, b))
        return out


# ---------------------------------------------------------------------------
# Scaled geometry
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _scaled(long_strut_in: float):
    """The hemisphere's vertices scaled so the long strut is exactly
    ``long_strut_in`` inches, plus the incidence tables the unfolders need."""
    geo = build_demo_geometry()
    radius = long_strut_in / geo.long_factor
    verts = np.asarray(geo.vertices, dtype=np.float64) * radius
    faces = [tuple(int(i) for i in f) for f in geo.hemisphere_faces]
    class_by_edge = {tuple(sorted(edge)): name
                     for edge, name in zip(geo.edges, geo.edge_class_by_edge)}
    at_vertex: dict[int, list[int]] = defaultdict(list)
    for index, face in enumerate(faces):
        for vertex in face:
            at_vertex[vertex].append(index)
    return verts, faces, class_by_edge, dict(at_vertex), radius


def _edge_name(class_by_edge, a: int, b: int) -> str:
    return class_by_edge.get(tuple(sorted((a, b))), "LONG")


def _side_len(verts, a: int, b: int) -> float:
    return float(np.linalg.norm(verts[a] - verts[b]))


# ---------------------------------------------------------------------------
# Development (unfolding) -- pure 2D trigonometry
# ---------------------------------------------------------------------------

def _place_triangle(len_ab: float, len_bc: float, len_ca: float):
    """A triangle of known side lengths, laid flat: A at origin, B on the
    +x axis, C above. Sides are AB, BC, CA."""
    ax, ay = 0.0, 0.0
    bx, by = len_ab, 0.0
    # C from the two circle radii CA (about A) and BC (about B).
    cx = (len_ab * len_ab + len_ca * len_ca - len_bc * len_bc) / (2.0 * len_ab)
    cy = math.sqrt(max(0.0, len_ca * len_ca - cx * cx))
    return [(ax, ay), (bx, by), (cx, cy)]


def _rotate(point, pivot, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    dx, dy = point[0] - pivot[0], point[1] - pivot[1]
    return (pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca)


def _reflect(point, a, b):
    """Reflect ``point`` across the line through a, b."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom < 1e-12:
        return point
    t = ((point[0] - ax) * dx + (point[1] - ay) * dy) / denom
    foot = (ax + t * dx, ay + t * dy)
    return (2 * foot[0] - point[0], 2 * foot[1] - point[1])


def unfold_strip(long_strut_in: float, face_list):
    """Develop a chain of faces across shared edges into one flat piece.

    Returns (triangle 2D-vertex lists, ordered boundary loop, fold
    segments). A chain has no loop around a vertex, so this is an exact,
    seamless development.
    """
    verts, faces, *_ = _scaled(long_strut_in)
    placed: list[dict[int, tuple[float, float]]] = []
    folds = []

    first = faces[face_list[0]]
    coords = _place_triangle(
        _side_len(verts, first[0], first[1]),
        _side_len(verts, first[1], first[2]),
        _side_len(verts, first[2], first[0]))
    placed.append({first[i]: coords[i] for i in range(3)})

    for prev_pos, face_index in zip(face_list, face_list[1:]):
        prev_face = faces[face_list[face_list.index(prev_pos)]]
        prev_map = placed[-1]
        face = faces[face_index]
        shared = [v for v in face if v in prev_face]
        if len(shared) != 2:
            raise ValueError("strip faces must share an edge")
        s0, s1 = shared
        p0, p1 = prev_map[s0], prev_map[s1]
        third = next(v for v in face if v not in shared)
        # The third vertex sits at its true distances from the shared
        # edge's two ends; reflect the trial placement to the far side of
        # the shared edge so the new face lies beyond the old one.
        trial = _place_triangle(
            _side_len(verts, s0, s1),
            _side_len(verts, s1, third),
            _side_len(verts, third, s0))
        # trial has s0 at origin, s1 on +x; map that frame onto p0->p1.
        base_len = math.dist(p0, p1)
        angle = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        tx, ty = trial[2]
        # rotate trial's third point onto the p0->p1 frame
        rx = p0[0] + (tx * math.cos(angle) - ty * math.sin(angle))
        ry = p0[1] + (tx * math.sin(angle) + ty * math.cos(angle))
        cand = (rx, ry)
        # put it on the opposite side of the shared edge from the prev face
        prev_third = next(v for v in prev_face if v not in shared)
        if _same_side((rx, ry), prev_map[prev_third], p0, p1):
            cand = _reflect(cand, p0, p1)
        placed.append({s0: p0, s1: p1, third: cand})
        folds.append((p0, p1))

    boundary = _strip_boundary(placed)
    return placed, boundary, folds


def _same_side(p, q, a, b) -> bool:
    def cross(u, v, w):
        return ((v[0] - u[0]) * (w[1] - u[1])
                - (v[1] - u[1]) * (w[0] - u[0]))
    return cross(a, b, p) * cross(a, b, q) > 0


def _strip_boundary(placed):
    """The outer loop of a set of placed triangles: every edge used once
    is a boundary edge; walk them into a single loop."""
    edge_count: dict[tuple, int] = defaultdict(int)
    edge_pts: dict[tuple, tuple] = {}
    for tri in placed:
        keys = list(tri.keys())
        for i in range(3):
            a, b = keys[i], keys[(i + 1) % 3]
            key = tuple(sorted((a, b)))
            edge_count[key] += 1
            edge_pts[key] = (tri[a], tri[b])
    outer = [k for k, c in edge_count.items() if c == 1]
    adjacency: dict[int, list[int]] = defaultdict(list)
    for a, b in outer:
        adjacency[a].append(b)
        adjacency[b].append(a)
    start = outer[0][0]
    loop = [start]
    prev = None
    current = start
    while True:
        nxt = next((v for v in adjacency[current] if v != prev), None)
        if nxt is None or nxt == start:
            break
        loop.append(nxt)
        prev, current = current, nxt
    any_tri = placed[0]
    coord = {}
    for tri in placed:
        coord.update(tri)
    return [coord[v] for v in loop]


def unfold_fan(long_strut_in: float, apex: int):
    """Unfold the ring of triangles around ``apex`` as a fan.

    Returns (2D triangles, boundary loop, fold segments, dart, deficit
    degrees). The fan spans the sum of the apex interior angles and leaves
    a wedge equal to the angular deficit.
    """
    verts, faces, class_by_edge, at_vertex, _ = _scaled(long_strut_in)
    ring = _ordered_ring(faces, at_vertex[apex], apex)

    origin = (0.0, 0.0)
    cursor = 0.0
    placed = []
    folds = []
    first_dir_pt = None
    last_dir_pt = None
    for face in ring:
        others = [v for v in face if v != apex]
        # Keep a consistent winding so successive triangles fan the same
        # way round the apex.
        others = _order_pair(faces, ring, face, others, apex)
        r0 = _side_len(verts, apex, others[0])
        r1 = _side_len(verts, apex, others[1])
        base = _side_len(verts, others[0], others[1])
        apex_angle = _law_of_cosines(r0, r1, base)
        p0 = (r0 * math.cos(cursor), r0 * math.sin(cursor))
        p1 = (r1 * math.cos(cursor + apex_angle),
              r1 * math.sin(cursor + apex_angle))
        placed.append({apex: origin, others[0]: p0, others[1]: p1})
        if first_dir_pt is None:
            first_dir_pt = p0
        last_dir_pt = p1
        folds.append((origin, p1))
        cursor += apex_angle
    folds = folds[:-1]  # the last radial is the pattern's own edge, not a fold

    boundary = [origin]
    for tri, face in zip(placed, ring):
        others = [v for v in tri if v != apex]
        others = _order_pair(faces, ring, face, others, apex)
        boundary.append(tri[others[0]])
        boundary.append(tri[others[1]])
    # de-dupe consecutive shared vertices
    cleaned = [boundary[0]]
    for pt in boundary[1:]:
        if math.dist(pt, cleaned[-1]) > 1e-6:
            cleaned.append(pt)

    deficit = 360.0 - math.degrees(cursor)
    dart = (last_dir_pt, origin, first_dir_pt)
    return placed, cleaned, folds, dart, deficit


def _law_of_cosines(a: float, b: float, opposite: float) -> float:
    cosine = (a * a + b * b - opposite * opposite) / (2.0 * a * b)
    return math.acos(max(-1.0, min(1.0, cosine)))


def _ordered_ring(faces, face_indices, apex):
    """Order the faces around ``apex`` so each shares an edge with the
    next, giving a proper ring."""
    remaining = list(face_indices)
    ring = [remaining.pop(0)]
    while remaining:
        last = faces[ring[-1]]
        last_verts = set(last)
        for i, idx in enumerate(remaining):
            shared = last_verts & set(faces[idx])
            # adjacent faces around a vertex share the apex plus one more
            if apex in shared and len(shared) == 2:
                ring.append(remaining.pop(i))
                break
        else:
            ring.append(remaining.pop(0))
    return [faces[i] for i in ring]


def _order_pair(faces, ring, face, others, apex):
    """Put the two non-apex vertices of a fan face in ring order: the
    first is the edge shared with the previous face."""
    prev_index = ring.index(face) - 1
    if prev_index >= 0:
        prev = set(ring[prev_index])
        if others[1] in prev and others[0] not in prev:
            return [others[1], others[0]]
    return list(others)


# ---------------------------------------------------------------------------
# Seam allowance (outward offset)
# ---------------------------------------------------------------------------

def seam_offset(loop, inches: float):
    """Push a closed loop outward by ``inches`` -- the slack that wraps the
    frame edge for stapling or the seam allowance for sewing.

    Each edge slides out along its outward normal; adjacent offset edges
    are re-intersected at the corners (a mitred offset). Correct for the
    convex outer boundaries these patterns have.
    """
    if inches <= 0.0 or len(loop) < 3:
        return list(loop)
    pts = [np.array(p, dtype=np.float64) for p in loop]
    n = len(pts)
    signed = _signed_area(loop)
    winding = 1.0 if signed > 0 else -1.0
    lines = []
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        edge = b - a
        length = float(np.linalg.norm(edge))
        if length < 1e-9:
            continue
        direction = edge / length
        # outward normal for this winding
        normal = np.array([direction[1], -direction[0]]) * winding
        lines.append((a + normal * inches, direction))
    out = []
    m = len(lines)
    for i in range(m):
        p0, d0 = lines[(i - 1) % m]
        p1, d1 = lines[i]
        hit = _intersect(p0, d0, p1, d1)
        out.append(tuple(hit) if hit is not None else tuple(p1))
    return out


def _signed_area(loop) -> float:
    total = 0.0
    n = len(loop)
    for i in range(n):
        x0, y0 = loop[i]
        x1, y1 = loop[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return total * 0.5


def _intersect(p0, d0, p1, d1):
    denom = d0[0] * d1[1] - d0[1] * d1[0]
    if abs(denom) < 1e-12:
        return None
    diff = p1 - p0
    t = (diff[0] * d1[1] - diff[1] * d1[0]) / denom
    return p0 + d0 * t


def polygon_area(loop) -> float:
    return abs(_signed_area(loop))


def bounds(loop):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------------------
# Fitting on a sheet
# ---------------------------------------------------------------------------

@dataclass
class FitReport:
    fits: bool
    rotated: bool
    pattern_w: float
    pattern_h: float
    sheet_w: float
    sheet_h: float
    used_fraction: float
    per_sheet: int


def fit_on_sheet(loop, sheet_w_in: float, sheet_h_in: float) -> FitReport:
    """Can this outline lie on a sheet of the given size? Tries the sheet
    both ways round (0 and 90 degrees) and reports the tighter fit, plus a
    rough count of how many copies tile onto one sheet by bounding box."""
    x0, y0, x1, y1 = bounds(loop)
    pw, ph = x1 - x0, y1 - y0
    options = [
        (False, pw <= sheet_w_in and ph <= sheet_h_in),
        (True, ph <= sheet_w_in and pw <= sheet_h_in),
    ]
    rotated = False
    fits = False
    for is_rot, ok in options:
        if ok:
            fits, rotated = True, is_rot
            break
    across = max(0, int(sheet_w_in // pw)) * max(0, int(sheet_h_in // ph))
    swapped = max(0, int(sheet_w_in // ph)) * max(0, int(sheet_h_in // pw))
    per_sheet = max(across, swapped)
    used = (pw * ph) / (sheet_w_in * sheet_h_in) if sheet_w_in and sheet_h_in else 0.0
    return FitReport(fits, rotated, pw, ph, sheet_w_in, sheet_h_in,
                     min(1.0, used), per_sheet)


# ---------------------------------------------------------------------------
# The named patterns
# ---------------------------------------------------------------------------

def _chain_of(long_strut_in: float, count: int):
    """A contiguous run of ``count`` real hemisphere faces, for the
    single/double/triple covers, so the shapes are authentic."""
    _, faces, _, at_vertex, _ = _scaled(long_strut_in)
    chain = [0]
    used = {0}
    while len(chain) < count:
        last = set(faces[chain[-1]])
        for idx, face in enumerate(faces):
            if idx in used:
                continue
            if len(last & set(face)) == 2:
                chain.append(idx)
                used.add(idx)
                break
        else:
            break
    return chain


PATTERN_SPECS = (
    ("single_iso", "Single triangle (isosceles)", 1),
    ("single_equi", "Single triangle (equilateral)", 1),
    ("double", "Double (two triangles)", 2),
    ("triple", "Triple (three triangles)", 3),
    ("pentagon", "Pentagon (five, ~15.7 deg dart)", 5),
    ("pentagon_3", "Pentagon 3-piece (of a 3+2 split)", 3),
    ("pentagon_2", "Pentagon 2-piece (of a 3+2 split)", 2),
    ("hexagon", "Hexagon (six, ~17.7 deg dart)", 6),
    ("hexagon_4", "Hexagon 4-piece (of a 4+2 split)", 4),
    ("hexagon_2", "Hexagon 2-piece (of a 4+2 split)", 2),
)


def _partial_group_faces(long_strut_in: float, degree: int, take: int,
                         skip: int = 0):
    """A contiguous run of ``take`` faces from the ring around a degree-N
    vertex, skipping the first ``skip``.

    A pentagon or hexagon that will not fit the sheet whole is split into
    contiguous runs (a 3+2 for a pentagon). Adjacent triangles in the ring
    share a radial edge, so each run develops as an exact seamless strip.
    """
    _, faces, _, at_vertex, _ = _scaled(long_strut_in)
    apex = next(v for v, fs in at_vertex.items() if len(fs) == degree)
    ring = _ordered_ring(faces, at_vertex[apex], apex)
    face_index = {tuple(sorted(f)): i for i, f in enumerate(faces)}
    chosen = ring[skip:skip + take]
    return [face_index[tuple(sorted(f))] for f in chosen]


def build_pattern(key: str, long_strut_in: float, seam_in: float) -> Pattern:
    _, faces, class_by_edge, at_vertex, _ = _scaled(long_strut_in)
    equilateral = {i for i, f in enumerate(faces)
                   if all(_edge_name(class_by_edge, f[j], f[(j + 1) % 3]) == "LONG"
                          for j in range(3))}

    dart = None
    dart_angle = 0.0
    folds = []
    per_dome = 0
    notes = ""

    if key in ("single_iso", "single_equi"):
        if key == "single_equi":
            face_index = next(iter(equilateral))
            per_dome = len(equilateral)
            notes = "The 10 all-72in faces. Base of every hourglass."
        else:
            face_index = next(i for i in range(len(faces)) if i not in equilateral)
            per_dome = len(faces) - len(equilateral)
            notes = "The 30 isosceles faces. Every pentagon is five of these."
        placed, net, folds = unfold_strip(long_strut_in, [face_index])
        triangles = 1
    elif key in ("double", "triple"):
        count = 2 if key == "double" else 3
        placed, net, folds = unfold_strip(long_strut_in, _chain_of(long_strut_in, count))
        triangles = count
        notes = ("Cover two adjacent triangles from one piece; the ridge "
                 "between them is a fold line, not a seam.") if count == 2 else (
                 "Three-triangle strip -- one continuous cover across a "
                 "run of the frame.")
    elif key in ("pentagon_3", "pentagon_2", "hexagon_4", "hexagon_2"):
        degree = 5 if key.startswith("pentagon") else 6
        take = int(key.split("_")[1])
        skip = 0 if take in (3, 4) else (3 if degree == 5 else 4)
        placed, net, folds = unfold_strip(
            long_strut_in, _partial_group_faces(long_strut_in, degree, take, skip))
        triangles = take
        per_dome = sum(1 for v, fs in at_vertex.items() if len(fs) == degree)
        whole = "pentagon" if degree == 5 else "hexagon"
        other = {3: 2, 2: 3, 4: 2}[take]
        notes = (f"{take} of a {whole}'s triangles as one seamless strip. "
                 f"The matching {other}-piece covers the rest; they overlap "
                 f"along the shared radial. Use when a whole {whole} is too "
                 f"big for the sheet.")
    elif key in ("pentagon", "hexagon"):
        degree = 5 if key == "pentagon" else 6
        apex = next(v for v, fs in at_vertex.items() if len(fs) == degree)
        placed, net, folds, dart, dart_angle = unfold_fan(long_strut_in, apex)
        triangles = degree
        per_dome = sum(1 for v, fs in at_vertex.items() if len(fs) == degree)
        notes = (f"Five triangles around a point. Lay flat, close the "
                 f"{dart_angle:.1f} deg dart, and the centre lifts into the "
                 f"dome's curve.") if degree == 5 else (
                 f"Six triangles around a point, {dart_angle:.1f} deg dart.")

    outline = seam_offset(net, seam_in)
    label = dict((k, l) for k, l, _ in PATTERN_SPECS)[key]
    return Pattern(key, label, outline, net, folds, dart, dart_angle,
                   seam_in, triangles, per_dome, notes)


# ---------------------------------------------------------------------------
# Nesting: many pieces on one or more sheets
# ---------------------------------------------------------------------------

@dataclass
class Placement:
    """One pattern piece laid on the cover material at a position and a
    free rotation angle, on a given sheet."""

    key: str
    x: float = 0.0          # inches, top-left of the rotated bbox
    y: float = 0.0
    rot: float = 0.0        # degrees, any angle
    sheet: int = 0

    def to_json(self) -> dict:
        return {"key": self.key, "x": round(self.x, 2), "y": round(self.y, 2),
                "rot": round(float(self.rot), 2), "sheet": self.sheet}

    @staticmethod
    def from_json(data: dict) -> "Placement":
        return Placement(data["key"], float(data.get("x", 0)),
                         float(data.get("y", 0)), float(data.get("rot", 0)),
                         int(data.get("sheet", 0)))


def _rotate_loop(loop, deg: float):
    """Rotate a loop about the origin by any angle in degrees."""
    if not deg:
        return [(x, y) for x, y in loop]
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [(x * c - y * s, x * s + y * c) for x, y in loop]


def placed_geometry(placement: Placement, long_strut_in: float, seam_in: float):
    """A placement's outline, net, folds and dart in sheet coordinates."""
    pattern = build_pattern(placement.key, long_strut_in, seam_in)
    rot = placement.rot

    def xform_loop(loop):
        r = _rotate_loop(loop, rot)
        minx = min(p[0] for p in r)
        miny = min(p[1] for p in r)
        return [(p[0] - minx + placement.x, p[1] - miny + placement.y)
                for p in r]

    # net/folds/dart share the outline's rotate+shift, so compute the
    # shift once from the outline (the largest loop) and reuse it.
    r_out = _rotate_loop(pattern.outline, rot)
    minx = min(p[0] for p in r_out)
    miny = min(p[1] for p in r_out)

    def shift(loop):
        r = _rotate_loop(loop, rot)
        return [(p[0] - minx + placement.x, p[1] - miny + placement.y)
                for p in r]

    outline = shift(pattern.outline)
    net = shift(pattern.net)
    folds = [(shift([a])[0], shift([b])[0]) for a, b in pattern.folds]
    dart = shift(pattern.dart) if pattern.dart else None
    return pattern, outline, net, folds, dart


def piece_size(key: str, long_strut_in: float, seam_in: float, rot: float):
    pattern = build_pattern(key, long_strut_in, seam_in)
    r = _rotate_loop(pattern.outline, rot)
    x0, y0, x1, y1 = bounds(r)
    return x1 - x0, y1 - y0


def placed_centroid(placement: Placement, long_strut_in: float,
                    seam_in: float):
    """The centroid of a placement's net edge, in sheet coordinates."""
    _p, _outline, net, *_ = placed_geometry(placement, long_strut_in, seam_in)
    return (sum(p[0] for p in net) / len(net),
            sum(p[1] for p in net) / len(net))


def set_rotation_about_centroid(placement: Placement, new_rot: float,
                                long_strut_in: float, seam_in: float) -> None:
    """Spin a placed piece to ``new_rot`` degrees while keeping its centroid
    fixed on the sheet -- what a rotate handle should feel like, rather than
    the piece jumping as its bounding box changes."""
    target = placed_centroid(placement, long_strut_in, seam_in)
    placement.rot = new_rot
    now = placed_centroid(placement, long_strut_in, seam_in)
    placement.x += target[0] - now[0]
    placement.y += target[1] - now[1]


def rotate_handle(placement: Placement, long_strut_in: float, seam_in: float):
    """Where the rotate grip sits: the piece's centroid, and a knob point
    held a fixed distance beyond the piece's farthest corner, in the
    direction the piece currently points -- so the grip rides just outside
    the piece at every angle. Returns (centroid, knob, radius) in inches."""
    _p, _outline, net, *_ = placed_geometry(placement, long_strut_in, seam_in)
    cx = sum(p[0] for p in net) / len(net)
    cy = sum(p[1] for p in net) / len(net)
    reach = max(math.dist((cx, cy), v) for v in net) + 9.0
    ang = math.radians(placement.rot - 90.0)   # "up" in the piece's frame
    knob = (cx + reach * math.cos(ang), cy + reach * math.sin(ang))
    return (cx, cy), knob, reach


def point_in_loop(pt, loop) -> bool:
    x, y = pt
    inside = False
    n = len(loop)
    j = n - 1
    for i in range(n):
        xi, yi = loop[i]
        xj, yj = loop[j]
        if ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def auto_nest(keys, long_strut_in: float, seam_in: float,
              sheet_w_in: float, sheet_h_in: float, gap_in: float = 1.0):
    """Shelf-pack the pieces onto as many sheets as needed.

    Each piece takes its better of two rotations (whichever is shorter),
    biggest first; pieces flow left to right along a shelf, wrap to a new
    shelf when the row is full, and start a fresh sheet when the column
    is full. Returns a list of Placement.
    """
    sized = []
    for key in keys:
        w0, h0 = piece_size(key, long_strut_in, seam_in, 0)
        w9, h9 = piece_size(key, long_strut_in, seam_in, 90)
        # prefer the orientation that is shorter (packs into fewer shelves)
        if h9 < h0 and w9 <= sheet_w_in:
            sized.append((key, 90, w9, h9))
        else:
            sized.append((key, 0, w0, h0))
    sized.sort(key=lambda s: -s[3])   # tallest first

    placements = []
    sheet = 0
    cursor_x = 0.0
    cursor_y = 0.0
    shelf_h = 0.0
    for key, rot, w, h in sized:
        if w > sheet_w_in or h > sheet_h_in:
            # Too big for a sheet at all -- park it on its own sheet so the
            # user sees it flagged rather than silently dropped.
            sheet_used = max((p.sheet for p in placements), default=-1) + 1
            placements.append(Placement(key, 0.0, 0.0, rot, sheet_used + 1))
            continue
        if cursor_x + w > sheet_w_in:
            cursor_x = 0.0
            cursor_y += shelf_h + gap_in
            shelf_h = 0.0
        if cursor_y + h > sheet_h_in:
            sheet += 1
            cursor_x = cursor_y = shelf_h = 0.0
        placements.append(Placement(key, cursor_x, cursor_y, rot, sheet))
        cursor_x += w + gap_in
        shelf_h = max(shelf_h, h)
    return placements


def sheet_usage(placements, long_strut_in: float, seam_in: float,
                sheet_w_in: float, sheet_h_in: float):
    """Per-sheet used-area fraction and a total sheet count."""
    sheets = {}
    for placement in placements:
        _, outline, *_ = placed_geometry(placement, long_strut_in, seam_in)
        sheets.setdefault(placement.sheet, 0.0)
        sheets[placement.sheet] += polygon_area(outline)
    area = sheet_w_in * sheet_h_in
    return {s: min(1.0, used / area) for s, used in sheets.items()}


def dome_coverage(long_strut_in: float, sheet_w_in: float,
                  sheet_h_in: float, seam_in: float) -> list[str]:
    """A whole-dome material summary: how many of each group the dome
    needs and how they land on the chosen sheet."""
    lines = []
    for key in ("pentagon", "hexagon", "single_iso", "single_equi"):
        pattern = build_pattern(key, long_strut_in, seam_in)
        report = fit_on_sheet(pattern.outline, sheet_w_in, sheet_h_in)
        need = pattern.per_dome
        verb = "fits" if report.fits else "TOO BIG for"
        extra = "" if report.fits else " (split into smaller groups)"
        lines.append(
            f"{pattern.label}: need {need}; "
            f"{report.pattern_w:.0f}x{report.pattern_h:.0f}in {verb} the "
            f"{sheet_w_in:.0f}x{sheet_h_in:.0f}in sheet{extra}")
    return lines
