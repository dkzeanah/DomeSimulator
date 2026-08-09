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

from .build import build_scene, scene_stats, tint, TINTS
from .jigs import STEPS, emit_jig, jig_specs, step_lines
from .layers import LAYER_KINDS, KIND_BY_KEY, LayerStack, default_stack


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
PANEL_W = 340
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

        self.mode = "dome"            # "dome" or "jigs"
        self.jig_index = 0            # which of the two jigs
        self.step_index = 0           # which build step
        self.yaw, self.pitch, self.distance = 38.0, 22.0, 15.0
        self.playing = True
        self.clock_t = 0.0
        self.running = True
        self.dragging = None          # active slider drag
        self.orbiting = False
        self.show_add = False
        self.message = "Drag to orbit. Scroll to zoom. Click a layer to tune it."
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

    def camera(self):
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

    def layout(self, height: int):
        """Return (rows, regions, content_height). ``rows`` are draw
        instructions; ``regions`` are (rect, action, payload) for mouse
        hits. Both are produced from the same running ``y``, so what you
        see and what you can click can never disagree -- including while
        the panel is scrolled."""
        rows: list[tuple] = []
        regions: list[tuple] = []
        x, w = 10, PANEL_W - 20
        y = 10 - self.scroll

        rows.append(("title", (x, y), "DOME FORGE"))
        y += 26
        rect = (x, y, w, 20)
        rows.append(("button", rect,
                     "Mode: DOME  (m to switch)" if self.mode == "dome"
                     else "Mode: JIG SHOP  (m to switch)"))
        regions.append((rect, "toggle_mode", None))
        y += 26

        if self.mode == "jigs":
            return self._layout_jigs(rows, regions, x, y, w)
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

        # Layer list, topmost layer shown first (paint-program order)
        rows.append(("head", (x, y), "LAYERS  (top draws last)"))
        y += 20
        for display_index, layer in enumerate(reversed(self.stack.layers)):
            index = len(self.stack.layers) - 1 - display_index
            rect = (x, y, w, 20)
            rows.append(("layer", rect,
                         (layer, index == self.stack.selected)))
            eye_rect = (x + 2, y + 2, 16, 16)
            regions.append((eye_rect, "toggle_layer", index))
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

        # Selected layer's own controls
        active = self.stack.active
        if active is not None:
            rows.append(("head", (x, y), active.name.upper()))
            y += 19
            for line in self._wrap(active.spec.blurb, 44):
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

        content_height = y + self.scroll + 20

        # The add-layer picker floats over everything when open.
        if self.show_add:
            ax, ay = PANEL_W + 20, 40
            aw = 320
            rows.append(("panel_bg", (ax - 10, ay - 30, aw + 20,
                                      len(LAYER_KINDS) * 24 + 46), None))
            rows.append(("head", (ax, ay - 24), "ADD A LAYER"))
            for kind in LAYER_KINDS:
                rect = (ax, ay, aw, 21)
                rows.append(("button", rect, kind.label))
                regions.append((rect, "add_layer", kind.key))
                ay += 24
            rect = (ax, ay + 2, aw, 21)
            rows.append(("button", rect, "Cancel"))
            regions.append((rect, "close_add", None))

        return rows, regions, content_height

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
        return rows, regions, y + self.scroll + 20

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

        rows, _, content_height = self.layout(height)
        self._clamp_scroll(content_height, height)
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
        if self.mode == "jigs":
            keys = ("[m] back to dome   [Tab] other jig   "
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

    def _clamp_scroll(self, content_height: int, height: int) -> None:
        self.scroll = max(0, min(self.scroll, max(0, content_height - height + 30)))

    def hit(self, pos, height):
        _, regions, _ = self.layout(height)
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

    def click(self, pos, height, button: int) -> None:
        found = self.hit(pos, height)
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
        elif action == "param_choice":
            active = stack.active
            if active is not None:
                spec = active.spec.spec(payload[0])
                if spec and spec.choices:
                    current = str(active.get(payload[0]))
                    index = (spec.choices.index(current) + (1 if button != 3 else -1)
                             ) % len(spec.choices) if current in spec.choices else 0
                    active.set(payload[0], spec.choices[index])
        elif action == "open_add":
            self.show_add = True
        elif action == "close_add":
            self.show_add = False
        elif action == "add_layer":
            layer = stack.add(payload)
            self.show_add = False
            self.notify(f"Added {layer.name}.")
        elif action == "toggle_mode":
            self.set_mode("jigs" if self.mode == "dome" else "dome")
        elif action == "next_jig":
            self.jig_index = (self.jig_index + 1) % 2
            self.notify(self.jig_spec().label)
        elif action == "step_forward":
            self.step_index = (self.step_index + 1) % len(STEPS)
        elif action == "step_back":
            self.step_index = (self.step_index - 1) % len(STEPS)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.scroll = 0
        if mode == "jigs":
            self.yaw, self.pitch, self.distance = 52.0, 46.0, 7.5
            self.notify("Jig Shop: arrows step through the build, Tab swaps jig.")
        else:
            self.yaw, self.pitch, self.distance = 38.0, 22.0, 15.0
            self.notify("Dome: drag to orbit, click a layer to tune it.")

    def key(self, event) -> None:
        pg = self.pygame
        settings = self.stack.settings
        if event.key == pg.K_ESCAPE:
            self.running = False
        elif event.key == pg.K_m:
            self.set_mode("jigs" if self.mode == "dome" else "dome")
        elif event.key == pg.K_TAB and self.mode == "jigs":
            self.jig_index = (self.jig_index + 1) % 2
            self.notify(self.jig_spec().label)
        elif event.key == pg.K_RIGHT and self.mode == "jigs":
            self.step_index = (self.step_index + 1) % len(STEPS)
        elif event.key == pg.K_LEFT and self.mode == "jigs":
            self.step_index = (self.step_index - 1) % len(STEPS)
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
        else:
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
            _, height = pg.display.get_window_size()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    self.key(event)
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.pos[0] < PANEL_W or self.show_add:
                        if event.button in (1, 3):
                            self.click(event.pos, height, event.button)
                        elif event.button == 4:
                            self.scroll = max(0, self.scroll - 48)
                        elif event.button == 5:
                            self.scroll += 48
                    else:
                        if event.button == 1:
                            self.orbiting = True
                        elif event.button == 4:
                            self.distance = max(2.0, self.distance * 0.9)
                        elif event.button == 5:
                            self.distance = min(80.0, self.distance * 1.1)
                elif event.type == pg.MOUSEBUTTONUP:
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
