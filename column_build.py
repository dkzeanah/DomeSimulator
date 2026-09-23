"""Building a utility core, in the order a person actually builds one.

:mod:`seed_model` knows what a core *is* -- fourteen objects, four services,
$1,405. That is a specification. This is the other document: what you buy,
what you need on the bench, and what you do first, second and third, written
so somebody can assemble one without having designed it.

The core is the right module to start with, and not only because it is the
hardest. It is the one part of the dome that is **the same in every dome** --
every size, every fit-out, every shape shares this assembly, because the
interface it plugs into never changes. Get the core into production and the
rest of the product line is panels.

Three rules the sequence obeys, and they are the reason it is this order and
not a plausible-looking other one:

* **Wet before dry.** Every plumbing joint is made and pressure-tested before
  a single electrical component is mounted, so a leak is found while the only
  thing it can damage is a floor.
* **Heavy before fragile.** The housing, the stack and the manifold go in
  while the chase is open and can be manhandled. The sub-panel goes in last
  because it is the thing you do not want to be reaching past.
* **Nothing is buried.** Every joint in the finished core is reachable behind
  one cover panel. A step that would bury a connection is a step in the wrong
  order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import seed_model


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("shop_rate_usd_per_hour", 28.00, "USD/hour",
     "borrowed: the build labour rate seed_model already pays. A core built "
     "in the shop is paid at the same rate as a dome built on site"),
    ("first_build_multiple", 2.4, "multiple",
     "assumption: how much longer the first one takes than the tenth. It is "
     "here because quoting the practised time to somebody building their "
     "first is how a schedule gets missed"),
    ("pressure_test_psi", 80.0, "psi",
     "standard: the pressure a domestic water assembly is held at, for the "
     "period below, before anything is closed in"),
    ("pressure_test_min", 30.0, "minutes",
     "standard: how long it is held. Shorter finds only the bad leaks"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _u, _w in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    if name in CONSTANTS:
        return CONSTANTS[name]
    return seed_model.declared(name)


# ----------------------------------------------------------------------
# What you buy and what you need
# ----------------------------------------------------------------------

TOOLS: tuple[tuple[str, str], ...] = (
    ("Cordless driver", "everything is screwed, nothing is nailed"),
    ("Step drill", "clean holes through the housing for the grommets"),
    ("PEX crimp tool and go/no-go gauge",
     "the gauge is not optional -- an uncrimped ring passes a pressure test "
     "and fails in a year"),
    ("Tubing cutter", "a square cut on PEX and on the 2 in stack"),
    ("Deburring tool", "a burr in the stack is where the blockage starts"),
    ("Torque screwdriver", "terminals in the sub-panel are torque-specified "
                           "and a loose terminal is how a panel burns"),
    ("Multimeter", "continuity and polarity before the feeder goes live"),
    ("Pressure test pump and gauge", "for the water test at the end of "
                                     "stage three"),
    ("Spirit level", "the chase is plumb or the seal cap does not seat"),
)


MATERIALS: tuple[tuple[str, str, float, str], ...] = (
    # (service, what, quantity, unit)
    ("structure", "12 in square insulated chase section", 4.0, "sections"),
    ("structure", "base flange and gasket", 1.0, "set"),
    ("structure", "apex sleeve with laminating flange", 1.0, "each"),
    ("structure", "seal cap, gasket and six over-centre catches", 1.0, "set"),
    ("structure", "removable cover panel and captive fasteners", 1.0, "set"),
    ("structure", "grommets for every penetration of the chase", 8.0, "each"),
    ("water", "PEX-A, 1/2 in", 24.0, "ft"),
    ("water", "crimp rings", 16.0, "each"),
    ("water", "four-port manifold with valves", 1.0, "each"),
    ("water", "full-port isolating valve", 1.0, "each"),
    ("water", "capped fixture tails", 4.0, "each"),
    ("drain", "2 in ABS stack", 11.0, "ft"),
    ("drain", "2 in P-trap", 1.0, "each"),
    ("drain", "floor-port boot and clamp", 1.0, "each"),
    ("drain", "solvent cement and primer", 1.0, "tin"),
    ("power", "50 A four-wire feeder cord", 12.0, "ft"),
    ("power", "recessed inlet, 50 A", 1.0, "each"),
    ("power", "eight-space load centre with 50 A main", 1.0, "each"),
    ("power", "branch breakers", 4.0, "each"),
    ("power", "12/2 for the outlet ring", 60.0, "ft"),
    ("power", "14/2 for the lighting drop", 25.0, "ft"),
    ("power", "receptacles, boxes and covers", 6.0, "each"),
    ("power", "cable clamps and strain reliefs", 10.0, "each"),
)


def materials(service: str | None = None):
    if service is None:
        return MATERIALS
    return tuple(row for row in MATERIALS if row[0] == service)


# ----------------------------------------------------------------------
# The sequence
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Step:
    """One thing you do, with what it needs and what it must not skip."""

    number: int
    stage: str
    title: str
    detail: str
    minutes: float
    tools: tuple[str, ...] = ()
    checkpoint: str = ""
    parts: tuple[str, ...] = field(default_factory=tuple)


STEPS: tuple[Step, ...] = (
    # -- stage 1: the chase --------------------------------------------
    Step(1, "chase", "Set the base flange on the bench",
         "The whole core is built upside down on a bench and stood up at the "
         "end. Working at waist height on a flange you can walk around is "
         "the difference between a four-hour job and a day of kneeling.",
         20.0, ("Spirit level", "Cordless driver"),
         "Flange square to the bench and the bolt pattern matching the "
         "pad's service port template.",
         ("base flange and gasket",)),
    Step(2, "chase", "Stack and pin the chase sections",
         "Four sections dry-assembled, pinned, checked for plumb over the "
         "whole run, then taken apart again. Nothing is glued or screwed "
         "yet -- this is the fit check, and the chase is the one part where "
         "an error at the bottom is an inch of error at the apex.",
         35.0, ("Spirit level", "Cordless driver"),
         "Plumb within 1/8 in over the full height, dry.",
         ("12 in square insulated chase section",)),
    Step(3, "chase", "Drill and grommet every penetration",
         "Mark where the drain, the water riser, the feeder and each branch "
         "leave the chase. Step-drill them, deburr, and fit a grommet in "
         "every one. Do this now, with the sections apart and on the bench, "
         "and never afterwards with a hole saw inside a finished core.",
         40.0, ("Step drill", "Deburring tool"),
         "Every hole grommeted. No bare edge anywhere a cable or a pipe "
         "will move against.",
         ("grommets for every penetration of the chase",)),

    # -- stage 2: drain -------------------------------------------------
    Step(4, "drain", "Cut, dry-fit and mark the stack",
         "The 2 in stack runs the full height with the trap at its foot. "
         "Dry-fit the whole run and mark every joint across the socket "
         "before you cement anything -- solvent cement gives you about five "
         "seconds and no second chance at alignment.",
         30.0, ("Tubing cutter", "Deburring tool"),
         "Every joint marked. Trap at the foot, and the outlet pointing at "
         "where the floor port will be.",
         ("2 in ABS stack", "2 in P-trap")),
    Step(5, "drain", "Prime and cement the stack",
         "Primer, cement, quarter turn, hold. Work bottom to top so gravity "
         "is not pulling a fresh joint apart, and do not touch it for "
         "fifteen minutes.",
         25.0, (),
         "No joint moved after setting. Stack rigid when the top is "
         "twisted by hand.",
         ("solvent cement and primer",)),
    Step(6, "drain", "Fit the floor-port boot",
         "The gasketed boot at the bottom is what the pad's drain meets. It "
         "is a joint that gets made once by the host and then left alone for "
         "the life of the pad, so it is worth the extra five minutes now.",
         15.0, ("Cordless driver",),
         "Boot clamped, square, and the clamp screw reachable from inside "
         "the finished core.",
         ("floor-port boot and clamp",)),

    # -- stage 3: water, and the test ----------------------------------
    Step(7, "water", "Mount the manifold and the isolating valve",
         "Manifold at chest height on the chase wall, isolating valve below "
         "it at knee height where somebody who does not know the building "
         "will look for it. Both on the opposite face from the sub-panel.",
         25.0, ("Cordless driver",),
         "Valve handle has clearance to swing fully with the cover on.",
         ("four-port manifold with valves", "full-port isolating valve")),
    Step(8, "water", "Run and crimp the riser and the tails",
         "Riser from the base flange up to the valve, valve to manifold, "
         "then four capped tails off the manifold. Every crimp gets the "
         "go/no-go gauge -- every single one, including the ones you are "
         "sure about.",
         45.0, ("PEX crimp tool and go/no-go gauge", "Tubing cutter"),
         "Every crimp passes the gauge. Tails capped, not left open.",
         ("PEX-A, 1/2 in", "crimp rings", "capped fixture tails")),
    Step(9, "water", "Pressure test, and do not skip it",
         f"Cap the riser, pump to "
         f"{declared('pressure_test_psi'):.0f} psi and leave it "
         f"{declared('pressure_test_min'):.0f} minutes with a gauge on it. "
         "This is the last moment a leak costs nothing. After this the "
         "electrical goes in and a leak costs the panel.",
         35.0, ("Pressure test pump and gauge",),
         f"No measurable drop over {declared('pressure_test_min'):.0f} "
         "minutes. A drop means find it now, not after stage four.",
         ()),

    # -- stage 4: power -------------------------------------------------
    Step(10, "power", "Mount the load centre and the inlet",
         "Sub-panel at chest height on the dry face, recessed inlet at the "
         "base. Both on the opposite side of the chase from the water, "
         "which is the rule the whole layout is built around.",
         30.0, ("Cordless driver", "Spirit level"),
         "Panel door opens fully with the cover on. Inlet reachable from "
         "outside the dome's skirt.",
         ("eight-space load centre with 50 A main", "recessed inlet, 50 A")),
    Step(11, "power", "Land the feeder",
         "Feeder cord from the inlet to the main lugs. Strain relief at both "
         "ends. Torque every lug to the figure printed inside the panel "
         "door, with a torque screwdriver, not by feel.",
         30.0, ("Torque screwdriver", "Multimeter"),
         "Every lug at its specified torque. Continuity and polarity "
         "checked before anything is energised.",
         ("50 A four-wire feeder cord", "cable clamps and strain reliefs")),
    Step(12, "power", "Fit breakers and run the branches",
         "Four breakers: outlet ring, lighting, the window unit, and the "
         "spare that exists so the first snap-in module does not need the "
         "panel opened. The ring leaves the chase through its grommet and "
         "goes into the seam channel.",
         50.0, ("Cordless driver", "Multimeter"),
         "Every branch identified at the panel with a written legend, not "
         "from memory.",
         ("branch breakers", "12/2 for the outlet ring",
          "14/2 for the lighting drop", "receptacles, boxes and covers")),

    # -- stage 5: close and stand --------------------------------------
    Step(13, "close", "Fit the apex sleeve and the seal cap",
         "Sleeve onto the top of the chase, cap onto the sleeve, six "
         "catches set so the gasket compresses evenly. Open and close it "
         "five times: if it is stiff on the bench it will be impossible at "
         "the top of a dome in the rain.",
         25.0, ("Cordless driver",),
         "Cap seats and releases by hand, no tool, gasket evenly "
         "compressed all round.",
         ("apex sleeve with laminating flange",
          "seal cap, gasket and six over-centre catches")),
    Step(14, "close", "Hang the cover panel and stand it up",
         "Cover on captive fasteners so there is no bag of screws to lose. "
         "Then two people stand the core up, and it goes onto the pad's "
         "service port as one object.",
         25.0, ("Cordless driver",),
         "Every joint made in the last thirteen steps still reachable with "
         "the cover off and nothing behind anything else.",
         ("removable cover panel and captive fasteners",)),
)


STAGES: tuple[tuple[str, str], ...] = (
    ("chase", "Build the chase on the bench"),
    ("drain", "Drain first, because it is the one you cannot re-route"),
    ("water", "Water, then prove it before anything electrical exists"),
    ("power", "Power last, into a core already known to be dry"),
    ("close", "Close it, prove the cap, stand it up"),
)


def steps(stage: str | None = None) -> tuple[Step, ...]:
    if stage is None:
        return STEPS
    return tuple(s for s in STEPS if s.stage == stage)


def stage_minutes(stage: str) -> float:
    return sum(s.minutes for s in steps(stage))


def practised_hours() -> float:
    """How long the tenth one takes."""
    return sum(s.minutes for s in STEPS) / 60.0


def first_build_hours() -> float:
    """How long the first one takes, which is the number that matters."""
    return practised_hours() * declared("first_build_multiple")


def labour_usd(first: bool = False) -> float:
    hours = first_build_hours() if first else practised_hours()
    return hours * declared("shop_rate_usd_per_hour")


def report() -> str:
    lines = [
        "BUILDING ONE UTILITY CORE",
        f"  practised {practised_hours():.1f} h  "
        f"(${labour_usd():,.0f} at "
        f"${declared('shop_rate_usd_per_hour'):.0f}/h)",
        f"  first one {first_build_hours():.1f} h  "
        f"(${labour_usd(True):,.0f}) -- "
        f"{declared('first_build_multiple'):.1f} times as long",
        f"  parts in the core cost "
        f"${seed_model.column_group().cost:,.0f}",
        "",
        "  TOOLS ON THE BENCH",
    ]
    for tool, why in TOOLS:
        lines.append(f"    {tool:<38} {why}")
    lines.append("")
    for stage, title in STAGES:
        lines.append(f"  {title.upper()}  ({stage_minutes(stage):.0f} min)")
        for step in steps(stage):
            lines.append(f"    {step.number:>2}. {step.title} "
                         f"[{step.minutes:.0f} min]")
            lines.append(f"        {step.detail}")
            if step.checkpoint:
                lines.append(f"        CHECK: {step.checkpoint}")
        lines.append("")
    lines.append("  MATERIALS")
    for service, what, qty, unit in MATERIALS:
        lines.append(f"    {service:<10} {what:<46} {qty:>6.0f} {unit}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_column_build() -> None:
    """The sequence has to be buildable, and in this order for a reason."""
    assert len(STEPS) >= 12
    assert [s.number for s in STEPS] == list(range(1, len(STEPS) + 1))
    for step in STEPS:
        assert step.title and step.detail, step.number
        assert step.minutes > 0.0, step.number
        assert step.stage in {key for key, _t in STAGES}, step.number

    # Every stage is used and in the order STAGES declares.
    order = [key for key, _t in STAGES]
    seen = [s.stage for s in STEPS]
    assert seen == sorted(seen, key=order.index), seen

    # The three rules, checked rather than asserted in prose.
    first_power = min(s.number for s in STEPS if s.stage == "power")
    test = next(s for s in STEPS if "Pressure test" in s.title)
    assert test.number < first_power, (
        "electrical work starts before the water has been proved")
    last_water = max(s.number for s in STEPS if s.stage == "water")
    assert last_water < first_power, "water and power stages interleave"

    # Every tool a step names is on the bench list.
    bench = {name for name, _why in TOOLS}
    for step in STEPS:
        for tool in step.tools:
            assert tool in bench, (step.number, tool)

    # Every part a step names is on the materials list.
    catalogue = {what for _s, what, _q, _u in MATERIALS}
    for step in STEPS:
        for part in step.parts:
            assert part in catalogue, (step.number, part)

    # Every material is used by some step, or it is on the list for nothing.
    used = {part for step in STEPS for part in step.parts}
    unused = catalogue - used
    assert not unused, f"bought but never fitted: {sorted(unused)}"

    # Checkpoints are the point of a process sheet.
    assert sum(1 for s in STEPS if s.checkpoint) >= len(STEPS) - 2

    assert practised_hours() > 0.0
    assert first_build_hours() > practised_hours()
    assert declared("first_build_multiple") > 1.0


if __name__ == "__main__":
    validate_column_build()
    print(report())
