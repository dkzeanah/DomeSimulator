# Manual video authoring with a local LLM

This is a hands-on route from an idea to Python to a rendered DomeSim clip.
Open **Launcher → Project Agent → Manual video authoring**. Choose a short
file key, describe the element, select Compact or Full, then **Copy LLM prompt**.
Paste it into your Ollama chat. You save its Python response yourself and run
the commands shown under **Commands**. Copying a prompt does not contact Ollama,
write lesson code, register a film, or start a render.

## What is actually producing the video

The model writes a content module. It does not directly produce the frames.

    your brief → Python Lesson → chapters → painter(progress) → geometry
               → ModernGL frames → FFmpeg MP4
               → optional neural narration + subtitles

The practical authoring loop used in this project is: inspect the existing
functions; choose the facts and reusable objects; write a small scene; validate
the numbers and code; render and inspect stills; correct framing; test motion;
then export the narrated film. You can perform each of those steps yourself.
Selftests check only what their assertions cover; they do not establish that
the picture, explanation, or physical assumptions are correct.

There are two video systems. This guide uses **Masterclass lessons**, where
you write a `Lesson`, `Chapter` records, and Python painters. **Presenter Studio**
instead consumes a `Presentation` containing `Scene` and `Shot` objects from
`presenter/document.py`. Do not mix those APIs in one generated lesson. See
`docs/programmatic-video-guide.md` for the Presenter route.

## Start with your models

Try `qwen2.5-coder:7b` first for the Python file: its published purpose includes
code generation and repair. This is a practical starting choice, not a measured
ranking on this project. [Ollama model card](https://ollama.com/library/qwen2.5-coder)

Your other text-generation models can use the same prompt. The selector keeps
the names you supplied: `deepseek-rl:7b`, `qwen3-vl:4b`, `granite3.2-vision:2b`,
`qwen3.5:4b`, and `llama3.1`. Confirm exact installed names with `ollama list`;
in particular, `deepseek-rl:7b` is retained as entered, not silently renamed
to `deepseek-r1:7b`. No assumptions about their local settings or performance
are built into this workbench. Models with image input can also review rendered
PNGs for cropping and overlapping text, if your chat tool supports attachments.

`embeddinggemma` produces text embeddings for retrieval/search. It does not
generate the Python response in this workflow. It could help a future search
system find relevant code, but choose a generation model for this task.
[Ollama model card](https://ollama.com/library/embeddinggemma)

Use **Compact** for the first one-scene experiment. It includes the essential
contract and a small runnable example. **Full** adds the existing live catalogues,
the longer dome example, the Creator bridge recipe, and this manual. The GUI
shows character and word counts; its token count is only a rough estimate.
The model's configured context must fit the prompt, chat history, and answer.
Parameter count (4B/7B) does not tell you how much context your current runtime
has allocated. Start a fresh chat; use Compact or a larger configured context
if Full is cut off. [Ollama context documentation](https://docs.ollama.com/context-length)

## First experiment: a single new element

Use key `my_element`. A suitable brief is:

> Create one eight-second clip of three members assembling into a triangular
> frame. Keep the camera steady enough to see the assembly. Use the supplied
> renderer, compute the member count and perimeter from the endpoints, and
> explain where to change the appearance and timing in code comments.

The **Starter example** tab contains working Python for that experiment.
You can copy it before involving a model, proving the local renderer works.
The **Full** packet also contains an existing multi-chapter dome lesson to
show how a larger film is organized.

1. Choose a unique lowercase key such as `my_element` or `roof_reveal`.
   Keys start with a letter and contain only letters, digits, and underscores.
2. Copy the prompt to your local model. The final task states the exact key,
   destination, and requested subject. Ask for one complete file.
3. Create `two_v_demo/lesson_my_element.py` in your editor, under the DomeSim
   project. Save as UTF-8, with a real `.py` extension, not `.py.txt`.
4. Paste only the Python. Remove markdown fences, chat introductions, and any
   separate reasoning text. Keep the opening docstring and code comments.
5. Read the `SAVE THIS AS`, `HOW TO USE`, and `WHAT TO CHANGE` comments.
   The model is required to repeat the commands there using your actual key.
6. Run the validation command, inspect stills, and export a silent clip first.
   Use a new key for a different experiment; do not overwrite existing lessons.

The file is a module imported by the renderer. Double-clicking it or running
`py lesson_my_element.py` is not the rendering step.

## Manual commands: render only the new file

Open PowerShell in `C:\Users\Don\Desktop\DomeSim`. The GUI's Commands tab
substitutes your selected key and the actual project location. For `my_element`:

```powershell
Set-Location -LiteralPath 'C:\Users\Don\Desktop\DomeSim'

# A. Syntax only. This does not draw or prove the lesson's claims.
py -3.12 -m py_compile two_v_demo/lesson_my_element.py

# B. Lesson structure plus its own mathematical/geometry checks; no GL window.
py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --selftest

# C. PNGs at each chapter midpoint on the silent timeline.
py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --chapter-stills --size 960x540

# D. For the eight-second starter: inspect early, middle, and final frames.
py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --stills 0.5,4,7.9 --size 960x540

# E. Low-cost motion check: just this lesson, with no generated speech.
py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --export exports/manual/my_element-silent.mp4 --silent --size 960x540 --fps 24

# F. Narrated 1080p film: the same standalone lesson, at 30 fps.
py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --export exports/manual/my_element.mp4 --size 1920x1080 --fps 30
```

The standalone `render_lesson.py` really supports these command-line flags.
Most other project tools, including the root Masterclass entry point, use
launcher tickets instead; do not transfer these flags to a different script.
If `py` is unavailable, replace `py -3.12` with `& 'FULL_PATH_TO_python.exe'`
for the Python 3.12 environment used by the launcher.

This imports the one module and passes its `Lesson` directly to `MasterclassApp`.
It does not look up your film in the registry or compose standard segments.
Only the chapters you included render. If you explicitly import and compose
other chapters in your module, those become part of your film.

The runner writes each still run into a fresh folder under
`two_v_demo_output/<lesson-key>/`. The console prints every path. MP4 exports
use `-v2`, `-v3`, etc. if the requested output exists. Keep the terminal open
until it reports `saved ...`; import can take time because the engine loads
shared modules. A short simple clip need not take hours, but complex geometry,
resolution, frame rate, and speech synthesis all affect render time.

You can also load a loose file with `--file exports/drafts/lesson_draft.py`.
Use absolute `two_v_demo...` imports in generated files. The primary documented
route is the module name above, with your code inside `two_v_demo/`.

## What the generated Python contains

| Piece | Responsibility | What you normally edit |
|---|---|---|
| Inputs and derived facts | Dimensions, counts, areas, cost assumptions | Named inputs, functions and units |
| `scene_<key>(app, opaque, transparent, p)` | Geometry for one frame | Shapes, positions, reveals, labels |
| `SCENES` | Stage name → painter function | Add a name when adding a painter |
| `CHAPTERS` | Shot sequence, narration, duration, camera, stage | Order, copy, timing and framing |
| `validate_<key>()` | Meaningful checks before spending render time | Invariants, stages, finite geometry |
| `LESSON = Lesson(...)` | The renderer's entry point for your film | Key, title, scenes, style, selftest |

Every painter receives `p` between 0 and 1 for its chapter. The engine creates
new geometry batches on every frame. Use interpolation such as
`start + (end - start) * smoothstep(p)`, or stagger parts with
`clamp(p * count - index)`. Do not update a global position incrementally or
use the clock: the renderer seeks, rewinds, and exports frames independently.
Cache static computed geometry; seed any randomness.

`duration` is a minimum chapter length. Narrated export synthesizes speech,
measures it, and stretches the chapter when needed. `p=0.5` is halfway through
the resulting chapter, not necessarily a particular spoken word. Word/sentence
timed callouts use the project's separate callout/timing helpers.

## Drawing vocabulary and camera rules

The prompt lists the actual primitive signatures. Use `opaque` for solids and
`transparent` for alpha below one. Positions are three-component NumPy arrays;
primitive colours are RGBA floats from zero to one. `WorldLabel` instead takes
RGB integers from zero to 255. `cylinder` calls its resolution argument `sides`;
`sphere` uses `rings` and `segments`. These are not interchangeable keywords.

The orbit camera targets `(0, 0, 2.25)`. The chapter camera tuple is
`(yaw_degrees, pitch_degrees, distance)`. At yaw 90 the camera sits on +Y, so
arrange comparisons along X or stack them in Z. A row along Y recedes into
the screen and its nearer objects can hide the others. For one subject, a
three-quarter view around yaw 45 is useful. Increase distance if edges crop;
change the target with `Lesson.camera_fn` only after the simple orbit works.
The default export camera can add a small yaw drift; a strict locked camera
needs a `camera_fn`. Keep geometry above the z=0 ground and labels away from
the headline/worksheet areas. Check actual stills, not just coordinate values.

Styles: `teaching` draws explanatory cards; `hype` draws a headline over a
large scene; chapter `overlay="math"` creates a worksheet. `plate` removes
headlines/cards but retains world labels/icons/callouts. To produce clean
footage for an editor, choose `plate` and omit those overlay additions too.
`ground="off"` removes the engine's ground, not the background colour. MP4
exports are ordinary opaque video; this workflow does not create an alpha video.

## Reuse existing objects and finished domes

For a diagram, primitives are enough. For a familiar project object, use
`two_v_demo.visual_objects` so the film draws the existing asset:

```python
from two_v_demo import visual_objects
stage = visual_objects.stage_for(app, opaque, transparent, origin=(4.0, 0.0, 0.0))
visual_objects.draw(stage, "person", height=1.8)
```

The Full prompt reads the current object keys/knobs, colours, icon keys, and
facts map from this checkout. A catalogue entry is a locator, not permission
to invent a function's return attributes. When needed, paste that function's
source into the model chat and request an implementation using its real fields.

For a finished Dome Creator building with its actual materials, use the bridge:

```python
from two_v_demo import creator_bridge as creator
BUILD = creator.preset("Glass Studio Loft")

def scene_build(app, opaque, transparent, p):
    phase = BUILD.phase(p)
    creator.draw(app, BUILD, limits=phase["limits"])
```

Set the Lesson's `ground="off"` because the building has a foundation.
`creator.draw(app, BUILD, cut_z=2.1)` shows a cutaway; `offset`, `scale`, and
`yaw` place the model. Use `BUILD.apex` for labels, especially on raised
foundations. `BUILD.hours` is the source tool's labor estimate, not measured
construction performance. Do not reconstruct a finished product with generic
rods when the requested image is the Creator's actual building. The raw-wedge
tool has its own `raw_wedge_bridge`; see `docs/dome-creator-in-films.md` and
`project_agent/authoring/visual-language.md` for deeper references.

For a wholly new object, first define a local `draw_<object>` function in your
one lesson file and call it from the painter. No global registration is needed.
Once it works, that helper can be extracted into a reusable module. Adding a
shared `visual_objects` registry entry is a separate, optional integration.

## Numbers and physical claims

Use the live geometry/facts functions already in the repository. A new diagram
can compute its own lengths and areas directly from its endpoints. A chosen
dimension, colour, duration, or animation speed is an illustration input; label
its units and purpose. A claimed material price, labor rate, or performance
number needs a named input with an actual source or an explicit estimate label.
Do not invent citations. Do not weaken a failed assertion merely to make a
render run. A diagram or renderer selftest does not certify a structure.

## Narration and adding clips over existing footage

Silent export is fully local and skips voice generation. Narrated export uses
the film engine's default Andrew neural voice (`en-US-AndrewMultilingualNeural`,
rate `-3%`, pitch `-2Hz`, voice volume `+0%`) through the online Edge TTS service.
It needs connectivity for uncached speech, plus FFmpeg/FFprobe for the export.
For this runner these defaults come from `MasterclassApp.export_video`; a
`Lesson.voice_rate` alone does not override the runner's export arguments.
Narration text and an SRT are written beside the video; silent SRT timings use
the silent chapter schedule.

For independent custom statements, use **Local Voice Studio → Presentation
Voice** to generate a WAV/MP3. Import that audio and the silent MP4 into your
video editor and align them by ear. The manual renderer does not automatically
attach an arbitrary WAV to your new file. Rendering `plate` removes visual
cards; it does not itself turn speech off—use `--silent` for that.

## Troubleshooting and asking the model to repair its file

| Symptom | Check |
|---|---|
| `ModuleNotFoundError: two_v_demo.lesson_...` | Correct root folder, matching key, actual `.py` extension |
| Syntax error at a backtick or chat sentence | Save Python only; remove fences and reasoning text |
| `unexpected keyword argument` | Compare against the live signature in the packet |
| No Lesson or several Lessons found | Define exactly one public `LESSON`; avoid importing unrelated Lesson instances |
| Missing painter / wrong scene | Every Chapter.stage must be in SCENES with exactly the same spelling |
| Failed selftest | Inspect the claim and inputs; do not delete the test to hide it |
| Correct code but bad picture | Check camera distance, X/Y placement, z=0, overlays and label crowding |
| Stills look fine but motion jumps | Remove accumulated state; derive every frame from p |
| Still time rejected as outside duration | Use a time below the silent duration; this runner rejects times the underlying renderer would wrap |
| Online voice fails | Use `--silent` to inspect motion, then retry narrated export when service access works |
| OpenGL / pygame / moderngl failure | Use the launcher Python and working desktop graphics driver |
| FFmpeg not found | Use the environment/PATH that exports the existing presentation videos |

Repair prompt to paste after the original context:

> Keep the same SAVE THIS AS path and public LESSON. Below is the complete
> current file and the exact error output. Explain the cause briefly, then give
> one complete replacement Python file with its usage comments. Preserve valid
> computed facts and checks. Do not invent APIs or claim you ran my renderer.

For visual problems, add a rendered PNG, the timestamp, and the requested
change, such as: "At four seconds the title covers the top joint; move that
label and preserve the rest of the composition."

## Later: putting the finished lesson into the main menus

Standalone experiments do not appear in Masterclass presets or batch exports.
Permanent integration requires the coordinated registry, deliverables, and
render preset entries (`two_v_demo/lesson_registry.py`,
`two_v_demo/deliverables.py`, `render_presets.py`). The existing Project Agent
film recipe can manage those edits, but it also runs additional production
steps; it is not the step for a quick isolated clip. First finish the one-file
experiment. Keep the source file, output MP4, transcript, and voice cache if
you need to reproduce its timing later.
