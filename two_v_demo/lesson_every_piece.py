"""Every Piece, Numbered: filling a triangle and framing the floor.

The Triangle Infill 3-D tool's work, filmed in the Cabin World (October 2026).
One of the dome's forty triangles is filled with wedges split from a log, each
piece numbered and its cuts shown on the mitre saw -- which face down, what
against the fence, the mitre and the bevel, and the offcut falling away. Then
the same triangle is filled nine other ways. Then the floor the dome stands
on: the owner's five 20 ft half trunks as a pentagon, a star across it,
joists between, every span and pier checked, seven ways to frame it compared,
and the materials swapped.

Nothing here is drawn for the film. The pieces are the tool's solids
(:mod:`two_v_demo.infill_scene`), the cuts are :mod:`infill.sawview`'s, and
every figure is :func:`infill.facts.facts` -- the same function the book's
chapter reads. The declared tables go on screen first; the patterns that fail
are shown failing.

    py -3.12 -m rerender stills cabin_every_piece
"""

from __future__ import annotations

import math

import numpy as np

from infill.facts import by, facts
from infill import methodology as method

from . import cabin_stage
from . import cabin_world as cw
from . import infill_scene as isc
from . import shots
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)

F = facts()
B = F["base"]
W = F["wedge"]
MF = method.reference()
PG = method.pentagon()
WEDGE = ("w8", "parallel", "flipflop", "fill")
PERMS = [(p["key"], p["arr"], p["lay_key"], p["mode"]) for p in F["perms"]]
PC = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
ST = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1] + 0.25, cabin_stage.HEIGHT + isc.SAW_TABLE_Z])
PATTERN_ORDER = [r["key"] for r in F["patterns"]]
MATERIAL_ORDER = ["half", "round", "quarter", "6x6", "4x4"]


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def ease(p: float) -> float:
    return shots.ease(p)


def pct(r: float) -> str:
    return f"{100 * r:.0f}"


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def _world(app, floor: bool = False, dome: bool = True) -> None:
    hide = ["builder"]
    if floor:
        hide.append("deck")
    if not dome:
        hide.append("dome")
    cw.paint(app, hide=tuple(hide), subject=False)
    app.static_layer("every:platform", cabin_stage.platform)


def _frame(app, index: int = 0, tilt: float = 0.0, raise_m: float = 0.0) -> None:
    xf = isc.panel_xf(index, tilt_deg=tilt, raise_m=raise_m)
    app.static_layer(f"every:frame:{index}:{tilt}:{raise_m}", lambda: isc.frame_batch(index, xf))


def _pieces(app, key, tilt: float = 0.0, raise_m: float = 0.0, highlight=None) -> None:
    xf = isc.panel_xf(0, tilt_deg=tilt, raise_m=raise_m)
    app.static_layer(f"every:pieces:{key}:{tilt}:{raise_m}:{highlight}",
                     lambda: isc.pieces_batch(*key, xf=xf, highlight=highlight))


def _base(app, pattern="star_joists", prim="half", support="piers", roles=("frame", "primary", "joist")):
    b = isc.base(pattern, prim, support)
    app.static_layer(f"every:base:{pattern}:{prim}:{support}:{','.join(roles)}",
                     lambda: isc.base_batch(b, roles))
    return b


def _ring(opaque, r_m: float, z: float, colour, segments: int = 72) -> None:
    pts = [np.array([r_m * math.cos(a), r_m * math.sin(a), z]) for a in np.linspace(0, math.tau, segments + 1)]
    for a, b in zip(pts, pts[1:]):
        opaque.cylinder(a, b, 0.025, colour, 6)


def _edge_mid(k: int) -> np.ndarray:
    a, b = isc.panel_corner(k), isc.panel_corner((k + 1) % 3)
    return (a + b) / 2 + [0, 0, 0.25]


def p_open(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _pieces(app, WEDGE)
    _label(app, PC + [0, 0, 0.75], "EVERY PIECE, NUMBERED", AMBER)


def p_declared(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _pieces(app, WEDGE)
    _label(app, PC + [0, 0, 0.7], f"{F['infill_constants']} + {B['declared']} DECLARED, A REASON EACH", WHITE)


def p_panel(app, opaque, transparent, p):
    _world(app)
    index = 0 if p < 0.55 else 1
    _frame(app, index)
    t = F["types"][index]
    xf = isc.panel_xf(index)
    for k in range(3):
        a, b = isc.panel_corner(k, xf, index), isc.panel_corner((k + 1) % 3, xf, index)
        _label(app, (a + b) / 2 + [0, 0, 0.3], f"{t['classes'][k]} {t['edges'][k]:.2f} in",
               AMBER if t["classes"][k] == "LONG" else BLUE)
    _label(app, PC + [0, 0, 0.9], f"x{t['count']}: {t['label'].upper()}", WHITE)


def p_tray(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _label(app, _edge_mid(0), "WALLS AT 45°", AMBER)
    _label(app, _edge_mid(1), f"{F['thickness_in']:.2f} in DEEP", BLUE)
    _label(app, PC + [0, 0, 0.8], "FOLDS " + " / ".join(f"{a:.2f}°" for a in F["folds"]), WHITE)


def p_fill(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    n = W["pieces"]
    u = min(1.0, p * 1.15) * n
    count = max(1, min(n, int(u) + 1))
    drop = u - int(u) if count <= n and u < n else 1.0
    b = isc.pieces_batch(*WEDGE, count=count, drop=min(1.0, drop * 1.6))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0, 0.8], f"{count} OF {n}", AMBER)
    _label(app, _edge_mid(0) + [0, 0, 0.2], f"{W['longest']:.1f} in DOWN TO {W['shortest']:.1f}", WHITE)


def p_numbered(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _pieces(app, WEDGE, highlight=W["piece"])
    xf = isc.panel_xf()
    for k in range(1, W["pieces"] + 1):
        # Flip-flopped neighbours overlap in plan: odd numbers left, even right.
        shift = np.asarray(xf.R @ np.array([-14.0 if k % 2 else 14.0, 0.0, 0.0]) * isc.IN)
        _label(app, isc.piece_centre(*WEDGE, k) + shift, str(k), AMBER if k == W["piece"] else WHITE)


def _saw(app, opaque, key, number, step, p, labels: bool = True):
    _world(app)
    sc = isc.cut_parts(*key, number, step)
    t = 0.05 + 0.9 * p
    b, mo = isc.saw_batch(sc, t)
    opaque.vertices.extend(b.vertices)
    if labels:
        xf = isc.saw_xf()
        _label(app, xf.point(mo["blade_centre"] + [0, 0, 7.5]),
               f"MITRE {abs(sc['mitre']):.1f}°, BEVEL {sc['bevel']:.0f}°", AMBER)
        _label(app, isc.saw_point(sc, "keeper", t), "KEEPER", WHITE)
        if sc["offcut"] is not None and t > 0.55:
            _label(app, isc.saw_point(sc, "offcut", t), "OFFCUT", AMBER)
        _label(app, xf.point([22.0, 3.0, 7.0]), "FENCE", BLUE)
    return sc, mo


def p_saw1(app, opaque, transparent, p):
    _saw(app, opaque, WEDGE, W["piece"], 1, p)


def p_saw2(app, opaque, transparent, p):
    sc, _mo = _saw(app, opaque, WEDGE, W["piece"], 2, p)
    if p > 0.6:
        _label(app, isc.saw_point(sc, "offcut", 0.05 + 0.9 * p, up=9.0), f"{W['cuts'][1]['off_long']:.1f} in: KEEP IT",
               GREEN)


def p_sheet(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _pieces(app, ("osb", "sheet", "", "cover"))
    bev = F["sheet"]["bevels"]
    for k, a in enumerate(bev):
        _label(app, _edge_mid(k) + [0, 0, 0.12], f"BEVEL {a:.1f}°", AMBER)
    _label(app, PC + [0, 0, 0.9], f"{F['sheet']['pieces']} HALVES, CUT BY HAND", WHITE)


def p_perms(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    k = min(len(PERMS) - 1, int(p * len(PERMS)))
    _pieces(app, PERMS[k])
    row = F["perms"][k]
    name = row["material"].upper() + ": " + row["arrangement"].upper()
    _label(app, PC + [0, 0, 0.95], f"{k + 1}/{len(PERMS)}  {name}", AMBER)
    _label(app, PC + [0, 0, 0.72], f"{row['pieces']} PIECES" + (" (COVER)" if row["mode"] == "cover" else ""), WHITE)


def p_rounds(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    L = isc.layout("rounds", "hex", "aligned", "fill")
    layers = sorted({q.group for q in L.pieces})
    k = min(len(layers), 1 + int(p * len(layers) * 1.05))
    show = set(layers[:k])

    def make(show=tuple(sorted(show))):
        b = TriangleBatch()
        xf = isc.panel_xf()
        for i, q in enumerate(L.pieces):
            if q.group in show:
                xf.emit(b, q.solid, isc.piece_colour(q), shade=1.0 if i % 2 == 0 else 0.93)
        return b
    app.static_layer(f"every:rounds:{k}", make)
    r = F["rounds"]
    _label(app, PC + [0, 0, 0.9], f"LAYER {k} OF {r['layers']}", AMBER)
    _label(app, PC + [0, 0, 0.68], f"WHOLE {r['kinds'].get('full', 0)}, AT THE WALL {r['kinds'].get('wall', 0)}, "
                                   f"GAPS {r['kinds'].get('copy', 0)}", WHITE)


def p_under(app, opaque, transparent, p):
    _world(app)
    tilt = 72.0 * ease(min(1.0, p * 1.6))
    _frame(app, 0, round(tilt, 1), 0.05)
    _pieces(app, WEDGE, round(tilt, 1), 0.05)
    _label(app, PC + [0, -0.3, 2.3], "FROM UNDERNEATH: EVERY OTHER POINT DOWN", AMBER)


def _floor(app, dome: bool = False) -> None:
    _world(app, floor=True, dome=dome)


def p_frame5(app, opaque, transparent, p):
    _floor(app)
    b = _base(app, roles=("frame",))
    top = cw.landmarks().deck_centre[2]
    _ring(opaque, B["inner_r_ft"] * 0.3048, top + 0.02, (0.45, 0.85, 1.0, 1.0))
    if p > 0.45:
        _ring(opaque, B["dome_need_ft"] * 0.3048, top + 0.02, (1.0, 0.75, 0.3, 1.0))
    _label(app, isc.member_point(b, 1, 0.5, 14.0), f"{B['side_ft']:.0f} ft ALONG THE ROUND BACK", AMBER)
    _label(app, np.array([0.0, B["inner_r_ft"] * 0.3048, top + 0.4]), f"INSIDE r {B['inner_r_ft']:.2f} ft", BLUE)
    if p > 0.45:
        _label(app, np.array([0.0, 0.0, top + 0.5]), f"DOME NEEDS {B['dome_need_ft']:.2f} ft: "
                                                     f"{B['margin_ft']:.2f} ft SPARE", AMBER)


def p_corner(app, opaque, transparent, p):
    _floor(app)
    b = isc.base("star_joists")
    app.static_layer("every:frame-but-one", lambda: isc.base_batch(b, ("frame",), piers=True) if False else
                     _frame_except(b, 1))
    cut, info = isc.corner_cut(b, 1, p)
    opaque.vertices.extend(cut.vertices)
    end = isc.member_point(b, 1, 0.0, 16.0)
    _label(app, end, f"{B['corner_deg']:.0f}° OFF SQUARE, PLUMB", AMBER)
    _label(app, isc.member_point(b, 1, 0.45, 14.0), f"BACK {B['frame_back_in']:.2f} in, TOP {B['frame_top_in']:.2f} in",
           WHITE)


def _frame_except(b, skip: int) -> TriangleBatch:
    xf = isc.base_xf(b)
    out = TriangleBatch()
    for m in b.members:
        if m.role == "frame" and m.number != skip:
            xf.emit(out, m.solid, (0.42, 0.27, 0.16, 1.0))
    return out


def p_star(app, opaque, transparent, p):
    _floor(app)
    b = isc.base("star")
    _base(app, "star", roles=("frame",))
    prim = [m for m in b.members if m.role == "primary"]
    u = min(1.0, p * 1.3) * len(prim)
    count = max(1, min(len(prim), int(u) + 1))
    xf = isc.base_xf(b)
    for i, m in enumerate(prim[:count]):
        drop = (u - int(u)) if i == count - 1 and u < len(prim) else 1.0
        xf.emit(opaque, m.solid, (0.55, 0.38, 0.24, 1.0), (0.0, 0.0, 60.0 * (1 - min(1.0, drop * 1.6)) ** 2))
    _label(app, isc.member_point(b, prim[0].number, 0.5, 14.0),
           f"{B['star_members']} PIECES: {B['star_pieces'][1]:.1f} AND {B['star_pieces'][0]:.1f} in", AMBER)
    if p > 0.55:
        star = by(F["patterns"], "star")
        _label(app, np.array([0.0, 2.9, cw.landmarks().deck_centre[2] + 0.4]),
               f"DECK GAP {star['deck_gap_in']:.0f} in: TOO WIDE", RED)


def p_joists(app, opaque, transparent, p):
    _floor(app)
    b = isc.base("star_joists")
    _base(app, roles=("frame", "primary"))
    js = [m for m in b.members if m.role == "joist"]
    count = max(1, min(len(js), int(min(1.0, p * 1.25) * len(js)) + 1))
    xf = isc.base_xf(b)
    for i, m in enumerate(js[:count]):
        xf.emit(opaque, m.solid, (0.86, 0.72, 0.50, 1.0), shade=1.0 if i % 2 == 0 else 0.85)
    _label(app, isc.member_point(b, js[0].number, 0.5, 12.0), f"{count} OF {len(js)} JOISTS, "
                                                               f"{B['spacing_in']:.0f} in APART", AMBER)
    if p > 0.8:
        _label(app, np.array([0.0, 0.0, cw.landmarks().deck_centre[2] + 0.5]),
               f"DECK GAP {B['deck_gap_in']:.1f} in, INSIDE {B['deck_allow_in']:.0f}", GREEN)


def p_joist_saw(app, opaque, transparent, p):
    _world(app)
    b = isc.base("star_joists")
    joist = next(m for m in b.members if m.role == "joist")
    sc = isc.base_cut("star_joists", joist.number, "mitre")
    t = 0.05 + 0.9 * p
    bb, mo = isc.saw_batch(sc, t)
    opaque.vertices.extend(bb.vertices)
    xf = isc.saw_xf()
    _label(app, xf.point(mo["blade_centre"] + [0, 0, 7.5]),
           f"MITRE {abs(sc['mitre']):.0f}°, BEVEL {sc['bevel']:.0f}°", AMBER)
    _label(app, isc.saw_point(sc, "keeper", t), f"LAID FLAT: {B['joist_depth_in']:.2f} in ON EDGE IS TOO TALL", WHITE)
    _label(app, xf.point([22.0, 3.0, 7.0]), "FENCE", BLUE)


def p_loads(app, opaque, transparent, p):
    _floor(app)
    _base(app)
    _label(app, np.array([0.0, 0.0, cw.landmarks().deck_centre[2] + 0.6]),
            f"{B['total_lb']:,.0f} lb IN, {B['pier_sum_lb']:,.0f} lb TO THE PIERS", AMBER)


def p_piers(app, opaque, transparent, p):
    _floor(app)
    b = _base(app)
    heavy = max(b.piers, key=lambda q: q.load_lb)
    xf = isc.base_xf(b)
    top = xf.point([heavy.xy[0], heavy.xy[1], heavy.top])
    pad = isc.IN * B["pad_max_in"]
    opaque.box(np.array([top[0], top[1], 0.02]), np.array([pad, pad, 0.04]), (0.7, 0.68, 0.62, 1.0))
    _label(app, top + [0, 0, 0.9], f"{B['pier_max_lb']:,.0f} lb: {B['pad_max_in']:.0f} in PAD", AMBER)
    _label(app, np.array([0.0, -3.4, 1.1]), f"{B['piers']} PIERS, {B['extra_piers']} ADDED MID-SPAN", WHITE)


def p_patterns(app, opaque, transparent, p):
    _floor(app)
    k = min(len(PATTERN_ORDER) - 1, int(p * len(PATTERN_ORDER)))
    key = PATTERN_ORDER[k]
    _base(app, key)
    row = by(F["patterns"], key)
    z = cw.landmarks().deck_centre[2]
    _label(app, np.array([0.0, 0.0, z + 0.9]), f"{k + 1}/{len(PATTERN_ORDER)}  {row['name'].upper()}", AMBER)
    _label(app, np.array([0.0, 0.0, z + 0.55]),
           f"{row['members']} PIECES, {row['piers']} PIERS, WORST SPAN {pct(row['worst'])}%",
           GREEN if row["deck_ok"] else RED)
    if not row["deck_ok"]:
        _label(app, np.array([0.0, 2.9, z + 0.4]), f"DECK GAP {row['deck_gap_in']:.0f} in: FAILS", RED)


def p_extremes(app, opaque, transparent, p):
    _floor(app)
    key = "beams" if p < 0.45 else "fan"
    b = _base(app, key)
    row = by(F["patterns"], key)
    z = cw.landmarks().deck_centre[2]
    if key == "beams":
        _label(app, np.array([0.0, 0.0, z + 0.7]), f"BEAMS: HARDEST SPAN AT {pct(row['worst'])}%", GREEN)
    else:
        heavy = max(b.piers, key=lambda q: q.load_lb)
        top = isc.base_xf(b).point([heavy.xy[0], heavy.xy[1], heavy.top])
        _label(app, top + [0, 0, 1.0], f"FAN CENTRE PIER {row['pier_max_lb']:,.0f} lb, "
                                       f"{row['pad_max_in']:.0f} in PAD", RED)


def p_gravel(app, opaque, transparent, p):
    _floor(app)
    b = _base(app, "rings", support="gravel")
    row = by(F["gravel"], "rings")
    z = 0.4
    _label(app, np.array([0.0, 0.0, z + 0.6]), f"{B['rings']} RINGS ON GRAVEL, NO PIERS", AMBER)
    _label(app, np.array([0.0, -3.2, z + 0.3]), f"${row['usd']:,.0f} BOUGHT, {row['logs']} LOGS", WHITE)
    del b


def p_materials(app, opaque, transparent, p):
    _floor(app)
    k = min(len(MATERIAL_ORDER) - 1, int(p * len(MATERIAL_ORDER)))
    mat = MATERIAL_ORDER[k]
    _base(app, "star_joists", prim=mat)
    row = next(r for r in F["materials"] if r["prim"] == mat)
    z = cw.landmarks().deck_centre[2]
    _label(app, np.array([0.0, 0.0, z + 0.9]), f"STAR OF {row['material'].split(' (')[0].upper()}", AMBER)
    _label(app, np.array([0.0, 0.0, z + 0.55]), f"{row['piers']} PIERS, {row['logs']} LOGS, ${row['usd']:,.0f}", WHITE)


def p_dome(app, opaque, transparent, p):
    _floor(app, dome=True)
    _base(app)
    z = cw.landmarks().apex[2]
    _label(app, np.array([0.0, 0.0, z + 0.6]), f"IT FITS: {B['margin_ft']:.2f} ft TO SPARE", GREEN)


def p_honest(app, opaque, transparent, p):
    _floor(app, dome=True)
    _base(app)
    z = cw.landmarks().apex[2]
    _label(app, np.array([0.0, 0.0, z + 0.6]), f"WOOD {B['fb_psi']:.0f} psi: A GUESS, NOT A GRADE", RED)


def p_method_inputs(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _label(app, PC + [0, 0, 0.85], "PLANNING ASSUMPTIONS, NOT A CUT LIST", AMBER)


def p_frame_footage(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _label(app, PC + [0, 0, 0.85], "CHORDS / ACTUAL CUTS / UNCUT BLANKS", AMBER)


def p_pair_budget(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _pieces(app, WEDGE)
    _label(app, PC + [0, 0, 0.85], "SOLVED FLIP-FLOP EXAMPLE; TEST INWARD-POINT PAIRS SEPARATELY", AMBER)


def p_tree_budget(app, opaque, transparent, p):
    _world(app)
    _frame(app)
    _label(app, PC + [0, 0, 0.85], "TREE EQUIVALENTS ASSUME UNIFORM USABLE TRUNK", AMBER)


def p_pentagon_math(app, opaque, transparent, p):
    _floor(app)
    _base(app, "star", roles=("frame", "primary"))
    _label(app, cw.landmarks().deck_centre + [0, 0, 0.7], "IDEAL PLAN LENGTHS; REAL CUTS STOP AT FACES", AMBER)


def p_close(app, opaque, transparent, p):
    _floor(app, dome=True)
    _base(app)
    _frame(app)
    _pieces(app, WEDGE)
    _label(app, PC + [0, 0, 0.8], "TRIANGLE INFILL, IN THE LAUNCHER", AMBER)


SCENES = {
    "open": p_open, "declared": p_declared, "panel": p_panel, "tray": p_tray, "fill": p_fill,
    "numbered": p_numbered, "saw1": p_saw1, "saw2": p_saw2, "sheet": p_sheet, "perms": p_perms,
    "rounds": p_rounds, "under": p_under, "frame5": p_frame5, "corner": p_corner, "star": p_star,
    "joists": p_joists, "joist_saw": p_joist_saw, "loads": p_loads, "piers": p_piers, "patterns": p_patterns,
    "extremes": p_extremes, "gravel": p_gravel, "materials": p_materials, "dome": p_dome, "honest": p_honest,
    "close": p_close,
    "method_inputs": p_method_inputs, "frame_footage": p_frame_footage,
    "pair_budget": p_pair_budget, "tree_budget": p_tree_budget,
    "pentagon_math": p_pentagon_math,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

MATH = ("declared", "loads", "method_inputs", "frame_footage", "pair_budget", "tree_budget", "pentagon_math")


def beside_worksheet(shot, portion: float = 0.40):
    """Slide the camera right so the subject sits left of a math chapter's worksheet."""
    def moved(p: float):
        eye, target, fov = shot(p)
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        f = target - eye
        d = np.linalg.norm(f)
        f /= d
        right = np.cross(f, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        k = portion * d * math.tan(math.radians(fov) / 2) * 16 / 9
        return eye + right * k, target + right * k, fov
    return moved


def _moves() -> dict:
    m = cw.landmarks()
    deck = m.deck_centre
    floor = np.array([0.0, 0.0, deck[2]])
    panel = PC + [0.0, 0.0, 0.05]
    saw = ST + [0.0, 0.0, 0.05]
    b = isc.base("star_joists")
    corner = isc.member_point(b, 1, 0.0, 0.0)
    out_dir = np.array([corner[0], corner[1], 0.0]) / max(1e-6, math.hypot(corner[0], corner[1]))
    hero = np.array(cw.HERO_EYE)
    table = {
        "open": shots.crane_reveal(panel, panel + [1.6, 2.6, 0.9], panel + [2.4, 6.5, 4.6], 44, 52),
        "declared": shots.orbit(panel, 4.2, 2.4, 70, 20, 46),
        "panel": shots.orbit(panel, 3.3, 3.0, 75, 25, 44),
        "tray": shots.push_in(panel, panel + [2.2, 3.0, 1.9], panel + [1.7, 2.4, 1.5], 46, 42),
        "fill": shots.orbit(panel, 2.4, 3.4, 65, 35, 44),
        "numbered": shots.orbit(panel, 2.9, 3.1, 95, -20, 44),
        "saw1": shots.orbit(saw, 1.9, 0.95, 60, 30, 44),
        "saw2": shots.orbit(saw, 1.9, 0.95, 120, -30, 44),
        "sheet": shots.orbit(panel, 3.3, 2.0, 50, 30, 44),
        "perms": shots.orbit(panel, 3.6, 2.8, 70, 40, 44),
        "rounds": shots.push_in(panel, panel + [1.5, 2.8, 2.2], panel + [0.9, 2.0, 1.6], 46, 42),
        "under": shots.orbit(panel + [0, -0.2, 0.9], 3.4, 0.6, 80, 20, 46),
        "frame5": shots.orbit(floor, 12.0, 6.5, -70, 30, 50),
        "corner": shots.push_in(corner + [0, 0, 0.3], corner + out_dir * 4.0 + [1.2, 0.0, 2.4],
                                corner + out_dir * 2.4 + [0.8, 0.0, 1.5], 50, 44),
        "star": shots.orbit(floor, 12.0, 7.5, -80, 30, 50),
        "joists": shots.orbit(floor, 11.0, 7.0, -110, 40, 50),
        "joist_saw": shots.orbit(saw, 2.4, 1.2, 70, 30, 46),
        "loads": shots.orbit(floor, 13.0, 6.0, -95, 20, 50),
        "piers": shots.orbit(floor, 9.0, 3.2, -55, 30, 52),
        "patterns": shots.orbit(floor, 12.5, 8.0, -90, 50, 50),
        "extremes": shots.orbit(floor, 11.5, 6.5, -60, 30, 50),
        "gravel": shots.orbit(np.array([0.0, 0.0, 0.3]), 10.0, 6.0, -100, 40, 50),
        "materials": shots.orbit(floor, 12.0, 6.0, -120, 50, 50),
        "dome": shots.crane_reveal(m.dome_centre + [0, 0, 1.2], hero + [0.5, 3.5, -2.0], hero + [0.8, -1.5, 2.5],
                                   44, 52, look_start=floor),
        "honest": shots.orbit(m.dome_centre + [0, 0, 1.4], 11.5, 3.0, -100, 25, 52),
        "close": shots.crane_reveal(m.dome_centre + [0, 0, 1.0], hero + [0.4, 3.0, 0.0], hero + [1.2, -2.5, 4.0],
                                    46, 54, look_start=floor),
    }
    for key in ("method_inputs", "frame_footage", "pair_budget", "tree_budget"):
        table[key] = shots.orbit(panel, 3.8, 2.8, 75, 20, 46)
    table["pentagon_math"] = shots.orbit(floor, 1.0, 18.0, -90, 8, 50)
    out = {}
    for slug, shot in table.items():
        if slug in MATH:
            shot = beside_worksheet(shot, 0.30 if slug == "pentagon_math" else 0.40)
        out[slug] = cabin_stage.clear_view(shot, cabin_stage.safe)
    return out


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=(),
        overlay: str | None = None) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, overlay)


def _declared_steps() -> list[str]:
    k = B["declared_kinds"]
    return [
        "SOLVED, from the strut length and the log:",
        f"   dome {F['dome_diameter_ft']:.2f} ft across from a {F['strut_in']:.0f} in strut",
        "   two triangle shapes; every piece from its triangle and log",
        f"DECLARED for the triangles: {F['infill_constants']} figures",
        "   saw kerfs, sheet and board sizes, densities, prices",
        f"DECLARED for the floor: {B['declared']} figures",
        f"   {k['standard']} standards, {k['estimate']} estimates, {k['assumption']} assumptions, "
        f"{k['nominal']} catalogue sizes",
        f"   floor load {B['live_psf']:.0f} + {B['dead_psf']:.0f} lb/ft2; wood {B['fb_psi']:.0f} psi (a guess)",
        f"   soil {B['soil_psf']:,.0f} lb/ft2 under every pier pad",
    ]


def _chapters() -> tuple[Chapter, ...]:
    t0, t1 = F["types"]
    c1, c2 = W["cuts"][0], W["cuts"][1]
    cn = W["corners"]
    sh = F["sheet"]["bevels"]
    pr = {i: p["pieces"] for i, p in enumerate(F["perms"])}
    rd = F["rounds"]
    star = by(F["patterns"], "star")
    beams, fan, wheel = by(F["patterns"], "beams"), by(F["patterns"], "fan"), by(F["patterns"], "wheel")
    rings = by(F["patterns"], "rings")
    g_rings, g_sj = by(F["gravel"], "rings"), by(F["gravel"], "star_joists")
    mats = {r["prim"]: r for r in F["materials"]}
    jo = B["joist"]
    trim = (B["frame_back_in"] - B["frame_top_in"]) / 2
    rows = [
        (1, "open", "Every piece, numbered", "A triangle and a floor, cut by the numbers.",
         "Two things are built from wood in this film. One of the dome's forty triangles, filled with wedges "
         "split from a log. And the floor the whole dome stands on, framed from five twenty-foot half trunks. "
         "Every piece of both has a number. Every number has a length, an angle, and a way of cutting it, worked "
         "out by one calculator and shown on the saw before anyone picks up a blade.",
         [f"{len(F['types'])} triangle shapes, 40 panels",
          f"floor: {B['members']} members, {B['piers']} piers"]),
        (2, "declared", "What is solved, what is assumed", "Two tables before any number.",
         f"First, what this rests on. The shapes are solved: the dome from its {F['strut_in']:.0f} inch strut, "
         f"the triangles from the dome, every piece from its triangle and the log it is split from. What cannot "
         f"be solved is written down, each line with its reason. {F['infill_constants']} figures for the "
         f"triangles: saw kerfs, the sizes things are sold in, prices. And {B['declared']} for the floor, from "
         f"the forty pounds a square foot a floor must carry, to how strong ungraded wood is taken to be. Change "
         f"any line, and every number after it changes.",
         _declared_steps(), "math"),
        (3, "panel", "Two triangles, forty panels", "Only two shapes.",
         f"A dome whose longest stick is {F['strut_in']:.0f} inches is {F['dome_diameter_ft']:.1f} feet across, "
         f"and its forty triangles come in only two shapes. {t0['count']} have a long base of "
         f"{t0['edges'][0]:.1f} inches and two short sides of {t0['edges'][1]:.1f}. {t1['count']} have three "
         f"long sides. Fill one of each well, and you have filled them all.",
         [f"{t0['count']} x long {t0['edges'][0]:.2f} + short {t0['edges'][1]:.2f} x 2",
          f"{t1['count']} x long {t1['edges'][0]:.2f} x 3"]),
        (4, "tray", "The frame is a tray", "Forty-five degree walls.",
         f"Each frame member is a wedge, an eighth of a {F['frame_log_in']:.0f} inch log, lying on one sawn face "
         f"with its point toward the opening. Its other sawn face rises at forty-five degrees, so the opening is "
         f"a tray, narrow at the flat side and widening up the slope, {F['thickness_in']:.2f} inches deep. "
         f"Every piece that fills it rests on that slope. Next door, the panels fold away at "
         f"{F['folds'][0]:.1f} and {F['folds'][1]:.1f} degrees, and a covering has to meet those too.",
         ["walls: 45 deg (an eighth of a log)", f"depth {F['thickness_in']:.2f} in",
          "folds " + ", ".join(f"{a:.3f}" for a in F["folds"]) + " deg"]),
        (5, "fill", "Seventeen wedges" if W["pieces"] == 17 else f"{W['pieces']} wedges",
         "Stripes, flip-flopped.",
         f"Fill it with wedges split from a {F['infill_log_in']:.0f} inch log, in stripes along the long base, "
         f"flip-flopped: one point up, the next point down, so they nest. It takes {W['pieces']}, from "
         f"{W['longest']:.1f} inches long down to {W['shortest']:.1f}. Each one ends where it meets a forty-five "
         f"degree wall, so every end is a compound cut, and no two pieces are the same length.",
         [f"{W['pieces']} pieces", f"longest {W['longest']:.2f} in, shortest {W['shortest']:.2f} in"]),
        (6, "numbered", "A number on every piece", "Chalked on as it is cut.",
         f"Every piece gets a number, chalked on as it is cut, and the number carries everything: which stick it "
         f"comes from, its length along each edge, and both end cuts. Take piece {W['piece']}. Along its point it "
         f"runs {cn[0]:.2f} inches. Its other two long corners run {cn[1]:.2f} and {cn[2]:.2f}. Three lengths, "
         f"because its ends lean.",
         [f"piece {W['piece']}: " + " / ".join(f"{v:.2f}" for v in cn) + " in"]),
        (7, "saw1", "Cut one, on the mitre saw", "Sawn face down, bark corner to the fence.",
         f"Here is its first cut. The stick lies on its sawn face, the bark corner against the fence, the keeper "
         f"to the {'right' if c1['keeper_right'] else 'left'} of the blade. Swing the mitre {c1['mitre']:.1f} "
         f"degrees, tilt the blade {c1['bevel']:.0f}, and take just enough to clear the raw end. What falls away "
         f"is a tapered sliver, {c1['off_long']:.2f} inches at its longest and {c1['off_short']:.2f} at its "
         f"shortest. The calculator found that setting by trying every face down, both ends toward the fence, "
         f"and keeping the one a single-bevel saw can make.",
         [f"mitre {c1['mitre']:.1f} deg, bevel {c1['bevel']:.1f} deg (blade tilted left)",
          f"offcut {c1['off_long']:.2f} to {c1['off_short']:.2f} in"]),
        (8, "saw2", "Cut two, and an offcut to keep", "Measure from the first cut.",
         f"Then end for end, the point against the fence, and measure from the first cut: {cn[0]:.2f} inches "
         f"along the point, and the other two corners. Join the marks and the blade follows the line, at the same "
         f"{c2['mitre']:.1f} and {c2['bevel']:.0f}. This offcut is {c2['off_long']:.2f} inches long. That is a "
         f"piece in its own right, so it goes back on the pile for a shorter run.",
         [f"offcut {c2['off_long']:.2f} to {c2['off_short']:.2f} in: kept"]),
        (9, "sheet", "Too steep for the saw", "A sheet's edges, bevelled by hand.",
         f"Not every cut fits a mitre saw. Cover the panel instead, with a sheet of strand board cut in "
         f"{F['sheet']['pieces']} halves, and each edge has to lean to meet the next panel's covering, half the "
         f"fold at its seam: {sh[0]:.1f}, {sh[1]:.1f} and {sh[2]:.1f} degrees. Those cuts run the length of a "
         f"sheet, so they are snapped with a chalk line and made with a circular saw, its blade tilted.",
         ["bevel = fold / 2: " + ", ".join(f"{a:.2f}" for a in sh) + " deg"]),
        (10, "perms", "Ten ways to fill one triangle", "Every one with its cut list.",
         f"The same triangle, ten ways. Wedges in stripes, {pr[0]} pieces. Wedges in a chevron, {pr[1]}. "
         f"Sixteenth slices, points alternating, {pr[2]}. Wedges in rings, {pr[3]}. Milled boards, {pr[4]}. "
         f"Fence pickets as vent louvers, {pr[5]}. Log rounds, {pr[6]}. Or covered over: a sheet in {pr[7]} "
         f"halves, {pr[8]} strips of metal, {pr[9]} piece of film. Every one comes with its cut list, and the "
         f"calculator will put any of them on the saw.",
         [f"{p['material']}, {p['arrangement'].lower()}: {p['pieces']}" for p in F["perms"][:5]]),
        (11, "rounds", "Rounds, and the gaps cut to fit", "Copy a round over the gap, trace, cut.",
         f"Log rounds are the odd one out: slices across a whole trunk, {rd['thick_in']:.1f} inches thick, in a "
         f"honeycomb {rd['layers']} layers deep. {rd['kinds'].get('full', 0)} go in whole, "
         f"{rd['kinds'].get('wall', 0)} are cut where they meet the wall, and the {rd['kinds'].get('copy', 0)} "
         f"gaps left over are filled the way a carpenter would: lay another round over the gap, trace the gap "
         f"onto it from below, and cut to the line. {rd['pieces']} pieces in all.",
         [f"{rd['layers']} layers x {rd['thick_in']:.1f} in", f"whole {rd['kinds'].get('full', 0)}, wall "
          f"{rd['kinds'].get('wall', 0)}, gap pieces {rd['kinds'].get('copy', 0)}"]),
        (12, "under", "Turn it over", "The inside face.",
         "Turn the panel over and look at it from the inside, the face the room will see. The flip-flop shows: "
         "every other wedge has its point down, and the frame's points run round the edge. The calculator shows "
         "every pattern from underneath too, so you can see how the pieces meet before cutting any of them.",
         ["flat side: points of the frame and of every other wedge"]),
        (13, "frame5", "Five trunks, one pentagon", "Round back out, flat face in.",
         f"Now the floor. The dome stands on a platform, and the owner already has its edge: five half trunks, "
         f"twenty feet long. Stood on edge, round back out, flat face in, and joined at the corners, they make a "
         f"pentagon whose backs measure the full {B['side_ft']:.0f} feet. The biggest circle inside the flat faces "
         f"is {B['inner_r_ft']:.2f} feet in radius. The dome needs {B['dome_need_ft']:.2f}: its sphere, plus "
         f"{B['overhang_in']:.0f} inches for its frame at the foot. It fits, with {B['margin_ft']:.2f} feet to "
         f"spare.",
         [f"apothem = s / (2 tan 36) = {B['apothem_ft']:.3f} ft", f"less the half trunk: {B['inner_r_ft']:.3f} ft",
          f"dome {F['dome_radius_in'] / 12:.3f} ft + {B['overhang_in']:.0f} in = {B['dome_need_ft']:.3f} ft"]),
        (14, "corner", "Every corner, one cut", "Thirty-six degrees, plumb, by chainsaw.",
         f"Each corner is a mitre, and every one is the same: {B['corner_deg']:.0f} degrees off square. Along the "
         f"round back a trunk is the full {B['frame_back_in'] / 12:.0f} feet. Along its top, where the flat face "
         f"starts, the cuts take {trim:.2f} inches off each end, so it is {B['frame_top_in']:.2f} inches. No mitre "
         f"saw takes a log that size: mark the line across the top, plumb it down both sides with a level, and "
         f"cut to it with the chainsaw.",
         [f"back {B['frame_back_in']:.2f} in, top {B['frame_top_in']:.2f} in",
          f"each end: r tan 36 = {trim:.2f} in"]),
        (15, "star", "A star across it", "Strong, and not enough.",
         f"Inside goes a five-point star, corner to corner, in half trunks again. Each line crosses two others, so "
         f"each is cut in three: {B['star_members']} pieces of {B['star_pieces'][1]:.1f} and "
         f"{B['star_pieces'][0]:.1f} inches, mitred where they meet. A star braces a pentagon across every "
         f"corner. But on its own it leaves the floor in big triangles. The widest gap a deck board would have to "
         f"cross is {star['deck_gap_in']:.0f} inches, and a two by six deck may cross {B['deck_allow_in']:.0f}. "
         f"The star alone fails.",
         [f"diagonal = {PG['phi']:.6f} x side, cut in three", f"deck gap {star['deck_gap_in']:.1f} in > "
          f"{B['deck_allow_in']:.0f} in allowed"]),
        (16, "joists", "Joists between the points", "Every gap inside a deck board's reach.",
         f"So every space between the points is filled with joists, {B['joist_name']}, {B['spacing_in']:.0f} "
         f"inches apart, each cut to meet the star or the frame where it lands. {B['roles']['joist']} of them. "
         f"Now the widest gap is {B['deck_gap_in']:.1f} inches, inside the {B['deck_allow_in']:.0f} a deck board "
         f"may cross.",
         [f"{B['roles']['joist']} joists at {B['spacing_in']:.0f} in", f"deck gap {B['deck_gap_in']:.2f} in"]),
        (17, "joist_saw", "A joist on the saw", "Too tall on edge, so it lies flat.",
         f"A joist meets a star line at an angle, so its end is cut off square. Stood on edge, a two by eight is "
         f"{B['joist_depth_in']:.2f} inches tall, beyond the saw's {B['saw_height_in']:.0f} inch reach. So it lies "
         f"flat, and the angle moves from the mitre to the bevel: mitre zero, bevel {jo['bevel']:.0f} degrees. Its "
         f"other end, {jo['end1']}, is past the blade's {B['bevel_max']:.0f} degree tilt, and is marked and cut "
         f"by hand.",
         [f"on edge {B['joist_depth_in']:.2f} in > {B['saw_height_in']:.0f} in", f"flat: bevel {jo['bevel']:.1f} deg"]),
        (18, "loads", "Where the weight goes", "Every pound, to a pier.",
         f"Every square foot of floor has to go somewhere. Forty pounds for living, ten for the floor itself, "
         f"over {B['area_ft2']:.0f} square feet: {B['total_lb']:,.0f} pounds. Each patch goes to the member "
         f"nearest it. Joists hand theirs to what they hang on; the star and the frame hand everything to the "
         f"piers; and the piers carry {B['pier_sum_lb']:,.0f} pounds, every pound accounted for. Every span is "
         f"checked for bending and for sag. Where one fails, a pier goes under it: {B['extra_piers']} of them, and "
         f"now the hardest span works at {pct(B['worst'])} percent of what it can carry.",
         [f"W = ({B['live_psf']:.0f} + {B['dead_psf']:.0f}) x {B['area_ft2']:.0f} = {B['total_lb']:,.0f} lb",
          "bending: w L^2 / 8 <= Fb S", f"Fb = {B['fb_psi']:.0f} psi (declared)",
          "sag: 5 w L^4 / 384 E I <= L / 360",
          f"piers carry {B['pier_sum_lb']:,.0f} lb; hardest span {pct(B['worst'])}%"], "math"),
        (19, "piers", f"{B['piers']} piers, each sized", "A pad for every load.",
         f"{B['piers']} stump piers, rounds of log on tamped gravel. Each pad is sized from its own load, at "
         f"{B['soil_psf']:,.0f} pounds a square foot of soil. Most need only the smallest pad, "
         f"{B['pad_min_in']:.0f} inches square. The heaviest carries {B['pier_max_lb']:,.0f} pounds, and needs "
         f"{B['pad_max_in']:.0f}.",
         [f"pad = sqrt(load / {B['soil_psf']:,.0f}) ft", f"heaviest {B['pier_max_lb']:,.0f} lb -> "
          f"{B['pad_max_in']:.0f} in"]),
        (20, "patterns", "Seven ways to frame the floor", "Same trunks, same joists.",
         "The star is one way. The calculator builds seven, from the same trunks and joists, and checks each the "
         "same way. The star with joists. The star alone, which fails its deck. A wheel, five spokes with rings "
         "of joists. A sunburst of ten. A fan, its joists square to the walls. Beams across with joists between, "
         "the way a deck is usually framed. And nested rings, the idea this began with.",
         [f"{r['name']}: {r['members']} pieces, {r['piers']} piers" for r in F["patterns"]]),
        (21, "extremes", "The most to spare, the heaviest pier", "Spokes bring their load to one point.",
         f"They do not pass equally. Beams with joists works its hardest span at only {pct(beams['worst'])} "
         f"percent. Only the nested rings have more to spare, {pct(rings['worst'])} percent, and they take "
         f"{rings['piers']} piers to get it. The fan is the other end: five spokes meet at one centre pier, and "
         f"that pier carries {fan['pier_max_lb']:,.0f} pounds, on a pad {fan['pad_max_in']:.0f} inches square. "
         f"The wheel's carries {wheel['pier_max_lb']:,.0f}. Bring the spokes to one point, and you bring the load "
         f"there too.",
         [f"beams: hardest span {pct(beams['worst'])}%", f"fan centre {fan['pier_max_lb']:,.0f} lb",
          f"wheel centre {wheel['pier_max_lb']:,.0f} lb"]),
        (22, "gravel", "Or lay it on gravel", "Where the nested rings belong.",
         f"On a levelled gravel bed nothing spans. Every member bears along its length, and the piers go away. "
         f"That is where the nested rings belong: {B['rings']} rings, each one's back pressed against the flat "
         f"face of the ring outside it, every corner the same {B['corner_deg']:.0f} degree cut, the gaps packed "
         f"with gravel or cob. About {g_rings['usd']:,.0f} dollars of gravel, and nothing else to buy. But it "
         f"eats logs: {g_rings['logs']} of them, against {g_sj['logs']} for the star with joists.",
         [f"rings: {B['rings']}, logs {g_rings['logs']}, ${g_rings['usd']:,.0f}",
          f"star + joists on gravel: logs {g_sj['logs']}, ${g_sj['usd']:,.0f}"]),
        (23, "materials", "Trunks, quarters or lumber", "Swap what the star is made of.",
         f"Swap what the star is made of, and the floor changes round it. Half trunks: {mats['half']['piers']} "
         f"piers and {mats['half']['logs']} logs. Whole logs: the same piers, but {mats['round']['logs']} logs. "
         f"Quarter trunks, weaker: {mats['quarter']['piers']} piers. Six by sixes: {mats['6x6']['piers']} piers, "
         f"and about {mats['6x6']['usd']:,.0f} dollars, because they are bought. Four by fours: "
         f"{mats['4x4']['piers']} piers, {mats['4x4']['extra']} of them propping spans a four by four cannot "
         f"carry.",
         [f"{r['material'].split(' (')[0]}: {r['piers']} piers, {r['logs']} logs, ${r['usd']:,.0f}"
          for r in F["materials"]]),
        (24, "dome", "The dome on its floor", "Five corners left over.",
         f"And the dome goes on it, its foot inside the flat faces, {B['margin_ft']:.2f} feet to spare at the "
         f"narrowest, with the pentagon's five corners left over outside it.",
         [f"{B['inner_r_ft']:.2f} - {B['dome_need_ft']:.2f} = {B['margin_ft']:.2f} ft"]),
        (25, "honest", "What these numbers are not", "Checked and priced, not rated.",
         f"A word about these numbers. The floor loads are a dwelling's. But the wood's strength, "
         f"{B['fb_psi']:.0f} pounds per square inch, is a guess: these logs are not graded, and the guess is a "
         f"careful one, stricter than a lumber span table. The prices are estimates. Change any of it in the "
         f"calculator and every pier and span is worked again. Before people live on it, an engineer signs it. "
         f"Here it is checked and priced, not rated.",
         [f"Fb {B['fb_psi']:.0f} psi: declared, not graded", "an engineer signs a floor people live on"]),
        (26, "close", "Cut by the numbers", "In the launcher: Triangle Infill.",
         f"{W['pieces']} wedges and their offcuts. Five trunks and a star. {B['members']} members and "
         f"{B['piers']} piers, every one numbered, every cut shown before it is made. The calculator that worked "
         f"all of this out is in the launcher, called Triangle Infill, and it will do the same for whatever is "
         f"stacked by your saw.",
         [f"triangle: {W['pieces']} pieces", f"floor: {B['members']} members, {B['piers']} piers"]),
    ]
    least, most = MF["rows"][0], MF["rows"][-1]
    rows[3:3] = [
        (0, "method_inputs", "The stock budget has assumptions", "State the example before using it.",
         f"Before estimating a wooden face, state the example. The planning reference takes the long chord as "
         f"{MF['long_in']:.0f} inches, not the finished stick. Its log is {MF['log_in']:.0f} inches across, split "
         f"{MF['splits']} ways, with {MF['trunk_ft']:.0f} feet of uniform usable trunk. The frame allowance is "
         f"one {MF['blank_in']:.0f} inch blank per member. For the opening estimate, we assume the frame occupies "
         "half the outer chord width inward from each edge. The actual tray opening is solved separately. "
         "Pair coverage, kerf, taper, defects and sealing still need a measured layout.",
         [f"nominal long chord {MF['long_in']:.0f} in; NOT the tool's maximum finished member",
          f"uniform log {MF['log_in']:.0f} in, {MF['splits']} splits, usable trunk {MF['trunk_ft']:.0f} ft",
          f"frame blank {MF['blank_in']:.0f} in; frame inset ASSUMED {MF['inset_in']:.3f} in",
          "pair pitch (2-p)w assumes continuous coverage; p is projected overlap",
          "kerf / taper / defects / end cuts / seals / packing loss NOT included"], "math"),
        (0, "frame_footage", "Three different timber totals", "A drawing, a cut, and the blank it came from.",
         f"Every panel owns its three members: {MF['members']} members for {MF['shared_edges']} shared geometric "
         f"edges. In the nominal-chord example their edge lengths total {MF['nominal_frame_ft']:.2f} feet. "
         f"The live solver's physical cut-stock total is {MF['finished_frame_ft']:.2f}, because the joints stop "
         f"at faces. But buying a blank for every member reserves {MF['gross_frame_ft']:.0f} feet of wedge stock. "
         "These are three different ledgers. A shorter finished member leaves an offcut; it does not make "
         "the original blank shorter. Reuse that offcut only when the cutting plan gives it a job.",
         [f"reference chords {MF['long_in']:.3f} / {MF['short_in']:.3f} in",
          f"panel-owned nominal edges = {MF['nominal_frame_ft']:.2f} wedge ft",
          f"solver cut-stock = {MF['finished_frame_ft']:.2f} wedge ft",
          f"{MF['members']} blanks x {MF['blank_in']/12:g} ft = {MF['gross_frame_ft']:.0f} wedge ft"], "math"),
        (0, "pair_budget", "Pair span is not face coverage", "An overlap range, with its condition attached.",
         f"The outer chord of an eighth of this log is {MF['chord_in']:.3f} inches. Under the stated "
         f"half-width inset, the clear area estimate is {MF['opening_sqft']:.2f} square feet. If a pair "
         "continuously covers two chord widths, it uses the least timber in this model. If two wedges cover "
         "only one width, the timber doubles. That is an assumed face-pitch range, not proof that sliding "
         "a bowtie closes the face. The alternating-point infill pictured here is solved by the tool. "
         "Two points both inward are another seating problem. An opposed-point section experiment has "
         "another orientation again. Sliding changes void and contact, not the wood already in the pair.",
         ["w = diameter x sin(pi / splits)", "assumed pair pitch = (2-p)w",
          "infill wedge ft = 2 x clear sq ft x 12 / continuous pair pitch",
          f"conditional range {least['infill_ft']:,.1f} to {most['infill_ft']:,.1f} wedge ft",
          "bowtie span / void fraction do NOT prove coverage, strength or R-value"], "math"),
        (0, "tree_budget", "Count raw trunk before finished timber", "Reserve the frame first, then add infill.",
         f"A uniform usable trunk of {MF['trunk_ft']:.0f} feet gives {MF['rounds_per_tree']} six-foot rounds "
         f"and {MF['wedges_per_tree']} wedges in the ideal model. Reserve {MF['frame_trunk_ft']:.0f} feet "
         "of raw trunk for the framing blanks, then add the infill wedge footage divided by the splits. "
         f"The conditional range is {least['raw_trunk_ft']:.1f} to {most['raw_trunk_ft']:.1f} feet of usable "
         f"trunk: {least['whole_tree_equivalents']} to {most['whole_tree_equivalents']} whole reference-tree "
         "equivalents. These are uniform-diameter equivalents, not guaranteed standing trees. A real pine "
         "tapers, cuts consume wood, and short triangle courses need a packing plan.",
         [f"ideal tree yield = {MF['trunk_ft']:.0f} x {MF['splits']} = {MF['tree_wedge_ft']:.0f} wedge ft",
          f"frame reserve = {MF['gross_frame_ft']:.0f} / {MF['splits']} = {MF['frame_trunk_ft']:.0f} trunk ft",
          f"frame + infill = {least['raw_trunk_ft']:.1f} to {most['raw_trunk_ft']:.1f} trunk ft",
          f"ceil(trunk / {MF['trunk_ft']:.0f}) = {least['whole_tree_equivalents']} to {most['whole_tree_equivalents']} equivalents"], "math"),
    ]
    idx = next(i for i, row in enumerate(rows) if row[1] == "star")
    rows[idx:idx] = [(0, "pentagon_math", "The star divides the stock", "Golden-ratio lengths, before the saw.",
        f"The floor's regular pentagon has a diagonal {PG['phi']:.6f} times its side. A diagonal crosses "
        "two others and splits into long, short and long. One long plus one short is exactly a perimeter "
        "side in the centreline drawing. That gives complementary stock, but not zero saw waste. The "
        "actual pieces stop at other members' faces and the saw consumes a kerf. Also distinguish the "
        f"corner's {PG['interior_deg']:.0f} degree included angle from a symmetrical "
        f"{PG['miter_deg']:.0f} degree mitre, a nominal {PG['butt_deg']:.0f} degree perimeter side-face butt, "
        f"and a {PG['diagonal_butt_deg']:.0f} degree diagonal-to-side butt. Those are plan angles for "
        "different joints, not bevel settings through a wedge.",
        [f"D = phi S = {PG['diagonal_in']:.2f} in",
         f"L = D-S = {PG['long_in']:.2f} in; C = D-2L = {PG['short_in']:.2f} in",
         f"L+C = {PG['side_in']:.2f} in; 2L+C = {PG['diagonal_in']:.2f} in",
         f"star {PG['long_count']} long + {PG['short_count']} short; perimeter {PG['perimeter_count']} sides",
         f"plan cuts: mitre {PG['miter_deg']:.0f}, side butt {PG['butt_deg']:.0f}, diagonal butt {PG['diagonal_butt_deg']:.0f} deg"], "math")]
    return tuple(_ch(i, *row[1:]) for i, row in enumerate(rows, 1))


CHAPTERS = _chapters()


# ----------------------------------------------------------------------
# Selftest
# ----------------------------------------------------------------------

def validate_every_piece_film() -> None:
    method.validate_methodology()
    isc.validate_infill_scene()
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
    # The claims the narration makes, held against the facts.
    by_slug = {c.slug: c.narration[0] for c in CHAPTERS}
    assert "not proof" in by_slug["pair_budget"] and "both inward" in by_slug["pair_budget"]
    assert "raw trunk" in by_slug["tree_budget"] and "not guaranteed" in by_slug["tree_budget"]
    assert "plan angles" in by_slug["pentagon_math"]
    star, beams, fan = by(F["patterns"], "star"), by(F["patterns"], "beams"), by(F["patterns"], "fan")
    assert not star["deck_ok"] and "fails" in by_slug["star"]
    assert B["deck_gap_in"] <= B["deck_allow_in"] and "inside the" in by_slug["joists"]
    assert abs(B["pier_sum_lb"] - B["total_lb"]) < 1.0 and "every pound accounted for" in by_slug["loads"]
    assert B["worst"] <= 1.0
    rings = by(F["patterns"], "rings")
    others = [r for r in F["patterns"] if r["key"] not in ("beams", "rings")]
    assert all(beams["worst"] <= r["worst"] for r in others) and rings["worst"] < beams["worst"]
    assert rings["piers"] > 2 * beams["piers"] and "Only the nested rings" in by_slug["extremes"]
    assert all(fan["pier_max_lb"] >= r["pier_max_lb"] for r in F["patterns"])
    assert B["fits"] and B["margin_ft"] > 0 and "It fits" in by_slug["frame5"]
    assert abs(B["corner_deg"] - 36.0) < 0.01 and abs(B["frame_back_in"] - 240.0) < 0.01
    assert by(F["gravel"], "rings")["logs"] > by(F["gravel"], "star_joists")["logs"] and "eats logs" in by_slug["gravel"]
    assert B["joist_depth_in"] > B["saw_height_in"] and "beyond the saw" in by_slug["joist_saw"]
    mats = {r["prim"]: r for r in F["materials"]}
    assert mats["round"]["piers"] == mats["half"]["piers"] and "the same piers" in by_slug["materials"]
    assert mats["4x4"]["piers"] > mats["half"]["piers"]
    assert W["cuts"][1]["off_long"] > 12 and "goes back on the pile" in by_slug["saw2"]
    EVERY_PIECE_LESSON.validate()


def report() -> str:
    from infill import base as bs
    from infill.constants import table
    return table() + "\n\n" + "\n".join(bs.constants_table()) + "\n\n" + method.report()


EVERY_PIECE_LESSON = Lesson(
    key="cabin_every_piece", brand="DOMESIM", title="Every Piece, Numbered: Filling the Triangles and Framing the Floor",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_every_piece_film, report=report,
    snapshot_prefix="cabin_every_piece", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
