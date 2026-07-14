"""
Parametric Geodesic Dome Creator — a walkable build-a-home customizer.

Everything about the dome is live-editable from the in-world menu:
frequency, radius, strut shape/size, frame material and color, the
recessed interchangeable panels between struts (windows, shingles,
plastic sheeting, solar, ...), stacked cladding layers, and the
foundation (deck / concrete / gravel / pavers). A material breakdown
(weights, costs, strut cut list) updates in real time and can be
exported as a bill of materials.

Rendering keeps the original dual pipeline: a normal perspective view
and a full 360-degree six-point (azimuthal equidistant) projection.

Install:
    py -3.12 -m pip install pygame moderngl numpy

Run:
    py -3.12 dome_creator.py

Controls:
    M                   Open / close operations suite
    Arrows / Enter      Navigate menu, change values, apply
    Mouse aim + Click   Swap the aimed panel (right-click = previous type)
    V                   Apply the aimed panel's type to every panel
    W / A / S / D       Move        Shift  Sprint      Mouse  Look
    F                   Fly/walk    Space/Ctrl  Up/down in fly mode
    Tab                 Toggle six-point 360 / normal perspective
    Q / E               Roll the six-point image
    G                   Spherical guide grid      H   Toggle HUD
    F5 / F9 / F6        Save design / Load design / Export BOM
    R                   Reset player
    Escape              Release mouse; press again to quit
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from typing import Iterable

import moderngl
import numpy as np
import pygame

from dome_model import DomeConfig, DomeModel, FRAME_STYLES, HUB_STYLES
from materials import (
    FRAME_COLORS,
    FRAME_MATERIALS,
    FOUNDATION_TYPES,
    LAYER_TYPES,
    PANEL_COLORS,
    PANEL_TYPES,
    STRUT_SHAPES,
)
from mesh_builder import (
    Mesh,
    build_avatar_mesh,
    build_dome_mesh,
    build_environment,
    build_prop_mesh,
    build_worker_mesh,
    console_placement,
)
import overlay_ui
import workshop
from electrical import ElectricalSystem
from overlay_ui import Fonts, MenuItem
from workshop import PROP_TYPES, ROOM_TYPES, ROOM_TYPE_BY_NAME


WINDOW_WIDTH = 1720
WINDOW_HEIGHT = 960
CUBE_FACE_SIZE = 768
PLAYER_HEIGHT = 1.83
NEAR_PLANE = 0.06
FAR_PLANE = 500.0

DESIGN_FILE = "dome_design.json"
BOM_FILE = "dome_bom.txt"
DEMO_DB_FILE = "dome_demo.sqlite3"

PTZ_TEXTURE_SIZE = (960, 540)      # high-definition 16:9 video feed
VIDEO_WINDOW_SIZE = (384, 216)
VIDEO_WINDOW_SIZE_HELM = (640, 360)
HELM_RANGE = 4.0                   # max distance to click the wall screen
HELM_LEASH = 5.5                   # walk further than this and helm releases
RIGHT_RAIL_WIDTH = 340
SUITE_TABS = [
    ("SITE", "Site Command"),
    ("DOME", "Dome Editor"),
    ("ROOMS", "Interior Planner"),
    ("PROPS", "Equipment"),
    ("CREW", "Workforce"),
    ("MATERIALS", "Materials"),
    ("POWER", "Energy"),
    ("LAB", "Panel Lab"),
    ("FILES", "Administration"),
]
SUITE_MENU_PAGES = {"DOME": 0, "ROOMS": 1, "PROPS": 2,
                    "LAB": 3, "FILES": 4}


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def normalize(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32)
    length = float(np.linalg.norm(vector))
    if length <= 1e-8:
        return vector.copy()
    return vector / length


def perspective_matrix(fov_y_degrees, aspect, near, far) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_y_degrees) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at_matrix(eye, target, up_hint) -> np.ndarray:
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, up_hint))
    if np.linalg.norm(right) < 1e-6:
        right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0],
                                                     dtype=np.float32)))
    up = normalize(np.cross(right, forward))
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = right
    m[1, :3] = up
    m[2, :3] = -forward
    m[0, 3] = -float(np.dot(right, eye))
    m[1, 3] = -float(np.dot(up, eye))
    m[2, 3] = float(np.dot(forward, eye))
    return m


def rotation_about_axis(vector, axis, angle) -> np.ndarray:
    axis = normalize(axis)
    vector = np.asarray(vector, dtype=np.float32)
    c, s = math.cos(angle), math.sin(angle)
    return (vector * c + np.cross(axis, vector) * s
            + axis * float(np.dot(axis, vector)) * (1.0 - c)).astype(np.float32)


# ---------------------------------------------------------------------------
# Shaders
# ---------------------------------------------------------------------------

SCENE_VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
in float in_mat;

uniform mat4 u_mvp;
uniform mat4 u_model;

out vec3 v_world_position;
out vec3 v_normal;
out vec4 v_color;
flat out float v_mat;

void main() {
    vec4 world = u_model * vec4(in_position, 1.0);
    v_world_position = world.xyz;
    v_normal = mat3(u_model) * in_normal;
    v_color = in_color;
    v_mat = in_mat;
    gl_Position = u_mvp * world;
}
"""


SCENE_FRAGMENT_SHADER = """
#version 330

in vec3 v_world_position;
in vec3 v_normal;
in vec4 v_color;
flat in float v_mat;

uniform vec3 u_camera_position;
uniform vec3 u_light_direction;
uniform vec3 u_sky_color;
uniform float u_ghost;          // 0 off, 1 valid placement, 2 invalid
uniform float u_cut_z;          // roof fade: discard everything above
uniform float u_exposure;       // camera auto-exposure boost
uniform float u_headlamp;       // camera illuminator strength (PTZ pass)
uniform int u_light_count;      // placed lamp props
uniform vec3 u_light_positions[16];

out vec4 frag_color;

float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Procedural material patterns, keyed by mat id.
float surface_pattern(int id, vec3 p, vec3 n) {
    if (id == 1) {                                     // shingles
        float az = atan(p.y, p.x);
        vec2 g = vec2(az * 14.0, p.z * 3.6);
        g.x += step(0.5, fract(g.y * 0.5)) * 0.5;
        float fy = fract(g.y);
        float fx = fract(g.x);
        float row_gap = 1.0 - smoothstep(0.02, 0.12, fy);
        float col_gap = 1.0 - smoothstep(0.01, 0.06, fx);
        float shade = 0.95 + 0.10 * hash21(floor(g));
        return shade * (1.0 - 0.38 * max(row_gap, col_gap * 0.8));
    }
    if (id == 2) {                                     // plastic sheeting
        float w = sin(p.x * 7.0 + p.z * 5.0) * sin(p.y * 6.0 - p.z * 3.0);
        return 1.0 + 0.14 * w;
    }
    if (id == 4) {                                     // wood grain
        return 1.0 + 0.08 * sin((p.x + p.y) * 25.0 + sin(p.z * 8.0) * 2.0);
    }
    if (id == 5) {                                     // solar cells
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0))
            : cross(n, vec3(1.0, 0.0, 0.0)));
        vec3 t2 = cross(n, t1);
        vec2 uv = vec2(dot(p, t1), dot(p, t2)) * 3.0;
        vec2 f = abs(fract(uv) - 0.5);
        float line = 1.0 - smoothstep(0.44, 0.5, max(f.x, f.y));
        return 0.85 + 0.55 * (1.0 - line);
    }
    if (id == 6) {                                     // concrete
        float speck = 0.95 + 0.08 * hash21(floor(p.xy * 6.0));
        float jx = 1.0 - smoothstep(0.0, 0.02, abs(fract(p.x / 2.4) - 0.5) * 2.4 - 1.16);
        float jy = 1.0 - smoothstep(0.0, 0.02, abs(fract(p.y / 2.4) - 0.5) * 2.4 - 1.16);
        return speck * (1.0 - 0.25 * max(jx, jy));
    }
    if (id == 7) {                                     // deck planks
        float fy = fract(p.y / 0.145);
        float gap = 1.0 - smoothstep(0.02, 0.06, fy);
        float row = hash21(vec2(floor(p.y / 0.145), 0.0));
        float grain = 0.96 + 0.07 * sin(p.x * 40.0 + row * 20.0);
        return grain * (1.0 - 0.45 * gap);
    }
    if (id == 8) {                                     // grass
        float coarse = 0.90 + 0.16 * hash21(floor(p.xy * 1.5));
        float fine = 0.95 + 0.10 * hash21(floor(p.xy * 9.0));
        return coarse * fine;
    }
    if (id == 9) {                                     // ribbed metal
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0))
            : cross(n, vec3(1.0, 0.0, 0.0)));
        return 1.0 + 0.10 * sin(dot(p, t1) * 30.0);
    }
    if (id == 10) {                                    // canvas weave
        return 0.97 + 0.06 * sin(p.x * 90.0) * sin(p.y * 90.0)
             + 0.04 * sin(p.z * 70.0);
    }
    if (id == 11) {                                    // gravel
        return 0.85 + 0.16 * hash21(floor(p.xy * 22.0))
             + 0.08 * hash21(floor(p.xy * 5.0));
    }
    return 1.0;
}

void main() {
    if (v_world_position.z > u_cut_z) {
        discard;    // RuneScape-style hidden roof
    }

    vec3 normal = normalize(v_normal);
    if (!gl_FrontFacing) {
        normal = -normal;
    }

    vec3 light_direction = normalize(-u_light_direction);
    vec3 view_direction = normalize(u_camera_position - v_world_position);
    vec3 half_direction = normalize(light_direction + view_direction);

    float diffuse = max(dot(normal, light_direction), 0.0);
    float specular = pow(max(dot(normal, half_direction), 0.0), 48.0);
    float rim = pow(1.0 - max(dot(normal, view_direction), 0.0), 3.0);

    int mat_id = int(v_mat + 0.5);

    if (mat_id == 12) {
        // Emissive surfaces (lamp panels, status lights) ignore lighting.
        frag_color = vec4(v_color.rgb * 1.3, v_color.a);
        return;
    }

    float pattern = surface_pattern(mat_id, v_world_position, normal);

    vec3 base = v_color.rgb * pattern;
    vec3 lit = base * (0.40 + 0.62 * diffuse);
    lit += vec3(1.0, 0.98, 0.92) * specular * (mat_id == 3 ? 0.9 : 0.30);
    lit += u_sky_color * rim * (mat_id == 3 ? 0.45 : 0.12);

    // Point lights from placed workshop lamps (warm white, attenuated).
    vec3 point_sum = vec3(0.0);
    for (int i = 0; i < u_light_count; i++) {
        vec3 to_light = u_light_positions[i] - v_world_position;
        float dist = length(to_light);
        float atten = 3.5 / (1.0 + 0.6 * dist + 0.30 * dist * dist);
        point_sum += vec3(1.0, 0.92, 0.78) * atten
                   * max(dot(normal, to_light / dist), 0.0);
    }
    lit += base * point_sum;

    // Camera-mounted illuminator: lights whatever the PTZ looks at.
    if (u_headlamp > 0.0) {
        vec3 to_cam = u_camera_position - v_world_position;
        float cam_dist = length(to_cam);
        float boost = u_headlamp / (1.0 + 0.015 * cam_dist * cam_dist);
        lit += base * boost * max(dot(normal, to_cam / cam_dist), 0.0);
    }

    float alpha = v_color.a;
    if (mat_id == 3) {
        // Glass gets a fresnel-style opacity boost at grazing angles.
        alpha = clamp(alpha + rim * 0.5, 0.0, 1.0);
    }

    float dist = length(u_camera_position - v_world_position);
    float fog = clamp((dist - 90.0) / 220.0, 0.0, 0.9);

    if (u_ghost > 0.5) {
        vec3 tint = (u_ghost > 1.5)
            ? vec3(1.0, 0.25, 0.20)
            : vec3(0.30, 1.00, 0.45);
        lit = mix(lit, tint, 0.45);
        alpha = 0.55;
    }

    frag_color = vec4(mix(lit, u_sky_color, fog) * u_exposure, alpha);
}
"""


SCREEN_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
uniform mat4 u_mvp;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
"""

SCREEN_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() {
    vec3 color = texture(u_texture, v_uv).rgb;
    float scanline = 0.94 + 0.06 * sin(v_uv.y * 540.0);
    vec2 edge = abs(v_uv - 0.5) * 2.0;
    float vignette = 1.0 - 0.25 * pow(max(edge.x, edge.y), 6.0);
    frag_color = vec4(color * scanline * vignette * 1.08
                      + vec3(0.01, 0.015, 0.02), 1.0);
}
"""


HIGHLIGHT_VERTEX_SHADER = """
#version 330
in vec3 in_position;
uniform mat4 u_mvp;
void main() { gl_Position = u_mvp * vec4(in_position, 1.0); }
"""

HIGHLIGHT_FRAGMENT_SHADER = """
#version 330
uniform vec4 u_color;
out vec4 frag_color;
void main() { frag_color = u_color; }
"""


PANORAMA_VERTEX_SHADER = """
#version 330

in vec2 in_position;
out vec2 v_uv;

void main() {
    v_uv = in_position * 0.5 + 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


PANORAMA_FRAGMENT_SHADER = """
#version 330

in vec2 v_uv;

uniform sampler2D u_front;
uniform sampler2D u_back;
uniform sampler2D u_right;
uniform sampler2D u_left;
uniform sampler2D u_up;
uniform sampler2D u_down;

uniform vec2 u_resolution;
uniform float u_roll;
uniform bool u_show_grid;
uniform vec3 u_outside_color;

out vec4 frag_color;

const float PI = 3.14159265358979323846;

vec3 azimuthal_equidistant_ray(vec2 disk) {
    float radius = length(disk);
    float theta = radius * PI;
    float azimuth = atan(disk.y, disk.x) + u_roll;
    float sin_theta = sin(theta);
    return normalize(vec3(
        sin_theta * cos(azimuth),
        sin_theta * sin(azimuth),
        cos(theta)
    ));
}

vec4 sample_six_views(vec3 direction) {
    vec3 a = abs(direction);
    vec2 uv;

    if (a.z >= a.x && a.z >= a.y) {
        if (direction.z >= 0.0) {
            uv = vec2(direction.x, direction.y) / a.z * 0.5 + 0.5;
            return texture(u_front, uv);
        }
        uv = vec2(-direction.x, direction.y) / a.z * 0.5 + 0.5;
        return texture(u_back, uv);
    }
    if (a.x >= a.y) {
        if (direction.x >= 0.0) {
            uv = vec2(-direction.z, direction.y) / a.x * 0.5 + 0.5;
            return texture(u_right, uv);
        }
        uv = vec2(direction.z, direction.y) / a.x * 0.5 + 0.5;
        return texture(u_left, uv);
    }
    if (direction.y >= 0.0) {
        uv = vec2(direction.x, -direction.z) / a.y * 0.5 + 0.5;
        return texture(u_up, uv);
    }
    uv = vec2(direction.x, direction.z) / a.y * 0.5 + 0.5;
    return texture(u_down, uv);
}

float spherical_grid(vec3 direction) {
    float longitude = atan(direction.x, direction.z);
    float latitude = asin(clamp(direction.y, -1.0, 1.0));
    float line = min(abs(sin(longitude * 12.0)), abs(sin(latitude * 12.0)));
    return 1.0 - smoothstep(0.0, 0.035, line);
}

void main() {
    vec2 pixel = v_uv * u_resolution;
    vec2 center = u_resolution * 0.5;
    float diameter = min(u_resolution.x, u_resolution.y);
    vec2 disk = (pixel - center) / (diameter * 0.5);

    float radius = length(disk);
    if (radius > 1.0) {
        frag_color = vec4(u_outside_color, 1.0);
        return;
    }

    vec3 direction = azimuthal_equidistant_ray(disk);
    vec4 scene_color = sample_six_views(direction);

    if (u_show_grid) {
        float grid = spherical_grid(direction);
        scene_color.rgb = mix(scene_color.rgb, vec3(0.22, 0.48, 0.62),
                              grid * 0.22);
    }

    float rim = 1.0 - smoothstep(0.985, 1.0, radius);
    scene_color.rgb *= 0.72 + 0.28 * rim;
    frag_color = scene_color;
}
"""


NORMAL_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, v_uv); }
"""


OVERLAY_VERTEX_SHADER = """
#version 330

in vec2 in_position;
uniform vec4 u_rect;      // x, y, w, h in pixels (top-left origin)
uniform vec2 u_screen;
uniform int u_flip;       // 1 when drawing a GL-rendered (bottom-up) texture
out vec2 v_uv;

void main() {
    vec2 p01 = in_position * 0.5 + 0.5;
    vec2 pixel = u_rect.xy + p01 * u_rect.zw;
    vec2 ndc = vec2(
        pixel.x / u_screen.x * 2.0 - 1.0,
        1.0 - pixel.y / u_screen.y * 2.0
    );
    v_uv = vec2(p01.x, u_flip == 1 ? 1.0 - p01.y : p01.y);
    gl_Position = vec4(ndc, 0.0, 1.0);
}
"""

OVERLAY_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, v_uv); }
"""


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

@dataclass
class PlayerCamera:
    position: np.ndarray
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    fly_mode: bool = False
    movement_speed: float = 6.0
    sprint_multiplier: float = 3.0
    mouse_sensitivity: float = 0.0022

    def basis(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        forward = normalize(np.array([
            math.sin(self.yaw) * math.cos(self.pitch),
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
        ], dtype=np.float32))
        world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        right = normalize(np.cross(forward, world_up))
        if np.linalg.norm(right) < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        up = normalize(np.cross(right, forward))
        if abs(self.roll) > 1e-7:
            right = rotation_about_axis(right, forward, self.roll)
            up = rotation_about_axis(up, forward, self.roll)
        return forward, right, up


@dataclass
class PTZCamera:
    """Simulated pan-tilt-zoom camera hanging from the dome apex."""
    pan: float = 180.0      # degrees, azimuth (0 = north/+Y)
    tilt: float = 32.0      # degrees from straight down (0..100)
    fov: float = 58.0       # degrees, zoom = narrower fov
    pan_rate: float = 70.0
    tilt_rate: float = 45.0
    zoom_rate: float = 35.0

    def basis(self) -> tuple[np.ndarray, np.ndarray]:
        """Forward and no-roll up vector from pan/tilt."""
        p = math.radians(self.pan)
        t = math.radians(self.tilt)
        forward = np.array([
            math.sin(t) * math.sin(p),
            math.sin(t) * math.cos(p),
            -math.cos(t),
        ], dtype=np.float32)
        up = np.array([
            math.cos(t) * math.sin(p),
            math.cos(t) * math.cos(p),
            math.sin(t),
        ], dtype=np.float32)
        return normalize(forward), normalize(up)


def ray_triangle(origin, direction, v0, v1, v2) -> float | None:
    """Möller–Trumbore; returns hit distance or None."""
    e1 = v1 - v0
    e2 = v2 - v0
    pvec = np.cross(direction, e2)
    det = float(np.dot(e1, pvec))
    if abs(det) < 1e-9:
        return None
    inv = 1.0 / det
    tvec = origin - v0
    u = float(np.dot(tvec, pvec)) * inv
    if u < 0.0 or u > 1.0:
        return None
    qvec = np.cross(tvec, e1)
    v = float(np.dot(direction, qvec)) * inv
    if v < 0.0 or u + v > 1.0:
        return None
    t = float(np.dot(e2, qvec)) * inv
    return t if t > 0.05 else None


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class DomeCreatorApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

        pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
        )
        pygame.display.set_caption("Geodesic Dome Creator")

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.blend_func = (
            moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self.ctx.gc_mode = "auto"

        self.clock = pygame.time.Clock()
        self.running = True
        self.mouse_captured = True
        self.escape_armed = False
        self.six_point_enabled = False
        self.show_grid = False
        self.show_hud = True
        self.six_point_spin_speed = 0.0
        self.sky_color = (0.60, 0.74, 0.90)

        # The site holds any number of domes; menus/stats/camera follow
        # the active (selected) one.
        import presets
        first = DomeModel(DomeConfig.from_dict(presets.PRESETS[0][1]))
        self.domes: list[DomeModel] = [first]
        self.active_dome = 0
        self.rebuild_queue: set[int] = {0}

        self.camera = PlayerCamera(
            position=np.array(
                [0.0, -(self.model.config.radius * 2.0 + 6.0), PLAYER_HEIGHT],
                dtype=np.float32,
            ),
            pitch=0.06,
        )

        # Programs.
        self.scene_program = self.ctx.program(
            vertex_shader=SCENE_VERTEX_SHADER,
            fragment_shader=SCENE_FRAGMENT_SHADER,
        )
        self.highlight_program = self.ctx.program(
            vertex_shader=HIGHLIGHT_VERTEX_SHADER,
            fragment_shader=HIGHLIGHT_FRAGMENT_SHADER,
        )
        self.panorama_program = self.ctx.program(
            vertex_shader=PANORAMA_VERTEX_SHADER,
            fragment_shader=PANORAMA_FRAGMENT_SHADER,
        )
        self.normal_program = self.ctx.program(
            vertex_shader=PANORAMA_VERTEX_SHADER,
            fragment_shader=NORMAL_FRAGMENT_SHADER,
        )
        self.overlay_program = self.ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER,
        )
        self.screen_program = self.ctx.program(
            vertex_shader=SCREEN_VERTEX_SHADER,
            fragment_shader=SCREEN_FRAGMENT_SHADER,
        )

        self._create_screen_quad()
        self._create_render_targets()

        self.demo_notes: dict[str, str] = self._load_demo_notes()
        self.hover_info: dict | None = None
        self.hover_state: tuple | None = None
        self.tooltip_dirty = True
        self.note_edit: dict | None = None

        # PTZ camera system: one camera + feed + wall monitor per dome.
        self.ptzs: list[PTZCamera] = [PTZCamera()]
        self.consoles: list[dict] = [{}]
        self.feeds: list[dict] = [self._create_feed()]
        self.monitors: list[dict] = [self._create_monitor()]
        self.trackers: list = []
        import vision
        self.trackers.append(vision.VisionTracker())
        self._feed_cycle = 0
        self.helm_active = False
        self.helm_remote = False
        self.preset_index = 0
        self.aiming_screen = False
        self.aimed_screen_dome = 0
        self.screen_distance = 0.0
        self._osd_state: tuple | None = None

        # Prop placement and picking.
        self.placing = None                  # PropType while in place mode
        self.placing_from_slot: int | None = None   # backpack slot source
        self.moving_prop_source: dict | None = None
        self.ghost_yaw = 0.0
        self.ghost_pos = np.zeros(3)
        self.ghost_valid = False
        self.ghost_cache: dict[str, dict] = {}
        self.aimed_prop_index: int | None = None
        self.light_array = np.zeros((16, 3), dtype=np.float32)
        self.light_count = 0

        # RuneScape-style controls: orbit camera + click to move.
        self.control_mode = "orbit"          # "orbit" or "fp"
        self.orbit_yaw = math.pi             # look north at the dome
        self.orbit_pitch = 0.62
        self.orbit_dist = 11.0
        self.avatar_yaw = 0.0
        self.walk_target: np.ndarray | None = None
        self.pending_action: dict | None = None
        self.roof_hidden = False
        self.inventory_open = True
        self.inventory_selected: int | None = None
        self.inventory_rects: list = []
        self.inventory_origin = (0, 0)
        self.toolbar_rects: list = []
        self.toolbar_origin = (0, 0)
        self.widget_offsets: dict[str, tuple[float, float]] = {}
        self.widget_scales: dict[str, float] = {}
        self.widget_drag: dict | None = None
        self.toolbar_dirty = True
        self.inventory_dirty = True
        self.avatar_buffers = self._upload_mesh(build_avatar_mesh())
        self.marker_vbo = self.ctx.buffer(reserve=6 * 3 * 4)
        self.marker_vao = self.ctx.vertex_array(
            self.highlight_program,
            [(self.marker_vbo, "3f", "in_position")],
        )
        self.selected_ring_vbo = self.ctx.buffer(reserve=96 * 3 * 4)
        self.selected_ring_vao = self.ctx.vertex_array(
            self.highlight_program,
            [(self.selected_ring_vbo, "3f", "in_position")],
        )

        # Static environment mesh.
        self.env_buffers = self._upload_mesh(build_environment())

        # Construction simulation and the shared power grid.
        self.dome_buffers_list: list[dict | None] = [None]
        self.dome_events_list: list[list] = [[]]
        self.render_limits: dict[int, tuple[int, int]] = {}
        self.sim: dict | None = None
        self.worker_buffers = self._upload_mesh(build_worker_mesh())
        self.worker_states: list[dict] = []
        self.worker_open = False
        self.worker_dirty = True
        self.worker_seq = 0
        self.energy = ElectricalSystem()
        self.energy_open = False

        # RuneScape-style UI state.
        self.context_menu: dict | None = None
        self.legend_open = True
        self.domes_open = False
        self.dome_rows_rects: list = []
        self.dome_add_rect = None
        self.domes_origin = (0, 0)
        self.placing_dome: dict | None = None
        self.moving_dome: int | None = None
        self.menu_hit_map: dict = {"tabs": [], "rows": []}
        self.lab_base = 1
        self.lab_qty: dict[str, int] = {}
        self.lab_counter = 1

        self._rebuild_dome(0)

        # Aim highlight.
        self.highlight_vbo = self.ctx.buffer(reserve=3 * 3 * 4)
        self.highlight_vao = self.ctx.vertex_array(
            self.highlight_program,
            [(self.highlight_vbo, "3f", "in_position")],
        )

        # Overlays.
        self.fonts = Fonts()
        self.menu_open = False
        self.menu_page = 0
        self.menu_pages = ["DOME", "ROOMS", "PROPS", "LAB", "FILE"]
        self.menu_selected = 1
        self.menu_items = self._build_menu_items()
        self.menu_dirty = True
        self.stats_dirty = True
        self.stats_open = False
        self.help_open = True
        self.help_dirty = True
        self.suite_open = False
        self.suite_page = "SITE"
        self.suite_scroll = 0
        self.suite_dirty = True
        self.suite_hit_map: dict = {"tabs": [], "controls": []}
        self.suite_restore_capture = False
        self.aimed_panel = None
        self.aimed_panel_dome = 0
        self.ghost_dome = 0
        self.aimed_distance = 0.0
        self.flash_message = ""
        self.flash_until = 0.0
        self.overlay_textures: dict[str, dict] = {}
        self._update_overlay("crosshair", overlay_ui.render_crosshair())

        # Orbit (RuneScape-style) mode starts with a free, visible cursor.
        self._set_mouse_capture(False)
        self.escape_armed = False

        # Smoke-test mode: run a scripted sequence and quit.
        self.smoke_frames = int(os.environ.get("DOME_SMOKE", "0"))
        self.frame_count = 0

    # -- active-dome accessors ---------------------------------------------

    @property
    def model(self) -> DomeModel:
        return self.domes[self.active_dome]

    @property
    def ptz(self) -> PTZCamera:
        return self.ptzs[self.active_dome]

    @property
    def console(self) -> dict:
        return self.consoles[self.active_dome]

    @property
    def ptz_texture(self):
        return self.feeds[self.active_dome]["texture"]

    def _create_feed(self) -> dict:
        texture = self.ctx.texture(PTZ_TEXTURE_SIZE, components=3,
                                   dtype="f1")
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        depth = self.ctx.depth_renderbuffer(PTZ_TEXTURE_SIZE)
        fbo = self.ctx.framebuffer(color_attachments=[texture],
                                   depth_attachment=depth)
        return {"texture": texture, "depth": depth, "fbo": fbo}

    def _create_monitor(self) -> dict:
        vbo = self.ctx.buffer(reserve=6 * 5 * 4)
        vao = self.ctx.vertex_array(
            self.screen_program,
            [(vbo, "3f 2f", "in_position", "in_uv")])
        return {"vbo": vbo, "vao": vao}

    def _select_dome(self, idx: int, open_editor: bool = True) -> None:
        idx = max(0, min(idx, len(self.domes) - 1))
        changed = idx != self.active_dome
        if changed and self.helm_active:
            self._set_helm(False)
        self.active_dome = idx
        if open_editor:
            self._open_suite("DOME")
        elif self.suite_open and self.suite_page in SUITE_MENU_PAGES:
            self.menu_page = SUITE_MENU_PAGES[self.suite_page]
            self.menu_items = self._build_menu_items()
        self.stats_dirty = True
        self.help_dirty = True
        self.suite_dirty = True
        self._osd_state = None
        self._flash(f"Dome {idx + 1} controls open")

    # -- menu ------------------------------------------------------------

    def _mark_changed(self, dome: int | None = None) -> None:
        self.rebuild_queue.add(
            self.active_dome if dome is None else dome)
        self.menu_dirty = True
        self.stats_dirty = True
        self.suite_dirty = True

    def _open_suite(self, page: str) -> None:
        page = page if page in {key for key, _ in SUITE_TABS} else "SITE"
        if not self.suite_open:
            self.suite_restore_capture = self.mouse_captured
        if self.mouse_captured:
            self._set_mouse_capture(False)
        if self.helm_active:
            self._set_helm(False)
        self.suite_open = True
        self.suite_page = page
        self.suite_scroll = 0
        if page in SUITE_MENU_PAGES:
            self.menu_page = SUITE_MENU_PAGES[page]
            self.menu_items = self._build_menu_items()
            self.menu_selected = 1
        self.context_menu = None
        self.suite_dirty = True
        self.escape_armed = False

    def _close_suite(self) -> None:
        self.suite_open = False
        self.context_menu = None
        if self.suite_restore_capture and self.control_mode == "fp":
            self._set_mouse_capture(True)
        self.suite_restore_capture = False
        self.help_dirty = True

    def _begin_suite_dome_placement(self, name: str, data: dict) -> None:
        self._begin_dome_placement(name, data)
        self._close_suite()

    def _cancel_construction(self) -> None:
        if not self.sim:
            self._flash("No construction assignment is running")
            return
        self.render_limits.pop(self.sim["dome"], None)
        self.sim = None
        self.worker_states = []
        self.worker_dirty = True
        self.suite_dirty = True
        self._flash("Construction cancelled")

    def _set_crew_task(self, task: str) -> None:
        if not self.sim:
            self._flash("Start construction before assigning task focus")
            return
        self.sim["task"] = task
        for worker in self.worker_states:
            worker["task"] = task
        self.worker_dirty = True
        self.suite_dirty = True
        self._flash(f"Crew focus: {task}")

    def _minimap_click(self, pos, button: int) -> None:
        local = self._widget_local_pos("minimap", pos)
        world = overlay_ui.minimap_world_position(
            self.domes, self.camera.position, local)
        if world is None:
            self._flash("Click inside the minimap field to navigate")
            return
        x, y = world
        dome_idx = self._dome_at(x, y)
        if button == 3 and dome_idx is not None:
            self._open_context(self._dome_context_entries(dome_idx), pos)
            return
        if button != 1:
            return
        if dome_idx is not None:
            self._select_dome(dome_idx, open_editor=False)
        self.walk_target = np.array(
            [x, y, self.ground_height(x, y)], dtype=np.float64)
        self.pending_action = None
        destination = (f"inside dome {dome_idx + 1}"
                       if dome_idx is not None else "on the site")
        self._flash(f"Walking to minimap target {destination}")

    def _suite_action(self, action: str, pos) -> None:
        if action in ("active_prev", "active_next"):
            delta = -1 if action.endswith("prev") else 1
            self._select_dome(
                (self.active_dome + delta) % len(self.domes),
                open_editor=False)
        elif action == "summary_edit":
            self._open_suite("DOME")
        elif action == "summary_world":
            model = self.model
            x = float(model.origin[0])
            y = float(model.origin[1]) - model.floor_radius * 0.65
            self.walk_target = np.array(
                [x, y, self.ground_height(x, y)], dtype=np.float64)
            self.pending_action = None
            self._close_suite()
            self._flash(f"Walking toward dome {self.active_dome + 1}")
        elif action == "site_add":
            import presets
            entries = [
                (f"Place: {name}",
                 lambda name=name, data=data:
                     self._begin_suite_dome_placement(name, data))
                for name, data in presets.PRESETS
            ]
            entries.append(("Cancel", None))
            self._open_context(entries, pos)
        elif action.startswith("site_") and ":" in action:
            command, raw_idx = action.split(":", 1)
            idx = int(raw_idx)
            if idx >= len(self.domes):
                return
            if command == "site_edit":
                self._select_dome(idx, open_editor=False)
                self._open_suite("DOME")
            elif command == "site_move":
                self._select_dome(idx, open_editor=False)
                self.moving_dome = idx
                self._close_suite()
                self._flash(f"Moving dome {idx + 1}: click open ground")
            elif command == "site_grow":
                self._set_dome_radius(idx, self.domes[idx].config.radius * 1.10)
            elif command == "site_shrink":
                self._set_dome_radius(idx, self.domes[idx].config.radius * 0.90)
            elif command == "site_build":
                self.start_construction(idx)
            elif command == "site_delete":
                self._flash(self._remove_dome(idx))
        elif action == "crew_start":
            self.start_construction(self.active_dome)
        elif action == "crew_add":
            self._set_worker_count((self.sim or {}).get("workers", 0) + 1)
        elif action == "crew_remove":
            self._set_worker_count((self.sim or {}).get("workers", 2) - 1)
        elif action in ("crew_fast", "crew_slow"):
            if not self.sim:
                self._flash("No construction assignment is running")
            elif action == "crew_fast":
                self.sim["speed"] = min(self.sim["speed"] * 2.0, 32.0)
            else:
                self.sim["speed"] = max(self.sim["speed"] * 0.5, 0.1)
        elif action == "crew_stop":
            self._cancel_construction()
        elif action.startswith("crew_task:"):
            tasks = ["Frame assembly", "Panel install",
                     "Electrical rough-in", "Interior setup",
                     "Safety inspection"]
            self._set_crew_task(tasks[int(action.split(":", 1)[1])])
        elif action == "materials_export":
            from pathlib import Path
            Path(BOM_FILE).write_text(self.model.bom_text(), encoding="utf-8")
            self._flash(f"Exported {BOM_FILE}")
        elif action == "power_electrify":
            self._flash(self._electrify_dome())
        self.suite_dirty = True

    def _suite_click(self, pos, button: int) -> None:
        hit = self.suite_hit_map
        close = hit.get("close")
        if close and close.collidepoint(pos):
            self._close_suite()
            return
        for page, rect in hit.get("tabs", []):
            if rect.collidepoint(pos):
                self._open_suite(page)
                return
        for action, rect in hit.get("controls", []):
            if not rect.collidepoint(pos):
                continue
            if action.startswith("item"):
                index = int(action.split(":", 1)[1])
                if index >= len(self.menu_items):
                    return
                item = self.menu_items[index]
                if action.startswith("item_prev"):
                    if item.change:
                        item.change(-1)
                elif action.startswith("item_next"):
                    if item.change:
                        item.change(1)
                elif item.activate is not None and button == 1:
                    self._flash(item.activate())
                elif item.change is not None:
                    item.change(1 if button == 1 else -1)
                self.menu_selected = index
                if self.placing is not None or self.placing_dome is not None:
                    self._close_suite()
                self.suite_dirty = True
                return
            self._suite_action(action, pos)
            return

    def _build_menu_items(self) -> list[MenuItem]:
        builders = [self._menu_page_dome, self._menu_page_rooms,
                    self._menu_page_props, self._menu_page_lab,
                    self._menu_page_file]
        return builders[self.menu_page]()

    def _menu_helpers(self, items: list[MenuItem]):
        def choice(label, options, get_idx, set_idx):
            def value():
                return options[get_idx()]

            def change(delta):
                set_idx((get_idx() + delta) % len(options))
                self._mark_changed()

            items.append(MenuItem(label, "choice", value, change))

        def number(label, get, set_val, step, low, high, fmt):
            def value():
                return fmt(get())

            def change(delta):
                set_val(min(high, max(low, get() + delta * step)))
                self._mark_changed()

            items.append(MenuItem(label, "choice", value, change))

        def header(label):
            items.append(MenuItem(label, "header"))

        def action(label, fn):
            items.append(MenuItem(label, "action", activate=fn))

        return choice, number, header, action

    def _menu_page_dome(self) -> list[MenuItem]:
        cfg = self.model.config
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("STRUCTURE")
        choice("Frequency",
               [f"{i}V" for i in range(1, 5)],
               lambda: cfg.frequency - 1,
               lambda i: setattr(cfg, "frequency", i + 1))
        number("Radius",
               lambda: cfg.radius,
               lambda v: self._set_dome_radius(self.active_dome, v),
               0.5, 2.0, 15.0, lambda v: f"{v:.1f} m")
        number("Dome X",
               lambda: float(self.model.origin[0]),
               lambda v: self._move_dome_to(
                   self.active_dome, (v, float(self.model.origin[1]))),
               0.5, -80.0, 80.0, lambda v: f"{v:.1f} m")
        number("Dome Y",
               lambda: float(self.model.origin[1]),
               lambda v: self._move_dome_to(
                   self.active_dome, (float(self.model.origin[0]), v)),
               0.5, -80.0, 80.0, lambda v: f"{v:.1f} m")
        action("Move selected dome (click map)",
               lambda: (setattr(self, "moving_dome", self.active_dome),
                        f"Moving dome {self.active_dome + 1}: click open ground"))

        header("FRAME")
        choice("Strut shape",
               [s.name for s in STRUT_SHAPES],
               lambda: cfg.strut_shape,
               lambda i: setattr(cfg, "strut_shape", i))
        number("Strut width",
               lambda: cfg.strut_width,
               lambda v: setattr(cfg, "strut_width", v),
               0.005, 0.02, 0.35, lambda v: f"{v * 100:.1f} cm")
        number("Trunk length",
               lambda: cfg.trunk_stock_length,
               lambda v: self._set_trunk_stock_length(self.active_dome, v),
               0.3048, 0.0, 12.192, lambda v: (
                   "off" if v <= 0 else f"{v * 3.28084:.0f} ft"))

        def set_trunk_circumference(v):
            cfg.trunk_circumference = v
            if v > 0:
                cfg.strut_width = v / math.pi

        number("Trunk circumference",
               lambda: cfg.trunk_circumference,
               set_trunk_circumference,
               0.0254, 0.0, 1.524, lambda v: (
                   "off" if v <= 0 else f"{v * 39.3701:.0f} in"))
        choice("Material",
               [m.name for m in FRAME_MATERIALS],
               lambda: cfg.frame_material,
               lambda i: setattr(cfg, "frame_material", i))
        choice("Frame color",
               [c.name for c in FRAME_COLORS],
               lambda: cfg.frame_color,
               lambda i: setattr(cfg, "frame_color", i))
        choice("Frame style",
               FRAME_STYLES,
               lambda: FRAME_STYLES.index(cfg.frame_style),
               lambda i: setattr(cfg, "frame_style", FRAME_STYLES[i]))
        choice("Hub style",
               HUB_STYLES,
               lambda: HUB_STYLES.index(cfg.hub_style),
               lambda i: setattr(cfg, "hub_style", HUB_STYLES[i]))
        choice("Wedge curve",
               ["Inside", "Outside"],
               lambda: 1 if cfg.wedge_flip else 0,
               lambda i: setattr(cfg, "wedge_flip", bool(i)))

        header("PANELS")

        def panel_fill_value():
            return cfg.default_panel

        def panel_fill_change(delta):
            import materials
            names = materials.panel_type_names()
            current = (names.index(cfg.default_panel)
                       if cfg.default_panel in names else 0)
            cfg.default_panel = names[(current + delta) % len(names)]
            self._mark_changed()

        def panel_fill_apply():
            self.model.set_all_panels(cfg.default_panel)
            self._mark_changed()
            return f"All panels set to {cfg.default_panel}"

        items.append(MenuItem("Panel fill", "choice", panel_fill_value,
                              panel_fill_change, panel_fill_apply))
        choice("Panel color",
               [c.name for c in PANEL_COLORS],
               lambda: cfg.panel_color,
               lambda i: setattr(cfg, "panel_color", i))
        number("Recess depth",
               lambda: cfg.recess_pct,
               lambda v: setattr(cfg, "recess_pct", v),
               0.05, 0.05, 0.95, lambda v: f"{v * 100:.0f} %")

        header("CLADDING LAYERS")
        layer_names = [l.name for l in LAYER_TYPES]
        for slot in range(3):
            def layer_get(slot=slot):
                return layer_names.index(cfg.layers[slot])

            def layer_set(i, slot=slot):
                cfg.layers[slot] = layer_names[i]

            choice(f"Layer {slot + 1}", layer_names, layer_get, layer_set)

        header("SITE")
        foundation_names = [f.name for f in FOUNDATION_TYPES]
        choice("Foundation",
               foundation_names,
               lambda: foundation_names.index(cfg.foundation),
               lambda i: setattr(cfg, "foundation", foundation_names[i]))
        number("Foundation size",
               lambda: cfg.foundation_scale,
               lambda v: setattr(cfg, "foundation_scale", v),
               0.05, 1.0, 1.6, lambda v: f"x{v:.2f}")

        return items

    def _menu_page_rooms(self) -> list[MenuItem]:
        cfg = self.model.config
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("PARTITIONS")
        choice("Partition style",
               workshop.PARTITION_MODES,
               lambda: workshop.PARTITION_MODES.index(cfg.partitions),
               lambda i: setattr(
                   cfg, "partitions", workshop.PARTITION_MODES[i]))

        header("ROOM ASSIGNMENTS")
        room_names = [r.name for r in ROOM_TYPES]
        for section in range(10):
            def get_idx(section=section):
                return room_names.index(cfg.sections[section])

            def set_idx(i, section=section):
                cfg.sections[section] = room_names[i]

            choice(workshop.section_label(section), room_names,
                   get_idx, set_idx)
        return items

    def _menu_page_props(self) -> list[MenuItem]:
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        category = None
        for prop in PROP_TYPES:
            if prop.category != category:
                category = prop.category
                header(category)

            def start(prop=prop):
                self.placing = prop
                self.ghost_yaw = 0.0
                self.help_dirty = True
                return (f"Placing {prop.name} — aim at floor, click to "
                        "place, , . rotate, Esc done")

            watts = f", {prop.watts:.0f} W" if prop.watts else ""
            items.append(MenuItem(
                f"{prop.name}  (${prop.cost:,.0f}, {prop.weight:.0f} kg"
                f"{watts})", "action", activate=start))

        header("EDIT")

        def clear_props():
            count = len(self.model.config.props)
            self.model.config.props.clear()
            self._mark_changed()
            return f"Removed {count} props"

        action("Clear all props", clear_props)
        return items

    def _menu_page_lab(self) -> list[MenuItem]:
        """Panel Lab: compose custom panels from a base surface plus
        hardware components (brackets, screws, seals...)."""
        import materials
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("PANEL LAB — BASE SURFACE")
        base_names = [p.name for p in materials.PANEL_TYPES
                      if p.name != "Open"]
        self.lab_base = min(self.lab_base, len(base_names) - 1)

        def base_value():
            return base_names[self.lab_base]

        def base_change(delta):
            self.lab_base = (self.lab_base + delta) % len(base_names)
            self.menu_dirty = True

        items.append(MenuItem("Base panel", "choice", base_value,
                              base_change))

        header("COMPONENTS PER PANEL")
        for comp in materials.PANEL_COMPONENTS:
            def get_qty(comp=comp):
                return self.lab_qty.get(comp.name, 0)

            def change_qty(delta, comp=comp):
                qty = max(0, min(12, get_qty() + delta))
                self.lab_qty[comp.name] = qty
                self.menu_dirty = True

            def qty_value(comp=comp):
                extra = ""
                if comp.screws_each:
                    extra = f"  (+{comp.screws_each} screws ea)"
                return f"{get_qty()}{extra}"

            items.append(MenuItem(comp.name, "choice", qty_value,
                                  change_qty))

        header("RESULT")

        def totals_value():
            definition = {"base": base_names[self.lab_base],
                          "components": dict(self.lab_qty)}
            cost, weight, screws, minutes = \
                materials.custom_panel_extras(definition)
            return (f"+${cost:.0f}, +{weight:.1f} kg, {screws} scr, "
                    f"+{minutes:.0f} min")

        items.append(MenuItem("Per-panel extras", "choice",
                              totals_value, None))

        def create_panel():
            import materials as mats
            definition = {
                "base": base_names[self.lab_base],
                "components": {k: v for k, v in self.lab_qty.items()
                               if v > 0},
            }
            if not definition["components"]:
                return "Add at least one component first"
            name = f"Custom Mk{self.lab_counter} " \
                   f"({base_names[self.lab_base]})"
            self.lab_counter += 1
            mats.register_custom_panel(name, definition)
            self.model.config.default_panel = name
            self._mark_changed()
            return (f"Created '{name}' — applied as panel fill; also in "
                    "panel swap cycle")

        def apply_aimed():
            if self.aimed_panel is None:
                return "Aim at a panel first"
            customs = sorted(materials.CUSTOM_PANEL_DEFS)
            if not customs:
                return "Create a custom panel first"
            pmodel = self.domes[self.aimed_panel_dome]
            pmodel.set_panel(self.aimed_panel.key, customs[-1])
            self._mark_changed(self.aimed_panel_dome)
            return f"Applied {customs[-1]} to the aimed panel"

        action("Create custom panel", create_panel)
        action("Apply newest custom to aimed panel", apply_aimed)
        return items

    def _menu_page_file(self) -> list[MenuItem]:
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("SITE OPERATIONS")

        def sim_active():
            self.start_construction(self.active_dome)
            return f"Simulating dome {self.active_dome + 1} construction"

        def build_dome2():
            import presets
            return self._add_dome(presets.SECOND_DOME, simulate=True)

        def add_worker():
            if self.sim:
                self.sim["workers"] = min(self.sim["workers"] + 1, 8)
                return f"Crew size: {self.sim['workers']}"
            return "No construction running"

        action("Electrify dome (kit + outlets)", self._electrify_dome)
        action("Simulate construction (this dome)", sim_active)
        action("Build power-spoke dome (worker sim)", build_dome2)
        action("Add worker to crew", add_worker)

        header("PRESET SETUPS")
        import presets
        for idx, (name, _data) in enumerate(presets.PRESETS):
            action(f"Load: {name}",
                   lambda idx=idx: self._apply_preset(idx))

        header("FILE")

        def save_design():
            return self._save_design()

        def load_design():
            return self._load_design()

        def export_bom():
            from pathlib import Path
            Path(BOM_FILE).write_text(self.model.bom_text(), encoding="utf-8")
            return f"Exported {BOM_FILE}"

        def reset_player():
            self.camera.position[:] = (
                0.0, -(self.model.config.radius * 2.0 + 6.0),
                PLAYER_HEIGHT)
            self.camera.yaw = 0.0
            self.camera.pitch = 0.06
            self.camera.roll = 0.0
            self.walk_target = None
            self.pending_action = None
            return "Player position reset"

        action("Save design", save_design)
        action("Load design", load_design)
        action("Export bill of materials", export_bom)
        action("Reset player position", reset_player)

        return items

    def _menu_move(self, delta: int) -> None:
        n = len(self.menu_items)
        i = self.menu_selected
        for _ in range(n):
            i = (i + delta) % n
            if self.menu_items[i].kind != "header":
                self.menu_selected = i
                break
        self.menu_dirty = True

    def _flash(self, message: str | None) -> None:
        if message:
            self.flash_message = str(message)
            self.flash_until = time.perf_counter() + 3.0
            self.help_dirty = True

    # -- GPU resources -----------------------------------------------------

    def _create_screen_quad(self) -> None:
        quad = np.array([
            -1.0, -1.0, 1.0, -1.0, -1.0, 1.0,
            -1.0, 1.0, 1.0, -1.0, 1.0, 1.0,
        ], dtype=np.float32)
        self.quad_vbo = self.ctx.buffer(quad.tobytes())
        self.panorama_vao = self.ctx.vertex_array(
            self.panorama_program, [(self.quad_vbo, "2f", "in_position")])
        self.normal_vao = self.ctx.vertex_array(
            self.normal_program, [(self.quad_vbo, "2f", "in_position")])
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program, [(self.quad_vbo, "2f", "in_position")])

    def _create_render_targets(self) -> None:
        self.face_textures: dict[str, moderngl.Texture] = {}
        self.face_fbos: dict[str, moderngl.Framebuffer] = {}
        for name in ("front", "back", "right", "left", "up", "down"):
            texture = self.ctx.texture(
                (CUBE_FACE_SIZE, CUBE_FACE_SIZE), components=3, dtype="f1")
            texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            texture.repeat_x = False
            texture.repeat_y = False
            depth = self.ctx.depth_renderbuffer(
                (CUBE_FACE_SIZE, CUBE_FACE_SIZE))
            self.face_textures[name] = texture
            self.face_fbos[name] = self.ctx.framebuffer(
                color_attachments=[texture], depth_attachment=depth)

        width, height = pygame.display.get_window_size()
        self._make_normal_target(width, height)

    def _make_normal_target(self, width: int, height: int) -> None:
        self.normal_texture = self.ctx.texture(
            (max(1, width), max(1, height)), components=3, dtype="f1")
        self.normal_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.normal_depth = self.ctx.depth_renderbuffer(
            (max(1, width), max(1, height)))
        self.normal_fbo = self.ctx.framebuffer(
            color_attachments=[self.normal_texture],
            depth_attachment=self.normal_depth)

    def _recreate_window_target(self) -> None:
        width, height = pygame.display.get_window_size()
        self.normal_fbo.release()
        self.normal_depth.release()
        self.normal_texture.release()
        self._make_normal_target(width, height)
        self.help_dirty = True

    def _upload_mesh(self, mesh: Mesh) -> dict:
        vbo = self.ctx.buffer(mesh.vertices.tobytes())
        buffers = {"vbo": vbo, "opaque": None, "transparent": None,
                   "opaque_vao": None, "transparent_vao": None}
        layout = [(vbo, "3f 3f 4f 1f",
                   "in_position", "in_normal", "in_color", "in_mat")]
        if len(mesh.opaque):
            buffers["opaque"] = self.ctx.buffer(mesh.opaque.tobytes())
            buffers["opaque_vao"] = self.ctx.vertex_array(
                self.scene_program, layout, buffers["opaque"])
        if len(mesh.transparent):
            buffers["transparent"] = self.ctx.buffer(
                mesh.transparent.tobytes())
            buffers["transparent_vao"] = self.ctx.vertex_array(
                self.scene_program, layout, buffers["transparent"])
        return buffers

    def _release_buffers(self, buffers: dict | None) -> None:
        if not buffers:
            return
        for key in ("opaque_vao", "transparent_vao", "opaque",
                    "transparent", "vbo"):
            obj = buffers.get(key)
            if obj is not None:
                obj.release()

    def _rebuild_dome(self, idx: int) -> None:
        if idx >= len(self.domes):
            return
        model = self.domes[idx]
        model.rebuild()
        events: list = []
        mesh = build_dome_mesh(model, events=events)
        self.dome_events_list[idx] = events
        model.construction_hours = sum(e["hours"] for e in events)
        self._release_buffers(self.dome_buffers_list[idx])
        self.dome_buffers_list[idx] = self._upload_mesh(mesh)
        self.rebuild_queue.discard(idx)
        if idx == self.active_dome:
            self.stats_dirty = True
        if self.sim and self.sim["dome"] == idx:
            self._sim_refresh_events()
        self._refresh_lights()

        # Reposition this dome's wall monitor (bl, br, tr, tl corners).
        self.consoles[idx] = console_placement(model)
        bl, br, tr, tl = self.consoles[idx]["screen_corners"]
        data = np.array([
            [*bl, 0.0, 0.0], [*br, 1.0, 0.0], [*tr, 1.0, 1.0],
            [*bl, 0.0, 0.0], [*tr, 1.0, 1.0], [*tl, 0.0, 1.0],
        ], dtype=np.float32)
        self.monitors[idx]["vbo"].write(data.tobytes())

    def _add_dome(self, config_data: dict, origin=None,
                  simulate: bool = False) -> str:
        import vision
        cfg = DomeConfig.from_dict(config_data)
        if origin is None:
            edge = max(
                (float(m.origin[0]) + m.config.radius
                 * m.config.foundation_scale for m in self.domes),
                default=0.0)
            origin = (edge + cfg.radius * cfg.foundation_scale + 4.0, 0.0)
        ok, reason = self._dome_fits(origin, cfg)
        if not ok:
            return f"Cannot place dome: {reason}"
        model = DomeModel(cfg, origin=(float(origin[0]),
                                       float(origin[1])))
        self.domes.append(model)
        self.dome_buffers_list.append(None)
        self.dome_events_list.append([])
        self.ptzs.append(PTZCamera())
        self.consoles.append({})
        self.feeds.append(self._create_feed())
        self.monitors.append(self._create_monitor())
        self.trackers.append(vision.VisionTracker())
        idx = len(self.domes) - 1
        self._rebuild_dome(idx)
        if simulate:
            self.start_construction(idx)
            return f"Worker crew dispatched — constructing dome {idx + 1}"
        return f"Dome {idx + 1} placed"

    def _remove_dome(self, idx: int) -> str:
        if len(self.domes) <= 1:
            return "The last dome cannot be removed"
        if self.sim and self.sim["dome"] == idx:
            self.sim = None
            self.worker_states = []
            self.worker_dirty = True
        self._release_buffers(self.dome_buffers_list[idx])
        feed = self.feeds[idx]
        feed["fbo"].release()
        feed["depth"].release()
        feed["texture"].release()
        self.monitors[idx]["vao"].release()
        self.monitors[idx]["vbo"].release()
        for seq in (self.domes, self.dome_buffers_list,
                    self.dome_events_list, self.ptzs, self.consoles,
                    self.feeds, self.monitors, self.trackers):
            seq.pop(idx)
        self.render_limits.pop(idx, None)
        self.render_limits = {
            (k - 1 if k > idx else k): v
            for k, v in self.render_limits.items()}
        if self.sim and self.sim["dome"] > idx:
            self.sim["dome"] -= 1
        for worker in self.worker_states:
            if worker.get("dome", 0) > idx:
                worker["dome"] -= 1
        if self.active_dome >= len(self.domes):
            self.active_dome = len(self.domes) - 1
        self.menu_items = self._build_menu_items()
        self.menu_dirty = True
        self.stats_dirty = True
        self._refresh_lights()
        return f"Dome {idx + 1} demolished"

    def _all_models(self) -> list:
        return self.domes

    def _refresh_lights(self) -> None:
        """Point lights from lamps that are on, plugged in, and powered."""
        self.light_array[:] = 0.0
        count = 0
        for model in self._all_models():
            fh = model.foundation.height
            ox, oy = float(model.origin[0]), float(model.origin[1])
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None or prop.light_z is None:
                    continue
                if not self.energy.lamps_powered(model, entry):
                    continue
                if count >= 16:
                    break
                self.light_array[count] = (
                    ox + float(entry["x"]), oy + float(entry["y"]),
                    fh + prop.light_z)
                count += 1
        self.light_count = count

    # -- construction simulation ----------------------------------------------

    def _sim_events(self) -> list:
        return self.dome_events_list[self.sim["dome"]]

    def _sim_refresh_events(self) -> None:
        events = self._sim_events()
        self.sim["total"] = sum(e["hours"] for e in events)

    @staticmethod
    def _crew_factor(workers: int) -> float:
        # Diminishing returns: 4 workers ≈ 3.2x, 8 ≈ 5.9x.
        return max(1, workers) ** 0.85

    @staticmethod
    def _action_for_label(label: str) -> str:
        text = label.lower()
        if any(word in text for word in ("foundation", "floor", "deck")):
            return "Setting base"
        if any(word in text for word in ("strut", "hub", "frame")):
            return "Framing"
        if any(word in text for word in ("panel", "skin", "window")):
            return "Installing panels"
        if any(word in text for word in ("monitor", "camera", "computer")):
            return "Commissioning"
        if any(word in text for word in ("light", "wire", "outlet", "power")):
            return "Electrical"
        return "Building"

    def _new_worker(self, dome_idx: int, pos) -> dict:
        self.worker_seq += 1
        return {
            "id": self.worker_seq,
            "name": f"W{self.worker_seq:02d}",
            "dome": dome_idx,
            "task": f"Dome {dome_idx + 1} construction",
            "action": "Dispatching",
            "pos": np.array(pos, dtype=np.float64),
            "yaw": 0.0,
            "hours": 0.0,
            "distance": 0.0,
            "completed": 0,
        }

    def _set_worker_count(self, count: int) -> None:
        if not self.sim:
            self._flash("No construction assignment is running")
            return
        self.sim["workers"] = int(np.clip(count, 1, 8))
        self.worker_dirty = True
        self.suite_dirty = True
        self._flash(f"Crew size: {self.sim['workers']}")

    def start_construction(self, dome_idx: int) -> None:
        events = self.dome_events_list[dome_idx]
        if not events:
            return
        self.sim = {
            "dome": dome_idx,
            "elapsed": 0.0,
            "total": sum(e["hours"] for e in events),
            "speed": 1.0,          # simulated labor-hours per real second
            "step": 0,
            "workers": 1,
            "task": f"Dome {dome_idx + 1} construction",
        }
        self.render_limits[dome_idx] = (0, 0)
        self.worker_states = [self._new_worker(dome_idx, events[0]["pos"])]
        self.worker_dirty = True
        self._flash("Construction started — [ ] speed, right-click the "
                    "status bar for crew options")
        self.help_dirty = True

    def _update_construction(self, dt: float) -> None:
        if not self.sim:
            return
        sim = self.sim
        events = self._sim_events()
        if not events:
            self.sim = None
            return
        crew = self._crew_factor(sim["workers"])
        sim["elapsed"] += dt * sim["speed"] * crew
        acc = 0.0
        step = 0
        limits = (0, 0)
        for i, event in enumerate(events):
            if sim["elapsed"] >= acc + event["hours"]:
                acc += event["hours"]
                limits = (event["opaque"], event["transparent"])
                step = i + 1
            else:
                break
        sim["step"] = step
        self.render_limits[sim["dome"]] = limits

        # Crew members spread across the next work stations.
        while len(self.worker_states) < sim["workers"]:
            self.worker_states.append(
                self._new_worker(sim["dome"], self.worker_states[0]["pos"]))
        del self.worker_states[sim["workers"]:]
        step_label = events[min(step, len(events) - 1)]["label"]
        action = self._action_for_label(step_label)
        labor_delta = dt * sim["speed"] / max(1, sim["workers"])
        for w, worker in enumerate(self.worker_states):
            idx = min(step + w, len(events) - 1)
            t = np.array(events[idx]["pos"], dtype=np.float64)
            gap = t - worker["pos"]
            dist = float(np.linalg.norm(gap[:2]))
            if dist > 0.05:
                walk = min(2.2 * dt * max(sim["speed"], 1.0), dist)
                worker["pos"][:2] += gap[:2] / dist * walk
                worker["yaw"] = math.atan2(float(gap[0]), float(gap[1]))
                worker["distance"] = worker.get("distance", 0.0) + walk
            worker["pos"][2] = t[2]
            worker["dome"] = sim["dome"]
            worker["task"] = sim.get("task", f"Dome {sim['dome'] + 1}")
            worker["action"] = "Walking" if dist > 0.15 else action
            worker["hours"] = worker.get("hours", 0.0) + labor_delta
            worker["completed"] = max(worker.get("completed", 0), step)
        self.worker_dirty = True

        if sim["elapsed"] >= sim["total"]:
            dome = sim["dome"]
            self.render_limits.pop(dome, None)
            total = sim["total"]
            workers = sim["workers"]
            self.sim = None
            self.worker_states = []
            self.worker_dirty = True
            days = total / (8.0 * self._crew_factor(workers))
            self._flash(
                f"Dome {dome + 1} complete: {total:,.0f} labor-hours, "
                f"crew of {workers} → ~{days:,.0f} site-days @ 8 h")
            self._refresh_lights()
            self.stats_dirty = True

    # -- site actions ----------------------------------------------------------

    def _electrify_dome(self) -> str:
        cfg = self.model.config
        fr = self.model.floor_radius
        existing = {p["type"] for p in cfg.props}
        added = []

        def add(name, x, y, yaw=0.0):
            cfg.props.append({"type": name, "x": round(x, 2),
                              "y": round(y, 2), "yaw": yaw, "on": True})
            added.append(name)

        if "Battery Bank" not in existing:
            add("Battery Bank", -0.7, -fr * 0.62, 200.0)
        if "Charge Controller" not in existing:
            add("Charge Controller", 0.5, -fr * 0.66, 180.0)
        if "Power Meter LCD" not in existing:
            add("Power Meter LCD", 1.4, -fr * 0.60, 160.0)
        # Outlets around the outer wall (skipping the north doorway).
        outlet_r = fr - 0.55
        for az in (40, 90, 140, 220, 270, 320):
            a = math.radians(az)
            add("Wall Outlet", outlet_r * math.sin(a),
                outlet_r * math.cos(a), (az + 180.0) % 360.0)

        # A south-facing band of shell panels becomes solar.
        solar_set = 0
        for panel in self.model.panels:
            unit = (panel.centroid - self.model.sphere_center)
            unit = unit / np.linalg.norm(unit)
            if 0.2 < unit[2] < 0.7 and unit[1] < -0.35:
                cfg.panel_overrides[panel.key] = "Solar Panel"
                solar_set += 1

        self.energy.charge_kwh = max(self.energy.charge_kwh, 6.0)
        self._mark_changed()
        return (f"Electrified: battery kit, {added.count('Wall Outlet')} "
                f"outlets, {solar_set} solar panels")

    # -- investor demo notes --------------------------------------------------

    def _load_demo_notes(self) -> dict[str, str]:
        conn = sqlite3.connect(DEMO_DB_FILE)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS demo_notes ("
                "key TEXT PRIMARY KEY, note TEXT NOT NULL, "
                "updated_at REAL NOT NULL)")
            rows = conn.execute("SELECT key, note FROM demo_notes").fetchall()
            return {str(key): str(note) for key, note in rows}
        finally:
            conn.close()

    def _save_demo_note(self, key: str, note: str) -> None:
        self.demo_notes[key] = note
        conn = sqlite3.connect(DEMO_DB_FILE)
        try:
            conn.execute(
                "INSERT INTO demo_notes(key, note, updated_at) "
                "VALUES(?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET "
                "note=excluded.note, updated_at=excluded.updated_at",
                (key, note, time.time()))
            conn.commit()
        finally:
            conn.close()

    def _start_note_edit(self) -> None:
        if not self.hover_info:
            self._flash("Hover a dome, panel, prop, or camera first")
            return
        key = self.hover_info["key"]
        self.note_edit = {
            "key": key,
            "title": self.hover_info["title"],
            "text": self.demo_notes.get(key, self.hover_info["body"]),
        }
        pygame.key.start_text_input()
        self.tooltip_dirty = True

    def _finish_note_edit(self, save: bool) -> None:
        if not self.note_edit:
            return
        if save:
            self._save_demo_note(self.note_edit["key"],
                                 self.note_edit["text"].strip())
            self._flash("Investor note saved")
        else:
            self._flash("Investor note edit cancelled")
        self.note_edit = None
        pygame.key.stop_text_input()
        self.tooltip_dirty = True

    def _demo_hover_info(self) -> dict | None:
        if self.aiming_screen:
            dome = self.aimed_screen_dome
            return {
                "key": f"dome:{dome}:camera",
                "title": f"Dome {dome + 1} PTZ camera",
                "body": (
                    "Live investor demo camera: steerable PTZ feed, "
                    "vision detections, occupancy, and worker action "
                    "recognition per dome."),
            }
        aimed = self._aimed_prop()
        if aimed is not None:
            dome, _model, entry = aimed
            return {
                "key": f"dome:{dome}:prop:{entry['type']}",
                "title": f"{entry['type']} in dome {dome + 1}",
                "body": (
                    "Interactive fit-out object. Props affect BOM weight, "
                    "cost, power draw, room storytelling, and camera "
                    "detections."),
            }
        if self.aimed_panel is not None:
            p = self.aimed_panel
            dome = self.aimed_panel_dome
            return {
                "key": f"dome:{dome}:panel:{p.panel_type.name}",
                "title": f"{p.panel_type.name} panel",
                "body": (
                    f"Exterior panel slot area {p.area:.1f} m2. Click to "
                    "cycle materials, Ctrl-click to walk here, or press V "
                    "to apply this panel type across the dome."),
            }
        origin, direction = self._interaction_ray()
        point = self._floor_click_point(origin, direction)
        if point is None:
            return None
        dome = self._dome_at(float(point[0]), float(point[1]))
        if dome is None:
            return {
                "key": "site:open-ground",
                "title": "Open build site",
                "body": (
                    "Right-click open ground to place any preset dome. "
                    "The demo supports multi-dome site planning."),
            }
        model = self.domes[dome]
        s = model.stats()
        trunk = ""
        if s.get("trunk_stock_count"):
            trunk = (f" Uses {s['trunk_stock_count']} stock trunks at "
                     f"{s['trunk_stock_length'] * 3.28084:.0f} ft each.")
        return {
            "key": f"dome:{dome}:overview",
            "title": f"Dome {dome + 1}: {model.config.frequency}V, "
                     f"radius {model.config.radius:.1f} m",
            "body": (
                f"True-scale dome: height {s['height']:.1f} m, floor "
                f"{s['floor_area']:.0f} m2, frame "
                f"{s['frame_weight'] + s['hub_weight']:,.0f} kg."
                f"{trunk} Press T to edit this investor note."),
        }

    # -- overlays ----------------------------------------------------------

    def _update_overlay(self, name: str, surface: pygame.Surface) -> None:
        data = pygame.image.tobytes(surface, "RGBA", False)
        entry = self.overlay_textures.get(name)
        size = surface.get_size()
        if entry and entry["size"] == size:
            entry["texture"].write(data)
        else:
            if entry:
                entry["texture"].release()
            texture = self.ctx.texture(size, components=4, data=data)
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.overlay_textures[name] = {"texture": texture, "size": size}

    def _draw_texture(self, texture, size, x, y, flip=False) -> None:
        width, height = pygame.display.get_window_size()
        texture.use(location=0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_program["u_flip"].value = 1 if flip else 0
        self.overlay_program["u_screen"].value = (float(width), float(height))
        self.overlay_program["u_rect"].value = (
            float(x), float(y), float(size[0]), float(size[1]))
        self.overlay_vao.render(moderngl.TRIANGLES)

    def _draw_overlay(self, name: str, x: float, y: float) -> None:
        entry = self.overlay_textures.get(name)
        if not entry:
            return
        self._draw_texture(entry["texture"], entry["size"], x, y)

    def _video_window_rect(self) -> tuple[float, float, int, int]:
        w, h = (VIDEO_WINDOW_SIZE_HELM if self.helm_active
                else VIDEO_WINDOW_SIZE)
        return 16, 16, w, h

    def _default_widget_origin(self, name: str) -> tuple[float, float]:
        width, height = pygame.display.get_window_size()
        size = self._widget_display_size(name)
        if name == "video_osd":
            vx, vy, _, _ = self._video_window_rect()
            return vx, vy
        if name == "construction":
            return (width - size[0]) / 2, 12
        if name == "energy":
            return (width - size[0]) / 2, 84 if self.sim is not None else 12
        if name == "domes":
            menu_w = (self._widget_display_size("menu")[0]
                      if self.menu_open and "menu"
                      in self.overlay_textures else 0)
            menu_x = self._default_widget_origin("menu")[0]
            return (menu_x + menu_w + 12 if self.menu_open else menu_x), 16
        if name == "menu":
            video_w = self._widget_display_size("video_osd")[0]
            if video_w <= 0:
                video_w = self._video_window_rect()[2]
            return 16 + video_w + 12, 16
        if name == "stats":
            return width - RIGHT_RAIL_WIDTH + 12, 520
        if name == "help":
            return 16, height - size[1] - 12
        if name == "toolbar":
            return (max(1, width - RIGHT_RAIL_WIDTH) - size[0]) / 2, height - size[1] - 62
        if name == "inventory":
            return width - size[0] - 16, height - size[1] - 110
        if name == "workers":
            return width - RIGHT_RAIL_WIDTH + 12, 560
        if name == "minimap":
            return width - RIGHT_RAIL_WIDTH + 12, 16
        if name == "selected_dome":
            return width - RIGHT_RAIL_WIDTH + 12, 342
        if name == "stats":
            return width - RIGHT_RAIL_WIDTH + 12, 520
        if name == "tooltip":
            return 18, height - size[1] - 72
        if name == "note_editor":
            return (width - size[0]) / 2, (height - size[1]) / 2
        if name == "legend":
            return self._legend_origin()
        return 16, 16

    def _widget_scale(self, name: str) -> float:
        return self.widget_scales.get(name, 1.0)

    def _widget_display_size(self, name: str) -> tuple[float, float]:
        entry = self.overlay_textures.get(name)
        if not entry:
            return 0.0, 0.0
        scale = self._widget_scale(name)
        return entry["size"][0] * scale, entry["size"][1] * scale

    def _widget_rect(self, name: str) -> pygame.Rect:
        ox, oy = self._widget_origin(name)
        width, height = self._widget_display_size(name)
        return pygame.Rect(round(ox), round(oy), round(width), round(height))

    def _widget_local_pos(self, name: str, pos) -> tuple[float, float]:
        ox, oy = self._widget_origin(name)
        scale = self._widget_scale(name)
        return (pos[0] - ox) / scale, (pos[1] - oy) / scale

    def _widget_origin(self, name: str) -> tuple[float, float]:
        dx, dy = self.widget_offsets.get(name, (0.0, 0.0))
        ox, oy = self._default_widget_origin(name)
        entry = self.overlay_textures.get(name)
        if entry:
            width, height = pygame.display.get_window_size()
            display_w, display_h = self._widget_display_size(name)
            ox = float(np.clip(ox + dx, 0, max(0, width - display_w)))
            oy = float(np.clip(oy + dy, 0, max(0, height - display_h)))
            return ox, oy
        return ox + dx, oy + dy

    def _draw_widget(self, name: str) -> None:
        ox, oy = self._widget_origin(name)
        entry = self.overlay_textures.get(name)
        if entry:
            self._draw_texture(entry["texture"], self._widget_display_size(name),
                               ox, oy)
        if name == "toolbar":
            self.toolbar_origin = (ox, oy)
        elif name == "inventory":
            self.inventory_origin = (ox, oy)
        elif name == "domes":
            self.domes_origin = (ox, oy)

    def _refresh_suite_overlay(self) -> None:
        if not self.suite_open:
            return
        width, height = pygame.display.get_window_size()
        items = (self.menu_items
                 if self.suite_page in SUITE_MENU_PAGES else [])
        item_state = tuple(
            (item.label, item.kind,
             str(item.value()) if item.value is not None else "")
            for item in items)
        dome_state = tuple(
            (round(float(d.origin[0]), 2), round(float(d.origin[1]), 2),
             round(d.config.radius, 2), d.config.frequency,
             d.config.default_panel, d.config.foundation,
             tuple(d.config.sections), len(d.config.props))
            for d in self.domes)
        sim_state = None if self.sim is None else (
            self.sim.get("dome"), round(self.sim.get("elapsed", 0.0)),
            round(self.sim.get("total", 0.0)),
            round(self.sim.get("speed", 1.0), 1),
            self.sim.get("workers"), self.sim.get("task"),
            self.sim.get("step"))
        worker_state = tuple(
            (w.get("name"), w.get("dome"), w.get("task"),
             w.get("action"), round(w.get("hours", 0.0), 1),
             round(w.get("distance", 0.0), 1))
            for w in self.worker_states)
        energy_state = (
            round(self.energy.charge_kwh, 1),
            round(self.energy.capacity_kwh, 1),
            round(self.energy.solar_watts),
            tuple(round(v) for v in self.energy.load_by_dome),
            tuple(self.energy.lights_by_dome), self.energy.has_system,
            self.energy.battery_empty)
        state = (
            width, height, self.suite_page, self.suite_scroll,
            self.active_dome, dome_state, item_state, sim_state,
            worker_state, energy_state, self.flash_message)
        if not self.suite_dirty and getattr(self, "_suite_state", None) == state:
            return
        stats = self.model.stats()
        surface, hit_map = overlay_ui.render_management_suite(
            self.fonts, (width, height), self.suite_page, SUITE_TABS,
            items, self.suite_scroll, self.domes, self.active_dome,
            self.worker_states, self.sim, self.trackers, stats,
            self.energy, self.camera.position, self.flash_message)
        self.suite_scroll = min(
            self.suite_scroll, hit_map.get("scroll_max", 0))
        self.suite_hit_map = hit_map
        self._update_overlay("suite", surface)
        self._suite_state = state
        self.suite_dirty = False

    def _refresh_overlays(self) -> None:
        now = time.perf_counter()
        if self.flash_message and now > self.flash_until:
            self.flash_message = ""
            self.help_dirty = True

        if self.menu_dirty and self.menu_open:
            surface, hit_map = overlay_ui.render_menu(
                self.fonts, self.menu_items, self.menu_selected,
                self.menu_pages, self.menu_page)
            self.menu_hit_map = hit_map
            self._update_overlay("menu", surface)
            self.menu_dirty = False

        if "legend" not in self.overlay_textures:
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))

        if self.domes_open:
            rows = []
            for i, model in enumerate(self.domes):
                cfg = model.config
                mat = FRAME_MATERIALS[cfg.frame_material].name.split()[0]
                title = (f"{cfg.frequency}V {mat} "
                         f"r={cfg.radius:.0f}m — {cfg.default_panel}")
                if self.sim and self.sim["dome"] == i:
                    status = (f"BUILDING {self.sim['step']}"
                              f"/{len(self.dome_events_list[i])}")
                else:
                    status = "READY"
                load = (self.energy.load_by_dome[i]
                        if i < len(self.energy.load_by_dome) else 0.0)
                info = (f"{status} · {load:,.0f} W · "
                        f"{self.trackers[i].summary()}")
                rows.append({"title": title, "info": info})
            state = tuple((r["title"], r["info"]) for r in rows) + \
                (self.active_dome,)
            if getattr(self, "_domes_state", None) != state:
                surface, rects, add_rect = overlay_ui.render_dome_manager(
                    self.fonts, rows, self.active_dome)
                self.dome_rows_rects = rects
                self.dome_add_rect = add_rect
                self._update_overlay("domes", surface)
                self._domes_state = state
        if self.stats_dirty:
            self._update_overlay("stats", overlay_ui.render_stats(
                self.fonts, self.model.stats()))
            self.stats_dirty = False
        if self.help_dirty:
            width, _ = pygame.display.get_window_size()
            aim_text = ""
            if self.placing is not None:
                spot = "OK" if self.ghost_valid else "blocked"
                aim_text = (
                    f"Placing {self.placing.name} ({spot}) — click to "
                    "place, , . rotate, right-click/Esc finish"
                )
            elif self.moving_dome is not None:
                aim_text = (
                    f"Moving dome {self.moving_dome + 1}: click open "
                    "ground to place it; Esc/right-click cancels"
                )
            elif self.helm_active:
                aim_text = (
                    "HELM ACTIVE — arrow keys pan/tilt, PgUp/PgDn or "
                    "wheel zoom, click or Esc to release"
                )
            elif self._aimed_prop() is not None:
                dome_idx, model, entry = self._aimed_prop()
                section = model.section_at(
                    float(model.origin[0]) + float(entry["x"]),
                    float(model.origin[1]) + float(entry["y"]))
                room = ""
                if section >= 0:
                    room = f" in S{section + 1} " + \
                        model.config.sections[section]
                prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                if prop is not None and prop.watts > 0:
                    state = "ON" if entry.get("on", True) else "OFF"
                    aim_text = (
                        f"Dome {dome_idx + 1} {entry['type']}{room} "
                        f"[{state}, {prop.watts:.0f} W] — click to "
                        "switch, DEL to pack"
                    )
                else:
                    aim_text = (
                        f"Dome {dome_idx + 1} prop: {entry['type']}"
                        f"{room} — click to pick up, DEL to pack"
                    )
            elif self.aiming_screen:
                aim_text = (
                    "Console screen — click to TAKE HELM of the "
                    "PTZ camera"
                )
            elif self.aimed_panel is not None:
                aim_text = (
                    f"Aimed panel: {self.aimed_panel.panel_type.name}  "
                    f"({self.aimed_distance:.1f} m)  "
                    "— click to swap, right-click for options"
                )
            self._update_overlay("help", overlay_ui.render_help(
                self.fonts, max(200, width - RIGHT_RAIL_WIDTH - 32), aim_text,
                self.flash_message))
            self.help_dirty = False

        width, height = pygame.display.get_window_size()
        rail_state = (RIGHT_RAIL_WIDTH, height)
        if getattr(self, "_rail_state", None) != rail_state:
            self._update_overlay("side_rail", overlay_ui.render_side_rail(
                self.fonts, RIGHT_RAIL_WIDTH, height))
            self._rail_state = rail_state

        if self.hover_info is not None:
            key = self.hover_info["key"]
            state = (
                key, self.hover_info["title"], self.hover_info["body"],
                self.demo_notes.get(key, ""),
            )
            if self.tooltip_dirty or getattr(self, "_tooltip_state", None) != state:
                self._update_overlay("tooltip", overlay_ui.render_tooltip(
                    self.fonts, self.hover_info["title"],
                    self.hover_info["body"], self.demo_notes.get(key, "")))
                self._tooltip_state = state
                self.tooltip_dirty = False

        if self.note_edit is not None:
            state = (self.note_edit["title"], self.note_edit["text"])
            if getattr(self, "_note_edit_state", None) != state:
                self._update_overlay("note_editor",
                                     overlay_ui.render_note_editor(
                                         self.fonts,
                                         self.note_edit["title"],
                                         self.note_edit["text"]))
                self._note_edit_state = state

        if self.toolbar_dirty:
            buttons = [
                ("build", "Build", self.suite_open and self.suite_page == "DOME"),
                ("rooms", "Rooms", self.suite_open and self.suite_page == "ROOMS"),
                ("props", "Props", self.suite_open and self.suite_page == "PROPS"),
                ("lab", "Lab", self.suite_open and self.suite_page == "LAB"),
                ("domes", "Domes", self.suite_open and self.suite_page == "SITE"),
                ("bag", "Bag", self.inventory_open),
                ("cam", "Cam", self.helm_active),
                ("roof", "Roof", self.roof_hidden),
                ("pov", "POV", self.control_mode == "fp"),
                ("crew", "Crew", self.suite_open and self.suite_page == "CREW"),
                ("power", "Power", self.suite_open and self.suite_page == "POWER"),
                ("materials", "Materials", self.suite_open and self.suite_page == "MATERIALS"),
                ("help", "Help", self.help_open),
                ("keys", "Keys", self.legend_open),
                ("save", "Save", False),
                ("bom", "BOM", False),
            ]
            surface, rects = overlay_ui.render_toolbar(self.fonts, buttons)
            self._update_overlay("toolbar", surface)
            self.toolbar_rects = rects
            self.toolbar_dirty = False

        if self.inventory_dirty:
            surface, rects = overlay_ui.render_inventory(
                self.fonts, self.model.config.inventory,
                self.inventory_selected)
            self._update_overlay("inventory", surface)
            self.inventory_rects = rects
            self.inventory_dirty = False

        if self.energy_open:
            e = self.energy
            energy_state = (
                round(e.charge_kwh, 2), round(e.solar_watts),
                tuple(round(v) for v in e.load_by_dome),
                tuple(e.lights_by_dome), e.has_system, e.battery_empty,
                len(self._all_models()))
            if getattr(self, "_energy_state", None) != energy_state:
                self._update_overlay("energy", overlay_ui.render_energy(
                    self.fonts, e, len(self._all_models())))
                self._energy_state = energy_state

        if self.worker_open:
            worker_state = (
                tuple((w.get("name"), w.get("dome"), w.get("task"),
                       w.get("action"), round(w.get("hours", 0.0), 1),
                       round(w.get("distance", 0.0), 1))
                      for w in self.worker_states),
                None if self.sim is None else (
                    self.sim.get("dome"), self.sim.get("task"),
                    self.sim.get("step"), round(self.sim.get("elapsed", 0.0), 1),
                    round(self.sim.get("total", 0.0), 1)),
                tuple(tuple(t.current_actions) for t in self.trackers),
            )
            if self.worker_dirty or getattr(self, "_worker_state", None) != worker_state:
                self._update_overlay("workers", overlay_ui.render_workers(
                    self.fonts, self.sim, self.worker_states, self.trackers))
                self._worker_state = worker_state
                self.worker_dirty = False

        selected_state = (
            self.active_dome,
            round(float(self.model.origin[0]), 2),
            round(float(self.model.origin[1]), 2),
            round(self.model.config.radius, 2),
            self.moving_dome,
            len(self.domes),
        )
        if getattr(self, "_selected_dome_state", None) != selected_state:
            self._update_overlay(
                "selected_dome",
                overlay_ui.render_selected_dome_panel(
                    self.fonts, self.model, self.active_dome,
                    self.moving_dome == self.active_dome))
            self._selected_dome_state = selected_state

        minimap_state = (
            self.active_dome,
            self.moving_dome,
            round(float(self.camera.position[0]), 1),
            round(float(self.camera.position[1]), 1),
            (None if self.walk_target is None else
             (round(float(self.walk_target[0]), 1),
              round(float(self.walk_target[1]), 1))),
            tuple((round(float(d.origin[0]), 1),
                   round(float(d.origin[1]), 1),
                   round(d.config.radius, 1)) for d in self.domes),
        )
        if getattr(self, "_minimap_state", None) != minimap_state:
            self._update_overlay(
                "minimap",
                overlay_ui.render_minimap(
                    self.fonts, self.domes, self.active_dome,
                    self.camera.position, self.moving_dome,
                    self.walk_target))
            self._minimap_state = minimap_state

        if self.sim is not None:
            events = self._sim_events()
            step_idx = min(self.sim["step"], len(events) - 1)
            label = events[step_idx]["label"] if events else ""
            sim_state = (self.sim["dome"], self.sim["step"],
                         round(self.sim["elapsed"], 1),
                         round(self.sim["speed"], 2))
            if getattr(self, "_sim_state", None) != sim_state:
                width, _ = pygame.display.get_window_size()
                self._update_overlay(
                    "construction", overlay_ui.render_construction(
                        self.fonts, min(940, width - 40),
                        f"DOME {self.sim['dome'] + 1}", label,
                        self.sim["step"] + 1, len(events),
                        self.sim["elapsed"], self.sim["total"],
                        self.sim["speed"]))
                self._sim_state = sim_state

        # PTZ video window frame (readout changes while steering).
        _, _, vw, vh = self._video_window_rect()
        area_label, area_hint = self._ptz_watch_info()
        detect = self.trackers[self.active_dome].detect_text()
        osd_state = (round(self.ptz.pan, 1), round(self.ptz.tilt, 1),
                     round(self.ptz.fov, 1), self.helm_active,
                     self.aiming_screen, vw, area_label, area_hint,
                     detect, self.active_dome)
        if osd_state != self._osd_state:
            self._update_overlay("video_osd", overlay_ui.render_video_osd(
                self.fonts, (vw, vh), self.ptz.pan, self.ptz.tilt,
                self.ptz.fov, self.helm_active, self.aiming_screen,
                area_label, area_hint, detect,
                cam_label=f"CAM-{self.active_dome + 1:02d}"))
            self._osd_state = osd_state

        self._refresh_suite_overlay()

    def _render_overlays(self) -> None:
        width, height = pygame.display.get_window_size()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)

        if self.suite_open and "suite" in self.overlay_textures:
            self._draw_overlay("suite", 0, 0)
            if self.context_menu is not None \
                    and "context" in self.overlay_textures:
                self._draw_overlay("context", *self.context_menu["origin"])
            self.ctx.disable(moderngl.BLEND)
            self.ctx.enable(moderngl.DEPTH_TEST)
            return

        if "side_rail" in self.overlay_textures:
            self._draw_overlay("side_rail", width - RIGHT_RAIL_WIDTH, 0)
        if "minimap" in self.overlay_textures:
            self._draw_widget("minimap")
        if "selected_dome" in self.overlay_textures:
            self._draw_widget("selected_dome")

        # The PTZ video window is always on screen, minimap-style.
        _, _, vw, vh = self._video_window_rect()
        vx, vy = self._widget_origin("video_osd")
        scale = self._widget_scale("video_osd")
        display_size = (vw * scale, vh * scale)
        self._draw_texture(self.ptz_texture, display_size, vx, vy, flip=True)
        entry = self.overlay_textures.get("video_osd")
        if entry:
            self._draw_texture(entry["texture"], display_size, vx, vy)

        if self.sim is not None and "construction" in self.overlay_textures:
            self._draw_widget("construction")
        if self.energy_open and "energy" in self.overlay_textures:
            self._draw_widget("energy")
        if self.worker_open and "workers" in self.overlay_textures:
            self._draw_widget("workers")
        if self.hover_info is not None and "tooltip" in self.overlay_textures:
            self._draw_widget("tooltip")

        if self.show_hud:
            if self.legend_open or "legend" in self.overlay_textures:
                self._draw_widget("legend")
            if self.domes_open and "domes" in self.overlay_textures:
                self._draw_widget("domes")
            if self.menu_open and "menu" in self.overlay_textures:
                self._draw_widget("menu")
            if self.stats_open and "stats" in self.overlay_textures:
                self._draw_widget("stats")
            if self.help_open and "help" in self.overlay_textures:
                self._draw_widget("help")
            if "toolbar" in self.overlay_textures:
                self._draw_widget("toolbar")
            if self.inventory_open and "inventory" in self.overlay_textures:
                self._draw_widget("inventory")
            if self.control_mode == "fp" \
                    and "crosshair" in self.overlay_textures:
                entry = self.overlay_textures["crosshair"]
                self._draw_overlay(
                    "crosshair",
                    width / 2 - entry["size"][0] / 2,
                    height / 2 - entry["size"][1] / 2)

        # Context menu always renders on top.
        if self.context_menu is not None \
                and "context" in self.overlay_textures:
            self._draw_overlay("context", *self.context_menu["origin"])
        if self.note_edit is not None \
                and "note_editor" in self.overlay_textures:
            self._draw_widget("note_editor")

        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)

    # -- input -------------------------------------------------------------

    def _set_mouse_capture(self, enabled: bool) -> None:
        self.mouse_captured = enabled
        pygame.event.set_grab(enabled)
        pygame.mouse.set_visible(not enabled)
        pygame.mouse.get_rel()

    def process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self._recreate_window_target()

            elif event.type == pygame.KEYDOWN:
                if self.note_edit is not None:
                    if event.key == pygame.K_RETURN:
                        self._finish_note_edit(True)
                    elif event.key == pygame.K_ESCAPE:
                        self._finish_note_edit(False)
                    elif event.key == pygame.K_BACKSPACE:
                        self.note_edit["text"] = self.note_edit["text"][:-1]
                    continue
                self._handle_key(event.key)

            elif event.type == pygame.TEXTINPUT:
                if self.note_edit is not None:
                    self.note_edit["text"] = (
                        self.note_edit["text"] + event.text)[:520]

            elif event.type == pygame.MOUSEMOTION:
                if self.widget_drag is not None:
                    name = self.widget_drag["name"]
                    if self.widget_drag["mode"] == "scale":
                        dx = event.pos[0] - self.widget_drag["start"][0]
                        dy = event.pos[1] - self.widget_drag["start"][1]
                        entry = self.overlay_textures[name]
                        window_w, window_h = pygame.display.get_window_size()
                        max_scale = min(
                            2.0,
                            max(0.5, (window_w - 8) / entry["size"][0]),
                            max(0.5, (window_h - 8) / entry["size"][1]),
                        )
                        scale = float(np.clip(
                            self.widget_drag["scale"] + (dx + dy) * 0.003,
                            0.5, max_scale))
                        self.widget_scales[name] = scale
                        base = self._default_widget_origin(name)
                        anchor = self.widget_drag["origin"]
                        self.widget_offsets[name] = (
                            anchor[0] - base[0], anchor[1] - base[1])
                    else:
                        base = self._default_widget_origin(name)
                        offset = (
                            event.pos[0] - self.widget_drag["grab"][0] - base[0],
                            event.pos[1] - self.widget_drag["grab"][1] - base[1])
                        self.widget_offsets[name] = offset
                    continue
                if self.control_mode == "orbit" and event.buttons[1]:
                    self.orbit_yaw += event.rel[0] * 0.008
                    self.orbit_pitch = float(np.clip(
                        self.orbit_pitch + event.rel[1] * 0.006,
                        0.12, 1.45))
                if self.context_menu is not None:
                    row = self._context_row_at(event.pos)
                    if row != self.context_menu["hover"]:
                        self.context_menu["hover"] = row
                        self._render_context_overlay()
                elif self.menu_open and not self.mouse_captured:
                    lx, ly = self._widget_local_pos("menu", event.pos)
                    hover = None
                    for index, rect in self.menu_hit_map.get("rows", []):
                        if rect.collidepoint(lx, ly):
                            hover = index
                            break
                    if hover is not None and hover != self.menu_selected:
                        self.menu_selected = hover
                        self.menu_dirty = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):
                    self._on_mouse_button(event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.widget_drag = None

            elif event.type == pygame.MOUSEWHEEL:
                if self.suite_open:
                    max_scroll = self.suite_hit_map.get("scroll_max", 0)
                    self.suite_scroll = int(np.clip(
                        self.suite_scroll - event.y * 3, 0, max_scroll))
                    self.suite_dirty = True
                elif self.helm_active:
                    self.ptz.fov = float(np.clip(
                        self.ptz.fov - event.y * 4.0, 12.0, 80.0))
                elif self.control_mode == "orbit":
                    self.orbit_dist = float(np.clip(
                        self.orbit_dist - event.y * 1.2, 2.5, 22.0))
                else:
                    self.camera.movement_speed = float(np.clip(
                        self.camera.movement_speed + event.y, 2.0, 30.0))

    def _ui_hit(self, pos) -> str | None:
        """Which UI region a screen point lands in, if any."""
        if self.suite_open:
            return "suite"
        x, y = pos
        toolbar_local = self._widget_local_pos("toolbar", pos)
        for bid, rect in self.toolbar_rects:
            if rect.collidepoint(*toolbar_local):
                return f"toolbar:{bid}"
        if self.inventory_open:
            inventory_local = self._widget_local_pos("inventory", pos)
            for i, rect in enumerate(self.inventory_rects):
                if rect.collidepoint(*inventory_local):
                    return f"slot:{i}"
            entry = self.overlay_textures.get("inventory")
            if entry and self._widget_rect("inventory").collidepoint(x, y):
                return "panel"
        if self.context_menu is not None:
            entry = self.overlay_textures.get("context")
            if entry and pygame.Rect(*self.context_menu["origin"],
                                     *entry["size"]).collidepoint(x, y):
                return "context"
        if self.domes_open:
            entry = self.overlay_textures.get("domes")
            if entry and self._widget_rect("domes").collidepoint(x, y):
                return "domes"
        entry = self.overlay_textures.get("legend")
        if entry and self._widget_rect("legend").collidepoint(x, y):
            return "legend"
        if self.menu_open:
            entry = self.overlay_textures.get("menu")
            if entry and self._widget_rect("menu").collidepoint(x, y):
                return "menu"
        if self.worker_open:
            entry = self.overlay_textures.get("workers")
            if entry and self._widget_rect("workers").collidepoint(x, y):
                return "workers"
        if self.hover_info is not None:
            entry = self.overlay_textures.get("tooltip")
            if entry and self._widget_rect("tooltip").collidepoint(x, y):
                return "tooltip"
        if self.note_edit is not None:
            entry = self.overlay_textures.get("note_editor")
            if entry and self._widget_rect("note_editor").collidepoint(x, y):
                return "note_editor"
        for name in ("minimap", "selected_dome", "side_rail"):
            entry = self.overlay_textures.get(name)
            if not entry:
                continue
            if name == "side_rail":
                origin = (pygame.display.get_window_size()[0] - RIGHT_RAIL_WIDTH, 0)
                rect = pygame.Rect(*origin, *entry["size"])
            else:
                rect = self._widget_rect(name)
            if rect.collidepoint(x, y):
                return name
        for name in ("stats", "help", "video_osd", "energy", "construction"):
            entry = self.overlay_textures.get(name)
            if not entry:
                continue
            if name == "energy":
                if not self.energy_open:
                    continue
            elif name == "stats":
                if not self.stats_open:
                    continue
            elif name == "help":
                if not self.help_open:
                    continue
            elif name == "construction":
                if self.sim is None:
                    continue
            if self._widget_rect(name).collidepoint(x, y):
                return name
        return None

    def _widget_at(self, pos) -> str | None:
        names = [
            "note_editor", "context", "toolbar", "inventory", "workers",
            "selected_dome", "minimap", "tooltip", "domes", "menu",
            "energy", "construction", "stats", "legend", "video_osd", "help",
        ]
        for name in names:
            entry = self.overlay_textures.get(name)
            if not entry:
                continue
            if name == "context" and self.context_menu is None:
                continue
            if name == "inventory" and not self.inventory_open:
                continue
            if name == "workers" and not self.worker_open:
                continue
            if name == "tooltip" and self.hover_info is None:
                continue
            if name == "note_editor" and self.note_edit is None:
                continue
            if name == "domes" and not self.domes_open:
                continue
            if name == "menu" and not self.menu_open:
                continue
            if name == "energy" and not self.energy_open:
                continue
            if name == "stats" and not self.stats_open:
                continue
            if name == "help" and not self.help_open:
                continue
            if name == "construction" and self.sim is None:
                continue
            if name == "context":
                rect = pygame.Rect(*self.context_menu["origin"], *entry["size"])
            else:
                rect = self._widget_rect(name)
            if rect.collidepoint(*pos):
                return name
        return None

    def _floor_click_point(self, origin, direction) -> np.ndarray | None:
        dz = float(direction[2])
        if dz >= -1e-5:
            return None
        for model in self.domes:
            fh = model.foundation.height
            if fh <= 0.0:
                continue
            t = (fh - float(origin[2])) / dz
            if t > 0.05:
                hit = origin + direction * t
                lx = hit[0] - float(model.origin[0])
                ly = hit[1] - float(model.origin[1])
                if math.hypot(lx, ly) <= model.floor_radius * 1.02:
                    return np.array([hit[0], hit[1], fh])
        t = (0.0 - float(origin[2])) / dz
        if t > 0.05:
            hit = origin + direction * t
            if abs(hit[0]) < 80 and abs(hit[1]) < 80:
                return np.array([hit[0], hit[1], 0.0])
        return None

    def _dome_at(self, x: float, y: float) -> int | None:
        for i, model in enumerate(self.domes):
            dx = x - float(model.origin[0])
            dy = y - float(model.origin[1])
            if math.hypot(dx, dy) <= model.floor_radius * 1.05:
                return i
        return None

    def _inside_dome(self, dome_idx: int, position=None) -> bool:
        """Whether the avatar occupies a dome's usable interior."""
        if not 0 <= dome_idx < len(self.domes):
            return False
        model = self.domes[dome_idx]
        position = self.camera.position if position is None else position
        dx = float(position[0]) - float(model.origin[0])
        dy = float(position[1]) - float(model.origin[1])
        floor_z = float(model.foundation.height)
        top_z = floor_z + float(model.config.radius) * 1.5 + PLAYER_HEIGHT
        return (
            math.hypot(dx, dy) <= model.floor_radius * 0.98
            and floor_z + 0.25 <= float(position[2]) <= top_z
        )

    def _point_inside_dome(self, dome_idx: int, point) -> bool:
        if not 0 <= dome_idx < len(self.domes):
            return False
        model = self.domes[dome_idx]
        dx = float(point[0]) - float(model.origin[0])
        dy = float(point[1]) - float(model.origin[1])
        return math.hypot(dx, dy) <= model.floor_radius * 0.98

    def _walk_to_panel_exterior(self, dome_idx: int, panel) -> None:
        """Walk to open ground just outside the selected shell panel."""
        model = self.domes[dome_idx]
        dx = float(panel.centroid[0]) - float(model.origin[0])
        dy = float(panel.centroid[1]) - float(model.origin[1])
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            dx, dy, length = 0.0, -1.0, 1.0
        distance = model.floor_radius + 1.2
        x = float(model.origin[0]) + dx / length * distance
        y = float(model.origin[1]) + dy / length * distance
        self.walk_target = np.array([x, y, self.ground_height(x, y)])
        self.pending_action = None
        self._flash(f"Walking outside dome {dome_idx + 1}...")

    @staticmethod
    def _dome_clearance_radius(model_or_cfg) -> float:
        cfg = getattr(model_or_cfg, "config", model_or_cfg)
        return float(cfg.radius) * float(cfg.foundation_scale)

    def _dome_fits(self, origin, cfg, ignore_idx: int | None = None) -> tuple[bool, str]:
        ox, oy = float(origin[0]), float(origin[1])
        radius = self._dome_clearance_radius(cfg)
        for i, model in enumerate(self.domes):
            if ignore_idx is not None and i == ignore_idx:
                continue
            other = self._dome_clearance_radius(model)
            d = math.hypot(ox - float(model.origin[0]),
                           oy - float(model.origin[1]))
            if d < radius + other + 1.0:
                return False, f"Overlaps dome {i + 1}"
        return True, "OK"

    def _set_dome_radius(self, idx: int, radius: float) -> bool:
        model = self.domes[idx]
        old = model.config.radius
        model.config.radius = float(radius)
        ok, reason = self._dome_fits(model.origin, model.config, ignore_idx=idx)
        if not ok:
            model.config.radius = old
            self._flash(f"Resize blocked: {reason}")
            return False
        self._mark_changed(idx)
        return True

    def _set_trunk_stock_length(self, idx: int, length: float) -> None:
        model = self.domes[idx]
        cfg = model.config
        old_length = cfg.trunk_stock_length
        cfg.trunk_stock_length = float(length)
        if length <= 0 or model.shape.name != "Full Tree Trunk":
            return
        stats = model.stats()
        longest = float(stats.get("trunk_longest", 0.0))
        if longest <= 1e-6:
            return
        target_radius = cfg.radius * (float(length) * 0.995 / longest)
        if not self._set_dome_radius(idx, target_radius):
            cfg.trunk_stock_length = old_length

    def _move_dome_to(self, idx: int, origin) -> bool:
        model = self.domes[idx]
        new_origin = np.array([float(origin[0]), float(origin[1]), 0.0])
        ok, reason = self._dome_fits(new_origin, model.config, ignore_idx=idx)
        if not ok:
            self._flash(f"Move blocked: {reason}")
            return False
        model.origin[:] = new_origin
        self._mark_changed(idx)
        self._refresh_lights()
        self._flash(f"Dome {idx + 1} moved")
        return True

    def _legend_origin(self) -> tuple[float, float]:
        _, height = pygame.display.get_window_size()
        h = self._widget_display_size("legend")[1] or 300
        vx, vy, vw, _ = self._video_window_rect()
        return vx + vw + 10, height - h - 64

    # -- RuneScape-style context menu -------------------------------------

    def _open_context(self, entries: list, pos) -> None:
        """entries: list of (label, callable | None)."""
        if not entries:
            return
        self.context_menu = {
            "origin": (float(pos[0]), float(pos[1])),
            "entries": entries,
            "hover": -1,
        }
        self._render_context_overlay()

    def _render_context_overlay(self) -> None:
        surface, rects = overlay_ui.render_context_menu(
            self.fonts, [e[0] for e in self.context_menu["entries"]],
            self.context_menu["hover"])
        self.context_menu["rects"] = rects
        # Keep the popup inside the window.
        width, height = pygame.display.get_window_size()
        ox, oy = self.context_menu["origin"]
        ox = min(ox, width - surface.get_width() - 4)
        oy = min(oy, height - surface.get_height() - 4)
        self.context_menu["origin"] = (max(0, ox), max(0, oy))
        self._update_overlay("context", surface)

    def _context_row_at(self, pos) -> int:
        if not self.context_menu:
            return -1
        ox, oy = self.context_menu["origin"]
        for i, rect in enumerate(self.context_menu.get("rects", [])):
            if rect.move(int(ox), int(oy)).collidepoint(*pos):
                return i
        return -1

    def _world_context_entries(self) -> list:
        """Options for whatever is under the cursor right now."""
        entries: list = []
        origin, direction = self._interaction_ray()
        point = self._floor_click_point(origin, direction)

        def walk_here():
            if point is not None:
                self.walk_target = point
                self.pending_action = None

        aimed = self._aimed_prop()
        if aimed is not None:
            dome_idx, model, entry = aimed
            prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
            name = entry["type"]
            if prop is not None and prop.watts > 0:
                state = "off" if entry.get("on", True) else "on"
                entries.append((
                    f"Switch {state} {name}",
                    lambda: self._toggle_device(dome_idx, entry)))
            entries.append((
                f"Move {name}",
                lambda: self._begin_move_prop(
                    dome_idx, model.config.props.index(entry))))
            entries.append((
                f"Pick up {name}",
                lambda: self._pickup_prop(
                    dome_idx, model.config.props.index(entry))))
            if prop is not None:
                entries.append((
                    f"Examine {name}",
                    lambda: self._flash(
                        f"{name}: ${prop.cost:,.0f}, {prop.weight:.0f} kg"
                        + (f", {prop.watts:.0f} W" if prop.watts else ""))))

        if self.aiming_screen:
            sd = self.aimed_screen_dome
            entries.append((
                f"Take helm (dome {sd + 1} camera)",
                lambda: (self._select_dome(sd, open_editor=False),
                         self._set_helm(True))))
            tracker = self.trackers[sd]
            entries.append((
                "Examine vision system",
                lambda: self._flash(
                    f"Dome {sd + 1} vision: {tracker.summary()}")))

        if self.aimed_panel is not None:
            pd = self.aimed_panel_dome
            key = self.aimed_panel.key
            pmodel = self.domes[pd]
            pname = self.aimed_panel.panel_type.name

            def swap(step, pd=pd, key=key):
                new = self.domes[pd].cycle_panel(key, step)
                self._mark_changed(pd)
                self._flash(f"Panel -> {new}")

            entries.append(("Swap panel (next)", lambda: swap(1)))
            entries.append(("Swap panel (prev)", lambda: swap(-1)))
            entries.append((
                f"Apply {pname} to all",
                lambda: (pmodel.set_all_panels(pname),
                         self._mark_changed(pd),
                         self._flash(f"All panels set to {pname}"))))
            entries.append((
                "Examine panel",
                lambda: self._flash(
                    f"{pname}, {self.aimed_panel.area:.1f} m2 slot")))

        if point is not None:
            dome_idx = self._dome_at(float(point[0]), float(point[1]))
            entries.append(("Walk here", walk_here))
            if dome_idx is not None:
                model = self.domes[dome_idx]
                if aimed is None and self.aimed_panel is None \
                        and not self.aiming_screen \
                        and self._point_inside_dome(dome_idx, point):
                    menu_pos = pygame.mouse.get_pos()
                    entries.append((
                        "Add item here...",
                        lambda dome_idx=dome_idx, point=point.copy(),
                        menu_pos=menu_pos: self._open_add_item_context(
                            dome_idx, point, menu_pos)))
                if dome_idx != self.active_dome:
                    entries.append((
                        f"Select dome {dome_idx + 1}",
                        lambda: self._select_dome(dome_idx)))
                entries.append((
                    f"Simulate construction (dome {dome_idx + 1})",
                    lambda: self.start_construction(dome_idx)))
                entries.append((
                    f"Examine dome {dome_idx + 1}",
                    lambda: self._flash(
                        f"Dome {dome_idx + 1}: "
                        f"{model.config.frequency}V r="
                        f"{model.config.radius:.0f} m — "
                        f"{self.trackers[dome_idx].summary()}")))
            else:
                import presets
                for pi, (pname_, pdata) in enumerate(presets.PRESETS):
                    entries.append((
                        f"Build here: {pname_}",
                        lambda pdata=pdata, point=point: self._flash(
                            self._add_dome(
                                pdata,
                                origin=(float(point[0]),
                                        float(point[1])),
                                simulate=True))))
        entries.append(("Cancel", None))
        return entries

    def _open_add_item_context(self, dome_idx: int, point, pos) -> None:
        categories = list(dict.fromkeys(prop.category for prop in PROP_TYPES))
        entries = [
            (category.title(),
             lambda category=category: self._open_prop_category_context(
                 dome_idx, point, category, pos))
            for category in categories
        ]
        entries.append(("Cancel", None))
        self._open_context(entries, pos)

    def _open_prop_category_context(
            self, dome_idx: int, point, category: str, pos) -> None:
        entries = [
            (f"Add {prop.name}",
             lambda prop=prop: self._place_prop_at_point(
                 dome_idx, prop, point))
            for prop in PROP_TYPES if prop.category == category
        ]
        entries.append(("Back", lambda: self._open_add_item_context(
            dome_idx, point, pos)))
        self._open_context(entries, pos)

    def _place_prop_at_point(self, dome_idx: int, prop, point) -> None:
        if not self._point_inside_dome(dome_idx, point):
            self._flash("Item must be placed inside the dome")
            return
        model = self.domes[dome_idx]
        local_x = float(point[0]) - float(model.origin[0])
        local_y = float(point[1]) - float(model.origin[1])
        if math.hypot(local_x, local_y) + prop.pick_radius \
                > model.floor_radius * 0.98:
            self._flash("Item is too close to the dome wall")
            return
        for existing in model.config.props:
            other = workshop.PROP_TYPE_BY_NAME.get(existing.get("type"))
            if other is None:
                continue
            gap = math.hypot(
                local_x - float(existing["x"]),
                local_y - float(existing["y"]))
            if gap < (prop.pick_radius + other.pick_radius) * 0.8:
                self._flash(f"Placement blocked by {existing['type']}")
                return
        model.config.props.append({
            "type": prop.name,
            "x": round(local_x, 3),
            "y": round(local_y, 3),
            "yaw": 0.0,
            "on": True,
        })
        self._mark_changed(dome_idx)
        self._refresh_lights()
        self._flash(f"Added {prop.name} inside dome {dome_idx + 1}")

    def _dome_context_entries(self, idx: int, point=None) -> list:
        model = self.domes[idx]

        def walk_to():
            self.walk_target = np.array([
                float(model.origin[0]),
                float(model.origin[1]) - model.floor_radius - 1.5,
                self.ground_height(float(model.origin[0]),
                                   float(model.origin[1])),
            ])

        def begin_move():
            self.moving_dome = idx
            self._flash(f"Moving dome {idx + 1} — click an open location")

        entries = [
            (f"Select dome {idx + 1}", lambda idx=idx: self._select_dome(idx)),
            ("Walk to dome", walk_to),
            ("Move dome", begin_move),
            ("Resize +10%", lambda idx=idx: self._set_dome_radius(
                idx, self.domes[idx].config.radius * 1.10)),
            ("Resize -10%", lambda idx=idx: self._set_dome_radius(
                idx, self.domes[idx].config.radius * 0.90)),
            ("Simulate construction", lambda idx=idx: self.start_construction(idx)),
        ]
        if model.shape.name == "Full Tree Trunk":
            entries.extend([
                ("Trunk stock +1 ft", lambda idx=idx: self._set_trunk_stock_length(
                    idx, self.domes[idx].config.trunk_stock_length + 0.3048)),
                ("Trunk stock -1 ft", lambda idx=idx: self._set_trunk_stock_length(
                    idx, max(0.3048,
                             self.domes[idx].config.trunk_stock_length - 0.3048))),
            ])
        entries.extend([
            ("Examine dome", lambda idx=idx: self._flash(
                f"Dome {idx + 1}: {model.config.frequency}V r="
                f"{model.config.radius:.1f} m — "
                f"{self.trackers[idx].summary()}")),
            ("Delete dome", lambda idx=idx: self._flash(self._remove_dome(idx))),
            ("Cancel", None),
        ])
        return entries

    def _construction_context_entries(self) -> list:
        entries = []
        if self.sim:
            tasks = [
                "Frame assembly", "Panel install", "Electrical rough-in",
                "Interior setup", "Safety inspection",
            ]
            entries.append(("Add worker", lambda: self._set_worker_count(
                self.sim["workers"] + 1)))
            entries.append(("Remove worker", lambda: self._set_worker_count(
                self.sim["workers"] - 1)))
            entries.append((
                f"Assign crew to active dome {self.active_dome + 1}",
                lambda: self.start_construction(self.active_dome)))
            for task in tasks:
                entries.append((
                    f"Task focus: {task}",
                    lambda task=task: (
                        self.sim.update({"task": task}),
                        [w.update({"task": task}) for w in self.worker_states],
                        setattr(self, "worker_dirty", True))))
            entries.append(("Speed x2", lambda: self.sim.update(
                {"speed": min(self.sim["speed"] * 2, 32.0)})))
            entries.append(("Speed /2", lambda: self.sim.update(
                {"speed": max(self.sim["speed"] * 0.5, 0.1)})))

            def cancel():
                self.render_limits.pop(self.sim["dome"], None)
                self.sim = None
                self.worker_states = []
                self.worker_dirty = True
                self._flash("Construction cancelled")

            entries.append(("Cancel construction", cancel))
        entries.append(("Cancel", None))
        return entries

    def _menu_panel_click(self, pos, button: int) -> None:
        lx, ly = self._widget_local_pos("menu", pos)
        for page, rect in self.menu_hit_map.get("tabs", []):
            if rect.collidepoint(lx, ly):
                self.menu_page = page
                self.menu_items = self._build_menu_items()
                self.menu_selected = 1
                self.menu_dirty = True
                self.toolbar_dirty = True
                return
        for index, rect in self.menu_hit_map.get("rows", []):
            if rect.collidepoint(lx, ly):
                item = self.menu_items[index]
                self.menu_selected = index
                if item.activate is not None and button == 1:
                    self._flash(item.activate())
                elif item.change is not None:
                    item.change(1 if button == 1 else -1)
                self.menu_dirty = True
                return

    def _domes_panel_click(self, pos, button: int) -> None:
        lx, ly = self._widget_local_pos("domes", pos)
        for i, rect in enumerate(self.dome_rows_rects):
            if rect.collidepoint(lx, ly):
                if button == 1:
                    self._select_dome(i)
                    self._open_context(self._dome_context_entries(i), pos)
                else:
                    self._open_context(self._dome_context_entries(i), pos)
                return
        if self.dome_add_rect is not None and \
                self.dome_add_rect.collidepoint(lx, ly):
            import presets
            entries = [
                (f"Place: {name}",
                 lambda data=data, name=name: self._begin_dome_placement(
                     name, data))
                for name, data in presets.PRESETS
            ]
            entries.append(("Place: Power Spoke (small)",
                            lambda: self._begin_dome_placement(
                                "Power Spoke", presets.SECOND_DOME)))
            entries.append(("Cancel", None))
            self._open_context(entries, pos)

    def _begin_dome_placement(self, name: str, data: dict) -> None:
        self.placing_dome = {"name": name, "data": data}
        self._flash(f"Placing {name} — click open ground to build "
                    "(Esc cancels)")

    def _place_ghost(self) -> None:
        if not self.ghost_valid or self.placing is None:
            return
        dome_idx = getattr(self, "ghost_dome", 0)
        target = self._all_models()[min(dome_idx,
                                        len(self._all_models()) - 1)]
        entry = dict(self.moving_prop_source["entry"]) \
            if self.moving_prop_source is not None else {}
        entry.update({
            "type": self.placing.name,
            "x": round(float(self.ghost_pos[0])
                       - float(target.origin[0]), 3),
            "y": round(float(self.ghost_pos[1])
                       - float(target.origin[1]), 3),
            "yaw": round(self.ghost_yaw, 1),
            "on": entry.get("on", True),
        })
        target.config.props.append(entry)
        moving_prop = self.moving_prop_source is not None
        if moving_prop:
            source_dome = self.moving_prop_source["dome"]
            self.moving_prop_source = None
            self.placing = None
            self.placing_from_slot = None
            self.inventory_selected = None
            self._mark_changed(source_dome)
            self._flash(f"Moved {entry['type']} to dome {dome_idx + 1}")
        elif self.placing_from_slot is not None:
            inv = self.model.config.inventory
            if self.placing_from_slot < len(inv):
                inv.pop(self.placing_from_slot)
            self.placing = None
            self.placing_from_slot = None
            self.inventory_selected = None
            self.inventory_dirty = True
            self._flash("Placed from backpack")
        else:
            self._flash(f"Placed {self.placing.name} — "
                        "click for another, Esc to finish")
        self._mark_changed(dome_idx)
        self._refresh_lights()
        self.help_dirty = True

    def _aimed_prop(self) -> tuple[int, "DomeModel", dict] | None:
        if self.aimed_prop_index is None:
            return None
        dome_idx, i = self.aimed_prop_index
        models = self._all_models()
        if dome_idx >= len(models):
            return None
        model = models[dome_idx]
        if i >= len(model.config.props):
            return None
        return dome_idx, model, model.config.props[i]

    def _pickup_prop(self, dome_idx: int, index: int) -> None:
        inv = self.model.config.inventory
        if len(inv) >= 28:
            self._flash("Backpack is full")
            return
        models = self._all_models()
        if dome_idx >= len(models):
            return
        model = models[dome_idx]
        if index >= len(model.config.props):
            return
        entry = model.config.props.pop(index)
        inv.append(entry["type"])
        self._mark_changed(dome_idx)
        self.inventory_dirty = True
        self._flash(f"Picked up {entry['type']}")

    def _begin_move_prop(self, dome_idx: int, index: int) -> None:
        models = self._all_models()
        if dome_idx >= len(models) or index >= len(models[dome_idx].config.props):
            return
        model = models[dome_idx]
        entry = model.config.props.pop(index)
        prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
        if prop is None:
            model.config.props.insert(index, entry)
            return
        self.moving_prop_source = {
            "dome": dome_idx,
            "index": index,
            "entry": entry,
        }
        self.placing = prop
        self.placing_from_slot = None
        self.inventory_selected = None
        self.ghost_yaw = float(entry.get("yaw", 0.0))
        self._mark_changed(dome_idx)
        self._refresh_lights()
        self.help_dirty = True
        self._flash(f"Moving {prop.name} - click a dome floor to place")

    def _cancel_prop_placement(self) -> None:
        if self.moving_prop_source is not None:
            source = self.moving_prop_source
            model = self._all_models()[source["dome"]]
            index = min(source["index"], len(model.config.props))
            model.config.props.insert(index, source["entry"])
            self._mark_changed(source["dome"])
            self._refresh_lights()
            message = f"Move cancelled - {source['entry']['type']} restored"
        else:
            message = "Placement finished"
        self.moving_prop_source = None
        self.placing = None
        self.placing_from_slot = None
        self.inventory_selected = None
        self.inventory_dirty = True
        self.help_dirty = True
        self._flash(message)

    def _toggle_device(self, dome_idx: int, entry: dict) -> None:
        entry["on"] = not entry.get("on", True)
        model = self._all_models()[dome_idx]
        state = "ON" if entry["on"] else "OFF"
        connected = self.energy.device_connected(
            model, entry, self.energy.has_system)
        note = "" if connected else "  (no outlet in reach — unpowered)"
        self._flash(f"{entry['type']} switched {state}{note}")
        self._mark_changed(dome_idx)
        self._refresh_lights()

    def _drop_from_slot(self, slot: int) -> None:
        inv = self.model.config.inventory
        if slot >= len(inv):
            return
        # Drop at the avatar's feet, just in front, into whichever
        # dome the player is standing in (else the active one).
        px = float(self.camera.position[0]) + \
            math.sin(self.avatar_yaw) * 0.9
        py = float(self.camera.position[1]) + \
            math.cos(self.avatar_yaw) * 0.9
        dome_idx = self._dome_at(px, py)
        if dome_idx is None:
            dome_idx = self.active_dome
        target = self.domes[dome_idx]
        lx = px - float(target.origin[0])
        ly = py - float(target.origin[1])
        name = inv.pop(slot)
        target.config.props.append({
            "type": name, "x": round(lx, 3), "y": round(ly, 3),
            "yaw": round(math.degrees(self.avatar_yaw) + 180.0, 1) % 360.0,
            "on": True,
        })
        self._mark_changed(dome_idx)
        self.inventory_dirty = True
        self.inventory_selected = None
        self._flash(f"Dropped {name}")

    def _save_design(self) -> str:
        from pathlib import Path
        import materials
        data = {
            "domes": [
                {**model.config.to_dict(),
                 "origin": [float(model.origin[0]),
                            float(model.origin[1])]}
                for model in self.domes
            ],
            "custom_panels": dict(materials.CUSTOM_PANEL_DEFS),
            "active_dome": self.active_dome,
        }
        Path(DESIGN_FILE).write_text(json.dumps(data, indent=2),
                                     encoding="utf-8")
        return f"Saved {DESIGN_FILE} ({len(self.domes)} domes)"

    def _load_design(self) -> str:
        from pathlib import Path
        import materials
        path = Path(DESIGN_FILE)
        if not path.exists():
            return f"{DESIGN_FILE} not found"
        data = json.loads(path.read_text(encoding="utf-8"))

        for name, definition in dict(
                data.get("custom_panels", {})).items():
            materials.register_custom_panel(name, definition)

        while len(self.domes) > 1:
            self._remove_dome(len(self.domes) - 1)

        if "domes" in data:
            dome_list = data["domes"]
            self.domes[0].config = DomeConfig.from_dict(dome_list[0])
            org = dome_list[0].get("origin", [0.0, 0.0])
            self.domes[0].origin[:2] = (float(org[0]), float(org[1]))
            for extra in dome_list[1:]:
                self._add_dome(extra, origin=extra.get("origin"))
        else:
            # Older single/dual-dome save files.
            self.domes[0].config = DomeConfig.from_dict(data)
            if "second_dome" in data:
                org = data.get("second_dome_origin", [14.0, 0.0])
                self._add_dome(data["second_dome"], origin=org)

        self.active_dome = 0
        self.menu_items = self._build_menu_items()
        self._mark_changed(0)
        return f"Loaded {DESIGN_FILE} ({len(self.domes)} domes)"

    def _apply_preset(self, index: int) -> str:
        import presets
        name, data = presets.PRESETS[index % len(presets.PRESETS)]
        self.preset_index = index % len(presets.PRESETS)
        self.model.config = DomeConfig.from_dict(data)
        self.placing = None
        self.placing_from_slot = None
        self.inventory_selected = None
        self.menu_items = self._build_menu_items()
        self._mark_changed()
        self.inventory_dirty = True
        return f"Preset: {name}"

    def _toolbar_click(self, bid: str) -> None:
        suite_pages = {
            "build": "DOME", "rooms": "ROOMS", "props": "PROPS",
            "lab": "LAB", "domes": "SITE", "crew": "CREW",
            "power": "POWER", "materials": "MATERIALS",
        }
        if bid in suite_pages:
            self._open_suite(suite_pages[bid])
        elif bid == "bag":
            self.inventory_open = not self.inventory_open
            self.inventory_dirty = True
        elif bid == "roof":
            self.roof_hidden = not self.roof_hidden
            self._flash("Roof hidden" if self.roof_hidden
                        else "Roof visible")
        elif bid == "pov":
            self._set_control_mode(
                "fp" if self.control_mode == "orbit" else "orbit")
        elif bid == "view360":
            self._toggle_six_point()
        elif bid == "cam":
            if self.helm_active:
                self._set_helm(False)
            else:
                self._set_helm(True, remote=True)
        elif bid == "help":
            self.help_open = not self.help_open
        elif bid == "keys":
            self.legend_open = not self.legend_open
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))
        elif bid == "save":
            self._flash(self._save_design())
        elif bid == "bom":
            from pathlib import Path
            Path(BOM_FILE).write_text(self.model.bom_text(),
                                      encoding="utf-8")
            self._flash(f"Exported {BOM_FILE}")
        self.toolbar_dirty = True

    def _toggle_six_point(self) -> None:
        self.six_point_enabled = not self.six_point_enabled
        if self.six_point_enabled and self.control_mode == "orbit":
            self._set_control_mode("fp")
        self.toolbar_dirty = True

    def _on_mouse_button(self, button: int) -> None:
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        mouse_pos = pygame.mouse.get_pos()

        if button == 1 and (shift or ctrl) and not self.mouse_captured \
                and not self.suite_open:
            widget = self._widget_at(mouse_pos)
            if widget is not None and widget != "context":
                ox, oy = self._widget_origin(widget)
                self.widget_drag = {
                    "name": widget,
                    "mode": "scale" if ctrl else "move",
                    "grab": (mouse_pos[0] - ox, mouse_pos[1] - oy),
                    "start": mouse_pos,
                    "origin": (ox, oy),
                    "scale": self._widget_scale(widget),
                }
                return

        # An open context menu captures the next click.
        if self.context_menu is not None:
            row = self._context_row_at(mouse_pos)
            entries = self.context_menu["entries"]
            self.context_menu = None
            if button == 1 and 0 <= row < len(entries) \
                    and entries[row][1] is not None:
                entries[row][1]()
            self.menu_dirty = True
            return

        # UI first (orbit mode has a live cursor).
        if not self.mouse_captured:
            hit = self._ui_hit(mouse_pos)
            if hit is not None:
                if hit == "suite":
                    self._suite_click(mouse_pos, button)
                elif hit.startswith("toolbar:"):
                    self._toolbar_click(hit.split(":", 1)[1])
                elif hit == "menu":
                    self._menu_panel_click(mouse_pos, button)
                elif hit == "domes":
                    self._domes_panel_click(mouse_pos, button)
                elif hit == "legend":
                    self.legend_open = not self.legend_open
                    self._update_overlay(
                        "legend", overlay_ui.render_legend(
                            self.fonts, not self.legend_open))
                elif hit == "help" and button == 1:
                    self.help_open = False
                    self.toolbar_dirty = True
                elif hit == "minimap":
                    self._minimap_click(mouse_pos, button)
                elif hit == "construction" and button == 3:
                    self._open_context(
                        self._construction_context_entries(), mouse_pos)
                elif hit == "selected_dome":
                    if button == 1:
                        self._open_suite("DOME")
                    else:
                        self._open_context(
                            self._dome_context_entries(self.active_dome),
                            mouse_pos)
                elif hit.startswith("slot:"):
                    slot = int(hit.split(":", 1)[1])
                    if slot < len(self.model.config.inventory):
                        if button == 3:
                            self._drop_from_slot(slot)
                        else:
                            if self.moving_prop_source is not None:
                                self._cancel_prop_placement()
                            name = self.model.config.inventory[slot]
                            self.placing = \
                                workshop.PROP_TYPE_BY_NAME[name]
                            self.placing_from_slot = slot
                            self.inventory_selected = slot
                            self.ghost_yaw = 0.0
                            self.inventory_dirty = True
                            self._flash(f"Placing {name} — click the "
                                        "floor, , . rotate")
                return

        if self.control_mode == "fp" and not self.mouse_captured:
            self._set_mouse_capture(True)
            self.escape_armed = False
            return

        if self.moving_dome is not None:
            if button != 1:
                self._flash("Move dome cancelled")
                self.moving_dome = None
                return
            origin, direction = self._interaction_ray()
            dz = float(direction[2])
            if dz < -1e-5:
                t = -float(origin[2]) / dz
                hit = origin + direction * t
                if self._move_dome_to(
                        self.moving_dome, (float(hit[0]), float(hit[1]))):
                    self.moving_dome = None
            return

        # Placing a whole new dome: click open ground to build it.
        if self.placing_dome is not None:
            if button != 1:
                self.placing_dome = None
                self._flash("Dome placement cancelled")
                return
            origin, direction = self._interaction_ray()
            dz = float(direction[2])
            if dz < -1e-5:
                t = -float(origin[2]) / dz
                hit = origin + direction * t
                data = self.placing_dome["data"]
                cfg = DomeConfig.from_dict(data)
                ok, reason = self._dome_fits((float(hit[0]), float(hit[1])), cfg)
                if not ok:
                    self._flash(f"Cannot place dome: {reason}")
                    return
                self.placing_dome = None
                self._flash(self._add_dome(
                    data, origin=(float(hit[0]), float(hit[1])),
                    simulate=True))
            return

        if self.placing is not None:
            if button == 1:
                self._place_ghost()
            else:
                self._cancel_prop_placement()
            return

        if self.helm_active:
            self._set_helm(False)
            return

        if self.control_mode == "fp":
            # Classic first-person interactions at the crosshair.
            aimed = self._aimed_prop()
            if ctrl and self.aimed_panel is not None and button == 1:
                self._walk_to_panel_exterior(
                    self.aimed_panel_dome, self.aimed_panel)
            elif self.aiming_screen and self.screen_distance < HELM_RANGE:
                self._select_dome(self.aimed_screen_dome,
                                  open_editor=False)
                self._set_helm(True)
            elif aimed is not None and button == 1:
                dome_idx, model, entry = aimed
                prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                if prop is not None and prop.watts > 0:
                    self._toggle_device(dome_idx, entry)
                else:
                    self._begin_move_prop(dome_idx,
                                          self.aimed_prop_index[1])
            elif self.aimed_panel is not None:
                pmodel = self._all_models()[self.aimed_panel_dome]
                step = 1 if button == 1 else -1
                name = pmodel.cycle_panel(self.aimed_panel.key, step)
                self._mark_changed(self.aimed_panel_dome)
                self._flash(f"Panel -> {name}")
            return

        # Orbit mode: RuneScape-style world clicks.
        origin, direction = self._interaction_ray()
        if ctrl and self.aimed_panel is not None:
            self._walk_to_panel_exterior(
                self.aimed_panel_dome, self.aimed_panel)
            return
        if shift and self.aimed_panel is not None:
            pmodel = self._all_models()[self.aimed_panel_dome]
            step = 1 if button == 1 else -1
            name = pmodel.cycle_panel(self.aimed_panel.key, step)
            self._mark_changed(self.aimed_panel_dome)
            self._flash(f"Panel -> {name}")
            return
        if button == 3:
            # Right-click: RuneScape "Choose Option" for the world.
            self._open_context(self._world_context_entries(), mouse_pos)
            return
        if button != 1:
            return

        player = self.camera.position.astype(np.float64)
        if self.aiming_screen:
            self._select_dome(self.aimed_screen_dome,
                              open_editor=False)
            if self.screen_distance_from_player() < HELM_RANGE:
                self._set_helm(True)
            else:
                target = self.console["screen_center"].copy()
                target[1] -= 1.3
                target[2] = self.model.foundation.height
                self.walk_target = target
                self.pending_action = {"kind": "helm"}
                self._flash("Walking to the console...")
            return
        aimed = self._aimed_prop()
        if aimed is not None:
            dome_idx, model, entry = aimed
            wx = float(model.origin[0]) + float(entry["x"])
            wy = float(model.origin[1]) + float(entry["y"])
            dist = math.hypot(wx - player[0], wy - player[1])
            prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
            is_device = prop is not None and prop.watts > 0
            if dist < 2.2:
                if is_device:
                    self._toggle_device(dome_idx, entry)
                else:
                    self._begin_move_prop(dome_idx,
                                          self.aimed_prop_index[1])
            else:
                fh = model.foundation.height
                self.walk_target = np.array([wx, wy, fh])
                kind = "toggle" if is_device else "move"
                self.pending_action = {"kind": kind, "entry": entry,
                                       "dome": dome_idx}
                verb = "switch" if is_device else "move"
                self._flash(f"Walking to {verb} {entry['type']}...")
            return
        if self.aimed_panel is not None:
            dome_idx = self.aimed_panel_dome
            if dome_idx != self.active_dome:
                self._select_dome(dome_idx, open_editor=False)
            pmodel = self._all_models()[dome_idx]
            name = pmodel.cycle_panel(self.aimed_panel.key, 1)
            self._mark_changed(dome_idx)
            self._flash(f"Dome {dome_idx + 1} panel -> {name}")
            return
        point = self._floor_click_point(origin, direction)
        if point is not None:
            self.walk_target = point
            self.pending_action = None

    def _execute_pending(self) -> None:
        action = self.pending_action
        self.pending_action = None
        if not action:
            return
        if action["kind"] == "helm":
            if self.screen_distance_from_player() < HELM_RANGE + 0.4:
                self._set_helm(True)
            return
        dome_idx = action.get("dome", 0)
        models = self._all_models()
        if dome_idx >= len(models):
            return
        model = models[dome_idx]
        entry = action["entry"]
        for i, existing in enumerate(model.config.props):
            if existing is entry:
                if action["kind"] == "pickup":
                    self._pickup_prop(dome_idx, i)
                elif action["kind"] == "move":
                    self._begin_move_prop(dome_idx, i)
                elif action["kind"] == "toggle":
                    self._toggle_device(dome_idx, entry)
                break

    def screen_distance_from_player(self) -> float:
        if not self.console:
            return 1e9
        gap = self.camera.position.astype(np.float64) - \
            self.console["screen_center"]
        return float(np.linalg.norm(gap))

    def _set_helm(self, active: bool, remote: bool = False) -> None:
        if active == self.helm_active:
            return
        self.helm_active = active
        self.helm_remote = remote if active else False
        if active:
            self.menu_open = False
            if remote:
                self._flash("CAMERA CONTROL — arrows steer, "
                            "C or Esc to release")
            else:
                self._flash("HELM TAKEN — arrow keys steer the camera")
        else:
            self._flash("Helm released")
        self.menu_dirty = True
        self.help_dirty = True
        self.toolbar_dirty = True

    def _handle_key(self, key: int) -> None:
        if self.suite_open:
            if key in (pygame.K_ESCAPE, pygame.K_m):
                self._close_suite()
            elif key in (pygame.K_PAGEUP, pygame.K_UP):
                self.suite_scroll = max(0, self.suite_scroll - 3)
                self.suite_dirty = True
            elif key in (pygame.K_PAGEDOWN, pygame.K_DOWN):
                self.suite_scroll = min(
                    self.suite_hit_map.get("scroll_max", 0),
                    self.suite_scroll + 3)
                self.suite_dirty = True
            return

        if key == pygame.K_ESCAPE:
            if self.context_menu is not None:
                self.context_menu = None
            elif self.placing_dome is not None:
                self.placing_dome = None
                self._flash("Dome placement cancelled")
            elif self.moving_dome is not None:
                self.moving_dome = None
                self._flash("Move dome cancelled")
            elif self.placing is not None:
                self._cancel_prop_placement()
            elif self.helm_active:
                self._set_helm(False)
            elif self.mouse_captured:
                self._set_mouse_capture(False)
                self.escape_armed = True
            elif self.escape_armed:
                self.running = False
            else:
                self.escape_armed = True
                self._flash("Press Esc again to quit")
            return

        if key == pygame.K_m:
            self._open_suite("DOME")
            return

        if key in (pygame.K_COMMA, pygame.K_PERIOD) and self.placing:
            self.ghost_yaw += 15.0 if key == pygame.K_PERIOD else -15.0
            self.ghost_yaw %= 360.0
            return

        if key in (pygame.K_DELETE, pygame.K_BACKSPACE) \
                and self.aimed_prop_index is not None:
            self._pickup_prop(self.aimed_prop_index[0],
                              self.aimed_prop_index[1])
            return

        if self.menu_open and not self.helm_active:
            page_keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                         pygame.K_4: 3, pygame.K_5: 4}
            if key in page_keys and page_keys[key] < len(self.menu_pages):
                self.menu_page = page_keys[key]
                self.menu_items = self._build_menu_items()
                self.menu_selected = 1
                self.menu_dirty = True
                self.toolbar_dirty = True
                return

        if key == pygame.K_k:
            self.legend_open = not self.legend_open
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))
        elif key == pygame.K_TAB:
            self._toggle_six_point()
        elif key == pygame.K_f:
            if self.control_mode == "fp":
                self.camera.fly_mode = not self.camera.fly_mode
        elif key == pygame.K_p:
            self._set_control_mode(
                "fp" if self.control_mode == "orbit" else "orbit")
        elif key == pygame.K_r:
            self.roof_hidden = not self.roof_hidden
            self.toolbar_dirty = True
            self._flash("Roof hidden" if self.roof_hidden
                        else "Roof visible")
        elif key in (pygame.K_b, pygame.K_i):
            self.inventory_open = not self.inventory_open
            self.inventory_dirty = True
            self.toolbar_dirty = True
        elif key == pygame.K_c:
            if self.helm_active:
                self._set_helm(False)
            else:
                self._set_helm(True, remote=True)
        elif key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif key == pygame.K_h:
            self.show_hud = not self.show_hud
        elif key == pygame.K_t:
            self._start_note_edit()
        elif key == pygame.K_z:
            self.six_point_spin_speed -= 0.15
        elif key == pygame.K_x:
            self.six_point_spin_speed += 0.15
        elif key == pygame.K_v and self.aimed_panel is not None:
            pmodel = self._all_models()[self.aimed_panel_dome]
            name = self.aimed_panel.panel_type.name
            pmodel.set_all_panels(name)
            self._mark_changed(self.aimed_panel_dome)
            self._flash(f"All panels set to {name}")
        elif key == pygame.K_n:
            self._open_suite("POWER")
        elif key == pygame.K_LEFTBRACKET and self.sim:
            self.sim["speed"] = max(self.sim["speed"] * 0.5, 0.1)
        elif key == pygame.K_RIGHTBRACKET and self.sim:
            self.sim["speed"] = min(self.sim["speed"] * 2.0, 32.0)
        elif key == pygame.K_F5:
            self._flash(self._save_design())
        elif key == pygame.K_F9:
            self._flash(self._load_design())
        elif key == pygame.K_F6:
            from pathlib import Path
            Path(BOM_FILE).write_text(
                self.model.bom_text(), encoding="utf-8")
            self._flash(f"Exported {BOM_FILE}")

    # -- cameras and rays ------------------------------------------------------

    def _orbit_eye_target(self) -> tuple[np.ndarray, np.ndarray]:
        target = self.camera.position.astype(np.float32) + \
            np.array([0.0, 0.0, 0.35], dtype=np.float32)
        cp = math.cos(self.orbit_pitch)
        offset = np.array([
            math.sin(self.orbit_yaw) * cp,
            math.cos(self.orbit_yaw) * cp,
            math.sin(self.orbit_pitch),
        ], dtype=np.float32)
        eye = target + offset * self.orbit_dist
        eye[2] = max(eye[2], 0.5)
        return eye, target

    def _main_view_proj(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """View, projection, and eye of the main (non-six-point) camera."""
        width, height = pygame.display.get_window_size()
        world_width = max(1, width - RIGHT_RAIL_WIDTH)
        aspect = world_width / max(1, height)
        if self.control_mode == "orbit":
            eye, target = self._orbit_eye_target()
            view = look_at_matrix(eye, target,
                                  np.array([0.0, 0.0, 1.0],
                                           dtype=np.float32))
            projection = perspective_matrix(60.0, aspect, NEAR_PLANE,
                                            FAR_PLANE)
            return view, projection, eye
        forward, _, up = self.camera.basis()
        view = look_at_matrix(
            self.camera.position, self.camera.position + forward, up)
        projection = perspective_matrix(78.0, aspect, NEAR_PLANE, FAR_PLANE)
        return view, projection, self.camera.position

    def _mouse_ray(self) -> tuple[np.ndarray, np.ndarray]:
        """World ray under the mouse cursor (orbit mode picking)."""
        width, height = pygame.display.get_window_size()
        mx, my = pygame.mouse.get_pos()
        world_width = max(1, width - RIGHT_RAIL_WIDTH)
        ndc_x = 2.0 * min(mx, world_width) / world_width - 1.0
        ndc_y = 1.0 - 2.0 * my / max(1, height)
        view, projection, eye = self._main_view_proj()
        inv = np.linalg.inv(projection @ view)
        near = inv @ np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float64)
        far = inv @ np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float64)
        near = near[:3] / near[3]
        far = far[:3] / far[3]
        return near, normalize(far - near).astype(np.float64)

    def _interaction_ray(self) -> tuple[np.ndarray, np.ndarray]:
        """The ray used for hover/click picking."""
        if self.control_mode == "orbit" and not self.six_point_enabled \
                and not self.mouse_captured:
            return self._mouse_ray()
        forward, _, _ = self.camera.basis()
        return (self.camera.position.astype(np.float64),
                forward.astype(np.float64))

    def _set_control_mode(self, mode: str) -> None:
        if mode == self.control_mode:
            return
        self.control_mode = mode
        self.walk_target = None
        self.pending_action = None
        if mode == "fp":
            self.camera.yaw = self.orbit_yaw + math.pi
            self.camera.pitch = 0.0
            self._set_mouse_capture(True)
            self._flash("First-person view — mouse look, WASD")
        else:
            self.camera.fly_mode = False
            self.orbit_yaw = self.camera.yaw + math.pi
            self._set_mouse_capture(False)
            self._flash("Overhead view — click the ground to walk")
        self.toolbar_dirty = True
        self.help_dirty = True

    # -- simulation ----------------------------------------------------------

    def _pick_prop(self, origin, direction) \
            -> tuple[float, tuple[int, int] | None]:
        """Ray vs vertical bounding cylinder of every placed prop on
        the site. Returns (distance, (dome_index, prop_index))."""
        best_t, best_hit = 1e9, None
        dx, dy, dz = float(direction[0]), float(direction[1]), \
            float(direction[2])
        a = dx * dx + dy * dy
        for dome_idx, model in enumerate(self._all_models()):
            fh = model.foundation.height
            mox, moy = float(model.origin[0]), float(model.origin[1])
            for i, entry in enumerate(model.config.props):
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None:
                    continue
                cx = mox + float(entry["x"])
                cy = moy + float(entry["y"])
                r = prop.pick_radius
                z0, z1 = fh, fh + prop.pick_height
                ox = float(origin[0]) - cx
                oy = float(origin[1]) - cy

                if a > 1e-9:
                    bq = ox * dx + oy * dy
                    c = ox * ox + oy * oy - r * r
                    disc = bq * bq - a * c
                    if disc >= 0.0:
                        sq = math.sqrt(disc)
                        for t in ((-bq - sq) / a, (-bq + sq) / a):
                            if 0.1 < t < best_t:
                                z = float(origin[2]) + dz * t
                                if z0 <= z <= z1:
                                    best_t = t
                                    best_hit = (dome_idx, i)
                                    break
                if abs(dz) > 1e-6:
                    t = (z1 - float(origin[2])) / dz
                    if 0.1 < t < best_t:
                        px = ox + dx * t
                        py = oy + dy * t
                        if px * px + py * py <= r * r:
                            best_t = t
                            best_hit = (dome_idx, i)
        return best_t, best_hit

    def ground_height(self, x: float, y: float) -> float:
        height = 0.0
        for model in self._all_models():
            foundation = model.foundation
            if foundation.name == "Bare Ground":
                continue
            f_radius = model.config.radius * model.config.foundation_scale
            dx = x - float(model.origin[0])
            dy = y - float(model.origin[1])
            if dx * dx + dy * dy <= f_radius * f_radius:
                height = max(height, foundation.height)
        return height

    def update(self, delta_time: float) -> None:
        if self.mouse_captured and self.control_mode == "fp" \
                and not self.smoke_frames:
            dx, dy = pygame.mouse.get_rel()
            self.camera.yaw += dx * self.camera.mouse_sensitivity
            self.camera.pitch -= dy * self.camera.mouse_sensitivity
            self.camera.pitch = float(np.clip(
                self.camera.pitch, -math.radians(89.0), math.radians(89.0)))

        keys = pygame.key.get_pressed()

        if self.control_mode == "orbit":
            # RuneScape-style camera: arrow keys orbit around the player.
            if not self.helm_active:
                if keys[pygame.K_LEFT]:
                    self.orbit_yaw += 1.8 * delta_time
                if keys[pygame.K_RIGHT]:
                    self.orbit_yaw -= 1.8 * delta_time
                if keys[pygame.K_UP]:
                    self.orbit_pitch += 1.1 * delta_time
                if keys[pygame.K_DOWN]:
                    self.orbit_pitch -= 1.1 * delta_time
                self.orbit_pitch = float(np.clip(
                    self.orbit_pitch, 0.12, 1.45))
            forward = normalize(np.array(
                [-math.sin(self.orbit_yaw), -math.cos(self.orbit_yaw),
                 0.0], dtype=np.float32))
            up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            right = normalize(np.cross(forward, up))
        else:
            forward, right, up = self.camera.basis()
            if not self.camera.fly_mode:
                forward = normalize(np.array(
                    [forward[0], forward[1], 0.0], dtype=np.float32))
                right = normalize(np.array(
                    [right[0], right[1], 0.0], dtype=np.float32))
                up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # WASD moves only in first-person; orbit mode is click-to-walk.
        movement = np.zeros(3, dtype=np.float32)
        if self.control_mode == "fp":
            if keys[pygame.K_w]:
                movement += forward
            if keys[pygame.K_s]:
                movement -= forward
            if keys[pygame.K_d]:
                movement += right
            if keys[pygame.K_a]:
                movement -= right
        if self.control_mode == "fp" and self.camera.fly_mode:
            if keys[pygame.K_SPACE]:
                movement += up
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                movement -= up

        if self.control_mode == "fp":
            if keys[pygame.K_q]:
                self.camera.roll -= delta_time * 0.8
            if keys[pygame.K_e]:
                self.camera.roll += delta_time * 0.8

        length = float(np.linalg.norm(movement))
        if length > 1e-6:
            movement /= length
            speed = self.camera.movement_speed
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                speed *= self.camera.sprint_multiplier
            self.camera.position += movement * speed * delta_time
            self.walk_target = None
            self.pending_action = None
            self.avatar_yaw = math.atan2(
                float(movement[0]), float(movement[1]))

        # Click-to-move walking.
        if self.walk_target is not None:
            dx = float(self.walk_target[0] - self.camera.position[0])
            dy = float(self.walk_target[1] - self.camera.position[1])
            dist = math.hypot(dx, dy)
            if dist < 0.15:
                self.walk_target = None
                self._execute_pending()
            else:
                step = min(self.camera.movement_speed * delta_time, dist)
                self.camera.position[0] += dx / dist * step
                self.camera.position[1] += dy / dist * step
                self.avatar_yaw = math.atan2(dx, dy)

        if not (self.control_mode == "fp" and self.camera.fly_mode):
            self.camera.position[2] = PLAYER_HEIGHT + self.ground_height(
                float(self.camera.position[0]),
                float(self.camera.position[1]))

        self.camera.roll += self.six_point_spin_speed * delta_time

        # PTZ helm steering (held keys, like a real joystick controller).
        if self.helm_active:
            if keys[pygame.K_LEFT]:
                self.ptz.pan += self.ptz.pan_rate * delta_time
            if keys[pygame.K_RIGHT]:
                self.ptz.pan -= self.ptz.pan_rate * delta_time
            if keys[pygame.K_UP]:
                self.ptz.tilt += self.ptz.tilt_rate * delta_time
            if keys[pygame.K_DOWN]:
                self.ptz.tilt -= self.ptz.tilt_rate * delta_time
            if keys[pygame.K_PAGEUP]:
                self.ptz.fov -= self.ptz.zoom_rate * delta_time
            if keys[pygame.K_PAGEDOWN]:
                self.ptz.fov += self.ptz.zoom_rate * delta_time
            self.ptz.pan %= 360.0
            self.ptz.tilt = float(np.clip(self.ptz.tilt, 0.0, 100.0))
            self.ptz.fov = float(np.clip(self.ptz.fov, 12.0, 80.0))

            # Walking away releases the helm — unless controlling
            # remotely via the C hotkey.
            if not self.helm_remote:
                gap = self.camera.position.astype(np.float64) - \
                    self.console["screen_center"]
                if float(np.linalg.norm(gap)) > HELM_LEASH:
                    self._set_helm(False)

        while self.rebuild_queue:
            self._rebuild_dome(next(iter(self.rebuild_queue)))

        # Construction crew and the shared power system.
        self._update_construction(delta_time)
        was_empty = self.energy.battery_empty
        self.energy.update(self._all_models(), delta_time)
        if self.energy.battery_empty != was_empty:
            self._refresh_lights()
            self._flash("BATTERY EMPTY — loads shed"
                        if self.energy.battery_empty
                        else "Battery recovering — loads restored")

        # Every dome's vision system samples what its camera can see.
        for i, model in enumerate(self.domes):
            model.site_index = i
            self.trackers[i].update(
                model, self.ptzs[i], self.consoles[i],
                self.camera.position, delta_time, self.worker_states)

        # Hover/crosshair picking: console screen, then props, then panels.
        origin, direction = self._interaction_ray()

        screen_t = None
        for ci, console in enumerate(self.consoles):
            if not console:
                continue
            bl, br, tr, tl = console["screen_corners"]
            for tri in ((bl, br, tr), (bl, tr, tl)):
                hit = ray_triangle(origin, direction, *tri)
                if hit is not None and (screen_t is None
                                        or hit < screen_t):
                    screen_t = hit
                    self.aimed_screen_dome = ci

        prop_t, prop_index = self._pick_prop(origin, direction)
        panel, distance = None, 1e9
        self.aimed_panel_dome = 0
        for di, dmodel in enumerate(self.domes):
            if self._inside_dome(di):
                continue
            p, d = dmodel.pick_panel(origin, direction)
            if p is not None and d < distance:
                panel, distance = p, d
                self.aimed_panel_dome = di

        candidates = []
        if screen_t is not None:
            candidates.append((screen_t, "screen"))
        if prop_index is not None:
            candidates.append((prop_t, "prop"))
        if panel is not None:
            candidates.append((distance, "panel"))
        winner = min(candidates)[1] if candidates else None

        aiming_screen = winner == "screen"
        aimed_prop = prop_index if winner == "prop" else None
        if winner != "panel":
            panel = None

        previous = (
            self.aimed_panel.key if self.aimed_panel else None,
            self.aimed_panel.panel_type.name if self.aimed_panel else None,
            self.aiming_screen,
            self.aimed_prop_index,
        )
        self.aimed_panel = panel
        self.aimed_distance = distance if panel else 0.0
        self.aiming_screen = aiming_screen
        self.screen_distance = screen_t if screen_t is not None else 1e9
        self.aimed_prop_index = aimed_prop
        current = (
            panel.key if panel else None,
            panel.panel_type.name if panel else None,
            aiming_screen,
            aimed_prop,
        )
        if current != previous:
            self.help_dirty = True

        hover = self._demo_hover_info()
        hover_state = None if hover is None else (
            hover["key"], hover["title"], hover["body"])
        if hover_state != self.hover_state:
            self.hover_info = hover
            self.hover_state = hover_state
            self.tooltip_dirty = True

        # Placement ghost follows the crosshair's floor intersection,
        # snapping to whichever dome's floor the ray lands on.
        if self.placing is not None:
            dz = float(direction[2])
            self.ghost_valid = False
            self.ghost_dome = 0
            if dz < -1e-4:
                fallback = None
                for dome_idx, model in enumerate(self._all_models()):
                    fh = model.foundation.height
                    t = (fh - float(origin[2])) / dz
                    if not (0.1 < t < 80.0):
                        continue
                    hit = origin + direction * t
                    if fallback is None:
                        fallback = (hit, fh)
                    lx = hit[0] - float(model.origin[0])
                    ly = hit[1] - float(model.origin[1])
                    limit = model.floor_radius - \
                        max(0.3, self.placing.pick_radius * 0.8)
                    if math.hypot(lx, ly) <= limit:
                        self.ghost_pos = hit.copy()
                        self.ghost_pos[2] = fh
                        self.ghost_valid = True
                        self.ghost_dome = dome_idx
                        break
                if not self.ghost_valid and fallback is not None:
                    self.ghost_pos = fallback[0].copy()
                    self.ghost_pos[2] = fallback[1]

    # -- rendering -----------------------------------------------------------

    def _set_uniform(self, program, name, value) -> None:
        try:
            program[name].value = value
        except KeyError:
            pass

    def _render_scene(self, framebuffer, view, projection,
                      camera_pos=None, draw_monitor=True,
                      roof_cut=None, draw_avatar=False,
                      exposure=1.0, headlamp=0.0) -> None:
        if camera_pos is None:
            camera_pos = self.camera.position
        if roof_cut is None:
            roof_cut = 1e9
        framebuffer.use()
        self.ctx.viewport = (0, 0, *framebuffer.size)
        framebuffer.clear(*self.sky_color, 1.0, depth=1.0)

        mvp = projection @ view
        identity = np.eye(4, dtype=np.float32)
        self.scene_program["u_mvp"].write(
            np.ascontiguousarray(mvp.T).tobytes())
        self.scene_program["u_model"].write(identity.tobytes())
        self._set_uniform(self.scene_program, "u_camera_position",
                          tuple(map(float, camera_pos)))
        self._set_uniform(self.scene_program, "u_light_direction",
                          (-0.40, -0.25, -0.90))
        self._set_uniform(self.scene_program, "u_sky_color", self.sky_color)
        self._set_uniform(self.scene_program, "u_ghost", 0.0)
        self._set_uniform(self.scene_program, "u_cut_z", float(roof_cut))
        self._set_uniform(self.scene_program, "u_exposure", float(exposure))
        self._set_uniform(self.scene_program, "u_headlamp", float(headlamp))
        self._set_uniform(self.scene_program, "u_light_count",
                          self.light_count)
        try:
            self.scene_program["u_light_positions"].write(
                self.light_array.tobytes())
        except KeyError:
            pass

        # Opaque pass (construction sims render a prefix of the mesh).
        def draw_pass(kind: str) -> None:
            vao = self.env_buffers.get(f"{kind}_vao")
            if vao is not None:
                vao.render(moderngl.TRIANGLES)
            for dome_idx, buffers in enumerate(self.dome_buffers_list):
                if not buffers:
                    continue
                vao = buffers.get(f"{kind}_vao")
                if vao is None:
                    continue
                limit = self.render_limits.get(dome_idx)
                if limit is None:
                    vao.render(moderngl.TRIANGLES)
                else:
                    count = limit[0] if kind == "opaque" else limit[1]
                    if count > 0:
                        vao.render(moderngl.TRIANGLES, vertices=count)

        draw_pass("opaque")

        # Construction crew on site.
        if self.sim is not None:
            vao = self.worker_buffers.get("opaque_vao")
            for worker in self.worker_states:
                a = -worker["yaw"]
                c, s = math.cos(a), math.sin(a)
                worker_matrix = np.array([
                    [c, -s, 0.0, float(worker["pos"][0])],
                    [s, c, 0.0, float(worker["pos"][1])],
                    [0.0, 0.0, 1.0, float(worker["pos"][2])],
                    [0.0, 0.0, 0.0, 1.0],
                ], dtype=np.float32)
                self.scene_program["u_model"].write(
                    np.ascontiguousarray(worker_matrix.T).tobytes())
                if vao is not None:
                    vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())

        # Third-person avatar (in overhead mode and on the PTZ feed).
        if draw_avatar:
            ax, ay = float(self.camera.position[0]), \
                float(self.camera.position[1])
            az = float(self.camera.position[2]) - PLAYER_HEIGHT
            a = -self.avatar_yaw
            c, s = math.cos(a), math.sin(a)
            avatar_matrix = np.array([
                [c, -s, 0.0, ax],
                [s, c, 0.0, ay],
                [0.0, 0.0, 1.0, az],
                [0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)
            self.scene_program["u_model"].write(
                np.ascontiguousarray(avatar_matrix.T).tobytes())
            vao = self.avatar_buffers.get("opaque_vao")
            if vao is not None:
                vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())

        # In-world monitors, each showing its own dome's live feed.
        # A dome's monitor is skipped inside that dome's PTZ pass (a
        # texture cannot be sampled while it is the render target).
        if draw_monitor is not False:
            skip_idx = draw_monitor if isinstance(draw_monitor, int) \
                and not isinstance(draw_monitor, bool) else -1
            self.screen_program["u_mvp"].write(
                np.ascontiguousarray(mvp.T).tobytes())
            for mi, monitor in enumerate(self.monitors):
                if mi == skip_idx or not self.consoles[mi]:
                    continue
                self.feeds[mi]["texture"].use(location=0)
                self.screen_program["u_texture"].value = 0
                monitor["vao"].render(moderngl.TRIANGLES)

        # Transparent pass (glass, sheeting, films).
        self.ctx.enable(moderngl.BLEND)
        framebuffer.depth_mask = False
        draw_pass("transparent")

        # Placement ghost preview (green = valid spot, red = invalid).
        if self.placing is not None:
            ghost = self._ghost_buffers(self.placing.name)
            a = -math.radians(self.ghost_yaw)
            c, s = math.cos(a), math.sin(a)
            model_matrix = np.array([
                [c, -s, 0.0, float(self.ghost_pos[0])],
                [s, c, 0.0, float(self.ghost_pos[1])],
                [0.0, 0.0, 1.0, float(self.ghost_pos[2])],
                [0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)
            self.scene_program["u_model"].write(
                np.ascontiguousarray(model_matrix.T).tobytes())
            self._set_uniform(self.scene_program, "u_ghost",
                              1.0 if self.ghost_valid else 2.0)
            for key in ("opaque_vao", "transparent_vao"):
                vao = ghost.get(key)
                if vao is not None:
                    vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())
            self._set_uniform(self.scene_program, "u_ghost", 0.0)

        # Click-to-move destination marker (spinning yellow beacon).
        if self.walk_target is not None and draw_avatar:
            tx, ty, tz = map(float, self.walk_target)
            spin = time.perf_counter() * 2.5
            r = 0.28
            verts = []
            for k in (0, 1):
                a0 = spin + k * math.pi * 0.5
                dx, dy = math.cos(a0) * r, math.sin(a0) * r
                verts.extend([
                    tx - dx, ty - dy, tz + 0.02,
                    tx + dx, ty + dy, tz + 0.02,
                    tx, ty, tz + 0.85,
                ])
            self.marker_vbo.write(
                np.asarray(verts, dtype=np.float32).tobytes())
            self.highlight_program["u_mvp"].write(
                np.ascontiguousarray((projection @ view).T).tobytes())
            pulse = 0.5 + 0.25 * math.sin(time.perf_counter() * 6.0)
            self.highlight_program["u_color"].value = (
                1.0, 0.85, 0.15, pulse)
            self.marker_vao.render(moderngl.TRIANGLES)

        # Selected dome ground ring.
        if self.domes:
            model = self.domes[self.active_dome]
            z = model.foundation.height + 0.035
            r = model.floor_radius
            verts = []
            for i in range(96):
                a = math.tau * i / 96
                verts.append((
                    float(model.origin[0]) + math.cos(a) * r,
                    float(model.origin[1]) + math.sin(a) * r,
                    z,
                ))
            data = np.asarray(verts, dtype=np.float32)
            self.selected_ring_vbo.write(data.tobytes())
            self.highlight_program["u_mvp"].write(mvp.tobytes())
            self.highlight_program["u_color"].value = (
                0.25, 0.85, 1.0, 0.92)
            self.selected_ring_vao.render(moderngl.LINE_LOOP, vertices=96)

        # Aimed-panel highlight.
        if self.aimed_panel is not None:
            tri = self.aimed_panel.world_verts.astype(np.float32)
            outward = normalize(
                (self.aimed_panel.centroid
                 - self.model.sphere_center).astype(np.float32))
            to_camera = normalize(
                np.asarray(camera_pos, dtype=np.float32)
                - tri.mean(axis=0).astype(np.float32))
            tri = tri + to_camera * 0.02 + outward * 0.01
            self.highlight_vbo.write(tri.astype(np.float32).tobytes())
            self.highlight_program["u_mvp"].write(
                np.ascontiguousarray(mvp.T).tobytes())
            pulse = 0.22 + 0.12 * math.sin(time.perf_counter() * 5.0)
            self.highlight_program["u_color"].value = (
                1.0, 0.72, 0.20, pulse)
            self.highlight_vao.render(moderngl.TRIANGLES)

        framebuffer.depth_mask = True
        self.ctx.disable(moderngl.BLEND)

    def _ghost_buffers(self, name: str) -> dict:
        if name not in self.ghost_cache:
            self.ghost_cache[name] = self._upload_mesh(build_prop_mesh(name))
        return self.ghost_cache[name]

    def _ptz_watch_info(self) -> tuple[str, str]:
        """Which section the camera center is watching, plus the room's
        expected-activity hint for the vision system."""
        if not self.console:
            return "", ""
        eye = self.console["ptz_eye"]
        forward, _ = self.ptz.basis()
        dz = float(forward[2])
        if dz > -0.06:
            return "HORIZON", "camera aimed above the floor"
        fh = self.model.foundation.height
        t = (fh - float(eye[2])) / dz
        point = eye + forward.astype(np.float64) * t
        section = self.model.section_at(float(point[0]), float(point[1]))
        if section < 0:
            return "PERIMETER", "outside the dome floor"
        room_name = self.model.config.sections[section]
        room = ROOM_TYPE_BY_NAME.get(room_name)
        label = f"S{section + 1} {room_name.upper()}"
        hint = room.hint if room else ""
        return label, hint

    def _render_feed(self, idx: int) -> None:
        console = self.consoles[idx]
        if not console:
            return
        eye = console["ptz_eye"].astype(np.float32)
        forward, up = self.ptzs[idx].basis()
        view = look_at_matrix(eye, eye + forward, up)
        projection = perspective_matrix(
            self.ptzs[idx].fov,
            PTZ_TEXTURE_SIZE[0] / PTZ_TEXTURE_SIZE[1],
            NEAR_PLANE, FAR_PLANE)
        self._render_scene(self.feeds[idx]["fbo"], view, projection,
                           camera_pos=eye, draw_monitor=idx,
                           draw_avatar=True, exposure=1.25,
                           headlamp=0.9)

    def render_ptz_feed(self) -> None:
        """Active dome's camera renders every frame; the other domes'
        cameras refresh round-robin, one per frame."""
        self._render_feed(self.active_dome)
        others = [i for i in range(len(self.domes))
                  if i != self.active_dome]
        if others:
            self._feed_cycle = (self._feed_cycle + 1) % len(others)
            self._render_feed(others[self._feed_cycle])

    def _six_face_views(self) -> Iterable[tuple[str, np.ndarray]]:
        position = self.camera.position
        forward, right, up = self.camera.basis()
        definitions = (
            ("front", forward, up),
            ("back", -forward, up),
            ("right", right, up),
            ("left", -right, up),
            ("up", up, -forward),
            ("down", -up, forward),
        )
        for name, direction, face_up in definitions:
            yield name, look_at_matrix(
                position, position + direction, face_up)

    def _roof_cut_value(self) -> float:
        def lower_ring_cut(model) -> float:
            fh = model.foundation.height
            zs = sorted({
                round(float(v[2]), 4)
                for v in getattr(model, "world_verts", [])
                if float(v[2]) > fh + 0.05
            })
            if zs:
                return zs[0] + max(0.08, model.strut_depth * 0.75)
            return fh + 2.0

        if self.roof_hidden:
            return lower_ring_cut(self.model)
        # RuneScape-style auto-roof: when the player is inside a dome in
        # orbit view, the structure above them turns see-through so the
        # camera is never blocked.
        if self.control_mode == "orbit":
            px, py = float(self.camera.position[0]), \
                float(self.camera.position[1])
            for model in self.domes:
                dx = px - float(model.origin[0])
                dy = py - float(model.origin[1])
                if math.hypot(dx, dy) <= model.floor_radius + 0.4:
                    return lower_ring_cut(model)
        return 1e9

    def render_six_point(self) -> None:
        projection = perspective_matrix(90.0, 1.0, NEAR_PLANE, FAR_PLANE)
        for name, view in self._six_face_views():
            self._render_scene(self.face_fbos[name], view, projection,
                               roof_cut=self._roof_cut_value())

        self.ctx.screen.use()
        width, height = pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.012, 0.016, 0.022, 1.0)

        for unit, (name, uniform_name) in enumerate((
            ("front", "u_front"), ("back", "u_back"),
            ("right", "u_right"), ("left", "u_left"),
            ("up", "u_up"), ("down", "u_down"),
        )):
            self.face_textures[name].use(location=unit)
            self.panorama_program[uniform_name].value = unit

        self.panorama_program["u_resolution"].value = (
            float(width), float(height))
        self.panorama_program["u_roll"].value = float(self.camera.roll)
        self.panorama_program["u_show_grid"].value = self.show_grid
        self.panorama_program["u_outside_color"].value = (
            0.012, 0.016, 0.022)
        self.panorama_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

    def render_normal(self) -> None:
        width, height = pygame.display.get_window_size()
        view, projection, eye = self._main_view_proj()
        self._render_scene(
            self.normal_fbo, view, projection, camera_pos=eye,
            roof_cut=self._roof_cut_value(),
            draw_avatar=self.control_mode == "orbit")

        self.ctx.screen.use()
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.clear(0.006, 0.008, 0.010, 1.0)
        self.ctx.viewport = (0, 0, max(1, width - RIGHT_RAIL_WIDTH), height)
        self.normal_texture.use(location=0)
        self.normal_program["u_texture"].value = 0
        self.normal_vao.render(moderngl.TRIANGLES)
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.enable(moderngl.DEPTH_TEST)

    def update_caption(self, fps: float) -> None:
        mode = "360 SIX-POINT" if self.six_point_enabled else "NORMAL"
        movement = "FLY" if self.camera.fly_mode else "WALK"
        pygame.display.set_caption(
            f"Geodesic Dome Creator | {mode} | {movement} | "
            f"{fps:5.1f} FPS | M suite, H help")

    # -- smoke test ----------------------------------------------------------

    def _save_screenshot(self, path: str) -> None:
        width, height = pygame.display.get_window_size()
        data = self.ctx.screen.read(components=3)
        surface = pygame.image.frombytes(data, (width, height), "RGB", True)
        pygame.image.save(surface, path)

    def _smoke_step(self) -> None:
        cfg = self.model.config
        f = self.frame_count
        if f == 20:
            cfg.frequency = 2
            self._mark_changed()
        elif f == 30:
            # Quarter-wedge split logs on a hubless doubled frame.
            cfg.strut_shape = 4
            cfg.frame_style = "Hubless Doubled"
            self._mark_changed()
        elif f == 36:
            cfg.wedge_flip = True
            self._mark_changed()
        elif f == 40:
            cfg.frequency = 4
            cfg.strut_shape = 0
            cfg.frame_style = "Hub & Strut"
            cfg.hub_style = "Metal Brackets"
            cfg.wedge_flip = False
            self._mark_changed()
        elif f == 60:
            cfg.foundation = "Wood Deck"
            cfg.layers[0] = "Asphalt Shingles"
            cfg.layers[1] = "Plastic Film"
            self._mark_changed()
        elif f == 64:
            cfg.sections[0] = "Lounge"
            cfg.sections[1] = "Office"
            cfg.sections[2] = "Bathroom"
            cfg.sections[4] = "Wood Shop"
            cfg.sections[5] = "Assembly"
            cfg.sections[9] = "Storage"
            cfg.partitions = "Low Walls"
            cfg.props.extend([
                {"type": "Worktable", "x": 1.9, "y": -1.4, "yaw": 200.0},
                {"type": "Pegboard Bench", "x": 3.0, "y": 0.6, "yaw": 105.0},
                {"type": "Office Desk", "x": 1.2, "y": 3.2, "yaw": 25.0},
                {"type": "Office Chair", "x": 1.0, "y": 2.5, "yaw": 205.0},
                {"type": "Toilet", "x": -1.4, "y": 3.4, "yaw": 180.0},
                {"type": "Bathroom Sink", "x": -2.3, "y": 2.9, "yaw": 220.0},
                {"type": "Shelving Unit", "x": -3.1, "y": -1.2, "yaw": 70.0},
                {"type": "Tripod Light", "x": 0.9, "y": -0.9, "yaw": 0.0},
                {"type": "Shop Light", "x": -1.2, "y": -0.6, "yaw": 0.0},
            ])
            self._mark_changed()
        elif f == 68:
            self.placing = PROP_TYPES[0]
            self.ghost_yaw = 45.0
        elif f == 76:
            self.placing = None
        elif f == 80:
            cfg.default_panel = "Glass Window"
            self._mark_changed()
        elif f == 100:
            if self.model.panels:
                self.model.cycle_panel(self.model.panels[0].key, 1)
            self._mark_changed()
        elif f == 108:
            self._flash(self._apply_preset(1))     # Glass Studio Loft
        elif f == 114:
            self._flash(self._apply_preset(2))     # Split-Log Homestead
            self._set_helm(True, remote=True)      # hotkey camera control
            self.ptz.tilt = 40.0
        elif f == 118:
            self._set_helm(False)
            self._flash(self._electrify_dome())
            self.energy_open = True
        elif f == 120:
            self.six_point_enabled = True
        elif f == 150:
            self.six_point_enabled = False
            self.control_mode = "orbit"
            self.roof_hidden = True
            self.orbit_pitch = 1.2
            self.orbit_dist = 14.0
            self.camera.position[:2] = (0.0, 0.5)
        elif f == 162:
            if self.model.config.props:
                self._pickup_prop(0, 0)
        elif f == 166:
            if self.model.config.inventory:
                self._drop_from_slot(0)
        elif f == 168:
            self.roof_hidden = False
        elif f == 160:
            from pathlib import Path
            self._save_design()
            Path(BOM_FILE).write_text(
                self.model.bom_text(), encoding="utf-8")
        elif f == 170:
            self._load_design()
        elif f == 174:
            # Walk up to the console so the helm leash keeps hold.
            target = self.console["screen_center"]
            self.camera.position[:] = (
                float(target[0]), float(target[1]) - 1.6,
                PLAYER_HEIGHT + self.ground_height(
                    float(target[0]), float(target[1]) - 1.6))
            self.camera.yaw = 0.0
            self.camera.pitch = -0.1
            self.orbit_yaw = math.pi
            self.orbit_pitch = 0.35
            self.orbit_dist = 4.5
        elif f == 175:
            self._set_helm(True)
        elif 175 < f < 195:
            self.ptz.pan += 4.0
            self.ptz.tilt = min(100.0, self.ptz.tilt + 1.5)
            self.ptz.fov = max(12.0, self.ptz.fov - 1.0)
        elif f == 195:
            self._set_helm(False)
        elif f == 200:
            import presets
            self._flash(self._add_dome(presets.SECOND_DOME,
                                       simulate=True))
            if self.sim:
                self.sim["speed"] = self.sim["total"] / 0.8
                self.sim["workers"] = 3
            self.domes_open = True
            self.legend_open = True
        elif f == 220:
            # Exercise the RuneScape context menu + Panel Lab.
            self._open_context(self._world_context_entries(),
                               (500, 400))
            self.lab_qty = {"V-Bracket": 3, "Foam Seal (m)": 4}
            self.menu_page = 3
            self.menu_items = self._build_menu_items()
            self.menu_open = True
            self.menu_dirty = True
        elif f == 230:
            self.context_menu = None
            for item in self.menu_items:
                if item.label == "Create custom panel":
                    self._flash(item.activate())
                    break
        elif f == 335:
            if len(self.domes) > 1:
                for entry in self.domes[1].config.props:
                    prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                    if prop is not None and prop.light_z is not None:
                        entry["on"] = True
                self._mark_changed(1)
                self._refresh_lights()
            self.camera.position[:2] = (
                self.model.config.radius + 8.0, -14.0)
            self.orbit_pitch = 0.9
            self.orbit_dist = 18.0
            self.orbit_yaw = math.pi

        if os.environ.get("DOME_DEBUG") and f in (176, 189):
            print(f"frame {f}: cam={self.camera.position.round(2)} "
                  f"yaw={self.camera.yaw:.2f} pitch={self.camera.pitch:.2f} "
                  f"console={self.console['screen_center'].round(2)} "
                  f"helm={self.helm_active} "
                  f"aim_screen={self.aiming_screen}", flush=True)

        shot_dir = os.environ.get("DOME_SHOT_DIR")
        if shot_dir and f in (15, 34, 55, 72, 95, 112, 117, 130, 156,
                              178, 190, 226, 240, 330, 350):
            self._save_screenshot(
                os.path.join(shot_dir, f"smoke_{f:03d}.png"))

    # -- main loop -------------------------------------------------------------

    def run(self) -> None:
        last_time = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            delta_time = min(now - last_time, 0.05)
            last_time = now

            self.process_events()
            self.update(delta_time)
            self._refresh_overlays()

            self.render_ptz_feed()
            if self.six_point_enabled:
                self.render_six_point()
            else:
                self.render_normal()

            self.ctx.screen.use()
            self._render_overlays()

            pygame.display.flip()
            self.clock.tick(144)
            self.update_caption(self.clock.get_fps())

            self.frame_count += 1
            if self.smoke_frames:
                self._smoke_step()
                if self.frame_count >= self.smoke_frames:
                    print("SMOKE OK", flush=True)
                    self.running = False

        self.shutdown()

    def shutdown(self) -> None:
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()


def main() -> None:
    try:
        app = DomeCreatorApp()
        app.run()
    except ImportError as error:
        print(
            "\nMissing dependency. Install the required packages with:\n"
            "    py -3.12 -m pip install pygame moderngl numpy\n",
            file=sys.stderr,
        )
        raise error
    except Exception as error:
        print(
            "\nApplication failed to start or render.\n"
            "Confirm that your graphics driver supports OpenGL 3.3.\n"
            f"Error: {error}\n",
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    main()
