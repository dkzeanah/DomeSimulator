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
    ("hexagon", "Hexagon (six, ~17.7 deg dart)", 6),
)


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
