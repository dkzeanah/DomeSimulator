"""The exhibits for *The Wedge as a Structural Member*: the blade, the beam,
the column, the box and the dyad, at true proportion, on the Cabin World
platform.

Every solid is extruded from a real sector cross-section, and every
proportion -- the equal-area depths and chords, the sector angles -- is read
from :mod:`two_v_demo.wedge_grammar`, the same engine the book's Part 16 and
its figures use.  Builders return :class:`~two_v_demo.render_kit.TriangleBatch`
es in world metres, standing on the exhibit platform, exactly as
:mod:`two_v_demo.wedge_beyond_scene` does -- whose ``extrude``, ``solid``,
units and colours this module reuses rather than restating.
"""

from __future__ import annotations

import math

import numpy as np

from . import wedge_beyond_scene as ws
from . import wedge_grammar as g
from .render_kit import TriangleBatch

IN = ws.IN
PC = ws.PC
WOOD, WOOD_B, END, BARK = ws.WOOD, ws.WOOD_B, ws.END, ws.BARK
WEB = (0.80, 0.66, 0.30, 1.0)
VOIDCOL = (0.5, 0.57, 0.6, 1.0)


def _sector(radius_in: float, n: int, segments: int = 10) -> list[tuple[float, float]]:
    """One sector's cross-section in metres: apex at the origin, bark arc
    centred on +v, so the member's depth runs along v and its width along u."""
    r = radius_in * IN
    half = math.pi / n
    pts = [(0.0, 0.0)]
    for j in range(segments + 1):
        a = (math.pi / 2 - half) + 2 * half * j / segments
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _side_cols(section) -> list:
    """Bark on the long arc, sawn faces on the two radial sides."""
    return [WOOD_B] + [BARK] * (len(section) - 2) + [WOOD_B]


# ----------------------------------------------------------------------
# The blade: one two-by-four's wood, split four ways, stood on end
# ----------------------------------------------------------------------

# The equal-area blades are at true PROPORTION but displayed larger than life,
# so a sixty-fourth reads as the tall thin blade it is; the comparison is of
# shape, not absolute size, so a uniform scale changes nothing it argues.
FAM_SCALE = 3.0
FAM_GAP_IN = 6.0
FAM_LEN_IN = 14.0


def _fam_layout():
    rows = g.equal_area_families()
    gap = FAM_GAP_IN * IN
    widths = [FAM_SCALE * 2.0 * r.radial_depth_in * math.sin(math.pi / r.splits) * IN
              for r in rows]
    total = sum(widths) + gap * (len(rows) - 1)
    xs, x = [], -total / 2
    for w in widths:
        xs.append(x + w / 2)
        x += w + gap
    return rows, xs


def families(length_in: float = FAM_LEN_IN) -> TriangleBatch:
    """The equal-area W8..W64 sectors, side by side, apex down -- the deeper
    and narrower the blade, the finer the split."""
    b = TriangleBatch()
    rows, xs = _fam_layout()
    for r, x in zip(rows, xs):
        sec = _sector(r.radial_depth_in * FAM_SCALE, r.splits)
        origin = PC + ws._v(x, -length_in * IN / 2, 0.004)
        ws.extrude(b, sec, origin, ws._v(0, 1, 0), ws._v(1, 0, 0), ws._v(0, 0, 1),
                   length_in * IN, WOOD, _side_cols(sec))
    return b


def blade_tops() -> list[np.ndarray]:
    """Where to hang a label over each blade, tallest last."""
    rows, xs = _fam_layout()
    return [PC + ws._v(x, 0.0, r.radial_depth_in * FAM_SCALE * IN + 0.12)
            for r, x in zip(rows, xs)]


# ----------------------------------------------------------------------
# The connection law: a separated-chord beam, two chords and a web
# ----------------------------------------------------------------------

def separated_beam(length_in: float = 30.0, web: bool = True,
                   splits: int = 8, scale: float = 1.7) -> TriangleBatch:
    """Two sector chords, points toward each other, a web between them."""
    b = TriangleBatch()
    stud = ws._v  # alias
    r_in = g.diameter_for_area(g.equal_area_families()[0].area_in2, splits) * 0.5 * scale
    sec = _sector(r_in, splits)
    depth = r_in * IN
    sep = 1.0 * depth                      # clear gap between the two points
    axis, u = ws._v(1, 0, 0), ws._v(0, 1, 0)
    origin = PC + stud(-length_in * IN / 2, 0.0, depth + sep / 2 + 0.01)
    # top chord: bark up (+z), point down toward the web
    ws.extrude(b, sec, origin, axis, u, ws._v(0, 0, -1), length_in * IN, WOOD, _side_cols(sec))
    # bottom chord: mirror, point up toward the web
    origin2 = PC + stud(-length_in * IN / 2, 0.0, 0.01)
    ws.extrude(b, sec, origin2, axis, u, ws._v(0, 0, 1), length_in * IN, WOOD, _side_cols(sec))
    if web:
        hw = 0.18 * depth
        wv = sep / 2
        wsec = [(-hw, -wv), (hw, -wv), (hw, wv), (-hw, wv)]
        worigin = PC + stud(-length_in * IN / 2, 0.0, depth / 2 + sep / 2 + 0.01 + 0.0)
        ws.extrude(b, wsec, worigin, axis, u, ws._v(0, 0, 1), length_in * IN, WEB,
                   [WEB, WEB, WEB, WEB])
    return b


# ----------------------------------------------------------------------
# The dyad: opposite sector, reversed fat-to-thin
# ----------------------------------------------------------------------

def dyad(length_in: float = 40.0, splits: int = 8) -> TriangleBatch:
    """Two tapered wedges, one reversed, so the pair runs parallel."""
    b = TriangleBatch()
    r_fat = g.BUTT_CIRCUMFERENCE_IN / (2 * math.pi)
    r_thin = g.TOP_CIRCUMFERENCE_IN / (2 * math.pi)
    L = length_in * IN
    axis = ws._v(1, 0, 0)

    def taper(origin, fat_left: bool, up: int):
        rl, rr = (r_fat, r_thin) if fat_left else (r_thin, r_fat)
        v = ws._v(0, 0, up)
        a_ring = [origin + ws._v(0, 1, 0) * s[0] + v * s[1] for s in _sector(rl, splits)]
        bo = origin + axis * L
        b_ring = [bo + ws._v(0, 1, 0) * s[0] + v * s[1] for s in _sector(rr, splits)]
        ws.solid(b, a_ring, b_ring, WOOD, None, END)

    base = PC + ws._v(-L / 2, 0.0, 0.01)
    taper(base + ws._v(0, 0, r_fat * IN + 0.02), fat_left=True, up=1)     # top, bark up
    taper(base, fat_left=False, up=1)                                     # bottom mate, reversed
    return b


# ----------------------------------------------------------------------
# The archetypes: beam, hollow column, four-piece box
# ----------------------------------------------------------------------

def _ring_member(b, radius_in, splits, theta, void_in, height_in, base_z,
                 colour=WOOD):
    """One sector standing vertically, apex toward the axis at ``void_in``."""
    sec = _sector(radius_in, splits)
    dirv = np.array([math.cos(theta), math.sin(theta), 0.0])
    tang = np.array([-math.sin(theta), math.cos(theta), 0.0])
    origin = PC + ws._v(0, 0, base_z) + dirv * (void_in * IN)
    ws.extrude(b, sec, origin, ws._v(0, 0, 1), tang, dirv, height_in * IN, colour,
               _side_cols(sec))


def hollow_column(height_in: float = 40.0, splits: int = 8) -> TriangleBatch:
    """Eight sectors in a ring round a void -- a wooden tube."""
    b = TriangleBatch()
    r_in = g.diameter_for_area(g.equal_area_families()[0].area_in2, splits) * 0.5
    void = 0.55 * r_in
    for k in range(8):
        _ring_member(b, r_in, splits, math.tau * k / 8, void, height_in, 0.01)
    return b


def box_member(height_in: float = 40.0, splits: int = 8) -> TriangleBatch:
    """Four sectors round a larger void -- a closed, torsion-stiff member."""
    b = TriangleBatch()
    r_in = g.diameter_for_area(g.equal_area_families()[0].area_in2, splits) * 0.5
    void = 0.9 * r_in
    for k in range(4):
        _ring_member(b, r_in, splits, math.tau * k / 4, void, height_in, 0.01)
    return b


def archetypes() -> tuple[TriangleBatch, list[tuple[np.ndarray, str]]]:
    """Beam, column and box side by side, with where to label each."""
    b = TriangleBatch()
    beam = separated_beam(length_in=30.0)
    col = hollow_column(height_in=34.0)
    box = box_member(height_in=34.0)
    labels: list[tuple[np.ndarray, str]] = []
    for built, (dx, dy), tag, lz in (
            (beam, (-0.95, 0.0), "SEPARATED-CHORD BEAM", 0.55),
            (col, (0.1, 0.0), "HOLLOW COLUMN", 1.05),
            (box, (1.05, 0.0), "FOUR-PIECE BOX", 1.05)):
        b.vertices.extend(ws._place(built, PC + [dx, dy, 0]).vertices)
        labels.append((PC + [dx, dy, lz], tag))
    return b, labels


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_wedge_grammar_scene() -> None:
    g.validate_wedge_grammar()
    for name, builder in (("families", families), ("beam", separated_beam),
                          ("dyad", dyad), ("column", hollow_column),
                          ("box", box_member)):
        batch = builder()
        assert len(batch.vertices) > 0, name
        assert np.all(np.isfinite(batch.vertices)), name
    montage, labels = archetypes()
    assert len(montage.vertices) > 0 and len(labels) == 3
    assert len(blade_tops()) == len(g.equal_area_families())


if __name__ == "__main__":
    validate_wedge_grammar_scene()
    print("wedge_grammar_scene ok")
