"""Beyond the Dome: building with wedges -- the zome, the shed, the octagon, the joints.

The film of *'Square' on Demand* and the Wedge Zome tool (October 2026), set
in the Cabin World. The wedge method beyond the dome: what a split gives, two
wedges made into a square on demand, quarters back to back, finer splits that
pair into boards, shims split from the same log, the skew as a roof pitch, the
octagon already in the log, the joints wedges make easy, the seam as a
channel, the honest comparison with the mill -- and then a whole zome framed
from the dome's own wedges, every stick's cut on screen, the square-stick
method beside it, the buildings wedges suit, the crews that could build them.

Nothing is drawn for the film. The pieces are :mod:`two_v_demo.wedge_beyond_scene`'s
solids, built from :mod:`square_book.geometry` and :mod:`wedge_zome.geometry`;
every figure is read from :mod:`square_book.tokens`, :func:`wedge_zome.fabrication.facts`
or the pitch's published veteran table.

    py -3.12 -m rerender stills cabin_wedge_beyond
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import shots
from . import wedge_beyond_scene as ws
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)


def _facts() -> dict:
    from master_book import pitch
    from square_book import tokens as sq
    from wedge_zome import fabrication as fab

    t = sq.table()
    z = fab.facts("wedge")
    zs = fab.facts("square")
    from master_book import tokens as mb

    def tok(name: str) -> str:
        return mb.resolve("{{" + name + "}}")

    t = dict(t, **{"dome.members": tok("dome.members"), "wood.shrink_t": tok("wood.shrink_t"),
                   "wood.shrink_r": tok("wood.shrink_r"), "parts.sections": tok("parts.sections"),
                   "cut.splits": tok("cut.splits")})
    return {"t": t, "z": z, "zs": zs, "vets": pitch.VETERANS, "when": pitch.VETERANS_COUNTED,
            "programs": ", ".join(pitch.VETERAN_PROGRAMS)}


F = _facts()
T, Z, ZS = F["t"], F["z"], F["zs"]
PC = ws.PC


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app) -> None:
    cw.paint(app, hide=("builder",), subject=False)
    app.static_layer("beyond:platform", cabin_stage.platform)


def _layer(app, key: str, builder) -> None:
    app.static_layer(f"beyond:{key}", builder)


def _pair_layer(app, key, builder, transparent) -> None:
    opaque, clear = builder()
    _layer(app, key, lambda: opaque)
    transparent.vertices.extend(clear.vertices)


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome", lambda: ws.zome("wedge"), transparent)
    _label(app, ws.zome_point("apex") + [0, 0, 0.35], "BEYOND THE DOME", AMBER)


def p_split(app, opaque, transparent, p):
    _world(app)
    b = ws.log_split(min(1.0, p * 1.4))
    opaque.vertices.extend(b.vertices)
    _label(app, PC + [0, 0, 0.55], f"{T['sq.split_pct']}% OF THE LOG KEPT", AMBER)
    _label(app, PC + [0.9, 0, 0.35], f"{T['sq.theta']}° AT THE PITH", WHITE)


def p_measured(app, opaque, transparent, p):
    _world(app)
    _layer(app, "single", ws.wedge_single)
    _label(app, PC + [0.55, 0, 0.18], f"BACK {T['sq.chord']} in", AMBER)
    _label(app, PC + [0.55, 0, 0.32], f"DEPTH {T['sq.depth']} in", BLUE)
    _label(app, PC + [0.55, 0, 0.46], f"{T['sq.beta']}° AT THE BACK", WHITE)


def p_square(app, opaque, transparent, p):
    _world(app)
    b, tr = ws.slant_pair(min(1.0, p * 1.6))
    opaque.vertices.extend(b.vertices)
    transparent.vertices.extend(tr.vertices)
    if p > 0.62:
        _label(app, PC + [0.55, 0, 0.3], f"{T['sq.square']} in SQUARE", AMBER)
    _label(app, PC + [0.55, 0, 0.45], f"{T['sq.acute']}° / {T['sq.obtuse']}°", WHITE)


def p_back(app, opaque, transparent, p):
    _world(app)
    _layer(app, "back", ws.back_pairs)
    _label(app, PC + [0.5, -0.25, 0.32], f"QUARTERS: {T['sq.quarter_square']} in SQUARE", AMBER)
    _label(app, PC + [0.5, 0.3, 0.32], "EIGHTHS: A DIAMOND", BLUE)


def p_finer(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "tradeoff", ws.tradeoff, transparent)
    for k, n in enumerate((6, 8, 12, 16)):
        _label(app, PC + [0.45, -0.6 + 0.4 * k, 0.3], f"{n} WAYS", AMBER if n == int(T["sq.best_n"]) else WHITE)


def p_shim(app, opaque, transparent, p):
    _world(app)
    _layer(app, "shim", ws.shim)
    _label(app, PC + [0.5, -0.15, 0.25], f"{T['sq.shim_deg']}° SHIM: A {T['sq.shim_split']}-WAY SPLIT", AMBER)


def p_pitch(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "shed", ws.shed, transparent)
    _label(app, PC + [0, 0, 1.75], f"{T['sq.pitch8']} IN 12", AMBER)


def p_octagon(app, opaque, transparent, p):
    _world(app)
    _layer(app, "octagon", ws.octagon)
    _label(app, PC + [0, 0, 0.35], f"{T['sq.theta']}° x 8", AMBER)


def p_joints(app, opaque, transparent, p):
    _world(app)
    _layer(app, "joints", ws.joints)
    _label(app, PC + [0.2, -0.55, 0.32], "SLANT LAP", WHITE)
    _label(app, PC + [-0.45, 0.05, 0.36], "BIRD'S MOUTH", WHITE)
    _label(app, PC + [0.2, 0.6, 0.32], "BUTTERFLY KEY", WHITE)


def p_pinwheel(app, opaque, transparent, p):
    _world(app)
    _layer(app, "jig2", lambda: ws.zome_panel_on_jig(2))
    _label(app, PC + [0, 0, 1.15], "FOUR STICKS, A PINWHEEL", AMBER)


def p_seam(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "seam", ws.seam_v, transparent)
    _label(app, PC + [0.5, 0, 0.3], f"A {T['sq.theta']}° CHANNEL", BLUE)


def p_mill(app, opaque, transparent, p):
    _world(app)
    _layer(app, "mill_log", lambda: ws.log_split(1.0))


def p_zome(app, opaque, transparent, p):
    _world(app)
    b, tr = ws.zome("wedge", rise=min(1.0, p * 1.3))
    opaque.vertices.extend(b.vertices)
    transparent.vertices.extend(tr.vertices)
    _label(app, ws.zome_point("apex") + [0, 0, 0.3], f"{Z['panels']} PANELS, {len(Z['rows'])} ROWS", AMBER)


def p_backout(app, opaque, transparent, p):
    _world(app)
    explode = 14.0 * math.sin(math.pi * min(1.0, p * 1.2)) if p < 0.85 else 0.0
    b, tr = ws.zome("wedge", explode=explode, channels=explode == 0.0)
    opaque.vertices.extend(b.vertices)
    transparent.vertices.extend(tr.vertices)
    _label(app, ws.zome_point("seam") + [0, -0.2, 0.25],
           f"CLOSED OUTSIDE, {Z['gap_lo']:.1f}-{Z['gap_hi']:.1f}° V INSIDE", BLUE)


def p_cuts(app, opaque, transparent, p):
    _world(app)
    row = 1 + min(3, int(p * 4))
    b, tr = ws.zome("wedge", highlight=row)
    opaque.vertices.extend(b.vertices)
    _label(app, ws.zome_point("apex") + [0, 0, 0.3], f"ROW {row}", AMBER)


def p_jig(app, opaque, transparent, p):
    _world(app)
    _layer(app, "jig3", lambda: ws.zome_panel_on_jig(3))
    r = Z["rows"][2]
    _label(app, PC + [0, 0, 1.15], f"ROW 3: SHARP CORNER {r['acute']:.1f}°", AMBER)


def p_square_method(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome_square", lambda: ws.zome("square"), transparent)
    _label(app, ws.zome_point("apex") + [0, 0, 0.3], "SQUARE STICKS + WEDGE BLOCKS", AMBER)


def p_takes(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome_ch", lambda: ws.zome("wedge", channels=True), transparent)
    _label(app, ws.zome_point("apex") + [0, 0, 0.3],
           f"{Z['stock']['sections']} SECTIONS (SQUARE: {ZS['stock']['sections']})", AMBER)


def p_meet(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome_posts", lambda: ws.zome("wedge"), transparent)
    _label(app, ws.zome_point("rim") + [0, -0.2, 0.0], f"POSTS: {T['sq.quarter_square']} in SQUARE", AMBER)


def _montage():
    b, tr = TriangleBatch(), TriangleBatch()
    pieces = (
        (lambda: ws.shed(0.5), (-0.95, -0.85), 0),
        (lambda: (ws.aframe(0.5), TriangleBatch()), (0.95, -0.85), 0),
        (lambda: (ws.octagon(26.0), TriangleBatch()), (-0.95, 0.9), 0),
        (lambda: ws.zome("wedge", fit=0.26), (0.95, 0.9), 0),
    )
    for build, (dx, dy), yaw in pieces:
        o, c = build()
        b.vertices.extend(ws._place(o, PC + [dx, dy, 0], yaw).vertices)
        tr.vertices.extend(ws._place(c, PC + [dx, dy, 0], yaw).vertices)
    return b, tr


def p_buildings(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "montage", _montage, transparent)
    _label(app, PC + [-0.95, -0.85, 1.0], "SHED", WHITE)
    _label(app, PC + [0.95, -0.85, 0.95], "A-FRAME", WHITE)
    _label(app, PC + [-0.95, 0.9, 0.25], "OCTAGON", WHITE)
    _label(app, PC + [0.95, 0.9, 0.75], "ZOME", WHITE)


def p_vets(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome", lambda: ws.zome("wedge"), transparent)
    _label(app, ws.zome_point("apex") + [0, 0, 0.35], f"{F['vets']['pit'][0]:,} VETERANS (HUD)", AMBER)


def p_safety(app, opaque, transparent, p):
    _world(app)
    _layer(app, "safe_log", lambda: ws.log_split(0.0))
    _label(app, PC + [0, 0, 0.6], "NEVER ALONE AT THE LOG", RED)


def p_close(app, opaque, transparent, p):
    _world(app)
    _pair_layer(app, "zome", lambda: ws.zome("wedge"), transparent)


SCENES = {
    "open": p_open, "split": p_split, "measured": p_measured, "square": p_square, "back": p_back,
    "finer": p_finer, "shim": p_shim, "pitch": p_pitch, "octagon": p_octagon, "joints": p_joints,
    "pinwheel": p_pinwheel, "seam": p_seam, "mill": p_mill, "zome": p_zome, "backout": p_backout,
    "cuts": p_cuts, "jig": p_jig, "square_method": p_square_method, "takes": p_takes, "meet": p_meet,
    "buildings": p_buildings, "vets": p_vets, "safety": p_safety, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

MATH = ("square", "mill", "cuts")


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
    low = PC + [0.0, 0.0, 0.12]
    mid = PC + [0.0, 0.0, 0.6]
    zc = ws.zome_point("centre")
    seam = ws.zome_point("seam")
    rim = ws.zome_point("rim")
    table = PC + [0.0, 0.0, 0.8]
    hero = np.array(cw.HERO_EYE)
    end = PC + [0.48, 0.0, 0.07]                       # the pieces' end grain, where the sections show
    end_on = lambda r, h, a=-35, s=30, at=None: shots.orbit(end if at is None else at, r, h, a, s, 40)

    def outward(point, near: float, far: float, up_near: float, up_far: float):
        o = np.array([point[0] - PC[0], point[1] - PC[1], 0.0])
        o /= np.linalg.norm(o) + 1e-9
        side = np.array([-o[1], o[0], 0.0]) * 0.35
        return shots.push_in(point, point + o * far + side + [0, 0, up_far],
                             point + o * near + side + [0, 0, up_near], 46, 40)

    t = {
        "open": shots.crane_reveal(zc, zc + [1.4, 3.0, -0.4], zc + [2.6, 5.4, 2.2], 44, 50),
        "split": shots.orbit(PC + [0.95, 0, 0.17], 1.6, 0.35, -40, 40, 44),
        "measured": end_on(0.85, 0.14),
        "square": end_on(0.9, 0.16, -30, 25),
        "back": end_on(1.25, 0.25, -25, 30, at=PC + [0.46, 0.02, 0.08]),
        "finer": shots.orbit(PC + [0.4, 0, 0.06], 1.9, 0.6, -20, 30, 44),
        "shim": end_on(0.9, 0.16, -30, 25),
        "pitch": shots.orbit(mid, 4.2, 1.7, 40, 40, 46),
        "octagon": shots.orbit(low, 3.3, 2.6, 60, 40, 46),
        "joints": shots.orbit(low, 2.6, 1.3, 25, 40, 46),
        "pinwheel": shots.orbit(table, 2.4, 1.6, 70, 30, 44),
        "seam": end_on(0.85, 0.2, -25, 25),
        "mill": shots.orbit(PC + [0.95, 0, 0.17], 1.8, 0.45, 20, 30, 44),
        "zome": shots.orbit(zc, 5.2, 2.1, 70, 40, 46),
        "backout": outward(seam, 1.6, 3.2, 0.5, 1.1),
        "cuts": shots.orbit(zc, 5.0, 2.6, 100, 30, 46),
        "jig": shots.orbit(table, 2.3, 1.7, 110, -30, 44),
        "square_method": shots.orbit(zc, 5.0, 2.0, 40, 40, 46),
        "takes": shots.orbit(zc, 4.4, 1.2, 120, 30, 48),
        "meet": outward(rim, 1.5, 3.0, 0.4, 1.0),
        "buildings": shots.orbit(mid, 5.2, 2.6, 70, 50, 48),
        "vets": shots.orbit(zc, 5.6, 1.6, 140, 30, 48),
        "safety": shots.orbit(PC + [0.95, 0, 0.17], 2.0, 0.6, -60, 30, 44),
        "close": shots.crane_reveal(m.dome_centre + [0, 0, 1.0], hero + [0.4, 3.0, 0.0],
                                    hero + [1.2, -2.5, 4.0], 46, 54, look_start=zc),
    }
    out = {}
    for slug, shot in t.items():
        if slug in MATH:
            shot = beside_worksheet(shot)
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


def _chapters() -> tuple[Chapter, ...]:
    s = Z["stock"]
    ss = ZS["stock"]
    rows = Z["rows"]
    types = Z["types"]
    mitres = " / ".join(f"{abs(t['tail'][0]):.1f}" for t in types[::2])
    blocks = " / ".join(str(b["split"]) for b in Z["blocks"])
    vets = F["vets"]
    t = T
    rows_ = [
        (1, "open", "Beyond the dome", "The same wedges, other buildings.",
         f"The dome on this hill is framed from {t['dome.members']} wedges split from logs "
         f"with one chainsaw. This film is about everything else those wedges can build. A zome, framed from the "
         f"same pile. Square posts, made from wedges on demand. A roof whose pitch is already in the log. An "
         f"octagon, a set of joints, and a seam that carries water. And it starts where every wedge does: with a "
         f"log.", [f"one log -> {t['sq.split_pct']}% kept as wedges"]),
        (2, "split", "Why wedges", "The log does the geometry.",
         f"A log split through its centre, halved, halved again and halved once more, gives {t['cut.splits']} wedges of "
         f"exactly {t['sq.theta']} degrees, and nobody measures an angle. The saw takes only its kerf: "
         f"{t['sq.split_pct']} percent of a {t['sq.log']} inch log is kept as members. And because every flat face "
         f"runs through the heart, wedges move least as they dry: pine shrinks {t['wood.shrink_t']} percent around "
         f"its rings and {t['wood.shrink_r']} across them, and a radial face sits square across the rings.",
         [f"{t['sq.theta']} deg x 8 = 360", f"kept: {t['sq.split_pct']}%"]),
        (3, "measured", "The wedge, measured", "Two faces, a back, two angles.",
         f"Know the stick you have. An eighth of the reference log has two flat faces meeting at the pith at "
         f"{t['sq.theta']} degrees. Trim its curved back flat and the back is {t['sq.chord']} inches wide, "
         f"{t['sq.depth']} inches from the point, with corners of {t['sq.beta']} degrees. Those angles never change "
         f"with the size of the log. Only the split changes them.",
         [f"back {t['sq.chord']} in, depth {t['sq.depth']} in", f"corners {t['sq.beta']} deg"]),
        (4, "square", "Square on demand", "Two wedges, slant to slant.",
         f"Now take two. Turn one end for end and lay it against the other, slant to slant. What you hold looks "
         f"like a two by four pushed sideways, with corners of {t['sq.acute']} and {t['sq.obtuse']} degrees. Plane "
         f"it square to its long face and the board inside it is the radius times the cosine of the point angle, by "
         f"the radius times the sine. For an eighth, those are the same number. The pair planes to a square, "
         f"{t['sq.square']} inches on a side. It costs wood: it keeps {t['sq.square_kept']} percent of the log, "
         f"against {t['sq.split_pct']} for the wedges as they are. So you square only what needs it. Square, on "
         f"demand.",
         ["planed board = R cos(theta) x R sin(theta)", f"theta = {t['sq.theta']} deg: cos = sin = {t['sq.cos45']}",
          f"square: {t['sq.square']} in", f"kept: {t['sq.square_kept']}% vs {t['sq.split_pct']}% as wedges"],
         "math"),
        (5, "back", "Back to back", "Quarters make a post.",
         f"Put two wedges together on their backs instead. Quarters, back to back, are already a square, "
         f"{t['sq.quarter_square']} inches on a side, with nothing to plane: the heaviest square the method makes, "
         f"and the one for posts. Two eighths back to back make a diamond, a poor board but the right shape for a "
         f"ridge, a rail that sheds water both ways, or a spline.",
         [f"quarters: {t['sq.quarter_square']} in square, {t['sq.quarter_kept']}% kept"]),
        (6, "finer", "Split finer, get boards", "Thinner wedges pair flatter.",
         f"The thinner the wedge, the closer a pair is to a board, because a pair keeps the cosine of its point "
         f"angle when it is planed. But every split is another saw cut. On the reference log the two balance at "
         f"{t['sq.best_n']} ways: pairs plane to boards {t['sq.n16_w']} by {t['sq.n16_t']} inches and keep "
         f"{t['sq.best_kept']} percent of the log. Quarter the butt for posts, split the middle {t['cut.splits']} ways for "
         f"frames, and take the top {t['sq.best_n']} ways for boards.",
         [f"16 ways: {t['sq.n16_w']} x {t['sq.n16_t']} in, {t['sq.best_kept']}%",
          f"12 ways: {t['sq.n12_w']} x {t['sq.n12_t']} in, {t['sq.n12_kept']}%"]),
        (7, "shim", "Shims from the same log", "Halve once more.",
         f"Where a wedge has to meet the square world for a short way, shim it there and leave it a wedge everywhere "
         f"else. Lying on its back, an eighth's face stands at {t['sq.beta']} degrees. A plumb face needs "
         f"{t['sq.shim_deg']} more, which is half the point, which is exactly a wedge from a log split "
         f"{t['sq.shim_split']} ways. The shims come from the same log. Halve one more time.",
         [f"90 - {t['sq.beta']} = {t['sq.shim_deg']} deg = a {t['sq.shim_split']}-way split"]),
        (8, "pitch", "The skew is a roof pitch", f"{t['sq.pitch8']} in twelve, from the log.",
         f"Keep the skew where the building already slopes. A pair of eighths laid flat has faces at "
         f"{t['sq.shim_deg']} degrees, a rise of {t['sq.pitch8']} in twelve: an ordinary roof. Use pairs as rafters "
         f"and the sheathing seats flat with no bevel cut. Twelfths give {t['sq.pitch12']} in twelve, a low shed "
         f"roof; quarters {t['sq.pitch4']} in twelve, a steep one. Choose the split for the roof you want.",
         [f"eighths: {t['sq.pitch8']} in 12", f"twelfths: {t['sq.pitch12']} in 12"]),
        (9, "octagon", "The octagon is in the log", f"{t['sq.theta']} degrees, {t['cut.splits']} times.",
         f"An eighth's point is the angle at the centre of an octagon. Eight wedge joists meet at the middle of a "
         f"round deck with no angle measured, and the corners round the rim are the {t['sq.oct_interior']} degrees "
         f"an octagon needs. Gazebos, round decks, yurt floors and tables are the log, put back together flat.",
         [f"{t['sq.theta']} x 8 = 360; rim corners {t['sq.oct_interior']} deg"]),
        (10, "joints", "Joints wedges make easy", "Lap, bird's mouth, key.",
         "Wedge lumber has flat faces at known angles, and each is the start of a joint. Two pairs laid slant to "
         "slant and offset make a scarf, a long member from short wedges. A wedge's point, set down over a square "
         "plate, is a bird's mouth already cut. A butterfly key let in across a glued pair stitches it. None of "
         "them needs a square face to start from: the joint line is the reference.",
         ["slant lap, bird's mouth, butterfly key"]),
        (11, "pinwheel", "The pinwheel", "Nothing meets at the corner.",
         "The dome's joint, and the zome's. Where sticks meet at a corner, none of them runs into it. Each reaches "
         "the corner ahead of it, and its tail butts the side of the stick behind, round the corner like the "
         "blades of a pinwheel. Nothing meets at a point, so nothing has to be cut to a compound angle there. Here "
         "it frames one zome panel, flat on its jig.",
         ["each stick: head at the corner, tail on the stick behind"]),
        (12, "seam", "The seam is a channel", "The V is the duct.",
         f"Square lumber laid side by side closes up. Wedges on their backs open a V, the full length of the "
         f"member, of exactly the wedge's point, {t['sq.theta']} degrees. Capped, it is a gutter that cannot "
         f"overflow sideways, a cable run you can open, a way to breathe a wall. Big services go in the building's "
         f"core; the seams take water, wire and air.",
         [f"V = {t['sq.theta']} deg, every seam the same"]),
        (13, "mill", "Against the mill", "The number that argues back.",
         f"Here is the method measured against a sawmill, on the reference log. Split, the log keeps "
         f"{t['sq.split_pct']} percent. With the backs trimmed, {t['sq.tri_pct']}. Split {t['sq.best_n']} ways and "
         f"paired into boards, {t['sq.best_kept']}. The project's sawmill simulator, packing two by fours, keeps "
         f"{t['sq.sawn_pct']}. And eighths paired and planed square keep only {t['sq.squares_pct']}, less than the "
         f"mill. That is the number that argues back, and it is why the title says on demand.",
         [f"split: {t['sq.split_pct']}%", f"backs trimmed: {t['sq.tri_pct']}%",
          f"paired boards ({t['sq.best_n']} ways): {t['sq.best_kept']}%", f"mill, 2x4s: {t['sq.sawn_pct']}%",
          f"paired squares: {t['sq.squares_pct']}%"], "math"),
        (14, "zome", "A zome from the same pile", f"{Z['panels']} panels, {len(rows)} rows.",
         f"Now a whole building that is not a dome. A zome: {Z['panels']} rhombus panels in {len(rows)} rows "
         f"twisting round a point, {Z['rim_ft']:.1f} feet across and {Z['height_ft']:.1f} feet tall, every panel "
         f"side {Z['side']:.1f} inches. It is the same zome the Complete Edition works through, framed here from "
         f"the dome's own wedges: eighths of a {Z['log']:.0f} inch log.",
         [f"{Z['panels']} panels, {len(rows)} rows", f"{Z['rim_ft']:.1f} ft x {Z['height_ft']:.1f} ft"]),
        (15, "backout", "Wedges, back out", "The seams close by themselves.",
         f"Every panel is four wedge sticks in a pinwheel, framed flat, with the wedge's back on the outside and "
         f"its point toward the room. A wedge's sides lean {Z['half']:.1f} degrees away from square, so where two "
         f"panels fold together their backs close tight along the outside seam, and the inside opens into a V of "
         f"{Z['gap_lo']:.1f} to {Z['gap_hi']:.1f} degrees: the wedge's point less the fold. Every fold of this zome, "
         f"up to {Z['fold_hi']:.1f} degrees, is less than an eighth's point, so nothing collides and nothing needs a "
         f"block. The weather side is closed. The inside is a channel.",
         [f"inside V = {Z['theta']:.0f} - fold = {Z['gap_lo']:.1f} to {Z['gap_hi']:.1f} deg"]),
        (16, "cuts", "One bevel for every cut", "Only the mitre changes.",
         f"And this is the part a builder will like. Solve every stick's two end cuts in three dimensions, and "
         f"every end of every stick in the zome takes the same bevel: {Z['half']:.1f} degrees, half the wedge's "
         f"point. Set it once. Only the mitre changes, once per row: {mitres} degrees, and the two stick types in a "
         f"row are mirror images. {s['sticks']} sticks, {len(types)} types.",
         [f"bevel, every end: {Z['half']:.1f} deg"] +
         [f"row {r['row']}: {t_['outer']:.2f} in, mitre {abs(t_['tail'][0]):.1f} deg x{2 * t_['count']}"
          for r, t_ in zip(rows, types[::2])], "math"),
        (17, "jig", "A panel on the jig", "Built flat, at waist height.",
         f"Each row has its own jig: stops screwed to a sheet at the row's rhombus, full size. Row three's sharp "
         f"corner is {rows[2]['acute']:.1f} degrees, nearly square; the crown's is {rows[0]['acute']:.1f}. Lay four "
         f"sticks in, back down, glue and screw each butt in the thick part, and the panel comes off true. Nine "
         f"times a row, four rows.",
         [f"row 3 corner {rows[2]['acute']:.1f} deg", f"crown corner {rows[0]['acute']:.1f} deg"]),
        (18, "square_method", "The other way: square sticks", "Wedge blocks in the gaps.",
         f"There is a second way, the one the Complete Edition describes: square sticks, two wedges paired and "
         f"planed {ZS['stick_w']:.2f} inches square. Square-edged panels meet on their inside edges and open a V "
         f"outside, which a wedge block fills. A block's point is three hundred and sixty degrees divided by its "
         f"split, so each fold wants a log split that many ways: {blocks}. It works, and it takes "
         f"{ss['sections']} log sections against {s['sections']}.",
         [f"blocks: {blocks}-way splits", f"sections: {ss['sections']} vs {s['sections']}"]),
        (19, "takes", "What it takes", f"{s['sections']} sections of log.",
         f"Framed the wedge way, the zome's {s['sticks']} sticks come {s['sticks_per_wedge']} from each wedge of the "
         f"dome's own {Z['section']:.0f} inch sections: {s['wedges']} wedges, {s['sections']} sections of log. The "
         f"dome on this hill takes {t['parts.sections']}. And every one of the zome's {Z['seams']} inside seams is a channel "
         f"before anybody runs a wire.",
         [f"{s['sticks']} sticks, {s['wedges']} wedges, {s['sections']} sections"]),
        (20, "meet", "Meeting the square world", "Posts, shims and a sill.",
         f"A zome's rim zigzags: {Z['rim_corners']} corners, {Z['posts']} of them {Z['post_h']:.1f} inches above the "
         f"rest. Stand a post under each high corner, quarters back to back, {Z['post_square']:.2f} inches square. "
         f"Set a sill ring under the low ones. Where a door frame or a square wall meets a wedge, shim it there. "
         f"The wedge stays a wedge; only the joints learn to be square.",
         [f"{Z['posts']} posts, {Z['post_h']:.1f} in, {Z['post_square']:.2f} in square"]),
        (21, "buildings", "Buildings that suit wedges", "Triangles, slopes, octagons.",
         "Some buildings want boards. The ones made of triangles, slopes, octagons and posts want wedges. A shed "
         "with pair rafters at the log's own pitch. An A-frame. A gazebo on an octagon of wedge joists. A zome. "
         "The pattern is the same in every one: square the pieces that meet the level world, and leave everything "
         "triangulated, sloped or radial as wedges.",
         ["square: posts, plates, frames", "wedge: everything triangulated, sloped, radial"]),
        (22, "vets", "Built by veterans", "A system, a crew, a village.",
         f"This method was written by a veteran. On one night in {F['when']}, {vets['pit'][0]:,} veterans had no home "
         f"of their own, {vets['unsheltered'][0]:,} of them unsheltered, by HUD's count. A building that is a "
         f"system, maintained on a schedule, with parts you swap in the field and a crew that builds together, "
         f"fits the way a lot of veterans already work. It is designed to sit beside {F['programs']}, and to be "
         f"built and kept by veterans.",
         [f"{vets['pit'][0]:,} veterans, one night ({F['when']}, HUD)"]),
        (23, "safety", "Safety at the log", "Never alone.",
         "All of it starts with a chainsaw in a log, the most dangerous part of the work. Never alone at the log. "
         "Full protective gear. The log cradled for the first cut. A chain filed for ripping. Every split made "
         "with the saw, never with an axe or a maul. And none of these buildings is rated by this film: an "
         "engineer checks anything that carries people, snow or wind before anyone lives in it.",
         ["two people at the log, every session", "an engineer before anyone lives in it"]),
        (24, "close", "Split everything. Square on demand.", "The zome is in the toolkit.",
         f"Split everything, and square only what needs it. The book is called Square on Demand, and the zome "
         f"you have just watched go up is a tool you can walk round: every stick, every cut, every jig, from the "
         f"same software that solves the dome.",
         [f"{s['sticks']} sticks, one bevel, {len(rows)} mitres"]),
    ]
    return tuple(_ch(*row) for row in rows_)


CHAPTERS = _chapters()


# ----------------------------------------------------------------------
# Selftest
# ----------------------------------------------------------------------

def validate_wedge_beyond_film() -> None:
    ws.validate_wedge_beyond_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert len({c.title for c in CHAPTERS}) == len(CHAPTERS)
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            eye, target, fov = MOVES[ch.slug](p)
            eye, target = np.asarray(eye, float), np.asarray(target, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, p)
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
            assert np.all(np.isfinite(opaque.vertices)), slug


def report() -> str:
    lines = ["BEYOND THE DOME -- figures", ""]
    for ch in CHAPTERS:
        lines.append(f"{ch.number} {ch.title}")
        lines += [f"    {e}" for e in ch.equations]
    return "\n".join(lines)


WEDGE_BEYOND_LESSON = Lesson(
    key="cabin_wedge_beyond", brand="DOMESIM", title="Beyond the Dome: Building With Wedges",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_wedge_beyond_film, report=report,
    snapshot_prefix="cabin_wedge_beyond", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
