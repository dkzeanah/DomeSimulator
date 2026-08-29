"""The assembly line, and what it costs the bodies that run it.

Twenty-four chapters about one question: when two people build one dome,
where does the energy actually go?  The line, the station, and the six
motions that make up every single part placement are drawn literally --
an articulated two-person crew squatting, lifting, carrying, reaching and
fastening -- and every joule and kilocalorie on screen is measured off
:mod:`two_v_demo.energetics`, which in turn is measured off the assembly
line's own element catalogue in ``al_build``.

The lesson is careful about one distinction throughout, because it is the
distinction most such estimates get wrong: the mechanical work is
computed and exact, the metabolic cost is modelled from published task
intensities, and the two are never quietly added together.
"""

from __future__ import annotations

import math

import numpy as np

import al_build as AL

from .energetics import (
    BODY_MASS_KG,
    CONCENTRIC_EFFICIENCY,
    EXTERNAL_CONSTANTS,
    JOULES_PER_KCAL,
    OVERHEAD_HEIGHT_M,
    PFD_ALLOWANCE,
    PFD_OVERHEAD_EXTRA,
    STATURE_M,
    SUSTAINABLE_SHIFT_WATTS,
    TWO_PERSON_LIFT_KG,
    build_energy,
    element_motions,
    energy_report,
    home_spec,
    met_watts,
    motion_cost,
    pandolf_watts,
    resting_metabolic_watts,
    validate_energetics,
)
from .figure import (
    place_figure,
    LIMB_GROUP,
    LIMB_GROUPS,
    POSES,
    SEGMENTS,
    draw_figure,
    draw_load,
    grip_point,
    joint_positions,
    validate_figure,
    walk_pose,
)
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    TriangleBatch,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


# ----------------------------------------------------------------------
# The line, measured once
# ----------------------------------------------------------------------

CREW = 2
SPEC = home_spec(1)
CATALOG, _MESH = AL.build_dome_catalog(SPEC)
ENERGY = build_energy(1, CREW)
STATION_ROWS = AL.station_cycle_times(CATALOG, CREW)
THROUGHPUT = AL.throughput(CATALOG, CREW)
STAGE_TITLE = {stage.key: stage.title for stage in SPEC.stages}
STAGE_COLOR = {stage.key: stage.color for stage in SPEC.stages}
STAGE_ENERGY = ENERGY.by_stage()


def _representative_element():
    """One ordinary frame member, picked without cherry-picking.

    The median-mass element of the biggest station is what the crew spends
    most of its day handling, so it is the honest thing to animate.
    """
    frame = [item for item in CATALOG.elements if item.stage == "frame"]
    frame.sort(key=lambda item: float(item.weight))
    return frame[len(frame) // 2]


DEMO_ELEMENT = _representative_element()
DEMO_MOTIONS = element_motions(DEMO_ELEMENT, crew=CREW)
DEMO_COSTS = tuple(motion_cost(motion) for motion in DEMO_MOTIONS)
DEMO_SECONDS = sum(motion.duration for motion in DEMO_MOTIONS)
DEMO_KCAL = sum(cost.kcal for cost in DEMO_COSTS)

RMR_WATTS = resting_metabolic_watts()
MOTION_EFFICIENCY = ENERGY.motion_efficiency()
MOTION_KCAL = ENERGY.by_motion()
LIMB_WORK = ENERGY.by_limb()

LIMB_COLOR = {"legs": CYAN, "trunk": AMBER, "arms": GREEN}


# The renderer's world is about five units across and its camera looks
# at a point 2.25 units up.  Drawing a 1.75 m person at this scale puts
# their chest on that point and makes them the size of the charts they
# stand beside.  Every figure-relative height in this module is in the
# same scaled units.
FIGURE_SCALE = 2.2

LOAD_MAX_LENGTH = 1.7


def _load_dims(dims):
    """Readable box for a carried part, keeping its real proportions."""
    values = sorted((abs(float(value)) for value in dims), reverse=True)
    while len(values) < 3:
        values.append(0.1)
    longest = max(values[0], 1e-3)
    shrink = min(1.0, LOAD_MAX_LENGTH / longest)
    # Long axis across the body rather than fore-and-aft: that is how a
    # strut is actually carried, and from this lesson's side-on camera it
    # recedes from the viewer instead of hiding the torso behind it.
    return (max(0.08, values[1] * shrink),
            max(0.12, values[0] * shrink),
            max(0.06, values[2] * shrink))





def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _fade(colour, alpha: float):
    return (colour[0], colour[1], colour[2], alpha)


# ----------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------

_place = place_figure


def _motion_at(progress: float, motions=DEMO_MOTIONS):
    """Which motion of the cycle a chapter's progress lands in."""
    total = sum(motion.duration for motion in motions) or 1.0
    cursor = progress * total
    for index, motion in enumerate(motions):
        if cursor < motion.duration or index == len(motions) - 1:
            return index, motion, clamp(cursor / max(motion.duration, 1e-6))
        cursor -= motion.duration
    return 0, motions[0], 0.0


def _pose_for(motion, local: float):
    """The body's shape part-way through one named motion."""
    if motion.start_pose == "walk" or motion.end_pose == "walk":
        return walk_pose(local * 2.0)
    if motion.start_pose == motion.end_pose and motion.is_locomotion:
        # Carrying: still a walk, but holding the load in front.
        stride = walk_pose(local * 2.0)
        return POSES[motion.end_pose].blend(stride, 0.35)
    start = POSES[motion.start_pose]
    end = POSES[motion.end_pose]
    return start.blend(end, smoothstep(local))


def _worker(
    batch: TriangleBatch,
    origin,
    pose,
    *,
    yaw: float = 0.0,
    highlight=None,
    load=None,
    load_colour=AMBER,
) -> dict:
    """Draw one crew member and whatever is in their hands."""
    joints = _place(
        joint_positions(pose, STATURE_M * FIGURE_SCALE), origin, yaw)
    draw_figure(batch, joints, highlight=highlight, scale=FIGURE_SCALE)
    if load is not None:
        draw_load(batch, joints,
                  tuple(value * FIGURE_SCALE for value in load), load_colour)
    return joints


def _floor(batch: TriangleBatch, centre, size, colour=(0.09, 0.15, 0.21, 1.0)) -> None:
    batch.box((float(centre[0]), float(centre[1]), -0.03),
              (float(size[0]), float(size[1]), 0.06), colour)


def _bars(
    app,
    batch: TriangleBatch,
    rows,
    *,
    origin=(0.0, 0.0, 0.0),
    width: float = 0.62,
    gap: float = 0.36,
    height: float = 4.4,
    reveal: float = 1.0,
    label_below: bool = True,
) -> None:
    """A row of vertical bars: rows are (label, value, colour, caption)."""
    values = [max(0.0, float(row[1])) for row in rows]
    peak = max(values) if values and max(values) > 0 else 1.0
    origin = np.asarray(origin, dtype=np.float64)
    span = len(rows) * (width + gap) - gap
    for index, row in enumerate(rows):
        label, value, colour = row[0], float(row[1]), row[2]
        caption = row[3] if len(row) > 3 else ""
        grown = max(0.0, value) / peak * height * clamp(reveal * 1.25)
        # +X points to screen left from this lesson's camera, so the
        # first row has to take the largest X to read first.
        x = origin[0] + span * 0.5 - index * (width + gap) - width * 0.5
        batch.box((x, origin[1], origin[2] + grown * 0.5),
                  (width, width, max(1e-3, grown)), colour)
        if caption:
            app.world_labels.append(WorldLabel(
                origin + np.array([x - origin[0], 0.0, grown + 0.42]),
                caption, _rgb(colour)))
        if label_below:
            app.world_labels.append(WorldLabel(
                origin + np.array([x - origin[0], 0.0, -0.52]),
                label, (150, 172, 190)))


def _station_pads(app, batch: TriangleBatch, highlight: int | None, reveal: float = 1.0):
    """The fifteen stations, laid out along the line."""
    stages = list(SPEC.stages)
    count = int(math.ceil(len(stages) * clamp(reveal)))
    spacing = 1.46
    span = (len(stages) - 1) * spacing
    positions = []
    for index, stage in enumerate(stages):
        x = -span * 0.5 + index * spacing
        positions.append(x)
        if index >= count:
            continue
        colour = stage.color
        bright = highlight is None or index == highlight
        pad = _fade(colour, 1.0 if bright else 0.30)
        batch.box((x, 0.0, 0.06), (1.44, 2.5, 0.12), pad)
        # A post at each pad so the line reads as stations, not stripes.
        batch.cylinder(np.array([x, -1.15, 0.0]), np.array([x, -1.15, 1.05]),
                       0.045, _fade(colour, 1.0 if bright else 0.25), 6)
        if bright:
            app.world_labels.append(WorldLabel(
                np.array([x, -1.15, 1.42]), f"{index + 1:02d}", _rgb(colour)))
    return positions


def _dome_hull(batch: TriangleBatch, origin, radius: float, progress: float,
               colour=CYAN, alpha: float = 0.30) -> None:
    """A quick dome shell, filled in from the base up as work proceeds."""
    origin = np.asarray(origin, dtype=np.float64)
    rings, segments = 6, 16
    filled = clamp(progress) * rings
    for ring in range(rings):
        lat_a = (math.pi * 0.5) * ring / rings
        lat_b = (math.pi * 0.5) * (ring + 1) / rings
        done = ring < filled
        shade = _fade(colour, alpha if done else 0.06)
        for step in range(segments):
            lon_a = math.tau * step / segments
            lon_b = math.tau * (step + 1) / segments

            def point(lat, lon):
                return origin + radius * np.array([
                    math.cos(lat) * math.cos(lon),
                    math.cos(lat) * math.sin(lon),
                    math.sin(lat),
                ])

            a, b = point(lat_a, lon_a), point(lat_a, lon_b)
            c, d = point(lat_b, lon_b), point(lat_b, lon_a)
            batch.triangle(a, b, c, shade, np.array([0.0, 0.0, 1.0]))
            batch.triangle(a, c, d, shade, np.array([0.0, 0.0, 1.0]))


def _stockpile(batch: TriangleBatch, origin, count: int = 6,
               colour=(0.62, 0.48, 0.30, 1.0)) -> None:
    origin = np.asarray(origin, dtype=np.float64)
    for index in range(count):
        batch.box((float(origin[0]), float(origin[1]),
                   0.09 + index * 0.11), (1.5, 0.42, 0.10), colour)


def _clock(app, batch: TriangleBatch, centre, fraction: float, label: str,
           colour=AMBER, radius: float = 0.9) -> None:
    """A pie-style share indicator, for 'this is most of the shift'."""
    centre = np.asarray(centre, dtype=np.float64)
    steps = 48
    filled = int(round(steps * clamp(fraction)))
    for step in range(steps):
        angle_a = math.tau * step / steps - math.pi * 0.5
        angle_b = math.tau * (step + 1) / steps - math.pi * 0.5
        shade = colour if step < filled else (0.20, 0.28, 0.36, 1.0)
        a = centre + radius * np.array([math.cos(angle_a), 0.0, math.sin(angle_a)])
        b = centre + radius * np.array([math.cos(angle_b), 0.0, math.sin(angle_b)])
        batch.triangle(centre, b, a, shade, np.array([0.0, 1.0, 0.0]))
    app.world_labels.append(WorldLabel(centre, label, _rgb(colour)))


def _limb_highlight(share: dict) -> dict:
    """Colour every body segment by which limb group it belongs to."""
    return {
        segment.name: LIMB_COLOR[LIMB_GROUP[segment.name]]
        for segment in SEGMENTS
    }


# ----------------------------------------------------------------------
# Act one -- the line
# ----------------------------------------------------------------------

def scene_line_overview(app, opaque, transparent, p: float) -> None:
    positions = _station_pads(app, opaque, None, smoothstep(p * 1.3))
    travel = ease_in_out(clamp(p * 1.1))
    # Keep the dome off the very ends of the line so it is never half out
    # of frame or hidden behind the teaching card.
    index = min(len(positions) - 4, max(2, int(travel * len(positions))))
    _dome_hull(transparent, np.array([positions[index], 0.0, 0.12]), 1.75,
               clamp((index + 1) / len(positions)))
    for offset, pose in ((-1.5, POSES["fasten"]), (1.5, POSES["reach_out"])):
        _worker(opaque, np.array([positions[index] + offset, 1.9, 0.12]),
                pose, yaw=180.0 if offset > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 5.6]),
                   f"{len(SPEC.stages)} STATIONS   {len(CATALOG.elements)} PARTS   "
                   f"{CATALOG.total_weight():,.0f} kg", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 4.6]),
                   f"{SPEC.name}  -  {SPEC.radius:.2f} m radius, {SPEC.frequency}V",
                   (169, 188, 203)),
    ])


def scene_line_why(app, opaque, transparent, p: float) -> None:
    """One person doing everything, against a line doing it in parallel."""
    reveal = smoothstep(p * 1.3)
    serial = THROUGHPUT["total_cycle_min"] / 60.0
    bottleneck = THROUGHPUT["bottleneck"]["cycle_min"] / 60.0
    _bars(app, opaque, (
        ("ONE CREW, ALL 15", serial, AMBER, f"{serial:.0f} h per dome"),
        ("A LINE, IN PARALLEL", bottleneck, GREEN,
         f"{bottleneck:.1f} h per dome"),
    ), origin=(0.0, 0.0, 0.0), width=1.5, gap=2.4, height=4.6, reveal=reveal)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.5]),
        f"SAME LABOUR, {serial / max(bottleneck, 1e-6):.0f}x THE RATE",
        (111, 235, 155)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.5]),
        "the line does not make the work smaller\nit makes the waiting smaller",
        (169, 188, 203)))


def scene_line_station(app, opaque, transparent, p: float) -> None:
    """One station, close enough to see what is in it."""
    _floor(opaque, (0.0, 0.0, 0.0), (14.0, 6.0))
    _stockpile(opaque, (5.2, 0.0, 0.0))
    _dome_hull(transparent, np.array([-4.4, 0.0, 0.0]), 2.6, 0.55)
    index, motion, local = _motion_at(p)
    pose = _pose_for(motion, local)
    # Both workers along X: separating them in Y would only stack them in
    # depth from this lesson's camera.
    _worker(opaque, np.array([1.5, 0.0, 0.0]), pose,
            load=_load_dims(DEMO_ELEMENT.dims) if motion.load_kg > 0 else None)
    _worker(opaque, np.array([-1.4, 0.0, 0.0]), POSES["reach_out"], yaw=180.0)
    app.world_labels.extend([
        WorldLabel(np.array([5.2, 0.0, 2.2]), "STOCKPILE", (169, 188, 203)),
        WorldLabel(np.array([-4.4, 0.0, 3.4]), "THE DOME", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 5.4]),
                   f"CREW OF {CREW}", (111, 235, 155)),
    ])


def scene_line_bottleneck(app, opaque, transparent, p: float) -> None:
    rows = sorted(STATION_ROWS, key=lambda row: -row["cycle_min"])[:8]
    slowest = rows[0]["key"]
    _bars(app, opaque, tuple(
        (row["key"][:9].upper(), row["cycle_min"] / 60.0,
         GREEN if row["key"] == slowest else _fade(STAGE_COLOR[row["key"]], 1.0),
         f"{row['cycle_min'] / 60.0:.1f} h")
        for row in rows
    ), height=4.2, reveal=smoothstep(p * 1.3), width=0.72, gap=0.42)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.4]),
        f"THE LINE RUNS AT THE SPEED OF {slowest.upper()}", (111, 235, 155)))


# ----------------------------------------------------------------------
# Act two -- the anatomy of one task
# ----------------------------------------------------------------------

def scene_line_cycle(app, opaque, transparent, p: float) -> None:
    """All six motions of one placement, side by side."""
    _floor(opaque, (0.0, 0.0, 0.0), (14.0, 4.0))
    reveal = int(math.ceil(len(DEMO_MOTIONS) * clamp(p * 1.25)))
    spacing = 2.05
    span = (len(DEMO_MOTIONS) - 1) * spacing
    for index, (motion, cost) in enumerate(zip(DEMO_MOTIONS, DEMO_COSTS)):
        if index >= reveal:
            continue
        x = span * 0.5 - index * spacing
        pose = _pose_for(motion, 0.65)
        _worker(opaque, np.array([x, 0.0, 0.0]), pose,
                load=_load_dims(DEMO_ELEMENT.dims) if motion.load_kg > 0 else None)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 2.35]),
            f"{index + 1}. {motion.name.upper()}\n{motion.duration:.1f} s\n"
            f"{cost.kcal:.2f} kcal",
            _rgb(CYAN if motion.load_kg else AMBER)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.1]),
        f"ONE PART: {DEMO_SECONDS:.0f} s, {DEMO_KCAL:.1f} kcal   x "
        f"{len(CATALOG.elements)} PARTS", (111, 235, 155)))


def scene_line_walk(app, opaque, transparent, p: float) -> None:
    motion = DEMO_MOTIONS[0]
    cost = DEMO_COSTS[0]
    _floor(opaque, (0.0, 0.0, 0.0), (12.0, 3.0))
    _stockpile(opaque, (4.2, 0.0, 0.0))
    travel = ease_in_out(clamp(p * 1.15))
    x = -4.0 + travel * 8.0
    _worker(opaque, np.array([x, 0.0, 0.0]), walk_pose(p * 6.0))
    for step in range(9):
        mark = -4.0 + step
        opaque.box((mark, 0.0, 0.02), (0.10, 0.5, 0.04),
                   _fade(CYAN, 0.9 if mark <= x else 0.20))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.6]),
                   f"{motion.distance:.1f} m EACH WAY", (61, 211, 255)),
        WorldLabel(np.array([x, 0.0, 3.9]),
                   f"{cost.watts:.0f} W", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   f"{MOTION_KCAL['walk_out']:,.0f} kcal over the whole dome",
                   (169, 188, 203)),
    ])


def scene_line_lift(app, opaque, transparent, p: float) -> None:
    """The lift, slowed down, with the working limbs coloured."""
    motion = DEMO_MOTIONS[1]
    cost = DEMO_COSTS[1]
    _floor(opaque, (0.0, 0.0, 0.0), (6.0, 4.0))
    local = clamp(p * 1.2)
    pose = _pose_for(motion, local)
    joints = _worker(opaque, np.array([0.0, 0.0, 0.0]), pose,
                     highlight=_limb_highlight(cost.by_limb()),
                     load=_load_dims(DEMO_ELEMENT.dims))
    limb = cost.by_limb()
    for index, group in enumerate(LIMB_GROUPS):
        app.world_labels.append(WorldLabel(
            np.array([3.1, 0.0, 4.3 - index * 0.62]),
            f"{group.upper()}  {limb[group]:.1f} J", _rgb(LIMB_COLOR[group])))
    grip = grip_point(joints)
    app.world_labels.extend([
        WorldLabel(grip + np.array([0.9, 0.0, 0.0]),
                   f"{motion.load_kg:.1f} kg", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, 5.2]),
                   f"MECHANICAL WORK {cost.mechanical_joules:.0f} J   "
                   f"FUEL {cost.metabolic_joules:.0f} J", (111, 235, 155)),
    ])


def scene_line_carry(app, opaque, transparent, p: float) -> None:
    """Carrying, and why the load term is not linear."""
    _floor(opaque, (3.4, 2.6, 0.0), (5.0, 3.0))
    travel = ease_in_out(clamp(p * 1.15))
    x = 2.2 + travel * 2.4
    _worker(opaque, np.array([x, 2.6, 0.0]),
            _pose_for(DEMO_MOTIONS[2], p * 3.0), load=_load_dims(DEMO_ELEMENT.dims))
    loads = (0.0, 10.0, 20.0, 30.0, 40.0)
    _bars(app, opaque, tuple(
        (f"{load:.0f} kg", pandolf_watts(BODY_MASS_KG, load, 1.05), AMBER,
         f"{pandolf_watts(BODY_MASS_KG, load, 1.05):.0f} W")
        for load in loads
    ), origin=(-3.6, 0.0, 0.0), height=3.6, reveal=smoothstep(p * 1.3),
        width=0.72, gap=0.62)
    app.world_labels.append(WorldLabel(
        np.array([-3.6, 0.0, 5.2]),
        "PANDOLF: THE LOAD TERM IS QUADRATIC", (111, 235, 155)))


def scene_line_position(app, opaque, transparent, p: float) -> None:
    motion = DEMO_MOTIONS[3]
    _floor(opaque, (0.0, 0.0, 0.0), (6.0, 4.0))
    _dome_hull(transparent, np.array([1.9, 0.0, 0.0]), 2.2, 0.7)
    local = clamp(p * 1.2)
    _worker(opaque, np.array([-0.5, 0.0, 0.0]), _pose_for(motion, local),
            load=_load_dims(DEMO_ELEMENT.dims))
    height = float(DEMO_ELEMENT.centroid[2])
    opaque.cylinder(np.array([-1.7, 0.0, 0.0]), np.array([-1.7, 0.0, height]),
                    0.03, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-1.7, 0.0, height + 0.35]),
                   f"LANDS AT {height:.2f} m", (61, 211, 255)),
        WorldLabel(np.array([1.9, 0.0, 5.0]),
                   f"OVERHEAD ABOVE {OVERHEAD_HEIGHT_M:.2f} m", (255, 177, 62)),
    ])


def scene_line_fasten(app, opaque, transparent, p: float) -> None:
    """Where ninety per cent of the shift actually goes."""
    motion = DEMO_MOTIONS[4]
    _floor(opaque, (-2.0, 0.0, 0.0), (5.0, 4.0))
    wobble = math.sin(p * math.tau * 3.0) * 0.10
    pose = POSES[motion.end_pose].blend(POSES["reach_out"], 0.18 + wobble)
    _worker(opaque, np.array([-2.0, 0.0, 0.0]), pose)
    share = MOTION_KCAL["fasten"] / max(ENERGY.kcal_per_worker, 1e-9)
    _clock(app, opaque, np.array([2.4, 0.0, 2.0]), smoothstep(p * 1.3) * share,
           f"{share * 100:.0f} %\nOF THE FUEL", AMBER, 1.35)
    app.world_labels.extend([
        WorldLabel(np.array([-2.0, 0.0, 4.6]),
                   f"{motion.duration:.0f} s PER PART", (61, 211, 255)),
        WorldLabel(np.array([2.4, 0.0, 0.15]),
                   f"{MOTION_KCAL['fasten']:,.0f} kcal", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.2]),
                   "and it raises nothing at all", (169, 188, 203)),
    ])


def scene_line_allowance(app, opaque, transparent, p: float) -> None:
    reveal = smoothstep(p * 1.3)
    _floor(opaque, (-3.2, 0.0, 0.0), (3.4, 3.4))
    _worker(opaque, np.array([-3.2, 0.0, 0.0]), POSES["stand"])
    _bars(app, opaque, (
        ("TASK", 1.0, CYAN, "100 %"),
        ("+ ALLOWANCE", 1.0 + PFD_ALLOWANCE, AMBER,
         f"+{PFD_ALLOWANCE * 100:.0f} %"),
        ("+ OVERHEAD", 1.0 + PFD_ALLOWANCE + PFD_OVERHEAD_EXTRA, RED,
         f"+{(PFD_ALLOWANCE + PFD_OVERHEAD_EXTRA) * 100:.0f} %"),
    ), origin=(1.4, 0.0, 0.0), height=3.8, reveal=reveal, width=0.9, gap=0.7)
    app.world_labels.extend([
        WorldLabel(np.array([1.4, 0.0, 4.7]),
                   f"{ENERGY.rest_seconds / 3600.0:.0f} h OF THE BUILD IS RECOVERY",
                   (111, 235, 155)),
        WorldLabel(np.array([1.4, 0.0, -1.3]),
                   "a rate set without it cannot be held for a shift",
                   (169, 188, 203)),
    ])


# ----------------------------------------------------------------------
# Act three -- the body
# ----------------------------------------------------------------------

def scene_line_skeleton(app, opaque, transparent, p: float) -> None:
    """The figure, and what each piece of it weighs."""
    _floor(opaque, (0.0, 0.0, 0.0), (5.0, 4.0))
    joints = _worker(opaque, np.array([0.0, 0.0, 0.0]), POSES["stand"],
                     highlight=_limb_highlight(LIMB_WORK))
    shown = int(math.ceil(6 * clamp(p * 1.3)))
    picks = (("head", "head_top", 1.9), ("trunk", "chest", -2.4),
             ("l_upper_arm", "l_elbow", -2.6), ("l_forearm", "l_wrist", -2.6),
             ("l_thigh", "l_knee", 2.4), ("l_shank", "l_ankle", 2.4))
    for index, (segment_name, joint_name, offset) in enumerate(picks):
        if index >= shown:
            continue
        segment = next(item for item in SEGMENTS if item.name == segment_name)
        app.world_labels.append(WorldLabel(
            joints[joint_name] + np.array([offset, 0.0, 0.12]),
            f"{segment_name.replace('_', ' ')}\n"
            f"{segment.mass(BODY_MASS_KG):.1f} kg",
            _rgb(LIMB_COLOR[LIMB_GROUP[segment_name]])))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.6]),
        f"{BODY_MASS_KG:.0f} kg, {STATURE_M:.2f} m", (61, 211, 255)))


def scene_line_selflift(app, opaque, transparent, p: float) -> None:
    """Most of what a body lifts is the body."""
    reveal = smoothstep(p * 1.3)
    body_work = sum(
        sum(cost.segment_work.values()) for cost in DEMO_COSTS
    )
    load_work = sum(cost.load_work for cost in DEMO_COSTS)
    _bars(app, opaque, (
        ("YOUR OWN BODY", body_work, CYAN, f"{body_work:.0f} J"),
        ("THE PART", load_work, AMBER, f"{load_work:.0f} J"),
    ), height=4.0, reveal=reveal, width=1.4, gap=2.0)
    _worker(opaque, np.array([-4.4, 0.0, 0.0]), POSES["squat_deep"],
            load=_load_dims(DEMO_ELEMENT.dims))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.0]),
        f"ONE PLACEMENT OF A {float(DEMO_ELEMENT.weight):.1f} kg PART",
        (111, 235, 155)))


def scene_line_limbs(app, opaque, transparent, p: float) -> None:
    reveal = smoothstep(p * 1.3)
    total = sum(LIMB_WORK.values()) or 1.0
    _worker(opaque, np.array([-4.2, 0.0, 0.0]), POSES["squat_mid"],
            highlight=_limb_highlight(LIMB_WORK), load=_load_dims(DEMO_ELEMENT.dims))
    _bars(app, opaque, tuple(
        (group.upper(), LIMB_WORK[group], LIMB_COLOR[group],
         f"{LIMB_WORK[group] / total * 100:.0f} %")
        for group in LIMB_GROUPS
    ), origin=(1.2, 0.0, 0.0), height=4.0, reveal=reveal, width=1.0, gap=0.9)
    app.world_labels.append(WorldLabel(
        np.array([1.2, 0.0, 5.0]),
        "WHO DOES THE LIFTING WORK", (111, 235, 155)))


def scene_line_team(app, opaque, transparent, p: float) -> None:
    """The threshold where one person stops lifting alone."""
    _floor(opaque, (0.0, 0.0, 0.0), (7.0, 4.0))
    heavy = max(CATALOG.elements, key=lambda item: float(item.weight))
    local = clamp(p * 1.2)
    pose = POSES["squat_mid"].blend(POSES["team_carry"], smoothstep(local))
    left = _worker(opaque, np.array([-2.0, 0.0, 0.0]), pose, yaw=0.0)
    right = _worker(opaque, np.array([2.0, 0.0, 0.0]), pose, yaw=180.0)
    centre = (grip_point(left) + grip_point(right)) * 0.5
    opaque.box((float(centre[0]), float(centre[1]), float(centre[2]) + 0.12),
               (4.4, 0.65, 0.30), AMBER)
    app.world_labels.extend([
        WorldLabel(centre + np.array([0.0, 0.0, 1.5]),
                   f"{float(heavy.weight):.0f} kg  ->  "
                   f"{float(heavy.weight) / CREW:.0f} kg EACH", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, 5.4]),
                   f"TWO-PERSON LIFT ABOVE {TWO_PERSON_LIFT_KG:.0f} kg",
                   (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   f"one worker still raises "
                   f"{ENERGY.lifted_mass_kg:,.0f} kg of the "
                   f"{ENERGY.total_mass_kg:,.0f} kg dome", (169, 188, 203)),
    ])


def scene_line_overhead(app, opaque, transparent, p: float) -> None:
    """The same task, at two heights, costing two different amounts."""
    _floor(opaque, (0.0, 0.0, 0.0), (8.0, 4.0))
    low = motion_cost(DEMO_MOTIONS[4])
    high_motion = type(DEMO_MOTIONS[4])(
        "fasten_high", "Fix it in place overhead", "fasten_high",
        "fasten_high", DEMO_MOTIONS[4].duration, 4.2, 0.0, 0.0, "")
    high = motion_cost(high_motion)
    _worker(opaque, np.array([-2.0, 0.0, 0.0]), POSES["fasten"])
    _worker(opaque, np.array([2.0, 0.0, 0.0]), POSES["fasten_high"])
    app.world_labels.extend([
        WorldLabel(np.array([-2.0, 0.0, 4.4]),
                   f"AT THE DECK\n{low.watts:.0f} W", (61, 211, 255)),
        WorldLabel(np.array([2.0, 0.0, 5.0]),
                   f"OVERHEAD\n{high.watts:.0f} W", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, 5.8]),
                   f"+{(high.watts / max(low.watts, 1e-9) - 1) * 100:.0f} % "
                   "FOR THE SAME PART", (111, 235, 155)),
    ])


# ----------------------------------------------------------------------
# Act four -- the ledger
# ----------------------------------------------------------------------

def scene_line_work(app, opaque, transparent, p: float) -> None:
    """m g h, drawn: the part of this that is exact."""
    _floor(opaque, (-2.6, 0.0, 0.0), (4.0, 3.4))
    rise = ease_in_out(clamp(p * 1.2))
    height = float(DEMO_ELEMENT.centroid[2]) * rise
    mass = float(DEMO_ELEMENT.weight)
    opaque.box((1.6, 0.0, height + 0.2), (1.5, 0.6, 0.28), AMBER)
    opaque.cylinder(np.array([0.4, 0.0, 0.0]), np.array([0.4, 0.0, height + 0.2]),
                    0.03, CYAN, 6)
    _worker(opaque, np.array([-2.6, 0.0, 0.0]), POSES["reach_out"])
    app.world_labels.extend([
        WorldLabel(np.array([0.4, 0.0, height * 0.5 + 0.2]),
                   f"h = {height:.2f} m", (61, 211, 255)),
        WorldLabel(np.array([1.6, 0.0, height + 0.75]),
                   f"m = {mass:.1f} kg", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, 5.6]),
                   f"W = m g h = {mass * 9.80665 * height:,.0f} J",
                   (111, 235, 155)),
    ])


def scene_line_model(app, opaque, transparent, p: float) -> None:
    """The honesty chapter: what is computed, and what is assumed."""
    reveal = int(math.ceil(5 * clamp(p * 1.3)))
    computed = ("element mass", "placement height", "walk distance",
                "segment masses", "m g h")
    assumed = ("muscle efficiency", "task intensities (METs)",
               "Pandolf regression", "resting rate", "rest allowance")
    for index in range(min(reveal, 5)):
        z = 3.4 - index * 0.62
        opaque.box((-2.6, 0.0, z), (2.9, 0.4, 0.42), _fade(CYAN, 0.85))
        opaque.box((2.6, 0.0, z), (2.9, 0.4, 0.42), _fade(AMBER, 0.85))
        app.world_labels.append(WorldLabel(
            np.array([-2.6, 0.0, z]), computed[index], (61, 211, 255)))
        app.world_labels.append(WorldLabel(
            np.array([2.6, 0.0, z]), assumed[index], (255, 177, 62)))
    app.world_labels.extend([
        WorldLabel(np.array([-2.6, 0.0, 4.3]), "COMPUTED HERE", (61, 211, 255)),
        WorldLabel(np.array([2.6, 0.0, 4.3]), "TAKEN ON AUTHORITY", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -0.5]),
                   f"{len(EXTERNAL_CONSTANTS)} external constants, "
                   "every one of them named in the report", (169, 188, 203)),
    ])


def scene_line_efficiency(app, opaque, transparent, p: float) -> None:
    """Nineteen per cent during the lift; a fifth of one per cent overall."""
    reveal = smoothstep(p * 1.3)
    _bars(app, opaque, (
        ("MUSCLE CEILING", CONCENTRIC_EFFICIENCY * 100.0, MUTED,
         f"{CONCENTRIC_EFFICIENCY * 100:.0f} %"),
        ("DURING THE LIFT", MOTION_EFFICIENCY["lift"] * 100.0, GREEN,
         f"{MOTION_EFFICIENCY['lift'] * 100:.1f} %"),
        ("WHOLE BUILD", ENERGY.mechanical_fraction * 100.0, RED,
         f"{ENERGY.mechanical_fraction * 100:.2f} %"),
    ), height=4.2, reveal=reveal, width=1.1, gap=1.1)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.2]),
        "MECHANICAL WORK AS A SHARE OF THE FOOD", (111, 235, 155)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.4]),
        "the gap is posture, grip and holding still", (169, 188, 203)))


def scene_line_motions(app, opaque, transparent, p: float) -> None:
    """The whole build's fuel, split by which motion spent it."""
    order = sorted(MOTION_KCAL.items(), key=lambda kv: -kv[1])
    palette = (AMBER, PURPLE, CYAN, GREEN, RED, MUTED, WHITE)
    _bars(app, opaque, tuple(
        (name.upper(), kcal, palette[index % len(palette)],
         f"{kcal / max(ENERGY.kcal_per_worker, 1e-9) * 100:.0f} %")
        for index, (name, kcal) in enumerate(order)
    ), height=4.2, reveal=smoothstep(p * 1.3), width=0.66, gap=0.42)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.2]),
        f"{ENERGY.kcal_per_worker:,.0f} kcal PER WORKER, PER DOME",
        (111, 235, 155)))


def scene_line_stations(app, opaque, transparent, p: float) -> None:
    rows = sorted(STAGE_ENERGY.items(), key=lambda kv: -kv[1]["kcal"])[:9]
    _bars(app, opaque, tuple(
        (key[:9].upper(), row["kcal"], _fade(STAGE_COLOR[key], 1.0),
         f"{row['kcal']:,.0f}")
        for key, row in rows
    ), height=4.2, reveal=smoothstep(p * 1.3), width=0.68, gap=0.40)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.2]),
        "KILOCALORIES PER STATION, PER DOME", (111, 235, 155)))


def scene_line_shift(app, opaque, transparent, p: float) -> None:
    """One working day, measured against what a body can sustain."""
    reveal = smoothstep(p * 1.3)
    _worker(opaque, np.array([-4.4, 0.0, 0.0]), POSES["carry"],
            load=_load_dims(DEMO_ELEMENT.dims))
    _bars(app, opaque, (
        ("RESTING", RMR_WATTS, MUTED, f"{RMR_WATTS:.0f} W"),
        ("THIS LINE", ENERGY.mean_watts, GREEN, f"{ENERGY.mean_watts:.0f} W"),
        ("SUSTAINABLE", SUSTAINABLE_SHIFT_WATTS, AMBER,
         f"{SUSTAINABLE_SHIFT_WATTS:.0f} W"),
    ), origin=(1.0, 0.0, 0.0), height=4.0, reveal=reveal, width=1.0, gap=0.9)
    app.world_labels.extend([
        WorldLabel(np.array([1.0, 0.0, 5.0]),
                   f"{ENERGY.mean_met:.2f} METs SUSTAINED", (111, 235, 155)),
        WorldLabel(np.array([1.0, 0.0, -1.3]),
                   f"{ENERGY.kcal_per_shift:,.0f} kcal per shift, "
                   f"{ENERGY.shifts:.1f} shifts per dome", (169, 188, 203)),
    ])


def scene_line_food(app, opaque, transparent, p: float) -> None:
    """The total, in units a person can actually picture."""
    reveal = clamp(p * 1.25)
    rows = ENERGY.food_equivalent()
    loaves = int(rows[0][1] * reveal)
    columns = 26
    for index in range(min(loaves, 260)):
        column = index % columns
        row = index // columns
        opaque.box((-4.6 + column * 0.36, 0.0, 0.22 + row * 0.30),
                   (0.30, 0.5, 0.24), (0.78, 0.62, 0.35, 1.0))
    _worker(opaque, np.array([5.2, 0.0, 0.0]), POSES["stand"])
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.2]),
                   f"{ENERGY.kcal_crew:,.0f} kcal FOR THE CREW, PER DOME",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   "   ".join(f"{amount:,.0f} {label.split(' at ')[0]}"
                              for label, amount in rows[:2]),
                   (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.6]),
                   f"{rows[2][1]:.0f} days of a 2,500 kcal diet",
                   (169, 188, 203)),
    ])


def scene_line_recap(app, opaque, transparent, p: float) -> None:
    positions = _station_pads(app, opaque, None, 1.0)
    index = min(len(positions) - 4, max(2, int(clamp(p) * len(positions))))
    _dome_hull(transparent, np.array([positions[index], 0.0, 0.12]), 1.75,
               clamp(p * 1.2))
    for offset in (-1.5, 1.5):
        _worker(opaque, np.array([positions[index] + offset, 1.9, 0.12]),
                POSES["reach_out"], yaw=180.0 if offset > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 5.8]),
                   f"{len(CATALOG.elements)} PARTS   "
                   f"{ENERGY.hours_per_worker:.0f} h   "
                   f"{ENERGY.kcal_crew:,.0f} kcal", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 4.7]),
                   "every number traceable to a part, a height, or a "
                   "named constant", (111, 235, 155)),
    ])


SCENES = {
    "line_overview": scene_line_overview,
    "line_why": scene_line_why,
    "line_station": scene_line_station,
    "line_bottleneck": scene_line_bottleneck,
    "line_cycle": scene_line_cycle,
    "line_walk": scene_line_walk,
    "line_lift": scene_line_lift,
    "line_carry": scene_line_carry,
    "line_position": scene_line_position,
    "line_fasten": scene_line_fasten,
    "line_allowance": scene_line_allowance,
    "line_skeleton": scene_line_skeleton,
    "line_selflift": scene_line_selflift,
    "line_limbs": scene_line_limbs,
    "line_team": scene_line_team,
    "line_overhead": scene_line_overhead,
    "line_work": scene_line_work,
    "line_model": scene_line_model,
    "line_efficiency": scene_line_efficiency,
    "line_motions": scene_line_motions,
    "line_stations": scene_line_stations,
    "line_shift": scene_line_shift,
    "line_food": scene_line_food,
    "line_recap": scene_line_recap,
}


def line_equations(app, stage: str) -> list[str]:
    if stage == "line_overview":
        return [
            f"stations     = {len(SPEC.stages)}   crew {CREW} each",
            f"per station  = {len(CATALOG.elements) / len(SPEC.stages):.0f} parts",
            f"heaviest     = {max(float(item.weight) for item in CATALOG.elements):,.0f} kg",
        ]
    if stage == "line_why":
        return [
            f"total cycle   = {THROUGHPUT['total_cycle_min'] / 60.0:,.1f} h",
            f"bottleneck    = {THROUGHPUT['bottleneck']['key']} at "
            f"{THROUGHPUT['bottleneck']['cycle_min'] / 60.0:.1f} h",
            f"single flow   = {THROUGHPUT['single_flow_per_year']:,.0f} /year",
            f"pipelined     = {THROUGHPUT['pipelined_per_year']:,.0f} /year",
        ]
    if stage == "line_bottleneck":
        return [
            f"{row['key']:<11} {row['cycle_min'] / 60.0:6.2f} h  "
            f"{row['elements']:>4} parts"
            for row in sorted(STATION_ROWS,
                              key=lambda item: -item["cycle_min"])[:6]
        ]
    if stage == "line_cycle":
        return [
            f"{motion.name:<9} {motion.duration:6.1f} s  {cost.kcal:6.2f} kcal"
            for motion, cost in zip(DEMO_MOTIONS, DEMO_COSTS)
        ]
    if stage == "line_walk":
        motion = DEMO_MOTIONS[0]
        return [
            f"distance = {motion.distance:.2f} m",
            f"speed    = {motion.speed:.2f} m/s",
            f"Pandolf  = {DEMO_COSTS[0].watts:.0f} W",
            f"cost     = {DEMO_COSTS[0].kcal:.3f} kcal",
        ]
    if stage == "line_lift":
        cost = DEMO_COSTS[1]
        limb = cost.by_limb()
        return [
            f"load        = {DEMO_MOTIONS[1].load_kg:.1f} kg",
            f"work        = {cost.mechanical_joules:.1f} J",
            f"fuel        = {cost.metabolic_joules:.0f} J",
        ] + [f"{group:<11} = {limb[group]:6.1f} J" for group in LIMB_GROUPS]
    if stage == "line_carry":
        return [
            f"{load:2.0f} kg -> {pandolf_watts(BODY_MASS_KG, load, 1.05):5.0f} W"
            for load in (0.0, 10.0, 20.0, 30.0, 40.0)
        ]
    if stage == "line_fasten":
        return [
            f"fasten time  = {DEMO_MOTIONS[4].duration:.0f} s per part",
            f"intensity    = {DEMO_MOTIONS[4].met:.1f} METs",
            f"mechanical   = {MOTION_EFFICIENCY['fasten'] * 100:.2f} %",
            f"whole dome   = {MOTION_KCAL['fasten']:,.0f} kcal",
        ]
    if stage == "line_allowance":
        return [
            f"PF&D allowance   = {PFD_ALLOWANCE * 100:.0f} %",
            f"overhead extra   = {PFD_OVERHEAD_EXTRA * 100:.0f} %",
            f"recovery total   = {ENERGY.rest_seconds / 3600.0:.1f} h",
            f"share of build   = {ENERGY.rest_fraction * 100:.1f} %",
        ]
    if stage == "line_skeleton":
        return [
            f"{segment.name:<12} {segment.mass(BODY_MASS_KG):5.2f} kg"
            for segment in SEGMENTS[:6]
        ]
    if stage == "line_limbs":
        total = sum(LIMB_WORK.values()) or 1.0
        return [
            f"{group:<7} {LIMB_WORK[group] / 1000.0:8.1f} kJ  "
            f"{LIMB_WORK[group] / total * 100:5.1f} %"
            for group in LIMB_GROUPS
        ]
    if stage == "line_team":
        heavy = max(CATALOG.elements, key=lambda item: float(item.weight))
        return [
            f"threshold     = {TWO_PERSON_LIFT_KG:.0f} kg",
            f"heaviest part = {float(heavy.weight):,.0f} kg ({heavy.label})",
            f"dome mass     = {ENERGY.total_mass_kg:,.0f} kg",
            f"one worker    = {ENERGY.lifted_mass_kg:,.0f} kg raised",
        ]
    if stage == "line_efficiency":
        return [
            f"muscle ceiling   = {CONCENTRIC_EFFICIENCY * 100:.0f} %",
            f"during the lift  = {MOTION_EFFICIENCY['lift'] * 100:.2f} %",
            f"whole build      = {ENERGY.mechanical_fraction * 100:.3f} %",
            f"work done        = {ENERGY.mechanical_joules / 1e6:.3f} MJ",
        ]
    if stage == "line_motions":
        return [
            f"{name:<9} {kcal:8,.0f} kcal  "
            f"{kcal / max(ENERGY.kcal_per_worker, 1e-9) * 100:5.1f} %"
            for name, kcal in sorted(MOTION_KCAL.items(), key=lambda kv: -kv[1])
        ]
    if stage == "line_stations":
        return [
            f"{key:<11} {row['kcal']:7,.0f} kcal  {row['seconds'] / 3600:5.1f} h"
            for key, row in sorted(STAGE_ENERGY.items(),
                                   key=lambda kv: -kv[1]["kcal"])[:6]
        ]
    if stage == "line_shift":
        return [
            f"mean rate    = {ENERGY.mean_watts:.0f} W = {ENERGY.mean_met:.2f} METs",
            f"per shift    = {ENERGY.kcal_per_shift:,.0f} kcal",
            f"shifts       = {ENERGY.shifts:.1f} per dome",
            f"resting      = {RMR_WATTS:.0f} W",
        ]
    if stage in ("line_food", "line_recap"):
        return [
            f"per worker   = {ENERGY.kcal_per_worker:,.0f} kcal",
            f"crew of {CREW}    = {ENERGY.kcal_crew:,.0f} kcal",
        ] + [f"{amount:9,.0f}  {label}"
             for label, amount in ENERGY.food_equivalent()]
    return []


# ----------------------------------------------------------------------
# The lesson
# ----------------------------------------------------------------------

# Every figure in the narration below is interpolated from the model at
# import time.  Nothing here is a typed-in number, so the script cannot
# drift away from the calculation the way a hand-written one would.
_ELEMENT_KG = float(DEMO_ELEMENT.weight)
_HEAVIEST = max(CATALOG.elements, key=lambda item: float(item.weight))
_FASTEN_SHARE = MOTION_KCAL["fasten"] / max(ENERGY.kcal_per_worker, 1e-9) * 100.0
_SERIAL_H = THROUGHPUT["total_cycle_min"] / 60.0
_BOTTLENECK = THROUGHPUT["bottleneck"]
_LIMB_TOTAL = sum(LIMB_WORK.values()) or 1.0
_FOOD = ENERGY.food_equivalent()
_LIFT_HEIGHT = float(DEMO_ELEMENT.centroid[2])
_LIFT_WORK = _ELEMENT_KG * 9.80665 * _LIFT_HEIGHT


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "overview", "01", "One building, fifteen stations",
        f"{len(CATALOG.elements)} parts, {CATALOG.total_weight():,.0f} kilograms, "
        f"and two people at every station.",
        (
            f"This is the {SPEC.name}: a {SPEC.radius:.2f} metre {SPEC.frequency}V dome home",
            f"that leaves the line as {len(CATALOG.elements)} placed parts weighing",
            f"{CATALOG.total_weight():,.0f} kilograms in total. It passes through",
            f"{len(SPEC.stages)} stations, and a crew of {CREW} works each one.",
            "Over the next chapters we are going to follow those two people through",
            "every motion they make, and account for the energy each motion costs them.",
        ),
        (f"parts = {len(CATALOG.elements)}",
         f"mass = {CATALOG.total_weight():,.0f} kg",
         f"labour = {CATALOG.labor_minutes() / 60.0:,.0f} h"),
        20.0, (84.0, 30.0, 24.0), "line_overview",
    ),
    Chapter(
        "why", "02", "What a line actually buys you",
        "Not less work. Less waiting.",
        (
            f"One crew doing all {len(SPEC.stages)} stations spends {_SERIAL_H:,.0f} hours",
            "on a dome, and the next dome cannot start until the last one is finished.",
            f"Split the same work across {len(SPEC.stages)} stations and a dome comes off",
            f"the end every {_BOTTLENECK['cycle_min'] / 60.0:.1f} hours instead.",
            "The total labour did not change at all. What changed is that nobody",
            "is standing still waiting for someone else to finish.",
        ),
        (f"serial = {_SERIAL_H:,.0f} h per dome",
         f"pipelined = {_BOTTLENECK['cycle_min'] / 60.0:.1f} h per dome"),
        20.0, (90.0, 22.0, 13.0), "line_why",
    ),
    Chapter(
        "station", "03", "Inside one station",
        "A stockpile, a dome, and two people who never leave.",
        (
            "Every station holds the same three things: the material waiting in a",
            "stockpile, the dome that arrived from the station before, and the crew.",
            "The crew does not follow the dome down the line. They stay, they learn",
            "one job completely, and a different dome arrives in front of them.",
            "That is the trade a line makes: depth of skill against variety of work.",
        ),
        (f"crew = {CREW}", f"stockpile at {DEMO_MOTIONS[0].distance:.1f} m"),
        20.0, (96.0, 24.0, 17.0), "line_station",
    ),
    Chapter(
        "bottleneck", "04", "The line runs at the speed of its slowest station",
        f"Here that is {_BOTTLENECK['key']}, and nothing else matters until it changes.",
        (
            f"Station cycle times are not equal. The {_BOTTLENECK['key']} station takes",
            f"{_BOTTLENECK['cycle_min'] / 60.0:.1f} hours, and every other station",
            "finishes early and then waits. Speeding up a fast station buys you nothing.",
            "This is the first place the energy question becomes a design question:",
            "the busiest station is also the one spending the most out of its crew.",
        ),
        (f"bottleneck = {_BOTTLENECK['key']}",
         f"cycle = {_BOTTLENECK['cycle_min'] / 60.0:.2f} h"),
        20.0, (90.0, 26.0, 13.0), "line_bottleneck",
    ),
    Chapter(
        "cycle", "05", "Every part is the same six motions",
        f"Walk, lift, carry, position, fasten, recover. {DEMO_SECONDS:.0f} seconds, "
        f"{DEMO_KCAL:.1f} kilocalories.",
        (
            "Whatever the part, the body does the same six things with it.",
            "It walks to the stockpile empty. It squats, grips, and stands the load up.",
            "It carries the load to where the part goes. It lifts the part into position,",
            "fixes it there, and straightens back up. Every one of those six has a",
            "duration taken from the part itself and a cost we can put a number on.",
        ),
        (f"one part = {DEMO_SECONDS:.0f} s",
         f"one part = {DEMO_KCAL:.2f} kcal",
         f"x {len(CATALOG.elements)} parts"),
        22.0, (90.0, 17.0, 23.0), "line_cycle",
    ),
    Chapter(
        "walk", "06", "The walk out",
        f"{DEMO_MOTIONS[0].distance:.1f} metres, empty-handed, and it still costs something.",
        (
            f"The stockpile sits {DEMO_MOTIONS[0].distance:.1f} metres from where this part",
            f"lands, so the trip out is {DEMO_MOTIONS[0].duration:.1f} seconds of walking",
            f"at {DEMO_COSTS[0].watts:.0f} watts. That is a small number on its own.",
            f"Across the whole dome those trips add up to {MOTION_KCAL['walk_out']:,.0f}",
            "kilocalories, which is exactly why stockpile placement is a real decision",
            "and not a detail left to whoever unloads the truck.",
        ),
        (f"distance = {DEMO_MOTIONS[0].distance:.2f} m",
         f"rate = {DEMO_COSTS[0].watts:.0f} W"),
        20.0, (90.0, 16.0, 18.0), "line_walk",
    ),
    Chapter(
        "lift", "07", "The lift, limb by limb",
        "Most of what you raise is yourself.",
        (
            f"Here is the squat and the stand, slowed down, with a {DEMO_MOTIONS[1].load_kg:.1f}",
            "kilogram part in the hands. Watch what the colours say: the legs straighten,",
            "the trunk comes up, the arms barely move. The trunk alone is about half the",
            f"body's mass, so raising it accounts for {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f}",
            "per cent of the lifting work across the entire dome. The part is almost an",
            "afterthought next to the body carrying it.",
        ),
        (f"load = {DEMO_MOTIONS[1].load_kg:.1f} kg",
         f"trunk share = {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} %"),
        24.0, (93.0, 12.0, 11.5), "line_lift",
    ),
    Chapter(
        "carry", "08", "Carrying is not linear in the load",
        "Double what someone carries and you more than double what it costs them.",
        (
            "Walking with a load is the one part of this that has a proper published",
            "equation behind it. Pandolf and colleagues measured it in 1977, and the",
            "load term in their equation is squared, not linear. Twenty kilograms does",
            "not cost twice what ten kilograms costs. It costs appreciably more.",
            "That single fact is the argument for carts, for conveyors, and for putting",
            "the stockpile closer, in one line.",
        ),
        (f"0 kg = {pandolf_watts(BODY_MASS_KG, 0.0, 1.05):.0f} W",
         f"40 kg = {pandolf_watts(BODY_MASS_KG, 40.0, 1.05):.0f} W"),
        22.0, (90.0, 25.0, 20.0), "line_carry",
    ),
    Chapter(
        "position", "09", "Getting it where it lands",
        f"This one goes to {_LIFT_HEIGHT:.2f} metres, and the height changes the price.",
        (
            "Positioning is the short motion between carrying a part and fastening it.",
            f"This part lands at {_LIFT_HEIGHT:.2f} metres.",
            f"Anything above {OVERHEAD_HEIGHT_M:.2f} metres is overhead work, which means",
            "the arms are above the heart, the posture costs more, and the crew fatigues",
            "faster. The dome's own geometry decides how much of the shell falls into",
            "that band, which is a design decision disguised as a shape.",
        ),
        (f"height = {_LIFT_HEIGHT:.2f} m",
         f"overhead above {OVERHEAD_HEIGHT_M:.2f} m"),
        20.0, (98.0, 16.0, 15.0), "line_position",
    ),
    Chapter(
        "fasten", "10", "Where the shift actually goes",
        f"Fastening raises nothing and spends {_FASTEN_SHARE:.0f} per cent of the fuel.",
        (
            "Here is the result that surprises people. Fastening does no lifting at all.",
            "Nothing rises. No mechanical work is done against gravity in any meaningful",
            f"amount. And it consumes {_FASTEN_SHARE:.0f} per cent of everything the crew",
            f"burns, because it is {DEMO_MOTIONS[4].duration:.0f} seconds per part of",
            "holding a posture, gripping a tool, and stabilising against its torque.",
            "The body pays for holding still. It pays a lot.",
        ),
        (f"{DEMO_MOTIONS[4].duration:.0f} s per part",
         f"{MOTION_KCAL['fasten']:,.0f} kcal per dome",
         f"mechanical share = {MOTION_EFFICIENCY['fasten'] * 100:.2f} %"),
        24.0, (90.0, 14.0, 15.0), "line_fasten",
    ),
    Chapter(
        "allowance", "11", "The rest that is not slacking",
        f"{ENERGY.rest_seconds / 3600.0:.0f} hours of this build are recovery, by design.",
        (
            "Industrial engineering has added a recovery allowance to every task time",
            "for a century. It is called the personal, fatigue and delay allowance, and",
            f"the standard figure is about {PFD_ALLOWANCE * 100:.0f} per cent on top of",
            f"the task. Overhead work earns another {PFD_OVERHEAD_EXTRA * 100:.0f} per cent",
            "because it fatigues fastest. A schedule written without it is not an",
            "efficient schedule, it is a schedule that will not be met.",
        ),
        (f"allowance = {PFD_ALLOWANCE * 100:.0f} %",
         f"overhead + {PFD_OVERHEAD_EXTRA * 100:.0f} %",
         f"total = {ENERGY.rest_seconds / 3600.0:.1f} h"),
        20.0, (90.0, 20.0, 14.0), "line_allowance",
    ),
    Chapter(
        "skeleton", "12", "The body doing the work",
        f"{BODY_MASS_KG:.0f} kilograms, and every segment of it has a known mass.",
        (
            "To cost a movement you have to know what is being moved. This figure uses",
            "Winter's anthropometric tables, the standard reference in biomechanics:",
            "each body segment is a fixed fraction of total mass, and its centre of mass",
            "sits at a fixed fraction along its length. A thigh is a tenth of the body.",
            "The trunk is almost half. Those fractions are why the numbers in this lesson",
            "come out the way they do.",
        ),
        (f"body = {BODY_MASS_KG:.0f} kg",
         f"trunk = {SEGMENTS[6].mass(BODY_MASS_KG):.1f} kg",
         f"thigh = {SEGMENTS[0].mass(BODY_MASS_KG):.1f} kg"),
        22.0, (52.0, 14.0, 11.5), "line_skeleton",
    ),
    Chapter(
        "selflift", "13", "You are the heaviest thing you lift",
        "The part is the small number in this comparison.",
        (
            f"Placing this {_ELEMENT_KG:.1f} kilogram part takes a certain amount of work",
            "to raise the part itself. It takes considerably more to raise the body that",
            "is doing it, because the body outweighs the part several times over and it",
            "goes up and down with every single placement.",
            "This is the honest reason a lower stockpile, a taller bench, or a part",
            "presented at waist height changes a shift so much.",
        ),
        (f"part = {_ELEMENT_KG:.1f} kg",
         f"body = {BODY_MASS_KG:.0f} kg"),
        20.0, (90.0, 18.0, 14.0), "line_selflift",
    ),
    Chapter(
        "limbs", "14", "Legs, trunk, arms",
        f"The trunk does {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} per cent of the "
        "lifting work.",
        (
            "Splitting the lifting work by limb group across the whole dome gives a",
            f"clear answer: legs {LIMB_WORK['legs'] / _LIMB_TOTAL * 100:.0f} per cent,",
            f"trunk {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} per cent,",
            f"arms {LIMB_WORK['arms'] / _LIMB_TOTAL * 100:.0f} per cent.",
            "The arms get all the attention because they are what you watch, but they",
            "are the lightest part of the body and they do the least raising. The back",
            "is where the work is, and that is also where the injuries are.",
        ),
        tuple(f"{group} = {LIMB_WORK[group] / _LIMB_TOTAL * 100:.1f} %"
              for group in LIMB_GROUPS),
        22.0, (90.0, 18.0, 14.0), "line_limbs",
    ),
    Chapter(
        "team", "15", "When one person stops lifting alone",
        f"Above {TWO_PERSON_LIFT_KG:.0f} kilograms it takes both of them.",
        (
            "Manual handling guidance puts the single-person limit near",
            f"{TWO_PERSON_LIFT_KG:.0f} kilograms. Above that the crew lifts together and",
            "each person carries half. The heaviest part on this dome is the",
            f"{_HEAVIEST.label.lower()} at {float(_HEAVIEST.weight):,.0f} kilograms,",
            f"which is {float(_HEAVIEST.weight) / CREW:,.0f} kilograms each.",
            "Even with every team lift split, one worker still raises",
            f"{ENERGY.lifted_mass_kg:,.0f} kilograms to build one dome.",
        ),
        (f"threshold = {TWO_PERSON_LIFT_KG:.0f} kg",
         f"heaviest = {float(_HEAVIEST.weight):,.0f} kg",
         f"raised per worker = {ENERGY.lifted_mass_kg:,.0f} kg"),
        22.0, (90.0, 12.0, 15.0), "line_team",
    ),
    Chapter(
        "overhead", "16", "The same part costs more up high",
        "Arms above the heart is the most expensive posture on the line.",
        (
            "Two workers, the same fastener, the same number of turns. One is working",
            "at deck height and one is working above their shoulders. The overhead",
            "worker is spending noticeably more per second, is fatiguing faster, and",
            "will need more recovery for the same output.",
            "Whenever the dome's geometry pushes work above that line, the cost lands",
            "on a body rather than on a spreadsheet.",
        ),
        (f"deck = {DEMO_COSTS[4].watts:.0f} W",
         f"overhead = {met_watts(4.2):.0f} W"),
        20.0, (90.0, 12.0, 16.0), "line_overhead",
    ),
    Chapter(
        "work", "17", "The part that is exact",
        "Mass times gravity times height. No estimate anywhere in it.",
        (
            "Raising a part is the one piece of this with no modelling in it at all.",
            f"This part weighs {_ELEMENT_KG:.1f} kilograms and rises",
            f"{_LIFT_HEIGHT:.2f} metres, so the work done on it is",
            f"{_LIFT_WORK:,.0f} joules.",
            "The mass comes from the catalogue, the height comes from the dome's",
            "geometry, and gravity is gravity. Every mechanical number in this lesson",
            "is that calculation, run once per segment and once per part.",
        ),
        (f"m = {_ELEMENT_KG:.1f} kg",
         f"h = {_LIFT_HEIGHT:.2f} m",
         f"W = {_LIFT_WORK:,.0f} J"),
        20.0, (90.0, 16.0, 13.5), "line_work",
    ),
    Chapter(
        "model", "18", "The part that is a model",
        "Kilocalories are not measured here. They are estimated, and here is from what.",
        (
            "A muscle holding a panel steady does no mechanical work and still burns",
            "fuel, so there is no way to get from joules of lifting to kilocalories of",
            "food without external information. This lesson uses published task",
            "intensities for stationary work and the Pandolf equation for walking.",
            f"There are {len(EXTERNAL_CONSTANTS)} such constants, every one of them named",
            "in the report. Change the efficiency figure and every calorie here moves.",
        ),
        (f"external constants = {len(EXTERNAL_CONSTANTS)}",
         "computed: mass, height, distance",
         "assumed: intensity, efficiency"),
        22.0, (90.0, 20.0, 12.0), "line_model",
    ),
    Chapter(
        "efficiency", "19", "Nineteen per cent, and a fifth of one per cent",
        "Both are true. They answer different questions.",
        (
            f"During the lift itself, {MOTION_EFFICIENCY['lift'] * 100:.0f} per cent of the",
            "fuel becomes height, which is close to what muscle can manage at best.",
            f"Across the whole dome, mechanical work is {ENERGY.mechanical_fraction * 100:.2f}",
            "per cent of the food energy. The difference is not an error. It is that",
            "almost none of a working day is spent lifting. The rest is posture, grip,",
            "stabilising, and holding still, and none of that raises anything.",
        ),
        (f"lift = {MOTION_EFFICIENCY['lift'] * 100:.1f} %",
         f"build = {ENERGY.mechanical_fraction * 100:.3f} %",
         f"muscle ceiling = {CONCENTRIC_EFFICIENCY * 100:.0f} %"),
        24.0, (90.0, 22.0, 13.0), "line_efficiency",
    ),
    Chapter(
        "motions", "20", "The whole dome, by motion",
        f"{ENERGY.kcal_per_worker:,.0f} kilocalories per worker, and where each one went.",
        (
            "Here is every motion of every part, totalled. Fastening dominates, because",
            "fastening is where the time is. Walking, lifting, carrying and positioning",
            "together are a small fraction, even though they are the parts that look",
            "like work and the parts a manager would think to optimise.",
            "If you want to reduce what this line costs its crew, the target is the",
            "posture people hold while fastening, not the distance they walk.",
        ),
        tuple(f"{name} = {kcal:,.0f} kcal"
              for name, kcal in sorted(MOTION_KCAL.items(),
                                       key=lambda kv: -kv[1])[:4]),
        22.0, (90.0, 26.0, 14.0), "line_motions",
    ),
    Chapter(
        "stations", "21", "The ledger, station by station",
        "The busiest station is also the hungriest one.",
        (
            "Broken down per station, the energy follows the part count and the time,",
            "not the tonnage. Stations that place many light pieces slowly cost their",
            "crews more than stations that place a few heavy ones quickly.",
            "This is the table to look at when deciding where a jig, a lift assist, or",
            "an extra pair of hands would actually change someone's day.",
        ),
        tuple(f"{key} = {row['kcal']:,.0f} kcal"
              for key, row in sorted(STAGE_ENERGY.items(),
                                     key=lambda kv: -kv[1]["kcal"])[:4]),
        22.0, (90.0, 26.0, 14.0), "line_stations",
    ),
    Chapter(
        "shift", "22", "What one working day costs",
        f"{ENERGY.kcal_per_shift:,.0f} kilocalories, at {ENERGY.mean_met:.2f} METs.",
        (
            f"Averaged over the build, the crew works at {ENERGY.mean_watts:.0f} watts,",
            f"which is {ENERGY.mean_met:.2f} times resting metabolism.",
            "Occupational physiology puts the ceiling for a sustained eight-hour shift",
            f"at roughly {SUSTAINABLE_SHIFT_WATTS:.0f} watts, so this line sits just",
            "under it, with the recovery allowance included. Take the allowance away",
            "and the same work stops being sustainable, which is the whole point of it.",
        ),
        (f"rate = {ENERGY.mean_watts:.0f} W",
         f"per shift = {ENERGY.kcal_per_shift:,.0f} kcal",
         f"shifts = {ENERGY.shifts:.1f} per dome"),
        22.0, (90.0, 22.0, 14.0), "line_shift",
    ),
    Chapter(
        "food", "23", "The total, in food",
        f"{ENERGY.kcal_crew:,.0f} kilocalories to build one house.",
        (
            f"The two of them together spend {ENERGY.kcal_crew:,.0f} kilocalories turning",
            f"{CATALOG.total_weight():,.0f} kilograms of material into a finished dome.",
            f"That is about {_FOOD[0][1]:,.0f} slices of bread, or",
            f"{_FOOD[1][1]:,.0f} bananas, or {_FOOD[2][1]:.0f} days of eating at",
            "two and a half thousand kilocalories a day.",
            "It is a real cost, it is paid by people, and until now it was not on any",
            "drawing of this building.",
        ),
        (f"crew total = {ENERGY.kcal_crew:,.0f} kcal",
         f"= {_FOOD[0][1]:,.0f} slices of bread",
         f"= {_FOOD[2][1]:.0f} days of eating"),
        22.0, (90.0, 20.0, 18.0), "line_food",
    ),
    Chapter(
        "recap", "24", "What the ledger changes",
        "Design the posture, not just the part.",
        (
            "We followed two people through every motion needed to build one dome and",
            "put a number on each one. The parts that look like effort turned out to be",
            "cheap. The part that looks like nothing, holding a position while fastening,",
            "turned out to be almost the whole bill.",
            "Every figure came from a part mass, a placement height, a walk distance, or",
            "a named published constant, and every one of them can be recomputed rather",
            "than trusted. That is the only reason it is worth putting on screen.",
        ),
        (f"{len(CATALOG.elements)} parts",
         f"{ENERGY.hours_per_worker:.0f} h per worker",
         f"{ENERGY.kcal_crew:,.0f} kcal for the crew"),
        22.0, (84.0, 30.0, 24.0), "line_recap",
    ),
)


def _selftest() -> None:
    validate_figure()
    validate_energetics()


LINE_LESSON = Lesson(
    key="line",
    brand="ASSEMBLY LINE / THE ENERGY LEDGER",
    title="Assembly Line Energy Masterclass",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=line_equations,
    selftest=_selftest,
    report=energy_report,
    snapshot_prefix="line",
)
