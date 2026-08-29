"""Exact saw settings for a hubless dome strut, and how to verify them.

The compound cut is the hardest operation in the whole build, and it is
hard for a reason that is not obvious: it is two cuts on two different
machines, and each machine can only do the one the other cannot.

    The table saw rips the bevel along the length.
        That angle decides how a triangle meets its NEIGHBOUR.
    The mitre saw crosscuts the ends.
        That angle decides how a strut meets the other two struts of its
        OWN triangle.

Either one alone produces a part that looks perfectly good and fits
nothing.  Everything below is measured off the same 2V hemisphere the
rest of the package uses; nothing here is a table copied from anywhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from .hubless_geometry import (
    TYPICAL_MITRE_SAW_MAX_DEG,
    compound_setups,
    hubless_struts,
)


# ----------------------------------------------------------------------
# Tool limits and shop conventions -- the parts that are not geometry
# ----------------------------------------------------------------------

TABLE_SAW_MAX_TILT_DEG = 45.0
"""Every cabinet and contractor saw tilts to 45 degrees. The bevels this
dome needs are nowhere near that, which is why the rip is the easy half."""

BLADE_DIAMETER_IN = 10.0
STOCK_WIDTH_IN = 3.5
"""Nominal 2x4 face width. Uniform width is the master reference for the
whole job: every angle downstream is measured from it."""

STOCK_THICKNESS_IN = 1.5

FIVE_CUT_MULTIPLIER = 4.0
"""The five-cut method multiplies a sled's fence error by four, which is
what makes an error too small to measure directly become measurable."""


@dataclass(frozen=True)
class SawSetting:
    """One machine setting, in the words the machine's own scale uses."""

    machine: str
    control: str
    value_deg: float
    reachable: bool
    note: str


@dataclass(frozen=True)
class CutPlan:
    """Every setting needed to make one class of strut end."""

    name: str
    mitre_deg: float
    bevel_deg: float
    ends: int

    @property
    def mitre_reachable(self) -> bool:
        return self.mitre_deg <= TYPICAL_MITRE_SAW_MAX_DEG

    @property
    def complement_deg(self) -> float:
        """The same cut taken from the other reference face."""
        return 90.0 - self.mitre_deg

    @property
    def sled_fence_deg(self) -> float:
        """Angle to build into a crosscut sled's fence, from the blade.

        A sled fence is set against the blade, not against square, so the
        number to build to is the complement -- and it is comfortably
        inside what a protractor and a trammel can lay out.
        """
        return self.complement_deg

    @property
    def bevel_reachable(self) -> bool:
        return self.bevel_deg <= TABLE_SAW_MAX_TILT_DEG

    def settings(self) -> tuple[SawSetting, ...]:
        return (
            SawSetting(
                "table saw", "blade tilt", self.bevel_deg, self.bevel_reachable,
                "rip along the full length, one pass per strut",
            ),
            SawSetting(
                "mitre saw", "table swing", self.mitre_deg, self.mitre_reachable,
                "off the scale on a common saw -- use the sled instead"
                if not self.mitre_reachable else "set directly",
            ),
            SawSetting(
                "crosscut sled", "fence to blade", self.sled_fence_deg, True,
                "the same cut, referenced off the blade instead of the fence",
            ),
        )


@lru_cache(maxsize=1)
def cut_plans() -> tuple[CutPlan, ...]:
    """One plan per distinct compound setup, commonest first."""
    return tuple(
        CutPlan(
            name=f"SET-{index + 1}",
            mitre_deg=item.mitre_deg,
            bevel_deg=item.bevel_deg,
            ends=item.count,
        )
        for index, item in enumerate(compound_setups())
    )


# ----------------------------------------------------------------------
# Verification: how you know the setting is right before you cut 240 ends
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BevelCheck:
    """Proving a blade tilt without trusting the saw's own scale.

    Rip two offcuts at the same setting and put the two cut faces
    together.  If the tilt is correct the pair closes to exactly the
    dihedral the dome wants, and any error in the setting shows up
    doubled -- which is the whole point of checking it this way.
    """

    bevel_deg: float
    dihedral_deg: float

    @property
    def paired_angle_deg(self) -> float:
        return 180.0 - 2.0 * self.bevel_deg

    def error_for(self, measured_pair_deg: float) -> float:
        """Half the pair error is the error in the blade tilt."""
        return (measured_pair_deg - self.paired_angle_deg) * 0.5


@dataclass(frozen=True)
class FiveCutCheck:
    """The five-cut method, for squaring a sled fence to the blade.

    Cut a scrap four times, rotating it a quarter turn between cuts, then
    slice a fifth strip off.  Measure that strip at both ends: the
    difference is four times the fence error, so an error far too small to
    see with a square becomes an easy measurement.
    """

    strip_length_in: float
    wide_end_in: float
    narrow_end_in: float

    @property
    def difference_in(self) -> float:
        return self.wide_end_in - self.narrow_end_in

    @property
    def fence_error_deg(self) -> float:
        if self.strip_length_in <= 0.0:
            return 0.0
        return math.degrees(math.atan(
            self.difference_in / (FIVE_CUT_MULTIPLIER * self.strip_length_in)
        ))

    @property
    def error_over_a_strut(self) -> float:
        """What that error costs across a real strut's width."""
        return math.tan(math.radians(self.fence_error_deg)) * STOCK_WIDTH_IN


def blade_projection_in(bevel_deg: float, thickness: float = STOCK_THICKNESS_IN
                        ) -> float:
    """How far a tilted blade must stand above the table to cut through.

    A tilted blade travels further through the same thickness, so a height
    set square will not cut through once the blade is over.
    """
    return thickness / math.cos(math.radians(bevel_deg))


def sled_capacity_in(mitre_deg: float, stock_width: float = STOCK_WIDTH_IN
                     ) -> float:
    """Blade travel needed to cross a strut held at this angle.

    The steeper the fence, the longer the cut, which is why an angle this
    far from square eats sled capacity faster than people expect.
    """
    return stock_width / max(0.05, math.cos(math.radians(90.0 - mitre_deg)))


# ----------------------------------------------------------------------
# The written procedure
# ----------------------------------------------------------------------

STEPS: tuple[tuple[str, str], ...] = (
    ("1. Rip every stick to one width",
     "Every angle after this is measured from the edge of the board. If the "
     "boards are not all the same width, nothing downstream can be right, "
     "and no amount of care at the mitre saw will rescue it. Rip the whole "
     "pile in one session, with the fence untouched."),
    ("2. Mark the mating edge",
     "Only one long edge of each strut gets the bevel: the one that will "
     "lie against the neighbouring triangle. Mark it on every stick before "
     "any of them go near the blade. This is the single most common way to "
     "produce a pile of mirror-image scrap."),
    ("3. Set the blade tilt",
     "Set the tilt to the bevel for that strut class. Do not trust the "
     "saw's scale: rip two offcuts, put the cut faces together, and "
     "measure the pair. The pair reads twice the error, so anything you "
     "cannot see in the single is obvious in the double."),
    ("4. Rip the bevel, full length, one pass",
     "Featherboard before the blade, push stick past it, and keep the "
     "marked edge against the fence for every stick without exception. "
     "This cut decides how the triangle meets its neighbour."),
    ("5. Build the sled before you touch the ends",
     "The mitres this dome wants are past the stop on a common mitre saw, "
     "so the ends are cut on a crosscut sled whose fence is built to the "
     "complement and referenced off the blade instead of off square. "
     "Build it, prove it with the five-cut method, and only then cut a "
     "part you care about."),
    ("6. Cut the relief lap into the sled fence",
     "The strut sits against the sled fence with one end projecting past "
     "it. The blade has to finish that cut flush, so the fence needs a lap "
     "cut away at the blade path -- deep enough for the blade to pass the "
     "full width of the strut, no deeper. Cut it once, with the sled in "
     "the position it will always be used in."),
    ("7. Set the stop block, not the tape",
     "Length comes from a stop block clamped to the sled, never from a "
     "pencil line. Two hundred and forty ends measured individually will "
     "drift; two hundred and forty ends against one block will not."),
    ("8. Cut the first end",
     "Bevelled edge down and against the fence, marked face up, strut "
     "butted to the stop, end projecting over the lap. One pass, all the "
     "way through, and let the blade stop before lifting."),
    ("9. Turn the strut, do not flip it",
     "The second end is not a mirror of the first. Rotate the strut end "
     "for end about its long axis in the sled -- a quarter turn, the way "
     "the sled was built for -- so the bevel stays on the same side of "
     "the dome. Flipping it face over face puts the bevel on the wrong "
     "side and the strut will not close its triangle."),
    ("10. Batch by setting, never by triangle",
     "Cut every end that shares a setting before you change anything. "
     "Changing a setting is where error enters, so change it as few times "
     "as the job allows -- six times, not two hundred and forty."),
    ("11. Dry-assemble one triangle before cutting the rest",
     "Three struts, no fasteners, laid on a flat floor. If it closes with "
     "no gap at any corner and lies flat, the settings are right. If it "
     "does not, you have lost three sticks instead of the whole pile."),
)


FAILURES: tuple[tuple[str, str], ...] = (
    ("Bevel on the wrong edge",
     "The strut looks correct and mates the wrong way. Marking the edge "
     "before ripping is the only reliable prevention."),
    ("Complement confusion",
     "Setting the sled to the mitre instead of its complement gives a cut "
     "that is wrong by exactly the amount that looks plausible."),
    ("Flipped instead of turned",
     "Flipping face over face between ends mirrors the part. It will look "
     "right on the bench and refuse to close a triangle."),
    ("Stop block creep",
     "A clamped block walks under repeated impact. Check it against a "
     "reference stick every twenty cuts."),
    ("Blade not through",
     "A tilted blade needs more height to clear the same thickness. Set "
     "the height after the tilt, never before."),
)


def sawing_report() -> str:
    """A portable audit of every setting the cutting lesson states."""
    lines = ["HUBLESS COMPOUND CUT - SAW SETTINGS AUDIT", ""]
    lines.append(f"stock {STOCK_WIDTH_IN:g} x {STOCK_THICKNESS_IN:g} in, "
                 f"{BLADE_DIAMETER_IN:g} in blade")
    lines.append(f"mitre saw reaches {TYPICAL_MITRE_SAW_MAX_DEG:g} deg, "
                 f"table saw tilts to {TABLE_SAW_MAX_TILT_DEG:g} deg")
    lines.append("")
    plans = cut_plans()
    lines.append(f"{len(plans)} distinct setups covering "
                 f"{sum(item.ends for item in plans)} strut ends:")
    for plan in plans:
        lines.append(
            f"  {plan.name}  mitre {plan.mitre_deg:7.3f}  "
            f"bevel {plan.bevel_deg:6.3f}  x{plan.ends}"
        )
        for setting in plan.settings():
            flag = "" if setting.reachable else "   <- NOT REACHABLE"
            lines.append(
                f"      {setting.machine:<14} {setting.control:<14} "
                f"{setting.value_deg:7.3f} deg{flag}"
            )
        lines.append(
            f"      blade height for the rip: "
            f"{blade_projection_in(plan.bevel_deg):.4f} in "
            f"(square would be {STOCK_THICKNESS_IN:g})"
        )
        lines.append(
            f"      sled travel across the strut: "
            f"{sled_capacity_in(plan.mitre_deg):.3f} in"
        )
    lines.append("")
    lines.append("bevel verification, by pairing two offcuts:")
    for plan in plans:
        check = BevelCheck(plan.bevel_deg, 180.0 - 2.0 * plan.bevel_deg)
        lines.append(
            f"  bevel {plan.bevel_deg:6.3f} -> the pair must read "
            f"{check.paired_angle_deg:7.3f} deg"
        )
    lines.append("")
    lines.append("five-cut check on the sled fence:")
    for difference in (0.001, 0.005, 0.020):
        check = FiveCutCheck(20.0, 2.0 + difference, 2.0)
        lines.append(
            f"  {difference:.3f} in across a 20 in strip "
            f"-> fence off by {check.fence_error_deg:.4f} deg "
            f"= {check.error_over_a_strut:.5f} in across a strut"
        )
    lines.append("")
    lines.append("procedure:")
    for title, _ in STEPS:
        lines.append(f"  {title}")
    lines.append("")
    lines.append("the five ways it goes wrong:")
    for title, _ in FAILURES:
        lines.append(f"  {title}")
    return "\n".join(lines)


def validate_sawing() -> None:
    """Prove the settings before any of them reach a screen."""
    plans = cut_plans()
    assert plans, "there must be at least one cut plan"
    assert sum(item.ends for item in plans) == 2 * len(hubless_struts())

    for plan in plans:
        # The whole premise of the chapter.
        assert not plan.mitre_reachable, plan
        assert plan.complement_deg <= TYPICAL_MITRE_SAW_MAX_DEG, plan
        # And the other half: the bevel is never the problem.
        assert plan.bevel_reachable, plan
        assert plan.sled_fence_deg == plan.complement_deg
        machines = {item.machine for item in plan.settings()}
        assert machines == {"table saw", "mitre saw", "crosscut sled"}, machines
        # A tilted blade always needs more height, never less.
        projection = blade_projection_in(plan.bevel_deg)
        assert projection >= STOCK_THICKNESS_IN, (plan.bevel_deg, projection)
        if plan.bevel_deg > 0.0:
            assert projection > STOCK_THICKNESS_IN
        # A steep fence angle always costs travel.
        assert sled_capacity_in(plan.mitre_deg) > STOCK_WIDTH_IN, plan

    # Pairing two offcuts must reproduce the fold the dome asked for.
    for plan in plans:
        check = BevelCheck(plan.bevel_deg, 180.0 - 2.0 * plan.bevel_deg)
        assert abs(check.paired_angle_deg - check.dihedral_deg) < 1e-9
        # An error in the setting shows up doubled in the pair.
        assert abs(check.error_for(check.paired_angle_deg + 1.0) - 0.5) < 1e-9

    # The five-cut method multiplies the error it is looking for.
    small = FiveCutCheck(20.0, 2.001, 2.0)
    large = FiveCutCheck(20.0, 2.020, 2.0)
    assert large.fence_error_deg > small.fence_error_deg > 0.0
    assert FiveCutCheck(20.0, 2.0, 2.0).fence_error_deg == 0.0
    assert small.error_over_a_strut < 0.01, small.error_over_a_strut

    assert len(STEPS) >= 10
    assert len(FAILURES) >= 5
