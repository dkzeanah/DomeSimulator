"""The Dome Forge window: a scoped, single-dome layer editor in 3D.

Deliberately not a world. There is one dome at the origin, an orbit
camera, and a layer panel -- the shape of a character creator, aimed at a
building.

The panel is drawn onto a pygame surface and composited over the 3D scene
as a texture. Layout is computed once per frame by :meth:`layout`, which
returns both what to draw and where the clickable regions are, so the
picture and the hit-testing can never drift apart.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from presenter.world import Batch

from .build import (build_scene, face_edge_classes, pick_face, scene_stats,
                    tint, TINTS)
from .catalog import (FILL_BY_KEY, FILL_KEYS, PROFILE_BY_KEY, PROFILE_KEYS,
                      strut_label, strut_profile)
from .groups import (JOINT_BY_KEY, JOINT_KEYS, group_centre, hourglasses,
                     pentagons)
from .jigs import STEPS, emit_jig, jig_specs, step_lines
from .layers import LAYER_KINDS, KIND_BY_KEY, LayerStack, default_stack
from .panel import build_panel


SCENE_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
uniform mat4 u_mvp;
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
    float specular = pow(max(dot(n, h), 0.0), 38.0);
    float rim = pow(1.0 - max(dot(n, v), 0.0), 2.5);
    vec3 lit = v_color.rgb * (0.34 + 0.70 * diffuse);
    lit += vec3(0.74, 0.88, 1.0) * rim * 0.20;
    lit += vec3(1.0, 0.90, 0.72) * specular * 0.25;
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
void main() { frag_color = texture(u_texture, v_uv); }
"""


BG = (0.020, 0.032, 0.052, 1.0)
# Controls sit down the left, the layer stack down the right, and the dome
# gets the whole middle. Two narrow columns fit far more than one wide one
# without ever pushing content off the bottom of a big screen.
PANEL_W = 330
RIGHT_W = 340
# Sliders carry their label above the track rather than beside it, so long
# plain-language labels never collide with the value or the bar itself.
SLIDER_H = 28
INK = (232, 240, 248)
DIM = (150, 172, 192)
ACCENT = (88, 213, 255)
WARN = (245, 185, 93)
PANEL_BG = (12, 22, 34, 232)
ROW_BG = (24, 40, 57)
ROW_SEL = (37, 73, 98)


def perspective(fov_degrees: float, aspect: float, near: float, far: float):
    f = 1.0 / math.tan(math.radians(fov_degrees) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at(eye, target, up_hint=(0.0, 0.0, 1.0)):
    def unit(v):
        n = float(np.linalg.norm(v))
        return v / n if n > 1e-12 else v
    forward = unit(np.asarray(target, dtype=np.float32) - eye)
    right = unit(np.cross(forward, np.asarray(up_hint, dtype=np.float32)))
    up = unit(np.cross(right, forward))
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = right
    m[1, :3] = up
    m[2, :3] = -forward
    m[0, 3] = -float(np.dot(right, eye))
    m[1, 3] = -float(np.dot(up, eye))
    m[2, 3] = float(np.dot(forward, eye))
    return m


def _ray_triangle(origin, direction, a, b, c):
    """Moller-Trumbore. Returns the distance along the ray, or None."""
    edge1, edge2 = np.subtract(b, a), np.subtract(c, a)
    pvec = np.cross(direction, edge2)
    det = float(np.dot(edge1, pvec))
    if abs(det) < 1e-12:
        return None
    inv = 1.0 / det
    tvec = np.subtract(origin, a)
    u = float(np.dot(tvec, pvec)) * inv
    if u < 0.0 or u > 1.0:
        return None
    qvec = np.cross(tvec, edge1)
    v = float(np.dot(direction, qvec)) * inv
    if v < 0.0 or u + v > 1.0:
        return None
    distance = float(np.dot(edge2, qvec)) * inv
    return distance if distance > 1e-6 else None


class GpuMesh:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.buffer = ctx.buffer(reserve=8 * 1024 * 1024, dynamic=True)
        self.vao = self._vao()

    def _vao(self):
        return self.ctx.vertex_array(
            self.program,
            [(self.buffer, "3f 3f 4f", "in_position", "in_normal", "in_color")],
        )

    def draw(self, batch):
        if not batch.v:
            return
        data = np.asarray(batch.v, dtype="f4")
        if data.nbytes > self.buffer.size:
            self.vao.release()
            self.buffer.release()
            self.buffer = self.ctx.buffer(
                reserve=int(data.nbytes * 1.4), dynamic=True
            )
            self.vao = self._vao()
        self.buffer.write(data.tobytes())
        self.vao.render(vertices=len(batch.v) // 10)


class DomeForgeApp:
    """One dome, many layers."""

    def __init__(self, size=(1600, 900), fullscreen=False, hidden=False,
                 preset: Path | None = None):
        try:
            import pygame
            import moderngl
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Dome Forge needs pygame and moderngl. Install with: "
                "py -3.12 -m pip install pygame moderngl numpy"
            ) from exc
        self.pygame = pygame
        self.moderngl = moderngl
        pygame.init()
        pygame.font.init()
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        display_size = size
        if fullscreen:
            flags |= pygame.FULLSCREEN
            display_size = (0, 0)
        else:
            flags |= pygame.RESIZABLE
        if hidden and hasattr(pygame, "HIDDEN"):
            flags |= pygame.HIDDEN
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.set_caption("Dome Forge - layered dome builder")
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
        self.opaque = GpuMesh(self.ctx, self.scene_program)
        self.translucent = GpuMesh(self.ctx, self.scene_program)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
        self.overlay_buffer = self.ctx.buffer(quad.tobytes())
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program, [(self.overlay_buffer, "2f", "in_position")]
        )
        self.overlay_texture = None
        self.overlay_size = (0, 0)

        self.font = pygame.font.SysFont("Segoe UI", 15)
        self.font_small = pygame.font.SysFont("Segoe UI", 13)
        self.font_bold = pygame.font.SysFont("Segoe UI Semibold", 16)
        # A fixed-width face for the cut list, so columns of numbers line up.
        self.font_mono = pygame.font.SysFont("Consolas", 13)

        self.stack = LayerStack.load(preset) if preset else default_stack()
        self.preset_path = Path(preset) if preset else Path("dome_forge_preset.json")

        self.mode = "dome"            # "dome", "jigs", or "panel"
        self.jig_index = 0            # which of the two jigs
        self.step_index = 0           # which build step
        # Selection is a set so several triangles can be worked at once;
        # `primary_face` is whichever one the detail panel describes.
        self.stack.selected_faces = set()
        self.stack.explode = 0.0
        self.explode_amount = 0.55
        # The bench panel in the Panel Creator: three strut choices that
        # need not match, plus one fill.
        self.bench_struts = ["log_half", "lumber_2x2", "log_quarter"]
        self.bench_fill = "polycarbonate"
        self.bench_edge = 0
        # Which of the bench panel's three struts are selected.
        self.bench_selection: set[int] = set()
        self.group_kind = "pentagon"   # or "hourglass"
        self.group_index = 0
        self.scroll_right = 0
        self.picker = None
        # An inline name box, so saving a design can ask what to call it
        # without dragging in a whole dialog toolkit.
        self.prompt = None
        self.yaw, self.pitch, self.distance = 38.0, 22.0, 15.0
        self.playing = True
        self.clock_t = 0.0
        self.running = True
        self.dragging = None          # active slider drag
        self.orbiting = False
        self.press_at = None
        self.message = "Drag to orbit, click a triangle to select it, scroll to zoom."
        self.message_at = time.monotonic()
        self.scroll = 0

    # -- helpers ---------------------------------------------------------

    def notify(self, text: str) -> None:
        self.message = text
        self.message_at = time.monotonic()

    def jig_spec(self):
        specs = jig_specs(
            self.stack.settings.radius,
            self._frame_param("width", 0.089),
            self._frame_param("thickness", 0.038),
        )
        return specs[self.jig_index % len(specs)]

    def _frame_param(self, key: str, fallback: float) -> float:
        """Read board size off the triangle-frame layer, so the jig always
        builds the boards the dome is actually made of."""
        for layer in self.stack.layers:
            if layer.kind == "triangle_frames":
                return float(layer.get(key))
        return fallback

    def build_jig_scene(self):
        opaque, translucent = Batch(), Batch()
        step = STEPS[self.step_index % len(STEPS)]
        emit_jig(opaque, translucent, self.jig_spec(), step.stage,
                 self.clock_t, tint)
        # A bench under the jig, so it reads as sitting on something
        # rather than floating in the dark. Kept modest -- a big slab
        # just swallows the light.
        if step.stage != "deficit":
            opaque.box((0.0, -0.7, -0.30), (5.2, 6.4, 0.16),
                       tint("charcoal", 1.0))
        return opaque, translucent

    def bench_corners(self):
        """The bench panel's three corners, taken from the dome's own
        isosceles face so what you design on the bench is what you get."""
        spec = jig_specs(self.stack.settings.radius)[1]
        pts = np.array(spec.flat, dtype=np.float64)
        pts = pts - pts.mean(axis=0)
        return [np.array([p[0], p[1], 0.0]) for p in pts]

    def build_panel_scene(self):
        """One panel alone on a bench, with its individual struts
        selectable the same way the dome's triangles are."""
        from .panel import build_panel_selective

        opaque, translucent = Batch(), Batch()
        corners = self.bench_corners()
        build_panel_selective(
            opaque, translucent, corners, self.bench_struts,
            self.bench_fill, tint, seam=0.004,
            highlight_edges=self.bench_selection,
        )
        opaque.box((0.0, 0.0, -0.36), (5.0, 5.0, 0.16), tint("charcoal", 1.0))
        return opaque, translucent

    def pick_bench_edge(self, pos, width: int, height: int) -> int:
        """Which of the bench panel's three struts is under the cursor."""
        from .panel import panel_strut_quads

        origin, direction = self.ray_from(pos, width, height)
        quads = panel_strut_quads(self.bench_corners(), self.bench_struts,
                                  seam=0.004)
        best, best_t = -1, float("inf")
        for index, quad in enumerate(quads):
            for tri in ((quad[0], quad[1], quad[2]),
                        (quad[0], quad[2], quad[3])):
                hit = _ray_triangle(origin, direction, *tri)
                if hit is not None and hit < best_t:
                    best_t, best = hit, index
        return best

    @property
    def selection(self) -> set:
        return self.stack.selected_faces

    @property
    def primary_face(self) -> int:
        """The one triangle the detail panel describes. With several
        selected this is simply the lowest index, so the panel is stable
        rather than jumping about as the set changes."""
        return min(self.selection) if self.selection else -1

    @primary_face.setter
    def primary_face(self, value: int) -> None:
        self.stack.selected_faces = {value} if value is not None and value >= 0 else set()

    @property
    def has_selection(self) -> bool:
        if self.mode == "panel":
            return bool(self.bench_selection)
        return bool(self.selection) and self.mode in ("dome", "groups")

    def toolbar_action(self, action: str) -> None:
        """One entry point for the toolbar, whether it was clicked or
        typed -- so a button and its shortcut can never drift apart."""
        if action in ("sel_fill", "sel_strut"):
            self._open_catalog_picker(action, None)
        elif action == "sel_roll":
            self._roll_selection(1, False)
        elif action == "sel_flip":
            self._roll_selection(0, True)
        elif action == "sel_explode_up":
            self.explode_amount = min(3.0, self.explode_amount + 0.35)
            self.notify(f"Pop-out {self.explode_amount:.2f} m.")
        elif action == "sel_explode_down":
            self.explode_amount = max(0.0, self.explode_amount - 0.35)
            self.notify(f"Pop-out {self.explode_amount:.2f} m.")
        elif action == "sel_clear":
            if self.mode == "panel":
                self.bench_selection = set()
            else:
                self.stack.selected_faces = set()

    def cycle_variant(self, step: int) -> None:
        """Step the selection through the variants of whatever it is.

        A selected strut walks the profile catalogue; a selected triangle
        walks the fills. Whichever kind of component is selected, the
        arrows move it to the next one of its own kind.
        """
        from .catalog import STRUT_PROFILES, format_strut, parse_strut
        if self.mode == "panel":
            keys = [p.key for p in STRUT_PROFILES]
            for edge in sorted(self.bench_selection):
                key, spin, flip = parse_strut(self.bench_struts[edge])
                index = keys.index(key) if key in keys else 0
                chosen = keys[(index + step) % len(keys)]
                self.bench_struts[edge] = format_strut(chosen, spin, flip)
            shown = parse_strut(self.bench_struts[min(self.bench_selection)])[0]
            self.notify(f"Strut: {strut_label(self.bench_struts[min(self.bench_selection)])}")
            return
        keys = list(FILL_KEYS)
        assignments = self.stack.assignments
        current = assignments.fill_for(self.primary_face)
        index = keys.index(current) if current in keys else 0
        chosen = keys[(index + step) % len(keys)]
        for face in self.selection:
            assignments.face_fill[str(face)] = chosen
        self.notify(f"Fill: {FILL_BY_KEY[chosen].label}  "
                    f"({len(self.selection)} triangle(s))")

    def pick_component(self, pos, width: int, height: int,
                       additive: bool) -> None:
        """Click a component in whichever editor is open.

        Every mode that shows parts lets you select them the same way:
        the dome picks triangles, the Panel Creator picks individual
        struts, and the group editors pick triangles but only from the
        group you are currently working on -- so a stray click cannot
        drag an unrelated face into the selection.
        """
        if self.mode == "panel":
            hit = self.pick_bench_edge(pos, width, height)
            if hit < 0:
                if not additive:
                    self.bench_selection = set()
                self.notify("No strut under the cursor.")
                return
            if additive:
                self.bench_selection ^= {hit}
            else:
                self.bench_selection = {hit}
            if self.bench_selection:
                self.bench_edge = min(self.bench_selection)
            self.notify(f"{len(self.bench_selection)} strut(s) selected.")
            return

        hit = self.pick_at(pos, width, height)
        if self.mode == "groups" and hit >= 0:
            if hit not in self.group_faces():
                self.notify("That triangle is not in this group -- step to "
                            "it, or work in DOME mode.")
                return
        self.toggle_face(hit, additive)
        count = len(self.selection)
        if hit < 0:
            self.notify("No triangle under the cursor.")
        elif count > 1:
            self.notify(f"{count} triangles selected "
                        f"(ctrl-click to add or remove).")
        else:
            self.notify(f"Selected triangle #{hit}. Ctrl-click to add more.")

    def toggle_face(self, index: int, additive: bool) -> None:
        """Click selects; ctrl-click adds to or removes from the set."""
        if index < 0:
            if not additive:
                self.stack.selected_faces = set()
            return
        if additive:
            if index in self.stack.selected_faces:
                self.stack.selected_faces.discard(index)
            else:
                self.stack.selected_faces.add(index)
        else:
            self.stack.selected_faces = {index}

    def current_group(self):
        items = pentagons() if self.group_kind == "pentagon" else hourglasses()
        return items[self.group_index % len(items)], items

    def group_faces(self) -> tuple[int, ...]:
        group, _ = self.current_group()
        return tuple(group.faces)

    def camera(self):
        if self.mode == "groups":
            # Look straight at whichever group is selected, so stepping
            # through them never leaves you hunting for the next one.
            from .build import DomeContext
            ctx = DomeContext(self.stack.settings.radius)
            centre = group_centre(ctx, self.group_faces())
            direction = centre / max(1e-6, float(np.linalg.norm(centre)))
            eye = centre + direction * self.distance
            up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            forward = centre - eye
            forward = forward / max(1e-9, float(np.linalg.norm(forward)))
            right = np.cross(forward, up)
            if float(np.linalg.norm(right)) < 1e-6:
                right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            right = right / max(1e-9, float(np.linalg.norm(right)))
            pan = right * (self.distance * 0.20)
            return ((eye - pan).astype(np.float32),
                    (centre - pan).astype(np.float32))
        if self.mode == "panel":
            pitch = math.radians(max(-20.0, min(88.0, self.pitch)))
            yaw = math.radians(self.yaw)
            target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            eye = target + np.array([
                self.distance * math.cos(pitch) * math.cos(yaw),
                self.distance * math.cos(pitch) * math.sin(yaw),
                self.distance * math.sin(pitch),
            ], dtype=np.float32)
            forward = target - eye
            forward = forward / max(1e-6, float(np.linalg.norm(forward)))
            right = np.cross(forward, np.array([0.0, 0.0, 1.0], dtype=np.float32))
            right = right / max(1e-6, float(np.linalg.norm(right)))
            pan = right * (self.distance * 0.17)
            return eye - pan, target - pan
        if self.mode == "jigs":
            pitch = math.radians(max(-12.0, min(88.0, self.pitch)))
            yaw = math.radians(self.yaw)
            target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            eye = target + np.array([
                self.distance * math.cos(pitch) * math.cos(yaw),
                self.distance * math.cos(pitch) * math.sin(yaw),
                self.distance * math.sin(pitch),
            ], dtype=np.float32)
            # The layer panel covers the left of the window, so pan the
            # camera left to sit the jig in the part actually visible.
            forward = target - eye
            forward = forward / max(1e-6, float(np.linalg.norm(forward)))
            right = np.cross(forward, np.array([0.0, 0.0, 1.0], dtype=np.float32))
            right = right / max(1e-6, float(np.linalg.norm(right)))
            pan = right * (self.distance * 0.17)
            return eye - pan, target - pan
        radius = self.stack.settings.radius
        pitch = math.radians(max(-12.0, min(84.0, self.pitch)))
        yaw = math.radians(self.yaw)
        target = np.array([0.0, 0.0, radius * 0.35], dtype=np.float32)
        eye = target + np.array([
            self.distance * math.cos(pitch) * math.cos(yaw),
            self.distance * math.cos(pitch) * math.sin(yaw),
            self.distance * math.sin(pitch),
        ], dtype=np.float32)
        return eye, target

    # -- layout: the single source of truth for drawing AND hit-testing ---

    def layout(self, width: int, height: int):
        """Return (rows, regions, left_height, right_height).

        ``rows`` are draw instructions; ``regions`` are (rect, action,
        payload) for mouse hits. Both come from the same running ``y`` in
        each column, so what you see and what you can click can never
        disagree -- including while a column is scrolled.
        """
        rows: list[tuple] = []
        regions: list[tuple] = []
        right_height = self._layout_right(rows, regions, width, height)
        x, w = 10, PANEL_W - 20
        y = 10 - self.scroll

        rows.append(("title", (x, y), "DOME FORGE"))
        y += 26
        rect = (x, y, w, 20)
        label = {"dome": "Mode: DOME", "groups": "Mode: GROUPS",
                 "jigs": "Mode: JIG SHOP",
                 "panel": "Mode: PANEL CREATOR"}[self.mode]
        rows.append(("button", rect, f"{label}   (m cycles)"))
        regions.append((rect, "toggle_mode", None))
        y += 26

        if self.mode == "jigs":
            out = self._layout_jigs(rows, regions, x, y, w)
            self._layout_toolbar(rows, regions, width, height)
            self._layout_picker(rows, regions, width, height)
            self._layout_prompt(rows, regions, width, height)
            return out
        if self.mode == "panel":
            out = self._layout_panel(rows, regions, x, y, w)
            self._layout_toolbar(rows, regions, width, height)
            self._layout_picker(rows, regions, width, height)
            self._layout_prompt(rows, regions, width, height)
            return out
        if self.mode == "groups":
            out = self._layout_groups(rows, regions, x, y, w)
            self._layout_toolbar(rows, regions, width, height)
            self._layout_picker(rows, regions, width, height)
            self._layout_prompt(rows, regions, width, height)
            return out
        stats = scene_stats(self.stack)
        rows.append(("small", (x, y),
                     f"{stats['struts']} struts  {stats['panels']} panels  "
                     f"{stats['hubs']} hubs"))
        y += 17
        rows.append(("small", (x, y),
                     f"r={stats['radius']:.2f}m  floor={stats['footprint']:.1f}m2"))
        y += 17
        rows.append(("small", (x, y),
                     f"short {stats['short_len']:.2f}m  long {stats['long_len']:.2f}m"))
        y += 22

        # Dome-wide controls
        rows.append(("head", (x, y), "DOME"))
        y += 20
        for key, label, low, high, value, shown in (
            ("radius", "Radius", 1.5, 9.0, self.stack.settings.radius,
             f"{self.stack.settings.radius:.2f}m"),
            ("cut_start", "Cut from", 0.0, 360.0, self.stack.settings.cut_start,
             f"{self.stack.settings.cut_start:.0f}deg"),
            ("cut_sweep", "Cut width", 0.0, 300.0, self.stack.settings.cut_sweep,
             f"{self.stack.settings.cut_sweep:.0f}deg"),
        ):
            rect = (x, y, w, SLIDER_H)
            rows.append(("slider", rect, (label, value, low, high, shown)))
            regions.append((rect, "dome_slider", (key, low, high)))
            y += SLIDER_H + 5
        rect = (x, y, w, 18)
        rows.append(("toggle", rect,
                     ("Cutaway view", self.stack.settings.cut_enabled)))
        regions.append((rect, "cut_toggle", None))
        y += 26

        # Whichever triangle was last clicked in the 3D view.
        assignments = self.stack.assignments
        face = self.primary_face
        rows.append(("head", (x, y), "SELECTED TRIANGLE"))
        y += 20
        if face < 0:
            rows.append(("small", (x, y),
                         "Click a triangle in the 3D view to select it."))
            y += 20
        else:
            classes = face_edge_classes(self.stack, face)
            shape = ("equilateral" if classes.count("LONG") == 3
                     else "isosceles")
            rows.append(("small", (x, y), f"Face #{face}  ({shape})"))
            y += 18
            rect = (x, y, w, 18)
            current = FILL_BY_KEY[assignments.fill_for(face)].label
            rows.append(("choice", rect, ("Fill", current)))
            regions.append((rect, "face_fill", None))
            y += 22
            triple = assignments.strut_triple(face, classes)
            for i in range(3):
                rect = (x, y, w, 18)
                name = strut_label(triple[i])
                rows.append(("choice", rect,
                             (f"Edge {i + 1} ({classes[i].lower()})", name)))
                regions.append((rect, "face_strut", (i,)))
                y += 22
            for label_text, action in (
                ("Apply fill to all", "apply_fill_all"),
                (f"Apply all to every {shape}", "apply_shape"),
                ("Reset this triangle", "reset_face"),
            ):
                rect = (x, y, w, 20)
                rows.append(("button", rect, label_text))
                regions.append((rect, action, None))
                y += 24
        y += 6
        rows.append(("head", (x, y), "DEFAULTS FOR EVERY TRIANGLE"))
        y += 20
        for label_text, key in (("Fill", "fill"),
                                ("Long-edge strut", "strut_long"),
                                ("Short-edge strut", "strut_short")):
            rect = (x, y, w, 18)
            value = getattr(assignments, key)
            shown = (FILL_BY_KEY[value].label if key == "fill"
                     else strut_label(value))
            rows.append(("choice", rect, (label_text, shown)))
            regions.append((rect, "default_choice", (key,)))
            y += 22
        y += 6

        self._layout_toolbar(rows, regions, width, height)
        self._layout_picker(rows, regions, width, height)
        self._layout_prompt(rows, regions, width, height)
        return rows, regions, y + self.scroll + 20, right_height

    def _layout_right(self, rows, regions, width: int, height: int) -> int:
        """The right-hand column: the layer stack and the selected layer's
        own controls. Only the dome has layers, so the other modes leave
        this column empty and give the space back to the 3D view."""
        if self.mode != "dome":
            return 0
        x = width - RIGHT_W + 10
        w = RIGHT_W - 20
        y = 10 - self.scroll_right

        rows.append(("head", (x, y), "LAYERS  (top draws last)"))
        y += 20
        for display_index, layer in enumerate(reversed(self.stack.layers)):
            index = len(self.stack.layers) - 1 - display_index
            rect = (x, y, w, 20)
            rows.append(("layer", rect,
                         (layer, index == self.stack.selected)))
            regions.append(((x + 2, y + 2, 16, 16), "toggle_layer", index))
            regions.append(((x + 20, y, w - 82, 20), "select_layer", index))
            regions.append(((x + w - 60, y, 18, 20), "move_up", index))
            regions.append(((x + w - 40, y, 18, 20), "move_down", index))
            regions.append(((x + w - 20, y, 18, 20), "delete_layer", index))
            y += 21
            orect = (x + 20, y, w - 24, 10)
            rows.append(("opacity", orect, layer.opacity))
            regions.append((orect, "layer_opacity", index))
            y += 15

        y += 6
        rect = (x, y, w, 22)
        rows.append(("button", rect, "+ Add layer"))
        regions.append((rect, "open_add", None))
        y += 28

        active = self.stack.active
        if active is not None:
            rows.append(("head", (x, y), active.name.upper()))
            y += 19
            for line in self._wrap(active.spec.blurb, 45):
                rows.append(("small", (x, y), line))
                y += 15
            y += 4
            for param in active.spec.params:
                value = active.get(param.key)
                if param.kind == "bool":
                    rect = (x, y, w, 18)
                    rows.append(("toggle", rect, (param.label, bool(value))))
                    regions.append((rect, "param_bool", (param.key,)))
                    y += 23
                elif param.kind == "choice":
                    rect = (x, y, w, 18)
                    rows.append(("choice", rect, (param.label, str(value))))
                    regions.append((rect, "param_choice", (param.key,)))
                    y += 23
                else:
                    rect = (x, y, w, SLIDER_H)
                    rows.append(("slider", rect,
                                 (param.label, float(value),
                                  param.low, param.high, param.format(value))))
                    regions.append((rect, "param_slider",
                                    (param.key, param.low, param.high)))
                    y += SLIDER_H + 5
        return y + self.scroll_right + 20

    def _layout_toolbar(self, rows, regions, width: int, height: int) -> None:
        """A floating bar that appears over the 3D view whenever anything
        is selected, and acts on the whole selection.

        Strut rotation lives here rather than in the strut list: rolling a
        piece is something you do *to* the thing you already picked, not a
        different thing to pick. Keeping it here also drops the strut list
        back to 18 honest profiles instead of 72 near-duplicates.
        """
        if self.mode == "panel":
            count = len(self.bench_selection)
            if not count:
                return
            buttons = [
                ("Strut... (T)", "sel_strut"),
                ("Roll 90 (R)", "sel_roll"),
                ("Mirror (X)", "sel_flip"),
                ("Clear (Del)", "sel_clear"),
            ]
            label = (f"{count} struts selected" if count > 1
                     else f"Edge {min(self.bench_selection) + 1}")
        else:
            count = len(self.selection)
            if not count or self.mode not in ("dome", "groups"):
                return
            buttons = [
                ("Fill... (F)", "sel_fill"),
                ("Strut... (T)", "sel_strut"),
                ("Roll 90 (R)", "sel_roll"),
                ("Mirror (X)", "sel_flip"),
                ("Pop + (])", "sel_explode_up"),
                ("Pop - ([)", "sel_explode_down"),
                ("Clear (Del)", "sel_clear"),
            ]
            label = (f"{count} selected" if count > 1
                     else f"Triangle #{self.primary_face}")
        pad, gap, h = 12, 6, 26
        widths = [max(74, self.font_small.size(text)[0] + 22)
                  for text, _ in buttons]
        label_w = self.font_small.size(label)[0] + 16
        total = pad * 2 + label_w + sum(widths) + gap * len(buttons)
        left = max(PANEL_W + 12, (width - total) // 2)
        top = height - 78
        rows.append(("panel_bg", (left, top - 20, total, h + pad * 2 + 14), None))
        rows.append(("small", (left + pad, top - 16),
                     "<- -> steps through variants"))
        rows.append(("small", (left + pad, top + pad + 2), label))
        x = left + pad + label_w
        for (text, action), bw in zip(buttons, widths):
            rect = (x, top + pad - 4, bw, h)
            rows.append(("button", rect, text))
            regions.append((rect, action, None))
            x += bw + gap

    def _layout_prompt(self, rows, regions, width: int, height: int) -> None:
        """The name box shown while saving a design."""
        if not self.prompt:
            return
        box_w, box_h = 460, 108
        ox, oy = (width - box_w) // 2, (height - box_h) // 2
        rows.append(("panel_bg", (ox, oy, box_w, box_h), None))
        rows.append(("head", (ox + 14, oy + 12), self.prompt["title"]))
        rows.append(("field", (ox + 14, oy + 38, box_w - 28, 26),
                     self.prompt["value"]))
        rows.append(("small", (ox + 14, oy + 70),
                     "Type a name, Enter to save, Escape to cancel."))

    def _layout_picker(self, rows, regions, width: int, height: int) -> None:
        """A real dropdown. Cycling one click at a time through 19 fills or
        18 strut profiles is unusable, so a choice opens a list instead --
        laid out in as many columns as the window can take."""
        picker = self.picker
        if not picker:
            return
        options = picker["options"]
        row_h, col_w = 22, 250
        usable = max(1, (height - 150) // row_h)
        columns = max(1, min(4, math.ceil(len(options) / usable)))
        per_column = math.ceil(len(options) / columns)
        box_w = columns * col_w + 20
        box_h = min(len(options), per_column) * row_h + 62
        ox = max(10, (width - box_w) // 2)
        oy = max(10, (height - box_h) // 2)
        rows.append(("panel_bg", (ox, oy, box_w, box_h), None))
        rows.append(("head", (ox + 12, oy + 10), picker["title"]))
        for index, (key, label) in enumerate(options):
            column, row = divmod(index, per_column)
            rect = (ox + 10 + column * col_w, oy + 34 + row * row_h,
                    col_w - 8, row_h - 2)
            rows.append(("option", rect, (label, key == picker.get("current"))))
            regions.append((rect, "picker_choose", key))
        rect = (ox + 10, oy + box_h - 26, 110, 20)
        rows.append(("button", rect, "Cancel"))
        regions.append((rect, "picker_cancel", None))

    def _layout_jigs(self, rows, regions, x, y, w):
        """The Jig Shop panel: which jig, which step, and the exact numbers
        for that step."""
        spec = self.jig_spec()
        step = STEPS[self.step_index % len(STEPS)]

        rect = (x, y, w, 20)
        rows.append(("button", rect, f"{spec.label}   (Tab)"))
        regions.append((rect, "next_jig", None))
        y += 26

        rows.append(("head", (x, y),
                     f"STEP {self.step_index + 1} OF {len(STEPS)}"))
        y += 20
        rows.append(("small", (x, y), step.title))
        y += 18
        for line in self._wrap(step.detail, 44):
            rows.append(("small", (x, y), line))
            y += 15
        y += 8

        half = (w - 6) // 2
        back = (x, y, half, 22)
        forward = (x + half + 6, y, half, 22)
        rows.append(("button", back, "< Back"))
        rows.append(("button", forward, "Next >"))
        regions.append((back, "step_back", None))
        regions.append((forward, "step_forward", None))
        y += 30

        rows.append(("head", (x, y), "CUT LIST FOR THIS STEP"))
        y += 20
        for line in step_lines(spec, step):
            rows.append(("mono", (x, y), line))
            y += 16
        y += 8
        rows.append(("small", (x, y),
                     f"Dome radius {self.stack.settings.radius:.2f} m -- change"))
        y += 15
        rows.append(("small", (x, y), "it in DOME mode and every number here"))
        y += 15
        rows.append(("small", (x, y), "follows."))
        y += 20
        return rows, regions, y + self.scroll + 20, 0

    def _layout_groups(self, rows, regions, x, y, w):
        """Edit a whole sub-assembly at once: a pentagon of five
        triangles, or an hourglass of two meeting point to point."""
        group, items = self.current_group()
        assignments = self.stack.assignments
        pentagon = self.group_kind == "pentagon"

        rect = (x, y, w, 20)
        rows.append(("button", rect,
                     f"{'PENTAGONS' if pentagon else 'HOURGLASSES'}   (Tab)"))
        regions.append((rect, "toggle_group_kind", None))
        y += 26

        half = (w - 6) // 2
        back = (x, y, half, 22)
        forward = (x + half + 6, y, half, 22)
        rows.append(("button", back, "< Prev"))
        rows.append(("button", forward, "Next >"))
        regions.append((back, "group_back", None))
        regions.append((forward, "group_forward", None))
        y += 28

        rows.append(("head", (x, y),
                     f"{'PENTAGON' if pentagon else 'HOURGLASS'} "
                     f"{self.group_index % len(items) + 1} OF {len(items)}"))
        y += 20
        if pentagon:
            detail = ("Five isosceles triangles meeting at their apex -- "
                      "the point between their two short sides. Six of "
                      "these ring a hemisphere.")
        else:
            detail = ("Two equilateral triangles touching at exactly one "
                      "vertex, point to point. They fill the gaps between "
                      "the pentagons; ten waists per hemisphere.")
        for line in self._wrap(detail, 44):
            rows.append(("small", (x, y), line))
            y += 15
        rows.append(("mono", (x, y),
                     f"faces {', '.join(str(f) for f in group.faces)}"))
        y += 18
        rows.append(("mono", (x, y),
                     f"{'apex' if pentagon else 'waist'} vertex "
                     f"{group.vertex if pentagon else group.waist}"))
        y += 22

        if not pentagon:
            rows.append(("head", (x, y), "WAIST JOINT"))
            y += 20
            joint = JOINT_BY_KEY[assignments.joint_for(group.index)]
            rect = (x, y, w, 18)
            rows.append(("choice", rect, ("Joint", joint.label)))
            regions.append((rect, "waist_joint", None))
            y += 22
            for line in self._wrap(joint.blurb, 44):
                rows.append(("small", (x, y), line))
                y += 15
            y += 4
            rect = (x, y, w, 20)
            rows.append(("button", rect, "Use this joint everywhere"))
            regions.append((rect, "joint_all", None))
            y += 26

        library = self.stack.designs
        saved = library.groups_of("pentagon" if pentagon else "hourglass")
        rows.append(("head", (x, y), "DESIGN LIBRARY"))
        y += 20
        rect = (x, y, w, 22)
        rows.append(("button", rect,
                     f"Save this {'pentagon' if pentagon else 'hourglass'}..."))
        regions.append((rect, "save_group_design", None))
        y += 26
        rect = (x, y, w, 22)
        rows.append(("button", rect, f"Load a saved design  ({len(saved)})"))
        regions.append((rect, "load_group_design", None))
        y += 26
        if pentagon:
            rect = (x, y, w, 22)
            rows.append(("button", rect, "Load a ready-made pentagon..."))
            regions.append((rect, "pentagon_preset", None))
            y += 28

        rows.append(("head", (x, y), "WHOLE GROUP"))
        y += 20
        first = group.faces[0]
        classes = face_edge_classes(self.stack, first)
        rect = (x, y, w, 18)
        rows.append(("choice", rect,
                     ("Fill", FILL_BY_KEY[assignments.fill_for(first)].label)))
        regions.append((rect, "group_fill", None))
        y += 22
        triple = assignments.strut_triple(first, classes)
        rect = (x, y, w, 18)
        rows.append(("choice", rect,
                     ("Strut", strut_label(triple[0]))))
        regions.append((rect, "group_strut", None))
        y += 24
        rows.append(("small", (x, y), "Changes apply to every triangle"))
        y += 15
        rows.append(("small", (x, y), "in this group at once."))
        y += 22
        return rows, regions, y + self.scroll + 20, 0

    def _layout_panel(self, rows, regions, x, y, w):
        """The Panel Creator: build one panel out of any three struts."""
        rows.append(("small", (x, y),
                     "Design one panel on the bench. The three edges"))
        y += 15
        rows.append(("small", (x, y),
                     "can each use a different strut -- that is the"))
        y += 15
        rows.append(("small", (x, y), "point. Then push it to the dome."))
        y += 22

        rows.append(("head", (x, y), "STRUTS  (one per edge)"))
        y += 20
        for i in range(3):
            profile = strut_profile(self.bench_struts[i])
            rect = (x, y, w, 18)
            rows.append(("choice", rect,
                         (f"Edge {i + 1}", strut_label(self.bench_struts[i]))))
            regions.append((rect, "bench_strut", (i,)))
            y += 21
            rows.append(("small", (x, y),
                         f"   {profile.family}, {profile.summary}"))
            y += 16
        y += 6

        spec = self.bench_struts[self.bench_edge % 3]
        profile = strut_profile(spec)
        rows.append(("head", (x, y),
                     f"EDGE {self.bench_edge % 3 + 1}: {strut_label(spec).upper()}"))
        y += 19
        for line in self._wrap(profile.blurb, 44):
            rows.append(("small", (x, y), line))
            y += 15
        y += 8

        rows.append(("head", (x, y), "FILL"))
        y += 20
        fill = FILL_BY_KEY[self.bench_fill]
        rect = (x, y, w, 18)
        rows.append(("choice", rect, ("Material", fill.label)))
        regions.append((rect, "bench_fill", None))
        y += 22
        for line in self._wrap(fill.blurb, 44):
            rows.append(("small", (x, y), line))
            y += 15
        y += 10

        for label_text, action in (
            ("Send to selected triangle", "bench_to_face"),
            ("Send to every triangle", "bench_to_all"),
        ):
            rect = (x, y, w, 22)
            rows.append(("button", rect, label_text))
            regions.append((rect, action, None))
            y += 26
        y += 6
        library = self.stack.designs
        rows.append(("head", (x, y), "DESIGN LIBRARY"))
        y += 20
        rect = (x, y, w, 22)
        rows.append(("button", rect, "Save as a triangle design..."))
        regions.append((rect, "save_triangle_design", None))
        y += 26
        rect = (x, y, w, 22)
        rows.append(("button", rect,
                     f"Load a triangle design  ({len(library.triangles)})"))
        regions.append((rect, "load_triangle_design", None))
        y += 30
        rows.append(("small", (x, y),
                     "Left-click a choice to go forward,"))
        y += 15
        rows.append(("small", (x, y), "right-click to go back."))
        y += 20
        return rows, regions, y + self.scroll + 20, 0

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words, lines, line = text.split(), [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if len(candidate) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    # -- drawing ---------------------------------------------------------

    def draw_ui(self, width: int, height: int):
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        panel = pg.Surface((PANEL_W, height), pg.SRCALPHA)
        panel.fill(PANEL_BG)
        surface.blit(panel, (0, 0))

        rows, _, left_h, right_h = self.layout(width, height)
        self.scroll = max(0, min(self.scroll, max(0, left_h - height + 30)))
        self.scroll_right = max(0, min(self.scroll_right,
                                       max(0, right_h - height + 30)))
        for kind, rect, payload in rows:
            if kind == "panel_bg":
                box = pg.Surface((rect[2], rect[3]), pg.SRCALPHA)
                box.fill((14, 26, 40, 244))
                surface.blit(box, (rect[0], rect[1]))
            elif kind == "title":
                surface.blit(self.font_bold.render(payload, True, ACCENT), rect)
            elif kind == "head":
                surface.blit(self.font_small.render(payload, True, WARN), rect)
            elif kind == "small":
                surface.blit(self.font_small.render(payload, True, DIM), rect)
            elif kind == "mono":
                surface.blit(self.font_mono.render(payload, True, INK), rect)
            elif kind == "field":
                pg.draw.rect(surface, (8, 16, 26), rect, border_radius=4)
                pg.draw.rect(surface, ACCENT, rect, 1, border_radius=4)
                surface.blit(self.font.render(payload + "_", True, INK),
                             (rect[0] + 8, rect[1] + 4))
            elif kind == "option":
                label, is_current = payload
                pg.draw.rect(surface, ROW_SEL if is_current else ROW_BG, rect,
                             border_radius=4)
                surface.blit(
                    self.font_small.render(label, True,
                                           ACCENT if is_current else INK),
                    (rect[0] + 8, rect[1] + 3))
            elif kind == "button":
                pg.draw.rect(surface, ROW_BG, rect, border_radius=4)
                pg.draw.rect(surface, (60, 92, 118), rect, 1, border_radius=4)
                label = self.font_small.render(payload, True, INK)
                surface.blit(label, (rect[0] + 8, rect[1] + 3))
            elif kind == "toggle":
                label, on = payload
                pg.draw.rect(surface, ROW_BG, rect, border_radius=4)
                box = (rect[0] + 4, rect[1] + 4, 10, 10)
                pg.draw.rect(surface, ACCENT if on else (70, 84, 96), box)
                surface.blit(self.font_small.render(label, True, INK),
                             (rect[0] + 20, rect[1] + 2))
            elif kind == "choice":
                label, value = payload
                pg.draw.rect(surface, ROW_BG, rect, border_radius=4)
                surface.blit(self.font_small.render(label, True, DIM),
                             (rect[0] + 6, rect[1] + 2))
                text = self.font_small.render(value, True, ACCENT)
                surface.blit(text, (rect[0] + rect[2] - text.get_width() - 8,
                                    rect[1] + 2))
            elif kind == "slider":
                label, value, low, high = payload[0], payload[1], payload[2], payload[3]
                shown = payload[4] if len(payload) > 4 else f"{value:.3g}"
                surface.blit(self.font_small.render(label, True, DIM),
                             (rect[0], rect[1]))
                text = self.font_small.render(shown, True, INK)
                surface.blit(text, (rect[0] + rect[2] - text.get_width(),
                                    rect[1]))
                track_y = rect[1] + 20
                pg.draw.rect(surface, (38, 56, 74),
                             (rect[0], track_y, rect[2], 4), border_radius=2)
                frac = 0.0 if high <= low else (value - low) / (high - low)
                frac = max(0.0, min(1.0, frac))
                pg.draw.rect(surface, ACCENT,
                             (rect[0], track_y, int(rect[2] * frac), 4),
                             border_radius=2)
                knob = int(rect[0] + rect[2] * frac)
                pg.draw.circle(surface, INK, (knob, track_y + 2), 5)
            elif kind == "opacity":
                frac = max(0.0, min(1.0, payload))
                pg.draw.rect(surface, (30, 46, 62), rect, border_radius=2)
                pg.draw.rect(surface, (120, 170, 210),
                             (rect[0], rect[1], int(rect[2] * frac), rect[3]),
                             border_radius=2)
            elif kind == "layer":
                layer, selected = payload
                pg.draw.rect(surface, ROW_SEL if selected else ROW_BG, rect,
                             border_radius=4)
                eye = (rect[0] + 5, rect[1] + 5, 10, 10)
                pg.draw.rect(surface, ACCENT if layer.visible else (64, 78, 90), eye)
                swatch = TINTS.get(str(layer.get("tint")), (0.5, 0.5, 0.5))
                pg.draw.rect(surface,
                             tuple(int(c * 255) for c in swatch),
                             (rect[0] + 21, rect[1] + 5, 8, 10))
                name = self.font_small.render(layer.name, True,
                                              INK if layer.visible else DIM)
                surface.blit(name, (rect[0] + 33, rect[1] + 2))
                for offset, glyph in ((60, "^"), (40, "v"), (20, "x")):
                    surface.blit(
                        self.font_small.render(glyph, True, DIM),
                        (rect[0] + rect[2] - offset + 4, rect[1] + 2),
                    )

        hint = self.font_small.render(self.message, True, DIM)
        surface.blit(hint, (PANEL_W + 16, height - 26))
        state = "playing" if self.playing else "paused"
        if self.mode == "groups":
            keys = ("[m] next mode   [Tab] pentagons/hourglasses   "
                    "[<- ->] step through   [esc] quit")
        elif self.mode == "jigs":
            keys = ("[m] next mode   [Tab] other jig   "
                    "[<- ->] step   [esc] quit")
        else:
            keys = (f"[m] jig shop   [space] {state}   [c] cutaway   "
                    f"[s] save   [l] load   [1-4] views   [esc] quit")
        info = self.font_small.render(keys, True, DIM)
        surface.blit(info, (PANEL_W + 16, height - 46))
        return surface

    def upload_overlay(self, surface) -> None:
        size = surface.get_size()
        if self.overlay_texture is None or self.overlay_size != size:
            if self.overlay_texture is not None:
                self.overlay_texture.release()
            self.overlay_texture = self.ctx.texture(size, 4)
            self.overlay_texture.filter = (self.moderngl.LINEAR,
                                           self.moderngl.LINEAR)
            self.overlay_size = size
        self.overlay_texture.write(
            self.pygame.image.tobytes(surface, "RGBA", True)
        )

    # -- interaction -----------------------------------------------------

    def ray_from(self, pos, width: int, height: int):
        """The world-space ray under the cursor, shared by every picker so
        they can never disagree about where the mouse is pointing."""
        eye, target = self.camera()
        forward = target - eye
        forward = forward / max(1e-9, float(np.linalg.norm(forward)))
        up_hint = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        right = np.cross(forward, up_hint)
        right = right / max(1e-9, float(np.linalg.norm(right)))
        up = np.cross(right, forward)
        aspect = width / max(1, height)
        half = math.tan(math.radians(46.0) * 0.5)
        ndc_x = (2.0 * pos[0] / max(1, width)) - 1.0
        ndc_y = 1.0 - (2.0 * pos[1] / max(1, height))
        direction = forward + right * (ndc_x * half * aspect) + up * (ndc_y * half)
        return eye, direction / max(1e-9, float(np.linalg.norm(direction)))

    def pick_at(self, pos, width: int, height: int) -> int:
        """Turn a click in the 3D area into a triangle index."""
        eye, direction = self.ray_from(pos, width, height)
        return pick_face(self.stack, eye, direction)


    def hit(self, pos, width, height):
        _, regions, _, _ = self.layout(width, height)
        x, y = pos
        # Later regions are drawn on top, so test them first.
        for rect, action, payload in reversed(regions):
            rx, ry, rw, rh = rect
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return rect, action, payload
        return None

    def apply_slider(self, rect, action, payload, mouse_x) -> None:
        rx, _, rw, _ = rect
        frac = max(0.0, min(1.0, (mouse_x - rx) / max(1, rw)))
        if action == "dome_slider":
            key, low, high = payload
            setattr(self.stack.settings, key, low + (high - low) * frac)
        elif action == "param_slider":
            key, low, high = payload
            active = self.stack.active
            if active is not None:
                active.set(key, low + (high - low) * frac)
        elif action == "layer_opacity":
            self.stack.layers[payload].opacity = frac

    def click(self, pos, width, height, button: int) -> None:
        found = self.hit(pos, width, height)
        if found is None:
            return
        rect, action, payload = found
        stack = self.stack
        if action in ("dome_slider", "param_slider", "layer_opacity"):
            self.dragging = (rect, action, payload)
            self.apply_slider(rect, action, payload, pos[0])
        elif action == "toggle_layer":
            stack.layers[payload].visible = not stack.layers[payload].visible
        elif action == "select_layer":
            stack.selected = payload
        elif action == "move_up":
            stack.move(payload, 1)
        elif action == "move_down":
            stack.move(payload, -1)
        elif action == "delete_layer":
            name = stack.layers[payload].name
            stack.remove(payload)
            self.notify(f"Removed {name}.")
        elif action == "cut_toggle":
            stack.settings.cut_enabled = not stack.settings.cut_enabled
        elif action == "param_bool":
            active = stack.active
            if active is not None:
                active.set(payload[0], not bool(active.get(payload[0])))
        elif action.startswith("sel_"):
            self.toolbar_action(action)
        elif action == "save_triangle_design":
            self.prompt = {"title": "NAME THIS TRIANGLE DESIGN",
                           "value": "", "action": "save_triangle_design"}
        elif action == "load_triangle_design":
            library = stack.designs
            if not library.triangles:
                self.notify("No triangle designs saved yet.")
            else:
                self.open_picker(
                    "TRIANGLE DESIGNS",
                    [(n, f"{n}  ({FILL_BY_KEY[d.fill].label})")
                     for n, d in library.triangles.items()],
                    None, "load_triangle_design")
        elif action == "save_group_design":
            kind = self.group_kind
            self.prompt = {"title": f"NAME THIS {kind.upper()} DESIGN",
                           "value": "", "action": "save_group_design"}
        elif action == "load_group_design":
            saved = stack.designs.groups_of(self.group_kind)
            if not saved:
                self.notify(f"No {self.group_kind} designs saved yet.")
            else:
                self.open_picker(
                    f"{self.group_kind.upper()} DESIGNS",
                    [(g.name, g.name) for g in saved],
                    None, "load_group_design")
        elif action == "open_add":
            self.open_picker("ADD A LAYER",
                             [(k.key, k.label) for k in LAYER_KINDS],
                             None, "add_layer")
        elif action == "toggle_mode":
            self.set_mode(self._next_mode())
        elif action == "toggle_group_kind":
            self.group_kind = ("hourglass" if self.group_kind == "pentagon"
                               else "pentagon")
            self.group_index = 0
        elif action == "group_forward":
            self.group_index += 1
        elif action == "group_back":
            self.group_index -= 1
        elif action == "joint_all":
            group, _ = self.current_group()
            chosen = stack.assignments.joint_for(group.index)
            stack.assignments.joint = chosen
            stack.assignments.waist_joint.clear()
            self.notify(f"Every waist now uses {JOINT_BY_KEY[chosen].label}.")
        elif action == "next_jig":
            self.jig_index = (self.jig_index + 1) % 2
            self.notify(self.jig_spec().label)
        elif action == "step_forward":
            self.step_index = (self.step_index + 1) % len(STEPS)
        elif action == "step_back":
            self.step_index = (self.step_index - 1) % len(STEPS)
        elif action in ("face_fill", "face_strut", "default_choice",
                        "bench_strut", "bench_fill", "waist_joint",
                        "group_fill", "group_strut", "param_choice"):
            self._open_catalog_picker(action, payload)
        elif action == "picker_choose":
            self._picker_choose(payload)
        elif action == "picker_cancel":
            self.picker = None
        elif action == "pentagon_preset":
            from .groups import PENTAGON_PRESETS
            self.open_picker(
                "PENTAGON PRESET",
                [(p.key, p.label) for p in PENTAGON_PRESETS],
                None, "pentagon_preset")
        elif action == "apply_fill_all":
            chosen = stack.assignments.fill_for(self.primary_face)
            stack.assignments.fill = chosen
            stack.assignments.face_fill.clear()
            self.notify(f"Every triangle is now {FILL_BY_KEY[chosen].label}.")
        elif action == "apply_shape":
            self._apply_to_shape()
        elif action == "reset_face":
            stack.assignments.clear_face(self.primary_face)
            self.notify("Triangle reset to the defaults.")
        elif action == "bench_to_face":
            if self.primary_face < 0:
                self.notify("Select a triangle in DOME mode first.")
            else:
                stack.assignments.face_fill[str(self.primary_face)] = \
                    self.bench_fill
                stack.assignments.set_face_struts(self.primary_face,
                                                  self.bench_struts)
                self.notify(f"Sent to triangle #{self.primary_face}.")
        elif action == "bench_to_all":
            stack.assignments.fill = self.bench_fill
            stack.assignments.strut_long = self.bench_struts[0]
            stack.assignments.strut_short = self.bench_struts[1]
            stack.assignments.face_fill.clear()
            stack.assignments.face_struts.clear()
            self.notify("Every triangle now uses this panel.")

    def _next_mode(self) -> str:
        return {"dome": "groups", "groups": "panel",
                "panel": "jigs", "jigs": "dome"}[self.mode]


    def _roll_selection(self, turn: int, mirror: bool) -> None:
        """Roll (or mirror) every strut of every selected triangle.

        The roll is carried in the strut key, so this rewrites the keys
        rather than storing orientation somewhere separate that could
        drift out of step with the profile it belongs to.
        """
        from .catalog import format_strut, parse_strut
        if self.mode == "panel":
            for edge in sorted(self.bench_selection):
                key, spin, flip = parse_strut(self.bench_struts[edge])
                self.bench_struts[edge] = format_strut(
                    key, spin + turn, (not flip) if mirror else flip)
            what = "Mirrored" if mirror else "Rolled 90 deg"
            self.notify(f"{what}: {len(self.bench_selection)} strut(s).")
            return
        assignments = self.stack.assignments
        for face in sorted(self.selection):
            classes = face_edge_classes(self.stack, face)
            triple = assignments.strut_triple(face, classes)
            rolled = []
            for spec in triple:
                key, spin, flip = parse_strut(spec)
                rolled.append(format_strut(key, spin + turn,
                                           (not flip) if mirror else flip))
            assignments.set_face_struts(face, rolled)
        what = "Mirrored" if mirror else "Rolled 90 deg"
        self.notify(f"{what}: {len(self.selection)} triangle(s).")

    def _strut_options(self) -> list[tuple[str, str]]:
        """The 18 real profiles. Orientation is a toolbar action, not 72
        near-duplicate list entries."""
        from .catalog import STRUT_PROFILES
        return [(p.key, f"{p.label}   {p.summary}") for p in STRUT_PROFILES]


    def open_picker(self, title: str, options, current, action: str,
                    payload=None) -> None:
        self.picker = {"title": title, "options": list(options),
                       "current": current, "action": action,
                       "payload": payload}

    def _picker_choose(self, key: str) -> None:
        picker, self.picker = self.picker, None
        if not picker:
            return
        action, payload = picker["action"], picker["payload"]
        stack = self.stack
        assignments = stack.assignments
        if action == "sel_fill":
            for face in self.selection:
                assignments.face_fill[str(face)] = key
        elif action == "sel_strut" and self.mode == "panel":
            from .catalog import format_strut, parse_strut
            for edge in sorted(self.bench_selection):
                _k, spin, flip = parse_strut(self.bench_struts[edge])
                self.bench_struts[edge] = format_strut(key, spin, flip)
        elif action == "sel_strut":
            from .catalog import format_strut, parse_strut
            for face in sorted(self.selection):
                classes = face_edge_classes(stack, face)
                triple = assignments.strut_triple(face, classes)
                # Swapping the profile must not silently un-roll a strut
                # the user already turned, so the roll is carried over.
                assignments.set_face_struts(face, [
                    format_strut(key, parse_strut(spec)[1],
                                 parse_strut(spec)[2])
                    for spec in triple])
        elif action == "face_fill":
            assignments.face_fill[str(self.primary_face)] = key
        elif action == "face_strut":
            face = self.primary_face
            classes = face_edge_classes(stack, face)
            triple = assignments.strut_triple(face, classes)
            triple[payload[0]] = key
            assignments.set_face_struts(face, triple)
        elif action == "default_choice":
            if payload[0] == "fill":
                assignments.fill = key
            else:
                from .catalog import format_strut, parse_strut
                _k, spin, flip = parse_strut(getattr(assignments, payload[0]))
                setattr(assignments, payload[0],
                        format_strut(key, spin, flip))
        elif action == "bench_strut":
            self.bench_struts[payload[0]] = key
        elif action == "bench_fill":
            self.bench_fill = key
        elif action == "waist_joint":
            group, _ = self.current_group()
            assignments.waist_joint[str(group.index)] = key
        elif action == "group_fill":
            group, _ = self.current_group()
            for face in group.faces:
                assignments.face_fill[str(face)] = key
        elif action == "group_strut":
            group, _ = self.current_group()
            for face in group.faces:
                assignments.set_face_struts(face, [key] * 3)
        elif action == "pentagon_preset":
            self._apply_pentagon_preset(key)
        elif action == "load_triangle_design":
            self._apply_triangle_design(key)
        elif action == "load_group_design":
            self._apply_group_design(key)
        elif action == "param_choice":
            active = stack.active
            if active is not None:
                active.set(payload[0], key)
        elif action == "add_layer":
            layer = stack.add(key)
            self.notify(f"Added {layer.name}.")

    def _open_catalog_picker(self, action: str, payload) -> None:
        """Turn any catalog choice into a real dropdown."""
        stack = self.stack
        assignments = stack.assignments
        fills = [(k, FILL_BY_KEY[k].label) for k in FILL_KEYS]
        struts = self._strut_options()
        if action == "sel_strut" and self.mode == "panel":
            from .catalog import parse_strut
            current = self.bench_struts[min(self.bench_selection)] \
                if self.bench_selection else self.bench_struts[0]
            self.open_picker("STRUT FOR THE SELECTED EDGE(S)", struts,
                             parse_strut(current)[0], action)
        elif action == "sel_fill" and self.selection:
            self.open_picker("FILL FOR THE SELECTION", fills,
                             assignments.fill_for(self.primary_face), action)
        elif action == "sel_strut" and self.selection:
            classes = face_edge_classes(stack, self.primary_face)
            current = assignments.strut_triple(self.primary_face, classes)[0]
            from .catalog import parse_strut
            self.open_picker("STRUT FOR THE SELECTION", struts,
                             parse_strut(current)[0], action)
        elif action == "face_fill" and self.primary_face >= 0:
            self.open_picker("PANEL FILL", fills,
                             assignments.fill_for(self.primary_face),
                             action)
        elif action == "face_strut" and self.primary_face >= 0:
            face = self.primary_face
            classes = face_edge_classes(stack, face)
            from .catalog import parse_strut
            current = assignments.strut_triple(face, classes)[payload[0]]
            self.open_picker(f"STRUT FOR EDGE {payload[0] + 1}", struts,
                             parse_strut(current)[0], action, payload)
        elif action == "default_choice":
            key = payload[0]
            if key == "fill":
                self.open_picker("DEFAULT FILL", fills, assignments.fill,
                                 action, payload)
            else:
                from .catalog import parse_strut
                self.open_picker("DEFAULT STRUT", struts,
                                 parse_strut(getattr(assignments, key))[0],
                                 action, payload)
        elif action == "bench_strut":
            self.bench_edge = payload[0]
            self.open_picker(f"STRUT FOR EDGE {payload[0] + 1}", struts,
                             self.bench_struts[payload[0]], action, payload)
        elif action == "bench_fill":
            self.open_picker("PANEL FILL", fills, self.bench_fill, action)
        elif action == "waist_joint":
            group, _ = self.current_group()
            self.open_picker(
                "WAIST JOINT",
                [(k, JOINT_BY_KEY[k].label) for k in JOINT_KEYS],
                assignments.joint_for(group.index), action)
        elif action == "group_fill":
            group, _ = self.current_group()
            self.open_picker("FILL FOR THE WHOLE GROUP", fills,
                             assignments.fill_for(group.faces[0]), action)
        elif action == "group_strut":
            from .catalog import parse_strut
            group, _ = self.current_group()
            classes = face_edge_classes(stack, group.faces[0])
            current = assignments.strut_triple(group.faces[0], classes)[0]
            self.open_picker("STRUT FOR THE WHOLE GROUP", struts,
                             parse_strut(current)[0], action)
        elif action == "param_choice":
            active = stack.active
            if active is not None:
                spec = active.spec.spec(payload[0])
                if spec and spec.choices:
                    self.open_picker(spec.label.upper(),
                                     [(c, c) for c in spec.choices],
                                     str(active.get(payload[0])), action,
                                     payload)


    def _finish_prompt(self, prompt: dict) -> None:
        name = prompt["value"].strip()
        if not name:
            self.notify("Not saved -- a design needs a name.")
            return
        if prompt["action"] == "save_triangle_design":
            design = self.stack.designs.save_triangle(
                name, list(self.bench_struts), self.bench_fill)
            self.notify(f"Saved triangle design '{design.name}'.")
        elif prompt["action"] == "save_group_design":
            self._save_current_group_design(name)

    def _apply_triangle_design(self, name: str) -> None:
        """Load a saved part onto the bench, or onto whatever is selected."""
        design = self.stack.designs.triangle(name)
        if design is None:
            return
        if self.mode == "panel":
            self.bench_struts = list(design.struts)
            self.bench_fill = design.fill
            self.notify(f"Loaded '{name}' onto the bench.")
            return
        if not self.selection:
            self.notify("Select a triangle first, or load it in the "
                        "Panel Creator.")
            return
        for face in self.selection:
            self.stack.assignments.set_face_struts(face, list(design.struts))
            self.stack.assignments.face_fill[str(face)] = design.fill
        self.notify(f"Applied '{name}' to {len(self.selection)} triangle(s).")

    def _apply_group_design(self, name: str) -> None:
        """Rebuild the current group from a saved design.

        The design stores triangle *references*, so this resolves each one
        through the library -- meaning a later edit to a shared part shows
        up in every group built from it.
        """
        library = self.stack.designs
        design = library.group(name)
        if design is None:
            return
        group, _ = self.current_group()
        parts = library.resolve(design)
        for face, part in zip(group.faces, parts):
            self.stack.assignments.set_face_struts(face, list(part.struts))
            self.stack.assignments.face_fill[str(face)] = part.fill
        if design.kind == "hourglass":
            self.stack.assignments.waist_joint[str(group.index)] = design.joint
        self.notify(f"Built this {design.kind} from '{name}'.")

    def _save_current_group_design(self, name: str) -> None:
        """Capture the current group as a reusable design.

        Each distinct face composition becomes a triangle design, reusing
        an existing one where the composition already matches, so saving a
        pentagon of five identical faces adds one part and not five.
        """
        library = self.stack.designs
        group, _ = self.current_group()
        assignments = self.stack.assignments
        names = []
        for slot, face in enumerate(group.faces):
            classes = face_edge_classes(self.stack, face)
            struts = assignments.strut_triple(face, classes)
            fill = assignments.fill_for(face)
            names.append(library.ensure_triangle(
                struts, fill, f"{name or 'Part'} {'ABCDE'[slot]}"))
        joint = (assignments.joint_for(group.index)
                 if self.group_kind == "hourglass" else "banding")
        design = library.save_group(name, self.group_kind, names, joint)
        self.notify(f"Saved '{design.name}' "
                    f"({len(set(names))} distinct triangle design(s)).")

    def _apply_pentagon_preset(self, key: str) -> None:
        from .groups import PRESET_BY_KEY
        preset = PRESET_BY_KEY.get(key)
        group, _ = self.current_group()
        if preset is None:
            return
        assignments = self.stack.assignments
        for face, fill in zip(group.faces, preset.fills):
            assignments.face_fill[str(face)] = fill
            if preset.strut:
                assignments.set_face_struts(face, [preset.strut] * 3)
        self.notify(f"Pentagon set to {preset.label}.")

    def _apply_to_shape(self) -> None:
        """Copy the selected triangle's make-up onto every triangle of the
        same shape -- the 10 equilaterals or the 30 isosceles."""
        stack = self.stack
        face = self.primary_face
        if face < 0:
            return
        classes = face_edge_classes(stack, face)
        equilateral = classes.count("LONG") == 3
        fill = stack.assignments.fill_for(face)
        triple = stack.assignments.strut_triple(face, classes)
        count = 0
        for index in range(40):
            other = face_edge_classes(stack, index)
            if (other.count("LONG") == 3) != equilateral:
                continue
            stack.assignments.face_fill[str(index)] = fill
            stack.assignments.set_face_struts(index, triple)
            count += 1
        self.notify(f"Applied to {count} "
                    f"{'equilateral' if equilateral else 'isosceles'} triangles.")

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.scroll = 0
        if mode == "groups":
            self.distance = 7.0
            self.notify("Groups: Tab swaps pentagons/hourglasses, "
                        "arrows step through them.")
        elif mode == "jigs":
            self.yaw, self.pitch, self.distance = 62.0, 50.0, 6.6
            self.notify("Jig Shop: arrows step through the build, Tab swaps jig.")
        elif mode == "panel":
            self.yaw, self.pitch, self.distance = 56.0, 40.0, 4.4
            self.notify("Panel Creator: mix any three struts, pick a fill.")
        else:
            self.yaw, self.pitch, self.distance = 38.0, 22.0, 15.0
            self.notify("Dome: click a triangle to select it.")

    def key(self, event) -> None:
        pg = self.pygame
        settings = self.stack.settings
        if self.prompt is not None:
            # While the name box is open it takes every keystroke, so a
            # name containing "s" or "c" cannot trigger save or cutaway.
            if event.key == pg.K_ESCAPE:
                self.prompt = None
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                prompt, self.prompt = self.prompt, None
                self._finish_prompt(prompt)
            elif event.key == pg.K_BACKSPACE:
                self.prompt["value"] = self.prompt["value"][:-1]
            elif event.unicode and event.unicode.isprintable():
                self.prompt["value"] = (self.prompt["value"]
                                        + event.unicode)[:40]
            return
        if self.picker is not None and event.key == pg.K_ESCAPE:
            self.picker = None
            return

        # With something selected, the keyboard drives the toolbar. These
        # are checked before the view keys so they never collide with
        # save/cutaway/mode.
        if self.has_selection:
            shortcuts = {
                pg.K_f: "sel_fill", pg.K_t: "sel_strut",
                pg.K_r: "sel_roll", pg.K_x: "sel_flip",
                pg.K_RIGHTBRACKET: "sel_explode_up",
                pg.K_LEFTBRACKET: "sel_explode_down",
                pg.K_DELETE: "sel_clear", pg.K_BACKSPACE: "sel_clear",
            }
            if event.key in shortcuts:
                self.toolbar_action(shortcuts[event.key])
                return
            if event.key in (pg.K_LEFT, pg.K_RIGHT):
                self.cycle_variant(1 if event.key == pg.K_RIGHT else -1)
                return
        if event.key == pg.K_ESCAPE:
            self.running = False
        elif event.key == pg.K_m:
            self.set_mode(self._next_mode())
        elif event.key == pg.K_TAB and self.mode == "jigs":
            self.jig_index = (self.jig_index + 1) % 2
            self.notify(self.jig_spec().label)
        elif event.key == pg.K_TAB and self.mode == "groups":
            self.group_kind = ("hourglass" if self.group_kind == "pentagon"
                               else "pentagon")
            self.group_index = 0
            self.notify(f"Editing {self.group_kind}s.")
        elif event.key == pg.K_RIGHT and self.mode == "jigs":
            self.step_index = (self.step_index + 1) % len(STEPS)
        elif event.key == pg.K_LEFT and self.mode == "jigs":
            self.step_index = (self.step_index - 1) % len(STEPS)
        elif event.key == pg.K_RIGHT and self.mode == "groups":
            self.group_index += 1
        elif event.key == pg.K_LEFT and self.mode == "groups":
            self.group_index -= 1
        elif event.key == pg.K_SPACE:
            self.playing = not self.playing
        elif event.key == pg.K_c:
            settings.cut_enabled = not settings.cut_enabled
            self.notify(f"Cutaway {'on' if settings.cut_enabled else 'off'}.")
        elif event.key == pg.K_s:
            path = self.stack.save(self.preset_path)
            self.notify(f"Saved {path}")
        elif event.key == pg.K_l:
            if self.preset_path.is_file():
                self.stack = LayerStack.load(self.preset_path)
                self.notify(f"Loaded {self.preset_path}")
            else:
                self.notify(f"No preset at {self.preset_path} yet -- press s first.")
        elif event.key == pg.K_1:
            self.yaw, self.pitch, self.distance = 38.0, 22.0, 15.0
        elif event.key == pg.K_2:                       # look inside
            self.yaw, self.pitch, self.distance = 200.0, 8.0, 6.5
            settings.cut_enabled = True
        elif event.key == pg.K_3:                       # top-down
            self.yaw, self.pitch, self.distance = 90.0, 78.0, 16.0
        elif event.key == pg.K_4:                       # ground level
            self.yaw, self.pitch, self.distance = 300.0, -6.0, 12.0

    # -- frame -----------------------------------------------------------

    def render(self, present: bool = True) -> None:
        width, height = self.pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.clear(*BG)
        eye, target = self.camera()
        mvp = perspective(46.0, width / max(1, height), 0.05, 400.0) @ look_at(
            eye, target
        )
        self.scene_program["u_mvp"].write(np.ascontiguousarray(mvp.T).tobytes())
        self.scene_program["u_camera"].value = tuple(float(v) for v in eye)
        self.scene_program["u_light"].value = (-0.42, -0.58, -0.70)

        if self.mode == "jigs":
            opaque, translucent = self.build_jig_scene()
        elif self.mode == "panel":
            opaque, translucent = self.build_panel_scene()
        else:
            self.stack.highlight_faces = (
                self.group_faces() if self.mode == "groups" else ())
            opaque, translucent = build_scene(self.stack, self.clock_t)
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.ctx.depth_mask = True
        self.opaque.draw(opaque)
        if translucent.v:
            self.ctx.disable(self.moderngl.CULL_FACE)
            self.ctx.depth_mask = False
            self.translucent.draw(translucent)
            self.ctx.depth_mask = True
            self.ctx.enable(self.moderngl.CULL_FACE)

        self.upload_overlay(self.draw_ui(width, height))
        self.ctx.disable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.overlay_texture.use(0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_vao.render(self.moderngl.TRIANGLE_STRIP)
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        if present:
            self.pygame.display.flip()

    def capture(self, path: Path) -> Path:
        width, height = self.pygame.display.get_window_size()
        self.render(present=False)
        self.ctx.finish()
        data = self.ctx.screen.read((0, 0, width, height), components=3, alignment=1)
        surface = self.pygame.image.frombytes(data, (width, height), "RGB", True)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pygame.image.save(surface, str(path))
        return path

    def run(self) -> None:
        pg = self.pygame
        clock = pg.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            if self.playing:
                self.clock_t += dt
            # Ease the pop-out in and out rather than snapping, so it reads
            # as the piece lifting off the shell.
            target = self.explode_amount if self.selection else 0.0
            self.stack.explode += (target - self.stack.explode) * min(1.0, dt * 7.0)
            width, height = pg.display.get_window_size()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    self.key(event)
                elif event.type == pg.MOUSEBUTTONDOWN:
                    on_left = event.pos[0] < PANEL_W
                    on_right = (event.pos[0] > width - RIGHT_W
                                and self.mode == "dome")
                    # Ask the layout whether anything clickable is under the
                    # cursor rather than guessing from screen bands. The
                    # floating toolbar sits *over* the 3D view, so a band
                    # test sent clicks on it straight through to the picker,
                    # which then cleared the very selection the toolbar was
                    # acting on.
                    over_ui = (event.button in (1, 3)
                               and self.hit(event.pos, width, height) is not None)
                    if over_ui:
                        self.click(event.pos, width, height, event.button)
                    elif self.picker or self.prompt:
                        # A modal is open: clicking off it dismisses rather
                        # than falling through to the scene behind.
                        self.picker = None
                    elif on_left or on_right:
                        if event.button in (4, 5):
                            step = -48 if event.button == 4 else 48
                            if on_right:
                                self.scroll_right = max(0, self.scroll_right + step)
                            else:
                                self.scroll = max(0, self.scroll + step)
                    else:
                        if event.button == 1:
                            self.orbiting = True
                            self.press_at = event.pos
                        elif event.button == 4:
                            self.distance = max(2.0, self.distance * 0.9)
                        elif event.button == 5:
                            self.distance = min(80.0, self.distance * 1.1)
                elif event.type == pg.MOUSEBUTTONUP:
                    # A click that did not turn into a drag is a pick, not
                    # an orbit -- so selecting a triangle never fights with
                    # rotating the view.
                    if (event.button == 1 and self.orbiting
                            and self.press_at is not None
                            and abs(event.pos[0] - self.press_at[0]) < 4
                            and abs(event.pos[1] - self.press_at[1]) < 4):
                        mods = pg.key.get_mods()
                        additive = bool(mods & (pg.KMOD_CTRL | pg.KMOD_SHIFT))
                        self.pick_component(event.pos, width, height, additive)
                    self.press_at = None
                    self.dragging = None
                    self.orbiting = False
                elif event.type == pg.MOUSEMOTION:
                    if self.dragging is not None:
                        self.apply_slider(*self.dragging, event.pos[0])
                    elif self.orbiting:
                        self.yaw -= event.rel[0] * 0.35
                        self.pitch = max(-12.0, min(84.0,
                                                    self.pitch + event.rel[1] * 0.3))
            self.render()
        pg.quit()


def launch(preset: Path | None = None, size=(1600, 900),
           fullscreen: bool = False) -> None:
    DomeForgeApp(size=size, fullscreen=fullscreen, preset=preset).run()
