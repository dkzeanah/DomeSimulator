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
        (22, "close", "Dew point decides", "Send air toward the wood only when it is drier.",
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
    "plan": p_plan, "close": p_close,
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


CABIN_SEAM_CLIMATE_LESSON = Lesson(
    key="cabin_seam_climate", brand="DOMESIM", title="Which Way the Seam Breathes",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_seam_climate_film,
    snapshot_prefix="cabin_seam_climate", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
