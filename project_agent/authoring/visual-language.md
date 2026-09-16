# The visual language — everything you can build a film out of today

This answers two questions: *what already exists that I can use?* and *is it
modular enough that I can add to it easily?*

Short answer to the second: yes for anything that is a shape, a number or a
chapter; no for anything that needs a new kind of surface. There are five
layers, and which one you reach for decides whether your new idea is twenty
minutes of work or two days.

---

## The five layers

```
  5  whole worlds .......... the Dome Creator, the raw-wedge simulator, the
                             assembly line -- entire tools, borrowed through
                             a bridge, drawn with their own shaders
  4  visual objects ........ named nouns with knobs: a person, a pine tree,
                             a solved dome, a force arrow
  3  reusable drawers ...... timber, figures, icons, interiors, glam
  2  primitives ............ cylinder, sphere, box, disc, cone, arrow,
                             triangle, quad
  1  the renderer .......... batches, camera, overlay, narration, export
```

Everything you write lives at layers 2-4. Layer 1 you almost never touch.
Layer 5 is where the most impressive shots come from and it costs a bridge.

---

## Layer 2 — the primitives

Every painter receives two batches: `opaque` for solid things, `transparent`
for anything with alpha under 1. Both are `TriangleBatch`
(`two_v_demo/render_kit.py`) and take the same calls:

| call | use it for |
|---|---|
| `cylinder(start, end, radius, colour, sides=8)` | struts, poles, bars, pipes |
| `sphere(centre, radius, colour, rings=5, segments=8)` | nodes, hubs, blobs |
| `box(centre, size, colour)` | boards, panels, crates, cards |
| `disc(centre, radius, colour, segments=48)` | pads, floors, discs |
| `cone(base, tip, radius, colour, sides=10)` | roofs, tips, trees |
| `arrow(start, end, radius, colour)` | forces, flows, pointing |
| `triangle(a, b, c, colour, normal=None)` | shells, panels, faces |
| `quad(a, b, c, d, colour, normal=None)` | flat plates |

Points are `np.array([x, y, z])`. Colours are RGBA 0-1 tuples; the named ones
(`CYAN`, `AMBER`, `GREEN`, `RED`, `PURPLE`, `WHITE`, `MUTED`, `NAVY`, plus the
`_SOFT` variants and `SURFACE`, `GROUND`) are in `render_kit`.

Easing helpers live there too: `clamp`, `smoothstep`, `ease_in_out`. A reveal
is nearly always `ease_in_out(clamp(p * 1.3))`.

**Cost to add something new here:** minutes. This is just arithmetic and a
loop.

---

## Layer 3 — the reusable drawers

Things that already look right, so you never draw them twice.

| module | what it draws | the call |
|---|---|---|
| `timber.py` | real-looking wood with grain, knots, weathering | `draw_timber(batch, a, b, radius, seed, style=ROUGH)` |
| `figure.py` | an articulated human: posed, walking, carrying | `place_figure(joints, origin, yaw)` then `draw_figure(batch, joints)` |
| `icons.py` | 24 flat pictograms drawn onto the overlay | `WorldIcon(point, key, size)` appended to `app.world_icons` |
| `dome_interiors.py` | furnished interiors | used by the lookbook and composer |
| `glam_*.py` | cast, bodies, hair, wardrobe | the lookbook's people |
| `visuals_forest.py` | trees and forest floor | harvest films |
| `scene_composer.py` | whole staged scenes | composer films |

`timber.py` is the one to know. Every stick of wood in every film goes through
it, which is why they all look like the same forest.

**Cost to add:** an hour. Write a function that takes a batch and some points.
Keep it deterministic — seed anything random.

---

## Layer 4 — visual objects (the noun catalogue)

A visual object is a named thing with tuned knobs, so a chapter can say "put a
person here, 1.8 tall, facing left" instead of drawing limbs.

```python
stage = visual_objects.stage_for(app, opaque, transparent, origin=(4, 0, 0))
visual_objects.draw(stage, "pine_tree", fell=0.4, units_per_ft=0.3)
```

The catalogue (`two_v_demo/visual_objects.py`) currently holds 14:

| key | what it is | knobs |
|---|---|---|
| `wedge_member` | one raw wedge member | length, depth, lift, roll_deg |
| `timber_stick` | rough timber | length, radius, lift, seed, style |
| `board_2x4` | dressed two-by-four | length_ft, units_per_ft, on_edge, lift |
| `section_disc` | bucked section, end-on | radius, pieces, spread, lift |
| `wedge_shell` | pinwheel wedge dome | radius, reveal |
| `solved_dome` | the simulator's solved dome | radius, orientation, keys, alpha |
| `hub_dome` | 2V hub dome | radius, reveal, rough |
| `person` | a person | height, pose, walk, heading_deg |
| `force_arrow` | compression or tension | length, kind, thickness, lift |
| `dimension` | a dimension line | length, lift |
| `icon` | pinned pictogram | size, alpha, angle, lift |
| `pine_tree` | standing or felled | fell, limb, units_per_ft, icon |
| `log_sections` | log, bucked and split | buck, explode, units_per_ft, icon |
| `harvest` | the whole harvest, tree to wedges | fell, limb, buck, explode, ... |

Every one returns **anchors** — named points on the object — so you can hang a
label or attach the next thing without guessing coordinates.

**Cost to add:** an hour or two. Write the drawer, declare its knobs, register
it. It then works in films *and* in Presenter Studio automatically, because
the presenter reads the same registry.

---

## Layer 5 — whole worlds, through bridges

The most valuable shots in the catalogue are not drawn by the film at all.
They are borrowed from a tool that already models the thing properly.

| bridge | what it gives you |
|---|---|
| `raw_wedge_bridge.py` | the raw-wedge simulator's solved dome: 120 real members with compound butt cuts, seam keys, the jig |
| `creator_bridge.py` | the Dome Creator's finished buildings — materials, foundations, partitions, furniture, wiring — drawn by the Creator's own shader |

The Creator bridge is the newest and the pattern to copy:

```python
from two_v_demo import creator_bridge as creator

build = creator.preset("Glass Studio Loft")
creator.draw(app, build, cut_z=2.1)          # roof cut away: see inside
phase = build.phase(p)                        # the tool's own build order
creator.draw(app, build, limits=phase["limits"])   # a half-built dome
```

**Cost to add a new bridge:** a day, and worth it when the target tool already
has geometry you would otherwise re-model badly. The rule from CLAUDE.md
applies: a film about the wedge dome should show the simulator's dome, not a
sketch of one.

---

## The numbers layer

Nothing goes on screen that is not computed. The validated sources:

| module | what it computes |
|---|---|
| `geometry.py` | 2V chord factors, strut classes, fits, areas |
| `hubless_geometry.py` | hubless frame counts, seams, panels |
| `wedge_geometry.py` | tree yield, wedges, build plans |
| `dome_costing.py` | costed build variants |
| `book_math.py` | the book's arithmetic, both methods |
| `pine_value_economics.py` | the pine value ladder |
| `house_economics.py`, `why_build_economics.py` | house and method economics |
| `creator_facts.py` | the Dome Creator's menus, priced and counted |
| `al_build.py` | factory comparisons and assumptions |

Each has a `validate_*` that the selftests run. `py -3.12 -m project_agent
facts <id>` prints any of them; `list facts` shows the index.

---

## The overlay — what sits on top of the picture

You do not draw text in 3-D. You hand it to the overlay:

* **World labels** — `app.world_labels.append(WorldLabel(point, text, rgb))`.
  Pinned to a 3-D point, always facing the viewer. Set
  `label_layout="declutter"` on the lesson and they stop landing on each other.
* **World icons** — the same, with a pictogram instead of words.
* **Callouts and tallies** (`callouts.py`) — figures that arrive *with the
  words that say them*, cued to the narration, and a tally that must add up or
  the lesson refuses to load.
* **Chapter cards** — automatic from `title`, `promise`, `narration`.
* **The live calculation panel** — a chapter's `equations` tuple.
* **Math overlay** — `overlay="math"` on a chapter turns it into a worksheet:
  picture on the left, steps revealed one at a time on the right.

---

## Chapters, styles and cameras

A **chapter** is the unit: copy, duration, camera, and which painter runs.

Two styles: `teaching` (cards down the left, calculation panel) and `hype`
(one big line at the bottom, nothing else). A chapter can override the lesson
with `overlay=`.

The camera is `(yaw, pitch, distance)`, orbiting a target at `(0, 0, 2.25)`.
At `yaw=90` the camera sits on +Y and X runs across the screen — which is why
**rows go along X**. Anything laid along Y is laid into the screen.

For shots the orbit cannot express, a lesson can set `camera_fn` and drive the
camera itself (the drama films do this).

---

## Segments — reusable chapters

`segments.py` holds finished chapter runs you splice in rather than rewrite:
the outro contact card, the share call-to-action, the "who am I" bio, the
party sting, the plain frankendome. `compose_segments=True` on a render adds
the automatic ones.

---

## What the renderer gives you for free

* **Narration** — written per chapter, synthesized, and chapter durations are
  then *measured off the speech*, so timing follows the words.
* **Subtitles and a script** written beside every export.
* **Both shapes** — `orientation=both` renders landscape and a phone cut,
  re-framing the camera and restacking the overlay (`frame.py`,
  `portrait_ui.py`).
* **Teasers** — `teasers.py` builds a ~35-second hook from any film.
* **Beats** — `beats.py` renders chapter-scale pieces so a fix costs thirty
  seconds instead of half a day.
* **Append-only output** — a re-render never overwrites a published cut.

---

## So: how modular is it, really?

| what you want to add | where | effort |
|---|---|---|
| a new shape out of primitives | your painter | minutes |
| a new chapter in an existing film | that lesson module | minutes |
| a whole new film | one new `lesson_<key>.py` | an afternoon |
| a new reusable drawer (wood, cloth, glass) | `two_v_demo/` module | an hour |
| a new visual object with knobs | `visual_objects.py` | an hour or two |
| new computed numbers | a `*_facts.py` with a validator | an hour |
| a new overlay style | `app.py` draw_ui | a day, and think first |
| borrowing another tool's world | a new bridge | a day |
| a new material/shader | the renderer's shaders | hard — this is the one real wall |

The wall is surfaces. The film renderer has one shader: flat colour with a
diffuse term, a rim light and a specular. Anything needing a *pattern* — wood
grain per pixel, glass, mirror, procedural shingles — cannot be done by adding
a call to a painter. That is exactly why the Dome Creator bridge exists: the
Creator already has a shader that knows those materials, so the film borrows
its whole program rather than trying to imitate it.

If you want a new material, the cheap route is to fake it with geometry (that
is what `timber.py` does — visible grain is actual thin cylinders) and the
expensive route is a second shader program plus a bridge.
