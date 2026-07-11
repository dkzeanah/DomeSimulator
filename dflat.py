# Geodesic Dome Creator — flattened project

Generated 2026-07-11 00:53 UTC by flatten.py. 11 files, 7,454 lines total.

Each file below is delimited by a `======== FILE: path ========` marker.

## Table of contents

- README.md  (246 lines)
- materials.py  (324 lines)
- workshop.py  (609 lines)
- presets.py  (188 lines)
- dome_model.py  (873 lines)
- mesh_builder.py  (625 lines)
- electrical.py  (127 lines)
- vision.py  (103 lines)
- overlay_ui.py  (600 lines)
- dome_creator.py  (3659 lines)
- flatten.py  (100 lines)

==========================================================================
======== FILE: README.md ========
==========================================================================

```markdown
# Geodesic Dome Creator

A walkable, build-a-home style **parametric dome customizer** with
RuneScape-style controls: an orbit camera, click-to-move avatar, a
clickable toolbar, a transparent-roof aerial view, and a 28-slot
backpack for picking up and dropping workshop equipment. Change the
structure, swap the recessed panels between the struts one by one
(windows, shingles, solar, plastic sheeting, ...), stack cladding
layers, pick a foundation — and watch a complete material breakdown
(weights, costs, strut cut list, trees to harvest) update live.

Includes the original 360° six-point perspective renderer (press `Tab`).

Every dome ships with its **workshop monitoring system**: a PTZ
(pan-tilt-zoom) camera hangs from the top center of the dome looking down,
and its live video feed is always on screen in a minimap-style window.
A monitor hangs high on the north wall above the doorway (with the
computer unit tucked beneath it) — it shows the same live feed, angled
down toward the floor. Click it to **take helm**, or press `C` anywhere
for remote camera control (no leash). Steer with the arrow keys, zoom
with PgUp/PgDn or the wheel; the 960x540 feed has a camera-mounted
illuminator so it clearly sees the equipment below even in a closed
dome.

## RuneScape-style interface

Everything is mouse-first. **Left-click** walks, uses, toggles, and
advances menu values; **right-click** opens a "Choose Option" context
menu whose entries depend on what's under the cursor — props offer
switch/pick up/examine, panels offer swap/apply-to-all, screens offer
take-helm, dome floors offer select/construct/examine, and open ground
offers "Build here" with every preset. The menu panel is fully
clickable (tabs included), the toolbar drives all panels, and a
collapsible **hotkey legend** (`K` or the Keys button) sits by the video
feed. WASD moves only in first-person (`P`); in the default overhead
view the arrow keys rotate the camera and clicking the ground walks.
When you're inside a dome, the structure above you automatically turns
see-through so the camera never gets blocked.

## Many domes

The **Domes** toolbar button opens the site manager: every dome on the
site with its style, status, live load, and vision summary. Click a row
to select it (menus, stats, BOM, and the video window all follow the
selection), right-click for options (walk to, simulate construction,
demolish), and use **+ Add dome** to pick a style and click the ground
to have a crew build it there. Save/load round-trips the entire site.

Every dome carries the same monitoring computer: its own apex PTZ
camera, wall monitor, and **vision system** that runs simulated object
detection on whatever the camera sees — counting props and people in
view and building quantitative averages over time (objects in view,
occupancy %, most-seen types). The stats appear on the camera OSD
(`DETECT 3: Person, Worktable... · avg 2.7 · occ 12%`) and in the dome
manager rows.

## Panel Lab

Menu page `LAB` is the custom panel creator: pick a base surface (ply,
glass, solar...), stack hardware components — V-brackets (8 screws
each), L-brackets, corner gussets, foam seal, silicone, hinges,
latches, LED strips — and create it as a new panel type. Custom panels
join the panel-swap cycle and fill options, render their brackets along
panel edges, add their install minutes to the construction schedule,
and roll up in the BOM as total hardware counts (e.g. 315 V-brackets,
2,520 screws for a 3-bracket panel across a 105-panel dome).

## Manufacturing operation: construction sim, power, plumbing

**Construction simulation** (`File > Simulate construction`): a worker
in a hi-vis vest builds the dome element by element in real
trailer-manufacturing order — site/foundation, floor layout, frame from
the base ring up, hubs, entrance framing, sheathing bottom-up, cladding,
rough electrical conduit, plumbing rough-in, partitions, equipment, and
commissioning. Every step carries a real-world labor estimate; the
status bar shows step, elapsed vs. total labor-hours, and the projected
schedule (e.g. ~100 h / 12 days for the Timber Workshop). `[` / `]`
change the time scale, and right-clicking the status bar opens crew
options — add workers (diminishing returns: a crew of 3 cuts a 47-hour
dome to ~2 site-days) or cancel the job. The BOM includes the full
construction estimate.

**Electrical system** (`File > Electrify dome`): adds a battery bank,
charge controller, and LCD power meter, rings the outer wall with wall
outlets, and converts a south band of shell panels to solar. Devices
must be within cord reach (3 m) of an outlet to draw power — click a
lamp or appliance to switch it on/off. The **Power** panel (toolbar or
`N`) is the live meter: battery %, kWh, solar input, net flow, and
per-dome load, with time accelerated ×600 so charge/drain is visible.
Drain the battery and loads shed until solar recovers it. Plumbing
rough-in (hot/cold PEX + drain runs to every water fixture) is drawn on
the floor and priced in the BOM.

**Second dome** (`File > Build second dome`): dispatches the worker to
construct a smaller dome next door — watch it rise piece by piece. It
ships with a central **power column with four concentric outlets** and
lamps plugged in around it, and it ties into the *same* battery bank
and solar input as dome 1. The power panel then tracks consumption per
dome; toggle individual lamps in either dome to vary the loads.

## Preset setups

Four out-of-the-box designs ship in [presets.py](presets.py) — cycle
them with the toolbar **Preset** button or load one from menu page
`4·FILE`:

1. **Timber Workshop** — 3V lumber, metal brackets, concrete slab, full
   shop fit-out (default at startup)
2. **Glass Studio Loft** — 4V glass on a wood deck, office/lounge/bath
3. **Split-Log Homestead** — 2V hubless quarter-wedge frame, cedar
   shakes, kitchen/bath/lounge
4. **Grow Dome** — aluminum + polycarb greenhouse with grow racks

Applying a preset replaces the whole design — save yours first (`F5`).

## Workshop fit-out

The dome floor is divided into **10 sections** — a center hub plus nine
40° wedges. On menu page `2·ROOMS` each section gets a function (office,
bathroom, wood shop, metal shop, electronics, 3D printing, storage, grow
room, ...). Assigned sections get colored floor markings, and adjacent
wedges with *different* functions get partition walls with doorway gaps
(Low or Full, chosen under "Partition style") — same-function neighbors
merge into one larger room. The PTZ camera knows what it is looking at:
the video OSD reports `WATCH S4 WOOD SHOP · sawing, sanding, assembly`,
the contextual grounding for the vision system's likely-scenario
narrowing.

Menu page `3·PROPS` holds the placeable equipment library: worktables,
pegboard benches, machine stations, tool chests, shelving, crates,
filing cabinets, office desk/chair/whiteboard/sofa, kitchenette, toilet,
sink, shower stall, tripod and shop lights, and more. Pick one, aim at
the floor (green ghost = valid), click to place, `,` / `.` to rotate,
right-click or Esc to finish, and `Del` removes an aimed prop. Placed
lamps actually light the interior. Every prop carries weight, cost, and
power draw — the stats panel and exported BOM include the full fit-out
with a total equipment power budget.

## Install & run

```
py -3.12 -m pip install pygame moderngl numpy
py -3.12 dome_creator.py
```

(Any Python 3.10–3.13 with prebuilt wheels for `pygame`/`moderngl` works;
3.14 currently has no wheels for these packages.)

## What you can customize

| Category | Options |
| --- | --- |
| Structure | Frequency 1V–4V (flat-base class I), radius 2–15 m |
| Strut shape | Round tube, square tube, dimensional lumber, hex |
| Frame | Steel, aluminum, timber, PVC, bamboo + strut width + color |
| Panels | Recessed slot in every triangle; depth adjustable 5–95 % |
| Panel types | Open, plywood, glass window, acrylic window, polycarb, plastic sheeting, insulated SIP, shingle, metal, solar, canvas |
| Layers | Up to 3 stacked cladding shells: plastic film, house wrap, foam, asphalt shingles, cedar shakes, EPDM, green roof |
| Site | Bare ground, grass pad, gravel, concrete slab, wood deck, pavers |

Every choice feeds the live bill of materials: strut count and cut-list
classes (A/B/C...), hub count, cross-section-accurate frame weight, panel
areas/weights/costs, layer and foundation totals, floor/shell area, even
total solar kW.

## Frame engineering

- **Frame style** — `Hub & Strut` (classic: struts meet at hubs) or
  `Hubless Doubled`: every triangle is its own complete 3-strut frame
  (a 2V dome reads exactly "40 triangles × 3 struts = 120 pcs"),
  neighbours run side by side along shared edges and are through-bolted —
  the BOM counts the bolts instead of hubs.
- **Hub style** — `Node Puck` or `Metal Brackets` (steel gusset plates
  radiating along each incoming strut).
- **Quarter Wedge struts** — split a log in half, then quarters: the
  right-angle split faces point outward and the bark arc curves into the
  dome, so the panel recess forms against the curve naturally. "Wedge
  curve: Outside" flips it. The BOM reports **trees to harvest** at four
  quarter-wedges per log.

## Controls (RuneScape-style by default)

| Input | Action |
| --- | --- |
| `Left-click` ground | Walk there (yellow beacon marks the spot) |
| `Left-click` prop | Walk over and pick it up into the backpack |
| `Left-click` wall monitor | Walk over and take helm of the PTZ camera |
| `C` | Remote camera control from anywhere (toolbar: Cam) |
| `Left-click` lamp/appliance | Switch it on/off (walks over if far) |
| `N` / toolbar **Power** | Live power-system meter |
| `[` / `]` | Construction sim speed |
| `Del` | Pack the aimed prop into the backpack |
| Toolbar **Preset** | Cycle the out-of-the-box dome setups |
| `Shift+Click` panel | Swap that panel (Shift+right-click = back) |
| `Middle-drag` / `Arrows` | Rotate the orbit camera |
| Mouse wheel | Zoom the camera (PTZ zoom while at helm) |
| Toolbar | Build / Rooms / Props / Bag / Roof / POV / 360 / Save / BOM |
| `R` | Toggle transparent roof (aerial view of the interior) |
| `B` or `I` | Toggle the backpack |
| Backpack slot click | Place that item (ghost preview); right-click drops at feet |
| `P` | Switch first-person walk mode (mouse look, WASD, crosshair) |
| `M`, `1`–`4` | Menu, menu pages |
| `,` `.` | Rotate the placement ghost; `Del` removes an aimed prop |
| `Arrows` (at helm) | Pan / tilt; `PgUp`/`PgDn` zoom |
| `V` | Apply the aimed panel's type to all panels |
| `Tab` | 360° six-point projection (switches to first-person) |
| `G`, `H` | Guide grid, HUD |
| `F5` / `F9` / `F6` | Save / load design, export BOM |
| `Esc` | Cancel placement / release helm / quit (press twice) |

## Code map

- `materials.py` — the material database: frame materials, strut profiles,
  panel types, cladding layers, foundations, color palettes. All physical
  numbers (kg/m³, kg/m², $/kg, $/m²) live here; edit them and every stat
  updates.
- `dome_model.py` — parametric geodesic geometry (any frequency, base ring
  flattened onto the ground plane), the `panel_overrides` map that makes
  panels individually interchangeable in code, ray picking, stats and BOM.
- `mesh_builder.py` — turns the model into GPU geometry: profile-swept
  struts oriented radially, hubs, recessed panel triangles, offset layer
  shells, foundation discs.
- `workshop.py` — the workshop fit-out layer: room types with vision-system
  hints, the 10-section floor math, partition wall generation, and the
  full prop library (each prop is a small parametric model with weight /
  cost / wattage). Add a new prop by writing one builder function and one
  `PropType` entry.
- `overlay_ui.py` — menu / stats / help widgets drawn with pygame fonts.
- `dome_creator.py` — the app: renderer (normal + six-point), pattern
  shaders (shingles, solar cells, wood grain, concrete, deck planks...),
  input, and the live rebuild loop.

## Working with panels in code

Panels are keyed by their unit-sphere centroid direction, so assignments
survive radius and material changes:

```python
from dome_model import DomeModel

model = DomeModel()
model.config.panel_overrides[model.panels[0].key] = "Glass Window"
model.rebuild()
print(model.bom_text())
```
```

==========================================================================
======== FILE: materials.py ========
==========================================================================

```python
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
    FrameMaterial("Aluminum", 2700.0, 7.5, 0.70, 24.0, (0.72, 0.75, 0.78)),
    FrameMaterial("Timber (SPF)", 480.0, 2.0, 0.45, 7.0, (0.62, 0.47, 0.30)),
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
        watts_per_m2=base.watts_per_m2)
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
```

==========================================================================
======== FILE: workshop.py ========
==========================================================================

```python
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
```

==========================================================================
======== FILE: presets.py ========
==========================================================================

```python
"""
Out-of-the-box dome setups.

Each preset is a full design dict (the same format as dome_design.json),
so applying one swaps the entire configuration: structure, panels,
rooms, partitions, and furnishings. Cycle them with the toolbar Preset
button or load one from the File menu page.
"""

from __future__ import annotations

PRESETS: list[tuple[str, dict]] = [
    ("Timber Workshop", {
        "frequency": 3,
        "radius": 5.0,
        "strut_shape": "Dimensional Lumber",
        "strut_width": 0.06,
        "frame_material": "Timber (SPF)",
        "frame_color": "Material",
        "frame_style": "Hub & Strut",
        "hub_style": "Metal Brackets",
        "default_panel": "Plywood",
        "panel_color": "Natural",
        "recess_pct": 0.5,
        "layers": ["None", "None", "None"],
        "foundation": "Concrete Slab",
        "foundation_scale": 1.15,
        "partitions": "Markings",
        "sections": ["Assembly", "Wood Shop", "Wood Shop", "Storage",
                     "Metal Shop", "Metal Shop", "Unassigned", "Office",
                     "Unassigned", "Storage"],
        "props": [
            {"type": "Worktable", "x": 1.9, "y": -1.4, "yaw": 200.0},
            {"type": "Pegboard Bench", "x": 3.0, "y": 0.8, "yaw": 105.0},
            {"type": "Machine Station", "x": -2.9, "y": 0.9, "yaw": 90.0},
            {"type": "Tool Chest", "x": 2.5, "y": -2.5, "yaw": 30.0},
            {"type": "Shelving Unit", "x": -3.0, "y": -1.4, "yaw": 70.0},
            {"type": "Crate Stack", "x": -2.1, "y": -2.7, "yaw": 10.0},
            {"type": "Whiteboard", "x": 1.2, "y": 3.4, "yaw": 200.0},
            {"type": "Office Desk", "x": 2.6, "y": 2.8, "yaw": 220.0},
            {"type": "Office Chair", "x": 2.2, "y": 2.2, "yaw": 40.0},
            {"type": "Trash Bin", "x": 0.9, "y": -2.9, "yaw": 0.0},
            {"type": "Tripod Light", "x": 0.9, "y": -0.6, "yaw": 0.0},
            {"type": "Shop Light", "x": -1.3, "y": -0.4, "yaw": 0.0},
        ],
    }),
    ("Glass Studio Loft", {
        "frequency": 4,
        "radius": 5.0,
        "strut_shape": "Round Tube",
        "strut_width": 0.05,
        "frame_material": "Timber (SPF)",
        "frame_color": "Material",
        "frame_style": "Hub & Strut",
        "hub_style": "Node Puck",
        "default_panel": "Glass Window",
        "panel_color": "Natural",
        "recess_pct": 0.5,
        "layers": ["None", "None", "None"],
        "foundation": "Wood Deck",
        "foundation_scale": 1.15,
        "partitions": "Low Walls",
        "sections": ["Lounge", "Office", "Bathroom", "Unassigned",
                     "Studio", "Assembly", "Unassigned", "Unassigned",
                     "Unassigned", "Storage"],
        "props": [
            {"type": "Office Desk", "x": 1.2, "y": 3.2, "yaw": 25.0},
            {"type": "Office Chair", "x": 1.0, "y": 2.5, "yaw": 205.0},
            {"type": "Whiteboard", "x": 2.6, "y": 2.6, "yaw": 235.0},
            {"type": "Toilet", "x": -1.6, "y": 3.3, "yaw": 180.0},
            {"type": "Bathroom Sink", "x": -2.5, "y": 2.8, "yaw": 220.0},
            {"type": "Sofa", "x": -0.6, "y": -1.1, "yaw": 340.0},
            {"type": "Worktable", "x": 2.4, "y": -2.2, "yaw": 155.0},
            {"type": "Shelving Unit", "x": -3.1, "y": -1.4, "yaw": 70.0},
            {"type": "Crate Stack", "x": -2.4, "y": -2.8, "yaw": 0.0},
            {"type": "Tripod Light", "x": 0.9, "y": -0.6, "yaw": 0.0},
            {"type": "Shop Light", "x": -1.4, "y": 0.6, "yaw": 0.0},
        ],
    }),
    ("Split-Log Homestead", {
        "frequency": 2,
        "radius": 6.0,
        "strut_shape": "Quarter Wedge",
        "strut_width": 0.10,
        "frame_material": "Timber (SPF)",
        "frame_color": "Cedar",
        "frame_style": "Hubless Doubled",
        "hub_style": "Node Puck",
        "wedge_flip": False,
        "default_panel": "Plywood",
        "panel_color": "Sand",
        "recess_pct": 0.6,
        "layers": ["Cedar Shakes", "None", "None"],
        "foundation": "Gravel Pad",
        "foundation_scale": 1.2,
        "partitions": "Low Walls",
        "sections": ["Lounge", "Kitchen", "Bathroom", "Unassigned",
                     "Storage", "Unassigned", "Unassigned", "Office",
                     "Unassigned", "Unassigned"],
        "props": [
            {"type": "Kitchenette", "x": 1.6, "y": 3.9, "yaw": 205.0},
            {"type": "Toilet", "x": -1.8, "y": 4.0, "yaw": 175.0},
            {"type": "Bathroom Sink", "x": -2.8, "y": 3.4, "yaw": 215.0},
            {"type": "Shower Stall", "x": -3.6, "y": 2.2, "yaw": 245.0},
            {"type": "Sofa", "x": 0.4, "y": -1.4, "yaw": 350.0},
            {"type": "Office Desk", "x": 3.6, "y": -2.2, "yaw": 130.0},
            {"type": "Office Chair", "x": 3.0, "y": -1.8, "yaw": 310.0},
            {"type": "Crate Stack", "x": -3.4, "y": -2.4, "yaw": 20.0},
            {"type": "Shelving Unit", "x": -2.4, "y": -3.6, "yaw": 35.0},
            {"type": "Trash Bin", "x": 2.4, "y": 1.4, "yaw": 0.0},
            {"type": "Tripod Light", "x": 1.1, "y": -0.4, "yaw": 0.0},
            {"type": "Tripod Light", "x": -1.5, "y": 1.0, "yaw": 0.0},
        ],
    }),
    ("Grow Dome", {
        "frequency": 3,
        "radius": 5.0,
        "strut_shape": "Round Tube",
        "strut_width": 0.04,
        "frame_material": "Aluminum",
        "frame_color": "Material",
        "frame_style": "Hub & Strut",
        "hub_style": "Node Puck",
        "default_panel": "Polycarb Twinwall",
        "panel_color": "Natural",
        "recess_pct": 0.4,
        "layers": ["None", "None", "None"],
        "foundation": "Grass Pad",
        "foundation_scale": 1.2,
        "partitions": "Markings",
        "sections": ["Assembly", "Grow Room", "Grow Room", "Grow Room",
                     "Storage", "Grow Room", "Grow Room", "Grow Room",
                     "Unassigned", "Kitchen"],
        "props": [
            {"type": "Shelving Unit", "x": 2.6, "y": 2.2, "yaw": 220.0},
            {"type": "Shelving Unit", "x": -2.6, "y": 2.2, "yaw": 140.0},
            {"type": "Shelving Unit", "x": 3.2, "y": -1.2, "yaw": 250.0},
            {"type": "Shelving Unit", "x": -3.2, "y": -1.2, "yaw": 110.0},
            {"type": "Worktable", "x": 0.0, "y": -2.6, "yaw": 0.0},
            {"type": "Crate Stack", "x": 1.6, "y": -3.2, "yaw": 15.0},
            {"type": "Kitchenette", "x": -1.8, "y": -3.4, "yaw": 25.0},
            {"type": "Trash Bin", "x": 0.9, "y": -1.6, "yaw": 0.0},
            {"type": "Tripod Light", "x": 1.2, "y": 0.8, "yaw": 0.0},
            {"type": "Tripod Light", "x": -1.2, "y": 0.8, "yaw": 0.0},
            {"type": "Shop Light", "x": 0.0, "y": 2.4, "yaw": 0.0},
        ],
    }),
]

PRESET_NAMES = [name for name, _ in PRESETS]

# The dome a worker constructs as the site's second unit: a power spoke
# with a central column of outlets and lamps plugged in around it.
SECOND_DOME = {
    "frequency": 2,
    "radius": 4.0,
    "strut_shape": "Dimensional Lumber",
    "strut_width": 0.06,
    "frame_material": "Timber (SPF)",
    "frame_color": "Material",
    "frame_style": "Hub & Strut",
    "hub_style": "Metal Brackets",
    "default_panel": "Plywood",
    "panel_color": "Snow",
    "recess_pct": 0.5,
    "layers": ["None", "None", "None"],
    "foundation": "Concrete Slab",
    "foundation_scale": 1.15,
    "partitions": "Markings",
    "sections": ["Assembly", "Storage", "Unassigned", "Unassigned",
                 "Lounge", "Lounge", "Unassigned", "Unassigned",
                 "Unassigned", "Storage"],
    "props": [
        {"type": "Power Column", "x": 0.0, "y": 0.0, "yaw": 0.0},
        {"type": "Tripod Light", "x": 1.8, "y": 1.8, "yaw": 0.0,
         "on": True},
        {"type": "Tripod Light", "x": -1.8, "y": 1.8, "yaw": 0.0,
         "on": True},
        {"type": "Tripod Light", "x": 1.8, "y": -1.8, "yaw": 0.0,
         "on": False},
        {"type": "Tripod Light", "x": -1.8, "y": -1.8, "yaw": 0.0,
         "on": False},
        {"type": "Sofa", "x": 0.2, "y": -2.6, "yaw": 355.0},
        {"type": "Worktable", "x": 2.4, "y": -0.4, "yaw": 100.0},
        {"type": "Crate Stack", "x": -2.5, "y": -0.6, "yaw": 30.0},
    ],
}
```

==========================================================================
======== FILE: dome_model.py ========
==========================================================================

```python
"""
Parametric geodesic dome model.

Builds class-I geodesic domes at any frequency, exposes struts / hubs /
panel slots, tracks per-panel overrides (the interchangeable recessed
panels), and computes a complete live bill of materials: lengths, areas,
weights, and costs for frame, panels, cladding layers, and foundation.
"""

from __future__ import annotations

import json
import math
import string
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from materials import (
    FRAME_COLORS,
    FRAME_MATERIALS,
    FOUNDATION_TYPES,
    LAYER_TYPES,
    PANEL_COLORS,
    PANEL_TYPES,
    PANEL_TYPE_BY_NAME,
    STRUT_SHAPES,
    FoundationType,
    FrameMaterial,
    LayerType,
    PanelType,
    StrutShape,
)


def normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        return v.copy()
    return v / n


def _icosahedron() -> tuple[np.ndarray, np.ndarray]:
    g = (1.0 + math.sqrt(5.0)) * 0.5
    verts = np.array([
        [-1, g, 0], [1, g, 0], [-1, -g, 0], [1, -g, 0],
        [0, -1, g], [0, 1, g], [0, -1, -g], [0, 1, -g],
        [g, 0, -1], [g, 0, 1], [-g, 0, -1], [-g, 0, 1],
    ], dtype=np.float64)
    verts = np.array([normalize(v) for v in verts])
    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int32)
    return verts, faces


def _rotate_vertex_up(verts: np.ndarray) -> np.ndarray:
    top = verts[np.argmax(verts[:, 2])]
    target = np.array([0.0, 0.0, 1.0])
    axis = np.cross(top, target)
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return verts
    axis /= length
    angle = math.acos(float(np.clip(np.dot(top, target), -1.0, 1.0)))
    c, s = math.cos(angle), math.sin(angle)
    rotated = []
    for v in verts:
        rotated.append(
            v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)
        )
    return np.array(rotated)


@dataclass
class GeodesicData:
    """Unit-radius dome in 'dome frame': sphere center at origin."""
    verts: np.ndarray                      # (N, 3) unit sphere, base flattened
    faces: np.ndarray                      # (M, 3) vertex indices
    edges: list[tuple[int, int]]
    base_z: float                          # z of the flattened base plane
    base_ring: list[int]                   # indices of base-ring vertices


_GEO_CACHE: dict[int, GeodesicData] = {}


def build_geodesic(frequency: int) -> GeodesicData:
    """Subdivide an icosahedron, cut at the vertex ring nearest the equator,
    and flatten that ring onto a single plane (flat-base adaptation)."""
    if frequency in _GEO_CACHE:
        return _GEO_CACHE[frequency]

    base_verts, base_faces = _icosahedron()
    base_verts = _rotate_vertex_up(base_verts)

    lookup: dict[tuple, int] = {}
    verts: list[np.ndarray] = []
    faces: list[tuple[int, int, int]] = []

    def add_vert(p: np.ndarray) -> int:
        p = normalize(p)
        key = tuple(np.round(p, 6))
        idx = lookup.get(key)
        if idx is not None:
            return idx
        idx = len(verts)
        lookup[key] = idx
        verts.append(p)
        return idx

    f = frequency
    for ia, ib, ic in base_faces:
        a, b, c = base_verts[ia], base_verts[ib], base_verts[ic]
        grid: dict[tuple[int, int], int] = {}
        for i in range(f + 1):
            for j in range(f + 1 - i):
                point = a * (f - i - j) + b * i + c * j
                grid[(i, j)] = add_vert(point)
        for i in range(f):
            for j in range(f - i):
                faces.append((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
                if i + j < f - 1:
                    faces.append((
                        grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]
                    ))

    varr = np.array(verts)

    # Cluster vertex z-values into latitude rings, pick the ring nearest the
    # equator (preferring the one just below for odd frequencies), and
    # flatten it into a plane so the dome sits cleanly on the ground.
    order = np.argsort(-varr[:, 2])
    clusters: list[list[int]] = []
    for idx in order:
        z = varr[idx, 2]
        if clusters and abs(varr[clusters[-1][-1], 2] - z) < 0.045:
            clusters[-1].append(int(idx))
        else:
            clusters.append([int(idx)])

    def cluster_rank(cluster: list[int]) -> tuple:
        mean = float(np.mean([varr[i, 2] for i in cluster]))
        return (round(abs(mean), 4), 0 if mean <= 1e-6 else 1)

    candidates = [c for c in clusters if len(c) >= 3]
    base_cluster = min(candidates, key=cluster_rank)
    base_z = float(np.mean([varr[i, 2] for i in base_cluster]))
    for i in base_cluster:
        varr[i, 2] = base_z

    base_set = set(base_cluster)
    kept_faces = [
        face for face in faces
        if all(varr[i, 2] >= base_z - 1e-5 for i in face)
    ]

    used = sorted({i for face in kept_faces for i in face})
    remap = {old: new for new, old in enumerate(used)}
    out_verts = varr[used]
    out_faces = np.array(
        [[remap[a], remap[b], remap[c]] for a, b, c in kept_faces],
        dtype=np.int32,
    )
    edge_set = {
        tuple(sorted((face[i], face[(i + 1) % 3])))
        for face in out_faces for i in range(3)
    }
    ring = [remap[i] for i in base_cluster if i in remap]

    data = GeodesicData(
        verts=out_verts,
        faces=out_faces,
        edges=sorted(edge_set),
        base_z=base_z,
        base_ring=ring,
    )
    _GEO_CACHE[frequency] = data
    return data


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FRAME_STYLES = ["Hub & Strut", "Hubless Doubled"]
HUB_STYLES = ["Node Puck", "Metal Brackets"]

BOLT_COST = 1.6            # per through-bolt in hubless mode
BOLT_WEIGHT = 0.09
WEDGES_PER_TREE = 4        # split a log in half, then quarters


@dataclass
class DomeConfig:
    frequency: int = 3
    radius: float = 5.0
    strut_shape: int = 2          # index into STRUT_SHAPES (lumber)
    strut_width: float = 0.06     # m
    frame_style: str = "Hub & Strut"
    hub_style: str = "Node Puck"
    wedge_flip: bool = False      # quarter wedge: curve outward instead
    frame_material: int = 2       # index into FRAME_MATERIALS (timber)
    frame_color: int = 0          # index into FRAME_COLORS (material color)
    default_panel: str = "Plywood"
    panel_color: int = 0          # index into PANEL_COLORS
    recess_pct: float = 0.50      # 0..1 of strut depth
    layers: list[str] = field(default_factory=lambda: ["None", "None", "None"])
    foundation: str = "Concrete Slab"
    foundation_scale: float = 1.15
    panel_overrides: dict[str, str] = field(default_factory=dict)
    sections: list[str] = field(
        default_factory=lambda: ["Unassigned"] * 10)
    partitions: str = "Markings"
    props: list[dict] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frequency": self.frequency,
            "radius": self.radius,
            "strut_shape": STRUT_SHAPES[self.strut_shape].name,
            "strut_width": self.strut_width,
            "frame_material": FRAME_MATERIALS[self.frame_material].name,
            "frame_color": FRAME_COLORS[self.frame_color].name,
            "default_panel": self.default_panel,
            "panel_color": PANEL_COLORS[self.panel_color].name,
            "recess_pct": self.recess_pct,
            "layers": list(self.layers),
            "foundation": self.foundation,
            "foundation_scale": self.foundation_scale,
            "panel_overrides": dict(self.panel_overrides),
            "sections": list(self.sections),
            "partitions": self.partitions,
            "props": [dict(p) for p in self.props],
            "inventory": list(self.inventory),
            "frame_style": self.frame_style,
            "hub_style": self.hub_style,
            "wedge_flip": self.wedge_flip,
        }

    @staticmethod
    def from_dict(data: dict) -> "DomeConfig":
        cfg = DomeConfig()
        cfg.frequency = int(data.get("frequency", cfg.frequency))
        cfg.radius = float(data.get("radius", cfg.radius))
        cfg.strut_width = float(data.get("strut_width", cfg.strut_width))
        cfg.recess_pct = float(data.get("recess_pct", cfg.recess_pct))
        cfg.foundation_scale = float(
            data.get("foundation_scale", cfg.foundation_scale)
        )

        def index_of(items, name, fallback):
            for i, item in enumerate(items):
                if item.name == name:
                    return i
            return fallback

        cfg.strut_shape = index_of(
            STRUT_SHAPES, data.get("strut_shape"), cfg.strut_shape)
        cfg.frame_material = index_of(
            FRAME_MATERIALS, data.get("frame_material"), cfg.frame_material)
        cfg.frame_color = index_of(
            FRAME_COLORS, data.get("frame_color"), cfg.frame_color)
        cfg.panel_color = index_of(
            PANEL_COLORS, data.get("panel_color"), cfg.panel_color)

        if data.get("default_panel") in PANEL_TYPE_BY_NAME:
            cfg.default_panel = data["default_panel"]
        layer_names = {l.name for l in LAYER_TYPES}
        cfg.layers = [
            name if name in layer_names else "None"
            for name in (list(data.get("layers", [])) + ["None"] * 3)[:3]
        ]
        foundation_names = {f.name for f in FOUNDATION_TYPES}
        if data.get("foundation") in foundation_names:
            cfg.foundation = data["foundation"]
        cfg.panel_overrides = {
            str(k): v for k, v in dict(data.get("panel_overrides", {})).items()
            if v in PANEL_TYPE_BY_NAME
        }

        import workshop
        room_names = set(workshop.ROOM_TYPE_BY_NAME)
        cfg.sections = [
            name if name in room_names else "Unassigned"
            for name in (list(data.get("sections", []))
                         + ["Unassigned"] * 10)[:10]
        ]
        if data.get("partitions") in workshop.PARTITION_MODES:
            cfg.partitions = data["partitions"]
        cfg.props = [
            {"type": p["type"], "x": float(p.get("x", 0.0)),
             "y": float(p.get("y", 0.0)), "yaw": float(p.get("yaw", 0.0)),
             "on": bool(p.get("on", True))}
            for p in list(data.get("props", []))
            if isinstance(p, dict)
            and p.get("type") in workshop.PROP_TYPE_BY_NAME
        ]
        cfg.inventory = [
            name for name in list(data.get("inventory", []))
            if name in workshop.PROP_TYPE_BY_NAME
        ][:28]
        if data.get("frame_style") in FRAME_STYLES:
            cfg.frame_style = data["frame_style"]
        if data.get("hub_style") in HUB_STYLES:
            cfg.hub_style = data["hub_style"]
        cfg.wedge_flip = bool(data.get("wedge_flip", False))
        return cfg


@dataclass
class PanelSlot:
    key: str
    face: tuple[int, int, int]
    world_verts: np.ndarray          # (3, 3)
    centroid: np.ndarray
    area: float
    panel_type: PanelType


class DomeModel:
    """Config + generated world-space geometry + stats."""

    def __init__(self, config: DomeConfig | None = None,
                 origin: tuple[float, float] = (0.0, 0.0)) -> None:
        self.config = config or DomeConfig()
        self.origin = np.array([origin[0], origin[1], 0.0])
        self.geo: GeodesicData | None = None
        self.world_verts = np.zeros((0, 3))
        self.sphere_center = np.zeros(3)
        self.panels: list[PanelSlot] = []
        self.struts: list[tuple[np.ndarray, np.ndarray, float]] = []
        self.hubs: list[tuple[np.ndarray, list[np.ndarray]]] = []
        self.bolt_points: list[np.ndarray] = []
        self.rebuild()

    # -- convenience accessors ------------------------------------------------

    @property
    def shape(self) -> StrutShape:
        return STRUT_SHAPES[self.config.strut_shape]

    @property
    def material(self) -> FrameMaterial:
        return FRAME_MATERIALS[self.config.frame_material]

    @property
    def foundation(self) -> FoundationType:
        for f in FOUNDATION_TYPES:
            if f.name == self.config.foundation:
                return f
        return FOUNDATION_TYPES[0]

    @property
    def active_layers(self) -> list[LayerType]:
        out = []
        for name in self.config.layers:
            layer = next((l for l in LAYER_TYPES if l.name == name), None)
            if layer and layer.name != "None":
                out.append(layer)
        return out

    @property
    def strut_depth(self) -> float:
        return self.shape.depth(self.config.strut_width)

    @property
    def floor_radius(self) -> float:
        base_z = self.geo.base_z if self.geo else 0.0
        return self.config.radius * math.sqrt(max(0.0, 1.0 - base_z ** 2))

    def section_at(self, x: float, y: float) -> int:
        import workshop
        return workshop.section_of(x - float(self.origin[0]),
                                   y - float(self.origin[1]),
                                   self.floor_radius)

    def light_positions(self) -> list[tuple[float, float, float]]:
        """World positions of powered lamp props (shader point lights)."""
        import workshop
        fh = self.foundation.height
        ox, oy = float(self.origin[0]), float(self.origin[1])
        out = []
        for entry in self.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is not None and prop.light_z is not None \
                    and entry.get("on", True):
                out.append((ox + float(entry.get("x", 0.0)),
                            oy + float(entry.get("y", 0.0)),
                            fh + prop.light_z))
        return out[:16]

    def frame_color_rgb(self) -> tuple[float, float, float]:
        named = FRAME_COLORS[self.config.frame_color]
        if named.rgb[0] < 0:
            return self.material.color
        return named.rgb

    def panel_tint(self) -> tuple[float, float, float]:
        return PANEL_COLORS[self.config.panel_color].rgb

    # -- geometry -------------------------------------------------------------

    def rebuild(self) -> None:
        cfg = self.config
        self.geo = build_geodesic(cfg.frequency)
        radius = cfg.radius
        base_lift = self.foundation.height
        # World: dome base plane sits on top of the foundation, dome axis at
        # the origin. Sphere center is below/at the base plane.
        self.sphere_center = np.array(
            [float(self.origin[0]), float(self.origin[1]),
             base_lift - self.geo.base_z * radius]
        )
        self.world_verts = self.geo.verts * radius + self.sphere_center

        self.struts = []
        self.hubs = []
        self.bolt_points = []
        if cfg.frame_style == "Hubless Doubled":
            # Every triangle is its own complete 3-strut frame, shrunk
            # toward its centroid so neighbours run side by side along
            # the shared edge, bolted together — no hubs.
            inset = cfg.strut_width * 0.75
            for face in self.geo.faces:
                tri = self.world_verts[list(face)]
                centroid = tri.mean(axis=0)
                pulled = []
                for v in tri:
                    to_c = centroid - v
                    d = float(np.linalg.norm(to_c))
                    pulled.append(v + to_c * (min(inset, d * 0.4) / d))
                for i in range(3):
                    p0, p1 = pulled[i], pulled[(i + 1) % 3]
                    self.struts.append(
                        (p0, p1, float(np.linalg.norm(p1 - p0))))
            for a, b in self.geo.edges:
                pa, pb = self.world_verts[a], self.world_verts[b]
                for frac in (0.33, 0.67):
                    self.bolt_points.append(pa + (pb - pa) * frac)
        else:
            incident: dict[int, list[np.ndarray]] = {}
            for a, b in self.geo.edges:
                pa, pb = self.world_verts[a], self.world_verts[b]
                self.struts.append(
                    (pa, pb, float(np.linalg.norm(pb - pa))))
                incident.setdefault(a, []).append(normalize(pb - pa))
                incident.setdefault(b, []).append(normalize(pa - pb))
            self.hubs = [
                (self.world_verts[i], incident.get(i, []))
                for i in range(len(self.world_verts))
            ]

        self.panels = []
        for face in self.geo.faces:
            tri = self.world_verts[list(face)]
            centroid = tri.mean(axis=0)
            unit_c = normalize(
                self.geo.verts[list(face)].mean(axis=0)
            )
            key = f"{unit_c[0]:.3f},{unit_c[1]:.3f},{unit_c[2]:.3f}"
            area = 0.5 * float(np.linalg.norm(
                np.cross(tri[1] - tri[0], tri[2] - tri[0])
            ))
            type_name = cfg.panel_overrides.get(key, cfg.default_panel)
            panel_type = PANEL_TYPE_BY_NAME.get(
                type_name, PANEL_TYPE_BY_NAME[cfg.default_panel]
            )
            self.panels.append(PanelSlot(
                key=key,
                face=tuple(int(i) for i in face),
                world_verts=tri,
                centroid=centroid,
                area=area,
                panel_type=panel_type,
            ))

    # -- panel interchange ----------------------------------------------------

    def cycle_panel(self, key: str, step: int) -> str:
        import materials
        current = self.config.panel_overrides.get(key, self.config.default_panel)
        names = materials.panel_type_names()
        idx = ((names.index(current) if current in names else 0)
               + step) % len(names)
        self.config.panel_overrides[key] = names[idx]
        return names[idx]

    def set_panel(self, key: str, name: str) -> None:
        if name in PANEL_TYPE_BY_NAME:
            self.config.panel_overrides[key] = name

    def set_all_panels(self, name: str) -> None:
        if name in PANEL_TYPE_BY_NAME:
            self.config.default_panel = name
            self.config.panel_overrides.clear()

    def panel_at(self, key: str) -> PanelSlot | None:
        for p in self.panels:
            if p.key == key:
                return p
        return None

    # -- ray picking ----------------------------------------------------------

    def pick_panel(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        max_distance: float = 120.0,
    ) -> tuple[PanelSlot | None, float]:
        """Möller–Trumbore over all panel slots; returns nearest hit."""
        best: PanelSlot | None = None
        best_t = max_distance
        o = np.asarray(origin, dtype=np.float64)
        d = normalize(direction)
        for panel in self.panels:
            v0, v1, v2 = panel.world_verts
            e1 = v1 - v0
            e2 = v2 - v0
            pvec = np.cross(d, e2)
            det = float(np.dot(e1, pvec))
            if abs(det) < 1e-9:
                continue
            inv = 1.0 / det
            tvec = o - v0
            u = float(np.dot(tvec, pvec)) * inv
            if u < 0.0 or u > 1.0:
                continue
            qvec = np.cross(tvec, e1)
            v = float(np.dot(d, qvec)) * inv
            if v < 0.0 or u + v > 1.0:
                continue
            t = float(np.dot(e2, qvec)) * inv
            if 0.05 < t < best_t:
                best_t = t
                best = panel
        return best, best_t

    # -- stats / bill of materials --------------------------------------------

    def layer_covered_panels(self) -> list[PanelSlot]:
        """Cladding layers skip open slots and windows."""
        return [
            p for p in self.panels
            if p.panel_type.name != "Open" and not p.panel_type.is_window
        ]

    def stats(self) -> dict:
        cfg = self.config
        shape = self.shape
        mat = self.material

        # Struts grouped into length classes (A, B, C, ...).
        groups: dict[float, int] = {}
        total_len = 0.0
        for _, _, length in self.struts:
            key = round(length, 2)
            groups[key] = groups.get(key, 0) + 1
            total_len += length
        classes = [
            (string.ascii_uppercase[i % 26], length, count)
            for i, (length, count) in enumerate(
                sorted(groups.items(), key=lambda kv: -kv[0])
            )
        ]

        cs_area = shape.cross_section_area(cfg.strut_width)
        frame_weight = total_len * cs_area * mat.density
        frame_cost = frame_weight * mat.cost_per_kg * 1.15

        hub_count = len(self.hubs)
        hub_scale = (cfg.strut_width / 0.05) ** 1.5
        if cfg.hub_style == "Metal Brackets":
            hub_scale *= 0.85               # plates weigh less than pucks
            hub_cost_scale = hub_scale * 1.25
        else:
            hub_cost_scale = hub_scale
        hub_weight = hub_count * mat.hub_weight * hub_scale
        hub_cost = hub_count * mat.hub_cost * hub_cost_scale

        bolt_count = len(self.bolt_points)
        bolt_weight = bolt_count * BOLT_WEIGHT
        bolt_cost = bolt_count * BOLT_COST
        hub_weight += bolt_weight
        hub_cost += bolt_cost

        # Quarter wedges are harvested four to a log.
        trees_required = 0
        if shape.kind == "wedge":
            trees_required = math.ceil(len(self.struts) / WEDGES_PER_TREE)

        # Panels grouped by type.
        panel_groups: dict[str, dict] = {}
        panel_weight = 0.0
        panel_cost = 0.0
        solar_watts = 0.0
        for p in self.panels:
            t = p.panel_type
            g = panel_groups.setdefault(
                t.name, {"count": 0, "area": 0.0, "weight": 0.0, "cost": 0.0}
            )
            g["count"] += 1
            g["area"] += p.area
            g["weight"] += p.area * t.area_weight
            g["cost"] += p.area * t.cost_per_m2
            panel_weight += p.area * t.area_weight
            panel_cost += p.area * t.cost_per_m2
            solar_watts += p.area * t.watts_per_m2

        covered_area = sum(p.area for p in self.layer_covered_panels())
        layer_rows = []
        layer_weight = 0.0
        layer_cost = 0.0
        for layer in self.active_layers:
            w = covered_area * layer.area_weight
            c = covered_area * layer.cost_per_m2
            layer_rows.append((layer.name, covered_area, w, c))
            layer_weight += w
            layer_cost += c

        foundation = self.foundation
        f_radius = cfg.radius * cfg.foundation_scale
        f_area = math.pi * f_radius ** 2 if foundation.height > 0 else 0.0
        if foundation.name == "Bare Ground":
            f_area = 0.0
        f_weight = f_area * foundation.weight_per_m2
        f_cost = f_area * foundation.cost_per_m2

        base_z = self.geo.base_z
        base_ring_radius = math.sqrt(max(0.0, 1.0 - base_z * base_z))
        floor_area = math.pi * (base_ring_radius * cfg.radius) ** 2
        surface_area = sum(p.area for p in self.panels)
        height = (1.0 - base_z) * cfg.radius

        # Workshop fit-out: props and partition walls.
        import workshop
        prop_groups: dict[str, dict] = {}
        prop_weight = prop_cost = prop_watts = 0.0
        for entry in cfg.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is None:
                continue
            g = prop_groups.setdefault(
                prop.name, {"count": 0, "weight": 0.0, "cost": 0.0,
                            "watts": 0.0})
            g["count"] += 1
            g["weight"] += prop.weight
            g["cost"] += prop.cost
            g["watts"] += prop.watts
            prop_weight += prop.weight
            prop_cost += prop.cost
            prop_watts += prop.watts

        wall_segments = workshop.partition_segments(self)
        wall_area = sum(s["length"] * s["height"] for s in wall_segments)
        wall_weight = wall_area * workshop.WALL_WEIGHT_PER_M2
        wall_cost = wall_area * workshop.WALL_COST_PER_M2

        wire_runs = workshop.wiring_runs(self)
        wire_len = sum(r["length"] for r in wire_runs)
        wire_cost = wire_len * workshop.WIRE_COST_PER_M
        pipe_runs = workshop.plumbing_runs(self)
        pex_len = sum(r["length"] for r in pipe_runs) * 2.0   # hot + cold
        drain_len = sum(r["length"] for r in pipe_runs)
        plumbing_cost = (pex_len * workshop.PEX_COST_PER_M
                         + drain_len * workshop.DRAIN_COST_PER_M
                         + len(pipe_runs) * workshop.FIXTURE_ROUGH_COST)

        assigned_sections = sum(
            1 for name in cfg.sections if name != "Unassigned")

        # Custom-panel hardware rollup (brackets, screws, seals...).
        import materials
        hardware: dict[str, int] = {}
        hardware_screws = 0
        for p in self.panels:
            definition = materials.CUSTOM_PANEL_DEFS.get(p.panel_type.name)
            if not definition:
                continue
            for comp_name, qty in definition.get("components", {}).items():
                comp = materials.PANEL_COMPONENT_BY_NAME.get(comp_name)
                if comp is None or qty <= 0:
                    continue
                hardware[comp_name] = hardware.get(comp_name, 0) + qty
                hardware_screws += comp.screws_each * qty

        structure_weight = (frame_weight + hub_weight + panel_weight
                            + layer_weight + prop_weight + wall_weight)
        total_cost = (frame_cost + hub_cost + panel_cost + layer_cost
                      + f_cost + prop_cost + wall_cost
                      + wire_cost + plumbing_cost)

        return {
            "frequency": cfg.frequency,
            "radius": cfg.radius,
            "height": height,
            "floor_area": floor_area,
            "surface_area": surface_area,
            "strut_classes": classes,
            "strut_count": len(self.struts),
            "strut_total_len": total_len,
            "hub_count": hub_count,
            "panel_groups": panel_groups,
            "panel_count": len(self.panels),
            "frame_weight": frame_weight,
            "frame_cost": frame_cost,
            "hub_weight": hub_weight,
            "hub_cost": hub_cost,
            "panel_weight": panel_weight,
            "panel_cost": panel_cost,
            "layer_rows": layer_rows,
            "layer_weight": layer_weight,
            "layer_cost": layer_cost,
            "foundation_name": foundation.name,
            "foundation_area": f_area,
            "foundation_weight": f_weight,
            "foundation_cost": f_cost,
            "structure_weight": structure_weight,
            "total_cost": total_cost,
            "solar_watts": solar_watts,
            "prop_groups": prop_groups,
            "prop_count": len(cfg.props),
            "prop_weight": prop_weight,
            "prop_cost": prop_cost,
            "prop_watts": prop_watts,
            "wall_count": len(wall_segments),
            "wall_area": wall_area,
            "wall_weight": wall_weight,
            "wall_cost": wall_cost,
            "assigned_sections": assigned_sections,
            "frame_style": cfg.frame_style,
            "hub_style": cfg.hub_style,
            "bolt_count": bolt_count,
            "trees_required": trees_required,
            "wire_runs": len(wire_runs),
            "wire_len": wire_len,
            "wire_cost": wire_cost,
            "pipe_fixtures": len(pipe_runs),
            "pex_len": pex_len,
            "drain_len": drain_len,
            "plumbing_cost": plumbing_cost,
            "hardware": hardware,
            "hardware_screws": hardware_screws,
        }

    def bom_text(self) -> str:
        s = self.stats()
        cfg = self.config
        lines: list[str] = []
        add = lines.append
        add("=" * 62)
        add("GEODESIC DOME — BILL OF MATERIALS")
        add("=" * 62)
        add(f"Frequency:        {cfg.frequency}V (flat-base class I)")
        add(f"Radius:           {cfg.radius:.2f} m")
        add(f"Height:           {s['height']:.2f} m")
        add(f"Floor area:       {s['floor_area']:.1f} m^2")
        add(f"Surface area:     {s['surface_area']:.1f} m^2")
        add("")
        add("-- FRAME " + "-" * 53)
        add(f"Material:         {self.material.name}")
        add(f"Strut profile:    {self.shape.name}, "
            f"{cfg.strut_width * 100:.1f} cm wide")
        add(f"Frame style:      {s['frame_style']}")
        add(f"Struts:           {s['strut_count']} pcs, "
            f"{s['strut_total_len']:.1f} m total")
        for label, length, count in s["strut_classes"]:
            add(f"   {label}: {count:3d} x {length:.2f} m")
        if s["trees_required"]:
            add(f"Trees to harvest: {s['trees_required']} logs "
                f"({WEDGES_PER_TREE} quarter-wedges each)")
        if s["bolt_count"]:
            add(f"Edge bolts:       {s['bolt_count']} pcs (hubless joins)")
        else:
            add(f"Hubs:             {s['hub_count']} pcs "
                f"({s['hub_style']})")
        add(f"Frame weight:     {s['frame_weight']:.1f} kg "
            f"(+ hubs {s['hub_weight']:.1f} kg)")
        add(f"Frame cost:       ${s['frame_cost']:,.0f} "
            f"(+ hubs ${s['hub_cost']:,.0f})")
        add("")
        add("-- PANELS " + "-" * 52)
        for name, g in sorted(s["panel_groups"].items()):
            add(f"   {name:<18} {g['count']:3d} pcs  {g['area']:7.1f} m^2  "
                f"{g['weight']:8.1f} kg  ${g['cost']:,.0f}")
        if s["solar_watts"] > 0:
            add(f"   Solar capacity:  {s['solar_watts'] / 1000.0:.2f} kW")
        add("")
        add("-- CLADDING LAYERS " + "-" * 43)
        if s["layer_rows"]:
            for name, area, weight, cost in s["layer_rows"]:
                add(f"   {name:<18} {area:7.1f} m^2  {weight:8.1f} kg  "
                    f"${cost:,.0f}")
        else:
            add("   (none)")
        add("")
        add("-- FOUNDATION " + "-" * 48)
        add(f"   {s['foundation_name']:<18} {s['foundation_area']:7.1f} m^2  "
            f"{s['foundation_weight']:8.1f} kg  ${s['foundation_cost']:,.0f}")
        add("")
        add("-- WORKSHOP FIT-OUT " + "-" * 42)
        import workshop
        for i, name in enumerate(cfg.sections):
            if name != "Unassigned":
                add(f"   {workshop.section_label(i):<14} {name}")
        if s["wall_count"]:
            add(f"   Partition walls   {s['wall_count']} pcs  "
                f"{s['wall_area']:.1f} m^2  {s['wall_weight']:.0f} kg  "
                f"${s['wall_cost']:,.0f}")
        if s["prop_groups"]:
            for name, g in sorted(s["prop_groups"].items()):
                watts = f"  {g['watts']:.0f} W" if g["watts"] else ""
                add(f"   {name:<18} {g['count']:3d} pcs  "
                    f"{g['weight']:6.0f} kg  ${g['cost']:,.0f}{watts}")
            add(f"   Equipment power:  {s['prop_watts']:,.0f} W")
        if not s["prop_groups"] and not s["wall_count"]:
            add("   (empty)")
        add("")
        if s["wire_runs"]:
            add("-- ELECTRICAL ROUGH-IN " + "-" * 39)
            add(f"   Wire runs:        {s['wire_runs']} circuits, "
                f"{s['wire_len']:.1f} m conduit  ${s['wire_cost']:,.0f}")
        if s["pipe_fixtures"]:
            add("-- PLUMBING ROUGH-IN " + "-" * 41)
            add(f"   Fixtures:         {s['pipe_fixtures']}")
            add(f"   PEX supply:       {s['pex_len']:.1f} m "
                f"(hot + cold)")
            add(f"   Drain/waste:      {s['drain_len']:.1f} m")
            add(f"   Rough-in cost:    ${s['plumbing_cost']:,.0f}")
        if s["hardware"]:
            add("-- PANEL HARDWARE (custom panels) " + "-" * 28)
            for comp_name, qty in sorted(s["hardware"].items()):
                add(f"   {comp_name:<18} {qty} pcs")
            add(f"   Screws:           {s['hardware_screws']} pcs")
        if s["wire_runs"] or s["pipe_fixtures"] or s["hardware"]:
            add("")
        hours = getattr(self, "construction_hours", 0.0)
        if hours:
            add(f"ESTIMATED CONSTRUCTION: {hours:,.0f} labor-hours "
                f"(~{hours / 8.0:,.0f} days @ 8 h, 1 worker)")
        add("=" * 62)
        add(f"STRUCTURE WEIGHT (above foundation): "
            f"{s['structure_weight']:,.0f} kg")
        add(f"TOTAL ESTIMATED COST:                ${s['total_cost']:,.0f}")
        add("=" * 62)
        return "\n".join(lines)

    # -- persistence ----------------------------------------------------------

    def save(self, path: str | Path = "dome_design.json") -> Path:
        path = Path(path)
        path.write_text(
            json.dumps(self.config.to_dict(), indent=2), encoding="utf-8"
        )
        return path

    def load(self, path: str | Path = "dome_design.json") -> bool:
        path = Path(path)
        if not path.exists():
            return False
        self.config = DomeConfig.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.rebuild()
        return True
```

==========================================================================
======== FILE: mesh_builder.py ========
==========================================================================

```python
"""
Mesh assembly for the dome creator.

Vertex layout (11 floats): position(3) normal(3) rgba(4) mat_id(1).
Opaque and transparent triangles are kept in separate index lists so the
renderer can draw glass / sheeting in a blended second pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from dome_model import DomeModel, normalize
import materials
from materials import (
    MAT_GRASS,
    MAT_PLAIN,
)
import workshop

VERTEX_FLOATS = 11


@dataclass
class Mesh:
    vertices: np.ndarray          # (N, 11) float32
    opaque: np.ndarray            # uint32 index array
    transparent: np.ndarray      # uint32 index array


class MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[list[float]] = []
        self.opaque: list[int] = []
        self.transparent: list[int] = []

    # -- low level -------------------------------------------------------

    def _indices(self, alpha: float) -> list[int]:
        return self.transparent if alpha < 0.999 else self.opaque

    def add_vertex(
        self,
        p,
        n,
        color: tuple[float, float, float],
        alpha: float,
        mat_id: int,
    ) -> int:
        self.vertices.append([
            float(p[0]), float(p[1]), float(p[2]),
            float(n[0]), float(n[1]), float(n[2]),
            color[0], color[1], color[2], alpha,
            float(mat_id),
        ])
        return len(self.vertices) - 1

    def triangle(self, p0, p1, p2, color, alpha=1.0, mat_id=MAT_PLAIN,
                 normal=None) -> None:
        p0 = np.asarray(p0, dtype=np.float64)
        p1 = np.asarray(p1, dtype=np.float64)
        p2 = np.asarray(p2, dtype=np.float64)
        if normal is None:
            normal = normalize(np.cross(p1 - p0, p2 - p0))
        base = self.add_vertex(p0, normal, color, alpha, mat_id)
        self.add_vertex(p1, normal, color, alpha, mat_id)
        self.add_vertex(p2, normal, color, alpha, mat_id)
        self._indices(alpha).extend([base, base + 1, base + 2])

    def quad(self, p0, p1, p2, p3, normal, color, alpha=1.0,
             mat_id=MAT_PLAIN) -> None:
        base = self.add_vertex(p0, normal, color, alpha, mat_id)
        self.add_vertex(p1, normal, color, alpha, mat_id)
        self.add_vertex(p2, normal, color, alpha, mat_id)
        self.add_vertex(p3, normal, color, alpha, mat_id)
        self._indices(alpha).extend([
            base, base + 1, base + 2, base, base + 2, base + 3,
        ])

    # -- primitives ------------------------------------------------------

    def prism(
        self,
        start,
        end,
        profile: list[tuple[float, float]],
        u_axis,
        v_axis,
        color,
        alpha=1.0,
        mat_id=MAT_PLAIN,
        cap_ends=True,
        smooth=False,
    ) -> None:
        """Sweep a 2D CCW profile from start to end.

        u_axis / v_axis are the world-space directions of the profile's
        local x / y axes (both perpendicular to the sweep axis).
        """
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        axis = end - start
        length = float(np.linalg.norm(axis))
        if length < 1e-7:
            return
        axis_dir = axis / length
        u_axis = np.asarray(u_axis, dtype=np.float64)
        v_axis = np.asarray(v_axis, dtype=np.float64)

        n = len(profile)
        ring0 = [start + u_axis * u + v_axis * v for u, v in profile]
        ring1 = [end + u_axis * u + v_axis * v for u, v in profile]

        for i in range(n):
            j = (i + 1) % n
            if smooth:
                n0 = normalize(u_axis * profile[i][0] + v_axis * profile[i][1])
                n1 = normalize(u_axis * profile[j][0] + v_axis * profile[j][1])
            else:
                du = profile[j][0] - profile[i][0]
                dv = profile[j][1] - profile[i][1]
                flat = normalize(u_axis * dv - v_axis * du)
                n0 = n1 = flat
            base = self.add_vertex(ring0[i], n0, color, alpha, mat_id)
            self.add_vertex(ring0[j], n1, color, alpha, mat_id)
            self.add_vertex(ring1[j], n1, color, alpha, mat_id)
            self.add_vertex(ring1[i], n0, color, alpha, mat_id)
            self._indices(alpha).extend([
                base, base + 1, base + 2, base, base + 2, base + 3,
            ])

        if not cap_ends:
            return
        for center, ring, cap_normal in (
            (start, ring0, -axis_dir),
            (end, ring1, axis_dir),
        ):
            c = self.add_vertex(center, cap_normal, color, alpha, mat_id)
            first = len(self.vertices)
            for p in ring:
                self.add_vertex(p, cap_normal, color, alpha, mat_id)
            for i in range(n):
                j = (i + 1) % n
                self._indices(alpha).extend([c, first + i, first + j])

    def cylinder(self, start, end, radius, sides, color, alpha=1.0,
                 mat_id=MAT_PLAIN, cap_ends=True) -> None:
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        axis_dir = normalize(end - start)
        helper = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(axis_dir, helper))) > 0.92:
            helper = np.array([0.0, 1.0, 0.0])
        u_axis = normalize(np.cross(axis_dir, helper))
        v_axis = normalize(np.cross(axis_dir, u_axis))
        profile = [
            (radius * math.cos(2 * math.pi * i / sides),
             radius * math.sin(2 * math.pi * i / sides))
            for i in range(sides)
        ]
        self.prism(start, end, profile, u_axis, v_axis, color, alpha,
                   mat_id, cap_ends, smooth=sides >= 8)

    def disc(self, center, radius, sides, color, alpha=1.0,
             mat_id=MAT_PLAIN, z_normal=1.0) -> None:
        center = np.asarray(center, dtype=np.float64)
        normal = np.array([0.0, 0.0, float(np.sign(z_normal))])
        c = self.add_vertex(center, normal, color, alpha, mat_id)
        first = len(self.vertices)
        for i in range(sides):
            a = 2 * math.pi * i / sides
            p = center + np.array([radius * math.cos(a),
                                   radius * math.sin(a), 0.0])
            self.add_vertex(p, normal, color, alpha, mat_id)
        for i in range(sides):
            j = (i + 1) % sides
            if z_normal >= 0:
                self._indices(alpha).extend([c, first + i, first + j])
            else:
                self._indices(alpha).extend([c, first + j, first + i])

    # -- output ----------------------------------------------------------

    def build(self) -> Mesh:
        vertices = (
            np.asarray(self.vertices, dtype=np.float32)
            if self.vertices else np.zeros((0, VERTEX_FLOATS), np.float32)
        )
        return Mesh(
            vertices=vertices,
            opaque=np.asarray(self.opaque, dtype=np.uint32),
            transparent=np.asarray(self.transparent, dtype=np.uint32),
        )


# ---------------------------------------------------------------------------
# Scene assembly
# ---------------------------------------------------------------------------

def build_environment() -> Mesh:
    """Static ground plane and reference grid (built once)."""
    b = MeshBuilder()

    b.disc((0.0, 0.0, -0.02), 220.0, 64, (0.30, 0.36, 0.26),
           mat_id=MAT_GRASS)

    extent = 60.0
    spacing = 3.0
    count = int(extent / spacing)
    for i in range(-count, count + 1):
        coord = i * spacing
        major = i % 5 == 0
        color = (0.40, 0.45, 0.36) if major else (0.34, 0.39, 0.31)
        radius = 0.035 if major else 0.02
        b.cylinder((-extent, coord, 0.0), (extent, coord, 0.0),
                   radius, 5, color, cap_ends=False)
        b.cylinder((coord, -extent, 0.0), (coord, extent, 0.0),
                   radius, 5, color, cap_ends=False)

    return b.build()


def console_placement(model: DomeModel) -> dict:
    """The monitoring system: apex PTZ camera plus a wall-mounted
    monitor hung high on the north wall, above the doorway, angled
    down toward the middle of the floor."""
    cfg = model.config
    r = cfg.radius
    fh = model.foundation.height
    up = np.array([0.0, 0.0, 1.0])
    cz = float(model.sphere_center[2])
    apex_z = cz + r

    ox, oy = float(model.origin[0]), float(model.origin[1])
    zs = min(fh + 2.75, apex_z - 0.7)
    zs = max(zs, fh + 1.55)
    horiz = math.sqrt(max(r * r - (zs - cz) ** 2, 0.09))
    d = max(horiz - 0.34, 0.8)
    screen_center = np.array([ox, oy + d, zs])

    # Angle the screen down toward the center of the floor.
    target = np.array([ox, oy, fh + 1.0])
    n_t = normalize(target - screen_center)
    right = normalize(np.cross(up, n_t))
    up_s = normalize(np.cross(n_t, right))

    hw, hh = 0.60, 0.34                        # generous 16:9 monitor
    front = screen_center + n_t * 0.02
    corners = np.array([
        front - right * hw - up_s * hh,        # bottom-left
        front + right * hw - up_s * hh,        # bottom-right
        front + right * hw + up_s * hh,        # top-right
        front - right * hw + up_s * hh,        # top-left
    ])

    door_h = min(2.05, zs - fh - 0.55)
    door_y = math.sqrt(
        max(r * r - (fh + door_h - cz) ** 2, 0.05)) - 0.18

    return {
        "screen_center": screen_center,
        "screen_corners": corners,
        "right": right,
        "up_s": up_s,
        "normal": n_t,
        "half_w": hw,
        "half_h": hh,
        "ptz_eye": np.array([ox, oy, apex_z - 0.62]),
        "apex_z": apex_z,
        "door_y": door_y,
        "door_h": door_h,
        "origin": (ox, oy),
    }


def build_dome_mesh(model: DomeModel, events: list | None = None,
                    include_console: bool = True) -> Mesh:
    """Full dome assembly, emitted in real construction order (inspired
    by trailer-home manufacturing: site → chassis/foundation → frame →
    sheathing → rough MEP → interior fit-out → commissioning).

    When `events` is given, a checkpoint is appended after each work
    step: {label, hours (real-world estimate), opaque/transparent index
    counts, pos (worker station)}. Rendering only up to a checkpoint's
    counts shows the dome partially built.
    """
    b = MeshBuilder()
    cfg = model.config
    shape = model.shape
    frame_color = model.frame_color_rgb()
    hub_color = tuple(c * 0.45 for c in frame_color)
    tint = model.panel_tint()
    center = model.sphere_center
    radius = cfg.radius
    width = cfg.strut_width
    depth = model.strut_depth
    fh = model.foundation.height
    ox, oy = float(model.origin[0]), float(model.origin[1])
    up_axis = np.array([0.0, 0.0, 1.0])
    east = np.array([1.0, 0.0, 0.0])
    north = np.array([0.0, 1.0, 0.0])

    def mark(label: str, hours: float, pos) -> None:
        if events is not None:
            events.append({
                "label": label,
                "hours": max(hours, 0.02),
                "opaque": len(b.opaque),
                "transparent": len(b.transparent),
                "pos": (float(pos[0]), float(pos[1]), float(pos[2])),
            })

    def floor_pos(p) -> tuple:
        """Worker station: below/near a point, pulled toward center."""
        v = np.array([float(p[0]) - ox, float(p[1]) - oy])
        d = float(np.linalg.norm(v))
        if d > 1e-6:
            v = v / d * max(d - 1.0, 0.5)
        return (ox + v[0], oy + v[1], fh)

    # ---- 1. site prep and foundation (the "chassis") ----
    foundation = model.foundation
    f_area = math.pi * (radius * cfg.foundation_scale) ** 2
    if foundation.name != "Bare Ground":
        f_radius = radius * cfg.foundation_scale
        h = foundation.height
        b.disc((ox, oy, h), f_radius, 48, foundation.top_color,
               mat_id=foundation.mat_id)
        if h > 0.015:
            b.cylinder((ox, oy, 0.0), (ox, oy, h), f_radius, 48,
                       foundation.side_color, mat_id=MAT_PLAIN,
                       cap_ends=False)
        mark(f"Site prep & {foundation.name.lower()}",
             max(6.0, f_area * 0.12), (ox, oy + radius * 0.5, fh))

    # ---- 2. floor layout markings ----
    workshop.build_sections(b, model)
    mark("Floor layout & section markings", 1.5, (ox, oy, fh))

    # ---- 3. frame: struts from the base ring upward ----
    profile = shape.profile(width, flip=getattr(cfg, "wedge_flip", False))
    smooth = shape.kind == "circle"
    hubless = cfg.frame_style == "Hubless Doubled"
    strut_hours = 0.08 if hubless else 0.12
    if shape.kind == "wedge":
        strut_hours += 0.04           # sizing split logs takes longer
    ordered_struts = sorted(
        model.struts, key=lambda s: float((s[0][2] + s[1][2]) * 0.5))
    n_struts = len(ordered_struts)
    for i, (p0, p1, _length) in enumerate(ordered_struts):
        mid = (p0 + p1) * 0.5
        radial = normalize(mid - center)
        axis_dir = normalize(p1 - p0)
        u_axis = normalize(np.cross(axis_dir, radial))
        if np.linalg.norm(u_axis) < 1e-6:
            u_axis = np.array([1.0, 0.0, 0.0])
        v_axis = normalize(np.cross(u_axis, axis_dir))
        if float(np.dot(v_axis, radial)) < 0.0:
            v_axis = -v_axis
        b.prism(p0, p1, profile, u_axis, v_axis, frame_color,
                mat_id=MAT_PLAIN, cap_ends=True, smooth=smooth)
        mark(f"Install strut {i + 1}/{n_struts}", strut_hours,
             floor_pos(mid))

    # ---- 4. joins: hubs / bracket plates / hubless edge bolts ----
    bracket_steel = (0.62, 0.65, 0.69)
    hub_list = sorted(model.hubs, key=lambda hb: float(hb[0][2]))
    hub_hours = 0.20 if cfg.hub_style == "Metal Brackets" else 0.15
    for hi, (p, directions) in enumerate(hub_list):
        radial = normalize(p - center)
        if cfg.hub_style == "Metal Brackets":
            plate_len = width * 3.4
            plate_w = width * 0.95
            b.cylinder(p + radial * depth * 0.40,
                       p + radial * depth * 0.58,
                       max(width * 0.7, 0.025), 8, bracket_steel,
                       cap_ends=True)
            for direction in directions:
                along = normalize(
                    direction - radial * float(np.dot(direction, radial)))
                side = normalize(np.cross(radial, along))
                start = p + radial * depth * 0.52
                b.prism(start, start + along * plate_len,
                        [(-plate_w * 0.5, -0.006), (plate_w * 0.5, -0.006),
                         (plate_w * 0.5, 0.006), (-plate_w * 0.5, 0.006)],
                        side, radial, bracket_steel, cap_ends=True)
        else:
            b.cylinder(p - radial * depth * 0.52,
                       p + radial * depth * 0.58,
                       max(width * 0.95, 0.03), 8, hub_color,
                       cap_ends=True)
        mark(f"Fasten hub {hi + 1}/{len(hub_list)}", hub_hours,
             floor_pos(p))

    if model.bolt_points:
        bolt_color = (0.20, 0.22, 0.25)
        for p in model.bolt_points:
            radial = normalize(p - center)
            b.cylinder(p - radial * depth * 0.9, p + radial * depth * 0.9,
                       0.013, 6, bolt_color, cap_ends=True)
        mark(f"Through-bolt {len(model.bolt_points)} edge joins",
             len(model.bolt_points) * 0.03, (ox, oy, fh))

    # ---- 5. doorway framing ----
    place = console_placement(model)
    door_y = place["door_y"]
    door_h = place["door_h"]
    wood = (0.42, 0.28, 0.16)
    for sx in (-0.55, 0.55):
        b.prism(np.array([ox + sx, oy + door_y, fh]),
                np.array([ox + sx, oy + door_y, fh + door_h]),
                [(-0.06, -0.05), (0.06, -0.05), (0.06, 0.05), (-0.06, 0.05)],
                east, north, wood, cap_ends=True)
    b.prism(np.array([ox - 0.64, oy + door_y, fh + door_h + 0.06]),
            np.array([ox + 0.64, oy + door_y, fh + door_h + 0.06]),
            [(-0.05, -0.08), (0.05, -0.08), (0.05, 0.08), (-0.05, 0.08)],
            north, up_axis, wood, cap_ends=True)
    mark("Frame the entrance", 2.0, (ox, oy + door_y - 1.0, fh))

    # ---- 6. sheathing: panels bottom-up ----
    recess = depth * min(max(cfg.recess_pct, 0.05), 0.95)
    pull = width * 0.62
    fitted = [p for p in model.panels if p.panel_type.name != "Open"]
    fitted.sort(key=lambda p: float(p.centroid[2]))
    for pi, panel in enumerate(fitted):
        ptype = panel.panel_type
        outward = normalize(panel.centroid - center)
        pts = []
        for v in panel.world_verts:
            to_c = panel.centroid - v
            dist = float(np.linalg.norm(to_c))
            q = v + to_c * (min(pull, dist * 0.45) / max(dist, 1e-9))
            pts.append(q - outward * recess)
        if ptype.colorable:
            color = tuple(
                min(1.0, ptype.color[i] * tint[i]) for i in range(3))
        else:
            color = ptype.color
        b.triangle(pts[0], pts[1], pts[2], color, ptype.alpha,
                   ptype.mat_id, normal=outward)

        # Custom panels show their bracket hardware along the edges.
        hours = 0.7 if ptype.is_window else 0.4
        definition = materials.CUSTOM_PANEL_DEFS.get(ptype.name)
        if definition:
            _c, _w, _s, minutes = materials.custom_panel_extras(definition)
            hours += minutes / 60.0
            brackets = sum(
                qty for comp, qty in
                definition.get("components", {}).items()
                if "Bracket" in comp or "Gusset" in comp)
            for k in range(min(int(brackets), 6)):
                e = k % 3
                m0 = np.asarray(pts[e])
                m1 = np.asarray(pts[(e + 1) % 3])
                frac = 0.5 if k < 3 else 0.3
                mp = m0 + (m1 - m0) * frac
                edge_dir = normalize(m1 - m0)
                b.prism(mp - edge_dir * 0.07 + outward * 0.008,
                        mp + edge_dir * 0.07 + outward * 0.008,
                        [(-0.025, -0.008), (0.025, -0.008),
                         (0.0, 0.018)],
                        normalize(np.cross(outward, edge_dir)), outward,
                        (0.55, 0.58, 0.62), cap_ends=True)
        mark(f"Fit {ptype.name.lower()} {pi + 1}/{len(fitted)}", hours,
             floor_pos(panel.centroid))

    # ---- 7. cladding layers ----
    covered = model.layer_covered_panels()
    covered_area = sum(p.area for p in covered)
    offset = depth * 0.55 + 0.01
    for layer in model.active_layers:
        offset += layer.thickness * 0.5
        for panel in covered:
            pts = []
            for v in panel.world_verts:
                rel = v - center
                dist = float(np.linalg.norm(rel))
                pts.append(center + rel * ((dist + offset) / dist))
            outward = normalize(panel.centroid - center)
            b.triangle(pts[0], pts[1], pts[2], layer.color, layer.alpha,
                       layer.mat_id, normal=outward)
        offset += layer.thickness * 0.5 + 0.008
        mark(f"Apply {layer.name.lower()} layer",
             max(1.0, covered_area * 0.05), (ox, oy - radius - 1.0, 0.0))

    # ---- 8. rough electrical: conduit runs to outlets ----
    wire_runs = workshop.wiring_runs(model)
    for run in wire_runs:
        sx, sy = run["from"]
        tx, ty = run["to"]
        start = np.array([ox + sx, oy + sy, fh + 0.025])
        end = np.array([ox + tx, oy + ty, fh + 0.025])
        if float(np.linalg.norm(end - start)) > 0.05:
            direction = normalize(end - start)
            perp = normalize(np.cross(up_axis, direction))
            b.prism(start, end,
                    [(-0.016, -0.016), (0.016, -0.016),
                     (0.016, 0.016), (-0.016, 0.016)],
                    perp, up_axis, (0.25, 0.26, 0.29), cap_ends=True)
        mark(f"Wire {run['target'].lower()} "
             f"({run['length']:.0f} m run)",
             0.5 + run["length"] * 0.05,
             (ox + tx, oy + ty - 0.8, fh))

    # ---- 9. rough plumbing: supply + drain to each fixture ----
    pipe_runs = workshop.plumbing_runs(model)
    for run in pipe_runs:
        sx, sy = run["from"]
        tx, ty = run["to"]
        direction = normalize(np.array([tx - sx, ty - sy, 0.0]))
        perp = normalize(np.cross(up_axis, direction))
        for side, color in ((-0.06, (0.75, 0.20, 0.18)),   # hot PEX
                            (0.0, (0.20, 0.35, 0.75)),      # cold PEX
                            (0.06, (0.45, 0.46, 0.48))):    # drain
            start = np.array([ox + sx, oy + sy, fh + 0.015]) + perp * side
            end = np.array([ox + tx, oy + ty, fh + 0.015]) + perp * side
            b.prism(start, end,
                    [(-0.012, -0.012), (0.012, -0.012),
                     (0.012, 0.012), (-0.012, 0.012)],
                    perp, up_axis, color, cap_ends=True)
        mark(f"Plumb {run['fixture'].lower()} "
             f"({run['length']:.0f} m runs)",
             2.0 + run["length"] * 0.1, (ox + tx, oy + ty - 0.8, fh))

    # ---- 10. interior partitions ----
    seg_count_before = len(b.opaque)
    workshop.build_partitions(b, model)
    segs = workshop.partition_segments(model)
    if segs and len(b.opaque) > seg_count_before:
        mark(f"Frame {len(segs)} partition walls", len(segs) * 1.5,
             (ox, oy, fh))

    # ---- 11. equipment & furnishing ----
    prop_hours = {"battery": 1.5, "controller": 2.0, "meter": 0.75,
                  "outlet": 0.5}
    for entry in model.config.props:
        prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
        if prop is None:
            continue
        workshop.build_prop(b, model, entry)
        hours = prop_hours.get(prop.role, 0.3)
        mark(f"Install {prop.name.lower()}", hours,
             (ox + float(entry["x"]), oy + float(entry["y"]) - 0.9, fh))

    # ---- 12. monitoring system: monitor, computer, PTZ camera ----
    if include_console:
        bezel_color = (0.09, 0.09, 0.10)
        sc = place["screen_center"]
        hw, hh = place["half_w"], place["half_h"]
        n_t, right_s, up_s = (place["normal"], place["right"],
                              place["up_s"])
        b.prism(sc - n_t * 0.36, sc - n_t * 0.02,
                [(-0.05, -0.05), (0.05, -0.05), (0.05, 0.05),
                 (-0.05, 0.05)],
                right_s, up_s, (0.30, 0.31, 0.34), cap_ends=True)
        b.prism(sc - n_t * 0.07, sc + n_t * 0.012,
                [(-hw - 0.05, -hh - 0.05), (hw + 0.05, -hh - 0.05),
                 (hw + 0.05, hh + 0.05), (-hw - 0.05, hh + 0.05)],
                right_s, up_s, bezel_color, cap_ends=True)
        cb = sc - up_s * (hh + 0.17)
        b.prism(cb - n_t * 0.10, cb + n_t * 0.02,
                [(-0.28, -0.09), (0.28, -0.09), (0.28, 0.09),
                 (-0.28, 0.09)],
                right_s, up_s, (0.16, 0.17, 0.19), cap_ends=True)
        b.prism(cb + n_t * 0.02, cb + n_t * 0.028,
                [(0.16, -0.03), (0.22, -0.03), (0.22, 0.03),
                 (0.16, 0.03)],
                right_s, up_s, (0.3, 0.9, 0.4), mat_id=12, cap_ends=True)

        apex = np.array([ox, oy, place["apex_z"]])
        b.cylinder(apex - up_axis * 0.02, apex - up_axis * 0.30, 0.035, 8,
                   (0.30, 0.31, 0.33), cap_ends=True)
        b.cylinder(apex - up_axis * 0.30, apex - up_axis * 0.48, 0.095,
                   10, (0.10, 0.10, 0.11), cap_ends=True)
        b.cylinder(apex - up_axis * 0.48, apex - up_axis * 0.53, 0.045,
                   10, (0.05, 0.08, 0.14), cap_ends=True)
        mark("Install monitoring system", 1.5,
             (ox, oy + door_y - 1.2, fh))

    # ---- 13. commissioning (no geometry, pure labor) ----
    mark("Test, inspect & commission", 2.0, (ox, oy, fh))

    return b.build()


def build_avatar_mesh() -> Mesh:
    """Simple third-person player figure, built at the origin facing +Y."""
    b = MeshBuilder()
    body = (0.22, 0.32, 0.52)
    skin = (0.85, 0.68, 0.52)
    b.cylinder((0, 0, 0.05), (0, 0, 0.95), 0.17, 10, body, cap_ends=True)
    b.cylinder((0, 0, 0.95), (0, 0, 1.38), 0.14, 10,
               (0.28, 0.38, 0.58), cap_ends=True)
    b.cylinder((0, 0, 1.40), (0, 0, 1.66), 0.11, 10, skin, cap_ends=True)
    # Nose marker so the facing direction reads clearly.
    b.cylinder((0, 0.10, 1.52), (0, 0.16, 1.52), 0.025, 6, skin,
               cap_ends=True)
    return b.build()


def build_worker_mesh() -> Mesh:
    """Construction worker: safety vest and hard hat."""
    b = MeshBuilder()
    b.cylinder((0, 0, 0.05), (0, 0, 0.95), 0.17, 10,
               (0.30, 0.30, 0.34), cap_ends=True)          # work pants
    b.cylinder((0, 0, 0.95), (0, 0, 1.38), 0.15, 10,
               (0.95, 0.45, 0.08), cap_ends=True)          # hi-vis vest
    b.cylinder((0, 0, 1.40), (0, 0, 1.62), 0.11, 10,
               (0.85, 0.68, 0.52), cap_ends=True)
    b.cylinder((0, 0, 1.62), (0, 0, 1.72), 0.13, 10,
               (0.95, 0.85, 0.10), cap_ends=True)          # hard hat
    return b.build()


def build_prop_mesh(name: str) -> Mesh:
    """A single prop at the origin (for the placement ghost preview)."""
    b = MeshBuilder()
    prop = workshop.PROP_TYPE_BY_NAME[name]
    prop.build(b, workshop.Transform(0.0, 0.0, 0.0, 0.0))
    return b.build()
```

==========================================================================
======== FILE: electrical.py ========
==========================================================================

```python
"""
Live electrical system simulation across all domes on the site.

One shared battery bank + charge controller serves every dome (the tie
that links dome 1 and dome 2). Solar comes from Solar Panel shell
panels on any dome; loads come from powered-on devices plugged into
outlets. Battery dynamics run at an accelerated time factor so charge
and drain are visible while you play.
"""

from __future__ import annotations

import math

import workshop

BATTERY_KWH_EACH = 10.0
SUN_FACTOR = 0.75              # average irradiance vs nameplate
OUTLET_REACH = 3.0             # cord length from an outlet, meters
TIME_FACTOR = 600.0            # 1 real second = 10 simulated minutes


class ElectricalSystem:
    def __init__(self) -> None:
        self.charge_kwh = 6.0
        self.capacity_kwh = 0.0
        self.solar_watts = 0.0
        self.solar_by_dome: list[float] = []
        self.load_by_dome: list[float] = []
        self.lights_by_dome: list[int] = []
        self.has_system = False
        self.battery_empty = False

    @staticmethod
    def _outlet_positions(model) -> list[tuple[float, float]]:
        out = []
        for entry in model.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is not None and prop.role in ("outlet", "battery",
                                                  "controller"):
                out.append((float(entry["x"]), float(entry["y"])))
        return out

    @classmethod
    def device_connected(cls, model, entry, has_system: bool) -> bool:
        """A device is powered if plugged into an outlet in reach —
        or freely, when no battery system exists anywhere (standalone
        generator / extension-cord mode)."""
        if not has_system:
            return True
        ex, ey = float(entry["x"]), float(entry["y"])
        for px, py in cls._outlet_positions(model):
            if math.hypot(ex - px, ey - py) <= OUTLET_REACH:
                return True
        return False

    def update(self, models: list, dt: float) -> None:
        banks = 0
        for model in models:
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is not None and prop.role == "battery":
                    banks += 1
        self.has_system = banks > 0
        self.capacity_kwh = banks * BATTERY_KWH_EACH

        self.solar_by_dome = []
        self.load_by_dome = []
        self.lights_by_dome = []
        for model in models:
            solar = sum(
                p.area * p.panel_type.watts_per_m2 for p in model.panels
            ) * SUN_FACTOR
            self.solar_by_dome.append(solar)

            load = 0.0
            lights = 0
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None or prop.watts <= 0:
                    continue
                if not entry.get("on", True):
                    continue
                if not self.device_connected(model, entry,
                                             self.has_system):
                    continue
                load += prop.watts
                if prop.light_z is not None:
                    lights += 1
            self.load_by_dome.append(load)
            self.lights_by_dome.append(lights)

        self.solar_watts = sum(self.solar_by_dome)

        if self.has_system:
            usable_load = 0.0 if self.battery_empty else \
                sum(self.load_by_dome)
            net_watts = self.solar_watts - usable_load
            self.charge_kwh += net_watts / 1000.0 * \
                (dt * TIME_FACTOR / 3600.0)
            self.charge_kwh = min(max(self.charge_kwh, 0.0),
                                  self.capacity_kwh)
            self.battery_empty = self.charge_kwh <= 1e-6 and \
                self.solar_watts < sum(self.load_by_dome)
        else:
            self.battery_empty = False

    @property
    def net_watts(self) -> float:
        load = 0.0 if self.battery_empty else sum(self.load_by_dome)
        return self.solar_watts - load

    def charge_fraction(self) -> float:
        if self.capacity_kwh <= 0:
            return 0.0
        return self.charge_kwh / self.capacity_kwh

    def lamps_powered(self, model, entry) -> bool:
        """Should this lamp actually emit light right now?"""
        if not entry.get("on", True):
            return False
        if not self.has_system:
            return True
        if self.battery_empty:
            return False
        return self.device_connected(model, entry, True)
```

==========================================================================
======== FILE: vision.py ========
==========================================================================

```python
"""
Per-dome vision system.

Every dome's apex PTZ camera runs simulated object detection: anything
inside the camera's current field of view (props, the player) counts as
a detection sample. Samples accumulate into a quantitative model over
time — exponential moving averages of objects in view, occupancy, and
per-type detection frequencies — the groundwork for likely-scenario
narrowing per room.
"""

from __future__ import annotations

import math

import numpy as np

import workshop

SAMPLE_PERIOD = 0.5      # seconds between detection samples
DETECT_RANGE = 40.0
EMA_ALPHA = 0.06


class VisionTracker:
    def __init__(self) -> None:
        self.timer = 0.0
        self.samples = 0
        self.ema_objects = 0.0
        self.ema_occupancy = 0.0
        self.type_counts: dict[str, int] = {}
        self.current: list[str] = []
        self.person_now = False

    def update(self, model, ptz, console, player_pos, dt: float) -> None:
        self.timer += dt
        if self.timer < SAMPLE_PERIOD or not console:
            return
        self.timer = 0.0
        self.samples += 1

        eye = np.asarray(console["ptz_eye"], dtype=np.float64)
        forward, _ = ptz.basis()
        forward = np.asarray(forward, dtype=np.float64)
        half_fov = math.radians(ptz.fov) * 0.55   # slight margin

        def in_view(point) -> bool:
            vec = np.asarray(point, dtype=np.float64) - eye
            dist = float(np.linalg.norm(vec))
            if dist < 0.3 or dist > DETECT_RANGE:
                return False
            cos_angle = float(np.dot(vec / dist, forward))
            return cos_angle > math.cos(half_fov)

        fh = model.foundation.height
        ox, oy = float(model.origin[0]), float(model.origin[1])
        seen: list[str] = []
        for entry in model.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is None:
                continue
            center = (ox + float(entry["x"]), oy + float(entry["y"]),
                      fh + prop.pick_height * 0.5)
            if in_view(center):
                seen.append(entry["type"])
                self.type_counts[entry["type"]] = \
                    self.type_counts.get(entry["type"], 0) + 1

        # Player counts as a person detection when on this dome's floor.
        px, py = float(player_pos[0]) - ox, float(player_pos[1]) - oy
        person = 0.0
        self.person_now = False
        if math.hypot(px, py) <= model.floor_radius:
            if in_view((float(player_pos[0]), float(player_pos[1]),
                        fh + 0.9)):
                person = 1.0
                self.person_now = True
                seen.append("Person")
                self.type_counts["Person"] = \
                    self.type_counts.get("Person", 0) + 1

        self.current = seen
        self.ema_objects += EMA_ALPHA * (len(seen) - self.ema_objects)
        self.ema_occupancy += EMA_ALPHA * (person - self.ema_occupancy)

    def detect_text(self) -> str:
        if not self.current:
            return (f"DETECT 0 obj · avg {self.ema_objects:.1f} · "
                    f"occ {self.ema_occupancy * 100:.0f}%")
        shown = ", ".join(sorted(set(self.current))[:3])
        more = len(set(self.current)) - 3
        if more > 0:
            shown += f" +{more}"
        return (f"DETECT {len(self.current)}: {shown} · "
                f"avg {self.ema_objects:.1f} · "
                f"occ {self.ema_occupancy * 100:.0f}%")

    def summary(self) -> str:
        top = sorted(self.type_counts.items(), key=lambda kv: -kv[1])[:2]
        names = "/".join(name for name, _count in top) if top else "—"
        return (f"avg {self.ema_objects:.1f} obj · "
                f"occ {self.ema_occupancy * 100:.0f}% · top {names}")
```

==========================================================================
======== FILE: overlay_ui.py ========
==========================================================================

```python
"""
2D overlay widgets for the dome creator, rendered with pygame fonts into
RGBA surfaces. The main app uploads these surfaces as GL textures and
composites them over the 3D view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

BG = (14, 18, 22, 215)
BG_SOFT = (14, 18, 22, 170)
HEADER = (120, 200, 255)
TEXT = (225, 230, 235)
DIM = (150, 158, 165)
VALUE = (255, 220, 130)
SELECT_BG = (40, 80, 110, 235)
ACCENT = (255, 170, 60)
GOOD = (140, 230, 150)


@dataclass
class MenuItem:
    label: str
    kind: str                               # "header", "choice", "action"
    value: Callable[[], str] | None = None  # current value as display text
    change: Callable[[int], None] | None = None  # left/right delta
    activate: Callable[[], str | None] | None = None  # enter; returns message
    hint: str = ""


class Fonts:
    def __init__(self) -> None:
        pygame.font.init()
        self.body = pygame.font.SysFont("consolas,couriernew,monospace", 15)
        self.small = pygame.font.SysFont("consolas,couriernew,monospace", 13)
        self.title = pygame.font.SysFont(
            "consolas,couriernew,monospace", 17, bold=True
        )


def render_menu(
    fonts: Fonts,
    items: list[MenuItem],
    selected: int,
    pages: list[str] | None = None,
    active_page: int = 0,
) -> tuple[pygame.Surface, dict]:
    """Returns (surface, hit_map). hit_map: {"tabs": [(page, Rect)],
    "rows": [(item_index, Rect, arrows_bool)]} in panel-local coords."""
    width = 380
    row_h = 22
    header_h = 30
    tabs_h = 22 if pages else 0
    pad = 10
    height = pad * 2 + header_h + tabs_h + row_h * len(items) + 24
    hit_map: dict = {"tabs": [], "rows": []}

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    surf.blit(
        fonts.title.render("DOME CREATOR", True, HEADER), (pad, pad)
    )
    y = pad + header_h

    if pages:
        x = pad
        for i, name in enumerate(pages):
            label = f"{name}"
            color = ACCENT if i == active_page else DIM
            rendered = fonts.body.render(label, True, color)
            tab_rect = pygame.Rect(x - 3, y - 2,
                                   rendered.get_width() + 6, 20)
            if i == active_page:
                pygame.draw.rect(surf, SELECT_BG, tab_rect)
            surf.blit(rendered, (x, y))
            hit_map["tabs"].append((i, tab_rect))
            x += rendered.get_width() + 14
        y += tabs_h

    for i, item in enumerate(items):
        if item.kind == "header":
            pygame.draw.line(surf, (60, 90, 110), (pad, y + row_h // 2),
                             (width - pad, y + row_h // 2), 1)
            label = fonts.small.render(f" {item.label} ", True, HEADER)
            surf.blit(label, (pad + 8, y + row_h // 2 - 8))
            y += row_h
            continue

        row_rect = pygame.Rect(pad - 4, y, width - pad * 2 + 8, row_h)
        hit_map["rows"].append((i, row_rect))
        if i == selected:
            pygame.draw.rect(surf, SELECT_BG, row_rect)
            surf.blit(fonts.body.render(">", True, ACCENT), (pad - 2, y + 2))

        surf.blit(fonts.body.render(item.label, True, TEXT), (pad + 12, y + 2))
        if item.value is not None:
            value_text = f"< {item.value()} >" if item.kind == "choice" \
                else item.value()
            rendered = fonts.body.render(value_text, True, VALUE)
            surf.blit(rendered, (width - pad - rendered.get_width() - 2, y + 2))
        elif item.kind == "action":
            rendered = fonts.body.render("[CLICK]", True, GOOD)
            surf.blit(rendered, (width - pad - rendered.get_width() - 2, y + 2))
        y += row_h

    tip = fonts.small.render(
        "Click: next / apply    Right-click: previous", True, DIM
    )
    surf.blit(tip, (pad, height - 20))
    return surf, hit_map


def render_stats(fonts: Fonts, stats: dict) -> pygame.Surface:
    lines: list[tuple[str, tuple]] = []

    def add(text: str, color=TEXT) -> None:
        lines.append((text, color))

    add("LIVE MATERIAL BREAKDOWN", HEADER)
    add(f"{stats['frequency']}V  r={stats['radius']:.1f}m  "
        f"h={stats['height']:.1f}m", DIM)
    add(f"Floor {stats['floor_area']:.1f} m2   "
        f"Shell {stats['surface_area']:.1f} m2", DIM)
    add("")
    add("FRAME", HEADER)
    add(f" Struts {stats['strut_count']} pcs  "
        f"{stats['strut_total_len']:.1f} m")
    for label, length, count in stats["strut_classes"][:6]:
        add(f"   {label}: {count:3d} x {length:.2f} m", DIM)
    add(f" Hubs {stats['hub_count']} pcs")
    add(f" {stats['frame_weight'] + stats['hub_weight']:,.0f} kg    "
        f"${stats['frame_cost'] + stats['hub_cost']:,.0f}", VALUE)
    add("")
    add("PANELS", HEADER)
    for name, g in sorted(stats["panel_groups"].items()):
        add(f" {name:<17}{g['count']:3d}  {g['area']:6.1f} m2", DIM)
    add(f" {stats['panel_weight']:,.0f} kg    "
        f"${stats['panel_cost']:,.0f}", VALUE)
    if stats["solar_watts"] > 0:
        add(f" Solar {stats['solar_watts'] / 1000.0:.2f} kW", GOOD)
    add("")
    if stats["layer_rows"]:
        add("LAYERS", HEADER)
        for name, area, weight, cost in stats["layer_rows"]:
            add(f" {name:<17}{weight:6.0f} kg  ${cost:,.0f}", DIM)
        add(f" {stats['layer_weight']:,.0f} kg    "
            f"${stats['layer_cost']:,.0f}", VALUE)
        add("")
    add("FOUNDATION", HEADER)
    add(f" {stats['foundation_name']:<16} "
        f"{stats['foundation_weight']:,.0f} kg", DIM)
    add(f" ${stats['foundation_cost']:,.0f}", VALUE)
    add("")
    if stats["prop_count"] or stats["wall_count"] \
            or stats["assigned_sections"]:
        add("WORKSHOP FIT-OUT", HEADER)
        if stats["assigned_sections"]:
            add(f" Rooms assigned  {stats['assigned_sections']}/10", DIM)
        if stats["wall_count"]:
            add(f" Partitions {stats['wall_count']} pcs "
                f"{stats['wall_weight']:,.0f} kg  "
                f"${stats['wall_cost']:,.0f}", DIM)
        for name, g in sorted(stats["prop_groups"].items()):
            add(f" {name:<17}x{g['count']}", DIM)
        if stats["prop_count"]:
            add(f" {stats['prop_weight']:,.0f} kg    "
                f"${stats['prop_cost']:,.0f}", VALUE)
        if stats["prop_watts"]:
            add(f" Power draw {stats['prop_watts']:,.0f} W", GOOD)
        add("")
    add(f"WEIGHT {stats['structure_weight']:,.0f} kg", ACCENT)
    add(f"COST   ${stats['total_cost']:,.0f}", ACCENT)

    width = 300
    row_h = 18
    pad = 10
    height = pad * 2 + row_h * len(lines)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    y = pad
    for text, color in lines:
        if text:
            surf.blit(fonts.small.render(text, True, color), (pad, y))
        y += row_h
    return surf


def render_help(
    fonts: Fonts,
    width: int,
    aim_text: str,
    flash: str,
) -> pygame.Surface:
    height = 46
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG_SOFT)

    line1 = aim_text or "Aim at a panel and click to swap it"
    color1 = VALUE if aim_text else DIM
    if flash:
        line1 = flash
        color1 = GOOD
    surf.blit(fonts.body.render(line1, True, color1), (12, 4))

    help_line = (
        "Click: walk / pick up / take helm | Shift+Click: swap panel | "
        "C camera control | Mid-drag+arrows: view | Wheel: zoom | "
        "R roof | B bag | P first-person | M menu | F5/F9/F6 file"
    )
    surf.blit(fonts.small.render(help_line, True, DIM), (12, 26))
    return surf


def render_video_osd(
    fonts: Fonts,
    size: tuple[int, int],
    pan: float,
    tilt: float,
    fov: float,
    helm: bool,
    aiming_screen: bool,
    area_label: str = "",
    area_hint: str = "",
    detect_text: str = "",
    cam_label: str = "CAM-01",
) -> pygame.Surface:
    """Frame drawn over the PTZ video window: border, readout, prompts.

    The center is transparent so the live feed shows through.
    """
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    border = ACCENT if helm else (70, 130, 170)
    pygame.draw.rect(surf, border, (0, 0, w, h), 2)

    strip = pygame.Surface((w - 4, 20), pygame.SRCALPHA)
    strip.fill((10, 14, 18, 195))
    surf.blit(strip, (2, 2))
    zoom = 80.0 / max(fov, 1.0)
    readout = (
        f"{cam_label}  PAN {pan % 360.0:05.1f}  TILT {tilt:04.1f}  "
        f"ZOOM {zoom:.1f}x"
    )
    surf.blit(fonts.small.render(readout, True, TEXT), (8, 4))
    pygame.draw.circle(surf, (230, 60, 50), (w - 40, 12), 4)
    surf.blit(fonts.small.render("LIVE", True, DIM), (w - 32, 4))

    # Contextual awareness: which section the camera is watching and
    # what the vision system should expect to see happening there.
    if area_label:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, 22))
        context = f"WATCH {area_label}"
        if area_hint:
            context += f" · {area_hint}"
        surf.blit(fonts.small.render(context[:64], True, GOOD), (8, 23))
    if detect_text:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, 40))
        surf.blit(fonts.small.render(detect_text[:70], True,
                                     (255, 220, 130)), (8, 41))

    prompt = ""
    color = DIM
    if helm:
        prompt = "HELM  ARROWS pan/tilt  PGUP/PGDN zoom  ESC release"
        color = ACCENT
    elif aiming_screen:
        prompt = "CLICK SCREEN TO TAKE HELM"
        color = GOOD
    if prompt:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, h - 20))
        surf.blit(fonts.small.render(prompt, True, color), (8, h - 19))
    return surf


def render_toolbar(
    fonts: Fonts,
    buttons: list[tuple[str, str, bool]],   # (id, label, active)
) -> tuple[pygame.Surface, list[tuple[str, pygame.Rect]]]:
    """Clickable button strip. Returns the surface plus per-button rects
    (relative to the surface origin) for hit testing."""
    pad = 6
    btn_h = 30
    widths = []
    for _, label, _ in buttons:
        widths.append(fonts.body.size(label)[0] + 18)
    width = pad * 2 + sum(widths) + 6 * (len(buttons) - 1)
    height = btn_h + pad * 2

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    rects: list[tuple[str, pygame.Rect]] = []
    x = pad
    for (bid, label, active), w in zip(buttons, widths):
        rect = pygame.Rect(x, pad, w, btn_h)
        if active:
            pygame.draw.rect(surf, SELECT_BG, rect, border_radius=4)
            pygame.draw.rect(surf, ACCENT, rect, 1, border_radius=4)
        else:
            pygame.draw.rect(surf, (35, 45, 55, 235), rect,
                             border_radius=4)
            pygame.draw.rect(surf, (80, 100, 120), rect, 1,
                             border_radius=4)
        text = fonts.body.render(label, True,
                                 ACCENT if active else TEXT)
        surf.blit(text, (x + (w - text.get_width()) // 2,
                         pad + (btn_h - text.get_height()) // 2))
        rects.append((bid, rect))
        x += w + 6
    return surf, rects


def _item_abbrev(name: str) -> str:
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0] + words[-1][-1]).upper()
    return name[:3].upper()


def _item_color(name: str) -> tuple[int, int, int]:
    h = sum(ord(c) * (i + 7) for i, c in enumerate(name))
    return (70 + (h * 37) % 140, 70 + (h * 61) % 140, 70 + (h * 89) % 140)


def render_inventory(
    fonts: Fonts,
    items: list[str],
    selected: int | None,
) -> tuple[pygame.Surface, list[pygame.Rect]]:
    """RuneScape-style 4x7 backpack grid. Returns surface + slot rects."""
    cols, rows = 4, 7
    cell = 42
    pad = 8
    header = 24
    width = pad * 2 + cols * cell
    height = pad * 2 + header + rows * cell

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (150, 110, 60, 255), surf.get_rect(), 2)
    surf.blit(fonts.body.render(
        f"BACKPACK  {len(items)}/{cols * rows}", True, VALUE), (pad, pad))

    rects: list[pygame.Rect] = []
    for i in range(cols * rows):
        cx = pad + (i % cols) * cell
        cy = pad + header + (i // cols) * cell
        rect = pygame.Rect(cx + 2, cy + 2, cell - 4, cell - 4)
        rects.append(rect)
        pygame.draw.rect(surf, (30, 36, 42, 220), rect, border_radius=3)
        if i < len(items):
            color = _item_color(items[i])
            inner = rect.inflate(-8, -8)
            pygame.draw.rect(surf, color, inner, border_radius=3)
            abbrev = fonts.small.render(
                _item_abbrev(items[i]), True, (15, 15, 15))
            surf.blit(abbrev, (rect.centerx - abbrev.get_width() // 2,
                               rect.centery - abbrev.get_height() // 2))
        if selected == i:
            pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=3)
        else:
            pygame.draw.rect(surf, (60, 70, 80), rect, 1, border_radius=3)
    return surf, rects


def render_energy(fonts: Fonts, energy, dome_count: int) -> pygame.Surface:
    """LCD-style power system panel: battery, solar, per-dome loads."""
    width = 300
    lines = 7 + dome_count
    height = 14 + lines * 19
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((8, 14, 12, 225))
    pygame.draw.rect(surf, (60, 200, 140, 255), surf.get_rect(), 2)
    lcd = (120, 255, 180)
    dim = (70, 150, 110)

    y = 8
    surf.blit(fonts.body.render("POWER SYSTEM", True, lcd), (10, y))
    surf.blit(fonts.small.render("x600 time", True, dim), (width - 80, y + 2))
    y += 24
    if not energy.has_system:
        surf.blit(fonts.small.render(
            "No battery bank installed.", True, lcd), (10, y))
        y += 19
        surf.blit(fonts.small.render(
            "Lamps run standalone. See File >", True, dim), (10, y))
        y += 19
        surf.blit(fonts.small.render(
            "'Electrify dome' to build the system.", True, dim), (10, y))
        y += 19
    else:
        frac = energy.charge_fraction()
        bar_w = width - 20
        pygame.draw.rect(surf, (25, 45, 35), (10, y, bar_w, 14))
        color = (90, 230, 140) if frac > 0.25 else (230, 120, 60)
        pygame.draw.rect(surf, color,
                         (10, y, int(bar_w * frac), 14))
        y += 18
        surf.blit(fonts.small.render(
            f"BATTERY {frac * 100:5.1f}%   "
            f"{energy.charge_kwh:.2f}/{energy.capacity_kwh:.0f} kWh",
            True, lcd), (10, y))
        y += 19
        net = energy.net_watts
        sign = "+" if net >= 0 else ""
        surf.blit(fonts.small.render(
            f"NET {sign}{net:,.0f} W", True,
            (120, 255, 180) if net >= 0 else (255, 150, 90)), (10, y))
        y += 19
        if energy.battery_empty:
            surf.blit(fonts.small.render(
                "!! BATTERY EMPTY - LOADS SHED !!", True,
                (255, 110, 80)), (10, y))
            y += 19
    surf.blit(fonts.small.render(
        f"SOLAR IN  {energy.solar_watts:,.0f} W", True, lcd), (10, y))
    y += 19
    for i in range(dome_count):
        load = energy.load_by_dome[i] if i < len(energy.load_by_dome) else 0
        lights = (energy.lights_by_dome[i]
                  if i < len(energy.lights_by_dome) else 0)
        surf.blit(fonts.small.render(
            f"DOME {i + 1} LOAD  {load:,.0f} W  ({lights} lights on)",
            True, dim), (10, y))
        y += 19
    return surf


def render_construction(
    fonts: Fonts,
    width: int,
    dome_label: str,
    step_label: str,
    step_index: int,
    step_count: int,
    elapsed_h: float,
    total_h: float,
    speed: float,
) -> pygame.Surface:
    height = 64
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((20, 16, 8, 225))
    pygame.draw.rect(surf, (240, 180, 60, 255), surf.get_rect(), 2)

    title = (f"CONSTRUCTING {dome_label} — step {step_index}/{step_count}: "
             f"{step_label}")
    surf.blit(fonts.body.render(title[:110], True, (255, 210, 120)),
              (12, 6))
    days = total_h / 8.0
    info = (f"{elapsed_h:,.1f} / {total_h:,.0f} labor-hours "
            f"(~{days:,.0f} days @ 8 h, 1 worker)   "
            f"speed: 1 s = {speed:.2f} h   [ - / + ]")
    surf.blit(fonts.small.render(info, True, (210, 190, 150)), (12, 26))

    bar_w = width - 24
    frac = min(elapsed_h / max(total_h, 0.01), 1.0)
    pygame.draw.rect(surf, (50, 42, 25), (12, 46, bar_w, 10))
    pygame.draw.rect(surf, (240, 180, 60),
                     (12, 46, int(bar_w * frac), 10))
    return surf


def render_context_menu(
    fonts: Fonts,
    entries: list[str],
    hover: int = -1,
) -> tuple[pygame.Surface, list[pygame.Rect]]:
    """RuneScape-style 'Choose Option' popup."""
    row_h = 19
    width = max(
        [fonts.small.render(e, True, TEXT).get_width()
         for e in entries] + [110]) + 20
    height = 22 + row_h * len(entries) + 6
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((30, 26, 20, 245))
    pygame.draw.rect(surf, (10, 8, 6), surf.get_rect(), 1)
    pygame.draw.rect(surf, (94, 80, 56),
                     pygame.Rect(1, 1, width - 2, 18))
    surf.blit(fonts.small.render("Choose Option", True, (20, 16, 10)),
              (8, 3))
    rects = []
    y = 22
    for i, entry in enumerate(entries):
        rect = pygame.Rect(2, y, width - 4, row_h)
        if i == hover:
            pygame.draw.rect(surf, (74, 62, 40), rect)
        color = (235, 225, 200) if i != hover else (255, 255, 240)
        surf.blit(fonts.small.render(entry, True, color), (8, y + 2))
        rects.append(rect)
        y += row_h
    return surf, rects


LEGEND_LINES = [
    ("MOUSE", HEADER),
    ("L-click   walk / use / next", TEXT),
    ("R-click   options menu", TEXT),
    ("Mid-drag  rotate view", TEXT),
    ("Wheel     zoom", TEXT),
    ("KEYS", HEADER),
    ("Arrows    rotate camera", TEXT),
    ("          (PTZ at helm)", DIM),
    ("P         first-person (WASD)", TEXT),
    ("C         camera helm", TEXT),
    ("R         roof on/off", TEXT),
    ("B         backpack", TEXT),
    ("N         power meter", TEXT),
    ("K         this legend", TEXT),
    (", .       rotate placement", TEXT),
    ("[ ]       sim speed", TEXT),
    ("Del       pack up prop", TEXT),
    ("Tab       360 view", TEXT),
    ("F5/F9/F6  save/load/BOM", TEXT),
]


def render_legend(fonts: Fonts, collapsed: bool) -> pygame.Surface:
    if collapsed:
        surf = pygame.Surface((92, 22), pygame.SRCALPHA)
        surf.fill(BG_SOFT)
        pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
        surf.blit(fonts.small.render("K: keys ▸", True, DIM), (8, 4))
        return surf
    width = 196
    height = 14 + len(LEGEND_LINES) * 17
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG_SOFT)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
    y = 6
    for text, color in LEGEND_LINES:
        font = fonts.small
        surf.blit(font.render(text, True, color), (8, y))
        y += 17
    return surf


def render_dome_manager(
    fonts: Fonts,
    rows: list[dict],
    active: int,
) -> tuple[pygame.Surface, list[pygame.Rect], pygame.Rect]:
    """Site overview: one row per dome + an 'Add dome' row.
    Returns (surface, row_rects, add_rect)."""
    width = 430
    row_h = 34
    pad = 8
    height = pad + 24 + row_h * len(rows) + 26 + pad
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
    surf.blit(fonts.title.render("SITE — DOMES", True, HEADER),
              (pad + 2, pad))
    y = pad + 24
    rects = []
    for i, row in enumerate(rows):
        rect = pygame.Rect(4, y, width - 8, row_h - 2)
        if i == active:
            pygame.draw.rect(surf, SELECT_BG, rect)
        pygame.draw.rect(surf, (50, 70, 88), rect, 1)
        title = f"DOME {i + 1}  {row['title']}"
        surf.blit(fonts.body.render(title, True,
                                    ACCENT if i == active else TEXT),
                  (12, y + 2))
        surf.blit(fonts.small.render(row["info"], True, DIM),
                  (12, y + 17))
        rects.append(rect)
        y += row_h
    add_rect = pygame.Rect(4, y + 2, width - 8, 20)
    pygame.draw.rect(surf, (30, 60, 42), add_rect)
    pygame.draw.rect(surf, (60, 140, 90), add_rect, 1)
    surf.blit(fonts.body.render("+ Add dome  (choose style, then click "
                                "the ground)", True, GOOD), (12, y + 3))
    return surf, rects, add_rect


def render_crosshair() -> pygame.Surface:
    size = 22
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(surf, (255, 255, 255, 200), (c, c), 7, 1)
    pygame.draw.circle(surf, (255, 180, 60, 255), (c, c), 2)
    return surf
```

==========================================================================
======== FILE: dome_creator.py ========
==========================================================================

```python
"""
Parametric Geodesic Dome Creator — a walkable build-a-home customizer.

Everything about the dome is live-editable from the in-world menu:
frequency, radius, strut shape/size, frame material and color, the
recessed interchangeable panels between struts (windows, shingles,
plastic sheeting, solar, ...), stacked cladding layers, and the
foundation (deck / concrete / gravel / pavers). A material breakdown
(weights, costs, strut cut list) updates in real time and can be
exported as a bill of materials.

Rendering keeps the original dual pipeline: a normal perspective view
and a full 360-degree six-point (azimuthal equidistant) projection.

Install:
    py -3.12 -m pip install pygame moderngl numpy

Run:
    py -3.12 dome_creator.py

Controls:
    M                   Toggle the build menu
    Arrows / Enter      Navigate menu, change values, apply
    Mouse aim + Click   Swap the aimed panel (right-click = previous type)
    V                   Apply the aimed panel's type to every panel
    W / A / S / D       Move        Shift  Sprint      Mouse  Look
    F                   Fly/walk    Space/Ctrl  Up/down in fly mode
    Tab                 Toggle six-point 360 / normal perspective
    Q / E               Roll the six-point image
    G                   Spherical guide grid      H   Toggle HUD
    F5 / F9 / F6        Save design / Load design / Export BOM
    R                   Reset player
    Escape              Release mouse; press again to quit
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Iterable

import moderngl
import numpy as np
import pygame

from dome_model import DomeConfig, DomeModel, FRAME_STYLES, HUB_STYLES
from materials import (
    FRAME_COLORS,
    FRAME_MATERIALS,
    FOUNDATION_TYPES,
    LAYER_TYPES,
    PANEL_COLORS,
    PANEL_TYPES,
    STRUT_SHAPES,
)
from mesh_builder import (
    Mesh,
    build_avatar_mesh,
    build_dome_mesh,
    build_environment,
    build_prop_mesh,
    build_worker_mesh,
    console_placement,
)
import overlay_ui
import workshop
from electrical import ElectricalSystem
from overlay_ui import Fonts, MenuItem
from workshop import PROP_TYPES, ROOM_TYPES, ROOM_TYPE_BY_NAME


WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
CUBE_FACE_SIZE = 768
PLAYER_HEIGHT = 1.75
NEAR_PLANE = 0.06
FAR_PLANE = 500.0

DESIGN_FILE = "dome_design.json"
BOM_FILE = "dome_bom.txt"

PTZ_TEXTURE_SIZE = (960, 540)      # high-definition 16:9 video feed
VIDEO_WINDOW_SIZE = (384, 216)
VIDEO_WINDOW_SIZE_HELM = (640, 360)
HELM_RANGE = 4.0                   # max distance to click the wall screen
HELM_LEASH = 5.5                   # walk further than this and helm releases


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def normalize(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32)
    length = float(np.linalg.norm(vector))
    if length <= 1e-8:
        return vector.copy()
    return vector / length


def perspective_matrix(fov_y_degrees, aspect, near, far) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_y_degrees) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at_matrix(eye, target, up_hint) -> np.ndarray:
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, up_hint))
    if np.linalg.norm(right) < 1e-6:
        right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0],
                                                     dtype=np.float32)))
    up = normalize(np.cross(right, forward))
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = right
    m[1, :3] = up
    m[2, :3] = -forward
    m[0, 3] = -float(np.dot(right, eye))
    m[1, 3] = -float(np.dot(up, eye))
    m[2, 3] = float(np.dot(forward, eye))
    return m


def rotation_about_axis(vector, axis, angle) -> np.ndarray:
    axis = normalize(axis)
    vector = np.asarray(vector, dtype=np.float32)
    c, s = math.cos(angle), math.sin(angle)
    return (vector * c + np.cross(axis, vector) * s
            + axis * float(np.dot(axis, vector)) * (1.0 - c)).astype(np.float32)


# ---------------------------------------------------------------------------
# Shaders
# ---------------------------------------------------------------------------

SCENE_VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;
in vec4 in_color;
in float in_mat;

uniform mat4 u_mvp;
uniform mat4 u_model;

out vec3 v_world_position;
out vec3 v_normal;
out vec4 v_color;
flat out float v_mat;

void main() {
    vec4 world = u_model * vec4(in_position, 1.0);
    v_world_position = world.xyz;
    v_normal = mat3(u_model) * in_normal;
    v_color = in_color;
    v_mat = in_mat;
    gl_Position = u_mvp * world;
}
"""


SCENE_FRAGMENT_SHADER = """
#version 330

in vec3 v_world_position;
in vec3 v_normal;
in vec4 v_color;
flat in float v_mat;

uniform vec3 u_camera_position;
uniform vec3 u_light_direction;
uniform vec3 u_sky_color;
uniform float u_ghost;          // 0 off, 1 valid placement, 2 invalid
uniform float u_cut_z;          // roof fade: discard everything above
uniform float u_exposure;       // camera auto-exposure boost
uniform float u_headlamp;       // camera illuminator strength (PTZ pass)
uniform int u_light_count;      // placed lamp props
uniform vec3 u_light_positions[16];

out vec4 frag_color;

float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Procedural material patterns, keyed by mat id.
float surface_pattern(int id, vec3 p, vec3 n) {
    if (id == 1) {                                     // shingles
        float az = atan(p.y, p.x);
        vec2 g = vec2(az * 14.0, p.z * 3.6);
        g.x += step(0.5, fract(g.y * 0.5)) * 0.5;
        float fy = fract(g.y);
        float fx = fract(g.x);
        float row_gap = 1.0 - smoothstep(0.02, 0.12, fy);
        float col_gap = 1.0 - smoothstep(0.01, 0.06, fx);
        float shade = 0.95 + 0.10 * hash21(floor(g));
        return shade * (1.0 - 0.38 * max(row_gap, col_gap * 0.8));
    }
    if (id == 2) {                                     // plastic sheeting
        float w = sin(p.x * 7.0 + p.z * 5.0) * sin(p.y * 6.0 - p.z * 3.0);
        return 1.0 + 0.14 * w;
    }
    if (id == 4) {                                     // wood grain
        return 1.0 + 0.08 * sin((p.x + p.y) * 25.0 + sin(p.z * 8.0) * 2.0);
    }
    if (id == 5) {                                     // solar cells
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0))
            : cross(n, vec3(1.0, 0.0, 0.0)));
        vec3 t2 = cross(n, t1);
        vec2 uv = vec2(dot(p, t1), dot(p, t2)) * 3.0;
        vec2 f = abs(fract(uv) - 0.5);
        float line = 1.0 - smoothstep(0.44, 0.5, max(f.x, f.y));
        return 0.85 + 0.55 * (1.0 - line);
    }
    if (id == 6) {                                     // concrete
        float speck = 0.95 + 0.08 * hash21(floor(p.xy * 6.0));
        float jx = 1.0 - smoothstep(0.0, 0.02, abs(fract(p.x / 2.4) - 0.5) * 2.4 - 1.16);
        float jy = 1.0 - smoothstep(0.0, 0.02, abs(fract(p.y / 2.4) - 0.5) * 2.4 - 1.16);
        return speck * (1.0 - 0.25 * max(jx, jy));
    }
    if (id == 7) {                                     // deck planks
        float fy = fract(p.y / 0.145);
        float gap = 1.0 - smoothstep(0.02, 0.06, fy);
        float row = hash21(vec2(floor(p.y / 0.145), 0.0));
        float grain = 0.96 + 0.07 * sin(p.x * 40.0 + row * 20.0);
        return grain * (1.0 - 0.45 * gap);
    }
    if (id == 8) {                                     // grass
        float coarse = 0.90 + 0.16 * hash21(floor(p.xy * 1.5));
        float fine = 0.95 + 0.10 * hash21(floor(p.xy * 9.0));
        return coarse * fine;
    }
    if (id == 9) {                                     // ribbed metal
        vec3 t1 = normalize(abs(n.z) < 0.9
            ? cross(n, vec3(0.0, 0.0, 1.0))
            : cross(n, vec3(1.0, 0.0, 0.0)));
        return 1.0 + 0.10 * sin(dot(p, t1) * 30.0);
    }
    if (id == 10) {                                    // canvas weave
        return 0.97 + 0.06 * sin(p.x * 90.0) * sin(p.y * 90.0)
             + 0.04 * sin(p.z * 70.0);
    }
    if (id == 11) {                                    // gravel
        return 0.85 + 0.16 * hash21(floor(p.xy * 22.0))
             + 0.08 * hash21(floor(p.xy * 5.0));
    }
    return 1.0;
}

void main() {
    if (v_world_position.z > u_cut_z) {
        discard;    // RuneScape-style hidden roof
    }

    vec3 normal = normalize(v_normal);
    if (!gl_FrontFacing) {
        normal = -normal;
    }

    vec3 light_direction = normalize(-u_light_direction);
    vec3 view_direction = normalize(u_camera_position - v_world_position);
    vec3 half_direction = normalize(light_direction + view_direction);

    float diffuse = max(dot(normal, light_direction), 0.0);
    float specular = pow(max(dot(normal, half_direction), 0.0), 48.0);
    float rim = pow(1.0 - max(dot(normal, view_direction), 0.0), 3.0);

    int mat_id = int(v_mat + 0.5);

    if (mat_id == 12) {
        // Emissive surfaces (lamp panels, status lights) ignore lighting.
        frag_color = vec4(v_color.rgb * 1.3, v_color.a);
        return;
    }

    float pattern = surface_pattern(mat_id, v_world_position, normal);

    vec3 base = v_color.rgb * pattern;
    vec3 lit = base * (0.40 + 0.62 * diffuse);
    lit += vec3(1.0, 0.98, 0.92) * specular * (mat_id == 3 ? 0.9 : 0.30);
    lit += u_sky_color * rim * (mat_id == 3 ? 0.45 : 0.12);

    // Point lights from placed workshop lamps (warm white, attenuated).
    vec3 point_sum = vec3(0.0);
    for (int i = 0; i < u_light_count; i++) {
        vec3 to_light = u_light_positions[i] - v_world_position;
        float dist = length(to_light);
        float atten = 3.5 / (1.0 + 0.6 * dist + 0.30 * dist * dist);
        point_sum += vec3(1.0, 0.92, 0.78) * atten
                   * max(dot(normal, to_light / dist), 0.0);
    }
    lit += base * point_sum;

    // Camera-mounted illuminator: lights whatever the PTZ looks at.
    if (u_headlamp > 0.0) {
        vec3 to_cam = u_camera_position - v_world_position;
        float cam_dist = length(to_cam);
        float boost = u_headlamp / (1.0 + 0.015 * cam_dist * cam_dist);
        lit += base * boost * max(dot(normal, to_cam / cam_dist), 0.0);
    }

    float alpha = v_color.a;
    if (mat_id == 3) {
        // Glass gets a fresnel-style opacity boost at grazing angles.
        alpha = clamp(alpha + rim * 0.5, 0.0, 1.0);
    }

    float dist = length(u_camera_position - v_world_position);
    float fog = clamp((dist - 90.0) / 220.0, 0.0, 0.9);

    if (u_ghost > 0.5) {
        vec3 tint = (u_ghost > 1.5)
            ? vec3(1.0, 0.25, 0.20)
            : vec3(0.30, 1.00, 0.45);
        lit = mix(lit, tint, 0.45);
        alpha = 0.55;
    }

    frag_color = vec4(mix(lit, u_sky_color, fog) * u_exposure, alpha);
}
"""


SCREEN_VERTEX_SHADER = """
#version 330
in vec3 in_position;
in vec2 in_uv;
uniform mat4 u_mvp;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = u_mvp * vec4(in_position, 1.0);
}
"""

SCREEN_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() {
    vec3 color = texture(u_texture, v_uv).rgb;
    float scanline = 0.94 + 0.06 * sin(v_uv.y * 540.0);
    vec2 edge = abs(v_uv - 0.5) * 2.0;
    float vignette = 1.0 - 0.25 * pow(max(edge.x, edge.y), 6.0);
    frag_color = vec4(color * scanline * vignette * 1.08
                      + vec3(0.01, 0.015, 0.02), 1.0);
}
"""


HIGHLIGHT_VERTEX_SHADER = """
#version 330
in vec3 in_position;
uniform mat4 u_mvp;
void main() { gl_Position = u_mvp * vec4(in_position, 1.0); }
"""

HIGHLIGHT_FRAGMENT_SHADER = """
#version 330
uniform vec4 u_color;
out vec4 frag_color;
void main() { frag_color = u_color; }
"""


PANORAMA_VERTEX_SHADER = """
#version 330

in vec2 in_position;
out vec2 v_uv;

void main() {
    v_uv = in_position * 0.5 + 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


PANORAMA_FRAGMENT_SHADER = """
#version 330

in vec2 v_uv;

uniform sampler2D u_front;
uniform sampler2D u_back;
uniform sampler2D u_right;
uniform sampler2D u_left;
uniform sampler2D u_up;
uniform sampler2D u_down;

uniform vec2 u_resolution;
uniform float u_roll;
uniform bool u_show_grid;
uniform vec3 u_outside_color;

out vec4 frag_color;

const float PI = 3.14159265358979323846;

vec3 azimuthal_equidistant_ray(vec2 disk) {
    float radius = length(disk);
    float theta = radius * PI;
    float azimuth = atan(disk.y, disk.x) + u_roll;
    float sin_theta = sin(theta);
    return normalize(vec3(
        sin_theta * cos(azimuth),
        sin_theta * sin(azimuth),
        cos(theta)
    ));
}

vec4 sample_six_views(vec3 direction) {
    vec3 a = abs(direction);
    vec2 uv;

    if (a.z >= a.x && a.z >= a.y) {
        if (direction.z >= 0.0) {
            uv = vec2(direction.x, direction.y) / a.z * 0.5 + 0.5;
            return texture(u_front, uv);
        }
        uv = vec2(-direction.x, direction.y) / a.z * 0.5 + 0.5;
        return texture(u_back, uv);
    }
    if (a.x >= a.y) {
        if (direction.x >= 0.0) {
            uv = vec2(-direction.z, direction.y) / a.x * 0.5 + 0.5;
            return texture(u_right, uv);
        }
        uv = vec2(direction.z, direction.y) / a.x * 0.5 + 0.5;
        return texture(u_left, uv);
    }
    if (direction.y >= 0.0) {
        uv = vec2(direction.x, -direction.z) / a.y * 0.5 + 0.5;
        return texture(u_up, uv);
    }
    uv = vec2(direction.x, direction.z) / a.y * 0.5 + 0.5;
    return texture(u_down, uv);
}

float spherical_grid(vec3 direction) {
    float longitude = atan(direction.x, direction.z);
    float latitude = asin(clamp(direction.y, -1.0, 1.0));
    float line = min(abs(sin(longitude * 12.0)), abs(sin(latitude * 12.0)));
    return 1.0 - smoothstep(0.0, 0.035, line);
}

void main() {
    vec2 pixel = v_uv * u_resolution;
    vec2 center = u_resolution * 0.5;
    float diameter = min(u_resolution.x, u_resolution.y);
    vec2 disk = (pixel - center) / (diameter * 0.5);

    float radius = length(disk);
    if (radius > 1.0) {
        frag_color = vec4(u_outside_color, 1.0);
        return;
    }

    vec3 direction = azimuthal_equidistant_ray(disk);
    vec4 scene_color = sample_six_views(direction);

    if (u_show_grid) {
        float grid = spherical_grid(direction);
        scene_color.rgb = mix(scene_color.rgb, vec3(0.22, 0.48, 0.62),
                              grid * 0.22);
    }

    float rim = 1.0 - smoothstep(0.985, 1.0, radius);
    scene_color.rgb *= 0.72 + 0.28 * rim;
    frag_color = scene_color;
}
"""


NORMAL_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, v_uv); }
"""


OVERLAY_VERTEX_SHADER = """
#version 330

in vec2 in_position;
uniform vec4 u_rect;      // x, y, w, h in pixels (top-left origin)
uniform vec2 u_screen;
uniform int u_flip;       // 1 when drawing a GL-rendered (bottom-up) texture
out vec2 v_uv;

void main() {
    vec2 p01 = in_position * 0.5 + 0.5;
    vec2 pixel = u_rect.xy + p01 * u_rect.zw;
    vec2 ndc = vec2(
        pixel.x / u_screen.x * 2.0 - 1.0,
        1.0 - pixel.y / u_screen.y * 2.0
    );
    v_uv = vec2(p01.x, u_flip == 1 ? 1.0 - p01.y : p01.y);
    gl_Position = vec4(ndc, 0.0, 1.0);
}
"""

OVERLAY_FRAGMENT_SHADER = """
#version 330
in vec2 v_uv;
uniform sampler2D u_texture;
out vec4 frag_color;
void main() { frag_color = texture(u_texture, v_uv); }
"""


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

@dataclass
class PlayerCamera:
    position: np.ndarray
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    fly_mode: bool = False
    movement_speed: float = 6.0
    sprint_multiplier: float = 3.0
    mouse_sensitivity: float = 0.0022

    def basis(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        forward = normalize(np.array([
            math.sin(self.yaw) * math.cos(self.pitch),
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
        ], dtype=np.float32))
        world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        right = normalize(np.cross(forward, world_up))
        if np.linalg.norm(right) < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        up = normalize(np.cross(right, forward))
        if abs(self.roll) > 1e-7:
            right = rotation_about_axis(right, forward, self.roll)
            up = rotation_about_axis(up, forward, self.roll)
        return forward, right, up


@dataclass
class PTZCamera:
    """Simulated pan-tilt-zoom camera hanging from the dome apex."""
    pan: float = 180.0      # degrees, azimuth (0 = north/+Y)
    tilt: float = 32.0      # degrees from straight down (0..100)
    fov: float = 58.0       # degrees, zoom = narrower fov
    pan_rate: float = 70.0
    tilt_rate: float = 45.0
    zoom_rate: float = 35.0

    def basis(self) -> tuple[np.ndarray, np.ndarray]:
        """Forward and no-roll up vector from pan/tilt."""
        p = math.radians(self.pan)
        t = math.radians(self.tilt)
        forward = np.array([
            math.sin(t) * math.sin(p),
            math.sin(t) * math.cos(p),
            -math.cos(t),
        ], dtype=np.float32)
        up = np.array([
            math.cos(t) * math.sin(p),
            math.cos(t) * math.cos(p),
            math.sin(t),
        ], dtype=np.float32)
        return normalize(forward), normalize(up)


def ray_triangle(origin, direction, v0, v1, v2) -> float | None:
    """Möller–Trumbore; returns hit distance or None."""
    e1 = v1 - v0
    e2 = v2 - v0
    pvec = np.cross(direction, e2)
    det = float(np.dot(e1, pvec))
    if abs(det) < 1e-9:
        return None
    inv = 1.0 / det
    tvec = origin - v0
    u = float(np.dot(tvec, pvec)) * inv
    if u < 0.0 or u > 1.0:
        return None
    qvec = np.cross(tvec, e1)
    v = float(np.dot(direction, qvec)) * inv
    if v < 0.0 or u + v > 1.0:
        return None
    t = float(np.dot(e2, qvec)) * inv
    return t if t > 0.05 else None


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class DomeCreatorApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

        pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
        )
        pygame.display.set_caption("Geodesic Dome Creator")

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.blend_func = (
            moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self.ctx.gc_mode = "auto"

        self.clock = pygame.time.Clock()
        self.running = True
        self.mouse_captured = True
        self.escape_armed = False
        self.six_point_enabled = False
        self.show_grid = False
        self.show_hud = True
        self.six_point_spin_speed = 0.0
        self.sky_color = (0.60, 0.74, 0.90)

        # The site holds any number of domes; menus/stats/camera follow
        # the active (selected) one.
        import presets
        first = DomeModel(DomeConfig.from_dict(presets.PRESETS[0][1]))
        self.domes: list[DomeModel] = [first]
        self.active_dome = 0
        self.rebuild_queue: set[int] = {0}

        self.camera = PlayerCamera(
            position=np.array(
                [0.0, -(self.model.config.radius * 2.0 + 6.0), PLAYER_HEIGHT],
                dtype=np.float32,
            ),
            pitch=0.06,
        )

        # Programs.
        self.scene_program = self.ctx.program(
            vertex_shader=SCENE_VERTEX_SHADER,
            fragment_shader=SCENE_FRAGMENT_SHADER,
        )
        self.highlight_program = self.ctx.program(
            vertex_shader=HIGHLIGHT_VERTEX_SHADER,
            fragment_shader=HIGHLIGHT_FRAGMENT_SHADER,
        )
        self.panorama_program = self.ctx.program(
            vertex_shader=PANORAMA_VERTEX_SHADER,
            fragment_shader=PANORAMA_FRAGMENT_SHADER,
        )
        self.normal_program = self.ctx.program(
            vertex_shader=PANORAMA_VERTEX_SHADER,
            fragment_shader=NORMAL_FRAGMENT_SHADER,
        )
        self.overlay_program = self.ctx.program(
            vertex_shader=OVERLAY_VERTEX_SHADER,
            fragment_shader=OVERLAY_FRAGMENT_SHADER,
        )
        self.screen_program = self.ctx.program(
            vertex_shader=SCREEN_VERTEX_SHADER,
            fragment_shader=SCREEN_FRAGMENT_SHADER,
        )

        self._create_screen_quad()
        self._create_render_targets()

        # PTZ camera system: one camera + feed + wall monitor per dome.
        self.ptzs: list[PTZCamera] = [PTZCamera()]
        self.consoles: list[dict] = [{}]
        self.feeds: list[dict] = [self._create_feed()]
        self.monitors: list[dict] = [self._create_monitor()]
        self.trackers: list = []
        import vision
        self.trackers.append(vision.VisionTracker())
        self._feed_cycle = 0
        self.helm_active = False
        self.helm_remote = False
        self.preset_index = 0
        self.aiming_screen = False
        self.aimed_screen_dome = 0
        self.screen_distance = 0.0
        self._osd_state: tuple | None = None

        # Prop placement and picking.
        self.placing = None                  # PropType while in place mode
        self.placing_from_slot: int | None = None   # backpack slot source
        self.ghost_yaw = 0.0
        self.ghost_pos = np.zeros(3)
        self.ghost_valid = False
        self.ghost_cache: dict[str, dict] = {}
        self.aimed_prop_index: int | None = None
        self.light_array = np.zeros((16, 3), dtype=np.float32)
        self.light_count = 0

        # RuneScape-style controls: orbit camera + click to move.
        self.control_mode = "orbit"          # "orbit" or "fp"
        self.orbit_yaw = math.pi             # look north at the dome
        self.orbit_pitch = 0.62
        self.orbit_dist = 11.0
        self.avatar_yaw = 0.0
        self.walk_target: np.ndarray | None = None
        self.pending_action: dict | None = None
        self.roof_hidden = False
        self.inventory_open = True
        self.inventory_selected: int | None = None
        self.inventory_rects: list = []
        self.inventory_origin = (0, 0)
        self.toolbar_rects: list = []
        self.toolbar_origin = (0, 0)
        self.toolbar_dirty = True
        self.inventory_dirty = True
        self.avatar_buffers = self._upload_mesh(build_avatar_mesh())
        self.marker_vbo = self.ctx.buffer(reserve=6 * 3 * 4)
        self.marker_vao = self.ctx.vertex_array(
            self.highlight_program,
            [(self.marker_vbo, "3f", "in_position")],
        )

        # Static environment mesh.
        self.env_buffers = self._upload_mesh(build_environment())

        # Construction simulation and the shared power grid.
        self.dome_buffers_list: list[dict | None] = [None]
        self.dome_events_list: list[list] = [[]]
        self.render_limits: dict[int, tuple[int, int]] = {}
        self.sim: dict | None = None
        self.worker_buffers = self._upload_mesh(build_worker_mesh())
        self.worker_states: list[dict] = []
        self.energy = ElectricalSystem()
        self.energy_open = False

        # RuneScape-style UI state.
        self.context_menu: dict | None = None
        self.legend_open = True
        self.domes_open = False
        self.dome_rows_rects: list = []
        self.dome_add_rect = None
        self.domes_origin = (0, 0)
        self.placing_dome: dict | None = None
        self.menu_hit_map: dict = {"tabs": [], "rows": []}
        self.lab_base = 1
        self.lab_qty: dict[str, int] = {}
        self.lab_counter = 1

        self._rebuild_dome(0)

        # Aim highlight.
        self.highlight_vbo = self.ctx.buffer(reserve=3 * 3 * 4)
        self.highlight_vao = self.ctx.vertex_array(
            self.highlight_program,
            [(self.highlight_vbo, "3f", "in_position")],
        )

        # Overlays.
        self.fonts = Fonts()
        self.menu_open = True
        self.menu_page = 0
        self.menu_pages = ["DOME", "ROOMS", "PROPS", "LAB", "FILE"]
        self.menu_selected = 1
        self.menu_items = self._build_menu_items()
        self.menu_dirty = True
        self.stats_dirty = True
        self.help_dirty = True
        self.aimed_panel = None
        self.aimed_panel_dome = 0
        self.ghost_dome = 0
        self.aimed_distance = 0.0
        self.flash_message = ""
        self.flash_until = 0.0
        self.overlay_textures: dict[str, dict] = {}
        self._update_overlay("crosshair", overlay_ui.render_crosshair())

        # Orbit (RuneScape-style) mode starts with a free, visible cursor.
        self._set_mouse_capture(False)
        self.escape_armed = False

        # Smoke-test mode: run a scripted sequence and quit.
        self.smoke_frames = int(os.environ.get("DOME_SMOKE", "0"))
        self.frame_count = 0

    # -- active-dome accessors ---------------------------------------------

    @property
    def model(self) -> DomeModel:
        return self.domes[self.active_dome]

    @property
    def ptz(self) -> PTZCamera:
        return self.ptzs[self.active_dome]

    @property
    def console(self) -> dict:
        return self.consoles[self.active_dome]

    @property
    def ptz_texture(self):
        return self.feeds[self.active_dome]["texture"]

    def _create_feed(self) -> dict:
        texture = self.ctx.texture(PTZ_TEXTURE_SIZE, components=3,
                                   dtype="f1")
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        depth = self.ctx.depth_renderbuffer(PTZ_TEXTURE_SIZE)
        fbo = self.ctx.framebuffer(color_attachments=[texture],
                                   depth_attachment=depth)
        return {"texture": texture, "depth": depth, "fbo": fbo}

    def _create_monitor(self) -> dict:
        vbo = self.ctx.buffer(reserve=6 * 5 * 4)
        vao = self.ctx.vertex_array(
            self.screen_program,
            [(vbo, "3f 2f", "in_position", "in_uv")])
        return {"vbo": vbo, "vao": vao}

    def _select_dome(self, idx: int) -> None:
        idx = max(0, min(idx, len(self.domes) - 1))
        if idx == self.active_dome:
            return
        if self.helm_active:
            self._set_helm(False)
        self.active_dome = idx
        self.menu_items = self._build_menu_items()
        self.menu_dirty = True
        self.stats_dirty = True
        self.help_dirty = True
        self._osd_state = None
        self._flash(f"Selected dome {idx + 1}")

    # -- menu ------------------------------------------------------------

    def _mark_changed(self, dome: int | None = None) -> None:
        self.rebuild_queue.add(
            self.active_dome if dome is None else dome)
        self.menu_dirty = True
        self.stats_dirty = True

    def _build_menu_items(self) -> list[MenuItem]:
        builders = [self._menu_page_dome, self._menu_page_rooms,
                    self._menu_page_props, self._menu_page_lab,
                    self._menu_page_file]
        return builders[self.menu_page]()

    def _menu_helpers(self, items: list[MenuItem]):
        def choice(label, options, get_idx, set_idx):
            def value():
                return options[get_idx()]

            def change(delta):
                set_idx((get_idx() + delta) % len(options))
                self._mark_changed()

            items.append(MenuItem(label, "choice", value, change))

        def number(label, get, set_val, step, low, high, fmt):
            def value():
                return fmt(get())

            def change(delta):
                set_val(min(high, max(low, get() + delta * step)))
                self._mark_changed()

            items.append(MenuItem(label, "choice", value, change))

        def header(label):
            items.append(MenuItem(label, "header"))

        def action(label, fn):
            items.append(MenuItem(label, "action", activate=fn))

        return choice, number, header, action

    def _menu_page_dome(self) -> list[MenuItem]:
        cfg = self.model.config
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("STRUCTURE")
        choice("Frequency",
               [f"{i}V" for i in range(1, 5)],
               lambda: cfg.frequency - 1,
               lambda i: setattr(cfg, "frequency", i + 1))
        number("Radius",
               lambda: cfg.radius,
               lambda v: setattr(cfg, "radius", v),
               0.5, 2.0, 15.0, lambda v: f"{v:.1f} m")

        header("FRAME")
        choice("Strut shape",
               [s.name for s in STRUT_SHAPES],
               lambda: cfg.strut_shape,
               lambda i: setattr(cfg, "strut_shape", i))
        number("Strut width",
               lambda: cfg.strut_width,
               lambda v: setattr(cfg, "strut_width", v),
               0.005, 0.02, 0.16, lambda v: f"{v * 100:.1f} cm")
        choice("Material",
               [m.name for m in FRAME_MATERIALS],
               lambda: cfg.frame_material,
               lambda i: setattr(cfg, "frame_material", i))
        choice("Frame color",
               [c.name for c in FRAME_COLORS],
               lambda: cfg.frame_color,
               lambda i: setattr(cfg, "frame_color", i))
        choice("Frame style",
               FRAME_STYLES,
               lambda: FRAME_STYLES.index(cfg.frame_style),
               lambda i: setattr(cfg, "frame_style", FRAME_STYLES[i]))
        choice("Hub style",
               HUB_STYLES,
               lambda: HUB_STYLES.index(cfg.hub_style),
               lambda i: setattr(cfg, "hub_style", HUB_STYLES[i]))
        choice("Wedge curve",
               ["Inside", "Outside"],
               lambda: 1 if cfg.wedge_flip else 0,
               lambda i: setattr(cfg, "wedge_flip", bool(i)))

        header("PANELS")

        def panel_fill_value():
            return cfg.default_panel

        def panel_fill_change(delta):
            import materials
            names = materials.panel_type_names()
            current = (names.index(cfg.default_panel)
                       if cfg.default_panel in names else 0)
            cfg.default_panel = names[(current + delta) % len(names)]
            self._mark_changed()

        def panel_fill_apply():
            self.model.set_all_panels(cfg.default_panel)
            self._mark_changed()
            return f"All panels set to {cfg.default_panel}"

        items.append(MenuItem("Panel fill", "choice", panel_fill_value,
                              panel_fill_change, panel_fill_apply))
        choice("Panel color",
               [c.name for c in PANEL_COLORS],
               lambda: cfg.panel_color,
               lambda i: setattr(cfg, "panel_color", i))
        number("Recess depth",
               lambda: cfg.recess_pct,
               lambda v: setattr(cfg, "recess_pct", v),
               0.05, 0.05, 0.95, lambda v: f"{v * 100:.0f} %")

        header("CLADDING LAYERS")
        layer_names = [l.name for l in LAYER_TYPES]
        for slot in range(3):
            def layer_get(slot=slot):
                return layer_names.index(cfg.layers[slot])

            def layer_set(i, slot=slot):
                cfg.layers[slot] = layer_names[i]

            choice(f"Layer {slot + 1}", layer_names, layer_get, layer_set)

        header("SITE")
        foundation_names = [f.name for f in FOUNDATION_TYPES]
        choice("Foundation",
               foundation_names,
               lambda: foundation_names.index(cfg.foundation),
               lambda i: setattr(cfg, "foundation", foundation_names[i]))
        number("Foundation size",
               lambda: cfg.foundation_scale,
               lambda v: setattr(cfg, "foundation_scale", v),
               0.05, 1.0, 1.6, lambda v: f"x{v:.2f}")

        return items

    def _menu_page_rooms(self) -> list[MenuItem]:
        cfg = self.model.config
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("PARTITIONS")
        choice("Partition style",
               workshop.PARTITION_MODES,
               lambda: workshop.PARTITION_MODES.index(cfg.partitions),
               lambda i: setattr(
                   cfg, "partitions", workshop.PARTITION_MODES[i]))

        header("ROOM ASSIGNMENTS")
        room_names = [r.name for r in ROOM_TYPES]
        for section in range(10):
            def get_idx(section=section):
                return room_names.index(cfg.sections[section])

            def set_idx(i, section=section):
                cfg.sections[section] = room_names[i]

            choice(workshop.section_label(section), room_names,
                   get_idx, set_idx)
        return items

    def _menu_page_props(self) -> list[MenuItem]:
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        category = None
        for prop in PROP_TYPES:
            if prop.category != category:
                category = prop.category
                header(category)

            def start(prop=prop):
                self.placing = prop
                self.ghost_yaw = 0.0
                self.help_dirty = True
                return (f"Placing {prop.name} — aim at floor, click to "
                        "place, , . rotate, Esc done")

            watts = f", {prop.watts:.0f} W" if prop.watts else ""
            items.append(MenuItem(
                f"{prop.name}  (${prop.cost:,.0f}, {prop.weight:.0f} kg"
                f"{watts})", "action", activate=start))

        header("EDIT")

        def clear_props():
            count = len(self.model.config.props)
            self.model.config.props.clear()
            self._mark_changed()
            return f"Removed {count} props"

        action("Clear all props", clear_props)
        return items

    def _menu_page_lab(self) -> list[MenuItem]:
        """Panel Lab: compose custom panels from a base surface plus
        hardware components (brackets, screws, seals...)."""
        import materials
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("PANEL LAB — BASE SURFACE")
        base_names = [p.name for p in materials.PANEL_TYPES
                      if p.name != "Open"]
        self.lab_base = min(self.lab_base, len(base_names) - 1)

        def base_value():
            return base_names[self.lab_base]

        def base_change(delta):
            self.lab_base = (self.lab_base + delta) % len(base_names)
            self.menu_dirty = True

        items.append(MenuItem("Base panel", "choice", base_value,
                              base_change))

        header("COMPONENTS PER PANEL")
        for comp in materials.PANEL_COMPONENTS:
            def get_qty(comp=comp):
                return self.lab_qty.get(comp.name, 0)

            def change_qty(delta, comp=comp):
                qty = max(0, min(12, get_qty() + delta))
                self.lab_qty[comp.name] = qty
                self.menu_dirty = True

            def qty_value(comp=comp):
                extra = ""
                if comp.screws_each:
                    extra = f"  (+{comp.screws_each} screws ea)"
                return f"{get_qty()}{extra}"

            items.append(MenuItem(comp.name, "choice", qty_value,
                                  change_qty))

        header("RESULT")

        def totals_value():
            definition = {"base": base_names[self.lab_base],
                          "components": dict(self.lab_qty)}
            cost, weight, screws, minutes = \
                materials.custom_panel_extras(definition)
            return (f"+${cost:.0f}, +{weight:.1f} kg, {screws} scr, "
                    f"+{minutes:.0f} min")

        items.append(MenuItem("Per-panel extras", "choice",
                              totals_value, None))

        def create_panel():
            import materials as mats
            definition = {
                "base": base_names[self.lab_base],
                "components": {k: v for k, v in self.lab_qty.items()
                               if v > 0},
            }
            if not definition["components"]:
                return "Add at least one component first"
            name = f"Custom Mk{self.lab_counter} " \
                   f"({base_names[self.lab_base]})"
            self.lab_counter += 1
            mats.register_custom_panel(name, definition)
            self.model.config.default_panel = name
            self._mark_changed()
            return (f"Created '{name}' — applied as panel fill; also in "
                    "panel swap cycle")

        def apply_aimed():
            if self.aimed_panel is None:
                return "Aim at a panel first"
            customs = sorted(materials.CUSTOM_PANEL_DEFS)
            if not customs:
                return "Create a custom panel first"
            pmodel = self.domes[self.aimed_panel_dome]
            pmodel.set_panel(self.aimed_panel.key, customs[-1])
            self._mark_changed(self.aimed_panel_dome)
            return f"Applied {customs[-1]} to the aimed panel"

        action("Create custom panel", create_panel)
        action("Apply newest custom to aimed panel", apply_aimed)
        return items

    def _menu_page_file(self) -> list[MenuItem]:
        items: list[MenuItem] = []
        choice, number, header, action = self._menu_helpers(items)

        header("SITE OPERATIONS")

        def sim_active():
            self.start_construction(self.active_dome)
            return f"Simulating dome {self.active_dome + 1} construction"

        def build_dome2():
            import presets
            return self._add_dome(presets.SECOND_DOME, simulate=True)

        def add_worker():
            if self.sim:
                self.sim["workers"] = min(self.sim["workers"] + 1, 8)
                return f"Crew size: {self.sim['workers']}"
            return "No construction running"

        action("Electrify dome (kit + outlets)", self._electrify_dome)
        action("Simulate construction (this dome)", sim_active)
        action("Build power-spoke dome (worker sim)", build_dome2)
        action("Add worker to crew", add_worker)

        header("PRESET SETUPS")
        import presets
        for idx, (name, _data) in enumerate(presets.PRESETS):
            action(f"Load: {name}",
                   lambda idx=idx: self._apply_preset(idx))

        header("FILE")

        def save_design():
            return self._save_design()

        def load_design():
            return self._load_design()

        def export_bom():
            from pathlib import Path
            Path(BOM_FILE).write_text(self.model.bom_text(), encoding="utf-8")
            return f"Exported {BOM_FILE}"

        def reset_player():
            self.camera.position[:] = (
                0.0, -(self.model.config.radius * 2.0 + 6.0),
                PLAYER_HEIGHT)
            self.camera.yaw = 0.0
            self.camera.pitch = 0.06
            self.camera.roll = 0.0
            self.walk_target = None
            self.pending_action = None
            return "Player position reset"

        action("Save design", save_design)
        action("Load design", load_design)
        action("Export bill of materials", export_bom)
        action("Reset player position", reset_player)

        return items

    def _menu_move(self, delta: int) -> None:
        n = len(self.menu_items)
        i = self.menu_selected
        for _ in range(n):
            i = (i + delta) % n
            if self.menu_items[i].kind != "header":
                self.menu_selected = i
                break
        self.menu_dirty = True

    def _flash(self, message: str | None) -> None:
        if message:
            self.flash_message = message
            self.flash_until = time.perf_counter() + 3.0
            self.help_dirty = True

    # -- GPU resources -----------------------------------------------------

    def _create_screen_quad(self) -> None:
        quad = np.array([
            -1.0, -1.0, 1.0, -1.0, -1.0, 1.0,
            -1.0, 1.0, 1.0, -1.0, 1.0, 1.0,
        ], dtype=np.float32)
        self.quad_vbo = self.ctx.buffer(quad.tobytes())
        self.panorama_vao = self.ctx.vertex_array(
            self.panorama_program, [(self.quad_vbo, "2f", "in_position")])
        self.normal_vao = self.ctx.vertex_array(
            self.normal_program, [(self.quad_vbo, "2f", "in_position")])
        self.overlay_vao = self.ctx.vertex_array(
            self.overlay_program, [(self.quad_vbo, "2f", "in_position")])

    def _create_render_targets(self) -> None:
        self.face_textures: dict[str, moderngl.Texture] = {}
        self.face_fbos: dict[str, moderngl.Framebuffer] = {}
        for name in ("front", "back", "right", "left", "up", "down"):
            texture = self.ctx.texture(
                (CUBE_FACE_SIZE, CUBE_FACE_SIZE), components=3, dtype="f1")
            texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            texture.repeat_x = False
            texture.repeat_y = False
            depth = self.ctx.depth_renderbuffer(
                (CUBE_FACE_SIZE, CUBE_FACE_SIZE))
            self.face_textures[name] = texture
            self.face_fbos[name] = self.ctx.framebuffer(
                color_attachments=[texture], depth_attachment=depth)

        width, height = pygame.display.get_window_size()
        self._make_normal_target(width, height)

    def _make_normal_target(self, width: int, height: int) -> None:
        self.normal_texture = self.ctx.texture(
            (max(1, width), max(1, height)), components=3, dtype="f1")
        self.normal_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.normal_depth = self.ctx.depth_renderbuffer(
            (max(1, width), max(1, height)))
        self.normal_fbo = self.ctx.framebuffer(
            color_attachments=[self.normal_texture],
            depth_attachment=self.normal_depth)

    def _recreate_window_target(self) -> None:
        width, height = pygame.display.get_window_size()
        self.normal_fbo.release()
        self.normal_depth.release()
        self.normal_texture.release()
        self._make_normal_target(width, height)
        self.help_dirty = True

    def _upload_mesh(self, mesh: Mesh) -> dict:
        vbo = self.ctx.buffer(mesh.vertices.tobytes())
        buffers = {"vbo": vbo, "opaque": None, "transparent": None,
                   "opaque_vao": None, "transparent_vao": None}
        layout = [(vbo, "3f 3f 4f 1f",
                   "in_position", "in_normal", "in_color", "in_mat")]
        if len(mesh.opaque):
            buffers["opaque"] = self.ctx.buffer(mesh.opaque.tobytes())
            buffers["opaque_vao"] = self.ctx.vertex_array(
                self.scene_program, layout, buffers["opaque"])
        if len(mesh.transparent):
            buffers["transparent"] = self.ctx.buffer(
                mesh.transparent.tobytes())
            buffers["transparent_vao"] = self.ctx.vertex_array(
                self.scene_program, layout, buffers["transparent"])
        return buffers

    def _release_buffers(self, buffers: dict | None) -> None:
        if not buffers:
            return
        for key in ("opaque_vao", "transparent_vao", "opaque",
                    "transparent", "vbo"):
            obj = buffers.get(key)
            if obj is not None:
                obj.release()

    def _rebuild_dome(self, idx: int) -> None:
        if idx >= len(self.domes):
            return
        model = self.domes[idx]
        model.rebuild()
        events: list = []
        mesh = build_dome_mesh(model, events=events)
        self.dome_events_list[idx] = events
        model.construction_hours = sum(e["hours"] for e in events)
        self._release_buffers(self.dome_buffers_list[idx])
        self.dome_buffers_list[idx] = self._upload_mesh(mesh)
        self.rebuild_queue.discard(idx)
        if idx == self.active_dome:
            self.stats_dirty = True
        if self.sim and self.sim["dome"] == idx:
            self._sim_refresh_events()
        self._refresh_lights()

        # Reposition this dome's wall monitor (bl, br, tr, tl corners).
        self.consoles[idx] = console_placement(model)
        bl, br, tr, tl = self.consoles[idx]["screen_corners"]
        data = np.array([
            [*bl, 0.0, 0.0], [*br, 1.0, 0.0], [*tr, 1.0, 1.0],
            [*bl, 0.0, 0.0], [*tr, 1.0, 1.0], [*tl, 0.0, 1.0],
        ], dtype=np.float32)
        self.monitors[idx]["vbo"].write(data.tobytes())

    def _add_dome(self, config_data: dict, origin=None,
                  simulate: bool = False) -> str:
        import vision
        cfg = DomeConfig.from_dict(config_data)
        if origin is None:
            edge = max(
                (float(m.origin[0]) + m.config.radius
                 * m.config.foundation_scale for m in self.domes),
                default=0.0)
            origin = (edge + cfg.radius * cfg.foundation_scale + 4.0, 0.0)
        model = DomeModel(cfg, origin=(float(origin[0]),
                                       float(origin[1])))
        self.domes.append(model)
        self.dome_buffers_list.append(None)
        self.dome_events_list.append([])
        self.ptzs.append(PTZCamera())
        self.consoles.append({})
        self.feeds.append(self._create_feed())
        self.monitors.append(self._create_monitor())
        self.trackers.append(vision.VisionTracker())
        idx = len(self.domes) - 1
        self._rebuild_dome(idx)
        if simulate:
            self.start_construction(idx)
            return f"Worker crew dispatched — constructing dome {idx + 1}"
        return f"Dome {idx + 1} placed"

    def _remove_dome(self, idx: int) -> str:
        if len(self.domes) <= 1:
            return "The last dome cannot be removed"
        if self.sim and self.sim["dome"] == idx:
            self.sim = None
        self._release_buffers(self.dome_buffers_list[idx])
        feed = self.feeds[idx]
        feed["fbo"].release()
        feed["depth"].release()
        feed["texture"].release()
        self.monitors[idx]["vao"].release()
        self.monitors[idx]["vbo"].release()
        for seq in (self.domes, self.dome_buffers_list,
                    self.dome_events_list, self.ptzs, self.consoles,
                    self.feeds, self.monitors, self.trackers):
            seq.pop(idx)
        self.render_limits.pop(idx, None)
        self.render_limits = {
            (k - 1 if k > idx else k): v
            for k, v in self.render_limits.items()}
        if self.sim and self.sim["dome"] > idx:
            self.sim["dome"] -= 1
        if self.active_dome >= len(self.domes):
            self.active_dome = len(self.domes) - 1
        self.menu_items = self._build_menu_items()
        self.menu_dirty = True
        self.stats_dirty = True
        self._refresh_lights()
        return f"Dome {idx + 1} demolished"

    def _all_models(self) -> list:
        return self.domes

    def _refresh_lights(self) -> None:
        """Point lights from lamps that are on, plugged in, and powered."""
        self.light_array[:] = 0.0
        count = 0
        for model in self._all_models():
            fh = model.foundation.height
            ox, oy = float(model.origin[0]), float(model.origin[1])
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None or prop.light_z is None:
                    continue
                if not self.energy.lamps_powered(model, entry):
                    continue
                if count >= 16:
                    break
                self.light_array[count] = (
                    ox + float(entry["x"]), oy + float(entry["y"]),
                    fh + prop.light_z)
                count += 1
        self.light_count = count

    # -- construction simulation ----------------------------------------------

    def _sim_events(self) -> list:
        return self.dome_events_list[self.sim["dome"]]

    def _sim_refresh_events(self) -> None:
        events = self._sim_events()
        self.sim["total"] = sum(e["hours"] for e in events)

    @staticmethod
    def _crew_factor(workers: int) -> float:
        # Diminishing returns: 4 workers ≈ 3.2x, 8 ≈ 5.9x.
        return max(1, workers) ** 0.85

    def start_construction(self, dome_idx: int) -> None:
        events = self.dome_events_list[dome_idx]
        if not events:
            return
        self.sim = {
            "dome": dome_idx,
            "elapsed": 0.0,
            "total": sum(e["hours"] for e in events),
            "speed": 1.0,          # simulated labor-hours per real second
            "step": 0,
            "workers": 1,
        }
        self.render_limits[dome_idx] = (0, 0)
        self.worker_states = [{
            "pos": np.array(events[0]["pos"], dtype=np.float64),
            "yaw": 0.0,
        }]
        self._flash("Construction started — [ ] speed, right-click the "
                    "status bar for crew options")
        self.help_dirty = True

    def _update_construction(self, dt: float) -> None:
        if not self.sim:
            return
        sim = self.sim
        events = self._sim_events()
        if not events:
            self.sim = None
            return
        crew = self._crew_factor(sim["workers"])
        sim["elapsed"] += dt * sim["speed"] * crew
        acc = 0.0
        step = 0
        limits = (0, 0)
        for i, event in enumerate(events):
            if sim["elapsed"] >= acc + event["hours"]:
                acc += event["hours"]
                limits = (event["opaque"], event["transparent"])
                step = i + 1
            else:
                break
        sim["step"] = step
        self.render_limits[sim["dome"]] = limits

        # Crew members spread across the next work stations.
        while len(self.worker_states) < sim["workers"]:
            self.worker_states.append({
                "pos": self.worker_states[0]["pos"].copy(),
                "yaw": 0.0})
        del self.worker_states[sim["workers"]:]
        for w, worker in enumerate(self.worker_states):
            idx = min(step + w, len(events) - 1)
            t = np.array(events[idx]["pos"], dtype=np.float64)
            gap = t - worker["pos"]
            dist = float(np.linalg.norm(gap[:2]))
            if dist > 0.05:
                walk = min(2.2 * dt * max(sim["speed"], 1.0), dist)
                worker["pos"][:2] += gap[:2] / dist * walk
                worker["yaw"] = math.atan2(float(gap[0]), float(gap[1]))
            worker["pos"][2] = t[2]

        if sim["elapsed"] >= sim["total"]:
            dome = sim["dome"]
            self.render_limits.pop(dome, None)
            total = sim["total"]
            workers = sim["workers"]
            self.sim = None
            self.worker_states = []
            days = total / (8.0 * self._crew_factor(workers))
            self._flash(
                f"Dome {dome + 1} complete: {total:,.0f} labor-hours, "
                f"crew of {workers} → ~{days:,.0f} site-days @ 8 h")
            self._refresh_lights()
            self.stats_dirty = True

    # -- site actions ----------------------------------------------------------

    def _electrify_dome(self) -> str:
        cfg = self.model.config
        fr = self.model.floor_radius
        existing = {p["type"] for p in cfg.props}
        added = []

        def add(name, x, y, yaw=0.0):
            cfg.props.append({"type": name, "x": round(x, 2),
                              "y": round(y, 2), "yaw": yaw, "on": True})
            added.append(name)

        if "Battery Bank" not in existing:
            add("Battery Bank", -0.7, -fr * 0.62, 200.0)
        if "Charge Controller" not in existing:
            add("Charge Controller", 0.5, -fr * 0.66, 180.0)
        if "Power Meter LCD" not in existing:
            add("Power Meter LCD", 1.4, -fr * 0.60, 160.0)
        # Outlets around the outer wall (skipping the north doorway).
        outlet_r = fr - 0.55
        for az in (40, 90, 140, 220, 270, 320):
            a = math.radians(az)
            add("Wall Outlet", outlet_r * math.sin(a),
                outlet_r * math.cos(a), (az + 180.0) % 360.0)

        # A south-facing band of shell panels becomes solar.
        solar_set = 0
        for panel in self.model.panels:
            unit = (panel.centroid - self.model.sphere_center)
            unit = unit / np.linalg.norm(unit)
            if 0.2 < unit[2] < 0.7 and unit[1] < -0.35:
                cfg.panel_overrides[panel.key] = "Solar Panel"
                solar_set += 1

        self.energy.charge_kwh = max(self.energy.charge_kwh, 6.0)
        self._mark_changed()
        return (f"Electrified: battery kit, {added.count('Wall Outlet')} "
                f"outlets, {solar_set} solar panels")

    # -- overlays ----------------------------------------------------------

    def _update_overlay(self, name: str, surface: pygame.Surface) -> None:
        data = pygame.image.tobytes(surface, "RGBA", False)
        entry = self.overlay_textures.get(name)
        size = surface.get_size()
        if entry and entry["size"] == size:
            entry["texture"].write(data)
        else:
            if entry:
                entry["texture"].release()
            texture = self.ctx.texture(size, components=4, data=data)
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.overlay_textures[name] = {"texture": texture, "size": size}

    def _draw_texture(self, texture, size, x, y, flip=False) -> None:
        width, height = pygame.display.get_window_size()
        texture.use(location=0)
        self.overlay_program["u_texture"].value = 0
        self.overlay_program["u_flip"].value = 1 if flip else 0
        self.overlay_program["u_screen"].value = (float(width), float(height))
        self.overlay_program["u_rect"].value = (
            float(x), float(y), float(size[0]), float(size[1]))
        self.overlay_vao.render(moderngl.TRIANGLES)

    def _draw_overlay(self, name: str, x: float, y: float) -> None:
        entry = self.overlay_textures.get(name)
        if not entry:
            return
        self._draw_texture(entry["texture"], entry["size"], x, y)

    def _video_window_rect(self) -> tuple[float, float, int, int]:
        _, height = pygame.display.get_window_size()
        w, h = (VIDEO_WINDOW_SIZE_HELM if self.helm_active
                else VIDEO_WINDOW_SIZE)
        return 16, height - h - 64, w, h

    def _refresh_overlays(self) -> None:
        now = time.perf_counter()
        if self.flash_message and now > self.flash_until:
            self.flash_message = ""
            self.help_dirty = True

        if self.menu_dirty and self.menu_open:
            surface, hit_map = overlay_ui.render_menu(
                self.fonts, self.menu_items, self.menu_selected,
                self.menu_pages, self.menu_page)
            self.menu_hit_map = hit_map
            self._update_overlay("menu", surface)
            self.menu_dirty = False

        if "legend" not in self.overlay_textures:
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))

        if self.domes_open:
            rows = []
            for i, model in enumerate(self.domes):
                cfg = model.config
                mat = FRAME_MATERIALS[cfg.frame_material].name.split()[0]
                title = (f"{cfg.frequency}V {mat} "
                         f"r={cfg.radius:.0f}m — {cfg.default_panel}")
                if self.sim and self.sim["dome"] == i:
                    status = (f"BUILDING {self.sim['step']}"
                              f"/{len(self.dome_events_list[i])}")
                else:
                    status = "READY"
                load = (self.energy.load_by_dome[i]
                        if i < len(self.energy.load_by_dome) else 0.0)
                info = (f"{status} · {load:,.0f} W · "
                        f"{self.trackers[i].summary()}")
                rows.append({"title": title, "info": info})
            state = tuple((r["title"], r["info"]) for r in rows) + \
                (self.active_dome,)
            if getattr(self, "_domes_state", None) != state:
                surface, rects, add_rect = overlay_ui.render_dome_manager(
                    self.fonts, rows, self.active_dome)
                self.dome_rows_rects = rects
                self.dome_add_rect = add_rect
                self._update_overlay("domes", surface)
                self._domes_state = state
        if self.stats_dirty:
            self._update_overlay("stats", overlay_ui.render_stats(
                self.fonts, self.model.stats()))
            self.stats_dirty = False
        if self.help_dirty:
            width, _ = pygame.display.get_window_size()
            aim_text = ""
            if self.placing is not None:
                spot = "OK" if self.ghost_valid else "blocked"
                aim_text = (
                    f"Placing {self.placing.name} ({spot}) — click to "
                    "place, , . rotate, right-click/Esc finish"
                )
            elif self.helm_active:
                aim_text = (
                    "HELM ACTIVE — arrow keys pan/tilt, PgUp/PgDn or "
                    "wheel zoom, click or Esc to release"
                )
            elif self._aimed_prop() is not None:
                dome_idx, model, entry = self._aimed_prop()
                section = model.section_at(
                    float(model.origin[0]) + float(entry["x"]),
                    float(model.origin[1]) + float(entry["y"]))
                room = ""
                if section >= 0:
                    room = f" in S{section + 1} " + \
                        model.config.sections[section]
                prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                if prop is not None and prop.watts > 0:
                    state = "ON" if entry.get("on", True) else "OFF"
                    aim_text = (
                        f"Dome {dome_idx + 1} {entry['type']}{room} "
                        f"[{state}, {prop.watts:.0f} W] — click to "
                        "switch, DEL to pack"
                    )
                else:
                    aim_text = (
                        f"Dome {dome_idx + 1} prop: {entry['type']}"
                        f"{room} — click to pick up, DEL to pack"
                    )
            elif self.aiming_screen:
                aim_text = (
                    "Console screen — click to TAKE HELM of the "
                    "PTZ camera"
                )
            elif self.aimed_panel is not None:
                aim_text = (
                    f"Aimed panel: {self.aimed_panel.panel_type.name}  "
                    f"({self.aimed_distance:.1f} m)  "
                    "— click to swap, V to apply everywhere"
                )
            self._update_overlay("help", overlay_ui.render_help(
                self.fonts, max(200, width - 32), aim_text,
                self.flash_message))
            self.help_dirty = False

        if self.toolbar_dirty:
            buttons = [
                ("build", "Build", self.menu_open and self.menu_page == 0),
                ("rooms", "Rooms", self.menu_open and self.menu_page == 1),
                ("props", "Props", self.menu_open and self.menu_page == 2),
                ("lab", "Lab", self.menu_open and self.menu_page == 3),
                ("domes", "Domes", self.domes_open),
                ("bag", "Bag", self.inventory_open),
                ("cam", "Cam", self.helm_active),
                ("roof", "Roof", self.roof_hidden),
                ("pov", "POV", self.control_mode == "fp"),
                ("power", "Power", self.energy_open),
                ("keys", "Keys", self.legend_open),
                ("save", "Save", False),
                ("bom", "BOM", False),
            ]
            surface, rects = overlay_ui.render_toolbar(self.fonts, buttons)
            self._update_overlay("toolbar", surface)
            self.toolbar_rects = rects
            self.toolbar_dirty = False

        if self.inventory_dirty:
            surface, rects = overlay_ui.render_inventory(
                self.fonts, self.model.config.inventory,
                self.inventory_selected)
            self._update_overlay("inventory", surface)
            self.inventory_rects = rects
            self.inventory_dirty = False

        if self.energy_open:
            e = self.energy
            energy_state = (
                round(e.charge_kwh, 2), round(e.solar_watts),
                tuple(round(v) for v in e.load_by_dome),
                tuple(e.lights_by_dome), e.has_system, e.battery_empty,
                len(self._all_models()))
            if getattr(self, "_energy_state", None) != energy_state:
                self._update_overlay("energy", overlay_ui.render_energy(
                    self.fonts, e, len(self._all_models())))
                self._energy_state = energy_state

        if self.sim is not None:
            events = self._sim_events()
            step_idx = min(self.sim["step"], len(events) - 1)
            label = events[step_idx]["label"] if events else ""
            sim_state = (self.sim["dome"], self.sim["step"],
                         round(self.sim["elapsed"], 1),
                         round(self.sim["speed"], 2))
            if getattr(self, "_sim_state", None) != sim_state:
                width, _ = pygame.display.get_window_size()
                self._update_overlay(
                    "construction", overlay_ui.render_construction(
                        self.fonts, min(940, width - 40),
                        f"DOME {self.sim['dome'] + 1}", label,
                        self.sim["step"] + 1, len(events),
                        self.sim["elapsed"], self.sim["total"],
                        self.sim["speed"]))
                self._sim_state = sim_state

        # PTZ video window frame (readout changes while steering).
        _, _, vw, vh = self._video_window_rect()
        area_label, area_hint = self._ptz_watch_info()
        detect = self.trackers[self.active_dome].detect_text()
        osd_state = (round(self.ptz.pan, 1), round(self.ptz.tilt, 1),
                     round(self.ptz.fov, 1), self.helm_active,
                     self.aiming_screen, vw, area_label, area_hint,
                     detect, self.active_dome)
        if osd_state != self._osd_state:
            self._update_overlay("video_osd", overlay_ui.render_video_osd(
                self.fonts, (vw, vh), self.ptz.pan, self.ptz.tilt,
                self.ptz.fov, self.helm_active, self.aiming_screen,
                area_label, area_hint, detect,
                cam_label=f"CAM-{self.active_dome + 1:02d}"))
            self._osd_state = osd_state

    def _render_overlays(self) -> None:
        width, height = pygame.display.get_window_size()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)

        # The PTZ video window is always on screen, minimap-style.
        vx, vy, vw, vh = self._video_window_rect()
        self._draw_texture(self.ptz_texture, (vw, vh), vx, vy, flip=True)
        self._draw_overlay("video_osd", vx, vy)

        if self.sim is not None and "construction" in self.overlay_textures:
            entry = self.overlay_textures["construction"]
            self._draw_overlay("construction",
                               (width - entry["size"][0]) / 2, 12)
        if self.energy_open and "energy" in self.overlay_textures:
            entry = self.overlay_textures["energy"]
            ey = 84 if self.sim is not None else 12
            self._draw_overlay("energy",
                               (width - entry["size"][0]) / 2, ey)

        if self.show_hud:
            if self.legend_open or "legend" in self.overlay_textures:
                lx, ly = self._legend_origin()
                self._draw_overlay("legend", lx, ly)
            if self.domes_open and "domes" in self.overlay_textures:
                menu_w = (self.overlay_textures["menu"]["size"][0]
                          if self.menu_open and "menu"
                          in self.overlay_textures else 0)
                self.domes_origin = (16 + (menu_w + 12 if self.menu_open
                                           else 0), 16)
                self._draw_overlay("domes", *self.domes_origin)
            if self.menu_open and "menu" in self.overlay_textures:
                self._draw_overlay("menu", 16, 16)
            if "stats" in self.overlay_textures:
                entry = self.overlay_textures["stats"]
                self._draw_overlay(
                    "stats", width - entry["size"][0] - 16, 16)
            if "help" in self.overlay_textures:
                entry = self.overlay_textures["help"]
                self._draw_overlay(
                    "help", 16, height - entry["size"][1] - 12)
            if "toolbar" in self.overlay_textures:
                entry = self.overlay_textures["toolbar"]
                tx = (width - entry["size"][0]) / 2
                ty = height - entry["size"][1] - 62
                self.toolbar_origin = (tx, ty)
                self._draw_overlay("toolbar", tx, ty)
            if self.inventory_open and "inventory" in self.overlay_textures:
                entry = self.overlay_textures["inventory"]
                ix = width - entry["size"][0] - 16
                iy = height - entry["size"][1] - 110
                self.inventory_origin = (ix, iy)
                self._draw_overlay("inventory", ix, iy)
            if self.control_mode == "fp" \
                    and "crosshair" in self.overlay_textures:
                entry = self.overlay_textures["crosshair"]
                self._draw_overlay(
                    "crosshair",
                    width / 2 - entry["size"][0] / 2,
                    height / 2 - entry["size"][1] / 2)

        # Context menu always renders on top.
        if self.context_menu is not None \
                and "context" in self.overlay_textures:
            self._draw_overlay("context", *self.context_menu["origin"])

        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)

    # -- input -------------------------------------------------------------

    def _set_mouse_capture(self, enabled: bool) -> None:
        self.mouse_captured = enabled
        pygame.event.set_grab(enabled)
        pygame.mouse.set_visible(not enabled)
        pygame.mouse.get_rel()

    def process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self._recreate_window_target()

            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

            elif event.type == pygame.MOUSEMOTION:
                if self.control_mode == "orbit" and event.buttons[1]:
                    self.orbit_yaw += event.rel[0] * 0.008
                    self.orbit_pitch = float(np.clip(
                        self.orbit_pitch + event.rel[1] * 0.006,
                        0.12, 1.45))
                if self.context_menu is not None:
                    row = self._context_row_at(event.pos)
                    if row != self.context_menu["hover"]:
                        self.context_menu["hover"] = row
                        self._render_context_overlay()
                elif self.menu_open and not self.mouse_captured:
                    lx = event.pos[0] - 16
                    ly = event.pos[1] - 16
                    hover = None
                    for index, rect in self.menu_hit_map.get("rows", []):
                        if rect.collidepoint(lx, ly):
                            hover = index
                            break
                    if hover is not None and hover != self.menu_selected:
                        self.menu_selected = hover
                        self.menu_dirty = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):
                    self._on_mouse_button(event.button)

            elif event.type == pygame.MOUSEWHEEL:
                if self.helm_active:
                    self.ptz.fov = float(np.clip(
                        self.ptz.fov - event.y * 4.0, 12.0, 80.0))
                elif self.control_mode == "orbit":
                    self.orbit_dist = float(np.clip(
                        self.orbit_dist - event.y * 1.2, 2.5, 22.0))
                else:
                    self.camera.movement_speed = float(np.clip(
                        self.camera.movement_speed + event.y, 2.0, 30.0))

    def _ui_hit(self, pos) -> str | None:
        """Which UI region a screen point lands in, if any."""
        x, y = pos
        for bid, rect in self.toolbar_rects:
            ox, oy = self.toolbar_origin
            if rect.move(ox, oy).collidepoint(x, y):
                return f"toolbar:{bid}"
        if self.inventory_open:
            ox, oy = self.inventory_origin
            for i, rect in enumerate(self.inventory_rects):
                if rect.move(ox, oy).collidepoint(x, y):
                    return f"slot:{i}"
            entry = self.overlay_textures.get("inventory")
            if entry and pygame.Rect(
                    ox, oy, *entry["size"]).collidepoint(x, y):
                return "panel"
        if self.context_menu is not None:
            entry = self.overlay_textures.get("context")
            if entry and pygame.Rect(*self.context_menu["origin"],
                                     *entry["size"]).collidepoint(x, y):
                return "context"
        if self.domes_open:
            entry = self.overlay_textures.get("domes")
            if entry and pygame.Rect(*self.domes_origin,
                                     *entry["size"]).collidepoint(x, y):
                return "domes"
        entry = self.overlay_textures.get("legend")
        if entry and pygame.Rect(*self._legend_origin(),
                                 *entry["size"]).collidepoint(x, y):
            return "legend"
        if self.menu_open:
            entry = self.overlay_textures.get("menu")
            if entry and pygame.Rect(16, 16,
                                     *entry["size"]).collidepoint(x, y):
                return "menu"
        for name, origin in (("stats", None),
                             ("help", None), ("video_osd", None),
                             ("energy", None), ("construction", None)):
            entry = self.overlay_textures.get(name)
            if not entry:
                continue
            if name == "energy":
                if not self.energy_open:
                    continue
                width, _ = pygame.display.get_window_size()
                origin = ((width - entry["size"][0]) / 2,
                          84 if self.sim is not None else 12)
            if name == "construction":
                if self.sim is None:
                    continue
                width, _ = pygame.display.get_window_size()
                origin = ((width - entry["size"][0]) / 2, 12)
            if name == "stats":
                width, _ = pygame.display.get_window_size()
                origin = (width - entry["size"][0] - 16, 16)
            elif name == "help":
                _, height = pygame.display.get_window_size()
                origin = (16, height - entry["size"][1] - 12)
            elif name == "video_osd":
                vx, vy, _, _ = self._video_window_rect()
                origin = (vx, vy)
            if pygame.Rect(*origin, *entry["size"]).collidepoint(x, y):
                return name
        return None

    def _floor_click_point(self, origin, direction) -> np.ndarray | None:
        dz = float(direction[2])
        if dz >= -1e-5:
            return None
        for model in self.domes:
            fh = model.foundation.height
            if fh <= 0.0:
                continue
            t = (fh - float(origin[2])) / dz
            if t > 0.05:
                hit = origin + direction * t
                lx = hit[0] - float(model.origin[0])
                ly = hit[1] - float(model.origin[1])
                if math.hypot(lx, ly) <= model.floor_radius * 1.02:
                    return np.array([hit[0], hit[1], fh])
        t = (0.0 - float(origin[2])) / dz
        if t > 0.05:
            hit = origin + direction * t
            if abs(hit[0]) < 80 and abs(hit[1]) < 80:
                return np.array([hit[0], hit[1], 0.0])
        return None

    def _dome_at(self, x: float, y: float) -> int | None:
        for i, model in enumerate(self.domes):
            dx = x - float(model.origin[0])
            dy = y - float(model.origin[1])
            if math.hypot(dx, dy) <= model.floor_radius * 1.05:
                return i
        return None

    def _legend_origin(self) -> tuple[float, float]:
        _, height = pygame.display.get_window_size()
        entry = self.overlay_textures.get("legend")
        h = entry["size"][1] if entry else 300
        vx, vy, vw, _ = self._video_window_rect()
        return vx + vw + 10, height - h - 64

    # -- RuneScape-style context menu -------------------------------------

    def _open_context(self, entries: list, pos) -> None:
        """entries: list of (label, callable | None)."""
        if not entries:
            return
        self.context_menu = {
            "origin": (float(pos[0]), float(pos[1])),
            "entries": entries,
            "hover": -1,
        }
        self._render_context_overlay()

    def _render_context_overlay(self) -> None:
        surface, rects = overlay_ui.render_context_menu(
            self.fonts, [e[0] for e in self.context_menu["entries"]],
            self.context_menu["hover"])
        self.context_menu["rects"] = rects
        # Keep the popup inside the window.
        width, height = pygame.display.get_window_size()
        ox, oy = self.context_menu["origin"]
        ox = min(ox, width - surface.get_width() - 4)
        oy = min(oy, height - surface.get_height() - 4)
        self.context_menu["origin"] = (max(0, ox), max(0, oy))
        self._update_overlay("context", surface)

    def _context_row_at(self, pos) -> int:
        if not self.context_menu:
            return -1
        ox, oy = self.context_menu["origin"]
        for i, rect in enumerate(self.context_menu.get("rects", [])):
            if rect.move(int(ox), int(oy)).collidepoint(*pos):
                return i
        return -1

    def _world_context_entries(self) -> list:
        """Options for whatever is under the cursor right now."""
        entries: list = []
        origin, direction = self._interaction_ray()
        point = self._floor_click_point(origin, direction)

        def walk_here():
            if point is not None:
                self.walk_target = point
                self.pending_action = None

        aimed = self._aimed_prop()
        if aimed is not None:
            dome_idx, model, entry = aimed
            prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
            name = entry["type"]
            if prop is not None and prop.watts > 0:
                state = "off" if entry.get("on", True) else "on"
                entries.append((
                    f"Switch {state} {name}",
                    lambda: self._toggle_device(dome_idx, entry)))
            entries.append((
                f"Pick up {name}",
                lambda: self._pickup_prop(
                    dome_idx, model.config.props.index(entry))))
            if prop is not None:
                entries.append((
                    f"Examine {name}",
                    lambda: self._flash(
                        f"{name}: ${prop.cost:,.0f}, {prop.weight:.0f} kg"
                        + (f", {prop.watts:.0f} W" if prop.watts else ""))))

        if self.aiming_screen:
            sd = self.aimed_screen_dome
            entries.append((
                f"Take helm (dome {sd + 1} camera)",
                lambda: (self._select_dome(sd), self._set_helm(True))))
            tracker = self.trackers[sd]
            entries.append((
                "Examine vision system",
                lambda: self._flash(
                    f"Dome {sd + 1} vision: {tracker.summary()}")))

        if self.aimed_panel is not None:
            pd = self.aimed_panel_dome
            key = self.aimed_panel.key
            pmodel = self.domes[pd]
            pname = self.aimed_panel.panel_type.name

            def swap(step, pd=pd, key=key):
                new = self.domes[pd].cycle_panel(key, step)
                self._mark_changed(pd)
                self._flash(f"Panel -> {new}")

            entries.append(("Swap panel (next)", lambda: swap(1)))
            entries.append(("Swap panel (prev)", lambda: swap(-1)))
            entries.append((
                f"Apply {pname} to all",
                lambda: (pmodel.set_all_panels(pname),
                         self._mark_changed(pd),
                         self._flash(f"All panels set to {pname}"))))
            entries.append((
                "Examine panel",
                lambda: self._flash(
                    f"{pname}, {self.aimed_panel.area:.1f} m2 slot")))

        if point is not None:
            dome_idx = self._dome_at(float(point[0]), float(point[1]))
            entries.append(("Walk here", walk_here))
            if dome_idx is not None:
                model = self.domes[dome_idx]
                if dome_idx != self.active_dome:
                    entries.append((
                        f"Select dome {dome_idx + 1}",
                        lambda: self._select_dome(dome_idx)))
                entries.append((
                    f"Simulate construction (dome {dome_idx + 1})",
                    lambda: self.start_construction(dome_idx)))
                entries.append((
                    f"Examine dome {dome_idx + 1}",
                    lambda: self._flash(
                        f"Dome {dome_idx + 1}: "
                        f"{model.config.frequency}V r="
                        f"{model.config.radius:.0f} m — "
                        f"{self.trackers[dome_idx].summary()}")))
            else:
                import presets
                for pi, (pname_, pdata) in enumerate(presets.PRESETS):
                    entries.append((
                        f"Build here: {pname_}",
                        lambda pdata=pdata, point=point: self._flash(
                            self._add_dome(
                                pdata,
                                origin=(float(point[0]),
                                        float(point[1])),
                                simulate=True))))
        entries.append(("Cancel", None))
        return entries

    def _construction_context_entries(self) -> list:
        entries = []
        if self.sim:
            entries.append(("Add worker", lambda: self.sim.update(
                {"workers": min(self.sim["workers"] + 1, 8)})))
            entries.append(("Remove worker", lambda: self.sim.update(
                {"workers": max(self.sim["workers"] - 1, 1)})))
            entries.append(("Speed x2", lambda: self.sim.update(
                {"speed": min(self.sim["speed"] * 2, 32.0)})))
            entries.append(("Speed /2", lambda: self.sim.update(
                {"speed": max(self.sim["speed"] * 0.5, 0.1)})))

            def cancel():
                self.render_limits.pop(self.sim["dome"], None)
                self.sim = None
                self.worker_states = []
                self._flash("Construction cancelled")

            entries.append(("Cancel construction", cancel))
        entries.append(("Cancel", None))
        return entries

    def _menu_panel_click(self, pos, button: int) -> None:
        lx = pos[0] - 16
        ly = pos[1] - 16
        for page, rect in self.menu_hit_map.get("tabs", []):
            if rect.collidepoint(lx, ly):
                self.menu_page = page
                self.menu_items = self._build_menu_items()
                self.menu_selected = 1
                self.menu_dirty = True
                self.toolbar_dirty = True
                return
        for index, rect in self.menu_hit_map.get("rows", []):
            if rect.collidepoint(lx, ly):
                item = self.menu_items[index]
                self.menu_selected = index
                if item.activate is not None and button == 1:
                    self._flash(item.activate())
                elif item.change is not None:
                    item.change(1 if button == 1 else -1)
                self.menu_dirty = True
                return

    def _domes_panel_click(self, pos, button: int) -> None:
        lx = pos[0] - self.domes_origin[0]
        ly = pos[1] - self.domes_origin[1]
        for i, rect in enumerate(self.dome_rows_rects):
            if rect.collidepoint(lx, ly):
                if button == 1:
                    self._select_dome(i)
                else:
                    model = self.domes[i]
                    entries = [
                        (f"Select dome {i + 1}",
                         lambda i=i: self._select_dome(i)),
                        ("Walk to dome",
                         lambda m=model: setattr(
                             self, "walk_target", np.array(
                                 [float(m.origin[0]),
                                  float(m.origin[1])
                                  - m.floor_radius - 1.5,
                                  0.0]))),
                        ("Simulate construction",
                         lambda i=i: self.start_construction(i)),
                        ("Demolish dome",
                         lambda i=i: self._flash(self._remove_dome(i))),
                        ("Cancel", None),
                    ]
                    self._open_context(entries, pos)
                return
        if self.dome_add_rect is not None and \
                self.dome_add_rect.collidepoint(lx, ly):
            import presets
            entries = [
                (f"Place: {name}",
                 lambda data=data, name=name: self._begin_dome_placement(
                     name, data))
                for name, data in presets.PRESETS
            ]
            entries.append(("Place: Power Spoke (small)",
                            lambda: self._begin_dome_placement(
                                "Power Spoke", presets.SECOND_DOME)))
            entries.append(("Cancel", None))
            self._open_context(entries, pos)

    def _begin_dome_placement(self, name: str, data: dict) -> None:
        self.placing_dome = {"name": name, "data": data}
        self._flash(f"Placing {name} — click open ground to build "
                    "(Esc cancels)")

    def _place_ghost(self) -> None:
        if not self.ghost_valid or self.placing is None:
            return
        dome_idx = getattr(self, "ghost_dome", 0)
        target = self._all_models()[min(dome_idx,
                                        len(self._all_models()) - 1)]
        target.config.props.append({
            "type": self.placing.name,
            "x": round(float(self.ghost_pos[0])
                       - float(target.origin[0]), 3),
            "y": round(float(self.ghost_pos[1])
                       - float(target.origin[1]), 3),
            "yaw": round(self.ghost_yaw, 1),
            "on": True,
        })
        if self.placing_from_slot is not None:
            inv = self.model.config.inventory
            if self.placing_from_slot < len(inv):
                inv.pop(self.placing_from_slot)
            self.placing = None
            self.placing_from_slot = None
            self.inventory_selected = None
            self.inventory_dirty = True
            self._flash("Placed from backpack")
        else:
            self._flash(f"Placed {self.placing.name} — "
                        "click for another, Esc to finish")
        self._mark_changed(dome_idx)
        self.help_dirty = True

    def _aimed_prop(self) -> tuple[int, "DomeModel", dict] | None:
        if self.aimed_prop_index is None:
            return None
        dome_idx, i = self.aimed_prop_index
        models = self._all_models()
        if dome_idx >= len(models):
            return None
        model = models[dome_idx]
        if i >= len(model.config.props):
            return None
        return dome_idx, model, model.config.props[i]

    def _pickup_prop(self, dome_idx: int, index: int) -> None:
        inv = self.model.config.inventory
        if len(inv) >= 28:
            self._flash("Backpack is full")
            return
        models = self._all_models()
        if dome_idx >= len(models):
            return
        model = models[dome_idx]
        if index >= len(model.config.props):
            return
        entry = model.config.props.pop(index)
        inv.append(entry["type"])
        self._mark_changed(dome_idx)
        self.inventory_dirty = True
        self._flash(f"Picked up {entry['type']}")

    def _toggle_device(self, dome_idx: int, entry: dict) -> None:
        entry["on"] = not entry.get("on", True)
        model = self._all_models()[dome_idx]
        state = "ON" if entry["on"] else "OFF"
        connected = self.energy.device_connected(
            model, entry, self.energy.has_system)
        note = "" if connected else "  (no outlet in reach — unpowered)"
        self._flash(f"{entry['type']} switched {state}{note}")
        self._mark_changed(dome_idx)
        self._refresh_lights()

    def _drop_from_slot(self, slot: int) -> None:
        inv = self.model.config.inventory
        if slot >= len(inv):
            return
        # Drop at the avatar's feet, just in front, into whichever
        # dome the player is standing in (else the active one).
        px = float(self.camera.position[0]) + \
            math.sin(self.avatar_yaw) * 0.9
        py = float(self.camera.position[1]) + \
            math.cos(self.avatar_yaw) * 0.9
        dome_idx = self._dome_at(px, py)
        if dome_idx is None:
            dome_idx = self.active_dome
        target = self.domes[dome_idx]
        lx = px - float(target.origin[0])
        ly = py - float(target.origin[1])
        name = inv.pop(slot)
        target.config.props.append({
            "type": name, "x": round(lx, 3), "y": round(ly, 3),
            "yaw": round(math.degrees(self.avatar_yaw) + 180.0, 1) % 360.0,
            "on": True,
        })
        self._mark_changed(dome_idx)
        self.inventory_dirty = True
        self.inventory_selected = None
        self._flash(f"Dropped {name}")

    def _save_design(self) -> str:
        from pathlib import Path
        import materials
        data = {
            "domes": [
                {**model.config.to_dict(),
                 "origin": [float(model.origin[0]),
                            float(model.origin[1])]}
                for model in self.domes
            ],
            "custom_panels": dict(materials.CUSTOM_PANEL_DEFS),
            "active_dome": self.active_dome,
        }
        Path(DESIGN_FILE).write_text(json.dumps(data, indent=2),
                                     encoding="utf-8")
        return f"Saved {DESIGN_FILE} ({len(self.domes)} domes)"

    def _load_design(self) -> str:
        from pathlib import Path
        import materials
        path = Path(DESIGN_FILE)
        if not path.exists():
            return f"{DESIGN_FILE} not found"
        data = json.loads(path.read_text(encoding="utf-8"))

        for name, definition in dict(
                data.get("custom_panels", {})).items():
            materials.register_custom_panel(name, definition)

        while len(self.domes) > 1:
            self._remove_dome(len(self.domes) - 1)

        if "domes" in data:
            dome_list = data["domes"]
            self.domes[0].config = DomeConfig.from_dict(dome_list[0])
            org = dome_list[0].get("origin", [0.0, 0.0])
            self.domes[0].origin[:2] = (float(org[0]), float(org[1]))
            for extra in dome_list[1:]:
                self._add_dome(extra, origin=extra.get("origin"))
        else:
            # Older single/dual-dome save files.
            self.domes[0].config = DomeConfig.from_dict(data)
            if "second_dome" in data:
                org = data.get("second_dome_origin", [14.0, 0.0])
                self._add_dome(data["second_dome"], origin=org)

        self.active_dome = 0
        self.menu_items = self._build_menu_items()
        self._mark_changed(0)
        return f"Loaded {DESIGN_FILE} ({len(self.domes)} domes)"

    def _apply_preset(self, index: int) -> str:
        import presets
        name, data = presets.PRESETS[index % len(presets.PRESETS)]
        self.preset_index = index % len(presets.PRESETS)
        self.model.config = DomeConfig.from_dict(data)
        self.placing = None
        self.placing_from_slot = None
        self.inventory_selected = None
        self.menu_items = self._build_menu_items()
        self._mark_changed()
        self.inventory_dirty = True
        return f"Preset: {name}"

    def _toolbar_click(self, bid: str) -> None:
        if bid in ("build", "rooms", "props", "lab", "file"):
            page = {"build": 0, "rooms": 1, "props": 2, "lab": 3,
                    "file": 4}[bid]
            if self.menu_open and self.menu_page == page:
                self.menu_open = False
            else:
                self.menu_open = True
                self.menu_page = page
                self.menu_items = self._build_menu_items()
                self.menu_selected = 1
            self.menu_dirty = True
        elif bid == "bag":
            self.inventory_open = not self.inventory_open
            self.inventory_dirty = True
        elif bid == "roof":
            self.roof_hidden = not self.roof_hidden
            self._flash("Roof hidden" if self.roof_hidden
                        else "Roof visible")
        elif bid == "pov":
            self._set_control_mode(
                "fp" if self.control_mode == "orbit" else "orbit")
        elif bid == "view360":
            self._toggle_six_point()
        elif bid == "cam":
            if self.helm_active:
                self._set_helm(False)
            else:
                self._set_helm(True, remote=True)
        elif bid == "power":
            self.energy_open = not self.energy_open
        elif bid == "domes":
            self.domes_open = not self.domes_open
            self._domes_state = None
        elif bid == "keys":
            self.legend_open = not self.legend_open
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))
        elif bid == "save":
            self._flash(self._save_design())
        elif bid == "bom":
            from pathlib import Path
            Path(BOM_FILE).write_text(self.model.bom_text(),
                                      encoding="utf-8")
            self._flash(f"Exported {BOM_FILE}")
        self.toolbar_dirty = True

    def _toggle_six_point(self) -> None:
        self.six_point_enabled = not self.six_point_enabled
        if self.six_point_enabled and self.control_mode == "orbit":
            self._set_control_mode("fp")
        self.toolbar_dirty = True

    def _on_mouse_button(self, button: int) -> None:
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        mouse_pos = pygame.mouse.get_pos()

        # An open context menu captures the next click.
        if self.context_menu is not None:
            row = self._context_row_at(mouse_pos)
            entries = self.context_menu["entries"]
            self.context_menu = None
            if button == 1 and 0 <= row < len(entries) \
                    and entries[row][1] is not None:
                entries[row][1]()
            self.menu_dirty = True
            return

        # UI first (orbit mode has a live cursor).
        if not self.mouse_captured:
            hit = self._ui_hit(mouse_pos)
            if hit is not None:
                if hit.startswith("toolbar:"):
                    self._toolbar_click(hit.split(":", 1)[1])
                elif hit == "menu":
                    self._menu_panel_click(mouse_pos, button)
                elif hit == "domes":
                    self._domes_panel_click(mouse_pos, button)
                elif hit == "legend":
                    self.legend_open = not self.legend_open
                    self._update_overlay(
                        "legend", overlay_ui.render_legend(
                            self.fonts, not self.legend_open))
                elif hit == "construction" and button == 3:
                    self._open_context(
                        self._construction_context_entries(), mouse_pos)
                elif hit.startswith("slot:"):
                    slot = int(hit.split(":", 1)[1])
                    if slot < len(self.model.config.inventory):
                        if button == 3:
                            self._drop_from_slot(slot)
                        else:
                            name = self.model.config.inventory[slot]
                            self.placing = \
                                workshop.PROP_TYPE_BY_NAME[name]
                            self.placing_from_slot = slot
                            self.inventory_selected = slot
                            self.ghost_yaw = 0.0
                            self.inventory_dirty = True
                            self._flash(f"Placing {name} — click the "
                                        "floor, , . rotate")
                return

        if self.control_mode == "fp" and not self.mouse_captured:
            self._set_mouse_capture(True)
            self.escape_armed = False
            return

        # Placing a whole new dome: click open ground to build it.
        if self.placing_dome is not None:
            if button != 1:
                self.placing_dome = None
                self._flash("Dome placement cancelled")
                return
            origin, direction = self._interaction_ray()
            dz = float(direction[2])
            if dz < -1e-5:
                t = -float(origin[2]) / dz
                hit = origin + direction * t
                cfg_r = float(self.placing_dome["data"].get(
                    "radius", 5.0))
                pad = cfg_r * 1.2 + 2.0
                for model in self.domes:
                    d = math.hypot(hit[0] - float(model.origin[0]),
                                   hit[1] - float(model.origin[1]))
                    if d < pad + model.config.radius * 1.2:
                        self._flash("Too close to another dome")
                        return
                data = self.placing_dome["data"]
                self.placing_dome = None
                self._flash(self._add_dome(
                    data, origin=(float(hit[0]), float(hit[1])),
                    simulate=True))
            return

        if self.placing is not None:
            if button == 1:
                self._place_ghost()
            else:
                self.placing = None
                self.placing_from_slot = None
                self.inventory_selected = None
                self.inventory_dirty = True
                self._flash("Placement finished")
                self.help_dirty = True
            return

        if self.helm_active:
            self._set_helm(False)
            return

        if self.control_mode == "fp":
            # Classic first-person interactions at the crosshair.
            aimed = self._aimed_prop()
            if self.aiming_screen and self.screen_distance < HELM_RANGE:
                self._select_dome(self.aimed_screen_dome)
                self._set_helm(True)
            elif aimed is not None and button == 1:
                dome_idx, model, entry = aimed
                prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                if prop is not None and prop.watts > 0:
                    self._toggle_device(dome_idx, entry)
                else:
                    self._pickup_prop(dome_idx,
                                      self.aimed_prop_index[1])
            elif self.aimed_panel is not None:
                pmodel = self._all_models()[self.aimed_panel_dome]
                step = 1 if button == 1 else -1
                name = pmodel.cycle_panel(self.aimed_panel.key, step)
                self._mark_changed(self.aimed_panel_dome)
                self._flash(f"Panel -> {name}")
            return

        # Orbit mode: RuneScape-style world clicks.
        origin, direction = self._interaction_ray()
        if shift and self.aimed_panel is not None:
            pmodel = self._all_models()[self.aimed_panel_dome]
            step = 1 if button == 1 else -1
            name = pmodel.cycle_panel(self.aimed_panel.key, step)
            self._mark_changed(self.aimed_panel_dome)
            self._flash(f"Panel -> {name}")
            return
        if button == 3:
            # Right-click: RuneScape "Choose Option" for the world.
            self._open_context(self._world_context_entries(), mouse_pos)
            return
        if button != 1:
            return

        player = self.camera.position.astype(np.float64)
        if self.aiming_screen:
            self._select_dome(self.aimed_screen_dome)
            if self.screen_distance_from_player() < HELM_RANGE:
                self._set_helm(True)
            else:
                target = self.console["screen_center"].copy()
                target[1] -= 1.3
                target[2] = self.model.foundation.height
                self.walk_target = target
                self.pending_action = {"kind": "helm"}
                self._flash("Walking to the console...")
            return
        aimed = self._aimed_prop()
        if aimed is not None:
            dome_idx, model, entry = aimed
            wx = float(model.origin[0]) + float(entry["x"])
            wy = float(model.origin[1]) + float(entry["y"])
            dist = math.hypot(wx - player[0], wy - player[1])
            prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
            is_device = prop is not None and prop.watts > 0
            if dist < 2.2:
                if is_device:
                    self._toggle_device(dome_idx, entry)
                else:
                    self._pickup_prop(dome_idx,
                                      self.aimed_prop_index[1])
            else:
                fh = model.foundation.height
                self.walk_target = np.array([wx, wy, fh])
                kind = "toggle" if is_device else "pickup"
                self.pending_action = {"kind": kind, "entry": entry,
                                       "dome": dome_idx}
                verb = "switch" if is_device else "pick up"
                self._flash(f"Walking to {verb} {entry['type']}...")
            return
        point = self._floor_click_point(origin, direction)
        if point is not None:
            self.walk_target = point
            self.pending_action = None

    def _execute_pending(self) -> None:
        action = self.pending_action
        self.pending_action = None
        if not action:
            return
        if action["kind"] == "helm":
            if self.screen_distance_from_player() < HELM_RANGE + 0.4:
                self._set_helm(True)
            return
        dome_idx = action.get("dome", 0)
        models = self._all_models()
        if dome_idx >= len(models):
            return
        model = models[dome_idx]
        entry = action["entry"]
        for i, existing in enumerate(model.config.props):
            if existing is entry:
                if action["kind"] == "pickup":
                    self._pickup_prop(dome_idx, i)
                elif action["kind"] == "toggle":
                    self._toggle_device(dome_idx, entry)
                break

    def screen_distance_from_player(self) -> float:
        if not self.console:
            return 1e9
        gap = self.camera.position.astype(np.float64) - \
            self.console["screen_center"]
        return float(np.linalg.norm(gap))

    def _set_helm(self, active: bool, remote: bool = False) -> None:
        if active == self.helm_active:
            return
        self.helm_active = active
        self.helm_remote = remote if active else False
        if active:
            self.menu_open = False
            if remote:
                self._flash("CAMERA CONTROL — arrows steer, "
                            "C or Esc to release")
            else:
                self._flash("HELM TAKEN — arrow keys steer the camera")
        else:
            self._flash("Helm released")
        self.menu_dirty = True
        self.help_dirty = True
        self.toolbar_dirty = True

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.context_menu is not None:
                self.context_menu = None
            elif self.placing_dome is not None:
                self.placing_dome = None
                self._flash("Dome placement cancelled")
            elif self.placing is not None:
                self.placing = None
                self._flash("Placement finished")
                self.help_dirty = True
            elif self.helm_active:
                self._set_helm(False)
            elif self.mouse_captured:
                self._set_mouse_capture(False)
                self.escape_armed = True
            elif self.escape_armed:
                self.running = False
            else:
                self.escape_armed = True
                self._flash("Press Esc again to quit")
            return

        if key == pygame.K_m:
            self.menu_open = not self.menu_open
            self.menu_dirty = True
            self.toolbar_dirty = True
            return

        if key in (pygame.K_COMMA, pygame.K_PERIOD) and self.placing:
            self.ghost_yaw += 15.0 if key == pygame.K_PERIOD else -15.0
            self.ghost_yaw %= 360.0
            return

        if key in (pygame.K_DELETE, pygame.K_BACKSPACE) \
                and self.aimed_prop_index is not None:
            self._pickup_prop(self.aimed_prop_index[0],
                              self.aimed_prop_index[1])
            return

        if self.menu_open and not self.helm_active:
            page_keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                         pygame.K_4: 3, pygame.K_5: 4}
            if key in page_keys and page_keys[key] < len(self.menu_pages):
                self.menu_page = page_keys[key]
                self.menu_items = self._build_menu_items()
                self.menu_selected = 1
                self.menu_dirty = True
                self.toolbar_dirty = True
                return

        if key == pygame.K_k:
            self.legend_open = not self.legend_open
            self._update_overlay("legend", overlay_ui.render_legend(
                self.fonts, not self.legend_open))
        elif key == pygame.K_TAB:
            self._toggle_six_point()
        elif key == pygame.K_f:
            if self.control_mode == "fp":
                self.camera.fly_mode = not self.camera.fly_mode
        elif key == pygame.K_p:
            self._set_control_mode(
                "fp" if self.control_mode == "orbit" else "orbit")
        elif key == pygame.K_r:
            self.roof_hidden = not self.roof_hidden
            self.toolbar_dirty = True
            self._flash("Roof hidden" if self.roof_hidden
                        else "Roof visible")
        elif key in (pygame.K_b, pygame.K_i):
            self.inventory_open = not self.inventory_open
            self.inventory_dirty = True
            self.toolbar_dirty = True
        elif key == pygame.K_c:
            if self.helm_active:
                self._set_helm(False)
            else:
                self._set_helm(True, remote=True)
        elif key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif key == pygame.K_h:
            self.show_hud = not self.show_hud
        elif key == pygame.K_z:
            self.six_point_spin_speed -= 0.15
        elif key == pygame.K_x:
            self.six_point_spin_speed += 0.15
        elif key == pygame.K_v and self.aimed_panel is not None:
            pmodel = self._all_models()[self.aimed_panel_dome]
            name = self.aimed_panel.panel_type.name
            pmodel.set_all_panels(name)
            self._mark_changed(self.aimed_panel_dome)
            self._flash(f"All panels set to {name}")
        elif key == pygame.K_n:
            self.energy_open = not self.energy_open
            self.toolbar_dirty = True
        elif key == pygame.K_LEFTBRACKET and self.sim:
            self.sim["speed"] = max(self.sim["speed"] * 0.5, 0.1)
        elif key == pygame.K_RIGHTBRACKET and self.sim:
            self.sim["speed"] = min(self.sim["speed"] * 2.0, 32.0)
        elif key == pygame.K_F5:
            self._flash(self._save_design())
        elif key == pygame.K_F9:
            self._flash(self._load_design())
        elif key == pygame.K_F6:
            from pathlib import Path
            Path(BOM_FILE).write_text(
                self.model.bom_text(), encoding="utf-8")
            self._flash(f"Exported {BOM_FILE}")

    # -- cameras and rays ------------------------------------------------------

    def _orbit_eye_target(self) -> tuple[np.ndarray, np.ndarray]:
        target = self.camera.position.astype(np.float32) + \
            np.array([0.0, 0.0, 0.35], dtype=np.float32)
        cp = math.cos(self.orbit_pitch)
        offset = np.array([
            math.sin(self.orbit_yaw) * cp,
            math.cos(self.orbit_yaw) * cp,
            math.sin(self.orbit_pitch),
        ], dtype=np.float32)
        eye = target + offset * self.orbit_dist
        eye[2] = max(eye[2], 0.5)
        return eye, target

    def _main_view_proj(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """View, projection, and eye of the main (non-six-point) camera."""
        width, height = pygame.display.get_window_size()
        aspect = width / max(1, height)
        if self.control_mode == "orbit":
            eye, target = self._orbit_eye_target()
            view = look_at_matrix(eye, target,
                                  np.array([0.0, 0.0, 1.0],
                                           dtype=np.float32))
            projection = perspective_matrix(60.0, aspect, NEAR_PLANE,
                                            FAR_PLANE)
            return view, projection, eye
        forward, _, up = self.camera.basis()
        view = look_at_matrix(
            self.camera.position, self.camera.position + forward, up)
        projection = perspective_matrix(78.0, aspect, NEAR_PLANE, FAR_PLANE)
        return view, projection, self.camera.position

    def _mouse_ray(self) -> tuple[np.ndarray, np.ndarray]:
        """World ray under the mouse cursor (orbit mode picking)."""
        width, height = pygame.display.get_window_size()
        mx, my = pygame.mouse.get_pos()
        ndc_x = 2.0 * mx / max(1, width) - 1.0
        ndc_y = 1.0 - 2.0 * my / max(1, height)
        view, projection, eye = self._main_view_proj()
        inv = np.linalg.inv(projection @ view)
        near = inv @ np.array([ndc_x, ndc_y, -1.0, 1.0], dtype=np.float64)
        far = inv @ np.array([ndc_x, ndc_y, 1.0, 1.0], dtype=np.float64)
        near = near[:3] / near[3]
        far = far[:3] / far[3]
        return near, normalize(far - near).astype(np.float64)

    def _interaction_ray(self) -> tuple[np.ndarray, np.ndarray]:
        """The ray used for hover/click picking."""
        if self.control_mode == "orbit" and not self.six_point_enabled \
                and not self.mouse_captured:
            return self._mouse_ray()
        forward, _, _ = self.camera.basis()
        return (self.camera.position.astype(np.float64),
                forward.astype(np.float64))

    def _set_control_mode(self, mode: str) -> None:
        if mode == self.control_mode:
            return
        self.control_mode = mode
        self.walk_target = None
        self.pending_action = None
        if mode == "fp":
            self.camera.yaw = self.orbit_yaw + math.pi
            self.camera.pitch = 0.0
            self._set_mouse_capture(True)
            self._flash("First-person view — mouse look, WASD")
        else:
            self.camera.fly_mode = False
            self.orbit_yaw = self.camera.yaw + math.pi
            self._set_mouse_capture(False)
            self._flash("Overhead view — click the ground to walk")
        self.toolbar_dirty = True
        self.help_dirty = True

    # -- simulation ----------------------------------------------------------

    def _pick_prop(self, origin, direction) \
            -> tuple[float, tuple[int, int] | None]:
        """Ray vs vertical bounding cylinder of every placed prop on
        the site. Returns (distance, (dome_index, prop_index))."""
        best_t, best_hit = 1e9, None
        dx, dy, dz = float(direction[0]), float(direction[1]), \
            float(direction[2])
        a = dx * dx + dy * dy
        for dome_idx, model in enumerate(self._all_models()):
            fh = model.foundation.height
            mox, moy = float(model.origin[0]), float(model.origin[1])
            for i, entry in enumerate(model.config.props):
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None:
                    continue
                cx = mox + float(entry["x"])
                cy = moy + float(entry["y"])
                r = prop.pick_radius
                z0, z1 = fh, fh + prop.pick_height
                ox = float(origin[0]) - cx
                oy = float(origin[1]) - cy

                if a > 1e-9:
                    bq = ox * dx + oy * dy
                    c = ox * ox + oy * oy - r * r
                    disc = bq * bq - a * c
                    if disc >= 0.0:
                        sq = math.sqrt(disc)
                        for t in ((-bq - sq) / a, (-bq + sq) / a):
                            if 0.1 < t < best_t:
                                z = float(origin[2]) + dz * t
                                if z0 <= z <= z1:
                                    best_t = t
                                    best_hit = (dome_idx, i)
                                    break
                if abs(dz) > 1e-6:
                    t = (z1 - float(origin[2])) / dz
                    if 0.1 < t < best_t:
                        px = ox + dx * t
                        py = oy + dy * t
                        if px * px + py * py <= r * r:
                            best_t = t
                            best_hit = (dome_idx, i)
        return best_t, best_hit

    def ground_height(self, x: float, y: float) -> float:
        height = 0.0
        for model in self._all_models():
            foundation = model.foundation
            if foundation.name == "Bare Ground":
                continue
            f_radius = model.config.radius * model.config.foundation_scale
            dx = x - float(model.origin[0])
            dy = y - float(model.origin[1])
            if dx * dx + dy * dy <= f_radius * f_radius:
                height = max(height, foundation.height)
        return height

    def update(self, delta_time: float) -> None:
        if self.mouse_captured and self.control_mode == "fp" \
                and not self.smoke_frames:
            dx, dy = pygame.mouse.get_rel()
            self.camera.yaw += dx * self.camera.mouse_sensitivity
            self.camera.pitch -= dy * self.camera.mouse_sensitivity
            self.camera.pitch = float(np.clip(
                self.camera.pitch, -math.radians(89.0), math.radians(89.0)))

        keys = pygame.key.get_pressed()

        if self.control_mode == "orbit":
            # RuneScape-style camera: arrow keys orbit around the player.
            if not self.helm_active:
                if keys[pygame.K_LEFT]:
                    self.orbit_yaw -= 1.8 * delta_time
                if keys[pygame.K_RIGHT]:
                    self.orbit_yaw += 1.8 * delta_time
                if keys[pygame.K_UP]:
                    self.orbit_pitch += 1.1 * delta_time
                if keys[pygame.K_DOWN]:
                    self.orbit_pitch -= 1.1 * delta_time
                self.orbit_pitch = float(np.clip(
                    self.orbit_pitch, 0.12, 1.45))
            forward = normalize(np.array(
                [-math.sin(self.orbit_yaw), -math.cos(self.orbit_yaw),
                 0.0], dtype=np.float32))
            up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            right = normalize(np.cross(forward, up))
        else:
            forward, right, up = self.camera.basis()
            if not self.camera.fly_mode:
                forward = normalize(np.array(
                    [forward[0], forward[1], 0.0], dtype=np.float32))
                right = normalize(np.array(
                    [right[0], right[1], 0.0], dtype=np.float32))
                up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # WASD moves only in first-person; orbit mode is click-to-walk.
        movement = np.zeros(3, dtype=np.float32)
        if self.control_mode == "fp":
            if keys[pygame.K_w]:
                movement += forward
            if keys[pygame.K_s]:
                movement -= forward
            if keys[pygame.K_d]:
                movement += right
            if keys[pygame.K_a]:
                movement -= right
        if self.control_mode == "fp" and self.camera.fly_mode:
            if keys[pygame.K_SPACE]:
                movement += up
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                movement -= up

        if self.control_mode == "fp":
            if keys[pygame.K_q]:
                self.camera.roll -= delta_time * 0.8
            if keys[pygame.K_e]:
                self.camera.roll += delta_time * 0.8

        length = float(np.linalg.norm(movement))
        if length > 1e-6:
            movement /= length
            speed = self.camera.movement_speed
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                speed *= self.camera.sprint_multiplier
            self.camera.position += movement * speed * delta_time
            self.walk_target = None
            self.pending_action = None
            self.avatar_yaw = math.atan2(
                float(movement[0]), float(movement[1]))

        # Click-to-move walking.
        if self.walk_target is not None:
            dx = float(self.walk_target[0] - self.camera.position[0])
            dy = float(self.walk_target[1] - self.camera.position[1])
            dist = math.hypot(dx, dy)
            if dist < 0.15:
                self.walk_target = None
                self._execute_pending()
            else:
                step = min(self.camera.movement_speed * delta_time, dist)
                self.camera.position[0] += dx / dist * step
                self.camera.position[1] += dy / dist * step
                self.avatar_yaw = math.atan2(dx, dy)

        if not (self.control_mode == "fp" and self.camera.fly_mode):
            self.camera.position[2] = PLAYER_HEIGHT + self.ground_height(
                float(self.camera.position[0]),
                float(self.camera.position[1]))

        self.camera.roll += self.six_point_spin_speed * delta_time

        # PTZ helm steering (held keys, like a real joystick controller).
        if self.helm_active:
            if keys[pygame.K_LEFT]:
                self.ptz.pan -= self.ptz.pan_rate * delta_time
            if keys[pygame.K_RIGHT]:
                self.ptz.pan += self.ptz.pan_rate * delta_time
            if keys[pygame.K_UP]:
                self.ptz.tilt += self.ptz.tilt_rate * delta_time
            if keys[pygame.K_DOWN]:
                self.ptz.tilt -= self.ptz.tilt_rate * delta_time
            if keys[pygame.K_PAGEUP]:
                self.ptz.fov -= self.ptz.zoom_rate * delta_time
            if keys[pygame.K_PAGEDOWN]:
                self.ptz.fov += self.ptz.zoom_rate * delta_time
            self.ptz.pan %= 360.0
            self.ptz.tilt = float(np.clip(self.ptz.tilt, 0.0, 100.0))
            self.ptz.fov = float(np.clip(self.ptz.fov, 12.0, 80.0))

            # Walking away releases the helm — unless controlling
            # remotely via the C hotkey.
            if not self.helm_remote:
                gap = self.camera.position.astype(np.float64) - \
                    self.console["screen_center"]
                if float(np.linalg.norm(gap)) > HELM_LEASH:
                    self._set_helm(False)

        while self.rebuild_queue:
            self._rebuild_dome(next(iter(self.rebuild_queue)))

        # Construction crew and the shared power system.
        self._update_construction(delta_time)
        was_empty = self.energy.battery_empty
        self.energy.update(self._all_models(), delta_time)
        if self.energy.battery_empty != was_empty:
            self._refresh_lights()
            self._flash("BATTERY EMPTY — loads shed"
                        if self.energy.battery_empty
                        else "Battery recovering — loads restored")

        # Every dome's vision system samples what its camera can see.
        for i, model in enumerate(self.domes):
            self.trackers[i].update(
                model, self.ptzs[i], self.consoles[i],
                self.camera.position, delta_time)

        # Hover/crosshair picking: console screen, then props, then panels.
        origin, direction = self._interaction_ray()

        screen_t = None
        for ci, console in enumerate(self.consoles):
            if not console:
                continue
            bl, br, tr, tl = console["screen_corners"]
            for tri in ((bl, br, tr), (bl, tr, tl)):
                hit = ray_triangle(origin, direction, *tri)
                if hit is not None and (screen_t is None
                                        or hit < screen_t):
                    screen_t = hit
                    self.aimed_screen_dome = ci

        prop_t, prop_index = self._pick_prop(origin, direction)
        panel, distance = None, 1e9
        self.aimed_panel_dome = 0
        for di, dmodel in enumerate(self.domes):
            p, d = dmodel.pick_panel(origin, direction)
            if p is not None and d < distance:
                panel, distance = p, d
                self.aimed_panel_dome = di

        candidates = []
        if screen_t is not None:
            candidates.append((screen_t, "screen"))
        if prop_index is not None:
            candidates.append((prop_t, "prop"))
        if panel is not None:
            candidates.append((distance, "panel"))
        winner = min(candidates)[1] if candidates else None

        aiming_screen = winner == "screen"
        aimed_prop = prop_index if winner == "prop" else None
        if winner != "panel":
            panel = None

        previous = (
            self.aimed_panel.key if self.aimed_panel else None,
            self.aimed_panel.panel_type.name if self.aimed_panel else None,
            self.aiming_screen,
            self.aimed_prop_index,
        )
        self.aimed_panel = panel
        self.aimed_distance = distance if panel else 0.0
        self.aiming_screen = aiming_screen
        self.screen_distance = screen_t if screen_t is not None else 1e9
        self.aimed_prop_index = aimed_prop
        current = (
            panel.key if panel else None,
            panel.panel_type.name if panel else None,
            aiming_screen,
            aimed_prop,
        )
        if current != previous:
            self.help_dirty = True

        # Placement ghost follows the crosshair's floor intersection,
        # snapping to whichever dome's floor the ray lands on.
        if self.placing is not None:
            dz = float(direction[2])
            self.ghost_valid = False
            self.ghost_dome = 0
            if dz < -1e-4:
                fallback = None
                for dome_idx, model in enumerate(self._all_models()):
                    fh = model.foundation.height
                    t = (fh - float(origin[2])) / dz
                    if not (0.1 < t < 80.0):
                        continue
                    hit = origin + direction * t
                    if fallback is None:
                        fallback = (hit, fh)
                    lx = hit[0] - float(model.origin[0])
                    ly = hit[1] - float(model.origin[1])
                    limit = model.floor_radius - \
                        max(0.3, self.placing.pick_radius * 0.8)
                    if math.hypot(lx, ly) <= limit:
                        self.ghost_pos = hit.copy()
                        self.ghost_pos[2] = fh
                        self.ghost_valid = True
                        self.ghost_dome = dome_idx
                        break
                if not self.ghost_valid and fallback is not None:
                    self.ghost_pos = fallback[0].copy()
                    self.ghost_pos[2] = fallback[1]

    # -- rendering -----------------------------------------------------------

    def _set_uniform(self, program, name, value) -> None:
        try:
            program[name].value = value
        except KeyError:
            pass

    def _render_scene(self, framebuffer, view, projection,
                      camera_pos=None, draw_monitor=True,
                      roof_cut=None, draw_avatar=False,
                      exposure=1.0, headlamp=0.0) -> None:
        if camera_pos is None:
            camera_pos = self.camera.position
        if roof_cut is None:
            roof_cut = 1e9
        framebuffer.use()
        self.ctx.viewport = (0, 0, *framebuffer.size)
        framebuffer.clear(*self.sky_color, 1.0, depth=1.0)

        mvp = projection @ view
        identity = np.eye(4, dtype=np.float32)
        self.scene_program["u_mvp"].write(
            np.ascontiguousarray(mvp.T).tobytes())
        self.scene_program["u_model"].write(identity.tobytes())
        self._set_uniform(self.scene_program, "u_camera_position",
                          tuple(map(float, camera_pos)))
        self._set_uniform(self.scene_program, "u_light_direction",
                          (-0.40, -0.25, -0.90))
        self._set_uniform(self.scene_program, "u_sky_color", self.sky_color)
        self._set_uniform(self.scene_program, "u_ghost", 0.0)
        self._set_uniform(self.scene_program, "u_cut_z", float(roof_cut))
        self._set_uniform(self.scene_program, "u_exposure", float(exposure))
        self._set_uniform(self.scene_program, "u_headlamp", float(headlamp))
        self._set_uniform(self.scene_program, "u_light_count",
                          self.light_count)
        try:
            self.scene_program["u_light_positions"].write(
                self.light_array.tobytes())
        except KeyError:
            pass

        # Opaque pass (construction sims render a prefix of the mesh).
        def draw_pass(kind: str) -> None:
            vao = self.env_buffers.get(f"{kind}_vao")
            if vao is not None:
                vao.render(moderngl.TRIANGLES)
            for dome_idx, buffers in enumerate(self.dome_buffers_list):
                if not buffers:
                    continue
                vao = buffers.get(f"{kind}_vao")
                if vao is None:
                    continue
                limit = self.render_limits.get(dome_idx)
                if limit is None:
                    vao.render(moderngl.TRIANGLES)
                else:
                    count = limit[0] if kind == "opaque" else limit[1]
                    if count > 0:
                        vao.render(moderngl.TRIANGLES, vertices=count)

        draw_pass("opaque")

        # Construction crew on site.
        if self.sim is not None:
            vao = self.worker_buffers.get("opaque_vao")
            for worker in self.worker_states:
                a = -worker["yaw"]
                c, s = math.cos(a), math.sin(a)
                worker_matrix = np.array([
                    [c, -s, 0.0, float(worker["pos"][0])],
                    [s, c, 0.0, float(worker["pos"][1])],
                    [0.0, 0.0, 1.0, float(worker["pos"][2])],
                    [0.0, 0.0, 0.0, 1.0],
                ], dtype=np.float32)
                self.scene_program["u_model"].write(
                    np.ascontiguousarray(worker_matrix.T).tobytes())
                if vao is not None:
                    vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())

        # Third-person avatar (in overhead mode and on the PTZ feed).
        if draw_avatar:
            ax, ay = float(self.camera.position[0]), \
                float(self.camera.position[1])
            az = float(self.camera.position[2]) - PLAYER_HEIGHT
            a = -self.avatar_yaw
            c, s = math.cos(a), math.sin(a)
            avatar_matrix = np.array([
                [c, -s, 0.0, ax],
                [s, c, 0.0, ay],
                [0.0, 0.0, 1.0, az],
                [0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)
            self.scene_program["u_model"].write(
                np.ascontiguousarray(avatar_matrix.T).tobytes())
            vao = self.avatar_buffers.get("opaque_vao")
            if vao is not None:
                vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())

        # In-world monitors, each showing its own dome's live feed.
        # A dome's monitor is skipped inside that dome's PTZ pass (a
        # texture cannot be sampled while it is the render target).
        if draw_monitor is not False:
            skip_idx = draw_monitor if isinstance(draw_monitor, int) \
                and not isinstance(draw_monitor, bool) else -1
            self.screen_program["u_mvp"].write(
                np.ascontiguousarray(mvp.T).tobytes())
            for mi, monitor in enumerate(self.monitors):
                if mi == skip_idx or not self.consoles[mi]:
                    continue
                self.feeds[mi]["texture"].use(location=0)
                self.screen_program["u_texture"].value = 0
                monitor["vao"].render(moderngl.TRIANGLES)

        # Transparent pass (glass, sheeting, films).
        self.ctx.enable(moderngl.BLEND)
        framebuffer.depth_mask = False
        draw_pass("transparent")

        # Placement ghost preview (green = valid spot, red = invalid).
        if self.placing is not None:
            ghost = self._ghost_buffers(self.placing.name)
            a = -math.radians(self.ghost_yaw)
            c, s = math.cos(a), math.sin(a)
            model_matrix = np.array([
                [c, -s, 0.0, float(self.ghost_pos[0])],
                [s, c, 0.0, float(self.ghost_pos[1])],
                [0.0, 0.0, 1.0, float(self.ghost_pos[2])],
                [0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)
            self.scene_program["u_model"].write(
                np.ascontiguousarray(model_matrix.T).tobytes())
            self._set_uniform(self.scene_program, "u_ghost",
                              1.0 if self.ghost_valid else 2.0)
            for key in ("opaque_vao", "transparent_vao"):
                vao = ghost.get(key)
                if vao is not None:
                    vao.render(moderngl.TRIANGLES)
            self.scene_program["u_model"].write(identity.tobytes())
            self._set_uniform(self.scene_program, "u_ghost", 0.0)

        # Click-to-move destination marker (spinning yellow beacon).
        if self.walk_target is not None and draw_avatar:
            tx, ty, tz = map(float, self.walk_target)
            spin = time.perf_counter() * 2.5
            r = 0.28
            verts = []
            for k in (0, 1):
                a0 = spin + k * math.pi * 0.5
                dx, dy = math.cos(a0) * r, math.sin(a0) * r
                verts.extend([
                    tx - dx, ty - dy, tz + 0.02,
                    tx + dx, ty + dy, tz + 0.02,
                    tx, ty, tz + 0.85,
                ])
            self.marker_vbo.write(
                np.asarray(verts, dtype=np.float32).tobytes())
            self.highlight_program["u_mvp"].write(
                np.ascontiguousarray((projection @ view).T).tobytes())
            pulse = 0.5 + 0.25 * math.sin(time.perf_counter() * 6.0)
            self.highlight_program["u_color"].value = (
                1.0, 0.85, 0.15, pulse)
            self.marker_vao.render(moderngl.TRIANGLES)

        # Aimed-panel highlight.
        if self.aimed_panel is not None:
            tri = self.aimed_panel.world_verts.astype(np.float32)
            outward = normalize(
                (self.aimed_panel.centroid
                 - self.model.sphere_center).astype(np.float32))
            to_camera = normalize(
                np.asarray(camera_pos, dtype=np.float32)
                - tri.mean(axis=0).astype(np.float32))
            tri = tri + to_camera * 0.02 + outward * 0.01
            self.highlight_vbo.write(tri.astype(np.float32).tobytes())
            self.highlight_program["u_mvp"].write(
                np.ascontiguousarray(mvp.T).tobytes())
            pulse = 0.22 + 0.12 * math.sin(time.perf_counter() * 5.0)
            self.highlight_program["u_color"].value = (
                1.0, 0.72, 0.20, pulse)
            self.highlight_vao.render(moderngl.TRIANGLES)

        framebuffer.depth_mask = True
        self.ctx.disable(moderngl.BLEND)

    def _ghost_buffers(self, name: str) -> dict:
        if name not in self.ghost_cache:
            self.ghost_cache[name] = self._upload_mesh(build_prop_mesh(name))
        return self.ghost_cache[name]

    def _ptz_watch_info(self) -> tuple[str, str]:
        """Which section the camera center is watching, plus the room's
        expected-activity hint for the vision system."""
        if not self.console:
            return "", ""
        eye = self.console["ptz_eye"]
        forward, _ = self.ptz.basis()
        dz = float(forward[2])
        if dz > -0.06:
            return "HORIZON", "camera aimed above the floor"
        fh = self.model.foundation.height
        t = (fh - float(eye[2])) / dz
        point = eye + forward.astype(np.float64) * t
        section = self.model.section_at(float(point[0]), float(point[1]))
        if section < 0:
            return "PERIMETER", "outside the dome floor"
        room_name = self.model.config.sections[section]
        room = ROOM_TYPE_BY_NAME.get(room_name)
        label = f"S{section + 1} {room_name.upper()}"
        hint = room.hint if room else ""
        return label, hint

    def _render_feed(self, idx: int) -> None:
        console = self.consoles[idx]
        if not console:
            return
        eye = console["ptz_eye"].astype(np.float32)
        forward, up = self.ptzs[idx].basis()
        view = look_at_matrix(eye, eye + forward, up)
        projection = perspective_matrix(
            self.ptzs[idx].fov,
            PTZ_TEXTURE_SIZE[0] / PTZ_TEXTURE_SIZE[1],
            NEAR_PLANE, FAR_PLANE)
        self._render_scene(self.feeds[idx]["fbo"], view, projection,
                           camera_pos=eye, draw_monitor=idx,
                           draw_avatar=True, exposure=1.25,
                           headlamp=0.9)

    def render_ptz_feed(self) -> None:
        """Active dome's camera renders every frame; the other domes'
        cameras refresh round-robin, one per frame."""
        self._render_feed(self.active_dome)
        others = [i for i in range(len(self.domes))
                  if i != self.active_dome]
        if others:
            self._feed_cycle = (self._feed_cycle + 1) % len(others)
            self._render_feed(others[self._feed_cycle])

    def _six_face_views(self) -> Iterable[tuple[str, np.ndarray]]:
        position = self.camera.position
        forward, right, up = self.camera.basis()
        definitions = (
            ("front", forward, up),
            ("back", -forward, up),
            ("right", right, up),
            ("left", -right, up),
            ("up", up, -forward),
            ("down", -up, forward),
        )
        for name, direction, face_up in definitions:
            yield name, look_at_matrix(
                position, position + direction, face_up)

    def _roof_cut_value(self) -> float:
        if self.roof_hidden:
            return float(self.camera.position[2]) + 1.9
        # RuneScape-style auto-roof: when the player is inside a dome in
        # orbit view, the structure above them turns see-through so the
        # camera is never blocked.
        if self.control_mode == "orbit":
            px, py = float(self.camera.position[0]), \
                float(self.camera.position[1])
            for model in self.domes:
                dx = px - float(model.origin[0])
                dy = py - float(model.origin[1])
                if math.hypot(dx, dy) <= model.floor_radius + 0.4:
                    return float(self.camera.position[2]) + 1.4
        return 1e9

    def render_six_point(self) -> None:
        projection = perspective_matrix(90.0, 1.0, NEAR_PLANE, FAR_PLANE)
        for name, view in self._six_face_views():
            self._render_scene(self.face_fbos[name], view, projection,
                               roof_cut=self._roof_cut_value())

        self.ctx.screen.use()
        width, height = pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.012, 0.016, 0.022, 1.0)

        for unit, (name, uniform_name) in enumerate((
            ("front", "u_front"), ("back", "u_back"),
            ("right", "u_right"), ("left", "u_left"),
            ("up", "u_up"), ("down", "u_down"),
        )):
            self.face_textures[name].use(location=unit)
            self.panorama_program[uniform_name].value = unit

        self.panorama_program["u_resolution"].value = (
            float(width), float(height))
        self.panorama_program["u_roll"].value = float(self.camera.roll)
        self.panorama_program["u_show_grid"].value = self.show_grid
        self.panorama_program["u_outside_color"].value = (
            0.012, 0.016, 0.022)
        self.panorama_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

    def render_normal(self) -> None:
        width, height = pygame.display.get_window_size()
        view, projection, eye = self._main_view_proj()
        self._render_scene(
            self.normal_fbo, view, projection, camera_pos=eye,
            roof_cut=self._roof_cut_value(),
            draw_avatar=self.control_mode == "orbit")

        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.normal_texture.use(location=0)
        self.normal_program["u_texture"].value = 0
        self.normal_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

    def update_caption(self, fps: float) -> None:
        mode = "360 SIX-POINT" if self.six_point_enabled else "NORMAL"
        movement = "FLY" if self.camera.fly_mode else "WALK"
        pygame.display.set_caption(
            f"Geodesic Dome Creator | {mode} | {movement} | "
            f"{fps:5.1f} FPS | M menu, H help")

    # -- smoke test ----------------------------------------------------------

    def _save_screenshot(self, path: str) -> None:
        width, height = pygame.display.get_window_size()
        data = self.ctx.screen.read(components=3)
        surface = pygame.image.frombytes(data, (width, height), "RGB", True)
        pygame.image.save(surface, path)

    def _smoke_step(self) -> None:
        cfg = self.model.config
        f = self.frame_count
        if f == 20:
            cfg.frequency = 2
            self._mark_changed()
        elif f == 30:
            # Quarter-wedge split logs on a hubless doubled frame.
            cfg.strut_shape = 4
            cfg.frame_style = "Hubless Doubled"
            self._mark_changed()
        elif f == 36:
            cfg.wedge_flip = True
            self._mark_changed()
        elif f == 40:
            cfg.frequency = 4
            cfg.strut_shape = 0
            cfg.frame_style = "Hub & Strut"
            cfg.hub_style = "Metal Brackets"
            cfg.wedge_flip = False
            self._mark_changed()
        elif f == 60:
            cfg.foundation = "Wood Deck"
            cfg.layers[0] = "Asphalt Shingles"
            cfg.layers[1] = "Plastic Film"
            self._mark_changed()
        elif f == 64:
            cfg.sections[0] = "Lounge"
            cfg.sections[1] = "Office"
            cfg.sections[2] = "Bathroom"
            cfg.sections[4] = "Wood Shop"
            cfg.sections[5] = "Assembly"
            cfg.sections[9] = "Storage"
            cfg.partitions = "Low Walls"
            cfg.props.extend([
                {"type": "Worktable", "x": 1.9, "y": -1.4, "yaw": 200.0},
                {"type": "Pegboard Bench", "x": 3.0, "y": 0.6, "yaw": 105.0},
                {"type": "Office Desk", "x": 1.2, "y": 3.2, "yaw": 25.0},
                {"type": "Office Chair", "x": 1.0, "y": 2.5, "yaw": 205.0},
                {"type": "Toilet", "x": -1.4, "y": 3.4, "yaw": 180.0},
                {"type": "Bathroom Sink", "x": -2.3, "y": 2.9, "yaw": 220.0},
                {"type": "Shelving Unit", "x": -3.1, "y": -1.2, "yaw": 70.0},
                {"type": "Tripod Light", "x": 0.9, "y": -0.9, "yaw": 0.0},
                {"type": "Shop Light", "x": -1.2, "y": -0.6, "yaw": 0.0},
            ])
            self._mark_changed()
        elif f == 68:
            self.placing = PROP_TYPES[0]
            self.ghost_yaw = 45.0
        elif f == 76:
            self.placing = None
        elif f == 80:
            cfg.default_panel = "Glass Window"
            self._mark_changed()
        elif f == 100:
            if self.model.panels:
                self.model.cycle_panel(self.model.panels[0].key, 1)
            self._mark_changed()
        elif f == 108:
            self._flash(self._apply_preset(1))     # Glass Studio Loft
        elif f == 114:
            self._flash(self._apply_preset(2))     # Split-Log Homestead
            self._set_helm(True, remote=True)      # hotkey camera control
            self.ptz.tilt = 40.0
        elif f == 118:
            self._set_helm(False)
            self._flash(self._electrify_dome())
            self.energy_open = True
        elif f == 120:
            self.six_point_enabled = True
        elif f == 150:
            self.six_point_enabled = False
            self.control_mode = "orbit"
            self.roof_hidden = True
            self.orbit_pitch = 1.2
            self.orbit_dist = 14.0
            self.camera.position[:2] = (0.0, 0.5)
        elif f == 162:
            if self.model.config.props:
                self._pickup_prop(0, 0)
        elif f == 166:
            if self.model.config.inventory:
                self._drop_from_slot(0)
        elif f == 168:
            self.roof_hidden = False
        elif f == 160:
            from pathlib import Path
            self._save_design()
            Path(BOM_FILE).write_text(
                self.model.bom_text(), encoding="utf-8")
        elif f == 170:
            self._load_design()
        elif f == 174:
            # Walk up to the console so the helm leash keeps hold.
            target = self.console["screen_center"]
            self.camera.position[:] = (
                float(target[0]), float(target[1]) - 1.6,
                PLAYER_HEIGHT + self.ground_height(
                    float(target[0]), float(target[1]) - 1.6))
            self.camera.yaw = 0.0
            self.camera.pitch = -0.1
            self.orbit_yaw = math.pi
            self.orbit_pitch = 0.35
            self.orbit_dist = 4.5
        elif f == 175:
            self._set_helm(True)
        elif 175 < f < 195:
            self.ptz.pan += 4.0
            self.ptz.tilt = min(100.0, self.ptz.tilt + 1.5)
            self.ptz.fov = max(12.0, self.ptz.fov - 1.0)
        elif f == 195:
            self._set_helm(False)
        elif f == 200:
            import presets
            self._flash(self._add_dome(presets.SECOND_DOME,
                                       simulate=True))
            if self.sim:
                self.sim["speed"] = self.sim["total"] / 0.8
                self.sim["workers"] = 3
            self.domes_open = True
            self.legend_open = True
        elif f == 220:
            # Exercise the RuneScape context menu + Panel Lab.
            self._open_context(self._world_context_entries(),
                               (500, 400))
            self.lab_qty = {"V-Bracket": 3, "Foam Seal (m)": 4}
            self.menu_page = 3
            self.menu_items = self._build_menu_items()
            self.menu_open = True
            self.menu_dirty = True
        elif f == 230:
            self.context_menu = None
            for item in self.menu_items:
                if item.label == "Create custom panel":
                    self._flash(item.activate())
                    break
        elif f == 335:
            if len(self.domes) > 1:
                for entry in self.domes[1].config.props:
                    prop = workshop.PROP_TYPE_BY_NAME.get(entry["type"])
                    if prop is not None and prop.light_z is not None:
                        entry["on"] = True
                self._mark_changed(1)
                self._refresh_lights()
            self.camera.position[:2] = (
                self.model.config.radius + 8.0, -14.0)
            self.orbit_pitch = 0.9
            self.orbit_dist = 18.0
            self.orbit_yaw = math.pi

        if os.environ.get("DOME_DEBUG") and f in (176, 189):
            print(f"frame {f}: cam={self.camera.position.round(2)} "
                  f"yaw={self.camera.yaw:.2f} pitch={self.camera.pitch:.2f} "
                  f"console={self.console['screen_center'].round(2)} "
                  f"helm={self.helm_active} "
                  f"aim_screen={self.aiming_screen}", flush=True)

        shot_dir = os.environ.get("DOME_SHOT_DIR")
        if shot_dir and f in (15, 34, 55, 72, 95, 112, 117, 130, 156,
                              178, 190, 226, 240, 330, 350):
            self._save_screenshot(
                os.path.join(shot_dir, f"smoke_{f:03d}.png"))

    # -- main loop -------------------------------------------------------------

    def run(self) -> None:
        last_time = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            delta_time = min(now - last_time, 0.05)
            last_time = now

            self.process_events()
            self.update(delta_time)
            self._refresh_overlays()

            self.render_ptz_feed()
            if self.six_point_enabled:
                self.render_six_point()
            else:
                self.render_normal()

            self.ctx.screen.use()
            self._render_overlays()

            pygame.display.flip()
            self.clock.tick(144)
            self.update_caption(self.clock.get_fps())

            self.frame_count += 1
            if self.smoke_frames:
                self._smoke_step()
                if self.frame_count >= self.smoke_frames:
                    print("SMOKE OK", flush=True)
                    self.running = False

        self.shutdown()

    def shutdown(self) -> None:
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()


def main() -> None:
    try:
        app = DomeCreatorApp()
        app.run()
    except ImportError as error:
        print(
            "\nMissing dependency. Install the required packages with:\n"
            "    py -3.12 -m pip install pygame moderngl numpy\n",
            file=sys.stderr,
        )
        raise error
    except Exception as error:
        print(
            "\nApplication failed to start or render.\n"
            "Confirm that your graphics driver supports OpenGL 3.3.\n"
            f"Error: {error}\n",
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    main()
```

==========================================================================
======== FILE: flatten.py ========
==========================================================================

```python
"""
Flatten the entire project into a single file for uploading to LLMs.

Run:
    py -3.12 flatten.py            -> writes dome_flat.md
    py -3.12 flatten.py out.txt    -> custom output name

The output contains every source file, each preceded by a clear
======== FILE: path ======== marker, plus a table of contents with line
counts, so a model (or a human) can navigate the whole codebase from
one upload. Generated artifacts, caches, and the flat file itself are
excluded.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_OUTPUT = "dome_flat.md"

INCLUDE_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".cfg"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".claude", ".venv", "venv",
                "node_modules"}
EXCLUDE_FILES = {DEFAULT_OUTPUT, "dome_flat.txt", "dome_bom.txt",
                 "dome_design.json"}

# Read order: overview first, then the code in dependency order.
PRIORITY = ["README.md", "materials.py", "workshop.py", "presets.py",
            "dome_model.py", "mesh_builder.py", "electrical.py",
            "vision.py", "overlay_ui.py", "dome_creator.py",
            "flatten.py"]


def gather_files() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_SUFFIXES:
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)

    def order(path: Path) -> tuple:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        try:
            return (0, PRIORITY.index(rel))
        except ValueError:
            return (1, rel)

    return sorted(files, key=order)


def main() -> None:
    output = ROOT / (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT)
    files = gather_files()

    sections = []
    toc = []
    total_lines = 0
    for path in files:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.count("\n") + 1
        total_lines += lines
        toc.append(f"- {rel}  ({lines} lines)")
        lang = {".py": "python", ".md": "markdown",
                ".json": "json"}.get(path.suffix.lower(), "")
        sections.append(
            f"\n\n{'=' * 74}\n"
            f"======== FILE: {rel} ========\n"
            f"{'=' * 74}\n\n"
            f"```{lang}\n{text.rstrip()}\n```"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# Geodesic Dome Creator — flattened project\n\n"
        f"Generated {stamp} by flatten.py. "
        f"{len(files)} files, {total_lines:,} lines total.\n\n"
        "Each file below is delimited by a `======== FILE: path "
        "========` marker.\n\n"
        "## Table of contents\n\n" + "\n".join(toc)
    )

    output.write_text(header + "".join(sections), encoding="utf-8")
    size_kb = output.stat().st_size / 1024
    print(f"Wrote {output.name}: {len(files)} files, "
          f"{total_lines:,} lines, {size_kb:,.0f} KB")


if __name__ == "__main__":
    main()
```