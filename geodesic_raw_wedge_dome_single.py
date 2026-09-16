#!/usr/bin/env python3
from __future__ import annotations

"""
RAW WEDGE 2V GEODESIC DOME — SINGLE-FILE EDITION

This file is a flattened, self-contained edition of the full ModernGL project.
It preserves the geometry, visualization, fabrication, analysis, export, HUD,
4-orientation wedge system, pinwheel joints, clean vertex cuts, panel explosion,
solo side-panel inspection, seam minimap, inverted horizontal mouse-look,
center-X wheel zoom, and max-zoom arrow-key pan behavior.

Run normally:
    python geodesic_raw_wedge_dome_single.py

Other built-in modes:
    python geodesic_raw_wedge_dome_single.py --validate
    python geodesic_raw_wedge_dome_single.py --fabrication
    python geodesic_raw_wedge_dome_single.py --extract-resources

The graphical mode requires numpy, pygame, and moderngl. Missing graphics packages
are installed automatically with the active Python interpreter when possible.
"""

from dataclasses import dataclass, field, asdict, replace
from collections import defaultdict
from pathlib import Path
from typing import Iterable
import argparse
import base64
import csv
import html
import importlib
import json
import math
import os
import subprocess
import sys


def _ensure_numpy() -> None:
    try:
        import numpy  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy>=2.0.0"])


_ensure_numpy()
import numpy as np

# Graphics dependencies are lazy so --validate and --fabrication can run headless.
try:
    import pygame
except ImportError:
    pygame = None
try:
    import moderngl
except ImportError:
    moderngl = None


def ensure_graphics_dependencies() -> None:
    """Install/import pygame + ModernGL only when the interactive world is requested."""
    global pygame, moderngl
    missing=[]
    if pygame is None:
        missing.append("pygame>=2.6.0")
    if moderngl is None:
        missing.append("moderngl>=5.12.0")
    if missing:
        print("Installing missing graphical dependencies:", ", ".join(missing))
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        pygame = importlib.import_module("pygame")
        moderngl = importlib.import_module("moderngl")

# ============================================================================
# FLATTENED SOURCE: math3d.py
# ============================================================================
def normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        raise ValueError("Cannot normalize a zero-length vector")
    return v / n


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def angle_between_deg(a: np.ndarray, b: np.ndarray) -> float:
    a = normalize(a)
    b = normalize(b)
    return math.degrees(math.acos(clamp(float(np.dot(a, b)), -1.0, 1.0)))


def perspective_matrix(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """OpenGL right-handed perspective matrix, column-vector convention."""
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    out = np.zeros((4, 4), dtype=np.float32)
    out[0, 0] = f / aspect
    out[1, 1] = f
    out[2, 2] = (far + near) / (near - far)
    out[2, 3] = (2.0 * far * near) / (near - far)
    out[3, 2] = -1.0
    return out


def look_at_matrix(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    """OpenGL view matrix, column-vector convention."""
    eye = np.asarray(eye, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    up = normalize(up)

    f = normalize(target - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)

    out = np.eye(4, dtype=np.float32)
    out[0, :3] = s
    out[1, :3] = u
    out[2, :3] = -f
    out[0, 3] = -float(np.dot(s, eye))
    out[1, 3] = -float(np.dot(u, eye))
    out[2, 3] = float(np.dot(f, eye))
    return out


def basis_from_axis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return two perpendicular unit vectors spanning the plane normal to axis."""
    axis = normalize(axis)
    reference = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    if abs(float(np.dot(axis, reference))) > 0.92:
        reference = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    u = normalize(np.cross(axis, reference))
    v = normalize(np.cross(axis, u))
    return u, v

# ============================================================================
# FLATTENED SOURCE: config.py
# ============================================================================
@dataclass
class DomeConfig:
    """Serializable parameters controlling the generated dome world."""

    # Geodesic geometry, inches. This is the NOMINAL long geodesic edge,
    # not automatically the raw stock cut length after physical corner cuts are solved.
    long_edge_in: float = 72.0

    # Raw trunk geometry.
    trunk_diameter_in: float = 8.0
    radial_splits: int = 8
    arc_segments: int = 12

    # Physical panel corner construction.
    # Each triangle is a rotational end-to-side assembly. One end of each member
    # terminates into the SIDE of the next member while the other end receives the
    # previous member. Mathematical geodesic vertices are reference geometry.
    panel_joint_mode: str = "cyclic_pinwheel_butt"
    panel_joint_handedness: str = "clockwise"  # viewed from dome exterior

    # Raw wedge rotation around each strut longitudinal axis. These are the four
    # cardinal physical orientations of the 45-degree sector cross-section.
    # The name states where the SECTOR POINT faces.
    #   point_dome_in   : point -> sphere center (legacy/default)
    #   point_panel_in  : point -> center of its triangular panel
    #   point_dome_out  : point -> sky / dome exterior
    #   point_panel_out : point -> across the panel edge / seam
    wedge_orientation: str = "point_dome_in"

    # CRITICAL NODE-CLEANING RULE:
    # The receiving/through end is NOT allowed to protrude freely past a dome vertex.
    # Its physical cut is the plane of the incoming mathematical triangle edge,
    # extruded through the panel normal. This clips every panel to its own triangular
    # footprint and removes the spikes/overlaps at multi-panel dome vertices.
    vertex_trim_mode: str = "triangle_envelope"

    # Spacer / gasket geometry between complete, duplicated triangle panels.
    spacer_mode: str = "rigid"  # rigid | hose | none
    hose_outer_diameter_in: float = 1.25
    hose_segments: int = 12

    # Renderable connector indicators.
    node_radius_in: float = 2.25
    skin_enabled: bool = False
    skin_offset_in: float = 4.10

    # ANALYSIS-ONLY panel explosion. Every complete triangular frame is translated
    # rigidly along its own outward face normal by this amount. This does NOT alter
    # fabrication geometry; it only opens the seams so wedge orientation can be inspected.
    # At zero the model is the real assembled dome.
    panel_explode_in: float = 0.0

    # Fabrication jig.
    jig_enabled: bool = True
    jig_base_margin_in: float = 7.0
    jig_base_thickness_in: float = 0.75
    jig_rail_width_in: float = 0.75
    jig_rail_height_in: float = 1.00
    jig_cut_guide_thickness_in: float = 0.20
    jig_cut_guide_height_in: float = 5.50
    jig_world_clearance_in: float = 30.0

    # Material estimates.
    dry_wood_density_lb_ft3: float = 32.0
    green_wood_density_lb_ft3: float = 55.0
    rigid_spacer_density_lb_ft3: float = 35.0

    # First-person camera.
    camera_height_in: float = 68.0
    walk_speed_in_s: float = 72.0
    sprint_multiplier: float = 3.0
    mouse_sensitivity_deg_px: float = 0.10

    # Window.
    window_width: int = 1600
    window_height: int = 900
    fov_deg: float = 70.0
    near_clip_in: float = 0.5
    far_clip_in: float = 5000.0

    def validate(self) -> None:
        if self.long_edge_in <= 0:
            raise ValueError("long_edge_in must be positive")
        if self.trunk_diameter_in <= 0:
            raise ValueError("trunk_diameter_in must be positive")
        if self.radial_splits < 3:
            raise ValueError("radial_splits must be >= 3")
        if self.arc_segments < 2:
            raise ValueError("arc_segments must be >= 2")
        if self.panel_joint_mode != "cyclic_pinwheel_butt":
            raise ValueError("panel_joint_mode must be cyclic_pinwheel_butt")
        if self.panel_joint_handedness not in {"clockwise", "counterclockwise"}:
            raise ValueError("panel_joint_handedness must be clockwise or counterclockwise")
        if self.wedge_orientation not in {
            "point_dome_in", "point_panel_in", "point_dome_out", "point_panel_out"
        }:
            raise ValueError(
                "wedge_orientation must be point_dome_in, point_panel_in, "
                "point_dome_out, or point_panel_out"
            )
        if self.vertex_trim_mode != "triangle_envelope":
            raise ValueError("vertex_trim_mode must be triangle_envelope")
        if self.hose_outer_diameter_in <= 0:
            raise ValueError("hose_outer_diameter_in must be positive")
        if self.hose_segments < 6:
            raise ValueError("hose_segments must be >= 6")
        if self.spacer_mode not in {"rigid", "hose", "none"}:
            raise ValueError("spacer_mode must be rigid, hose, or none")
        if self.panel_explode_in < 0:
            raise ValueError("panel_explode_in must be >= 0")
        if self.jig_base_margin_in < 0:
            raise ValueError("jig_base_margin_in must be >= 0")
        if self.jig_base_thickness_in <= 0:
            raise ValueError("jig_base_thickness_in must be positive")
        if self.jig_rail_width_in <= 0 or self.jig_rail_height_in <= 0:
            raise ValueError("jig rail dimensions must be positive")
        if self.jig_cut_guide_thickness_in <= 0 or self.jig_cut_guide_height_in <= 0:
            raise ValueError("jig cut-guide dimensions must be positive")

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DomeConfig":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))

        # Backward compatibility with the previous pinwheel package. The old free
        # through-overhang parameter caused the node spikes this revision removes.
        data.pop("joint_receiving_overhang_in", None)

        obj = cls(**data)
        obj.validate()
        return obj

# ============================================================================
# FLATTENED SOURCE: geometry.py
# ============================================================================
EPS = 1.0e-10


@dataclass
class EdgeInfo:
    key: tuple[int, int]
    length: float
    edge_type: str
    adjacent_faces: list[int] = field(default_factory=list)
    is_base: bool = False


@dataclass
class FaceInfo:
    index: int
    # vertices are guaranteed CCW when viewed from the exterior/outward normal.
    vertices: tuple[int, int, int]
    normal: np.ndarray
    center: np.ndarray
    face_type: str


@dataclass
class MemberInfo:
    """One physical raw-log-sector member owned by exactly one triangular panel.

    IMPORTANT: nominal_start/end are geodesic references. physical receiving and butt
    boundaries are solved separately. Every member is receiving/through at one end and
    terminating/butt at the other.
    """

    member_id: str
    face_index: int
    local_edge_index: int
    edge_key: tuple[int, int]
    edge_type: str

    directed_start_vertex: int
    directed_end_vertex: int
    receiving_vertex: int
    butt_vertex: int

    nominal_start: np.ndarray
    nominal_end: np.ndarray
    tangent: np.ndarray
    face_normal: np.ndarray
    inward: np.ndarray
    point_offset_in: float
    nominal_length_in: float

    # Pinwheel connectivity.
    receives_member_id: str
    butt_into_member_id: str
    handedness: str

    # Receiving/through-end VERTEX CLEAN CUT. The old implementation used a
    # perpendicular cap with arbitrary overhang beyond the virtual vertex. That caused
    # neighboring panel corners to overlap at dome nodes. The receiving end is now
    # clipped by the incoming ideal triangle-edge plane, extruded through the panel normal.
    receiving_plane_point: np.ndarray
    receiving_plane_normal: np.ndarray
    receiving_axis_parameter_in: float
    receiving_axis_setback_in: float
    receiving_axis_extension_in: float
    receiving_cut_points: np.ndarray

    # Butt cut is an oblique plane coincident with the receiving neighbor's
    # PANEL_INTERIOR radial face.
    butt_plane_point: np.ndarray
    butt_plane_normal: np.ndarray
    butt_axis_parameter_in: float
    butt_setback_in: float
    butt_contact_points: np.ndarray

    # Fabrication/reporting lengths.
    physical_axis_length_in: float
    physical_stock_length_in: float
    volume_equivalent_length_in: float

    @property
    def length_in(self) -> float:
        """Backward-compatible alias: physical maximum stock length, not nominal edge."""
        return self.physical_stock_length_in


@dataclass
class PanelJointInfo:
    joint_id: str
    face_index: int
    corner_vertex: int
    virtual_vertex: np.ndarray
    terminating_member_id: str
    receiving_member_id: str
    contact_plane_point: np.ndarray
    contact_plane_normal: np.ndarray
    contact_points: np.ndarray
    receiving_axis_setback_in: float
    vertex_trim_plane_point: np.ndarray
    vertex_trim_plane_normal: np.ndarray


@dataclass
class SeamInfo:
    seam_id: str
    edge_key: tuple[int, int]
    edge_type: str
    face_a: int
    face_b: int
    start: np.ndarray
    end: np.ndarray
    tangent: np.ndarray
    fold_angle_deg: float
    internal_dihedral_deg: float
    raw_gap_angle_deg: float
    member_point_offset_in: float
    contact_depth_in: float
    spacer_base_width_in: float
    hose_max_radius_in: float
    hose_max_diameter_in: float
    normal_a: np.ndarray
    normal_b: np.ndarray
    inward_a: np.ndarray
    inward_b: np.ndarray
    apex_start: np.ndarray
    apex_end: np.ndarray
    point_a_start: np.ndarray
    point_a_end: np.ndarray
    point_b_start: np.ndarray
    point_b_end: np.ndarray


@dataclass
class GeodesicTopology:
    vertices: np.ndarray
    faces: list[FaceInfo]
    edges: dict[tuple[int, int], EdgeInfo]
    sphere_radius_in: float
    long_edge_in: float
    short_edge_in: float


@dataclass
class DomePhysicalModel:
    config: DomeConfig
    topology: GeodesicTopology
    members: list[MemberInfo]
    seams: list[SeamInfo]
    joints: list[PanelJointInfo]

    @property
    def base_edges(self) -> list[EdgeInfo]:
        return [edge for edge in self.topology.edges.values() if edge.is_base]

    @property
    def member_by_id(self) -> dict[str, MemberInfo]:
        return {m.member_id: m for m in self.members}


def _icosahedron_polar() -> tuple[list[np.ndarray], list[tuple[int, int, int]]]:
    """Create an icosahedron oriented so a 2V subdivision cuts cleanly at z=0."""
    verts: list[np.ndarray] = [np.array([0.0, 0.0, 1.0], dtype=np.float64)]
    z = 1.0 / math.sqrt(5.0)
    ring_r = 2.0 / math.sqrt(5.0)

    for i in range(5):
        a = math.radians(i * 72.0)
        verts.append(np.array([ring_r * math.cos(a), ring_r * math.sin(a), z], dtype=np.float64))

    for i in range(5):
        a = math.radians(36.0 + i * 72.0)
        verts.append(np.array([ring_r * math.cos(a), ring_r * math.sin(a), -z], dtype=np.float64))

    verts.append(np.array([0.0, 0.0, -1.0], dtype=np.float64))

    faces: list[tuple[int, int, int]] = []
    for i in range(5):
        faces.append((0, 1 + i, 1 + ((i + 1) % 5)))
    for i in range(5):
        u = 1 + i
        un = 1 + ((i + 1) % 5)
        l = 6 + i
        lp = 6 + ((i - 1) % 5)
        faces.append((u, l, un))
        faces.append((u, lp, l))
    for i in range(5):
        faces.append((11, 6 + ((i + 1) % 5), 6 + i))
    return verts, faces


def _subdivide_once_projected(
    vertices: list[np.ndarray], faces: list[tuple[int, int, int]]
) -> tuple[list[np.ndarray], list[tuple[int, int, int]]]:
    """Subdivide every triangle into four and project new midpoints to the unit sphere."""
    new_vertices = [v.copy() for v in vertices]
    midpoint_cache: dict[tuple[int, int], int] = {}

    def midpoint_index(i: int, j: int) -> int:
        key = tuple(sorted((i, j)))
        if key in midpoint_cache:
            return midpoint_cache[key]
        p = normalize((new_vertices[i] + new_vertices[j]) * 0.5)
        index = len(new_vertices)
        new_vertices.append(p)
        midpoint_cache[key] = index
        return index

    new_faces: list[tuple[int, int, int]] = []
    for a, b, c in faces:
        ab = midpoint_index(a, b)
        bc = midpoint_index(b, c)
        ca = midpoint_index(c, a)
        new_faces.extend([(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)])
    return new_vertices, new_faces


def _canonical_outward_triangle(vertices: np.ndarray, tri: tuple[int, int, int]) -> tuple[tuple[int, int, int], np.ndarray]:
    """Return a triangle wound CCW as seen from exterior plus its outward normal."""
    a, b, c = vertices[list(tri)]
    n = normalize(np.cross(b - a, c - a))
    center = (a + b + c) / 3.0
    if float(np.dot(n, center)) < 0.0:
        tri = (tri[0], tri[2], tri[1])
        a, b, c = vertices[list(tri)]
        n = normalize(np.cross(b - a, c - a))
    return tri, n


def build_2v_hemisphere(long_edge_in: float) -> GeodesicTopology:
    """Generate the standard 40-face, 26-vertex 2V geodesic hemisphere."""
    verts, faces = _icosahedron_polar()
    verts, faces = _subdivide_once_projected(verts, faces)

    hemi_faces_old = [tri for tri in faces if all(verts[i][2] >= -1e-10 for i in tri)]
    used = sorted({i for tri in hemi_faces_old for i in tri})
    remap = {old: new for new, old in enumerate(used)}
    unit_vertices = np.array([verts[i] for i in used], dtype=np.float64)
    hemi_faces = [tuple(remap[i] for i in tri) for tri in hemi_faces_old]

    edge_lengths_unit: list[float] = []
    edge_keys_unit: set[tuple[int, int]] = set()
    for tri in hemi_faces:
        for i, j in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = tuple(sorted((i, j)))
            if key not in edge_keys_unit:
                edge_keys_unit.add(key)
                edge_lengths_unit.append(float(np.linalg.norm(unit_vertices[i] - unit_vertices[j])))

    long_factor = max(edge_lengths_unit)
    radius = long_edge_in / long_factor
    vertices = unit_vertices * radius

    raw_face_data: list[tuple[tuple[int, int, int], np.ndarray, np.ndarray, list[float]]] = []
    all_lengths: list[float] = []
    for tri_raw in hemi_faces:
        tri, n = _canonical_outward_triangle(vertices, tri_raw)
        center = vertices[list(tri)].mean(axis=0)
        lengths = [
            float(np.linalg.norm(vertices[tri[1]] - vertices[tri[0]])),
            float(np.linalg.norm(vertices[tri[2]] - vertices[tri[1]])),
            float(np.linalg.norm(vertices[tri[0]] - vertices[tri[2]])),
        ]
        all_lengths.extend(lengths)
        raw_face_data.append((tri, n, center, lengths))

    short_edge = min(all_lengths)
    long_edge = max(all_lengths)
    threshold = (short_edge + long_edge) * 0.5

    face_infos: list[FaceInfo] = []
    for idx, (tri, n, center, lengths) in enumerate(raw_face_data):
        count_long = sum(1 for x in lengths if x >= threshold)
        face_type = "AAA" if count_long == 3 else "BAB"
        face_infos.append(FaceInfo(idx, tri, n, center, face_type))

    adjacency: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face in face_infos:
        a, b, c = face.vertices
        for i, j in ((a, b), (b, c), (c, a)):
            adjacency[tuple(sorted((i, j)))].append(face.index)

    edges: dict[tuple[int, int], EdgeInfo] = {}
    for key, face_ids in adjacency.items():
        length = float(np.linalg.norm(vertices[key[1]] - vertices[key[0]]))
        edge_type = "A" if length >= threshold else "B"
        edges[key] = EdgeInfo(
            key=key,
            length=length,
            edge_type=edge_type,
            adjacent_faces=face_ids,
            is_base=(len(face_ids) == 1),
        )

    topo = GeodesicTopology(vertices, face_infos, edges, radius, long_edge, short_edge)
    validate_topology(topo)
    return topo


def face_edge_inward(
    vertices: np.ndarray,
    face: FaceInfo,
    edge_key: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return sorted-key start/end, tangent, and panel-inward vector for a face edge."""
    start = vertices[edge_key[0]].copy()
    end = vertices[edge_key[1]].copy()
    tangent = normalize(end - start)
    midpoint = (start + end) * 0.5
    inward = face.center - midpoint
    inward = inward - tangent * float(np.dot(inward, tangent))
    inward = normalize(inward)
    inward = normalize(inward - face.normal * float(np.dot(inward, face.normal)))
    return start, end, tangent, inward


def _physical_vertex_cycle(face: FaceInfo, handedness: str) -> tuple[int, int, int]:
    """Return the cyclic vertex order used by the pinwheel.

    FaceInfo.vertices is CCW from exterior. The user's supplied sketch is CLOCKWISE
    from exterior, so default clockwise reverses the topological winding.
    """
    a, b, c = face.vertices
    if handedness == "clockwise":
        return (a, c, b)
    return (a, b, c)


WEDGE_ORIENTATION_ORDER = (
    "point_dome_in",
    "point_panel_in",
    "point_dome_out",
    "point_panel_out",
)


def wedge_orientation_rotation_deg(orientation: str) -> float:
    """Rotation of the raw sector about the strut axis in the local (panel-in, dome-out) plane.

    Zero is the historical orientation: curved arc toward +dome-out and the sector point
    toward -dome-out. Positive rotation turns the point toward +panel-in next.
    """
    mapping = {
        "point_dome_in": 0.0,
        "point_panel_in": 90.0,
        "point_dome_out": 180.0,
        "point_panel_out": 270.0,
    }
    try:
        return mapping[orientation]
    except KeyError as exc:
        raise ValueError(f"Unknown wedge orientation: {orientation}") from exc


def rotate_sector_yz(y: float, z: float, orientation: str) -> tuple[float, float]:
    """Rotate one cross-section coordinate around the longitudinal member axis."""
    a = math.radians(wedge_orientation_rotation_deg(orientation))
    c = math.cos(a)
    s = math.sin(a)
    # Standard right-handed rotation in the local Y(panel-in) / Z(dome-out) plane.
    return y * c - z * s, y * s + z * c


def sector_radial_vectors(config: DomeConfig) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return (SEAM_FACE radial vector, PINWHEEL/receiver radial vector) in local Y/Z.

    Face identity rotates with the physical wood. In the legacy point_dome_in state the
    first vector is the seam-side radial face (-Y,+Z), and the second is the triangle-side
    radial face (+Y,+Z). Rotating the wedge rotates these actual faces as solids rather
    than silently choosing new faces after the rotation.
    """
    r = config.trunk_diameter_in * 0.5
    half = math.radians((360.0 / config.radial_splits) * 0.5)
    lateral = r * math.sin(half)
    axial = r * math.cos(half)
    face_a = rotate_sector_yz(-lateral, axial, config.wedge_orientation)
    face_b = rotate_sector_yz(+lateral, axial, config.wedge_orientation)

    # At 180 degrees the two indistinguishable radial-sawn faces exchange physical
    # panel/seam sides. Swap their construction roles so the pinwheel still terminates
    # into the face that is actually available before the clean geodesic vertex cut.
    if config.wedge_orientation == "point_dome_out":
        return face_b, face_a
    return face_a, face_b


def sector_point_direction_local(config: DomeConfig) -> tuple[float, float]:
    """Unit local Y/Z direction toward which the sharp sector point faces."""
    arc_y, arc_z = rotate_sector_yz(0.0, 1.0, config.wedge_orientation)
    return -arc_y, -arc_z


def _geometry_sector_local_points(config: DomeConfig) -> list[tuple[float, float]]:
    """Exact raw-sector boundary after applying the selected 0/90/180/270-degree rotation."""
    r = config.trunk_diameter_in * 0.5
    half = math.radians((360.0 / config.radial_splits) * 0.5)
    points: list[tuple[float, float]] = [(0.0, 0.0)]
    for i in range(config.arc_segments + 1):
        angle = -half + 2.0 * half * i / config.arc_segments
        y, z = rotate_sector_yz(r * math.sin(angle), r * math.cos(angle), config.wedge_orientation)
        points.append((y, z))
    return points


def _plane_intersection_parameter(
    line_point: np.ndarray,
    line_dir: np.ndarray,
    plane_point: np.ndarray,
    plane_normal: np.ndarray,
) -> float:
    denom = float(np.dot(line_dir, plane_normal))
    if abs(denom) <= EPS:
        raise ValueError("Pinwheel butt plane is parallel to terminating member axis")
    return float(np.dot(plane_point - line_point, plane_normal) / denom)


def build_physical_model(config: DomeConfig) -> DomePhysicalModel:
    """Create the duplicated raw-wedge panels, cyclic pinwheel corner joints, and seam spacers.

    There are intentionally TWO geometry layers:
      1) the zero-thickness geodesic reference, whose vertices/edges define the dome;
      2) the physical wood, whose ends do NOT meet tip-to-tip at those vertices.

    Every panel uses the same handed pinwheel. For directed members M0, M1, M2:
        M0 terminates into the side of M1
        M1 terminates into the side of M2
        M2 terminates into the side of M0
    Therefore every member is receiving/through at its directed START and butt/terminating
    at its directed END.
    """
    config.validate()
    topology = build_2v_hemisphere(config.long_edge_in)

    radius = config.trunk_diameter_in * 0.5
    sector_angle_deg = 360.0 / config.radial_splits
    (seam_y, seam_z), (receiver_y, receiver_z) = sector_radial_vectors(config)

    # Face-edge frames define the local panel-in (+Y) and dome-out (+Z) directions.
    # The raw sector is then rotated in this plane according to wedge_orientation.
    face_edge_frames: dict[tuple[int, tuple[int, int]], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for face in topology.faces:
        a_idx, b_idx, c_idx = face.vertices
        for e in ((a_idx, b_idx), (b_idx, c_idx), (c_idx, a_idx)):
            key = tuple(sorted(e))
            face_edge_frames[(face.index, key)] = face_edge_inward(topology.vertices, face, key)

    seams: list[SeamInfo] = []
    seam_offsets: dict[tuple[int, tuple[int, int]], float] = {}
    seam_counter = {"A": 0, "B": 0}

    for edge in topology.edges.values():
        if edge.is_base:
            only_face = edge.adjacent_faces[0]
            # Place the selected SEAM_FACE outer corner on the ideal base-edge line in
            # the panel plane. This is the fold=0 specialization of the interior solver.
            seam_offsets[(only_face, edge.key)] = -seam_y
            continue

        face_a_idx, face_b_idx = edge.adjacent_faces
        face_a = topology.faces[face_a_idx]
        face_b = topology.faces[face_b_idx]
        start, end, tangent, inward_a = face_edge_frames[(face_a_idx, edge.key)]
        _, _, _, inward_b = face_edge_frames[(face_b_idx, edge.key)]

        fold = angle_between_deg(face_a.normal, face_b.normal)
        internal_dihedral = 180.0 - fold

        # Keep the exact same physical radial face assigned as SEAM_FACE while the whole
        # sector rotates. Solve the member offset so the outer endpoint of that face from
        # both panels lands on one common seam ridge. For legacy orientation this reduces
        # exactly to d = lateral - outward*tan(fold/2).
        d = -seam_y - seam_z * math.tan(math.radians(fold * 0.5))
        seam_offsets[(face_a_idx, edge.key)] = d
        seam_offsets[(face_b_idx, edge.key)] = d

        p_a_start = start + d * inward_a
        p_a_end = end + d * inward_a
        p_b_start = start + d * inward_b
        p_b_end = end + d * inward_b

        seam_vec_a = seam_y * inward_a + seam_z * face_a.normal
        seam_vec_b = seam_y * inward_b + seam_z * face_b.normal
        apex_a_start = p_a_start + seam_vec_a
        apex_a_end = p_a_end + seam_vec_a
        apex_b_start = p_b_start + seam_vec_b
        apex_b_end = p_b_end + seam_vec_b

        # Numerical averaging tolerates tiny floating-point disagreement while preserving
        # the mathematically common ridge. raw_gap is the ACTUAL included angle between
        # the two selected seam faces after orientation, not sector_angle-fold by assumption.
        apex_start = (apex_a_start + apex_b_start) * 0.5
        apex_end = (apex_a_end + apex_b_end) * 0.5
        spacer_base = float(np.linalg.norm(p_a_start - p_b_start))
        raw_gap = angle_between_deg(seam_vec_a, seam_vec_b)
        if raw_gap <= 1.0e-7 or raw_gap >= 179.999999:
            hose_max_radius = 0.0
        else:
            hose_max_radius = radius * math.tan(math.radians(raw_gap * 0.5))

        seam_counter[edge.edge_type] += 1
        seam_id = f"SEAM_{edge.edge_type}_{seam_counter[edge.edge_type]:03d}"
        seams.append(
            SeamInfo(
                seam_id=seam_id,
                edge_key=edge.key,
                edge_type=edge.edge_type,
                face_a=face_a_idx,
                face_b=face_b_idx,
                start=start,
                end=end,
                tangent=tangent,
                fold_angle_deg=fold,
                internal_dihedral_deg=internal_dihedral,
                raw_gap_angle_deg=raw_gap,
                member_point_offset_in=d,
                contact_depth_in=radius,
                spacer_base_width_in=spacer_base,
                hose_max_radius_in=hose_max_radius,
                hose_max_diameter_in=hose_max_radius * 2.0,
                normal_a=face_a.normal,
                normal_b=face_b.normal,
                inward_a=inward_a,
                inward_b=inward_b,
                apex_start=apex_start,
                apex_end=apex_end,
                point_a_start=p_a_start,
                point_a_end=p_a_end,
                point_b_start=p_b_start,
                point_b_end=p_b_end,
            )
        )

    # Build three provisional directed members for each face. The directed cycle itself
    # defines the pinwheel: edge i terminates into edge i+1, while edge i receives edge i-1.
    provisional_by_face: dict[int, list[dict[str, object]]] = {}
    for face in topology.faces:
        cycle = _physical_vertex_cycle(face, config.panel_joint_handedness)
        directed_edges = ((cycle[0], cycle[1]), (cycle[1], cycle[2]), (cycle[2], cycle[0]))
        provisional: list[dict[str, object]] = []
        for local_idx, (v_start, v_end) in enumerate(directed_edges):
            key = tuple(sorted((v_start, v_end)))
            edge = topology.edges[key]
            nominal_start = topology.vertices[v_start].copy()
            nominal_end = topology.vertices[v_end].copy()
            tangent = normalize(nominal_end - nominal_start)
            _, _, _, inward = face_edge_frames[(face.index, key)]
            d = seam_offsets[(face.index, key)]
            member_id = f"WOOD_P{face.index + 1:03d}_E{local_idx}"
            provisional.append(
                {
                    "member_id": member_id,
                    "face_index": face.index,
                    "local_edge_index": local_idx,
                    "edge_key": key,
                    "edge_type": edge.edge_type,
                    "directed_start_vertex": v_start,
                    "directed_end_vertex": v_end,
                    "nominal_start": nominal_start,
                    "nominal_end": nominal_end,
                    "tangent": tangent,
                    "inward": inward,
                    "face_normal": face.normal,
                    "point_offset_in": d,
                    "nominal_length_in": edge.length,
                    "point_origin": nominal_start + d * inward,
                }
            )
        provisional_by_face[face.index] = provisional

    local_points = _geometry_sector_local_points(config)
    members: list[MemberInfo] = []
    joints: list[PanelJointInfo] = []

    for face in topology.faces:
        pms = provisional_by_face[face.index]

        # Precompute every member's PANEL_INTERIOR radial-face plane. The interior radial
        # vector is +inward +outward. The opposite radial face is reserved for the inter-panel seam.
        interior_planes: list[tuple[np.ndarray, np.ndarray]] = []
        for pm in pms:
            tangent = pm["tangent"]  # type: ignore[assignment]
            inward = pm["inward"]  # type: ignore[assignment]
            normal = pm["face_normal"]  # type: ignore[assignment]
            point_origin = pm["point_origin"]  # type: ignore[assignment]
            if config.wedge_orientation == "point_panel_out":
                # With the sector point aimed across the seam, the curved raw-log arc is
                # the surface facing the center of the triangle. There is no flat radial
                # face on that side. Keep the pinwheel solver valid by using the tangent
                # plane at the midpoint of that curved arc as its receiving datum. This
                # represents line/tangent contact to the untouched round surface; a real
                # build would use a saddle/notch/compliant pad if broad bearing is wanted.
                arc_y, arc_z = rotate_sector_yz(0.0, radius, config.wedge_orientation)
                arc_mid = point_origin + arc_y * inward + arc_z * normal
                plane_normal = normalize(arc_y * inward + arc_z * normal)
                if float(np.dot(plane_normal, inward)) < 0.0:
                    plane_normal = -plane_normal
                interior_planes.append((arc_mid, plane_normal))
            else:
                radial_vec = receiver_y * inward + receiver_z * normal
                plane_normal = normalize(np.cross(tangent, radial_vec))
                # Preserve deterministic normal orientation. In sideways sector states this
                # physical receiver face need not literally face panel-center; it is the same
                # raw radial face carried through the 90-degree rotation.
                if float(np.dot(plane_normal, inward)) < 0.0:
                    plane_normal = -plane_normal
                interior_planes.append((point_origin, plane_normal))

        # Butt-contact polygons: member i is cut by member i+1's interior-side plane.
        butt_points_by_member: list[np.ndarray] = []
        butt_axis_params: list[float] = []
        butt_vertex_params: list[list[float]] = []
        for i, pm in enumerate(pms):
            receiver_i = (i + 1) % 3
            plane_point, plane_normal = interior_planes[receiver_i]
            origin = pm["point_origin"]  # type: ignore[assignment]
            tangent = pm["tangent"]  # type: ignore[assignment]
            inward = pm["inward"]  # type: ignore[assignment]
            normal = pm["face_normal"]  # type: ignore[assignment]

            params: list[float] = []
            points: list[np.ndarray] = []
            for y, z in local_points:
                line_point = origin + y * inward + z * normal
                t = _plane_intersection_parameter(line_point, tangent, plane_point, plane_normal)
                params.append(t)
                points.append(line_point + t * tangent)
            butt_points_by_member.append(np.asarray(points, dtype=np.float64))
            butt_vertex_params.append(params)
            butt_axis_params.append(
                _plane_intersection_parameter(origin, tangent, plane_point, plane_normal)
            )

        # ------------------------------------------------------------------
        # CLEAN GEODESIC VERTEX CUTS
        # ------------------------------------------------------------------
        # The previous revision intentionally let each receiving member continue past
        # the virtual geodesic vertex so the incoming butt member had side material to
        # land on. In a complete dome those free overhangs collide with other panels
        # converging on the same topological vertex.
        #
        # The corrected construction keeps the pinwheel END-TO-SIDE joint but clips the
        # receiving end to the exact triangular face envelope. For member i, the plane
        # that limits its directed START is the mathematical edge occupied by member
        # i-1, extruded through the face normal. This is the red cut requested by the
        # user: it is a vertical-to-panel plane through the geodesic vertex. The seam-side
        # corner of the raw sector can reach the mathematical vertex, while no part of
        # the member is allowed to trespass across the incoming edge into a neighboring
        # panel's face footprint.
        receiving_planes: list[tuple[np.ndarray, np.ndarray]] = []
        receiving_points_by_member: list[np.ndarray] = []
        receiving_vertex_params: list[list[float]] = []
        receiving_axis_params: list[float] = []

        for i, pm in enumerate(pms):
            prev_i = (i - 1) % 3
            prev_pm = pms[prev_i]
            # The previous ideal edge and face normal define the vertex clipping plane.
            # face_edge_inward returns a normal lying in the panel plane and pointing
            # toward the triangle interior; that makes the valid half-space deterministic.
            _, _, _, prev_edge_inward = face_edge_frames[(face.index, prev_pm["edge_key"])]  # type: ignore[index]
            plane_point = pm["nominal_start"]  # the shared virtual geodesic vertex
            plane_normal = prev_edge_inward
            receiving_planes.append((plane_point, plane_normal))

            origin = pm["point_origin"]  # type: ignore[assignment]
            tangent = pm["tangent"]  # type: ignore[assignment]
            inward = pm["inward"]  # type: ignore[assignment]
            normal = pm["face_normal"]  # type: ignore[assignment]

            params: list[float] = []
            points: list[np.ndarray] = []
            for y, z in local_points:
                line_point = origin + y * inward + z * normal
                t = _plane_intersection_parameter(
                    line_point, tangent, plane_point, plane_normal
                )
                params.append(t)
                points.append(line_point + t * tangent)

            receiving_points_by_member.append(np.asarray(points, dtype=np.float64))
            receiving_vertex_params.append(params)
            receiving_axis_params.append(
                _plane_intersection_parameter(origin, tangent, plane_point, plane_normal)
            )

        # Exact sector centroid along the rotated arc bisector. End-plane intersection
        # parameters are affine across the cross-section, so evaluating at this centroid
        # gives the exact average extrusion length used for volume in every orientation.
        theta = math.radians(sector_angle_deg)
        centroid_radius = 4.0 * radius * math.sin(theta * 0.5) / (3.0 * theta)
        centroid_y, centroid_z = rotate_sector_yz(
            0.0, centroid_radius, config.wedge_orientation
        )

        for i, pm in enumerate(pms):
            receiver_i = (i + 1) % 3
            previous_i = (i - 1) % 3

            butt_plane_point, butt_plane_normal = interior_planes[receiver_i]
            receive_plane_point, receive_plane_normal = receiving_planes[i]
            origin = pm["point_origin"]  # type: ignore[assignment]
            tangent = pm["tangent"]  # type: ignore[assignment]
            normal = pm["face_normal"]  # type: ignore[assignment]

            receive_axis = receiving_axis_params[i]
            butt_axis = butt_axis_params[i]
            receive_values = receiving_vertex_params[i]
            butt_values = butt_vertex_params[i]

            # Every longitudinal generator must run from the clean vertex cut to the
            # cyclic butt cut in that order. This also catches accidental flipped planes.
            generator_lengths = [b - a for a, b in zip(receive_values, butt_values)]
            if min(generator_lengths) <= 1e-8:
                raise ValueError(
                    f"Invalid vertex-clean pinwheel member on face {face.index}, edge {i}: "
                    "receiving cut crosses butt cut"
                )

            # Raw stock must be long enough to contain the most advanced point of each
            # oblique cut before those cuts are made.
            stock_length = max(butt_values) - min(receive_values)
            axis_length = butt_axis - receive_axis

            inward = pm["inward"]  # type: ignore[assignment]
            centroid_line_point = origin + centroid_y * inward + centroid_z * normal
            t_receive_centroid = _plane_intersection_parameter(
                centroid_line_point, tangent, receive_plane_point, receive_plane_normal
            )
            t_butt_centroid = _plane_intersection_parameter(
                centroid_line_point, tangent, butt_plane_point, butt_plane_normal
            )
            volume_length = t_butt_centroid - t_receive_centroid

            if stock_length <= 0.0 or axis_length <= 0.0 or volume_length <= 0.0:
                raise ValueError(f"Invalid pinwheel member length on face {face.index}, edge {i}")

            receiving_setback = max(0.0, receive_axis)
            receiving_extension = max(0.0, -receive_axis)

            member = MemberInfo(
                member_id=pm["member_id"],  # type: ignore[arg-type]
                face_index=face.index,
                local_edge_index=i,
                edge_key=pm["edge_key"],  # type: ignore[arg-type]
                edge_type=pm["edge_type"],  # type: ignore[arg-type]
                directed_start_vertex=pm["directed_start_vertex"],  # type: ignore[arg-type]
                directed_end_vertex=pm["directed_end_vertex"],  # type: ignore[arg-type]
                receiving_vertex=pm["directed_start_vertex"],  # type: ignore[arg-type]
                butt_vertex=pm["directed_end_vertex"],  # type: ignore[arg-type]
                nominal_start=pm["nominal_start"],  # type: ignore[arg-type]
                nominal_end=pm["nominal_end"],  # type: ignore[arg-type]
                tangent=tangent,
                face_normal=normal,
                inward=pm["inward"],  # type: ignore[arg-type]
                point_offset_in=pm["point_offset_in"],  # type: ignore[arg-type]
                nominal_length_in=pm["nominal_length_in"],  # type: ignore[arg-type]
                receives_member_id=pms[previous_i]["member_id"],  # type: ignore[arg-type]
                butt_into_member_id=pms[receiver_i]["member_id"],  # type: ignore[arg-type]
                handedness=config.panel_joint_handedness,
                receiving_plane_point=receive_plane_point,
                receiving_plane_normal=receive_plane_normal,
                receiving_axis_parameter_in=receive_axis,
                receiving_axis_setback_in=receiving_setback,
                receiving_axis_extension_in=receiving_extension,
                receiving_cut_points=receiving_points_by_member[i],
                butt_plane_point=butt_plane_point,
                butt_plane_normal=butt_plane_normal,
                butt_axis_parameter_in=butt_axis,
                butt_setback_in=pm["nominal_length_in"] - butt_axis,  # type: ignore[operator]
                butt_contact_points=butt_points_by_member[i],
                physical_axis_length_in=axis_length,
                physical_stock_length_in=stock_length,
                volume_equivalent_length_in=volume_length,
            )
            members.append(member)

            # Joint i is at the terminating end of member i. The receiver is member i+1.
            # Record both the butt-contact plane and the receiver's clean vertex trim plane
            # so the fabrication jig can display both operations explicitly.
            receiver_receive_plane_point, receiver_receive_plane_normal = receiving_planes[receiver_i]
            joints.append(
                PanelJointInfo(
                    joint_id=f"JOINT_P{face.index + 1:03d}_C{i}",
                    face_index=face.index,
                    corner_vertex=pm["directed_end_vertex"],  # type: ignore[arg-type]
                    virtual_vertex=pm["nominal_end"],  # type: ignore[arg-type]
                    terminating_member_id=pm["member_id"],  # type: ignore[arg-type]
                    receiving_member_id=pms[receiver_i]["member_id"],  # type: ignore[arg-type]
                    contact_plane_point=butt_plane_point,
                    contact_plane_normal=butt_plane_normal,
                    contact_points=butt_points_by_member[i],
                    receiving_axis_setback_in=max(0.0, receiving_axis_params[receiver_i]),
                    vertex_trim_plane_point=receiver_receive_plane_point,
                    vertex_trim_plane_normal=receiver_receive_plane_normal,
                )
            )

    model = DomePhysicalModel(config=config, topology=topology, members=members, seams=seams, joints=joints)
    validate_physical_model(model)
    return model


def validate_topology(topo: GeodesicTopology) -> None:
    if len(topo.vertices) != 26:
        raise AssertionError(f"Expected 26 hemisphere vertices, got {len(topo.vertices)}")
    if len(topo.faces) != 40:
        raise AssertionError(f"Expected 40 hemisphere faces, got {len(topo.faces)}")
    if len(topo.edges) != 65:
        raise AssertionError(f"Expected 65 unique topological edges, got {len(topo.edges)}")

    aaa = sum(face.face_type == "AAA" for face in topo.faces)
    bab = sum(face.face_type == "BAB" for face in topo.faces)
    if (aaa, bab) != (10, 30):
        raise AssertionError(f"Expected face classes (10 AAA, 30 BAB), got ({aaa}, {bab})")

    count_a = sum(edge.edge_type == "A" for edge in topo.edges.values())
    count_b = sum(edge.edge_type == "B" for edge in topo.edges.values())
    if (count_a, count_b) != (35, 30):
        raise AssertionError(f"Expected edge classes (35 A, 30 B), got ({count_a}, {count_b})")

    base = [edge for edge in topo.edges.values() if edge.is_base]
    if len(base) != 10 or any(edge.edge_type != "A" for edge in base):
        raise AssertionError("Expected exactly 10 exposed A-type base edges")

    # Every stored face must be CCW when seen from the exterior.
    for face in topo.faces:
        a, b, c = topo.vertices[list(face.vertices)]
        geometric = normalize(np.cross(b - a, c - a))
        if float(np.dot(geometric, face.normal)) < 1.0 - 1e-9:
            raise AssertionError(f"Face {face.index} winding is not consistently exterior-CCW")


def validate_physical_model(model: DomePhysicalModel) -> None:
    if len(model.members) != 120:
        raise AssertionError(f"Expected 120 duplicated panel members, got {len(model.members)}")
    a_members = sum(m.edge_type == "A" for m in model.members)
    b_members = sum(m.edge_type == "B" for m in model.members)
    if (a_members, b_members) != (60, 60):
        raise AssertionError(f"Expected 60 A and 60 B physical members, got {a_members}, {b_members}")

    if len(model.joints) != 120:
        raise AssertionError(f"Expected 120 cyclic end-to-side panel joints, got {len(model.joints)}")

    # Every panel must be one closed 3-member directed cycle, never a symmetric miter graph.
    # Each raw-sector solid must also stay inside the exact triangular face prism. The latter
    # is the clean-node invariant that removes the spikes seen in the previous build.
    by_face: dict[int, list[MemberInfo]] = defaultdict(list)
    for member in model.members:
        by_face[member.face_index].append(member)
        if member.physical_stock_length_in <= 0.0:
            raise AssertionError(f"{member.member_id} has non-positive stock length")

        # Vertex trim plane contains the face normal, so its normal lies entirely in the
        # panel plane. A nonzero dot here means the cut was accidentally tilted out of plane.
        if abs(float(np.dot(member.receiving_plane_normal, member.face_normal))) > 1e-8:
            raise AssertionError(f"{member.member_id} vertex trim plane is not vertical to its panel")
        plane_error = max(
            abs(float(np.dot(p - member.receiving_plane_point, member.receiving_plane_normal)))
            for p in member.receiving_cut_points
        )
        if plane_error > 1e-7:
            raise AssertionError(f"{member.member_id} receiving cut does not lie on its vertex trim plane")

    for face_idx, face_members in by_face.items():
        if len(face_members) != 3:
            raise AssertionError(f"Panel {face_idx} does not own exactly three members")
        mapping = {m.member_id: m.butt_into_member_id for m in face_members}
        start_id = face_members[0].member_id
        second = mapping[start_id]
        third = mapping[second]
        if mapping[third] != start_id or len({start_id, second, third}) != 3:
            raise AssertionError(f"Panel {face_idx} pinwheel does not form one 3-member cycle")
        for m in face_members:
            receiver = next(x for x in face_members if x.member_id == m.butt_into_member_id)
            if receiver.receives_member_id != m.member_id:
                raise AssertionError(f"Panel {face_idx} receiving/butt roles are not reciprocal")

        face = model.topology.faces[face_idx]

        # Vertex-boundary validation. The sector may intentionally project across its
        # OWN ideal seam edge because the inter-panel spline solver offsets the two raw
        # wedges from that abstract line. What is forbidden here is longitudinal corner
        # spill across either of the OTHER two edges meeting the member endpoints.
        # Those are the planes that caused the visible node spikes.
        by_id = {m.member_id: m for m in face_members}
        for m in face_members:
            previous = by_id[m.receives_member_id]
            receiver = by_id[m.butt_into_member_id]

            prev_start, _, _, prev_inward = face_edge_inward(
                model.topology.vertices, face, previous.edge_key
            )
            next_start, _, _, next_inward = face_edge_inward(
                model.topology.vertices, face, receiver.edge_key
            )

            # The receiving cut lies exactly on the previous edge boundary; the rest of
            # the member must proceed into the triangle from there.
            for point in m.receiving_cut_points:
                signed = float(np.dot(point - prev_start, prev_inward))
                if abs(signed) > 1e-6:
                    raise AssertionError(
                        f"{m.member_id} receiving end is not coincident with its clean vertex plane"
                    )

            # The butt end is deliberately inside the next edge because it terminates
            # against the next member's PANEL_INTERIOR_FACE before reaching the vertex.
            for point in m.butt_contact_points:
                if float(np.dot(point - prev_start, prev_inward)) < -1e-6:
                    raise AssertionError(f"{m.member_id} crosses behind its clean receiving vertex cut")
                if float(np.dot(point - next_start, next_inward)) < -1e-6:
                    raise AssertionError(f"{m.member_id} protrudes through its butt-side vertex boundary")

    if len(model.seams) != 55:
        raise AssertionError(f"Expected 55 interior seams, got {len(model.seams)}")
    a_seams = [s for s in model.seams if s.edge_type == "A"]
    b_seams = [s for s in model.seams if s.edge_type == "B"]
    if (len(a_seams), len(b_seams)) != (25, 30):
        raise AssertionError(f"Expected 25 A and 30 B seams, got {len(a_seams)}, {len(b_seams)}")

    avg_a_fold = sum(s.fold_angle_deg for s in a_seams) / len(a_seams)
    avg_b_fold = sum(s.fold_angle_deg for s in b_seams) / len(b_seams)
    if abs(avg_a_fold - 18.0291021112) > 1e-6:
        raise AssertionError(f"Unexpected A-seam fold angle: {avg_a_fold}")
    if abs(avg_b_fold - 22.4589239153) > 1e-6:
        raise AssertionError(f"Unexpected B-seam fold angle: {avg_b_fold}")

# ============================================================================
# FLATTENED SOURCE: exporters.py
# ============================================================================
def _sector_area_in2(model: DomePhysicalModel) -> float:
    cfg = model.config
    r = cfg.trunk_diameter_in * 0.5
    sector_angle_rad = math.radians(360.0 / cfg.radial_splits)
    return 0.5 * r * r * sector_angle_rad


def _cut_plane_components(member: MemberInfo, normal: np.ndarray) -> tuple[float, float, float, float, float]:
    """Describe a cut plane in the member's own tangent/inward/outward coordinate frame.

    The returned yaw/pitch are geometry descriptors, not brand-specific compound-miter-saw
    dial settings. A square crosscut has normal=(+1,0,0), yaw=0, pitch=0.
    """
    n = normalize(normal)
    x = float(np.dot(n, member.tangent))
    y = float(np.dot(n, member.inward))
    z = float(np.dot(n, member.face_normal))
    # Flip the normal to keep its along-member component nonnegative; the plane itself is unchanged.
    if x < 0.0:
        x, y, z = -x, -y, -z
    yaw = math.degrees(math.atan2(y, x))
    pitch = math.degrees(math.atan2(z, math.hypot(x, y)))
    return x, y, z, yaw, pitch


def export_bom(model: DomePhysicalModel, path: str | Path) -> None:
    """Export fabrication quantities with nominal geometry and solved physical cuts separated."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cfg = model.config
    sector_area_in2 = _sector_area_in2(model)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "object_id",
                "object_type",
                "class",
                "nominal_geodesic_length_in",
                "physical_stock_blank_length_in",
                "physical_sector_point_axis_length_in",
                "volume_equivalent_length_in",
                "receiving_axis_setback_from_virtual_vertex_in",
                "receiving_axis_extension_past_virtual_vertex_in",
                "butt_axis_setback_from_virtual_vertex_in",
                "receives_member",
                "butt_into_member",
                "pinwheel_handedness",
                "wedge_orientation",
                "vertex_trim_mode",
                "cross_section_area_in2",
                "volume_ft3",
                "estimated_dry_mass_lb",
                "face_or_seam",
                "fold_angle_deg",
                "gap_angle_deg",
                "spacer_base_width_in",
            ]
        )

        for m in model.members:
            volume_in3 = sector_area_in2 * m.volume_equivalent_length_in
            volume_ft3 = volume_in3 / 1728.0
            writer.writerow(
                [
                    m.member_id,
                    "raw_log_sector_vertex_clean_pinwheel_member",
                    m.edge_type,
                    f"{m.nominal_length_in:.6f}",
                    f"{m.physical_stock_length_in:.6f}",
                    f"{m.physical_axis_length_in:.6f}",
                    f"{m.volume_equivalent_length_in:.6f}",
                    f"{m.receiving_axis_setback_in:.6f}",
                    f"{m.receiving_axis_extension_in:.6f}",
                    f"{m.butt_setback_in:.6f}",
                    m.receives_member_id,
                    m.butt_into_member_id,
                    m.handedness,
                    cfg.wedge_orientation,
                    cfg.vertex_trim_mode,
                    f"{sector_area_in2:.6f}",
                    f"{volume_ft3:.8f}",
                    f"{volume_ft3 * cfg.dry_wood_density_lb_ft3:.6f}",
                    f"PANEL_{m.face_index + 1:03d}",
                    "",
                    "",
                    "",
                ]
            )

        for s in model.seams:
            base = s.spacer_base_width_in
            side = s.contact_depth_in
            height = math.sqrt(max(side * side - (base * 0.5) ** 2, 0.0))
            area = 0.5 * base * height
            length = float(np.linalg.norm(s.end - s.start))
            volume_ft3 = area * length / 1728.0
            writer.writerow(
                [
                    f"SPACER_{s.seam_id}",
                    "rigid_triangular_spline",
                    s.edge_type,
                    f"{length:.6f}",
                    f"{length:.6f}",
                    f"{length:.6f}",
                    f"{length:.6f}",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    cfg.wedge_orientation,
                    "",
                    f"{area:.6f}",
                    f"{volume_ft3:.8f}",
                    f"{volume_ft3 * cfg.rigid_spacer_density_lb_ft3:.6f}",
                    s.seam_id,
                    f"{s.fold_angle_deg:.6f}",
                    f"{s.raw_gap_angle_deg:.6f}",
                    f"{s.spacer_base_width_in:.6f}",
                ]
            )


def export_cut_schedule(model: DomePhysicalModel, path: str | Path) -> None:
    """Export both end-cut planes for all 120 raw-sector members.

    Each member receives TWO deliberately different cuts:
      * RECEIVE/VERTEX CLEAN CUT: triangle-envelope plane through the geodesic node.
      * BUTT/PINWHEEL CUT: compound plane coincident with the next member's interior radial face.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "panel_id", "panel_type", "member_id", "local_edge_index", "edge_class",
                "wedge_orientation", "nominal_edge_in", "raw_blank_length_in", "cut_end", "cut_purpose",
                "plane_normal_local_x_along_member", "plane_normal_local_y_panel_inward",
                "plane_normal_local_z_dome_outward", "normal_yaw_from_square_deg",
                "normal_pitch_out_of_panel_deg", "axis_setback_from_virtual_vertex_in",
                "mate_member_id",
            ]
        )
        for m in model.members:
            face = model.topology.faces[m.face_index]
            rx, ry, rz, ryaw, rpitch = _cut_plane_components(m, m.receiving_plane_normal)
            writer.writerow(
                [
                    f"PANEL_{m.face_index + 1:03d}", face.face_type, m.member_id, m.local_edge_index,
                    m.edge_type, model.config.wedge_orientation, f"{m.nominal_length_in:.6f}", f"{m.physical_stock_length_in:.6f}",
                    "RECEIVING", "CLEAN_GEODESIC_VERTEX_TRIANGLE_ENVELOPE",
                    f"{rx:.9f}", f"{ry:.9f}", f"{rz:.9f}", f"{ryaw:.6f}", f"{rpitch:.6f}",
                    f"{m.receiving_axis_setback_in:.6f}", m.receives_member_id,
                ]
            )
            bx, by, bz, byaw, bpitch = _cut_plane_components(m, m.butt_plane_normal)
            writer.writerow(
                [
                    f"PANEL_{m.face_index + 1:03d}", face.face_type, m.member_id, m.local_edge_index,
                    m.edge_type, model.config.wedge_orientation, f"{m.nominal_length_in:.6f}", f"{m.physical_stock_length_in:.6f}",
                    "BUTT", "CYCLIC_PINWHEEL_END_TO_RECEIVER_INTERIOR_FACE",
                    f"{bx:.9f}", f"{by:.9f}", f"{bz:.9f}", f"{byaw:.6f}", f"{bpitch:.6f}",
                    f"{m.butt_setback_in:.6f}", m.butt_into_member_id,
                ]
            )


def _panel_frame(model: DomePhysicalModel, panel_index: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    face = model.topology.faces[panel_index]
    vertices = model.topology.vertices[list(face.vertices)]
    anchor = vertices[0]
    x = normalize(vertices[1] - vertices[0])
    z = face.normal
    y = normalize(np.cross(z, x))
    if float(np.dot(vertices[2] - anchor, y)) < 0.0:
        x = -x
        y = -y
    return anchor, x, y, z


def _panel_xy(p: np.ndarray, frame: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]) -> tuple[float, float]:
    anchor, x, y, _ = frame
    d = p - anchor
    return float(np.dot(d, x)), float(np.dot(d, y))


def export_panel_jig_svg(model: DomePhysicalModel, panel_index: int, path: str | Path) -> None:
    """Export a printable/scalable exterior-view cutting/assembly jig drawing."""
    panel_index %= len(model.topology.faces)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    face = model.topology.faces[panel_index]
    frame = _panel_frame(model, panel_index)
    members = sorted([m for m in model.members if m.face_index == panel_index], key=lambda m: m.local_edge_index)

    tri = [_panel_xy(model.topology.vertices[i], frame) for i in face.vertices]
    all_xy = list(tri)
    for m in members:
        all_xy.extend(_panel_xy(p, frame) for p in m.receiving_cut_points)
        all_xy.extend(_panel_xy(p, frame) for p in m.butt_contact_points)
    min_x = min(x for x, _ in all_xy) - 6.0
    max_x = max(x for x, _ in all_xy) + 6.0
    min_y = min(y for _, y in all_xy) - 6.0
    max_y = max(y for _, y in all_xy) + 6.0
    scale = 6.0  # SVG pixels per inch; viewBox remains dimensional through labels.
    width = (max_x - min_x) * scale
    height = (max_y - min_y) * scale

    def pt(x: float, y: float) -> tuple[float, float]:
        return (x - min_x) * scale, (max_y - y) * scale

    def points_string(points: list[tuple[float, float]]) -> str:
        return " ".join(f"{pt(x,y)[0]:.3f},{pt(x,y)[1]:.3f}" for x, y in points)

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="0 0 {width:.1f} {height:.1f}">')
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<polygon points="{points_string(tri)}" fill="none" stroke="#1976a8" stroke-width="2"/>')
    orientation = html.escape(model.config.wedge_orientation.upper())
    parts.append(f'<text x="12" y="22" font-family="monospace" font-size="14">PANEL {panel_index+1:03d} / {html.escape(face.face_type)} / EXTERIOR VIEW / {orientation}</text>')
    parts.append('<text x="12" y="40" font-family="monospace" font-size="12" fill="#b00020">RED = CLEAN VERTEX CUT</text>')
    parts.append('<text x="250" y="40" font-family="monospace" font-size="12" fill="#087f4b">GREEN = CYCLIC BUTT CUT / CONTACT</text>')

    for m in members:
        origin = m.nominal_start + m.point_offset_in * m.inward
        a = origin + m.receiving_axis_parameter_in * m.tangent
        b = origin + m.butt_axis_parameter_in * m.tangent
        ax, ay = pt(*_panel_xy(a, frame)); bx, by = pt(*_panel_xy(b, frame))
        parts.append(f'<line x1="{ax:.3f}" y1="{ay:.3f}" x2="{bx:.3f}" y2="{by:.3f}" stroke="#c57800" stroke-width="1.5"/>')

        rpoly = [_panel_xy(p, frame) for p in m.receiving_cut_points]
        bpoly = [_panel_xy(p, frame) for p in m.butt_contact_points]
        parts.append(f'<polyline points="{points_string(rpoly + [rpoly[0]])}" fill="none" stroke="#d50000" stroke-width="2"/>')
        parts.append(f'<polyline points="{points_string(bpoly + [bpoly[0]])}" fill="none" stroke="#00a65a" stroke-width="2"/>')
        mx = (ax + bx) * 0.5; my = (ay + by) * 0.5
        label = f'{m.member_id} {m.edge_type} blank={m.physical_stock_length_in:.3f}in'
        parts.append(f'<text x="{mx+5:.3f}" y="{my-5:.3f}" font-family="monospace" font-size="10">{html.escape(label)}</text>')

    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def _member_recipe_signature(member: MemberInfo) -> tuple[object, ...]:
    _, _, _, receive_yaw, receive_pitch = _cut_plane_components(member, member.receiving_plane_normal)
    _, _, _, butt_yaw, butt_pitch = _cut_plane_components(member, member.butt_plane_normal)
    return (
        member.edge_type,
        round(member.point_offset_in, 5),
        round(member.physical_stock_length_in, 5),
        round(member.receiving_axis_setback_in, 5),
        round(member.butt_setback_in, 5),
        round(receive_yaw, 4),
        round(receive_pitch, 4),
        round(butt_yaw, 4),
        round(butt_pitch, 4),
    )


def _panel_variant_signature(model: DomePhysicalModel, panel_index: int) -> tuple[object, ...]:
    face = model.topology.faces[panel_index]
    members = sorted([m for m in model.members if m.face_index == panel_index], key=lambda m: m.local_edge_index)
    recipes = [_member_recipe_signature(m) for m in members]
    # A rotated jig is the same physical recipe; canonicalize cyclic rotations while
    # preserving handedness (do not mirror/reverse the order).
    rotations = [tuple(recipes[i:] + recipes[:i]) for i in range(3)]
    return (model.config.wedge_orientation, face.face_type, min(rotations))


def export_fabrication_package(model: DomePhysicalModel, directory: str | Path) -> None:
    """Generate the complete fabrication package, including exact reusable 3D jig variants."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    export_bom(model, directory / "DOME_BOM.csv")
    export_cut_schedule(model, directory / "ALL_MEMBER_CUT_SCHEDULE.csv")

    svg_dir = directory / "panel_jig_svgs"
    svg_dir.mkdir(exist_ok=True)
    for panel_index in range(len(model.topology.faces)):
        export_panel_jig_svg(model, panel_index, svg_dir / f"PANEL_{panel_index + 1:03d}_JIG.svg")

    # Collapse rotationally equivalent panel fixtures into reusable physical jig variants.
    groups: dict[tuple[object, ...], list[int]] = {}
    for panel_index in range(len(model.topology.faces)):
        groups.setdefault(_panel_variant_signature(model, panel_index), []).append(panel_index)

    variant_rows: list[list[object]] = []
    variant_obj_dir = directory / "jig_variant_objs"
    variant_obj_dir.mkdir(exist_ok=True)

    # Local import avoids making the core geometry/export modules depend on ModernGL/Pygame.
    # Single-file edition: build_fabrication_jig/export_mesh_obj are globals below.

    for variant_number, (_, panel_indices) in enumerate(sorted(groups.items(), key=lambda item: item[1][0]), start=1):
        representative = panel_indices[0]
        face_type = model.topology.faces[representative].face_type
        variant_id = f"JIG_VARIANT_{variant_number:02d}_{face_type}"
        variant_rows.append(
            [
                variant_id,
                model.config.wedge_orientation,
                f"PANEL_{representative + 1:03d}",
                " ".join(f"PANEL_{i + 1:03d}" for i in panel_indices),
                len(panel_indices),
            ]
        )
        jig = build_fabrication_jig(model, representative)
        export_mesh_obj(jig["jig_fixture"], variant_obj_dir / f"{variant_id}_FIXTURE.obj", variant_id + "_FIXTURE")
        export_mesh_obj(jig["jig_wood"], variant_obj_dir / f"{variant_id}_EXAMPLE_WOOD.obj", variant_id + "_EXAMPLE_WOOD")

    with (directory / "JIG_VARIANTS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["jig_variant", "wedge_orientation", "representative_panel", "compatible_panels", "panel_count"])
        writer.writerows(variant_rows)

# ============================================================================
# FLATTENED SOURCE: mesh_builders.py
# ============================================================================
# RGBA colors are deliberately centralized so the world remains easy to retheme.
# Orientation-identification colors for the raw wedge itself.
# The colors rotate with the actual wedge geometry so the user can immediately tell
# how the sector is oriented in 3D.
WEDGE_LEFT_COLOR = (0.92, 0.18, 0.14, 1.0)
WEDGE_RIGHT_COLOR = (0.18, 0.82, 0.22, 1.0)
WEDGE_TIP_COLOR = (1.00, 0.92, 0.10, 1.0)
WEDGE_BACK_COLOR = (0.60, 0.38, 0.18, 1.0)
SPACER_COLOR = (0.85, 0.68, 0.18, 1.0)
HOSE_COLOR = (0.10, 0.10, 0.12, 1.0)
NODE_COLOR = (0.70, 0.70, 0.73, 1.0)
SKIN_COLOR = (0.25, 0.55, 0.78, 0.18)
IDEAL_A_COLOR = (0.20, 0.85, 1.00, 1.0)
IDEAL_B_COLOR = (0.70, 0.35, 1.00, 1.0)
BASE_COLOR = (0.35, 1.00, 0.45, 1.0)
GROUND_COLOR = (0.25, 0.27, 0.30, 1.0)
SELECT_COLOR = (1.00, 0.25, 0.15, 1.0)
PINWHEEL_AXIS_COLOR = (1.00, 0.58, 0.12, 0.95)
PINWHEEL_CONTACT_COLOR = (0.25, 1.00, 0.55, 0.95)
VIRTUAL_VERTEX_COLOR = (1.00, 0.20, 0.75, 1.0)
VERTEX_CUT_COLOR = (1.00, 0.08, 0.08, 1.0)
JIG_BASE_COLOR = (0.28, 0.30, 0.33, 0.82)
JIG_RAIL_COLOR = (0.52, 0.55, 0.58, 1.0)
JIG_GUIDE_VERTEX_COLOR = (0.95, 0.12, 0.12, 0.72)
JIG_GUIDE_BUTT_COLOR = (0.18, 0.88, 0.50, 0.62)
JIG_IDEAL_COLOR = (0.25, 0.80, 1.00, 1.0)


@dataclass
class MeshData:
    """CPU-side indexed triangle mesh using position, normal, RGBA vertex fields."""

    vertices: np.ndarray
    indices: np.ndarray


@dataclass
class LineData:
    """CPU-side non-indexed line vertices using position and RGBA color."""

    vertices: np.ndarray


class MeshAccumulator:
    """Build a single indexed mesh from many primitives."""

    def __init__(self) -> None:
        self.vertices: list[list[float]] = []
        self.indices: list[int] = []

    def _push_vertex(self, position: np.ndarray, normal: np.ndarray, color: tuple[float, float, float, float]) -> int:
        idx = len(self.vertices)
        self.vertices.append(
            [
                float(position[0]), float(position[1]), float(position[2]),
                float(normal[0]), float(normal[1]), float(normal[2]),
                float(color[0]), float(color[1]), float(color[2]), float(color[3]),
            ]
        )
        return idx

    def add_triangle(
        self,
        p0: np.ndarray,
        p1: np.ndarray,
        p2: np.ndarray,
        color: tuple[float, float, float, float],
        normal: np.ndarray | None = None,
    ) -> None:
        if normal is None:
            n = np.cross(p1 - p0, p2 - p0)
            if np.linalg.norm(n) <= 1e-10:
                return
            normal = normalize(n)
        else:
            normal = normalize(normal)
        i0 = self._push_vertex(p0, normal, color)
        i1 = self._push_vertex(p1, normal, color)
        i2 = self._push_vertex(p2, normal, color)
        self.indices.extend([i0, i1, i2])

    def add_quad(
        self,
        p0: np.ndarray,
        p1: np.ndarray,
        p2: np.ndarray,
        p3: np.ndarray,
        color: tuple[float, float, float, float],
    ) -> None:
        n = np.cross(p1 - p0, p2 - p0)
        if np.linalg.norm(n) <= 1e-10:
            return
        n = normalize(n)
        ids = [self._push_vertex(p, n, color) for p in (p0, p1, p2, p3)]
        self.indices.extend([ids[0], ids[1], ids[2], ids[0], ids[2], ids[3]])

    def add_triangular_prism(
        self,
        a0: np.ndarray,
        b0: np.ndarray,
        c0: np.ndarray,
        a1: np.ndarray,
        b1: np.ndarray,
        c1: np.ndarray,
        color: tuple[float, float, float, float],
    ) -> None:
        self.add_triangle(a0, c0, b0, color)
        self.add_triangle(a1, b1, c1, color)
        self.add_quad(a0, a1, c1, c0, color)
        self.add_quad(a0, b0, b1, a1, color)
        self.add_quad(b0, c0, c1, b1, color)

    def add_cylinder(
        self,
        start: np.ndarray,
        end: np.ndarray,
        radius: float,
        segments: int,
        color: tuple[float, float, float, float],
    ) -> None:
        axis = normalize(end - start)
        u, v = basis_from_axis(axis)
        ring0: list[np.ndarray] = []
        ring1: list[np.ndarray] = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            radial = math.cos(a) * u + math.sin(a) * v
            ring0.append(start + radius * radial)
            ring1.append(end + radius * radial)

        for i in range(segments):
            j = (i + 1) % segments
            self.add_quad(ring0[i], ring0[j], ring1[j], ring1[i], color)

        center0 = start
        center1 = end
        for i in range(segments):
            j = (i + 1) % segments
            self.add_triangle(center0, ring0[j], ring0[i], color, -axis)
            self.add_triangle(center1, ring1[i], ring1[j], color, axis)

    def add_box(
        self,
        center: np.ndarray,
        axis_x: np.ndarray,
        axis_y: np.ndarray,
        axis_z: np.ndarray,
        size_x: float,
        size_y: float,
        size_z: float,
        color: tuple[float, float, float, float],
    ) -> None:
        """Add an oriented rectangular box from orthogonal local axes and full dimensions."""
        x = normalize(axis_x) * (size_x * 0.5)
        y = normalize(axis_y) * (size_y * 0.5)
        z = normalize(axis_z) * (size_z * 0.5)
        p000 = center - x - y - z
        p100 = center + x - y - z
        p110 = center + x + y - z
        p010 = center - x + y - z
        p001 = center - x - y + z
        p101 = center + x - y + z
        p111 = center + x + y + z
        p011 = center - x + y + z
        self.add_quad(p000, p010, p110, p100, color)
        self.add_quad(p001, p101, p111, p011, color)
        self.add_quad(p000, p100, p101, p001, color)
        self.add_quad(p010, p011, p111, p110, color)
        self.add_quad(p000, p001, p011, p010, color)
        self.add_quad(p100, p110, p111, p101, color)

    def add_octa_sphere(
        self,
        center: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
    ) -> None:
        x = np.array([radius, 0.0, 0.0])
        y = np.array([0.0, radius, 0.0])
        z = np.array([0.0, 0.0, radius])
        pts = [center + x, center - x, center + y, center - y, center + z, center - z]
        # Eight triangles of an octahedron; normals are flat for a deliberately mechanical node marker.
        faces = [
            (4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0),
            (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3),
        ]
        for a, b, c in faces:
            self.add_triangle(pts[a], pts[b], pts[c], color)

    def finish(self) -> MeshData:
        if not self.vertices:
            return MeshData(np.empty((0, 10), dtype=np.float32), np.empty((0,), dtype=np.uint32))
        return MeshData(
            np.asarray(self.vertices, dtype=np.float32),
            np.asarray(self.indices, dtype=np.uint32),
        )


class LineAccumulator:
    """Build GL_LINES data as position + RGBA per vertex."""

    def __init__(self) -> None:
        self.vertices: list[list[float]] = []

    def add(self, a: np.ndarray, b: np.ndarray, color: tuple[float, float, float, float]) -> None:
        self.vertices.append([float(a[0]), float(a[1]), float(a[2]), *map(float, color)])
        self.vertices.append([float(b[0]), float(b[1]), float(b[2]), *map(float, color)])

    def finish(self) -> LineData:
        if not self.vertices:
            return LineData(np.empty((0, 7), dtype=np.float32))
        return LineData(np.asarray(self.vertices, dtype=np.float32))


def _mesh_sector_local_points(model: DomePhysicalModel) -> list[tuple[float, float]]:
    """Return the exact rendered sector boundary after the configured axial rotation."""
    cfg = model.config
    r = cfg.trunk_diameter_in * 0.5
    half = math.radians((360.0 / cfg.radial_splits) * 0.5)
    local: list[tuple[float, float]] = [(0.0, 0.0)]
    for i in range(cfg.arc_segments + 1):
        angle = -half + (2.0 * half) * i / cfg.arc_segments
        local.append(
            rotate_sector_yz(
                r * math.sin(angle), r * math.cos(angle), cfg.wedge_orientation
            )
        )
    return local


def _intersect_member_boundary_with_butt_plane(
    member: MemberInfo,
    local: list[tuple[float, float]],
) -> list[np.ndarray]:
    """Intersect every longitudinal boundary generator with the member's actual butt plane."""
    origin = member.nominal_start + member.point_offset_in * member.inward
    denom = float(np.dot(member.tangent, member.butt_plane_normal))
    if abs(denom) <= 1e-10:
        raise ValueError(f"{member.member_id} butt plane is parallel to its axis")

    ring: list[np.ndarray] = []
    for y, z in local:
        line_point = origin + y * member.inward + z * member.face_normal
        t = float(np.dot(member.butt_plane_point - line_point, member.butt_plane_normal) / denom)
        ring.append(line_point + t * member.tangent)
    return ring


def add_raw_sector_member(
    acc: MeshAccumulator,
    model: DomePhysicalModel,
    member: MemberInfo,
    position_offset: np.ndarray | None = None,
) -> None:
    """Build a true raw-sector member with the CYCLIC PINWHEEL BUTT end geometry.

    This is intentionally NOT a conventional vertex-to-vertex prism. The receiving end is
    an oblique CLEAN VERTEX CUT on the adjacent mathematical edge plane, so the member cannot
    spike into another panel at a dome node. The opposite end is the cyclic butt cut lying
    on the next member's panel-interior radial face. The visible solid therefore carries both
    the pinwheel/chasing relationship and the corrected node-cleaning geometry.
    """
    local = _mesh_sector_local_points(model)
    offset = np.zeros(3, dtype=np.float64) if position_offset is None else np.asarray(position_offset, dtype=np.float64)

    # Receiving/through end: CLEAN VERTEX CUT. This ring is the intersection of
    # every longitudinal sector generator with the adjacent ideal-edge boundary plane.
    # It replaces the old perpendicular overhanging cap and keeps the complete member
    # inside its triangular panel footprint at a dome node.
    ring_receive = [p.copy() + offset for p in member.receiving_cut_points]

    # Terminating/butt end: each longitudinal generator is clipped against the actual
    # receiving neighbor's panel-interior side plane, producing the pinwheel butt surface.
    ring_butt = [p.copy() + offset for p in member.butt_contact_points]

    # Receiving end cap. The solid lies on the +receiving_plane_normal side, so the
    # outward-facing cap normal points in the opposite direction.
    receive_cap_normal = -normalize(member.receiving_plane_normal)
    for i in range(1, len(local) - 1):
        acc.add_triangle(
            ring_receive[0], ring_receive[i + 1], ring_receive[i],
            WEDGE_BACK_COLOR, receive_cap_normal,
        )

    # Butt cap lies on the receiving neighbor's side plane. Let geometry derive the visible
    # normal so winding remains robust even when the panel is transformed around the dome.
    for i in range(1, len(local) - 1):
        acc.add_triangle(ring_butt[0], ring_butt[i], ring_butt[i + 1], WEDGE_BACK_COLOR)

    # Side boundary 0 -> 1 is the seam-facing radial surface. The final boundary edge
    # returns from the panel-interior arc corner to the sector point.
    acc.add_quad(ring_receive[0], ring_butt[0], ring_butt[1], ring_receive[1], WEDGE_LEFT_COLOR)
    for i in range(1, len(local) - 1):
        acc.add_quad(
            ring_receive[i], ring_butt[i], ring_butt[i + 1], ring_receive[i + 1],
            WEDGE_BACK_COLOR,
        )
    acc.add_quad(ring_receive[-1], ring_butt[-1], ring_butt[0], ring_receive[0], WEDGE_RIGHT_COLOR)

    # Highlight the sharp sector tip/apex with a thin yellow spine so the current
    # wedge orientation is obvious from nearly any camera angle.
    tip_radius = max(0.06, model.config.trunk_diameter_in * 0.014)
    acc.add_cylinder(ring_receive[0], ring_butt[0], tip_radius, 10, WEDGE_TIP_COLOR)


def build_pinwheel_debug_lines(model: DomePhysicalModel) -> LineData:
    """Draw the physical chasing/pinwheel logic independently of the ideal geodesic mesh.

    Orange lines are the physical sector-point axes from the through extension to the butt
    cut. Green polygons are end-to-side contact outlines. Magenta crosses are the mathematical
    geodesic vertices, deliberately shown separately from physical wood endpoints.
    """
    lines = LineAccumulator()
    member_map = model.member_by_id

    for member in model.members:
        face_offset = model.topology.faces[member.face_index].normal * model.config.panel_explode_in
        nominal_origin = member.nominal_start + member.point_offset_in * member.inward + face_offset
        receive_axis = nominal_origin + member.receiving_axis_parameter_in * member.tangent
        butt_axis = nominal_origin + member.butt_axis_parameter_in * member.tangent
        lines.add(receive_axis, butt_axis, PINWHEEL_AXIS_COLOR)

        # Red outline = the requested clean geodesic-vertex cut. This is the actual
        # receiving-end polygon after clipping to the triangular face envelope.
        rpts = member.receiving_cut_points + face_offset
        if len(rpts) >= 2:
            for i in range(len(rpts)):
                lines.add(rpts[i], rpts[(i + 1) % len(rpts)], VERTEX_CUT_COLOR)

    for joint in model.joints:
        face_offset = model.topology.faces[joint.face_index].normal * model.config.panel_explode_in
        pts = joint.contact_points + face_offset
        if len(pts) >= 2:
            for i in range(len(pts)):
                lines.add(pts[i], pts[(i + 1) % len(pts)], PINWHEEL_CONTACT_COLOR)

        # Cross centered on the VIRTUAL vertex. It should not generally coincide with both
        # wood endpoints; that visual separation is the point of this debug layer.
        receiver = member_map[joint.receiving_member_id]
        scale = max(0.65, model.config.trunk_diameter_in * 0.10)
        v = joint.virtual_vertex + face_offset
        lines.add(v - receiver.inward * scale, v + receiver.inward * scale, VIRTUAL_VERTEX_COLOR)
        lines.add(v - receiver.face_normal * scale, v + receiver.face_normal * scale, VIRTUAL_VERTEX_COLOR)

    return lines.finish()

def add_rigid_spacer(acc: MeshAccumulator, seam: SeamInfo) -> None:
    """Full-contact triangular spline generated from the actual untouched radial faces."""
    acc.add_triangular_prism(
        seam.apex_start,
        seam.point_a_start,
        seam.point_b_start,
        seam.apex_end,
        seam.point_a_end,
        seam.point_b_end,
        SPACER_COLOR,
    )


def hose_centerline(seam: SeamInfo, requested_radius: float) -> tuple[np.ndarray, np.ndarray, float, bool]:
    """Return tangent hose centerline, actual radius, and whether the requested hose had to be clamped."""
    max_r = seam.hose_max_radius_in
    radius = min(requested_radius, max_r * 0.98)
    clamped = requested_radius > radius + 1e-9

    base_mid_start = (seam.point_a_start + seam.point_b_start) * 0.5
    base_mid_end = (seam.point_a_end + seam.point_b_end) * 0.5
    inward_dir_start = normalize(base_mid_start - seam.apex_start)
    inward_dir_end = normalize(base_mid_end - seam.apex_end)

    gap_half = math.radians(seam.raw_gap_angle_deg * 0.5)
    distance = radius / math.sin(gap_half)
    center_start = seam.apex_start + inward_dir_start * distance
    center_end = seam.apex_end + inward_dir_end * distance
    return center_start, center_end, radius, clamped


def _panel_flat_frame(model: DomePhysicalModel, panel_index: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return anchor and orthonormal X/Y/Z axes for flattening one panel exterior-up."""
    face = model.topology.faces[panel_index % len(model.topology.faces)]
    verts = model.topology.vertices[list(face.vertices)]
    anchor = verts[0]
    x_axis = normalize(verts[1] - verts[0])
    z_axis = face.normal
    y_axis = normalize(np.cross(z_axis, x_axis))
    if float(np.dot(verts[2] - anchor, y_axis)) < 0.0:
        y_axis = -y_axis
        x_axis = -x_axis
    return anchor, x_axis, y_axis, z_axis


def _flat_point(p: np.ndarray, anchor: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    d = p - anchor
    return np.array([float(np.dot(d, x)), float(np.dot(d, y)), float(np.dot(d, z))], dtype=np.float64)


def _flat_vector(v: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    return np.array([float(np.dot(v, x)), float(np.dot(v, y)), float(np.dot(v, z))], dtype=np.float64)


def _shift_mesh(mesh: MeshData, shift: np.ndarray) -> MeshData:
    if len(mesh.vertices) == 0:
        return mesh
    out = mesh.vertices.copy()
    out[:, 0:3] += shift.astype(np.float32)
    return MeshData(out, mesh.indices.copy())


def _flatten_mesh(mesh: MeshData, anchor: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray, shift: np.ndarray) -> MeshData:
    """Rigidly rotate an existing panel mesh into an exterior-up fabrication-jig plane."""
    if len(mesh.vertices) == 0:
        return mesh
    out = mesh.vertices.copy()
    positions = mesh.vertices[:, 0:3].astype(np.float64)
    normals = mesh.vertices[:, 3:6].astype(np.float64)
    for i, p in enumerate(positions):
        out[i, 0:3] = _flat_point(p, anchor, x, y, z) + shift
    for i, n in enumerate(normals):
        out[i, 3:6] = normalize(_flat_vector(n, x, y, z))
    return MeshData(out.astype(np.float32), mesh.indices.copy())


def fabrication_jig_world_shift(model: DomePhysicalModel, panel_index: int) -> np.ndarray:
    """Place the flat jig beyond the +X side of the dome while keeping it on the ground."""
    face = model.topology.faces[panel_index % len(model.topology.faces)]
    anchor, x, y, z = _panel_flat_frame(model, panel_index)
    verts = [_flat_point(model.topology.vertices[i], anchor, x, y, z) for i in face.vertices]
    min_x = min(float(p[0]) for p in verts)
    min_y = min(float(p[1]) for p in verts)
    max_y = max(float(p[1]) for p in verts)
    clearance = model.config.jig_world_clearance_in
    target_min_x = model.topology.sphere_radius_in + clearance
    target_center_y = 0.0
    return np.array([
        target_min_x - min_x,
        target_center_y - (min_y + max_y) * 0.5,
        model.config.jig_base_thickness_in,
    ], dtype=np.float64)


def build_fabrication_jig(model: DomePhysicalModel, panel_index: int) -> dict[str, MeshData | LineData]:
    """Build an exact flat assembly/cutting jig for one solved physical triangle.

    The selected dome orientation is preserved when the panel is flattened. Because the
    sector may point dome-in, dome-out, panel-in, or panel-out, the jig automatically lifts
    the solved wood enough that its lowest cross-section point clears the base. The fixture
    contains member-axis locator rails, RED clean-vertex cut guides, and GREEN cyclic
    butt-cut guides generated from the same cut geometry as the dome.
    """
    panel_index %= len(model.topology.faces)
    face = model.topology.faces[panel_index]
    members = sorted(
        [m for m in model.members if m.face_index == panel_index],
        key=lambda m: m.local_edge_index,
    )
    member_map = {m.member_id: m for m in members}
    anchor, fx, fy, fz = _panel_flat_frame(model, panel_index)
    shift = fabrication_jig_world_shift(model, panel_index)

    # Preserve the chosen cross-section rotation but lift the panel so no part of a
    # dome-out/sideways sector falls through the jig base. The point axis therefore need
    # not be the lowest feature in all four orientations.
    profile_min_z = min(z for _, z in _mesh_sector_local_points(model))
    wood_lift = max(0.0, -profile_min_z)
    wood_shift = shift + np.array([0.0, 0.0, wood_lift], dtype=np.float64)

    # Copy the exact solved wood for the selected panel into the flat jig.
    temp_wood = MeshAccumulator()
    for member in members:
        add_raw_sector_member(temp_wood, model, member)
    jig_wood = _flatten_mesh(temp_wood.finish(), anchor, fx, fy, fz, wood_shift)

    fixture = MeshAccumulator()
    lines = LineAccumulator()
    verts_local = [_flat_point(model.topology.vertices[i], anchor, fx, fy, fz) for i in face.vertices]
    min_x = min(float(p[0]) for p in verts_local)
    max_x = max(float(p[0]) for p in verts_local)
    min_y = min(float(p[1]) for p in verts_local)
    max_y = max(float(p[1]) for p in verts_local)
    margin = model.config.jig_base_margin_in
    base_t = model.config.jig_base_thickness_in
    base_center_local = np.array([
        (min_x + max_x) * 0.5,
        (min_y + max_y) * 0.5,
        -base_t * 0.5,
    ]) + shift
    fixture.add_box(
        base_center_local,
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        (max_x - min_x) + 2.0 * margin,
        (max_y - min_y) + 2.0 * margin,
        base_t,
        JIG_BASE_COLOR,
    )

    # Ideal mathematical triangle on the jig surface.
    for i in range(3):
        a = verts_local[i] + shift + np.array([0.0, 0.0, 0.04])
        b = verts_local[(i + 1) % 3] + shift + np.array([0.0, 0.0, 0.04])
        lines.add(a, b, JIG_IDEAL_COLOR)

    # Low locator rails sit just to the SEAM side of each sector-point axis. The point
    # axis itself is the exact repeatable placement reference; unlike the curved bark side,
    # it does not depend on bark irregularity.
    for member in members:
        origin = member.nominal_start + member.point_offset_in * member.inward
        receive_axis = origin + member.receiving_axis_parameter_in * member.tangent
        butt_axis = origin + member.butt_axis_parameter_in * member.tangent
        a = _flat_point(receive_axis, anchor, fx, fy, fz) + wood_shift
        b = _flat_point(butt_axis, anchor, fx, fy, fz) + wood_shift
        tangent_local = normalize(b - a)
        inward_local = normalize(_flat_vector(member.inward, fx, fy, fz))
        inward_local[2] = 0.0
        inward_local = normalize(inward_local)
        rail_width = model.config.jig_rail_width_in
        rail_height = model.config.jig_rail_height_in
        rail_center = (a + b) * 0.5 - inward_local * (rail_width * 0.5 + 0.10)
        rail_center[2] = wood_shift[2] + rail_height * 0.5
        fixture.add_box(
            rail_center,
            tangent_local,
            inward_local,
            np.array([0.0, 0.0, 1.0]),
            float(np.linalg.norm(b - a)) + 2.0,
            rail_width,
            rail_height,
            JIG_RAIL_COLOR,
        )

        # Red receiving-end guide = exact clean triangle-envelope cut plane.
        cut_center_world = np.mean(member.receiving_cut_points, axis=0)
        cut_center = _flat_point(cut_center_world, anchor, fx, fy, fz) + wood_shift
        cut_normal = normalize(_flat_vector(member.receiving_plane_normal, fx, fy, fz))
        cut_normal[2] = 0.0
        cut_normal = normalize(cut_normal)
        cut_tangent = normalize(np.cross(np.array([0.0, 0.0, 1.0]), cut_normal))
        guide_h = model.config.jig_cut_guide_height_in
        cut_center[2] = wood_shift[2] + guide_h * 0.5
        fixture.add_box(
            cut_center,
            cut_tangent,
            cut_normal,
            np.array([0.0, 0.0, 1.0]),
            model.config.trunk_diameter_in + 5.0,
            model.config.jig_cut_guide_thickness_in,
            guide_h,
            JIG_GUIDE_VERTEX_COLOR,
        )

        rpts = [_flat_point(p, anchor, fx, fy, fz) + wood_shift for p in member.receiving_cut_points]
        for j in range(len(rpts)):
            lines.add(rpts[j], rpts[(j + 1) % len(rpts)], VERTEX_CUT_COLOR)

        # Green butt-cut guide = the actual receiving neighbor's PANEL_INTERIOR_FACE.
        butt_center_world = np.mean(member.butt_contact_points, axis=0)
        butt_center = _flat_point(butt_center_world, anchor, fx, fy, fz) + wood_shift
        butt_normal = normalize(_flat_vector(member.butt_plane_normal, fx, fy, fz))
        receiver = member_map[member.butt_into_member_id]
        plane_axis_u = normalize(_flat_vector(receiver.tangent, fx, fy, fz))
        plane_axis_v = normalize(np.cross(butt_normal, plane_axis_u))
        fixture.add_box(
            butt_center,
            plane_axis_u,
            butt_normal,
            plane_axis_v,
            model.config.trunk_diameter_in + 4.0,
            model.config.jig_cut_guide_thickness_in,
            model.config.trunk_diameter_in + 4.0,
            JIG_GUIDE_BUTT_COLOR,
        )

        bpts = [_flat_point(p, anchor, fx, fy, fz) + wood_shift for p in member.butt_contact_points]
        for j in range(len(bpts)):
            lines.add(bpts[j], bpts[(j + 1) % len(bpts)], PINWHEEL_CONTACT_COLOR)

    return {
        "jig_wood": jig_wood,
        "jig_fixture": fixture.finish(),
        "jig_lines": lines.finish(),
    }


def build_world_meshes(model: DomePhysicalModel) -> dict[str, MeshData | LineData]:
    """Generate render batches for the complete world."""
    wood = MeshAccumulator()
    rigid = MeshAccumulator()
    hose = MeshAccumulator()
    nodes = MeshAccumulator()
    skins = MeshAccumulator()
    ideal = LineAccumulator()
    ground = LineAccumulator()
    joint_debug = build_pinwheel_debug_lines(model)

    for member in model.members:
        panel_offset = model.topology.faces[member.face_index].normal * model.config.panel_explode_in
        add_raw_sector_member(wood, model, member, panel_offset)

    requested_hose_radius = model.config.hose_outer_diameter_in * 0.5
    for seam in model.seams:
        add_rigid_spacer(rigid, seam)
        hs, he, hr, _ = hose_centerline(seam, requested_hose_radius)
        hose.add_cylinder(hs, he, hr, model.config.hose_segments, HOSE_COLOR)

    # Node markers identify the 26 places where longitudinal seam logic must terminate into a node system.
    for v in model.topology.vertices:
        nodes.add_octa_sphere(v, model.config.node_radius_in, NODE_COLOR)

    # Optional panel skins are deliberately slightly outside the wood's nominal face plane.
    if model.config.skin_enabled:
        for face in model.topology.faces:
            tri = (
                model.topology.vertices[list(face.vertices)]
                + face.normal * (model.config.skin_offset_in + model.config.panel_explode_in)
            )
            skins.add_triangle(tri[0], tri[1], tri[2], SKIN_COLOR, face.normal)

    for edge in model.topology.edges.values():
        a = model.topology.vertices[edge.key[0]]
        b = model.topology.vertices[edge.key[1]]
        if edge.is_base:
            color = BASE_COLOR
        else:
            color = IDEAL_A_COLOR if edge.edge_type == "A" else IDEAL_B_COLOR
        ideal.add(a, b, color)

    # Ground grid, in inches. Major lines every 24 inches across a region larger than the dome.
    extent = model.topology.sphere_radius_in * 1.45
    spacing = 24.0
    count = int(math.ceil(extent / spacing))
    z = -0.10
    for i in range(-count, count + 1):
        x = i * spacing
        ground.add(np.array([x, -extent, z]), np.array([x, extent, z]), GROUND_COLOR)
        y = i * spacing
        ground.add(np.array([-extent, y, z]), np.array([extent, y, z]), GROUND_COLOR)

    return {
        "wood": wood.finish(),
        "rigid": rigid.finish(),
        "hose": hose.finish(),
        "nodes": nodes.finish(),
        "skins": skins.finish(),
        "ideal": ideal.finish(),
        "ground": ground.finish(),
        "joint_debug": joint_debug,
    }



def build_single_panel_mesh(model: DomePhysicalModel, panel_index: int) -> MeshData:
    """Render exactly one complete physical triangle for orientation analysis.

    The triangle retains its solved cyclic cuts and current four-state wedge rotation.
    It also receives the same analysis-only face-normal explosion offset as the full dome.
    """
    panel_index %= len(model.topology.faces)
    acc = MeshAccumulator()
    face = model.topology.faces[panel_index]
    panel_offset = face.normal * model.config.panel_explode_in
    for member in model.members:
        if member.face_index == panel_index:
            add_raw_sector_member(acc, model, member, panel_offset)
    return acc.finish()

def build_selected_seam_lines(model: DomePhysicalModel, seam_index: int) -> LineData:
    seam = model.seams[seam_index % len(model.seams)]
    lines = LineAccumulator()

    # Longitudinal boundaries of the exact spacer/contact geometry.
    lines.add(seam.apex_start, seam.apex_end, SELECT_COLOR)
    lines.add(seam.point_a_start, seam.point_a_end, SELECT_COLOR)
    lines.add(seam.point_b_start, seam.point_b_end, SELECT_COLOR)
    lines.add(seam.apex_start, seam.point_a_start, SELECT_COLOR)
    lines.add(seam.apex_start, seam.point_b_start, SELECT_COLOR)
    lines.add(seam.point_a_start, seam.point_b_start, SELECT_COLOR)
    lines.add(seam.apex_end, seam.point_a_end, SELECT_COLOR)
    lines.add(seam.apex_end, seam.point_b_end, SELECT_COLOR)
    lines.add(seam.point_a_end, seam.point_b_end, SELECT_COLOR)

    # Face-normal vectors at seam midpoint make the fold direction visually obvious.
    mid = (seam.start + seam.end) * 0.5
    scale = 18.0
    lines.add(mid, mid + seam.normal_a * scale, (1.0, 0.3, 0.3, 1.0))
    lines.add(mid, mid + seam.normal_b * scale, (0.3, 0.8, 1.0, 1.0))
    return lines.finish()


def export_mesh_obj(mesh: MeshData, path: str | Path, object_name: str) -> None:
    """Export one generated triangle batch as a simple OBJ file."""
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"o {object_name}\n")
        for row in mesh.vertices:
            f.write(f"v {row[0]:.8f} {row[1]:.8f} {row[2]:.8f}\n")
        for row in mesh.vertices:
            f.write(f"vn {row[3]:.8f} {row[4]:.8f} {row[5]:.8f}\n")
        for i in range(0, len(mesh.indices), 3):
            a, b, c = [int(x) + 1 for x in mesh.indices[i:i + 3]]
            f.write(f"f {a}//{a} {b}//{b} {c}//{c}\n")

# ============================================================================
# FLATTENED SOURCE: camera.py
# ============================================================================
class FirstPersonCamera:
    """Mouse-look FPS camera with optional fly, zoom-pan, and inverted horizontal look."""

    def __init__(self, config: DomeConfig, sphere_radius: float) -> None:
        self.config = config
        self.position = np.array([0.0, -sphere_radius * 1.30, config.camera_height_in], dtype=np.float64)
        self.yaw_deg = 90.0
        self.pitch_deg = -3.0
        self.fly_mode = False
        self.walk_height = config.camera_height_in

    @property
    def forward(self) -> np.ndarray:
        yaw = math.radians(self.yaw_deg)
        pitch = math.radians(self.pitch_deg)
        return normalize(
            np.array(
                [
                    math.cos(pitch) * math.cos(yaw),
                    math.cos(pitch) * math.sin(yaw),
                    math.sin(pitch),
                ],
                dtype=np.float64,
            )
        )

    @property
    def horizontal_forward(self) -> np.ndarray:
        f = self.forward.copy()
        f[2] = 0.0
        if np.linalg.norm(f) <= 1e-10:
            return np.array([0.0, 1.0, 0.0], dtype=np.float64)
        return normalize(f)

    @property
    def right(self) -> np.ndarray:
        return normalize(np.cross(self.horizontal_forward, np.array([0.0, 0.0, 1.0], dtype=np.float64)))

    @property
    def screen_up(self) -> np.ndarray:
        up = np.cross(self.right, self.forward)
        if np.linalg.norm(up) <= 1e-10:
            return np.array([0.0, 0.0, 1.0], dtype=np.float64)
        return normalize(up)

    def mouse_look(self, dx: float, dy: float) -> None:
        sensitivity = self.config.mouse_sensitivity_deg_px
        # Horizontal mouse look intentionally inverted to match the requested feel.
        self.yaw_deg -= dx * sensitivity
        self.pitch_deg -= dy * sensitivity
        self.pitch_deg = max(-89.0, min(89.0, self.pitch_deg))

    def move(self, forward_axis: float, right_axis: float, vertical_axis: float, dt: float, sprint: bool) -> None:
        speed = self.config.walk_speed_in_s * (self.config.sprint_multiplier if sprint else 1.0)
        if self.fly_mode:
            direction = self.forward * forward_axis + self.right * right_axis + np.array([0.0, 0.0, vertical_axis])
        else:
            direction = self.horizontal_forward * forward_axis + self.right * right_axis

        if np.linalg.norm(direction) > 1e-10:
            direction = normalize(direction)
            self.position += direction * speed * dt

        if not self.fly_mode:
            self.position[2] = self.walk_height

    def pan(self, right_axis: float, up_axis: float, dt: float, sprint: bool) -> None:
        """Screen-plane panning used only when fully zoomed in for close inspection."""
        speed = (self.config.walk_speed_in_s * 0.60) * (self.config.sprint_multiplier if sprint else 1.0)
        direction = self.right * right_axis + self.screen_up * up_axis
        if np.linalg.norm(direction) > 1e-10:
            direction = normalize(direction)
            self.position += direction * speed * dt

    def view_matrix(self) -> np.ndarray:
        return look_at_matrix(
            self.position,
            self.position + self.forward,
            np.array([0.0, 0.0, 1.0], dtype=np.float64),
        )

# ============================================================================
# FLATTENED SOURCE: hud.py
# ============================================================================
@dataclass(frozen=True)
class HudTheme:
    """Visual parameters for the in-world keyboard legend."""

    margin_px: int = 10
    padding_px: int = 8
    column_gap_px: int = 16
    row_gap_px: int = 2
    section_gap_px: int = 5
    font_size_px: int = 13
    title_size_px: int = 14
    text_alpha: int = 210
    muted_alpha: int = 162
    panel_alpha: int = 96
    border_alpha: int = 92


class ControlsHud:
    """Builds a compact transparent Pygame surface used as a ModernGL HUD texture."""

    def __init__(self, theme: HudTheme | None = None) -> None:
        self.theme = theme or HudTheme()
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", self.theme.font_size_px)
        self.title_font = pygame.font.SysFont("consolas", self.theme.title_size_px, bold=True)

    @staticmethod
    def _text(font: pygame.font.Font, value: str, alpha: int) -> pygame.Surface:
        surface = font.render(value, True, (238, 244, 250))
        surface.set_alpha(alpha)
        return surface

    def build(
        self,
        *,
        walk_mode: str,
        spacer_mode: str,
        mouse_captured: bool,
        pinwheel_handedness: str,
        wedge_orientation: str,
        jig_visible: bool,
        jig_panel: int,
        jig_face_type: str,
        vertex_trim_mode: str,
        panel_explode_in: float,
        solo_panel: bool,
        seam_open_a_in: float,
        seam_open_b_in: float,
        zoom_steps: int,
        zoom_max_steps: int,
        pan_mode: bool,
    ) -> pygame.Surface:
        movement = [
            ("Mouse", "look  (L/R inverted)"),
            ("Wheel", "zoom at center X"),
            ("Arrows/WASD", "move / strafe"),
            ("Arrows @ max zoom", "pan mode"),
            ("Shift", "sprint"),
            ("PgUp/PgDn", "vertical (fly)"),
            ("F", "walk / fly"),
            ("Tab", "capture mouse"),
            ("Esc", "release / exit"),
        ]
        world = [
            ("H", "rigid / hose / none"),
            ("U", "cycle wedge orientation"),
            ("Shift+U", "wedge orientation back"),
            ("Z / X", "panel explode - / +"),
            ("C", "collapse panels"),
            ("Q", "solo selected triangle"),
            ("[ / ]", "select seam"),
            ("J", "joint + cut debug"),
            ("I", "ideal geometry"),
            ("N", "node markers"),
            ("G", "ground grid"),
            ("P", "panel skins"),
            ("V / O", "wood / spacers"),
        ]
        fabrication = [
            ("T", "show / hide exact jig"),
            ("Y", "next jig panel"),
            ("Shift+Y", "previous jig panel"),
            (", / .", "trunk diameter"),
            ("- / =", "nominal A length"),
            ("R", "reset camera"),
            ("B", "export BOM"),
            ("E", "export all + jig package"),
            ("F12", "screenshot"),
            ("F1", "console help"),
            ("F2", "hide this legend"),
        ]

        orientation_labels = {
            "point_dome_in": "DOME-IN",
            "point_panel_in": "PANEL-IN",
            "point_dome_out": "DOME-OUT",
            "point_panel_out": "PANEL-OUT",
        }
        wedge_label = orientation_labels.get(wedge_orientation, wedge_orientation.upper())
        channel_labels = {
            "point_dome_in": "CH IN",
            "point_dome_out": "CH OUT",
            "point_panel_in": "CH SIDE",
            "point_panel_out": "CH SIDE",
        }
        channel_label = channel_labels.get(wedge_orientation, "CH ?")

        status_lines = [
            "   |   ".join(
                [
                    f"{walk_mode.upper()}",
                    f"{spacer_mode.upper()}",
                    f"MOUSE {'ON' if mouse_captured else 'FREE'}",
                    f"PIN {'CW' if pinwheel_handedness == 'clockwise' else 'CCW'}",
                    f"WEDGE {wedge_label}",
                    channel_label,
                ]
            ),
            "   |   ".join(
                [
                    f"EXP {panel_explode_in:.0f}in",
                    f"SEAM A {seam_open_a_in:.1f}",
                    f"B {seam_open_b_in:.1f}",
                    f"SOLO {'P%03d' % (jig_panel + 1) if solo_panel else 'OFF'}",
                    f"JIG {'ON' if jig_visible else 'OFF'} {jig_face_type}",
                    f"ZOOM {zoom_steps}/{zoom_max_steps}{' PAN' if pan_mode else ''}",
                ]
            ),
        ]
        if vertex_trim_mode:
            status_lines.append("VERTEX CUT TRIANGLE-ENVELOPE")

        columns = [
            ("MOVE", movement),
            ("WORLD", world),
            ("FILE", fabrication),
        ]

        column_widths: list[int] = []
        row_height = self.font.get_linesize() + self.theme.row_gap_px
        for heading, rows in columns:
            heading_width = self.title_font.size(heading)[0]
            key_width = max(self.font.size(key)[0] for key, _ in rows)
            action_width = max(self.font.size(action)[0] for _, action in rows)
            column_widths.append(max(heading_width, key_width + 10 + action_width))

        status_width = max(self.font.size(line)[0] for line in status_lines)
        columns_width = sum(column_widths) + self.theme.column_gap_px * (len(columns) - 1)
        content_width = max(columns_width, status_width)

        max_rows = max(len(rows) for _, rows in columns)
        status_height = len(status_lines) * row_height + self.theme.section_gap_px
        columns_height = self.title_font.get_linesize() + self.theme.section_gap_px + max_rows * row_height
        content_height = status_height + columns_height

        width = content_width + self.theme.padding_px * 2
        height = content_height + self.theme.padding_px * 2
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.rect(surface, (8, 12, 18, self.theme.panel_alpha), surface.get_rect(), border_radius=7)
        pygame.draw.rect(surface, (220, 232, 242, self.theme.border_alpha), surface.get_rect(), width=1, border_radius=7)

        x0 = self.theme.padding_px
        y = self.theme.padding_px
        for line in status_lines:
            surface.blit(self._text(self.font, line, self.theme.muted_alpha), (x0, y))
            y += row_height
        y += self.theme.section_gap_px

        x = x0
        for (heading, rows), col_width in zip(columns, column_widths):
            surface.blit(self._text(self.title_font, heading, self.theme.text_alpha), (x, y))
            row_y = y + self.title_font.get_linesize() + self.theme.section_gap_px
            key_width = max(self.font.size(key)[0] for key, _ in rows)
            for key, action in rows:
                surface.blit(self._text(self.font, key, self.theme.text_alpha), (x, row_y))
                surface.blit(self._text(self.font, action, self.theme.muted_alpha), (x + key_width + 10, row_y))
                row_y += row_height
            x += col_width + self.theme.column_gap_px

        return surface


class SeamMinimapHud:
    """Builds a minimal bottom-right schematic showing seam/wedge orientation."""

    def __init__(self, theme: HudTheme | None = None) -> None:
        self.theme = theme or HudTheme()

    @staticmethod
    def _rotate(points: list[tuple[float, float]], quarter_turns: int) -> list[tuple[float, float]]:
        result = points
        q = quarter_turns % 4
        for _ in range(q):
            result = [(y, -x) for (x, y) in result]
        return result

    @staticmethod
    def _transform(points: list[tuple[float, float]], scale: float, cx: float, cy: float) -> list[tuple[int, int]]:
        return [(int(round(cx + x * scale)), int(round(cy + y * scale))) for x, y in points]

    def _draw_single_diagram(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        orientation: str,
        active: bool,
    ) -> None:
        # canonical wedge in cross-section coordinates:
        # point_dome_in means tip down toward dome interior, bark up toward dome exterior.
        tip = (0.0, 1.0)
        left_outer = (-0.78, -0.85)
        right_outer = (0.78, -0.85)
        arc_top = [(x, -0.95 + 0.18 * (x * x)) for x in (-0.62, -0.30, 0.0, 0.30, 0.62)]
        base_tip = [tip] + arc_top + [tip]
        left_face = [tip, left_outer, arc_top[0], tip]
        right_face = [tip, right_outer, arc_top[-1], tip]
        bark_face = [left_outer] + arc_top + [right_outer]

        rotation = {
            "point_dome_in": 0,
            "point_panel_in": 1,
            "point_dome_out": 2,
            "point_panel_out": 3,
        }.get(orientation, 0)

        pad = 8
        inner = rect.inflate(-pad * 2, -pad * 2)
        bg = (8, 12, 18, 120 if active else 78)
        border = (240, 244, 248, 190) if active else (170, 178, 190, 115)
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2 if active else 1, border_radius=8)

        cx_left = inner.left + inner.width * 0.31
        cx_right = inner.left + inner.width * 0.69
        cy = inner.centery
        scale = min(inner.width * 0.14, inner.height * 0.18)

        # seam gap and panel guide lines
        seam_x = inner.centerx
        pygame.draw.line(surface, (155, 165, 180, 90), (seam_x, inner.top + 4), (seam_x, inner.bottom - 4), 1)
        # tiny panel-outline cue
        tri_left = [(inner.left + 10, inner.bottom - 12), (inner.centerx - 10, inner.centery - 10), (inner.left + 10, inner.top + 12)]
        tri_right = [(inner.right - 10, inner.bottom - 12), (inner.centerx + 10, inner.centery - 10), (inner.right - 10, inner.top + 12)]
        pygame.draw.lines(surface, (90, 125, 170, 85), False, tri_left, 1)
        pygame.draw.lines(surface, (90, 125, 170, 85), False, tri_right, 1)

        for mirror, cx in ((1.0, cx_left), (-1.0, cx_right)):
            lf = [(mirror * x, y) for x, y in left_face]
            rf = [(mirror * x, y) for x, y in right_face]
            bf = [(mirror * x, y) for x, y in bark_face]
            bt = [(mirror * x, y) for x, y in base_tip]
            lf = self._rotate(lf, rotation)
            rf = self._rotate(rf, rotation)
            bf = self._rotate(bf, rotation)
            bt = self._rotate(bt, rotation)

            pygame.draw.polygon(surface, (153, 97, 46, 225), self._transform(bt, scale, cx, cy))
            pygame.draw.polygon(surface, (214, 40, 32, 235), self._transform(lf, scale, cx, cy))
            pygame.draw.polygon(surface, (42, 194, 58, 235), self._transform(rf, scale, cx, cy))
            pygame.draw.lines(surface, (250, 248, 130, 245), False, self._transform([tip, (0.0, -0.84)], scale, cx, cy), 3)
            pygame.draw.lines(surface, (252, 252, 252, 200), False, self._transform(bt, scale, cx, cy), 1)

    def build(self, *, wedge_orientation: str) -> pygame.Surface:
        width, height = 380, 210
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (8, 12, 18, 72), surface.get_rect(), border_radius=10)
        pygame.draw.rect(surface, (220, 232, 242, 72), surface.get_rect(), width=1, border_radius=10)

        cells = [
            pygame.Rect(10, 10, 175, 92),
            pygame.Rect(195, 10, 175, 92),
            pygame.Rect(10, 108, 175, 92),
            pygame.Rect(195, 108, 175, 92),
        ]
        order = ["point_dome_in", "point_panel_in", "point_dome_out", "point_panel_out"]
        for rect, orientation in zip(cells, order):
            self._draw_single_diagram(surface, rect, orientation, orientation == wedge_orientation)
        return surface


class CrosshairHud:
    """Tiny center-screen X used as the zoom reference."""

    def build(self) -> pygame.Surface:
        size = 24
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        col = (240, 244, 250, 205)
        shadow = (10, 14, 18, 165)
        pygame.draw.line(surface, shadow, (cx - 5, cx - 5), (cx + 5, cx + 5), 3)
        pygame.draw.line(surface, shadow, (cx - 5, cx + 5), (cx + 5, cx - 5), 3)
        pygame.draw.line(surface, col, (cx - 4, cx - 4), (cx + 4, cx + 4), 1)
        pygame.draw.line(surface, col, (cx - 4, cx + 4), (cx + 4, cx - 4), 1)
        return surface

# ============================================================================
# FLATTENED SOURCE: renderer.py
# ============================================================================
MESH_VERTEX_SHADER = r"""
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;

uniform mat4 u_view_projection;

out vec3 v_normal;
out vec4 v_color;

void main() {
    gl_Position = u_view_projection * vec4(in_position, 1.0);
    v_normal = in_normal;
    v_color = in_color;
}
"""

MESH_FRAGMENT_SHADER = r"""
#version 330
in vec3 v_normal;
in vec4 v_color;

uniform vec3 u_light_dir;

out vec4 fragColor;

void main() {
    vec3 n = normalize(v_normal);
    float diffuse = max(dot(n, normalize(-u_light_dir)), 0.0);
    float light = 0.30 + 0.70 * diffuse;
    fragColor = vec4(v_color.rgb * light, v_color.a);
}
"""

LINE_VERTEX_SHADER = r"""
#version 330
in vec3 in_position;
in vec4 in_color;

uniform mat4 u_view_projection;
out vec4 v_color;

void main() {
    gl_Position = u_view_projection * vec4(in_position, 1.0);
    v_color = in_color;
}
"""

LINE_FRAGMENT_SHADER = r"""
#version 330
in vec4 v_color;
out vec4 fragColor;

void main() {
    fragColor = v_color;
}
"""


OVERLAY_VERTEX_SHADER = r"""
#version 330
in vec2 in_corner;

uniform vec2 u_screen_size;
uniform vec2 u_position_px;
uniform vec2 u_size_px;

out vec2 v_uv;

void main() {
    vec2 pixel = u_position_px + in_corner * u_size_px;
    vec2 ndc = vec2(
        (pixel.x / u_screen_size.x) * 2.0 - 1.0,
        1.0 - (pixel.y / u_screen_size.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    // Pygame's uploaded bytes are vertically flipped, so screen-top maps to texture v=1.
    v_uv = vec2(in_corner.x, 1.0 - in_corner.y);
}
"""

OVERLAY_FRAGMENT_SHADER = r"""
#version 330
uniform sampler2D u_texture;
in vec2 v_uv;
out vec4 fragColor;

void main() {
    fragColor = texture(u_texture, v_uv);
}
"""


@dataclass
class GPUMesh:
    vbo: moderngl.Buffer
    ibo: moderngl.Buffer
    vao: moderngl.VertexArray
    count: int

    def release(self) -> None:
        self.vao.release()
        self.ibo.release()
        self.vbo.release()


@dataclass
class GPULines:
    vbo: moderngl.Buffer
    vao: moderngl.VertexArray
    count: int

    def release(self) -> None:
        self.vao.release()
        self.vbo.release()


@dataclass
class GPUOverlay:
    texture: moderngl.Texture
    width: int
    height: int

    def release(self) -> None:
        self.texture.release()


class Renderer:
    def __init__(self, ctx: moderngl.Context) -> None:
        self.ctx = ctx
        self.mesh_program = ctx.program(vertex_shader=MESH_VERTEX_SHADER, fragment_shader=MESH_FRAGMENT_SHADER)
        self.line_program = ctx.program(vertex_shader=LINE_VERTEX_SHADER, fragment_shader=LINE_FRAGMENT_SHADER)
        self.overlay_program = ctx.program(vertex_shader=OVERLAY_VERTEX_SHADER, fragment_shader=OVERLAY_FRAGMENT_SHADER)
        self.meshes: dict[str, GPUMesh] = {}
        self.lines: dict[str, GPULines] = {}
        self.overlays: dict[str, GPUOverlay] = {}

        # Four corners for a screen-space triangle strip: TL, TR, BL, BR.
        corners = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype="f4")
        self.overlay_vbo = self.ctx.buffer(corners.tobytes())
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program,
            [(self.overlay_vbo, "2f", "in_corner")],
        )

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

    def clear_batches(self) -> None:
        for mesh in self.meshes.values():
            mesh.release()
        for line in self.lines.values():
            line.release()
        self.meshes.clear()
        self.lines.clear()

    def upload_mesh(self, name: str, data: MeshData) -> None:
        if name in self.meshes:
            self.meshes.pop(name).release()
        if len(data.vertices) == 0 or len(data.indices) == 0:
            return
        vbo = self.ctx.buffer(data.vertices.astype("f4").tobytes())
        ibo = self.ctx.buffer(data.indices.astype("u4").tobytes())
        vao = self.ctx.vertex_array(
            self.mesh_program,
            [(vbo, "3f 3f 4f", "in_position", "in_normal", "in_color")],
            index_buffer=ibo,
            index_element_size=4,
        )
        self.meshes[name] = GPUMesh(vbo, ibo, vao, len(data.indices))

    def upload_lines(self, name: str, data: LineData) -> None:
        if name in self.lines:
            self.lines.pop(name).release()
        if len(data.vertices) == 0:
            return
        vbo = self.ctx.buffer(data.vertices.astype("f4").tobytes())
        vao = self.ctx.vertex_array(
            self.line_program,
            [(vbo, "3f 4f", "in_position", "in_color")],
        )
        self.lines[name] = GPULines(vbo, vao, len(data.vertices))

    def render_mesh(self, name: str, view_projection: np.ndarray) -> None:
        mesh = self.meshes.get(name)
        if mesh is None:
            return
        self.mesh_program["u_view_projection"].write(view_projection.astype("f4").T.tobytes())
        self.mesh_program["u_light_dir"].value = (0.35, -0.45, -1.0)
        mesh.vao.render(moderngl.TRIANGLES)

    def render_lines(self, name: str, view_projection: np.ndarray, width: float = 1.0) -> None:
        line = self.lines.get(name)
        if line is None:
            return
        self.line_program["u_view_projection"].write(view_projection.astype("f4").T.tobytes())
        self.ctx.line_width = width
        line.vao.render(moderngl.LINES)

    def upload_overlay(self, name: str, surface: pygame.Surface) -> None:
        """Upload/replace an RGBA Pygame surface used as a screen-space overlay."""
        existing = self.overlays.pop(name, None)
        if existing is not None:
            existing.release()

        width, height = surface.get_size()
        rgba = pygame.image.tobytes(surface, "RGBA", True)
        texture = self.ctx.texture((width, height), 4, rgba)
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        texture.repeat_x = False
        texture.repeat_y = False
        self.overlays[name] = GPUOverlay(texture=texture, width=width, height=height)

    def render_overlay(
        self,
        name: str,
        screen_width: int,
        screen_height: int,
        x_px: int = 14,
        y_px: int = 14,
    ) -> None:
        """Render an alpha-blended texture in top-left pixel coordinates."""
        overlay = self.overlays.get(name)
        if overlay is None:
            return

        self.ctx.disable(moderngl.DEPTH_TEST)
        self.overlay_program["u_screen_size"].value = (float(screen_width), float(screen_height))
        self.overlay_program["u_position_px"].value = (float(x_px), float(y_px))
        self.overlay_program["u_size_px"].value = (float(overlay.width), float(overlay.height))
        self.overlay_program["u_texture"].value = 0
        overlay.texture.use(location=0)
        self.overlay_vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.enable(moderngl.DEPTH_TEST)

    def release(self) -> None:
        """Release all GPU resources owned by the renderer."""
        self.clear_batches()
        for overlay in self.overlays.values():
            overlay.release()
        self.overlays.clear()
        self.overlay_vao.release()
        self.overlay_vbo.release()
        self.mesh_program.release()
        self.line_program.release()
        self.overlay_program.release()

# ============================================================================
# FLATTENED SOURCE: app.py
# ============================================================================
ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "dome_config.json"
EXPORT_DIR = ROOT / "exports"


class DomeWorldApp:
    """Interactive ModernGL world for the raw-sector / pinwheel / spline dome system."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        self.config = DomeConfig.load(CONFIG_PATH) if CONFIG_PATH.exists() else DomeConfig()
        self.config.validate()

        self.width = self.config.window_width
        self.height = self.config.window_height
        pygame.display.set_mode(
            (self.width, self.height),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
        )
        pygame.display.set_caption("Raw Wedge 2V Dome — Vertex-Clean Cyclic Pinwheel — ModernGL")

        self.ctx = moderngl.create_context()
        self.renderer = Renderer(self.ctx)
        self.hud = ControlsHud()
        self.minimap_hud = SeamMinimapHud()
        self.crosshair_hud = CrosshairHud()
        self._hud_cache_key: tuple[object, ...] | None = None
        self.clock = pygame.time.Clock()

        self.model: DomePhysicalModel = build_physical_model(self.config)
        self.world_cpu: dict[str, MeshData | LineData] = {}
        self.jig_cpu: dict[str, MeshData | LineData] = {}
        self.camera = FirstPersonCamera(self.config, self.model.topology.sphere_radius_in)

        self.mouse_captured = True
        self.show_wood = True
        self.show_spacer = True
        self.show_nodes = True
        self.show_ideal = True
        self.show_ground = True
        self.show_skin = self.config.skin_enabled
        self.show_hud = True
        self.show_pinwheel_joints = True
        self.show_jig = self.config.jig_enabled
        self.selected_seam = 0
        self.jig_panel = self._find_default_side_panel_index()
        self.solo_panel = False
        self.running = True

        self.zoom_steps = 0
        self.zoom_max_steps = 8
        self.zoom_min_fov_deg = 15.0

        self._capture_mouse(True)
        self.rebuild_world(reset_camera=False)
        self.renderer.upload_overlay("crosshair", self.crosshair_hud.build())
        self._refresh_hud(force=True)
        self.print_controls()

    def _capture_mouse(self, captured: bool) -> None:
        self.mouse_captured = captured
        pygame.event.set_grab(captured)
        pygame.mouse.set_visible(not captured)
        pygame.mouse.get_rel()

    def _find_default_side_panel_index(self) -> int:
        """Pick a first-level side triangle instead of the upper/top region."""
        faces = self.model.topology.faces
        z_levels = sorted({round(float(face.center[2]), 6) for face in faces}, reverse=True)
        target_level = z_levels[2] if len(z_levels) >= 3 else (z_levels[1] if len(z_levels) >= 2 else z_levels[0])
        candidates = [face for face in faces if abs(float(face.center[2]) - target_level) <= 1.0e-6]
        if not candidates:
            return 0
        chosen = max(candidates, key=lambda face: (float(face.center[0]), -abs(float(face.center[1]))))
        return chosen.index

    def current_fov_deg(self) -> float:
        if self.zoom_max_steps <= 0:
            return self.config.fov_deg
        t = self.zoom_steps / float(self.zoom_max_steps)
        return self.config.fov_deg + (self.zoom_min_fov_deg - self.config.fov_deg) * t

    def in_pan_mode(self) -> bool:
        return self.zoom_steps >= self.zoom_max_steps

    def change_zoom(self, delta_steps: int) -> None:
        old_zoom = self.zoom_steps
        self.zoom_steps = max(0, min(self.zoom_max_steps, self.zoom_steps + delta_steps))
        if self.zoom_steps != old_zoom:
            self._refresh_hud(force=True)

    def _refresh_hud(self, force: bool = False) -> None:
        """Rebuild the control legend and seam minimap only when live state changes."""
        face_type = self.model.topology.faces[self.jig_panel].face_type
        explode = self.config.panel_explode_in
        a_folds = [s.fold_angle_deg for s in self.model.seams if s.edge_type == "A"]
        b_folds = [s.fold_angle_deg for s in self.model.seams if s.edge_type == "B"]
        a_fold = sum(a_folds) / len(a_folds) if a_folds else 0.0
        b_fold = sum(b_folds) / len(b_folds) if b_folds else 0.0
        seam_open_a = 2.0 * explode * math.sin(math.radians(a_fold * 0.5))
        seam_open_b = 2.0 * explode * math.sin(math.radians(b_fold * 0.5))
        state = (
            "fly" if self.camera.fly_mode else "walk",
            self.config.spacer_mode,
            self.mouse_captured,
            self.config.panel_joint_handedness,
            self.config.wedge_orientation,
            self.show_jig,
            self.jig_panel,
            face_type,
            self.config.vertex_trim_mode,
            self.config.panel_explode_in,
            self.solo_panel,
            seam_open_a,
            seam_open_b,
            self.zoom_steps,
            self.zoom_max_steps,
            self.in_pan_mode(),
        )
        if not force and state == self._hud_cache_key:
            return

        controls_surface = self.hud.build(
            walk_mode=str(state[0]),
            spacer_mode=str(state[1]),
            mouse_captured=bool(state[2]),
            pinwheel_handedness=str(state[3]),
            wedge_orientation=str(state[4]),
            jig_visible=bool(state[5]),
            jig_panel=int(state[6]),
            jig_face_type=str(state[7]),
            vertex_trim_mode=str(state[8]),
            panel_explode_in=float(state[9]),
            solo_panel=bool(state[10]),
            seam_open_a_in=float(state[11]),
            seam_open_b_in=float(state[12]),
            zoom_steps=int(state[13]),
            zoom_max_steps=int(state[14]),
            pan_mode=bool(state[15]),
        )
        minimap_surface = self.minimap_hud.build(wedge_orientation=str(state[4]))
        self.renderer.upload_overlay("controls_hud", controls_surface)
        self.renderer.upload_overlay("seam_minimap", minimap_surface)
        self._hud_cache_key = state

    def _upload_jig(self) -> None:
        self.jig_panel %= len(self.model.topology.faces)
        self.jig_cpu = build_fabrication_jig(self.model, self.jig_panel)
        for name in ("jig_wood", "jig_fixture"):
            data = self.jig_cpu[name]
            assert isinstance(data, MeshData)
            self.renderer.upload_mesh(name, data)
        line_data = self.jig_cpu["jig_lines"]
        assert isinstance(line_data, LineData)
        self.renderer.upload_lines("jig_lines", line_data)
        self.renderer.upload_mesh("solo_panel", build_single_panel_mesh(self.model, self.jig_panel))
        self._refresh_hud(force=True)

    def rebuild_world(self, reset_camera: bool = False) -> None:
        """Regenerate the complete parametric dome, clean vertex cuts, seams, and jig."""
        self.model = build_physical_model(self.config)
        self.world_cpu = build_world_meshes(self.model)

        self.renderer.clear_batches()
        for name in ("wood", "rigid", "hose", "nodes", "skins"):
            data = self.world_cpu[name]
            assert isinstance(data, MeshData)
            self.renderer.upload_mesh(name, data)
        for name in ("ideal", "ground", "joint_debug"):
            data = self.world_cpu[name]
            assert isinstance(data, LineData)
            self.renderer.upload_lines(name, data)

        self.selected_seam %= len(self.model.seams)
        self.renderer.upload_lines("selected", build_selected_seam_lines(self.model, self.selected_seam))
        self.jig_panel %= len(self.model.topology.faces)
        self.renderer.upload_mesh("solo_panel", build_single_panel_mesh(self.model, self.jig_panel))
        self._upload_jig()

        if reset_camera:
            self.camera = FirstPersonCamera(self.config, self.model.topology.sphere_radius_in)
        self.renderer.upload_overlay("crosshair", self.crosshair_hud.build())
        self._refresh_hud(force=True)

    def selected_seam_info(self) -> str:
        seam = self.model.seams[self.selected_seam]
        return (
            f"{seam.seam_id} | fold {seam.fold_angle_deg:.2f}° | raw gap {seam.raw_gap_angle_deg:.2f}° | "
            f"spline base {seam.spacer_base_width_in:.2f}\" | max hose OD {seam.hose_max_diameter_in:.2f}\""
        )

    def jig_info(self) -> str:
        face = self.model.topology.faces[self.jig_panel]
        return f"JIG=P{self.jig_panel + 1:03d}/{face.face_type}/{('ON' if self.show_jig else 'OFF')}"

    def update_caption(self, fps: float) -> None:
        spacer = self.config.spacer_mode.upper()
        mode = "FLY" if self.camera.fly_mode else "WALK"
        title = (
            f"Raw Wedge 2V Dome — VERTEX-CLEAN CYCLIC PINWHEEL | {fps:5.1f} FPS | {mode} | "
            f"spacer={spacer} | A={self.model.topology.long_edge_in:.2f}\" "
            f"B={self.model.topology.short_edge_in:.2f}\" | trunk={self.config.trunk_diameter_in:.1f}\" | "
            f"PINWHEEL={self.config.panel_joint_handedness.upper()} | WEDGE={self.config.wedge_orientation.upper()} | "
            f"EXPLODE={self.config.panel_explode_in:.1f}in | SOLO={'ON' if self.solo_panel else 'OFF'} | "
            f"ZOOM={self.zoom_steps}/{self.zoom_max_steps}{'/PAN' if self.in_pan_mode() else ''} | "
            f"{self.jig_info()} | {self.selected_seam_info()}"
        )
        pygame.display.set_caption(title)

    def print_controls(self) -> None:
        print(
            """
RAW WEDGE 2V DOME CONTROLS — VERTEX-CLEAN PINWHEEL
---------------------------------------------------
Mouse                    Look around (horizontal inverted)
Mouse wheel              Zoom at center-screen X
Arrow Up/Down or W/S     Walk forward/back
Arrow Left/Right or A/D  Strafe left/right
At maximum zoom only     Arrow keys switch to pan mode
PageUp/PageDown          Move vertically in fly mode
F                        Toggle walk/fly mode
Tab                      Capture/release mouse
Esc                      Release mouse; Esc again quits

H                        Cycle rigid / hose / no spacer
I                        Toggle ideal geodesic edge overlay
N                        Toggle node markers
J                        Toggle pinwheel + clean-vertex-cut debug
K                        Flip pinwheel handedness (CW/CCW)
U                        Cycle 4 raw-wedge orientations
Shift+U                  Cycle wedge orientation backward
Z / X                    Decrease / increase panel explosion by 2 in
C                        Collapse exploded panels back to assembled position
Q                        Solo selected triangle (defaults to a first-level side triangle)
G                        Toggle ground grid
P                        Toggle panel skins
V                        Toggle dome wood visibility
O                        Toggle spacer visibility
[ / ]                    Previous / next seam
T                        Toggle fabrication jig
Y                        Next exact physical panel on jig
Shift+Y                  Previous exact physical panel on jig
, / .                    Decrease / increase trunk diameter by 0.5 in
- / =                    Decrease / increase nominal long A edge by 1 in
R                        Reset camera outside dome
B                        Export CSV BOM
E                        Export dome OBJ/config + full 40-panel fabrication package
F12                      Save screenshot PNG
F1                       Print this help again
F2                       Toggle top control legend
"""
        )

    def cycle_spacer_mode(self) -> None:
        modes = ["rigid", "hose", "none"]
        idx = modes.index(self.config.spacer_mode)
        self.config.spacer_mode = modes[(idx + 1) % len(modes)]
        self._refresh_hud(force=True)

    def export_all(self) -> None:
        EXPORT_DIR.mkdir(exist_ok=True)
        export_config = replace(self.config, panel_explode_in=0.0)
        export_model = build_physical_model(export_config)
        export_world = build_world_meshes(export_model)

        export_bom(export_model, EXPORT_DIR / "dome_bom.csv")
        for name in ("wood", "rigid", "hose", "nodes", "skins"):
            data = export_world.get(name)
            if isinstance(data, MeshData) and len(data.indices):
                export_mesh_obj(data, EXPORT_DIR / f"{name}.obj", name)
        for name in ("jig_wood", "jig_fixture"):
            data = self.jig_cpu.get(name)
            if isinstance(data, MeshData) and len(data.indices):
                export_mesh_obj(data, EXPORT_DIR / f"selected_{name}_P{self.jig_panel + 1:03d}.obj", name)
        export_config.save(EXPORT_DIR / "dome_config.json")
        export_fabrication_package(export_model, EXPORT_DIR / "fabrication_package")
        print(f"Exported ASSEMBLED dome + fabrication package to: {EXPORT_DIR}")
        if self.config.panel_explode_in > 0.0:
            print("Note: panel explosion is visualization-only and was reset to 0 for exports.")

    def save_screenshot(self) -> None:
        EXPORT_DIR.mkdir(exist_ok=True)
        raw = self.ctx.screen.read(components=3, alignment=1)
        image = pygame.image.fromstring(raw, (self.width, self.height), "RGB", True)
        path = EXPORT_DIR / "dome_screenshot.png"
        pygame.image.save(image, path)
        print(f"Saved screenshot: {path}")

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.mouse_captured:
                self._capture_mouse(False)
            else:
                self.running = False
        elif key == pygame.K_TAB:
            self._capture_mouse(not self.mouse_captured)
            self._refresh_hud(force=True)
        elif key == pygame.K_f:
            self.camera.fly_mode = not self.camera.fly_mode
            self._refresh_hud(force=True)
        elif key == pygame.K_h:
            self.cycle_spacer_mode()
        elif key == pygame.K_i:
            self.show_ideal = not self.show_ideal
        elif key == pygame.K_n:
            self.show_nodes = not self.show_nodes
        elif key == pygame.K_j:
            self.show_pinwheel_joints = not self.show_pinwheel_joints
        elif key == pygame.K_k:
            self.config.panel_joint_handedness = (
                "counterclockwise" if self.config.panel_joint_handedness == "clockwise" else "clockwise"
            )
            self.rebuild_world()
        elif key == pygame.K_u:
            direction = -1 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1
            current = WEDGE_ORIENTATION_ORDER.index(self.config.wedge_orientation)
            self.config.wedge_orientation = WEDGE_ORIENTATION_ORDER[(current + direction) % len(WEDGE_ORIENTATION_ORDER)]
            self.rebuild_world()
        elif key == pygame.K_z:
            self.config.panel_explode_in = max(0.0, self.config.panel_explode_in - 2.0)
            self.rebuild_world()
        elif key == pygame.K_x:
            self.config.panel_explode_in = min(96.0, self.config.panel_explode_in + 2.0)
            self.rebuild_world()
        elif key == pygame.K_c:
            self.config.panel_explode_in = 0.0
            self.rebuild_world()
        elif key == pygame.K_q:
            self.solo_panel = not self.solo_panel
            if self.solo_panel and self.jig_panel == 0:
                self.jig_panel = self._find_default_side_panel_index()
                self._upload_jig()
            self._refresh_hud(force=True)
        elif key == pygame.K_g:
            self.show_ground = not self.show_ground
        elif key == pygame.K_v:
            self.show_wood = not self.show_wood
        elif key == pygame.K_o:
            self.show_spacer = not self.show_spacer
        elif key == pygame.K_p:
            self.config.skin_enabled = not self.config.skin_enabled
            self.show_skin = self.config.skin_enabled
            self.rebuild_world()
        elif key == pygame.K_t:
            self.show_jig = not self.show_jig
            self._refresh_hud(force=True)
        elif key == pygame.K_y:
            direction = -1 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1
            self.jig_panel = (self.jig_panel + direction) % len(self.model.topology.faces)
            self._upload_jig()
        elif key == pygame.K_LEFTBRACKET:
            self.selected_seam = (self.selected_seam - 1) % len(self.model.seams)
            self.renderer.upload_lines("selected", build_selected_seam_lines(self.model, self.selected_seam))
            print(self.selected_seam_info())
        elif key == pygame.K_RIGHTBRACKET:
            self.selected_seam = (self.selected_seam + 1) % len(self.model.seams)
            self.renderer.upload_lines("selected", build_selected_seam_lines(self.model, self.selected_seam))
            print(self.selected_seam_info())
        elif key == pygame.K_COMMA:
            self.config.trunk_diameter_in = max(2.0, self.config.trunk_diameter_in - 0.5)
            self.rebuild_world()
        elif key == pygame.K_PERIOD:
            self.config.trunk_diameter_in += 0.5
            self.rebuild_world()
        elif key == pygame.K_MINUS:
            self.config.long_edge_in = max(12.0, self.config.long_edge_in - 1.0)
            self.rebuild_world()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.config.long_edge_in += 1.0
            self.rebuild_world()
        elif key == pygame.K_r:
            self.camera = FirstPersonCamera(self.config, self.model.topology.sphere_radius_in)
            self.zoom_steps = 0
            self._refresh_hud(force=True)
        elif key == pygame.K_b:
            EXPORT_DIR.mkdir(exist_ok=True)
            export_bom(self.model, EXPORT_DIR / "dome_bom.csv")
            print(f"Exported BOM: {EXPORT_DIR / 'dome_bom.csv'}")
        elif key == pygame.K_e:
            self.export_all()
        elif key == pygame.K_F12:
            self.save_screenshot()
        elif key == pygame.K_F1:
            self.print_controls()
        elif key == pygame.K_F2:
            self.show_hud = not self.show_hud
            if self.show_hud:
                self._refresh_hud(force=True)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.width = max(1, event.w)
                self.height = max(1, event.h)
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
            elif event.type == pygame.MOUSEMOTION and self.mouse_captured:
                dx, dy = event.rel
                self.camera.mouse_look(dx, dy)
            elif event.type == pygame.MOUSEWHEEL:
                self.change_zoom(event.y)

    def update_camera(self, dt: float) -> None:
        keys = pygame.key.get_pressed()

        # WASD remains regular movement/strafe regardless of zoom.
        forward = 0.0
        right = 0.0
        vertical = 0.0
        if keys[pygame.K_w]:
            forward += 1.0
        if keys[pygame.K_s]:
            forward -= 1.0
        if keys[pygame.K_d]:
            right += 1.0
        if keys[pygame.K_a]:
            right -= 1.0
        if keys[pygame.K_PAGEUP]:
            vertical += 1.0
        if keys[pygame.K_PAGEDOWN]:
            vertical -= 1.0

        sprint = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        self.camera.move(forward, right, vertical, dt, sprint)

        # Arrow keys either move normally, or switch to pan mode only at max zoom.
        arrow_up = 1.0 if keys[pygame.K_UP] else 0.0
        arrow_down = 1.0 if keys[pygame.K_DOWN] else 0.0
        arrow_right = 1.0 if keys[pygame.K_RIGHT] else 0.0
        arrow_left = 1.0 if keys[pygame.K_LEFT] else 0.0

        if self.in_pan_mode():
            pan_x = arrow_right - arrow_left
            pan_y = arrow_up - arrow_down
            self.camera.pan(pan_x, pan_y, dt, sprint)
        else:
            arrow_forward = arrow_up - arrow_down
            arrow_right_axis = arrow_right - arrow_left
            self.camera.move(arrow_forward, arrow_right_axis, 0.0, dt, sprint)

    def render(self) -> None:
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear(0.035, 0.045, 0.060, 1.0, depth=1.0)

        projection = perspective_matrix(
            self.current_fov_deg(),
            self.width / max(1.0, float(self.height)),
            self.config.near_clip_in,
            self.config.far_clip_in,
        )
        view_projection = projection @ self.camera.view_matrix()

        if self.show_ground:
            self.renderer.render_lines("ground", view_projection, 1.0)
        if self.show_wood:
            self.renderer.render_mesh("solo_panel" if self.solo_panel else "wood", view_projection)

        assembled_analysis_view = self.config.panel_explode_in <= 1.0e-9 and not self.solo_panel
        if self.show_spacer and assembled_analysis_view:
            if self.config.spacer_mode == "rigid":
                self.renderer.render_mesh("rigid", view_projection)
            elif self.config.spacer_mode == "hose":
                self.renderer.render_mesh("hose", view_projection)
        if self.show_nodes and assembled_analysis_view:
            self.renderer.render_mesh("nodes", view_projection)
        if self.show_skin:
            self.renderer.render_mesh("skins", view_projection)
        if self.show_ideal:
            self.renderer.render_lines("ideal", view_projection, 2.0)
        if self.show_pinwheel_joints and not self.solo_panel:
            self.renderer.render_lines("joint_debug", view_projection, 2.5)

        if not self.solo_panel:
            self.renderer.render_lines("selected", view_projection, 4.0)

        if self.show_jig:
            self.renderer.render_mesh("jig_fixture", view_projection)
            self.renderer.render_mesh("jig_wood", view_projection)
            self.renderer.render_lines("jig_lines", view_projection, 3.0)

        if self.show_hud:
            self._refresh_hud()
            self.renderer.render_overlay(
                "controls_hud",
                self.width,
                self.height,
                x_px=self.hud.theme.margin_px,
                y_px=self.hud.theme.margin_px,
            )
            seam_overlay = self.renderer.overlays.get("seam_minimap")
            if seam_overlay is not None:
                self.renderer.render_overlay(
                    "seam_minimap",
                    self.width,
                    self.height,
                    x_px=max(self.hud.theme.margin_px, self.width - seam_overlay.width - self.hud.theme.margin_px),
                    y_px=max(self.hud.theme.margin_px, self.height - seam_overlay.height - self.hud.theme.margin_px),
                )

        crosshair = self.renderer.overlays.get("crosshair")
        if crosshair is not None:
            self.renderer.render_overlay(
                "crosshair",
                self.width,
                self.height,
                x_px=(self.width - crosshair.width) // 2,
                y_px=(self.height - crosshair.height) // 2,
            )

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(144) / 1000.0, 0.05)
            self.handle_events()
            self.update_camera(dt)
            self.render()
            self.update_caption(self.clock.get_fps())

        self.config.jig_enabled = self.show_jig
        self.config.save(CONFIG_PATH)
        self.renderer.release()
        pygame.quit()


def run_interactive_app() -> None:
    try:
        app = DomeWorldApp()
        app.run()
    except Exception as exc:
        pygame.quit()
        print(f"Fatal error: {exc}", file=sys.stderr)
        raise

# ============================================================================
# BUILT-IN VALIDATION MODE
# ============================================================================
def summarize_orientation(orientation: str) -> list[str]:
    cfg = DomeConfig(wedge_orientation=orientation)
    model = build_physical_model(cfg)
    a_members = [m for m in model.members if m.edge_type == "A"]
    b_members = [m for m in model.members if m.edge_type == "B"]
    a_seams = [s for s in model.seams if s.edge_type == "A"]
    b_seams = [s for s in model.seams if s.edge_type == "B"]
    return [
        f"ORIENTATION:           {orientation.upper()}",
        f"  Vertices/Faces:      {len(model.topology.vertices)} / {len(model.topology.faces)}",
        f"  Physical wood:       {len(model.members)}",
        f"  Pinwheel joints:     {len(model.joints)}",
        f"  Interior seams:      {len(model.seams)}",
        f"  A blank range:       {min(m.physical_stock_length_in for m in a_members):.6f} .. {max(m.physical_stock_length_in for m in a_members):.6f} in",
        f"  B blank range:       {min(m.physical_stock_length_in for m in b_members):.6f} .. {max(m.physical_stock_length_in for m in b_members):.6f} in",
        f"  A fold/gap avg:      {sum(s.fold_angle_deg for s in a_seams)/len(a_seams):.6f} / {sum(s.raw_gap_angle_deg for s in a_seams)/len(a_seams):.6f} deg",
        f"  B fold/gap avg:      {sum(s.fold_angle_deg for s in b_seams)/len(b_seams):.6f} / {sum(s.raw_gap_angle_deg for s in b_seams)/len(b_seams):.6f} deg",
        f"  A spline base avg:   {sum(s.spacer_base_width_in for s in a_seams)/len(a_seams):.6f} in",
        f"  B spline base avg:   {sum(s.spacer_base_width_in for s in b_seams)/len(b_seams):.6f} in",
    ]


def run_geometry_validation() -> None:
    cfg = DomeConfig()
    default_model = build_physical_model(cfg)

    print("FOUR-ORIENTATION VERTEX-CLEAN RAW-WEDGE 2V DOME VALIDATION")
    print("=" * 72)
    print(f"Nominal A:            {default_model.topology.long_edge_in:.6f} in")
    print(f"Nominal B:            {default_model.topology.short_edge_in:.6f} in")
    print(f"Mathematical edges:   {len(default_model.topology.edges)}")
    print(f"Pinwheel handedness:  {cfg.panel_joint_handedness.upper()} viewed from exterior")
    print(f"Vertex trim:          {cfg.vertex_trim_mode.upper()}")
    print(f"Default orientation:  {cfg.wedge_orientation.upper()}")
    print()

    for orientation in WEDGE_ORIENTATION_ORDER:
        for line in summarize_orientation(orientation):
            print(line)
        print()

    print("PASS: all four wedge rotations regenerate 120 members, clean vertex cuts,")
    print("      cyclic panel joints, 55 seams, spacers, and fabrication geometry.")
    print("NOTE: POINT_PANEL_OUT uses tangent/line contact to the inward-facing curved arc")
    print("      as its pinwheel receiving datum; broad bearing would require a fitted interface.")

# ============================================================================
# EMBEDDED PROJECT DOCUMENTATION / REFERENCE RESOURCES
# ============================================================================
MASTER_BUILD_SPEC_MD = "# MASTER BUILD SPECIFICATION\n## Vertex-Clean 2V Geodesic Dome From Raw 1/8-Log Wedges, Cyclic Pinwheel Triangle Frames, Inter-Panel Splines/Gaskets, and Exact Fabrication Jigs\n\nThis file is the **single authoritative Markdown specification for the entire project**. It supersedes every earlier README, pinwheel note, change log, prompt fragment, and geometry explanation. If this project is handed to another LLM, CAD programmer, fabricator, or engineer, give them this file first.\n\nThe unusual construction rules in this document are deliberate. **Do not “correct” them into conventional geodesic framing.**\n\n---\n\n# 1. One-sentence definition of the building system\n\nBuild a standard 2-frequency geodesic hemisphere from **40 independent triangular frames** made from **raw circular-sector wood members obtained by splitting round tree trunks lengthwise into eight wedges**; each raw sector may be rotated around its own longitudinal strut axis into any of four cardinal orientations—**POINT_DOME_IN, POINT_PANEL_IN, POINT_DOME_OUT, or POINT_PANEL_OUT**—without changing the 45° raw sector itself; within each triangle, the three members form a same-handed **cyclic pinwheel end-to-side joint sequence**, while neighboring triangles retain duplicated edge members and are joined across the resulting inter-panel gap using a separate rigid spline/key, rubber hose, gasket, or custom spacer; at every geodesic vertex, all panel wood is additionally **clipped to the exact triangular face envelope so no through-member spike protrudes into a neighboring panel’s node territory**.\n\n---\n\n# 2. Non-negotiable conceptual hierarchy\n\nThe project contains three different kinds of geometry. They must remain separate in code and in thought.\n\n## 2.1 Mathematical geodesic geometry\n\nThe mathematical 2V geodesic mesh defines:\n\n- sphere radius;\n- 26 mathematical vertices;\n- 40 triangular faces;\n- 65 unique topological edges;\n- A/B edge classes;\n- face normals;\n- neighboring-face relationships;\n- fold angles.\n\nThese mathematical edges and vertices are **reference geometry**.\n\nThey are not automatically physical saw-cut endpoints.\n\n## 2.2 Physical triangle-panel fabrication geometry\n\nEach mathematical face owns a complete three-member wooden frame.\n\nEach frame contains:\n\n- three raw circular-sector wood solids;\n- three cyclic end-to-side pinwheel joints;\n- three receiving-end clean vertex cuts;\n- three butt-end pinwheel cuts;\n- actual raw-stock blank lengths that can differ from nominal geodesic edge lengths.\n\n## 2.3 Dome assembly geometry\n\nThe completed dome adds:\n\n- duplicated wooden members on each shared face edge;\n- 55 inter-panel seams;\n- rigid splines, rubber hoses, or custom spacers;\n- multi-panel node regions;\n- optional fasteners;\n- optional skins/weather seals.\n\nDo not collapse these three layers into one simplistic line model.\n\n---\n\n# 3. Standard 2V geometry\n\nDefault long geodesic edge:\n\n```text\nA = 72.000000 inches\n```\n\nThe short 2V edge is generated from the actual icosahedral subdivision geometry rather than entered manually.\n\nDefault generated value:\n\n```text\nB ≈ 63.670253 inches\n```\n\nDefault sphere radius:\n\n```text\nR ≈ 116.50 inches\n  ≈ 9.71 feet\n```\n\nDefault sphere diameter:\n\n```text\n≈ 233.0 inches\n≈ 19.42 feet\n```\n\nExpected hemisphere topology:\n\n```text\n26 mathematical vertices\n40 triangular faces\n65 unique mathematical edges\n```\n\nFace classes:\n\n```text\n10 × AAA equilateral faces\n30 × BAB isosceles faces\n```\n\nUnique mathematical edge classes:\n\n```text\n35 × A edges\n30 × B edges\n```\n\nBase perimeter:\n\n```text\n10 × A edges\n```\n\nInterior shared seams:\n\n```text\n25 × A seams\n30 × B seams\n55 total interior seams\n```\n\n---\n\n# 4. Physical wooden-member count\n\nEvery triangular face is a complete physical frame.\n\nNeighboring triangles do **not** share one wooden strut.\n\nTherefore:\n\n```text\n40 panels × 3 physical wood members = 120 physical wood members\n```\n\nBreakdown:\n\n```text\n60 nominal A-class members\n60 nominal B-class members\n```\n\nThe mathematical mesh has 65 unique edges, while the physical panelized construction intentionally has 120 wooden members.\n\nThat duplication is a feature of the construction paradigm.\n\n---\n\n# 5. Raw wood source geometry\n\nDefault source trunk:\n\n```text\ndiameter = 8.000 inches\nradius   = 4.000 inches\n```\n\nDefault longitudinal radial split count:\n\n```text\n8\n```\n\nTherefore every raw member is a genuine:\n\n```text\n45° circular sector\n```\n\nDo not approximate the cross section as a triangle, rectangle, trapezoid, or nominal 2×4.\n\nFor an 8-inch-diameter trunk:\n\n```text\nsector angle                 = 45°\nradial side length           = 4.000000 in\nsector cross-sectional area  = 6.283185 in²\nouter curved arc length      = 3.141593 in\nouter straight chord         = 3.061467 in\n```\n\nThe actual curved surface is rendered as a segmented circular arc.\n\n---\n\n# 6. Four-state raw-wedge orientation system\n\nThe raw 45° circular-sector cross section is **not permanently locked to curved-out / point-in anymore**. The program supports all four cardinal 90° rotations of the sector around each strut's own longitudinal axis. The raw wood is still untouched: no orientation planes the wedge into dimensional lumber and no orientation changes the sector angle.\n\nThe configuration field is:\n\n```text\nwedge_orientation\n```\n\nAllowed values, in the exact cycle used by the **U** key, are:\n\n```text\nPOINT_DOME_IN\nPOINT_PANEL_IN\nPOINT_DOME_OUT\nPOINT_PANEL_OUT\n```\n\n`Shift+U` cycles in the reverse direction.\n\nThe names state where the **sharp sector point / original tree-center line** faces.\n\n## 6.1 POINT_DOME_IN — legacy/default orientation\n\n```text\n                 DOME EXTERIOR / SKY\n                         ↑\n\n                   curved tree side\n                 ╭───────────────╮\n                /                 \\\n               /                   \\\n              /                     \\\n             /                       \\\n            ●\n            ↓ point\n\n              DOME INTERIOR / SPHERE CENTER\n```\n\nThe point faces the sphere center. The curved former-bark arc faces the sky. This is the orientation used by the earlier project revisions.\n\n## 6.2 POINT_PANEL_IN\n\nThe sector is rotated 90° about the strut axis from the legacy state.\n\nThe sharp point faces laterally **toward the center of the member's own triangular panel**. The curved arc faces laterally toward the panel seam/outside-of-triangle direction.\n\nThis is a sideways wedge orientation; neither the point nor the curved arc is primarily dome-in/dome-out.\n\n## 6.3 POINT_DOME_OUT\n\nThe sector is rotated 180° from the legacy state.\n\n```text\n              DOME EXTERIOR / SKY\n                     ↑ point\n                     ●\n                    / \\\n                   /   \\\n                  /     \\\n                 ╰───────╯\n                 curved arc\n\n             DOME INTERIOR / SPHERE CENTER\n```\n\nThe sharp tree-center point faces the sky/exterior. The curved former-bark surface faces inward toward the sphere center. Because the two radial-sawn faces are physically equivalent, their **construction roles are swapped** in this 180° state so the pinwheel butt joint still reaches an available flat receiving face before the clean geodesic vertex boundary.\n\n## 6.4 POINT_PANEL_OUT\n\nThe sector is rotated 270° from the legacy state (or -90°).\n\nThe sharp point faces laterally **across the mathematical panel edge / toward the seam**. The curved former-bark surface faces laterally **toward the center of the triangular panel**.\n\nThis orientation has an important physical distinction: the panel-interior side of the wedge is now the **curved tree surface**, not a flat radial-sawn face. The software therefore uses the tangent plane at the midpoint of that curved arc as the pinwheel receiving datum. This represents tangent/line contact to an untouched round surface. A real fabrication seeking broad bearing in this orientation would need a saddle cut, fitted block, compliant pad, or another purpose-designed interface. The software must not falsely describe this as full flat-face bearing.\n\n## 6.5 Local coordinate definition\n\nFor every directed member:\n\n```text\nlocal X = strut longitudinal direction\nlocal Y = in the panel plane toward panel center\nlocal Z = panel normal toward dome exterior\n```\n\nThe four states are rotations in the local Y/Z cross-section plane. The point directions are:\n\n```text\nPOINT_DOME_IN   : -Z\nPOINT_PANEL_IN  : +Y\nPOINT_DOME_OUT  : +Z\nPOINT_PANEL_OUT : -Y\n```\n\nThe physical sector is rotated; this is **not a cosmetic mesh flip**. End-cut intersections, seam offsets, spacer geometry, blank lengths, jig geometry, exports, and HUD state are regenerated from the selected orientation.\n\n## 6.6 Orientation is independent from pinwheel handedness\n\n`panel_joint_handedness` controls whether the three triangle members chase clockwise or counterclockwise when viewed from the dome exterior.\n\n`wedge_orientation` controls rotation of each individual sector around its strut axis.\n\nThey are independent parameters. Flipping CW/CCW does not change the sector orientation. Cycling the sector orientation does not reverse the pinwheel graph.\n\n## 6.7 The clean red geodesic-vertex cut remains authoritative in all four states\n\nNo orientation is allowed to reintroduce the old free spikes at dome nodes. Every receiving end remains clipped by the exact incoming mathematical triangle-edge plane. The complete physical receiving cut polygon must lie on that plane.\n\nBecause a rotated sector's point axis can intersect an oblique triangle-boundary plane before or after the abstract mathematical vertex when expressed as a one-dimensional axis parameter, **the cut polygon and valid half-space are authoritative**, not a simplistic expectation that the point-axis setback is always exactly zero.\n\n---\n\n# 7. Longitudinal contact surfaces rotate with the wedge\n\nThe two flat radial-sawn faces are part of the physical sector and rotate with it. They are not imaginary faces that remain fixed in panel coordinates while the wood rotates.\n\nFor the legacy `POINT_DOME_IN` state:\n\n- one radial face is the seam-side face used by the inter-panel spline;\n- the opposite radial face is the pinwheel receiving face.\n\nFor `POINT_DOME_OUT`, those two physically equivalent radial faces exchange construction roles after the 180° rotation so the assembly remains buildable and vertex-clean.\n\nFor the sideways modes, surface availability changes:\n\n- `POINT_PANEL_IN`: the point faces panel center; the configured radial receiver face is retained and the seam solver follows the rotated seam face;\n- `POINT_PANEL_OUT`: the curved arc faces panel center, so the pinwheel receiving datum becomes the **arc-midpoint tangent plane** rather than pretending a nonexistent inward-facing flat face exists.\n\nThe inter-panel seam solver likewise follows the selected rotated seam radial face and recomputes member lateral offset, included gap angle, spline base width, and hose geometry from the actual orientation.\n\nThe UI and exported BOM/cut schedule must always record the active `wedge_orientation`.\n\n---\n\n# 8. The individual triangle is NOT a conventional triangle\n\nThis is one of the most important rules in the entire project.\n\nA physical triangle must **not** be constructed as three struts whose endpoints meet neatly at the three mathematical vertices.\n\nForbidden conceptual result:\n\n```text\n                 ●\n                / \\\n               /   \\\n              /     \\\n             /       \\\n            ●---------●\n```\n\nForbidden corner logic:\n\n```text\nmember A ends at vertex\nmember B ends at same vertex\nsplit the corner angle 50/50\ncut two matching miters\n```\n\nThat is ordinary triangular framing and is not this system.\n\n---\n\n# 9. Cyclic pinwheel triangle construction\n\nEach physical panel is a **cyclic, chasing, end-to-side pinwheel**.\n\nFor a canonical upright triangle viewed from the dome exterior:\n\n```text\n                    A\n                   / \\\n                  /   \\\n                 /     \\\n                C-------B\n```\n\nDefine:\n\n```text\nRIGHT = A → B\nBASE  = B → C\nLEFT  = C → A\n```\n\nThe required end-to-side relationships are:\n\n```text\nLEFT  terminates into RIGHT\nRIGHT terminates into BASE\nBASE  terminates into LEFT\n```\n\nSymbolically:\n\n```text\nLEFT → RIGHT → BASE → LEFT\n```\n\nwhere:\n\n```text\nX → Y\n```\n\nmeans:\n\n```text\nTHE TERMINATING END OF X BUTTS AGAINST THE LONGITUDINAL PANEL-INTERIOR SIDE OF Y\n```\n\nEvery member therefore has exactly:\n\n```text\none RECEIVING end\none BUTT / TERMINATING end\n```\n\n---\n\n# 10. Canonical exterior-view pinwheel interpretation\n\nViewed from the dome exterior, the conceptual triangle resembles:\n\n```text\n                          RIGHT\n                            /\n                           /\n                          /\n             LEFT -------/\n                        /\n                       /\n                      /\n                     /\n                    /\n                   /\n                  /\n                 /\n                /\n               /\n              /\n             /\n            /\n           /\n          /\n         /\n        /\n       /____________________________ BASE\n```\n\nAt the top corner:\n\n```text\nLEFT terminates into RIGHT\nRIGHT is the receiver\n```\n\nAt the lower-right corner:\n\n```text\nRIGHT terminates into BASE\nBASE is the receiver\n```\n\nAt the lower-left corner:\n\n```text\nBASE terminates into LEFT\nLEFT is the receiver\n```\n\nThis chasing relationship must survive every 3D transformation applied to the panel.\n\n---\n\n# 11. Handedness\n\nAll panels must use one globally consistent pinwheel handedness when viewed from the **dome exterior**.\n\nDefault:\n\n```text\nCLOCKWISE\n```\n\nThe generated geodesic face winding is normalized before physical member assignment so triangles do not randomly mirror the pinwheel.\n\nFor normalized exterior-CCW face vertices `(v0, v1, v2)`, the default physical clockwise cycle is generated consistently.\n\nThe valid graph is one closed directed cycle:\n\n```text\n0 → 1\n1 → 2\n2 → 0\n```\n\nor the globally reversed form in counterclockwise mode.\n\nA mixture of clockwise and counterclockwise panels is invalid.\n\n---\n\n# 12. Mathematical vertices are reference points, not generic saw endpoints\n\nThe mathematical geodesic vertex remains important, but it does not mean:\n\n```text\ncut both members square here\n```\n\nor:\n\n```text\nmake both members end here\n```\n\nInstead, the mathematical vertex provides the exact geometric location through which the **clean triangle-envelope cut plane** passes.\n\nThis revision therefore makes a more precise statement than the older free-overhang model:\n\n> A geodesic vertex is not a generic member endpoint, but it is the apex reference that limits the physical triangle footprint. The receiving member is cut by the adjacent ideal-edge plane passing through that vertex, so the resulting panel terminates cleanly without trespassing into neighboring panel territory.\n\n---\n\n# 13. Why the previous free through-overhang was wrong in the complete dome\n\nThe earlier pinwheel implementation allowed the receiving member to continue a configurable distance beyond the mathematical corner.\n\nThat was useful for demonstrating the end-to-side relationship in a single isolated triangle.\n\nHowever, when many physical triangles were assembled into the full dome, several independent receiving-member extensions converged around each geodesic node.\n\nThe result was exactly the problem visible in the supplied dome screenshot:\n\n- spikes extending past face corners;\n- neighboring panel wood overlapping at vertices;\n- star-shaped collisions at node locations;\n- no clean visual or physical termination point.\n\nThat behavior is no longer allowed.\n\nThe old arbitrary default:\n\n```text\n2-inch free receiving overhang\n```\n\nhas been removed from the authoritative construction geometry.\n\n---\n\n# 14. New clean geodesic-vertex rule\n\nThis rule is mandatory.\n\n## 14.1 Core rule\n\nEvery physical triangular panel is constrained at its corners by the planes of its **other ideal triangle edges**.\n\nAt the receiving end of a member:\n\n1. identify the incoming/previous member in the pinwheel cycle;\n2. identify that previous member’s mathematical geodesic edge;\n3. take the plane containing that ideal edge and the panel outward normal;\n4. intersect every longitudinal generator of the receiving raw-sector solid with that plane;\n5. use those intersection points as the actual receiving-end cut polygon.\n\nThis plane is the **CLEAN GEODESIC VERTEX CUT**.\n\n## 14.2 What the cut does\n\nIt removes the free spike that previously projected beyond the corner.\n\nIt allows the seam-side edge of the sector to approach the mathematical vertex naturally.\n\nIt prevents the member from continuing longitudinally across the adjacent triangle-edge boundary.\n\nThe result is a panel corner that terminates in the geometric territory of its own face rather than invading another panel at the node.\n\n## 14.3 Visual debug convention\n\nThe application draws this cut in:\n\n```text\nRED\n```\n\nThis is intentionally matched to the red cut indication in the supplied screenshot.\n\n---\n\n# 15. The clean vertex cut is not a square crosscut\n\nDo not replace the receiving cut with a plane perpendicular to the member axis.\n\nThat would be a conventional square end and would not preserve the exact triangular face boundary.\n\nThe receiving-end plane is generally oblique relative to the member axis because it is aligned with the neighboring mathematical edge.\n\nFor a flat triangle, this is a plan-view miter-like cut whose plane contains the panel normal.\n\nIts normal therefore lies in the panel plane.\n\nConsequently:\n\n```text\nreceiving cut out-of-panel pitch = approximately 0°\n```\n\nwhile its plan-view angle varies with the triangle corner geometry.\n\n---\n\n# 16. The butt end remains a different cut\n\nThe opposite end of the same member is still the cyclic pinwheel butt end.\n\nIt is solved differently.\n\nThe butt end is cut against the actual `PANEL_INTERIOR_FACE` of the next receiving member.\n\nProcedure:\n\n1. identify the next member in the directed pinwheel cycle;\n2. construct the next member’s panel-interior radial face as a true 3D plane;\n3. extend every longitudinal generator of the terminating member’s sector geometry;\n4. intersect each generator with the receiving plane;\n5. use the resulting polygon as the physical butt-end cut;\n6. cap the member with that polygon.\n\nThe butt cut is therefore often a **compound plane** relative to the terminating piece.\n\nIt is not the same cut as the receiving-end vertex trim.\n\n---\n\n# 17. Two end cuts per member\n\nEvery one of the 120 raw-sector pieces has two fundamentally different fabrication cuts.\n\n## End A — receiving / clean vertex end\n\nPurpose:\n\n```text\nprevent node overlap\nconstrain panel to clean geodesic corner\nprovide receiving side for previous member\n```\n\nPlane source:\n\n```text\nincoming ideal triangle-edge plane\n```\n\nDebug color:\n\n```text\nRED\n```\n\n## End B — terminating / cyclic butt end\n\nPurpose:\n\n```text\nterminate member into the next member's side\ncomplete cyclic pinwheel joint\n```\n\nPlane source:\n\n```text\nnext member's PANEL_INTERIOR_FACE\n```\n\nDebug color:\n\n```text\nGREEN\n```\n\nThese cuts must never be conflated.\n\n---\n\n# 18. No conventional 50/50 miter logic\n\nThe following algorithm is explicitly forbidden:\n\n```text\ncorner_angle / 2\ncut member A to half-angle\ncut member B to half-angle\njoin both at virtual vertex\n```\n\nThere is no symmetric shared miter plane in the pinwheel panel construction.\n\nThe receiving end and terminating end have different owners, different planes, and different fabrication purposes.\n\n---\n\n# 19. Nominal edge length versus physical blank length\n\nThe values:\n\n```text\nA = 72.000 in\nB ≈ 63.670253 in\n```\n\nare **nominal geodesic edge dimensions**.\n\nThey define the mathematical dome.\n\nThey are not automatically the raw stock blank lengths after both oblique end cuts are considered.\n\nEvery member stores separately:\n\n```text\nnominal_geodesic_length\nphysical_stock_blank_length\nphysical_sector_point_axis_length\nvolume_equivalent_length\nreceiving_axis_setback\nreceiving_axis_extension\nbutt_axis_setback\n```\n\nUnder the default 8-inch-trunk / 72-inch-A configuration, the corrected vertex-clean model currently produces approximately:\n\n```text\nA-class raw blank range:\n69.984 .. 70.788 inches\n\nB-class raw blank range:\n61.552 .. 63.011 inches\n```\n\nThese values vary by the exact member role, panel type, edge offset, and whether the panel is associated with the dome base geometry.\n\nDo not replace them with one universal “cut every A at 72 inches” instruction.\n\n---\n\n# 20. Current default unique member cut recipes\n\nThe default physical model resolves to eight recurring member cut recipes.\n\nThe following values are provided as **validation references**, not hard-coded source-of-truth constants.\n\n`Receive yaw` and `Butt yaw/pitch` describe the cut-plane normal in the member’s local coordinate frame. They are geometric descriptors, not guaranteed to equal the dial readings of every commercial compound-miter saw.\n\n| Qty | Edge | Point offset | Raw blank | Receive setback | Butt setback | Receive yaw | Receive pitch | Butt yaw | Butt pitch |\n|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|\n| 5 | A | 1.5307 | 69.9844 | 1.0493 | 2.0157 | -34.431° | 0° | 34.431° | 22.5° |\n| 5 | A | 0.9445 | 70.0257 | 0.5453 | 2.3128 | -30.000° | 0° | 30.000° | 22.5° |\n| 5 | A | 1.5307 | 70.0257 | 0.8838 | 1.9743 | -30.000° | 0° | 30.000° | 22.5° |\n| 20 | A | 0.9445 | 70.7026 | 0.5453 | 1.6359 | -30.000° | 0° | 30.000° | 22.5° |\n| 25 | A | 0.9445 | 70.7881 | 0.6474 | 1.6138 | -34.431° | 0° | 34.431° | 22.5° |\n| 5 | B | 0.7970 | 61.5517 | 0.3082 | 2.4022 | -21.138° | 0° | 34.431° | 22.5° |\n| 25 | B | 0.7970 | 62.2625 | 0.3082 | 1.6914 | -21.138° | 0° | 34.431° | 22.5° |\n| 30 | B | 0.7970 | 63.0105 | 0.5464 | 1.1627 | -34.431° | 0° | 21.138° | 22.5° |\n\nThe exported `ALL_MEMBER_CUT_SCHEDULE.csv` is authoritative for individual pieces.\n\n---\n\n# 21. Why the butt cut has approximately 22.5° local pitch\n\nThe raw member is an unchanged 45° circular sector.\n\nIts panel-interior radial surface is one of the two radial faces of that sector.\n\nEach radial face lies 22.5° from the sector bisector.\n\nBecause the receiving member’s panel-interior face becomes the terminating member’s butt plane, a recurring 22.5° out-of-panel component naturally appears in the local compound cut description.\n\nThat is a consequence of keeping the raw wedge instead of squaring it into dimensional lumber.\n\n---\n\n# 22. Inter-panel seam system remains separate\n\nThe clean node cut does not convert the project into a shared-strut geodesic frame.\n\nTwo adjacent triangles still own two independent wooden members along a shared mathematical edge.\n\nThe assembly remains:\n\n```text\nRAW WEDGE FROM PANEL A\n        ↓\nSEPARATE SPACER / KEY / HOSE / GASKET\n        ↓\nRAW WEDGE FROM PANEL B\n```\n\nThe panel corner system and panel seam system are separate mechanisms.\n\n---\n\n# 23. Geodesic face-fold calculation\n\nFor every interior mathematical edge:\n\n1. find the two adjacent faces;\n2. obtain their outward unit normals `N1` and `N2`;\n3. calculate the small face-fold angle:\n\n```text\nfold = acos(clamp(dot(N1, N2), -1, 1))\n```\n\nThe internal dihedral is:\n\n```text\n180° - fold\n```\n\nReference fold angles for the default standard 2V geometry:\n\n```text\nA seam ≈ 18.0291°\nB seam ≈ 22.4589°\n```\n\nThe generated geometry is authoritative.\n\n---\n\n# 24. Raw-sector spacer gap\n\nFor an 8-way trunk split:\n\n```text\nraw sector angle = 45°\n```\n\nThe approximate spacer gap relationship is:\n\n```text\nraw_gap = 45° - face_fold\n```\n\nReference values:\n\n```text\nA seam raw gap ≈ 26.9709°\nB seam raw gap ≈ 22.5411°\n```\n\n---\n\n# 25. Rigid spline/key mode\n\nThe rigid key runs longitudinally between the two panel-owned edge members.\n\nThe key profile is generated from the actual opposing `SEAM_FACE` planes.\n\nConceptual cross-section:\n\n```text\n                       EXTERIOR\n                          ↑\n\n       raw wood          spline          raw wood\n          \\                ▲                /\n           \\              / \\              /\n            \\            /   \\            /\n             \\          /     \\          /\n              ●________/_______\\________●\n\n                          ↓\n                       INTERIOR\n```\n\nFor full 4-inch face contact, default reference base widths are approximately:\n\n```text\nA seam ≈ 1.87 in\nB seam ≈ 1.56 in\n```\n\nThese are generated values, not fixed constants.\n\n---\n\n# 26. Rubber hose / gasket mode\n\nThe inter-panel spacer may instead be represented as a round hose or compressible gasket.\n\nFor gap angle `G` and hose radius `r`, the ideal two-line tangent relationship is:\n\n```text\ndistance from virtual apex to hose center:\nd = r / sin(G/2)\n\ncontact distance along each face:\nt = r / tan(G/2)\n```\n\nThe tangent point must remain on the available wood face.\n\nApproximate default maximum uncompressed hose diameters:\n\n```text\nA seam ≈ 1.92 in\nB seam ≈ 1.59 in\n```\n\nThe program clamps or warns when a requested hose is geometrically too large.\n\n---\n\n# 27. Hose is not automatically an angle-locking structural connector\n\nA soft hose may function as:\n\n- gasket;\n- compression seal;\n- tolerance absorber;\n- weather barrier;\n- gap filler.\n\nIt does not automatically prevent two panels from rotating around the seam.\n\nTherefore distinguish:\n\n```text\nHOSE_GASKET_ONLY\n```\n\nfrom a future or conceptual:\n\n```text\nHOSE_WITH_MECHANICAL_ANGLE_CONSTRAINT\n```\n\nwhich may use bolts, plates, straps, clamps, node hardware, or a rigid internal key.\n\n---\n\n# 28. Dome vertex / node concept after the clean cut\n\nThe new triangle-envelope trim removes wooden spikes from the node.\n\nIt does **not** imply that a multi-way dome vertex requires no connector.\n\nAt a mathematical geodesic vertex, several complete panel corners, seam keys, gaskets, and potential fasteners still converge.\n\nThe clean trim merely establishes a disciplined boundary:\n\n> Each panel contributes only the wood that belongs to its own corner geometry instead of arbitrary through-member protrusions.\n\nOptional node connector types may still include:\n\n```text\nNONE\nRUBBER_PUCK\nWOODEN_KEY\nMETAL_PLATE\nPROCEDURAL_FILLER\nCUSTOM\n```\n\n---\n\n# 29. Fabrication jig — purpose\n\nThe project now contains a true parametric fabrication jig system.\n\nThe jig is not a generic picture of a triangle.\n\nIt is generated from the exact solved physical panel.\n\nIts purpose is to make the unusual triangle repeatable without manually measuring every compound cut from scratch.\n\nThe jig must establish:\n\n- exact panel geometry;\n- exact member placement;\n- raw-sector orientation;\n- receiving-end clean vertex cut planes;\n- butt-end pinwheel cut planes;\n- exterior/up orientation;\n- correct pinwheel handedness.\n\n---\n\n# 30. Jig orientation\n\nThe fabrication jig lays one selected triangle flat.\n\nThe panel-local convention is:\n\n```text\nDOME EXTERIOR / PANEL +Z = JIG UP\n```\n\nThe **wood itself retains the selected `wedge_orientation`**. Therefore the curved tree side is not always up and the tree-center point is not always down. In `POINT_DOME_OUT`, for example, the point is up and the curved arc is down. In sideways modes the point/arc lie primarily across the jig plane.\n\nThe jig automatically lifts/supports the flattened wood by the amount necessary to keep the lowest rotated sector surface above the base. This preserves the exact dome orientation rather than silently rotating each wedge back to the legacy position for fabrication.\n\nThe global clockwise/CCW pinwheel interpretation remains visually consistent.\n\n---\n\n# 31. Jig elements\n\nThe generated jig contains four major categories.\n\n## 31.1 Base plate\n\nA flat support board under the triangle.\n\nDefault virtual thickness:\n\n```text\n0.75 in\n```\n\nThe base extends beyond the triangle by a configurable margin.\n\n## 31.2 Locator rails\n\nGray rails establish the exact placement of each raw sector’s **sector-point axis**.\n\nThe point-axis is used as a repeatable reference because irregular bark curvature is a poor fabrication datum.\n\nThe rails sit on the seam side of the point-axis so a wedge can be laid against them repeatably.\n\n## 31.3 Red clean-vertex guide plates\n\nThese plates coincide with the exact receiving-end triangle-envelope cut planes.\n\nTheir purpose is to produce the red cuts that eliminate the node overlap shown in the earlier screenshot.\n\n## 31.4 Green butt-cut guide plates\n\nThese plates coincide with the active cyclic receiving datum that terminates each member into the next member in the pinwheel. In the three flat-face-compatible states this is a radial-sawn receiving plane. In `POINT_PANEL_OUT` it is the tangent plane at the inward-facing curved arc midpoint, representing tangent/line contact unless a fitted bearing interface is added.\n\nBecause these can be compound relative to the stock, the 3D guide itself is more authoritative than a single angle number.\n\n---\n\n# 32. Jig color language\n\nIn the application and exported jig logic:\n\n```text\nBLUE   = ideal mathematical triangle\nGRAY   = locator / fixture rails\nRED    = clean geodesic-vertex receiving cut\nGREEN  = cyclic butt/contact cut\nWOOD   = exact solved raw-sector members\n```\n\nThis color language is intentionally simple and should not be changed casually.\n\n---\n\n# 33. Jig fabrication sequence\n\nA practical conceptual workflow is:\n\n1. generate or select the appropriate jig variant;\n2. place the jig with panel +Z / dome exterior upward;\n3. set `wedge_orientation` to the fabrication state being built and place each raw wedge in that exact rotated orientation;\n4. support/lift the wedge as shown by the generated fixture and locate it against its exact point-axis rail;\n5. mark or cut the receiving end using the red vertex guide;\n6. mark or cut the terminating end using the green pinwheel butt guide;\n7. return the three cut members to the jig;\n8. verify that each butt end lands on the next member’s panel-interior face;\n9. verify that no receiving end projects beyond the clean triangle corner boundary;\n10. clamp the cyclic assembly;\n11. drill/fasten according to the eventual mechanical joint design;\n12. remove the completed panel as one repeatable triangular module.\n\nThe code models geometry only and does not prescribe a certified fastening schedule.\n\n---\n\n# 34. Jig variants\n\nThe default 40 panels reduce to **four reusable rotationally equivalent jig variants** under the current geometry.\n\nThe generated fabrication package currently groups them as:\n\n```text\nJIG_VARIANT_01_BAB  → 25 panels\nJIG_VARIANT_02_AAA  → 5 panels\nJIG_VARIANT_03_AAA  → 5 panels\nJIG_VARIANT_04_BAB  → 5 panels\n```\n\nThe difference between nominally similar triangle classes arises from physical edge offsets and base/perimeter conditions.\n\nDo not assume “one AAA jig and one BAB jig” is always sufficient.\n\nThe code determines variants from actual solved member recipes.\n\n---\n\n# 35. Fabrication package exports\n\nThe project includes a generated `fabrication_package/` directory and can regenerate it from the model.\n\nIt contains:\n\n```text\nDOME_BOM.csv\nALL_MEMBER_CUT_SCHEDULE.csv\nJIG_VARIANTS.csv\npanel_jig_svgs/\n    PANEL_001_JIG.svg\n    ...\n    PANEL_040_JIG.svg\njig_variant_objs/\n    reusable exact 3D fixture OBJ files\n    matching example wood OBJ files\n```\n\nThe SVG files are exterior-view dimensional panel plans.\n\nThe OBJ jig variants are 3D fixture concepts containing the actual cut-guide orientations.\n\n---\n\n# 36. Cut schedule interpretation\n\n`ALL_MEMBER_CUT_SCHEDULE.csv` contains two records per wood member:\n\n```text\nRECEIVING\nBUTT\n```\n\nEach record contains:\n\n- panel ID;\n- panel type;\n- member ID;\n- local edge index;\n- A/B edge class;\n- nominal geodesic length;\n- raw stock blank length;\n- cut purpose;\n- cut-plane normal in member-local coordinates;\n- geometric yaw;\n- geometric pitch;\n- setback from virtual vertex;\n- mating member ID.\n\nThe plane-normal vector is the most unambiguous representation.\n\nIf translating to a particular saw or CNC machine, derive that machine’s settings from the plane normal instead of assuming the reported yaw/pitch map directly to the tool’s dial conventions.\n\n---\n\n# 37. Local member coordinate frame for cut descriptions\n\nEach member uses:\n\n```text\nlocal X = along member tangent\nlocal Y = toward panel interior\nlocal Z = toward dome exterior\n```\n\nA square crosscut would have a plane normal approximately:\n\n```text\n(+1, 0, 0)\n```\n\nThe receiving vertex cut has approximately zero Z component because the plane is vertical to the panel.\n\nThe butt cut generally has nonzero Y and Z components because it coincides with the angled radial face of the receiving raw sector.\n\n---\n\n# 38. Panel-local edge frame\n\nFor a directed panel edge:\n\n```text\nT = normalized edge direction\nN = outward face normal\nS = in-plane direction perpendicular to edge, pointing toward panel center\n```\n\nConceptually:\n\n```text\nlocal X = T\nlocal Y = S\nlocal Z = N\n```\n\nThe raw-sector point axis is displaced inward from the mathematical edge according to the solved seam/member offset.\n\nThe cross section is generated in the local Y-Z plane and extruded along X.\n\n---\n\n# 39. Clean vertex cut algorithm in implementation terms\n\nFor member `Mi`:\n\n```text\nprevious member = M(i-1)\nnext/receiver    = M(i+1)\n```\n\nAt `Mi`’s receiving end:\n\n1. find the ideal edge belonging to `M(i-1)`;\n2. obtain that edge’s inward normal within the panel;\n3. choose the shared virtual corner as a point on the cut plane;\n4. this plane contains the panel normal and the previous ideal edge;\n5. for every raw-sector boundary generator `P + t*T`, solve:\n\n```text\ndot((P + t*T) - plane_point, plane_normal) = 0\n```\n\n6. collect all solved intersection points;\n7. use the polygon as `receiving_cut_points`;\n8. cap the sector solid there.\n\nNo arbitrary overhang distance is used.\n\n---\n\n# 40. Butt cut algorithm in implementation terms\n\nFor member `Mi` terminating into `M(i+1)`:\n\n1. identify the next member’s `PANEL_INTERIOR_FACE` plane;\n2. for each generator of `Mi`’s raw-sector boundary, solve intersection with that plane;\n3. collect the points as `butt_contact_points`;\n4. use them to create the actual oblique butt-end cap;\n5. record the plane, contact polygon, axis setback, and mating member ID.\n\n---\n\n# 41. Raw stock length calculation\n\nBoth end cuts are oblique.\n\nTherefore a single point-axis distance does not necessarily equal the minimum raw blank required.\n\nFor every cross-section boundary generator, the solver obtains:\n\n```text\nt_receive\n t_butt\n```\n\nThe finished generator length is:\n\n```text\nt_butt - t_receive\n```\n\nThe raw blank must encompass the extreme longitudinal cut extents:\n\n```text\nblank_length = max(t_butt) - min(t_receive)\n```\n\nThis is what the BOM reports as the physical raw stock blank length.\n\n---\n\n# 42. Exact volume calculation with oblique cuts\n\nThe end-plane intersection parameter varies affinely over the cross section.\n\nTherefore the average longitudinal extent can be evaluated at the area centroid of the circular sector.\n\nFor sector angle `θ` and radius `R`, the centroid lies along the sector bisector at:\n\n```text\n4 R sin(θ/2)\n----------------\n     3 θ\n```\n\nUsing the receiving and butt plane intersections at that centroid gives the volume-equivalent length.\n\nThen:\n\n```text\nwood volume = sector area × volume-equivalent length\n```\n\nThis is more accurate than multiplying nominal edge length by sector area.\n\n---\n\n# 43. Structural section caveat\n\nThe raw sector can contain more cross-sectional wood area than a conventional dimensional member while still having different bending properties.\n\nDo not infer equal strength from equal area alone.\n\nFuture structural analysis may use:\n\n- centroid;\n- principal axes;\n- second moments of area;\n- section modulus;\n- buckling analysis;\n- connection capacity;\n- wood grading;\n- moisture effects.\n\nThis project is currently a geometry/fabrication concept simulator, not a structural certification package.\n\n---\n\n# 44. ModernGL world controls\n\nMovement:\n\n```text\nMouse                 look / head control\nArrow keys / WASD     move / strafe\nShift                 sprint\nPageUp / PageDown     vertical movement in fly mode\nF                     walk / fly\nTab                   capture / release mouse\nEsc                   release / exit\n```\n\nWorld/construction:\n\n```text\nH                     rigid / hose / none spacer\nI                     ideal geodesic overlay\nN                     node markers\nJ                     pinwheel + red vertex-cut debug\nK                     flip global CW/CCW pinwheel\nU                     cycle wedge orientation forward\nShift+U               cycle wedge orientation backward\nG                     ground grid\nP                     panel skins\nV                     dome wood visibility\nO                     spacer visibility\n[ / ]                 select seam\n```\n\nFabrication jig:\n\n```text\nT                     show / hide exact jig\nY                     next panel on jig\nShift+Y               previous panel on jig\n```\n\nGeometry editing:\n\n```text\n, / .                 trunk diameter down/up\n- / =                 nominal A length down/up\n```\n\nFile/output:\n\n```text\nB                     export BOM\nE                     export dome objects + full fabrication package\nF12                   screenshot\nF1                    console help\nF2                    hide/show HUD\n```\n\n---\n\n# 45. In-world HUD\n\nThe upper-left transparent legend reports live state including:\n\n```text\nWALK / FLY\nSPACER mode\nMOUSE CAPTURED / FREE\nPINWHEEL CW / CCW\nWEDGE POINT DOME-IN / PANEL-IN / DOME-OUT / PANEL-OUT\nVERTEX CUT CLEAN TRIANGLE ENVELOPE\nJIG ON/OFF\nselected jig panel\nselected panel type\nRED=VERTEX CUT\nGREEN=BUTT CUT\n```\n\nThe HUD is rendered as a screen-space OpenGL overlay after the 3D scene and ignores the depth buffer.\n\n---\n\n# 46. Pinwheel/debug visualization\n\n`J` toggles construction debug geometry.\n\nThe debug layer includes:\n\n- physical sector-point axes;\n- green butt/contact polygons;\n- red clean receiving-end cut polygons;\n- virtual mathematical vertex markers.\n\nThe virtual vertex and physical cut geometry are deliberately shown simultaneously so it is visually obvious that the construction is not a conventional tip-to-tip triangle.\n\n---\n\n# 47. Fabrication jig visualization in the world\n\nThe jig is placed flat beside the dome rather than replacing the dome.\n\nIt contains:\n\n- exact copied wood solids from the selected panel;\n- a base plate;\n- gray locating rails;\n- red clean-vertex guide plates;\n- green compound butt-cut guide plates;\n- blue mathematical triangle lines.\n\nThe jig is regenerated when:\n\n- selected panel changes;\n- trunk diameter changes;\n- nominal A length changes;\n- pinwheel handedness changes;\n- any geometry-affecting setting changes.\n\n---\n\n# 48. Panel skin concept\n\nOptional triangular skins may be shown outside each panel.\n\nA skin belongs to one complete triangular panel.\n\nIt does not merge neighboring wooden edge members.\n\nThe seam spline/gasket can therefore be interpreted as both a structural separator and potential weather-seal interface between panelized skins.\n\n---\n\n# 49. Node markers\n\nThe current application renders mechanical node markers at the 26 mathematical vertices as references.\n\nThese are not intended to hide collisions.\n\nThe corrected wood geometry should terminate cleanly before any node connector is designed.\n\nA future node subsystem can replace the markers with actual rubber, wood, metal, or procedural connectors.\n\n---\n\n# 50. Collision and validation philosophy\n\nThe model validates critical invariants instead of trusting visual appearance alone.\n\nRequired invariants include:\n\n```text\n26 vertices\n40 faces\n65 mathematical edges\n120 wood members\n120 cyclic panel corner joints\n55 interior seams\n60 A wood members\n60 B wood members\n25 A seams\n30 B seams\n```\n\nEvery panel must form one closed directed three-member cycle.\n\nEvery receiving cut polygon must lie on its clean vertex plane.\n\nThe receiving cut plane must contain the panel normal rather than being accidentally tilted.\n\nEvery butt contact must lie on the intended receiving face.\n\nThe butt end must remain inside the next vertex boundary rather than protruding beyond the panel corner.\n\n---\n\n# 51. Important nuance about the mathematical seam edge\n\nThe physical raw sector may intentionally project across its **own** ideal mathematical seam line because the inter-panel seam solver positions two raw wedges around a separate spacer/key geometry.\n\nTherefore “clean triangle envelope” in this implementation specifically eliminates **longitudinal corner spill across the other edge at a node**.\n\nDo not incorrectly clip the entire sector to all three zero-thickness mathematical edge planes in a way that destroys the designed seam geometry.\n\nThe critical restrictions are:\n\n- receiving end terminates on the incoming adjacent edge plane;\n- butt end remains before the outgoing adjacent edge boundary;\n- the member’s own seam-face geometry remains controlled by the spacer solver.\n\nThis distinction prevents an overzealous clipping algorithm from breaking the inter-panel spline system.\n\n---\n\n# 52. Base edges\n\nThe 10 base perimeter A edges have only one adjacent dome face.\n\nThey do not receive an ordinary two-panel interior seam spacer unless an optional foundation/interface system is added.\n\nThis causes some physical edge offsets and jig recipes to differ from otherwise similar interior panels.\n\nThat is why the default model currently resolves to four jig variants rather than only two nominal triangle shapes.\n\n---\n\n# 53. Parametric trunk split count\n\nAlthough 8 radial splits is the default, the architecture should not depend permanently on 45°.\n\nGeneral sector angle:\n\n```text\nsector_angle = 360° / radial_splits\n```\n\nChanging the split count must regenerate:\n\n- sector cross section;\n- outer arc;\n- section area;\n- member radial faces;\n- seam offsets;\n- spacer gap;\n- hose limits;\n- butt-cut planes;\n- fabrication jigs;\n- mass/volume estimates.\n\n---\n\n# 54. Object IDs\n\nStable identifiers should be preserved.\n\nExamples:\n\n```text\nPANEL_001\nWOOD_P001_E0\nWOOD_P001_E1\nWOOD_P001_E2\nJOINT_P001_C0\nSEAM_A_001\nSPACER_SEAM_A_001\n```\n\nThe IDs are used by BOMs, cut schedules, jig plans, debug output, and future selection/inspection tools.\n\n---\n\n# 55. Primary data stored for every wood member\n\nA physical `MemberInfo` conceptually includes:\n\n```text\nmember ID\nowning panel\nlocal edge index\nA/B edge class\nideal edge key\nreceiving vertex\nbutt vertex\nnominal geodesic start/end\nmember tangent\npanel outward normal\npanel inward vector\npoint-axis seam offset\nnominal edge length\nreceives-member ID\nbutt-into-member ID\npinwheel handedness\nreceiving cut plane\nreceiving cut polygon\nreceiving axis setback/extension\nbutt plane\nbutt contact polygon\nbutt axis setback\nphysical point-axis length\nraw stock blank length\nvolume-equivalent length\n```\n\n---\n\n# 56. Primary data stored for every panel joint\n\nA `PanelJointInfo` records:\n\n```text\njoint ID\npanel index\nmathematical corner vertex\nvirtual vertex position\nterminating member\nreceiving member\nbutt/contact plane\ncontact polygon\nreceiving-axis setback\nreceiver clean vertex-trim plane\n```\n\nThis makes both fabrication cuts recoverable from the model instead of only existing inside rendered mesh vertices.\n\n---\n\n# 57. Geometry source-of-truth order\n\nThe software must resolve geometry in this order:\n\n```text\nstandard 2V topology\n        ↓\nmathematical vertices\n        ↓\noutward face normals\n        ↓\nconsistent exterior face winding\n        ↓\nA/B edge classification\n        ↓\nraw-sector cross section\n        ↓\ninter-panel seam/member offsets\n        ↓\npanel-local directed pinwheel cycle\n        ↓\nPANEL_INTERIOR_FACE planes\n        ↓\nbutt-contact planes/polygons\n        ↓\nclean vertex-envelope receiving planes/polygons\n        ↓\nphysical stock lengths and volume lengths\n        ↓\nspacers / hoses\n        ↓\nfabrication jig\n        ↓\nrendering / export / BOM\n```\n\nDo not work backward from a visual approximation.\n\n---\n\n# 58. Project architecture\n\nCurrent principal files:\n\n```text\napp.py\n    ModernGL/Pygame world, controls, visibility, exports, jig selection\n\ncamera.py\n    first-person walk/fly camera\n\nconfig.py\n    serializable parametric configuration\n\ngeometry.py\n    2V topology, wedge placement, seams, pinwheel joints,\n    clean vertex cuts, physical member lengths, validation\n\nmesh_builders.py\n    raw-sector meshes, spacers, hoses, debug lines,\n    fabrication jig geometry, OBJ mesh helper\n\nrenderer.py\n    ModernGL GPU resources, mesh/line shaders, transparent HUD overlay\n\nhud.py\n    in-world keyboard/status legend\n\nexporters.py\n    BOM, cut schedule, SVG jig plans, fabrication package,\n    reusable jig-variant grouping\n\nvalidate_geometry.py\n    text validation report\n\ntests/test_geometry.py\n    automated geometry/fabrication invariants\n\nMASTER_BUILD_SPEC.md\n    this document — the only authoritative Markdown file\n```\n\n---\n\n# 59. Generated fabrication files included with this package\n\nThe project contains a default generated fabrication package so geometry can be inspected without first launching ModernGL.\n\nIt can be regenerated at any time.\n\nFiles include:\n\n- full BOM;\n- all 240 end-cut records for 120 members;\n- 40 SVG panel-jig drawings;\n- reusable 3D jig fixture OBJ variants;\n- matching example wood OBJ variants;\n- panel-to-jig-variant mapping.\n\n---\n\n# 60. Running on Windows\n\nUse:\n\n```bat\nrun.bat\n```\n\nThe launcher creates/uses a Python virtual environment and installs the project requirements.\n\nMain dependencies:\n\n```text\nmoderngl\npygame\nnumpy\npytest\n```\n\nGeometry tests can be run with:\n\n```bat\nrun_tests.bat\n```\n\nor:\n\n```text\npython -m pytest -q\n```\n\n---\n\n# 61. Expected validation state for the default model\n\nThe corrected package should report approximately:\n\n```text\n26 mathematical vertices\n40 faces\n65 mathematical edges\n120 physical wood sectors\n120 cyclic pinwheel joints\n55 interior seams\n25 A seams\n30 B seams\nCLOCKWISE pinwheel viewed from exterior\nTRIANGLE_ENVELOPE vertex trim\n0.000 in maximum free receiving-axis overhang\n```\n\nNominal edges:\n\n```text\nA = 72.000000 in\nB = 63.670253 in\n```\n\nDefault stock blank ranges:\n\n```text\nA ≈ 69.984 .. 70.788 in\nB ≈ 61.552 .. 63.011 in\n```\n\n---\n\n# 62. Anti-misinterpretation block for another LLM\n\nCopy this section verbatim into another LLM’s implementation prompt if needed:\n\n> **DO NOT MODEL THESE PANELS AS CONVENTIONAL THREE-STRUT TRIANGLES. EACH PANEL OWNS THREE RAW CIRCULAR-SECTOR LOG MEMBERS. THE MEMBERS FORM A SAME-HANDED CYCLIC PINWHEEL: MEMBER 0 TERMINATES END-TO-SIDE INTO MEMBER 1, MEMBER 1 TERMINATES END-TO-SIDE INTO MEMBER 2, AND MEMBER 2 TERMINATES END-TO-SIDE INTO MEMBER 0. THE RAW SECTOR ORIENTATION IS A FOUR-STATE PARAMETER; DO NOT SILENTLY FORCE IT BACK TO CURVED-OUT / POINT-IN.**\n\n> **DO NOT GIVE THE RECEIVING MEMBER A FREE THROUGH-OVERHANG PAST THE DOME VERTEX. THAT EARLIER MODEL CAUSED THE WOODEN SPIKES AND NODE OVERLAPS VISIBLE IN THE REFERENCE SCREENSHOT. THE RECEIVING END MUST BE CUT BY THE PLANE OF THE INCOMING ADJACENT MATHEMATICAL TRIANGLE EDGE, EXTRUDED THROUGH THE PANEL NORMAL. THIS IS THE RED CLEAN-VERTEX CUT. IT ALLOWS THE PANEL TO TERMINATE CLEANLY AT THE GEODESIC CORNER WITHOUT INVADING A NEIGHBORING PANEL’S NODE REGION.**\n\n> **THE OTHER END OF EACH MEMBER IS A DIFFERENT CUT: THE GREEN CYCLIC BUTT CUT AGAINST THE NEXT MEMBER’S PANEL-INTERIOR RADIAL FACE. DO NOT REPLACE THESE TWO ASYMMETRIC CUTS WITH A 50/50 MITER.**\n\n> **NEIGHBORING TRIANGLES STILL DO NOT SHARE A WOODEN STRUT. EACH TRIANGLE OWNS ITS EDGE MEMBER, SO A SHARED DOME EDGE HAS TWO RAW WOOD MEMBERS WITH A SEPARATE SPLINE/KEY/HOSE/GASKET BETWEEN THEM. THE CLEAN VERTEX CUT FIXES THE NODE OVERLAP; IT DOES NOT CONVERT THE SYSTEM BACK INTO A NORMAL GEODESIC FRAME.**\n\n> **THE FABRICATION JIG MUST BE GENERATED FROM THE ACTUAL SOLVED PANEL GEOMETRY AND THE ACTIVE FOUR-STATE WEDGE ORIENTATION. IT MUST SHOW GRAY LOCATOR RAILS, RED CLEAN-VERTEX CUT GUIDES, GREEN PINWHEEL BUTT-CUT GUIDES, AND THE EXACT SOLVED RAW-SECTOR MEMBERS. DOME-OUT OR SIDEWAYS SECTORS MUST BE LIFTED/SUPPORTED SO THE ROTATED WOOD DOES NOT PASS THROUGH THE JIG BASE.**\n\n---\n\n# 63. Visual correctness tests\n\nA rendered panel is wrong if:\n\n- all three wooden members meet symmetrically at three neat mitered corners;\n- the pinwheel handedness randomly flips between faces;\n- the rendered point direction does not match the selected `wedge_orientation`;\n- changing `wedge_orientation` merely changes appearance without regenerating cuts/seams/jig geometry;\n- a receiving member projects as a free spike past a dome vertex;\n- several panels form a starburst of overlapping wood at a node;\n- the red clean vertex cut is absent from debug mode;\n- the green butt-contact cut is replaced by a square end;\n- the two panel-owned edge members are collapsed into one shared strut;\n- the spacer is removed merely to make the conventional frame easier to draw.\n\nA rendered panel is conceptually correct when:\n\n- its three members form one chasing cyclic end-to-side sequence;\n- the raw sector orientation exactly matches the selected one of the four cardinal states;\n- its receiving ends are clipped cleanly by adjacent ideal-edge planes;\n- no arbitrary through spike remains at a mathematical dome vertex;\n- its butt ends land on the next member’s panel-interior radial face;\n- the panel remains physically independent from its neighbors;\n- a separate seam connector occupies the inter-panel joint.\n\n---\n\n# 64. Fabrication correctness tests\n\nA fabrication output is wrong if it says simply:\n\n```text\n60 pieces at 72 inches\n60 pieces at 63.67 inches\n```\n\nwithout distinguishing the real end-cut blank requirements.\n\nA fabrication output must preserve:\n\n- nominal geodesic class;\n- exact physical blank length;\n- receiving clean-cut plane;\n- butt compound-cut plane;\n- mating member IDs;\n- panel ownership;\n- handedness;\n- reusable jig variant.\n\n---\n\n# 65. What “comes cleanly to a point” means in this project\n\nThe phrase does **not** mean forcing all physical wood centerlines to end at one infinitesimal point.\n\nThe raw sector has finite width and depth.\n\nInstead, “cleanly to a point” means:\n\n- the mathematical geodesic vertex remains the apex reference;\n- the receiving member is sliced by the adjacent face-edge boundary passing through that apex;\n- no arbitrary part of the receiving member continues past that boundary;\n- the panel’s visible corner converges toward the intended node rather than producing a protruding tongue;\n- adjacent panels therefore arrive at the common node as separately bounded panel corners rather than mutually intersecting spikes.\n\nThis is a **solid-geometry boundary condition**, not merely a centerline shortening operation.\n\n---\n\n# 66. Engineering disclaimer\n\nThis project provides geometry, fabrication visualization, cut-plane calculations, and a repeatability-jig concept.\n\nIt does not certify:\n\n- structural capacity;\n- allowable wood stress;\n- connection strength;\n- fastener count;\n- bolt shear;\n- splitting resistance;\n- buckling;\n- foundation loads;\n- wind uplift;\n- snow loads;\n- building-code compliance;\n- rubber creep;\n- weather sealing;\n- fire resistance;\n- long-term wood shrinkage.\n\nThose are separate engineering tasks.\n\n---\n\n# 67. Final immutable design statement\n\nThe defining paradigm of this project is:\n\n```text\nRAW UNSQUARED RADIAL LOG SECTOR\n        +\nFOUR-STATE RAW-SECTOR AXIAL ORIENTATION\n(POINT_DOME_IN / POINT_PANEL_IN / POINT_DOME_OUT / POINT_PANEL_OUT)\n        +\nCYCLIC PINWHEEL END-TO-SIDE PANEL CORNERS\n        +\nRED TRIANGLE-ENVELOPE CLEAN VERTEX CUTS\n        +\n40 INDEPENDENT TRIANGULAR PANELS\n        +\n120 PHYSICAL WOOD MEMBERS\n        +\nDUPLICATED PANEL EDGES\n        +\n55 INTER-PANEL SPLINES / HOSES / GASKETS\n        +\nMULTI-WAY DOME NODE SYSTEM\n        +\nEXACT PARAMETRIC FABRICATION JIGS\n```\n\nIt is **not** conventional shared-strut geodesic construction.\n\nIt is **not** dimensional-lumber framing.\n\nIt is **not** a symmetric mitered triangle.\n\nIt is **not** a free-overhang pinwheel whose ends collide at the dome vertices.\n\nThe current authoritative physical corner is a **vertex-clean cyclic pinwheel**.\n\n\n# ORIENTATION ANALYSIS / EXPLODED-PANEL REVISION\n\nThe renderer includes an analysis-only panel explosion system specifically so the four raw-sector orientations can be understood without neighboring triangle frames hiding the colored radial faces. This is NOT fabrication geometry and MUST NOT alter stock lengths, cut planes, pinwheel contacts, seam solutions, or exports.\n\n## Wedge color language\n\nEvery raw sector carries colors with the physical wood as it rotates around the strut axis:\n\n- RED = one local radial-sawn face (sector boundary at the negative local sector angle / seam-side in the legacy POINT_DOME_IN state).\n- GREEN = the opposite local radial-sawn face (positive local sector angle / panel-side in the legacy POINT_DOME_IN state).\n- YELLOW = the sharp sector-point/apex ridge.\n- BROWN = the curved former-bark / fat back surface.\n\nFor POINT_DOME_IN, an observer standing inside the dome and looking outward toward a strut should conceptually have the YELLOW point nearest the observer and the BROWN curved bark-side farthest away toward the sky. RED and GREEN are the two radial faces meeting at that yellow point. Whether red appears screen-left or screen-right depends on which end of a directed strut the camera is viewing from; the colors identify physical sector faces, not absolute screen directions.\n\n## Four cardinal sector rotations\n\nU cycles the point direction around the strut axis in 90-degree increments:\n\n1. POINT_DOME_IN: yellow point toward sphere center, brown bark toward sky. The pair of duplicated edge sectors creates an inside-opening V/channel.\n2. POINT_PANEL_IN: yellow point sideways toward the center of its triangular panel. No simple inside/outside radial V-channel.\n3. POINT_DOME_OUT: yellow point toward sky, brown bark toward sphere center. The pair creates an outside-opening V/channel.\n4. POINT_PANEL_OUT: yellow point sideways across the panel edge/seam. No simple inside/outside radial V-channel; this state may use tangent contact to the curved face for pinwheel receiving geometry.\n\n## Rigid panel explosion\n\nZ decreases and X increases `panel_explode_in` in 2-inch increments. C resets it to zero. Each COMPLETE solved triangular frame translates rigidly along its own outward face normal. The three members, cyclic cuts, member orientation, and internal panel relationships do not change. The operation exists only to open visual space between adjacent panels.\n\nBecause the A and B seam folds differ, a single panel-normal explosion distance does not create exactly the same physical opening on every seam. For an explosion distance `e` and local face-fold angle `F`, the distance between corresponding translated seam points is:\n\n`opening = 2 * e * sin(F / 2)`\n\nThe HUD reports the resulting A-seam and B-seam openings live. Connectors and node markers automatically hide while exploded so the original assembled spline geometry does not mask the raw wedge faces.\n\n## Solo triangle analysis\n\nQ toggles SOLO PANEL mode. The current analysis panel is the same panel selected with Y / Shift+Y for the fabrication jig. In SOLO mode only the three physical raw-sector members of that panel are rendered. Their actual cyclic pinwheel end cuts and current wedge orientation remain intact. This mode is intended for standing inside/outside the virtual triangle, orbiting/walking around it, and determining exactly which colored sector surface faces the dome interior, exterior, panel center, and seam.\n\n## Export invariant\n\nPanel explosion is strictly visual. OBJ, BOM, configuration-for-fabrication, and fabrication-package export must force `panel_explode_in = 0.0` so an analysis view can never accidentally become an exploded fabrication model.\n"
REFERENCE_PINWHEEL_TRIANGLE_PNG_B64 = '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UE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFBOAQQAAABQTgEEAAAAUE4BBAAAAFDu/wEoQ0uYd3DjrwAAAABJRU5ErkJggg=='
REFERENCE_VERTEX_CUT_SCREENSHOT_PNG_B64 = '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YvSdo5g/dy4AefllARB3d3f27N5NSUkJAQ0aMHrMGNw9PPD08uK++x/AzcOdlJTTxMcfsda7edMmAAZGDGJA+Zz9O7Zvt+aLSM2SW75m0NChw/D09OTE8ePs3buHtu3a0atXLwDy8/OrPJYAlJaWkJR4kn/98x8APP3b3+LuUTZ2XS13Dw+Cunbl/6a/AMCauFgyz50zFhOR6+xm7Yth4eFYLBYWLYymuKjImC0iIiIiIiIi16DaAiAeF54AKSpbeLSigvI1QNzc3DiXns4H770LwMOPPsbipV/zxZKvGD12LEWFhbw2a5bNBYKEhAQyzp3Dz8+fxk2a8MvBg6SlplrzK7rU4pwjRo4yFhORm1h+eQCkQ6dObNmymaLCQpISE8nKyiKkX7+yMvn5VR5LKtq1cycH9u2jlq8vY8aONWZTz8/vorHk5VdmXbLM4qVf85e//Z16fn4cPnyYt/77X5tyInL1zJzXzfTFJ576DStiYlmwcJE17ZtvV7AiJpa7x4+3ptmbg6Mj4yeULX6+du1aY/Z1U9X9NTPmYfL7EBEREREREalO1RYAcfcoC4AUFV4cACksT7twp/XiL75g5ssvsXvXLvJycjmXnk7M6lU89sgj/PLzzzbvLSkuJjYmxvr3hSmxRKRmKihfMwhgy+bNUD4OfP/9RgCKi4ut40xVxhIbpaW8Vx48mTR5CvX8/IwlTMs4d45tW7fy97/+hT/89mmyL7Eou4hcfzdjX+zQoQMBDRqwNi6OjGpYo0NERERERETkduPg7lnrqlb4nTD5XqLnzzMmi4iIiIgJf5w+nQEDB/G7p3/DwQMHjNki192EyVOInl82Ja2IiIiIiEhNVG1PgIiIiIhIGd/atRkwcBBJSYn8cvCgMVtERERERERE7EABEBEREZFqdi49najBkTw4bRqlJSXGbBERERERERGxAwVARERERERERERERESkxlEAREREREREREREREREahwFQEREREREREREREREpMZRAERERERERERERERERGocBUBERERERERERERERKTGUQBERERERERERERERERqHAVARERERERERERERESkxlEAREREREREREREREREahwFQEREREREREREREREpMZRAERERERERERERERERGocBUBERERERERERERERKTGUQBERERERERERERERERqHAVARERE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bdi7dy+lJSXWslfi4urK+IkTWbr0K+vc4VfDzEK0iYmJ5OTkMHToMIYNH07k4MEMiihbxPXCRevjx0/Qo1dPhkUNp127dpw8eRIoJS01zXr3a0JCAq1at+aOO++ieYsWrFq5Ag9PTzIyMqp8h+zN5sIi6Mu++ZqMc79O8dO0WTN69epdoxZB79Chw0ULcldkpj85ODowfPgIOncJIiw8nEERkbTv2JGMc+esixubqcdebao6+5OZcSKsf38efvRRBkVEEBoaRpMmTVm1coVNGTP90oybbd/N1GOvfb9eatepw7Co4aSePcv+ffuM2ZVyc3dn+gt/4t//foPzhimgrkbPXr1o1bo1Gzes53RysjG7ygoLCjiZmEj//v2JihpO5JAhFBUVWX+jmBknUlJSaNioIaPuuJPOXbqwY/t2crKzyc3NtVkEvbK2YK9zqpmxxMyYVNm50NvHh67BwWxYvx4PDw/6hISwds0aXF1d6RcayvrvvqO4qMh0G6/suzBTj5nvq7ppEXQREREREanpHNw9a13VhNcTJt9L9Px5xmSRGqdLcDDdu/fgw/ffM2aJ3NRc3dx45tnn+PLLLzhYHhx2cHSkV+/eRA0fzqyZM01Ph2Qvt3N/up33/XrxqVWL6C++5O9//StxMauN2ZUaGBHB0GFRPP/cs8YskdvChMlTiJ4/15gsIiIiIiJSY1TbFFgityQHB8LCwvn++43GHJGbnqubG+4e7nh6eODk7Fw+978HDRs25HRycrUHP27r/nQ77/t14ubuzl2jx3AuPZ3Nm34wZlfOwYHx4yewaOFCY46IiIiIiIiI1BB6AkREpAZr2749/fqF0qhxYywWC+cyznFg3342rF9Pbk7ZYtkitxqfWrV49/0P2LB+PZ/Nn0d6+XRuIlI1egJERERERERqOgVARERERERuQwqAiIiIiIhITacpsEREREREREREREREpMZRAERERERERERERERERGocBUBERERERERERERERKTGUQBERERERERERERERERqHAVARERERERERERERESkxlEAREREREREREREREREahwFQEREREREREREREREpMaxOLu4zTAmmhEY1IV9e3Ybk8UkR4uFjz6dy6HDhziTkmLMlpuYg6Mjf3j2WU4lJ3MuPd2YfctxtFjoGxrG6DFjiBoxgojBg9m9axe5OTnGonID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C5EmJiaSk5PD0KHDGDZ8OJGDBzMoomxR5EtdALkcF1dXxk+cyNKlX1mfwrkaYf378/CjjzIoIoLQ0DCaNGnKqpUrLtqvwoICTiYm0r9/f6KihhM5ZAhFRUXWNlnfz48OHTrYLIZrdPz4CXr06smwqOG0a9eOkydPAqWkpaZddGd/9549OZ2cTOLJkzbp2PEY2tuDDz/C7L/8heEjRwIwfuJEpkydyrFjR696Qd6bTdSIEUy7/376DxgAQM+ePRkUEYGzs4s1SJuQkECr1q254867aN6iBatWrsDD05OMjAzr92zmOzTTXsx8HjMcHB0YPnwEnbsEERYezqCISNqXP8V2YeFiM5+5snHC7HhjZlvYqV9SPo6XlEJYWBhLFn95TRfd5drZ49x8vVTnOSMlJYWGjRoy6o476dylCzu2bycnO5vc3FxOHD9uLVfZtswwM5aY6ZeVLdyOyfEGE/tlZlu3Ki2CLiIiIiIiNZ2Du2etq5rwesLke4meP8+YLJcxMCKCocOieP65Z41ZcpPrEhxM9+49+PD994xZIlIFrm5uPPPsc3z55RccPHAAyqfa6dW7N1HDhzNr5kzT01fdyiIGD6FevbpEL1hgzJJqpnNzzaXxxpwJk6cQPX+uMVlERERERKTGqLYpsG5rDg6MHz+BRQsXGnPkZufgQFhYON9/v9GYIyJV5OrmhruHO54eHjg5O5evM+BBw4YNOZ2cXOMvRjpaLAQGBdEnJIQVKy6eblCqmc7NNdrtPt6IiIiIiIhIGT0BIiIi1aZt+/b06xdKo8aNsVgsnMs4x4F9+9mwfj25OWWLm9dEvUNCiIiM5MTx46xcsYIzKSnGIiJiZ7freFMVegJERERERERqOgVARERERERuQwqAiIiIiIhITacpsEREREREREREREREpMZRAERERERERERERERERGocBUBERERERERERERERKTGUQBERERERERERERERERqHAVARERERERERERERESkxlEAREREREREREREREREahwFQEREREREREREREREpMa56QIgz7/wApOmTDEmX1JIv34sWLiIJk2bGbOsLE5OjLn7bt55732WrVzFiphYAho0NBaTGqxjYCDPv/ACfgEBxiyR29LjTz5Jj169jcm3lLD+/bl32jRjsoiIiIiIiIiIiFW1BkAcLRbCBwzg3/+dw9Jly1kR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nClTpzJl6lQGDx5MfT9/5sz5j83i5qHh4WRkZLB39691D4qI5NSpJH4+cACABx9+hNl/+QsTJ90DwPCRI5kydSrOzs7s3LHD+j6AYVFRxMfHc+iXX2zSL8jPy+Pnnw8wcdI9PPrY40y7/wHy8/PYv2+fsajYQVj//jz86KMMioggNDSMJk2asmrlCpvvJ7BzZwI7BxEW3p/effrg4+PD4sVfkpT46wLm9f386NChAxvWr7emGUWNGMG0+++n/4ABAPTs2ZNBERE4O7tw5PBhKN9WTk4OCfHx1vd1DQ4mLS2NE8ePW9MKCwo4mZhI//79iYoaTuSQIRQVFXH82K29+OmtyGKxMGnyZL7+6iuysjIBSEpK4snfPE3GuXMsX/aN8S23JDNt8/Dhw3h4eDBkyFAGRUbg7x/Aim+X2/SnhIQEWrVuzR133kXzFi1YtXIFHp6eZGRkWO9gTkxMJCcnh6FDhzFs+HAiBw9mUEQEZ86cIeW0uSevvH186BoczIb16/Hw8KBPSAhr16zB1dWVfqGhrP/uO4qLijh+/AQ9evVkWNRw2rVrx8mTJ4FS0lLTrJ/HTP9u1rw5vr6+7N61i5KSEn7++Wf69O5D6zZt2Lt3L6UlJab2y8y2zIxbUr269+yJs7Mzmzf9AEBJSQmlpaVMvvdevl2+nJIrTK90qzDTNs20cTPt10w92OlcmJuby4EDB+jcuTODBw8hasQIBkVEEB8fT8a5sin9KhsnzI43ZvbLzHGu7PPcygKDgqr0e15ERERERORW4+DuWatsPoMqmjD5XqLnzzMmi1yzCZMmcebMGdbExhqzRERERMROJkyeQvT8ucZkERERERGRGuOGTYElIiIiIiIiIiIiIiJyvSgAIiIiIiIiIiIiIiIiNY4CIHLTiV6wQNNfiYiIiIiIiIiIiMg1UQBERERERERERERERERqHAVARERERERERERERESkxlEAREREREREREREREREahwFQEREREREREREREREpMZRAERERERERERERERERGocBUBERERERERERERERKTGUQBE5BbXvWcvOnbqZEyuVgMjImjStJkxWUREREREREREROSGsTi7uM0wJpoRGNSFfXt2G5NrPEeLhY8+ncuhw4c4k5JizJZbVMfAQB58+GF+OXSI7PPnjdl20aZtO37/zDMMiohgUEQEBw8eJCsz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'


def generate_fabrication_package_standalone() -> None:
    """Reproduce the former generate_fabrication_package.py utility from this one file."""
    root = Path(__file__).resolve().parent
    config_path = root / "dome_config.json"
    config = DomeConfig.load(config_path) if config_path.exists() else DomeConfig()
    model = build_physical_model(config)
    output = root / "fabrication_package"
    export_fabrication_package(model, output)
    print(f"Generated fabrication package: {output}")


def extract_embedded_resources() -> None:
    """Write the original master spec and visual references beside this single file."""
    root = Path(__file__).resolve().parent
    (root / "MASTER_BUILD_SPEC.md").write_text(MASTER_BUILD_SPEC_MD, encoding="utf-8")
    (root / "reference_pinwheel_triangle.png").write_bytes(base64.b64decode(REFERENCE_PINWHEEL_TRIANGLE_PNG_B64))
    (root / "reference_vertex_cut_screenshot.png").write_bytes(base64.b64decode(REFERENCE_VERTEX_CUT_SCREENSHOT_PNG_B64))
    print(f"Extracted embedded resources to: {root}")


def _single_file_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Single-file Raw Wedge 2V geodesic dome simulator / fabrication tool."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--validate", action="store_true", help="Run all four-orientation geometry validation and exit.")
    group.add_argument("--fabrication", action="store_true", help="Generate the fabrication package headlessly and exit.")
    group.add_argument("--extract-resources", action="store_true", help="Extract embedded master spec/reference images and exit.")
    args = parser.parse_args()

    if args.validate:
        run_geometry_validation()
        return
    if args.fabrication:
        generate_fabrication_package_standalone()
        return
    if args.extract_resources:
        extract_embedded_resources()
        return

    ensure_graphics_dependencies()
    run_interactive_app()


if __name__ == "__main__":
    _single_file_cli()
