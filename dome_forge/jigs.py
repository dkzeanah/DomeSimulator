"""The Jig Shop: how to build the two jigs that mass-produce the triangles.

A 2V hemisphere is 40 triangles, but only **two distinct shapes**: 10
equilateral and 30 isosceles. Build one jig for each and every triangle
after that is a repeat, which is the whole reason this dome can be made
in a shed instead of on a scaffold.

Every angle and length here is computed from the same
:func:`two_v_demo.geometry.build_demo_geometry` the dome itself is built
from, then measured *back off the real 3D faces* in :func:`verify` -- so
the cut list on screen and the dome on screen cannot disagree.

The bit that catches people out is at the corners. The interior angles of
the flat triangles meeting at a vertex do **not** add up to 360 degrees.
That shortfall (the angular deficit) is exactly what makes the assembly
curve. It also means a mitered tip is only a true point while the piece
is lying on the bench: once the dome folds up, the tips of the boards
meeting at a vertex converge on a *line through the vertex*, not on a
point in a plane. That is why each board also needs a bevel ripped along
its seam edge, and why the tips are usually blunted rather than left
razor-sharp.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from two_v_demo.geometry import build_demo_geometry, normalize


@dataclass(frozen=True)
class BoardCut:
    """One board in a jig's triangle."""

    edge_class: str
    outer_length: float
    inner_length: float
    miter_start: float
    miter_end: float
    bevel: float
    per_dome: int

    @property
    def summary(self) -> str:
        return (
            f"{self.edge_class} board  {self.outer_length:.3f}m long edge / "
            f"{self.inner_length:.3f}m short edge"
        )


@dataclass(frozen=True)
class JigSpec:
    key: str
    label: str
    triangles_needed: int
    edge_classes: tuple[str, str, str]
    corner_angles: tuple[float, float, float]
    chords: tuple[float, float, float]
    boards: tuple[BoardCut, ...]
    flat: tuple[tuple[float, float], ...]
    board_width: float
    board_thickness: float

    @property
    def miters(self) -> tuple[float, ...]:
        """Miter angle at each corner, measured off a square cut -- what
        you actually dial into a mitre saw."""
        return tuple(90.0 - angle / 2.0 for angle in self.corner_angles)


def _dihedrals() -> dict[str, float]:
    """Angle between the two faces meeting at each class of edge."""
    geo = build_demo_geometry()
    verts = geo.vertices
    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, face in enumerate(geo.faces):
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_faces[tuple(sorted((int(a), int(b))))].append(index)

    def outward_normal(face):
        points = verts[face]
        normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
        return normal if np.dot(normal, points.mean(axis=0)) > 0 else -normal

    class_by_edge = {tuple(sorted(edge)): name
                     for edge, name in zip(geo.edges, geo.edge_class_by_edge)}
    totals: dict[str, list[float]] = defaultdict(list)
    for edge, faces in edge_faces.items():
        if len(faces) != 2:
            continue
        n1 = outward_normal(geo.faces[faces[0]])
        n2 = outward_normal(geo.faces[faces[1]])
        between = math.degrees(math.acos(float(np.clip(np.dot(n1, n2), -1.0, 1.0))))
        totals[class_by_edge[edge]].append(180.0 - between)
    return {name: sum(values) / len(values) for name, values in totals.items()}


def _flat_triangle(chords: tuple[float, float, float]):
    """Lay a triangle of known side lengths flat on the bench.

    Sides are given in order (AB, BC, CA); the returned points are the
    jig's own coordinates, which is the pattern you actually scribe.
    """
    ab, bc, ca = chords
    a = (0.0, 0.0)
    b = (ab, 0.0)
    # Intersect the two circles of radius CA about A and BC about B.
    x = (ab * ab + ca * ca - bc * bc) / (2.0 * ab)
    y = math.sqrt(max(0.0, ca * ca - x * x))
    return (a, b, (x, y))


def jig_specs(radius: float = 4.2, board_width: float = 0.089,
              board_thickness: float = 0.038) -> tuple[JigSpec, ...]:
    """The full cut list for both jigs at a given dome size and board size."""
    geo = build_demo_geometry()
    dihedral = _dihedrals()
    factor = {item.name: item.factor for item in geo.edge_classes}
    specs = []
    for triangle in geo.triangle_classes:
        sides = triangle.side_names
        chords = tuple(factor[name] * radius for name in sides)
        # `angles_deg[i]` is the angle opposite side i, where side i runs
        # from vertex i to vertex i+1. The sides touching vertex k are
        # sides k-1 and k, so the side *not* touching it is side k+1 --
        # meaning the angle at vertex k is angles_deg[k+1].
        opposite = triangle.angles_deg
        corner_at = tuple(opposite[(i + 1) % 3] for i in range(3))
        boards = []
        for i, name in enumerate(sides):
            # Side i runs between the corners at its two ends; those are
            # the corners opposite the other two sides.
            start_angle = corner_at[i]
            end_angle = corner_at[(i + 1) % 3]
            trim = (board_width / math.tan(math.radians(start_angle / 2.0))
                    + board_width / math.tan(math.radians(end_angle / 2.0)))
            boards.append(BoardCut(
                edge_class=name,
                outer_length=chords[i],
                inner_length=chords[i] - trim,
                miter_start=90.0 - start_angle / 2.0,
                miter_end=90.0 - end_angle / 2.0,
                bevel=(180.0 - dihedral[name]) / 2.0,
                per_dome=triangle.hemisphere_count,
            ))
        equilateral = len(set(sides)) == 1
        specs.append(JigSpec(
            key="equilateral" if equilateral else "isosceles",
            label=("Jig A - equilateral (LONG-LONG-LONG)" if equilateral
                   else "Jig B - isosceles (LONG-SHORT-SHORT)"),
            triangles_needed=triangle.hemisphere_count,
            edge_classes=sides,
            corner_angles=corner_at,
            chords=chords,
            boards=tuple(boards),
            flat=_flat_triangle(chords),
            board_width=board_width,
            board_thickness=board_thickness,
        ))
    specs.sort(key=lambda s: s.key != "equilateral")
    return tuple(specs)


def vertex_report() -> tuple[dict, ...]:
    """How many triangles meet at each kind of vertex, and by how much
    their flat angles fall short of a full turn."""
    geo = build_demo_geometry()
    verts, faces = geo.vertices, geo.hemisphere_faces

    def interior(face, at):
        points = [verts[i] for i in face]
        k = list(face).index(at)
        v1 = points[(k + 1) % 3] - points[k]
        v2 = points[(k + 2) % 3] - points[k]
        cosine = float(np.dot(v1, v2) / np.linalg.norm(v1) / np.linalg.norm(v2))
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))

    at_vertex: dict[int, list[int]] = defaultdict(list)
    for index, face in enumerate(faces):
        for i in face:
            at_vertex[int(i)].append(index)
    grouped: dict[tuple[int, float], int] = defaultdict(int)
    for vertex, face_list in at_vertex.items():
        total = sum(interior(faces[f], vertex) for f in face_list)
        grouped[(len(face_list), round(total, 3))] += 1
    return tuple(
        {"triangles": n, "flat_sum": total, "deficit": 360.0 - total,
         "count": count}
        for (n, total), count in sorted(grouped.items())
    )


# ---------------------------------------------------------------------------
# The guided build
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Step:
    title: str
    detail: str
    stage: str


STEPS: tuple[Step, ...] = (
    Step("1. Know the two shapes",
         "A 2V hemisphere is 40 triangles but only two shapes: 10 "
         "equilateral and 30 isosceles. Two jigs is all you ever need. "
         "Press Tab to switch between them.",
         "shape"),
    Step("2. Cut the base plate",
         "Any flat, stiff sheet bigger than the triangle. Everything "
         "downstream inherits this plate's flatness, so pick the "
         "flattest sheet you have and keep it off the damp floor.",
         "plate"),
    Step("3. Scribe the outer triangle",
         "Draw the triangle at the chord lengths shown. These lines are "
         "the OUTSIDE face of the finished frame -- the boards sit "
         "inside them, not on them.",
         "scribe"),
    Step("4. Screw down three fences",
         "A fence along each scribed line. The boards get pushed out "
         "against these, so the outer edges land exactly on the chord "
         "lines every single time.",
         "fences"),
    Step("5. Add corner stops",
         "Short blocks on the angle bisector at each corner. They locate "
         "the mitered tips without trapping them -- leave the very point "
         "clear so sawdust can't push a board out of position.",
         "stops"),
    Step("6. Cut the boards",
         "Miter each end to the angle listed, and rip the bevel along "
         "the outer edge. The bevel is what lets the neighbouring "
         "triangle sit flat against this one instead of pinching at a "
         "line.",
         "boards"),
    Step("7. Load the jig",
         "Drop the three boards in, push each out against its fence, "
         "and clamp. If a tip stands proud, the miter is off before the "
         "jig is.",
         "loaded"),
    Step("8. Fasten and repeat",
         "Plate, screw, or bolt the corners, lift the finished triangle "
         "out, and go again. This is the step you repeat until you have "
         "the full count for this shape.",
         "fastened"),
    Step("9. Why the tips do not meet flat",
         "At a finished vertex the flat angles fall short of a full "
         "turn. That shortfall is what curves the dome -- and it means "
         "the tips converge on a line through the vertex, not a point "
         "on a plane. Expect a small void at each vertex; blunt the "
         "tips rather than chasing a perfect point.",
         "deficit"),
)


def step_lines(spec: JigSpec, step: Step) -> list[str]:
    """The numbers worth putting on screen for this step of this jig."""
    lines: list[str] = []
    if step.stage in ("shape", "scribe", "fences"):
        lines.append(f"Need {spec.triangles_needed} of this shape")
        for i, (name, chord) in enumerate(zip(spec.edge_classes, spec.chords)):
            lines.append(f"  side {i + 1}  {name:<5} {chord:.3f} m")
        for i, (angle, miter) in enumerate(zip(spec.corner_angles, spec.miters)):
            lines.append(f"  corner {i + 1}  {angle:.3f} deg  "
                         f"(saw {miter:.3f} deg)")
    elif step.stage == "stops":
        for i, (angle, miter) in enumerate(zip(spec.corner_angles, spec.miters)):
            lines.append(f"  corner {i + 1}  bisector {angle / 2:.3f} deg  "
                         f"saw {miter:.3f} deg")
    elif step.stage in ("boards", "loaded", "fastened"):
        lines.append(f"Board {spec.board_width * 1000:.0f} x "
                     f"{spec.board_thickness * 1000:.0f} mm")
        for i, board in enumerate(spec.boards):
            lines.append(f"  {i + 1}. {board.edge_class:<5} "
                         f"{board.outer_length:.3f}m -> "
                         f"{board.inner_length:.3f}m")
            lines.append(f"      miter {board.miter_start:.2f} / "
                         f"{board.miter_end:.2f}   bevel {board.bevel:.3f}")
        total = spec.triangles_needed
        lines.append(f"  x{total} triangles = {total * 3} boards")
    elif step.stage == "deficit":
        for entry in vertex_report():
            lines.append(f"  {entry['triangles']} triangles meet: "
                         f"sum {entry['flat_sum']:.2f} deg, "
                         f"short {entry['deficit']:.2f} deg "
                         f"(x{entry['count']})")
    return lines


def vertex_fans() -> tuple[tuple[int, tuple[float, ...]], ...]:
    """For each interior vertex type, the actual list of triangle corner
    angles that meet there -- used to fan them out flat and show the gap
    that has to close when the dome folds up."""
    geo = build_demo_geometry()
    verts, faces = geo.vertices, geo.hemisphere_faces

    def interior(face, at):
        points = [verts[i] for i in face]
        k = list(face).index(at)
        v1 = points[(k + 1) % 3] - points[k]
        v2 = points[(k + 2) % 3] - points[k]
        cosine = float(np.dot(v1, v2) / np.linalg.norm(v1) / np.linalg.norm(v2))
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))

    at_vertex: dict[int, list[int]] = defaultdict(list)
    for index, face in enumerate(faces):
        for i in face:
            at_vertex[int(i)].append(index)
    picked: dict[int, tuple[float, ...]] = {}
    for vertex, face_list in at_vertex.items():
        if len(face_list) < 5:            # skip the cut base ring
            continue
        picked.setdefault(
            len(face_list),
            tuple(interior(faces[f], vertex) for f in face_list),
        )
    return tuple(sorted(picked.items()))


# ---------------------------------------------------------------------------
# Drawing the jig itself
# ---------------------------------------------------------------------------

PLATE_T = 0.018
FENCE_H = 0.045
FENCE_W = 0.05

STAGE_ORDER = ("shape", "plate", "scribe", "fences", "stops",
               "boards", "loaded", "fastened", "deficit")


def _centred(spec: JigSpec):
    """The jig's flat triangle, moved so its centroid is at the origin."""
    pts = np.array(spec.flat, dtype=np.float64)
    return pts - pts.mean(axis=0)


def _inset_polygon(points: np.ndarray, offset: float) -> np.ndarray:
    """Pull a triangle in by ``offset`` measured perpendicular to each
    side -- the same operation the real boards perform."""
    out = []
    for i in range(3):
        corner = points[i]
        u1 = points[(i + 1) % 3] - corner
        u2 = points[(i + 2) % 3] - corner
        u1 = u1 / np.linalg.norm(u1)
        u2 = u2 / np.linalg.norm(u2)
        bisector = u1 + u2
        bisector = bisector / np.linalg.norm(bisector)
        half = math.acos(float(np.clip(np.dot(u1, u2), -1.0, 1.0))) * 0.5
        out.append(corner + bisector * (offset / max(1e-6, math.sin(half))))
    return np.array(out)


def _slab(batch, poly2d, z0: float, z1: float, color, shade) -> None:
    """A flat polygon extruded in z -- plates, boards, fences, blocks."""
    top = [(float(p[0]), float(p[1]), z1) for p in poly2d]
    bottom = [(float(p[0]), float(p[1]), z0) for p in poly2d]
    n = len(top)
    for i in range(1, n - 1):
        batch.tri(top[0], top[i], top[i + 1], color, (0.0, 0.0, 1.0))
        batch.tri(bottom[0], bottom[i + 1], bottom[i], shade, (0.0, 0.0, -1.0))
    for i in range(n):
        j = (i + 1) % n
        batch.quad(top[i], bottom[i], bottom[j], top[j], shade)


def emit_jig(op, tr, spec: JigSpec, stage: str, t: float, tint_of) -> None:
    """Build the jig scene for one step. Stages are cumulative, so the
    picture grows as you step forward rather than jumping between
    unrelated views."""
    reached = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

    def at_least(name: str) -> bool:
        return reached >= STAGE_ORDER.index(name)

    points = _centred(spec)
    timber = tint_of("timber", 1.0)
    ply = tint_of("moss", 1.0)
    steel = tint_of("steel", 1.0)
    mark = tint_of("amber", 1.0)
    # Fences read as a distinct part, not as shadow -- against a dark
    # scene a charcoal block simply disappears.
    fence_col = tint_of("white", 1.0)

    if stage == "deficit":
        _emit_deficit(op, tr, spec, t, tint_of)
        return

    # The finished shape, always shown faintly as the target.
    if stage == "shape":
        _slab(tr, points, 0.0, 0.004,
              tint_of("glass", 0.5), tint_of("glass", 0.35))

    if at_least("plate"):
        margin = 0.28
        pts = _inset_polygon(points, -margin)
        _slab(op, pts, -PLATE_T, 0.0, ply,
              tuple(c * 0.75 for c in ply[:3]) + (ply[3],))

    if at_least("scribe"):
        # The scribed lines sit exactly on the chord lines, which is where
        # the OUTSIDE face of every finished board must end up.
        inner = _inset_polygon(points, 0.008)
        for i in range(3):
            j = (i + 1) % 3
            _slab(op, np.array([points[i], points[j], inner[j], inner[i]]),
                  0.0, 0.002, mark, mark)

    if at_least("fences"):
        outer = _inset_polygon(points, -FENCE_W)
        for i in range(3):
            j = (i + 1) % 3
            _slab(op, np.array([points[i], points[j], outer[j], outer[i]]),
                  0.0, FENCE_H, fence_col,
                  tuple(c * 0.66 for c in fence_col[:3]) + (fence_col[3],))

    if at_least("stops"):
        # Blocks on the bisector, held back from the very tip so the
        # mitered points are located but never pinched.
        for i in range(3):
            corner = points[i]
            u1 = points[(i + 1) % 3] - corner
            u2 = points[(i + 2) % 3] - corner
            u1 = u1 / np.linalg.norm(u1)
            u2 = u2 / np.linalg.norm(u2)
            bis = u1 + u2
            bis = bis / np.linalg.norm(bis)
            centre = corner + bis * 0.20
            side = np.array([-bis[1], bis[0]])
            block = np.array([
                centre + side * 0.05, centre - side * 0.05,
                centre - side * 0.05 + bis * 0.09,
                centre + side * 0.05 + bis * 0.09,
            ])
            _slab(op, block, 0.0, FENCE_H * 0.8, steel,
                  tuple(c * 0.7 for c in steel[:3]) + (steel[3],))

    if at_least("boards"):
        width = spec.board_width
        inner = _inset_polygon(points, width)
        staged = not at_least("loaded")
        bench_top = -0.22
        stage_y = float(points[:, 1].min()) - 0.55
        for i in range(3):
            j = (i + 1) % 3
            quad = np.array([points[i], points[j], inner[j], inner[i]])
            z0 = 0.0
            if staged:
                # Before loading, the boards lie out flat and parallel the
                # way they come off the saw, so the real cut shape -- a
                # trapezoid, longer on its outer edge, never a rectangle --
                # is plain to see.
                origin = quad[0]
                along = quad[1] - origin
                length = float(np.linalg.norm(along))
                along = along / length
                across = np.array([-along[1], along[0]])
                local = np.array([[float(np.dot(p - origin, along)),
                                   float(np.dot(p - origin, across))]
                                  for p in quad])
                if local[:, 1].mean() < 0.0:      # keep every board same side up
                    local[:, 1] *= -1.0
                local[:, 0] -= length * 0.5
                local[:, 1] += stage_y - i * (width + 0.10)
                quad = local
                z0 = bench_top
            _slab(op, quad, z0, z0 + spec.board_thickness, timber,
                  tuple(c * 0.78 for c in timber[:3]) + (timber[3],))

    if at_least("fastened"):
        inner = _inset_polygon(points, spec.board_width)
        for i in range(3):
            corner = points[i]
            plate_pts = _inset_polygon(
                np.array([points[i], points[(i + 1) % 3], points[(i + 2) % 3]]),
                0.03,
            )
            centre = (corner * 0.72 + plate_pts[0] * 0.28)
            for k in range(3):
                angle = TAU_LOCAL * k / 3 + 0.4
                at = centre + np.array([math.cos(angle), math.sin(angle)]) * 0.055
                op.cylinder(
                    (at[0], at[1], spec.board_thickness - 0.004),
                    (at[0], at[1], spec.board_thickness + 0.012),
                    0.009, steel, sides=6,
                )


TAU_LOCAL = math.tau


def _emit_deficit(op, tr, spec: JigSpec, t: float, tint_of) -> None:
    """Fan the triangles that meet at one vertex out flat, so the gap that
    has to close when the dome folds is directly visible."""
    fans = vertex_fans()
    timber = tint_of("timber", 1.0)
    warn = tint_of("amber", 0.55)
    reach = 1.5
    for row, (count, angles) in enumerate(fans):
        origin = np.array([0.0, (row - 0.5) * -3.6])
        cursor = 0.0
        for index, angle in enumerate(angles):
            a0 = math.radians(cursor)
            a1 = math.radians(cursor + angle)
            p0 = origin
            p1 = origin + np.array([math.cos(a0), math.sin(a0)]) * reach
            p2 = origin + np.array([math.cos(a1), math.sin(a1)]) * reach
            shade = 1.0 - 0.06 * (index % 3)
            color = tuple(c * shade for c in timber[:3]) + (timber[3],)
            _slab(op, np.array([p0, p1, p2]), 0.0, 0.03, color, color)
            cursor += angle
        # The wedge that is missing -- the angular deficit.
        a0 = math.radians(cursor)
        a1 = math.radians(360.0)
        p0 = origin
        p1 = origin + np.array([math.cos(a0), math.sin(a0)]) * reach
        p2 = origin + np.array([math.cos(a1), math.sin(a1)]) * reach
        _slab(tr, np.array([p0, p1, p2]), 0.0, 0.05, warn, warn)


def verify() -> None:
    """Check the cut list against the real 3D dome faces.

    The jig numbers are derived from the geometry's own class tables; this
    measures the same quantities straight off the assembled hemisphere and
    insists they match. If the two ever drift apart, this raises rather
    than quietly shipping a jig that builds the wrong triangle.
    """
    geo = build_demo_geometry()
    verts = geo.vertices
    radius, width = 4.2, 0.089
    specs = {spec.key: spec for spec in jig_specs(radius, width)}
    class_by_edge = {tuple(sorted(edge)): name
                     for edge, name in zip(geo.edges, geo.edge_class_by_edge)}

    seen = set()
    for face in geo.hemisphere_faces:
        names = [class_by_edge[tuple(sorted((int(face[i]), int(face[(i + 1) % 3]))))]
                 for i in range(3)]
        key = "equilateral" if len(set(names)) == 1 else "isosceles"
        spec = specs[key]
        points = [verts[i] * radius for i in face]
        # Measured side lengths must match the spec's chords as a multiset.
        measured = sorted(float(np.linalg.norm(points[(i + 1) % 3] - points[i]))
                          for i in range(3))
        expected = sorted(spec.chords)
        for got, want in zip(measured, expected):
            assert abs(got - want) < 1e-9, (key, got, want)
        # Measured interior angles must match the spec's corner angles.
        angles = []
        for i in range(3):
            v1 = points[(i + 1) % 3] - points[i]
            v2 = points[(i + 2) % 3] - points[i]
            cosine = float(np.dot(v1, v2) / np.linalg.norm(v1) / np.linalg.norm(v2))
            angles.append(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
        for got, want in zip(sorted(angles), sorted(spec.corner_angles)):
            assert abs(got - want) < 1e-6, (key, got, want)
        seen.add(key)
    assert seen == {"equilateral", "isosceles"}, seen

    # Interior angles of any triangle must close to 180.
    for spec in specs.values():
        assert abs(sum(spec.corner_angles) - 180.0) < 1e-6, spec.corner_angles
        # A board can never be longer on the inside than the outside.
        for board in spec.boards:
            assert board.inner_length < board.outer_length, board
            assert board.inner_length > 0.0, board

        # Side i runs from corner i to corner i+1, so each board's two
        # miters must be built from exactly those two corners. Getting
        # this mapping wrong is silent -- every number still looks
        # plausible -- so it is checked directly.
        for i, board in enumerate(spec.boards):
            start = spec.corner_angles[i]
            end = spec.corner_angles[(i + 1) % 3]
            assert abs(board.miter_start - (90.0 - start / 2.0)) < 1e-9, (i, board)
            assert abs(board.miter_end - (90.0 - end / 2.0)) < 1e-9, (i, board)

        # The classic triangle law: the longest side faces the largest
        # angle. This is what catches a rotated corner mapping.
        order_sides = sorted(range(3), key=lambda i: spec.chords[i])
        order_angles = sorted(
            range(3), key=lambda i: spec.corner_angles[(i + 2) % 3]
        )
        assert order_sides == order_angles, (spec.key, spec.chords,
                                             spec.corner_angles)

        # Equal sides must carry equal opposite angles, so a symmetric
        # board really does get the same miter at both ends.
        for i, board in enumerate(spec.boards):
            for j, other in enumerate(spec.boards):
                if i < j and abs(board.outer_length - other.outer_length) < 1e-12:
                    assert abs(board.inner_length - other.inner_length) < 1e-9, (
                        spec.key, "equal sides must trim equally", board, other)

    counts = {spec.key: spec.triangles_needed for spec in specs.values()}
    assert counts["equilateral"] + counts["isosceles"] == 40, counts
