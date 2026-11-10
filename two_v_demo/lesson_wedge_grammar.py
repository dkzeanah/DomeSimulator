"""The Wedge as a Structural Member -- the film of Part 16 of the 40 Hour Cabin.

The video companion to the book's Part 16, set in the Cabin World. It opens on
why a two-frequency dome is the wedge's natural home, then takes the split
sector off the dome and shows what it is as a general structural member: the
equal-area blade, the connection law, the reversed-taper dyad, the assembly
archetypes built at true proportion, which split suits which job, and the
honest closer -- a second moment is not a load.

Nothing is drawn for the film. The solids are :mod:`two_v_demo.wedge_grammar_scene`'s,
extruded from real sector sections, and every figure is read from
:mod:`two_v_demo.wedge_grammar` -- the same engine the book's Part 16 uses, which
imports the dome's own section routine. The 2V dome is the Cabin World's own.

    py -3.12 -m film stills cabin_wedge_grammar
    py -3.12 -m film make   cabin_wedge_grammar --voice mine --pace 1.5
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import shots
from . import wedge_grammar as g
from . import wedge_grammar_scene as wgs
from .lessons import Chapter, Lesson
from .render_kit import WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)

PC = wgs.PC

# The 2V reference chords: the six-foot stick the line is named after, and the
# short chord the icosahedral geometry then forces (chord factors A, B). The
# same pair the book's reference build uses.
_LONG_IN = 72.0
_SHORT_IN = _LONG_IN * (0.5465330581 / 0.6180339887)


def _facts() -> dict:
    from .hubless_geometry import hubless_summary

    fam = g.equal_area_families()
    gates = g.three_gate(g.BUTT_CIRCUMFERENCE_IN)
    stack = g.lamina_stack_bounds()
    chords = g.separated_chord_bounds()
    fat = {gr.splits: gr for gr in gates}
    finest = max(n for n, gr in fat.items() if gr.area_vs_stud >= 1.0)
    return {
        "fam": fam, "gates": gates, "stack": stack, "chords": chords,
        "members": int(hubless_summary().struts),
        "sector": int(round(g.family_angle_deg(8))),
        "glue8": int(round(stack[-1].premium)),
        "finest": finest,
    }


F = _facts()


# Precompute the montage once, so the frame painter only reads it.
_ARCH, _ARCH_LABELS = wgs.archetypes()


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app) -> None:
    cw.paint(app, hide=("builder",), subject=False)
    app.static_layer("grammar:platform", cabin_stage.platform)


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_why2v(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.45], f"TWO LENGTHS, {F['members']} MEMBERS", AMBER)
    _label(app, m.dome_centre + [0, 0, m.dome_r * 0.55],
           f"{F['sector']}° SECTOR = THE SEAM BUDGET", BLUE)


def p_blade(app, opaque, transparent, p):
    _world(app)
    app.static_layer("grammar:families", wgs.families)
    tops = wgs.blade_tops()
    for top, r in zip(tops, F["fam"]):
        _label(app, top, r.name, AMBER if r.splits == F["finest"] else WHITE)
    _label(app, tops[-1] + [0, 0, 0.26], "ONE 2x4'S WOOD, FOUR BLADES", WHITE)


def p_connect(app, opaque, transparent, p):
    _world(app)
    app.static_layer("grammar:beam", wgs.separated_beam)
    _label(app, PC + [0, 0, 0.52], "TWO CHORDS, A WEB", AMBER)
    _label(app, PC + [0, 0, 0.38], f"GLUED {F['glue8']}x LOOSE", BLUE)


def p_dyad(app, opaque, transparent, p):
    _world(app)
    app.static_layer("grammar:dyad", wgs.dyad)
    _label(app, PC + [-0.55, 0, 0.26], "FAT", WHITE)
    _label(app, PC + [0.55, 0, 0.26], "THIN", WHITE)
    _label(app, PC + [0, 0, 0.5], "OPPOSITE SECTOR, REVERSED", AMBER)


def p_archetypes(app, opaque, transparent, p):
    _world(app)
    app.static_layer("grammar:arch", lambda: _ARCH)
    for pt, tag in _ARCH_LABELS:
        _label(app, pt, tag, AMBER)


def p_gates(app, opaque, transparent, p):
    _world(app)
    app.static_layer("grammar:families", wgs.families)
    tops = wgs.blade_tops()
    for top, gr in zip(tops, F["gates"]):
        hot = gr.splits == F["finest"]
        _label(app, top, f"{gr.area_vs_stud:.1f}x 2x4", AMBER if hot else WHITE)
    _label(app, tops[-1] + [0, 0, 0.26],
           f"FINEST WITH A 2x4'S WOOD: {g.family_name(F['finest'])}", GREEN)


def p_close(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.45], "A SECOND MOMENT IS NOT A LOAD", RED)
    _label(app, m.dome_centre + [0, 0, m.dome_r * 0.55], "GEOMETRY, NOT A RATING", WHITE)


SCENES = {
    "why2v": p_why2v, "blade": p_blade, "connect": p_connect, "dyad": p_dyad,
    "archetypes": p_archetypes, "gates": p_gates, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

MATH = ("blade", "connect", "gates")


def beside_worksheet(shot):
    """Slide the camera right so the subject sits left of a math worksheet."""
    def moved(p: float):
        eye, target, fov = shot(p)
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        f = target - eye
        d = np.linalg.norm(f)
        f /= d
        right = np.cross(f, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        k = 0.40 * d * math.tan(math.radians(fov) / 2) * 16 / 9
        return eye + right * k, target + right * k, fov
    return moved


def _moves() -> dict:
    m = cw.landmarks()
    zc = m.dome_centre + [0, 0, m.dome_r * 0.45]
    exhibit = PC + [0.0, 0.0, 0.25]
    tall = PC + [0.0, 0.0, 0.5]
    low = PC + [0.0, 0.0, 0.12]
    t = {
        "why2v": shots.crane_reveal(zc, zc + [1.4, 3.2, -0.3], zc + [2.6, 5.6, 2.2], 44, 50),
        "blade": shots.orbit(tall, 2.4, 0.9, -90, 16, 42),
        "connect": shots.orbit(exhibit, 2.4, 0.7, -90, 12, 44),
        "dyad": shots.orbit(exhibit, 1.9, 0.5, -40, 35, 44),
        "archetypes": shots.orbit(low, 4.6, 2.1, 60, 45, 48),
        "gates": shots.orbit(tall, 2.4, 0.9, -90, 16, 42),
        "close": shots.crane_reveal(zc, np.array(cw.HERO_EYE) + [0.4, 2.6, 0.0],
                                    np.array(cw.HERO_EYE) + [1.2, -2.4, 3.6], 46, 54, look_start=zc),
    }
    out = {}
    for slug, shot in t.items():
        if slug in MATH:
            shot = beside_worksheet(shot)
        out[slug] = cabin_stage.clear_view(shot, cabin_stage.safe)
    return out


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str,
        equations=(), overlay: str | None = None) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, overlay)


def _blade_eqs() -> tuple[str, ...]:
    fam = {r.splits: r for r in F["fam"]}
    out = [f"one 2x4 = {fam[8].area_in2:.2f} sq in, held constant"]
    for n in (8, 32, 64):
        r = fam[n]
        out.append(f"{r.name}: depth {r.radial_depth_in:.1f} in, "
                   f"I {r.i_strong_in4:.1f} strong / {r.i_weak_in4:.2f} weak")
    out.append("strong up, weak down: a blade")
    return tuple(out)


def _connect_eqs() -> tuple[str, ...]:
    s = {b.members: b for b in F["stack"]}
    return (
        "loose: n members = n x one",
        "glued: one section grows as n^3",
        f"so the ratio is n^2: 2->{s[2].premium:.0f}x, 4->{s[4].premium:.0f}x, 8->{s[8].premium:.0f}x",
        f"separated chords, 3 depths apart: {F['chords'][-1].premium:.0f}x",
        "the real member sits between: a test, not a formula",
    )


def _gate_eqs() -> tuple[str, ...]:
    fat = {gr.splits: gr for gr in F["gates"]}
    out = [f"fat end, {g.BUTT_CIRCUMFERENCE_IN:.0f} in round:"]
    for n in (8, 32, 64):
        gr = fat[n]
        out.append(f"{gr.name}: {gr.gross_area_in2:.1f} sq in ({gr.area_vs_stud:.1f}x 2x4), "
                   f"kerf {gr.kerf_fraction * 100:.0f}%")
    out.append(f"finest with a 2x4's wood: {g.family_name(F['finest'])}")
    return tuple(out)


def _chapters() -> tuple[Chapter, ...]:
    rows = [
        (1, "why2v", "Why a two-frequency dome", "The wedge's natural home.",
         f"The dome on this hill is a two-frequency geodesic, and it is the perfect building for a "
         f"split wedge, for four reasons at once. It needs only two stick lengths, which is what a "
         f"bucked log makes. It loads every member along its grain, which is the one thing a wedge is "
         f"superb at. The angle split out of the log, {F['sector']} degrees, is exactly the seam budget "
         f"the dome spends. And it is coarse enough to forgive a variable stick. {F['members']} members, "
         f"two lengths, and the member is more general than the dome.",
         (f"two lengths: {_LONG_IN:.0f} in and {_SHORT_IN:.1f} in",
          f"{F['members']} members, 40 panels",
          f"{F['sector']} deg x 8 = 360: the seam budget")),
        (2, "blade", "Area was never the argument", "Same wood, four shapes.",
         "Take one dressed two-by-four's worth of wood and split it finer: into an eighth, a "
         "sixteenth, a thirty-second, a sixty-fourth. These are not four sizes of one stick. They are "
         "four shapes. As the sector narrows, its strong-axis stiffness climbs and its weak-axis "
         "stiffness collapses. A fine wedge is a structural blade, and that is not a defect. It tells "
         "you to use it as a flange, a rib, a chord, with its depth where the load is.",
         _blade_eqs(), "math"),
        (3, "connect", "The connection makes the structure", "A bundle is not a beam.",
         "Here is the rule everything rests on. Loose, a stack of members is only as stiff as the sum "
         "of its parts, because the layers slide. Glue them so the shear is carried, and the stiffness "
         "grows with the cube of the depth, so the same wood is many times stiffer. The wedges supply "
         "the material. The connection makes the structure. Add wood and add the load path that "
         "activates it, or you have added nothing but weight.",
         _connect_eqs(), "math"),
        (4, "dyad", "Mirror the wedge, reverse the taper", "A part becomes a unit.",
         "One sector is lopsided about the way it bends, so pair it. Take its mate from the far side "
         "of the log and turn it end for end, fat against thin, so the taper cancels and the pair runs "
         "parallel. Now it is symmetric, with two broad faces to connect through and two load paths "
         "down the grain. One wedge is a part. Two opposing wedges, one reversed, are a structural "
         "unit.",
         ("mate = i + N/2, mod N", "reversed fat-to-thin: the taper averages out")),
        (5, "archetypes", "What the shape wants to become", "Beam, column, box.",
         "Give the blade what its shape wants. Opposing sectors as the chords of a beam, a light web "
         "between them, the wood held far from the neutral axis. Eight sectors in a ring around a void, "
         "a wooden column stiff against buckling with its services up the middle. Four closed into a "
         "box, stiff in every direction and in torsion. The fine split that failed as a joist is "
         "excellent as one wall of the box.",
         ("beam: chords apart + web", "column and box: wood round a void")),
        (6, "gates", "Which split, for which job", "Three gates on one tree.",
         f"Not every split works at every size. Three gates decide it. Is there a stick's worth of "
         f"wood in the sector. Is the face wide enough to land a connector on. And how much of the log "
         f"the kerf eats. On the fat end of the example pine, {g.family_name(F['finest'])} is the finest "
         f"split still holding a two-by-four's worth of wood, and a chainsaw's kerf is a few percent of "
         f"a coarse sector's rim but nearly a third of a sixty-fourth's. Choose the split for the job, "
         f"and go coarser as the trunk narrows.",
         _gate_eqs(), "math"),
        (7, "close", "A second moment is not a load", "Geometry, not a rating.",
         "Everything here is geometry. A second moment is not an allowable stress, and a crossover "
         "diameter is not a working load. These numbers carry no species, no grade, no knot, no "
         "moisture. A real rating comes only from testing the primitive, then the connection, then the "
         "bundle, then the building. The sections are promising. The stamp comes from the test rig. "
         "That is the honest end of the deep dive.",
         ("geometry: area, I, S, the crossover", "a working load: a tested rating")),
    ]
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()


# ----------------------------------------------------------------------
# Selftest and report
# ----------------------------------------------------------------------

def validate_wedge_grammar_film() -> None:
    wgs.validate_wedge_grammar_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert len({c.title for c in CHAPTERS}) == len(CHAPTERS)
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye, target = np.asarray(eye, float), np.asarray(target, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, p)
            assert np.linalg.norm(eye - target) > 0.3, ch.slug

    class App:
        def __init__(self):
            self.world_labels = []
            self.built: set = set()

        def static_layer(self, key, builder, subject_points=None):
            if key in self.built:
                return
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key
            assert len(batch.vertices) > 0, (key, "an empty layer")
            self.built.add(key)

    from .render_kit import TriangleBatch
    built: set = set()
    for slug, painter in SCENES.items():
        for p in (0.1, 0.6, 0.95):
            app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
            app.built = built
            painter(app, opaque, transparent, p)
            assert np.all(np.isfinite(opaque.vertices)), slug


def report() -> str:
    lines = ["THE WEDGE AS A STRUCTURAL MEMBER -- figures", ""]
    for ch in CHAPTERS:
        lines.append(f"{ch.number} {ch.title}")
        lines += [f"    {e}" for e in ch.equations]
    return "\n".join(lines)


WEDGE_GRAMMAR_LESSON = Lesson(
    key="cabin_wedge_grammar", brand="DOMESIM",
    title="The Wedge as a Structural Member",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_wedge_grammar_film, report=report,
    snapshot_prefix="cabin_wedge_grammar", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
