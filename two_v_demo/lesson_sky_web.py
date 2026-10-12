"""The Sky Web: building the dome in the air, from cables between four trees.

The owner's method (October 2026), worked through in the Cabin World. Two wire
ropes cross between four trees in an X; a spiral is woven onto it over the
dome's footprint, above it. A 12 V battery winch on one tree pulls each
triangle up, flat in a three-leg harness, to a hook at the X's centre; it is
swung out to its place, three pigtails of cord are thrown over the web, and it
slips the harness and hangs there. Forty times. Then they are joined -- lashed,
perhaps, rather than screwed -- the cords are gathered to the apex so one
bigger winch can lift the whole dome evenly from one point, a cotton skin
soaked in silicone goes over it, and it may simply stay up, off the ground,
held by a network of living trees. A second, higher web is shown, and called
experimental.

The second cut (October 2026) corrects the first: the winch is a 12 V battery
winch, not a hand winch, and the struts weigh what the owner weighed, 15 to 22
kg, two to three times the solver's estimate -- which moves every load in the
film. Both corrections are named on screen.

The triangles are the solver's own, panel by panel
(:mod:`two_v_demo.sky_web_scene`); every figure is :mod:`two_v_demo.sky_web`'s,
weighed by the owner or declared in its tables, which go on screen first. The
film keeps the numbers that argue back.

    py -3.12 -m rerender stills cabin_sky_web
    py -3.12 -m rerender render cabin_sky_web
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import shots
from . import sky_web as sw
from . import sky_web_scene as ss
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)
ORANGE = (255, 160, 80)

FT = 3.28084
GAP = sw.C["float_gap_m"]


# ----------------------------------------------------------------------
# Every number the film states
# ----------------------------------------------------------------------

F = sw.facts()
C = sw.C
O = sw.O
ORDER = F["order"]


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def ease(p: float) -> float:
    return shots.ease(p)


def ft(m: float) -> str:
    return f"{m * FT:.0f}"


def lb(kg: float) -> str:
    return f"{kg * sw.LB_PER_KG:,.0f}"


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def _world(app, webs=(1,), rigs=(1,)) -> None:
    cw.paint(app, hide=("dome", "builder"), subject=False)
    app.static_layer("sky:trees", ss.tree_batch)
    for level in webs:
        app.static_layer(f"sky:web{level}", lambda lv=level: ss.web_batch(lv))
    for level in rigs:
        app.static_layer(f"sky:rig{level}", lambda lv=level: ss.rig_batch(lv))


def _hung(app, i: int, level: int = 1, gap: float = GAP) -> None:
    app.static_layer(f"sky:hung:{i}:{level}:{gap:.3f}", lambda: ss.hung_batch(i, level, gap),
                     list(ss.corners_at(i, np.eye(3), ss.hung_balance(i, level, gap))))


def _stacked(app, i: int) -> None:
    R, P = ss.stack_pose()[i]
    app.static_layer(f"sky:stack:{i}", lambda: ss.stacked_batch(i), list(ss.corners_at(i, R, P)))


def _all_hung(app, level: int = 1, gap: float = GAP) -> None:
    """All forty hung, as one cached layer."""
    def make():
        b = TriangleBatch()
        for i in ORDER:
            b.vertices.extend(ss.hung_batch(i, level, gap).vertices)
        return b
    app.static_layer(f"sky:hungall:{level}:{gap:.3f}", make, _dome_points(level))


def _build(app, opaque, done: int, current: float | None = None, level: int = 1, gap: float = GAP):
    """``done`` panels hung, the next ``current`` of the way through its trip,
    the rest still stacked on the deck."""
    if done >= len(ORDER) and current is None:
        _all_hung(app, level, gap)
        ss.hoist_line(opaque, ss.hook_rest(level), level)
        return None
    for i in ORDER[:done]:
        _hung(app, i, level, gap)
    rest = ORDER[done:]
    state = None
    if current is not None and rest:
        state = ss.draw_trip(opaque, rest[0], current, level, gap)
        rest = rest[1:]
    else:
        ss.hoist_line(opaque, ss.hook_rest(level), level)
    for i in rest:
        _stacked(app, i)
    return state


def _dome_points(level: int = 1) -> list:
    v = ss.joints(level)
    return [v[np.argmin(v[:, 0])], v[np.argmax(v[:, 0])], v[np.argmax(v[:, 2])], v[np.argmin(v[:, 1])]]


def _dome(app, level: int = 1) -> None:
    """The joined dome, no pigtails: as it hangs once its cords go to the apex."""
    def make():
        b = TriangleBatch()
        ss.dome_pose(b, np.eye(3), np.zeros(3), np.array([0.0, 0.0, ss.lift_z(level)]), 0.0)
        return b
    app.static_layer(f"sky:dome:{level}", make, _dome_points(level))


def _apex(app, level: int = 1) -> None:
    def make():
        b = TriangleBatch()
        ss.apex_rig(b, level)
        return b
    app.static_layer(f"sky:apex:{level}", make)


def _skin(app, level: int = 1) -> None:
    app.static_layer(f"sky:skin:{level}", lambda: ss.skin_batch(level), _dome_points(level))


def _hanging(app, skin: bool = True) -> None:
    """The finished state: joined, gathered to the apex, skinned, on web 1."""
    _world(app)
    _dome(app)
    _apex(app)
    if skin:
        _skin(app)


def _top(z: float = 1.4) -> np.ndarray:
    return np.array([0.0, 0.0, ss.web_z(0, 0) + z])


def _dome_label(app, text: str, colour=AMBER, z: float = 1.4) -> None:
    _label(app, _top(z), text, colour)


def p_open(app, opaque, transparent, p):
    _world(app)
    _build(app, opaque, 40)
    _dome_label(app, "FORTY TRIANGLES, HUNG FROM A WEB")


def p_declared(app, opaque, transparent, p):
    _world(app)
    _build(app, opaque, 40)
    _dome_label(app, f"{len(sw.OWNER)} WEIGHED OR OWNED, {len(C)} DECLARED", WHITE)


def p_corrections(app, opaque, transparent, p):
    _world(app)
    s = _build(app, opaque, 0, 0.10 + 0.06 * ease(p))
    w = F["weights"]
    _label(app, s["P"] + [0.0, 0.0, 1.6], f"3 STRUTS x {O['strut_kg_lo']:.0f}-{O['strut_kg_hi']:.0f} kg", AMBER)
    _label(app, s["P"] + [1.4, -0.8, 0.4], f"SOLVER: {w['solver_strut_kg']:.1f} kg A STRUT", RED)
    _label(app, ss.winch_at() + [0, 0, 0.9], f"12 V WINCH, {O['winch_lb']:,.0f} lb", GREEN)


def _ground_line(opaque, a, b, colour=(1.0, 0.86, 0.3, 1.0)):
    a, b = np.asarray(a, float), np.asarray(b, float)
    opaque.cylinder(a + [0, 0, 0.04], b + [0, 0, 0.04], 0.035, colour, 6)


def p_trees(app, opaque, transparent, p):
    _world(app, webs=(), rigs=())
    for i in ORDER:
        _stacked(app, i)
    t = ss.trees()
    grow = ease(min(1.0, p * 1.6))
    for k in range(4):
        a, b = t[k], t[(k + 1) % 4]
        _ground_line(opaque, a, a + (b - a) * grow)
    if p > 0.5:
        g = ease((p - 0.5) * 2)
        _ground_line(opaque, t[0], t[0] + (t[2] - t[0]) * g, (0.45, 0.85, 1.0, 1.0))
    _label(app, (t[0] + t[1]) / 2 + [0, -0.6, 0.4], f"{C['tree_square_m']:.0f} m SQUARE", AMBER)
    _label(app, np.array([0.0, 0.0, 0.9]), f"DIAGONAL {F['x']['span_m']:.1f} m", BLUE)
    for k in range(4):
        _label(app, t[k] + [0, 0, C["anchor1_m"]], f"TIE {C['anchor1_m']:.0f} m" if k == 0 else "TIE", WHITE)


def _x(opaque, level: int, a: float, b: float) -> None:
    """The X's two ropes, strung ``a`` and ``b`` of the way across."""
    for rope, u in zip((0, 1), (a, b)):
        if u > 0.01:
            ss.tube(opaque, ss.x_ropes(level, u)[rope], ss.rope_r(0.5), ss.WIRE)


def p_xrope(app, opaque, transparent, p):
    _world(app, webs=(), rigs=())
    for i in ORDER:
        _stacked(app, i)
    ss.straps(opaque, 1)
    _x(opaque, 1, ease(min(1.0, p * 2.2)), ease(max(0.0, p * 2.2 - 1.1)))
    sp, st = F["spread"], F["spread_taut"]
    _label(app, np.array([0.0, 0.0, ss.web_z(0, 0) - 0.5]), f"SAG {sp['sag_m']:.2f} m (10%)", BLUE)
    _label(app, ss.tie(1) + [0, 0, 0.8], f"{sp['tension_kn']:.0f} kN: {sp['rope']} ROPE", AMBER)
    _label(app, ss.tie(2) + [0, 0, 0.8], f"5% SAG: {st['tension_kn']:.0f} kN", RED)


def _guys(opaque, g: float) -> None:
    for k in range(4):
        a, b = ss.guy_line(k, 1)
        ss.tube(opaque, ss.catenary(a, b, 0.08, 10, g), ss.rope_r(0.625), ss.GUY, 5)


def p_guys(app, opaque, transparent, p):
    _world(app, webs=(), rigs=())
    for i in ORDER:
        _stacked(app, i)
    ss.straps(opaque, 1)
    for rope in ss.x_ropes(1):
        ss.tube(opaque, rope, ss.rope_r(0.5), ss.WIRE)
    _guys(opaque, ease(min(1.0, p * 1.5)))
    t1, tt = F["tree1"], F["tree1_taut"]
    _label(app, ss.tie(1) + [0, 0, 0.9], f"UNGUYED: MARGIN {t1['factor']:.1f}, WANTS {C['tree_factor']:.0f}", RED)
    _label(app, ss.next_trees()[1] + [0, 0, 1.6], f"GUY {t1['guy_kn']:.0f} kN TO THE NEXT TREE'S BASE", AMBER)
    _label(app, np.array([0.0, 0.0, ss.web_z(0, 0) + 1.0]), f"5% SAG UNGUYED: {tt['factor']:.2f}, IT BREAKS", RED)


def p_treepost(app, opaque, transparent, p):
    _world(app)
    t = ss.trees()[1]
    inward = -np.array([t[0], t[1], 0.0]) / math.hypot(t[0], t[1])
    side = np.cross(inward, [0, 0, 1.0])
    post_at = t + inward * 0.5 + side * 1.6
    h = C["anchor1_m"] * ease(min(1.0, p * 1.6))
    s = C["post_in"] * sw.IN
    if h > 0.05:
        opaque.box(post_at + [0, 0, h / 2], np.array([s, s, h]), (0.86, 0.70, 0.46, 1.0))
    pv, t1 = F["post"], F["tree1"]
    _label(app, post_at + [0, 0, C["anchor1_m"] + 0.5], f"MILLED 6x6: {pv['post_kn']:.0f} kN", RED)
    _label(app, ss.tie(1) + [0, 0, 1.4], f"THE TREE: {pv['tree_kn'] / 1000:.1f} MN, x{pv['times']:.0f}", GREEN)
    _label(app, t + [0, 0, 3.0], f"SQUEEZED {t1['squeeze_kn']:.0f} kN: x{t1['buckle_factor']:.0f} SPARE", AMBER)


def p_spiral(app, opaque, transparent, p):
    _world(app, webs=(), rigs=())
    for i in ORDER:
        _stacked(app, i)
    b = ss.web_batch(1, guys=True, x=1.0, spiral=0.0)
    opaque.vertices.extend(b.vertices)
    u = ease(min(1.0, p * 1.25))
    if u > 0.01:
        ss.tube(opaque, ss.spiral_points(1, u), ss.rope_r(0.375), ss.SPIRAL, 5)
    sp = F["spiral"]
    _label(app, np.array([sp["radius_m"], 0.0, ss.web_z(sp["radius_m"], 0) + 0.5]),
           f"{sp['turns']:.1f} TURNS, {sp['length_m']:.0f} m", AMBER)
    _label(app, np.array([0.0, 0.0, 0.9]), f"FOOTPRINT r = {sp['radius_m']:.2f} m", BLUE)
    r = sp["radius_m"]
    pts = [np.array([r * math.cos(a), r * math.sin(a), cw.landmarks().deck_centre[2] + 0.03])
           for a in np.linspace(0, math.tau, 61)]
    ss.tube(opaque, pts, 0.03, (0.45, 0.85, 1.0, 1.0), 5)


def p_winch(app, opaque, transparent, p):
    _world(app)
    for i in ORDER:
        _stacked(app, i)
    down = ss.hook_rest() + (np.array([0.0, 0.0, cw.landmarks().deck_centre[2] + 1.4]) - ss.hook_rest()) * ease(p)
    ss.hoist_line(opaque, down)
    h = F["hoist"]
    _label(app, ss.winch_at() + [0, 0, 0.7], f"12 V, {O['winch_lb']:,.0f} lb = {h['winch_kn']:.1f} kN", RED)
    _label(app, ss.winch_at() + [0.6, 0.2, 0.25], f"40 LIFTS: {h['all_wh']:.0f} Wh", GREEN)
    _label(app, ss.pulley_at() + [0, 0, 0.6], "BLOCK AND HOOK AT THE CENTRE", AMBER)


def _first() -> int:
    return ORDER[0]


def p_harness(app, opaque, transparent, p):
    _world(app)
    _build(app, opaque, 0, 0.10 + 0.08 * ease(p))
    hk = F["harness"]
    s = ss.trip(_first(), 0.12)
    _label(app, s["eye"] + [0, 0, 0.35], f"EYE {C['bridle_h_m']:.1f} m OVER THE BALANCE POINT", AMBER)
    rows = hk["rows"]
    _label(app, s["P"] + [0.9, -0.6, 0.1],
           "LEGS " + " / ".join(f"{l:.2f}" for l in rows[0]["legs_m"]) + " m", GREEN)


def p_hoist(app, opaque, transparent, p):
    _world(app)
    s = _build(app, opaque, 0, 0.12 + 0.28 * ease(p))
    _label(app, s["P"] + [0.0, 0.0, -0.6], f"{s['P'][2]:.1f} m UP, FLAT", AMBER)


def p_swing(app, opaque, transparent, p):
    _world(app)
    s = _build(app, opaque, 0, 0.40 + 0.26 * ease(p))
    _label(app, s["P"] + [0.0, 0.0, -0.7], "SWUNG OUT, TURNED INTO PLACE", AMBER)


def p_pigtails(app, opaque, transparent, p):
    _world(app)
    s = _build(app, opaque, 0, 0.66 + 0.34 * ease(p))
    w = F["wind"]
    _label(app, s["P"] + [0.0, 0.0, -0.7], f"3 PIGTAILS, {w['pig_load_kn'] * 1000:.0f} N EACH", ORANGE)
    _label(app, s["P"] + [0.0, 0.0, 1.9], f"CORD {C['pigtail_kn']:.0f} kN: x{w['pig_factor']:.0f}", GREEN)


def p_order(app, opaque, transparent, p):
    _world(app)
    k = float(np.clip((p - 0.04) / 0.92, 0.0, 1.0)) * 39
    done = 1 + int(k)
    if done >= 40:
        _build(app, opaque, 40)
    else:
        _build(app, opaque, done, k - int(k))
    _dome_label(app, f"{min(done, 40)} / 40 HUNG", AMBER)
    if done >= 35:
        _label(app, np.array([0.0, 0.0, ss.web_z(0, 0) - 0.3]),
               f"CROWN: HAULED THE LAST {100 * F['reach']['haul_max_m']:.0f} cm ON ITS PIGTAILS", ORANGE)


def p_floating(app, opaque, transparent, p):
    _world(app)
    _build(app, opaque, 40)
    _label(app, np.array([0.0, 0.0, ss.hung_balance(ORDER[-1])[2] + 0.2]), "NONE OF THEM TOUCHING", AMBER)
    _label(app, np.array([0.0, 0.0, F["hang"]["rim_m"] - 0.4]),
           f"RIM {F['hang']['rim_m']:.1f} m ({ft(F['hang']['rim_m'])} ft) UP", WHITE)


def _pig_cords(level: int):
    return lambda b, corners: ss.pigtails(b, corners, 1.0, level)


def p_join(app, opaque, transparent, p):
    _world(app)
    gap = GAP * (1 - ease(min(1.0, p * 1.3)))
    lift = np.array([0.0, 0.0, ss.lift_z(1)])
    ss.dome_pose(opaque, np.eye(3), np.zeros(3), lift, gap, _pig_cords(1))
    ss.hoist_line(opaque, ss.hook_rest())
    _dome_label(app, f"GAP {100 * gap:.0f} cm", AMBER)


def _joined(app, level: int = 1) -> None:
    _all_hung(app, level, 0.0)


def p_lashed(app, opaque, transparent, p):
    _world(app)
    _joined(app)
    ss.hoist_line(opaque, ss.hook_rest())
    app.static_layer("sky:lash:1", lambda: ss.lashings_batch(1))
    la = F["lash"]
    _label(app, LASH_SEAM + np.array([0.0, -0.4, 0.5]), f"{la['lashings']} LASHINGS, {la['cord_m']:,.0f} m OF CORD", ORANGE)
    _dome_label(app, f"{la['seams']} SEAMS, NO SCREWS", AMBER, 0.6)


def p_apex(app, opaque, transparent, p):
    _world(app)
    _dome(app)
    grow = ease(min(1.0, p * 1.4))
    b = TriangleBatch()
    rig = ss.apex_rig(b, 1, grow)
    opaque.vertices.extend(b.vertices)
    a = F["apex"]
    _label(app, rig["ring"] + [0.0, 0.0, -0.45], f"{a['cords']} CORDS TO ONE FREE RING", ORANGE)
    _label(app, rig["apex"] + [0.0, 0.0, 0.5], "ONE LINE OUT THROUGH THE CAP", AMBER)
    _label(app, ss.joints(1)[np.argmin(ss.joints(1)[:, 1])] + [0, -0.3, -0.3],
           f"RIM CORDS AT {a['rim_deg']:.0f} deg", WHITE)


def p_headroom(app, opaque, transparent, p):
    _world(app)
    _dome(app)
    _apex(app)
    rim = F["hang"]["rim_m"]
    r = sw.triangles()["radius_m"]
    pts = []
    for k in range(36):
        a0, a1 = math.tau * k / 36, math.tau * (k + 1) / 36
        c = np.array([0.0, 0.0, rim])
        p0 = c + [r * 0.97 * math.cos(a0), r * 0.97 * math.sin(a0), 0]
        p1 = c + [r * 0.97 * math.cos(a1), r * 0.97 * math.sin(a1), 0]
        opaque.triangle(c, p0, p1, (0.62, 0.45, 0.28, 1.0))
        opaque.triangle(c, p1, p0, (0.62, 0.45, 0.28, 1.0))
        pts.append(p0)
    a = F["apex"]
    pole = np.array([r * 0.5, 0.0, rim])
    opaque.cylinder(pole, pole + [0, 0, a["head_half_m"]], 0.03, (0.95, 0.85, 0.2, 1.0), 6)
    _label(app, pole + [0, 0, a["head_half_m"] + 0.2], f"HALFWAY OUT: {a['head_half_m']:.1f} m UP", RED)
    _label(app, np.array([0.0, 0.0, rim + 0.15]), "A FLOOR AT THE RIM", WHITE)


def p_onepoint(app, opaque, transparent, p):
    _world(app, rigs=())
    o = F["one"]
    u = ease(float(np.clip((p - 0.15) / 0.75, 0, 1)))
    deck = cw.landmarks().deck_centre[2]
    start = deck + 0.05 - ss.BASE
    dz = start + (ss.lift_z(1) - start) * u
    lift = np.array([0.0, 0.0, dz])
    ss.dome_pose(opaque, np.eye(3), np.zeros(3), lift, 0.0)
    b = TriangleBatch()
    v = ss.joints(1) + np.array([0.0, 0.0, dz - ss.lift_z(1)])
    apex = v[np.argmax(v[:, 2])]
    ring = apex - [0, 0, C["master_drop_m"]]
    for q in v:
        d = ring - q
        horiz = math.hypot(d[0], d[1])
        if horiz > 1e-6 and math.degrees(math.atan2(d[2], horiz)) >= C["cord_min_deg"]:
            ss.tube(b, [q, ring], ss.rope_r(0.375), ss.CORD, 4)
    winch = ss.pulley_at(1) + [0, 0, -0.05]
    ss.tube(b, [ring, apex, winch], ss.rope_r(0.5), ss.WIRE_DARK, 6)
    opaque.vertices.extend(b.vertices)
    opaque.box(winch + [0, 0, 0.12], np.array([0.55, 0.30, 0.30]), ss.WINCH)
    opaque.cylinder(winch + [-0.28, 0, 0.12], winch + [0.28, 0, 0.12], 0.13, ss.STEEL, 12)
    _label(app, winch + [0, 0, 0.75], f"x{O['upgrade_lo']:.0f}: {o['lo_kn']:.1f} kN   x{O['upgrade_hi']:.0f}: {o['hi_kn']:.1f} kN", GREEN)
    _label(app, ring + [0, 0, -1.4], f"DOME + SKIN {o['mass_kg']:,.0f} kg = {o['w_kn']:.1f} kN", AMBER)
    _label(app, ss.winch_at() + [0, 0, 1.0], f"TODAY'S WINCH: {100 * o['now_x']:.0f}% OF IT", RED)


def _tilted(opaque, deg: float, skin: bool = False, axis=(1.0, 0.0, 0.0)) -> np.ndarray:
    """The joined dome on its apex cords, turned ``deg`` about the free ring."""
    v = ss.joints(1)
    apex = v[np.argmax(v[:, 2])]
    pivot = apex - [0, 0, C["master_drop_m"]]
    R = ss.rotation(axis, math.radians(deg))
    ss.dome_pose(opaque, R, pivot - [0, 0, ss.lift_z(1)], pivot, 0.0)
    b = TriangleBatch()
    for q in v:
        d = pivot - q
        horiz = math.hypot(d[0], d[1])
        if horiz > 1e-6 and math.degrees(math.atan2(d[2], horiz)) >= C["cord_min_deg"]:
            ss.tube(b, [pivot + R @ (q - pivot), pivot], ss.rope_r(0.375), ss.CORD, 4)
    ss.tube(b, [pivot, pivot + R @ (apex - pivot), ss.pulley_at(1)], ss.rope_r(0.5), ss.WIRE_DARK, 6)
    if skin:
        sk = ss.skin_batch(1)
        arr = np.asarray(sk.vertices, dtype=np.float64).reshape(-1, 10)
        arr[:, 0:3] = (arr[:, 0:3] - pivot) @ R.T + pivot
        arr[:, 3:6] = arr[:, 3:6] @ R.T
        b.vertices.extend(arr.reshape(-1).astype(np.float32).tolist())
    opaque.vertices.extend(b.vertices)
    return pivot


def p_level(app, opaque, transparent, p):
    _world(app)
    lv = F["level"]
    deg = lv["random_95_deg"] * (ease(min(1.0, p * 2.0)) - ease(max(0.0, p * 2.0 - 1.0)))
    pivot = _tilted(opaque, deg)
    _label(app, pivot + [0, 0, 1.4], f"UNSORTED: UP TO {lv['random_95_deg']:.1f} deg" if p < 0.55
           else "SORTED: LEVEL", RED if p < 0.55 else GREEN)
    _label(app, pivot + [0, 0, -3.0], f"{lv['rim_drop_mm_95'] / 10:.0f} cm ACROSS THE RIM", AMBER)


def p_skin(app, opaque, transparent, p):
    _world(app)
    _dome(app)
    _apex(app)
    g = ease(min(1.0, p * 1.3))
    sk = ss.skin_batch(1, g)
    opaque.vertices.extend(sk.vertices)
    s = F["skin"]
    _dome_label(app, f"{s['tubes']} TUBES OF SILICONE, {s['naphtha_l']:.0f} L OF NAPHTHA", AMBER, 0.4)
    _label(app, np.array([0.0, -3.4, F["hang"]["rim_m"] + 0.3]),
           f"{s['layers']:.0f} LAYERS: ${s['diy_usd']:,.0f} vs SAILCLOTH ${s['sail_usd']:,.0f}", GREEN)


def p_tight(app, opaque, transparent, p):
    _hanging(app)
    for k in range(4):
        t = ss.tie(k)
        inward = -np.array([t[0], t[1], 0.0]) / math.hypot(t[0], t[1])
        _spring(opaque, t + inward * 0.05, t + inward * 0.75 - [0, 0, 0.04])
    w = F["wind"]
    _label(app, ss.tie(1) + [0, 0, 1.0], f"10% SAG: TAUT AFTER {100 * F['tight_m']:.0f} cm OF LEAN", GREEN)
    _label(app, ss.tie(2) + [0, 0, 1.0], f"THEN +{w['kn_per_cm']:.1f} kN PER cm", RED)
    _label(app, ss.tie(3) + [0, 0, 1.0], f"5% SAG: {100 * F['tight_taut_m']:.1f} cm", RED)
    _label(app, ss.tie(0) + [0, 0, 1.0], "A SPRING AT EVERY END", AMBER)


def _spring(opaque, a, b, colour=(0.95, 0.85, 0.25, 1.0)) -> None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    u = d / L
    v = np.cross(u, [0, 0, 1.0])
    v /= np.linalg.norm(v)
    w = np.cross(u, v)
    pts = [a + u * L * t + (v * math.cos(t * 40) + w * math.sin(t * 40)) * 0.06
           for t in np.linspace(0, 1, 120)]
    ss.tube(opaque, pts, 0.012, colour, 4)


def p_wind(app, opaque, transparent, p):
    _world(app, rigs=())
    w = F["wind"]
    swing = w["gust_deg"] * math.sin(math.pi * min(1.0, p * 1.2)) if p < 0.5 else \
        w["storm_deg"] * math.sin(math.pi * float(np.clip((p - 0.5) * 2.0, 0, 1)))
    pivot = _tilted(opaque, swing, skin=True)
    gust = p < 0.5
    y0 = -6.5
    for dz in (-1.0, 0.0, 1.0):
        a = np.array([0.0, y0, pivot[2] - 2.0 + dz])
        opaque.arrow(a, a + [0, 1.6, 0], 0.06, (0.55, 0.85, 1.0, 1.0))
    _label(app, np.array([0.0, y0, pivot[2] - 0.7]),
           f"{C['gust_m_s'] * 3.6:.0f} km/h: {w['gust_kn']:.1f} kN, {w['gust_deg']:.0f} deg" if gust else
           f"{C['gust_hi_m_s'] * 3.6:.0f} km/h: {w['storm_kn']:.1f} kN, {w['storm_deg']:.0f} deg",
           AMBER if gust else RED)
    _label(app, pivot + [0, 0, 1.0], f"IT WEIGHS {w['w_kn']:.0f} kN", GREEN)


def p_nature(app, opaque, transparent, p):
    _hanging(app)
    n = F["nature"]
    for k, t in enumerate(ss.trees()):
        _label(app, t + [0, 0, 2.2], f"~{C['transpire_l_day']:.0f} L/DAY" if k == 1 else "ROOTS", BLUE)
    _label(app, ss.trees()[2] + [0, 0, 14.0], "SHADE", GREEN)
    _label(app, np.array([0.0, 0.0, 1.3]), "NOTHING TOUCHES THE GROUND", AMBER)
    _label(app, ss.next_trees()[0] + [0, 0, 1.5], "THE NEXT TREE IS THE ANCHOR", WHITE)
    del n


def p_higher(app, opaque, transparent, p):
    _world(app, webs=(1,), rigs=(1,))
    _joined(app)
    ss.hoist_line(opaque, ss.hook_rest())
    ss.straps(opaque, 2)
    a = ease(min(1.0, p * 2.0))
    b = ease(float(np.clip(p * 2.0 - 0.8, 0, 1)))
    _x(opaque, 2, a, ease(float(np.clip(p * 2.0 - 0.4, 0, 1))))
    if b > 0.01:
        ss.tube(opaque, ss.spiral_points(2, b), ss.rope_r(0.375), ss.SPIRAL, 5)
    t2 = F["tree2"]
    _label(app, ss.tie(1, 2) + [0, 0, 0.8], f"EXPERIMENTAL: {C['anchor2_m']:.0f} m ({ft(C['anchor2_m'])} ft)", RED)
    _label(app, ss.tie(2, 2) + [0, 0, 0.8], f"UNGUYED MARGIN {t2['factor']:.1f}; GUY {t2['guy_kn']:.0f} kN", RED)


@lru_cache(maxsize=None)
def _web1_parts():
    """The first web, as a list of polylines, for taking it apart."""
    return ss.x_ropes(1), ss.spiral_points(1)


def p_inway(app, opaque, transparent, p):
    _world(app, webs=(2,), rigs=(2,))
    ss.straps(opaque, 1)
    lift = np.array([0.0, 0.0, ss.lift_z(1)])
    long = ease(min(1.0, p / 0.35))

    def cords(b, corners):
        ss.pigtails(b, corners, long, 2)
    ss.dome_pose(opaque, np.eye(3), np.zeros(3), lift, 0.0, cords)
    xs, spiral = _web1_parts()
    out = ease(float(np.clip((p - 0.40) / 0.35, 0, 1)))
    if out < 1:
        n = len(spiral)
        ss.tube(opaque, spiral[int(out * (n - 2)):], ss.rope_r(0.375), ss.SPIRAL, 5)
    gone = ease(float(np.clip((p - 0.75) / 0.25, 0, 1)))
    if gone < 1:
        for rope in xs:
            keep = max(2, int(len(rope) * (1 - gone)))
            ss.tube(opaque, rope[:keep], ss.rope_r(0.5), ss.WIRE)
    ss.hoist_line(opaque, ss.hook_rest(2), 2)
    r = F["raise"]
    _label(app, np.array([0.0, 0.0, r["web1_centre_m"] + 0.4]),
           f"FIRST WEB {r['web1_centre_m']:.1f} m: THE DOME MUST PASS {r['clash_m']:.1f} m ABOVE IT", RED)
    _label(app, np.array([0.0, 0.0, ss.web_z(0, 0, 2) + 0.9]), "HUNG FROM THE SECOND WEB FIRST", AMBER)


def _tree_dirs() -> np.ndarray:
    t = np.array([[x, y] for x, y in sw.tree_xy()], float)
    return t / np.linalg.norm(t, axis=1, keepdims=True)


def raise_pose(p: float):
    """The joined dome, ``p`` of the way up: one corner a step at a time, in
    order round the trees. Returns (rotation, rim centre, corner raised)."""
    r = F["raise"]
    steps = r["pulls"]
    s = float(np.clip(p, 0, 1)) * steps
    full, part = int(s), s - int(s)
    step = r["rise_m"] / r["rounds"]
    h = np.zeros(4)
    for k in range(4):
        h[k] = step * (full // 4 + (1 if k < full % 4 else 0))
    active = full % 4 if full < steps else None
    if active is not None:
        h[active] += step * ease(part)
    xy = _tree_dirs() * sw.triangles()["radius_m"]
    A = np.c_[np.ones(4), xy]
    a, bx, cy = np.linalg.lstsq(A, h, rcond=None)[0]
    n = np.array([-bx, -cy, 1.0])
    n /= np.linalg.norm(n)
    R = ss.rotation(np.cross([0, 0, 1.0], n), math.acos(float(np.clip(n[2], -1, 1))))
    centre = np.array([0.0, 0.0, ss.BASE + ss.lift_z(1) + a])
    return R, centre, active


def p_corners(app, opaque, transparent, p):
    _world(app, webs=(2,), rigs=(2,))
    R, centre, active = raise_pose(p)
    ss.dome_pose(opaque, R, np.array([0.0, 0.0, ss.BASE]), centre, 0.0, _pig_cords(2))
    r = F["raise"]
    if active is not None:
        d = _tree_dirs()[active] * sw.triangles()["radius_m"]
        top = np.array([d[0], d[1], centre[2] + 0.9])
        opaque.arrow(top - [0, 0, 0.8], top + [0, 0, 0.3], 0.07, (1.0, 0.86, 0.2, 1.0))
    s = int(float(np.clip(p, 0, 1)) * r["pulls"])
    _label(app, np.array([0.0, 0.0, ss.web_z(0, 0, 2) + 0.9]), f"PULL {min(s + 1, r['pulls'])} OF {r['pulls']}", AMBER)
    _label(app, centre + [0, 0, 3.6], f"HEAVIEST CORNER {r['corner_pull_kn']:.1f} kN", WHITE)


def p_leave(app, opaque, transparent, p):
    _hanging(app)
    fl, o = F["floor"], F["one"]
    _dome_label(app, f"SHELL {o['mass_kg']:,.0f} kg: {o['xd']['tension_kn']:.0f} kN, {o['xd']['rope']}", GREEN, 0.6)
    _label(app, np.array([0.0, 0.0, F["hang"]["rim_m"] - 0.6]),
           f"+ FLOOR AND CONTENTS {fl['mass_kg'] / 1000:.1f} t: {fl['tension_kn']:.0f} kN, {fl['rope']}", RED)


def p_caveats(app, opaque, transparent, p):
    _hanging(app)
    t = ss.trees()
    _label(app, t[2] + [0, 0, ss.TREE_H + 0.8], "LIGHTNING: TALLEST THING, STEEL TO THE DOME", RED)
    _label(app, ss.tie(1) + [0, 0, 0.9], "TRUNKS GROW: LOOSEN THE STRAPS", AMBER)
    _label(app, t[3] + [0, 0, 12.0], "DEADWOOD FALLS", AMBER)
    _label(app, t[0] + [0, 0, 1.6], "ROT HIDES: INSPECT EVERY SEASON", WHITE)


def p_safety(app, opaque, transparent, p):
    _world(app)
    s = _build(app, opaque, 6, 0.14 + 0.20 * ease(p))
    deck = cw.landmarks().deck_centre
    rr = 1.6
    ring = [np.array([rr * math.cos(a), rr * math.sin(a), deck[2] + 0.025]) for a in np.linspace(0, math.tau, 49)]
    ss.tube(opaque, ring, 0.05, (0.95, 0.20, 0.15, 1.0), 5)
    sf = F["safety"]
    _label(app, s["P"] + [0, 0, -0.8], f"FROM {sf['drop_m']:.1f} m: {sf['impact_kmh']:.0f} km/h", RED)
    _label(app, deck + [0, -rr, 0.5], "NOBODY INSIDE THE RING", RED)


def p_close(app, opaque, transparent, p):
    _hanging(app)
    _dome_label(app, "BUILT WITH THE TREES", AMBER, 0.6)


def _batched(painter):
    """Every rope a painter draws in a frame goes to the GPU in one batch."""
    def paint(app, opaque, transparent, p):
        with ss.batched(opaque):
            painter(app, opaque, transparent, p)
    paint.__name__ = painter.__name__
    return paint


SCENES = {
    "open": p_open, "declared": p_declared, "corrections": p_corrections, "trees": p_trees,
    "xrope": p_xrope, "guys": p_guys, "treepost": p_treepost, "spiral": p_spiral, "winch": p_winch,
    "harness": p_harness, "hoist": p_hoist, "swing": p_swing, "pigtails": p_pigtails, "order": p_order,
    "floating": p_floating, "join": p_join, "lashed": p_lashed, "apex": p_apex, "headroom": p_headroom,
    "onepoint": p_onepoint, "level": p_level, "skin": p_skin, "tight": p_tight, "wind": p_wind,
    "nature": p_nature, "higher": p_higher, "inway": p_inway, "corners": p_corners, "leave": p_leave,
    "caveats": p_caveats, "safety": p_safety, "close": p_close,
}
SCENES = {slug: _batched(painter) for slug, painter in SCENES.items()}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

MATH = ("declared",)


def _lash_seam() -> np.ndarray:
    """A seam on the south face, at eye level in the lower band, to film a lashing."""
    v = ss.joints(1)
    best = None
    rim = v[:, 2].min()
    for a, c in ss.seam_pairs():
        m = (v[a] + v[c]) / 2
        if m[2] - rim < 0.6:
            continue
        score = -m[1] - abs(m[0]) - abs(m[2] - rim - 1.2)
        if best is None or score > best[0]:
            best = (score, m)
    return best[1]


LASH_SEAM = _lash_seam()


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
    hang = F["hang"]
    mid = np.array([0.0, 0.0, (hang["rim_m"] + hang["web_centre_m"]) / 2])
    web = np.array([0.0, 0.0, hang["web_centre_m"] - 0.4])
    deck = m.deck_centre + [0, 0, 0.6]
    first = ss.hung_balance(ORDER[0])
    s0 = ss.trip(ORDER[0], 0.12)
    mid2 = np.array([0.0, 0.0, F["hang2"]["rim_m"] + 1.6])
    rising = np.array([0.0, 0.0, (hang["rim_m"] + F["hang2"]["rim_m"]) / 2 + 2.0])
    hero = np.array(cw.HERO_EYE)
    rim = hang["rim_m"]
    t1 = ss.trees()[1]
    seam = LASH_SEAM
    seam_out = np.array([seam[0], seam[1], 0.0]) / max(1e-6, math.hypot(seam[0], seam[1]))
    table = {
        "open": shots.crane_reveal(mid, hero + [0.0, 2.0, -1.8], hero + [0.6, -3.5, 3.5], 40, 50,
                                   look_start=deck),
        "declared": shots.orbit(mid, 15.0, 1.0, -100, 16, 48),
        "corrections": shots.push_in(s0["P"] + [0, 0, 0.4], s0["P"] + [1.0, -3.8, 6.0],
                                     s0["P"] + [0.7, -2.9, 5.0], 56, 52),
        "trees": shots.orbit(np.array([0.0, 0.0, 3.0]), 16.0, 6.0, -98, 22, 50),
        "xrope": shots.orbit(web, 14.0, 0.5, -110, 30, 50),
        "guys": shots.orbit(np.array([0.0, 0.0, 4.0]), 17.5, 3.5, -95, -20, 54),
        "treepost": shots.push_in(t1 + np.array([-0.9, 0.9, 3.6]), np.array([-2.2, 0.2, 2.0]),
                                  np.array([-1.0, -0.8, 2.2]), 58, 56),
        "spiral": shots.crane_reveal(web, np.array([1.5, -11.0, 6.0]), np.array([0.5, -8.5, 13.0]), 50, 50),
        "winch": shots.push_in(ss.winch_at() + [0.0, 0.0, 0.9], ss.winch_at() + [3.4, 1.4, 1.9],
                               ss.winch_at() + [2.5, 1.0, 1.6], 50, 46),
        "harness": shots.push_in(s0["P"] + [0, 0, 0.5], s0["P"] + [0.8, -3.6, 4.8],
                                 s0["P"] + [0.5, -2.6, 4.0], 54, 50),
        "hoist": shots.orbit(np.array([0.0, 0.0, 3.3]), 11.0, 0.2, -100, 20, 50),
        "swing": shots.orbit(mid, 12.0, 0.4, -92, 18, 50),
        "pigtails": shots.push_in(first + [0, 0, 0.7], first + np.array([first[0], first[1], 0]) * 0.2
                                  + np.array([0.0, -8.5, 0.6]), first + np.array([0.0, -6.2, 0.6]), 46, 40),
        "order": shots.orbit(mid, 14.5, 1.6, -105, 40, 50),
        "floating": shots.low_hero(mid, 6.0, eye_height=1.3, start_deg=-110, sweep_deg=45, look_up=1.0, fov=60),
        "join": shots.orbit(mid, 9.5, 0.2, -95, 25, 50),
        "lashed": shots.push_in(seam, seam + seam_out * 3.8 + [0.5, 0.0, 0.7],
                                seam + seam_out * 2.8 + [0.4, 0.0, 0.5], 48, 44),
        "apex": shots.orbit(mid, 9.0, -0.6, -100, 30, 54),
        "headroom": shots.hold(np.array([-0.8, 1.2, rim + 1.7]), np.array([1.48, 0.0, rim + 0.7]), 64),
        "onepoint": shots.orbit(np.array([0.0, 0.0, 3.6]), 14.0, 1.0, -98, 22, 54),
        "level": shots.orbit(mid, 11.0, 0.0, -90, 8, 50),
        "skin": shots.orbit(mid, 11.5, 0.8, -110, 35, 50),
        "tight": shots.orbit(web, 15.0, 1.0, -110, 30, 52),
        "wind": shots.orbit(mid, 15.5, 0.6, -178, 10, 52),
        "nature": shots.crane_reveal(mid, np.array([0.5, -12.5, 2.0]), np.array([1.5, -17.0, 10.0]), 50, 56),
        "higher": shots.crane_reveal(np.array([0.0, 0.0, 8.0]), np.array([0.5, -13.0, 4.0]),
                                     np.array([1.0, -15.5, 7.0]), 50, 54),
        "inway": shots.orbit(np.array([0.0, 0.0, 7.5]), 15.5, 0.5, -100, 25, 54),
        "corners": shots.orbit(rising, 16.0, 0.0, -110, 40, 54),
        "leave": shots.low_hero(mid, 11.0, eye_height=1.6, start_deg=-112, sweep_deg=30, look_up=0.4, fov=56),
        "caveats": shots.orbit(np.array([0.0, 0.0, 7.0]), 17.0, 2.0, -100, 25, 58),
        "safety": shots.push_in(np.array([0.0, 0.0, 2.6]), np.array([1.0, -10.0, 6.5]),
                                np.array([0.6, -8.0, 5.6]), 52, 48),
        "close": shots.crane_reveal(mid, hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0], 46, 54, look_start=mid),
    }
    del mid2
    out = {}
    for slug, shot in table.items():
        if slug in MATH:
            shot = beside_worksheet(shot)
        out[slug] = shot if slug == "headroom" else cabin_stage.clear_view(shot, cabin_stage.safe)
    return out


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def anchor_blocked(eye, target, samples: int = 40) -> bool:
    """True when one of the anchor trees' crowns, or a trunk close to the
    lens, stands in the way."""
    t = np.linspace(0.0, 1.0, samples)[:, None]
    ray = np.asarray(eye, float) * (1 - t) + np.asarray(target, float) * t
    for tr, clear in [(x, 12.8) for x in ss.trees()] + [(x, 8.8) for x in ss.next_trees()]:
        d = np.hypot(ray[:, 0] - tr[0], ray[:, 1] - tr[1])
        z = ray[:, 2] - tr[2]
        crown = (z > clear) & (d < 2.8)
        trunk = (t[:, 0] < 0.35) & (d < 0.6) & (z < ss.TREE_H)
        if np.any(crown | trunk):
            return True
    return False


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=(),
        overlay: str | None = None) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, overlay)


def _declared_steps() -> list[str]:
    kinds: dict[str, int] = {}
    for _n, _v, _u, k, _w in sw.CONSTANTS:
        kinds[k] = kinds.get(k, 0) + 1
    w = F["weights"]
    return [
        "WEIGHED OR OWNED, by the owner:",
        f"   struts {O['strut_kg_lo']:.0f} to {O['strut_kg_hi']:.0f} kg; loads use {O['strut_kg_hi']:.0f}",
        f"   12 V winch {O['winch_lb']:,.0f} lb; planned x{O['upgrade_lo']:.0f} to x{O['upgrade_hi']:.0f}",
        "MEASURED off the solver's dome:",
        f"   {F['faces']} triangles, {w['struts']} struts, {F['lash']['seams']} seams, 26 joints",
        f"   solver's own estimate: {w['solver_kg']:.0f} kg of frame ({w['solver_strut_kg']:.1f} kg a strut)",
        f"DECLARED, typed in by a person: {len(sw.CONSTANTS)}, a reason each",
        f"   {kinds.get('assumption', 0)} assumptions, {kinds.get('estimate', 0)} estimates, "
        f"{kinds.get('nominal', 0)} catalogue sizes, {kinds.get('standard', 0)} standards",
        f"   trees {C['tree_square_m']:.0f} m square, ties at {C['anchor1_m']:.0f} m; "
        f"next trees {C['next_tree_m']:.0f} m out",
        f"   sag {100 * C['sag_ratio']:.0f}% of the span; rope worked at 1/{C['design_factor']:.0f}",
        f"   trunk {100 * C['tree_dbh_m']:.0f} cm; green pine {C['green_mor_mpa']:.0f} MPa, "
        f"E {C['green_e_gpa']:.0f} GPa (estimates)",
        f"   skin: cotton {C['cotton_gsm']:.0f} g/m2 + silicone {C['silicone_gsm']:.0f} g/m2 a layer (estimate)",
        f"Ropes are drawn {ss.ROPE_DRAWN:.0f}x thicker, to be seen.",
    ]


def _chapters() -> tuple[Chapter, ...]:
    f = F
    w8 = f["weights"]
    x, xt, sp, st = f["x"], f["x_taut"], f["spread"], f["spread_taut"]
    t1, tt, t2, pv = f["tree1"], f["tree1_taut"], f["tree2"], f["post"]
    spi, h, hk, ho = f["spiral"], f["hang"], f["harness"], f["hoist"]
    w, r, sf, rc = f["wind"], f["raise"], f["safety"], f["reach"]
    la, ap, sk, one, lv, fl, mat = f["lash"], f["apex"], f["skin"], f["one"], f["level"], f["floor"], f["materials"]
    legs = hk["rows"]
    rows = [
        (1, "open", "Built in the air", "Forty triangles, hung from a web.",
         "Most domes are built from the ground up, a ring at a time, with scaffolding inside. This one is "
         "built in the air. A web of cable strung between four living trees, and every triangle of the dome "
         "hauled up by a battery winch, swung into its place, and left hanging there on three cords. Then "
         "joined, gathered to one point at the top, skinned, and perhaps never let down. The ground, the "
         "foundation and the gasket can wait. Here is how, with every load worked out, and the numbers that "
         "argue back.",
         [f"{f['faces']} triangles, {w8['frame_hi_kg']:,.0f} kg of frame", f"web at {C['anchor1_m']:.0f} m"]),
        (2, "declared", "What is weighed, what is assumed", "Two tables, before the numbers.",
         f"First, what this rests on, in two tables. What the owner weighed and owns: struts of "
         f"{O['strut_kg_lo']:.0f} to {O['strut_kg_hi']:.0f} kilograms, and a {O['winch_lb']:,.0f} pound, twelve "
         f"volt winch. And what a person assumed, each with a reason: where the trees stand, how high the ropes "
         f"are tied, how far they sag, what rope, wood and cloth will take. {len(sw.CONSTANTS)} figures. Every "
         f"load in this film uses the heaviest strut. Change any line, and every number after it changes.",
         _declared_steps(), "math"),
        (3, "corrections", "Two corrections", "The winch, and what a strut weighs.",
         f"The first cut of this film got two things wrong. It showed a hand winch. The winch is electric: "
         f"twelve volts, off a battery, rated {O['winch_lb']:,.0f} pounds, {ho['winch_kn']:.1f} kilonewtons. "
         f"And it weighed the frame with the solver's estimate, {w8['solver_strut_kg']:.1f} kilograms a strut. "
         f"The owner's struts, weighed, are {O['strut_kg_lo']:.0f} to {O['strut_kg_hi']:.0f}: "
         f"{w8['ratio_lo']:.1f} to {w8['ratio_hi']:.1f} times as heavy. So a triangle is "
         f"{w8['tri_lo_kg']:.0f} to {w8['tri_hi_kg']:.0f} kilograms, and the frame "
         f"{w8['frame_lo_kg']:,.0f} to {w8['frame_hi_kg']:,.0f}. Every load from here on is the heavier one.",
         [f"solver: {w8['solver_kg']:.0f} kg / {w8['struts']} = {w8['solver_strut_kg']:.2f} kg a strut",
          f"weighed: {O['strut_kg_lo']:.0f}-{O['strut_kg_hi']:.0f} kg = x{w8['ratio_lo']:.1f}-{w8['ratio_hi']:.1f}",
          f"triangle 3 x strut = {w8['tri_lo_kg']:.0f}-{w8['tri_hi_kg']:.0f} kg",
          f"frame {w8['struts']} struts = {w8['frame_lo_kg']:,.0f}-{w8['frame_hi_kg']:,.0f} kg "
          f"({lb(w8['frame_hi_kg'])} lb)"]),
        (4, "trees", "Four trees, a square", "The X runs corner to corner.",
         f"Four trees round the pad, near enough a square, {C['tree_square_m']:.0f} metres a side. The ropes run "
         f"corner to corner, so each one spans the diagonal: {x['span_m']:.1f} metres, about "
         f"{ft(x['span_m'])} feet. They are tied {C['anchor1_m']:.0f} metres up, {ft(C['anchor1_m'])} feet, on "
         f"tree-saver straps, never wrapped bare round the bark. Real trees are never a perfect square. The "
         f"arithmetic only needs the longest diagonal, and the height of the lowest tie.",
         [f"side {C['tree_square_m']:.1f} m", f"diagonal = side x 1.414 = {x['span_m']:.2f} m",
          f"ties at {C['anchor1_m']:.0f} m"]),
        (5, "xrope", "Two ropes make an X", "And how hard they pull.",
         f"Two wire ropes, crossing in the middle, carrying {f['frame_kg']:,.0f} kilograms of frame. A rope "
         f"with weight on it pulls sideways on its ends, and the flatter it hangs, the harder it pulls. Sagging "
         f"ten percent, {sp['sag_m']:.1f} metres, with each triangle's cords on the rope nearest it, the worse "
         f"rope pulls {sp['tension_kn']:.0f} kilonewtons: five-eighths wire rope, worked at a fifth of its "
         f"strength. Pull it flatter, to five percent, and it doubles, to {st['tension_kn']:.0f}, and wants "
         f"{st['rope']} rope. With real struts, a deep sag is not a choice. It is the design.",
         [f"H = M / s: the beam moment at midspan over the sag",
          f"10% sag: H {sp['horizontal_kn']:.1f} kN, T {sp['tension_kn']:.1f} kN, {sp['rope']}",
          f"5% sag: T {st['tension_kn']:.1f} kN, {st['rope']}",
          f"all at the crossing, 10%: {x['tension_kn']:.1f} kN"]),
        (6, "guys", "Guy to the next tree", "Unguyed, a flat web breaks its trees.",
         f"And the trees take all of it, eight metres up, as a lever. A {100 * C['tree_dbh_m']:.0f} centimetre "
         f"pine, green, breaks in bending at about {C['green_mor_mpa']:.0f} megapascals. Unguyed, the ten "
         f"percent web works its trunk to a margin of {t1['factor']:.1f}, where a living tree should keep "
         f"three; the five percent web, to {tt['factor']:.2f}, which is past breaking. So every anchor tree is "
         f"guyed, and the guy goes where the owner put it: to the base of the next tree out, "
         f"{C['next_tree_m']:.0f} metres behind. No ground anchors to buy or dig. The guy pulls "
         f"{t1['guy_kn']:.0f} kilonewtons, {t1['guy_rope']} rope, on a trunk at its strongest point, its roots.",
         [f"M = {sp['horizontal_kn']:.1f} kN x {C['anchor1_m']:.0f} m = {t1['moment_knm']:.0f} kN m",
          f"stress = M / (pi d^3/32) = {t1['stress_mpa']:.1f} MPa: margin {t1['factor']:.2f}",
          f"5% sag: {tt['stress_mpa']:.0f} MPa, margin {tt['factor']:.2f}",
          f"guy at {t1['guy_deg']:.0f} deg to the next tree's base: {t1['guy_kn']:.1f} kN"]),
        (7, "treepost", "A tree is a better post", "Why cut it down to hold something up?",
         f"Guyed at the tie, the anchor tree stops being a lever. It becomes a post, squeezed from above by "
         f"{t1['squeeze_kn']:.0f} kilonewtons, held at the top by its guy, and fixed in the ground by its own "
         f"roots. Cut that tree, mill it, haul it to a store and back, and you get a six by six post. Eight "
         f"metres tall, that post buckles at about {pv['post_kn']:.0f} kilonewtons. The living trunk it came "
         f"from, at about {pv['tree_kn'] / 1000:.1f} meganewtons, is {pv['times']:.0f} times stiffer, and it "
         f"carries this web with {t1['buckle_factor']:.0f} times to spare. The tree was already the better post.",
         [f"P = pi^2 E I / (0.7 h)^2, h = {C['anchor1_m']:.0f} m",
          f"6x6, {C['post_e_gpa']:.0f} GPa: {pv['post_kn']:.0f} kN", f"trunk {100 * C['tree_dbh_m']:.0f} cm, "
          f"{C['green_e_gpa']:.0f} GPa: {pv['tree_kn']:,.0f} kN",
          f"squeeze {t1['squeeze_kn']:.0f} kN: x{t1['buckle_factor']:.0f}; crushing x{t1['crush_factor']:.0f}"]),
        (8, "spiral", "A spiral over the footprint", "So a thrown cord always finds a strand.",
         f"Then the spiral, woven out from the crossing and seized to the X wherever it crosses. It covers the "
         f"dome's footprint, a circle {2 * spi['radius_m']:.1f} metres across, but above it. The turns are "
         f"{100 * C['spiral_pitch_m']:.0f} centimetres apart, so a cord thrown up from anywhere under it always "
         f"lands across a strand. That is {spi['turns']:.1f} turns, {spi['length_m']:.0f} metres of line, and "
         f"{spi['ties']} seizings. The X carries the weight. The spiral gives the pigtails somewhere to land.",
         [f"turns = r / pitch = {spi['radius_m']:.2f} / {C['spiral_pitch_m']:.1f} = {spi['turns']:.1f}",
          f"length = {spi['length_m']:.1f} m", f"seizings: {spi['ties']}"]),
        (9, "winch", "A twelve-volt winch", "Forty lifts on a fifth of one battery.",
         f"The winch is a twelve volt one, bolted to the first tree and run off a battery. Its line runs up the "
         f"trunk to a block at the tie, along under the rope to a pulley at the crossing, and down to a hook. "
         f"The heaviest triangle, {ho['heaviest_kg']:.0f} kilograms, pulls {ho['pull_kn']:.2f} kilonewtons "
         f"against a winch rated {ho['winch_kn']:.1f}: {ho['winch_margin']:.0f} times over. Lifting it "
         f"{ho['hook_m']:.1f} metres costs about {ho['one_wh']:.0f} watt hours, so all forty take "
         f"{ho['all_wh']:.0f}, about {100 * ho['battery_share']:.0f} percent of what one hundred amp hour "
         f"battery should give.",
         [f"pull {ho['heaviest_kg']:.0f} kg x g = {ho['pull_kn']:.3f} kN; winch x{ho['winch_margin']:.1f}",
          f"energy = m g h / {C['winch_eff']:.2f} = {ho['one_wh']:.1f} Wh a lift",
          f"40 lifts: {ho['all_wh']:.0f} Wh of {C['battery_wh'] * C['battery_use']:.0f} usable"]),
        (10, "harness", "A harness that hangs it flat", "Three legs, one eye, over the balance point.",
         f"A triangle comes up in a harness: three legs, one to each corner, meeting in an eye "
         f"{C['bridle_h_m']:.0f} metre above the point the triangle balances on. Hook the eye and it rises flat. "
         f"The dome has {hk['kinds']} shapes of triangle, so there are {hk['kinds']} harnesses. The one with two "
         f"short sides needs legs of {legs[0]['legs_m'][0]:.2f} and {legs[0]['legs_m'][1]:.2f} metres; the "
         f"equal one, three of {legs[1]['legs_m'][0]:.2f}. Make them once, label them, and use them forty times.",
         [f"{hk['kinds']} shapes: sides " + "; ".join("/".join(f"{s:.2f}" for s in row["sides_m"]) for row in legs),
          *[f"legs {' / '.join(f'{l:.2f}' for l in row['legs_m'])} m" for row in legs]]),
        (11, "hoist", "Up, flat", "Under two minutes a triangle.",
         f"Up it goes, flat, under the crossing. The hook tops out {ho['hook_m']:.1f} metres up, "
         f"{ft(ho['hook_m'])} feet. A small twelve volt winch brings in about {C['winch_m_min']:.0f} metres a "
         f"minute at this load, so a triangle takes {ho['lift_min']:.1f} minutes to raise, and all forty about "
         f"an hour of winding. Flat matters: a triangle that tips on the way up catches the line, the X, and "
         f"anyone underneath.",
         [f"{ho['hook_m']:.2f} m / {C['winch_m_min']:.0f} m/min = {ho['lift_min']:.2f} min",
          f"x 40 = {ho['all_lift_min']:.0f} min"]),
        (12, "swing", "Swing it out", "From the centre to where it belongs.",
         "At the top it hangs from the centre, and its place is somewhere else. A tag line from the ground "
         "swings it out from under the crossing, and as it goes it is turned, from flat to the angle it will "
         "sit at in the finished dome. The hook stays on. Nothing lets go until the pigtails are on.",
         ["start: under the crossing, flat", "end: its own place, its own angle"]),
        (13, "pigtails", "Three pigtails over the web", "Then it slips the harness.",
         f"Every triangle carries three pigtails, a cord tied at each corner. Thrown up over the spiral and "
         f"tied back, they hold it where it is. Then it slips the harness, and the hook goes back for the next. "
         f"The pigtails are {h['pig_min_m']:.1f} to {h['pig_max_m']:.1f} metres long: {h['pigtails']} of them, "
         f"{h['cord_m']:.0f} metres of cord. Each holds {w['pig_load_kn'] * 1000:.0f} newtons, on a cord that "
         f"breaks at {C['pigtail_kn']:.0f} kilonewtons: {w['pig_factor']:.0f} times over.",
         [f"pigtail = web height - corner + {C['pigtail_tie_m']:.1f} m tie",
          f"{h['pigtails']} pigtails, {h['pig_min_m']:.2f} to {h['pig_max_m']:.2f} m, {h['cord_m']:.0f} m",
          f"load {ho['heaviest_kg']:.0f} kg / 3 = {w['pig_load_kn'] * 1000:.0f} N; cord x{w['pig_factor']:.0f}"]),
        (14, "order", "Rim first, crown last", "Keep the middle clear for the hook.",
         f"The order matters. The hook comes down at the centre, so the middle has to stay clear until the "
         f"end: hang the rim first, then the band above it, and the crown last. And the crown is where the "
         f"hook runs out. With a metre of harness above them, {rc['short']} crown triangles would need the hook "
         f"higher than it can climb. They are hung low, the pigtails go on, and they are hauled the last "
         f"{100 * rc['haul_max_m']:.0f} centimetres on their own cords.",
         ["order: by distance from the centre, outermost first",
          f"hook top {rc['hook_top_m']:.2f} m", f"{rc['short']} crown triangles short by up to "
          f"{100 * rc['haul_max_m']:.0f} cm"]),
        (15, "floating", "Forty, floating", "None of them touching.",
         f"And there it is. Forty triangles, each in its place, each on its own three cords, none of them "
         f"touching. The rim hangs {h['rim_m']:.1f} metres up, {ft(h['rim_m'])} feet, the crown at "
         f"{h['apex_m']:.1f}. Walk underneath and look up through it. Every seam is still open, every edge is "
         f"reachable, and nothing is holding anything else up.",
         [f"rim {h['rim_m']:.2f} m, crown {h['apex_m']:.2f} m", f"web {h['web_centre_m']:.2f} m at the centre",
          f"gap between triangles: {100 * GAP:.0f} cm (drawn)"]),
        (16, "join", "Join them later", "The gap closes on the cords.",
         "Joining is later, and it is easy from here. Each triangle swings a little on its cords, so its "
         "neighbour can be drawn up to it and the seam closed, a pair at a time, with nothing to lift. When "
         "the last seam closes, forty separate triangles are one dome, still hanging where they were.",
         ["each triangle: its own three cords", "joined: one dome, the same cords"]),
        (17, "lashed", "Lashed, not screwed", "Cord, strut to strut, under a hard shell.",
         f"And the seams need not be screwed. A dome works mostly in compression: its triangles lean on each "
         f"other. A joint only has to stop them sliding apart, and cord can do that. Lash each of the "
         f"{la['seams']} seams in {C['lash_per_seam']:.0f} places, {C['lash_wraps']:.0f} turns round both "
         f"struts, and it takes {la['lashings']} lashings and about {la['cord_m']:,.0f} metres of cord. Cord "
         f"stretches and creeps, so lashings want re-tightening, and they suit best a dome whose shell, "
         f"fibreglass, say, takes the pulling. Under a hard shell, the lashings only hold the shape.",
         [f"seams: {la['seams']} (edges two triangles share)",
          f"{la['seams']} x {C['lash_per_seam']:.0f} = {la['lashings']} lashings",
          f"{C['lash_wraps']:.0f} turns x {la['girth_m']:.2f} m + tie = {la['per_m']:.1f} m each",
          f"cord: {la['cord_m']:,.0f} m"]),
        (18, "apex", "Every cord to the apex", "Through the air, not along the struts.",
         f"Then the pigtails come off the web and are gathered to the top, so the whole dome hangs from one "
         f"point, and the shell can go over the cords. How they run matters. Laid along the struts, a cord "
         f"pressed on a curved surface lifts nothing where it lies: what it pulls up at its corner it pushes "
         f"back down along its length, and the whole weight ends up on the cap. Run straight through the air "
         f"inside, from each joint to one free ring just under the cap, every joint is lifted by its own cord. "
         f"{ap['cords'] - 1} cords and the apex, and one line out through the cap. The rim cords lean in at "
         f"{ap['rim_deg']:.0f} degrees and squeeze the rim with {ap['rim_hoop_kn']:.1f} kilonewtons, which a "
         f"dome takes happily. {ap['strutted']} joints sit too close to the ring for a cord, and hang from the "
         f"apex on their struts.",
         [f"joints {ap['joints']}: {ap['cords'] - 1} cords + apex; {ap['strutted']} hang on struts",
          f"cord T = w / sin(angle); rim {ap['rim_deg']:.0f} deg",
          f"apex line carries {ap['apex_kn']:.1f} kN; hardest cord squeezes {ap['max_in_kn']:.1f} kN",
          f"rim ring squeeze: {ap['rim_hoop_kn']:.2f} kN", f"cord: {ap['cord_m']:.0f} m"]),
        (19, "headroom", "Cords across the room", "The price of one point.",
         f"And here is what that costs. Through the air means through the room. A cord from the rim to the "
         f"ring under the cap passes, halfway to the wall, only {ap['head_half_m']:.1f} metres above a floor "
         f"laid at the rim. Fine while it is a frame hanging in the trees. In a home, those cords are lowered "
         f"away once the dome is set where it will stay, or it is hung by its rim instead.",
         [f"ring {sw.triangles()['height_m'] - C['master_drop_m']:.2f} m above the rim",
          f"halfway out: {ap['head_half_m']:.2f} m above the floor"]),
        (20, "onepoint", "One winch, the whole dome", "Today's winch lifts a quarter of it.",
         f"With every cord at one point, one winch can lift the whole dome, up and down, evenly. But this is "
         f"the whole weight: the frame and a skin, {one['mass_kg']:,.0f} kilograms, {one['w_kn']:.1f} "
         f"kilonewtons. Today's winch lifts {100 * one['now_x']:.0f} percent of it. The planned one, "
         f"{O['upgrade_lo']:.0f} times bigger, lifts it with almost nothing to spare. {O['upgrade_hi']:.0f} times "
         f"bigger lifts it twice over, and that is the one to buy. Hang the winch itself at the crossing: "
         f"pulled from a tree, the line turns at the pulley and loads the X with {one['block_kn']:.0f} "
         f"kilonewtons, not {one['w_kn']:.0f}. And now every kilogram is at the crossing, so the ropes pull "
         f"{one['xd']['tension_kn']:.0f}: still {one['xd']['rope']}, with the guys at {one['tree']['guy_kn']:.0f}.",
         [f"dome {f['frame_kg']:,.0f} + skin {sk['mass_kg']:.0f} = {one['mass_kg']:,.0f} kg = {one['w_kn']:.1f} kN",
          f"x1 {one['now_kn']:.1f} kN ({100 * one['now_x']:.0f}%); x{O['upgrade_lo']:.0f} {one['lo_kn']:.1f} "
          f"(x{one['lo_x']:.2f}); x{O['upgrade_hi']:.0f} {one['hi_kn']:.1f} (x{one['hi_x']:.1f})",
          f"block, winch at a tree: W x 1.41 = {one['block_kn']:.1f} kN",
          f"X, all at the crossing: {one['xd']['tension_kn']:.1f} kN, {one['xd']['rope']}",
          f"lift {one['rise_m']:.1f} m: {one['wh']:.0f} Wh"]),
        (21, "level", "It hangs level, if you sort the struts", "A dome's weight is on its axis.",
         f"This is what a dome can do that a house cannot. Its weight sits on its own axis, so hung from one "
         f"point it hangs level by itself. A house, with its kitchen at one end and its loads everywhere, "
         f"would hang at whatever angle its contents chose. But your struts are not all the same. Placed at "
         f"random, struts of {O['strut_kg_lo']:.0f} to {O['strut_kg_hi']:.0f} kilograms tip it about "
         f"{lv['random_med_deg']:.0f} degree, and one time in twenty more than {lv['random_95_deg']:.0f}: "
         f"{lv['rim_drop_mm_95'] / 10:.0f} centimetres across the rim. Every heavy strut on one side, "
         f"{lv['worst_deg']:.0f}. So weigh them, and spread the heavy ones round the dome. Sorted, it hangs dead "
         f"level.",
         [f"tilt = atan(offset / {lv['depth_m']:.2f} m below the ring)",
          f"random: median {lv['random_med_deg']:.2f} deg, 1 in 20 {lv['random_95_deg']:.2f} deg",
          f"heavy on one side: {lv['worst_deg']:.1f} deg", f"sorted: {lv['even_deg']:.2f} deg"]),
        (22, "skin", "A silicone skin", "Cotton, soaked in silicone dissolved in naphtha.",
         f"The covering. Sailcloth would do, at about {C['sailcloth_usd_m2']:.0f} dollars a square metre. The "
         f"owner's way is cheaper: dissolve one hundred percent silicone in naphtha, soak cotton in it, and let "
         f"the naphtha evaporate. The silicone stays in the fibres, a waterproof, chemically quiet skin. Two "
         f"layers over {sk['shell_m2']:.0f} square metres of dome, with laps, take about {sk['tubes']} tubes of "
         f"silicone, {sk['naphtha_l']:.0f} litres of naphtha and {sk['cotton_m2']:.0f} square metres of cotton: "
         f"about {sk['diy_usd']:,.0f} dollars, against {sk['sail_usd']:,.0f} in sailcloth, and "
         f"{sk['mass_kg']:.0f} kilograms. Silicone sticks to silicone, so layers stack into one skin; almost "
         f"nothing else will stick to it later. Naphtha is very flammable: soak outdoors, far from any flame.",
         [f"area {sk['shell_m2']:.1f} m2 + {100 * C['skin_overlap']:.0f}% = {sk['area_m2']:.1f} m2 x "
          f"{sk['layers']:.0f} layers",
          f"silicone {sk['silicone_kg']:.1f} kg = {sk['silicone_l']:.1f} L = {sk['tubes']} tubes",
          f"naphtha {C['mix_parts']:.0f}:1 = {sk['naphtha_l']:.0f} L (estimate)",
          f"${sk['diy_usd']:,.0f} (${sk['per_m2_usd']:.0f}/m2) vs sailcloth ${sk['sail_usd']:,.0f}",
          f"skin {sk['mass_kg']:.0f} kg"]),
        (23, "tight", "A taut web is a stiff web", "Trees move. Give the rope a spring.",
         f"Trees move in the wind, and they move apart. A rope sagging ten percent goes straight once its "
         f"trees lean apart {100 * f['tight_m']:.0f} centimetres; at five percent, after only "
         f"{100 * f['tight_taut_m']:.1f}. After that the rope stretches, and every further centimetre adds "
         f"about {w['kn_per_cm']:.0f} kilonewtons. So the deep sag earns its keep twice, and the X still gets a "
         f"heavy spring at every end, to let it give.",
         [f"slack = 8 s^2 / 3L: 10% {100 * f['tight_m']:.1f} cm, 5% {100 * f['tight_taut_m']:.1f} cm",
          f"stretch: EA/L = {w['kn_per_cm']:.1f} kN per cm"]),
        (24, "wind", "Wind on a hung dome", "Heavy and round, it barely swings.",
         f"Skinned, the dome catches wind. Side on it shows {w['side_m2']:.1f} square metres. A "
         f"{C['gust_m_s'] * 3.6:.0f} kilometre an hour gust pushes it with about {w['gust_kn']:.1f} "
         f"kilonewtons; it weighs {w['w_kn']:.0f}, so it swings {w['gust_deg']:.0f} degrees. A "
         f"{C['gust_hi_m_s'] * 3.6:.0f} kilometre an hour storm, {w['storm_kn']:.1f} kilonewtons, "
         f"{w['storm_deg']:.0f} degrees. Its weight is what keeps it still, and its round shape sheds the wind "
         f"the same from every side. Tie it down to the trees on three sides before a storm all the same.",
         [f"F = 1/2 rho v^2 Cd A, A = pi R^2 / 2 = {w['side_m2']:.1f} m2",
          f"{C['gust_m_s']:.0f} m/s: {w['gust_kn']:.2f} kN -> atan(F/W) = {w['gust_deg']:.1f} deg",
          f"{C['gust_hi_m_s']:.0f} m/s: {w['storm_kn']:.2f} kN -> {w['storm_deg']:.1f} deg"]),
        (25, "nature", "Building with the trees", "Posts, shade and drainage, already standing.",
         f"Step back and look at what the trees are doing. They are the posts, stronger than anything sawn "
         f"from them. Their crowns shade the dome in summer. Their roots draw water out of the ground round "
         f"it, a mature pine perhaps {C['transpire_l_day']:.0f} litres on a summer day, "
         f"{f['nature']['drink_l_day']:.0f} for the four. Nothing touches the soil, so there is no "
         f"foundation, no damp rising, and air moves under and round it. And the guys tie to the next trees "
         f"out, so the anchors are trees too: a network of trees, doing a foundation's work. Why cut a tree "
         f"to make a post, when it is already the post?",
         [f"4 trees x ~{C['transpire_l_day']:.0f} L/day = ~{f['nature']['drink_l_day']:.0f} L/day (estimate)",
          f"ground contact: {f['nature']['ground_contact']}", f"ground anchors bought: {f['nature']['anchors_bought']}"]),
        (26, "higher", "A second web, if the trees allow", "Experimental, and planned before the trees are chosen.",
         f"Higher still is possible, and it is experimental. It depends on the trees, and it has to be "
         f"planned before they are chosen; the owner's are not set up for it. Strung at {C['anchor2_m']:.0f} "
         f"metres, the same pull is half again the lever: unguyed, the trunks would be worked to a margin of "
         f"{t2['factor']:.1f}, at the edge of breaking, and the guys pull {t2['guy_kn']:.0f} kilonewtons. Here is how it "
         f"would go, if the trees allowed it.",
         [f"M = {sp['horizontal_kn']:.1f} x {C['anchor2_m']:.0f} = {t2['moment_knm']:.0f} kN m",
          f"unguyed margin {t2['factor']:.2f}; guy {t2['guy_kn']:.1f} kN at {t2['guy_deg']:.0f} deg"]),
        (27, "inway", "The first web is in the way", "It has to come out.",
         f"The first web is in the way. Hung from the second, the crown rises to {r['apex2_m']:.1f} metres, "
         f"and the first web crosses at {r['web1_centre_m']:.1f}: the dome would pass {r['clash_m']:.1f} "
         f"metres up through it. So the dome is handed over first, on long cords from the second web, a "
         f"corner at a time. Then the first web comes out: the spiral unwound from its outer end, and each "
         f"rope of the X untied at one tree and pulled through from the other.",
         [f"crown on web 2: {r['apex2_m']:.2f} m", f"web 1 centre: {r['web1_centre_m']:.2f} m",
          f"overlap {r['clash_m']:.2f} m: web 1 comes out"]),
        (28, "corners", "A corner at a time", "Thirty-two pulls, and a bigger winch.",
         f"Then up, a corner at a time: the block moves over one corner, the winch raises that side "
         f"{100 * C['raise_step_m']:.0f} centimetres, its cords are re-tied, and on to the next, each step a "
         f"tilt of {r['tilt_deg']:.1f} degrees. {r['rise_m']:.0f} metres up is {r['rounds']} rounds of four, "
         f"{r['pulls']} pulls. The heaviest corner is {max(r['corner_kg']):.0f} kilograms, "
         f"{r['corner_pull_kn']:.1f} kilonewtons: more than today's winch, well within the "
         f"{O['upgrade_lo']:.0f} times one.",
         [f"rise {r['rise_m']:.1f} m / {C['raise_step_m']:.1f} m = {r['rounds']} rounds x 4 = {r['pulls']} pulls",
          f"heaviest corner {max(r['corner_kg']):.0f} kg = {r['corner_pull_kn']:.2f} kN",
          f"winch x1 {one['now_kn']:.1f} kN; x{O['upgrade_lo']:.0f} {one['lo_kn']:.1f} kN"]),
        (29, "leave", "Leave it hanging", "The shell, yes. A floor full of life, on bigger rope.",
         f"So, leave it up? The shell, frame and skin, {one['mass_kg']:,.0f} kilograms, hangs from this X on "
         f"{one['xd']['rope']} rope at {one['xd']['tension_kn']:.0f} kilonewtons, the trees guyed. Add a floor "
         f"and what a household puts on it, by the cell wall's own figure {fl['floor_kg'] / 1000:.1f} tonnes, "
         f"and it is {fl['mass_kg'] / 1000:.1f} tonnes, pulling {fl['tension_kn']:.0f} kilonewtons: "
         f"{fl['rope']} rope, and every guy and tree checked again. It can be done. It is a structure an "
         f"engineer and an arborist should sign, and it is priced here, not rated.",
         [f"shell: {one['mass_kg']:,.0f} kg -> {one['xd']['tension_kn']:.1f} kN, {one['xd']['rope']}",
          f"+ floor {fl['floor_kg']:,.0f} kg = {fl['mass_kg']:,.0f} kg -> {fl['tension_kn']:.1f} kN, {fl['rope']}",
          f"1 in works to {C['rope_1_kn'] / C['design_factor']:.0f} kN"]),
        (30, "caveats", "What the trees ask in return", "Lightning, growth, deadwood, rot.",
         "The trees give a lot, and they ask some things back. They are the tallest things on the hill, and "
         "now they carry steel rope to the dome: bond the ropes and ground them, or lightning will use them. "
         "Trunks grow, so tree-saver straps are loosened every year, never left to girdle the bark. Dead "
         "branches fall, so the crowns are cleaned before anything hangs under them. And rot hides, so an "
         "arborist looks at all eight trees every season, and after every big storm.",
         ["bond and ground the wire rope", "loosen straps yearly", "clean the crowns", "inspect every season"]),
        (31, "safety", "Never under the load", "Sixty-six kilograms at nearly forty kilometres an hour.",
         f"And the rule that matters most. Nobody stands under a triangle on its way up. Dropped from the top "
         f"of the hoist, {sf['drop_m']:.1f} metres, a {ho['heaviest_kg']:.0f} kilogram triangle lands at "
         f"{sf['impact_kmh']:.0f} kilometres an hour, with {sf['energy_kj']:.1f} kilojoules. Mark a ring under "
         f"the hook and keep it empty. Wear a helmet. Climb on a proper climbing system, tied in twice, or hire "
         f"an arborist for the ties. The web is only as safe as the worst knot in it.",
         [f"v = sqrt(2 g h) = {sf['impact_m_s']:.1f} m/s = {sf['impact_kmh']:.0f} km/h",
          f"E = m v^2 / 2 = {sf['energy_kj']:.2f} kJ"]),
        (32, "close", "The ground can wait", "Built with the trees.",
         f"Two ropes for the X, {mat['spiral_m']:.0f} metres of spiral, four guys to four more trees, "
         f"{mat['pigtails_m']:.0f} metres of pigtails, one battery winch and, one day, a bigger one at the "
         f"top. Forty triangles hung, joined and lifted without a scaffold, a crane or a foundation, by a "
         f"network of living trees that were already doing the job. The ground can wait. Maybe it can wait "
         f"for good.",
         [f"X {mat['x_m']:.1f} m, spiral {mat['spiral_m']:.0f} m", f"guys {mat['guys_m']:.0f} m, "
          f"pigtails {mat['pigtails_m']:.0f} m"]),
    ]
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()


# ----------------------------------------------------------------------
# Selftest
# ----------------------------------------------------------------------

def validate_sky_web_film() -> None:
    ss.validate_sky_web_scene()
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
            assert not anchor_blocked(eye, target), (ch.slug, p, "an anchor tree is in the way")

    class App:
        def __init__(self):
            self.world_labels = []
            self.built: set = set()

        def static_layer(self, key, builder, subject_points=None):
            if key in self.built:
                return
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key
            assert len(batch.vertices) > 0, (key, "a cached layer came back empty")
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
    R, centre, active = raise_pose(1.0)
    assert active is None and np.allclose(R, np.eye(3)) and abs(centre[2] - (ss.BASE + ss.lift_z(2))) < 1e-6
    # The claims the narration makes, held against the facts.
    by = {c.slug: c.narration[0] for c in CHAPTERS}
    w8, one, lv, ap = F["weights"], F["one"], F["level"], F["apex"]
    assert "hand winch" in by["corrections"] and "twelve" in by["corrections"]
    assert 2 < w8["ratio_lo"] < w8["ratio_hi"] < 3.1 and "two to three" in __doc__
    assert F["spread_taut"]["tension_kn"] > 1.8 * F["spread"]["tension_kn"] and "doubles" in by["xrope"]
    assert F["tree1"]["factor"] < C["tree_factor"] and F["tree1_taut"]["factor"] < 1 and "past breaking" in by["guys"]
    assert F["post"]["times"] > 10 and "stiffer" in by["treepost"]
    assert F["hoist"]["battery_share"] < 0.25 and "a fifth of one battery" in CHAPTERS[8].promise
    assert F["hoist"]["lift_min"] < 2 and "Under two minutes" in CHAPTERS[10].promise
    assert one["now_x"] < 0.3 and "a quarter" in CHAPTERS[19].promise
    assert 0.95 < one["lo_x"] < 1.2 and "almost nothing to spare" in by["onepoint"]
    assert 1.8 < one["hi_x"] < 2.2 and "twice over" in by["onepoint"]
    assert one["block_kn"] > one["w_kn"]
    assert lv["even_deg"] < 0.05 < lv["random_med_deg"] and "dead level" in by["level"]
    assert ap["strutted"] > 0 and ap["rim_hoop_kn"] > 0 and "lifts nothing where it lies" in by["apex"]
    assert F["skin"]["diy_usd"] < F["skin"]["sail_usd"] and "flammable" in by["skin"]
    assert F["wind"]["gust_deg"] < 10 and "barely swings" in CHAPTERS[23].promise
    assert 0.9 < F["tree2"]["factor"] < 1.2 and "edge of breaking" in by["higher"] and "experimental" in by["higher"] and "not set up" in by["higher"]
    assert not F["raise"]["winch_ok"] and F["raise"]["lo_ok"] and "more than today's winch" in by["corners"]
    assert F["floor"]["rope"] == "1 in"
    assert F["reach"]["short"] > 0 and "runs out" in by["order"]
    assert abs(F["hoist"]["heaviest_kg"] - 66) < 0.5 and "Sixty-six" in CHAPTERS[30].promise
    assert 35 <= F["safety"]["impact_kmh"] < 40 and "nearly forty kilometres" in CHAPTERS[30].promise
    SKY_WEB_LESSON.validate()


def report() -> str:
    return sw.constants_table()


SKY_WEB_LESSON = Lesson(
    key="cabin_sky_web", brand="DOMESIM", title="The Sky Web: Building a Dome in the Air",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_sky_web_film, report=report,
    snapshot_prefix="cabin_sky_web", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
