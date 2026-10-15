"""The world's window: the dome's and the zome's camera and controls, and the editing tools.

It moves exactly as the worlds it grew from move -- mouse-look with a crosshair,
Tab to free the mouse, the wheel to zoom, W A S D and the arrows to walk at eye
height, F to fly, PageUp / PageDown up and down in fly mode, R back to the start,
L to the jigs, G V P T for the grid, wood, skins and jigs, B F12 F1 F2 -- and the
editing is on keys those worlds leave free (see :data:`world3d.app.HELP`).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import pieces as pc
from . import structures as st
from .app import HELP, STEPS, VIEWS, World, _aim, _config, _dome, draw, panel_surface, text_surface, upload_all


#: Every control, one per row: (key, what it does). A row with no action is a heading.
LEGEND: tuple[tuple[str, str], ...] = (
    ("CONTROLS", "(F1 hides this)"),
    ("THE WORLD", ""),
    ("Mouse", "look around"),
    ("Tab", "free the mouse / look again"),
    ("Mouse wheel", "zoom on the crosshair"),
    ("W A S D, arrows", "walk"),
    ("F", "walk / fly"),
    ("PageUp / PageDown", "up and down (fly mode)"),
    ("Shift", "faster"),
    ("Left click", "select (length, section, board ft)"),
    ("R", "camera back to the start"),
    ("L", "camera to the next jig"),
    ("G", "ground grid on / off"),
    ("V", "wood on / off"),
    ("P", "skins on / off"),
    ("T", "jigs on / off"),
    ("B", "cut list to the library"),
    ("F12", "screenshot"),
    ("F2", "readouts on / off"),
    ("Esc", "free the mouse; again to quit"),
    ("EDITING", ""),
    ("Delete", "delete the selected piece"),
    ("Ctrl+X", "saw the piece at the crosshair"),
    ("Insert", "add a strut, then click 2 ends"),
    ("Ctrl+1 / 2 / 3", "strut: wedge / square / half trunk"),
    ("Alt+arrows", "move the selected piece"),
    ("Alt+PageUp / Down", "move it up / down"),
    ("Alt+Shift+arrows", "move the whole active layer"),
    ("Ctrl+D", "copy the selected piece"),
    ("Ctrl+[  Ctrl+]", "grid step 1 / 3 / 6 / 12 / 24 in"),
    ("Ctrl+Z", "undo"),
    ("Ctrl+S", "save"),
    ("Layers panel", "Tab, then click: show / active; right-click: lock"),
)


def legend_surface():
    """The controls as a two-column table: keys left, actions right, nothing cut off."""
    import pygame
    from .app import _font
    font = _font(15)
    key_w = max(font.size(k)[0] for k, a in LEGEND if a) + 18
    act_w = max(font.size(a)[0] for _k, a in LEGEND)
    h = 20
    surf = pygame.Surface((key_w + act_w + 24, h * len(LEGEND) + 12), pygame.SRCALPHA)
    surf.fill((12, 16, 22, 205))
    for i, (k, a) in enumerate(LEGEND):
        y = 6 + i * h
        heading = not a or i == 0
        surf.blit(font.render(k, True, (255, 205, 130) if heading else (150, 210, 255)), (10, y))
        if a:
            surf.blit(font.render(a, True, (255, 205, 130) if i == 0 else (235, 235, 230)), (10 + key_w, y))
    return surf


class App:
    def __init__(self) -> None:
        import moderngl
        import pygame

        self.d = _dome()
        pygame.init()
        for attr, val in ((pygame.GL_CONTEXT_MAJOR_VERSION, 3), (pygame.GL_CONTEXT_MINOR_VERSION, 3),
                          (pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE),
                          (pygame.GL_DEPTH_SIZE, 24)):
            pygame.display.gl_set_attribute(attr, val)
        self.width, self.height = 1440, 860
        pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption("DomeSim world -- foundation, dome, zome")
        self.ctx = moderngl.create_context()
        self.renderer = self.d.Renderer(self.ctx)
        self.world = World()
        if self.world.doc.load():
            self.world.message = f"opened your saved world ({len(self.world.doc.ops)} edits)"
        self.sphere_r = float(st.dome_model().topology.sphere_radius_in)
        self.reset_camera()
        self.zoom = 0
        self.jig_view = 0
        self.clock = pygame.time.Clock()
        self.dirty = True
        self.show_help = True              # the controls legend stays on screen; F1 hides it
        self._legend_size = None
        self._errors: set[str] = set()
        self.show_hud = True
        self.running = True
        self._capture(True)
        print(HELP)

    # -- the originals' camera -------------------------------------------
    def reset_camera(self) -> None:
        """Where the dome's world starts you -- in front of the dome, at eye height, looking at
        it -- moved back just far enough to stand outside the foundation it now sits on."""
        self.cam = self.d.FirstPersonCamera(_config(), self.sphere_r)
        apothem = float(np.min(np.linalg.norm(st.foundation_model().crown[:, :2], axis=1))) * np.cos(np.pi / 5)
        self.cam.position[1] = -max(self.sphere_r * 1.30, apothem + 48.0)

    def fov(self) -> float:
        return 60.0 - self.zoom * (45.0 / 8)

    def _capture(self, on: bool) -> None:
        import pygame
        self.captured = on
        pygame.event.set_grab(on)
        pygame.mouse.set_visible(not on)
        pygame.mouse.get_rel()

    def vp(self):
        proj = self.d.perspective_matrix(self.fov(), self.width / max(1, self.height), 2.0, 40000.0)
        return proj @ self.cam.view_matrix()

    def ray(self, pos=None):
        if pos is None or self.captured:
            return self.cam.position.copy(), self.cam.forward
        x, y = pos
        inv = np.linalg.inv(self.vp())
        nx, ny = 2 * x / self.width - 1, 1 - 2 * y / self.height
        a = inv @ np.array([nx, ny, -1.0, 1.0])
        b = inv @ np.array([nx, ny, 1.0, 1.0])
        a, b = a[:3] / a[3], b[:3] / b[3]
        return a, (b - a) / np.linalg.norm(b - a)

    def panel_row(self, pos) -> str | None:
        if self.captured or pos is None:
            return None
        x, y = pos
        row_h, top = 20, 24 + 6 + 20
        if not (24 <= x <= 24 + 470):
            return None
        i = (y - top) // row_h
        return st.LAYER_KEYS[i] if 0 <= i < len(st.LAYER_KEYS) else None

    def _toggle(self, keys) -> None:
        on = not any(self.world.doc.visible[k] for k in keys)
        for k in keys:
            self.world.doc.visible[k] = on

    # -- keys --------------------------------------------------------------
    def key(self, e) -> None:
        import pygame
        w, k = self.world, e.key
        ctrl, shift, alt = e.mod & pygame.KMOD_CTRL, e.mod & pygame.KMOD_SHIFT, e.mod & pygame.KMOD_ALT
        step = w.step
        # the originals' keys
        if k == pygame.K_ESCAPE:
            if w.tool == "add" or w.pending is not None:
                w.tool, w.pending, w.message = "select", None, "stopped adding"
            elif self.captured:
                self._capture(False)
            else:
                self.running = False
        elif k == pygame.K_TAB:
            self._capture(not self.captured)
        elif k == pygame.K_f and not ctrl:
            self.cam.fly_mode = not self.cam.fly_mode
        elif k == pygame.K_r and not ctrl:
            self.reset_camera()
            self.zoom = 0
        elif k == pygame.K_l:
            names = ("dome_jig", "zome_jig", "foundation_jig")
            name = names[self.jig_view % len(names)]
            self.jig_view += 1
            _aim(self.cam, *VIEWS[name])
            self.cam.fly_mode = False
            self.cam.walk_height = self.cam.position[2]
            w.message = f"camera at the {name.replace('_', ' ')} (R: back to the start)"
        elif k == pygame.K_g:
            w.grid = not w.grid
        elif k == pygame.K_v:
            self._toggle(("foundation", "dome", "zome"))
        elif k == pygame.K_p:
            self._toggle(("foundation_deck", "dome_skin", "zome_skin"))
        elif k == pygame.K_t:
            self._toggle(("foundation_jig", "dome_jig", "zome_jig"))
        elif k == pygame.K_b:
            w.message = f"cut list: {w.doc.export_cut_list()}"
        elif k == pygame.K_F1:
            self.show_help = not self.show_help
        elif k == pygame.K_F2:
            self.show_hud = not self.show_hud
        elif k == pygame.K_F12:
            self.screenshot()
        # editing
        elif k in (pygame.K_DELETE, pygame.K_BACKSPACE):
            w.delete_selected()
        elif ctrl and k == pygame.K_x:
            w.tool = "cut"
            w.click(*self.ray(None if self.captured else pygame.mouse.get_pos()))
            w.tool = "select"
        elif k == pygame.K_INSERT:
            w.tool, w.pending = ("select", None) if w.tool == "add" else ("add", None)
            w.message = ("click the first end of the new strut (Esc to stop)" if w.tool == "add"
                         else "stopped adding")
        elif ctrl and k in (pygame.K_1, pygame.K_2, pygame.K_3):
            w.section = pc.SECTIONS[k - pygame.K_1]
            w.message = f"new struts: {w.section}"
        elif ctrl and k == pygame.K_z:
            w.message = "undone" if w.doc.undo() else "nothing to undo"
        elif ctrl and k == pygame.K_s:
            w.message = f"saved: {w.doc.save()}"
        elif ctrl and k == pygame.K_d:
            w.move_selected((step, 0, 0), copy=True)
        elif ctrl and k == pygame.K_LEFTBRACKET:
            w.step = STEPS[max(0, STEPS.index(w.step) - 1)]
            w.message = f"grid {w.step:g} in"
        elif ctrl and k == pygame.K_RIGHTBRACKET:
            w.step = STEPS[min(len(STEPS) - 1, STEPS.index(w.step) + 1)]
            w.message = f"grid {w.step:g} in"
        elif alt and k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                           pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            delta = {pygame.K_LEFT: (-step, 0, 0), pygame.K_RIGHT: (step, 0, 0), pygame.K_UP: (0, step, 0),
                     pygame.K_DOWN: (0, -step, 0), pygame.K_PAGEUP: (0, 0, step),
                     pygame.K_PAGEDOWN: (0, 0, -step)}[k]
            w.move_selected(delta, whole_layer=bool(shift))
        else:
            return
        self.dirty = True

    def report(self, exc: Exception) -> None:
        """A fault while running: written in full to world3d/crash.log, named on screen, and the
        world kept open rather than closed."""
        import datetime as _dt
        import traceback
        text = "".join(traceback.format_exception(exc))
        key = text.strip().splitlines()[-1] if text.strip() else repr(exc)
        if key not in self._errors:
            self._errors.add(key)
            log = Path(__file__).resolve().parent / "crash.log"
            with log.open("a", encoding="utf-8") as f:
                f.write(f"--- {_dt.datetime.now().isoformat(timespec='seconds')}\n{text}\n")
            print(text)
        self.world.message = f"Something went wrong: {key[:110]} -- details in world3d/crash.log"
        self.dirty = True

    def screenshot(self) -> None:
        import medialib
        from PIL import Image
        path = medialib.new_path("world-screenshot.png")
        raw = self.ctx.screen.read(components=3, alignment=1)
        Image.frombytes("RGB", (self.width, self.height), raw).transpose(Image.FLIP_TOP_BOTTOM).save(path)
        self.world.message = f"screenshot: {path}"

    def click(self, button: int, pos) -> None:
        row = self.panel_row(pos)
        if row is not None:
            doc = self.world.doc
            if button == 1:
                if pos[0] < 24 + 44:
                    doc.visible[row] = not doc.visible[row]
                else:
                    doc.active = row
                    doc.visible[row] = True
            elif button == 3:
                doc.locked[row] = not doc.locked[row]
            self.dirty = True
            return
        if button == 1:
            self.world.click(*self.ray(pos))
            self.dirty = True

    def handle(self) -> None:
        import pygame
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                self.width, self.height = e.w, e.h
            elif e.type == pygame.MOUSEMOTION and self.captured:
                self.cam.mouse_look(*e.rel)
            elif e.type == pygame.MOUSEWHEEL:
                self.zoom = max(0, min(8, self.zoom + (1 if e.y > 0 else -1)))
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                self.click(e.button, None if self.captured else e.pos)
            elif e.type == pygame.KEYDOWN:
                self.key(e)

    def update(self, dt: float) -> None:
        """Walking as the originals walk. With Ctrl or Alt held the keys edit instead."""
        import pygame
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        editing = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_ALT))
        sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        arrows = (0, 0) if editing else (keys[pygame.K_UP] - keys[pygame.K_DOWN],
                                         keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        walk = 0 if editing else 1
        fwd = (keys[pygame.K_w] - keys[pygame.K_s]) * walk + arrows[0] * (self.zoom < 8)
        right = (keys[pygame.K_d] - keys[pygame.K_a]) * walk + arrows[1] * (self.zoom < 8)
        up = 0 if editing else keys[pygame.K_PAGEUP] - keys[pygame.K_PAGEDOWN]
        self.cam.move(fwd, right, up, dt, sprint)
        if self.zoom >= 8 and any(arrows):
            self.cam.pan(arrows[1], arrows[0], dt, sprint)

    def _crosshair(self):
        import pygame
        surf = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.line(surf, (255, 255, 255, 220), (11, 2), (11, 20), 2)
        pygame.draw.line(surf, (255, 255, 255, 220), (2, 11), (20, 11), 2)
        return surf

    def render(self) -> None:
        import pygame
        if self.dirty:
            upload_all(self.renderer, self.world)
            self.renderer.upload_overlay("panel", panel_surface(self.world))
            self.renderer.upload_overlay("cross", self._crosshair())
            self.dirty = False
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear(0.62, 0.74, 0.86, 1.0, depth=1.0)
        draw(self.renderer, self.vp(), self.world)
        r = self.renderer
        if self.show_hud:
            r.render_overlay("panel", self.width, self.height, 24, 24)
            lines = self.world.info_lines()
            if not self.captured:
                lines.append("mouse free: click a layer or a piece; Tab to look around again")
            if lines != getattr(self, "_info_lines", None):
                r.upload_overlay("info", text_surface(lines, 900))
                self._info_lines = lines
            info = r.overlays["info"]
            r.render_overlay("info", self.width, self.height, 24, self.height - info.height - 24)
        if self.show_help:
            if self._legend_size != (self.width, self.height):
                r.upload_overlay("legend", legend_surface())
                self._legend_size = (self.width, self.height)
            legend = r.overlays["legend"]
            r.render_overlay("legend", self.width, self.height, self.width - legend.width - 24, 24)
        cross = r.overlays["cross"]
        r.render_overlay("cross", self.width, self.height, (self.width - cross.width) // 2,
                         (self.height - cross.height) // 2)
        pygame.display.flip()

    def run(self, frames: int = 0) -> None:
        import pygame
        n = 0
        while self.running:
            dt = min(self.clock.tick(120) / 1000.0, 0.05)
            try:
                self.handle()
                self.update(dt)
                self.render()
            except Exception as exc:          # noqa: BLE001 -- say what went wrong, keep the world open
                self.report(exc)
            n += 1
            if frames and n >= frames:
                break
        self.renderer.release()
        pygame.quit()
