"""Why wedges: the argument for building a dome out of split logs.

The earlier wedge film, :mod:`two_v_demo.lesson_wedge`, shows *what* the method is.
This one argues *why* it is worth doing, and it argues in numbers rather than in
adjectives: how much more of a tree survives being split than being sawn, which
machines stop being necessary, how many hours it takes three different ways, who gets
paid what out of a shelf price, whether the stick is actually strong enough, why the
wedge is turned the way it is, why there is a key in every seam, and how one flat jig
turns all of it into forty identical panels.

Every figure comes from :mod:`two_v_demo.wedge_why_facts`, which in turn derives from
the live simulator through :mod:`two_v_demo.raw_wedge_bridge` and from
:mod:`two_v_demo.wedge_geometry`.  Nothing on screen is typed in by hand.

The drawing helpers come from :mod:`two_v_demo.lesson_wedge` on purpose.  A wedge here
must look like the wedge there, and re-implementing the prism would let the two films
drift apart in the one respect the audience would notice first.

One chapter says something unflattering.  A single split wedge is a weaker stick in
bending than a dressed two-by-four, and the film says so, on screen, with the number,
before it makes the narrower claim that actually holds.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from . import raw_wedge_bridge as bridge
from .geometry import normalize
from .lesson_franken import SCENES as FRANKEN_SCENES
from .lesson_wedge import (
    SCENES as WEDGE_SCENES,
    BARK,
    WOOD,
    WOOD_DARK,
    _disc_xz,
    _fade,
    _label,
    _panel_members,
    _shell,
    _wedge_prism,
    FOOT,
    PANELS,
    SCENE_RADIUS,
)
from .lessons import Chapter, Lesson, math_shift, prose
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    TriangleBatch,
    clamp,
    ease_in_out,
)
from .wedge_facts import (
    steps_dome as wf_steps_dome,
    steps_pinwheel as wf_steps_pinwheel,
    steps_sector as wf_steps_sector,
)
from .wedge_geometry import (
    DEFAULT_LOG as LOG,
    SECTOR_ANGLE_DEG,
    SECTORS_PER_LOG,
    build_plan,
    section_rows,
    tree_yield,
)
from .wedge_why_facts import (
    ALL_SCREENS,
    ASSUMED_CONSTANTS,
    DRESSED_STUD_IN,
    FULL_STUD_IN,
    MEASURED_CONSTANTS,
    MIDDLE_MEN,
    PROCESS_CHAIN,
    cut_rate_model,
    defect_model,
    dome_facts,
    earnings_model,
    machines_dropped,
    orientation_table,
    purchase_model,
    sector_at_diameter,
    wedge_value_model,
    sector_section,
    steps_assumptions,
    steps_close,
    steps_defects,
    steps_dihedral,
    steps_jig,
    steps_middlemen,
    steps_mills,
    steps_orientation,
    steps_overhead,
    steps_rate,
    steps_structure,
    steps_value,
    steps_yield,
    structure_model,
    validate_wedge_why_facts,
    wedge_why_report,
)


FACTS = dome_facts()
STRUCTURE = structure_model()
EARNINGS = earnings_model()
YIELD = tree_yield(LOG)
PLAN = build_plan()
MEASURED = {name: value for name, value, _u, _w in MEASURED_CONSTANTS}
ASSUMED = {name: value for name, value, _u, _w in ASSUMED_CONSTANTS}
RATE_MEASURED = MEASURED

# One scene inch per real inch would put a 72-inch member off the end of the world, so
# the drawings share the earlier film's scale: the shell is five units across.
LOG_RADIUS = FACTS["trunk_diameter_in"] * 0.5
SECTION_SCALE = 0.34            # scene units per real inch, for cross-section drawings
SAWDUST = (0.72, 0.63, 0.44, 1.0)
STEEL = (0.62, 0.66, 0.74, 1.0)
OFFCUT = (1.00, 0.46, 0.22, 1.0)


# ======================================================================
# Cross-sections, taken from the simulator rather than drawn by eye
# ======================================================================

def _sector_outline(orientation: str, scale: float) -> list[np.ndarray]:
    """The raw sector's cross-section, in scene units, in the XZ plane.

    Local panel-in becomes scene +X and local dome-out becomes scene +Z, so a picture
    of a cross-section is laid out the same way the simulator's own corner diagram
    lays it out.
    """
    section = sector_section(orientation)
    return [np.array([y * scale, 0.0, z * scale]) for y, z in section.points]


def _sector_outline_at(diameter_in: float, scale: float) -> list[np.ndarray]:
    """The raw sector at any trunk diameter, in scene units, in the XZ plane."""
    section = sector_at_diameter(diameter_in)
    return [np.array([y * scale, 0.0, z * scale]) for y, z in section.points]


def _extrude_outline(batch, outline, depth: float, colour, edge_colour=None) -> None:
    """Turn a closed XZ outline into a short prism pointing along +Y."""
    front = [point + np.array([0.0, -depth * 0.5, 0.0]) for point in outline]
    back = [point + np.array([0.0, depth * 0.5, 0.0]) for point in outline]
    centre = sum(outline) / len(outline)
    count = len(outline)
    for index in range(count):
        nxt = (index + 1) % count
        side = normalize(np.cross(back[index] - front[index],
                                  front[nxt] - front[index]))
        if float(np.dot(side, front[index] - centre)) < 0.0:
            side = -side
        batch.quad(front[index], back[index], back[nxt], front[nxt],
                   edge_colour or colour, side)
    for index in range(1, count - 1):
        batch.triangle(front[0], front[index], front[index + 1], colour,
                       np.array([0.0, -1.0, 0.0]))
        batch.triangle(back[0], back[index + 1], back[index], colour,
                       np.array([0.0, 1.0, 0.0]))


def _both_sides(batch, a, b, c, d, colour) -> None:
    """A quad visible from either side.

    The renderer culls back faces, so a single quad drawn for two panels that face
    opposite ways renders only one of them. Two windings costs four triangles and
    removes a whole class of "half the picture is missing" bug.
    """
    batch.quad(a, b, c, d, colour)
    batch.quad(d, c, b, a, colour)


def _rect_outline(width_in: float, depth_in: float, scale: float) -> list[np.ndarray]:
    half_w, half_d = width_in * 0.5 * scale, depth_in * 0.5 * scale
    return [
        np.array([-half_w, 0.0, -half_d]),
        np.array([half_w, 0.0, -half_d]),
        np.array([half_w, 0.0, half_d]),
        np.array([-half_w, 0.0, half_d]),
    ]


# Short enough to sit under a cell without colliding with its neighbour.
SHORT_READING = {
    "point_dome_in": "POINTS IN, AT THE CENTRE",
    "point_panel_in": "POINTS APART",
    "point_dome_out": "POINTS OUT, AT THE SKY",
    "point_panel_out": "POINTS TOGETHER",
}


def _representative_seam():
    """One interior seam whose fold is closest to the middle of the shell's range.

    Drawing the extreme seam would make the fold look like a special case; drawing the
    median one makes the picture the typical joint, and every number on it is that
    seam's own solved answer.
    """
    model = bridge.model()
    seams = [seam for seam in model.seams]
    middle = (FACTS["fold_min_deg"] + FACTS["fold_max_deg"]) * 0.5
    return min(seams, key=lambda seam: abs(seam.fold_angle_deg - middle))


# ======================================================================
# The scenes
# ======================================================================

def scene_ww_open(app, opaque, transparent, p: float) -> None:
    """The shell, and the stick it is made of, in the same frame."""
    _shell(opaque, clamp(0.2 + p * 1.6))
    length = 5.2
    start = np.array([-length * 0.5, -7.4, 1.1])
    _wedge_prism(opaque, start, start + np.array([length, 0.0, 0.0]),
                 np.array([0.0, 0.0, 1.0]), 0.62)
    _label(app, np.array([0.0, -7.4, 2.4]),
           "ONE SPLIT LOG, USED AS IT COMES OFF THE SAW", AMBER)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.9]),
           f"{FACTS['members']:.0f} OF THEM MAKE THE BUILDING", GREEN)
    if p > 0.55:
        _label(app, np.array([0.0, -7.4, -0.4]),
               "nothing between the tree and the wall\n"
               "except a chainsaw and a flat board", WHITE)


def scene_ww_round(app, opaque, transparent, p: float) -> None:
    """The round section, and the rectangle we normally force out of it.

    Both discs are the SAME section -- the first bucked section of the film's own log --
    at the same scale, packed the way :func:`two_by_four_packing` packs it.  Drawing the
    rectangles at any other scale would make the comparison a cartoon.
    """
    shift = math_shift(app)
    row = section_rows(LOG)[0]
    unit = 0.55                                   # scene units per real inch
    radius = row.top_diameter_in * 0.5 * unit
    reveal = clamp(p * 1.8)

    # Split radially: three saw passes, drawn as they are made.
    centre = np.array([shift + 3.6, 0.0, radius + 0.7])
    _disc_xz(opaque, centre, radius, _fade(BARK, 0.95))
    splits = int(FACTS["radial_splits"])
    made = int(round(clamp(p * 2.2) * splits * 0.5))
    for index in range(splits // 2):
        if index >= made:
            continue
        angle = math.radians(index * 360.0 / splits)
        direction = np.array([math.cos(angle), 0.0, math.sin(angle)])
        # Lifted toward the camera, which sits on +Y for these chapters. Drawn in
        # the disc's own plane it z-fights; drawn behind it, it simply vanishes.
        front = centre + np.array([0.0, 0.35, 0.0])
        opaque.cylinder(front - direction * radius, front + direction * radius,
                        0.08, SAWDUST, 8)
    _label(app, centre + np.array([0.0, 0.0, radius + 0.6]),
           f"SPLIT: {splits} SECTORS, {FACTS['sector_angle_deg']:.0f} DEG EACH", GREEN)
    if reveal > 0.7:
        _label(app, centre + np.array([0.0, 0.0, -radius - 0.6]),
               f"{YIELD.wedge_recovery * 100:.0f}% OF THE TREE KEPT", GREEN)

    # The same section, packed with rectangles, and everything left outside them.
    other = np.array([shift - 3.6, 0.0, radius + 0.7])
    _disc_xz(opaque, other, radius, _fade(BARK, 0.38))
    thickness = FULL_STUD_IN[0] * unit
    width = FULL_STUD_IN[1] * unit
    bottom = -radius
    drawn = 0
    total = max(1, row.two_by_four_count)
    for count in row.two_by_four_rows:
        top = bottom + thickness
        for index in range(count):
            drawn += 1
            if drawn / total > reveal:
                break
            x = -count * width * 0.5 + (index + 0.5) * width
            # Thin in Y: a deep box seen in perspective projects wider than the
            # circle it is supposed to fit inside, which reverses the whole point.
            opaque.box(other + np.array([x, 0.22, bottom + thickness * 0.5]),
                       np.array([width * 0.94, 0.3, thickness * 0.9]), SAWDUST)
        bottom = top
    _label(app, other + np.array([0.0, 0.0, radius + 0.6]),
           f"SAWN: {row.two_by_four_count} RECTANGLES INSIDE A CIRCLE", RED)
    if reveal > 0.7:
        _label(app, other + np.array([0.0, 0.0, -radius - 0.6]),
               f"{YIELD.two_by_four_recovery * 100:.0f}% OF THE TREE KEPT", RED)
    if p > 0.5:
        _label(app, np.array([shift, 0.0, -1.4]),
               "the corners of the log are not waste because they are bad wood.\n"
               "they are waste because they are not rectangular.", WHITE)


def scene_ww_chain(app, opaque, transparent, p: float) -> None:
    """The processing chain, with the machines the wedge path never buys fading out.

    The dropped machines stay in place and go translucent rather than dropping through
    the floor.  An earlier cut had them fall, which left their labels hanging over an
    empty grid: you could see that something had gone but not what.
    """
    shift = math_shift(app)
    spacing = 1.85
    total = len(PROCESS_CHAIN)
    for index, (name, machine, sawn, wedge, _note) in enumerate(PROCESS_CHAIN):
        x = shift + ((total - 1) * 0.5 - index) * spacing
        dropped = sawn and not wedge
        gone = clamp((p - 0.25) * 2.2) if dropped else 0.0
        colour = RED if dropped else GREEN
        size = 1.25 * (1.0 - gone * 0.55)
        opaque.box(np.array([x, 0.0, 0.7]),
                   np.array([size, size * 0.8, size]),
                   _fade(colour, 1.0 - gone * 0.78))
        _label(app, np.array([x, 0.0, 1.75]), machine,
               _fade(colour, 1.0 - gone * 0.55))
        _label(app, np.array([x, 0.0, -0.5]),
               "DROPPED" if gone > 0.6 else name,
               _fade(MUTED, 1.0 - gone * 0.3))
    dropped = machines_dropped()
    if p > 0.45:
        _label(app, np.array([shift, 0.0, 3.1]),
               f"{len(dropped)} WHOLE MACHINES LEAVE THE CHAIN", AMBER)


def scene_ww_stack(app, opaque, transparent, p: float) -> None:
    """A shelf price, stacked by who takes what."""
    shift = math_shift(app)
    grow = ease_in_out(clamp(0.08 + p * 1.45))
    # The stack is the fifteen hands, grouped into the five stages a board passes
    # through, sized by how many of them each stage holds.
    groups = (
        ("FOREST", 4, GREEN),
        ("SAWMILL", 3, RED),
        ("DRY AND GRADE", 3, AMBER),
        ("PACK AND HAUL", 3, PURPLE),
        ("SELL", 2, MUTED),
    )
    total = float(sum(count for _n, count, _c in groups))
    parts = tuple((name, float(count), colour) for name, count, colour in groups)
    height = 6.0
    # The stack stands ON the ground: an earlier cut started it below zero and the two
    # bottom slices were buried under the grid, which is exactly the two the film is
    # arguing about.
    bottom = 0.15
    for name, value, colour in parts:
        block = height * (value / total) * grow
        if block <= 1e-6:
            continue
        opaque.box(np.array([shift - 1.6, 0.0, bottom + block * 0.5]),
                   np.array([2.0, 1.6, block]), colour)
        if grow > 0.55:
            _label(app, np.array([shift + 1.2, 0.0, bottom + block * 0.5]),
                   f"{name}   {value:.0f} pairs of hands", colour)
        bottom += block
    _label(app, np.array([shift - 1.6, 0.0, bottom + 0.6]),
           f"{len(MIDDLE_MEN)} HANDS, TREE TO RACK", WHITE)
    if p > 0.55:
        _label(app, np.array([shift - 1.6, 0.0, -0.9]),
               f"${MEASURED['stud_shelf_usd']:.2f} on the rack, "
               f"${MEASURED['stud_with_tax_usd']:.2f} paid,\n"
               "and every margin above is inside it", AMBER)


def scene_ww_store(app, opaque, transparent, p: float) -> None:
    """The stack you buy, the part of it you throw away, and the trips it takes."""
    shift = math_shift(app)
    b = purchase_model()
    grow = ease_in_out(clamp(0.1 + p * 1.5))

    # One block per five sticks, so the pile stays countable at this size.
    per_block = 5.0
    blocks = int(round(b["sticks_bought"] / per_block))
    culls = int(round(b["cull_boards"] / per_block))
    rows, columns = 6, 5
    base = np.array([shift + 2.6, 0.0, 0.35])
    shown = int(round(blocks * grow))
    for index in range(min(shown, rows * columns)):
        column, row = index % columns, index // columns
        spot = base + np.array([-column * 1.15, 0.0, row * 0.7])
        opaque.box(spot, np.array([1.02, 1.6, 0.58]),
                   RED if index >= blocks - culls else SAWDUST)
    _label(app, base + np.array([-2.3, 0.0, rows * 0.7 + 0.9]),
           f"{b['sticks_bought']:.0f} STICKS BOUGHT", MUTED)
    if grow > 0.5:
        _label(app, base + np.array([-2.3, 0.0, -1.0]),
               f"{b['cull_boards']:.0f} of them never make it "
               f"(${b['cull_usd']:.0f})", RED)

    # The truck runs that fetch them.
    for load in range(int(b["loads"])):
        if (load + 1) / max(1.0, b["loads"]) > grow * 1.2:
            continue
        x = shift - 3.4 - load * 1.9
        opaque.box(np.array([x, 0.0, 1.0]), np.array([1.5, 1.9, 1.0]), STEEL)
        opaque.cylinder(np.array([x - 0.5, -1.0, 0.35]),
                        np.array([x - 0.5, 1.0, 0.35]), 0.35, (0.1, 0.1, 0.12, 1.0), 8)
        opaque.cylinder(np.array([x + 0.5, -1.0, 0.35]),
                        np.array([x + 0.5, 1.0, 0.35]), 0.35, (0.1, 0.1, 0.12, 1.0), 8)
    _label(app, np.array([shift - 4.6, 0.0, 2.4]),
           f"{b['loads']:.0f} LOADS  ·  {b['trip_miles']:.0f} MILES", AMBER)
    if p > 0.5:
        _label(app, np.array([shift - 4.6, 0.0, -0.9]),
               f"{b['trip_hours']:.1f} h of driving, picking, queuing,\n"
               f"loading and unloading", WHITE)
    if p > 0.7:
        _label(app, np.array([shift - 0.6, 0.0, 5.4]),
               f"${b['buy_cash_usd']:.0f} CASH TO BUY  vs  "
               f"${b['cut_cash_usd']:.0f} OF FUEL TO CUT", GREEN)


def scene_ww_stick(app, opaque, transparent, p: float) -> None:
    """The comparison that does not flatter the wedge, then the one that does."""
    shift = math_shift(app)
    depth = 1.9
    scale = SECTION_SCALE * 1.25
    ground = 2.4

    stud = [point + np.array([shift + 4.4, 0.0, ground])
            for point in _rect_outline(DRESSED_STUD_IN[0], DRESSED_STUD_IN[1], scale)]
    _extrude_outline(opaque, stud, depth, SAWDUST)
    _label(app, np.array([shift + 4.4, 0.0, ground + 1.5]),
           f"DRESSED 2x4   S {STRUCTURE['dressed_modulus']:.2f} in3", MUTED)

    # The same member at the simulator's trunk and at the trunk actually being cut.
    # Drawing only one of them is what let an earlier cut state a verdict where the
    # honest answer is a crossover.
    small = [point + np.array([shift + 0.8, 0.0, ground - 0.9])
             for point in _sector_outline_at(STRUCTURE["dome_diameter_in"], scale)]
    _extrude_outline(opaque, small, depth, WOOD, BARK)
    _label(app, np.array([shift + 0.8, 0.0, ground + 1.5]),
           f"{STRUCTURE['dome_diameter_in']:.0f} IN TRUNK\n"
           f"S {STRUCTURE['dome_modulus']:.2f} in3", RED)
    _label(app, np.array([shift + 0.8, 0.0, ground - 2.1]),
           f"{STRUCTURE['dome_modulus_vs_dressed'] * 100:.0f}% OF THE STUD", RED)

    if p > 0.35:
        big = [point + np.array([shift - 3.9, 0.0, ground - 1.6])
               for point in _sector_outline_at(STRUCTURE["measured_diameter_in"],
                                               scale)]
        _extrude_outline(opaque, big, depth, WOOD, BARK)
        _label(app, np.array([shift - 3.9, 0.0, ground + 2.6]),
               f"{STRUCTURE['measured_diameter_in']:.0f} IN TRUNK\n"
               f"S {STRUCTURE['real_modulus']:.2f} in3", GREEN)
        _label(app, np.array([shift - 3.9, 0.0, ground - 2.9]),
               f"{STRUCTURE['real_modulus_vs_dressed'] * 100:.0f}% OF THE STUD",
               GREEN)
    if p > 0.65:
        _label(app, np.array([shift - 1.4, 0.0, ground + 4.3]),
               f"THE SECTOR OVERTAKES THE STUD AT "
               f"{STRUCTURE['crossover_modulus_dressed']:.2f} IN OF TRUNK", AMBER)


def scene_ww_turn(app, opaque, transparent, p: float) -> None:
    """The same stick, four ways up, each drawn as the pair either side of one seam.

    Laid out as a row rather than a grid: in a 16:9 frame with a teaching card down the
    left, a two-by-two grid put half the states behind the other half.
    """
    shift = math_shift(app)
    scale = SECTION_SCALE * 1.15
    depth = 1.5
    rows = orientation_table()
    live = int(clamp(p * 1.45) * len(rows))
    spacing = 4.9
    for index, (orientation, _reading, _area, _i, modulus) in enumerate(rows):
        # Nudged away from the teaching card, which occupies screen left and was
        # covering the first cell.
        centre = np.array([shift - 2.4 + ((len(rows) - 1) * 0.5 - index) * spacing,
                           0.0, 3.1])
        active = index <= live
        alpha = 1.0 if active else 0.42
        # The seam runs down the middle of each cell; each stick is drawn in its own
        # panel's frame, which is why the two are mirrored.
        opaque.cylinder(centre + np.array([0.0, 0.0, -2.1]),
                        centre + np.array([0.0, 0.0, 2.1]), 0.04,
                        _fade(CYAN, alpha * 0.8), 6)
        tip_y, tip_z = bridge.simulator().rotate_sector_yz(0.0, -1.0, orientation)
        for mirror in (-1.0, 1.0):
            offset = centre + np.array([mirror * 1.25, 0.0, 0.0])
            outline = [
                np.array([point[0] * mirror, point[1], point[2]]) + offset
                for point in _sector_outline(orientation, scale)
            ]
            _extrude_outline(opaque, outline, depth,
                             _fade(WOOD, alpha), _fade(BARK, alpha))
            # An arrow out of the sharp point, which is the only thing that makes
            # "apart" and "toward each other" readable at a glance.
            tip = outline[0]
            direction = np.array([mirror * tip_y, 0.0, tip_z])
            if float(np.linalg.norm(direction)) > 1.0e-6:
                opaque.arrow(tip, tip + normalize(direction) * 1.05, 0.05,
                             _fade(AMBER, alpha))
        name = orientation.replace("point_", "").replace("_", "-").upper()
        _label(app, centre + np.array([0.0, 0.0, 2.1]),
               f"{name}\nS {modulus:.2f} in3", AMBER if active else MUTED)
        if active:
            _label(app, centre + np.array([0.0, 0.0, -2.3]),
                   SHORT_READING[orientation], WHITE)


def scene_ww_fold(app, opaque, transparent, p: float) -> None:
    """One real seam, seen down its own length: the fold, the gap and the key.

    The layout is not sketched.  It is the seam solver's own answer for one interior
    seam of the dome -- the fold angle, the member offset that puts both sawn seam
    faces on a common ridge, and the spacer base width between the two sector points.
    """
    shift = math_shift(app)
    seam = _representative_seam()
    fold = math.radians(seam.fold_angle_deg)
    half = fold * 0.5
    unit = 0.62
    ridge = np.array([shift, 0.0, 3.4])
    reach = 6.4
    grow = ease_in_out(clamp(0.15 + p * 1.5))

    tips = {}
    for sign in (-1.0, 1.0):
        # Panel-inward runs away from the seam and downward by half the fold; the panel
        # normal is dome-outward, perpendicular to it.
        inward = np.array([sign * math.cos(half), 0.0, -math.sin(half)])
        normal = np.array([sign * math.sin(half), 0.0, math.cos(half)])
        far = ridge + inward * reach * grow
        # Drawn as ribs rather than one quad: a zero-thickness panel seen from the
        # camera this chapter uses is a sliver, and the fold it exists to show goes
        # with it.
        for depth_offset in (-2.8, 0.0, 2.8):
            slab = np.array([0.0, depth_offset, 0.0])
            _both_sides(opaque,
                        ridge + slab + np.array([0.0, -0.07, 0.0]),
                        far + slab + np.array([0.0, -0.07, 0.0]),
                        far + slab + np.array([0.0, 0.07, 0.0]),
                        ridge + slab + np.array([0.0, 0.07, 0.0]),
                        _fade(MUTED, 0.80))
        _both_sides(opaque,
                    ridge + np.array([0.0, -2.9, 0.0]),
                    far + np.array([0.0, -2.9, 0.0]),
                    far + np.array([0.0, 2.9, 0.0]),
                    ridge + np.array([0.0, 2.9, 0.0]),
                    _fade(MUTED, 0.22))
        tip = ridge + inward * (seam.member_point_offset_in * unit)
        tips[sign] = tip
        outline = [
            tip + inward * (y * unit) + normal * (z * unit)
            for y, z in sector_section("point_dome_in").points
        ]
        _extrude_outline(opaque, outline, 3.4, WOOD, BARK)

    _label(app, ridge + np.array([0.0, 0.0, 3.6]),
           f"FOLD {seam.fold_angle_deg:.2f} DEG", CYAN)
    if p > 0.42:
        # The key is the triangle between the two sector points and the common ridge:
        # exactly the gap the two raw sawn faces leave once the panels have folded.
        apex = ridge
        a, b = tips[-1.0], tips[1.0]
        for offset in (-1.5, 1.5):
            slice_ = np.array([0.0, offset, 0.0])
            opaque.triangle(a + slice_, b + slice_, apex + slice_, AMBER)
        opaque.quad(a - np.array([0.0, 1.5, 0.0]), a + np.array([0.0, 1.5, 0.0]),
                    apex + np.array([0.0, 1.5, 0.0]), apex - np.array([0.0, 1.5, 0.0]),
                    AMBER)
        opaque.quad(b + np.array([0.0, 1.5, 0.0]), b - np.array([0.0, 1.5, 0.0]),
                    apex - np.array([0.0, 1.5, 0.0]), apex + np.array([0.0, 1.5, 0.0]),
                    AMBER)
        opaque.quad(a - np.array([0.0, 1.5, 0.0]), apex - np.array([0.0, 1.5, 0.0]),
                    apex + np.array([0.0, 1.5, 0.0]), a + np.array([0.0, 1.5, 0.0]),
                    AMBER)
        _label(app, (a + b) * 0.5 + np.array([0.0, 0.0, -1.1]),
               f"THE KEY   base {seam.spacer_base_width_in:.2f} in", AMBER)
        _label(app, ridge + np.array([0.0, 0.0, -3.4]),
               f"raw gap {seam.raw_gap_angle_deg:.2f} deg here, "
               f"{FACTS['gap_min_deg']:.1f}-{FACTS['gap_max_deg']:.1f} deg "
               f"across {FACTS['seams']:.0f} seams", WHITE)


def scene_ww_bench(app, opaque, transparent, p: float) -> None:
    """The jig, built up one component at a time, then loaded."""
    shift = math_shift(app)
    stages = bridge.jig_stages()
    step = int(clamp(p * 1.02) * (len(stages) - 1))
    board_z = 0.25
    board = np.array([shift, 0.0, board_z])
    opaque.box(board, np.array([13.0, 11.0, 0.5]), (0.24, 0.27, 0.31, 1.0))

    top = board_z + 0.3
    corners = [
        np.array([shift - 4.6, -3.8, top]),
        np.array([shift + 4.6, -3.0, top]),
        np.array([shift - 0.5, 4.3, top]),
    ]
    if step >= 1:
        for index in range(3):
            a, b = corners[index], corners[(index + 1) % 3]
            opaque.cylinder(a, b, 0.09, CYAN, 6)
    if step >= 2:
        for index in range(3):
            a, b = corners[index], corners[(index + 1) % 3]
            direction = normalize(b - a)
            offset = normalize(np.cross(direction, np.array([0.0, 0.0, 1.0]))) * 0.78
            opaque.cylinder(a + offset + np.array([0.0, 0.0, 0.26]),
                            b + offset + np.array([0.0, 0.0, 0.26]),
                            0.26, STEEL, 8)
    if step >= 3:
        for index in range(3):
            a, b = corners[index], corners[(index + 1) % 3]
            for fraction, colour in ((0.32, RED), (0.68, GREEN)):
                here = a + (b - a) * fraction
                opaque.box(here + np.array([0.0, 0.0, 0.55]),
                           np.array([0.7, 0.7, 1.0]), colour)
    if step >= 6:
        placed = 3 if step >= 8 else max(0, step - 5)
        sliding = 2 if step == 8 else None
        for index in range(placed):
            a, b = corners[index], corners[(index + 1) % 3]
            direction = normalize(b - a)
            lift = np.array([0.0, 0.0, 0.85])
            # The last member is captured at both ends once the other two are down, so
            # it is shown backed off along its own axis, about to slide home.
            if index == sliding:
                lift = lift - direction * 2.4
            long_end = b + direction * (0.0 if step >= 10 else 1.8)
            _wedge_prism(opaque, a - direction * 0.5 + lift, long_end + lift,
                         np.array([0.0, 0.0, 1.0]), 0.5)
            if step < 10:
                _wedge_prism(opaque, b + lift, long_end + lift,
                             np.array([0.0, 0.0, 1.0]), 0.505,
                             wood=_fade(OFFCUT, 0.85), bark=_fade(OFFCUT, 0.7))

    _slug, headline, _looking, _forces = stages[step]
    _label(app, board + np.array([0.0, 0.0, 5.6]), headline, AMBER)
    if p > 0.3:
        _label(app, board + np.array([0.0, 0.0, -1.3]),
               f"{len(stages)} steps, and {FACTS['jig_variants']:.0f} fixtures "
               f"for all {FACTS['panels']:.0f} panels", WHITE)


def scene_ww_flush(app, opaque, transparent, p: float) -> None:
    """One corner: the head arrives long, the loop closes, the saw runs on the fence."""
    shift = math_shift(app)
    cut = ease_in_out(clamp((p - 0.40) * 2.3))
    origin = np.array([shift + 3.6, 0.0, 1.4])
    direction = np.array([-1.0, 0.0, 0.0])
    finished = 5.2
    over = 2.8
    across = origin + direction * finished

    _wedge_prism(opaque, origin, across, np.array([0.0, 0.0, 1.0]), 0.55)
    if cut < 0.98:
        _wedge_prism(opaque, across, across + direction * over,
                     np.array([0.0, 0.0, 1.0]), 0.55,
                     wood=_fade(OFFCUT, 0.9 - cut * 0.7),
                     bark=_fade(OFFCUT, 0.75 - cut * 0.6))

    # The receiving member whose sawn face establishes the plane the head is cut to.
    _wedge_prism(opaque, across + np.array([0.0, -3.0, 0.0]),
                 across + np.array([0.0, 3.0, 0.0]),
                 np.array([0.0, 0.0, 1.0]), 0.55)

    # The fence is translucent so it reads as a guide surface rather than a wall.
    fence = across + np.array([0.0, 0.0, 1.1])
    transparent.box(fence, np.array([0.08, 5.4, 2.4]), _fade(PURPLE, 0.34))
    if 0.08 < cut < 0.96:
        blade_y = -2.4 + 4.8 * cut
        opaque.box(across + np.array([-0.16, blade_y, 1.1]),
                   np.array([0.05, 1.1, 2.2]), WHITE)

    _label(app, across + np.array([0.0, 0.0, 2.8]),
           "THE FENCE IS THE PLANE. NOTHING IS MEASURED.", PURPLE)
    if cut < 0.35:
        _label(app, across + direction * 1.2 + np.array([0.0, 0.0, -1.2]),
               f"{FACTS['head_overfit_in']:.0f} in TOO LONG, ON PURPOSE", OFFCUT)
    elif p > 0.65:
        _label(app, across + np.array([0.0, 0.0, -1.9]),
               f"{FACTS['head_offcut_share'] * 100:.1f}% of raw length leaves "
               "as offcut,\nand every error leaves with it", GREEN)


def scene_ww_close(app, opaque, transparent, p: float) -> None:
    """The finished shell, and the one sentence it stands on."""
    _shell(opaque, 1.0)
    stand = np.array([SCENE_RADIUS + 1.6, 0.0, 0.0])
    opaque.cylinder(stand, stand + np.array([0.0, 0.0, 6.0 * FOOT]),
                    0.16, _fade(WHITE, 0.55), 8)
    _label(app, stand + np.array([0.0, 0.0, 6.2 * FOOT]), "6 ft", MUTED)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 2.1]),
           f"{FACTS['panels']:.0f} PANELS  ·  {FACTS['members']:.0f} SPLIT LOGS  ·  "
           f"{FACTS['jig_variants']:.0f} FIXTURES", GREEN)
    if p > 0.4:
        _label(app, np.array([0.0, 0.0, -1.2]),
               "the shape is what makes the cheap stick sufficient", WHITE)


def scene_ww_sessions(app, opaque, transparent, p: float) -> None:
    """The two timed cutting sessions, and the number they agree on."""
    shift = math_shift(app)
    rates = cut_rate_model()
    grow = ease_in_out(clamp(0.1 + p * 1.5))

    # Session A counted finished wedges.
    base_a = np.array([shift - 4.4, 0.0, 3.6])
    made = int(round(RATE_MEASURED["session_a_wedges"] * grow))
    for index in range(made):
        column, row = index % 6, index // 6
        spot = base_a + np.array([column * 1.05, 0.0, -row * 1.15])
        _wedge_prism(opaque, spot, spot + np.array([0.0, 1.5, 0.0]),
                     np.array([0.0, 0.0, 1.0]), 0.30)
    _label(app, base_a + np.array([2.6, 0.0, 1.1]),
           f"SESSION A   {RATE_MEASURED['session_a_wedges']:.0f} WEDGES "
           f"IN {RATE_MEASURED['session_a_hours']:.0f} H", GREEN)
    if grow > 0.5:
        _label(app, base_a + np.array([2.6, 0.0, -2.9]),
               f"{rates['wedges_per_hour']:.0f} wedges/hour  ·  "
               f"${rates['consumables_usd_per_hour']:.2f}/hour of fuel", WHITE)

    # Session B counted linear feet of rip.
    base_b = np.array([shift + 3.4, 0.0, -1.2])
    length = rates["rip_feet_per_hour"] * 0.16 * grow
    for index in range(6):
        z = base_b[2] + index * 0.62
        run = min(length, rates["section_ft"] * 0.16 * 6.0)
        piece = min(max(0.0, length - index * rates["section_ft"] * 0.16),
                    rates["section_ft"] * 0.16)
        if piece <= 1.0e-4:
            continue
        opaque.box(np.array([base_b[0] - piece * 0.5, 0.0, z]),
                   np.array([piece, 0.6, 0.42]), AMBER)
    _label(app, base_b + np.array([-1.4, 0.0, 4.4]),
           f"SESSION B   {rates['rip_feet_per_hour']:.0f} FT OF RIP IN "
           f"{RATE_MEASURED['session_b_hours']:.0f} H", AMBER)
    if p > 0.55:
        _label(app, base_b + np.array([-1.4, 0.0, -1.4]),
               f"{rates['measured_ft_per_wedge']:.2f} ft of rip per wedge;\n"
               f"the geometry predicts {rates['geometric_ft_per_wedge']:.2f}",
               CYAN)


def scene_ww_worth(app, opaque, transparent, p: float) -> None:
    """One wedge, against the studs it would take to match its section."""
    shift = math_shift(app)
    value = wedge_value_model()
    scale = SECTION_SCALE * 0.78
    depth = 2.2
    ground = 2.2

    wedge = [point + np.array([shift + 3.4, 0.0, ground - 1.2])
             for point in _sector_outline_at(value["diameter_in"], scale)]
    _extrude_outline(opaque, wedge, depth, WOOD, BARK)
    _label(app, np.array([shift + 3.4, 0.0, ground + 2.6]),
           f"ONE WEDGE, {value['diameter_in']:.0f} IN TRUNK\n"
           f"{value['wedge_area_in2']:.2f} in2", GREEN)

    whole = int(math.floor(value["computed_multiplier"]))
    shown = clamp(p * 1.7)
    for index in range(whole + 1):
        fraction = value["computed_multiplier"] - whole if index == whole else 1.0
        if fraction <= 0.02 or (index + 1) / (whole + 1) > shown + 0.15:
            continue
        stud = [point + np.array([shift - 2.6 - index * 1.5, 0.0, ground - 1.0])
                for point in _rect_outline(DRESSED_STUD_IN[0],
                                           DRESSED_STUD_IN[1] * fraction, scale)]
        _extrude_outline(opaque, stud, depth, SAWDUST)
    _label(app, np.array([shift - 4.0, 0.0, ground + 2.6]),
           f"{value['computed_multiplier']:.2f} DRESSED 2x4s", MUTED)
    if p > 0.5:
        earn = earnings_model()
        _label(app, np.array([shift - 0.4, 0.0, ground - 3.2]),
               f"${value['rule_usd_per_wedge']:.2f} of wood per wedge  ·  "
               f"${earn['net_usd_per_hour']:.0f}/hour net", AMBER)


def scene_ww_bend(app, opaque, transparent, p: float) -> None:
    """A bent trunk: what one defect costs a short piece and a long one."""
    shift = math_shift(app)
    d = defect_model()
    span = 11.0
    bend_at = 0.52
    reveal = clamp(0.15 + p * 1.6)

    # The trunk, drawn with a kink in the middle.
    segments = 26
    previous = None
    for index in range(segments + 1):
        t = index / segments
        x = shift + (0.5 - t) * span
        z = 3.4 + (-1.15 * math.exp(-((t - bend_at) ** 2) / 0.004))
        point = np.array([x, 0.0, z])
        if previous is not None and t <= reveal:
            opaque.cylinder(previous, point, 0.45, _fade(BARK, 0.95), 8)
        previous = point

    # The short pieces that survive it, and the one long stick that does not.
    piece = span * d["short_ft"] / d["usable_ft"] * (d["usable_ft"] / (span * 0.0 + 60.0))
    piece = span / 10.0
    for index in range(10):
        t0 = index / 10.0
        t1 = (index + 1) / 10.0
        spoiled = t0 < bend_at < t1
        if (index + 1) / 10.0 > reveal * 1.2:
            continue
        x = shift + (0.5 - (t0 + t1) * 0.5) * span
        opaque.box(np.array([x, -1.6, 1.2]),
                   np.array([piece * 0.86, 0.8, 0.5]),
                   RED if spoiled else GREEN)
    _label(app, np.array([shift, 0.0, 0.2]),
           f"{d['short_ft']:.0f} FT PIECES: ONE IS SPOILED, "
           f"{d['short_pieces'] - 1:.0f} SURVIVE", GREEN)

    if p > 0.45:
        long_len = span * d["long_ft"] / 60.0 * (60.0 / d["usable_ft"])
        long_len = span * (d["long_ft"] / d["usable_ft"])
        for index in range(3):
            t0 = index * d["long_ft"] / d["usable_ft"]
            t1 = t0 + d["long_ft"] / d["usable_ft"]
            spoiled = t0 < bend_at < t1
            x = shift + (0.5 - (t0 + t1) * 0.5) * span
            opaque.box(np.array([x, 1.8, -0.9]),
                       np.array([long_len * 0.9, 0.8, 0.5]),
                       RED if spoiled else GREEN)
        _label(app, np.array([shift, 0.0, -1.9]),
               f"{d['long_ft']:.0f} FT STICKS: ONE IS SPOILED, "
               f"{d['long_pieces'] - 1:.0f} SURVIVE", RED)
        _label(app, np.array([shift, 0.0, -3.1]),
               f"the same bend costs {d['short_loss_share'] * 100:.0f}% of the "
               f"tree, or {d['long_loss_share'] * 100:.0f}%", WHITE)


SCENES = {
    "ww_open": scene_ww_open,
    "ww_round": scene_ww_round,
    "ww_chain": scene_ww_chain,
    "ww_stack": scene_ww_stack,
    "ww_stick": scene_ww_stick,
    "ww_turn": scene_ww_turn,
    "ww_fold": scene_ww_fold,
    "ww_bench": scene_ww_bench,
    "ww_flush": scene_ww_flush,
    "ww_close": scene_ww_close,
    "ww_sessions": scene_ww_sessions,
    "ww_worth": scene_ww_worth,
    "ww_bend": scene_ww_bend,
    "ww_store": scene_ww_store,
}

# Chapters borrowed whole from the two earlier films. Reusing the painters rather than
# re-drawing the same wood is the only way the three films can be guaranteed to agree
# about what a wedge, a pinwheel and a folded V bracket look like.
BORROWED_SCENES = {
    name: WEDGE_SCENES[name]
    for name in ("wg_mill", "wg_split", "wg_section", "wg_short", "wg_explode",
                 "wg_pinwheel", "wg_corner", "wg_pair", "wg_scale")
}
BORROWED_SCENES.update({
    name: FRANKEN_SCENES[name]
    for name in ("fk_triangle", "fk_bracket_fitted")
})
SCENES.update(BORROWED_SCENES)

# Math screens borrowed from `eight-cuts-to-a-house`. They measure the member, the
# joint and the shell the trees size -- mechanism this film needs and would otherwise
# have had to restate in slightly different words, which is how two films start
# disagreeing about the same number.
BORROWED_SCREENS = (wf_steps_sector, wf_steps_pinwheel, wf_steps_dome)


# ======================================================================
# The chapters
# ======================================================================

def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps,
                   duration, camera, stage, "math")


# Identical in behaviour; named separately so the validation can tell which math
# screens this film owns and which it is borrowing.
_borrowed = _math


_AUTHORED: tuple[Chapter, ...] = (
    # ---------------------------------------------- where it came from
    Chapter(
        "open", "00", "Why I build like this",
        "The tree is already the right shape for something.",
        (
            "Every stick of framing lumber you can buy started as a round,",
            "tapered, slightly bent thing, and was then cut, edged, dried,",
            "planed and graded until it became a rectangle.",
            "That rectangle is not a structural requirement. It is a handling",
            "requirement. Rectangles stack on a pallet, price by the piece and",
            "fit a stud wall.",
            "A geodesic dome does not need any of that. It needs sticks whose",
            "ends can be made to meet. So I stopped making rectangles.",
            "This is how that decision got made, what it does, and what it is",
            "worth, in numbers I measured rather than adjectives I chose.",
        ),
        (f"{FACTS['members']:.0f} members from split logs",
         f"{FACTS['panels']:.0f} panels, one flat jig"),
        29.0, (34.0, 22.0, 21.0), "ww_open",
    ),
    Chapter(
        "franken", "00", "It started with the frankendome",
        "A shell that did not care what shape its sticks were.",
        (
            "Before any of this there was the frankendome. Forty triangles",
            "joined along their edges from the top down, and deliberately",
            "strut-agnostic: any section, any stock, whatever was to hand.",
            "The crown was the interesting part. Instead of the usual",
            "fifteen-piece pentagon it used one strut from each corner to the",
            "apex rather than two, making a heavier-duty ten-piece cap.",
            "What that build proved is the thing everything after it depends",
            "on. If the shell will accept members of any section, then the",
            "section stops being a constraint and becomes a choice.",
        ),
        ("40 triangles, joined edge to edge",
         "10-piece crown pentagon, not 15"),
        30.0, (32.0, 24.0, 20.0), "fk_triangle",
    ),
    Chapter(
        "bracket", "00", "The V bracket that made it possible",
        "One connector that does not care what it is holding.",
        (
            "Edge-to-edge joining between odd-shaped members is a bracket",
            "problem, and most bracket types need to know what they are",
            "gripping before you can make them.",
            "A V bracket does not. Folded from flat stock, it takes a corner",
            "from any of the agnostic member types, which is hard to achieve",
            "with anything else at the moment.",
            "Once the connector stopped caring about section, the obvious next",
            "question was what the cheapest possible member is. The answer was",
            "a log with three saw cuts in it.",
        ),
        ("folded from flat stock",
         "any member type, same corner"),
        28.0, (26.0, 20.0, 16.0), "fk_bracket_fitted",
    ),

    # ---------------------------------------------- the tree and the stick
    Chapter(
        "square", "00", "What a mill is actually for",
        "Four machines whose entire job is making a circle into a box.",
        (
            "A sawmill breaks the log down. An edger squares the waney sides.",
            "A trimmer squares the ends. A planing mill, usually a separate",
            "plant altogether, surfaces four faces to a known dimension.",
            "None of those machines make the wood stronger. Every one of them",
            "exists to make a round, tapered, irregular thing into a",
            "rectangular prism that can be stacked, priced and shipped.",
            "That is a genuinely useful thing to do if you are building a stud",
            "wall. It is a completely wasted effort if you are building a",
            "shell out of triangles.",
        ),
        ("square, edge, trim, plane",
         "none of it adds strength"),
        27.0, (30.0, 22.0, 18.0), "wg_mill",
    ),
    Chapter(
        "round", "00", "The corners of a round log",
        "Waste is not bad wood. It is wood of the wrong shape.",
        (
            "Put a rectangle inside a circle and you leave four crescents",
            "outside it. Put a second rectangle beside the first and the",
            "crescents get bigger, because the circle is pinching in.",
            "None of that discarded wood is defective. It is slabs and edgings",
            "and planer shavings because it failed a geometry test, not a",
            "strength test.",
            "Split the same section radially instead and there are no crescents",
            "at all. Every sector runs from the pith to the bark, and the only",
            "wood that leaves is the width of the saw.",
        ),
        ("radial split: pith to bark, no offcut",
         "sawn: everything outside the rectangle"),
        26.0, (78.0, 14.0, 22.0), "ww_round",
    ),
    _math(
        "yield", "How much of the tree survives",
        "The same two trees, converted both ways, counted in board feet.",
        (
            "This is one pine measured at the butt and at the top, bucked into",
            "twelve foot sections, and then converted twice on paper.",
            "Split radially it keeps almost everything, losing only the kerf of",
            "the passes down each section. Packed with rectangles it keeps under",
            "half, and that is with the rectangles packed as favourably as a",
            "mill would pack them.",
            "The measured figure across whole trees on site is eighty-eight",
            "percent, against fifty to sixty-five for square milling, which",
            "loses wood to a good deal more than the kerf.",
        ),
        steps_yield(), 36.0, (74.0, 15.0, 24.0), "ww_round",
    ),
    Chapter(
        "split", "00", "Three cuts and it is structure",
        "One saw, one sequence, and the stick exists.",
        (
            "The whole conversion is one saw and a sequence. Halve the round.",
            "Halve each half. Halve each quarter. Eight sectors, forty-five",
            "degrees each, and every one of them already has two flat faces",
            "and a curved back.",
            "Nothing is squared, nothing is edged, nothing is dried to a spec",
            "and nothing is planed. The sawn faces come off the split flat",
            "enough to bear on each other, which is the only flatness this",
            "building needs.",
        ),
        (f"{SECTORS_PER_LOG} sectors, {SECTOR_ANGLE_DEG:.0f} deg each",
         "two sawn faces, one bark back"),
        26.0, (28.0, 20.0, 17.0), "wg_split",
    ),
    Chapter(
        "member", "00", "One eighth of a tree, used as a stick",
        "The section is a wedge, and the wedge is the point.",
        (
            "A member here is literally an eighth of the trunk. It keeps the",
            "pith line as a sharp edge, the two radial saw cuts as flat faces,",
            "and the outer growth rings as a curved back.",
            "Put the bark face outward and the densest wood in the tree ends up",
            "on the weather side, while the deep dimension of the section faces",
            "the load.",
            "How strong that is depends on how big the tree was, and that turns",
            "out to be the hinge the whole structural argument swings on. We",
            "will come back to it with a number.",
        ),
        ("bark out, pith in",
         f"1/{SECTORS_PER_LOG} of the trunk, per member"),
        27.0, (24.0, 18.0, 15.0), "wg_section",
    ),
    _borrowed(
        "sector", "The member, measured",
        "What one raw sector is, in section and in bearing.",
        (
            "This is the member the rest of the film keeps referring to,",
            "measured rather than described: the sector's angle, its chord and",
            "depth, the area it presents, and what that is worth against a",
            "two-by-four.",
            "The bearing figure matters more than it looks. In this frame one",
            "member's end presses on the flat sawn side of the next, so the",
            "joint's capacity is an area of wood against wood rather than a",
            "fastener in shear.",
        ),
        wf_steps_sector(), 34.0, (24.0, 18.0, 15.0), "wg_section",
    ),
    Chapter(
        "short", "00", "Why six feet is the useful length",
        "A defect in a long stick ruins a long stick.",
        (
            "The members here are short, and that is not a compromise. A knot",
            "or a bend does not destroy wood; it destroys whatever length has",
            "to be thrown away around it.",
            "That length is set by the piece you were trying to make. On a",
            "sixteen foot stick, one bad metre in the middle costs the whole",
            "board. On six foot pieces it costs one piece.",
            "It also means a crooked farm tree is usable. Cut the bend out at",
            "its middle, go six feet clear either side, and the sections above",
            "and below it are both still structure.",
        ),
        ("short pieces, more places for a defect to fall",
         "a bend costs one piece, not one board"),
        27.0, (26.0, 18.0, 16.0), "wg_short",
    ),
    _math(
        "defects", "What one bend actually costs",
        "The same flaw, priced against two different piece lengths.",
        (
            "Here is the arithmetic behind that. A single defect takes out one",
            "piece, so its cost as a share of the tree is just the length of",
            "the piece you were cutting.",
            "Short members make a defect several times cheaper, and they also",
            "give the trunk more pieces, so there are more places for a flaw to",
            "fall harmlessly between two of them.",
            "In square milling the same bend follows the board down its whole",
            "length, because the rectangle has to be straight before it exists",
            "at all.",
        ),
        steps_defects(), 34.0, (26.0, 18.0, 16.0), "ww_bend",
    ),

    # ---------------------------------------------- the frame
    Chapter(
        "panels", "00", "Forty frames, not one lattice",
        "Each triangle is finished before it meets its neighbours.",
        (
            "The shell is not assembled stick by stick in the air. It is forty",
            "independent triangular frames, each one completed flat on a bench",
            "and then lifted into place.",
            "That is what turns a geodesic dome from a scaffolding problem into",
            "a panel problem. The awkward geometry all happens on a board at",
            "waist height, indoors, in daylight.",
            "It also means a panel can be rejected, remade or replaced without",
            "touching anything else.",
        ),
        (f"{FACTS['panels']:.0f} independent frames",
         "every joint made flat on a bench"),
        27.0, (34.0, 24.0, 19.0), "wg_explode",
    ),
    Chapter(
        "pinwheel", "00", "The joint with no mitres in it",
        "No mitres, no coping, nothing shaved to a point.",
        (
            "Inside each triangle the three members run as a same-handed",
            "pinwheel. Every member's end lands on the flat side of the next",
            "one, the same way round for all three.",
            "Nothing is mitred, coped or shaved to a point. The mathematical",
            "corner of the triangle becomes a reference point that no stick",
            "actually reaches.",
            "That is the move that makes raw split wood viable. A wedge already",
            "has flat sawn faces; the pinwheel is the joint that only ever asks",
            "for the faces it already has.",
        ),
        ("end to side, three times round",
         "the corner is a reference, not a meeting"),
        29.0, (22.0, 18.0, 14.0), "wg_pinwheel",
    ),
    _borrowed(
        "joint", "The pinwheel, measured",
        "Offsets, bearing and the gap at the mathematical vertex.",
        (
            "The pinwheel is not free. Every member sits a small distance back",
            "from the ideal edge, and that offset is what opens the gap at the",
            "vertex that no stick reaches.",
            "Both figures come out of the same solve, and they are what the jig",
            "later has to hold. The bearing area is the joint's real capacity;",
            "the vertex gap is what has to be trimmed away cleanly so that",
            "panels do not fight each other at a node.",
        ),
        wf_steps_pinwheel(), 34.0, (22.0, 18.0, 14.0), "wg_corner",
    ),
    Chapter(
        "duplicate", "00", "Neighbours never share a stick",
        "Two members along every shared edge, on purpose.",
        (
            "A conventional frame would put one member on the edge between two",
            "panels and bolt both to it. This one does not. Each panel carries",
            "its own member along that edge, so the shell has two.",
            "That sounds wasteful and is the opposite. It means a panel is",
            "complete before it meets anything, and it means the joint between",
            "panels is a connection between two finished things rather than a",
            "shared dependency.",
            "It also doubles the wood on every interior edge, which is where",
            "the structural argument later gets its margin from.",
        ),
        (f"{FACTS['seams']:.0f} interior seams, two members each",
         "panels finish before they meet"),
        28.0, (20.0, 16.0, 14.0), "wg_pair",
    ),

    # ---------------------------------------------- the case
    _math(
        "assumptions", "What I measured and what I guessed",
        "Two piles, kept apart, before any money is discussed.",
        (
            "Angles, board feet and section properties in this film are",
            "computed from the same code that builds the dome. What follows now",
            "is not, so here is the whole table before it gets used.",
            "The first pile is measured: two timed cutting sessions, the fuel",
            "they burned, a price read off a rack, and the diameter of the log",
            "being cut.",
            "The second pile is estimated, and every item in it sits on the",
            "store-bought side of the comparison. That is the side it flatters",
            "me least to be guessing about.",
        ),
        steps_assumptions(), 38.0, (26.0, 16.0, 18.0), "ww_stack",
    ),
    Chapter(
        "chain", "00", "Machines that stop being necessary",
        "Each conversion step is a building full of steel somebody owns.",
        (
            "Follow a log through the conversion chain and count the plant. A",
            "headrig, an edger, a trimmer, a kiln, a grading line and a planing",
            "mill, which is usually a separate factory again.",
            "The wedge path keeps the chainsaw that felled the tree and drops",
            "the rest, because a split face is already flat, already exact, and",
            "already dry enough for a shell that is not a graded-lumber",
            "assembly.",
            "I started this build believing it saved me one entire mill. The",
            "count says more than that, and the count is on the next screen",
            "rather than the claim.",
        ),
        (", ".join(machines_dropped()),
         "the chainsaw does the primary breakdown"),
        29.0, (86.0, 12.0, 22.0), "ww_chain",
    ),
    _math(
        "mills", "Counting the machines out",
        "Station by station, which survives and which does not.",
        (
            "Here is the whole chain with the wedge path laid alongside it.",
            "Felling and bucking is in both, so it cancels. Crosscutting to",
            "length is in both.",
            "End joinery is in both too, though it is a very different",
            "operation on each side, and that difference is most of the time",
            "saving later.",
            "What is left on the wedge side, at the end of the count, is one",
            "chainsaw and a flat board.",
        ),
        steps_mills(), 36.0, (84.0, 13.0, 25.0), "ww_chain",
    ),
    Chapter(
        "middlemen", "00", "What a shelf price is made of",
        "Almost none of it is the tree.",
        (
            "When you buy a stud you are not mostly buying wood. You are buying",
            "the sawing, the drying, the planing, the grading, the log truck,",
            "the flatbed, the warehouse that held it and the yard that sold it.",
            "None of those people are villains and none of that work is fake.",
            "But every one of those steps exists to turn a round local thing",
            "into a standard shippable thing.",
            "A dome does not need it to be standard, and I do not need it to be",
            "shipped, because the tree was already here.",
        ),
        (f"{len(MIDDLE_MEN)} hands between the tree and the rack",
         f"${MEASURED['stud_shelf_usd']:.2f} on the rack, "
         f"${MEASURED['stud_with_tax_usd']:.2f} paid"),
        29.0, (84.0, 12.0, 17.0), "ww_stack",
    ),
    _math(
        "middlemen_math", "Fifteen sets of hands",
        "Listed, because a round number is easy to say and hard to check.",
        (
            "Claiming you have cut out about fifteen middle men is the sort of",
            "thing that deserves a list rather than a wave, so here is the list.",
            "Every one of them took a margin, and every one of those margins is",
            "in the price on the rack, along with the tax on top of all of it.",
            "The wedge path in full is three steps: fell the tree, rip the",
            "trunk, use the wood.",
        ),
        steps_middlemen(), 38.0, (82.0, 13.0, 19.0), "ww_stack",
    ),
    Chapter(
        "sessions", "00", "What the saw actually does",
        "Two sittings, timed, with the fuel written down.",
        (
            "Everything so far could be argued. This part was measured.",
            "One sitting produced twelve wedges in two hours and burned ten",
            "dollars of fuel and bar oil. A separate sitting cut forty-two feet",
            "of rip at six inches of depth in one hour, on two tanks of fuel and",
            "two of bar oil, including a chain sharpening.",
            "Those two sessions counted different things, which is what makes",
            "them worth having. Divide one by the other and you get feet of cut",
            "per finished wedge, and the geometry can predict that number",
            "independently.",
        ),
        (f"{cut_rate_model()['wedges_per_hour']:.0f} wedges/hour",
         f"{cut_rate_model()['rip_feet_per_hour']:.0f} ft of rip/hour"),
        31.0, (80.0, 16.0, 22.0), "ww_sessions",
    ),
    _math(
        "rate", "Do the two sessions agree?",
        "A prediction the geometry can make without being told.",
        (
            "Splitting a round into eight sectors takes seven passes down the",
            "whole length of the section. That is a pure geometric statement and",
            "it gives feet of cut per wedge without any timing at all.",
            "Set it beside the number the two timed sessions imply and they land",
            "close. The gap between them is rolling the log, setting up and",
            "sharpening, which is exactly the sort of thing that should be the",
            "difference.",
            "Planning then uses a rate below both, because an afternoon is not",
            "a timed sprint.",
        ),
        steps_rate(), 38.0, (80.0, 16.0, 22.0), "ww_sessions",
    ),
    Chapter(
        "worth", "00", "What one wedge is worth",
        "Priced against the sticks it would take to replace it.",
        (
            "A wedge is not one two-by-four. It is thicker, so comparing them",
            "piece for piece would quietly build a weaker dome and call it",
            "cheaper.",
            "The honest comparison is by cross-section: how many dressed studs",
            "you would have to lay alongside one wedge to match the wood in it.",
            "At the trunk diameter I actually cut, that number is close to",
            "three, and the estimate I have been using for planning is two.",
        ),
        (f"{wedge_value_model()['computed_multiplier']:.2f} studs' section per wedge",
         f"${wedge_value_model()['rule_usd_per_wedge']:.2f} of wood per wedge"),
        29.0, (78.0, 15.0, 20.0), "ww_worth",
    ),
    _math(
        "value", "The rule of thumb, checked",
        "Two ways to price a wedge, and how far apart they land.",
        (
            "The rule of thumb multiplies a conservative section factor by the",
            "price of an eight-foot stud section. The strict version uses the",
            "computed section and also corrects for the fact that a six-foot",
            "wedge is shorter than an eight-foot stud.",
            "They should not agree as closely as they do. The conservative",
            "multiplier and the generous length happen to cancel almost exactly,",
            "which is a piece of luck rather than a method.",
            "Either way, an afternoon of ripping produces a specific number of",
            "dollars of wood I would otherwise have had to buy.",
        ),
        steps_value(), 38.0, (78.0, 15.0, 20.0), "ww_worth",
    ),
    Chapter(
        "store", "00", "The part nobody counts",
        "Culls, trips, hours and the boards that never make it.",
        (
            "A shelf price is not what lumber costs you. There is the drive",
            "there and back, the time picking through a rack for boards that",
            "are not bowed, the queue, the loading and the unloading.",
            "There are the boards you buy and then reject anyway, and the ones",
            "that split or soak between the yard and the site. You paid for",
            "those too.",
            "My chainsaw's fuel bill sits roughly where the truck's fuel bill",
            "would have been, so it is not the consumables that differ. It is",
            "everything attached to them.",
        ),
        (f"{ASSUMED['cull_share'] * 100:.0f}% bought and rejected",
         f"{purchase_model()['loads']:.0f} truck loads, "
         f"{purchase_model()['trip_hours']:.1f} h of driving"),
        29.0, (84.0, 16.0, 21.0), "ww_store",
    ),
    _math(
        "overhead", "The same frame, bought",
        "Enough studs to match the section, plus everything attached.",
        (
            "This prices the store-bought route properly: enough dressed studs",
            "to match the cross-section the wedges provide, not one stud per",
            "member, because those are not the same building.",
            "Then the culls, the transit losses, the truck runs and the hours",
            "those runs take. Every one of those is an estimate and every one is",
            "on the side of the comparison I am arguing against.",
            "The cutting column is the measured rate and the measured fuel, and",
            "it contains no trips at all.",
        ),
        steps_overhead(), 40.0, (82.0, 16.0, 23.0), "ww_store",
    ),

    # ---------------------------------------------- why it holds up
    Chapter(
        "stick", "00", "The number that depends on the tree",
        "The one figure that could sink all of this.",
        (
            "A raw sector is literally one eighth of the tree. Whether that is",
            "a stronger stick than a two-by-four is not a yes or a no; it is a",
            "question about diameter.",
            "Cross-section grows with the square of the radius and bending",
            "stiffness grows with the cube, so there is a trunk diameter where",
            "the sector overtakes the stud, and below it the sector loses.",
            "I am going to give you that crossover diameter rather than a",
            "slogan, because it is the one number that could sink this whole",
            "method and it deserves to be said out loud.",
        ),
        (f"crossover at "
         f"{STRUCTURE['crossover_modulus_dressed']:.2f} in of trunk",
         f"the trees being cut are "
         f"{STRUCTURE['measured_diameter_in']:.0f}-15 in"),
        31.0, (80.0, 14.0, 20.0), "ww_stick",
    ),
    _math(
        "structure", "Section properties, and the crossover",
        "Area, second moment and section modulus, at both diameters.",
        (
            "These are not looked up. The sector outline comes out of the same",
            "code that builds the dome, and the area and second moments are",
            "integrated around that polygon, checked against the closed form for",
            "a circular sector.",
            "At the eight-inch trunk the simulator defaults to, one wedge is the",
            "weaker stick in bending. At the twelve-inch trunks I actually cut,",
            "it is comfortably the stronger one. The crossover is solved for",
            "rather than asserted.",
            "None of this is an engineer's design check. A real build needs",
            "species, grade, moisture and somebody who will sign it. This is the",
            "geometry underneath that conversation.",
        ),
        steps_structure(), 40.0, (78.0, 15.0, 22.0), "ww_stick",
    ),
    Chapter(
        "turn", "00", "Four ways up, one of them free",
        "The wedge is not symmetric, so which way it faces is a decision.",
        (
            "A sector has a point, two flat sawn faces and a curved bark back.",
            "Rotate it about its own long axis and you have four distinct",
            "positions in the wall.",
            "The way to read them is to look at a pair either side of one seam.",
            "The points can face into the dome together, out at the sky",
            "together, apart into their own panels, or in toward each other",
            "across the seam.",
            "It costs nothing to choose. Same stick, same wood, turned before it",
            "goes down. But the choice changes how deep the section is in the",
            "direction the shell actually bends.",
        ),
        ("points in, points out, points apart, points together",
         "same wood, different depth under load"),
        30.0, (88.0, 11.0, 24.0), "ww_turn",
    ),
    _math(
        "orientation", "What the rotation is worth",
        "The same area, turned four ways, measured each time.",
        (
            "A shell member is pushed in and out along the dome's own radius, so",
            "the stiffness that matters is measured in that direction.",
            "Turn the sector and the area does not move by a thousandth of an",
            "inch, because rotating a shape does not add wood to it. The section",
            "modulus moves a great deal.",
            "Pointing the wedge at the centre of the dome, bark out at the",
            "weather, is the position that puts the most depth where the bending",
            "is. It also puts the densest outer wood on the wet side and leaves",
            "both flat sawn faces where the seam key wants them.",
        ),
        steps_orientation(), 36.0, (86.0, 12.0, 26.0), "ww_turn",
    ),
    Chapter(
        "fold", "00", "Why there is a key in every seam",
        "Put the variation somewhere it is cheap to be wrong.",
        (
            "Neighbouring triangles in a geodesic shell meet at an angle, and it",
            "is not the same angle everywhere. That fold is what makes the thing",
            "a dome instead of a floor.",
            "Because each panel carries its own member, a seam is two raw sawn",
            "faces looking at each other with a gap between them, and the gap",
            "changes seam by seam.",
            "You can close it by shaving the wood to suit each neighbour, which",
            "is a different bevel every time. Or you can leave the structure",
            "alone and put the variation into a small tapered part that is not",
            "holding the building up.",
        ),
        (f"fold {FACTS['fold_min_deg']:.2f}-{FACTS['fold_max_deg']:.2f} deg",
         f"key base {FACTS['key_base_min_in']:.2f}-"
         f"{FACTS['key_base_max_in']:.2f} in"),
        30.0, (90.0, 9.0, 18.0), "ww_fold",
    ),
    _math(
        "dihedral", "The angle nobody wants to cut",
        "Better in a cheap part than in every stick.",
        (
            "Here is the fold at every interior seam, and what is left over",
            "after two forty-five degree faces have folded toward each other.",
            "The spread is small in degrees and enormous in workshop terms,",
            "because it is a setup change on a saw, repeated once per seam, cut",
            "into structural members that are then not interchangeable.",
            "Moving that variation into the key means the wood stays generic and",
            "the fussy part is small, cheap and replaceable.",
        ),
        steps_dihedral(), 36.0, (88.0, 10.0, 20.0), "ww_fold",
    ),
    Chapter(
        "bench", "00", "One flat board, forty panels",
        "The jig is not a drawing aid. It is what makes them identical.",
        (
            "The fixture is a flat board with the panel's triangle struck on it",
            "once, three rails, six little plates and some clamps.",
            "The rails set each member across the panel by its sawn point line,",
            "never by its bark, because the bark is the part of a log that is",
            "different every time.",
            "The red and green plates do something a drawing cannot. A sector",
            "dropped in rotated ninety degrees still looks plausible; against",
            "these plates it physically will not seat. The fixture refuses the",
            "mistake instead of relying on someone noticing it.",
        ),
        (f"{FACTS['jig_variants']:.0f} fixtures for "
         f"{FACTS['panels']:.0f} panels",
         "rails on the sawn point, not the bark"),
        30.0, (62.0, 38.0, 22.0), "ww_bench",
    ),
    Chapter(
        "flush", "00", "The cut that is never measured",
        "One end arrives finished. The other arrives too long, on purpose.",
        (
            "The two ends of a member are made in completely different places.",
            "The butt is cut before assembly, off the jig, to the angle its",
            "neighbour presents. It is the same cut for every member of a",
            "family, so it batches.",
            "The head is not cut at all. It arrives long, hangs off the board,",
            "and stays long while all three butts are pulled up tight and the",
            "pinwheel closes.",
            "Only then does a saw run flat along the fence and take the head off",
            "at the plane the neighbouring member has already established.",
            "Nothing is measured, and every error in stock length or butt angle",
            "walks away in the offcut instead of accumulating around the",
            "triangle.",
        ),
        (f"head arrives {FACTS['head_overfit_in']:.0f} in long",
         f"{FACTS['head_offcut_share'] * 100:.1f}% of raw length becomes offcut"),
        33.0, (55.0, 42.0, 16.0), "ww_flush",
    ),
    _math(
        "jig", "What the fixture is enforcing",
        "Twelve steps, three constraints, and the offcut that buys accuracy.",
        (
            "The fixture holds three things and nothing else: where the member",
            "sits across the panel, which way up it is turned, and the plane its",
            "head will be cut to.",
            "It is worth being precise about what the offcut buys. Every stick",
            "has some error in it. Cut both ends to a measurement and those",
            "errors add up around the triangle until the last corner does not",
            "close.",
            "Cut one end in place, against the neighbour, and the error has",
            "nowhere to accumulate. It leaves in the piece that falls on the",
            "floor.",
        ),
        steps_jig(), 38.0, (60.0, 40.0, 24.0), "ww_bench",
    ),

    # ---------------------------------------------- the building
    Chapter(
        "dome", "00", "What two trees make",
        "The building at the end of all of that.",
        (
            "So this is what the arithmetic buys. Two pines off the property,",
            "converted with a chainsaw and a flat board, become a shell you can",
            "stand up in.",
            "The floor area, the height and the member count all fall out of the",
            "longest useful piece the trees give, rather than the other way",
            "round. The building is sized by the wood, not the wood by the",
            "building.",
            "That inversion is the part I would most like to hand to somebody",
            "else, because it is what makes the whole thing available to anyone",
            "with a saw and some trees.",
        ),
        (f"{PLAN.trees} trees -> {PLAN.members_needed} members",
         f"{PLAN.floor_sqft:.0f} sq ft of floor"),
        29.0, (36.0, 24.0, 21.0), "wg_scale",
    ),
    _borrowed(
        "sizing", "The dome the trees size",
        "Solved backwards from the longest member the wood gives.",
        (
            "Normally you pick a dome diameter and then go and find members long",
            "enough for it. This is the same solve run the other way: start from",
            "the piece the tree actually yields and ask what shell that makes.",
            "The chord factors do not change, so the radius, the floor area and",
            "the member count all follow from one length.",
        ),
        wf_steps_dome(), 34.0, (36.0, 24.0, 21.0), "wg_scale",
    ),
    Chapter(
        "close", "00", "The shape is doing the work",
        "None of this is a claim that split wood is better wood.",
        (
            "A wedge from a small tree is not a stronger stick than a stud. It",
            "is a cheaper stick, a faster stick, a stick that leaves far more of",
            "the tree standing as structure instead of as shavings, and a stick",
            "that can be made without owning a factory.",
            "From a big enough tree it is also simply the stronger stick, and I",
            "gave you the diameter where that flips.",
            "But what makes it sufficient either way is the building. A",
            "triangulated shell puts its members mostly in axial load, doubles",
            "every interior edge, and asks only that the ends can be made to",
            "meet.",
            "So the honest version is not that I found a better board. It is",
            "that I picked a building that does not need one.",
        ),
        (f"{EARNINGS['net_usd_per_hour']:.0f} dollars an hour, in wood",
         f"{FACTS['members']:.0f} members, "
         f"{FACTS['jig_variants']:.0f} fixtures"),
        32.0, (36.0, 24.0, 21.0), "ww_close",
    ),
    _math(
        "summary", "The whole argument on one page",
        "Wood, machines, hands, rate, value, cost, strength, angle and cuts.",
        (
            "This is everything the film just showed, in the order it showed it,",
            "with the number attached to each line.",
            "One line still carries a condition rather than a boast: below about",
            "nine inches of trunk the single wedge is the weaker member and this",
            "stops working. That stays on the page.",
            "Change the assumptions and the money moves. Change the log or the",
            "dome and the geometry moves with it, because all of it is computed",
            "and none of it is typed in.",
        ),
        steps_close(), 40.0, (40.0, 26.0, 23.0), "ww_close",
    ),
)


CHAPTERS: tuple[Chapter, ...] = tuple(
    replace(chapter, number=f"{index + 1:02d}",
            narration=prose(chapter.narration))
    for index, chapter in enumerate(_AUTHORED)
)


def validate_wedge_why_lesson() -> None:
    """Prove the film before a frame of it renders."""
    validate_wedge_why_facts()

    lesson = WEDGE_WHY_LESSON
    lesson.validate()

    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug in the lesson"
    for chapter in lesson.chapters:
        assert chapter.narration, chapter.slug
        assert chapter.stage in SCENES, (chapter.slug, chapter.stage)
        if chapter.overlay == "math":
            assert len(chapter.equations) >= 5, chapter.slug
            assert len(chapter.equations[-1]) >= 30, chapter.slug

    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    own = {builder() for _name, builder in ALL_SCREENS}
    borrowed = {builder() for builder in BORROWED_SCREENS}
    assert own <= used, f"{len(own - used)} of this film's own screens go unused"
    assert used <= own | borrowed, (
        f"{len(used - own - borrowed)} screens come from nowhere")
    assert borrowed <= used, "a screen is imported and then never shown"

    # The argument has to arrive in an order that earns each claim: what the method
    # is before what it saves, what it saves before what it costs structurally, and
    # the honest structural number before the jig that makes it buildable.
    order = {slug: index for index, slug in enumerate(slugs)}
    # Every money screen must come after the table of what was measured and what was
    # guessed, or the film is asking to be believed before it has said on what terms.
    for money in ("value", "overhead", "middlemen_math"):
        assert order["assumptions"] < order[money], f"{money} before its assumptions"
    # The backstory earns the method; the method earns the argument.
    assert order["open"] < order["franken"] < order["bracket"] < order["square"]
    assert order["square"] < order["round"] < order["yield"] < order["split"]
    assert order["split"] < order["member"] < order["sector"] < order["short"]
    assert order["short"] < order["defects"] < order["panels"]
    assert order["panels"] < order["pinwheel"] < order["joint"] < order["duplicate"]
    assert order["duplicate"] < order["assumptions"] < order["chain"]
    assert order["chain"] < order["mills"] < order["middlemen"]
    assert order["middlemen"] < order["middlemen_math"] < order["sessions"]
    assert order["sessions"] < order["rate"] < order["worth"] < order["value"]
    assert order["value"] < order["store"] < order["overhead"] < order["stick"]
    assert order["stick"] < order["structure"] < order["turn"]
    assert order["turn"] < order["orientation"] < order["fold"]
    assert order["fold"] < order["dihedral"] < order["bench"]
    assert order["bench"] < order["flush"] < order["jig"] < order["dome"]
    assert order["dome"] < order["sizing"] < order["close"] < order["summary"]

    # The voice reads a chapter's headline, pauses, then reads the body. A headline
    # that summarises its own opening lines is therefore heard twice in a row, which
    # is what a doubled voice sounds like even when the audio is clean.
    common = {
        "this", "that", "with", "from", "they", "them", "then", "than",
        "what", "when", "which", "there", "their", "have", "been", "into",
        "over", "only", "just", "some", "more", "most", "will", "would",
        "could", "should", "about", "because", "does", "here", "every",
        "much", "many", "make", "makes", "your", "yours", "same", "than",
    }

    def _content_words(text: str) -> set:
        words = {word.strip(".,:;!?-—\"'").lower() for word in text.split()}
        return {word for word in words if len(word) > 3 and word not in common}

    for chapter in lesson.chapters:
        opening = " ".join(" ".join(chapter.narration).split(". ")[:2])
        headline = _content_words(chapter.promise)
        if not headline:
            continue
        shared = headline & _content_words(opening)
        overlap = len(shared) / len(headline)
        assert overlap < 0.5, (
            f"chapter {chapter.number} headline repeats its own opening: "
            f"{sorted(shared)}")

    class _App:
        def __init__(self):
            self.world_labels = []

    for stage, painter in SCENES.items():
        for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            assert opaque.vertices or transparent.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    # The cross-sections the pictures draw must be the cross-sections the screens
    # measure, or the film is illustrating one thing and claiming another.
    outline = _sector_outline("point_dome_in", 1.0)
    section = sector_section("point_dome_in")
    assert len(outline) == len(section.points)
    assert abs(outline[3][2] - section.points[3][1]) < 1.0e-9

    # The condition on the structural claim has to survive into the narration, not
    # just sit on a screen. An earlier cut of this film stated a flat "the wedge is
    # weaker", which was an artefact of the simulator's default trunk rather than a
    # fact about the method; the honest version is a diameter, and it has to be said.
    stick = next(c for c in lesson.chapters if c.slug == "stick")
    spoken = " ".join(stick.narration).lower()
    assert "crossover" in spoken and "diameter" in spoken, stick.narration
    assert "loses" in spoken, stick.narration


WEDGE_WHY_LESSON = Lesson(
    key="why",
    brand="WHY WEDGES",
    title="Why Wedges: A Dome That Does Not Need a Sawmill",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_wedge_why_lesson,
    report=wedge_why_report,
    snapshot_prefix="wedge_why",
    label_layout="declutter",
)
