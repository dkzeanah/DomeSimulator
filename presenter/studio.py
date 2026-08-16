"""The Scene Composer: a real-time editor for building a movie from scratch.

This is the cutting room. It puts four things on one screen:

* a **library** of everything that can go on a stage -- domes, doors,
  stoves, tanks, batteries, the builder's own panel and vein layers,
* a **viewport** showing the live 3-D scene at the playhead,
* a **timeline** of scenes and shots you can drag, trim, reorder and
  scrub, exactly like a video editor's track,
* an **inspector** for whatever is selected: the shot's camera and
  narration, a placed object's knobs, or the scene's backdrop.

Nothing here is a preview of something rendered elsewhere. The viewport
uses the same engine, the same frame function and the same camera rig
that the exporter uses, so what you arrange is precisely what renders.

The editor edits a plain document (see :mod:`presenter.edit`) which can be
saved to JSON, reopened, and exported to video from inside this window.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from . import edit as ED
from .engine import OVERLAY_HELP, OVERLAY_LEVELS, PresenterApp
from .library import CATEGORIES, SPEC_BY_KEY, label_for, specs_in
from .script import LENSES, Presentation

# -- palette ---------------------------------------------------------------
BG = (12, 18, 26)
PANEL = (18, 27, 38)
PANEL_HI = (26, 38, 52)
EDGE = (44, 62, 80)
TEXT = (218, 230, 241)
DIM = (137, 157, 175)
CYAN = (68, 205, 255)
AMBER = (255, 186, 92)
GREEN = (113, 227, 166)
RED = (255, 122, 122)

LIB_W = 236
INSP_W = 344
BAR_H = 32
TIMELINE_H = 232
PERSPECTIVE_NAMES = {
    1: "1-point", 2: "2-point", 3: "3-point",
    4: "panorama", 5: "fisheye", 6: "360",
}


class StudioApp(PresenterApp):
    """A Presenter that edits its own presentation instead of just playing
    it. Everything the parent does still works; this adds the chrome."""

    def __init__(self, presentation: Presentation, size=(1600, 900),
                 windowed: bool = True, doc_path: Path | None = None,
                 headless: bool = False):
        # The composer is resizable so its four panels always reflow to
        # fit, and it can flip to full screen and back without losing any
        # of them (F11).
        super().__init__(presentation, headless=headless, windowed=windowed,
                         size=size, resizable=True)
        if not headless:
            self.pygame.display.set_caption(
                f"Scene Composer -- {presentation.title}")
        self.editing_ui = True
        self.doc_path = Path(doc_path) if doc_path else None
        self.sel_shot = 0
        self.sel_object = 0
        self.tab = "shot"                  # shot | stage | scene
        self.lib_category = CATEGORIES[0]
        self.lib_scroll = 0
        self.insp_scroll = 0
        self.tl_zoom = 1.0
        self.regions: list = []
        self.drag = None
        self.text_edit = None              # (action, buffer, prompt, payload)
        self.status = ("Click a piece in the LIBRARY to put it on the "
                       "stage. Space plays.")
        self.playing = False
        self.last_targets = {"origin": None}
        self._undo: list[Presentation] = []
        self._metrics()

    # -- geometry ---------------------------------------------------------

    def _metrics(self) -> None:
        width, height = self.size
        # The side panels and the timeline keep their designed size on a
        # roomy window, but shrink rather than overrun a small one, so all
        # four regions are always fully on screen whatever the size.
        lib_w = int(min(LIB_W, max(150, width * 0.30)))
        insp_w = int(min(INSP_W, max(200, width * 0.34)))
        if width - lib_w - insp_w < 240:              # keep a usable viewport
            spare = max(240, int(width * 0.34))
            lib_w = insp_w = max(120, (width - spare) // 2)
        time_h = int(min(TIMELINE_H, max(120, height * 0.32)))
        self.r_bar = (0, 0, width, BAR_H)
        body_h = max(80, height - BAR_H - time_h)
        self.r_lib = (0, BAR_H, lib_w, body_h)
        self.r_view = (lib_w, BAR_H, max(1, width - lib_w - insp_w), body_h)
        self.r_insp = (width - insp_w, BAR_H, insp_w, body_h)
        self.r_time = (0, BAR_H + body_h, width, height - BAR_H - body_h)
        # moderngl counts rows from the bottom; pygame from the top.
        self.viewport = (self.r_view[0], height - self.r_view[1]
                         - self.r_view[3], self.r_view[2], self.r_view[3])

    def on_resize(self) -> None:
        self._metrics()

    # -- document helpers -------------------------------------------------

    def _push_undo(self) -> None:
        self._undo.append(self.pres)
        del self._undo[:-40]

    def undo(self) -> None:
        if self._undo:
            self.pres = self._undo.pop()
            self._clamp_selection()
            self.status = "Undone."
        else:
            self.status = "Nothing left to undo."

    def _apply(self, new_pres: Presentation, message: str = "") -> None:
        self._push_undo()
        self.pres = new_pres
        self._clamp_selection()
        if message:
            self.status = message

    def _clamp_selection(self) -> None:
        total = ED.shot_count(self.pres)
        self.sel_shot = max(0, min(self.sel_shot, total - 1))
        world = self.scene().world
        self.sel_object = max(0, min(self.sel_object, max(0, len(world) - 1)))

    def scene_index(self) -> int:
        return ED.locate(self.pres, self.sel_shot)[0]

    def scene(self):
        return self.pres.scenes[self.scene_index()]

    def shot(self):
        scene_i, shot_i = ED.locate(self.pres, self.sel_shot)
        return self.pres.scenes[scene_i].shots[shot_i]

    def select_shot(self, flat: int) -> None:
        total = ED.shot_count(self.pres)
        was_scene = self.scene_index()
        self.sel_shot = max(0, min(flat, total - 1))
        self.timeline = self.pres.shot_start(self.sel_shot) + 0.001
        # Keep whatever object is being tuned selected while stepping
        # through shots of the same scene; a different scene has a
        # different stage, so there the selection has to start over.
        if self.scene_index() != was_scene:
            self.sel_object = 0
        self._clamp_selection()
        self._reset_view()

    # -- immediate-mode widgets -------------------------------------------

    def _hit(self, rect, action, payload=None) -> None:
        self.regions.append((rect, action, payload))

    def _text(self, surf, xy, text, color=TEXT, size=14, bold=False):
        surf.blit(self.font(size, bold).render(str(text), True, color), xy)

    def _panel_box(self, surf, rect, title=None):
        pg = self.pygame
        pg.draw.rect(surf, PANEL, rect)
        pg.draw.rect(surf, EDGE, rect, 1)
        if title:
            self._text(surf, (rect[0] + 10, rect[1] + 7), title, CYAN, 13,
                       True)

    def _button(self, surf, rect, text, action, payload=None, active=False,
                tone=None, enabled=True):
        pg = self.pygame
        fill = PANEL_HI if not active else (30, 58, 78)
        pg.draw.rect(surf, fill, rect)
        pg.draw.rect(surf, tone or (CYAN if active else EDGE), rect, 1)
        color = tone or (TEXT if enabled else DIM)
        label = self.font(13).render(str(text), True, color)
        if label.get_width() > rect[2] - 8:          # keep it inside
            while label.get_width() > rect[2] - 14 and len(text) > 3:
                text = text[:-1]
                label = self.font(13).render(text + "…", True, color)
        surf.blit(label, (rect[0] + (rect[2] - label.get_width()) // 2,
                          rect[1] + (rect[3] - label.get_height()) // 2))
        if enabled:
            self._hit(rect, action, payload)

    def _row_button(self, surf, rect, text, action, payload=None,
                    active=False, note=""):
        pg = self.pygame
        pg.draw.rect(surf, (30, 58, 78) if active else PANEL_HI, rect)
        pg.draw.rect(surf, CYAN if active else EDGE, rect, 1)
        font = self.font(13)
        note_w = self.font(12).size(str(note))[0] + 10 if note else 0
        room = rect[2] - 16 - note_w
        text = str(text)
        if font.size(text)[0] > room:          # never run under the note
            while text and font.size(text + "…")[0] > room:
                text = text[:-1]
            text += "…"
        surf.blit(font.render(text, True,
                              TEXT if active else (200, 214, 226)),
                  (rect[0] + 8, rect[1] + 4))
        if note:
            label = self.font(12).render(str(note), True, DIM)
            surf.blit(label, (rect[0] + rect[2] - label.get_width() - 8,
                              rect[1] + 5))
        self._hit(rect, action, payload)

    def _slider(self, surf, rect, label, value, low, high, action, payload,
                shown=None):
        """A labelled value you can drag. Returns nothing; the drag is
        dispatched through ``action`` with the new value."""
        pg = self.pygame
        span = max(1e-9, high - low)
        frac = max(0.0, min(1.0, (float(value) - low) / span))
        x, y, w, h = rect
        self._text(surf, (x, y), label, DIM, 12)
        shown = shown if shown is not None else f"{float(value):.3g}"
        text = self.font(12, True).render(str(shown), True, AMBER)
        surf.blit(text, (x + w - text.get_width(), y))
        track = (x, y + 16, w, 6)
        pg.draw.rect(surf, (30, 42, 56), track)
        pg.draw.rect(surf, CYAN, (x, y + 16, int(w * frac), 6))
        knob = (int(x + w * frac), y + 19)
        pg.draw.circle(surf, (12, 20, 30), knob, 6)
        pg.draw.circle(surf, CYAN, knob, 6, 2)
        self._hit((x, y + 10, w, 18), action, (payload, low, high, x, w))

    def _field(self, surf, rect, label, value, action, payload=None,
               placeholder=""):
        pg = self.pygame
        x, y, w, h = rect
        self._text(surf, (x, y), label, DIM, 12)
        box = (x, y + 15, w, h - 15)
        editing = (self.text_edit is not None
                   and self.text_edit[0] == action
                   and self.text_edit[3] == payload)
        pg.draw.rect(surf, (10, 16, 24), box)
        pg.draw.rect(surf, AMBER if editing else EDGE, box, 1)
        shown = self.text_edit[1] + "_" if editing else str(value or "")
        color = TEXT if (shown or editing) else DIM
        if not shown:
            shown, color = placeholder, DIM
        label_s = self.font(13).render(shown[-46:], True, color)
        surf.blit(label_s, (box[0] + 6, box[1] + (box[3] - 16) // 2))
        self._hit(box, action, payload)

    # -- top bar ----------------------------------------------------------

    def _draw_bar(self, surf):
        pg = self.pygame
        pg.draw.rect(surf, PANEL_HI, self.r_bar)
        pg.draw.line(surf, EDGE, (0, BAR_H), (self.size[0], BAR_H))
        x = 8
        buttons = [
            ("New", "new", None), ("Open…", "open", None),
            ("Save", "save", None), ("Save as…", "save_as", None),
            ("Export video…", "export", None),
            ("Export all demos", "export_all", None),
            ("Undo", "undo", None),
        ]
        for text, action, payload in buttons:
            w = self.font(13).size(text)[0] + 20
            self._button(surf, (x, 5, w, BAR_H - 11), text, action, payload)
            x += w + 5
        level = f"On-screen text: {self.overlay_level.replace('_', ' ')}"
        w = self.font(13).size(level)[0] + 20
        self._button(surf, (x, 5, w, BAR_H - 11), level, "cycle_overlay",
                     None, tone=GREEN)
        x += w + 5
        fs = "Windowed (F11)" if self.is_fullscreen else "Full screen (F11)"
        w = self.font(13).size(fs)[0] + 20
        self._button(surf, (x, 5, w, BAR_H - 11), fs, "fullscreen", None)
        x += w + 5
        name = self.doc_path.name if self.doc_path else "unsaved"
        self._text(surf, (x + 6, 10),
                   f"{self.pres.title}  ({name})", DIM, 13)

    # -- library ----------------------------------------------------------

    def _draw_library(self, surf):
        x, y, w, h = self.r_lib
        self._panel_box(surf, self.r_lib, "LIBRARY")
        self._text(surf, (x + 74, y + 8), "click to add to this scene", DIM,
                   11)
        cy = y + 26
        for category in CATEGORIES:
            rect = (x + 6, cy, w - 12, 19)
            self._row_button(surf, rect, category, "lib_category", category,
                             active=category == self.lib_category)
            cy += 21
        cy += 6
        self.pygame.draw.line(surf, EDGE, (x + 6, cy), (x + w - 6, cy))
        cy += 6
        items = specs_in(self.lib_category)
        visible_h = y + h - cy - 30
        per = max(1, visible_h // 23)
        self.lib_scroll = max(0, min(self.lib_scroll,
                                     max(0, len(items) - per)))
        for spec in items[self.lib_scroll:self.lib_scroll + per]:
            rect = (x + 6, cy, w - 12, 21)
            self._row_button(surf, rect, spec.label, "lib_add", spec.key,
                             note="+")
            cy += 23
        if len(items) > per:
            self._text(surf, (x + 8, y + h - 24),
                       f"{self.lib_scroll + 1}-"
                       f"{min(len(items), self.lib_scroll + per)}"
                       f" of {len(items)}  (wheel scrolls)", DIM, 12)

    # -- inspector --------------------------------------------------------

    def _draw_inspector(self, surf):
        x, y, w, h = self.r_insp
        self._panel_box(surf, self.r_insp)
        tabs = (("shot", "SHOT"), ("stage", "STAGE"), ("scene", "SCENE"))
        tw = (w - 12 - 8) // 3
        for i, (key, label) in enumerate(tabs):
            self._button(surf, (x + 6 + i * (tw + 4), y + 6, tw, 22), label,
                         "tab", key, active=self.tab == key)
        cy = y + 34
        if self.tab == "shot":
            cy = self._insp_shot(surf, x, cy, w)
        elif self.tab == "stage":
            cy = self._insp_stage(surf, x, cy, w, y + h)
        else:
            cy = self._insp_scene(surf, x, cy, w)

    def _insp_shot(self, surf, x, cy, w):
        shot = self.shot()
        flat = self.sel_shot
        inner = w - 24
        self._text(surf, (x + 12, cy),
                   f"Shot {flat + 1} of {ED.shot_count(self.pres)}", CYAN,
                   13, True)
        cy += 20
        self._field(surf, (x + 12, cy, inner, 38), "Name", shot.slug,
                    "edit_slug", flat)
        cy += 44
        self._slider(surf, (x + 12, cy, inner, 30), "Length", shot.duration,
                     0.6, 40.0, "set_duration", "duration",
                     shown=f"{shot.duration:.1f} s")
        cy += 36
        lenses = list(LENSES)
        self._text(surf, (x + 12, cy), "Lens", DIM, 12)
        cy += 15
        lw = (inner - 9) // 4
        for i, lens in enumerate(lenses):
            self._button(surf, (x + 12 + i * (lw + 3), cy, lw, 21), lens,
                         "set_lens", lens, active=shot.lens == lens)
        cy += 27
        self._text(surf, (x + 12, cy), "Perspective", DIM, 12)
        cy += 15
        pw = (inner - 15) // 6
        for i in range(1, 7):
            self._button(surf, (x + 12 + (i - 1) * (pw + 3), cy, pw, 21),
                         PERSPECTIVE_NAMES[i][:7], "set_persp", i,
                         active=shot.perspective == i)
        cy += 27
        # Focus choices come from what this scene actually built.
        names = ["(middle of the scene)"] + sorted(
            k for k in self.last_targets if k != "origin")
        self._text(surf, (x + 12, cy), "Camera looks at", DIM, 12)
        cy += 15
        current = shot.focus or "(middle of the scene)"
        self._row_button(surf, (x + 12, cy, inner, 21), current,
                         "cycle_focus", names, note="change")
        cy += 27
        for label, key, low, high, unit in (
                ("Orbit across the shot", "orbit", -180.0, 180.0, " deg"),
                ("Push in / pull out", "dolly", -0.8, 2.0, "x"),
                ("Start angle", "yaw", -180.0, 180.0, " deg"),
                ("Height of the camera", "pitch", -20.0, 85.0, " deg"),
                ("Raise the look-at point", "height_bias", -3.0, 6.0, " m")):
            value = getattr(shot, key)
            self._slider(surf, (x + 12, cy, inner, 30), label, value, low,
                         high, "set_shot_num", key,
                         shown=f"{value:.3g}{unit}")
            cy += 34
        self._field(surf, (x + 12, cy, inner, 38), "Caption on screen",
                    shot.caption, "edit_caption", flat,
                    placeholder="(nothing written on the picture)")
        cy += 44
        self._field(surf, (x + 12, cy, inner, 38),
                    "Narration (spoken aloud)", " ".join(shot.narration),
                    "edit_narration", flat,
                    placeholder="(silent shot)")
        cy += 44
        bw = (inner - 9) // 4
        for i, (label, action) in enumerate(
                (("+ Shot", "add_shot"), ("Copy", "dup_shot"),
                 ("Delete", "del_shot"), ("+ Scene", "add_scene"))):
            self._button(surf, (x + 12 + i * (bw + 3), cy, bw, 22), label,
                         action, None,
                         tone=RED if action == "del_shot" else None)
        return cy + 28

    def _insp_stage(self, surf, x, cy, w, bottom):
        world = list(self.scene().world)
        inner = w - 24
        self._text(surf, (x + 12, cy),
                   f"On stage in {self.scene().title or self.scene().slug}",
                   CYAN, 13, True)
        cy += 20
        if not world:
            self._text(surf, (x + 12, cy),
                       "Nothing here yet. Click a piece", DIM, 13)
            self._text(surf, (x + 12, cy + 16),
                       "in the LIBRARY to add one.", DIM, 13)
            return cy + 40
        for i, (key, _params) in enumerate(world):
            rect = (x + 12, cy, inner - 56, 21)
            self._row_button(surf, rect, label_for(key), "sel_object", i,
                             active=i == self.sel_object)
            self._button(surf, (x + inner - 40, cy, 20, 21), "^",
                         "obj_up", i)
            self._button(surf, (x + inner - 18, cy, 20, 21), "x",
                         "obj_del", i, tone=RED)
            cy += 23
        cy += 6
        if not 0 <= self.sel_object < len(world):
            return cy
        key, params = world[self.sel_object]
        spec = SPEC_BY_KEY.get(key)
        if spec is None:
            return cy
        self.pygame.draw.line(surf, EDGE, (x + 12, cy), (x + w - 12, cy))
        cy += 8
        blurb = _wrap(spec.blurb, 44)
        for i, line in enumerate(blurb[:3]):
            if i == 2 and len(blurb) > 3:
                line += "…"
            self._text(surf, (x + 12, cy), line, DIM, 12)
            cy += 14
        cy += 4
        shot = self.shot()
        rows = spec.params[self.insp_scroll:]
        for ps in rows:
            if cy > bottom - 46:
                self._text(surf, (x + 12, cy),
                           "…wheel scrolls for more knobs", DIM, 12)
                break
            value = params.get(ps.key, ps.default)
            animated = next((a for a in shot.actions
                             if a[0] == key and a[1] == ps.key), None)
            shown = ps.format(value)
            if animated:
                shown = f"{animated[2]:.3g} -> {animated[3]:.3g}"
            if ps.kind in ("float", "int"):
                self._slider(surf, (x + 12, cy, inner - 48, 30), ps.label,
                             value, ps.low, ps.high, "set_obj_param", ps.key,
                             shown=shown)
                self._button(surf, (x + 12 + inner - 44, cy + 9, 44, 19),
                             "moves" if animated else "move",
                             "toggle_anim", ps.key,
                             tone=GREEN if animated else None)
                cy += 34
            elif ps.kind == "bool":
                self._row_button(surf, (x + 12, cy, inner, 21), ps.label,
                                 "toggle_obj_bool", ps.key,
                                 active=bool(value),
                                 note="on" if value else "off")
                cy += 23
            else:
                self._row_button(surf, (x + 12, cy, inner, 21),
                                 f"{ps.label}: {value}", "cycle_obj_choice",
                                 ps.key, note="change")
                cy += 23
        return cy

    def _insp_scene(self, surf, x, cy, w):
        scene = self.scene()
        scene_i = self.scene_index()
        inner = w - 24
        self._text(surf, (x + 12, cy),
                   f"Scene {scene_i + 1} of {len(self.pres.scenes)}", CYAN,
                   13, True)
        cy += 20
        self._field(surf, (x + 12, cy, inner, 38), "Scene title", scene.title,
                    "edit_scene_title", scene_i)
        cy += 44
        self._field(surf, (x + 12, cy, inner, 38),
                    "Backdrop, in plain English", scene.environment,
                    "edit_environment", scene_i,
                    placeholder="e.g. on a beach at dusk")
        cy += 42
        for line in _wrap("Understood words include beach, desert, snow, "
                          "tropical, forest, mountains, lake, ocean, storm, "
                          "rain, tsunami, tornado, night, dusk and fog, in "
                          "any combination.", 46):
            self._text(surf, (x + 12, cy), line, DIM, 12)
            cy += 14
        cy += 8
        self._field(surf, (x + 12, cy, inner, 38), "Movie title",
                    self.pres.title, "edit_title", None)
        cy += 46
        bw = (inner - 6) // 3
        for i, (label, action, payload) in enumerate(
                (("Scene up", "scene_move", -1),
                 ("Scene down", "scene_move", 1),
                 ("Delete scene", "scene_del", None))):
            self._button(surf, (x + 12 + i * (bw + 3), cy, bw, 22), label,
                         action, payload,
                         tone=RED if action == "scene_del" else None)
        cy += 30
        self._button(surf, (x + 12, cy, inner, 22),
                     "Copy this stage into the next scene", "copy_stage",
                     None)
        return cy + 28

    # -- timeline ---------------------------------------------------------

    def _timeline_metrics(self):
        x, y, w, h = self.r_time
        pad = 12
        avail = w - pad * 2
        total = max(0.5, self.pres.duration)
        return x + pad, avail, (avail / total) * self.tl_zoom

    def _draw_timeline(self, surf):
        pg = self.pygame
        x, y, w, h = self.r_time
        self._panel_box(surf, self.r_time, "TIMELINE")
        ox, avail, pps = self._timeline_metrics()
        ruler_y = y + 26
        clip_y = ruler_y + 40
        clip_h = 62
        total = self.pres.duration

        # ruler
        pg.draw.rect(surf, (10, 16, 24), (ox, ruler_y, avail, 16))
        self._hit((ox, ruler_y, avail, 16), "scrub", (ox, pps))
        step = _tick_step(pps)
        seconds = 0.0
        while seconds <= total + 1e-6:
            px = ox + seconds * pps
            if px > ox + avail:
                break
            pg.draw.line(surf, EDGE, (px, ruler_y), (px, ruler_y + 16))
            self._text(surf, (px + 3, ruler_y + 1), f"{seconds:g}s", DIM, 11)
            seconds += step

        # scene bands
        flat = 0
        band_y = ruler_y + 20
        for si, scene in enumerate(self.pres.scenes):
            span = sum(s.duration for s in scene.shots)
            start = self.pres.shot_start(flat)
            rect = (ox + start * pps + 1, band_y,
                    max(6, span * pps - 2), 16)
            selected = si == self.scene_index()
            pg.draw.rect(surf, (32, 60, 82) if selected else (24, 36, 50),
                         rect)
            pg.draw.rect(surf, CYAN if selected else EDGE, rect, 1)
            name = scene.title or scene.slug
            label = self.font(12).render(name, True,
                                         TEXT if selected else DIM)
            if label.get_width() < rect[2] - 6:
                surf.blit(label, (rect[0] + 4, rect[1] + 2))
            self._hit(rect, "sel_scene", flat)
            flat += len(scene.shots)

        # clips
        for i, (scene, shot) in enumerate(self.pres.all_shots()):
            start = self.pres.shot_start(i)
            cw = max(10, shot.duration * pps - 2)
            rect = (ox + start * pps + 1, clip_y, cw, clip_h)
            selected = i == self.sel_shot
            pg.draw.rect(surf, (30, 54, 74) if selected else (22, 34, 46),
                         rect)
            pg.draw.rect(surf, CYAN if selected else EDGE, rect,
                         2 if selected else 1)
            pg.draw.rect(surf, AMBER if selected else (60, 82, 102),
                         (rect[0], clip_y, 3, clip_h))
            if cw > 34:
                self._text(surf, (rect[0] + 7, clip_y + 5),
                           shot.slug[:int(cw / 7)], TEXT if selected else
                           (196, 210, 224), 12)
                self._text(surf, (rect[0] + 7, clip_y + 20),
                           f"{shot.duration:.1f}s {shot.lens}", DIM, 11)
                if shot.narration:
                    self._text(surf, (rect[0] + 7, clip_y + 34), "says: "
                               + " ".join(shot.narration)[:int(cw / 6)],
                               GREEN, 11)
                if shot.focus:
                    self._text(surf, (rect[0] + 7, clip_y + 47),
                               "at: " + shot.focus[:int(cw / 6)], AMBER,
                               11)
            self._hit((rect[0], clip_y, max(4, cw - 8), clip_h), "clip",
                      (i, ox, pps))
            # the trim handle on the right edge
            self._hit((rect[0] + cw - 8, clip_y, 8, clip_h), "trim",
                      (i, pps))
            pg.draw.rect(surf, (70, 96, 120),
                         (rect[0] + cw - 4, clip_y + clip_h // 2 - 8, 2, 16))

        # playhead
        head = ox + (self.timeline % max(1e-6, total)) * pps
        pg.draw.line(surf, RED, (head, ruler_y), (head, clip_y + clip_h), 2)
        pg.draw.polygon(surf, RED, [(head - 5, ruler_y), (head + 5, ruler_y),
                                    (head, ruler_y + 7)])

        # transport
        ty = clip_y + clip_h + 8
        controls = (("|< Start", "go_start"),
                    ("< Prev", "go_prev"),
                    ("> Play" if not self.playing else "|| Pause",
                     "toggle_play"),
                    ("Next >", "go_next"))
        cx = ox
        for label, action in controls:
            bw = self.font(13).size(label)[0] + 18
            self._button(surf, (cx, ty, bw, 22), label, action, None,
                         active=(action == "toggle_play" and self.playing))
            cx += bw + 5
        self._text(surf, (cx + 8, ty + 4),
                   f"{self.timeline % max(1e-6, total):6.2f}s  of  "
                   f"{total:.1f}s   ·   {ED.shot_count(self.pres)} shots"
                   f" in {len(self.pres.scenes)} scenes", DIM, 13)
        self._text(surf, (ox, ty + 26), self.status, GREEN, 13)
        self._text(surf, (ox, ty + 43),
                   "drag a clip to move it  ·  drag its right edge to "
                   "change its length  ·  click the ruler to scrub  ·  "
                   "wheel over the timeline zooms  ·  space plays", DIM, 12)

    # -- the whole overlay -------------------------------------------------

    def draw_overlay(self, scene, shot, idx, prog, t):
        if not self.editing_ui:
            return super().draw_overlay(scene, shot, idx, prog, t)
        pg = self.pygame
        width, height = self.size
        surf = pg.Surface((width, height), pg.SRCALPHA)
        self.regions = []
        self._draw_bar(surf)
        self._draw_library(surf)
        self._draw_inspector(surf)
        self._draw_timeline(surf)
        # viewport frame + what the camera is doing right now
        vx, vy, vw, vh = self.r_view
        pg.draw.rect(surf, EDGE, (vx, vy, vw, vh), 1)
        info = (f"{scene.title or scene.slug}  ·  {shot.slug}  ·  "
                f"{shot.lens} lens, {PERSPECTIVE_NAMES[shot.perspective]}"
                f"  ·  looking at "
                f"{shot.focus or 'the middle of the scene'}")
        bar = pg.Surface((vw, 22), pg.SRCALPHA)
        bar.fill((8, 14, 22, 190))
        surf.blit(bar, (vx, vy))
        self._text(surf, (vx + 8, vy + 4), info, (200, 216, 230), 13)
        if shot.caption:
            cap = pg.Surface((vw, 20), pg.SRCALPHA)
            cap.fill((8, 14, 22, 190))
            surf.blit(cap, (vx, vy + vh - 20))
            self._text(surf, (vx + 8, vy + vh - 18),
                       f"caption: {shot.caption}", AMBER, 12)
        if self.text_edit is not None:
            self._draw_prompt(surf)
        return surf

    def _draw_prompt(self, surf):
        pg = self.pygame
        width, height = self.size
        _action, buffer, prompt, _payload = self.text_edit
        pw, ph = min(760, width - 80), 104
        x, y = (width - pw) // 2, height // 3
        shade = pg.Surface((width, height), pg.SRCALPHA)
        shade.fill((4, 8, 14, 150))
        surf.blit(shade, (0, 0))
        pg.draw.rect(surf, PANEL, (x, y, pw, ph))
        pg.draw.rect(surf, AMBER, (x, y, pw, ph), 2)
        self._text(surf, (x + 14, y + 12), prompt, AMBER, 14, True)
        box = (x + 14, y + 38, pw - 28, 28)
        pg.draw.rect(surf, (10, 16, 24), box)
        pg.draw.rect(surf, EDGE, box, 1)
        self._text(surf, (box[0] + 6, box[1] + 6), buffer + "_", TEXT, 14)
        self._text(surf, (x + 14, y + 76),
                   "Enter accepts  ·  Esc cancels", DIM, 12)

    # -- interaction -------------------------------------------------------

    def _begin_text(self, action, payload, prompt, initial=""):
        self.text_edit = (action, str(initial), prompt, payload)

    def _commit_text(self):
        if self.text_edit is None:
            return
        action, buffer, _prompt, payload = self.text_edit
        self.text_edit = None
        flat = self.sel_shot
        if action == "edit_slug":
            self._apply(ED.set_shot(self.pres, flat, slug=buffer or "shot"),
                        "Renamed the shot.")
        elif action == "edit_caption":
            self._apply(ED.set_shot(self.pres, flat, caption=buffer),
                        "Caption set." if buffer else "Caption cleared.")
        elif action == "edit_narration":
            self._apply(ED.set_narration(self.pres, flat, buffer),
                        "Narration set." if buffer else "Shot is silent.")
        elif action == "edit_scene_title":
            self._apply(ED.set_scene(self.pres, payload, title=buffer),
                        "Scene renamed.")
        elif action == "edit_environment":
            self._apply(ED.set_scene(self.pres, payload,
                                     environment=buffer),
                        f"Backdrop: {buffer or 'plain'}.")
            self.env_cache.clear()
        elif action == "edit_title":
            self._apply(replace(self.pres, title=buffer or "Untitled"),
                        "Movie renamed.")
        elif buffer:
            if action == "save_as":
                self._save(Path(buffer))
            elif action == "open":
                self._open(Path(buffer))
            elif action == "export":
                self._export(Path(buffer))
            elif action == "export_all":
                self._export_all(Path(buffer))

    def _dispatch(self, action, payload, pos):
        pres, flat = self.pres, self.sel_shot
        scene_i = self.scene_index()
        if action == "lib_category":
            self.lib_category, self.lib_scroll = payload, 0
        elif action == "lib_add":
            self._apply(ED.add_object(pres, scene_i, payload),
                        f"Added {label_for(payload)} to the stage.")
            self.tab = "stage"
            self.sel_object = len(self.scene().world) - 1
        elif action == "tab":
            self.tab, self.insp_scroll = payload, 0
        elif action == "sel_object":
            self.sel_object, self.insp_scroll = payload, 0
        elif action == "obj_del":
            self._apply(ED.remove_object(pres, scene_i, payload),
                        "Removed from the stage.")
        elif action == "obj_up":
            self._apply(ED.move_object(pres, scene_i, payload, -1),
                        "Moved up the stage order.")
            self.sel_object = max(0, payload - 1)
        elif action == "set_lens":
            self._apply(ED.set_shot(pres, flat, lens=payload),
                        f"{payload} lens.")
        elif action == "set_persp":
            self._apply(ED.set_shot(pres, flat, perspective=payload),
                        f"{PERSPECTIVE_NAMES[payload]} perspective.")
        elif action == "cycle_focus":
            names = payload
            current = self.shot().focus or names[0]
            nxt = names[(names.index(current) + 1) % len(names)] \
                if current in names else names[0]
            self._apply(ED.set_shot(pres, flat,
                                    focus="" if nxt == names[0] else nxt),
                        f"Camera looks at {nxt}.")
        elif action == "toggle_anim":
            self._toggle_anim(payload)
        elif action == "toggle_obj_bool":
            key, params = self.scene().world[self.sel_object]
            value = not bool(params.get(payload))
            self._apply(ED.set_object_param(pres, scene_i, self.sel_object,
                                            payload, value))
        elif action == "cycle_obj_choice":
            self._cycle_choice(payload)
        elif action == "add_shot":
            self._apply(ED.add_shot(pres, flat), "Shot added.")
            self.select_shot(flat + 1)
        elif action == "dup_shot":
            self._apply(ED.duplicate_shot(pres, flat), "Shot copied.")
            self.select_shot(flat + 1)
        elif action == "del_shot":
            self._apply(ED.delete_shot(pres, flat), "Shot deleted.")
            self.select_shot(min(flat, ED.shot_count(self.pres) - 1))
        elif action == "add_scene":
            self._apply(ED.add_scene(pres, scene_i), "Scene added.")
            self.select_shot(ED.flat_index(self.pres, scene_i + 1, 0))
        elif action == "scene_move":
            self._apply(ED.move_scene(pres, scene_i, payload), "Scene moved.")
        elif action == "scene_del":
            self._apply(ED.delete_scene(pres, scene_i), "Scene deleted.")
            self.select_shot(min(flat, ED.shot_count(self.pres) - 1))
        elif action == "copy_stage":
            target = min(scene_i + 1, len(pres.scenes) - 1)
            self._apply(ED.copy_stage(pres, scene_i, target),
                        "Stage copied into the next scene.")
        elif action == "fullscreen":
            self.toggle_fullscreen()
        elif action == "sel_scene":
            self.select_shot(payload)
        elif action == "clip":
            index, ox, pps = payload
            self.select_shot(index)
            self.drag = ("clip", index, ox, pps, pos)
        elif action == "trim":
            index, pps = payload
            self.select_shot(index)
            self.drag = ("trim", index, pps, pos, self.shot().duration)
        elif action == "scrub":
            ox, pps = payload
            self._scrub(pos[0], ox, pps)
            self.drag = ("scrub", ox, pps)
        elif action in ("set_duration", "set_shot_num", "set_obj_param"):
            self.drag = ("slider", action, payload, pos)
            self._slider_to(action, payload, pos[0])
        elif action == "toggle_play":
            self.playing = not self.playing
        elif action == "go_start":
            self.select_shot(0)
        elif action == "go_prev":
            self.select_shot(max(0, flat - 1))
        elif action == "go_next":
            self.select_shot(min(ED.shot_count(pres) - 1, flat + 1))
        elif action == "cycle_overlay":
            levels = list(OVERLAY_LEVELS)
            self.overlay_level = levels[
                (levels.index(self.overlay_level) + 1) % len(levels)]
            self.status = (f"Exports will show: "
                           f"{OVERLAY_HELP[self.overlay_level]}.")
        elif action == "undo":
            self.undo()
        elif action == "new":
            self._push_undo()
            self.pres = ED.blank_presentation("Untitled")
            self.doc_path = None
            self.env_cache.clear()
            self.select_shot(0)
            self.status = "New empty movie. Add pieces from the LIBRARY."
        elif action == "save":
            if self.doc_path:
                self._save(self.doc_path)
            else:
                self._begin_text("save_as", None, "Save this movie as:",
                                 "presenter_output/my_movie.json")
        elif action == "save_as":
            self._begin_text("save_as", None, "Save this movie as:",
                             str(self.doc_path
                                 or "presenter_output/my_movie.json"))
        elif action == "open":
            self._begin_text("open", None, "Open which movie file?",
                             "presenter_output/my_movie.json")
        elif action == "export":
            self._begin_text("export", None,
                             "Render to which video file?",
                             "presenter_output/my_movie.mp4")
        elif action == "export_all":
            self._begin_text("export_all", None,
                             "Render every built-in demo into which folder?",
                             "presenter_output/all")
        elif action.startswith("edit_"):
            self._start_field_edit(action, payload)

    def _start_field_edit(self, action, payload):
        shot, scene = self.shot(), self.scene()
        prompts = {
            "edit_slug": ("Name this shot:", shot.slug),
            "edit_caption": ("Caption written on the picture "
                             "(leave empty for none):", shot.caption),
            "edit_narration": ("What is said out loud over this shot:",
                               " ".join(shot.narration)),
            "edit_scene_title": ("Name this scene:", scene.title),
            "edit_environment": ("Describe the backdrop in plain English:",
                                 scene.environment),
            "edit_title": ("Name the movie:", self.pres.title),
        }
        prompt, initial = prompts[action]
        self._begin_text(action, payload, prompt, initial)

    def _toggle_anim(self, param):
        """Turn a knob into a move: hold its value at one end of the shot
        and drive it to the other."""
        key, params = self.scene().world[self.sel_object]
        shot = self.shot()
        existing = next((a for a in shot.actions
                         if a[0] == key and a[1] == param), None)
        if existing:
            self._apply(ED.clear_action(self.pres, self.sel_shot, key,
                                        param),
                        f"{param} holds still again.")
            return
        spec = SPEC_BY_KEY[key].spec(param)
        value = float(params.get(param, spec.default))
        target = spec.high if value < (spec.low + spec.high) * 0.5 \
            else spec.low
        self._apply(ED.set_action(self.pres, self.sel_shot, key, param,
                                  value, target),
                    f"{param} now moves {value:.3g} to {target:.3g} "
                    f"across this shot.")

    def _cycle_choice(self, param):
        scene_i = self.scene_index()
        key, params = self.scene().world[self.sel_object]
        spec = SPEC_BY_KEY[key].spec(param)
        choices = list(spec.choices)
        if not choices:
            return
        current = params.get(param, spec.default)
        nxt = choices[(choices.index(current) + 1) % len(choices)] \
            if current in choices else choices[0]
        self._apply(ED.set_object_param(self.pres, scene_i, self.sel_object,
                                        param, nxt))

    def _slider_to(self, action, payload, mouse_x):
        key, low, high, x0, w = payload
        frac = max(0.0, min(1.0, (mouse_x - x0) / max(1, w)))
        value = low + (high - low) * frac
        if action == "set_duration":
            self._push_undo()
            self.pres = ED.set_shot(self.pres, self.sel_shot,
                                    duration=value)
        elif action == "set_shot_num":
            self._push_undo()
            self.pres = ED.set_shot(self.pres, self.sel_shot, **{key: value})
        else:
            spec = SPEC_BY_KEY[self.scene().world[self.sel_object][0]]
            ps = spec.spec(key)
            if ps and ps.kind == "int":
                value = round(value)
            self._push_undo()
            self.pres = ED.set_object_param(self.pres, self.scene_index(),
                                            self.sel_object, key, value)
        del self._undo[:-40]

    def _scrub(self, mouse_x, ox, pps):
        total = max(1e-6, self.pres.duration)
        self.timeline = max(0.0, min(total - 1e-3, (mouse_x - ox) / pps))
        self.sel_shot = self.pres.shot_at(self.timeline)[0]

    # -- files and rendering ----------------------------------------------

    def _save(self, path: Path) -> None:
        path = Path(path)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pres.to_json(path)
        self.doc_path = path
        self.status = f"Saved {path}"

    def _open(self, path: Path) -> None:
        path = Path(path)
        if not path.is_file():
            self.status = f"No file at {path}"
            return
        try:
            loaded = Presentation.from_json(path)
            loaded.validate()
        except Exception as exc:                     # noqa: BLE001
            self.status = f"Could not open {path.name}: {exc}"
            return
        self._push_undo()
        self.pres = loaded
        self.doc_path = path
        self.env_cache.clear()
        self.select_shot(0)
        self.status = f"Opened {path.name}"

    def _render_message(self, lines) -> None:
        """Paint a standalone notice and show it immediately -- rendering
        blocks the window, so the reason has to be on screen first."""
        pg = self.pygame
        width, height = self.size
        self.screen_fbo.use()
        self.ctx.viewport = (0, 0, width, height)
        self.screen_fbo.clear(0.05, 0.07, 0.11, 1.0)
        surf = pg.Surface((width, height), pg.SRCALPHA)
        y = height // 2 - 20 * len(lines)
        for i, line in enumerate(lines):
            font = self.font(24 if i == 0 else 16, bold=i == 0)
            text = font.render(line, True, AMBER if i == 0 else TEXT)
            surf.blit(text, ((width - text.get_width()) // 2, y))
            y += 34 if i == 0 else 24
        raw = pg.image.tostring(surf, "RGBA", True)
        self.overlay_tex.write(raw)
        self.ctx.disable(self.moderngl.DEPTH_TEST)
        self.ctx.enable(self.moderngl.BLEND)
        self.overlay_tex.use(0)
        self.blit_prog["u_texture"].value = 0
        self.blit_vao.render(mode=5)
        if not self.headless:
            pg.display.flip()

    def _with_full_frame(self, work):
        """Run an export with the editor chrome out of the way.

        The exporter re-uses this very app to draw frames, so the panels
        have to come off and the picture has to fill the window first --
        otherwise the timeline would be baked into the video. Narration
        also stretches shots to fit the speech, so the document is put
        back exactly as it was afterwards."""
        saved_pres = self.pres
        saved_view, saved_ui = self.viewport, self.editing_ui
        self.viewport, self.editing_ui = None, False
        try:
            return work()
        finally:
            self.pres = saved_pres
            self.viewport, self.editing_ui = saved_view, saved_ui
            self._clamp_selection()

    def _export(self, path: Path, narration: bool = True) -> None:
        path = Path(path)
        if path.suffix.lower() != ".mp4":
            path = path.with_suffix(".mp4")
        self._render_message([
            "Rendering your movie…",
            f"to {path}",
            f"On-screen text: {OVERLAY_HELP[self.overlay_level]}.",
            "This window stays frozen until it finishes;",
            "progress is printed in the console window.",
        ])
        try:
            self._with_full_frame(
                lambda: super(StudioApp, self).export(
                    path, narration=narration, overlay=self.overlay_level))
            self.status = f"Rendered {path}"
        except Exception as exc:                     # noqa: BLE001
            self.status = f"Export failed: {exc}"

    def _export_all(self, folder: Path) -> None:
        """Render every built-in demo, plus this movie, into one folder."""
        import importlib
        from presenter_studio import DEMOS
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        saved = self.pres
        done, failed = [], []
        try:
            for i, (key, module_name) in enumerate(DEMOS.items(), 1):
                self._render_message([
                    f"Rendering demo {i} of {len(DEMOS)}: {key}",
                    f"into {folder}",
                    f"On-screen text: {OVERLAY_HELP[self.overlay_level]}.",
                    "This window stays frozen until every one is done;",
                    "progress is printed in the console window.",
                ])
                try:
                    self.pres = importlib.import_module(module_name).build()
                    self.pres.validate()
                    self.env_cache.clear()
                    self._with_full_frame(
                        lambda: super(StudioApp, self).export(
                            folder / f"{key}.mp4",
                            overlay=self.overlay_level))
                    done.append(key)
                except Exception as exc:             # noqa: BLE001
                    failed.append(f"{key}: {exc}")
        finally:
            self.pres = saved
            self.env_cache.clear()
            self._clamp_selection()
        self.status = (f"Rendered {len(done)} demo(s) into {folder}"
                       + (f"; {len(failed)} failed" if failed else ""))
        for line in failed:
            print(f"  export failed -- {line}")

    # -- event loop --------------------------------------------------------

    def handle_events(self):
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type in (pg.VIDEORESIZE, pg.WINDOWRESIZED):
                self.resize(pg.display.get_window_size())
                continue
            if self.text_edit is not None:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.text_edit = None
                    elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                        self._commit_text()
                    elif event.key == pg.K_BACKSPACE:
                        action, buf, prompt, payload = self.text_edit
                        self.text_edit = (action, buf[:-1], prompt, payload)
                    elif event.unicode and event.unicode.isprintable():
                        action, buf, prompt, payload = self.text_edit
                        self.text_edit = (action, buf + event.unicode,
                                          prompt, payload)
                continue
            if event.type == pg.KEYDOWN:
                if not self._key(event):
                    return False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self._mouse_down(event)
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.drag = None
                    self.dragging = False
            elif event.type == pg.MOUSEMOTION:
                self._mouse_motion(event)
        return True

    def _key(self, event) -> bool:
        pg = self.pygame
        key = event.key
        mods = pg.key.get_mods()
        if key == pg.K_ESCAPE:
            return False
        if key == pg.K_F11:
            self.toggle_fullscreen()
        elif key == pg.K_SPACE:
            self.playing = not self.playing
        elif key == pg.K_RIGHT:
            self.select_shot(self.sel_shot + 1)
        elif key == pg.K_LEFT:
            self.select_shot(self.sel_shot - 1)
        elif key == pg.K_HOME:
            self.select_shot(0)
        elif key == pg.K_z and (mods & pg.KMOD_CTRL):
            self.undo()
        elif key == pg.K_s and (mods & pg.KMOD_CTRL):
            self._dispatch("save", None, (0, 0))
        elif key == pg.K_n and (mods & pg.KMOD_CTRL):
            self._dispatch("new", None, (0, 0))
        elif key == pg.K_DELETE:
            self._dispatch("del_shot", None, (0, 0))
        elif key == pg.K_r:
            self._reset_view()
        elif key == pg.K_c:
            self._dispatch("cycle_overlay", None, (0, 0))
        elif key == pg.K_TAB:
            order = ["shot", "stage", "scene"]
            self.tab = order[(order.index(self.tab) + 1) % 3]
        return True

    def _in(self, rect, pos) -> bool:
        x, y, w, h = rect
        return x <= pos[0] < x + w and y <= pos[1] < y + h

    def _mouse_down(self, event) -> None:
        pos = event.pos
        if event.button in (4, 5):
            step = -1 if event.button == 4 else 1
            if self._in(self.r_lib, pos):
                self.lib_scroll = max(0, self.lib_scroll + step)
            elif self._in(self.r_insp, pos):
                self.insp_scroll = max(0, self.insp_scroll + step)
            elif self._in(self.r_time, pos):
                self.tl_zoom = max(0.25, min(8.0, self.tl_zoom
                                             * (0.9 if step > 0 else 1.11)))
            elif self._in(self.r_view, pos):
                self.dist_scale = max(0.3, min(4.0, self.dist_scale
                                               * (1.11 if step > 0 else 0.9)))
            return
        if event.button != 1:
            return
        # Later regions are drawn on top, so test them first.
        for rect, action, payload in reversed(self.regions):
            if self._in(rect, pos):
                self._dispatch(action, payload, pos)
                return
        if self._in(self.r_view, pos):
            self.dragging = True          # orbit the preview camera

    def _mouse_motion(self, event) -> None:
        if self.drag is not None:
            kind = self.drag[0]
            if kind == "slider":
                _k, action, payload, _p = self.drag
                self._slider_to(action, payload, event.pos[0])
            elif kind == "scrub":
                _k, ox, pps = self.drag
                self._scrub(event.pos[0], ox, pps)
            elif kind == "trim":
                _k, index, pps, start, base = self.drag
                delta = (event.pos[0] - start[0]) / max(1e-6, pps)
                self.pres = ED.set_shot(self.pres, index,
                                        duration=base + delta)
                self.status = (f"Shot {index + 1} is now "
                               f"{self.pres.all_shots()[index][1].duration:.1f}s")
            elif kind == "clip":
                _k, index, ox, pps, start = self.drag
                target = self.pres.shot_at(
                    max(0.0, (event.pos[0] - ox) / max(1e-6, pps)))[0]
                if target != index:
                    self._apply(ED.move_shot(self.pres, index, target),
                                f"Moved shot {index + 1} to slot "
                                f"{target + 1}.")
                    self.sel_shot = target
                    self.drag = ("clip", target, ox, pps, event.pos)
            return
        if self.dragging:
            self.yaw_off -= event.rel[0] * 0.25
            self.pitch_off += event.rel[1] * 0.2

    def run(self):
        clock = self.pygame.time.Clock()
        running = True
        while running:
            dt = min(0.1, clock.tick(60) / 1000.0)
            running = self.handle_events()
            if self.playing:
                self.timeline += dt * self.speed
                total = max(1e-6, self.pres.duration)
                if self.timeline >= total:
                    self.timeline = 0.0
                self.sel_shot = self.pres.shot_at(self.timeline)[0]
            self.render(self.timeline)
        self.pygame.quit()


def _wrap(text: str, width: int) -> list[str]:
    words, out, line = str(text).split(), [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if len(trial) <= width or not line:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def _tick_step(pps: float) -> float:
    """A ruler spacing that leaves labels readable at this zoom."""
    for step in (1, 2, 5, 10, 15, 30, 60, 120, 300, 600):
        if step * pps >= 56:
            return float(step)
    return 900.0


def launch(presentation: Presentation, size=(1600, 900),
           fullscreen: bool = True, doc_path=None) -> None:
    # The composer opens full screen so the whole desktop is usable from
    # the start; F11 (or the top-bar button) drops it to a resizable
    # window, and either way every panel reflows to fit.
    StudioApp(presentation, size=size, windowed=not fullscreen,
              doc_path=doc_path).run()
