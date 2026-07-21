"""
Dome Home Assembly Line — investor-demo manufacturing simulation.

A manufactured-housing production line for dome homes. A transfer
carriage rolls a dome down the line past 15 numbered gantry stations,
each adding one build step in real trailer-plant order, until every
component of the finished home is present. A gantry crane then lifts
the finished home by its apex anchor onto a big mechanical lazy susan
that rotates to keep the solar band tracking the sun.

This build is designed to *persuade*: the geometry, cost, and labor
model are all driven from ``al_build.py`` (which holds every editable
assumption), so the running demo shows real unit economics, throughput,
break-even, a benchmark against conventional housing, and the finished
product's value story — not just an animation.

What makes it a decision tool, not a cartoon:
  * Every element carries a real material cost and install-labor time.
  * A per-station crew physically walks the dome deck at a real human
    stride to place each element; steps, distance, labor-hours, and
    dollars accrue live as ground-truth numbers.
  * Each production run randomizes the dome (size / frequency / layout /
    cladding); finished homes are serialized, saved to SQLite, and
    stacked in a growing yard that persists across sessions.
  * Live dockable panels: P&L, throughput / bottleneck, BOM + cost
    sensitivity, benchmark, product value, scale scenarios, and a
    cumulative production ledger.
  * Interactive: speed slider, pause/step, follow / cutaway / cinematic
    cameras, snapshot export, click-to-inspect any element, a pre-run
    configurator, disruption injection, and clear-yard.

Install:
    py -3.12 -m pip install pygame moderngl numpy

Run:
    py -3.12 assembly_line.py               fullscreen
    py -3.12 assembly_line.py --window      windowed 1600x900
    py -3.12 assembly_line.py --selftest    head-less model + DB check
    py -3.12 assembly_line.py --shots 6,40  offscreen PNG renders
"""

from __future__ import annotations

import math
import os
import random
import sqlite3
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import pygame

import al_build as AL
from al_build import (
    ASSUMPTIONS,
    STAGES,
    STAGE_INDEX,
    DomeSpec,
    add_box,
    break_even,
    benchmark,
    build_dome_catalog,
    build_finished_dome_mesh,
    product_value,
    random_spec,
    scale_scenarios,
    station_cycle_times,
    throughput,
    unit_economics,
)
from dome_model import normalize
from materials import (
    MAT_CONCRETE,
    MAT_EMISSIVE,
    MAT_GLASS,
    MAT_GRASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_WOOD,
)
from mesh_builder import Mesh, MeshBuilder

# ---------------------------------------------------------------------------
# Line layout
# ---------------------------------------------------------------------------

CARRIAGE_TOP = 0.62
DECK_Z = CARRIAGE_TOP + AL.FLOOR_TOP
STATION_SPACING = 13.0
START_X = -16.0
RAIL_GAUGE = 2.2
STATION_X = [i * STATION_SPACING for i in range(len(STAGES))]
PICKUP_X = STATION_X[-1] + 14.0
TURNTABLE_X = PICKUP_X + 14.0
PLATTER_TOP = 0.62
LIFT_Z = 4.6
SUN_CYCLE_SECS = 80.0
DB_FILE = "dome_yard.sqlite3"

# Sales lot layout
OFFICE_POS = (TURNTABLE_X + 30.0, -7.0)
DEPOT_POS = (TURNTABLE_X + 30.0, -14.5)
EXIT_POS = (TURNTABLE_X + 95.0, -26.0)
SALE_AUTO_INTERVAL = 22.0        # sim-seconds between automatic sales

SKY_COLOR = (0.55, 0.70, 0.86)

# Animation pacing. Reported metrics (steps, distance, labor-hours, $) are
# the model's real numbers; these constants only compress the *animation*
# so a full build is watchable. The speed slider multiplies animation dt.
PLACE_ANIM_PER_LABOR_MIN = 0.028    # animation seconds shown per labor-minute
ANIM_WALK_SPEED = 8.5               # m/s on screen (real pace is ~1.3)
TRAVEL_SECS = 2.4

# ===========================================================================
# Shaders
# ===========================================================================

SCENE_VS = """
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
in float in_mat;
uniform mat4 u_mvp;
uniform mat4 u_model;
out vec3 v_world;
out vec3 v_local;
out vec3 v_normal;
out vec4 v_color;
flat out float v_mat;
void main() {
    vec4 world = u_model * vec4(in_position, 1.0);
    v_world = world.xyz;
    v_local = in_position;
    v_normal = mat3(u_model) * in_normal;
    v_color = in_color;
    v_mat = in_mat;
    gl_Position = u_mvp * world;
}
"""

SCENE_FS = """
#version 330
in vec3 v_world;
in vec3 v_local;
in vec3 v_normal;
in vec4 v_color;
flat in float v_mat;
uniform vec3 u_camera_position;
uniform vec3 u_light_direction;
uniform vec3 u_sky_color;
uniform vec3 u_tint;
uniform float u_cut_z;
uniform float u_force_alpha;   // >0 overrides alpha (x-ray see-through)
out vec4 frag_color;

float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}
float surface_pattern(int id, vec3 p, vec3 n) {
    if (id == 1) {
        float az = atan(p.y, p.x);
        vec2 g = vec2(az * 14.0, p.z * 3.6);
        g.x += step(0.5, fract(g.y * 0.5)) * 0.5;
        float row_gap = 1.0 - smoothstep(0.02, 0.12, fract(g.y));
        float col_gap = 1.0 - smoothstep(0.01, 0.06, fract(g.x));
        return (0.95 + 0.10 * hash21(floor(g)))
             * (1.0 - 0.38 * max(row_gap, col_gap * 0.8));
    }
    if (id == 2) {
        return 1.0 + 0.14 * sin(p.x * 7.0 + p.z * 5.0)
                          * sin(p.y * 6.0 - p.z * 3.0);
    }
    if (id == 4) {
        return 1.0 + 0.08 * sin((p.x + p.y) * 25.0 + sin(p.z * 8.0) * 2.0);
    }
    if (id == 5) {
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0)) : cross(n, vec3(1.0, 0.0, 0.0)));
        vec3 t2 = cross(n, t1);
        vec2 uv = vec2(dot(p, t1), dot(p, t2)) * 3.0;
        vec2 f = abs(fract(uv) - 0.5);
        return 0.85 + 0.55 * (1.0 - (1.0 - smoothstep(0.44, 0.5,
                                                       max(f.x, f.y))));
    }
    if (id == 6) {
        float speck = 0.95 + 0.08 * hash21(floor(p.xy * 6.0));
        float jx = 1.0 - smoothstep(0.0, 0.02,
            abs(fract(p.x / 2.4) - 0.5) * 2.4 - 1.16);
        float jy = 1.0 - smoothstep(0.0, 0.02,
            abs(fract(p.y / 2.4) - 0.5) * 2.4 - 1.16);
        return speck * (1.0 - 0.25 * max(jx, jy));
    }
    if (id == 7) {
        float gap = 1.0 - smoothstep(0.02, 0.06, fract(p.y / 0.145));
        float row = hash21(vec2(floor(p.y / 0.145), 0.0));
        return (0.96 + 0.07 * sin(p.x * 40.0 + row * 20.0))
             * (1.0 - 0.45 * gap);
    }
    if (id == 8) {
        return (0.90 + 0.16 * hash21(floor(p.xy * 1.5)))
             * (0.95 + 0.10 * hash21(floor(p.xy * 9.0)));
    }
    if (id == 9) {
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0)) : cross(n, vec3(1.0, 0.0, 0.0)));
        return 1.0 + 0.10 * sin(dot(p, t1) * 30.0);
    }
    if (id == 10) {
        return 0.95 + 0.08 * sin(p.x * 60.0) * sin(p.y * 60.0)
             + 0.05 * sin(p.z * 45.0);
    }
    return 1.0;
}
void main() {
    if (v_local.z > u_cut_z) { discard; }
    vec3 normal = normalize(v_normal);
    if (!gl_FrontFacing) { normal = -normal; }
    vec3 light_direction = normalize(-u_light_direction);
    vec3 view_direction = normalize(u_camera_position - v_world);
    vec3 half_direction = normalize(light_direction + view_direction);
    float diffuse = max(dot(normal, light_direction), 0.0);
    float specular = pow(max(dot(normal, half_direction), 0.0), 48.0);
    float rim = pow(1.0 - max(dot(normal, view_direction), 0.0), 3.0);
    int mat_id = int(v_mat + 0.5);
    vec3 col = v_color.rgb * u_tint;
    if (mat_id == 12) {
        frag_color = vec4(col * 1.3,
            u_force_alpha > 0.001 ? u_force_alpha : v_color.a);
        return;
    }
    float pattern = surface_pattern(mat_id, v_local, normal);
    vec3 base = col * pattern;
    vec3 lit = base * (0.40 + 0.62 * diffuse);
    lit += vec3(1.0, 0.98, 0.92) * specular * (mat_id == 3 ? 0.9 : 0.30);
    lit += u_sky_color * rim * (mat_id == 3 ? 0.45 : 0.12);
    float alpha = v_color.a;
    if (mat_id == 3) { alpha = clamp(alpha + rim * 0.5, 0.0, 1.0); }
    if (u_force_alpha > 0.001) { alpha = u_force_alpha; }
    float dist = length(u_camera_position - v_world);
    float fog = clamp((dist - 95.0) / 280.0, 0.0, 0.9);
    frag_color = vec4(mix(lit, u_sky_color, fog), alpha);
}
"""

OVERLAY_VS = """
#version 330
in vec2 in_pos;
uniform vec4 u_rect;
uniform vec2 u_screen;
out vec2 v_uv;
void main() {
    v_uv = in_pos;
    vec2 p = (u_rect.xy + in_pos * u_rect.zw) / u_screen * 2.0 - 1.0;
    gl_Position = vec4(p, 0.0, 1.0);
}
"""

OVERLAY_FS = """
#version 330
in vec2 v_uv;
uniform sampler2D u_tex;
uniform vec4 u_color;
uniform float u_use_tex;
out vec4 frag_color;
void main() {
    if (u_use_tex > 0.5) {
        vec4 c = texture(u_tex, v_uv);
        frag_color = vec4(c.rgb, c.a * u_color.a);
    } else {
        frag_color = u_color;
    }
}
"""

# ===========================================================================
# Matrix helpers
# ===========================================================================

def perspective(fov_y_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_y_deg) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at(eye, target, up_hint=(0.0, 0.0, 1.0)):
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, np.asarray(up_hint, np.float32)))
    up = normalize(np.cross(right, forward))
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = right
    m[1, :3] = up
    m[2, :3] = -forward
    m[0, 3] = -float(np.dot(right, eye))
    m[1, 3] = -float(np.dot(up, eye))
    m[2, 3] = float(np.dot(forward, eye))
    return m


def mat_translate(x, y, z):
    m = np.eye(4, dtype=np.float32)
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    return m


def mat_rot_z(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[0, 1] = c, -s
    m[1, 0], m[1, 1] = s, c
    return m


def mat_scale(sx, sy, sz):
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[1, 1], m[2, 2] = sx, sy, sz
    return m


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def project_point(mvp, p, w, h):
    v = mvp @ np.array([p[0], p[1], p[2], 1.0], dtype=np.float32)
    if v[3] <= 1e-5:
        return None
    ndc = v[:3] / v[3]
    if abs(ndc[0]) > 1.2 or abs(ndc[1]) > 1.2 or ndc[2] < -1 or ndc[2] > 1:
        return None
    return ((ndc[0] * 0.5 + 0.5) * w, (1.0 - (ndc[1] * 0.5 + 0.5)) * h)


# ===========================================================================
# Static scene geometry
# ===========================================================================

DIGIT_SEGS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgcde", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
SEG_DEFS = {
    "a": (0.0, 1.0, True), "g": (0.0, 0.0, True), "d": (0.0, -1.0, True),
    "b": (0.5, 0.5, False), "c": (0.5, -0.5, False),
    "f": (-0.5, 0.5, False), "e": (-0.5, -0.5, False),
}
SIGN_AMBER = (1.0, 0.62, 0.10)


def add_digit(b, x, y, z, ch, scale=1.0):
    half_w, half_h = 0.22 * scale, 0.45 * scale
    for seg in DIGIT_SEGS[ch]:
        oy, oz, horizontal = SEG_DEFS[seg]
        if horizontal:
            add_box(b, (x, y, z + oz * half_h),
                    (0.05, 2 * half_w, 0.07 * scale), SIGN_AMBER,
                    mat_id=MAT_EMISSIVE)
        else:
            add_box(b, (x, y - oy * 2.0 * half_w, z + oz * half_h),
                    (0.05, 0.07 * scale, half_h), SIGN_AMBER,
                    mat_id=MAT_EMISSIVE)


def add_station_sign(b, x, number, color):
    add_box(b, (x, 0.0, 9.45), (0.14, 3.6, 1.7), (0.10, 0.12, 0.16),
            mat_id=MAT_METAL)
    add_box(b, (x - 0.09, 1.25, 9.45), (0.06, 0.7, 1.1), color,
            mat_id=MAT_EMISSIVE)
    text = str(number)
    if len(text) == 1:
        add_digit(b, x - 0.10, -0.30, 9.45, text, 1.2)
    else:
        add_digit(b, x - 0.10, 0.15, 9.45, text[0], 1.2)
        add_digit(b, x - 0.10, -0.70, 9.45, text[1], 1.2)


def add_gantry(b, x, color):
    steel = (0.74, 0.77, 0.80)
    for sy in (-5.2, 5.2):
        add_box(b, (x, sy, 4.1), (0.5, 0.5, 8.2), steel, mat_id=MAT_METAL)
        add_box(b, (x, sy, 1.0), (0.56, 0.56, 0.8), color)
    add_box(b, (x, 0.0, 8.35), (0.6, 11.0, 0.5), steel, mat_id=MAT_METAL)


def add_pallet(b, x, y, color):
    add_box(b, (x, y, 0.07), (1.4, 1.1, 0.14), (0.55, 0.42, 0.25),
            mat_id=MAT_WOOD)
    add_box(b, (x, y, 0.45), (1.3, 1.0, 0.62), color)
    lighter = tuple(min(1.0, c * 1.25 + 0.05) for c in color)
    add_box(b, (x + 0.1, y, 0.90), (1.0, 0.8, 0.28), lighter)


def build_worker_mesh():
    """A single hi-vis worker, feet at z=0, facing +X."""
    b = MeshBuilder()
    b.cylinder((-0.09, 0, 0.0), (-0.09, 0, 0.46), 0.065, 6, (0.16, 0.18, 0.30))
    b.cylinder((0.09, 0, 0.0), (0.09, 0, 0.46), 0.065, 6, (0.16, 0.18, 0.30))
    b.cylinder((0, 0, 0.44), (0, 0, 1.06), 0.17, 8, (1.00, 0.45, 0.05))
    b.cylinder((0, 0, 0.70), (0, 0, 0.80), 0.175, 8, (0.88, 0.88, 0.25))
    b.sphere((0, 0, 1.22), 0.13, (0.87, 0.66, 0.50), rings=5, sides=8)
    b.sphere((0, 0, 1.30), 0.115, (0.95, 0.75, 0.10), rings=4, sides=8)
    return b.build()


def build_environment():
    b = MeshBuilder()
    b.disc((0.0, 0.0, -0.05), 340.0, 48, (0.30, 0.36, 0.26), mat_id=MAT_GRASS)
    add_box(b, ((START_X + TURNTABLE_X) / 2, 0.0, -0.09),
            (TURNTABLE_X - START_X + 44.0, 28.0, 0.18), (0.55, 0.55, 0.52),
            mat_id=MAT_CONCRETE)
    rail_end = PICKUP_X + 3.0
    x = START_X - 2.0
    while x < rail_end:
        add_box(b, (x, 0.0, 0.045), (0.24, 2 * RAIL_GAUGE + 1.2, 0.09),
                (0.35, 0.28, 0.22), mat_id=MAT_WOOD)
        x += 2.0
    for sy in (-RAIL_GAUGE, RAIL_GAUGE):
        add_box(b, ((START_X - 2 + rail_end) / 2, sy, 0.16),
                (rail_end - START_X + 4.0, 0.16, 0.14), (0.60, 0.62, 0.66),
                mat_id=MAT_METAL)
    for i, stage in enumerate(STAGES):
        x = STATION_X[i]
        add_gantry(b, x, stage.color)
        add_station_sign(b, x, i + 1, stage.color)
        add_pallet(b, x + 4.6, -5.4, stage.color)
        add_pallet(b, x - 4.6, 5.4, stage.color)
    crane_yellow = (0.95, 0.70, 0.12)
    for cx in (PICKUP_X - 3.5, TURNTABLE_X + 5.5):
        for sy in (-7.4, 7.4):
            add_box(b, (cx, sy, 5.5), (0.8, 0.8, 11.0), crane_yellow,
                    mat_id=MAT_METAL)
    for sy in (-7.4, 7.4):
        add_box(b, ((PICKUP_X - 3.5 + TURNTABLE_X + 5.5) / 2, sy, 11.3),
                (TURNTABLE_X - PICKUP_X + 12.0, 0.9, 0.6), crane_yellow,
                mat_id=MAT_METAL)
    b.cylinder((TURNTABLE_X, 0.0, 0.0), (TURNTABLE_X, 0.0, 0.25), 7.0, 40,
               (0.48, 0.48, 0.46), mat_id=MAT_CONCRETE)
    add_box(b, (TURNTABLE_X + 7.4, 1.0, 0.65), (1.5, 1.1, 1.3),
            (0.85, 0.65, 0.10), mat_id=MAT_METAL)
    add_box(b, (TURNTABLE_X + 7.4, -1.6, 0.75), (0.9, 0.7, 1.5),
            (0.65, 0.68, 0.72), mat_id=MAT_METAL)
    for i in range(18):
        a = 2 * math.pi * i / 18 + 0.35
        r = 130.0 + (i % 4) * 24.0
        tx = (START_X + TURNTABLE_X) / 2 + r * math.cos(a) * 1.7
        ty = r * math.sin(a) * 0.55
        if abs(ty) < 17:
            continue
        h = 5.0 + (i % 3) * 1.4
        b.cylinder((tx, ty, 0.0), (tx, ty, h), 0.3, 8, (0.34, 0.22, 0.12),
                   mat_id=MAT_WOOD)
        for lvl in range(3):
            z0 = h - 1.0 + lvl * 1.2
            b.cone((tx, ty, z0), (tx, ty, z0 + 3.0), 2.4 - lvl * 0.45, 10,
                   (0.12, 0.31, 0.15), mat_id=MAT_GRASS)
    return b.build()


def build_carriage():
    b = MeshBuilder()
    dark = (0.30, 0.32, 0.36)
    for sy in (-RAIL_GAUGE, RAIL_GAUGE):
        add_box(b, (0.0, sy, 0.47), (6.8, 0.5, 0.16), dark, mat_id=MAT_METAL)
    for sx in (-2.6, 0.0, 2.6):
        add_box(b, (sx, 0.0, 0.47), (0.4, 2 * RAIL_GAUGE, 0.16), dark,
                mat_id=MAT_METAL)
    b.cylinder((0, 0, 0.55), (0, 0, CARRIAGE_TOP), 4.6, 36,
               (0.42, 0.44, 0.48), mat_id=MAT_METAL)
    b.cylinder((0, 0, CARRIAGE_TOP - 0.015), (0, 0, CARRIAGE_TOP), 4.62, 36,
               (0.90, 0.72, 0.10), cap_ends=False)
    for ax in (-2.4, -0.8, 0.8, 2.4):
        for sy in (-RAIL_GAUGE, RAIL_GAUGE):
            b.cylinder((ax, sy - 0.13, 0.31), (ax, sy + 0.13, 0.31), 0.16,
                       10, (0.18, 0.19, 0.22), mat_id=MAT_METAL)
    return b.build()


def build_platter():
    b = MeshBuilder()
    b.cylinder((0, 0, 0.0), (0, 0, 0.37), 6.4, 48, (0.42, 0.44, 0.48),
               mat_id=MAT_METAL)
    b.cylinder((0, 0, 0.27), (0, 0, 0.37), 6.43, 48, (0.95, 0.75, 0.10),
               cap_ends=False)
    for i in range(48):
        a = 2 * math.pi * i / 48
        add_box(b, (6.62 * math.cos(a), 6.62 * math.sin(a), 0.14),
                (0.30, 0.34, 0.20), (0.30, 0.32, 0.36), mat_id=MAT_METAL,
                yaw=a)
    for i in range(12):
        a = 2 * math.pi * i / 12
        add_box(b, (3.5 * math.cos(a), 3.5 * math.sin(a), 0.385),
                (5.4, 0.12, 0.02), (0.32, 0.34, 0.38), yaw=a)
    b.cylinder((0, 0, 0.37), (0, 0, 0.45), 0.5, 16, (0.55, 0.57, 0.62),
               mat_id=MAT_METAL)
    return b.build()


def build_bridge():
    b = MeshBuilder()
    cy = (0.95, 0.70, 0.12)
    add_box(b, (0.0, 0.0, 10.85), (1.0, 16.2, 0.7), cy, mat_id=MAT_METAL)
    for sy in (-7.4, 7.4):
        add_box(b, (0.0, sy, 11.15), (1.6, 1.2, 0.5), (0.30, 0.32, 0.36),
                mat_id=MAT_METAL)
    add_box(b, (0.0, 0.0, 10.30), (1.4, 1.6, 0.5), (0.30, 0.32, 0.36),
            mat_id=MAT_METAL)
    return b.build()


def build_cable_unit():
    b = MeshBuilder()
    b.cylinder((0, 0, 0), (0, 0, -1.0), 1.0, 8, (0.22, 0.22, 0.25),
               mat_id=MAT_METAL, cap_ends=False)
    return b.build()


def build_hook():
    b = MeshBuilder()
    add_box(b, (0.0, 0.0, -0.25), (0.42, 0.30, 0.50), (0.85, 0.62, 0.10),
            mat_id=MAT_METAL)
    b.sphere((0.0, 0.0, -0.58), 0.11, (0.45, 0.47, 0.52), rings=4, sides=8)
    b.cone((0.0, 0.0, -0.60), (0.12, 0.0, -0.86), 0.09, 8, (0.45, 0.47, 0.52))
    return b.build()


def build_sun():
    b = MeshBuilder()
    b.sphere((0, 0, 0), 5.0, (1.0, 0.95, 0.72), mat_id=MAT_EMISSIVE,
             rings=8, sides=12)
    return b.build()


def build_material_box():
    """A small crate of material a worker carries (origin at its center)."""
    b = MeshBuilder()
    add_box(b, (0, 0, 0), (0.34, 0.30, 0.26), (0.72, 0.60, 0.36),
            mat_id=MAT_WOOD)
    add_box(b, (0, 0, 0.14), (0.30, 0.26, 0.05), (0.85, 0.72, 0.45))
    return b.build()


def build_pallet_box():
    """A stockpile crate (origin at its base center)."""
    b = MeshBuilder()
    add_box(b, (0, 0, 0.0), (0.9, 0.8, 0.5), (0.72, 0.62, 0.42))
    add_box(b, (0, 0, 0.3), (0.7, 0.6, 0.2), (0.85, 0.76, 0.55))
    return b.build()


def build_sales_office():
    """A small sales office building (origin at base center, faces -X)."""
    b = MeshBuilder()
    wall = (0.86, 0.82, 0.72)
    add_box(b, (0, 0, 1.6), (7.0, 5.0, 3.2), wall, mat_id=MAT_PLAIN)
    # gable roof
    for sy in (-1, 1):
        b.triangle((-3.5, sy * 2.5, 3.2), (3.5, sy * 2.5, 3.2),
                   (0.0, 0.0, 4.4), (0.55, 0.32, 0.24), mat_id=MAT_WOOD)
    for sx in (-3.5, 3.5):
        b.quad((sx, -2.5, 3.2), (sx, 2.5, 3.2), (sx * 0.0, 2.5, 4.4),
               (sx * 0.0, -2.5, 4.4), (1, 0, 0), (0.45, 0.24, 0.18),
               mat_id=MAT_WOOD)
    # door + windows on the -X face
    add_box(b, (-3.52, 0.0, 1.05), (0.1, 1.1, 2.1), (0.35, 0.25, 0.18),
            mat_id=MAT_WOOD)
    for wy in (-1.6, 1.6):
        add_box(b, (-3.52, wy, 2.0), (0.08, 1.0, 0.9), (0.55, 0.75, 0.85),
                alpha=0.6, mat_id=MAT_GLASS)
    # illuminated sign board over the door
    add_box(b, (-3.7, 0.0, 3.9), (0.2, 3.4, 0.9), (0.15, 0.35, 0.75),
            mat_id=MAT_EMISSIVE)
    add_box(b, (-3.55, 0.0, 3.9), (0.1, 3.2, 0.7), (0.95, 0.97, 1.0),
            mat_id=MAT_EMISSIVE)
    return b.build()


def build_truck():
    """A flatbed transport truck (origin at base center, faces +X)."""
    b = MeshBuilder()
    dark = (0.20, 0.22, 0.26)
    cab = (0.80, 0.20, 0.18)
    # chassis
    add_box(b, (0.0, 0.0, 0.7), (9.0, 2.4, 0.4), dark, mat_id=MAT_METAL)
    # flatbed deck
    add_box(b, (-1.2, 0.0, 1.0), (6.0, 2.6, 0.2), (0.45, 0.40, 0.34),
            mat_id=MAT_WOOD)
    # cab
    add_box(b, (3.3, 0.0, 1.4), (2.2, 2.3, 1.8), cab, mat_id=MAT_METAL)
    add_box(b, (2.3, 0.0, 2.0), (0.3, 2.1, 0.7), (0.55, 0.75, 0.85),
            alpha=0.6, mat_id=MAT_GLASS)
    # wheels
    for wx in (3.2, -1.2, -3.2):
        for sy in (-1.25, 1.25):
            b.cylinder((wx, sy - 0.18, 0.42), (wx, sy + 0.18, 0.42), 0.42,
                       10, (0.10, 0.10, 0.12), mat_id=MAT_METAL)
    return b.build()


def build_customer():
    """A prospective buyer figure (origin at feet, faces +X)."""
    b = MeshBuilder()
    b.cylinder((-0.09, 0, 0.0), (-0.09, 0, 0.48), 0.07, 6, (0.20, 0.22, 0.30))
    b.cylinder((0.09, 0, 0.0), (0.09, 0, 0.48), 0.07, 6, (0.20, 0.22, 0.30))
    b.cylinder((0, 0, 0.46), (0, 0, 1.12), 0.19, 8, (0.20, 0.42, 0.68))
    b.sphere((0, 0, 1.28), 0.14, (0.88, 0.68, 0.54), rings=5, sides=8)
    return b.build()


# ===========================================================================
# Persistence — the finished-dome yard
# ===========================================================================

class YardDB:
    def __init__(self, path=None):
        self.conn = sqlite3.connect(path or os.environ.get("AL_DB", DB_FILE))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS domes (
                serial INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, dtype TEXT, radius REAL, frequency INTEGER,
                layout TEXT, cladding TEXT, floor_area REAL,
                material REAL, labor_cost REAL, overhead REAL,
                total_cost REAL, price REAL, margin REAL, monthly REAL,
                labor_hours REAL, steps INTEGER, distance_m REAL,
                solar_kw REAL, r_value REAL,
                cr REAL, cg REAL, cb REAL, created TEXT, sold INTEGER)
        """)
        self.conn.commit()

    def add(self, rec: dict) -> int:
        cols = ("name dtype radius frequency layout cladding floor_area "
                "material labor_cost overhead total_cost price margin monthly "
                "labor_hours steps distance_m solar_kw r_value cr cg cb "
                "created sold").split()
        placeholders = ",".join("?" for _ in cols)
        cur = self.conn.execute(
            f"INSERT INTO domes ({','.join(cols)}) VALUES ({placeholders})",
            [rec.get(c, 0) for c in cols])
        self.conn.commit()
        return cur.lastrowid

    def mark_sold(self, serial):
        self.conn.execute("UPDATE domes SET sold=1 WHERE serial=?", (serial,))
        self.conn.commit()

    def all(self) -> list[dict]:
        cur = self.conn.execute("SELECT * FROM domes ORDER BY serial")
        names = [d[0] for d in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]

    def clear(self):
        self.conn.execute("DELETE FROM domes")
        self.conn.execute("DELETE FROM sqlite_sequence WHERE name='domes'")
        self.conn.commit()

    def summary(self) -> dict:
        cur = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(price),0), "
            "COALESCE(SUM(margin),0), COALESCE(SUM(floor_area),0), "
            "COALESCE(SUM(labor_hours),0), COALESCE(AVG(margin),0) "
            "FROM domes")
        n, rev, profit, area, hrs, avg_margin = cur.fetchone()
        return {"count": n, "revenue": rev, "profit": profit,
                "area": area, "labor_hours": hrs, "avg_margin": avg_margin}

    def sales_summary(self) -> dict:
        cur = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(price),0), "
            "COALESCE(SUM(margin),0) FROM domes WHERE sold=1")
        n, rev, profit = cur.fetchone()
        return {"sold": n, "sold_revenue": rev, "sold_profit": profit}


# ===========================================================================
# GPU wrappers
# ===========================================================================

class GpuMesh:
    def __init__(self, ctx, program, mesh: Mesh):
        self.vbo = ctx.buffer(mesh.vertices.tobytes())
        layout = [(self.vbo, "3f 3f 4f 1f",
                   "in_position", "in_normal", "in_color", "in_mat")]
        self.opaque_vao = None
        self.transparent_vao = None
        if len(mesh.opaque):
            ibo = ctx.buffer(mesh.opaque.tobytes())
            self.opaque_vao = ctx.vertex_array(program, layout, ibo,
                                               index_element_size=4)
        if len(mesh.transparent):
            ibo = ctx.buffer(mesh.transparent.tobytes())
            self.transparent_vao = ctx.vertex_array(program, layout, ibo,
                                                    index_element_size=4)


class DomeGpu:
    """A built catalog on the GPU; visible subset is an index-buffer write."""

    def __init__(self, ctx, program, cat: AL.Catalog):
        mesh = cat.b.build()
        self.full_opaque = mesh.opaque
        self.full_transparent = mesh.transparent
        self.stages = cat.stages
        # element ranges per stage, in catalog order
        self.stage_ranges = {
            s.key: [(e.o0, e.o1, e.t0, e.t1) for e in cat.by_stage[s.key]]
            for s in cat.stages}
        self.vbo = ctx.buffer(mesh.vertices.tobytes())
        layout = [(self.vbo, "3f 3f 4f 1f",
                   "in_position", "in_normal", "in_color", "in_mat")]
        self.opaque_ibo = ctx.buffer(reserve=max(4, mesh.opaque.nbytes))
        self.transparent_ibo = ctx.buffer(
            reserve=max(4, mesh.transparent.nbytes))
        self.opaque_vao = ctx.vertex_array(program, layout, self.opaque_ibo,
                                           index_element_size=4)
        self.transparent_vao = ctx.vertex_array(
            program, layout, self.transparent_ibo, index_element_size=4)
        self.opaque_count = 0
        self.transparent_count = 0
        self.signature = None

    def release(self):
        for o in (self.opaque_vao, self.transparent_vao, self.opaque_ibo,
                  self.transparent_ibo, self.vbo):
            try:
                o.release()
            except Exception:
                pass

    def update(self, placed_counts: dict[str, int]):
        sig = tuple(placed_counts[s.key] for s in self.stages)
        if sig == self.signature:
            return
        self.signature = sig
        chunks_o, chunks_t = [], []
        for stage in self.stages:
            k = placed_counts[stage.key]
            for (o0, o1, t0, t1) in self.stage_ranges[stage.key][:k]:
                if o1 > o0:
                    chunks_o.append(self.full_opaque[o0:o1])
                if t1 > t0:
                    chunks_t.append(self.full_transparent[t0:t1])
        opaque = (np.concatenate(chunks_o) if chunks_o
                  else np.zeros(0, np.uint32))
        transparent = (np.concatenate(chunks_t) if chunks_t
                       else np.zeros(0, np.uint32))
        self.opaque_count = len(opaque)
        self.transparent_count = len(transparent)
        if self.opaque_count:
            self.opaque_ibo.write(opaque.tobytes())
        if self.transparent_count:
            self.transparent_ibo.write(transparent.tobytes())


def spec_from_rec(rec) -> DomeSpec:
    return DomeSpec(
        serial=rec.get("serial", 0), name=rec.get("name", "Dome"),
        dtype=rec.get("dtype", "home"), radius=rec.get("radius", 4.0),
        frequency=int(rec.get("frequency", 3)),
        layout=rec.get("layout", "Studio"),
        cladding=rec.get("cladding", "Slate Scale"),
        cladding_color=(rec.get("cr", 0.2), rec.get("cg", 0.3),
                        rec.get("cb", 0.38)))


class InspectDome:
    """A finished dome rebuilt with independent per-layer GPU geometry so
    each layer can be toggled visible/hidden and solid/transparent — a
    Photoshop-style layers view for buyer inspection."""

    def __init__(self, ctx, program, spec: DomeSpec):
        self.ctx = ctx
        self.spec = spec
        cat, info = build_dome_catalog(spec)
        self.info = info
        self.stages = cat.stages
        mesh = cat.b.build()
        self.vbo = ctx.buffer(mesh.vertices.tobytes())
        layout = [(self.vbo, "3f 3f 4f 1f",
                   "in_position", "in_normal", "in_color", "in_mat")]
        self.stage_vaos = {}
        for s in cat.stages:
            els = cat.by_stage.get(s.key, [])
            o = [mesh.opaque[e.o0:e.o1] for e in els if e.o1 > e.o0]
            t = [mesh.transparent[e.t0:e.t1] for e in els if e.t1 > e.t0]
            ovao = tvao = None
            if o:
                oi = ctx.buffer(np.concatenate(o).tobytes())
                ovao = ctx.vertex_array(program, layout, oi,
                                        index_element_size=4)
            if t:
                ti = ctx.buffer(np.concatenate(t).tobytes())
                tvao = ctx.vertex_array(program, layout, ti,
                                        index_element_size=4)
            self.stage_vaos[s.key] = (ovao, tvao)
        # layer states: visible + solid (else transparent)
        self.layers = {s.key: {"visible": True, "solid": True}
                       for s in cat.stages}

    def release(self):
        for ovao, tvao in self.stage_vaos.values():
            for v in (ovao, tvao):
                if v is not None:
                    try:
                        v.release()
                    except Exception:
                        pass
        try:
            self.vbo.release()
        except Exception:
            pass


# ===========================================================================
# Worker labor model
# ===========================================================================

class Worker:
    def __init__(self, home_xy, stockpile_xy=(0.0, -3.2)):
        self.home = np.array(home_xy, dtype=np.float64)
        self.pos = self.home.copy()
        self.stockpile = np.array(stockpile_xy, dtype=np.float64)
        self.yaw = 0.0
        self.queue: list[AL.Element] = []
        self.qi = 0
        self.state = "idle"      # idle | fetch | walk | place
        self.carrying = False
        self.timer = 0.0
        self.target = self.home.copy()

    def assign(self, elements, home_xy, stockpile_xy):
        self.home = np.array(home_xy, dtype=np.float64)
        self.pos = self.home.copy()
        self.stockpile = np.array(stockpile_xy, dtype=np.float64)
        self.queue = list(elements)
        self.qi = 0
        self.carrying = False
        self.timer = 0.0
        self._aim()

    def _aim(self):
        # Each element: walk to the stockpile to pick up material, then
        # carry it to the placement point.
        if self.qi < len(self.queue):
            self.state = "fetch"
            self.carrying = False
            self.target = self.stockpile.copy()
        else:
            self.target = self.home.copy()
            self.state = "idle"

    def _walk_toward(self, dt_anim, dome_x):
        world_target = np.array([dome_x + self.target[0], self.target[1]])
        world_pos = np.array([dome_x + self.pos[0], self.pos[1]])
        delta = world_target - world_pos
        dist = float(np.linalg.norm(delta))
        step = ANIM_WALK_SPEED * dt_anim
        if dist <= step or dist < 1e-6:
            self.pos = self.target.copy()
            return dist, True
        self.yaw = math.atan2(delta[1], delta[0])
        self.pos = self.pos + (delta / dist) * step
        return step, False

    def update(self, dt_anim, dome_x, run, stalled):
        """Returns real distance walked this frame (meters)."""
        if self.state == "idle" or stalled:
            return 0.0
        moved = 0.0
        if self.state == "fetch":
            moved, arrived = self._walk_toward(dt_anim, dome_x)
            if arrived:
                self.carrying = True
                el = self.queue[self.qi]
                self.target = np.array([el.floor_point[0],
                                        el.floor_point[1]])
                self.state = "walk"
        elif self.state == "walk":
            moved, arrived = self._walk_toward(dt_anim, dome_x)
            if arrived:
                el = self.queue[self.qi]
                self.state = "place"
                self.timer = max(0.12, el.labor_min * PLACE_ANIM_PER_LABOR_MIN)
        elif self.state == "place":
            self.timer -= dt_anim
            if self.timer <= 0.0:
                el = self.queue[self.qi]
                run.on_placed(el)
                self.carrying = False
                self.qi += 1
                self._aim()
        return moved


# ===========================================================================
# Production run — one dome from raw floor to finished home
# ===========================================================================

@dataclass
class ProductionRun:
    spec: DomeSpec
    cat: AL.Catalog
    info: dict
    gpu: DomeGpu
    placed: dict = field(default_factory=dict)
    material: float = 0.0
    labor_min: float = 0.0
    steps: float = 0.0
    distance_m: float = 0.0
    elements_done: int = 0
    econ_preview: dict = field(default_factory=dict)

    def __post_init__(self):
        self.stages = self.cat.stages
        self.recent_placements = []
        self.placed = {s.key: 0 for s in self.stages}
        self.totals = {s.key: len(self.cat.by_stage[s.key])
                       for s in self.stages}
        self.overhead = unit_economics(self.cat, self.spec)["overhead"]
        self.econ_preview = unit_economics(self.cat, self.spec)

    def on_placed(self, el: AL.Element):
        self.placed[el.stage] += 1
        self.material += el.material_cost
        self.labor_min += el.labor_min
        self.elements_done += 1
        self.recent_placements.append(el)

    def add_distance(self, meters):
        self.distance_m += meters
        self.steps = self.distance_m / ASSUMPTIONS["worker_stride_m"]

    def station_done(self, key):
        return self.placed[key] >= self.totals[key]

    def labor_cost(self):
        return (self.labor_min / 60.0) * ASSUMPTIONS["burdened_wage_per_hour"]

    def cost_so_far(self):
        # material + labor accrued + full per-unit overhead once started
        oh = self.overhead if self.elements_done else 0.0
        return self.material + self.labor_cost() + oh

    def final_record(self) -> dict:
        econ = unit_economics(self.cat, self.spec,
                              labor_hours=self.labor_min / 60.0)
        pv = product_value(self.cat, self.spec)
        c = self.spec.cladding_color
        return {
            "name": self.spec.name, "dtype": self.spec.dtype,
            "radius": self.spec.radius,
            "frequency": self.spec.frequency, "layout": self.spec.layout,
            "cladding": self.spec.cladding, "floor_area": self.spec.floor_area,
            "material": econ["material"], "labor_cost": econ["labor_cost"],
            "overhead": econ["overhead"], "total_cost": econ["total_cost"],
            "price": econ["price"], "margin": econ["margin"],
            "monthly": self.spec.monthly_payment,
            "labor_hours": self.labor_min / 60.0, "steps": int(self.steps),
            "distance_m": self.distance_m, "solar_kw": pv["solar_kw"],
            "r_value": pv["r_value"], "cr": c[0], "cg": c[1], "cb": c[2],
            "created": time.strftime("%Y-%m-%d %H:%M"), "sold": 0,
        }


# ===========================================================================
# Timeline
# ===========================================================================

@dataclass
class Phase:
    kind: str
    station: int = -1
    x0: float = 0.0
    x1: float = 0.0
    dur: float = 0.0


def build_phases(n_stations=len(STAGES)):
    phases = [Phase("intro", dur=1.2)]
    x_prev = START_X
    for i in range(n_stations):
        phases.append(Phase("travel", i, x_prev, STATION_X[i], TRAVEL_SECS))
        phases.append(Phase("work", i))
        x_prev = STATION_X[i]
    phases.append(Phase("tocrane", -1, x_prev, PICKUP_X, 4.0))
    phases.append(Phase("hook", dur=2.6))
    phases.append(Phase("lift", dur=3.4))
    phases.append(Phase("carry", -1, PICKUP_X, TURNTABLE_X, 5.5))
    phases.append(Phase("lower", dur=3.4))
    phases.append(Phase("unhook", dur=2.6))
    phases.append(Phase("park", dur=2.0))
    return phases


# ===========================================================================
# UI toolkit
# ===========================================================================

@dataclass
class Button:
    key: str
    label: str
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    toggle: bool = False


class YardDome:
    def __init__(self, rec, x, y):
        self.rec = rec
        self.x = x
        self.y = y
        self.dtype = rec.get("dtype") or "home"
        ref = min(AL.DOME_TYPES[self.dtype].radius_range[1],
                  AL.REFERENCE_RADIUS)
        self.scale = rec["radius"] / ref
        self.tint = (rec["cr"] / 0.28, rec["cg"] / 0.34, rec["cb"] / 0.38)
        self.tint = tuple(max(0.4, min(1.6, t)) for t in self.tint)
        self.sold = bool(rec.get("sold"))


def yard_slot(index):
    """Grid of finished domes behind the turntable."""
    cols = 6
    row, col = divmod(index, cols)
    x = TURNTABLE_X + 4.0 + col * 11.0
    y = -22.0 - row * 11.0
    return x, y


# ===========================================================================
# Application
# ===========================================================================

class AssemblyLineApp:
    def __init__(self, headless=False, windowed=False, size=(1600, 900),
                 seed=None):
        self.headless = headless
        self.rng = random.Random(seed)
        pygame.init()
        import moderngl
        self.moderngl = moderngl
        if headless:
            self.size = size
            self.ctx = moderngl.create_standalone_context()
            self.color_tex = self.ctx.texture(size, components=3)
            self.depth_rb = self.ctx.depth_renderbuffer(size)
            self.fbo = self.ctx.framebuffer([self.color_tex], self.depth_rb)
        else:
            flags = pygame.OPENGL | pygame.DOUBLEBUF
            if windowed:
                pygame.display.set_mode(size, flags)
            else:
                pygame.display.set_mode((0, 0), flags | pygame.FULLSCREEN)
            pygame.display.set_caption("Dome Home Assembly Line")
            self.size = pygame.display.get_window_size()
            self.ctx = moderngl.create_context()
            self.fbo = self.ctx.screen

        ctx = self.ctx
        self.scene_prog = ctx.program(vertex_shader=SCENE_VS,
                                      fragment_shader=SCENE_FS)
        self.overlay_prog = ctx.program(vertex_shader=OVERLAY_VS,
                                        fragment_shader=OVERLAY_FS)
        quad = np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype=np.float32)
        self.quad_vbo = ctx.buffer(quad.tobytes())
        self.quad_vao = ctx.vertex_array(
            self.overlay_prog, [(self.quad_vbo, "2f", "in_pos")])

        self.env = GpuMesh(ctx, self.scene_prog, build_environment())
        self.carriage = GpuMesh(ctx, self.scene_prog, build_carriage())
        self.platter = GpuMesh(ctx, self.scene_prog, build_platter())
        self.bridge = GpuMesh(ctx, self.scene_prog, build_bridge())
        self.cable = GpuMesh(ctx, self.scene_prog, build_cable_unit())
        self.hook = GpuMesh(ctx, self.scene_prog, build_hook())
        self.sun = GpuMesh(ctx, self.scene_prog, build_sun())
        self.worker_mesh = GpuMesh(ctx, self.scene_prog, build_worker_mesh())
        self.carry_mesh = GpuMesh(ctx, self.scene_prog, build_material_box())
        self.pallet_mesh = GpuMesh(ctx, self.scene_prog, build_pallet_box())
        self.office_mesh = GpuMesh(ctx, self.scene_prog, build_sales_office())
        self.truck_mesh = GpuMesh(ctx, self.scene_prog, build_truck())
        self.customer_mesh = GpuMesh(ctx, self.scene_prog, build_customer())
        self.finished_meshes = {
            dt: GpuMesh(ctx, self.scene_prog, build_finished_dome_mesh(dt))
            for dt in AL.DOME_TYPE_LIST}
        self.finished = self.finished_meshes["home"]

        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 19)
        self.font_small = pygame.font.SysFont("consolas", 16)
        self.font_tiny = pygame.font.SysFont("consolas", 14)
        self.text_cache: dict = {}

        # database + yard
        self.db = YardDB()
        self.yard: list[YardDome] = []
        self._load_yard()

        # crew
        self.workers_per_station = ASSUMPTIONS["workers_per_station"]
        self.crew = [Worker((0, 0))
                     for _ in range(self.workers_per_station)]

        # sim state
        self.phases = build_phases()
        self.run: ProductionRun | None = None
        self.next_serial = self.db.summary()["count"] + 1
        self.speed = 4.0
        self.paused = False
        self.follow = True
        self.force_cutaway = False
        self.cinematic = False
        self.cine_speed = 0.20
        self.xray = False
        self.popups: list[dict] = []
        self.auto_run = True
        self.pipeline_view = True
        self.panel = "pnl"
        self.sensitivity = {"lumber": 1.0, "resin": 1.0, "wage": 1.0}
        self.event_log: list[str] = []
        self.stall_timer = 0.0
        self.stall_reason = ""
        self.downtime_cost = 0.0
        self.hover_element = None
        self.hover_screen = None
        self.selected_yard = None
        self.inspect = None          # InspectDome when inspecting a yard dome
        self.tour = False
        self.sale = None             # active buying-process state
        self.sale_cooldown = SALE_AUTO_INTERVAL
        self.next_slot = 0
        self.configuring = False
        self.config_spec = None
        self.cinematic_angle = 0.0
        self.saved_cam = None

        # camera
        self.cam_yaw = math.radians(-118.0)
        self.cam_pitch = math.radians(17.0)
        self.cam_dist = 18.0
        self.cam_target = np.array([START_X, 0.0, 2.5], dtype=np.float32)
        self.dragging = False
        self.mouse = (0, 0)
        self.buttons: dict[str, Button] = {}
        self.slider_rect = (0, 0, 0, 0)
        self.slider_drag = False

        self.phase_idx = 0
        self.phase_t = 0.0
        self.track_t = 0.0
        self.platter_yaw = 0.0
        self.line_time = 0.0
        self.start_new_run()

    # -- yard / runs -----------------------------------------------------

    def _load_yard(self):
        self.yard = []
        recs = self.db.all()
        for i, rec in enumerate(recs):
            x, y = yard_slot(i)
            yd = YardDome(rec, x, y)
            if not yd.sold:               # sold domes have been hauled away
                self.yard.append(yd)
        self.next_slot = len(recs)

    def start_new_run(self, spec=None):
        if self.run is not None:
            self.run.gpu.release()
        spec = spec or random_spec(self.next_serial, self.rng)
        spec.serial = self.next_serial
        cat, info = build_dome_catalog(spec)
        gpu = DomeGpu(self.ctx, self.scene_prog, cat)
        self.run = ProductionRun(spec=spec, cat=cat, info=info, gpu=gpu)
        self.phases = build_phases(len(self.run.stages))
        self.phase_idx = 0
        self.phase_t = 0.0
        self.line_time = 0.0
        self.stall_timer = 0.0
        self.downtime_cost = 0.0
        tag = spec.type.name if spec.dtype != "home" else spec.layout
        self.log(f"Run #{spec.serial} started: {spec.name} "
                 f"({spec.type.name} · {tag} · {spec.floor_area:.0f} m²)")

    def finish_run(self):
        rec = self.run.final_record()
        serial = self.db.add(rec)
        rec["serial"] = serial
        x, y = yard_slot(self.next_slot)
        self.next_slot += 1
        self.yard.append(YardDome(rec, x, y))
        self.log(f"#{serial} {rec['name']} built — to yard "
                 f"({self.money(rec['price'])})")
        self.next_serial = serial + 1

    def log(self, msg):
        self.event_log.append(msg)
        self.event_log = self.event_log[-6:]

    # -- finished-dome inspection ---------------------------------------

    def enter_inspect(self, yd):
        self.exit_inspect()
        self.selected_yard = yd
        try:
            self.inspect = InspectDome(self.ctx, self.scene_prog,
                                       spec_from_rec(yd.rec))
        except Exception as exc:
            self.log(f"inspect failed: {exc}")
            self.inspect = None
            return
        self.saved_cam = (self.cam_target.copy(), self.cam_yaw,
                          self.cam_pitch, self.cam_dist, self.follow)
        self.follow = False
        self.tour = False
        self.cam_target = np.array([yd.x, yd.y, 2.0], dtype=np.float32)
        self.cam_yaw = math.radians(-120.0)
        self.cam_pitch = math.radians(16.0)
        self.cam_dist = 12.0 * max(0.6, yd.scale)

    def exit_inspect(self):
        if self.inspect is not None:
            self.inspect.release()
            self.inspect = None
        self.tour = False
        if self.saved_cam is not None:
            (self.cam_target, self.cam_yaw, self.cam_pitch, self.cam_dist,
             self.follow) = (self.saved_cam[0], *self.saved_cam[1:])
            self.saved_cam = None
        self.selected_yard = None

    def rebuild_inspect(self):
        if self.inspect is None or self.selected_yard is None:
            return
        spec = self.inspect.spec
        old_layers = self.inspect.layers
        self.inspect.release()
        self.inspect = InspectDome(self.ctx, self.scene_prog, spec)
        for k, v in old_layers.items():
            if k in self.inspect.layers:
                self.inspect.layers[k] = v

    def toggle_tour(self):
        self.tour = not self.tour
        yd = self.selected_yard
        if yd is None:
            return
        if self.tour:
            # buyer's-eye view: stand low and close, shell x-rayed
            self.cam_target = np.array([yd.x, yd.y, 1.2], dtype=np.float32)
            self.cam_pitch = math.radians(4.0)
            self.cam_dist = 5.0 * max(0.6, yd.scale)
        else:
            self.cam_target = np.array([yd.x, yd.y, 2.0], dtype=np.float32)
            self.cam_pitch = math.radians(16.0)
            self.cam_dist = 12.0 * max(0.6, yd.scale)

    # -- sales / buying process -----------------------------------------

    SALE_PHASES = [("approach", 4.0), ("consider", 2.5), ("truck_in", 4.0),
                   ("load", 2.5), ("haul", 5.5)]

    def start_sale(self, yd=None):
        candidates = [y for y in self.yard if not y.sold]
        if not candidates:
            return False
        yd = yd or self.rng.choice(candidates)
        if yd.sold:
            return False
        self.sale = {"yd": yd, "idx": 0, "t": 0.0}
        self.log(f"Customer arriving for #{yd.rec.get('serial','?')} "
                 f"{yd.rec['name']}")
        return True

    def _sale_sold(self, yd):
        yd.sold = True
        yd.rec["sold"] = 1
        serial = yd.rec.get("serial")
        if serial:
            self.db.mark_sold(serial)
        self.log(f"SOLD #{serial} {yd.rec['name']} — "
                 f"{self.money(yd.rec['price'])} "
                 f"({self.money(yd.rec.get('monthly', 0))}/mo)")

    def _sale_delivered(self, yd):
        if yd in self.yard:
            self.yard.remove(yd)
        self.log(f"Delivered #{yd.rec.get('serial','?')} {yd.rec['name']} "
                 f"— hauled off the lot")
        self.sale = None
        self.sale_cooldown = SALE_AUTO_INTERVAL

    def update_sale(self, dt_anim):
        if self.sale is None:
            self.sale_cooldown -= dt_anim
            if (self.auto_run and self.sale_cooldown <= 0.0
                    and self.inspect is None
                    and any(not y.sold for y in self.yard)):
                if not self.start_sale():
                    self.sale_cooldown = SALE_AUTO_INTERVAL
            return
        self.sale["t"] += dt_anim
        phase, dur = self.SALE_PHASES[self.sale["idx"]]
        if self.sale["t"] >= dur:
            self.sale["idx"] += 1
            self.sale["t"] = 0.0
            if self.sale["idx"] == 2:            # decision made
                self._sale_sold(self.sale["yd"])
            if self.sale["idx"] >= len(self.SALE_PHASES):
                self._sale_delivered(self.sale["yd"])

    def sale_positions(self):
        """Returns dict with customer/truck/dome render positions."""
        s = self.sale
        yd = s["yd"]
        phase, dur = self.SALE_PHASES[s["idx"]]
        f = smoothstep(s["t"] / dur)
        door = np.array([OFFICE_POS[0] - 4.0, OFFICE_POS[1]])
        dome = np.array([yd.x, yd.y])
        near = dome + np.array([4.5, 1.5])          # customer stands here
        truck_spot = dome + np.array([8.0, 0.0])    # truck parks here
        out = {"customer": None, "truck": None, "truck_yaw": 0.0,
               "dome_on_truck": False, "dome_pos": (yd.x, yd.y, 0.0)}

        def lerp(a, b, t):
            return a + (b - a) * t

        def yaw_of(a, b):
            d = b - a
            return math.atan2(d[1], d[0])
        if phase == "approach":
            out["customer"] = lerp(door, near, f)
        elif phase == "consider":
            out["customer"] = near
        elif phase == "truck_in":
            out["customer"] = near
            out["truck"] = lerp(np.array(DEPOT_POS), truck_spot, f)
            out["truck_yaw"] = yaw_of(np.array(DEPOT_POS), truck_spot)
        elif phase == "load":
            out["customer"] = near
            out["truck"] = truck_spot
            out["truck_yaw"] = math.pi
        elif phase == "haul":
            pos = lerp(truck_spot, np.array(EXIT_POS), f)
            out["truck"] = pos
            out["truck_yaw"] = yaw_of(truck_spot, np.array(EXIT_POS))
            out["dome_on_truck"] = True
            yaw = out["truck_yaw"]
            bed = np.array([pos[0] - 1.6 * math.cos(yaw),
                            pos[1] - 1.6 * math.sin(yaw)])
            out["dome_pos"] = (bed[0], bed[1], 1.15)
        return out

    @property
    def phase(self):
        return self.phases[self.phase_idx]

    # -- simulation ------------------------------------------------------

    def advance_phase(self):
        self.phase_idx += 1
        self.phase_t = 0.0
        if self.phase_idx >= len(self.phases):
            # dome finished -> yard, then next run
            self.finish_run()
            if self.auto_run:
                self.start_new_run()
            else:
                self.paused = True
                self.phase_idx = len(self.phases) - 1
            return
        ph = self.phase
        if ph.kind == "work":
            self._begin_station(ph.station)

    def _begin_station(self, station):
        stage = self.run.stages[station]
        # only assign elements not yet placed, so re-assigning mid-station
        # (crew change / worker absence) never re-places or double-counts
        placed = self.run.placed[stage.key]
        els = self.run.cat.by_stage[stage.key][placed:]
        n = len(self.crew)
        floor_r = self.run.info["floor_r"]
        # material stockpile sits at the deck edge on the -Y side
        stock_y = -min(3.4, floor_r - 0.2)
        for w in range(n):
            subset = els[w::n]
            hx = (-1.6 if w % 2 else 1.6) * (0.5 + 0.35 * (w // 2))
            hy = stock_y + 0.4
            sx = (-0.9 if w % 2 else 0.9) * (0.4 + 0.3 * (w // 2))
            self.crew[w].assign(subset, (hx, hy), (sx, stock_y))

    def update(self, dt):
        if self.paused:
            return
        dt_anim = dt * self.speed
        self.line_time += dt_anim
        ph = self.phase

        # disruption stall countdown
        stalled = False
        if self.stall_timer > 0.0:
            self.stall_timer -= dt_anim
            stalled = True
            self.downtime_cost += (dt_anim / 3600.0) \
                * ASSUMPTIONS["burdened_wage_per_hour"] * len(self.crew)
            if self.stall_timer <= 0.0:
                self.log(f"{self.stall_reason} cleared — line resumes")

        if ph.kind in ("travel", "tocrane", "carry"):
            self.phase_t += dt_anim
            if self.phase_t >= ph.dur:
                self.advance_phase()
        elif ph.kind in ("intro", "hook", "lift", "lower", "unhook", "park"):
            self.phase_t += dt_anim
            if self.phase_t >= ph.dur:
                self.advance_phase()
        elif ph.kind == "work":
            dome_x = STATION_X[ph.station]
            for w in self.crew:
                moved = w.update(dt_anim, dome_x, self.run, stalled)
                if moved:
                    self.run.add_distance(moved)
            # spawn a fade-away cost popup for each newly placed element
            for el in self.run.recent_placements:
                wp = (dome_x + float(el.centroid[0]), float(el.centroid[1]),
                      CARRIAGE_TOP + float(el.centroid[2]))
                self.popups.append({"pos": wp,
                                    "text": f"+${el.material_cost:,.0f}",
                                    "age": 0.0})
            self.run.recent_placements.clear()
            if self.run.station_done(self.run.stages[ph.station].key):
                self.advance_phase()
        else:
            self.run.recent_placements.clear()

        # age money popups (real time, so fade rate is speed-independent)
        for p in self.popups:
            p["age"] += dt
        self.popups = [p for p in self.popups if p["age"] < 1.5][-60:]

        # buying process
        self.update_sale(dt_anim)

        self.run.gpu.update(self.run.placed)

        # sun / turntable
        sun_dir, tracking, az, _el = self.sun_state()
        if tracking:
            target = az + math.pi / 2.0
            d = target - self.platter_yaw
            self.platter_yaw += max(-0.6 * dt_anim, min(0.6 * dt_anim, d))

        # cameras — cinematic adds a slow orbit on top of the user's angle,
        # so you can still drag to change the pitch/height while it sweeps.
        if self.cinematic:
            self.cam_yaw += self.cine_speed * dt
        x, y, z, *_ = self.dome_pose()
        goal = np.array([x, y, z + 2.4], dtype=np.float32)
        if self.follow or self.cinematic:
            self.cam_target += (goal - self.cam_target) * min(1.0, dt * 2.2)

    def sun_state(self):
        park = self.phase.kind == "park" or self.phase_idx >= len(self.phases)
        if park:
            self.track_t += 0.0
        # track once a dome is parked in the yard scene; otherwise fixed
        frac = (self.line_time % SUN_CYCLE_SECS) / SUN_CYCLE_SECS
        az = math.radians(-165.0 + 150.0 * frac)
        el = math.radians(16.0 + 52.0 * math.sin(math.pi * frac))
        d = np.array([math.cos(az) * math.cos(el),
                      math.sin(az) * math.cos(el), math.sin(el)])
        return d, True, az, el

    def dome_pose(self):
        """(x,y,z,yaw, on_carriage, hook_z|None, bridge_x)."""
        ph = self.phase
        anchor = self.run.info["anchor_top"]
        dur = max(ph.dur, 1e-6)
        t = smoothstep(self.phase_t / dur)
        if ph.kind in ("intro", "work"):
            station = ph.station if ph.kind == "work" else 0
            x = STATION_X[station] if ph.kind == "work" else START_X
            return x, 0.0, CARRIAGE_TOP, 0.0, True, None, PICKUP_X
        if ph.kind in ("travel", "tocrane"):
            x = ph.x0 + (ph.x1 - ph.x0) * t
            return x, 0.0, CARRIAGE_TOP, 0.0, True, None, PICKUP_X
        if ph.kind == "hook":
            hz = CARRIAGE_TOP + anchor + 0.15
            return PICKUP_X, 0.0, CARRIAGE_TOP, 0.0, True, \
                9.8 - (9.8 - hz) * t, PICKUP_X
        if ph.kind == "lift":
            z = CARRIAGE_TOP + (LIFT_Z - CARRIAGE_TOP) * t
            return PICKUP_X, 0.0, z, 0.0, False, z + anchor + 0.15, PICKUP_X
        if ph.kind == "carry":
            x = ph.x0 + (ph.x1 - ph.x0) * t
            return x, 0.0, LIFT_Z, 0.0, False, LIFT_Z + anchor + 0.15, x
        if ph.kind == "lower":
            z = LIFT_Z + (PLATTER_TOP - LIFT_Z) * t
            return TURNTABLE_X, 0.0, z, self.platter_yaw, False, \
                z + anchor + 0.15, TURNTABLE_X
        if ph.kind == "unhook":
            hz = PLATTER_TOP + anchor + 0.15
            return TURNTABLE_X, 0.0, PLATTER_TOP, self.platter_yaw, False, \
                hz + (9.8 - hz) * t, TURNTABLE_X
        # park
        return TURNTABLE_X, 0.0, PLATTER_TOP, self.platter_yaw, False, \
            None, TURNTABLE_X

    # -- disruptions -----------------------------------------------------

    def inject(self, kind):
        if kind == "supply":
            self.stall_timer = 6.0
            self.stall_reason = "Supply delay"
            self.log("! Supply delay injected — station starved 6 min-eq")
        elif kind == "breakdown":
            self.stall_timer = 8.0
            self.stall_reason = "Machine breakdown"
            self.log("! Equipment breakdown — maintenance responding")
        elif kind == "absence":
            if len(self.crew) > 1:
                self.crew.pop()
                self.log(f"! Worker absence — crew down to {len(self.crew)}")
                if self.phase.kind == "work":
                    self._begin_station(self.phase.station)

    # ===================================================================
    # Rendering
    # ===================================================================

    def upload_model(self, m):
        self.scene_prog["u_model"].write(
            np.ascontiguousarray(m.T.astype(np.float32)).tobytes())

    def draw_gpu(self, gm, model=None, transparent=False, tint=(1, 1, 1)):
        self.upload_model(model if model is not None
                          else np.eye(4, dtype=np.float32))
        self.scene_prog["u_tint"].value = tint
        vao = gm.transparent_vao if transparent else gm.opaque_vao
        if vao is not None:
            vao.render(self.moderngl.TRIANGLES)

    def render(self):
        ctx = self.ctx
        mgl = self.moderngl
        w, h = self.size
        self.fbo.use()
        ctx.viewport = (0, 0, w, h)
        self.fbo.clear(*SKY_COLOR, 1.0, depth=1.0)
        ctx.enable(mgl.DEPTH_TEST | mgl.BLEND)
        ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA

        eye = self.cam_target + np.array([
            self.cam_dist * math.cos(self.cam_pitch) * math.cos(self.cam_yaw),
            self.cam_dist * math.cos(self.cam_pitch) * math.sin(self.cam_yaw),
            self.cam_dist * math.sin(self.cam_pitch)], dtype=np.float32)
        proj = perspective(56.0, w / h, 0.1, 700.0)
        view = look_at(eye, self.cam_target)
        self.mvp = proj @ view
        prog = self.scene_prog
        prog["u_mvp"].write(np.ascontiguousarray(self.mvp.T).tobytes())
        prog["u_camera_position"].value = tuple(map(float, eye))
        sun_dir, _tracking, _az, _el = self.sun_state()
        prog["u_light_direction"].value = tuple(map(float, -sun_dir))
        prog["u_sky_color"].value = SKY_COLOR
        prog["u_force_alpha"].value = 0.0

        x, y, z, yaw, on_carriage, hook_z, bridge_x = self.dome_pose()
        dome_model = mat_translate(x, y, z) @ mat_rot_z(yaw)
        interior = (self.phase.kind == "work"
                    and self.run.stages[self.phase.station].key == "interior")
        cutaway = self.force_cutaway or interior
        dome_cut = 2.95 if cutaway else 1e9

        prog["u_cut_z"].value = 1e9
        self.draw_gpu(self.env)
        carriage_x = x if on_carriage else PICKUP_X
        self.draw_gpu(self.carriage, mat_translate(carriage_x, 0, 0))
        self.draw_gpu(self.platter,
                      mat_translate(TURNTABLE_X, 0, 0.25)
                      @ mat_rot_z(self.platter_yaw))
        self.draw_gpu(self.bridge, mat_translate(bridge_x, 0, 0))
        if hook_z is not None:
            length = max(0.05, 10.0 - hook_z)
            self.draw_gpu(self.cable, mat_translate(bridge_x, 0, 10.0)
                          @ mat_scale(0.04, 0.04, length))
            self.draw_gpu(self.hook, mat_translate(bridge_x, 0, hook_z))
        sun_pos = self.cam_target + sun_dir.astype(np.float32) * 280.0
        self.draw_gpu(self.sun, mat_translate(*sun_pos))

        # sales office (static structure by the lot)
        self.draw_gpu(self.office_mesh, mat_translate(*OFFICE_POS, 0))

        # buying process: customer, truck, and the sold dome on the bed
        sale_pos = self.sale_positions() if self.sale else None
        if sale_pos:
            if sale_pos["customer"] is not None:
                cx, cy = sale_pos["customer"]
                self.draw_gpu(self.customer_mesh, mat_translate(cx, cy, 0))
            if sale_pos["truck"] is not None:
                tx, ty = sale_pos["truck"]
                self.draw_gpu(self.truck_mesh,
                              mat_translate(tx, ty, 0)
                              @ mat_rot_z(sale_pos["truck_yaw"]))

        # finished domes in the yard (skip inspected; move a hauled dome)
        for yd in self.yard:
            if self.inspect is not None and yd is self.selected_yard:
                continue
            if sale_pos and yd is self.sale["yd"] and sale_pos["dome_on_truck"]:
                dp = sale_pos["dome_pos"]
                self.draw_gpu(
                    self.finished_meshes.get(yd.dtype, self.finished),
                    mat_translate(dp[0], dp[1], dp[2])
                    @ mat_rot_z(sale_pos["truck_yaw"])
                    @ mat_scale(yd.scale, yd.scale, yd.scale), tint=yd.tint)
                continue
            self.draw_gpu(self.finished_meshes.get(yd.dtype, self.finished),
                          mat_translate(yd.x, yd.y, 0)
                          @ mat_scale(yd.scale, yd.scale, yd.scale),
                          tint=yd.tint)
        if self.inspect is not None:
            self._draw_inspect()

        # pipeline: show trailing/leading domes at other stations
        if self.pipeline_view and self.phase.kind == "work":
            self._draw_pipeline(x)

        # workers + material stockpile (active station only)
        if self.phase.kind == "work":
            self._draw_stockpile(x)
            self._draw_workers(x)

        # the dome under construction
        xray = self.xray and not cutaway
        prog["u_cut_z"].value = dome_cut
        self.upload_model(dome_model)
        prog["u_tint"].value = (1, 1, 1)
        if xray:
            # whole shell rendered see-through so the interior stays visible
            prog["u_force_alpha"].value = 0.26
            ctx.depth_mask = False
            if self.run.gpu.opaque_count:
                self.run.gpu.opaque_vao.render(
                    mgl.TRIANGLES, vertices=self.run.gpu.opaque_count)
            if self.run.gpu.transparent_count:
                self.run.gpu.transparent_vao.render(
                    mgl.TRIANGLES, vertices=self.run.gpu.transparent_count)
            ctx.depth_mask = True
            prog["u_force_alpha"].value = 0.0
        else:
            if self.run.gpu.opaque_count:
                self.run.gpu.opaque_vao.render(
                    mgl.TRIANGLES, vertices=self.run.gpu.opaque_count)
            ctx.depth_mask = False
            if self.run.gpu.transparent_count:
                self.run.gpu.transparent_vao.render(
                    mgl.TRIANGLES, vertices=self.run.gpu.transparent_count)
            ctx.depth_mask = True

        prog["u_cut_z"].value = 1e9
        for yd in self.yard:
            if sale_pos and yd is self.sale["yd"] and sale_pos["dome_on_truck"]:
                continue
            self.draw_gpu(self.finished_meshes.get(yd.dtype, self.finished),
                          mat_translate(yd.x, yd.y, 0)
                          @ mat_scale(yd.scale, yd.scale, yd.scale),
                          transparent=True, tint=yd.tint)

        self.draw_hud()

    SHELL_KEYS = {"insulation", "sheetrock", "osb", "wrap", "shingles",
                  "fiberglass", "sheetmetal", "glazing", "steelplate",
                  "solar"}

    def _draw_inspect(self):
        insp = self.inspect
        yd = self.selected_yard
        mgl = self.moderngl
        prog = self.scene_prog
        prog["u_cut_z"].value = 1e9
        prog["u_tint"].value = (1, 1, 1)
        self.upload_model(mat_translate(yd.x, yd.y, 0))
        for s in insp.stages:
            L = insp.layers[s.key]
            if not L["visible"]:
                continue
            ovao, tvao = insp.stage_vaos[s.key]
            see_through = (not L["solid"]) or (self.tour and s.key in
                                               self.SHELL_KEYS)
            if see_through:
                prog["u_force_alpha"].value = 0.22
                self.ctx.depth_mask = False
                if ovao:
                    ovao.render(mgl.TRIANGLES)
                if tvao:
                    tvao.render(mgl.TRIANGLES)
                self.ctx.depth_mask = True
                prog["u_force_alpha"].value = 0.0
            else:
                if ovao:
                    ovao.render(mgl.TRIANGLES)
                self.ctx.depth_mask = False
                if tvao:
                    tvao.render(mgl.TRIANGLES)
                self.ctx.depth_mask = True

    def _draw_pipeline(self, hero_x):
        """Draw a couple of finished/leading domes at neighbouring stations
        to show the line running full (throughput visualization)."""
        station = self.phase.station
        mesh = self.finished_meshes.get(self.run.spec.dtype, self.finished)
        sc = 0.85 * self.run.spec.radius / AL.REFERENCE_RADIUS
        if station + 1 < len(self.run.stages):
            self.draw_gpu(mesh,
                          mat_translate(STATION_X[station + 1], 0, CARRIAGE_TOP)
                          @ mat_scale(sc, sc, sc), tint=(0.8, 0.85, 0.9))
            self.draw_gpu(self.carriage,
                          mat_translate(STATION_X[station + 1], 0, 0))

    def _draw_stockpile(self, dome_x):
        floor_r = self.run.info["floor_r"]
        sy = -min(3.4, floor_r - 0.2)
        col = self.run.stages[self.phase.station].color
        for i, (dx, dz, s) in enumerate(((-0.55, 0.0, 0.5), (0.4, 0.0, 0.55),
                                         (-0.1, 0.5, 0.42))):
            add = mat_translate(dome_x + dx, sy - 0.1, DECK_Z + 0.25 + dz)
            self.draw_gpu(self.pallet_mesh, add, tint=tuple(
                min(1.0, c * (0.8 + 0.1 * i)) for c in col))

    def _draw_workers(self, dome_x):
        for wk in self.crew:
            wx = dome_x + wk.pos[0]
            wy = wk.pos[1]
            m = mat_translate(wx, wy, DECK_Z) @ mat_rot_z(wk.yaw)
            self.draw_gpu(self.worker_mesh, m)
            if wk.carrying:
                # a small material box carried in front of the worker
                fx = wx + 0.28 * math.cos(wk.yaw)
                fy = wy + 0.28 * math.sin(wk.yaw)
                self.draw_gpu(self.carry_mesh,
                              mat_translate(fx, fy, DECK_Z + 0.55))

    # ===================================================================
    # HUD
    # ===================================================================

    def text_texture(self, key, lines, pad=8):
        cached = self.text_cache.get(key)
        if cached is not None and cached[0] == lines:
            return cached[1], cached[2], cached[3]
        if cached is not None:
            try:
                cached[1].release()
            except Exception:
                pass
        surfs = [font.render(text, True, color)
                 for text, color, font in lines if text != ""]
        if not surfs:
            surfs = [self.font_small.render(" ", True, (0, 0, 0))]
        width = max(s.get_width() for s in surfs) + pad * 2
        height = sum(s.get_height() + 3 for s in surfs) + pad * 2
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        yy = pad
        for s in surfs:
            surface.blit(s, (pad, yy))
            yy += s.get_height() + 3
        raw = pygame.image.tostring(surface, "RGBA", True)
        tex = self.ctx.texture((width, height), 4, raw)
        tex.filter = (self.moderngl.LINEAR, self.moderngl.LINEAR)
        self.text_cache[key] = (lines, tex, width, height)
        return tex, width, height

    def draw_rect(self, x, y_top, w, h, color):
        sw, sh = self.size
        self.overlay_prog["u_rect"].value = (x, sh - y_top - h, w, h)
        self.overlay_prog["u_screen"].value = (sw, sh)
        self.overlay_prog["u_color"].value = color
        self.overlay_prog["u_use_tex"].value = 0.0
        self.quad_vao.render(self.moderngl.TRIANGLE_STRIP)

    def draw_texture(self, tex, x, y_top, w, h, alpha=1.0):
        sw, sh = self.size
        tex.use(0)
        self.overlay_prog["u_tex"].value = 0
        self.overlay_prog["u_rect"].value = (x, sh - y_top - h, w, h)
        self.overlay_prog["u_screen"].value = (sw, sh)
        self.overlay_prog["u_color"].value = (1, 1, 1, alpha)
        self.overlay_prog["u_use_tex"].value = 1.0
        self.quad_vao.render(self.moderngl.TRIANGLE_STRIP)

    def draw_text_block(self, key, lines, x, y, bg=(0.03, 0.05, 0.08, 0.62)):
        tex, w, h = self.text_texture(key, lines)
        if bg:
            self.draw_rect(x - 4, y - 4, w + 8, h + 8, bg)
        self.draw_texture(tex, x, y, w, h)
        return w, h

    # -- money helpers ---------------------------------------------------

    def money(self, v):
        return f"${v:,.0f}"

    def banner_lines(self):
        ph = self.phase
        n = len(self.run.stages)
        amber = (255, 210, 90)
        grey = (215, 220, 226)
        sp = self.run.spec
        tag = sp.layout if sp.dtype == "home" else sp.type.name
        if ph.kind == "intro":
            return [(f"RUN #{sp.serial} — {sp.name}  "
                     f"({sp.type.name} · {tag} · {sp.floor_area:.0f}"
                     f" m² · {sp.cladding})", amber, self.font_big)]
        if ph.kind == "travel":
            s = self.run.stages[ph.station]
            return [(f"-> STATION {ph.station + 1}/{n}  {s.title}", amber,
                     self.font_big)]
        if ph.kind == "work":
            s = self.run.stages[ph.station]
            done = self.run.placed[s.key]
            tot = self.run.totals[s.key]
            return [(f"STATION {ph.station + 1}/{n}  {s.title}   "
                     f"[{done}/{tot}]", amber, self.font_big),
                    (s.desc, grey, self.font_med)]
        done_word = "HOME" if sp.dtype == "home" else sp.type.name.upper()
        labels = {"tocrane": "LINE COMPLETE — ROLLING TO CRANE",
                  "hook": "CRANE — HOOKING APEX ANCHOR",
                  "lift": "CRANE — LIFTING OFF CARRIAGE",
                  "carry": "CRANE — CARRYING TO TURNTABLE",
                  "lower": "CRANE — SETTING ON LAZY SUSAN",
                  "unhook": "CRANE — RELEASING HOOK",
                  "park": f"{done_word} COMPLETE — SUN-TRACKING TURNTABLE"}
        col = (140, 235, 150) if ph.kind == "park" else amber
        return [(labels.get(ph.kind, ph.kind), col, self.font_big)]

    def draw_yard_signs(self):
        """A price / BHPH-monthly sign floating over each finished dome."""
        w, h = self.size
        for yd in self.yard:
            if self.inspect is not None and yd is self.selected_yard:
                continue
            top = 2.6 * yd.scale + 1.4
            sp = project_point(self.mvp, (yd.x, yd.y, top), w, h)
            if sp is None:
                continue
            rec = yd.rec
            if yd.sold:
                lines = [("SOLD", (255, 130, 120), self.font_small)]
                key = ("sign", rec.get("serial"), "sold")
            else:
                lines = [(self.money(rec["price"]), (150, 240, 160),
                          self.font_small),
                         (f"{self.money(rec.get('monthly', 0))}/mo",
                          (210, 216, 224), self.font_tiny)]
                key = ("sign", rec.get("serial"), int(rec["price"]))
            tex, tw, th = self.text_texture(key, lines)
            self.draw_rect(sp[0] - tw / 2 - 3, sp[1] - th - 3, tw + 6, th + 6,
                           (0.04, 0.06, 0.10, 0.72))
            self.draw_texture(tex, sp[0] - tw / 2, sp[1] - th, tw, th)

    def draw_money_popups(self):
        w, h = self.size
        for p in self.popups:
            age = p["age"]
            frac = age / 1.5
            alpha = max(0.0, 1.0 - frac)
            sp = project_point(self.mvp, (p["pos"][0], p["pos"][1],
                                          p["pos"][2] + frac * 1.4), w, h)
            if sp is None:
                continue
            tex, tw, th = self.text_texture(("pop", p["text"]),
                                            [(p["text"], (150, 240, 160),
                                              self.font_small)], pad=2)
            self.draw_texture(tex, sp[0] - tw / 2, sp[1] - th, tw, th,
                              alpha=alpha)

    def draw_hud(self):
        ctx = self.ctx
        ctx.disable(self.moderngl.DEPTH_TEST)
        w, h = self.size
        amber = (255, 210, 90)
        white = (232, 236, 240)
        grey = (176, 182, 192)
        green = (130, 224, 150)

        inspecting = self.inspect is not None
        self.draw_yard_signs()
        if not inspecting:
            self.draw_money_popups()

        # top banner
        if inspecting:
            yd = self.selected_yard
            tname = AL.DOME_TYPES.get(yd.dtype, AL.DOME_TYPES["home"]).name
            banner = [(f"INSPECTING #{yd.rec.get('serial', '?')} — "
                       f"{yd.rec['name']} ({tname})", amber, self.font_big)]
            tex, tw, th = self.text_texture(
                ("ibanner", yd.rec.get("serial")), banner)
        else:
            tex, tw, th = self.text_texture(("banner", self.phase_idx,
                                             self.run.spec.serial,
                                             self.phase.kind == "work" and
                                             self.run.elements_done),
                                            self.banner_lines())
        self.draw_rect((w - tw) / 2 - 6, 8, tw + 12, th + 10,
                       (0.03, 0.05, 0.08, 0.66))
        self.draw_texture(tex, (w - tw) / 2, 13, tw, th)

        if not inspecting:
            # live money strip (money counter grown into a P&L ticker)
            r = self.run
            strip = [
                (f"COST TO DATE {self.money(r.cost_so_far())}", amber,
                 self.font_med),
                (f"materials {self.money(r.material)}   labor "
                 f"{self.money(r.labor_cost())}   overhead "
                 f"{self.money(r.overhead)}", grey, self.font_small),
                (f"elements placed {r.elements_done}/{len(r.cat.elements)}   "
                 f"worker steps {int(r.steps):,}   distance "
                 f"{r.distance_m:,.0f} m", white, self.font_small),
                (f"projected sale {self.money(r.econ_preview['price'])}   "
                 f"projected margin {self.money(r.econ_preview['margin'])} "
                 f"({r.econ_preview['margin_pct']:.0f}%)", green,
                 self.font_small),
            ]
            self.draw_text_block(("moneystrip", int(r.cost_so_far()),
                                  int(r.steps), r.elements_done), strip,
                                 14, th + 30)
            self.draw_text_block("checklist", self.checklist_lines(),
                                 14, th + 150)
            self.draw_panel()

        # bottom control bar
        self.draw_controls()

        # event log
        if self.event_log:
            lines = [("EVENT LOG", amber, self.font_small)] + [
                (m, grey, self.font_tiny) for m in self.event_log]
            tex, tw, th2 = self.text_texture(
                ("log", tuple(self.event_log)), lines)
            self.draw_rect(w - tw - 14, h - th2 - 92, tw + 8, th2 + 8,
                           (0.03, 0.05, 0.08, 0.55))
            self.draw_texture(tex, w - tw - 10, h - th2 - 88, tw, th2)

        # stall banner
        if self.stall_timer > 0.0:
            tex, tw, th2 = self.text_texture(
                ("stall", int(self.stall_timer * 5)),
                [(f"! {self.stall_reason.upper()} — LINE STALLED", (255, 120,
                  90), self.font_big)])
            self.draw_rect((w - tw) / 2 - 6, h - 150, tw + 12, th2 + 8,
                           (0.15, 0.03, 0.03, 0.7))
            self.draw_texture(tex, (w - tw) / 2, h - 146, tw, th2)

        # hover tooltip
        if self.hover_element and self.hover_screen:
            el = self.hover_element
            lines = [(el.label, amber, self.font_small),
                     (f"material {self.money(el.material_cost)}   "
                      f"labor {el.labor_min:.0f} min   "
                      f"{el.weight:.0f} kg", white, self.font_tiny)]
            tex, tw, th2 = self.text_texture(("tip", id(el)), lines)
            hx, hy = self.hover_screen
            self.draw_rect(hx + 10, hy - 4, tw + 8, th2 + 8,
                           (0.05, 0.07, 0.10, 0.9))
            self.draw_texture(tex, hx + 14, hy, tw, th2)

        # yard spec plate
        if self.selected_yard is not None:
            self.draw_spec_plate()

        # configurator overlay
        if self.configuring:
            self.draw_configurator()

        ctx.enable(self.moderngl.DEPTH_TEST)

    def checklist_lines(self):
        amber = (255, 210, 90)
        green = (120, 220, 140)
        grey = (150, 155, 165)
        white = (220, 224, 230)
        ph = self.phase
        active = ph.station if ph.kind in ("travel", "work") else -1
        lines = [("BUILD SEQUENCE", white, self.font_med)]
        for i, s in enumerate(self.run.stages):
            done = self.run.placed[s.key] >= self.run.totals[s.key] \
                and self.run.totals[s.key] > 0
            if self.phase_idx > 1 + i * 2 + 1:
                done = True
            if done:
                mark, col = "[x]", green
            elif i == active:
                mark, col = " > ", amber
            else:
                mark, col = "[ ]", grey
            lines.append((f"{mark} {i + 1:>2} {s.title}", col,
                          self.font_small))
        crane = ph.kind in ("tocrane", "hook", "lift", "carry", "lower",
                            "unhook")
        park = ph.kind == "park"
        lines.append((("[x]" if park else " > " if crane else "[ ]")
                      + "    CRANE TO TURNTABLE",
                      green if park else amber if crane else grey,
                      self.font_small))
        lines.append(((" > " if park else "[ ]") + "    SUN TRACKING",
                      amber if park else grey, self.font_small))
        return lines

    # -- dock panels -----------------------------------------------------

    def panel_lines(self):
        white = (230, 234, 240)
        amber = (255, 210, 90)
        grey = (176, 182, 192)
        green = (130, 224, 150)
        red = (240, 150, 130)
        r = self.run
        sens = self.sensitivity
        if self.panel == "pnl":
            econ = self._econ_with_sensitivity()
            return [("UNIT ECONOMICS (P&L)", white, self.font_med),
                    (f"sale price      {self.money(econ['price'])}", green,
                     self.font_small),
                    (f"materials      -{self.money(econ['material'])}", grey,
                     self.font_small),
                    (f"labor ({econ['labor_hours']:.0f} h) -"
                     f"{self.money(econ['labor_cost'])}", grey,
                     self.font_small),
                    (f"overhead       -{self.money(econ['overhead'])}", grey,
                     self.font_small),
                    (f"GROSS MARGIN    {self.money(econ['margin'])} "
                     f"({econ['margin_pct']:.0f}%)", amber, self.font_med),
                    ("", grey, self.font_small),
                    ("sensitivity toggles (click):", white, self.font_small),
                    (f"  lumber x{sens['lumber']:.2f}   "
                     f"resin x{sens['resin']:.2f}   "
                     f"wage x{sens['wage']:.2f}", grey, self.font_small)]
        if self.panel == "throughput":
            tp = throughput(r.cat, self.workers_per_station)
            bn = tp["bottleneck"]
            lines = [("THROUGHPUT & BOTTLENECK", white, self.font_med)]
            for row in tp["rows"]:
                mark = "<< BOTTLENECK" if row["key"] == bn["key"] else ""
                col = red if row["key"] == bn["key"] else grey
                lines.append((f"{row['title'][:16]:<16} "
                              f"{row['cycle_min']:5.0f} min {mark}", col,
                              self.font_tiny))
            fpy = ASSUMPTIONS["first_pass_yield"]
            econ = self._econ_with_sensitivity()
            rework = ((1.0 - fpy) * ASSUMPTIONS["rework_cost_fraction"]
                      * econ["total_cost"])
            dt_col = red if self.downtime_cost > 0 else grey
            lines += [
                ("", grey, self.font_small),
                (f"single-piece flow: {tp['single_flow_per_year']:.0f}/yr",
                 white, self.font_small),
                (f"pipelined (bottleneck): "
                 f"{tp['pipelined_per_year']:.0f}/yr", green,
                 self.font_small),
                (f"-> pipelining unlocks "
                 f"{tp['pipelined_per_year'] / max(1, tp['single_flow_per_year']):.1f}x",
                 amber, self.font_small),
                ("", grey, self.font_small),
                (f"QC first-pass yield {fpy * 100:.0f}%", grey,
                 self.font_small),
                (f"rework provision {self.money(rework)}", grey,
                 self.font_small),
                (f"downtime this run {self.money(self.downtime_cost)}",
                 dt_col, self.font_small)]
            return lines
        if self.panel == "bom":
            lines = [("BILL OF MATERIALS", white, self.font_med)]
            by_cat = {}
            for e in r.cat.elements:
                by_cat.setdefault(e.category, [0, 0.0])
                by_cat[e.category][0] += 1
                by_cat[e.category][1] += e.material_cost
            for cat_key, (cnt, cost) in sorted(
                    by_cat.items(), key=lambda kv: -kv[1][1])[:12]:
                lines.append((f"{cat_key:<11} {cnt:>4}  "
                              f"{self.money(cost)}", grey, self.font_tiny))
            lines.append((f"TOTAL MATERIAL {self.money(r.cat.material_cost())}",
                          amber, self.font_small))
            return lines
        if self.panel == "benchmark":
            econ = self._econ_with_sensitivity()
            days = self.run.spec.floor_area  # placeholder replaced below
            bd = self._build_days()
            bm = benchmark(r.cat, r.spec, econ, bd, r.cat.labor_minutes() / 60)
            d, c = bm["dome"], bm["conventional"]
            return [("VS CONVENTIONAL HOUSING", white, self.font_med),
                    (f"{'':14}{'DOME':>10}{'CONV':>10}", grey,
                     self.font_tiny),
                    (f"{'price':<14}{self.money(d['price']):>10}"
                     f"{self.money(c['price']):>10}", white, self.font_tiny),
                    (f"{'material':<14}{self.money(d['material']):>10}"
                     f"{self.money(c['material']):>10}", grey,
                     self.font_tiny),
                    (f"{'labor hrs':<14}{d['labor_hours']:>10.0f}"
                     f"{c['labor_hours']:>10.0f}", grey, self.font_tiny),
                    (f"{'build days':<14}{d['build_days']:>10.1f}"
                     f"{c['build_days']:>10.0f}", grey, self.font_tiny),
                    ("", grey, self.font_small),
                    (f"→ {c['labor_hours'] / max(1, d['labor_hours']):.1f}x "
                     f"less labor, "
                     f"{c['build_days'] / max(0.1, d['build_days']):.1f}x "
                     f"faster", green, self.font_small)]
        if self.panel == "value":
            pv = product_value(r.cat, r.spec)
            return [("FINISHED PRODUCT VALUE", white, self.font_med),
                    (f"floor area      {pv['floor_area']:.0f} m²", grey,
                     self.font_small),
                    (f"solar array     {pv['solar_kw']:.1f} kW "
                     f"({pv['solar_panels']} panels)", green,
                     self.font_small),
                    (f"daily generation {pv['daily_generation_kwh']:.0f} kWh",
                     grey, self.font_small),
                    (f"battery / autonomy {pv['battery_kwh']:.0f} kWh / "
                     f"{pv['autonomy_days']:.1f} d", grey, self.font_small),
                    (f"insulation      R-{pv['r_value']:.0f}", grey,
                     self.font_small),
                    (f"embodied carbon {pv['embodied_carbon_kg']:,.0f} kg",
                     grey, self.font_small),
                    (f"OSHA target     {pv['osha_target']:.1f}/100", grey,
                     self.font_small),
                    ("zero windows · sealed envelope", amber,
                     self.font_small)]
        if self.panel == "scale":
            econ = self._econ_with_sensitivity()
            tp = throughput(r.cat, self.workers_per_station)
            scn = scale_scenarios(tp["single_flow_per_year"], econ["margin"],
                                  econ["price"])
            lines = [("SCALE SCENARIOS", white, self.font_med),
                     (f"{'lines':<7}{'units/yr':>9}{'revenue':>12}"
                      f"{'profit':>12}", grey, self.font_tiny)]
            for s in scn:
                lines.append((f"{s['lines']:<7}{s['units_per_year']:>9.0f}"
                              f"{self.money(s['revenue']):>12}"
                              f"{self.money(s['gross_profit']):>12}", white,
                              self.font_tiny))
            be = break_even(econ["margin"], econ["overhead"])
            lines += [("", grey, self.font_small),
                      (f"CapEx/line {self.money(ASSUMPTIONS['line_capex'])}",
                       grey, self.font_small),
                      (f"break-even: {be['units_to_recover_capex']:.0f} "
                       f"units to recover CapEx", amber, self.font_small)]
            return lines
        if self.panel == "ledger":
            s = self.db.summary()
            sold = self.db.sales_summary()
            in_yard = len([y for y in self.yard if not y.sold])
            return [("PRODUCTION & SALES LEDGER", white, self.font_med),
                    (f"units built      {s['count']}", green, self.font_med),
                    (f"in yard (unsold) {in_yard}", grey, self.font_small),
                    (f"sold & delivered {sold['sold']}", green,
                     self.font_small),
                    (f"sold revenue     {self.money(sold['sold_revenue'])}",
                     white, self.font_small),
                    (f"sold gross profit {self.money(sold['sold_profit'])}",
                     green, self.font_small),
                    ("", grey, self.font_small),
                    (f"build value in yard "
                     f"{self.money(s['revenue'] - sold['sold_revenue'])}",
                     grey, self.font_small),
                    (f"total floor built {s['area']:,.0f} m²", grey,
                     self.font_small),
                    (f"avg margin/unit  {self.money(s['avg_margin'])}", grey,
                     self.font_small),
                    ("", grey, self.font_small),
                    ("click a yard dome to inspect · SELL to ship one",
                     amber, self.font_tiny)]
        return [("", white, self.font_small)]

    def _build_days(self):
        # emergent build time: total labor-hours / crew / shift-hours
        hrs = self.run.cat.labor_minutes() / 60.0
        return hrs / max(1, len(self.crew)) / ASSUMPTIONS["shift_hours_per_day"]

    def _econ_with_sensitivity(self):
        base = unit_economics(self.run.cat, self.run.spec)
        s = self.sensitivity
        # lumber affects frame/floor material; resin affects fiberglass/shingle
        mat = 0.0
        for e in self.run.cat.elements:
            f = 1.0
            if e.category in ("frame", "floor", "hub"):
                f = s["lumber"]
            elif e.category in ("fiberglass", "shingle", "wrap"):
                f = s["resin"]
            mat += e.material_cost * f
        labor = base["labor_cost"] * s["wage"]
        overhead = base["overhead"]
        total = mat + labor + overhead
        price = base["price"]
        return {"price": price, "material": mat, "labor_cost": labor,
                "labor_hours": base["labor_hours"], "overhead": overhead,
                "total_cost": total, "margin": price - total,
                "margin_pct": (price - total) / price * 100 if price else 0}

    def draw_panel(self):
        w, h = self.size
        pw = 360
        px = w - pw - 12
        py = 66
        tabs = [("pnl", "P&L"), ("throughput", "FLOW"), ("bom", "BOM"),
                ("benchmark", "VS"), ("value", "VALUE"), ("scale", "SCALE"),
                ("ledger", "YARD")]
        # tab row
        tab_w = pw / len(tabs)
        self.buttons_panel = []
        for i, (key, label) in enumerate(tabs):
            bx = px + i * tab_w
            active = self.panel == key
            self.draw_rect(bx, py, tab_w - 2, 24,
                           (0.16, 0.20, 0.28, 0.95) if active
                           else (0.06, 0.08, 0.12, 0.8))
            tex, tw, tht = self.text_texture(
                (f"tab{key}", active),
                [(label, (255, 220, 120) if active else (170, 176, 186),
                  self.font_tiny)], pad=2)
            self.draw_texture(tex, bx + (tab_w - tw) / 2, py + 5, tw, tht)
            self.buttons_panel.append(("tab:" + key, bx, py, tab_w - 2, 24))
        # body
        tex, tw, tht = self.text_texture(
            ("panelbody", self.panel, self.run.spec.serial,
             self.run.elements_done // 12, tuple(self.sensitivity.values())),
            self.panel_lines())
        self.draw_rect(px, py + 26, pw, tht + 10, (0.04, 0.06, 0.10, 0.82))
        self.draw_texture(tex, px + 6, py + 30, tw, tht)
        self.panel_body_rect = (px, py + 26, pw, tht + 10)

    def draw_controls(self):
        w, h = self.size
        bar_h = 46
        y = h - bar_h
        self.draw_rect(0, y, w, bar_h, (0.04, 0.06, 0.10, 0.85))
        self.buttons_bar = []
        x = 12

        def add_btn(key, label, width, active=False):
            nonlocal x
            self.draw_rect(x, y + 8, width, 30,
                           (0.20, 0.28, 0.20, 0.95) if active
                           else (0.10, 0.13, 0.18, 0.95))
            tex, tw, tht = self.text_texture((f"btn{key}", label, active),
                                             [(label, (235, 238, 244),
                                               self.font_small)], pad=4)
            self.draw_texture(tex, x + (width - tw) / 2, y + 14, tw, tht)
            self.buttons_bar.append((key, x, y + 8, width, 30))
            x += width + 6

        add_btn("pause", "> RUN" if self.paused else "|| PAUSE", 92)
        add_btn("step", "STEP", 60)
        # speed slider
        self.draw_rect(x, y + 18, 130, 8, (0.2, 0.22, 0.26, 1))
        frac = (math.log2(self.speed) + 2) / 5.0  # 0.25..8 -> 0..1
        hx = x + max(0, min(1, frac)) * 130
        self.draw_rect(hx - 5, y + 10, 10, 24, (0.9, 0.72, 0.2, 1))
        tex, tw, tht = self.text_texture(("spd", self.speed),
                                         [(f"x{self.speed:g}", (235, 238, 244),
                                           self.font_small)], pad=2)
        self.draw_texture(tex, x + 45, y + 1, tw, tht)
        self.slider_rect = (x, y + 10, 130, 24)
        x += 140
        add_btn("follow", "FOLLOW", 74, self.follow)
        add_btn("cutaway", "CUTAWAY", 82, self.force_cutaway)
        add_btn("xray", "X-RAY", 62, self.xray)
        add_btn("cinematic", "CINE", 54, self.cinematic)
        add_btn("snapshot", "SNAP", 56)
        add_btn("config", "CONFIG", 72)
        add_btn("auto", "AUTO", 54, self.auto_run)
        add_btn("wminus", "CREW -", 66)
        add_btn("wplus", f"{self.workers_per_station} +", 44)
        add_btn("sell", "SELL", 54, self.sale is not None)
        add_btn("supply", "SUPPLY×", 78)
        add_btn("breakdown", "BREAK×", 72)
        add_btn("absence", "ABSENT×", 78)
        add_btn("clear", "CLEAR", 66)

    def draw_spec_plate(self):
        rec = self.selected_yard.rec
        w, h = self.size
        white = (230, 234, 240)
        amber = (255, 210, 90)
        grey = (176, 182, 192)
        green = (130, 224, 150)
        tname = AL.DOME_TYPES.get(rec.get("dtype", "home"),
                                  AL.DOME_TYPES["home"]).name
        sub = (rec["layout"] if rec.get("dtype", "home") == "home"
               else tname)
        lines = [(f"SERIAL #{rec.get('serial', '?')}  {rec['name']}", amber,
                  self.font_med),
                 (f"{tname}  ·  {sub}  ·  {rec['floor_area']:.0f} m²",
                  white, self.font_small),
                 (f"radius {rec['radius']:.1f} m  freq {rec['frequency']}V "
                  f" ·  {rec['cladding']}", grey, self.font_small),
                 ("", grey, self.font_tiny),
                 (f"material   {self.money(rec['material'])}", grey,
                  self.font_small),
                 (f"labor      {self.money(rec['labor_cost'])} "
                  f"({rec['labor_hours']:.0f} h)", grey, self.font_small),
                 (f"total cost {self.money(rec['total_cost'])}", grey,
                  self.font_small),
                 (f"sale price {self.money(rec['price'])}   "
                  f"({self.money(rec.get('monthly', 0))}/mo BHPH)", white,
                  self.font_small),
                 (f"MARGIN     {self.money(rec['margin'])}", green,
                  self.font_med),
                 ("", grey, self.font_tiny),
                 (f"solar {rec['solar_kw']:.1f} kW  ·  R-{rec['r_value']:.0f}",
                  grey, self.font_small),
                 (f"built {rec['created']}", grey, self.font_tiny),
                 (f"worker steps {rec['steps']:,}  ·  "
                  f"{rec['distance_m']:,.0f} m walked", grey, self.font_tiny),
                 (f"sold: {'YES' if self.selected_yard.sold else 'in yard'}",
                  green if not self.selected_yard.sold else grey,
                  self.font_tiny),
                 ("EXIT to close" if self.inspect else "click to close",
                  amber, self.font_tiny)]
        tex, tw, th = self.text_texture(
            ("plate", rec.get("serial"), self.selected_yard.sold,
             bool(self.inspect)), lines)
        if self.inspect is not None:
            px = w - tw - 20
            py = 70
        else:
            px = (w - tw) / 2
            py = (h - th) / 2
        self.draw_rect(px - 8, py - 8, tw + 16, th + 16,
                       (0.05, 0.07, 0.11, 0.95))
        self.draw_texture(tex, px, py, tw, th)
        if self.inspect is not None:
            self.draw_inspect_panel()

    def draw_inspect_panel(self):
        insp = self.inspect
        white = (230, 234, 240)
        amber = (255, 210, 90)
        grey = (170, 176, 186)
        green = (120, 220, 140)
        px, py = 14, 96
        row_h = 22
        pw = 300
        self.inspect_buttons = []
        n = len(insp.stages)
        panel_h = 34 + n * row_h + 96
        self.draw_rect(px - 6, py - 6, pw + 12, panel_h,
                       (0.04, 0.06, 0.10, 0.9))
        tex, tw, th = self.text_texture(
            ("insphdr",), [("LAYERS  (eye = show · box = solid)", white,
                            self.font_small)])
        self.draw_texture(tex, px, py, tw, th)
        yy = py + 26
        for s in insp.stages:
            L = insp.layers[s.key]
            # visibility toggle
            self.draw_rect(px, yy, 18, 18,
                           (0.2, 0.5, 0.25, 1) if L["visible"]
                           else (0.18, 0.2, 0.24, 1))
            self.inspect_buttons.append((f"vis:{s.key}", px, yy, 18, 18))
            # solid/transparent toggle
            self.draw_rect(px + 24, yy, 18, 18,
                           (0.5, 0.45, 0.2, 1) if L["solid"]
                           else (0.2, 0.35, 0.5, 1))
            self.inspect_buttons.append((f"solid:{s.key}", px + 24, yy, 18,
                                         18))
            col = white if L["visible"] else grey
            t2, w2, h2 = self.text_texture((f"lyr{s.key}", L["visible"],
                                            L["solid"]),
                                           [(s.title.title(), col,
                                             self.font_tiny)], pad=2)
            self.draw_texture(t2, px + 48, yy + 1, w2, h2)
            yy += row_h
        # controls
        yy += 6
        ctrls = [("insp_tour", "TOUR" if not self.tour else "TOUR*"),
                 ("insp_allon", "ALL ON"), ("insp_alloff", "ALL OFF")]
        cx = px
        for key, label in ctrls:
            self.draw_rect(cx, yy, 92, 26,
                           (0.2, 0.3, 0.2, 1) if (key == "insp_tour" and
                                                  self.tour)
                           else (0.12, 0.16, 0.22, 1))
            t2, w2, h2 = self.text_texture((f"ic{key}", label, self.tour),
                                           [(label, amber, self.font_small)],
                                           pad=3)
            self.draw_texture(t2, cx + 8, yy + 5, w2, h2)
            self.inspect_buttons.append((key, cx, yy, 92, 26))
            cx += 98
        yy += 32
        cx = px
        for key, label in [("insp_clad", "CLADDING »"),
                           ("insp_exit", "EXIT")]:
            wbtn = 140 if key == "insp_clad" else 90
            self.draw_rect(cx, yy, wbtn, 26,
                           (0.30, 0.16, 0.16, 1) if key == "insp_exit"
                           else (0.12, 0.16, 0.22, 1))
            t2, w2, h2 = self.text_texture(
                (f"ic{key}",), [(label, white, self.font_small)], pad=3)
            self.draw_texture(t2, cx + 8, yy + 5, w2, h2)
            self.inspect_buttons.append((key, cx, yy, wbtn, 26))
            cx += wbtn + 8

    def draw_configurator(self):
        w, h = self.size
        white = (230, 234, 240)
        amber = (255, 210, 90)
        grey = (176, 182, 192)
        cs = self.config_spec
        layout_line = (f"Layout    < {cs.layout} >" if cs.dtype == "home"
                       else "Layout    (n/a for this type)")
        lines = [("CONFIGURE NEXT DOME", amber, self.font_big),
                 ("", grey, self.font_small),
                 (f"Type      < {cs.type.name} >", (150, 220, 255),
                  self.font_med),
                 (f"  {cs.type.tagline}", grey, self.font_small),
                 (layout_line, white, self.font_med),
                 (f"Size      < {cs.radius:.1f} m  ({cs.floor_area:.0f} m²) >",
                  white, self.font_med),
                 (f"Frequency < {cs.frequency}V >", white, self.font_med),
                 (f"Cladding  < {cs.cladding} >", white, self.font_med),
                 ("", grey, self.font_small),
                 (f"projected sale {self.money(cs.sale_price)}   "
                  f"({self.money(cs.monthly_payment)}/mo)", amber,
                  self.font_med)]
        ck = (cs.dtype, cs.layout, cs.radius, cs.frequency, cs.cladding)
        tex, tw, th = self.text_texture(("config", ck), lines)
        px = (w - tw) / 2 - 20
        py = (h - th) / 2 - 40
        self.draw_rect(px - 14, py - 14, tw + 28, th + 90,
                       (0.05, 0.07, 0.11, 0.96))
        self.draw_texture(tex, px, py, tw, th)
        by = py + th + 6
        self.config_buttons = []
        for i, (key, label) in enumerate([("cfg_type", "Type"),
                                          ("cfg_layout", "Layout"),
                                          ("cfg_size", "Size"),
                                          ("cfg_freq", "Freq"),
                                          ("cfg_clad", "Cladding")]):
            bx = px + i * 108
            self.draw_rect(bx, by, 102, 28, (0.12, 0.16, 0.22, 0.95))
            t2, tw2, th2 = self.text_texture(
                (f"cfgb{key}", label), [(f"cycle {label}", white,
                                        self.font_tiny)], pad=3)
            self.draw_texture(t2, bx + 6, by + 6, tw2, th2)
            self.config_buttons.append((key, bx, by, 102, 28))
        # start / random / cancel
        by2 = by + 34
        for i, (key, label) in enumerate([("cfg_start", "START RUN"),
                                          ("cfg_random", "RANDOMIZE"),
                                          ("cfg_cancel", "CANCEL")]):
            bx = px + i * 150
            self.draw_rect(bx, by2, 144, 30,
                           (0.20, 0.30, 0.20, 0.95) if key == "cfg_start"
                           else (0.12, 0.16, 0.22, 0.95))
            t2, tw2, th2 = self.text_texture(
                (f"cfgm{key}", label), [(label, amber if key == "cfg_start"
                                         else white, self.font_small)], pad=4)
            self.draw_texture(t2, bx + (144 - tw2) / 2, by2 + 7, tw2, th2)
            self.config_buttons.append((key, bx, by2, 144, 30))

    # ===================================================================
    # Interaction
    # ===================================================================

    def hit(self, mx, my, rect):
        x, y, w, h = rect
        return x <= mx <= x + w and y <= my <= y + h

    def update_hover(self):
        if self.dragging or self.phase.kind != "work" or self.headless:
            self.hover_element = None
            return
        mx, my = self.mouse
        w, h = self.size
        dome_x = STATION_X[self.phase.station]
        best = None
        best_d = 26 ** 2
        # only inspect placed elements of the current dome
        for stage in self.run.stages:
            k = self.run.placed[stage.key]
            for el in self.run.cat.by_stage[stage.key][:k]:
                wp = (dome_x + el.centroid[0], el.centroid[1],
                      CARRIAGE_TOP + el.centroid[2])
                sp = project_point(self.mvp, wp, w, h)
                if sp is None:
                    continue
                d = (sp[0] - mx) ** 2 + (sp[1] - my) ** 2
                if d < best_d:
                    best_d = d
                    best = (el, sp)
        if best:
            self.hover_element, self.hover_screen = best
        else:
            self.hover_element = None

    def click_yard(self, mx, my):
        w, h = self.size
        best = None
        best_d = 60 ** 2
        for yd in self.yard:
            sp = project_point(self.mvp, (yd.x, yd.y, 2.0 * yd.scale), w, h)
            if sp is None:
                continue
            d = (sp[0] - mx) ** 2 + (sp[1] - my) ** 2
            if d < best_d:
                best_d = d
                best = yd
        return best

    def handle_click(self, mx, my):
        if self.configuring:
            for key, x, y, bw, bh in getattr(self, "config_buttons", []):
                if self.hit(mx, my, (x, y, bw, bh)):
                    self.config_action(key)
                    return
            return
        # inspection mode: layer toggles + controls
        if self.inspect is not None:
            for key, x, y, bw, bh in getattr(self, "inspect_buttons", []):
                if self.hit(mx, my, (x, y, bw, bh)):
                    self.inspect_action(key)
                    return
            # click another yard dome to inspect it instead
            yd = self.click_yard(mx, my)
            if yd is not None and yd is not self.selected_yard:
                self.enter_inspect(yd)
            return
        # control bar
        for key, x, y, bw, bh in getattr(self, "buttons_bar", []):
            if self.hit(mx, my, (x, y, bw, bh)):
                self.control_action(key)
                return
        # panel tabs
        for key, x, y, bw, bh in getattr(self, "buttons_panel", []):
            if self.hit(mx, my, (x, y, bw, bh)):
                self.panel = key.split(":")[1]
                return
        # sensitivity toggles on the P&L panel
        if self.panel == "pnl" and hasattr(self, "panel_body_rect"):
            if self.hit(mx, my, self.panel_body_rect):
                self.cycle_sensitivity()
                return
        # yard dome -> open advanced inspection
        yd = self.click_yard(mx, my)
        if yd is not None:
            self.enter_inspect(yd)

    def inspect_action(self, key):
        insp = self.inspect
        if key.startswith("vis:"):
            k = key[4:]
            insp.layers[k]["visible"] = not insp.layers[k]["visible"]
        elif key.startswith("solid:"):
            k = key[6:]
            insp.layers[k]["solid"] = not insp.layers[k]["solid"]
        elif key == "insp_tour":
            self.toggle_tour()
        elif key == "insp_allon":
            for v in insp.layers.values():
                v["visible"] = True
        elif key == "insp_alloff":
            for v in insp.layers.values():
                v["visible"] = False
        elif key == "insp_clad":
            names = [c[0] for c in AL.CLADDINGS]
            i = names.index(insp.spec.cladding) \
                if insp.spec.cladding in names else 0
            nm, col = AL.CLADDINGS[(i + 1) % len(names)]
            insp.spec.cladding, insp.spec.cladding_color = nm, col
            self.rebuild_inspect()
        elif key == "insp_exit":
            self.exit_inspect()

    def cycle_sensitivity(self):
        order = [1.0, 1.2, 0.85, 1.0]
        for kkey in ("lumber", "resin", "wage"):
            cur = self.sensitivity[kkey]
            nxt = order[(order.index(cur) + 1) % len(order)] \
                if cur in order else 1.0
            self.sensitivity[kkey] = nxt
            break  # cycle one factor per click, rotate which one
        # rotate which factor cycles next
        self._sens_keys = getattr(self, "_sens_keys",
                                  ["lumber", "resin", "wage"])
        self._sens_keys = self._sens_keys[1:] + self._sens_keys[:1]

    def set_crew(self, n):
        n = max(1, min(6, n))
        if n == self.workers_per_station:
            return
        self.workers_per_station = n
        self.crew = [Worker((0, 0)) for _ in range(n)]
        if self.phase.kind == "work":
            self._begin_station(self.phase.station)
        self.log(f"Crew set to {n} workers/station")

    def control_action(self, key):
        if key == "pause":
            self.paused = not self.paused
        elif key == "step":
            self.paused = True
            self.update(1.0 / 30.0 / max(0.001, self.speed) * self.speed)
        elif key == "follow":
            self.follow = not self.follow
            self.cinematic = False
        elif key == "cutaway":
            self.force_cutaway = not self.force_cutaway
        elif key == "xray":
            self.xray = not self.xray
        elif key == "cinematic":
            self.cinematic = not self.cinematic
        elif key == "snapshot":
            self.snapshot()
        elif key == "config":
            self.open_configurator()
        elif key == "auto":
            self.auto_run = not self.auto_run
        elif key in ("wminus", "wplus"):
            self.set_crew(self.workers_per_station
                          + (1 if key == "wplus" else -1))
        elif key == "sell":
            if self.sale is None:
                if not self.start_sale():
                    self.log("No unsold domes in the yard to sell")
        elif key in ("supply", "breakdown", "absence"):
            self.inject(key)
        elif key == "clear":
            self.db.clear()
            self.yard = []
            self.next_serial = 1
            self.log("Yard cleared")

    def open_configurator(self):
        self.configuring = True
        self.paused = True
        self.config_spec = random_spec(self.next_serial, self.rng)

    def config_action(self, key):
        cs = self.config_spec
        if key == "cfg_type":
            i = AL.DOME_TYPE_LIST.index(cs.dtype)
            nd = AL.DOME_TYPE_LIST[(i + 1) % len(AL.DOME_TYPE_LIST)]
            # regenerate within the new type's valid ranges, keep name
            new = random_spec(self.next_serial, self.rng, dtype=nd)
            new.name = cs.name
            new.cladding, new.cladding_color = cs.cladding, cs.cladding_color
            self.config_spec = new
        elif key == "cfg_layout" and cs.dtype == "home":
            i = AL.LAYOUTS.index(cs.layout)
            cs.layout = AL.LAYOUTS[(i + 1) % len(AL.LAYOUTS)]
        elif key == "cfg_size":
            lo, hi = cs.type.radius_range
            step = (hi - lo) / 4.0
            cs.radius = round(lo + ((cs.radius - lo + step) % (hi - lo)), 2)
        elif key == "cfg_freq":
            opts = cs.type.freq_choices
            uniq = list(dict.fromkeys(opts))
            cur = cs.frequency if cs.frequency in uniq else uniq[0]
            cs.frequency = uniq[(uniq.index(cur) + 1) % len(uniq)]
        elif key == "cfg_clad":
            names = [c[0] for c in AL.CLADDINGS]
            i = names.index(cs.cladding)
            nm, col = AL.CLADDINGS[(i + 1) % len(names)]
            cs.cladding, cs.cladding_color = nm, col
        elif key == "cfg_random":
            self.config_spec = random_spec(self.next_serial, self.rng)
        elif key == "cfg_start":
            self.configuring = False
            self.paused = False
            self.start_new_run(self.config_spec)
        elif key == "cfg_cancel":
            self.configuring = False
            self.paused = False

    def snapshot(self):
        os.makedirs("snapshots", exist_ok=True)
        data = self.fbo.read(components=3)
        surf = pygame.image.fromstring(data, self.size, "RGB", True)
        path = os.path.join("snapshots",
                            f"dome_{time.strftime('%H%M%S')}.png")
        pygame.image.save(surf, path)
        self.log(f"Snapshot saved: {path}")

    def set_speed_from_x(self, mx):
        x, _y, wdt, _h = self.slider_rect
        frac = max(0.0, min(1.0, (mx - x) / wdt))
        self.speed = round(2 ** (frac * 5 - 2), 2)
        self.speed = max(0.25, min(8.0, self.speed))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.configuring:
                        self.configuring = False
                        self.paused = False
                    elif self.inspect is not None:
                        self.exit_inspect()
                    elif self.selected_yard is not None:
                        self.selected_yard = None
                    else:
                        return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_LEFTBRACKET:
                    self.speed = max(0.25, self.speed * 0.5)
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.speed = min(8.0, self.speed * 2.0)
                elif event.key == pygame.K_f:
                    self.follow = not self.follow
                    self.cinematic = False
                elif event.key == pygame.K_c:
                    self.force_cutaway = not self.force_cutaway
                elif event.key == pygame.K_x:
                    self.xray = not self.xray
                elif event.key == pygame.K_r:
                    self.start_new_run()
                elif event.key == pygame.K_v:
                    self.cinematic = not self.cinematic
                elif event.key == pygame.K_MINUS:
                    self.set_crew(self.workers_per_station - 1)
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.set_crew(self.workers_per_station + 1)
            if event.type == pygame.MOUSEMOTION:
                self.mouse = event.pos
                if self.dragging:
                    self.cam_yaw -= event.rel[0] * 0.008
                    self.cam_pitch = max(math.radians(4), min(
                        math.radians(82),
                        self.cam_pitch + event.rel[1] * 0.006))
                if self.slider_drag:
                    self.set_speed_from_x(event.pos[0])
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse = event.pos
                if event.button == 1:
                    if self.hit(*event.pos, self.slider_rect):
                        self.slider_drag = True
                        self.set_speed_from_x(event.pos[0])
                    else:
                        # UI first; if nothing hit, treat as camera drag
                        before = (self.panel, self.paused, self.configuring,
                                  self.selected_yard, len(self.yard),
                                  self.cinematic, self.follow)
                        self.handle_click(*event.pos)
                        after = (self.panel, self.paused, self.configuring,
                                 self.selected_yard, len(self.yard),
                                 self.cinematic, self.follow)
                        if before == after and not self.configuring:
                            self.dragging = True
                elif event.button == 3:
                    self.dragging = True
                elif event.button == 4:
                    self.cam_dist = max(6.0, self.cam_dist * 0.88)
                elif event.button == 5:
                    self.cam_dist = min(90.0, self.cam_dist * 1.14)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    self.dragging = False
                    self.slider_drag = False
        if not self.follow and not self.cinematic:
            keys = pygame.key.get_pressed()
            pan = 16.0 / 60.0
            fx, fy = math.cos(self.cam_yaw) * pan, math.sin(self.cam_yaw) * pan
            if keys[pygame.K_w]:
                self.cam_target[0] -= fx
                self.cam_target[1] -= fy
            if keys[pygame.K_s]:
                self.cam_target[0] += fx
                self.cam_target[1] += fy
            if keys[pygame.K_a]:
                self.cam_target[0] -= fy
                self.cam_target[1] += fx
            if keys[pygame.K_d]:
                self.cam_target[0] += fy
                self.cam_target[1] -= fx
        return True

    def run_loop(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(0.05, clock.tick(60) / 1000.0)
            running = self.handle_events()
            if not self.paused:
                self.update(dt)
            self.update_hover()
            self.render()
            pygame.display.flip()
        pygame.quit()

    # -- headless shots --------------------------------------------------

    def render_shots(self, times, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        sim_t = 0.0
        step = 1.0 / 30.0
        for target in sorted(times):
            while sim_t < target:
                dt = min(step, target - sim_t)
                self.update(dt)
                sim_t += dt
            self.render()
            data = self.fbo.read(components=3)
            surf = pygame.image.fromstring(data, self.size, "RGB", True)
            path = os.path.join(out_dir, f"shot_{target:07.1f}s.png")
            pygame.image.save(surf, path)
            print(f"saved {path}")


# ===========================================================================
# Entry points
# ===========================================================================

def selftest():
    print("=== economics / model self-test ===")
    rng = random.Random(11)
    for i in range(3):
        spec = random_spec(i + 1, rng)
        cat, info = build_dome_catalog(spec)
        econ = unit_economics(cat, spec)
        tp = throughput(cat)
        pv = product_value(cat, spec)
        be = break_even(econ["margin"], econ["overhead"])
        assert econ["margin"] > 0, "margin must be positive"
        assert 0.10 < econ["margin_pct"] / 100 < 0.6, "margin out of range"
        print(f"#{i+1} {spec.name} {spec.layout} r{spec.radius} "
              f"f{spec.frequency} area {spec.floor_area:.0f}m2 "
              f"elems {len(cat.elements)}")
        print(f"    cost {econ['total_cost']:,.0f}  price {econ['price']:,.0f}"
              f"  margin {econ['margin']:,.0f} ({econ['margin_pct']:.0f}%)"
              f"  labor {econ['labor_hours']:.0f}h")
        print(f"    throughput single {tp['single_flow_per_year']:.0f}/yr "
              f"pipelined {tp['pipelined_per_year']:.0f}/yr  "
              f"break-even {be['units_to_recover_capex']:.0f} units")
        print(f"    solar {pv['solar_kw']:.1f}kW  R{pv['r_value']:.0f}  "
              f"autonomy {pv['autonomy_days']:.1f}d")
    print("=== DB round-trip ===")
    db = YardDB(":memory:")
    spec = random_spec(1, rng)
    cat, info = build_dome_catalog(spec)
    econ = unit_economics(cat, spec)
    pv = product_value(cat, spec)
    rec = {"name": spec.name, "radius": spec.radius,
           "frequency": spec.frequency, "layout": spec.layout,
           "cladding": spec.cladding, "floor_area": spec.floor_area,
           "material": econ["material"], "labor_cost": econ["labor_cost"],
           "overhead": econ["overhead"], "total_cost": econ["total_cost"],
           "price": econ["price"], "margin": econ["margin"],
           "labor_hours": econ["labor_hours"], "steps": 1234,
           "distance_m": 456.0, "solar_kw": pv["solar_kw"],
           "r_value": pv["r_value"], "cr": 0.2, "cg": 0.3, "cb": 0.4,
           "created": "2026-07-21 12:00"}
    sid = db.add(rec)
    got = db.all()
    assert len(got) == 1 and got[0]["serial"] == sid
    print(f"    stored serial {sid}, summary {db.summary()}")
    print("selftest OK")


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
        return
    if "--shots" in args:
        times = [float(v) for v in args[args.index("--shots") + 1].split(",")]
        out = os.environ.get("SHOT_DIR", "shots")
        app = AssemblyLineApp(headless=True, seed=42)
        app.speed = float(os.environ.get("SHOT_SPEED", "3.0"))
        if os.environ.get("SHOT_PANEL"):
            app.panel = os.environ["SHOT_PANEL"]
        app.render_shots(times, out)
        return
    app = AssemblyLineApp(windowed="--window" in args)
    app.run_loop()


if __name__ == "__main__":
    main()
