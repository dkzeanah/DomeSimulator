# Wheelchair-First Dome Living — Programmatic Presentation and Video Playbook

Run ID: `dome_accessibility_20260816_082305_167_1d3f14`

This package separates persuasive thinking from rendering. The presentation, narration, scene timing, image prompts, and assembly instructions are stored as versioned files, so a different LLM or renderer can reproduce the work without overwriting a previous run.

## 1. The central argument

Use respectful, person-first or identity-first language such as **wheelchair user**, **older adult**, or **person with limited mobility**. Avoid phrases such as “wheelchair-ridden.”

The persuasive thesis is:

> A purpose-built, single-level dome can make accessible movement the organizing idea of the home. Its open central volume can shorten routes, reduce tight turns, keep daily life on one floor, and make the accessible route the route everyone uses. The dome shape alone does not guarantee accessibility; the plan, thresholds, doors, fixtures, service walls, and site approach must be deliberately designed around the resident and their mobility device.

The argument should remain honest about limitations: curved perimeter walls require straight service walls or carefully planned cabinetry; snow, drainage, site slope, acoustics, ventilation, and local code still require professional design; and the actual user’s chair, transfer method, strength, and reach matter more than a generic standard.

## 2. Source-of-truth architecture

Keep one structured manifest as the handoff contract between LLMs and tools:

1. `video_manifest_20260816_082305_v001.json` — scene order, timing, narration, visual direction, transitions, and evidence.
2. `image_prompt_registry_20260816_082305_v001.txt` — locked image prompts and negative constraints.
3. `narration_script_20260816_082305_v001.txt` — recording-ready narration.
4. `wheelchair_first_dome_living_20260816_082305_v005.pptx` — the editable 12-slide presentation.
5. `build/build_deck_20260816_082305_v005.mjs` — programmatic presentation source.
6. `assemble_slideshow_video_20260816_082305_v001.py` — deterministic FFmpeg assembly wrapper.

Treat the JSON as canonical. An LLM may rewrite prose only by creating a new manifest version, such as `v002`; it should never silently mutate `v001`.

## 3. End-to-end generation sequence

### Phase A — research and argument

1. Define the audience, emotional outcome, desired action, and one-sentence thesis.
2. Retrieve primary sources and store a source ledger with the URL, claim, section, retrieval date, and intended scene.
3. Distinguish evidence from design judgment. For example, ADA dimensions can be used as best-practice reference points without claiming that every private home is governed by ADA standards.
4. Ask an LLM to produce a 10–12 scene argument: problem, opportunity, proof, room-by-room examples, dimensions, counterarguments, and next step.
5. Run a language pass for dignity and agency. The wheelchair user should be shown doing things independently, not positioned as a passive object of care.

### Phase B — storyboard and asset contracts

1. Give every scene a stable ID, duration, narration, on-screen copy, visual description, motion direction, transition, prompt ID, and sources.
2. Generate five to eight high-value reference frames before generating motion. Reuse the same character description, chair geometry, wardrobe, dome materials, lens language, and color palette to improve continuity.
3. Keep labels, dimensions, charts, and captions out of generated images. Add them deterministically in PowerPoint, HTML/CSS, Remotion, Manim, or FFmpeg.
4. For video generation, request short atomic shots—typically 4–8 seconds—with one camera move and one human action. Long multi-action prompts are harder to control.
5. Preserve each prompt, provider, model, seed if available, aspect ratio, source image, and output path in the asset manifest.

### Phase C — narration and timing

1. Generate narration scene by scene rather than as one uninterrupted paragraph.
2. Record or synthesize each scene separately. This makes revisions local and keeps scene timing stable.
3. Measure the produced audio duration, then update `duration_seconds` in the manifest. Do not force narration into a guessed duration.
4. Normalize final narration to a consistent loudness, leave headroom, and keep music below speech.
5. Generate captions from the final audio or approved script, then visually check line breaks and reading speed.

### Phase D — deterministic composition

Recommended baseline: render the slide deck to 16:9 PNGs, assemble them with the included FFmpeg wrapper, and optionally mux a single mastered narration track. This is inexpensive, repeatable, and reliable.

For more motion, rebuild each scene in Remotion or another code-native renderer. Keep text, charts, paths, masks, pan/zoom, captions, music, and transitions in code. Use generated video only for the architectural or human-action plates.

### Phase E — QA gates

Before publishing, verify:

- No text overlaps, clips, or leaves the safe area.
- Wheelchair scale, hands, door swing, counter clearance, and travel path remain visually plausible.
- Every numeric claim has a source and is labeled as a benchmark when appropriate.
- The accessible route is the primary route, not a hidden secondary entrance.
- Captions match the final audio and remain readable on a phone.
- Music does not compete with narration.
- The output directory and filenames are new; the pipeline never overwrites prior media.
- The final MP4 plays from beginning to end and includes the expected number of scenes.

## 4. Programmatic video mechanisms

| Mechanism | Best use | Strength | Tradeoff |
|---|---|---|---|
| Slide PNGs + FFmpeg | Fastest explanatory video | Deterministic, inexpensive, easy to audit | Limited motion unless pan/zoom is added |
| Remotion (React) | Branded motion graphics and captions | Code-native layout, reusable components, precise timing | Requires Node/React development |
| Manim | Animated dimensions, paths, and diagrams | Excellent for geometric explanations | Less natural for lifestyle footage |
| Blender or a 3D engine | Accurate walkthroughs and spatial validation | Camera and geometry can be physically consistent | Highest modeling effort |
| Generative image model | Hero frames, room concepts, visual continuity boards | Fast ideation and strong art direction | Not a construction or compliance drawing |
| Generative video API | Short human-action and camera-movement shots | Creates motion without a full 3D scene | Continuity and geometry can drift |
| TTS API or local voice studio | Narration | Re-records quickly and can be automated | Requires pronunciation and pacing review |
| Avatar video system | Direct-to-camera host segments | Human presence without filming | Can distract from architectural evidence |

A strong hybrid is: **LLM storyboard → image reference frames → optional 4–8 second generated clips → code-rendered text/graphics → TTS → FFmpeg/Remotion master**.

## 5. Handoff prompt for another LLM

Use this as a system or task prompt and attach the manifest:

```text
You are producing a persuasive, evidence-based 16:9 explainer about a purpose-built,
wheelchair-first dome home. Treat the supplied JSON manifest as the source of truth.
Keep the resident dignified, active, and visually consistent. Do not invent statistics.
Do not place text inside generative images. Generate or render one scene at a time,
write outputs into a new timestamp-plus-random-suffix run directory, and refuse to
overwrite any existing file. Preserve prompt, source, model, seed, duration, and output
metadata. Use deterministic code for all typography, charts, dimensions, captions, and
transitions. Label the architecture as conceptual, not a compliance drawing. Finish by
rendering a contact sheet and checking every frame for clipping, continuity, accessibility,
and factual accuracy.
```

## 6. No-overwrite convention

Create a new run directory before doing any work:

```text
{project_slug}_{local_YYYYMMDD_HHMMSS_mmm}_{6_char_random}
```

Inside that run, use immutable versions:

```text
storyboard_v001.json
storyboard_v002.json
hero_entry_v001.png
hero_entry_v002.png
final_video_v001.mp4
```

Creation rules:

1. Create directories with an operation that fails if the path already exists.
2. Before writing a file, assert that the target does not exist.
3. Use FFmpeg’s `-n` flag, never `-y`.
4. A revision increments the version or creates a new run; it never replaces the earlier output.
5. Write a small receipt containing run ID, command, inputs, hashes, model IDs, and final output path.

## 7. Reproduction commands

The final PowerPoint-rendered frames are already in:

```text
wheelchair_first_dome_living_20260816_082305_v005/slide-1.png
...
wheelchair_first_dome_living_20260816_082305_v005/slide-12.png
```

Create a silent draft and captions:

```powershell
python .\assemble_slideshow_video_20260816_082305_v001.py `
  --manifest .\video_manifest_20260816_082305_v001.json `
  --slides-dir .\wheelchair_first_dome_living_20260816_082305_v005 `
  --out-dir .\video_outputs
```

Mux a mastered narration track:

```powershell
python .\assemble_slideshow_video_20260816_082305_v001.py `
  --manifest .\video_manifest_20260816_082305_v001.json `
  --slides-dir .\wheelchair_first_dome_living_20260816_082305_v005 `
  --out-dir .\video_outputs `
  --audio .\narration_master.wav
```

The assembler creates a new timestamped subdirectory every time, uses FFmpeg `-n`, writes an SRT sidecar, and refuses to overwrite existing output.

## 8. Evidence used in this concept

- ADA 2010 Standards, used as best-practice dimensional references for turning space, doors, routes, ramps, and bathroom clearances: https://www.ada.gov/law-and-regs/design-standards/2010-stds/
- CDC older-adult falls data, including the “more than one in four” annual fall estimate and injury consequences: https://www.cdc.gov/falls/data-research/index.html
- National Institute on Aging guidance on aging in place and planning for changing needs: https://www.nia.nih.gov/health/aging-place-growing-older-home
- HUD Fair Housing Act Design Manual for accessible dwelling-unit planning context: https://www.huduser.gov/portal/publications/pdf/fairhousing/fairch1.pdf

Use local residential code and qualified architecture, occupational-therapy, and accessibility professionals before treating any concept as construction-ready.
