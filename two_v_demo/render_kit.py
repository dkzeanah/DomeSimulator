"""Shared rendering primitives for every masterclass lesson.

Extracted from ``app.py`` so lesson modules can build geometry batches without
importing the renderer (which imports the lessons).  Nothing here touches
OpenGL state except :class:`DynamicGpuMesh`, which needs a live context.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .geometry import normalize




SCENE_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
uniform mat4 u_mvp;
uniform vec3 u_camera;
out vec3 v_world;
out vec3 v_normal;
out vec4 v_color;
void main() {
    v_world = in_position;
    v_normal = in_normal;
    v_color = in_color;
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
"""


SCENE_FRAGMENT_SHADER = """
#version 330
in vec3 v_world;
in vec3 v_normal;
in vec4 v_color;
uniform vec3 u_camera;
uniform vec3 u_light;
out vec4 frag_color;
void main() {
    vec3 n = normalize(v_normal);
    if (!gl_FrontFacing) n = -n;
    vec3 l = normalize(-u_light);
    vec3 v = normalize(u_camera - v_world);
    vec3 h = normalize(l + v);
    float diffuse = max(dot(n, l), 0.0);
    float specular = pow(max(dot(n, h), 0.0), 42.0);
    float rim = pow(1.0 - max(dot(n, v), 0.0), 2.5);
    vec3 lit = v_color.rgb * (0.30 + 0.74 * diffuse);
    lit += vec3(0.78, 0.91, 1.0) * rim * 0.18;
    lit += vec3(1.0, 0.87, 0.64) * specular * 0.22;
    frag_color = vec4(lit, v_color.a);
}
"""


OVERLAY_VERTEX_SHADER = """
#version 330
in vec2 in_position;
out vec2 v_uv;
void main() {
    v_uv = in_position * 0.5 + 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


OVERLAY_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() {
    frag_color = texture(u_texture, v_uv);
}
"""


BG = (0.018, 0.029, 0.050, 1.0)
NAVY = (0.035, 0.069, 0.115, 1.0)
CYAN = (0.15, 0.82, 1.00, 1.0)
CYAN_SOFT = (0.15, 0.82, 1.00, 0.30)
AMBER = (1.00, 0.67, 0.20, 1.0)
AMBER_SOFT = (1.00, 0.67, 0.20, 0.28)
WHITE = (0.91, 0.95, 0.98, 1.0)
MUTED = (0.47, 0.59, 0.70, 1.0)
GREEN = (0.32, 0.91, 0.58, 1.0)
RED = (1.00, 0.34, 0.37, 1.0)
PURPLE = (0.66, 0.48, 1.00, 1.0)
SURFACE = (0.12, 0.28, 0.43, 0.14)
GROUND = (0.025, 0.052, 0.077, 1.0)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smoothstep(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(clamp(value) * math.pi)


def perspective(fov_degrees: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_degrees) * 0.5)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = f / aspect
    matrix[1, 1] = f
    matrix[2, 2] = (far + near) / (near - far)
    matrix[2, 3] = (2.0 * far * near) / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def look_at(
    eye: np.ndarray,
    target: np.ndarray,
    up_hint: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> np.ndarray:
    forward = normalize(target - eye).astype(np.float32)
    right = normalize(np.cross(forward, np.asarray(up_hint, dtype=np.float32)))
    up = normalize(np.cross(right, forward))
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, :3] = right
    matrix[1, :3] = up
    matrix[2, :3] = -forward
    matrix[0, 3] = -float(np.dot(right, eye))
    matrix[1, 3] = -float(np.dot(up, eye))
    matrix[2, 3] = float(np.dot(forward, eye))
    return matrix


def project_point(
    mvp: np.ndarray,
    point: np.ndarray | tuple[float, float, float],
    width: int,
    height: int,
) -> tuple[float, float] | None:
    clip = mvp @ np.array([point[0], point[1], point[2], 1.0], dtype=np.float32)
    if clip[3] <= 0.001:
        return None
    ndc = clip[:3] / clip[3]
    if abs(float(ndc[0])) > 1.3 or abs(float(ndc[1])) > 1.3:
        return None
    return (
        (float(ndc[0]) * 0.5 + 0.5) * width,
        (1.0 - (float(ndc[1]) * 0.5 + 0.5)) * height,
    )


@dataclass
class TriangleBatch:
    """CPU-side non-indexed triangle batch."""

    vertices: list[float] = field(default_factory=list)

    def vertex(
        self,
        position: np.ndarray | tuple[float, float, float],
        normal: np.ndarray | tuple[float, float, float],
        color: tuple[float, float, float, float],
    ) -> None:
        self.vertices.extend((
            float(position[0]), float(position[1]), float(position[2]),
            float(normal[0]), float(normal[1]), float(normal[2]),
            *color,
        ))

    def triangle(
        self,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
        color: tuple[float, float, float, float],
        normal: np.ndarray | None = None,
    ) -> None:
        if normal is None:
            normal = normalize(np.cross(b - a, c - a))
        self.vertex(a, normal, color)
        self.vertex(b, normal, color)
        self.vertex(c, normal, color)

    def quad(
        self,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
        d: np.ndarray,
        color: tuple[float, float, float, float],
        normal: np.ndarray | None = None,
    ) -> None:
        self.triangle(a, b, c, color, normal)
        self.triangle(a, c, d, color, normal)

    def cylinder(
        self,
        start: np.ndarray,
        end: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
        sides: int = 8,
    ) -> None:
        axis = np.asarray(end, dtype=np.float64) - np.asarray(start, dtype=np.float64)
        length = float(np.linalg.norm(axis))
        if length <= 1e-8:
            return
        direction = axis / length
        trial = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(direction, trial))) > 0.88:
            trial = np.array([0.0, 1.0, 0.0])
        tangent = normalize(np.cross(direction, trial))
        bitangent = normalize(np.cross(direction, tangent))
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        ring_a: list[np.ndarray] = []
        ring_b: list[np.ndarray] = []
        normals: list[np.ndarray] = []
        for index in range(sides):
            angle = math.tau * index / sides
            normal = tangent * math.cos(angle) + bitangent * math.sin(angle)
            normals.append(normal)
            ring_a.append(start + normal * radius)
            ring_b.append(end + normal * radius)
        for index in range(sides):
            nxt = (index + 1) % sides
            self.triangle(ring_a[index], ring_b[index], ring_b[nxt], color, normals[index])
            self.triangle(ring_a[index], ring_b[nxt], ring_a[nxt], color, normals[nxt])
        for index in range(1, sides - 1):
            self.triangle(start, ring_a[index + 1], ring_a[index], color, -direction)
            self.triangle(end, ring_b[index], ring_b[index + 1], color, direction)

    def cone(
        self,
        base: np.ndarray,
        tip: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
        sides: int = 10,
    ) -> None:
        axis = np.asarray(tip) - np.asarray(base)
        if float(np.linalg.norm(axis)) <= 1e-8:
            return
        direction = normalize(axis)
        trial = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(direction, trial))) > 0.88:
            trial = np.array([0.0, 1.0, 0.0])
        tangent = normalize(np.cross(direction, trial))
        bitangent = normalize(np.cross(direction, tangent))
        ring = []
        for index in range(sides):
            angle = math.tau * index / sides
            ring.append(base + radius * (
                tangent * math.cos(angle) + bitangent * math.sin(angle)
            ))
        for index in range(sides):
            nxt = (index + 1) % sides
            self.triangle(ring[index], tip, ring[nxt], color)
        for index in range(1, sides - 1):
            self.triangle(base, ring[index], ring[index + 1], color, -direction)

    def arrow(
        self,
        start: np.ndarray,
        end: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
    ) -> None:
        direction = normalize(np.asarray(end) - np.asarray(start))
        length = float(np.linalg.norm(np.asarray(end) - np.asarray(start)))
        head_length = min(length * 0.34, radius * 6.0)
        shoulder = np.asarray(end) - direction * head_length
        self.cylinder(np.asarray(start), shoulder, radius, color, 8)
        self.cone(shoulder, np.asarray(end), radius * 2.4, color, 10)

    def sphere(
        self,
        center: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
        rings: int = 5,
        segments: int = 8,
    ) -> None:
        center = np.asarray(center, dtype=np.float64)
        for ring in range(rings):
            latitude_a = -math.pi * 0.5 + math.pi * ring / rings
            latitude_b = -math.pi * 0.5 + math.pi * (ring + 1) / rings
            for segment in range(segments):
                longitude_a = math.tau * segment / segments
                longitude_b = math.tau * (segment + 1) / segments

                def point(latitude: float, longitude: float) -> np.ndarray:
                    return np.array([
                        math.cos(latitude) * math.cos(longitude),
                        math.cos(latitude) * math.sin(longitude),
                        math.sin(latitude),
                    ])

                na = point(latitude_a, longitude_a)
                nb = point(latitude_a, longitude_b)
                nc = point(latitude_b, longitude_b)
                nd = point(latitude_b, longitude_a)
                self.triangle(center + na * radius, center + nb * radius,
                              center + nc * radius, color, normalize(na + nb + nc))
                self.triangle(center + na * radius, center + nc * radius,
                              center + nd * radius, color, normalize(na + nc + nd))

    def box(
        self,
        center: np.ndarray | tuple[float, float, float],
        size: np.ndarray | tuple[float, float, float],
        color: tuple[float, float, float, float],
    ) -> None:
        center = np.asarray(center, dtype=np.float64)
        half = np.asarray(size, dtype=np.float64) * 0.5
        corners = np.array([
            center + [x * half[0], y * half[1], z * half[2]]
            for x, y, z in (
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
            )
        ])
        for indices in (
            (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        ):
            self.quad(*(corners[index] for index in indices), color)

    def disc(
        self,
        center: np.ndarray,
        radius: float,
        color: tuple[float, float, float, float],
        segments: int = 48,
    ) -> None:
        center = np.asarray(center, dtype=np.float64)
        for index in range(segments):
            a = math.tau * index / segments
            b = math.tau * (index + 1) / segments
            pa = center + np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
            pb = center + np.array([radius * math.cos(b), radius * math.sin(b), 0.0])
            self.triangle(center, pa, pb, color, np.array([0.0, 0.0, 1.0]))


class DynamicGpuMesh:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.buffer = ctx.buffer(reserve=4 * 1024 * 1024, dynamic=True)
        self.vao = ctx.vertex_array(
            program,
            [(self.buffer, "3f 3f 4f", "in_position", "in_normal", "in_color")],
        )

    def draw(self, batch: TriangleBatch) -> None:
        if not batch.vertices:
            return
        data = np.asarray(batch.vertices, dtype="f4")
        required = data.nbytes
        if required > self.buffer.size:
            self.vao.release()
            self.buffer.release()
            capacity = max(required, int(required * 1.35))
            self.buffer = self.ctx.buffer(reserve=capacity, dynamic=True)
            self.vao = self.ctx.vertex_array(
                self.program,
                [(self.buffer, "3f 3f 4f", "in_position", "in_normal", "in_color")],
            )
        self.buffer.write(data.tobytes())
        self.vao.render(vertices=len(batch.vertices) // 10)


@dataclass
class WorldLabel:
    point: np.ndarray
    text: str
    color: tuple[int, int, int]

