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
# OpenGL rendering
# -----------------------------------------------------------------------------
VERTEX_SHADER = """
#version 330

in vec3 in_position;
uniform mat4 u_mvp;

void main() {
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330

uniform vec4 u_color;
out vec4 fragColor;

void main() {
    fragColor = u_color;
}
"""

OVERLAY_VERTEX_SHADER = """
#version 330

in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

OVERLAY_FRAGMENT_SHADER = """
#version 330

uniform sampler2D u_texture;
in vec2 v_uv;
out vec4 fragColor;

void main() {
    fragColor = texture(u_texture, v_uv);
}
"""


@dataclass
class ViewSpec:
    title: str
    mode: str


VIEWS = [
    ViewSpec("1  SIDE ORTHOGRAPHIC ELEVATION", "side_ortho"),
    ViewSpec("2  PERSPECTIVE", "perspective"),
    ViewSpec("3  CABINET OBLIQUE", "oblique"),
    ViewSpec("4  SIDE WIREFRAME - ALL STRUTS", "side_wire"),
    ViewSpec("5  TOP ORTHOGRAPHIC PLAN", "top_ortho"),
    ViewSpec("6  FRONT ORTHOGRAPHIC ELEVATION", "front_ortho"),
]


class DomeRenderer:
    def __init__(self, ctx: moderngl.Context, geometry: DomeGeometry):
        self.ctx = ctx
        self.g = geometry

        self.program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        self.overlay_program = ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER,
        )

        # Keep explicit references to every VBO; ModernGL objects do not permit
        # arbitrary Python attributes on every platform.
        self._owned_buffers: List[moderngl.Buffer] = []

        # Separate buffers for A and B struts make color coding and counts obvious.
        self.short_vao = self._create_edge_vao(self.g.short_edges)
        self.long_vao = self._create_edge_vao(self.g.long_edges)
        self.face_vao = self._create_face_vao()
        self.base_vao = self._create_base_vao()
        self.grid_vao = self._create_grid_vao()

        # Full-screen overlay quad.  Texture coordinates are vertically flipped
        # because pygame surfaces use top-left origin while OpenGL uses bottom-left.
        quad = np.array(
            [
                -1.0, -1.0, 0.0, 1.0,
                 1.0, -1.0, 1.0, 1.0,
                -1.0,  1.0, 0.0, 0.0,
                -1.0,  1.0, 0.0, 0.0,
                 1.0, -1.0, 1.0, 1.0,
                 1.0,  1.0, 1.0, 0.0,
            ],
            dtype=np.float32,
        )
        self.overlay_vbo = ctx.buffer(quad.tobytes())
        self.overlay_vao = ctx.vertex_array(
            self.overlay_program,
            [(self.overlay_vbo, "2f 2f", "in_position", "in_uv")],
        )
        self.overlay_texture: moderngl.Texture | None = None

        self.show_faces = True
        self.hidden_line = True
        self.show_grid = True
        self.yaw = math.radians(0.0)
        self.pitch = math.radians(0.0)
        self.zoom = 1.0

    def _create_edge_vao(self, edges: Sequence[Tuple[int, int]]) -> moderngl.VertexArray:
        line_vertices = np.asarray(
            [self.g.vertices[idx] for edge in edges for idx in edge],
            dtype=np.float32,
        )
        vbo = self.ctx.buffer(line_vertices.tobytes())
        vao = self.ctx.vertex_array(self.program, [(vbo, "3f", "in_position")])
        self._owned_buffers.append(vbo)
        return vao

    def _create_face_vao(self) -> moderngl.VertexArray:
        tri_vertices = np.asarray(
            [self.g.vertices[int(idx)] for tri in self.g.faces for idx in tri],
            dtype=np.float32,
        )
        vbo = self.ctx.buffer(tri_vertices.tobytes())
        vao = self.ctx.vertex_array(self.program, [(vbo, "3f", "in_position")])
        self._owned_buffers.append(vbo)
        return vao

    def _create_base_vao(self) -> moderngl.VertexArray:
        ids = self.g.base_vertices
        lines = []
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]
            lines.extend((self.g.vertices[a], self.g.vertices[b]))
        arr = np.asarray(lines, dtype=np.float32)
        vbo = self.ctx.buffer(arr.tobytes())
        vao = self.ctx.vertex_array(self.program, [(vbo, "3f", "in_position")])
        self._owned_buffers.append(vbo)
        return vao

    def _create_grid_vao(self) -> moderngl.VertexArray:
        r = self.g.base_radius
        extent = math.ceil((r * 1.25) / 12.0) * 12.0
        lines: List[Tuple[float, float, float]] = []

        # One-foot spacing grid on the z=0 plane.
        value = -extent
        while value <= extent + 1e-6:
            lines.extend(((-extent, value, 0.0), (extent, value, 0.0)))
            lines.extend(((value, -extent, 0.0), (value, extent, 0.0)))
            value += 12.0

        arr = np.asarray(lines, dtype=np.float32)
        vbo = self.ctx.buffer(arr.tobytes())
        vao = self.ctx.vertex_array(self.program, [(vbo, "3f", "in_position")])
        self._owned_buffers.append(vbo)
        return vao

    def reset_view(self) -> None:
        self.yaw = 0.0
        self.pitch = 0.0
        self.zoom = 1.0

    def _draw_vao(self, vao: moderngl.VertexArray, mvp: np.ndarray,
                  color: Tuple[float, float, float, float], mode: int) -> None:
        self.program["u_mvp"].write(matrix_bytes(mvp))
        self.program["u_color"].value = color
        vao.render(mode=mode)

    def _projection_for(self, mode: str, aspect: float) -> Tuple[np.ndarray, np.ndarray, bool]:
        """Return model-view, projection, and whether hidden-line depth should apply."""
        radius = self.g.base_radius
        height = self.g.height
        center = np.array([0.0, 0.0, height * 0.45], dtype=np.float64)

        # User rotation affects the 3D/perspective family, but fixed drafting views
        # remain true orthographic elevations/plans.
        user_rot = rotation_z(self.yaw) @ rotation_x(self.pitch)

        if mode == "perspective":
            distance = radius * 3.1 / self.zoom
            eye = np.array([distance * 0.72, -distance, height * 1.15], dtype=np.float64)
            view = look_at(eye, center, (0.0, 0.0, 1.0)) @ user_rot
            proj = perspective_matrix(42.0, aspect, 1.0, radius * 20.0)
            return view, proj, True

        # Orthographic fitting margin.  Wider aspect ratios need extra horizontal
        # half-span so the dome remains completely visible.
        vertical_half = max(height * 0.62, radius * 0.58) / self.zoom
        horizontal_half = vertical_half * aspect
        if horizontal_half < radius * 1.12 / self.zoom:
            horizontal_half = radius * 1.12 / self.zoom
            vertical_half = horizontal_half / max(aspect, 1e-8)

        proj = ortho_matrix(
            -horizontal_half,
            horizontal_half,
            -vertical_half,
            vertical_half,
        )

        if mode in ("side_ortho", "side_wire"):
            # Look along +Y.  Shift the dome so the base is below panel center and
            # its overall silhouette is vertically centered.
            view = look_at(
                (0.0, -radius * 5.0, height * 0.5),
                (0.0, 0.0, height * 0.5),
                (0.0, 0.0, 1.0),
            )
            return view, proj, mode != "side_wire"

        if mode == "front_ortho":
            # Look along +X.  Because the dome has fivefold symmetry this is still
            # an elevation, but the projected strut overlap pattern differs.
            view = look_at(
                (-radius * 5.0, 0.0, height * 0.5),
                (0.0, 0.0, height * 0.5),
                (0.0, 0.0, 1.0),
            )
            return view, proj, True

        if mode == "top_ortho":
            # Looking straight down requires a non-Z up vector.
            view = look_at(
                (0.0, 0.0, radius * 5.0),
                (0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            )
            return view, proj, True

        if mode == "oblique":
            # Start with a true side orthographic camera, then shear world depth
            # into screen X/Z.  This is an actual parallel oblique projection,
            # not a perspective camera imitation.
            base_view = look_at(
                (0.0, -radius * 5.0, height * 0.5),
                (0.0, 0.0, height * 0.5),
                (0.0, 0.0, 1.0),
            )
            shear = cabinet_oblique_matrix(0.5, 45.0)
            view = base_view @ shear @ user_rot
            return view, proj, True

        raise ValueError(f"Unknown view mode: {mode}")

    def render_view(self, spec: ViewSpec, viewport: Tuple[int, int, int, int]) -> None:
        x, y, w, h = viewport
        if w <= 2 or h <= 2:
            return

        self.ctx.viewport = viewport
        self.ctx.scissor = viewport

        aspect = w / max(h, 1)
        view, proj, view_uses_hidden_lines = self._projection_for(spec.mode, aspect)
        mvp = proj @ view

        # Reference grid first, with depth disabled so it remains a simple drafting
        # aid.  It is omitted in the top plan only if G is toggled off.
        if self.show_grid:
            self.ctx.disable(moderngl.DEPTH_TEST)
            self._draw_vao(
                self.grid_vao,
                mvp,
                (0.18, 0.20, 0.24, 0.50),
                moderngl.LINES,
            )

        use_depth = self.hidden_line and view_uses_hidden_lines

        # Hidden-line removal needs the triangular shell in the depth buffer even
        # when the user does not want the faces visibly shaded.
        if use_depth:
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.depth_func = "<"
            self.ctx.color_mask = (False, False, False, False)
            self._draw_vao(
                self.face_vao,
                mvp,
                (0.0, 0.0, 0.0, 1.0),
                moderngl.TRIANGLES,
            )
            self.ctx.color_mask = (True, True, True, True)
            # Allow struts lying exactly on a triangular face to pass the depth
            # test after the depth-only prepass.
            self.ctx.depth_func = "<="

        # Light translucent shell faces help the perspective/oblique views read as
        # a 3D dome while preserving the wireframe structure.
        if self.show_faces and spec.mode in ("perspective", "oblique", "side_ortho", "front_ortho"):
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            self.ctx.depth_func = "<="
            self._draw_vao(
                self.face_vao,
                mvp,
                (0.18, 0.22, 0.28, 0.20),
                moderngl.TRIANGLES,
            )

        if use_depth:
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.depth_func = "<="
        else:
            self.ctx.disable(moderngl.DEPTH_TEST)

        # A-struts (short) and B-struts (long) are deliberately distinct.
        self.ctx.line_width = 1.6
        self._draw_vao(
            self.short_vao,
            mvp,
            (1.00, 0.62, 0.18, 1.0),
            moderngl.LINES,
        )
        self._draw_vao(
            self.long_vao,
            mvp,
            (0.20, 0.76, 1.00, 1.0),
            moderngl.LINES,
        )

        # Reinforce the decagonal base perimeter.
        self.ctx.line_width = 2.0
        self._draw_vao(
            self.base_vao,
            mvp,
            (0.92, 0.92, 0.92, 1.0),
            moderngl.LINES,
        )

        self.ctx.scissor = None

    def set_overlay(self, surface: pygame.Surface) -> None:
        if self.overlay_texture is not None:
            self.overlay_texture.release()

        rgba = pygame.image.tostring(surface, "RGBA", False)
        self.overlay_texture = self.ctx.texture(surface.get_size(), 4, rgba)
        self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.overlay_texture.swizzle = "RGBA"

    def render_overlay(self, window_size: Tuple[int, int]) -> None:
        if self.overlay_texture is None:
            return
        self.ctx.viewport = (0, 0, window_size[0], window_size[1])
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.overlay_texture.use(location=0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_vao.render(mode=moderngl.TRIANGLES)


# -----------------------------------------------------------------------------
# Pygame/OpenGL application
# -----------------------------------------------------------------------------
class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()

        # Request a normal desktop OpenGL 3.3 core context compatible with the
        # shaders above.
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK,
            pygame.GL_CONTEXT_PROFILE_CORE,
        )
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        self.window_size = (WINDOW_W, WINDOW_H)
        pygame.display.set_mode(
            self.window_size,
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
        )
        pygame.display.set_caption(WINDOW_TITLE)

        self.ctx = moderngl.create_context()
        self.ctx.gc_mode = "auto"

        self.geometry = DomeBuilder(SHORT_STRUT_IN, LONG_STRUT_IN).build()
        self.renderer = DomeRenderer(self.ctx, self.geometry)

        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_view = 0  # 0 = multi-view, 1..6 = single
        self.dragging = False
        self.last_mouse = (0, 0)
        self.overlay_dirty = True

        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.tiny_font = pygame.font.SysFont("consolas", 14)

        self._print_geometry_report()

    @staticmethod
    def _feet_inches(inches: float) -> str:
        feet = int(inches // 12.0)
        remain = inches - feet * 12.0
        return f"{feet} ft {remain:.3f} in"

    def _print_geometry_report(self) -> None:
        g = self.geometry
        print("\n=== EXACT 2V DOME GEOMETRY ===")
        print(f"Short A strut : {g.short_length:.6f} in  ({len(g.short_edges)} pieces)")
        print(f"Long  B strut : {g.long_length:.6f} in  ({len(g.long_edges)} pieces)")
        print(f"Total struts  : {len(g.all_edges)}")
        print(f"Vertices      : {len(g.vertices)}")
        print(f"Triangles     : {len(g.faces)}")
        print(f"Base radius   : {g.base_radius:.6f} in")
        print(f"Base diameter : {g.base_radius * 2.0:.6f} in = {self._feet_inches(g.base_radius * 2.0)}")
        print(f"Dome height   : {g.height:.6f} in = {self._feet_inches(g.height)}")
        print("Every A/B edge is solved to the requested physical length.\n")

    def _viewports(self) -> List[Tuple[int, int, int, int]]:
        w, h = self.window_size
        if self.selected_view:
            return [(0, 0, w, h)]

        cols = 3
        rows = 2
        panel_w = w // cols
        panel_h = h // rows
        result = []

        # OpenGL viewport origin is bottom-left.  VIEWS are visually ordered
        # left-to-right on the top row, then left-to-right on the bottom row.
        for index in range(6):
            row_top = index // cols
            col = index % cols
            x = col * panel_w
            y = h - (row_top + 1) * panel_h
            vw = panel_w if col < cols - 1 else w - x
            vh = panel_h if row_top < rows - 1 else h - panel_h
            result.append((x, y, vw, vh))
        return result

    def _build_overlay(self) -> pygame.Surface:
        w, h = self.window_size
        surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        surface.fill((0, 0, 0, 0))

        # Panel borders and titles.
        viewports = self._viewports()
        specs = [VIEWS[self.selected_view - 1]] if self.selected_view else VIEWS

        for spec, gl_vp in zip(specs, viewports):
            x, gl_y, vw, vh = gl_vp
            # Convert OpenGL bottom-left viewport to pygame top-left rectangle.
            py_y = h - gl_y - vh
            rect = pygame.Rect(x, py_y, vw, vh)
            pygame.draw.rect(surface, (90, 96, 108, 180), rect, width=1)

            title_bg = pygame.Surface((min(vw - 12, 420), 30), pygame.SRCALPHA)
            title_bg.fill((8, 10, 14, 205))
            surface.blit(title_bg, (x + 6, py_y + 6))
            text = self.small_font.render(spec.title, True, (235, 238, 244))
            surface.blit(text, (x + 13, py_y + 12))

        # Global legend/status bar.
        g = self.geometry
        legend_h = 86
        legend = pygame.Surface((w, legend_h), pygame.SRCALPHA)
        legend.fill((7, 8, 11, 218))
        surface.blit(legend, (0, h - legend_h))

        # Color swatches matching the rendered struts.
        pygame.draw.line(surface, (255, 158, 46), (18, h - 63), (62, h - 63), 4)
        pygame.draw.line(surface, (51, 194, 255), (18, h - 39), (62, h - 39), 4)

        a_text = self.small_font.render(
            f"A SHORT  {g.short_length:.3f} in  x {len(g.short_edges)}",
            True,
            (241, 241, 241),
        )
        b_text = self.small_font.render(
            f"B LONG   {g.long_length:.3f} in  x {len(g.long_edges)}",
            True,
            (241, 241, 241),
        )
        surface.blit(a_text, (74, h - 72))
        surface.blit(b_text, (74, h - 48))

        dimensions = (
            f"BASE DIA {g.base_radius * 2.0:.3f} in ({self._feet_inches(g.base_radius * 2.0)})   "
            f"HEIGHT {g.height:.3f} in ({self._feet_inches(g.height)})   "
            f"65 STRUTS / 26 VERTICES / 40 TRIANGLES"
        )
        dim_text = self.tiny_font.render(dimensions, True, (202, 207, 218))
        surface.blit(dim_text, (310, h - 65))

        controls = (
            "0 multi | 1-6 single view | drag rotate 3D views | wheel zoom | "
            "F faces | H hidden-line | G grid | S screenshot | R reset | Esc quit"
        )
        ctrl_text = self.tiny_font.render(controls, True, (172, 179, 192))
        surface.blit(ctrl_text, (310, h - 39))

        flags = (
            f"faces={'ON' if self.renderer.show_faces else 'OFF'}   "
            f"hidden-line={'ON' if self.renderer.hidden_line else 'OFF'}   "
            f"grid={'ON' if self.renderer.show_grid else 'OFF'}   "
            f"zoom={self.renderer.zoom:.2f}x"
        )
        flag_text = self.tiny_font.render(flags, True, (139, 217, 172))
        surface.blit(flag_text, (310, h - 19))

        return surface

    def _refresh_overlay_if_needed(self) -> None:
        if not self.overlay_dirty:
            return
        self.renderer.set_overlay(self._build_overlay())
        self.overlay_dirty = False

    def _save_screenshot(self) -> None:
        w, h = self.window_size
        raw = self.ctx.screen.read(components=3, alignment=1)
        image = pygame.image.fromstring(raw, (w, h), "RGB", True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = Path(__file__).resolve().parent / f"geodesic_2v_views_{stamp}.png"
        pygame.image.save(image, str(out))
        print(f"Saved screenshot: {out}")

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.window_size = (max(640, event.w), max(480, event.h))
                self.overlay_dirty = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_0:
                    self.selected_view = 0
                    self.overlay_dirty = True
                elif pygame.K_1 <= event.key <= pygame.K_6:
                    self.selected_view = event.key - pygame.K_0
                    self.overlay_dirty = True
                elif event.key == pygame.K_f:
                    self.renderer.show_faces = not self.renderer.show_faces
                    self.overlay_dirty = True
                elif event.key == pygame.K_h:
                    self.renderer.hidden_line = not self.renderer.hidden_line
                    self.overlay_dirty = True
                elif event.key == pygame.K_g:
                    self.renderer.show_grid = not self.renderer.show_grid
                    self.overlay_dirty = True
                elif event.key == pygame.K_r:
                    self.renderer.reset_view()
                    self.overlay_dirty = True
                elif event.key == pygame.K_s:
                    # Screenshot is taken after this frame is rendered.
                    self._screenshot_pending = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
                self.last_mouse = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.last_mouse = event.pos
                self.renderer.yaw += dx * 0.008
                self.renderer.pitch += dy * 0.008
                self.renderer.pitch = max(math.radians(-75.0), min(math.radians(75.0), self.renderer.pitch))

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.renderer.zoom *= 1.10 ** event.y
                elif event.y < 0:
                    self.renderer.zoom /= 1.10 ** (-event.y)
                self.renderer.zoom = max(0.45, min(3.5, self.renderer.zoom))
                self.overlay_dirty = True

    def render(self) -> None:
        self.ctx.viewport = (0, 0, self.window_size[0], self.window_size[1])
        self.ctx.scissor = None
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.035, 0.042, 0.055, 1.0, depth=1.0)

        viewports = self._viewports()
        specs = [VIEWS[self.selected_view - 1]] if self.selected_view else VIEWS

        for spec, viewport in zip(specs, viewports):
            # The panels occupy disjoint screen regions, so the single full-window
            # depth clear above is sufficient for all six viewports.
            self.renderer.render_view(spec, viewport)

        self.ctx.scissor = None
        self._refresh_overlay_if_needed()
        self.renderer.render_overlay(self.window_size)

        # Read the back buffer before swapping it to the screen so screenshots
        # contain exactly the frame the user is looking at.
        if self._screenshot_pending:
            self._save_screenshot()
            self._screenshot_pending = False

        pygame.display.flip()

    def run(self) -> None:
        self._screenshot_pending = False

        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(120)

        pygame.quit()


def main() -> None:
    try:
        App().run()
    except Exception as exc:
        pygame.quit()
        print("\nERROR:")
        print(exc)
        print("\nInstall dependencies with:")
        print("    pip install pygame moderngl numpy")
        raise


if __name__ == "__main__":
    main()
