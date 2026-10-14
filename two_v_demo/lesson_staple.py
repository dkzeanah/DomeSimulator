"""The Staple House: the dome as housing's staple, and the papercuts it leaves out.

The film of the Complete Edition's chapter of the same name (October 2026), set in
the Cabin World and narrated in the owner's voice. His analogy -- *the dome is a
McDouble*: cheap, fast, known, the same every time, the staple a whole market stands
on -- is spoken as his; the title, the thumbnails and the campaign use the idea's own
name, because the analogy names somebody else's trademark.

Nothing is typed. Every figure is read from :mod:`two_v_demo.staple_facts` (the
published NAHB house, the numbers page's loan, the stem cell's invoice, the fifteen
hands), and every exhibit is sized by one (:mod:`two_v_demo.staple_scene`).

    py -3.12 -m film stills cabin_staple
    py -3.12 -m film make cabin_staple --voice mine --pace 1.5
"""

from __future__ import annotations

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import shots
from . import staple_facts as sfacts
from . import staple_scene as ss
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)

F = sfacts.facts()
PC = ss.PC


def usd(v: float) -> str:
    return f"${v:,.0f}"


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app, builder: bool = False) -> None:
    cw.paint(app, hide=() if builder else ("builder",), subject=False)
    app.static_layer("staple:platform", cabin_stage.platform)


def _grow(p: float, speed: float = 1.6) -> float:
    return min(1.0, max(0.0, p * speed))


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.4], "THE STAPLE HOUSE", AMBER)


def p_staple(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.35], "CHEAP. FAST. KNOWN. THE SAME EVERY TIME.", WHITE)


def p_first(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.builder + [0, 0, 2.1], "A FIRST HOME, NOT A LAST ONE", AMBER)


def p_papercuts(app, opaque, transparent, p):
    _world(app)
    (b, tops), names, _scale = ss.papercuts(_grow(p))
    opaque.vertices.extend(b.vertices)
    if p > 0.55:
        for k, (top, name) in enumerate(zip(tops, names)):
            if k % 2 == 0 or name in ("Profit", "Overhead and general expenses", "Sales commission"):
                _label(app, top + [0, 0, 0.08], name.split(",")[0].upper()[:22], WHITE)
    _label(app, PC + [0, 0.9, 1.9], f"{F['papercut_lines']} LINES, {usd(F['papercuts'])}", AMBER)


def p_share(app, opaque, transparent, p):
    _world(app)
    (b, _tops), _names, _scale = ss.papercuts(1.0)
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0.9, 1.9], f"{F['papercut_pct']:.0f}% OF THE PRICE", AMBER)
    _label(app, PC + [0, 0.9, 1.65], "NOT ONE BOARD, NOT ONE HOUR ON THE HOUSE", WHITE)


def p_hands(app, opaque, transparent, p):
    _world(app)
    lit = max(1, int(round(F["hands"] * _grow(p, 1.3))))
    b, points = ss.hands(lit)
    opaque.vertices.extend(b.vertices)
    _label(app, points[min(lit, len(points)) - 1] + [0, 0, 0.12], f"{lit}", AMBER)
    _label(app, PC + [0, 0.9, 1.55], f"{F['hands']} SETS OF HANDS IN ONE STUD", WHITE)


def p_interest(app, opaque, transparent, p):
    _world(app)
    b, points = ss.domes(F["interest_domes"], _grow(p, 1.4))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 1.2, 1.4], f"INTEREST: {usd(F['interest'])}", RED)
    _label(app, PC + [0, 1.2, 1.15], f"= {F['interest_domes']:.1f} DOMES", AMBER)


def p_bill(app, opaque, transparent, p):
    _world(app)
    (b, tops), names = ss.invoice(_grow(p), same_scale=False)
    opaque.vertices.extend(b.vertices)
    if p > 0.5:
        for top, name in zip(tops, names):
            _label(app, top + [0, 0, 0.08], name.split(" (")[0].upper()[:18], AMBER if "Margin" in name else WHITE)
    _label(app, PC + [0, 0.9, 1.9], f"{F['dome_lines']} LINES, ONE SELLER: {usd(F['dome_price'])}", AMBER)


def p_side(app, opaque, transparent, p):
    _world(app)
    (pb, _), _n, _s = ss.papercuts(1.0)
    (ib, _), _in = ss.invoice(1.0, same_scale=True)
    opaque.vertices.extend(pb.vertices)
    from .wedge_beyond_scene import _place
    opaque.vertices.extend(_place(ib, [0.0, 1.1, 0.0]).vertices)
    _label(app, PC + [0, -0.3, 1.8], "THEIR PAPERCUTS", WHITE)
    _label(app, PC + [0, 1.1, 0.75], "THE STAPLE'S WHOLE BILL", AMBER)


def p_caveat(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.45], "NOT LIKE FOR LIKE", RED)
    _label(app, m.apex + [0, 0, 0.2], f"{F['dome_floor']:.0f} SQ FT ON A PAD -- NO LAND, NO BEDROOM WING", WHITE)


def p_baseline(app, opaque, transparent, p):
    _world(app)
    b, tops, names, vals = ss.three_prices(_grow(p))
    opaque.vertices.extend(b.vertices)
    for top, name, v in zip(tops, names, vals):
        _label(app, top + [0, 0, 0.12], f"{name} {usd(v)}", AMBER if name == "THE DOME" else WHITE)
    _label(app, PC + [0, 0.9, 1.9], f"THE SAME {F['dome_floor']:.0f} SQ FT", WHITE)


def p_family(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.log_end + [0, 0, 0.6], "FELL. SPLIT. JIG. RAISE.", AMBER)
    _label(app, m.apex + [0, 0, 0.35], "A FAMILY EVENT, NOT A TRANSACTION", WHITE)


def p_close(app, opaque, transparent, p):
    _world(app, builder=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.4], "THE FIRST RUNG", AMBER)


SCENES = {
    "open": p_open, "staple": p_staple, "first": p_first, "papercuts": p_papercuts, "share": p_share,
    "hands": p_hands, "interest": p_interest, "bill": p_bill, "side": p_side, "caveat": p_caveat,
    "baseline": p_baseline, "family": p_family, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    hero = np.array(cw.HERO_EYE)
    dome = m.dome_centre + [0, 0, 0.9]
    exhibit = PC + [0, 0.1, 0.75]
    t = {
        "open": shots.crane_reveal(dome, hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0], 46, 54,
                                   look_start=m.apex),
        "staple": shots.orbit(dome, 7.5, 2.4, 200, 40, 48),
        "first": shots.orbit(dome, 9.0, 2.8, 230, 30, 46),        # outside the frame, the builder in it
        "papercuts": shots.orbit(exhibit, 4.6, 1.3, -95, 20, 48),
        "share": shots.orbit(exhibit, 4.4, 1.0, -75, 20, 48),
        "hands": shots.orbit(PC + [0, 0.2, 0.5], 4.0, 1.9, -90, 25, 48),
        "interest": shots.orbit(PC + [0.5, 0.3, 0.3], 5.6, 3.0, -100, 20, 46),     # row left of the panel
        "bill": shots.orbit(exhibit, 4.4, 1.2, -85, 20, 48),
        "side": shots.orbit(PC + [0, 0.5, 0.7], 5.0, 1.5, -120, 30, 50),
        "caveat": shots.orbit(dome, 9.5, 3.2, 150, 30, 48),
        "baseline": shots.orbit(exhibit, 4.6, 1.4, -80, 20, 48),
        "family": shots.orbit(m.dome_centre + [0, -2.0, 0.8], 8.5, 2.6, 250, 40, 50),
        "close": shots.crane_reveal(dome, hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0], 46, 54,
                                    look_start=m.apex),
    }
    return {slug: cabin_stage.clear_view(shot, cabin_stage.safe) for slug, shot in t.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, None)


def _chapters() -> tuple[Chapter, ...]:
    f = F
    fees = ", ".join(n.split(",")[0].lower() for n, _ in f["fees"][:3])
    rows = [
        (1, "open", "The staple house", "What a dome should be.",
         "When people ask me what this dome is, I don't say shelter. I say it's a McDouble. Cheap, fast, "
         "reliable, consistent, known everywhere. Not the five-course meal. The staple the whole menu "
         "stands on.",
         ["the dome = the staple"]),
        (2, "staple", "What a staple is", "Always there, always the same.",
         "A staple isn't the best thing on the menu. It's the thing that's always there, always the same, "
         "priced so nobody thinks twice, and known so well nobody reads the ingredients to trust it. Its "
         "job is that everybody who walks in walks out fed.",
         ["always there", "always the same", "known"]),
        (3, "first", "A first home, not a last one", "The eighteen-year-old.",
         "An eighteen-year-old doesn't need his first home to be a five-course meal. He needs one that's "
         "honest and filling and gets him through, so he can save for the rest. Without that staple, most "
         "people never get into the housing market at all.",
         ["first rung, not the last"]),
        (4, "papercuts", "The papercuts", "Counted, from the builders' own survey.",
         f"Here's what I mean by papercuts. By the home builders' own survey, a new house sells for "
         f"{usd(f['survey_price'])}. {f['papercut_lines']} lines of that are things like {fees}, financing, "
         f"overhead, marketing, commission and profit. Together, {usd(f['papercuts'])}.",
         [f"{f['fee_lines']} fee lines: {usd(f['fee_total'])}",
          f"{f['margin_lines']} margin lines: {usd(f['margin_total'])}"]),
        (5, "share", "None of it is the house", "A share, not a number.",
         f"That's {f['papercut_pct']:.0f} percent of the price, and not one line of it is a board, a nail or an "
         f"hour of work on the house itself. Each one has a reason. None of them is the house. That's "
         f"{f['papercut_domes']:.0f} of these domes.",
         [f"{f['papercut_pct']:.0f}% of the price", f"= {f['papercut_domes']:.0f} domes"]),
        (6, "hands", "Fifteen sets of hands", "Every stud's road to the wall.",
         f"Under all that, the building itself is {f['building_lines']} separately priced trades, and every "
         f"stud in its frame has passed through {f['hands']} sets of hands between the tree and the wall. "
         f"Every one of them took a margin. A thousand small cuts, and they belong to somebody who isn't you.",
         [f"{f['building_lines']} trades", f"{f['hands']} hands in a stud"]),
        (7, "interest", "The biggest papercut", "Paid by the month.",
         f"And then the loan. Borrow {usd(f['loan'])} at {f['loan_rate']:g} percent for {f['loan_years']:.0f} "
         f"years and the interest alone is {usd(f['interest'])}. More than you borrowed. That's "
         f"{f['interest_domes']:.1f} of these domes, paid a month at a time, so it never looks like a cut.",
         [f"interest {usd(f['interest'])}", f"= {f['interest_domes']:.1f} domes"]),
        (8, "bill", "The staple's bill", "One sheet, one seller.",
         f"Now the staple. The stem cell's whole bill is {f['dome_lines']} lines from one seller, and it adds "
         f"to {usd(f['dome_price'])}. The margin's on it, {usd(f['dome_margin'])}, "
         f"{f['dome_margin_pct']:.0f} percent, where you can see it and argue with it. A staple's allowed to "
         f"make money. It's not allowed to hide where the money goes.",
         [f"{f['dome_lines']} lines: {usd(f['dome_price'])}", f"margin {usd(f['dome_margin'])} printed"]),
        (9, "side", "Side by side", "One scale, both bills.",
         "Put the two bills side by side at the same scale. On the left, only the papercuts. On the right, "
         "the staple's whole bill, frame, shell, services, labour, overhead and margin. Every line of it is "
         "shorter than the tallest papercut.",
         ["same scale"]),
        (10, "caveat", "Not like for like", "What this does not say.",
         f"That's not like for like, and I won't pretend it is. The survey house is many times the floor and "
         f"comes with {usd(f['survey_lot'])} of land. The dome is {f['dome_floor']:.0f} square feet on a pad. "
         f"A family that needs four bedrooms needs the bigger house. What I'm comparing is the shape of the "
         f"bills: how many hands, how many lines that aren't the building.",
         [f"survey land {usd(f['survey_lot'])}", f"dome {f['dome_floor']:.0f} sq ft"]),
        (11, "baseline", "A baseline", "What a staple does to a market.",
         f"Here's the hope. When a dry, serviced, movable building costs {usd(f['dome_price'])}, a "
         f"{usd(f['mhs_same'])} manufactured home of the same floor has to say what the other "
         f"{usd(f['mhs_gap'])} buys, and a {usd(f['site_same'])} site-built one has to say it again. Some of "
         f"it buys real things. Some of it is papercuts. A staple on the menu is how you find out which. "
         f"That's a hope, not a measurement. Not enough of these exist yet to move anything.",
         [f"dome {f['dome_vs_mhs_pct']:.0f}% of manufactured", f"{f['dome_vs_site_pct']:.0f}% of site-built"]),
        (12, "family", "A family event", "Known, and added to for life.",
         "A house bought the usual way is a transaction with a long row of people you never meet. This "
         "one's a family event. Felling, splitting, a jig on the grass, forty panels, a weekend of lifting. "
         "The kids learn the triangle. Every part's on one list and every cut's in one book, and you add to "
         "it a panel at a time for a lifetime, instead of paying for it a month at a time.",
         ["one list", "one book", "a panel at a time"]),
        (13, "close", "The first rung", "The staple underneath.",
         "A staple doesn't end the menu. It's what makes the menu possible. Everything else in the book is "
         "optional: the panels, the fit-outs, the bigger frames. The staple underneath isn't. Build the first "
         "rung like a staple, and a lot more people get to climb.",
         ["the staple house"]),
    ]
    return tuple(_ch(*r) for r in rows)


CHAPTERS = _chapters()


def validate_staple_film() -> None:
    ss.validate_staple_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert len({c.title for c in CHAPTERS}) == len(CHAPTERS)
    assert all("mcdouble" not in c.title.lower() for c in CHAPTERS), "the analogy is spoken, not a title"
    assert any("not like for like" in " ".join(c.narration).lower() for c in CHAPTERS), "keep the caveat"
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye, target = np.asarray(eye, float), np.asarray(target, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, p)
            assert np.linalg.norm(eye - target) > 0.3, ch.slug
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
    lines = ["THE STAPLE HOUSE -- figures", ""]
    for ch in CHAPTERS:
        lines.append(f"{ch.number} {ch.title}")
        lines += [f"    {e}" for e in ch.equations]
    return "\n".join(lines)


STAPLE_LESSON = Lesson(
    key="cabin_staple", brand="DOMESIM", title="The Staple House",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_staple_film, report=report,
    snapshot_prefix="cabin_staple", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
