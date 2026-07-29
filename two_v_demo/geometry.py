"""Pure mathematical model for the standalone 2V teaching world.

The renderer never invents its own dimensions.  Every animated point, edge,
label, cut-list result, and validation number comes from this module.

Terminology
-----------
``SHORT`` and ``LONG`` are intentionally used instead of A/B.  Published dome
calculators do not agree on the letter assignment.  The user's convention is
displayed in the lesson as A=LONG and B=SHORT without making it a universal
claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import numpy as np


PHI = (1.0 + math.sqrt(5.0)) / 2.0
INCHES_PER_FOOT = 12.0
MM_PER_INCH = 25.4


def normalize(vector: np.ndarray) -> np.ndarray:
    """Return a unit vector, preserving a zero vector."""
    vector = np.asarray(vector, dtype=np.float64)
    magnitude = float(np.linalg.norm(vector))
    if magnitude <= 1e-12:
        return vector.copy()
    return vector / magnitude


def rotation_from_to(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Return a 3x3 rotation matrix that maps *source* onto *target*."""
    a = normalize(source)
    b = normalize(target)
    cross = np.cross(a, b)
    sine = float(np.linalg.norm(cross))
    cosine = float(np.clip(np.dot(a, b), -1.0, 1.0))
    if sine <= 1e-12:
        if cosine > 0.0:
            return np.eye(3, dtype=np.float64)
        trial = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(a, trial))) > 0.9:
            trial = np.array([0.0, 1.0, 0.0])
        axis = normalize(np.cross(a, trial))
        # A 180-degree Rodrigues rotation.
        return -np.eye(3, dtype=np.float64) + 2.0 * np.outer(axis, axis)
    axis = cross / sine
    skew = np.array([
        [0.0, -axis[2], axis[1]],
        [axis[2], 0.0, -axis[0]],
        [-axis[1], axis[0], 0.0],
    ])
    return (
        np.eye(3, dtype=np.float64)
        + skew * sine
        + (skew @ skew) * (1.0 - cosine)
    )


def raw_icosahedron() -> tuple[np.ndarray, np.ndarray]:
    """Return the canonical phi-coordinate icosahedron and its 20 faces.

    Raw coordinates have circumradius ``sqrt(1 + phi**2)`` and edge length 2.
    The vertex selected as the north pole is rotated to +Z before the vertices
    are normalized to a unit sphere.  This exposes the natural equatorial ring
    needed for a true 2V hemisphere.
    """
    vertices = np.array([
        [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
        [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
        [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1],
    ], dtype=np.float64)
    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int32)
    north_index = 4
    rotation = rotation_from_to(vertices[north_index], np.array([0.0, 0.0, 1.0]))
    vertices = vertices @ rotation.T
    return vertices, faces


def unique_edges(faces: np.ndarray) -> tuple[tuple[int, int], ...]:
    edges: set[tuple[int, int]] = set()
    for face in faces:
        for index in range(3):
            a = int(face[index])
            b = int(face[(index + 1) % 3])
            edges.add((a, b) if a < b else (b, a))
    return tuple(sorted(edges))


def nearest_edges(vertices: np.ndarray) -> tuple[tuple[int, int], ...]:
    """Infer a regular solid's edge graph from its smallest point distance."""
    distances: list[tuple[float, int, int]] = []
    for a in range(len(vertices)):
        for b in range(a + 1, len(vertices)):
            distances.append((float(np.linalg.norm(vertices[a] - vertices[b])), a, b))
    edge_length = min(distance for distance, _, _ in distances if distance > 1e-8)
    tolerance = edge_length * 1e-5
    return tuple(
        (a, b) for distance, a, b in distances
        if abs(distance - edge_length) <= tolerance
    )


@dataclass(frozen=True)
class Solid:
    name: str
    vertices: np.ndarray
    edges: tuple[tuple[int, int], ...]
    faces: int


def platonic_solids() -> tuple[Solid, ...]:
    """Return normalized vertex/edge models for all five Platonic solids."""
    tetra = np.array([
        [1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1],
    ], dtype=np.float64)
    cube = np.array([
        [x, y, z]
        for x in (-1.0, 1.0)
        for y in (-1.0, 1.0)
        for z in (-1.0, 1.0)
    ])
    octa = np.array([
        [1, 0, 0], [-1, 0, 0], [0, 1, 0],
        [0, -1, 0], [0, 0, 1], [0, 0, -1],
    ], dtype=np.float64)
    ico_raw, _ = raw_icosahedron()
    inv_phi = 1.0 / PHI
    dodeca = np.array(
        [[x, y, z] for x in (-1.0, 1.0)
         for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
        + [[0.0, y * inv_phi, z * PHI]
           for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
        + [[x * inv_phi, y * PHI, 0.0]
           for x in (-1.0, 1.0) for y in (-1.0, 1.0)]
        + [[x * PHI, 0.0, z * inv_phi]
           for x in (-1.0, 1.0) for z in (-1.0, 1.0)],
        dtype=np.float64,
    )
    definitions = (
        ("Tetrahedron", tetra, 4),
        ("Cube", cube, 6),
        ("Octahedron", octa, 8),
        ("Dodecahedron", dodeca, 12),
        ("Icosahedron", ico_raw, 20),
    )
    solids: list[Solid] = []
    for name, vertices, face_count in definitions:
        normalized = np.array([normalize(vertex) for vertex in vertices])
        solids.append(Solid(name, normalized, nearest_edges(normalized), face_count))
    return tuple(solids)


@dataclass(frozen=True)
class EdgeClass:
    name: str
    factor: float
    central_angle_deg: float
    full_sphere_count: int
    hemisphere_count: int


@dataclass(frozen=True)
class TriangleClass:
    name: str
    side_names: tuple[str, str, str]
    full_sphere_count: int
    hemisphere_count: int
    angles_deg: tuple[float, float, float]
    planar_area_factor: float


@dataclass(frozen=True)
class DemoGeometry:
    raw_vertices: np.ndarray
    base_faces: np.ndarray
    ico_vertices: np.ndarray
    ico_edges: tuple[tuple[int, int], ...]
    flat_midpoints: np.ndarray
    vertices: np.ndarray
    faces: np.ndarray
    edges: tuple[tuple[int, int], ...]
    edge_class_by_edge: tuple[str, ...]
    edge_classes: tuple[EdgeClass, ...]
    hemisphere_faces: np.ndarray
    hemisphere_edges: tuple[tuple[int, int], ...]
    base_ring: tuple[int, ...]
    triangle_classes: tuple[TriangleClass, ...]

    @property
    def short_factor(self) -> float:
        return next(item.factor for item in self.edge_classes if item.name == "SHORT")

    @property
    def long_factor(self) -> float:
        return next(item.factor for item in self.edge_classes if item.name == "LONG")

    @property
    def ratio(self) -> float:
        return self.long_factor / self.short_factor


def _classify_lengths(
    vertices: np.ndarray,
    edges: Iterable[tuple[int, int]],
    tolerance: float = 1e-7,
) -> list[tuple[float, list[tuple[int, int]]]]:
    groups: list[tuple[float, list[tuple[int, int]]]] = []
    for edge in edges:
        length = float(np.linalg.norm(vertices[edge[0]] - vertices[edge[1]]))
        for index, (representative, members) in enumerate(groups):
            if abs(length - representative) <= tolerance:
                members.append(edge)
                break
        else:
            groups.append((length, [edge]))
    return sorted(groups, key=lambda item: item[0])


def _triangle_angles(side_lengths: tuple[float, float, float]) -> tuple[float, float, float]:
    a, b, c = side_lengths
    values = []
    for opposite, adjacent_1, adjacent_2 in ((a, b, c), (b, a, c), (c, a, b)):
        cosine = (
            adjacent_1**2 + adjacent_2**2 - opposite**2
        ) / (2.0 * adjacent_1 * adjacent_2)
        values.append(math.degrees(math.acos(float(np.clip(cosine, -1.0, 1.0)))))
    return tuple(values)  # type: ignore[return-value]


def _heron_area(sides: tuple[float, float, float]) -> float:
    semiperimeter = sum(sides) * 0.5
    return math.sqrt(max(
        0.0,
        semiperimeter
        * (semiperimeter - sides[0])
        * (semiperimeter - sides[1])
        * (semiperimeter - sides[2]),
    ))


@lru_cache(maxsize=1)
def build_demo_geometry() -> DemoGeometry:
    """Build a class-I 2V sphere and its exact upper hemisphere."""
    raw_vertices, base_faces = raw_icosahedron()
    raw_radius = math.sqrt(1.0 + PHI**2)
    ico_vertices = raw_vertices / raw_radius
    ico_edges = unique_edges(base_faces)

    vertices: list[np.ndarray] = [vertex.copy() for vertex in ico_vertices]
    flat_points: list[np.ndarray] = [vertex.copy() for vertex in ico_vertices]
    edge_midpoint_index: dict[tuple[int, int], int] = {}
    for edge in ico_edges:
        flat_midpoint = (ico_vertices[edge[0]] + ico_vertices[edge[1]]) * 0.5
        edge_midpoint_index[edge] = len(vertices)
        flat_points.append(flat_midpoint)
        vertices.append(normalize(flat_midpoint))

    subdivided_faces: list[tuple[int, int, int]] = []
    for a, b, c in base_faces:
        ab_key = tuple(sorted((int(a), int(b))))
        bc_key = tuple(sorted((int(b), int(c))))
        ca_key = tuple(sorted((int(c), int(a))))
        ab = edge_midpoint_index[ab_key]
        bc = edge_midpoint_index[bc_key]
        ca = edge_midpoint_index[ca_key]
        subdivided_faces.extend([
            (int(a), ab, ca),
            (int(b), bc, ab),
            (int(c), ca, bc),
            (ab, bc, ca),
        ])

    vertex_array = np.asarray(vertices, dtype=np.float64)
    flat_array = np.asarray(flat_points, dtype=np.float64)
    face_array = np.asarray(subdivided_faces, dtype=np.int32)
    edges = unique_edges(face_array)
    length_groups = _classify_lengths(vertex_array, edges)
    if len(length_groups) != 2:
        raise AssertionError(f"2V sphere should have 2 edge classes, got {len(length_groups)}")

    # The chosen fivefold orientation has a genuine z=0 equatorial ring.
    hemisphere_face_list = [
        tuple(int(value) for value in face)
        for face in face_array
        if all(vertex_array[int(index), 2] >= -1e-9 for index in face)
    ]
    hemisphere_faces = np.asarray(hemisphere_face_list, dtype=np.int32)
    hemisphere_edges = unique_edges(hemisphere_faces)
    base_ring = tuple(
        sorted(
            (index for index, vertex in enumerate(vertex_array)
             if abs(float(vertex[2])) <= 1e-8),
            key=lambda index: math.atan2(
                float(vertex_array[index, 1]), float(vertex_array[index, 0])
            ),
        )
    )

    edge_names: dict[tuple[int, int], str] = {}
    edge_classes: list[EdgeClass] = []
    for name, (factor, members) in zip(("SHORT", "LONG"), length_groups):
        member_set = set(members)
        for member in members:
            edge_names[member] = name
        hemisphere_count = sum(1 for edge in hemisphere_edges if edge in member_set)
        angle = math.degrees(2.0 * math.asin(factor * 0.5))
        edge_classes.append(EdgeClass(
            name=name,
            factor=factor,
            central_angle_deg=angle,
            full_sphere_count=len(members),
            hemisphere_count=hemisphere_count,
        ))
    class_by_edge = tuple(edge_names[edge] for edge in edges)

    triangle_groups: dict[tuple[str, str, str], list[tuple[int, int, int]]] = {}
    for face in face_array:
        face_edges = [
            tuple(sorted((int(face[0]), int(face[1])))),
            tuple(sorted((int(face[1]), int(face[2])))),
            tuple(sorted((int(face[2]), int(face[0])))),
        ]
        signature = tuple(sorted(edge_names[edge] for edge in face_edges))
        triangle_groups.setdefault(signature, []).append(tuple(map(int, face)))

    hemisphere_face_set = {tuple(map(int, face)) for face in hemisphere_faces}
    factor_by_name = {item.name: item.factor for item in edge_classes}
    triangle_classes: list[TriangleClass] = []
    for signature, members in sorted(triangle_groups.items()):
        sides = tuple(factor_by_name[name] for name in signature)
        pretty = "-".join(signature)
        triangle_classes.append(TriangleClass(
            name=pretty,
            side_names=signature,
            full_sphere_count=len(members),
            hemisphere_count=sum(1 for face in members if face in hemisphere_face_set),
            angles_deg=_triangle_angles(sides),
            planar_area_factor=_heron_area(sides),
        ))

    return DemoGeometry(
        raw_vertices=raw_vertices,
        base_faces=base_faces,
        ico_vertices=ico_vertices,
        ico_edges=ico_edges,
        flat_midpoints=flat_array,
        vertices=vertex_array,
        faces=face_array,
        edges=edges,
        edge_class_by_edge=class_by_edge,
        edge_classes=tuple(edge_classes),
        hemisphere_faces=hemisphere_faces,
        hemisphere_edges=hemisphere_edges,
        base_ring=base_ring,
        triangle_classes=tuple(triangle_classes),
    )


@dataclass(frozen=True)
class MeasurementFit:
    radius_from_long: float
    radius_from_short: float
    best_fit_radius: float
    predicted_long: float
    predicted_short: float
    long_residual: float
    short_residual: float
    measured_ratio: float
    theoretical_ratio: float


def fit_measurements(long_length: float, short_length: float) -> MeasurementFit:
    """Fit a radius to measured LONG and SHORT center-to-center lengths."""
    geometry = build_demo_geometry()
    long_factor = geometry.long_factor
    short_factor = geometry.short_factor
    radius_from_long = long_length / long_factor
    radius_from_short = short_length / short_factor
    best_fit_radius = (
        long_factor * long_length + short_factor * short_length
    ) / (long_factor**2 + short_factor**2)
    predicted_long = long_factor * best_fit_radius
    predicted_short = short_factor * best_fit_radius
    return MeasurementFit(
        radius_from_long=radius_from_long,
        radius_from_short=radius_from_short,
        best_fit_radius=best_fit_radius,
        predicted_long=predicted_long,
        predicted_short=predicted_short,
        long_residual=long_length - predicted_long,
        short_residual=short_length - predicted_short,
        measured_ratio=long_length / short_length,
        theoretical_ratio=long_factor / short_factor,
    )


@dataclass(frozen=True)
class DomeMeasurements:
    radius: float
    connector_deduction: float = 0.0

    @property
    def diameter(self) -> float:
        return self.radius * 2.0

    @property
    def height(self) -> float:
        return self.radius

    @property
    def floor_area(self) -> float:
        return math.pi * self.radius**2

    @property
    def spherical_skin_area(self) -> float:
        return 2.0 * math.pi * self.radius**2

    @property
    def enclosed_volume(self) -> float:
        return (2.0 / 3.0) * math.pi * self.radius**3

    @property
    def short_center_length(self) -> float:
        return build_demo_geometry().short_factor * self.radius

    @property
    def long_center_length(self) -> float:
        return build_demo_geometry().long_factor * self.radius

    @property
    def short_cut_length(self) -> float:
        return self.short_center_length - self.connector_deduction

    @property
    def long_cut_length(self) -> float:
        return self.long_center_length - self.connector_deduction

    @property
    def planar_panel_area(self) -> float:
        geometry = build_demo_geometry()
        return sum(
            triangle.planar_area_factor * self.radius**2
            * triangle.hemisphere_count
            for triangle in geometry.triangle_classes
        )


def calculation_report(
    long_length: float = 72.0,
    short_length: float = 63.5,
) -> str:
    """Return a portable, plain-text audit of the lesson's core values."""
    geometry = build_demo_geometry()
    fit = fit_measurements(long_length, short_length)
    lines = [
        "2V GEODESIC MASTERCLASS - CALCULATION AUDIT",
        "",
        f"phi                              {PHI:.12f}",
        f"raw icosahedron radius           {math.sqrt(1 + PHI**2):.12f}",
        f"raw icosahedron edge             2.000000000000",
        f"normalized icosahedron edge      {2 / math.sqrt(1 + PHI**2):.12f} R",
        f"SHORT chord factor               {geometry.short_factor:.12f} R",
        f"LONG chord factor                {geometry.long_factor:.12f} R",
        f"LONG / SHORT                     {geometry.ratio:.12f}",
        "",
        f"full sphere vertices/faces/edges {len(geometry.vertices)}/"
        f"{len(geometry.faces)}/{len(geometry.edges)}",
        f"hemisphere faces/edges/base      {len(geometry.hemisphere_faces)}/"
        f"{len(geometry.hemisphere_edges)}/{len(geometry.base_ring)}",
    ]
    for edge_class in geometry.edge_classes:
        lines.append(
            f"{edge_class.name:<5} counts sphere/dome        "
            f"{edge_class.full_sphere_count}/{edge_class.hemisphere_count}"
        )
    for triangle in geometry.triangle_classes:
        lines.append(
            f"{triangle.name:<16} triangles sphere/dome "
            f"{triangle.full_sphere_count}/{triangle.hemisphere_count}"
        )
    lines.extend([
        "",
        f"measured LONG / SHORT            {fit.measured_ratio:.12f}",
        f"radius from LONG                 {fit.radius_from_long:.6f} in",
        f"radius from SHORT                {fit.radius_from_short:.6f} in",
        f"least-squares radius             {fit.best_fit_radius:.6f} in",
        f"best-fit predicted LONG          {fit.predicted_long:.6f} in",
        f"best-fit predicted SHORT         {fit.predicted_short:.6f} in",
        f"residual LONG / SHORT            {fit.long_residual:+.6f} / "
        f"{fit.short_residual:+.6f} in",
    ])
    return "\n".join(lines)


def validate_geometry() -> None:
    geometry = build_demo_geometry()
    assert len(geometry.raw_vertices) == 12
    assert len(geometry.base_faces) == 20
    assert len(geometry.ico_edges) == 30
    assert len(geometry.vertices) == 42
    assert len(geometry.faces) == 80
    assert len(geometry.edges) == 120
    assert len(geometry.hemisphere_faces) == 40
    assert len(geometry.hemisphere_edges) == 65
    assert len(geometry.base_ring) == 10
    assert math.isclose(geometry.short_factor, 0.5465330578, rel_tol=1e-8)
    assert math.isclose(geometry.long_factor, 1.0 / PHI, rel_tol=1e-8)
    assert math.isclose(geometry.ratio, 1.1308263606, rel_tol=1e-8)
    assert sum(item.hemisphere_count for item in geometry.edge_classes) == 65
    assert sum(item.hemisphere_count for item in geometry.triangle_classes) == 40
    # Euler characteristic for the full triangulated sphere.
    assert len(geometry.vertices) - len(geometry.edges) + len(geometry.faces) == 2
    fit = fit_measurements(72.0, 63.5)
    assert abs(fit.long_residual) < 0.2
    assert abs(fit.short_residual) < 0.2

