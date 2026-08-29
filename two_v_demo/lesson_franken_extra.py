"""Hubless strut coding, the floor deck, and the commercial case.

Added to the franken-dome lesson.  The strut-coding scenes are the point:
a hubless frame is 120 sticks rather than 65, and in a franken-dome every
one of them is whatever section came off the log, so the only way to see
what is going on is to colour them by type and put a key on screen.
"""

from __future__ import annotations

import math

import numpy as np

from .franken_economics import (
    EXTERNAL_PRICES,
    BuildCost,
    Floor,
    flat_rate_table,
    glass_job,
)
from .geometry import build_demo_geometry, normalize
from .hubless_geometry import hubless_struts, hubless_summary
from .lessons import Chapter
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
    smoothstep,
)
from .strut_stock import STOCK_TYPES, draw_stock_strut, stock_for, tally
from .timber import CHAINSAW, draw_timber


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()
STRUTS = hubless_struts()
TALLY = tally()
SCALE = 5.2
RADIUS_IN = 120.0
COST = BuildCost(RADIUS_IN)


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _jitter(settle: float = 0.55) -> np.ndarray:
    rng = np.random.default_rng(7)
    raw = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.055
    return GEOMETRY.vertices + raw * (1.0 - settle * 0.72)


def _hubless_frame(batch, points, coded: bool, spread: float = 0.0,
                   radius: float = 0.085) -> None:
    """Draw all 120 struts: three per triangle, doubled on shared edges.

    ``spread`` pushes each triangle out along its own normal, which is
    what makes the doubling visible -- the two sticks on a shared edge
    separate and you can count them.
    """
    index = 0
    for face in GEOMETRY.hemisphere_faces:
        corners = points[[int(v) for v in face]] * SCALE
        offset = normalize(corners.mean(axis=0)) * spread
        for position in range(3):
            a = corners[position] + offset
            b = corners[(position + 1) % 3] + offset
            draw_stock_strut(batch, a, b, index, radius, coded)
            index += 1


# A horizontal key under the dome. A vertical column beside it kept
# projecting over the frame at every camera that showed the whole dome,
# and moving it further out only pushed it off frame instead.
def _legend(app, batch, p: float, z: float = -2.4, span: float = 16.0) -> None:
    """The colour key, laid out along X under the model."""
    reveal = clamp(p * 1.5)
    step = span / (len(STOCK_TYPES) - 1)
    for index, stock in enumerate(STOCK_TYPES):
        if index / len(STOCK_TYPES) > reveal:
            continue
        x = -span * 0.5 + index * step
        batch.box((x, 0.0, z), (1.5, 0.5, 0.75), stock.colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z - 1.15]),
            f"{stock.glyph} {stock.fraction}" + chr(10) + f"x{TALLY.counts[stock.key]}",
            stock.rgb))


def scene_fk_hubless(app, opaque, transparent, p: float) -> None:
    """120 struts, colour-coded, with the triangles drifting apart."""
    spread = ease_in_out(clamp((p - 0.15) / 0.7)) * 1.5
    points = _jitter()
    _hubless_frame(opaque, points, coded=True, spread=spread)
    _legend(app, opaque, p)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.4]),
                   f"{SUMMARY.triangles} TRIANGLES x 3 = "
                   f"{SUMMARY.struts} STRUTS", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   f"{SUMMARY.doubled_edges} shared edges carry two sticks; "
                   f"{SUMMARY.rim_edges} rim edges carry one",
                   (169, 188, 203)),
    ])


def scene_fk_doubling(app, opaque, transparent, p: float) -> None:
    """One shared edge, opened up, so the doubling is countable."""
    fold = ease_in_out(clamp((p - 0.12) / 0.7))
    spine_a = np.array([0.0, -3.0, 2.4])
    spine_b = np.array([0.0, 3.0, 2.4])
    for side, index in ((-1.0, 4), (1.0, 17)):
        stock = stock_for(index)
        gap = 0.22 * side * (0.35 + fold)
        offset = np.array([gap, 0.0, 0.0])
        draw_stock_strut(opaque, spine_a + offset, spine_b + offset,
                         index, 0.17, True)
        half = math.radians(24.0) * fold
        direction = np.array([side * math.cos(half), 0.0, -math.sin(half)])
        far_a = spine_a + offset + direction * 3.4
        far_b = spine_b + offset + direction * 3.4
        for a, b, seed in ((spine_a + offset, far_a, index + 40),
                           (spine_b + offset, far_b, index + 41),
                           (far_a, far_b, index + 42)):
            draw_stock_strut(opaque, a, b, seed, 0.10, True)
        normal = normalize(np.cross(spine_b - spine_a, direction))
        transparent.triangle(spine_a + offset, spine_b + offset, far_b,
                             (stock.colour[0], stock.colour[1],
                              stock.colour[2], 0.16), normal)
        transparent.triangle(spine_a + offset, far_b, far_a,
                             (stock.colour[0], stock.colour[1],
                              stock.colour[2], 0.16), normal)
        app.world_labels.append(WorldLabel(
            far_a + np.array([0.0, -1.4, 0.9]),
            f"{stock.glyph}  {stock.label}", stock.rgb))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.2]),
                   "ONE EDGE, TWO STICKS", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   f"2 x {SUMMARY.doubled_edges} + {SUMMARY.rim_edges} "
                   f"= {SUMMARY.strut_check}", (111, 235, 155)),
    ])


def scene_fk_stockpile(app, opaque, transparent, p: float) -> None:
    """One log becoming eight sticks, which is where the sections come from."""
    reveal = clamp(p * 1.3)
    span = 13.6
    step = span / (len(STOCK_TYPES) - 1)
    for index, stock in enumerate(STOCK_TYPES):
        if index / len(STOCK_TYPES) > reveal:
            continue
        x = -span * 0.5 + index * step
        opaque.cylinder(np.array([x, 0.0, 0.8]), np.array([x, 0.0, 4.6]),
                        0.44 * stock.radius_scale, stock.colour, stock.sides)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 5.5]),
            f"{stock.glyph}\n{stock.fraction}\nx{TALLY.counts[stock.key]}",
            stock.rgb))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 7.2]),
                   f"{SUMMARY.struts} STRUTS FROM "
                   f"{TALLY.logs_needed():.0f} LOGS", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.8]),
                   "one log rips into two halves, four quarters or eight eighths",
                   (169, 188, 203)),
    ])


def scene_fk_floor(app, opaque, transparent, p: float) -> None:
    """A round deck on blocks, with the dome standing on it."""
    build = ease_in_out(clamp(p * 1.25))
    floor = COST.floor
    view = SCALE / (floor.radius_in / 12.0)
    radius = SCALE

    # Piers first: the deck sits on them, not on the ground.
    for ring in range(floor.block_ring_count):
        count = 6 * (ring + 1)
        ring_radius = radius * (ring + 1) / (floor.block_ring_count + 0.4)
        for index in range(count):
            angle = math.tau * index / count
            centre = np.array([ring_radius * math.cos(angle),
                               ring_radius * math.sin(angle), 0.30])
            opaque.box(tuple(centre), (0.42, 0.42, 0.60),
                       (0.42, 0.44, 0.47, 1.0))
    opaque.box((0.0, 0.0, 0.30), (0.42, 0.42, 0.60), (0.42, 0.44, 0.47, 1.0))

    # Joists across the circle, then the deck over them.
    spacing = floor.joist_spacing_in / 12.0 * view
    count = int(build * floor.joists)
    for index in range(count):
        offset = (index + 1) * spacing - radius
        half = math.sqrt(max(0.0, radius ** 2 - offset ** 2))
        draw_timber(opaque, np.array([-half, offset, 0.78]),
                    np.array([half, offset, 0.78]), 0.09, index * 3 + 5,
                    CHAINSAW, sides=4)
    if build > 0.75:
        segments = 44
        for index in range(segments):
            a = math.tau * index / segments
            b = math.tau * (index + 1) / segments
            corner_a = np.array([radius * math.cos(a), radius * math.sin(a), 0.95])
            corner_b = np.array([radius * math.cos(b), radius * math.sin(b), 0.95])
            transparent.triangle(np.array([0.0, 0.0, 0.95]), corner_a, corner_b,
                                 (0.62, 0.50, 0.34, 0.55),
                                 np.array([0.0, 0.0, 1.0]))

    if build > 0.55:
        points = _jitter()
        lift = np.array([0.0, 0.0, 0.98])
        index = 0
        for face in GEOMETRY.hemisphere_faces:
            corners = points[[int(v) for v in face]] * SCALE + lift
            for position in range(3):
                draw_stock_strut(opaque, corners[position],
                                 corners[(position + 1) % 3], index, 0.075,
                                 False)
                index += 1

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 2.2]),
                   f"{floor.area_sqft:.0f} SQ FT DECK", (61, 211, 255)),
        WorldLabel(np.array([0.0, -radius - 1.4, 0.4]),
                   f"{floor.joists} joists, {floor.joist_feet:.0f} ft, "
                   f"on {floor.blocks} blocks", (169, 188, 203)),
    ])


def scene_fk_flatrate(app, opaque, transparent, p: float) -> None:
    """The whole commercial argument in one picture."""
    reveal = clamp(p * 1.3)
    sizes = flat_rate_table()
    biggest = max(item.floor_area_sqft for item in sizes)
    span = 13.4
    step = span / (len(sizes) - 1)
    for index, size in enumerate(sizes):
        if index / len(sizes) > reveal:
            continue
        x = -span * 0.5 + index * step
        # Floor area grows; the parts count does not.
        height = 4.4 * (size.floor_area_sqft / biggest)
        opaque.box((x, 1.1, height * 0.5 + 0.15), (2.2, 0.9, max(0.05, height)),
                   CYAN)
        opaque.box((x, -1.1, 1.15), (2.2, 0.9, 2.2), AMBER)
        app.world_labels.extend([
            WorldLabel(np.array([x, 1.1, height + 0.85]),
                       f"{size.floor_area_sqft:.0f} sq ft", (61, 211, 255)),
            WorldLabel(np.array([x, -1.1, 2.7]),
                       f"{size.struts} struts\n{size.screws} screws",
                       (255, 177, 62)),
            WorldLabel(np.array([x, 0.0, -0.9]),
                       f"{size.diameter_ft:.0f} ft", (169, 188, 203)),
        ])
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.4]),
        "FLOOR AREA GROWS.  THE PARTS LIST DOES NOT.", (111, 235, 155)))


def scene_fk_glass(app, opaque, transparent, p: float) -> None:
    """What has to be laminated, by area."""
    reveal = clamp(p * 1.3)
    glass = glass_job(RADIUS_IN)
    rows = (("SHELL", glass.shell_sqft, CYAN),
            ("FLOOR UNDERSIDE", glass.floor_under_sqft, AMBER),
            ("UTILITY TOWER", glass.tower_sqft, GREEN))
    biggest = max(value for _, value, _ in rows)
    span = 10.0
    step = span / (len(rows) - 1)
    for index, (label, value, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.2 * (value / biggest)
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.4, 1.0, max(0.05, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.9]),
            f"{label}\n{value:.0f} sq ft", _rgb(colour)))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.2]),
                   f"{glass.total_sqft:.0f} SQ FT TO LAMINATE",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   f"{glass.resin_gallons:.0f} gal resin, "
                   f"{glass.cloth_sqyd:.0f} sq yd cloth, "
                   f"{glass.csm_sqyd:.0f} sq yd mat", (169, 188, 203)),
    ])


def scene_fk_cost(app, opaque, transparent, p: float) -> None:
    """Where the money actually went."""
    reveal = clamp(p * 1.3)
    glass = COST.glass
    rows = (("TIMBER", 0.0, GREEN), ("BRACKETS", 0.0, GREEN),
            ("SCREWS", COST.screw_cost, AMBER),
            ("FIBREGLASS", glass.total_cost, RED))
    biggest = max(value for _, value, _ in rows) or 1.0
    span = 12.4
    step = span / (len(rows) - 1)
    for index, (label, value, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.4 * (value / biggest)
        opaque.box((x, 0.0, max(0.06, height) * 0.5 + 0.15),
                   (2.1, 1.0, max(0.06, height)), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, max(0.3, height) + 0.9]),
            f"{label}\n${value:,.0f}", _rgb(colour)))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.2]),
                   f"TOTAL ${COST.total:,.0f}  =  "
                   f"${COST.cost_per_sqft:,.2f} / SQ FT", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "the wood was free because I cut it down myself",
                   (169, 188, 203)),
    ])


EXTRA_SCENES = {
    "fk_hubless": scene_fk_hubless,
    "fk_doubling": scene_fk_doubling,
    "fk_stockpile": scene_fk_stockpile,
    "fk_floor": scene_fk_floor,
    "fk_flatrate": scene_fk_flatrate,
    "fk_glass": scene_fk_glass,
    "fk_cost": scene_fk_cost,
}


def extra_equations(app, stage: str) -> list[str]:
    if stage in ("fk_hubless", "fk_doubling"):
        return [
            f"{stock.glyph} {stock.label:<17} x{TALLY.counts[stock.key]}"
            for stock in STOCK_TYPES
        ]
    if stage == "fk_stockpile":
        return [
            f"struts = {SUMMARY.struts}",
            f"logs   = {TALLY.logs_needed():.0f}",
        ]
    if stage == "fk_floor":
        floor = COST.floor
        return [
            f"deck    = {floor.area_sqft:.0f} sq ft",
            f"joists  = {floor.joists} at {floor.joist_spacing_in:.0f} in",
            f"length  = {floor.joist_feet:.0f} ft",
            f"blocks  = {floor.blocks}",
        ]
    if stage == "fk_flatrate":
        return [
            f"{size.diameter_ft:>4.0f} ft  {size.floor_area_sqft:>5.0f} sq ft  "
            f"{size.struts} struts  {size.screws} screws"
            for size in flat_rate_table()
        ]
    if stage in ("fk_glass", "fk_cost"):
        glass = COST.glass
        return [
            f"area   = {glass.total_sqft:.0f} sq ft",
            f"resin  = {glass.resin_gallons:.1f} gal  ${glass.resin_cost:,.0f}",
            f"cloth  = {glass.cloth_sqyd:.0f} sq yd  ${glass.cloth_cost:,.0f}",
            f"mat    = {glass.csm_sqyd:.0f} sq yd  ${glass.csm_cost:,.0f}",
            f"screws = ${COST.screw_cost:,.0f}",
            f"TOTAL  = ${COST.total:,.0f}",
        ]
    return []


EXTRA_CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "hubless", "00", "One hundred and twenty sticks",
        "Forty triangles, three sticks each, and no hubs at all.",
        (
            "Here is the thing that makes a franken-dome buildable by one person with",
            "no jig and no precision. It is hubless. Every one of the forty triangles is",
            "a closed triangle carrying its own three sticks, so the frame is a hundred",
            "and twenty struts rather than the sixty-five a hubbed dome needs. Fifty-five",
            "edges end up with two sticks lying against each other, ten rim edges carry",
            "one, and two times fifty-five plus ten is one hundred and twenty.",
        ),
        ("40 triangles x 3 = 120 struts", "55 shared edges x 2 sticks",
         "10 rim edges x 1 stick"),
        24.0, (90.0, 17.0, 26.0), "fk_hubless",
    ),
    Chapter(
        "doubling", "00", "Why the edges double",
        "Two triangles meet, and each brings its own stick.",
        (
            "Open one of those joints up and you can see it. Two triangles meet along an",
            "edge, and each of them arrives with its own complete stick, so the joint is",
            "a lap between two members rather than a point where several converge. That",
            "is the whole trick: nothing has to meet accurately at a point, because",
            "nothing meets at a point at all.",
        ),
        ("a lap, not a hub", "nothing converges, so nothing has to be accurate"),
        20.0, (90.0, 16.0, 17.0), "fk_doubling",
    ),
    Chapter(
        "stockpile", "00", "Six sections, one woodpile",
        "Full round, half, quarter, eighth, square, and salvaged steel.",
        (
            "And because nothing has to be accurate, the sticks do not have to match.",
            "The colour key is the section each one was cut to. Green is a full round log",
            "as it fell. Blue is a half, one rip down the middle. Red is a quarter and",
            "amber is an eighth, which is three rips and eight thin struts out of one",
            "log. Black is milled square stock and grey is salvaged steel, used only",
            "where wood would not serve. A hundred and twenty struts came out of about",
            "forty-six logs.",
        ),
        ("O full round  D half  L quarter", "< eighth  # square  T steel",
         "120 struts from about 46 logs"),
        26.0, (90.0, 15.0, 19.0), "fk_stockpile",
    ),
    Chapter(
        "floor", "00", "It stands on a deck, not on the ground",
        "A round deck matching the dome, sitting on blocks.",
        (
            "The dome does not sit on dirt. It sits on a round deck the same diameter as",
            "the dome, built first and levelled first, standing on blocks so air moves",
            "underneath it. Three hundred and fourteen square feet of floor, fourteen",
            "joists, two hundred and thirty-one feet of joist, on thirty-seven blocks.",
            "Get that deck round and level and the dome has something honest to land on;",
            "get it wrong and every triangle above it inherits the error.",
        ),
        ("314 sq ft deck", "14 joists, 231 ft", "37 blocks"),
        24.0, (40.0, 20.0, 19.0), "fk_floor",
    ),
    Chapter(
        "flatrate", "00", "Dome labour is a flat rate",
        "Floor area grows. The parts list does not.",
        (
            "Now the argument that makes this a business rather than a hobby. Take a ten",
            "foot dome and a thirty foot dome. The thirty is nine times the floor area.",
            "It is also exactly forty triangles, exactly a hundred and twenty struts,",
            "exactly a hundred and twenty brackets and exactly nine hundred and sixty",
            "screws, through exactly the same nine operations. Only the sticks get",
            "longer, and they grow linearly while the floor grows with the square.",
        ),
        ("10 ft: 79 sq ft, 120 struts", "30 ft: 707 sq ft, 120 struts",
         "9x the house, the same parts list"),
        26.0, (90.0, 15.0, 19.0), "fk_flatrate",
    ),
    Chapter(
        "optimise", "00", "Few processes, endlessly repeated",
        "Optimise nine operations and you have optimised every dome you will build.",
        (
            "That is a very strange property for a building, and it is worth sitting",
            "with. A conventional house is thousands of dissimilar operations, so",
            "improving any one of them barely moves the total. A dome is nine operations",
            "repeated a hundred and twenty times, so shaving ten seconds off one cut",
            "saves twenty minutes on every dome you will ever build. That is what makes",
            "a factory worth building around this shape rather than around a rectangle.",
        ),
        ("9 operations, repeated", "improve one, improve every dome"),
        24.0, (52.0, 22.0, 18.0), "fk_flatrate",
    ),
    Chapter(
        "glass", "00", "What actually has to be paid for",
        "A thousand square feet of laminating.",
        (
            "So what does one of these really cost? Everything structural was free. The",
            "cost is the skin. Six hundred and twenty-eight square feet of shell, three",
            "hundred and fourteen underneath the floor, and another hundred and",
            "seventeen for the utility tower, which comes to about a thousand and sixty",
            "square feet to laminate. At two layers and fifteen per cent waste that is",
            "sixty-one gallons of resin and a hundred and thirty-five square yards each",
            "of cloth and mat.",
        ),
        ("shell 628 + floor 314 + tower 117", "= 1059 sq ft to laminate",
         "61 gal resin, 135 sq yd each of cloth and mat"),
        26.0, (90.0, 16.0, 18.0), "fk_glass",
    ),
    Chapter(
        "cost", "00", "The bill",
        "Under five thousand dollars, and the wood was free.",
        (
            "The ledger, honestly. Timber: nothing, because I cut it down myself.",
            "Brackets: nothing, because I folded them out of a scrapped washing machine.",
            "Screws: forty-eight dollars. Fibreglass: about four thousand seven hundred.",
            "That is the whole structure for under five thousand dollars, which is",
            "roughly fifteen dollars a square foot of floor, and almost all of it is the",
            "one material I could not make myself.",
        ),
        ("timber $0, brackets $0", "screws $48", "fibreglass ~$4,700",
         "~$15 per sq ft of floor"),
        26.0, (90.0, 15.0, 19.0), "fk_cost",
    ),
)
