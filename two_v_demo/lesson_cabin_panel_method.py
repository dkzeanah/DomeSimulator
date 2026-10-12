"""The Panel Method: a three-frequency dome of framed panels, in the Cabin World.

The method -- every triangle its own small frame of sawn sticks, built flat on
a plywood jig, skinned in sections and screwed to its neighbours -- builds a
popular, tried-and-true dome, the three-frequency five-eighths, and the film
shows it for comparison with the wedge dome. Every shape is solved by
:mod:`two_v_demo.panel_method` for this project's own reference dome and drawn
by :mod:`two_v_demo.panel_scene`; every figure in the narration is read from
:func:`panel_method.facts` or, for the wedge dome, from ``wedge_book.numbers``
-- the same values the book prints.

    py -3.12 -m rerender stills cabin_panel_method
    py -3.12 -m rerender render cabin_panel_method
"""

from __future__ import annotations

import math
from functools import partial

import numpy as np

from . import cabin_stage, cabin_world as cw, panel_method as pm, panel_scene as ps, shots
from . import channel_scene as sc
from .geometry import normalize
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

IN, FT, SQFT = 1 / 0.0254, 1 / 0.3048, 1 / 0.3048 ** 2
WHITE, AMBER, GREEN, CYAN, RED = (240, 236, 226), (255, 205, 130), (111, 235, 155), (120, 225, 240), (255, 140, 120)


def _figures() -> dict:
    """Every number the film says, from where it is computed."""
    from wedge_book import numbers

    f = pm.facts()
    q = numbers.quantities()
    pent, hexa = f["pent_class"], f["hex_class"]
    hex_sticks = [s for key, _n, s in f["stick_rows"] if key.startswith("hexa") and s.letter == "C"]
    zrows = f["zome_rows"]
    return {
        "base_ft": f"{pm.CONSTANTS['base_ft'].value:.0f}",
        "a": f"{f['chords']['A'] * IN:.1f}", "b": f"{f['chords']['B'] * IN:.1f}", "c": f"{f['chords']['C'] * IN:.1f}",
        "panels": f["panels"], "pent": f["pent"], "hex": f["hex"],
        "fraction": f"{f['height_fraction']:.3f}",
        "base_edges": f["base_edges"], "tapered": f["tapered"], "level": f["level"],
        "taper_mm": f"{f['taper_m'] * 1000:.0f}", "taper_in": f"{f['taper_m'] * IN:.2f}",
        "hex_height": f"{hexa.height * IN:.1f}",
        "c1": f"{hex_sticks[0].outer_length * IN:.2f}", "c2": f"{hex_sticks[1].outer_length * IN:.2f}",
        "m1": f"{hex_sticks[0].tail_miter:.1f}", "m2": f"{hex_sticks[1].tail_miter:.1f}",
        "bevel_lo": f"{f['bevel_lo']:.1f}", "bevel_hi": f"{f['bevel_hi']:.1f}",
        "bevel_mid": f"{f['bevel_mid']:.1f}", "bevel_err": f"{(f['bevel_hi'] - f['bevel_lo']) / 2:.1f}",
        "sec_pent": f["sections_pent"], "sec_hex": f["sections_hex"], "sec_single": f["sections_single"],
        "deck_sides": f["deck"].sides, "rim_miter": f"{f['deck'].rim_miter_deg:.0f}",
        "girders": f["deck"].girders, "girder_miter": f"{f['deck'].girder_miter_deg:.0f}",
        "rim_in": f"{f['deck'].rim_length_m * IN:.1f}",
        "sticks": f["sticks"], "distinct": f["distinct_sticks"], "stick_ft": f"{f['stick_m'] * FT:.0f}",
        "height_ft": f"{f['height_m'] * FT:.1f}", "floor_sqft": f"{f['floor_m2'] * SQFT:.0f}",
        "zome_panels": f["zome_panels"], "zome_rows": len(zrows), "zome_per_row": zrows[0].count,
        "zome_scale": f"{round(1 / ps.ZOME_SCALE):.0f}",
        "gap_lo": f"{min(r.gap_m for r in zrows) * IN:.1f}", "gap_hi": f"{max(r.gap_m for r in zrows) * IN:.1f}",
        "zome_rim_ft": f"{f['zome_rim_m'] * FT:.1f}",
        "w_diam": f"{q['diameter_ft'].value:.1f}", "w_members": f"{q['member_count'].value:.0f}",
        "w_panels": f"{q['face_count'].value:.0f}", "w_floor": f"{q['floor_sqft'].value:.0f}",
        "w_height": f"{q['height_ft'].value:.1f}",
        "pent_base": f"{pent.sides[0] * IN:.1f}", "pent_side": f"{pent.sides[1] * IN:.1f}",
        "hex_side": f"{hexa.sides[1] * IN:.1f}",
        "stick_w": f"{f['stick_w_m'] * IN:.2f}", "stick_d": f"{f['stick_d_m'] * IN:.2f}",
    }


F = _figures()


def label(app, position, text, colour=WHITE):
    app.world_labels.append(WorldLabel(np.asarray(position, dtype=np.float32), text, colour))


# ----------------------------------------------------------------------
# Layers: built once, drawn every frame
# ----------------------------------------------------------------------

def _dome_points():
    d = ps.dome()
    r = d.cut.base_radius * d.radius_m
    c = ps.SITE
    return [np.array([c[0] + dx * r, c[1] + dy * r, z]) for dx in (-1, 1) for dy in (-1, 1)
            for z in (ps.DECK_TOP, ps.centre_top()[2])]


def _jig_points():
    return [ps.on_jig(x, y, z) for x in (-0.9, 0.9) for y in (-0.6, 0.6) for z in (0.0, 0.25)]


def panel_dome(app, frame=True, coloured=False, skin=True, sections=False, base=True,
               highlight_base=False, deck=True):
    if deck:
        app.static_layer("panel:deck", ps.deck_batch)
        app.static_layer("panel:brackets", ps.brackets)
    if base:
        key = "panel:base-hi" if highlight_base else "panel:base"
        app.static_layer(key, partial(ps.base_batch, highlight_base), _dome_points())
    if frame:
        key = "panel:frame-col" if coloured else "panel:frame"
        app.static_layer(key, partial(ps.frame_batch, coloured), _dome_points())
    if skin:
        key = "panel:skin-sec" if sections else "panel:skin"
        app.static_layer(key, partial(ps.skin_batch, sections))


def shop(app):
    cw.paint(app, subject=False)
    app.static_layer("panel:jig", ps.jig_bench, _jig_points())


# ----------------------------------------------------------------------
# Painters
# ----------------------------------------------------------------------

def p_two(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app)
    m = cw.landmarks()
    label(app, m.apex + [0, 0, 0.5], f"WEDGE DOME: {F['w_members']} SPLIT-LOG MEMBERS", AMBER)
    label(app, ps.centre_top() + [0, 0, 0.45], f"PANEL DOME: {F['panels']} FRAMED PANELS", CYAN)


def p_tried(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app)
    label(app, ps.centre_top() + [0, 0, 0.55], "A POPULAR BUILD, TRIED AND TRUE", WHITE)
    label(app, ps.centre_top() + [0, 0, 0.25], "EVERY NUMBER HERE: SOLVED BY OUR OWN CODE", GREEN)


def p_sphere(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, coloured=True, skin=False)
    d = ps.dome()
    for v in range(len(d.sphere.vertices)):
        if d.sphere.valence[v] == 5 and d.sphere.vertices[v, 2] >= d.cut.cut_level - 1e-9:
            opaque.sphere(ps.to_world(d.sphere.vertices[v]), 0.06, (1.0, 0.85, 0.3, 1.0), 5, 10)
    top = ps.centre_top()
    for k, (x, col) in enumerate((("A", AMBER), ("B", CYAN), ("C", GREEN))):
        label(app, top + [0, 0, 0.35 + 0.28 * k], f"{x} = {F[x.lower()]} IN", col)


def p_cut(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, skin=False)
    app.static_layer("panel:ghost", ps.cut_ghost)
    d = ps.dome()
    lo = ps.to_world(np.array([0, 0, d.cut.cut_level]))
    transparent.disc(lo + [0, 0, 0.002], d.radius_m * 1.06, (0.95, 0.75, 0.3, 0.18 + 0.12 * p), 60)
    label(app, ps.centre_top() + [0, 0, 0.4], f"{F['panels']} PANELS KEPT: {F['pent']} PENT + {F['hex']} HEX", WHITE)
    label(app, lo + [d.radius_m * 1.1, 0, 0.1], f"HEIGHT = {F['fraction']} x WIDTH", AMBER)


def _base_corner():
    """The base corner facing east, where the hill is open and flat."""
    corners = ps.deck_corners()
    return max(corners, key=lambda c: c[0])


def p_base(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, skin=False, highlight_base=True)
    c = _base_corner()
    label(app, c + [0, 0, 0.55], f"{F['tapered']} TAPERED / {F['level']} LEVEL", AMBER)
    label(app, c + [0, 0, 0.30], f"CORNERS {F['taper_mm']} MM APART IN HEIGHT", CYAN)


def p_panels(app, opaque, transparent, p):
    shop(app)
    d = ps.dome()
    pent, hexa = d.panel_classes()
    for pc, x0, col in ((pent, -0.6, AMBER), (hexa, 0.55, CYAN)):
        pts = ps.panel_on_jig(pc, x0)
        for k in range(3):
            ps.scribe(opaque, pts[k], pts[(k + 1) % 3])
        mid = np.mean(pts, axis=0)
        label(app, mid + [0, 0, 0.32], f"{pc.kind.upper()} x {pc.count}", col)
        label(app, (pts[0] + pts[1]) / 2 + [0, -0.12, 0.08], f"{pc.base * IN:.1f} IN", WHITE)
        label(app, (pts[1] + pts[2]) / 2 + [0.12, 0, 0.08], f"{pc.sides[1] * IN:.1f} IN", WHITE)


def p_rip(app, opaque, transparent, p):
    shop(app)
    at = ps.on_jig(0.0, 0.0, 0.0)
    opaque.vertices.extend(ps.board_halves(at, 0.9, min(1.0, p * 1.4), float(F["bevel_mid"])).vertices)
    label(app, at + [0, 0, 0.40], "FINISH FIRST, THEN RIP ON THE BEVEL", AMBER)
    label(app, at + [0, 0, 0.22], "THROUGH THE CENTRE: TWO COPIES", GREEN)


def p_jig(app, opaque, transparent, p):
    shop(app)
    d = ps.dome()
    hexa = d.panel_classes()[1]
    pts = ps.panel_on_jig(hexa, 0.0)
    left, right, apex = pts
    ps.scribe(opaque, left - [0.15, 0, 0], right + [0.15, 0, 0])
    a0 = math.atan2(apex[1] - left[1], apex[0] - left[0])
    a1 = math.atan2(apex[1] - right[1], apex[0] - right[0])
    reach = min(1.0, p * 1.6)
    ps.arc(opaque, left, hexa.sides[1], a0 - 0.25, a0 - 0.25 + 0.5 * reach)
    if p > 0.45:
        r2 = min(1.0, (p - 0.45) * 2.2)
        ps.arc(opaque, right, hexa.sides[2], a1 + 0.25, a1 + 0.25 - 0.5 * r2)
        tip = right + hexa.sides[2] * np.array([math.cos(a1 + 0.25 - 0.5 * r2), math.sin(a1 + 0.25 - 0.5 * r2), 0])
        ps._box_along(opaque, right + [0, 0, 0.012], tip + [0, 0, 0.012], 0.02, 0.008, ps.PINE_DARK)
    else:
        tip = left + hexa.sides[1] * np.array([math.cos(a0 - 0.25 + 0.5 * reach), math.sin(a0 - 0.25 + 0.5 * reach), 0])
        ps._box_along(opaque, left + [0, 0, 0.012], tip + [0, 0, 0.012], 0.02, 0.008, ps.PINE_DARK)
    if p > 0.85:
        ps.scribe(opaque, left, apex)
        ps.scribe(opaque, right, apex)
        opaque.sphere(apex + [0, 0, 0.01], 0.012, (0.9, 0.2, 0.2, 1.0), 4, 8)
    label(app, apex + [0, 0, 0.30], "WHERE THE ARCS CROSS: THE APEX", AMBER)
    label(app, (left + right) / 2 + [0, -0.15, 0.10], f"APEX {F['hex_height']} IN ABOVE THE BASE", WHITE)


def p_rails(app, opaque, transparent, p):
    shop(app)
    d = ps.dome()
    hexa = d.panel_classes()[1]
    pts = ps.panel_on_jig(hexa, 0.0)
    for k in range(3):
        ps.scribe(opaque, pts[k], pts[(k + 1) % 3])
    ps.rails(opaque, pts, d.stick_width_m)
    show = int(min(3, 1 + p * 3))
    for k, quad in enumerate(ps.pinwheel_sticks(pts, np.array([0, 0, 1.0]), d.stick_width_m)):
        if k < show:
            ps.prism(opaque, [q + [0, 0, d.stick_depth_m] for q in quad], np.array([0, 0, -d.stick_depth_m]), ps.PINE)
    label(app, np.mean(pts, axis=0) + [0, 0, 0.30], "STICK EDGE SPLITS THE LINE; RAIL BEHIND IT", AMBER)


def p_pinwheel(app, opaque, transparent, p):
    shop(app)
    d = ps.dome()
    hexa = d.panel_classes()[1]
    pts = ps.panel_on_jig(hexa, 0.0)
    ps.rails(opaque, pts, d.stick_width_m)
    cols = [ps.LETTER["B"], ps.LETTER["C"], (0.45, 0.70, 0.35, 1.0)]
    for k, quad in enumerate(ps.pinwheel_sticks(pts, np.array([0, 0, 1.0]), d.stick_width_m)):
        ps.prism(opaque, [q + [0, 0, d.stick_depth_m] for q in quad], np.array([0, 0, -d.stick_depth_m]), cols[k])
    label(app, pts[1] + [0.10, 0.25, 0.25], f"C: {F['c1']} IN, TAIL {F['m1']} DEG", GREEN)
    label(app, pts[2] + [-0.35, 0.05, 0.25], f"C: {F['c2']} IN, TAIL {F['m2']} DEG", GREEN)
    label(app, np.mean(pts, axis=0) + [0, -0.1, 0.42], f"{F['distinct']} DIFFERENT STICKS IN ALL", AMBER)


def _bevel_error_frame():
    """The frame with every stick tinted by how far one shop bevel is from exact."""
    d = ps.dome()
    mid = float(F["bevel_mid"])
    spread = max(1e-6, (float(F["bevel_hi"]) - float(F["bevel_lo"])) / 2)
    nb: dict[tuple[int, int], list[int]] = {}
    for i, t in enumerate(d.sphere.faces):
        for k in range(3):
            nb.setdefault(tuple(sorted((int(t[k]), int(t[(k + 1) % 3])))), []).append(i)
    b = TriangleBatch()
    for i, corners, n, _z in ps.panels():
        t = d.sphere.faces[i]
        cols = []
        for k in range(3):
            e = tuple(sorted((int(t[k]), int(t[(k + 1) % 3]))))
            fs = nb[e]
            exact = pm.fold_deg(d.sphere, *fs) / 2 if len(fs) == 2 else mid
            err = min(1.0, abs(exact - mid) / spread)
            cols.append((0.35 + 0.65 * err, 0.85 - 0.55 * err, 0.95 - 0.75 * err, 1.0))
        ps.framed_panel(b, corners, n, d.stick_width_m, d.stick_depth_m, cols)
    return b


def p_bevel(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, frame=False, skin=False)
    app.static_layer("panel:bevel-err", _bevel_error_frame, _dome_points())
    label(app, ps.centre_top() + [0, 0, 0.55], f"EXACT BEVEL: {F['bevel_lo']} TO {F['bevel_hi']} DEG", RED)
    label(app, ps.centre_top() + [0, 0, 0.27], f"ONE SETTING {F['bevel_mid']}: UP TO {F['bevel_err']} OFF", WHITE)


def p_skin(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, sections=True)
    label(app, ps.centre_top() + [0, 0, 0.55], f"{F['sec_pent']} PENTAGONS + {F['sec_hex']} HEXAGONS IN ONE SHEET", AMBER)
    label(app, ps.centre_top() + [0, 0, 0.27], f"{F['sec_single']} PANELS ONE BY ONE", WHITE)


def _window_face():
    d = ps.dome()
    lo, hi = ps.DECK_TOP + 0.9, ps.DECK_TOP + 1.9
    best = None
    for i, corners, n, z in ps.panels():
        if lo < z < hi and not d.sphere.is_pentagon_face(i):
            score = n[0] - abs(n[1]) * 0.5     # facing east, where the camera stands
            if best is None or score > best[0]:
                best = (score, i, corners, n)
    return best[1], best[2], best[3]


def p_window(app, opaque, transparent, p):
    cw.paint(app)
    i, corners, n = _window_face()
    app.static_layer("panel:frame-win", partial(ps.frame_batch, False, None, (i,)), _dome_points())
    panel_dome(app, frame=False, skin=False)
    d = ps.dome()
    corners = sorted(corners, key=lambda c: -c[2])
    hinge_a, hinge_b, low = corners[0], corners[1], corners[2]
    ps.framed_panel(opaque, [hinge_a, hinge_b, low], n, d.stick_width_m, d.stick_depth_m)
    axis = normalize(hinge_b - hinge_a)
    ang = math.radians(32.0) * min(1.0, p * 1.5)

    def turn(v):
        v = v - hinge_a
        return hinge_a + (v * math.cos(ang) + np.cross(axis, v) * math.sin(ang)
                          + axis * np.dot(axis, v) * (1 - math.cos(ang)))
    sash = [turn(c + n * d.stick_depth_m) for c in (hinge_a, hinge_b, low)]
    sn = normalize(np.cross(sash[1] - sash[0], sash[2] - sash[0]))
    if np.dot(sn, n) < 0:
        sn = -sn
    ps.framed_panel(opaque, sash, sn, d.stick_width_m, d.stick_depth_m)
    ps.film(transparent, sash, sn, (0.6, 0.85, 1.0, 0.35))
    foot = (low + (hinge_a + hinge_b) / 2) / 2
    opaque.cylinder(foot, (sash[2] + (sash[0] + sash[1]) / 2) / 2, 0.012, ps.STEEL, 8)
    label(app, low + n * 0.5 + [0, 0, 0.2], "A SPARE FRAME, HINGED; A GAS STRUT HOLDS IT", AMBER)


def p_raise(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, frame=False, skin=False)
    top = ps.centre_top()[2]
    upto = ps.DECK_TOP + (top - ps.DECK_TOP) * min(1.0, 0.15 + p * 1.0)
    opaque.vertices.extend(ps.frame_batch(False, upto).vertices)
    label(app, ps.centre_top() + [0, 0, 0.5], "FEW SCREWS UNTIL IT CLOSES; GASKET BETWEEN FRAMES", AMBER)
    label(app, ps.centre_top() + [0, 0, 0.22], "TAPE SEAMS BOTTOM UP, EACH LAPPING THE ONE BELOW", WHITE)


def p_deck(app, opaque, transparent, p):
    cw.paint(app)
    opaque.vertices.extend(ps.deck_batch(min(1.0, 0.05 + p * 1.1), floor=p > 0.8).vertices)
    c = np.array([ps.SITE[0], ps.SITE[1], ps.DECK_TOP])
    label(app, c + [0, 0, 0.9], f"{F['deck_sides']} JOISTS, {F['deck_sides']} RIM BOARDS AT {F['rim_miter']} DEG", AMBER)
    label(app, c + [0, 0, 0.6], f"{F['girders']} GIRDERS ON THE DOME'S FIVE-FOLD", CYAN)


def p_anchor(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app, skin=False)
    for corner in ps.deck_corners():
        opaque.sphere(corner + [0, 0, 0.05], 0.035, (1.0, 0.45, 0.3, 1.0), 4, 8)
    label(app, _base_corner() + [0, 0, 0.6], "BRACKETS TO THE DECK; ON GRAVEL, STAKES AND STRAPS", AMBER)


def zome_bench(app):
    cw.paint(app, subject=False)
    faces, base, _scale = ps.zome_faces()
    pts = [base + [dx, dy, dz] for dx in (-0.5, 0.5) for dy in (-0.5, 0.5) for dz in (0.0, 0.6)]
    app.static_layer("panel:zome-bench", lambda: _sawhorses_at(ps.ZOME_BENCH))
    app.static_layer("panel:zome", ps.zome_batch, pts)
    return base


def _sawhorses_at(xy):
    b = TriangleBatch()
    sc._sawhorses(b, xy)
    return b


def p_zome(app, opaque, transparent, p):
    base = zome_bench(app)
    label(app, base + [0, 0, 0.75], f"1:{F['zome_scale']} MODEL: {F['zome_panels']} PANELS, {F['zome_rows']} ROWS", AMBER)
    label(app, base + [0, 0, 0.55], "FOUR SAME STICKS A PANEL; NO BEVEL", GREEN)


def p_zome_joint(app, opaque, transparent, p):
    shop(app)
    pts = ps.zome_panel_on_jig(1, 0.0)
    w = pm.CONSTANTS["zome_w_in"].value * 0.0254
    depth = pm.CONSTANTS["zome_d_in"].value * 0.0254
    for k, quad in enumerate(ps.pinwheel_sticks(pts, np.array([0, 0, 1.0]), w)):
        ps.prism(opaque, [q + [0, 0, depth] for q in quad], np.array([0, 0, -depth]), ps.PINE)
    r = pm.reference_zome()[0]
    label(app, np.mean(pts, axis=0) + [0, 0, 0.35], f"BOTH ENDS {r.miter_deg:.1f} DEG, PARALLEL", AMBER)
    label(app, np.mean(pts, axis=0) + [0, 0, 0.17], f"OUTSIDE GAP {F['gap_lo']} TO {F['gap_hi']} IN", GREEN)


def p_compare(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app)
    m = cw.landmarks()
    label(app, m.apex + [0, 0, 0.75], f"{F['w_diam']} FT, {F['w_members']} MEMBERS, 2 LENGTHS", AMBER)
    label(app, m.apex + [0, 0, 0.45], "LOGS AND A CHAINSAW", AMBER)
    label(app, ps.centre_top() + [0, 0, 0.7], f"{F['base_ft']} FT, {F['sticks']} STICKS, {F['distinct']} KINDS", CYAN)
    label(app, ps.centre_top() + [0, 0, 0.4], "BOARDS, A TABLE SAW, A MITER SAW", CYAN)


def p_close(app, opaque, transparent, p):
    cw.paint(app)
    panel_dome(app)
    label(app, ps.centre_top() + [0, 0, 0.5], "CHOOSE BY WHAT YOU HAVE", WHITE)


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def ch(number, slug, title, promise, narration, equations):
    return Chapter(slug, f"{number:02}", title, promise, (narration,), tuple(equations),
                   max(8, len(narration.split()) / 2.5 + 1.5), (0, 0, 0), slug)


CHAPTERS = (
    ch(1, "two", "Two ways to frame a dome", "Same hill, two methods.",
       f"On this hill stand two domes framed two different ways. One is the wedge dome: {F['w_members']} members "
       "split from logs with a chainsaw, carrying their angles in their own shape. The other is a three-frequency dome "
       f"of framed panels: {F['panels']} triangles, each one its own small frame of sawn sticks, built flat on a jig, "
       "skinned in the shop, and screwed to its neighbours on site. It is how most small timber domes built from bought "
       "plans are made, and it is worth knowing properly.",
       (f"wedge dome: {F['w_members']} members", f"panel dome: {F['panels']} panels")),
    ch(2, "tried", "A popular build, tried and true", "Shown for comparison.",
       "The three-frequency five-eighths dome built from framed panels is one of the most popular small domes people "
       "build. It is tried and true: a great many of them are standing. That is why it is here, beside the wedge dome, "
       "for comparison. Every length, angle and count in this film is solved by this project's own code, at our own "
       "size, and every picture is drawn by our own software.",
       ("a popular build, tried and true", "geometry, figures and drawings: this project")),
    ch(3, "sphere", "Three frequency", "Three strut lengths, two kinds of point.",
       "Take the icosahedron's twenty faces and cut each into nine smaller triangles, three to an edge, then push every "
       "new point out onto the sphere. That is a three-frequency dome, and it has only three strut lengths. At our size, "
       f"{F['base_ft']} feet across the base, A is {F['a']} inches, B is {F['b']} and C is {F['c']}. Twelve points have "
       "five neighbours and every other point has six. The triangles round the fives make pentagons; the rest make hexagons.",
       (f"A = {F['a']} in", f"B = {F['b']} in", f"C = {F['c']} in")),
    ch(4, "cut", "Five eighths", "Cut below the middle.",
       "This sphere has no level ring of points at its middle, so the usual cut goes lower, to the points nearest "
       f"five-eighths of the way down. What is kept is {F['panels']} triangles: {F['pent']} in pentagons and {F['hex']} "
       f"in hexagons. Its height is {F['fraction']} of its width, a little under the five-eighths of its name. That wall "
       "below the middle is the point of the cut: it stands up nearly straight, so the floor near the edge is floor you "
       "can stand on.",
       (f"panels kept = {F['panels']}", f"height / width = {F['fraction']}")),
    ch(5, "base", "A base that zig-zags", "Some sections taper; some do not.",
       f"The bottom of the cut is {F['base_edges']} edges, and it does not lie on one level. Its corners alternate "
       f"between two heights, {F['taper_mm']} millimetres apart, about {F['taper_in']} inches. So {F['tapered']} of the "
       f"base sections must be tapered, low at one end and high at the other, and {F['level']} sit level. Build the base "
       "ring first, set it on the deck, check its diagonals, and fasten it down. Everything above it goes together "
       "easier when this first ring is right.",
       (f"{F['base_edges']} base edges", f"{F['tapered']} tapered + {F['level']} level", f"rise = {F['taper_mm']} mm")),
    ch(6, "panels", "Two panels, over and over", "A pentagon triangle and a hexagon triangle.",
       f"Every panel in the dome is one of two triangles. The pentagon panel has a {F['pent_base']} inch base and two "
       f"{F['pent_side']} inch sides, and there are {F['pent']} of them. The hexagon panel has the same base and two "
       f"{F['hex_side']} inch sides, and there are {F['hex']}. These outlines are the outside faces of the panels. "
       "Nothing may stick out past them, and nothing may fall short of them.",
       (f"pentagon: {F['pent_base']} / {F['pent_side']} / {F['pent_side']} in  x {F['pent']}",
        f"hexagon: {F['pent_base']} / {F['hex_side']} / {F['hex_side']} in  x {F['hex']}")),
    ch(7, "rip", "Finish, then rip in half", "A cut through the centre makes two copies.",
       "The sticks are sawn lumber. Finish the boards first, while they are whole: the face you rip will be hidden in "
       "the joint. Then tilt the table saw blade to the bevel and rip each board down its middle. A cut through the "
       "centre of a rectangle leaves two pieces that are copies of each other, turned end for end. It is the same "
       "symmetry that makes a split log give identical wedges. Turn the offcut over and send it back through for a "
       "hair more, and the two halves come out exactly alike.",
       (f"stick = {F['stick_w']} x {F['stick_d']} in", f"bevel set at {F['bevel_mid']} deg")),
    ch(8, "jig", "Draw the jig with two arcs", "Three lengths make one triangle.",
       "The jig is a sheet of plywood with the panel drawn on it full size. Snap a straight line for the base and mark "
       "its two ends. A thin stick with a nail at each end is a trammel. Set it to one side length and swing an arc from "
       "one end; set it to the other side and swing from the other end. Where the arcs cross is the third corner. Measure "
       f"all three sides again, then join the points. For the hexagon panel the apex lands {F['hex_height']} inches above "
       "the base.",
       ("two arcs from the base ends", "they cross at the apex", f"hexagon apex height = {F['hex_height']} in")),
    ch(9, "rails", "Rails, and the line", "The jig holds any stick of the right section.",
       "Lay a stick along each side, flat face down and bevel out, with its outer edge splitting the line. Clamp it, butt "
       "a rail against its inside edge, and screw the rail down. Do all three sides. Now any stick pushed against a rail "
       "lands exactly on its line. The jig does not care what size the sticks are, so long as every stick is the same "
       "size and the bevel is right.",
       ("stick edge on the line", "rail behind every stick")),
    ch(10, "pinwheel", "Sticks that turn like a pinwheel", "Equal sides, different sticks.",
       "The three sticks do not meet at a point. Each runs to one corner and butts into the inside face of the next, so "
       "from above the corners turn like a pinwheel. That is why the two equal sides of a panel still take different "
       f"sticks. In a hexagon panel the two C sticks are {F['c1']} and {F['c2']} inches along their outer edges, with "
       f"tail cuts {F['m1']} and {F['m2']} degrees off square. Cut one end, lay the stick in, mark where the next stick "
       "crosses it, and cut that end with the miter and the bevel set together. Clamp a stop block and repeat, and check "
       "the fit every few sticks.",
       (f"C sticks: {F['c1']} in and {F['c2']} in", f"tail cuts: {F['m1']} and {F['m2']} deg",
        f"{F['distinct']} distinct sticks in the dome")),
    ch(11, "bevel", "One bevel cannot be exact", "The number that does not flatter the method.",
       "Here is the number that does not flatter this method. The panels do not all turn by the same angle where they "
       f"meet, so the exact bevel runs from {F['bevel_lo']} degrees to {F['bevel_hi']}. A shop rips every stick at one "
       f"setting, {F['bevel_mid']} degrees, so the worst joint is {F['bevel_err']} degrees off. That is too small to see "
       "and not too small to leak. Lay a bead of sealant or a gasket between the frames as they go together; that is "
       "what takes up the difference.",
       (f"exact: {F['bevel_lo']} to {F['bevel_hi']} deg", f"one setting: {F['bevel_mid']} deg",
        f"worst error: {F['bevel_err']} deg")),
    ch(12, "skin", "Skin it in sections", "One sheet per pentagon or hexagon.",
       "Before raising, screw panels into whole pentagons and hexagons on the shop floor and cover each group with one "
       f"sheet. At this cut {F['sec_pent']} pentagons and {F['sec_hex']} hexagons come out whole, and {F['sec_single']} "
       "panels are skinned one at a time. Pull the film tight across the group and staple it on the bevelled edges, where "
       "the next section hides the staples. A torn section is then one section to replace, not the whole dome.",
       (f"{F['sec_pent']} pentagons + {F['sec_hex']} hexagons", f"{F['sec_single']} single panels")),
    ch(13, "window", "A window is a panel with hinges", "A spare frame on two hinges.",
       "For each window, build one extra frame. Leave the skin off that panel in the dome, cover the spare frame, and "
       "hinge it along its top edge. A small gas strut of the kind kitchen cabinets use holds it open. Weather-strip the "
       "face it closes on so rain running down the dome cannot creep under it, and tape the hinge seam once the dome "
       "is up.",
       ("one spare frame per window", "hinged at the top")),
    ch(14, "raise", "Raise it loose, then tighten", "Flexible until the last panel.",
       "Assemble from the base up, with a helper and plenty of clamps. Put only a few screws in each joint until the "
       "last panel closes the dome: until then the shell flexes, and that flex is what lets the last panels in. Lay a "
       "bead of sealant or a gasket between frames as they meet. Then tape the open seams between sections from the bottom "
       "up, each strip lapping over the one below, so water always runs onto tape and never under it. Do not raise a loose "
       "shell in a wind.",
       ("base up, few screws", "gasket as it goes", "tape bottom up, lapped")),
    ch(15, "deck", "A floor the shape of the base", "Joists to the corners, girders on the five-fold.",
       f"This dome stands on a radial deck that copies its base: {F['deck_sides']} joists from the centre, one to each "
       f"base corner, and a rim board along each base edge, each end cut {F['rim_miter']} degrees off square. Under the "
       f"joists, a ring of {F['girders']} girders follows the dome's own five-fold symmetry, with a post under each girder "
       "joint. Mark the centre, lay the girders out on the ground to place the posts, set the post heights to a level "
       "line, then roll in the joists.",
       (f"{F['deck_sides']} joists, {F['deck_sides']} rim boards", f"rim end cut = 180 / {F['deck_sides']} = {F['rim_miter']} deg",
        f"girder end cut = 180 / {F['girders']} = {F['girder_miter']} deg")),
    ch(16, "anchor", "Hold it down", "Light for its size; wind lifts.",
       "A dome is light for its size, and wind lifts. On a deck like this one, angle brackets tie every base section to "
       "the frame below. On gravel or earth, steel stakes driven at a slant and strapped to the base sections do the same "
       "job. Anchor it before the skin is finished, not after the first storm.",
       ("deck: brackets", "gravel or earth: slanted stakes + straps")),
    ch(17, "zome", "A zome without a bevel", "One stick, one miter, per row.",
       f"The same panel thinking frames a zome. On the bench is a one-to-{F['zome_scale']} model of a nine-sided zome, "
       f"{F['zome_panels']} panels in {F['zome_rows']} rows of {F['zome_per_row']}. Each panel is four identical sticks "
       "in a pinwheel, square through their depth, with a miter at each end and the two ends parallel. Nothing is "
       "bevelled at all: one stick and one miter for every panel in a row.",
       (f"{F['zome_panels']} panels = {F['zome_rows']} rows x {F['zome_per_row']}", "4 identical sticks per panel",
        "no bevels")),
    ch(18, "zome_joint", "The gap that is allowed", "Square edges leave a V outside.",
       "Square-edged panels butted on their inside edges leave a V-shaped gap on the outside. In a two-by-four on edge "
       f"ours opens from {F['gap_lo']} to {F['gap_hi']} inches. On a small zome, screw the inside edges together and let "
       "the roof bridge the gap. On a big one, a wedge block bevelled to half the fold fills it and gives the joint more "
       "to bear on. Fasten loosely at first: the panels hinge, and the angle sets itself as the inside edges line up. "
       "The hub problem of a zome is gone.",
       (f"gap = 2 x depth x tan(fold / 2)", f"= {F['gap_lo']} to {F['gap_hi']} in", "block bevel = fold / 2")),
    ch(19, "compare", "What each method asks of you", "Choose by what you have.",
       f"Side by side: the wedge dome is {F['w_diam']} feet across, with {F['w_members']} members of two lengths cut "
       f"from logs with a chainsaw. The panel dome is {F['base_ft']} feet across, with {F['panels']} panels and "
       f"{F['sticks']} sticks of {F['distinct']} kinds, sawn from bought boards on a table saw and a miter saw, and "
       f"{F['tapered']} tapered base sections. The panel dome is the better-trodden road; many people have built one. "
       "The wedge dome asks for trees, and gives back fewer, bigger pieces. Choose by what you have.",
       (f"wedge: {F['w_members']} members, 2 lengths", f"panels: {F['sticks']} sticks, {F['distinct']} kinds")),
    ch(20, "close", "Two good roads", "Choose by what you have.",
       "Every number in this film came from this project's own solver, and the same numbers are in the book. The "
       "panel dome is a road a great many builders have already walked, and it works. The wedge dome is the other road, "
       "starting from trees instead of boards. Both end in a dome. Choose by what you have.",
       ("figures: panel_method.py", "two methods, one geometry")),
)

SCENES = {
    "two": p_two, "tried": p_tried, "sphere": p_sphere, "cut": p_cut, "base": p_base,
    "panels": p_panels, "rip": p_rip, "jig": p_jig, "rails": p_rails, "pinwheel": p_pinwheel,
    "bevel": p_bevel, "skin": p_skin, "window": p_window, "raise": p_raise, "deck": p_deck,
    "anchor": p_anchor, "zome": p_zome, "zome_joint": p_zome_joint, "compare": p_compare, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves():
    m = cw.landmarks()
    d = ps.dome()
    c = np.array([ps.SITE[0], ps.SITE[1], ps.DECK_TOP + d.height_m * 0.45])
    r = d.cut.base_radius * d.radius_m
    both = (m.dome_centre + c) / 2 + [0, 0, 0.6]
    # From the east the two domes stand side by side rather than one behind the other.
    wide = shots.orbit(both, 8.2, 6.2, -12, 18, 56)
    hero = shots.orbit(c, r * 3.0, 1.6, 70, 28, 44)
    hero_b = shots.orbit(c, r * 3.0, 2.4, 115, -26, 44)
    low = shots.low_hero(c - [0, 0, 0.6], r * 2.6, 0.9, 80, 22, 0.4, 46)
    corner = _base_corner()
    out = normalize(np.array([corner[0] - ps.SITE[0], corner[1] - ps.SITE[1], 0.0]))
    base = shots.push_in(corner + [0, 0, 0.2], corner + out * 2.6 + [0, -0.9, 1.2],
                         corner + out * 1.9 + [0, -0.6, 0.85], 44, 40)
    jig = ps.on_jig(0, 0, 0)
    bench = shots.push_in(jig + [0, 0.05, 0.05], jig + [0.3, -2.3, 1.6], jig + [0.2, -1.8, 1.3], 44, 40)
    top = shots.push_in(jig + [0, 0.05, 0.0], jig + [0.05, -1.0, 2.2], jig + [0.05, -0.8, 1.9], 46, 42)
    # End-on to the board, so the bevel through its centre reads as a line.
    end = jig + [-0.45, 0.05, 0.05]
    rip = shots.push_in(end, end + [-0.75, -0.30, 0.30], end + [-0.48, -0.20, 0.20], 36, 30)
    win_i, win_c, win_n = _window_face()
    wc = np.mean(win_c, axis=0)
    flat = normalize(np.array([win_n[0], win_n[1], 0.0]))
    window = shots.push_in(wc, wc + flat * 3.4 + [0.6, 0, 0.3], wc + flat * 2.6 + [0.4, 0, 0.2], 44, 38)
    deck_c = np.array([ps.SITE[0], ps.SITE[1], ps.DECK_TOP])
    deck = shots.orbit(deck_c, r * 2.4, 1.9, 75, 30, 46)
    zbase = ps.zome_faces()[1]
    zome = shots.push_in(zbase + [0, 0, 0.25], zbase + [0.5, -1.9, 1.15], zbase + [0.35, -1.45, 0.9], 44, 40)
    close = shots.crane_reveal(both, c + [2.0, 7.5, 1.5], both + [3.0, 15.0, 6.5], 44, 50)
    table = {
        "two": wide, "tried": hero, "sphere": hero_b, "cut": low, "base": base, "panels": top, "rip": rip,
        "jig": top, "rails": bench, "pinwheel": top, "bevel": hero, "skin": hero_b, "window": window,
        "raise": hero, "deck": deck, "anchor": base, "zome": zome, "zome_joint": top, "compare": wide,
        "close": close,
    }
    return {name: cabin_stage.clear_view(move, cabin_stage.safe) for name, move in table.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def report() -> str:
    from wedge_book import tokens
    return "\n\n".join(tokens.resolve("{{" + t + "}}") for t in
                       ("pm.constants", "pm.compare", "pm.jig_table", "pm.stick_table", "zm.table"))


def validate_cabin_panel_method() -> None:
    ps.validate_panel_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    # The comparison dome is named only as a popular build: no maker, no source.
    for chapter in CHAPTERS:
        text = " ".join((chapter.title, chapter.promise, *chapter.narration, *chapter.equations)).lower()
        assert "trillium" not in text, chapter.slug
    assert "tried and true" in CHAPTERS[1].narration[0]
    # The film states the number that argues against the method.
    assert F["bevel_err"] in next(c for c in CHAPTERS if c.slug == "bevel").narration[0]
    for chapter in CHAPTERS:
        for p in (0, 0.25, 0.5, 0.75, 1):
            eye, target, fov = MOVES[chapter.slug](p)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target)), chapter.slug
            assert 20 < fov < 70 and eye[2] > 0, chapter.slug
            assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.3, chapter.slug

    class App:
        def __init__(self):
            self.world_labels = []

        def static_layer(self, key, builder, subject_points=None):
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key

    for slug, painter in SCENES.items():
        app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
        painter(app, opaque, transparent, 0.7)
        assert np.all(np.isfinite(opaque.vertices)) and np.all(np.isfinite(transparent.vertices)), slug
        assert app.world_labels, slug
    CABIN_PANEL_METHOD_LESSON.validate()


CABIN_PANEL_METHOD_LESSON = Lesson(
    key="cabin_panel_method", brand="DOMESIM", title="The Panel Method: A Three-Frequency Dome, Framed on a Jig",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_panel_method, report=report,
    snapshot_prefix="cabin_panel_method", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
