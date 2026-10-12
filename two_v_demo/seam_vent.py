"""The cap that breathes downward: ventilating a watertight dome through its seams.

The dome's skin is one watertight "shower cap" (wedge book, "One Watertight
Layer, and Only One"). A cap with no hole in it keeps every drop of weather
out, and it also keeps every breath of the room in: the people inside put
water into the air by breathing, cooking and washing, and with nowhere to go
that water condenses on the coldest surface it finds, which is the frame.

The design, as the owner set it out: take the room's air in at the **top**,
inside the shell, where the warmest, wettest, stalest air gathers; send it
**down** the seam channels, inside their printed keys; and let it out at the
**bottom** of the dome, through ports that **face the ground** under the cap's
brim. Fresh air comes in at the bottom too, through its own downward-facing
ports, and into the room low. Nothing pierces the cap anywhere above its rim.

This module computes what that design does, from the solver's own seams:

* which seams run downhill all the way from the apex to the rim, and that the
  dead-level pentagon ring is not one of them (:func:`descending_seams`);
* the air the dome needs, and the seams' room to carry it (:func:`capacity`);
* the **cold siphon**: in winter the exhaust cools as it falls through the
  channel, becomes heavier than the room's air, and pulls itself down -- how
  much of the need it carries on its own in each weather, and the fan
  pressure for the rest (:func:`weather_table`);
* the **water**: when the channel is colder than the room air's dew point the
  exhaust drops liquid inside the key, and that water runs the same way the
  air goes -- down -- and leaves by the same door (:func:`condensate`);
* where it stops working: an outlet below freezing ices up
  (:func:`freeze_limit`).

Every input that is not geometry is declared in :data:`CONSTANTS` with its
kind and reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import channel_facts as cf
from . import seam_climate as sc

M_PER_IN = 0.0254
M3S_PER_CFM = 0.000471947

# name, value, unit, kind, why
CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    ("channel_share", 0.5, "-", "assumption",
     "where the channel's air temperature sits between outside (0) and inside (1): the key "
     "lies inside the frame, about halfway through the wall's resistance to heat"),
    ("summer_channel_c", 35.0, "C", "assumption",
     "channel air on a sunny summer afternoon, the cap above it warmed by the sun"),
    ("room_rh", 0.45, "-", "assumption", "the room's relative humidity in winter"),
    ("f_re", 64.0, "-", "standard",
     "laminar friction, f x Re, for a round duct; a triangle's is lower (53), so 64 overstates "
     "the channel's resistance"),
    ("k_junction", 1.5, "-", "estimate",
     "loss at each vertex rosette where the air turns from one seam into the next"),
    ("k_entry_exit", 1.5, "-", "estimate", "entry at the crown grille plus exit at the outlet"),
    ("paths", 5.0, "-", "geometry",
     "the five cap seams leave the apex: all exhaust passes through them, so five parallel "
     "paths, each treated as one channel carrying a fifth of the flow the whole way (a "
     "conservative simplification: lower down the flow divides among more seams)"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}

#: The weathers the design is checked against: (label, outside C, channel C or None).
WEATHERS = (
    ("hard winter", -15.0, None),
    ("winter", -5.0, None),
    ("cool", 5.0, None),
    ("mild", 15.0, None),
    ("summer sun", 30.0, C["summer_channel_c"]),
)


# ----------------------------------------------------------------------
# Which seams run downhill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Route:
    seams_down: int          # seams that fall all the way to the rim from the apex
    level_seams: int         # dead-level seams, kept out of the exhaust
    path_ft: float           # the shortest falling path, apex to rim
    junctions: int           # rosettes on that path between apex and rim
    rim_outlets: int
    cap_penetrations: int    # holes through the cap above the rim: none


def descending_seams() -> Route:
    """Seams that can carry exhaust from the apex to the rim without ever
    climbing: a seam qualifies if it lies on some strictly-falling path."""
    model = cf.reference_model()
    topo = model.topology
    z = [float(v[2]) for v in topo.vertices]
    verts = [np.asarray(v, dtype=float) for v in topo.vertices]
    top = max(range(len(z)), key=lambda i: z[i])
    rim = {i for i, h in enumerate(z) if abs(h) < 1e-6}
    down: dict[int, list[tuple[int, float]]] = {}
    level = 0
    for s in model.seams:
        a, b = s.edge_key
        if abs(z[a] - z[b]) < 1e-6:
            level += 1
            continue
        hi, lo = (a, b) if z[a] > z[b] else (b, a)
        down.setdefault(hi, []).append((lo, float(np.linalg.norm(verts[a] - verts[b]))))
    # Every seam reachable from the apex going only downhill.
    reach, stack, used = {top}, [top], set()
    while stack:
        v = stack.pop()
        for u, _w in down.get(v, ()):
            used.add((v, u))
            if u not in reach:
                reach.add(u)
                stack.append(u)
    # shortest falling path to the rim, and its junction count
    best = {top: (0.0, 0)}
    for v in sorted(reach, key=lambda i: -z[i]):
        if v not in best:
            continue
        d, n = best[v]
        for u, w in down.get(v, ()):
            cand = (d + w, n + 1)
            if u not in best or cand[0] < best[u][0]:
                best[u] = cand
    path = min(best[i] for i in rim if i in best)
    return Route(len(used), level, path[0] / 12.0, path[1] - 1, len(rim), 0)


# ----------------------------------------------------------------------
# The air
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def channel() -> dict:
    """The empty channel inside the tighter seam's key: its area and its
    hydraulic diameter (4 A / P). Exhaust seams carry no services."""
    t = min(cf.seam_types(), key=lambda s: cf.room(s).inside_in2)
    inner = cf.inset(cf.v_polygon(t, 0.0, t.nose_in), cf.K["key_wall_in"])
    area_in2 = cf.area(inner)
    perim_in = cf.perimeter(inner)
    return {"area_m2": area_in2 * M_PER_IN ** 2, "dh_m": 4 * area_in2 / perim_in * M_PER_IN,
            "area_in2": area_in2}


def need_cfm() -> float:
    return cf.air()["need_cfm"]


def capacity() -> dict:
    """What the falling seams can carry at a quiet speed, against the need."""
    r = descending_seams()
    ch = channel()
    per = ch["area_in2"] / 144.0 * cf.K["quiet_air_fpm"]
    return {"per_seam_cfm": per, "cap_seams_cfm": per * C["paths"], "need_cfm": need_cfm(),
            "headroom": per * C["paths"] / need_cfm(), "route": r}


def _drop_pa(q_m3s_per_path: float, path_m: float, junctions: int) -> float:
    """Pressure to push q down one path: laminar friction plus fittings."""
    ch = channel()
    rho, mu = sc.C["air_density"], sc.C["air_viscosity"]
    v = q_m3s_per_path / ch["area_m2"]
    friction = C["f_re"] / 2 * mu * path_m * v / ch["dh_m"] ** 2
    fittings = (C["k_junction"] * junctions + C["k_entry_exit"]) * rho * v * v / 2
    return friction + fittings


def drive_pa(t_out_c: float, t_channel_c: float | None = None) -> float:
    """The cold siphon: the room's warm column against the channel's cooler
    one, over the dome's height. Positive pulls the exhaust down."""
    t_in = sc.C["indoor_t_c"]
    t_ch = t_channel_c if t_channel_c is not None else t_out_c + C["channel_share"] * (t_in - t_out_c)
    h = sc.rings()["apex_height_ft"] * 0.3048
    return sc.C["air_density"] * sc.C["gravity"] * h * (t_in - t_ch) / (t_in + 273.15)


def natural_cfm(drive: float) -> float:
    """Flow the siphon alone sustains, all five paths together."""
    if drive <= 0:
        return 0.0
    r = descending_seams()
    path_m, n = r.path_ft * 0.3048, r.junctions
    lo, hi = 0.0, 1.0
    while _drop_pa(hi, path_m, n) < drive:
        hi *= 2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _drop_pa(mid, path_m, n) < drive else (lo, mid)
    return lo * C["paths"] / M3S_PER_CFM


def fan_pa_for_need(drive: float) -> float:
    """Fan pressure to move the full need, after the siphon's help (or against it)."""
    r = descending_seams()
    q = need_cfm() * M3S_PER_CFM / C["paths"]
    return max(0.0, _drop_pa(q, r.path_ft * 0.3048, r.junctions) - drive)


def condensate(t_out_c: float, t_channel_c: float | None = None) -> dict:
    """Water the exhaust drops inside the keys, litres a day, at the full need."""
    t_in = sc.C["indoor_t_c"]
    t_ch = t_channel_c if t_channel_c is not None else t_out_c + C["channel_share"] * (t_in - t_out_c)
    w_in = sc.humidity_ratio(t_in, C["room_rh"]) / 1000.0        # g/kg -> kg/kg
    w_ch = sc.humidity_ratio(t_ch, 1.0) / 1000.0
    kg_s = need_cfm() * M3S_PER_CFM * sc.C["air_density"]
    per_day = max(0.0, w_in - w_ch) * kg_s * 86400
    return {"channel_c": t_ch, "dew_point_c": sc.dew_point(t_in, C["room_rh"]), "litres_day": per_day}


def freeze_limit() -> float:
    """The outside temperature at which the channel, and so the outlet, reaches 0 C."""
    t_in, s = sc.C["indoor_t_c"], C["channel_share"]
    return -s * t_in / (1 - s)


def weather_table() -> list[dict]:
    rows = []
    for label, t_out, t_ch in WEATHERS:
        d = drive_pa(t_out, t_ch)
        nat = natural_cfm(d)
        rows.append({"weather": label, "t_out": t_out, "drive_pa": d, "natural_cfm": nat,
                     "share": min(1.0, nat / need_cfm()), "fan_pa": fan_pa_for_need(d),
                     **condensate(t_out, t_ch)})
    return rows


def table_text() -> str:
    rows = ["weather       outside   siphon    carries    fan for the rest   water in the keys",
            "                  C       Pa     of the need          Pa            litres/day"]
    for r in weather_table():
        rows.append(f"{r['weather']:<12} {r['t_out']:>7.0f} {r['drive_pa']:>8.2f} {100 * r['share']:>10.0f}% "
                    f"{r['fan_pa']:>15.2f} {r['litres_day']:>17.2f}")
    return "\n".join(rows)


def constants_table() -> str:
    width = max(len(n) for n, *_ in CONSTANTS)
    return "\n".join(f"{n:<{width}}  {v:>8g} {u:<4} {k:<10} {w}" for n, v, u, k, w in CONSTANTS)


def validate_seam_vent() -> None:
    r = descending_seams()
    rings = sc.rings()
    pent = next(b for b in rings["bands"] if b.key == "pentagon")
    assert r.level_seams == pent.seams, "the only level seams are the pentagon ring's"
    assert r.cap_penetrations == 0 and r.rim_outlets == rings["rim_ports"]
    assert 0 < r.path_ft < rings["meridian_ft"], "a falling path is shorter than over-the-top"
    cap = capacity()
    assert cap["headroom"] > 1, "the five cap seams carry the need at a quiet speed"
    table = weather_table()
    # colder outside: stronger siphon; summer sun: the siphon runs the wrong way
    drives = [row["drive_pa"] for row in table]
    assert drives[:4] == sorted(drives[:4], reverse=True) and drives[-1] < 0
    assert table[-1]["natural_cfm"] == 0 and table[-1]["fan_pa"] > 0
    assert table[-1]["fan_pa"] < sc.C["fan_static_pa"], "a small fan covers the worst case"
    assert table[0]["litres_day"] > 0, "a hard winter condenses in the keys"
    assert freeze_limit() < 0


if __name__ == "__main__":
    validate_seam_vent()
    print(descending_seams())
    print(capacity())
    print(table_text())
    print("outlet freezes below", round(freeze_limit(), 1), "C")
