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

## Launcher — start here

This project has grown into several standalone tools (the dome creator
below, the [assembly line](#dome-home-assembly-line-assembly_linepy),
the [2V masterclass](#standalone-2v-geodesic-masterclass-two_v_masterclasspy),
[Local Voice Studio](#local-voice-studio-local_voice_studiopy), and
Presenter Studio). None of them take command-line flags anymore — every
option that used to be a `--flag` is now a field in one consolidated
GUI:

```
py -3.12 -m pip install pygame moderngl numpy
py -3.12 launcher.py
```

Each tab mirrors one tool's former CLI surface (run mode, offscreen
stills, video export + narration voice settings, build-packet export,
project folders, and so on). Clicking a launch button writes a one-shot
JSON "ticket" describing your choices, then starts that tool with no
arguments; the tool reads and deletes the ticket at startup and acts on
it. Output from self-tests, exports, and other console-only actions
streams into the log pane at the bottom of the launcher window, so
nothing requires an external terminal.

The launcher is written for people who have never touched this
codebase: every tab opens with a plain-language description of what
that tool does and why you'd use it, every non-obvious field carries
grey example text showing its expected format (never treated as a real
value — it clears the moment you click in), and every dropdown/Action
choice is explained inline. Every tab also scrolls independently with
its launch button pinned in a fixed footer, so the button that actually
runs the tool is never hidden below a long list of fields.

Running any tool directly (`py -3.12 dome_creator.py`, etc.) still
works — with no ticket present it just falls back to that tool's plain
default (usually the fullscreen live app), since the launcher is now
the only supported way to change what a run does.

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
py -3.12 launcher.py                 # Assembly Line tab: windowed/fullscreen,
                                      # self-test, offscreen-stills options
py -3.12 assembly_line.py            # direct run, fullscreen, no options
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

## Standalone 2V Geodesic Masterclass (`two_v_masterclass.py`)

The 2V Masterclass is a separate ModernGL world for teaching and YouTube
capture. It does not enter the Dome Creator site or the assembly-line factory.
Its 14-chapter timeline reconstructs the geometry from phi coordinates,
normalizes the parent icosahedron, animates midpoint projection, discovers the
two chord classes numerically, audits the supplied 72 in / 63.5 in members,
builds the 30-SHORT / 35-LONG hemisphere cut list, and raises the dome from the
base ring to the apex.

```powershell
py -3.12 -m pip install -r two_v_demo/requirements.txt
py -3.12 launcher.py               # 2V Masterclass tab: every option below
py -3.12 two_v_masterclass.py      # direct run, fullscreen presenter mode
```

Self-test, calculation report, narration script/SRT, build-packet export
(CSV cut list + OBJ + field guide), offscreen stills, video export with
neural narration, voice preview/listing, and the ffmpeg/ffprobe paths are
all fields on the launcher's **2V Masterclass** tab now, in place of the
former `--selftest` / `--report` / `--script` / `--build-packet` /
`--shots` / `--export-video` / `--voice*` / `--ffmpeg` flags.

See [two_v_demo/README.md](two_v_demo/README.md) for presenter controls,
voice audition/selection, measurement conventions, and video-export notes.
The exporter also contains a compatibility audio mixer for older FFmpeg builds
that lack `adelay`/`loudnorm`, so generated chapter audio is still assembled
and embedded in the final MP4.

## Presenter Studio (`presenter_studio.py`)

Presenter Studio is a fourth standalone world: a scriptable text-to-video
engine built on the 2V Masterclass's rendering core. A `Presentation` is
pure data — scenes with a free-text environment prompt, shots with a lens
(macro/portrait/wide/ultrawide), a 1-6 point camera perspective (1-3
linear, 4 cylindrical, 5 fisheye, 6 full 360), a snap-to focus target,
animatable object parameters, narration lines, a lower-third caption, and
a floatable overlay panel (bullets/equations/stats) — so the same
deterministic frame renders identically live and in the exported MP4.

```powershell
py -3.12 launcher.py            # Presenter Studio tab: every option below
py -3.12 presenter_studio.py    # direct run, live fullscreen
```

Pick a **Built-in demo**, or point at a presentation script (a `.py` with
a `build()` function, or a saved `.json`), or type a free-text
**production brief** ("seven scenes each of three shots, a close up,
macro and ultra wide shot of elements 1, 2 and 3") and the engine drafts a
skeleton `Presentation` from it. Action / Export MP4 / narration toggle /
fps / size / still-frame times / fullscreen / self-test are all launcher
fields, in place of the former CLI flags.

Twelve built-in demos ship in `presentations/`:

- **`airflow`** — *The Dome That Breathes*: a perimeter-plenum tube
  ringing a 2V dome's base, one leaf blower holding the whole envelope at
  negative pressure, and the same loop reversed into a central vacuum.
- **`housing_case`** — *The 2V Housing Case*: the convergent
  housing-market argument for 2V domes — fundamentals (including a live
  debunk of the golden-ratio myth), a station-by-station build of all 15
  stages the assembly-line simulator uses, the real shed- and home-tier
  cost comparisons from `al_build.building_comparisons()`, a hedged
  structural/energy case, the manufacturing and factory-economics case, an
  explicit list of claims the project will not make, and the real product
  line and financing math. Every number on screen comes from the same
  modules the interactive tools use, not a hardcoded figure.
- **The ten-part `case_*` series** — the same convergent argument as
  `housing_case`, split into ten standalone, full-length presentations,
  one per argument, each with its own hook, evidence, honest hedge, and
  close: `case_manufacturing` (the standardized-product/manufacturing
  case), `case_bare_shell` (the shed-tier cost comparison),
  `case_more_room` (the home-tier comparison — a small honest price gap,
  a real volume win), `case_triangles` (the structural-rigidity
  argument, built from a first-principles degrees-of-freedom count),
  `case_benchmark` (vs. a conventional manufactured home, plus the
  factory throughput/break-even math), `case_energy` (the hedged
  off-grid/solar case), `case_resilience` (the hedged wind/seismic case
  and the resilience claims this project refuses to make),
  `case_financing` (real BHPH financing math across every product
  tier), `case_utility_core` (the curved-wall objection and the rest of
  presentation.txt's "what must be solved" list), and
  `case_market_fit` (honest market fit — where this is, and is not, the
  right product, closing the ten-part series). All numbers in every one
  of the ten come from `presentations/_numbers.py`, computed once from
  the same modules the interactive tools use, shared so a figure can
  never drift out of sync between presentations.

Every shot in every demo carries on-screen text — a caption plus, where
there is a real claim to make, an overlay panel — so the argument reads
complete with the sound off; narration is a second channel, not the only
one.

## Dome Forge (`dome_forge.py`)

Dome Forge is a **single-dome builder made of layers** — the way an image
is made of layers in a paint program, or a character is made of
adjustable parts in a game's character creator. There is no site, no
factory, and no timeline: exactly one dome, at the origin, that you can
orbit and take apart.

Every part of the dome is its own layer that can be hidden, faded with an
opacity slider, reordered, duplicated, deleted, and tuned through its own
named controls. Thirteen layer types ship:

| Layer | What it is |
| --- | --- |
| Ground pad | The slab, for scale and orientation |
| Triangle frames (hubless) | 40 separate bolted triangles — how these domes are really built |
| Strut frame | A simpler stick diagram of the same edges, for teaching |
| Hub connectors | The joints where struts meet (only for the stick diagram) |
| Panels | The triangular skin — flat, or dished inward like a golf-ball dimple |
| Micro-drains | An outlet at the low point of each dished panel |
| Seam veins (gasket) | A channel along the inside of every seam, held clear of the skin |
| Water in the veins | Animated flow, running downhill toward the base |
| Runoff on panels | Droplets sliding to each panel's micro-drain |
| Shell surface | A surface at any depth — liner, vapour barrier, or insulation |
| Collector ring | The gutter every vein empties into |
| Downpipe | The pipe down to the tank |
| Cistern | The tank under the dome, with an adjustable fill level |
| Rain | Falling rain, so the capture story reads at a glance |

### The water-harvesting dome it opens with

The default stack is built around turning the classic leaky-dome
complaint into plumbing. Panels are dished inward so rain runs to one low
point per panel instead of sheeting across the seams; a micro-drain sits
at each of those low points; and a **vein network runs along the inside of
every one of the 65 seams, standing off from the outer skin by a
deliberate gap** — so anything that does get past a seam lands in a
channel instead of dripping inside, and the gap stays an inspectable air
space rather than wet material sealed against the structure. The veins
drain downhill into a collector ring, through a downpipe, into a cistern
under the dome. Press `C` for the cutaway and watch it move.

### Per-triangle make-up, and the Panel Creator

Click any triangle in the 3D view to select it, then change what *that
one* is made of. Each triangle carries its own **fill** and its own
**strut on each of its three edges** — and the three edges deliberately
do not have to match, because real builds mix sections.

Struts (18): quarter-round, half-round and full-round split logs; 2x2,
2x4, 2x6 and wide plank lumber; bamboo; steel rod, tube, square tube and
angle; the aluminium equivalents; PVC pipe and square tube; solid
plastic bar. Fills (19): glass, polycarbonate, acrylic, Fresnel lens,
mirror, solar panel, louvered vent, AC unit, fabric, screen mesh, stone,
metal sheet, wood sheet, wood planks, shingles, plastic sheet, insulated
panel, door, or open.

Press `m` a second time for the **Panel Creator**: build one panel on a
bench from any three struts plus a fill, look at it up close, then send
it to the selected triangle or to the whole dome.

Every choice opens a **dropdown**, laid out in as many columns as the
window can take, rather than making you click through a list one item at
a time.

**Selecting works the same way in every editor.** In the dome you click
triangles; in the **Panel Creator** you click individual **struts** on
the bench; in the **group editors** you click triangles too, but only
ones belonging to the group you are working on, so a stray click cannot
drag an unrelated face in. That means a pentagon is not all-or-nothing —
select one, two, or all five of its triangles and change just those. The
floating toolbar follows the selection in every case.

Click a component to select it; **ctrl-click** (or
shift-click) adds and removes others.

The toolbar has keyboard equivalents, live whenever something is
selected: `F` fill, `T` strut, `R` roll 90, `X` mirror, `]` and `[`
pop-out, `Del` clear. **Left and right arrows step the selection through
its own variants** — a selected strut walks the profile catalogue, a
selected triangle walks the fills. With nothing selected the arrows go
back to stepping through groups or jig steps. Selected pieces light up and
**pop out** of the shell — they lift straight off along their own
normal so you can orbit right around a piece and see it whole, without
hiding anything or leaving a hole where it came from. A **floating
toolbar** appears over the 3D view whenever anything is selected and
acts on the whole selection: fill, strut, roll, mirror, pop-out
distance, and clear.

**Struts can be rolled about their own axis.** For anything that is not
symmetrical this changes the build, not just the look: a quarter-round
can show its curve to the inside, to the outside, or turn its right-angle
corner where you want it, and a half-round can sit flat-face-out or
flat-face-in. Rolling is stored in the strut key (`log_quarter/2`), so
older presets that carry a bare key still mean "unrolled". Rolling a
non-square section genuinely changes its footprint — a half-round is
180 mm wide flat but 90 mm on edge — and the selftest asserts exactly
that, along with checking that every roll of every profile still anchors
to its seam line instead of drifting off it.

Rolling is a **toolbar action on the selection**, not a set of entries
in the strut list: rolling is something you do *to* the piece you have
already picked. That keeps the strut list at 18 honest profiles instead
of 72 near-duplicates. Swapping a profile keeps whatever roll the strut
already had.

Mixing sections is a geometry problem, not a paint job. Struts of
different widths push their inner faces in by different amounts, so the
opening left in the middle is *not* a scaled-down triangle. The inner
outline is therefore built by intersecting each edge's own offset line
with its neighbour's, and the selftest asserts that every inner corner
sits exactly its own edge's width in from that edge — for a deliberately
mismatched half-round / 2x2 / quarter-round set.

The **splitlog** starting dome in the launcher matches a real split-log
build: half-round logs on the long seams, quarter-round on the short
ones, 2x2 on the ten equilateral caps. Split a trunk once for two
half-rounds; split those again for four quarter-rounds per log.

### Cover patterns (flat developments)

A dome is doubly curved, but it is made of flat triangles, so any
connected patch develops into a flat cutting pattern exactly -- the way
a sailmaker or a stitch-and-glue boatbuilder flattens a curved surface
into panels cut from flat stock. `m` reaches a **Cover Patterns** mode
(arrows change the shape) that does this and lays the result on your
sheet, to scale, with real dimensions:

- **Single / double / triple** triangles develop as *strips* -- a chain
  of triangles has no loop around a vertex, so it flattens with no gap:
  an exact, seamless pattern. The ridge between triangles is a fold line
  (score it, don't cut).
- **Pentagon** (five triangles) and **hexagon** (six) develop as *fans*
  around their centre vertex. Going all the way around meets the
  **angular deficit** -- the flat angles don't add to 360 degrees -- so
  the fan leaves an open wedge: a **~15.7 deg dart** for a pentagon,
  **~17.7 deg** for a hexagon. Lay the sheet flat, close the dart (sew,
  or lap and staple), and the centre lifts into the dome's curve. That
  dart *is* the "upward centre".

Set your dome's long strut (72 in for the reference dome, giving a
63.67 in / 63⅝ in short strut) and your sheet size, add a seam / wrap
allowance for the slack that folds around the frame and staples, and the
drawing shows the cut line, the finished edge, the fold lines, and the
dart, dimensioned in feet and inches. It reports whether the pattern
fits the sheet and how many of each the whole dome needs -- and a
monolithic pentagon on a 25 x 10 ft sheet does **not** fit (it develops
to about 10.5 x 10.6 ft), which is exactly the kind of thing this view
exists to catch before you cut. Save the image to print.

Every length in every pattern is developed from `two_v_demo`'s own
geometry and checked in the selftest to equal the true 3D edge to
within 1e-6 in, so a printed pattern is cut to the same numbers the
frame was built to.

### The design library

The whole tool is built around one chain, and it is now explicit:

```text
strut profiles  ->  a triangle  ->  a pentagon or an hourglass  ->  a dome
```

A **triangle design** is three strut specs plus a fill — exactly what the
Panel Creator makes. Save one with a name, load it back onto the bench,
or apply it to whatever is selected in the dome. A **pentagon design** is
five references to triangle designs, and an **hourglass design** is two
plus the joint at its waist.

Groups store **references, not copies**, so fixing a shared triangle
fixes every group built from it. Saving a group captures each distinct
face composition as a triangle design and reuses one that already
matches — save a pentagon whose five faces are all the same part and you
get one new part, not five. Renaming is never destructive either: saving
over an existing name adds a suffix rather than overwriting, and deleting
a part also removes the groups that referenced it rather than leaving
them pointing at something gone.

Designs live in the preset file next to the layers, so a saved dome
carries the parts it was made from and not just the finished result.
Nine starter designs ship, including the split-log mix (half-round,
2x2, quarter-round) this project was asked about.

### Pentagons and hourglasses

Nobody thinks about a dome one triangle at a time, so `m` also reaches a
**Groups** mode (Tab swaps between the two kinds, arrows step through
them, and the selected group lights up on the dome):

- A **pentagon** is the five isosceles triangles ringing a five-way
  vertex, meeting at the apex between their two short sides. **Six** per
  hemisphere.
- An **hourglass** is two equilateral triangles touching at **exactly
  one vertex** — point to point, waist in the middle. **Ten** per
  hemisphere, filling the gaps between the pentagons.

Both are found from the geometry, and the selftest asserts the counts
and, for every hourglass, that its two triangles share exactly one
vertex — two shared vertices would make them edge neighbours, which is a
different thing entirely.

Pentagons ship with **16 ready-made designs** — all glazed, glass cap,
solar cap, solid, planked, shingled, skylight-plus-solid, vent pair,
alternating glass and solid, entry pentagon with a door, mirror cluster,
Fresnel collector, a plant pentagon with an AC unit, insulated,
split-log solid, and a light 2x2 frame — so a whole five-triangle
assembly drops in with one pick.

Because an equilateral triangle has three corners, one triangle belongs
to more than one hourglass. A joint therefore belongs to the **waist**,
not to either triangle. Six waist joints ship:

| Joint | What it is |
| --- | --- |
| Bare tips | The points just touch — fine for dry-fitting, carries nothing |
| Metal banding | Steel strap wrapped round both tips and tensioned |
| Square wooden braces | Blocks bridging the two sides that form each point, bolted through to the block opposite |
| Monolithic waist | Both points are one continuous piece — strongest, least forgiving |
| Steel gusset plate | A flat plate over the waist, bolted into both triangles |
| Bolted lap | Tips halved in thickness and overlapped so they finish flush |

The wooden braces are the point worth understanding: they put the load
into the *sides* of the triangles rather than into their mitered tips,
which are end grain and the weakest part of the whole assembly.

### Hubless construction, and the Jig Shop

The frame layer models the way these domes are actually built: **40
separate triangles**, each three flat-laid boards mitered at the corners,
bolted to their neighbours. Because every triangle brings its own board
to a shared seam, each seam ends up two boards thick — and there are no
hub connectors anywhere in the dome.

Press **`m`** for the **Jig Shop**, a second world in the same tool. A
2V hemisphere has 40 triangles but only **two shapes** (10 equilateral,
30 isosceles), so two jigs produce the whole dome. Nine steps walk
through building each one — base plate, scribed triangle, fences, corner
stops, cutting, loading, fastening — with the exact cut list at every
step, all following the radius you set:

| | Equilateral (×10) | Isosceles (×30) |
| --- | --- | --- |
| Corner angles | 60° / 60° / 60° | 55.569° / 55.569° / 68.862° |
| Saw miter | 60° all six cuts | 62.215° / 62.215° / 55.569° |
| Edge bevel | 9.0146° (all LONG) | 9.0146° LONG, 11.2295° SHORT |

Two things here catch people out, and the last step is about both. The
**boards are trapezoids, not rectangles** — the outer edge runs the full
chord while the inner edge is shorter, because both ends are mitered
inward. And the flat interior angles meeting at a vertex do **not** sum
to 360°: they fall short by 15.69° at a five-way vertex and 17.72° at a
six-way one. That shortfall is exactly what curves the dome, and it means
the mitered tips converge on a *line through the vertex* rather than
meeting at a point on a plane — so expect a small void at each vertex,
and blunt the tips rather than chasing a perfect point.

Every one of those figures is computed from `two_v_demo/geometry.py` and
then **re-measured straight off the assembled 3D faces** by
`dome_forge/jigs.py`'s `verify()`, which the selftest runs. If the shop
drawing and the dome ever disagree, it raises instead of quietly
shipping a jig that builds the wrong triangle.

```powershell
py -3.12 launcher.py     # "Dome Forge" tab, then press m
```

Mouse: drag to orbit, scroll to zoom, click a layer to select it, click
its square to hide it, drag the bar under its name to fade it. Keys:
`space` pause/play the water, `c` cutaway, `1`–`4` preset views
(outside / inside / top-down / ground level), `s` save, `l` load,
`Escape` quit. The launcher's `shots` action renders four stills
headlessly, and `selftest` checks the geometry and every layer type
without opening a window.

Every count and dimension in the readout — 65 struts (30 short, 35
long), 40 panels, 26 hubs, both strut lengths, the floor area — is
computed from the same `two_v_demo/geometry.py` used by the masterclass
and the presentations, scaled by the radius slider. None of it is written
down twice.

## Local Voice Studio (`local_voice_studio.py`)

Local Voice Studio is a third standalone program for recording speech you own,
curating 24 kHz voice clips, building a locked reference profile, and
synthesizing narration locally. It uses no hosted inference API. Chatterbox
Turbo provides optional local reference-voice generation, faster-whisper
provides optional local transcription, and the F5 adapter exports an
`audio_file|text` dataset for advanced fine-tuning.

```powershell
py -3.11 -m venv .venv-voice
.\.venv-voice\Scripts\python.exe -m pip install `
    -r .\local_voice_studio\requirements-core.txt
py -3.12 launcher.py   # Local Voice Studio tab: project folder, self-test,
                       # diagnose — replaces --project / --selftest / --diagnose
```

The launcher spawns most tools with whichever Python interpreter it is
itself running under. Local Voice Studio is the one exception: if a
`.venv-voice` folder exists (see setup above), the launcher always uses
that environment for Local Voice Studio specifically, regardless of
which Python started the launcher window — so installing the optional
local-AI backends there is enough on its own; you do not also need to
relaunch the whole launcher with a different interpreter. Run
`.\local_voice_studio\setup-windows.ps1 -WithLocalAI` once to create
`.venv-voice` with Chatterbox and faster-whisper installed. Voice
Studio still opens normally without it and reports those backends as
"not ready," with the exact fix, rather than failing; its own "How
this works" panel (Project tab, inside the tool's window) and its
"diagnose" action explain the same thing.

The Dome Narration tab generates chapter WAVs, a loudness-normalized local
track, timing JSON, and SRT, then passes that existing track to the 2V exporter.
See [local_voice_studio/README.md](local_voice_studio/README.md) for setup,
privacy behavior, model downloads, licensing, and the complete workflow.

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
py -3.12 launcher.py           # consolidated GUI for every tool, or:
py -3.12 dome_creator.py       # this tool directly (fullscreen, no options)
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
