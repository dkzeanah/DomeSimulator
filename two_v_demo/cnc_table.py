"""The 10 by 5 foot CNC plasma table, and the router that shares its frame.

The design is the Homemade Madness DIY CNC plasma build (plans in
``I:/HMM-DIY-CNC-PLASMA-PLANS``, credited by name wherever this is shown):
a box-section base with a water pan and slats, a 100 x 50 tube gantry with
5 mm plate sides, HGR20 rails on every axis, mod 1.5 rack and pinion on both
long-axis sides and the gantry, a floating head on a short ballscrew, a
pilot-arc plasma, Mach3. The plans are drawn for a 2 x 1 m sheet and say the
machine may be built "as big as you want" by two rules, both used here:

* the base frame is :data:`FRAME_OVER_SHEET_MM` longer and wider than the
  largest sheet it must cut;
* the gantry tube is :data:`GANTRY_OVER_WIDTH_MM` longer than the cut width.

Everything else -- rail and rack counts, joins, steel cut list, motor force,
steps per millimetre, the bill -- is computed from those rules and the sheet.

Prices come in three kinds and the bill keeps them apart:

``paid``      what this shop actually paid (the rack, pinion and rail kits)
``quoted``    a current retail listing, with where it was found and when
``allowance`` a declared estimate for a part not yet priced; replace it

The earlier version of this module bought NEMA 34 motors (a 14 mm shaft: the
10 mm-bore pinions do not fit it), counted long-axis rack for one side of a
gantry driven on both, bought three pinions for three motors and called one a
spare, put a torch height controller on a breakout board the guide says cannot
run one, and bought 144 metres of 100 x 50 tube for a frame the guide builds
from 50 x 50. Those are corrected here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

MM_PER_IN = 25.4

# ----------------------------------------------------------------------
# The sheet, and the guide's scaling rules
# ----------------------------------------------------------------------

#: The largest sheet the table must cut: 10 by 5 feet.
TRAVEL_X_IN = 120.0
TRAVEL_Y_IN = 60.0
SHEET_X_MM = TRAVEL_X_IN * MM_PER_IN
SHEET_Y_MM = TRAVEL_Y_IN * MM_PER_IN
#: Guide rule: the base frame is this much longer and wider than the sheet.
FRAME_OVER_SHEET_MM = 250.0
#: Guide rule: the gantry tube is this much longer than the cut width.
GANTRY_OVER_WIDTH_MM = 253.0
#: Guide: leg height before feet or wheels; slat pitch (30 slats in 2140 mm).
LEG_MM = 700.0
SLAT_PITCH_MM = 2140.0 / 30
#: Guide: racks sit 50 mm in from the leg on the home side; the far rail may be
#: 50 mm short; the Z ballscrew is cut to about 250 mm.
RACK_SET_IN_MM = 50.0
Z_SCREW_MM = 250.0
#: Our addition for a frame half again as long as the guide's: a leg pair and a
#: cross member at mid-length, so no rail span is longer than this.
MAX_UNSUPPORTED_MM = 1700.0

#: Stock as sold: rack in 500 mm lengths, rail kits of 2 x 1500 mm + 4 blocks,
#: steel tube in 12 ft sticks, flat bar in 20 ft sticks.
RACK_LENGTH_MM = 500.0
RAIL_LENGTH_MM = 1500.0
TUBE_STICK_IN = 144.0
FLAT_STICK_IN = 240.0
SAW_KERF_IN = 0.125

#: The pinion as bought: 15 teeth, module 1.5, 10 mm bore.
PINION_TEETH = 15
PINION_MODULE = 1.5
PINION_BORE_MM = 10.0
#: The motor chosen to match that bore (a NEMA 34's 14 mm shaft does not).
MOTOR_SHAFT_MM = 10.0
MOTOR_HOLD_NM = 3.0
#: Share of holding torque a stepper keeps at a plasma's working speeds:
#: an allowance from typical torque curves, not a measurement.
MOTOR_WORKING_SHARE = 0.5
#: Gantry moving mass, kg: an estimate built from the steel below plus rails,
#: carriage, Z and torch -- see :func:`gantry_mass_kg`.
STEEL_KG_PER_M3 = 7850.0
HGR20_KG_PER_M = 2.21


# ----------------------------------------------------------------------
# The machine's geometry
# ----------------------------------------------------------------------

def frame_mm() -> tuple[float, float]:
    return SHEET_X_MM + FRAME_OVER_SHEET_MM, SHEET_Y_MM + FRAME_OVER_SHEET_MM


def gantry_tube_mm() -> float:
    return SHEET_Y_MM + GANTRY_OVER_WIDTH_MM


def legs_per_side() -> int:
    length, _ = frame_mm()
    return math.ceil(length / MAX_UNSUPPORTED_MM) + 1


def rails_per_side() -> dict:
    """Rail and rack lengths per axis, and how many pieces each takes."""
    length, _ = frame_mm()
    y_len = gantry_tube_mm()
    x_rack_mm = length - 2 * RACK_SET_IN_MM
    y_rack_mm = y_len - 2 * RACK_SET_IN_MM
    return {
        "x_rail_mm": length,                              # home side flush, the far side up to 50 short
        "y_rail_mm": y_len,
        "x_rails_per_line": math.ceil(length / RAIL_LENGTH_MM),
        "y_rails_per_line": math.ceil(y_len / RAIL_LENGTH_MM),
        "x_racks": math.ceil(x_rack_mm / RACK_LENGTH_MM),  # per side
        "y_racks": math.ceil(y_rack_mm / RACK_LENGTH_MM),
        "x_rack_joins": math.ceil(x_rack_mm / RACK_LENGTH_MM) - 1,
        "x_rail_joins": math.ceil(length / RAIL_LENGTH_MM) - 1,
    }


def counts() -> dict:
    r = rails_per_side()
    x_lines, y_lines = 2, 2          # a rail each side; two rails on the gantry face (guide)
    rails = x_lines * r["x_rails_per_line"] + y_lines * r["y_rails_per_line"]
    # The Z's short rail is cut from a gantry rail's offcut.
    y_offcut = r["y_rails_per_line"] * RAIL_LENGTH_MM - r["y_rail_mm"]
    kits = math.ceil(rails / 2)
    blocks_needed = 2 * x_lines + 2 * y_lines + 2
    return {
        "x_racks": 2 * r["x_racks"], "y_racks": r["y_racks"],
        "racks": 2 * r["x_racks"] + r["y_racks"] + 1,     # one spare for a joint cut wrong
        "pinions": 3 + 1,                                 # two on X, one on Y, one spare
        "motors": 4,                                      # X, X, Y, Z
        "rails": rails, "kits": kits, "blocks": 4 * kits, "blocks_needed": blocks_needed,
        "z_from_offcut": y_offcut >= 2 * 300.0,
        "slats": int(frame_mm()[0] // SLAT_PITCH_MM) - 1,
    }


def pinion_steps_per_mm(microsteps: int = 8, motor_steps: int = 200) -> dict:
    """The number that must be right before anything is cut.

    One motor turn moves an axis the pinion's pitch circumference, pi x
    teeth x module. The guide prefers a 13-tooth pinion for torque and says to
    set whatever pinion you have in Mach3 rather than buy another.
    """
    pitch_dia_mm = PINION_TEETH * PINION_MODULE
    per_rev = math.pi * pitch_dia_mm
    return {"pitch_dia_mm": pitch_dia_mm, "mm_per_rev": per_rev,
            "steps_per_mm": motor_steps * microsteps / per_rev,
            "mm_per_step": per_rev / (motor_steps * microsteps)}


def _tube_kg_per_m(w_mm: float, h_mm: float, t_mm: float) -> float:
    area = (w_mm * h_mm - (w_mm - 2 * t_mm) * (h_mm - 2 * t_mm)) / 1e6
    return area * STEEL_KG_PER_M3


def gantry_mass_kg() -> float:
    """Estimated moving mass on the long axis: the tube, two 5 mm plate sides
    (the guide's parts, about 0.35 x 0.18 m each), the gantry's two rails,
    and a declared allowance for the carriage, Z, motors and torch."""
    tube = _tube_kg_per_m(100, 50, 3) * gantry_tube_mm() / 1000
    sides = 2 * 0.35 * 0.18 * 0.005 * STEEL_KG_PER_M3
    rails = 2 * HGR20_KG_PER_M * gantry_tube_mm() / 1000
    carriage_z_torch = 12.0        # allowance, kg
    motors = 2 * 1.4               # a 3 Nm NEMA 23 weighs about 1.4 kg
    return tube + sides + rails + carriage_z_torch + motors


def torque_check() -> dict:
    """Do two of these motors move this gantry? Force at the rack against the
    mass, at the share of torque a stepper keeps at speed."""
    pitch_r_m = PINION_TEETH * PINION_MODULE / 2 / 1000
    per_motor_n = MOTOR_HOLD_NM * MOTOR_WORKING_SHARE / pitch_r_m
    mass = gantry_mass_kg()
    return {"pitch_r_mm": pitch_r_m * 1000, "per_motor_n": per_motor_n,
            "x_force_n": 2 * per_motor_n, "gantry_kg": mass,
            "x_accel_ms2": 2 * per_motor_n / mass,
            "rpm_at_3m_min": 3000 / pinion_steps_per_mm()["mm_per_rev"]}


def gantry_deflection_mm(force_n: float = 50.0) -> float:
    """The gantry tube's sag under a force at mid-span (a router's side load),
    simply supported: F L^3 / 48 E I, 100 x 50 x 3 on its strong axis."""
    b, h, t = 0.050, 0.100, 0.003
    i = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
    L = gantry_tube_mm() / 1000
    return force_n * L ** 3 / (48 * 200e9 * i) * 1000


# ----------------------------------------------------------------------
# Steel, cut from stock
# ----------------------------------------------------------------------

def _first_fit(pieces_in: list[float], stick_in: float) -> list[list[float]]:
    sticks: list[list[float]] = []
    for p in sorted(pieces_in, reverse=True):
        for s in sticks:
            if sum(s) + len(s) * SAW_KERF_IN + p <= stick_in:
                s.append(p)
                break
        else:
            sticks.append([p])
    return sticks


def steel_cut_list() -> dict:
    """The base frame in 50 x 50 x 3 (2 x 2 x 11 ga) box, the gantry in
    100 x 50 x 3 (2 x 4 x 11 ga), the slats in 50 x 5 (2 x 3/16) flat bar."""
    length, width = frame_mm()
    L, W, leg = length / MM_PER_IN, width / MM_PER_IN, LEG_MM / MM_PER_IN
    n_legs = legs_per_side()
    frame_pieces = [L] * 4 + [W] * (n_legs) + [leg] * (2 * n_legs)
    sticks = _first_fit(frame_pieces, TUBE_STICK_IN)
    inner_w = width - 2 * 50.0
    slat_in = (inner_w - 10.0) / MM_PER_IN
    n_slats = counts()["slats"]
    slat_sticks = _first_fit([slat_in] * n_slats, FLAT_STICK_IN)
    return {
        "frame_pieces": {"long rails": (4, L), "cross members": (n_legs, W), "legs": (2 * n_legs, leg)},
        "frame_sticks": len(sticks), "frame_in": sum(frame_pieces),
        "gantry_in": gantry_tube_mm() / MM_PER_IN,
        "slats": n_slats, "slat_in": slat_in, "slat_sticks": len(slat_sticks),
        "pan_in": (length / MM_PER_IN, width / MM_PER_IN),
    }


def pan_sheets() -> int:
    """4 x 8 ft sheets laid across the pan: the 8 ft side spans the width."""
    length, width = frame_mm()
    assert width / MM_PER_IN <= 96, "a pan wider than a sheet's length needs another layout"
    return math.ceil(length / MM_PER_IN / 48)


# ----------------------------------------------------------------------
# The bill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    """One line of the machine's bill."""

    label: str
    quantity: float
    unit: str
    unit_usd: float
    basis: str = "allowance"      # paid | quoted | allowance
    note: str = ""

    @property
    def usd(self) -> float:
        return self.quantity * self.unit_usd


#: Where each quoted price came from, looked up 2026-10-03. Retail moves; these
#: are a reference point, not a promise.
SOURCES = {
    "motor": "STEPPERONLINE 23HS45-4204S, Nema 23 3 Nm 4.2 A, 10 mm shaft: RobotShop US $48.39",
    "driver": "STEPPERONLINE DM556T digital stepper driver: $33.08",
    "psu": "48 V 10.4 A power adapter for CNC: Sienci Labs $46.99",
    "mach3": "Mach3 licence (Newfangled Solutions), via Maker Store: $218.73",
    "plasma": "PrimeWeld CUT60, blowback pilot arc with CNC port: $699.00 (Weldmonger)",
    "tube2x2": "2 x 2 x 11 ga square tube, 12 ft: $51.98 (Steel Supply LP)",
}


@lru_cache(maxsize=1)
def bill() -> tuple[Line, ...]:
    """Every part of the plasma table."""
    c = counts()
    s = steel_cut_list()
    return (
        # -- bought already, at the prices paid ---------------------------
        Line("Gear rack, mod 1.5, 15 x 15 x 500 mm", c["racks"], "lengths", 29.39, "paid",
             f"{c['x_racks'] // 2} each side of the long axis, {c['y_racks']} on the gantry, 1 spare"),
        Line("Pinion, mod 1.5, 15 T, 10 mm bore", c["pinions"], "gears", 12.23, "paid",
             "two on the long axis, one on the gantry, one spare"),
        Line("HGR20 rail kit, 2 x 1500 mm + 4 HGH20CA blocks", c["kits"], "kits", 109.99, "paid",
             f"{c['rails']} rails joined end to end; the Z rail is a gantry offcut"),
        # -- the drive and the control, quoted ----------------------------
        Line("Stepper, NEMA 23, 3 Nm, 10 mm shaft", c["motors"], "motors", 48.39, "quoted",
             "its shaft fits the pinion's bore with no sleeve"),
        Line("Stepper driver, DM556T", c["motors"], "drivers", 33.08, "quoted"),
        Line("Power supply, 48 V 10 A", 1, "supply", 46.99, "quoted"),
        Line("Mach3 licence", 1, "licence", 218.73, "quoted", "the guide's control software"),
        Line("Plasma cutter, 60 A pilot arc, CNC port", 1, "unit", 699.00, "quoted",
             "pilot arc, as the guide advises: high-frequency start puts noise in the wiring"),
        Line("Square tube, 2 x 2 x 11 ga, 12 ft", s["frame_sticks"], "sticks", 51.98, "quoted",
             "the base frame, cut list from the guide's rules"),
        # -- allowances: estimates until priced ---------------------------
        Line("Breakout board (the guide's red board) + relay for the torch", 1, "set", 45.0),
        Line("Ballscrew SFU1605, 300 mm, with nut and end supports", 1, "set", 40.0,
             note=f"cut to about {Z_SCREW_MM:.0f} mm for the floating head"),
        Line("Rect. tube, 2 x 4 x 11 ga, gantry", math.ceil(s["gantry_in"] / 12), "ft", 9.0,
             note="yard price for a full length; cut pieces cost far more"),
        Line("Plate, 3/16 in (5 mm), gantry sides and carriage", 1, "2 x 4 ft piece", 110.0,
             note="the guide's cut list; cut by hand from its paper templates"),
        Line("Flat bar, 2 x 3/16 in, 20 ft, slats", s["slat_sticks"], "sticks", 38.0),
        Line("Sheet, 16 ga, 4 x 8 ft, water pan bottom", pan_sheets(), "sheets", 80.0,
             note="laid across the frame, welded edge to edge"),
        Line("Drag chain, cable, e-stop, connectors", 1, "lot", 160.0),
        Line("Floating-head switch, Z coupler, mounts, bolts, paint", 1, "lot", 120.0),
    )


@lru_cache(maxsize=1)
def total() -> float:
    return sum(line.usd for line in bill())


def subtotal(basis: str) -> float:
    return sum(line.usd for line in bill() if line.basis == basis)


def router_variant() -> list[Line]:
    """The same frame, rails, racks, motors and control with a router head:
    for cutting panel jigs, templates and wooden panels. A router needs a
    rigid Z rather than a floating head, a spindle, a flat bed and dust
    extraction -- and the plasma's water pan and slats lift out for it."""
    return [
        Line("Spindle, 2.2 kW water-cooled, with VFD and pump", 1, "set", 260.0),
        Line("Z axis, ballscrew, 200 mm travel, rigid plate", 1, "set", 180.0),
        Line("Bed: support grid + MDF spoilboard", 1, "lot", 220.0,
             note="sits on the frame where the slats were; skimmed flat by the machine"),
        Line("Dust shoe and extraction hose", 1, "set", 90.0),
        Line("Collets, end mills, v-bits", 1, "set", 180.0),
        Line("Fifth driver and wiring for the spindle's control", 1, "lot", 60.0),
    ]


def router_total() -> float:
    return sum(line.usd for line in router_variant())


def bill_table() -> str:
    rows = ["part                                                qty      each      total   basis"]
    for line in bill():
        rows.append(f"{line.label[:50]:<50} {line.quantity:>5g} {line.unit_usd:>9,.2f} {line.usd:>10,.2f}   {line.basis}")
    rows.append(f"{'':<50} {'':>5} {'':>9} {'-' * 10}")
    rows.append(f"{'the plasma table':<50} {'':>5} {'':>9} {total():>10,.2f}")
    return "\n".join(rows)


def validate_cnc_table() -> None:
    """Checks that keep the machine's arithmetic honest."""
    assert MOTOR_SHAFT_MM == PINION_BORE_MM, "the pinion must fit the motor"
    per = pinion_steps_per_mm()
    assert per["pitch_dia_mm"] == 22.5 and 70.6 < per["mm_per_rev"] < 70.7
    c = counts()
    r = rails_per_side()
    assert c["x_racks"] == 2 * r["x_racks"], "racks on both long sides"
    assert c["x_racks"] * RACK_LENGTH_MM / 2 >= frame_mm()[0] - 2 * RACK_SET_IN_MM
    assert c["pinions"] == 4 and c["motors"] == 4
    assert c["blocks"] >= c["blocks_needed"] and c["z_from_offcut"]
    assert r["x_rails_per_line"] * RAIL_LENGTH_MM >= frame_mm()[0]
    tc = torque_check()
    assert tc["x_accel_ms2"] > 1.0, "the long axis can accelerate a plasma gantry"
    assert gantry_deflection_mm() < 0.1
    assert all(line.basis in ("paid", "quoted", "allowance") for line in bill())
    assert abs(total() - sum(subtotal(b) for b in ("paid", "quoted", "allowance"))) < 1e-6
