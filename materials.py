"""
Material, panel, layer, and foundation databases for the dome creator.

Every entry carries the physical properties used for the live bill-of-material
breakdown: densities, area weights, and unit costs. Tweak numbers here and the
stats panel updates automatically.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# Shader pattern ids (must match the fragment shader in dome_creator.py).
MAT_PLAIN = 0
MAT_SHINGLE = 1
MAT_SHEETING = 2
MAT_GLASS = 3
MAT_WOOD = 4
MAT_SOLAR = 5
MAT_CONCRETE = 6
MAT_DECK = 7
MAT_GRASS = 8
MAT_METAL = 9
MAT_CANVAS = 10
MAT_GRAVEL = 11
MAT_EMISSIVE = 12
MAT_MIRROR = 13


@dataclass(frozen=True)
class FrameMaterial:
    name: str
    density: float            # kg/m^3
    cost_per_kg: float        # USD
    hub_weight: float         # kg per hub at 5 cm strut size
    hub_cost: float           # USD per hub at 5 cm strut size
    color: tuple[float, float, float]


FRAME_MATERIALS: list[FrameMaterial] = [
    FrameMaterial("Galvanized Steel", 7850.0, 2.8, 1.30, 14.0, (0.55, 0.60, 0.64)),
    FrameMaterial("Structural Steel", 7850.0, 3.2, 2.10, 24.0, (0.35, 0.39, 0.43)),
    FrameMaterial("Rebar Steel", 7850.0, 1.9, 0.35, 5.0, (0.30, 0.32, 0.30)),
    FrameMaterial("Aluminum", 2700.0, 7.5, 0.70, 24.0, (0.72, 0.75, 0.78)),
    FrameMaterial("Timber (SPF)", 480.0, 2.0, 0.45, 7.0, (0.62, 0.47, 0.30)),
    FrameMaterial("Whole Tree Trunk", 650.0, 0.9, 1.00, 9.0, (0.44, 0.30, 0.17)),
    FrameMaterial("PVC Pipe", 1400.0, 3.4, 0.25, 5.0, (0.88, 0.88, 0.86)),
    FrameMaterial("Bamboo", 720.0, 1.6, 0.30, 4.0, (0.71, 0.60, 0.32)),
]


@dataclass(frozen=True)
class StrutShape:
    name: str
    kind: str                 # "circle", "square", "rect", "hex"
    hollow: bool
    depth_ratio: float        # depth = width * depth_ratio (radial direction)
    sides: int                # sides used for round rendering

    def wall_thickness(self, width: float) -> float:
        return min(max(0.10 * width, 0.002), 0.006)

    def cross_section_area(self, width: float) -> float:
        """Solid material area of the cross section, in m^2."""
        w = width
        if self.kind == "wedge":
            # Quarter of a log whose split faces span the strut width.
            s = w / math.sqrt(2.0)
            return math.pi * s * s / 4.0
        if self.kind == "circle":
            if self.hollow:
                t = self.wall_thickness(w)
                return math.pi / 4.0 * (w * w - (w - 2 * t) ** 2)
            return math.pi / 4.0 * w * w
        if self.kind == "square":
            if self.hollow:
                t = self.wall_thickness(w)
                return w * w - (w - 2 * t) ** 2
            return w * w
        if self.kind == "rect":
            return w * (w * self.depth_ratio)
        if self.kind == "hex":
            # Regular hexagon with circumradius w/2.
            return 1.5 * math.sqrt(3.0) * (w * 0.5) ** 2
        return w * w

    def profile(
        self, width: float, flip: bool = False,
    ) -> list[tuple[float, float]]:
        """2D cross-section outline (u = tangent, v = radial), CCW.

        For the quarter wedge, the right-angle corner (the two split
        faces of the log) points radially outward and the bark arc bulges
        inward — the panel recess forms naturally against the curve.
        `flip` turns the curve outward instead.
        """
        w = width * 0.5
        if self.kind == "wedge":
            s = width / math.sqrt(2.0)
            corner_v = s * 0.5
            points = [(0.0, corner_v)]
            arc_steps = 8
            for i in range(arc_steps + 1):
                theta = math.radians(-45.0 + 90.0 * i / arc_steps)
                points.append((
                    s * math.sin(theta),
                    corner_v - s * math.cos(theta),
                ))
            if flip:
                points = [(u, -v) for u, v in reversed(points)]
            return points
        if self.kind == "circle":
            return [
                (w * math.cos(2 * math.pi * i / self.sides),
                 w * math.sin(2 * math.pi * i / self.sides))
                for i in range(self.sides)
            ]
        if self.kind == "square":
            return [(-w, -w), (w, -w), (w, w), (-w, w)]
        if self.kind == "rect":
            d = w * self.depth_ratio
            return [(-w, -d), (w, -d), (w, d), (-w, d)]
        if self.kind == "hex":
            return [
                (w * math.cos(2 * math.pi * i / 6 + math.pi / 6),
                 w * math.sin(2 * math.pi * i / 6 + math.pi / 6))
                for i in range(6)
            ]
        return [(-w, -w), (w, -w), (w, w), (-w, w)]

    def depth(self, width: float) -> float:
        if self.kind == "rect":
            return width * self.depth_ratio
        if self.kind == "wedge":
            return width / math.sqrt(2.0)
        return width


STRUT_SHAPES: list[StrutShape] = [
    StrutShape("Round Tube", "circle", True, 1.0, 12),
    StrutShape("Solid Steel Rod", "circle", False, 1.0, 12),
    StrutShape("Rebar Rod", "circle", False, 1.0, 10),
    StrutShape("Full Tree Trunk", "circle", False, 1.0, 16),
    StrutShape("Square Tube", "square", True, 1.0, 4),
    StrutShape("Dimensional Lumber", "rect", False, 2.2, 4),
    StrutShape("Hex Strut", "hex", False, 1.0, 6),
    StrutShape("Quarter Wedge", "wedge", False, 0.707, 9),
]


@dataclass(frozen=True)
class PanelType:
    name: str
    area_weight: float        # kg/m^2
    cost_per_m2: float        # USD/m^2
    color: tuple[float, float, float]
    alpha: float
    mat_id: int
    colorable: bool
    transparent: bool
    is_window: bool = False
    watts_per_m2: float = 0.0
    shape: str = "triangle"       # triangle / hexagon / square


PANEL_TYPES: list[PanelType] = [
    PanelType("Open", 0.0, 0.0, (0, 0, 0), 0.0, MAT_PLAIN, False, False),
    PanelType("Plywood", 6.6, 18.0, (0.71, 0.55, 0.35), 1.0, MAT_WOOD, True, False),
    PanelType("Glass Window", 15.0, 95.0, (0.55, 0.72, 0.80), 0.30, MAT_GLASS, False, True, is_window=True),
    PanelType("Acrylic Window", 6.0, 65.0, (0.62, 0.78, 0.82), 0.35, MAT_GLASS, False, True, is_window=True),
    PanelType("Polycarb Twinwall", 1.7, 28.0, (0.75, 0.82, 0.85), 0.55, MAT_SHEETING, False, True),
    PanelType("Plastic Sheeting", 0.15, 1.5, (0.80, 0.84, 0.86), 0.45, MAT_SHEETING, False, True),
    PanelType("Insulated SIP", 12.0, 55.0, (0.82, 0.80, 0.75), 1.0, MAT_PLAIN, True, False),
    PanelType("Shingle Panel", 16.0, 42.0, (0.36, 0.33, 0.31), 1.0, MAT_SHINGLE, True, False),
    PanelType("Metal Panel", 5.0, 30.0, (0.60, 0.63, 0.66), 1.0, MAT_METAL, True, False),
    PanelType("Solar Panel", 12.0, 180.0, (0.10, 0.14, 0.30), 1.0, MAT_SOLAR, False, False, watts_per_m2=190.0),
    PanelType("Canvas", 0.5, 8.0, (0.85, 0.80, 0.68), 1.0, MAT_CANVAS, True, False),
    PanelType("Hex Composite", 8.5, 52.0, (0.48, 0.58, 0.52), 1.0,
              MAT_METAL, True, False, shape="hexagon"),
    PanelType("Hex Mirror", 13.0, 210.0, (0.72, 0.78, 0.80), 1.0,
              MAT_MIRROR, False, False, shape="hexagon"),
    PanelType("Square Mirror", 13.0, 195.0, (0.72, 0.78, 0.80), 1.0,
              MAT_MIRROR, False, False, shape="square"),
    PanelType("Concrete Form Panel", 18.0, 46.0, (0.56, 0.48, 0.34), 1.0,
              MAT_WOOD, False, False),
    PanelType("Precast Concrete", 92.0, 125.0, (0.61, 0.62, 0.60), 1.0,
              MAT_CONCRETE, False, False),
]

PANEL_TYPE_BY_NAME = {p.name: p for p in PANEL_TYPES}


# ---------------------------------------------------------------------------
# Panel Lab: custom panels assembled from hardware components
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PanelComponent:
    name: str
    cost: float               # USD each
    weight: float             # kg each
    minutes: float            # extra install time each
    screws_each: int = 0      # fasteners implied per component


PANEL_COMPONENTS: list[PanelComponent] = [
    PanelComponent("V-Bracket", 4.50, 0.40, 6.0, screws_each=8),
    PanelComponent("L-Bracket", 2.80, 0.25, 4.0, screws_each=6),
    PanelComponent("Corner Gusset", 3.20, 0.30, 5.0, screws_each=9),
    PanelComponent("Foam Seal (m)", 1.10, 0.05, 1.5),
    PanelComponent("Silicone Bead (m)", 0.80, 0.02, 2.0),
    PanelComponent("Hinge", 6.50, 0.35, 8.0, screws_each=6),
    PanelComponent("Latch", 4.00, 0.15, 4.0, screws_each=4),
    PanelComponent("LED Strip (m)", 9.00, 0.10, 5.0),
]

PANEL_COMPONENT_BY_NAME = {c.name: c for c in PANEL_COMPONENTS}
SCREW_COST = 0.06

# name -> {"base": str, "components": {component_name: qty}}
CUSTOM_PANEL_DEFS: dict[str, dict] = {}


def custom_panel_extras(definition: dict) -> tuple[float, float, int, float]:
    """(extra_cost, extra_weight, screw_count, extra_minutes) per panel."""
    cost = weight = minutes = 0.0
    screws = 0
    for comp_name, qty in definition.get("components", {}).items():
        comp = PANEL_COMPONENT_BY_NAME.get(comp_name)
        if comp is None or qty <= 0:
            continue
        cost += comp.cost * qty
        weight += comp.weight * qty
        minutes += comp.minutes * qty
        screws += comp.screws_each * qty
    cost += screws * SCREW_COST
    return cost, weight, screws, minutes


def register_custom_panel(name: str, definition: dict) -> PanelType:
    """Create a PanelType from a base type + component list and make it
    available everywhere panels are chosen."""
    base = PANEL_TYPE_BY_NAME.get(definition.get("base", "Plywood"))
    if base is None or base.name == "Open":
        base = PANEL_TYPE_BY_NAME["Plywood"]
    extra_cost, extra_weight, _screws, _minutes = \
        custom_panel_extras(definition)
    # Approximate per-m2 uplift using a nominal 2 m^2 panel.
    panel = PanelType(
        name, base.area_weight + extra_weight / 2.0,
        base.cost_per_m2 + extra_cost / 2.0,
        base.color, base.alpha, base.mat_id, base.colorable,
        base.transparent, is_window=base.is_window,
        watts_per_m2=base.watts_per_m2, shape=base.shape)
    CUSTOM_PANEL_DEFS[name] = dict(definition)
    PANEL_TYPE_BY_NAME[name] = panel
    return panel


def panel_type_names() -> list[str]:
    """All selectable panel types: built-in first, then customs."""
    return [p.name for p in PANEL_TYPES] + sorted(CUSTOM_PANEL_DEFS)


@dataclass(frozen=True)
class LayerType:
    name: str
    area_weight: float        # kg/m^2
    cost_per_m2: float        # USD/m^2
    thickness: float          # visual shell thickness, m
    color: tuple[float, float, float]
    alpha: float
    mat_id: int


LAYER_TYPES: list[LayerType] = [
    LayerType("None", 0.0, 0.0, 0.0, (0, 0, 0), 0.0, MAT_PLAIN),
    LayerType("Plastic Film", 0.15, 1.2, 0.010, (0.80, 0.85, 0.88), 0.35, MAT_SHEETING),
    LayerType("House Wrap", 0.20, 1.8, 0.010, (0.90, 0.90, 0.92), 1.0, MAT_PLAIN),
    LayerType("Foam Insulation", 1.20, 12.0, 0.050, (0.93, 0.87, 0.62), 1.0, MAT_PLAIN),
    LayerType("Asphalt Shingles", 12.0, 15.0, 0.030, (0.30, 0.28, 0.27), 1.0, MAT_SHINGLE),
    LayerType("Cedar Shakes", 9.0, 32.0, 0.040, (0.48, 0.32, 0.18), 1.0, MAT_SHINGLE),
    LayerType("EPDM Membrane", 1.8, 11.0, 0.015, (0.14, 0.14, 0.15), 1.0, MAT_PLAIN),
    LayerType("Green Roof", 55.0, 48.0, 0.090, (0.25, 0.42, 0.20), 1.0, MAT_GRASS),
    LayerType("Poured Concrete Shell", 120.0, 95.0, 0.080,
              (0.60, 0.61, 0.59), 1.0, MAT_CONCRETE),
]

LAYER_TYPE_BY_NAME = {l.name: l for l in LAYER_TYPES}


@dataclass(frozen=True)
class FoundationType:
    name: str
    cost_per_m2: float
    weight_per_m2: float      # kg/m^2
    height: float             # m above grade
    top_color: tuple[float, float, float]
    side_color: tuple[float, float, float]
    mat_id: int


FOUNDATION_TYPES: list[FoundationType] = [
    FoundationType("Bare Ground", 0.0, 0.0, 0.0, (0.30, 0.36, 0.26), (0.3, 0.3, 0.3), MAT_GRASS),
    FoundationType("Grass Pad", 2.0, 4.0, 0.03, (0.30, 0.44, 0.24), (0.26, 0.30, 0.20), MAT_GRASS),
    FoundationType("Gravel Pad", 9.0, 160.0, 0.09, (0.58, 0.56, 0.53), (0.48, 0.46, 0.43), MAT_GRAVEL),
    FoundationType("Concrete Slab", 85.0, 300.0, 0.13, (0.62, 0.62, 0.61), (0.52, 0.52, 0.51), MAT_CONCRETE),
    FoundationType("Wood Deck", 60.0, 28.0, 0.32, (0.55, 0.38, 0.22), (0.42, 0.29, 0.17), MAT_DECK),
    FoundationType("Stone Pavers", 55.0, 130.0, 0.06, (0.57, 0.54, 0.50), (0.47, 0.44, 0.40), MAT_CONCRETE),
    FoundationType("Treehouse Platform", 190.0, 70.0, 4.50,
                   (0.48, 0.33, 0.19), (0.34, 0.23, 0.14), MAT_DECK),
]

FOUNDATION_TYPE_BY_NAME = {f.name: f for f in FOUNDATION_TYPES}


@dataclass(frozen=True)
class NamedColor:
    name: str
    rgb: tuple[float, float, float]


FRAME_COLORS: list[NamedColor] = [
    NamedColor("Material", (-1.0, -1.0, -1.0)),   # sentinel: use material color
    NamedColor("Matte Black", (0.12, 0.12, 0.13)),
    NamedColor("White", (0.88, 0.89, 0.90)),
    NamedColor("Barn Red", (0.55, 0.16, 0.13)),
    NamedColor("Forest Green", (0.16, 0.34, 0.20)),
    NamedColor("Cedar", (0.52, 0.33, 0.18)),
    NamedColor("Navy", (0.13, 0.20, 0.36)),
    NamedColor("Safety Orange", (0.90, 0.35, 0.08)),
]

PANEL_COLORS: list[NamedColor] = [
    NamedColor("Natural", (1.0, 1.0, 1.0)),        # multiplies the base color
    NamedColor("Snow", (1.25, 1.25, 1.28)),
    NamedColor("Slate", (0.55, 0.60, 0.68)),
    NamedColor("Terracotta", (1.15, 0.62, 0.45)),
    NamedColor("Sage", (0.72, 0.88, 0.66)),
    NamedColor("Sand", (1.18, 1.05, 0.80)),
    NamedColor("Charcoal", (0.38, 0.38, 0.40)),
    NamedColor("Sky", (0.70, 0.92, 1.15)),
]
