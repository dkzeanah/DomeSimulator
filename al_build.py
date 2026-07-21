"""
Dome-home assembly line — build geometry, economics, and labor model.

This module is deliberately free of any OpenGL / windowing code so the
whole cost-and-labor model can be exercised head-less (see
``assembly_line.py --selftest``). It provides three things:

1.  A parametric :class:`DomeSpec` and :func:`build_dome_catalog`, which
    emit the dome geometry **element by element**. Every element records
    where it is placed, what it costs in materials, and how many
    labor-minutes it takes to install — so the runtime can walk a worker
    to it, accrue real cost, and reveal it only once "placed".

2.  A single, clearly-labeled :data:`ASSUMPTIONS` block holding every
    dollar and time figure the investor demo depends on. These are
    editable estimates, not gospel — change them here and the entire P&L,
    break-even, throughput, and benchmark story updates.

3.  Derived business math: per-dome unit economics, line throughput and
    bottleneck analysis, a break-even model, a comparison against
    conventional manufactured housing, and the finished product's value
    story (solar output, insulation R-value, off-grid autonomy).

Nothing here draws anything; it returns plain data and small meshes.
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
# These are defensible planning estimates; edit them to match your model.
# ===========================================================================

ASSUMPTIONS = {
    # --- labor -----------------------------------------------------------
    "burdened_wage_per_hour": 46.0,     # wage + benefits + payroll burden
    "install_crew_size": 4,             # workers placing elements per dome
    "worker_stride_m": 0.76,            # average human step length
    "worker_walk_speed_mps": 1.30,      # average walking speed on a plant floor
    "hand_place_seconds": 6.0,          # baseline per-element handling overhead
    "shift_hours_per_day": 8.0,
    "work_days_per_year": 250,

    # --- fixed / capital -------------------------------------------------
    "line_capex": 2_400_000.0,          # gantries, crane, turntable, tooling, fit
    "capex_amortize_years": 7.0,
    "fixed_overhead_per_month": 85_000.0,  # rent, utilities, admin, insurance
    "target_units_per_year": 300,       # planning volume for overhead allocation

    # --- product pricing (base; scaled by size & layout) -----------------
    "sale_price_base": 52_000.0,
    "sale_price_per_m2": 820.0,         # added value per m² of floor area
    "layout_price": {                   # premium by interior configuration
        "Studio": 0.0,
        "1-Bedroom": 8_000.0,
        "2-Bedroom": 16_000.0,
    },

    # --- comparison baseline (conventional manufactured home) ------------
    "benchmark_name": "Conventional manufactured home",
    "benchmark_price": 128_000.0,
    "benchmark_build_days": 34,
    "benchmark_labor_hours": 640.0,
    "benchmark_material_cost": 58_000.0,

    # --- product value story --------------------------------------------
    "solar_watts_per_panel": 340.0,     # per solar-skin element
    "battery_kwh": 20.0,                # standard pack for autonomy math
    "daily_load_kwh": 14.0,             # typical all-electric dome home
    "insulation_r_per_element": 0.28,   # contribution to whole-shell R-value
    "carbon_kg_per_kg_material": 1.7,   # embodied CO2e factor
    "osha_incident_rate_target": 1.8,   # recordables per 100 workers/year

    # --- QC / risk -------------------------------------------------------
    "first_pass_yield": 0.94,           # fraction needing no rework
    "rework_cost_fraction": 0.06,       # of unit cost, when reworked
}

# Per-category unit economics: (material $ per element, labor-minutes per
# element, weight kg per element). Scaled per element by its physical size,
# so a long strut costs more than a short one. Calibrated so a mid-size
# dome lands near real manufactured-home materials/labor.
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
    "hatch":       (2100.0, 180.0, 140.0),   # the sealed marine hatch assembly
    "furniture":   (430.0, 36.0, 55.0),
    "solar":       (150.0, 19.0, 11.0),
}

# Human-readable element labels for the click-to-inspect tooltip.
CATEGORY_LABEL = {
    "floor": "Floor joist / decking",
    "frame": "Geodesic strut",
    "hub": "Hub connector set",
    "column": "Utility column section",
    "water": "Water line run",
    "power": "Power conduit run",
    "fixture": "Plumbing fixture / outlet",
    "insulation": "Insulation batt",
    "sheetrock": "Sheetrock panel",
    "osb": "OSB sheathing panel",
    "wrap": "Water-barrier membrane",
    "shingle": "Shingle-scale course",
    "fiberglass": "Fiberglass encasement",
    "hatch": "Watertight hatch assembly",
    "furniture": "Interior fit-out item",
    "solar": "Solar skin panel",
}

# ---------------------------------------------------------------------------
# Stage definitions (the 15 stations, in build order)
# ---------------------------------------------------------------------------


@dataclass
class StageDef:
    key: str
    title: str
    desc: str
    color: tuple


STAGES = [
    StageDef("floor", "FLOOR FRAMING",
             "Wood floor built into the base ring: rim, joists, decking",
             (0.72, 0.55, 0.30)),
    StageDef("frame", "DOME SHELL FRAMING",
             "Geodesic timber frame raised from the base ring to the apex",
             (0.82, 0.62, 0.28)),
    StageDef("column", "CENTER UTILITY COLUMN",
             "Floor-to-apex service column + exterior crane anchor at the top",
             (0.60, 0.63, 0.68)),
    StageDef("water", "WATER LINES",
             "Hot / cold PEX and drains through the floor, terminating "
             "centrally at the column", (0.25, 0.50, 0.90)),
    StageDef("power", "POWER LINES",
             "Electrical conduit through the floor, terminating at the column",
             (0.95, 0.80, 0.20)),
    StageDef("fixtures", "FIXTURES & OUTLETS",
             "Plumbing fixtures set; outlets on the column and perimeter",
             (0.88, 0.90, 0.94)),
    StageDef("insulation", "INSULATION",
             "Insulation batts packed into every frame bay",
             (0.94, 0.52, 0.62)),
    StageDef("sheetrock", "SHEETROCK",
             "Interior shell sheetrocked", (0.90, 0.90, 0.85)),
    StageDef("osb", "OSB SHEATHING",
             "OSB panel board covering the dome exterior",
             (0.84, 0.70, 0.44)),
    StageDef("wrap", "WATER BARRIER",
             "Sill / water membrane wrapped over the OSB",
             (0.60, 0.64, 0.72)),
    StageDef("shingles", "SHINGLE SCALES",
             "Plastic scale shingles — the mechanical water barrier",
             (0.20, 0.40, 0.45)),
    StageDef("fiberglass", "FIBERGLASS ENCASEMENT",
             "The entire structure encased in a watertight fiberglass shell",
             (0.62, 0.85, 0.90)),
    StageDef("hatch", "WATERTIGHT HATCH DOOR",
             "Sealed marine-style hatch — the home's only opening, zero "
             "windows", (0.52, 0.56, 0.62)),
    StageDef("interior", "KITCHEN / BATH / BEDROOM",
             "Complete kitchen, bathroom and bedroom fit-out",
             (0.68, 0.50, 0.80)),
    StageDef("solar", "SOLAR ARRAY",
             "Solar skin applied to the sun-facing band + final QC",
             (0.15, 0.28, 0.60)),
]
STAGE_INDEX = {s.key: i for i, s in enumerate(STAGES)}

DOME_FREQ_DEFAULT = 3
FLOOR_TOP = 0.35            # dome-local z of the finished deck surface
REFERENCE_RADIUS = 4.0     # radius the yard/finished mesh is modeled at


# ---------------------------------------------------------------------------
# Dome specification (randomized per production run)
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
    radius: float = 4.0
    frequency: int = DOME_FREQ_DEFAULT
    layout: str = "1-Bedroom"
    cladding: str = "Slate Scale"
    cladding_color: tuple = (0.16, 0.34, 0.38)
    accent: tuple = (0.85, 0.65, 0.10)

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
        return {"Studio": 0, "1-Bedroom": 1, "2-Bedroom": 2}[self.layout]

    @property
    def sale_price(self) -> float:
        a = ASSUMPTIONS
        return (a["sale_price_base"]
                + a["sale_price_per_m2"] * self.floor_area
                + a["layout_price"][self.layout])


def random_spec(serial: int, rng: random.Random | None = None) -> DomeSpec:
    rng = rng or random
    cladding, color = rng.choice(CLADDINGS)
    # Frequency 3 and 4 only: a 2V dome has too few elements for its floor
    # area, which distorts the area-based price into an unrealistic margin.
    freq = rng.choice([3, 3, 4])
    radius = round(rng.uniform(3.2, 4.6), 2)
    layout = rng.choice(LAYOUTS)
    accent_choices = [(0.85, 0.65, 0.10), (0.20, 0.55, 0.85),
                      (0.85, 0.30, 0.25), (0.35, 0.70, 0.40),
                      (0.70, 0.45, 0.80)]
    name = f"{rng.choice(MODEL_NAMES)}-{rng.randint(10, 99)}"
    return DomeSpec(serial=serial, name=name, radius=radius, frequency=freq,
                    layout=layout, cladding=cladding, cladding_color=color,
                    accent=rng.choice(accent_choices))


# ---------------------------------------------------------------------------
# Element records and the Catalog that collects them
# ---------------------------------------------------------------------------

@dataclass
class Element:
    stage: str
    category: str
    o0: int
    o1: int
    t0: int
    t1: int
    centroid: np.ndarray            # dome-local placement point
    floor_point: np.ndarray         # where the worker stands (on the floor)
    material_cost: float
    labor_min: float
    weight: float
    label: str


class Catalog:
    """Collects dome geometry as discrete, costed, locatable elements."""

    def __init__(self, spec: DomeSpec):
        self.spec = spec
        self.b = MeshBuilder()
        self.elements: list[Element] = []
        self.by_stage: dict[str, list[Element]] = {s.key: [] for s in STAGES}
        self._o = 0
        self._t = 0
        self._v = 0
        self._cat = "frame"
        self._label = None

    def begin(self, category: str, label: str | None = None):
        self._cat = category
        self._label = label
        self._o = len(self.b.opaque)
        self._t = len(self.b.transparent)
        self._v = len(self.b.vertices)

    def end(self, stage: str, cost=None, labor=None, weight=None):
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
        fx = float(centroid[0])
        fy = float(centroid[1])
        d = math.hypot(fx, fy)
        if d > floor_r - 0.4 and d > 1e-6:      # keep worker on the deck
            s = (floor_r - 0.4) / d
            fx, fy = fx * s, fy * s
        el = Element(
            stage=stage, category=self._cat,
            o0=self._o, o1=len(self.b.opaque),
            t0=self._t, t1=len(self.b.transparent),
            centroid=centroid,
            floor_point=np.array([fx, fy, 0.0]),
            material_cost=(cost if cost is not None else base_cost * size),
            labor_min=(labor if labor is not None else base_labor * size),
            weight=(weight if weight is not None else base_weight * size),
            label=self._label or CATEGORY_LABEL.get(self._cat, self._cat),
        )
        self.elements.append(el)
        self.by_stage[stage].append(el)

    # -- aggregate economics --------------------------------------------

    def material_cost(self) -> float:
        return sum(e.material_cost for e in self.elements)

    def labor_minutes(self) -> float:
        return sum(e.labor_min for e in self.elements)

    def total_weight(self) -> float:
        return sum(e.weight for e in self.elements)

    def solar_panel_count(self) -> int:
        return len(self.by_stage["solar"])

    def insulation_count(self) -> int:
        return len(self.by_stage["insulation"])


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
# The full dome, emitted element by element
# ---------------------------------------------------------------------------

def build_dome_catalog(spec: DomeSpec):
    """The complete dome in dome-local space, as costed elements.

    Origin at the carriage deck center; +X points down the line; the
    hatch and solar band face -Y."""
    geo = build_geodesic(spec.frequency)
    base_z = geo.base_z
    R = spec.radius
    floor_r = R * math.sqrt(max(0.0, 1.0 - base_z * base_z))
    apex_z = FLOOR_TOP + (1.0 - base_z) * R

    def fr(frac):
        return frac * floor_r

    def spt(v, d=0.0):
        r = R + d
        return np.array([v[0] * r, v[1] * r, (v[2] - base_z) * r + FLOOR_TOP])

    cat = Catalog(spec)
    b = cat.b

    # ---- Station 1: floor framing --------------------------------------
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

    # ---- Station 2: dome shell framing ---------------------------------
    edges = sorted(
        geo.edges,
        key=lambda e: (round(min(geo.verts[e[0]][2], geo.verts[e[1]][2]), 3),
                       math.atan2(geo.verts[e[0]][1] + geo.verts[e[1]][1],
                                  geo.verts[e[0]][0] + geo.verts[e[1]][0])))
    wood = (0.55, 0.42, 0.26)
    for i, j in edges:
        cat.begin("frame")
        b.cylinder(spt(geo.verts[i]), spt(geo.verts[j]), 0.052, 7, wood,
                   mat_id=MAT_WOOD)
        cat.end("frame")
    hub_order = sorted(range(len(geo.verts)),
                       key=lambda k: round(geo.verts[k][2], 3))
    for g in range(0, len(hub_order), 6):
        cat.begin("hub")
        for k in hub_order[g:g + 6]:
            p = spt(geo.verts[k])
            n = normalize(np.array(geo.verts[k], dtype=np.float64))
            b.cylinder(p - n * 0.05, p + n * 0.07, 0.10, 8,
                       (0.55, 0.57, 0.62), mat_id=MAT_METAL)
        cat.end("frame")

    # ---- Station 3: center utility column + apex crane anchor ----------
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
    cat.begin("column", "Apex crane anchor")
    anchor_top = FLOOR_TOP + (1.0 - base_z) * (R + 0.24) + 0.14
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
    cat.end("column")

    # ---- Station 4: water lines ----------------------------------------
    hot = (0.85, 0.20, 0.20)
    cold = (0.20, 0.40, 0.90)
    drain = (0.28, 0.28, 0.32)
    cat.begin("water", "Central water manifold")
    b.cylinder((0, 0, FLOOR_TOP), (0, 0, FLOOR_TOP + 0.12), 0.30, 14,
               (0.30, 0.42, 0.62), mat_id=MAT_METAL)
    cat.end("water")

    def water_run(az, r_target, color, radius, offset_deg, label):
        a = az + offset_deg
        cat.begin("water", label)
        p0 = polar(a, 0.32, FLOOR_TOP + 0.045)
        p1 = polar(a, r_target, FLOOR_TOP + 0.045)
        b.cylinder(p0, p1, radius, 6, color)
        b.cylinder(p1, (p1[0], p1[1], FLOOR_TOP + 0.32), radius, 6, color)
        cat.end("water")

    for az, r_t, kinds, name in (
            (150, fr(0.685), "hcd", "Kitchen"),
            (40, fr(0.622), "hc", "Bath sink"),
            (60, fr(0.635), "cd", "Toilet"),
            (82, fr(0.596), "hcd", "Shower")):
        if "h" in kinds:
            water_run(az, r_t, hot, 0.022, -3.5, f"{name} hot PEX")
        if "c" in kinds:
            water_run(az, r_t, cold, 0.022, 3.5, f"{name} cold PEX")
        if "d" in kinds:
            water_run(az, r_t, drain, 0.048, 0.0, f"{name} drain")

    # ---- Station 5: power lines ----------------------------------------
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

    # ---- Station 6: fixtures & outlets ---------------------------------
    white = (0.95, 0.96, 0.97)
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
    b.sphere((sx, sy, FLOOR_TOP + 2.02), 0.07, (0.70, 0.72, 0.76),
             rings=4, sides=8)
    b.cone((sx, sy, FLOOR_TOP + 1.98), (sx, sy, FLOOR_TOP + 1.86), 0.09, 10,
           (0.70, 0.72, 0.76))
    cat.end("fixtures")
    cat.begin("fixture", "Bath pedestal sink")
    bx, by, _ = polar(40, fr(0.622))
    b.cylinder((bx, by, FLOOR_TOP), (bx, by, FLOOR_TOP + 0.76), 0.07, 8,
               white)
    b.cylinder((bx, by, FLOOR_TOP + 0.76), (bx, by, FLOOR_TOP + 0.88),
               0.20, 12, white)
    cat.end("fixtures")
    cat.begin("fixture", "Kitchen rough-in cabinet")
    kx, ky, _ = polar(150, fr(0.685))
    add_box(b, (kx, ky, FLOOR_TOP + 0.44), (0.62, 0.55, 0.88),
            (0.62, 0.64, 0.68), mat_id=MAT_METAL, yaw=math.radians(150))
    b.cylinder((kx, ky, FLOOR_TOP + 0.88), (kx, ky, FLOOR_TOP + 1.12),
               0.020, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
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
    for dz, col in ((1.05, hot), (1.20, cold)):
        px, py, _ = polar(270, 0.16)
        b.cylinder((px, py, FLOOR_TOP + dz), (px * 1.9, py * 1.9,
                   FLOOR_TOP + dz), 0.022, 6, col)
        b.sphere((px * 1.9, py * 1.9, FLOOR_TOP + dz), 0.045, col,
                 rings=4, sides=8)
    cat.end("fixtures")

    # ---- Shell layers (stations 7-12, 15): per-face skins --------------
    faces = sorted(
        (tuple(f) for f in geo.faces),
        key=lambda f: (round(sum(geo.verts[i][2] for i in f) / 3.0, 3),
                       math.atan2(sum(geo.verts[i][1] for i in f),
                                  sum(geo.verts[i][0] for i in f))))

    def shell(stage, cat_key, d, color, alpha=1.0, mat_id=MAT_PLAIN,
              shrink=1.0, face_filter=None):
        for f in faces:
            c_unit = np.mean([geo.verts[i] for i in f], axis=0)
            if face_filter and not face_filter(normalize(c_unit)):
                continue
            pts = [spt(geo.verts[i], d) for i in f]
            centroid = np.mean(pts, axis=0)
            pts = [centroid + (p - centroid) * shrink for p in pts]
            for p in pts:
                p[2] = max(p[2], FLOOR_TOP + 0.01)
            cat.begin(cat_key)
            b.triangle(pts[0], pts[1], pts[2], color, alpha, mat_id)
            cat.end(stage)

    shell("insulation", "insulation", -0.03, (0.93, 0.45, 0.55),
          mat_id=MAT_CANVAS, shrink=0.80)
    shell("sheetrock", "sheetrock", -0.10, (0.92, 0.92, 0.88))
    shell("osb", "osb", 0.07, (0.80, 0.68, 0.42), mat_id=MAT_CONCRETE,
          shrink=0.985)
    shell("wrap", "wrap", 0.105, (0.84, 0.85, 0.87), mat_id=MAT_SHEETING)
    shell("shingles", "shingle", 0.14, spec.cladding_color,
          mat_id=MAT_SHINGLE)
    shell("fiberglass", "fiberglass", 0.19, (0.72, 0.85, 0.88), alpha=0.30,
          mat_id=MAT_GLASS)
    cat.begin("fiberglass", "Fiberglass floor skirt")
    b.cylinder((0, 0, 0.02), (0, 0, FLOOR_TOP + 0.12), floor_r + 0.20, 40,
               (0.72, 0.85, 0.88), alpha=0.30, mat_id=MAT_GLASS,
               cap_ends=False)
    cat.end("fiberglass")

    # ---- Station 13: watertight hatch door (zero windows) --------------
    rh = R + 0.19
    u = (1.25 - FLOOR_TOP) / rh + base_z
    horiz = math.sqrt(max(0.0, 1.0 - u * u))
    hpos = np.array([0.0, -horiz * rh, 1.25])
    n = normalize(np.array([0.0, -horiz, u]))
    right = normalize(np.cross(np.array([0.0, 0.0, 1.0]), n))
    up = normalize(np.cross(n, right))

    def hpt(a, scale=1.0, out=0.0):
        return (hpos + right * (0.56 * scale * math.cos(a))
                + up * (0.86 * scale * math.sin(a)) + n * out)

    cat.begin("hatch", "Hatch coaming ring")
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 1.0, 0.05), hpt(a1, 1.0, 0.05), 0.05, 6,
                   (0.36, 0.39, 0.44), mat_id=MAT_METAL)
    cat.end("hatch", cost=CATEGORY_ECON["hatch"][0] * 0.35,
            labor=CATEGORY_ECON["hatch"][1] * 0.35)
    cat.begin("hatch", "Hatch door leaf + gasket")
    door = (0.62, 0.64, 0.68)
    center = hpos + n * 0.09
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.triangle(center, hpt(a0, 0.93, 0.09), hpt(a1, 0.93, 0.09), door,
                   mat_id=MAT_METAL, normal=n)
    for i in range(18):
        a0 = 2 * math.pi * i / 18
        a1 = 2 * math.pi * (i + 1) / 18
        b.cylinder(hpt(a0, 0.95, 0.07), hpt(a1, 0.95, 0.07), 0.022, 5,
                   (0.10, 0.10, 0.12))
    cat.end("hatch", cost=CATEGORY_ECON["hatch"][0] * 0.4,
            labor=CATEGORY_ECON["hatch"][1] * 0.4)
    cat.begin("hatch", "Hatch dogs + locking wheel")
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.5
        p = hpt(a, 1.02, 0.07)
        b.sphere(p, 0.055, (0.25, 0.27, 0.30), rings=4, sides=8)
    wc = hpos + n * 0.20
    for i in range(12):
        a0 = 2 * math.pi * i / 12
        a1 = 2 * math.pi * (i + 1) / 12
        p0 = wc + right * (0.22 * math.cos(a0)) + up * (0.22 * math.sin(a0))
        p1 = wc + right * (0.22 * math.cos(a1)) + up * (0.22 * math.sin(a1))
        b.cylinder(p0, p1, 0.028, 6, (0.78, 0.80, 0.84), mat_id=MAT_METAL)
    for i in range(3):
        a = 2 * math.pi * i / 3
        p1 = wc + right * (0.21 * math.cos(a)) + up * (0.21 * math.sin(a))
        b.cylinder(wc, p1, 0.020, 5, (0.78, 0.80, 0.84), mat_id=MAT_METAL)
    b.sphere(wc, 0.05, (0.78, 0.80, 0.84), rings=4, sides=8)
    for dz in (0.30, -0.30):
        p = hpos + right * 0.62 + up * dz + n * 0.05
        add_box(b, tuple(p), (0.14, 0.10, 0.18), (0.30, 0.32, 0.36),
                mat_id=MAT_METAL)
    cat.end("hatch", cost=CATEGORY_ECON["hatch"][0] * 0.25,
            labor=CATEGORY_ECON["hatch"][1] * 0.25)

    # ---- Station 14: interior fit-out (varies by layout) ---------------
    wall = (0.90, 0.90, 0.86)

    def wall_run(az, segments, label):
        a = math.radians(az)
        cat.begin("furniture", label)
        for r0f, r1f in segments:
            r0, r1 = fr(r0f), fr(r1f)
            rc = (r0 + r1) * 0.5
            add_box(b, (rc * math.cos(a), rc * math.sin(a),
                        FLOOR_TOP + 1.10), (r1 - r0, 0.08, 2.20), wall,
                    yaw=a)
        cat.end("interior")

    has_bath_walls = True
    if has_bath_walls:
        wall_run(30, [(0.10, 0.24), (0.44, 0.74)], "Bathroom partition")
        wall_run(90, [(0.10, 0.74)], "Bathroom partition")
    if spec.bedrooms >= 1:
        wall_run(300, [(0.10, 0.74)], "Bedroom partition")
        wall_run(0, [(0.10, 0.24), (0.44, 0.74)], "Bedroom partition")
    if spec.bedrooms >= 2:
        wall_run(258, [(0.10, 0.74)], "Second-bedroom partition")
        wall_run(222, [(0.10, 0.24), (0.44, 0.74)], "Second-bedroom door")

    cabinet = (0.45, 0.32, 0.20)
    counter_top = (0.85, 0.84, 0.80)
    for az in (140, 163):
        cat.begin("furniture", "Kitchen counter run")
        cx, cy, _ = polar(az, fr(0.761))
        yaw = math.radians(az + 90)
        add_box(b, (cx, cy, FLOOR_TOP + 0.45), (1.45, 0.62, 0.90), cabinet,
                mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (cx, cy, FLOOR_TOP + 0.925), (1.55, 0.68, 0.05),
                counter_top, yaw=yaw)
        cat.end("interior")
    cat.begin("furniture", "Kitchen sink + faucet")
    kx, ky, _ = polar(150, fr(0.749))
    add_box(b, (kx, ky, FLOOR_TOP + 0.93), (0.50, 0.40, 0.06),
            (0.68, 0.70, 0.74), mat_id=MAT_METAL, yaw=math.radians(240))
    b.cylinder((kx, ky, FLOOR_TOP + 0.95), (kx, ky, FLOOR_TOP + 1.22),
               0.020, 6, (0.70, 0.72, 0.76), mat_id=MAT_METAL)
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
    for bi in range(4):
        ba = math.radians(267)
        dx = (-0.15 + 0.30 * (bi % 2))
        dy = (-0.15 + 0.30 * (bi // 2))
        wx = ox + dx * math.cos(ba) - dy * math.sin(ba)
        wy = oy + dx * math.sin(ba) + dy * math.cos(ba)
        b.cylinder((wx, wy, FLOOR_TOP + 0.90), (wx, wy, FLOOR_TOP + 0.915),
                   0.09, 10, (0.10, 0.10, 0.12))
    cat.end("interior")
    if spec.bedrooms >= 1:
        cat.begin("furniture", "Primary bed")
        bx, by, _ = polar(332, fr(0.558))
        yaw = math.radians(332 + 90)
        add_box(b, (bx, by, FLOOR_TOP + 0.18), (1.45, 2.00, 0.32),
                (0.48, 0.36, 0.22), mat_id=MAT_WOOD, yaw=yaw)
        add_box(b, (bx, by, FLOOR_TOP + 0.45), (1.38, 1.92, 0.22),
                (0.93, 0.93, 0.95), yaw=yaw)
        hx = bx + 0.72 * math.cos(yaw + math.pi / 2)
        hy = by + 0.72 * math.sin(yaw + math.pi / 2)
        add_box(b, (hx, hy, FLOOR_TOP + 0.60), (1.20, 0.45, 0.12),
                (0.98, 0.98, 1.00), yaw=yaw)
        cat.end("interior")
        cat.begin("furniture", "Wardrobe + nightstand")
        wx, wy, _ = polar(297, fr(0.685))
        add_box(b, (wx, wy, FLOOR_TOP + 0.95), (1.20, 0.60, 1.90),
                (0.50, 0.38, 0.24), mat_id=MAT_WOOD,
                yaw=math.radians(297 + 90))
        nx, ny, _ = polar(352, fr(0.647))
        add_box(b, (nx, ny, FLOOR_TOP + 0.25), (0.45, 0.45, 0.50),
                (0.50, 0.38, 0.24), mat_id=MAT_WOOD)
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
    b.cylinder((dx, dy, FLOOR_TOP + 0.72), (dx, dy, FLOOR_TOP + 0.77),
               0.50, 16, (0.60, 0.46, 0.28), mat_id=MAT_WOOD)
    for sa in (150, 290):
        sx2, sy2, _ = polar(sa, 0.75)
        b.cylinder((dx + sx2, dy + sy2, FLOOR_TOP),
                   (dx + sx2, dy + sy2, FLOOR_TOP + 0.45), 0.16, 10,
                   (0.45, 0.34, 0.22), mat_id=MAT_WOOD)
    cat.end("interior")

    # ---- Station 15: solar array ---------------------------------------
    shell("solar", "solar", 0.23, (0.10, 0.15, 0.32), mat_id=MAT_SOLAR,
          shrink=0.86,
          face_filter=lambda c: (-c[1]) > 0.40 and 0.10 < c[2] < 0.74)

    info = {
        "floor_r": floor_r,
        "apex_z": apex_z,
        "anchor_top": anchor_top + 0.45,
        "base_z": base_z,
        "hatch_floor": np.array([0.0, -floor_r * 0.9, 0.0]),
    }
    return cat, info


# ---------------------------------------------------------------------------
# Finished-dome mesh for the yard (built once, drawn scaled + tinted)
# ---------------------------------------------------------------------------

def build_finished_dome_mesh(frequency=DOME_FREQ_DEFAULT) -> Mesh:
    spec = DomeSpec(radius=REFERENCE_RADIUS, frequency=frequency)
    cat, _ = build_dome_catalog(spec)
    return cat.b.build()


# ===========================================================================
# Business math — pure functions over a spec + a built catalog
# ===========================================================================

def worker_place_seconds(labor_min: float) -> float:
    """Seconds a worker spends handling/placing one element (excludes
    walking)."""
    return labor_min * 60.0


def unit_economics(cat: Catalog, spec: DomeSpec,
                   labor_hours: float | None = None) -> dict:
    """Full per-dome P&L. If ``labor_hours`` is None it is derived from the
    catalog's labor-minutes across the configured crew size."""
    a = ASSUMPTIONS
    material = cat.material_cost()
    if labor_hours is None:
        labor_hours = cat.labor_minutes() / 60.0
    labor_cost = labor_hours * a["burdened_wage_per_hour"]

    # Overhead allocated per unit: amortized CapEx + fixed overhead spread
    # across the planning volume.
    capex_year = a["line_capex"] / a["capex_amortize_years"]
    fixed_year = a["fixed_overhead_per_month"] * 12.0
    overhead = (capex_year + fixed_year) / max(1, a["target_units_per_year"])

    total_cost = material + labor_cost + overhead
    price = spec.sale_price
    margin = price - total_cost
    return {
        "material": material,
        "labor_hours": labor_hours,
        "labor_cost": labor_cost,
        "overhead": overhead,
        "total_cost": total_cost,
        "price": price,
        "margin": margin,
        "margin_pct": (margin / price * 100.0) if price else 0.0,
    }


def station_cycle_times(cat: Catalog) -> list[dict]:
    """Per-station labor time (minutes) and cost, plus the crew-parallel
    cycle time. The bottleneck is the max cycle time."""
    a = ASSUMPTIONS
    crew = max(1, a["install_crew_size"])
    rows = []
    for stage in STAGES:
        els = cat.by_stage[stage.key]
        labor_min = sum(e.labor_min for e in els)
        # Cycle time with the crew working in parallel (rough balance).
        cycle_min = labor_min / crew
        rows.append({
            "key": stage.key,
            "title": stage.title,
            "elements": len(els),
            "labor_min": labor_min,
            "cycle_min": cycle_min,
        })
    return rows


def throughput(cat: Catalog) -> dict:
    a = ASSUMPTIONS
    rows = station_cycle_times(cat)
    bottleneck = max(rows, key=lambda r: r["cycle_min"])
    total_cycle = sum(r["cycle_min"] for r in rows)
    minutes_per_day = a["shift_hours_per_day"] * 60.0
    # Single-piece flow: one dome occupies the line end to end.
    single_per_day = minutes_per_day / total_cycle if total_cycle else 0.0
    # Pipelined: a new dome exits every bottleneck interval.
    pipe_per_day = (minutes_per_day / bottleneck["cycle_min"]
                    if bottleneck["cycle_min"] else 0.0)
    return {
        "rows": rows,
        "bottleneck": bottleneck,
        "total_cycle_min": total_cycle,
        "single_flow_per_day": single_per_day,
        "single_flow_per_year": single_per_day * a["work_days_per_year"],
        "pipelined_per_day": pipe_per_day,
        "pipelined_per_year": pipe_per_day * a["work_days_per_year"],
    }


def break_even(avg_margin: float) -> dict:
    a = ASSUMPTIONS
    fixed_year = a["fixed_overhead_per_month"] * 12.0
    capex = a["line_capex"]
    # Contribution per unit toward capex+fixed = margin already nets overhead
    # allocation, so add the allocated overhead back to get contribution.
    capex_year = a["line_capex"] / a["capex_amortize_years"]
    overhead_alloc = ((capex_year + fixed_year)
                      / max(1, a["target_units_per_year"]))
    contribution = max(1.0, avg_margin + overhead_alloc)
    units_to_capex = capex / contribution
    units_to_annual = fixed_year / contribution
    return {
        "capex": capex,
        "fixed_year": fixed_year,
        "contribution_per_unit": contribution,
        "units_to_recover_capex": units_to_capex,
        "units_to_cover_annual_fixed": units_to_annual,
    }


def benchmark(cat: Catalog, spec: DomeSpec, econ: dict,
              build_days: float, labor_hours: float) -> dict:
    a = ASSUMPTIONS
    return {
        "dome": {
            "name": spec.name,
            "price": econ["price"],
            "material": econ["material"],
            "labor_hours": labor_hours,
            "build_days": build_days,
        },
        "conventional": {
            "name": a["benchmark_name"],
            "price": a["benchmark_price"],
            "material": a["benchmark_material_cost"],
            "labor_hours": a["benchmark_labor_hours"],
            "build_days": a["benchmark_build_days"],
        },
    }


def product_value(cat: Catalog, spec: DomeSpec) -> dict:
    a = ASSUMPTIONS
    panels = cat.solar_panel_count()
    solar_kw = panels * a["solar_watts_per_panel"] / 1000.0
    # ~4.5 peak-sun-hours/day, sun-tracked band gains ~25%.
    daily_gen = solar_kw * 4.5 * 1.25
    autonomy_days = a["battery_kwh"] / max(0.1, a["daily_load_kwh"])
    r_value = 12.0 + cat.insulation_count() * a["insulation_r_per_element"]
    carbon = cat.total_weight() * a["carbon_kg_per_kg_material"]
    return {
        "solar_kw": solar_kw,
        "solar_panels": panels,
        "daily_generation_kwh": daily_gen,
        "net_daily_kwh": daily_gen - a["daily_load_kwh"],
        "battery_kwh": a["battery_kwh"],
        "autonomy_days": autonomy_days,
        "r_value": r_value,
        "embodied_carbon_kg": carbon,
        "osha_target": a["osha_incident_rate_target"],
        "floor_area": spec.floor_area,
    }


def scale_scenarios(single_per_year: float, avg_margin: float,
                    avg_price: float) -> list[dict]:
    a = ASSUMPTIONS
    out = []
    for lines in (1, 3, 6):
        units = single_per_year * lines
        out.append({
            "lines": lines,
            "units_per_year": units,
            "revenue": units * avg_price,
            "gross_profit": units * avg_margin,
            "capex": a["line_capex"] * lines,
        })
    return out
