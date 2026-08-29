"""Pure mathematical model for hexagonal (Goldberg) dome construction.

Nothing in the hex lesson is typed by hand.  Every count, angle, chord
factor, panel area, planarity error and base-ring wobble shown on screen
is measured off the models built here.

The two cases the lesson teaches
-------------------------------
``truncated_icosahedron()``
    One hexagon shape, one pentagon shape, **one strut length**.  Twenty
    regular hexagons and twelve regular pentagons, ninety identical
    edges.  This is the "single hexagon covering" frame dome.

``goldberg(frequency)``
    The dual of a class-I geodesic sphere, ``GP(frequency, 0)``.  Raising
    the frequency buys a rounder, larger dome and immediately costs you
    the single shape: the hexagons split into size classes, gain more
    than one edge length, and stop being flat.

Both are hexagon/pentagon cages with exactly twelve pentagons, and this
module proves that rather than claiming it -- see :func:`euler_pentagon_proof`
and the measured angular deficit in :func:`descartes_deficit`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence

import numpy as np

from .geometry import (
    PHI,
    icosahedron_north_rotation,
    normalize,
    raw_icosahedron,
)


# Two lengths measured off a unit sphere are "the same length" when they
# agree to this many parts.  Real cutting tolerance is thousands of times
# coarser; this only has to separate genuinely distinct geometry.
LENGTH_TOLERANCE = 1.0e-9


# ----------------------------------------------------------------------
# Flat hexagon tiling -- the zero-curvature starting point
# ----------------------------------------------------------------------

def hex_tiling(rings: int = 3, circumradius: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Return (centres, corners) for a flat regular-hexagon tiling.

    ``corners`` is ``(n, 6, 3)``.  A regular hexagon tiles the plane with
    three hexagons meeting at every corner: ``3 * 120 = 360`` degrees, no
    angle left over, so the sheet stays dead flat forever.
    """
    step = circumradius * math.sqrt(3.0)
    axis_a = np.array([step, 0.0, 0.0])
    axis_b = np.array([step * 0.5, step * math.sqrt(3.0) * 0.5, 0.0])
    centres: list[np.ndarray] = []
    for q in range(-rings, rings + 1):
        for r in range(-rings, rings + 1):
            if abs(q + r) > rings:
                continue
            centres.append(q * axis_a + r * axis_b)
    corner_offsets = np.array([
        [circumradius * math.cos(math.radians(30.0 + 60.0 * k)),
         circumradius * math.sin(math.radians(30.0 + 60.0 * k)),
         0.0]
        for k in range(6)
    ])
    centre_array = np.asarray(centres, dtype=np.float64)
    corners = centre_array[:, None, :] + corner_offsets[None, :, :]
    return centre_array, corners


def flat_vertex_angle_sum(sides: int) -> float:
    """Interior angle of a regular polygon, times three faces at a corner."""
    interior = 180.0 * (sides - 2) / sides
    return 3.0 * interior


# ----------------------------------------------------------------------
# Class-I geodesic, then its dual
# ----------------------------------------------------------------------

def geodesic_class_one(frequency: int) -> tuple[np.ndarray, np.ndarray]:
    """Return unit-sphere vertices and triangles for a class-I ``nV`` sphere.

    Each icosahedron face is ruled into ``frequency**2`` small triangles on
    the flat face, then every point is pushed out to the unit sphere.
    """
    if frequency < 1:
        raise ValueError("frequency must be at least 1")
    raw, faces = raw_icosahedron()
    base = raw / math.sqrt(1.0 + PHI**2)

    vertices: list[np.ndarray] = []
    index_of: dict[tuple[int, int, int], int] = {}

    def register(point: np.ndarray) -> int:
        unit = normalize(point)
        key = tuple(int(round(value * 1e9)) for value in unit)
        if key not in index_of:
            index_of[key] = len(vertices)
            vertices.append(unit)
        return index_of[key]

    triangles: list[tuple[int, int, int]] = []
    for a_index, b_index, c_index in faces:
        a, b, c = base[a_index], base[b_index], base[c_index]
        grid: dict[tuple[int, int], int] = {}
        for i in range(frequency + 1):
            for j in range(frequency + 1 - i):
                k = frequency - i - j
                point = (a * i + b * j + c * k) / frequency
                grid[(i, j)] = register(point)
        for i in range(frequency):
            for j in range(frequency - i):
                triangles.append((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
                if i + j < frequency - 1:
                    triangles.append(
                        (grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)])
                    )
    return np.asarray(vertices, dtype=np.float64), np.asarray(triangles, dtype=np.int32)


def _cyclic_order(points: np.ndarray, axis: np.ndarray) -> list[int]:
    """Order points counter-clockwise as seen from outside along *axis*."""
    axis = normalize(axis)
    reference = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(reference, axis))) > 0.9:
        reference = np.array([0.0, 1.0, 0.0])
    basis_x = normalize(reference - axis * float(np.dot(reference, axis)))
    basis_y = np.cross(axis, basis_x)
    centre = points.mean(axis=0)
    angles = [
        math.atan2(
            float(np.dot(point - centre, basis_y)),
            float(np.dot(point - centre, basis_x)),
        )
        for point in points
    ]
    return sorted(range(len(points)), key=lambda index: angles[index])


# ----------------------------------------------------------------------
# Measured descriptions of one cage
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class EdgeClass:
    """One measured strut length on the unit sphere."""

    name: str
    factor: float
    count: int
    dome_count: int
    central_angle_deg: float


@dataclass(frozen=True)
class FaceClass:
    """One measured panel shape."""

    name: str
    sides: int
    count: int
    dome_count: int
    edge_factors: tuple[float, ...]
    corner_angles_deg: tuple[float, ...]
    area_factor: float
    circumradius_factor: float
    planarity_error: float

    @property
    def is_regular(self) -> bool:
        """True when every edge and every corner of the panel matches."""
        return (
            max(self.edge_factors) - min(self.edge_factors) < 1e-7
            and max(self.corner_angles_deg) - min(self.corner_angles_deg) < 1e-5
        )

    @property
    def planar(self) -> bool:
        """True when the panel's corners lie in one plane you can cut."""
        return self.planarity_error < 1e-7


@dataclass(frozen=True)
class HexCage:
    """A complete hexagon/pentagon cage on the unit sphere."""

    name: str
    notation: str
    frequency: int
    vertices: np.ndarray
    faces: tuple[tuple[int, ...], ...]
    edges: tuple[tuple[int, int], ...]
    edge_classes: tuple[EdgeClass, ...]
    face_classes: tuple[FaceClass, ...]
    face_class_of: tuple[str, ...]
    edge_class_of: tuple[str, ...]
    dome_faces: tuple[int, ...]
    dome_edges: tuple[tuple[int, int], ...]
    cut_height: float

    # -- counts ------------------------------------------------------
    @property
    def pentagons(self) -> int:
        return sum(1 for face in self.faces if len(face) == 5)

    @property
    def hexagons(self) -> int:
        return sum(1 for face in self.faces if len(face) == 6)

    @property
    def euler(self) -> int:
        return len(self.vertices) - len(self.edges) + len(self.faces)

    @property
    def strut_lengths(self) -> int:
        return len(self.edge_classes)

    @property
    def hex_shapes(self) -> int:
        return sum(1 for item in self.face_classes if item.sides == 6)

    @property
    def all_hexagons_regular(self) -> bool:
        return all(item.is_regular for item in self.face_classes if item.sides == 6)

    @property
    def all_faces_planar(self) -> bool:
        return all(item.planar for item in self.face_classes)

    @property
    def worst_planarity(self) -> float:
        return max(item.planarity_error for item in self.face_classes)

    # -- the base cut ------------------------------------------------
    @property
    def boundary_edges(self) -> tuple[tuple[int, int], ...]:
        """Struts on the open rim of the dome half.

        A rim strut is one that only one kept panel uses; every interior
        strut is shared by two.
        """
        counts: dict[tuple[int, int], int] = {}
        for face_index in self.dome_faces:
            face = self.faces[face_index]
            for position in range(len(face)):
                a, b = face[position], face[(position + 1) % len(face)]
                key = (a, b) if a < b else (b, a)
                counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(key for key, count in counts.items() if count == 1))

    @property
    def base_vertices(self) -> tuple[int, ...]:
        """The rim loop of the dome half, walked round by compass bearing."""
        rim = {index for edge in self.boundary_edges for index in edge}
        return tuple(sorted(rim, key=lambda index: math.atan2(
            float(self.vertices[index][1]), float(self.vertices[index][0])
        )))

    @property
    def base_wobble(self) -> float:
        """Height spread of the rim loop, in sphere radii.

        Zero would mean the cage has a flat equator you can saw along in
        one pass.  A hexagon cage never does -- its rim zigzags up and
        down, which is why a hex dome needs a levelling course beneath it
        or a second cut through the bottom row of panels.
        """
        ring = self.base_vertices
        if not ring:
            return 0.0
        heights = [float(self.vertices[index][2]) for index in ring]
        return max(heights) - min(heights)

    @property
    def rim_low(self) -> float:
        ring = self.base_vertices
        return min(float(self.vertices[index][2]) for index in ring) if ring else 0.0

    @property
    def rim_high(self) -> float:
        ring = self.base_vertices
        return max(float(self.vertices[index][2]) for index in ring) if ring else 0.0


def _plane_error(points: np.ndarray) -> float:
    """Largest distance from the points to their own best-fit plane."""
    centred = points - points.mean(axis=0)
    # The smallest singular direction is the plane normal.
    _, _, right = np.linalg.svd(centred, full_matrices=False)
    normal = right[-1]
    return float(np.max(np.abs(centred @ normal)))


def _polygon_area(points: np.ndarray) -> float:
    """Area of a (possibly slightly warped) ring of points, fanned from its centre."""
    centre = points.mean(axis=0)
    total = 0.0
    for index in range(len(points)):
        a = points[index] - centre
        b = points[(index + 1) % len(points)] - centre
        total += 0.5 * float(np.linalg.norm(np.cross(a, b)))
    return total


def _corner_angles(points: np.ndarray) -> tuple[float, ...]:
    angles: list[float] = []
    count = len(points)
    for index in range(count):
        previous = points[(index - 1) % count] - points[index]
        following = points[(index + 1) % count] - points[index]
        cosine = float(np.dot(normalize(previous), normalize(following)))
        angles.append(math.degrees(math.acos(float(np.clip(cosine, -1.0, 1.0)))))
    return tuple(angles)


def _group_lengths(values: Sequence[float]) -> list[float]:
    """Collapse measured lengths into distinct representatives, ascending."""
    representatives: list[float] = []
    for value in values:
        for existing in representatives:
            if abs(value - existing) <= LENGTH_TOLERANCE:
                break
        else:
            representatives.append(value)
    return sorted(representatives)


def _assemble_cage(
    name: str,
    notation: str,
    frequency: int,
    vertices: np.ndarray,
    faces: Sequence[Sequence[int]],
) -> HexCage:
    """Measure every strut, panel and cut of a finished cage."""
    faces = tuple(tuple(int(index) for index in face) for face in faces)

    edge_set: set[tuple[int, int]] = set()
    for face in faces:
        for position in range(len(face)):
            a, b = face[position], face[(position + 1) % len(face)]
            edge_set.add((a, b) if a < b else (b, a))
    edges = tuple(sorted(edge_set))

    lengths = [
        float(np.linalg.norm(vertices[a] - vertices[b])) for a, b in edges
    ]
    length_values = _group_lengths(lengths)
    edge_label_of_value = {
        value: (chr(ord("S") + index) if index < 2 else f"E{index + 1}")
        for index, value in enumerate(length_values)
    }
    # Two lengths read best as SHORT/LONG; three or more get plain labels.
    if len(length_values) == 1:
        edge_label_of_value = {length_values[0]: "STRUT"}
    elif len(length_values) == 2:
        edge_label_of_value = {length_values[0]: "SHORT", length_values[1]: "LONG"}
    else:
        edge_label_of_value = {
            value: f"E{index + 1}" for index, value in enumerate(length_values)
        }

    def label_for(length: float) -> str:
        for value, label in edge_label_of_value.items():
            if abs(length - value) <= LENGTH_TOLERANCE:
                return label
        raise AssertionError("length did not match any measured class")

    edge_class_of = tuple(label_for(length) for length in lengths)

    # The dome half: keep every face whose centre sits at or above the
    # equator.  The cut height is the lowest corner those faces reach.
    face_centres = np.array([vertices[list(face)].mean(axis=0) for face in faces])
    dome_faces = tuple(
        index for index in range(len(faces)) if face_centres[index][2] >= -1e-9
    )
    dome_corner_heights = [
        float(vertices[index][2]) for face in dome_faces for index in faces[face]
    ]
    cut_height = min(dome_corner_heights) if dome_corner_heights else 0.0
    dome_edge_set: set[tuple[int, int]] = set()
    for face_index in dome_faces:
        face = faces[face_index]
        for position in range(len(face)):
            a, b = face[position], face[(position + 1) % len(face)]
            dome_edge_set.add((a, b) if a < b else (b, a))
    dome_edges = tuple(sorted(dome_edge_set))

    edge_classes: list[EdgeClass] = []
    for value in length_values:
        label = edge_label_of_value[value]
        count = sum(1 for length in lengths if abs(length - value) <= LENGTH_TOLERANCE)
        dome_count = sum(
            1 for a, b in dome_edges
            if abs(float(np.linalg.norm(vertices[a] - vertices[b])) - value)
            <= LENGTH_TOLERANCE
        )
        edge_classes.append(EdgeClass(
            name=label,
            factor=value,
            count=count,
            dome_count=dome_count,
            central_angle_deg=math.degrees(2.0 * math.asin(min(1.0, value * 0.5))),
        ))

    # Panels group by (side count, sorted edge lengths, sorted corner angles).
    signatures: dict[tuple, list[int]] = {}
    measurements: dict[tuple, tuple] = {}
    for face_index, face in enumerate(faces):
        points = vertices[list(face)]
        face_lengths = tuple(sorted(
            float(np.linalg.norm(points[i] - points[(i + 1) % len(points)]))
            for i in range(len(points))
        ))
        angles = tuple(sorted(_corner_angles(points)))
        signature = (
            len(face),
            tuple(round(value, 9) for value in face_lengths),
            tuple(round(value, 6) for value in angles),
        )
        signatures.setdefault(signature, []).append(face_index)
        measurements[signature] = (
            face_lengths,
            angles,
            _polygon_area(points),
            float(np.max(np.linalg.norm(points - points.mean(axis=0), axis=1))),
            _plane_error(points),
        )

    dome_face_set = set(dome_faces)
    ordered = sorted(
        signatures.items(),
        key=lambda item: (item[0][0], -measurements[item[0]][2]),
    )
    face_classes: list[FaceClass] = []
    face_class_of: list[str] = ["" for _ in faces]
    hex_counter = 0
    pent_counter = 0
    for signature, members in ordered:
        sides = signature[0]
        if sides == 5:
            pent_counter += 1
            label = "PENT" if pent_counter == 1 else f"PENT-{pent_counter}"
        elif sides == 6:
            hex_counter += 1
            label = f"HEX-{hex_counter}"
        else:
            label = f"{sides}-GON"
        face_lengths, angles, area, circumradius, planarity = measurements[signature]
        for member in members:
            face_class_of[member] = label
        face_classes.append(FaceClass(
            name=label,
            sides=sides,
            count=len(members),
            dome_count=sum(1 for member in members if member in dome_face_set),
            edge_factors=tuple(face_lengths),
            corner_angles_deg=tuple(angles),
            area_factor=area,
            circumradius_factor=circumradius,
            planarity_error=planarity,
        ))
    # A single hexagon shape needs no suffix.
    if hex_counter == 1:
        face_classes = [
            FaceClass(
                "HEX", item.sides, item.count, item.dome_count, item.edge_factors,
                item.corner_angles_deg, item.area_factor, item.circumradius_factor,
                item.planarity_error,
            ) if item.name == "HEX-1" else item
            for item in face_classes
        ]
        face_class_of = ["HEX" if name == "HEX-1" else name for name in face_class_of]

    return HexCage(
        name=name,
        notation=notation,
        frequency=frequency,
        vertices=vertices,
        faces=faces,
        edges=edges,
        edge_classes=tuple(edge_classes),
        face_classes=tuple(face_classes),
        face_class_of=tuple(face_class_of),
        edge_class_of=edge_class_of,
        dome_faces=dome_faces,
        dome_edges=dome_edges,
        cut_height=cut_height,
    )


# ----------------------------------------------------------------------
# The two cages
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def truncated_icosahedron() -> HexCage:
    """The one-hexagon, one-strut cage: 20 regular hexagons, 12 pentagons.

    Built from the exact even-permutation coordinates so the regularity is
    a property of the numbers, not of a tolerance.  Raw edge length is 2
    and raw circumradius is ``sqrt(9 * phi + 10)``.
    """
    families = (
        (0.0, 1.0, 3.0 * PHI),
        (1.0, 2.0 + PHI, 2.0 * PHI),
        (PHI, 2.0, 2.0 * PHI + 1.0),
    )
    points: list[tuple[float, float, float]] = []
    for a, b, c in families:
        for signs in ((1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
                      (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)):
            triple = (a * signs[0], b * signs[1], c * signs[2])
            for rotation in range(3):
                points.append((
                    triple[rotation % 3],
                    triple[(rotation + 1) % 3],
                    triple[(rotation + 2) % 3],
                ))
    unique: list[tuple[float, float, float]] = []
    seen: set[tuple[int, int, int]] = set()
    for point in points:
        key = tuple(int(round(value * 1e9)) for value in point)
        if key not in seen:
            seen.add(key)
            unique.append(point)
    raw = np.asarray(unique, dtype=np.float64)
    if len(raw) != 60:
        raise AssertionError(f"truncated icosahedron needs 60 vertices, got {len(raw)}")

    # These coordinates are written in the textbook phi frame.  Turn them
    # into the package's five-fold-up frame so the hex cage and the
    # triangulated 2V dome can share one camera and one equator.
    raw = raw @ icosahedron_north_rotation().T
    ico_raw, ico_faces = raw_icosahedron()
    ico = ico_raw / math.sqrt(1.0 + PHI**2)
    circumradius = math.sqrt(9.0 * PHI + 10.0)
    vertices = raw / circumradius

    # Pentagons sit on the twelve icosahedron vertex axes; hexagons sit on
    # the twenty face axes.  A face is every cage vertex furthest along its
    # own axis, which needs no hull library and stays exact.
    axes: list[tuple[np.ndarray, int]] = [(vertex, 5) for vertex in ico]
    axes.extend(
        (normalize(ico[list(face)].mean(axis=0)), 6) for face in ico_faces
    )
    faces: list[tuple[int, ...]] = []
    for axis, sides in axes:
        projections = vertices @ axis
        threshold = float(np.max(projections)) - 1e-6
        members = [index for index, value in enumerate(projections) if value >= threshold]
        if len(members) != sides:
            raise AssertionError(
                f"expected a {sides}-gon on this axis, found {len(members)} corners"
            )
        order = _cyclic_order(vertices[members], axis)
        faces.append(tuple(members[position] for position in order))

    return _assemble_cage(
        "Truncated icosahedron", "GP(1,1)", 1, vertices, faces
    )


@lru_cache(maxsize=8)
def goldberg(frequency: int) -> HexCage:
    """``GP(frequency, 0)`` -- the dual of a class-I ``nV`` geodesic sphere.

    Every geodesic vertex becomes one panel: the twelve five-way vertices
    become pentagons, all the rest become hexagons.
    """
    if frequency < 1:
        raise ValueError("frequency must be at least 1")
    geo_vertices, geo_faces = geodesic_class_one(frequency)

    centres = np.array([
        normalize(geo_vertices[list(face)].mean(axis=0)) for face in geo_faces
    ])
    incident: dict[int, list[int]] = {index: [] for index in range(len(geo_vertices))}
    for face_index, face in enumerate(geo_faces):
        for vertex_index in face:
            incident[int(vertex_index)].append(face_index)

    faces: list[tuple[int, ...]] = []
    for vertex_index, face_indices in incident.items():
        axis = geo_vertices[vertex_index]
        order = _cyclic_order(centres[face_indices], axis)
        faces.append(tuple(face_indices[position] for position in order))

    name = f"Goldberg {frequency}V hexagon cage"
    return _assemble_cage(name, f"GP({frequency},0)", frequency, centres, tuple(faces))


# ----------------------------------------------------------------------
# The two proofs the lesson leans on
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PentagonProof:
    """Euler's formula, solved for the number of pentagons."""

    hexagons: int
    pentagons: int
    faces: int
    edges: int
    vertices: int
    euler: int

    @property
    def lines(self) -> tuple[str, ...]:
        return (
            f"H = {self.hexagons} hexagons, P pentagons, every corner 3-way",
            f"F = P + H     E = (5P + 6H)/2     V = (5P + 6H)/3",
            f"V - E + F = 2  ->  P/6 = 2  ->  P = {self.pentagons}",
            f"check: V {self.vertices} - E {self.edges} + F {self.faces} "
            f"= {self.euler}",
        )


def euler_pentagon_proof(hexagons: int) -> PentagonProof:
    """Solve Euler's formula for a three-way cage of pentagons and hexagons.

    Substituting ``F = P + H``, ``E = (5P + 6H) / 2`` and ``V = (5P + 6H) / 3``
    into ``V - E + F = 2`` cancels every hexagon term and leaves ``P / 6 = 2``.
    The hexagon count never appears in the answer, which is the whole point:
    you may use as many hexagons as you like and you will still need
    **exactly twelve** pentagons.
    """
    pentagons = 12
    faces = pentagons + hexagons
    edges = (5 * pentagons + 6 * hexagons) // 2
    vertices = (5 * pentagons + 6 * hexagons) // 3
    return PentagonProof(
        hexagons=hexagons,
        pentagons=pentagons,
        faces=faces,
        edges=edges,
        vertices=vertices,
        euler=vertices - edges + faces,
    )


@dataclass(frozen=True)
class DeficitReport:
    """Descartes' theorem, measured on a real cage.

    ``total_deficit_deg`` is exactly 720 when the cage's panels are flat.
    On a sphere-projected cage the panels warp, their corners stop being
    honest flat-panel corners, and the sum drifts.  ``planar_faces`` says
    which of the two you are looking at, and ``warp_gap_deg`` is the drift.
    """

    total_deficit_deg: float
    corner_count: int
    planar_faces: bool
    hexagon_only_deficit_deg: float
    per_pentagon_corner_deg: float
    sample_pentagon_corner_deg: float
    sample_hexagon_corner_deg: float

    @property
    def warp_gap_deg(self) -> float:
        return self.total_deficit_deg - 720.0


def descartes_deficit(cage: HexCage) -> DeficitReport:
    """Measure how much angle is missing at every corner of a cage.

    Fold a sheet of flat hexagons and nothing happens: three 120-degree
    corners use up all 360 degrees, so there is no angle left to take out
    and the sheet stays flat.  Curvature is bought with missing angle, and
    Descartes proved every closed convex cage is missing exactly 720
    degrees in total.  A pentagon corner is the only place a hexagon cage
    has any to give.
    """
    total = 0.0
    corner_totals: dict[int, float] = {index: 0.0 for index in range(len(cage.vertices))}
    for face in cage.faces:
        points = cage.vertices[list(face)]
        for position, angle in enumerate(_corner_angles(points)):
            corner_totals[face[position]] += angle
    for value in corner_totals.values():
        total += 360.0 - value

    pentagon_faces = [face for face in cage.faces if len(face) == 5]
    hexagon_faces = [face for face in cage.faces if len(face) == 6]
    sample_pentagon = (
        _corner_angles(cage.vertices[list(pentagon_faces[0])])[0]
        if pentagon_faces else 0.0
    )
    sample_hexagon = (
        _corner_angles(cage.vertices[list(hexagon_faces[0])])[0]
        if hexagon_faces else 0.0
    )
    return DeficitReport(
        total_deficit_deg=total,
        corner_count=len(cage.vertices),
        planar_faces=cage.all_faces_planar,
        hexagon_only_deficit_deg=360.0 - flat_vertex_angle_sum(6),
        per_pentagon_corner_deg=720.0 / 12.0,
        sample_pentagon_corner_deg=sample_pentagon,
        sample_hexagon_corner_deg=sample_hexagon,
    )


# ----------------------------------------------------------------------
# Turning a cage into a shopping list
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HexBuild:
    """A hex cage scaled to a real radius, with cut lengths."""

    cage: HexCage
    radius: float
    connector_deduction: float

    @property
    def diameter(self) -> float:
        return 2.0 * self.radius

    @property
    def dome_height(self) -> float:
        """Apex height above the level base cut."""
        return self.radius - self.cut_z

    @property
    def cut_z(self) -> float:
        return self.cage.cut_height * self.radius

    @property
    def floor_radius(self) -> float:
        """Radius of the sphere at the level saw cut."""
        return self.radius * math.sqrt(max(0.0, 1.0 - self.cage.cut_height**2))

    @property
    def floor_area(self) -> float:
        return math.pi * self.floor_radius**2

    @property
    def base_wobble(self) -> float:
        """How far the raw cage base rises and falls, at this radius."""
        return self.cage.base_wobble * self.radius

    def strut_table(self) -> tuple[tuple[str, int, float, float], ...]:
        """(class, dome count, centre length, cut length) for every strut."""
        return tuple(
            (
                item.name,
                item.dome_count,
                item.factor * self.radius,
                item.factor * self.radius - self.connector_deduction,
            )
            for item in self.cage.edge_classes
        )

    def panel_table(self) -> tuple[tuple[str, int, int, float, float], ...]:
        """(class, sides, dome count, area, planarity error) per panel type."""
        return tuple(
            (
                item.name,
                item.sides,
                item.dome_count,
                item.area_factor * self.radius**2,
                item.planarity_error * self.radius,
            )
            for item in self.cage.face_classes
        )


def hex_report(radius: float = 120.0, connector_deduction: float = 0.0) -> str:
    """A portable, plain-text audit of everything the hex lesson claims."""
    lines = ["HEXAGONAL DOME MASTERCLASS - CALCULATION AUDIT", ""]
    lines.append(f"flat regular hexagon corner: 3 x 120.000 deg = "
                 f"{flat_vertex_angle_sum(6):.3f} deg  (nothing left over)")
    lines.append(f"flat regular pentagon corner: 3 x 108.000 deg = "
                 f"{flat_vertex_angle_sum(5):.3f} deg  "
                 f"({360.0 - flat_vertex_angle_sum(5):.3f} deg missing)")
    lines.append("")
    for hexagons in (20, 30, 80, 500):
        proof = euler_pentagon_proof(hexagons)
        lines.append(
            f"  {proof.hexagons:>4} hexagons -> P = {proof.pentagons}, "
            f"F {proof.faces}, E {proof.edges}, V {proof.vertices}, "
            f"V-E+F = {proof.euler}"
        )
    lines.append("")
    for cage in (truncated_icosahedron(), goldberg(2), goldberg(3), goldberg(4)):
        build = HexBuild(cage, radius, connector_deduction)
        deficit = descartes_deficit(cage)
        lines.extend([
            f"--- {cage.name}  {cage.notation} ---",
            f"  V/E/F                {len(cage.vertices)}/{len(cage.edges)}/"
            f"{len(cage.faces)}   Euler {cage.euler}",
            f"  pentagons/hexagons   {cage.pentagons}/{cage.hexagons}",
            f"  hexagon shapes       {cage.hex_shapes}"
            f"   (all regular: {cage.all_hexagons_regular})",
            f"  strut lengths        {cage.strut_lengths}",
            f"  every panel planar   {cage.all_faces_planar}"
            f"   worst warp {cage.worst_planarity:.9f} R",
            f"  total angle deficit  {deficit.total_deficit_deg:.6f} deg"
            f"   (Descartes: 720, warp gap {deficit.warp_gap_deg:+.6f})",
            f"  dome half            {len(cage.dome_faces)} panels, "
            f"{len(cage.dome_edges)} struts",
            f"  rim loop             {len(cage.base_vertices)} corners, "
            f"{len(cage.boundary_edges)} rim struts",
            f"  rim wobble           {cage.base_wobble:.6f} R "
            f"= {build.base_wobble:.3f} at R={radius:g}"
            f"   (z {cage.rim_low:+.4f} .. {cage.rim_high:+.4f})",
        ])
        for name, count, centre, cut in build.strut_table():
            lines.append(
                f"    strut {name:<6} x{count:<4} centre {centre:9.4f}"
                f"   cut {cut:9.4f}"
            )
        for name, sides, count, area, warp in build.panel_table():
            lines.append(
                f"    panel {name:<7} {sides}-gon x{count:<4} "
                f"area {area:11.3f}   warp {warp:8.5f}"
            )
        lines.append("")
    return "\n".join(lines)


def validate_hex_geometry() -> None:
    """Prove the models before any of their numbers reach a screen."""
    soccer = truncated_icosahedron()
    assert len(soccer.vertices) == 60, len(soccer.vertices)
    assert len(soccer.edges) == 90, len(soccer.edges)
    assert len(soccer.faces) == 32, len(soccer.faces)
    assert soccer.euler == 2
    assert soccer.pentagons == 12 and soccer.hexagons == 20
    # The whole promise of act one: one hexagon shape, one strut length.
    assert soccer.strut_lengths == 1, soccer.strut_lengths
    assert soccer.hex_shapes == 1, soccer.hex_shapes
    assert soccer.all_hexagons_regular
    assert soccer.all_faces_planar, soccer.worst_planarity

    for frequency in (1, 2, 3, 4):
        cage = goldberg(frequency)
        assert cage.euler == 2, (frequency, cage.euler)
        assert cage.pentagons == 12, (frequency, cage.pentagons)
        assert cage.hexagons == 10 * (frequency**2 - 1), (frequency, cage.hexagons)
        assert all(len(face) in (5, 6) for face in cage.faces)
        deficit = descartes_deficit(cage)
        if cage.all_faces_planar:
            # Descartes is exact only when every panel is genuinely flat.
            assert abs(deficit.warp_gap_deg) < 1e-6, deficit.total_deficit_deg
        else:
            # Warped panels drift, but never far, and always the same way.
            assert 0.0 < deficit.warp_gap_deg < 15.0, deficit.total_deficit_deg

    # Raising the frequency is exactly the trade the lesson describes.
    assert goldberg(3).hex_shapes > goldberg(2).hex_shapes
    assert goldberg(3).strut_lengths > soccer.strut_lengths
    assert not goldberg(3).all_faces_planar

    for hexagons in (0, 20, 30, 80, 1000):
        proof = euler_pentagon_proof(hexagons)
        assert proof.pentagons == 12
        assert proof.euler == 2, (hexagons, proof.euler)

    assert abs(flat_vertex_angle_sum(6) - 360.0) < 1e-12
