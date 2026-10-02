# Concept Inventory — *2 Trees: Build Your (D)Home*

Research deliverable. Covers the "domology / forge / park / seed / campaign tooling" side of the DomeSim repository and maps every concept onto the 71-chapter book outline (`two_v_demo/book.py`).

**Key structural finding up front:** the repo contains **two distinct book systems**, not one.

1. **`two_v_demo/book.py`** — *2 Trees: Build Your (D)Home*. 3 parts, **71 chapters**, 4 strands (`story` / `howto` / `explain` / `reference`). Part 1 "How to Build One" absorbs nine legacy parts (ch 1–52), Part 2 "Why It Scales" (ch 53–68), Part 3 "Variations and Future Systems" (ch 69–71). Every number-bearing chapter declares `derives=` callables, so the concept→chapter mapping is already *declared in code*.
2. **`domology/`** — a separate, parallel book *"Domology: the geodesic dome, the science, the journey and the build"*. 3 books in one (The Dome / The Journey / The Build), 29 chapters + front/back matter, with its own plates, worked-math sheets, typesetter, PDF/reader/reading-video pipeline. **Domology's "Journey" book is where the tool-history concepts live** (simulator, assembly line, teaching, Dome Forge, Frankendome, wedge, two-trees, corrections) — these are *not* chapters in the 71-chapter 2 Trees book.

---

## Section A — Concept inventory table

| Source | Concepts / ideas it defines | 1-line description | Visual assets produced |
|---|---|---|---|
| **domology/outline.py** | `ChapterPlan`, `BookPlan`, `FRONT`/`BOOKS`/`BACK`, `chapter_numbers()`, `chapter_tokens()` | The *Domology* book structure as data: 3 books, 29 chapters, each with purpose/target/plates/sheets; cross-refs via `{{dmch.wedge}}` tokens so insertions never break numbers. | — (drives the book) |
| **domology/build.py** | `read_chapters`, `glossary_chapter`, `numbers_chapter`, `plates_chapter`, `audit`, `build(final/publish)`, `TOKEN`/`PLACEHOLDER` | The composition engine: manuscript + code → laid-out pages; three back-matter chapters (glossary, live-numbers appendix, plate index) are *generated*; refuses a `--final` build while placeholders/author-requests remain. | interior PDF, `reader.html`, page PNGs, `layout.json`, build report |
| **domology/__init__.py + config.py** | "three books in one", `Trim`/`Grid`/`Type`, KDP rules, `LONG`/`SHORT` ink colours | The Domology package manifest and the print spec (8×10 KDP premium colour, spine/gutter computed from page count). Amber = long strut, cyan = short strut. | — |
| **domology/plates.py** | `Plate` (id/title/caption/`concept`/`change`/`tool`/recipe), tools `film|scene|forge|line|chart|composite` | Every Domology illustration as a *recipe*: a scene from a project tool with one thing changed to show one idea. ~60 named plates. | ~60 plates rendered into `deliverables/domology/plates` |
| **domology/science.py** | `Sheet`, `SHEETS` (~33 worked-math boxes), `token_specs()`, `validate_science()` | Book One's live arithmetic: each "sheet" is a worked example (phi→normalize→euler→midpoint→project→chords→counts; yield/mills/middlemen; deficit/pentagons; hub_vs_hubless; catalogue/cost). | math-sheet boxes printed in the book |
| **domology/markup.py / layout.py / pages.py / reader.py / charts.py / tables.py** | manuscript Markdown format (blocks, spans, `[[plate:]]`, `[[math:]]`, author requests), paginator, SVG/PNG/PDF pages, live reader, charts/tables | The Domology typesetting chain; same page model → PDF, HTML reader, editor, narrated reading video. | PDF + reader + reading-video page images |
| **domology/manuscript/0-front/creed.md** | **The Round House Creed** ("Every house is an argument about what a person is worth") | The project's thesis statement, printed verbatim in both books. | — |
| **two_v_demo/book.py** | `Chapter`/`Page`/`Figure`/`Part`/`Book`, `PAGE_KINDS` (11 kinds incl. `errata`, `safety`, `worked`), `STRANDS`, `derives`, `corrects`, `ref`, figure renderers (`DOME/JIG/PANEL/SHOT/PLOT/DIAG/PHOTO/HAT/MAST`), `validate_book`, source-selftest runner | The *2 Trees* outline as code: 71 chapters, strand per chapter, per-page beats, and a hard link from every figure to the code that computes it. | figure *placement* spec (pixels come from `book_figures`) |
| **dome_forge.py** | `main` → `dome_forge.cli`; "Dome Forge, the layered dome builder" | Launcher for Dome Forge, the layer/panel/cover-pattern thinking tool. | via Forge app |
| **dome_creator.py** | `PlayerCamera`, `PTZCamera`, `DomeCreatorApp`, GLSL `surface_pattern`/`hash21`, six-point 360° panorama (`azimuthal_equidistant_ray`, `sample_six_views`), `ray_triangle`, Panel Lab, construction sim, investor-demo notes | The walkable RuneScape-style **Dome Creator** simulator: parametric dome customizer, live BOM, PTZ "workshop monitoring" camera, six-point renderer. | full-screen 3D app, 360° panorama, HUD, construction animation |
| **dome_composer.py** | `main` → `two_v_demo.composer_app` | Launcher for the scene composer (furnish a round room; dome rejects what doesn't fit under the shell). | furnished dome room |
| **dome_model.py** | `GeodesicData`, `build_geodesic` (class-I, flat base), `DomeConfig`, `DomeModel` (+`.stats`, `.bom_text`), `FRAME_STYLES`, `PanelSlot`, hubless-doubled logic | The Creator's data model: icosahedron→subdivide→flatten; serializable design; live bill of materials (strut classes, weights, costs, solar watts, trees-to-harvest). | BOM text, geometry consumed downstream |
| **mesh_builder.py** | `Mesh`, `MeshBuilder`, `build_environment`, `build_dome_mesh` (construction-order + labour checkpoints), `build_avatar/worker/prop` | GPU mesh assembler; the dome is emitted in real build order with per-step `{label, hours}` checkpoints. | all 3-D geometry, build animation |
| **dflat.py / flatten.py** | flatten/`gather_files`, `DEFAULT_OUTPUT`, `PRIORITY` | Flattens the whole repo into one LLM-uploadable markdown bundle (`dome_flat.md`/`dflat.py`). | `dome_flat.md` |
| **geodesic_2v_114_views.py** | `SHORT_STRUT_IN=63.625`/`LONG_STRUT_IN=72.0`, `DomeGeometry`/`DomeBuilder._solve_ring_geometry` (Newton ring solve), `VIEWS` (114 named projections: perspective/ortho/oblique/cavalier/cabinet/cylindrical/equirect/mercator/fisheye/stereographic/gnomonic/azimuthal/conical/octahedral/reverse), `ProjectionRenderer` | Exact-length 2V solver + a 114-view drawing/projection catalogue (19 pages). | 2V wireframe, 114 projection views |
| **geodesic_raw_wedge_dome_dihedral.py** | `DomeConfig` (`panel_joint_mode="cyclic_pinwheel_butt"`, `wedge_orientation` ×4, `vertex_trim_mode`, `seam_join_mode` raw_trapezoid\|shaved_flat), `JIG_STAGES` (12), `SeamInfo` (`fold_angle_deg`, `internal_dihedral_deg`, `raw_gap_angle_deg`), `DomePhysicalModel`, `export_bom/cut_schedule/panel_jig_svg/seam_join_schedule/butt_cut_setups/fabrication_package`, `DomeWorldApp`, figure-shot cameras | **The live raw-wedge solver and 3-D world**: duplicated raw-log-sector panels, cyclic pinwheel joints, the 12-stage fabrication jig, head overfit, both seam modes; fabrication exports. | solved dome world, jig, single panel, seam lines, OBJ, CSV/SVG/HTML fabrication package, figure stills |
| **geodesic_raw_wedge_dome_single.py** | (same engine, "single-seam" edition) | Raw-wedge solver without `seam_join_mode`/jig-stage/figure-shot extras. | 3-D raw-wedge dome, jig, seam minimap |
| **seed_world.py** | `SeedPlacement`, `SHAPES`, `SEAMS`, `build_seed_frame`, `build_pad_port`, `build_utility_column`, `build_seal_cap`, `build_camera_ring`, `POLYP_SLOTS`/`build_polyp`, `DECK_STAGES`, `build_stove_dome`/`berm`/`tree_support`, `build_mast`/`build_dome_floor`/`build_float_rig`, `build_layer_stack`, `build_composite_member`, `build_seed_shell(grow_in=)`, `Crane`, `build_highway`, `build_seam_ducts`, `build_panels` | Draws the **stem-cell dome** in the Creator's mesh system from the live solver's frame: utility column, seal cap, PTZ ring, polyps, deck, stove dome, berm, tree saddle, mast, floor, floating rig (2 trees + 3 cables), exploded layer stack, removable shell, crane, highway, seam-duct network. | full seed-dome mesh + all its subsystems |
| **seed_model.py** | `SeedGeometry`, `seed_geometry()`, `ShellPlan`, `frame_group`, `pad_group`, `wet_group`, `InsulationPlan`, `SeamDuct`/`airflow_group`, `QuiltLadder`/`quilt_ladder`, `column_group`, `mast_group`, `dome_floor_group`, `suspension_group`, `CoolingLoad`, `Panel`(13)/`Module`(25)/`Fitout`(15 seeds)/`FITOUT_ORDER`, `Quote`/`quote`, `Harvest`, `DEFERMENT_LADDER` (shelter→serviced→plumbed→warm), `Joint`/`joint_hardware`, `Part`/`CORE_PARTS`/`PAD_PARTS`/`interfaces`, `SolarPlan`, `CoolingPaint`, `Lever`/`levers`, `published_check` | The **arithmetic of the stem-cell dome**: one product priced entirely from solved geometry, borrowed rates, declared inputs; the 15 named seeds; deferment ladder; floating/upgrade reports. | text reports (quote/ladder/lever/hardware/deferment/floating) |
| **seed_console.py** | `Console`/`ConsoleRenderer`/`Toolbar`, `PAGES` (quote/prices/levers/seeds), `validate_seed_console` | The seed cost calculator as an in-window Pygame overlay, editing the same `seed_model` figures. | 4 overlay pages + toolbar + CSV export |
| **park_world.py** | `PAD_STAGES`(8), `build_pad`, `_service_core`/`_pedestal`/`_utility_column`/`_sun_marker`, `build_bathhouse`, `build_service_spine`, `Park`, `default_park`, `seed_park`, `crane_for`, `SEEDS_PER_ROW` | Draws the **park** (pads, metered pedestal, service spine, bathhouse, crane, sun marker) in the Creator's mesh system. | ground/disc, pads, spine, bathhouse, crane, park mesh |
| **park_model.py** | `dome_catalogue`, `pad_sizes`/`domes_that_fit`, `Pad`(+`lease_per_month`), `HostComparison`/`host_comparison`, `Metering`, `Guarantee`, `DomeClass`/`iris_span`, `SolarLayout`, `OnPad`/`foundation_share`, `hardware_invariance`, `HousingOption`/`crossover_months`, `ShellStep`/`shell_ladder`, `basic_pad`/`standard_pad`, `park_report` | The **arithmetic of hosting a dome park**: pads, hookups, rent, metering, guarantee, tenant vs host economics, hardware invariance, foundation share, iris, solar tracking, shell ladder. | `park_report()` text + validations |
| **dome_park.py** | `DomeParkApp` (orbit/zoom, `pick`, `cycle_seed`, `swing_crane_to`, `panel_lines`, `bill_lines`), `VIEWS`/`render_shots`, `selftest` | The walkable **Dome Park** interactive tool ("an RV park for domes"). | interactive 3-D site + 7 headless stills (site/row/pad/overhead/locked/naked/lifted) |
| **soft_shell.py** | `SoftShell`/`soft_shell`, `hat_sizes`, `growth_fraction`, `Comparison`/`hard_equivalent`/`cavity_limit`/`compare`, `lifetime_usd_per_year`, `CONCERNS` | The **"shower cap"**: a soft shell that grows one quilted layer at a time, priced against the rigid hull that cannot grow. | — (geometry drawn by `seed_world`) |
| **hull_laminate.py** | `Ply`(BIAX_1708/MAT_15/…), `Laminate`+`LAMINATES` (sheathed/boatyard/marine/vinylester), `LaminatePlan`, `plan/compare/report` | The **laminated hull**: marine-composite skins costed like a boat hull by glass weight and resin-to-glass ratio. | text report |
| **quilt_network.py** | `Layer`(+`waste_years`), `stack`, `dome_totals`, `TAG_FIELDS`, `WAYS_IN`, `provenance_card` | The **quilt network**: quilted insulation as a participatory, paid, provenance-tagged object (shirts→pounds→R-value→EPA person-years). | provenance card / report text |
| **electrical.py** | `ElectricalSystem` (net watts, `charge_fraction`, `lamps_powered`), `BATTERY_KWH_EACH`, `SUN_FACTOR` | Live battery/solar/load simulation; one shared bank + charge controller ties dome 1 and dome 2. | lamp emission / charge-drain state |
| **fitout_wet.py** | `PanelFixing`/`panel_fixing` ("panels that pull in"), `WetArea`/`wet_area` ("a shower that doesn't flood"), `water_path`, `separation_ok` | Fit-out rules: threaded-insert fixing grid; kerbed two-barrier wet insert with electrical clearance. | text report |
| **workshop.py** | `RoomType`(16), `section_of` (1 hub + 9 wedges), 39 `PropType` builders, `build_partitions`, `wiring_runs`, `plumbing_runs` | Workshop fit-out: floor split into hub+wedges, room functions, parametric furniture/equipment props. | floor markings, partitions, 39 prop meshes |
| **materials.py** | `MAT_*`(14), `FrameMaterial`(8), `StrutShape`(8), `PanelType`(17), `PanelComponent`(8)+`register_custom_panel`, `LayerType`(9), `FoundationType`(7), `FRAME_COLORS`/`PANEL_COLORS` | The Creator's physical-property databases driving the live BOM. | — (data tables) |
| **site_shed.py** | `CostItem`(10), `SHED_STAGES`(9), `shed_economics`, `shed_record`, `build_shed_layers`, `validate_shed` | A conventional 24×16 gable shed, priced as a fixed <$10k benchmark independent of the dome line. | one mesh per inspection layer (9 stages) |
| **pad_deck.py** (root) | `deck(kind)` for `gravel|blocks|ring|slab`, `KINDS`, `EXTERNAL_CONSTANTS` | A dome's ground priced by *takeoff* from one lumber receipt, not by flat rate; four real constructions. | — (cost table) |
| **overlay_ui.py** (root) | `MenuItem`, `Fonts`, `render_menu`, HUD renderers | 2-D overlay widgets (menus, tabs, arrows) composited over the 3-D view. | HUD/menu overlays |
| **vision.py** (root) | `VisionTracker` (EMA object/occupancy/type counts) | Per-dome simulated object detection off the apex PTZ camera. | vision OSD / detect text |
| **kickstarter.py** | `MARGIN=0.20`, `GOAL_LINES` (12 itemised lines), `Tier`/`tiers()` (9 tiers), `CostStack`, `goal()`, `quilt_economics` | The campaign arithmetic: named 20% markup on cost; goal = sum of the list; tiers from $35 plans to $19,800 dome kit. | `report()` text |
| **campaign.py** | `AUDIENCES` (Quilters / Pad hosts / Dome owners), `ARCTIC` (pumpkin-suit story), `page()`, `validate_campaign`, `kit_numbers`/`validate_kit` | The generated Kickstarter page ("A house you can take apart"); the Arctic layering story; the shower-cap metaphor; three audiences in one campaign. | `deliverables/campaign/campaign-page.md`, handoff kit table |
| **campaign_schematics.py** | `ViewGeometry` (crown point / hourglass / lower star heights+radii, `fold_long_deg`/`fold_short_deg`, `seam_v_long_deg`), `view_geometry`, `check_view_geometry` | Orthographic/multi-view sheets for each build concept, read off the 2V mesh (not a generic dome idea). | multi-view schematic sheets |
| **campaign_prompts.py** | `STYLE_BRICK` ("premium building-brick set"), `words()`/`about()` (numbers→words), `dome_truth` row-by-row block, `validate_prompts` | Image prompts for the campaign, written from the model; **no digits in any prompt** (figures are overlay copy set in type). | `deliverables/promo/stem-cell-campaign-prompts.md` |
| **frankendome_hype.py / frankendome_masterclass.py** | `main(default_lesson="hype"/"franken")` | Launchers for the Frankendome montage (hype/argument) and the franken-dome build lesson. | montage / lesson films |
| **geodesic_wedge_presentation.md** | radial-wedge argument, "divide the circle instead of inscribing rectangles", NAHB 2024 cost data, 33-week construction clock, 2021 lumber spike, regulatory cost, "rectangles are not mandatory" | The full *Why Radial Log Wedges* investor presentation, with source notes. | — (script for the presentation) |
| **presentation.txt** | "weaponized 2V dome" brief (grok + gemini outputs, 12 disruption arguments) | An earlier AI-generated disruption framing of the 2V dome (material efficiency, resilience, modularity, code arbitrage, etc.). | — |
| **prompt.txt** | "$1500/1000 bdft lumber", "compare board feet wedged vs milled", "remove 'weaker stick in bending'" | Author editing notes for the presentation. | — |
| **2v-masterclass-narration.md** | 14-chapter 2V masterclass script (phi→icosahedron→midpoint→projection→two chord factors→cut list→build sequence→close the loop) | The narrated 2V geometry lesson. | — (script for `2v-masterclass.mp4`) |
| **dome_flat.md** | (flattened bundle of the whole repo) | The single-file project dump for LLM context. | — |
| **geodesic_2v_multiview (1).py** | multi-view 2V renders | Multi-view sheet generator for the 2V dome. | multi-view PNGs |

---

### A.1 — Campaign specifics (exact live figures and language, model v7)

**The product: the "stem cell".** Tagline: *"We make the stem cell. You build on it."* / *"A house you can take apart."* / *"A gym on Monday, a guest room on Friday."* The stem cell is one solved 2V frame (19.4 ft diameter, 40 bays, 120 members) wearing any of **15 named seeds** — `stem_cell, home, food, advertiser, storage, bunker, treehouse, sauna, gym, guest, workshop, garage, studio, nursery, jacuzzi` — via snap-in panels + modules. All 15 are one cut list.

**Price stack (live):** stem cell (shower cap) **$12,036** = $10,030 build + $2,006 profit (**20% markup on cost**, stated on camera), **$43.45/sq ft**; laminated hull **$21,513**; one quilt layer **$50**; mast + floor + rig **$4,011**; host's pad **$6,240**; dome + ground standing **$18,276**; campaign **goal $110,000**. (Superseded figures $18,834 / $30,477 survive only in `docs/seed-dome-brief.md`.)

**Reward tiers (9):** $35 plans · $95 quilter's kit · $180 one-bay hardware set · $1,450 shower cap · $2,400 utility hub · $19,800 dome kit (frame included) · $11,400 dome kit (bring your own trees) · $640 pad host's pack. The 12-line goal breakdown (test platform $4,200 → engineering $6,800 → strut tooling $18,000 → composite R&D $12,500 → …) sums to $110,000.

**"Hatch" (the term the brief asked about):** the **serving hatch** — a food-truck window panel (~$780), part of the `food` seed — plus **under-floor storage hatches** on the host's pad. (A separate *watertight* hatch door exists only in the Dome Creator assembly-line project, not the campaign.)

**The Arctic story / shower cap:** the owner's Navy lookout story — *a dome is a head, and it wears hats; one waterproof cap over dry layers; exactly one watertight layer in the building* — is the campaign's central analogy (the "pumpkin suit").

**Three audiences, one campaign:** Quilters (sew recycled clothing → insulation), Pad hosts (own land, build a serviced platform, no landlord), Dome owners (have trees, or don't).

**The 14 builder concepts** (`campaign_schematics.py`), each a multi-view sheet: `dome · lengths · wedge · seam · junctions · bay · column · pad · interface · layers · polyp · floor · rig · network`.

**Image-pack look** (`campaign_prompts.py`): 15 sections (hero → manual → schematics → core → platform → layers → seam channel → rig → wood/network → fit-outs → panel icons → tier graphics → goal lines → social → book/web → motion); styles `brick / manual / schematic / photo / icon`; mascot **Lumen** (low-poly glowing jellyfish); **no digits in any prompt** (figures are overlay copy). Colour key (identical everywhere): LONG = warm tan, SHORT = honey-caramel, **owner's hardware = cyan-teal**, **host's hardware = amber** `#FFB13E`, services = power-yellow / water-blue / drain-grey. **Banned phrases** (check-enforced): `frankendome, revolutionary, game changer, no mitre, two people can carry`.

**Frankendome hype** (`frankendome_hype.py` montage): *"THE FRANKENDOME IS HAVING A PARTY"* / *"120 struts, no two alike, held by folded sheet metal."*

---

## Section B — Concepts mapped to the 2 Trees book (71 chapters)

### How the mapping is declared
`book.py` already pins concept→chapter via each chapter's `derives=` tuple and figure `source=`. The table below reproduces that *and* adds the concepts that are not yet in the outline.

### B.1 Concepts that map cleanly (existing chapters)

| Concept (source) | 2 Trees chapter | Strand |
|---|---|---|
| Book tree / measured trunk (`book_math.BOOK_TREE`) | 1 The Tree That Was Already Down | story |
| Fifteen-middlemen supply chain; nominal vs dressed 2×4 (`book_math.NOMINAL/DRESSED`) | 2 Fifteen Middlemen | explain |
| Frankendome, hubless shared edges, ten-piece pentagon (`hubless_geometry.hubless_summary`) | 3 The Frankendome | story |
| V-bracket tolerance (struts of unlike section) | 4 The V-Bracket Afternoon | story |
| The wedge cut — 3 passes, 8 sectors (`wedge_geometry.SECTORS_PER_LOG`, `sector_chord/depth`, recovery) | 5 The Cut That Changed It | story |
| Triangulation = axial load = section shape is a detail (`bearing_area_in2`) | 6 Triangles Do Not Care What Shape Your Stick Is | explain |
| Wedge vs board (area vs bending; stiffness/strength deficit) (`wedge_versus_board`, `sector_section`, `board_section`) | 7 Not a Worse Two-by-Four | explain |
| 2V hemisphere counted (40 panels / 120 members / 65 edges) (`frame_counts`, `panel_seam_count`) | 8 Forty Panels, One Hundred and Twenty Members | explain |
| Two lengths → four classes via pinwheel (`wedge_geometry.member_classes`) | 9 Two Lengths, Not Forty | explain |
| Compression/tension; end-to-side bearing (`bearing_area_in2`) | 10 Compression, Tension, and One Eighth of a Tree | explain |
| Honest dome cost; round-room fit-out penalty (`dome_costing.costing_report`) | 11 What a Dome Costs You | explain |
| Split like a cake; why 8 not 6/12 (`SECTORS_PER_LOG`, `sector_area/chord`) | 12 Split Like a Cake | howto |
| Recovery arithmetic; 88→87 erratum (`tree_yield`, `section_rows`) | 13 Eighty-Seven Percent | explain |
| Four wedge orientations (`raw_wedge_bridge.orientations`, `seam_pair_reading`) | 14 Four Ways Up | explain |
| Pinwheel (end-to-side, no mitre); mitre erratum (`pinwheel_panels`) | 15 The Pinwheel | explain |
| Seam & key; fold angles; raw trapezoid vs shaved flat (`gasket_plan`, `raw_wedge_bridge.model`) | 16 The Seam and Its Key | explain |
| Connector holds the angle; precision in the small part (`shaving_plan`) | 17 Let the Connector Hold the Angle | explain |
| Every panel keeps its own edge (120 members / 65 edges, seam sandwich) (`edge_accounting`) | 18 Why Every Panel Keeps Its Own Edge | explain |
| Bends/knots/small units; supply-chain-as-handling (`BOOK_TREE`) | 19 Bends, Knots and Small Units | explain |
| Choose your method; radius↔member-length (`longest_member_in`, `radius_for_member_length`) | 20 Which Way Round Are You Working? | howto |
| Method A (floor first) (`design_first`, `design_first_for_floor`) | 21 Method A: From the Dome You Want | howto |
| Method B (tree first); two trees = 120 struts (`tree_first`) | 22 Method B: From the Tree You Have | howto |
| Round trip closes (`round_trip`) | 23 The Round Trip | explain |
| Worked build reference tables (`book_math_report`) | 24 The Worked Build | reference |
| When the numbers say no (`tree_first`, `design_first`) | 25 When the Numbers Say No | howto |
| Day zero: the $199 saw (`DECLARED`) | 26 Day Zero: The Saw | story |
| Felling (notch/back cut/hinge) | 27 Days One and Two: Felling | howto |
| Bucking (`BOOK_TREE` sections) | 28 Days Three and Four: Bucking | howto |
| Ripping; struts/hour (`fortnight`) | 29 Days Five to Eight: Ripping | howto |
| The jig (`raw_wedge_bridge.jig_stages`) | 30 Day Nine: The Jig | howto |
| Forty panels; 12 jig motions (`jig_stages`, `model`) | 31 Days Ten to Twelve: Forty Panels | howto |
| Raising; bottom ring first (`frame_counts`) | 32 Days Thirteen and Fourteen: Raising | howto |
| One bench reference; locate-from-sawn-faces (`jig_stages`) | 33 One Bench, Forty Panels | reference |
| The butt cut = the one compound cut (`model`) | 34 The Butt Cut | reference |
| Head overfit (overshoot, pull tight, flush cut) (`DECLARED`, `model`) | 35 The Head Overfit | reference |
| Flush-cutting in place (`jig_stages`) | 36 Flush-Cutting in Place | reference |
| Panel drawings (`model`) | 37 Panel Drawings | reference |
| Tolerance budget; error goes to offcut (`tolerance_budget` diagram) | 38 Where Error Goes | explain |
| Footing & ring; uplift ("a dome is a wing") | 39 The Footing and the Ring | howto |
| Closing the shell; nesting sheet goods (`dome_costing.shell_sqft`) | 40 Closing the Shell | howto |
| Doors/windows/rim; risers (`openings` diagram) | 41 Doors, Windows and the Rim | howto |
| Weather & water; shedding not sealing; harvesting (`panel_seam_count`) | 42 Weather and Water | howto |
| Inside a round room; headroom map (`tree_first`) | 43 Inside a Round Room | explain |
| Heat/power/small systems; insulate between wedges | 44 Heat, Power and the Small Systems | howto |
| Money both ways; $50/hr erratum (`fortnight`, `BOOK_TREE`) | 45 The Money, Both Ways | reference |
| The hours (`fortnight`) | 46 The Hours | reference |
| What broke | 47 What Broke | story |
| Corrections (mitre, 88/87, hourly, seams-vs-edges) (`frame_counts`, `panel_seam_count`, recovery) | 48 Corrections | reference |
| Frequencies 1V–4V; member classes (`member_classes`) | 49 Bigger, Smaller, Other Frequencies | explain |
| Other species/sections; oval trunk; green vs dry | 50 Other Species, Other Sections | howto |
| Building with other people; parallel jigs | 51 Building With Other People | howto |
| What I would do differently | 52 What I Would Do Differently | story |
| **Flat rate** — parts list does not grow with diameter (`franken_economics.flat_rate_table`, `solo_band`, `SOLO_LIMITS`) | 53 The List That Does Not Grow | explain |
| **Nine processes** (`franken_economics.PROCESSES`, `DomeSize`; rip payback) | 54 Nine Processes at Any Size | explain |
| **Hour at the log** — strut valued 3 ways (`book_math.fortnight`, `EXTERNAL_PRICES`) | 55 What an Hour at the Log Is Worth | explain |
| **Metabolic ledger** — mechanical vs metabolic work; fastening surprise (`energetics.build_energy`) | 56 Where the Fuel Actually Goes | explain |
| **Less skin** — dome vs box envelope, crossover (`dome_advantage.*`) | 57 Less Skin for the Same Floor | explain |
| **Pony wall** — cheapest square footage (`dome_performance.pony_wall_ladder`) | 58 The Cheapest Square Footage in the Building | explain |
| **Brim as gutter** — water catch (`dome_performance.WaterCatch`, `hat_rim_radius_ft`) | 59 The Roof Is Already a Gutter | explain |
| **Shell ladder** — warmer every winter (`park_model.shell_ladder`, `running_costs`) | 60 A House That Gets Warmer Every Winter | explain |
| **Hardware invariance** — one bracket set, three sizes (`park_model.hardware_invariance`, `dome_catalogue`) | 61 One Hardware Set, Three Sizes | explain |
| **Growth path** — buy for next two steps (`housing_options`, `crossover_months`) | 62 Buy for the Next Two Steps | explain |
| **Foundation share** — ground you can't take with you (`foundation_share`, `on_pad`) | 63 The Ground Is What You Cannot Take With You | explain |
| **The pad** — pad vs plot; gravel/concrete/wood (`Pad`, `pad_sizes`, `cheap_pad_*`) | 64 A Pad, Not a Plot | explain |
| **Solar tracking rotation** (`solar_layouts`, `steps_solar`) | 65 Turning the House Toward the Sun… | explain |
| **Iris pad** — one pad, every size (`iris_span/covers/cost`, `domes_that_fit`) | 66 One Pad, Every Dome Size | explain |
| **Network vs park** — host/tenant, resale (`host_comparison`, `tenant_utilities`) | 67 Why a Network Beats a Park | explain |
| **Honest limits** — every claim restated as a condition (`house_economics`, `dome_performance.ten_points`, `lexicon_concepts.CONCEPTS`) | 68 What Would Have to Be True | explain |
| **Soft shell / stacking hats** (`soft_shell.soft_shell/compare/cavity_limit`, `seed_model.quote`) | 69 The Dome That Stacks Hats | explain |
| **Mast & floor** (`seed_model.mast_group`, `dome_floor_group`, `frame_weight_lb`) | 70 The Mast and the Floor | explain |
| **Floating dome** (`seed_model.suspension_group`, `floating_report`) | 71 The Floating Dome | explain |

### B.2 Concepts that live in *Domology*, not in the 71-chapter book (cross-reference)
These are the "journey/tool" concepts. In the 2 Trees book they appear only in the back-matter chapter **"The Software in This Book"**. If the author wants them as full chapters, they are Domology's Book 2:

| Concept (source) | Domology chapter |
|---|---|
| The simulator / Dome Creator / 12 presets (`dome_creator`, `dome_model`, `presets`) | "A Dome in Software First" (simulator) |
| The Dome Home Assembly Line — 15 stations, 4 products (`assembly_line.py`, `al_build.py`) | "The Factory Line" |
| The masterclass engine + from-scratch lesson + "computed numbers" rule | "Teaching the Geometry to Myself" |
| Dome Forge, hubless triangles, jig shop, cover patterns, nesting (`dome_forge`, `dome_forge.patterns`) | "Dome Forge and the Water Dome" |
| The water dome — dished panels, micro-drains, seam veins, collector ring, cistern | "Dome Forge and the Water Dome" + Book 1 "Wind, Water and Weight" |
| Angular deficit, Descartes' 720°, pentagons, darts | Domology Book 1 "The Missing Fifteen Degrees" |
| Hex / zome / higher frequencies / dome family | Domology Book 1 "The Dome Family" |

### B.3 NEW CHAPTER CANDIDATES (concepts genuinely absent from the 71 chapters)

Only four concepts have no home. Each is proposed with a title, strand, and placement.

1. **"The Stem-Cell Dome"** *(strand: `explain`; place in Part 3 "Variations and Future Systems", before ch 69 — or as the opener of a future Part 4).*
   The campaign's core product concept: one solved 2V frame, one cut list, wearing any of **15 named seeds** (`stem_cell, gym, studio, nursery, guest, workshop, garage, home, sauna, food, advertiser, storage, bunker, treehouse, jacuzzi`) via snap-in panels + modules. The existing book has "frequencies" (49) and "hats/mast/floating" (69–71) but never says *the same frame is fifteen different buildings*. This is what makes the "network beats a park" argument (ch 67) concrete — the seed is the portable unit.
   *Source: `seed_model.Fitout`/`FITOUT_ORDER`, `seed_world`, `campaign.py`.*

2. **"The Quilt Network"** *(strand: `explain`; place in Part 2 "Why It Scales", beside ch 60).*
   Insulation as a **participatory, paid, provenance-tagged** object: ~132 t-shirts per layer, R-value per layer, EPA person-years of diverted textile waste, "three ways in," a tag card every dome keeps. ch 60 covers *adding* layers; ch 69 covers the *cap*; neither covers the *social mechanism* by which a stranger makes and gets paid for the insulation — the part that turns the building into a recruiting engine.
   *Source: `quilt_network.py`, `kickstarter` quilter tier, `campaign.py`.*

3. **"The Utility Hub and the Seal Cap"** *(strand: `reference`; place beside ch 44 or in Part 3).*
   The one part an owner cannot make — pad port → water manifold → drain stack → sub-panel → riser → seal cap — priced as a manufactured part (the campaign's **$2,400 "core" tier**), and the claim that **the apex is an interface, not a roof** (four joints + a lift to unhook a dome). ch 44 treats services generically; ch 70 treats the mast; neither names the hub as a *product*.
   *Source: `seed_model.column_group`/`interfaces`, `seed_world.build_utility_column`/`build_seal_cap`, `kickstarter` "core".*

4. **"The Site Shed Benchmark"** *(strand: `reference`; back-matter table or a sidebar beside ch 11/45).*
   A conventional 24×16 gable shed, priced stage-by-stage under $10k as a fixed, inspectable comparison anchor, deliberately independent of the dome line. The book compares against houses and 2×4s but has no *single fixed small building* a reader can check the dome against.
   *Source: `site_shed.py`.*

*(Not proposed: the "weaponized 2V" disruption framing in `presentation.txt` is campaign rhetoric the book deliberately rebuts in ch 11 and ch 68; the PTZ/vision/electrical simulator features and the 114-view projection catalogue are software/reference material for back matter, not chapters.)*

---

## Section C — Visual assets for the book's figure plan

### C.1 The book's own rendered figure set (highest value)
- **`deliverables/book/figures/`** — **138 PNG + 2 SVG**, versioned, the actual *2 Trees* figure set, organised by subject (frame/strut, seam/skin, jig/joinery, trees/logging, numbers/tables). These are the figures `book.py` places by key.
- **`deliverables/book/`** — **37 PDF** (three compiled books: `the-40-hour-cabin`, `the-wedge-method`, `2-trees` + KDP print versions), **10 cover PNG+PDF pairs**, plus HTML/MD/TXT sources.

### C.2 Chapter stills (usable as figure candidates / captions)
- **`deliverables/releases/`** — **515 files across 24 film cuts**: **448 chapter-thumbnail JPGs** (each with a descriptive caption slug), 24 `description.md`, 22 `video.txt`, 21 `.srt`.

### C.3 Domology plates (~60 named, render into `deliverables/domology/plates`)
Key plates by subject (full list in `domology/plates.py`):
- **Geometry:** `creator-lineup` (12 domes), `rigidity`, `force-panel`, `classes-colored`, `platonic`, `ico-coordinates`, `midpoints`, `projection`, `chart-frequency`, `classes-dome`, `cutlist`, `forge-deficit`, `forge-pattern`, `hex-deficit`.
- **Joinery:** `hub-dome`, `forge-hubless`, `compound-cut`, `forge-waist`, `forge-pentagon`, `forge-jig-shop`, `jig-panel`, `jig-stages`, `pinwheel`, `panel-corner`, `panel-drawing`, `flush-cut`, `gasket`, `keystone`, `fold`, `buttcut`, `wedge-stick`, `wedge-section`.
- **Water dome:** `forge-water`, `forge-rain`, `forge-veins`, `forge-layers`.
- **Economics:** `chart-skin`, `chart-comparison`, `creator-economics`, `why-dome`, `chart-house`, `pine-ladder`.
- **Journey:** `creator-homestead` (Split-Log Homestead), `creator-trunk` (Whole Trunk Lodge), `line-frame`, `line-services`, `line-interior`, `scratch-pipeline`, `math-screen`, `franken-bracket/triangle/slack`, `wedge-split/round/orient/chain`.
- **Build:** `harvest-fell/buck/pile/explode`, `solved-dome`, `method-dome`, `dome-top`, `foundation`, `riser`, `raise`, `apex`, `assemble`, `skin`, `openings`, `look-room`, `line-interior-room`, `check`, `error`, plus dividers/frontispiece.

### C.4 Raw tool stills and shots
- **`dome_forge_shots/`** — 57 PNG (Forge UI stills, accessibility/wheelchair, jig, pattern sequences).
- **`snapshots/`** — 9 PNG (`dome_*` simulator shots).
- **`shots/dome_park/`** — 4 PNG (overhead/pad/row/site).
- **`galleries/general/`** — 50 JPEG + 50 `.info.json` (AI-generated gallery).
- **`deliverables/figures/`** — `2v-72in-ring-levels.png`.

### C.5 Hero images / covers / key diagrams (repo root)
- **Book covers:** `Book_Cover.jpg`, `Book_Cover_final.png`, `Book-Cover-Final(-2/3/4).png`, `book-cover-asyma.png`, `Book-Cover-Final2.png`.
- **Campaign art:** `Frankendome-kickstarter.png`, `FrankenDomeCover.jpg`.
- **Key diagrams:** `channel.png` (the channel/seam), `rings-render.png`, `2v_dome_joinery_options_guide.png` (joinery options guide), `dome1.png`, `seam.png`, `wedges-edges.png`.
- **AI cover candidates:** 12 `Gemini_Generated_Image_*.jpg`, 8 `ChatGPT Image *.png`, 1 Codex image, 1 `Gemini_Generated_Image.jpeg` (dated 2026-09-20→27).

### C.6 Videos (for a "films that go with each chapter" appendix)
- **~225 `.mp4` total.** Masterclass (`masterclass/`) = **76 finished films** (landscape + phone cuts); `teasers/` = **78 short teasers**; `presenter/` = **13 `dome_case_*` clips**; `launcher_trailer/` = 2; `byod(+deepseek/styled)/` = **10 "bring your own dome" exports**; `tree-value-video/` = 1 main + 26 chapter clips.
- **Root exports:** `2v-masterclass.mp4`, `testo.mp4`, `ks-gemini.mp4`, `Stem_cell_dome_campaign_i.mp4` (+dup), `Create_a_highly_detailed_anima.mp4`, `2v-masterclass-silent-backup.mp4`.
- **`deliverables/` root:** `the-seam-does-four-jobs.mp4` (+ `-vertical`), `.m4a`, `.srt`.

---

*Inventory produced from: `domology/*` (outline, build, plates, science, config, creed), `two_v_demo/book.py` (full 71-chapter outline), the geometry/tool files, the seed/park/world files, the campaign/presentation files, and directory enumeration of the render folders.*
