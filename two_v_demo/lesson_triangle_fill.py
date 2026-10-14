"""Closing the Triangle: pairs of wedges, nested to bowtie, filling a dome panel.

The owner's method, shown rather than told: one wedge end-on; a pair, points facing each
other, sliding along the slant from a solid parallelogram to a bowtie while its reach down
the triangle is measured; a real dome triangle at true size filled course by course from
its top corner, nested and then bowtie, side by side; then the whole dome and the trees.
And the correction to the first count, on camera.

Every figure is :mod:`two_v_demo.triangle_fill`'s, which lays every pair in every one of the
solver's triangles; the pieces are :mod:`two_v_demo.triangle_fill_scene`'s.

    py -3.12 -m film stills cabin_triangle_fill
    py -3.12 -m film make cabin_triangle_fill --voice mine --pace 1.5
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import shots
from . import triangle_fill as tf
from . import triangle_fill_scene as ts
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
BLUE = (120, 200, 255)
RED = (255, 140, 120)
GREEN = (111, 235, 155)

F = tf.facts()
BASE, SIDE, _N = tf.dome_faces()[0]
PC = ts.PC
LEFT = PC + np.array([-0.98, 0.0, 0.0])
RIGHT = PC + np.array([0.98, 0.0, 0.0])


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app) -> None:
    cw.paint(app, hide=("builder",), subject=False)
    app.static_layer("fill:platform", cabin_stage.platform)


def _add(opaque, transparent, pieces) -> None:
    b, air = pieces if isinstance(pieces, tuple) else (pieces, None)
    opaque.vertices.extend(b.vertices)
    if air is not None:
        transparent.vertices.extend(air.vertices)


def _p_of(p: float) -> float:
    """The slide: nested, held, out to a bowtie, held."""
    if p < 0.15:
        return 1.0
    if p > 0.80:
        return 0.0
    return 1.0 - (p - 0.15) / 0.65


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    _world(app)
    b, info = ts.triangle(BASE, SIDE, 1.0, show=0.0)
    _add(opaque, transparent, b)
    _label(app, info["apex"] + np.array([0, 0, 0.25]), "THE FRAME IS DONE. NOW CLOSE IT.", AMBER)


def p_wedge(app, opaque, transparent, p):
    _world(app)
    _add(opaque, transparent, ts.wedge_close())
    c = ts.close_points(1.0)
    _label(app, c["top"] + np.array([0, 0.4, 0.06]), f"FACE {F['face_in']:.2f} IN", AMBER)
    _label(app, c["side"] + np.array([0, 0.1, 0]), f"DEPTH {F['depth_in']:.2f} IN", BLUE)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "ONE WEDGE, END ON (3x LIFE SIZE)", WHITE)


def p_pair(app, opaque, transparent, p):
    _world(app)
    _add(opaque, transparent, ts.pair_close(1.0))
    c = ts.close_points(1.0)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "A PAIR, POINTS FACING EACH OTHER", AMBER)
    _label(app, c["side"] + np.array([0, 0.25, 0]), f"NESTED: REACHES {F['depth_in']:.2f} IN DOWN", BLUE)


def p_slide(app, opaque, transparent, p):
    _world(app)
    q = _p_of(p)
    _add(opaque, transparent, ts.pair_close(q))
    pr = tf.pair(q)
    c = ts.close_points(q)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "SLIDE ONE ALONG THE OTHER'S SLANT", AMBER)
    _label(app, c["side"] + np.array([0, 0.3, 0]),
           f"REACH {pr['span_in']:.1f} IN   WOOD {pr['solid']:.0%}", BLUE)
    if q < 0.02:
        _label(app, c["bottom"] + np.array([0, 0.3, -0.05]), "BOWTIE: TIP TO TIP", RED)


def _fill(app, opaque, transparent, p, show, at, tag):
    b, info = ts.triangle(BASE, SIDE, p, show=show, at=at)
    _add(opaque, transparent, b)
    _label(app, info["label"], f"{tag}: {info['shown']} PAIRS, {info['wedges']} WEDGES, {info['feet']:.0f} FT",
           AMBER if p > 0.5 else BLUE)
    return info


def p_nested(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 1.0, min(1.0, p * 1.35), PC, "NESTED")


def p_bowtie(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 0.0, min(1.0, p * 1.35), PC, "BOWTIE")


def p_side(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 1.0, 1.0, LEFT, "NESTED")
    _fill(app, opaque, transparent, 0.0, 1.0, RIGHT, "BOWTIE")


def p_dome(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    n, b = F["nested"], F["bowtie"]
    _label(app, m.apex + np.array([0, 0, 0.55]), f"NESTED: {n['infill_wedges']} WEDGES, {n['infill_ft']:,.0f} FT", AMBER)
    _label(app, m.apex + np.array([0, 0, 0.3]), f"BOWTIE: {b['infill_wedges']} WEDGES, {b['infill_ft']:,.0f} FT", BLUE)


def p_trees(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    n, b = F["nested"], F["bowtie"]
    _label(app, m.log_end + np.array([0, 0, 0.85]), f"{b['trees']:.1f} TO {n['trees']:.1f} PINES", AMBER)
    _label(app, m.log_end + np.array([0, 0, 0.6]), "FRAME AND EVERY TRIANGLE", WHITE)


def p_correction(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 1.0, 1.0, LEFT, "LAID")
    _fill(app, opaque, transparent, 0.0, 1.0, RIGHT, "LAID")
    _label(app, PC + np.array([0, 0.9, 1.6]), "THE FIRST COUNT: AREA / FACE WIDTH", RED)
    _label(app, PC + np.array([0, 0.9, 1.38]), "THIS COUNT: EVERY PAIR LAID", GREEN)


def p_dial(app, opaque, transparent, p):
    _world(app)
    _add(opaque, transparent, ts.pair_close(0.5))
    c = ts.close_points(0.5)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "THE OVERLAP IS A DIAL", AMBER)
    _label(app, c["side"] + np.array([0, 0.3, 0]), "SOLID AT THE CORNERS, AIR IN THE MIDDLE", BLUE)


SCENES = {"open": p_open, "wedge": p_wedge, "pair": p_pair, "slide": p_slide, "nested": p_nested,
          "bowtie": p_bowtie, "side": p_side, "dome": p_dome, "trees": p_trees, "correction": p_correction,
          "dial": p_dial}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    hero = np.array(cw.HERO_EYE)
    dome = m.dome_centre + [0, 0, 0.9]
    close = ts.CLOSE + np.array([0.0, 0.0, -0.25])
    # square on the end grain (the wedges run along x), barely moving, so the section reads
    end_on = lambda r, h, a, s: shots.orbit(close, r, h, 180.0, 4.0, 40)    # the sun behind the camera
    tri = PC + np.array([0.0, 0.0, 0.45])
    t = {
        "open": shots.orbit(tri, 2.8, 2.2, -90, 12, 46),       # in front of the panel's face
        "wedge": end_on(1.7, 0.05, 15, 18),
        "pair": end_on(1.8, 0.05, 15, 18),
        "slide": end_on(1.9, 0.05, 10, 10),
        "nested": shots.orbit(tri, 2.6, 1.7, -90, 85, 44),     # front, then round to the side: the profile
        "bowtie": shots.orbit(tri, 2.6, 1.7, -90, 85, 44),
        "side": shots.orbit(tri, 3.4, 2.8, -90, 8, 50),
        "dome": shots.orbit(dome, 8.0, 2.4, 200, 40, 50),
        "trees": shots.orbit(m.log_end + [0, 0, 0.3], 3.6, 1.2, 170, 40, 46),
        "correction": shots.orbit(tri, 3.4, 2.8, -90, 8, 50),
        "dial": end_on(1.8, 0.05, 15, 18),
    }
    return {slug: cabin_stage.clear_view(shot, cabin_stage.safe) for slug, shot in t.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 2.0)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, None)


def _chapters() -> tuple[Chapter, ...]:
    f = F
    n, b, h = f["nested"], f["bowtie"], f["half"]
    tn, tb = f["iso_nested"], f["iso_bowtie"]
    rows = [
        (1, "open", "Closing the triangle", "The same wedges, again.",
         "The frame is done: three wedges round every triangle. Now close the middle, with the same wedges.",
         [f"one triangle: {BASE:.0f} in base, {SIDE:.2f} in sides"]),
        (2, "wedge", "One wedge", "Its face and its depth.",
         f"Here is one wedge, end on, three times life size. Its face is {f['face_in']:.2f} inches wide. From the "
         f"face to the point it is {f['depth_in']:.2f} inches deep. Deeper than it is wide.",
         [f"face = {f['log_in']:.0f} sin 22.5 = {f['face_in']:.2f} in", f"depth = {f['depth_in']:.2f} in"]),
        (3, "pair", "A pair, points in", "Solid.",
         f"Now a pair. Turn the second one over so the points face each other, and lay the slants together. "
         f"That's a solid block, and it reaches one depth down the triangle: {f['depth_in']:.2f} inches.",
         [f"nested: reach {n['pair_span_in']:.2f} in, {n['solid']:.0%} wood"]),
        (4, "slide", "Slide it to a bowtie", "Twice the reach, half the wood.",
         f"Slide one along the other's slant. The pair reaches further down, and opens in the middle. At the end "
         f"only the points touch: a bowtie. It reaches {b['pair_span_in']:.1f} inches, and it's half air.",
         [f"bowtie: reach {b['pair_span_in']:.2f} in, {b['solid']:.0%} wood", "reach = (2 - overlap) x depth"]),
        (5, "nested", "Filled nested", "Top corner down.",
         f"Fill a triangle from its top corner down, nested. Each pair is as long as the triangle is wide where "
         f"it lies. {tn['courses']} pairs close it: {tn['wedges']} wedges, {tn['wedge_ft']:.0f} feet.",
         [f"{tn['courses']} pairs, {tn['wedge_ft']:.0f} ft"]),
        (6, "bowtie", "Filled bowtie", "Fewer pairs.",
         f"The same triangle with bowtie pairs. Each one reaches twice as far, so {tb['courses']} pairs close it: "
         f"{tb['wedges']} wedges, {tb['wedge_ft']:.0f} feet.",
         [f"{tb['courses']} pairs, {tb['wedge_ft']:.0f} ft"]),
        (7, "side", "Side by side", "The same opening.",
         f"Side by side: the same opening, {tn['wedge_ft']:.0f} feet of wedge nested, {tb['wedge_ft']:.0f} as "
         f"bowties.",
         [f"nested {tn['wedge_ft']:.0f} ft, bowtie {tb['wedge_ft']:.0f} ft"]),
        (8, "dome", "Every triangle", "Forty of them.",
         f"Every triangle in the dome, laid the same way. Nested: {n['infill_wedges']} wedges, "
         f"{n['infill_ft']:,.0f} feet. Bowtie: {b['infill_wedges']} wedges, {b['infill_ft']:,.0f} feet.",
         [f"half way: {h['infill_ft']:,.0f} ft"]),
        (9, "trees", "In trees", "Frame and all.",
         f"With the frame, the whole dome is {b['total_ft']:,.0f} to {n['total_ft']:,.0f} feet of wedge: "
         f"{b['trees']:.1f} to {n['trees']:.1f} sixty foot pines of a foot across.",
         [f"{b['total_ft']:,.0f} to {n['total_ft']:,.0f} ft", f"{tf.TREE_FT:.0f} ft x {tf.SPLITS} wedges a tree"]),
        (10, "correction", "What the first count got wrong", "Laid, not divided.",
         f"The first count divided the open area by the wedge's face width. Laying every pair, nested comes to "
         f"{n['infill_ft']:,.0f} feet, not {f['first_max_ft']:,.0f}, and bowtie to {b['infill_ft']:,.0f}, "
         f"not {f['first_min_ft']:,.0f}. Lay it, don't divide it.",
         [f"first count {f['first_min_ft']:,.0f} to {f['first_max_ft']:,.0f} ft",
          f"laid {b['infill_ft']:,.0f} to {n['infill_ft']:,.0f} ft"]),
        (11, "dial", "The dial", "Solid or air.",
         "The overlap is a dial. Nest them tight at the corners, where the loads gather. Open them in the middle, "
         "where a cavity holds insulation. A bowtie touching at its points alone doesn't keep the weather out, so "
         "test the joint before you trust the least number.",
         ["nested at the corners, open in the middle"]),
    ]
    return tuple(_ch(*r) for r in rows)


CHAPTERS = _chapters()


def validate_triangle_fill_film() -> None:
    ts.validate_triangle_fill_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for q in (0.0, 0.5, 1.0):
            eye, target, fov = MOVES[ch.slug](q)
            eye = np.asarray(eye, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, q)
            m = cw.landmarks()
            assert np.linalg.norm((eye - m.dome_centre)[:2]) > m.dome_r * 1.15, (ch.slug, q, "inside the dome")

    class App:
        def __init__(self):
            self.world_labels = []
            self.built: set = set()

        def static_layer(self, key, builder, subject_points=None):
            if key in self.built:
                return
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key
            self.built.add(key)

    built: set = set()
    for slug, painter in SCENES.items():
        for q in (0.1, 0.5, 0.95):
            app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
            app.built = built
            painter(app, opaque, transparent, q)
            assert np.all(np.isfinite(opaque.vertices)), slug


def report() -> str:
    return "\n".join(f"{c.number} {c.title}: {' '.join(c.narration)}" for c in CHAPTERS)


TRIANGLE_FILL_LESSON = Lesson(
    key="cabin_triangle_fill", brand="DOMESIM", title="Closing the Triangle",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_triangle_fill_film, report=report,
    snapshot_prefix="cabin_triangle_fill", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
