# Manual video authoring

Open **Project Agent → Manual video authoring** in the launcher. Describe an
element, choose a file key, then copy a Compact or Full prompt into your local
model. The answer must be one Python file with its save location, usage
commands, and editing instructions included as comments.

The **Read me / full guide** page explains the complete process. The same
reference lives in [MANUAL.md](MANUAL.md): geometry, animation, cameras, text,
existing objects, Dome Creator buildings, narration, inspection, exports,
and repairing model-generated code.

## Files in this pack

| File | Purpose |
|---|---|
| `MANUAL.md` | Complete human workflow and renderer reference shown in the GUI |
| `gui.py` | Manual authoring panel with copy, preview, and save controls |
| `workbench.py` | Per-brief prompts, exact file paths, commands, and live API signatures |
| `starter_element.py` | Small, runnable eight-second triangle assembly example |
| `example_lesson.py` | Longer dome film demonstrating chapters and project facts |
| `render_lesson.py` | Validate, inspect, and export one lesson without registering it |
| `visual-language.md` | Catalogue of reusable visual elements |
| `__init__.py` | Existing catalogue prompt builder used by the Full packet and CLI |
| `PROMPT.md` | Generated snapshot of that catalogue prompt |

Compact supplies the essential contract and small example. Full adds the
manual, live object/facts catalogue, and longer worked example. The GUI shows
packet size; available context depends on the model and its runtime settings,
so parameter count alone does not establish whether a packet fits. Model
selection records your intended tool; it does not call Ollama. See the manual
for the supplied model list and embedding-model limitations.

## Try the included example

Run these in PowerShell from the DomeSim folder, inspecting the PNGs before
the export command:

```powershell
py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.starter_element --selftest
py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.starter_element --chapter-stills --size 960x540
py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.starter_element --export exports/manual/triangle-demo.mp4 --silent --size 960x540 --fps 24
```

Each still run prints a fresh folder under `two_v_demo_output/my_element/`.
Existing MP4s receive a new version suffix. Omit `--silent` for the normal
online film narrator. Only this lesson's chapters are rendered.

For your own element, save the model's Python to the location displayed in the
panel, such as `two_v_demo/lesson_roof_reveal.py`, then use the **Commands** page.
Remove Markdown fences and chat text; retain the Python docstring and comments.
No lesson registry, launcher preset, or deliverables edit is needed for this
manual workflow.

## Existing command-line prompt builder

The CLI remains available for the original catalogue packet:

```powershell
py -3.12 -m project_agent authoring --brief "A film explaining triangular bracing" --out prompt.md
py -3.12 -m project_agent authoring --out project_agent/authoring/PROMPT.md
```

The second command regenerates the tracked snapshot from the current source.
Use the GUI for a packet tailored to an exact file key with the complete
save-and-export comment contract.
