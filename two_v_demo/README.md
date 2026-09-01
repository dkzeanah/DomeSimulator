# Masterclass lessons

One standalone ModernGL teaching world: eight lessons and one montage. It does not import
or launch the assembly-line simulation or the main Dome Creator world;
the `line` lesson reads `al_build`'s element catalogue as data, but
starts nothing.

| Lesson key | Title | Chapters | What it teaches |
| --- | --- | --- | --- |
| `2v` | 2V Geodesic Masterclass | 14 | Why a 2V dome has exactly two strut lengths, and why their ratio is not the golden ratio. |
| `build` | 2V Dome Construction Masterclass | 46 | The same geometry, then everything after it: sizing, hub systems, end cuts, bevels, stock and offcut, jigs, setting out, foundations, riser walls, raising, checking, skinning, openings, and the four mistakes that actually stop domes going up. |
| `hex` | Hexagonal Dome Masterclass | 20 | The single-hexagon frame dome you can cut from one strut length, why every hexagon cage needs exactly twelve pentagons, and what raising the frequency costs in extra sizes and warped panels. |
| `zome` | Zome Construction Masterclass | 19 | Rooms swept from a star of directions: parallelogram panels that are flat by construction, one strut length, level hub rings, and a point at the top. |
| `line` | Assembly Line Energy Masterclass | 24 | What building one dome costs the two people who build it: an articulated crew animated through all six motions of every placement, with the mechanical work computed limb by limb and the food energy totalled per motion, per station and per shift. |
| `cuts` | The Compound Cut, Both Machines | 18 | The hardest operation in a hubless dome, in full: the rip bevel on the table saw, the end mitre on a sled because no mitre saw reaches the angle, the relief lap, the stop block, and turning rather than flipping between ends. |
| `franken` | The Franken-Dome | 13 | Struts of any section held by V brackets folded from scrap sheet: four screws into each strut, the slack that leaves no joint on the sphere, the settling, and the sheathing that spans the rest. |
| `scratch` | From Scratch: Every Calculation Behind a Dome on Screen | 46 | For someone who has never written code: every calculation between one irrational number and a lit pixel. Half one derives the shape (phi, normalizing, Euler's check, midpoints, projection, two chord factors, a cut list); half two derives the picture (tubes from cross products, normals, the vertex buffer, the orbit camera, the view and projection matrices, the divide by w, the viewport, the depth buffer, backface culling and the lighting sum). 18 math screens, with the render-side figures computed by calling `render_kit`'s own functions and the renderer's settings parsed back out of `app.py` and the shader rather than retyped. |
| `hype` | Frankendome | 36 | Not a lesson. The montage: full-frame pictures, one line of type, a quicker voice, and the argument for treating a dome as a platform you keep upgrading rather than a house you finish once. |

## Run

```powershell
py -3.12 -m pip install -r two_v_demo/requirements.txt
py -3.12 launcher.py               # Masterclass tab — see below
py -3.12 two_v_masterclass.py      # direct run: 2V geometry lesson
py -3.12 dome_build_masterclass.py # direct run: construction lesson
py -3.12 hex_masterclass.py        # direct run: hexagonal dome lesson
py -3.12 zome_masterclass.py       # direct run: zome lesson
py -3.12 line_masterclass.py       # direct run: assembly-line energy lesson
py -3.12 hubless_cut_masterclass.py # direct run: the compound cut
py -3.12 frankendome_masterclass.py # direct run: the franken-dome
py -3.12 frankendome_hype.py       # direct run: the Frankendome montage
```

This tool no longer takes command-line flags. Every mode that used to be
a `--flag` is a field on the launcher's **Masterclass** tab: pick a
**Lesson**, pick an **Action** (run / selftest / report / shots /
export_video / voice_preview / list_voices / narration_only / script /
build_packet / list_lessons), fill in the fields relevant to it, and
click **Launch**. Former flags map onto that tab like this:

| Former flag | Launcher field |
| --- | --- |
| `--fullscreen` | Fullscreen checkbox |
| `--selftest` / `--report` | Action = selftest / report |
| `--shots 0,45,95` | Action = shots + Still times |
| `--export-video FILE` | Action = export_video + Export MP4 |
| `--no-narration` | No narration checkbox |
| `--local-narration-plan JSON` | Local Voice Studio narration plan |
| `--voice` / `--voice-rate` / `--voice-pitch` / `--voice-volume` | Voice / Rate / Pitch / Volume |
| `--voice-preview MP3` | Action = voice_preview + its path |
| `--list-voices` / `--voice-locale` | Action = list_voices + Voice locale |
| `--narration-only M4A` | Action = narration_only + its path |
| `--ffmpeg` / `--ffprobe` | their path fields |
| `--script PATH` | Action = script + its path |
| `--build-packet DIR` (+ `--radius-in`, `--connector-deduction-in`) | Action = build_packet + Output directory / Radius / Connector deduction |
| *(new)* | Lesson dropdown — which of the four lessons to play or export |
| `--fps` / `--size` | FPS / Size WxH |

The video exporter requires `ffmpeg` on `PATH` (or the ffmpeg path field
filled in). It renders the complete, deterministic lesson timeline at
1920x1080 and includes the same equations, captions, camera moves, and
geometry shown in the live app. By default it generates a natural neural
teacher voice, extends each chapter to fit the measured speech duration,
loudness-normalizes the result, and muxes it into the MP4. It also
writes the separate AAC narration track, timed voiceover script, chapter
MP3 stems, and a YouTube-ready `.srt` subtitle file.

The default is Microsoft Edge's warm, confident
`en-US-AndrewMultilingualNeural` voice at a relaxed `-3%` rate. No API key is
needed, but the narration text is sent to Microsoft's online speech service.

Current FFmpeg builds use the `adelay` and `loudnorm` filter mixer. If those
filters are absent—as with the 2013 FFmpeg build bundled by some Python
packages—the exporter automatically decodes the chapter files to timed PCM,
inserts silence itself, encodes AAC, and then embeds that track in the MP4.

For a voice profile that stays local, use Local Voice Studio's Dome
Narration tab: it writes an AAC track and `narration-plan.json`, and the
2V Masterclass tab's "Local Voice Studio narration plan" field points
the exporter at that existing track instead of calling the Edge speech
service.

## How a lesson is put together

A lesson is a `Lesson` (in `lessons.py`): a title, a tuple of `Chapter`s,
and a table of scene painters. The renderer in `app.py` walks the
chapters, asks the lesson to paint each stage, and asks it for any live
figures to print under the chapter's fixed equations. It has no knowledge
of which lesson it is playing, so adding a fifth is a new module plus one
line in `lesson_registry.py`.

Nothing on screen is a typed-in number. Each lesson has a geometry module
that computes and then *proves* its own claims, and `Action = selftest`
runs those proofs:

| Lesson | Geometry module | Proves, among other things |
| --- | --- | --- |
| `2v` | `geometry.py` | 42/120/80 sphere, two chord classes, Euler characteristic 2 |
| `build` | `build_geometry.py` | end cut is exactly half the central angle; a ten-sided base ring amplifies a strut error by exactly phi |
| `hex` | `hex_geometry.py` | the truncated icosahedron really has one strut length and one regular hexagon; every cage has exactly twelve pentagons; the measured angle deficit is 720 degrees when the panels are flat |
| `zome` | `zome_geometry.py` | F = n(n-1), V = n(n-1)+2, E = 2n(n-1); every face a rhombus; a polar zome's level cut is one repeated setting at every height, and the golden zome's is not |

A scene painter is a plain function `(app, opaque, transparent, progress)`.
It fills two `TriangleBatch`es from `render_kit.py` and appends
`WorldLabel`s; it never touches OpenGL. A lesson that omits a stage falls
back to the renderer's own `scene_*` method of that name, which is how the
construction lesson reuses the original 2V derivation scenes.

The build-packet action runs without graphics. It exports CSV cut lists,
triangle details, hub coordinates, edge connectivity, a calculation workbook,
an inch-unit OBJ for CAD, a JSON manifest, and a field guide. Connector
deduction means the total shortening across both ends of one member.

## Presentation controls

- `Space`: play/pause the lesson
- `Left` / `Right`: previous/next chapter
- `Home`: restart
- `1` through `9`, `0`: jump to chapters 1 through 10
- Mouse drag: orbit the camera
- Mouse wheel: zoom
- `R`: restore the chapter camera
- `X`: X-ray sphere
- `U`: switch dimension display between inches and metric
- `S`: save a screenshot in `two_v_demo_output`
- `F11`: toggle fullscreen
- `Esc`: leave fullscreen or quit

## Measurement convention

The math engine uses `SHORT` and `LONG`, because published calculators use
inconsistent A/B naming. The lesson explicitly shows the supplied convention
as A = 72 in LONG and B = 63.5 in SHORT.

All theoretical member lengths are hub-center to hub-center. Physical stock
cut lengths require a connector deduction measured for the chosen hub system.
