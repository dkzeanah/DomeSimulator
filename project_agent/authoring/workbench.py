"""Copyable manual packets. No model calls, shell execution, or lesson writes."""
from __future__ import annotations

import inspect
from pathlib import Path
import re

PACK_DIR = Path(__file__).resolve().parent
ROOT = PACK_DIR.parents[1]
MANUAL_PATH = PACK_DIR / "MANUAL.md"
STARTER_PATH = PACK_DIR / "starter_element.py"
MODELS = ("qwen2.5-coder:7b", "deepseek-rl:7b", "qwen3-vl:4b",
          "granite3.2-vision:2b", "qwen3.5:4b", "llama3.1", "embeddinggemma")
DEFAULT_BRIEF = (
    "Create one eight-second clip showing three members assembling into a "
    "triangular frame. Compute the member count and perimeter from the geometry. "
    "Explain in comments how I change the shapes, narration, camera, and timing."
)


def validate_key(key: str) -> str:
    key = key.strip()
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", key):
        raise ValueError("Use a key of 1–48 lowercase letters, digits, and underscores, starting with a letter.")
    return key


def commands(key: str) -> str:
    key = validate_key(key)
    root = str(ROOT).replace("'", "''")
    runner = "py -3.12 project_agent/authoring/render_lesson.py"
    source = f"--module two_v_demo.lesson_{key}"
    return f"""# Run these yourself in PowerShell, one step at a time.
Set-Location -LiteralPath '{root}'

# Save the model's Python as: {ROOT / 'two_v_demo' / ('lesson_' + key + '.py')}
# Keep the docstring/comments. Remove markdown fences and chat/reasoning text.

# 1. Check Python syntax.
py -3.12 -m py_compile two_v_demo/lesson_{key}.py

# 2. Check the lesson and run its own selftest.
{runner} {source} --selftest

# 3. Inspect a still from each chapter before rendering the video.
{runner} {source} --chapter-stills --size 960x540
# The terminal prints the new folder under two_v_demo_output/{key}/.

# 4. Render ONLY this file's chapters, silent, for checking motion.
{runner} {source} --export exports/manual/{key}-silent.mp4 --silent --size 960x540 --fps 24

# 5. Export only this lesson with the normal film narrator (internet needed).
{runner} {source} --export exports/manual/{key}.mp4 --size 1920x1080 --fps 30

# Existing MP4s are versioned, never replaced. No catalogue registration needed.
# For specific PNG times add --stills 0.5,4,7.9 instead of --chapter-stills,
# but only when those times fall inside YOUR clip's silent duration.
# If 'py' is not available, replace 'py -3.12' with & 'path/to/python.exe'
# using the Python 3.12 interpreter that runs your DomeSim launcher.
"""


def starter_source(key: str = "my_element") -> str:
    return STARTER_PATH.read_text(encoding="utf-8").replace("my_element", validate_key(key))


def api_contract() -> str:
    """Inspect the lightweight source objects, not copied signatures."""
    from two_v_demo.lessons import Chapter, Lesson
    from two_v_demo.render_kit import TriangleBatch, WorldLabel
    lines = ["## Live Python signatures from this checkout", "Use keyword arguments for Chapter and Lesson."]
    for cls in (Chapter, Lesson, WorldLabel):
        lines.append(f"{cls.__name__}{inspect.signature(cls)}")
    for name in ("cylinder", "sphere", "box", "disc", "cone", "arrow", "triangle", "quad"):
        lines.append(f"TriangleBatch.{name}{inspect.signature(getattr(TriangleBatch, name))}")
    return "\n".join(lines)


def output_contract(key: str, brief: str) -> str:
    path = f"two_v_demo/lesson_{key}.py"
    comments = "\n".join("# " + line if line else "#" for line in commands(key).splitlines())
    return f"""## Exact task and required answer format

The requested key is {key!r}. The human will save your answer at:
{ROOT / path}

Requested video element:
{brief.strip()}

Return ONE complete Python file, without markdown fences, separate thinking,
or prose outside that file. Do not claim to have rendered or tested it here.
Begin with a module docstring containing exactly:
SAVE THIS AS: {path}

Use key={key!r}, snapshot_prefix={key!r}, and prefix your painter/stage names
with {key!r}. Define exactly one public Lesson instance named LESSON.
Use absolute two_v_demo imports. Supply all helpers in this one file unless
they are verified existing imports in the context. Do not edit registries,
the renderer, launcher, or other films. Do not compose standard segments.
The file must include a nontrivial validate_{key} function as selftest.
Check that every Chapter.stage is in SCENES and that the computed claims hold.
Use a short single chapter by default unless the brief requests more.

Include HOW TO USE and WHAT TO CHANGE code comments. Explain which functions
control geometry, copy, timing, and camera. Repeat these working commands in
the file's comments (adjust only time-specific examples to the actual duration):

{comments}

An incomplete placeholder, ellipsis, TODO body, invented API, hardcoded claimed
result, or missing usage comment is not a completed answer. If a needed API is
not documented here, request its source instead of guessing its attributes.
"""


def build_manual_prompt(key="my_element", brief=DEFAULT_BRIEF, *, full=False,
                        model="qwen2.5-coder:7b") -> str:
    key = validate_key(key)
    if not brief.strip():
        raise ValueError("Describe the element you want the model to create.")
    if model.strip().split(":")[0].lower() == "embeddinggemma":
        raise ValueError("embeddinggemma is an embedding model. Choose a text-generation model for Python output.")
    from . import CAMERA, RULES, build_prompt
    sections = [
        "# DomeSim manual authoring context\n\n"
        "You receive this as pasted text in a local model chat. You have no implied "
        "access to the human's filesystem or running tools. The human will save, "
        "inspect, and run your Python manually. The requested product is content "
        "for an existing renderer, not a new rendering engine.",
    ]
    if full:
        sections.append("## Human workflow and renderer knowledge\n\n" + MANUAL_PATH.read_text(encoding="utf-8"))
        sections.append(build_prompt(include_example=True))
    else:
        sections.extend([RULES, CAMERA,
            "## Small-clip contract\n"
            "Use math, types.SimpleNamespace, numpy, two_v_demo.lessons, and "
            "two_v_demo.render_kit as shown in the starter. Compute your own "
            "illustration geometry from named inputs. Do not invent project "
            "fact functions or external prices. Use Full context for the existing "
            "object catalogue or a finished Dome Creator building.\n"
            "A painter receives (app, opaque, transparent, p), with p in [0,1]. "
            "Recompute the frame from p so seeking backwards works. Primitive "
            "colours are 0..1 RGBA, WorldLabel colours 0..255 RGB. Label positions "
            "are NumPy 3-vectors appended to app.world_labels.\n"
            "Chapter.duration must exceed 0.5 seconds and is a minimum; online "
            "narration can extend it. Chapter.narration must be a nonempty tuple "
            "of strings, even for --silent. style='hype' gives a large picture "
            "with a headline; style='plate' removes cards/headlines but retains "
            "world labels. Omit labels too for clean footage.\n"
            "The standalone runner runs Lesson.validate and lesson.selftest "
            "before rendering. It does not register your file or add other films.",
        ])
    sections.extend([api_contract(),
        "## Minimal runnable example\n\nCopy this structure and change the visual content to match the brief.\n\n"
        "```python\n" + starter_source(key) + "\n```",
        output_contract(key, brief)])
    return "\n\n".join(sections) + "\n"
