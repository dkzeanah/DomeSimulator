# The video pipeline, traced

A code-level companion to `programmatic-video-guide.md`. That document
explains the *method*; this one explains the *machinery* — which module
is called in what order to turn a Python `build()` function into a
narrated MP4, and where every control lever actually lives.

Written against the tree as of commit `a2167d6`, updated when the
masterclass renderer became lesson-driven.

---

## 0. There are three separate pipelines in this repo

Do not confuse them. They share a house style (1920x1080, 30 fps,
libx264, CRF 18, `+faststart`, an `.srt` sidecar) but no code.

| | Pipeline | Entry point | Picture comes from | Use it for |
|---|---|---|---|---|
| **A** | **Presenter** | `presenter_studio.py` | Live 3-D, rendered per frame by OpenGL | Everything. This is the real engine. |
| **B** | **Masterclass lessons** | `two_v_demo/app.py` -> `export_video()` | Live 3-D, one of four fixed chapter lessons | Geometry and construction lessons |
| **C** | **Slideshow trailer** | `deliverables/launcher_trailer/build_launcher_trailer.py` | Still PNGs drawn with PIL | Title cards / montage over pre-made renders |

Everything below is **pipeline A** unless it says otherwise.

### 0a. The local-voice side door

`local_voice_studio/dome.py` is not a fourth renderer — it is an
alternative *voice source* that feeds pipeline **B**:

```
build_dome_narration(project, profile)
    synthesize_chatterbox(...)        your own cloned voice, on your machine
    -> chapter WAVs + a narration plan JSON
export_dome_video(plan_path, out)
    _find_renderer_command()          probes for an interpreter with pygame+moderngl
    launcher_common.write_config("two_v_masterclass", {..., "local_narration_plan": ...})
    -> spawns two_v_masterclass.py, which renders against the plan instead of edge-TTS
```

Two limits worth knowing:

* **It only wires into pipeline B**, and inside pipeline B it is still
  hardwired to the 2V lesson: `local_voice_studio/dome.py` does
  `from two_v_demo.lessons import CHAPTERS`. Pointing it at the hex, zome
  or construction lessons means handing it the same `chapters` argument
  the rest of pipeline B now takes. Nothing equivalent exists for the
  Presenter — swapping the Presenter's voice source would mean giving
  `narrate.prepare_narration()` a pluggable backend.
* **`synthesize_chatterbox()` takes no language argument.** As wired it
  is English-only, so the local-voice route does not currently help with
  section 7. F5-TTS (exportable via `backends.export_f5_dataset`) is the
  path that could, since community F5 checkpoints exist for several of
  the target languages — but that is a fine-tune project, not a config
  change.

### 0b. Pipeline B is no longer one lesson

`two_v_demo` renders **five** lessons through one renderer, selected by a
`lesson` key on the launch ticket (`2v`, `build`, `hex`, `zome`, `line`).

```
lessons.py          Chapter, Lesson, and the 14-chapter 2V timeline
lesson_build.py     32 chapters: the 2V dome, start to finish
lesson_hex.py       20 chapters: hexagonal / Goldberg domes
lesson_zome.py      19 chapters: zomes / zonohedra
lesson_line.py      24 chapters: the assembly line's energy ledger
lesson_registry.py  the only module that imports all of them
render_kit.py       TriangleBatch, shaders, colours, easing, no GL state
figure.py           an articulated body: skeleton, poses, drawing
energetics.py       what a motion costs, from al_build's own catalogue
```

`figure.py` and `energetics.py` are only used by the `line` lesson, but
they are deliberately independent of it: the figure knows nothing about
domes, and the energy model takes any object with `weight`, `labor_min`,
`centroid` and `floor_point` -- which is exactly `al_build.Element`.

`MasterclassApp.__init__(lesson=...)` stores `self.chapters`, and
`build_scene(stage, progress)` looks the stage up in `lesson.scenes`
first, falling back to its own `scene_<stage>` method. That fallback is
load-bearing: `lesson_build` reuses the original 2V derivation scenes
(`rigidity`, `platonic`, `coordinates`, `icosahedron`, `midpoints`,
`projection`, `classes`, `audit`, `cutlist`) by name, and only supplies
painters for the construction stages.

`dynamic_equations(stage)` composes: the built-in 2V figures first, then
whatever `lesson.equations(app, stage)` returns. A reused stage therefore
keeps its live numbers and the lesson can add more.

`narration.py`, `audio.py` and `lessons.chapter_at_time` all take an
explicit `chapters` tuple defaulted to the 2V one, which is why nothing
about pipeline A or the older callers changed.

Each lesson owns a geometry module that computes and then proves its own
claims; `Action = selftest` runs the lesson's proof as well as the 2V one:

| Lesson | Geometry module | Proves, among other things |
| --- | --- | --- |
| `2v` | `geometry.py` | 42/120/80 sphere, two chord classes, Euler 2 |
| `build` | `build_geometry.py` | end cut is exactly half the central angle; a ten-sided base ring amplifies a strut error by exactly phi |
| `hex` | `hex_geometry.py` | the truncated icosahedron has one strut length and one regular hexagon; every cage has exactly twelve pentagons; measured deficit is 720 degrees when the panels are flat |
| `zome` | `zome_geometry.py` | F = n(n-1), V = n(n-1)+2, E = 2n(n-1); every face a rhombus; a polar zome's level cut is one repeated setting at every height and the golden zome's is not |
| `line` | `figure.py` + `energetics.py` | segment masses sum to the whole body exactly once; Pandolf is superlinear in load; raising a load costs more than lowering it; a whole build lands between 1,800 and 4,500 kcal per shift and under the sustainable working rate |

**Adding a sixth lesson** is: a geometry module with a `validate_*`
function, a lesson module with `CHAPTERS` + `SCENES` + a `Lesson`, one
line in `lesson_registry.LESSONS`, and one entry in the launcher's Lesson
dropdown. Local Voice Studio's lesson picker reads the registry, so it
needs no change.

### 0c. The `line` lesson costs motions, and says which half is modelled

`energetics.py` turns each `al_build` element into six named motions --
walk, lift, carry, position, fasten, recover -- plus a recovery
allowance, and costs each one. It keeps two quantities strictly apart:

* **Mechanical work** is computed. `m g h` for the part, and the same
  calculation per body segment for the body, using Winter's tables. It
  traces entirely to element masses and placement heights.
* **Metabolic cost** is modelled, from Compendium task intensities and
  the Pandolf load-carriage equation. Every such value is an
  `ExternalConstant` with a `source`, and `Action = report` prints all of
  them.

Do not let those two merge. `BuildEnergy.mechanical_fraction` is a
fraction of a per cent across a build, while `motion_efficiency()['lift']`
is near the muscle ceiling; a change that makes those two similar has
broken one of them.

Two rendering conventions this lesson introduces, both of which will bite
anyone extending it:

* **Bodies are drawn at `FIGURE_SCALE`.** `joint_positions` works in real
  metres, but the renderer's world is about five units across and the
  camera looks at a fixed point 2.25 units up, so an unscaled figure came
  out small and sat below frame centre.
* **+X is screen left.** The lesson's cameras sit on the +Y axis, which
  is what makes a sagittal squat readable, and it also reverses left-to-
  right order. `_bars` and the motion sequence both lay out from +X down.

---

## 1. The call chain, in order

```
launcher.py  (Tk GUI, "Presenter Studio" tab)
  |- go_presenter()                     builds a cfg dict from the form fields
     |- launcher_common.run(...)        writes a JSON "launch ticket" to .launcher_configs/
        |- spawns  presenter_studio.py
             |- main()
                  |- launcher_common.consume_config("presenter")   reads + DELETES the ticket
                  |- load_presentation(cfg)      ->  a Presentation object   (section 2)
                  |- PresenterApp(pres, headless=True).export(...)          (section 4)
```

The launch ticket is the whole GUI-to-tool contract. `consume_config`
returns `{}` when the tool is started directly, which is why running
`presenter_studio.py` on its own opens the Scene Composer on a blank
movie instead of erroring.

### 1a. The four ways a Presentation gets loaded

`presenter_studio.load_presentation()` picks exactly one source:

| cfg key | What happens |
|---|---|
| `demo` | `importlib.import_module(DEMOS[key]).build()` — the 13-entry `DEMOS` registry at the top of `presenter_studio.py` |
| `script` ending `.json` | `Presentation.from_json(path)` |
| `script` ending `.py` | loaded by file path, then `module.build()` is called |
| `prompt` | `presenter.prompt.parse_brief(text, env, focus)` -> a *skeleton*, then a default dome stage is stapled onto every scene |
| *(none)* | falls back to `presentations.airflow_dome` |

---

## 2. The document model — `presenter/script.py`

Four plain dataclasses. Everything about a video is one of these.

```
Presentation(title, author, scenes, fps=30, size=(1920,1080),
             voice="en-US-AndrewMultilingualNeural", voice_rate="-3%")
  |- Scene(slug, title, environment, shots, world)
       |- Shot(slug, duration, lens, perspective, focus, orbit, dolly,
               yaw, pitch, height_bias, narration, caption, panel,
               actions, xray)
            |- OverlayPanel(title, bullets, equations, stats, position,
                            anchor, visible)
```

Facts that matter:

* **`duration` is a minimum, not a duration.** Narration stretches it
  (section 4b). This is why the preview in the Composer and the exported
  file are different lengths.
* **`world` lives on the Scene, `actions` live on the Shot.** The Scene
  says what is on stage; the Shot says which one knob moves and between
  which two values.
* **`Presentation.shot_at(t)`** is the only time lookup: it returns
  `(flat shot index, progress 0..1)` and it **loops** (`t %= total`).
  Every frame is a pure function of `t`.
* `to_json` / `from_json` round-trip losslessly (`asdict` plus
  hand-written re-hydration for the nested tuples). `validate()` asserts
  lens name, perspective number, and `duration > 0.5`.

### 2a. Shot vocabulary

**Lenses** (`LENSES` — fov degrees, framing factor):
`macro` 21/0.52 · `portrait` 34/1.05 · `wide` 58/1.45 · `ultrawide` 92/2.10

**Perspectives** (`PERSPECTIVES`, 1-6):
1 one-point (snaps yaw to nearest 90 degrees, level, gentle push-in) ·
2 two-point (pitch clamped near level) · 3 free ·
4 cylindrical panorama · 5 fisheye 180 · 6 azimuthal 360.
Modes 4-6 render six 90-degree cube faces and resolve them in a shader.

**`actions`** — `(object_name, param_name, from, to)`. Read back per
frame by `Shot.action_value()`, linearly interpolated on shot progress
and clamped to 0..1.

---

## 3. What a frame is made of

`presenter/world.py :: build_frame(env, objects, t, shot, progress)` ->
`(opaque_batch, transparent_batch, targets)`.

* `objects` is the Scene's `world` list of `(key, params)`. Shot actions
  override params for the length of the shot.
* `targets` is `{name: (position_vec3, framing_radius)}` — **this is what
  the camera can look at.** Because it is rebuilt every frame, a moving
  object gives you a follow-cam for free: set `focus="wheelchair"`.
* `all_emitters()` merges three sources: the star objects in `world.py`,
  the `ACCESSORY_EMITTERS` in `accessories.py`, and every Dome Forge
  layer bridged in under a `forge:` prefix.

**Focus target names currently registered:**
`apex battery_rack blower canister ceiling_lift compare_box compare_dome
compare_pair condenser crane_anchor deck dome door fixtures furniture
grab_bar grille hatch hose kitchen loft mini_split plenum rain_catch
ramp rigidity_pair rigidity_square rigidity_triangle shell_layers
skylight solar utility_column water_tank wheelchair wheelchair_wide
windows wood_stove` — plus `forge_<layer>` for each Forge layer, and
`origin` as the fallback.

**Object catalog** — 43 placeable objects in 7 categories, defined in
`presenter/library.py` as `ObjectSpec`s with per-param min/max/default.
Print the live list rather than trusting a copy in a document:

```bash
python -c "import sys;sys.path.insert(0,'.');from presenter.library import OBJECT_SPECS;[print(s.key,[p.key for p in s.params]) for s in OBJECT_SPECS]"
```

`presenter_studio.selftest()` guarantees the catalog and the emitters
stay in sync — every catalogued object must build geometry, register a
focus target, and survive both stops of every slider.

**Environment** — `presenter/prompt.py :: parse_environment(text)` is an
ordered list of 15 regex rules that compose. `"a lake in the desert"`
keeps sand terrain, adds water, and infers a shoreline. Output is an
`EnvironmentSpec` (terrain, water, shoreline, weather, tsunami, tornado,
palms, cacti, pines, rocks, sky, haze).

---

## 4. The export, line by line — `presenter/engine.py :: PresenterApp.export`

Order matters: **all the speech is synthesized before a single frame is
drawn**, because speech length decides the timeline.

### 4a. Setup
```python
ffmpeg_exe = resolve_executable("ffmpeg", ffmpeg)   # two_v_demo.audio
fps = fps or self.pres.fps
```
`resolve_executable` walks *every* PATH match (not just the first, unlike
`shutil.which`) and picks the newest by its `Copyright (c) YYYY-YYYY`
banner. On this machine that matters — see section 8.

### 4b. Narration first — `apply_narration()`
1. Flatten to `[(scene, shot), ...]` via `pres.all_shots()`.
2. One spoken segment per shot: `" ".join(shot.narration)`.
3. `narrate.prepare_narration()`:
   * cache key = `sha1(f"{voice}|{rate}|{text}")[:16]`, file
     `<stem>-voice/seg-NN-<hash>.mp3`
   * on a miss: `edge_tts.Communicate(text, voice, rate=rate,
     pitch="-2Hz").save_sync(path)` — **network call**, Microsoft's
     neural endpoint, no API key
   * measure each clip with `ffprobe` (`media_duration`)
4. `narrate.stretch_durations()`:
   `shot_len = max(scripted, SPEECH_DELAY 0.45 + speech + TAIL_PAD 0.75)`
5. Rebuild the whole immutable document with `dataclasses.replace` and
   recompute `starts` per shot. **`self.pres` is now the retimed copy.**

### 4c. Build the audio track — `narrate.build_track()`
* Decode every mp3 to raw `s16le` mono 44.1 kHz through ffmpeg stdout.
* Sum into one `int32` numpy buffer, each clip placed at
  `(start + 0.45s) * 44100`; clip to `int16`.
* Write a WAV with the stdlib `wave` module, encode to
  `<stem>-narration.m4a` at 160 kb/s via `_aac_encoder()`, delete the WAV.
* **No ffmpeg filters are used anywhere** (no `adelay`, no `amix`) — that
  is deliberate, so pre-2015 ffmpeg builds still work.

### 4d. Subtitles — always
`narrate.write_srt(path.with_suffix(".srt"), ...)` runs regardless of the
overlay level. Each cue starts at `shot_start + 0.45` and lasts
`max(1.2, speech)`. So a `clean` render with nothing burned in still
ships a full subtitle file.

### 4e. Frames to ffmpeg over a pipe
```
ffmpeg -y -v error
  -f rawvideo -pixel_format rgb24 -video_size WxH -framerate FPS -i -
  -vf vflip -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p
  -movflags +faststart  <target>
```
opened with `subprocess.Popen(..., stdin=PIPE)`, then:

```python
for frame in range(ceil(total * fps)):
    self.render(frame / fps, present=False)
    process.stdin.write(self.capture_rgb())
```

`capture_rgb()` is `ctx.finish()` plus `screen_fbo.read(components=3,
alignment=1)`. OpenGL hands back rows bottom-up, hence `-vf vflip` (and
`pygame.transform.flip` in `screenshot()`).

If there is a narration track the target here is a hidden temp,
`.<stem>-silent.mp4`.

### 4f. Mux
```
ffmpeg -y -i silent.mp4 -i narration.m4a
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -shortest
  -movflags +faststart  out.mp4
```
then the temp is unlinked. **Stream copy only** — the picture is never
re-encoded.

### 4g. What `render(t)` does per frame
```
locate(t)                       -> scene, shot, index, progress
parse_environment(scene.env)    -> cached per scene slug
build_frame(env, world, t, shot, progress)   -> geometry + targets
shot_camera(shot, targets, progress, ...)    -> CameraState
    distance = target_radius / tan(fov/2) * lens_framing
               * (1 + dolly*ease(p))
    yaw      = shot.yaw + shot.orbit * ease(p)
draw the 3-D pass (1 pass for modes 1-3, 6 cube faces for 4-6)
draw_overlay(...)  -> a pygame RGBA Surface -> texture -> blitted on top
```

`ease()` is smoothstep (`v*v*(3-2v)`), so every camera move accelerates
and settles rather than starting hard.

### 4h. Overlay levels — `OVERLAY_LEVELS`

| level | title | caption | panel | progress |
|---|---|---|---|---|
| `full` | yes | yes | yes | yes |
| `no_captions` | yes | no | yes | yes |
| `titles_only` | yes | no | no | yes |
| `clean` | no | no | no | no |

The `.srt` and the spoken audio are unaffected by this choice.

---

## 5. Driving it yourself

### 5a. From the GUI
```bash
py -3.12 launcher.py
```
Presenter Studio tab -> Action: `run` / `compose` / `shots` / `export` /
`export_all` / `selftest`.

### 5b. From a text prompt (what `parse_brief` actually understands)

It is a small regex parser, not an LLM. It reads:

* **scene / shot counts** — `"seven scenes each of three shots"`
  (words `one` through `twelve`, or digits; defaults 3 and 3)
* **lens words, in the order spoken** — `close up` -> portrait, `macro`,
  `ultra wide` -> ultrawide, `wide`, `portrait`, `establish` -> ultrawide
* **`"elements 1, 2 and 3"`** — 1-based indices into the `focus` list you
  pass, or literal object names

It emits a *skeleton*: slugs, lenses, focuses, spread yaw/pitch, and
placeholder captions. **No narration, no panels, no stage** (the caller
staples on a default dome world). Treat it as scaffolding you then edit,
not as a text-to-video engine.

The real "text prompting" story is section 5d: an LLM writes the
`build()`.

### 5c. Programmatically — the smallest complete example

```python
from pathlib import Path
from presenter.script import Presentation, Scene, Shot, OverlayPanel
from presenter.engine import PresenterApp

STAGE = (("dome",  {"radius": 4.2, "skin_alpha": 0.16}),
         ("door",  {"radius": 4.2, "az_deg": 0.0, "open": 0.0}),
         ("ramp",  {"radius": 4.2, "az_deg": 0.0, "rise": 0.30}),
         ("wheelchair", {"radius": 4.2, "progress": 0.0}))

def build() -> Presentation:
    return Presentation(
        title="Halfway Home", author="Don", fps=30, size=(1920, 1080),
        voice="en-US-AndrewMultilingualNeural", voice_rate="-3%",
        scenes=(
            Scene(slug="arrival", title="Arrival",
                  environment="on a beach at dusk",
                  world=STAGE,
                  shots=(
                      Shot(slug="roll_in", duration=9.0,
                           lens="wide", perspective=3,
                           focus="wheelchair_wide",
                           yaw=150, pitch=11, orbit=-8, dolly=-0.10,
                           actions=(("wheelchair", "progress", 0.0, 0.30),
                                    ("door", "open", 0.0, 1.0)),
                           caption="No steps to stop at the threshold",
                           narration=("Here is our resident, arriving home.",),
                           panel=OverlayPanel(
                               title="ZERO-THRESHOLD ENTRY",
                               bullets=("One continuous slope",),
                               stats=(("Door clear width", "34 in"),),
                               position="right")),
                  )),
        ))

pres = build()
pres.validate()                        # catches bad lens / perspective / duration

app = PresenterApp(pres, headless=True, size=(1920, 1080))
app.screenshot(Path("check_arrival.png"))          # look before you render
app.export(Path("out/halfway.mp4"), fps=30, narration=True, overlay="full")
app.pygame.quit()
```

Run it with `py -3.12`. `headless=True` uses
`moderngl.create_standalone_context()`, so no window opens.

**Never skip the stills.** `presenter_studio.selftest()` proves every
focus target resolves and every object draws, but it cannot see that a
column is standing in front of your subject.

### 5d. The pattern with the most control: an LLM writes the document

1. Compute every number in a `_numbers.py`-style module from `al_build` /
   `two_v_demo.geometry`. Never type a figure into a caption.
2. Hand the model: the beat structure, the object catalog dump from
   section 3, the focus-target list, and the `Shot` field table.
3. It emits a `build() -> Presentation`.
4. `validate()` -> stills -> export.

The prompt template in `programmatic-video-guide.md` section 4 is written
for exactly this.

### 5e. Editing an existing document

`presenter/edit.py` is a pure-functional API over the immutable document
— `add_scene`, `move_shot`, `set_shot`, `set_narration`, `set_panel`,
`set_action`, `add_object`, `set_object_param`, `copy_stage`, and so on.
Each returns a new `Presentation`; nothing mutates. Values are clamped to
what the object and the engine accept, so a bad number cannot crash a
render. The Scene Composer (`presenter/studio.py`) is a GUI over these.

Round-trip through JSON to hand-edit:
```bash
python -c "import sys;sys.path.insert(0,'.');from presentations.dome_accessibility import build;build().to_json('work.json')"
```

---

## 6. Control levers, ranked by how much they change the picture

| Lever | Where | Note |
|---|---|---|
| `focus` | Shot | The single biggest one. Point at a *moving* name for a follow-cam. |
| `lens` | Shot | Changes fov *and* framing distance together. |
| `perspective` | Shot | 1 and 2 impose discipline; 4-6 cost 6x the draw calls. |
| `yaw` / `pitch` / `orbit` / `dolly` | Shot | `orbit` and `dolly` are *deltas across the shot*, eased. |
| `height_bias` | Shot | Raises the look-at point without moving the subject. |
| `actions` | Shot | The only animation mechanism. One number, from -> to. |
| `environment` | Scene | Free text, section 3. |
| `world` | Scene | The stage. Keep a shared base tuple and override deltas. |
| `xray` | Shot | Translucent shell layers. |
| `overlay` | export arg | How much text burns in. |
| `voice` / `voice_rate` | Presentation | Section 7. |
| `size` / `fps` | Presentation or export arg | Export arg wins for fps. |

**Not currently exposed:** TTS pitch is hardcoded to `-2Hz` in
`narrate.synthesize_segment`'s default; `SPEECH_DELAY` (0.45 s) and
`TAIL_PAD` (0.75 s) are module constants; the CRF and preset are literals
in `export()`. All four are one-line changes if you need them.

---

## 7. Ten languages — what works, what breaks

Everything here was checked against this machine, not assumed.

### 7a. Voices actually available in edge-tts (322 total)

| Language | Locale | Voices |
|---|---|---|
| Japanese | `ja-JP` | `KeitaNeural` (m), `NanamiNeural` (f) |
| Korean | `ko-KR` | **`HyunsuMultilingualNeural`**, `InJoonNeural` (m), `SunHiNeural` (f) |
| Chinese (Simplified) | `zh-CN` | `YunxiNeural`, `YunyangNeural`, `YunjianNeural` (m); `XiaoxiaoNeural`, `XiaoyiNeural`, `XiaoxiaNeural` (f) |
| Vietnamese | `vi-VN` | `NamMinhNeural` (m), `HoaiMyNeural` (f) |
| Tagalog / Filipino | `fil-PH` | `AngeloNeural` (m), `BlessicaNeural` (f) |
| Cebuano | — | **none exist** |
| French | `fr-FR` | **`RemyMultilingualNeural`**, **`VivienneMultilingualNeural`**, `HenriNeural`, `DeniseNeural`, `EloiseNeural` |
| German | `de-DE` | **`FlorianMultilingualNeural`**, **`SeraphinaMultilingualNeural`**, `ConradNeural`, `KatjaNeural`, `AmalaNeural`, `KillianNeural` |
| Russian | `ru-RU` | `DmitryNeural` (m), `SvetlanaNeural` (f) |
| Spanish | `es-MX` / `es-ES` / `es-US` | `JorgeNeural`/`DaliaNeural`, `AlvaroNeural`/`ElviraNeural`/`XimenaNeural`, `AlonsoNeural`/`PalomaNeural` |

> **Cebuano is not available.** **Decided 2026-08-20: ship Tagalog
> (`fil-PH-AngeloNeural`) for the Philippines for now.** Revisit only
> if a Cebuano-capable TTS backend is added.

Regenerate this table any time:
```bash
python -c "import edge_tts,asyncio;[print(v['ShortName']) for v in asyncio.run(edge_tts.list_voices())]"
```

There are 12 `...MultilingualNeural` voices, including the project's own
default `en-US-AndrewMultilingualNeural`.

**Tested, 2026-08-20 — the house voice speaks all ten.** The same sentence
was synthesized in every target language with `en-US-AndrewMultilingualNeural`
(rate `-3%`, pitch `-2Hz`, matching every rendered video in this repo) and
again with each locale's native voice. Every clip came back as real speech
— mean volume -18 to -25 dB, no silences, no errors — at a duration within
0.83x to 1.18x of the native voice:

| | en | ja | ko | zh | vi | fil | fr | de | ru | es |
|---|---|---|---|---|---|---|---|---|---|---|
| house / native duration | 1.00 | 0.92 | 0.88 | 1.17 | 0.92 | 1.18 | 1.03 | 0.99 | 0.92 | 0.83 |

A voice that could not handle a script would show up here as a near-zero
duration or a wild outlier (character-by-character spelling). Nothing
does. **One narrator across all ten languages is viable**, which keeps the
brand voice identical everywhere.

What this does **not** establish is accent quality — whether a native
speaker finds it natural. That needs ears, not ffprobe. The probe writes
paired samples plus a labelled A/B reel (`voice_ab_reel.mp3`) for exactly
that judgement. The edge-tts endpoint is also unofficial, so treat the
result as verified-today, not contractual.

Nothing needs downloading for any of this: edge-tts is a streaming
service, not a local model. `py -3.12` already has edge-tts 7.2.8,
pygame 2.6.1, moderngl 5.12.0 and numpy 2.4.6.

### 7b. The burned-in text will break for CJK — verified

`presenter/engine.py:322` is:
```python
self.fonts[key] = self.pygame.font.SysFont("consolas", size, bold=bold)
```

Consolas has **no CJK glyphs.** Glyph-coverage check of the fonts on this
machine against real sample strings:

| font | JA | KO | ZH | VI | TL | FR | DE | RU | ES |
|---|---|---|---|---|---|---|---|---|---|
| `consola.ttf` | no | no | no | yes | yes | yes | yes | yes | yes |
| `YuGothR.ttc` | yes | no | partial | no | yes | yes | yes | yes | yes |
| `malgun.ttf` | no | yes | no | no | yes | yes | yes | yes | yes |
| `msyh.ttc` | yes | no | yes | no | yes | yes | yes | yes | yes |

So Consolas already covers Vietnamese, Tagalog, French, German,
**Russian** and Spanish. No single installed font covers JA+KO+ZH+VI, so
this needs a **per-language font map**, not one universal font:

```python
FONT_FOR_LANG = {           # used by engine.PresenterApp.font()
    "ja": "Yu Gothic",
    "ko": "Malgun Gothic",
    "zh": "Microsoft YaHei",
}                            # everything else keeps Consolas
```

`SysFont` accepts a comma-separated list but picks a single face — it
does **not** do per-glyph fallback. The map has to be per language.

The `.srt` file needs no change: `write_srt` already writes UTF-8.

**Tested, 2026-08-20 — the map works, verified by eye.** A real caption
frame was rendered through the actual engine in all ten languages (with
`PresenterApp.font` monkeypatched to the map above, no repo source
touched), exercising all four overlay text kinds: title, subtitle,
lower-third caption, and panel title/bullet/stat. All ten render correct
glyphs at correct weight. Vietnamese stacked diacritics
(ộ ề ữ ơ) come through Consolas uncut. Nothing needs installing — Yu
Gothic, Malgun Gothic and Microsoft YaHei are already on this machine.

An earlier worry that pygame resolves Japanese to `YuGothL.ttc` and
Chinese to `msyhl.ttc` (the *Light* weights) turned out not to matter:
`SysFont(name, size, bold=True)` correctly selects `YuGothB.ttc` /
`msyhbd.ttc`, and the rendered titles read as properly bold. Pixel
metrics could not distinguish the weights — only the rendered frames
could. Look at frames, not numbers.

Two things the renders exposed that a font check alone would have missed:

* **`engine.py:454` hardcodes an English word into every frame.** The
  subtitle line is
  `f"{scene.title or scene.slug}  ·  shot {idx + 1}/{len(...)}"`, so
  "shot 1/1" appears in Latin script over the Japanese, Korean, Chinese
  and Russian frames. It needs localizing or removing before any language
  version ships.
* **The look shifts between language versions.** Latin and Cyrillic
  render in monospaced Consolas (technical, on-brand); CJK renders in
  proportional Yu Gothic / Malgun / YaHei (softer, more like ordinary UI
  text). Not a bug, but the CJK cuts will not look like siblings of the
  English one. Choosing a proportional face for *every* language would
  make them consistent at the cost of the current house look — a design
  call, not a technical one.

### 7c. The timeline retimes itself — for free, and that has a cost

`stretch_durations` sets each shot from its *measured* speech length. A
German narration 25% longer than the English simply produces a longer
video, in sync, with no hand-timing. Good.

The cost: **every language has a different timeline, so frames must be
re-rendered per language.** Ten languages equals ten full GL renders.

If that becomes the bottleneck, the fix is small: compute stretched
durations for all ten languages, take the per-shot `max`, and hold that
timeline fixed for every language. Then render frames **once**
(`overlay="clean"`) and mux ten audio tracks against it — ten
stream-copy muxes instead of ten renders. `apply_narration()` would need
to accept externally supplied durations instead of computing its own.

### 7d. Translating the text without breaking the numbers

Panels and captions build their strings with f-strings over
`presentations/_numbers.py`, which computes everything from `al_build` /
`two_v_demo.geometry`. If a translator is handed the finished string,
the numbers get retyped into ten files and the integrity discipline is
gone.

The structure that keeps it: a per-language **string catalog** keyed by
`(scene_slug, shot_slug, field)` holding *only* the words, with the
numbers still injected at build time from `_numbers.py`. The catalog is
what gets translated and reviewed; the values are never in it.

Two more things that are localization, not translation:

* **Units.** The presentations are in feet and square feet. Nine of the
  ten target locales are metric. `al_build.FT_PER_M` already exists, so
  this is a formatting decision, not a computation.
* **The ADA reference.** `presentations/dome_accessibility.py` cites the
  ADA 60-inch turning circle as an external US standard. In a Japanese or
  German video that citation is either wrong or needs its local
  equivalent. Leaving it in translated is the kind of thing the honesty
  rules in `programmatic-video-guide.md` section 8 exist to prevent.

There is **no translation library installed** (`deep_translator`,
`argostranslate`, `googletrans` all absent) and no API key in the
environment. `openai` and `transformers` are installed but unconfigured.

### 7e. What a language run looks like

```python
LANGS = {                       # slug: (voice, font, rate)
  "en": ("en-US-AndrewMultilingualNeural",  "consolas",        "-3%"),
  "ja": ("ja-JP-KeitaNeural",               "Yu Gothic",       "-3%"),
  "ko": ("ko-KR-HyunsuMultilingualNeural",  "Malgun Gothic",   "-3%"),
  "zh": ("zh-CN-YunxiNeural",               "Microsoft YaHei", "-3%"),
  "vi": ("vi-VN-NamMinhNeural",             "consolas",        "-3%"),
  "fil":("fil-PH-AngeloNeural",             "consolas",        "-3%"),
  "fr": ("fr-FR-RemyMultilingualNeural",    "consolas",        "-3%"),
  "de": ("de-DE-FlorianMultilingualNeural", "consolas",        "-3%"),
  "ru": ("ru-RU-DmitryNeural",              "consolas",        "-3%"),
  "es": ("es-MX-JorgeNeural",               "consolas",        "-3%"),
}
```
For each: rebuild the `Presentation` with that language's catalog and
`replace(pres, voice=..., voice_rate=...)`, set the engine font, and
export to `case_energy.<lang>.mp4`. The voice cache key already includes
the voice and the text, so the ten runs never collide; the `.srt` lands
beside each file automatically.

---

## 8. Gotchas found in the tree

* **Three ffmpeg builds are on PATH here**, and the two code paths
  disagree about which one they get:
  * `resolve_executable` (pipelines A and B) -> the modern `N-124716`
    build
  * `shutil.which` (pipeline C — `build_launcher_trailer.py`,
    `add_narration.py`) -> `C:\Users\Don\AppData\Local\Python\bin\ffmpeg.exe`,
    **a build from 2013**.

  It works today only because those scripts avoid modern filters and pass
  `-c:a aac -strict -2`. Anything added to them that needs a current
  ffmpeg will fail confusingly. Switching them to `resolve_executable`
  would remove the trap.
* **edge-tts needs the network.** Every voiced export contacts
  Microsoft's endpoint on a cache miss. A populated `<stem>-voice/` folder
  makes re-exports offline; deleting it makes them not.
  **Observed 2026-08-23:** `speech.platform.bing.com` intermittently
  failed to resolve on this machine while general DNS was fine, which
  abandoned a whole export mid-run. `audio._synthesize_one` now retries
  each clip `SYNTHESIS_ATTEMPTS` times with an exponential backoff and
  deletes any partial file first, so a transient failure costs seconds
  rather than the render. A thirty-two chapter lesson is thirty-two
  separate calls, so this matters more the longer the lesson.
  **Export lessons one at a time.** Three exports were started in parallel
  the same day; within seconds the endpoint began refusing connections and
  its name stopped resolving for all three, and the two still in their
  speech stage died while the one already past it rendered fine. The
  per-chapter cache means a re-run resumes rather than restarts, but the
  parallelism buys nothing anyway: the speech stage is endpoint-bound and
  the render stage is GPU-bound, so serialising costs almost no wall
  clock.
* **GL frames arrive upside down.** `-vf vflip` on export,
  `transform.flip` in `screenshot()`. Any new capture path needs one of
  the two.
* **`export()` mutates `self.pres`** — it replaces the document with the
  retimed copy. The Scene Composer works around this in
  `_with_full_frame()`, and `selftest()` asserts the document comes back
  unchanged.
* **`shot_at()` loops.** Asking for `t` past the end wraps to the start
  rather than clamping.
