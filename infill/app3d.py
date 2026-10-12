"""Triangle Infill 3-D: fill or cover a triangle, piece by piece, and see
every cut.

The triangle and its frame in 3-D, every infill piece a real solid with its
number on it. Click a piece (or pick it from the list) for its cutting
instructions: every length to mark, every saw setting, what each offcut looks
like. Pick a step and the saw view shows it -- the stick on the mitre saw,
the face that goes down, the side against the fence, the blade swung and
tilted, the cut, and the offcut falling away.

    py -3.12 -m infill.app3d

Mouse: left-drag to turn (keep dragging up to go underneath and see the flat
side), right-drag (or Shift+left) to slide, wheel to zoom, click a piece to
pick it. Keys: U top/underside, Space play/pause, Left/Right step, Tab panel
or saw view, L numbers on/off, F zoom to the picked piece, Home reset, Esc quit.
"""

from __future__ import annotations

import math
import sys
import textwrap
import time
from pathlib import Path

import numpy as np

from . import geom2d as g2
from . import recipes as rc
from . import section as sec
from . import base as bs
from . import sawview
from . import solids as so
from .draw import PALETTE
from .frame import Spec, solve
from .patterns import ARRANGEMENTS, LAYS, MATERIALS, OPTIONS, Options, layout, valid

LEFT_W = 300
RIGHT_W = 480
BOTTOM_H = 58

SCENE_VS = """
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
uniform mat4 u_mvp;
uniform vec3 u_offset;
out vec3 v_world;
out vec3 v_normal;
out vec4 v_color;
void main() {
    vec3 p = in_position + u_offset;
    v_world = p;
    v_normal = in_normal;
    v_color = in_color;
    gl_Position = u_mvp * vec4(p, 1.0);
}
"""

SCENE_FS = """
#version 330
in vec3 v_world;
in vec3 v_normal;
in vec4 v_color;
uniform vec3 u_camera;
uniform vec3 u_light;
uniform vec4 u_tint;
out vec4 frag_color;
void main() {
    vec3 n = normalize(v_normal);
    if (!gl_FrontFacing) n = -n;
    vec3 l = normalize(-u_light);
    vec3 v = normalize(u_camera - v_world);
    vec3 h = normalize(l + v);
    float diffuse = max(dot(n, l), 0.0);
    float specular = pow(max(dot(n, h), 0.0), 36.0);
    vec3 base = mix(v_color.rgb, u_tint.rgb, u_tint.a);
    vec3 lit = base * (0.36 + 0.70 * diffuse) + vec3(1.0, 0.92, 0.75) * specular * 0.18;
    frag_color = vec4(lit, v_color.a);
}
"""

LINE_VS = """
#version 330
in vec3 in_position;
in vec4 in_color;
uniform mat4 u_mvp;
uniform vec3 u_offset;
out vec4 v_color;
void main() {
    v_color = in_color;
    gl_Position = u_mvp * vec4(in_position + u_offset, 1.0);
}
"""

LINE_FS = """
#version 330
in vec4 v_color;
out vec4 frag_color;
void main() { frag_color = v_color; }
"""

PICK_VS = """
#version 330
in vec3 in_position;
uniform mat4 u_mvp;
uniform vec3 u_offset;
void main() { gl_Position = u_mvp * vec4(in_position + u_offset, 1.0); }
"""

PICK_FS = """
#version 330
uniform vec4 u_id;
out vec4 frag_color;
void main() { frag_color = u_id; }
"""

OVERLAY_VS = """
#version 330
in vec2 in_position;
out vec2 v_uv;
void main() { v_uv = in_position * 0.5 + 0.5; gl_Position = vec4(in_position, 0.0, 1.0); }
"""

OVERLAY_FS = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, vec2(v_uv.x, 1.0 - v_uv.y)); }
"""


def rgb(h: str, a: float = 1.0) -> tuple[float, float, float, float]:
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


POSE_COLOR = {k: rgb(PALETTE[k]) for k in ("FDR", "FUL", "FDL", "FUR", "PD", "PU", "BD", "BU", "BE",
                                           "full", "wall", "graded", "copy")}


# ----------------------------------------------------------------------
# Solids to triangles
# ----------------------------------------------------------------------

def _newell(poly: np.ndarray) -> np.ndarray:
    n = np.zeros(3)
    for i in range(len(poly)):
        n += np.cross(poly[i], poly[(i + 1) % len(poly)])
    L = np.linalg.norm(n)
    return n / L if L > 1e-12 else np.array([0.0, 0.0, 1.0])


def _ear_clip(p2: np.ndarray) -> list[tuple[int, int, int]]:
    idx = list(range(len(p2)))
    area = 0.5 * sum(p2[i][0] * p2[(i + 1) % len(p2)][1] - p2[(i + 1) % len(p2)][0] * p2[i][1]
                     for i in range(len(p2)))
    if area < 0:
        idx.reverse()
    out = []

    def inside(p, a, b, c):
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % n]
            a, b, c = p2[i0], p2[i1], p2[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            if any(inside(p2[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            out.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def solid_tris(solid: so.Solid, color) -> np.ndarray:
    rows = []
    if solid is None:
        return np.zeros((0, 10), "f4")
    centre = solid.vertices().mean(axis=0)
    for poly, tag in solid.faces:
        n = _newell(poly)
        if float(n @ (poly.mean(axis=0) - centre)) < 0 and "traced" not in tag:
            n = -n
        col = color
        if tag == "bark":
            col = (color[0] * 0.62, color[1] * 0.5, color[2] * 0.42, color[3])
        elif tag.startswith(("wall", "edge", "centre", "end", "cut")):
            col = (min(1, color[0] * 1.12), min(1, color[1] * 1.08), min(1, color[2] * 1.02), color[3])
        if "traced" in tag and len(poly) > 3:
            u = poly[1] - poly[0]
            u /= max(np.linalg.norm(u), 1e-12)
            w = np.cross(n, u)
            p2 = np.c_[(poly - poly[0]) @ u, (poly - poly[0]) @ w]
            tri = _ear_clip(p2)
        else:
            tri = [(0, i, i + 1) for i in range(1, len(poly) - 1)]
        for a, b, c in tri:
            for v in (poly[a], poly[b], poly[c]):
                rows.append([*v, *n, *col])
    return np.asarray(rows, "f4").reshape(-1, 10)


def solid_lines(solid: so.Solid, color=(0.18, 0.13, 0.09, 1.0)) -> np.ndarray:
    edges: dict = {}
    if solid is None:
        return np.zeros((0, 7), "f4")
    for poly, tag in solid.faces:
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            key = tuple(sorted((tuple(np.round(a, 4)), tuple(np.round(b, 4)))))
            edges.setdefault(key, set()).add(tag)
    rows = []
    for (a, b), tags in edges.items():
        if tags == {"bark"}:
            continue
        rows.append([*a, *color])
        rows.append([*b, *color])
    return np.asarray(rows, "f4").reshape(-1, 7)


def batch_rows(batch) -> np.ndarray:
    return np.asarray(batch.vertices, "f4").reshape(-1, 10)


# ----------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------

class Camera:
    def __init__(self):
        self.target = np.zeros(3)
        self.yaw, self.pitch, self.dist, self.fov = -90.0, 55.0, 120.0, 40.0

    def eye(self) -> np.ndarray:
        cy, sy = math.cos(math.radians(self.yaw)), math.sin(math.radians(self.yaw))
        cp, sp = math.cos(math.radians(self.pitch)), math.sin(math.radians(self.pitch))
        return self.target + self.dist * np.array([cp * cy, cp * sy, sp])

    def mvp(self, aspect: float) -> np.ndarray:
        from two_v_demo.render_kit import look_at, perspective
        return perspective(self.fov, aspect, max(0.1, self.dist * 0.01), self.dist * 20) @ \
            look_at(self.eye(), self.target)

    def basis(self):
        e = self.eye()
        f = self.target - e
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0])
        if np.linalg.norm(r) < 1e-6:
            r = np.array([1.0, 0, 0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        return r, u, f


# ----------------------------------------------------------------------
# The app
# ----------------------------------------------------------------------

class App:
    def __init__(self, size=(1600, 940)):
        import moderngl
        import pygame
        self.pg, self.mgl = pygame, moderngl
        pygame.init()
        pygame.display.set_caption("Triangle Infill 3-D")
        self.W, self.H = size
        self.screen = pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.ctx = moderngl.create_context()
        self.p_scene = self.ctx.program(vertex_shader=SCENE_VS, fragment_shader=SCENE_FS)
        self.p_line = self.ctx.program(vertex_shader=LINE_VS, fragment_shader=LINE_FS)
        self.p_pick = self.ctx.program(vertex_shader=PICK_VS, fragment_shader=PICK_FS)
        self.p_over = self.ctx.program(vertex_shader=OVERLAY_VS, fragment_shader=OVERLAY_FS)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], "f4")
        self.quad_vao = self.ctx.vertex_array(self.p_over, [(self.ctx.buffer(quad.tobytes()), "2f", "in_position")])
        self.overlay_tex = None
        self.fonts = {}
        self.cam = Camera()
        self.saw_cam = Camera()
        self.saw_cam.yaw, self.saw_cam.pitch, self.saw_cam.dist = -90.0, 30.0, 60.0
        # Choices.
        self.strut, self.frame_log, self.infill_log = 72.0, 12.0, 12.0
        self.panel_i = 0
        self.mode = "fill"
        self.material = "w8"
        self.arrangement = "parallel"
        self.lay = "flipflop"
        self.edge = 0
        self.round_t, self.round_min, self.leftover = 1.5, 3.0, "cut"
        self.layer = None
        # The floor base.
        self.make = "infill"
        self.bo = bs.BaseOptions()
        self.B = None
        # View state.
        self.view = "panel"
        self.selected = None
        self.step_i = 0
        self.playing = True
        self.t = 0.0
        self.labels = True
        self.explode = 0.0
        self.build_t = None
        self.list_scroll = 0
        self.recipe_scroll = 0
        self.hover = None
        self.status = ""
        self.widgets: list = []
        self.dragging = None
        self.last_mouse = (0, 0)
        self.pick_fbo = None
        self.saw_cache = {}
        self.rebuild()

    # -------------------------------------------------------------- data
    def options(self) -> Options:
        return valid(Options(self.material, self.arrangement, self.lay, self.mode, self.edge,
                             self.infill_log, 45.0, "open", self.round_t, self.round_min, self.leftover, 1))

    def rebuild(self):
        self.status = "Working it out..."
        self._present_status()
        spec = Spec(max_strut_in=self.strut, frame_log_in=self.frame_log)
        self.solved = solve(spec)
        if self.make == "base":
            self._rebuild_base()
            return
        self.ground_z = -0.6
        self.types = self.solved["types"]
        self.panel_i %= len(self.types)
        self.panel = self.types[self.panel_i]
        o = self.options()
        self.arrangement, self.lay = o.arrangement, o.lay
        self.L = layout(self.panel, o)
        self.recipes = rc.recipes(self.L)
        self.prep = rc.prep_card(self.L)
        self.selected = 0 if self.L.pieces else None
        self.step_i = 0
        self.layers = sorted({int(p.group.split()[1]) for p in self.L.pieces if p.group.startswith("Layer ")})
        if self.layer not in self.layers:
            self.layer = None
        self.saw_cache.clear()
        self._vis = None
        self.footprint = self.panel.tri
        self.top_z = self.panel.spec.thickness_in
        self._upload_panel()
        self._frame_view(reset=True)
        self.status = f"{len(self.L.pieces)} pieces. Click one, or pick it from the list."

    def _rebuild_base(self):
        """The floor base: the pentagon of half trunks and its pattern, sized
        to house the dome the strut and frame log describe."""
        self.B = bs.build(bs.replace(self.bo, dome_radius_in=float(self.solved["radius_in"])))
        self.bo = self.B.opts
        self.L = self.B
        self.recipes = self.B.recipes
        self.prep = self.B.prep
        self.layers, self.layer = [], None
        self.selected = None
        self.step_i = 0
        self.saw_cache.clear()
        self._vis = None
        self.footprint = self.B.crown
        self.top_z = self.B.top
        self.ground_z = -0.05
        self._upload_panel()
        self._frame_view(reset=True)
        c = self.B.checks
        verdict = []
        if self.bo.support == "piers":
            verdict.append("every span passes" if c["worst_ratio"] <= 1 + 1e-9 else "SPANS FAIL")
        verdict.append("deck ok" if c["deck_ok"] else "DECK GAPS TOO WIDE")
        if c["dome_fits"] is not None:
            verdict.append("dome fits" if c["dome_fits"] else "DOME DOES NOT FIT")
        self.status = (f"{len(self.B.members)} members, {len(self.B.piers)} piers: " + ", ".join(verdict) +
                       ". The summary is on the right; click any piece for its cuts.")

    def _present_status(self):
        try:
            self.draw()
        except Exception:  # noqa: BLE001
            pass

    def _upload_panel(self):
        ctx = self.ctx
        # The frame: each member a wedge lying on a sawn face, point at the opening.
        frame_rows, frame_lines = [], []
        members = [] if self.make == "base" else self.panel.members()
        if members:
            spec = self.panel.spec
            wall = sec.frame_section(spec.radius_in, spec.wall_deg)
        for k, poly in enumerate(members):
            a, b = self.panel.edge(k)
            d = g2.unit(b - a)
            m = self.panel.inward(k)
            org = a + m * self.panel.inset_at(0.0)
            s = so.prism(wall, ["frame"] * len(wall), org, d, m, 0.0)
            proj = (poly - org) @ d
            o3 = s.origin
            s = so.clip(s, so.Plane(s.along, float(s.along @ o3) + float(proj.min()), "frame end"))
            s = so.clip(s, so.Plane(-s.along, -(float(s.along @ o3) + float(proj.max())), "frame end"))
            frame_rows.append(solid_tris(s, rgb(PALETTE["frame"])))
            frame_lines.append(solid_lines(s, (0.25, 0.15, 0.08, 1.0)))
        self.frame_mesh = self._mesh(np.concatenate(frame_rows)) if frame_rows else None
        self.frame_lines = self._lines(np.concatenate(frame_lines)) if frame_lines else None
        # The pieces, each its own range in one buffer.
        rows, lines, self.ranges, self.centres, self.piece_z = [], [], [], [], []
        start = 0
        for p in self.L.pieces:
            col = POSE_COLOR.get(p.pose, rgb(PALETTE.get(p.material, PALETTE["sheet"])))
            if getattr(p, "color", None) is not None:
                col = p.color
            elif p.material in ("osb", "ply"):
                col = rgb(PALETTE["sheet"])
            elif p.material in ("metal", "film"):
                col = rgb(PALETTE[p.material], 0.95)
            tr = solid_tris(p.solid, col)
            rows.append(tr)
            self.ranges.append((start, len(tr)))
            start += len(tr)
            ln = solid_lines(p.solid)
            lines.append(ln)
            v = p.solid.vertices() if p.solid is not None else np.zeros((1, 3))
            self.centres.append(v.mean(axis=0) if len(v) else np.zeros(3))
            self.piece_z.append(float(v[:, 2].mean()) if len(v) else 0.0)
        self.line_ranges = []
        s = 0
        for ln in lines:
            self.line_ranges.append((s, len(ln)))
            s += len(ln)
        data = np.concatenate(rows) if rows else np.zeros((0, 10), "f4")
        self.piece_mesh = self._mesh(data)
        self.piece_lines = self._lines(np.concatenate(lines) if lines else np.zeros((0, 7), "f4"))
        # Ground under it all.
        pad = 60 if self.make == "base" else 20
        lo = self.footprint.min(axis=0) - pad
        hi = self.footprint.max(axis=0) + pad
        gz = self.ground_z
        g = np.array([[lo[0], lo[1], gz], [hi[0], lo[1], gz], [hi[0], hi[1], gz],
                      [lo[0], lo[1], gz], [hi[0], hi[1], gz], [lo[0], hi[1], gz]])
        gr = np.c_[g, np.tile([0, 0, 1.0], (6, 1)), np.tile(rgb("#2f3a33"), (6, 1))].astype("f4")
        self.ground = self._mesh(gr)

    def _mesh(self, data: np.ndarray):
        if len(data) == 0:
            return None
        vbo = self.ctx.buffer(np.ascontiguousarray(data, "f4").tobytes())
        return (vbo, self.ctx.vertex_array(self.p_scene, [(vbo, "3f 3f 4f", "in_position", "in_normal", "in_color")]),
                self.ctx.vertex_array(self.p_pick, [(vbo, "3f 28x", "in_position")]),
                len(data))

    def _lines(self, data: np.ndarray):
        if len(data) == 0:
            return None
        vbo = self.ctx.buffer(np.ascontiguousarray(data, "f4").tobytes())
        return (vbo, self.ctx.vertex_array(self.p_line, [(vbo, "3f 4f", "in_position", "in_color")]), len(data))

    def _frame_view(self, reset=False):
        tri = self.footprint
        c = tri.mean(axis=0)
        self.cam.target = np.array([c[0], c[1], self.top_z * 0.5])
        if reset:
            self.cam.dist = float(np.linalg.norm(tri.max(axis=0) - tri.min(axis=0))) * 1.5
            self.cam.yaw, self.cam.pitch = -90.0, 58.0

    # -------------------------------------------------------------- drawing
    def viewport(self):
        return (LEFT_W, BOTTOM_H, max(10, self.W - LEFT_W - RIGHT_W), max(10, self.H - BOTTOM_H))

    def _uniforms(self, prog, mvp, cam, offset=(0, 0, 0), tint=(0, 0, 0, 0)):
        prog["u_mvp"].write(np.ascontiguousarray(mvp.T, "f4").tobytes())
        if "u_offset" in prog:
            prog["u_offset"].value = tuple(float(x) for x in offset)
        if "u_camera" in prog:
            prog["u_camera"].value = tuple(float(x) for x in cam.eye())
        if "u_light" in prog:
            # The sun comes from whichever side you look from, so the underside is not left in shadow.
            below = cam.eye()[2] < cam.target[2]
            prog["u_light"].value = (0.45, 0.6, 0.75 if below else -0.75)
        if "u_tint" in prog:
            prog["u_tint"].value = tuple(float(x) for x in tint)

    def _hidden(self, i: int) -> bool:
        return self.layer is not None and self.L.pieces[i].group != f"Layer {self.layer}"

    def _offset(self, i: int) -> tuple[float, float, float]:
        if self._hidden(i):
            return (0.0, 0.0, 1e5)
        dx = dy = dz = 0.0
        if self.explode:
            # Pull every piece out from the middle and lift neighbours apart.
            c = self.footprint.mean(axis=0)
            dx, dy = (self.centres[i][:2] - c) * 0.35 * self.explode
            dz = self.explode * (4.0 + 6.0 * (i % 2))
        if self.build_t is not None:
            n = len(self.L.pieces)
            k = self.build_t * (n + 4) - i
            if k < 0:
                return (0.0, 0.0, 1e5)
            if k < 1:
                return (dx, dy, dz + (1 - k) ** 2 * 40)
        return (dx, dy, dz)

    def draw_panel(self, mvp):
        mgl = self.mgl
        self.ctx.disable(mgl.CULL_FACE)
        if self.ground and self.cam.eye()[2] > 0.0:
            self._uniforms(self.p_scene, mvp, self.cam)
            self.ground[1].render(mgl.TRIANGLES)
        if self.frame_mesh:
            self._uniforms(self.p_scene, mvp, self.cam)
            self.frame_mesh[1].render(mgl.TRIANGLES)
            self._uniforms(self.p_line, mvp, self.cam)
            self.frame_lines[1].render(mgl.LINES)
        if self.piece_mesh:
            for i, (st, n) in enumerate(self.ranges):
                if n == 0:
                    continue
                tint = (0, 0, 0, 0)
                if i == self.selected:
                    tint = (1.0, 0.86, 0.2, 0.6)
                elif i == self.hover:
                    tint = (1.0, 1.0, 1.0, 0.25)
                off = self._offset(i)
                if off[2] > 1e4:
                    continue
                self._uniforms(self.p_scene, mvp, self.cam, off, tint)
                self.piece_mesh[1].render(mgl.TRIANGLES, vertices=n, first=st)
                ls, ln = self.line_ranges[i]
                if ln and self.piece_lines:
                    self._uniforms(self.p_line, mvp, self.cam, off)
                    self.piece_lines[1].render(mgl.LINES, vertices=ln, first=ls)

    def pick(self, mx, my):
        """The piece under the mouse: every piece drawn in its own colour."""
        x, y, w, h = self._render_ids()
        px, py = mx - x, (self.H - my) - y
        if not (0 <= px < w and 0 <= py < h):
            self.ctx.screen.use()
            return None
        data = self.pick_fbo.read(viewport=(px, py, 1, 1), components=4)
        self.ctx.screen.use()
        code = data[0] + (data[1] << 8)
        return code - 1 if code > 0 else None

    def _visible(self) -> dict:
        """Where each piece can actually be seen: the visible pixel of it
        nearest the middle of its visible part. Pieces hidden behind others,
        or under another layer, get no number."""
        key = (self.cam.yaw, self.cam.pitch, self.cam.dist, tuple(self.cam.target), self.explode,
               self.build_t, self.layer, self.W, self.H, id(self.L))
        if getattr(self, "_vis_key", None) == key:
            return self._vis
        if key != getattr(self, "_last_key", None) and getattr(self, "_vis", None) is not None:
            # Still moving: follow the last pieces seen, and look properly once the view settles.
            self._last_key = key
            x, y, w, h = self.viewport()
            mvp = self.cam.mvp(w / h)
            out = {}
            for i in self._vis:
                if i >= len(self.centres):
                    continue
                c, off = self.centres[i], self._offset(i)
                q = mvp @ np.array([c[0] + off[0], c[1] + off[1], c[2] + off[2], 1.0])
                if q[3] > 0:
                    out[i] = (x + (q[0] / q[3] * 0.5 + 0.5) * w, self.H - (y + (q[1] / q[3] * 0.5 + 0.5) * h))
            return out
        self._last_key = key
        x, y, w, h = self._render_ids()
        a = np.frombuffer(self.pick_fbo.read(components=4), np.uint8).reshape(h, w, 4)
        self.ctx.screen.use()
        codes = a[..., 0].astype(np.int64) + (a[..., 1].astype(np.int64) << 8)
        rows, cols = np.nonzero(codes)
        out = {}
        if len(rows):
            c = codes[rows, cols]
            n = np.bincount(c)
            mx = np.bincount(c, weights=cols) / np.maximum(n, 1)
            my = np.bincount(c, weights=rows) / np.maximum(n, 1)
            d = (cols - mx[c]) ** 2 + (rows - my[c]) ** 2
            order = np.lexsort((d, c))
            ids, first = np.unique(c[order], return_index=True)
            for code, k in zip(ids, first):
                if n[code] < 12:
                    continue
                j = order[k]
                out[int(code) - 1] = (x + cols[j] + 0.5, self.H - (y + rows[j] + 0.5))
        self._vis_key, self._vis = key, out
        return out

    def _render_ids(self):
        mgl = self.mgl
        x, y, w, h = self.viewport()
        if self.pick_fbo is None or self.pick_fbo.size != (w, h):
            self.pick_fbo = self.ctx.framebuffer(color_attachments=[self.ctx.texture((w, h), 4)],
                                                 depth_attachment=self.ctx.depth_renderbuffer((w, h)))
        self.pick_fbo.use()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.clear(0, 0, 0, 0)
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.disable(mgl.CULL_FACE)
        mvp = self.cam.mvp(w / h)
        if self.frame_mesh:
            self._uniforms(self.p_pick, mvp, self.cam)
            self.p_pick["u_id"].value = (0, 0, 0, 1)
            self.frame_mesh[2].render(mgl.TRIANGLES)
        if self.piece_mesh:
            for i, (st, n) in enumerate(self.ranges):
                off = self._offset(i)
                if n == 0 or off[2] > 1e4:
                    continue
                self._uniforms(self.p_pick, mvp, self.cam, off)
                code = i + 1
                self.p_pick["u_id"].value = ((code & 255) / 255, ((code >> 8) & 255) / 255, 0.0, 1.0)
                self.piece_mesh[2].render(mgl.TRIANGLES, vertices=n, first=st)
        return x, y, w, h

    # ---------------------------------------------------------- the saw view
    def current_step(self):
        if self.selected is None or self.selected >= len(self.recipes):
            return None
        steps = self.recipes[self.selected].steps
        if not steps:
            return None
        self.step_i = max(0, min(self.step_i, len(steps) - 1))
        return steps[self.step_i]

    def saw_scene(self, step):
        key = (self.selected, self.step_i)
        if key in self.saw_cache:
            return self.saw_cache[key]
        an = step.anim or {}
        sc = sawview.parts(an)
        if sc is None:
            out = {"type": "place" if an.get("type") == "place" else None}
            self.saw_cache[key] = out
            return out
        out = dict(sc)

        def conv(sol, col):
            if sol is None:
                return None
            return self._mesh(solid_tris(sol, col)), self._lines(solid_lines(sol))
        out["keeper"] = conv(sc["keeper"], rgb(PALETTE["sheet"]) if sc["whole"] else rgb(PALETTE["FUL"]))
        out["offcut"] = conv(sc["offcut"], rgb("#e8c35a"))
        from two_v_demo.render_kit import TriangleBatch
        b = TriangleBatch()
        for centre, size, colour in sawview.bench(sc):
            b.box(centre, size, rgb(colour))
        out["bench"] = self._mesh(batch_rows(b))
        self.saw_cache[key] = out
        return out

    def draw_saw(self, mvp, step, t):
        mgl = self.mgl
        sc = self.saw_scene(step)
        self.ctx.disable(mgl.CULL_FACE)
        if sc.get("type") not in ("mitre", "freehand"):
            return False
        if sc.get("bench"):
            self._uniforms(self.p_scene, mvp, self.saw_cam)
            sc["bench"][1].render(mgl.TRIANGLES)
        mo = sawview.moment(sc, t)
        sc["offsets"] = {k: tuple(v) for k, v in mo["offsets"].items()}
        for part, off in sc["offsets"].items():
            m = sc.get(part)
            if not m or not m[0]:
                continue
            self._uniforms(self.p_scene, mvp, self.saw_cam, off)
            m[0][1].render(mgl.TRIANGLES)
            if m[1]:
                self._uniforms(self.p_line, mvp, self.saw_cam, off)
                m[1][1].render(mgl.LINES)
        # The blade: a disc in the cut plane, coming down through the stick.
        ns, centre, Rb = mo["blade_axis"], mo["blade_centre"], mo["blade_r"]
        from two_v_demo.render_kit import TriangleBatch
        bb = TriangleBatch()
        bb.cylinder(centre - ns * 0.06, centre + ns * 0.06, Rb, rgb("#d6dde3"), 48)
        bb.cylinder(centre - ns * 0.12, centre + ns * 0.12, 0.8, rgb("#39424a"), 16)
        rows = batch_rows(bb)
        mesh = self._mesh(rows)
        if mesh:
            self._uniforms(self.p_scene, mvp, self.saw_cam)
            mesh[1].render(mgl.TRIANGLES)
            mesh[0].release()
        return True

    # -------------------------------------------------------------- overlay
    def font(self, size, bold=False):
        k = (size, bold)
        if k not in self.fonts:
            self.fonts[k] = self.pg.font.SysFont("segoeui", size, bold=bold)
        return self.fonts[k]

    def text(self, surf, s, x, y, size=13, color=(235, 230, 220), bold=False, maxw=None):
        f = self.font(size, bold)
        if maxw is None:
            img = f.render(s, True, color)
            surf.blit(img, (x, y))
            return y + img.get_height()
        lines = []
        for para in s.split("\n"):
            words = para.split(" ")
            cur = ""
            for w_ in words:
                trial = (cur + " " + w_).strip()
                if f.size(trial)[0] <= maxw:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w_
            lines.append(cur)
        for ln in lines:
            img = f.render(ln, True, color)
            surf.blit(img, (x, y))
            y += img.get_height()
        return y

    def button(self, surf, rect, label, cb, active=False, size=13):
        pg = self.pg
        r = pg.Rect(rect)
        mx, my = pg.mouse.get_pos()
        hot = r.collidepoint(mx, my)
        bg = (214, 168, 98) if active else ((74, 82, 92) if hot else (52, 58, 66))
        pg.draw.rect(surf, bg, r, border_radius=5)
        f = self.font(size, active)
        img = f.render(label, True, (20, 18, 16) if active else (235, 230, 220))
        surf.blit(img, (r.x + (r.w - img.get_width()) // 2, r.y + (r.h - img.get_height()) // 2))
        self.widgets.append((r, cb))

    def chooser(self, surf, y, label, value, prev_cb, next_cb):
        self.text(surf, label, 14, y, 12, (180, 175, 165))
        self.button(surf, (14, y + 18, 28, 26), "<", prev_cb)
        pg = self.pg
        pg.draw.rect(surf, (36, 40, 46), (46, y + 18, LEFT_W - 94, 26), border_radius=4)
        f = self.font(12)
        s = value
        while f.size(s)[0] > LEFT_W - 104 and len(s) > 4:
            s = s[:-2]
        if s != value:
            s = s[:-1] + "…"
        surf.blit(f.render(s, True, (240, 236, 226)), (52, y + 22))
        self.button(surf, (LEFT_W - 44, y + 18, 28, 26), ">", next_cb)
        return y + 50

    def draw_overlay(self, mvp):
        pg = self.pg
        surf = pg.Surface((self.W, self.H), pg.SRCALPHA)
        self.widgets = []
        panel_bg = (24, 27, 31, 238)
        pg.draw.rect(surf, panel_bg, (0, 0, LEFT_W, self.H))
        pg.draw.rect(surf, panel_bg, (self.W - RIGHT_W, 0, RIGHT_W, self.H))
        pg.draw.rect(surf, panel_bg, (LEFT_W, self.H - BOTTOM_H, self.W - LEFT_W - RIGHT_W, BOTTOM_H))
        self._left(surf)
        self._right(surf)
        self._bottom(surf)
        if self.view == "panel":
            self._labels(surf, mvp)
        else:
            self._saw_labels(surf)
        data = pg.image.tostring(surf, "RGBA", False)
        if self.overlay_tex is None or self.overlay_tex.size != (self.W, self.H):
            self.overlay_tex = self.ctx.texture((self.W, self.H), 4)
        self.overlay_tex.write(data)
        self.ctx.viewport = (0, 0, self.W, self.H)
        self.ctx.enable(self.mgl.BLEND)
        self.ctx.blend_func = self.mgl.SRC_ALPHA, self.mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.disable(self.mgl.DEPTH_TEST)
        self.overlay_tex.use(0)
        self.p_over["u_texture"].value = 0
        self.quad_vao.render(self.mgl.TRIANGLE_STRIP)
        self.ctx.disable(self.mgl.BLEND)

    def _cycle(self, attr, values, d):
        cur = getattr(self, attr)
        i = values.index(cur) if cur in values else 0
        setattr(self, attr, values[(i + d) % len(values)])
        self.rebuild()

    def _left(self, surf):
        y = self.text(surf, "Triangle Infill 3-D", 14, 10, 18, (240, 220, 180), True) + 4
        y = self.text(surf, "Fill or cover a triangle, or build the floor base, piece by piece, and see every "
                            "cut.", 14, y, 11, (170, 165, 155), maxw=LEFT_W - 28) + 6
        y = self.chooser(surf, y, "Make", "Triangle infill" if self.make == "infill" else "Floor base (pentagon)",
                         lambda: self._set_make(), lambda: self._set_make())
        if self.make == "base":
            y = self._left_base(surf, y)
        else:
            y = self._left_infill(surf, y)
        self._left_common(surf, y)

    def _left_infill(self, surf, y):

        def num_row(y, label, attr, step, lo, hi):
            self.text(surf, label, 14, y, 12, (180, 175, 165))
            self.button(surf, (LEFT_W - 140, y - 2, 26, 22), "-", lambda: self._bump(attr, -step, lo, hi))
            self.text(surf, f"{getattr(self, attr):g}", LEFT_W - 106, y, 13, (240, 236, 226), True)
            self.button(surf, (LEFT_W - 44, y - 2, 26, 22), "+", lambda: self._bump(attr, step, lo, hi))
            return y + 26
        y = num_row(y, "Max strut (in)", "strut", 6.0, 36.0, 144.0)
        y = num_row(y, "Frame log (in)", "frame_log", 1.0, 6.0, 30.0)
        y = num_row(y, "Infill log (in)", "infill_log", 1.0, 4.0, 30.0)
        tri_names = [f"{t.label} (x{t.count})" for t in self.types]
        y = self.chooser(surf, y + 4, "Triangle", tri_names[self.panel_i],
                         lambda: self._set_panel(-1), lambda: self._set_panel(1))
        y = self.chooser(surf, y, "Fill or cover", "Fill (inside the frame)" if self.mode == "fill" else
                         "Cover (over the open side)", lambda: self._cycle("mode", ["fill", "cover"], -1),
                         lambda: self._cycle("mode", ["fill", "cover"], 1))
        mats = list(MATERIALS)
        y = self.chooser(surf, y, "Material", MATERIALS[self.material][0],
                         lambda: self._cycle("material", mats, -1), lambda: self._cycle("material", mats, 1))
        kind = MATERIALS[self.material][1]
        arrs = OPTIONS[kind]["arrangements"]
        y = self.chooser(surf, y, "Arrangement", ARRANGEMENTS[self.arrangement],
                         lambda: self._cycle("arrangement", arrs, -1), lambda: self._cycle("arrangement", arrs, 1))
        lays = [l for l in OPTIONS[kind]["lays"] if not (l == "shim" and self.material == "s32")]
        if self.arrangement != "louvers" and lays:
            y = self.chooser(surf, y, "Lay", LAYS[self.lay][0] if self.lay in LAYS else "-",
                             lambda: self._cycle("lay", lays, -1), lambda: self._cycle("lay", lays, 1))
        if self.arrangement in ("parallel", "louvers", "chevron", "strips", "across"):
            names = [f"edge {k + 1}: {self.panel.edge_class[k].lower()} {self.panel.edge_len[k]:.0f} in"
                     for k in range(3)]
            y = self.chooser(surf, y, "Lay the runs from", names[self.edge],
                             lambda: self._cycle("edge", [0, 1, 2], -1), lambda: self._cycle("edge", [0, 1, 2], 1))
        if self.material == "rounds":
            y = num_row(y, "Slice thickness (in)", "round_t", 0.25, 0.5, 6.0)
            y = num_row(y, "Smallest round (in)", "round_min", 1.0, 1.0, 12.0)
            y = self.chooser(surf, y, "Gaps", "cut to fit" if self.leftover == "cut" else "left open",
                             lambda: self._cycle("leftover", ["cut", "open"], -1),
                             lambda: self._cycle("leftover", ["cut", "open"], 1))
        if len(self.layers) > 1:
            y = self.chooser(surf, y, "Show layer", "all layers" if self.layer is None else
                             f"layer {self.layer} of {len(self.layers)}",
                             lambda: self._step_layer(-1), lambda: self._step_layer(1))
        return y

    def _left_base(self, surf, y):
        o = self.bo

        def cyc(y, field, values, label, names):
            cur = getattr(o, field)
            i = values.index(cur) if cur in values else 0
            return self.chooser(surf, y, label, names(cur),
                                lambda: self._bo_set(field, values[(i - 1) % len(values)]),
                                lambda: self._bo_set(field, values[(i + 1) % len(values)]))

        def num(y, label, value, setter, step, lo, hi):
            self.text(surf, label, 14, y, 12, (180, 175, 165))
            self.button(surf, (LEFT_W - 140, y - 2, 26, 22), "-", lambda: setter(max(lo, value - step)))
            self.text(surf, f"{value:g}", LEFT_W - 106, y, 13, (240, 236, 226), True)
            self.button(surf, (LEFT_W - 44, y - 2, 26, 22), "+", lambda: setter(min(hi, value + step)))
            return y + 25
        mats = list(bs.MATERIALS)
        pats = list(bs.PATTERNS)
        y = cyc(y, "pattern", pats, "Pattern", lambda k: bs.PATTERNS[k][0])
        y = cyc(y, "frame_mat", mats, "Frame (your five 20 ft trunks)", lambda k: bs.MATERIALS[k][0])
        word = bs._primary_word(o)
        y = cyc(y, "prim_mat", mats, f"{word}s", lambda k: bs.MATERIALS[k][0])
        if o.pattern not in ("star", "rings"):
            y = cyc(y, "sec_mat", mats, "Joists", lambda k: bs.MATERIALS[k][0])
        y = cyc(y, "support", list(bs.SUPPORTS), "Support", lambda k: bs.SUPPORTS[k].split(" (")[0])
        decks = [k for k in bs.DECKS if k != "fill" or o.support == "gravel"]
        y = cyc(y, "deck", decks, "Deck", lambda k: bs.DECKS[k][0])
        y += 2
        y = num(y, "Log diameter (in)", o.log_in, lambda v: self._bo_set("log_in", v), 1.0, 4.0, 30.0)
        y = num(y, "Side, round backs (ft)", o.side_in / 12, lambda v: self._bo_set("side_in", v * 12), 0.5,
                8.0, 30.0)
        if o.pattern not in ("star", "rings"):
            y = num(y, "Joist spacing (in o.c.)", o.spacing_in, lambda v: self._bo_set("spacing_in", v), 2.0,
                    12.0, 48.0)
        if o.pattern == "beams":
            y = num(y, "Beam spacing (in)", o.beam_spacing_in, lambda v: self._bo_set("beam_spacing_in", v), 6.0,
                    24.0, 144.0)
        if o.pattern in ("star", "star_joists"):
            y = num(y, "Stars inside stars", float(o.star_levels),
                    lambda v: self._bo_set("star_levels", int(v)), 1.0, 1.0, 3.0)
        y = num(y, "Dome max strut (in)", self.strut, lambda v: self._bump("strut", v - self.strut, 36.0, 144.0),
                6.0, 36.0, 144.0)
        return y

    def _left_common(self, surf, y):
        y += 6
        self.text(surf, "View", 14, y, 12, (180, 175, 165))
        y += 18
        self.button(surf, (14, y, 88, 26), "Panel", lambda: self._set_view("panel"), self.view == "panel")
        self.button(surf, (106, y, 88, 26), "Saw", lambda: self._set_view("saw"), self.view == "saw")
        self.button(surf, (198, y, 88, 26), "Numbers", self._toggle_labels, self.labels)
        y += 32
        self.button(surf, (14, y, 88, 26), "Build it", self._start_build, self.build_t is not None)
        self.button(surf, (106, y, 88, 26), "Explode", self._toggle_explode, self.explode > 0)
        self.button(surf, (198, y, 88, 26), "Reset view", lambda: self._frame_view(True))
        y += 32
        side = self._side()
        self.button(surf, (14, y, 88, 26), "From top", lambda: self._look("top"), side == "top")
        self.button(surf, (106, y, 88, 26), "From under", lambda: self._look("under"), side == "under")
        self.button(surf, (198, y, 88, 26), "Edge-on", lambda: self._look("edge"), side == "edge")
        y += 36
        self.text(surf, "Save", 14, y, 12, (180, 175, 165))
        y += 18
        base = self.make == "base"
        self.button(surf, (14, y, 134, 26), "Instructions (TXT)", self.save_instructions, size=12)
        self.button(surf, (152, y, 134, 26), "Plan (SVG)" if base else "Cut sheet (SVG)", self.save_svg, size=12)
        y += 30
        self.button(surf, (14, y, 134, 26), "Cut list (CSV)" if base else "Buying list (CSV)", self.save_csv,
                    size=12)
        self.button(surf, (152, y, 134, 26), "Compare patterns" if base else "Patterns (PNG)", self.save_gallery,
                    size=12)
        if base:
            y += 30
            self.button(surf, (14, y, 272, 26), "Summary: strength, decking, buying", self._show_summary,
                        self.selected is None, size=12)
        y += 36
        if y < self.H - 110:
            self.text(surf, "Left-drag turn (drag up to go underneath) · right-drag slide · wheel zoom · click a "
                            "piece · U top/under · Space play · arrows step · Tab view · F zoom to piece",
                      14, y, 11, (150, 146, 138), maxw=LEFT_W - 28)
        self.text(surf, self.status, 14, self.H - 40, 11, (214, 190, 140), maxw=LEFT_W - 28)

    def _right(self, surf):
        pg = self.pg
        x0 = self.W - RIGHT_W + 12
        w = RIGHT_W - 24
        y = self.text(surf, self.L.title, x0, 10, 14, (240, 220, 180), True, maxw=w) + 2
        sub_title = (f"{len(self.B.members)} members, {len(self.B.piers)} piers · "
                     f"{bs.SUPPORTS[self.bo.support].split(' (')[0].lower()}" if self.make == "base" else
                     f"{self.panel.label}, {self.mode} · {len(self.L.pieces)} pieces")
        y = self.text(surf, sub_title, x0, y, 11, (170, 165, 155)) + 6
        # The piece list.
        list_h = int(self.H * 0.30)
        list_top = y
        self.list_rect = pg.Rect(x0 - 4, list_top, w + 8, list_h)
        pg.draw.rect(surf, (32, 36, 41), self.list_rect, border_radius=4)
        row_h = 20
        n = len(self.recipes)
        self.list_scroll = max(0, min(self.list_scroll, max(0, n - list_h // row_h)))
        clip = surf.get_clip()
        surf.set_clip(self.list_rect)
        for j in range(self.list_scroll, min(n, self.list_scroll + list_h // row_h + 1)):
            r = self.recipes[j]
            ry = list_top + (j - self.list_scroll) * row_h
            rr = pg.Rect(x0 - 2, ry, w + 4, row_h)
            if j == self.selected:
                pg.draw.rect(surf, (214, 168, 98), rr, border_radius=3)
            col = (20, 18, 16) if j == self.selected else (225, 220, 210)
            label = f"{r.number:>3}  {r.name}"
            self.text(surf, label[:44], x0 + 2, ry + 2, 12, col, j == self.selected)
            self.text(surf, r.summary[:30], x0 + w - 190, ry + 2, 11, col)
            self.widgets.append((rr, (lambda jj=j: self._select(jj))))
        surf.set_clip(clip)
        y = list_top + list_h + 8
        # The recipe.
        self.recipe_rect = pg.Rect(x0 - 4, y, w + 8, self.H - y - 8)
        pg.draw.rect(surf, (32, 36, 41), self.recipe_rect, border_radius=4)
        surf.set_clip(self.recipe_rect)
        ry = y + 6 - self.recipe_scroll
        if self.selected is not None and self.selected < len(self.recipes):
            r = self.recipes[self.selected]
            ry = self.text(surf, f"Piece {r.number}: {r.name}", x0 + 4, ry, 15, (240, 220, 180), True,
                           maxw=w - 8) + 4
            for a, b in r.dims:
                ry2 = self.text(surf, a, x0 + 6, ry, 11, (170, 165, 155), maxw=w * 0.5)
                ry3 = self.text(surf, b, x0 + w * 0.52, ry, 12, (240, 236, 226), True, maxw=w * 0.46)
                ry = max(ry2, ry3) + 2
            ry += 6
            for k, s in enumerate(r.steps):
                top = ry
                active = k == self.step_i
                ry = self.text(surf, f"{k + 1}. {s.title}", x0 + 10, ry + 4, 13,
                               (20, 18, 16) if active else (240, 236, 226), True, maxw=w - 20)
                ry = self.text(surf, s.text, x0 + 10, ry, 12, (30, 26, 22) if active else (205, 200, 190),
                               maxw=w - 20) + 6
                box = pg.Rect(x0, top, w, ry - top)
                if active:
                    hl = pg.Surface((box.w, box.h), pg.SRCALPHA)
                    hl.fill((214, 168, 98, 255))
                    surf.blit(hl, box.topleft)
                    # Redraw the text over the highlight.
                    yy = self.text(surf, f"{k + 1}. {s.title}", x0 + 10, top + 4, 13, (20, 18, 16), True, maxw=w - 20)
                    self.text(surf, s.text, x0 + 10, yy, 12, (30, 26, 22), maxw=w - 20)
                self.widgets.append((box, (lambda kk=k: self._set_step(kk))))
            self.recipe_h = ry + self.recipe_scroll - y
        if self.prep is not None:
            ry += 8
            ry = self.text(surf, self.prep.name, x0 + 4, ry, 13, (240, 220, 180), True, maxw=w - 8) + 2
            for s in self.prep.steps:
                ry = self.text(surf, f"{s.title}: {s.text}", x0 + 8, ry, 11, (190, 185, 175), maxw=w - 16) + 4
        surf.set_clip(clip)

    def _bottom(self, surf):
        x0 = LEFT_W + 12
        y = self.H - BOTTOM_H + 14
        self.button(surf, (x0, y, 74, 28), "< Step", lambda: self._set_step(self.step_i - 1))
        self.button(surf, (x0 + 80, y, 74, 28), "Pause" if self.playing else "Play", self._toggle_play)
        self.button(surf, (x0 + 160, y, 74, 28), "Step >", lambda: self._set_step(self.step_i + 1))
        step = self.current_step()
        if step is not None:
            r = self.recipes[self.selected]
            self.text(surf, f"Piece {r.number} · step {self.step_i + 1} of {len(r.steps)}: {step.title}",
                      x0 + 248, y + 4, 13, (240, 236, 226), True)

    def _labels(self, surf, mvp):
        if not self.labels:
            return
        x, y, w, h = self.viewport()
        pg = self.pg
        f = self.font(11, True)
        taken: list = []
        vis = self._visible()
        order = list(range(len(self.centres)))
        if self.selected is not None:
            order.remove(self.selected)
            order.insert(0, self.selected)
        for i in order:
            if i not in vis:
                continue
            sx, sy = vis[i]
            if not (x < sx < x + w and 0 < sy < self.H - BOTTOM_H):
                continue
            label = str(i + 1)
            img = f.render(label, True, (20, 18, 16))
            rr = max(img.get_width(), img.get_height()) // 2 + 3
            if any((sx - a) ** 2 + (sy - b) ** 2 < (rr + r2) ** 2 for a, b, r2 in taken):
                continue
            taken.append((sx, sy, rr))
            col = (255, 214, 90) if i == self.selected else (245, 240, 228)
            pg.draw.circle(surf, col + (230,), (int(sx), int(sy)), rr)
            surf.blit(img, (int(sx - img.get_width() / 2), int(sy - img.get_height() / 2)))

    def _saw_labels(self, surf):
        step = self.current_step()
        x, y, w, h = self.viewport()
        if step is None:
            return
        sc = self.saw_scene(step)
        top = 14
        if sc.get("type") == "mitre":
            lines = [f"Mitre {abs(sc['mitre']):.1f}° " + ("(cut drifts right toward you)" if sc["mitre"] > 0.05 else
                                                         "(cut drifts left toward you)" if sc["mitre"] < -0.05 else "(square)"),
                     f"Bevel {abs(sc['bevel']):.1f}° " + ("(blade top tilted left)" if sc["bevel"] > 0.05 else "(upright)"),
                     "Fence at the back · you stand at the front",
                     f"Keeper {'right' if sc['keeper_right'] else 'left'} of the blade · offcut "
                     f"{'left' if sc['keeper_right'] else 'right'}"]
        elif sc.get("type") == "freehand":
            lines = ["Marked and cut by hand: the blade's plane is shown", "The offcut parts along the cut"]
        else:
            lines = ["This step has no saw cut: see the panel view"]
        for ln in lines:
            top = self.text(surf, ln, x + 14, top, 14, (245, 238, 220), True) + 2
        mvp = getattr(self, "_saw_mvp", None)
        if mvp is None or sc.get("type") not in ("mitre", "freehand"):
            return
        offs = sc.get("offsets", {})
        tags = []
        if sc["type"] == "mitre":
            tags += [("FENCE", (16.0, 1.0, 5.6)), ("YOU STAND HERE", (0.0, -21.0, 0.0))]
        for part, name in (("keeper", "KEEPER"), ("offcut", "OFFCUT")):
            at = sc.get(part + "_at")
            if at is not None:
                o = offs.get(part, (0, 0, 0))
                tags.append((name, (at[0] + o[0], at[1] + o[1], at[2] + o[2] + 3.0)))
        for name, p in tags:
            q = mvp @ np.array([*p, 1.0])
            if q[3] <= 0:
                continue
            sx = x + (q[0] / q[3] * 0.5 + 0.5) * w
            sy = self.H - (y + (q[1] / q[3] * 0.5 + 0.5) * h)
            if not (x < sx < x + w and 0 < sy < self.H - BOTTOM_H):
                continue
            f = self.font(13, True)
            img = f.render(name, True, (20, 18, 16))
            box = self.pg.Rect(0, 0, img.get_width() + 12, img.get_height() + 4)
            box.center = (int(sx), int(sy))
            col = (232, 195, 90) if name == "OFFCUT" else (245, 240, 228)
            self.pg.draw.rect(surf, col + (235,), box, border_radius=4)
            surf.blit(img, (box.x + 6, box.y + 2))

    # -------------------------------------------------------------- actions
    def _set_make(self):
        self.make = "base" if self.make == "infill" else "infill"
        self.view = "panel"
        self.rebuild()

    def _bo_set(self, field, value):
        self.bo = bs.replace(self.bo, **{field: value})
        self.rebuild()

    def _show_summary(self):
        self.selected = None
        self.recipe_scroll = 0
        self.view = "panel"

    def _step_layer(self, d):
        seq = [None] + self.layers
        self.layer = seq[(seq.index(self.layer) + d) % len(seq)]

    def _bump(self, attr, d, lo, hi):
        setattr(self, attr, float(min(hi, max(lo, getattr(self, attr) + d))))
        self.rebuild()

    def _set_panel(self, d):
        self.panel_i = (self.panel_i + d) % len(self.types)
        self.rebuild()

    def _set_view(self, v):
        self.view = v
        self.t = 0.0
        if v == "saw":
            self._frame_saw()

    def _frame_saw(self):
        self.saw_cam.target = np.array([-4.0, -6.0, 2.0])
        self.saw_cam.yaw, self.saw_cam.pitch, self.saw_cam.dist = -100.0, 24.0, 72.0
        step = self.current_step()
        if step is not None and step.anim and step.anim.get("type") == "freehand":
            ext = self.saw_scene(step).get("extent")
            if ext is not None:
                lo, hi = ext
                size = float(np.linalg.norm(hi - lo))
                self.saw_cam.pitch = 50.0
                if size > 150.0:
                    # A long log: look at the cut, not the whole stick.
                    sc = self.saw_scene(step)
                    self.saw_cam.target = np.array([float(sc["bp"][0]), (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2])
                    self.saw_cam.dist = 110.0
                else:
                    self.saw_cam.target = (lo + hi) / 2
                    self.saw_cam.dist = max(40.0, size * 1.5)

    def _side(self) -> str:
        if self.view != "panel":
            return ""
        p = self.cam.pitch
        return "top" if p > 20 else "under" if p < -20 else "edge"

    def _look(self, side: str):
        """Swing round to the open side, the flat side underneath, or edge-on."""
        self.view = "panel"
        self.cam.pitch = {"top": 58.0, "under": -58.0, "edge": 4.0}[side]

    def _toggle_labels(self):
        self.labels = not self.labels

    def _toggle_explode(self):
        self.explode = 0.0 if self.explode else 1.0

    def _toggle_play(self):
        self.playing = not self.playing

    def _start_build(self):
        self.view = "panel"
        self.build_t = 0.0

    def _select(self, j):
        self.selected = j
        if self.layer is not None and self._hidden(j):
            self.layer = int(self.L.pieces[j].group.split()[1])
        self.step_i = 0
        self.recipe_scroll = 0
        self.t = 0.0

    def _set_step(self, k):
        if self.selected is None:
            return
        n = len(self.recipes[self.selected].steps)
        self.step_i = max(0, min(n - 1, k))
        self.t = 0.0
        step = self.current_step()
        if step is not None and step.anim and step.anim.get("type") in ("mitre", "freehand"):
            self._set_view("saw")
        elif step is not None and step.anim and step.anim.get("type") == "place":
            self.view = "panel"

    def _focus(self):
        if self.selected is None:
            return
        c = self.centres[self.selected]
        self.cam.target = np.array(c)
        self.cam.dist = max(12.0, self.cam.dist * 0.45)

    def _out_dir(self) -> Path:
        from .export import OUT
        return OUT

    def save_instructions(self):
        from .export import free_path, slug
        if self.make == "base":
            o = self.bo
            path = free_path(self._out_dir() / f"base-{o.pattern}-{o.prim_mat}-{o.sec_mat}-instructions.txt")
            lines = [self.L.title, f"{len(self.B.members)} members, {len(self.B.piers)} piers", ""]
        else:
            path = free_path(self._out_dir() / f"{slug(self.L)}-instructions.txt")
            lines = [self.L.title, f"{self.panel.label}, {self.mode}", ""]
        if self.prep:
            lines += [self.prep.name.upper()] + [f"  {s.title}: {s.text}" for s in self.prep.steps] + [""]
        for r in self.recipes:
            lines.append(f"PIECE {r.number}: {r.name}   ({r.summary})")
            lines += [f"    {a}: {b}" for a, b in r.dims]
            for k, s in enumerate(r.steps):
                wrapped = textwrap.fill(s.text, 96, initial_indent="       ", subsequent_indent="       ")
                lines.append(f"  {k + 1}. {s.title}")
                lines.append(wrapped)
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        self.status = f"Saved {path.name} in deliverables/infill"

    def save_csv(self):
        """Every piece of every triangle in the dome, with how many triangles use each."""
        from .export import OUT, write_csv
        if self.make == "base":
            path = bs.write_cut_list(self.B, OUT)
            self.status = f"Saved {path.name} in deliverables/infill"
            return
        o = self.options()
        layouts = [(layout(t, o), t.count) for t in self.types]
        path = write_csv(layouts, OUT / f"{self.mode}-{self.material}-whole-dome.csv")
        self.status = f"Saved {path.name} in deliverables/infill (all {sum(n for _l, n in layouts)} triangles)"

    def save_gallery(self):
        from .export import OUT, gallery, slug
        if self.make == "base":
            self.status = "Building every pattern with these materials..."
            self._present_status()
            rows = bs.compare(self.bo)
            self.prep.steps.insert(min(4, len(self.prep.steps)),
                                   rc.Step("info", "How the patterns compare (these materials)",
                                           "\n" + "\n".join("- " + r for r in rows)))
            path = bs.write_compare(self.bo, rows, OUT)
            self._show_summary()
            self.status = f"Compared {len(rows)} patterns; saved {path.name}. See the summary."
            return
        self.status = "Drawing every pattern for this material..."
        self._present_status()
        path = gallery(self.panel, self.options(), OUT / f"{slug(self.L)}-patterns.png")
        self.status = f"Saved {path.name} in deliverables/infill"

    def save_svg(self):
        from .export import OUT, slug, write_svg
        from .stock import plan
        if self.make == "base":
            path = bs.write_plan_svg(self.B, OUT)
            self.status = f"Saved {path.name} in deliverables/infill"
            return
        path = write_svg(self.L, plan([(self.L, 1)], "one").lines, OUT / f"{slug(self.L)}.svg")
        self.status = f"Saved {path.name} in deliverables/infill"

    # -------------------------------------------------------------- loop
    def draw(self, flip: bool = True):
        ctx = self.ctx
        ctx.screen.use()
        ctx.viewport = (0, 0, self.W, self.H)
        ctx.clear(0.11, 0.12, 0.14, 1.0)
        x, y, w, h = self.viewport()
        ctx.viewport = (x, y, w, h)
        ctx.enable(self.mgl.DEPTH_TEST)
        drawn = False
        if self.view == "saw":
            step = self.current_step()
            if step is not None:
                mvp = self.saw_cam.mvp(w / h)
                drawn = self.draw_saw(mvp, step, self.t)
        if not drawn:
            mvp = self.cam.mvp(w / h)
            self.draw_panel(mvp)
        self._saw_mvp = self.saw_cam.mvp(w / h)
        ctx.viewport = (0, 0, self.W, self.H)
        self.draw_overlay(self.cam.mvp(w / h))
        if flip:
            self.pg.display.flip()

    def handle(self, ev):
        pg = self.pg
        if ev.type == pg.QUIT:
            return False
        if ev.type == pg.VIDEORESIZE:
            self.W, self.H = ev.w, ev.h
            self.screen = pg.display.set_mode((self.W, self.H), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        if ev.type == pg.KEYDOWN:
            if ev.key == pg.K_ESCAPE:
                return False
            if ev.key == pg.K_SPACE:
                self._toggle_play()
            elif ev.key == pg.K_RIGHT:
                self._set_step(self.step_i + 1)
            elif ev.key == pg.K_LEFT:
                self._set_step(self.step_i - 1)
            elif ev.key == pg.K_TAB:
                self._set_view("saw" if self.view == "panel" else "panel")
            elif ev.key == pg.K_u:
                self._look("top" if self._side() == "under" else "under")
            elif ev.key == pg.K_l:
                self._toggle_labels()
            elif ev.key == pg.K_f:
                self._focus()
            elif ev.key == pg.K_HOME:
                self._frame_view(True)
            elif ev.key == pg.K_DOWN and self.selected is not None:
                self._select(min(len(self.recipes) - 1, self.selected + 1))
            elif ev.key == pg.K_UP and self.selected is not None:
                self._select(max(0, self.selected - 1))
        if ev.type == pg.MOUSEWHEEL:
            mx, my = pg.mouse.get_pos()
            if getattr(self, "list_rect", None) is not None and self.list_rect.collidepoint(mx, my):
                self.list_scroll = max(0, self.list_scroll - ev.y * 3)
            elif getattr(self, "recipe_rect", None) is not None and self.recipe_rect.collidepoint(mx, my):
                self.recipe_scroll = max(0, self.recipe_scroll - ev.y * 40)
            elif LEFT_W < mx < self.W - RIGHT_W:
                cam = self.saw_cam if self.view == "saw" else self.cam
                cam.dist *= 0.88 if ev.y > 0 else 1.0 / 0.88
                cam.dist = max(2.0, min(2000.0, cam.dist))
        if ev.type == pg.MOUSEBUTTONDOWN and ev.button in (1, 3):
            mx, my = ev.pos
            for r, cb in reversed(self.widgets):
                if r.collidepoint(mx, my) and ev.button == 1:
                    cb()
                    return True
            if LEFT_W < mx < self.W - RIGHT_W and my < self.H - BOTTOM_H:
                shift = pg.key.get_mods() & pg.KMOD_SHIFT
                self.dragging = ("pan" if (ev.button == 3 or shift) else "orbit", ev.pos, ev.pos)
        if ev.type == pg.MOUSEBUTTONUP and self.dragging:
            kind, start, _last = self.dragging
            self.dragging = None
            if kind == "orbit" and abs(ev.pos[0] - start[0]) + abs(ev.pos[1] - start[1]) < 4 \
                    and self.view == "panel":
                hit = self.pick(*ev.pos)
                if hit is not None:
                    self._select(hit)
                    self._scroll_to_selected()
        if ev.type == pg.MOUSEMOTION:
            if self.dragging:
                kind, start, last = self.dragging
                dx, dy = ev.pos[0] - last[0], ev.pos[1] - last[1]
                cam = self.saw_cam if self.view == "saw" else self.cam
                if kind == "orbit":
                    cam.yaw -= dx * 0.4
                    cam.pitch = max(-85.0, min(89.0, cam.pitch + dy * 0.4))
                else:
                    r, u, _f = cam.basis()
                    k = cam.dist * 0.0018
                    cam.target = cam.target - r * dx * k + u * dy * k
                self.dragging = (kind, start, ev.pos)
        return True

    def _scroll_to_selected(self):
        rows = max(1, int(self.H * 0.30) // 20)
        if self.selected < self.list_scroll or self.selected >= self.list_scroll + rows:
            self.list_scroll = max(0, self.selected - rows // 2)

    def run(self, frames: int | None = None, shot: str | None = None):
        pg = self.pg
        clock = pg.time.Clock()
        running = True
        k = 0
        while running:
            for ev in pg.event.get():
                if not self.handle(ev):
                    running = False
            dt = clock.tick(60) / 1000.0
            if self.playing:
                self.t = (self.t + dt / 4.0) % 1.0
            if self.build_t is not None:
                self.build_t += dt / max(2.0, len(self.L.pieces) * 0.12)
                if self.build_t > 1.0:
                    self.build_t = None
            if self.view == "panel" and not self.dragging:
                mx, my = pg.mouse.get_pos()
                if LEFT_W < mx < self.W - RIGHT_W and my < self.H - BOTTOM_H and k % 6 == 0:
                    self.hover = self.pick(mx, my)
            self.draw()
            k += 1
            if frames is not None and k >= frames:
                if shot:
                    self.screenshot(shot)
                running = False
        pg.quit()

    def screenshot(self, path: str):
        self.draw(flip=False)
        self.draw(flip=False)
        data = self.ctx.screen.read(viewport=(0, 0, self.W, self.H), components=3)
        from PIL import Image
        img = Image.frombytes("RGB", (self.W, self.H), data).transpose(Image.FLIP_TOP_BOTTOM)
        img.save(path)
        self.pg.display.flip()


def validate_meshes() -> None:
    """Every material's pieces turn into closed, finite triangles, and every
    piece has a recipe -- no window needed."""
    from .patterns import OPTIONS as OPTS
    panel = solve(Spec())["types"][0]
    for material, (_name, kind, *_rest) in MATERIALS.items():
        for mode in ("fill", "cover"):
            arr = OPTS[kind]["arrangements"][0]
            lay = (OPTS[kind]["lays"] or ["flipflop"])[0]
            L = layout(panel, valid(Options(material, arr, lay, mode, 0, 12.0, 45.0, "open",
                                            1.5, 3.0, "cut", 1)))
            R = rc.recipes(L)
            assert len(R) == len(L.pieces), (material, mode)
            for p in L.pieces:
                if p.solid is None:
                    continue
                t = solid_tris(p.solid, (1, 1, 1, 1))
                assert len(t) and len(t) % 3 == 0 and np.isfinite(t).all(), (material, mode, p.group)


def main() -> int:
    app = App()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
