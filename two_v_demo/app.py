"""ModernGL renderer for the standalone masterclass lessons.

One renderer, several lessons.  ``MasterclassApp`` knows how to play a
:class:`~two_v_demo.lessons.Lesson`: it walks the lesson's chapters, asks
the lesson to paint each stage, and asks it for any live figures the
chapter wants under its fixed equations.  The 2V geodesic lesson is the
default and is still drawn by the ``scene_*`` methods below; the hex,
zome and construction lessons supply their own painters.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

import launcher_common as _lc
from .geometry import (
    MM_PER_INCH,
    PHI,
    DomeMeasurements,
    build_demo_geometry,
    calculation_report,
    fit_measurements,
    normalize,
    platonic_solids,
    validate_geometry,
)
from .export import export_build_packet
from .audio import (
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    NarrationPlan,
    SPEECH_DELAY,
    companion_ffprobe,
    list_neural_voices,
    resolve_executable,
    synthesize_narration,
    synthesize_preview,
    voice_cache_slug,
)
from .lessons import (
    TWO_V_LESSON,
    Lesson,
    chapter_at_time,
    chapter_start,
    timeline_duration,
)
from .deliverables import deliverables_menu, render_all, validate_deliverables
from .segments import compose, segment_menu, validate_segments
from .narration import narration_script, subtitle_file, write_companion_files
from .render_kit import (
    AMBER,
    AMBER_SOFT,
    BG,
    CYAN,
    CYAN_SOFT,
    GREEN,
    GROUND,
    MUTED,
    NAVY,
    OVERLAY_FRAGMENT_SHADER,
    OVERLAY_VERTEX_SHADER,
    PURPLE,
    RED,
    SCENE_FRAGMENT_SHADER,
    SCENE_VERTEX_SHADER,
    SURFACE,
    WHITE,
    DynamicGpuMesh,
    TriangleBatch,
    WorldLabel,
    clamp,
    ease_in_out,
    look_at,
    perspective,
    project_point,
    smoothstep,
)

class MasterclassApp:
    """Interactive presenter and deterministic video renderer."""

    def __init__(
        self,
        size: tuple[int, int] = (1600, 900),
        fullscreen: bool = False,
        hidden: bool = False,
        lesson: Lesson | None = None,
    ) -> None:
        try:
            import pygame
            import moderngl
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The 2V demo needs pygame and moderngl. Install with: "
                "py -3.12 -m pip install pygame moderngl numpy"
            ) from exc
        self.pygame = pygame
        self.moderngl = moderngl
        pygame.init()
        pygame.font.init()
        self.fullscreen = fullscreen
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            display_size = (0, 0)
        else:
            flags |= pygame.RESIZABLE
            display_size = size
        if hidden and hasattr(pygame, "HIDDEN"):
            flags |= pygame.HIDDEN
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        self.lesson = lesson or TWO_V_LESSON
        self.lesson.validate()
        self.chapters = self.lesson.chapters
        pygame.display.set_caption(self.lesson.title)
        pygame.display.set_mode(display_size, flags)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE | moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.scene_program = self.ctx.program(
            vertex_shader=SCENE_VERTEX_SHADER,
            fragment_shader=SCENE_FRAGMENT_SHADER,
        )
        self.overlay_program = self.ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER,
        )
        self.opaque_mesh = DynamicGpuMesh(self.ctx, self.scene_program)
        self.transparent_mesh = DynamicGpuMesh(self.ctx, self.scene_program)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
        self.overlay_buffer = self.ctx.buffer(quad.tobytes())
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program,
            [(self.overlay_buffer, "2f", "in_position")],
        )
        self.overlay_texture = None
        self.overlay_size = (0, 0)
        self.geometry = build_demo_geometry()
        self.fit = fit_measurements(72.0, 63.5)
        self.measurements = DomeMeasurements(self.fit.best_fit_radius)
        self.solids = platonic_solids()
        self.edge_class = {
            edge: name
            for edge, name in zip(
                self.geometry.edges, self.geometry.edge_class_by_edge
            )
        }
        self.timeline = 0.0
        self.chapter_durations = tuple(
            chapter.duration for chapter in self.chapters
        )
        self.total_duration = timeline_duration(
            self.chapter_durations, self.chapters
        )
        self.playing = True
        self.playback_speed = 1.0
        self.exporting = False
        self.narration_active = False
        self.chapter_index = 0
        self.chapter_progress = 0.0
        self.camera_yaw = self.chapters[0].camera[0]
        self.camera_pitch = self.chapters[0].camera[1]
        self.camera_distance = self.chapters[0].camera[2]
        self.camera_override = False
        self.xray = True
        self.metric = False
        self.dragging = False
        self.last_mouse = (0, 0)
        self.world_labels: list[WorldLabel] = []
        self.font_cache: dict[tuple[int, bool], object] = {}
        self.ui_buttons: dict[str, object] = {}
        self.mvp = np.eye(4, dtype=np.float32)
        self.last_frame_time = time.perf_counter()
        self.output_dir = Path("two_v_demo_output")
        self.stage_state: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Geometry drawing helpers
    # ------------------------------------------------------------------

    def add_ground(self, opaque: TriangleBatch) -> None:
        opaque.box((0.0, 0.0, -0.20), (36.0, 28.0, 0.28), GROUND)
        grid_color = (0.08, 0.18, 0.24, 1.0)
        for value in range(-16, 17, 2):
            opaque.cylinder(
                np.array([value, -12.0, -0.045]),
                np.array([value, 12.0, -0.045]),
                0.012, grid_color, 5,
            )
        for value in range(-12, 13, 2):
            opaque.cylinder(
                np.array([-16.0, value, -0.044]),
                np.array([16.0, value, -0.044]),
                0.012, grid_color, 5,
            )
        # A visual center mark keeps camera motion legible.
        for angle in np.linspace(0.0, math.tau, 40, endpoint=False):
            a = np.array([6.4 * math.cos(angle), 6.4 * math.sin(angle), -0.035])
            b_angle = angle + math.tau / 40
            b = np.array([6.4 * math.cos(b_angle), 6.4 * math.sin(b_angle), -0.035])
            opaque.cylinder(a, b, 0.018, (0.08, 0.32, 0.42, 1.0), 5)

    def add_edges(
        self,
        batch: TriangleBatch,
        vertices: np.ndarray,
        edges: Iterable[tuple[int, int]],
        scale: float,
        offset: np.ndarray,
        color: tuple[float, float, float, float],
        radius: float = 0.055,
        colors: dict[tuple[int, int], tuple[float, float, float, float]] | None = None,
        reveal: float = 1.0,
    ) -> None:
        edge_list = list(edges)
        reveal_count = int(math.ceil(len(edge_list) * clamp(reveal)))
        for index, edge in enumerate(edge_list):
            if index >= reveal_count:
                break
            edge_color = colors.get(edge, color) if colors else color
            a = vertices[edge[0]] * scale + offset
            b = vertices[edge[1]] * scale + offset
            if reveal_count and index == reveal_count - 1 and reveal < 1.0:
                fraction = len(edge_list) * reveal - math.floor(len(edge_list) * reveal)
                if fraction > 0.02:
                    b = a + (b - a) * fraction
            batch.cylinder(a, b, radius, edge_color, 8)

    def add_nodes(
        self,
        batch: TriangleBatch,
        vertices: np.ndarray,
        scale: float,
        offset: np.ndarray,
        color: tuple[float, float, float, float],
        radius: float = 0.10,
        subset: Iterable[int] | None = None,
    ) -> None:
        indices = subset if subset is not None else range(len(vertices))
        for index in indices:
            batch.sphere(vertices[index] * scale + offset, radius, color, 4, 8)

    def add_face_shell(
        self,
        batch: TriangleBatch,
        vertices: np.ndarray,
        faces: np.ndarray,
        scale: float,
        offset: np.ndarray,
        color: tuple[float, float, float, float],
        reveal: float = 1.0,
    ) -> None:
        count = int(math.ceil(len(faces) * clamp(reveal)))
        for face in faces[:count]:
            a, b, c = (vertices[int(index)] * scale + offset for index in face)
            batch.triangle(a, b, c, color, normalize(a + b + c - offset * 3.0))

    def add_latitude_sphere(
        self,
        batch: TriangleBatch,
        radius: float,
        center: np.ndarray,
        hemisphere: bool = False,
        alpha: float = 0.08,
    ) -> None:
        latitudes = 8
        longitudes = 24
        start = 0.0 if hemisphere else -math.pi * 0.5
        end = math.pi * 0.5
        for latitude_index in range(latitudes):
            lat_a = start + (end - start) * latitude_index / latitudes
            lat_b = start + (end - start) * (latitude_index + 1) / latitudes
            for longitude_index in range(longitudes):
                lon_a = math.tau * longitude_index / longitudes
                lon_b = math.tau * (longitude_index + 1) / longitudes

                def point(latitude: float, longitude: float) -> np.ndarray:
                    return center + radius * np.array([
                        math.cos(latitude) * math.cos(longitude),
                        math.cos(latitude) * math.sin(longitude),
                        math.sin(latitude),
                    ])

                a, b = point(lat_a, lon_a), point(lat_a, lon_b)
                c, d = point(lat_b, lon_b), point(lat_b, lon_a)
                batch.triangle(a, b, c, (0.16, 0.68, 0.95, alpha),
                               normalize(a + b + c - center * 3.0))
                batch.triangle(a, c, d, (0.16, 0.68, 0.95, alpha),
                               normalize(a + c + d - center * 3.0))

    def add_dimension(
        self,
        batch: TriangleBatch,
        a: np.ndarray,
        b: np.ndarray,
        color: tuple[float, float, float, float],
        label: str,
    ) -> None:
        batch.cylinder(a, b, 0.025, color, 6)
        direction = normalize(b - a)
        batch.cone(a + direction * 0.45, a, 0.11, color, 8)
        batch.cone(b - direction * 0.45, b, 0.11, color, 8)
        self.world_labels.append(WorldLabel((a + b) * 0.5, label, (
            int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        )))

    def dome_class_colors(self) -> dict[tuple[int, int], tuple[float, float, float, float]]:
        colors: dict[tuple[int, int], tuple[float, float, float, float]] = {}
        for edge in self.geometry.edges:
            colors[edge] = CYAN if self.edge_class[edge] == "SHORT" else AMBER
        return colors

    # ------------------------------------------------------------------
    # Lesson scenes
    # ------------------------------------------------------------------

    def build_scene(
        self, stage: str, progress: float
    ) -> tuple[TriangleBatch, TriangleBatch]:
        opaque = TriangleBatch()
        transparent = TriangleBatch()
        self.world_labels = []
        self.add_ground(opaque)
        painter = self.lesson.scenes.get(stage)
        if painter is not None:
            painter(self, opaque, transparent, progress)
        else:
            getattr(self, f"scene_{stage}")(opaque, transparent, progress)
        return opaque, transparent

    def scene_hero(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        center = np.array([0.0, 0.0, 0.0])
        self.add_latitude_sphere(transparent, scale, center, True, 0.075)
        self.add_face_shell(transparent, self.geometry.vertices,
                            self.geometry.hemisphere_faces, scale, center,
                            (0.08, 0.35, 0.52, 0.12))
        self.add_edges(opaque, self.geometry.vertices, self.geometry.hemisphere_edges,
                       scale, center, WHITE, 0.065, self.dome_class_colors(),
                       smoothstep(p * 1.5))
        self.add_nodes(opaque, self.geometry.vertices, scale, center,
                       (0.77, 0.86, 0.91, 1.0), 0.105,
                       sorted({i for edge in self.geometry.hemisphere_edges for i in edge}))
        # The supplied boards sit beside the mathematical dome.
        opaque.box((-7.2, 0.0, 1.25), (0.32, 0.75, 6.0), AMBER)
        opaque.box((-6.1, 0.0, 1.25), (0.32, 0.75, 5.29), CYAN)
        self.world_labels.extend([
            WorldLabel(np.array([-7.2, 0.0, 4.5]), "A / LONG  72.0 in", (255, 177, 62)),
            WorldLabel(np.array([-6.1, 0.0, 4.15]), "B / SHORT  63.5 in", (61, 211, 255)),
        ])

    def scene_rigidity(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        triangle = np.array([[-6.0, 0.0, 0.2], [-1.0, 0.0, 0.2], [-3.5, 0.0, 4.8]])
        square = np.array([[1.0, 0.0, 0.2], [6.0, 0.0, 0.2],
                           [6.0, 0.0, 4.8], [1.0, 0.0, 4.8]])
        for index in range(3):
            opaque.cylinder(triangle[index], triangle[(index + 1) % 3], 0.10, CYAN, 10)
        shear = math.sin(p * math.tau) * 0.65
        moving_square = square.copy()
        moving_square[2:, 0] += shear
        for index in range(4):
            opaque.cylinder(moving_square[index], moving_square[(index + 1) % 4],
                            0.10, AMBER, 10)
        load = np.array([-3.5, 0.0, 6.5])
        opaque.arrow(load, triangle[2] + np.array([0.0, 0.0, 0.3]), 0.08, RED)
        for endpoint in triangle[:2]:
            opaque.arrow(triangle[2] * 0.88 + endpoint * 0.12,
                         endpoint * 0.60 + triangle[2] * 0.40,
                         0.055, GREEN)
        self.world_labels.extend([
            WorldLabel(np.array([-3.5, 0.0, 5.35]), "TRIANGLE: fixed geometry", (61, 211, 255)),
            WorldLabel(np.array([3.5, 0.0, 5.35]), "SQUARE: shears without a brace", (255, 177, 62)),
        ])

    def scene_platonic(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        positions = np.linspace(-9.2, 9.2, 5)
        phase = ease_in_out(min(1.0, p * 1.8))
        for index, (solid, x) in enumerate(zip(self.solids, positions)):
            center = np.array([x, 0.0, 2.5])
            scale = 1.65 + index * 0.04
            rotated = solid.vertices.copy()
            angle = p * math.tau * (0.12 + index * 0.015)
            rotation = np.array([
                [math.cos(angle), -math.sin(angle), 0.0],
                [math.sin(angle), math.cos(angle), 0.0],
                [0.0, 0.0, 1.0],
            ])
            rotated = rotated @ rotation.T
            color = CYAN if solid.name == "Icosahedron" else (
                0.34, 0.48, 0.61, 1.0
            )
            self.add_edges(opaque, rotated, solid.edges, scale, center, color,
                           0.045 if index < 4 else 0.075, reveal=phase)
            self.add_nodes(opaque, rotated, scale, center, color,
                           0.08 if index < 4 else 0.12)
            self.world_labels.append(WorldLabel(
                center + np.array([0.0, 0.0, -2.2]),
                f"{solid.name}\n{solid.faces} faces",
                (61, 211, 255) if solid.name == "Icosahedron" else (145, 165, 182),
            ))

    def scene_coordinates(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 2.75
        center = np.array([0.0, 0.0, 2.8])
        vertices = self.geometry.raw_vertices.copy()
        reveal = smoothstep(p * 1.7)
        self.add_edges(opaque, vertices, self.geometry.ico_edges, scale / 1.902113,
                       center, PURPLE, 0.055, reveal=reveal)
        self.add_nodes(opaque, vertices, scale / 1.902113, center, WHITE, 0.10)
        axes = (
            (np.array([5.5, 0.0, 0.0]), RED, "x"),
            (np.array([0.0, 5.5, 0.0]), GREEN, "y"),
            (np.array([0.0, 0.0, 5.5]), CYAN, "z"),
        )
        for vector, color, label in axes:
            opaque.arrow(center, center + vector, 0.035, color)
            self.world_labels.append(WorldLabel(center + vector, label, (
                int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
            )))
        selected = 4
        point = vertices[selected] * scale / 1.902113 + center
        opaque.sphere(point, 0.19, AMBER, 6, 10)
        self.world_labels.append(WorldLabel(point + np.array([0.0, 0.0, 0.45]),
                                            "(0, -1, phi)", (255, 177, 62)))

    def scene_icosahedron(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        center = np.array([0.0, 0.0, 0.0])
        self.add_latitude_sphere(transparent, scale, center, False, 0.075)
        self.add_face_shell(transparent, self.geometry.ico_vertices,
                            self.geometry.base_faces, scale, center,
                            (0.43, 0.31, 0.72, 0.13))
        self.add_edges(opaque, self.geometry.ico_vertices, self.geometry.ico_edges,
                       scale, center, PURPLE, 0.085,
                       reveal=smoothstep(p * 1.5))
        self.add_nodes(opaque, self.geometry.ico_vertices, scale, center, WHITE, 0.13)
        edge = self.geometry.ico_edges[8]
        a = self.geometry.ico_vertices[edge[0]] * scale
        b = self.geometry.ico_vertices[edge[1]] * scale
        opaque.cylinder(a, b, 0.13, AMBER, 12)
        self.world_labels.append(WorldLabel((a + b) * 0.5, "1.051462 R", (255, 177, 62)))

    def scene_midpoints(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        center = np.zeros(3)
        self.add_latitude_sphere(transparent, scale, center, False, 0.055)
        self.add_edges(opaque, self.geometry.ico_vertices, self.geometry.ico_edges,
                       scale, center, (0.40, 0.47, 0.57, 1.0), 0.045)
        t = ease_in_out(min(1.0, p * 1.5))
        for index, edge in enumerate(self.geometry.ico_edges):
            midpoint = (
                self.geometry.ico_vertices[edge[0]]
                + self.geometry.ico_vertices[edge[1]]
            ) * 0.5
            if index / len(self.geometry.ico_edges) <= t:
                opaque.sphere(midpoint * scale, 0.105, CYAN, 4, 8)
        focus_edge = self.geometry.ico_edges[6]
        midpoint = (
            self.geometry.ico_vertices[focus_edge[0]]
            + self.geometry.ico_vertices[focus_edge[1]]
        ) * 0.5
        opaque.arrow(np.zeros(3), midpoint * scale, 0.035, AMBER)
        self.world_labels.append(WorldLabel(midpoint * scale * 0.55,
                                            "||m|| = 0.850651 R", (255, 177, 62)))

    def scene_projection(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        center = np.zeros(3)
        self.add_latitude_sphere(transparent, scale, center, False, 0.08)
        projection = ease_in_out(clamp((p - 0.12) / 0.72))
        moving = self.geometry.flat_midpoints.copy()
        moving[12:] = (
            moving[12:] * (1.0 - projection)
            + self.geometry.vertices[12:] * projection
        )
        self.add_edges(opaque, moving, self.geometry.edges, scale, center,
                       (0.58, 0.70, 0.78, 1.0), 0.048,
                       reveal=smoothstep(p * 1.5))
        self.add_nodes(opaque, moving, scale, center, CYAN, 0.085, range(12, 42))
        # Show a handful of radial projection vectors clearly.
        for index in range(12, 42, 6):
            a = self.geometry.flat_midpoints[index] * scale
            b = self.geometry.vertices[index] * scale
            opaque.arrow(a, b, 0.035, AMBER)
        self.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 5.7]), f"RADIAL PROJECTION  {projection * 100:3.0f}%",
            (255, 177, 62),
        ))

    def scene_classes(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        self.add_latitude_sphere(transparent, scale, np.zeros(3), True,
                                 0.035 if self.xray else 0.13)
        self.add_face_shell(transparent, self.geometry.vertices,
                            self.geometry.hemisphere_faces, scale, np.zeros(3),
                            (0.10, 0.32, 0.45, 0.10))
        self.add_edges(opaque, self.geometry.vertices, self.geometry.hemisphere_edges,
                       scale, np.zeros(3), WHITE, 0.075,
                       self.dome_class_colors(), smoothstep(p * 1.4))
        short_edge = next(edge for edge in self.geometry.hemisphere_edges
                          if self.edge_class[edge] == "SHORT")
        long_edge = next(edge for edge in self.geometry.hemisphere_edges
                         if self.edge_class[edge] == "LONG")
        for edge, label, color in (
            (short_edge, "SHORT  0.546533 R", CYAN),
            (long_edge, "LONG  0.618034 R", AMBER),
        ):
            a, b = (self.geometry.vertices[index] * scale for index in edge)
            opaque.cylinder(a, b, 0.14, color, 12)
            self.world_labels.append(WorldLabel((a + b) * 0.5, label, (
                int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
            )))

    def scene_derivations(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        # Use a real SHORT edge as the chord of a unit-radius teaching circle.
        edge = next(edge for edge in self.geometry.edges
                    if self.edge_class[edge] == "SHORT")
        u = self.geometry.vertices[edge[0]]
        v = self.geometry.vertices[edge[1]]
        # Rotate the actual configuration for a readable central-angle view.
        normal = normalize(np.cross(u, v))
        axis_x = normalize(u + v)
        axis_y = normalize(np.cross(normal, axis_x))
        scale = 5.0
        center = np.array([0.0, 0.0, 0.2])
        theta = math.acos(float(np.dot(u, v)))
        half = theta * 0.5
        a = center + scale * (axis_x * math.cos(half) - axis_y * math.sin(half))
        b = center + scale * (axis_x * math.cos(half) + axis_y * math.sin(half))
        opaque.cylinder(center, a, 0.045, MUTED, 7)
        opaque.cylinder(center, b, 0.045, MUTED, 7)
        opaque.cylinder(a, b, 0.12, CYAN, 12)
        opaque.sphere(center, 0.15, WHITE, 5, 9)
        opaque.sphere(a, 0.13, CYAN, 5, 9)
        opaque.sphere(b, 0.13, CYAN, 5, 9)
        # Arc inside the angle.
        for index in range(18):
            angle_a = -half + theta * index / 18
            angle_b = -half + theta * (index + 1) / 18
            pa = center + 1.45 * (
                axis_x * math.cos(angle_a) + axis_y * math.sin(angle_a)
            )
            pb = center + 1.45 * (
                axis_x * math.cos(angle_b) + axis_y * math.sin(angle_b)
            )
            opaque.cylinder(pa, pb, 0.03, AMBER, 6)
        self.world_labels.extend([
            WorldLabel((a + b) * 0.5 + np.array([0.0, 0.0, 0.45]),
                       "chord c", (61, 211, 255)),
            WorldLabel(center + axis_x * 1.9, f"theta = {math.degrees(theta):.3f} deg",
                       (255, 177, 62)),
            WorldLabel(center + (a - center) * 0.52, "R", (145, 165, 182)),
        ])

    def scene_audit(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        # Two dimensionally honest bars, scaled relative to one another.
        # The relative lengths are exact; the display scale is reduced so the
        # tops and their labels stay inside a 16:9 title-safe frame.
        long_visual = 5.5
        short_visual = long_visual * 63.5 / 72.0
        base_z = 0.55
        opaque.box((-2.2, 0.0, base_z + long_visual * 0.5),
                   (0.55, 0.9, long_visual), AMBER)
        opaque.box((2.2, 0.0, base_z + short_visual * 0.5),
                   (0.55, 0.9, short_visual), CYAN)
        self.world_labels.extend([
            WorldLabel(np.array([-2.2, 0.0, base_z + long_visual + 0.4]),
                       "MEASURED LONG  72.000 in", (255, 177, 62)),
            WorldLabel(np.array([2.2, 0.0, base_z + short_visual + 0.4]),
                       "MEASURED SHORT  63.500 in", (61, 211, 255)),
            WorldLabel(np.array([-2.2, 0.0, 0.45]),
                       f"implied R  {self.fit.radius_from_long:.3f} in", (255, 177, 62)),
            WorldLabel(np.array([2.2, 0.0, 0.45]),
                       f"implied R  {self.fit.radius_from_short:.3f} in", (61, 211, 255)),
        ])
        # Residual scale in the middle.
        opaque.cylinder(np.array([-0.65, 0.0, 3.3]), np.array([0.65, 0.0, 3.3]),
                        0.035, WHITE, 6)
        marker = (self.fit.long_residual - self.fit.short_residual) * 2.0
        opaque.sphere(np.array([clamp(marker, -0.6, 0.6), 0.0, 3.3]),
                      0.14, GREEN, 5, 9)
        self.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 3.8]),
            f"BEST-FIT R  {self.fit.best_fit_radius:.3f} in", (111, 235, 155),
        ))

    def scene_cutlist(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        # A visual stock rack: all 65 members are present and countable.
        short_length = 1.65
        long_length = short_length * self.geometry.ratio
        reveal = int(65 * smoothstep(p * 1.45))
        count = 0
        for group, amount, length, color, x_offset in (
            ("SHORT", 30, short_length, CYAN, -5.6),
            ("LONG", 35, long_length, AMBER, 1.0),
        ):
            for index in range(amount):
                if count >= reveal:
                    break
                column = index % 5
                row = index // 5
                x = x_offset + column * 0.90
                y = (row - 3.0) * 0.52
                z = 0.45 + column * 0.10
                opaque.cylinder(
                    np.array([x, y, z]),
                    np.array([x + length, y, z]),
                    0.055, color, 7,
                )
                count += 1
            self.world_labels.append(WorldLabel(
                np.array([x_offset + 2.0, -2.6, 1.2]),
                f"{amount} x {group}", (
                    int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
                ),
            ))
        unit = "mm" if self.metric else "in"
        multiplier = MM_PER_INCH if self.metric else 1.0
        self.world_labels.extend([
            WorldLabel(np.array([-3.6, 2.4, 1.4]),
                       f"{self.measurements.short_center_length * multiplier:.2f} {unit}",
                       (61, 211, 255)),
            WorldLabel(np.array([3.0, 2.4, 1.4]),
                       f"{self.measurements.long_center_length * multiplier:.2f} {unit}",
                       (255, 177, 62)),
        ])

    def scene_assembly(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        # Reveal by altitude, which reads as an actual base-to-apex sequence.
        edge_records = []
        for edge in self.geometry.hemisphere_edges:
            midpoint_z = float(np.mean(self.geometry.vertices[list(edge), 2]))
            edge_records.append((midpoint_z, edge))
        edge_records.sort()
        reveal = smoothstep(p)
        count = int(math.ceil(len(edge_records) * reveal))
        colors = self.dome_class_colors()
        for _, edge in edge_records[:count]:
            a, b = (self.geometry.vertices[index] * scale for index in edge)
            opaque.cylinder(a, b, 0.078, colors[edge], 9)
        built_vertices = sorted({i for _, edge in edge_records[:count] for i in edge})
        self.add_nodes(opaque, self.geometry.vertices, scale, np.zeros(3),
                       WHITE, 0.10, built_vertices)
        face_records = sorted(
            self.geometry.hemisphere_faces,
            key=lambda face: float(np.mean(self.geometry.vertices[face, 2])),
        )
        face_count = max(0, int(len(face_records) * (reveal - 0.14) / 0.86))
        if face_count:
            self.add_face_shell(transparent, self.geometry.vertices,
                                np.asarray(face_records[:face_count]), scale,
                                np.zeros(3), (0.11, 0.48, 0.62, 0.15))
        self.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 5.8]),
            f"BASE-TO-APEX BUILD  {count:02d} / 65 STRUTS", (111, 235, 155),
        ))

    def scene_verification(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        self.add_latitude_sphere(transparent, scale, np.zeros(3), True, 0.055)
        self.add_edges(opaque, self.geometry.vertices, self.geometry.hemisphere_edges,
                       scale, np.zeros(3), WHITE, 0.055, self.dome_class_colors())
        self.add_dimension(opaque, np.array([-5.0, -0.8, 0.0]),
                           np.array([5.0, -0.8, 0.0]), AMBER, "DIAMETER = 2R")
        self.add_dimension(opaque, np.array([0.0, 0.8, 0.0]),
                           np.array([0.0, 0.8, 5.0]), CYAN, "HEIGHT = R")
        # Base diagonal cross checks.
        ring = self.geometry.base_ring
        for offset in (0, 2):
            a = self.geometry.vertices[ring[offset]] * scale
            b = self.geometry.vertices[ring[(offset + 5) % 10]] * scale
            opaque.cylinder(a, b, 0.035, GREEN, 6)

    def scene_finale(self, opaque: TriangleBatch, transparent: TriangleBatch, p: float) -> None:
        scale = 5.0
        if p < 0.28:
            local = p / 0.28
            self.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.045)
            self.add_edges(opaque, self.geometry.ico_vertices, self.geometry.ico_edges,
                           scale, np.zeros(3), PURPLE, 0.08,
                           reveal=smoothstep(local))
        elif p < 0.62:
            local = (p - 0.28) / 0.34
            moving = self.geometry.flat_midpoints.copy()
            amount = ease_in_out(local)
            moving[12:] = moving[12:] * (1 - amount) + self.geometry.vertices[12:] * amount
            self.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.06)
            self.add_edges(opaque, moving, self.geometry.edges, scale,
                           np.zeros(3), WHITE, 0.055,
                           self.dome_class_colors(), smoothstep(local * 1.4))
        else:
            local = (p - 0.62) / 0.38
            self.add_latitude_sphere(transparent, scale, np.zeros(3), True, 0.055)
            self.add_face_shell(transparent, self.geometry.vertices,
                                self.geometry.hemisphere_faces, scale, np.zeros(3),
                                (0.10, 0.39, 0.53, 0.13), smoothstep(local))
            self.add_edges(opaque, self.geometry.vertices,
                           self.geometry.hemisphere_edges, scale, np.zeros(3),
                           WHITE, 0.075, self.dome_class_colors())
        self.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 5.9]),
            "ONE UNIT MODEL  x  ONE RADIUS  =  EVERY 2V SCALE", (111, 235, 155),
        ))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def font(self, size: int, bold: bool = False):
        key = (size, bold)
        if key not in self.font_cache:
            family = "Segoe UI"
            self.font_cache[key] = self.pygame.font.SysFont(family, size, bold=bold)
        return self.font_cache[key]

    def draw_text(
        self,
        surface,
        text: str,
        position: tuple[int, int],
        size: int,
        color: tuple[int, int, int],
        bold: bool = False,
    ) -> object:
        rendered = self.font(size, bold).render(text, True, color)
        surface.blit(rendered, position)
        return rendered.get_rect(topleft=position)

    def wrap_text(self, text: str, font, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def rounded_panel(self, surface, rect, color, border=None, radius=12) -> None:
        self.pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border is not None:
            self.pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)

    def dynamic_equations(self, stage: str) -> list[str]:
        # The built-in figures below belong to the 2V stages.  A lesson that
        # reuses one of those stages gets them for free; anything else gets
        # only what its own table returns.
        equations: list[str] = []
        if stage == "audit":
            equations.extend([
                f"measured LONG / SHORT = {self.fit.measured_ratio:.6f}",
                f"theoretical ratio     = {self.fit.theoretical_ratio:.6f}",
                f"best-fit radius       = {self.fit.best_fit_radius:.3f} in",
                f"predicted LONG         = {self.fit.predicted_long:.3f} in",
                f"predicted SHORT        = {self.fit.predicted_short:.3f} in",
                f"residuals              = {self.fit.long_residual:+.3f}, "
                f"{self.fit.short_residual:+.3f} in",
            ])
        elif stage == "cutlist":
            unit = "mm" if self.metric else "in"
            multiplier = MM_PER_INCH if self.metric else 1.0
            equations.extend([
                f"R = {self.measurements.radius * multiplier:.3f} {unit}",
                f"30 SHORT @ {self.measurements.short_center_length * multiplier:.3f} {unit}",
                f"35 LONG  @ {self.measurements.long_center_length * multiplier:.3f} {unit}",
                "physical cuts = these lengths - hub deduction",
            ])
        elif stage == "classes":
            equations.extend([
                f"SHORT count = 30    factor = {self.geometry.short_factor:.9f} R",
                f"LONG count  = 35    factor = {self.geometry.long_factor:.9f} R",
                f"ratio = {self.geometry.ratio:.9f}",
            ])
        elif stage == "assembly":
            equations.extend([
                "panels: 30 SHORT-SHORT-LONG + 10 LONG-LONG-LONG",
                "struts: 30 SHORT + 35 LONG = 65 unique edges",
                "hubs: 10 base + 15 upper + 1 apex = 26",
            ])
        if self.lesson.equations is not None:
            equations.extend(self.lesson.equations(self, stage))
        return equations

    @staticmethod
    def _equation_key(text: str) -> str:
        """Reduce an equation to its content, ignoring spacing and symbols."""
        return "".join(character for character in text.lower()
                       if character.isalnum())

    def merge_equations(self, chapter) -> list[str]:
        """The chapter's fixed equations, plus any live ones that add something.

        A lesson often states a figure in the chapter and then computes the
        same figure live.  Printing both wastes half the card, so a live
        line is dropped when a chapter line already says it -- including
        when one is simply a longer phrasing of the other.
        """
        equations = list(chapter.equations)
        keys = [self._equation_key(item) for item in equations]
        for extra in self.dynamic_equations(chapter.stage):
            key = self._equation_key(extra)
            if not key:
                continue
            if any(key == existing
                   or (len(existing) > 6 and existing in key)
                   or (len(key) > 6 and key in existing)
                   for existing in keys):
                continue
            equations.append(extra)
            keys.append(key)
        return equations

    def draw_ui(self, width: int, height: int) -> object:
        # A chapter may override the lesson's style, which is how a
        # four-second sting goes full-frame inside a teaching lesson.
        chapter = self.chapters[self.chapter_index]
        style = chapter.overlay or self.lesson.style
        if style == "hype":
            return self.draw_ui_hype(width, height)
        if style == "math":
            return self.draw_ui_math(width, height)
        return self.draw_ui_teaching(width, height)

    # Two labels may overlap by this much of the smaller one before the
    # layout pass intervenes. Generous on purpose: the overlapping look
    # is wanted, only the unreadable part is not.
    LABEL_OVERLAP_TOLERANCE = 0.28

    def layout_labels(self, rects: list) -> list:
        """Nudge labels apart only where they would bury each other.

        Returns the rects in the same order, moved vertically by the
        smallest amount that brings every pairwise overlap under the
        tolerance. Panels still overlap; glyphs no longer share pixels.
        """
        if self.lesson.label_layout != "declutter":
            return rects
        placed: list = []
        for rect in rects:
            moved = rect.copy()
            for _ in range(24):
                clash = None
                for other in placed:
                    overlap = moved.clip(other)
                    if not overlap.width or not overlap.height:
                        continue
                    smaller = min(moved.width * moved.height,
                                  other.width * other.height) or 1
                    share = (overlap.width * overlap.height) / smaller
                    if share > self.LABEL_OVERLAP_TOLERANCE:
                        clash = other
                        break
                if clash is None:
                    break
                # Move whichever way is shorter, and only far enough
                # to bring the pair back under the tolerance.
                if moved.centery >= clash.centery:
                    moved.y = clash.bottom - int(moved.height * 0.22)
                else:
                    moved.y = clash.top - moved.height + int(
                        moved.height * 0.22)
            placed.append(moved)
        return placed

    def draw_ui_hype(self, width: int, height: int) -> object:
        """Full-frame picture, one line of type, no chrome.

        Everything the teaching overlay puts in cards is dropped: a
        montage is carried by the pictures and the voice, and a
        sidebar of prose competes with both.
        """
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        scale = min(width / 1600.0, height / 900.0)
        chapter = self.chapters[self.chapter_index]
        self.ui_buttons.clear()

        # Labels stay: they are part of the picture, not the chrome.
        label_font = self.font(max(13, int(17 * scale)), True)
        drawn = []
        for world_label in self.world_labels:
            screen = project_point(self.mvp, world_label.point, width, height)
            if screen is None:
                continue
            lines = world_label.text.splitlines()
            if not lines:
                continue
            widest = max(label_font.size(line)[0] for line in lines)
            label_height = len(lines) * int(22 * scale) + int(14 * scale)
            drawn.append((pg.Rect(
                int(screen[0] - widest * 0.5 - 10 * scale),
                int(screen[1] - label_height * 0.5),
                int(widest + 20 * scale), label_height), lines,
                world_label.color))
        laid_out = self.layout_labels([item[0] for item in drawn])
        # A touch more backing when decluttering, so whatever overlap
        # survives still reads as layered rather than smeared.
        backing = 232 if self.lesson.label_layout == "declutter" else 210
        for rect, (_, lines, colour) in zip(laid_out, drawn):
            self.rounded_panel(surface, rect, (3, 10, 18, backing),
                               (*colour, 190), int(7 * scale))
            line_y = rect.y + int(7 * scale)
            for line in lines:
                rendered = label_font.render(line, True, colour)
                surface.blit(rendered, (
                    rect.centerx - rendered.get_width() // 2, line_y))
                line_y += int(22 * scale)

        # A scrim only under the type, so the picture stays clean.
        headline_font = self.font(max(30, int(54 * scale)), True)
        kicker_font = self.font(max(13, int(19 * scale)), True)
        margin = int(70 * scale)
        lines = self.wrap_text(chapter.promise, headline_font,
                               width - 2 * margin)
        block_height = len(lines) * int(64 * scale) + int(46 * scale)
        block_top = height - int(96 * scale) - block_height
        scrim = pg.Surface((width, block_height + int(120 * scale)),
                           pg.SRCALPHA)
        for row in range(scrim.get_height()):
            alpha = int(196 * min(1.0, row / (scrim.get_height() * 0.55)))
            pg.draw.line(scrim, (3, 8, 16, alpha), (0, row), (width, row))
        surface.blit(scrim, (0, block_top - int(52 * scale)))

        kicker = kicker_font.render(chapter.title.upper(), True, (61, 211, 255))
        surface.blit(kicker, (margin, block_top - int(6 * scale)))
        text_y = block_top + int(30 * scale)
        for line in lines:
            shadow = headline_font.render(line, True, (2, 6, 12))
            surface.blit(shadow, (margin + int(3 * scale),
                                  text_y + int(3 * scale)))
            surface.blit(headline_font.render(line, True, (240, 247, 252)),
                         (margin, text_y))
            text_y += int(64 * scale)

        # One hairline of progress, and nothing else.
        played = (self.timeline % self.total_duration) / self.total_duration
        bar = int(5 * scale)
        pg.draw.rect(surface, (22, 44, 60, 220),
                     pg.Rect(0, height - bar, width, bar))
        pg.draw.rect(surface, (255, 177, 62, 255),
                     pg.Rect(0, height - bar, int(width * played), bar))
        return surface

    def draw_ui_math(self, width: int, height: int) -> object:
        """The math screen: the picture stays live, the numbers get made.

        The chapter's equations are treated as an ordered derivation and
        revealed one line at a time as the chapter plays -- the line being
        written is amber, settled lines are white, and the final line is
        held back and then presented as the conclusion in its own band.
        The point of the mode is transparency: the viewer watches the
        figure being computed instead of being told it.
        """
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        scale = min(width / 1600.0, height / 900.0)
        chapter = self.chapters[self.chapter_index]
        self.ui_buttons.clear()

        # World labels first: they belong to the picture, not the panel.
        label_font = self.font(max(12, int(15 * scale)), True)
        for world_label in self.world_labels:
            screen = project_point(self.mvp, world_label.point, width, height)
            if screen is None:
                continue
            lines = world_label.text.splitlines()
            if not lines:
                continue
            widest = max(label_font.size(line)[0] for line in lines)
            label_height = len(lines) * int(20 * scale) + int(12 * scale)
            rect = pg.Rect(
                int(screen[0] - widest * 0.5 - 9 * scale),
                int(screen[1] - label_height * 0.5),
                int(widest + 18 * scale), label_height)
            self.rounded_panel(surface, rect, (3, 10, 18, 215),
                               (*world_label.color, 170), int(6 * scale))
            line_y = rect.y + int(6 * scale)
            for line in lines:
                rendered = label_font.render(line, True, world_label.color)
                surface.blit(rendered, (
                    rect.centerx - rendered.get_width() // 2, line_y))
                line_y += int(20 * scale)

        # The worksheet panel, right side, floor to ceiling.
        margin = int(26 * scale)
        panel_width = int(width * 0.42)
        panel_x = width - margin - panel_width
        panel_height = height - 2 * margin - int(16 * scale)
        panel_rect = pg.Rect(panel_x, margin, panel_width, panel_height)
        self.rounded_panel(surface, panel_rect, (4, 11, 21, 236),
                           (57, 95, 114, 255), int(14 * scale))

        inner_x = panel_x + int(24 * scale)
        text_width = panel_width - int(48 * scale)
        y = margin + int(20 * scale)
        kicker_font = self.font(max(12, int(14 * scale)), True)
        surface.blit(kicker_font.render(
            f"THE MATH  --  CHAPTER {chapter.number}", True,
            (255, 177, 62)), (inner_x, y))
        y += int(26 * scale)
        title_font = self.font(max(17, int(23 * scale)), True)
        for line in self.wrap_text(chapter.title, title_font, text_width):
            surface.blit(title_font.render(line, True, (238, 246, 252)),
                         (inner_x, y))
            y += int(29 * scale)
        y += int(6 * scale)

        # The chapter's own equations only, in their authored order: a
        # math screen is a complete derivation whose last line is the
        # conclusion, and letting the live-equation merge append lines
        # would put a stray figure in the conclusion band.
        equations = list(chapter.equations)
        steps = equations[:-1] if len(equations) > 1 else list(equations)
        conclusion = equations[-1] if len(equations) > 1 else ""

        # Reserve the conclusion band before laying out steps, so a long
        # derivation shrinks rather than colliding with its own verdict.
        conclusion_font = self.font(max(14, int(19 * scale)), True)
        conclusion_lines = (self.wrap_text(conclusion, conclusion_font,
                                           text_width - int(20 * scale))
                            if conclusion else [])
        band_height = (len(conclusion_lines) * int(25 * scale)
                       + int(52 * scale)) if conclusion_lines else 0
        band_top = panel_rect.bottom - band_height - int(18 * scale)

        # Steps appear one at a time across the first four fifths of the
        # chapter, so the conclusion still gets a beat of its own.
        progress = clamp(self.chapter_progress)
        visible = len(steps) if progress >= 0.80 else max(
            1, int(progress / 0.80 * len(steps)) + 1)
        visible = min(visible, len(steps))

        step_size = max(12, int(16 * scale))
        step_font = self.font(step_size)

        def step_rows(point_size: int):
            font = self.font(point_size)
            rows = []
            for index, step in enumerate(steps):
                wrapped = self.wrap_text(step, font, text_width - int(18 * scale))
                rows.append((index, wrapped))
            line_height = int(point_size * 1.38)
            total = sum(len(wrapped) for _, wrapped in rows) * line_height \
                + len(rows) * int(6 * scale)
            return rows, line_height, total

        rows, line_height, total = step_rows(step_size)
        while total > band_top - y - int(12 * scale) and step_size > 10:
            step_size -= 1
            rows, line_height, total = step_rows(step_size)
        step_font = self.font(step_size)

        for index, wrapped in rows:
            if index >= visible:
                break
            settled = index < visible - 1 or progress >= 0.80
            colour = (206, 221, 233) if settled else (255, 197, 92)
            marker = "=" if settled else ">"
            surface.blit(self.font(step_size, True).render(
                marker, True, (61, 211, 255)),
                (inner_x, y))
            for line in wrapped:
                surface.blit(step_font.render(line, True, colour),
                             (inner_x + int(20 * scale), y))
                y += line_height
            y += int(6 * scale)

        # The conclusion band: held until the derivation has landed.
        if conclusion_lines and progress >= 0.80:
            band_rect = pg.Rect(panel_x + int(12 * scale), band_top,
                                panel_width - int(24 * scale), band_height)
            self.rounded_panel(surface, band_rect, (8, 34, 22, 240),
                               (83, 233, 152, 255), int(10 * scale))
            surface.blit(kicker_font.render("CONCLUSION", True,
                                            (83, 233, 152)),
                         (band_rect.x + int(14 * scale),
                          band_rect.y + int(11 * scale)))
            text_y = band_rect.y + int(34 * scale)
            for line in conclusion_lines:
                surface.blit(conclusion_font.render(line, True,
                                                    (233, 249, 239)),
                             (band_rect.x + int(14 * scale), text_y))
                text_y += int(25 * scale)

        # The transparency footnote, under the panel.
        foot_font = self.font(max(10, int(12 * scale)))
        foot = foot_font.render(
            "computed live by the code drawing this frame -- "
            "the audit report ships with this film", True, (91, 119, 137))
        surface.blit(foot, (panel_x + panel_width - foot.get_width(),
                            panel_rect.bottom + int(4 * scale)))

        # Same hairline of progress the montage carries.
        played = (self.timeline % self.total_duration) / self.total_duration
        bar = int(5 * scale)
        pg.draw.rect(surface, (22, 44, 60, 220),
                     pg.Rect(0, height - bar, width, bar))
        pg.draw.rect(surface, (255, 177, 62, 255),
                     pg.Rect(0, height - bar, int(width * played), bar))
        return surface

    def draw_ui_teaching(self, width: int, height: int) -> object:
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        scale = min(width / 1600.0, height / 900.0)
        margin = int(24 * scale)
        chapter = self.chapters[self.chapter_index]
        self.ui_buttons.clear()

        # Header
        self.rounded_panel(surface, (margin, margin, width - 2 * margin, int(78 * scale)),
                           (5, 13, 25, 222), (30, 74, 100, 255), int(12 * scale))
        self.draw_text(surface, self.lesson.brand,
                       (margin + int(20 * scale), margin + int(13 * scale)),
                       max(14, int(16 * scale)), (55, 210, 255), True)
        self.draw_text(surface, chapter.title,
                       (margin + int(20 * scale), margin + int(35 * scale)),
                       max(21, int(29 * scale)), (238, 246, 252), True)
        if self.exporting:
            status = "NARRATED EXPORT" if self.narration_active else "VIDEO EXPORT"
            status_color = (83, 233, 152)
            status_suffix = ""
        else:
            status = "PLAYING" if self.playing else "PAUSED"
            status_color = (83, 233, 152) if self.playing else (255, 179, 70)
            status_suffix = f"  {self.playback_speed:g}x"
        self.draw_text(surface, f"{status}{status_suffix}",
                       (width - margin - int(170 * scale), margin + int(25 * scale)),
                       max(14, int(17 * scale)), status_color, True)

        # Teaching card.  A verbose chapter has far more narration than the
        # original fourteen-chapter lesson, so the card is laid out twice:
        # once to measure at the preferred size, then again a size smaller
        # if that did not fit the space between the header and the bar.
        card_width = int(424 * scale)
        card_top = margin + int(94 * scale)
        card_room = height - margin - int(105 * scale) - card_top - int(16 * scale)
        text_width = card_width - int(40 * scale)
        title_size = max(18, int(24 * scale))
        body_size = max(13, int(16 * scale))

        def lay_out(title_pt: int, body_pt: int):
            title_font = self.font(title_pt, True)
            body_font = self.font(body_pt)
            title_step = int(title_pt * 1.26)
            body_step = int(body_pt * 1.44)
            rows: list[tuple[object, str, tuple[int, int, int], int]] = []
            for line in self.wrap_text(chapter.promise, title_font, text_width):
                rows.append((title_font, line, (239, 245, 249), title_step))
            rows.append((body_font, "", (0, 0, 0), int(body_pt * 0.75)))
            for paragraph in chapter.narration:
                for line in self.wrap_text(paragraph, body_font, text_width):
                    rows.append((body_font, line, (169, 188, 203), body_step))
                rows.append((body_font, "", (0, 0, 0), int(body_pt * 0.45)))
            return rows, sum(row[3] for row in rows)

        rows, text_height = lay_out(title_size, body_size)
        while text_height > card_room - int(60 * scale) and body_size > 10:
            title_size = max(15, title_size - 1)
            body_size -= 1
            rows, text_height = lay_out(title_size, body_size)
        card_height = min(card_room, text_height + int(58 * scale))
        self.rounded_panel(surface, (margin, card_top, card_width, card_height),
                           (5, 15, 28, 224), (34, 76, 101, 255), int(14 * scale))
        x = margin + int(20 * scale)
        y = card_top + int(18 * scale)
        self.draw_text(surface, f"CHAPTER {chapter.number}",
                       (x, y), max(13, int(15 * scale)), (65, 210, 255), True)
        y += int(27 * scale)
        limit = card_top + card_height - int(8 * scale)
        for row_font, line, colour, step in rows:
            if y + step > limit:
                break
            if line:
                surface.blit(row_font.render(line, True, colour), (x, y))
            y += step

        # Equation card
        equation_width = int(455 * scale)
        equation_height = int(210 * scale)
        equation_x = width - margin - equation_width
        equation_y = height - margin - int(105 * scale) - equation_height
        self.rounded_panel(surface, (equation_x, equation_y, equation_width, equation_height),
                           (5, 15, 28, 230), (57, 95, 114, 255), int(14 * scale))
        self.draw_text(surface, "LIVE CALCULATION",
                       (equation_x + int(18 * scale), equation_y + int(15 * scale)),
                       max(13, int(14 * scale)), (255, 177, 62), True)
        eq_y = equation_y + int(44 * scale)
        equation_font = self.font(max(12, int(15 * scale)), False)
        equations = self.merge_equations(chapter)
        for equation in equations[:7]:
            for line in self.wrap_text(equation, equation_font, equation_width - int(36 * scale)):
                surface.blit(equation_font.render(line, True, (216, 229, 237)),
                             (equation_x + int(18 * scale), eq_y))
                eq_y += int(21 * scale)

        # Projected labels live inside the 3D view.
        for world_label in self.world_labels:
            screen = project_point(self.mvp, world_label.point, width, height)
            if screen is None:
                continue
            lines = world_label.text.splitlines()
            label_font = self.font(max(11, int(14 * scale)), True)
            max_label_width = max(label_font.size(line)[0] for line in lines)
            label_height = len(lines) * int(18 * scale) + int(12 * scale)
            label_rect = pg.Rect(
                int(screen[0] - max_label_width * 0.5 - 8 * scale),
                int(screen[1] - label_height * 0.5),
                int(max_label_width + 16 * scale),
                label_height,
            )
            self.rounded_panel(surface, label_rect, (3, 10, 18, 205),
                               (*world_label.color, 150), int(6 * scale))
            line_y = label_rect.y + int(6 * scale)
            for line in lines:
                rendered = label_font.render(line, True, world_label.color)
                surface.blit(rendered, (
                    label_rect.centerx - rendered.get_width() // 2, line_y
                ))
                line_y += int(18 * scale)

        # Bottom presenter controls and chapter timeline.
        bar_height = int(87 * scale)
        bar_y = height - margin - bar_height
        bar_rect = pg.Rect(margin, bar_y, width - 2 * margin, bar_height)
        self.rounded_panel(surface, bar_rect, (5, 13, 25, 235),
                           (30, 74, 100, 255), int(12 * scale))
        button_y = bar_y + int(13 * scale)
        button_size = int(37 * scale)
        for name, label, x_offset in (
            ("previous", "<", 15), ("play", "||" if self.playing else ">", 59),
            ("next", ">", 103),
        ):
            rect = pg.Rect(margin + int(x_offset * scale), button_y,
                           button_size, button_size)
            self.ui_buttons[name] = rect
            self.rounded_panel(surface, rect, (18, 45, 66, 255),
                               (55, 125, 155, 255), int(8 * scale))
            rendered = self.font(max(14, int(18 * scale)), True).render(
                label, True, (225, 241, 248)
            )
            surface.blit(rendered, rendered.get_rect(center=rect.center))

        timeline_x = margin + int(164 * scale)
        timeline_right = width - margin - int(116 * scale)
        timeline_y = bar_y + int(24 * scale)
        timeline_width = timeline_right - timeline_x
        gap = max(2, int(3 * scale))
        count = len(self.chapters)
        cell_width = (timeline_width - gap * (count - 1)) / count
        # A long lesson cannot label every cell; label about eight of them.
        label_step = max(1, round(count / 8))
        for index, item in enumerate(self.chapters):
            rect = pg.Rect(
                int(timeline_x + index * (cell_width + gap)),
                timeline_y,
                max(2, int(cell_width)),
                int(17 * scale),
            )
            self.ui_buttons[f"chapter_{index}"] = rect.inflate(0, int(22 * scale))
            active = index == self.chapter_index
            color = (47, 205, 247, 255) if active else (42, 73, 91, 255)
            pg.draw.rect(surface, color, rect, border_radius=max(2, int(4 * scale)))
            if active:
                fill = rect.copy()
                fill.width = max(2, int(rect.width * self.chapter_progress))
                pg.draw.rect(surface, (255, 177, 62, 255), fill,
                             border_radius=max(2, int(4 * scale)))
            if width >= 1300 and (index % label_step == 0 or index == count - 1):
                self.draw_text(surface, item.number,
                               (rect.x, rect.bottom + int(6 * scale)),
                               max(9, int(10 * scale)), (113, 139, 156), True)

        unit_rect = pg.Rect(width - margin - int(96 * scale), button_y,
                            int(80 * scale), button_size)
        self.ui_buttons["units"] = unit_rect
        self.rounded_panel(surface, unit_rect, (18, 45, 66, 255),
                           (55, 125, 155, 255), int(8 * scale))
        unit_label = "MM" if self.metric else "INCH"
        rendered = self.font(max(11, int(13 * scale)), True).render(
            unit_label, True, (225, 241, 248)
        )
        surface.blit(rendered, rendered.get_rect(center=unit_rect.center))

        # A minimal keyboard prompt remains unobtrusive for recorded video.
        controls = "SPACE play/pause   <- -> chapter   drag orbit   wheel zoom   X x-ray   S snapshot"
        rendered = self.font(max(10, int(12 * scale))).render(
            controls, True, (91, 119, 137)
        )
        surface.blit(rendered, (width // 2 - rendered.get_width() // 2,
                                height - int(10 * scale) - rendered.get_height()))
        return surface

    def upload_overlay(self, surface) -> None:
        size = surface.get_size()
        if self.overlay_texture is None or self.overlay_size != size:
            if self.overlay_texture is not None:
                self.overlay_texture.release()
            self.overlay_texture = self.ctx.texture(size, 4)
            self.overlay_texture.filter = (
                self.moderngl.LINEAR, self.moderngl.LINEAR
            )
            self.overlay_size = size
        data = self.pygame.image.tobytes(surface, "RGBA", True)
        self.overlay_texture.write(data)

    # ------------------------------------------------------------------
    # Frame lifecycle
    # ------------------------------------------------------------------

    def set_chapter(self, index: int) -> None:
        self.chapter_index = index % len(self.chapters)
        self.timeline = chapter_start(
            self.chapter_index, self.chapter_durations, self.chapters
        )
        self.chapter_progress = 0.0
        self.reset_camera()

    def reset_camera(self) -> None:
        chapter = self.chapters[self.chapter_index]
        self.camera_yaw, self.camera_pitch, self.camera_distance = chapter.camera
        self.camera_override = False

    def update(self, dt: float) -> None:
        if self.playing:
            self.timeline += dt * self.playback_speed
            if self.timeline >= self.total_duration:
                self.timeline %= self.total_duration
        previous_chapter = self.chapter_index
        self.chapter_index, self.chapter_progress = chapter_at_time(
            self.timeline, self.chapter_durations, self.chapters
        )
        if previous_chapter != self.chapter_index and not self.camera_override:
            self.reset_camera()

    def camera(self) -> tuple[np.ndarray, np.ndarray]:
        chapter = self.chapters[self.chapter_index]
        yaw = self.camera_yaw
        if not self.camera_override and (self.playing or self.exporting):
            yaw += math.sin(self.chapter_progress * math.pi) * 7.0
        pitch = math.radians(clamp(self.camera_pitch, 8.0, 78.0))
        yaw_radians = math.radians(yaw)
        distance = self.camera_distance
        target = np.array([0.0, 0.0, 2.25], dtype=np.float32)
        eye = target + np.array([
            distance * math.cos(pitch) * math.cos(yaw_radians),
            distance * math.cos(pitch) * math.sin(yaw_radians),
            distance * math.sin(pitch),
        ], dtype=np.float32)
        return eye, target

    def render(self, present: bool = True) -> None:
        width, height = self.pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.clear(*BG)
        eye, target = self.camera()
        projection = perspective(48.0, width / max(1, height), 0.08, 120.0)
        chapter = self.chapters[self.chapter_index]
        if self.lesson.camera_fn is not None:
            # A lesson directing its own camera replaces both the orbit
            # and the lens; everything downstream is unchanged, which is
            # what lets a drama and a masterclass share one renderer.
            eye, target, fov = self.lesson.camera_fn(
                self, chapter, self.chapter_progress, width, height)
            eye = np.asarray(eye, dtype=np.float32)
            target = np.asarray(target, dtype=np.float32)
            projection = perspective(float(fov), width / max(1, height),
                                     0.08, 120.0)
        view = look_at(eye, target)
        self.mvp = projection @ view
        self.scene_program["u_mvp"].write(
            np.ascontiguousarray(self.mvp.T).tobytes()
        )
        self.scene_program["u_camera"].value = tuple(float(value) for value in eye)
        self.scene_program["u_light"].value = (-0.45, -0.55, -0.72)
        opaque, transparent = self.build_scene(chapter.stage, self.chapter_progress)

        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.ctx.depth_mask = True
        self.opaque_mesh.draw(opaque)
        if transparent.vertices:
            self.ctx.disable(self.moderngl.CULL_FACE)
            self.ctx.depth_mask = False
            self.transparent_mesh.draw(transparent)
            self.ctx.depth_mask = True
            self.ctx.enable(self.moderngl.CULL_FACE)

        overlay = self.draw_ui(width, height)
        self.upload_overlay(overlay)
        self.ctx.disable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.overlay_texture.use(0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_vao.render(self.moderngl.TRIANGLE_STRIP)
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        if present:
            self.pygame.display.flip()

    def capture_rgb(self) -> bytes:
        width, height = self.pygame.display.get_window_size()
        self.ctx.finish()
        return self.ctx.screen.read((0, 0, width, height), components=3, alignment=1)

    def save_screenshot(self, path: Path | None = None) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if path is None:
            path = self.output_dir / (
                f"{self.lesson.snapshot_prefix}_{int(time.time() * 1000)}.png"
            )
        width, height = self.pygame.display.get_window_size()
        raw = self.capture_rgb()
        image = self.pygame.image.fromstring(raw, (width, height), "RGB")
        image = self.pygame.transform.flip(image, False, True)
        self.pygame.image.save(image, str(path))
        return path

    def click(self, position: tuple[int, int]) -> None:
        for name, rect in self.ui_buttons.items():
            if rect.collidepoint(position):
                if name == "previous":
                    self.set_chapter(self.chapter_index - 1)
                elif name == "next":
                    self.set_chapter(self.chapter_index + 1)
                elif name == "play":
                    self.playing = not self.playing
                elif name == "units":
                    self.metric = not self.metric
                elif name.startswith("chapter_"):
                    self.set_chapter(int(name.split("_")[1]))
                return

    def toggle_fullscreen(self) -> None:
        # pygame 2 can toggle the existing OpenGL display without rebuilding
        # the ModernGL context on supported desktop drivers.
        try:
            self.pygame.display.toggle_fullscreen()
            self.fullscreen = not self.fullscreen
        except self.pygame.error:
            pass

    def handle_events(self) -> bool:
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.fullscreen:
                        self.toggle_fullscreen()
                    else:
                        return False
                elif event.key == pg.K_SPACE:
                    self.playing = not self.playing
                elif event.key == pg.K_LEFT:
                    self.set_chapter(self.chapter_index - 1)
                elif event.key == pg.K_RIGHT:
                    self.set_chapter(self.chapter_index + 1)
                elif event.key == pg.K_HOME:
                    self.set_chapter(0)
                elif event.key == pg.K_r:
                    self.reset_camera()
                elif event.key == pg.K_x:
                    self.xray = not self.xray
                elif event.key == pg.K_u:
                    self.metric = not self.metric
                elif event.key == pg.K_s:
                    path = self.save_screenshot()
                    print(f"saved {path}")
                elif event.key == pg.K_F11:
                    self.toggle_fullscreen()
                elif pg.K_1 <= event.key <= pg.K_9:
                    self.set_chapter(event.key - pg.K_1)
                elif event.key == pg.K_0:
                    self.set_chapter(9)
                elif event.key in (pg.K_LEFTBRACKET, pg.K_RIGHTBRACKET):
                    direction = -1 if event.key == pg.K_LEFTBRACKET else 1
                    speeds = (0.5, 1.0, 1.5, 2.0)
                    current = min(range(len(speeds)),
                                  key=lambda i: abs(speeds[i] - self.playback_speed))
                    self.playback_speed = speeds[
                        max(0, min(len(speeds) - 1, current + direction))
                    ]
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)
                self.dragging = True
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pg.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                if abs(dx) + abs(dy) > 1:
                    self.camera_yaw += dx * 0.28
                    self.camera_pitch = clamp(
                        self.camera_pitch - dy * 0.22, 8.0, 78.0
                    )
                    self.camera_override = True
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEWHEEL:
                self.camera_distance = clamp(
                    self.camera_distance - event.y * 0.55, 5.5, 18.0
                )
                self.camera_override = True
        return True

    def run(self) -> None:
        clock = self.pygame.time.Clock()
        running = True
        while running:
            dt = min(0.05, clock.tick(60) / 1000.0)
            running = self.handle_events()
            self.update(dt)
            self.render()
        self.pygame.quit()

    def render_shots(self, times: list[float], output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        self.playing = False
        for target in times:
            self.timeline = target % self.total_duration
            self.chapter_index, self.chapter_progress = chapter_at_time(
                self.timeline, self.chapter_durations, self.chapters
            )
            self.reset_camera()
            # Read the populated back buffer before a swap makes it the front
            # buffer; this is deterministic on Windows OpenGL drivers.
            self.render(present=False)
            path = output_dir / (
                f"{self.lesson.snapshot_prefix}_{target:07.2f}s.png"
            )
            paths.append(self.save_screenshot(path))
            print(f"saved {path}")
        return paths

    @property
    def speak_promise(self) -> bool:
        """Whether the voice reads the on-screen headline as well.

        Teaching lessons do: the promise is a separate summary line.
        A montage does not: its headline is a condensed form of the
        narration underneath it, so reading both says it twice.
        """
        return self.lesson.style != "hype"

    def export_video(
        self,
        path: Path,
        fps: int = 30,
        *,
        render_fps: int | None = None,
        video_encoder: str = "libx264",
        video_preset: str = "medium",
        narration: bool = True,
        local_narration_plan: Path | None = None,
        voice: str = DEFAULT_VOICE,
        voice_rate: str = DEFAULT_RATE,
        voice_pitch: str = DEFAULT_PITCH,
        voice_volume: str = DEFAULT_VOLUME,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
    ) -> None:
        capture_fps = fps if render_fps is None else int(render_fps)
        if capture_fps < 1 or capture_fps > fps:
            raise ValueError("render_fps must be between 1 and the output fps")
        x264_presets = {
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow",
        }
        nvenc_presets = {f"p{index}" for index in range(1, 8)}
        if video_encoder == "libx264" and video_preset not in x264_presets:
            raise ValueError(
                f"unsupported x264 preset {video_preset!r}; expected one of "
                f"{', '.join(sorted(x264_presets))}"
            )
        if video_encoder == "h264_nvenc" and video_preset not in nvenc_presets:
            raise ValueError(
                f"unsupported NVENC preset {video_preset!r}; expected one of "
                f"{', '.join(sorted(nvenc_presets))}"
            )
        if video_encoder not in {"libx264", "h264_nvenc"}:
            raise ValueError(
                f"unsupported video encoder {video_encoder!r}; expected "
                "'libx264' or 'h264_nvenc'"
            )
        ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
        plan: NarrationPlan | None = None
        speech_delay = SPEECH_DELAY
        self.exporting = True
        self.narration_active = narration or local_narration_plan is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        if local_narration_plan is not None:
            plan_path = Path(local_narration_plan).resolve()
            if not plan_path.is_file():
                raise FileNotFoundError(
                    f"Local narration plan was not found: {plan_path}"
                )
            payload = json.loads(plan_path.read_text(encoding="utf-8"))
            if int(payload.get("schema", 0)) != 1:
                raise ValueError("Unsupported local narration-plan schema")
            chapter_durations = tuple(
                float(value) for value in payload.get("chapter_durations", [])
            )
            speech_durations = tuple(
                float(value) for value in payload.get("speech_durations", [])
            )
            chapter_starts = tuple(
                float(value) for value in payload.get("chapter_starts", [])
            )
            expected = len(self.chapters)
            if (
                len(chapter_durations) != expected
                or len(speech_durations) != expected
                or len(chapter_starts) != expected
            ):
                raise ValueError(
                    "Local narration plan does not match the lesson chapter count"
                )
            if any(value <= 0.0 for value in chapter_durations):
                raise ValueError("Local narration plan contains invalid durations")

            def plan_file(value: str) -> Path:
                candidate = Path(value)
                return (
                    candidate
                    if candidate.is_absolute()
                    else plan_path.parent / candidate
                ).resolve()

            track_path = plan_file(str(payload.get("track", "")))
            if not track_path.is_file():
                raise FileNotFoundError(
                    f"Local narration track was not found: {track_path}"
                )
            clip_paths = tuple(
                plan_file(str(value)) for value in payload.get("clips", [])
            )
            speech_delay = float(payload.get("speech_delay", SPEECH_DELAY))
            plan = NarrationPlan(
                voice=str(payload.get("voice_profile", "local-profile")),
                rate="local",
                pitch="local",
                volume="local",
                clip_paths=clip_paths,
                speech_durations=speech_durations,
                chapter_durations=chapter_durations,
                chapter_starts=chapter_starts,
                total_duration=sum(chapter_durations),
                track_path=track_path,
            )
            self.chapter_durations = plan.chapter_durations
            self.total_duration = plan.total_duration
            print(
                f"Local narration: {plan.voice}, {self.total_duration:.1f}s "
                f"across {len(self.chapters)} chapters"
            )
        elif narration:
            ffprobe = companion_ffprobe(ffmpeg, ffprobe_path)
            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume, self.chapters,
                self.speak_promise
            )
            stem_directory = path.parent / f"{path.stem}-voice-{voice_slug}"
            track_path = path.parent / f"{path.stem}-narration.m4a"
            plan = synthesize_narration(
                stem_directory,
                track_path,
                ffmpeg,
                ffprobe,
                voice=voice,
                rate=voice_rate,
                pitch=voice_pitch,
                volume=voice_volume,
                chapters=self.chapters,
                speak_promise=self.speak_promise,
            )
            self.chapter_durations = plan.chapter_durations
            self.total_duration = plan.total_duration
            print(
                f"Natural narration: {voice}, {self.total_duration:.1f}s "
                f"across {len(self.chapters)} chapters"
            )
            if self.lesson.audio_bed:
                from .soundboard import mix_bed_into_track
                mix_bed_into_track(plan.track_path, self.lesson.audio_bed,
                                   ffmpeg, self.lesson.audio_bed_gain)
        width, height = self.pygame.display.get_window_size()
        # Tag the temp with this process, because two exports of the same
        # lesson to the same output otherwise share one hidden file: the
        # first to finish deletes it out from under the second, which then
        # muxes a truncated picture against a full narration track and
        # leaves a plausible-looking MP4 with seconds of video in it.
        render_path = (
            path.parent / f".{path.stem}-silent-render-{os.getpid()}.mp4"
            if plan is not None else path
        )
        encoder_args = (
            ["-c:v", "h264_nvenc", "-preset", video_preset,
             "-tune", "hq", "-rc", "vbr", "-cq", "18", "-b:v", "0"]
            if video_encoder == "h264_nvenc"
            else ["-c:v", "libx264", "-preset", video_preset, "-crf", "18"]
        )
        command = [
            ffmpeg, "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24",
            "-video_size", f"{width}x{height}",
            "-framerate", str(capture_fps), "-i", "-",
            "-vf", "vflip",
            *encoder_args,
            "-r", str(fps),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(render_path),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        total_frames = int(math.ceil(self.total_duration * capture_fps))
        self.playing = False
        rendered_chapter = -1
        try:
            for frame in range(total_frames):
                self.timeline = frame / capture_fps
                self.chapter_index, self.chapter_progress = chapter_at_time(
                    self.timeline, self.chapter_durations, self.chapters
                )
                if self.chapter_index != rendered_chapter:
                    self.reset_camera()
                    rendered_chapter = self.chapter_index
                self.render(present=False)
                assert process.stdin is not None
                process.stdin.write(self.capture_rgb())
                if frame % capture_fps == 0:
                    print(
                        f"\rRendering {frame / capture_fps:6.1f}s / "
                        f"{self.total_duration:6.1f}s", end="", flush=True
                    )
            assert process.stdin is not None
            process.stdin.close()
            return_code = process.wait()
        except BaseException:
            process.kill()
            raise
        print()
        if return_code != 0:
            raise RuntimeError(f"ffmpeg exited with status {return_code}")
        if plan is not None:
            mux_command = [
                ffmpeg, "-y",
                "-i", str(render_path),
                "-i", str(plan.track_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "copy",
                "-shortest", "-movflags", "+faststart",
                str(path),
            ]
            subprocess.run(mux_command, check=True)
            try:
                render_path.unlink()
            except OSError:
                pass
            script_path, subtitle_path = write_companion_files(
                path,
                plan.chapter_durations,
                plan.speech_durations,
                speech_delay,
                self.chapters,
                self.lesson.title,
                self.speak_promise,
            )
            print(f"saved {plan.track_path}")
        else:
            script_path, subtitle_path = write_companion_files(
                path,
                chapters=self.chapters,
                title=self.lesson.title,
                speak_promise=self.speak_promise,
            )
        self.exporting = False
        print(f"saved {path}")
        print(f"saved {script_path}")
        print(f"saved {subtitle_path}")


def parse_size(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("size must look like 1600x900") from exc
    if width < 960 or height < 540:
        raise ValueError("minimum supported size is 960x540")
    return width, height


def main(default_lesson: str = "2v") -> int:
    """Dispatch on the launcher's config ticket instead of argv.

    Launch and configure this from the consolidated launcher
    (``py -3.12 launcher.py``), which exposes every option below as a
    GUI field. Run directly with no ticket present and it opens the
    normal live presentation, fullscreen.
    """
    cfg = _lc.consume_config("two_v_masterclass")
    action = cfg.get("action", "run")
    # Imported here, not at module scope: the lesson modules import this
    # module's render kit, so the registry can only be built once this
    # module has finished loading.
    from .lesson_registry import get_lesson, lesson_menu

    try:
        lesson = get_lesson(cfg.get("lesson") or default_lesson)
        # Segments are opt-in per render: everything that shipped before
        # they existed stays uncomposed and keeps reproducing exactly.
        if cfg.get("compose_segments"):
            extra = cfg.get("segments_include") or ""
            lesson = compose(
                lesson,
                include=tuple(k for k in str(extra).split(",") if k),
                exclude=tuple(
                    k for k in str(cfg.get("segments_exclude") or "").split(",")
                    if k),
            )
    except ValueError as exc:
        print(exc)
        print(lesson_menu())
        return 2
    voice = cfg.get("voice", DEFAULT_VOICE)
    voice_rate = cfg.get("voice_rate") or DEFAULT_RATE
    voice_pitch = cfg.get("voice_pitch", DEFAULT_PITCH)
    voice_volume = cfg.get("voice_volume", DEFAULT_VOLUME)
    ffmpeg_path = cfg.get("ffmpeg") or None
    ffprobe_path = cfg.get("ffprobe") or None
    no_narration = bool(cfg.get("no_narration", False))
    local_narration_plan = cfg.get("local_narration_plan") or None

    if local_narration_plan and action != "export_video":
        print("--local-narration-plan requires the export-video action")
        return 2
    if local_narration_plan and no_narration:
        print("local narration plan cannot be combined with no-narration")
        return 2

    if action == "soundboard":
        from .soundboard import board_menu, ensure_layout
        made = ensure_layout()
        if made:
            print(f"created {len(made)} category folder(s)")
        print(board_menu())
        return 0
    if action == "list_segments":
        print(segment_menu())
        return 0
    if action == "list_deliverables":
        print(deliverables_menu())
        return 0
    if action == "render_all":
        # One at a time, in the order they were made. See deliverables.py
        # for why this is sequential and what "exactly" costs.
        only = cfg.get("render_only") or None
        return render_all(
            only=tuple(str(only).split(",")) if only else None,
            force=bool(cfg.get("force_rerender", False)),
            fps=max(1, int(cfg.get("fps", 30))),
            size=cfg.get("size", "1920x1080"),
        )
    if action == "list_lessons":
        print(lesson_menu())
        return 0
    if action == "selftest":
        validate_geometry()
        lesson.validate()
        if lesson.selftest is not None:
            lesson.selftest()
        print((lesson.report or calculation_report)())
        # Write the companion files to a scratch directory and throw
        # them away.  They are the last thing an export does, long
        # after the expensive part, so a fault here is the costliest
        # kind to discover late and the cheapest to catch here.
        validate_deliverables()
        validate_segments()
        from .soundboard import validate_soundboard
        from .timber import validate_timber
        validate_timber()
        validate_soundboard()
        with tempfile.TemporaryDirectory() as scratch:
            script_path, subtitle_path = write_companion_files(
                Path(scratch) / f"{lesson.key}.mp4",
                chapters=lesson.chapters,
                title=lesson.title,
                speak_promise=lesson.style != "hype",
            )
            for written in (script_path, subtitle_path):
                if written.stat().st_size <= 0:
                    print(f"selftest FAILED: {written.name} is empty")
                    return 1
            print(
                f"companion files OK: {script_path.name}, "
                f"{subtitle_path.name}"
            )
        print(f"\nselftest OK: {lesson.title}, {len(lesson.chapters)} chapters")
        return 0
    if action == "report":
        print((lesson.report or calculation_report)())
        return 0
    if action == "list_voices":
        locale = cfg.get("voice_locale", "en-US")
        try:
            voices = list_neural_voices(locale)
        except RuntimeError as exc:
            print(exc)
            return 1
        if not voices:
            print(f"No voices found for locale {locale}")
            return 1
        for entry in voices:
            personalities = ", ".join(
                entry.get("VoiceTag", {}).get("VoicePersonalities", [])
            )
            print(
                f"{entry.get('ShortName', ''):<42} "
                f"{entry.get('Gender', ''):<7} {personalities}"
            )
        return 0
    if action == "voice_preview":
        try:
            preview_path = synthesize_preview(
                Path(cfg["voice_preview"]), voice=voice, rate=voice_rate,
                pitch=voice_pitch, volume=voice_volume)
        except (RuntimeError, ValueError) as exc:
            print(exc)
            return 1
        print(f"saved {preview_path}")
        return 0
    if action == "narration_only":
        try:
            ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
            ffprobe = companion_ffprobe(ffmpeg, ffprobe_path)
            output_path = Path(cfg["narration_only"])
            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume, lesson.chapters)
            plan = synthesize_narration(
                output_path.parent / f"{output_path.stem}-voice-{voice_slug}",
                output_path, ffmpeg, ffprobe, voice=voice, rate=voice_rate,
                pitch=voice_pitch, volume=voice_volume,
                chapters=lesson.chapters)
        except (RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            print(exc)
            return 1
        script_path, subtitle_path = write_companion_files(
            output_path, plan.chapter_durations, plan.speech_durations,
            SPEECH_DELAY, lesson.chapters, lesson.title)
        print(f"saved {plan.track_path}")
        print(f"saved {script_path}")
        print(f"saved {subtitle_path}")
        return 0
    if action == "script":
        script_path = Path(cfg["script"])
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(
            narration_script(None, lesson.chapters, lesson.title),
            encoding="utf-8",
        )
        subtitle_path = script_path.with_suffix(".srt")
        subtitle_path.write_text(
            subtitle_file(None, None, 0.0, lesson.chapters), encoding="utf-8"
        )
        print(f"saved {script_path}")
        print(f"saved {subtitle_path}")
        return 0
    if action == "build_packet":
        try:
            paths = export_build_packet(
                Path(cfg["build_packet"]),
                radius=cfg.get("radius_in"),
                connector_deduction=cfg.get("connector_deduction_in", 0.0))
        except ValueError as exc:
            print(exc)
            return 1
        for path in paths:
            print(f"saved {path}")
        return 0

    # A montage lesson carries its own pacing, which the launcher can
    # still override by filling the Rate field in.
    if not cfg.get("voice_rate") and lesson.voice_rate:
        voice_rate = lesson.voice_rate
    try:
        size = parse_size(cfg.get("size", "1600x900"))
    except ValueError as exc:
        print(exc)
        return 2
    app = MasterclassApp(
        size=size,
        fullscreen=bool(cfg.get("fullscreen", False)),
        hidden=action in ("shots", "export_video"),
        lesson=lesson,
    )
    if action == "shots" and cfg.get("shots"):
        try:
            times = [float(v.strip()) for v in str(cfg["shots"]).split(",")
                     if v.strip()]
        except ValueError as exc:
            print(f"shots values must be seconds: {exc}")
            return 2
        app.render_shots(times, Path("two_v_demo_output") / lesson.key)
        app.pygame.quit()
        return 0
    if action == "export_video" and cfg.get("export_video"):
        try:
            app.export_video(
                Path(cfg["export_video"]), max(1, int(cfg.get("fps", 30))),
                render_fps=(
                    int(cfg["render_fps"]) if cfg.get("render_fps") else None
                ),
                video_encoder=str(cfg.get("video_encoder", "libx264")),
                video_preset=str(cfg.get("video_preset", "medium")),
                narration=not no_narration,
                local_narration_plan=(
                    Path(local_narration_plan)
                    if local_narration_plan else None),
                voice=voice, voice_rate=voice_rate, voice_pitch=voice_pitch,
                voice_volume=voice_volume, ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path)
        except (RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            app.pygame.quit()
            print(exc)
            return 1
        app.pygame.quit()
        return 0
    app.run()
    return 0
