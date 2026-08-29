# Masterclass lesson videos

Four narrated teaching videos rendered by the masterclass engine in
`two_v_demo/`, at 1920x1080 / 30 fps / libx264 CRF 18, in the same house
style as `2v-masterclass.mp4` at the repository root.

| File | Lesson key | Chapters | What it covers |
| --- | --- | --- | --- |
| `hex-dome-masterclass.mp4` | `hex` | 20 | Hexagonal domes: why a sheet of hexagons will never curve, why every hexagon cage needs exactly twelve pentagons, the one-hexagon frame dome you can cut from a single strut length, and what raising the frequency costs. |
| `zome-construction-masterclass.mp4` | `zome` | 19 | Zomes: rooms swept from a star of directions, every face a flat parallelogram, one strut length, level hub rings, and a true point on top. |
| `dome-construction-masterclass.mp4` | `build` | 32 | The 2V dome start to finish: the geometry, then sizing, hub systems, end cuts, bevels, stock and offcut, jigs, setting out, foundations, riser walls, raising, checking, skinning, openings, and the four things that actually go wrong. |
| `assembly-line-energy-masterclass.mp4` | `line` | 24 | The assembly line itself, and what it costs the people running it: an articulated two-person crew animated through all six motions of every part placement, with the mechanical work computed limb by limb and the metabolic cost totalled per motion, per station and per shift. |

Each video ships with three sidecars, written automatically by the
exporter:

* `<name>.srt` — upload-ready subtitles, one cue per spoken statement.
* `<name>-narration.md` — the timed voiceover script, for re-recording
  the narration in another voice or another language.
* `<name>-narration.m4a` — the finished AAC narration track on its own.

The `<name>-voice-.../` folder beside each video holds the per-chapter
speech clips. Keeping it makes a re-export offline and instant; deleting
it means the next export re-synthesizes every chapter.

## Regenerating any of them

```powershell
py -3.12 launcher.py
```

On the **Masterclass** tab, pick the Lesson, set Action to
`export_video`, set Size to `1920x1080`, choose the output path, and
click Launch. `Action = selftest` first is worth the few seconds: it
re-derives and re-checks every number the chosen lesson puts on screen
before a frame is drawn.

Three things worth knowing before starting a render:

* **Rendering is roughly four times slower than real time** on this
  machine, so the 32-chapter construction lesson is a long job. It runs
  headless and prints progress as it goes.
* **The narration needs the network, and only one export at a time.**
  Every chapter is synthesized through Microsoft's edge-tts endpoint on a
  cache miss. If `speech.platform.bing.com` cannot be reached, the export
  stops before rendering anything. Running several exports at once causes
  exactly that: the endpoint throttles, connections time out, and the name
  stops resolving. Chapter clips are cached, so a failed run resumes where
  it stopped rather than starting over.
* **There is a fully offline alternative.** Local Voice Studio's **Dome
  Narration** tab now has its own Lesson picker: it synthesizes the chosen
  lesson in a local voice profile, contacts nothing, and hands the
  renderer a narration plan instead of a cloud track.

## The energy lesson keeps two numbers apart

`assembly-line-energy-masterclass.mp4` reports two quantities that are
easy to confuse, and it never adds them together:

* **Mechanical work is computed and exact.** Raising a part is `m g h`,
  with the mass and the placement height read straight out of
  `al_build`'s element catalogue. Raising the *body* is the same
  calculation run once per body segment, using Winter's anthropometric
  tables in `two_v_demo/figure.py`.
* **Metabolic cost is a model.** A muscle holding a panel still does no
  mechanical work and burns fuel anyway, so joules of lifting cannot be
  converted to kilocalories of food without outside information. Task
  intensities come from the Compendium of Physical Activities, and
  walking under load uses the Pandolf equation, which is preferred to a
  flat figure because it takes the carried mass as an input.

Every constant taken on authority is listed, with its source, at the
bottom of `Action = report` for the `line` lesson. The lesson says so on
screen too, in the chapter called "The part that is a model".

The result worth knowing: across a whole dome, mechanical work is a
fraction of one per cent of the food energy, while during the lift itself
it is close to what muscle can manage at best. Both figures are true;
they answer different questions, and the gap between them is posture,
grip and holding still.

## Where the numbers come from

Nothing in these videos is a typed-in figure. Each lesson has a geometry
module that computes its own claims and a `validate_*` function that
proves them:

| Lesson | Module | Sample of what it proves |
| --- | --- | --- |
| `hex` | `two_v_demo/hex_geometry.py` | the truncated icosahedron really does have one strut length and one regular hexagon; every hexagon/pentagon cage has exactly twelve pentagons; the measured angle deficit is 720 degrees when the panels are flat |
| `zome` | `two_v_demo/zome_geometry.py` | F = n(n-1), V = n(n-1)+2, E = 2n(n-1); every face is a rhombus; a polar zome's level cut is one repeated saw setting at every height, and the golden zome's is not |
| `build` | `two_v_demo/build_geometry.py` | a strut's end cut is exactly half its central angle; a ten-sided base ring amplifies a strut error by exactly the golden ratio |
