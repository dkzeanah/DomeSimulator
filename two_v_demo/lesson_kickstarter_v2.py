"""Campaign film, version two: the brim, the pony wall, and the ten points.

Version one argued that a dome is cheap to build.  This one argues it is
cheap to *live in*, which is the argument that actually sells a house.

Three things are new in the geometry:

**The brim.**  The hat has to overhang or rain runs straight down the
bottom ring and into the joints. Once it overhangs it is a gutter, so it
is drawn as a real projecting annulus with fins, not as a colour change
on the shell.

**The pony wall.**  A short stem wall under the shell, drawn with the
head-height line on screen so the gain in usable floor is visible rather
than asserted.

**The tank.**  Where the water off the brim goes.
"""

from __future__ import annotations

import math

import numpy as np

from .dome_advantage import FACT as ADV_FACT, advantages, box_envelope, dome_envelope
from .dome_costing import Startup, build_variants
from .dome_performance import (
    FACT,
    PonyWall,
    WaterCatch,
    assemblies,
    hat_rim_radius_ft,
    running_costs,
    sky_cooling,
    ten_points,
)
from .franken_economics import flat_rate_table
from .geometry import build_demo_geometry, normalize
from .lesson_kickstarter import SCENES as V1_SCENES, _box_house, _dome
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
DOME_RADIUS_FT = 10.0

BUILDS = build_variants()
STARTUP = Startup()
POINTS = ten_points()
DOME_RUN, BOX_RUN = running_costs()
PAINT = sky_cooling()
WATER = WaterCatch(1.5)
BARE_WALL, PONY = PonyWall(0.0), PonyWall(3.0)


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


# ----------------------------------------------------------------------
# Where the hat stops, in scene units
# ----------------------------------------------------------------------

def _hat_ring() -> tuple[float, float]:
    """Scene radius and height of the ring the hat ends on."""
    faces = list(GEOMETRY.hemisphere_faces)
    order = sorted(range(len(faces)), key=lambda i: float(
        GEOMETRY.vertices[[int(v) for v in faces[i]]][:, 2].mean()))
    upper = {int(v) for i in order[20:] for v in faces[i]}
    lower = {int(v) for i in order[:20] for v in faces[i]}
    shared = sorted(upper & lower,
                    key=lambda v: -float(math.hypot(*GEOMETRY.vertices[v][:2])))
    vertex = GEOMETRY.vertices[shared[0]]
    return (float(math.hypot(*vertex[:2])) * SCALE, float(vertex[2]) * SCALE)


HAT_RADIUS, HAT_HEIGHT = _hat_ring()

FT = SCALE / DOME_RADIUS_FT
"""Scene units per foot. Drawing the brim in scene units instead of feet
made it twice its real size and the dome looked like a flying saucer."""

BRIM = WATER.brim_ft * FT


def _brim(batch, overhang: float, drop: float = 0.28, segments: int = 40,
          colour=(0.72, 0.76, 0.82, 1.0), fins: bool = True) -> None:
    """The projecting brim: a real annulus that sticks out past the shell.

    Drawn as geometry rather than as a colour band on the shell, because
    the whole point is that it stands proud far enough to throw water
    clear of the bottom ring.
    """
    inner, outer = HAT_RADIUS, HAT_RADIUS + overhang
    for index in range(segments):
        a = math.tau * index / segments
        b = math.tau * (index + 1) / segments
        for sign in (1.0, -1.0):
            # Top and underside, wound so both survive culling.
            thickness = 0.07 * sign
            normal = np.array([0.0, 0.0, sign])
            p0 = np.array([inner * math.cos(a), inner * math.sin(a),
                           HAT_HEIGHT + thickness])
            p1 = np.array([inner * math.cos(b), inner * math.sin(b),
                           HAT_HEIGHT + thickness])
            p2 = np.array([outer * math.cos(b), outer * math.sin(b),
                           HAT_HEIGHT - drop + thickness])
            p3 = np.array([outer * math.cos(a), outer * math.sin(a),
                           HAT_HEIGHT - drop + thickness])
            corners = [p0, p1, p2, p3] if sign > 0 else [p3, p2, p1, p0]
            batch.quad(*corners, colour, normal)
        if fins and index % 4 == 0:
            # A rib every few segments, which is what stops a thin brim
            # flapping and is how it gets built anyway.
            root = np.array([inner * math.cos(a), inner * math.sin(a),
                             HAT_HEIGHT])
            tip = np.array([outer * math.cos(a), outer * math.sin(a),
                            HAT_HEIGHT - drop])
            batch.cylinder(root, tip, 0.07, (0.55, 0.58, 0.64, 1.0), 6)


def _pony_wall(batch, height: float, segments: int = 40,
               colour=(0.48, 0.40, 0.32, 1.0)) -> None:
    """A stem wall under the shell, lifting the whole dome."""
    radius = SCALE
    for index in range(segments):
        a = math.tau * index / segments
        b = math.tau * (index + 1) / segments
        p0 = np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
        p1 = np.array([radius * math.cos(b), radius * math.sin(b), 0.0])
        p2 = np.array([radius * math.cos(b), radius * math.sin(b), height])
        p3 = np.array([radius * math.cos(a), radius * math.sin(a), height])
        normal = normalize(np.array([math.cos((a + b) * 0.5),
                                     math.sin((a + b) * 0.5), 0.0]))
        batch.quad(p0, p1, p2, p3, colour, normal)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_kick_brim(app, opaque, transparent, p: float) -> None:
    """The hat, with the overhang that keeps rain off the bottom ring."""
    faces = list(GEOMETRY.hemisphere_faces)
    order = sorted(range(len(faces)), key=lambda i: float(
        GEOMETRY.vertices[[int(v) for v in faces[i]]][:, 2].mean()))
    upper = set(order[20:])
    for index, face in enumerate(faces):
        corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
        colour = ((0.30, 0.78, 0.95, 0.88) if index in upper
                  else (0.42, 0.30, 0.26, 0.40))
        transparent.triangle(corners[0], corners[1], corners[2], colour,
                             normalize(corners.mean(axis=0)))
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * SCALE for i in edge)
        opaque.cylinder(a, b, 0.06, WHITE, 6)

    grow = ease_in_out(clamp(p * 1.8))
    _brim(opaque, 0.06 * FT + (BRIM - 0.06 * FT) * grow)

    # Rain, falling past the brim rather than onto the bottom ring.
    for index in range(28):
        angle = math.tau * index / 28.0 + p * 2.0
        radius = (HAT_RADIUS + BRIM + 0.5) * (1.0 + 0.05 * math.sin(index * 2.0))
        fall = ((p * 2.4 + index * 0.13) % 1.0)
        z = HAT_HEIGHT + 3.4 - fall * 4.6
        opaque.box((radius * math.cos(angle), radius * math.sin(angle), z),
                   (0.07, 0.07, 0.42), (0.45, 0.72, 0.95, 0.85))

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.0]),
                   "THE HAT HAS TO OVERHANG", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   "throw the water clear of the bottom ring, "
                   "or it runs into every joint", (169, 188, 203)),
    ])


def scene_kick_water(app, opaque, transparent, p: float) -> None:
    """Once it overhangs, it is a gutter."""
    _dome(opaque, transparent, SCALE, phase=1.0, frame=CYAN,
          skin=(0.30, 0.62, 0.92, 0.20))
    _brim(opaque, BRIM)

    # A downpipe and a tank, screen left because the camera is out on +Y.
    pipe_x = HAT_RADIUS + BRIM * 0.9
    opaque.cylinder(np.array([pipe_x, 0.0, HAT_HEIGHT - 0.55]),
                    np.array([pipe_x, 0.0, 1.1]), 0.16,
                    (0.62, 0.66, 0.72, 1.0), 8)
    fill = clamp((p - 0.2) * 1.8)
    opaque.cylinder(np.array([pipe_x + 1.9, 0.0, 0.0]),
                    np.array([pipe_x + 1.9, 0.0, 2.6]), 1.15,
                    (0.24, 0.28, 0.34, 1.0), 16)
    if fill > 0.02:
        opaque.cylinder(np.array([pipe_x + 1.9, 0.0, 0.05]),
                        np.array([pipe_x + 1.9, 0.0, 0.05 + 2.4 * fill]),
                        1.05, (0.22, 0.55, 0.85, 1.0), 16)

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.0]),
                   f"{WATER.gallons_year:,.0f} GALLONS A YEAR",
                   (61, 211, 255)),
        WorldLabel(np.array([pipe_x + 1.9, 0.0, 3.6]),
                   f"{WATER.gallons_day:.0f} gal/day", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   f"{WATER.brim_ft*12:.0f} in of brim gives "
                   f"{WATER.catchment_sqft:.0f} sq ft of catchment at "
                   f"{FACT['rainfall_in_year']:.0f} in of rain",
                   (169, 188, 203)),
    ])


def scene_kick_pony(app, opaque, transparent, p: float) -> None:
    """A stem wall turns the wasted rim into room you can stand in."""
    lift = ease_in_out(clamp(p * 1.6)) * (PONY.height_ft / DOME_RADIUS_FT
                                          * SCALE)
    _pony_wall(opaque, lift + 0.02)

    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * SCALE + np.array([0.0, 0.0, lift])
                for i in edge)
        opaque.cylinder(a, b, 0.06, CYAN, 6)

    # The head-height line, and the floor it makes usable.
    head = FACT["headroom_ft"] / DOME_RADIUS_FT * SCALE
    opaque.box((0.0, 0.0, head), (SCALE * 2.2, 0.05, 0.035),
               (0.95, 0.72, 0.25, 0.9))
    wall = PonyWall(PONY.height_ft * clamp(p * 1.6))
    usable = wall.usable_radius_ft() / DOME_RADIUS_FT * SCALE
    opaque.disc(np.array([0.0, 0.0, 0.06]), max(0.05, usable),
                (0.24, 0.72, 0.46, 0.55), 40)

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + lift + 1.8]),
                   "A PONY WALL BUYS THE PERIMETER BACK", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, head + 0.7]),
                   "6 ft 8 in -- where floor becomes usable", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.6]),
                   f"{BARE_WALL.usable_sqft:.0f} sq ft usable becomes "
                   f"{PONY.usable_sqft:.0f} for "
                   f"${PONY.cost - BARE_WALL.cost:,.0f}  -- "
                   f"${PONY.cost_per_gained_sqft(BARE_WALL):.0f} a square foot",
                   (111, 235, 155)),
    ])


def scene_kick_energy(app, opaque, transparent, p: float) -> None:
    """What a year of heating and cooling costs, both shapes."""
    reveal = clamp(p * 1.4)
    rows = ((f"2V DOME\n${DOME_RUN.annual_cost:,.0f}/yr",
             DOME_RUN.annual_cost, CYAN),
            (f"SQUARE HOUSE\n${BOX_RUN.annual_cost:,.0f}/yr",
             BOX_RUN.annual_cost, RED))
    biggest = max(value for _, value, _ in rows)
    for index, (label, value, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = 4.6 - index * 9.2
        tall = 4.4 * (value / biggest)
        opaque.box((x, 0.0, tall * 0.5 + 0.2), (2.6, 1.2, max(0.05, tall)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, tall + 1.0]), label, _rgb(colour)))

    saving = BOX_RUN.annual_cost - DOME_RUN.annual_cost
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 7.2]),
                   f"${saving:,.0f} A YEAR, EVERY YEAR", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.4]),
                   f"{DOME_RUN.total_kwh:,.0f} kWh against "
                   f"{BOX_RUN.total_kwh:,.0f} at "
                   f"{FACT['power_price']*100:.0f} cents, same insulation, "
                   f"same climate", (169, 188, 203)),
    ])


def scene_kick_paint(app, opaque, transparent, p: float) -> None:
    """Radiative sky cooling: the roof stops being a heat source."""
    for face in GEOMETRY.hemisphere_faces:
        corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
        transparent.triangle(corners[0], corners[1], corners[2],
                             (0.97, 0.98, 1.0, 0.92),
                             normalize(corners.mean(axis=0)))
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * SCALE for i in edge)
        opaque.cylinder(a, b, 0.05, (0.80, 0.84, 0.90, 1.0), 6)

    # Sunlight arriving and bouncing straight back off.
    phase = (p * 1.7) % 1.0
    # Spread across the frame rather than bunched to one side, and low
    # enough to stay in shot under the labels.
    for index in range(13):
        x = -13.0 + index * 2.1
        for step in range(5):
            t = (step / 5.0 + phase) % 1.0
            opaque.box((x, -3.2, 8.2 - t * 3.2), (0.10, 0.10, 0.42),
                       (1.0, 0.86, 0.35, 0.9))
            # The same ray leaving again, having been reflected.
            opaque.box((x + 1.3 * t, -3.2, 5.0 + t * 3.2),
                       (0.10, 0.10, 0.42), (1.0, 0.94, 0.66, 0.55))

    # And heat leaving upward, through the window the atmosphere leaves open.
    for index in range(7):
        angle = math.tau * index / 7.0
        radius = 2.6
        rise = ((p * 1.3 + index * 0.14) % 1.0)
        opaque.box((radius * math.cos(angle), radius * math.sin(angle),
                    SCALE + 0.6 + rise * 3.6), (0.13, 0.13, 0.5),
                   (0.42, 0.86, 0.98, 0.85 * (1.0 - rise)))

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 3.3]),
                   "8-13 MICRONS: THE SKY IS TRANSPARENT THERE",
                   (134, 210, 255)),
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.5]),
                   f"{PAINT.solar_delta_f + PAINT.radiative_delta_f:.0f} F "
                   f"COOLER THAN A DARK ROOF", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   "the shell sits below air temperature in full sun, so the "
                   "roof stops adding heat and starts removing it",
                   (169, 188, 203)),
    ])


def scene_kick_points(app, opaque, transparent, p: float) -> None:
    """The ten points, three at a time, over the shell."""
    _dome(opaque, transparent, SCALE * 0.78, phase=1.0, frame=MUTED,
          skin=(0.22, 0.42, 0.62, 0.16))
    group = min(3, int(clamp(p * 0.999) * 4))
    shown = POINTS[group * 3:group * 3 + 3] or POINTS[-1:]
    for index, point in enumerate(shown):
        z = 6.4 - index * 2.5
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, z]),
            f"{point.number}.  {point.headline}\n{point.figure}",
            (111, 235, 155) if index % 2 == 0 else (134, 210, 255)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.6]),
        "ten reasons this shape, for cheap manufactured housing",
        (169, 188, 203)))


SCENES = dict(V1_SCENES)
SCENES.update({
    "kick_brim": scene_kick_brim,
    "kick_water": scene_kick_water,
    "kick_pony": scene_kick_pony,
    "kick_energy": scene_kick_energy,
    "kick_paint": scene_kick_paint,
    "kick_points": scene_kick_points,
})


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

_SURFACE = advantages()[0]
_WIND = advantages()[3]
_CHEAP, _BUDGET, _PRISTINE, _FULL = BUILDS
_SMALL, _LARGE = flat_rate_table()[0], flat_rate_table()[-1]
_BASIC, _FILLED = assemblies()
_ROUGH_PAINT = sky_cooling(assembly=_BASIC)
_ROUGH_DOME, _ROUGH_BOX = running_costs(_BASIC)
_BOX = box_envelope()
_DOME = dome_envelope()
_SAVING = BOX_RUN.annual_cost - DOME_RUN.annual_cost


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
        f"{_BOX.envelope_sqft:.0f} square feet of skin for "
        f"{_BOX.footprint_sqft:.0f} of floor.",
        (
            "Start with the shape everybody already builds. Four walls, a roof,",
            "and corners. Give it three hundred and fourteen square feet of floor",
            f"and you have to build, wrap, seal and heat {_BOX.envelope_sqft:.0f} square",
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
            f"The house needs {_BOX.envelope_sqft:.0f} square feet of skin.",
            f"The dome needs {_DOME.envelope_sqft:.0f}.",
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
            "shape alone, before you have bolted anything down.",
        ),
        (), 7.5, (68.0, 14.0, 20.0), "kick_wind",
    ),
    Chapter(
        "pony", "06", "The pony wall",
        f"{BARE_WALL.usable_sqft:.0f} usable square feet becomes "
        f"{PONY.usable_sqft:.0f}.",
        (
            "Now the honest complaint about domes, and the fix for it.",
            "A hemisphere has a beautiful volume and almost none of it is against",
            "the edge, where the ceiling comes down to meet the floor. Out of three",
            f"hundred and fourteen square feet you can only stand up in",
            f"{BARE_WALL.usable_sqft:.0f}. The rest is crawl space with a view.",
            f"So put the whole shell on a {PONY.height_ft:.0f} foot wall. The ceiling",
            f"profile lifts with it, and usable floor goes from {BARE_WALL.usable_sqft:.0f}",
            f"square feet to {PONY.usable_sqft:.0f}.",
            f"That costs about {PONY.cost - BARE_WALL.cost:,.0f} dollars, which works out",
            f"near {PONY.cost_per_gained_sqft(BARE_WALL):.0f} dollars a square foot.",
            "It is the cheapest room in the building, and it is the first thing",
            "I would build into every one of them.",
        ),
        (), 12.0, (74.0, 12.0, 22.0), "kick_pony",
    ),
    Chapter(
        "flatrate", "07", "Nine times the house, same parts list",
        f"{_SMALL.floor_area_sqft:.0f} sq ft or {_LARGE.floor_area_sqft:.0f}: "
        f"{_LARGE.struts} struts either way.",
        (
            "And here is the part that makes it a business instead of a hobby.",
            f"A {_SMALL.diameter_ft:.0f} foot dome has {_SMALL.floor_area_sqft:.0f} square feet of floor.",
            f"A {_LARGE.diameter_ft:.0f} foot dome has {_LARGE.floor_area_sqft:.0f}. Nine times the house.",
            f"Both of them are {_LARGE.struts} struts, {_LARGE.brackets} brackets and",
            f"{_LARGE.screws} screws. The sticks get longer. The parts list does not",
            "change at all.",
        ),
        (), 9.0, (90.0, 12.0, 25.0), "kick_flatrate",
    ),
    Chapter(
        "proof", "08", "One already exists",
        "Four trees, ten days, half a year standing.",
        (
            "This is not a rendering of an idea. One of these is already standing",
            "in a yard. Four trees, cut and milled by hand. Ten days of work.",
            "It has been up through half a year of weather and it has not moved.",
        ),
        (), 7.5, (46.0, 16.0, 19.0), "fk_trees",
    ),
    Chapter(
        "brackets", "09", "Made, not bought",
        "A flat band, eight holes, folded once.",
        (
            "Every joint is a strip of flat steel with eight holes in it, folded",
            "once down the middle into a V. Four holes each side, four screws into",
            "each strut. Washing machine gauge.",
            "That is the entire connector, and it is why the frame does not need a",
            "machine shop, a supplier, or permission from anyone to exist.",
        ),
        (), 8.5, (58.0, 18.0, 16.0), "fk_bracket_fitted",
    ),
    Chapter(
        "brim", "10", "The hat has to overhang",
        "Throw the water clear, or it runs into every joint.",
        (
            "The top of the dome gets laminated like a hat. But a hat that stops",
            "flush with the wall is useless, because the water just runs down the",
            "face and into every joint below it.",
            "So the brim stands proud, with ribs to keep it stiff, and it throws",
            "the rain clear of the bottom ring entirely.",
        ),
        (), 8.5, (40.0, 18.0, 18.0), "kick_brim",
    ),
    Chapter(
        "water", "11", "The brim is already a gutter",
        f"{WATER.gallons_year:,.0f} gallons a year into a tank.",
        (
            "And once it overhangs, it is a gutter. You have built the catchment",
            "whether you wanted one or not.",
            f"An eighteen inch brim gives {WATER.catchment_sqft:.0f} square feet of",
            f"catchment. On average rainfall that is {WATER.gallons_year:,.0f} gallons",
            f"a year, about {WATER.gallons_day:.0f} gallons a day, straight into a tank",
            "beside the door.",
            "One downpipe. No pump. The roof shape does the collecting.",
        ),
        (), 10.0, (66.0, 14.0, 22.0), "kick_water",
    ),
    Chapter(
        "hat", "12", "Glass the top, skip the bottom",
        "The lowest twenty triangles are exactly half the shell.",
        (
            "Waterproofing is where the money goes, so here is the trick.",
            "Sort the forty triangles by height and the bottom twenty come to",
            "exactly half the surface. Exactly. That is a property of the shape,",
            "not a rounding. So glass the top twenty and leave the bottom ring to",
            f"the siding. {_PRISTINE.glass_sqft:.0f} square feet instead of",
            f"{_FULL.glass_sqft:.0f}. Half the resin, and resin is the expensive part.",
        ),
        (), 9.0, (40.0, 22.0, 17.0), "kick_hat",
    ),
    Chapter(
        "bom", "13", "Every part, bought new",
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
        "energy", "14", "What it costs to run",
        f"${DOME_RUN.annual_cost:,.0f} a year to heat and cool.",
        (
            "Now the number nobody puts on a listing. What does it cost to run.",
            f"At {FACT['power_price']*100:.0f} cents a kilowatt hour, with the cavity",
            f"insulated, this dome takes about {DOME_RUN.annual_cost:,.0f} dollars a year",
            "to heat and cool. Not a month. A year.",
            f"The same floor in a square house costs {BOX_RUN.annual_cost:,.0f}, because",
            f"it has {_BOX.envelope_sqft - _DOME.envelope_sqft:.0f} more square feet of skin",
            "to lose heat through.",
            f"That is {_SAVING:,.0f} dollars a year you never spend, on a building that",
            "was already cheaper to put up.",
        ),
        (), 11.0, (90.0, 12.0, 24.0), "kick_energy",
    ),
    Chapter(
        "paint", "15", "A roof that refuses the sun",
        "Below air temperature, in full sun.",
        (
            "And you can do better than that, with paint.",
            "Radiative sky cooling paint reflects about ninety six percent of",
            "sunlight, and it is a strong emitter in the eight to thirteen micron",
            "band, which happens to be the window the atmosphere is transparent at.",
            "So the heat does not stop in the air. It goes to space.",
            f"The shell runs roughly {PAINT.solar_delta_f + PAINT.radiative_delta_f:.0f} degrees",
            "cooler than a dark one, and it sits below air temperature in full sun.",
            "The roof stops being a heat source and becomes a heat sink.",
            "I will be straight with you about the money: on a well insulated shell",
            f"that is only about {PAINT.annual_saving:.0f} dollars a year, because very",
            "little of that heat was getting in anyway. On a thin wall it is more",
            f"like {_ROUGH_PAINT.annual_saving:.0f}. You do it for the comfort, and for",
            "the air conditioner you do not have to buy.",
        ),
        (), 14.0, (34.0, 20.0, 17.0), "kick_paint",
    ),
    Chapter(
        "points", "16", "Ten reasons this shape",
        "For cheap, affordable, manufactured housing.",
        (
            "So here is the whole argument in ten lines.",
            "Less exterior for the same floor. A parts list that does not grow with",
            "the house. Nine operations, endlessly repeated. Rigid because of its",
            "shape, not its bracing. Almost nothing for wind to push on.",
            "It costs what the parts cost. A stem wall buys back the wasted rim for",
            "eight dollars a square foot. Less skin means less to heat.",
            "A painted roof that refuses the sun. And a brim that collects the rain",
            "it was already throwing clear.",
            "Ten things, and every one of them is a consequence of the shape.",
        ),
        (), 13.0, (34.0, 20.0, 18.0), "kick_points",
    ),
    Chapter(
        "ladder", "17", "Four ways to build the same dome",
        f"${_CHEAP.total:,.0f} bare, ${_FULL.total:,.0f} with everything.",
        (
            f"Bare frame, no foam, a hat on top: {_CHEAP.total:,.0f} dollars.",
            f"Pressure treated everywhere and glassed all over: {_FULL.total:,.0f}.",
            "The same building, four ways, and the cheapest of them is under the",
            "price of a used car.",
        ),
        (), 8.0, (90.0, 12.0, 25.0), "kick_ladder",
    ),
    Chapter(
        "factory", "18", "What the money buys",
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
        "ask", "19", "One hundred thousand dollars",
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


_KICK2_BASE = Lesson(
    key="kick2",
    brand="DOMESIM",
    title="Build A Dome: The Campaign, Version Two",
    chapters=CHAPTERS,
    scenes=SCENES,
    snapshot_prefix="kick2",
    style="hype",
    voice_rate="+6%",
    label_layout="declutter",
)

KICKSTARTER_V2_LESSON = compose(
    _KICK2_BASE,
    include=("whoami",),
    exclude=("cta_share", "party"),
)


def validate_kickstarter_v2() -> None:
    """No claim on screen the modules underneath cannot prove."""
    from .dome_performance import validate_performance
    from .render_kit import TriangleBatch

    validate_performance()

    lesson = KICKSTARTER_V2_LESSON
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"
    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration and chapter.duration > 0.0, chapter.slug
        for line in chapter.narration:
            assert line.strip(), chapter.slug

    # The brim must genuinely project past the shell, or the rain scene is
    # a lie and the catchment number has nothing behind it.
    assert HAT_RADIUS > 0.0 and HAT_HEIGHT > 0.0
    assert HAT_RADIUS < SCALE, (HAT_RADIUS, SCALE)
    # The drawn brim must be the brim the water model was costed on.
    assert math.isclose(BRIM / FT, WATER.brim_ft, rel_tol=1e-9), BRIM
    assert HAT_RADIUS + BRIM > SCALE, "the brim has to project past the shell"
    batch = TriangleBatch()
    _brim(batch, BRIM)
    assert batch.vertices, "the brim drew nothing"

    # The pony wall has to be visible geometry too.
    wall = TriangleBatch()
    _pony_wall(wall, 1.5)
    assert wall.vertices, "the pony wall drew nothing"

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

    # Every one of the ten points has to actually appear on screen across
    # the run of that scene, or the chapter is claiming more than it shows.
    seen = set()
    for step in range(24):
        app = _App()
        SCENES["kick_points"](app, TriangleBatch(), TriangleBatch(),
                              step / 23.0)
        for label in app.world_labels:
            for point in POINTS:
                if f"{point.number}.  {point.headline}" in label.text:
                    seen.add(point.number)
    assert seen == set(range(1, 11)), sorted(set(range(1, 11)) - seen)
