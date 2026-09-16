"""Dome Park -- serviced pads, and the network they belong to.

An RV park for domes. A landowner builds pads: a deck, a power pedestal, a
water and drain stub, optionally a rotating base and a utility column. A dome
owner brings the house and plugs in. Nobody rents a building from anybody.

This tool shows the site. Every pad on it is priced by :mod:`park_model`,
every dome standing on one is the Dome Creator's own building drawn through
the Creator's own shader, and the arithmetic in the corner is the same
arithmetic the film quotes -- there is no second set of numbers.

Run it
------
    py -3.12 dome_park.py                 # the site, walkable by camera
    py -3.12 -m project_agent ...         # or from the launcher's tab

Controls
--------
    drag / wheel      orbit and zoom
    [ and ]           select the previous or next pad
    D                 cycle this pad's deck: gravel, concrete, wood
    R                 rotating base on this pad, on or off
    U                 utility column on this pad, on or off
    V                 lease this pad, or empty it
    space             run the sun, so tracking pads follow it
    H                 hide the panel
    S                 save a screenshot
    Escape            quit
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

import launcher_common as lc
import park_model
import park_world

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SKY = (0.53, 0.68, 0.84)
PANEL_BG = (12, 16, 22, 232)
INK = (232, 240, 248)
DIM = (150, 168, 186)
ACCENT = (95, 210, 255)
MONEY = (120, 226, 160)
WARN = (255, 178, 90)


def _matrix(offset, yaw_deg: float = 0.0, lift: float = 0.0) -> np.ndarray:
    angle = math.radians(yaw_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    return np.array([
        [cos, -sin, 0.0, float(offset[0])],
        [sin, cos, 0.0, float(offset[1])],
        [0.0, 0.0, 1.0, float(lift)],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float32)


def perspective(fov_deg: float, aspect: float, near: float,
                far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = f / aspect
    matrix[1, 1] = f
    matrix[2, 2] = (far + near) / (near - far)
    matrix[2, 3] = (2.0 * far * near) / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def look_at(eye, target, up=(0.0, 0.0, 1.0)) -> np.ndarray:
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    forward = target - eye
    forward /= np.linalg.norm(forward) or 1.0
    right = np.cross(forward, np.asarray(up, dtype=np.float32))
    right /= np.linalg.norm(right) or 1.0
    true_up = np.cross(right, forward)
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, :3], matrix[1, :3], matrix[2, :3] = right, true_up, -forward
    matrix[0, 3] = -float(np.dot(right, eye))
    matrix[1, 3] = -float(np.dot(true_up, eye))
    matrix[2, 3] = float(np.dot(forward, eye))
    return matrix


class DomeParkApp:
    """The site, its pads, and the domes parked on them."""

    def __init__(self, size=(1600, 900), hidden: bool = False,
                 park: park_world.Park | None = None) -> None:
        import moderngl
        import pygame

        self.pygame = pygame
        self.moderngl = moderngl
        pygame.init()
        pygame.font.init()
        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        if hidden and hasattr(pygame, "HIDDEN"):
            flags |= pygame.HIDDEN
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        # Ask for a deep depth buffer explicitly. A driver handing back 16
        # bits, combined with a wide near/far ratio, makes a pad 16 cm above
        # the ground z-fight with it in horizontal bands.
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.set_caption("Dome Park")
        pygame.display.set_mode(size, flags)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        from two_v_demo import creator_bridge
        from two_v_demo.render_kit import (OVERLAY_FRAGMENT_SHADER,
                                           OVERLAY_VERTEX_SHADER)
        self.bridge = creator_bridge
        vertex, fragment = creator_bridge.shaders()
        self.scene_program = self.ctx.program(vertex_shader=vertex,
                                              fragment_shader=fragment)
        self.overlay_program = self.ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
        self.overlay_buffer = self.ctx.buffer(quad.tobytes())
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program, [(self.overlay_buffer, "2f", "in_position")])
        self.overlay_texture = None
        self.overlay_size = (0, 0)

        self.park = park or park_world.default_park()
        self.selected = 0
        self.show_panel = True
        self.sun_running = True
        self.sun_angle = 38.0
        self.site_buffers = None
        self.dome_cache: dict[str, dict] = {}
        self.rebuild_site()

        self.yaw, self.pitch, self.distance = 52.0, 24.0, 64.0
        self.dragging = False
        self.last_mouse = (0, 0)
        self.font = pygame.font.SysFont("Segoe UI", 17)
        self.bold = pygame.font.SysFont("Segoe UI", 19, bold=True)
        self.small = pygame.font.SysFont("Consolas", 15)

    # -- GPU ------------------------------------------------------------
    def _upload(self, mesh) -> dict:
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
            entry[kind] = self.ctx.vertex_array(self.scene_program, layout,
                                                ibo, index_element_size=4)
            entry[f"{kind}_count"] = len(indices)
            entry[f"{kind}_ibo"] = ibo
        return entry

    def _release(self, entry: dict | None) -> None:
        if not entry:
            return
        for key in ("opaque", "transparent", "opaque_ibo", "transparent_ibo",
                    "vbo"):
            item = entry.get(key)
            if item is not None:
                item.release()

    def rebuild_site(self) -> None:
        """Rebuild the ground, pads and services after an edit."""
        self._release(self.site_buffers)
        self.site_buffers = self._upload(park_world.park_mesh(self.park))

    def dome_buffers(self, placed: park_world.Placed) -> dict | None:
        """The Creator's own building for this pad, uploaded once."""
        if not placed.occupied:
            return None
        key = placed.dome
        entry = self.dome_cache.get(key)
        if entry is None:
            build = self.bridge.build(placed.dome_config(), placed.dome)
            entry = self._upload(build.mesh)
            self.dome_cache[key] = entry
        return entry

    # -- the site -------------------------------------------------------
    @property
    def current(self) -> park_world.Placed:
        return self.park.placements[self.selected]

    def edit(self, **changes) -> None:
        """Change the selected pad and rebuild what that affects."""
        placed = self.current
        pad = placed.pad
        fields = {
            "diameter_ft": pad.diameter_ft, "deck": pad.deck,
            "rotating": pad.rotating, "utility_column": pad.utility_column,
            "solar_watts": pad.solar_watts,
        }
        fields.update(changes)
        placed.pad = park_model.Pad(**fields)
        self.rebuild_site()

    def toggle_lease(self) -> None:
        placed = self.current
        if placed.occupied:
            placed.dome = ""
        else:
            fits = park_model.domes_that_fit(placed.pad.diameter_ft)
            if fits:
                placed.dome = max(fits, key=lambda d: d.floor_sqft).name
        self.rebuild_site()

    # -- drawing --------------------------------------------------------
    def camera(self):
        centre = np.array([0.0, 0.0, 2.0], dtype=np.float32)
        pitch = math.radians(max(6.0, min(80.0, self.pitch)))
        yaw = math.radians(self.yaw)
        eye = centre + np.array([
            self.distance * math.cos(pitch) * math.cos(yaw),
            self.distance * math.cos(pitch) * math.sin(yaw),
            self.distance * math.sin(pitch),
        ], dtype=np.float32)
        return eye, centre

    def sun_direction(self) -> tuple[float, float, float]:
        angle = math.radians(self.sun_angle)
        height = math.radians(34.0)
        return (-math.cos(angle) * math.cos(height),
                -math.sin(angle) * math.cos(height),
                -math.sin(height))

    def render(self, present: bool = True) -> None:
        width, height = self.pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.clear(*SKY, 1.0)
        self.ctx.enable(self.moderngl.DEPTH_TEST)

        eye, target = self.camera()
        # Near is pushed well out and far pulled in: the site is tens of
        # metres across, nothing is closer than a metre, and a 6000:1 ratio
        # spends all the depth precision on space nothing occupies.
        projection = perspective(46.0, width / max(1, height), 0.8, 400.0)
        mvp = projection @ look_at(eye, target)
        program = self.scene_program
        program["u_mvp"].write(np.ascontiguousarray(mvp.T).tobytes())
        for name, value in (("u_camera_position", tuple(float(v) for v in eye)),
                            ("u_light_direction", self.sun_direction()),
                            ("u_sky_color", SKY),
                            ("u_ghost", 0.0), ("u_cut_z", 1.0e9),
                            ("u_exposure", 1.0), ("u_headlamp", 0.0),
                            ("u_light_count", 0)):
            try:
                program[name].value = value
            except KeyError:
                pass

        identity = np.eye(4, dtype=np.float32)
        program["u_model"].write(identity.tobytes())
        self._draw(self.site_buffers, "opaque")

        for placed in self.park.placements:
            entry = self.dome_buffers(placed)
            if entry is None:
                continue
            matrix = _matrix(placed.origin, placed.heading_deg,
                             placed.dome_base_z)
            program["u_model"].write(
                np.ascontiguousarray(matrix.T).tobytes())
            self._draw(entry, "opaque")
        program["u_model"].write(identity.tobytes())

        self.ctx.depth_mask = False
        self._draw(self.site_buffers, "transparent")
        for placed in self.park.placements:
            entry = self.dome_buffers(placed)
            if entry is None:
                continue
            matrix = _matrix(placed.origin, placed.heading_deg,
                             placed.dome_base_z)
            program["u_model"].write(
                np.ascontiguousarray(matrix.T).tobytes())
            self._draw(entry, "transparent")
        program["u_model"].write(identity.tobytes())
        self.ctx.depth_mask = True

        if self.show_panel:
            self.draw_panel(width, height)
        if present:
            self.pygame.display.flip()

    def _draw(self, entry: dict | None, kind: str) -> None:
        if not entry:
            return
        vao = entry.get(kind)
        if vao is None:
            return
        vao.render(self.moderngl.TRIANGLES, vertices=entry[f"{kind}_count"])

    # -- the panel ------------------------------------------------------
    def panel_lines(self) -> list[tuple[str, tuple[int, int, int], object]]:
        placed = self.current
        pad = placed.pad
        year = pad.year()
        figures = self.park.economics()
        fits = park_model.domes_that_fit(pad.diameter_ft)
        catalogue = park_model.dome_catalogue()
        rows: list[tuple[str, tuple[int, int, int], object]] = [
            ("DOME PARK", ACCENT, self.bold),
            (f"{figures['pads']} pads, {figures['occupied']} leased", DIM,
             self.font),
            ("", DIM, self.small),
            (f"site build     ${figures['build_cost']:>11,.0f}", INK, self.small),
            (f"net a year     ${figures['net_year']:>11,.0f}", MONEY, self.small),
            (f"payback         {figures['payback_years']:>11.1f} yr", MONEY,
             self.small),
            (f"service run     {figures['spine_metres']:>11.0f} m", DIM,
             self.small),
            ("", DIM, self.small),
            (f"PAD {self.selected + 1} of {len(self.park.placements)}", ACCENT,
             self.bold),
            (f"{pad.diameter_ft:.0f} ft, {pad.deck}"
             + (", rotating" if pad.rotating else "")
             + (", utility column" if pad.utility_column else ""), INK,
             self.font),
            (f"takes {len(fits)} of {len(catalogue)} dome designs", DIM,
             self.small),
            (placed.dome if placed.occupied else "vacant",
             MONEY if placed.occupied else WARN, self.font),
            ("", DIM, self.small),
        ]
        for label, amount in pad.cost_rows():
            rows.append((f"  {label[:30]:<30} ${amount:>9,.0f}", DIM,
                         self.small))
        rows.extend([
            (f"  {'build cost':<30} ${pad.build_cost:>9,.0f}", INK, self.small),
            ("", DIM, self.small),
            (f"  lease          ${pad.lease_per_month:>9,.0f} / month", INK,
             self.small),
            (f"  net            ${year['net']:>9,.0f} / year", MONEY,
             self.small),
            (f"  payback         {year['payback_years']:>9.1f} years", MONEY,
             self.small),
        ])
        if pad.solar_watts > 0.0:
            rows.append((f"  solar          {pad.solar_kwh_per_month:>9,.0f} "
                         "kWh / month", MONEY, self.small))
        rows.extend([
            ("", DIM, self.small),
            ("[ ] pad   D deck   R rotate   U column   V lease", DIM,
             self.small),
            ("space sun   H panel   S shot   Esc quit", DIM, self.small),
        ])
        return rows

    def draw_panel(self, width: int, height: int) -> None:
        pygame = self.pygame
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        rows = self.panel_lines()
        pad_x, pad_y = 22, 20
        line_h = 24
        box_w = 430
        box_h = pad_y * 2 + sum(line_h if text else 10 for text, _c, _f in rows)
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill(PANEL_BG)
        pygame.draw.rect(panel, (60, 92, 120), panel.get_rect(), 1)
        y = pad_y
        for text, colour, font in rows:
            if not text:
                y += 10
                continue
            panel.blit(font.render(text, True, colour), (pad_x, y))
            y += line_h
        surface.blit(panel, (20, 20))

        raw = pygame.image.tostring(surface, "RGBA", True)
        if self.overlay_texture is None or self.overlay_size != (width, height):
            if self.overlay_texture is not None:
                self.overlay_texture.release()
            self.overlay_texture = self.ctx.texture((width, height), 4, raw)
            self.overlay_size = (width, height)
        else:
            self.overlay_texture.write(raw)
        self.ctx.disable(self.moderngl.DEPTH_TEST)
        self.overlay_texture.use(0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_vao.render(self.moderngl.TRIANGLE_STRIP)
        self.ctx.enable(self.moderngl.DEPTH_TEST)

    # -- input ----------------------------------------------------------
    def handle_events(self) -> bool:
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return False
                if event.key == pg.K_LEFTBRACKET:
                    self.selected = (self.selected - 1) % len(self.park.placements)
                elif event.key == pg.K_RIGHTBRACKET:
                    self.selected = (self.selected + 1) % len(self.park.placements)
                elif event.key == pg.K_d:
                    decks = park_model.DECKS
                    nxt = decks[(decks.index(self.current.pad.deck) + 1)
                                % len(decks)]
                    self.edit(deck=nxt)
                elif event.key == pg.K_r:
                    self.edit(rotating=not self.current.pad.rotating)
                elif event.key == pg.K_u:
                    self.edit(utility_column=not self.current.pad.utility_column)
                elif event.key == pg.K_v:
                    self.toggle_lease()
                elif event.key == pg.K_SPACE:
                    self.sun_running = not self.sun_running
                elif event.key == pg.K_h:
                    self.show_panel = not self.show_panel
                elif event.key == pg.K_s:
                    print(f"saved {self.capture()}")
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pg.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.yaw += dx * 0.3
                self.pitch = max(6.0, min(80.0, self.pitch - dy * 0.25))
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEWHEEL:
                self.distance = max(14.0, min(220.0,
                                              self.distance - event.y * 3.0))
        return True

    def update(self, dt: float) -> None:
        if not self.sun_running:
            return
        self.sun_angle = (self.sun_angle + dt * 9.0) % 360.0
        # Tracking pads follow the sun; fixed pads do not, which is the whole
        # point of paying for a rotating base.
        for placed in self.park.placements:
            if placed.pad.rotating and placed.occupied:
                placed.heading_deg = self.sun_angle

    def capture(self, path: Path | None = None) -> Path:
        width, height = self.pygame.display.get_window_size()
        self.ctx.finish()
        raw = self.ctx.screen.read((0, 0, width, height), components=3,
                                   alignment=1)
        image = self.pygame.image.fromstring(raw, (width, height), "RGB")
        image = self.pygame.transform.flip(image, False, True)
        if path is None:
            path = ROOT / "shots" / f"dome_park_{int(time.time())}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pygame.image.save(image, str(path))
        return path

    def run(self) -> None:
        clock = self.pygame.time.Clock()
        running = True
        while running:
            dt = min(0.05, clock.tick(60) / 1000.0)
            running = self.handle_events()
            self.update(dt)
            self.render()
        self.pygame.quit()


# ----------------------------------------------------------------------
# Views for headless stills
# ----------------------------------------------------------------------

VIEWS = (
    ("site", 52.0, 26.0, 74.0, 0),
    ("row", 90.0, 12.0, 58.0, 1),
    ("pad", 34.0, 18.0, 26.0, 1),
    ("overhead", 68.0, 62.0, 62.0, 3),
)


def render_shots(shot_dir: Path, size=(1600, 900)) -> list[Path]:
    """One PNG per named view, with no window."""
    app = DomeParkApp(size=size, hidden=True)
    app.sun_running = False
    written: list[Path] = []
    try:
        for name, yaw, pitch, distance, selected in VIEWS:
            app.yaw, app.pitch, app.distance = yaw, pitch, distance
            app.selected = min(selected, len(app.park.placements) - 1)
            app.update(0.0)
            app.render(present=False)
            written.append(app.capture(shot_dir / f"{name}.png"))
    finally:
        app.pygame.quit()
    return written


def selftest() -> int:
    park_world.validate_park_world()
    park = park_world.default_park()
    figures = park.economics()
    assert figures["pads"] > 0 and figures["net_year"] > 0.0
    # Every leased pad must carry a dome that fits it, or the tool is drawing
    # a claim the model does not support.
    for placed in park.placements:
        if placed.occupied:
            dome = next(d for d in park_model.dome_catalogue()
                        if d.name == placed.dome)
            assert dome.pad_diameter_ft <= placed.pad.diameter_ft + 1e-9
    print(f"dome park selftest ok: {figures['pads']} pads, "
          f"{figures['occupied']} leased, "
          f"${figures['build_cost']:,.0f} to build, "
          f"{figures['payback_years']:.1f} year payback")
    return 0


def main() -> int:
    cfg = lc.consume_config("dome_park")
    action = str(cfg.get("action") or "run").lower()

    if action == "selftest":
        return selftest()

    size = (1600, 900)
    raw_size = str(cfg.get("size") or "")
    if "x" in raw_size:
        try:
            size = tuple(int(part) for part in raw_size.lower().split("x", 1))
        except ValueError:
            pass

    pad_count = int(cfg.get("pads") or 6)
    deck = str(cfg.get("deck") or "gravel")
    if deck not in park_model.DECKS:
        deck = "gravel"
    rotating = bool(cfg.get("rotating", True))
    park = park_world.default_park(pad_count=pad_count, rotating=rotating,
                                   deck=deck)

    if action == "shots":
        shot_dir = Path(cfg.get("shot_dir") or (ROOT / "shots" / "dome_park"))
        written = render_shots(shot_dir, size=size)
        for path in written:
            print(f"saved {path}")
        return 0

    app = DomeParkApp(size=size, hidden=False, park=park)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
