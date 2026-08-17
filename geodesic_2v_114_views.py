"""
2V Geodesic Dome Multi-Projection Viewer
========================================

Exact strut targets:
    Short strut A = 63 5/8 in = 63.625 in
    Long  strut B = 72.000 in

The program builds a frequency-2 geodesic hemisphere with the normal 2V
connectivity, then solves the rotationally symmetric ring coordinates so every
short edge is exactly A and every long edge is exactly B. This means the model
honors the supplied physical strut lengths rather than forcing all vertices to
lie on one mathematically perfect sphere.

Views shown:
    1. Side orthographic elevation
    2. Perspective projection
    3. Cabinet oblique projection
    4. Side wireframe projection (all struts; no hidden-line removal)
    5. Top orthographic plan
    6. Front orthographic elevation

Controls:
    0           Multi-view 2x3 layout
    1..6        Show one view full-window
    Left drag   Rotate the perspective/oblique viewing orientation
    Wheel       Zoom
    F           Toggle translucent triangular faces
    H           Toggle hidden-line/depth testing for applicable views
    G           Toggle ground/base reference grid
    S           Save PNG screenshot beside this script
    R           Reset rotation and zoom
    ESC         Quit

Dependencies:
    pip install pygame moderngl numpy
"""

from __future__ import annotations

import itertools
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import moderngl
import numpy as np
import pygame


# -----------------------------------------------------------------------------
# Physical specification
# -----------------------------------------------------------------------------
SHORT_STRUT_IN = 63.625  # 63 5/8 in
LONG_STRUT_IN = 72.0

WINDOW_W = 1600
WINDOW_H = 1000
WINDOW_TITLE = "2V Geodesic Dome - Orthographic / Perspective / Oblique Views"


# -----------------------------------------------------------------------------
# Small linear-algebra helpers.  Everything is kept in numpy so no PyGLM is
# required.
# -----------------------------------------------------------------------------
def normalize(v: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(v))
    if length <= 1e-12:
        return v.copy()
    return v / length


def perspective_matrix(fovy_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fovy_deg) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / max(aspect, 1e-8)
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def ortho_matrix(left: float, right: float, bottom: float, top: float,
                 near: float = -5000.0, far: float = 5000.0) -> np.ndarray:
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = 2.0 / (right - left)
    m[1, 1] = 2.0 / (top - bottom)
    m[2, 2] = -2.0 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    return m


def look_at(eye: Sequence[float], target: Sequence[float], up: Sequence[float]) -> np.ndarray:
    eye_v = np.asarray(eye, dtype=np.float64)
    target_v = np.asarray(target, dtype=np.float64)
    up_v = np.asarray(up, dtype=np.float64)

    fwd = normalize(target_v - eye_v)
    side = normalize(np.cross(fwd, up_v))
    true_up = np.cross(side, fwd)

    m = np.eye(4, dtype=np.float32)
    m[0, :3] = side
    m[1, :3] = true_up
    m[2, :3] = -fwd
    m[0, 3] = -float(np.dot(side, eye_v))
    m[1, 3] = -float(np.dot(true_up, eye_v))
    m[2, 3] = float(np.dot(fwd, eye_v))
    return m


def rotation_z(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array(
        [[c, -s, 0.0, 0.0],
         [s,  c, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=np.float32,
    )


def rotation_x(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, c, -s, 0.0],
         [0.0, s,  c, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=np.float32,
    )


def rotation_y(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array(
        [[ c, 0.0, s, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [-s, 0.0, c, 0.0],
         [0.0, 0.0, 0.0, 1.0]],
        dtype=np.float32,
    )


def cabinet_oblique_matrix(depth_scale: float = 0.5, angle_deg: float = 45.0) -> np.ndarray:
    """Shear depth (Y) into screen X/Z for a standard cabinet-style oblique view."""
    a = math.radians(angle_deg)
    m = np.eye(4, dtype=np.float32)
    # World coordinates are X/Y horizontal, Z vertical.  Looking along +Y,
    # this shear makes Y remain visible in the 2D result.
    m[0, 1] = depth_scale * math.cos(a)
    m[2, 1] = depth_scale * math.sin(a)
    return m


def matrix_bytes(m: np.ndarray) -> bytes:
    """ModernGL expects column-major matrix memory for GLSL mat4 uniforms."""
    return np.asarray(m, dtype=np.float32).T.tobytes()


# -----------------------------------------------------------------------------
# Dome topology and exact geometry
# -----------------------------------------------------------------------------
@dataclass
class DomeGeometry:
    vertices: np.ndarray              # shape (N, 3), inches
    faces: np.ndarray                 # shape (F, 3), vertex indices
    short_edges: List[Tuple[int, int]]
    long_edges: List[Tuple[int, int]]
    all_edges: List[Tuple[int, int]]
    base_vertices: List[int]
    base_radius: float
    height: float
    short_length: float
    long_length: float


class DomeBuilder:
    """Build the standard 2V hemisphere topology, then fit exact A/B strut lengths."""

    def __init__(self, short_length: float, long_length: float):
        self.a = float(short_length)
        self.b = float(long_length)

    @staticmethod
    def _icosahedron() -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        phi = (1.0 + math.sqrt(5.0)) * 0.5

        raw = []
        for a in (-1.0, 1.0):
            for b in (-phi, phi):
                raw.extend(((0.0, a, b), (a, b, 0.0), (b, 0.0, a)))

        # The generation above can produce no duplicates mathematically, but
        # de-duplicate explicitly to keep the construction robust.
        unique: List[Tuple[float, float, float]] = []
        for v in raw:
            if v not in unique:
                unique.append(v)

        vertices = np.asarray(unique, dtype=np.float64)
        vertices /= np.linalg.norm(vertices[0])

        distances = np.linalg.norm(vertices[:, None, :] - vertices[None, :, :], axis=2)
        nonzero = distances[distances > 1e-12]
        edge_length = float(nonzero.min())

        edges = {
            (i, j)
            for i in range(len(vertices))
            for j in range(i + 1, len(vertices))
            if abs(float(distances[i, j]) - edge_length) < 1e-8
        }

        faces: List[Tuple[int, int, int]] = []
        for tri in itertools.combinations(range(len(vertices)), 3):
            if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(tri, 2)):
                faces.append(tri)

        return vertices, faces

    @staticmethod
    def _rotation_from_to(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        a = normalize(np.asarray(a, dtype=np.float64))
        b = normalize(np.asarray(b, dtype=np.float64))
        v = np.cross(a, b)
        c = float(np.dot(a, b))
        s = float(np.linalg.norm(v))

        if s < 1e-12:
            if c > 0.0:
                return np.eye(3, dtype=np.float64)
            # 180-degree rotation around any axis perpendicular to a.
            axis = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            if abs(float(np.dot(axis, a))) > 0.9:
                axis = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            axis = normalize(axis - float(np.dot(axis, a)) * a)
            k = np.array(
                [[0.0, -axis[2], axis[1]],
                 [axis[2], 0.0, -axis[0]],
                 [-axis[1], axis[0], 0.0]],
                dtype=np.float64,
            )
            return np.eye(3) + 2.0 * (k @ k)

        k = np.array(
            [[0.0, -v[2], v[1]],
             [v[2], 0.0, -v[0]],
             [-v[1], v[0], 0.0]],
            dtype=np.float64,
        )
        return np.eye(3) + k + (k @ k) * ((1.0 - c) / (s * s))

    @staticmethod
    def _subdivide_frequency_2(
        vertices: np.ndarray,
        faces: Sequence[Tuple[int, int, int]],
    ) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
        points = [v.copy() for v in vertices]
        midpoint_cache: Dict[Tuple[int, int], int] = {}
        new_faces: List[Tuple[int, int, int]] = []

        def midpoint(i: int, j: int) -> int:
            key = tuple(sorted((i, j)))
            if key in midpoint_cache:
                return midpoint_cache[key]
            p = normalize((points[i] + points[j]) * 0.5)
            idx = len(points)
            points.append(p)
            midpoint_cache[key] = idx
            return idx

        for a, b, c in faces:
            ab = midpoint(a, b)
            bc = midpoint(b, c)
            ca = midpoint(c, a)
            new_faces.extend(
                ((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca))
            )

        return np.asarray(points, dtype=np.float64), new_faces

    @staticmethod
    def _unique_edges(faces: Iterable[Tuple[int, int, int]]) -> List[Tuple[int, int]]:
        edges = set()
        for tri in faces:
            for i, j in itertools.combinations(tri, 2):
                edges.add(tuple(sorted((i, j))))
        return sorted(edges)

    def _solve_ring_geometry(self) -> Tuple[List[float], List[float]]:
        """
        Solve the symmetric ring geometry with only numpy.

        Ring numbering, top to bottom:
            0: apex, 1 vertex
            1: 5 vertices
            2: 5 vertices
            3: 5 vertices
            4: base, 10 vertices

        There are eight symmetry-distinct edge equations and eight useful ring
        dimensions.  Two radii are available directly from regular polygons;
        the remaining six quantities are solved with Newton iteration.
        """
        A = self.a
        B = self.b

        # Ring 1 is a regular pentagon whose side is B.
        r1 = B / (2.0 * math.sin(math.radians(36.0)))

        # Ring 4 is the regular decagonal base whose side is B.
        r4 = B / (2.0 * math.sin(math.radians(18.0)))

        # Initial guess from a mathematically ideal spherical 2V dome scaled to B.
        ideal_long_chord = 0.6180339887498948
        scale = B / ideal_long_chord
        x = np.array(
            [
                0.85065080835204 * scale,   # r2
                0.525731112119134 * scale,  # z2
                0.894427190999916 * scale,  # r3
                0.447213595499958 * scale,  # z3
                0.85065080835204 * scale,   # z1
                1.0 * scale,                # apex height H
            ],
            dtype=np.float64,
        )

        def d(r_a: float, z_a: float, r_b: float, z_b: float, delta_deg: float) -> float:
            delta = math.radians(delta_deg)
            return math.sqrt(
                r_a * r_a + r_b * r_b
                - 2.0 * r_a * r_b * math.cos(delta)
                + (z_a - z_b) ** 2
            )

        def residual(v: np.ndarray) -> np.ndarray:
            r2, z2, r3, z3, z1, H = map(float, v)
            return np.array(
                [
                    math.sqrt(r1 * r1 + (H - z1) ** 2) - A,
                    d(r1, z1, r2, z2, 36.0) - B,
                    d(r1, z1, r3, z3, 0.0) - A,
                    d(r2, z2, r3, z3, 36.0) - A,
                    d(r2, z2, r4, 0.0, 18.0) - B,
                    d(r3, z3, r4, 0.0, 18.0) - A,
                ],
                dtype=np.float64,
            )

        # Six unknowns, six equations.  Finite-difference Jacobian keeps the
        # script dependency-free beyond numpy.
        for _ in range(50):
            f = residual(x)
            if float(np.max(np.abs(f))) < 1e-11:
                break

            jac = np.zeros((6, 6), dtype=np.float64)
            for col in range(6):
                step = max(1e-6, abs(float(x[col])) * 1e-7)
                xp = x.copy()
                xm = x.copy()
                xp[col] += step
                xm[col] -= step
                jac[:, col] = (residual(xp) - residual(xm)) / (2.0 * step)

            try:
                delta = np.linalg.solve(jac, -f)
            except np.linalg.LinAlgError as exc:
                raise RuntimeError("Could not solve exact 2V ring geometry.") from exc

            x += delta

            if float(np.linalg.norm(delta)) < 1e-12:
                break
        else:
            raise RuntimeError("Exact 2V ring solver failed to converge.")

        if float(np.max(np.abs(residual(x)))) > 1e-7:
            raise RuntimeError("Exact 2V ring solver converged poorly.")

        r2, z2, r3, z3, z1, H = map(float, x)
        radii = [0.0, r1, r2, r3, r4]
        heights = [H, z1, z2, z3, 0.0]
        return radii, heights

    def build(self) -> DomeGeometry:
        base_vertices, base_faces = self._icosahedron()

        # Rotate one original icosahedron vertex to the north pole.  In this
        # orientation the frequency-2 subdivision produces a clean z=0 decagon.
        rot = self._rotation_from_to(base_vertices[0], np.array([0.0, 0.0, 1.0]))
        base_vertices = (rot @ base_vertices.T).T

        unit_vertices, subdivided_faces = self._subdivide_frequency_2(base_vertices, base_faces)

        # Keep exactly the upper hemisphere.  At frequency 2, the cut passes
        # through ten subdivision vertices, giving the familiar decagonal base.
        dome_faces_old = [
            tri for tri in subdivided_faces
            if min(float(unit_vertices[i, 2]) for i in tri) >= -1e-9
        ]

        used_old = sorted({idx for tri in dome_faces_old for idx in tri})
        old_to_new = {old: new for new, old in enumerate(used_old)}
        vertices_unit = unit_vertices[used_old].copy()
        faces = np.asarray(
            [tuple(old_to_new[i] for i in tri) for tri in dome_faces_old],
            dtype=np.int32,
        )

        edges = self._unique_edges([tuple(map(int, tri)) for tri in faces])
        unit_edge_lengths = np.array(
            [np.linalg.norm(vertices_unit[i] - vertices_unit[j]) for i, j in edges],
            dtype=np.float64,
        )

        # Standard ideal 2V edge classes on the unit sphere.
        ideal_short = 0.5465330578253432
        ideal_long = 0.6180339887498948
        short_edges: List[Tuple[int, int]] = []
        long_edges: List[Tuple[int, int]] = []
        for edge, length in zip(edges, unit_edge_lengths):
            if abs(float(length) - ideal_short) < abs(float(length) - ideal_long):
                short_edges.append(edge)
            else:
                long_edges.append(edge)

        # Determine each vertex's symmetry ring from its unit-sphere Z level.
        z_levels = sorted(
            {round(float(v[2]), 9) for v in vertices_unit},
            reverse=True,
        )
        if len(z_levels) != 5:
            raise RuntimeError(f"Expected 5 dome rings, got {len(z_levels)}: {z_levels}")

        radii, heights = self._solve_ring_geometry()

        vertices_exact = np.zeros_like(vertices_unit)
        base_vertex_indices: List[int] = []

        for idx, v in enumerate(vertices_unit):
            z_key = round(float(v[2]), 9)
            ring = z_levels.index(z_key)

            if ring == 0:
                vertices_exact[idx] = (0.0, 0.0, heights[0])
            else:
                angle = math.atan2(float(v[1]), float(v[0]))
                radius = radii[ring]
                vertices_exact[idx] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    heights[ring],
                )
                if ring == 4:
                    base_vertex_indices.append(idx)

        # Validate every physical strut to engineering precision.
        short_actual = [
            float(np.linalg.norm(vertices_exact[i] - vertices_exact[j]))
            for i, j in short_edges
        ]
        long_actual = [
            float(np.linalg.norm(vertices_exact[i] - vertices_exact[j]))
            for i, j in long_edges
        ]

        max_short_error = max(abs(v - self.a) for v in short_actual)
        max_long_error = max(abs(v - self.b) for v in long_actual)
        if max(max_short_error, max_long_error) > 1e-6:
            raise RuntimeError(
                f"Strut validation failed: A error={max_short_error}, B error={max_long_error}"
            )

        # Sort the ten base vertices by polar angle, useful for reference drawing.
        base_vertex_indices.sort(
            key=lambda i: math.atan2(float(vertices_exact[i, 1]), float(vertices_exact[i, 0]))
        )

        return DomeGeometry(
            vertices=vertices_exact.astype(np.float32),
            faces=faces,
            short_edges=short_edges,
            long_edges=long_edges,
            all_edges=edges,
            base_vertices=base_vertex_indices,
            base_radius=float(radii[4]),
            height=float(heights[0]),
            short_length=self.a,
            long_length=self.b,
        )


# -----------------------------------------------------------------------------
# 114-view catalog renderer
# -----------------------------------------------------------------------------
VIEW_NAMES = [
    'Zero-Point Perspective','One-Point Perspective','Two-Point Perspective','Three-Point Perspective','Four-Point Perspective','Five-Point Perspective','Six-Point Perspective',
    'Curvilinear Perspective','Cylindrical Perspective','Spherical Perspective','Fisheye Perspective','Panoramic Perspective','Equirectangular Perspective','Mercator-Like Perspective',
    'Orthographic Projection','Front Orthographic View','Rear Orthographic View','Left-Side Orthographic View','Right-Side Orthographic View','Top Orthographic View','Bottom Orthographic View','Plan View','Elevation View','Section View','Cross-Section View','Longitudinal Section','Transverse Section',
    'Axonometric Projection','Isometric Projection','Dimetric Projection','Trimetric Projection','Military Projection','Plan Oblique / Axonometric Plan',
    'Oblique Projection','Cavalier Projection','Cabinet Projection','General Oblique Projection',
    'Eye-Level View','High-Angle View','Low-Angle View',"Bird's-Eye View",'Aerial View',"God's-Eye View", "Worm's-Eye View",'Ground-Level View','Top-Down View','Bottom-Up View','Overhead View','Three-Quarter View','Front Three-Quarter View','Rear Three-Quarter View','Profile View','Front View','Rear View','Dutch Angle / Canted View','Over-the-Shoulder View','POV / First-Person Perspective','Third-Person View',
    'Exploded View','Cutaway View','Transparent / Ghosted View','Wireframe View','Hidden-Line View','Silhouette View','Contour View','Sectional Perspective','Sectional Axonometric','Exploded Axonometric','Exploded Isometric',
    'Turnaround View','Front / Side / Back Model Sheet','Three-Quarter Turnaround','Eight-Point Turnaround','Twelve-Point Turnaround','Orthographic Turnaround','Perspective Turnaround',
    'Forced Perspective','Reverse Perspective','Inverse Perspective','Multiple Perspective','Composite Perspective','Simultaneous Perspective','Cubist Perspective','Hierarchical Perspective','Twisted Perspective',
    'Flat Perspective','Layered Perspective','Overlap Perspective','Size Perspective','Vertical Perspective','Atmospheric Perspective','Aerial Perspective','Color Perspective','Detail Perspective','Value Perspective',
    'Wide-Angle Perspective','Ultra-Wide Perspective','Telephoto Perspective','Long-Lens Compression','Macro Perspective','Microscopic View','Telescope View','Circular Fisheye','Full-Frame Fisheye',
    'Stereographic Projection','Gnomonic Projection','Azimuthal Projection','Equidistant Projection','Equal-Area Projection','Cylindrical Projection','Conical Projection','Spherical Projection','Cube-Map Projection','Octahedral Projection',
]

PAGE_SIZE = 6
PAGE_COUNT = 19
WINDOW_TITLE = '2V Geodesic Dome - 114 Projection / Perspective Views'

COLOR_BG = (8, 11, 16)
COLOR_PANEL = (12, 16, 23)
COLOR_PANEL_ALT = (15, 20, 28)
COLOR_SHORT = (255, 158, 46)
COLOR_LONG = (51, 194, 255)
COLOR_BASE = (235, 235, 235)
COLOR_GRID = (68, 75, 88)
COLOR_DIM = (152, 160, 176)
COLOR_SECTION = (255, 80, 96)
COLOR_HIGHLIGHT = (140, 220, 170)

QUAD_VERTEX_SHADER = '''
#version 330
in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
'''

QUAD_FRAGMENT_SHADER = '''
#version 330
uniform sampler2D u_texture;
in vec2 v_uv;
out vec4 fragColor;
void main() {
    fragColor = texture(u_texture, v_uv);
}
'''


@dataclass
class ViewSpec:
    number: int
    name: str
    mode: str


MODE_BY_NUMBER = {
    1:'ortho_front',2:'persp1',3:'persp2',4:'persp3',5:'four_point',6:'five_point',7:'six_point',
    8:'curvilinear',9:'cylindrical',10:'spherical',11:'fisheye',12:'panoramic',13:'equirect',14:'mercator',
    15:'ortho_iso',16:'ortho_front',17:'ortho_rear',18:'ortho_left',19:'ortho_right',20:'ortho_top',21:'ortho_bottom',22:'ortho_top',23:'ortho_front',24:'section_x',25:'section_z',26:'section_y',27:'section_x',
    28:'ortho_iso',29:'isometric',30:'dimetric',31:'trimetric',32:'military',33:'plan_oblique',
    34:'oblique',35:'cavalier',36:'cabinet',37:'general_oblique',
    38:'eye_level',39:'high_angle',40:'low_angle',41:'birds_eye',42:'aerial',43:'gods_eye',44:'worms_eye',45:'ground_level',46:'top_down',47:'bottom_up',48:'overhead',49:'three_quarter',50:'front_three_quarter',51:'rear_three_quarter',52:'profile',53:'front_view',54:'rear_view',55:'dutch',56:'over_shoulder',57:'pov_inside',58:'third_person',
    59:'exploded',60:'cutaway',61:'ghosted',62:'wireframe',63:'hidden_line',64:'silhouette',65:'contour',66:'sectional_perspective',67:'sectional_axonometric',68:'exploded_axonometric',69:'exploded_isometric',
    70:'turnaround',71:'model_sheet3',72:'turnaround_3q',73:'turnaround8',74:'turnaround12',75:'turnaround_ortho',76:'turnaround_persp',
    77:'forced',78:'reverse',79:'inverse',80:'multiple',81:'composite',82:'simultaneous',83:'cubist',84:'hierarchical',85:'twisted',
    86:'flat',87:'layered',88:'overlap',89:'size',90:'vertical',91:'atmospheric',92:'aerial_perspective',93:'color_depth',94:'detail_depth',95:'value_depth',
    96:'wide',97:'ultrawide',98:'telephoto',99:'long_lens',100:'macro',101:'microscopic',102:'telescope',103:'circular_fisheye',104:'fullframe_fisheye',
    105:'stereographic',106:'gnomonic',107:'azimuthal',108:'equidistant',109:'equal_area',110:'cylindrical_projection',111:'conical',112:'spherical_projection',113:'cube_map',114:'octahedral',
}
VIEWS = [ViewSpec(i, name, MODE_BY_NUMBER[i]) for i, name in enumerate(VIEW_NAMES, start=1)]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def camera_basis(eye, target, up):
    eye = np.asarray(eye, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    up = np.asarray(up, dtype=np.float64)
    fwd = normalize(target - eye)
    right = normalize(np.cross(fwd, up))
    if float(np.linalg.norm(right)) < 1e-9:
        up = np.array([0.0, 1.0, 0.0])
        right = normalize(np.cross(fwd, up))
    true_up = normalize(np.cross(right, fwd))
    return eye, right, true_up, fwd


def world_to_camera(points, eye, target, up):
    eye, right, true_up, fwd = camera_basis(eye, target, up)
    rel = np.asarray(points, dtype=np.float64) - eye
    return np.stack((rel @ right, rel @ true_up, rel @ fwd), axis=1)


def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    hi=[]
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0: hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]


class ProjectionRenderer:
    def __init__(self, geometry, font, small_font, tiny_font):
        self.g=geometry
        self.font=font
        self.small_font=small_font
        self.tiny_font=tiny_font
        self.zoom=1.0
        self.show_faces=True
        self.show_grid=True
        self.hidden_line=True
        self.edge_faces=self._edge_faces()

    def reset(self):
        self.zoom=1.0

    def _edge_faces(self):
        out={e:[] for e in self.g.all_edges}
        for fi,tri in enumerate(self.g.faces):
            a,b,c=map(int,tri)
            for e in ((a,b),(b,c),(c,a)):
                out.setdefault(tuple(sorted(e)),[]).append(fi)
        return out

    @staticmethod
    def family(number):
        if number<=7:return 'LINEAR PERSPECTIVE'
        if number<=14:return 'CURVILINEAR / PANORAMIC'
        if number<=27:return 'ORTHOGRAPHIC / SECTION'
        if number<=33:return 'AXONOMETRIC'
        if number<=37:return 'OBLIQUE'
        if number<=58:return 'CAMERA ORIENTATION'
        if number<=69:return 'TECHNICAL / ARCHITECTURAL'
        if number<=76:return 'TURNAROUND / MODEL SHEET'
        if number<=85:return 'COMPOSITIONAL PERSPECTIVE'
        if number<=95:return 'DEPTH REPRESENTATION'
        if number<=104:return 'LENS-LIKE PERSPECTIVE'
        return 'SPECIAL GEOMETRIC PROJECTION'

    def render_panel(self, surface, rect, spec, t):
        pygame.draw.rect(surface, COLOR_PANEL_ALT if spec.number%2==0 else COLOR_PANEL, rect)
        inner=rect.inflate(-18,-58)
        inner.y+=20
        inner.h-=16
        if spec.mode in ('model_sheet3','turnaround8','turnaround12','multiple','composite','simultaneous','cubist','cube_map'):
            self._render_composite(surface,inner,spec,t)
        elif spec.mode in ('exploded','exploded_axonometric','exploded_isometric'):
            self._render_exploded(surface,inner,spec,t)
        else:
            self._render_single(surface,inner,spec,t)
        pygame.draw.rect(surface,(82,91,106),rect,1)
        surface.blit(self.small_font.render(f'{spec.number:03d}  {spec.name}',True,(238,241,246)),(rect.x+10,rect.y+8))
        surface.blit(self.tiny_font.render(self.family(spec.number),True,(145,154,171)),(rect.x+10,rect.bottom-22))

    def _camera(self, mode, t):
        r,h=self.g.base_radius,self.g.height
        c=np.array([0.,0.,h*.46])
        d=r*3.0/self.zoom
        up=np.array([0.,0.,1.])
        P='perspective'; f=48.; roll=0.
        if mode in ('ortho_front','front_view','profile','flat'): return np.array([0,-d,h*.5]),c,up,'orthographic',f,0
        if mode in ('ortho_rear','rear_view'): return np.array([0,d,h*.5]),c,up,'orthographic',f,0
        if mode=='ortho_left': return np.array([-d,0,h*.5]),c,up,'orthographic',f,0
        if mode=='ortho_right': return np.array([d,0,h*.5]),c,up,'orthographic',f,0
        if mode in ('ortho_top','top_down'): return np.array([0,0,d+h]),np.array([0,0,0]),np.array([0,1,0]),'orthographic',f,0
        if mode in ('ortho_bottom','bottom_up'): return np.array([0,0,-d]),c,np.array([0,1,0]),'orthographic',f,0
        if mode=='persp1': return np.array([0,-d,h*.62]),c,up,P,48,0
        if mode=='persp2': return np.array([d*.78,-d,h*.66]),c,up,P,52,0
        if mode=='persp3': return np.array([d*.9,-d*.9,h*.14]),c,up,P,58,0
        if mode in ('four_point','curvilinear','cylindrical','panoramic','cylindrical_projection'): return np.array([0,-r*2.45,h*.55]),c,up,'cylindrical',160,0
        if mode in ('five_point','fisheye','circular_fisheye'): return np.array([0,-r*2.15,h*.58]),c,up,'fisheye',180,0
        if mode=='fullframe_fisheye': return np.array([0,-r*2.15,h*.58]),c,up,'fullframe_fisheye',180,0
        if mode in ('six_point','spherical_projection'):
            eye=np.array([0,0,h*.40]);return eye,eye+np.array([0,1,0]),up,'equirect',360,0
        if mode in ('spherical','equirect'): return np.array([0,-r*2.2,h*.55]),c,up,'equirect',320,0
        if mode=='mercator': return np.array([0,-r*2.2,h*.55]),c,up,'mercator',320,0
        if mode in ('ortho_iso','isometric','sectional_axonometric'): return np.array([d*.9,-d*.9,d*.72]),c,up,'orthographic',f,0
        if mode=='dimetric': return np.array([d*.55,-d,d*.72]),c,up,'orthographic',f,0
        if mode=='trimetric': return np.array([d*.95,-d*.55,d*.48]),c,up,'orthographic',f,0
        if mode=='military': return np.array([0,0,d+h]),np.array([0,0,0]),np.array([0,1,0]),'military',f,0
        if mode=='plan_oblique': return np.array([0,0,d+h]),np.array([0,0,0]),np.array([0,1,0]),'plan_oblique',f,0
        if mode in ('oblique','general_oblique'): return np.array([0,-d,h*.5]),c,up,'oblique',f,0
        if mode=='cavalier': return np.array([0,-d,h*.5]),c,up,'cavalier',f,0
        if mode=='cabinet': return np.array([0,-d,h*.5]),c,up,'cabinet',f,0
        angles={
            'eye_level':(d*.6,-d,h*.52,50),'high_angle':(d*.6,-d,h*1.65,50),'low_angle':(d*.6,-d,h*.05,52),
            'birds_eye':(d*.65,-d*.65,h*2.4,55),'aerial':(d*.2,-d*.2,h*4.5,45),'gods_eye':(0,-r*.2,h*7,36),
            'worms_eye':(d*.25,-d*.6,-h*.65,70),'ground_level':(d*.15,-d*.95,2,62),'overhead':(d*.25,-d*.25,h*3,48),
            'three_quarter':(d*.82,-d,h*.72,48),'front_three_quarter':(d*.52,-d,h*.62,48),'rear_three_quarter':(-d*.6,d,h*.68,48),
            'third_person':(d*.85,-d*1.1,h*.95,45),'cutaway':(d*.72,-d,h*.72,50),'ghosted':(d*.72,-d,h*.72,50),
            'wireframe':(d*.72,-d,h*.72,50),'hidden_line':(d*.72,-d,h*.72,50),'silhouette':(d*.72,-d,h*.72,50),
            'contour':(d*.72,-d,h*.72,50),'sectional_perspective':(d*.72,-d,h*.72,50),'overlap':(d*.72,-d,h*.72,50),
            'hierarchical':(d*.65,-d,h*.72,50),'twisted':(d*.65,-d,h*.72,50),'layered':(d*.65,-d,h*.72,50),
            'vertical':(d*.65,-d,h*.72,50),'atmospheric':(d*.65,-d,h*.72,50),'color_depth':(d*.65,-d,h*.72,50),
            'detail_depth':(d*.65,-d,h*.72,50),'value_depth':(d*.65,-d,h*.72,50),
        }
        if mode in angles:
            x,y,z,fov=angles[mode];return np.array([x,y,z]),c,up,P,fov,0
        if mode=='dutch': return np.array([d*.65,-d,h*.68]),c,up,P,50,math.radians(22)
        if mode=='over_shoulder': return np.array([d*.92,-d*.55,h*.83]),c,up,P,56,math.radians(-4)
        if mode=='pov_inside':
            eye=np.array([0,0,h*.32]);return eye,eye+np.array([0,1,h*.05]),up,P,105,0
        if mode=='turnaround':
            a=t*.65;return np.array([math.sin(a)*d,-math.cos(a)*d,h*.72]),c,up,P,48,0
        if mode=='turnaround_3q': return np.array([d*.75,-d*.75,h*.7]),c,up,P,48,0
        if mode=='turnaround_ortho':
            a=t*.55;return np.array([math.sin(a)*d,-math.cos(a)*d,h*.62]),c,up,'orthographic',48,0
        if mode=='turnaround_persp':
            a=t*.55;return np.array([math.sin(a)*d,-math.cos(a)*d,h*.72]),c,up,P,48,0
        if mode=='forced': return np.array([r*.15,-r*.72,h*.38]),c,up,P,105,0
        if mode in ('reverse','inverse'): return np.array([0,-d,h*.58]),c,up,'reverse',55,0
        if mode=='size': return np.array([d*.25,-d*.7,h*.58]),c,up,P,95,0
        if mode=='aerial_perspective': return np.array([d*.45,-d*.55,h*2.5]),c,up,P,52,0
        if mode=='wide': return np.array([d*.55,-d*.8,h*.55]),c,up,P,82,0
        if mode=='ultrawide': return np.array([d*.3,-d*.62,h*.5]),c,up,P,120,0
        if mode=='telephoto': return np.array([d*4,-d*5,h]),c,up,P,16,0
        if mode=='long_lens': return np.array([d*5,-d*6,h]),c,up,P,11,0
        if mode=='macro': return np.array([r*.2,-r*.95,h*.78]),np.array([0,-r*.15,h*.72]),up,P,35,0
        if mode=='microscopic': return np.array([r*.05,-r*.48,h*.76]),np.array([0,-r*.05,h*.72]),up,P,28,0
        if mode=='telescope': return np.array([d*8,-d*10,h]),c,up,P,5.5,0
        if mode in ('stereographic','gnomonic','azimuthal','equidistant','equal_area','conical'):
            return np.array([0,-r*2.1,h*.55]),c,up,mode,180,0
        if mode=='octahedral':
            eye=np.array([0,0,h*.40]);return eye,eye+np.array([0,1,0]),up,'octahedral',360,0
        return np.array([d*.72,-d,h*.72]),c,up,P,f,roll

    def _transform(self, spec):
        p=np.asarray(self.g.vertices,dtype=np.float64).copy();h=self.g.height
        if spec.mode=='hierarchical':
            factor=1+.45*(p[:,2]/h);p[:,0]*=factor;p[:,1]*=factor
        elif spec.mode=='twisted':
            for i,v in enumerate(p.copy()):
                a=math.radians(55)*(v[2]/h);c,s=math.cos(a),math.sin(a)
                p[i,0]=v[0]*c-v[1]*s;p[i,1]=v[0]*s+v[1]*c
        return p

    def _project(self, pc, projection, rect, fov, roll=0):
        x,y,z=map(float,pc);aspect=rect.w/max(rect.h,1);nx=ny=0.0
        if projection=='orthographic':
            scale=self.g.base_radius*1.2/self.zoom;nx=x/(scale*aspect);ny=y/scale
        elif projection in ('military','plan_oblique'):
            scale=self.g.base_radius*1.3/self.zoom;k=.55 if projection=='military' else .42
            nx=(x+z*k*.65)/(scale*aspect);ny=(y+z*k)/scale
        elif projection in ('oblique','cavalier','cabinet'):
            scale=self.g.base_radius*1.25/self.zoom;k={'oblique':.7,'cavalier':1.0,'cabinet':.5}[projection];a=math.radians(42)
            nx=(x+z*k*math.cos(a))/(scale*aspect);ny=(y+z*k*math.sin(a))/scale
        elif projection=='reverse':
            scale=self.g.base_radius*1.35/self.zoom;gain=.55+max(z,0)/(self.g.base_radius*2.2)
            nx=x*gain/(scale*aspect);ny=y*gain/scale
        elif projection=='perspective':
            if z<=1e-4:return None
            th=math.tan(math.radians(fov)*.5);nx=x/(z*th*aspect);ny=y/(z*th)
        elif projection=='cylindrical':
            lon=math.atan2(x,z);lat=math.atan2(y,math.hypot(x,z));nx=lon/max(math.radians(fov)*.5,1e-6);ny=lat/math.radians(75)
        elif projection in ('equirect','mercator'):
            lon=math.atan2(x,z);lat=math.atan2(y,math.hypot(x,z));nx=lon/math.pi
            if projection=='mercator':
                lat=clamp(lat,math.radians(-82),math.radians(82));ny=-math.log(math.tan(math.pi/4+lat/2))/math.pi
            else: ny=-lat/(math.pi/2)
        elif projection in ('fisheye','fullframe_fisheye','stereographic','gnomonic','azimuthal','equidistant','equal_area'):
            rr=math.hypot(x,y);theta=math.atan2(rr,z);phi=math.atan2(y,x)
            if projection in ('fisheye','fullframe_fisheye') and theta>math.pi/2:return None
            if projection in ('fisheye','azimuthal','equidistant'):rad=theta/(math.pi/2)
            elif projection=='stereographic':rad=math.tan(theta/2)
            elif projection=='gnomonic':
                if theta>=math.radians(88):return None
                rad=math.tan(theta)/math.tan(math.radians(80))
            elif projection=='equal_area':rad=math.sqrt(2)*math.sin(theta/2)
            else:rad=theta/(math.pi/2)
            nx=rad*math.cos(phi);ny=-rad*math.sin(phi)
            if projection=='fullframe_fisheye':nx*=1.35;ny*=1.35
        elif projection=='conical':
            lon=math.atan2(x,z);lat=math.atan2(y,math.hypot(x,z));rho=(math.pi/2-lat)/(math.pi/2);n=.72
            nx=rho*math.sin(n*lon);ny=-(1-rho*math.cos(n*lon))
        elif projection=='octahedral':
            d=np.array([x,y,z],dtype=float);norm=np.sum(np.abs(d))
            if norm<1e-9:return (rect.centerx,rect.centery)
            d/=norm;ox,oy=float(d[0]),float(d[1])
            if d[2]<0:
                oldx,oldy=ox,oy;ox=(1-abs(oldy))*(1 if oldx>=0 else -1);oy=(1-abs(oldx))*(1 if oldy>=0 else -1)
            nx=ox;ny=-oy
        else:return None
        if roll:
            c,s=math.cos(roll),math.sin(roll);nx,ny=nx*c-ny*s,nx*s+ny*c
        return rect.centerx+nx*rect.w*.44,rect.centery-ny*rect.h*.44

    def _edge_poly(self,a,b,projection,rect,fov,roll):
        nonlinear=projection in ('cylindrical','equirect','mercator','fisheye','fullframe_fisheye','stereographic','gnomonic','azimuthal','equidistant','equal_area','conical','octahedral')
        count=22 if nonlinear else 2;groups=[];cur=[];last=None
        for i in range(count):
            p=a+(b-a)*(i/(count-1));q=self._project(p,projection,rect,fov,roll)
            if q is None:
                if len(cur)>=2:groups.append(cur)
                cur=[];last=None;continue
            xy=(int(q[0]),int(q[1]))
            if last and (abs(xy[0]-last[0])>rect.w*.55 or abs(xy[1]-last[1])>rect.h*.55):
                if len(cur)>=2:groups.append(cur)
                cur=[xy]
            else:cur.append(xy)
            last=xy
        if len(cur)>=2:groups.append(cur)
        return groups

    def _draw_grid(self,surface,rect,eye,target,up,projection,fov,roll):
        if not self.show_grid or projection not in ('perspective','orthographic','oblique','cavalier','cabinet'):return
        ext=math.ceil(self.g.base_radius*1.15/12)*12;world=[]
        for v in np.arange(-ext,ext+.1,24):world.extend([[-ext,v,0],[ext,v,0],[v,-ext,0],[v,ext,0]])
        cam=world_to_camera(np.asarray(world),eye,target,up)
        for i in range(0,len(cam),2):
            a=self._project(cam[i],projection,rect,fov,roll);b=self._project(cam[i+1],projection,rect,fov,roll)
            if a and b:pygame.draw.line(surface,COLOR_GRID,a,b,1)

    def _depth(self,z,cam):
        lo=float(np.min(cam[:,2]));hi=float(np.max(cam[:,2]));return .5 if hi-lo<1e-8 else clamp((z-lo)/(hi-lo),0,1)

    def _front_edges(self,cam):
        vf=set()
        for fi,tri in enumerate(self.g.faces):
            a,b,c=(cam[int(i)] for i in tri);n=np.cross(b-a,c-a)
            if n[2]<0:vf.add(fi)
        return {e for e,fs in self.edge_faces.items() if any(f in vf for f in fs)}

    def _draw_faces(self,surface,rect,cam,projection,fov,roll,alpha,world,cut_axis=None):
        if projection not in ('perspective','orthographic','oblique','cavalier','cabinet','military','plan_oblique','reverse'):return
        layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA);faces=[]
        for tri in self.g.faces:
            ids=list(map(int,tri))
            if cut_axis is not None and float(np.mean(world[ids,cut_axis]))>0:continue
            pts=[]
            for i in ids:
                q=self._project(cam[i],projection,rect,fov,roll)
                if not q:pts=[];break
                pts.append((int(q[0]),int(q[1])))
            if pts:faces.append((float(np.mean(cam[ids,2])),pts))
        for _,pts in sorted(faces,reverse=True):
            pygame.draw.polygon(layer,(65,76,92,alpha),pts);pygame.draw.polygon(layer,(90,102,118,min(110,alpha+20)),pts,1)
        surface.blit(layer,(0,0))

    def _render_single(self,surface,rect,spec,t):
        eye,target,up,P,fov,roll=self._camera(spec.mode,t);world=self._transform(spec);cam=world_to_camera(world,eye,target,up)
        self._draw_grid(surface,rect,eye,target,up,P,fov,roll)
        cut_axis=0 if spec.mode in ('cutaway','sectional_perspective','sectional_axonometric') else None
        if self.show_faces:
            if spec.mode=='ghosted':self._draw_faces(surface,rect,cam,P,fov,roll,38,world)
            elif spec.mode=='overlap':self._draw_faces(surface,rect,cam,P,fov,roll,175,world)
            elif spec.mode not in ('wireframe','hidden_line','silhouette','contour','section_x','section_y','section_z'):
                self._draw_faces(surface,rect,cam,P,fov,roll,58,world,cut_axis)
        if spec.mode=='silhouette':
            pts=[]
            for p in cam:
                q=self._project(p,P,rect,fov,roll)
                if q:pts.append((int(q[0]),int(q[1])))
            hull=convex_hull(pts)
            if len(hull)>=3:pygame.draw.lines(surface,COLOR_BASE,True,hull,3)
            return
        if spec.mode=='contour':
            self._draw_contour(surface,rect,cam,P,fov,roll);return
        if spec.mode in ('section_x','section_y','section_z'):
            axis={'section_x':0,'section_y':1,'section_z':2}[spec.mode];self._draw_section(surface,rect,axis,t);return
        visible=self._front_edges(cam) if spec.mode=='hidden_line' and self.hidden_line else None
        def draw(edges,base):
            for e in edges:
                if visible is not None and tuple(sorted(e)) not in visible:continue
                if cut_axis is not None and float(np.mean(world[list(e),cut_axis]))>0:continue
                dep=self._depth(float(np.mean(cam[list(e),2])),cam);color=base;width=2
                if spec.mode in ('atmospheric','aerial_perspective'):
                    k=int(70+185*(1-dep));color=tuple(int(c*k/255) for c in base)
                elif spec.mode=='color_depth':color=(int(255*(1-dep)),int(110+120*dep),int(255*dep))
                elif spec.mode=='detail_depth':width=max(1,int(4-3*dep))
                elif spec.mode=='value_depth':v=int(80+175*(1-dep));color=(v,v,v)
                elif spec.mode=='layered':color=((255,155,55),(90,210,255),(200,120,255))[min(int(dep*3),2)]
                for pts in self._edge_poly(cam[e[0]],cam[e[1]],P,rect,fov,roll):
                    if spec.mode=='vertical':pts=[(x,y+int((.5-dep)*rect.h*.1)) for x,y in pts]
                    if len(pts)>=2:pygame.draw.lines(surface,color,False,pts,width)
        draw(self.g.short_edges,COLOR_SHORT);draw(self.g.long_edges,COLOR_LONG)
        ids=self.g.base_vertices
        for i,a in enumerate(ids):
            b=ids[(i+1)%len(ids)]
            if cut_axis is not None and float(np.mean(world[[a,b],cut_axis]))>0:continue
            for pts in self._edge_poly(cam[a],cam[b],P,rect,fov,roll):pygame.draw.lines(surface,COLOR_BASE,False,pts,2)
        if cut_axis is not None:self._section_overlay(surface,rect,world,eye,target,up,P,fov,roll,0)
        if spec.mode=='over_shoulder':
            local=pygame.Surface((rect.w,rect.h),pygame.SRCALPHA);pygame.draw.ellipse(local,(8,10,14,190),(0,int(rect.h*.55),int(rect.w*.34),int(rect.h*.6)));surface.blit(local,rect.topleft)
        if spec.mode in ('five_point','fisheye','circular_fisheye'):pygame.draw.circle(surface,(110,118,132),rect.center,int(min(rect.w,rect.h)*.44),1)
        if P in ('equirect','mercator'):pygame.draw.rect(surface,(100,108,122),rect.inflate(-10,-10),1)
        if P=='octahedral':
            d=[(rect.centerx,rect.top+8),(rect.right-8,rect.centery),(rect.centerx,rect.bottom-8),(rect.left+8,rect.centery)];pygame.draw.lines(surface,(110,118,132),True,d,1)

    def _draw_contour(self,surface,rect,cam,P,fov,roll):
        pts=[]
        for p in cam:
            q=self._project(p,P,rect,fov,roll)
            if q:pts.append((int(q[0]),int(q[1])))
        hull=convex_hull(pts)
        if len(hull)>=3:pygame.draw.lines(surface,COLOR_BASE,True,hull,2)
        levels=sorted(set(round(float(z),4) for z in self.g.vertices[:,2]))
        for lev in levels:
            ids=[i for i,v in enumerate(self.g.vertices) if round(float(v[2]),4)==lev]
            if len(ids)<3:continue
            ids.sort(key=lambda i:math.atan2(float(self.g.vertices[i,1]),float(self.g.vertices[i,0])))
            ring=[]
            for i in ids:
                q=self._project(cam[i],P,rect,fov,roll)
                if q:ring.append((int(q[0]),int(q[1])))
            if len(ring)>=3:pygame.draw.lines(surface,(110,200,220),True,ring,1)

    def _draw_section(self,surface,rect,axis,t):
        mode='ortho_top' if axis==2 else 'ortho_front';eye,target,up,P,fov,roll=self._camera(mode,t);world=np.asarray(self.g.vertices,dtype=float);cam=world_to_camera(world,eye,target,up)
        for e in self.g.all_edges:
            for pts in self._edge_poly(cam[e[0]],cam[e[1]],P,rect,fov,roll):pygame.draw.lines(surface,(75,82,96),False,pts,1)
        self._section_overlay(surface,rect,world,eye,target,up,P,fov,roll,axis)

    def _section_overlay(self,surface,rect,world,eye,target,up,P,fov,roll,axis):
        plane=0 if axis in (0,1) else self.g.height*.48
        for tri in self.g.faces:
            pts=world[list(map(int,tri))];hits=[]
            for i,j in ((0,1),(1,2),(2,0)):
                a,b=pts[i],pts[j];da=float(a[axis]-plane);db=float(b[axis]-plane)
                if abs(da)<1e-9:hits.append(a)
                if da*db<0:hits.append(a+(b-a)*(da/(da-db)))
            unique=[]
            for p in hits:
                if not any(np.linalg.norm(p-q)<1e-6 for q in unique):unique.append(p)
            if len(unique)>=2:
                c=world_to_camera(np.asarray(unique[:2]),eye,target,up);a=self._project(c[0],P,rect,fov,roll);b=self._project(c[1],P,rect,fov,roll)
                if a and b:pygame.draw.line(surface,COLOR_SECTION,a,b,3)

    def _render_exploded(self,surface,rect,spec,t):
        mode='isometric' if spec.mode=='exploded_isometric' else 'sectional_axonometric' if spec.mode=='exploded_axonometric' else 'third_person'
        eye,target,up,P,fov,roll=self._camera(mode,t);base=np.asarray(self.g.vertices,dtype=float);center=np.array([0,0,self.g.height*.38])
        for fi,tri in enumerate(self.g.faces):
            ids=list(map(int,tri));face=base[ids].copy();fc=np.mean(face,axis=0);face+=normalize(fc-center)*self.g.long_length*.2;cam=world_to_camera(face,eye,target,up);pts=[]
            for p in cam:
                q=self._project(p,P,rect,fov,roll)
                if q:pts.append((int(q[0]),int(q[1])))
            if len(pts)==3:pygame.draw.lines(surface,COLOR_SHORT if fi%2==0 else COLOR_LONG,True,pts,1)

    def _render_composite(self,surface,rect,spec,t):
        if spec.mode=='model_sheet3':return self._subviews(surface,rect,[('ortho_front','FRONT'),('ortho_right','SIDE'),('ortho_rear','REAR')],3,1,t,True)
        if spec.mode=='turnaround8':return self._subviews(surface,rect,[(f'angle:{i*45}','') for i in range(8)],4,2,t,False)
        if spec.mode=='turnaround12':return self._subviews(surface,rect,[(f'angle:{i*30}','') for i in range(12)],4,3,t,False)
        if spec.mode=='multiple':return self._subviews(surface,rect,[('ortho_front','FRONT'),('isometric','ISO'),('top_down','TOP')],3,1,t,False)
        if spec.mode=='simultaneous':return self._subviews(surface,rect,[('front_view','FRONT'),('three_quarter','3/4'),('ortho_top','TOP'),('rear_view','REAR')],2,2,t,False)
        if spec.mode=='composite':
            for m,col in [('ortho_front',(255,160,70)),('ortho_top',(70,205,255)),('isometric',(200,120,255))]:self._subview(surface,rect,m,t,col)
            return
        if spec.mode=='cubist':
            for a,col in [(0,(255,150,60)),(45,(60,200,255)),(90,(210,120,255)),(135,(130,235,160))]:self._angle(surface,rect,a,col,True)
            return
        if spec.mode=='cube_map':return self._cube(surface,rect)

    def _subviews(self,surface,rect,cams,cols,rows,t,ortho):
        cw=rect.w//cols;ch=rect.h//rows
        for i,(m,label) in enumerate(cams):
            c=i%cols;r=i//cols;sub=pygame.Rect(rect.x+c*cw,rect.y+r*ch,cw if c<cols-1 else rect.w-c*cw,ch if r<rows-1 else rect.h-r*ch);pygame.draw.rect(surface,(72,80,94),sub,1)
            if m.startswith('angle:'):self._angle(surface,sub,float(m.split(':')[1]),COLOR_BASE,ortho)
            else:self._subview(surface,sub,m,t,COLOR_BASE)
            if label:surface.blit(self.tiny_font.render(label,True,COLOR_DIM),(sub.x+4,sub.y+4))

    def _subview(self,surface,rect,mode,t,color):
        eye,target,up,P,fov,roll=self._camera(mode,t);cam=world_to_camera(np.asarray(self.g.vertices,dtype=float),eye,target,up)
        for e in self.g.all_edges:
            for pts in self._edge_poly(cam[e[0]],cam[e[1]],P,rect,fov,roll):pygame.draw.lines(surface,color,False,pts,1)

    def _angle(self,surface,rect,angle,color,ortho=False):
        r,h=self.g.base_radius,self.g.height;d=r*3;a=math.radians(angle);eye=np.array([math.sin(a)*d,-math.cos(a)*d,h*.65]);target=np.array([0,0,h*.45]);up=np.array([0,0,1]);P='orthographic' if ortho else 'perspective';cam=world_to_camera(np.asarray(self.g.vertices,dtype=float),eye,target,up)
        for e in self.g.all_edges:
            for pts in self._edge_poly(cam[e[0]],cam[e[1]],P,rect,48,0):pygame.draw.lines(surface,color,False,pts,1)

    def _cube(self,surface,rect):
        size=min(rect.w//4,rect.h//3);ox=rect.centerx-2*size;oy=rect.centery-int(1.5*size);eye=np.array([0,0,self.g.height*.40])
        faces=[('+Y',(1,1)),('-X',(0,1)),('+Z',(1,0)),('+X',(2,1)),('-Z',(1,2)),('-Y',(3,1))]
        dirs={'+X':(1,0,0),'-X':(-1,0,0),'+Y':(0,1,0),'-Y':(0,-1,0),'+Z':(0,0,1),'-Z':(0,0,-1)};ups={'+X':(0,0,1),'-X':(0,0,1),'+Y':(0,0,1),'-Y':(0,0,1),'+Z':(0,1,0),'-Z':(0,-1,0)}
        for name,(cx,cy) in faces:
            sub=pygame.Rect(ox+cx*size,oy+cy*size,size,size);pygame.draw.rect(surface,(78,86,100),sub,1);cam=world_to_camera(np.asarray(self.g.vertices,dtype=float),eye,eye+np.asarray(dirs[name]),ups[name])
            for e in self.g.all_edges:
                for pts in self._edge_poly(cam[e[0]],cam[e[1]],'perspective',sub,90,0):pygame.draw.lines(surface,COLOR_BASE,False,pts,1)
            surface.blit(self.tiny_font.render(name,True,COLOR_DIM),(sub.x+3,sub.y+3))


class ModernGLPresenter:
    def __init__(self,ctx):
        self.ctx=ctx;self.program=ctx.program(vertex_shader=QUAD_VERTEX_SHADER,fragment_shader=QUAD_FRAGMENT_SHADER)
        quad=np.array([-1,-1,0,1, 1,-1,1,1, -1,1,0,0, -1,1,0,0, 1,-1,1,1, 1,1,1,0],dtype=np.float32)
        self.vbo=ctx.buffer(quad.tobytes());self.vao=ctx.vertex_array(self.program,[(self.vbo,'2f 2f','in_position','in_uv')]);self.texture=None
    def draw(self,surface):
        if self.texture:self.texture.release()
        self.texture=self.ctx.texture(surface.get_size(),4,pygame.image.tostring(surface,'RGBA',False));self.texture.filter=(moderngl.LINEAR,moderngl.LINEAR);self.texture.use(0);self.program['u_texture'].value=0;self.ctx.viewport=(0,0,*surface.get_size());self.vao.render(moderngl.TRIANGLES)

class App:
    def __init__(self):
        pygame.init();pygame.font.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER,1)
        self.window_size=(WINDOW_W,WINDOW_H)
        pygame.display.set_mode(self.window_size,pygame.OPENGL|pygame.DOUBLEBUF|pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        self.ctx=moderngl.create_context();self.presenter=ModernGLPresenter(self.ctx)
        self.geometry=DomeBuilder(SHORT_STRUT_IN,LONG_STRUT_IN).build()
        self.font=pygame.font.SysFont('consolas',20,bold=True);self.small_font=pygame.font.SysFont('consolas',15,bold=True);self.tiny_font=pygame.font.SysFont('consolas',13)
        self.renderer=ProjectionRenderer(self.geometry,self.font,self.small_font,self.tiny_font)
        self.clock=pygame.time.Clock();self.running=True;self.page=0;self.single_view=None;self.screenshot_pending=False
        self._report()

    def _report(self):
        g=self.geometry
        print('\n=== 2V DOME / 114-VIEW ATLAS ===')
        print(f'A short strut : {g.short_length:.6f} in x {len(g.short_edges)}')
        print(f'B long strut  : {g.long_length:.6f} in x {len(g.long_edges)}')
        print(f'Base diameter : {g.base_radius*2:.6f} in')
        print(f'Dome height   : {g.height:.6f} in')
        print(f'Views         : {len(VIEWS)}')
        print(f'Pages         : {PAGE_COUNT} pages x {PAGE_SIZE} views')
        print('LEFT/RIGHT page; UP/DOWN individual view; 0 six-up; 1-6 fullscreen slot.\n')

    def current_specs(self):
        s=self.page*PAGE_SIZE;return VIEWS[s:s+PAGE_SIZE]

    def page_rects(self):
        w,h=self.window_size;head=38;foot=94;usable=h-head-foot;cw=w//3;ch=usable//2;out=[]
        for i in range(6):
            c=i%3;r=i//3;x=c*cw;y=head+r*ch;rw=cw if c<2 else w-x;rh=ch if r<1 else head+usable-y;out.append(pygame.Rect(x,y,rw,rh))
        return out

    def single_rect(self):
        w,h=self.window_size;return pygame.Rect(0,38,w,h-132)

    def footer(self,surface):
        w,h=self.window_size;pygame.draw.rect(surface,(6,8,12),(0,0,w,38));pygame.draw.rect(surface,(6,8,12),(0,h-94,w,94))
        start=self.page*6+1;end=min(start+5,114)
        surface.blit(self.font.render(f'2V GEODESIC DOME - 114 VIEW ATLAS   PAGE {self.page+1:02d}/19   VIEWS {start:03d}-{end:03d}',True,(238,241,246)),(12,8))
        g=self.geometry
        l1=f'A SHORT 63 5/8 in x {len(g.short_edges)}   |   B LONG 72 in x {len(g.long_edges)}   |   BASE DIA {g.base_radius*2:.3f} in   |   HEIGHT {g.height:.3f} in'
        l2='LEFT/RIGHT = page   UP/DOWN = previous/next single view   0 = six-view page   1-6 = fullscreen page slot   Tab = next page'
        l3=f'F faces={"ON" if self.renderer.show_faces else "OFF"}   G grid={"ON" if self.renderer.show_grid else "OFF"}   H hidden-line={"ON" if self.renderer.hidden_line else "OFF"}   wheel zoom={self.renderer.zoom:.2f}x   R reset   S screenshot   Esc quit'
        surface.blit(self.tiny_font.render(l1,True,(205,211,221)),(12,h-82));surface.blit(self.tiny_font.render(l2,True,(175,184,198)),(12,h-56));surface.blit(self.tiny_font.render(l3,True,COLOR_HIGHLIGHT),(12,h-30))

    def frame(self):
        s=pygame.Surface(self.window_size,pygame.SRCALPHA,32);s.fill(COLOR_BG);t=pygame.time.get_ticks()/1000.0
        if self.single_view is None:
            for spec,rect in zip(self.current_specs(),self.page_rects()):self.renderer.render_panel(s,rect,spec,t)
        else:self.renderer.render_panel(s,self.single_rect(),VIEWS[self.single_view],t)
        self.footer(s);return s

    def select_global(self,i):
        i%=len(VIEWS);self.single_view=i;self.page=i//6

    def change_page(self,d):
        self.page=(self.page+d)%PAGE_COUNT;self.single_view=None

    def events(self):
        for e in pygame.event.get():
            if e.type==pygame.QUIT:self.running=False
            elif e.type==pygame.VIDEORESIZE:self.window_size=(max(900,e.w),max(650,e.h))
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:self.running=False
                elif e.key==pygame.K_RIGHT:self.change_page(1)
                elif e.key==pygame.K_LEFT:self.change_page(-1)
                elif e.key==pygame.K_TAB:self.change_page(1)
                elif e.key==pygame.K_UP:
                    self.select_global(self.page*6 if self.single_view is None else self.single_view-1)
                elif e.key==pygame.K_DOWN:
                    self.select_global(self.page*6 if self.single_view is None else self.single_view+1)
                elif e.key==pygame.K_0:self.single_view=None
                elif pygame.K_1<=e.key<=pygame.K_6:
                    idx=self.page*6+(e.key-pygame.K_1)
                    if idx<len(VIEWS):self.select_global(idx)
                elif e.key==pygame.K_f:self.renderer.show_faces=not self.renderer.show_faces
                elif e.key==pygame.K_g:self.renderer.show_grid=not self.renderer.show_grid
                elif e.key==pygame.K_h:self.renderer.hidden_line=not self.renderer.hidden_line
                elif e.key==pygame.K_r:self.renderer.reset()
                elif e.key==pygame.K_s:self.screenshot_pending=True
            elif e.type==pygame.MOUSEWHEEL:self.renderer.zoom=clamp(self.renderer.zoom*(1.1**e.y),.45,3.5)

    def screenshot(self,frame):
        stamp=time.strftime('%Y%m%d_%H%M%S');suffix=f'view_{self.single_view+1:03d}' if self.single_view is not None else f'page_{self.page+1:02d}';out=Path(__file__).resolve().parent/f'geodesic_2v_{suffix}_{stamp}.png';pygame.image.save(frame,str(out));print('Saved screenshot:',out)

    def run(self):
        while self.running:
            self.events();frame=self.frame();self.ctx.clear(.02,.025,.035,1);self.presenter.draw(frame)
            if self.screenshot_pending:self.screenshot(frame);self.screenshot_pending=False
            pygame.display.flip();self.clock.tick(60)
        pygame.quit()


def main():
    try:App().run()
    except Exception as exc:
        pygame.quit();print('\nERROR:\n',exc);print('\nInstall dependencies with:\n    pip install pygame moderngl numpy');raise

if __name__=='__main__':main()
