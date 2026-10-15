"""Closing the Triangle: pairs of wedges, nested to bowtie, filling a dome panel.

The owner's method, shown rather than told: one wedge end-on; a pair, points facing each
other, sliding along the slant from a solid parallelogram to a bowtie while its reach down
the triangle is measured; a real dome triangle at true size filled course by course from
its top corner, nested and then bowtie, side by side. Then the **whole dome, filled**: every
triangle closed with pairs, cut to its walls and planed flush, nested, slid, bowtie and
dialled; and then **every other way** the Triangle Infill tool knows to fill or cover a
triangle with eighth-log wedges -- rings, parallel, across, chevron and louvers, each in
every lay -- each worn by the whole dome, and all of them side by side as models. The first
count's layout stands beside this one, on camera: which face shows decides the pitch.

Triangle figures are :mod:`two_v_demo.triangle_fill`'s (the book's reference dome); the whole
dome and every pattern are :mod:`two_v_demo.infill_dome`'s, from the tool's own solids.

    py -3.12 -m film stills cabin_triangle_fill
    py -3.12 -m film make cabin_triangle_fill --voice mine --pace 1.5
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import cabin_world as cw
from . import infill_dome as idm
from . import shots
from . import triangle_fill as tf
from . import triangle_fill_scene as ts
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
BLUE = (120, 200, 255)
RED = (255, 140, 120)
GREEN = (111, 235, 155)

F = tf.facts()
BASE, SIDE, _N = tf.dome_faces()[0]
PC = ts.PC
LEFT = PC + np.array([-0.98, 0.0, 0.0])
RIGHT = PC + np.array([0.98, 0.0, 0.0])


def _label(app, point, text: str, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _world(app, fill: str | None = None, show: float = 1.0, subject: bool = False) -> None:
    """The Cabin World with the tool's dome on the deck in place of the world's own: frame
    only, or wearing ``fill`` in the first ``show`` of its triangles (whole panels only)."""
    cw.paint(app, hide=("builder", "dome"), subject=False)
    app.static_layer("fill:platform", cabin_stage.platform)
    steps = len(idm.seats())
    k = int(math.ceil(max(0.0, min(1.0, show)) * steps))
    key = f"idome:{fill or 'frame'}:{k if fill else 0}"
    app.static_layer(key, lambda: idm.dome_batch(fill, show=k / steps),
                     idm.dome_points() if subject else None)


def _dome_label(app, text: str, colour=WHITE, row: int = 0, near_deg: float | None = None) -> None:
    """Above the apex; or, for a close shot from bearing ``near_deg``, on the near shoulder
    of the dome where the camera can see it."""
    o, r = idm.world_origin(), idm.dome_radius_m()
    if near_deg is None:
        at = o + np.array([0.0, 0.0, r + 0.55 + 0.32 * row])
    else:
        a = math.radians(near_deg)
        at = o + np.array([math.cos(a) * r * 0.92, math.sin(a) * r * 0.92, r * 0.50 + 0.22 * row])
    _label(app, at, text, colour)


def _cycle(p: float, items: tuple):
    """Which of ``items`` is on screen at progress ``p``: each gets an equal share."""
    return items[min(len(items) - 1, int(p * len(items)))]


def _grow(p: float) -> float:
    """The dome fills over the first two thirds of the chapter, then holds."""
    return min(1.0, p / 0.66)


def _add(opaque, transparent, pieces) -> None:
    b, air = pieces if isinstance(pieces, tuple) else (pieces, None)
    opaque.vertices.extend(b.vertices)
    if air is not None:
        transparent.vertices.extend(air.vertices)


def _p_of(p: float) -> float:
    """The slide: nested, held, out to a bowtie, held."""
    if p < 0.15:
        return 1.0
    if p > 0.80:
        return 0.0
    return 1.0 - (p - 0.15) / 0.65


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    _world(app, None, subject=True)
    _dome_label(app, f"{len(idm.seats())} OPEN TRIANGLES. THE FRAME IS DONE.", AMBER)


def p_wedge(app, opaque, transparent, p):
    _world(app)
    _add(opaque, transparent, ts.wedge_close())
    c = ts.close_points(1.0)
    _label(app, c["top"] + np.array([0, 0.4, 0.06]), f"FACE {F['face_in']:.2f} IN", AMBER)
    _label(app, c["side"] + np.array([0, 0.1, 0]), f"DEPTH {F['depth_in']:.2f} IN", BLUE)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "ONE WEDGE, END ON (3x LIFE SIZE)", WHITE)


def p_pair(app, opaque, transparent, p):
    _world(app)
    _add(opaque, transparent, ts.pair_close(1.0))
    c = ts.close_points(1.0)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "A PAIR, POINTS FACING EACH OTHER", AMBER)
    _label(app, c["side"] + np.array([0, 0.25, 0]), f"NESTED: REACHES {F['depth_in']:.2f} IN DOWN", BLUE)


def p_slide(app, opaque, transparent, p):
    _world(app)
    q = _p_of(p)
    _add(opaque, transparent, ts.pair_close(q))
    pr = tf.pair(q)
    c = ts.close_points(q)
    _label(app, c["top"] + np.array([0, -0.4, 0.2]), "SLIDE ONE ALONG THE OTHER'S SLANT", AMBER)
    _label(app, c["side"] + np.array([0, 0.3, 0]),
           f"REACH {pr['span_in']:.1f} IN   WOOD {pr['solid']:.0%}", BLUE)
    if q < 0.02:
        _label(app, c["bottom"] + np.array([0, 0.3, -0.05]), "BOWTIE: TIP TO TIP", RED)


def _fill(app, opaque, transparent, p, show, at, tag):
    b, info = ts.triangle(BASE, SIDE, p, show=show, at=at)
    _add(opaque, transparent, b)
    _label(app, info["label"], f"{tag}: {info['shown']} PAIRS, {info['wedges']} WEDGES, {info['feet']:.0f} FT",
           AMBER if p > 0.5 else BLUE)
    return info


def p_nested(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 1.0, min(1.0, p * 1.35), PC, "NESTED")


def p_bowtie(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 0.0, min(1.0, p * 1.35), PC, "BOWTIE")


def p_side(app, opaque, transparent, p):
    _world(app)
    _fill(app, opaque, transparent, 1.0, 1.0, LEFT, "NESTED")
    _fill(app, opaque, transparent, 0.0, 1.0, RIGHT, "BOWTIE")


def _dome_fill(app, key: str, p: float, colour) -> None:
    _world(app, key, _grow(p), subject=True)
    f = idm.facts(key)
    _dome_label(app, f"{f['title'].upper()}: {f['pieces']:,} PIECES, {f['feet']:,.0f} FT", colour)


def p_dome_nested(app, opaque, transparent, p):
    _dome_fill(app, "pairs-nested", p, AMBER)


def p_dome_slide(app, opaque, transparent, p):
    key = _cycle(p, ("pairs-nested", "pairs-half", "pairs-bowtie"))
    _world(app, key, 1.0, subject=True)
    f = idm.facts(key)
    _dome_label(app, f"{f['title'].upper()}: {f['pieces']:,} PIECES, {f['feet']:,.0f} FT",
                AMBER if key != "pairs-bowtie" else BLUE)


def p_dome_dial(app, opaque, transparent, p):
    _dome_fill(app, "pairs-dial", p, GREEN)


def p_flush(app, opaque, transparent, p):
    _world(app, "pairs-dial", 1.0)
    _dome_label(app, "CUT TO THE WALLS, PLANED FLUSH", AMBER, 1, near_deg=FLUSH_DEG)
    _dome_label(app, f"PLANED OFF: NESTED {idm.planed_off(1.0):.0%}, BOWTIE {idm.planed_off(0.0):.0%}", WHITE,
                0, near_deg=FLUSH_DEG)


def p_dome(app, opaque, transparent, p):
    _world(app, "pairs-bowtie", 1.0)
    m = cw.landmarks()
    n, b = F["nested"], F["bowtie"]
    _label(app, m.apex + np.array([0, 0, 0.95]), f"REFERENCE DOME, NESTED: {n['infill_wedges']} WEDGES, "
                                                  f"{n['infill_ft']:,.0f} FT", AMBER)
    _label(app, m.apex + np.array([0, 0, 0.7]), f"REFERENCE DOME, BOWTIE: {b['infill_wedges']} WEDGES, "
                                                 f"{b['infill_ft']:,.0f} FT", BLUE)


def p_trees(app, opaque, transparent, p):
    _world(app, "pairs-dial", 1.0)
    m = cw.landmarks()
    n, b = F["nested"], F["bowtie"]
    _label(app, m.log_end + np.array([0, 0, 0.85]), f"{b['trees']:.1f} TO {n['trees']:.1f} PINES", AMBER)
    _label(app, m.log_end + np.array([0, 0, 0.6]), "FRAME AND EVERY TRIANGLE", WHITE)


#: the two layouts side by side, end-on: this film's pair, and faces out
PAIR_AT, FACES_AT = np.array([0.0, -0.55, 0.0]), np.array([0.0, 0.55, 0.0])


def p_correction(app, opaque, transparent, p):
    _world(app, "pairs-dial", 1.0)
    _add(opaque, transparent, ts.pair_close(0.0, offset=PAIR_AT))
    _add(opaque, transparent, ts.faces_out_close(2, offset=FACES_AT))
    top = ts.CLOSE + np.array([0.0, 0.0, 0.22])
    bow = tf.pair(0.0)["span_in"]
    _label(app, top + PAIR_AT, f"POINTS DOWN: A PAIR REACHES {bow:.1f} IN", GREEN)
    _label(app, top + FACES_AT, f"FACES OUT: EACH WEDGE COVERS {F['face_in']:.2f} IN", RED)


FLUSH_DEG, LOUVER_DEG = 237.0, 238.0      # the close shots' middle bearings (see the cameras)


def family(mode: str, *arrangements: str) -> tuple[str, ...]:
    return tuple(v.key for v in idm.pattern_variants(mode) if v.arrangement in arrangements)


#: per chapter, the share of its narration spent before the first pattern is named; the
#: patterns then change in step with the words that name them (filled in by _chapters()).
LEADS: dict[str, float] = {}


def _family_painter(slug: str, keys: tuple[str, ...], covered: bool = False, near: float | None = None):
    def paint(app, opaque, transparent, p):
        lead = LEADS.get(slug, 0.0)
        key = _cycle(max(0.0, (p - lead) / max(1e-6, 1.0 - lead)), keys)
        _world(app, key, 1.0, subject=True)
        f = idm.facts(key)
        _dome_label(app, ("COVERED: " if covered else "") + f["title"].upper(), BLUE if covered else AMBER, 1, near_deg=near)
        _dome_label(app, f"{f['pieces']:,} PIECES, {f['feet']:,.0f} FT, {f['solid']:.0%} SOLID", WHITE, near_deg=near)
    return paint


COVER_KEYS = family("cover", "parallel", "across", "chevron", "louvers")
COVER_CHAPTERS = (("cover_parallel", family("cover", "parallel")), ("cover_across", family("cover", "across")),
                  ("cover_chevron", family("cover", "chevron", "louvers")))
assert sum(len(k) for _s, k in COVER_CHAPTERS) == len(COVER_KEYS), "every cover is shown"


GALLERY_KEYS = tuple(v.key for v in idm.PAIRS + idm.pattern_variants("fill"))


def p_gallery(app, opaque, transparent, p):
    _world(app, "pairs-dial", 1.0)
    app.static_layer("idome:gallery", lambda: idm.gallery_batch(GALLERY_KEYS),
                     [idm.gallery_label_point(k, GALLERY_KEYS) for k in (GALLERY_KEYS[0], GALLERY_KEYS[-1])])
    for k in GALLERY_KEYS:
        _label(app, idm.gallery_label_point(k, GALLERY_KEYS), idm.facts(k)["title"].upper(),
               BLUE if k.startswith("pairs") else WHITE)


def p_dial(app, opaque, transparent, p):
    _world(app, "pairs-dial", 1.0, subject=True)
    _dome_label(app, "NESTED AT THE CORNERS, OPEN IN THE MIDDLE", GREEN, 1)
    _dome_label(app, "TEST THE JOINT BEFORE YOU TRUST THE LEAST NUMBER", WHITE)


SCENES = {"open": p_open, "wedge": p_wedge, "pair": p_pair, "slide": p_slide, "nested": p_nested,
          "bowtie": p_bowtie, "side": p_side, "dome_nested": p_dome_nested, "dome_slide": p_dome_slide,
          "dome_dial": p_dome_dial, "flush": p_flush, "dome": p_dome, "trees": p_trees,
          "correction": p_correction,
          **{a: _family_painter(a, family("fill", a)) for a in ("rings", "parallel", "across", "chevron")},
          "louvers": _family_painter("louvers", family("fill", "louvers"), near=LOUVER_DEG),
          **{slug: _family_painter(slug, keys, covered=True) for slug, keys in COVER_CHAPTERS},
          "gallery": p_gallery,
          "dial": p_dial}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    hero = np.array(cw.HERO_EYE)
    dome = m.dome_centre + [0, 0, 0.9]
    close = ts.CLOSE + np.array([0.0, 0.0, -0.25])
    # square on the end grain (the wedges run along x), barely moving, so the section reads
    end_on = lambda r, h, a, s: shots.orbit(close, r, h, 180.0, 4.0, 40)    # the sun behind the camera
    tri = PC + np.array([0.0, 0.0, 0.45])
    o, r = idm.world_origin(), idm.dome_radius_m()
    mid = o + np.array([0.0, 0.0, r * 0.42])
    # the sunlit side of the dome is the 200-300 degree arc; every orbit stays in it
    wide = lambda a0, sweep: shots.orbit(mid, r * 2.7, r * 0.55, a0, sweep, 42)
    near = lambda a0, sweep: shots.orbit(o + np.array([0.0, 0.0, r * 0.55]), r * 1.55, r * 0.15, a0, sweep, 44)
    gal = idm.gallery_slots(GALLERY_KEYS)
    gc = np.mean(list(gal.values()), axis=0)
    t = {
        "open": wide(205, 30),
        "wedge": end_on(1.7, 0.05, 15, 18),
        "pair": end_on(1.8, 0.05, 15, 18),
        "slide": end_on(1.9, 0.05, 10, 10),
        "nested": shots.orbit(tri, 2.6, 1.7, -90, 85, 44),     # front, then round to the side: the profile
        "bowtie": shots.orbit(tri, 2.6, 1.7, -90, 85, 44),
        "side": shots.orbit(tri, 3.4, 2.8, -90, 8, 50),
        "dome_nested": wide(215, 40),
        "dome_slide": wide(250, 20),
        "dome_dial": wide(275, -45),
        "flush": near(228, 18),
        "dome": wide(240, 25),
        "trees": shots.orbit(m.log_end + [0, 0, 0.3], 3.6, 1.2, 170, 40, 46),
        "correction": end_on(4.2, 0.05, 10, 10),            # both layouts, end-on
        "rings": wide(205, 25), "parallel": wide(235, 25), "across": wide(265, 25),
        "chevron": wide(290, -25), "louvers": near(232, 12),
        "cover_parallel": wide(215, 30), "cover_across": wide(250, 25), "cover_chevron": wide(285, -30),
        "gallery": shots.orbit(gc + np.array([0.05, 0.1, 0.0]), 2.6, 4.6, -90, 10, 46),   # outside the filled dome
        "dial": wide(250, 35),
    }
    return {slug: cabin_stage.clear_view(shot, cabin_stage.safe) for slug, shot in t.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=(), least: float = 8.0) -> Chapter:
    seconds = max(least, len(narration.split()) / 2.5 + 2.0)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug, None)


def _chapters() -> tuple[Chapter, ...]:
    f = F
    n, b, h = f["nested"], f["bowtie"], f["half"]
    tn, tb = f["iso_nested"], f["iso_bowtie"]
    dn, dh, db, dd = (idm.facts(k) for k in ("pairs-nested", "pairs-half", "pairs-bowtie", "pairs-dial"))
    lays = ", ".join(idm.LAY_NAMES[x] for x in ("flipflop", "samehand", "shim", "standing", "comb"))

    def _fam(arr):
        return [idm.facts(v.key) for v in idm.pattern_variants("fill") if v.arrangement == arr]

    def _lo(arr):
        return min(_fam(arr), key=lambda f: f["pieces"])

    def _hi(arr):
        return max(_fam(arr), key=lambda f: f["pieces"])

    def rng(arr):
        return f"{_lo(arr)['pieces']:,} to {_hi(arr)['pieces']:,}"

    def _span(keys):
        n = [idm.facts(k)["pieces"] for k in keys]
        return f"{min(n):,} to {max(n):,}"

    def fam(slug: str, mode: str, intro: str):
        """The intro, then each pattern named in the order the dome shows it, with the tool's
        own one-line description of the lay and its count -- so every pattern is on screen
        for as long as it takes to say it. Returns (narration, equations-placeholder)."""
        from infill.patterns import LAYS
        keys = dict(COVER_CHAPTERS).get(slug) or family(mode, slug)
        parts = []
        for k in keys:
            v, fk = idm.by_key(k), idm.facts(k)
            what = LAYS[v.lay][1].split(":")[0].split(",")[0] if v.lay else "slats tilted and lapped"
            name = idm.LAY_NAMES[v.lay].capitalize() if v.lay else "Louvered"
            if v.arrangement == "louvers" and mode == "cover":
                name = "Louvered"
            parts.append(f"{name}: {what}, {fk['pieces']:,} pieces.")
        text = intro + " " + " ".join(parts)
        LEADS[slug] = len(intro.split()) / len(text.split())
        return (text,)

    def _least():
        """The least wood among the fills that close every triangle completely."""
        return min((idm.facts(k) for k in GALLERY_KEYS if idm.facts(k)["left_sqft"] < 0.05), key=lambda f: f["feet"])

    rows = [
        (1, "open", "Closing the triangle", "The same wedges, again.",
         f"The frame is done: three wedges round every one of these {len(idm.seats())} triangles. Now close "
         f"the middles, with the same wedges.",
         [f"{idm.counts()[0]} + {idm.counts()[1]} triangles", f"one triangle: {BASE:.0f} in base, {SIDE:.2f} in sides"]),
        (2, "wedge", "One wedge", "Its face and its depth.",
         f"Here is one wedge, end on, three times life size. Its face is {f['face_in']:.2f} inches wide. From the "
         f"face to the point it is {f['depth_in']:.2f} inches deep. Deeper than it is wide.",
         [f"face = {f['log_in']:.0f} sin 22.5 = {f['face_in']:.2f} in", f"depth = {f['depth_in']:.2f} in"]),
        (3, "pair", "A pair, points in", "Solid.",
         f"Now a pair. Turn the second one over so the points face each other, and lay the slants together. "
         f"That's a solid block, and it reaches one depth down the triangle: {f['depth_in']:.2f} inches. Its faces "
         f"bear on the next pair's, and the slants are what shows.",
         [f"nested: reach {n['pair_span_in']:.2f} in, {n['solid']:.0%} wood"]),
        (4, "slide", "Slide it to a bowtie", "Twice the reach, half the wood.",
         f"Slide one along the other's slant. The pair reaches further down, and opens in the middle. At the end "
         f"only the points touch: a bowtie. It reaches {b['pair_span_in']:.1f} inches, and it's half air.",
         [f"bowtie: reach {b['pair_span_in']:.2f} in, {b['solid']:.0%} wood", "reach = (2 - overlap) x depth"]),
        (5, "nested", "Filled nested", "Top corner down.",
         f"Fill a triangle from its top corner down, nested. Each pair is as long as the triangle is wide where "
         f"it lies. {tn['courses']} pairs close it: {tn['wedges']} wedges, {tn['wedge_ft']:.0f} feet.",
         [f"{tn['courses']} pairs, {tn['wedge_ft']:.0f} ft"]),
        (6, "bowtie", "Filled bowtie", "Fewer pairs.",
         f"The same triangle with bowtie pairs. Each one reaches twice as far, so {tb['courses']} pairs close it: "
         f"{tb['wedges']} wedges, {tb['wedge_ft']:.0f} feet.",
         [f"{tb['courses']} pairs, {tb['wedge_ft']:.0f} ft"]),
        (7, "side", "Side by side", "The same opening.",
         f"Side by side: the same opening, {tn['wedge_ft']:.0f} feet of wedge nested, {tb['wedge_ft']:.0f} as "
         f"bowties.",
         [f"nested {tn['wedge_ft']:.0f} ft, bowtie {tb['wedge_ft']:.0f} ft"]),
        (8, "dome_nested", "The whole dome, nested", "Every triangle, closed.",
         f"Now every triangle. Nested pairs, laid from each top corner down, every wedge cut to the walls and "
         f"planed flush with the frame. {dn['pieces']:,} pieces, {dn['feet']:,.0f} feet.",
         [f"the Triangle Infill tool's dome: {2 * idm.radius_in() / 12:.1f} ft across",
          f"{dn['pieces']:,} pieces, {dn['feet']:,.0f} ft"], 10.0),
        (9, "dome_slide", "Slide them all", "Nested, half, bowtie.",
         f"Slide every pair at once. Nested, {dn['pieces']:,} pieces. Half slid, {dh['pieces']:,}. "
         f"Bowtie, {db['pieces']:,}, and {db['feet']:,.0f} feet.",
         [f"nested {dn['feet']:,.0f} ft", f"half {dh['feet']:,.0f} ft", f"bowtie {db['feet']:,.0f} ft"], 10.0),
        (10, "dome_dial", "Dial it in each triangle", "Solid at the corners.",
         f"Or dial it inside every triangle: nested at the top corner and along the base, where the frame "
         f"carries its load, opening to bowties through the middle. {dd['pieces']:,} pieces, "
         f"{dd['feet']:,.0f} feet.",
         [f"{dd['pieces']:,} pieces, {dd['feet']:,.0f} ft"], 10.0),
        (11, "flush", "Cut flush", "No stubs, no gaps.",
         f"Close in. Every pair ends on the opening's wall in the frame's own compound cut, and both faces "
         f"are planed flush with the frame. Planing takes {idm.planed_off(1.0):.0%} off a nested pair, "
         f"{idm.planed_off(0.5):.0%} off a half slid one, and {idm.planed_off(0.0):.0%} off a bowtie.",
         [f"frame {idm.spec().thickness_in:.2f} in thick", f"planed off: nested {idm.planed_off(1.0):.0%}, "
          f"bowtie {idm.planed_off(0.0):.0%}"]),
        (12, "dome", "The book's count", "The reference dome.",
         f"The book counts its reference dome, seventy two inch chords, laid the same way. Nested: {n['infill_wedges']} wedges, "
         f"{n['infill_ft']:,.0f} feet. Bowtie: {b['infill_wedges']} wedges, {b['infill_ft']:,.0f} feet.",
         [f"half way: {h['infill_ft']:,.0f} ft"]),
        (13, "trees", "In trees", "Frame and all.",
         f"With the frame, the whole dome is {b['total_ft']:,.0f} to {n['total_ft']:,.0f} feet of wedge: "
         f"{b['trees']:.1f} to {n['trees']:.1f} sixty foot pines of a foot across.",
         [f"{b['total_ft']:,.0f} to {n['total_ft']:,.0f} ft", f"frame: {n['members']} blanks of {n['blank_in']:.0f} in"]),
        (14, "correction", "Two layouts, two counts", "Which face shows.",
         f"The first count divided the open area by the wedge's face width. That fits a different layout: faces "
         f"out, points in, each wedge covering its own face. With the points facing each other down the "
         f"triangle, the reach sets the pitch. Laid pair by pair that way, nested is {n['infill_ft']:,.0f} feet "
         f"against the first count's {f['first_max_ft']:,.0f}, and bowtie {b['infill_ft']:,.0f} against "
         f"{f['first_min_ft']:,.0f}. Both are ideal counts, before kerf and offcuts.",
         [f"faces out (first count): {f['first_min_ft']:,.0f} to {f['first_max_ft']:,.0f} ft",
          f"points down, laid: {b['infill_ft']:,.0f} to {n['infill_ft']:,.0f} ft"]),
        (15, "rings", "Rings", "The frame, repeated inward.",
         *fam("rings", "fill", "That is one family. The Triangle Infill tool knows others, and the dome wears every one. "
              "Rings: the frame repeated inward, ring by ring."),
         [f"{_lo('rings')['title']}: {_lo('rings')['pieces']:,}", f"{_hi('rings')['title']}: {_hi('rings')['pieces']:,}"]),
        (16, "parallel", "Parallel", "Along one edge.",
         *fam("parallel", "fill", "Parallel: runs along one edge, stepping across, every run ending in a compound cut on the walls."),
         [f"{_lo('parallel')['title']}: {_lo('parallel')['feet']:,.0f} ft", f"{_hi('parallel')['title']}: {_hi('parallel')['feet']:,.0f} ft"]),
        (17, "across", "Across", "Square to an edge.",
         *fam("across", "fill", "Across: runs square to one edge, stepping along it. Short pieces, many of them."),
         [f"{_lo('across')['title']}: {_lo('across')['feet']:,.0f} ft", f"{_hi('across')['title']}: {_hi('across')['feet']:,.0f} ft"]),
        (18, "chevron", "Chevron", "Two sides, one centre line.",
         *fam("chevron", "fill", "Chevron: runs along the two sides, meeting on the centre line."),
         [f"{_lo('chevron')['title']}: {_lo('chevron')['feet']:,.0f} ft", f"{_hi('chevron')['title']}: {_hi('chevron')['feet']:,.0f} ft"]),
        (19, "louvers", "Louvers", "Covered, but open to air.",
         f"Louvers: slats tilted and lapped. Covered from above, open to the air: a dome that breathes. "
         f"{_lo('louvers')['pieces']:,} pieces, {_lo('louvers')['feet']:,.0f} feet.",
         [f"{_lo('louvers')['pieces']:,} pieces"]),
        (20, "cover_parallel", "Or cover it", "Over the frame, not in it.",
         *fam("cover_parallel", "cover", f"Or leave the frame open and cover it, laid over the outside and bevelled to meet "
              f"the next panel across each seam. {len(COVER_KEYS)} ways. First, parallel."),
         [f"{len(COVER_KEYS)} covers", f"{_span(COVER_KEYS)} pieces"]),
        (21, "cover_across", "Covered, across", "Square to an edge, over the frame.",
         *fam("cover_across", "cover", "Covered across."),
         [f"{_span(dict(COVER_CHAPTERS)['cover_across'])} pieces"]),
        (22, "cover_chevron", "Covered, chevron", "And the louvered cover.",
         *fam("cover_chevron", "cover", "Covered chevron, and last, the louvered cover."),
         [f"{_span(dict(COVER_CHAPTERS)['cover_chevron'])} pieces"]),
        (23, "gallery", "Every fill, side by side", "Quarter scale.",
         f"Every fill, side by side at quarter scale: {len(idm.PAIRS)} with pairs, "
         f"{len(GALLERY_KEYS) - len(idm.PAIRS)} with the tool's patterns. Nothing shows through any of them. "
         f"The least wood that closes every triangle completely is {_least()['title']}: {_least()['feet']:,.0f} "
         f"feet, {_least()['solid']:.0%} solid. Rings leave a plug to cut at each centre.",
         [f"{len(GALLERY_KEYS)} fills", f"least: {_least()['title']}, {_least()['feet']:,.0f} ft"], 12.0),
        (24, "dial", "The dial", "Solid or air.",
         "The overlap is a dial. Nest them tight at the corners, where the loads gather. Open them in the middle, "
         "where a cavity holds insulation. A bowtie touching at its points alone doesn't keep the weather out, so "
         "test the joint before you trust the least number.",
         ["nested at the corners, open in the middle"]),
    ]
    return tuple(_ch(*r) for r in rows)


CHAPTERS = _chapters()


def validate_triangle_fill_film() -> None:
    ts.validate_triangle_fill_scene()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    for ch in CHAPTERS:
        text = " ".join(ch.narration)
        assert "{" not in text and "}" not in text, ch.slug
        for q in (0.0, 0.5, 1.0):
            eye, target, fov = MOVES[ch.slug](q)
            eye = np.asarray(eye, float)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0.25, (ch.slug, q)
            m = cw.landmarks()
            # the filled dome on the deck is the infill tool's, wider than the world's own
            r = max(m.dome_r, idm.dome_radius_m())
            assert np.linalg.norm(eye - m.dome_centre) > r * 1.05, (ch.slug, q, "inside the dome's shell")

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
        for q in (0.1, 0.5, 0.95):
            app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
            app.built = built
            painter(app, opaque, transparent, q)
            assert np.all(np.isfinite(opaque.vertices)), slug


def report() -> str:
    return "\n".join(f"{c.number} {c.title}: {' '.join(c.narration)}" for c in CHAPTERS)


TRIANGLE_FILL_LESSON = Lesson(
    key="cabin_triangle_fill", brand="DOMESIM", title="Closing the Triangle",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_triangle_fill_film, report=report,
    snapshot_prefix="cabin_triangle_fill", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
