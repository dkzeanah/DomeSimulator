"""The presenter engine: live preview and deterministic video export."""

from __future__ import annotations

import math
import subprocess
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from .camera import CameraState, cube_faces, shot_camera
from .prompt import parse_environment
from .script import Presentation, Shot
from .world import SKIES, build_frame
from . import narrate

SCENE_VS = """
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

SCENE_FS = """
#version 330
in vec3 v_world;
in vec3 v_normal;
in vec4 v_color;
uniform vec3 u_camera;
uniform vec3 u_light;
uniform vec3 u_fog_color;
uniform float u_fog_density;
out vec4 frag_color;
void main() {
    vec3 n = normalize(v_normal);
    if (!gl_FrontFacing) n = -n;
    vec3 l = normalize(-u_light);
    vec3 v = normalize(u_camera - v_world);
    vec3 h = normalize(l + v);
    float diffuse = max(dot(n, l), 0.0);
    float specular = pow(max(dot(n, h), 0.0), 40.0);
    float rim = pow(1.0 - max(dot(n, v), 0.0), 2.5);
    vec3 lit = v_color.rgb * (0.32 + 0.72 * diffuse);
    lit += vec3(0.80, 0.90, 1.0) * rim * 0.15;
    lit += vec3(1.0, 0.88, 0.66) * specular * 0.20;
    float dist = length(u_camera - v_world);
    float fog = 1.0 - exp(-dist * u_fog_density);
    frag_color = vec4(mix(lit, u_fog_color, clamp(fog, 0.0, 0.92)),
                      v_color.a);
}
"""

BLIT_VS = """
#version 330
in vec2 in_position;
out vec2 v_uv;
void main() {
    v_uv = in_position * 0.5 + 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

BLIT_FS = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, v_uv); }
"""

# Curvilinear resolve: map each screen pixel to a view direction for the
# active projection, then sample whichever of the six cube faces sees it.
PANO_FS = """
#version 330
in vec2 v_uv;
uniform sampler2D u_face0;
uniform sampler2D u_face1;
uniform sampler2D u_face2;
uniform sampler2D u_face3;
uniform sampler2D u_face4;
uniform sampler2D u_face5;
uniform int u_mode;          // 4 cylindrical, 5 fisheye180, 6 azimuthal360
uniform float u_aspect;
out vec4 frag_color;

vec4 sample_face(int face, vec2 uv) {
    if (face == 0) return texture(u_face0, uv);
    if (face == 1) return texture(u_face1, uv);
    if (face == 2) return texture(u_face2, uv);
    if (face == 3) return texture(u_face3, uv);
    if (face == 4) return texture(u_face4, uv);
    return texture(u_face5, uv);
}

void main() {
    vec2 s = v_uv * 2.0 - 1.0;               // -1..1
    vec3 d;                                   // camera space: +z forward
    if (u_mode == 4) {
        float az = s.x * 1.7453293;           // +-100 degrees
        d = normalize(vec3(sin(az), s.y * 1.05, cos(az)));
    } else {
        vec2 q = vec2(s.x * u_aspect, s.y);
        float r = length(q);
        float max_theta = (u_mode == 5) ? 1.5707963 : 3.1415926;
        if (r > 1.0) { frag_color = vec4(0.01, 0.02, 0.04, 1.0); return; }
        float theta = r * max_theta;
        vec2 dir = (r > 1e-5) ? q / r : vec2(0.0, 0.0);
        d = vec3(sin(theta) * dir, cos(theta));
    }
    // faces in camera space: forward, right, back, left, up, down
    vec3 fwd[6] = vec3[](vec3(0,0,1), vec3(1,0,0), vec3(0,0,-1),
                          vec3(-1,0,0), vec3(0,1,0), vec3(0,-1,0));
    vec3 upv[6] = vec3[](vec3(0,1,0), vec3(0,1,0), vec3(0,1,0),
                          vec3(0,1,0), vec3(0,0,-1), vec3(0,0,1));
    int best = 0;
    float best_dot = -2.0;
    for (int i = 0; i < 6; i++) {
        float dp = dot(d, fwd[i]);
        if (dp > best_dot) { best_dot = dp; best = i; }
    }
    vec3 f = fwd[best];
    vec3 u = upv[best];
    vec3 r3 = cross(u, f);
    float depth = dot(d, f);
    vec2 uv = vec2(dot(d, r3), dot(d, u)) / max(depth, 1e-5);
    uv = clamp(uv * 0.5 + 0.5, 0.0, 1.0);
    frag_color = sample_face(best, uv);
}
"""


def perspective_matrix(fov_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_matrix(eye, forward, up):
    forward = forward / max(1e-9, float(np.linalg.norm(forward)))
    right = np.cross(forward, up)
    right = right / max(1e-9, float(np.linalg.norm(right)))
    up2 = np.cross(right, forward)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = right
    m[1, :3] = up2
    m[2, :3] = -forward
    m[0, 3] = -float(np.dot(right, eye))
    m[1, 3] = -float(np.dot(up2, eye))
    m[2, 3] = float(np.dot(forward, eye))
    return m


class DynMesh:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.capacity = 4096 * 40
        self.buffer = ctx.buffer(reserve=self.capacity)
        self.vao = ctx.vertex_array(
            program, [(self.buffer, "3f 3f 4f",
                       "in_position", "in_normal", "in_color")])

    def draw(self, batch) -> None:
        if not batch.v:
            return
        data = np.asarray(batch.v, dtype=np.float32).tobytes()
        if len(data) > self.capacity:
            while self.capacity < len(data):
                self.capacity *= 2
            self.buffer.release()
            self.buffer = self.ctx.buffer(reserve=self.capacity)
            self.vao = self.ctx.vertex_array(
                self.program, [(self.buffer, "3f 3f 4f",
                                "in_position", "in_normal", "in_color")])
        self.buffer.write(data)
        self.vao.render(mode=4, vertices=len(batch.v) // 10)


PANEL_POSITIONS = ("right", "left", "bottom", "float")

# How much writing appears over the picture. The narration is always
# spoken and always written to the .srt sidecar; these levels only decide
# what gets burned into the frames themselves, so a video can be handed to
# someone who wants to add their own titles -- or who simply does not want
# the words they are hearing also printed on screen.
OVERLAY_LEVELS = {
    "full": {"title": True, "caption": True, "panel": True,
             "progress": True},
    "no_captions": {"title": True, "caption": False, "panel": True,
                    "progress": True},
    "titles_only": {"title": True, "caption": False, "panel": False,
                    "progress": True},
    "clean": {"title": False, "caption": False, "panel": False,
              "progress": False},
}

OVERLAY_HELP = {
    "full": "title, spoken-line captions, info panel and progress bar",
    "no_captions": "no spoken-line captions; keeps the title and info panel",
    "titles_only": "title and progress bar only",
    "clean": "nothing written on the picture at all -- just the 3-D scene",
}


class PresenterApp:
    def __init__(self, presentation: Presentation, headless=False,
                 windowed=True, size=None):
        import pygame
        import moderngl
        self.pygame = pygame
        self.moderngl = moderngl
        self.pres = presentation
        self.pres.validate()
        self.size = tuple(size or presentation.size)
        pygame.init()
        if headless:
            self.ctx = moderngl.create_standalone_context()
            self.screen_tex = self.ctx.texture(self.size, 4)
            self.screen_fbo = self.ctx.framebuffer(
                [self.screen_tex], self.ctx.depth_renderbuffer(self.size))
        else:
            flags = pygame.OPENGL | pygame.DOUBLEBUF
            if not windowed:
                flags |= pygame.FULLSCREEN
                pygame.display.set_mode((0, 0), flags)
            else:
                pygame.display.set_mode(self.size, flags)
            pygame.display.set_caption(f"Presenter — {presentation.title}")
            self.size = pygame.display.get_window_size()
            self.ctx = moderngl.create_context()
            self.screen_fbo = self.ctx.screen
        self.headless = headless

        ctx = self.ctx
        self.scene_prog = ctx.program(vertex_shader=SCENE_VS,
                                      fragment_shader=SCENE_FS)
        self.blit_prog = ctx.program(vertex_shader=BLIT_VS,
                                     fragment_shader=BLIT_FS)
        self.pano_prog = ctx.program(vertex_shader=BLIT_VS,
                                     fragment_shader=PANO_FS)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype=np.float32)
        qbuf = ctx.buffer(quad.tobytes())
        self.blit_vao = ctx.vertex_array(
            self.blit_prog, [(qbuf, "2f", "in_position")])
        self.pano_vao = ctx.vertex_array(
            self.pano_prog, [(qbuf, "2f", "in_position")])

        self.opaque = DynMesh(ctx, self.scene_prog)
        self.transparent = DynMesh(ctx, self.scene_prog)

        # cube faces for curvilinear projections
        face = 1024
        self.face_size = face
        self.face_tex = []
        self.face_fbo = []
        for _ in range(6):
            tex = ctx.texture((face, face), 4)
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.repeat_x = tex.repeat_y = False     # no seam bleeding
            self.face_tex.append(tex)
            self.face_fbo.append(ctx.framebuffer(
                [tex], ctx.depth_renderbuffer((face, face))))

        # overlay
        self.overlay_tex = ctx.texture(self.size, 4)
        self.overlay_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        pygame.font.init()
        self.fonts = {}
        self.env_cache = {}

        # playback state
        self.timeline = 0.0
        self.playing = True
        self.speed = 1.0
        self.shot_index = 0
        self.progress = 0.0
        self.yaw_off = 0.0
        self.pitch_off = 0.0
        self.dist_scale = 1.0
        self.dragging = False
        self.panel_override = None       # None | True | False
        self.panel_position_override = None
        self.mode_override = None
        self.output_dir = Path("presenter_output")
        # How much writing is burned into the frame (see OVERLAY_LEVELS).
        self.overlay_level = "full"
        # Where the 3-D scene is drawn. None fills the window; the scene
        # composer sets a rectangle so the picture sits in a panel with
        # the timeline and library around it.
        self.viewport = None

    # ---- helpers -------------------------------------------------------

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = self.pygame.font.SysFont(
                "consolas", size, bold=bold)
        return self.fonts[key]

    def environment(self, scene):
        if scene.slug not in self.env_cache:
            self.env_cache[scene.slug] = parse_environment(scene.environment)
        return self.env_cache[scene.slug]

    def locate(self, t):
        idx, prog = self.pres.shot_at(t)
        scene = self.pres.scene_of(idx)
        shot = self.pres.all_shots()[idx][1]
        return scene, shot, idx, prog

    # ---- frame construction -------------------------------------------

    def overlay_flags(self) -> dict:
        return OVERLAY_LEVELS.get(self.overlay_level, OVERLAY_LEVELS["full"])

    def scene_rect(self):
        """Pixel rectangle the 3-D scene draws into: the whole window
        unless a viewport has been set."""
        width, height = self.size
        if self.viewport is None:
            return (0, 0, width, height)
        x, y, w, h = self.viewport
        return (int(x), int(y), max(1, int(w)), max(1, int(h)))

    def _draw_scene_pass(self, fbo, mvp, eye, sky, rect):
        mgl = self.moderngl
        x, y, width, height = rect
        fbo.use()
        self.ctx.viewport = (x, y, width, height)
        fbo.clear(*sky["clear"], 1.0, viewport=(x, y, width, height))
        self.scene_prog["u_mvp"].write(np.ascontiguousarray(mvp.T).tobytes())
        self.scene_prog["u_camera"].value = tuple(map(float, eye))
        self.scene_prog["u_light"].value = sky["light"]
        self.scene_prog["u_fog_color"].value = sky["fog"]
        self.scene_prog["u_fog_density"].value = sky["fogd"]
        self.ctx.enable(mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.depth_mask = True
        self.opaque.draw(self._frame_opaque)
        self.ctx.depth_mask = False
        self.transparent.draw(self._frame_transparent)
        self.ctx.depth_mask = True

    def render(self, t, present=True):
        scene, shot, idx, prog = self.locate(t)
        env = self.environment(scene)
        sky = SKIES.get(env.sky, SKIES["day"])
        self._frame_opaque, self._frame_transparent, targets = build_frame(
            env, list(scene.world), t, shot, prog)
        # What the camera could be pointed at this frame. The scene
        # composer offers these as the focus choices, so the list is
        # always what the scene really contains.
        self.last_targets = targets
        cam = shot_camera(shot, targets, prog, self.yaw_off, self.pitch_off,
                          self.dist_scale, self.mode_override)
        width, height = self.size
        rect = self.scene_rect()
        aspect = rect[2] / max(1, rect[3])
        if self.viewport is not None:
            # Wipe the whole window first: the scene only repaints its own
            # rectangle, and the editor chrome around it is drawn by the
            # overlay on top.
            self.screen_fbo.use()
            self.ctx.viewport = (0, 0, width, height)
            self.screen_fbo.clear(0.04, 0.06, 0.09, 1.0)

        if cam.mode <= 3:
            projection = perspective_matrix(cam.fov, aspect, 0.06, 320.0)
            fwd = (cam.target - cam.eye)
            view = look_matrix(cam.eye, fwd, np.array([0.0, 0.0, 1.0]))
            self._draw_scene_pass(self.screen_fbo, projection @ view,
                                  cam.eye, sky, rect)
        else:
            face_proj = perspective_matrix(90.0, 1.0, 0.06, 320.0)
            for i, (fwd, up) in enumerate(cube_faces(cam)):
                view = look_matrix(cam.eye, np.asarray(fwd, np.float64),
                                   np.asarray(up, np.float64))
                self._draw_scene_pass(self.face_fbo[i], face_proj @ view,
                                      cam.eye, sky,
                                      (0, 0, self.face_size, self.face_size))
            self.screen_fbo.use()
            self.ctx.viewport = rect
            self.screen_fbo.clear(0.01, 0.02, 0.04, 1.0, viewport=rect)
            self.ctx.disable(self.moderngl.DEPTH_TEST)
            for i, tex in enumerate(self.face_tex):
                tex.use(i)
                self.pano_prog[f"u_face{i}"].value = i
            self.pano_prog["u_mode"].value = int(cam.mode)
            self.pano_prog["u_aspect"].value = aspect
            self.pano_vao.render(mode=5)

        self.ctx.viewport = (0, 0, width, height)
        overlay = self.draw_overlay(scene, shot, idx, prog, t)
        raw = self.pygame.image.tostring(overlay, "RGBA", True)
        self.overlay_tex.write(raw)
        self.ctx.disable(self.moderngl.DEPTH_TEST)
        self.ctx.enable(self.moderngl.BLEND)
        self.overlay_tex.use(0)
        self.blit_prog["u_texture"].value = 0
        self.blit_vao.render(mode=5)
        self.ctx.enable(self.moderngl.DEPTH_TEST)
        if present and not self.headless:
            self.pygame.display.flip()

    # ---- overlay -------------------------------------------------------

    def draw_overlay(self, scene, shot, idx, prog, t):
        pygame = self.pygame
        width, height = self.size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        white = (233, 240, 246)
        cyan = (68, 205, 255)
        amber = (255, 173, 64)
        muted = (140, 156, 170)
        scale = height / 1080.0

        def px(v):
            return max(1, int(v * scale))

        show = self.overlay_flags()

        # title strip
        if show["title"]:
            title_font = self.font(px(30), bold=True)
            surface.blit(title_font.render(self.pres.title, True, white),
                         (px(36), px(24)))
            sub = f"{scene.title or scene.slug}  ·  shot {idx + 1}" \
                  f"/{len(self.pres.all_shots())}"
            surface.blit(self.font(px(19)).render(sub, True, muted),
                         (px(36), px(62)))

        # lower-third caption
        if shot.caption and show["caption"]:
            cap_font = self.font(px(26), bold=True)
            text = cap_font.render(shot.caption, True, white)
            bar = pygame.Surface((text.get_width() + px(44), px(52)),
                                 pygame.SRCALPHA)
            bar.fill((8, 16, 26, 200))
            pygame.draw.rect(bar, cyan, (0, 0, px(6), px(52)))
            bar.blit(text, (px(24), px(11)))
            surface.blit(bar, (px(36), height - px(120)))

        # progress ribbon
        if show["progress"]:
            total = max(1e-6, self.pres.duration)
            pygame.draw.rect(surface, (30, 44, 58),
                             (0, height - px(6), width, px(6)))
            pygame.draw.rect(surface, cyan,
                             (0, height - px(6),
                              int(width * (t % total) / total), px(6)))

        # the floatable second screen
        panel = shot.panel
        visible = panel.visible if panel else False
        if self.panel_override is not None:
            visible = self.panel_override and panel is not None
        if not show["panel"]:
            visible = False
        if panel and visible:
            self._draw_panel(surface, panel, scale)
        return surface

    def _draw_panel(self, surface, panel, scale):
        pygame = self.pygame
        width, height = self.size

        def px(v):
            return max(1, int(v * scale))
        lines = []
        if panel.title:
            lines.append(("title", panel.title))
        for b in panel.bullets:
            lines.append(("bullet", b))
        for e in panel.equations:
            lines.append(("eq", e))
        for label, value in panel.stats:
            lines.append(("stat", (label, value)))
        # Size the card to its widest line, capped to a fraction of the
        # screen. Probe each kind with the SAME font it actually renders
        # with below — the title is larger and bold, and a stat line is a
        # left label plus a separately right-aligned bold value, not one
        # run of plain text.
        pw = px(470)
        bullet_font = self.font(px(20))
        title_font = self.font(px(24), bold=True)
        stat_label_font = self.font(px(19))
        stat_value_font = self.font(px(21), bold=True)
        for kind, payload in lines:
            if kind == "title":
                pw = max(pw, title_font.size(str(payload))[0] + px(64))
            elif kind == "stat":
                label_w = stat_label_font.size(str(payload[0]))[0]
                value_w = stat_value_font.size(str(payload[1]))[0]
                pw = max(pw, label_w + value_w + px(88))
            else:
                text = ("· " if kind == "bullet" else "") + str(payload)
                pw = max(pw, bullet_font.size(text)[0] + px(64))
        pw = min(pw, int(width * 0.46))

        def wrap(font, text, max_w):
            words = str(text).split(" ")
            out, cur = [], ""
            for word in words:
                trial = (cur + " " + word).strip()
                if not cur or font.size(trial)[0] <= max_w:
                    cur = trial
                else:
                    out.append(cur)
                    cur = word
            out.append(cur)
            return out

        # Expand every logical line into 1+ visual rows that actually fit
        # inside pw — capping pw to the content's widest line only avoids
        # clipping if nothing is EVER too wide for that cap; a single long
        # bullet or stat value still needs to wrap across rows, or it
        # overflows the card exactly like the width alone used to.
        rows: list[tuple] = []
        for kind, payload in lines:
            if kind == "title":
                for seg in wrap(title_font, payload, pw - px(40)):
                    rows.append(("title", seg))
            elif kind == "bullet":
                segs = wrap(bullet_font, "· " + str(payload), pw - px(48))
                for i, seg in enumerate(segs):
                    rows.append(("bullet", seg if i == 0 else "  " + seg))
            elif kind == "eq":
                for seg in wrap(bullet_font, payload, pw - px(60)):
                    rows.append(("eq", seg))
            else:
                label, value = payload
                label_w = stat_label_font.size(str(label))[0]
                room = pw - px(48) - label_w
                if stat_value_font.size(str(value))[0] <= max(room, px(80)):
                    rows.append(("stat", (label, value)))
                else:
                    rows.append(("stat_label", label))
                    for seg in wrap(stat_value_font, value, pw - px(60)):
                        rows.append(("stat_value", seg))
        line_h = px(30)
        ph = px(30) + line_h * len(rows) + px(16)
        position = self.panel_position_override or panel.position
        if position == "right":
            x, y = width - pw - px(30), px(110)
        elif position == "left":
            x, y = px(30), px(110)
        elif position == "bottom":
            x, y = (width - pw) // 2, height - ph - px(140)
        else:
            x = int(panel.anchor[0] * width)
            y = int(panel.anchor[1] * height)
        card = pygame.Surface((pw, ph), pygame.SRCALPHA)
        card.fill((7, 14, 24, 216))
        pygame.draw.rect(card, (68, 205, 255), (0, 0, pw, px(5)))
        yy = px(18)
        for kind, payload in rows:
            if kind == "title":
                card.blit(title_font.render(
                    payload, True, (255, 214, 130)), (px(20), yy))
            elif kind == "bullet":
                card.blit(bullet_font.render(
                    payload, True, (226, 234, 240)), (px(24), yy + px(3)))
            elif kind == "eq":
                card.blit(bullet_font.render(
                    payload, True, (120, 226, 176)), (px(30), yy + px(3)))
            elif kind == "stat":
                label, value = payload
                card.blit(stat_label_font.render(
                    str(label), True, (150, 166, 180)), (px(24), yy + px(4)))
                text = stat_value_font.render(
                    str(value), True, (255, 255, 255))
                card.blit(text, (pw - text.get_width() - px(22), yy + px(2)))
            elif kind == "stat_label":
                card.blit(stat_label_font.render(
                    str(payload), True, (150, 166, 180)), (px(24), yy + px(4)))
            elif kind == "stat_value":
                # a wrapped continuation line, not the single-line label+
                # value case above: left-align under the label instead of
                # right-aligning each wrapped chunk independently, which
                # read as a ragged block.
                card.blit(stat_value_font.render(
                    str(payload), True, (255, 255, 255)),
                    (px(40), yy + px(2)))
            yy += line_h
        surface.blit(card, (x, y))

    # ---- live app ------------------------------------------------------

    def handle_events(self):
        pygame = self.pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    return False
                if key == pygame.K_SPACE:
                    self.playing = not self.playing
                elif key == pygame.K_RIGHT:
                    idx, _ = self.pres.shot_at(self.timeline)
                    self.timeline = self.pres.shot_start(
                        (idx + 1) % len(self.pres.all_shots()))
                    self._reset_view()
                elif key == pygame.K_LEFT:
                    idx, _ = self.pres.shot_at(self.timeline)
                    self.timeline = self.pres.shot_start(
                        (idx - 1) % len(self.pres.all_shots()))
                    self._reset_view()
                elif key == pygame.K_HOME:
                    self.timeline = 0.0
                    self._reset_view()
                elif key == pygame.K_r:
                    self._reset_view()
                elif key == pygame.K_o:
                    # cycle: script default -> hidden -> forced on
                    cycle = {None: False, False: True, True: None}
                    self.panel_override = cycle[self.panel_override]
                elif key == pygame.K_c:
                    # cycle how much writing is burned into the picture
                    levels = list(OVERLAY_LEVELS)
                    nxt = levels[(levels.index(self.overlay_level) + 1)
                                 % len(levels)]
                    self.overlay_level = nxt
                elif key == pygame.K_p:
                    current = self.panel_position_override or "right"
                    nxt = PANEL_POSITIONS[
                        (PANEL_POSITIONS.index(current) + 1)
                        % len(PANEL_POSITIONS)]
                    self.panel_position_override = nxt
                elif pygame.K_1 <= key <= pygame.K_6:
                    self.mode_override = key - pygame.K_0
                elif key == pygame.K_0:
                    self.mode_override = None
                elif key == pygame.K_s and not self.headless:
                    self.screenshot()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):
                    self.dragging = True
                elif event.button == 4:
                    self.dist_scale = max(0.3, self.dist_scale * 0.9)
                elif event.button == 5:
                    self.dist_scale = min(4.0, self.dist_scale * 1.11)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    self.dragging = False
            if event.type == pygame.MOUSEMOTION and self.dragging:
                self.yaw_off -= event.rel[0] * 0.25
                self.pitch_off += event.rel[1] * 0.2
        return True

    def _reset_view(self):
        self.yaw_off = self.pitch_off = 0.0
        self.dist_scale = 1.0

    def screenshot(self, path=None):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if path is None:
            path = self.output_dir / f"frame_{int(time.time() * 1000)}.png"
        raw = self.capture_rgb()
        image = self.pygame.image.fromstring(raw, self.size, "RGB")
        image = self.pygame.transform.flip(image, False, True)
        self.pygame.image.save(image, str(path))
        return path

    def capture_rgb(self):
        self.ctx.finish()
        return self.screen_fbo.read((0, 0, *self.size), components=3,
                                    alignment=1)

    def run(self):
        clock = self.pygame.time.Clock()
        running = True
        while running:
            dt = min(0.1, clock.tick(60) / 1000.0)
            running = self.handle_events()
            if self.playing:
                previous = self.pres.shot_at(self.timeline)[0]
                self.timeline += dt * self.speed
                if self.pres.shot_at(self.timeline)[0] != previous:
                    self._reset_view()
            self.render(self.timeline)
        self.pygame.quit()

    # ---- deterministic export -----------------------------------------

    def apply_narration(self, cache_dir: Path, ffmpeg=None):
        """Voice every shot, stretch durations, return narration payload."""
        shots = self.pres.all_shots()
        segments = [" ".join(shot.narration) for _sc, shot in shots]
        clips, speech = narrate.prepare_narration(
            segments, cache_dir, self.pres.voice, self.pres.voice_rate,
            ffmpeg)
        stretched = narrate.stretch_durations(
            [shot.duration for _sc, shot in shots], speech)
        new_scenes = []
        cursor = 0
        for scene in self.pres.scenes:
            new_shots = []
            for shot in scene.shots:
                new_shots.append(replace(shot,
                                         duration=stretched[cursor]))
                cursor += 1
            new_scenes.append(replace(scene, shots=tuple(new_shots)))
        self.pres = replace(self.pres, scenes=tuple(new_scenes))
        starts = [self.pres.shot_start(i) for i in range(len(shots))]
        return segments, clips, speech, starts

    def export(self, path: Path, fps=None, narration=True, ffmpeg=None,
               overlay=None):
        """Render the whole presentation to an MP4.

        ``overlay`` picks how much writing is burned into the picture (see
        :data:`OVERLAY_LEVELS`). Whatever is chosen, narration is still
        spoken and still written next to the video as a .srt subtitle
        file, so a caption-free video can still be subtitled later by
        anyone who wants captions."""
        from two_v_demo.audio import resolve_executable
        if overlay:
            if overlay not in OVERLAY_LEVELS:
                raise ValueError(
                    f"unknown overlay level {overlay!r}; choose one of "
                    f"{', '.join(OVERLAY_LEVELS)}")
            self.overlay_level = overlay
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = resolve_executable("ffmpeg", ffmpeg)
        fps = fps or self.pres.fps
        track = None
        if narration:
            cache = path.parent / f"{path.stem}-voice"
            segments, clips, speech, starts = self.apply_narration(
                cache, ffmpeg_exe)
            if any(c is not None for c in clips):
                track = path.parent / f"{path.stem}-narration.m4a"
                narrate.build_track(clips, starts, self.pres.duration,
                                    track, ffmpeg_exe)
                narrate.write_srt(path.with_suffix(".srt"), segments,
                                  starts, speech)
        total = self.pres.duration
        width, height = self.size
        render_path = (path.parent / f".{path.stem}-silent.mp4"
                       if track else path)
        command = [
            ffmpeg_exe, "-y", "-v", "error",
            "-f", "rawvideo", "-pixel_format", "rgb24",
            "-video_size", f"{width}x{height}",
            "-framerate", str(fps), "-i", "-",
            "-vf", "vflip", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(render_path)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        frames = int(math.ceil(total * fps))
        self._reset_view()
        try:
            for frame in range(frames):
                t = frame / fps
                self.render(t, present=False)
                process.stdin.write(self.capture_rgb())
                if frame % (fps * 5) == 0:
                    print(f"\r  rendering {t:6.1f}s / {total:6.1f}s",
                          end="", flush=True)
            process.stdin.close()
            code = process.wait()
        except BaseException:
            process.kill()
            raise
        print()
        if code != 0:
            raise RuntimeError(f"ffmpeg exited with {code}")
        if track:
            subprocess.run([
                ffmpeg_exe, "-y", "-v", "error", "-i", str(render_path),
                "-i", str(track), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "copy", "-shortest",
                "-movflags", "+faststart", str(path)], check=True)
            Path(render_path).unlink(missing_ok=True)
        print(f"saved {path} ({total:.1f}s @ {fps}fps)")
        return path
