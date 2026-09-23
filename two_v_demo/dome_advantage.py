"""Why a dome, argued in numbers a sceptic can check.

A campaign video has to persuade, and the cheapest way to persuade is to
be right.  Everything in this module is computed from the geometry and
compared against a conventional house of *identical floor area*, because
"domes are efficient" is a slogan and "forty-two percent less exterior
wall at three hundred square feet" is an argument.

The comparison is deliberately generous to the box: it gets a gable roof
rather than a flat one, standard eight foot walls, and no penalty for the
fact that its corners are the part that leaks.

Read the second half of this module before quoting the first.  The margin
is not a property of domes, it is a property of *small* domes, and it has
three separate holes in it:

* it shrinks with floor area and **reverses** above
  :func:`envelope_crossover_sqft`, because a hemisphere has to grow
  upward to grow outward while a stud wall stays eight feet tall;
* below :func:`volume_crossover_sqft` a good part of it is simply that
  the dome encloses *less building*; and
* a hemisphere has no headroom at its perimeter, so equal floor area is
  not equal usable area -- see :func:`standing_sqft`.

The headline used to read "thirty-four percent" here, which was a figure
from an older floor area that stayed in the docstring after the model had
moved.  :func:`validate_advantage` now pins it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .dome_costing import FLOOR_SQFT, radius_for_floor, shell_sqft


@dataclass(frozen=True)
class ExternalFact:
    key: str
    value: float
    units: str
    source: str


EXTERNAL: tuple[ExternalFact, ...] = (
    ExternalFact("cd_hemisphere", 0.42, "drag coefficient",
                 "Hoerner, Fluid-Dynamic Drag: hemisphere, curved face to "
                 "the flow."),
    ExternalFact("cd_cube", 1.05, "drag coefficient",
                 "Hoerner: cube, face normal to the flow."),
    ExternalFact("wall_u", 0.060, "BTU/hr/sq ft/F",
                 "Assembly U-value for a 2x6 wall at about R-17 whole-wall."),
    ExternalFact("heating_degree_days", 4200.0, "F-days",
                 "A middling US heating climate; scales linearly, so the "
                 "ratio below is climate-independent."),
    ExternalFact("wall_height_ft", 8.0, "ft",
                 "Standard stud wall, used for the box being compared."),
    ExternalFact("gable_pitch", 6.0 / 12.0, "rise over run",
                 "A 6:12 roof, the most common residential pitch."),
    ExternalFact("headroom_ft", 6.67, "ft",
                 "Where a floor stops being usable: 6 ft 8 in, the height a "
                 "door header sits at and the US minimum for a hallway or a "
                 "bathroom. A habitable room is held higher still, at seven "
                 "feet, so even this line is lenient -- and it is lenient in "
                 "the dome's favour, since the box clears any such line "
                 "everywhere and the dome does not. This is the only "
                 "headroom number in the project: dome_performance reads it "
                 "from here, so the surface argument and the pony wall "
                 "argument cannot drift apart."),
)

FACT = {item.key: item.value for item in EXTERNAL}


@dataclass(frozen=True)
class Envelope:
    """One building's skin and the volume behind it."""

    name: str
    envelope_sqft: float
    volume_cuft: float
    footprint_sqft: float

    @property
    def skin_per_cuft(self) -> float:
        return self.envelope_sqft / self.volume_cuft

    @property
    def skin_per_floor(self) -> float:
        return self.envelope_sqft / self.footprint_sqft

    def heat_loss_btu_hr_f(self) -> float:
        return self.envelope_sqft * FACT["wall_u"]

    def seasonal_btu(self) -> float:
        return self.heat_loss_btu_hr_f() * FACT["heating_degree_days"] * 24.0


def dome_envelope(floor_sqft: float = FLOOR_SQFT) -> Envelope:
    """The faceted 2V hemisphere: flat triangles, not a smooth sphere."""
    radius_in = radius_for_floor(floor_sqft)
    radius_ft = radius_in / 12.0
    return Envelope(
        name="2V dome",
        envelope_sqft=shell_sqft(radius_in),
        volume_cuft=(2.0 / 3.0) * math.pi * radius_ft ** 3,
        footprint_sqft=floor_sqft,
    )


def box_envelope(floor_sqft: float = FLOOR_SQFT) -> Envelope:
    """A square house with a gable roof and the same floor area."""
    side = math.sqrt(floor_sqft)
    height = FACT["wall_height_ft"]
    pitch = FACT["gable_pitch"]

    walls = 4.0 * side * height
    rise = (side / 2.0) * pitch
    # Two rectangular roof planes plus the two triangular gable ends.
    slope = math.hypot(side / 2.0, rise)
    roof = 2.0 * side * slope
    gables = 2.0 * (0.5 * side * rise)

    return Envelope(
        name="square house",
        envelope_sqft=walls + roof + gables,
        volume_cuft=floor_sqft * height + 0.5 * side * rise * side,
        footprint_sqft=floor_sqft,
    )


@dataclass(frozen=True)
class Advantage:
    """One claim the campaign is allowed to make, and its margin."""

    headline: str
    dome: float
    other: float
    units: str
    lower_is_better: bool = True

    @property
    def ratio(self) -> float:
        return self.dome / self.other if self.other else 0.0

    @property
    def percent_better(self) -> float:
        if self.lower_is_better:
            return (1.0 - self.ratio) * 100.0
        return (self.ratio - 1.0) * 100.0


def advantages(floor_sqft: float = FLOOR_SQFT) -> tuple[Advantage, ...]:
    dome, box = dome_envelope(floor_sqft), box_envelope(floor_sqft)
    return (
        Advantage("Exterior surface to build, seal and paint",
                  dome.envelope_sqft, box.envelope_sqft, "sq ft"),
        Advantage("Surface per cubic foot enclosed",
                  dome.skin_per_cuft, box.skin_per_cuft, "sq ft/cu ft"),
        Advantage("Heat leaving through the envelope",
                  dome.heat_loss_btu_hr_f(), box.heat_loss_btu_hr_f(),
                  "BTU/hr/F"),
        Advantage("Wind load on the shape itself",
                  FACT["cd_hemisphere"], FACT["cd_cube"], "drag coefficient"),
    )


SWEEP_FLOORS: tuple[float, ...] = (80.0, 150.0, 314.0, 500.0, 707.0, 1000.0,
                                   1500.0, 2000.0, 3000.0, 4000.0, 5000.0)
"""The sizes the size-dependence chart and its table both walk.

One tuple so a figure and a paragraph cannot disagree about which houses
were compared.  The top of the range is past the crossover on purpose:
a sweep that stops where the argument stops winning is not a sweep.
"""


def envelope_saving(floor_sqft: float = FLOOR_SQFT) -> float:
    """Percent less exterior surface than the equal-floor box.

    Negative above :func:`envelope_crossover_sqft`, where the box wins.
    Every quotation of the headline in this project goes through here.
    """
    dome, box = dome_envelope(floor_sqft), box_envelope(floor_sqft)
    return (1.0 - dome.envelope_sqft / box.envelope_sqft) * 100.0


def dome_radius_ft(floor_sqft: float = FLOOR_SQFT) -> float:
    """Hemisphere radius -- which is also its height -- for this floor."""
    return radius_for_floor(floor_sqft) / 12.0


def standing_sqft(floor_sqft: float = FLOOR_SQFT) -> tuple[float, float]:
    """Floor area with headroom over it: ``(dome, box)``.

    The box has straight walls taller than the line, so all of its floor
    counts.  The dome is a hemisphere, so its ceiling meets its floor at
    the perimeter and the usable disc is the one inside the radius where
    the shell is still overhead.  This is the concession that equal floor
    area quietly hides.
    """
    radius = dome_radius_ft(floor_sqft)
    head = FACT["headroom_ft"]
    inner = max(0.0, radius ** 2 - head ** 2)
    return math.pi * inner, floor_sqft


def floor_for_standing(standing: float) -> float:
    """The dome floor area needed to get this much standing room."""
    head = FACT["headroom_ft"]
    return math.pi * (standing / math.pi + head ** 2)


def equal_standing_advantage(standing: float = FLOOR_SQFT) -> Advantage:
    """The surface claim re-run at equal *usable* area rather than floor.

    Grows the dome until it stands up over as much ground as the box
    does, then compares skin.  The honest version of the headline, and
    roughly half of it.
    """
    dome = dome_envelope(floor_for_standing(standing))
    box = box_envelope(standing)
    return Advantage("Exterior surface at equal standing room",
                     dome.envelope_sqft, box.envelope_sqft, "sq ft")


def _crossover(gap, low: float = 100.0, high: float = 20000.0) -> float:
    """Where ``gap`` changes sign, by bisection rather than by typing it."""
    if gap(low) * gap(high) > 0.0:
        raise ValueError("no sign change in the bracket")
    for _ in range(120):
        mid = 0.5 * (low + high)
        if gap(low) * gap(mid) <= 0.0:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


def volume_crossover_sqft() -> float:
    """Floor area at which the dome starts enclosing more air than the box.

    Below it, some of the dome's surface saving is not efficiency at all
    -- it is a smaller building.
    """
    return _crossover(lambda area: dome_envelope(area).volume_cuft
                      - box_envelope(area).volume_cuft)


def envelope_crossover_sqft() -> float:
    """Floor area at which the box takes *less* skin than the dome.

    A hemisphere grows upward as it grows outward; a stud wall does not.
    Past this size the whole argument of this module is backwards, and
    the fix is a riser wall rather than a bigger sphere.
    """
    return _crossover(envelope_saving)


def advantage_report(floor_sqft: float = FLOOR_SQFT) -> str:
    dome, box = dome_envelope(floor_sqft), box_envelope(floor_sqft)
    lines = ["WHY A DOME - THE ARGUMENT, CHECKED", ""]
    lines.append(f"  both buildings have the same floor: {floor_sqft:.0f} sq ft")
    lines.append("")
    for item in (dome, box):
        lines.append(f"  {item.name:<16} envelope {item.envelope_sqft:>7.0f} "
                     f"sq ft   volume {item.volume_cuft:>7.0f} cu ft")
    lines.append("")
    for claim in advantages(floor_sqft):
        lines.append(f"  {claim.headline}")
        lines.append(f"      dome {claim.dome:>10.3f}   box {claim.other:>10.3f}"
                     f"   {claim.units}")
        lines.append(f"      -> {claim.percent_better:.0f}% better")
    lines.append("")
    lines.append("external facts this argument rests on:")
    for item in EXTERNAL:
        lines.append(f"  {item.key:<22}{item.value:>10.3f} {item.units:<22} "
                     f"{item.source}")
    return "\n".join(lines)


def validate_advantage() -> None:
    """The campaign may not claim anything this function cannot prove."""
    dome, box = dome_envelope(), box_envelope()

    assert math.isclose(dome.footprint_sqft, box.footprint_sqft), \
        "the comparison is only fair at equal floor area"
    assert dome.envelope_sqft < box.envelope_sqft, \
        (dome.envelope_sqft, box.envelope_sqft)
    assert dome.skin_per_cuft < box.skin_per_cuft

    surface = advantages()[0]
    # The headline number the video will say out loud. If this drifts, the
    # narration is wrong and the test must fail rather than the video ship.
    assert 25.0 < surface.percent_better < 45.0, surface.percent_better

    heat = advantages()[2]
    # Heat loss is proportional to area at equal U, so the margins must
    # agree exactly -- a good check that neither was fudged.
    assert math.isclose(heat.percent_better, surface.percent_better,
                        rel_tol=1e-9)

    wind = advantages()[3]
    assert wind.percent_better > 50.0

    # The shape wins at house sizes -- but NOT at every size, and the
    # loop that used to stop at 707 sq ft implied otherwise.
    for floor in (80.0, 314.0, 707.0):
        assert dome_envelope(floor).envelope_sqft < box_envelope(floor).envelope_sqft

    # One function behind the headline, agreeing with the Advantage.
    assert math.isclose(envelope_saving(), surface.percent_better)

    # Size dependence, in the direction that hurts: the margin falls
    # monotonically across the whole sweep and ends up negative.
    savings = [envelope_saving(area) for area in SWEEP_FLOORS]
    assert savings == sorted(savings, reverse=True), savings
    assert savings[0] > 60.0 and savings[-1] < 0.0, (savings[0], savings[-1])

    crossover = envelope_crossover_sqft()
    assert 3500.0 < crossover < 5000.0, crossover
    assert envelope_saving(crossover * 1.2) < 0.0, "the box must be allowed to win"
    assert math.isclose(envelope_saving(crossover), 0.0, abs_tol=1e-6)

    # Below the volume crossover the dome is also a smaller building, so
    # the surface margin is partly a size difference rather than a shape
    # one. The reference build sits below it; say so rather than hide it.
    volume_line = volume_crossover_sqft()
    assert 800.0 < volume_line < 1300.0, volume_line
    assert dome.volume_cuft < box.volume_cuft, "reference dome encloses less"
    assert dome_envelope(volume_line * 1.5).volume_cuft \
        > box_envelope(volume_line * 1.5).volume_cuft

    # Equal floor is not equal usable area: a hemisphere has no headroom
    # at its rim, and the honest margin is about half the headline.
    dome_stand, box_stand = standing_sqft()
    assert box_stand == FLOOR_SQFT, "straight walls clear the line everywhere"
    assert 0.50 < dome_stand / FLOOR_SQFT < 0.70, dome_stand

    # The ring a bare hemisphere cannot stand up in is pi * headroom^2, and
    # that is a *constant*: it does not depend on the dome's radius at all.
    # A bigger dome does not fix the rim, it only dilutes it. The pony wall
    # chapter turns on this, so it is pinned here at the source.
    dead_ring = math.pi * FACT["headroom_ft"] ** 2
    for floor in (200.0, 314.0, 365.0, 1000.0, 3000.0):
        lost = floor - standing_sqft(floor)[0]
        assert math.isclose(lost, dead_ring, rel_tol=1e-9), (floor, lost)
    assert math.isclose(floor_for_standing(dome_stand), FLOOR_SQFT), \
        "the standing-room round trip must close"

    honest = equal_standing_advantage()
    assert 0.0 < honest.percent_better < surface.percent_better, \
        (honest.percent_better, surface.percent_better)

    # Two sentences in the "Less Skin for the Same Floor" chapter describe
    # these margins in words rather than figures. Prose cannot be a live
    # token, so it is pinned here, at both reference floors: this module's
    # round 314 and the book's own two-tree dome at 365.
    #
    # The two claims do not have the same reach, and the bands say so. The
    # per-cubic-foot share climbs steeply with size -- it is already past
    # 0.44 at 500 sq ft -- so that sentence is written "at this size" and
    # is only checked at these sizes. The standing-room deduction is much
    # steadier, and is checked further out.
    for floor in (314.0, 365.0):
        claims = advantages(floor)
        share = claims[1].percent_better / claims[0].percent_better
        assert 0.22 < share < 0.35, \
            ("per-cubic-foot margin is no longer 'roughly a third'",
             floor, share)

    for floor in (314.0, 365.0, 500.0, 707.0):
        headline = advantages(floor)[0].percent_better
        share = equal_standing_advantage(floor).percent_better / headline
        assert 0.33 < share < 0.52, \
            ("equal-standing margin is no longer 'well under half'",
             floor, share)

    # Two numbers, one fact. dome_performance borrows this rather than
    # declaring its own, and for a while it declared its own.
    from . import dome_performance as _performance  # noqa: PLC0415
    assert _performance.FACT["headroom_ft"] == FACT["headroom_ft"], \
        "headroom is declared twice again"

    for item in EXTERNAL:
        assert item.source and item.units and item.value > 0.0
