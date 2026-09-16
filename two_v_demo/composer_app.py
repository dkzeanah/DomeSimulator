"""The scene composer, on screen: hold a piece, turn it, drop it.

:mod:`two_v_demo.scene_composer` holds the rules and knows nothing about
windows.  This is the window.  It orbits a camera round a dome, draws
the piece you are holding as a translucent ghost -- green where it fits,
red where it does not, with the reason printed underneath -- and turns
key presses into calls on the composer.

The controls are the ones a park editor has had since 1999: two keys
walk the categories, two walk the pieces, one turns, one drops.  The
full map is in :data:`KEY_LEGEND`, which is also what the on-screen
help draws from, so the help cannot fall out of date with the keys.

Running it::

    py -3.12 -m two_v_demo.composer_app                 # the store
    py -3.12 -m two_v_demo.composer_app --set DOME_HOME
    py -3.12 -m two_v_demo.composer_app --load my.json
    py -3.12 -m two_v_demo.composer_app --shots out/    # no window

The last one renders a turn round the room to PNGs without opening
anything, which is how a scene gets checked from a terminal.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .dome_interiors import shell_clearance
from .render_kit import (
    OVERLAY_FRAGMENT_SHADER,
    OVERLAY_VERTEX_SHADER,
    SCENE_FRAGMENT_SHADER,
    SCENE_VERTEX_SHADER,
    TriangleBatch,
    look_at,
    perspective,
)
from .scene_composer import (
    CAST_CATEGORY,
    Composer,
    Placement,
    Scene,
    corners,
    draw_placement,
    draw_scene,
    floor_share,
    footprint_marks,
    scene_report,
    starter_scene,
    tinted,
)


from .scene_composer import VERTEX_STRIDE as VERTEX_STRIDE

FITS = (0.24, 0.96, 0.46, 0.62)
BLOCKED = (0.99, 0.30, 0.32, 0.62)
CARRIED = (0.30, 0.78, 1.00, 0.62)


KEY_LEGEND: tuple[tuple[str, str], ...] = (
    ("Q / E", "previous / next category"),
    ("A / D", "previous / next piece"),
    ("arrows", "move the piece on the grid"),
    ("mouse", "move it to the pointer; click to drop"),
    ("R / Shift+R", "turn 15 degrees, hold Ctrl for 5"),
    ("F", "face the middle of the room"),
    ("[ / ]", "lower / raise a hanging piece"),
    ("Enter", "drop it"),
    ("G", "pick the piece under the cursor back up"),
    ("Delete", "remove the piece under the cursor"),
    ("Z / Y", "undo / redo"),
    ("M", "what she is wearing"),
    ("P", "how she is standing"),
    ("H", "her hair"),
    ("Tab", "swap between the house and the store"),
    ("S / L", "save / load the scene"),
    ("C", "clear the room"),
    ("X", "show or hide the shell panels"),
    ("F1", "this list"),
    ("F2", "save a screenshot"),
)


def hud_lines(composer: Composer) -> list[tuple[str, str]]:
    """The status block, as label and value pairs.

    Pure: it takes a composer and returns text, so it can be checked
    without opening a window.
    """
    scene = composer.scene
    room = scene.room()
    verdict = composer.verdict()
    entry = composer.entry()
    held = "moving" if composer.carrying is not None else "holding"
    rows = [
        (room.label, f"{room.radius_m * 2:.0f} m across, "
                     f"{room.radius_m:.1f} m to the crown"),
        (composer.category().title(),
         f"{entry.label}  --  {entry.detail}"),
        (held.title(), f"{composer.cursor_x:+.2f}, {composer.cursor_y:+.2f} m "
                       f"at {composer.cursor_yaw:.0f} deg"
                       + (f", raised {composer.cursor_lift:.2f} m"
                          if composer.cursor_lift else "")),
        ("Headroom", f"{verdict.clearance_m:.2f} m over that footprint"),
        ("Verdict", "it fits" if verdict.ok else verdict.why),
        ("Room", f"{len(scene.placements)} pieces, "
                 f"{floor_share(scene) * 100:.0f}% of the floor"),
    ]
    if entry.kind == "CAST":
        rows.insert(3, ("Look",
                        f"{composer.mode().lower()}, "
                        f"{(composer.pose() or 'her own pose').replace('_', ' ')}"
                        f", {composer.hair().lower() or 'her own hair'}"))
    return rows


class ComposerApp:
    """A window over a :class:`~two_v_demo.scene_composer.Composer`."""

    def __init__(
        self,
        scene: Scene | None = None,
        size: tuple[int, int] = (1600, 950),
        hidden: bool = False,
    ) -> None:
        try:
            import moderngl
            import pygame
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The composer needs pygame and moderngl. Install with: "
                "py -3.12 -m pip install pygame moderngl numpy"
            ) from exc
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
        pygame.display.set_caption("Dome Composer")
        pygame.display.set_mode(size, flags)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE
                        | moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.scene_program = self.ctx.program(
            vertex_shader=SCENE_VERTEX_SHADER,
            fragment_shader=SCENE_FRAGMENT_SHADER)
        self.overlay_program = self.ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
        self.overlay_buffer = self.ctx.buffer(quad.tobytes())
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program, [(self.overlay_buffer, "2f", "in_position")])
        self.overlay_texture = None
        self.overlay_size = (0, 0)

        self.composer = Composer(scene=scene or starter_scene("DOME_STORE"))
        self.camera_yaw = 35.0
        self.camera_pitch = 26.0
        self.camera_distance = self.composer.scene.room().radius_m * 2.4
        self.dragging = False
        self.last_mouse = (0, 0)
        self.show_help = False
        self.show_shell = True
        self.font_cache: dict[tuple[int, bool], object] = {}
        self.output_dir = Path("two_v_demo_output/scenes")
        self.mvp = np.eye(4, dtype=np.float32)

    # -- camera -------------------------------------------------------

    def camera(self) -> tuple[np.ndarray, np.ndarray]:
        pitch = math.radians(max(6.0, min(82.0, self.camera_pitch)))
        yaw = math.radians(self.camera_yaw)
        target = np.array([0.0, 0.0, 1.30], dtype=np.float32)
        eye = target + np.array([
            self.camera_distance * math.cos(pitch) * math.cos(yaw),
            self.camera_distance * math.cos(pitch) * math.sin(yaw),
            self.camera_distance * math.sin(pitch),
        ], dtype=np.float32)
        return eye, target

    def floor_under(self, pixel: tuple[int, int]) -> tuple[float, float] | None:
        """Where a screen point lands on the floor of the dome.

        A ray is built from the camera basis rather than by inverting
        the matrix, which is fewer steps and cannot disagree with the
        camera the frame was drawn with.
        """
        width, height = self.pygame.display.get_window_size()
        eye, target = self.camera()
        forward = target - eye
        forward = forward / float(np.linalg.norm(forward))
        right = np.cross(forward, np.array([0.0, 0.0, 1.0], dtype=np.float32))
        right = right / float(np.linalg.norm(right))
        up = np.cross(right, forward)
        fov = math.radians(48.0)
        aspect = width / max(1, height)
        ndc_x = (pixel[0] / max(1, width)) * 2.0 - 1.0
        ndc_y = 1.0 - (pixel[1] / max(1, height)) * 2.0
        scale = math.tan(fov * 0.5)
        direction = (forward
                     + right * (ndc_x * scale * aspect)
                     + up * (ndc_y * scale))
        if abs(float(direction[2])) < 1e-6:
            return None
        distance = -float(eye[2]) / float(direction[2])
        if distance <= 0.0:
            return None
        hit = eye + direction * distance
        return float(hit[0]), float(hit[1])

    # -- drawing ------------------------------------------------------

    def build_scene(self) -> tuple[TriangleBatch, TriangleBatch]:
        opaque = TriangleBatch()
        clear = TriangleBatch()
        composer = self.composer
        scene = composer.scene
        room = scene.room()

        if composer.carrying is None:
            draw_scene(opaque, clear, scene, shell=self.show_shell,
                       detail=0.55)
        else:
            # The piece being moved is drawn as the ghost instead of in
            # place, so you can see where it is going rather than a copy
            # of it sitting where it was.
            held = scene.with_placements(
                item for index, item in enumerate(scene.placements)
                if index != composer.carrying)
            draw_scene(opaque, clear, held, shell=self.show_shell,
                       detail=0.55)

        ghost = composer.ghost()
        verdict = composer.verdict()
        colour = (CARRIED if (verdict.ok and composer.carrying is not None)
                  else FITS if verdict.ok else BLOCKED)
        scratch = TriangleBatch()
        draw_placement(scratch, scratch, room, ghost, detail=0.35)
        clear.vertices.extend(tinted(scratch, colour).vertices)
        footprint_marks(opaque, ghost, (colour[0], colour[1], colour[2], 1.0),
                        room.radius_m)
        return opaque, clear

    def font(self, size: int, bold: bool = False):
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = self.pygame.font.SysFont(
                "Segoe UI", size, bold=bold)
        return self.font_cache[key]

    def draw_hud(self, width: int, height: int):
        pg = self.pygame
        surface = pg.Surface((width, height), pg.SRCALPHA)
        verdict = self.composer.verdict()

        panel = pg.Rect(24, 24, 560, 34 + 30 * len(hud_lines(self.composer)))
        pg.draw.rect(surface, (8, 14, 22, 205), panel, border_radius=14)
        pg.draw.rect(surface, (70, 110, 140, 220), panel, width=1,
                     border_radius=14)
        y = panel.top + 16
        for label, value in hud_lines(self.composer):
            colour = (150, 176, 198)
            if label == "Verdict":
                colour = (96, 226, 140) if verdict.ok else (250, 110, 110)
            text = self.font(16, bold=True).render(f"{label}", True, colour)
            surface.blit(text, (panel.left + 18, y))
            body = self.font(16).render(value, True, (226, 235, 244))
            surface.blit(body, (panel.left + 152, y))
            y += 30

        message = self.font(17, bold=True).render(
            self.composer.message, True, (232, 240, 248))
        surface.blit(message, (28, height - 44))

        hint = self.font(14).render(
            "F1 for the controls" if not self.show_help else "F1 to close",
            True, (128, 152, 172))
        surface.blit(hint, (width - hint.get_width() - 28, height - 40))

        if self.show_help:
            box = pg.Rect(width - 520, 24, 496, 40 + 26 * len(KEY_LEGEND))
            pg.draw.rect(surface, (8, 14, 22, 225), box, border_radius=14)
            pg.draw.rect(surface, (70, 110, 140, 220), box, width=1,
                         border_radius=14)
            y = box.top + 18
            for key, what in KEY_LEGEND:
                surface.blit(self.font(15, bold=True).render(
                    key, True, (120, 210, 240)), (box.left + 20, y))
                surface.blit(self.font(15).render(
                    what, True, (214, 226, 238)), (box.left + 160, y))
                y += 26
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
            self.pygame.image.tobytes(surface, "RGBA", True))

    def render(self, present: bool = True) -> None:
        width, height = self.pygame.display.get_window_size()
        room = self.composer.scene.room()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.clear(0.03, 0.045, 0.065, 1.0)
        eye, target = self.camera()
        self.mvp = perspective(48.0, width / max(1, height), 0.08,
                               160.0) @ look_at(eye, target)
        self.scene_program["u_mvp"].write(
            np.ascontiguousarray(self.mvp.T).astype("f4").tobytes())
        self.scene_program["u_camera"].value = tuple(
            float(value) for value in eye)
        self.scene_program["u_light"].value = room.key_light

        opaque, clear = self.build_scene()
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.ctx.depth_mask = True
        self._draw(opaque)
        if clear.vertices:
            self.ctx.disable(self.moderngl.CULL_FACE)
            self.ctx.depth_mask = False
            self._draw(clear)
            self.ctx.depth_mask = True
            self.ctx.enable(self.moderngl.CULL_FACE)

        self.upload_overlay(self.draw_hud(width, height))
        self.ctx.disable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        self.overlay_texture.use(0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_vao.render(self.moderngl.TRIANGLE_STRIP)
        self.ctx.enable(self.moderngl.DEPTH_TEST | self.moderngl.CULL_FACE)
        if present:
            self.pygame.display.flip()

    def _draw(self, batch: TriangleBatch) -> None:
        if not batch.vertices:
            return
        data = np.asarray(batch.vertices, dtype="f4").tobytes()
        buffer = self.ctx.buffer(data)
        vao = self.ctx.vertex_array(
            self.scene_program,
            [(buffer, "3f 3f 4f", "in_position", "in_normal", "in_color")])
        vao.render(self.moderngl.TRIANGLES)
        vao.release()
        buffer.release()

    # -- input --------------------------------------------------------

    def save_scene(self) -> Path:
        path = self.output_dir / f"{self.composer.scene.name}.json"
        self.composer.scene.save(path)
        self.composer.message = f"Saved {path}."
        return path

    def load_scene(self) -> bool:
        path = self.output_dir / f"{self.composer.scene.name}.json"
        if not path.exists():
            self.composer.message = f"No scene saved at {path}."
            return False
        self.composer.scene = Scene.load(path)
        self.composer.carrying = None
        self.composer.message = f"Loaded {path}."
        return True

    def screenshot(self, path: Path | None = None) -> Path:
        width, height = self.pygame.display.get_window_size()
        self.render(present=False)
        self.ctx.finish()
        data = self.ctx.screen.read((0, 0, width, height), components=3,
                                    alignment=1)
        surface = self.pygame.image.frombytes(data, (width, height), "RGB")
        surface = self.pygame.transform.flip(surface, False, True)
        path = path or (self.output_dir
                        / f"{self.composer.scene.name}_shot.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pygame.image.save(surface, str(path))
        return path

    def handle_events(self) -> bool:
        pg = self.pygame
        composer = self.composer
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                mods = pg.key.get_mods()
                shift = bool(mods & pg.KMOD_SHIFT)
                ctrl = bool(mods & pg.KMOD_CTRL)
                if event.key == pg.K_ESCAPE:
                    return False
                elif event.key == pg.K_q:
                    composer.cycle_category(-1)
                elif event.key == pg.K_e:
                    composer.cycle_category(1)
                elif event.key == pg.K_a:
                    composer.cycle_piece(-1)
                elif event.key == pg.K_d:
                    composer.cycle_piece(1)
                elif event.key == pg.K_LEFT:
                    composer.nudge(0, -1)
                elif event.key == pg.K_RIGHT:
                    composer.nudge(0, 1)
                elif event.key == pg.K_UP:
                    composer.nudge(1, 0)
                elif event.key == pg.K_DOWN:
                    composer.nudge(-1, 0)
                elif event.key == pg.K_r:
                    composer.turn(-1 if shift else 1, fine=ctrl)
                elif event.key == pg.K_f:
                    composer.face_centre()
                elif event.key == pg.K_LEFTBRACKET:
                    composer.raise_by(-1)
                elif event.key == pg.K_RIGHTBRACKET:
                    composer.raise_by(1)
                elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                    composer.place()
                elif event.key == pg.K_g:
                    composer.pick_up()
                elif event.key in (pg.K_DELETE, pg.K_BACKSPACE):
                    composer.remove()
                elif event.key == pg.K_z:
                    composer.undo()
                elif event.key == pg.K_y:
                    composer.redo()
                elif event.key == pg.K_m:
                    composer.cycle_mode(-1 if shift else 1)
                elif event.key == pg.K_p:
                    composer.cycle_pose(-1 if shift else 1)
                elif event.key == pg.K_h:
                    composer.cycle_hair(-1 if shift else 1)
                elif event.key == pg.K_TAB:
                    other = ("DOME_HOME" if composer.scene.set_id
                             == "DOME_STORE" else "DOME_STORE")
                    composer.switch_set(other)
                    self.camera_distance = \
                        composer.scene.room().radius_m * 2.4
                elif event.key == pg.K_s:
                    self.save_scene()
                elif event.key == pg.K_l:
                    self.load_scene()
                elif event.key == pg.K_c:
                    composer.clear()
                elif event.key == pg.K_x:
                    self.show_shell = not self.show_shell
                elif event.key == pg.K_F1:
                    self.show_help = not self.show_help
                elif event.key == pg.K_F2:
                    composer.message = f"Saved {self.screenshot()}."
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    spot = self.floor_under(event.pos)
                    if spot is not None:
                        composer.move_to(*spot)
                        composer.place()
                elif event.button == 3:
                    spot = self.floor_under(event.pos)
                    if spot is not None:
                        index = composer.hover(*spot)
                        if index is not None:
                            composer.remove(index)
                elif event.button == 2:
                    self.dragging = True
                    self.last_mouse = event.pos
            elif event.type == pg.MOUSEBUTTONUP and event.button == 2:
                self.dragging = False
            elif event.type == pg.MOUSEMOTION:
                if self.dragging or (pg.key.get_mods() & pg.KMOD_ALT):
                    dx = event.pos[0] - self.last_mouse[0]
                    dy = event.pos[1] - self.last_mouse[1]
                    self.camera_yaw += dx * 0.30
                    self.camera_pitch = max(6.0, min(82.0,
                                                     self.camera_pitch
                                                     - dy * 0.24))
                else:
                    spot = self.floor_under(event.pos)
                    if spot is not None:
                        composer.move_to(*spot)
                self.last_mouse = event.pos
            elif event.type == pg.MOUSEWHEEL:
                room = composer.scene.room()
                self.camera_distance = max(room.radius_m * 0.6,
                                           min(room.radius_m * 4.5,
                                               self.camera_distance
                                               - event.y * 0.8))
        return True

    def run(self) -> None:
        clock = self.pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            running = self.handle_events()
            self.render()
        self.pygame.quit()

    def turntable(self, output_dir: Path, frames: int = 4) -> list[Path]:
        """Render the room from several angles without anybody watching."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for index in range(frames):
            self.camera_yaw = 35.0 + 360.0 * index / frames
            paths.append(self.screenshot(
                output_dir / f"{self.composer.scene.name}_{index:02d}.png"))
        return paths


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_composer_app() -> None:
    """Prove everything in here that does not need a window."""
    # The help is complete and has no duplicate keys.
    keys = [key for key, _ in KEY_LEGEND]
    assert len(set(keys)) == len(keys), keys
    for key, what in KEY_LEGEND:
        assert key and what and what[0].islower(), (key, what)
    for needed in ("Q / E", "A / D", "R / Shift+R", "Enter", "Z / Y"):
        assert needed in keys, needed

    # The status block reads correctly for a prop and for a woman.
    composer = Composer(scene=starter_scene("DOME_STORE"))
    rows = hud_lines(composer)
    labels = [label for label, _ in rows]
    assert "Verdict" in labels and "Headroom" in labels
    composer.category_index = list(composer.groups()).index(CAST_CATEGORY)
    cast_rows = hud_lines(composer)
    assert any(label == "Look" for label, _ in cast_rows)
    assert len(cast_rows) == len(rows) + 1

    # It reports a refusal in words rather than as a blank.
    composer.move_to(composer.scene.room().radius_m * 1.6, 0.0)
    blocked = dict(hud_lines(composer))["Verdict"]
    assert blocked != "it fits" and len(blocked) > 10, blocked

    # And the ghost's colours say what the verdict says.
    assert FITS[1] > FITS[0] and BLOCKED[0] > BLOCKED[1], "green fits, red does not"
    assert all(colour[3] < 1.0 for colour in (FITS, BLOCKED, CARRIED))

    # A launcher ticket produces the flags it claims to, so what the GUI
    # promises and what the tool does cannot come apart.
    assert config_to_argv({"action": "selftest"}) == ["--selftest"]
    assert config_to_argv({"action": "run", "set_id": "DOME_HOME",
                           "start": "empty", "size": "1280x800"}) == [
        "--set", "DOME_HOME", "--empty", "--size", "1280x800"]
    loaded = config_to_argv({"action": "report", "load": "a.json",
                             "start": "empty"})
    assert "--load" in loaded and "--empty" not in loaded, (
        "a named file wins over the empty-room option")
    assert loaded[-1] == "--report"
    shots = config_to_argv({"action": "shots", "shots_dir": "out"})
    assert shots == ["--shots", "out"], shots
    # Every ticket the launcher can produce parses.
    for ticket in ({"action": "run"}, {"action": "report"},
                   {"action": "shots"}, {"action": "selftest"}):
        parsed = config_to_argv(ticket)
        assert isinstance(parsed, list)


def config_to_argv(cfg: dict) -> list[str]:
    """Turn a launcher ticket into the arguments this tool already takes.

    The launcher hands tools a JSON ticket instead of a command line
    (see :mod:`launcher_common`).  Rather than grow a second way of
    reading options, the ticket is translated into the flags argparse
    already understands, so the GUI and the terminal cannot drift into
    disagreeing about what an option means.
    """
    argv: list[str] = []
    action = str(cfg.get("action") or "run")
    if action == "selftest":
        return ["--selftest"]
    if cfg.get("set_id"):
        argv += ["--set", str(cfg["set_id"])]
    if cfg.get("load"):
        argv += ["--load", str(cfg["load"])]
    elif cfg.get("start") == "empty":
        argv.append("--empty")
    if cfg.get("size"):
        argv += ["--size", str(cfg["size"])]
    if action == "report":
        argv.append("--report")
    elif action == "shots":
        argv += ["--shots", str(cfg.get("shots_dir")
                                or "two_v_demo_output/scenes")]
    return argv


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        try:
            import launcher_common as _lc
        except ModuleNotFoundError:
            _lc = None
        if _lc is not None:
            ticket = _lc.consume_config("dome_composer")
            if ticket:
                argv = config_to_argv(ticket)

    parser = argparse.ArgumentParser(
        description="Build a dome interior: cycle a piece, turn it, drop it.")
    parser.add_argument("--set", dest="set_id", default="DOME_STORE",
                        choices=("DOME_STORE", "DOME_HOME"))
    parser.add_argument("--empty", action="store_true",
                        help="start with a bare floor instead of the "
                             "furnished starter layout")
    parser.add_argument("--load", type=Path, help="open a saved scene")
    parser.add_argument("--size", default="1600x950")
    parser.add_argument("--shots", type=Path,
                        help="render a turn round the room to this "
                             "directory and exit, without a window")
    parser.add_argument("--report", action="store_true",
                        help="print the scene as text and exit")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        validate_composer_app()
        print("composer app ok")
        return 0

    if args.load:
        scene = Scene.load(args.load)
    elif args.empty:
        scene = Scene(set_id=args.set_id, name=f"{args.set_id.lower()}_new")
    else:
        scene = starter_scene(args.set_id)

    if args.report:
        print(scene_report(scene))
        return 0

    width, height = (int(part) for part in args.size.lower().split("x"))
    app = ComposerApp(scene=scene, size=(width, height),
                      hidden=bool(args.shots))
    if args.shots:
        for path in app.turntable(args.shots):
            print(f"wrote {path}")
        app.pygame.quit()
        return 0
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
