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
