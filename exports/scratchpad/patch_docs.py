"""Record the fifth lesson and the two new modules in the pipeline reference."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\docs\video-pipeline-reference.md")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:200])
    s = s.replace(old, new, 1)


sub(
    "`two_v_demo` renders **four** lessons through one renderer, selected by a\n"
    "`lesson` key on the launch ticket (`2v`, `build`, `hex`, `zome`).",
    "`two_v_demo` renders **five** lessons through one renderer, selected by a\n"
    "`lesson` key on the launch ticket (`2v`, `build`, `hex`, `zome`, `line`).",
)

sub(
    "lesson_zome.py      19 chapters: zomes / zonohedra\n"
    "lesson_registry.py  the only module that imports all of them\n"
    "render_kit.py       TriangleBatch, shaders, colours, easing, no GL state\n"
    "```",
    "lesson_zome.py      19 chapters: zomes / zonohedra\n"
    "lesson_line.py      24 chapters: the assembly line's energy ledger\n"
    "lesson_registry.py  the only module that imports all of them\n"
    "render_kit.py       TriangleBatch, shaders, colours, easing, no GL state\n"
    "figure.py           an articulated body: skeleton, poses, drawing\n"
    "energetics.py       what a motion costs, from al_build's own catalogue\n"
    "```\n"
    "\n"
    "`figure.py` and `energetics.py` are only used by the `line` lesson, but\n"
    "they are deliberately independent of it: the figure knows nothing about\n"
    "domes, and the energy model takes any object with `weight`, `labor_min`,\n"
    "`centroid` and `floor_point` -- which is exactly `al_build.Element`.",
)

sub(
    "| `zome` | `zome_geometry.py` | F = n(n-1), V = n(n-1)+2, E = 2n(n-1); "
    "every face a rhombus; a polar zome's level cut is one repeated setting "
    "at every height and the golden zome's is not |",
    "| `zome` | `zome_geometry.py` | F = n(n-1), V = n(n-1)+2, E = 2n(n-1); "
    "every face a rhombus; a polar zome's level cut is one repeated setting "
    "at every height and the golden zome's is not |\n"
    "| `line` | `figure.py` + `energetics.py` | segment masses sum to the "
    "whole body exactly once; Pandolf is superlinear in load; raising a load "
    "costs more than lowering it; a whole build lands between 1,800 and "
    "4,500 kcal per shift and under the sustainable working rate |",
)

sub(
    "**Adding a fifth lesson** is: a geometry module with a `validate_*`\n"
    "function, a lesson module with `CHAPTERS` + `SCENES` + a `Lesson`, one\n"
    "line in `lesson_registry.LESSONS`, and one entry in the launcher's Lesson\n"
    "dropdown.",
    "**Adding a sixth lesson** is: a geometry module with a `validate_*`\n"
    "function, a lesson module with `CHAPTERS` + `SCENES` + a `Lesson`, one\n"
    "line in `lesson_registry.LESSONS`, and one entry in the launcher's Lesson\n"
    "dropdown. Local Voice Studio's lesson picker reads the registry, so it\n"
    "needs no change.\n"
    "\n"
    "### 0c. The `line` lesson costs motions, and says which half is modelled\n"
    "\n"
    "`energetics.py` turns each `al_build` element into six named motions --\n"
    "walk, lift, carry, position, fasten, recover -- plus a recovery\n"
    "allowance, and costs each one. It keeps two quantities strictly apart:\n"
    "\n"
    "* **Mechanical work** is computed. `m g h` for the part, and the same\n"
    "  calculation per body segment for the body, using Winter's tables. It\n"
    "  traces entirely to element masses and placement heights.\n"
    "* **Metabolic cost** is modelled, from Compendium task intensities and\n"
    "  the Pandolf load-carriage equation. Every such value is an\n"
    "  `ExternalConstant` with a `source`, and `Action = report` prints all of\n"
    "  them.\n"
    "\n"
    "Do not let those two merge. `BuildEnergy.mechanical_fraction` is a\n"
    "fraction of a per cent across a build, while `motion_efficiency()['lift']`\n"
    "is near the muscle ceiling; a change that makes those two similar has\n"
    "broken one of them.\n"
    "\n"
    "Two rendering conventions this lesson introduces, both of which will bite\n"
    "anyone extending it:\n"
    "\n"
    "* **Bodies are drawn at `FIGURE_SCALE`.** `joint_positions` works in real\n"
    "  metres, but the renderer's world is about five units across and the\n"
    "  camera looks at a fixed point 2.25 units up, so an unscaled figure came\n"
    "  out small and sat below frame centre.\n"
    "* **+X is screen left.** The lesson's cameras sit on the +Y axis, which\n"
    "  is what makes a sagittal squat readable, and it also reverses left-to-\n"
    "  right order. `_bars` and the motion sequence both lay out from +X down.",
)

p.write_text(s, encoding="utf-8")
print("pipeline reference updated")
