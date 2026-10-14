"""The House That Was a Tree: the promo -- the whole project's case, in ninety seconds.

Built for a phone, made to be shared, and the strongest *true* case for the wedge dome:
a steel man. Its devices are the ones short films that travel are built on, used on
facts the project computes:

* a **hook** in the first breath (a tree that is now a house, for less than a used car);
* an **open loop** promised for the end (the trees were the cheapest part) and closed;
* a **villain** that is not a person: the papercuts, the hands, the interest;
* **specific numbers**, every one computed -- specificity is what makes a claim believable;
* **the turn**, and a **rule of three** (two lengths, one jig, forty panels);
* **awe**: the golden ratio in the floor, 148 and 92 inches making a 20 ft log;
* **contrast** of the two bills, one sheet against ten lines of papercuts;
* **inoculation**: the weakest point said out loud -- not yet engineered -- because a
  two-sided case is believed where a one-sided one is not;
* **identity** and a **call to action**: who it is for, and what to do next.

Nothing is typed. Figures come from :mod:`two_v_demo.staple_facts`,
:mod:`two_v_demo.wedge_coverage_facts` and :mod:`master_book.numbers`; the exhibits are the
films' own (:mod:`two_v_demo.staple_scene`, :mod:`two_v_demo.wedge_beyond_scene`,
:mod:`two_v_demo.promo_scene`).

    py -3.12 -m film stills cabin_promo
    py -3.12 -m film make cabin_promo --voice mine --pace 1.5
"""

from __future__ import annotations

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import promo_scene as ps
from . import shots
from . import staple_facts as sfacts
from . import staple_scene as ss
from . import wedge_beyond_scene as ws
from . import wedge_coverage_facts as wc
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)

S = sfacts.facts()
C = wc.facts()
PC = ss.PC


def usd(v: float) -> str:
    return f"${v:,.0f}"


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app, builder: bool = True) -> None:
    cw.paint(app, hide=() if builder else ("builder",), subject=False)
    app.static_layer("promo:platform", cabin_stage.platform)


def _grow(p: float, speed: float = 2.2) -> float:
    return min(1.0, max(0.0, p * speed))


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_hook(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.45], "THIS WAS A TREE", AMBER)
    if p > 0.4:
        _label(app, m.apex + [0, 0, 0.2], f"NOW IT'S A HOUSE: {usd(S['dome_price'])}", WHITE)


def p_loop(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.log_end + [0, 0, 0.7], "THE CHEAPEST PART?", AMBER)


def p_papercuts(app, opaque, transparent, p):
    _world(app, False)
    (b, _tops), _names, _scale = ss.papercuts(_grow(p))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0.9, 1.9], f"{usd(S['papercuts'])} OF PAPERCUTS", RED)
    _label(app, PC + [0, 0.9, 1.65], "NOT ONE BOARD", WHITE)


def p_interest(app, opaque, transparent, p):
    _world(app, False)
    b, _pts = ss.domes(S["interest_domes"], _grow(p, 1.8))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 1.2, 1.4], f"INTEREST: {usd(S['interest'])}", RED)
    _label(app, PC + [0, 1.2, 1.15], f"= MORE THAN {int(S['interest_domes'])} OF THESE HOUSES", AMBER)


def p_hands(app, opaque, transparent, p):
    _world(app, False)
    lit = max(1, int(round(S["hands"] * _grow(p, 1.6))))
    b, _pts = ss.hands(lit)
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0.9, 1.55], f"{S['hands']} HANDS IN ONE STUD", RED)


def p_turn(app, opaque, transparent, p):
    _world(app, False)
    b = ws.log_split(min(1.0, p * 1.6))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0, 0.55], "ONE SAW. ONE LOG. EIGHT WEDGES.", AMBER)


def p_three(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.4], "2 LENGTHS. 1 JIG. 40 PANELS.", AMBER)


def p_golden(app, opaque, transparent, p):
    _world(app, False)
    b = ps.pentagon(_grow(p, 1.5))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0, 1.0], f"{C['pentagon_long_in']:.1f} + {C['pentagon_short_in']:.1f} = 240 IN", AMBER)
    _label(app, PC + [0, 0, 0.8], "THE GOLDEN RATIO, IN ONE LOG", WHITE)


def p_bill(app, opaque, transparent, p):
    _world(app, False)
    (b, _tops), _names = ss.invoice(_grow(p), same_scale=False)
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0.9, 1.9], f"THE WHOLE BILL: {usd(S['dome_price'])}", AMBER)
    _label(app, PC + [0, 0.9, 1.65], f"{S['dome_lines']} LINES. ONE SELLER.", WHITE)


def p_trees(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.log_end + [0, 0, 0.8], f"{C['trees_min_12']} TO {C['trees_max_12']} TREES", AMBER)
    _label(app, m.log_end + [0, 0, 0.55], "FRAME AND EVERY WALL", WHITE)


def p_honest(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.45], "NOT ENGINEERED YET", RED)
    _label(app, m.apex + [0, 0, 0.2], "EVERY NUMBER: OPEN CODE", GREEN)


def p_who(app, opaque, transparent, p):
    _world(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.4], "FOLLOW THE BUILD", AMBER)


SCENES = {"hook": p_hook, "loop": p_loop, "papercuts": p_papercuts, "interest": p_interest, "hands": p_hands,
          "turn": p_turn, "three": p_three, "golden": p_golden, "bill": p_bill, "trees": p_trees,
          "honest": p_honest, "who": p_who}


# ----------------------------------------------------------------------
# Cameras: closer and quicker than a lesson's
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    hero = np.array(cw.HERO_EYE)
    dome = m.dome_centre + [0, 0, 0.9]
    exhibit = PC + [0, 0.1, 0.75]
    log = m.log_end + [0, 0, 0.3]
    t = {
        "hook": shots.crane_reveal(dome, hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0], 46, 54, look_start=m.apex),
        "loop": shots.orbit(log, 3.2, 1.0, 200, 50, 46),
        "papercuts": shots.orbit(exhibit, 4.4, 1.2, -100, 30, 48),
        "interest": shots.orbit(PC + [0.3, 0.3, 0.3], 5.0, 3.0, 80, 25, 46),        # from the far side, clear of the dome
        "hands": shots.orbit(PC + [0, 0.2, 0.5], 3.8, 1.8, -95, 30, 48),
        "turn": shots.orbit(PC + [0.95, 0, 0.17], 1.7, 0.4, -40, 50, 44),
        "three": shots.orbit(dome, 8.0, 2.6, 220, 60, 50),
        "golden": shots.orbit(PC + [0, 0, 0.1], 3.6, 4.2, 80, 35, 44),        # from above, the far side
        "bill": shots.orbit(exhibit, 4.4, 1.2, -80, 30, 48),
        "trees": shots.orbit(log, 4.0, 1.4, 160, 40, 46),
        "honest": shots.orbit(dome, 8.6, 2.4, 140, 40, 48),
        "who": shots.crane_reveal(dome, hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0], 46, 54, look_start=m.apex),
    }
    return {slug: cabin_stage.clear_view(shot, cabin_stage.safe) for slug, shot in t.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script: the owner's voice
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(5.0, len(narration.split()) / 2.6 + 1.0)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, None)


def _chapters() -> tuple[Chapter, ...]:
    s, c = S, C
    rows = [
        (1, "hook", "This was a tree", "Now it's a house.",
         f"This was a tree. Now it's a house. And it cost less than a used car: {usd(s['dome_price'])}.",
         [f"{usd(s['dome_price'])}, the whole building"]),
        (2, "loop", "The cheapest part", "Stay for the end.",
         "Stay to the end, because the strangest number in it is the trees. They were the cheapest part.",
         ["the trees: at the end"]),
        (3, "papercuts", "The papercuts", "Not one board.",
         f"A new house sells for {usd(s['survey_price'])}. {usd(s['papercuts'])} of that is fees and margins. "
         f"Not one board. Not one hour on the house.",
         [f"{s['papercut_lines']} lines, {s['papercut_pct']:.0f}% of the price"]),
        (4, "interest", "The biggest cut", "Paid by the month.",
         f"Borrow {usd(s['loan'])} and you pay back {usd(s['loan_total'])}. The interest alone would build "
         f"more than {int(s['interest_domes'])} of these.",
         [f"interest {usd(s['interest'])}"]),
        (5, "hands", "Fifteen hands", "Every one took a cut.",
         f"Every stud in that house went through {s['hands']} sets of hands. Every one of them took a cut.",
         [f"{s['hands']} hands, tree to wall"]),
        (6, "turn", "So I cut them out", "One saw.",
         "So I cut them out. One chainsaw. One log. Eight wedges, and nobody measures an angle.",
         ["one log -> 8 wedges"]),
        (7, "three", "Two lengths", "One jig, forty panels.",
         f"{c['members']} members in two lengths. One jig. Forty flat panels, built on the grass and lifted "
         f"into a dome.",
         [f"{c['long_in']:.0f} in and {c['short_in']:.2f} in"]),
        (8, "golden", "Even the floor", "The golden ratio.",
         f"Even the floor is free geometry. Cut a twenty foot log at {c['pentagon_long_in']:.1f} inches and "
         f"what's left is {c['pentagon_short_in']:.1f}: the golden ratio. Five logs make a pentagon.",
         [f"{c['pentagon_long_in']:.1f} + {c['pentagon_short_in']:.1f} = 240 in"]),
        (9, "bill", "The whole bill", "On one sheet.",
         f"The whole bill is {s['dome_lines']} lines, from one seller. {usd(s['dome_price'])}, with the margin "
         f"printed on it.",
         [f"margin {usd(s['dome_margin'])}"]),
        (10, "trees", "The trees", "As promised.",
         f"And the trees? The frame and every wall closed in wood: {c['trees_min_12']} to "
         f"{c['trees_max_12']} pines.",
         [f"{c['total_min_ft_12']:,.0f} to {c['total_max_ft_12']:,.0f} ft of wedge"]),
        (11, "honest", "Not yet", "What it isn't.",
         "Is it engineered yet? No. That's the first thing the money buys. Everything else is open: every "
         "number you just heard is computed in code anyone can check.",
         [f"{sum(ok for *_x, ok in wc.verification())} of {len(wc.verification())} figures checked"]),
        (12, "who", "Who it's for", "Follow the build.",
         "It isn't for everyone. It's for the eighteen-year-old, the veteran, the mother who's done paying for "
         "someone else's papercuts. Follow the build.",
         ["follow the build"]),
    ]
    return tuple(_ch(*r) for r in rows)


CHAPTERS = _chapters()


def validate_promo_film() -> None:
    ss.validate_staple_scene()
    ps.validate_promo_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert any("engineered" in " ".join(c.narration) for c in CHAPTERS), "the weakest point stays in"
    hook = " ".join(CHAPTERS[0].narration)
    assert len(hook.split()) <= 25, "the hook must land in the first breath"
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for p in (0.0, 0.5, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye = np.asarray(eye, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, p)
            m = cw.landmarks()
            assert np.linalg.norm((eye - m.dome_centre)[:2]) > m.dome_r * 1.15, (ch.slug, p, "inside the dome")

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
        for p in (0.1, 0.6, 0.95):
            app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
            app.built = built
            painter(app, opaque, transparent, p)
            assert np.all(np.isfinite(opaque.vertices)), slug


def report() -> str:
    lines = ["THE HOUSE THAT WAS A TREE -- figures", ""]
    for ch in CHAPTERS:
        lines.append(f"{ch.number} {ch.title}: {' '.join(ch.narration)}")
    return "\n".join(lines)


PROMO_LESSON = Lesson(
    key="cabin_promo", brand="DOMESIM", title="The House That Was a Tree",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_promo_film, report=report,
    snapshot_prefix="cabin_promo", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/frankenbeat", audio_bed_gain=0.14,
)
