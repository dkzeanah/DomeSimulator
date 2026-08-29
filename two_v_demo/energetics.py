"""What building one dome costs the two people who build it.

This module turns the assembly line's own element list into a metabolic
budget: every strut, panel and fixture becomes a sequence of named body
motions, each motion is costed, and the costs total up per station, per
motion and per limb.

Two numbers, and they are not the same number
---------------------------------------------
The lesson keeps these strictly apart, because conflating them is the
usual way this kind of estimate goes wrong.

**Mechanical work** is exact.  Raising a 30 kg panel 2.4 m is
``m g h`` and nothing about it is estimated.  Raising the *body* to do it
is the same calculation run segment by segment, using Winter's
anthropometric tables from :mod:`two_v_demo.figure`.  Every joule of it
traces to an element mass and a placement height in ``al_build``.

**Metabolic cost** is a model.  A muscle holding a panel steady against
gravity does no mechanical work at all and still burns fuel; most of what
a working body spends goes to activation, stabilisation and posture, not
to lifting.  There is no way to derive that from geometry, so activity
intensity comes from published task data -- the Compendium of Physical
Activities for stationary tasks, and the Pandolf load-carriage equation
for walking, which is used in preference to a flat figure because it
takes the actual carried mass as an input.

The interesting result falls out of keeping them separate: across a whole
dome, the mechanical work is a single-digit percentage of the food energy.
That is not an error in the model.  That is what manual labour is.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np

from .figure import (
    GRAVITY,
    LIMB_GROUP,
    LIMB_GROUPS,
    POSES,
    SEGMENTS,
    Pose,
    grip_point,
    joint_positions,
    segment_centres,
    walk_pose,
)


# ----------------------------------------------------------------------
# The crew
# ----------------------------------------------------------------------

BODY_MASS_KG = 82.0
STATURE_M = 1.75
AGE_YEARS = 34

KCAL_PER_JOULE = 1.0 / 4184.0
JOULES_PER_KCAL = 4184.0


# ----------------------------------------------------------------------
# Published constants -- the parts that are not geometry
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalConstant:
    """One number this model takes on authority rather than deriving."""

    key: str
    value: float
    units: str
    source: str
    note: str


EXTERNAL_CONSTANTS: tuple[ExternalConstant, ...] = (
    ExternalConstant(
        "met_definition", 1.0, "kcal/kg/h",
        "Metabolic equivalent of task, standard definition",
        "One MET is roughly resting. Every intensity below is a multiple "
        "of it, and already includes the resting cost.",
    ),
    ExternalConstant(
        "met_lift", 5.5, "METs",
        "Compendium of Physical Activities: lifting items continuously",
        "Repeated floor-to-waist lifting, moderate effort.",
    ),
    ExternalConstant(
        "met_position", 4.0, "METs",
        "Compendium: carrying and placing building materials",
        "Getting a part to where it lands and holding it there.",
    ),
    ExternalConstant(
        "met_fasten", 3.5, "METs",
        "Compendium: installing or repairing, general",
        "Driving fasteners. Most of the shift is spent here.",
    ),
    ExternalConstant(
        "met_fasten_overhead", 4.2, "METs",
        "Compendium: work above shoulder height",
        "The same task costs more with the arms above the heart.",
    ),
    ExternalConstant(
        "met_recover", 2.5, "METs",
        "Compendium: standing, light activity",
        "Straightening up between parts.",
    ),
    ExternalConstant(
        "pandolf_terrain_factor", 1.0, "dimensionless",
        "Pandolf, Givoni and Goldman (1977) load-carriage equation",
        "1.0 is a paved surface, which is what a factory floor is. This "
        "equation replaces a flat MET for walking because it takes the "
        "carried mass as an input.",
    ),
    ExternalConstant(
        "concentric_efficiency", 0.25, "fraction",
        "Standard exercise-physiology value for positive muscular work",
        "Used only to report how much of the food energy could possibly "
        "have become lifting, never to compute the total.",
    ),
    ExternalConstant(
        "rmr_mifflin", 0.0, "kcal/day",
        "Mifflin-St Jeor (1990) resting metabolic rate",
        "Used for the off-shift baseline and as a floor on any activity.",
    ),
    ExternalConstant(
        "pfd_allowance", 0.15, "fraction",
        "Industrial engineering: personal, fatigue and delay allowance",
        "Standard work measurement adds this to every task time. It is "
        "not slack -- a rate set without it cannot be held for a shift.",
    ),
    ExternalConstant(
        "pfd_overhead_extra", 0.10, "fraction",
        "Ergonomics practice: added recovery for above-shoulder work",
        "Overhead posture fatigues fastest, so it earns more recovery.",
    ),
    ExternalConstant(
        "met_pause", 1.5, "METs",
        "Compendium: standing at rest",
        "What the recovery allowance actually costs.",
    ),
    ExternalConstant(
        "sustainable_shift_watts", 350.0, "W",
        "Occupational physiology: sustainable 8-hour working rate",
        "A whole-shift average much above this is not sustainable, so it "
        "is a useful bound on whether the model is sane.",
    ),
)

_CONSTANT = {item.key: item.value for item in EXTERNAL_CONSTANTS}

TERRAIN_FACTOR = _CONSTANT["pandolf_terrain_factor"]
CONCENTRIC_EFFICIENCY = _CONSTANT["concentric_efficiency"]
SUSTAINABLE_SHIFT_WATTS = _CONSTANT["sustainable_shift_watts"]


def resting_metabolic_watts(
    body_mass: float = BODY_MASS_KG,
    stature: float = STATURE_M,
    age: int = AGE_YEARS,
) -> float:
    """Mifflin-St Jeor resting metabolic rate, converted to watts."""
    kcal_per_day = 10.0 * body_mass + 6.25 * (stature * 100.0) - 5.0 * age + 5.0
    return kcal_per_day * JOULES_PER_KCAL / 86400.0


def met_watts(met: float, body_mass: float = BODY_MASS_KG) -> float:
    """Convert an activity intensity in METs to watts for this body."""
    return met * body_mass * JOULES_PER_KCAL / 3600.0


def pandolf_watts(
    body_mass: float,
    load_mass: float,
    speed: float,
    grade_percent: float = 0.0,
    terrain: float = TERRAIN_FACTOR,
) -> float:
    """Metabolic rate of walking while carrying a load, in watts.

    Pandolf, Givoni and Goldman (1977).  The load term is quadratic in the
    load-to-body-mass ratio, so doubling what someone carries more than
    doubles what the carrying costs them.
    """
    if body_mass <= 0.0:
        raise ValueError("body mass must be positive")
    total = body_mass + load_mass
    ratio = load_mass / body_mass
    return (
        1.5 * body_mass
        + 2.0 * total * ratio * ratio
        + terrain * total * (1.5 * speed * speed + 0.35 * speed * grade_percent)
    )


# ----------------------------------------------------------------------
# One motion, and what it costs
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Motion:
    """One named movement of the body, with everything needed to cost it."""

    name: str
    label: str
    start_pose: str
    end_pose: str
    duration: float
    met: float
    """Activity intensity. Ignored when ``distance`` is non-zero, because
    walking is costed by Pandolf instead."""
    load_kg: float = 0.0
    distance: float = 0.0
    detail: str = ""

    @property
    def speed(self) -> float:
        if self.distance <= 0.0 or self.duration <= 0.0:
            return 0.0
        return self.distance / self.duration

    @property
    def is_locomotion(self) -> bool:
        return self.distance > 0.0


@dataclass(frozen=True)
class MotionCost:
    """The bill for one motion, with work and fuel kept separate."""

    motion: Motion
    segment_work: dict[str, float]
    """Mechanical work raising each body segment, joules. Never negative."""
    load_work: float
    lowering_work: float
    metabolic_joules: float

    @property
    def kcal(self) -> float:
        return self.metabolic_joules * KCAL_PER_JOULE

    @property
    def watts(self) -> float:
        if self.motion.duration <= 0.0:
            return 0.0
        return self.metabolic_joules / self.motion.duration

    @property
    def mechanical_joules(self) -> float:
        """Work actually done against gravity, body and load together."""
        return sum(self.segment_work.values()) + self.load_work

    @property
    def mechanical_fraction(self) -> float:
        if self.metabolic_joules <= 0.0:
            return 0.0
        return self.mechanical_joules / self.metabolic_joules

    def by_limb(self) -> dict[str, float]:
        """Split the segment-raising work across legs, trunk and arms."""
        totals = {group: 0.0 for group in LIMB_GROUPS}
        for name, work in self.segment_work.items():
            totals[LIMB_GROUP[name]] += work
        return totals


def _pose_of(name: str, phase: float = 0.0) -> Pose:
    return walk_pose(phase) if name == "walk" else POSES[name]


def motion_cost(
    motion: Motion,
    body_mass: float = BODY_MASS_KG,
    stature: float = STATURE_M,
) -> MotionCost:
    """Cost one motion, computing the work and modelling the fuel."""
    start_joints = joint_positions(_pose_of(motion.start_pose, 0.0), stature)
    end_joints = joint_positions(_pose_of(motion.end_pose, 0.5), stature)
    start_centres = segment_centres(start_joints)
    end_centres = segment_centres(end_joints)

    segment_work: dict[str, float] = {}
    lowering = 0.0
    for segment in SEGMENTS:
        rise = float(end_centres[segment.name][2] - start_centres[segment.name][2])
        work = segment.mass(body_mass) * GRAVITY * rise
        segment_work[segment.name] = max(0.0, work)
        if work < 0.0:
            lowering += -work

    load_rise = float(grip_point(end_joints)[2] - grip_point(start_joints)[2])
    load_work = motion.load_kg * GRAVITY * load_rise
    if load_work < 0.0:
        lowering += -load_work
        load_work = 0.0

    if motion.is_locomotion:
        watts = pandolf_watts(body_mass, motion.load_kg, motion.speed)
    else:
        watts = met_watts(motion.met, body_mass)
    # A motion can never cost less than lying down would.
    watts = max(watts, resting_metabolic_watts(body_mass, stature))

    return MotionCost(
        motion=motion,
        segment_work=segment_work,
        load_work=load_work,
        lowering_work=lowering,
        metabolic_joules=watts * motion.duration,
    )


# ----------------------------------------------------------------------
# One element, decomposed into motions
# ----------------------------------------------------------------------

STOCKPILE_XY = (0.0, -3.2)
"""Where material waits -- ``Worker``'s default stockpile in assembly_line."""

TWO_PERSON_LIFT_KG = 23.0
"""Above this, one person does not lift alone and the crew splits the load."""

OVERHEAD_HEIGHT_M = 1.75
"""Above this the work is overhead, and the posture costs more."""

WALK_SPEED = 1.30
CARRY_SPEED = 1.05

PFD_ALLOWANCE = _CONSTANT["pfd_allowance"]
PFD_OVERHEAD_EXTRA = _CONSTANT["pfd_overhead_extra"]


def _grip_height(pose_name: str) -> float:
    return float(grip_point(joint_positions(POSES[pose_name], STATURE_M))[2])


def element_motions(
    element,
    stockpile: Sequence[float] = STOCKPILE_XY,
    crew: int = 2,
) -> tuple[Motion, ...]:
    """Break one catalogue element into the motions needed to place it.

    The cycle is always the same shape -- fetch, lift, carry, position,
    fasten, recover -- but every duration, distance, mass and height in it
    comes from the element itself.
    """
    mass = float(element.weight)
    team = mass > TWO_PERSON_LIFT_KG
    share = mass / max(1, crew) if team else mass

    floor = np.asarray(element.floor_point, dtype=np.float64)[:2]
    distance = float(np.linalg.norm(floor - np.asarray(stockpile, dtype=np.float64)))
    place_height = float(element.centroid[2])
    overhead = place_height > OVERHEAD_HEIGHT_M

    walk_out = max(0.6, distance / WALK_SPEED)
    carry_in = max(0.6, distance / CARRY_SPEED)
    lift_time = 1.4 + 0.05 * share
    place_time = 1.8 + 0.04 * share
    fasten_pose = "fasten_high" if overhead else (
        "fasten" if place_height < 0.6 else "reach_out"
    )
    carry_pose = "team_carry" if team else "carry"
    pick_pose = "squat_deep" if place_height < 1.2 else "squat_mid"

    # The catalogue's labour minutes are the whole task.  Walking, lifting
    # and placing are computed from distance and mass; whatever is left is
    # the fastening, which is where most of the time actually goes.
    fixed = walk_out + carry_in + lift_time + place_time + 1.2
    fasten_time = max(3.0, float(element.labor_min) * 60.0 / max(1, crew) - fixed)

    # Work measurement adds a recovery allowance on top of task time, and
    # above-shoulder work earns more of it than work at waist height.
    allowance = PFD_ALLOWANCE + (PFD_OVERHEAD_EXTRA if overhead else 0.0)
    pause_time = (fixed + fasten_time) * allowance

    return (
        Motion("walk_out", "Walk to the stockpile", "stand", "walk",
               walk_out, 3.5, 0.0, distance,
               f"{distance:.1f} m unloaded at {WALK_SPEED:.2f} m/s"),
        Motion("lift", "Squat, grip, and stand the load up", pick_pose,
               carry_pose, lift_time, _CONSTANT["met_lift"], share, 0.0,
               f"{share:.1f} kg raised to {_grip_height(carry_pose):.2f} m"
               + ("  (two-person lift)" if team else "")),
        Motion("carry", "Carry it to the placement point", carry_pose,
               carry_pose, carry_in, 5.0, share, distance,
               f"{share:.1f} kg over {distance:.1f} m"),
        Motion("position", "Lift it to where it lands", carry_pose,
               fasten_pose, place_time, _CONSTANT["met_position"], share, 0.0,
               f"placed at {place_height:.2f} m"),
        Motion("fasten", "Fix it in place", fasten_pose, fasten_pose,
               fasten_time,
               _CONSTANT["met_fasten_overhead"] if overhead
               else _CONSTANT["met_fasten"],
               0.0, 0.0,
               f"{fasten_time / 60.0:.1f} min in the {fasten_pose} posture"),
        Motion("recover", "Stand back up", fasten_pose, "stand",
               1.2, _CONSTANT["met_recover"], 0.0, 0.0, "return to standing"),
        Motion("pause", "Recovery allowance", "stand", "stand",
               pause_time, _CONSTANT["met_pause"], 0.0, 0.0,
               f"{allowance * 100:.0f} % of task time, "
               + ("overhead rate" if overhead else "standard rate")),
    )


# ----------------------------------------------------------------------
# The whole build
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ElementEnergy:
    """One element's complete bill, per worker."""

    element: object
    costs: tuple[MotionCost, ...]

    @property
    def kcal(self) -> float:
        return sum(cost.kcal for cost in self.costs)

    @property
    def seconds(self) -> float:
        return sum(cost.motion.duration for cost in self.costs)

    @property
    def mechanical_joules(self) -> float:
        return sum(cost.mechanical_joules for cost in self.costs)

    def by_motion(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for cost in self.costs:
            totals[cost.motion.name] = totals.get(cost.motion.name, 0.0) + cost.kcal
        return totals

    def by_limb(self) -> dict[str, float]:
        totals = {group: 0.0 for group in LIMB_GROUPS}
        for cost in self.costs:
            for group, work in cost.by_limb().items():
                totals[group] += work
        return totals


@dataclass(frozen=True)
class BuildEnergy:
    """Every element of one dome, costed."""

    elements: tuple[ElementEnergy, ...]
    crew: int
    body_mass: float

    @property
    def kcal_per_worker(self) -> float:
        return sum(item.kcal for item in self.elements)

    @property
    def kcal_crew(self) -> float:
        return self.kcal_per_worker * self.crew

    @property
    def seconds_per_worker(self) -> float:
        return sum(item.seconds for item in self.elements)

    @property
    def hours_per_worker(self) -> float:
        return self.seconds_per_worker / 3600.0

    @property
    def shifts(self) -> float:
        return self.hours_per_worker / 8.0

    @property
    def rest_seconds(self) -> float:
        """Time inside the total that is recovery allowance, not task."""
        return sum(
            cost.motion.duration
            for item in self.elements
            for cost in item.costs
            if cost.motion.name == "pause"
        )

    @property
    def rest_fraction(self) -> float:
        if self.seconds_per_worker <= 0.0:
            return 0.0
        return self.rest_seconds / self.seconds_per_worker

    @property
    def mechanical_joules(self) -> float:
        return sum(item.mechanical_joules for item in self.elements)

    @property
    def mechanical_kcal(self) -> float:
        return self.mechanical_joules * KCAL_PER_JOULE

    @property
    def mechanical_fraction(self) -> float:
        """How much of the food energy became lifting. It is small."""
        if self.kcal_per_worker <= 0.0:
            return 0.0
        return self.mechanical_kcal / self.kcal_per_worker

    @property
    def mean_watts(self) -> float:
        if self.seconds_per_worker <= 0.0:
            return 0.0
        return self.kcal_per_worker * JOULES_PER_KCAL / self.seconds_per_worker

    @property
    def mean_met(self) -> float:
        return self.mean_watts * 3600.0 / (JOULES_PER_KCAL * self.body_mass)

    @property
    def kcal_per_shift(self) -> float:
        """The scale-free number: what one working day costs a body."""
        if self.shifts <= 0.0:
            return 0.0
        return self.kcal_per_worker / self.shifts

    @property
    def total_mass_kg(self) -> float:
        return sum(float(item.element.weight) for item in self.elements)

    @property
    def lifted_mass_kg(self) -> float:
        """Mass actually raised by one worker, after team lifts are split."""
        total = 0.0
        for item in self.elements:
            mass = float(item.element.weight)
            total += mass / self.crew if mass > TWO_PERSON_LIFT_KG else mass
        return total

    def by_stage(self) -> dict[str, dict[str, float]]:
        totals: dict[str, dict[str, float]] = {}
        for item in self.elements:
            row = totals.setdefault(
                item.element.stage,
                {"kcal": 0.0, "seconds": 0.0, "elements": 0, "kg": 0.0},
            )
            row["kcal"] += item.kcal
            row["seconds"] += item.seconds
            row["elements"] += 1
            row["kg"] += float(item.element.weight)
        return totals

    def by_motion(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for item in self.elements:
            for name, kcal in item.by_motion().items():
                totals[name] = totals.get(name, 0.0) + kcal
        return totals

    def by_limb(self) -> dict[str, float]:
        totals = {group: 0.0 for group in LIMB_GROUPS}
        for item in self.elements:
            for group, work in item.by_limb().items():
                totals[group] += work
        return totals

    def motion_efficiency(self) -> dict[str, float]:
        """Mechanical work as a share of fuel, per motion type.

        The whole-build figure is tiny because most of the shift is spent
        fastening, which raises nothing.  Asking the same question of the
        lift alone gives a very different -- and much more familiar --
        answer, and the gap between the two is the point.
        """
        work: dict[str, float] = {}
        fuel: dict[str, float] = {}
        for item in self.elements:
            for cost in item.costs:
                name = cost.motion.name
                work[name] = work.get(name, 0.0) + cost.mechanical_joules
                fuel[name] = fuel.get(name, 0.0) + cost.metabolic_joules
        return {
            name: (work[name] / fuel[name] if fuel[name] else 0.0)
            for name in work
        }

    def food_equivalent(self) -> tuple[tuple[str, float], ...]:
        """The crew's total, expressed as things a person actually eats."""
        kcal = self.kcal_crew
        return (
            ("slices of bread at 80 kcal", kcal / 80.0),
            ("bananas at 105 kcal", kcal / 105.0),
            ("days of a 2,500 kcal diet", kcal / 2500.0),
        )


def home_spec(serial: int = 1):
    """The line's flagship product, chosen deterministically.

    ``random_spec`` picks a product line at random, which would let the
    lesson's numbers change between runs and could land on a four-station
    shed instead of the fifteen-station house line.  Seeding it and
    naming the type pins both.
    """
    import al_build as AL

    return AL.random_spec(serial, random.Random(serial), "home")


@lru_cache(maxsize=4)
def build_energy(serial: int = 1, crew: int = 2) -> BuildEnergy:
    """Cost a complete dome, element by element, for one crew member."""
    import al_build as AL

    spec = home_spec(serial)
    catalog, _ = AL.build_dome_catalog(spec)
    elements = tuple(
        ElementEnergy(
            element,
            tuple(
                motion_cost(motion, BODY_MASS_KG, STATURE_M)
                for motion in element_motions(element, crew=crew)
            ),
        )
        for element in catalog.elements
    )
    return BuildEnergy(elements, crew, BODY_MASS_KG)


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------

def energy_report(serial: int = 1, crew: int = 2) -> str:
    """A portable audit of every claim the assembly-line lesson makes."""
    energy = build_energy(serial, crew)
    rmr = resting_metabolic_watts()
    spec = home_spec(serial)
    lines = ["ASSEMBLY LINE ENERGY MASTERCLASS - CALCULATION AUDIT", ""]
    lines.append(f"product                 {spec.name}, {spec.dtype}, "
                 f"radius {spec.radius:.2f} m, {spec.frequency}V, "
                 f"{spec.layout}")
    lines.append(f"stations                {len(spec.stages)}")
    lines.append(f"crew                    {crew} x {BODY_MASS_KG:.0f} kg, "
                 f"{STATURE_M:.2f} m, age {AGE_YEARS}")
    lines.append(f"resting metabolic rate  {rmr:.1f} W = "
                 f"{rmr * 86400 * KCAL_PER_JOULE:.0f} kcal/day")
    lines.append("")
    lines.append(f"elements                {len(energy.elements)}")
    lines.append(f"material in the dome    {energy.total_mass_kg:,.0f} kg")
    lines.append(f"lifted by one worker    {energy.lifted_mass_kg:,.0f} kg")
    lines.append(f"time per worker         {energy.hours_per_worker:.2f} h "
                 f"= {energy.shifts:.2f} shifts")
    lines.append(f"energy per worker       {energy.kcal_per_worker:,.0f} kcal")
    lines.append(f"energy for the crew     {energy.kcal_crew:,.0f} kcal")
    lines.append(f"energy per shift        {energy.kcal_per_shift:,.0f} kcal")
    lines.append(f"mean working rate       {energy.mean_watts:.0f} W "
                 f"= {energy.mean_met:.2f} METs")
    lines.append(f"  sustainable bound     {SUSTAINABLE_SHIFT_WATTS:.0f} W")
    lines.append(f"recovery allowance      {energy.rest_fraction * 100.0:.1f} % "
                 f"of the total ({energy.rest_seconds / 3600.0:.2f} h)")
    lines.append("")
    lines.append(f"mechanical work done    {energy.mechanical_joules / 1e6:.3f} MJ "
                 f"= {energy.mechanical_kcal:,.0f} kcal")
    lines.append(f"  as a share of food    {energy.mechanical_fraction * 100.0:.1f} %")
    lines.append(f"  ceiling at {CONCENTRIC_EFFICIENCY * 100:.0f} % muscle  "
                 f"{CONCENTRIC_EFFICIENCY * 100:.0f} %  "
                 "(everything else is posture, grip and stabilising)")
    lines.append("")
    lines.append("food energy by motion:")
    total = energy.kcal_per_worker or 1.0
    for name, kcal in sorted(energy.by_motion().items(), key=lambda kv: -kv[1]):
        lines.append(f"  {name:<10} {kcal:8,.0f} kcal  {kcal / total * 100:5.1f} %")
    lines.append("")
    lines.append("mechanical share of the fuel, per motion:")
    for name, share in sorted(energy.motion_efficiency().items(),
                              key=lambda kv: -kv[1]):
        lines.append(f"  {name:<10} {share * 100.0:6.2f} %")
    lines.append("")
    lines.append("mechanical lifting work by limb group:")
    limb = energy.by_limb()
    limb_total = sum(limb.values()) or 1.0
    for group in LIMB_GROUPS:
        lines.append(f"  {group:<10} {limb[group] / 1000.0:8.1f} kJ"
                     f"  {limb[group] / limb_total * 100:5.1f} %")
    lines.append("")
    lines.append("by station:")
    for key, row in sorted(energy.by_stage().items(), key=lambda kv: -kv[1]["kcal"]):
        lines.append(
            f"  {key:<12} {row['elements']:>4} parts  {row['kg']:8,.0f} kg  "
            f"{row['seconds'] / 3600.0:6.2f} h  {row['kcal']:7,.0f} kcal"
        )
    lines.append("")
    lines.append("the crew's total, in food:")
    for label, amount in energy.food_equivalent():
        lines.append(f"  {amount:10,.0f}  {label}")
    lines.append("")
    lines.append("external constants this model takes on authority:")
    for item in EXTERNAL_CONSTANTS:
        shown = f"{item.value:g} {item.units}" if item.value else item.units
        lines.append(f"  {item.key:<26} {shown:<14} {item.source}")
    return "\n".join(lines)


def validate_energetics() -> None:
    """Prove the model before any of its numbers reach a screen."""
    rmr = resting_metabolic_watts()
    kcal_day = rmr * 86400.0 * KCAL_PER_JOULE
    assert 1600.0 < kcal_day < 2000.0, kcal_day

    # One MET is about resting, by definition.
    assert abs(met_watts(1.0) / rmr - 1.0) < 0.15, met_watts(1.0) / rmr

    # Pandolf must rise with load and speed, and be superlinear in load.
    base = pandolf_watts(82.0, 0.0, 1.3)
    loaded = pandolf_watts(82.0, 20.0, 1.3)
    heavier = pandolf_watts(82.0, 40.0, 1.3)
    assert loaded > base
    assert (heavier - loaded) > (loaded - base), (base, loaded, heavier)
    assert pandolf_watts(82.0, 20.0, 1.6) > loaded

    # Mechanical work: raising a load does work, lowering it does none.
    up = Motion("up", "up", "squat_deep", "carry", 2.0, 5.5, 25.0)
    down = Motion("down", "down", "carry", "squat_deep", 2.0, 5.5, 25.0)
    assert motion_cost(up).load_work > 0.0
    assert motion_cost(down).load_work == 0.0
    assert motion_cost(down).lowering_work > 0.0

    # Segment work must cover the whole body, never be negative, and the
    # limb split must account for all of it.
    cost = motion_cost(up)
    assert set(cost.segment_work) == {segment.name for segment in SEGMENTS}
    assert all(value >= 0.0 for value in cost.segment_work.values())
    assert abs(sum(cost.by_limb().values())
               - sum(cost.segment_work.values())) < 1e-9

    # Overhead fastening costs more than fastening at waist height.
    high = Motion("high", "high", "fasten_high", "fasten_high", 60.0, 4.2)
    low = Motion("low", "low", "fasten", "fasten", 60.0, 3.5)
    assert motion_cost(high).kcal > motion_cost(low).kcal

    # Nothing costs less than lying down.
    idle = Motion("idle", "idle", "stand", "stand", 10.0, 0.1)
    assert motion_cost(idle).watts >= rmr - 1e-6

    energy = build_energy(1, 2)
    assert len(energy.elements) > 100
    # Check the rate, not the total: the total scales with how big a dome
    # was ordered, but a shift is a shift whatever is being built.
    kcal_per_shift = energy.kcal_per_worker / max(energy.shifts, 1e-9)
    assert 1800.0 < kcal_per_shift < 4500.0, kcal_per_shift
    assert 2.0 < energy.mean_met < 7.0, energy.mean_met
    assert energy.mean_watts < SUSTAINABLE_SHIFT_WATTS, energy.mean_watts
    # The headline finding: lifting is a small slice of the fuel, and it
    # can never exceed what muscle efficiency allows.
    assert 0.0 < energy.mechanical_fraction < CONCENTRIC_EFFICIENCY, \
        energy.mechanical_fraction
    # The lift itself must be far more mechanically efficient than the
    # build average, or the two numbers are not measuring what they claim.
    efficiency = energy.motion_efficiency()
    assert efficiency["lift"] > energy.mechanical_fraction * 5.0, efficiency
    assert efficiency["fasten"] < 1e-6, efficiency["fasten"]
    # Legs and trunk are heavy; arms cannot dominate the lifting work.
    limb = energy.by_limb()
    assert limb["arms"] < limb["legs"] + limb["trunk"], limb
    # Team lifting must actually reduce what one person raises.
    assert energy.lifted_mass_kg < energy.total_mass_kg
    # The recovery allowance has to be really present in the timeline.
    assert 0.10 < energy.rest_fraction < 0.25, energy.rest_fraction
