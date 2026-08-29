"""Pure mathematical model for zome (zonohedral) construction.

A zome is not a piece of a sphere.  It is a **zonohedron**: the shape you
get by sweeping a solid along a small set of directions, one after
another.  That single idea forces every property the lesson teaches, and
this module derives all of them rather than quoting them.

Why every face is a parallelogram
---------------------------------
Sweep a point along direction ``a`` and you draw a segment.  Sweep that
segment along ``b`` and you sweep out a parallelogram -- necessarily flat,
because two directions define a plane.  Do it for a whole star of
directions and the outer surface of the result is built entirely from
those parallelograms.  Make every direction the same length and every
parallelogram becomes a rhombus, which is why a zome can be framed from
**one strut length**.

Why the top comes to a point
----------------------------
The far corner of the sweep is reached by travelling along *every*
direction in the star.  Exactly one vertex does that, so the roof closes
on a single point where one face per direction meets.

The two zomes the lesson builds
-------------------------------
``polar_zonohedron(n, pitch)``
    The classic pointed zome.  Its vertices fall on perfectly level
    rings, so it can be sawn off flat at any height.

``golden_zonohedron()``
    The rhombic triacontahedron: thirty identical golden rhombi from six
    directions.  One strut, one panel -- but no level ring to cut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np

from .geometry import PHI, icosahedron_north_rotation, normalize


# Zonohedron corners are reached by adding the same handful of vectors in
# different orders, so identical corners agree to machine precision and a
# tight key is safe.
POINT_KEY_SCALE = 1.0e9
LENGTH_TOLERANCE = 1.0e-9


# ----------------------------------------------------------------------
# The generic construction
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RhombusClass:
    """One measured panel shape."""

    name: str
    separation: int
    count: int
    dome_count: int
    side_lengths: tuple[float, float]
    acute_deg: float
    obtuse_deg: float
    short_diagonal: float
    long_diagonal: float
    area: float

    @property
    def diagonal_ratio(self) -> float:
        return self.long_diagonal / self.short_diagonal

    @property
    def is_rhombus(self) -> bool:
        """True when all four sides match, so one strut length fits it."""
        return abs(self.side_lengths[0] - self.side_lengths[1]) <= LENGTH_TOLERANCE


@dataclass(frozen=True)
class HubClass:
    """One measured joint: how many struts arrive, and how they splay."""

    name: str
    strut_count: int
    hub_count: int
    angles_deg: tuple[float, ...]
    angle_sum_deg: float

    @property
    def deficit_deg(self) -> float:
        """Angle missing at this joint -- what makes the surface curve."""
        return 360.0 - self.angle_sum_deg


@dataclass(frozen=True)
class LevelCut:
    """What a horizontal saw cut through the frame actually meets.

    A zonohedron has no horizontal struts at all -- every strut climbs
    from one ring of hubs to the next -- so a level floor line always
    crosses struts in mid-span.  The question that decides whether the
    job is easy is how many *different* cuts that takes.
    """

    height: float
    strut_count: int
    fractions: tuple[float, ...]

    @property
    def distinct_cuts(self) -> int:
        return len(self.fractions)

    @property
    def one_repeated_cut(self) -> bool:
        """True when every strut the plane meets is cut at the same place."""
        return self.distinct_cuts == 1


@dataclass(frozen=True)
class Zome:
    """A finished zonohedron, measured."""

    name: str
    generators: np.ndarray
    vertices: np.ndarray
    faces: tuple[tuple[int, int, int, int], ...]
    edges: tuple[tuple[int, int], ...]
    face_separation: tuple[int, ...]
    rhombus_classes: tuple[RhombusClass, ...]
    rhombus_class_of: tuple[str, ...]
    hub_classes: tuple[HubClass, ...]
    strut_length: float
    strut_lengths: tuple[float, ...]
    pitch_deg: float
    dome_faces: tuple[int, ...]
    level_rings: tuple[float, ...]
    polar: bool

    # -- counts ------------------------------------------------------
    @property
    def generator_count(self) -> int:
        return len(self.generators)

    @property
    def euler(self) -> int:
        return len(self.vertices) - len(self.edges) + len(self.faces)

    @property
    def panel_shapes(self) -> int:
        return len(self.rhombus_classes)

    @property
    def one_strut(self) -> bool:
        """True when the whole frame is cut from a single length."""
        return len(self.strut_lengths) == 1

    @property
    def apex_index(self) -> int:
        return int(np.argmax(self.vertices[:, 2]))

    @property
    def base_index(self) -> int:
        return int(np.argmin(self.vertices[:, 2]))

    @property
    def apex_faces(self) -> tuple[int, ...]:
        apex = self.apex_index
        return tuple(
            index for index, face in enumerate(self.faces) if apex in face
        )

    @property
    def apex_angle_sum(self) -> float:
        """Sum of the panel corners that meet at the point of the roof."""
        apex = self.apex_index
        total = 0.0
        for face in self.faces:
            if apex not in face:
                continue
            position = face.index(apex)
            previous = self.vertices[face[(position - 1) % 4]] - self.vertices[apex]
            following = self.vertices[face[(position + 1) % 4]] - self.vertices[apex]
            cosine = float(np.dot(normalize(previous), normalize(following)))
            total += math.degrees(math.acos(float(np.clip(cosine, -1.0, 1.0))))
        return total

    @property
    def height(self) -> float:
        return float(self.vertices[:, 2].max() - self.vertices[:, 2].min())

    @property
    def widest_radius(self) -> float:
        return float(np.max(np.linalg.norm(self.vertices[:, :2], axis=1)))

    # -- the buildable half ------------------------------------------
    @property
    def boundary_edges(self) -> tuple[tuple[int, int], ...]:
        counts: dict[tuple[int, int], int] = {}
        for face_index in self.dome_faces:
            face = self.faces[face_index]
            for position in range(4):
                a, b = face[position], face[(position + 1) % 4]
                key = (a, b) if a < b else (b, a)
                counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(key for key, count in counts.items() if count == 1))

    @property
    def rim_vertices(self) -> tuple[int, ...]:
        rim = {index for edge in self.boundary_edges for index in edge}
        return tuple(sorted(rim, key=lambda index: math.atan2(
            float(self.vertices[index][1]), float(self.vertices[index][0])
        )))

    @property
    def rim_wobble(self) -> float:
        """Depth of the rim zigzag.

        Never zero for any zonohedron: with no horizontal struts, a rim
        that follows the frame has to step between two rings.  What makes
        a polar zome easy is not a flat rim, it is that the zigzag is
        perfectly regular -- see :meth:`level_cut`.
        """
        ring = self.rim_vertices
        if not ring:
            return 0.0
        heights = [float(self.vertices[index][2]) for index in ring]
        return max(heights) - min(heights)

    @property
    def rim_levels(self) -> tuple[float, ...]:
        """The distinct heights the rim corners sit at."""
        ring = self.rim_vertices
        found: list[float] = []
        for index in ring:
            height = float(self.vertices[index][2])
            if not any(abs(height - value) <= 1e-9 for value in found):
                found.append(height)
        return tuple(sorted(found))

    def level_cut(self, height: float) -> LevelCut:
        """Measure the saw cut a level floor line makes through the frame."""
        fractions: list[float] = []
        crossed = 0
        for a, b in self.edges:
            low, high = sorted(
                (float(self.vertices[a][2]), float(self.vertices[b][2]))
            )
            if not (low < height - 1e-9 and high > height + 1e-9):
                continue
            crossed += 1
            fraction = (height - low) / (high - low)
            if not any(abs(fraction - value) <= 1e-9 for value in fractions):
                fractions.append(fraction)
        return LevelCut(height, crossed, tuple(sorted(fractions)))

    @property
    def rim_height(self) -> float:
        ring = self.rim_vertices
        return min(float(self.vertices[index][2]) for index in ring) if ring else 0.0

    @property
    def rim_radius(self) -> float:
        ring = self.rim_vertices
        if not ring:
            return 0.0
        return float(np.mean([
            float(np.linalg.norm(self.vertices[index][:2])) for index in ring
        ]))

    @property
    def dome_height(self) -> float:
        return float(self.vertices[:, 2].max()) - self.rim_height

    @property
    def dome_edges(self) -> tuple[tuple[int, int], ...]:
        kept: set[tuple[int, int]] = set()
        for face_index in self.dome_faces:
            face = self.faces[face_index]
            for position in range(4):
                a, b = face[position], face[(position + 1) % 4]
                kept.add((a, b) if a < b else (b, a))
        return tuple(sorted(kept))

    @property
    def floor_area(self) -> float:
        """Area enclosed by the rim, taken as a regular polygon on it."""
        ring = self.rim_vertices
        if len(ring) < 3:
            return 0.0
        total = 0.0
        centre = np.array([0.0, 0.0])
        for index in range(len(ring)):
            a = self.vertices[ring[index]][:2] - centre
            b = self.vertices[ring[(index + 1) % len(ring)]][:2] - centre
            total += 0.5 * abs(float(a[0] * b[1] - a[1] * b[0]))
        return total


def _point_key(point: np.ndarray) -> tuple[int, int, int]:
    return tuple(int(round(float(value) * POINT_KEY_SCALE)) for value in point)


def zonohedron_faces(
    generators: np.ndarray,
) -> tuple[np.ndarray, tuple[tuple[int, int, int, int], ...], tuple[tuple[int, int], ...]]:
    """Build every rhombic face of the zonohedron spanned by *generators*.

    For each pair of directions ``(i, j)`` the surface has exactly two
    parallel faces, one on each side.  Their common plane normal is
    ``g_i x g_j``; the face centre is reached by adding every *other*
    direction with the sign that pushes it toward that side.  The four
    corners are then ``centre +- g_i +- g_j``, which is a parallelogram by
    construction and never needs a convex-hull library.
    """
    count = len(generators)
    if count < 3:
        raise ValueError("a zonohedron needs at least three directions")
    index_of: dict[tuple[int, int, int], int] = {}
    points: list[np.ndarray] = []

    def register(point: np.ndarray) -> int:
        key = _point_key(point)
        if key not in index_of:
            index_of[key] = len(points)
            points.append(np.asarray(point, dtype=np.float64))
        return index_of[key]

    faces: list[tuple[int, int, int, int]] = []
    for i in range(count):
        for j in range(i + 1, count):
            normal = np.cross(generators[i], generators[j])
            if float(np.linalg.norm(normal)) <= 1e-12:
                raise ValueError("two directions are parallel; that is not a zonohedron")
            base = np.zeros(3)
            for k in range(count):
                if k in (i, j):
                    continue
                projection = float(np.dot(normal, generators[k]))
                if abs(projection) <= 1e-12:
                    raise ValueError(
                        "three directions are coplanar; the faces stop being rhombi"
                    )
                base += math.copysign(1.0, projection) * generators[k]
            for side in (1.0, -1.0):
                centre = base * side
                corners = (
                    centre - generators[i] - generators[j],
                    centre + generators[i] - generators[j],
                    centre + generators[i] + generators[j],
                    centre - generators[i] + generators[j],
                )
                faces.append(tuple(register(corner) for corner in corners))

    vertices = np.asarray(points, dtype=np.float64)
    edge_set: set[tuple[int, int]] = set()
    for face in faces:
        for position in range(4):
            a, b = face[position], face[(position + 1) % 4]
            edge_set.add((a, b) if a < b else (b, a))
    return vertices, tuple(faces), tuple(sorted(edge_set))


def _face_separation(generators: np.ndarray, i: int, j: int) -> int:
    """How many steps apart two directions sit around the star."""
    count = len(generators)
    step = (j - i) % count
    return min(step, count - step)


def _measure(
    name: str,
    generators: np.ndarray,
    pitch_deg: float,
    polar: bool,
    cut_z: float | None,
) -> Zome:
    vertices, faces, edges = zonohedron_faces(generators)
    count = len(generators)

    # Recover which pair of directions made each face, in the same order
    # zonohedron_faces emitted them.
    pair_of_face: list[tuple[int, int]] = []
    for i in range(count):
        for j in range(i + 1, count):
            pair_of_face.extend([(i, j), (i, j)])
    separations = tuple(
        _face_separation(generators, i, j) for i, j in pair_of_face
    )

    levels: list[float] = []
    for height in sorted(float(value) for value in vertices[:, 2]):
        if not levels or abs(height - levels[-1]) > 1e-9:
            levels.append(height)
    if cut_z is None:
        # Stand the building on the ring where the zome is widest: that is
        # the lowest cut that leaves no overhanging wall.
        radius_at = [
            max(
                float(np.linalg.norm(vertex[:2]))
                for vertex in vertices
                if abs(float(vertex[2]) - level) <= 1e-9
            )
            for level in levels
        ]
        cut_z = levels[int(np.argmax(radius_at))]
    # Keep whole panels only: a panel is in the building when none of its
    # corners falls below the cut.
    dome_faces = tuple(
        index for index, face in enumerate(faces)
        if min(float(vertices[corner][2]) for corner in face) >= cut_z - 1e-9
    )
    dome_face_set = set(dome_faces)

    strut_values: list[float] = []
    for a, b in edges:
        length = float(np.linalg.norm(vertices[a] - vertices[b]))
        for existing in strut_values:
            if abs(length - existing) <= LENGTH_TOLERANCE:
                break
        else:
            strut_values.append(length)
    strut_values.sort()

    # Panels group by their measured shape, not by which pair made them.
    groups: dict[tuple, list[int]] = {}
    for face_index, face in enumerate(faces):
        points = vertices[list(face)]
        sides = tuple(sorted(
            round(float(np.linalg.norm(points[k] - points[(k + 1) % 4])), 9)
            for k in range(4)
        ))
        diagonals = tuple(sorted((
            round(float(np.linalg.norm(points[0] - points[2])), 9),
            round(float(np.linalg.norm(points[1] - points[3])), 9),
        )))
        groups.setdefault((sides, diagonals), []).append(face_index)

    rhombus_classes: list[RhombusClass] = []
    rhombus_class_of: list[str] = ["" for _ in faces]
    for order, (signature, members) in enumerate(
        sorted(groups.items(), key=lambda item: item[0][1][0])
    ):
        label = f"R{order + 1}"
        sides, diagonals = signature
        points = vertices[list(faces[members[0]])]
        first = points[1] - points[0]
        second = points[3] - points[0]
        cosine = float(np.dot(normalize(first), normalize(second)))
        corner = math.degrees(math.acos(float(np.clip(cosine, -1.0, 1.0))))
        acute = min(corner, 180.0 - corner)
        for member in members:
            rhombus_class_of[member] = label
        rhombus_classes.append(RhombusClass(
            name=label,
            separation=separations[members[0]],
            count=len(members),
            dome_count=sum(1 for member in members if member in dome_face_set),
            side_lengths=(min(sides), max(sides)),
            acute_deg=acute,
            obtuse_deg=180.0 - acute,
            short_diagonal=diagonals[0],
            long_diagonal=diagonals[1],
            area=0.5 * diagonals[0] * diagonals[1],
        ))

    # Hubs group by how many struts arrive and at what angles between them.
    incident: dict[int, list[int]] = {index: [] for index in range(len(vertices))}
    for a, b in edges:
        incident[a].append(b)
        incident[b].append(a)
    corner_angle_total: dict[int, float] = {index: 0.0 for index in range(len(vertices))}
    for face in faces:
        points = vertices[list(face)]
        for position in range(4):
            previous = points[(position - 1) % 4] - points[position]
            following = points[(position + 1) % 4] - points[position]
            cosine = float(np.dot(normalize(previous), normalize(following)))
            corner_angle_total[face[position]] += math.degrees(
                math.acos(float(np.clip(cosine, -1.0, 1.0)))
            )
    hub_groups: dict[tuple, list[int]] = {}
    for index, neighbours in incident.items():
        splay: list[float] = []
        for first in range(len(neighbours)):
            for second in range(first + 1, len(neighbours)):
                a = normalize(vertices[neighbours[first]] - vertices[index])
                b = normalize(vertices[neighbours[second]] - vertices[index])
                splay.append(round(math.degrees(math.acos(
                    float(np.clip(float(np.dot(a, b)), -1.0, 1.0))
                )), 6))
        key = (len(neighbours), tuple(sorted(splay)),
               round(corner_angle_total[index], 6))
        hub_groups.setdefault(key, []).append(index)
    hub_classes: list[HubClass] = []
    for order, (key, members) in enumerate(
        sorted(hub_groups.items(), key=lambda item: (-item[0][0], item[0][2]))
    ):
        hub_classes.append(HubClass(
            name=f"H{order + 1}",
            strut_count=key[0],
            hub_count=len(members),
            angles_deg=key[1],
            angle_sum_deg=key[2],
        ))

    return Zome(
        name=name,
        generators=generators,
        vertices=vertices,
        faces=faces,
        edges=edges,
        face_separation=separations,
        rhombus_classes=tuple(rhombus_classes),
        rhombus_class_of=tuple(rhombus_class_of),
        hub_classes=tuple(hub_classes),
        strut_length=strut_values[0],
        strut_lengths=tuple(strut_values),
        pitch_deg=pitch_deg,
        dome_faces=dome_faces,
        level_rings=tuple(levels),
        polar=polar,
    )


# ----------------------------------------------------------------------
# The two zomes
# ----------------------------------------------------------------------

def polar_generators(count: int, pitch_deg: float) -> np.ndarray:
    """``count`` equal directions evenly spaced around a cone.

    ``pitch_deg`` is measured from the vertical axis: a small pitch gives
    a tall spire, a large pitch a low saucer.
    """
    pitch = math.radians(pitch_deg)
    return np.array([
        [
            math.sin(pitch) * math.cos(math.tau * index / count),
            math.sin(pitch) * math.sin(math.tau * index / count),
            math.cos(pitch),
        ]
        for index in range(count)
    ], dtype=np.float64)


@lru_cache(maxsize=16)
def polar_zonohedron(count: int = 6, pitch_deg: float = 54.0) -> Zome:
    """The classic pointed zome: a star of equal directions round a cone.

    Every vertex height is a whole number of ``cos(pitch)`` steps, so the
    corners land on perfectly level rings and the wall can be sawn off
    flat wherever you like.
    """
    generators = polar_generators(count, pitch_deg)
    return _measure(
        f"{count}-fold polar zome", generators, pitch_deg, True, None
    )


@lru_cache(maxsize=1)
def golden_zonohedron() -> Zome:
    """The rhombic triacontahedron: thirty identical golden rhombi.

    Its six directions are the icosahedron's five-fold axes, which is why
    the faces all come out the same and their diagonals land on phi.  One
    strut, one panel -- and, as the lesson shows, no level ring anywhere.
    """
    raw = np.array([
        [-1.0, PHI, 0.0], [1.0, PHI, 0.0],
        [0.0, -1.0, PHI], [0.0, 1.0, PHI],
        [PHI, 0.0, -1.0], [PHI, 0.0, 1.0],
    ], dtype=np.float64)
    generators = np.array([
        normalize(vector) for vector in raw @ icosahedron_north_rotation().T
    ])
    return _measure("Rhombic triacontahedron", generators, float("nan"), False, None)


# ----------------------------------------------------------------------
# Turning a zome into a shopping list
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ZomeBuild:
    """A zome scaled so its struts are a chosen real length."""

    zome: Zome
    strut_length: float
    connector_deduction: float = 0.0

    @property
    def scale(self) -> float:
        return self.strut_length / self.zome.strut_length

    @property
    def height(self) -> float:
        return self.zome.dome_height * self.scale

    @property
    def full_height(self) -> float:
        return self.zome.height * self.scale

    @property
    def floor_radius(self) -> float:
        return self.zome.rim_radius * self.scale

    @property
    def floor_area(self) -> float:
        return self.zome.floor_area * self.scale**2

    @property
    def widest_diameter(self) -> float:
        return 2.0 * self.zome.widest_radius * self.scale

    def strut_table(self) -> tuple[tuple[str, int, float, float], ...]:
        counts: dict[float, int] = {}
        for a, b in self.zome.dome_edges:
            length = float(np.linalg.norm(
                self.zome.vertices[a] - self.zome.vertices[b]
            ))
            for existing in counts:
                if abs(length - existing) <= LENGTH_TOLERANCE:
                    counts[existing] += 1
                    break
            else:
                counts[length] = 1
        rows = []
        for order, (length, count) in enumerate(sorted(counts.items())):
            centre = length * self.scale
            rows.append((
                f"S{order + 1}" if len(counts) > 1 else "STRUT",
                count,
                centre,
                centre - self.connector_deduction,
            ))
        return tuple(rows)

    def panel_table(self) -> tuple[tuple[str, int, float, float, float, float], ...]:
        """(class, dome count, acute angle, short diag, long diag, area)."""
        return tuple(
            (
                item.name,
                item.dome_count,
                item.acute_deg,
                item.short_diagonal * self.scale,
                item.long_diagonal * self.scale,
                item.area * self.scale**2,
            )
            for item in self.zome.rhombus_classes
        )


def zome_report(strut_length: float = 48.0, connector_deduction: float = 0.0) -> str:
    """A portable, plain-text audit of everything the zome lesson claims."""
    lines = ["ZOME / ZONOHEDRON MASTERCLASS - CALCULATION AUDIT", ""]
    models = [polar_zonohedron(5, 54.0), polar_zonohedron(6, 54.0),
              polar_zonohedron(7, 54.0), golden_zonohedron()]
    for zome in models:
        build = ZomeBuild(zome, strut_length, connector_deduction)
        level = zome.level_cut(
            (zome.rim_levels[0] + zome.rim_levels[-1]) * 0.5
        )
        lines.extend([
            f"--- {zome.name} ---",
            f"  directions           {zome.generator_count}"
            + (f"   pitch {zome.pitch_deg:.3f} deg" if zome.polar else ""),
            f"  V/E/F                {len(zome.vertices)}/{len(zome.edges)}/"
            f"{len(zome.faces)}   Euler {zome.euler}",
            f"  predicted V/E/F      {zome.generator_count**2 - zome.generator_count + 2}"
            f"/{2 * zome.generator_count * (zome.generator_count - 1)}"
            f"/{zome.generator_count * (zome.generator_count - 1)}",
            f"  panel shapes         {zome.panel_shapes}",
            f"  strut lengths        {len(zome.strut_lengths)}"
            f"   (one strut: {zome.one_strut})",
            f"  hub types            {len(zome.hub_classes)}",
            f"  level rings          {len(zome.level_rings)}",
            f"  apex corners meet    {len(zome.apex_faces)} panels, "
            f"{zome.apex_angle_sum:.4f} deg used, "
            f"{360.0 - zome.apex_angle_sum:.4f} deg missing",
            f"  roof half            {len(zome.dome_faces)} panels, "
            f"{len(zome.dome_edges)} struts, rim {len(zome.rim_vertices)} corners",
            f"  rim zigzag           {zome.rim_wobble:.6f} across "
            f"{len(zome.rim_levels)} heights",
            f"  level floor cut      {level.strut_count} struts crossed, "
            f"{level.distinct_cuts} distinct cut(s)"
            f"   (one repeated cut: {level.one_repeated_cut})",
            f"  at strut {strut_length:g}: height {build.height:.3f}, "
            f"floor radius {build.floor_radius:.3f}, "
            f"floor area {build.floor_area:.1f}",
        ])
        for name, count, centre, cut in build.strut_table():
            lines.append(
                f"    strut {name:<6} x{count:<4} centre {centre:9.4f}"
                f"   cut {cut:9.4f}"
            )
        for name, count, acute, short, long, area in build.panel_table():
            lines.append(
                f"    panel {name:<4} x{count:<4} acute {acute:8.4f} deg"
                f"   diagonals {short:8.3f} x {long:8.3f}"
                f"   area {area:10.3f}"
            )
        for hub in zome.hub_classes:
            lines.append(
                f"    hub   {hub.name:<4} x{hub.hub_count:<4} "
                f"{hub.strut_count} struts   corner sum "
                f"{hub.angle_sum_deg:8.4f} deg   deficit {hub.deficit_deg:7.4f} deg"
            )
        lines.append("")
    return "\n".join(lines)


def validate_zome_geometry() -> None:
    """Prove the models before any of their numbers reach a screen."""
    for count in (4, 5, 6, 7, 8, 9):
        zome = polar_zonohedron(count, 54.0)
        # Minkowski counts, derived: F = n(n-1), V = n(n-1)+2, E = 2n(n-1).
        assert len(zome.faces) == count * (count - 1), (count, len(zome.faces))
        assert len(zome.vertices) == count * (count - 1) + 2, (count, len(zome.vertices))
        assert len(zome.edges) == 2 * count * (count - 1), (count, len(zome.edges))
        assert zome.euler == 2, (count, zome.euler)
        # The whole promise of a zome: one strut length, flat panels.
        assert zome.one_strut, (count, zome.strut_lengths)
        assert all(item.is_rhombus for item in zome.rhombus_classes)
        # Directions s and n-s apart give the same rhombus, so shapes pair up.
        assert zome.panel_shapes == math.ceil((count - 1) / 2), (
            count, zome.panel_shapes
        )
        # The roof closes on exactly one point, with one panel per direction.
        assert len(zome.apex_faces) == count, (count, len(zome.apex_faces))
        assert zome.apex_angle_sum < 360.0, (count, zome.apex_angle_sum)
        # Polar zome corners land on level rings: n+1 heights, evenly spaced.
        assert len(zome.level_rings) == count + 1, (count, len(zome.level_rings))
        steps = [
            zome.level_rings[index + 1] - zome.level_rings[index]
            for index in range(count)
        ]
        assert max(steps) - min(steps) < 1e-9, (count, steps)
        # No zonohedron has a horizontal strut, so the rim always steps
        # between two rings -- but on a polar zome it steps exactly once.
        assert len(zome.rim_levels) == 2, (count, zome.rim_levels)
        assert abs(zome.rim_wobble - steps[0]) < 1e-9, (count, zome.rim_wobble)
        # And a level floor line meets every strut it crosses at the same
        # place -- at *any* height, not just a lucky one.  That is the
        # property that makes the bottom row one repeated cut.
        for gap in range(len(zome.level_rings) - 1):
            middle = (zome.level_rings[gap] + zome.level_rings[gap + 1]) * 0.5
            cut = zome.level_cut(middle)
            assert cut.one_repeated_cut, (count, gap, cut.fractions)
            # Two struts climb out of every hub on a middle ring, one out
            # of each on the rings beside the two points.
            assert cut.strut_count in (count, 2 * count), (
                count, gap, cut.strut_count
            )

    # Pitch is a free design knob and never costs a second strut length.
    for pitch in (30.0, 45.0, 54.0, 68.0):
        zome = polar_zonohedron(6, pitch)
        assert zome.one_strut, (pitch, zome.strut_lengths)
        assert zome.level_cut(zome.rim_levels[0] + zome.rim_wobble * 0.5)            .one_repeated_cut
    tall = polar_zonohedron(6, 30.0)
    wide = polar_zonohedron(6, 68.0)
    assert tall.height > wide.height
    assert tall.widest_radius < wide.widest_radius

    golden = golden_zonohedron()
    assert len(golden.faces) == 30, len(golden.faces)
    assert len(golden.vertices) == 32, len(golden.vertices)
    assert len(golden.edges) == 60, len(golden.edges)
    assert golden.euler == 2
    assert golden.one_strut
    # Thirty faces, all one shape, and that shape's diagonals are phi apart.
    assert golden.panel_shapes == 1, golden.panel_shapes
    assert abs(golden.rhombus_classes[0].diagonal_ratio - PHI) < 1e-9, (
        golden.rhombus_classes[0].diagonal_ratio
    )
    # The famous one-panel zome pays for its single panel at the floor.
    # Its hub rings are not evenly spaced, and no level line through it is
    # a single repeated cut -- unlike every polar zome above.
    golden_steps = [
        golden.level_rings[index + 1] - golden.level_rings[index]
        for index in range(len(golden.level_rings) - 1)
    ]
    assert max(golden_steps) - min(golden_steps) > 1e-6, golden_steps
    golden_gaps = [
        golden.level_cut(
            (golden.level_rings[gap] + golden.level_rings[gap + 1]) * 0.5
        )
        for gap in range(len(golden.level_rings) - 1)
    ]
    # Its seven bands are not alike: the two caps at each end do cut
    # uniformly, but the three bands in the middle -- exactly where a
    # floor would go -- each need two settings on the saw.
    uniform = [cut.one_repeated_cut for cut in golden_gaps]
    assert uniform == [True, True, False, False, False, True, True], uniform

    build = ZomeBuild(polar_zonohedron(6, 54.0), 48.0, 1.5)
    for _, _, centre, cut in build.strut_table():
        assert abs((centre - cut) - 1.5) < 1e-9
    assert build.height > 0.0 and build.floor_area > 0.0
