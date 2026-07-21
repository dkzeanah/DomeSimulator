"""Rectangular reference buildings for the comparison area.

These are the box-shaped halves of the two like-for-like comparisons that
``al_build.building_comparisons()`` costs:

  * :func:`build_metal_box`   — bare storage shell: frame + corrugated
    sheet-metal walls/roof over a wood deck. No siding, shingles or trim,
    so its materials match the bare storage dome exactly.
  * :func:`build_stick_house` — a finished stick-built house: slab, sided
    walls, gable roof with shingles, door and windows — the conventional
    counterpart to the finished dome home.

Geometry only; every dollar comes from the shared rate model in
``al_build`` so the models and the comparison panel cannot drift apart.
"""

from __future__ import annotations

import math

import numpy as np

from al_build import add_box
from materials import (
    MAT_CONCRETE,
    MAT_GLASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_SHINGLE,
    MAT_WOOD,
)
from mesh_builder import MeshBuilder

FT = 0.3048
DECK_TOP = 0.35


def build_metal_box(w_ft=24.0, l_ft=16.0, h_ft=10.0):
    """Bare storage box: wood deck, steel frame, corrugated metal skin."""
    b = MeshBuilder()
    W, L, H = w_ft * FT, l_ft * FT, h_ft * FT
    steel = (0.46, 0.48, 0.53)
    skin = (0.63, 0.66, 0.70)

    # skids + wood deck
    for sx in (-1, 1):
        add_box(b, (sx * (W * 0.5 - 0.25), 0.0, 0.09),
                (0.16, L, 0.18), (0.46, 0.36, 0.22), mat_id=MAT_WOOD)
    add_box(b, (0.0, 0.0, DECK_TOP - 0.05), (W, L, 0.10),
            (0.66, 0.53, 0.32), mat_id=MAT_WOOD)

    # corner posts and eave girts (the frame)
    post = 0.13
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(b, (sx * (W * 0.5 - post * 0.5),
                        sy * (L * 0.5 - post * 0.5), DECK_TOP + H * 0.5),
                    (post, post, H), steel, mat_id=MAT_METAL)
    for sx in (-1, 1):
        add_box(b, (sx * (W * 0.5 - post * 0.5), 0.0, DECK_TOP + H - 0.08),
                (post, L, 0.12), steel, mat_id=MAT_METAL)

    # corrugated skin (ribbed metal material gives it the profile)
    t = 0.045
    for sx in (-1, 1):
        add_box(b, (sx * W * 0.5, 0.0, DECK_TOP + H * 0.5),
                (t, L, H), skin, mat_id=MAT_METAL)
    for sy in (-1, 1):
        add_box(b, (0.0, sy * L * 0.5, DECK_TOP + H * 0.5),
                (W, t, H), skin, mat_id=MAT_METAL)
    # shallow metal roof with a small overhang
    add_box(b, (0.0, 0.0, DECK_TOP + H + 0.06),
            (W + 0.28, L + 0.28, 0.12), (0.54, 0.57, 0.62), mat_id=MAT_METAL)

    # roll-up door on the front (-Y) wall
    dw, dh = min(2.6, W * 0.55), 2.3
    add_box(b, (0.0, -L * 0.5 - 0.035, DECK_TOP + dh * 0.5),
            (dw, 0.05, dh), (0.38, 0.40, 0.44), mat_id=MAT_METAL)
    for i in range(5):
        add_box(b, (0.0, -L * 0.5 - 0.065,
                    DECK_TOP + 0.22 + i * (dh - 0.3) / 4.0),
                (dw - 0.05, 0.02, 0.05), (0.30, 0.32, 0.35),
                mat_id=MAT_METAL)
    return b.build()


def build_stick_house(w_ft=22.2, l_ft=28.8, wall_ft=9.0, peak_ft=12.5):
    """A finished stick-built house: slab, sided walls, shingled gable
    roof, entry door and windows."""
    b = MeshBuilder()
    W, L = w_ft * FT, l_ft * FT
    H, PK = wall_ft * FT, peak_ft * FT
    ft = 0.30
    siding = (0.85, 0.83, 0.75)
    trim = (0.95, 0.95, 0.92)

    # slab / stem wall
    add_box(b, (0.0, 0.0, ft * 0.5), (W + 0.30, L + 0.30, ft),
            (0.62, 0.62, 0.60), mat_id=MAT_CONCRETE)

    # walls
    t = 0.14
    for sx in (-1, 1):
        add_box(b, (sx * W * 0.5, 0.0, ft + H * 0.5), (t, L, H), siding)
    for sy in (-1, 1):
        add_box(b, (0.0, sy * L * 0.5, ft + H * 0.5), (W, t, H), siding)

    # gable in-fill at both ends
    for sy in (-1, 1):
        y = sy * L * 0.5
        p0 = (-W * 0.5, y, ft + H)
        p1 = (W * 0.5, y, ft + H)
        p2 = (0.0, y, ft + PK)
        if sy < 0:
            b.triangle(p0, p2, p1, siding, normal=(0.0, -1.0, 0.0))
        else:
            b.triangle(p0, p1, p2, siding, normal=(0.0, 1.0, 0.0))

    # shingled roof planes with overhang
    over = 0.30
    rise = PK - H
    for side in (-1, 1):
        xe = side * (W * 0.5 + over)
        y0, y1 = -L * 0.5 - over, L * 0.5 + over
        ez, pz = ft + H, ft + PK
        n = np.array([side * rise, 0.0, W * 0.5])
        n = n / float(np.linalg.norm(n))
        if side < 0:
            pts = [(xe, y0, ez), (0.0, y0, pz), (0.0, y1, pz), (xe, y1, ez)]
        else:
            pts = [(0.0, y0, pz), (xe, y0, ez), (xe, y1, ez), (0.0, y1, pz)]
        b.quad(*pts, n, (0.29, 0.30, 0.33), 1.0, MAT_SHINGLE)
    # ridge cap
    add_box(b, (0.0, 0.0, ft + PK + 0.04), (0.16, L + 2 * over, 0.09),
            (0.22, 0.23, 0.26), mat_id=MAT_SHINGLE)

    # entry door on the front (-Y) wall
    dh, dw = 2.05, 0.92
    add_box(b, (0.0, -L * 0.5 - 0.075, ft + dh * 0.5), (dw, 0.06, dh),
            (0.42, 0.28, 0.18), mat_id=MAT_WOOD)
    add_box(b, (0.0, -L * 0.5 - 0.10, ft + dh * 0.5),
            (dw + 0.12, 0.03, dh + 0.10), trim)
    b.sphere((0.30, -L * 0.5 - 0.13, ft + 1.05), 0.05, (0.80, 0.72, 0.35),
             rings=4, sides=8)

    # windows: two per long wall, one per gable end
    def window(cx, cy, cz, ww, wh, axis):
        if axis == "x":
            add_box(b, (cx, cy, cz), (0.05, ww + 0.14, wh + 0.14), trim)
            add_box(b, (cx, cy, cz), (0.03, ww, wh), (0.55, 0.72, 0.82),
                    alpha=0.55, mat_id=MAT_GLASS)
        else:
            add_box(b, (cx, cy, cz), (ww + 0.14, 0.05, wh + 0.14), trim)
            add_box(b, (cx, cy, cz), (ww, 0.03, wh), (0.55, 0.72, 0.82),
                    alpha=0.55, mat_id=MAT_GLASS)
    for sx in (-1, 1):
        for sy in (-0.28, 0.28):
            window(sx * (W * 0.5 + 0.03), sy * L, ft + 1.55, 1.05, 1.15, "x")
    window(-W * 0.22, -L * 0.5 - 0.05, ft + 1.55, 0.95, 1.15, "y")
    window(W * 0.22, L * 0.5 + 0.05, ft + 1.55, 0.95, 1.15, "y")
    return b.build()
