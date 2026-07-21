# Geodesic Dome Creator

A walkable, build-a-home style **parametric dome customizer** with
RuneScape-style controls: an orbit camera, click-to-move avatar, a
clickable toolbar, a transparent-roof aerial view, and a 28-slot
backpack for picking up and dropping workshop equipment. Change the
structure, swap the recessed panels between the struts one by one
(windows, shingles, solar, plastic sheeting, ...), stack cladding
layers, pick a foundation — and watch a complete material breakdown
(weights, costs, strut cut list, trees to harvest) update live.

This is also a live investor-demo presentation tool. Geometry stays in
real-world scale, the player/avatar is a six-foot reference, and hover
tooltips explain what the audience is seeing as you explore. Press `T`
while hovering a dome, panel, prop, or camera to edit the presentation
note; notes are saved in `dome_demo.sqlite3` and persist between
sessions.

Includes the original 360° six-point perspective renderer (press `Tab`).

The simulator starts at the desktop's native fullscreen resolution.
Optional widgets start minimized; use the toolbar to open the backpack,
help strip, key legend, and operations suites as needed.

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

The main 3D view is framed as its own world pane with a RuneScape-style
command rail on the right. The rail contains the site minimap, selected
dome summary, and contextual dome actions so investor demos stay less
cluttered. Selecting any dome opens the Dome controls automatically,
including manual X/Y coordinates and a click-to-move action.

## Many domes

The **Domes** toolbar button opens the site manager: every dome on the
site with its style, status, live load, and vision summary. Click a row
to select it (menus, stats, BOM, and the video window all follow the
selection) and open dome actions: walk to, move, resize, simulate, or
delete. Right-click a row opens the same action menu. Use **+ Add dome**
to pick a style and click the ground to have a crew build it there.
Placement, moving, and resizing refuse overlaps with other domes so the
site remains physically credible. Save/load round-trips the entire site.

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

The **Crew** toolbar widget adds worker management: each worker has a
target dome, assigned task focus, detected action, labor hours, and
walking distance. Right-click the construction status bar to add/remove
workers, assign the crew to a specific dome, or shift the task focus.
PTZ cameras identify visible workers and the action they appear to be
doing, then roll those counts into the live worker display.

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

## Dome Home Assembly Line (`assembly_line.py`)

A standalone factory simulation of the manufactured-housing production
line: a transfer carriage rolls a dome down rails through **15 numbered
gantry stations**, each adding one build step in real trailer-plant
order, until every component of the finished home is present:

1. **Floor framing** — wood floor built into the base ring (rim,
   joists, decking)
2. **Dome shell framing** — geodesic timber frame raised bottom-up
3. **Center utility column** — floor-to-apex service column carrying
   water and power in one column, with the **crane anchor** fitting on
   the outside of the apex
4. **Water lines** — hot/cold PEX + drains through the floor, all
   terminating centrally at the column
5. **Power lines** — conduit through the floor to the column
6. **Fixtures & outlets** — toilet, shower, sinks set; outlets on the
   column and perimeter; breaker panel
7. **Insulation** — batts packed into every frame bay
8. **Sheetrock** — interior shell rocked
9. **OSB sheathing** — panel board covering the dome exterior
10. **Water barrier** — sill/water membrane over the OSB
11. **Shingle scales** — plastic-scale mechanical water barrier
12. **Fiberglass encasement** — the entire structure encased watertight
13. **Watertight hatch door** — sealed marine-style hatch, the home's
    only opening (**zero windows**)
14. **Interior fit-out** — complete kitchen, bathroom, and bedroom
    (auto interior-cutaway view while this station works)
15. **Solar array** — solar skin on the sun-facing band + final QC

At the end of the line a gantry crane hooks the apex anchor, lifts the
home off the carriage, and sets it on a **big mechanical lazy susan**.
The geared turntable then rotates automatically so the solar band
tracks the sun as it arcs across the sky.

### An investor decision tool, not just an animation

The line is driven by a real cost-and-labor model in
[al_build.py](al_build.py), so the running demo shows the numbers an
investor actually underwrites. Dome-line assumptions live in its editable
`ASSUMPTIONS` block; the independent site-shed benchmark lives in
[site_shed.py](site_shed.py).

- **Four product lines.** The same line builds a **Dome Home** (full
  15-station build), a **Storage Shed** (frame + corrugated sheet metal),
  a **Greenhouse** (aluminium frame + polycarbonate glazing + grow
  benches), and a **Storm Shelter** (small welded short-strut steel-plate
  dome). Each has its own station sequence, materials, size range, and
  pricing; the build sequence and checklist adapt per type.
- **Real per-element economics.** Every strut, pipe, panel, and fixture
  carries a material cost and an install-labor time. A per-station crew
  (default **2 workers**, adjustable live) **fetches each element from a
  material stockpile** and walks it to its spot at a real human stride
  (0.76 m/step); **steps, distance, labor-hours, and dollars accrue live**
  as ground-truth numbers, and a **fade-away `+$cost` popup** rises off
  every element as it's placed.
- **Random product mix, persisted.** Each run randomizes the dome (type,
  size, frequency, layout, cladding). Finished units are serialized,
  saved to SQLite (`dome_yard.sqlite3`), and **stacked in a growing yard
  that survives across sessions** until you clear it. Startup performs an
  idempotent, column-by-column schema migration so older yard databases gain
  new fields without deleting units or requiring a manual reset.
- **Advanced finished-dome inspection.** Click any yard dome to open a
  **Photoshop-style LAYERS panel** — toggle each layer visible/hidden and
  solid/transparent to peel the shell back — plus a **buyer TOUR** camera
  (eye-level walk-through with the shell x-rayed) and live **material
  variance** swapping. The whole shell is also togglable to see-through
  mid-build with **X-RAY** (button or `X`) so the interior stays visible.
- **Fixed conventional comparison shed.** A **24 × 16 × 10 ft** site-built
  gable shed is parked beside the finished-dome yard and never enters the
  assembly line. This is intentionally a bare-minimum **sub-$10k** shell:
  compacted gravel strips, 15 precast deck blocks, pressure-treated skids,
  2×6 floor framing and plywood, 2×4 walls, site-built 3:12 rafters,
  structural T1-11 siding, economy shingles, and double plywood doors—no
  slab, windows, utilities, or finish package. Click it—or press
  **SHED VS**—to peel its nine build layers apart and see the itemized
  **$8,720 build / $9,689 quote** beside the
  selected/reference dome: floor area, enclosed volume, cost, quote,
  $/ft², labor, modeled crew, and working days. This benchmark is excluded
  from factory throughput, sales, and the production ledger.
- **Sales without disappearing inventory.** A sales office sits by the lot;
  each dome shows a
  **price + buy-here-pay-here monthly sign**. Customers walk over, buy a
  dome (it flips to **SOLD**), and then leave it in its assigned yard slot.
  Sold and unsold domes both persist, accumulate, and remain clickable for
  inspection; **SELL** only records ownership/revenue. The SOLD status is
  displayed with—not instead of—the original price and BHPH monthly payment.
- **Full-page live pricing editor.** Press **PRICES** or `P` to edit all 21
  catalog element categories used across Dome Home, Storage Shed,
  Greenhouse, and Storm Shelter builds. Material $/element, labor minutes,
  weight, burdened wage, overhead/labor-hour, and each product's base and
  per-m² sale price are editable. **APPLY + RESTART** reprices the current
  run and persists the settings in `assembly_pricing.json`; **RESET
  DEFAULTS** restores the shipped model.
- **Live dockable panels** (tab row, top-right): **P&L** (materials +
  labor + overhead vs. sale price = gross margin, with lumber/resin/wage
  **sensitivity toggles**), **FLOW** (per-station takt time, the
  bottleneck, single-piece vs. pipelined throughput, QC first-pass yield,
  downtime cost), **BOM**, **VS** (dome vs. the fixed site shed),
  **VALUE** (solar kW, R-value, off-grid autonomy, embodied carbon,
  OSHA), **SCALE** (1/3/6-line scenarios + break-even), and **YARD**
  (production & sales ledger — built, retained on lot, sold, revenue).
- **Interactive.** Speed slider, pause/step, follow / cutaway / **x-ray**
  / **cinematic** (drag to change angle while it orbits) cameras, snapshot
  export, **hover any placed element** to inspect its cost/labor/weight,
  a **pre-run configurator** (pick type/layout/size/frequency/cladding or
  randomize), **crew size** control, **disruption injection** (supply
  delay, breakdown, worker absence), **SELL**, **PRICES**, **SHED VS**, and
  **clear yard**. A faint bottom legend keeps every keyboard and camera
  control visible in normal and inspection views.

```
py -3.12 assembly_line.py            # fullscreen
py -3.12 assembly_line.py --window   # windowed
py -3.12 assembly_line.py --selftest # model + DB check, no GL
py -3.12 assembly_line.py --shots 4,60,120   # offscreen PNG renders
```

Controls: `Space` pause, `[` / `]` speed (x0.25–x8), on-screen speed
slider, mouse-drag orbit, wheel zoom, `F` follow/free camera (WASD pans
when free), `C` interior cutaway, `X` x-ray shell, `V` cinematic orbit,
`-` / `=` crew size, `P` / **PRICES** open the full pricing editor,
**SHED VS** open the site-shed comparison,
left/right arrows orbit in their matching on-screen direction,
`R` start a new random dome, `Esc` quit / exit
inspection. Everything else (panel tabs, control-bar buttons,
configurator, yard domes, layer toggles) is clickable; the bottom toolbar
remains active in both normal and inspection views. Every dollar and
time figure is editable live through **PRICES**, or directly in
[al_build.py](al_build.py) (dome line) and [site_shed.py](site_shed.py)
(site-built comparison).

## Preset setups

Twelve out-of-the-box designs ship in [presets.py](presets.py) — cycle
them with the toolbar **Preset** button or load one from menu page
`4·FILE`:

1. **Timber Workshop** — 3V lumber, metal brackets, concrete slab, full
   shop fit-out (default at startup)
2. **Glass Studio Loft** — 4V glass on a wood deck, office/lounge/bath
3. **Split-Log Homestead** — 2V hubless quarter-wedge frame, cedar
   shakes, kitchen/bath/lounge
4. **Whole Trunk Lodge - 20 ft** — massive full-round tree-trunk frame,
   scaled so its longest members are just under 20 ft, using 25 in
   circumference trunks; trunk stock counts appear in the live material
   panel and BOM
5. **Grow Dome** — aluminum + polycarb greenhouse with grow racks
6. **Hex Cell Pavilion** — structural-steel hex frame with composite
   hexagonal tiles and a presentation-ready studio fit-out
7. **Continuous Steel Arc Hangar** — large curved steel ribs with
   fabrication, access, safety, and site-power equipment
8. **Rebar Garden Dome** — dense meridian-and-ring rebar lattice with
   water and climate-control equipment
9. **Concrete Monocoque Form** — rebar/formwork system with a poured
   concrete shell, shoring, scaffold, mixer, and rebar bender
10. **Woodland Hex Mirror** — hexagonal mirror tiles that reflect the
    procedural sky, ground, trunks, and wooded site perimeter
11. **Woodland Square Mirror** — square mirror tile variant on a
    structural-steel frame
12. **Treehouse Canopy Dome** — elevated hex-tile dome on a supported
    timber platform with braces and ladder access

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

The **Props** toolbar button activates an equipment-target cursor in the
3D world. Click an empty dome-floor location to open a full two-pane
context menu there: hover or click a category on the left, then click an
item with visible price, weight, and power details on the right to place
it at the targeted point. Arrow keys and Enter remain available for
keyboard navigation. Right-clicking an empty dome floor opens the same
menu directly. Its 39 placeable items include
the original furniture and utilities plus
generators, compressors, welding and cutoff stations, rebar/concrete
tools, shoring, scaffold, ladders, mirror racks, water storage, climate
equipment, and fire/first-aid stations. Pick one, aim at
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
| `Left-click` prop | Walk over and move it; powered devices switch on/off |
| `Left-click` wall monitor | Walk over and take helm of the PTZ camera |
| `C` | Remote camera control from anywhere (toolbar: Cam) |
| `Left-click` lamp/appliance | Switch it on/off (walks over if far) |
| `N` / toolbar **Power** | Open the full energy-control suite |
| Toolbar **Crew** | Worker assignments, actions, and stats |
| Toolbar **Materials** | Show or hide the live material breakdown |
| Toolbar **Help** / click help strip | Show or collapse the contextual help strip |
| `[` / `]` | Construction sim speed |
| `Del` | Pack the aimed prop into the backpack |
| Toolbar **Preset** | Cycle the out-of-the-box dome setups |
| Select/right-click dome row | Move, resize, simulate, or delete that dome |
| Right command rail | Minimap and selected-dome controls |
| `Left-click` minimap | Walk to that site coordinate, including inside a dome |
| `Right-click` minimap dome | Open that dome's contextual actions |
| `Left-click` exterior panel | Select its dome and swap that panel |
| `Ctrl+click` exterior panel | Walk to that panel from outside |
| `Right-click` exterior panel | Open contextual panel and dome actions |
| `Right-click` empty dome floor | Open the equipment menu at that location |
| Interior shell panels | Transparent to picking so floor and items remain interactive |
| `Middle-drag` / `Arrows` | Rotate the orbit camera |
| `Shift+drag` overlay widget | Move that widget |
| `Ctrl+drag` overlay widget | Resize that widget (50% to 200%) |
| Live camera | Anchored unobstructed at the top-left of the world view |
| Build / Domes / Rooms / Crew / Materials / Power / Lab | Open the full-window operations suite |
| Props button | Toggle the in-world equipment targeting cursor |
| Equipment cursor click | Open category and item submenus at that floor point |
| Equipment menu `Up` / `Down` or wheel | Browse equipment |
| Equipment menu `Left` / `Right` | Change equipment category |
| Equipment menu `Enter` / `Space` | Place the selected equipment |
| `Esc` in operations suite | Return to the 3D world |
| Hover object/dome + `T` | Edit persistent investor-demo tooltip |
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
