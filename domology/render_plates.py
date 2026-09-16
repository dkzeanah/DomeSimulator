"""Render Domology's plates, each with the tool that owns it.

::

    py -3.12 -m domology.render_plates                # everything not yet rendered
    py -3.12 -m domology.render_plates --ids rigidity,forge-water
    py -3.12 -m domology.render_plates --tools chart --force

Every tool that opens a graphics window runs in its own process, so one tool's
OpenGL context can never trip another's. Every render is written to
``deliverables/domology/plates/<id>.png`` -- or ``-v2``, ``-v3`` if an older
version exists, because rendered output is append-only here -- beside a JSON
record of the recipe, the tool, the size and the time it was made.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config
from .plates import BY_ID, PLATES, Plate, latest_render

WORK = config.CACHE / "plate-work"


# ----------------------------------------------------------------------
# Publishing a finished render
# ----------------------------------------------------------------------

def publish(plate: Plate, source: Path, details: dict | None = None) -> Path:
    from two_v_demo.deliverables import next_version_path
    config.PLATES.mkdir(parents=True, exist_ok=True)
    target = next_version_path(config.PLATES / f"{plate.id}.png")
    shutil.copyfile(source, target)
    record = {"plate": plate.id, "title": plate.title, "tool": plate.tool,
              "concept": plate.concept, "change": plate.change, "recipe": plate.recipe,
              "size": list(plate.size), "rendered": datetime.now().isoformat(timespec="seconds"),
              **(details or {})}
    target.with_suffix(".json").write_text(json.dumps(record, indent=2, default=str),
                                           encoding="utf-8")
    return target


# ----------------------------------------------------------------------
# Workers (run in their own process)
# ----------------------------------------------------------------------

def film_worker(ids: list[str], size: tuple[int, int]) -> int:
    """Shoot the film and scene plates through the film engine.

    The engine's own shots action stops at the first scene that raises; this
    shoots one plate at a time, so one broken scene costs one plate.
    """
    import traceback
    sys.path.insert(0, str(config.ROOT))
    from two_v_demo import lesson_registry
    from two_v_demo.app import MasterclassApp
    from . import plate_lesson
    plates = [BY_ID[plate_id] for plate_id in ids]
    lesson, times = plate_lesson.build(plates)
    lesson_registry.LESSONS[lesson.key] = lesson
    app = MasterclassApp(size=size, fullscreen=False, hidden=True, lesson=lesson)
    output = config.ROOT / "two_v_demo_output" / lesson.key
    failures = 0
    for plate, shot in zip(plates, times):
        try:
            app.render_shots([shot], output)
        except Exception as error:  # report it and shoot the next plate
            failures += 1
            print(f"FAILED {plate.id}: {type(error).__name__}: {error}", flush=True)
            traceback.print_exc()
    app.pygame.quit()
    return 1 if failures else 0


def _forge_apply(app, recipe: dict) -> None:
    from dome_forge.jigs import STEPS
    from dome_forge.layers import default_stack, split_log_stack
    app.plate_recipe = recipe
    app.stack = split_log_stack() if recipe.get("stack") == "splitlog" else default_stack()
    stack = app.stack
    # A recipe may ask for a layer the starting stack does not carry.
    wanted = set(recipe.get("only") or ()) | set((recipe.get("layers") or {}).keys())
    for kind in sorted(wanted - {layer.kind for layer in stack.layers}):
        stack.add(kind)
    faces = recipe.get("select", ())
    if faces == "all":
        faces = range(40)
    stack.selected_faces = set(faces)
    # The app eases the pop-out toward explode_amount frame by frame; a still
    # has no frames, so set it where the easing would arrive.
    if recipe.get("explode"):
        app.explode_amount = float(recipe["explode"])
    stack.explode = app.explode_amount if stack.selected_faces else 0.0
    settings = stack.settings
    cut = recipe.get("cut")
    settings.cut_enabled = bool(cut)
    if cut:
        settings.cut_start, settings.cut_sweep = float(cut[0]), float(cut[1])
    only = recipe.get("only")
    for layer in stack.layers:
        if only is not None:
            layer.visible = layer.kind in only
        change = (recipe.get("layers") or {}).get(layer.kind, {})
        for key, value in change.items():
            if key == "visible":
                layer.visible = bool(value)
            elif key == "opacity":
                layer.opacity = float(value)
            else:
                layer.set(key, value)
    app.set_mode(recipe.get("mode", "dome"))
    if "jig" in recipe:
        app.jig_index = int(recipe["jig"])
    if "stage" in recipe:
        app.step_index = next(i for i, step in enumerate(STEPS) if step.stage == recipe["stage"])
    if "bench" in recipe:
        app.bench_struts = list(recipe["bench"])
    if "fill" in recipe:
        app.bench_fill = recipe["fill"]
    if "group" in recipe:
        app.group_kind, app.group_index = recipe["group"][0], int(recipe["group"][1])
    if "joint" in recipe:
        stack.assignments.joint = recipe["joint"]
        for layer in stack.layers:
            if layer.kind == "waist_joints":
                layer.visible = True
    app.yaw = float(recipe.get("yaw", app.yaw))
    app.pitch = float(recipe.get("pitch", app.pitch))
    app.distance = float(recipe.get("distance", app.distance))
    app.clock_t = float(recipe.get("clock", 0.0))


def forge_worker(jobs: list[tuple[str, dict]], size: tuple[int, int]) -> int:
    """Capture Dome Forge plates with the interface hidden."""
    import numpy as np
    import pygame
    from dome_forge.app import DomeForgeApp
    app = DomeForgeApp(size=size, hidden=True)
    app.draw_ui = lambda width, height: pygame.Surface((width, height), pygame.SRCALPHA)
    original = app.camera

    def centred():
        # The app shifts its view to leave room for the side panels; with the
        # panels hidden, aim at the middle of what is being shown.
        if app.mode == "groups":
            from dome_forge.build import DomeContext
            from dome_forge.groups import group_centre
            centre = np.asarray(group_centre(DomeContext(app.stack.settings.radius),
                                             app.group_faces()), dtype=np.float32)
            direction = centre / max(1e-6, float(np.linalg.norm(centre)))
            return (centre + direction * app.distance).astype(np.float32), centre
        if app.mode not in ("panel", "jigs"):
            return original()
        pitch, yaw = math.radians(app.pitch), math.radians(app.yaw)
        target = np.zeros(3, dtype=np.float32)
        focus = (getattr(app, "plate_recipe", None) or {}).get("focus_corner")
        if app.mode == "panel" and focus is not None:
            target = np.asarray(app.bench_corners()[int(focus)], dtype=np.float32)
        eye = target + np.array([app.distance * math.cos(pitch) * math.cos(yaw),
                                 app.distance * math.cos(pitch) * math.sin(yaw),
                                 app.distance * math.sin(pitch)], dtype=np.float32)
        return eye, target

    app.camera = centred
    try:
        for out, recipe in jobs:
            _forge_apply(app, recipe)
            app.capture(Path(out))
            print(f"forge: {out}", flush=True)
    finally:
        pygame.quit()
    return 0


def line_worker(jobs: list[tuple[str, dict]], size: tuple[int, int]) -> int:
    """Stop the assembly line at a station and capture it."""
    import numpy as np
    import pygame
    sys.path.insert(0, str(config.ROOT))
    from assembly_line_simple import STAGES, AssemblyLineApp
    app = AssemblyLineApp(headless=True, size=size)
    app.draw_hud = lambda: None
    try:
        for out, recipe in jobs:
            app.reset()
            index = next(i for i, phase in enumerate(app.phases)
                         if phase.kind == "work" and STAGES[phase.station].key == recipe["stage"])
            app.phase_idx = index
            # At the full duration the line would step on to the next phase.
            app.phase_t = app.phase.dur * min(0.995, float(recipe.get("fraction", 0.95)))
            app.force_cutaway = bool(recipe.get("cutaway", False))
            app.update(0)
            x, y, z, *_rest = app.dome_pose()
            app.cam_target = np.array([x, y, z + float(recipe.get("lift", 1.8))], dtype=np.float32)
            app.cam_yaw = math.radians(float(recipe.get("yaw", 0.0)))
            app.cam_pitch = math.radians(float(recipe.get("pitch", 32.0)))
            app.cam_dist = float(recipe.get("distance", 13.8))
            app.render()
            app.ctx.finish()
            pixels = app.fbo.read(components=3)
            surface = pygame.image.fromstring(pixels, app.size, "RGB", True)
            pygame.image.save(surface, str(out))
            print(f"line: {out}", flush=True)
    finally:
        pygame.quit()
    return 0


def _label_parts(sheet, widths, labels) -> None:
    """Name each part of a composite in the films' label style -- light type on a
    dark panel -- with any number in the name read from a token."""
    if not labels:
        return
    from PIL import ImageDraw, ImageFont
    from . import fonts
    from .markup import Resolver
    from .plate_scenes import resolve_text
    resolver = Resolver(strict=True)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(fonts.face_path("sans", "sb")), 46)
    x = 0
    for width, text in zip(widths, labels):
        text = resolve_text(text, resolver)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        box = (x + 48, 48, x + 96 + (right - left), 84 + (bottom - top))
        draw.rounded_rectangle(box, radius=14, fill=(3, 10, 18), outline=(233, 242, 250),
                               width=2)
        draw.text((box[0] + 24 - left, box[1] + 18 - top), text, font=font,
                  fill=(233, 242, 250))
        x += width + 24


# ----------------------------------------------------------------------
# The runner
# ----------------------------------------------------------------------

def _size_text(size) -> str:
    return f"{size[0]}x{size[1]}"


def _run_worker(args: list[str], log: list[str], timeout: int = 3600) -> bool:
    command = [sys.executable, "-m", "domology.render_plates", *args]
    result = subprocess.run(command, cwd=config.ROOT, capture_output=True, text=True,
                            timeout=timeout, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log.append(result.stdout[-4000:])
    if result.returncode != 0:
        log.append(result.stderr[-6000:])
        return False
    return True


def render(ids: list[str] | None = None, tools: list[str] | None = None,
           force: bool = False, proof: bool = False, verbose: bool = True) -> dict:
    """Render what is asked for (by default, every plate never rendered).

    ``proof`` renders into the work folder only, to be looked at before a
    plate is published into the book.
    """
    selected = [p for p in PLATES if (not ids or p.id in ids) and (not tools or p.tool in tools)]
    if not force and not proof:
        selected = [p for p in selected if latest_render(p.id) is None]
    WORK.mkdir(parents=True, exist_ok=True)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    folder = WORK / stamp
    folder.mkdir(parents=True, exist_ok=True)
    done: dict[str, Path] = {}
    failed: dict[str, str] = {}
    log: list[str] = []

    def say(text: str) -> None:
        if verbose:
            print(text, flush=True)

    def keep(plate: Plate, source: Path, details: dict) -> Path:
        if proof:
            target = folder / f"{plate.id}.png"
            if Path(source).resolve() != target.resolve():
                shutil.copyfile(source, target)
            return target
        return publish(plate, source, details)

    # Charts, in this process.
    from . import charts
    for plate in [p for p in selected if p.tool == "chart"]:
        out = folder / f"{plate.id}.png"
        try:
            charts.render(plate.recipe["chart"], out, plate.size)
            done[plate.id] = keep(plate,out, {"source": "domology.charts"})
            say(f"chart   {plate.id}")
        except Exception as error:  # a broken chart must not stop the others
            failed[plate.id] = f"{type(error).__name__}: {error}"

    # Film and scene plates, one engine process per print size.
    shoots = [p for p in selected if p.tool in ("film", "scene")]
    for size in sorted({p.size for p in shoots}):
        group = [p for p in shoots if p.size == size]
        say(f"film    {len(group)} plates at {_size_text(size)} ...")
        started = time.time()
        output = config.ROOT / "two_v_demo_output" / "domology_plates"
        ok = _run_worker(["--worker", "film", "--size", _size_text(size),
                          "--ids", ",".join(p.id for p in group)], log)
        for index, plate in enumerate(group):
            progress = min(0.985, max(0.0, float(plate.recipe.get("progress", 0.6))))
            shot = round(index * 10.0 + progress * 10.0, 2)
            png = output / f"plate_{shot:07.2f}s.png"
            if png.exists() and png.stat().st_mtime >= started - 1:
                done[plate.id] = keep(plate,png, {"engine": "two_v_demo.app shots"})
                say(f"film    {plate.id}")
            else:
                failed[plate.id] = "the film engine did not write this frame"

    # Dome Forge and the assembly line, one process each.
    for tool, worker in (("forge", "forge"), ("line", "line")):
        group = [p for p in selected if p.tool == tool]
        composite_parts = []
        if tool == "forge":
            for plate in [p for p in selected if p.tool == "composite"]:
                for number, part in enumerate(plate.recipe["parts"]):
                    if part.get("tool") == "forge":
                        composite_parts.append((f"{plate.id}__{number}", part, plate.size))
        jobs = [(str(folder / f"{p.id}.png"), p.recipe) for p in group]
        jobs += [(str(folder / f"{key}.png"), part) for key, part, _size in composite_parts]
        if not jobs:
            continue
        size = group[0].size if group else composite_parts[0][2]
        job_file = folder / f"{tool}-jobs.json"
        job_file.write_text(json.dumps(jobs), encoding="utf-8")
        say(f"{tool:<7} {len(jobs)} captures ...")
        ok = _run_worker(["--worker", worker, "--size", _size_text(size), "--jobs",
                          str(job_file)], log)
        for plate in group:
            out = folder / f"{plate.id}.png"
            if ok and out.exists():
                done[plate.id] = keep(plate,out, {"tool_process": worker})
                say(f"{tool:<7} {plate.id}")
            else:
                failed[plate.id] = f"{tool} did not write this capture"

    # Composites, from their parts.
    for plate in [p for p in selected if p.tool == "composite"]:
        parts = [folder / f"{plate.id}__{number}.png" for number in range(len(plate.recipe["parts"]))]
        if all(part.exists() for part in parts):
            from PIL import Image
            images = [Image.open(part).convert("RGB") for part in parts]
            # Each part was shot full width with its subject centred; keep the
            # middle of each so the pair fills one plate.
            share = (plate.size[0] - 24 * (len(images) - 1)) // len(images)
            images = [image.crop(((image.width - share) // 2, 0,
                                  (image.width - share) // 2 + share, image.height))
                      for image in images]
            width = sum(image.width for image in images) + 24 * (len(images) - 1)
            height = max(image.height for image in images)
            sheet = Image.new("RGB", (width, height), (255, 255, 255))
            x = 0
            for image in images:
                sheet.paste(image, (x, 0))
                x += image.width + 24
            _label_parts(sheet, [image.width for image in images],
                         plate.recipe.get("labels", ()))
            out = folder / f"{plate.id}.png"
            sheet.save(out)
            done[plate.id] = keep(plate,out, {"parts": [str(p) for p in parts]})
            say(f"compose {plate.id}")
        else:
            failed[plate.id] = "a part of this composite was not rendered"

    report = {"rendered": {k: str(v) for k, v in done.items()}, "failed": failed,
              "log": "\n".join(log)[-12000:]}
    (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failed and verbose:
        print("FAILED:", json.dumps(failed, indent=2))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", default="")
    parser.add_argument("--tools", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--worker", default="")
    parser.add_argument("--size", default="2400x1500")
    parser.add_argument("--jobs", default="")
    parser.add_argument("--proof", action="store_true",
                        help="render into the work folder only; publish nothing")
    args = parser.parse_args(argv)
    width, height = (int(v) for v in args.size.lower().split("x"))
    if args.worker == "film":
        return film_worker([i for i in args.ids.split(",") if i], (width, height))
    if args.worker in ("forge", "line"):
        jobs = [tuple(job) for job in json.loads(Path(args.jobs).read_text(encoding="utf-8"))]
        worker = forge_worker if args.worker == "forge" else line_worker
        return worker(jobs, (width, height))
    report = render([i for i in args.ids.split(",") if i] or None,
                    [t for t in args.tools.split(",") if t] or None, args.force, args.proof)
    if args.proof:
        print(f"proofs in {WORK}")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
