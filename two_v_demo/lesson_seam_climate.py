"""Which Way the Seam Breathes: the channel as the dome's climate system.

The owner's design, worked through in the Cabin World: a seam channel with
air going in and out, through a desiccant or past it, with a Peltier plate
on each skin -- and the questions that came with it. Which line is it that
runs from the centre outward? Will a channel far colder than the wood take
the water instead of the wood? What switches the air through the cartridge,
and where should the cartridge live: one place, packed along a seam, round a
ring, or over the top like a rainbow? What do the dome's four levels each do?

Every figure comes from :mod:`two_v_demo.seam_climate` (psychrometrics, the
controller, the bands, the bed physics), which reads the raw-wedge solver
through :mod:`two_v_demo.channel_facts`. The ten weathers are estimates and
are put on screen, marked as such, before the controller is run on them.

    py -3.12 -m rerender stills cabin_seam_climate
    py -3.12 -m rerender render cabin_seam_climate
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_world as cw
from . import channel_facts as cf
from . import channel_scene as sc
from . import seam_climate as scl
from . import shots
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)

COLD = (0.35, 0.72, 1.00, 1.0)
HOT = (1.00, 0.42, 0.25, 1.0)
DRY = (0.45, 0.92, 0.62, 0.9)
WET = (0.40, 0.70, 1.00, 0.9)
SIEVE = (0.92, 0.88, 0.70, 1.0)
BAND_COLOUR = {"lower": (0.30, 0.85, 1.00, 1.0), "belt": (0.45, 0.92, 0.62, 1.0),
               "upper": (0.95, 0.80, 0.35, 1.0), "pentagon": (1.00, 0.40, 0.30, 1.0),
               "cap": (0.85, 0.60, 1.00, 1.0)}


# ----------------------------------------------------------------------
# Every number the film states
# ----------------------------------------------------------------------

NUMBER_WORDS = {n: w for n, w in enumerate(
    "Zero One Two Three Four Five Six Seven Eight Nine Ten".split())}


def deg(x: float, places: int = 0) -> str:
    """A temperature as the narrator should say it."""
    text = f"{abs(x):.{places}f}"
    return f"minus {text}" if x < 0 and float(text) != 0 else text


def _facts() -> dict:
    r = scl.rings()
    bands = {b.key: b for b in r["bands"]}
    b = scl.beds()
    g = scl.regeneration()
    c = scl.cold_channel()
    cold_dry = next(s for s in scl.SCENARIOS if s.key == "cold_dry").sensors
    decisions = [(s, scl.decide(s.sensors)) for s in scl.SCENARIOS]
    levels = r["levels"]
    return {
        "seams": sum(x.seams for x in r["bands"]), "bands": bands, "levels": levels,
        "counts": [r["counts"][lv] for lv in levels],
        "rim_ports": r["rim_ports"], "belt_lows": r["belt_low_points"],
        "meridian": r["meridian_ft"], "stack": scl.stack_pa(10.0),
        "barrier": _barrier_pa(),
        "cd_t_out": cold_dry.t_out, "cd_rh_out": cold_dry.rh_out * 100,
        "cd_t_in": cold_dry.t_in, "cd_rh_in": cold_dry.rh_in * 100,
        "cd_dp_out": scl.dew_point(cold_dry.t_out, cold_dry.rh_out),
        "cd_dp_in": scl.dew_point(cold_dry.t_in, cold_dry.rh_in),
        "cd_w_out": scl.humidity_ratio(cold_dry.t_out, cold_dry.rh_out),
        "cd_w_in": scl.humidity_ratio(cold_dry.t_in, cold_dry.rh_in),
        "c": c, "b": b, "g": g, "decisions": decisions,
        "margin": scl.C["wood_margin_k"], "below": scl.C["plate_below_dp_k"],
        "frost": scl.C["frost_floor_c"], "approach": scl.C["plate_approach_k"],
        "fan": scl.C["fan_static_pa"], "mc_wet": scl.C["mc_wet"] * 100,
        "mc_target": scl.C["mc_target"] * 100,
        "face_cm": scl.C["drawer_face_m"] * 100, "depth_cm": scl.C["drawer_depth_m"] * 100,
        "stove_kw": scl.C["stove_exchanger_kw"],
    }


def _barrier_pa() -> float:
    from wedge_book import systems

    return systems.declared("barrier_pressure_pa")


F = _facts()


def _vent_facts() -> dict:
    """The breathing cap, from :mod:`two_v_demo.seam_vent` -- the same values
    the wedge book's chapter prints."""
    from . import seam_vent as sv

    rows = {r["weather"]: r for r in sv.weather_table()}
    route = sv.descending_seams()
    cap = sv.capacity()
    return {"route": route, "cap": cap, "rows": rows, "freeze": sv.freeze_limit(),
            "need": sv.need_cfm(), "fan": scl.C["fan_static_pa"]}


V = _vent_facts()


def _label(app, point, text, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


# ----------------------------------------------------------------------
# The dome's seams, by band, in the Cabin World
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def band_seams(band: str, lift_in: float = 6.0) -> tuple:
    """(low end, high end) of every seam in a band, lifted clear of the members."""
    model, scale, shift = sc._world()
    out = []
    for seam in scl.classify(model)[band]:
        mid = (seam.apex_start + seam.apex_end) / 2
        lift = mid / np.linalg.norm(mid) * lift_in
        a = (seam.apex_start + lift) * scale + shift
        b = (seam.apex_end + lift) * scale + shift
        out.append((a, b) if a[2] <= b[2] else (b, a))
    return tuple(out)


@lru_cache(maxsize=None)
def _band_batch(band: str) -> TriangleBatch:
    batch = TriangleBatch()
    for a, b in band_seams(band):
        batch.cylinder(a, b, 0.035, BAND_COLOUR[band], 8)
    return batch


def paint_bands(app, bands=tuple(scl.BAND_LABELS)) -> None:
    for band in bands:
        app.static_layer(f"climate:{band}", lambda b=band: _band_batch(b))


def flow(opaque, seams, p: float, colour, up: bool = True, count: int = 3,
         size: float = 0.20) -> None:
    """Air moving along seams: cones travelling up or down each one."""
    for a, b in seams:
        start, end = (a, b) if up else (b, a)
        d = end - start
        n = d / (np.linalg.norm(d) + 1e-9)
        for k in range(count):
            c = start + d * ((k / count + p * 0.9) % 1.0)
            opaque.cone(c, c + n * size, size * 0.4, colour, 10)


def rim_points() -> list[np.ndarray]:
    return [v["point"] for v in sc.vertices() if v["rim"]]


def belt_lows() -> list[np.ndarray]:
    """The five low corners of the zigzag belt, where it drains."""
    pts = [v["point"] for v in sc.vertices() if not v["rim"]]
    z = sorted({round(float(p[2]), 3) for p in pts})
    return [p for p in pts if round(float(p[2]), 3) == z[0]]


def near_dome(points, k: int = 1) -> list[np.ndarray]:
    """The points that face the hero camera."""
    hero = np.array(cw.HERO_EYE)
    return sorted(points, key=lambda q: np.linalg.norm(q - hero))[:k]


# ----------------------------------------------------------------------
# The bench: one seam in section, a plate on each skin
# ----------------------------------------------------------------------

def _bench(app, transparent, bundle=False):
    cw.paint(app, subject=False)
    frame = sc.paint_bench(app, "a", bundle=bundle, bolted=False)
    sc.key_shell(transparent, frame, sc.tight(), 0.0)
    return frame


def plates(opaque, frame, p: float, outer_cold: bool, inner_cold: bool) -> dict:
    """A Peltier on each skin: the outer at the ridge, the inner at the room side.

    Each is drawn as its cold face on the channel side (blue) or its hot face
    (red), with a stack of small arrows showing which way it moves heat."""
    t = sc.tight()
    poly = sc.inner(t)
    top, bottom = max(q[1] for q in poly), min(q[1] for q in poly)
    # At the end face the camera looks into, spanning the channel's width there.
    mid = 0.05
    where = {}
    for name, y, cold, out_dir in (("outer", top - 0.12, outer_cold, 1.0),
                                   ("inner", bottom + 0.12, inner_cold, -1.0)):
        width = 2.0 * sc.half_width(poly, y) * sc.M * 0.9
        centre = frame.at(0.0, y, mid)
        opaque.box(centre, (max(width, 0.012), 0.10, 0.006), COLD if cold else HOT)
        # Heat goes away from the channel when the channel face is cold.
        sign = out_dir if cold else -out_dir
        for k in range(3):
            base = frame.at(0.0, y + sign * (0.3 + 0.9 * ((k / 3 + p) % 1.0)), 0.0) + [0, -0.01, 0]
            opaque.cone(base, base + np.array([0.0, 0.0, sign * 0.014]), 0.007, HOT, 8)
        where[name] = centre
    return where


def cartridge_bypass(opaque, frame, p: float, through: bool) -> dict:
    """The gate at the end of the specimen: a drawer of beads and a bypass."""
    t = sc.tight()
    poly = sc.inner(t)
    bottom = min(q[1] for q in poly)
    end = frame.at(0.0, (bottom + max(q[1] for q in poly)) / 2, sc.SPECIMEN_LEN + 0.02)
    gate = end + np.array([0.0, 0.05, 0.0])
    opaque.box(gate, (0.07, 0.05, 0.07), (0.95, 0.60, 0.15, 1.0))
    drawer = gate + np.array([0.0, 0.10, -0.10])
    bypass = gate + np.array([0.0, 0.18, 0.02])
    opaque.box(drawer, (0.12, 0.08, 0.06), SIEVE)
    rng = np.random.default_rng(3)
    for _ in range(40):
        opaque.sphere(drawer + rng.uniform(-1, 1, 3) * [0.05, 0.03, 0.022], 0.006,
                      (0.80, 0.74, 0.55, 1.0), 3, 6)
    opaque.cylinder(gate, drawer, 0.010, (0.95, 0.60, 0.15, 1.0), 8)
    opaque.cylinder(gate, bypass, 0.010, (0.95, 0.60, 0.15, 1.0), 8)
    path = (gate, drawer) if through else (gate, bypass)
    d = path[1] - path[0]
    for k in range(3):
        c = path[0] + d * ((k / 3 + p) % 1.0)
        opaque.cone(c, c + d / np.linalg.norm(d) * 0.03, 0.012, DRY, 10)
    return {"gate": gate, "drawer": drawer, "bypass": bypass}


# ----------------------------------------------------------------------
# Painters
# ----------------------------------------------------------------------

def p_breathe(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app)
    flow(opaque, band_seams("lower")[:6], p, DRY, up=True)
    flow(opaque, band_seams("upper")[:4], p, DRY, up=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"{F['seams']} SEAMS, ONE CHANNEL", AMBER)


def p_radial(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    w = plates(opaque, frame, p, outer_cold=False, inner_cold=True)
    _label(app, w["outer"] + [0, 0, 0.09], "OUTER SKIN: THE RIDGE", RED)
    _label(app, w["inner"] + [0, 0, -0.08], "INNER SKIN: THE ROOM SIDE", BLUE)
    _label(app, frame.at(0, 1.2, 0), "RADIAL: CENTRE OUTWARD", AMBER)


def p_pump(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    winter = p < 0.5
    w = plates(opaque, frame, p, outer_cold=winter, inner_cold=not winter)
    _label(app, frame.at(0, 1.2, 0), "WINTER: HEAT TO THE ROOM" if winter
           else "SUMMER: HEAT OUTSIDE", AMBER)


def p_dewpoint(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], f"OUTSIDE {deg(F['cd_t_out'])} C, {F['cd_rh_out']:.0f}%: "
           f"DEW {deg(F['cd_dp_out'], 1)} C", BLUE)
    _label(app, m.apex + [0, 0, 0.5], f"INSIDE {F['cd_t_in']:.0f} C, {F['cd_rh_in']:.0f}%: "
           f"DEW {deg(F['cd_dp_in'], 1)} C", AMBER)


def p_condense(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    w = plates(opaque, frame, p, outer_cold=False, inner_cold=True)
    rng = np.random.default_rng(5)
    for k in range(int(6 + 10 * p)):
        drop = w["inner"] + [rng.uniform(-0.013, 0.013), rng.uniform(-0.04, 0.04), -0.006]
        opaque.sphere(drop, 0.003, WET, 3, 6)
    _label(app, frame.at(0, 1.2, 0), "DEW POINT ABOVE SURFACE: WATER", BLUE)


def p_owner(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    w = plates(opaque, frame, p, outer_cold=False, inner_cold=True)
    c = F["c"]
    rng = np.random.default_rng(9)
    for _ in range(30):     # frost on the plate the owner asked about
        opaque.box(w["inner"] + [rng.uniform(-0.015, 0.015), rng.uniform(-0.045, 0.045), -0.004],
                   (0.004, 0.004, 0.004), (0.95, 0.97, 1.0, 1.0))
    _label(app, frame.at(0, 1.2, 0), f"PLATE AT {deg(c['owners_plate'], 1)} C: FROST", RED)


def p_order(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    plates(opaque, frame, p, outer_cold=False, inner_cold=True)
    sc.air_arrows(opaque, frame, sc.tight(), 0.0, p, keys=("drain",))
    c = F["c"]
    _label(app, frame.at(0, 1.2, 0), "PLATE FIRST, WOOD SECOND", GREEN)
    _label(app, frame.at(3.4, -5.4, 0), f"AIR LEAVES AT DEW {c['dp_after']:.1f} C", BLUE)


def p_modes(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower", "upper", "pentagon"))
    flow(opaque, band_seams("lower")[:5], p, DRY, up=True)
    flow(opaque, band_seams("upper")[:4], p, WET, up=False)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"{len(scl.ACTIVE_MODES)} MODES, ONE CHANNEL", AMBER)


def p_weathers(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "THE WEATHERS WE ASSUMED", AMBER)


def p_choices(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "WHAT THE CONTROLLER CHOSE", GREEN)


def p_loop(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower", "belt"))
    seams = band_seams("lower")[:4]
    flow(opaque, seams[:2], p, DRY, up=True)
    flow(opaque, seams[2:], p, WET, up=False)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "FRAME LOOP: SEAM -> DESICCANT -> SEAM", GREEN)
    _label(app, m.apex + [0, 0, 0.35], "PURGE: OUTSIDE -> SEAM -> OUTSIDE", BLUE)


def p_levels(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app)
    m = cw.landmarks()
    for band, z in (("lower", 0.95), ("belt", 0.75), ("upper", 0.55), ("pentagon", 0.35), ("cap", 0.15)):
        b = F["bands"][band]
        _label(app, m.apex + [0, 0, z + 0.2], f"{b.label.upper()}: {b.seams}",
               tuple(int(c * 255) for c in BAND_COLOUR[band][:3]))


def p_pentagon(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("pentagon", "belt"))
    for q in belt_lows():
        opaque.sphere(q + [0, 0, -0.05], 0.09, WET, 5, 10)
    m = cw.landmarks()
    top = band_seams("pentagon")[0]
    _label(app, (top[0] + top[1]) / 2 + [0, 0, 0.35], "DEAD LEVEL: AIR ONLY", RED)
    _label(app, near_dome(belt_lows())[0] + [0, 0, 0.4], f"{F['belt_lows']} LOW POINTS: DRAINS", BLUE)


def p_rim(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower",))
    for q in rim_points():
        opaque.box(q + [0, 0, 0.06], (0.16, 0.16, 0.10), COLD)
    flow(opaque, band_seams("lower"), p, WET, up=False, count=2, size=0.16)
    _label(app, near_dome(rim_points())[0] + [0, 0, 0.45], f"{F['rim_ports']} RIM PORTS", AMBER)


def p_stack(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower", "pentagon", "cap"))
    flow(opaque, band_seams("lower")[:6], p, DRY, up=True)
    flow(opaque, band_seams("cap"), p, HOT, up=True)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"STACK {F['stack']:.1f} PA vs FAN {F['barrier']:.0f} PA", AMBER)


def p_packed(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    poly = sc.inner(sc.tight())
    rng = np.random.default_rng(1)
    ys = [q[1] for q in poly]
    for _ in range(int(80 + 260 * min(1.0, p * 1.5))):
        y = rng.uniform(min(ys) + 0.2, max(ys) - 0.2)
        x = rng.uniform(-1, 1) * max(0.0, sc.half_width(poly, y) - 0.15)
        opaque.sphere(frame.at(x, y, rng.uniform(0.02, sc.SPECIMEN_LEN - 0.02)), 0.0035,
                      (0.80, 0.74, 0.55, 1.0), 3, 6)
    _label(app, frame.at(0, 1.2, 0), f"{F['b'].seam_drop_pa:,.0f} PA", RED)


def p_regen(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    _label(app, frame.at(0, 1.2, 0), f"SIEVE {F['g']['sieve_c']:.0f} C > SEAM {F['g']['seam_max_c']:.0f} C", RED)


def p_drawer(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    w = cartridge_bypass(opaque, frame, p, through=p < 0.55)
    _label(app, w["drawer"] + [0, 0, -0.07], f"{F['b'].drawer_sieve_kg:.1f} KG BEADS", AMBER)
    _label(app, w["bypass"] + [0, 0, 0.06], "BYPASS: SPRING RETURN", GREEN)


def p_honest(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower", "belt", "upper"))
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"{F['b'].frame_water_kg:.0f} KG OF WATER", BLUE)
    _label(app, m.apex + [0, 0, 0.35], f"= {F['b'].drawers_for_frame:.0f} DRAWER FILLS", RED)


def p_stove(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    base = m.dome_centre + np.array([-0.9, -0.6, 0.0])
    opaque.box(base + [0, 0, 0.35], (0.5, 0.45, 0.7), (0.15, 0.15, 0.16, 1.0))
    opaque.cylinder(base + [0, 0, 0.7], m.apex + [-0.9, -0.6, 0.6], 0.07, (0.25, 0.25, 0.27, 1.0), 12)
    ex = base + [0, 0, 1.5]
    opaque.box(ex, (0.28, 0.28, 0.40), (0.72, 0.74, 0.78, 1.0))
    for k in range(4):
        c = ex + [0.2 + 0.25 * ((k / 4 + p) % 1.0), 0.0, 0.0]
        opaque.cone(c, c + [0.09, 0, 0], 0.035, HOT, 10)
    _label(app, ex + [0, 0, 0.45], f"CLEAN AIR, UNDER {F['g']['seam_max_c']:.0f} C", AMBER)
    _label(app, base + [0, 0, 0.95], "FLUE SEALED AWAY", RED)


def p_plan(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app)
    for q in rim_points():
        opaque.box(q + [0, 0, 0.06], (0.16, 0.16, 0.10), COLD)
    for q in belt_lows():
        opaque.sphere(q + [0, 0, -0.05], 0.08, WET, 5, 10)
    flow(opaque, band_seams("pentagon"), p, HOT, up=True, count=2)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "THE LAYOUT", AMBER)


def p_close(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "DEW POINT DECIDES", AMBER)


EXHAUST = (0.95, 0.55, 0.15, 1.0)
FRESH = (0.35, 0.85, 0.45, 1.0)


def _falling(opaque, p: float, colour=None, count: int = 2) -> None:
    """Exhaust going down every falling band: cap, upper band, lower band."""
    for band in ("cap", "upper", "lower"):
        flow(opaque, band_seams(band), p, colour or EXHAUST, up=False, count=count, size=0.30)


def _grille(opaque) -> np.ndarray:
    m = cw.landmarks()
    g = m.apex - np.array([0.0, 0.0, 0.45])
    opaque.disc(g, 0.22, (0.15, 0.15, 0.17, 1.0), 20)
    return g


def _ports(opaque, p: float, fresh_every: int = 2) -> None:
    """A port at every rim corner, outside and below the cap's edge, facing the
    ground: stale air leaving down, and on every other one fresh air coming in."""
    m = cw.landmarks()
    for i, q in enumerate(rim_points()):
        out = np.array([q[0] - m.dome_centre[0], q[1] - m.dome_centre[1], 0.0])
        out /= np.linalg.norm(out) + 1e-9
        # Above the deck, just outside the base ring, mouth facing the deck.
        port = q + out * 0.22 + np.array([0.0, 0.0, 0.55])
        opaque.box(port, (0.22, 0.22, 0.14), (0.30, 0.30, 0.33, 1.0))
        fresh = (i % fresh_every == 1)
        for k in range(2):
            t = (k / 2 + p) % 1.0
            if fresh:
                c = port - np.array([0.0, 0.0, 0.50 - 0.40 * t])
                opaque.cone(c, c + np.array([0.0, 0.0, 0.18]), 0.08, FRESH, 10)
            else:
                c = port - np.array([0.0, 0.0, 0.10 + 0.40 * t])
                opaque.cone(c, c - np.array([0.0, 0.0, 0.18]), 0.08, EXHAUST, 10)


def _room_rising(opaque, p: float) -> None:
    m = cw.landmarks()
    base = m.dome_centre + np.array([0.0, 0.0, 0.4])
    top = m.apex - np.array([0.0, 0.0, 0.6])
    d = top - base
    for k in range(4):
        c = base + d * ((k / 4 + p) % 1.0)
        opaque.cone(c, c + np.array([0.0, 0.0, 0.32]), 0.13, HOT, 12)


def p_correction(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("cap",))
    flow(opaque, band_seams("cap"), p, RED, up=True, count=2, size=0.30)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], "CORRECTION: NO VENT AT THE APEX", RED)
    _label(app, m.apex + [0, 0, 0.5], "A VENT THERE IS A HOLE IN THE CAP", WHITE)


def p_crown(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("cap", "upper", "lower"))
    g = _grille(opaque)
    _room_rising(opaque, p)
    flow(opaque, band_seams("cap"), p, EXHAUST, up=False, count=3, size=0.30)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], f"HOLES IN THE CAP: {V['route'].cap_penetrations}", GREEN)
    _label(app, g - [0, 0, 0.35], "CROWN GRILLE, UNDER THE CAP", AMBER)


def p_down(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("cap", "upper", "lower"))
    _falling(opaque, p)
    _ports(opaque, p, fresh_every=10 ** 6)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], f"{V['route'].seams_down} SEAMS FALL APEX TO RIM", AMBER)
    _label(app, near_dome(rim_points())[0] + [0, 0, -0.55], "OUT AT THE RIM, FACING THE GROUND", WHITE)


def p_siphon(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("cap", "upper", "lower"))
    _room_rising(opaque, p)
    _falling(opaque, p, (0.45, 0.70, 1.0, 1.0))
    m = cw.landmarks()
    w = V["rows"]["winter"]
    _label(app, m.apex + [0, 0, 0.85], f"WINTER: {w['drive_pa']:.1f} PA, {100 * w['share']:.0f}% OF THE NEED, NO FAN",
           BLUE)
    _label(app, m.apex + [0, 0, 0.5], "WARM AIR RISES IN THE ROOM; COOLED AIR FALLS IN THE SEAMS", WHITE)


def p_water(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower",))
    flow(opaque, band_seams("lower"), p, WET, up=False, count=3, size=0.30)
    _ports(opaque, p, fresh_every=10 ** 6)
    m = cw.landmarks()
    for q in rim_points():
        out = np.array([q[0] - m.dome_centre[0], q[1] - m.dome_centre[1], 0.0])
        out /= np.linalg.norm(out) + 1e-9
        for k in range(3):
            opaque.sphere(q + out * 0.22 + np.array([0.0, 0.0, 0.42 - 0.40 * ((k / 3 + p) % 1.0)]),
                          0.045, WET, 4, 8)
    _label(app, near_dome(rim_points())[0] + [0, 0, 0.6], "THE WATER LEAVES BY THE SAME DOOR", BLUE)


def p_twoway(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("cap", "upper", "lower"))
    _room_rising(opaque, p)
    _falling(opaque, p, count=1)
    _ports(opaque, p, fresh_every=2)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], "FRESH IN LOW, STALE OUT HIGH", GREEN)
    _label(app, m.apex + [0, 0, 0.5], "BOTH DOORS AT THE BOTTOM, FACING DOWN", WHITE)


def p_limits(app, opaque, transparent, p):
    cw.paint(app)
    paint_bands(app, ("lower",))
    _ports(opaque, p, fresh_every=10 ** 6)
    _label(app, near_dome(rim_points())[0] + [0, 0, 0.6], f"OUTLETS ICE BELOW {V['freeze']:.0f} C", BLUE)
    _label(app, near_dome(rim_points())[0] + [0, 0, 0.3], "KEEP PORTS ABOVE THE SNOW; SCREEN THEM", WHITE)


# ----------------------------------------------------------------------
# Ten Peltier modules at the rim, and the power to run them
# ----------------------------------------------------------------------

def _ring_facts() -> dict:
    """The owner's ten TEC1-12706s, from :mod:`two_v_demo.peltier_ring` -- the
    same values the wedge book's chapter prints."""
    from . import peltier_ring as pr

    f = pr.facts()
    room = pr.weather("humid")
    dp = scl.dew_point(room[2], room[3])
    return {**f, "C": pr.C, "room": room, "dp": dp, "setpoint": scl.plate_setpoint(dp),
            "rows": pr.voltage_table("humid"), "sun_hours": pr._borrowed("sun_hours_per_day")}


R = _ring_facts()
SINK = (0.78, 0.80, 0.84, 1.0)


def _stations(opaque, p: float, strength: float = 1.0, wet: bool = True,
              hot_inside: bool = False) -> None:
    """A module at every rim corner: cold plate facing the room (blue), finned
    hot sink facing out (red), room air drawn onto the plate, heat thrown out,
    and condensate running down to the port."""
    m = cw.landmarks()
    for q in rim_points():
        out = np.array([q[0] - m.dome_centre[0], q[1] - m.dome_centre[1], 0.0])
        out /= np.linalg.norm(out) + 1e-9
        body = q + np.array([0.0, 0.0, 0.45])
        cold = body - out * 0.20
        hot = body + out * 0.24
        opaque.box(body, (0.16, 0.16, 0.16), (0.25, 0.25, 0.28, 1.0))
        opaque.box(cold, (0.26, 0.26, 0.26), COLD)
        opaque.box(hot, (0.30, 0.30, 0.30), SINK)
        for k in range(4):                                   # fins
            opaque.box(hot + out * 0.17 + np.array([0.0, 0.0, -0.12 + 0.08 * k]),
                       (0.05, 0.05, 0.05), HOT)
        if strength <= 0:
            continue
        size = 0.10 + 0.14 * strength
        heat_dir = -out if hot_inside else out
        heat_from = cold if hot_inside else hot
        for k in range(2):
            t = (k / 2 + p) % 1.0
            a = body - out * (1.10 - 0.70 * t)               # room air onto the plate
            opaque.cone(a, a + out * size, size * 0.45, COLD, 10)
            h = heat_from + heat_dir * (0.30 + 0.70 * t) + np.array([0.0, 0.0, 0.10])
            opaque.cone(h, h + heat_dir * size, size * 0.45, HOT, 10)
        if wet:
            for k in range(3):
                opaque.sphere(cold + np.array([0.0, 0.0, -0.18 - 0.30 * ((k / 3 + p) % 1.0)]),
                              0.045, WET, 4, 8)


ARRAY_ROWS = 3


def _array_origin() -> np.ndarray:
    """Behind the pad, in the open valley the forest leaves clear
    (cover_scene.forest keeps its pines out of the corridor and the valley)."""
    m = cw.landmarks()
    per_row = math.ceil(R["plan"].panels / ARRAY_ROWS)
    return np.array([-(per_row - 1) * 0.54, m.deck_r + 2.6, 0.0])


def _power_bench(opaque) -> tuple[np.ndarray, np.ndarray]:
    """The 24/7 array, one tile per panel, and the bank, one box per rack."""
    plan = R["plan"]
    o = _array_origin()
    per_row = math.ceil(plan.panels / ARRAY_ROWS)
    for i in range(plan.panels):
        row, col = divmod(i, per_row)
        c = o + np.array([col * 1.08, row * 1.30, 0.75 + row * 0.55])
        opaque.box(c, (1.0, 1.15, 0.05), (0.10, 0.16, 0.32, 1.0))
        opaque.box(c - np.array([0.0, 0.0, 0.40 + row * 0.27]), (0.05, 0.05, 0.75 + row * 0.55),
                   (0.55, 0.55, 0.58, 1.0))
    bank = o + np.array([per_row * 1.08 + 0.3, -0.4, 0.0])     # the array's east end, in view
    for j in range(plan.racks):
        opaque.box(bank + np.array([0.0, 0.0, 0.14 + 0.24 * j]), (0.60, 0.45, 0.22),
                   (0.20, 0.22, 0.24, 1.0) if j % 2 else (0.28, 0.30, 0.33, 1.0))
    centre = o + np.array([(per_row - 1) * 0.54, 0.65, 1.6])
    return centre, bank + np.array([0.0, 0.0, 0.24 * plan.racks + 0.3])


def p_module(app, opaque, transparent, p):
    cw.paint(app)
    _stations(opaque, p)
    lc, pt = R["listing"], R["humid"]["point"]
    q = near_dome(rim_points())[0]
    _label(app, q + [0, 0, 1.45], f"ON THE BOX {lc['q_max_listed']:.0f} W; THE PHYSICS {lc['q_max_true']:.0f} W", AMBER)
    _label(app, q + [0, 0, 1.15], f"MOUNTED AT 12 V: {pt.q_cold:.0f} W MOVED FOR {pt.p_station:.0f} W", WHITE)


def p_rescore(app, opaque, transparent, p):
    cw.paint(app)
    _stations(opaque, p)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.85], f"CORRECTION: {R['C']['old_litres_per_kwh']:.2f} L/kWh WAS ASSUMED", RED)
    _label(app, m.apex + [0, 0, 0.5], f"SOLVED FROM THE MODULE: {R['humid']['litres_per_kwh']:.2f} L/kWh", GREEN)


def p_volts(app, opaque, transparent, p):
    cw.paint(app)
    rows = R["rows"]
    r = rows[min(len(rows) - 1, int(p * len(rows)))]
    pt = r["point"]
    _stations(opaque, p, strength=pt.q_cold / rows[-1]["point"].q_cold, wet=r["water_l_day"] > 0)
    q = near_dome(rim_points())[0]
    _label(app, q + [0, 0, 1.45], f"{pt.volts:.0f} V: {pt.q_cold:.0f} W MOVED, {pt.cop:.2f} PER WATT", AMBER)
    _label(app, q + [0, 0, 1.15], f"PLATE {pt.t_cold:.1f} C, DEW {R['dp']:.1f} C: "
           + (f"{r['water_l_day']:.1f} L/DAY" if r["water_l_day"] > 0 else "NO WATER"),
           BLUE if r["water_l_day"] > 0 else RED)


def p_day(app, opaque, transparent, p):
    cw.paint(app)
    inside = p > 0.6
    _stations(opaque, p, hot_inside=inside)
    m = cw.landmarks()
    h, ld = R["humid"], R["loads"]
    if inside:
        _label(app, m.apex + [0, 0, 0.85], f"HOT FACES INSIDE: A {h['draw_w']:.0f} W HEATER", RED)
    else:
        _label(app, m.apex + [0, 0, 0.85], f"TEN: {h['cooling_w']:.0f} W AND {h['water_l_day']:.1f} L/DAY OUT", BLUE)
    _label(app, m.apex + [0, 0, 0.5], f"THE ROOM TAKES ON {ld['water_l_day']:.1f} L/DAY", WHITE)


def p_sun(app, opaque, transparent, p):
    cw.paint(app)
    _stations(opaque, p)
    array, bank = _power_bench(opaque)
    plan = R["plan"]
    _label(app, array + [0, 0, 0.9], f"{plan.array_w:,.0f} W OF PANELS, ${plan.array_usd:,.0f}", AMBER)
    _label(app, bank + [0, 0, 0.2], f"{plan.bank_nameplate_kwh:.1f} kWh BANK, ${plan.bank_usd:,.0f}", AMBER)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"${plan.total_usd:,.0f} TO RUN ${plan.modules_usd:,.0f} OF PLATES", RED)


def p_instead(app, opaque, transparent, p):
    cw.paint(app)
    _stations(opaque, p, strength=R["volts"][9]["point"].q_cold / R["humid"]["point"].q_cold)
    m = cw.landmarks()
    d = R["daylight"]
    _label(app, m.apex + [0, 0, 0.85], f"DAYLIGHT SURPLUS: {d['hours']:.0f} H, {d['litres']:.2f} L/DAY, NO BANK", GREEN)
    _label(app, m.apex + [0, 0, 0.5], f"CAP THE DRIVE AT {R['best']['point'].volts:.0f} V", WHITE)


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    near = sc.Frame(sc.BENCH_A, sc.tight()).near
    dome = m.dome_centre + [0, 0, m.dome_r * 0.45]
    close = shots.push_in(near + [-0.07, 0.10, 0.0], near + [0.30, -0.85, 0.26],
                          near + [0.18, -0.58, 0.16], fov_start=38, fov_end=33)
    # The end face from a little higher and wider: the key, both plates and the
    # air moving along the channel.
    side_end = shots.push_in(near + [0.0, 0.15, -0.02], near + [0.42, -1.05, 0.42],
                             near + [0.30, -0.80, 0.30], fov_start=40, fov_end=36)
    end = near + [0.0, sc.SPECIMEN_LEN, 0.0]
    drawer = shots.push_in(end + [0.0, 0.08, -0.03], end + [0.75, 0.55, 0.30],
                           end + [0.45, 0.40, 0.18], 44, 38)
    lows = near_dome(belt_lows())[0]
    return {
        "breathe": shots.crane_reveal(dome, np.array(cw.HERO_EYE) + [0, 5.0, -2.2],
                                      np.array(cw.HERO_EYE) + [0, 1.5, 0.4], 44, 46, look_start=dome),
        "radial": close, "pump": close, "condense": close, "owner": close, "order": side_end,
        "packed": close, "regen": close, "drawer": drawer,
        "dewpoint": shots.orbit(dome, 10.5, 2.8, -115, 40, 46),
        "modes": shots.orbit(dome, 9.5, 3.4, -80, -35, 46),
        "weathers": shots.orbit(dome, 12.0, 4.0, -130, 25, 46),
        "choices": shots.orbit(dome, 11.0, 5.0, -60, -30, 46),
        "loop": shots.orbit(dome, 8.5, 2.2, -100, 30, 48),
        "levels": shots.orbit(dome, 10.0, 3.2, -95, 40, 46),
        "pentagon": shots.push_in((lows + m.apex) / 2, m.dome_centre + [2.6, -11.0, 4.4],
                                  m.dome_centre + [2.0, -9.4, 3.8], 46, 44),
        "rim": shots.low_hero(m.dome_centre + [0, 0, 0.8], 7.5, eye_height=0.9,
                              start_deg=-120, sweep_deg=40, look_up=0.4, fov=46),
        "stack": shots.orbit(dome, 9.5, 2.6, -110, 30, 48),
        "honest": shots.orbit(dome, 11.0, 3.5, -60, -25, 46),
        # From inside the dome, across the floor to the stove and its exchanger.
        "stove": shots.push_in(m.dome_centre + [-0.9, -0.6, 1.0], m.dome_centre + [1.3, 1.1, 1.5],
                               m.dome_centre + [0.9, 0.7, 1.4], 56, 50),
        "plan": shots.orbit(dome, 10.0, 6.0, -130, 60, 46),
        "correction": shots.orbit(dome, 9.0, 4.2, -100, 25, 46),
        "crown": shots.orbit(dome, 9.5, 3.0, -115, 30, 46),
        "down": shots.orbit(dome, 8.6, 1.8, -95, -30, 46),
        "siphon": shots.orbit(dome, 10.0, 2.6, -125, 35, 46),
        "water": shots.low_hero(m.dome_centre + [0, 0, 0.5], 6.8, eye_height=0.7,
                                start_deg=-110, sweep_deg=30, look_up=0.2, fov=46),
        "twoway": shots.orbit(dome, 10.0, 2.4, -80, 30, 46),
        "limits": shots.low_hero(m.dome_centre + [0, 0, 0.5], 7.2, eye_height=0.8,
                                 start_deg=-70, sweep_deg=-30, look_up=0.2, fov=46),
        "module": shots.low_hero(m.dome_centre + [0, 0, 0.5], 6.8, eye_height=0.9,
                                 start_deg=-110, sweep_deg=30, look_up=0.2, fov=46),
        "rescore": shots.orbit(dome, 9.0, 3.5, -100, 25, 46),
        "volts": shots.low_hero(m.dome_centre + [0, 0, 0.5], 6.5, eye_height=0.9,
                                start_deg=-95, sweep_deg=20, look_up=0.2, fov=46),
        "day": shots.orbit(dome, 9.5, 2.6, -120, 35, 46),
        # From above the treeline, south-east, over the dome to the array behind it.
        "sun": shots.push_in(m.dome_centre + [0.3, 3.2, 0.2], m.dome_centre + [5.2, -10.0, 9.5],
                             m.dome_centre + [3.8, -8.2, 8.2], 46, 44),
        "instead": shots.orbit(dome, 10.0, 3.0, -70, -30, 46),
        "close": shots.crane_reveal(m.dome_centre + [0, -0.6, 1.4], near + [0.4, -0.9, 0.3],
                                    cw.HERO_EYE, 40, 46, look_start=near),
    }


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug)


def _chapters() -> tuple[Chapter, ...]:
    f = F
    c, b, g = f["c"], f["b"], f["g"]
    bands = f["bands"]
    weathers = [f"{s.label}: out {deg(s.sensors.t_out)} C {s.sensors.rh_out * 100:.0f}%, "
                f"in {s.sensors.t_in:.0f} C {s.sensors.rh_in * 100:.0f}%"
                + (", rain" if s.sensors.rain else "")
                + (f", wood {s.sensors.wood_mc * 100:.0f}%" if s.sensors.wood_mc >= scl.C["mc_wet"] else "")
                for s in scl.SCENARIOS]
    choices = [f"{s.label}: dew {deg(d.dp_out)} out / {deg(d.dp_in)} in -> {d.mode}"
               for s, d in f["decisions"]]
    modes = [f"{k}: {scl.MODES[k][0]}" for k in scl.ACTIVE_MODES]
    r_c, r_lc, r_h, r_ld, r_cmp, r_plan = R["C"], R["listing"], R["humid"], R["loads"], R["compared"], R["plan"]
    r_pt, r_room, r_rows = r_h["point"], R["room"], R["rows"]
    rows = [
        (1, "breathe", "One channel, many jobs", "Which way should the seam breathe?",
         f"Every one of this dome's {f['seams']} seams has a channel inside it. Air can go in "
         f"through it, out through it, round in a loop, through a desiccant or past one, over a "
         f"cold plate or a warm one. That is a lot of choices. This film works out which one to "
         f"make, and when, from one number.",
         [f"seams = {f['seams']}", f"modes = {len(scl.ACTIVE_MODES)}"]),
        (2, "radial", "Inner skin, outer skin", "The line from the centre outward has a name.",
         "First, the word you were looking for. The line that runs from the centre of the dome "
         "straight outward is the radial direction. Through a wall it is the wall's thickness. In "
         "a seam it runs from the V's open mouth on the room side up to the ridge on the weather "
         "side. So the channel has two skins: an outer one that touches outside, and an inner one "
         "that touches the room. Put a Peltier plate on each and you can set the temperature of "
         "both.", ["radial = centre -> outward", "outer skin = ridge (weather)",
                   "inner skin = mouth (room)"]),
        (3, "pump", "A plate is a heat pump", "And it runs both ways.",
         "A Peltier plate is not a cooler. It is a pump that moves heat from one face to the "
         "other, and reversing the current reverses the direction. So the rule for both plates "
         "is simple: throw the heat to the side you want warmer. In winter, into the room. In "
         "summer, outside. The first film, The Wedge Dome Explained, showed the plate throwing "
         "its heat into the room. That is right in winter and wrong in summer.",
         ["winter: cold face in the channel, heat to the room",
          "summer: cold face in the channel, heat to the outside skin"]),
        (4, "dewpoint", "Compare dew points, not humidity", "The one rule that ends the confusion.",
         f"Now the rule the whole system runs on. Never compare relative humidity. Compare dew "
         f"points. Outside air at {deg(f['cd_t_out'])} degrees and {f['cd_rh_out']:.0f} percent "
         f"sounds damp. Its dew point is {deg(f['cd_dp_out'], 1)}. Inside at {f['cd_t_in']:.0f} "
         f"degrees and {f['cd_rh_in']:.0f} percent, the dew point is {deg(f['cd_dp_in'], 1)}. "
         f"Per kilogram, the damp-sounding air carries {f['cd_w_out']:.1f} grams of water; the "
         f"room's carries {f['cd_w_in']:.1f}. Bring it in, and it dries the dome.",
         [f"out {deg(f['cd_t_out'])} C {f['cd_rh_out']:.0f}% -> dew {f['cd_dp_out']:.1f} C, "
          f"{f['cd_w_out']:.1f} g/kg",
          f"in {f['cd_t_in']:.0f} C {f['cd_rh_in']:.0f}% -> dew {f['cd_dp_in']:.1f} C, "
          f"{f['cd_w_in']:.1f} g/kg",
          "dew point: Magnus formula (standard)"]),
        (5, "condense", "Will it condense?", "Dew point against surface temperature.",
         f"The second question: will this air leave water on that surface? It will whenever "
         f"the air's dew point is above the surface's temperature. So a condensing plate must be "
         f"colder than the dew point. And every piece of wood must be warmer than it, with room "
         f"to spare. This film keeps wood {f['margin']:.0f} degrees above the dew point of the "
         f"air that touches it.",
         ["water if dew point > surface", "collector: T < dew point",
          f"wood: T > dew point + {f['margin']:.0f} K (assumed margin)"]),
        (6, "owner", "Fifteen to twenty degrees colder", "The question you asked, with numbers.",
         f"You asked: if the wood sits at the dew point and the metal channel is fifteen to "
         f"twenty degrees below it, will the water go to the metal? Take a room at "
         f"{c['t_air']:.0f} degrees and {c['rh_air'] * 100:.0f} percent. Its dew point is "
         f"{c['dp']:.1f}. The middle of your range, {c['below']:.1f} degrees under that, is "
         f"{deg(c['owners_plate'], 1)}. "
         f"The plate freezes. Frost stops the water running and chokes the fins. So hold the "
         f"plate {f['below']:.0f} degrees under the dew point and never below {f['frost']:.0f}: "
         f"here, {c['plate']:.1f} degrees.",
         [f"dew point = {c['dp']:.1f} C",
          f"your plate = {c['dp']:.1f} - {c['below']:.1f} = {c['owners_plate']:.1f} C: frost",
          f"held at max({f['frost']:.0f}, {c['dp']:.1f} - {f['below']:.0f}) = {c['plate']:.1f} C"]),
        (7, "order", "Plate first, wood second", "A colder surface elsewhere does not protect the wood.",
         f"And the real answer: a colder surface somewhere else does not protect wood that is "
         f"already at the dew point. Wood touching raw room air still gets wet. What protects it "
         f"is the order. Send the air over the plate first. It leaves with a dew point of "
         f"{c['dp_after']:.1f}, so wood at {c['dp']:.1f} is now {c['dp'] - c['dp_after']:.1f} "
         f"degrees clear. One more rule: the cold metal must never touch the wood, or it chills "
         f"the wood to its own temperature.",
         [f"raw air: wood at {c['dp']:.1f} C = dew point -> wet",
          f"after the plate: dew point {c['dp_after']:.1f} C (plate + {f['approach']:.0f} K, assumed)",
          f"wood safe above {c['wood_min_dried']:.1f} C"]),
        (8, "modes", f"{NUMBER_WORDS[len(scl.ACTIVE_MODES)]} modes", "Two of them never touch the room.",
         "That gives the channel its modes. Take outside air in. Push inside air out. Condense "
         "inside air on a cold skin before it leaves. Loop the seam's own air through the "
         "desiccant. Purge a wet seam with outside air and send it straight back out. Supply "
         "dried air and hold the room at a slight positive pressure. Or shut the exposed "
         "intakes in the rain. The loop and the purge never touch the living space.", modes),
        (9, "weathers", "The weathers we assumed", "Estimates, not measurements.",
         f"To test the controller, here are the weathers from your table, plus one more. These "
         f"are typical conditions, our estimates, not measurements from a site. Each one gets "
         f"inside and outside temperatures and humidities, and the wet ones get a wood moisture "
         f"reading at or over {f['mc_wet']:.0f} percent, where lumber stops counting as dry.",
         weathers),
        (10, "choices", "What the controller chose", "All of them match your table.",
         f"And here is what the code chose, working only from dew points. Cold and dry: take it "
         f"in. Hot and humid: dried supply only. Rain: shut. After rain, with dry air outside: "
         f"purge the seam. Muggy outside with a wet frame: close the loop. All "
         f"{len(f['decisions'])} weathers get the answer your table gives, and the film's own "
         f"test fails if one ever does not.", choices),
        (11, "loop", "The loop and the purge", "Drying the structure is not ventilating the house.",
         "The two modes worth the extra plumbing are these. The frame loop takes the seam's air, "
         "dries it in the desiccant and sends it back: nothing thrown outside, nothing muggy "
         "pulled in. The purge takes dry outside air through a wet seam and straight back out. "
         "That needs two outside ports per circuit, and it means drying the frame is a separate "
         "job from ventilating the house.",
         ["frame loop: seam -> desiccant -> seam", "purge: outside -> seam -> outside"]),
        (12, "levels", "The dome's levels, from the solver", "Four rings, five bands of seams.",
         f"Now where each job goes. The solver's dome stands on five heights: "
         f"{f['counts'][0]} corners at the rim, {f['counts'][1]} and {f['counts'][2]} in a belt "
         f"that zigzags between two heights, {f['counts'][3]} round the crown, and the apex. The "
         f"seams between them fall into five bands: {bands['lower'].seams} in the lower band, "
         f"{bands['belt'].seams} in the belt, {bands['upper'].seams} in the upper band, "
         f"{bands['pentagon'].seams} round the crown pentagon, and {bands['cap'].seams} to the "
         f"apex.",
         [f"{x.label}: {x.seams} seams, {x.length_ft:.0f} ft, {x.slope_deg:.0f} deg"
          for x in bands.values()]),
        (13, "pentagon", "The ring that cannot drain", "Air at the top, water never.",
         f"The slopes decide the jobs. The lower band's seams rise at {bands['lower'].slope_deg:.0f} "
         f"degrees, and water runs down them fast. The belt zigzags at only "
         f"{bands['belt'].slope_deg:.0f} degrees, but that zigzag has {f['belt_lows']} low points, "
         f"and each one is a natural drain. The pentagon ring round the crown is dead level. "
         f"Water there stands in the wood. So that ring carries air, never water.",
         [f"lower: {bands['lower'].slope_deg:.1f} deg -> drains",
          f"belt: {bands['belt'].slope_deg:.1f} deg, {f['belt_lows']} low points -> drains",
          f"pentagon: {bands['pentagon'].slope_deg:.1f} deg -> dead level"]),
        (14, "rim", "Condense low, drain at the rim", "Your first-ring idea is right.",
         f"Your idea of putting the plates on the first ring is right, and here is why. "
         f"Condensate falls. A plate at the rim drops its water straight into a drain at one of "
         f"the {f['rim_ports']} rim corners, with no seam to travel through. The rain belongs "
         f"outside, in a gutter at the rim. It should not come in through a seam higher up. "
         f"Every foot of seam that carries liquid water is a foot of wood waiting for a leak.",
         [f"rim ports = {f['rim_ports']}", "condensing plates: rim", "rain: outside gutter at the rim"]),
        (15, "stack", "Warm air rises", "In low, out high, and the fan still does the work.",
         f"Air has its own preference. Warm inside air wants to leave at the top, so take air in "
         f"at the rim and let it out at the pentagon ring and the apex. But the pull is small. "
         f"With the inside ten degrees warmer, the height of this dome makes {f['stack']:.1f} "
         f"pascals. The barrier fan holds {f['barrier']:.0f}. The stack helps; it does not "
         f"replace the fan.",
         [f"stack = rho g h dT / T = {f['stack']:.2f} Pa at 10 K",
          f"barrier fan = {f['barrier']:.0f} Pa"]),
        (16, "packed", "Why the desiccant stays out of the seams", "The number that ends the rainbow.",
         f"Now the cartridge. Could you pack the beads into the seams themselves, round a ring, "
         f"or over the top like a rainbow, a path of {f['meridian']:.0f} feet? Push one seam's "
         f"share of air, {b.seam_flow_cfm:.0f} cubic feet a minute, through one packed seam and "
         f"the beads resist with {b.seam_drop_pa:,.0f} pascals. A small in-line fan manages about "
         f"{f['fan']:.0f}. At that, a packed seam passes {b.seam_flow_at_fan_cfm:.2f} cubic feet "
         f"a minute. The rainbow is longer still.",
         [f"packed seam at {b.seam_flow_cfm:.1f} cfm: {b.seam_drop_pa:,.0f} Pa (Ergun)",
          f"fan = {f['fan']:.0f} Pa (estimate) -> {b.seam_flow_at_fan_cfm:.2f} cfm",
          f"rim-apex-rim = {f['meridian']:.1f} ft",
          "beads 2.5 mm, voidage 0.37 (nominal)"]),
        (17, "regen", "And it cannot be dried where it sits", "The temperature that rules out the walls.",
         f"There is a second reason. A molecular sieve gives its water back only when it is hot: "
         f"about {g['sieve_c']:.0f} degrees. Even silica gel wants {g['silica_c']:.0f}. The printed "
         f"key softens at {g['petg_c']:.0f}, and this film never sends air hotter than "
         f"{g['seam_max_c']:.0f} through a seam. A desiccant in the seams could never be "
         f"regenerated in place.",
         [f"13X regenerates at {g['sieve_c']:.0f} C", f"silica gel {g['silica_c']:.0f} C",
          f"PETG softens {g['petg_c']:.0f} C", f"seam air limit {g['seam_max_c']:.0f} C (assumed)"]),
        (18, "drawer", "Two drawers and a gate", "One drying while the other is regenerated.",
         f"So the desiccant lives in drawers, at the rim, where the channels come down. One "
         f"drawer {f['face_cm']:.0f} centimetres square and {f['depth_cm']:.0f} deep holds "
         f"{b.drawer_sieve_kg:.1f} kilograms of beads, and passes the whole dome's "
         f"{b.drawer_flow_cfm:.0f} cubic feet a minute at {b.drawer_drop_pa:.0f} pascals. Use two: "
         f"one working, one being dried. The gate that picks between drawer and bypass should "
         f"fall back to the bypass when the power goes, so air never stops.",
         [f"drawer {f['face_cm']:.0f} x {f['face_cm']:.0f} x {f['depth_cm']:.0f} cm (assumed)",
          f"beads = {b.drawer_sieve_kg:.2f} kg, holds {b.drawer_hold_kg:.2f} kg of water",
          f"at {b.drawer_flow_cfm:.0f} cfm: {b.drawer_drop_pa:.0f} Pa",
          f"regenerate: {g['drawer_kwh']:.2f} kWh = {g['stove_minutes']:.0f} min at {f['stove_kw']:.0f} kW"]),
        (19, "honest", "What the desiccant will not do", "It does not dry a soaked frame.",
         f"And the number that does not help. A frame that gets wet, over {f['mc_wet']:.0f} "
         f"percent, has {b.frame_water_kg:.0f} kilograms of water to lose to get back to "
         f"{f['mc_target']:.0f}. That is {b.drawers_for_frame:.0f} drawer fills, and "
         f"{g['frame_kwh']:.0f} kilowatt hours to regenerate them. The desiccant is for the "
         f"weather when no air is dry enough. Drying a wet frame is the purge's job, on the next "
         f"dry day.",
         [f"frame water, {f['mc_wet']:.0f}% -> {f['mc_target']:.0f}% = {b.frame_water_kg:.0f} kg",
          f"= {b.drawers_for_frame:.1f} drawer fills", f"= {g['frame_kwh']:.0f} kWh of regeneration",
          "pine 420 kg/m3 dry (estimate)"]),
        (20, "stove", "The stove's heat, never its air", "A sealed exchanger, and nothing else.",
         f"The stove can help, but only through a wall of steel. A sealed exchanger on the flue "
         f"warms clean air, and that air can dry the frame or regenerate a drawer. The smoke side "
         f"never meets it. Keep the seam air under {g['seam_max_c']:.0f} degrees. Give the stove "
         f"its own outside combustion air. And never let the stove push or pull the seam air, "
         f"or a back draught puts smoke in the walls.",
         ["exchanger: flue gas | steel | clean air", f"seam air <= {g['seam_max_c']:.0f} C",
          "combustion air: its own outside duct"]),
        (21, "plan", "The layout", "Every level with one job.",
         f"So here is the layout. At the rim: {f['rim_ports']} ports, the condensing plates, the "
         f"drains and the two drawers. The lower band carries air up and water down. The belt's "
         f"{f['belt_lows']} low points drain it. The pentagon ring is the exhaust manifold: air "
         f"only. The cap vents at the apex. Sensors inside, outside and in the seam read "
         f"temperature and humidity, the wood's moisture, and the rain.",
         ["rim: ports, plates, drains, drawers", "lower band: air up, water down",
          "belt: drains at the low points", "pentagon: exhaust manifold, air only",
          "cap: apex vent", "sensors: T, RH in / out / seam, wood %, rain"]),
        (22, "correction", "A correction: the cap never opens", "Chapters 15 and 21 put a hole in the roof.",
         "First, a correction. Earlier in this film, the stack chapter let the exhaust out at the "
         "pentagon ring and the apex, and the layout said the cap vents at the apex. That is wrong. "
         "A vent at the apex is a hole in the cap, at the place the weather hits hardest, with the "
         "frame right under it. The cap is one watertight layer, and it is never opened. Here is "
         "how the dome breathes anyway.",
         ["was: exhaust out at the apex", "now: no opening in the cap above the rim"]),
        (23, "crown", "In at the crown, under the cap", "The stalest air is at the top.",
         f"Warm air rises, and the warmest air in the room is also the wettest and the stalest: "
         f"breath and steam, carried up. In a dome it collects at the crown. So a grille there, "
         f"inside the shell and under the cap, takes the room's air into the seam channels, inside "
         f"their printed keys. Holes through the cap above the rim: "
         f"{V['route'].cap_penetrations}.",
         ["intake: a grille at the crown, inside the shell",
          f"holes in the cap = {V['route'].cap_penetrations}"]),
        (24, "down", "Down the seams, out facing the ground", "Every falling seam is a path.",
         f"From the crown the air goes down. {V['route'].seams_down} of the dome's {F['seams']} "
         f"seams fall all the way from the apex to the rim without climbing; the "
         f"{V['route'].level_seams} level seams of the pentagon ring stay off the path. It leaves at "
         f"the rim, through ports under the cap's brim that face the ground. Rain falls; an opening "
         f"that faces down takes in only water that would have to climb. The dome needs "
         f"{V['need']:.1f} cubic feet a minute, and the five cap seams carry "
         f"{V['cap']['headroom']:.1f} times that at a quiet speed.",
         [f"falling seams = {V['route'].seams_down} of {F['seams']}",
          f"level, kept out = {V['route'].level_seams}",
          f"capacity = {V['cap']['headroom']:.1f} x the {V['need']:.1f} cfm need"]),
        (25, "siphon", "In winter the air falls by itself", "A loop that turns itself.",
         f"Here is why down is the right way. In winter the room's warm air rises to the crown. In "
         f"the channel the exhaust gives its heat to the cold shell, gets heavier than the room's "
         f"air, and falls. A warm column rising and a cool one falling make a loop that turns "
         f"itself. At {V['rows']['winter']['t_out']:.0f} degrees outside it pulls with "
         f"{V['rows']['winter']['drive_pa']:.1f} pascals and carries "
         f"{100 * V['rows']['winter']['share']:.0f} percent of the need with no fan. In cool weather, "
         f"{100 * V['rows']['cool']['share']:.0f} percent. In summer sun it runs backwards, and the "
         f"fan does it all against {V['rows']['summer sun']['fan_pa']:.0f} pascals, where a small fan "
         f"pushes {V['fan']:.0f}.",
         [f"{r['weather']}: {r['drive_pa']:.2f} Pa, {100 * r['share']:.0f}% of the need"
          for r in V["rows"].values()]),
        (26, "water", "The water leaves by the same door", "Air and condensate, the same way down.",
         f"When the channel is colder than the room air's dew point, the exhaust drops water inside "
         f"the key: {V['rows']['winter']['litres_day']:.2f} litres a day at "
         f"{V['rows']['winter']['t_out']:.0f} degrees outside, "
         f"{V['rows']['hard winter']['litres_day']:.1f} at {V['rows']['hard winter']['t_out']:.0f}. "
         f"That water runs downhill, which is the way the air is already going, and out of the same "
         f"ports. Sent up, it would run back against the air and pool. Sent down, nothing pools, and "
         f"the wet air never touches the wood: it runs inside the key.",
         [f"winter: {V['rows']['winter']['litres_day']:.2f} L/day",
          f"hard winter: {V['rows']['hard winter']['litres_day']:.2f} L/day", "out with the air, at the rim"]),
        (27, "twoway", "Two ways, both doors at the bottom", "Fresh in low, stale out high.",
         "The dome breathes both ways. Fresh air comes in through its own ports at the rim, facing "
         "the ground, and into the room low, past the drawers and plates. Stale air leaves from the "
         "crown, down the seams, and out at the rim. The room itself is the loop's rising leg. Run "
         "the two flows equal, and the room is neither pressed nor pulled, so no air is forced "
         "through the frame either way.",
         ["in: rim ports -> room, low", "out: crown -> seams -> rim ports", "in = out"]),
        (28, "limits", "Where it stops working", "Ice, snow, screens and summer.",
         f"And where it stops. With the channel halfway between inside and outside, the outlets "
         f"reach freezing below {V['freeze']:.0f} degrees outside, and ice can close them: heat the "
         f"outlet stubs, or run the exhaust through the rim drawers on those nights. A port under a "
         f"snowdrift does nothing, so keep the ports above the snow line. Screen every one. And in "
         f"summer the fan carries the whole need.",
         [f"outlets freeze below {V['freeze']:.0f} C (channel halfway, assumed)",
          "ports above the snow line, screened", "summer: the fan"]),
        (29, "module", "Seventy on the box", "Ten modules at the rim, run day and night.",
         f"Now the plates themselves. You bought one thermoelectric module, a TEC1-12706, for "
         f"{r_c['module_usd']:.0f} dollars, and want {r_c['modules']:.0f} round the rim, one at each "
         f"port, running day and night on the sun. The listing says {r_lc['q_max_listed']:.0f} watts. "
         f"Worked from the listing's own maxima, the most it can move is {r_lc['q_max_true']:.0f}, and "
         f"only with no temperature difference across it. Mounted here, hot face on a finned sink "
         f"outside at {r_room[4]:.0f} degrees, cold face in a room at {r_room[2]:.0f} and "
         f"{100 * r_room[3]:.0f} percent, it settles at {r_pt.t_cold:.1f} degrees, draws "
         f"{r_pt.amps:.1f} amps, and moves {r_pt.q_cold:.0f} watts of heat for {r_pt.p_station:.0f} "
         f"watts of electricity, its fans included.",
         [f"listed {r_lc['q_max_listed']:.0f} W; physics {r_lc['q_max_true']:.1f} W at dT = 0",
          f"mounted, 12 V: cold face {r_pt.t_cold:.1f} C, {r_pt.amps:.2f} A",
          f"moves {r_pt.q_cold:.1f} W for {r_pt.p_station:.1f} W",
          "sinks 0.20 K/W hot, 0.40 K/W cold (assumed)"]),
        (30, "rescore", "A correction: less water per watt", "Two earlier films assumed a yield.",
         f"A correction. The Seam Does Four Jobs and The Wedge Dome Explained counted "
         f"{r_c['old_modules']:.0f} plates at {r_c['old_watts_each']:.0f} watts, making "
         f"{r_c['old_litres_per_kwh']:.2f} litres of water per kilowatt hour. That yield was an "
         f"assumption, and it was wrong. Solved from the module, the cold face is "
         f"{R['dp'] - r_pt.t_cold:.1f} degrees under the room's dew point, and only "
         f"{100 * r_pt.latent_share:.0f} percent of the heat it takes is water. The yield is "
         f"{r_h['litres_per_kwh']:.2f} litres per kilowatt hour: a litre costs "
         f"{R['daylight']['kwh_per_litre']:.1f} kilowatt hours, not "
         f"{R['daylight']['old_kwh_per_litre']:.1f}.",
         [f"was: {r_c['old_modules']:.0f} x {r_c['old_watts_each']:.0f} W, "
          f"{r_c['old_litres_per_kwh']:.2f} L/kWh (assumed)",
          f"now: {r_c['modules']:.0f} x {r_pt.p_station:.0f} W, {r_h['litres_per_kwh']:.2f} L/kWh (solved)",
          f"water share of the heat = {100 * r_pt.latent_share:.0f}%"]),
        (31, "volts", "Slower is better, until it stops condensing", "Voltage against water.",
         f"Run a Peltier gently and it gets far more efficient: at {r_rows[0]['point'].volts:.0f} "
         f"volts it moves {r_rows[0]['point'].cop:.2f} watts of heat per watt, at 12 only "
         f"{r_pt.cop:.2f}. But at 6 volts the cold face stops at {R['volts'][6]['point'].t_cold:.1f} "
         f"degrees, above the dew point, and the water stops. The most water per kilowatt hour "
         f"comes at {R['best']['point'].volts:.0f} volts. And the controller asks for the plate "
         f"{f['below']:.0f} degrees under the dew point, {R['setpoint']:.1f}. At full drive the "
         f"module stops {r_pt.t_cold - R['setpoint']:.1f} short, so chasing that setpoint just runs "
         f"it flat out. Cap the drive at {R['best']['point'].volts:.0f} volts instead.",
         [f"{r['point'].volts:.0f} V: {r['point'].q_cold:.0f} W, COP {r['point'].cop:.2f}, "
          f"plate {r['point'].t_cold:.1f} C, ten make {r['water_l_day']:.1f} L/day"
          for r in r_rows] + [f"dew point {R['dp']:.1f} C, setpoint {R['setpoint']:.1f} C"]),
        (32, "day", "A day of ten", "Heat and water out, against what the room takes on.",
         f"Ten at 12 volts, all day, on a humid day: {r_h['cooling_w']:.0f} watts of heat out of the "
         f"room, and {r_h['water_l_day']:.1f} litres of water a day. Two people, their cooking and "
         f"washing, and the fresh air put in {r_ld['water_l_day']:.1f} litres. The ring takes out "
         f"about {100 * r_h['water_l_day'] / r_ld['water_l_day']:.0f} percent. It helps; it does not "
         f"keep up. And the hot faces must be outside: they throw {r_h['outside_w']:.0f} watts. "
         f"Mounted the other way round, the ring is a {r_h['draw_w']:.0f} watt heater that drips.",
         [f"ten: {r_h['cooling_w']:.0f} W of heat, {r_h['water_l_day']:.1f} L/day of water",
          f"room takes on {r_ld['water_l_day']:.1f} L/day, {r_ld['heat_w']:.0f} W (sun not counted)",
          f"hot faces: {r_h['outside_w']:.0f} W, outside"]),
        (33, "sun", "Feeding it on the sun", "Twenty-four hours a day, priced.",
         f"Running all day and all night, ten stations draw {r_plan.load_w:.0f} watts: "
         f"{r_plan.day_kwh:.1f} kilowatt hours a day, {r_plan.night_kwh:.1f} of them off a bank at "
         f"night. From {R['sun_hours']:.1f} "
         f"peak sun hours, that takes about {r_plan.array_w:,.0f} watts of panels, and a "
         f"{r_plan.bank_nameplate_kwh:.1f} kilowatt hour bank to cover the night and one dark day. "
         f"That is {r_plan.total_usd:,.0f} dollars, for {r_plan.modules_usd:.0f} dollars of modules. "
         f"A small compressor dehumidifier takes out the same water for "
         f"{r_cmp['dehumidifier_kwh']:.1f} kilowatt hours a day.",
         [f"load {r_plan.load_w:.0f} W x 24 h = {r_plan.day_kwh:.1f} kWh/day",
          f"array {r_plan.array_w:,.0f} W ({r_plan.panels} panels): ${r_plan.array_usd:,.0f}",
          f"bank {r_plan.bank_nameplate_kwh:.1f} kWh ({r_plan.racks} racks): ${r_plan.bank_usd:,.0f}",
          f"dehumidifier, same water: {r_cmp['dehumidifier_kwh']:.1f} kWh/day (estimate)"]),
        (34, "instead", "What to do instead", "Daylight surplus, a cap on the drive, a compressor.",
         f"So keep the plates for the job only they can do: drying a seam that will not dry itself "
         f"in warm, still, humid weeks. Run them on daylight surplus, "
         f"{R['daylight']['hours']:.0f} hours a day: {R['daylight']['kwh']:.1f} kilowatt hours the "
         f"array was making anyway, and {R['daylight']['litres']:.2f} litres a day, with no extra "
         f"battery. Cap the drive at {R['best']['point'].volts:.0f} volts. And if the room itself "
         f"needs drying or cooling for weeks, buy the compressor: the smallest window air "
         f"conditioner moves {r_cmp['ac_cop']:.1f} watts of heat per watt; the ring moves "
         f"{r_cmp['ring_cop']:.2f}.",
         [f"daylight surplus: {R['daylight']['hours']:.0f} h, {R['daylight']['kwh']:.1f} kWh, "
          f"{R['daylight']['litres']:.2f} L/day",
          f"cap the drive: {R['best']['point'].volts:.0f} V",
          f"window AC {r_cmp['ac_cop']:.1f} W per W; the ring {r_cmp['ring_cop']:.2f}"]),
        (35, "close", "Dew point decides", "Send air toward the wood only when it is drier.",
         "One rule runs all of it. Send air toward the structure only when its dew point is "
         "lower than the moisture you are trying to remove, unless you are sending wetter air to "
         "a cold metal surface built to collect and drain the water. The same seams, winter and "
         "summer, rain and sun.", []),
    ]
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()

SCENES = {
    "breathe": p_breathe, "radial": p_radial, "pump": p_pump, "dewpoint": p_dewpoint,
    "condense": p_condense, "owner": p_owner, "order": p_order, "modes": p_modes,
    "weathers": p_weathers, "choices": p_choices, "loop": p_loop, "levels": p_levels,
    "pentagon": p_pentagon, "rim": p_rim, "stack": p_stack, "packed": p_packed,
    "regen": p_regen, "drawer": p_drawer, "honest": p_honest, "stove": p_stove,
    "plan": p_plan, "correction": p_correction, "crown": p_crown, "down": p_down,
    "siphon": p_siphon, "water": p_water, "twoway": p_twoway, "limits": p_limits,
    "module": p_module, "rescore": p_rescore, "volts": p_volts, "day": p_day, "sun": p_sun,
    "instead": p_instead, "close": p_close,
}


def validate_seam_climate_film() -> None:
    scl.validate_seam_climate()
    sc.validate_channel_scene()
    cw.validate_cabin_world()
    for ch in CHAPTERS:
        assert ch.stage in SCENES, ch.stage
        eye, target, fov = MOVES[ch.slug](0.5)
        assert np.all(np.isfinite(eye)) and 20 < fov < 70, ch.slug
        assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.2, ch.slug
    # The Cabin World's dome sorts into the same bands as the reference build.
    model, _scale, _shift = sc._world()
    world = {k: len(v) for k, v in scl.classify(model).items()}
    assert world == {b.key: b.seams for b in F["bands"].values()}, world
    assert len(belt_lows()) == F["belt_lows"] and len(rim_points()) == F["rim_ports"]
    # The claims the narration makes, checked against the facts.
    assert all(d.mode in s.want for s, d in F["decisions"])
    # Chapter 8 speaks one sentence per active mode; its title counts them.
    assert len(scl.ACTIVE_MODES) == 7, "chapter 8's narration lists seven actions"
    assert F["cd_w_out"] < F["cd_w_in"], "the 'damp-sounding air is drier' line"
    assert F["stack"] < F["barrier"], "the stack helps, it does not replace the fan"
    assert F["b"].seam_flow_at_fan_cfm < 1.0
    assert F["c"]["plate"] > F["frost"] - 1e-9
    # The breathing cap: no hole in the cap, the correction names the old claim,
    # and the winter siphon claim holds.
    assert V["route"].cap_penetrations == 0
    corr = next(ch for ch in CHAPTERS if ch.slug == "correction").narration[0]
    assert "apex" in corr and "wrong" in corr
    assert V["rows"]["winter"]["share"] >= 1.0, "chapter 25 says winter needs no fan"
    assert V["rows"]["summer sun"]["fan_pa"] < V["fan"]
    for slug in ("correction", "crown", "down", "siphon", "water", "twoway", "limits",
                 "module", "rescore", "volts", "day", "sun", "instead"):
        assert slug in SCENES and slug in MOVES, slug
    # The ten plates: the module's own validator holds every claim the
    # narration makes (70 W above the physics, 6 V dry, the setpoint out of
    # reach, 9 V best, the power system dearer than the plates), and the
    # correction names what was assumed.
    from . import peltier_ring as pr
    pr.validate_peltier_ring()
    resc = next(ch for ch in CHAPTERS if ch.slug == "rescore").narration[0]
    assert "correction" in resc.lower() and "assumption" in resc
    assert R["humid"]["litres_per_kwh"] < R["C"]["old_litres_per_kwh"]
    assert R["humid"]["water_l_day"] < R["loads"]["water_l_day"], "it does not keep up"


CABIN_SEAM_CLIMATE_LESSON = Lesson(
    key="cabin_seam_climate", brand="DOMESIM", title="Which Way the Seam Breathes",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_seam_climate_film,
    snapshot_prefix="cabin_seam_climate", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
