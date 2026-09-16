#!/usr/bin/env python3
from __future__ import annotations

"""
JIG FOCUS WORLD

A dedicated wrapper around the full raw-wedge geodesic dome single-file engine.
This launches directly into a jig-centric view so the fabrication fixture,
member orientation, sacrificial butt hang-off, and cut guides are easier to study.

Run:
    python jig_focus_world.py
"""

from pathlib import Path
import math
import sys

import geodesic_raw_wedge_dome_single as base


class JigFocusWorldApp(base.DomeWorldApp):
    """A dedicated jig-only viewing mode using the full underlying geometry engine."""

    def __init__(self) -> None:
        super().__init__()
        self._apply_jig_focus_defaults()

    def _apply_jig_focus_defaults(self) -> None:
        # Start in the side-panel / jig workflow, not in assembled-dome study mode.
        self.config.wedge_orientation = "point_dome_in"
        self.config.seam_join_mode = "raw_trapezoid"
        self.config.spacer_mode = "rigid"
        self.config.panel_explode_in = 0.0
        self.jig_panel = self._find_default_side_panel_index()
        self.solo_panel = True

        # Make the scene about the fixture. The user can still toggle items back on.
        self.show_wood = False
        self.show_spacer = False
        self.show_nodes = False
        self.show_ideal = False
        self.show_skin = False
        self.show_pinwheel_joints = False
        self.show_ground = True
        self.show_jig = True
        self.zoom_steps = 0

        self._upload_jig()
        self.focus_view_iso()
        self._refresh_hud(force=True)
        self.print_controls()

    def _combined_bounds(self) -> tuple[base.np.ndarray, base.np.ndarray]:
        meshes: list[base.MeshData] = []
        for name in ("jig_fixture", "jig_wood", "jig_hangoff"):
            mesh = self.jig_cpu.get(name)
            if isinstance(mesh, base.MeshData) and mesh.vertices.size:
                meshes.append(mesh)
        if not meshes:
            center = base.np.array([0.0, 0.0, 0.0], dtype=base.np.float64)
            span = base.np.array([100.0, 100.0, 100.0], dtype=base.np.float64)
            return center, span
        pts = base.np.vstack([m.vertices[:, 0:3] for m in meshes])
        pmin = pts.min(axis=0)
        pmax = pts.max(axis=0)
        center = (pmin + pmax) * 0.5
        span = base.np.maximum(pmax - pmin, base.np.array([1.0, 1.0, 1.0]))
        return center, span

    def _set_camera_target(self, eye: base.np.ndarray, target: base.np.ndarray) -> None:
        vec = target - eye
        dist_xy = math.hypot(float(vec[0]), float(vec[1]))
        yaw = math.degrees(math.atan2(float(vec[1]), float(vec[0])))
        pitch = math.degrees(math.atan2(float(vec[2]), max(1e-9, dist_xy)))
        self.camera.position = eye.astype(base.np.float64)
        self.camera.yaw_deg = yaw
        self.camera.pitch_deg = pitch
        self.camera.fly_mode = True
        self._refresh_hud(force=True)

    def focus_view_iso(self) -> None:
        center, span = self._combined_bounds()
        radius = float(max(span[0], span[1], span[2]))
        eye = center + base.np.array([radius * 1.15, -radius * 1.55, radius * 0.95])
        self._set_camera_target(eye, center)

    def focus_view_front(self) -> None:
        center, span = self._combined_bounds()
        dist = float(max(span[0], span[1], span[2]) * 1.75)
        eye = center + base.np.array([0.0, -dist, span[2] * 0.25])
        self._set_camera_target(eye, center)

    def focus_view_side(self) -> None:
        center, span = self._combined_bounds()
        dist = float(max(span[0], span[1], span[2]) * 1.75)
        eye = center + base.np.array([dist, 0.0, span[2] * 0.25])
        self._set_camera_target(eye, center)

    def focus_view_top(self) -> None:
        center, span = self._combined_bounds()
        dist = float(max(span[0], span[1], span[2]) * 2.0)
        eye = center + base.np.array([0.0, 0.0, dist])
        target = center.copy()
        target[1] += 1.0
        self._set_camera_target(eye, target)

    def focus_view_close_corner(self) -> None:
        center, span = self._combined_bounds()
        radius = float(max(span[0], span[1], span[2]))
        eye = center + base.np.array([radius * 0.35, -radius * 0.55, radius * 0.28])
        self._set_camera_target(eye, center + base.np.array([0.0, 0.0, span[2] * 0.08]))

    def update_caption(self, fps: float) -> None:
        face = self.model.topology.faces[self.jig_panel]
        title = (
            f"Jig Focus World | {fps:5.1f} FPS | panel=P{self.jig_panel + 1:03d}/{face.face_type} | "
            f"wedge={self.config.wedge_orientation.upper()} | join={self.config.seam_join_mode.upper()} | "
            f"hangoff={self.config.jig_butt_hangoff_in:.1f}in | explode={self.config.panel_explode_in:.1f}in"
        )
        base.pygame.display.set_caption(title)

    def print_controls(self) -> None:
        print(
            """
JIG FOCUS WORLD CONTROLS
------------------------
Mouse                  look around (horizontal inverted)
Mouse wheel            zoom at center-screen X
Arrow keys / WASD      move; arrow keys pan at max zoom
Shift                  sprint
PageUp/PageDown        move vertically
Tab                    capture/release mouse
Esc                    release / quit

U / Shift+U            cycle wedge orientations
M                      toggle RAW_TRAPEZOID / SHAVED_FLAT join mode
5 / 6                  decrease / increase sacrificial butt hang-off
Y / Shift+Y            next / previous exact panel jig
Q                      toggle solo panel wood on/off
V                      show / hide triangle wood
T                      show / hide fixture
J                      joint/cut debug lines
I                      ideal guides
G                      ground
F                      walk / fly

F3                     isometric jig view
F4                     front jig view
F5                     side jig view
F6                     top jig view
Space                  close corner inspection view
R                      reset to isometric view
B                      export BOM
E                      export full fabrication package
F12                    screenshot
"""
        )

    def handle_keydown(self, key: int) -> None:
        if key == base.pygame.K_F3:
            self.focus_view_iso()
            return
        if key == base.pygame.K_F4:
            self.focus_view_front()
            return
        if key == base.pygame.K_F5:
            self.focus_view_side()
            return
        if key == base.pygame.K_F6:
            self.focus_view_top()
            return
        if key == base.pygame.K_SPACE:
            self.focus_view_close_corner()
            return
        if key == base.pygame.K_r:
            self.focus_view_iso()
            return

        previous_panel = self.jig_panel
        previous_orientation = self.config.wedge_orientation
        previous_mode = self.config.seam_join_mode
        previous_hangoff = self.config.jig_butt_hangoff_in
        super().handle_keydown(key)
        if (
            self.jig_panel != previous_panel
            or self.config.wedge_orientation != previous_orientation
            or self.config.seam_join_mode != previous_mode
            or self.config.jig_butt_hangoff_in != previous_hangoff
        ):
            self.focus_view_iso()


def main() -> None:
    base.ensure_graphics_dependencies()
    try:
        app = JigFocusWorldApp()
        app.run()
    except Exception as exc:
        if base.pygame is not None:
            base.pygame.quit()
        print(f"Fatal error: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
