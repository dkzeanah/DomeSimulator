"""Conventional site-built comparison shed for the assembly-line yard.

The shed is intentionally independent of the manufactured-dome catalog and
production line.  It is a fixed, inspectable benchmark built with a common
light-frame sequence: leveled pad, precast deck blocks, pressure-treated
skids/floor, 2x4 stud walls, site-built gable rafters, structural T1-11
siding, and asphalt roofing.

Dimensions and costs are planning assumptions, not permit drawings or a bid.
They live here so the visual model and the comparison panel cannot drift apart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from al_build import StageDef, add_box
from materials import (
    MAT_CONCRETE,
    MAT_EMISSIVE,
    MAT_GLASS,
    MAT_GRAVEL,
    MAT_METAL,
    MAT_PLAIN,
    MAT_SHEETING,
    MAT_SHINGLE,
    MAT_WOOD,
)
from mesh_builder import MeshBuilder


FT = 0.3048

# Requested outside dimensions: 24 ft long x 16 ft wide x 10 ft peak.
LENGTH_FT = 24.0
WIDTH_FT = 16.0
PEAK_HEIGHT_FT = 10.0
EAVE_HEIGHT_FT = 8.0
ROOF_RISE_FT = PEAK_HEIGHT_FT - EAVE_HEIGHT_FT
ROOF_PITCH = "3:12"

LENGTH = LENGTH_FT * FT
WIDTH = WIDTH_FT * FT
PEAK_HEIGHT = PEAK_HEIGHT_FT * FT
EAVE_HEIGHT = EAVE_HEIGHT_FT * FT
ROOF_RISE = ROOF_RISE_FT * FT
FLOOR_TOP = 0.50
# Backward-compatible internal name used by the skin helpers below.
SLAB_TOP = FLOOR_TOP


@dataclass(frozen=True)
class CostItem:
    key: str
    label: str
    material: float
    labor_hours: float


# Bare-minimum, owner-assisted planning inputs in 2026 dollars.  This is a
# simple storage shell on blocks—not a slab, utility building, or finished
# accessory structure.  The complete quoted model is intentionally <$10k.
COST_ITEMS = (
    CostItem("sitework", "Leveling and compacted gravel strips", 250.0, 4.0),
    CostItem("blocks", "15 precast deck blocks", 450.0, 6.0),
    CostItem("floor", "PT skids, 2x6 joists and plywood floor", 1_100.0, 14.0),
    CostItem("framing", "2x4 walls @ 16-in o.c. + fasteners", 1_200.0, 18.0),
    CostItem("trusses", "Site-built 3:12 rafters and ties", 700.0, 10.0),
    CostItem("siding", "Structural T1-11 wall panels", 800.0, 10.0),
    CostItem("roofing", "OSB, felt and economy shingles", 650.0, 8.0),
    CostItem("openings", "Site-built double plywood doors", 300.0, 4.0),
    CostItem("finish", "Corner trim, paint and misc. hardware", 350.0, 4.0),
    CostItem("permits", "Delivery / local allowance", 250.0, 0.0),
)

# Owner-assisted/basic shed crew allowance; this is deliberately not the
# fully burdened commercial trade rate used by the dome factory comparison.
BURDENED_LABOR_RATE = 25.0
BUILDER_OVERHEAD_RATE = 0.05
CONTINGENCY_RATE = 0.04
TARGET_GROSS_MARGIN = 0.10
FIELD_CREW = 2
WORKDAY_HOURS = 8.0


SHED_STAGES = [
    StageDef("sitework", "SITE + GRAVEL", "Leveled gravel bearing strips",
             (0.48, 0.43, 0.32)),
    StageDef("blocks", "DECK BLOCKS", "Fifteen precast concrete deck blocks",
             (0.58, 0.59, 0.58)),
    StageDef("floor", "FLOOR PLATFORM", "PT skids, 2x6 joists and plywood",
             (0.64, 0.46, 0.25)),
    StageDef("framing", "WALL FRAMING", "2x4 studs at 16 inches on center",
             (0.72, 0.54, 0.30)),
    StageDef("trusses", "ROOF FRAMING", "Site-built rafters and collar ties",
             (0.80, 0.60, 0.32)),
    StageDef("siding", "T1-11 SIDING", "Structural sheet siding; no wall wrap",
             (0.36, 0.53, 0.62)),
    StageDef("roofing", "ECONOMY ROOF", "OSB, felt, shingles and ridge cap",
             (0.20, 0.23, 0.27)),
    StageDef("openings", "DOUBLE DOORS", "Site-built plywood storage doors",
             (0.70, 0.72, 0.74)),
    StageDef("finish", "BASIC TRIM", "Corner boards, fascia and simple paint",
             (0.88, 0.87, 0.82)),
]


def cost_item(key: str) -> CostItem:
    return next(item for item in COST_ITEMS if item.key == key)


def shed_economics() -> dict:
    material = sum(item.material for item in COST_ITEMS)
    labor_hours = sum(item.labor_hours for item in COST_ITEMS)
    labor_cost = labor_hours * BURDENED_LABOR_RATE
    direct = material + labor_cost
    overhead = direct * BUILDER_OVERHEAD_RATE
    contingency = direct * CONTINGENCY_RATE
    total_cost = direct + overhead + contingency
    price = total_cost / (1.0 - TARGET_GROSS_MARGIN)
    margin = price - total_cost
    floor_sqft = WIDTH_FT * LENGTH_FT
    roof_slope_ft = math.hypot(WIDTH_FT / 2.0, ROOF_RISE_FT)
    return {
        "material": material,
        "labor_hours": labor_hours,
        "labor_cost": labor_cost,
        "overhead": overhead,
        "contingency": contingency,
        "total_cost": total_cost,
        "price": price,
        "margin": margin,
        "margin_pct": TARGET_GROSS_MARGIN * 100.0,
        "floor_sqft": floor_sqft,
        "floor_area": floor_sqft / 10.7639104167,
        "volume_cuft": (floor_sqft * EAVE_HEIGHT_FT
                         + 0.5 * WIDTH_FT * ROOF_RISE_FT * LENGTH_FT),
        "wall_sqft": (2 * LENGTH_FT * EAVE_HEIGHT_FT
                       + 2 * WIDTH_FT * EAVE_HEIGHT_FT
                       + WIDTH_FT * ROOF_RISE_FT),
        "roof_sqft": 2 * roof_slope_ft * LENGTH_FT,
        "build_days": labor_hours / (FIELD_CREW * WORKDAY_HOURS),
    }


def shed_record() -> dict:
    econ = shed_economics()
    return {
        "serial": "SITE",
        "name": "24x16 Gable Shed",
        "structure": "conventional_shed",
        "dtype": "conventional_shed",
        "width_ft": WIDTH_FT,
        "length_ft": LENGTH_FT,
        "height_ft": PEAK_HEIGHT_FT,
        "eave_height_ft": EAVE_HEIGHT_FT,
        "roof_pitch": ROOF_PITCH,
        "framing": "PT skids + 2x6 floor; 2x4 walls @ 16-in o.c.",
        "foundation": "15 precast deck blocks on compacted gravel",
        "cladding": "T1-11 structural siding + economy shingles",
        "created": "Site-built benchmark (2026 planning estimate)",
        "sold": 0,
        "monthly": 0.0,
        "solar_kw": 0.0,
        "r_value": 0.0,
        "steps": 0,
        "distance_m": 0.0,
        **econ,
    }


def _beam(b: MeshBuilder, start, end, depth, color, mat_id=MAT_WOOD):
    """Rectangular timber/steel member between arbitrary 3D endpoints."""
    start = np.asarray(start, dtype=np.float64)
    end = np.asarray(end, dtype=np.float64)
    axis = end - start
    axis /= max(1e-9, float(np.linalg.norm(axis)))
    helper = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(axis, helper))) > 0.92:
        helper = np.array([0.0, 1.0, 0.0])
    u = np.cross(axis, helper)
    u /= max(1e-9, float(np.linalg.norm(u)))
    v = np.cross(axis, u)
    v /= max(1e-9, float(np.linalg.norm(v)))
    h = depth * 0.5
    b.prism(start, end, [(-h, -h), (h, -h), (h, h), (-h, h)],
            u, v, color, mat_id=mat_id)


def _roof_plane(b: MeshBuilder, side: int, z_offset: float, color,
                alpha=1.0, mat_id=MAT_PLAIN, overhang=0.24):
    x_eave = side * (WIDTH * 0.5 + overhang)
    y0, y1 = -LENGTH * 0.5 - overhang, LENGTH * 0.5 + overhang
    eave_z = SLAB_TOP + EAVE_HEIGHT + z_offset
    peak_z = SLAB_TOP + PEAK_HEIGHT + z_offset
    ridge_x = 0.0
    if side < 0:
        pts = [(x_eave, y0, eave_z), (ridge_x, y0, peak_z),
               (ridge_x, y1, peak_z), (x_eave, y1, eave_z)]
        normal = (-ROOF_RISE, 0.0, WIDTH * 0.5)
    else:
        pts = [(ridge_x, y0, peak_z), (x_eave, y0, eave_z),
               (x_eave, y1, eave_z), (ridge_x, y1, peak_z)]
        normal = (ROOF_RISE, 0.0, WIDTH * 0.5)
    n = np.asarray(normal, dtype=np.float64)
    n /= float(np.linalg.norm(n))
    b.quad(*pts, n, color, alpha, mat_id)


def _wall_skin(b: MeshBuilder, color, offset=0.0, alpha=1.0,
               mat_id=MAT_PLAIN, cut_front_door=False):
    thick = 0.025
    zc = SLAB_TOP + EAVE_HEIGHT * 0.5
    # Long side walls.
    for sx in (-1, 1):
        add_box(b, (sx * (WIDTH * 0.5 + offset), 0.0, zc),
                (thick, LENGTH, EAVE_HEIGHT), color, alpha, mat_id)
    # Rear end wall.
    add_box(b, (0.0, LENGTH * 0.5 + offset, zc),
            (WIDTH, thick, EAVE_HEIGHT), color, alpha, mat_id)
    # Front end wall around the simple 6-ft double-door opening.
    door_w, door_h = 6.0 * FT, 6.67 * FT
    if cut_front_door:
        side_w = (WIDTH - door_w) * 0.5
        for sx in (-1, 1):
            add_box(b, (sx * (door_w * 0.5 + side_w * 0.5),
                        -LENGTH * 0.5 - offset, zc),
                    (side_w, thick, EAVE_HEIGHT), color, alpha, mat_id)
        add_box(b, (0.0, -LENGTH * 0.5 - offset,
                    SLAB_TOP + door_h + (EAVE_HEIGHT - door_h) * 0.5),
                (door_w, thick, EAVE_HEIGHT - door_h), color, alpha, mat_id)
    else:
        add_box(b, (0.0, -LENGTH * 0.5 - offset, zc),
                (WIDTH, thick, EAVE_HEIGHT), color, alpha, mat_id)
    # Triangular gable infill at each end.
    for sy in (-1, 1):
        y = sy * (LENGTH * 0.5 + offset + thick * 0.51)
        p0 = (-WIDTH * 0.5, y, SLAB_TOP + EAVE_HEIGHT)
        p1 = (WIDTH * 0.5, y, SLAB_TOP + EAVE_HEIGHT)
        p2 = (0.0, y, SLAB_TOP + PEAK_HEIGHT)
        if sy < 0:
            b.triangle(p0, p2, p1, color, alpha, mat_id,
                       normal=(0.0, -1.0, 0.0))
        else:
            b.triangle(p0, p1, p2, color, alpha, mat_id,
                       normal=(0.0, 1.0, 0.0))


def build_shed_layers() -> dict[str, object]:
    """Return one mesh per inspection layer, in ``SHED_STAGES`` order."""
    builders = {stage.key: MeshBuilder() for stage in SHED_STAGES}

    # Minimal bearing: gravel strips and fifteen independent deck blocks.
    b = builders["sitework"]
    skid_x = (-WIDTH * 0.5 + 0.48, 0.0, WIDTH * 0.5 - 0.48)
    block_y = np.linspace(-LENGTH * 0.5 + 0.48,
                          LENGTH * 0.5 - 0.48, 5)
    for x in skid_x:
        add_box(b, (x, 0.0, 0.035), (0.62, LENGTH + 0.35, 0.07),
                (0.43, 0.39, 0.31), mat_id=MAT_GRAVEL)
    b = builders["blocks"]
    for x in skid_x:
        for y in block_y:
            add_box(b, (x, float(y), 0.14), (0.46, 0.46, 0.28),
                    (0.56, 0.57, 0.56), mat_id=MAT_CONCRETE)

    # Pressure-treated skids, 2x6 joists, and a single plywood deck.
    b = builders["floor"]
    treated = (0.48, 0.38, 0.22)
    for x in skid_x:
        add_box(b, (x, 0.0, 0.33), (0.14, LENGTH - 0.24, 0.20),
                treated, mat_id=MAT_WOOD)
    for y in np.linspace(-LENGTH * 0.5 + 0.10,
                         LENGTH * 0.5 - 0.10, 19):
        add_box(b, (0.0, float(y), 0.43),
                (WIDTH - 0.18, 0.038, 0.14), treated, mat_id=MAT_WOOD)
    add_box(b, (0.0, 0.0, FLOOR_TOP - 0.018),
            (WIDTH, LENGTH, 0.036), (0.66, 0.52, 0.30), mat_id=MAT_WOOD)

    # Platform-framed walls: 2x4 members at 16 inches on center.
    b = builders["framing"]
    wood = (0.73, 0.54, 0.31)
    stud_w, stud_d = 1.5 / 12.0 * FT, 3.5 / 12.0 * FT
    plate_h = 1.5 / 12.0 * FT
    for sx in (-1, 1):
        x = sx * (WIDTH * 0.5 - stud_d * 0.5)
        for y in np.linspace(-LENGTH * 0.5, LENGTH * 0.5, 19):
            add_box(b, (x, float(y), SLAB_TOP + EAVE_HEIGHT * 0.5),
                    (stud_d, stud_w, EAVE_HEIGHT), wood, mat_id=MAT_WOOD)
        for z in (SLAB_TOP + plate_h * 0.5,
                  SLAB_TOP + EAVE_HEIGHT - plate_h * 1.5,
                  SLAB_TOP + EAVE_HEIGHT - plate_h * 0.5):
            add_box(b, (x, 0.0, z), (stud_d, LENGTH, plate_h), wood,
                    mat_id=MAT_WOOD)
    door_half = 3.0 * FT
    for sy in (-1, 1):
        y = sy * (LENGTH * 0.5 - stud_d * 0.5)
        for x in np.linspace(-WIDTH * 0.5, WIDTH * 0.5, 13):
            if sy < 0 and abs(float(x)) < door_half - 0.08:
                continue
            add_box(b, (float(x), y, SLAB_TOP + EAVE_HEIGHT * 0.5),
                    (stud_w, stud_d, EAVE_HEIGHT), wood, mat_id=MAT_WOOD)
        for z in (SLAB_TOP + plate_h * 0.5,
                  SLAB_TOP + EAVE_HEIGHT - plate_h * 1.5,
                  SLAB_TOP + EAVE_HEIGHT - plate_h * 0.5):
            add_box(b, (0.0, y, z), (WIDTH, stud_d, plate_h), wood,
                    mat_id=MAT_WOOD)
    # Simple double-door king/jack studs and built-up header.
    front_y = -LENGTH * 0.5 + stud_d * 0.5
    for x in (-door_half - stud_w, -door_half, door_half, door_half + stud_w):
        add_box(b, (x, front_y, SLAB_TOP + EAVE_HEIGHT * 0.5),
                (stud_w, stud_d, EAVE_HEIGHT), wood, mat_id=MAT_WOOD)
    add_box(b, (0.0, front_y, SLAB_TOP + 6.67 * FT + 0.12),
            (6.5 * FT, stud_d, 0.24), wood, mat_id=MAT_WOOD)
    # Gable-end studs above the double top plate.
    for sy in (-1, 1):
        y = sy * (LENGTH * 0.5 - stud_d * 0.5)
        for x in np.linspace(-WIDTH * 0.375, WIDTH * 0.375, 7):
            extra = ROOF_RISE * (1.0 - abs(float(x)) / (WIDTH * 0.5))
            add_box(b, (float(x), y,
                        SLAB_TOP + EAVE_HEIGHT + extra * 0.5),
                    (stud_w, stud_d, extra), wood, mat_id=MAT_WOOD)

    # Site-built rafters and ties at 24 inches on center.
    b = builders["trusses"]
    chord_z = SLAB_TOP + EAVE_HEIGHT + 0.06
    ridge_z = SLAB_TOP + PEAK_HEIGHT
    for y in np.linspace(-LENGTH * 0.5, LENGTH * 0.5, 13):
        y = float(y)
        _beam(b, (-WIDTH * 0.5, y, chord_z), (WIDTH * 0.5, y, chord_z),
              0.060, wood)
        _beam(b, (-WIDTH * 0.5, y, chord_z), (0.0, y, ridge_z), 0.060, wood)
        _beam(b, (0.0, y, ridge_z), (WIDTH * 0.5, y, chord_z), 0.060, wood)

    # T1-11 performs both the structural-sheet and cladding jobs.
    b = builders["siding"]
    _wall_skin(b, (0.38, 0.54, 0.60), offset=0.075, mat_id=MAT_WOOD,
               cut_front_door=True)

    # One roof layer contains OSB, felt, economy shingles, and ridge cap.
    b = builders["roofing"]
    for side in (-1, 1):
        _roof_plane(b, side, 0.035, (0.72, 0.58, 0.36), mat_id=MAT_WOOD)
        _roof_plane(b, side, 0.055, (0.28, 0.29, 0.31),
                    mat_id=MAT_SHEETING)
        _roof_plane(b, side, 0.075, (0.20, 0.23, 0.27), mat_id=MAT_SHINGLE)

    # Pair of inexpensive site-built plywood doors; no windows or utilities.
    b = builders["openings"]
    door_h = 6.67 * FT
    for sx in (-1, 1):
        add_box(b, (sx * 1.5 * FT, -LENGTH * 0.5 - 0.104,
                    SLAB_TOP + door_h * 0.5),
                (3.0 * FT - 0.02, 0.045, door_h), (0.62, 0.52, 0.34),
                mat_id=MAT_WOOD)
        for z in (SLAB_TOP + 0.35, SLAB_TOP + door_h - 0.35):
            add_box(b, (sx * 1.5 * FT, -LENGTH * 0.5 - 0.132, z),
                    (2.7 * FT, 0.025, 0.08), (0.30, 0.31, 0.30),
                    mat_id=MAT_METAL)

    # Bare fascia, corners, and ridge—no gutters or finish package.
    b = builders["finish"]
    trim = (0.88, 0.87, 0.82)
    for sx in (-1, 1):
        x = sx * (WIDTH * 0.5 + 0.145)
        for sy in (-1, 1):
            add_box(b, (x, sy * (LENGTH * 0.5 + 0.12),
                        SLAB_TOP + EAVE_HEIGHT * 0.5),
                    (0.10, 0.10, EAVE_HEIGHT), trim, mat_id=MAT_WOOD)
    add_box(b, (0.0, 0.0, SLAB_TOP + PEAK_HEIGHT + 0.07),
            (0.12, LENGTH + 0.48, 0.10), (0.24, 0.26, 0.28),
            mat_id=MAT_SHINGLE)

    return {key: builder.build() for key, builder in builders.items()}


def validate_shed() -> None:
    econ = shed_economics()
    assert econ["floor_sqft"] == 384.0
    assert PEAK_HEIGHT_FT == 10.0 and EAVE_HEIGHT_FT == 8.0
    assert len(SHED_STAGES) == 9 and len(COST_ITEMS) == 10
    assert econ["material"] > 0 and econ["labor_hours"] > 0
    assert econ["price"] > econ["total_cost"]
    assert econ["price"] <= 10_000.0
    layers = build_shed_layers()
    assert list(layers) == [stage.key for stage in SHED_STAGES]
    assert all(len(mesh.vertices) > 0 for mesh in layers.values())
