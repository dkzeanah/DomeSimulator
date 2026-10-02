"""The seam as a climate system: which way the air goes, and why.

The seam channel (:mod:`two_v_demo.channel_facts`) carries water, wire and
air, and :mod:`wedge_book.systems` fits it with a gate, a cartridge and
Peltier plates. This module is the part that decides what they do, in the
owner's own terms:

* **three questions** -- which air is actually drier (dew point, never
  relative humidity), will this air condense on that surface, and which way
  should the air move -- answered by :func:`decide` from the dome's sensors;
* **seven modes** the one channel can be switched between, including the
  two that never touch the living space: a closed **frame loop** through the
  desiccant, and an outside-to-outside **purge** of a wet seam;
* **where each job belongs on the dome**, from the solver's own seams: which
  seams drain, which lie dead level, where the low points are (:func:`rings`);
* **where the desiccant belongs**, from the bed's own physics: what it holds
  (:func:`beds`), what it costs to push air through it (:func:`ergun`), and
  the temperature it needs to give its water back (:func:`regeneration`).

Physical constants are declared ``standard`` or ``nominal``; everything that
is a judgement is ``estimate`` or ``assumption``, with its reason, in
:data:`CONSTANTS`. The ten weathers the owner listed are :data:`SCENARIOS`
(estimates: typical conditions, not measurements), each with the answer the
owner's table gives, and :func:`validate_seam_climate` checks the controller
reaches it.

    py -3.12 -m two_v_demo.seam_climate          # the whole report
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from functools import lru_cache

from . import channel_facts as cf

M_PER_IN = 0.0254
M3_PER_CUFT = 0.028316846592
PA_PER_INWC = 249.089


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    # -- physics ------------------------------------------------------
    ("magnus_a", 17.62, "-", "standard",
     "Magnus formula over water (Sonntag 1990), good to 0.1 K from -45 to 60 C"),
    ("magnus_b_c", 243.12, "C", "standard", "Magnus formula, second coefficient"),
    ("air_density", 1.20, "kg/m3", "standard", "air at about 20 C at sea level"),
    ("air_viscosity", 1.81e-5, "Pa s", "standard", "dynamic viscosity of air at 20 C"),
    ("gravity", 9.81, "m/s2", "standard", "standard gravity"),
    # -- the desiccant ------------------------------------------------
    ("sieve_uptake", 0.20, "kg/kg", "nominal",
     "13X molecular sieve: water held per kilogram of beads at room humidity; "
     "makers list about 0.20 to 0.25 at saturation"),
    ("sieve_bulk_density", 650.0, "kg/m3", "nominal", "13X beads, poured"),
    ("bead_diameter_mm", 2.5, "mm", "nominal", "8x12 mesh beads, the common size"),
    ("bed_voidage", 0.37, "-", "standard", "a random pack of spheres"),
    ("sieve_regen_c", 200.0, "C", "nominal",
     "13X gives up its water between about 150 and 300 C; the low end of useful"),
    ("silica_regen_c", 120.0, "C", "nominal", "silica gel regenerates at 110 to 130 C"),
    ("sieve_heat_kj_per_kg", 3700.0, "kJ/kg", "estimate",
     "heat to drive a kilogram of water off zeolite: its evaporation plus the "
     "binding energy; published figures run 3,300 to 4,200"),
    # -- what the seam is made of --------------------------------------
    ("petg_soft_c", 80.0, "C", "nominal", "PETG's glass transition: the printed key goes soft here"),
    ("seam_air_max_c", 60.0, "C", "assumption",
     "the hottest air sent through a seam: twenty degrees under PETG's softening, "
     "and a gentle kiln for softwood"),
    ("pine_dry_density", 420.0, "kg/m3", "estimate",
     "oven-dry pine; species run from about 350 to 510"),
    ("mc_wet", 0.19, "kg/kg", "standard",
     "lumber grading's line for 'dry': above 19% moisture, wood is wet enough to decay"),
    ("mc_target", 0.12, "kg/kg", "estimate", "what framing settles to indoors"),
    # -- control margins ----------------------------------------------
    ("dp_margin_k", 1.0, "K", "assumption",
     "one air must be this much drier than the other before the controller "
     "calls it drier, so it does not flap between modes"),
    ("wood_margin_k", 3.0, "K", "assumption",
     "keep every wood surface this far above the dew point of the air touching it"),
    ("plate_below_dp_k", 6.0, "K", "assumption",
     "how far under the air's dew point the condensing plate is driven"),
    ("plate_approach_k", 2.0, "K", "assumption",
     "air leaving the plate keeps a dew point this far above the plate"),
    ("frost_floor_c", 1.0, "C", "assumption",
     "the plate is never driven below this: under freezing it grows frost, "
     "which stops the water running and blocks the fins"),
    ("rh_high", 0.60, "-", "assumption", "indoor relative humidity the controller acts on"),
    ("seam_rh_wet", 0.85, "-", "assumption",
     "channel air this humid means a seam is wet, whatever the wood meter says"),
    # -- hardware -------------------------------------------------------
    ("fan_static_pa", 250.0, "Pa", "estimate",
     "what a small EC in-line fan can push against, about one inch of water"),
    ("drawer_face_m", 0.30, "m", "assumption", "one cartridge drawer, 30 cm square"),
    ("drawer_depth_m", 0.05, "m", "assumption", "a bed 5 cm deep"),
    ("stove_exchanger_kw", 2.0, "kW", "estimate",
     "heat a small sealed exchanger on a stove flue hands to clean air"),
    ("indoor_t_c", 21.0, "C", "assumption", "the room the dome is held at"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}


# ----------------------------------------------------------------------
# Psychrometrics
# ----------------------------------------------------------------------

def vapour_pressure_hpa(t_c: float) -> float:
    """Saturation vapour pressure over water (Magnus)."""
    return 6.112 * math.exp(C["magnus_a"] * t_c / (C["magnus_b_c"] + t_c))


def dew_point(t_c: float, rh: float) -> float:
    """Dew point in C from temperature and relative humidity (0-1)."""
    g = math.log(max(rh, 1e-6)) + C["magnus_a"] * t_c / (C["magnus_b_c"] + t_c)
    return C["magnus_b_c"] * g / (C["magnus_a"] - g)


def humidity_ratio(t_c: float, rh: float, p_hpa: float = 1013.25) -> float:
    """Grams of water per kilogram of dry air."""
    e = rh * vapour_pressure_hpa(t_c)
    return 622.0 * e / (p_hpa - e)


# ----------------------------------------------------------------------
# The controller
# ----------------------------------------------------------------------

MODES: dict[str, tuple[str, str]] = {
    "CLOSED": ("rain: exposed intakes shut", "nothing moves through a wet ridge"),
    "INTAKE": ("outside -> seam -> inside", "outside air is drier: free drying"),
    "EXHAUST": ("inside -> seam -> outside", "inside is too humid and outside is drier"),
    "CONDENSE": ("inside -> cold seam -> drain -> outside",
                 "harvest the water on a cold skin before the air leaves"),
    "FRAME_LOOP": ("seam -> desiccant -> seam", "dry the frame when no air is dry enough"),
    "PURGE": ("outside -> seam -> outside", "dry a wet seam without it touching the room"),
    "DRY_SUPPLY": ("dehumidified air in, slight positive pressure",
                   "outside is wetter: never take it raw"),
    "IDLE": ("gates shut, fans at barrier speed", "nothing to fix"),
}
ACTIVE_MODES = tuple(k for k in MODES if k != "IDLE")
"""The modes that move air somewhere: the count films and the book state.
IDLE is the controller's resting state, not a job the channel does."""


@dataclass(frozen=True)
class Sensors:
    t_in: float
    rh_in: float
    t_out: float
    rh_out: float
    t_seam: float
    rh_seam: float
    wood_mc: float
    rain: bool = False
    harvest: bool = False          # the owner wants the water, not just dry air
    cooling: bool = False          # an air conditioner is running


@dataclass(frozen=True)
class Decision:
    mode: str
    dp_in: float
    dp_out: float
    dp_seam: float
    reasons: tuple[str, ...]


def decide(s: Sensors) -> Decision:
    """The owner's three questions, in order, as code."""
    dp_in, dp_out = dew_point(s.t_in, s.rh_in), dew_point(s.t_out, s.rh_out)
    dp_seam = dew_point(s.t_seam, s.rh_seam)
    m = C["dp_margin_k"]
    why: list[str] = []

    def done(mode: str) -> Decision:
        return Decision(mode, dp_in, dp_out, dp_seam, tuple(why))

    wet_frame = s.wood_mc >= C["mc_wet"] or s.rh_seam >= C["seam_rh_wet"]
    if s.rain:
        why.append("raining: shut every exposed intake")
        if wet_frame:
            why.append("frame wet: dry it on its own loop, sealed from the rain")
            return done("FRAME_LOOP")
        return done("CLOSED")
    if wet_frame:
        why.append(f"frame wet (seam dew point {dp_seam:.1f} C)")
        if dp_out < dp_seam - m:
            why.append("outside air is drier than the seam's: purge it straight back out")
            return done("PURGE")
        why.append("no outside air dry enough: close the loop through the desiccant")
        return done("FRAME_LOOP")
    # Question 1: which air is actually drier?
    outside_drier = dp_out < dp_in - m
    outside_wetter = dp_out > dp_in + m
    why.append(f"dew point in {dp_in:.1f} C, out {dp_out:.1f} C: "
               + ("outside is drier" if outside_drier else
                  "outside is wetter" if outside_wetter else "about the same"))
    if s.rh_in > C["rh_high"]:
        if outside_drier:
            # Question 2: will indoor air condense on the outside skin?
            if s.harvest and s.t_out <= dp_in - C["plate_below_dp_k"]:
                why.append(f"outside skin near {s.t_out:.0f} C, under the indoor dew point: "
                           "condense for free, then exhaust")
                return done("CONDENSE")
            why.append("inside too humid, outside drier: exhaust")
            return done("EXHAUST")
        why.append("inside too humid and outside no help: dehumidify, hold pressure")
        return done("DRY_SUPPLY")
    # Question 3: which way should the air move?
    if outside_drier:
        why.append("outside air can dry the dome: take it in")
        return done("INTAKE")
    if outside_wetter:
        why.append("outside air is a moisture source: dry supply only"
                   + (", with the cooling running" if s.cooling else ""))
        return done("DRY_SUPPLY")
    return done("IDLE")


def plate_setpoint(dp_air: float) -> float:
    """Where the condensing plate is held: under the dew point, never frozen."""
    return max(C["frost_floor_c"], dp_air - C["plate_below_dp_k"])


def wood_is_safe(t_wood: float, dp_air: float, dried_first: bool) -> bool:
    """Air that has passed the plate carries the plate's dew point, not its own."""
    dp = min(dp_air, plate_setpoint(dp_air) + C["plate_approach_k"]) if dried_first else dp_air
    return t_wood > dp + C["wood_margin_k"]


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    sensors: Sensors
    want: tuple[str, ...]          # the answers the owner's table accepts
    why: str                       # the owner's own reason


def _s(t_out, rh_out, *, t_in=None, rh_in=0.45, t_seam=None, rh_seam=0.55, mc=0.13, **kw):
    t_in = C["indoor_t_c"] if t_in is None else t_in
    t_seam = (t_in + t_out) / 2 if t_seam is None else t_seam
    return Sensors(t_in, rh_in, t_out, rh_out, t_seam, rh_seam, mc, **kw)


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("cold_dry", "Cold + dry outside", _s(-5, 0.60), ("INTAKE",),
             "outdoor air holds little moisture"),
    Scenario("cold_humid_in", "Cold outside + humid inside", _s(-5, 0.80, rh_in=0.68),
             ("EXHAUST", "CONDENSE"), "removes moisture made indoors"),
    Scenario("cold_harvest", "Cold outside, harvesting water", _s(-2, 0.80, rh_in=0.68, harvest=True),
             ("CONDENSE",), "harvest the water before the air leaves"),
    Scenario("mild_dry", "Mild + dry outside", _s(16, 0.40), ("INTAKE",), "free drying"),
    Scenario("hot_dry", "Hot + dry outside", _s(33, 0.18, rh_in=0.50), ("INTAKE",),
             "outside dew point is lower"),
    Scenario("hot_humid", "Hot + humid outside", _s(32, 0.70, rh_in=0.50), ("DRY_SUPPLY",),
             "raw outside air adds moisture"),
    Scenario("hot_humid_ac", "Hot + humid, cooling on", _s(35, 0.60, t_in=24, rh_in=0.50, cooling=True),
             ("DRY_SUPPLY",), "positive pressure with dry supply"),
    Scenario("rain", "Rain", _s(14, 0.97, rain=True), ("CLOSED",),
             "no uncontrolled intake through wet seams"),
    Scenario("after_rain", "After rain, dry outside", _s(18, 0.45, rh_seam=0.90, mc=0.21),
             ("PURGE",), "dry what the rain left, outside the room"),
    Scenario("sun_wet", "Sun on a wet skin", _s(24, 0.55, t_seam=45, rh_seam=0.60, mc=0.20),
             ("PURGE",), "vent the vapour the sun drives, outward"),
    Scenario("muggy_wet", "Muggy outside, wet frame", _s(36, 0.60, t_in=24, rh_in=0.55, rh_seam=0.88, mc=0.20),
             ("FRAME_LOOP",), "neither air is dry enough: close the loop"),
)


# ----------------------------------------------------------------------
# The dome's seams, by where they are
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Band:
    key: str
    label: str
    seams: int
    length_ft: float
    slope_deg: float          # mean angle of the seam from horizontal
    drains: bool


BAND_LABELS = {"lower": "lower band, rim to belt", "belt": "the zigzag belt",
               "upper": "upper band, belt to pentagon", "pentagon": "the pentagon ring",
               "cap": "the cap, to the apex"}


def classify(model) -> dict[str, list]:
    """Any solved 2V dome's seams, by the band they run in.

    The dome stands on five vertex heights: the rim, a belt that zigzags
    between two heights, the pentagon round the crown, and the apex. Used for
    the reference build and for the Cabin World's own dome alike."""
    topo = model.topology
    r = topo.sphere_radius_in
    levels = sorted({round(float(v[2]) / r, 3) for v in topo.vertices})
    rim, low, high, penta, apex = levels
    names = {(rim, low): "lower", (rim, high): "lower", (low, high): "belt",
             (low, penta): "upper", (high, penta): "upper", (penta, penta): "pentagon",
             (penta, apex): "cap"}
    groups: dict[str, list] = {k: [] for k in BAND_LABELS}
    for s in model.seams:
        za, zb = sorted((round(float(s.start[2]) / r, 3), round(float(s.end[2]) / r, 3)))
        groups[names[(za, zb)]].append(s)
    return groups


@lru_cache(maxsize=1)
def rings() -> dict:
    """The solver's seams sorted into the dome's levels, with their slopes."""
    import numpy as np

    model = cf.reference_model()
    topo = model.topology
    r = topo.sphere_radius_in
    levels = sorted({round(float(v[2]) / r, 3) for v in topo.vertices})
    rim, low = levels[0], levels[1]
    labels = BAND_LABELS
    groups = classify(model)
    bands = []
    for key, seams in groups.items():
        slopes = [math.degrees(math.asin(abs(float(s.end[2] - s.start[2]))
                                         / float(np.linalg.norm(s.end - s.start)))) for s in seams]
        mean = sum(slopes) / len(slopes)
        bands.append(Band(key, labels[key], len(seams),
                          sum(float(np.linalg.norm(s.end - s.start)) for s in seams) / 12.0,
                          mean, min(slopes) > 2.0))
    counts = {lv: sum(1 for v in topo.vertices if round(float(v[2]) / r, 3) == lv) for lv in levels}
    return {"bands": tuple(bands), "levels": tuple(levels), "counts": counts,
            "belt_low_points": counts[low], "rim_ports": counts[rim],
            "apex_height_ft": r / 12.0, "meridian_ft": meridian_ft()}


def meridian_ft() -> float:
    """The shortest seam path from rim to rim over the apex: the 'rainbow'."""
    import numpy as np

    model = cf.reference_model()
    topo = model.topology
    verts = [np.asarray(v, dtype=float) for v in topo.vertices]
    top = max(range(len(verts)), key=lambda i: verts[i][2])
    rim = [i for i, v in enumerate(verts) if abs(v[2]) < 1e-6]
    graph: dict[int, list] = {}
    for s in model.seams:
        a, b = s.edge_key
        w = float(np.linalg.norm(verts[a] - verts[b]))
        graph.setdefault(a, []).append((b, w))
        graph.setdefault(b, []).append((a, w))
    dist = {top: 0.0}
    queue = [(0.0, top)]
    while queue:
        d, v = heapq.heappop(queue)
        if d > dist.get(v, math.inf):
            continue
        for u, w in graph.get(v, ()):
            if d + w < dist.get(u, math.inf):
                dist[u] = d + w
                heapq.heappush(queue, (d + w, u))
    return 2 * min(dist[i] for i in rim if i in dist) / 12.0


def stack_pa(delta_t_k: float = 10.0) -> float:
    """The chimney pull between rim and apex when the inside is warmer."""
    h = rings()["apex_height_ft"] * 0.3048
    t = C["indoor_t_c"] + 273.15
    return C["air_density"] * C["gravity"] * h * delta_t_k / t


# ----------------------------------------------------------------------
# The desiccant
# ----------------------------------------------------------------------

def ergun(velocity_m_s: float) -> float:
    """Pressure drop per metre of packed bed, Pa/m (Ergun)."""
    eps, d = C["bed_voidage"], C["bead_diameter_mm"] / 1000.0
    mu, rho = C["air_viscosity"], C["air_density"]
    return (150 * mu * (1 - eps) ** 2 * velocity_m_s / (eps ** 3 * d * d)
            + 1.75 * rho * (1 - eps) * velocity_m_s ** 2 / (eps ** 3 * d))


def frame_water_kg() -> float:
    """Water a wet frame must give up to reach its indoor moisture."""
    import seed_world

    m3 = seed_world.geometry().member_volume_cuft * M3_PER_CUFT
    return m3 * C["pine_dry_density"] * (C["mc_wet"] - C["mc_target"])


@dataclass(frozen=True)
class Beds:
    frame_water_kg: float
    # Packing every seam's channel with beads
    seams_sieve_kg: float
    seams_hold_kg: float
    seam_flow_cfm: float
    seam_velocity_m_s: float
    seam_drop_pa: float            # across one packed seam at that flow
    seam_flow_at_fan_cfm: float    # what the fan can push through one packed seam
    # One drawer in the manifold instead
    drawer_sieve_kg: float
    drawer_hold_kg: float
    drawer_flow_cfm: float
    drawer_drop_pa: float
    drawers_for_frame: float


def beds() -> Beds:
    types = cf.seam_types()
    air = cf.air()
    tight = min(types, key=lambda t: t.gap_deg)
    t_air = next(x for x in air["per_type"] if x["seam"] == tight)
    m3 = sum(cf.room(t).inside_in2 * M_PER_IN ** 2 * t.length_in * M_PER_IN * t.count for t in types)
    sieve = m3 * C["sieve_bulk_density"]
    area = cf.room(tight).inside_in2 * M_PER_IN ** 2
    length = tight.length_in * M_PER_IN
    q = t_air["cfm"] * M3_PER_CUFT / 60.0
    v = q / area
    drop = ergun(v) * length

    # The flow the fan can force through one packed seam: solve ergun(v) * L = fan.
    lo, hi = 0.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ergun(mid) * length < C["fan_static_pa"] else (lo, mid)
    at_fan = lo * area * 60.0 / M3_PER_CUFT

    face = C["drawer_face_m"] ** 2
    d_sieve = face * C["drawer_depth_m"] * C["sieve_bulk_density"]
    d_q = air["need_cfm"] * M3_PER_CUFT / 60.0
    d_drop = ergun(d_q / face) * C["drawer_depth_m"]
    water = frame_water_kg()
    return Beds(water, sieve, sieve * C["sieve_uptake"], t_air["cfm"], v, drop, at_fan,
                d_sieve, d_sieve * C["sieve_uptake"], air["need_cfm"], d_drop,
                water / (d_sieve * C["sieve_uptake"]))


def regeneration() -> dict:
    """What it takes to give the water back, and where that can happen."""
    b = beds()
    kwh = b.drawer_hold_kg * C["sieve_heat_kj_per_kg"] / 3600.0
    return {"drawer_kwh": kwh,
            "stove_minutes": kwh / C["stove_exchanger_kw"] * 60.0,
            "frame_kwh": b.frame_water_kg * C["sieve_heat_kj_per_kg"] / 3600.0,
            "sieve_c": C["sieve_regen_c"], "silica_c": C["silica_regen_c"],
            "seam_max_c": C["seam_air_max_c"], "petg_c": C["petg_soft_c"],
            "in_seam": C["sieve_regen_c"] <= C["seam_air_max_c"]}


# ----------------------------------------------------------------------
# The owner's question about the cold channel
# ----------------------------------------------------------------------

def cold_channel(t_air: float = None, rh_air: float = 0.55, below_dp: float = 17.5) -> dict:
    """A metal channel held well under the dew point, next to wood at the dew point.

    ``below_dp`` is the owner's 15 to 20 degrees, taken at its middle.
    """
    t_air = C["indoor_t_c"] if t_air is None else t_air
    dp = dew_point(t_air, rh_air)
    owners_plate = dp - below_dp
    plate = plate_setpoint(dp)
    after = min(dp, plate + C["plate_approach_k"])
    return {"t_air": t_air, "rh_air": rh_air, "dp": dp, "below": below_dp,
            "owners_plate": owners_plate, "owners_frost": owners_plate <= 0.0,
            "plate": plate, "dp_after": after,
            "wood_at_dp_safe_raw": wood_is_safe(dp, dp, dried_first=False),
            "wood_at_dp_safe_dried": wood_is_safe(dp, dp, dried_first=True),
            "wood_min_dried": after + C["wood_margin_k"]}


# ----------------------------------------------------------------------
# Report and checks
# ----------------------------------------------------------------------

def report() -> str:
    out = ["THE SEAM AS A CLIMATE SYSTEM", ""]
    for sc in SCENARIOS:
        d = decide(sc.sensors)
        out.append(f"{sc.label:<34} dp in {d.dp_in:5.1f}  out {d.dp_out:5.1f}  seam "
                   f"{d.dp_seam:5.1f} -> {d.mode:<10} (owner: {'/'.join(sc.want)})")
    r = rings()
    out += ["", "levels (z/R): " + ", ".join(f"{lv:.3f} x{r['counts'][lv]}" for lv in r["levels"])]
    for b in r["bands"]:
        out.append(f"  {b.label:<30} {b.seams:>2} seams {b.length_ft:6.1f} ft, "
                   f"slope {b.slope_deg:5.1f} deg, {'drains' if b.drains else 'DEAD LEVEL'}")
    out.append(f"  rainbow rim-apex-rim {r['meridian_ft']:.1f} ft; stack pull at 10 K: "
               f"{stack_pa():.2f} Pa")
    b = beds()
    out += ["", f"frame water to lose, 19% -> 12%: {b.frame_water_kg:.0f} kg",
            f"every seam packed: {b.seams_sieve_kg:.0f} kg sieve holds {b.seams_hold_kg:.1f} kg",
            f"  one packed seam at {b.seam_flow_cfm:.1f} cfm ({b.seam_velocity_m_s:.2f} m/s): "
            f"{b.seam_drop_pa:,.0f} Pa; at the fan's {C['fan_static_pa']:.0f} Pa: "
            f"{b.seam_flow_at_fan_cfm:.2f} cfm",
            f"one drawer: {b.drawer_sieve_kg:.1f} kg holds {b.drawer_hold_kg:.2f} kg, "
            f"{b.drawer_flow_cfm:.0f} cfm at {b.drawer_drop_pa:.0f} Pa; "
            f"{b.drawers_for_frame:.1f} fills dry the frame"]
    g = regeneration()
    out.append(f"regen: {g['drawer_kwh']:.2f} kWh a drawer = {g['stove_minutes']:.0f} min of "
               f"exchanger; whole frame {g['frame_kwh']:.0f} kWh; sieve {g['sieve_c']:.0f} C vs "
               f"seam limit {g['seam_max_c']:.0f} C")
    c = cold_channel()
    out.append(f"cold channel: air {c['t_air']:.0f} C {c['rh_air'] * 100:.0f}% dp {c['dp']:.1f}; "
               f"owner's plate {c['owners_plate']:.1f} C (frost {c['owners_frost']}); held at "
               f"{c['plate']:.1f}; wood at the dew point safe raw={c['wood_at_dp_safe_raw']} "
               f"dried-first={c['wood_at_dp_safe_dried']}")
    return "\n".join(out)


def validate_seam_climate() -> None:
    # Psychrometrics against textbook points.
    assert abs(dew_point(20.0, 0.50) - 9.3) < 0.1
    assert abs(dew_point(30.0, 0.70) - 23.9) < 0.15
    assert abs(humidity_ratio(20.0, 0.50) - 7.3) < 0.1
    for t in (-10.0, 0.0, 25.0):
        assert abs(dew_point(t, 1.0) - t) < 1e-9
    # Relative humidity is not the question: colder air at a higher RH can be drier.
    assert dew_point(-5, 0.80) < dew_point(21, 0.45)
    # Every one of the owner's weathers gets the owner's answer.
    for sc in SCENARIOS:
        got = decide(sc.sensors).mode
        assert got in sc.want, f"{sc.key}: {got} not in {sc.want}"
    assert set(MODES) >= {decide(sc.sensors).mode for sc in SCENARIOS}
    # The plate is never frozen and always under the dew point it serves.
    for dp in (-3.0, 5.0, 18.0):
        assert plate_setpoint(dp) >= C["frost_floor_c"]
    assert plate_setpoint(18.0) < 18.0
    # The dome's levels are the owner's four, and the ring at the top is level.
    r = rings()
    assert len(r["levels"]) == 5 and r["counts"][r["levels"][0]] == 10
    bands = {b.key: b for b in r["bands"]}
    assert sum(b.seams for b in bands.values()) == sum(t.count for t in cf.seam_types())
    assert not bands["pentagon"].drains and bands["lower"].drains
    assert r["meridian_ft"] > 0
    # The bed physics, and the conclusions the film draws from it.
    assert ergun(0.5) > ergun(0.1) > 0
    b = beds()
    assert b.seam_drop_pa > C["fan_static_pa"], "a packed seam would not be the problem the film says"
    assert b.drawer_drop_pa < C["fan_static_pa"], "the drawer must be pushable"
    assert not regeneration()["in_seam"], "zeolite cannot be regenerated inside a printed seam"
    c = cold_channel()
    # The owner's colder channel freezes; wood at the dew point is safe only when
    # the air meets the plate before it meets the wood.
    assert c["owners_frost"] and not c["wood_at_dp_safe_raw"] and c["wood_at_dp_safe_dried"]


if __name__ == "__main__":
    validate_seam_climate()
    print(report())
