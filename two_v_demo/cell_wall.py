"""The cell wall: the dome's skin as a stack of layers that each carry a network.

The owner's idea, worked through (October 2026). Every strut gets a groove
-- a C-channel -- in its round outer face, and a hose in that groove makes one
closed loop around each triangle: a *local* channel that reaches one triangle
and nothing else. The seams between triangles already hold the *global*
channel (:mod:`two_v_demo.channel_facts`). Stack several sheathing layers over
the frame, give each its own local and global network, and the wall becomes a
set of independent services that can be run alone, run both ways, or plugged
into each other -- closer to a car's CAN bus than to a wall.

This module is the arithmetic behind the film :mod:`two_v_demo.lesson_cell_wall`:

* the networks, measured off the solver's own dome (:func:`networks`);
* the groove's cost to the strut (:func:`groove`);
* the layer stack and **which side of the insulation** each layer must live
  on, from a steady-state temperature profile (:func:`profile`);
* one computed check per function -- foam, glue, rain, fire water, vacuum,
  filter, heat, cool, Faraday cage, fog, flotation, living surface, extras;
* the router: which layer may feed which, seven situations, and the
  interlocks that keep them from fighting (:data:`SCENARIOS`,
  :func:`check_scenario`);
* the cost of all of it in valves and joints (:func:`complexity`).

Every figure that is not geometry is declared in :data:`CONSTANTS` with its
kind and reason, or borrowed by name from the module that already declares it.

    py -3.12 -m two_v_demo.cell_wall
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import channel_facts as cf
from . import seam_climate as scl
from . import seam_vent as sv

IN = 0.0254
FT = 0.3048
M2_PER_FT2 = FT * FT
L_PER_GAL = 3.785411784
GPM_PER_LPS = 15.850323
RSI_PER_RIMP = 0.1761101838         # m2K/W per hr ft2 F/BTU
C_LIGHT = 299_792_458.0
R_GAS = 8.314462618
BDFT_PER_M3 = 423.776                # board feet in a cubic metre

# name, value, unit, kind, why
CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    # -- the groove and the hoses ----------------------------------------
    ("groove_w_in", 0.75, "in", "assumption",
     "the C-channel: a 3/4 in core-box groove routed down the middle of each strut's round face"),
    ("groove_d_in", 0.75, "in", "assumption", "and 3/4 in deep, enough to bury a 1/2 in hose"),
    ("local_hose_id_mm", 10.0, "mm", "assumption", "the local loop: 3/8 in bore tubing"),
    ("global_hose_id_mm", 25.0, "mm", "assumption", "a global run in the seam: 1 in bore"),
    ("hose_wall_mm", 1.5, "mm", "nominal", "polyethylene tubing's wall"),
    ("layer_gap_mm", 8.0, "mm", "nominal",
     "one networked layer: a dimpled drainage mat, the common 8 mm stud height"),
    ("osb_mm", 11.0, "mm", "nominal", "7/16 in OSB, the usual roof sheathing"),
    ("osb_kg_m2", 6.8, "kg/m2", "estimate", "7/16 in OSB weighs about 1.4 lb a square foot"),
    # -- the core ----------------------------------------------------------
    ("foam_r_per_in", 6.0, "imperial R/in", "nominal",
     "closed-cell polyurethane, R-6 to R-7 an inch; the low end"),
    ("foam_kit_bdft", 600.0, "board ft", "nominal", "a two-part foam kit sold as 600 board feet"),
    ("foam_kit_usd", 750.0, "USD", "estimate", "what such a kit costs"),
    ("foam_lifts", 3.0, "lifts", "assumption",
     "injection foam is poured in three lifts so its expansion pressure cannot bow "
     "the sheathing off the frame"),
    ("glue_cartridge_ml", 300.0, "mL", "nominal", "one caulking-gun cartridge of PU adhesive"),
    ("glue_bead_mm2", 30.0, "mm2", "assumption",
     "a bead pushed out of a perforated hose, about 6 mm across, instead of a full groove"),
    # -- pressures ---------------------------------------------------------
    ("sheet_vacuum_kpa", 1.0, "kPa", "assumption",
     "the most vacuum allowed across a whole layer: below the sheathing's design load"),
    ("hose_vacuum_kpa", 25.0, "kPa", "nominal",
     "central-vacuum sealed suction, about 100 in of water lift; lives in hoses only"),
    ("sheathing_design_kpa", 1.2, "kPa", "assumption",
     "the inward load the sheathing is designed for: a 25 psf roof live/snow load"),
    ("water_vacuum_kpa", 5.0, "kPa", "assumption",
     "the water layer's draw: lifts the rim gutter's water half a metre into a raised tank"),
    ("atmosphere_kpa", 101.325, "kPa", "standard", "the air's own pressure at sea level"),
    ("wind_gust_m_s", 40.0, "m/s", "assumption", "a 90 mph design gust"),
    ("wind_cp", 1.0, "-", "estimate", "peak suction coefficient on a dome's crown"),
    ("air_density", 1.2, "kg/m3", "standard", "air near sea level"),
    # -- water and fire ----------------------------------------------------
    ("wetting_gpm_ft2", 0.10, "gpm/ft2", "standard",
     "NFPA 13's light-hazard density: used here as the rate that keeps a surface wet"),
    ("pump_head_m", 20.0, "m", "assumption", "lift to the crown plus nozzle pressure"),
    ("pump_eff", 0.5, "-", "estimate", "a small electric pump, wire to water"),
    ("fibre_saturation", 0.28, "kg/kg", "standard", "wood holds water in its cell walls up to about 28%"),
    ("ember_minutes", 30.0, "min", "assumption",
     "how long embers keep landing as a fire front passes: tens of minutes"),
    ("bal_kw_m2", 29.0, "kW/m2", "standard",
     "AS 3959's BAL-29: the radiant heat a house is built to take at a bushfire's edge"),
    ("flame_zone_kw_m2", 40.0, "kW/m2", "standard",
     "above BAL-40 is the flame zone, where no skin is enough"),
    ("fire_side_fraction", 0.5, "-", "geometry", "half a dome faces the fire"),
    ("latent_mj_kg", 2.257, "MJ/kg", "standard", "heat water takes to evaporate at 100 C"),
    ("water_warm_k", 85.0, "K", "assumption", "the water warms from 15 C to boiling first"),
    ("flood_film_mm", 0.5, "mm", "assumption",
     "water left clinging to the sheathing's face when a flood drains"),
    ("purge_cfm", 100.0, "cfm", "assumption", "a small in-line fan pushing air through the flutes"),
    ("dry_day_c", 20.0, "C", "assumption", "a mild day after the front has passed"),
    ("dry_day_rh", 0.50, "-", "assumption", "and half-saturated"),
    ("exit_rh", 0.95, "-", "assumption", "air leaves the wet flutes nearly saturated"),
    # -- air ---------------------------------------------------------------
    ("furnace_face_m_s", 2.5, "m/s", "nominal", "air speed through a furnace filter, about 500 ft/min"),
    # -- heat --------------------------------------------------------------
    ("radiant_h", 8.0, "W/m2K", "estimate", "radiant plus convective exchange from a warm wall"),
    ("heating_dt_k", 10.0, "K", "assumption", "warm-water wall: 10 K above the room"),
    ("winter_out_c", -15.0, "C", "assumption", "the design cold night"),
    ("room_c", 21.0, "C", "assumption", "the room"),
    ("film_in_rsi", 0.13, "m2K/W", "standard", "inside surface film"),
    ("film_out_rsi", 0.04, "m2K/W", "standard", "outside surface film, windy"),
    ("osb_rsi", 0.10, "m2K/W", "standard", "7/16 in OSB"),
    ("layer_rsi", 0.02, "m2K/W", "estimate", "one thin networked layer"),
    # -- the cage ----------------------------------------------------------
    ("mesh_aperture_mm", 6.35, "mm", "nominal", "1/4 in hardware cloth"),
    ("door_w_m", 0.90, "m", "nominal", "a doorway in one panel"),
    ("wifi_ghz", 2.4, "GHz", "standard", "Wi-Fi and most phones' middle band"),
    # -- fog ---------------------------------------------------------------
    ("fog_m3_s", 10.0, "m3/s", "estimate",
     "a commercial security-fog unit: they are sold to fill a room in seconds"),
    # -- flotation ---------------------------------------------------------
    ("cap_kg_m2", 1.5, "kg/m2", "estimate", "the waterproof cap and its fabric"),
    ("floor_kg_m2", 120.0, "kg/m2", "assumption", "floor, fit-out and belongings, per square metre of plan"),
    ("airbag_m", 0.20, "m", "assumption", "how thick a bladder layer inflates"),
    ("water_density", 1000.0, "kg/m3", "standard", "fresh water"),
    ("co2_cylinder_kg", 9.0, "kg", "nominal", "a 20 lb CO2 cylinder"),
    # -- the living surface ------------------------------------------------
    ("plant_max_slope_deg", 30.0, "deg", "estimate",
     "steepest a planted surface holds its medium without cleats or a grid"),
    ("green_kg_m2", 120.0, "kg/m2", "estimate",
     "an extensive green roof, saturated: 4 in of medium and its plants"),
    ("green_water_l_m2_day", 3.0, "L/m2/day", "estimate", "summer irrigation"),
    ("felt_kg_m2", 30.0, "kg/m2", "estimate",
     "a felt living-wall system, wet: plants rooted in fabric pockets, no soil"),
    # -- extras ------------------------------------------------------------
    ("snowmelt_w_m2", 300.0, "W/m2", "estimate", "a residential snow-melting slab"),
    ("solar_eff", 0.40, "-", "estimate", "an unglazed water layer as a solar collector"),
    ("sunlit_fraction", 0.5, "-", "geometry", "half a dome faces the sun"),
    ("fumigation_co2", 0.60, "-", "nominal", "CO2 fraction used to kill insects in a closed space"),
    ("co2_density", 1.84, "kg/m3", "standard", "CO2 at room temperature"),
    ("borate_l_m2", 0.20, "L/m2", "estimate", "borate solution sprayed on bare timber"),
    # -- the bus and the sampling lines -------------------------------------
    ("can_500k_m", 100.0, "m", "standard", "the usual length limit of a CAN bus at 500 kbit/s"),
    ("can_125k_m", 500.0, "m", "standard", "and at 125 kbit/s"),
    ("sample_m_s", 1.0, "m/s", "assumption",
     "air speed down a smoke-sampling line; aspirating detectors must deliver a sample "
     "within 120 s"),
    ("sample_limit_s", 120.0, "s", "standard", "the longest an aspirating detector's sample may take"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}


def borrowed() -> dict:
    """Figures this module uses but other modules already declare."""
    from wedge_book import systems

    from .dome_performance import FACT

    return {"rain_in_year": FACT["rainfall_in_year"], "runoff": FACT["runoff_coefficient"],
            "radiative_w_m2": FACT["radiative_cool_w_m2"], "peak_solar_w_m2": FACT["peak_solar_w_m2"],
            "tank_gal": systems.declared("water_tank_gal"),
            "volume_m3": systems.air_barrier()["volume_cuft"] * FT ** 3,
            "pine_kg_m3": scl.C["pine_dry_density"], "mc_target": scl.C["mc_target"],
            "wood_margin_k": scl.C["wood_margin_k"], "need_cfm": sv.need_cfm()}


# ----------------------------------------------------------------------
# The networks, off the solver's dome
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Networks:
    triangles: int
    seams: int
    members: int
    rim_edges: int
    shell_m2: float
    plan_m2: float
    radius_m: float
    loop_m: tuple[float, ...]       # each triangle's local loop
    global_m: float                 # every seam
    rim_m: float                    # the base ring
    ring_m: tuple[float, ...]       # horizontal rings at each interior vertex height
    bands: tuple                    # seam_climate's bands
    face_slope_deg: tuple[float, ...]
    face_area_m2: tuple[float, ...]
    face_z_m: tuple[float, ...]     # each face centroid's height above the rim


def _wedge_bark_width_in() -> float:
    """The round face's width: the chord a sector of the log subtends."""
    import seed_model

    r = seed_model.SEED_TRUNK_DIAMETER_IN / 2
    return 2 * r * math.sin(math.pi / seed_model.SEED_RADIAL_SPLITS)


@lru_cache(maxsize=1)
def networks() -> Networks:
    model = cf.reference_model()
    topo = model.topology
    v = np.asarray(topo.vertices, dtype=float) * IN
    r = topo.sphere_radius_in * IN
    inset = _wedge_bark_width_in() / 2 * IN        # hose runs down the middle of the round face
    loops, slopes, areas, zs = [], [], [], []
    for f in topo.faces:
        a, b, c = (v[i] for i in f.vertices)
        la, lb, lc = np.linalg.norm(b - c), np.linalg.norm(c - a), np.linalg.norm(a - b)
        per = la + lb + lc
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        r_in = 2 * area / per
        loops.append(per * (r_in - inset) / r_in)   # the inset triangle is similar
        n = np.cross(b - a, c - a)
        n = n / np.linalg.norm(n)
        if np.dot(n, (a + b + c) / 3) < 0:
            n = -n
        slopes.append(math.degrees(math.acos(max(-1.0, min(1.0, float(n[2]))))))
        areas.append(float(area))
        zs.append(float((a[2] + b[2] + c[2]) / 3))
    seams_m = sum(float(np.linalg.norm(s.end - s.start)) for s in model.seams) * IN
    rim = [e for e in topo.edges.values() if e.is_base]
    rim_m = sum(float(np.linalg.norm(v[e.key[0]] - v[e.key[1]])) for e in rim)
    heights = sorted({round(float(z), 4) for z in v[:, 2]})
    rings = tuple(2 * math.pi * math.sqrt(max(r * r - z * z, 0.0)) for z in heights[1:-1])
    return Networks(len(topo.faces), len(model.seams), 3 * len(topo.faces), len(rim),
                    float(sum(areas)), math.pi * r * r, r, tuple(loops), seams_m, rim_m, rings,
                    scl.rings()["bands"], tuple(slopes), tuple(areas), tuple(zs))


def seam_room() -> dict:
    """Can every layer's global run share the seam's key? The tightest key, by
    channel_facts' own rules: each item must pass the key's round opening, and
    the bundle may fill 40% of the inside."""
    t = min(cf.seam_types(), key=lambda s: s.gap_deg)
    room = cf.room(t)
    out = {"inside_in2": room.inside_in2, "usable_in2": room.usable_in2, "round_in": room.inside_round_in,
           "fill_pct": 100 * cf.K["fill_fraction"],
           "netted": len([l for l in LAYERS if l.kind in ("sheet", "hose")])}
    for name, bore in (("big", C["global_hose_id_mm"]), ("small", C["local_hose_id_mm"])):
        od_in = (bore + 2 * C["hose_wall_mm"]) / 25.4
        area = math.pi * od_in ** 2 / 4
        out[f"{name}_od_in"] = od_in
        out[f"{name}_fit"] = int(room.usable_in2 // area) if od_in <= room.inside_round_in else 0
    return out


def groove() -> dict:
    """What the C-channel takes out of one strut, by numerical integration of
    the wedge's sector section with a rectangular groove at its round face."""
    import seed_model

    r = seed_model.SEED_TRUNK_DIAMETER_IN / 2
    half = math.pi / seed_model.SEED_RADIAL_SPLITS
    w, d = C["groove_w_in"], C["groove_d_in"]
    n = 900
    xs = np.linspace(0, r, n)
    ys = np.linspace(-r * math.sin(half), r * math.sin(half), n)
    X, Y = np.meshgrid(xs, ys)
    cell = (xs[1] - xs[0]) * (ys[1] - ys[0])
    sector = (X * X + Y * Y <= r * r) & (np.abs(np.arctan2(Y, X)) <= half)
    notch = (X * X + Y * Y > (r - d) ** 2) & (np.abs(Y) <= w / 2)

    def props(mask):
        a = mask.sum() * cell
        xc = (X[mask]).sum() * cell / a
        i = ((X[mask] - xc) ** 2).sum() * cell
        c = max(xc, X[mask].max() - xc)
        return a, i / c
    a0, s0 = props(sector)
    a1, s1 = props(sector & ~notch)
    return {"area_in2": a0, "area_loss_pct": 100 * (1 - a1 / a0), "s_loss_pct": 100 * (1 - s1 / s0),
            "bark_w_in": _wedge_bark_width_in(), "groove_area_in2": w * d}


# ----------------------------------------------------------------------
# The stack
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Layer:
    key: str
    label: str
    side: str            # room | core | weather
    medium: str          # air | water | vacuum | heat | fog | co2 | signal | nutrient | metal | foam | board
    modes: tuple         # what it can be set to; 'off' always allowed
    kind: str            # sheet | hose | mesh | cavity | board
    rsi: float
    colour: tuple
    job: str


LAYERS: tuple[Layer, ...] = (
    Layer("thermal", "heating and cooling", "room", "heat", ("off", "heat", "cool"), "sheet",
          C["layer_rsi"], (0.95, 0.42, 0.25, 0.55), "warm or cool water: the wall is the radiator"),
    Layer("air_in", "fresh air in", "room", "air", ("off", "supply", "exhaust"), "sheet",
          C["layer_rsi"], (0.45, 0.92, 0.62, 0.50), "filtered air delivered to the room, low"),
    Layer("fog", "fog out, smoke in", "room", "fog", ("off", "fog", "smoke_exhaust"), "hose",
          0.0, (0.80, 0.80, 0.84, 0.50), "security fog out; in a fire, smoke drawn away"),
    Layer("bus", "signal and power", "room", "signal", ("off", "on"), "hose",
          0.0, (0.35, 0.40, 0.95, 0.50), "the CAN wire: sensors and valves on every triangle"),
    Layer("core", "frame and cavity", "core", "foam", ("off", "inject_foam", "inject_glue"), "cavity",
          0.0, (0.95, 0.85, 0.30, 0.45), "the wedges, the local loops, the insulation"),
    Layer("osb", "hard cover", "weather", "board", ("off",), "board",
          C["osb_rsi"], (0.80, 0.62, 0.38, 0.70),
          "glued to the frame through the local loops: each triangle's outer skin"),
    Layer("water", "water: capture and flood", "weather", "water",
          ("off", "capture", "flood", "circulate", "drain"), "sheet", C["layer_rsi"],
          (0.30, 0.65, 1.00, 0.55),
          "on the OSB, nearest the wood: rain to the tank, the skin wetted at once, "
          "or water run under the sky"),
    Layer("filter", "intake filter", "weather", "air", ("off", "intake"), "sheet",
          C["layer_rsi"], (0.70, 0.95, 0.80, 0.45), "outside air drawn through the media"),
    Layer("vacuum", "vacuum: clamp and ring", "weather", "vacuum", ("off", "clamp", "test"), "sheet",
          C["layer_rsi"], (0.75, 0.45, 0.95, 0.50),
          "weak vacuum holds the skin down; strong vacuum stays in the rim ring's hoses"),
    Layer("cage", "Faraday cage", "weather", "metal", ("off", "on"), "mesh",
          0.0, (0.72, 0.74, 0.78, 0.60), "bonded mesh: lightning and radio"),
    Layer("cap", "the one watertight layer", "weather", "board", ("off",), "board",
          0.0, (0.20, 0.55, 0.85, 0.55), "the shower cap, unbroken"),
    Layer("airbag", "flotation bladders", "weather", "co2", ("off", "inflate"), "sheet",
          0.0, (1.00, 0.70, 0.30, 0.45),
          "folded under a skirt round the lower band, outside the cap; CO2 fills them"),
    Layer("living", "living surface", "weather", "nutrient", ("off", "irrigate", "feed"), "sheet",
          0.0, (0.35, 0.75, 0.30, 0.70), "root barrier, medium, drip and feed: the chia-pet"),
)
LAYER = {layer.key: layer for layer in LAYERS}

#: The order the owner drew it, wood outward, before the temperature argument.
OWNER_STACK = ("water", "air_in", "filter", "vacuum", "cage", "fog", "airbag", "thermal", "osb", "cap",
               "living")

#: Every layer is one piece -- fabric, semi-flexible or hard -- with its channels
#: built in. key: (what it is, how its channels are made, body, thickness mm, kind)
#: The core's depth is the log's radius and the board's is declared above; the
#: rest are typical thicknesses of the products named, declared here.
CONSTRUCTION: dict[str, tuple[str, str, str, float | None, str]] = {
    "thermal": ("capillary mat", "fine tubes woven into a fabric", "fabric", 5.0, "nominal"),
    "air_in": ("textile duct", "sewn air cells, perforated to the room", "fabric", 12.0, "estimate"),
    "fog": ("hose sleeves", "hoses sewn into sleeves", "fabric", 10.0, "estimate"),
    "bus": ("e-textile", "conductive thread and a node per cell", "fabric", 3.0, "estimate"),
    "core": ("frame and foam", "a C-channel in every member, the key in every seam", "hard", None, "geometry"),
    "osb": ("board", "none: glued on through the loops", "hard", None, "nominal"),
    "water": ("twin-wall sheet", "extruded flutes", "hard", 10.0, "nominal"),
    "filter": ("pleated media", "air drawn through the pleats", "semi-flexible", 15.0, "estimate"),
    "vacuum": ("spacer fabric", "a pile that holds the gap open", "semi-flexible", None, "nominal"),
    "cage": ("metal mesh", "woven wire, bonded at every seam", "semi-flexible", 2.0, "estimate"),
    "cap": ("membrane", "none: the one watertight layer", "fabric", 1.5, "nominal"),
    "airbag": ("drop-stitch", "two skins tied by threads, inflated", "fabric", 6.0, "estimate"),
    "living": ("felt pockets", "a drip line sewn into the felt", "fabric", 25.0, "estimate"),
}


def thickness_mm(key: str) -> float:
    """A layer's real thickness: computed where it can be, declared where not."""
    if key == "core":
        return cavity_depth_m() * 1000
    if key == "osb":
        return C["osb_mm"]
    if key == "vacuum":
        return C["layer_gap_mm"]
    return float(CONSTRUCTION[key][3])


def skin() -> dict:
    """How thick the whole cell wall is, inside and outside the frame."""
    room = sum(thickness_mm(l.key) for l in LAYERS if l.side == "room")
    weather = sum(thickness_mm(l.key) for l in LAYERS if l.side == "weather")
    bodies: dict[str, int] = {}
    for key, row in CONSTRUCTION.items():
        bodies[row[2]] = bodies.get(row[2], 0) + 1
    return {"room_mm": room, "weather_mm": weather, "core_mm": thickness_mm("core"),
            "wall_mm": room + weather + thickness_mm("core"), "bodies": bodies}


def cavity_depth_m() -> float:
    """The frame's cavity is as deep as a wedge: the log's radius."""
    import seed_model

    return seed_model.SEED_TRUNK_DIAMETER_IN / 2 * IN


def core_rsi() -> float:
    """The foam-filled cavity's resistance."""
    return cavity_depth_m() / IN * C["foam_r_per_in"] * RSI_PER_RIMP


def profile(stack: tuple[str, ...] | None = None, t_out: float | None = None) -> list[dict]:
    """Steady-state winter temperature at the middle of every layer, room to
    weather, with the foam-filled core as the insulation."""
    t_in = C["room_c"]
    t_out = C["winter_out_c"] if t_out is None else t_out
    order = stack or tuple(l.key for l in LAYERS)
    resist = [("room film", C["film_in_rsi"])]
    for key in order:
        rsi = core_rsi() if key == "core" else LAYER[key].rsi
        resist.append((key, rsi))
    resist.append(("outside film", C["film_out_rsi"]))
    total = sum(r for _k, r in resist)
    q = (t_in - t_out) / total
    out, acc = [], 0.0
    for key, rsi in resist:
        mid = acc + rsi / 2
        out.append({"layer": key, "temp_c": t_in - q * mid, "rsi": rsi})
        acc += rsi
    return out


def heat_split(where: str) -> dict:
    """Of the heat a thermal layer gives, the share that reaches the room: as
    drawn, on the room side of the insulation, or where the owner first put
    it, outside the frame under the OSB."""
    rs = [(p["layer"], p["rsi"]) for p in profile() if p["layer"] != "thermal"]
    keys = [k for k, _r in rs]
    cut = 1 if where == "room" else keys.index("osb")     # the source sits just before this
    to_room = sum(r for _k, r in rs[:cut])
    to_out = sum(r for _k, r in rs[cut:])
    g_room, g_out = 1 / to_room, 1 / to_out
    return {"to_room": g_room / (g_room + g_out), "to_weather": g_out / (g_room + g_out)}


def lower_of(zs) -> tuple[int, ...]:
    """Of faces at these centroid heights, the ones at or below the third of
    the dome's distinct face heights: the lower half of the shell, where the
    bladders go. Shared with the film's scene, so both pick the same faces."""
    levels = sorted(set(round(float(z), 2) for z in zs))
    cut = levels[len(levels) // 3]
    return tuple(i for i, z in enumerate(zs) if round(float(z), 2) <= cut)


def lower_faces() -> tuple[int, ...]:
    return lower_of(networks().face_z_m)


# ----------------------------------------------------------------------
# One check per function
# ----------------------------------------------------------------------

def foam() -> dict:
    """Injection foam into every triangle's cavity, after the OSB is on."""
    n = networks()
    inset = _wedge_bark_width_in() * IN
    vol = 0.0
    for area, loop in zip(n.face_area_m2, n.loop_m):
        # the cavity is the triangle inside the struts: shrink by the strut width
        per = loop
        r_in = 2 * area / per if per else 0
        k = max(0.0, (r_in - inset / 2) / r_in) if r_in else 0
        vol += area * k * k * cavity_depth_m()
    bdft = vol * BDFT_PER_M3
    kits = math.ceil(bdft / C["foam_kit_bdft"])
    return {"m3": vol, "bdft": bdft, "kits": kits, "usd": kits * C["foam_kit_usd"],
            "per_triangle_l": vol / n.triangles * 1000, "r_imperial": cavity_depth_m() / IN * C["foam_r_per_in"],
            "lifts": int(C["foam_lifts"]), "per_lift_l": vol / n.triangles * 1000 / C["foam_lifts"]}


def glue() -> dict:
    """Glue pushed through the local loops: flooding the whole groove, against
    a bead out of a perforated hose."""
    n = networks()
    hose_area = math.pi * ((C["local_hose_id_mm"] / 2 + C["hose_wall_mm"]) / 1000) ** 2
    groove_area = C["groove_w_in"] * C["groove_d_in"] * IN * IN
    fill_m2 = max(groove_area - hose_area, 0.0)
    loops = sum(n.loop_m)
    flood_l = fill_m2 * loops * 1000
    bead_l = C["glue_bead_mm2"] * 1e-6 * loops * 1000
    per = C["glue_cartridge_ml"] / 1000
    return {"flood_l": flood_l, "flood_cartridges": math.ceil(flood_l / per),
            "bead_l": bead_l, "bead_cartridges": math.ceil(bead_l / per), "loop_total_m": loops}


def vacuum() -> dict:
    """Vacuum across a sheet is a load. How much, against the wind and the sheathing,
    and what a hard vacuum -- the kind that insulates -- would ask of a panel."""
    n = networks()
    biggest = max(n.face_area_m2)
    q = 0.5 * C["air_density"] * C["wind_gust_m_s"] ** 2 * C["wind_cp"]
    atm = C["atmosphere_kpa"]
    lift = 1000 / (C["water_density"] * 9.81)                  # metres of water per kPa
    levels = (("rim ring, in hoses", C["hose_vacuum_kpa"]), ("water draw", C["water_vacuum_kpa"]),
              ("sheet clamp", C["sheet_vacuum_kpa"]))
    return {"triangle_m2": biggest,
            "sheet_kn": C["sheet_vacuum_kpa"] * biggest,
            "sheet_kg": C["sheet_vacuum_kpa"] * biggest * 1000 / 9.81,
            "hose_kn": C["hose_vacuum_kpa"] * biggest,
            "hose_tonnes": C["hose_vacuum_kpa"] * biggest / 9.81,
            "wind_kpa": q / 1000, "wind_kn": q / 1000 * biggest,
            "sheet_over_wind": C["sheet_vacuum_kpa"] * 1000 / q,
            "hose_over_design": C["hose_vacuum_kpa"] / C["sheathing_design_kpa"],
            "hard_kn": atm * biggest, "hard_tonnes": atm * biggest / 9.81, "hard_t_per_m2": atm / 9.81,
            "clamp_density_pct": 100 * (atm - C["sheet_vacuum_kpa"]) / atm,
            "levels": tuple((name, kpa, kpa * lift) for name, kpa in levels)}


def rain() -> dict:
    b = borrowed()
    n = networks()
    m3 = n.plan_m2 * b["rain_in_year"] * IN * b["runoff"]
    gal = m3 * 1000 / L_PER_GAL
    return {"gal_year": gal, "gal_day": gal / 365, "tank_gal": b["tank_gal"],
            "tank_fills": gal / b["tank_gal"]}


def frame_mass_kg() -> float:
    import seed_world

    b = borrowed()
    return seed_world.geometry().member_volume_cuft * FT ** 3 * b["pine_kg_m3"] * (1 + b["mc_target"])


def fire() -> dict:
    """Wet the outside first; wet the frame from inside as the last line."""
    import seed_world

    b = borrowed()
    n = networks()
    gpm = C["wetting_gpm_ft2"] * n.shell_m2 / M2_PER_FT2
    dry_kg = seed_world.geometry().member_volume_cuft * FT ** 3 * b["pine_kg_m3"]
    soak_l = dry_kg * (C["fibre_saturation"] - b["mc_target"])
    flow = gpm * L_PER_GAL / 60 / 1000                      # m3/s
    kw = C["water_density"] * 9.81 * flow * C["pump_head_m"] / C["pump_eff"] / 1000
    need_gal = gpm * C["ember_minutes"]
    one = gpm / n.triangles
    return {"gpm": gpm, "tank_min": b["tank_gal"] / gpm, "soak_l": soak_l, "pump_kw": kw,
            "tank_gal": b["tank_gal"], "tank_l": b["tank_gal"] * L_PER_GAL,
            "ember_gal": need_gal, "ember_tanks": need_gal / b["tank_gal"],
            "one_gpm": one, "one_min": b["tank_gal"] / one,
            "soak_share": soak_l / (b["tank_gal"] * L_PER_GAL)}


def air_filter() -> dict:
    """The whole shell as one filter, and the heat the intake air picks up on
    its way through a layer that lies between the core and the cold."""
    b = borrowed()
    n = networks()
    q = b["need_cfm"] * 0.000471947
    v = q / n.shell_m2
    rs = [(p["layer"], p["rsi"]) for p in profile()]
    keys = [k for k, _r in rs]
    i = keys.index("filter")
    r_in = sum(r for _k, r in rs[:i]) + rs[i][1] / 2
    r_out = rs[i][1] / 2 + sum(r for _k, r in rs[i + 1:])
    a, mcp = n.shell_m2, q * C["air_density"] * 1005
    t_in, t_out = C["room_c"], C["winter_out_c"]
    # mcp (T - t_out) = a (t_in - T) / r_in - a (T - t_out) / r_out
    t_layer = (mcp * t_out + a * t_in / r_in + a * t_out / r_out) / (mcp + a / r_in + a / r_out)
    recovered = mcp * (t_layer - t_out)
    wall = a * (t_in - t_out) / sum(r for _k, r in rs)
    return {"face_m_s": v, "face_mm_s": v * 1000, "ratio": C["furnace_face_m_s"] / v,
            "need_cfm": b["need_cfm"], "area_m2": n.shell_m2,
            "warmed_k": t_layer - t_out, "recovered_w": recovered, "wall_loss_w": wall,
            "recovered_share": recovered / wall}


def heating() -> dict:
    """A warm wall: what it delivers, against what the foam-wrapped dome loses."""
    b = borrowed()
    n = networks()
    cap_w = C["radiant_h"] * n.shell_m2 * C["heating_dt_k"]
    dt = C["room_c"] - C["winter_out_c"]
    u = 1 / sum(p["rsi"] for p in profile())
    loss_wall = u * n.shell_m2 * dt
    vent = b["need_cfm"] * 0.000471947 * C["air_density"] * 1005 * dt
    loss = loss_wall + vent
    return {"capacity_w": cap_w, "loss_w": loss, "wall_w": loss_wall, "vent_w": vent,
            "needed_dt_k": loss / (C["radiant_h"] * n.shell_m2), "u": u,
            "room_side": heat_split("room"), "weather_side": heat_split("weather")}


def cooling() -> dict:
    """A cool wall must stay above the room's dew point, with the wood's margin."""
    from . import peltier_ring as pr

    b = borrowed()
    n = networks()
    _k, _l, t_room, rh_room, _t_out, _rh = pr.weather("humid")
    dp = scl.dew_point(t_room, rh_room)
    surface = dp + b["wood_margin_k"]
    dt = max(0.0, t_room - surface)
    return {"room_c": t_room, "rh": rh_room, "dew_c": dp, "surface_c": surface, "dt_k": dt,
            "capacity_w": C["radiant_h"] * n.shell_m2 * dt,
            "peltier_ring_w": pr.ring_day("humid")["cooling_w"]}


def cage() -> dict:
    """A cage passes anything whose half-wavelength fits through its biggest hole."""
    n = networks()
    mesh = C["mesh_aperture_mm"] / 1000
    lam = C_LIGHT / (C["wifi_ghz"] * 1e9)
    longest_seam = max(float(np.linalg.norm(s.end - s.start)) * IN for s in cf.reference_model().seams)
    return {"mesh_cutoff_ghz": C_LIGHT / (2 * mesh) / 1e9,
            "door_cutoff_mhz": C_LIGHT / (2 * C["door_w_m"]) / 1e6,
            "seam_cutoff_mhz": C_LIGHT / (2 * longest_seam) / 1e6,
            "mesh_db_wifi": 20 * math.log10(lam / (2 * mesh)),
            "bond_m": n.global_m, "bond_ft": n.global_m / FT, "seams": n.seams}


def fog() -> dict:
    b = borrowed()
    return {"volume_m3": b["volume_m3"], "seconds": b["volume_m3"] / C["fog_m3_s"]}


@lru_cache(maxsize=1)
def _face_corners() -> tuple:
    """Every face's three corners, metres, z from the sphere's centre (the rim's level)."""
    topo = cf.reference_model().topology
    v = np.asarray(topo.vertices, dtype=float) * IN
    return tuple(np.array([v[i] for i in f.vertices]) for f in topo.faces)


def _area_below(tri: np.ndarray, z: float) -> float:
    pts = []
    for i in range(3):
        p, q = tri[i], tri[(i + 1) % 3]
        if p[2] <= z:
            pts.append(p)
        if (p[2] - z) * (q[2] - z) < 0:
            pts.append(p + (q - p) * (z - p[2]) / (q[2] - p[2]))
    return sum(0.5 * float(np.linalg.norm(np.cross(pts[i] - pts[0], pts[i + 1] - pts[0])))
               for i in range(1, len(pts) - 1))


def flotation() -> dict:
    """What it takes to float the house if the water comes up -- and how high
    the water is when the bladders alone lift it."""
    n = networks()
    shell = n.shell_m2
    mass = (frame_mass_kg() + shell * (C["osb_kg_m2"] + C["cap_kg_m2"])
            + n.plan_m2 * C["floor_kg_m2"])
    need_m3 = mass / C["water_density"]
    low_idx = lower_faces()
    low = [n.face_area_m2[i] for i in low_idx]
    have_m3 = sum(low) * C["airbag_m"]
    mol = 101_325 * need_m3 / (R_GAS * 288.15)
    co2_kg = mol * 0.04401
    # The water's height above the rim when the submerged part of the bladders
    # displaces the house's weight. Below that, the floor is already under water.
    tris = _face_corners()
    rim_z = min(float(t[:, 2].min()) for t in tris)

    def displaced(z: float) -> float:
        return C["airbag_m"] * sum(_area_below(tris[i], rim_z + z) for i in low_idx)
    lo, hi = 0.0, max(float(tris[i][:, 2].max()) for i in low_idx) - rim_z
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if displaced(mid) < need_m3 else (lo, mid)
    return {"mass_kg": mass, "need_m3": need_m3, "lower_m2": sum(low), "have_m3": have_m3,
            "ratio": have_m3 / need_m3, "co2_kg": co2_kg,
            "cylinders": math.ceil(co2_kg / C["co2_cylinder_kg"]),
            "bag_waterline_m": hi,
            # A sealed floor is a hull: every centimetre of draft floats plan_m2 x 1 cm of water.
            "hull_draft_m": need_m3 / n.plan_m2, "floor_kg": n.plan_m2 * C["floor_kg_m2"]}


def living() -> dict:
    """The chia-pet: soil on the faces flat enough to hold it, felt pockets on
    the steep ones, and what all of it weighs wet."""
    n = networks()
    flat = sum(a for a, s in zip(n.face_area_m2, n.face_slope_deg) if s <= C["plant_max_slope_deg"])
    steep = n.shell_m2 - flat
    soil_kg = flat * C["green_kg_m2"]
    felt_kg = steep * C["felt_kg_m2"]
    frame = frame_mass_kg()
    return {"plant_m2": flat, "steep_m2": steep, "plant_pct": 100 * flat / n.shell_m2,
            "soil_kg": soil_kg, "felt_kg": felt_kg, "wet_kg": soil_kg + felt_kg, "frame_kg": frame,
            "times_frame": (soil_kg + felt_kg) / frame,
            "water_l_day": n.shell_m2 * C["green_water_l_m2_day"]}


def extras() -> dict:
    b = borrowed()
    n = networks()
    lv = living()
    layer_m3 = n.shell_m2 * C["layer_gap_mm"] / 1000
    # A sample from the farthest loop: round that loop, then down the seams to the rim.
    reach_m = max(n.loop_m) + scl.rings()["meridian_ft"] * FT / 2
    return {
        "leak_tests": math.ceil(math.log2(n.triangles)),
        "snowmelt_kw": C["snowmelt_w_m2"] * lv["plant_m2"] / 1000,
        "snowmelt_all_kw": C["snowmelt_w_m2"] * n.shell_m2 / 1000,
        "solar_kw": b["peak_solar_w_m2"] * n.shell_m2 * C["sunlit_fraction"] * C["solar_eff"] / 1000,
        "sky_w": b["radiative_w_m2"] * n.shell_m2,
        "fumigate_kg": layer_m3 * C["fumigation_co2"] * C["co2_density"],
        "borate_l": C["borate_l_m2"] * n.shell_m2,
        "layer_m3": layer_m3,
        "sample_m": reach_m, "sample_s": reach_m / C["sample_m_s"],
    }


@lru_cache(maxsize=1)
def _face_graph() -> tuple:
    """Triangles as nodes; a link wherever two share a seam; and the rim edges."""
    topo = cf.reference_model().topology
    owners: dict[tuple, list[int]] = {}
    for i, f in enumerate(topo.faces):
        vs = f.vertices
        for j in range(3):
            owners.setdefault(tuple(sorted((vs[j], vs[(j + 1) % 3]))), []).append(i)
    links = tuple(tuple(v) for v in owners.values() if len(v) == 2)
    rim = tuple(v[0] for v in owners.values() if len(v) == 1)
    return len(topo.faces), links, rim


def _hops(n: int, links, sources) -> dict[int, int]:
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    dist = {s: 0 for s in sources}
    queue = list(sources)
    while queue:
        nxt = []
        for a in queue:
            for b in adj[a]:
                if b not in dist:
                    dist[b] = dist[a] + 1
                    nxt.append(b)
        queue = nxt
    return dist


def local_net() -> dict:
    """Every triangle's gasket ported to its neighbours: three through-holes a
    triangle, one per side. A side on a seam takes a jumper -- through the V
    (the inside seam) or over the ridge (the outside one) -- or a cap. A side on
    the rim ports out to the rim manifold. Jumpered everywhere, the gaskets form
    a network of locals only, separate from the global channel in the key."""
    n, links, rim = _face_graph()
    from_rim = _hops(n, links, sorted(set(rim)))
    every = [max(_hops(n, links, [s]).values()) for s in range(n)]
    # A jumper whose loss would cut the network in two (a bridge, in graph terms).
    cut = 0
    for k in range(len(links)):
        rest = links[:k] + links[k + 1:]
        if len(_hops(n, rest, [0])) < n:
            cut += 1
    return {"triangles": n, "ports": 3 * n, "jumpers": len(links), "rim_ports": len(rim),
            "loops": len(links) - n + 1, "single_points": cut,
            "max_hops_from_rim": max(from_rim.values()), "diameter_hops": max(every),
            "hops": from_rim}


def fire_evap() -> dict:
    """Water metered to the fire's heat instead of a sprinkler's rate: every
    kilogram warmed to boiling and evaporated on the skin, where the heat is."""
    n = networks()
    fi = fire()
    lnet = local_net()
    area = n.shell_m2 * C["fire_side_fraction"]
    load_kw = C["bal_kw_m2"] * area
    per_kg_mj = 4.186 * C["water_warm_k"] / 1000 + C["latent_mj_kg"]
    kg_s = load_kw / 1000 / per_kg_mj
    gpm = kg_s * 60 / L_PER_GAL
    tank_min = fi["tank_l"] / kg_s / 60
    flow_m3_s = kg_s / C["water_density"]
    bore = math.pi * (C["local_hose_id_mm"] / 2000) ** 2
    sprinkler_m3_s = fi["gpm"] * L_PER_GAL / 1000 / 60
    return {"area_m2": area, "load_kw": load_kw, "per_kg_mj": per_kg_mj, "kg_s": kg_s, "gpm": gpm,
            "tank_min": tank_min, "sprinkler_min": fi["tank_min"], "times_longer": tank_min / fi["tank_min"],
            "window_share": tank_min / C["ember_minutes"],
            "pump_w": C["water_density"] * 9.81 * flow_m3_s * C["pump_head_m"] / C["pump_eff"],
            "jumper_m_s": flow_m3_s / lnet["rim_ports"] / bore,
            "jumper_m_s_sprinkler": sprinkler_m3_s / lnet["rim_ports"] / bore}


def vent_dry() -> dict:
    """After a flood or a storm: dry air pushed through the water layer's flutes
    carries the film on the sheathing away. How long it takes."""
    n = networks()
    area = n.shell_m2 * C["fire_side_fraction"]
    water_kg = C["flood_film_mm"] / 1000 * area * C["water_density"]
    w_in = scl.humidity_ratio(C["dry_day_c"], C["dry_day_rh"])
    w_out = scl.humidity_ratio(C["dry_day_c"], C["exit_rh"])
    air_kg_s = C["purge_cfm"] * 0.000471947 * C["air_density"]
    rate = air_kg_s * (w_out - w_in) / 1000
    house_cfm = borrowed()["need_cfm"]
    return {"water_kg": water_kg, "w_in": w_in, "w_out": w_out, "kg_h": rate * 3600,
            "hours": water_kg / rate / 3600,
            "hours_house_air": water_kg / (rate * house_cfm / C["purge_cfm"]) / 3600}


#: What each network can be used for, and when in a house's life. Declared:
#: this is the design, and the film counts it rather than claiming a number.
USES: tuple[tuple[str, str, str], ...] = (
    ("core", "build", "glue each board on from the inside"),
    ("core", "build", "foam each cavity in lifts"),
    ("vacuum", "build", "clamp the board while the glue cures"),
    ("vacuum", "live", "hold the skin down in a gale"),
    ("vacuum", "maintain", "pressure-test a layer for leaks"),
    ("rings", "live", "a central vacuum with an inlet at every rim corner"),
    ("water", "live", "rain to the tank"),
    ("water", "live", "solar-warmed water in summer"),
    ("water", "live", "night-sky cooling into the tank"),
    ("water", "live", "melt snow off the crown"),
    ("water", "protect", "flood the sheathing in a fire"),
    ("water", "maintain", "borate the timber from inside"),
    ("water", "maintain", "dry the sheathing after a storm"),
    ("local_net", "protect", "water only to the cells that are hot"),
    ("local_net", "maintain", "find a leaking triangle in six tests"),
    ("filter", "live", "filtered fresh air from the whole shell"),
    ("filter", "protect", "shut tight against embers and smoke"),
    ("air_in", "live", "fresh air delivered low in the room"),
    ("thermal", "live", "a warm wall in winter"),
    ("thermal", "live", "a cool wall in summer"),
    ("fog", "protect", "security fog"),
    ("fog", "protect", "smoke drawn out in a fire"),
    ("bus", "maintain", "moisture reported from every cell"),
    ("bus", "protect", "heat reported from every cell"),
    ("bus", "maintain", "a smoke sample from every loop"),
    ("cage", "protect", "lightning carried round the people inside"),
    ("cage", "live", "radio kept out"),
    ("airbag", "protect", "float the house in a flood"),
    ("living", "live", "plants watered from inside"),
    ("living", "live", "plants fed from inside"),
    ("global", "live", "water and wire in every seam"),
)


def multipliers() -> dict:
    """Uses per network, by stage of a house's life."""
    nets = sorted({u[0] for u in USES})
    phases = ("build", "live", "protect", "maintain")
    by_phase = {p: sum(1 for u in USES if u[1] == p) for p in phases}
    per = {k: sum(1 for u in USES if u[0] == k) for k in nets}
    return {"uses": len(USES), "networks": len(nets), "per_network": len(USES) / len(nets),
            "by_phase": by_phase, "per": per, "most": max(per, key=per.get)}


def bus() -> dict:
    """The CAN bus: one node per triangle, the trunk laid along the seams."""
    n = networks()
    return {"nodes": n.triangles, "bits": math.ceil(math.log2(n.triangles)), "trunk_m": n.global_m,
            "spare_500k_m": C["can_500k_m"] - n.global_m, "spare_125k_m": C["can_125k_m"] - n.global_m}


# ----------------------------------------------------------------------
# The bus: routes, situations, interlocks
# ----------------------------------------------------------------------

#: Allowed plumbing between layers (source -> sink). Anything else is refused.
ROUTES: tuple[tuple[str, str, str], ...] = (
    ("filter", "air_in", "outside air, filtered, then into the room at the rim gateway"),
    ("water", "tank", "rain from the outside channel, through the rim, into the tank"),
    ("tank", "water", "the tank back into the frame layer: the flood"),
    ("vacuum", "water", "the clamp layer's pump pulls the water layer toward the tank"),
    ("vacuum", "core", "the clamp holds the OSB while injected glue or foam cures"),
    ("fog", "outside", "smoke drawn out of the room in a fire"),
    ("tank", "living", "irrigation and feed for the outer surface"),
    ("co2", "airbag", "cylinders into the bladders"),
    ("tank", "thermal", "stored water into the room-side wall: night-chilled, or sun-warmed"),
)
ROUTE = {(a, b) for a, b, _w in ROUTES}

#: Situations, as modes per layer; layers not named are 'off'.
SCENARIOS: tuple[tuple[str, str, dict], ...] = (
    ("winter", "a winter night", {"thermal": "heat", "air_in": "supply", "filter": "intake",
                                   "water": "drain", "vacuum": "clamp", "bus": "on", "cage": "on"}),
    ("summer", "a humid summer afternoon", {"thermal": "cool", "air_in": "supply", "filter": "intake",
                                             "living": "irrigate", "bus": "on", "cage": "on"}),
    ("night", "the summer night after it", {"water": "circulate", "air_in": "supply", "filter": "intake",
                                             "bus": "on", "cage": "on"}),
    ("rain", "a rainstorm", {"water": "capture", "vacuum": "clamp", "air_in": "supply",
                             "filter": "intake", "bus": "on", "cage": "on"}),
    ("wildfire", "embers on the wind", {"water": "flood", "fog": "smoke_exhaust", "bus": "on",
                                        "cage": "on"}),
    ("intrusion", "somebody breaking in", {"fog": "fog", "bus": "on", "cage": "on"}),
    ("flood", "the water coming up", {"airbag": "inflate", "bus": "on", "water": "drain"}),
    ("build", "building the wall", {"core": "inject_glue", "vacuum": "clamp", "bus": "on"}),
)


def check_scenario(modes: dict, t_out: float | None = None) -> list[str]:
    """Interlocks. Returns the broken rules (empty when the situation is safe)."""
    broken = []
    for key, mode in modes.items():
        if key not in LAYER:
            broken.append(f"no layer {key}")
        elif mode not in LAYER[key].modes:
            broken.append(f"{key} cannot be {mode}")
    on = {k: m for k, m in modes.items() if m != "off"}
    if on.get("fog") == "fog" and on.get("air_in") in ("supply", "exhaust"):
        broken.append("fog with the air layer running pushes it out or dilutes it")
    if on.get("fog") == "fog" and on.get("filter"):
        broken.append("fog must never reach the intake filter")
    if on.get("water") == "flood" and on.get("filter"):
        broken.append("no outside air in during a wildfire: smoke")
    if on.get("water") == "flood" and on.get("vacuum"):
        broken.append("a clamp beside a flooded layer pulls water through any leak")
    if on.get("airbag") == "inflate" and on.get("vacuum"):
        broken.append("the clamp would fight the bladders")
    if on.get("core") and on.get("vacuum") != "clamp":
        broken.append("injected glue or foam needs the clamp on while it cures")
    if t_out is not None and t_out <= 0 and on.get("water") in ("capture", "flood", "circulate"):
        broken.append("the water layer freezes below 0 C outside")
    return broken


def scenario_table() -> str:
    keys = [s[0] for s in SCENARIOS]
    rows = [f"{'layer':<10}" + "".join(f"{k:>11}" for k in keys)]
    for layer in LAYERS:
        if layer.modes == ("off",):
            continue
        rows.append(f"{layer.key:<10}" + "".join(
            f"{dict(s[2]).get(layer.key, '-'):>11}" for s in SCENARIOS))
    return "\n".join(rows)


def complexity() -> dict:
    """Valves and joints: the price of addressability. Two valves per cell (in
    and out), two joints per cell and two per seam run; the bladders cover the
    lower band only."""
    n = networks()
    low = lower_faces()
    lower_seams = next(b.seams for b in n.bands if b.key == "lower")
    netted = [l for l in LAYERS if l.kind in ("sheet", "hose")]
    cells = joints = by_band = 0
    for l in netted:
        part = l.key == "airbag"
        faces = len(low) if part else n.triangles
        cells += faces
        joints += 2 * faces + 2 * (lower_seams if part else n.seams)
        by_band += 2 * (1 if part else len(n.bands))
    return {"layers": len(LAYERS), "netted": len(netted), "cells": cells,
            "valves_every_cell": cells * 2, "valves_by_band": by_band,
            "joints": joints, "bands": len(n.bands), "lower_faces": len(low)}


def constants_table() -> str:
    width = max(len(n) for n, *_ in CONSTANTS)
    return "\n".join(f"{n:<{width}}  {v:>8g} {u:<14} {k:<10} {w}" for n, v, u, k, w in CONSTANTS)


def validate_cell_wall() -> None:
    n = networks()
    assert n.triangles == 40 and n.seams == 55 and n.members == 120, (n.triangles, n.seams)
    assert all(0 < loop < 3 * 2.5 for loop in n.loop_m)
    g = groove()
    assert 0 < g["area_loss_pct"] < 10 and g["s_loss_pct"] > g["area_loss_pct"]
    prof = {p["layer"]: p["temp_c"] for p in profile()}
    assert prof["thermal"] > 15 and prof["water"] < 0, "the insulation splits the stack"
    h = heating()
    assert h["room_side"]["to_room"] > 0.9 > h["weather_side"]["to_room"]
    assert h["capacity_w"] > h["loss_w"], "a lukewarm wall covers the loss"
    v = vacuum()
    assert C["sheet_vacuum_kpa"] <= C["sheathing_design_kpa"] and v["hose_over_design"] > 5
    assert v["sheet_over_wind"] > 1, "the clamp beats the design gust's suction"
    assert v["clamp_density_pct"] > 98, "the film says a clamp-strength vacuum does not insulate"
    assert v["hard_tonnes"] > 10 * v["hose_tonnes"] / 3
    fi = fire()
    assert fi["tank_min"] < 10 < fi["one_min"], "two minutes for all forty, over an hour for one"
    assert fi["ember_tanks"] > 10 and fi["soak_share"] < 0.5
    af = air_filter()
    assert af["recovered_share"] < 0.05, "the film says the intake air recovers almost nothing"
    assert af["ratio"] > 1000
    assert 0 < bus()["spare_500k_m"] < 10 < bus()["spare_125k_m"], "fits at 500k only just"
    sr = seam_room()
    assert sr["big_fit"] < sr["netted"] <= sr["small_fit"], \
        "the film says 1 in runs cannot all share a seam, 3/8 in runs can"
    ln = local_net()
    assert ln["jumpers"] == n.seams and ln["ports"] == 3 * n.triangles and ln["rim_ports"] == n.rim_edges
    assert ln["ports"] == 2 * ln["jumpers"] + ln["rim_ports"], "every port is a jumper end or a rim port"
    assert ln["loops"] == n.seams - n.triangles + 1 and ln["single_points"] == 0, \
        "the film says no one jumper can cut the network"
    fe = fire_evap()
    assert fe["times_longer"] > 5 and fe["window_share"] > 0.7, "metered water nearly covers the ember window"
    assert fe["jumper_m_s"] < 1.0 < fe["jumper_m_s_sprinkler"], "a jumper carries metered water, not a deluge"
    assert C["bal_kw_m2"] < C["flame_zone_kw_m2"]
    vd = vent_dry()
    assert 0 < vd["hours"] < vd["hours_house_air"]
    mu = multipliers()
    assert mu["per_network"] > 2 and all(mu["by_phase"].values())
    assert set(CONSTRUCTION) == set(LAYER), "every layer says what it is made of"
    assert skin()["weather_mm"] > 0 and skin()["room_mm"] > 0
    assert extras()["sample_s"] < C["sample_limit_s"]
    fl = flotation()
    assert 1 < fl["ratio"] < 1.5, "the film says the bladders float it, but only just"
    assert fl["hull_draft_m"] < 0.5, "the film says a sealed floor floats it in a hand's depth"
    assert fl["bag_waterline_m"] > 2 * fl["hull_draft_m"], "the film says the floor floods before the bladders lift"
    lv = living()
    assert lv["plant_pct"] < 25 and lv["times_frame"] > 1, "the film says soil fits the crown only, and outweighs the frame"
    gl = glue()
    assert gl["flood_cartridges"] > 5 * gl["bead_cartridges"]
    assert cooling()["capacity_w"] > cooling()["peltier_ring_w"]
    for key, _label, modes in SCENARIOS:
        broken = check_scenario(modes, C["winter_out_c"] if key == "winter" else None)
        assert not broken, (key, broken)
    assert check_scenario({"fog": "fog", "air_in": "supply"}), "the interlock must catch fog + air"
    assert check_scenario({"airbag": "inflate", "vacuum": "clamp"})
    assert check_scenario({"water": "capture"}, t_out=-5)
    assert check_scenario({"water": "circulate"}, t_out=-5)
    assert check_scenario({"water": "flood", "vacuum": "clamp"})
    for a, b, _w in ROUTES:
        assert a in LAYER or a in ("tank", "co2"), a
        assert b in LAYER or b in ("tank", "outside"), b
    for key, _label, modes in SCENARIOS:
        assert modes.get("bus") == "on", "the bus is always on"
    # The physical order: room-side services, the core, then the weather side.
    sides = [l.side for l in LAYERS]
    assert sides == sorted(sides, key=("room", "core", "weather").index)
    assert [l.key for l in LAYERS].index("osb") == [l.key for l in LAYERS].index("core") + 1, \
        "the OSB is glued straight onto the frame"


if __name__ == "__main__":
    validate_cell_wall()
    n = networks()
    print("triangles", n.triangles, "seams", n.seams, "shell m2", round(n.shell_m2, 1),
          "loops m", round(sum(n.loop_m), 1), "global m", round(n.global_m, 1), "rim m", round(n.rim_m, 2),
          "rings m", [round(r, 2) for r in n.ring_m])
    for fn in (groove, foam, glue, vacuum, rain, fire, air_filter, heating, cooling, cage, fog,
               flotation, living, extras, bus, seam_room, complexity, fire_evap, vent_dry, skin):
        print(fn.__name__, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in fn().items()
                            if not isinstance(v, dict)})
    for p in profile():
        print(f"  {p['layer']:<13} {p['temp_c']:7.1f} C")
    print(scenario_table())
