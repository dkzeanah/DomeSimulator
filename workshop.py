"""
Workshop fit-out: room sections, partition walls, and placeable props.

The dome floor is divided into 10 sections — a circular center hub plus
nine 40-degree wedges. Each section can be assigned a room function
(office, bathroom, wood shop, ...) which drives floor markings, optional
partition walls, and the PTZ camera's contextual awareness (what kind of
activity the vision system should expect in the area it is watching).

Props are parametric furniture/equipment models built from prisms and
cylinders, each carrying weight / cost / power-draw stats for the BOM.
Builder functions receive a duck-typed MeshBuilder plus a Transform, so
this module stays import-cycle-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from materials import (
    MAT_EMISSIVE,
    MAT_GRASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_WOOD,
)

CENTER_FRACTION = 0.34          # center hub radius as fraction of floor
SECTION_COUNT = 10              # 1 hub + 9 wedges
WEDGE_DEGREES = 40.0

PARTITION_MODES = ["None", "Markings", "Low Walls", "Full Walls"]
PARTITION_HEIGHTS = {"Low Walls": 1.15, "Full Walls": 2.05}
WALL_COST_PER_M2 = 45.0
WALL_WEIGHT_PER_M2 = 16.0


@dataclass(frozen=True)
class RoomType:
    name: str
    color: tuple[float, float, float]
    hint: str                    # likely happenings for the vision system


ROOM_TYPES: list[RoomType] = [
    RoomType("Unassigned", (0.55, 0.55, 0.55), "unassigned area"),
    RoomType("Office", (0.35, 0.55, 0.85), "desk work, calls, paperwork"),
    RoomType("Bathroom", (0.45, 0.75, 0.85), "hygiene, brief occupancy"),
    RoomType("Kitchen", (0.90, 0.65, 0.30), "cooking, dishes, breaks"),
    RoomType("Lounge", (0.60, 0.45, 0.75), "resting, meetings, guests"),
    RoomType("Wood Shop", (0.75, 0.55, 0.30), "sawing, sanding, assembly"),
    RoomType("Metal Shop", (0.60, 0.62, 0.68), "welding, grinding, sparks"),
    RoomType("Electronics", (0.30, 0.75, 0.50), "soldering, bench testing"),
    RoomType("3D Printing", (0.40, 0.70, 0.80), "printer runs, filament swaps"),
    RoomType("Assembly", (0.85, 0.75, 0.35), "kitting, fastening, packing"),
    RoomType("Paint Booth", (0.85, 0.45, 0.55), "spraying, drying, fumes"),
    RoomType("Storage", (0.55, 0.55, 0.45), "inventory, pick and place"),
    RoomType("Grow Room", (0.35, 0.70, 0.35), "watering, harvest, grow lights"),
    RoomType("Studio", (0.75, 0.40, 0.70), "filming, photo, audio work"),
    RoomType("Fitness", (0.80, 0.50, 0.30), "exercise, equipment use"),
    RoomType("Classroom", (0.40, 0.60, 0.80), "teaching, groups, demos"),
]

ROOM_TYPE_BY_NAME = {r.name: r for r in ROOM_TYPES}


def section_of(x: float, y: float, floor_radius: float) -> int:
    """Section index at a floor point: 0 = center hub, 1-9 = wedges,
    -1 = outside the dome floor."""
    d = math.hypot(x, y)
    if d > floor_radius * 1.02:
        return -1
    if d < floor_radius * CENTER_FRACTION:
        return 0
    azimuth = (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
    return 1 + int(azimuth // WEDGE_DEGREES) % 9


def section_label(index: int) -> str:
    if index == 0:
        return "S1 · Center"
    a0 = (index - 1) * 40
    return f"S{index + 1} · {a0}-{a0 + 40}°"


# ---------------------------------------------------------------------------
# Transform for prop placement (local: +Y is the prop's front, z up)
# ---------------------------------------------------------------------------

class Transform:
    def __init__(self, x: float, y: float, z: float, yaw_degrees: float):
        a = -math.radians(yaw_degrees)
        self.cos = math.cos(a)
        self.sin = math.sin(a)
        self.origin = np.array([x, y, z])
        self.right = np.array([self.cos, self.sin, 0.0])
        self.fwd = np.array([-self.sin, self.cos, 0.0])
        self.up = np.array([0.0, 0.0, 1.0])

    def p(self, lx: float, ly: float, lz: float) -> np.ndarray:
        return self.origin + self.right * lx + self.fwd * ly + \
            np.array([0.0, 0.0, lz])


def _box(b, t: Transform, cx, cy, z0, z1, hw, hd, color, mat=MAT_PLAIN,
         alpha=1.0):
    """Axis-aligned (in prop space) box from z0..z1."""
    b.prism(t.p(cx, cy, z0), t.p(cx, cy, z1),
            [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)],
            t.right, t.fwd, color, alpha=alpha, cap_ends=True)


# ---------------------------------------------------------------------------
# Prop builders
# ---------------------------------------------------------------------------

def _worktable(b, t):
    steel = (0.25, 0.27, 0.30)
    top = (0.72, 0.58, 0.38)
    for sx in (-0.72, 0.72):
        for sy in (-0.28, 0.28):
            _box(b, t, sx, sy, 0.0, 0.86, 0.03, 0.03, steel)
    _box(b, t, 0, 0, 0.86, 0.92, 0.80, 0.35, top, MAT_WOOD)
    _box(b, t, 0, 0, 0.25, 0.29, 0.70, 0.30, top, MAT_WOOD)


def _pegboard_bench(b, t):
    _worktable(b, t)
    _box(b, t, 0, 0.32, 0.92, 1.70, 0.80, 0.015, (0.76, 0.64, 0.45),
         MAT_WOOD)
    for row in range(3):
        _box(b, t, 0, 0.335, 1.05 + row * 0.22, 1.07 + row * 0.22,
             0.6, 0.02, (0.45, 0.47, 0.50), MAT_METAL)


def _tool_chest(b, t):
    red = (0.72, 0.15, 0.15)
    for sx in (-0.32, 0.32):
        for sy in (-0.18, 0.18):
            b.cylinder(t.p(sx, sy, 0.0), t.p(sx, sy, 0.12), 0.045, 6,
                       (0.10, 0.10, 0.11))
    _box(b, t, 0, 0, 0.12, 1.00, 0.42, 0.25, red, MAT_METAL)
    for z in (0.32, 0.55, 0.78):
        _box(b, t, 0, -0.252, z, z + 0.025, 0.36, 0.006,
             (0.85, 0.85, 0.87), MAT_METAL)


def _shelving(b, t):
    post = (0.35, 0.40, 0.45)
    shelf = (0.60, 0.62, 0.65)
    for sx in (-0.6, 0.6):
        for sy in (-0.25, 0.25):
            _box(b, t, sx, sy, 0.0, 1.90, 0.02, 0.02, post)
    for z in (0.10, 0.55, 1.00, 1.45, 1.88):
        _box(b, t, 0, 0, z, z + 0.035, 0.62, 0.28, shelf, MAT_METAL)


def _crates(b, t):
    _box(b, t, 0.05, 0.0, 0.0, 0.40, 0.30, 0.25, (0.55, 0.42, 0.25),
         MAT_WOOD)
    _box(b, t, 0.15, 0.05, 0.40, 0.74, 0.25, 0.22, (0.60, 0.48, 0.30),
         MAT_WOOD)
    _box(b, t, -0.32, -0.02, 0.0, 0.34, 0.18, 0.18, (0.50, 0.40, 0.28),
         MAT_WOOD)


def _machine(b, t):
    _box(b, t, 0, 0, 0.0, 1.30, 0.55, 0.45, (0.45, 0.48, 0.52), MAT_METAL)
    _box(b, t, 0, -0.05, 1.30, 1.70, 0.40, 0.30, (0.35, 0.38, 0.42),
         MAT_METAL)
    _box(b, t, 0.30, -0.46, 1.05, 1.35, 0.14, 0.02, (0.15, 0.16, 0.18))
    _box(b, t, 0.30, -0.468, 1.22, 1.28, 0.09, 0.004, (0.30, 0.90, 0.40),
         MAT_EMISSIVE)


def _desk(b, t):
    wood = (0.50, 0.36, 0.22)
    _box(b, t, 0, 0, 0.72, 0.76, 0.70, 0.35, wood, MAT_WOOD)
    for sx in (-0.66, 0.66):
        _box(b, t, sx, 0, 0.0, 0.72, 0.02, 0.33, wood, MAT_WOOD)
    _box(b, t, 0, 0.12, 0.76, 0.82, 0.05, 0.05, (0.20, 0.20, 0.22))
    _box(b, t, 0, 0.14, 0.82, 1.16, 0.26, 0.02, (0.08, 0.09, 0.11))


def _office_chair(b, t):
    b.disc(t.p(0, 0, 0.04), 0.26, 10, (0.15, 0.15, 0.17))
    b.cylinder(t.p(0, 0, 0.04), t.p(0, 0, 0.50), 0.035, 8,
               (0.30, 0.31, 0.34))
    _box(b, t, 0, 0, 0.50, 0.58, 0.24, 0.24, (0.20, 0.20, 0.28))
    _box(b, t, 0, 0.22, 0.58, 1.05, 0.22, 0.03, (0.20, 0.20, 0.28))


def _filing_cabinet(b, t):
    _box(b, t, 0, 0, 0.0, 1.32, 0.24, 0.30, (0.55, 0.57, 0.60), MAT_METAL)
    for z in (0.30, 0.72, 1.14):
        _box(b, t, 0, -0.302, z, z + 0.02, 0.18, 0.005,
             (0.80, 0.81, 0.83), MAT_METAL)


def _whiteboard(b, t):
    for sx in (-0.5, 0.5):
        _box(b, t, sx, 0, 0.0, 1.80, 0.02, 0.02, (0.35, 0.36, 0.38))
    _box(b, t, 0, 0, 0.90, 1.70, 0.60, 0.015, (0.93, 0.94, 0.95))
    _box(b, t, 0, -0.03, 0.86, 0.90, 0.55, 0.03, (0.55, 0.56, 0.58))


def _sofa(b, t):
    blue = (0.35, 0.42, 0.55)
    _box(b, t, 0, 0, 0.12, 0.45, 0.90, 0.40, blue)
    _box(b, t, 0, 0.32, 0.45, 0.88, 0.90, 0.08, blue)
    for sx in (-0.82, 0.82):
        _box(b, t, sx, 0, 0.12, 0.62, 0.08, 0.40, blue)


def _kitchenette(b, t):
    _box(b, t, 0, 0, 0.0, 0.90, 0.90, 0.35, (0.40, 0.42, 0.45), MAT_WOOD)
    _box(b, t, 0, 0, 0.90, 0.94, 0.92, 0.37, (0.85, 0.84, 0.80))
    b.disc(t.p(-0.40, 0, 0.945), 0.16, 12, (0.25, 0.27, 0.30))
    b.cylinder(t.p(-0.40, 0.16, 0.94), t.p(-0.40, 0.16, 1.16), 0.018, 6,
               (0.70, 0.72, 0.75))
    b.disc(t.p(0.35, 0, 0.945), 0.18, 12, (0.10, 0.10, 0.12))


def _toilet(b, t):
    white = (0.90, 0.91, 0.92)
    b.cylinder(t.p(0, -0.05, 0.0), t.p(0, -0.05, 0.38), 0.19, 10, white)
    _box(b, t, 0, -0.05, 0.38, 0.43, 0.21, 0.25, white)
    _box(b, t, 0, 0.22, 0.38, 0.80, 0.20, 0.09, white)


def _bath_sink(b, t):
    white = (0.90, 0.91, 0.92)
    b.cylinder(t.p(0, 0, 0.0), t.p(0, 0, 0.72), 0.06, 8, white)
    b.cylinder(t.p(0, 0, 0.72), t.p(0, 0, 0.84), 0.20, 12, white)
    b.cylinder(t.p(0, 0.14, 0.84), t.p(0, 0.14, 1.02), 0.016, 6,
               (0.70, 0.72, 0.75))


def _shower(b, t):
    _box(b, t, 0, 0, 0.0, 0.07, 0.45, 0.45, (0.80, 0.82, 0.84))
    _box(b, t, 0, 0.43, 0.0, 2.00, 0.45, 0.02, (0.70, 0.78, 0.82),
         alpha=0.55)
    _box(b, t, -0.43, 0, 0.0, 2.00, 0.02, 0.43, (0.70, 0.78, 0.82),
         alpha=0.55)
    b.cylinder(t.p(-0.30, 0.38, 1.90), t.p(-0.30, 0.30, 1.98), 0.05, 6,
               (0.70, 0.72, 0.75))


def _tripod_light(b, t, on=True):
    for k in range(3):
        a = 2 * math.pi * k / 3
        b.cylinder(t.p(0, 0, 1.05),
                   t.p(0.42 * math.sin(a), 0.42 * math.cos(a), 0.0),
                   0.018, 6, (0.22, 0.23, 0.25))
    b.cylinder(t.p(0, 0, 1.0), t.p(0, 0, 1.75), 0.025, 6,
               (0.28, 0.29, 0.32))
    _box(b, t, 0, 0, 1.75, 1.99, 0.19, 0.09, (0.20, 0.20, 0.22),
         MAT_METAL)
    if on:
        _box(b, t, 0, 0.095, 1.78, 1.96, 0.16, 0.004, (1.0, 0.97, 0.85),
             MAT_EMISSIVE)
    else:
        _box(b, t, 0, 0.095, 1.78, 1.96, 0.16, 0.004, (0.32, 0.33, 0.35))


def _shop_light(b, t, on=True):
    b.disc(t.p(0, 0, 0.04), 0.24, 10, (0.18, 0.19, 0.21))
    b.cylinder(t.p(0, 0, 0.0), t.p(0, 0, 2.45), 0.03, 6, (0.28, 0.29, 0.32))
    _box(b, t, 0, 0, 2.45, 2.60, 0.30, 0.12, (0.22, 0.23, 0.25), MAT_METAL)
    if on:
        _box(b, t, 0, 0, 2.435, 2.45, 0.27, 0.10, (1.0, 0.96, 0.82),
             MAT_EMISSIVE)
    else:
        _box(b, t, 0, 0, 2.435, 2.45, 0.27, 0.10, (0.32, 0.33, 0.35))


def _trash_bin(b, t):
    b.cylinder(t.p(0, 0, 0.0), t.p(0, 0, 0.55), 0.18, 10,
               (0.30, 0.32, 0.35), cap_ends=True)


def _battery_bank(b, t):
    dark = (0.13, 0.14, 0.16)
    _box(b, t, 0, 0, 0.0, 1.05, 0.52, 0.30, dark, MAT_METAL)
    _box(b, t, 0, -0.305, 0.72, 0.92, 0.30, 0.004, (0.25, 0.75, 0.95),
         MAT_EMISSIVE)                                   # LCD readout
    for i in range(3):
        _box(b, t, -0.30 + i * 0.30, -0.305, 0.15, 0.55, 0.10, 0.003,
             (0.30, 0.32, 0.36), MAT_METAL)              # cell handles
    _box(b, t, 0, 0, 1.05, 1.09, 0.54, 0.32, (0.20, 0.21, 0.24), MAT_METAL)


def _charge_controller(b, t):
    _box(b, t, 0, 0, 0.0, 1.30, 0.05, 0.05, (0.30, 0.31, 0.34))
    _box(b, t, 0, 0, 1.05, 1.55, 0.24, 0.10, (0.18, 0.19, 0.22), MAT_METAL)
    _box(b, t, 0, -0.105, 1.22, 1.44, 0.17, 0.004, (0.30, 0.90, 0.55),
         MAT_EMISSIVE)                                   # status display
    b.cylinder(t.p(-0.1, 0, 0.0), t.p(-0.1, 0, 1.05), 0.02, 6,
               (0.10, 0.10, 0.11))
    b.cylinder(t.p(0.1, 0, 0.0), t.p(0.1, 0, 1.05), 0.02, 6,
               (0.60, 0.20, 0.15))


def _power_meter(b, t):
    _box(b, t, 0, 0, 0.0, 1.45, 0.04, 0.04, (0.30, 0.31, 0.34))
    _box(b, t, 0, 0, 1.35, 1.75, 0.26, 0.08, (0.12, 0.13, 0.15), MAT_METAL)
    _box(b, t, 0, -0.085, 1.42, 1.68, 0.20, 0.004, (0.35, 0.80, 1.0),
         MAT_EMISSIVE)                                   # kWh LCD


def _wall_outlet(b, t):
    _box(b, t, 0, 0, 0.0, 0.42, 0.05, 0.05, (0.35, 0.36, 0.38))
    _box(b, t, 0, -0.055, 0.20, 0.42, 0.09, 0.015, (0.90, 0.90, 0.88))
    for z in (0.26, 0.34):
        _box(b, t, 0, -0.072, z, z + 0.035, 0.03, 0.003,
             (0.20, 0.20, 0.22))                          # socket faces


def _power_column(b, t):
    b.cylinder(t.p(0, 0, 0.0), t.p(0, 0, 2.40), 0.09, 10,
               (0.30, 0.32, 0.36), cap_ends=True)
    b.cylinder(t.p(0, 0, 0.02), t.p(0, 0, 0.10), 0.20, 10,
               (0.20, 0.21, 0.24), cap_ends=True)
    # Four outlets placed concentrically around the column.
    for k in range(4):
        a = math.pi * 0.5 * k
        dx, dy = math.sin(a), math.cos(a)
        b.prism(t.p(dx * 0.09, dy * 0.09, 0.40),
                t.p(dx * 0.15, dy * 0.15, 0.40),
                [(-0.05, -0.09), (0.05, -0.09), (0.05, 0.09), (-0.05, 0.09)],
                t.right * dy - t.fwd * dx,
                t.up, (0.90, 0.90, 0.88), cap_ends=True)
    b.cylinder(t.p(0, 0, 2.28), t.p(0, 0, 2.34), 0.10, 10,
               (1.0, 0.85, 0.4), mat_id=MAT_EMISSIVE, cap_ends=True)


@dataclass(frozen=True)
class PropType:
    name: str
    category: str
    cost: float
    weight: float
    watts: float
    pick_radius: float
    pick_height: float
    build: Callable
    light_z: float | None = None   # point-light height when it is a lamp
    role: str = ""                 # battery / controller / meter / outlet


PROP_TYPES: list[PropType] = [
    PropType("Worktable", "WORKSHOP", 180, 45, 0, 0.95, 1.0, _worktable),
    PropType("Pegboard Bench", "WORKSHOP", 260, 60, 0, 0.95, 1.8,
             _pegboard_bench),
    PropType("Machine Station", "WORKSHOP", 2400, 220, 1100, 0.75, 1.8,
             _machine),
    PropType("Tool Chest", "WORKSHOP", 320, 55, 0, 0.55, 1.1, _tool_chest),
    PropType("Shelving Unit", "STORAGE", 140, 40, 0, 0.75, 2.0, _shelving),
    PropType("Crate Stack", "STORAGE", 60, 25, 0, 0.55, 0.8, _crates),
    PropType("Filing Cabinet", "STORAGE", 150, 30, 0, 0.45, 1.4,
             _filing_cabinet),
    PropType("Trash Bin", "STORAGE", 25, 5, 0, 0.25, 0.6, _trash_bin),
    PropType("Office Desk", "OFFICE", 220, 35, 150, 0.85, 1.2, _desk),
    PropType("Office Chair", "OFFICE", 120, 12, 0, 0.35, 1.1,
             _office_chair),
    PropType("Whiteboard", "OFFICE", 90, 15, 0, 0.60, 1.9, _whiteboard),
    PropType("Sofa", "OFFICE", 450, 45, 0, 1.0, 0.95, _sofa),
    PropType("Kitchenette", "KITCHEN / BATH", 600, 80, 800, 1.0, 1.0,
             _kitchenette),
    PropType("Toilet", "KITCHEN / BATH", 240, 45, 0, 0.35, 0.85, _toilet),
    PropType("Bathroom Sink", "KITCHEN / BATH", 180, 25, 0, 0.30, 1.1,
             _bath_sink),
    PropType("Shower Stall", "KITCHEN / BATH", 420, 60, 0, 0.60, 2.05,
             _shower),
    PropType("Tripod Light", "LIGHTING", 70, 8, 50, 0.45, 2.0,
             _tripod_light, light_z=1.85),
    PropType("Shop Light", "LIGHTING", 110, 12, 80, 0.35, 2.65,
             _shop_light, light_z=2.40),
    PropType("Battery Bank", "ELECTRICAL", 3800, 180, 0, 0.65, 1.1,
             _battery_bank, role="battery"),
    PropType("Charge Controller", "ELECTRICAL", 850, 14, 0, 0.35, 1.6,
             _charge_controller, role="controller"),
    PropType("Power Meter LCD", "ELECTRICAL", 160, 5, 0, 0.32, 1.8,
             _power_meter, role="meter"),
    PropType("Wall Outlet", "ELECTRICAL", 18, 1, 0, 0.18, 0.5,
             _wall_outlet, role="outlet"),
    PropType("Power Column", "ELECTRICAL", 260, 25, 0, 0.28, 2.4,
             _power_column, role="outlet"),
]

PROP_TYPE_BY_NAME = {p.name: p for p in PROP_TYPES}


# ---------------------------------------------------------------------------
# Section / partition geometry (model is duck-typed DomeModel)
# ---------------------------------------------------------------------------

def _wedge_point(radius: float, azimuth_deg: float, z: float,
                 origin=None) -> np.ndarray:
    a = math.radians(azimuth_deg)
    p = np.array([radius * math.sin(a), radius * math.cos(a), z])
    if origin is not None:
        p = p + np.array([origin[0], origin[1], 0.0])
    return p


def build_sections(b, model) -> None:
    """Floor markings: translucent color fill per assigned section plus
    boundary lines. Skipped entirely in partition mode 'None'."""
    cfg = model.config
    if cfg.partitions == "None":
        return
    fr = model.floor_radius * 0.985
    rc = model.floor_radius * CENTER_FRACTION
    fh = model.foundation.height
    origin = (float(model.origin[0]), float(model.origin[1]))
    z_fill = fh + 0.006
    z_line = fh + 0.010
    up = np.array([0.0, 0.0, 1.0])

    center_room = ROOM_TYPE_BY_NAME.get(cfg.sections[0])
    if center_room and center_room.name != "Unassigned":
        b.disc((origin[0], origin[1], z_fill), rc * 0.97, 36,
               center_room.color, alpha=0.30)

    for w in range(9):
        room = ROOM_TYPE_BY_NAME.get(cfg.sections[1 + w])
        if not room or room.name == "Unassigned":
            continue
        a0 = w * WEDGE_DEGREES + 1.0
        a1 = (w + 1) * WEDGE_DEGREES - 1.0
        steps = 6
        for s in range(steps):
            b0 = a0 + (a1 - a0) * s / steps
            b1 = a0 + (a1 - a0) * (s + 1) / steps
            b.quad(
                _wedge_point(rc + 0.06, b0, z_fill, origin),
                _wedge_point(fr, b0, z_fill, origin),
                _wedge_point(fr, b1, z_fill, origin),
                _wedge_point(rc + 0.06, b1, z_fill, origin),
                up, room.color, alpha=0.30)

    # Boundary lines: nine radial spokes plus the center-hub ring.
    line_color = (0.88, 0.89, 0.92)
    o3 = np.array([origin[0], origin[1], 0.0])
    for k in range(9):
        az = k * WEDGE_DEGREES
        a = math.radians(az)
        direction = np.array([math.sin(a), math.cos(a), 0.0])
        perp = np.array([math.cos(a), -math.sin(a), 0.0]) * 0.022
        p_in = direction * rc + o3
        p_out = direction * fr + o3
        b.quad(
            p_in - perp + [0, 0, z_line], p_out - perp + [0, 0, z_line],
            p_out + perp + [0, 0, z_line], p_in + perp + [0, 0, z_line],
            up, line_color)
    ring_steps = 40
    for s in range(ring_steps):
        b0 = 360.0 * s / ring_steps
        b1 = 360.0 * (s + 1) / ring_steps
        b.quad(
            _wedge_point(rc - 0.022, b0, z_line, origin),
            _wedge_point(rc + 0.022, b0, z_line, origin),
            _wedge_point(rc + 0.022, b1, z_line, origin),
            _wedge_point(rc - 0.022, b1, z_line, origin),
            up, line_color)


def partition_segments(model) -> list[dict]:
    """Wall segments between wedges whose assigned rooms differ.
    Adjacent wedges with the same room merge into one bigger room."""
    cfg = model.config
    height = PARTITION_HEIGHTS.get(cfg.partitions)
    if height is None:
        return []
    fr = model.floor_radius
    rc = fr * CENTER_FRACTION
    inner = rc + 1.0            # leaves a ~1 m doorway near the hub
    outer = fr - 0.20
    if outer - inner < 0.4:
        return []
    segments = []
    for k in range(9):
        room_a = cfg.sections[1 + (k + 8) % 9]
        room_b = cfg.sections[1 + k]
        if room_a == room_b:
            continue
        az = k * WEDGE_DEGREES
        a = math.radians(az)
        direction = np.array([math.sin(a), math.cos(a), 0.0])
        segments.append({
            "inner": direction * inner,
            "outer": direction * outer,
            "length": outer - inner,
            "height": height,
            "azimuth": az,
        })
    return segments


def build_partitions(b, model) -> None:
    fh = model.foundation.height
    wall_color = (0.82, 0.80, 0.76)
    o3 = np.array([float(model.origin[0]), float(model.origin[1]), 0.0])
    for seg in partition_segments(model):
        a = math.radians(seg["azimuth"])
        perp = np.array([math.cos(a), -math.sin(a), 0.0])
        h = seg["height"]
        start = seg["inner"] + o3 + np.array([0.0, 0.0, fh + h * 0.5])
        end = seg["outer"] + o3 + np.array([0.0, 0.0, fh + h * 0.5])
        b.prism(start, end,
                [(-0.035, -h * 0.5), (0.035, -h * 0.5),
                 (0.035, h * 0.5), (-0.035, h * 0.5)],
                perp, np.array([0.0, 0.0, 1.0]), wall_color,
                cap_ends=True)


def build_prop(b, model, entry) -> None:
    prop = PROP_TYPE_BY_NAME.get(entry.get("type"))
    if prop is None:
        return
    fh = model.foundation.height
    ox, oy = float(model.origin[0]), float(model.origin[1])
    t = Transform(ox + float(entry.get("x", 0.0)),
                  oy + float(entry.get("y", 0.0)),
                  fh, float(entry.get("yaw", 0.0)))
    if prop.light_z is not None:
        prop.build(b, t, on=bool(entry.get("on", True)))
    else:
        prop.build(b, t)


def build_props(b, model) -> None:
    for entry in model.config.props:
        build_prop(b, model, entry)


# ---------------------------------------------------------------------------
# Electrical wiring and plumbing rough-in runs
# ---------------------------------------------------------------------------

WIRE_COST_PER_M = 1.4          # 12/2 romex in conduit
PEX_COST_PER_M = 2.1           # per line (hot + cold both run)
DRAIN_COST_PER_M = 5.0
FIXTURE_ROUGH_COST = 40.0
WATER_FIXTURES = {"Toilet", "Bathroom Sink", "Shower Stall", "Kitchenette"}


def _prop_entries_with_role(model, roles: set[str]) -> list[dict]:
    out = []
    for entry in model.config.props:
        prop = PROP_TYPE_BY_NAME.get(entry.get("type"))
        if prop is not None and prop.role in roles:
            out.append(entry)
    return out


def power_source_entry(model) -> dict | None:
    """The wiring origin: battery bank, else charge controller."""
    for roles in ({"battery"}, {"controller"}):
        found = _prop_entries_with_role(model, roles)
        if found:
            return found[0]
    return None


def wiring_runs(model) -> list[dict]:
    """Conduit runs from the power source to every outlet-role device.
    Local (dome-frame) coordinates; lengths include 30% routing slack."""
    source = power_source_entry(model)
    if source is None:
        return []
    sx, sy = float(source["x"]), float(source["y"])
    runs = []
    for entry in _prop_entries_with_role(model, {"outlet", "meter",
                                                 "controller"}):
        if entry is source:
            continue
        ex, ey = float(entry["x"]), float(entry["y"])
        direct = math.hypot(ex - sx, ey - sy)
        runs.append({
            "from": (sx, sy), "to": (ex, ey),
            "length": direct * 1.3,
            "target": entry.get("type", "device"),
        })
    return runs


def plumbing_runs(model) -> list[dict]:
    """Supply + drain runs from each water fixture to the south utility
    stub. Local coordinates."""
    fr = model.floor_radius
    utility = (0.6, -fr * 0.75)
    runs = []
    for entry in model.config.props:
        if entry.get("type") in WATER_FIXTURES:
            ex, ey = float(entry["x"]), float(entry["y"])
            direct = math.hypot(ex - utility[0], ey - utility[1])
            runs.append({
                "from": utility, "to": (ex, ey),
                "length": direct * 1.25,
                "fixture": entry["type"],
            })
    return runs
