"""Rectangular reference buildings for the comparison area.

These are the box-shaped halves of the two like-for-like comparisons that
``al_build.building_comparisons()`` costs:

  * :func:`metal_box`   — bare storage shell: frame + corrugated sheet-metal
    walls/roof over a wood deck. No siding, shingles or trim, so its
    materials match the bare storage dome exactly.
  * :func:`stick_house` — a finished stick-built house: slab, framed and
    sided walls, shingled gable roof, openings, and the turnkey fit-out
    allowance — the conventional counterpart to the finished dome home.

Each builder returns per-layer meshes plus the per-layer cost, so these
buildings get the same inspectable "layers" treatment as the domes and the
site shed. Every dollar comes from the shared rate model in ``al_build`` so
the models and the comparison panel cannot drift apart.
"""

from __future__ import annotations

import math

import numpy as np

import al_build as AL
from al_build import StageDef, add_box
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


# ---------------------------------------------------------------------------
# Bare storage box
# ---------------------------------------------------------------------------

BOX_STAGES = [
    StageDef("deck", "WOOD DECK", "Skids and plywood deck",
             (0.64, 0.48, 0.28)),
    StageDef("frame", "STEEL FRAME", "Corner posts and eave girts",
             (0.52, 0.55, 0.60)),
    StageDef("skin", "METAL WALLS", "Corrugated sheet-metal wall panels",
             (0.63, 0.66, 0.70)),
    StageDef("roof", "METAL ROOF", "Sheet-metal roof panels",
             (0.54, 0.57, 0.62)),
    StageDef("door", "ROLL-UP DOOR", "Single roll-up storage door",
             (0.40, 0.42, 0.46)),
]


def metal_box(w_ft=24.0, l_ft=16.0, h_ft=10.0, wage=None):
    """Per-layer meshes + costs for the bare storage box."""
    B = {s.key: MeshBuilder() for s in BOX_STAGES}
    W, L, H = w_ft * FT, l_ft * FT, h_ft * FT
    steel = (0.46, 0.48, 0.53)
    skin = (0.63, 0.66, 0.70)

    b = B["deck"]
    for sx in (-1, 1):
        add_box(b, (sx * (W * 0.5 - 0.25), 0.0, 0.09), (0.16, L, 0.18),
                (0.46, 0.36, 0.22), mat_id=MAT_WOOD)
    add_box(b, (0.0, 0.0, DECK_TOP - 0.05), (W, L, 0.10),
            (0.66, 0.53, 0.32), mat_id=MAT_WOOD)

    b = B["frame"]
    post = 0.13
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(b, (sx * (W * 0.5 - post * 0.5),
                        sy * (L * 0.5 - post * 0.5), DECK_TOP + H * 0.5),
                    (post, post, H), steel, mat_id=MAT_METAL)
    for sx in (-1, 1):
        add_box(b, (sx * (W * 0.5 - post * 0.5), 0.0, DECK_TOP + H - 0.08),
                (post, L, 0.12), steel, mat_id=MAT_METAL)

    b = B["skin"]
    t = 0.045
    for sx in (-1, 1):
        add_box(b, (sx * W * 0.5, 0.0, DECK_TOP + H * 0.5), (t, L, H),
                skin, mat_id=MAT_METAL)
    for sy in (-1, 1):
        add_box(b, (0.0, sy * L * 0.5, DECK_TOP + H * 0.5), (W, t, H),
                skin, mat_id=MAT_METAL)

    add_box(B["roof"], (0.0, 0.0, DECK_TOP + H + 0.06),
            (W + 0.28, L + 0.28, 0.12), (0.54, 0.57, 0.62), mat_id=MAT_METAL)

    b = B["door"]
    dw, dh = min(2.6, W * 0.55), 2.3
    add_box(b, (0.0, -L * 0.5 - 0.035, DECK_TOP + dh * 0.5), (dw, 0.05, dh),
            (0.38, 0.40, 0.44), mat_id=MAT_METAL)
    for i in range(5):
        add_box(b, (0.0, -L * 0.5 - 0.065,
                    DECK_TOP + 0.22 + i * (dh - 0.3) / 4.0),
                (dw - 0.05, 0.02, 0.05), (0.30, 0.32, 0.35), mat_id=MAT_METAL)

    # costs, straight from the shared rate model
    r = AL.COMPARISON_RATES
    if wage is None:
        wage = AL.ASSUMPTIONS["burdened_wage_per_hour"]
    q = AL.box_shell_quantities(w_ft, l_ft, h_ft)
    wall_sf = 2.0 * (w_ft + l_ft) * h_ft
    roof_sf = w_ft * l_ft

    def cost(mat_per, min_per, qty):
        return qty * (mat_per + min_per / 60.0 * wage)
    costs = {
        "deck": cost(r["floor_mat_per_ft2"], r["floor_min_per_ft2"],
                     q["floor_sf"]),
        "frame": cost(r["frame_mat_per_ft"], r["frame_min_per_ft"],
                      q["framing_lf"]),
        "skin": cost(r["sheet_mat_per_ft2"], r["sheet_min_per_ft2"], wall_sf),
        "roof": cost(r["sheet_mat_per_ft2"], r["sheet_min_per_ft2"], roof_sf),
        "door": 320.0,
    }
    return {"stages": BOX_STAGES,
            "meshes": {k: v.build() for k, v in B.items()},
            "costs": costs}


# ---------------------------------------------------------------------------
# Finished stick-built house
# ---------------------------------------------------------------------------

HOUSE_STAGES = [
    StageDef("slab", "SLAB / FLOOR", "Concrete stem wall and floor",
             (0.62, 0.62, 0.60)),
    StageDef("walls", "FRAMED WALLS", "2x studs, sheathing and siding",
             (0.85, 0.83, 0.75)),
    StageDef("gable", "GABLE ENDS", "Gable in-fill above the top plate",
             (0.82, 0.80, 0.72)),
    StageDef("roof", "SHINGLED ROOF", "Rafters, deck and asphalt shingles",
             (0.29, 0.30, 0.33)),
    StageDef("openings", "DOORS + WINDOWS", "Entry door and glazed openings",
             (0.55, 0.72, 0.82)),
    StageDef("fitout", "TURNKEY FIT-OUT",
             "Kitchen, bath, mech/elec/plumbing and finishes",
             (0.80, 0.62, 0.35)),
]


def stick_house(w_ft=22.2, l_ft=28.8, wall_ft=9.0, peak_ft=12.5, wage=None):
    """Per-layer meshes + costs for the finished stick-built house."""
    B = {s.key: MeshBuilder() for s in HOUSE_STAGES}
    W, L = w_ft * FT, l_ft * FT
    H, PK = wall_ft * FT, peak_ft * FT
    ft = 0.30
    siding = (0.85, 0.83, 0.75)
    trim = (0.95, 0.95, 0.92)

    add_box(B["slab"], (0.0, 0.0, ft * 0.5), (W + 0.30, L + 0.30, ft),
            (0.62, 0.62, 0.60), mat_id=MAT_CONCRETE)

    b = B["walls"]
    t = 0.14
    for sx in (-1, 1):
        add_box(b, (sx * W * 0.5, 0.0, ft + H * 0.5), (t, L, H), siding)
    for sy in (-1, 1):
        add_box(b, (0.0, sy * L * 0.5, ft + H * 0.5), (W, t, H), siding)

    b = B["gable"]
    for sy in (-1, 1):
        y = sy * L * 0.5
        p0 = (-W * 0.5, y, ft + H)
        p1 = (W * 0.5, y, ft + H)
        p2 = (0.0, y, ft + PK)
        if sy < 0:
            b.triangle(p0, p2, p1, siding, normal=(0.0, -1.0, 0.0))
        else:
            b.triangle(p0, p1, p2, siding, normal=(0.0, 1.0, 0.0))

    b = B["roof"]
    over, rise = 0.30, PK - H
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
    add_box(b, (0.0, 0.0, ft + PK + 0.04), (0.16, L + 2 * over, 0.09),
            (0.22, 0.23, 0.26), mat_id=MAT_SHINGLE)

    b = B["openings"]
    dh, dw = 2.05, 0.92
    add_box(b, (0.0, -L * 0.5 - 0.075, ft + dh * 0.5), (dw, 0.06, dh),
            (0.42, 0.28, 0.18), mat_id=MAT_WOOD)
    add_box(b, (0.0, -L * 0.5 - 0.10, ft + dh * 0.5),
            (dw + 0.12, 0.03, dh + 0.10), trim)

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

    # a token interior block so the fit-out layer is visible when toggled
    add_box(B["fitout"], (0.0, L * 0.22, ft + 0.45), (W * 0.55, L * 0.30, 0.9),
            (0.72, 0.58, 0.36), mat_id=MAT_WOOD)

    r = AL.COMPARISON_RATES
    if wage is None:
        wage = AL.ASSUMPTIONS["burdened_wage_per_hour"]
    q = AL.box_shell_quantities(w_ft, l_ft, wall_ft)
    wall_sf = 2.0 * (w_ft + l_ft) * wall_ft
    roof_sf = w_ft * l_ft

    def cost(mat_per, min_per, qty):
        return qty * (mat_per + min_per / 60.0 * wage)
    env_wall = (cost(r["sheathing_mat_per_ft2"], r["sheathing_min_per_ft2"],
                     wall_sf)
                + cost(r["cladding_mat_per_ft2"], r["cladding_min_per_ft2"],
                       wall_sf)
                + cost(r["insulation_mat_per_ft2"],
                       r["insulation_min_per_ft2"], wall_sf)
                + cost(r["drywall_mat_per_ft2"], r["drywall_min_per_ft2"],
                       wall_sf))
    env_roof = (cost(r["sheathing_mat_per_ft2"], r["sheathing_min_per_ft2"],
                     roof_sf)
                + cost(r["cladding_mat_per_ft2"], r["cladding_min_per_ft2"],
                       roof_sf)
                + cost(r["insulation_mat_per_ft2"],
                       r["insulation_min_per_ft2"], roof_sf)
                + cost(r["drywall_mat_per_ft2"], r["drywall_min_per_ft2"],
                       roof_sf))
    framing = cost(r["frame_mat_per_ft"], r["frame_min_per_ft"],
                   q["framing_lf"])
    costs = {
        "slab": cost(r["floor_mat_per_ft2"], r["floor_min_per_ft2"],
                     q["floor_sf"]),
        "walls": framing * 0.72 + env_wall,
        "gable": framing * 0.10,
        "roof": framing * 0.18 + env_roof,
        "openings": 3_400.0,
        "fitout": q["floor_sf"] * r["fitout_per_ft2"],
    }
    return {"stages": HOUSE_STAGES,
            "meshes": {k: v.build() for k, v in B.items()},
            "costs": costs}


def combined(parts):
    """Flatten a per-layer part set into one mesh (for the static lot view)."""
    keys = [s.key for s in parts["stages"]]
    return [parts["meshes"][k] for k in keys]
