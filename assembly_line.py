"""
Dome Home Assembly Line — factory manufacturing simulation.

A manufactured-housing production line for dome homes. A transfer
carriage rolls a dome down the line, pausing under 15 numbered gantry
stations. Each station adds one build step, in real trailer-plant
order, until every component of the finished home is present:

     1  FLOOR FRAMING        wood floor framed into the base ring
     2  DOME SHELL FRAMING   geodesic frame raised from the ring up
     3  CENTER COLUMN        floor-to-apex utility column + crane anchor
     4  WATER LINES          hot/cold PEX + drains through the floor,
                             terminating centrally at the column
     5  POWER LINES          conduit through the floor to the column
     6  FIXTURES & OUTLETS   toilet/shower/sinks set, outlets mounted
     7  INSULATION           batts packed into every frame bay
     8  SHEETROCK            interior shell rocked
     9  OSB SHEATHING        exterior panel board over the dome
    10  WATER BARRIER        sill/water membrane over the OSB
    11  SHINGLE SCALES       plastic-scale mechanical water barrier
    12  FIBERGLASS           entire structure encased in fiberglass
    13  WATERTIGHT HATCH     sealed marine hatch door — zero windows
    14  INTERIOR FIT-OUT     complete kitchen, bathroom, bedroom
    15  SOLAR ARRAY          solar skin on the sun-facing band + QC

At the end of the line a gantry crane hooks the apex anchor, lifts the
finished dome off the carriage, and sets it on a big mechanical lazy
susan.  The turntable then rotates automatically to keep the solar band
tracking the sun as it arcs across the sky.

Install:
    py -3.12 -m pip install pygame moderngl numpy

Run:
    py -3.12 assembly_line.py            fullscreen
    py -3.12 assembly_line.py --window   windowed 1600x900
    py -3.12 assembly_line.py --selftest geometry/timeline sanity check
    py -3.12 assembly_line.py --shots 10,60,200   offscreen PNG renders

Controls:
    SPACE        pause / resume the line
    [  /  ]      slow down / speed up (x0.25 .. x16)
    mouse drag   orbit the camera            wheel   zoom
    F            toggle follow-the-dome / free camera (WASD pans)
    C            force interior cutaway view
    R            restart the line
    ESC          quit
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pygame

from dome_model import build_geodesic, normalize
from materials import (
    MAT_CANVAS,
    MAT_CONCRETE,
    MAT_DECK,
    MAT_EMISSIVE,
    MAT_GLASS,
    MAT_GRASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_SHEETING,
    MAT_SHINGLE,
    MAT_SOLAR,
    MAT_WOOD,
)
from mesh_builder import Mesh, MeshBuilder

# ---------------------------------------------------------------------------
# Line layout
# ---------------------------------------------------------------------------

DOME_RADIUS = 4.0
DOME_FREQ = 3
FLOOR_TOP = 0.35              # dome-local z of the finished deck surface
CARRIAGE_TOP = 0.62           # world z of the carriage deck (= platter top)
STATION_SPACING = 13.0
START_X = -16.0
TRAVEL_SECS = 3.5
RAIL_GAUGE = 2.2

SKY_COLOR = (0.55, 0.70, 0.86)


class StageDef:
    def __init__(self, key, title, desc, secs, color):
        self.key = key
        self.title = title
        self.desc = desc
        self.secs = secs
        self.color = color


STAGES = [
    StageDef("floor", "FLOOR FRAMING",
             "Wood floor built into the base ring: rim, joists, decking",
             7.0, (0.72, 0.55, 0.30)),
    StageDef("frame", "DOME SHELL FRAMING",
             "Geodesic timber frame raised from the base ring to the apex",
             11.0, (0.82, 0.62, 0.28)),
    StageDef("column", "CENTER UTILITY COLUMN",
             "Floor-to-apex service column + exterior crane anchor at the top",
             6.0, (0.60, 0.63, 0.68)),
    StageDef("water", "WATER LINES",
             "Hot / cold PEX and drains through the floor, all terminating "
             "centrally at the column", 7.0, (0.25, 0.50, 0.90)),
    StageDef("power", "POWER LINES",
             "Electrical conduit through the floor, terminating at the column",
             6.5, (0.95, 0.80, 0.20)),
    StageDef("fixtures", "FIXTURES & OUTLETS",
             "Plumbing fixtures set; outlets on the column and perimeter",
             8.0, (0.88, 0.90, 0.94)),
    StageDef("insulation", "INSULATION",
             "Insulation batts packed into every frame bay",
             7.5, (0.94, 0.52, 0.62)),
    StageDef("sheetrock", "SHEETROCK",
             "Interior shell sheetrocked", 7.5, (0.90, 0.90, 0.85)),
    StageDef("osb", "OSB SHEATHING",
             "OSB panel board covering the dome exterior",
             8.5, (0.84, 0.70, 0.44)),
    StageDef("wrap", "WATER BARRIER",
             "Sill / water membrane wrapped over the OSB",
             6.0, (0.60, 0.64, 0.72)),
    StageDef("shingles", "SHINGLE SCALES",
             "Plastic scale shingles — the mechanical water barrier",
             8.5, (0.20, 0.40, 0.45)),
    StageDef("fiberglass", "FIBERGLASS ENCASEMENT",
             "The entire structure encased in a watertight fiberglass shell",
             7.5, (0.62, 0.85, 0.90)),
    StageDef("hatch", "WATERTIGHT HATCH DOOR",
             "Sealed marine-style hatch — the home's only opening, zero "
             "windows", 6.0, (0.52, 0.56, 0.62)),
    StageDef("interior", "KITCHEN / BATH / BEDROOM",
             "Complete kitchen, bathroom and bedroom fit-out",
             10.0, (0.68, 0.50, 0.80)),
    StageDef("solar", "SOLAR ARRAY",
             "Solar skin applied to the sun-facing band + final QC",
             6.0, (0.15, 0.28, 0.60)),
]
STAGE_INDEX = {s.key: i for i, s in enumerate(STAGES)}

STATION_X = [i * STATION_SPACING for i in range(len(STAGES))]
PICKUP_X = STATION_X[-1] + 14.0
TURNTABLE_X = PICKUP_X + 14.0
PLATTER_TOP = 0.62
LIFT_Z = 4.4
SUN_CYCLE_SECS = 75.0

# ---------------------------------------------------------------------------
# Shaders (trimmed version of the dome_creator scene shader; the surface
# pattern is evaluated in dome-local space so skins don't swim as the
# dome travels down the line)
# ---------------------------------------------------------------------------

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
uniform float u_cut_z;
out vec4 frag_color;

float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float surface_pattern(int id, vec3 p, vec3 n) {
    if (id == 1) {                                     // shingle scales
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
    if (id == 2) {                                     // membrane sheeting
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
    if (id == 6) {                                     // concrete / OSB panels
        float speck = 0.95 + 0.08 * hash21(floor(p.xy * 6.0));
        float jx = 1.0 - smoothstep(0.0, 0.02,
            abs(fract(p.x / 2.4) - 0.5) * 2.4 - 1.16);
        float jy = 1.0 - smoothstep(0.0, 0.02,
            abs(fract(p.y / 2.4) - 0.5) * 2.4 - 1.16);
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
    if (id == 10) {                                    // insulation weave
        return 0.95 + 0.08 * sin(p.x * 60.0) * sin(p.y * 60.0)
             + 0.05 * sin(p.z * 45.0);
    }
    return 1.0;
}

void main() {
    if (v_local.z > u_cut_z) {
        discard;
    }
    vec3 normal = normalize(v_normal);
    if (!gl_FrontFacing) {
        normal = -normal;
    }
    vec3 light_direction = normalize(-u_light_direction);
    vec3 view_direction = normalize(u_camera_position - v_world);
    vec3 half_direction = normalize(light_direction + view_direction);
    float diffuse = max(dot(normal, light_direction), 0.0);
    float specular = pow(max(dot(normal, half_direction), 0.0), 48.0);
    float rim = pow(1.0 - max(dot(normal, view_direction), 0.0), 3.0);

    int mat_id = int(v_mat + 0.5);
    if (mat_id == 12) {
        frag_color = vec4(v_color.rgb * 1.3, v_color.a);
        return;
    }
    float pattern = surface_pattern(mat_id, v_local, normal);
    vec3 base = v_color.rgb * pattern;
    vec3 lit = base * (0.40 + 0.62 * diffuse);
    lit += vec3(1.0, 0.98, 0.92) * specular * (mat_id == 3 ? 0.9 : 0.30);
    lit += u_sky_color * rim * (mat_id == 3 ? 0.45 : 0.12);

    float alpha = v_color.a;
    if (mat_id == 3) {
        alpha = clamp(alpha + rim * 0.5, 0.0, 1.0);
    }
    float dist = length(u_camera_position - v_world);
    float fog = clamp((dist - 90.0) / 260.0, 0.0, 0.9);
    frag_color = vec4(mix(lit, u_sky_color, fog), alpha);
}
"""

OVERLAY_VS = """
#version 330
in vec2 in_pos;
uniform vec4 u_rect;      // x, y, w, h in pixels (origin bottom-left)
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


# ---------------------------------------------------------------------------
# Matrix helpers (row-major math convention; transposed at upload)
# ---------------------------------------------------------------------------

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


def mat_rot_z(angle):
    c, s = math.cos(angle), math.sin(angle)
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


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def add_box(b, center, size, color, alpha=1.0, mat_id=MAT_PLAIN, yaw=0.0):
    cx, cy, cz = center
    hx, hy, hz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    ca, sa = math.cos(yaw), math.sin(yaw)

    def pt(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z)

    def nv(x, y, z):
        return (x * ca - y * sa, x * sa + y * ca, z)

    b.quad(pt(-hx, -hy, hz), pt(hx, -hy, hz), pt(hx, hy, hz),
           pt(-hx, hy, hz), nv(0, 0, 1), color, alpha, mat_id)
    b.quad(pt(-hx, hy, -hz), pt(hx, hy, -hz), pt(hx, -hy, -hz),
           pt(-hx, -hy, -hz), nv(0, 0, -1), color, alpha, mat_id)
    b.quad(pt(hx, -hy, -hz), pt(hx, hy, -hz), pt(hx, hy, hz),
           pt(hx, -hy, hz), nv(1, 0, 0), color, alpha, mat_id)
    b.quad(pt(-hx, hy, -hz), pt(-hx, -hy, -hz), pt(-hx, -hy, hz),
           pt(-hx, hy, hz), nv(-1, 0, 0), color, alpha, mat_id)
    b.quad(pt(hx, hy, -hz), pt(-hx, hy, -hz), pt(-hx, hy, hz),
           pt(hx, hy, hz), nv(0, 1, 0), color, alpha, mat_id)
    b.quad(pt(-hx, -hy, -hz), pt(hx, -hy, -hz), pt(hx, -hy, hz),
           pt(-hx, -hy, hz), nv(0, -1, 0), color, alpha, mat_id)


def add_worker(b, x, y):
    b.cylinder((x - 0.09, y, 0.0), (x - 0.09, y, 0.46), 0.065, 6,
               (0.16, 0.18, 0.30))
    b.cylinder((x + 0.09, y, 0.0), (x + 0.09, y, 0.46), 0.065, 6,
               (0.16, 0.18, 0.30))
    b.cylinder((x, y, 0.44), (x, y, 1.06), 0.17, 8, (1.00, 0.45, 0.05))
    b.cylinder((x, y, 0.70), (x, y, 0.80), 0.175, 8, (0.88, 0.88, 0.25))
    b.sphere((x, y, 1.22), 0.13, (0.87, 0.66, 0.50), rings=5, sides=8)
    b.sphere((x, y, 1.30), 0.115, (0.95, 0.75, 0.10), rings=4, sides=8)


SEG_DEFS = {
    "a": (0.0, 1.0, True), "g": (0.0, 0.0, True), "d": (0.0, -1.0, True),
    "b": (0.5, 0.5, False), "c": (0.5, -0.5, False),
    "f": (-0.5, 0.5, False), "e": (-0.5, -0.5, False),
}
DIGIT_SEGS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgcde", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
SIGN_AMBER = (1.0, 0.62, 0.10)


def add_digit(b, x, y, z, ch, scale=1.0):
    # Sign faces -X; a viewer there sees world +y on their left, so the
    # digit's local horizontal axis is mirrored into -y.
    half_w, half_h = 0.22 * scale, 0.45 * scale
    for seg in DIGIT_SEGS[ch]:
        oy, oz, horizontal = SEG_DEFS[seg]
        sy = y - oy * 2.0 * half_w
        sz = z + oz * half_h
        if horizontal:
            add_box(b, (x, y, sz), (0.05, 2 * half_w, 0.07 * scale),
                    SIGN_AMBER, mat_id=MAT_EMISSIVE)
        else:
            add_box(b, (x, sy, sz), (0.05, 0.07 * scale, half_h),
                    SIGN_AMBER, mat_id=MAT_EMISSIVE)


def add_station_sign(b, x, number, color):
    # The sign sits on top of the gantry beam so the beam never occludes
    # the digits from the approach side.
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


# ---------------------------------------------------------------------------
# Dome catalog: the complete dome built once, with per-stage, per-element
# index ranges so the visible subset is just an index-buffer prefix write.
# ---------------------------------------------------------------------------

class Catalog:
    def __init__(self):
        self.b = MeshBuilder()
        self.stages: dict[str, list[tuple[int, int, int, int]]] = {
            s.key: [] for s in STAGES
        }
        self._o = 0
        self._t = 0

    def begin(self):
        self._o = len(self.b.opaque)
        self._t = len(self.b.transparent)

    def end(self, stage):
        self.stages[stage].append(
            (self._o, len(self.b.opaque), self._t, len(self.b.transparent)))


def polar(az_deg, r, z=0.0):
    a = math.radians(az_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def build_dome_catalog():
    """The full dome in dome-local space: origin at the carriage deck,
    +X down the line, hatch/solar band facing -Y."""
    geo = build_geodesic(DOME_FREQ)
    base_z = geo.base_z
    R = DOME_RADIUS
    floor_r = R * math.sqrt(max(0.0, 1.0 - base_z * base_z))
    apex_z = FLOOR_TOP + (1.0 - base_z) * R

    def spt(v, d=0.0):
        r = R + d
        return np.array([v[0] * r, v[1] * r, (v[2] - base_z) * r + FLOOR_TOP])

    cat = Catalog()
    b = cat.b

    # ---- Station 1: floor framing --------------------------------------
    rim_segments = 24
    for group in range(6):
        cat.begin()
        for i in range(group * 4, group * 4 + 4):
            a0 = 2 * math.pi * i / rim_segments
            a1 = 2 * math.pi * (i + 1) / rim_segments
            mid = (a0 + a1) * 0.5
            arc = floor_r * (a1 - a0)
            add_box(b, (floor_r * 0.985 * math.cos(mid),
                        floor_r * 0.985 * math.sin(mid), 0.15),
                    (arc * 1.02, 0.10, 0.30), (0.58, 0.44, 0.26),
                    mat_id=MAT_WOOD, yaw=mid + math.pi / 2)
        cat.end("floor")
    y = -floor_r + 0.45
    while y < floor_r - 0.35:
        half = math.sqrt(max(0.05, floor_r * floor_r - y * y))
        cat.begin()
        add_box(b, (0.0, y, 0.17), (2 * half - 0.28, 0.09, 0.26),
                (0.62, 0.48, 0.28), mat_id=MAT_WOOD)
        cat.end("floor")
        y += 0.55
    cat.begin()
    b.cylinder((0, 0, 0.30), (0, 0, FLOOR_TOP), floor_r + 0.04, 40,
               (0.72, 0.60, 0.42), mat_id=MAT_DECK)
    cat.end("floor")

    # ---- Station 2: dome shell framing ---------------------------------
    edges = sorted(
        geo.edges,
        key=lambda e: (round(min(geo.verts[e[0]][2], geo.verts[e[1]][2]), 3),
                       math.atan2(geo.verts[e[0]][1] + geo.verts[e[1]][1],
                                  geo.verts[e[0]][0] + geo.verts[e[1]][0])))
    wood = (0.55, 0.42, 0.26)
    for i, j in edges:
        cat.begin()
        b.cylinder(spt(geo.verts[i]), spt(geo.verts[j]), 0.052, 7, wood,
                   mat_id=MAT_WOOD)
        cat.end("frame")
    hub_order = sorted(range(len(geo.verts)),
                       key=lambda k: round(geo.verts[k][2], 3))
    for g in range(0, len(hub_order), 6):
        cat.begin()
        for k in hub_order[g:g + 6]:
            p = spt(geo.verts[k])
            n = normalize(np.array(geo.verts[k], dtype=np.float64))
            b.cylinder(p - n * 0.05, p + n * 0.07, 0.10, 8,
                       (0.55, 0.57, 0.62), mat_id=MAT_METAL)
        cat.end("frame")

    # ---- Station 3: center utility column + apex crane anchor ----------
    steel = (0.58, 0.61, 0.66)
    cat.begin()
    b.cylinder((0, 0, FLOOR_TOP - 0.02), (0, 0, FLOOR_TOP + 0.06), 0.34, 16,
               (0.40, 0.42, 0.46), mat_id=MAT_METAL)          # base plate
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, apex_z), 0.14, 12, steel,
               mat_id=MAT_METAL)                              # the column
    cat.end("column")
    cat.begin()   # service risers strapped to the column
    b.cylinder((0.16, 0.0, FLOOR_TOP), (0.16, 0.0, 2.3), 0.035, 6,
               (0.20, 0.40, 0.90))
    b.cylinder((-0.16, 0.0, FLOOR_TOP), (-0.16, 0.0, 2.3), 0.035, 6,
               (0.85, 0.20, 0.20))
    b.cylinder((0.0, 0.16, FLOOR_TOP), (0.0, 0.16, 2.3), 0.030, 6,
               (0.72, 0.72, 0.75), mat_id=MAT_METAL)
    cat.end("column")
    cat.begin()   # apex sleeve + crane anchor with lifting eye (outside)
    anchor_top = FLOOR_TOP + (1.0 - base_z) * (R + 0.24) + 0.14
    b.cylinder((0, 0, apex_z - 0.1), (0, 0, anchor_top), 0.09, 10,
               (0.45, 0.47, 0.52), mat_id=MAT_METAL)
    b.cylinder((0, 0, anchor_top), (0, 0, anchor_top + 0.06), 0.24, 12,
               (0.45, 0.47, 0.52), mat_id=MAT_METAL)
    eye_c = anchor_top + 0.28
    for i in range(12):
        a0 = 2 * math.pi * i / 12
        a1 = 2 * math.pi * (i + 1) / 12
        p0 = (0.17 * math.cos(a0), 0.0, eye_c + 0.17 * math.sin(a0))
        p1 = (0.17 * math.cos(a1), 0.0, eye_c + 0.17 * math.sin(a1))
        b.cylinder(p0, p1, 0.035, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    cat.end("column")

    # ---- Station 4: water lines ----------------------------------------
    hot = (0.85, 0.20, 0.20)
    cold = (0.20, 0.40, 0.90)
    drain = (0.28, 0.28, 0.32)
    cat.begin()
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, FLOOR_TOP + 0.12), 0.30, 14,
               (0.30, 0.42, 0.62), mat_id=MAT_METAL)          # manifold
    cat.end("water")

    def water_run(az, r_target, color, radius, offset_deg):
        a = az + offset_deg
        cat.begin()
        p0 = polar(a, 0.32, FLOOR_TOP + 0.045)
        p1 = polar(a, r_target, FLOOR_TOP + 0.045)
        b.cylinder(p0, p1, radius, 6, color)
        b.cylinder(p1, (p1[0], p1[1], FLOOR_TOP + 0.32), radius, 6, color)
        cat.end("water")

    for az, r_t, kinds in (
            (150, 2.70, "hcd"),      # kitchen sink
            (40, 2.45, "hc"),        # bathroom sink
            (60, 2.50, "cd"),        # toilet
            (82, 2.35, "hcd")):      # shower
        if "h" in kinds:
            water_run(az, r_t, hot, 0.022, -3.5)
        if "c" in kinds:
            water_run(az, r_t, cold, 0.022, 3.5)
        if "d" in kinds:
            water_run(az, r_t, drain, 0.048, 0.0)

    # ---- Station 5: power lines ----------------------------------------
    conduit = (0.72, 0.72, 0.75)
    cat.begin()
    add_box(b, (0.0, -0.22, FLOOR_TOP + 0.55), (0.26, 0.12, 0.40),
            (0.42, 0.44, 0.48), mat_id=MAT_METAL)             # junction box
    cat.end("power")
    for az in (0, 60, 120, 150, 180, 240, 300):
        cat.begin()
        p0 = polar(az + 1.5, 0.30, FLOOR_TOP + 0.030)
        p1 = polar(az + 1.5, 3.35, FLOOR_TOP + 0.030)
        b.cylinder(p0, p1, 0.026, 6, conduit, mat_id=MAT_METAL)
        b.cylinder(p1, (p1[0], p1[1], FLOOR_TOP + 0.40), 0.026, 6, conduit,
                   mat_id=MAT_METAL)
        cat.end("power")

    # ---- Station 6: fixtures & outlets ---------------------------------
    white = (0.95, 0.96, 0.97)
    cat.begin()   # toilet
    tx, ty, _ = polar(60, 2.50)
    add_box(b, (tx, ty, FLOOR_TOP + 0.21), (0.42, 0.38, 0.42), white,
            yaw=math.radians(60))
    add_box(b, (tx * 1.12, ty * 1.12, FLOOR_TOP + 0.55), (0.18, 0.44, 0.42),
            white, yaw=math.radians(60))
    b.cylinder((tx, ty, FLOOR_TOP + 0.42), (tx, ty, FLOOR_TOP + 0.46),
               0.20, 12, white)
    cat.end("fixtures")
    cat.begin()   # shower
    sx, sy, _ = polar(82, 2.35)
    add_box(b, (sx, sy, FLOOR_TOP + 0.05), (0.95, 0.95, 0.10),
            (0.80, 0.83, 0.86), yaw=math.radians(82))
    b.cylinder((sx, sy, FLOOR_TOP + 0.1), (sx, sy, FLOOR_TOP + 2.05),
               0.025, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    b.sphere((sx, sy, FLOOR_TOP + 2.02), 0.07, (0.70, 0.72, 0.76),
             rings=4, sides=8)
    b.cone((sx, sy, FLOOR_TOP + 1.98), (sx, sy, FLOOR_TOP + 1.86), 0.09, 10,
           (0.70, 0.72, 0.76))
    cat.end("fixtures")
    cat.begin()   # bathroom pedestal sink
    bx, by, _ = polar(40, 2.45)
    b.cylinder((bx, by, FLOOR_TOP), (bx, by, FLOOR_TOP + 0.76), 0.07, 8,
               white)
    b.cylinder((bx, by, FLOOR_TOP + 0.76), (bx, by, FLOOR_TOP + 0.88),
               0.20, 12, white)
    cat.end("fixtures")
    cat.begin()   # kitchen sink cabinet rough-in
    kx, ky, _ = polar(150, 2.70)
    add_box(b, (kx, ky, FLOOR_TOP + 0.44), (0.62, 0.55, 0.88),
            (0.62, 0.64, 0.68), mat_id=MAT_METAL, yaw=math.radians(150))
    b.cylinder((kx, ky, FLOOR_TOP + 0.88), (kx, ky, FLOOR_TOP + 1.12),
               0.020, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    cat.end("fixtures")
    for group in ((0, 60, 120), (180, 240, 300)):   # perimeter outlets
        cat.begin()
        for az in group:
            px, py, _ = polar(az + 1.5, 3.35)
            add_box(b, (px, py, FLOOR_TOP + 0.50), (0.09, 0.09, 0.30),
                    (0.30, 0.32, 0.36), yaw=math.radians(az))
            add_box(b, (px, py, FLOOR_TOP + 0.70), (0.10, 0.12, 0.16),
                    white, yaw=math.radians(az))
        cat.end("fixtures")
    cat.begin()   # column outlets + breaker panel + water taps
    for az in (45, 135, 225, 315):
        px, py, _ = polar(az, 0.17)
        add_box(b, (px, py, FLOOR_TOP + 0.55), (0.10, 0.13, 0.18), white,
                yaw=math.radians(az))
    bxp, byp, _ = polar(150, 0.18)
    add_box(b, (bxp, byp, FLOOR_TOP + 1.45), (0.08, 0.34, 0.50),
            (0.80, 0.82, 0.85), mat_id=MAT_METAL, yaw=math.radians(150))
    for dz, col in ((1.05, hot), (1.20, cold)):
        px, py, _ = polar(270, 0.16)
        b.cylinder((px, py, FLOOR_TOP + dz), (px * 1.9, py * 1.9,
                   FLOOR_TOP + dz), 0.022, 6, col)
        b.sphere((px * 1.9, py * 1.9, FLOOR_TOP + dz), 0.045, col,
                 rings=4, sides=8)
    cat.end("fixtures")

    # ---- Shell layers (stations 7-12, 15): per-face skins --------------
    faces = sorted(
        (tuple(f) for f in geo.faces),
        key=lambda f: (round(sum(geo.verts[i][2] for i in f) / 3.0, 3),
                       math.atan2(sum(geo.verts[i][1] for i in f),
                                  sum(geo.verts[i][0] for i in f))))

    def shell(stage, d, color, alpha=1.0, mat_id=MAT_PLAIN, shrink=1.0,
              face_filter=None):
        for f in faces:
            c_unit = np.mean([geo.verts[i] for i in f], axis=0)
            if face_filter and not face_filter(normalize(c_unit)):
                continue
            pts = [spt(geo.verts[i], d) for i in f]
            centroid = np.mean(pts, axis=0)
            pts = [centroid + (p - centroid) * shrink for p in pts]
            for p in pts:
                p[2] = max(p[2], FLOOR_TOP + 0.01)
            cat.begin()
            b.triangle(pts[0], pts[1], pts[2], color, alpha, mat_id)
            cat.end(stage)

    shell("insulation", -0.03, (0.93, 0.45, 0.55), mat_id=MAT_CANVAS,
          shrink=0.80)
    shell("sheetrock", -0.10, (0.92, 0.92, 0.88))
    shell("osb", 0.07, (0.80, 0.68, 0.42), mat_id=MAT_CONCRETE, shrink=0.985)
    shell("wrap", 0.105, (0.84, 0.85, 0.87), mat_id=MAT_SHEETING)
    shell("shingles", 0.14, (0.16, 0.34, 0.38), mat_id=MAT_SHINGLE)
    shell("fiberglass", 0.19, (0.72, 0.85, 0.88), alpha=0.30,
          mat_id=MAT_GLASS)
    cat.begin()   # fiberglass skirt sealing the floor edge
    b.cylinder((0, 0, 0.02), (0, 0, FLOOR_TOP + 0.12), floor_r + 0.20, 40,
               (0.72, 0.85, 0.88), alpha=0.30, mat_id=MAT_GLASS,
               cap_ends=False)
    cat.end("fiberglass")

    # ---- Station 13: watertight hatch door (zero windows) --------------
    rh = R + 0.19
    u = (1.25 - FLOOR_TOP) / rh + base_z
    horiz = math.sqrt(max(0.0, 1.0 - u * u))
    hpos = np.array([0.0, -horiz * rh, 1.25])
    n = normalize(np.array([0.0, -horiz, u]))
    right = normalize(np.cross(np.array([0.0, 0.0, 1.0]), n))
    up = normalize(np.cross(n, right))

    def hpt(a, scale=1.0, out=0.0):
        return (hpos + right * (0.56 * scale * math.cos(a))
                + up * (0.86 * scale * math.sin(a)) + n * out)

    cat.begin()   # hatch coaming ring
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 1.0, 0.05), hpt(a1, 1.0, 0.05), 0.05, 6,
                   (0.36, 0.39, 0.44), mat_id=MAT_METAL)
    cat.end("hatch")
    cat.begin()   # door leaf + gasket
    door = (0.62, 0.64, 0.68)
    center = hpos + n * 0.09
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.triangle(center, hpt(a0, 0.93, 0.09), hpt(a1, 0.93, 0.09), door,
                   mat_id=MAT_METAL, normal=n)
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 0.95, 0.07), hpt(a1, 0.95, 0.07), 0.022, 5,
                   (0.10, 0.10, 0.12))
    cat.end("hatch")
    for half in (0, 1):   # dog lugs
        cat.begin()
        for i in range(half * 3, half * 3 + 3):
            a = 2 * math.pi * i / 6 + 0.5
            p = hpt(a, 1.02, 0.07)
            b.sphere(p, 0.055, (0.25, 0.27, 0.30), rings=4, sides=8)
        cat.end("hatch")
    cat.begin()   # locking wheel
    wc = hpos + n * 0.20
    for i in range(12):
        a0 = 2 * math.pi * i / 12
        a1 = 2 * math.pi * (i + 1) / 12
        p0 = wc + right * (0.22 * math.cos(a0)) + up * (0.22 * math.sin(a0))
        p1 = wc + right * (0.22 * math.cos(a1)) + up * (0.22 * math.sin(a1))
        b.cylinder(p0, p1, 0.028, 6, (0.78, 0.80, 0.84), mat_id=MAT_METAL)
    for i in range(3):
        a = 2 * math.pi * i / 3
        p1 = wc + right * (0.21 * math.cos(a)) + up * (0.21 * math.sin(a))
        b.cylinder(wc, p1, 0.020, 5, (0.78, 0.80, 0.84), mat_id=MAT_METAL)
    b.sphere(wc, 0.05, (0.78, 0.80, 0.84), rings=4, sides=8)
    cat.end("hatch")
    cat.begin()   # hinges
    for dz in (0.30, -0.30):
        p = hpos + right * 0.62 + up * dz + n * 0.05
        add_box(b, tuple(p), (0.14, 0.10, 0.18), (0.30, 0.32, 0.36),
                mat_id=MAT_METAL)
    cat.end("hatch")

    # ---- Station 14: interior fit-out ----------------------------------
    wall = (0.90, 0.90, 0.86)

    def wall_run(az, segments):
        a = math.radians(az)
        cat.begin()
        for r0, r1 in segments:
            rc = (r0 + r1) * 0.5
            add_box(b, (rc * math.cos(a), rc * math.sin(a),
                        FLOOR_TOP + 1.10), (r1 - r0, 0.08, 2.20), wall,
                    yaw=a)
        cat.end("interior")

    wall_run(30, [(0.40, 0.95), (1.75, 2.90)])     # bathroom wall w/ door
    wall_run(90, [(0.40, 2.90)])                   # bathroom wall
    wall_run(300, [(0.40, 2.90)])                  # bedroom wall
    wall_run(0, [(0.40, 0.95), (1.75, 2.90)])      # bedroom wall w/ door

    cabinet = (0.45, 0.32, 0.20)
    counter_top = (0.85, 0.84, 0.80)
    for az in (140, 163):   # kitchen counters
        cat.begin()
        cx, cy, _ = polar(az, 3.00)
        yaw = math.radians(az + 90)
        add_box(b, (cx, cy, FLOOR_TOP + 0.45), (1.45, 0.62, 0.90), cabinet,
                mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (cx, cy, FLOOR_TOP + 0.925), (1.55, 0.68, 0.05),
                counter_top, yaw=yaw)
        cat.end("interior")
    cat.begin()   # kitchen sink + faucet in the counter
    kx, ky, _ = polar(150, 2.95)
    add_box(b, (kx, ky, FLOOR_TOP + 0.93), (0.50, 0.40, 0.06),
            (0.68, 0.70, 0.74), mat_id=MAT_METAL, yaw=math.radians(240))
    b.cylinder((kx, ky, FLOOR_TOP + 0.95), (kx, ky, FLOOR_TOP + 1.22),
               0.020, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    cat.end("interior")
    cat.begin()   # fridge
    fx, fy, _ = polar(126, 2.90)
    add_box(b, (fx, fy, FLOOR_TOP + 0.925), (0.75, 0.70, 1.85),
            (0.75, 0.78, 0.80), mat_id=MAT_METAL, yaw=math.radians(216))
    cat.end("interior")
    cat.begin()   # stove
    ox, oy, _ = polar(177, 2.95)
    add_box(b, (ox, oy, FLOOR_TOP + 0.45), (0.62, 0.62, 0.90),
            (0.22, 0.23, 0.26), mat_id=MAT_METAL, yaw=math.radians(267))
    for bi in range(4):
        ba = math.radians(267)
        dx = (-0.15 + 0.30 * (bi % 2))
        dy = (-0.15 + 0.30 * (bi // 2))
        wx = ox + dx * math.cos(ba) - dy * math.sin(ba)
        wy = oy + dx * math.sin(ba) + dy * math.cos(ba)
        b.cylinder((wx, wy, FLOOR_TOP + 0.90), (wx, wy, FLOOR_TOP + 0.915),
                   0.09, 10, (0.10, 0.10, 0.12))
    cat.end("interior")
    cat.begin()   # bed
    bx, by, _ = polar(332, 2.20)
    yaw = math.radians(332 + 90)
    add_box(b, (bx, by, FLOOR_TOP + 0.18), (1.45, 2.00, 0.32),
            (0.48, 0.36, 0.22), mat_id=MAT_WOOD, yaw=yaw)
    add_box(b, (bx, by, FLOOR_TOP + 0.45), (1.38, 1.92, 0.22),
            (0.93, 0.93, 0.95), yaw=yaw)
    hx = bx + 0.72 * math.cos(yaw + math.pi / 2)
    hy = by + 0.72 * math.sin(yaw + math.pi / 2)
    add_box(b, (hx, hy, FLOOR_TOP + 0.60), (1.20, 0.45, 0.12),
            (0.98, 0.98, 1.00), yaw=yaw)
    add_box(b, (bx - 0.30 * math.cos(yaw + math.pi / 2),
                by - 0.30 * math.sin(yaw + math.pi / 2), FLOOR_TOP + 0.58),
            (1.42, 1.15, 0.07), (0.50, 0.30, 0.55), yaw=yaw)
    cat.end("interior")
    cat.begin()   # wardrobe + nightstand + lamp
    wx, wy, _ = polar(297, 2.70)
    add_box(b, (wx, wy, FLOOR_TOP + 0.95), (1.20, 0.60, 1.90),
            (0.50, 0.38, 0.24), mat_id=MAT_WOOD, yaw=math.radians(297 + 90))
    nx, ny, _ = polar(352, 2.55)
    add_box(b, (nx, ny, FLOOR_TOP + 0.25), (0.45, 0.45, 0.50),
            (0.50, 0.38, 0.24), mat_id=MAT_WOOD)
    b.cylinder((nx, ny, FLOOR_TOP + 0.50), (nx, ny, FLOOR_TOP + 0.72),
               0.03, 6, (0.30, 0.32, 0.36))
    b.sphere((nx, ny, FLOOR_TOP + 0.80), 0.11, (1.00, 0.88, 0.55),
             mat_id=MAT_EMISSIVE, rings=4, sides=8)
    cat.end("interior")
    cat.begin()   # shower glass
    gx, gy, _ = polar(82, 2.35)
    ga = math.radians(82)
    for side in (-1, 1):
        px = gx + 0.48 * side * math.cos(ga + math.pi / 2)
        py = gy + 0.48 * side * math.sin(ga + math.pi / 2)
        add_box(b, (px, py, FLOOR_TOP + 1.05), (0.95, 0.03, 1.90),
                (0.75, 0.88, 0.90), alpha=0.30, mat_id=MAT_GLASS, yaw=ga)
    cat.end("interior")
    cat.begin()   # small dining table + stools
    dx, dy, _ = polar(218, 1.95)
    b.cylinder((dx, dy, FLOOR_TOP), (dx, dy, FLOOR_TOP + 0.72), 0.05, 8,
               (0.35, 0.37, 0.40), mat_id=MAT_METAL)
    b.cylinder((dx, dy, FLOOR_TOP + 0.72), (dx, dy, FLOOR_TOP + 0.77),
               0.50, 16, (0.60, 0.46, 0.28), mat_id=MAT_WOOD)
    for sa in (150, 290):
        sx2, sy2, _ = polar(sa, 0.75)
        b.cylinder((dx + sx2, dy + sy2, FLOOR_TOP),
                   (dx + sx2, dy + sy2, FLOOR_TOP + 0.45), 0.16, 10,
                   (0.45, 0.34, 0.22), mat_id=MAT_WOOD)
    cat.end("interior")

    # ---- Station 15: solar array ---------------------------------------
    shell("solar", 0.23, (0.10, 0.15, 0.32), mat_id=MAT_SOLAR, shrink=0.86,
          face_filter=lambda c: (-c[1]) > 0.40 and 0.10 < c[2] < 0.74)

    info = {
        "floor_r": floor_r,
        "apex_z": apex_z,
        "anchor_top": anchor_top + 0.45,
        "base_z": base_z,
    }
    return cat, info


# ---------------------------------------------------------------------------
# Factory environment (static) and dynamic props
# ---------------------------------------------------------------------------

def build_environment():
    b = MeshBuilder()
    b.disc((0.0, 0.0, -0.05), 320.0, 48, (0.30, 0.36, 0.26),
           mat_id=MAT_GRASS)
    add_box(b, ((START_X + TURNTABLE_X) / 2, 0.0, -0.09),
            (TURNTABLE_X - START_X + 40.0, 26.0, 0.18), (0.55, 0.55, 0.52),
            mat_id=MAT_CONCRETE)

    # Rails + ties from the line start to the crane pickup point.
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
        add_worker(b, x - 1.9, -3.6)
        add_worker(b, x + 1.6, 3.4)
        add_pallet(b, x + 4.2, -4.8, stage.color)

    # Gantry crane (static portal; the bridge/trolley are dynamic).
    crane_yellow = (0.95, 0.70, 0.12)
    for cx in (PICKUP_X - 3.5, TURNTABLE_X + 5.5):
        for sy in (-7.4, 7.4):
            add_box(b, (cx, sy, 5.5), (0.8, 0.8, 11.0), crane_yellow,
                    mat_id=MAT_METAL)
    for sy in (-7.4, 7.4):
        add_box(b, ((PICKUP_X - 3.5 + TURNTABLE_X + 5.5) / 2, sy, 11.3),
                (TURNTABLE_X - PICKUP_X + 12.0, 0.9, 0.6), crane_yellow,
                mat_id=MAT_METAL)

    # Turntable plinth + drive unit (the platter itself is dynamic).
    b.cylinder((TURNTABLE_X, 0.0, 0.0), (TURNTABLE_X, 0.0, 0.25), 7.0, 40,
               (0.48, 0.48, 0.46), mat_id=MAT_CONCRETE)
    add_box(b, (TURNTABLE_X + 7.4, 1.0, 0.65), (1.5, 1.1, 1.3),
            (0.85, 0.65, 0.10), mat_id=MAT_METAL)
    b.cylinder((TURNTABLE_X + 6.65, 1.0, 0.28),
               (TURNTABLE_X + 6.65, 1.0, 0.62), 0.35, 12,
               (0.30, 0.32, 0.36), mat_id=MAT_METAL)
    add_box(b, (TURNTABLE_X + 7.4, -1.6, 0.75), (0.9, 0.7, 1.5),
            (0.65, 0.68, 0.72), mat_id=MAT_METAL)

    # Perimeter trees for depth.
    for i in range(16):
        a = 2 * math.pi * i / 16 + 0.35
        r = 120.0 + (i % 4) * 22.0
        tx = (START_X + TURNTABLE_X) / 2 + r * math.cos(a) * 1.6
        ty = r * math.sin(a) * 0.55
        if abs(ty) < 16:
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
    b.cylinder((0, 0, 0.55), (0, 0, CARRIAGE_TOP), 4.25, 36,
               (0.42, 0.44, 0.48), mat_id=MAT_METAL)
    b.cylinder((0, 0, CARRIAGE_TOP - 0.015), (0, 0, CARRIAGE_TOP), 4.27, 36,
               (0.90, 0.72, 0.10), cap_ends=False)
    for ax in (-2.4, -0.8, 0.8, 2.4):
        for sy in (-RAIL_GAUGE, RAIL_GAUGE):
            b.cylinder((ax, sy - 0.13, 0.31), (ax, sy + 0.13, 0.31), 0.16,
                       10, (0.18, 0.19, 0.22), mat_id=MAT_METAL)
    return b.build()


def build_platter():
    """Big mechanical lazy susan platter, local origin at plinth top."""
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
    crane_yellow = (0.95, 0.70, 0.12)
    add_box(b, (0.0, 0.0, 10.85), (1.0, 16.2, 0.7), crane_yellow,
            mat_id=MAT_METAL)
    for sy in (-7.4, 7.4):
        add_box(b, (0.0, sy, 11.15), (1.6, 1.2, 0.5), (0.30, 0.32, 0.36),
                mat_id=MAT_METAL)
    add_box(b, (0.0, 0.0, 10.30), (1.4, 1.6, 0.5), (0.30, 0.32, 0.36),
            mat_id=MAT_METAL)
    b.cylinder((0.0, -0.5, 10.10), (0.0, 0.5, 10.10), 0.18, 10,
               (0.55, 0.57, 0.62), mat_id=MAT_METAL)
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
    b.cone((0.0, 0.0, -0.60), (0.12, 0.0, -0.86), 0.09, 8,
           (0.45, 0.47, 0.52))
    return b.build()


def build_sun():
    b = MeshBuilder()
    b.sphere((0, 0, 0), 5.0, (1.0, 0.95, 0.72), mat_id=MAT_EMISSIVE,
             rings=8, sides=12)
    return b.build()


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class Phase:
    def __init__(self, kind, dur, station=-1, x0=0.0, x1=0.0):
        self.kind = kind
        self.dur = dur
        self.station = station
        self.x0 = x0
        self.x1 = x1


def build_phases():
    phases = []
    x_prev = START_X
    for i, stage in enumerate(STAGES):
        phases.append(Phase("travel", TRAVEL_SECS, i, x_prev, STATION_X[i]))
        phases.append(Phase("work", stage.secs, i))
        x_prev = STATION_X[i]
    phases.append(Phase("tocrane", 4.0, -1, x_prev, PICKUP_X))
    phases.append(Phase("hook", 3.0))
    phases.append(Phase("lift", 4.0))
    phases.append(Phase("carry", 6.0, -1, PICKUP_X, TURNTABLE_X))
    phases.append(Phase("lower", 4.0))
    phases.append(Phase("unhook", 3.0))
    phases.append(Phase("track", math.inf))
    return phases


# ---------------------------------------------------------------------------
# GPU helpers
# ---------------------------------------------------------------------------

class GpuMesh:
    """Static mesh with its own VAOs, drawn with a model matrix."""

    def __init__(self, ctx, program, mesh: Mesh):
        self.ctx = ctx
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
    """The dome catalog on the GPU; visibility is an index-buffer write."""

    def __init__(self, ctx, program, cat: Catalog):
        mesh = cat.b.build()
        self.full_opaque = mesh.opaque
        self.full_transparent = mesh.transparent
        self.stages = cat.stages
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

    def update(self, progress: dict[str, float]):
        sig = []
        for stage in STAGES:
            els = self.stages[stage.key]
            p = progress.get(stage.key, 0.0)
            if p <= 0.0 or not els:
                k = 0
            else:
                k = min(len(els), max(1, math.ceil(p * len(els) - 1e-9)))
            sig.append(k)
        sig = tuple(sig)
        if sig == self.signature:
            return
        self.signature = sig
        chunks_o, chunks_t = [], []
        for stage, k in zip(STAGES, sig):
            for (o0, o1, t0, t1) in self.stages[stage.key][:k]:
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


# ---------------------------------------------------------------------------
# The application
# ---------------------------------------------------------------------------

class AssemblyLineApp:
    def __init__(self, headless=False, windowed=False, size=(1600, 900)):
        self.headless = headless
        pygame.init()
        if headless:
            import moderngl
            self.size = size
            self.ctx = moderngl.create_standalone_context()
            self.color_tex = self.ctx.texture(size, components=3)
            self.depth_rb = self.ctx.depth_renderbuffer(size)
            self.fbo = self.ctx.framebuffer([self.color_tex], self.depth_rb)
        else:
            import moderngl
            flags = pygame.OPENGL | pygame.DOUBLEBUF
            if windowed:
                pygame.display.set_mode(size, flags)
            else:
                pygame.display.set_mode((0, 0), flags | pygame.FULLSCREEN)
            pygame.display.set_caption("Dome Home Assembly Line")
            self.size = pygame.display.get_window_size()
            self.ctx = moderngl.create_context()
            self.fbo = self.ctx.screen
        self.moderngl = __import__("moderngl")
        ctx = self.ctx

        self.scene_prog = ctx.program(vertex_shader=SCENE_VS,
                                      fragment_shader=SCENE_FS)
        self.overlay_prog = ctx.program(vertex_shader=OVERLAY_VS,
                                        fragment_shader=OVERLAY_FS)
        quad = np.array([0, 0, 1, 0, 0, 1, 1, 1], dtype=np.float32)
        self.quad_vbo = ctx.buffer(quad.tobytes())
        self.quad_vao = ctx.vertex_array(
            self.overlay_prog, [(self.quad_vbo, "2f", "in_pos")])

        cat, self.dome_info = build_dome_catalog()
        self.dome = DomeGpu(ctx, self.scene_prog, cat)
        self.env = GpuMesh(ctx, self.scene_prog, build_environment())
        self.carriage = GpuMesh(ctx, self.scene_prog, build_carriage())
        self.platter = GpuMesh(ctx, self.scene_prog, build_platter())
        self.bridge = GpuMesh(ctx, self.scene_prog, build_bridge())
        self.cable = GpuMesh(ctx, self.scene_prog, build_cable_unit())
        self.hook = GpuMesh(ctx, self.scene_prog, build_hook())
        self.sun = GpuMesh(ctx, self.scene_prog, build_sun())

        self.font_big = pygame.font.SysFont("consolas", 30, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 17)
        self.text_cache: dict = {}

        self.phases = build_phases()
        self.reset()

        self.speed = 1.0
        self.paused = False
        self.follow = True
        self.force_cutaway = False
        self.cam_yaw = math.radians(-115.0)
        self.cam_pitch = math.radians(16.0)
        self.cam_dist = 17.0
        self.cam_target = np.array([START_X, 0.0, 2.5], dtype=np.float32)
        self.dragging = False

    # -- simulation state ------------------------------------------------

    def reset(self):
        self.phase_idx = 0
        self.phase_t = 0.0
        self.track_t = 0.0
        self.platter_yaw = 0.0
        self.dome.signature = None

    @property
    def phase(self) -> Phase:
        return self.phases[self.phase_idx]

    def advance(self, dt):
        self.phase_t += dt
        while (self.phase_idx < len(self.phases) - 1
               and self.phase_t >= self.phase.dur):
            self.phase_t -= self.phase.dur
            self.phase_idx += 1
        if self.phase.kind == "track":
            self.track_t = self.phase_t

    def stage_progress(self) -> dict[str, float]:
        progress = {}
        for idx in range(self.phase_idx):
            ph = self.phases[idx]
            if ph.kind == "work":
                progress[STAGES[ph.station].key] = 1.0
        ph = self.phase
        if ph.kind == "work":
            progress[STAGES[ph.station].key] = min(
                1.0, self.phase_t / max(ph.dur, 1e-6))
        return progress

    def sun_state(self):
        """(sun_dir unit vector scene->sun, tracking bool)."""
        if self.phase.kind == "track":
            frac = (self.track_t % SUN_CYCLE_SECS) / SUN_CYCLE_SECS
            az = math.radians(-170.0 + 160.0 * frac)
            el = math.radians(14.0 + 54.0 * math.sin(math.pi * frac))
            return np.array([math.cos(az) * math.cos(el),
                             math.sin(az) * math.cos(el),
                             math.sin(el)]), True, az, el
        d = normalize(np.array([0.35, -0.45, 0.82]))
        return d, False, math.atan2(d[1], d[0]), math.asin(d[2])

    def dome_pose(self):
        """(x, y, z, yaw, on_carriage, hook_z or None, bridge_x)."""
        ph = self.phase
        t = smoothstep(self.phase_t / ph.dur) if math.isfinite(ph.dur) \
            else 0.0
        anchor = self.dome_info["anchor_top"]
        if ph.kind in ("travel", "work", "tocrane"):
            if ph.kind == "work":
                x = STATION_X[ph.station]
            else:
                x = ph.x0 + (ph.x1 - ph.x0) * t
            return x, 0.0, CARRIAGE_TOP, 0.0, True, None, PICKUP_X
        if ph.kind == "hook":
            hz = CARRIAGE_TOP + anchor + 0.15
            cable_z = 9.6 - (9.6 - hz) * t
            return PICKUP_X, 0.0, CARRIAGE_TOP, 0.0, True, cable_z, PICKUP_X
        if ph.kind == "lift":
            z = CARRIAGE_TOP + (LIFT_Z - CARRIAGE_TOP) * t
            return (PICKUP_X, 0.0, z, 0.0, False,
                    z + anchor + 0.15, PICKUP_X)
        if ph.kind == "carry":
            x = ph.x0 + (ph.x1 - ph.x0) * t
            return x, 0.0, LIFT_Z, 0.0, False, LIFT_Z + anchor + 0.15, x
        if ph.kind == "lower":
            z = LIFT_Z + (PLATTER_TOP - LIFT_Z) * t
            return (TURNTABLE_X, 0.0, z, 0.0, False,
                    z + anchor + 0.15, TURNTABLE_X)
        if ph.kind == "unhook":
            hz = PLATTER_TOP + anchor + 0.15
            cable_z = hz + (9.6 - hz) * t
            return (TURNTABLE_X, 0.0, PLATTER_TOP, self.platter_yaw, False,
                    cable_z, TURNTABLE_X)
        # track
        return (TURNTABLE_X, 0.0, PLATTER_TOP, self.platter_yaw, False,
                None, TURNTABLE_X)

    def update(self, dt):
        if not self.paused:
            self.advance(dt * self.speed)
            sun_dir, tracking, az, _el = self.sun_state()
            if tracking:
                target_yaw = az + math.pi / 2.0
                delta = target_yaw - self.platter_yaw
                max_step = 0.5 * dt * self.speed
                self.platter_yaw += max(-max_step, min(max_step, delta))
        self.dome.update(self.stage_progress())

        x, y, z, _yaw, _oc, _hz, _bx = self.dome_pose()
        goal = np.array([x, y, z + 2.6], dtype=np.float32)
        if self.follow:
            blend = min(1.0, dt * 2.5)
            self.cam_target = self.cam_target + (goal - self.cam_target) \
                * blend

    # -- rendering -------------------------------------------------------

    def upload_model(self, m):
        self.scene_prog["u_model"].write(
            np.ascontiguousarray(m.T.astype(np.float32)).tobytes())

    def draw_gpu(self, gm: GpuMesh, model=None, transparent_pass=False):
        self.upload_model(model if model is not None
                          else np.eye(4, dtype=np.float32))
        vao = gm.transparent_vao if transparent_pass else gm.opaque_vao
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
        proj = perspective(58.0, w / h, 0.1, 600.0)
        view = look_at(eye, self.cam_target)
        mvp = proj @ view
        prog = self.scene_prog
        prog["u_mvp"].write(np.ascontiguousarray(mvp.T).tobytes())
        prog["u_camera_position"].value = tuple(map(float, eye))
        sun_dir, tracking, _az, _el = self.sun_state()
        prog["u_light_direction"].value = tuple(map(float, -sun_dir))
        prog["u_sky_color"].value = SKY_COLOR

        x, y, z, yaw, on_carriage, hook_z, bridge_x = self.dome_pose()
        dome_model = (mat_translate(x, y, z) @ mat_rot_z(yaw))

        interior_station = (self.phase.kind == "work"
                            and STAGES[self.phase.station].key == "interior")
        cutaway = self.force_cutaway or interior_station
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
            self.draw_gpu(self.cable,
                          mat_translate(bridge_x, 0, 10.0)
                          @ mat_scale(0.04, 0.04, length))
            self.draw_gpu(self.hook, mat_translate(bridge_x, 0, hook_z))
        sun_pos = self.cam_target + sun_dir.astype(np.float32) * 260.0
        self.draw_gpu(self.sun, mat_translate(*sun_pos))

        prog["u_cut_z"].value = dome_cut
        self.upload_model(dome_model)
        if self.dome.opaque_count:
            self.dome.opaque_vao.render(mgl.TRIANGLES,
                                        vertices=self.dome.opaque_count)
        ctx.depth_mask = False
        if self.dome.transparent_count:
            self.dome.transparent_vao.render(
                mgl.TRIANGLES, vertices=self.dome.transparent_count)
        prog["u_cut_z"].value = 1e9
        self.draw_gpu(self.env, transparent_pass=True)
        ctx.depth_mask = True

        self.draw_hud()

    # -- HUD -------------------------------------------------------------

    def text_texture(self, key, lines):
        """lines: list of (text, rgb, font). Cached by key."""
        cached = self.text_cache.get(key)
        if cached is not None and cached[0] == lines:
            return cached[1], cached[2], cached[3]
        if cached is not None:
            cached[1].release()
        surfs = [font.render(text, True, color)
                 for text, color, font in lines if text]
        pad = 8
        width = max(s.get_width() for s in surfs) + pad * 2
        height = sum(s.get_height() + 4 for s in surfs) + pad * 2
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        yy = pad
        for s in surfs:
            surface.blit(s, (pad, yy))
            yy += s.get_height() + 4
        raw = pygame.image.tostring(surface, "RGBA", True)
        tex = self.ctx.texture((width, height), 4, raw)
        tex.filter = (self.moderngl.LINEAR, self.moderngl.LINEAR)
        self.text_cache[key] = (lines, tex, width, height)
        return tex, width, height

    def draw_rect(self, x, y_top, w, h, color):
        """Solid rect; x/y_top in top-left origin pixels."""
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
        self.overlay_prog["u_color"].value = (1.0, 1.0, 1.0, alpha)
        self.overlay_prog["u_use_tex"].value = 1.0
        self.quad_vao.render(self.moderngl.TRIANGLE_STRIP)

    def banner_lines(self):
        ph = self.phase
        n = len(STAGES)
        if ph.kind == "travel":
            stage = STAGES[ph.station]
            return [(f"MOVING TO STATION {ph.station + 1}/{n} — "
                     f"{stage.title}", (255, 210, 90), self.font_big)]
        if ph.kind == "work":
            stage = STAGES[ph.station]
            return [(f"STATION {ph.station + 1}/{n} — {stage.title}",
                     (255, 210, 90), self.font_big),
                    (stage.desc, (215, 220, 226), self.font_med)]
        if ph.kind == "tocrane":
            return [("LINE COMPLETE — ROLLING TO CRANE PICKUP",
                     (255, 210, 90), self.font_big)]
        if ph.kind in ("hook", "lift", "carry", "lower", "unhook"):
            label = {"hook": "HOOKING THE APEX ANCHOR",
                     "lift": "LIFTING OFF THE CARRIAGE",
                     "carry": "CARRYING TO THE TURNTABLE",
                     "lower": "SETTING DOWN ON THE LAZY SUSAN",
                     "unhook": "RELEASING THE HOOK"}[ph.kind]
            return [(f"CRANE TRANSFER — {label}", (255, 210, 90),
                     self.font_big),
                    ("Lifting by the apex anchor fitting",
                     (215, 220, 226), self.font_med)]
        _d, _t, az, el = self.sun_state()
        return [("SUN-TRACKING TURNTABLE — HOME COMPLETE",
                 (140, 235, 150), self.font_big),
                (f"Lazy susan az {math.degrees(self.platter_yaw):5.1f}°  ·  "
                 f"sun az {math.degrees(az):6.1f}°  el "
                 f"{math.degrees(el):4.1f}°  ·  solar band facing the sun",
                 (215, 220, 226), self.font_med)]

    def checklist_lines(self):
        progress = self.stage_progress()
        ph = self.phase
        active_station = ph.station if ph.kind in ("travel", "work") else -1
        lines = [("BUILD SEQUENCE", (235, 238, 242), self.font_med)]
        for i, stage in enumerate(STAGES):
            done = progress.get(stage.key, 0.0) >= 1.0
            if done:
                marker, color = "[x]", (120, 220, 140)
            elif i == active_station:
                marker, color = " > ", (255, 210, 90)
            else:
                marker, color = "[ ]", (150, 155, 165)
            lines.append((f"{marker} {i + 1:>2}  {stage.title}", color,
                          self.font_small))
        crane_kinds = ("tocrane", "hook", "lift", "carry", "lower", "unhook")
        if ph.kind == "track":
            lines.append(("[x]     CRANE TO TURNTABLE", (120, 220, 140),
                          self.font_small))
            lines.append((" >      SUN TRACKING", (255, 210, 90),
                          self.font_small))
        elif ph.kind in crane_kinds:
            lines.append((" >      CRANE TO TURNTABLE", (255, 210, 90),
                          self.font_small))
            lines.append(("[ ]     SUN TRACKING", (150, 155, 165),
                          self.font_small))
        else:
            lines.append(("[ ]     CRANE TO TURNTABLE", (150, 155, 165),
                          self.font_small))
            lines.append(("[ ]     SUN TRACKING", (150, 155, 165),
                          self.font_small))
        return lines

    def draw_hud(self):
        ctx = self.ctx
        ctx.disable(self.moderngl.DEPTH_TEST)
        w, _h = self.size

        if self.phase.kind == "track":
            key_tick = int(self.phase_t * 2)
        else:
            key_tick = 0
        tex, tw, th = self.text_texture(("banner", self.phase_idx, key_tick),
                                        self.banner_lines())
        self.draw_rect((w - tw) / 2 - 8, 8, tw + 16, th + 12,
                       (0.03, 0.05, 0.08, 0.62))
        self.draw_texture(tex, (w - tw) / 2, 14, tw, th)

        ph = self.phase
        if math.isfinite(ph.dur):
            frac = max(0.0, min(1.0, self.phase_t / ph.dur))
            bar_w = 420
            bx = (w - bar_w) / 2
            by = th + 26
            color = (STAGES[ph.station].color + (0.9,)) \
                if ph.kind == "work" else (0.9, 0.9, 0.9, 0.9)
            self.draw_rect(bx, by, bar_w, 9, (1, 1, 1, 0.18))
            self.draw_rect(bx, by, bar_w * frac, 9, color)

        tex, tw, th = self.text_texture("checklist", self.checklist_lines())
        self.draw_rect(10, 90, tw + 12, th + 10, (0.03, 0.05, 0.08, 0.55))
        self.draw_texture(tex, 16, 95, tw, th)

        controls = ("SPACE pause · [ / ] speed · drag orbit · wheel zoom · "
                    "F follow · C cutaway · R restart · ESC quit")
        tex, tw, th = self.text_texture(
            "controls", [(controls, (185, 190, 198), self.font_small)])
        self.draw_texture(tex, (w - tw) / 2, self.size[1] - th - 8, tw, th)

        status = f"speed x{self.speed:g}" + ("  ·  PAUSED" if self.paused
                                             else "")
        tex, tw, th = self.text_texture(
            ("status", self.speed, self.paused),
            [(status, (255, 210, 90) if self.paused else (185, 190, 198),
              self.font_small)])
        self.draw_texture(tex, w - tw - 14, 12, tw, th)
        ctx.enable(self.moderngl.DEPTH_TEST)

    # -- main loop -------------------------------------------------------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_LEFTBRACKET:
                    self.speed = max(0.25, self.speed * 0.5)
                if event.key == pygame.K_RIGHTBRACKET:
                    self.speed = min(16.0, self.speed * 2.0)
                if event.key == pygame.K_r:
                    self.reset()
                if event.key == pygame.K_f:
                    self.follow = not self.follow
                if event.key == pygame.K_c:
                    self.force_cutaway = not self.force_cutaway
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):
                    self.dragging = True
                if event.button == 4:
                    self.cam_dist = max(6.0, self.cam_dist * 0.88)
                if event.button == 5:
                    self.cam_dist = min(70.0, self.cam_dist * 1.14)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    self.dragging = False
            if event.type == pygame.MOUSEMOTION and self.dragging:
                self.cam_yaw -= event.rel[0] * 0.008
                self.cam_pitch = max(math.radians(4), min(
                    math.radians(80),
                    self.cam_pitch + event.rel[1] * 0.006))
        if not self.follow:
            keys = pygame.key.get_pressed()
            pan = 14.0 / 60.0
            fx = math.cos(self.cam_yaw) * pan
            fy = math.sin(self.cam_yaw) * pan
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

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(0.1, clock.tick(60) / 1000.0)
            running = self.handle_events()
            self.update(dt)
            self.render()
            pygame.display.flip()
        pygame.quit()

    # -- headless shots --------------------------------------------------

    def render_shots(self, times, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        sim_t = 0.0
        step = 1.0 / 30.0
        paths = []
        for target in sorted(times):
            while sim_t < target:
                dt = min(step, target - sim_t)
                self.update(dt)
                sim_t += dt
            self.render()
            data = self.fbo.read(components=3)
            surface = pygame.image.fromstring(data, self.size, "RGB", True)
            path = os.path.join(out_dir, f"shot_{target:07.1f}s.png")
            pygame.image.save(surface, path)
            paths.append(path)
            print(f"saved {path}")
        return paths


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def selftest():
    cat, info = build_dome_catalog()
    mesh = cat.b.build()
    print(f"dome: {len(mesh.vertices)} verts, "
          f"{len(mesh.opaque) // 3} opaque tris, "
          f"{len(mesh.transparent) // 3} transparent tris")
    print(f"floor radius {info['floor_r']:.2f} m, "
          f"apex {info['apex_z']:.2f} m, anchor top {info['anchor_top']:.2f}")
    for stage in STAGES:
        els = cat.stages[stage.key]
        tris = sum((o1 - o0) + (t1 - t0) for o0, o1, t0, t1 in els) // 3
        assert els, f"stage {stage.key} has no elements"
        print(f"  {stage.key:<11} {len(els):>3} elements  {tris:>5} tris")
    env = build_environment()
    print(f"environment: {len(env.vertices)} verts")
    phases = build_phases()
    t = 0.0
    for ph in phases:
        label = (STAGES[ph.station].key
                 if ph.station >= 0 and ph.kind == "work" else ph.kind)
        end = t + ph.dur if math.isfinite(ph.dur) else float("inf")
        print(f"  t={t:7.1f}s -> {end:7.1f}s  {label}")
        if math.isfinite(ph.dur):
            t += ph.dur
    print(f"line completes at t={t:.1f}s (x1 speed)")
    print("selftest OK")


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
        return
    if "--shots" in args:
        times = [float(v) for v in
                 args[args.index("--shots") + 1].split(",")]
        out = os.environ.get("SHOT_DIR", "shots")
        app = AssemblyLineApp(headless=True)
        app.render_shots(times, out)
        return
    app = AssemblyLineApp(windowed="--window" in args)
    app.run()


if __name__ == "__main__":
    main()
