"""The 40-hour cabin, styled twelve ways: the Dome Creator's finishes on the
book's own dome, on the Cabin World's hilltop.

The cabin is the Creator's 2V dome at the solver's radius
(:mod:`two_v_demo.cabin_styles`); each chapter dresses it in the skin, colours
and foundation of one of the Creator's twelve designs and draws it with the
Creator's own meshes and shader (:mod:`two_v_demo.creator_bridge`), in place
of the deck and the solver's dome. Every price on screen is the Creator's
declared unit price multiplied by a quantity its model measured.

The book's plates for the styling chapters are taken from this lesson; it is a
short narrated film in its own right.

    py -3.12 -m rerender stills cabin_styles
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_styles as cs
from . import cabin_world as cw
from . import creator_bridge as creator
from . import shots
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)

F = cs.facts()
STYLES = [r["label"] for r in F["styles"]]
SLUGS = {name: "s_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")[:24]
         for name in STYLES}


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _cabin(app, cfg: dict, name: str) -> None:
    cw.paint(app, hide=("deck", "dome", "builder"), subject=False)
    creator.draw(app, creator.build(cfg, name), offset=(0.0, 0.0, 0.0))


def _row(name: str) -> dict:
    return next(r for r in F["styles"] if r["label"] == name)


def p_bare(app, opaque, transparent, p):
    _cabin(app, cs.base_config(), "Bare cabin")
    b = F["base"]
    _label(app, (0.0, 0.0, F["radius_m"] + 1.2), f"THE CABIN, BARE: ${b['total']:,.0f}", AMBER)


def _style_painter(name: str):
    def paint(app, opaque, transparent, p):
        _cabin(app, cs.style_config(name), name)
        r = _row(name)
        top = F["radius_m"] + 1.2
        top = max(top, float(creator.build(cs.style_config(name), name).apex) + 1.0)
        _label(app, (0.0, 0.0, top + 0.5), name.upper(), AMBER)
        _label(app, (0.0, 0.0, top), f"${r['total']:,.0f}, {r['weight_kg'] * cs.LB:,.0f} lb, "
                                     f"{r['hours']:.0f} h", WHITE)
    paint.__name__ = "p_" + SLUGS[name]
    return paint


SCENES = {"bare": p_bare, **{SLUGS[n]: _style_painter(n) for n in STYLES}}


def _apex(slug: str) -> float:
    """How tall this chapter's building stands: a treehouse platform lifts it."""
    name = next((n for n, sl in SLUGS.items() if sl == slug), None)
    cfg = cs.style_config(name) if name else cs.base_config()
    return float(creator.build(cfg, name or "Bare cabin").apex)


def _moves() -> dict:
    out = {}
    keys = list(SCENES)
    for i, slug in enumerate(keys):
        apex = _apex(slug)
        target = np.array([0.0, 0.0, max(F["radius_m"] * 0.45, apex - F["radius_m"] * 0.75)])
        start = -120 + (i % 4) * 18
        shot = shots.orbit(target, 10.5 + max(0.0, apex - 2 * F["radius_m"]),
                           2.2 + 0.4 * (i % 3) + max(0.0, apex - 2 * F["radius_m"]) * 0.6, start, 28, 44)
        out[slug] = cabin_stage.clear_view(shot, cabin_stage.safe)
    return out


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations), seconds,
                   (0.0, 0.0, 0.0), slug, None)


def _chapters() -> tuple[Chapter, ...]:
    b = F["base"]
    rows = [(1, "bare", "The cabin, bare", "The book's dome, in the Creator.",
             f"This is the forty-hour cabin's dome, built in the Dome Creator at its own size: two-frequency, "
             f"{F['diameter_ft']:.1f} feet across, {F['struts']} struts and {F['panels']} panels. Bare -- plywood "
             f"panels, cedar shakes and a gravel pad -- the Creator prices it at {b['total']:,.0f} dollars. Now "
             f"the same frame, dressed twelve ways.",
             [f"{F['struts']} struts, {F['panels']} panels, {F['surface_sqft']:.0f} sq ft of shell",
              f"bare: ${b['total']:,.0f}"])]
    for i, name in enumerate(STYLES, start=2):
        r = _row(name)
        skin = r["panel_name"].lower() + (" under " + " and ".join(x.lower() for x in r["layer_names"])
                                         if r["layer_names"] else "")
        rows.append((i, SLUGS[name], name, f"The cabin, dressed as the {name}.",
                     f"The {name}'s finish on the cabin's frame: {skin}, standing on "
                     f"{r['foundation_name'].lower()}. {r['total']:,.0f} dollars, {r['weight_kg'] * cs.LB:,.0f} pounds, "
                     f"and about {r['hours']:.0f} hours of work by the Creator's estimate.",
                     [f"panels ${r['panels']:,.0f}, cladding ${r['cladding']:,.0f}",
                      f"foundation ${r['foundation']:,.0f}, frame ${r['frame']:,.0f}",
                      f"total ${r['total']:,.0f}"]))
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()


def validate_cabin_styles_film() -> None:
    cs.validate_cabin_styles()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert len({c.slug for c in CHAPTERS}) == len(CHAPTERS)
    for ch in CHAPTERS:
        for p in (0.0, 0.5, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye = np.asarray(eye, float)
            assert np.all(np.isfinite(eye)) and eye[2] > 0.3, ch.slug
            assert not cabin_stage.blocked(eye, target), (ch.slug, p)

    class App:
        def __init__(self):
            self.world_labels = []
            self.creator_draws = []

        def static_layer(self, key, builder, subject_points=None):
            assert len(builder().vertices) > 0, key
    for slug, painter in SCENES.items():
        app = App()
        painter(app, TriangleBatch(), TriangleBatch(), 0.5)
        assert app.world_labels and app.creator_draws, slug
    CABIN_STYLES_LESSON.validate()


CABIN_STYLES_LESSON = Lesson(
    key="cabin_styles", brand="DOMESIM", title="The 40 Hour Cabin, Styled Twelve Ways",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_styles_film,
    snapshot_prefix="cabin_styles", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)

del math
