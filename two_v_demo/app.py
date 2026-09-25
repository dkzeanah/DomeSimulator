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
import sys
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
from .frame import Frame, FitSmoother, apply_fit, design_aspect, fit_camera, subject_points

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
        # Ask for a 24-bit depth buffer. Left unasked, this renderer was given
        # 16 bits, and 16 bits over a near plane of 0.08 and a far plane of
        # 120 resolves to the better part of a metre at sixty metres out --
        # which is why a park of decks sitting 12 cm above their ground filmed
        # as a field of horizontal stripes. Nothing composes differently with
        # more precision; things that were fighting for the depth buffer stop.
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        self.lesson = lesson or TWO_V_LESSON
        self.lesson.validate()
        self.chapters = self.lesson.chapters
        pygame.display.set_caption(self.lesson.title)
        pygame.display.set_mode(display_size, flags)
        window_w, window_h = pygame.display.get_window_size()
        # The shape of this screen, and the shape the film was composed for.
        # A film shown in its own shape takes the original path untouched.
        self.frame = Frame(window_w, window_h, design_aspect(self.lesson.key))
        self.fit_smoother = FitSmoother()
        self.scene_vertex_start = 0
        self.portrait_plan = None
        self.overlay_free = None
        self.export_fps = 30
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
        # Buildings handed over by the Dome Creator, drawn by the Creator's own
        # shader so a film shows the product the tool renders rather than a
        # sketch of it (see two_v_demo/creator_bridge.py). Nothing is compiled
        # or uploaded until a painter asks for one, so every other film pays
        # nothing at all for this.
        self.creator_draws: list = []
        self.creator_program = None
        self.creator_cache: dict = {}
        self.creator_sky = (0.16, 0.26, 0.38)
        """Sky the Creator's shader lights glass, mirrors and haze against.

        Dimmed from the tool's daylight blue because a film is graded dark; the
        mirror panels still reflect a sky and a tree line, at film brightness."""
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
        # How this cut behaves -- camera, pace, mascot, treatment. The empty
        # profile is the house behaviour, so every film that predates profiles
        # gets the identical object it always effectively had.
        from .style_profiles import profile_for
        self.profile = profile_for(getattr(self.lesson, "profile", ""))
        self.xray = True
        self.metric = False
        self.dragging = False
        self.last_mouse = (0, 0)
        self.world_labels: list[WorldLabel] = []
        self.world_icons: list = []
        # Measured speech per chapter, known once narration has been synthesized.
        # Callouts use it to land a figure on the words that say it; None means
        # the chapter's timing is estimated from the narrator's measured pace.
        self.speech_durations: tuple[float, ...] | None = None
        self.speech_clips: tuple[Path, ...] | None = None
        self.font_cache: dict[tuple[int, bool], object] = {}
        self.ui_buttons: dict[str, object] = {}
        self.plate_mode = False
        """Draw the film without its transport controls.

        A frame of a film printed in a book should not carry the film's
        scrubber, its play button or the word PAUSED. Those are for somebody
        driving the video. The layout is unchanged -- the teaching card still
        reserves the same room -- so a plate is the same frame with the
        controls not drawn, and not a re-composed one."""
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
        self.world_icons = []
        self.creator_draws = []
        if getattr(self.lesson, "ground", "grid") != "off":
            self.add_ground(opaque)
        # Everything after this index is the subject, which is what a screen
        # of another shape fits the camera to.
        self.scene_vertex_start = len(opaque.vertices)
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
        if self.portrait_plan is not None and self.adapting:
            # A phone frame: the stacked layout planned before the scene was drawn.
            from . import portrait_ui
            surface = portrait_ui.draw(self, self.portrait_plan, width, height)
        elif style == "hype":
            surface = self.draw_ui_hype(width, height)
        elif style == "plate":
            surface = self.draw_ui_plate(width, height)
        elif style == "title":
            surface = self.draw_ui_title(width, height)
        elif style == "math":
            surface = self.draw_ui_math(width, height)
        else:
            surface = self.draw_ui_teaching(width, height)
        # Pinned icons and number callouts go over whichever chrome was drawn.
        # A chapter with neither is left exactly as it was.
        from .callouts import draw_extras
        draw_extras(self, surface, width, height, style)
        # Last, over everything. A profile whose treatment is "clean" -- which
        # includes the empty profile every shipped film uses -- draws nothing
        # and this costs one attribute read.
        from .style_profiles import apply_treatment
        apply_treatment(self, surface, width, height)
        # Over absolutely everything, including a profile's own treatment: the
        # beat number. It is a reference, so it must never be the thing that
        # got covered up.
        self.draw_beat_badge(surface, width, height)
        return surface

    BEAT_BADGE = True
    """Whether the beat number is burned into the top-left of every frame.

    On for every render. It is how a person watching a cut says *"beat 11 is
    wrong"* instead of *"the bit about the seams, maybe six minutes in"*, and
    the whole point is that it is there without anybody having to ask for it.

    A lesson can set ``beat_badge=False`` if it ever needs a clean frame --
    nothing does today, and the plate style opts out on its own below because
    a printed book page is not a beat of anything."""

    # Where the badge goes on a teaching-style landscape frame, in the same
    # 1080-referenced units the badge is scaled in. Teaching puts a brand
    # bar across the top AND a chapter card under its left end, so the badge
    # cannot go down (it lands on the card) and cannot stay put (it lands on
    # the brand line). It slides right instead, into the empty middle of the
    # bar, which both measurements off a still agree is clear.
    BEAT_BADGE_TEACHING_RIGHT = 560

    def draw_beat_badge(self, surface, width: int, height: int) -> None:
        """A small number in the top-left corner: which beat this is.

        Deliberately plain and deliberately unmissable. It carries the
        chapter's own number, which is the same number the narration script,
        the release folder's thumbnails and the chapter list all use, so a
        note about "beat 11" points at exactly one thing.
        """
        # A plate is a page, not a frame of video. The beat number is a
        # reference into the film and means nothing beside a paragraph.
        if self.plate_mode:
            return
        if not getattr(self.lesson, "beat_badge", self.BEAT_BADGE):
            return
        chapter = self.chapters[self.chapter_index]
        style = chapter.overlay or self.lesson.style
        if style == "plate":
            return
        pg = self.pygame
        # Scaled off the frame's short side, so it is the same size on a
        # phone as it is on a television.
        unit = min(width, height) / 1080.0
        font = self.font(max(15, int(30 * unit)), True)
        text = font.render(str(chapter.number), True, (18, 24, 32))
        pad = int(12 * unit)
        margin = int(26 * unit)
        left, top = margin, margin
        # The teaching style hangs a brand bar across the top and a chapter
        # card under its left end. The badge slides right along the bar
        # rather than shrinking: it is meant to be read off a paused frame,
        # so it stays full size and moves.
        if style == "teaching" and not self.frame.portrait:
            left = margin + int(self.BEAT_BADGE_TEACHING_RIGHT * unit)
        box = pg.Rect(left, top,
                      text.get_width() + pad * 2, text.get_height() + pad)
        self.rounded_panel(surface, box, (245, 197, 66, 236),
                           (255, 236, 186, 255), int(7 * unit))
        surface.blit(text, (box.centerx - text.get_width() // 2,
                            box.centery - text.get_height() // 2))
        total = self.font(max(11, int(18 * unit)), True).render(
            f"/{len(self.chapters)}", True, (214, 228, 240))
        surface.blit(total, (box.right + int(7 * unit),
                             box.centery - total.get_height() // 2))

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

    # World labels on a book plate are set this much larger than in a film,
    # because a plate is printed a few inches wide and read at arm's length.
    PLATE_LABEL_SCALE = 1.45

    def draw_world_labels(self, surface, width: int, height: int,
                          scale: float) -> None:
        """The in-scene labels, on a backing panel, decluttered if asked."""
        pg = self.pygame
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

    def draw_ui_plate(self, width: int, height: int) -> object:
        """A clean picture for a printed plate: the scene and its labels.

        No headline, cards or worksheet -- the book sets its own caption
        under the picture. Pinned icons and any callouts still follow, from
        ``draw_extras``.
        """
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        self.ui_buttons.clear()
        scale = min(width / 1600.0, height / 900.0) * self.PLATE_LABEL_SCALE
        self.draw_world_labels(surface, width, height, scale)
        return surface

    def draw_ui_title(self, width: int, height: int) -> object:
        """A centered opening title over the live scene, with no competing labels."""
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        surface.fill((3, 9, 17, 168))
        self.ui_buttons.clear()
        chapter = self.chapters[self.chapter_index]
        scale = min(width / 1600., height / 900.)
        font = self.font(max(24, int(115 * scale)), True)
        lines = self.wrap_text(chapter.promise, font, int(width * .84))
        line_height = font.get_linesize()
        top = (height - len(lines) * line_height) // 2
        for index, line in enumerate(lines):
            text = font.render(line, True, (241, 249, 255))
            surface.blit(text, ((width - text.get_width()) // 2, top + index * line_height))
        small = self.font(max(14, int(24 * scale)), True)
        kicker = small.render(chapter.title.upper(), True, (255, 177, 62))
        surface.blit(kicker, ((width - kicker.get_width()) // 2, top - int(56 * scale)))
        pg.draw.rect(surface, (61, 211, 255),
                     (int(width * .36), top + len(lines) * line_height + int(32 * scale),
                      int(width * .28), max(2, int(4 * scale))))
        return surface

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
        self.draw_world_labels(surface, width, height, scale)

        # A scrim only under the type, so the picture stays clean.
        # The profile's accent and type size. Both default to exactly what this
        # chrome drew with before profiles existed, so a film with no profile
        # is pixel-identical.
        profile = getattr(self, "profile", None)
        accent = profile.accent if profile else (255, 177, 62)
        headline_font = self.font(
            max(30, int(54 * scale * (profile.headline_scale if profile else 1.0))),
            True)
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
        pg.draw.rect(surface, accent + (255,),
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
        if not self.plate_mode:
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

        # Bottom presenter controls and chapter timeline. Not drawn for a
        # plate: a printed page has no play button.
        if self.plate_mode:
            return surface
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

    # ------------------------------------------------------------------
    # Buildings borrowed from the Dome Creator
    # ------------------------------------------------------------------

    def creator_program_ready(self):
        """The Dome Creator's own scene program, compiled on first use.

        Its vertex format carries a material id and its fragment shader is what
        knows shingles from glass from mirror tiles, so a film that wants the
        tool's real product uses the tool's real program rather than a second
        one that would slowly drift away from it.
        """
        if self.creator_program is None:
            from .creator_bridge import shaders
            vertex, fragment = shaders()
            self.creator_program = self.ctx.program(vertex_shader=vertex,
                                                    fragment_shader=fragment)
        return self.creator_program

    def creator_uniform(self, name: str, value) -> None:
        program = self.creator_program_ready()
        try:
            program[name].value = value
        except KeyError:
            pass

    def creator_gpu(self, build) -> dict:
        """Upload one Creator building once and keep it for the whole render.

        A film asks for the same dome on every frame of a chapter; uploading
        forty thousand vertices thirty times a second would cost more than
        drawing them. Keyed by the configuration, so two chapters showing the
        same design share one upload.
        """
        entry = self.creator_cache.get(build.key)
        if entry is not None:
            return entry
        program = self.creator_program_ready()
        mesh = build.mesh
        if not len(mesh.vertices):
            # A build with nothing in it is a legitimate thing for a painter
            # to hand over -- the first step of a pad's construction is graded
            # ground, which draws no geometry at all. moderngl refuses an
            # empty buffer, and an exception here kills a render that is
            # already an hour in, so an empty build becomes an empty entry
            # and the draw loop skips it.
            entry = {"vbo": None, "opaque": None, "transparent": None,
                     "opaque_count": 0, "transparent_count": 0}
            self.creator_cache[build.key] = entry
            return entry
        vbo = self.ctx.buffer(
            np.ascontiguousarray(mesh.vertices, dtype="f4").tobytes())
        entry = {"vbo": vbo, "opaque": None, "transparent": None,
                 "opaque_count": 0, "transparent_count": 0}
        layout = [(vbo, "3f 3f 4f 1f", "in_position", "in_normal",
                   "in_color", "in_mat")]
        for kind in ("opaque", "transparent"):
            indices = np.ascontiguousarray(getattr(mesh, kind), dtype="u4")
            if not len(indices):
                continue
            ibo = self.ctx.buffer(indices.tobytes())
            entry[kind] = self.ctx.vertex_array(program, layout, ibo,
                                                index_element_size=4)
            entry[f"{kind}_count"] = len(indices)
            entry[f"{kind}_ibo"] = ibo
        self.creator_cache[build.key] = entry
        return entry

    def draw_creator(self, kind: str, eye) -> None:
        """Draw the buildings painters handed over, in the Creator's shader."""
        program = self.creator_program_ready()
        program["u_mvp"].write(np.ascontiguousarray(self.mvp.T).tobytes())
        self.creator_uniform("u_camera_position",
                             tuple(float(value) for value in eye))
        self.creator_uniform("u_light_direction", (-0.40, -0.25, -0.90))
        self.creator_uniform("u_sky_color",
                             tuple(float(value) for value in self.creator_sky))
        self.creator_uniform("u_ghost", 0.0)
        self.creator_uniform("u_headlamp", 0.0)
        lights = np.zeros((16, 3), dtype="f4")
        # The Creator draws without face culling: its shader flips the normal on
        # a back face, which is what lets a cut-away roof show a real interior
        # instead of a hole. Culling is restored before the overlay.
        self.ctx.disable(self.moderngl.CULL_FACE)
        if kind == "transparent":
            self.ctx.depth_mask = False
        for request in self.creator_draws:
            entry = self.creator_gpu(request.build)
            vao = entry.get(kind)
            if vao is None:
                continue
            count = entry[f"{kind}_count"]
            if request.limits is not None:
                # A prefix of the mesh is the tool's own half-built dome.
                count = min(count, int(
                    request.limits[0 if kind == "opaque" else 1]))
            if count <= 0:
                continue
            program["u_model"].write(
                np.ascontiguousarray(request.matrix().T).tobytes())
            self.creator_uniform("u_exposure", float(request.exposure))
            self.creator_uniform(
                "u_cut_z",
                1.0e9 if request.cut_z is None else float(request.cut_z))
            placed = request.world_lights()[:16]
            lights[:] = 0.0
            if placed:
                lights[:len(placed)] = np.asarray(placed, dtype="f4")
            self.creator_uniform("u_light_count", len(placed))
            try:
                program["u_light_positions"].write(lights.tobytes())
            except KeyError:
                pass
            vao.render(self.moderngl.TRIANGLES, vertices=count)
        if kind == "transparent":
            self.ctx.depth_mask = True
        self.ctx.enable(self.moderngl.CULL_FACE)

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
        adapting = self.adapting
        if adapting:
            # A screen of another shape: plan the overlay, paint the scene, then
            # give the film's own camera room for what was painted. Painters
            # never read the camera, so painting first changes nothing they do.
            self.portrait_plan = None
            # The lens the film chose, read back from its own projection, so
            # the renderer still states its field of view in one place.
            fov = math.degrees(2.0 * math.atan(1.0 / float(projection[1, 1])))
            region = self.plan_frame(width, height)
            opaque, transparent = self.build_scene(chapter.stage, self.chapter_progress)
            extra = [label.point for label in self.world_labels]
            if self.creator_draws:
                # Dome Creator buildings never pass through the film's batches,
                # so the fit is given their points directly; without this a
                # phone cut would frame an empty stage.
                from . import creator_bridge
                for placed in creator_bridge.draw_points(self):
                    extra.extend(placed)
            points = subject_points(opaque, transparent, self.scene_vertex_start,
                                    extra=extra)
            fit = fit_camera(eye, target, fov, width, height, region, points,
                             design_aspect=self.frame.design)
            if self.exporting:
                dolly, zoom, shift = self.fit_smoother(
                    self.chapter_index, fit.dolly, fit.zoom, fit.shift,
                    1.0 / max(1, self.export_fps))
                eye, projection = apply_fit(eye, target, fov, width, height,
                                            dolly, zoom, shift)
            else:
                eye, projection = fit.eye, fit.projection
        view = look_at(eye, target)
        self.mvp = projection @ view
        self.scene_program["u_mvp"].write(
            np.ascontiguousarray(self.mvp.T).tobytes()
        )
        self.scene_program["u_camera"].value = tuple(float(value) for value in eye)
        self.scene_program["u_light"].value = (-0.45, -0.55, -0.72)
        if not adapting:
            opaque, transparent = self.build_scene(chapter.stage, self.chapter_progress)

        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.ctx.depth_mask = True
        self.opaque_mesh.draw(opaque)
        if self.creator_draws:
            self.draw_creator("opaque", eye)
        if transparent.vertices:
            self.ctx.disable(self.moderngl.CULL_FACE)
            self.ctx.depth_mask = False
            self.transparent_mesh.draw(transparent)
            self.ctx.depth_mask = True
            self.ctx.enable(self.moderngl.CULL_FACE)
        if self.creator_draws:
            # Glass, films and sheeting last, over everything already solid.
            self.draw_creator("transparent", eye)

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
    def adapting(self) -> bool:
        """Whether this screen needs the film re-fitted to its shape (see frame.py)."""
        return self.frame.narrower and getattr(self.lesson, "frame_fit", "auto") != "off"

    def plan_frame(self, width: int, height: int):
        """The part of this screen the picture may use, decided before it is drawn."""
        from .frame import Rect
        chapter = self.chapters[self.chapter_index]
        style = chapter.overlay or self.lesson.style
        if self.frame.portrait:
            from . import portrait_ui
            self.portrait_plan = portrait_ui.plan(self, self.frame, style)
            self.overlay_free = self.portrait_plan.callout or self.portrait_plan.free
            return self.portrait_plan.free
        # A vertical film on a wide screen keeps the landscape overlays; the
        # picture goes where they leave room, as the callouts already assume.
        from .callouts import free_region
        self.overlay_free = None
        return Rect(*free_region(style, width, height))

    @property
    def speak_promise(self) -> bool:
        """Whether the voice reads the on-screen headline as well.

        Teaching lessons do: the promise is a separate summary line.
        A montage does not: its headline is a condensed form of the
        narration underneath it, so reading both says it twice.
        """
        return self.lesson.style != "hype"

    def retarget(self, lesson) -> None:
        """Point this app at a different lesson without rebuilding the GL context.

        Beat rendering makes forty small films in a row. Constructing a window, a
        context and the whole geometry cache for each one costs more than the renders
        do, so the app is built once and re-aimed. Everything reset here is everything
        __init__ derives from the chapter list.
        """
        lesson.validate()
        self.lesson = lesson
        self.frame = Frame(self.frame.width, self.frame.height, design_aspect(lesson.key))
        self.fit_smoother.reset()
        self.portrait_plan = None
        self.overlay_free = None
        self.chapters = lesson.chapters
        self.timeline = 0.0
        self.chapter_durations = tuple(c.duration for c in self.chapters)
        self.total_duration = timeline_duration(self.chapter_durations, self.chapters)
        # The previous lesson's voice must not time this lesson's callouts.
        self.speech_durations = None
        self.speech_clips = None
        self.chapter_index = 0
        self.chapter_progress = 0.0
        self.camera_yaw = self.chapters[0].camera[0]
        self.camera_pitch = self.chapters[0].camera[1]
        self.camera_distance = self.chapters[0].camera[2]
        self.camera_override = False
        self.playing = True

    def export_video(
        self,
        path: Path,
        fps: int = 30,
        *,
        render_fps: int | None = None,
        video_encoder: str = "libx264",
        video_preset: str = "medium",
        narration: bool = True,
        chapter_range: tuple[int, int] | None = None,
        local_narration_plan: Path | None = None,
        voice: str = DEFAULT_VOICE,
        voice_rate: str = DEFAULT_RATE,
        voice_pitch: str = DEFAULT_PITCH,
        voice_volume: str = DEFAULT_VOLUME,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
        mux_audio: bool = True,
    ) -> None:
        # Rendered output is append-only: a re-render lands beside the previous cut
        # rather than destroying it. See CLAUDE.md and next_version_path.
        from .deliverables import next_version_path
        versioned = next_version_path(path)
        if versioned != path:
            print(f"{path.name} already exists; rendering to {versioned.name}")
        path = versioned

        capture_fps = fps if render_fps is None else int(render_fps)
        if capture_fps < 1 or capture_fps > fps:
            raise ValueError("render_fps must be between 1 and the output fps")
        self.export_fps = capture_fps
        self.fit_smoother.reset()
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
            # Callouts cue on the measured voice, not an estimate of it.
            self.speech_durations = plan.speech_durations
            self.speech_clips = plan.clip_paths
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
            # Callouts cue on the measured voice, not an estimate of it.
            self.speech_durations = plan.speech_durations
            self.speech_clips = plan.clip_paths
            print(
                f"Natural narration: {voice}, {self.total_duration:.1f}s "
                f"across {len(self.chapters)} chapters"
            )
            if self.lesson.audio_bed:
                from .soundboard import mix_bed_into_track
                mix_bed_into_track(plan.track_path, self.lesson.audio_bed,
                                   ffmpeg, self.lesson.audio_bed_gain)
            # Kept beside the video, so a cut in another shape can say the same
            # words at the same moments without synthesizing them again.
            write_narration_plan(path.parent / f"{path.stem}-narration-plan.json",
                                 plan, speech_delay, self.chapters)
        width, height = self.pygame.display.get_window_size()
        # Tag the temp with this process, because two exports of the same
        # lesson to the same output otherwise share one hidden file: the
        # first to finish deletes it out from under the second, which then
        # muxes a truncated picture against a full narration track and
        # leaves a plausible-looking MP4 with seconds of video in it.
        render_path = (
            path.parent / f".{path.stem}-silent-render-{os.getpid()}.mp4"
            if plan is not None and mux_audio else path
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
        # ffmpeg's own chatter goes to a file beside the render, never to an
        # inherited handle.
        #
        # This is a deadlock fix, and the deadlock is worth describing because
        # it looks like a crash. ffmpeg prints a progress line per frame on
        # stderr. When that stderr is a pipe somebody upstream has stopped
        # draining -- a CI capture, a background task's log reader, an
        # orchestrator -- ffmpeg blocks writing it, and an ffmpeg blocked on
        # stderr is an ffmpeg that has stopped reading stdin. This loop then
        # blocks writing the next frame, and both processes sit at zero CPU
        # forever. A render that dies this way leaves a half-length mp4, no
        # traceback, and an exit code from whatever eventually kills it.
        #
        # Writing to a real file cannot block that way, and it also leaves the
        # encoder log where somebody can read it after a bad render.
        log_path = render_path.with_suffix(".ffmpeg.log")
        encoder_log = open(log_path, "wb")
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                       stdout=encoder_log, stderr=encoder_log)
        except Exception:
            encoder_log.close()
            raise
        # A chapter window turns one long render into several short ones.
        # Long renders on this machine die somewhere past the twenty-minute
        # mark for reasons that move when the workload does, and a segment
        # that finishes is worth more than a whole film that does not. The
        # frames are the same frames -- this only decides which of them this
        # process draws -- so the pieces join without a seam.
        first_frame, total_frames = 0, int(
            math.ceil(self.total_duration * capture_fps))
        audio_from = 0.0
        if chapter_range is not None:
            start, stop = chapter_range
            starts, clock = [], 0.0
            for duration in self.chapter_durations:
                starts.append(clock)
                clock += duration
            start = max(0, min(start, len(starts) - 1))
            stop = max(start + 1, min(stop, len(starts)))
            audio_from = starts[start]
            end_time = (starts[stop] if stop < len(starts)
                        else self.total_duration)
            first_frame = int(math.floor(audio_from * capture_fps))
            total_frames = int(math.ceil(end_time * capture_fps))
            print(f"chapters {start + 1}..{stop} -> "
                  f"{audio_from:.1f}s to {end_time:.1f}s")
        self.playing = False
        rendered_chapter = -1
        try:
            for frame in range(first_frame, total_frames):
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
            encoder_log.close()
        except BaseException:
            process.kill()
            encoder_log.close()
            raise
        print()
        if return_code != 0:
            raise RuntimeError(
                f"ffmpeg exited with status {return_code}; its own log is at "
                f"{log_path}")
        if plan is not None and mux_audio:
            # A segment takes the slice of the one narration track that
            # belongs to it, so every piece is cut from the same speech and
            # the joins do not drift.
            audio_in = ([] if audio_from <= 0.0
                        else ["-ss", f"{audio_from:.3f}"])
            mux_command = [
                ffmpeg, "-y",
                "-i", str(render_path),
                *audio_in, "-i", str(plan.track_path),
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
        if plan is not None:
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
        from video_review.render_bridge import write_render_receipt
        write_render_receipt(path, self.lesson, self.chapter_durations, {
            **getattr(self, "review_render_config", {}),
            "size": f"{width}x{height}", "fps": fps, "voice": voice,
            "voice_rate": voice_rate, "voice_pitch": voice_pitch,
            "voice_volume": voice_volume, "video_encoder": video_encoder,
            "video_preset": video_preset, "no_narration": plan is None,
        })
        self.exporting = False
        print(f"saved {path}")
        print(f"saved {script_path}")
        print(f"saved {subtitle_path}")


def write_narration_plan(target: Path, plan: NarrationPlan, speech_delay: float, chapters=None) -> Path:
    """The narration an export used, as a plan another export can replay.

    The vertical cut of a film has to say the same words at the same moments as
    the horizontal one. Replaying this through ``local_narration_plan`` gives it
    the same clips, track and chapter timing without synthesizing anything.
    """
    payload = {
        "schema": 1,
        "voice_profile": plan.voice,
        "track": str(Path(plan.track_path).resolve()),
        "clips": [str(Path(clip).resolve()) for clip in plan.clip_paths],
        "chapter_durations": list(plan.chapter_durations),
        "speech_durations": list(plan.speech_durations),
        "chapter_starts": list(plan.chapter_starts),
        "speech_delay": speech_delay,
    }
    if chapters is not None:
        from video_review.model import text_hash
        words = json.dumps([(c.promise, c.narration) for c in chapters], ensure_ascii=False)
        payload["review_words_sha256"] = text_hash(words)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def _chapter_range(cfg: dict) -> tuple[int, int] | None:
    """A ticket's "chapter_range": "5-9" as a zero-based half-open window."""
    raw = str(cfg.get("chapter_range") or "").strip()
    if not raw:
        return None
    if "-" not in raw:
        raise ValueError("chapter_range looks like '5-9' (1-based, inclusive)")
    first, last = raw.split("-", 1)
    return (int(first) - 1, int(last))


def _export_both(cfg: dict) -> int:
    """Export a film twice -- horizontal, then vertical -- with one narration.

    Each cut runs in its own process, because a window cannot change shape
    under a live GL context. The vertical cut replays the horizontal cut's
    narration plan, so both say the same words at the same moments and the
    speech service is asked once.
    """
    script = Path(__file__).resolve().parent.parent / "two_v_masterclass.py"
    target = Path(cfg["export_video"])
    folder = target.parent
    # The children render; this parent builds the one release folder and cuts
    # the one teaser once both cuts exist. Neither child is allowed either,
    # or a "both" export produces three teasers and two release folders.
    before = set(folder.glob(f"{target.stem}*.mp4")) if folder.is_dir() else set()
    # The children render; this parent builds the one release folder once
    # both cuts exist, so neither child is allowed to build its own.
    _lc.write_config("two_v_masterclass",
                     dict(cfg, orientation="landscape", release=False,
                          teaser=False))
    code = subprocess.call([sys.executable, str(script)])
    if code != 0:
        return code
    written = sorted(set(folder.glob(f"{target.stem}*.mp4")) - before,
                     key=lambda item: item.stat().st_mtime)
    landscape = written[-1] if written else target
    vertical = target.with_name(f"{target.stem}-vertical{target.suffix}")
    second = dict(cfg, orientation="portrait", export_video=str(vertical),
                  release=False, teaser=False)
    plan_path = landscape.parent / f"{landscape.stem}-narration-plan.json"
    if plan_path.is_file() and not cfg.get("no_narration"):
        second["local_narration_plan"] = str(plan_path)
    print(f"landscape cut: {landscape.name}; now the vertical cut")
    before_vertical = set(folder.glob(f"{vertical.stem}*.mp4"))
    _lc.write_config("two_v_masterclass", second)
    code = subprocess.call([sys.executable, str(script)])
    if code != 0:
        return code
    phone = sorted(set(folder.glob(f"{vertical.stem}*.mp4")) - before_vertical,
                   key=lambda item: item.stat().st_mtime)
    if cfg.get("release", True):
        _build_release(str(cfg.get("lesson") or ""), landscape,
                       phone[-1] if phone else None)
    _render_teaser(cfg, str(cfg.get("lesson") or ""))
    return 0


def teaser_tickets(cfg: dict) -> list[dict]:
    """Every ticket a "both" export writes, so the fan-out can be checked.

    Exists for the selftest. A `both` export spawns two children and each
    child goes down the single-orientation path, which also cuts a teaser --
    so without `teaser=False` on the children a single render produced three
    teasers. Counting the tickets is the cheapest way to notice that again.
    """
    landscape = dict(cfg, orientation="landscape", release=False,
                     teaser=False)
    portrait = dict(cfg, orientation="portrait", release=False, teaser=False)
    return [landscape, portrait]


def _render_teaser(cfg: dict, lesson_key: str) -> None:
    """Cut this film's teaser, as part of rendering the film.

    A teaser used to be a separate thing somebody remembered to ask for, which
    meant most films did not have one. It is now part of what "render" means:
    every export builds the short vertical cut as well, from the film's own
    chapters, into ``deliverables/teasers``.

    Never allowed to fail the render that came before it. By the time this
    runs the film is already safely on disk, and a teaser that would not build
    is not a reason to report the film as a failure -- it is a reason to print
    why and move on.
    """
    from .teasers import OUTPUT_DIR, PREFIX

    if not lesson_key or lesson_key.startswith(PREFIX):
        return
    if not cfg.get("teaser", True):
        return
    try:
        target = Path(OUTPUT_DIR) / f"{lesson_key}-teaser.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        script = Path(__file__).resolve().parent.parent / "two_v_masterclass.py"
        ticket = {key: value for key, value in cfg.items()
                  if key in ("fps", "render_fps", "video_encoder",
                             "video_preset", "voice", "ffmpeg", "ffprobe",
                             "no_narration")}
        ticket.update({
            "lesson": f"{PREFIX}{lesson_key}",
            "action": "export_video",
            "export_video": str(target),
            # Vertical, because a teaser is for a phone, and its own release
            # folder would be a folder holding one short file.
            "orientation": "portrait",
            "release": False,
            # The one flag that matters: without it this would render a
            # teaser of the teaser, and then a teaser of that.
            "teaser": False,
            # A teaser is a hook, not a chapter of a film; the shared outro
            # and call to action belong on the film.
            "compose_segments": False,
        })
        print(f"film done; now the teaser: {target.name}")
        _lc.write_config("two_v_masterclass", ticket)
        code = subprocess.call([sys.executable, str(script)])
        if code != 0:
            print(f"teaser not built: renderer exited {code}")
    except (OSError, ValueError, KeyError, RuntimeError,
            subprocess.CalledProcessError) as exc:
        print(f"teaser not built: {exc}")


def _build_release(lesson_key: str, cut: Path,
                   portrait: Path | None = None) -> None:
    """Thumbnails, platform copy and captions for a cut that just finished.

    Never allowed to fail the render that came before it: by the time this
    runs, an hour of frames is already safely on disk, and a missing thumbnail
    is not a reason to report that hour as a failure.
    """
    if not lesson_key:
        return
    try:
        from .release import build_release, newest_version
        release = build_release(lesson_key, video=newest_version(cut),
                                portrait=portrait)
    except (OSError, ValueError, KeyError, RuntimeError,
            subprocess.CalledProcessError) as exc:
        print(f"release folder not built: {exc}")
        return
    print(release.summary())


def parse_size(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("size must look like 1600x900") from exc
    if width < 960 or height < 540:
        raise ValueError("minimum supported size is 960x540")
    return width, height


def _render_beats_many(cfg: dict, requested: str) -> int:
    """Beat-render several films in one run, one child process each.

    Each film gets its own process so a crash in one cannot take the rest with it, and
    so its GL context is torn down cleanly before the next begins. Failures are
    collected and reported at the end rather than stopping the run.
    """
    from .lesson_registry import LESSONS

    if requested == "all":
        keys = list(LESSONS)
    else:
        keys = [k.strip() for k in requested.split(",") if k.strip()]
        unknown = [k for k in keys if k not in LESSONS]
        if unknown:
            print(f"unknown films: {', '.join(unknown)}")
            print(f"choose from: {', '.join(LESSONS)}")
            return 2

    script = Path(__file__).resolve().parent.parent / "two_v_masterclass.py"
    print(f"rendering beats for {len(keys)} films: {', '.join(keys)}")
    failures: list[str] = []
    for index, key in enumerate(keys, start=1):
        print(f"\n=== [{index}/{len(keys)}] {key} " + "=" * 40)
        child = dict(cfg)
        child["lesson"] = key
        # Framing is per film; a vertical drama in a landscape frame is not the film
        # that was written, so a bulk size is never inherited.
        child.pop("size", None)
        # Some films compose their own segments at import, so composing again appends a
        # second outro and share card.
        if child.get("compose_segments") and _already_composed(LESSONS[key]):
            print(f"    {key} composes its own segments; not composing again")
            child["compose_segments"] = False
        _lc.write_config("two_v_masterclass", child)
        code = subprocess.call([sys.executable, str(script)])
        if code != 0:
            failures.append(key)
            print(f"!!! {key} exited {code}; continuing with the rest")
    if failures:
        print(f"\nfinished with failures: {', '.join(failures)}")
        return 1
    print("\nall films rendered as beats")
    return 0


def _already_composed(lesson) -> bool:
    """True when a lesson module already spliced its segments in.

    Segments are appended, so composing a second time duplicates them. The tell is a
    lesson whose chapters already include segment slugs.
    """
    from .segments import SEGMENTS
    segment_slugs = {
        chapter.slug
        for segment in SEGMENTS.values()
        for chapter in segment.chapters
    }
    return any(chapter.slug in segment_slugs for chapter in lesson.chapters)


def main(default_lesson: str = "2v", *, config: dict | None = None) -> int:
    """Dispatch on the launcher's config ticket instead of argv.

    Launch and configure this from the consolidated launcher
    (``py -3.12 launcher.py``), which exposes every option below as a
    GUI field. Run directly with no ticket present and it opens the
    normal live presentation, fullscreen.
    """
    cfg = dict(config) if config is not None else _lc.consume_config("two_v_masterclass")
    action = cfg.get("action", "run")
    # Imported here, not at module scope: the lesson modules import this
    # module's render kit, so the registry can only be built once this
    # module has finished loading.
    from .lesson_registry import get_lesson, lesson_menu

    # A multi-film beat render names several lessons at once, which get_lesson cannot
    # resolve. Dispatch it before the single-lesson lookup rather than after it.
    _requested = str(cfg.get("lesson") or "").strip().lower()
    if action == "render_beats" and (_requested == "all" or "," in _requested):
        return _render_beats_many(cfg, _requested)

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
    if cfg.get("review_packet"):
        try:
            from video_review.render_bridge import apply_packet, load_packet
            packet = load_packet(cfg["review_packet"])
            lesson = apply_packet(lesson, cfg["review_packet"])
            if action in ("render_all", "render_beats"):
                raise ValueError("Review packets apply to one complete lesson; choose export_video, script, shots or run")
            target = cfg.get("export_video")
            if action == "export_video" and target and Path(target).exists():
                raise ValueError("Video Review preserves earlier renders. Choose a fresh Export MP4 filename.")
            if packet.get("narration_overrides") and cfg.get("local_narration_plan"):
                from video_review.model import read_json, text_hash
                plan = read_json(cfg["local_narration_plan"])
                words = json.dumps([(c.promise, c.narration) for c in lesson.chapters], ensure_ascii=False)
                if plan.get("review_words_sha256") != text_hash(words):
                    raise ValueError("The review changes narration. Generate fresh audio instead of reusing this narration plan.")
            remaining = sum(n.get("application") == "task" for n in packet.get("notes", []))
            print(f"Video Review: narration overlay loaded; {remaining} production tasks remain in the handoff prompt.")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"Video Review: {exc}")
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
        from .frame import validate_frame
        validate_frame()
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
    if action == "render_beats":
        from .beats import (BEATS_DIR, beat_plan, concat, plan_for, size_for,
                            sub_lesson, write_manifest)
        # lesson=all walks every film in the registry. Each is rendered in its own
        # framing and composed with its own segments, because a vertical drama in a
        # landscape frame is not the film that was written.
        lesson_key = str(cfg.get("lesson") or "why")
        root = Path(cfg.get("beats_dir") or BEATS_DIR)
        # Vertical films must not be rendered in a landscape frame; the size in the
        # ticket only wins if it was set deliberately.
        beat_size = parse_size(cfg.get("size") or size_for(lesson_key))
        orientation = str(cfg.get("orientation") or "").lower()
        if orientation in ("landscape", "portrait"):
            from .frame import size_for as frame_size
            beat_size = frame_size(orientation)
            # A cut in another shape is its own library, never mixed into the
            # composed film's sections.
            if Frame(*beat_size, design_aspect(lesson_key)).adapted:
                lesson_key = f"{lesson_key}-{orientation}"
        plan = beat_plan(lesson)
        write_manifest(lesson, root, lesson_key)
        rebuild = bool(cfg.get("force_rerender"))
        only = {k for k in str(cfg.get("beats_only") or "").split(",") if k}

        todo = [b for b in plan
                if (not only or b.key in only)
                and (rebuild or not b.path(root, lesson_key).is_file())]
        print(f"{len(plan)} beats, {len(todo)} to render "
              f"({len(plan) - len(todo)} already on disk)")

        app = MasterclassApp(size=beat_size, fullscreen=False, hidden=True,
                             lesson=lesson)
        try:
            for index, beat in enumerate(todo, start=1):
                target = beat.path(root, lesson_key)
                target.parent.mkdir(parents=True, exist_ok=True)
                print(f"[{index}/{len(todo)}] {beat.section}/{beat.key} "
                      f"-> {target.name}")
                app.retarget(sub_lesson(lesson, beat.slugs))
                app.export_video(
                    target, max(1, int(cfg.get("fps", 30))),
                    video_encoder=str(cfg.get("video_encoder", "libx264")),
                    video_preset=str(cfg.get("video_preset", "medium")),
                    narration=not no_narration,
                    voice=voice, voice_rate=voice_rate, voice_pitch=voice_pitch,
                    voice_volume=voice_volume, ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path)
        finally:
            app.pygame.quit()

        # Sections and the whole film are joins of the beats, not new renders, so a
        # single re-rendered beat costs seconds to fold back in at every level.
        if not cfg.get("no_join"):
            base = root / lesson_key
            section_files = []
            for section in plan_for(lesson):
                parts = [b.path(root, lesson_key) for b in plan
                         if b.section == section.key]
                parts = [p for p in parts if p.is_file()]
                if not parts:
                    continue
                out = base / "sections" / f"{section.key}.mp4"
                concat(parts, out, ffmpeg_path or "ffmpeg")
                section_files.append(out)
                print(f"joined {section.key}: {len(parts)} beats -> {out.name}")
            if section_files:
                whole = base / f"{lesson_key}-full-from-beats.mp4"
                concat(section_files, whole, ffmpeg_path or "ffmpeg")
                print(f"joined whole film -> {whole}")
        print(f"beat library: {root / lesson_key}")
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
    orientation = str(cfg.get("orientation") or "").lower()
    if action == "export_video" and cfg.get("export_video") and not orientation:
        # Every film is published as a set: the landscape cut, a phone cut and
        # a release folder. Asking for one shape is still possible by naming
        # it. A film composed for a single frame ("frame_fit off") keeps that
        # frame, because re-fitting it for a phone is exactly what it opted
        # out of.
        orientation = "both" if lesson.frame_fit != "off" else "landscape"
        cfg = dict(cfg, orientation=orientation)
    if action == "export_video" and cfg.get("export_video") and orientation == "both":
        return _export_both(cfg)
    try:
        size = parse_size(cfg.get("size", "1600x900"))
    except ValueError as exc:
        print(exc)
        return 2
    if orientation in ("landscape", "portrait"):
        from .frame import size_for as frame_size
        size = frame_size(orientation)
    app = MasterclassApp(
        size=size,
        fullscreen=bool(cfg.get("fullscreen", False)),
        hidden=action in ("shots", "export_video"),
        lesson=lesson,
    )
    if action == "shots":
        app.plate_mode = bool(cfg.get("plate", False))
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
        app.review_render_config = {key: cfg[key] for key in (
            "local_narration_plan", "render_fps", "orientation", "compose_segments",
            "segments_include", "segments_exclude", "ffmpeg", "ffprobe") if cfg.get(key)}
        try:
            app.export_video(
                Path(cfg["export_video"]), max(1, int(cfg.get("fps", 30))),
                render_fps=(
                    int(cfg["render_fps"]) if cfg.get("render_fps") else None
                ),
                video_encoder=str(cfg.get("video_encoder", "libx264")),
                video_preset=str(cfg.get("video_preset", "medium")),
                narration=not no_narration,
                chapter_range=_chapter_range(cfg),
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
        if cfg.get("release", True) and not cfg.get("chapter_range"):
            _build_release(lesson.key, Path(cfg["export_video"]))
        if not cfg.get("chapter_range"):
            _render_teaser(cfg, lesson.key)
        return 0
    app.run()
    return 0
