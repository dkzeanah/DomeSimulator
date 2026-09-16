"""The authoring pack: what a language model needs to write a new film.

The agent can already *run* the film pipeline. What it could not do was
**author** one, because the visual vocabulary of this project lives in code
and in habit, not in a document a model can read.

This module builds that document. It assembles a single paste-ready prompt
from three things:

* the hard rules, written once, here;
* the live catalogues -- colours, drawing calls, ready-made objects, icons,
  chapter and lesson fields, the validated facts modules -- read out of the
  repository at build time, so the prompt cannot describe a tool that no
  longer exists;
* a worked example that is proven to render, inlined verbatim from
  ``example_lesson.py``.

    py -3.12 -m project_agent authoring                    # print it
    py -3.12 -m project_agent authoring --out PROMPT.md    # save it
    py -3.12 -m project_agent authoring --brief "a film about roof loads"

Paste the result into any code-capable model. It is sized for a 7B local
model: about 4,000 words, which is roughly 6,000 tokens, leaving room in a
32k context for the model's own answer.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = PACK_DIR / "example_lesson.py"


# ----------------------------------------------------------------------
# Live catalogues, read from the repository
# ----------------------------------------------------------------------

def catalogue() -> dict:
    """Everything the prompt states about the repo, read from the repo."""
    from two_v_demo import icons, render_kit, visual_objects
    from two_v_demo.lessons import Chapter, Lesson
    from project_agent.facts import FACT_SPECS

    colours = [name for name in dir(render_kit)
               if name.isupper() and isinstance(getattr(render_kit, name), tuple)
               and len(getattr(render_kit, name)) == 4]
    objects = []
    for key, obj in visual_objects.registry().items():
        knobs = ", ".join(knob.key for knob in obj.knobs)
        objects.append((key, obj.label, knobs))
    facts = [(fact_id, spec.description.split(".")[0])
             for fact_id, spec in sorted(FACT_SPECS.items())]
    return {
        "colours": sorted(colours),
        "objects": objects,
        "icons": list(icons.icon_keys()),
        "chapter_fields": [f.name for f in dataclasses.fields(Chapter)],
        "lesson_fields": [f.name for f in dataclasses.fields(Lesson)],
        "facts": facts,
    }


# ----------------------------------------------------------------------
# The prompt
# ----------------------------------------------------------------------

RULES = """\
# Write one DomeSim film

You are writing ONE Python file: a *lesson module* for the DomeSim
repository. A lesson is a narrated 3-D film. The renderer already exists;
your file supplies the chapters, the copy, and the painting code.

## Hard rules. A file that breaks any of these is rejected.

1. **Every number on screen is computed, never typed.** Import a facts
   module and call it. If a figure genuinely cannot be derived -- a price, a
   labour rate -- assign it to a named constant with a comment saying where
   it came from, and keep those together in one block.
2. **Lay rows of things out along X.** The camera sits on +Y looking at the
   origin, so two objects separated along Y are separated in *depth*: the
   near one hides the far one and both look foreshortened. Separate along X,
   or stack along Z.
3. **A painter is a pure function of (app, opaque, transparent, progress).**
   Never read the clock, never use an unseeded random number. The same
   progress value must always draw the same frame, or the render is not
   reproducible.
4. **The lesson proves itself.** Write a validate function that asserts what
   the film claims, and pass it as `selftest=`. The renderer runs it before
   drawing anything.
5. **Import only** from: `two_v_demo.lessons`, `two_v_demo.render_kit`,
   `two_v_demo.visual_objects`, the facts modules listed below, plus `math`
   and `numpy`. No file reading, no network, no subprocess.
6. **Nothing straddles z=0.** The ground is at z=0; build upward.
"""

CAMERA = """\
## The camera and the stage

`camera=(yaw_degrees, pitch_degrees, distance)` on every chapter. The camera
orbits a fixed target at (0, 0, 2.25).

* `yaw=90` puts the camera on +Y. X then runs across the screen: this is the
  yaw to use for any row or line-up.
* `yaw=40..55` gives a three-quarter view, good for a single object.
* `pitch` 12-22 for most shots; 30-40 to look down into something.
* `distance` about twice the widest thing on screen. A 5-unit dome frames
  well at 15-18.

World units are metres-ish: a person is 1.8 tall, a dome 5 across. Keep the
subject in the upper two-thirds of the frame -- the overlay uses the bottom.
"""

OUTPUT = """\
## What to output

Exactly one Python file. No explanation before or after it, no markdown
fences around it -- just the file, starting with its docstring.

The docstring must state, on its own line, where the file is saved:

    SAVE THIS AS: two_v_demo/lesson_<key>.py

Use the same `<key>` everywhere: the file name, the `key=` field, the
`snapshot_prefix=`, and the prefix on every scene name. `<key>` is lowercase
letters, digits and underscores, starting with a letter.

The file must end with a module-level `Lesson(...)` assignment.

After the Lesson, add a comment block giving the two commands that run it:

    # HOW TO SEE IT
    #   py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_<key> --chapter-stills
    #   py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_<key> --export exports/<key>.mp4

## Checklist -- read your own file against this before answering

* every figure on screen traces to a facts call or a named, sourced constant
* every row is laid along X, not Y
* every chapter has: slug, number, title, promise, narration, equations,
  duration, camera, stage -- in that order
* every `stage` string appears as a key in the SCENES dict
* narration is one complete sentence per tuple entry
* chapter numbers are "01", "02", ... and are unique
* the validate function asserts something that could actually fail
* the file imports nothing outside the allowed list
"""


def _section(title: str, rows, formatter) -> str:
    lines = [title]
    for row in rows:
        lines.append(formatter(row))
    return "\n".join(lines)


def build_prompt(brief: str = "", include_example: bool = True) -> str:
    """Assemble the paste-ready prompt from the live repository."""
    data = catalogue()
    parts: list[str] = [RULES]

    api = ["## The drawing API",
           "",
           "Two batches reach every painter. `opaque` for solid things,",
           "`transparent` for anything with alpha below 1 (glass, ghosts,",
           "shading). Both are the same type and take the same calls:",
           "",
           "    opaque.cylinder(start, end, radius, colour, sides=8)",
           "    opaque.sphere(centre, radius, colour, rings=5, segments=8)",
           "    opaque.box(centre, size, colour)",
           "    opaque.disc(centre, radius, colour, segments=48)",
           "    opaque.cone(base, tip, radius, colour, sides=10)",
           "    opaque.arrow(start, end, radius, colour)",
           "    opaque.triangle(a, b, c, colour, normal=None)",
           "    opaque.quad(a, b, c, d, colour, normal=None)",
           "",
           "Points are `np.array([x, y, z])`. Colours are RGBA tuples,",
           "0.0-1.0. Import the named ones from `two_v_demo.render_kit`:",
           "",
           "    " + "  ".join(data["colours"]),
           "",
           "Also from render_kit: `clamp(v)`, `smoothstep(v)`,",
           "`ease_in_out(v)` for easing a reveal, and `WorldLabel`.",
           "",
           "### Text pinned in the world",
           "",
           "    app.world_labels.append(WorldLabel(",
           "        np.array([x, y, z]), \"TEXT\", (red, green, blue)))",
           "",
           "The colour here is 0-255 integers, not floats. Labels are drawn",
           "as flat text at that point, always facing the viewer."]
    parts.append("\n".join(api))

    objects = ["## Ready-made objects",
               "",
               "Do not redraw what exists. Put one on the stage with:",
               "",
               "    stage = visual_objects.stage_for(app, opaque, transparent,",
               "                                     origin=(x, y, z))",
               "    visual_objects.draw(stage, \"person\", height=1.8)",
               "",
               "| key | what it is | knobs |",
               "|---|---|---|"]
    for key, label, knobs in data["objects"]:
        objects.append(f"| {key} | {label} | {knobs} |")
    objects.extend(["",
                    "Pictograms available to the `icon` object and to callouts:",
                    "",
                    "    " + ", ".join(data["icons"])])
    parts.append("\n".join(objects))

    facts = ["## Where numbers come from",
             "",
             "Call one of these. Each is validated by its own module, which",
             "is what makes it safe to put on screen:",
             "",
             "| facts id | module.function | what it gives |",
             "|---|---|---|"]
    from project_agent.facts import FACT_SPECS
    for fact_id, description in data["facts"]:
        spec = FACT_SPECS[fact_id]
        facts.append(f"| {fact_id} | {spec.module}.{spec.func} | {description} |")
    facts.extend(["",
                  "In a lesson module, import the function directly, e.g.",
                  "`from two_v_demo.geometry import build_demo_geometry`."])
    parts.append("\n".join(facts))

    parts.append(CAMERA)

    fields = ["## Chapter and Lesson",
              "",
              "`Chapter(" + ", ".join(data["chapter_fields"]) + ")`",
              "",
              "* `slug` short id, `number` \"01\" upward, `title` on the card",
              "* `promise` one sentence -- the headline, spoken as well in",
              "  teaching style",
              "* `narration` a tuple of complete sentences, one per entry",
              "* `equations` a tuple of short lines for the live calculation",
              "  panel; leave it `()` only if you want that panel empty",
              "* `duration` seconds, the floor -- narration may run longer",
              "* `stage` the SCENES key this chapter paints",
              "* `overlay` optional: \"math\" turns the chapter into a",
              "  worksheet with the picture on the left",
              "",
              "`Lesson(" + ", ".join(data["lesson_fields"]) + ")`",
              "",
              "* `style` \"teaching\" (cards) or \"hype\" (one big line)",
              "* `label_layout=\"declutter\"` stops world labels overlapping",
              "* `ground=\"off\"` if your subject brings its own floor",
              "* `selftest` your validate function"]
    parts.append("\n".join(fields))

    parts.append(OUTPUT)

    if include_example and EXAMPLE_PATH.is_file():
        example = EXAMPLE_PATH.read_text(encoding="utf-8")
        parts.append("## A complete worked example\n\n"
                     "This file renders today. Copy its shape.\n\n"
                     "```python\n" + example + "```")

    if brief:
        parts.append("## Your task\n\n" + brief.strip() + "\n\n"
                     "Write the file now. Output nothing but the file.")
    else:
        parts.append("## Your task\n\n"
                     "Replace this section with what the film should be about, "
                     "then output nothing but the file.")

    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m project_agent authoring",
        description="Build the paste-ready film-authoring prompt.")
    parser.add_argument("--out", default="",
                        help="write to this file instead of printing")
    parser.add_argument("--brief", default="",
                        help="what the film should be about")
    parser.add_argument("--no-example", action="store_true",
                        help="leave the worked example out (smaller prompt)")
    args = parser.parse_args(argv)

    text = build_prompt(args.brief, include_example=not args.no_example)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        words = len(text.split())
        print(f"wrote {path}  ({words:,} words, about {words * 4 // 3:,} tokens)")
    else:
        print(text)
    return 0
