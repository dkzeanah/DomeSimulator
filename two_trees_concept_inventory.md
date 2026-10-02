# 2 Trees: Build Your (D)Home — Video-Lesson / Rendering Concept Inventory

A complete inventory of every distinct concept, method, number, tool, scene, and
argument that lives on the **video-lesson / rendering** side of DomeSim, mapped
against the book outline in `two_v_demo/book.py` (chapters 1–71).

Sources read in full or introspected at the `Lesson`/`Chapter` object level:
`two_v_demo/lessons.py` (the 2V masterclass — *note: the task's "two_v_masterclass.py"
does not exist; the 2V masterclass is `TWO_V_LESSON` in `lessons.py`)*,
`two_v_demo/lesson_registry.py`, every `lesson_*.py`, `segments.py`, `beats.py`,
`score.py`, `cabin_world.py`, `render_presets.py`, `presets.py`, and the seven
concept/economics modules. Stills archive: `two_v_demo_output/` (914 stills, one
subdirectory per lesson).

---

## The book's 71-chapter spine (for mapping)

* **Part 1 "How to Build One"** = absorbed legacy parts I–IX (chapters 1–52).
* **Part 2 "Why It Scales"** = chapters 53–68 (the argument for scale).
* **Part 3 "Variations and Future Systems"** = chapters 69–71.

| # | Title | # | Title |
|---|---|---|---|
| 1 | The Tree That Was Already Down | 37 | Panel Drawings |
| 2 | Fifteen Middlemen | 38 | Where Error Goes |
| 3 | The Frankendome | 39 | The Footing and the Ring |
| 4 | The V-Bracket Afternoon | 40 | Closing the Shell |
| 5 | The Cut That Changed It | 41 | Doors, Windows and the Rim |
| 6 | Triangles Do Not Care… | 42 | Weather and Water |
| 7 | Not a Worse Two-by-Four | 43 | Inside a Round Room |
| 8 | Forty Panels, 120 Members | 44 | Heat, Power and the Small Systems |
| 9 | Two Lengths, Not Forty | 45 | The Money, Both Ways |
| 10 | Compression, Tension… | 46 | The Hours |
| 11 | What a Dome Costs You | 47 | What Broke |
| 12 | Split Like a Cake | 48 | Corrections |
| 13 | Eighty-Seven Percent | 49 | Bigger, Smaller, Other Frequencies |
| 14 | Four Ways Up | 50 | Other Species, Other Sections |
| 15 | The Pinwheel | 51 | Building With Other People |
| 16 | The Seam and Its Key | 52 | What I Would Do Differently |
| 17 | Let the Connector Hold the Angle | 53 | The List That Does Not Grow |
| 18 | Why Every Panel Keeps Its Own Edge | 54 | Nine Processes |
| 19 | Bends, Knots, Small Units | 55 | What an Hour at the Log Is Worth |
| 20 | Which Way Round | 56 | Where the Fuel Actually Goes |
| 21 | Method A | 57 | Less Skin for the Same Floor |
| 22 | Method B | 58 | Cheapest Square Footage |
| 23 | The Round Trip | 59 | Roof Is Already a Gutter |
| 24 | The Worked Build | 60 | House That Gets Warmer |
| 25 | When the Numbers Say No | 61 | One Hardware Set Three Sizes |
| 26 | Day Zero: The Saw | 62 | Buy for the Next Two Steps |
| 27 | Days 1–2: Felling | 63 | Ground You Cannot Take With You |
| 28 | Days 3–4: Bucking | 64 | A Pad Not a Plot |
| 29 | Days 5–8: Ripping | 65 | Turning the House Toward the Sun |
| 30 | Day Nine: The Jig | 66 | One Pad Every Dome Size |
| 31 | Days 10–12: Forty Panels | 67 | Why a Network Beats a Park |
| 32 | Days 13–14: Raising | 68 | What Would Have to Be True |
| 33 | One Bench, Forty Panels | 69 | The Dome That Stacks Hats |
| 34 | The Butt Cut | 70 | The Mast and the Floor |
| 35 | The Head Overfit | 71 | The Floating Dome |
| 36 | Flush-Cutting in Place | | |

---

# Section A — Lesson / Film inventory

Every registered film. Key = registry key; "core concepts" = what the film
actually teaches/argues; "notable scenes" = scene functions worth turning into
book figures (scene names come straight from each lesson's `scenes` dict and
`Chapter.stage`). Marketing montages that repeat content are compressed to their
deltas.

## Teaching masterclasses (the book's source material)

### `2v` — "2V Geodesic Masterclass" (brand: 2V / GEODESIC MASTERCLASS)
*File: `lessons.py` (TWO_V_LESSON). 14 chapters.*
- **Core concepts**: phi places the icosahedron's 12 corners (not the strut ratio);
  triangulation → axial tension/compression; 5 Platonic solids; normalize to a unit
  sphere; midpoint subdivision leaves points *inside* the sphere; radial projection
  creates the second length; 120 edges collapse to exactly 2 classes (SHORT/LONG);
  chord factors (SHORT≈0.5465·R, LONG≈0.6180·R); four routes to the same number
  (coordinates / dot product / central angle / law of cosines); least-squares radius
  fit from two measured boards (72″ and 63.5″); centre-length ≠ cut-length
  (connector deduction); hemisphere = 65 edges, 40 faces; measurement loop.
- **Notable scenes** (`hero`, `rigidity`, `platonic`, `coordinates`, `icosahedron`,
  `midpoints`, `projection`, `classes`, `derivations`, `audit`, `cutlist`,
  `assembly`, `verification`, `finale`): the icosahedron on a unit sphere, the
  projection step that "creates the second strut length", the two-colour chord
  classes, the audit of two real boards.

### `build` — "2V Dome Construction Masterclass" (2V / DOME CONSTRUCTION, START TO FINISH)
*File: `lesson_build.py` (BUILD_LESSON). 46 chapters.*
- **Core concepts**: the full 2V build — five words (hub, strut, panel, chord
  factor, frequency); why triangles; icosahedron → subdivision → projection; radius
  choice (floor ∝ r², volume ∝ r³); the dome is 4 rings + a crown (26 hubs); audit
  boards by least squares; choose the hub system before anything (deduction decides
  every cut); end-cut angle = half the central angle; only 2 fold angles; 5 hub
  types; stock nesting (8′ vs 16′ yield); stop block + master gauge; cut list
  (30 short + 35 long); subassembly flat on the ground; set out the base decagon
  from centre, check diagonals; foundation (piers / ring beam / slab); **riser wall**
  (cheapest headroom); raise in complete rings (never one side); close the crown
  (last hub = honest test); error in a 10-sided ring amplifies by phi (⅛″ → φ·⅛″);
  measurement loop (member→triangle→ring→radius→height); skin rim-upward; openings
  take whole panels; the four real failure modes (guessed deduction, unlevel base,
  one-sided raising, forced apex); **hubless intro** (40 closed triangles, no hubs);
  why 120 struts not 65; the compound cut; mitre saw runs out of scale (needs
  55.5°–62°, saw stops ~50°); the "breathing wall" air-tube digression; 40 panels
  nested on one 10×5′ sheet (a sub-$2,000 storm shelter); franken-dome recap.
- **Notable scenes** (37 painters: `build_finished`, `build_vocab`, `build_rings`,
  `build_size`, `build_deduction`, `build_endcut`, `build_bevel`, `build_hubs`,
  `build_hubkit`, `build_stock`, `build_jig`, `build_layout`, `build_foundation`,
  `build_riser`, `build_subassembly`, `build_raise`, `build_apex`, `build_error`,
  `build_check`, `build_skin`, `build_openings`, `build_failures`, `build_hubless_*`,
  `build_air_*`, `build_shelter_*`, `build_franken_*`): the "one eighth of an inch ×
  golden ratio" diagram, the ring-by-ring raising, the two triangle families flat on
  the ground, the mitre-saw protractor showing settings past the stop.

### `cuts` — "The Compound Cut, Both Machines" (HUBLESS / THE COMPOUND CUT)
*File: `lesson_cuts.py` (CUTS_LESSON). 18 chapters.*
- **Core concepts**: every hubless strut carries two independent angles (bevel along
  length + mitre at ends); table saw rips, mitre saw crosscuts — two machines;
  rip one width in one session; mark the mating edge; never trust the saw's cast
  scale; prove the tilt with two offcuts (reads 2× the error); the mitre saw runs
  out of scale (~50° stop vs 55.5°–62° needed); **complement angle** (62° from
  square = 27.8° from the blade); the crosscut sled; the **five-cut method**;
  the relief lap (fence cut away at the blade); first end then **turn, don't flip**;
  batch by setting (6 setups cover 240 ends); dry-fit one triangle; the five ways it
  goes wrong.
- **Notable scenes**: `cut_two_angles`, `cut_machines`, `cut_rip`, `cut_bevel_check`,
  `cut_mitre_limit`, `cut_complement`, `cut_sled_build`, `cut_fivecut`, `cut_lap`,
  `cut_first_end`, `cut_turn`, `cut_batch`, `cut_dryfit`, `cut_failures`, `cut_recap`.

### `hex` — "Hexagonal Dome Masterclass" (HEX / HEXAGONAL DOME MASTERCLASS)
*File: `lesson_hex.py` (HEX_LESSON). 20 chapters.*
- **Core concepts**: hexagon = most area per edge that still tiles; a sheet of
  hexagons cannot curve (3 × 120° = 360°, no deficit); curvature is bought with
  *missing angle* (cone from a cut disc); a pentagon subtracts 36°; Descartes'
  theorem → **exactly twelve pentagons, always**; the truncated icosahedron (soccer
  ball: 20 hexagons, 12 pentagons, 90 identical struts); one strut length cut 90×;
  two flat templates cut all 32 panels; a hex cage has no level equator → zigzag
  rim; the dual (triangle corners → panels); Goldberg subdivision splits one strut
  length into two; the size ladder (2,4,6 strut lengths); subdivided hexagon panels
  are **warped** (6 points on a sphere don't share a plane); warp cost measured at
  20′; 3-way seams at every hub point uphill; choose: repeated work is cheap, varied
  work is where mistakes live.
- **Notable scenes**: `hex_flat`, `hex_flat_angle`, `hex_deficit` (disc loses a wedge,
  rises into a cone), `hex_pentagon_swap`, `hex_euler`, `hex_soccer`,
  `hex_soccer_struts`, `hex_soccer_panels`, `hex_soccer_cut`, `hex_soccer_build`,
  `hex_dual` (triangulated dome → hexagon cage), `hex_two_struts`, `hex_size_ladder`,
  `hex_warp` (one hexagon lifted off its best-fit plane), `hex_warp_cost`,
  `hex_compare`, `hex_skin`, `hex_choose`, `hex_finale`.

### `zome` — "Zome Construction Masterclass" (ZOME / ZONOHEDRON MASTERCLASS)
*File: `lesson_zome.py` (ZOME_LESSON). 19 chapters.*
- **Core concepts**: a zome is swept from a star of directions, not cut from a
  sphere; point→stick→panel→solid sweep; every panel flat by construction (2
  directions define a plane); equal directions → rhombus → one strut length; the
  star + pitch angle; part counts as formulas in n; the apex closes at a point; hubs
  land on level rings (no tape); panel templates by angular separation; pitch is the
  free design knob; several hub types (not interchangeable); no horizontal strut but
  one repeated floor cut; the golden zome = rhombic triacontahedron (30 identical
  rhombi, diagonals on phi) and its uneven-ring cost; raise tier by tier; openings
  take whole rhombi; zome vs geodesic (both close, different reasons).
- **Notable scenes**: `zome_sweep`, `zome_parallelogram`, `zome_rhombus`, `zome_star`,
  `zome_counts`, `zome_apex`, `zome_rings`, `zome_shapes`, `zome_pitch`, `zome_hubs`,
  `zome_floor`, `zome_cutlist`, `zome_golden`, `zome_golden_cost`, `zome_raise`,
  `zome_openings`, `zome_versus`, `zome_finale`.

### `line` — "Assembly Line Energy Masterclass" (ASSEMBLY LINE / THE ENERGY LEDGER)
*File: `lesson_line.py` (LINE_LESSON). 24 chapters. Backed by `energetics.py`.*
- **Core concepts**: the Iris-25 (4.39 m, 4V) = 1,322 parts, 16,751 kg, 15 stations,
  2 workers each; a line buys *less waiting*, not less work (158 h solo → 30 h/unit);
  bottleneck = slowest station (frame); the six motions (walk, lift, carry, position,
  fasten, recover — 493 s, 41.1 kcal/placement); Pandolf's 1977 load equation
  (carrying is super-linear in load); overhead work >1.75 m; **fastening raises
  nothing but spends ~90% of the fuel**; PFD allowance (recovery, ~15%); Winter's
  anthropometric tables (82 kg body, per-segment mass); "you are the heaviest thing
  you lift"; trunk does 65% of lift work; 23 kg single-person lift limit;
  m·g·h is the exact part (622 J for one part); kilocalories are a *model*, not
  measured; 19% efficiency during the lift vs 0.16% across the whole dome;
  54,870 kcal/worker total; 2,298 kcal/day at 3.50 METs (ceiling ~350 W sustained);
  109,741 kcal total ≈ 1,372 slices of bread; "design the posture, not just the part."
- **Notable scenes**: `line_overview`, `line_why`, `line_station`, `line_bottleneck`,
  `line_cycle`, `line_walk`, `line_lift` (limbs coloured), `line_carry`,
  `line_position`, `line_fasten`, `line_allowance`, `line_skeleton`, `line_selflift`,
  `line_limbs`, `line_team`, `line_overhead`, `line_work` (mgh), `line_model`,
  `line_efficiency`, `line_motions`, `line_stations`, `line_shift`, `line_food`,
  `line_recap`.

### `franken` — "The Franken-Dome" (FRANKENDOME / MIXED STOCK)
*File: `lesson_franken.py` (FRANKEN_LESSON). 21 chapters. Backed by `franken_economics.py`.*
- **Core concepts**: 120 struts, no two alike (an experiment, not a recommendation);
  round/quarter-sawn/wedge/square/rectangular stock mixed; the **V-bracket** from a
  folded strip of washing-machine casing (8 holes, one fold); one triangle = 3
  sticks, 3 brackets, 24 screws; nothing lands on the sphere (green geometry vs red
  as-built); the frame **settles** and shares error out (every triangle rigid, so
  error is redistributed); monolithic skin bridges remaining slack; four trees
  borrowed the load; ledger (120 brackets, 960 screws); screwed not bolted (bolts =
  upgrade: 130 bolts); hubless (40 closed triangles); doubled edges; the **flat-rate
  labour** argument (10′ vs 30′ dome = 9× floor, same 120 struts/9 operations);
  the cost is the skin (fibreglass ≈ $4,700, timber/brackets free, screws $48).
- **Notable scenes** (20: `fk_premise`, `fk_stock`, `fk_bracket_flat`,
  `fk_bracket_bend`, `fk_bracket_fitted`, `fk_triangle`, `fk_slack`, `fk_settle`,
  `fk_skin`, `fk_trees`, `fk_ledger`, `fk_bolts`, `fk_trade`, `fk_hubless`,
  `fk_doubling`, `fk_stockpile` (one log → eight sticks), `fk_floor`,
  `fk_flatrate`, `fk_glass`, `fk_cost`).

### `wedge` — "Eight Cuts to a House" (EIGHT CUTS TO A HOUSE)
*File: `lesson_wedge.py` (WEDGE_LESSON). 29 chapters. The core "wedge method" film.*
- **Core concepts**: the tree gets a vote; squaring the circle wastes wood; the
  frustum/board-foot budget; honest 2×4 packing (45% recovery) vs the brief's
  kinder estimate; stop squaring, start splitting (halve→quarter→eighth = 8 radial
  sectors); the kerf is the *only* loss; both conversions on the same two trees
  (~2× wood, or +53% vs the brief); the wedge **is** the member (2 flat sawn faces +
  curved bark + pith edge); sector geometry (area = πr²/8, chord = 2r·sin 22.5°);
  one orientation rule — **bark out, pith in**; short members are the point
  (defects cost a section, not a tree); the triangulated network carries the load;
  40 independent frames lifted whole; the **pinwheel joint** (no shared vertex, every
  end square); the corner nothing touches; two edges → four stick lengths (four
  saw-stop settings); neighbours don't share (doubled members); the **gasket** does
  the shaving (spline/key/hose); 55 interior seams + 10 rim seams; **the tree sizes
  the building** (solve backwards from a 6′ member → 22′ dome, 380 ft²); least
  actions per building; counting the cuts both ways; the honest non-claim.
- **Notable scenes** (16: `wg_open`, `wg_mill`, `wg_pack`, `wg_split`, `wg_section`
  (end-on sector), `wg_orient`, `wg_short`, `wg_explode`, `wg_pinwheel`,
  `wg_corner`, `wg_pair`, `wg_gasket`, `wg_scale`, `wg_assemble`, `wg_chain`,
  `wg_close`).

### `why` — "Why Wedges: A Dome That Does Not Need a Sawmill" (WHY WEDGES)
*File: `lesson_wedge_why.py` (WEDGE_WHY_LESSON). 48 chapters; the *combined* wedge film.*
*The **beats plan** (`beats.py` `WHY_SECTIONS`) divides it into 10 sections:
origin / tree / frame / money / strength / orientation / variation / seam / jig /
close.*
- **Core concepts** (superset of `wedge`, plus): the frankendome origin and its
  V-bracket; the V-bracket solves a problem the wedge build doesn't have; what a mill
  is actually for (headrig/edger/trimmer/planing mill); waste is wood of the wrong
  shape; recovery counted in board feet; the member measured (section + bearing
  area vs a 2×4); what one bend costs (defect priced against piece length); the
  **actual solved shell** (not a sketch); pinwheel with no mitres; **the compound
  butt cut — the correction chapter** (the film's earlier "no mitres" claim was
  wrong; the bevel is identical everywhere = half the sector angle, so it gauges
  once); neighbours never share; measured vs guessed piles kept apart (2 timed
  cutting sessions cross-checked against a geometric prediction); counting machines
  out of the chain; a shelf price is mostly not the tree (**15 middlemen listed**);
  one wedge valued two ways (rule-of-thumb vs strict section); the part nobody
  counts (culls, trips, hours); the **crossover diameter** (~9″ below which a wedge
  is not stiffer than a 2×4) — the figure that could sink it; **four ways up**;
  the **keystone panel** (point out → tapered opening a panel drops into); the
  **seam vein/duct** (point out → continuous V along every seam); four rotations =
  four buildings; mixed logs 10–15″ (fold angles identical to 6 decimals); the key
  in every seam (put variation in a cheap part); the jig (flat board, 3 rails, 6
  plates); the head arrives long, flush-cut in place; two trees → a shell you can
  stand in; "the shape is doing the work."
- **Notable scenes** (31: `ww_open`, `ww_round` (same disc packed both ways),
  `ww_chain` (machines fade out), `ww_stack`, `ww_stick`, `ww_turn` (four ways up,
  as seam pairs), `ww_fold` (real seam down its length), `ww_bench`, `ww_flush`,
  `ww_close`, `ww_sessions`, `ww_worth`, `ww_bend`, `ww_store`, `ww_buttcut`,
  `ww_keystone`, `ww_channel` (the duct on the solver's own dome), `ww_mixed`,
  `ww_vbracket`, `ww_joinery`, `ww_realdome`, `seg_franken_plain`, + borrowed `wg_*`
  painters).

### `scratch` — "From Scratch: Every Calculation Behind a Dome on Screen" (FROM SCRATCH / GEOMETRY TO PIXELS)
*File: `lesson_scratch.py` (SCRATCH_LESSON). 46 chapters, 18 math screens.*
- **Core concepts**: a dome on screen = two calculations (a shape, a picture); the
  seven-station pipeline; triangles; icosahedron; 12 points from phi; normalization;
  Euler's check (V−E+F=2); midpoint sag (0.850651 < 1); projection; two lengths
  (4 independent routes); "never trust one calculation"; hemisphere cut at the
  equator (40 panels, 30+35 struts, 26 hubs); best-fit radius; **rendering chain**:
  GPUs draw only triangles (struts = tubes), cross products → normals, winding
  order (front/back), the vertex buffer (10 floats/vertex), world space, yaw/pitch/
  distance camera, the view matrix (no camera — move the world), the frustum, the
  projection matrix, divide by w (perspective), screen mapping, the depth buffer
  (and why its precision runs out), back-face culling, the diffuse lighting sum,
  transparency re-orders drawing, 30 fps loop (33.33 ms/frame, 3,900 triangles).
- **Notable scenes**: `sc_pipeline`, `sc_euler`, `sc_hemisphere`, `sc_tube`,
  `sc_winding`, `sc_buffer`, `sc_world`, `sc_orbit`, `sc_view`, `sc_frustum`,
  `sc_clip`, `sc_screen`, `sc_depth`, `sc_cull`, `sc_light`, `sc_blend`, `sc_frame`.

## Marketing / campaign films

### `hype` … `hype6` — "Frankendome" (montage, versions 1–6)
*File: `lesson_hype.py`. Keys `hype`, `hype2`…`hype6`.*
- **Core concepts/arguments**: the house-as-platform ("build the skeleton once, keep
  the bones"); chassis/component upgrade model (PC-building metaphor); salvage
  mindset ("organs are still good", failure is affordable when material is scrap);
  the Evil Dome Empire gag + the serious turn; institutional capital vs one
  prototype; "you know somebody who will never afford a house"; the $50,000 ask
  (later $100,000); audience = homesteaders/builders/makers/preppers; the
  four product lines (home / shed / greenhouse / storm shelter). Deltas by version:
  v2+ adds the Teslabot gag, the mother/Fuller/inuit-igloo passages, "women
  specifically"; v6 adds themed skins (baseball/basketball/disco ball), "forty
  rentable faces"/billboard (a road-facing dome sells ad space), and the four
  product lines; v4–v6 splice `seg_party`/`seg_franken_plain` + `seg_outro`.
- **Notable scenes** (`hype_*`): `hype_bones`, `hype_platform`, `hype_swap`,
  `hype_absurd`, `hype_archetypes`, `hype_chassis`, `hype_badges`, `hype_teardown`,
  `hype_organs`, `hype_failure`, `hype_title`, `hype_phases`, `hype_catalog`,
  `hype_fortress`, `hype_powertools`, `hype_bolted`, `hype_becomes`, `hype_tools`,
  `hype_forwho`, `hype_asymmetry`, `hype_friend`, `hype_share`, `hype_audiences`,
  `hype_needs`, `hype_number`, `hype_hr`, `hype_teslabot`, `hype_psyche`,
  `hype_socials`, `hype_mother`, `hype_igloo`, `hype_themes`, `hype_billboard`,
  `hype_lines`.

### `kick` / `kick2` — "Build A Dome: The Campaign" (DOMESIM)
*File: `lesson_kickstarter.py` / `lesson_kickstarter_v2.py`.*
- **Core concepts/arguments**: "a house costs what its parts cost" (120 sticks, 40
  triangles, 9 operations); 997 ft² skin for 314 ft² floor (box) vs 583 ft² (dome)
  = **42% less exterior**; triangle rigidity; wind drag 0.42 vs 1.05 (~60% less
  load); **flat rate** (79 ft² or 707 ft² = same 120 struts/brackets/960 screws);
  one already exists (4 trees, 10 days, 6 months standing); made-not-bought bracket;
  the cowboy **hat** (bottom 20 triangles = exactly half the shell → glass the top,
  skip the bottom); bill of materials $6,943 new; four build ladders ($5,116 bare →
  $9,496); one skeleton four products; $100,000 ask ($86,000 equipment + $14,000
  material). *v2 adds*: the **pony wall** (174 → 272 usable ft²), the **brim/gutter**
  (18″ brim = 343 ft² catchment = 7,259 gal/yr), running cost $129/yr, **radiative
  sky-cooling paint** (96% reflect, 8–13 µm emission), and the ten-point summary.
- **Notable scenes**: `kick_title`, `kick_problem`, `kick_versus`, `kick_wind`,
  `kick_triangle`, `kick_bom`, `kick_ladder`, `kick_hat`, `kick_flatrate`,
  `kick_factory`, `kick_ask`, `kick_themes`, `kick_brim`, `kick_water`, `kick_pony`,
  `kick_energy`, `kick_paint`, `kick_points`, + `seg_bio`, `seg_outro`.

### `master` — "The Dome Simulator Master Presentation" (DOMESIM / THE WHOLE ARGUMENT)
*File: `lesson_master.py` (MASTER_LESSON). 108 chapters, 13 math screens.*
- **Core concepts**: the whole project in one film — one codebase, five worlds
  (Dome Creator, Dome Forge, Jig Shop, Assembly Line, the renderer itself);
  "nothing here is typed in" (math screens count the live dome); then the full
  construction masterclass, the frankendome, the priced starter home, and the
  factory/energy case, each with a derived math screen; segments spliced (`seg_party`,
  `seg_bio`, `seg_share`, `seg_outro`).
- **Notable scenes** (superset of all painters + `ms_toolchain` (5 pedestals),
  `ms_creator`, `ms_forge` (water-harvesting stack layer by layer), `ms_jigshop`,
  `ms_engine` (film strip), `kick_*`, `line_*`, `hype_*`, `fk_*`, `build_*`, `cut_*`).

### `world` — "Every Dome In The World" (DOME CREATOR / EVERY DESIGN)
*File: `lesson_world.py` (WORLD_LESSON). 27 chapters.*
- **Core concepts**: twelve shipped Dome Creator designs (Timber Workshop, Glass
  Studio Loft, Split-Log Homestead, Whole Trunk Lodge 20′, Grow Dome, Hex Cell
  Pavilion, Continuous Steel Arc Hangar, Rebar Garden Dome, Concrete Monocoque Form,
  Woodland Hex/Square Mirror, Treehouse Canopy Dome); frequency cost (1V–4V); parity
  (even frequencies stop at the equator, odd don't); hub vs hubless framing; the
  **skin decides the price**; envelope-per-floor efficiency; size is a number you
  type (part counts depend on frequency alone, never on size).
- **Notable scenes**: `world_lineup`, `world_frequency`, `world_framing`,
  `world_economics`, `world_efficiency`, `world_scale`, `world_show_*` (12).

### `world_chatgpt` — "10 Dome Builds — The Accountable Master Cut"
*File: `lesson_world_chatgpt.py`. 30 chapters.*
- **Core concepts**: the same 10 builds with a full production ledger — Dome Creator
  BOM + Assembly Line hours + a modeled direct-sale price; material / conversion
  cost / margin kept separate; "what the model refuses to hide" (curves, code,
  freight, site work, local engineering).
- **Notable scenes**: `chatgpt_lineup`, `chatgpt_economics`, `chatgpt_show_*` (10),
  + borrowed `world_*`, `ms_*`, `line_*`.

### `all_domes` — "All Domes" (DOME CREATOR / EVERY PERMUTATION)
*File: `lesson_all_domes.py`. 34 chapters.*
- **Core concepts**: every permutation of the Dome Creator, drawn by the Creator's
  own renderer; declared vs measured (prices are declared inputs, everything else
  read off the model); the tool's construction order (348 work steps — the frame is
  not the expensive phase); frequency dials; **6 frame styles**; 8 strut shapes; 8
  materials; 16 finishes; 16 panel types; 9 cladding layers; 7 foundations; floor
  partitions; the fit-out (equipment/walls/plumbing — "the dome is the cheap part");
  8 random draws (seed on screen); **~16 billion shells**.
- **Notable scenes**: `ad_lineup`, `ad_hero`, `ad_build`, `ad_frequency`, `ad_styles`,
  `ad_shapes`, `ad_materials`, `ad_colours`, `ad_panels`, `ad_layers`, `ad_foundations`,
  `ad_floor`, `ad_fitout`, `ad_random`, `ad_show_*` (12).

### `look` — "The Dome House Lookbook" (DOME INTERIORS / CAST, WARDROBE AND THE COMPOSER)
*File: `lesson_lookbook.py`. 11 chapters.*
- **Core concepts**: headroom falls from the crown outward (how tall a thing can be
  depends on where it stands); a catalogue + editor that places furniture against the
  curve; eight women, no recolours; hair as geometry (strands off the scalp); outfits
  as lists lofted through the body; hems are **landmarks, not numbers** (same dress
  fits 1.58 m and 1.86 m); the composer refuses a piece the shell has come down on;
  the "house" set (stove flue wants the crown, sofa seat from the seated pose).
- **Notable scenes**: `look_room`, `look_furnished`, `look_cast`, `look_hair`,
  `look_wardrobe`, `look_form`, `look_landmarks`, `look_composer`, `look_refusal`,
  `look_home`, `look_finale`.

### `drama` / `series` — "The High Council Dome" / "The Vance Network"
*File: `lesson_drama.py`. Vertical 9:16 micro-drama (4 beats; the series = 6
episodes × 4 beats).*
- **Core concepts**: none structural — a narrative *wrapper* for the dome vocabulary
  (struts, key, base ring, facets, the Network). Useful to the book only as tone.
- **Notable scenes**: `drama`, `series`.

### `harvest` — "Two Trees, All at Once" (TWO TREES)
*File: `lesson_harvest.py`. 15 chapters. Backed by `house_economics.py`.*
- **Core concepts**: 2 trees → 8 sections × 8 wedges = 64 struts/tree, 128 for a
  120-member frame; the fell line (hinge steers, saw sets it free); split loses only
  the kerf (**87.4%** recovery: 318 bf → 40 kerf, 278 kept); measured vs guessed;
  the harvest in days (2 felling + 2 bucking + 4 ripping; 48 tanks); where a house's
  time goes (7.6 mo builder / 15.1 mo owner-built; framing = 16.6% of build); where
  the money goes ($200k house → $27.4k land, $128.7k building, $33.4k OH&P, $10.5k
  commission); labour ≈ 25.7%; the trailer built the other way; **what the fortnight
  is worth** vs buying the frame; every part of the house; where the saving comes
  from (mostly building your own, not the shape); what it doesn't show (37% is
  shape-agnostic).
- **Notable scenes**: `hv_harvest` (the harvest object), `hv_dome` (the simulator's
  solved dome).

### `why_build` — "Why Build This Way" (TWO TREES)
*File: `lesson_why_build.py`. 16 chapters.*
- **Core concepts**: not "how cheap" but "how much shelter an hour buys"; the long
  chain (income→tax→store→contractor→loan) vs the short one (tree→wedge→jig→shell);
  the tree is the product (8″ log → 6.28 in²/wedge vs 5.25 in² dressed 2×4); the
  wedge arrives with its angle in it (45° vs folds 18.03°/22.46°); locate-first-
  cut-second; 3.75 ft²/hour; $60/hr production value (2.5× framing labour) vs
  $24/hr; debt makes it larger (avoided $ → avoided interest; $4,800 → $10,922 over
  30 yr @ 6.5%); interest builds nothing ($127,544 interest on $100k); count it in
  hours of life (money = stored labour; 192 h buying vs 112 h building); the
  build-vs-buy rule (build while your hour creates more than it earns); out of the
  commodity chain (2021 lumber spike); the economic score on one sheet.
- **Notable scenes**: `wb_dome`, `wb_harvest`, `wb_chain`, `wb_section` (wedge vs
  2×4 end-on, same scale), `wb_panel`.

### `pine_value` — "The $20 Pine" (TWO TREES)
*File: `lesson_pine_value.py`. 16 chapters.*
- **Core concepts**: a tree has a **ladder** of values, not one price — stumpage
  (~$24), firewood ($113), sawn lumber ($398), split wedge stock ($584), built
  framing ($2,400/half ≈ $4,800 shell), mortgage-avoided ($5,461); 442 board feet
  in the stem; split keeps 88% vs mill 60% (or 45% honest) = **46.7% more wood,
  70% less thrown away**; 2 split trees = 2.93 sawn trees; "the wood did not get
  better — it got used"; vertical integration at household scale; the three cautions
  (mill figure generous, sawing rate, generous framing rate).
- **Notable scenes**: `pv_pine`, `pv_cord`, `pv_bars`, `pv_trees`, `pv_ladder` (the
  rising ladder), + borrowed `ww_round`, `hv_dome`, `hv_harvest`, `wb_chain`.

### `pvtwo` — "The Twenty Dollar Pine, Part Two" (THE TWENTY DOLLAR PINE, PART TWO)
*File: `lesson_pvtwo.py`. 3 chapters.*
- **Core concepts**: updated stumpage figures (Q4 2025 Alabama sawtimber $17–21/ton,
  Q2 2026 South-wide $23.34/ton, pulpwood ~$6/ton); local firewood $275–300/cord;
  15″ pine ≈ 0.35–0.45 cord; 2 trees ≈ 160 blanks vs ~120-member frame.

## Stem-Cell Dome / shop-floor films

### `seed_pitch` — "A house you can take apart" (THE STEM CELL DOME / CAMPAIGN)
*File: `lesson_seed_pitch.py`. 37 chapters. Backed by `seed_model` + `soft_shell`.*
- **Core concepts**: 19′ dome, 277 ft², under $10k stripped / $12k standard; measured
  vs priced kept apart; the frame already on your land (88% split vs 45% mill); wood
  was never the expensive part (~$100) — the shell is (~$4k); the **stem cell** (40
  identical undecided openings); what closes a triangle (inner panel, cavity, outer
  panel, shell — nothing screwed); the **gap nobody wanted** = the seam duct (two
  sawn faces don't close flush — good); the shell is a boat hull (wood-cored
  composite, gelcoat); the roof in 4 slices with an **S-lip** seam + gasket; four
  ways to skin it (glass/resin by weight); "no panel fits a 4×8 sheet" (hard-won);
  the top is a **socket** (services up the middle through the apex); everything else
  snaps on outside (fan/heater/cooling on a rim panel); the **core moves to the next
  dome** (~⅕ of materials, walks); it gets warmer every winter (shell lifts, layer
  goes under); only works as a system (landowner rents ground, you own the house);
  a pad not a plot; the platform (116 boards); whose bill is whose ($7k of ground);
  the invoice ($10,030 build + $2,006 profit); how far down it goes; three things it
  says against itself (empty cavity, wastes wood, unproven duct); 41% less skin +
  15% off the rest (sky cooling); running on nothing (800 W + a bank); six second
  buildings; **a dome is a head that wears hats** (one waterproof layer outside);
  the standard article wears a **shower cap** (soft shell, stacks hats); the **$50
  quilt** (recycled clothing, ~130 t-shirts/layer); the **mast through the column**
  + floor that comes later; hang it between two trees (3 cables, saddles, winch);
  the goal ($110k = a list); the molded member with hardware in it; three things at
  once (quilters, pad hosts, dome owners).
- **Notable scenes**: `sp_deck`, `sp_slices`, `sp_swap`, `sp_secondary`, `sp_bay`,
  `sp_duct`, `sp_standing`, `sp_frame`, `sp_shell`, `sp_cap` (hats stacking),
  `sp_quilt`, `sp_mast`, `sp_floating`, `sp_head` (wall cut through to show layer
  order), `sp_invoice`, `sp_goal`, `sp_next`, `sp_three`, `sp_core`, `sp_polyp`,
  `sp_move`, `sp_pad`, `sp_close`.

### `pitch_hero` — "A house you can take apart" (THE STEM CELL DOME — hero cut)
*File: `lesson_pitch_hero.py`. 9 chapters, ~100 s for the top of the Kickstarter page.*
- **Core concepts**: 19.4′, 277 ft²; 2 trees → 120 wedges, no hubs, 3 saw settings;
  one waterproof layer outside; $12,000 with the invoice shown; hull/mast/floor/rig
  as later upgrades; three kinds of people; every number is a runnable model.

### `module_build` — "Build one utility core" (THE STEM CELL DOME / SHOP FLOOR)
*File: `lesson_module_build.py`. 9 chapters. Backed by `column_build.py`.*
- **Core concepts**: the utility core is identical in every dome; build order =
  chase (bench, upside-down) → **drain first** (can't re-route) → water (prove it
  before anything electrical) → power last (into a known-dry core) → close/prove
  the cap/stand it up; 7.2 h practised vs 17.2 h first; the two skipped tools
  (go/no-go crimp gauge, torque screwdriver); 23-line shopping list (nothing exotic);
  build it once, it moves to the next dome.
- **Notable scenes**: `mb_bench`, `mb_stand`, `mb_chase`, `mb_drain`, `mb_water`,
  `mb_power`, `mb_close`.

### `seam` — "The seam does four jobs" (THE STEM CELL DOME / THE SEAM)
*File: `lesson_seam.py`. 7 chapters.*
- **Core concepts**: 55 seams, **309 ft of void**; the key fills the angle but leaves
  a run above/below; the seam's four jobs — (1) **guttering** (slot + gutter +
  suction; 185 gal/inch), (2) **air barrier** (4 Pa positive pressure → every gap
  blows outward), (3) **drying the wood** (perforated liner washes air down both
  faces), (4) **condensing on purpose** (thermoelectric plates; 73 gal/yr); cost
  $7,549 on a $12,036 dome.
- **Notable scenes**: `sm_channel`, `sm_open`, `sm_water`, `sm_air`, `sm_dry`,
  `sm_condense`, `sm_bill`.

## Cabin World films (the current baseline scene)

### `cabin_pilot` — "Cabin World Pilot"
*File: `lesson_cabin_pilot.py`. 2 chapters.*
- **Core concepts**: one log → 8 wedges ripped through its heart; 120 members, 2
  crown triangles still to go up. The worked example of a narrated film in the Cabin
  World.

### `cabin_wedge_explained` — "The Wedge Dome, Explained" (DOMESIM)
*File: `lesson_cabin_wedge_explained.py`. 23 chapters. Backed by `channel_facts.py`.*
- **Core concepts**: the whole method in the Cabin World; 120 members in two lengths
  (70.2″ / 62.7″); the pinwheel (no hubs); doubled edges (55 seams + 10 rim); the
  **V** (two sawn faces can't close flat; 2 folds: 18.0° at 25 seams, 22.5° at 30);
  the **key** (solid = spline, hollow = pipe; 309 ft); how much room (5.3–6.5 in²,
  1.69–1.97″ max round); the sizes assumed (nominal vs estimate vs fill rule); water
  and wire fit (11% of the tighter seam vs 40% allowed); **round ducts do not fit**
  (the number that doesn't help); the channel *is* the duct (13 cfm/seam vs 18 cfm
  needed); Peltier plates + three-way gate; what the plates are worth (360 W, 6 h/day,
  73 gal/yr — a dehumidifier, not a water supply); the **key as spacer** (3″ duct →
  +7.0″, dome +6%; 4″ → +14%); a bigger log (room ∝ r²: 10″→3.5 in², 12″→5.3, 15″→8.8,
  18″→…); **printing the key in halves** (121 kg / $2,425 / 1,768 printer-hrs for all;
  print only seams that carry something); where channels meet (6 five-way + 10 six-way
  + 10 rim rosettes); two rules (no pressure joints in seams; every fitting in an
  openable rosette); fitted seam cost $7,549; the reveal.
- **Notable scenes**: `grain`, `member`, `counts`, `pinwheel`, `doubled`, `vee`,
  `key`, `room`, `sizes`, `bundle`, `ducts`, `air`, `dehumid`, `water`, `spacer`,
  `ring`, `logs`, `print`, `print_cost`, `hubs`, `rules`, `cost`, `reveal`.

### `cabin_seam_climate` — "Which Way the Seam Breathes" (DOMESIM)
*File: `lesson_seam_climate.py`. 22 chapters. Backed by `seam_climate.py`.*
- **Core concepts**: which way the seam breathes; the **radial** direction; a Peltier
  plate is a heat pump (runs both ways); **compare dew points, not RH**; will it
  condense (dew point vs surface temperature); 15–20° colder plate; **plate first,
  wood second** (order, not a colder surface, protects wood); seven modes (take
  in / push out / condense on cold skin / desiccant loop / purge / …); the weathers
  assumed; what the controller chose; the loop vs the purge (drying ≠ ventilating);
  the dome's levels (4 rings, 5 seam bands); the pentagon ring that cannot drain;
  condense low, drain at the rim; warm air rises (in low, out high); desiccant stays
  out of the seams (32 ft packed path fails; regen needs 120–200°, key softens at
  80°); two drawers + a gate (2.9 kg beads, 18 cfm at 20 Pa); what the desiccant
  won't do (a soaked 19% frame = 54 kg water = 93 drawer fills, 56 kWh); the stove's
  heat never its air (sealed exchanger); the layout; "dew point decides."
- **Notable scenes**: `breathe`, `radial`, `pump`, `dewpoint`, `condense`, `owner`,
  `order`, `modes`, `weathers`, `choices`, `loop`, `levels`, `pentagon`, `rim`,
  `stack`, `packed`, `regen`, `drawer`, `honest`, `stove`, `plan`, `close`.

### `cabin_linseed_oil` — "Linseed Oil for a Dome" (DOMESIM)
*File: `lesson_cabin_linseed_oil.py`. 17 chapters.*
- **Core concepts**: where linseed oil earns a place (interior faces, trim, tool
  handles); **rag oxidation = heat** (spontaneous combustion — the rag station);
  raw vs boiled vs polymerized (read the exact can); finish sound wood, preserve
  clean joint surfaces; two product labels, two schedules (declared examples from
  Tried & True); apply thin, wipe dry; keep the seam doing its jobs (oil ≠ sealing
  land; adhesives/tapes need compatible substrate); outside needs a weather system;
  declare planning assumptions (350 ft²/gal/coat + 15% handling); measure **wood, not
  floor** (120 members, 664.3 ft stock, 6.0″ faces → 3.80 gal → 4.37 gal with
  allowance); the number that argues against it (manufacturer's 1,000 ft²/gal claim
  vs labour cost); tools; glazing (putty belongs to a specified sash); finish the
  parts people touch; inspect-clean-renew.
- **Notable scenes**: `purpose`, `rags`, `oils`, `prepare`, `label_inputs`, `apply`,
  `seam`, `weather`, `planning_inputs`, `area`, `quantity`, `limits`, `tools`,
  `glazing`, `interior`, `maintenance`, `close`.

## BYOD / Dome Park films

### `dome_park` — "Dome Park" (DOME PARK / BRING YOUR OWN HOME)
*File: `lesson_dome_park.py`. 25 chapters. Backed by `park_model` + `park_facts.py`.*
- **Core concepts**: an RV park for houses; two people (amber host = ground, cyan
  tenant = house, nothing shared); prices are assumptions, everything else measured;
  what a pad is (deck, rim, ring, 3 pipes up the middle); **the pad is the floor**
  (nothing poured/dug/left behind); pad sizes rounded up to 4′; host's short list;
  pad cost line-by-line (incl. site infrastructure); the line that never moves; host
  vs furnished-let comparison; **foundation share** (8–63% across designs); hotel /
  short-let / apartment / dome-on-pad; the crossover stay length; semi-nomadic
  (lift, drive, set down, plug in); one hardware set any size; what does not move
  (counts + hub bill) vs what does (sticks + skin); a house that gets warmer every
  winter (Arctic layers); what each layer is worth; the pad turns (single-axis
  tracking ≈ +25%); what the park provides (bathhouse → skip plumbing); why a
  network (RV park turns over nights/weeks, a dome park seasons/years); the first
  park ($100k); bring your own home.
- **Notable scenes**: `dp_site`, `dp_legend`, `dp_network`, `dp_pad_build`,
  `dp_pad_detail`, `dp_landing`, `dp_two_sides`, `dp_foundation`, `dp_move`,
  `dp_hardware`, `dp_layers`, `dp_solar`, `dp_shared`.

### `byod` / `byod_deepseek` / `byod_polished` / `byod_snarky` — "Bring Your Own Dome"
*Files: `lesson_bring_your_own_dome.py` (BYOD_LESSON), `lesson_byod_deepseek.py`,
`lesson_byod_styled.py` (polished/snarky profiles). 38–43 chapters; the polished and
snarky cuts are the same script in different style profiles (`polished` / `snarky`).*
- **Core concepts** (adds to `dome_park`): the animated **iris** pad (one pad, many
  sizes); the deluxe **rotating foundation**; the wedge's **service channels** (up
  the centre, along the seams, out of the way); the **lip** (outward wedge → tapered
  panel opening); veins along the outside skin; the pad catalogue; gravel/concrete/
  timber decks; the starter ($10k pad) tested at 3 rents; below/above the line; the
  deluxe price (the figure that does not help — the loaded pad loses day one); the
  storage-dome side thought; rewards tiers (founder status, 3-D-printed keychain,
  signed book); personal story (the $5k college loan, the military, "constructive
  revenge"); **buy for the next two steps** (6′→10′→12′ members); the R-value ladder;
  solar capacity (5–10 kW nameplate); shared bathhouse; small-scale/small-risk
  ($100k, one to three pads).
- **Notable scenes**: `byod_title`, `byod_iris`, `byod_rotation`, `byod_rooms`,
  `byod_channels`, `byod_growth`, `byod_layers`, `byod_solar`, `byod_starter`,
  `byod_departure`, `byod_rewards`, `byod_lip`, `byod_storage`, `byod_pad_build`,
  `byod_decks`, `byod_veins`, `byod_veins_joke`, `byod_catalog`, `byod_line`,
  `byod_host_design`, `byod_hardware`, `byod_close`, + `dp_*` shared painters.

## Auto-registered (not hand-authored)
- **`cabin_<key>` re-stages** — every non-cabin lesson re-staged in the Cabin World
  via `two_v_demo/cabin_stage.py` (same chapters/painters, cinematic cameras on the
  exhibit platform; drama/series/harvest keep their authored cameras). These are the
  re-render queue's target keys.
- **`concept_*` lessons** — ingested from `concepts/cards/*.json` via
  `concepts/film.py`; each renders one named visual-lexicon concept in the Cabin
  World (e.g. `concept_example_molecular_sieve_fridge`). These are the rendered
  forms of `lexicon_concepts.CONCEPTS`.
- **`lesson_build_extra.py` / `lesson_franken_extra.py`** — present but not registered
  (no `Lesson` object under `BUILD_EXTRA_LESSON`/`FRANKEN_EXTRA_LESSON`; painter/
  helper modules). Not film keys.

---

# Section B — Concept list (one bullet per distinct concept)

Every concept is given a 1–2 sentence definition, its source files, and a suggested
book chapter. Concepts already named in `two_v_demo/lexicon_concepts.py` are marked
**[lexicon]** (their `taught=` refs already point at book chapters, noted where
present). Concepts with no natural home are flagged **NEW CHAPTER CANDIDATE**.

## Geometry
- **Phi places the corners, not the struts** [lexicon]. The golden ratio builds the
  icosahedron's 12 vertices; a 2V dome's two strut lengths are set by projection, not
  by phi. Sources: `lessons.py`, `lesson_build.py`, `lesson_scratch.py`. → Ch 8/9
  (and the `2v`/`build`/`scratch` "phi" chapters).
- **Projection makes exactly two lengths** [lexicon]. Splitting each icosahedron edge
  and pushing midpoints out to the sphere makes every 2V edge fall into exactly two
  classes (SHORT/LONG). Sources: `lessons.py`, `lesson_build.py`, `lesson_scratch.py`.
  → Ch 9.
- **A triangle cannot change shape** [lexicon]. Three fixed side lengths fix a
  triangle completely; a frame of triangles needs no bracing (a square racks).
  Sources: every masterclass; `book.py` ch 6. → Ch 6.
- **Start from the icosahedron** [lexicon]. Of the five Platonic solids it starts
  closest to a sphere, so the projection correction is smallest. Sources:
  `lessons.py`, `lesson_build.py`, `lesson_scratch.py`. → Ch 8.
- **Solve at radius one, then scale** [lexicon]. Work everything on a unit sphere so
  every strut is a pure chord factor; multiply by the real radius to size it.
  Sources: `lessons.py`, `lesson_build.py`. → Ch 9, 20–24.
- **Chord factor / frequency vocabulary** (hub, strut, panel, chord factor,
  frequency). The five words the whole geometry rests on. Source: `lesson_build.py`
  `build_vocab`. → Ch 8/9.
- **The end-cut angle is half the central angle**. A chord dips below the sphere, so
  the angle a strut leaves the surface at is half the central angle it subtends.
  Source: `lesson_build.py` `build_endcut`. → Ch 34.
- **The dome is four rings and a crown** (26 hubs at measurable heights). Source:
  `lesson_build.py` `build_rings`. → Ch 8, 32.
- **Errors amplify around a ring** [lexicon]. A 10-sided ring has nowhere to put a
  small error except into the next piece; a base-strut error returns amplified by the
  golden ratio. Sources: `lesson_build.py` `build_error`; `lessons.py` `verify`. → Ch 38.
- **The measurement loop** (member → triangle → ring → radius → height). Source:
  `lesson_build.py` `build_check`. → Ch 24, 38.
- **Euler's check / closed surface** (V − E + F = 2; edges = faces×3/2). Source:
  `lesson_scratch.py` `sc_euler`. → Ch 8 (sidebar).
- **Frequency and parity** — even frequencies stop at the equator, odd don't; the
  gold line / cut placement changes. Source: `lesson_world.py`, `lesson_all_domes.py`
  `world_frequency`. → Ch 49.
- **Frequency cost ladder** — more panels, shorter sticks, more member classes
  (2V: 2 lengths; 3V: 4; 4V: 6). Sources: `lesson_hex.py` `hex_size_ladder`,
  `lesson_world.py`, `lesson_all_domes.py`. → Ch 49.
- **Curvature = missing angle (angular deficit)** [hex film]. A flat hexagon sheet
  can't curve because 3×120° = 360°; a pentagon removes 36° and makes the surface
  lift. Source: `lesson_hex.py`. → Ch 49 or **NEW** (only if hex domes get their own
  chapter).
- **Exactly twelve pentagons, always** [lexicon]. Descartes' theorem (a closed convex
  cage is missing exactly 720°) forces twelve pentagons however many hexagons.
  Source: `lesson_hex.py` `hex_euler`. → Ch 49 or NEW.
- **Truncated icosahedron (soccer ball)** — 20 hexagons + 12 pentagons, 90 identical
  struts, 2 flat templates, but a zigzag rim and no level equator. Source:
  `lesson_hex.py`. → Ch 49 or NEW.
- **Hexagon panels warp after subdivision** — six points on a sphere don't share a
  plane; only the soccer-ball hexagons are flat. Source: `lesson_hex.py` `hex_warp`.
  → Ch 49 or NEW.
- **A zome is swept, not cut from a sphere** [lexicon]. A star of directions swept
  out gives flat rhombic panels; equal directions give one strut length; the top
  closes at a point; hubs land on level rings. Sources: `lesson_zome.py`. → NEW
  (a zome chapter/box — none of ch 1–71 covers zomes).
- **The golden zome (rhombic triacontahedron)** — 30 identical rhombi whose diagonals
  land on phi, at the cost of uneven hub rings and a messy floor line. Source:
  `lesson_zome.py`. → NEW.
- **The pinwheel has two fold angles** [lexicon] — the wedge dome's seams close at
  only two fold angles (18.0° / 22.5°), so two key profiles close the whole shell.
  Sources: `lesson_wedge.py`, `lesson_wedge_why.py` `ww_fold`. → Ch 16.

## Structure / the wedge method
- **The shape does the work, not the stick** [lexicon]. A dome stands by triangulation,
  not by the stiffness of any one member. Sources: `lesson_wedge.py`, `lesson_wedge_why.py`.
  → Ch 6.
- **The crossover diameter** [lexicon]. Above a certain trunk diameter (~9″) a raw
  sector is stiffer than a dressed 2×4; below it, not. Stated as a limit, not a
  boast. Source: `lesson_wedge_why.py` `ww_stick`. → Ch 7 (and Ch 10).
- **Forty independent frames** [lexicon]. Each triangle is completed flat on the
  ground and lifted whole — this turns a geodesic dome from a scaffolding problem
  into a flat-pack one. Sources: `lesson_wedge.py` `wg_explode`, `lesson_wedge_why.py`.
  → Ch 18, 31–32.
- **Neighbours never share a stick (doubled edges)** [lexicon]. Each panel owns its
  three members, so every interior seam holds two members side by side (110 of 120;
  10 rim). Sources: `lesson_wedge.py` `wg_pair`, `lesson_wedge_why.py` `ww_pair`. → Ch 18.
- **The pinwheel joint (no mitres, no shared vertex)** [lexicon]. Three same-handed
  members, each end landing square on the next member's flat face; no two ends meet
  at a point. Sources: `lesson_wedge.py` `wg_pinwheel`, `lesson_wedge_why.py`. → Ch 15.
- **The corner nothing touches** — the mathematical vertex sits in a gap no stick
  reaches. Source: `lesson_wedge.py` `wg_corner`. → Ch 15.
- **Two edges become four stick lengths** — the pinwheel splits the 2 edge classes
  into 4 near-identical stick lengths (4 saw-stop settings for the whole house).
  Source: `lesson_wedge.py` `wg_pinwheel` (math). → Ch 9, 15.
- **Let the key hold the angle** [lexicon]. Put the precision in the small cheap part
  (the seam key), not in every stick; the tree supplies mass, the jig repeatability,
  the connector precision. Source: `lesson_wedge_why.py` `ww_fold`. → Ch 17.
- **Four ways up, four buildings** [lexicon]. The wedge is not symmetric, so its
  orientation (point in/out, panel in/out) changes the frame: keystone panel, seam
  duct, stiffness, weather face. Sources: `lesson_wedge.py` `wg_orient`,
  `lesson_wedge_why.py` `ww_turn`. → Ch 14.
- **Bark out, pith in** — the single orientation rule; dense outer growth to weather,
  and the stick tells you which way it goes (no label needed). Sources:
  `lesson_wedge.py`, `lesson_wedge_why.py`. → Ch 14.
- **The keystone panel** — point the wedge outward and the panel opening tapers, so a
  panel drops in and stops (can't fall through). Source: `lesson_wedge_why.py`
  `ww_keystone`. → Ch 14, 69 (the lip).
- **The seam vein / duct** — point outward and the two sawn faces open away from each
  other, leaving a continuous V along every seam = a services duct. Source:
  `lesson_wedge_why.py` `ww_channel`. → Ch 14, 44, 60 (and `byod_channels`, `seam`,
  `cabin_wedge_explained`).
- **Short members forgive defects** [lexicon]. A knot/bend destroys whatever length
  has to be thrown away around it; short members make a defect several times cheaper
  and salvage trees a mill would reject. Sources: `lesson_wedge.py` `wg_short`,
  `lesson_wedge_why.py` `ww_bend`. → Ch 19.
- **The compound butt cut (the correction)** — every butt end is a compound angle; the
  earlier "no mitres anywhere" claim was wrong and corrected on camera. The bevel is
  identical on every member (= half the sector angle), so it gauges once. Sources:
  `lesson_wedge_why.py` `ww_buttcut`; `lesson_cuts.py`. → Ch 15 (errata), 34.
- **The tree sizes the building** [lexicon] (Method B in reverse). Buck the tree to a
  carryable length, split to 8, and solve the radius that makes the longest member fit
  — the diameter "nobody chose" falls out. Sources: `lesson_wedge.py` `wg_scale`,
  `lesson_wedge_why.py`. → Ch 22–24.
- **Mixed logs don't move the fold angles** — solving the dome at 10″ vs 15″ trunks
  leaves the fold angles identical to six decimals; only the key/offset taper moves.
  Source: `lesson_wedge_why.py` `ww_mixed`. → Ch 50.
- **The gasket does the shaving** — a spline/key/hose takes up the fold-angle
  variation so no member is shaved to fit. Source: `lesson_wedge.py` `wg_gasket`. → Ch 16.
- **Locate first, cut second** — rough timber can't survive "measure→cut→fit"; the
  jig locates the member, and the cut is made in place. Sources: `lesson_wedge_why.py`
  `ww_bench`, `why_build` `wb_panel`. → Ch 35–36.
- **The head overfit / flush-cut** — one end arrives finished; the other arrives too
  long on purpose and is sawn off against the fence (the cut that is never measured).
  Source: `lesson_wedge_why.py` `ww_flush`. → Ch 35–36.

## Wood / recovery
- **A split log keeps most of itself** [lexicon]. The only loss is the kerf; a mill
  loses slabs/edgings/trim/drying. Source: `lesson_wedge.py` `wg_split`,
  `lesson_wedge_why.py`. → Ch 13.
- **Eighty-seven percent (recovery)** — this book's 12″ tree recovers ~87% split vs
  ~45% milled (or 60% on the brief's kinder estimate); "where 88 became 87" is an
  explicit errata. Sources: `lesson_wedge.py` `wg_mill`, `lesson_harvest.py`,
  `book.py` ch 13. → Ch 13.
- **Waste is the wrong shape, not bad wood** [lexicon]. The four crescents outside a
  rectangle in a circle are sound wood of the wrong shape. Source:
  `lesson_wedge_why.py` `ww_round`. → Ch 7.
- **One eighth of a tree, used as a stick** [lexicon]. A member is literally an 8th
  of the trunk (2 sawn faces, bark back, pith edge); nothing is squared or planed.
  Sources: `lesson_wedge.py` `wg_section`, `lesson_wedge_why.py`. → Ch 5, 12.
- **Sector geometry** — area = πr²/8; chord = 2r·sin 22.5°; depth = r; 45° per
  sector. Sources: `lesson_wedge.py` `wg_section` (math), `wedge_geometry.py`. → Ch 12.
- **The frustum / board-foot budget** — a trunk is a frustum; 1 bf = 1 ft² × 1″;
  the fixed budget every method starts from. Source: `lesson_wedge.py` `wg_mill` (math).
  → Ch 1, 13.
- **The honest 2×4 packing** — parallel rows can only be as wide as their narrowest
  point; this log yields 25 true 2×4s = 200 bf = 45% (vs the brief's kinder 60%).
  Source: `lesson_wedge.py` `wg_pack`. → Ch 7, 13.
- **The kerf is the only loss** — halve (1 diameter of kerf) + quarter (1 more) + 4
  pith-to-bark passes. Source: `lesson_wedge.py` `wg_split` (math). → Ch 13.
- **Two trees, one frame** [lexicon]. 2 pines → 128 struts (8 sections × 8 wedges
  each) against 120 needed. Source: `lesson_harvest.py`, `lesson_wedge.py`. → Ch 22, 24.
- **2 split trees = 2.93 sawn trees** — 46.7% more wood, 70% less thrown away.
  Source: `lesson_pine_value.py`. → Ch 13.
- **The $20 pine ladder** — stumpage (~$24) → firewood ($113) → sawn ($398) → split
  ($584) → built framing ($2,400) → mortgage-avoided ($5,461); "the wood did not get
  better — it got used." Source: `lesson_pine_value.py`, `house_economics.py`. → Ch 45,
  55 (or a dedicated NEW "value ladder" sidebar).
- **Stumpage/cord reference numbers** (Q4 2025 Alabama sawtimber $17–21/ton; Q2 2026
  $23.34/ton; pulpwood ~$6/ton; cord = 128 ft³ stacked ≈ 90 ft³ solid; 15″ pine ≈
  0.35–0.45 cord). Source: `lesson_pvtwo.py`. → Ch 55.

## Method / shop practice
- **Fewer operations, fewer machines** [lexicon]. The wedge path keeps the chainsaw
  and drops the headrig/edger/trimmer/kiln/grader/planing mill. Source:
  `lesson_wedge_why.py` `ww_chain`. → Ch 2, 54.
- **The jig, not the tape measure** [lexicon]. One flat board with the triangle struck
  once makes 40 identical panels; locate on the sawn faces, never the bark. Source:
  `lesson_wedge_why.py` `ww_bench`. → Ch 30, 33.
- **Cut it too long on purpose** [lexicon] (head overfit). Source: `lesson_wedge_why.py`
  `ww_flush`. → Ch 35.
- **The compound cut needs two saws** [lexicon]. Table saw rips the bevel, sled/mitre
  crosscuts the ends. Source: `lesson_cuts.py`. → Ch 34.
- **Turn it, don't flip it** [lexicon]. The second end is rotated about the long axis,
  not mirrored. Source: `lesson_cuts.py` `cut_turn`. → Ch 34.
- **The five-cut method** — cut a scrap 4× rotating 90°, slice a 5th strip and measure
  both ends to expose fence error. Source: `lesson_cuts.py` `cut_fivecut`. → Ch 34.
- **The complement angle** — an angle measured from the blade is the complement of the
  same angle from square; 62° from square = 27.8° from the blade (gets past the saw's
  ~50° stop). Source: `lesson_cuts.py` `cut_complement`. → Ch 34.
- **Batch by setting** — six setups cover all 240 ends; change a setting as few times
  as possible (changing is where error enters). Source: `lesson_cuts.py` `cut_batch`.
  → Ch 31, 34.
- **Dry-fit one triangle** — three struts on a flat floor, no fasteners; if it closes
  and lies flat, the settings are right. Source: `lesson_cuts.py` `cut_dryfit`. → Ch 31.
- **The hinge steers the tree** [lexicon] — the notch + back cut + hinge control the
  fell; the saw only sets it free. Source: `lesson_harvest.py` `hv_harvest`. → Ch 27.
- **Buck and split: a tree becomes struts** [lexicon]. 8 sections × 8 wedges; every
  section splits at once. Source: `lesson_harvest.py`. → Ch 28–29.
- **Raise by complete rings** [lexicon] — never build up one side; a closed ring is a
  rigid hoop, a half ring leans. Source: `lesson_build.py` `build_raise`. → Ch 32.
- **Openings come out as whole panels** [lexicon] — leave a panel out and frame the
  triangle; cutting a strut means replacing a load path. Source: `lesson_build.py`
  `build_openings`. → Ch 41.
- **Skin from the rim upward** [lexicon] — each panel laps the one below, like
  shingles; flash every hub. Source: `lesson_build.py` `build_skin`. → Ch 40, 42.
- **The utility-core build order** — chase → drain (un-routable) → water (prove before
  power) → power last (into a known-dry core) → close/prove/stand. Sources:
  `lesson_module_build.py`. → NEW (a "shop floor" chapter) or Ch 44.
- **Linseed-oil safety** — raw/boiled/polymerized differ; oiled rags oxidize and can
  self-ignite (the rag station); oil can't restore load capacity; keep sealing lands
  compatible; measure wood not floor (664.3 ft × 6″ faces → 4.37 gal with allowance).
  Source: `lesson_cabin_linseed_oil.py`. → Ch 44 or NEW (finishes box).

## Build (the fortnight) — already mapped 1:1 to chapters 26–32
- **Harvest in days** [lexicon] — 8 days: 2 felling + 2 bucking + 4 ripping; ripping
  timed at 2 tanks/hour × 24 h = 48 tanks. Source: `lesson_harvest.py`. → Ch 27–29.
- **Fuel as a range** [lexicon] — 0.28–0.37 L/tank; the fuel rate was measured, the
  ripping hours from the cutting rate, the day plan is a decision. Source:
  `lesson_harvest.py`. → Ch 29.
- **The four real failure modes** — guessed deduction, unlevel base, one-sided
  raising, forcing the apex. Source: `lesson_build.py` `build_failures`. → Ch 25, 47.
- **A standing frame is not a home** [lexicon]. Day 14 gives a frame, not a shell/
  home/finished thing. Source: `lesson_build.py` `build_raise` (finale); `book.py` ch 32.
  → Ch 32.

## Economics / costing
- **A shelf price is mostly not the tree** [lexicon] — the 15 middlemen (fell, skid,
  haul, scale, saw, edge, trim, dry, plane, grade, bundle, ship, stock, shelve, sell)
  each take a margin. Sources: `lesson_wedge_why.py` `ww_stack`; `book.py` ch 2. → Ch 2.
- **What an hour at the log is worth** [lexicon] — one strut valued three ways
  (nominal 2×4, dressed 2×4, board foot); the dressed number is the honest (higher)
  one. Sources: `lesson_wedge_why.py` `ww_worth`; `franken_economics.py`. → Ch 55.
- **The part nobody counts** [lexicon] — culls, trips, hours, and boards that never
  make it; the store-bought overheads. Source: `lesson_wedge_why.py` `ww_store`. → Ch 45.
- **Measured and guessed, kept apart** [lexicon] — every film separates published /
  author / decided / estimated numbers before using them. Sources: `house_economics.py`
  (`KINDS`, `SOURCES`), `lesson_harvest.py`, `lesson_pine_value.py`. → Ch 45, 68 (front
  matter constants table).
- **Dome labour is a flat rate** [lexicon] — the parts list (40 triangles, 120 struts,
  120 brackets, 960 screws) does not grow with the dome; only the stick and the skin
  do. Source: `franken_economics.py`. → Ch 53.
- **Nine processes** — fell, rip, crosscut, fold, drill, screw, raise, sheathe, glass;
  seven are flat across diameters, two (ripping, sheathing) grow with material/area.
  Source: `franken_economics.py` `PROCESSES`. → Ch 54.
- **The solo limit** — a declared handling limit on the longest member one person
  carries alone; it splits the size table and defines the flat-rate band. Source:
  `franken_economics.py` `SOLO_LIMITS`, `solo_band`. → Ch 53.
- **The prototype was nearly free** — timber self-harvested, brackets folded from
  scrap, only screws changed hands; the real cost is the fibreglass skin. Source:
  `franken_economics.py`, `lesson_franken.py` `fk_cost`. → Ch 3, 45.
- **Substitution value is not income** — "what you did not spend" is not "what you
  earned"; it only counts if you were going to buy the timber. Sources:
  `lesson_why_build.py`, `book.py` ch 45. → Ch 45.
- **Money is stored labour / count it in hours of life** — buying the $4,800 frame is
  192 h of take-home; building it is 80 h + 32 h for its $800 of cash = 112 h. Source:
  `lesson_why_build.py`. → Ch 55.
- **Debt makes it larger** — an avoided dollar can be an avoided interest-bearing
  dollar ($4,800 → $10,922 over 30 yr @ 6.5%); interest builds nothing. Source:
  `lesson_why_build.py`. → Ch 55 or 45.
- **The build-vs-buy rule** — build while your hour creates more ($50/hr) than it
  earns; the production value is 2.5× the framing labour. Source: `lesson_why_build.py`.
  → Ch 55.
- **Where a house's money goes** — NAHB/Census: $200k house = $27.4k land, $128.7k
  building, $33.4k OH&P, $10.5k commission; framing = 16.6% of build = 10.7% of price;
  labour ≈ 25.7%; the manufactured home splits another way. Source: `house_economics.py`,
  `lesson_harvest.py`. → Ch 45.
- **Where a house's time goes** — 7.6 mo builder / 15.1 mo owner-built; the
  week-by-week schedule. Source: `house_economics.py`, `lesson_harvest.py`. → Ch 46.
- **Most of the saving is building your own, not the shape** — 37% of cost is
  shape-agnostic (fees, windows, cabinets, appliances, floors). Source:
  `lesson_harvest.py`. → Ch 45, 68.

## Energy / metabolism
- **The six motions** — walk, lift, carry, position, fasten, recover (493 s,
  41.1 kcal/placement). Source: `energetics.py`, `lesson_line.py`. → Ch 56.
- **Pandolf's load equation (1977)** — carrying cost is super-linear in load; the load
  term is squared. Source: `energetics.py` `pandolf_watts`. → Ch 56.
- **Winter's anthropometric tables** — per-segment body mass fractions; the body model
  (82 kg). Source: `energetics.py`. → Ch 56.
- **Fastening raises nothing and spends ~90% of the fuel** — the screw doesn't go up,
  the arm does; therefore attack the screw gun / the fastener count, not the lifting.
  Source: `energetics.py`, `lesson_line.py` `line_fasten`. → Ch 56.
- **m·g·h is the exact part; kilocalories are a model** — 622 J to raise one part is
  exact; metabolic kcal is a published task-intensity model, not measured. Source:
  `energetics.py`, `lesson_line.py` `line_work`/`line_model`. → Ch 56.
- **19% vs 0.16% efficiency** — during a lift 19% of fuel becomes height (near muscle's
  best); across the whole dome mechanical work is 0.16% of food energy; both are true.
  Source: `lesson_line.py` `line_efficiency`. → Ch 56.
- **The sustainable shift** — 334 W ≈ 3.50 METs; the ~350 W ceiling for an 8-hour
  shift; PFD (personal/fatigue/delay) allowance ~15%; 23 kg single-person lift limit;
  overhead work >1.75 m. Sources: `energetics.py`, `lesson_line.py`. → Ch 56.
- **The build in food** — 54,870 kcal/worker; 109,741 kcal total; ≈1,372 slices of
  bread. Source: `lesson_line.py` `line_food`. → Ch 56.

## Performance / shape advantages
- **Less skin for the same floor** [lexicon] — 997 ft² (box) vs 583 ft² (dome) = 42%
  less exterior for the same 314 ft² floor; skin is bought/insulated/weathered/heated
  four times over. Sources: `dome_advantage.py`, `lesson_kickstarter_v2.py`. → Ch 57.
- **Where the box wins** — row housing shares walls and beats a dome on envelope/floor
  outright; the crossover size is where the margin dies. Source: `dome_advantage.py`
  `envelope_crossover_sqft`. → Ch 57.
- **Standing vs floor area** — floor area ≠ floor you can stand up on; the headroom
  map colours usable floor. Sources: `dome_advantage.py` `standing_sqft`,
  `book.py` ch 43. → Ch 43.
- **The pony wall (cheapest square footage)** [lexicon `more_room_same_money`] — lift
  the shell on a short wall; 174 → 272 usable ft²; the last foot of radius has almost
  no headroom. Sources: `dome_performance.py` `pony_wall_ladder`, `lesson_build.py`
  `build_riser`, `lesson_kickstarter_v2.py`. → Ch 58.
- **The brim is already a gutter** [lexicon] — an overhanging brim throws water clear
  of the base joints and collects it; 18″ brim = 343 ft² = 7,259 gal/yr (~20 gal/day).
  Sources: `dome_performance.py` `WaterCatch`, `lesson_kickstarter_v2.py` `kick_water`.
  → Ch 59.
- **Radiative sky cooling paint** — ~96% solar reflect + strong 8–13 µm emission → a
  roof below air temperature in full sun; takes 15% off the remaining skin load.
  Sources: `dome_performance.py` `SkyCooling`, `lesson_kickstarter_v2.py` `kick_paint`.
  → Ch 60 or NEW.
- **The ten points** — the whole argument in ten lines. Source: `dome_performance.py`
  `ten_points`, `lesson_kickstarter_v2.py` `kick_points`. → Ch 68.
- **The energy claim this project will not make** [lexicon] — a dome is not
  automatically cheaper to heat; envelope helps but airtightness is build quality and
  no winter has been metered. Source: `dome_performance.py` `ten_points`,
  `book.py` ch 68. → Ch 68.
- **The honest finished-number** [lexicon] — the all-in finished figure is several
  times the bare shell, which is why the bare shell keeps getting quoted. Sources:
  `house_economics.py` `price_total`/`construction_total`, `book.py` ch 68. → Ch 68.

## Housing / the network
- **A pad, not a plot** — land is sold in acres; a dome sits on a serviced pad (deck,
  services, diameter) priced as one thing. Sources: `park_model`, `lesson_dome_park.py`,
  `lesson_seed_pitch.py`. → Ch 64.
- **The pad is the floor** — the arriving dome brings no foundation; the deck it lands
  on is the deck it lives on; nothing poured/dug/left behind. Sources: `lesson_dome_park.py`
  `dp_landing`, `lesson_byod_deepseek.py`. → Ch 64.
- **Foundation share** — the foundation is 8–63% of a dome across the catalogue; it's
  the only part you leave behind. Sources: `park_model.foundation_share`,
  `lesson_dome_park.py` `dp_foundation`. → Ch 63.
- **One hardware set, three sizes** — brackets/keys/fasteners that frame a small dome
  frame a large one unchanged; the counts AND the hub bill are flat; only the stick
  and skin move. Sources: `park_model.hardware_invariance`, `lesson_dome_park.py`
  `dp_hardware`. → Ch 61.
- **Buy for the next two steps** — oversize the hard-to-change parts (trenches,
  conduit, pad diameter, service capacity); undersize nothing else; a path is an
  order, not a drawing of the end state. Sources: `park_model.housing_options`,
  `lesson_byod_deepseek.py` `byod_growth`. → Ch 62.
- **The iris pad (one pad, every dome size)** — hinged blades close one oversized pad
  down to whatever dome stands on it; a mechanism on a foundation (can seize/fill
  with grit). Sources: `park_model.iris_*`, `lesson_bring_your_own_dome.py` `byod_iris`.
  → Ch 66.
- **The rotating foundation** — a circular footprint has no preferred direction, so a
  dome (unlike a rectangle) can track the sun; single-axis tracking ≈ +25%, but the
  ring costs per foot of circumference and usually crosses in the wrong place. Sources:
  `park_model.solar_layouts`, `park_facts.steps_solar`, `lesson_dome_park.py` `dp_solar`.
  → Ch 65.
- **Why a network beats a park** — a park is pads you rent; a network is pads that
  hold value because a dome can leave one and arrive at another; the service line's
  cost per pad falls as pads are added; resale with the haircut left in. Sources:
  `park_model.host_comparison`, `lesson_dome_park.py` `dp_network`. → Ch 67.
- **Semi-nomadic** — a house that comes apart (2 days quick, 2 weeks heavy), not a
  caravan; moves are a burst of work, so it's seasons/years not nights/weeks. Sources:
  `lesson_bring_your_own_dome.py` `byod_departure`. → Ch 67.
- **The host/tenant line** — below the line is the host's money (in the ground);
  above it is the tenant's (a drive away with them). Sources: `lesson_byod_deepseek.py`
  `byod_line`. → Ch 64, 67.
- **The crossover stay length** — hotel / short-let / apartment / dome-on-pad compared
  at every length; the month the dome stops being the expensive answer. Sources:
  `park_facts.steps_stay`/`steps_crossover`, `lesson_dome_park.py` `dp_landing`. → Ch 67.
- **The shared bathhouse** — a bathhouse means a small dome skips plumbing (the most
  expensive/regulated thing in a small dwelling). Sources: `lesson_dome_park.py`
  `dp_shared`. → Ch 67.

## Future systems (chapters 69–71)
- **The shower-cap soft shell (stacks hats)** — a soft shell replaces the hard hull;
  frame → quilted recycled-clothing layers → rain-slick cap, each new hat a size up;
  the hull becomes the later upgrade. Sources: `soft_shell`, `lesson_seed_pitch.py`
  `sp_cap`/`sp_quilt`, `book.py` ch 69. → Ch 69.
- **The $50 quilt** — ~130 t-shirts per layer, quilted by the owner; the cheapest and
  only insulation, tagged with the sewer's name. Source: `lesson_seed_pitch.py`
  `sp_quilt`, `lesson_pitch_hero.py`. → Ch 69.
- **The utility core / socket** — services up the middle through a column that carries
  the shower/sink/drain/outlets; the top of the dome is a socket; everything else
  snaps on outside; the core is ~⅕ of materials and moves to the next dome. Sources:
  `lesson_seed_pitch.py` `sp_core`/`sp_polyp`/`sp_move`, `lesson_module_build.py`. → Ch 70.
- **The mast and the floor** — a steel-core mast through the utility column (one
  penetration carries structure and services); the floor clamps to the mast at
  working height. Sources: `seed_model.mast_group`, `lesson_seed_pitch.py` `sp_mast`.
  → Ch 70.
- **The floating dome** — hang the mast from three cables between trees (saddles, not
  holes) + a brake winch; the floor is what it stands on up there; loads are the
  engineer's job. Sources: `seed_model.floating_report`, `lesson_seed_pitch.py`
  `sp_floating`. → Ch 71.
- **The S-lip roof seam** — the hull is moulded in 4 slices; an S-lip + gasket seals
  the returns. Source: `lesson_seed_pitch.py` `sp_slices`. → Ch 69 (or 40).

## Rendering / the pipeline (the book's "software" back matter + the `scratch` film)
- **Nothing on screen is typed in** [lexicon] — every figure is computed and
  self-proved before a frame renders. Sources: `render_presets.py`, `book.py` (front
  matter), `lesson_scratch.py`. → Front matter / back matter.
- **Every frame is a pure function of time** [lexicon] — programmatic video; a still
  at second *t* is reproducible. Source: `lesson_scratch.py`, `lesson_master.py`
  `ms_engine`. → Back matter.
- **From a triangle to a lit pixel** [lexicon] — the 7-station pipeline (phi →
  normalize → subdivide → project → measure → tube/buffer → matrices → shade).
  Source: `lesson_scratch.py`. → Back matter ("The Software in This Book").
- **Figures arrive with the words that say them** [lexicon] — callouts/tallies cued to
  narration. Source: `two_v_demo/callouts.py`, `lexicon_concepts.py`. → Back matter.
- **Render beats, not films** [lexicon] — a beat is one chapter rendered alone, so a
  fix re-renders 30 s not 29 min; sections are concatenations. Source: `beats.py`. →
  Back matter.
- **Corrections belong on camera** [lexicon] — a published error is fixed by a chapter
  that names it, not a silent re-cut (`lesson_wedge_why` is the model). Source:
  `lesson_wedge_why.py` `ww_buttcut`, `book.py` ch 48. → Ch 48.
- **Every render is a release** — landscape + phone cut + a release folder (thumbnails,
  captions, `description.md` copy). Source: `two_v_demo/release.py`, `CLAUDE.md`. →
  Back matter (operational; not a book concept per se).

## Story / tone
- **Keep the bones** [lexicon] — build the skeleton once, then replace/repair/upgrade/
  mutate (chassis/component, PC-building metaphor). Sources: `lesson_hype.py`. → Ch 3,
  60, 69.
- **Failure is affordable when the material is scrap** [lexicon] — cheap/salvaged
  material makes a $400 mistake a funeral nobody has to attend. Source: `lesson_hype.py`
  `hype_failure`. → Ch 47.
- **Send it to one person** [lexicon] — the one-share CTA. Source: `segments.py`
  `CTA_SHARE`. → Back matter / colophon (not a body chapter).
- **The Evil Dome Empire / Hoboclass** — the montage's comic frame (a rental
  portfolio's yield curve is the stated endgame). Source: `lesson_hype.py`. → Not a
  book chapter (tone reference only).
- **Fuller's brief + the Inuit igloo** — "housing cheap enough that a mother could
  raise her child"; compression domes already shipped in the harshest terrain. Source:
  `lesson_hype.py` (v3+). → Ch 1 or the front matter epigraph.

## NEW CHAPTER CANDIDATES (concepts with no home in chapters 1–71)
1. **"Hexagons and the Missing Angle"** — angular deficit, Descartes' twelve
   pentagons, the soccer-ball cage, warped subdivided panels, the zigzag rim. (From
   `lesson_hex.py`.) → propose *"The Dome That Is Not Triangles"*.
2. **"The Zome: Swept, Not Cut"** — the sweep, flat rhombi, one strut length, level
   rings, the golden rhombic triacontahedron, zome vs geodesic. (From `lesson_zome.py`.)
   → propose *"The Shape You Sweep Instead of Cut"*.
3. **"The Seam as a Machine"** — the four jobs of the seam (gutter / air barrier /
   dryer / condenser), dew-point control, seven modes, the desiccant drawers. (From
   `lesson_seam.py` + `lesson_cabin_seam_climate.py`.) → propose *"The Seam That Does
   Four Jobs"* (extends ch 16/44 into a climate-system chapter).
4. **"Building the Utility Core"** — the shop-floor build order and the two skipped
   tools. (From `lesson_module_build.py`.) → propose *"One Core, Every Dome"* (a
   how-to companion to ch 70).
5. **"The $20 Pine, Priced Up the Ladder"** — the full value ladder with stumpage
   numbers. (From `lesson_pine_value.py` + `lesson_pvtwo.py`.) → propose *"What a Pine
   Is Worth"* (a reference chapter beside ch 55).
6. **"Rendering a Dome, Pixel by Pixel"** — the geometry-to-pixel pipeline. (From
   `lesson_scratch.py`.) → the back-matter "The Software in This Book" already covers
   it; promote to a full reference chapter only if the reader wants it.

---

# Section C — Concrete visuals the films contain (book-figure candidates)

## A. Stills the book outline already cites (frame grabs via the `SHOT` renderer)
These are `book_figures` "lesson_still" specs in `book.py` (renderer `lesson_still`,
`lesson=` + `second=`):
- `front-frame` — **lesson="wedge", second=425.0** — the finished frame against sky
  (frontispiece, day fourteen).
- `franken-standing` — **lesson="franken", second=158.0** — the lumpy frankendome
  standing (ch 3 full-page plate).
- `worked-render` — **lesson="wedge", second=973.0** — the exact dome the tables
  specify (ch 24 plate).
- `standing-frame` — **lesson="wedge", second=842.5** — day fourteen, 120 members, two
  trees (ch 32 plate).

The stills archive `two_v_demo_output/` holds 914 stills in one subdirectory per
lesson (e.g. `two_v_demo_output/wedge/`, `two_v_demo_output/why/`,
`two_v_demo_output/cabin_wedge_explained/` …). Any scene function below can be pulled
as a frame grab with the `lesson=<key> second=<t>` convention.

## B. Scene functions worth becoming figures (name → what it shows)
**Wedge method (the book's core):**
- `wg_section` — one member end-on: bark out, pith in, both ends square (ch 12/14).
- `wg_split` — half, quarter, eighth, nothing thrown away (ch 5, 12).
- `wg_pack` — the honest 2×4 packing inside the circle (ch 7, 13).
- `wg_pinwheel` / `ww_flush` — one panel flat, three members same way round; the head
  arrives long and is cut flush (ch 15, 35–36).
- `wg_corner` — the corner nothing is cut to, 8× size (ch 15).
- `wg_pair` — two panels either side of one seam, each with its own stick (ch 18).
- `wg_gasket` / `ww_fold` — a section through one seam at its real fold angle, with
  the key (ch 16–17).
- `ww_channel` — the seam duct drawn on the solver's own 120-member dome (ch 14, 44).
- `ww_keystone` — point outward; the panel opening tapers and a panel drops in (ch 14, 69).
- `ww_turn` — the same stick four ways up, as seam pairs (ch 14).
- `ww_round` — the same disc packed with 2×4s vs split into eighths (ch 7, 13).
- `ww_chain` — the processing chain with the machines the wedge path never buys fading
  out (ch 2, 54).
- `ww_stack` — a shelf price stacked by who takes what (ch 2, 45).
- `ww_stick` — the comparison that does not flatter the wedge, then the one that does
  (ch 7, 10).
- `ww_bend` — a bent trunk: what one defect costs a short piece vs a long one (ch 19).
- `ww_sessions` — the two timed cutting sessions and the number they agree on (ch 29).
- `ww_worth` — one wedge against the studs it takes to match its section (ch 55).
- `ww_store` — the stack you buy, the part you throw away, and the trips it takes (ch 45).
- `ww_buttcut` — the compound butt cut and the cradle that makes it repeatable (ch 34).
- `ww_bench` — the jig built up one component at a time, then loaded (ch 30, 33).
- `ww_vbracket` / `fk_bracket_bend` / `fk_bracket_fitted` — the V-bracket, folded and
  seated inside the corner (ch 4).
- `ww_realdome` / `hv_dome` / `wb_dome` — the simulator's solved dome itself, wood and
  keys (ch 8, 24, 32).
- `wg_scale` — the dome two trees make, with somebody standing in it (ch 22–24).
- `wg_chain` — two roads from a standing tree to a member (ch 2, 54).
- `wg_explode` / `build_hubless_intro` — forty frames, each finished before it is
  lifted (ch 18, 31).

**Construction (2V) figures:**
- `build_error` — ⅛″ per strut multiplied by the golden ratio (ch 38).
- `build_rings` — the dome coloured by the course it is raised in (ch 8, 32).
- `build_size` — what a radius buys: floor, headroom, volume, skin (ch 20–21).
- `build_riser` / `kick_pony` — the riser/pony wall: cheapest headroom (ch 58).
- `build_deduction` / `build_endcut` / `build_bevel` — centre-vs-cut length, end-cut
  angle, the two fold angles (ch 34).
- `build_hubkit` — three ways to make the joint and what each costs (ch 17).
- `build_stock` — nesting both strut classes into two stock lengths (ch 21).
- `build_layout` — setting out the base decagon and the diagonal that proves it (ch 32).
- `build_foundation` — three ways to meet the ground at the same base ring (ch 39).
- `build_raise` / `build_apex` — raise ring by ring; closing the crown (ch 32).
- `build_skin` / `build_openings` — skin rim-upward; a door and a skylight (ch 40–41).
- `build_shelter_nest` / `build_shelter_size` — 40 panels nested on one sheet; what it
  buys with a person for scale (ch 40).
- `build_franken_stock` / `fk_stockpile` — five stick profiles; one log → eight sticks
  (ch 3, 12).

**Geometry figures:**
- `projection` / `midpoints` / `classes` — the projection step and the two-length
  collapse (ch 8–9).
- `sc_euler` — count corners, edges, faces (ch 8).
- `sc_hemisphere` — cut the sphere at the equator (ch 8).
- `sc_tube` — one strut blown up: ring, frame, skin (back matter).
- `sc_winding` / `sc_buffer` / `sc_clip` / `sc_light` — normals, the vertex buffer, the
  divide-by-w, the lighting sum (back matter).
- `hex_deficit` — the disc loses a wedge and rises into a cone (hex NEW chapter).
- `hex_dual` — a triangulated dome turns into a hexagon cage (hex NEW chapter).
- `hex_warp` — one hexagon lifted off its best-fit plane (hex NEW chapter).
- `zome_sweep` — point, stick, panel, solid (zome NEW chapter).
- `zome_golden` — thirty identical golden rhombi (zome NEW chapter).
- `world_frequency` — 1V–4V side by side at one radius (ch 49).
- `world_framing` — hubbed vs hubless (ch 18).
- `world_efficiency` — envelope per floor, ranked (ch 57).

**Energy figures:**
- `line_lift` / `line_skeleton` / `line_fasten` / `line_motions` / `line_food` — the
  lift with limbs coloured; the body model; where the fuel goes; the total in food
  (ch 56).

**Performance / network figures:**
- `kick_versus` — same floor, side by side: 997 vs 583 ft² (ch 57).
- `kick_wind` — wind finds nothing to push on (ch 57).
- `kick_brim` / `kick_water` — the overhanging brim; once it overhangs it is a gutter
  (ch 59).
- `kick_paint` — radiative sky cooling: the roof stops being a heat source (ch 60).
- `dp_pad_build` / `dp_pad_detail` / `dp_landing` — a pad assembling; the pad is the
  floor (ch 64).
- `dp_foundation` — the same design twice: on its own foundation vs on a pad (ch 63).
- `dp_move` — off one pad, across, onto the next (ch 67).
- `dp_hardware` — one design at three radii, the part list that does not move (ch 61).
- `dp_layers` / `byod_layers` — the shell comes off, a layer goes on, the shell goes
  back (ch 60).
- `dp_solar` — three ways to clad a shell, all turning on their pads (ch 65).
- `byod_iris` / `byod_catalog` / `byod_line` / `byod_host_design` — the iris pad, the
  nested pad catalogue, the host/tenant line, six host bays (ch 66, 64, 67, 62).
- `sp_cap` / `sp_quilt` / `sp_mast` / `sp_floating` / `sp_bay` / `sp_duct` /
  `sp_head` / `sp_invoice` — hats stacking; the quilted layer; the mast; hung between
  trees; one bay apart; the seam network lit; the wall cut through to show layer order;
  the dome assembling group by group with costs (ch 69–71).

## C. The Cabin World landmarks (for consistent camera setups)
`cabin_world.landmarks()` returns named positions (metres, z-up) a figure or camera
should aim at by name, never by copied coordinates: `log_end`, `log_axis`, `stump_top`,
`saw`, `stack`, `deck_centre`, `dome_centre`, `apex`, `gap` (the unfinished crown),
`gap_dir`, `builder`, `long_member`, `short_member`, `splits`. Layers: ground, forest,
deck, dome, builder, props. Hero camera `HERO_EYE = (1.10, -12.2, 3.30)`, low sun
`LIGHT = (0.55, 0.70, -0.45)`. This is the baseline scene every re-render is set in.

## D. The 12 Dome Creator presets (the design catalogue — `presets.py`)
Timber Workshop (3V, lumber, slab), Glass Studio Loft (4V, glass, deck), Split-Log
Homestead (2V, quarter-wedge hubless, cedar shakes, gravel), Whole Trunk Lodge 20′
(2V, full trunks, canvas), Grow Dome (3V, aluminium/polycarbonate), Hex Cell Pavilion
(3V, steel hex), Continuous Steel Arc Hangar (2V, steel ribs), Rebar Garden Dome (3V,
rebar lattice), Concrete Monocoque Form (3V, formwork), Woodland Hex/Square Mirror
(3V/4V mirror tiles), Treehouse Canopy Dome (2V, hex, platform). These are the
"twelve designs" the `world` / `world_chatgpt` / `all_domes` films tour, and map to
ch 49 (frequency), 57 (efficiency), 63–66 (foundation/pad/hardware).

## E. The five named narration cuts (chapter titles, for cross-referencing film↔book)
- **`eight-cuts-to-a-house`** (`lesson_wedge`): 29 chapters from "Eight cuts to a
  house" through "The round tree is not defective lumber" (matches `lesson_wedge.py`
  chapter list exactly).
- **`why-wedges-no-sawmill`** (`lesson_wedge_why`): 46 chapters from "Why I build like
  this" through "The whole argument on one page" (the beats plan in `beats.py`
  `WHY_SECTIONS` groups these into 10 sections).
- **`cabin-two-trees-all-at-once`** (`lesson_harvest`): 15 chapters from "Two trees"
  through "What this does not show" (+ CTA/outro) — the value/economics film.
- **`stem-cell-dome-campaign-v7`** (`lesson_seed_pitch`): 37 chapters from "A house
  you can take apart" through "Bring your own ground" (+ CTA/outro) — the stem-cell
  campaign.
- **`stem-cell-hero-cut`** (`lesson_pitch_hero`): 9 chapters — the ~100 s hero cut.

## F. Reusable segments (splice-in stings/outros — `segments.py`)
`outro` (contact card), `whoami` (credentials stack), `cta_share` (one share),
`cta_build` (build one), `party` (Frankendome party sting — 7 looks: raw, painted,
greenhouse, led_frame, led_panels, cardboard, patched), `franken_plain` (static
unflattered frankendome), `franken_party` (party anchored after the `franken` chapter).
Music is synthesized by `score.py` (drone / pluck / pad / riser / bloom / knock, D
major) — never sampled.

---

*Generated by introspecting the live `Lesson`/`Chapter` objects in the DomeSim
repository (`_inventory_introspect.py`) plus direct reads of `book.py`, the
`lesson_*.py` sources, `segments.py`, `beats.py`, `score.py`, `cabin_world.py`,
`render_presets.py`, `presets.py`, and the concept/economics modules.*
