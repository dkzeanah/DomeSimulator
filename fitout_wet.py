"""Two things the dome needs before anybody can live in it.

**Panels that pull in.** The bay used to be a sandwich held by friction: an
inner panel dropped onto the wedge's lip from inside, an outer panel
compression-fitted from outside. That works on a wall and it is optimistic on
a dome, because most of a dome's bays are overhead and a friction fit
overhead is a fit fighting gravity for the life of the building.

So the panel moves to the **outside face** and is pulled *into* the frame by
screws that land in threaded inserts set into the wedges. Gravity now works
with the fixing rather than against it, the panel is the weather barrier
rather than a layer under one, and it comes off with a driver. Everything the
soft shell stacks -- membrane, quilt, cap -- sits on top of it.

The inserts have a second job that is worth more than the first. They are a
**grid of structural anchor points on a known pitch**, so a shelf, a bunk, a
kitchen run or a hanging rail can span two or three triangles and bolt to
them. A bay does not have to be *used* to be useful; it is a barrier with
fixings in it.

**A shower that does not flood the house.** A dome has no internal walls, a
round floor, and one drain. Water that gets away from the tray does not meet
a wall -- it runs to whichever part of the floor is lowest and stays there.
So the wet area is a fabricated insert rather than a curtain and a hope: a
sloped tray that falls to the drain, a raised kerb that stops water tracking
sideways, and two barriers rather than one.

And the constraint that is not negotiable: the utility column carries a
sub-panel and a 50 A feeder, and the shower is the wettest place in the
building. This module states the separation it requires and the selftest
refuses a layout that does not have it.

Nothing here decides geometry; sizes come from :mod:`seed_model`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import seed_model


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    # -- panels that pull in ------------------------------------------
    ("insert_usd_each", 1.35, "USD each",
     "assumption: a stainless threaded insert driven into the wedge's outer "
     "face. It takes the thread so the wood never does"),
    ("inserts_per_bay", 4.0, "each",
     "assumption: three near the corners and one at the middle of the "
     "longest edge, which is where an unsupported panel edge drums"),
    ("panel_screw_usd_each", 0.22, "USD each",
     "assumption: a stainless flange-head screw with a bonded washer"),
    ("insert_min_each", 1.6, "minutes each",
     "assumption: drill, drive, check. It is the slowest part of the frame "
     "build and it is why the process sheet counts it"),
    ("anchor_rating_lb", 180.0, "lb",
     "assumption: what one insert in end-grain-free pine holds in shear "
     "before it is the wood that fails, at a safety factor of 4"),

    # -- the wet area --------------------------------------------------
    ("shower_tray_ft", 3.0, "ft",
     "assumption: the side of the square wet area. Smaller than a house "
     "shower because the dome is 277 sq ft and this is the honest size"),
    ("tray_fall_per_ft", 0.25, "in/ft",
     "standard: the fall a wet-room tray needs to drain reliably. Less and "
     "it holds water, more and you feel the slope underfoot"),
    ("tray_usd_per_sqft", 14.00, "USD/sq ft",
     "assumption: a moulded sloped tray insert, formed to fall to one "
     "corner, made to sit into the deck rather than on it"),
    ("kerb_usd_per_ft", 9.50, "USD/ft",
     "assumption: the upstand around the wet area that stops water tracking "
     "across the floor. A dome has no walls to stop it"),
    ("curtain_usd_each", 48.00, "USD each",
     "assumption: a curtain on a curved rail with a weighted hem"),
    ("glass_panel_usd_per_sqft", 26.00, "USD/sq ft",
     "assumption: toughened glass screen, the upgrade from curtains"),
    ("wet_barriers", 2.0, "count",
     "the owner's stated requirement: two barriers, not one. An inner one "
     "that takes the spray and an outer one that catches what gets past it"),
    ("electrical_clearance_ft", 3.0, "ft",
     "code-led: the horizontal distance a socket or panel must keep from "
     "the wet area's edge. The real rule is jurisdictional; this is the "
     "conservative one and the selftest holds the layout to it"),
    ("drain_trap_usd", 86.00, "USD",
     "assumption: the trapped gulley the tray falls to, tied into the "
     "column's own stack"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _u, _w in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    if name in CONSTANTS:
        return CONSTANTS[name]
    return seed_model.declared(name)


@dataclass(frozen=True)
class Line:
    label: str
    quantity: float
    unit: str
    unit_cost: float
    source: str

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


# ----------------------------------------------------------------------
# Panels that pull in
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PanelFixing:
    """The fixing grid, and what it is worth beyond holding a panel on."""

    bays: int
    per_bay: float
    rating_lb: float

    @property
    def inserts(self) -> float:
        return self.bays * self.per_bay

    @property
    def anchor_capacity_lb(self) -> float:
        """What three inserts together will hold -- a shelf, a bunk, a rail.

        Three because anything spanning triangles lands on at least three of
        them, and quoting the single-insert figure would flatter it.
        """
        return self.rating_lb * 3.0


def panel_fixing(geometry=None) -> PanelFixing:
    geometry = geometry or seed_model.seed_geometry()
    bays = sum(face.count for face in geometry.faces)
    return PanelFixing(int(bays), declared("inserts_per_bay"),
                       declared("anchor_rating_lb"))


def panel_lines(geometry=None) -> tuple[Line, ...]:
    """The outside-face panel and everything that holds it there."""
    geometry = geometry or seed_model.seed_geometry()
    fixing = panel_fixing(geometry)
    gasket_ft = sum(face.count * face.perimeter_in
                    for face in geometry.faces) / 12.0
    return (
        Line("outer panels on the outside face", geometry.panel_sqft, "sq ft",
             seed_model.declared("hard_panel_usd_per_sqft"),
             "hard_panel_usd_per_sqft"),
        Line("threaded inserts in the wedge faces", fixing.inserts, "each",
             declared("insert_usd_each"), "insert_usd_each"),
        Line("flange screws with bonded washers", fixing.inserts, "each",
             declared("panel_screw_usd_each"), "panel_screw_usd_each"),
        Line("panel edge gasket", gasket_ft, "ft",
             seed_model.declared("hard_panel_gasket_usd_per_ft"),
             "hard_panel_gasket_usd_per_ft"),
    )


def panel_labour_hours(geometry=None) -> float:
    """How long the inserts add to the build. Not nothing, and not hidden."""
    fixing = panel_fixing(geometry)
    return fixing.inserts * declared("insert_min_each") / 60.0


# ----------------------------------------------------------------------
# The wet area
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class WetArea:
    """The shower, as a fabricated insert rather than a curtain and a hope."""

    side_ft: float
    barriers: int
    glazed: bool
    lines: tuple[Line, ...]

    @property
    def area_sqft(self) -> float:
        return self.side_ft * self.side_ft

    @property
    def fall_in(self) -> float:
        """Total drop from the high corner to the drain."""
        return self.side_ft * math.sqrt(2.0) * declared("tray_fall_per_ft")

    @property
    def kerb_ft(self) -> float:
        """Upstand around the open sides. One side meets the dome's rim."""
        return self.side_ft * 3.0

    @property
    def cost(self) -> float:
        return sum(line.cost for line in self.lines)


def wet_area(glazed: bool = False) -> WetArea:
    """The shower insert, with curtains or with glass."""
    side = declared("shower_tray_ft")
    barriers = int(declared("wet_barriers"))
    area = side * side
    kerb = side * 3.0
    lines = [
        Line("sloped tray, moulded to fall to one corner", area, "sq ft",
             declared("tray_usd_per_sqft"), "tray_usd_per_sqft"),
        Line("kerb upstand around the open sides", kerb, "ft",
             declared("kerb_usd_per_ft"), "kerb_usd_per_ft"),
        Line("trapped gulley into the column stack", 1.0, "each",
             declared("drain_trap_usd"), "drain_trap_usd"),
    ]
    if glazed:
        # Glass takes the inner barrier; a curtain still takes the outer one,
        # because two barriers is the requirement and glass alone is one.
        screen_sqft = side * 2.0 * 6.5
        lines.append(Line("toughened glass screen, inner barrier",
                          screen_sqft, "sq ft",
                          declared("glass_panel_usd_per_sqft"),
                          "glass_panel_usd_per_sqft"))
        lines.append(Line("curtain on a curved rail, outer barrier", 1.0,
                          "each", declared("curtain_usd_each"),
                          "curtain_usd_each"))
    else:
        lines.append(Line(f"curtains on curved rail, {barriers} barriers",
                          float(barriers), "each",
                          declared("curtain_usd_each"), "curtain_usd_each"))
    return WetArea(side, barriers, glazed, tuple(lines))


def water_path() -> tuple[tuple[str, str], ...]:
    """Where a drop of water goes, in order, and what stops it going elsewhere.

    Written as a sequence because that is how it has to be checked on site:
    every step is a place water is either moving toward the drain or being
    stopped from moving sideways.
    """
    tray = wet_area()
    return (
        ("It lands on the tray",
         f"which falls {declared('tray_fall_per_ft'):.2f} in per foot to one "
         f"corner -- {tray.fall_in:.1f} in of drop from the far corner."),
        ("It cannot run sideways",
         f"because the tray is kerbed on {tray.kerb_ft / tray.side_ft:.0f} "
         "sides. A dome has no internal walls, so nothing else would stop "
         "it; the floor is round and it would find the low point and sit "
         "there."),
        ("Spray is caught twice",
         f"by {int(declared('wet_barriers'))} barriers, not one. The inner "
         "takes the spray, the outer catches what gets past it, and the gap "
         "between them drains back onto the tray."),
        ("It leaves through a trap",
         "into the column's own 2 in stack, which is already going through "
         "the floor port to the pad's drain. The shower adds no new "
         "penetration."),
        ("It never meets electricity",
         f"because the sub-panel and every socket keep "
         f"{declared('electrical_clearance_ft'):.0f} ft of horizontal "
         "clearance from the kerb, and the wet area is placed on the "
         "opposite side of the column from the outlet ring."),
    )


def separation_ok(distance_ft: float) -> bool:
    """Whether a proposed column-to-wet-area distance clears the rule."""
    return distance_ft >= declared("electrical_clearance_ft")


def column_to_wet_ft() -> float:
    """How far the wet area sits from the column, as laid out.

    The column is central and the tray is against the rim, so the distance is
    the floor radius less half the tray. If a smaller dome ever makes that
    negative, the layout is wrong and the selftest says so rather than the
    building finding out.
    """
    geometry = seed_model.seed_geometry()
    return geometry.diameter_ft / 2.0 - declared("shower_tray_ft") / 2.0


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------

def report() -> str:
    fixing = panel_fixing()
    lines = [
        "PANELS THAT PULL IN",
        f"  {fixing.bays} bays x {fixing.per_bay:.0f} inserts = "
        f"{fixing.inserts:.0f} threaded inserts",
        f"  one insert holds {fixing.rating_lb:,.0f} lb; three together "
        f"hold {fixing.anchor_capacity_lb:,.0f} lb",
        f"  adds {panel_labour_hours():.1f} h to the build",
        "",
    ]
    total = 0.0
    for line in panel_lines():
        total += line.cost
        lines.append(f"    {line.label:<44} ${line.cost:>7,.0f}")
    lines.append(f"    {'':<44} ${total:>7,.0f}")
    lines.append("")
    lines.append("THE WET AREA")
    for glazed in (False, True):
        area = wet_area(glazed)
        lines.append(f"  {'glass and curtain' if glazed else 'two curtains'}"
                     f"  {area.side_ft:.0f} x {area.side_ft:.0f} ft, "
                     f"{area.fall_in:.1f} in of fall  ${area.cost:,.0f}")
        for line in area.lines:
            lines.append(f"    {line.label:<44} ${line.cost:>7,.0f}")
    lines.append("")
    lines.append("  WHERE THE WATER GOES")
    for step, detail in water_path():
        lines.append(f"    - {step}: {detail}")
    lines.append("")
    lines.append(f"  column sits {column_to_wet_ft():.1f} ft from the tray; "
                 f"the rule is {declared('electrical_clearance_ft'):.0f} ft")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_fitout_wet() -> None:
    """Prove both before anything quotes or draws them."""
    fixing = panel_fixing()
    assert fixing.bays == 40, fixing.bays
    assert fixing.inserts == fixing.bays * declared("inserts_per_bay")
    assert fixing.anchor_capacity_lb > fixing.rating_lb

    for line in panel_lines():
        assert line.quantity > 0.0 and line.unit_cost > 0.0, line.label
        assert line.source, line.label
    assert panel_labour_hours() > 0.0

    # The whole point of moving the panel outward: it is fixed, not wedged.
    # If the screw count ever stops matching the insert count, something is
    # being held by friction again.
    lines = {line.label: line for line in panel_lines()}
    assert (lines["threaded inserts in the wedge faces"].quantity
            == lines["flange screws with bonded washers"].quantity)

    # -- the wet area --------------------------------------------------
    for glazed in (False, True):
        area = wet_area(glazed)
        assert area.lines
        assert area.cost > 0.0
        assert area.fall_in > 0.0, "a tray with no fall is a puddle"
        # Two barriers is a stated requirement, not a preference.
        kinds = [l for l in area.lines
                 if "barrier" in l.label or "barriers" in l.label]
        count = sum(l.quantity if "barriers" in l.label else 1.0
                    for l in kinds)
        assert count >= declared("wet_barriers"), (glazed, count)

    # Glass costs more than curtains, or there is no reason to offer it.
    assert wet_area(True).cost > wet_area(False).cost

    # The kerb has to run the open sides, not all four.
    area = wet_area()
    assert area.kerb_ft == area.side_ft * 3.0

    # -- and the one that is not negotiable ----------------------------
    assert separation_ok(column_to_wet_ft()), (
        f"the wet area sits {column_to_wet_ft():.1f} ft from the column, "
        f"inside the {declared('electrical_clearance_ft'):.0f} ft clearance; "
        "this layout puts a sub-panel next to a shower")
    assert not separation_ok(declared("electrical_clearance_ft") - 0.1)

    assert len(water_path()) >= 5
    for step, detail in water_path():
        assert step and detail


if __name__ == "__main__":
    validate_fitout_wet()
    print(report())
