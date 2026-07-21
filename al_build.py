"""
Dome assembly line — build geometry, economics, and labor model.

GL-free so the whole model can run head-less (``assembly_line.py
--selftest``). It provides:

1.  A parametric :class:`DomeSpec` + :class:`DomeType` and
    :func:`build_dome_catalog`, which emit dome geometry **element by
    element** (each element records where it is placed, its material
    cost, and its install-labor time). Four product lines share the
    machinery: the manufactured **home**, a **storage shed**, a
    **greenhouse**, and a **storm shelter**.

2.  A single, editable :data:`ASSUMPTIONS` block with every dollar/time
    figure the demo rests on.

3.  Derived business math: per-dome P&L, throughput / bottleneck,
    break-even, benchmark vs. conventional housing, product value, scale
    scenarios, and buy-here-pay-here monthly financing.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np

from dome_model import build_geodesic, normalize
from materials import (
    MAT_CANVAS,
    MAT_CONCRETE,
    MAT_DECK,
    MAT_EMISSIVE,
    MAT_GLASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_SHEETING,
    MAT_SHINGLE,
    MAT_SOLAR,
    MAT_WOOD,
)
from mesh_builder import Mesh, MeshBuilder

# ===========================================================================
# ASSUMPTIONS — every business figure the demo rests on lives here.
# ===========================================================================

ASSUMPTIONS = {
    # --- labor -----------------------------------------------------------
    "burdened_wage_per_hour": 46.0,
    "workers_per_station": 2,           # default crew placing elements
    "worker_stride_m": 0.76,
    "worker_walk_speed_mps": 1.30,
    "hand_place_seconds": 6.0,
    "shift_hours_per_day": 8.0,
    "work_days_per_year": 250,

    # --- fixed / capital -------------------------------------------------
    "line_capex": 2_400_000.0,
    "capex_amortize_years": 7.0,
    "fixed_overhead_per_month": 85_000.0,
    "target_units_per_year": 300,
    # Overhead is allocated by the labor a unit consumes (activity-based),
    # so a cheap fast-built shed carries far less burden than a home.
    "overhead_per_labor_hour": 16.0,

    # --- home pricing (base; scaled by size & layout) --------------------
    "sale_price_base": 52_000.0,
    "sale_price_per_m2": 820.0,
    "layout_price": {"Studio": 0.0, "1-Bedroom": 8_000.0,
                     "2-Bedroom": 16_000.0},

    # --- buy-here-pay-here financing -------------------------------------
    "bhph_apr": 0.119,                  # annual rate
    "bhph_term_months": 60,
    "bhph_down_fraction": 0.10,

    # --- comparison baseline (conventional manufactured home) ------------
    "benchmark_name": "Conventional manufactured home",
    "benchmark_price": 128_000.0,
    "benchmark_build_days": 34,
    "benchmark_labor_hours": 640.0,
    "benchmark_material_cost": 58_000.0,

    # --- product value story --------------------------------------------
    "solar_watts_per_panel": 340.0,
    "battery_kwh": 20.0,
    "daily_load_kwh": 14.0,
    "insulation_r_per_element": 0.28,
    "carbon_kg_per_kg_material": 1.7,
    "osha_incident_rate_target": 1.8,

    # --- QC / risk -------------------------------------------------------
    "first_pass_yield": 0.94,
    "rework_cost_fraction": 0.06,
}

# Per-category unit economics: (material $ per element, labor-min per
# element, weight kg per element), scaled per element by physical size.
CATEGORY_ECON = {
    "floor":       (26.0, 11.0, 22.0),
    "frame":       (28.0, 13.0, 15.0),
    "hub":         (18.0, 8.0, 3.5),
    "column":      (240.0, 52.0, 90.0),
    "water":       (30.0, 17.0, 6.0),
    "power":       (24.0, 14.0, 4.0),
    "fixture":     (320.0, 40.0, 40.0),
    "insulation":  (22.0, 9.0, 4.0),
    "sheetrock":   (24.0, 11.0, 12.0),
    "osb":         (30.0, 11.0, 14.0),
    "wrap":        (12.0, 6.0, 2.0),
    "shingle":     (20.0, 9.0, 5.0),
    "fiberglass":  (38.0, 15.0, 8.0),
    "hatch":       (2100.0, 180.0, 140.0),
    "furniture":   (430.0, 36.0, 55.0),
    "solar":       (150.0, 19.0, 11.0),
    # other product lines
    "sheetmetal":  (34.0, 10.0, 12.0),
    "glazing":     (86.0, 12.0, 9.0),
    "steelplate":  (150.0, 22.0, 62.0),
    "grow":        (180.0, 16.0, 25.0),
    "shelter_kit": (260.0, 30.0, 40.0),
}

CATEGORY_LABEL = {
    "floor": "Floor joist / decking", "frame": "Geodesic strut",
    "hub": "Hub connector set", "column": "Utility column section",
    "water": "Water line run", "power": "Power conduit run",
    "fixture": "Plumbing fixture / outlet", "insulation": "Insulation batt",
    "sheetrock": "Sheetrock panel", "osb": "OSB sheathing panel",
    "wrap": "Water-barrier membrane", "shingle": "Shingle-scale course",
    "fiberglass": "Fiberglass encasement", "hatch": "Watertight hatch",
    "furniture": "Interior fit-out item", "solar": "Solar skin panel",
    "sheetmetal": "Sheet-metal panel", "glazing": "Glazing panel",
    "steelplate": "Steel plate", "grow": "Grow bench / vent",
    "shelter_kit": "Shelter fit-out",
}

DOME_FREQ_DEFAULT = 3
FLOOR_TOP = 0.35
REFERENCE_RADIUS = 4.0


# ---------------------------------------------------------------------------
# Stage registry — every station any product line can use
# ---------------------------------------------------------------------------

@dataclass
class StageDef:
    key: str
    title: str
    desc: str
    color: tuple


_STAGE_LIST = [
    StageDef("floor", "FLOOR FRAMING",
             "Wood floor built into the base ring: rim, joists, decking",
             (0.72, 0.55, 0.30)),
    StageDef("frame", "SHELL FRAMING",
             "Geodesic frame raised from the base ring to the apex",
             (0.82, 0.62, 0.28)),
    StageDef("column", "CENTER UTILITY COLUMN",
             "Floor-to-apex service column + exterior crane anchor",
             (0.60, 0.63, 0.68)),
    StageDef("water", "WATER LINES",
             "Hot / cold PEX and drains terminating at the column",
             (0.25, 0.50, 0.90)),
    StageDef("power", "POWER LINES",
             "Electrical conduit terminating at the column",
             (0.95, 0.80, 0.20)),
    StageDef("fixtures", "FIXTURES & OUTLETS",
             "Plumbing fixtures set; outlets on the column and perimeter",
             (0.88, 0.90, 0.94)),
    StageDef("insulation", "INSULATION",
             "Insulation batts packed into every frame bay",
             (0.94, 0.52, 0.62)),
    StageDef("sheetrock", "SHEETROCK", "Interior shell sheetrocked",
             (0.90, 0.90, 0.85)),
    StageDef("osb", "OSB SHEATHING", "OSB panel board over the dome",
             (0.84, 0.70, 0.44)),
    StageDef("wrap", "WATER BARRIER", "Sill / water membrane over the OSB",
             (0.60, 0.64, 0.72)),
    StageDef("shingles", "SHINGLE SCALES",
             "Plastic scale shingles — mechanical water barrier",
             (0.20, 0.40, 0.45)),
    StageDef("fiberglass", "FIBERGLASS ENCASEMENT",
             "Entire structure encased in a watertight fiberglass shell",
             (0.62, 0.85, 0.90)),
    StageDef("hatch", "WATERTIGHT HATCH DOOR",
             "Sealed marine-style hatch — the only opening, zero windows",
             (0.52, 0.56, 0.62)),
    StageDef("interior", "KITCHEN / BATH / BEDROOM",
             "Complete kitchen, bathroom and bedroom fit-out",
             (0.68, 0.50, 0.80)),
    StageDef("solar", "SOLAR ARRAY",
             "Solar skin applied to the sun-facing band + final QC",
             (0.15, 0.28, 0.60)),
    # --- other product lines --------------------------------------------
    StageDef("sheetmetal", "SHEET-METAL CLADDING",
             "Corrugated sheet metal fastened over the frame",
             (0.66, 0.68, 0.72)),
    StageDef("glazing", "GLAZING PANELS",
             "Twin-wall polycarbonate glazing clipped into every bay",
             (0.70, 0.86, 0.90)),
    StageDef("steelplate", "STEEL PLATE SHELL",
             "Welded steel plate — impact-rated storm envelope",
             (0.40, 0.44, 0.50)),
    StageDef("grow", "GROW BENCHES & VENTS",
             "Grow benches, irrigation, and ridge vents installed",
             (0.30, 0.60, 0.35)),
    StageDef("shelterkit", "SHELTER FIT-OUT",
             "Bench seating, air vent, and emergency supplies",
             (0.55, 0.50, 0.45)),
]
ALL_STAGES = {s.key: s for s in _STAGE_LIST}
# Back-compat: STAGES is the home sequence.
HOME_STAGE_KEYS = ["floor", "frame", "column", "water", "power", "fixtures",
                   "insulation", "sheetrock", "osb", "wrap", "shingles",
                   "fiberglass", "hatch", "interior", "solar"]
STAGES = [ALL_STAGES[k] for k in HOME_STAGE_KEYS]
STAGE_INDEX = {s.key: i for i, s in enumerate(STAGES)}


# ---------------------------------------------------------------------------
# Product lines (dome types)
# ---------------------------------------------------------------------------

@dataclass
class DomeType:
    key: str
    name: str
    stage_keys: list
    frame_color: tuple
    frame_mat: int
    strut_radius: float
    radius_range: tuple
    freq_choices: list
    price_base: float
    price_per_m2: float
    tagline: str

    @property
    def stages(self):
        return [ALL_STAGES[k] for k in self.stage_keys]


DOME_TYPES = {
    "home": DomeType(
        "home", "Dome Home", HOME_STAGE_KEYS,
        (0.55, 0.42, 0.26), MAT_WOOD, 0.052, (3.2, 4.6), [3, 3, 4],
        52_000.0, 820.0, "Turnkey off-grid manufactured home"),
    "shed": DomeType(
        "shed", "Storage Shed", ["floor", "frame", "sheetmetal", "hatch"],
        (0.50, 0.52, 0.56), MAT_METAL, 0.045, (2.8, 4.2), [3],
        8_200.0, 340.0, "Wood/metal frame in corrugated sheet metal"),
    "greenhouse": DomeType(
        "greenhouse", "Greenhouse",
        ["floor", "frame", "glazing", "grow"],
        (0.72, 0.74, 0.78), MAT_METAL, 0.040, (3.0, 4.6), [3],
        11_000.0, 500.0, "Aluminium frame under twin-wall polycarbonate"),
    "shelter": DomeType(
        "shelter", "Storm Shelter",
        ["floor", "frame", "steelplate", "hatch", "shelterkit"],
        (0.34, 0.37, 0.42), MAT_METAL, 0.075, (1.6, 2.3), [2],
        13_500.0, 900.0, "Welded short-strut steel-plate storm dome"),
}
DOME_TYPE_LIST = ["home", "shed", "greenhouse", "shelter"]


# ---------------------------------------------------------------------------
# Dome specification
# ---------------------------------------------------------------------------

CLADDINGS = [
    ("Slate Scale", (0.16, 0.34, 0.38)),
    ("Terra Scale", (0.42, 0.24, 0.18)),
    ("Forest Scale", (0.18, 0.34, 0.22)),
    ("Storm Scale", (0.28, 0.30, 0.36)),
    ("Sand Scale", (0.60, 0.52, 0.36)),
]
LAYOUTS = ["Studio", "1-Bedroom", "2-Bedroom"]
MODEL_NAMES = [
    "Aurora", "Basalt", "Cirrus", "Delta", "Ember", "Fjord", "Grove",
    "Haven", "Iris", "Juniper", "Kestrel", "Lumen", "Meridian", "Nimbus",
    "Onyx", "Petra", "Quartz", "Rowan", "Solace", "Terra", "Umbra", "Vega",
]


@dataclass
class DomeSpec:
    serial: int = 1
    name: str = "Meridian"
    dtype: str = "home"
    radius: float = 4.0
    frequency: int = DOME_FREQ_DEFAULT
    layout: str = "1-Bedroom"
    cladding: str = "Slate Scale"
    cladding_color: tuple = (0.16, 0.34, 0.38)
    accent: tuple = (0.85, 0.65, 0.10)

    @property
    def type(self) -> DomeType:
        return DOME_TYPES[self.dtype]

    @property
    def stages(self):
        return self.type.stages

    @property
    def floor_radius(self) -> float:
        geo = build_geodesic(self.frequency)
        bz = geo.base_z
        return self.radius * math.sqrt(max(0.0, 1.0 - bz * bz))

    @property
    def floor_area(self) -> float:
        return math.pi * self.floor_radius ** 2

    @property
    def bedrooms(self) -> int:
        return {"Studio": 0, "1-Bedroom": 1, "2-Bedroom": 2}.get(
            self.layout, 0)

    @property
    def sale_price(self) -> float:
        t = self.type
        p = t.price_base + t.price_per_m2 * self.floor_area
        if self.dtype == "home":
            p += ASSUMPTIONS["layout_price"].get(self.layout, 0.0)
        return p

    @property
    def monthly_payment(self) -> float:
        return bhph_monthly(self.sale_price)


def bhph_monthly(price: float) -> float:
    a = ASSUMPTIONS
    principal = price * (1.0 - a["bhph_down_fraction"])
    r = a["bhph_apr"] / 12.0
    n = a["bhph_term_months"]
    if r <= 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def random_spec(serial, rng=None, dtype=None) -> DomeSpec:
    rng = rng or random
    dtype = dtype or rng.choice(["home", "home", "shed", "greenhouse",
                                 "shelter"])
    t = DOME_TYPES[dtype]
    cladding, color = rng.choice(CLADDINGS)
    freq = rng.choice(t.freq_choices)
    radius = round(rng.uniform(*t.radius_range), 2)
    layout = rng.choice(LAYOUTS) if dtype == "home" else "Studio"
    accent_choices = [(0.85, 0.65, 0.10), (0.20, 0.55, 0.85),
                      (0.85, 0.30, 0.25), (0.35, 0.70, 0.40),
                      (0.70, 0.45, 0.80)]
    name = f"{rng.choice(MODEL_NAMES)}-{rng.randint(10, 99)}"
    return DomeSpec(serial=serial, name=name, dtype=dtype, radius=radius,
                    frequency=freq, layout=layout, cladding=cladding,
                    cladding_color=color, accent=rng.choice(accent_choices))


# ---------------------------------------------------------------------------
# Element records + Catalog
# ---------------------------------------------------------------------------

@dataclass
class Element:
    stage: str
    category: str
    o0: int
    o1: int
    t0: int
    t1: int
    centroid: np.ndarray
    floor_point: np.ndarray
    material_cost: float
    labor_min: float
    weight: float
    label: str


class Catalog:
    def __init__(self, spec: DomeSpec):
        self.spec = spec
        self.stages = spec.stages
        self.b = MeshBuilder()
        self.elements: list[Element] = []
        self.by_stage: dict[str, list[Element]] = {
            s.key: [] for s in self.stages}
        self._o = self._t = self._v = 0
        self._cat = "frame"
        self._label = None

    def begin(self, category, label=None):
        self._cat = category
        self._label = label
        self._o = len(self.b.opaque)
        self._t = len(self.b.transparent)
        self._v = len(self.b.vertices)

    def end(self, stage, cost=None, labor=None, weight=None):
        verts = self.b.vertices[self._v:]
        if verts:
            pts = np.array([v[:3] for v in verts])
            centroid = pts.mean(axis=0)
            diag = float(np.linalg.norm(pts.max(0) - pts.min(0)))
        else:
            centroid = np.zeros(3)
            diag = 0.0
        base_cost, base_labor, base_weight = CATEGORY_ECON[self._cat]
        size = max(0.5, min(2.6, diag / 1.4)) if diag else 1.0
        floor_r = self.spec.floor_radius
        fx, fy = float(centroid[0]), float(centroid[1])
        d = math.hypot(fx, fy)
        if d > floor_r - 0.4 and d > 1e-6:
            s = (floor_r - 0.4) / d
            fx, fy = fx * s, fy * s
        if stage not in self.by_stage:
            self.by_stage[stage] = []
        el = Element(
            stage=stage, category=self._cat,
            o0=self._o, o1=len(self.b.opaque),
            t0=self._t, t1=len(self.b.transparent),
            centroid=centroid, floor_point=np.array([fx, fy, 0.0]),
            material_cost=(cost if cost is not None else base_cost * size),
            labor_min=(labor if labor is not None else base_labor * size),
            weight=(weight if weight is not None else base_weight * size),
            label=self._label or CATEGORY_LABEL.get(self._cat, self._cat))
        self.elements.append(el)
        self.by_stage[stage].append(el)

    def material_cost(self):
        return sum(e.material_cost for e in self.elements)

    def labor_minutes(self):
        return sum(e.labor_min for e in self.elements)

    def total_weight(self):
        return sum(e.weight for e in self.elements)

    def solar_panel_count(self):
        return len(self.by_stage.get("solar", []))

    def insulation_count(self):
        return len(self.by_stage.get("insulation", []))


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def polar(az_deg, r, z=0.0):
    a = math.radians(az_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def add_box(b, center, size, color, alpha=1.0, mat_id=MAT_PLAIN, yaw=0.0):
    cx, cy, cz = center
    hx, hy, hz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    ca, sa = math.cos(yaw), math.sin(yaw)

    def pt(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z)

    def nv(x, y, z):
        return (x * ca - y * sa, x * sa + y * ca, z)

    b.quad(pt(-hx, -hy, hz), pt(hx, -hy, hz), pt(hx, hy, hz),
           pt(-hx, hy, hz), nv(0, 0, 1), color, alpha, mat_id)
    b.quad(pt(-hx, hy, -hz), pt(hx, hy, -hz), pt(hx, -hy, -hz),
           pt(-hx, -hy, -hz), nv(0, 0, -1), color, alpha, mat_id)
    b.quad(pt(hx, -hy, -hz), pt(hx, hy, -hz), pt(hx, hy, hz),
           pt(hx, -hy, hz), nv(1, 0, 0), color, alpha, mat_id)
    b.quad(pt(-hx, hy, -hz), pt(-hx, -hy, -hz), pt(-hx, -hy, hz),
           pt(-hx, hy, hz), nv(-1, 0, 0), color, alpha, mat_id)
    b.quad(pt(hx, hy, -hz), pt(-hx, hy, -hz), pt(-hx, hy, hz),
           pt(hx, hy, hz), nv(0, 1, 0), color, alpha, mat_id)
    b.quad(pt(-hx, -hy, -hz), pt(hx, -hy, -hz), pt(hx, -hy, hz),
           pt(-hx, -hy, hz), nv(0, -1, 0), color, alpha, mat_id)


# ---------------------------------------------------------------------------
# Section emitters (shared across product lines)
# ---------------------------------------------------------------------------

def _emit_floor(cat, geo, floor_r):
    b = cat.b
    rim_segments = 24
    for group in range(6):
        cat.begin("floor")
        for i in range(group * 4, group * 4 + 4):
            a0 = 2 * math.pi * i / rim_segments
            a1 = 2 * math.pi * (i + 1) / rim_segments
            mid = (a0 + a1) * 0.5
            arc = floor_r * (a1 - a0)
            add_box(b, (floor_r * 0.985 * math.cos(mid),
                        floor_r * 0.985 * math.sin(mid), 0.15),
                    (arc * 1.02, 0.10, 0.30), (0.58, 0.44, 0.26),
                    mat_id=MAT_WOOD, yaw=mid + math.pi / 2)
        cat.end("floor")
    y = -floor_r + 0.45
    while y < floor_r - 0.35:
        half = math.sqrt(max(0.05, floor_r * floor_r - y * y))
        cat.begin("floor")
        add_box(b, (0.0, y, 0.17), (2 * half - 0.28, 0.09, 0.26),
                (0.62, 0.48, 0.28), mat_id=MAT_WOOD)
        cat.end("floor")
        y += 0.55
    cat.begin("floor", "Floor decking disc")
    b.cylinder((0, 0, 0.30), (0, 0, FLOOR_TOP), floor_r + 0.04, 40,
               (0.72, 0.60, 0.42), mat_id=MAT_DECK)
    cat.end("floor", cost=CATEGORY_ECON["floor"][0] * 4,
            labor=CATEGORY_ECON["floor"][1] * 3)


def _emit_frame(cat, geo, spt, color, mat, strut_r):
    b = cat.b
    edges = sorted(
        geo.edges,
        key=lambda e: (round(min(geo.verts[e[0]][2], geo.verts[e[1]][2]), 3),
                       math.atan2(geo.verts[e[0]][1] + geo.verts[e[1]][1],
                                  geo.verts[e[0]][0] + geo.verts[e[1]][0])))
    for i, j in edges:
        cat.begin("frame")
        b.cylinder(spt(geo.verts[i]), spt(geo.verts[j]), strut_r, 7, color,
                   mat_id=mat)
        cat.end("frame")
    hub_order = sorted(range(len(geo.verts)),
                       key=lambda k: round(geo.verts[k][2], 3))
    for g in range(0, len(hub_order), 6):
        cat.begin("hub")
        for k in hub_order[g:g + 6]:
            p = spt(geo.verts[k])
            n = normalize(np.array(geo.verts[k], dtype=np.float64))
            b.cylinder(p - n * 0.05, p + n * 0.07, strut_r * 1.9, 8,
                       (0.55, 0.57, 0.62), mat_id=MAT_METAL)
        cat.end("frame")


def _emit_apex_anchor(cat, R, base_z, apex_z, with_column):
    b = cat.b
    steel = (0.58, 0.61, 0.66)
    anchor_top = FLOOR_TOP + (1.0 - base_z) * (R + 0.24) + 0.14
    stage = "column" if with_column else "frame"
    cat.begin("frame", "Apex crane anchor")
    b.cylinder((0, 0, apex_z - 0.1), (0, 0, anchor_top), 0.09, 10,
               (0.45, 0.47, 0.52), mat_id=MAT_METAL)
    b.cylinder((0, 0, anchor_top), (0, 0, anchor_top + 0.06), 0.24, 12,
               (0.45, 0.47, 0.52), mat_id=MAT_METAL)
    eye_c = anchor_top + 0.28
    for i in range(12):
        a0 = 2 * math.pi * i / 12
        a1 = 2 * math.pi * (i + 1) / 12
        p0 = (0.17 * math.cos(a0), 0.0, eye_c + 0.17 * math.sin(a0))
        p1 = (0.17 * math.cos(a1), 0.0, eye_c + 0.17 * math.sin(a1))
        b.cylinder(p0, p1, 0.035, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    cat.end(stage, cost=180.0, labor=40.0)
    return anchor_top + 0.45


def _emit_column(cat, R, base_z, apex_z):
    b = cat.b
    steel = (0.58, 0.61, 0.66)
    cat.begin("column", "Column base plate")
    b.cylinder((0, 0, FLOOR_TOP - 0.02), (0, 0, FLOOR_TOP + 0.06), 0.34, 16,
               (0.40, 0.42, 0.46), mat_id=MAT_METAL)
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, apex_z), 0.14, 12, steel,
               mat_id=MAT_METAL)
    cat.end("column")
    cat.begin("column", "Column service risers")
    b.cylinder((0.16, 0.0, FLOOR_TOP), (0.16, 0.0, 2.3), 0.035, 6,
               (0.20, 0.40, 0.90))
    b.cylinder((-0.16, 0.0, FLOOR_TOP), (-0.16, 0.0, 2.3), 0.035, 6,
               (0.85, 0.20, 0.20))
    b.cylinder((0.0, 0.16, FLOOR_TOP), (0.0, 0.16, 2.3), 0.030, 6,
               (0.72, 0.72, 0.75), mat_id=MAT_METAL)
    cat.end("column")


def _emit_utilities(cat, floor_r):
    b = cat.b
    hot, cold, drain = (0.85, 0.20, 0.20), (0.20, 0.40, 0.90), (0.28,
                                                                0.28, 0.32)

    def fr(f):
        return f * floor_r

    cat.begin("water", "Central water manifold")
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, FLOOR_TOP + 0.12), 0.30, 14,
               (0.30, 0.42, 0.62), mat_id=MAT_METAL)
    cat.end("water")

    def water_run(az, r_target, color, radius, off, label):
        a = az + off
        cat.begin("water", label)
        p0 = polar(a, 0.32, FLOOR_TOP + 0.045)
        p1 = polar(a, r_target, FLOOR_TOP + 0.045)
        b.cylinder(p0, p1, radius, 6, color)
        b.cylinder(p1, (p1[0], p1[1], FLOOR_TOP + 0.32), radius, 6, color)
        cat.end("water")

    for az, rt, kinds, nm in ((150, fr(0.685), "hcd", "Kitchen"),
                              (40, fr(0.622), "hc", "Bath sink"),
                              (60, fr(0.635), "cd", "Toilet"),
                              (82, fr(0.596), "hcd", "Shower")):
        if "h" in kinds:
            water_run(az, rt, hot, 0.022, -3.5, f"{nm} hot PEX")
        if "c" in kinds:
            water_run(az, rt, cold, 0.022, 3.5, f"{nm} cold PEX")
        if "d" in kinds:
            water_run(az, rt, drain, 0.048, 0.0, f"{nm} drain")

    conduit = (0.72, 0.72, 0.75)
    cat.begin("power", "Main junction box")
    add_box(b, (0.0, -0.22, FLOOR_TOP + 0.55), (0.26, 0.12, 0.40),
            (0.42, 0.44, 0.48), mat_id=MAT_METAL)
    cat.end("power")
    for az in (0, 60, 120, 150, 180, 240, 300):
        cat.begin("power", "Floor power conduit")
        p0 = polar(az + 1.5, 0.30, FLOOR_TOP + 0.030)
        p1 = polar(az + 1.5, fr(0.850), FLOOR_TOP + 0.030)
        b.cylinder(p0, p1, 0.026, 6, conduit, mat_id=MAT_METAL)
        b.cylinder(p1, (p1[0], p1[1], FLOOR_TOP + 0.40), 0.026, 6, conduit,
                   mat_id=MAT_METAL)
        cat.end("power")


def _emit_fixtures(cat, floor_r):
    b = cat.b
    white = (0.95, 0.96, 0.97)
    hot, cold = (0.85, 0.20, 0.20), (0.20, 0.40, 0.90)

    def fr(f):
        return f * floor_r

    cat.begin("fixture", "Toilet")
    tx, ty, _ = polar(60, fr(0.635))
    add_box(b, (tx, ty, FLOOR_TOP + 0.21), (0.42, 0.38, 0.42), white,
            yaw=math.radians(60))
    add_box(b, (tx * 1.12, ty * 1.12, FLOOR_TOP + 0.55), (0.18, 0.44, 0.42),
            white, yaw=math.radians(60))
    b.cylinder((tx, ty, FLOOR_TOP + 0.42), (tx, ty, FLOOR_TOP + 0.46),
               0.20, 12, white)
    cat.end("fixtures")
    cat.begin("fixture", "Shower pan + valve")
    sx, sy, _ = polar(82, fr(0.596))
    add_box(b, (sx, sy, FLOOR_TOP + 0.05), (0.95, 0.95, 0.10),
            (0.80, 0.83, 0.86), yaw=math.radians(82))
    b.cylinder((sx, sy, FLOOR_TOP + 0.1), (sx, sy, FLOOR_TOP + 2.05),
               0.025, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
    b.cone((sx, sy, FLOOR_TOP + 1.98), (sx, sy, FLOOR_TOP + 1.86), 0.09, 10,
           (0.70, 0.72, 0.76))
    cat.end("fixtures")
    cat.begin("fixture", "Bath pedestal sink")
    bx, by, _ = polar(40, fr(0.622))
    b.cylinder((bx, by, FLOOR_TOP), (bx, by, FLOOR_TOP + 0.76), 0.07, 8, white)
    b.cylinder((bx, by, FLOOR_TOP + 0.76), (bx, by, FLOOR_TOP + 0.88), 0.20,
               12, white)
    cat.end("fixtures")
    cat.begin("fixture", "Kitchen rough-in cabinet")
    kx, ky, _ = polar(150, fr(0.685))
    add_box(b, (kx, ky, FLOOR_TOP + 0.44), (0.62, 0.55, 0.88),
            (0.62, 0.64, 0.68), mat_id=MAT_METAL, yaw=math.radians(150))
    cat.end("fixtures")
    for group in ((0, 60, 120), (180, 240, 300)):
        cat.begin("fixture", "Perimeter wall outlets")
        for az in group:
            px, py, _ = polar(az + 1.5, fr(0.850))
            add_box(b, (px, py, FLOOR_TOP + 0.50), (0.09, 0.09, 0.30),
                    (0.30, 0.32, 0.36), yaw=math.radians(az))
            add_box(b, (px, py, FLOOR_TOP + 0.70), (0.10, 0.12, 0.16),
                    white, yaw=math.radians(az))
        cat.end("fixtures")
    cat.begin("fixture", "Column outlets + breaker panel")
    for az in (45, 135, 225, 315):
        px, py, _ = polar(az, 0.17)
        add_box(b, (px, py, FLOOR_TOP + 0.55), (0.10, 0.13, 0.18), white,
                yaw=math.radians(az))
    bxp, byp, _ = polar(150, 0.18)
    add_box(b, (bxp, byp, FLOOR_TOP + 1.45), (0.08, 0.34, 0.50),
            (0.80, 0.82, 0.85), mat_id=MAT_METAL, yaw=math.radians(150))
    cat.end("fixtures")


def _sorted_faces(geo):
    return sorted(
        (tuple(f) for f in geo.faces),
        key=lambda f: (round(sum(geo.verts[i][2] for i in f) / 3.0, 3),
                       math.atan2(sum(geo.verts[i][1] for i in f),
                                  sum(geo.verts[i][0] for i in f))))


def _emit_shell(cat, geo, faces, spt, stage, category, d, color, alpha=1.0,
                mat_id=MAT_PLAIN, shrink=1.0, face_filter=None):
    b = cat.b
    for f in faces:
        c_unit = np.mean([geo.verts[i] for i in f], axis=0)
        if face_filter and not face_filter(normalize(c_unit)):
            continue
        pts = [spt(geo.verts[i], d) for i in f]
        centroid = np.mean(pts, axis=0)
        pts = [centroid + (p - centroid) * shrink for p in pts]
        for p in pts:
            p[2] = max(p[2], FLOOR_TOP + 0.01)
        cat.begin(category)
        b.triangle(pts[0], pts[1], pts[2], color, alpha, mat_id)
        cat.end(stage)


def _emit_hatch(cat, R, base_z, door_color=(0.62, 0.64, 0.68),
                cost_scale=1.0):
    b = cat.b
    hc, hl = CATEGORY_ECON["hatch"][0] * cost_scale, \
        CATEGORY_ECON["hatch"][1] * cost_scale
    rh = R + 0.19
    z_center = min(1.25, FLOOR_TOP + (1.0 - base_z) * R * 0.55)
    u = (z_center - FLOOR_TOP) / rh + base_z
    horiz = math.sqrt(max(0.05, 1.0 - u * u))
    hpos = np.array([0.0, -horiz * rh, z_center])
    n = normalize(np.array([0.0, -horiz, u]))
    right = normalize(np.cross(np.array([0.0, 0.0, 1.0]), n))
    up = normalize(np.cross(n, right))
    sc = min(1.0, R / 4.0 + 0.35)

    def hpt(a, s=1.0, out=0.0):
        return (hpos + right * (0.56 * s * sc * math.cos(a))
                + up * (0.86 * s * sc * math.sin(a)) + n * out)

    cat.begin("hatch", "Hatch coaming ring")
    for i in range(18):
        a0, a1 = 2 * math.pi * i / 18, 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 1.0, 0.05), hpt(a1, 1.0, 0.05), 0.05, 6,
                   (0.36, 0.39, 0.44), mat_id=MAT_METAL)
    cat.end("hatch", cost=hc * 0.35, labor=hl * 0.35)
    cat.begin("hatch", "Hatch door leaf + gasket")
    center = hpos + n * 0.09
    for i in range(18):
        a0, a1 = 2 * math.pi * i / 18, 2 * math.pi * (i + 1) / 18
        b.triangle(center, hpt(a0, 0.93, 0.09), hpt(a1, 0.93, 0.09),
                   door_color, mat_id=MAT_METAL, normal=n)
    for i in range(18):
        a0, a1 = 2 * math.pi * i / 18, 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 0.95, 0.07), hpt(a1, 0.95, 0.07), 0.022, 5,
                   (0.10, 0.10, 0.12))
    cat.end("hatch", cost=hc * 0.4, labor=hl * 0.4)
    cat.begin("hatch", "Hatch dogs + locking wheel")
    wc = hpos + n * 0.20
    for i in range(12):
        a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
        p0 = wc + right * (0.22 * sc * math.cos(a0)) + up * (0.22 * sc
                                                             * math.sin(a0))
        p1 = wc + right * (0.22 * sc * math.cos(a1)) + up * (0.22 * sc
                                                             * math.sin(a1))
        b.cylinder(p0, p1, 0.028, 6, (0.78, 0.80, 0.84), mat_id=MAT_METAL)
    b.sphere(wc, 0.05, (0.78, 0.80, 0.84), rings=4, sides=8)
    cat.end("hatch", cost=hc * 0.25, labor=hl * 0.25)


def _emit_interior(cat, spec, floor_r):
    b = cat.b
    wall = (0.90, 0.90, 0.86)

    def fr(f):
        return f * floor_r

    def wall_run(az, segs, label):
        a = math.radians(az)
        cat.begin("furniture", label)
        for r0f, r1f in segs:
            r0, r1 = fr(r0f), fr(r1f)
            rc = (r0 + r1) * 0.5
            add_box(b, (rc * math.cos(a), rc * math.sin(a), FLOOR_TOP + 1.10),
                    (r1 - r0, 0.08, 2.20), wall, yaw=a)
        cat.end("interior")

    wall_run(30, [(0.10, 0.24), (0.44, 0.74)], "Bathroom partition")
    wall_run(90, [(0.10, 0.74)], "Bathroom partition")
    if spec.bedrooms >= 1:
        wall_run(300, [(0.10, 0.74)], "Bedroom partition")
        wall_run(0, [(0.10, 0.24), (0.44, 0.74)], "Bedroom partition")
    if spec.bedrooms >= 2:
        wall_run(258, [(0.10, 0.74)], "Second-bedroom partition")
        wall_run(222, [(0.10, 0.24), (0.44, 0.74)], "Second-bedroom door")

    cabinet, counter = (0.45, 0.32, 0.20), (0.85, 0.84, 0.80)
    for az in (140, 163):
        cat.begin("furniture", "Kitchen counter run")
        cx, cy, _ = polar(az, fr(0.761))
        yaw = math.radians(az + 90)
        add_box(b, (cx, cy, FLOOR_TOP + 0.45), (1.45, 0.62, 0.90), cabinet,
                mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (cx, cy, FLOOR_TOP + 0.925), (1.55, 0.68, 0.05), counter,
                yaw=yaw)
        cat.end("interior")
    cat.begin("furniture", "Refrigerator")
    fx, fy, _ = polar(126, fr(0.736))
    add_box(b, (fx, fy, FLOOR_TOP + 0.925), (0.75, 0.70, 1.85),
            (0.75, 0.78, 0.80), mat_id=MAT_METAL, yaw=math.radians(216))
    cat.end("interior")
    cat.begin("furniture", "Range / stove")
    ox, oy, _ = polar(177, fr(0.749))
    add_box(b, (ox, oy, FLOOR_TOP + 0.45), (0.62, 0.62, 0.90),
            (0.22, 0.23, 0.26), mat_id=MAT_METAL, yaw=math.radians(267))
    cat.end("interior")
    if spec.bedrooms >= 1:
        cat.begin("furniture", "Primary bed")
        bx, by, _ = polar(332, fr(0.558))
        yaw = math.radians(332 + 90)
        add_box(b, (bx, by, FLOOR_TOP + 0.18), (1.45, 2.00, 0.32),
                (0.48, 0.36, 0.22), mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (bx, by, FLOOR_TOP + 0.45), (1.38, 1.92, 0.22),
                (0.93, 0.93, 0.95), yaw=yaw)
        cat.end("interior")
        cat.begin("furniture", "Wardrobe + nightstand")
        wx, wy, _ = polar(297, fr(0.685))
        add_box(b, (wx, wy, FLOOR_TOP + 0.95), (1.20, 0.60, 1.90),
                (0.50, 0.38, 0.24), mat_id=MAT_WOOD, yaw=math.radians(297+90))
        nx, ny, _ = polar(352, fr(0.647))
        b.sphere((nx, ny, FLOOR_TOP + 0.80), 0.11, (1.00, 0.88, 0.55),
                 mat_id=MAT_EMISSIVE, rings=4, sides=8)
        cat.end("interior")
    if spec.bedrooms >= 2:
        cat.begin("furniture", "Second bed")
        bx, by, _ = polar(240, fr(0.558))
        yaw = math.radians(240 + 90)
        add_box(b, (bx, by, FLOOR_TOP + 0.18), (1.30, 1.90, 0.32),
                (0.48, 0.36, 0.22), mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (bx, by, FLOOR_TOP + 0.42), (1.24, 1.82, 0.20),
                (0.90, 0.92, 0.96), yaw=yaw)
        cat.end("interior")
    cat.begin("furniture", "Shower enclosure glass")
    gx, gy, _ = polar(82, fr(0.596))
    ga = math.radians(82)
    for side in (-1, 1):
        px = gx + 0.48 * side * math.cos(ga + math.pi / 2)
        py = gy + 0.48 * side * math.sin(ga + math.pi / 2)
        add_box(b, (px, py, FLOOR_TOP + 1.05), (0.95, 0.03, 1.90),
                (0.75, 0.88, 0.90), alpha=0.30, mat_id=MAT_GLASS, yaw=ga)
    cat.end("interior")
    cat.begin("furniture", "Dining table + stools")
    dx, dy, _ = polar(218, fr(0.495))
    b.cylinder((dx, dy, FLOOR_TOP), (dx, dy, FLOOR_TOP + 0.72), 0.05, 8,
               (0.35, 0.37, 0.40), mat_id=MAT_METAL)
    b.cylinder((dx, dy, FLOOR_TOP + 0.72), (dx, dy, FLOOR_TOP + 0.77), 0.50,
               16, (0.60, 0.46, 0.28), mat_id=MAT_WOOD)
    cat.end("interior")


def _emit_grow(cat, floor_r):
    """Greenhouse benches, plants, and ridge vents."""
    b = cat.b

    def fr(f):
        return f * floor_r
    for az in (30, 90, 150, 210, 270, 330):
        cat.begin("grow", "Grow bench + trays")
        cx, cy, _ = polar(az, fr(0.62))
        yaw = math.radians(az + 90)
        add_box(b, (cx, cy, FLOOR_TOP + 0.42), (1.6, 0.7, 0.06),
                (0.45, 0.34, 0.22), mat_id=MAT_WOOD, yaw=yaw)
        for leg in (-0.7, 0.7):
            lx = cx + leg * math.cos(yaw)
            ly = cy + leg * math.sin(yaw)
            b.cylinder((lx, ly, FLOOR_TOP), (lx, ly, FLOOR_TOP + 0.42),
                       0.04, 6, (0.4, 0.42, 0.45), mat_id=MAT_METAL)
        for k in range(3):
            px = cx + (k - 1) * 0.42 * math.cos(yaw)
            py = cy + (k - 1) * 0.42 * math.sin(yaw)
            b.sphere((px, py, FLOOR_TOP + 0.58), 0.16, (0.20, 0.55, 0.24),
                     rings=4, sides=8)
        cat.end("grow")
    cat.begin("grow", "Irrigation manifold")
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, FLOOR_TOP + 0.5), 0.06, 8,
               (0.4, 0.6, 0.8), mat_id=MAT_METAL)
    cat.end("grow")


def _emit_shelterkit(cat, floor_r):
    b = cat.b

    def fr(f):
        return f * floor_r
    cat.begin("shelter_kit", "Bench seating")
    for az in (200, 340):
        cx, cy, _ = polar(az, fr(0.55))
        yaw = math.radians(az + 90)
        add_box(b, (cx, cy, FLOOR_TOP + 0.22), (1.2, 0.45, 0.44),
                (0.45, 0.42, 0.40), mat_id=MAT_METAL, yaw=yaw)
        cat.end("shelter_kit") if az == 340 else cat.begin(
            "shelter_kit", "Bench seating")
    cat.begin("shelter_kit", "Air vent + supplies")
    b.cylinder((0, 0, FLOOR_TOP + 0.9), (0, 0, FLOOR_TOP + 1.6), 0.10, 8,
               (0.6, 0.62, 0.66), mat_id=MAT_METAL)
    add_box(b, (fr(0.3), fr(0.3), FLOOR_TOP + 0.2), (0.4, 0.4, 0.4),
            (0.8, 0.5, 0.2))
    cat.end("shelter_kit")


# ---------------------------------------------------------------------------
# The dispatcher
# ---------------------------------------------------------------------------

def build_dome_catalog(spec: DomeSpec):
    t = spec.type
    geo = build_geodesic(spec.frequency)
    base_z = geo.base_z
    R = spec.radius
    floor_r = R * math.sqrt(max(0.0, 1.0 - base_z * base_z))
    apex_z = FLOOR_TOP + (1.0 - base_z) * R

    def spt(v, d=0.0):
        r = R + d
        return np.array([v[0] * r, v[1] * r, (v[2] - base_z) * r + FLOOR_TOP])

    cat = Catalog(spec)
    faces = _sorted_faces(geo)
    keys = set(t.stage_keys)

    _emit_floor(cat, geo, floor_r)
    _emit_frame(cat, geo, spt, t.frame_color, t.frame_mat, t.strut_radius)

    with_column = "column" in keys
    anchor_top = _emit_apex_anchor(cat, R, base_z, apex_z, with_column)
    if with_column:
        _emit_column(cat, R, base_z, apex_z)
    if "water" in keys or "power" in keys:
        _emit_utilities(cat, floor_r)
    if "fixtures" in keys:
        _emit_fixtures(cat, floor_r)

    # shell layers per product line
    if "insulation" in keys:
        _emit_shell(cat, geo, faces, spt, "insulation", "insulation", -0.03,
                    (0.93, 0.45, 0.55), mat_id=MAT_CANVAS, shrink=0.80)
    if "sheetrock" in keys:
        _emit_shell(cat, geo, faces, spt, "sheetrock", "sheetrock", -0.10,
                    (0.92, 0.92, 0.88))
    if "osb" in keys:
        _emit_shell(cat, geo, faces, spt, "osb", "osb", 0.07,
                    (0.80, 0.68, 0.42), mat_id=MAT_CONCRETE, shrink=0.985)
    if "wrap" in keys:
        _emit_shell(cat, geo, faces, spt, "wrap", "wrap", 0.105,
                    (0.84, 0.85, 0.87), mat_id=MAT_SHEETING)
    if "shingles" in keys:
        _emit_shell(cat, geo, faces, spt, "shingles", "shingle", 0.14,
                    spec.cladding_color, mat_id=MAT_SHINGLE)
    if "sheetmetal" in keys:
        _emit_shell(cat, geo, faces, spt, "sheetmetal", "sheetmetal", 0.06,
                    (0.66, 0.68, 0.72), mat_id=MAT_METAL, shrink=0.99)
    if "glazing" in keys:
        _emit_shell(cat, geo, faces, spt, "glazing", "glazing", 0.05,
                    (0.72, 0.86, 0.90), alpha=0.34, mat_id=MAT_GLASS,
                    shrink=0.94)
    if "steelplate" in keys:
        _emit_shell(cat, geo, faces, spt, "steelplate", "steelplate", 0.05,
                    (0.40, 0.44, 0.50), mat_id=MAT_METAL, shrink=1.0)
    if "fiberglass" in keys:
        _emit_shell(cat, geo, faces, spt, "fiberglass", "fiberglass", 0.19,
                    (0.72, 0.85, 0.88), alpha=0.30, mat_id=MAT_GLASS)
        cat.begin("fiberglass", "Fiberglass floor skirt")
        cat.b.cylinder((0, 0, 0.02), (0, 0, FLOOR_TOP + 0.12), floor_r + 0.20,
                       40, (0.72, 0.85, 0.88), alpha=0.30, mat_id=MAT_GLASS,
                       cap_ends=False)
        cat.end("fiberglass")

    if "hatch" in keys:
        door = (0.42, 0.45, 0.52) if spec.dtype == "shelter" \
            else (0.62, 0.64, 0.68)
        # A storage shed gets a plain barn door, not a $2k marine hatch.
        scale = 0.18 if spec.dtype == "shed" else 1.0
        _emit_hatch(cat, R, base_z, door, cost_scale=scale)
    if "interior" in keys:
        _emit_interior(cat, spec, floor_r)
    if "grow" in keys:
        _emit_grow(cat, floor_r)
    if "shelterkit" in keys:
        _emit_shelterkit(cat, floor_r)
    if "solar" in keys:
        _emit_shell(cat, geo, faces, spt, "solar", "solar", 0.23,
                    (0.10, 0.15, 0.32), mat_id=MAT_SOLAR, shrink=0.86,
                    face_filter=lambda c: (-c[1]) > 0.40 and 0.10 < c[2]
                    < 0.74)

    info = {"floor_r": floor_r, "apex_z": apex_z, "anchor_top": anchor_top,
            "base_z": base_z}
    return cat, info


def build_finished_dome_mesh(dtype="home", frequency=DOME_FREQ_DEFAULT):
    t = DOME_TYPES[dtype]
    r = min(t.radius_range[1], REFERENCE_RADIUS)
    spec = DomeSpec(dtype=dtype, radius=r, frequency=frequency)
    cat, _ = build_dome_catalog(spec)
    return cat.b.build()


# ===========================================================================
# Business math
# ===========================================================================

def unit_economics(cat, spec, labor_hours=None):
    a = ASSUMPTIONS
    material = cat.material_cost()
    if labor_hours is None:
        labor_hours = cat.labor_minutes() / 60.0
    labor_cost = labor_hours * a["burdened_wage_per_hour"]
    overhead = labor_hours * a["overhead_per_labor_hour"]
    total_cost = material + labor_cost + overhead
    price = spec.sale_price
    margin = price - total_cost
    return {"material": material, "labor_hours": labor_hours,
            "labor_cost": labor_cost, "overhead": overhead,
            "total_cost": total_cost, "price": price, "margin": margin,
            "margin_pct": (margin / price * 100.0) if price else 0.0}


def station_cycle_times(cat, crew=None):
    a = ASSUMPTIONS
    crew = crew or a["workers_per_station"]
    crew = max(1, crew)
    rows = []
    for stage in cat.stages:
        els = cat.by_stage.get(stage.key, [])
        labor_min = sum(e.labor_min for e in els)
        rows.append({"key": stage.key, "title": stage.title,
                     "elements": len(els), "labor_min": labor_min,
                     "cycle_min": labor_min / crew})
    return rows


def throughput(cat, crew=None):
    a = ASSUMPTIONS
    rows = station_cycle_times(cat, crew)
    active = [r for r in rows if r["cycle_min"] > 0] or rows
    bottleneck = max(active, key=lambda r: r["cycle_min"])
    total_cycle = sum(r["cycle_min"] for r in rows)
    minutes_per_day = a["shift_hours_per_day"] * 60.0
    single = minutes_per_day / total_cycle if total_cycle else 0.0
    pipe = (minutes_per_day / bottleneck["cycle_min"]
            if bottleneck["cycle_min"] else 0.0)
    return {"rows": rows, "bottleneck": bottleneck,
            "total_cycle_min": total_cycle,
            "single_flow_per_day": single,
            "single_flow_per_year": single * a["work_days_per_year"],
            "pipelined_per_day": pipe,
            "pipelined_per_year": pipe * a["work_days_per_year"]}


def break_even(avg_margin, avg_overhead=None):
    a = ASSUMPTIONS
    fixed_year = a["fixed_overhead_per_month"] * 12.0
    if avg_overhead is None:
        capex_year = a["line_capex"] / a["capex_amortize_years"]
        avg_overhead = ((capex_year + fixed_year)
                        / max(1, a["target_units_per_year"]))
    contribution = max(1.0, avg_margin + avg_overhead)
    return {"capex": a["line_capex"], "fixed_year": fixed_year,
            "contribution_per_unit": contribution,
            "units_to_recover_capex": a["line_capex"] / contribution,
            "units_to_cover_annual_fixed": fixed_year / contribution}


def benchmark(cat, spec, econ, build_days, labor_hours):
    a = ASSUMPTIONS
    return {"dome": {"name": spec.name, "price": econ["price"],
                     "material": econ["material"],
                     "labor_hours": labor_hours, "build_days": build_days},
            "conventional": {"name": a["benchmark_name"],
                             "price": a["benchmark_price"],
                             "material": a["benchmark_material_cost"],
                             "labor_hours": a["benchmark_labor_hours"],
                             "build_days": a["benchmark_build_days"]}}


def product_value(cat, spec):
    a = ASSUMPTIONS
    panels = cat.solar_panel_count()
    solar_kw = panels * a["solar_watts_per_panel"] / 1000.0
    daily_gen = solar_kw * 4.5 * 1.25
    autonomy = a["battery_kwh"] / max(0.1, a["daily_load_kwh"])
    r_value = 12.0 + cat.insulation_count() * a["insulation_r_per_element"]
    carbon = cat.total_weight() * a["carbon_kg_per_kg_material"]
    return {"solar_kw": solar_kw, "solar_panels": panels,
            "daily_generation_kwh": daily_gen,
            "net_daily_kwh": daily_gen - a["daily_load_kwh"],
            "battery_kwh": a["battery_kwh"], "autonomy_days": autonomy,
            "r_value": r_value, "embodied_carbon_kg": carbon,
            "osha_target": a["osha_incident_rate_target"],
            "floor_area": spec.floor_area}


def scale_scenarios(single_per_year, avg_margin, avg_price):
    a = ASSUMPTIONS
    out = []
    for lines in (1, 3, 6):
        units = single_per_year * lines
        out.append({"lines": lines, "units_per_year": units,
                    "revenue": units * avg_price,
                    "gross_profit": units * avg_margin,
                    "capex": a["line_capex"] * lines})
    return out
