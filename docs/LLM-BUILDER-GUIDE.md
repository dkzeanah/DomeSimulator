# DomeSim — the builder's guide for an outside model

**Who this is for.** A language model working on this repository from outside it
(ChatGPT, another Claude, anything) that has been asked to *add something*: a new
idea from a video it transcribed, a new object in the 3-D world, a new calculation,
a new chapter, a whole new film. You are expected to write real code here — new
modules, new painters, new lessons, new shots — and have it render correctly the
first time a person runs the commands at the end of this file.

**How to use it.** Read §1 (the rules) and §2 (the map) completely. Then read the
files in §3 in the order given. Then follow the recipe in §6–§10 that matches what
you were asked to make. §11 is the checklist you must pass before handing anything
back; §12 is how to hand it back.

An earlier handoff (the *concept card*, `concepts/README.md`) said the ingesting
model never has to touch rendering code. That is still true for ideas that fit a
card — and a card is still the fastest lane (§10) — but it is not a limit. Anything
the card cannot express, you build in code, following this guide.

---

## 1. The rules (non-negotiable)

These come from `CLAUDE.md` at the repo root, which is the authority. A change that
breaks one of them is rejected, however good it looks.

1. **Numbers on screen are computed, not typed.** Every figure a film shows or says
   comes from a function. Where a number genuinely cannot be derived (a price, a
   bead size, a fan's pressure), it goes in a **declared-constants table** with a
   unit, a *kind* and a reason, and that table is put **on screen before it is
   used**. Kinds: `measured`, `claimed` (with its source and timestamp), `standard`
   / `nominal` (textbook or catalogue value, with reference), `estimate` or
   `assumption` (your judgement, with why). Keep measured values and estimates
   visibly separate.
2. **If two films state the same figure, they read it from the same function.**
   Never re-derive something a module already computes. Import it.
3. **Show the number that does not help.** Every film states at least one
   unflattering figure about its own idea. Several chapters in this repo exist only
   to do that.
4. **Reuse what exists.** Before drawing, computing or animating anything, find the
   module that already does it (§3, §4). A film about the wedge dome shows the
   *solver's* dome, never a sketch of one.
5. **Deliverables are append-only.** A rendered file that exists is never
   overwritten. Re-renders get `-v2`, `-v3` (`two_v_demo.deliverables.next_version_path`
   does this automatically — never add a way around it). Never edit an original to
   make a re-render.
6. **Corrections belong on camera.** If a published film said something wrong, the
   fix is a chapter that names the error and corrects it, not a silent re-cut.
7. **Stills before a render.** A render takes one to three hours. Shoot one still
   per chapter and look at every one before rendering (§11).
8. **Every render is a release.** A render produces the landscape cut, the phone
   cut, a release folder (thumbnails, captions, description with hashtags) and a
   teaser. The standard exporter does all of it; a film rendered any other way must
   build its release by hand (§9).
9. **New films are set in the Cabin World** (`two_v_demo/cabin_world.py`): the
   hilltop at sunset, the solver's dome on its pad, the builder, the log, the
   stump and chainsaw, the member stack. Aim at named landmarks, never copied
   coordinates. Music is synthesised (`two_v_demo/score.py`), never sampled.
10. **Never commit, and never touch** `my_voice/` (a person's voice data),
    `web/.env` (secrets), anything under `deliverables/` that already exists, or an
    original lesson module in order to make a re-render. The owner commits.

---

## 2. The map: how an idea becomes a video

```
facts module          painters                   lesson                    exporter
(arithmetic,   --->   (draw one chapter's  --->  (chapters, narration, --> landscape mp4
 constants,            3-D content from           equations, cameras,      phone mp4
 selftest)             the facts)                 selftest)                release folder
                                                   |                       teaser
                                                   v
                         lesson_registry.LESSONS["your_key"]
                         deliverables.DELIVERABLES   (output filename)
                         render_presets              (launcher buttons)
                         release.HASHTAG_BANK        (publishing copy)
```

* A **facts module** holds every number a film uses: declared constants, the
  functions that derive the rest, a `report()` and a `validate_*()` that asserts
  the film's claims are true. Example: `two_v_demo/seam_climate.py`.
* A **painter** is `def p_name(app, opaque, transparent, p)`: it adds triangles to
  two batches (opaque and see-through) and labels to `app.world_labels`, for
  chapter progress `p` from 0 to 1. It is called every frame.
* A **lesson** (`two_v_demo.lessons.Lesson`) is the film: a tuple of `Chapter`s, a
  dict of painters keyed by stage name, a camera function and a selftest.
* The **exporter** (`two_v_demo/app.py`, driven by `py -3.12 -m rerender render`)
  voices the narration, renders every frame on the GPU, encodes both cuts, splices
  the call-to-action and outro segments, and builds the release.

---

## 3. What to read, in order

Read these before writing a line. The right-hand column is what to take from each.

| # | file | take from it |
|---|---|---|
| 1 | `CLAUDE.md` | the rules, in the owner's words |
| 2 | `two_v_demo/lessons.py` — classes `Chapter` and `Lesson` | every field a film has; read the docstrings on `camera_fn`, `ground`, `label_layout`, `frame_fit`, `overlay`, `callouts` |
| 3 | `two_v_demo/lesson_cabin_pilot.py` | **the smallest complete film** (two chapters). Copy this to start |
| 4 | `two_v_demo/cabin_world.py` | the world: `paint(app, subject=...)`, `landmarks()`, `HERO_EYE`, `LIGHT`, `backdrop`, `LAYERS` |
| 5 | `two_v_demo/lesson_seam_climate.py` + `two_v_demo/seam_climate.py` | **the full worked example**: a facts module with a constants table and a selftest, a controller, 22 chapters, bench close-ups, dome-wide flows, a correction on camera |
| 6 | `two_v_demo/lesson_cabin_wedge_explained.py` | a second full film; how `channel_scene` bench shots and dome shots mix |
| 7 | `two_v_demo/render_kit.py` — class `TriangleBatch`, `WorldLabel` | the drawing primitives (§5) |
| 8 | `two_v_demo/shots.py` | the camera moves (§5) |
| 9 | `two_v_demo/channel_facts.py`, `two_v_demo/channel_scene.py` | the seam channel: room, fits, spacer, printing, hubs, and the bench specimen |
| 10 | `wedge_book/systems.py` | the seam module's parts, prices and physics (`air_barrier`, `water_comparison`, `declared(...)`) |
| 11 | `seed_world.py`, `seed_model.py` | the dome's own geometry and costs (`seed_world.geometry()`: radius, members, seam length, member volume…) |
| 12 | `two_v_demo/raw_wedge_bridge.py` | how the live raw-wedge solver reaches films (`model(...)`, `world_batches()`) |
| 13 | `two_v_demo/lesson_registry.py`, `two_v_demo/deliverables.py`, `render_presets.py`, `two_v_demo/release.py` | where a new film is wired in (§6 step 6) |
| 14 | `two_v_demo/cabin_stage.py` | how older films are re-staged on the exhibit platform; the pine-aware cinematic cameras |
| 15 | `rerender/README.md`, `rerender/__main__.py` | the re-render queue and the two commands that make a film |
| 16 | `concepts/README.md`, `concepts/card.py` | the concept-card fast lane (§10) |
| 17 | `two_v_demo/score.py`, `two_v_demo/segments.py`, `two_v_demo/teasers.py` | music beds, plug-in segments, teasers — reuse, do not re-author |

Other facts modules worth knowing before you compute anything yourself:
`two_v_demo/wedge_geometry.py`, `hubless_geometry.py`, `dome_costing.py`,
`house_economics.py`, `book_math.py`, `franken_economics.py`.
`grep -rn "def <what you need>"` before writing it.

---

## 4. The world: coordinates and places

* **Units: metres. z is up.** The dome's centre is at the origin, standing on its
  pad. `cabin_world.landmarks()` returns every named place — **read, never
  retype**:

  | field | what |
  |---|---|
  | `dome_centre`, `dome_r`, `apex` | the dome's sphere centre, radius, top |
  | `deck_centre`, `deck_r` | the pad's top surface |
  | `gap`, `gap_dir` | the unfinished crown and the direction to it |
  | `builder` | where the builder stands |
  | `log_end`, `log_axis`, `trunk_r` | the split log in the foreground |
  | `stump_top`, `saw` | the stump and the chainsaw on it |
  | `stack` | the member stack |
  | `long_member`, `short_member`, `splits` | sizes from the solver |

* `cabin_world.HERO_EYE` is the dressed side (south): the missing crown triangles
  and the builder face it. Cameras usually look from this side.
* **The forest.** Seventy pines stand outside a clear corridor running north–south
  (`|x| < 7.5 + 0.35·max(0, y)`), and outside 9 m of the dome. Their canopies are
  4–5 m wide. A camera placed in them, or looking through them, ruins a shot:
  `cabin_stage.pines()` lists every pine and `cabin_stage.blocked(eye, target)`
  tests a sight line.
* **Two work areas already built:** the seam **bench** (`channel_scene.BENCH_A`,
  `BENCH_B`, in the foreground, with `channel_scene.Frame(bench, seam_type).at(x_in,
  y_in, along_m)` converting seam-section inches to world metres) and the **exhibit
  platform** north of the dome (`cabin_stage.CENTRE`, `RADIUS`, `HEIGHT`).
* **New places** go in as named things, not numbers inside a painter: a module
  constant with a docstring saying why it is there, or a new field on `Landmarks`
  if every film will use it.

---

## 5. Drawing and filming

### Painters

```python
def p_example(app, opaque, transparent, p):      # p: 0 -> 1 across the chapter
    cw.paint(app)                                # the whole world, cached on the GPU
    m = cw.landmarks()
    opaque.box(m.apex + [0, 0, 0.5], (0.3, 0.3, 0.3), (1.0, 0.4, 0.3, 1.0))
    app.world_labels.append(WorldLabel(m.apex + np.array([0, 0, 0.9]),
                                       f"{F['seams']} SEAMS", (255, 205, 130)))
```

* `TriangleBatch` methods: `triangle(a, b, c, rgba, normal=None)`,
  `quad(a, b, c, d, rgba, normal=None)`, `box(centre, (sx, sy, sz), rgba)`,
  `cylinder(start, end, radius, rgba, sides=8)`, `cone(base, tip, radius, rgba,
  sides=10)`, `arrow(start, end, radius, rgba)`, `sphere(centre, radius, rgba,
  rings=5, segments=8)`, `disc(centre, radius, rgba, segments=48)` (flat, facing up). Geometry colours are **RGBA floats 0–1**.
* **Label colours are 0–255 integers.** Handing a label 0–1 colours renders its text
  nearly black — a real bug that shipped once.
* `opaque` vs `transparent`: see-through things (a key shell, glass, a ghosted
  part) go in `transparent` with alpha < 1.
* **Heavy geometry that never changes** is built once and handed over by key:
  `app.static_layer("mymodule:thing", lambda: build_thing(), subject_points)`, with
  `build_thing` decorated `@lru_cache`. Per-frame geometry (anything that moves
  with `p`) goes in the batches. A painter that rebuilds thousands of triangles
  every frame makes a three-hour render a ten-hour one.
* `subject_points` (a few points round the thing) tell the phone cut what to keep
  in frame. Scenery passes none. For a close-up on something other than the dome,
  call `cw.paint(app, subject=False)` so the phone cut does not frame the dome.
* Painters must be **deterministic in `p`**: seeded random only
  (`np.random.default_rng(3)`), never time or global state.
* Dome Creator buildings are drawn with `two_v_demo.creator_bridge.draw(app, build,
  offset=..., scale=..., yaw=...)`, not triangle batches.

### Cameras

`camera_fn(app, chapter, progress, width, height) -> (eye, target, fov_degrees)`.
Build a table of moves from `two_v_demo/shots.py` and let `shots.by_chapter(table)`
dispatch by chapter slug:

| move | use |
|---|---|
| `orbit(target, radius, height, start_deg, sweep_deg, fov)` | establishing, dome-wide |
| `push_in(target, start_eye, end_eye, fov_start, fov_end)` | the default: slow move toward the subject |
| `crane_reveal(target, start_eye, end_eye, fov_start, fov_end, look_start=)` | openers and closers |
| `low_hero(target, radius, eye_height, start_deg, sweep_deg, look_up, fov)` | heroic low arc |
| `dolly_zoom(target, direction, d0, d1, subject_width=, height=)` | the "why" moment |
| `fly_through(eye_points, look_points, fov)` | a path past several things |
| `top_down_spin`, `hold` | plans; a still frame |

Rules: fov between 20 and 70 (40–48 looks like cinema here; the renderer's house
fov is 48); keep the eye out of geometry, out of the pines and above the ground;
aim at landmarks or at points computed from the thing you drew. The selftest
checks every move is finite and not zero-length (copy the pattern).

### Chapters

```python
Chapter(slug, "07", "Title", "promise line",
        (narration,),            # one string, built from F[...] with f-strings
        (equation, ...),         # the LIVE CALCULATION panel: the arithmetic, shown
        seconds,                 # silent timeline; use max(8, words / 2.5 + 1.5)
        (0.0, 0.0, 0.0),         # legacy orbit camera, unused with camera_fn
        stage)                   # key into the lesson's scenes dict
```

* Narration: every number comes from the facts dict through an f-string. Write
  numbers the way a voice should say them (`deg()` in `lesson_seam_climate.py`
  says "minus 6", not "-6").
* The equations panel is where declared inputs are shown: list them, marked
  (assumed) / (estimate) / (nominal), in a chapter **before** the chapter that uses
  them.
* `overlay="math"` turns a chapter into a worksheet; `callouts` bring figures in
  with the words that say them (`two_v_demo/callouts.py`).

---

## 6. Recipe: a new film

1. **Facts module** `two_v_demo/<topic>.py`:
   * `CONSTANTS = ((name, value, unit, kind, reason), ...)` and `C = {...}`;
   * functions that derive everything else, importing existing modules for
     anything already computed (dome geometry from `seed_world.geometry()`, seam
     room from `channel_facts`, prices from `wedge_book.systems.declared`, …);
   * `report() -> str`, and `validate_<topic>()` asserting: textbook check values;
     every claim the film will make (including the unflattering one);
   * `if __name__ == "__main__": validate_...(); print(report())`.
2. **Film module** `two_v_demo/lesson_<topic>.py`, copied from
   `lesson_cabin_pilot.py` (small) or `lesson_seam_climate.py` (full):
   * `F = _facts()` — a dict of every number the film states, built once;
   * painters `p_<slug>` using `cw.paint` plus your own geometry;
   * `MOVES = _moves()` and `camera = shots.by_chapter(MOVES)`;
   * `CHAPTERS` built with a `_ch(n, slug, title, promise, narration, equations)`
     helper; slugs equal stage keys;
   * `validate_<topic>_film()` calling the facts selftest, `cw.validate_cabin_world()`,
     checking every chapter has a painter and a sane camera, and asserting the
     narration's claims against `F`;
   * the lesson:

     ```python
     MY_LESSON = Lesson(
         key="cabin_<topic>", brand="DOMESIM", title="Human Title",
         chapters=CHAPTERS, scenes=SCENES, selftest=validate_<topic>_film,
         snapshot_prefix="cabin_<topic>", camera_fn=camera, ground="off",
         backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
         audio_bed="beds/cabin-explained", audio_bed_gain=0.12)
     ```

     Keys of new Cabin World films start `cabin_`. `ground="off"`,
     `backdrop=cw.backdrop` and `light=cw.LIGHT` are what put it in the Cabin World.
3. **Music.** Reuse `beds/cabin-explained`, or synthesise a bed with
   `score.loop_bed(seconds, seed=N)` + `score.write_wav(track,
   Path("assets/audio/beds/<name>.wav"))` and set `audio_bed="beds/<name>"`.
4. **Selftest** (§11). Fix until it passes.
5. **Stills**, and look at every one (§11).
6. **Wire it in** — four one-line additions, each beside the
   `cabin_wedge_explained` entry that is already there:
   * `two_v_demo/lesson_registry.py`: import the lesson, add it to the `LESSONS` tuple;
   * `two_v_demo/deliverables.py`: `Deliverable("cabin_<topic>", "<file-name>.mp4",
     "one-paragraph note", compose=True)` — a filename that does not already exist;
   * `render_presets.py`: a `_video(...)` preset and a `..._stills` preset;
   * `two_v_demo/release.py`: an entry in `HASHTAG_BANK`.
7. **Render** (§9).

---

## 7. Recipe: a new thing inside the 3-D world

(A machine, a tank, a solar array, a desiccant tower, a new prop.)

* Build it in its own module as a function returning a `TriangleBatch`, sized from
  the facts module that owns its dimensions — never from typed numbers. Cache it
  with `@lru_cache`.
* Place it relative to `landmarks()` (or a new named constant with a reason), and
  draw it from a painter with `app.static_layer("<module>:<thing>", ...)`.
* Add a `validate_...()` that checks it stands where it should: above the ground,
  clear of the deck, the dome, the log and stump, the platform and the forest
  (`cabin_stage.validate_cabin_stage` shows the pattern).
* **Adding it to the baseline world for every film** (`cabin_world.LAYERS`) changes
  every future render, including the re-render queue. Do not do this unless the
  owner asked; propose it and leave it as a separate layer until then.

---

## 8. Recipe: a new camera move, shot kind or re-staging rule

* New moves go in `two_v_demo/shots.py` as functions returning `Shot` (a callable
  `p -> (eye, target, fov)`), with a docstring and a case in `validate_shots()`.
* Re-staged old films take their cameras from `cabin_stage.cinematic(...)`. It
  measures the exhibit, frames it by width and height, keeps out of the pines
  (`clear_view`), out of the exhibit (`clear_of`) and inside the corridor (`safe`).
  Run `validate_cabin_stage()` after any change, then shoot stills of at least three
  re-staged films.

---

## 9. Commands (Windows, from the repo root, Python 3.12)

```bat
:: the arithmetic and its checks
py -3.12 -m two_v_demo.<topic>

:: the film's selftest
py -3.12 -c "from two_v_demo.lesson_registry import LESSONS; LESSONS['cabin_<topic>'].selftest(); print('ok')"

:: one still per chapter, 70% of the way in -> two_v_demo_output\cabin_<topic>\
py -3.12 -m rerender stills cabin_<topic>

:: THE render: landscape + phone cut + release folder (+ teaser); 1-3 hours
py -3.12 -m rerender render cabin_<topic>

:: only if a film was rendered some other way: build its release by hand
py -3.12 -m two_v_demo.release --lesson cabin_<topic> --video deliverables\masterclass\<file>.mp4

:: a teaser on its own
py -3.12 -m two_v_demo.teasers --lesson cabin_<topic>

:: the launcher (every one of the above as buttons)
py -3.12 launcher.py
```

Where things land: cuts in `deliverables/masterclass/` (`<name>.mp4`,
`<name>-vertical.mp4`, a narration plan and a review file), the release in
`deliverables/releases/<name>/`, teasers in `deliverables/teasers/`, stills in
`two_v_demo_output/<lesson key>/`.

Practicalities:
* **One render at a time.** Two GPU jobs at once has crashed a render with no
  traceback. Stills during a render are a risk too.
* The narrator is Microsoft's `en-US-AndrewMultilingualNeural`
  (`my_voice/default_voice.json` says `andrew`); do not change it.
* ffmpeg comes from `imageio_ffmpeg`; the one on PATH is ancient and fails on
  filters.

---

## 10. The fast lane: a concept card

When the idea is one mechanism with a handful of numbers — "what would X do for this
dome?" — write a card instead of code: a JSON file in `concepts/cards/`, checked by
`py -3.12 -m concepts check`, filmed by `py -3.12 -m rerender render
concept_<slug>`. `concepts/README.md` is the full spec; `py -3.12 -m concepts facts`
lists the dome's own numbers a card may use by name.

**Graduate to code** when the idea needs any of: its own world geometry beyond
boxes, cylinders and flows; logic (a controller, a search, a simulation); a
calculation the card's safe arithmetic cannot express; figures another film will
also state (they must come from one function); or more than about six beats.
`two_v_demo/seam_climate.py` is exactly that graduation: a controller and bed
physics no card could hold.

---

## 11. Before you hand anything back: the checklist

1. `py -3.12 -m two_v_demo.<topic>` prints the report and raises nothing.
2. The film's selftest passes.
3. `py -3.12 -c "from two_v_demo import deliverables as d; d.validate_deliverables()"`
   and `py -3.12 -c "import render_presets as r; r.validate_render_presets()"` —
   no new failures. (One old failure about `2v` and `seam` is known and not yours.)
4. **Stills**: `py -3.12 -m rerender stills cabin_<topic>`, then open every PNG
   and check, chapter by chapter:
   * the subject is in frame and readable; nothing is behind a pine, a member, the
     hillside or the builder;
   * the camera is not inside anything (a slab of flat colour filling the frame
     means it is);
   * every label is on screen, legible, and not on top of another;
   * the equations panel shows the declared inputs before they are used;
   * nothing the narration mentions is missing from the picture.
5. `grep` your narration strings for digits you typed by hand. There should be none
   outside f-string placeholders (dome words like "2V" excepted).
6. The unflattering number is in the film, and the selftest asserts it.

---

## 12. Handing it back

Give the owner:
* the list of **new files** and, for **changed files**, the exact lines changed
  (a unified diff is best);
* the output of the checks in §11 (paste them);
* the four commands they should run, in order: selftest, stills, render — and
  what each should print;
* any declared constant you were unsure of, called out.

Do not commit. Do not render over an existing file. Do not edit an original lesson,
`my_voice/`, `web/.env` or anything already in `deliverables/`.

---

## 13. Pitfalls this repo has already paid for

* **Labels in 0–1 colours** render near-black. Labels take 0–255.
* **Cameras inside geometry or pines.** Measure what you drew; test sight lines
  (`cabin_stage.blocked`); look at stills.
* **A thin, tall subject framed by width** puts the camera a metre from it. Frame
  by height too.
* **Spliced segments** (the call to action, the outro) are chapters with stages the
  lesson has no painter for. `shots.by_chapter` falls back to the house camera for
  them; a custom camera function must do the same.
* **`perspective(48.0, ...)`** is a literal the phone-cut fitting relies on. Leave it.
* **The dome in a film is the solver's dome.** `raw_wedge_bridge` and
  `channel_scene._world()` give you its seams, vertices and faces;
  `seam_climate.classify(model)` sorts its seams into bands.
* **Two trees.** `BOOK_TREE` and `DEFAULT_LOG` are different logs; check which one
  a figure should come from.
* **A number that changes.** Films read figures at import; if you change a declared
  constant, every film that states it changes too. That is intended — say so in
  your handback.

---

## 14. The worked example to copy: *Which Way the Seam Breathes*

| file | what it shows |
|---|---|
| `two_v_demo/seam_climate.py` | a facts module with psychrometrics (Magnus dew point, humidity ratio), a **controller** (`decide(Sensors) -> Decision`) that turns three questions into seven modes, eleven declared weathers with the owner's expected answers, the dome's seams sorted into bands from the solver (`rings`, `classify`), packed-bed pressure drop (`ergun`), desiccant capacity and regeneration, and a selftest that asserts every claim |
| `two_v_demo/lesson_seam_climate.py` | 22 chapters in the Cabin World: bench close-ups with plates drawn on each skin of the seam, dome-wide bands coloured by level with moving air, a correction of an earlier film on camera, declared inputs shown before use, and the numbers that argue against the idea |
| stills: `py -3.12 -m rerender stills cabin_seam_climate` | what "ready to render" looks like |
