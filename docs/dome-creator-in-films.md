# Putting Dome Creator buildings in a film

**In one sentence:** a film can now show the buildings the Dome Creator actually
renders -- wood grain, glass, mirror tiles, cedar shakes, foundations, partition
walls, benches, lamps and pipework -- instead of re-drawing a preset as tubes and
flat triangles.

This page is for anyone who wants to use that, or who is wondering why the domes
in the older catalogue film look so much plainer than the ones in the tool.

## What was actually missing

The Dome Creator builds a dome in two halves. `dome_model.py` works out the
geometry; `mesh_builder.py` assembles the finished building, and the fragment
shader in `dome_creator.py` is what knows the difference between a shingle, a
sheet of glass, a mirror tile and a poured concrete shell.

Until now the films only ever borrowed the first half. `lesson_world.py` rebuilds
each preset's geometry and then paints it with the film engine's own
primitives -- a cylinder per strut, a translucent triangle per panel. That is an
honest drawing of the frame, and it is why those domes have no material, no
foundation, no interior and no way to look inside.

Nothing was wrong with the film engine. It simply had never been handed the
tool's own mesh, because the two use different vertex formats: the film's shader
takes position, normal and colour, and the Creator's takes those plus a material
id, which is the thing that selects the pattern.

## How it works now

`two_v_demo/creator_bridge.py` imports the real modules, builds a design exactly
as the tool does, and hands the renderer the finished mesh. `MasterclassApp`
compiles the Creator's own shaders on first use and draws those meshes in a
second pass. A lesson that never asks for one is completely unaffected: nothing
is compiled, nothing is uploaded, and every film that shipped before this
renders exactly as it did.

From a scene painter it is two lines:

```python
from . import creator_bridge as creator

def scene_my_dome(app, opaque, transparent, p):
    build = creator.preset("Glass Studio Loft")
    creator.draw(app, build)
```

`creator.build(config_dict, name)` takes any design dict -- the same shape as a
saved `dome_design.json` -- so a sweep can vary one menu at a time. Meshes are
cached by configuration, because a painter runs thirty times a second and a
preset takes about half a second to assemble.

### What a draw request can carry

| argument | what it does |
| --- | --- |
| `offset`, `scale`, `yaw` | where the building stands, for lineups and grids |
| `limits` | draw only part of the mesh: the tool's own half-built dome |
| `cut_z` | the Creator's roof fade -- everything above this height is discarded, which is how you show an interior without moving the camera inside |
| `exposure` | brightness for that building alone |
| `lights` | point lights; by default the design's own lamp props, if they are switched on |

`build.phase(fraction)` is the interesting one. `mesh_builder.build_dome_mesh`
emits the building in real construction order and records a label, an hours
estimate and an index count at every work step, which is how the tool animates a
crew. Feed those counts to `limits` and the dome assembles itself on camera, in
the order a real crew would work:

```python
phase = build.phase(p)              # p is the chapter's 0..1 progress
creator.draw(app, build, limits=phase["limits"])
# phase["label"] -> "Fit plywood 54/105", phase["hours"] -> 44.6
```

## Things that will bite you

* **The Creator draws without face culling.** Its shader flips the normal on a
  back face, which is what makes a cut-away roof show a real interior instead of
  a hole. The renderer turns culling off for this pass and back on afterwards.
* **Put the film's ground away.** A Creator building arrives standing on its own
  foundation, and the renderer's dark plate and grid only cut across it. Set
  `ground="off"` on the lesson.
* **Labels go on `build.apex`, not `build.height`.** The height is the shell's
  own; a treehouse platform lifts the whole dome four and a half metres, so a
  label at the shell height lands inside the roof.
* **Phone cuts need the points.** This geometry never passes through the film's
  triangle batches, so the frame fit is handed the buildings' points separately
  (`creator_bridge.draw_points`). It happens automatically in `render`.
* **Math chapters have half a frame.** A worksheet takes the right half, so a
  stage composed for the whole frame comes back sliced. `lesson_all_domes.py`
  moves its stage left by a share of the camera distance and thins a sweep down
  to three domes; copy that if you build another one.

## The film this was built for

`all_domes` -- *All Domes*, rendered to
`deliverables/masterclass/all-domes-every-permutation.mp4`.

Thirty-four chapters: the twelve shipped presets as finished products, one dome
assembled step by step in the tool's own construction order, then one sweep per
menu in the customizer (frequency, frame style, strut shape, material, colour,
panel, cladding layer, foundation, partitions), the fit-out with the roof off,
eight designs drawn at random, and the arithmetic of how many buildings the menus
add up to.

Run it from the launcher's **Video preset** menu -- *ALL DOMES* -- or check it
without a render first:

```bash
py -3.12 -m two_v_demo.app --lesson all_domes --action selftest
```

The counts come from `two_v_demo/creator_facts.py`, which reads the menus out of
`dome_model.py`, `materials.py` and `workshop.py`, and reads the slider ranges
out of the Dome Creator's own menu code. Add a panel type to the tool and the
film's arithmetic moves on the next render without anybody editing a script.

Two things that module reports which are worth knowing:

* Two frame styles -- continuous steel arcs and the rebar lattice -- bill for hub
  connectors their own assembly never fits. The film says so on camera rather
  than averaging it away.
* No shipped preset contains a power source, and conduit runs start at a battery
  bank or a charge controller, so every design in the catalogue reports zero
  circuits until you place one.
