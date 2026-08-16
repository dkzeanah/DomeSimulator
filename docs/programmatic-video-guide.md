# Making explanatory & persuasive video, programmatically

A reproducible, LLM-agnostic recipe for generating narrated 3-D explainer
videos — the method used to build **"A Home That Meets You Halfway"**
(`presentations/dome_accessibility.py`) — plus a map of the wider
landscape of tools so you can pick a mechanism that fits your project.

The worked example here is the dome-accessibility video: a wheelchair
rolls up a ramp, enters, turns in place, and tours an open floor while a
narrator makes the case, bullet by bullet, for why a dome suits people
with limited mobility. Everything below is how that was produced and how
to reproduce the method with any capable LLM.

---

## 1. The one idea that makes it work

**Separate the *what* from the *how*.** The video is described by a plain
**data document** — scenes, shots, camera moves, narration, captions,
bullet panels. A fixed **renderer** turns that document into pixels the
same way every time. The LLM never renders anything; its whole job is to
**emit the document**.

That split is what makes LLM-generated video *controllable*:

- the output is deterministic — the same document always yields the same
  frames, so a preview and the final export are identical;
- it is editable — change one line (a number, a camera angle, a
  narration sentence) and only that changes;
- it is inspectable — you can read the document and know exactly what the
  video will say and show, before rendering a single frame.

This is the opposite of prompting a generative video model ("a wheelchair
enters a dome home"), which gives you a plausible but uncontrollable clip
with no guarantee the numbers, geometry, or claims are correct. For
explanatory and persuasive content, where being *right* matters, the
data-document approach wins. (Section 7 compares the two directly.)

---

## 2. The five mechanisms

The engine in this repo (`presenter/`) is one concrete implementation of
five mechanisms. Any programmatic-video stack needs the same five, under
different names.

| # | Mechanism | Here | What it buys you |
|---|-----------|------|------------------|
| 1 | **A scene/shot data model** | `presenter/script.py` — immutable `Presentation → Scene → Shot` | The thing the LLM writes. Pure data, serializes to JSON. |
| 2 | **Parametric objects, animated by interpolating a parameter** | `presenter/world.py`, `presenter/accessories.py` | Motion without keyframes: a shot says "move this object's `progress` 0→1" and the object is a pure function of that number. |
| 3 | **Camera as constraints, not hand-flown** | `presenter/camera.py` | Pick a lens + a *named focus target*; the target can move, so the camera *follows* automatically. |
| 4 | **Text-to-speech, measured and auto-timed** | `presenter/narrate.py` (edge-TTS) | Write the words; the shot auto-stretches to fit the spoken length, and an `.srt` is emitted. |
| 5 | **Deterministic frame render → encoder** | `presenter/engine.py` (moderngl → ffmpeg) | Every frame is a pure function of time *t*; pipe raw frames to `libx264`, then mux the audio. |

### 2a. The data model (what the LLM writes)

```python
Shot(
    slug="roll_in", duration=9.0, lens="wide",
    focus="wheelchair_wide",              # a named target the camera frames
    yaw=150, pitch=11, orbit=-8,          # camera move across the shot
    actions=(("wheelchair", "progress", 0.0, 0.30),),   # the animation
    caption="No steps to stop at the threshold",         # burned-in text
    narration=("Here is our resident, arriving home. ...",),  # spoken
)
```

A `Scene` groups shots and declares the **stage** — a list of
`(object_name, params)` — plus a plain-English **environment** string
(`"on a beach at dusk"`) parsed into terrain/weather/sky.

### 2b. Animation = interpolate one number

An object is a function `emit(params, t) → geometry`. To move it, a shot
supplies `actions = ((object, param, from, to), …)`; the engine feeds the
object `param = from + (to−from)·progress` each frame. The wheelchair
reads a single `progress` (0 = out on the approach, 1 = settled inside)
and computes its own position, heading and wheel-spin from it
(`wheelchair_route()` in `presenter/accessories.py`). So "roll the chair
in up the ramp" is literally `("wheelchair", "progress", 0.0, 0.30)`.

### 2c. The camera follows a moving target

Each object registers focus targets — `targets["wheelchair"] = (position,
framing_radius)`. Because the target's position is recomputed every frame
and the object is moving, a shot with `focus="wheelchair"` **tracks** it
with no explicit camera animation. This is the cheapest way to get a
follow-cam: move the subject, point the camera at its name.

---

## 3. The authoring loop (do this, in order)

This is the loop to hand another LLM. It is the same loop used for the
accessibility video.

### Step 0 — Pin the numbers from a source of truth

Before writing a word, compute every figure the video will claim, from
real code, and never hardcode a marketing number. In the accessibility
file:

```python
R = 4.2                                    # a real "home" dome radius
FLOOR_DIAM_FT = 2*R*_FLOOR_FACTOR*ab.FT_PER_M      # from the geometry
FLOOR_AREA_FT2 = math.pi*(R*_FLOOR_FACTOR)**2 * ab.FT_PER_M**2
DOOR_CLEAR_IN  = (DOOR_W_M-0.05)*_IN_PER_M
```

Keep *external* standards visibly separate from *your* measurements. The
video compares the dome's computed floor to the **ADA** 60-inch turning
circle — an external, cited standard, labelled as such, not a measurement
of the model. Mixing the two is how persuasive video starts lying.

### Step 1 — Write the argument as beats, not scenes

A persuasive piece has a shape. Draft it as a list of beats first:

1. **Hook / the problem** — name the pain (a conventional house *is* the
   barrier: steps, narrow doors, halls too tight to turn).
2. **Evidence beats**, one idea each — zero-threshold entry; one open
   room / turning space; everything on one path; independent transfers.
3. **The honest hedge** — a whole beat admitting the real trade-offs
   (curved walls, acoustics, retrofit difficulty). This *increases*
   persuasiveness; audiences trust arguments that concede.
4. **The comparison** — the pros, side by side with the alternative.
5. **The close** — restate the through-line in one line.

### Step 2 — Map each beat to a scene

For every beat decide six things. This table *is* the scene:

| Field | Question | Example (beat 3, "one open room") |
|-------|----------|-----------------------------------|
| Stage | Which objects are present? | dome (see-through), door, ramp, kitchen, furniture, wheelchair |
| Camera | Lens + perspective + what it looks at | `wide`, 3-point, `focus="wheelchair_wide"` |
| Animation | What moves across the shot? | `("wheelchair","progress",0.40,0.55)` — the pivot in place |
| Caption | One line burned on screen | "A full turn in place — the whole floor is a turning space" |
| Panel | The bullet points / stats | ONE OPEN ROOM: 28 ft across, 597 sq ft, 0 interior walls |
| Narration | What is said aloud | "The shell carries its own load, so there are no interior bearing walls…" |

Two rules that keep it honest and legible:

- **Numbers only from Step 0.** The panel's "597 sq ft" is
  `FLOOR_AREA_FT2`, not a typed figure.
- **Caption carries the point without sound.** Assume the viewer is
  muted; the on-screen text must make the argument on its own. Narration
  is a *second* channel, not the only one.

### Step 3 — Emit the document

Write the `build() → Presentation`. Keep a shared base stage and override
per scene (see `_world(**overrides)` in the file) so props stay
consistent and only the deltas are visible.

### Step 4 — Validate, then self-check with stills

Never trust the code you just wrote — render and look.

```bash
# validate structure + that every focus target actually resolves
python -c "from presentations.dome_accessibility import build; build().validate()"
```

Then render one still per scene offscreen and *actually look at each one*
(this is how the central column was caught blocking the turn shot, and
the hoist was caught getting lost in clutter). In this repo:
`PresenterApp(pres, headless=True).screenshot(path)`.

### Step 5 — Export

```bash
py -3.12 launcher.py     # Presenter Studio tab → Action: export (or export_all)
```

Pick how much text burns into the picture (`full` … `clean`); the
voiceover is spoken and an `.srt` is written regardless, so a caption-free
render can still be subtitled.

---

## 4. A prompt template for another LLM

Paste this, filled in, into any capable model that can write code against
your renderer:

> You are composing a narrated explainer video as a **data document** for
> a deterministic renderer (do not try to generate video directly).
> **Topic:** _____. **Audience:** _____. **One-sentence thesis:** _____.
>
> 1. First list every number the video will claim and where each comes
>    from. Compute dome/product numbers from `<source module>`; cite
>    external standards separately as references, never as measurements.
> 2. Draft the argument as 6–9 **beats**: hook → evidence (one idea per
>    beat) → an honest-trade-offs beat → comparison → close.
> 3. Turn each beat into a scene by choosing: stage objects, camera
>    (lens + focus target), one animated parameter, a burned-in caption
>    that works muted, a bullet/stat panel, and the spoken narration.
> 4. Output the `build() -> Presentation` using only objects that exist in
>    `<object library>` and only numbers from step 1.
> 5. List the stills you would render to check it, and what each must
>    show.
>
> Constraints: every on-screen number traceable to step 1; include a
> scene that concedes real limitations; captions must stand alone without
> audio; keep narration plain-spoken (no symbols — write "one in twelve",
> not "1:12").

---

## 5. The wider landscape of mechanisms

You said you weren't aware of all the usable mechanisms. Here is the map.
They fall into four layers; a finished video usually combines one from
each.

### Layer A — Scene description & rendering (the "what → pixels")

**Code / scene-graph frameworks** (deterministic, controllable — best for
explainers):

- **This repo** — Python + pygame + moderngl. Custom parametric 3-D
  objects, a JSON-serializable document, offscreen render to ffmpeg.
- **Remotion** — write video as **React** components; state and props
  drive frames; renders via headless Chromium. Excellent for
  data-driven 2-D/motion-graphics and anything web-styled.
- **Motion Canvas** — TypeScript, purpose-built for narrated code/diagram
  explainers with a timeline API.
- **Manim** — Python; the "3Blue1Brown" library for mathematical
  animation; superb for equations, graphs, step-by-step reveals.
- **Blender + `bpy`** — full 3-D DCC scriptable in Python; photoreal or
  stylized; heavy but unlimited. Good when you need real materials,
  lighting, physics.
- **Three.js / Babylon.js + headless capture** — browser 3-D rendered
  frame-by-frame (e.g. via Puppeteer/Playwright) and piped to ffmpeg.
- **p5.js / Processing / OpenFrameworks** — creative-coding canvases,
  captured to frames.

**2-D / compositing / templating:**

- **SVG → frames** — generate an SVG per frame (D3, or hand-built), rasterize
  (resvg, sharp, cairosvg), encode. Great for charts and diagrams.
- **HTML/CSS + Puppeteer/Playwright** — animate a web page and
  screenshot each frame; reuse your web design system.
- **FFmpeg filtergraph alone** — `drawtext`, `zoompan`, `xfade`,
  `overlay` can build slideshow-style videos with Ken Burns moves and
  titles from images + a script, no renderer at all.
- **After Effects (ExtendScript/JS) or Nuke (Python)** — studio
  compositors, fully scriptable if you have them.

### Layer B — Voice / audio

- **Local, free:** edge-TTS (used here), Piper, Coqui-TTS, Kokoro. No
  account, deterministic enough, good quality.
- **Cloud, higher quality:** ElevenLabs, Azure Speech, Google Cloud TTS,
  Amazon Polly. Better prosody; per-character cost; network dependency.
- **Timing trick (important):** synthesize each narration segment first,
  **measure its duration**, then set each shot's length to fit the speech
  (see `narrate.stretch_durations`). This is what keeps voice and picture
  in sync without hand-timing.
- **Music/SFX:** mix a bed track at low gain under the voice; keep it a
  separate ffmpeg input so levels stay adjustable.

### Layer C — Assembly

- **FFmpeg** does essentially all of it: encode raw frames
  (`-f rawvideo … libx264`), concatenate segments, mux audio, burn or
  attach subtitles, add fades. One dependency, scriptable, deterministic.
- **MLT / Shotcut headless, or moviepy (Python)** — higher-level timeline
  assembly if you prefer objects over ffmpeg flags.

### Layer D — Generative AI video (a different tool for a different job)

- **Runway Gen-3, Pika, Luma, Kling, Google Veo, OpenAI Sora** — text/
  image → short photoreal clips.
- **Strengths:** striking, organic footage; b-roll; mood; things too
  costly to model.
- **Weaknesses for explainers:** non-deterministic (re-rolls differ),
  can't guarantee correct text/numbers/geometry, hard to make precise
  edits, temporal drift, length limits. Use them for *flavor cutaways*,
  not for the frame that shows a measurement.

A common professional hybrid: scene-graph framework for the substance
(diagrams, data, the thing being explained) + a generative clip or two
for atmosphere + TTS + ffmpeg to assemble.

---

## 6. How the layers combine (three example stacks)

| Goal | A: render | B: voice | C: assemble | D: gen-AI |
|------|-----------|----------|-------------|-----------|
| This dome video | pygame+moderngl (repo) | edge-TTS | ffmpeg | — |
| Data-driven web explainer | Remotion (React) | ElevenLabs | Remotion's own encoder | optional b-roll |
| Math lecture | Manim | Piper | ffmpeg concat | — |

---

## 7. Why deterministic beats generative for *this* kind of video

| | Scene-graph document | Prompt a video model |
|---|---|---|
| Same input → same output | Yes | No (re-rolls differ) |
| Correct numbers / labels on screen | Guaranteed (you place them) | Not guaranteed |
| Surgical edits ("shorten shot 3, fix a figure") | Trivial | Re-generate, hope |
| Preview == final | Yes | N/A |
| Cost to iterate | ~free, local | per-generation |
| Photoreal organic motion | Limited by your models | Its strength |

For persuasive and explanatory work — where a wrong number or an
un-editable claim is a real failure — describe the video as data and
render it deterministically. Reach for generative video only for the
moments where being *exactly right* doesn't matter and being *beautiful*
does.

---

## 8. Rules that keep programmatic persuasion honest

1. **Every on-screen number traces to code**, computed once, never typed.
   Cite external standards as external; never dress them up as your own
   measurements.
2. **Include a real trade-offs beat.** Conceding limitations makes the
   rest more believable, and is the honest thing to do.
3. **Captions must stand alone without audio.** Narration is a second
   channel.
4. **Follow motion with a moving focus target**, not hand-flown cameras.
5. **Verify by rendering stills and looking** — at every scene — before
   you export minutes of video. Most staging bugs (an object blocking the
   subject, a prop lost in clutter) are invisible in code and obvious in a
   still.
6. **Generate to a fresh, uniquely-named file every time.** Never
   overwrite a previous presentation or export; a new run is a new
   artifact.
