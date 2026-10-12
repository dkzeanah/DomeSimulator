"""The Cell Wall: the dome's skin as layers, each one piece, each a network.

The owner's idea, worked through in the Cabin World. A groove -- a C-channel --
down the round face of every member holds a hose-gasket round each triangle:
a *local* channel that reaches that triangle and nothing else. Each gasket is
ported three times, so a triangle can be jumpered to its neighbours through
the inside seam or over the outside one, or capped; jumpered everywhere, the
gaskets form a network of locals beside the *global* channel in the seams'
keys. Rings round the dome hold a third kind. Over and under the frame lie
layers, each made as one piece -- fabric, semi-flexible or hard -- with its
channels built in, and each a service that runs alone, runs both ways, or
hands what it carries to the next: a body with a bus, like a car.

The second cut (October 2026). The first drew the layers as see-through tiles;
here every layer is a solid shell with its thickness, cut away facing the
camera, every layer's contents flowing at once along the cut faces
(:mod:`two_v_demo.cell_wall_solids`); the fabric layers are quilts. It adds
the ports and the network of locals, the materials, venting, a wildfire worked
through from the first ember to the drying-out, and the uses counted.

Every figure is :mod:`two_v_demo.cell_wall`'s, measured off the solver's dome
or declared in its tables, which go on screen before they are used. The film
keeps the numbers that argue back.

    py -3.12 -m rerender stills cabin_cell_wall
    py -3.12 -m rerender render cabin_cell_wall
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import cell_wall as cwall
from . import cell_wall_scene as cs
from . import cell_wall_solids as so
from . import channel_scene as sc
from . import shots
from .lesson_seam_climate import band_seams, flow
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)
PURPLE = (205, 160, 255)

DRIP = (0.40, 0.70, 1.00, 0.95)
AIRFLOW = (0.45, 0.92, 0.62, 1.0)
SMOKE = (0.55, 0.55, 0.58, 1.0)
DRY_AIR = (0.95, 0.97, 1.00, 1.0)


# ----------------------------------------------------------------------
# Every number the film states
# ----------------------------------------------------------------------

def _facts() -> dict:
    from . import seam_vent as sv

    n = cwall.networks()
    kinds: dict[str, int] = {}
    for _name, _value, _unit, kind, _why in cwall.CONSTANTS:
        kinds[kind] = kinds.get(kind, 0) + 1
    flat = [s for s in n.face_slope_deg if s <= cwall.C["plant_max_slope_deg"]]
    cage = cwall.cage()
    return {
        "n": n, "g": cwall.groove(), "foam": cwall.foam(), "glue": cwall.glue(), "vac": cwall.vacuum(),
        "rain": cwall.rain(), "fire": cwall.fire(), "air": cwall.air_filter(), "heat": cwall.heating(),
        "cool": cwall.cooling(), "cage": cage, "fog": cwall.fog(), "fl": cwall.flotation(),
        "live": cwall.living(), "x": cwall.extras(), "bus": cwall.bus(), "cx": cwall.complexity(),
        "room": cwall.seam_room(), "b": cwall.borrowed(), "kinds": kinds, "C": cwall.C,
        "prof": {p["layer"]: p["temp_c"] for p in cwall.profile()},
        "flat_n": len(flat), "flat_deg": min(n.face_slope_deg),
        "seam_len_m": cwall.C_LIGHT / (2 * cage["seam_cutoff_mhz"] * 1e6),
        "shell_ft2": n.shell_m2 / cwall.M2_PER_FT2,
        "ln": cwall.local_net(), "fe": cwall.fire_evap(), "vd": cwall.vent_dry(), "mu": cwall.multipliers(),
        "sk": cwall.skin(), "cap_holes": sv.descending_seams().cap_penetrations,
    }


F = _facts()


def deg(x: float, places: int = 0) -> str:
    """A temperature as the narrator should say it."""
    text = f"{abs(x):.{places}f}"
    return f"minus {text}" if x < 0 and float(text) != 0 else text


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _m():
    return cw.landmarks()


def _top(z: float = 0.9) -> np.ndarray:
    return _m().apex + np.array([0.0, 0.0, z])


def ease(p: float) -> float:
    return shots.ease(p)


def _rng(seed: int):
    return np.random.default_rng(seed)


NET_NAME = {"water": "WATER", "vacuum": "VACUUM", "bus": "BUS", "core": "CORE", "filter": "FILTER",
            "fog": "FOG", "thermal": "HEAT", "cage": "CAGE", "living": "PLANTS", "local_net": "LOCAL-NET",
            "air_in": "AIR", "airbag": "BLADDERS", "rings": "RINGS", "global": "SEAMS"}


# ----------------------------------------------------------------------
# The stack, cut open facing the camera
# ----------------------------------------------------------------------

def _cam_az(slug: str, p: float = 0.5) -> float:
    eye = np.asarray(MOVES[slug](p)[0], dtype=float)
    c = _m().dome_centre
    return round(math.degrees(math.atan2(eye[1] - c[1], eye[0] - c[0])))


def _stack(app, slug: str, p: float, explode: float, opaque=None, keys=None, order=None,
           inflate: float = 0.0, flow_keys=None, reverse=None) -> dict:
    """The cut stack for this chapter's camera (a cached static layer), and its
    contents flowing along both cut faces."""
    az = _cam_az(slug)
    sec = so.paint_stack(app, az, explode, keys, order, inflate)
    if opaque is not None:
        so.draw_flows(opaque, sec, p, keys=flow_keys, cut=so.Cut.facing(az), reverse=reverse)
    return sec


def _sec_point(sec: dict, key: str, plane: int = 1, frac: float = 0.55, out: float = 0.0) -> np.ndarray | None:
    line = so.section_line(sec, key, plane)
    if not line:
        return None
    q = np.asarray(line[min(len(line) - 1, int(frac * len(line)))], dtype=float)
    if out:
        d = q - _m().dome_centre
        q = q + d / np.linalg.norm(d) * out
    return q


def _sec_label(app, sec: dict, key: str, text: str, colour, plane: int = 1, frac: float = 0.55) -> None:
    q = _sec_point(sec, key, plane, frac)
    if q is not None:
        _label(app, q, text, colour)


# ----------------------------------------------------------------------
# Shared pictures
# ----------------------------------------------------------------------

def _bench(app, transparent, key: bool = True) -> sc.Frame:
    cw.paint(app, subject=False)
    frame = sc.paint_bench(app, "a", bundle=False, bolted=False)
    cs.paint_static(app, "bench_grooves")
    if key:
        sc.key_shell(transparent, frame, sc.tight(), 0.0)
    return frame


def _rain(opaque, p: float, count: int = 140) -> None:
    rng = _rng(4)
    m = _m()
    for _ in range(count):
        a, r = rng.uniform(0, math.tau), 4.6 * math.sqrt(rng.random())
        x, y = m.dome_centre[0] + r * math.cos(a), m.dome_centre[1] + r * math.sin(a)
        t = (rng.random() + p * 2.2) % 1.0
        z = 7.5 - 7.0 * t
        opaque.cylinder((x, y, z), (x - 0.03, y + 0.02, z - 0.22), 0.012, DRIP, 4)


def _embers(opaque, p: float, count: int = 130) -> None:
    """Embers blown over from the fire's side, down onto and past the dome."""
    rng = _rng(8)
    m = _m()
    d = -so.fire_dir()
    side = np.array([-d[1], d[0], 0.0])
    for _ in range(count):
        start = m.dome_centre - d * rng.uniform(5.0, 10.0) + side * rng.uniform(-5, 5) \
            + np.array([0, 0, rng.uniform(4.0, 8.0)])
        t = (rng.random() + p * 1.6) % 1.0
        q = start + (d * 9.0 + np.array([0, 0, -7.0])) * t
        if q[2] > 0.1:
            opaque.sphere(q, rng.uniform(0.025, 0.05), cs.EMBER, 3, 6)


def _smoke(transparent, p: float, count: int = 28) -> None:
    rng = _rng(19)
    m = _m()
    d = -so.fire_dir()
    side = np.array([-d[1], d[0], 0.0])
    for _ in range(count):
        t = (rng.random() + p * 0.5) % 1.0
        q = m.dome_centre - d * (12.0 - 14.0 * t) + side * rng.uniform(-8, 8) + np.array([0, 0, 2.0 + 6.0 * t])
        transparent.sphere(q, 0.9 + 1.4 * t, (0.30, 0.28, 0.27, 0.22 * (1 - t) + 0.05), 4, 10)


def _spray(opaque, faces, p: float, per: int = 6) -> None:
    """Water arriving on a face: drops just above it, running down it."""
    rng = _rng(13)
    for f in faces:
        h = cs.height("water", f, 0.0) + 0.06
        a, b, c = cs.inset(f, 0.12, h)
        for _k in range(per):
            u, w = rng.random(), rng.random()
            if u + w > 1:
                u, w = 1 - u, 1 - w
            q = a + (b - a) * u + (c - a) * w
            down = np.array([0.0, 0.0, -1.0])
            down = down - f.normal * np.dot(down, f.normal)
            down /= np.linalg.norm(down) + 1e-9
            q = q + down * 0.35 * ((rng.random() + p * 2.0) % 1.0)
            opaque.sphere(q, 0.035, DRIP, 3, 6)


def _hot(transparent, faces, p: float) -> None:
    glow = 0.45 + 0.25 * math.sin(p * math.tau * 3)
    for f in faces:
        cs.tile(transparent, f, cs.height("cap", f, 0.0) + 0.02, (1.0, 0.35, 0.12, glow), 0.04)


def _arrows_from(opaque, faces, h: float, colour, p: float, inward: bool, size: float = 0.30) -> None:
    for f in faces:
        for k in range(2):
            t = (k / 2 + p) % 1.0
            base = f.incentre + f.normal * (h + (0.6 - 0.5 * t if inward else 0.1 + 0.5 * t))
            d = -f.normal if inward else f.normal
            opaque.cone(base, base + d * size, size * 0.35, colour, 10)


def _fog(transparent, p: float, fill: float) -> None:
    rng = _rng(17)
    m = _m()
    top = m.dome_centre[2] + m.dome_r * fill
    for _ in range(int(40 + 160 * fill)):
        a, r = rng.uniform(0, math.tau), (m.dome_r - 0.4) * math.sqrt(rng.random())
        z = m.deck_centre[2] + 0.2 + rng.random() * (top - m.deck_centre[2])
        if np.hypot(r, z - m.dome_centre[2]) > m.dome_r - 0.3:
            continue
        drift = 0.08 * math.sin(p * 4 + a * 3)
        transparent.sphere((r * math.cos(a) + drift, r * math.sin(a), z), rng.uniform(0.25, 0.45), cs.FOG, 4, 8)


def _pillows(opaque, inflate: float) -> None:
    """The bladders round the lower half, outside the cap."""
    t = cwall.C["airbag_m"] * max(0.0, min(1.0, inflate))
    col = cs.colour("airbag", 0.95)
    for f in cs.standing():
        if not f.lower:
            continue
        h = cs.height("airbag", f, 0.0)
        a, b, c = cs.inset(f, 0.06, h)
        top = f.incentre + f.normal * (h + max(t, 0.01))
        for p, q in ((a, b), (b, c), (c, a)):
            opaque.triangle(p, q, top, col)
            opaque.triangle(q, p, top, col)


def _thermal(transparent, opaque, p: float, warm: bool) -> None:
    col = (1.0, 0.40, 0.22, 0.55) if warm else (0.35, 0.68, 1.0, 0.55)
    for f in cs.standing():
        cs.tile(transparent, f, cs.height("thermal", f, 0.0), col, 0.03)
    cone = cs.HOT if warm else cs.COOL
    for f in cs.facing(14):
        for k in range(2):
            t = (k / 2 + p * 0.8) % 1.0
            base = f.incentre + f.normal * (cs.height("thermal", f, 0.0) - 0.15 - 0.6 * t)
            d = -f.normal if warm else f.normal
            opaque.cone(base, base + d * 0.22, 0.07, cone, 8)


def _route(opaque, app, a, b, colour, text: str, rgb, lift: float = 0.0) -> None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    opaque.arrow(a, b, 0.035, colour)
    _label(app, (a + b) / 2 + np.array([0.0, 0.0, 0.25 + lift]), text, rgb)


def _skin_window(opaque, transparent, p: float, flood: float, dry: float = 0.0) -> None:
    """The dome clad, with the cap made clear on the fire's side so the water
    layer beneath it shows: the board, the water flooding down its flutes, and
    the cap over it like glass."""
    for f in cs.standing():
        hc = cs.height("cap", f, 0.0)
        if not so.fire_side(f):
            cs.tile(opaque, f, hc, tone(cs.colour("cap", 1.0), 0.9), 0.0, both=True)
            continue
        cs.tile(opaque, f, cs.height("osb", f, 0.0), cs.colour("osb", 1.0), 0.0, both=True)
        wet = max(0.0, min(1.0, flood)) * (1.0 - max(0.0, min(1.0, dry)))
        if wet > 0:
            cs.tile(transparent, f, cs.height("water", f, 0.0), (0.40, 0.78, 1.0, 0.18 + 0.30 * wet), 0.02)
            down = np.array([0.0, 0.0, -1.0]) - f.normal * f.normal[2]
            down /= np.linalg.norm(down) + 1e-9
            a, b, c = cs.inset(f, 0.10, cs.height("water", f, 0.0) + 0.012)
            rng = _rng(f.index)
            for _k in range(int(5 + 9 * wet)):
                u, w = rng.random(), rng.random()
                if u + w > 1:
                    u, w = 1 - u, 1 - w
                q = a + (b - a) * u + (c - a) * w + down * 0.45 * ((rng.random() + p * 1.8) % 1.0)
                opaque.cylinder(q, q + down * 0.22, 0.017, (0.80, 0.94, 1.0, 1.0), 6)
        cs.tile(transparent, f, hc, (0.70, 0.86, 1.0, 0.10), 0.0)


def tone(rgba, k: float) -> tuple:
    return (min(1.0, rgba[0] * k), min(1.0, rgba[1] * k), min(1.0, rgba[2] * k), 1.0)


# ----------------------------------------------------------------------
# The bench, in section: every layer over one seam
# ----------------------------------------------------------------------

SLICE = (0.0, 0.07)          # the slice of the stack drawn at the near end of the specimen
GAP_IN = 0.9                 # exploded spacing between layers in the section, inches
THICK_IN = {"osb": 7 / 16, "cap": 0.12, "cage": 0.08, "living": 0.6, "airbag": 0.45}
JUMPER = (0.96, 0.98, 1.00, 1.0)
PORT_DARK = (0.08, 0.07, 0.07, 1.0)
PLUG = (0.90, 0.20, 0.16, 1.0)


def section_offsets() -> dict:
    """Each layer's place in the section, in inches from where the sheathing bears."""
    out = {}
    off = 0.0
    for key in cs.WEATHER:
        t = THICK_IN.get(key, 0.30)
        out[key] = (off, t)
        off += t + GAP_IN
    r = sc.tight().depth_in
    off = -r - 0.25
    out["skin"] = (off, 0.25)
    for key in cs.ROOM:
        off -= GAP_IN + 0.30
        out[key] = (off, 0.30)
    return out


def owner_offsets() -> dict:
    """The section as first drawn: every layer outside the wood, in the owner's order."""
    out, off = {}, 0.0
    for key in cwall.OWNER_STACK:
        t = THICK_IN.get(key, 0.30)
        out[key] = (off, t)
        off += t + GAP_IN
    return out


def _bench_channels(batch, side: int, key: str, off: float, t: float, p: float) -> None:
    """The layer's channels where the slice ends, pulsing with what runs in them."""
    colour, share, pitch_m = so.SECTION[key][0], so.SECTION[key][1], so.SECTION[key][2]
    pitch = max(0.45, pitch_m / cs.M * 0.55)
    s0 = cs.bench_side(side)["s0"]
    k = 0
    s = s0 + 0.35
    while s < s0 + 6.8:
        r = min(t * max(share, 0.3), pitch * 0.42) * (0.85 + 0.2 * math.sin(p * 9 + k * 1.3))
        centre = cs.bench_point(side, off + t / 2, s - s0 + s0, SLICE[0] - 0.0012)
        so.disc_on(batch, centre, (0.0, -1.0, 0.0), r * cs.M, colour, 8)
        s += pitch
        k += 1


def _section(app, opaque, transparent, labels=True, offs: dict | None = None, p: float = 0.0) -> None:
    """Every layer over one seam, in section, each a solid slab with its channels
    showing on the cut. ``labels`` is True, False, or the keys to label."""
    offs = offs or section_offsets()
    a0, a1 = SLICE
    for key, (off, t) in offs.items():
        col = (0.82, 0.82, 0.80, 1.0) if key == "skin" else cs.colour(key, 1.0)
        for side in (-1, 1):
            cs.bench_slab(opaque, side, off, t, col, 7.0, a0, a1)
            if key in so.SECTION:
                _bench_channels(opaque, side, key, off, t, p)
        if key == "skin":
            continue
        mid = off + t / 2
        if cwall.LAYER[key].kind in ("sheet", "hose"):
            # The layer's own run over the seam: its global.
            bright = tuple(min(1.0, c * 1.25) for c in cs.colour(key, 1.0)[:3]) + (1.0,)
            q0, q1 = cs.bench_seam_point(mid, a0 - 0.006), cs.bench_seam_point(mid, a1 + 0.006)
            opaque.cylinder(q0, q1, 0.0060, bright, 10)
        if labels is True or (labels and key in labels):
            _label(app, cs.bench_point(1, mid, 9.0, a0), cwall.LAYER[key].label.upper(), cs.rgb(key))


def _bench_ports(opaque, app, p: float, labels: bool = True) -> None:
    """The three things a port can be: a jumper through the V (shown in section,
    at the near end), a jumper over the ridge, and a cap."""
    frame = cs.bench_frame()
    left, right = cs.bench_side(-1), cs.bench_side(1)
    hl, hr = cs.groove_hose_centre(-1), cs.groove_hose_centre(1)
    sl, sr = left["pith"] * 0.5, right["pith"] * 0.5          # halfway down each sawn face
    near = -0.003
    # Inside: drilled from each gasket down through its member, and a jumper across the V.
    for h, s in ((hl, sl), (hr, sr)):
        opaque.cylinder(frame.at(*h, near), frame.at(*s, near), 0.30 * cs.M, PORT_DARK, 10)
        opaque.sphere(frame.at(*s, near - 0.001), 0.34 * cs.M, PORT_DARK, 3, 8)
    path = [frame.at(*hl, near - 0.002), frame.at(*sl, near - 0.002), frame.at(*sr, near - 0.002),
            frame.at(*hr, near - 0.002)]
    opaque.cylinder(path[1], path[2], 0.17 * cs.M, JUMPER, 12)
    for k in range(5):
        t = (k / 5 + p * 0.9) % 1.0
        seg = min(2, int(t * 3))
        u = t * 3 - seg
        q = path[seg] + (path[seg + 1] - path[seg]) * u
        opaque.sphere(q + np.array([0.0, -0.004, 0.0]), 0.0055, (0.35, 0.75, 1.0, 1.0), 3, 6)
    # Outside: over the ridge, under where the board will lie.
    along = 0.30
    gl = left["groove"] + left["normal"] * 0.12
    gr = right["groove"] + right["normal"] * 0.12
    arc = [frame.at(*gl, along), frame.at(0.0, 1.0, along), frame.at(*gr, along)]
    for a, b in zip(arc, arc[1:]):
        opaque.cylinder(a, b, 0.17 * cs.M, JUMPER, 12)
    for k in range(4):
        t = (k / 4 + p * 0.9) % 1.0
        seg = 0 if t < 0.5 else 1
        u = t * 2 - seg
        opaque.sphere(arc[seg] + (arc[seg + 1] - arc[seg]) * u, 0.0055, (0.35, 0.75, 1.0, 1.0), 3, 6)
    # A cap: this triangle keeps to itself.
    capped = 0.14
    g = left["groove"]
    opaque.cylinder(frame.at(*(g - left["normal"] * 0.1), capped), frame.at(*(g + left["normal"] * 0.75), capped),
                    0.34 * cs.M, PLUG, 14)
    opaque.sphere(frame.at(*(g + left["normal"] * 0.75), capped), 0.34 * cs.M, PLUG, 4, 10)
    if labels:
        _label(app, frame.at(0.0, -7.4, 0.0), "INSIDE JUMPER: THROUGH THE V", WHITE)
        _label(app, frame.at(3.0, 2.8, along), "OUTSIDE JUMPER: OVER THE RIDGE", WHITE)
        _label(app, frame.at(*(g + left["normal"] * 2.4 - left["along"] * 1.5), capped), "CAPPED", RED)


# ----------------------------------------------------------------------
# Painters
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    cw.paint(app)
    _stack(app, "open", p, 0.35, opaque)
    _label(app, _top(2.3), "THE CELL WALL", AMBER)
    _label(app, _top(1.9), "EVERY LAYER RUNNING AT ONCE", WHITE)


def p_why(app, opaque, transparent, p):
    cw.paint(app)
    _stack(app, "why", p, 0.0, opaque)
    bars = so.uses_bars(opaque, ease(min(1.0, p * 1.5)))
    for key, top, count in bars[:4]:
        _label(app, top, f"{NET_NAME[key]}: {count} USES", WHITE)
    mu = F["mu"]
    _label(app, _top(2.0), f"{mu['uses']} USES FROM {mu['networks']} NETWORKS", AMBER)


def p_declared(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "loops_frame", subject=True)
    cs.paint_static(app, "seams_frame")
    _label(app, _top(0.8), "MEASURED: OFF THE SOLVER'S DOME", GREEN)


def p_cchannel(app, opaque, transparent, p):
    _bench(app, transparent, key=False)
    g = F["g"]
    _label(app, cs.bench_point(-1, 0.9, 0.0, 0.0), f"C-CHANNEL {cwall.C['groove_w_in']:.2f} x "
           f"{cwall.C['groove_d_in']:.2f} IN", AMBER)
    _label(app, cs.bench_point(1, 3.0, 2.0, 0.0), f"-{g['area_loss_pct']:.1f}% WOOD, "
           f"-{g['s_loss_pct']:.1f}% BENDING STRENGTH", WHITE)
    _label(app, cs.bench_point(1, 1.2, 1.5, 0.0), "THE HOSE-GASKET", BLUE)


def p_local(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "loops_frame", subject=True)
    pulse = 0.35 + 0.35 * (0.5 + 0.5 * math.sin(p * math.tau * 2))
    for f in cs.facing(1, lower=False):
        cs.tile(transparent, f, f.top + 0.03, (0.3, 0.9, 1.0, pulse), 0.06)
        cs.loop(opaque, f, f.top + 0.02, (0.85, 1.0, 1.0, 1.0), 0.020)
        _label(app, f.centre + f.normal * 0.9, "ONE GASKET, ONE TRIANGLE", BLUE)
    n = F["n"]
    _label(app, _top(0.8), f"{n.triangles} GASKETS, {sum(n.loop_m):.0f} M", WHITE)


def p_ports(app, opaque, transparent, p):
    _bench(app, transparent)
    _bench_ports(opaque, app, p)
    ln = F["ln"]
    _label(app, cs.bench_frame().at(1.5, 5.2, 0.0), f"3 PORTS A GASKET: {ln['ports']} IN ALL", AMBER)


def p_localnet(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "loops_frame", subject=True)
    app.static_layer("cellwall:jumpers", lambda: so.jumper_batch(True))
    ln = F["ln"]
    top = ln["max_hops_from_rim"]
    k = min(top, int(p / 0.8 * (top + 1)))
    for fi, hop in so.face_hops().items():
        if hop <= k:
            f = cs.faces()[fi]
            fade = 0.55 if hop == k else 0.32
            cs.tile(transparent, f, f.top + 0.035, (0.35, 0.70, 1.0, fade), 0.07)
    _label(app, _top(1.0), f"WATER FROM THE RIM: HOP {k} OF {top}", BLUE)
    _label(app, _top(0.6), f"{ln['jumpers']} JUMPERS, {ln['loops']} LOOPS, NO SINGLE POINT OF FAILURE", WHITE)


def p_global(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "seams_frame", subject=True)
    for band in ("lower", "upper", "cap"):
        flow(opaque, band_seams(band), p, (1.0, 0.85, 0.4, 1.0), up=band != "cap", count=2, size=0.24)
    n, c = F["n"], F["cage"]
    _label(app, _top(0.8), f"{n.seams} SEAMS: {n.global_m:.0f} M ({c['bond_ft']:.0f} FT)", AMBER)


def p_rings(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "rings", subject=True)
    m, n = _m(), F["n"]
    for z, length in zip(cs.ring_heights(), n.ring_m):
        rad = math.sqrt(max(m.dome_r ** 2 - z * z, 0.0)) + 0.24
        d = np.array(cw.HERO_EYE) - m.dome_centre
        d[2] = 0
        d /= np.linalg.norm(d)
        side = np.array([-d[1], d[0], 0.0])
        _label(app, m.dome_centre + (d * 0.55 + side * 0.83) * rad + np.array([0, 0, z]),
               f"RING {length:.1f} M", AMBER)
    _label(app, cs.rim_corners()[0] + np.array([0, 0, -0.3]), f"RIM {n.rim_m:.1f} M", WHITE)


def p_seamroom(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    r = F["room"]
    big = p < 0.5
    od = r["big_od_in"] if big else r["small_od_in"]
    count = r["big_fit"] if big else r["small_fit"]
    keys = [l.key for l in cwall.LAYERS if l.kind in ("sheet", "hose")]
    for k, c in enumerate(cs.pack_key(od, count)):
        col = cs.colour(keys[k], 1.0) if k < len(keys) else (0.6, 0.6, 0.62, 1.0)
        opaque.cylinder(frame.at(*c, -0.01), frame.at(*c, sc.SPECIMEN_LEN + 0.01), od / 2 * cs.M, col, 16)
    text = (f"1 IN RUNS: {r['big_fit']} FIT" if big else f"3/8 IN RUNS: {r['small_fit']} FIT")
    _label(app, frame.at(0.0, 0.9, 0.0), text, AMBER)
    _label(app, frame.at(0.0, -7.6, 0.0), f"THE TIGHTEST KEY: {r['inside_in2']:.1f} SQ IN INSIDE", WHITE)


def p_address(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "nodes", subject=True)
    seams = cs.seam_runs(TriangleBatch(), -0.07, cs.colour("bus", 1.0))
    for a, b in seams:
        transparent.cylinder(a, b, 0.008, (0.45, 0.50, 1.0, 0.8), 4)
    gate = min(cs.rim_corners(), key=lambda c: np.linalg.norm(c - np.array(cw.HERO_EYE)))
    box = gate + np.array([0.0, 0.0, 0.35])
    opaque.box(box, (0.26, 0.18, 0.30), (0.20, 0.22, 0.30, 1.0))
    for f in cs.facing(6):
        node = f.centre + f.normal * (f.bottom - 0.05)
        for k in range(2):
            t = (k / 2 + p * 1.5) % 1.0
            opaque.sphere(node + (box - node) * t, 0.045, (0.70, 0.75, 1.0, 1.0), 4, 8)
    b = F["bus"]
    _label(app, _top(0.8), f"{b['nodes']} NODES, ONE PAIR OF WIRES", BLUE)
    _label(app, box + np.array([0.0, 0.0, 0.45]), "THE CONTROLLER", WHITE)


def p_monolithic(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    tx, ty = so.TABLE
    app.static_layer("cellwall:swatches", so.swatch_batch,
                     [np.array([tx, ty, so.TABLE_TOP]), np.array([tx, ty, 2.25]),
                      np.array([tx + 0.8, ty, 1.5]), np.array([tx - 0.3, ty, 1.5])])
    so.swatch_flows(opaque, p)
    for key in so.SWATCH_ORDER:
        if key != "skin":
            _label(app, so.swatch_label_point(key), so.swatch_label(key), cs.rgb(key) if key != "core" else WHITE)


def p_quilt(app, opaque, transparent, p):
    cw.paint(app)
    h = float(np.mean([f.top for f in cs.faces()])) + 0.30
    app.static_layer("cellwall:quilt", lambda: so.quilt_batch(h), cs._subject("quilt"))
    _label(app, _top(1.4), f"{F['n'].triangles} PATCHES, {F['n'].triangles} CELLS", AMBER)
    _label(app, _top(1.0), "CHANNELS RUN IN THE STITCHING", WHITE)


def p_stack(app, opaque, transparent, p):
    cw.paint(app)
    sec = _stack(app, "stack", p, 0.55, keys=cwall.OWNER_STACK + ("core", "skin"), order=cwall.OWNER_STACK)
    _sec_label(app, sec, "water", "WATER: NEAREST THE WOOD", cs.rgb("water"), 1, 0.5)
    _sec_label(app, sec, "living", "PLANTS: ON TOP", cs.rgb("living"), 2, 0.5)
    _sec_label(app, sec, "thermal", "HEAT: OUTSIDE THE WOOD", cs.rgb("thermal"), 2, 0.25)
    _label(app, _top(2.4), "AS FIRST DRAWN: ALL OUTSIDE THE WOOD", AMBER)


def p_sides(app, opaque, transparent, p):
    """The section as first drawn, then each layer moving to its side of the foam."""
    _bench(app, transparent)
    move = ease(min(1.0, max(0.0, (p - 0.12) / 0.55)))
    first, final = owner_offsets(), section_offsets()
    offs = {}
    for key in cwall.OWNER_STACK:
        a, b = first[key], final[key]
        offs[key] = (a[0] + (b[0] - a[0]) * move, b[1])
    if move > 0.97:
        offs["skin"], offs["bus"] = final["skin"], final["bus"]
    _section(app, opaque, transparent, labels=("thermal", "air_in", "fog"), offs=offs, p=p)
    prof = F["prof"]
    top = max(o + t for o, t in offs.values())
    bottom = min(o for o, _t in offs.values())
    _label(app, cs.bench_point(-1, top + 1.5, 0.0, 0.0), f"WEATHER SIDE {prof['water']:.0f} C", BLUE)
    if move > 0.5:
        _label(app, cs.bench_point(-1, bottom - 1.2, 0.0, 0.0), f"ROOM SIDE {prof['thermal']:.0f} C", RED)


def p_section(app, opaque, transparent, p):
    _bench(app, transparent)
    _section(app, opaque, transparent, p=p)
    _bench_ports(opaque, app, p, labels=False)


def p_cutaway(app, opaque, transparent, p):
    cw.paint(app)
    sec = _stack(app, "cutaway", p, 0.30, opaque)
    for key, frac, plane in (("thermal", 0.35, 2), ("air_in", 0.55, 2), ("water", 0.40, 1),
                             ("filter", 0.62, 1), ("vacuum", 0.80, 1)):
        _sec_label(app, sec, key, cwall.LAYER[key].label.upper(), cs.rgb(key), plane, frac)


def p_glue(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    drop = 1.0 - ease(min(1.0, p / 0.35))
    for side in (-1, 1):
        cs.bench_slab(opaque, side, 3.0 * drop, 7 / 16, cs.colour("osb", 1.0), 7.0)
    if p > 0.30:
        for side in (-1, 1):
            c = cs.groove_hose_centre(side)
            g = cs.bench_side(side)
            bead = c + g["normal"] * 0.22
            opaque.cylinder(frame.at(*bead, 0.0), frame.at(*bead, sc.SPECIMEN_LEN), 0.12 * cs.M, cs.GLUE, 10)
    gl, v = F["glue"], F["vac"]
    if p > 0.5:
        for side in (-1, 1):
            for along in (0.15, 0.45, 0.75):
                for k in range(2):
                    t = (k / 2 + p * 1.4) % 1.0
                    top = cs.bench_point(side, 3.2 - 2.2 * t, 3.0, along)
                    opaque.cone(top, top - np.array([0.0, 0.0, 0.03]), 0.012, cs.colour("vacuum", 1.0), 8)
        _label(app, cs.bench_point(1, 5.0, 4.0, 0.0), f"CLAMP 1 KPA: {v['sheet_kg']:.0f} KG ON A PANEL",
               PURPLE)
    _label(app, cs.bench_point(-1, 4.2, 2.0, 0.0), f"GLUE: {gl['bead_cartridges']} CARTRIDGES, "
           f"NOT {gl['flood_cartridges']}", AMBER)


def _cavity_fill(opaque, frac: float) -> None:
    """Foam rising in every triangle's cavity, from its low side, in lifts."""
    w = cs.member_width()
    for f in cs.standing():
        a, b, c = cs.inset(f, w, 0.0)
        zs = [a[2], b[2], c[2]]
        z_cut = min(zs) + (max(zs) - min(zs)) * frac
        poly = _clip_below([a, b, c], z_cut)
        if len(poly) < 3:
            continue
        lo, hi = f.bottom + 0.01, f.top - 0.03
        bottom = [q + f.normal * lo for q in poly]
        top = [q + f.normal * hi for q in poly]
        for i in range(1, len(poly) - 1):
            opaque.triangle(top[0], top[i], top[i + 1], cs.FOAM, f.normal)
            opaque.triangle(top[0], top[i + 1], top[i], cs.FOAM, f.normal)
        for i in range(len(poly)):
            j = (i + 1) % len(poly)
            opaque.quad(bottom[i], bottom[j], top[j], top[i], cs.FOAM)
            opaque.quad(bottom[i], top[i], top[j], bottom[j], cs.FOAM)


def _clip_below(poly, z: float) -> list:
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        if p[2] <= z:
            out.append(p)
        if (p[2] - z) * (q[2] - z) < 0:
            t = (z - p[2]) / (q[2] - p[2])
            out.append(p + (q - p) * t)
    return out


def p_foam(app, opaque, transparent, p):
    cw.paint(app)
    lifts = F["foam"]["lifts"]
    k = min(lifts, int(p * lifts * 1.15))
    within = min(1.0, (p * lifts * 1.15 - k) * 1.6) if k < lifts else 0.0
    frac = min(1.0, (k + within) / lifts)
    _cavity_fill(opaque, max(0.04, frac))
    cs.shell(transparent, "osb", 0.0, 0.30)
    fo = F["foam"]
    _label(app, _top(0.9), f"LIFT {min(lifts, k + 1)} OF {lifts}: {fo['per_lift_l']:.0f} L A TRIANGLE", AMBER)
    _label(app, _top(0.5), f"R-{fo['r_imperial']:.0f}, {fo['kits']} KITS, ${fo['usd']:,.0f}", WHITE)


def p_oneway(app, opaque, transparent, p):
    cw.paint(app)
    _cavity_fill(opaque, 1.0)
    cs.shell(transparent, "osb", 0.0, 0.30)
    for f in cs.facing(12):
        cs.loop(opaque, f, f.top + 0.010, (1.0, 0.25, 0.2, 1.0), 0.020)
    fi = F["fire"]
    _label(app, _top(0.9), "AGAINST: ONE-WAY DOORS", RED)
    _label(app, _top(0.5), f"A HOLLOW CORE SOAKS ITS FRAME IN {fi['soak_l']:.0f} L; A FOAMED ONE CANNOT", WHITE)


def p_water(app, opaque, transparent, p):
    cw.paint(app)
    cs.shell(transparent, "water", 0.0, 0.40)
    cs.paint_static(app, "tank", subject=True)
    _rain(opaque, p)
    flow(opaque, band_seams("lower"), p, cs.WATER, up=False, count=2, size=0.24)
    ra = F["rain"]
    _label(app, _top(0.9), f"{ra['gal_year']:,.0f} GAL OF RAIN A YEAR", BLUE)
    _label(app, cs.tank_top() + np.array([0.0, 0.0, 0.4]),
           f"{ra['tank_gal']:.0f} GAL TANK: FILLS {ra['tank_fills']:.0f} TIMES", WHITE)


def p_filter(app, opaque, transparent, p):
    cw.paint(app)
    cs.shell(transparent, "filter", 0.0, 0.45)
    cs.shell(transparent, "air_in", 0.0, 0.35)
    m = _m()
    for c in cs.rim_corners():
        d = np.array([c[0] - m.dome_centre[0], c[1] - m.dome_centre[1], 0.0])
        d /= np.linalg.norm(d)
        for k in range(2):
            t = (k / 2 + p) % 1.0
            q = c + d * 0.45 + np.array([0.0, 0.0, -0.25 + 0.4 * t])
            opaque.cone(q, q + np.array([0.0, 0.0, 0.15]), 0.06, AIRFLOW, 8)
    for f in cs.facing(10):
        up = np.array([0.0, 0.0, 1.0]) - f.normal * f.normal[2]
        up /= np.linalg.norm(up) + 1e-9
        t = (p * 0.35 + f.index * 0.13) % 1.0
        q = f.incentre + f.normal * cs.height("filter", f, 0.0) + up * (t - 0.5) * 0.6
        opaque.cone(q, q + up * 0.12, 0.035, AIRFLOW, 8)
    a = F["air"]
    _label(app, _top(0.9), f"{a['ratio']:,.0f} x SLOWER THAN A FURNACE FILTER", GREEN)
    _label(app, _top(0.5), f"HEAT PICKED UP: {a['recovered_w']:.0f} W OF {a['wall_loss_w']:.0f}", WHITE)


def p_vent(app, opaque, transparent, p):
    cw.paint(app)
    az = _cam_az("vent")
    sec = so.paint_stack(app, az, 0.30)
    cut = so.Cut.facing(az)
    for plane, n in ((1, cut.n1), (2, cut.n2)):
        so.flow_along(opaque, so.section_line(sec, "water", plane), p, DRY_AIR, 1, "cone", 10, 0.09, n)
    m = _m()
    rng = _rng(23)
    for c in cs.rim_corners():
        if cut.removed(c):
            continue
        d = np.array([c[0] - m.dome_centre[0], c[1] - m.dome_centre[1], 0.0])
        d /= np.linalg.norm(d)
        for _k in range(2):
            t = (rng.random() + p * 0.8) % 1.0
            transparent.sphere(c + d * (0.5 + 0.6 * t) + np.array([0, 0, 0.3 + 0.5 * t]), 0.08 + 0.12 * t,
                               (0.95, 0.96, 1.0, 0.45 * (1 - t)), 4, 8)
    vd = F["vd"]
    _sec_label(app, sec, "water", f"DRY AIR THROUGH THE FLUTES: {vd['kg_h']:.1f} KG/H", BLUE, 1, 0.45)
    _label(app, _top(2.0), f"DRY IN {vd['hours']:.0f} HOURS, NOT {vd['hours_house_air']:.0f}", AMBER)


def p_declared2(app, opaque, transparent, p):
    cw.paint(app)
    _stack(app, "declared2", p, 0.55, opaque)
    _label(app, _top(2.0), "DECLARED: THE SERVICES", AMBER)


def p_warm(app, opaque, transparent, p):
    cw.paint(app)
    _thermal(transparent, opaque, p, warm=True)
    h = F["heat"]
    _label(app, _top(0.9), f"A WALL {h['needed_dt_k']:.1f} K WARMER THAN THE ROOM", RED)
    _label(app, _top(0.5), f"LOSS {h['loss_w']:.0f} W AT {F['C']['winter_out_c']:.0f} C", WHITE)


def p_cool(app, opaque, transparent, p):
    cw.paint(app)
    _thermal(transparent, opaque, p, warm=False)
    cs.shell(transparent, "water", 0.0, 0.30)
    c = F["cool"]
    _label(app, _top(0.9), f"WALL NO COLDER THAN {c['surface_c']:.1f} C", BLUE)
    _label(app, _top(0.5), f"{c['capacity_w'] / 1000:.1f} KW vs THE PELTIER RING'S {c['peltier_ring_w']:.0f} W",
           WHITE)


def p_vacuum(app, opaque, transparent, p):
    cw.paint(app)
    f = max(cs.facing(8), key=lambda f: f.inradius)
    v = F["vac"]
    if p < 0.5:
        cs.tile(transparent, f, cs.height("vacuum", f, 0.0), cs.colour("vacuum", 0.6), 0.03)
        _arrows_from(opaque, [f], cs.height("cap", f, 0.0), cs.colour("vacuum", 1.0), p, inward=True)
        _arrows_from(opaque, [f], cs.height("cap", f, 0.0) + 0.05, (0.85, 0.85, 0.9, 1.0), p, inward=False,
                     size=0.22)
        _label(app, _top(0.9), f"CLAMP {v['sheet_kn']:.2f} KN vs GUST {v['wind_kn']:.2f} KN", PURPLE)
        _label(app, _top(0.5), "THE CLAMP HOLDS THE SKIN DOWN", WHITE)
    else:
        cs.tile(transparent, f, cs.height("vacuum", f, 0.0), (1.0, 0.25, 0.2, 0.65), 0.03)
        _arrows_from(opaque, [f], cs.height("cap", f, 0.0), (1.0, 0.3, 0.25, 1.0), p, inward=True, size=0.45)
        _label(app, _top(0.9), f"25 KPA ON A SHEET: {v['hose_tonnes']:.1f} T", RED)
        _label(app, _top(0.5), f"HARD VACUUM: {v['hard_tonnes']:.0f} T ON ONE PANEL", RED)


def p_levels(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "rim_vacuum", subject=True)
    cs.shell(transparent, "water", 0.35, 0.22)
    cs.shell(transparent, "vacuum", 0.35, 0.22)
    m = _m()
    gate = min(cs.rim_corners(), key=lambda c: np.linalg.norm(c - np.array(cw.HERO_EYE)))
    out = np.array([gate[0] - m.dome_centre[0], gate[1] - m.dome_centre[1], 0.0])
    out /= np.linalg.norm(out)
    reg = gate + out * 0.30 + np.array([0.0, 0.0, 0.45])
    opaque.box(reg, (0.20, 0.20, 0.26), (0.35, 0.25, 0.45, 1.0))
    for c in cs.rim_corners():
        d = np.array([c[0] - m.dome_centre[0], c[1] - m.dome_centre[1], 0.0])
        d /= np.linalg.norm(d)
        opaque.box(c + d * 0.42 + np.array([0.0, 0.0, 0.10]), (0.10, 0.10, 0.10), (0.85, 0.85, 0.88, 1.0))
    levels = F["vac"]["levels"]
    _label(app, reg + np.array([0.0, 0.0, 0.5]), f"RIM RING {levels[0][1]:.0f} KPA: HOSES ONLY", PURPLE)
    f = cs.facing(1, lower=True)[0]
    _label(app, f.centre + f.normal * cs.height("water", f, 0.35) + np.array([0, 0, 0.3]),
           f"WATER DRAW {levels[1][1]:.0f} KPA", BLUE)
    g = cs.facing(1, lower=False)[0]
    _label(app, g.centre + g.normal * cs.height("vacuum", g, 0.35), f"CLAMP {levels[2][1]:.0f} KPA", PURPLE)


def p_firethreat(app, opaque, transparent, p):
    cw.paint(app)
    so.fire_front(opaque, p)
    _embers(opaque, p)
    _smoke(transparent, p)
    hot = [f for f in cs.standing() if so.fire_side(f)]
    so.radiant(opaque, hot[::2], p)
    C = F["C"]
    _label(app, _top(1.2), f"BAL-29: {C['bal_kw_m2']:.0f} KW ON EVERY M2", RED)
    _label(app, _top(0.8), f"FLAME ZONE: OVER {C['flame_zone_kw_m2']:.0f}", WHITE)


def p_fireseal(app, opaque, transparent, p):
    cw.paint(app)
    shut = ease(min(1.0, max(0.0, (p - 0.12) / 0.4)))
    ports = so.intakes(opaque, shut)
    _embers(opaque, p, 90)
    _smoke(transparent, p, 18)
    near = min(ports, key=lambda q: np.linalg.norm(q - np.array(cw.HERO_EYE)))
    ln = F["ln"]
    _label(app, near + np.array([0, 0, 0.55]), "INTAKES SHUT" if shut > 0.5 else "INTAKES OPEN", RED if shut > 0.5 else WHITE)
    _label(app, _top(0.9), f"{ln['rim_ports']} INTAKES CLOSED; THE CAP HAS NO OPENINGS", AMBER)


def p_fireflood(app, opaque, transparent, p):
    cw.paint(app)
    flood = ease(min(1.0, p / 0.35))
    _skin_window(opaque, transparent, p, flood)
    hot = [f for f in cs.standing() if so.fire_side(f)]
    so.radiant(opaque, hot[::2], p)
    if flood > 0.5:
        so.steam(transparent, hot, p)
    _embers(opaque, p, 70)
    fe, fi = F["fe"], F["fire"]
    _label(app, _top(1.2), f"METERED: {fe['gpm']:.1f} GPM, NOT {fi['gpm']:.0f}", BLUE)
    _label(app, _top(0.8), f"THE TANK LASTS {fe['tank_min']:.0f} MIN, NOT {fi['tank_min']:.1f}", AMBER)


def p_fireaim(app, opaque, transparent, p):
    cw.paint(app)
    _embers(opaque, p)
    hot = cs.facing(3, toward=_m().dome_centre + so.fire_dir() * 12 + np.array([0, 0, 2]))
    _hot(transparent, hot, p)
    _spray(opaque, hot, p, per=10)
    fi = F["fire"]
    _label(app, hot[0].centre + hot[0].normal * 0.9, f"ONE TRIANGLE: {fi['one_min']:.0f} MIN", GREEN)
    _label(app, _top(0.9), "WATER ONLY WHERE THE EMBERS LAND", WHITE)


def p_fireafter(app, opaque, transparent, p):
    cw.paint(app)
    _skin_window(opaque, transparent, p, 1.0, dry=ease(p))
    hot = [f for f in cs.standing() if so.fire_side(f)]
    for f in hot[::2]:
        up = np.array([0.0, 0.0, 1.0]) - f.normal * f.normal[2]
        up /= np.linalg.norm(up) + 1e-9
        for k in range(2):
            t = (k / 2 + p * 0.9) % 1.0
            q = f.incentre + f.normal * (cs.height("water", f, 0.0) + 0.04) + up * (t - 0.5) * 0.7
            opaque.cone(q, q + up * 0.14, 0.04, DRY_AIR, 8)
    _smoke(transparent, p * 0.3, 8)
    vd, x = F["vd"], F["x"]
    _label(app, _top(1.2), f"DRY IN {vd['hours']:.0f} HOURS", BLUE)
    _label(app, _top(0.8), f"DAMAGE FOUND IN {x['leak_tests']} TESTS", WHITE)


def p_cage(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "cage", subject=True)
    m = _m()
    if 0.25 < p < 0.36:
        rng = _rng(int(p * 400))
        a = m.apex + np.array([1.4, 1.0, 7.0])
        for k in range(8):
            b = a + (m.apex + np.array([0, 0, 0.25]) - a) / (8 - k) + np.append(rng.uniform(-0.3, 0.3, 2), 0.0)
            opaque.cylinder(a, b, 0.035, (1.0, 1.0, 0.85, 1.0), 6)
            a = b
    if 0.30 < p < 0.75:
        for band in ("cap", "upper", "lower"):
            flow(opaque, band_seams(band), p, (1.0, 0.95, 0.5, 1.0), up=False, count=1, size=0.22)
    c = F["cage"]
    _label(app, _top(0.9), f"BOND ALL {c['seams']} SEAMS: {c['bond_ft']:.0f} FT", AMBER)
    _label(app, _top(0.5), f"AN OPEN DOOR LETS IN ALL ABOVE {c['door_cutoff_mhz']:.0f} MHZ", RED)


def p_fog(app, opaque, transparent, p):
    cw.paint(app)
    fill = ease(min(1.0, p / 0.45))
    if p < 0.62:
        _fog(transparent, p, fill)
    else:
        _fog(transparent, p, max(0.2, 1.0 - (p - 0.62) * 2.2))
        for band in ("cap", "upper", "lower"):
            flow(opaque, band_seams(band), p, SMOKE, up=False, count=2, size=0.26)
    fg = F["fog"]
    _label(app, _top(0.9), f"FOG: {fg['volume_m3']:.0f} M3 IN {fg['seconds']:.0f} S", WHITE)
    _label(app, _top(0.5), "NOT PEPPER" if p < 0.62 else "BACKWARDS: SMOKE OUT", RED if p < 0.62 else AMBER)


def p_airbag(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "posts")
    cs.paint_static(app, "tank")
    m = _m()
    fl = F["fl"]
    rim = m.dome_centre[2]
    if p < 0.55:
        level = 0.15 + (rim + fl["bag_waterline_m"] - 0.15) * ease(min(1.0, p / 0.45))
        _pillows(opaque, ease(min(1.0, max(0.0, (p - 0.1) / 0.35))))
        _label(app, _top(0.9), f"BLADDERS LIFT IT AT {fl['bag_waterline_m']:.1f} M OF WATER", AMBER)
        _label(app, _top(0.5), "THE FLOOR IS ALREADY UNDER", RED)
    else:
        level = rim + fl["hull_draft_m"]
        _label(app, _top(0.9), f"SEALED FLOOR: FLOATS AT {100 * fl['hull_draft_m']:.0f} CM", GREEN)
        _label(app, _top(0.5), "DRY INSIDE; GUIDE POSTS KEEP IT HOME", WHITE)
    transparent.disc(np.array([m.dome_centre[0], m.dome_centre[1], level]), 40.0, (0.25, 0.45, 0.65, 0.55), 96)


def p_twoway(app, opaque, transparent, p):
    cw.paint(app)
    out = p >= 0.5
    sec = _stack(app, "twoway", p, 0.35, opaque, flow_keys=("thermal", "air_in", "filter", "water"),
                 reverse=({"thermal", "air_in", "filter", "water"} if out else None))
    _sec_label(app, sec, "air_in", "AIR: " + ("OUT" if out else "IN"), cs.rgb("air_in"), 2, 0.55)
    _sec_label(app, sec, "thermal", "HEAT: " + ("COOL" if out else "WARM"), cs.rgb("thermal"), 2, 0.30)
    _sec_label(app, sec, "water", "WATER: " + ("BACK OUT" if out else "TO THE TANK"), cs.rgb("water"), 1, 0.45)
    _label(app, _top(2.0), "THE VALVES DECIDE THE DIRECTION", WHITE)


def p_routes(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "tank", subject=True)
    e = 0.7
    for key in ("filter", "air_in", "water", "living", "airbag", "vacuum"):
        cs.shell(transparent, key, e, 0.2)
    low = cs.facing(1, lower=True)[0]
    crown = cs.facing(1, lower=False)[0]
    gate = min(cs.rim_corners(), key=lambda c: np.linalg.norm(c - np.array(cw.HERO_EYE)))
    show = int(p * 5.5)
    a = low.centre + low.normal * cs.height("filter", low, e)
    _route(opaque, app, a, gate + np.array([0, 0, 0.3]), cs.colour("filter", 1.0), "FILTER", cs.rgb("filter"))
    _route(opaque, app, gate + np.array([0, 0, 0.3]), low.centre + low.normal * cs.height("air_in", low, e),
           cs.colour("air_in", 1.0), "TO THE ROOM", cs.rgb("air_in"), 0.2)
    if show >= 1:
        _route(opaque, app, cs.tank_top(), gate + np.array([0, 0, 0.1]), cs.colour("water", 1.0),
               "TANK", BLUE)
    if show >= 2:
        _route(opaque, app, cs.tank_top() + np.array([0, 0, 0.1]),
               crown.centre + crown.normal * cs.height("living", crown, e), cs.colour("living", 1.0),
               "FEED THE PLANTS", cs.rgb("living"), 0.3)
    if show >= 3:
        lowest = min((f for f in cs.standing() if f.lower), key=lambda f: np.linalg.norm(f.centre - cs.co2_top()))
        _route(opaque, app, cs.co2_top(), lowest.centre + lowest.normal * cs.height("airbag", lowest, e),
               cs.colour("airbag", 1.0), "CO2 TO THE BLADDERS", cs.rgb("airbag"))
    if show >= 4:
        f = cs.facing(2, lower=False)[1]
        _route(opaque, app, f.centre + f.normal * cs.height("vacuum", f, e), f.centre + f.normal * 0.08,
               cs.colour("vacuum", 1.0), "CLAMP THE CORE", PURPLE)
    _label(app, _top(2.3), f"{len(cwall.ROUTES)} ROUTES; EVERYTHING ELSE REFUSED", AMBER)


SCENE_ORDER = tuple(s[0] for s in cwall.SCENARIOS)


def _scenario_at(p: float) -> int:
    return min(len(SCENE_ORDER) - 1, int(p / 0.8 * len(SCENE_ORDER)))


def p_scenes(app, opaque, transparent, p):
    cw.paint(app)
    k = _scenario_at(p)
    key, label, modes = cwall.SCENARIOS[k]
    for layer, mode in modes.items():
        if layer in ("bus", "core") or mode == "off":
            continue
        cs.shell(transparent, layer, 0.45, 0.32)
    if key == "flood":
        _pillows(opaque, 1.0)
    if key == "intrusion":
        _fog(transparent, p, 0.8)
    _label(app, _top(2.0), label.upper(), AMBER)


def p_more(app, opaque, transparent, p):
    cw.paint(app)
    x = F["x"]
    tests = x["leak_tests"]
    order = sorted(cs.standing(), key=lambda f: f.index)
    where = [f.index for f in order].index(cs.facing(1)[0].index)
    lo, hi = 0, len(order)
    step = min(tests, int(p / 0.8 * (tests + 1)))
    for _ in range(step):
        mid = (lo + hi) // 2
        if where < mid:
            hi = mid
        else:
            lo = mid
    for i, f in enumerate(order):
        if lo <= i < hi:
            cs.tile(transparent, f, cs.height("vacuum", f, 0.0) + 0.02, (1.0, 0.45, 0.3, 0.55), 0.04)
    _label(app, _top(0.9), f"TEST {step} OF {tests}: {hi - lo} CELLS LEFT", AMBER)
    _label(app, _top(0.5), f"A SMOKE SAMPLE FROM ANY CELL IN {x['sample_s']:.0f} S", WHITE)


def p_chia(app, opaque, transparent, p):
    cw.paint(app)
    cs.paint_static(app, "plants", subject=True)
    cs.paint_static(app, "tank")
    rng = _rng(31)
    for f in cs.facing(12):
        h = cs.height("living", f, 0.0)
        for _k in range(2):
            q = f.incentre + f.normal * (h + 0.30 - 0.28 * ((rng.random() + p * 1.5) % 1.0))
            opaque.sphere(q, 0.025, DRIP, 3, 6)
    lv = F["live"]
    _label(app, _top(0.9), f"SOIL HOLDS ON {lv['plant_pct']:.0f}% OF THE DOME", GREEN)
    _label(app, _top(0.5), f"WET: {lv['wet_kg'] / 1000:.1f} T = {lv['times_frame']:.1f} x THE FRAME", WHITE)


def p_multipliers(app, opaque, transparent, p):
    cw.paint(app)
    bars = so.uses_bars(opaque, ease(min(1.0, p * 1.4)))
    for key, top, count in bars:
        if count >= 2:
            _label(app, top, f"{NET_NAME[key]} {count}", cs.rgb(key) if key in cwall.LAYER else WHITE)
    mu = F["mu"]
    _label(app, _top(2.2), f"{mu['per_network']:.1f} USES PER NETWORK", AMBER)


def p_cost(app, opaque, transparent, p):
    cw.paint(app)
    cx = F["cx"]
    if p < 0.5:
        cs.paint_static(app, "valves_every", subject=True)
        _label(app, _top(0.9), f"EVERY CELL: {cx['valves_every_cell']} VALVES", RED)
    else:
        cs.paint_static(app, "valves_band", subject=True)
        _label(app, _top(0.9), f"BY BAND: {cx['valves_by_band']} VALVES", GREEN)
    _label(app, _top(0.5), f"{cx['joints']:,} JOINTS, EACH ONE A LEAK", WHITE)


def p_close(app, opaque, transparent, p):
    cw.paint(app)
    _stack(app, "close", p, 0.05, opaque)
    _label(app, _top(2.0), "THE SKIN IS AN ORGAN", AMBER)


SCENES = {
    "open": p_open, "why": p_why, "declared": p_declared, "cchannel": p_cchannel, "local": p_local,
    "ports": p_ports, "localnet": p_localnet, "global": p_global, "seamroom": p_seamroom, "rings": p_rings,
    "address": p_address, "monolithic": p_monolithic, "quilt": p_quilt, "stack": p_stack, "sides": p_sides,
    "section": p_section, "cutaway": p_cutaway, "glue": p_glue, "foam": p_foam, "oneway": p_oneway,
    "water": p_water, "filter": p_filter, "vent": p_vent, "declared2": p_declared2, "warm": p_warm,
    "cool": p_cool, "vacuum": p_vacuum, "levels": p_levels, "firethreat": p_firethreat,
    "fireseal": p_fireseal, "fireflood": p_fireflood, "fireaim": p_fireaim, "fireafter": p_fireafter,
    "cage": p_cage, "fog": p_fog, "airbag": p_airbag, "twoway": p_twoway, "routes": p_routes,
    "scenes": p_scenes, "more": p_more, "chia": p_chia, "multipliers": p_multipliers, "cost": p_cost,
    "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

MATH = ("declared", "declared2", "scenes", "monolithic")


def beside_worksheet(shot):
    """Slide the camera right so the subject sits left of a math chapter's worksheet."""
    def moved(p: float):
        eye, target, fov = shot(p)
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        f = target - eye
        d = np.linalg.norm(f)
        f /= d
        right = np.cross(f, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        k = 0.40 * d * math.tan(math.radians(fov) / 2) * 16 / 9
        return eye + right * k, target + right * k, fov
    return moved


def _moves() -> dict:
    m = cw.landmarks()
    dome = m.dome_centre + [0, 0, m.dome_r * 0.45]
    high = m.dome_centre + [0, 0, m.dome_r * 0.62]
    tank = cs.tank_spot()
    wet = dome + np.array([0.35 * (tank[0] - dome[0]), 0.35 * (tank[1] - dome[1]), -0.35])
    near = cs.bench_frame().near
    tx, ty = so.TABLE
    north = m.dome_centre + so.fire_dir() * 1.0
    close = shots.push_in(near + [-0.07, 0.10, 0.0], near + [0.30, -0.85, 0.26],
                          near + [0.18, -0.58, 0.16], fov_start=38, fov_end=33)
    keyview = shots.push_in(near + [0.0, 0.10, -0.06], near + [0.26, -0.80, 0.10],
                            near + [0.16, -0.55, 0.05], 38, 34)
    portview = shots.push_in(near + [0.0, 0.22, 0.02], near + [0.45, -0.95, 0.38],
                             near + [0.34, -0.72, 0.30], 42, 38)
    sect = shots.push_in(near + [0.10, 0.0, 0.05], near + [0.62, -1.55, 0.30],
                         near + [0.50, -1.25, 0.22], 42, 40)
    glue = shots.push_in(near + [0.0, 0.25, 0.04], near + [0.48, -1.00, 0.42],
                         near + [0.36, -0.78, 0.33], 40, 36)
    table = {
        "open": shots.crane_reveal(high, np.array(cw.HERO_EYE) + [0, 4.0, -1.9],
                                   np.array(cw.HERO_EYE) + [0.4, -0.6, 1.4], 44, 48, look_start=dome),
        "why": shots.orbit(dome + [0, 0, -0.2], 13.0, 3.4, -100, 20, 48),
        "declared": shots.orbit(dome, 11.5, 3.2, -105, 25, 46),
        "cchannel": close,
        "local": shots.orbit(dome, 9.0, 4.2, -115, 30, 46),
        "ports": portview,
        "localnet": shots.orbit(dome, 9.5, 4.4, -100, 30, 46),
        "global": shots.orbit(dome, 9.5, 3.6, -80, -30, 46),
        "seamroom": keyview,
        "rings": shots.orbit(dome, 10.5, 2.4, -120, 35, 46),
        "address": shots.orbit(dome, 9.0, 2.6, -95, 30, 48),
        "monolithic": shots.push_in((tx + 0.15, ty, 1.48), (tx + 1.5, ty - 3.4, 1.95), (tx + 1.25, ty - 3.0, 1.9),
                                    46, 44),
        "quilt": shots.orbit(dome, 11.0, 3.6, -120, 40, 46),
        "stack": shots.orbit(high, 12.5, 3.4, -100, 18, 46),
        "sides": sect,
        "section": sect,
        "cutaway": shots.push_in(high, m.dome_centre + [1.2, -10.5, 3.2], m.dome_centre + [0.8, -8.2, 2.6], 46, 44),
        "glue": glue,
        "foam": shots.orbit(dome, 9.0, 4.6, -100, 35, 46),
        "oneway": shots.orbit(dome, 9.5, 3.8, -70, -25, 46),
        "water": shots.orbit(wet, 11.0, 3.4, -100, 22, 46),
        "filter": shots.orbit(dome, 10.0, 2.6, -85, -30, 46),
        "vent": shots.orbit(high, 11.5, 3.0, -95, 16, 46),
        "declared2": shots.orbit(high, 13.0, 3.6, -100, 18, 46),
        "warm": shots.orbit(dome, 9.5, 3.4, -110, 30, 46),
        "cool": shots.orbit(dome, 9.5, 3.4, -70, -30, 46),
        "vacuum": shots.orbit(dome, 8.8, 2.8, -100, 20, 46),
        "levels": shots.low_hero(m.dome_centre + [0, 0, 0.8], 8.5, eye_height=1.4, start_deg=-120,
                                 sweep_deg=40, look_up=0.6, fov=48),
        # The fire comes up the valley to the north: look past the dome into it.
        "firethreat": shots.crane_reveal(north + [0, 2.5, 1.2], m.dome_centre + [-1.5, -9.0, 2.0],
                                         m.dome_centre + [-2.4, -12.0, 5.2], 46, 52, look_start=dome),
        "fireseal": shots.low_hero(m.dome_centre + [0, 0, 0.7], 7.6, eye_height=1.1, start_deg=-115,
                                   sweep_deg=30, look_up=0.5, fov=50),
        "fireflood": shots.orbit(dome, 10.5, 3.2, 62, 26, 48),
        "fireaim": shots.orbit(dome, 9.8, 3.4, 112, -24, 46),
        "fireafter": shots.orbit(dome, 10.5, 3.6, 70, -20, 46),
        "cage": shots.orbit(dome, 11.5, 4.2, -100, 30, 46),
        "fog": shots.orbit(dome, 8.8, 2.4, -95, 25, 46),
        "airbag": shots.orbit(dome, 12.0, 3.4, -120, 40, 46),
        "twoway": shots.orbit(high, 11.0, 3.0, -90, 16, 46),
        "routes": shots.orbit(high, 12.5, 4.4, -125, 40, 46),
        "scenes": shots.orbit(high, 12.0, 3.6, -95, 30, 46),
        "more": shots.orbit(dome, 10.0, 3.6, -80, -30, 46),
        "chia": shots.orbit(dome, 9.0, 4.8, -110, 40, 46),
        "multipliers": shots.orbit(dome + [0, 0, -0.2], 13.5, 3.8, -110, 30, 48),
        "cost": shots.orbit(dome, 9.5, 3.2, -95, 30, 46),
        "close": shots.crane_reveal(high, np.array(cw.HERO_EYE) + [0.4, 3.0, -1.4],
                                    np.array(cw.HERO_EYE) + [1.2, -1.5, 2.2], 44, 50, look_start=dome),
    }
    out = {}
    for slug, shot in table.items():
        if slug in MATH:
            shot = beside_worksheet(shot)
        out[slug] = cabin_stage.clear_view(shot, cabin_stage.safe)
    return out


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

SHORT = {"thermal": "heat/cool", "air_in": "air in", "fog": "fog", "bus": "bus", "core": "core",
         "osb": "OSB", "water": "water", "filter": "filter", "vacuum": "vacuum", "cage": "cage",
         "cap": "cap", "airbag": "bladders", "living": "plants", "tank": "tank", "co2": "CO2",
         "outside": "outside"}
"""Names short enough for a card."""


def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=(),
        overlay: str | None = None) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, overlay)


def _declared_steps() -> list[str]:
    n, k, C = F["n"], F["kinds"], F["C"]
    typed = len(cwall.CONSTANTS)
    return [
        "MEASURED, off the solver's own dome:",
        f"   {n.triangles} triangles, {n.seams} seams, {n.shell_m2:.1f} m2 of shell",
        f"   gaskets {sum(n.loop_m):.0f} m, seams {n.global_m:.0f} m, rim {n.rim_m:.1f} m",
        f"DECLARED, typed in by a person: {typed}, a reason each",
        f"   {k.get('assumption', 0)} assumptions, {k.get('estimate', 0)} estimates, "
        f"{k.get('nominal', 0)} product sizes, {k.get('standard', 0)} standards",
        f"   groove {C['groove_w_in']:.2f} x {C['groove_d_in']:.2f} in; hoses {C['local_hose_id_mm']:.0f} and "
        f"{C['global_hose_id_mm']:.0f} mm bore (assumed)",
        f"   foam R-{C['foam_r_per_in']:.0f}/in; a {C['foam_kit_bdft']:.0f} bd-ft kit ${C['foam_kit_usd']:.0f} (estimate)",
        f"   clamp {C['sheet_vacuum_kpa']:.0f} kPa, central vac {C['hose_vacuum_kpa']:.0f} kPa, "
        f"gust {C['wind_gust_m_s']:.0f} m/s (assumed)",
        f"   wetting {C['wetting_gpm_ft2']:.2f} gpm/ft2 (NFPA 13 light hazard)",
        "every figure after this reads the table",
    ]


def _declared2_steps() -> list[str]:
    C = F["C"]
    return [
        "DECLARED for the services:",
        f"   warm wall {C['heating_dt_k']:.0f} K over the room; h = {C['radiant_h']:.0f} W/m2K (estimate)",
        f"   design night {C['winter_out_c']:.0f} C, room {C['room_c']:.0f} C (assumed)",
        f"   fire: BAL-29 {C['bal_kw_m2']:.0f} kW/m2, flame zone {C['flame_zone_kw_m2']:.0f} (standard)",
        f"   water takes {C['latent_mj_kg']:.2f} MJ/kg to boil off (standard)",
        f"   embers {C['ember_minutes']:.0f} min; a {C['flood_film_mm']:.1f} mm film; a {C['purge_cfm']:.0f} cfm fan (assumed)",
        f"   mesh {C['mesh_aperture_mm']:.2f} mm, door {C['door_w_m']:.1f} m, Wi-Fi {C['wifi_ghz']:.1f} GHz",
        f"   floor and contents {C['floor_kg_m2']:.0f} kg/m2; bladders {100 * C['airbag_m']:.0f} cm deep (assumed)",
        f"   soil holds to {C['plant_max_slope_deg']:.0f} deg; wet {C['green_kg_m2']:.0f} kg/m2, felt "
        f"{C['felt_kg_m2']:.0f} (estimates)",
        "each one marked where it is used",
    ]


def _material_steps() -> list[str]:
    lines = []
    for key in cs.ROOM[::-1] + ("core",) + cs.WEATHER:
        what, how, body, _mm, kind = cwall.CONSTRUCTION[key]
        lines.append(f"{so.SWATCH_NAME[key].lower()}: {what}, {cwall.thickness_mm(key):.0f} mm, {body} ({kind})")
    sk = F["sk"]
    lines.append(f"skin: {sk['weather_mm']:.0f} mm outside the frame, {sk['room_mm']:.0f} mm inside")
    return lines


def _scene_steps() -> list[str]:
    short = {"thermal": {"heat": "wall warm", "cool": "wall cool"},
             "air_in": {"supply": "air in"}, "filter": {"intake": "filtered"},
             "water": {"drain": "water drained", "capture": "rain to tank", "flood": "FLOOD",
                       "circulate": "water under the sky"},
             "vacuum": {"clamp": "clamp"}, "fog": {"fog": "FOG", "smoke_exhaust": "smoke out"},
             "airbag": {"inflate": "BLADDERS"}, "living": {"irrigate": "plants watered"},
             "core": {"inject_glue": "glue in"}}
    lines = []
    for _key, label, modes in cwall.SCENARIOS:
        parts = [short.get(k, {}).get(v, "") for k, v in modes.items()]
        lines.append(f"{label}: " + ", ".join(x for x in parts if x))
    lines.append("interlocks: no fog with air; no clamp by a flood or the bladders; nothing wet below 0 C")
    return lines


def _chapters() -> tuple[Chapter, ...]:
    f = F
    n, g, fo, gl, v = f["n"], f["g"], f["foam"], f["glue"], f["vac"]
    ra, fi, ai, he, co = f["rain"], f["fire"], f["air"], f["heat"], f["cool"]
    ca, fg, fl, lv, x = f["cage"], f["fog"], f["fl"], f["live"], f["x"]
    bu, cx, rm, C, prof = f["bus"], f["cx"], f["room"], f["C"], f["prof"]
    ln, fe, vd, mu, sk = f["ln"], f["fe"], f["vd"], f["mu"], f["sk"]
    bp, bodies = mu["by_phase"], sk["bodies"]
    levels = v["levels"]
    rows = [
        # -- the idea ---------------------------------------------------------
        (1, "open", "The cell wall", "A skin that does work.",
         "Most walls do one job: they stand between you and the weather. This one is built like the wall of "
         "a living cell, a stack of layers, each made as one piece, each with its own channels built into it, "
         "carrying water, air, heat, vacuum and signal. Every layer can run on its own, run backwards, or hand "
         "what it carries to the layer beside it. Here they are, cut open, all of them running at once.",
         [f"{cx['layers']} layers, {cx['netted']} with channels", f"{n.triangles} cells in every layer",
          f"wall {sk['wall_mm']:.0f} mm; drawn {so.DRAW_SCALE:.0f}x thicker to be seen"]),
        (2, "why", "Why build this way", "Paid for once, used for decades.",
         f"Why build like this? Because a channel, once it is in the wall, can be used again and again for "
         f"different jobs. The network that glues the house together while you build it carries rain to a "
         f"tank while you live in it, floods the sheathing when a wildfire comes, and finds the leak when "
         f"something fails. This design lists {mu['uses']} uses for {mu['networks']} networks: {bp['build']} "
         f"while you build, {bp['live']} while you live in it, {bp['protect']} to protect it, and "
         f"{bp['maintain']} to look after it. Every use after the first costs a valve and a few lines of "
         f"code, not a new wall.",
         [f"uses: {mu['uses']} across {mu['networks']} networks",
          f"build {bp['build']}, live {bp['live']}, protect {bp['protect']}, maintain {bp['maintain']}",
          f"{mu['per_network']:.1f} uses per network (counted from the design's list)"]),
        (3, "declared", "Two kinds of number", "Measured off the dome, or typed in with a reason.",
         f"First, the two kinds of number in this film. Measured: the triangles, seams, areas and lengths, "
         f"read off the solver's dome. Nobody typed those. Declared: the groove's size, the hoses, the foam, "
         f"the pressures, the weather, the fire. A person typed those in, {len(cwall.CONSTANTS)} of them, each "
         f"with a unit, a kind and a reason. Each one is marked where it is used, and if one changes, every "
         f"figure after it moves.",
         _declared_steps(), "math"),
        # -- the frame's channels ----------------------------------------------
        (4, "cchannel", "A groove in every round face", "The C-channel, and what it costs the member.",
         f"It starts with one cut. Down the middle of every member's round face, the fat, curved side of the "
         f"wedge, rout a groove three quarters of an inch wide and three quarters deep. That middle line is "
         f"exactly where the sheathing bears, because each wedge sits square to its own panel. A hose goes in "
         f"the groove. The groove takes {g['area_loss_pct']:.1f} percent of the wood out of the member, and "
         f"{g['s_loss_pct']:.1f} percent of its bending strength. That is the structural price of everything "
         f"that follows.",
         [f"groove {C['groove_w_in']:.2f} x {C['groove_d_in']:.2f} in (assumed)",
          f"wedge section {g['area_in2']:.1f} sq in (12 in log)",
          f"wood lost {g['area_loss_pct']:.1f}%", f"bending strength lost {g['s_loss_pct']:.1f}%"]),
        (5, "local", "Forty gaskets", "A hose that reaches one triangle and nothing else.",
         f"Every triangle has its own three members, so the three grooves round one triangle make a closed "
         f"loop. The hose laid in them does two jobs. It is a gasket, sealing the board to the frame. And it "
         f"is a channel that reaches that one triangle and nothing else. The dome has {n.triangles} of them, "
         f"{min(n.loop_m):.1f} to {max(n.loop_m):.1f} metres each, {sum(n.loop_m):.0f} metres in all. Because "
         f"each one closes on itself, one triangle can be filled, emptied, warmed or tested without touching "
         f"its neighbours.",
         [f"{n.triangles} gaskets", f"each {min(n.loop_m):.2f} to {max(n.loop_m):.2f} m",
          f"total {sum(n.loop_m):.0f} m ({sum(n.loop_m) / cwall.FT:.0f} ft)"]),
        (6, "ports", "Three ports in every gasket", "Inside the seam, over it, or capped.",
         f"Now drill each gasket where it passes the middle of a side: three through-holes a triangle, "
         f"{ln['ports']} in all. Each port has three choices. A jumper down through the V, the inside seam, "
         f"to the gasket next door. A jumper over the ridge, the outside seam. Or a cap, and that triangle "
         f"keeps to itself. The {ln['rim_ports']} ports along the bottom edge go to a manifold round the rim, "
         f"which is where the tank, the pump and the outside world connect.",
         [f"3 ports x {n.triangles} gaskets = {ln['ports']}",
          f"{ln['jumpers']} seams: {ln['jumpers']} jumpers, 2 ports each",
          f"{ln['rim_ports']} rim ports: to the manifold",
          "a port: inside jumper, outside jumper, or cap"]),
        (7, "localnet", "A network of locals only", "Beside the global channel, never part of it.",
         f"Jumper every port and the gaskets become a network of their own: locals joined only to locals, "
         f"running beside the global channel in the key but never part of it. {ln['triangles']} gaskets and "
         f"{ln['jumpers']} jumpers make {ln['loops']} independent loops, so anything in it can always go round. "
         f"Take away any one jumper and every triangle can still be reached: there is no single point of "
         f"failure. From the nearest rim port, the farthest triangle is {ln['max_hops_from_rim']} jumpers "
         f"away.",
         [f"{ln['triangles']} gaskets + {ln['jumpers']} jumpers",
          f"loops = {ln['jumpers']} - {ln['triangles']} + 1 = {ln['loops']}",
          f"single points of failure: {ln['single_points']}",
          f"farthest from a rim port: {ln['max_hops_from_rim']} hops; corner to corner: {ln['diameter_hops']}"]),
        (8, "global", "The global channel", "Along the seams, everything is connected.",
         f"Between the triangles run the seams, and in every seam is the channel the earlier films built, the "
         f"key. That one is global. It runs from triangle to triangle all over the dome: {n.seams} seams, "
         f"{n.global_m:.0f} metres, {ca['bond_ft']:.0f} feet, down to the rim, where all of it can be reached "
         f"from one place. Local and global: a gasket that touches one cell, and a network that touches every "
         f"cell.",
         [f"{n.seams} seams = {n.global_m:.1f} m ({ca['bond_ft']:.0f} ft)", f"rim = {n.rim_m:.1f} m"]),
        (9, "seamroom", "What fits in a seam", "Not every layer gets a one-inch run.",
         f"Can every layer have its own run along every seam? Not at full size. The tightest seam's key has "
         f"{rm['inside_in2']:.1f} square inches inside, and the rule the channel film used fills "
         f"{rm['fill_pct']:.0f} percent of that. A one-inch hose fits {rm['big_fit']} times. A three-eighths "
         f"hose fits {rm['small_fit']} times: room for all {rm['netted']} networked layers, with "
         f"{rm['small_fit'] - rm['netted']} to spare. So the seams carry the small runs, and the big flows, "
         f"air and flood water, ride the rings.",
         [f"key inside {rm['inside_in2']:.2f} sq in, fill {rm['fill_pct']:.0f}%",
          f"1 in bore ({rm['big_od_in']:.2f} in OD): {rm['big_fit']} fit",
          f"3/8 in bore ({rm['small_od_in']:.2f} in OD): {rm['small_fit']} fit",
          f"networked layers: {rm['netted']}"]),
        (10, "rings", "Bands, like a greenhouse", "Channels that run round the dome.",
         f"There is a third kind. A greenhouse holds its plastic down with channels that run round the house, "
         f"level. A dome can have those too: a ring at every height where its corners stand, "
         f"{n.ring_m[0]:.1f}, {n.ring_m[1]:.1f} and {n.ring_m[2]:.1f} metres round, and the rim at "
         f"{n.rim_m:.1f}. A ring reaches every triangle at its height, so it serves one band of the dome at a "
         f"time: the bottom, the belt, the crown.",
         [f"rings: {n.ring_m[0]:.2f}, {n.ring_m[1]:.2f}, {n.ring_m[2]:.2f} m", f"rim: {n.rim_m:.2f} m",
          f"bands of seams: {cx['bands']}"]),
        (11, "address", "Every triangle an address", "One pair of wires, like a car's.",
         f"Give every triangle a small board on the room side: a few sensors, a few valves, and one pair of "
         f"wires along the seams to all of them. That is how a car's body works, one bus with every part "
         f"addressed. Forty triangles need {bu['bits']} bits of address. Along every seam the bus is "
         f"{bu['trunk_m']:.0f} metres. At 500 kilobits a second a bus is good for about {C['can_500k_m']:.0f}: "
         f"it fits, with {bu['spare_500k_m']:.0f} metres spare, which is too close. At 125 kilobits it is good "
         f"for {C['can_125k_m']:.0f}. Run it slow. Nothing in a wall needs to be fast.",
         [f"{bu['nodes']} nodes, {bu['bits']}-bit address", f"trunk {bu['trunk_m']:.1f} m",
          f"500 kbit/s: {C['can_500k_m']:.0f} m (standard), {bu['spare_500k_m']:.1f} m spare",
          f"125 kbit/s: {C['can_125k_m']:.0f} m, {bu['spare_125k_m']:.0f} m spare"]),
        # -- the layers ---------------------------------------------------------
        (12, "monolithic", "Every layer is one piece", "Fabric, semi-flexible or hard, channels built in.",
         f"Each layer is made as one piece, the way a quilt or a sheet of twin-wall plastic is, with its "
         f"channels built in rather than added afterwards. Heat runs in a capillary mat, fine tubes woven into "
         f"fabric. Room air runs in a textile duct, sewn into cells and perforated. Water runs in twin-wall "
         f"sheet, the fluted plastic greenhouses are glazed with. Vacuum runs in a spacer fabric whose pile "
         f"holds the gap open. The bladders are drop-stitch, two skins tied by thousands of threads, as "
         f"inflatable paddleboards are. {bodies.get('fabric', 0)} layers are fabric, "
         f"{bodies.get('semi-flexible', 0)} semi-flexible and {bodies.get('hard', 0)} hard. Outside the frame "
         f"the whole skin is {sk['weather_mm']:.0f} millimetres thick, inside it {sk['room_mm']:.0f}.",
         _material_steps(), "math"),
        (13, "quilt", "A quilt of forty shirts", "Each patch one cell, sewn together.",
         "The fabric layers are made like a T-shirt quilt: forty triangular patches, one for every triangle "
         "of the frame, each one a cell of its own, sewn together along the seams. The stitching is where the "
         "channels run, so one patch can be filled, drained or warmed while the rest stay as they are. A quilt "
         "folds flat for carrying. It stacks on the layer below it. And it can be added years later, or taken "
         "off and cleaned, without touching the frame.",
         [f"{n.triangles} patches = {n.triangles} cells", "channels in the stitching",
          "folds, stacks, comes off"]),
        (14, "stack", "The stack, as first drawn", "Every layer outside the wood.",
         "Now the stack, the way you first drew it, from the wood outward. Water nearest the wood, catching "
         "rain and flooding in a fire. Then the air intake, the filter, the vacuum network, the Faraday cage, "
         "the smoke channel, the bladders, heating and cooling, the hard cover, the one watertight cap, and "
         "plants on top. Every one of those can work. Not all of them work on the outside of the wood.",
         ["wood > " + " > ".join(SHORT[k] for k in cwall.OWNER_STACK[:6]),
          " > ".join(SHORT[k] for k in cwall.OWNER_STACK[6:]) + " > sky"]),
        (15, "sides", "The insulation splits the stack", "Heat inside the foam, water outside it.",
         f"Fill the frame with foam and it becomes the insulation, and insulation splits a wall in two. On a "
         f"{abs(C['winter_out_c']):.0f} below night, with the room at {C['room_c']:.0f}, the room side of the "
         f"foam sits near {prof['thermal']:.0f} degrees and the weather side near {deg(prof['water'])}. A "
         f"heating layer outside the foam sends {100 * he['weather_side']['to_weather']:.0f} percent of its "
         f"heat to the sky. Inside it, {100 * he['room_side']['to_room']:.0f} percent reaches the room. So "
         f"heat, cooling, room air and fog move inside the frame. Water, filter, vacuum, cage and bladders "
         f"stay out, and anything wet out there drains before it freezes.",
         [f"night {C['winter_out_c']:.0f} C, room {C['room_c']:.0f} C (assumed)",
          f"room side {prof['thermal']:.1f} C; core {prof['core']:.1f} C; weather side {prof['water']:.1f} C",
          f"heat outside the foam: {100 * he['weather_side']['to_room']:.0f}% to the room",
          f"heat inside the foam: {100 * he['room_side']['to_room']:.0f}% to the room"]),
        (16, "section", "The wall in section", "Every layer over one seam, drawn thick.",
         "Here it is in section, over one seam, drawn several times thicker than it is so every layer can be "
         "seen. In the frame, two members and the key between them, a gasket in each member's groove, and the "
         "jumper that joins them through the V. Glued to the frame, the board. Above it the weather side: "
         "water, filter, vacuum, cage, the one watertight cap, bladders and plants. Below the frame, an inner "
         "skin and the room side: signal, fog, air and heat. Every layer shows its channels where the cut "
         "passes through them.",
         [f"weather: {', '.join(SHORT[k] for k in cs.WEATHER)}", "core: frame, key, gaskets, foam",
          f"room: {', '.join(SHORT[k] for k in cs.ROOM)}"]),
        (17, "cutaway", "All of it, at once", "Every layer running, none in another's way.",
         "Now the whole wall, cut open, with everything running at once. Warm water climbs one side of the "
         "room-side mat and comes down the other. Fresh air rises through the duct. Signals run down to the "
         "controller at the rim. In the core, foam. Outside the board, rain water falls through the flutes "
         "toward the tank, filtered air rises through the pleats, vacuum draws toward the rim ring, and water "
         "drips through the plants' felt. Each layer does its own job, in its own channels, and not one of "
         "them is in another's way.",
         ["heat: up one side, down the other", "air: up the duct; signal: down to the rim",
          "water: down the flutes; filtered air: up the pleats", "vacuum: toward the rim ring"]),
        # -- building it ----------------------------------------------------------
        (18, "glue", "Glue from the inside", "And a vacuum to clamp it while it cures.",
         f"Now the build, and the first thing the gaskets are for. Lay a triangle of board on its frame and "
         f"push glue through the gasket's hose. Flooding the whole groove would take {gl['flood_l']:.0f} "
         f"litres for the dome, {gl['flood_cartridges']} cartridges. A perforated hose that pushes out a "
         f"bead takes {gl['bead_l']:.1f} litres, {gl['bead_cartridges']} cartridges. While it cures, pull a "
         f"vacuum on the cavity. At one kilopascal the air presses the biggest panel down with "
         f"{v['sheet_kg']:.0f} kilograms of force. Boat builders call it vacuum bagging. Every triangle glued "
         f"to its frame from the inside, with no nails.",
         [f"flood the groove: {gl['flood_l']:.1f} L = {gl['flood_cartridges']} cartridges",
          f"bead, {C['glue_bead_mm2']:.0f} mm2 (assumed): {gl['bead_l']:.2f} L = {gl['bead_cartridges']}",
          f"clamp {C['sheet_vacuum_kpa']:.0f} kPa x {v['triangle_m2']:.2f} m2 = {v['sheet_kn']:.2f} kN"]),
        (19, "foam", "Foam after the cover", "Three lifts, and the panel becomes a sandwich.",
         f"Then the foam, after the cover is on. Each triangle's cavity holds {fo['per_triangle_l']:.0f} "
         f"litres. The whole dome takes {fo['m3']:.2f} cubic metres, {fo['bdft']:,.0f} board feet, "
         f"{fo['kits']} two-part kits, about {fo['usd']:,.0f} dollars. Pour it in {fo['lifts']} lifts, "
         f"{fo['per_lift_l']:.0f} litres a triangle at a time, with the clamp still on, so the foam's push "
         f"cannot lift the cover. Glued on the outside and foamed within, each triangle becomes a sandwich "
         f"panel, and the wall becomes R-{fo['r_imperial']:.0f}.",
         [f"cavity {fo['per_triangle_l']:.0f} L a triangle; {fo['m3']:.2f} m3 = {fo['bdft']:,.0f} bd ft",
          f"{fo['kits']} kits x ${C['foam_kit_usd']:.0f} = ${fo['usd']:,.0f} (estimate)",
          f"{fo['lifts']} lifts of {fo['per_lift_l']:.0f} L (assumed)",
          f"6 in x R-{C['foam_r_per_in']:.0f}/in = R-{fo['r_imperial']:.0f}"]),
        (20, "oneway", "One-way doors", "Foam and glue spend the core's channels.",
         f"Against all that: foam and glue are one-way doors. The glue fills the gaskets it went through, and "
         f"the foam fills the cavity, so the core's own channels are spent the day they are used. Here is what "
         f"that costs. A hollow core could soak its whole frame to fibre saturation in a fire, with "
         f"{fi['soak_l']:.0f} litres, {100 * fi['soak_share']:.0f} percent of the tank. A foamed one cannot be "
         f"reached. Decide which layers are permanent before you build, and keep the ones you will want to "
         f"change where they can come off.",
         [f"soak the frame to {100 * C['fibre_saturation']:.0f}%: {fi['soak_l']:.0f} L",
          f"= {100 * fi['soak_share']:.0f}% of the {fi['tank_gal']:.0f} gal tank", "only while the core is hollow"]),
        # -- living in it ---------------------------------------------------------
        (21, "water", "Rain to the tank", "And drained before it freezes.",
         f"The water layer lies on the board, nearest the wood. A dome standing on {n.plan_m2:.1f} square "
         f"metres catches {f['b']['rain_in_year']:.0f} inches of rain a year: {ra['gal_year']:,.0f} gallons off "
         f"the cap, about {ra['gal_day']:.0f} a day. The rim channel takes it to the tank, and the "
         f"{ra['tank_gal']:.0f} gallon tank fills {ra['tank_fills']:.0f} times a year. Below freezing the layer "
         f"drains: on a {abs(C['winter_out_c']):.0f} below night it sits at {deg(prof['water'])} degrees, and "
         f"water left in it would split it.",
         [f"{n.plan_m2:.2f} m2 x {f['b']['rain_in_year']:.0f} in x {f['b']['runoff']:.2f} runoff",
          f"= {ra['gal_year']:,.0f} gal a year", f"tank {ra['tank_gal']:.0f} gal: {ra['tank_fills']:.0f} fills"]),
        (22, "filter", "The whole shell is the filter", "Air in, slower than a breeze.",
         f"Air in. Draw outside air in under the cap at the rim, through a filter layer that covers the whole "
         f"shell, and hand it to the room-side air layer at the rim. The house needs {ai['need_cfm']:.1f} cubic "
         f"feet a minute. Spread over {ai['area_m2']:.0f} square metres of filter, it moves "
         f"{ai['face_mm_s']:.2f} millimetres a second: {ai['ratio']:,.0f} times slower than a furnace filter. "
         f"A filter that slow catches nearly everything and almost never clogs. Does it also pick up the heat "
         f"leaking out? About {ai['recovered_w']:.0f} watts of the {ai['wall_loss_w']:.0f} the wall loses. "
         f"The cap is too close to the cold.",
         [f"{ai['need_cfm']:.1f} cfm over {ai['area_m2']:.1f} m2 = {ai['face_mm_s']:.3f} mm/s",
          f"furnace filter {C['furnace_face_m_s']:.1f} m/s (nominal): {ai['ratio']:,.0f} x faster",
          f"heat recovered: {ai['recovered_w']:.1f} W of {ai['wall_loss_w']:.0f} W"]),
        (23, "vent", "Venting the skin", "Dry air through the flutes.",
         f"Venting is the quiet job the network does every week. After a storm, or after the sheathing has "
         f"been flooded on purpose, dry air pushed through the water layer's flutes carries the wet away and "
         f"out at the rim. A film of half a millimetre over the side that got wet is {vd['water_kg']:.0f} "
         f"kilograms of water. A small fan moving {C['purge_cfm']:.0f} cubic feet a minute, on a "
         f"{C['dry_day_c']:.0f} degree day at {100 * C['dry_day_rh']:.0f} percent, takes {vd['kg_h']:.1f} "
         f"kilograms an hour: dry in about {vd['hours']:.0f} hours. With only the house's own fresh air it "
         f"would take {vd['hours_house_air']:.0f}. The same moving air, under the cap in summer, carries the "
         f"sun's heat off before it reaches the board.",
         [f"film {C['flood_film_mm']:.1f} mm x {fe['area_m2']:.1f} m2 = {vd['water_kg']:.1f} kg",
          f"air in {vd['w_in']:.1f} g/kg, out {vd['w_out']:.1f} g/kg (psychrometrics)",
          f"{C['purge_cfm']:.0f} cfm: {vd['kg_h']:.2f} kg/h -> {vd['hours']:.1f} h",
          f"house air only: {vd['hours_house_air']:.0f} h"]),
        (24, "declared2", "The services' numbers", "Typed in, before they are used.",
         "Before the services, the numbers they lean on. How warm a wall is run, and how fast it trades heat "
         "with a room. The design night. The heat a fire throws and the heat water takes to boil away. How "
         "long embers fall. The mesh, the doorway and the radio band. What a floor and its contents weigh. "
         "How steep soil will hold. All typed in, all marked as what they are.",
         _declared2_steps(), "math"),
        (25, "warm", "A wall a degree and a half warm", "The whole wall is the radiator.",
         f"Heating. On the room side, a layer of warm water makes the whole wall a radiator. A wall "
         f"{C['heating_dt_k']:.0f} degrees warmer than the room gives {he['capacity_w'] / 1000:.1f} kilowatts. "
         f"The foamed dome loses only {he['loss_w']:.0f} watts on a {abs(C['winter_out_c']):.0f} below night: "
         f"{he['wall_w']:.0f} through the wall and {he['vent_w']:.0f} in fresh air. So the wall needs to be "
         f"just {he['needed_dt_k']:.1f} degrees warmer than the room, cooler than your skin. Warm walls, not "
         f"warm air: the most comfortable heat there is.",
         [f"{C['radiant_h']:.0f} x {n.shell_m2:.1f} m2 x {C['heating_dt_k']:.0f} K = {he['capacity_w']:,.0f} W",
          f"loss {he['wall_w']:.0f} + {he['vent_w']:.0f} = {he['loss_w']:.0f} W",
          f"wall needs {he['needed_dt_k']:.2f} K over the room"]),
        (26, "cool", "A cool wall, above the dew point", "And where the cold comes from.",
         f"Cooling is the same layer run the other way, with one limit: a wall colder than the room's dew "
         f"point gets wet. On a humid day, {co['room_c']:.0f} degrees and {100 * co['rh']:.0f} percent, the "
         f"dew point is {co['dew_c']:.1f}. Keep the wood's {f['b']['wood_margin_k']:.0f} degree margin and the "
         f"coolest the wall may be is {co['surface_c']:.1f}. Even so, the whole wall takes "
         f"{co['capacity_w'] / 1000:.1f} kilowatts out of the room, against the Peltier ring's "
         f"{co['peltier_ring_w']:.0f} watts. The cold can come from the water layer outside at night, giving "
         f"heat to the sky, about {x['sky_w'] / 1000:.1f} kilowatts, kept in the tank for the afternoon.",
         [f"dew {co['dew_c']:.1f} C + {f['b']['wood_margin_k']:.0f} K = wall >= {co['surface_c']:.1f} C",
          f"{C['radiant_h']:.0f} x {n.shell_m2:.1f} m2 x {co['dt_k']:.2f} K = {co['capacity_w']:,.0f} W",
          f"Peltier ring: {co['peltier_ring_w']:.0f} W", f"night sky: {x['sky_w']:,.0f} W (borrowed)"]),
        (27, "vacuum", "A vacuum is a load", "It holds; it does not insulate.",
         f"A vacuum across a sheet is a load. The clamp's one kilopascal puts {v['sheet_kn']:.2f} kilonewtons "
         f"on the biggest triangle. A {C['wind_gust_m_s']:.0f} metre a second gust sucks on the same panel "
         f"with {v['wind_kn']:.2f}, so the clamp holds the skin down, by {100 * (v['sheet_over_wind'] - 1):.0f} "
         f"percent. A central vacuum's {C['hose_vacuum_kpa']:.0f} kilopascals across that sheet would be "
         f"{v['hose_tonnes']:.1f} tonnes: that strength lives in hoses only. A layer completely under vacuum, "
         f"the kind that insulates, would carry {v['hard_tonnes']:.0f} tonnes on one panel. The clamp leaves "
         f"the air {v['clamp_density_pct']:.0f} percent as dense: it holds, it does not insulate.",
         [f"clamp: {v['sheet_kn']:.2f} kN; gust: {v['wind_kn']:.2f} kN ({v['wind_kpa']:.2f} kPa)",
          f"central vac on a sheet: {v['hose_kn']:.0f} kN = {v['hose_tonnes']:.1f} t",
          f"hard vacuum: {v['hard_kn']:.0f} kN = {v['hard_tonnes']:.0f} t ({v['hard_t_per_m2']:.1f} t/m2)",
          f"air left at 1 kPa: {v['clamp_density_pct']:.0f}% as dense"]),
        (28, "levels", "Three vacuums at once", "Each strength only where it is safe.",
         f"So, different vacuums at once, at different levels. The rim ring is a central vacuum: "
         f"{levels[0][1]:.0f} kilopascals, enough to lift water {levels[0][2]:.1f} metres, sealed in hoses, with "
         f"an inlet at every rim corner. A regulator feeds the water layer at {levels[1][1]:.0f}, which lifts "
         f"rain {levels[1][2]:.1f} metres into a raised tank. Another feeds the clamp at {levels[2][1]:.0f}. "
         f"One pump, three levels, each strength only where it is safe.",
         [f"{name}: {kpa:.0f} kPa, lifts water {lift:.2f} m" for name, kpa, lift in levels]),
        # -- protecting it -----------------------------------------------------------
        (29, "firethreat", "How a wildfire takes a house", "Embers, radiant heat, and flame.",
         f"Now the case this network was built for. A wildfire takes a house three ways. Embers, carried far "
         f"ahead of the flames, find a vent or a gap and start the fire from inside; that is how most houses "
         f"are lost. Radiant heat, which Australia's building standard measures in kilowatts on every square "
         f"metre: a house rated BAL-29 is built to take {C['bal_kw_m2']:.0f} at the fire's edge. And flame "
         f"contact. Above {C['flame_zone_kw_m2']:.0f} kilowatts a square metre is the flame zone, where no skin "
         f"is enough and only a cleared perimeter helps.",
         ["embers: in through any opening", f"radiant: BAL-29 = {C['bal_kw_m2']:.0f} kW/m2 (AS 3959)",
          f"flame zone: above {C['flame_zone_kw_m2']:.0f} kW/m2"]),
        (30, "fireseal", "Close every door", "Nothing for an ember to find.",
         f"So first, the house shuts. All {ln['rim_ports']} intakes at the rim close. The filter layer stops "
         f"drawing outside air, and the room runs on its own air for the hour that matters. The cap has no "
         f"openings to begin with: the breathing film showed why the cap is never cut, and in a fire this is "
         f"the reason. An ember landing on this skin finds nothing to climb into.",
         [f"rim intakes: {ln['rim_ports']}, closed", "filter layer: off; room on its own air",
          f"openings in the cap: {f['cap_holes']}"]),
        (31, "fireflood", "Flood the sheathing, metered", "Water where the heat is, as fast as it boils off.",
         f"Then the water layer floods the sheathing on the side facing the fire, and here is the multiplier. "
         f"At a sprinkler's rate, wetting the whole dome takes {fi['gpm']:.0f} gallons a minute and empties "
         f"the tank in {fi['tank_min']:.1f} minutes. But the heat arriving on the fire's side, "
         f"{fe['load_kw']:.0f} kilowatts at BAL-29, only boils away {fe['gpm']:.1f} gallons a minute. Metered to "
         f"the heat by the sensor in every cell, the same {fi['tank_gal']:.0f} gallon tank lasts "
         f"{fe['tank_min']:.0f} minutes: {fe['times_longer']:.0f} times longer, "
         f"{100 * fe['window_share']:.0f} percent of the half hour embers keep falling. That flow runs through "
         f"the local-net's jumpers at {fe['jumper_m_s']:.1f} metres a second, on a {fe['pump_w']:.0f} watt pump.",
         [f"heat: {C['bal_kw_m2']:.0f} kW/m2 x {fe['area_m2']:.1f} m2 = {fe['load_kw']:.0f} kW",
          f"water takes {fe['per_kg_mj']:.2f} MJ/kg (warm + boil)",
          f"metered: {fe['kg_s']:.2f} kg/s = {fe['gpm']:.1f} gpm",
          f"tank: {fe['tank_min']:.0f} min vs {fi['tank_min']:.1f} at sprinkler rate",
          f"pump {fe['pump_w']:.0f} W; jumpers {fe['jumper_m_s']:.2f} m/s"]),
        (32, "fireaim", "Aim the water", "A nervous system, not a sprinkler.",
         f"What the network changes is where the water goes. A sensor in every cell knows which triangle is "
         f"hot. One triangle takes {fi['one_gpm']:.1f} gallons a minute at the sprinkler's rate, and on one "
         f"triangle at a time the same tank lasts {fi['one_min']:.0f} minutes. Water where the embers are "
         f"landing, nowhere else. That is the difference between a sprinkler and a nervous system.",
         [f"one triangle: {fi['one_gpm']:.2f} gpm", f"tank on one: {fi['one_min']:.0f} min",
          f"tank on all {n.triangles}: {fi['tank_min']:.1f} min"]),
        (33, "fireafter", "After the front", "Check, vent, dry.",
         f"When the front has passed, the network turns from defence to recovery. The sensor in every cell "
         f"reports which triangles got hot. The local-net pressure-tests the cells for damage, halving the "
         f"search each time: {x['leak_tests']} tests find one bad triangle in forty. And the venting run "
         f"dries the flooded side in about {vd['hours']:.0f} hours. The house defended itself with its own "
         f"skin, and then it checks itself over.",
         [f"leak search: {x['leak_tests']} tests", f"drying: {vd['hours']:.1f} h at {C['purge_cfm']:.0f} cfm",
          "sensors: every cell's heat and moisture"]),
        (34, "cage", "A cage is its biggest hole", "Bond every seam, or it is not a cage.",
         f"Bond a mesh into one layer and the dome is a Faraday cage: lightning goes round the people inside, "
         f"and radio is cut down. But a cage is only as good as its biggest hole. Quarter-inch mesh stops "
         f"everything below {ca['mesh_cutoff_ghz']:.1f} gigahertz, and cuts Wi-Fi by about "
         f"{ca['mesh_db_wifi']:.0f} decibels. An unbonded seam is a slot {f['seam_len_m']:.1f} metres long that "
         f"lets in everything above {ca['seam_cutoff_mhz']:.0f} megahertz. An open door lets in everything "
         f"above {ca['door_cutoff_mhz']:.0f}. So bond all {ca['seams']} seams, {ca['bond_ft']:.0f} feet of it, "
         f"and give the door a conductive gasket.",
         [f"mesh {C['mesh_aperture_mm']:.2f} mm: passes above {ca['mesh_cutoff_ghz']:.1f} GHz",
          f"Wi-Fi through mesh: -{ca['mesh_db_wifi']:.0f} dB",
          f"unbonded seam {f['seam_len_m']:.2f} m: leaks above {ca['seam_cutoff_mhz']:.0f} MHz",
          f"open door {C['door_w_m']:.1f} m: leaks above {ca['door_cutoff_mhz']:.0f} MHz"]),
        (35, "fog", "Fog, not pepper", "And backwards, a smoke exhaust.",
         f"Security. You asked about pepper spray. A device that sprays a person by itself is a trap, and in "
         f"many places a trap that hurts an intruder is illegal, even in your own home. It would also gas your "
         f"family, your dog and the firefighters. Fog does the job instead: a security fog unit fills the "
         f"dome's {fg['volume_m3']:.0f} cubic metres in about {fg['seconds']:.0f} seconds, and nobody can see "
         f"to take anything. Run the same channel backwards in a fire and it is a smoke exhaust: smoke out of "
         f"the crown, down the seams, and out at the rim.",
         [f"volume {fg['volume_m3']:.1f} m3 / {C['fog_m3_s']:.0f} m3/s = {fg['seconds']:.1f} s",
          "fog: harmless, blinding", "backwards: crown -> seams -> rim"]),
        (36, "airbag", "If the water comes up", "Bladders float it. A sealed floor floats it dry.",
         f"And if the water comes up. The house, frame, cover, floor and everything in it, is about "
         f"{fl['mass_kg'] / 1000:.1f} tonnes, so it floats once it pushes aside {fl['need_m3']:.1f} cubic metres "
         f"of water. Bladders round the lower half of the dome, {fl['lower_m2']:.1f} square metres inflated "
         f"{100 * C['airbag_m']:.0f} centimetres deep, hold {fl['have_m3']:.1f}: enough, with "
         f"{100 * (fl['ratio'] - 1):.0f} percent to spare, from one cylinder of carbon dioxide. But they only "
         f"lift it when the water is {fl['bag_waterline_m']:.1f} metres up the wall, and by then the floor is "
         f"under water. Seal the floor and the foot of the wall instead and it is a hull: it floats in "
         f"{100 * fl['hull_draft_m']:.0f} centimetres, dry inside. Either way it needs guide posts, as "
         f"amphibious houses have, or it floats away.",
         [f"mass {fl['mass_kg']:,.0f} kg -> {fl['need_m3']:.2f} m3 of water",
          f"bladders {fl['lower_m2']:.1f} m2 x {C['airbag_m']:.2f} m = {fl['have_m3']:.2f} m3",
          f"CO2 {fl['co2_kg']:.1f} kg = {fl['cylinders']} cylinder",
          f"bladders lift at {fl['bag_waterline_m']:.2f} m of water: floor flooded",
          f"sealed floor: floats at {100 * fl['hull_draft_m']:.0f} cm, dry"]),
        # -- running it --------------------------------------------------------------
        (37, "twoway", "Every layer runs both ways", "A pipe with valves at both ends.",
         "Most of these layers run both ways. Air in, or air out. Warm water, or cold. Fog out, or smoke in. "
         "Vacuum to clamp, or pressure to test for leaks. Rain in to the tank, or the tank's water back out as "
         "a flood. A layer is a pipe with valves at both ends, and the valves decide the direction, not the "
         "layer.",
         [f"{SHORT[l.key]}: {' / '.join(m.replace('_', ' ') for m in l.modes if m != 'off')}"
          for l in cwall.LAYERS if len(l.modes) > 2]),
        (38, "routes", "Plug one layer into another", "A short list of allowed routes.",
         f"And a layer can be plugged into another. The filter hands its air to the room's air layer. Rain "
         f"runs to the tank, and the tank feeds the flood, the plants and the warm or cool wall. The vacuum "
         f"pulls the water layer toward the tank, and holds the core while its glue cures. A cylinder fills "
         f"the bladders. {len(cwall.ROUTES)} routes in all, and the controller refuses anything not on the "
         f"list.",
         [f"{SHORT[a]} -> {SHORT[b]}" for a, b, _w in cwall.ROUTES]),
        (39, "scenes", "Situations, not settings", "And the interlocks that keep them apart.",
         "So the house runs in situations, not settings. A winter night: the wall warm, air in through the "
         "filter, the water layer drained, the clamp on. A humid afternoon: the wall cool, the plants "
         "watered. The summer night after it: water out under the sky, filling the tank with cold. A storm: "
         "rain to the tank. Embers: the flood, the smoke drawn out, no outside air. Someone breaking in: fog. "
         "Rising water: the bladders. And the interlocks that keep them from fighting.",
         _scene_steps(), "math"),
        (40, "more", "And more", "A leak found in six tests; smoke smelled in seconds.",
         f"And more, from the same network. Find a leaking triangle by pressurising half the cells, then half "
         f"of those: {x['leak_tests']} tests find one in forty. Draw air from every gasket to one smoke "
         f"detector, as big buildings do with sampling pipes: from the farthest triangle a sample takes "
         f"{x['sample_s']:.0f} seconds, inside the {C['sample_limit_s']:.0f} the standard allows. Treat bare "
         f"timber with borate from inside: {x['borate_l']:.0f} litres for the frame. Kill insects in a layer "
         f"with carbon dioxide: {x['fumigate_kg']:.2f} kilograms. Melt snow off the crown with "
         f"{x['snowmelt_kw']:.1f} kilowatts. Or run the water layer as a solar collector in summer: up to "
         f"{x['solar_kw']:.1f} kilowatts off half the dome.",
         [f"leak search: log2 {n.triangles} -> {x['leak_tests']} tests",
          f"smoke sample: {x['sample_m']:.1f} m at {C['sample_m_s']:.0f} m/s = {x['sample_s']:.0f} s",
          f"borate {C['borate_l_m2']:.2f} L/m2: {x['borate_l']:.1f} L",
          f"CO2 at {100 * C['fumigation_co2']:.0f}% in one layer: {x['fumigate_kg']:.2f} kg",
          f"snowmelt, crown: {x['snowmelt_kw']:.2f} kW; all of it {x['snowmelt_all_kw']:.1f} kW",
          f"solar, half the dome: {x['solar_kw']:.1f} kW"]),
        (41, "chia", "The chia-pet", "Plants on the outside, fed from within.",
         f"And the outside can be alive. Over the cap, a root barrier, and over that, plants, watered and fed "
         f"from inside through the living layer, with the food dissolved in the water, which growers call "
         f"fertigation. But a dome is steep. Only {lv['plant_pct']:.0f} percent of it, the {f['flat_n']} crown "
         f"triangles at {f['flat_deg']:.0f} degrees, is flat enough to hold soil. The rest takes felt pockets. "
         f"Wet, all of it weighs {lv['wet_kg'] / 1000:.1f} tonnes, {lv['times_frame']:.1f} times the frame, and "
         f"drinks {lv['water_l_day']:.0f} litres a summer day. It can be done. It is a structural decision, "
         f"not a decoration.",
         [f"soil on {lv['plant_m2']:.1f} m2 ({lv['plant_pct']:.0f}%): {lv['soil_kg']:,.0f} kg",
          f"felt on {lv['steep_m2']:.1f} m2: {lv['felt_kg']:,.0f} kg",
          f"wet total {lv['wet_kg']:,.0f} kg = {lv['times_frame']:.1f} x frame ({lv['frame_kg']:.0f} kg)",
          f"water {lv['water_l_day']:.0f} L/day"]),
        (42, "multipliers", "The multiplier", "Counted, not claimed.",
         f"Count it. {mu['uses']} uses from {mu['networks']} networks: {mu['per_network']:.1f} for every network "
         f"built. The water layer alone does {mu['per']['water']} jobs: rain to the tank, solar heat, night "
         f"cooling, snowmelt, borate, drying, and the fire flood. Then the stacked uses: filtered air handed "
         f"to the room's air layer, the tank feeding the wall and the plants, the vacuum holding the glue. A "
         f"wall that does one thing is paid for once and used once. This one is paid for once and used every "
         f"day, in every season, for as long as it stands.",
         [f"{NET_NAME[k].lower()}: {c}" for k, c in sorted(mu["per"].items(), key=lambda kc: -kc[1])[:7]]
         + [f"{mu['uses']} uses / {mu['networks']} networks = {mu['per_network']:.1f}"]),
        (43, "cost", "The price of an address", "Valves and joints.",
         f"Now the price of all those addresses. {cx['netted']} networked layers over forty triangles, with "
         f"the bladders only on the lower half, is {cx['cells']} cells. A valve in and a valve out on every "
         f"cell is {cx['valves_every_cell']} valves, and joining every cell and every seam run at both ends is "
         f"{cx['joints']:,} joints, every one of them a place to leak. Address by band instead, a pair of "
         f"valves per band per layer at the rim, and it is {cx['valves_by_band']}. Address by triangle only "
         f"where it pays: the water in a fire, the sensors, the bus. Everything else by band.",
         [f"cells = {cx['cells']}", f"valves, every cell: {cx['valves_every_cell']}",
          f"valves, by band: {cx['valves_by_band']}", f"joints: {cx['joints']:,}"]),
        (44, "close", "Start with three", "The skin is an organ.",
         "So where to start? Three layers earn their place on day one. Glue and foam through the core while "
         "you build, because the gaskets are already there. The bus and its sensors, because a wall that "
         "reports its own moisture is a wall that does not rot unseen. And the water layer, because the rain "
         "is free and the fire will come. The rest can be added later, if the ports, the rings and the seam "
         "runs go in now. The skin of this dome is not a wall. It is an organ.", []),
    ]
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()


# ----------------------------------------------------------------------
# Selftest
# ----------------------------------------------------------------------

def validate_cell_wall_film() -> None:
    cwall.validate_cell_wall()
    cs.validate_cell_wall_scene()
    so.validate_cell_wall_solids()
    sc.validate_channel_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert len({c.title for c in CHAPTERS}) == len(CHAPTERS)
    for ch in CHAPTERS:
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye, target = np.asarray(eye, float), np.asarray(target, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.3, (ch.slug, p)
            assert np.linalg.norm(eye - target) > 0.3, ch.slug
            assert not cabin_stage.blocked(eye, target), (ch.slug, p, "a pine is in the way")

    class App:
        def __init__(self):
            self.world_labels = []
            self.built: set = set()

        def static_layer(self, key, builder, subject_points=None):
            if key in self.built:
                return
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key
            self.built.add(key)

    built: set = set()
    for slug, painter in SCENES.items():
        for p in (0.1, 0.6, 0.95):
            app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
            app.built = built
            painter(app, opaque, transparent, p)
            assert np.all(np.isfinite(opaque.vertices)) and np.all(np.isfinite(transparent.vertices)), slug
            assert app.world_labels, slug
            for item in app.world_labels:
                assert all(isinstance(c, int) and 0 <= c <= 255 for c in item.color), slug
    # The claims the narration makes, held against the facts.
    by = {c.slug: c.narration[0] for c in CHAPTERS}
    assert F["fl"]["ratio"] > 1 and "floats" in by["airbag"]
    assert F["fl"]["bag_waterline_m"] > 0.5 > F["fl"]["hull_draft_m"], "the floor floods before the bladders lift"
    assert F["bus"]["spare_500k_m"] < 10 and "too close" in by["address"]
    assert "illegal" in by["fog"] and "pepper" in by["fog"]
    assert F["room"]["big_fit"] < F["room"]["netted"] <= F["room"]["small_fit"]
    assert 1.25 < F["heat"]["needed_dt_k"] < 1.75, "chapter 25's title says a degree and a half"
    assert F["air"]["recovered_share"] < 0.05 and "too close to the cold" in by["filter"]
    assert F["vac"]["sheet_over_wind"] > 1 and "does not insulate" in by["vacuum"]
    assert F["live"]["times_frame"] > 1 and F["live"]["plant_pct"] < 25
    assert F["x"]["leak_tests"] == 6, "chapter 40's promise says six tests"
    assert F["cx"]["valves_by_band"] < F["cx"]["valves_every_cell"] / 5
    assert "Against" in by["oneway"]
    assert F["n"].triangles == 40 and F["ln"]["triangles"] == 40, "titles say forty"
    assert F["ln"]["single_points"] == 0 and "no single point of failure" in by["localnet"]
    assert F["cap_holes"] == 0 and "no openings" in by["fireseal"]
    assert F["fe"]["times_longer"] > 5 and "multiplier" in by["fireflood"]
    assert F["mu"]["per_network"] > 2
    assert all(c in by["monolithic"] for c in ("capillary mat", "twin-wall", "drop-stitch"))
    assert set(F["sk"]["bodies"]) <= {"fabric", "semi-flexible", "hard"}
    CABIN_CELL_WALL_LESSON.validate()


def report() -> str:
    return "\n\n".join((cwall.constants_table(), cwall.scenario_table()))


CABIN_CELL_WALL_LESSON = Lesson(
    key="cabin_cell_wall", brand="DOMESIM", title="The Cell Wall: A Dome Skin in Layers",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cell_wall_film, report=report,
    snapshot_prefix="cabin_cell_wall", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
