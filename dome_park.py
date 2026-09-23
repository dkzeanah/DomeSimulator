"""Dome Park -- serviced pads, and the network they belong to.

An RV park for domes. A landowner builds pads: a deck, a power pedestal, a
water and drain stub, optionally a rotating base and a utility column. A dome
owner brings the house and plugs in. Nobody rents a building from anybody.

This tool shows the site. Every pad on it is priced by :mod:`park_model`,
every dome standing on one is either the Dome Creator's own building drawn
through the Creator's own shader or this shop's own seed dome drawn from the
raw-wedge solver, and the arithmetic in the corner is the same arithmetic the
film quotes -- there is no second set of numbers.

Run it
------
    py -3.12 dome_park.py                 # the site, walkable by camera
    py -3.12 -m project_agent ...         # or from the launcher's tab

Controls
--------
    click                  select a pad
    double-click / F       lock the camera onto it
    O or Home              back to the overview
    drag / wheel           orbit and zoom, around whatever is in focus
    [ and ]                select the previous or next pad
    D                      cycle this pad's deck: gravel, concrete, wood
    R                      rotating base on this pad, on or off
    U                      utility column on this pad, on or off
    V                      lease this pad, or empty it
    N / Shift+N            cycle which seed is parked here
    K                      shell on or off
    L                      lift the shell clear, as the crane would
    J                      cycle the seam: hose, solid key, or nothing
    C                      swing the crane to this pad
    B                      show or hide the bill for this dome
    space                  run the sun, so tracking pads follow it
    H                      hide the panel
    S                      save a screenshot
    Escape                 quit
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
import seed_model
import seed_world

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

CLICK_SLOP_PX = 5
"""Further than this between button down and up and it was a drag, not a
click. Without it, every orbit ends by selecting whatever was under the
mouse when the user let go."""

DOUBLE_CLICK_MS = 380


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


FOV_DEG = 46.0
OVERVIEW_HEIGHT = 2.0


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
        self.show_bill = True
        self.sun_running = True
        self.sun_angle = 38.0
        self.site_buffers = None
        self.dome_cache: dict[str, dict] = {}
        self.seed_cache: dict[tuple, dict] = {}
        self.rebuild_site()

        # The camera orbits a point, and that point is the thing this tool
        # gained when pads became selectable: overview looks at the middle of
        # the site, focus looks at one pad and stays looking at it.
        self.yaw, self.pitch = 52.0, 24.0
        self.overview_distance = 64.0
        self.distance = self.overview_distance
        self.distance_goal = self.overview_distance
        self.centre = np.array([0.0, 0.0, OVERVIEW_HEIGHT], dtype=np.float64)
        self.centre_goal = self.centre.copy()
        self.focus: int | None = None

        self.dragging = False
        self.drag_start = (0, 0)
        self.drag_moved = 0
        self.last_mouse = (0, 0)
        self.last_click_ms = 0
        self.last_click_index: int | None = None

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
        """This pad's building, uploaded once and reused.

        Built at the origin, pointing along +x, and put where it belongs by
        the model matrix. Building it in place instead would mean rebuilding
        every rotating pad's dome sixty times a second."""
        if not placed.occupied:
            return None
        if placed.is_seed:
            key = (placed.seed, placed.show_shell, placed.shell_open,
                   placed.seam)
            entry = self.seed_cache.get(key)
            if entry is None:
                placement = seed_world.SeedPlacement(
                    fitout=placed.seed, show_shell=placed.show_shell,
                    shell_open=placed.shell_open, seam=placed.seam)
                entry = self._upload(seed_world.seed_mesh(placement))
                self.seed_cache[key] = entry
            return entry
        entry = self.dome_cache.get(placed.dome)
        if entry is None:
            build = self.bridge.build(placed.dome_config(), placed.dome)
            entry = self._upload(build.mesh)
            self.dome_cache[placed.dome] = entry
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
            placed.seed = ""
        elif any(p.is_seed for p in self.park.placements):
            placed.seed = seed_model.FITOUT_ORDER[0]
        else:
            fits = park_model.domes_that_fit(placed.pad.diameter_ft)
            if fits:
                placed.dome = max(fits, key=lambda d: d.floor_sqft).name
        self.rebuild_site()

    def cycle_seed(self, step: int = 1) -> None:
        """Park a different one of this shop's own seeds on this pad.

        Refused when the seed would not fit the pad it is standing on, which
        only the sauna can do -- it is narrower than the rest, so every pad
        takes it and it does not take every pad."""
        placed = self.current
        order = list(seed_model.FITOUT_ORDER)
        if placed.seed in order:
            index = (order.index(placed.seed) + step) % len(order)
        else:
            index = 0 if step > 0 else len(order) - 1
        for _try in range(len(order)):
            candidate = order[index]
            shape = seed_model.fitout(candidate).shape
            if seed_world.pad_diameter_ft(shape) <= placed.pad.diameter_ft + 1e-9:
                placed.seed = candidate
                placed.dome = ""
                return
            index = (index + step) % len(order)

    def swing_crane_to(self, index: int) -> None:
        """Point the boom at a pad, and drop the hook over its apex."""
        if self.park.crane is None:
            return
        placed = self.park.placements[index]
        crane = self.park.crane
        dx = placed.origin[0] - crane.origin[0]
        dy = placed.origin[1] - crane.origin[1]
        reach = math.hypot(dx, dy)
        apex = placed.dome_base_z
        if placed.is_seed:
            shape = placed.seed_placement().shape
            apex += (seed_world.apex_m(shape)
                     + seed_world.base_lift_m(shape))
        self.park.crane = seed_world.Crane(
            origin=crane.origin, height=crane.height,
            reach=min(reach, 26.0),
            bearing_deg=math.degrees(math.atan2(dy, dx)),
            hook_drop=max(0.8, crane.height - apex - 1.2),
            carrying=placed.is_seed and placed.shell_open)
        self.rebuild_site()

    # -- the camera -----------------------------------------------------
    def focus_radius(self, index: int) -> float:
        """How far back a pad has to be looked at to fit on screen."""
        placed = self.park.placements[index]
        span = placed.radius_m
        if placed.is_seed:
            shape = placed.seed_placement().shape
            span = max(span, seed_world.apex_m(shape)
                       + seed_world.base_lift_m(shape))
        # Fit the span into the vertical field of view, with a margin.
        return max(6.0, span / math.tan(math.radians(FOV_DEG * 0.5)) * 1.55)

    def focus_centre(self, index: int) -> np.ndarray:
        placed = self.park.placements[index]
        height = placed.dome_base_z
        if placed.is_seed:
            shape = placed.seed_placement().shape
            height += (seed_world.apex_m(shape) * 0.45
                       + seed_world.base_lift_m(shape))
        else:
            height += placed.radius_m * 0.35
        return np.array([placed.origin[0], placed.origin[1], height],
                        dtype=np.float64)

    def focus_on(self, index: int, instant: bool = False) -> None:
        """Lock the camera onto one pad. Orbiting now turns around it."""
        self.focus = index % len(self.park.placements)
        self.selected = self.focus
        self.centre_goal = self.focus_centre(self.focus)
        self.distance_goal = self.focus_radius(self.focus)
        if instant:
            self.centre = self.centre_goal.copy()
            self.distance = self.distance_goal

    def overview(self, instant: bool = False) -> None:
        """Back out to the whole site."""
        self.focus = None
        self.centre_goal = np.array([0.0, 0.0, OVERVIEW_HEIGHT],
                                    dtype=np.float64)
        self.distance_goal = self.overview_distance
        if instant:
            self.centre = self.centre_goal.copy()
            self.distance = self.distance_goal

    def camera(self):
        pitch = math.radians(max(6.0, min(80.0, self.pitch)))
        yaw = math.radians(self.yaw)
        eye = self.centre + np.array([
            self.distance * math.cos(pitch) * math.cos(yaw),
            self.distance * math.cos(pitch) * math.sin(yaw),
            self.distance * math.sin(pitch),
        ], dtype=np.float64)
        return eye, self.centre

    def zoom_limits(self) -> tuple[float, float]:
        """A focused camera is allowed much closer than a site view."""
        if self.focus is None:
            return 14.0, 220.0
        placed = self.park.placements[self.focus]
        return max(2.2, placed.radius_m * 0.55), 90.0

    def pick(self, mouse) -> int | None:
        """Which pad is under the mouse, if any.

        Tested against a sphere sitting over each pad rather than against the
        drawn mesh: a dome is mostly holes, and a user clicking on a strut
        gap means the dome, not the grass behind it.
        """
        width, height = self.pygame.display.get_window_size()
        eye, target = self.camera()
        forward = target - eye
        forward /= np.linalg.norm(forward) or 1.0
        right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
        right /= np.linalg.norm(right) or 1.0
        up = np.cross(right, forward)

        scale = math.tan(math.radians(FOV_DEG * 0.5))
        aspect = width / max(1, height)
        nx = (2.0 * mouse[0] / max(1, width) - 1.0) * scale * aspect
        ny = (1.0 - 2.0 * mouse[1] / max(1, height)) * scale
        ray = forward + right * nx + up * ny
        ray /= np.linalg.norm(ray) or 1.0

        best: tuple[float, int] | None = None
        for index, placed in enumerate(self.park.placements):
            span = placed.radius_m
            lift = placed.dome_base_z
            if placed.occupied:
                if placed.is_seed:
                    shape = placed.seed_placement().shape
                    apex = (seed_world.apex_m(shape)
                            + seed_world.base_lift_m(shape))
                else:
                    apex = placed.radius_m * 0.8
                span = max(span, apex * 0.62)
                lift += apex * 0.40
            centre = np.array([placed.origin[0], placed.origin[1], lift])
            offset = eye - centre
            b = float(np.dot(offset, ray))
            c = float(np.dot(offset, offset)) - span * span
            disc = b * b - c
            if disc < 0.0:
                continue
            distance = -b - math.sqrt(disc)
            if distance < 0.0:
                distance = -b + math.sqrt(disc)
            if distance < 0.0:
                continue
            if best is None or distance < best[0]:
                best = (distance, index)
        return None if best is None else best[1]

    # -- drawing --------------------------------------------------------
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
        # spends all the depth precision on space nothing occupies. A focused
        # camera comes close enough that the near plane has to follow it in.
        near = 0.45 if self.focus is not None else 0.8
        projection = perspective(FOV_DEG, width / max(1, height), near, 400.0)
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
            (f"PAD {self.selected + 1} of {len(self.park.placements)}"
             + ("   [LOCKED]" if self.focus == self.selected else ""),
             ACCENT, self.bold),
            (f"{pad.diameter_ft:.0f} ft, {pad.deck}"
             + (", rotating" if pad.rotating else "")
             + (", utility column" if pad.utility_column else ""), INK,
             self.font),
        ]
        if placed.is_seed:
            spec = seed_model.fitout(placed.seed)
            rows.append((f"{spec.label} -- {seed_model.SHAPE_NOTE[spec.shape]}",
                         MONEY, self.font))
            rows.append(("shell " + ("lifted clear" if placed.shell_open
                                     else ("on" if placed.show_shell
                                           else "off"))
                         + f"   seam {placed.seam}"
                         + f"   {spec.polyps} panel(s)", DIM,
                         self.small))
        else:
            rows.append((f"takes {len(fits)} of {len(catalogue)} dome designs",
                         DIM, self.small))
            rows.append((placed.dome if placed.occupied else "vacant",
                         MONEY if placed.occupied else WARN, self.font))
        rows.append(("", DIM, self.small))
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
            ("click pad   F lock   O overview   [ ] step", DIM, self.small),
            ("D deck  R rotate  U column  V lease  N seed", DIM, self.small),
            ("K shell  L lift  J seam  C crane  B bill  sun", DIM,
             self.small),
            ("H panel   S shot   Esc quit", DIM, self.small),
        ])
        return rows

    def bill_lines(self) -> list[tuple[str, tuple[int, int, int], object]]:
        """What the selected seed dome costs to build and sells for.

        The same :mod:`seed_model` quote the wedge tool's calculator shows and
        the same one ``seed_model.py`` prints at the command line. One dome,
        one bill, wherever it is looked at."""
        placed = self.current
        if not placed.is_seed:
            return []
        result = seed_model.quote(placed.seed)
        spec = result.fitout
        rows: list[tuple[str, tuple[int, int, int], object]] = [
            (f"{spec.label.upper()}", ACCENT, self.bold),
            (f"{result.geometry.diameter_ft:.1f} ft across, "
             f"{result.geometry.floor_decagon_sqft:.0f} sq ft", DIM,
             self.font),
            ("", DIM, self.small),
        ]
        for label, amount in result.rows():
            rows.append((f"{label[:24]:<24} ${amount:>9,.0f}", DIM,
                         self.small))
        rows.extend([
            ("", DIM, self.small),
            (f"{'cost to build':<24} ${result.cost_to_build:>9,.0f}", INK,
             self.small),
            (f"{'list price':<24} ${result.price:>9,.0f}", MONEY, self.small),
            (f"{'per sq ft':<24} ${result.price_per_sqft:>9,.2f}", MONEY,
             self.small),
            ("", DIM, self.small),
            (f"{'cheapest pad for it':<24} "
             f"${seed_model.seed_pad_cost():>9,.0f}", DIM, self.small),
        ])
        if spec.modules:
            rows.append(("", DIM, self.small))
            rows.append(("MODULES", ACCENT, self.font))
            for key in spec.modules:
                module = seed_model.MODULE[key]
                count = spec.count_of(key)
                suffix = f" x{count}" if count > 1 else ""
                rows.append((f"  {module.label[:22]}{suffix}", DIM,
                             self.small))
        return rows

    def _render_block(self, rows, width_px: int):
        pygame = self.pygame
        pad_x, pad_y, line_h = 22, 20, 24
        box_h = pad_y * 2 + sum(line_h if text else 10 for text, _c, _f in rows)
        panel = pygame.Surface((width_px, box_h), pygame.SRCALPHA)
        panel.fill(PANEL_BG)
        pygame.draw.rect(panel, (60, 92, 120), panel.get_rect(), 1)
        y = pad_y
        for text, colour, font in rows:
            if not text:
                y += 10
                continue
            panel.blit(font.render(text, True, colour), (pad_x, y))
            y += line_h
        return panel

    def draw_panel(self, width: int, height: int) -> None:
        pygame = self.pygame
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.blit(self._render_block(self.panel_lines(), 430), (20, 20))
        if self.show_bill:
            bill = self.bill_lines()
            if bill:
                block = self._render_block(bill, 330)
                surface.blit(block, (width - 350, 20))

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
    def select(self, index: int) -> None:
        self.selected = index % len(self.park.placements)
        if self.focus is not None:
            self.focus_on(self.selected)

    def handle_events(self) -> bool:
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return False
                if event.key == pg.K_LEFTBRACKET:
                    self.select(self.selected - 1)
                elif event.key == pg.K_RIGHTBRACKET:
                    self.select(self.selected + 1)
                elif event.key in (pg.K_f, pg.K_RETURN, pg.K_KP_ENTER):
                    if self.focus == self.selected:
                        self.overview()
                    else:
                        self.focus_on(self.selected)
                elif event.key in (pg.K_o, pg.K_HOME):
                    self.overview()
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
                elif event.key == pg.K_n:
                    step = -1 if (pg.key.get_mods() & pg.KMOD_SHIFT) else 1
                    self.cycle_seed(step)
                elif event.key == pg.K_k:
                    placed = self.current
                    if placed.is_seed:
                        placed.show_shell = not placed.show_shell
                        placed.shell_open = False
                elif event.key == pg.K_l:
                    placed = self.current
                    if placed.is_seed:
                        placed.shell_open = not placed.shell_open
                        placed.show_shell = True
                        self.swing_crane_to(self.selected)
                elif event.key == pg.K_j:
                    placed = self.current
                    if placed.is_seed:
                        seams = seed_world.SEAMS
                        placed.seam = seams[
                            (seams.index(placed.seam) + 1) % len(seams)]
                elif event.key == pg.K_c:
                    self.swing_crane_to(self.selected)
                elif event.key == pg.K_b:
                    self.show_bill = not self.show_bill
                elif event.key == pg.K_SPACE:
                    self.sun_running = not self.sun_running
                elif event.key == pg.K_h:
                    self.show_panel = not self.show_panel
                elif event.key == pg.K_s:
                    print(f"saved {self.capture()}")
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
                self.drag_start = event.pos
                self.drag_moved = 0
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
                if self.drag_moved <= CLICK_SLOP_PX:
                    self._handle_click(event.pos)
            elif event.type == pg.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.drag_moved += abs(dx) + abs(dy)
                self.yaw += dx * 0.3
                self.pitch = max(6.0, min(80.0, self.pitch - dy * 0.25))
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEWHEEL:
                low, high = self.zoom_limits()
                self.distance_goal = max(low, min(high,
                                                  self.distance_goal - event.y * 3.0))
                if self.focus is None:
                    self.overview_distance = self.distance_goal
        return True

    def _handle_click(self, position) -> None:
        """Select what was clicked; click it again quickly to lock on."""
        index = self.pick(position)
        now = self.pygame.time.get_ticks()
        if index is None:
            self.last_click_index = None
            return
        double = (self.last_click_index == index
                  and now - self.last_click_ms < DOUBLE_CLICK_MS)
        self.last_click_ms = now
        self.last_click_index = index
        self.selected = index
        if double:
            self.focus_on(index)
        elif self.focus is not None:
            self.focus_on(index)

    def update(self, dt: float) -> None:
        # Ease the camera toward whatever it is meant to be looking at. A jump
        # cut between two pads loses the viewer; a glide keeps the site in one
        # piece. Frame-rate independent, so a slow frame does not overshoot.
        if dt > 0.0:
            blend = 1.0 - math.exp(-dt * 7.0)
            self.centre += (self.centre_goal - self.centre) * blend
            self.distance += (self.distance_goal - self.distance) * blend

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
    # name, yaw, pitch, distance, pad, locked on that pad, shell state
    ("site", 52.0, 26.0, 78.0, 0, False, None),
    ("row", 90.0, 12.0, 58.0, 1, False, None),
    ("pad", 34.0, 18.0, 26.0, 1, False, None),
    ("overhead", 68.0, 62.0, 66.0, 3, False, None),
    ("locked", 40.0, 16.0, 0.0, 1, True, "on"),
    # The two views the whole design has to survive: the shell off, so the
    # frame, the column and the stove are visible, and the shell held clear,
    # which is what "removable" means when a crane is holding it.
    ("naked", 26.0, 14.0, 0.0, 1, True, "off"),
    ("lifted", 26.0, 18.0, 0.0, 1, True, "open"),
)


def render_shots(shot_dir: Path, size=(1600, 900),
                 park: park_world.Park | None = None) -> list[Path]:
    """One PNG per named view, with no window."""
    app = DomeParkApp(size=size, hidden=True, park=park)
    app.sun_running = False
    written: list[Path] = []
    try:
        for name, yaw, pitch, distance, selected, locked, shell in VIEWS:
            app.yaw, app.pitch = yaw, pitch
            app.selected = min(selected, len(app.park.placements) - 1)
            placed = app.current
            if shell is not None and placed.is_seed:
                placed.show_shell = shell in ("on", "open")
                placed.shell_open = shell == "open"
                if shell == "open":
                    app.swing_crane_to(app.selected)
            if locked:
                app.focus_on(app.selected, instant=True)
            else:
                app.overview(instant=True)
                app.distance = app.distance_goal = distance
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

    # The seed side, end to end: the geometry against the published
    # calculator, everything the park draws of a seed dome, and one quote.
    seed_world.validate_seed_world()
    seeds = park_world.seed_park()
    assert all(p.is_seed for p in seeds.placements)
    quoted = seed_model.quote(seeds.placements[0].seed)
    assert quoted.price > quoted.cost_to_build

    print(f"dome park selftest ok: {figures['pads']} pads, "
          f"{figures['occupied']} leased, "
          f"${figures['build_cost']:,.0f} to build, "
          f"{figures['payback_years']:.1f} year payback; "
          f"{len(seeds.placements)} seed pads, "
          f"{quoted.fitout.label} at ${quoted.price:,.0f}")
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

    seed_model.load_overrides()
    raw_pads = cfg.get("pads")
    deck = str(cfg.get("deck") or "gravel")
    if deck not in park_model.DECKS:
        deck = "gravel"
    rotating = bool(cfg.get("rotating", True))
    mode = str(cfg.get("mode") or "domes").lower()

    if mode == "seeds":
        # A seed park with no pad count asked for shows every seed there is,
        # because the point of the layout is that they are all the same dome.
        count = int(raw_pads) if raw_pads else None
        if count is not None and count >= len(seed_model.FITOUT_ORDER):
            count = None
        park = park_world.seed_park(
            pad_count=count, deck=deck, rotating=rotating,
            highway=bool(cfg.get("highway", True)),
            crane=bool(cfg.get("crane", True)))
    else:
        park = park_world.default_park(pad_count=int(raw_pads or 6),
                                       rotating=rotating, deck=deck)

    if action == "shots":
        shot_dir = Path(cfg.get("shot_dir") or (ROOT / "shots" / "dome_park"))
        written = render_shots(shot_dir, size=size, park=park)
        for path in written:
            print(f"saved {path}")
        return 0

    app = DomeParkApp(size=size, hidden=False, park=park)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
