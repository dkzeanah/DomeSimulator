"""Generate a working new lesson from one command.

    py -3.12 scaffold_lesson.py mysubject "My Subject Masterclass"

Writes a facts module and a lesson module that already render, already
prove themselves, and already pass selftest.  The point is that the
first thing you do on a new subject is not boilerplate -- it is deleting
the placeholder facts and putting real ones in.

The generated pair follows the house rules on purpose:

* the facts module **computes** its numbers and **proves** them, so the
  discipline is in place before the first real figure is added;
* the lesson pulls every on-screen value from that module, so nothing
  can be typed into a caption;
* the scenes are laid out along X, because this renderer's cameras sit
  on +Y and anything separated along Y is separated in depth instead.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PACKAGE = Path("two_v_demo")

FACTS_TEMPLATE = '''"""Measured facts for the {title} lesson.

Every number the lesson puts on screen is computed here and proved in
:func:`validate_{key}`.  If a value cannot be computed from something,
it is an external constant: name it, source it, and print it in the
report so a viewer can see which figures are derived and which are
borrowed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache


# --- external constants ------------------------------------------------
# Anything this module takes on authority rather than deriving.  Keep the
# list short and keep it honest; it is the first thing a sceptic reads.

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("example_constant", 2.0, "dimensionless",
     "Replace this with a real sourced value, or delete it."),
)


@dataclass(frozen=True)
class {cls}Item:
    """One measured thing. Replace with whatever this subject is about."""

    name: str
    size: float
    count: int

    @property
    def total(self) -> float:
        return self.size * self.count


@lru_cache(maxsize=1)
def {key}_items() -> tuple[{cls}Item, ...]:
    """Compute the subject's parts. This is where the real work goes."""
    return tuple(
        {cls}Item(name=f"CLASS-{{index + 1}}",
                  size=1.0 / (index + 1),
                  count=(index + 1) * 4)
        for index in range(4)
    )


@lru_cache(maxsize=1)
def {key}_summary() -> dict:
    items = {key}_items()
    return {{
        "classes": len(items),
        "parts": sum(item.count for item in items),
        "total": sum(item.total for item in items),
        "largest": max(item.size for item in items),
    }}


def {key}_report() -> str:
    """A portable audit of every claim the lesson makes."""
    summary = {key}_summary()
    lines = ["{TITLE} - CALCULATION AUDIT", ""]
    for key, value in summary.items():
        lines.append(f"  {{key:<10}} {{value}}")
    lines.append("")
    for item in {key}_items():
        lines.append(f"  {{item.name:<10}} size {{item.size:8.4f}}  "
                     f"x{{item.count:<4}} total {{item.total:8.4f}}")
    lines.append("")
    lines.append("external constants this model takes on authority:")
    for name, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {{name:<22}} {{value:g}} {{units:<14}} {{source}}")
    return "\\n".join(lines)


def validate_{key}() -> None:
    """Prove the model before any of its numbers reach a screen."""
    items = {key}_items()
    assert items, "there must be at least one item"
    assert len({{item.name for item in items}}) == len(items), "duplicate names"
    for item in items:
        assert item.size > 0.0, item
        assert item.count > 0, item
        assert math.isclose(item.total, item.size * item.count), item

    summary = {key}_summary()
    assert summary["classes"] == len(items)
    assert summary["parts"] == sum(item.count for item in items)
    assert summary["largest"] == max(item.size for item in items)
    # Every external constant must be named and sourced.
    for name, _, units, source in EXTERNAL_CONSTANTS:
        assert name and units and source, name
'''


LESSON_TEMPLATE = '''"""{title}.

Scenes and copy.  Every figure comes from :mod:`two_v_demo.{key}_facts`,
which computes and proves them.

Layout note: this renderer's cameras sit on +Y, so two things separated
along Y are separated in *depth* and the nearer one hides the further
one.  Lay rows out along **X**.
"""

from __future__ import annotations

import math

import numpy as np

from .{key}_facts import (
    EXTERNAL_CONSTANTS,
    {key}_items,
    {key}_report,
    {key}_summary,
    validate_{key},
)
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


ITEMS = {key}_items()
SUMMARY = {key}_summary()
PALETTE = (CYAN, AMBER, GREEN, PURPLE, RED)


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def scene_{key}_overview(app, opaque, transparent, p: float) -> None:
    """Open on the whole subject, assembling."""
    reveal = smoothstep(clamp(p * 1.5))
    for index, item in enumerate(ITEMS):
        if index / len(ITEMS) > reveal:
            continue
        angle = math.tau * index / len(ITEMS)
        centre = np.array([4.0 * math.cos(angle), 4.0 * math.sin(angle), 1.6])
        colour = PALETTE[index % len(PALETTE)]
        opaque.sphere(centre, 0.5 + item.size, colour, 5, 12)
        opaque.cylinder(np.array([0.0, 0.0, 1.6]), centre, 0.05, MUTED, 6)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.0]),
        f"{{SUMMARY['parts']}} PARTS IN {{SUMMARY['classes']}} CLASSES",
        (61, 211, 255)))


def scene_{key}_classes(app, opaque, transparent, p: float) -> None:
    """A labelled bar per class -- the montage's workhorse shape."""
    reveal = clamp(p * 1.35)
    largest = max(item.total for item in ITEMS) or 1.0
    span = 12.0
    step = span / max(1, len(ITEMS) - 1)
    for index, item in enumerate(ITEMS):
        if index / len(ITEMS) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.0 * (item.total / largest)
        colour = PALETTE[index % len(PALETTE)]
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.0, 0.9, max(0.05, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.9]),
            f"{{item.name}}\\nx{{item.count}}", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.9]),
        "replace these with the real classes", (169, 188, 203)))


def scene_{key}_recap(app, opaque, transparent, p: float) -> None:
    """Close by restating the shape of the answer."""
    spin = p * math.tau * 0.35
    for index, item in enumerate(ITEMS):
        angle = math.tau * index / len(ITEMS) + spin
        centre = np.array([3.4 * math.cos(angle), 3.4 * math.sin(angle),
                           1.4 + item.size])
        opaque.box(tuple(centre), (1.2, 1.2, 0.5),
                   PALETTE[index % len(PALETTE)])
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.8]),
        "EVERY NUMBER HERE WAS COMPUTED", (111, 235, 155)))


SCENES = {{
    "{key}_overview": scene_{key}_overview,
    "{key}_classes": scene_{key}_classes,
    "{key}_recap": scene_{key}_recap,
}}


def {key}_equations(app, stage: str) -> list[str]:
    """Live figures. The renderer appends these to a chapter's fixed lines,
    so do not restate anything already written there."""
    if stage == "{key}_overview":
        return [f"total = {{SUMMARY['total']:.4f}}"]
    if stage == "{key}_classes":
        return [
            f"{{item.name:<10}} {{item.size:7.4f}} x{{item.count:<4}} "
            f"= {{item.total:8.4f}}"
            for item in ITEMS
        ]
    return []


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "overview", "01", "What we are looking at",
        "One sentence that says what this lesson proves.",
        (
            "Replace this narration with what is actually spoken. Keep it to prose a",
            "person would say out loud; the numbers live on the card, not in the mouth.",
        ),
        (f"parts = {{SUMMARY['parts']}}", f"classes = {{SUMMARY['classes']}}"),
        12.0, (34.0, 24.0, 16.0), "{key}_overview",
    ),
    Chapter(
        "classes", "02", "The classes",
        "What the parts sort into, and how many of each.",
        (
            "One bar per class, measured rather than asserted. Say why the grouping is",
            "the grouping, and what it costs the person building this.",
        ),
        ("grouped by measurement, not by name",),
        14.0, (90.0, 16.0, 18.0), "{key}_classes",
    ),
    Chapter(
        "recap", "03", "The whole thing, once more",
        "Every figure came from the model and can be recomputed.",
        (
            "Close by saying what changed for the viewer. Every number in this lesson",
            "came from a function that also proves itself, which is the only reason it",
            "is worth putting on screen at all.",
        ),
        ("computed -> proved -> drawn",),
        12.0, (30.0, 26.0, 16.0), "{key}_recap",
    ),
)


{KEY}_LESSON = Lesson(
    key="{key}",
    brand="{BRAND}",
    title="{title}",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations={key}_equations,
    selftest=validate_{key},
    report={key}_report,
    snapshot_prefix="{key}",
)
'''


ENTRY_TEMPLATE = '''"""Public launcher for the {title} lesson.

Same renderer as ``two_v_masterclass.py``, different lesson. Launch and
configure it from the consolidated launcher (``py -3.12 launcher.py``),
whose Masterclass tab has a Lesson field. Run directly with no launcher
ticket present and it opens this lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="{key}"))
'''


def scaffold(key: str, title: str, force: bool = False) -> int:
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,15}", key):
        print(f"key must be lower-case letters, digits and underscores: {key!r}")
        return 2
    if not PACKAGE.is_dir():
        print(f"run this from the repository root; {PACKAGE} not found")
        return 2

    cls = "".join(part.title() for part in key.split("_"))
    fields = {
        "key": key,
        "KEY": key.upper(),
        "cls": cls,
        "title": title,
        "TITLE": title.upper(),
        "BRAND": title.upper(),
    }

    targets = {
        PACKAGE / f"{key}_facts.py": FACTS_TEMPLATE.format(**fields),
        PACKAGE / f"lesson_{key}.py": LESSON_TEMPLATE.format(**fields),
        Path(f"{key}_masterclass.py"): ENTRY_TEMPLATE.format(**fields),
    }
    existing = [path for path in targets if path.exists()]
    if existing and not force:
        print("refusing to overwrite:")
        for path in existing:
            print(f"  {path}")
        print("pass --force if that is what you want")
        return 1

    for path, body in targets.items():
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path}")

    print()
    print("Now, in order:")
    print(f"  1. register it: add {key.upper()}_LESSON to "
          f"two_v_demo/lesson_registry.py")
    print(f"  2. prove it:    Action = selftest, Lesson = {key}")
    print(f"  3. look at it:  render a still per chapter and open every one")
    print(f"  4. replace the placeholder facts in "
          f"two_v_demo/{key}_facts.py with real ones")
    print(f"  5. add it to two_v_demo/deliverables.py so render_all "
          f"rebuilds it")
    print()
    print("docs/video-engine.md section 7 is the long version.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("key", help="short lower-case lesson key, e.g. 'trusses'")
    parser.add_argument("title", help='display title, e.g. "Truss Masterclass"')
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing files")
    args = parser.parse_args()
    return scaffold(args.key, args.title, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
