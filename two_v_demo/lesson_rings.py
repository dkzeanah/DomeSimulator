"""Why a Wedge Stays True: which way the rings run, and what it does to a board as it dries.

A web-engine film (sketch_claude/lesson_web.py; its pictures are
``lessonstage.js``'s ``build_section``). It answers the owner's question -- why a
wedge strut does not shrink the way a store-bought 2x does -- and corrects the
question on the way: **a wedge shrinks too.** What it does not do is change
shape, because both of its sawn faces lie on radii and its bark face lies on a
ring, which are exactly the lines a drying log leaves alone. A store board's
faces cross the rings at whatever angle the saw happened to meet them, so the
same pile of studs cups, leans and checks fifteen different ways, and the mill
planed it straight before most of that had happened.

Every figure, in the narration and on the sheets, is
:mod:`two_v_demo.grain_shrink`'s: the handbook shrinkage and target moisture
(:mod:`~two_v_demo.wood_care`, :mod:`~two_v_demo.seam_climate`), the mill's own
sawing pattern for the same 12-inch log (:func:`~two_v_demo.wedge_geometry.lumber_yield`)
and the exact kerfed wedge (:func:`~two_v_demo.wedge_geometry.split_section`).
The declared values go on screen in chapter 2, before any is used. Chapter 11
corrects, on camera, the book's drying chapter, which had the seam's V opening as
the frame dries (it closes; :func:`two_v_demo.wood_care.sector_after_drying` had the
sign backwards and is fixed). The last chapter states what the wedge still does and
what this film did not measure.

    py -3.12 -m film stills rings          # one still per chapter, both orientations (web engine)
    py -3.12 -m film make rings            # the release: landscape, phone cut, captions, release folder
"""

from __future__ import annotations

from . import grain_shrink as gs
from . import seam_climate as scl
from . import wood_care as wc
from .lessons import Chapter, Lesson

_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
          "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
          "nineteen", "twenty")


def _say(n: int) -> str:
    return _WORDS[n] if 0 <= n < len(_WORDS) else str(n)


def _inches(x: float) -> str:
    """A small length the way a person says it, from the computed figure."""
    x = abs(x)
    if x >= 0.095:
        tenths = round(x * 10)
        return "a tenth of an inch" if tenths == 1 else f"{_say(tenths)} tenths of an inch"
    if x >= 0.0095:
        h = round(x * 100)
        return "a hundredth of an inch" if h == 1 else f"{_say(h)} hundredths of an inch"
    if x >= 0.00095:
        t = round(x * 1000)
        return "a thousandth of an inch" if t == 1 else f"{_say(t)} thousandths of an inch"
    t = max(1, round(x * 10000))
    return "about a ten-thousandth of an inch" if t == 1 else f"{_say(t)} ten-thousandths of an inch"


def _from_heart(d: float) -> str:
    return "less than an inch" if d < 1 else f"about {_say(round(d))} inches"


F = gs.facts()
W = F.wedges[0]
CUP, CALM = F.boards[F.cup_board], F.boards[F.calm_board]
DIA, QTR, HEART = F.boards[F.diamond_board], F.boards[F.quarter_board], F.boards[F.heart_board]
KINDS = F.counts()
MC = scl.C["mc_target"] * 100
FSP = wc.C["fibre_saturation"] * 100
WIDTHS = [m.width_loss_pct for m in F.boards]
EQ = gs.equations()


def ch(n: int, slug: str, title: str, promise: str, narration: tuple[str, ...]) -> Chapter:
    """A chapter whose stage is its own scene in grain_shrink.scenes(), and whose sheet is
    grain_shrink.equations()[slug] (the web engine reads the same function)."""
    words = len(" ".join((promise,) + narration).split())
    return Chapter(slug, f"{n:02}", title, promise, narration, tuple(EQ[slug]),
                   max(10.0, words / 2.6 + 2.0), (0.12, -1.0, 0.2), slug)


CHAPTERS = (
    ch(1, "hook", "Both of them shrink",
       "A wedge strut shrinks. The question is what the shrinking does to its shape.",
       (f"Here are two pieces of wood from the same {_say(round(F.log_in))} inch log, drying from green "
        f"down to {_say(round(MC))} percent moisture.",
        "On the left, a 2x4 the way a mill saws one. On the right, one of the dome's wedges.",
        f"Both get smaller. Only one changes shape. The 2x4 cups by {_inches(CUP.cup_in)}, "
        f"and the wedge's sawn faces stay flat to {_inches(W.face_bow_in)}.",
        "The difference is which way the growth rings run through each piece.")),
    ch(2, "numbers", "Three directions, three numbers",
       "Wood shrinks by different amounts depending on which way you measure it.",
       (f"Green pine doesn't shrink at all until it dries below about {_say(round(FSP))} percent moisture.",
        f"From there to bone dry, the handbook gives {wc.C['shrink_tangential'] * 100:.1f} percent round the growth "
        f"rings, {wc.C['shrink_radial'] * 100:.1f} percent across them, and almost nothing along the grain.",
        f"A building settles near {_say(round(MC))} percent, which is {wc.shrinkage_fraction(scl.C['mc_target']) * 100:.0f} "
        f"percent of the way down. So a frame shrinks about {F.et * 100:.1f} percent round the rings and "
        f"{F.er * 100:.1f} across.",
        f"The pictures draw that movement {_say(round(gs.C['drawn_x']))} times life size, so you can see it. "
        "Every number on screen is the true one.")),
    ch(3, "rule", "One rule decides the shape",
       "Round the rings shrinks more than across them, and that one difference bends straight lines.",
       ("Picture every point on the end of the log moving in toward the pith by the across-the-rings number, "
        "and round the pith by the round-the-rings number.",
        "Lines that run straight out from the pith stay straight. The rings stay round. Every other straight line bends.",
        f"And a ring that goes all the way round can't do what it wants. It comes up {F.check_deg:.1f} degrees short, "
        "so the log end tears open along a radius. That's the check you see on every log end.")),
    ch(4, "sawing", "Where a store board comes from",
       "A mill saws parallel boards through a round log, so every board meets the rings at its own angle.",
       (f"Saw that same log for studs and you get {_say(len(F.boards))} 2x4s.",
        f"Near the top and bottom, the rings lie flat across the board: flatsawn, {_say(KINDS.get('flatsawn', 0))} of them.",
        f"Out at the sides, the rings stand up on edge: quartersawn, {_say(KINDS.get('quartersawn', 0))}.",
        f"And {_say(KINDS.get('boxed heart', 0))} board in the middle has the pith inside it: a boxed heart.",
        "They all get the same grade stamp and go in the same bundle, and nothing on the board says which one you've got.")),
    ch(5, "cup", "Flatsawn: the cup",
       "A face that cuts across the rings bends as it dries, and the nearer the heart, the more.",
       ("A flatsawn board's wide face isn't a radius and it isn't a ring, so it bends. The edges curl away from the heart.",
        f"The stud whose face sat {_from_heart(gs._dist(CUP.board))} from the pith cups {_inches(CUP.cup_in)}. "
        f"The one {_from_heart(gs._dist(CALM.board))} out cups {_inches(CALM.cup_in)}.",
        f"The wider the board, the worse: a 2x10 sawn from the same spot cups {_inches(F.joist.cup_in)}.",
        "That's the deck board that rocks and the shelf that won't sit flat.")),
    ch(6, "diamond", "Rings on a slant: the lean",
       "When the rings cross a board on a slant, its square corners stop being square.",
       ("Where the rings cross at an angle, the board shrinks more along one diagonal than the other, "
        "and the rectangle leans into a parallelogram.",
        f"The stud whose rings meet its face at {DIA.ring_angle_deg:.0f} degrees ends up "
        f"{DIA.diamond_deg:.2f} degrees off square.",
        f"The one cut with its rings standing straight up stays square, and loses the least width of any, "
        f"{QTR.width_loss_pct:.1f} percent against {CUP.width_loss_pct:.1f} for a flatsawn one.",
        "It's the board you'd want. Nobody sorts for it.")),
    ch(7, "check", "Boxed heart: the check",
       "A board with the pith inside holds whole rings, and a whole ring can't shrink the way it wants.",
       ("The middle stud holds the pith, so it holds complete rings, and every one of them wants to shrink "
        "more round its length than across it. A closed loop can't.",
        f"So the wood tears along a radius: a V of {HEART.check_deg:.1f} degrees, about {_inches(HEART.check_gap_in)} "
        "wide where it reaches the face.",
        "Where it opens depends on the weakest spot in that board, so you can't know in advance.")
       + (("A 4x4 post sawn from a log this size holds the pith too. That's why posts split.",)
          if F.post_heart else ())),
    ch(8, "pile", "The pile at the store",
       f"{_say(len(F.boards)).capitalize()} studs from one log, and no two dry alike.",
       ("Pile them the way they come on a cart, turned any which way, and let them dry.",
        f"The width each one loses runs from {min(WIDTHS):.1f} to {max(WIDTHS):.1f} percent. Some cup, some lean, one splits.",
        f"And the mill planed them flat and square at {_say(round(gs.C['sdry_mc'] * 100))} percent moisture, "
        f"the S-DRY on the stamp, so {F.share_still_to_come * 100:.0f} percent of that movement is still to come "
        "after the board is in your wall.",
        "That's the wavy line in the drywall and the nail that backs itself out.")),
    ch(9, "wedge", "Cut on the radius",
       "A wedge's two sawn faces are radii, and its bark face is a ring.",
       ("Now the wedge. Its point sits at the pith, so both sawn faces run straight out along radii, "
        "and its bark face is a growth ring. Those are exactly the lines the rule leaves alone.",
        f"Dried, its sawn faces stay flat to {_inches(W.face_bow_in)}. They sit half a saw kerf off the true radius, "
        "and that's all the bend there is. The bark face stays round.",
        f"The only thing that changes is the angle: {W.angle_green_deg:.0f} degrees closes by {F.sector.close_deg:.2f}.")),
    ch(10, "eight", "Eight wedges, one answer",
       "Every wedge from the log has its pith in the same place, so every one moves the same.",
       (f"Split the whole log into {_say(gs.splits())} and dry them all. Each wedge closes by the same "
        f"{min(x.close_deg for x in F.wedges):.2f} degrees. The difference between the most and the least is zero "
        "to six decimal places.",
        f"The {_say(len(F.boards))} studs from the same log spread across {gs.spread(WIDTHS):.1f} percentage points of width, "
        "with cups and a check on top.",
        "Same tree, same drying. The wedge just never gives the rings a face to pull against.")),
    ch(11, "keys", "Dry first, key last",
       "Predictable isn't the same as zero, and this project once had the direction backwards.",
       (f"In the dome, two wedges meet at a seam with a V between their sawn faces, cut green at "
        f"{F.sector.gap_green_deg:.1f} degrees.",
        "A correction first. The drying chapter of The 40-Hour Cabin said this V opens as the frame dries. "
        "It doesn't. The V is the sector angle less the fold, the fold belongs to the dome, and only the "
        "sector shrinks.",
        f"So the V closes by the same {F.sector.close_deg:.2f} degrees, to {F.sector.gap_dry_deg:.1f}, and each face "
        f"swings in {_inches(F.sector.face_tilt_in)} at the room side. A key fitted green is too wide there.",
        "Because every wedge moves by the same amount, the fix is a rule instead of a guess: dry the frame, "
        "then make the keys.")),
    ch(12, "limits", "What a wedge still does",
       "The numbers that don't help the argument.",
       (f"A wedge still shrinks: about {F.et * 100:.1f} percent round the rings and {F.er * 100:.1f} across, "
        "the same as any pine.",
        f"It's thicker than a 2x, so it dries about {_say(round(F.sector.times_slower_than_board))} times slower.",
        "This film used a textbook log: round, with its rings centred on the pith, no knots, no reaction wood. "
        "And it only looked at the end of the piece.",
        "Along its length, the youngest wood at a wedge's point shrinks a little more than the rest, so a wedge "
        "can bow toward its point. Every wedge the same way, but we haven't measured how much.")),
)


def _selftest() -> None:
    gs.validate_grain_shrink()
    sheets = gs.equations()
    scenes = gs.scenes()
    for c in CHAPTERS:
        assert c.stage in scenes, f"chapter {c.number} has no scene"
        assert list(c.equations) == sheets[c.slug], f"chapter {c.number}'s sheet is not grain_shrink's"
        assert len(c.equations) <= 5 and max(len(e) for e in c.equations) <= 46, c.slug
    RINGS_LESSON.validate()


RINGS_LESSON = Lesson(
    key="rings",
    brand="GRAIN / WHICH WAY THE RINGS RUN",
    title="Why a Wedge Stays True",
    chapters=CHAPTERS,
    selftest=_selftest,
    report=gs.report,
    snapshot_prefix="rings",
    engine="web",
)
