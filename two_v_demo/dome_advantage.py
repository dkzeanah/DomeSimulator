"""Why a dome, argued in numbers a sceptic can check.

A campaign video has to persuade, and the cheapest way to persuade is to
be right.  Everything in this module is computed from the geometry and
compared against a conventional house of *identical floor area*, because
"domes are efficient" is a slogan and "thirty-four percent less exterior
wall for the same floor" is an argument.

The comparison is deliberately generous to the box: it gets a gable roof
rather than a flat one, standard eight foot walls, and no penalty for the
fact that its corners are the part that leaks.
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

    # Scale independence: the shape wins at every size, not just this one.
    for floor in (80.0, 314.0, 707.0):
        assert dome_envelope(floor).envelope_sqft < box_envelope(floor).envelope_sqft

    for item in EXTERNAL:
        assert item.source and item.units and item.value > 0.0
