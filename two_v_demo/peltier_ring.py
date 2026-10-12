"""Ten Peltier modules round the rim, running all day and all night: what they do and what they cost to feed.

The owner bought one TEC1-12706 for $20 and proposes ten, one at each of the
dome's rim ports, running 24/7. The question has three parts:

* **what one module really does** -- not the 70 W on the listing, which is the
  most heat it can move with *no* temperature difference across it, but what it
  moves when its cold face is held under the room's dew point and its hot face is
  dumping into a real heat sink (:func:`operating_point`);
* **what ten of them do for the room** in a day: heat taken out, water taken out,
  against what two people and the ventilation air put in (:func:`ring_day`,
  :func:`loads`);
* **what it takes to run them round the clock on the sun**: array, bank, and
  their price, against the $200 of modules (:func:`power_plan`).

The module is modelled the standard way, from its own listed maxima: Seebeck
voltage, Joule heat and conduction back through the legs
(:func:`module_parameters`). Every figure that is not physics or the listing is
declared in :data:`CONSTANTS` with its kind and reason, and the borrowed solar
and battery rates come from :mod:`seed_model` and :mod:`park_model` by name, so
this module states no price the rest of the repository does not.

    py -3.12 -m two_v_demo.peltier_ring
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import seam_climate as sc
from . import seam_vent as sv

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

K0 = 273.15
H_FG = 2.45e6          # J/kg, latent heat of condensation near 20 C
CP_AIR = 1005.0        # J/kg K
M3S_PER_CFM = 0.000471947

# name, value, unit, kind, why
CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    # -- the module, from the owner's listing ----------------------------
    ("v_max", 15.0, "V", "listing", "TEC1-12706: rated 12 V, 15 V maximum"),
    ("dt_max", 67.0, "K", "listing", "the largest temperature difference it can hold, at no load"),
    ("r_module", 2.25, "ohm", "listing", "internal resistance 2.1-2.4 ohm: the middle"),
    ("q_max_listed", 70.0, "W", "listing",
     "the cooling power on the listing; checked here, never used"),
    ("i_listed", 4.3, "A", "listing", "working current at 12 V, 4-4.6 A: the middle"),
    ("th_rating_c", 27.0, "C", "assumption",
     "hot-face temperature the maxima are rated at; makers use 25 to 50 C, and the low end "
     "gives the module the benefit of the doubt"),
    ("module_usd", 20.0, "USD", "owner", "what the owner paid for one"),
    ("modules", 10.0, "-", "owner", "one at each of the dome's ten rim ports"),
    # -- what it is mounted on -------------------------------------------
    ("r_hot_sink", 0.20, "K/W", "assumption",
     "hot face to outside air: a finned aluminium sink with its fan, the kind sold with "
     "the module. A bare plate is several times worse"),
    ("r_cold_sink", 0.40, "K/W", "assumption",
     "cold face to room air: a smaller finned plate with a slow fan, wet with condensate"),
    ("fan_w", 2.4, "W", "nominal", "one 12 V 80 mm fan at 0.2 A; two per module, one each face"),
    ("converter_eff", 0.92, "-", "assumption",
     "a buck converter from the 24 V bank to each module's 12 V"),
    ("battery_round_trip", 0.95, "-", "nominal", "LiFePO4, energy in to energy out"),
    ("battery_dod", 0.90, "-", "assumption", "the share of a LiFePO4 bank used each night"),
    ("solar_window_h", 8.0, "h", "assumption",
     "hours a day the array is making more than the load; the other hours run on the bank"),
    ("autonomy_days", 1.0, "days", "assumption",
     "one sunless day the bank must cover on top of the night, for 24/7 to mean 24/7"),
    ("panel_w", 400.0, "W", "nominal", "one ordinary residential panel, about 1.0 x 1.9 m"),
    ("rack_kwh", 5.12, "kWh", "nominal", "one 48 V server-rack LiFePO4 battery"),
    # -- the room and the weather ----------------------------------------
    ("people", 2.0, "-", "assumption", "the household the cabin is sized for"),
    ("person_sensible_w", 75.0, "W", "standard", "ASHRAE: a person at rest, sensible heat"),
    ("person_latent_w", 45.0, "W", "standard",
     "ASHRAE: a person lightly active, latent heat (their breath and skin)"),
    ("household_extra_l_day", 3.0, "L/day", "estimate",
     "cooking, washing and a shower for two, beyond their breath; published household "
     "totals for two run about 5 to 8 litres a day all in"),
    # -- what it is compared with ----------------------------------------
    ("dehumidifier_l_per_kwh", 1.8, "L/kWh", "estimate",
     "a small compressor dehumidifier at the US Energy Star floor for its class"),
    ("window_ac_btu_h", 5000.0, "BTU/h", "nominal", "the smallest window air conditioner sold"),
    ("window_ac_ceer", 11.0, "BTU/Wh", "estimate", "its efficiency, about the US minimum"),
    # -- what the book and two films assumed before this model -------------
    ("old_modules", 6.0, "-", "superseded",
     "wedge_book.systems until 2026-10-04: six modules at the wettest seams"),
    ("old_watts_each", 60.0, "W", "superseded", "the draw it assumed per module"),
    ("old_litres_per_kwh", 0.35, "L/kWh", "superseded",
     "the yield it assumed; quoted by The Seam Does Four Jobs and The Wedge Dome Explained"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}

#: (key, label, room C, room RH, outside C, outside RH)
WEATHERS = (
    ("humid", "humid summer day", 26.0, 0.60, 30.0, 0.60),
    ("muggy", "muggy night", 24.0, 0.65, 24.0, 0.85),
    ("shoulder", "wet spring day", 21.0, 0.65, 16.0, 0.85),
)

VOLTS = (3.0, 6.0, 9.0, 12.0)


def _borrowed(name: str) -> float:
    """A solar or battery rate the rest of the repository already declares."""
    import park_model
    import seed_model

    try:
        return seed_model.declared(name)
    except KeyError:
        return park_model.declared(name)


BORROWED = ("solar_usd_per_watt_diy", "battery_usd_per_kwh", "solar_derate", "sun_hours_per_day")


# ----------------------------------------------------------------------
# One module
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Module:
    alpha: float        # V/K, Seebeck coefficient of the whole module
    r: float            # ohm
    k: float            # W/K, conduction back through the legs
    i_max: float
    q_max: float        # the true no-difference maximum


@lru_cache(maxsize=1)
def module_parameters() -> Module:
    """The module's three constants from its own maxima (the standard reduction:
    V_max = alpha Th, dT_max = Z Tc^2 / 2, I_max = alpha Tc / R)."""
    th = C["th_rating_c"] + K0
    alpha = C["v_max"] / th
    r = C["r_module"]
    tc = th - C["dt_max"]
    k = alpha * alpha * tc * tc / (2 * r * C["dt_max"])
    i_max = alpha * tc / r
    i_q = alpha * th / r                              # the current that maximises Qc at dT = 0
    q_max = alpha * th * i_q - 0.5 * i_q * i_q * r
    return Module(alpha, r, k, i_max, q_max)


@dataclass(frozen=True)
class Point:
    volts: float
    amps: float
    t_cold: float       # C, the cold face
    t_hot: float        # C, the hot face
    q_cold: float       # W taken from the room
    q_hot: float        # W thrown outside
    p_module: float     # W, the module alone
    p_station: float    # W from the bank: module through its converter, plus two fans
    water_l_day: float  # litres a day condensed on this module's cold plate
    latent_share: float

    @property
    def cop(self) -> float:
        return self.q_cold / self.p_module if self.p_module else 0.0


def operating_point(volts: float, t_room: float, rh_room: float, t_out: float) -> Point:
    """Steady state with real sinks on both faces: cold face fed by room air,
    hot face dumping outside. Solved by damped fixed-point iteration."""
    m = module_parameters()
    tc, th = t_room - 5.0, t_out + 5.0
    for _ in range(400):
        tck, thk = tc + K0, th + K0
        i = max(0.0, (volts - m.alpha * (thk - tck)) / m.r)
        qc = m.alpha * tck * i - 0.5 * i * i * m.r - m.k * (thk - tck)
        qh = m.alpha * thk * i + 0.5 * i * i * m.r - m.k * (thk - tck)
        tc_new = t_room - C["r_cold_sink"] * qc
        th_new = t_out + C["r_hot_sink"] * qh
        tc += 0.2 * (tc_new - tc)
        th += 0.2 * (th_new - th)
    p = volts * i
    # What the cooled air gives up: sensible to the plate's temperature, latent
    # down to the plate's saturation. The ratio does not depend on the fan.
    w_room = sc.humidity_ratio(t_room, rh_room) / 1000.0
    w_plate = sc.humidity_ratio(tc, 1.0) / 1000.0
    latent = H_FG * max(0.0, w_room - w_plate)
    sensible = CP_AIR * max(0.0, t_room - tc)
    share = latent / (latent + sensible) if latent + sensible > 0 else 0.0
    water = max(0.0, qc) * share / H_FG * 86400.0
    station = p / C["converter_eff"] + 2 * C["fan_w"]
    return Point(volts, i, tc, th, qc, qh, p, station, water, share)


def weather(key: str) -> tuple:
    return next(w for w in WEATHERS if w[0] == key)


def point_in(key: str, volts: float = 12.0) -> Point:
    _k, _l, t_room, rh_room, t_out, _rho = weather(key)
    return operating_point(volts, t_room, rh_room, t_out)


def listing_check() -> dict:
    """The listing's 70 W and 4-4.6 A against the module's own physics."""
    m = module_parameters()
    zero = operating_point(12.0, 27.0, 0.0, 27.0)
    return {"q_max_true": m.q_max, "q_max_listed": C["q_max_listed"],
            "i_at_12v_ideal": 12.0 / m.r, "i_at_12v_mounted": point_in("humid").amps,
            "i_listed": C["i_listed"], "alpha": m.alpha, "k": m.k, "i_max": m.i_max,
            "no_lift_q_12v": zero.q_cold}


# ----------------------------------------------------------------------
# Ten of them, a whole day
# ----------------------------------------------------------------------

def ring_day(key: str = "humid", volts: float = 12.0) -> dict:
    p = point_in(key, volts)
    n = C["modules"]
    return {
        "point": p,
        "cooling_w": n * p.q_cold,
        "cooling_kwh": n * p.q_cold * 24 / 1000,
        "outside_w": n * p.q_hot,
        "draw_w": n * p.p_station,
        "draw_kwh": n * p.p_station * 24 / 1000,
        "water_l_day": n * p.water_l_day,
        "litres_per_kwh": (n * p.water_l_day) / (n * p.p_station * 24 / 1000),
        "if_hot_side_inside_w": n * p.p_station,      # every watt drawn ends up as heat
    }


def voltage_table(key: str = "humid") -> list[dict]:
    return [ring_day(key, v) for v in VOLTS]


def loads(key: str = "humid") -> dict:
    """What the room takes on in a day that the plates would be working against.
    The sun on the shell is left out: it is the largest load and would make the
    plates look smaller still."""
    _k, _l, t_room, rh_room, t_out, rh_out = weather(key)
    people = C["people"]
    vent_kg_s = sv.need_cfm() * M3S_PER_CFM * sc.C["air_density"]
    w_in = sc.humidity_ratio(t_room, rh_room) / 1000.0
    w_out = sc.humidity_ratio(t_out, rh_out) / 1000.0
    water = (people * C["person_latent_w"] / H_FG * 86400 + C["household_extra_l_day"]
             + max(0.0, w_out - w_in) * vent_kg_s * 86400)
    heat = (people * C["person_sensible_w"]
            + max(0.0, t_out - t_room) * CP_AIR * vent_kg_s)
    return {"water_l_day": water, "heat_w": heat, "vent_water_l_day": max(0.0, w_out - w_in) * vent_kg_s * 86400,
            "people_water_l_day": people * C["person_latent_w"] / H_FG * 86400}


def compared(key: str = "humid") -> dict:
    """The same day's water and cooling from ordinary appliances."""
    ring = ring_day(key)
    dehum_kwh = ring["water_l_day"] / C["dehumidifier_l_per_kwh"]
    ac_cool_w = C["window_ac_btu_h"] / 3.412
    ac_draw_w = C["window_ac_btu_h"] / C["window_ac_ceer"]
    return {"dehumidifier_kwh": dehum_kwh, "ratio_vs_dehumidifier": ring["draw_kwh"] / dehum_kwh,
            "ac_cool_w": ac_cool_w, "ac_draw_w": ac_draw_w, "ac_cop": ac_cool_w / ac_draw_w,
            "ring_cop": ring["cooling_w"] / ring["draw_w"]}


# ----------------------------------------------------------------------
# Feeding it round the clock
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PowerPlan:
    load_w: float
    day_kwh: float
    night_kwh: float
    array_w: float
    bank_usable_kwh: float
    bank_nameplate_kwh: float
    array_usd: float
    bank_usd: float
    modules_usd: float
    one_night_bank_kwh: float

    @property
    def total_usd(self) -> float:
        return self.array_usd + self.bank_usd + self.modules_usd

    @property
    def panels(self) -> int:
        return math.ceil(self.array_w / C["panel_w"])

    @property
    def racks(self) -> int:
        return math.ceil(self.bank_nameplate_kwh / C["rack_kwh"])


def power_plan(key: str = "humid", volts: float = 12.0) -> PowerPlan:
    ring = ring_day(key, volts)
    load = ring["draw_w"]
    day_kwh = ring["draw_kwh"]
    night_h = 24.0 - C["solar_window_h"]
    night_kwh = load * night_h / 1000
    # the array makes the day's direct use plus what goes through the bank
    through_bank = night_kwh / C["battery_round_trip"]
    made = load * C["solar_window_h"] / 1000 + through_bank
    array_w = made / (_borrowed("sun_hours_per_day") * _borrowed("solar_derate")) * 1000
    one_night = night_kwh / C["battery_dod"]
    usable = night_kwh + C["autonomy_days"] * day_kwh
    nameplate = usable / C["battery_dod"]
    return PowerPlan(load, day_kwh, night_kwh, array_w, usable, nameplate,
                     array_w * _borrowed("solar_usd_per_watt_diy"),
                     nameplate * _borrowed("battery_usd_per_kwh"),
                     C["modules"] * C["module_usd"], one_night)


# ----------------------------------------------------------------------
# Text for the book and the films
# ----------------------------------------------------------------------

def constants_table() -> str:
    width = max(len(n) for n, *_ in CONSTANTS)
    rows = [f"{n:<{width}}  {v:>8g} {u:<5} {k:<10} {w}" for n, v, u, k, w in CONSTANTS]
    rows += [f"{n:<{width}}  {_borrowed(n):>8g} {'':<5} {'borrowed':<10} declared in seed_model / park_model"
             for n in BORROWED]
    return "\n".join(rows)


def voltage_text(key: str = "humid") -> str:
    rows = ["volts  amps  cold face  cooling  drawn   COP   water   ten modules",
            "              C        W each   W each        L/day   kWh/day  L/day"]
    for r in voltage_table(key):
        p = r["point"]
        rows.append(f"{p.volts:>5.0f} {p.amps:>5.2f} {p.t_cold:>9.1f} {p.q_cold:>8.1f} {p.p_station:>7.1f}"
                    f" {p.cop:>5.2f} {p.water_l_day:>7.2f} {r['draw_kwh']:>8.1f} {r['water_l_day']:>6.1f}")
    return "\n".join(rows)


def weather_text() -> str:
    rows = ["weather            room        outside   cold face  cooling  water   load: water  heat",
            "                   C   RH       C           C        W        L/day     L/day     W"]
    for key, label, t_in, rh, t_out, _ in WEATHERS:
        r, ld = ring_day(key), loads(key)
        rows.append(f"{label:<17} {t_in:>3.0f} {100 * rh:>3.0f}% {t_out:>7.0f} {r['point'].t_cold:>11.1f}"
                    f" {r['cooling_w']:>8.0f} {r['water_l_day']:>7.1f} {ld['water_l_day']:>10.1f}"
                    f" {ld['heat_w']:>7.0f}")
    return "\n".join(rows)


def plan_text(key: str = "humid") -> str:
    p = power_plan(key)
    return "\n".join([
        f"load, ten stations          {p.load_w:>8,.0f} W, all day and all night",
        f"energy a day                {p.day_kwh:>8,.1f} kWh",
        f"of it at night, off the bank{p.night_kwh:>8,.1f} kWh",
        f"array                       {p.array_w:>8,.0f} W   ${p.array_usd:,.0f}"
        f"   ({p.panels} panels of {C['panel_w']:.0f} W)",
        f"bank, a night + a dark day  {p.bank_nameplate_kwh:>8,.1f} kWh ${p.bank_usd:,.0f}"
        f"   ({p.racks} racks of {C['rack_kwh']:g} kWh)",
        f"ten modules                 {'':>8}     ${p.modules_usd:,.0f}",
        f"total                       {'':>8}     ${p.total_usd:,.0f}",
    ])


def facts() -> dict:
    """Everything the book and the films quote, from one place."""
    lc = listing_check()
    hum, mug, spr = ring_day("humid"), ring_day("muggy"), ring_day("shoulder")
    vt = {int(r["point"].volts): r for r in voltage_table("humid")}
    best = max(voltage_table("humid"), key=lambda r: r["litres_per_kwh"])
    plan = power_plan("humid")
    plan6 = power_plan("humid", 6.0)
    ld = loads("humid")
    cmp = compared("humid")
    from wedge_book import systems
    hours = systems.declared("peltier_run_hours")
    old_kwh = C["old_modules"] * C["old_watts_each"] * hours / 1000
    water = systems.water_comparison()
    daylight = {"hours": hours, "kwh": water["peltier_kwh_per_day"], "litres": water["peltier_litres_per_day"],
                "kwh_per_litre": water["kwh_per_litre"],
                "old_kwh": old_kwh, "old_litres": old_kwh * C["old_litres_per_kwh"],
                "old_kwh_per_litre": 1 / C["old_litres_per_kwh"]}
    return {"daylight": daylight, "listing": lc, "humid": hum, "muggy": mug, "spring": spr, "volts": vt, "best": best,
            "plan": plan, "plan6": plan6, "loads": ld, "compared": cmp,
            "old_l_per_kwh": C["old_litres_per_kwh"]}


def validate_peltier_ring() -> None:
    m = module_parameters()
    lc = listing_check()
    # the module's physics recovers its own listed maximum difference
    assert abs(m.alpha * m.alpha / (m.r * m.k) * (C["th_rating_c"] + K0 - C["dt_max"]) ** 2 / 2
               - C["dt_max"]) < 1e-6
    assert lc["q_max_true"] < C["q_max_listed"], "the listing's 70 W is above the physics"
    # mounted current sits near the listing's 4-4.6 A
    assert 3.8 < lc["i_at_12v_mounted"] < 5.2, lc["i_at_12v_mounted"]
    hum = ring_day("humid")
    p = hum["point"]
    # energy balance: heat out the hot side = heat in the cold side + electricity
    assert abs(p.q_hot - (p.q_cold + p.p_module)) < 0.5
    assert p.t_cold > sc.C["frost_floor_c"], "12 V does not frost the plate in humid summer"
    dp = sc.dew_point(26.0, 0.60)
    assert p.t_cold < dp, "the plate is under the room's dew point"
    assert p.t_cold > sc.plate_setpoint(dp), "the book says full drive cannot reach the setpoint"
    assert voltage_table("humid")[1]["water_l_day"] == 0, "the book says 6 V stops condensing"
    best = max(voltage_table("humid"), key=lambda r: r["litres_per_kwh"])
    assert best["point"].volts == 9.0, "the book caps the drive at the best-yield voltage"
    # lower voltage: less cooling, better efficiency (the reason to throttle)
    rows = voltage_table("humid")
    assert [r["cooling_w"] for r in rows] == sorted(r["cooling_w"] for r in rows)
    assert rows[0]["point"].cop > rows[-1]["point"].cop
    # the comparison the chapter exists to state
    assert compared()["ratio_vs_dehumidifier"] > 2
    assert power_plan().total_usd > 10 * C["modules"] * C["module_usd"]


if __name__ == "__main__":
    validate_peltier_ring()
    f = facts()
    print(f["listing"])
    print(voltage_text())
    print(weather_text())
    print(plan_text())
    print("6 V plan:", f["plan6"])
    print("loads", f["loads"])
    print("compared", f["compared"])
    print("old systems L/kWh", f["old_l_per_kwh"], "modelled at 12 V", f["humid"]["litres_per_kwh"],
          "best", f["best"]["point"].volts, f["best"]["litres_per_kwh"])
