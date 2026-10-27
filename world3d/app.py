"""One 3-D world for the foundation, the dome and the zome, their jigs and skins.

    py -3.12 -m world3d                    # the window
    py -3.12 -m world3d --still out.png --view overview
    py -3.12 -m world3d --selftest

It moves and looks exactly like the dome's world and the zome's world it grew from --
the same camera, the same walking, the same letters for the same things -- with the
three structures on one hilltop and editing added on keys those worlds leave free.
The layers panel on the left shows and hides each structure, its skin and its jig,
picks the layer new pieces go into, and locks a layer (press Tab to free the mouse,
then click it; right-click to lock). Then you can take it apart:

THE WORLD (as in the dome and zome worlds)
    Mouse                 look around (Tab frees the mouse to point and click)
    Mouse wheel           zoom on the crosshair
    W A S D / arrows      walk        F  walk / fly        PageUp / PageDown  up and down in fly mode
    Shift                 faster      R  camera back to the start        L  camera to the next jig
    Left click            select the piece under the crosshair: length, section, board feet
    G  ground grid    V  wood on / off    P  skins on / off    T  jigs on / off
THE ALTERNATING DOME (wedges pointing in and out, panel by panel)
    N  build it up one band at a time, from the ground (N again past the top: the whole dome)
    M  the next pattern: ground ring alternating / lower ring of twenty / least angle
    K  camera to it
    B  cut list to the library        F12  screenshot     F1  these controls     F2  readout on / off
    Esc                   free the mouse; Esc again quits
EDITING (new)
    Delete                delete the selected piece
    Ctrl+X                saw the piece under the crosshair, there, square to its length
    Insert                add a strut: then left click its two ends (snaps to ends, then the grid)
    Ctrl+1 / 2 / 3        the new strut's section: wedge, square pair, half trunk
    Alt+arrows            move the selected piece one grid step   (Alt+PageUp / PageDown: up, down)
    Alt+Shift+arrows      move the whole active layer
    Ctrl+D                copy the selected piece one grid step along
    Ctrl+[ / Ctrl+]       grid step: 1, 3, 6, 12, 24 in
    Ctrl+Z  undo          Ctrl+S  save (it opens again next time)
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from . import document as dm
from . import pieces as pc
from . import structures as st

HELP = __doc__.split("Then you can take it apart:")[1]
STEPS = (1.0, 3.0, 6.0, 12.0, 24.0)
SELECT = (1.0, 0.86, 0.30, 1.0)
GRASS = (0.42, 0.55, 0.30, 1.0)
TRANSPARENT = {"dome_skin", "zome_skin"}
BANDED = {"alt_dome", "alt_keys"}

VIEWS = {
    "overview": ((-700.0, -1150.0, 620.0), (260.0, 0.0, 60.0)),
    "foundation": ((0.0, -520.0, 360.0), (0.0, 0.0, 10.0)),
    "dome": ((-260.0, -420.0, 170.0), (0.0, 0.0, 110.0)),
    "zome": ((640.0, -470.0, 150.0), (640.0, 0.0, 90.0)),
    "foundation_jig": ((0.0, -1050.0, 330.0), (0.0, -600.0, 0.0)),
    "dome_jig": ((-560.0, -260.0, 160.0), (-560.0, 0.0, 30.0)),
    "zome_jig": ((640.0, -640.0, 140.0), (640.0, -430.0, 30.0)),
    "alt_dome": ((-190.0, 880.0, 160.0), (0.0, 640.0, 50.0)),     # the lit side
}


def _dome():
    import geodesic_raw_wedge_dome_dihedral as d
    return d


def ftin(inches: float) -> str:
    ft, inch = divmod(abs(inches), 12.0)
    return f"{int(ft)}' {inch:.1f}\"" if ft else f"{inch:.1f}\""


class World:
    """What the window shows: the document, the tool, the selection, the view."""

    def __init__(self, doc: dm.Document | None = None) -> None:
        self.doc = doc or dm.Document()
        self.selected: str | None = None
        self.tool = "select"                 # select | cut | add
        self.pending: np.ndarray | None = None
        self.section = "wedge"
        self.step = 6.0
        self.grid = True
        self.build_band: int | None = None    # the alternating dome up to this band; None = all of it
        self.message = "Click a piece. F1 for every control."

    # -- meshes ----------------------------------------------------------
    def layer_mesh(self, key: str):
        d = _dome()
        acc = d.MeshAccumulator()
        for p in self.doc.layers.get(key, []):
            if key in BANDED and self.build_band is not None and p.meta.get("band", 0) > self.build_band:
                continue
            colour = SELECT if p.pid == self.selected else p.colour
            for poly, _t in p.solid.faces:
                n = np.cross(poly[1] - poly[0], poly[2] - poly[0])
                if np.linalg.norm(n) < 1e-12:
                    continue
                for k in range(1, len(poly) - 1):
                    acc.add_triangle(poly[0], poly[k], poly[k + 1], colour, n)
        return acc.finish()

    def ground(self):
        d = _dome()
        acc, lines = d.MeshAccumulator(), d.LineAccumulator()
        r = 1400.0
        for k in range(96):
            a0, a1 = math.tau * k / 96, math.tau * (k + 1) / 96
            acc.add_triangle(np.array([0, 0, -0.3]), np.array([r * math.cos(a0), r * math.sin(a0), -0.3]),
                             np.array([r * math.cos(a1), r * math.sin(a1), -0.3]), GRASS, np.array([0, 0, 1.0]))
        if self.grid:
            for k in range(-int(r // 12), int(r // 12) + 1):
                c = (0.95, 0.95, 0.85, 1.0) if k % 5 == 0 else (0.70, 0.78, 0.58, 1.0)
                lim = math.sqrt(max(0.0, r * r - (k * 12) ** 2))
                lines.add(np.array([k * 12, -lim, 0.05]), np.array([k * 12, lim, 0.05]), c)
                lines.add(np.array([-lim, k * 12, 0.05]), np.array([lim, k * 12, 0.05]), c)
        if self.pending is not None:
            p = self.pending
            for dx, dy in ((6, 0), (0, 6)):
                lines.add(p - [dx, dy, 0], p + [dx, dy, 0], (1.0, 0.3, 0.3, 1.0))
        return acc.finish(), lines.finish()

    # -- reading out -------------------------------------------------------
    def panel_rows(self) -> list[tuple[str, str]]:
        rows = []
        for key, label, _s, _on in st.LAYERS:
            n = len(self.doc.layers.get(key, []))
            dot = "[x]" if self.doc.visible.get(key) else "[  ]"
            lock = "LOCKED " if self.doc.locked.get(key) else ""
            act = " <- new pieces go here" if key == self.doc.active else ""
            rows.append((key, f"{dot}  {label} ({n})  {lock}{act}"))
        return rows

    # -- the alternating dome ---------------------------------------------
    def next_band(self) -> None:
        bands = sorted(st.alt_plan().bands)
        b = self.build_band
        self.build_band = bands[0] if b is None else (None if b >= bands[-1] else b + 1)
        self.message = self.alt_line()

    def next_pattern(self) -> None:
        pats = st.ALT_PATTERNS
        st.ALT["pattern"] = pats[(pats.index(st.ALT["pattern"]) + 1) % len(pats)]
        self.doc.base.update({k: st.BUILDERS[k]() for k in BANDED})
        self.doc.replay()
        self.message = self.alt_line()

    def alt_line(self) -> str:
        from alternating_build import plan as ap
        p = st.alt_plan()
        c = p.counts()
        head = (f"ALTERNATING DOME ({p.pattern.replace('_', ' ')}): {c['in/out']} seams alternate, "
                f"{c['in/in'] + c['out/out']} matched (+{p.total_extra_deg():.2f} deg in all)")
        if self.build_band is None:
            return head + f"; all {len(p.bands)} bands shown (N: grow it from the ground)"
        return head + "; up to " + p.band_summary(self.build_band)

    def info_lines(self) -> list[str]:
        lines = [f"TOOL: {self.tool.upper()}   section for new struts: {self.section}   "
                 f"grid {self.step:g} in   edits: {len(self.doc.ops)}", self.message]
        p = self.doc.find(self.selected) if self.selected else None
        if p:
            L, w1, w2 = p.extents()
            lines += [f"{p.name}  [{p.pid}, {p.layer}]",
                      f"length {ftin(L)} ({L:.1f} in)   across {max(w1, w2):.1f} x {min(w1, w2):.1f} in   "
                      f"{p.volume() / dm.BF_IN3:.2f} board ft"]
            for k in ("centreline_in", "cut_in", "stock_in", "length_in"):
                if p.meta.get(k):
                    lines.append(f"{k.replace('_in', '').replace('_', ' ')}: {p.meta[k]} in (from the solver)")
        return lines

    # -- doing ----------------------------------------------------------------
    def click(self, origin, direction) -> None:
        hit = self.doc.pick(origin, direction)
        point = self.doc.last_hit
        if point is None and direction[2] < -1e-6:
            point = origin + direction * (-origin[2] / direction[2])
        if self.tool == "select":
            self.selected = hit.pid if hit else None
            self.message = f"selected {hit.name}" if hit else "nothing there"
        elif self.tool == "cut":
            if hit is None:
                self.message = "nothing to saw there"
                return
            a, b = hit.axis()
            d = b - a
            t = float(np.clip((point - a) @ d / (d @ d), 0.02, 0.98))
            s = round(t * np.linalg.norm(d) / self.step) * self.step / np.linalg.norm(d) if self.step else t
            cut_at = a + d * float(np.clip(s, 0.02, 0.98))
            if self.doc.do({"op": "cut", "pid": hit.pid, "point": cut_at.tolist(), "normal": d.tolist()}):
                self.selected = f"{hit.pid}.a"
                self.message = f"sawn {hit.name} at {np.linalg.norm(cut_at - a):.1f} in from its end"
            else:
                self.message = "that piece is locked, or the saw missed it"
        elif self.tool == "add":
            if point is None:
                return
            q = pc.snap(point, self.step, self.doc.nodes())
            if self.pending is None:
                self.pending = q
                self.message = f"first end at {q[0]:.0f}, {q[1]:.0f}, {q[2]:.0f} -- click the second"
            elif np.linalg.norm(q - self.pending) < 0.5:
                self.message = "both ends landed on the same point -- click somewhere else for the second end"
            else:
                if self.doc.do({"op": "add", "layer": self.doc.active, "kind": self.section,
                                "a": self.pending.tolist(), "b": q.tolist()}):
                    self.selected = self.doc.layers[self.doc.active][-1].pid
                    self.message = f"added a {self.section} strut, {np.linalg.norm(q - self.pending):.1f} in"
                else:
                    self.message = "the active layer is locked"
                self.pending = None

    def move_selected(self, delta, whole_layer: bool = False, copy: bool = False) -> None:
        if whole_layer:
            ok = self.doc.do({"op": "move", "layer": self.doc.active, "delta": list(delta)})
            self.message = f"moved {self.doc.active}" if ok else "the active layer is locked or empty"
            return
        if not self.selected:
            self.message = "select a piece first"
            return
        ok = self.doc.do({"op": "copy" if copy else "move", "pid": self.selected, "delta": list(delta)})
        self.message = ("copied" if copy else "moved") if ok else "that layer is locked"

    def delete_selected(self) -> None:
        if self.selected and self.doc.do({"op": "delete", "pid": self.selected}):
            self.message = f"deleted {self.selected}"
            self.selected = None


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------

_FONTS: dict = {}


def _font(size: int):
    """Loaded once and kept: loading a system font every frame made walking stutter."""
    import pygame
    if size not in _FONTS:
        pygame.font.init()
        _FONTS[size] = pygame.font.SysFont("segoeui", size)
    return _FONTS[size]


def text_surface(lines, width: int, scale: float = 1.0, title=(255, 205, 130)):
    import pygame
    font = _font(int(15 * scale))
    h = int(20 * scale)
    surf = pygame.Surface((width, h * len(lines) + int(12 * scale)), pygame.SRCALPHA)
    surf.fill((12, 16, 22, 205))
    for i, line in enumerate(lines):
        head = i == 0 or line.startswith(("THE WORLD", "EDITING", "CONTROLS"))
        surf.blit(font.render(line, True, title if head else (235, 235, 230)), (int(10 * scale), int(6 * scale) + i * h))
    return surf


def panel_surface(world: World, scale: float = 1.0):
    rows = world.panel_rows()
    return text_surface(["LAYERS   click [x]: show/hide   click name: active   right-click: lock"] + [t for _k, t in rows],
                        int(470 * scale), scale)


def upload_all(renderer, world: World) -> None:
    for key in st.LAYER_KEYS:
        renderer.upload_mesh(f"layer:{key}", world.layer_mesh(key))
    g, lines = world.ground()
    renderer.upload_mesh("ground", g)
    renderer.upload_lines("grid", lines)


def draw(renderer, vp, world: World) -> None:
    renderer.render_mesh("ground", vp)
    renderer.render_lines("grid", vp, 1.0)
    for key in st.LAYER_KEYS:
        if world.doc.visible.get(key) and key not in TRANSPARENT:
            renderer.render_mesh(f"layer:{key}", vp)
    for key in TRANSPARENT:
        if world.doc.visible.get(key):
            renderer.render_mesh(f"layer:{key}", vp)


def _config():
    return SimpleNamespace(camera_height_in=64.0, mouse_sensitivity_deg_px=0.12,
                           walk_speed_in_s=160.0, sprint_multiplier=4.0)


def _aim(cam, eye, target) -> None:
    cam.position = np.array(eye, float)
    d = np.array(target, float) - cam.position
    cam.yaw_deg = math.degrees(math.atan2(d[1], d[0]))
    cam.pitch_deg = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    cam.fly_mode = True


def render_still(path: Path, view: str = "overview", world: World | None = None, size=(1600, 900),
                 panel: bool = True) -> Path:
    import moderngl
    from PIL import Image

    d = _dome()
    world = world or World()
    w, h = size
    ss = 2
    ctx = moderngl.create_standalone_context()
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((w * ss, h * ss), 4)],
                          depth_attachment=ctx.depth_texture((w * ss, h * ss)))
    fbo.use()
    renderer = d.Renderer(ctx)
    upload_all(renderer, world)
    cam = d.FirstPersonCamera(_config(), 200.0)
    _aim(cam, *VIEWS[view])
    ctx.viewport = (0, 0, w * ss, h * ss)
    ctx.clear(0.62, 0.74, 0.86, 1.0, depth=1.0)
    vp = d.perspective_matrix(55.0, w / h, 4.0, 40000.0) @ cam.view_matrix()
    draw(renderer, vp, world)
    if panel:
        s = panel_surface(world, ss)
        renderer.upload_overlay("panel", s)
        renderer.render_overlay("panel", w * ss, h * ss, 24, 24)
        i = text_surface(world.info_lines(), int(1500 * ss), ss)
        renderer.upload_overlay("info", i)
        renderer.render_overlay("info", w * ss, h * ss, 24, h * ss - i.get_height() - 24)
    img = Image.frombytes("RGBA", (w * ss, h * ss), fbo.read(components=4)).transpose(Image.FLIP_TOP_BOTTOM)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((w, h), Image.LANCZOS).convert("RGB").save(path)
    renderer.release()
    ctx.release()
    return path


# ----------------------------------------------------------------------
# The window
# ----------------------------------------------------------------------

def selftest() -> None:
    pc.validate_pieces()
    st.validate_structures()
    dm.validate_document()
    w = World()
    w.tool = "add"
    w.click(np.array([0.0, -300.0, 300.0]), np.array([0.0, 0.0, -1.0]))     # on the ground: snaps to the grid
    w.click(np.array([60.0, -300.0, 300.0]), np.array([0.0, 0.0, -1.0]))
    assert w.doc.layers["mine"] and abs(w.doc.layers["mine"][0].extents()[0] - 60.0) < 1e-6
    w.tool = "add"
    n = len(w.doc.ops)
    w.click(np.array([0.0, -300.0, 300.0]), np.array([0.0, 0.0, -1.0]))
    w.click(np.array([0.5, -300.0, 300.0]), np.array([0.0, 0.0, -1.0]))       # the same grid point again
    assert len(w.doc.ops) == n and "same point" in w.message, w.message
    from . import window                                                     # the window module imports
    assert hasattr(window.App, "update")
    w.tool = "cut"
    z = w.doc.find("Z05A")
    a, b = z.axis()
    mid = (a + b) / 2
    eye = mid + np.array([0.0, -60.0, 0.0])
    w.click(eye, (mid - eye) / np.linalg.norm(mid - eye))
    assert w.doc.ops[-1]["op"] == "cut", w.message
    assert len(w.panel_rows()) == len(st.LAYERS) and w.info_lines()
    print("world3d selftest: ok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="world3d")
    ap.add_argument("--still")
    ap.add_argument("--view", default="overview", choices=list(VIEWS))
    ap.add_argument("--select")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--band", type=int, help="the alternating dome up to this band (a still)")
    ap.add_argument("--pattern", choices=st.ALT_PATTERNS, help="the alternating dome's pattern")
    a = ap.parse_args(argv)
    if a.pattern:
        st.ALT["pattern"] = a.pattern
    if a.selftest:
        selftest()
        return 0
    if a.still:
        w = World()
        w.selected = a.select
        w.build_band = a.band
        if a.band or a.view == "alt_dome":
            w.message = w.alt_line()
        print(render_still(Path(a.still), a.view, w))
        return 0
    from .window import App
    App().run(a.frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
