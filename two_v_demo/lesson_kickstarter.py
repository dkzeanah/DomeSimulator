"""The campaign video: the montage's persuasion, the masterclass's proof.

Every other lesson here teaches somebody who already wants to know.  This
one has to earn the next thirty seconds from a stranger who is scrolling,
so it is built on a different rule: **make a claim, then show the number
that makes it true, on the same screen.**

Nothing in the narration is a slogan.  The forty-two percent, the parts
list, the dollar figures and the equipment budget all come out of
``dome_advantage`` and ``dome_costing``, and both of those refuse to
import if their own arithmetic stops holding.
"""

from __future__ import annotations

import math

import numpy as np

from .dome_advantage import FACT, advantages, box_envelope, dome_envelope
from .dome_costing import Startup, build_variants
from .franken_economics import flat_rate_table
from .geometry import build_demo_geometry, normalize
from .lesson_franken import SCENES as FRANKEN_SCENES
from .lesson_hype import SCENES_V6 as HYPE_SCENES
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
)
from .segments import compose


GEOMETRY = build_demo_geometry()
SCALE = 5.0
DOME = dome_envelope()
BOX = box_envelope()
BUILDS = build_variants()
STARTUP = Startup()


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _dome(opaque, transparent, scale: float, origin=None, phase: float = 1.0,
          frame=WHITE, skin=(0.32, 0.62, 0.92, 0.30)) -> None:
    """The standard hemisphere, optionally somewhere other than the origin."""
    shift = np.zeros(3) if origin is None else np.asarray(origin, dtype=float)
    edges = list(GEOMETRY.hemisphere_edges)
    shown = int(len(edges) * clamp(phase))
    for edge in edges[:shown]:
        a, b = (GEOMETRY.vertices[i] * scale + shift for i in edge)
        opaque.cylinder(a, b, scale * 0.012, frame, 7)
    if phase > 0.85:
        for face in GEOMETRY.hemisphere_faces:
            corners = GEOMETRY.vertices[[int(v) for v in face]] * scale + shift
            transparent.triangle(corners[0], corners[1], corners[2], skin,
                                 normalize(corners.mean(axis=0) - shift))


def _box_house(opaque, origin, side: float, height: float, pitch: float,
               colour=(0.58, 0.30, 0.30, 1.0)) -> None:
    """A gable-roofed box, drawn to the same scale as the dome.

    The roof is two real planes and two gable ends rather than a stack of
    shrinking boxes -- stacked boxes render as a visible ziggurat, and a
    comparison that makes the rival look silly is not a fair comparison.
    """
    shift = np.asarray(origin, dtype=float)
    opaque.box(shift + np.array([0.0, 0.0, height * 0.5]),
               (side, side, height), colour)

    rise = (side / 2.0) * pitch
    half = side / 2.0
    roof = (0.44, 0.22, 0.22, 1.0)

    def at(x, y, z):
        return shift + np.array([x, y, z], dtype=float)

    ridge_a = at(-half, 0.0, height + rise)
    ridge_b = at(half, 0.0, height + rise)

    def facet(points, outward) -> None:
        """Emit a face wound so it survives back-face culling.

        The renderer culls by winding, not by the normal handed to it, so
        a face can be correctly lit and still invisible. Deriving the
        winding from the outward direction beats deducing it per face --
        the first version of this roof was wound backwards and simply did
        not appear.
        """
        outward = normalize(np.asarray(outward, dtype=float))
        wound = list(points)
        turn = np.cross(wound[1] - wound[0], wound[2] - wound[0])
        if float(np.dot(turn, outward)) < 0.0:
            wound.reverse()
        for index in range(1, len(wound) - 1):
            opaque.triangle(wound[0], wound[index], wound[index + 1], roof,
                            outward)

    for sign in (1.0, -1.0):
        facet([at(-half, sign * half, height), at(half, sign * half, height),
               ridge_b, ridge_a], (0.0, sign * pitch, 1.0))

    for sign in (1.0, -1.0):
        x = sign * half
        facet([at(x, -half, height), at(x, half, height),
               at(x, 0.0, height + rise)], (sign, 0.0, 0.0))


# ----------------------------------------------------------------------
# Act one: the problem, and the shape
# ----------------------------------------------------------------------

def scene_kick_title(app, opaque, transparent, p: float) -> None:
    spin = ease_in_out(clamp(p * 1.4))
    _dome(opaque, transparent, SCALE, phase=spin)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.0]),
                   "A HOUSE THAT COSTS WHAT ITS PARTS COST", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.4]),
                   "one hundred and twenty sticks", (169, 188, 203)),
    ])


def scene_kick_problem(app, opaque, transparent, p: float) -> None:
    """The thing everybody already lives in, and what its skin costs."""
    _box_house(opaque, (0.0, 0.0, 0.0), 7.2, 4.6, FACT["gable_pitch"])
    if p > 0.25:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 8.6]),
            f"{BOX.envelope_sqft:.0f} SQ FT OF SKIN", (255, 106, 106)))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 10.4]),
                   "THE SHAPE EVERYONE BUILDS", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.4]),
                   f"{BOX.footprint_sqft:.0f} sq ft of floor",
                   (169, 188, 203)),
    ])


def scene_kick_versus(app, opaque, transparent, p: float) -> None:
    """Same floor. Side by side. The whole argument in one frame.

    Laid along X because the camera sits out on +Y -- separating these
    along Y would stack them in depth and the comparison would vanish.
    """
    grow = ease_in_out(clamp(p * 1.5))
    _box_house(opaque, (7.0, 0.0, 0.0), 7.2, 4.6, FACT["gable_pitch"])
    _dome(opaque, transparent, SCALE, origin=(-7.5, 0.0, 0.0), phase=grow,
          frame=CYAN)

    surface = advantages()[0]
    app.world_labels.extend([
        WorldLabel(np.array([7.0, 0.0, 9.4]),
                   f"{BOX.envelope_sqft:.0f} sq ft", (255, 106, 106)),
        WorldLabel(np.array([-7.5, 0.0, SCALE + 1.6]),
                   f"{DOME.envelope_sqft:.0f} sq ft", (61, 211, 255)),
        WorldLabel(np.array([7.0, 0.0, -1.4]), "square house", (169, 188, 203)),
        WorldLabel(np.array([-7.5, 0.0, -1.4]), "2V dome", (169, 188, 203)),
    ])
    if p > 0.45:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 11.4]),
            f"{surface.percent_better:.0f}% LESS TO BUILD, SEAL AND HEAT",
            (111, 235, 155)))


def scene_kick_wind(app, opaque, transparent, p: float) -> None:
    """Wind finds nothing to push on."""
    _dome(opaque, transparent, SCALE, phase=1.0, frame=CYAN)
    # Streamlines sliding across the screen, parting where the shell is.
    flow = (p * 1.6) % 1.0
    for lane in range(7):
        z = 0.4 + lane * 0.85
        for step in range(16):
            t = (step / 16.0 + flow) % 1.0
            x = -13.0 + t * 26.0
            if math.hypot(x, z) < SCALE * 1.04 and z < SCALE:
                continue
            fade = 0.30 + 0.55 * math.sin(t * math.pi)
            opaque.box((x, -3.4, z), (0.5, 0.09, 0.09),
                       (0.38, 0.72, 0.95, fade))
    wind = advantages()[3]
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.1]),
                   "NOTHING FOR THE WIND TO PUSH ON", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   f"drag {wind.dome:.2f} against {wind.other:.2f} for a box"
                   f" -- {wind.percent_better:.0f}% less", (169, 188, 203)),
    ])


def scene_kick_triangle(app, opaque, transparent, p: float) -> None:
    """Why it holds: a triangle cannot change shape without breaking."""
    push = math.sin(clamp(p) * math.tau * 2.0) * 0.9

    # A square racks. Drawn at +X, which is screen left.
    corners = [np.array([3.4, 0.0, 0.4]), np.array([8.4, 0.0, 0.4]),
               np.array([8.4 + push, 0.0, 5.4]),
               np.array([3.4 + push, 0.0, 5.4])]
    for index in range(4):
        opaque.cylinder(corners[index], corners[(index + 1) % 4], 0.13, RED, 8)

    # A triangle does not.
    tri = [np.array([-8.4, 0.0, 0.4]), np.array([-3.4, 0.0, 0.4]),
           np.array([-5.9, 0.0, 5.4])]
    for index in range(3):
        opaque.cylinder(tri[index], tri[(index + 1) % 3], 0.13, GREEN, 8)

    app.world_labels.extend([
        WorldLabel(np.array([-5.9, 0.0, 6.4]), "RIGID", (111, 235, 155)),
        WorldLabel(np.array([5.9, 0.0, 6.6]), "RACKS", (255, 106, 106)),
        WorldLabel(np.array([0.0, 0.0, 8.4]),
                   "A TRIANGLE CANNOT CHANGE SHAPE", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.4]),
                   "and the dome is forty of them", (169, 188, 203)),
    ])


# ----------------------------------------------------------------------
# Act two: the money
# ----------------------------------------------------------------------

def _bars(app, opaque, rows, span: float, height: float, top: str,
          note: str = "") -> None:
    """A labelled bar chart along X, since the camera is out on Y."""
    biggest = max(value for _, value, _ in rows) or 1.0
    step = span / max(1, len(rows) - 1)
    for index, (label, value, colour) in enumerate(rows):
        x = span * 0.5 - index * step
        tall = height * (value / biggest)
        opaque.box((x, 0.0, tall * 0.5 + 0.2), (1.9, 1.0, max(0.05, tall)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, tall + 0.95]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, height + 2.4]), top, (111, 235, 155)))
    if note:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, -1.2]), note, (169, 188, 203)))


def scene_kick_bom(app, opaque, transparent, p: float) -> None:
    """Where every dollar of a pristine dome goes."""
    build = BUILDS[2]  # pressure treated, cowboy-hat laminate
    reveal = clamp(p * 1.35)
    palette = (CYAN, AMBER, GREEN, PURPLE, WHITE, MUTED, RED)
    entries = build.lines()
    rows = [(f"{label.split(' (')[0]}\n${value:,.0f}", value,
             palette[index % len(palette)])
            for index, (label, value) in enumerate(entries)
            if index / len(entries) <= reveal and value > 0.0]
    if not rows:
        rows = [("lumber", 1.0, CYAN)]
    _bars(app, opaque, rows, 15.0, 4.4,
          f"${build.total:,.0f}  -  EVERY PART, BOUGHT NEW",
          f"{build.floor_sqft:.0f} sq ft at ${build.per_sqft:.2f} "
          f"the square foot")


def scene_kick_ladder(app, opaque, transparent, p: float) -> None:
    """Four ways to build the same dome, cheapest first."""
    reveal = clamp(p * 1.3)
    palette = (GREEN, CYAN, AMBER, PURPLE)
    rows = [(f"{build.name}\n${build.total:,.0f}", build.total,
             palette[index % len(palette)])
            for index, build in enumerate(BUILDS)
            if index / len(BUILDS) <= reveal]
    if not rows:
        rows = [(BUILDS[0].name, 1.0, GREEN)]
    _bars(app, opaque, rows, 14.0, 4.2,
          "THE SAME DOME, FOUR WAYS",
          "bare and a hat on top, or pressure treated and glassed all over")


def scene_kick_hat(app, opaque, transparent, p: float) -> None:
    """The cowboy hat: laminate the top twenty, exactly half the shell."""
    faces = list(GEOMETRY.hemisphere_faces)
    order = sorted(range(len(faces)), key=lambda i: float(
        GEOMETRY.vertices[[int(v) for v in faces[i]]][:, 2].mean()))
    upper = set(order[20:])
    sweep = clamp(p * 1.5)
    for index, face in enumerate(faces):
        corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
        if index in upper:
            colour = ((0.30, 0.78, 0.95, 0.88) if sweep > 0.2
                      else (0.30, 0.34, 0.40, 0.35))
        else:
            colour = (0.42, 0.30, 0.26, 0.34)
        transparent.triangle(corners[0], corners[1], corners[2], colour,
                             normalize(corners.mean(axis=0)))
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * SCALE for i in edge)
        opaque.cylinder(a, b, 0.06, WHITE, 6)
    build = BUILDS[2]
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.0]),
                   "GLASS THE TOP TWENTY ONLY", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -1.3]),
                   f"exactly half the shell -- {build.glass_sqft:.0f} sq ft, "
                   f"{build.resin_gallons:.1f} gallons", (169, 188, 203)),
    ])


def scene_kick_flatrate(app, opaque, transparent, p: float) -> None:
    """Nine times the house. Identical parts list."""
    sizes = flat_rate_table()
    small, large = sizes[0], sizes[-1]
    grow = ease_in_out(clamp(p * 1.4))
    big_scale = 1.7 + 4.6 * grow
    _dome(opaque, transparent, 1.7, origin=(6.6, 0.0, 0.0), frame=AMBER)
    _dome(opaque, transparent, big_scale, origin=(-6.0, 0.0, 0.0), frame=CYAN)
    ratio = large.floor_area_sqft / small.floor_area_sqft
    app.world_labels.extend([
        WorldLabel(np.array([6.6, 0.0, 2.7]),
                   f"{small.diameter_ft:.0f} ft\n"
                   f"{small.floor_area_sqft:.0f} sq ft", (255, 177, 62)),
        WorldLabel(np.array([-6.0, 0.0, big_scale + 1.4]),
                   f"{large.diameter_ft:.0f} ft\n"
                   f"{large.floor_area_sqft:.0f} sq ft", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 9.4]),
                   f"{ratio:.0f} TIMES THE HOUSE", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   f"both: {large.struts} struts, {large.brackets} brackets, "
                   f"{large.screws} screws, {large.processes} operations",
                   (111, 235, 155)),
    ])


# ----------------------------------------------------------------------
# Act three: the ask
# ----------------------------------------------------------------------

def scene_kick_factory(app, opaque, transparent, p: float) -> None:
    """What a hundred thousand dollars actually buys."""
    reveal = clamp(p * 1.25)
    items = STARTUP.EQUIPMENT
    biggest = max(value for _, value in items)
    span = 20.0
    step = span / (len(items) - 1)
    palette = (CYAN, AMBER, GREEN, PURPLE, RED, WHITE, CYAN, AMBER, GREEN)
    for index, (label, value) in enumerate(items):
        if index / len(items) > reveal:
            continue
        x = span * 0.5 - index * step
        tall = 4.0 * (value / biggest)
        colour = palette[index % len(palette)]
        opaque.box((x, 0.0, tall * 0.5 + 0.2), (1.5, 1.0, max(0.05, tall)),
                   colour)
        # Nine labels along one line collide -- "Table saw" lost its w to
        # "Compressor" the first time. Lifting every other one clears the
        # neighbour without moving the bar it belongs to.
        lift = 0.9 + (1.5 if index % 2 else 0.0)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, tall + lift]),
            f"{label.split(',')[0]}\n${value / 1000:.0f}k", _rgb(colour)))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.6]),
                   f"${STARTUP.equipment_total:,.0f} OF EQUIPMENT",
                   (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.3]),
                   f"${STARTUP.working_capital:,.0f} left over -- materials "
                   f"for {STARTUP.units_fundable(BUILDS[1]):.1f} domes",
                   (111, 235, 155)),
    ])


def scene_kick_ask(app, opaque, transparent, p: float) -> None:
    """The number, said plainly, with the dome behind it.

    The frame completes in the first third: a half-drawn dome under a
    funding ask reads as an unfinished promise, which is the one thing
    this chapter cannot afford to look like.
    """
    spin = ease_in_out(clamp(p * 3.0))
    _dome(opaque, transparent, SCALE * 0.92, phase=spin, frame=GREEN,
          skin=(0.24, 0.72, 0.46, 0.24))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.2]),
                   f"${STARTUP.capital:,.0f}", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   "a truck, a lift, a mill, and a shop with the lights on",
                   (169, 188, 203)),
    ])


SCENES = dict(HYPE_SCENES)
SCENES.update(FRANKEN_SCENES)
SCENES.update({
    "kick_title": scene_kick_title,
    "kick_problem": scene_kick_problem,
    "kick_versus": scene_kick_versus,
    "kick_wind": scene_kick_wind,
    "kick_triangle": scene_kick_triangle,
    "kick_bom": scene_kick_bom,
    "kick_ladder": scene_kick_ladder,
    "kick_hat": scene_kick_hat,
    "kick_flatrate": scene_kick_flatrate,
    "kick_factory": scene_kick_factory,
    "kick_ask": scene_kick_ask,
})


# ----------------------------------------------------------------------
# The script
#
# Side-on cameras (yaw 90) wherever two things are compared: the camera
# sits out on +Y, so a row laid along X only reads as a row from there.
# ----------------------------------------------------------------------

_SURFACE = advantages()[0]
_WIND = advantages()[3]
_CHEAP, _BUDGET, _PRISTINE, _FULL = BUILDS
_SMALL, _LARGE = flat_rate_table()[0], flat_rate_table()[-1]


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "title", "01", "A house that costs what its parts cost",
        "One hundred and twenty sticks and a weekend crew.",
        (
            "A house costs what somebody says it costs.",
            "This one costs what its parts cost, and you can count the parts.",
            "One hundred and twenty sticks. Forty triangles. Nine operations,",
            "repeated. That is the whole building.",
        ),
        (), 6.5, (34.0, 20.0, 17.0), "kick_title",
    ),
    Chapter(
        "problem", "02", "The shape everyone builds",
        f"{BOX.envelope_sqft:.0f} square feet of skin for "
        f"{BOX.footprint_sqft:.0f} of floor.",
        (
            "Start with the shape everybody already builds. Four walls, a roof,",
            "and corners. Give it three hundred and fourteen square feet of floor",
            f"and you have to build, wrap, seal and heat {BOX.envelope_sqft:.0f} square",
            "feet of outside. Every one of them costs money twice. Once to put up,",
            "and again every winter for as long as you live there.",
        ),
        (), 8.0, (54.0, 16.0, 21.0), "kick_problem",
    ),
    Chapter(
        "versus", "03", "Same floor, less building",
        f"{_SURFACE.percent_better:.0f}% less exterior, for the same floor.",
        (
            "Now put a dome next to it with exactly the same floor.",
            f"The house needs {BOX.envelope_sqft:.0f} square feet of skin.",
            f"The dome needs {DOME.envelope_sqft:.0f}.",
            f"That is {_SURFACE.percent_better:.0f} percent less to build, less to seal,",
            "less to paint, and less to heat, forever, for the same room to stand in.",
            "Nobody invented that. It is just what the shape does.",
        ),
        (), 9.5, (90.0, 12.0, 27.0), "kick_versus",
    ),
    Chapter(
        "triangle", "04", "Why it stands up",
        "A triangle cannot change shape without breaking.",
        (
            "Here is why it holds. Push on a square and it leans. The corners hinge,",
            "and every rectangular building on earth needs bracing to stop it.",
            "Push on a triangle and nothing happens. To change its shape you have to",
            "change the length of a side, which means breaking something.",
            "A dome is forty triangles. There is nothing left to brace.",
        ),
        (), 8.5, (90.0, 10.0, 24.0), "kick_triangle",
    ),
    Chapter(
        "wind", "05", "Nothing for the wind to push on",
        f"Drag {_WIND.dome:.2f} against {_WIND.other:.2f} for a box.",
        (
            "Wind is the same story. A flat wall catches everything thrown at it.",
            f"A box has a drag coefficient of about {_WIND.other:.2f}. A dome, about",
            f"{_WIND.dome:.2f}. Roughly {_WIND.percent_better:.0f} percent less load out of the",
            "shape alone, before you have bolted anything down. The wind arrives,",
            "finds nothing square to lean on, and goes over the top.",
        ),
        (), 8.0, (68.0, 14.0, 20.0), "kick_wind",
    ),
    Chapter(
        "flatrate", "06", "Nine times the house, same parts list",
        f"{_SMALL.floor_area_sqft:.0f} sq ft or {_LARGE.floor_area_sqft:.0f}: "
        f"{_LARGE.struts} struts either way.",
        (
            "And here is the part that makes it a business instead of a hobby.",
            f"A {_SMALL.diameter_ft:.0f} foot dome has {_SMALL.floor_area_sqft:.0f} square feet of floor.",
            f"A {_LARGE.diameter_ft:.0f} foot dome has {_LARGE.floor_area_sqft:.0f}. Nine times the house.",
            f"Both of them are {_LARGE.struts} struts, {_LARGE.brackets} brackets,",
            f"{_LARGE.screws} screws and {_LARGE.processes} operations. The sticks get longer.",
            "The parts list does not change at all. Learn to build one, and you have",
            "learned to build every size of it.",
        ),
        (), 9.5, (90.0, 12.0, 25.0), "kick_flatrate",
    ),
    Chapter(
        "proof", "07", "One already exists",
        "Four trees, ten days, half a year standing.",
        (
            "This is not a rendering of an idea. One of these is already standing",
            "in a yard. Four trees, cut and milled by hand. Ten days of work.",
            "A hundred and twenty brackets bent out of sheet metal on a bench,",
            "because buying them was not an option. It has been up through half",
            "a year of weather and it has not moved.",
        ),
        (), 8.5, (46.0, 16.0, 19.0), "fk_trees",
    ),
    Chapter(
        "brackets", "08", "Made, not bought",
        "A flat band, eight holes, folded once.",
        (
            "Every joint is a strip of flat steel with eight holes in it, folded",
            "once down the middle into a V. Four holes each side, four screws into",
            "each strut. Washing machine gauge.",
            "That is the entire connector, and it is why the frame does not need",
            "a machine shop, a supplier, or permission from anyone to exist.",
        ),
        (), 7.5, (58.0, 18.0, 16.0), "fk_bracket_fitted",
    ),
    Chapter(
        "hat", "09", "Glass the top, skip the bottom",
        "The lowest twenty triangles are exactly half the shell.",
        (
            "Waterproofing is where the money goes, so here is the trick.",
            "Sort the forty triangles by height and the bottom twenty come to",
            "exactly half the surface. Exactly. That is a property of the shape,",
            "not a rounding. So glass the top twenty like a hat and leave the",
            f"bottom ring to the siding. {_PRISTINE.glass_sqft:.0f} square feet instead of",
            f"{_FULL.glass_sqft:.0f}. Half the resin, and resin is the expensive part.",
        ),
        (), 9.0, (40.0, 22.0, 17.0), "kick_hat",
    ),
    Chapter(
        "bom", "10", "Every part, bought new",
        f"${_PRISTINE.total:,.0f} at the till, nothing salvaged.",
        (
            "So price it honestly. Nothing free, nothing salvaged, nothing",
            "harvested. Pressure treated lumber off the rack. Sheathing, foam,",
            "epoxy, cloth, screws, and a basic kitchen and bathroom.",
            f"It comes to {_PRISTINE.total:,.0f} dollars. Three hundred and fourteen square",
            f"feet of floor at {_PRISTINE.per_sqft:.0f} dollars a square foot, finished.",
        ),
        (), 9.0, (90.0, 12.0, 26.0), "kick_bom",
    ),
    Chapter(
        "ladder", "11", "Four ways to build the same dome",
        f"${_CHEAP.total:,.0f} bare, ${_FULL.total:,.0f} with everything.",
        (
            "And that is the middle of the range. Bare frame, no foam, a hat on",
            f"top: {_CHEAP.total:,.0f} dollars. Pressure treated everywhere and glassed",
            f"all over: {_FULL.total:,.0f}. The same building, four ways, and the",
            "cheapest of them is under the price of a used car.",
            "Cut your own timber and the largest line on the sheet goes to zero.",
        ),
        (), 8.5, (90.0, 12.0, 25.0), "kick_ladder",
    ),
    Chapter(
        "lines", "12", "One skeleton, four products",
        "Home, shed, greenhouse, storm shelter.",
        (
            "One skeleton is already four products. A home. A storage shed.",
            "A greenhouse. A storm shelter you could put in a back yard.",
            "Four price points, four markets, and the same forty triangles",
            "underneath every one of them.",
        ),
        (), 7.5, (90.0, 14.0, 24.0), "hype_lines",
    ),
    Chapter(
        "themes", "13", "The bones do not care",
        "Any skin you like, on the same frame.",
        (
            "The bones do not care what you put on them. A baseball. A basketball.",
            "A disco ball with a facet on every panel. Forty flat faces, all of them",
            "replaceable, all of them pointing somewhere.",
            "It is a house that can also be a sign, a venue, or a greenhouse,",
            "without changing a single stick underneath.",
        ),
        (), 8.0, (34.0, 22.0, 17.0), "kick_themes",
    ),
    Chapter(
        "factory", "14", "What the money buys",
        f"${STARTUP.equipment_total:,.0f} of equipment, and the rest is material.",
        (
            "Which brings me to the ask, and I will be specific about it,",
            "because vague asks deserve to fail.",
            "A used flatbed. A trailer. A used telehandler, because a dome goes up",
            "in panels and panels are heavy. A portable sawmill, so the timber line",
            "on that cost sheet really does go to zero. Saws, jigs, a compressor,",
            "laminating gear and extraction. Six months of rent with the lights on,",
            "and the paperwork that makes it a company instead of a yard.",
        ),
        (), 11.0, (90.0, 12.0, 31.0), "kick_factory",
    ),
    Chapter(
        "ask", "15", "One hundred thousand dollars",
        f"${STARTUP.equipment_total:,.0f} of it is equipment. "
        f"${STARTUP.working_capital:,.0f} is the first domes.",
        (
            "One hundred thousand dollars.",
            f"{STARTUP.equipment_total / 1000:.0f} thousand of that is equipment that",
            "still exists on day three hundred, and the rest is material for the",
            "first units, so the thing can start paying for itself.",
            "I am not asking anyone to believe a projection. One is already built",
            "and standing. I am asking for the tools to build the next one faster",
            "than by hand, and the one after that faster than that.",
        ),
        (), 10.0, (34.0, 20.0, 17.0), "kick_ask",
    ),
)


def scene_kick_themes(app, opaque, transparent, p: float) -> None:
    """Themed skins, borrowed from the montage."""
    HYPE_SCENES["hype_themes"](app, opaque, transparent, p)


SCENES["kick_themes"] = scene_kick_themes


_KICKSTARTER_BASE = Lesson(
    key="kick",
    brand="DOMESIM",
    title="Build A Dome: The Campaign",
    chapters=CHAPTERS,
    scenes=SCENES,
    snapshot_prefix="kick",
    style="hype",
    voice_rate="+6%",
    label_layout="declutter",
)

KICKSTARTER_LESSON = compose(
    _KICKSTARTER_BASE,
    include=("whoami",),
    exclude=("cta_share", "party"),
)


def validate_kickstarter() -> None:
    """No claim on screen that the modules underneath cannot prove."""
    from .dome_advantage import validate_advantage
    from .dome_costing import validate_costing
    from .render_kit import TriangleBatch

    validate_advantage()
    validate_costing()

    lesson = KICKSTARTER_LESSON
    assert lesson.chapters, "no chapters"
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"

    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        assert chapter.duration > 0.0, chapter.slug
        assert chapter.title and chapter.promise, chapter.slug
        for line in chapter.narration:
            assert line.strip(), chapter.slug

    # Every painter is a pure function of progress and gets both ends of
    # the range, so both ends have to survive being drawn.
    class _App:
        def __init__(self):
            self.world_labels = []

    for chapter in lesson.chapters:
        painter = lesson.scenes[chapter.stage]
        for progress in (0.0, 0.5, 1.0):
            app = _App()
            painter(app, TriangleBatch(), TriangleBatch(), progress)
            for label in app.world_labels:
                assert label.text.strip(), (chapter.stage, progress)
