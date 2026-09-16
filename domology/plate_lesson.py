"""The book's film and scene plates, as one lesson the film engine can shoot.

Each plate becomes one ten-second chapter. A borrowed plate keeps its source
chapter's slug (scenes look their state up by slug), its scene painter and its
camera, wears the engine's clean ``plate`` style instead of the film's
headline and cards, and then gets whatever the recipe adds. The render runner
shoots one frame per chapter at the recipe's progress.
"""

from __future__ import annotations

import math

import numpy as np

from two_v_demo.lessons import Chapter, Lesson
from two_v_demo.render_kit import WorldLabel

from . import plate_scenes
from .markup import Resolver
from .plates import Plate

DURATION = 10.0
KEY = "domology_plates"


def _orbit(target, yaw_deg: float, pitch_deg: float, distance: float) -> np.ndarray:
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    return np.asarray(target, dtype=float) + distance * np.array([
        math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])


def _camera(plate: Plate, source_lesson, source_chapter, app, progress, width, height):
    recipe = plate.recipe
    adjust = recipe.get("camera", {}) or {}
    if "fn" in adjust:
        options = {key: value for key, value in adjust.items() if key != "fn"}
        return plate_scenes.CAMERAS[adjust["fn"]](app, source_chapter, progress, width, height,
                                                  **options)
    if "eye" in adjust:
        return (np.array(adjust["eye"], float), np.array(adjust["target"], float),
                float(adjust.get("fov", 44.0)))
    if source_lesson is not None and source_lesson.camera_fn is not None:
        eye, target, fov = source_lesson.camera_fn(app, source_chapter, progress, width, height)
        eye, target = np.asarray(eye, float), np.asarray(target, float)
    else:
        yaw, pitch, distance = source_chapter.camera if source_chapter else (90.0, 20.0, 20.0)
        pitch = min(78.0, max(8.0, pitch))
        target = np.array([0.0, 0.0, 2.25])
        eye = _orbit(target, yaw, pitch, distance)
        fov = 48.0
    if adjust:
        offset = eye - target
        distance = float(np.linalg.norm(offset))
        yaw = math.degrees(math.atan2(offset[1], offset[0])) + adjust.get("yaw", 0.0)
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, offset[2] / distance))))
        pitch = adjust.get("pitch", pitch + adjust.get("tilt", 0.0))
        distance *= adjust.get("zoom", 1.0)
        target = target + np.array(adjust.get("shift", (0.0, 0.0, 0.0)), float)
        eye = _orbit(target, yaw, pitch, distance)
        fov = adjust.get("fov", fov)
    return eye, target, fov


def _painter(plate: Plate, source_lesson, source_chapter, resolver: Resolver):
    recipe = plate.recipe
    extra = plate_scenes.EXTRAS.get(recipe.get("extra") or recipe.get("scene") or "")
    labels = [(np.array(point, float), plate_scenes.resolve_text(text, resolver), tuple(colour))
              for point, text, colour in recipe.get("labels", ())]

    def paint(app, opaque, transparent, p):
        if source_chapter is not None:
            painter = source_lesson.scenes.get(source_chapter.stage)
            if painter is not None:
                painter(app, opaque, transparent, p)
            else:
                getattr(app, f"scene_{source_chapter.stage}")(opaque, transparent, p)
        if recipe.get("hide_labels"):
            app.world_labels.clear()
        for point, text, colour in labels:
            app.world_labels.append(WorldLabel(point, text, colour))
        if extra is not None:
            extra(app, opaque, transparent, p, recipe, resolver)
    return paint


def build(plates: list[Plate]) -> tuple[Lesson, list[float]]:
    from two_v_demo.lesson_registry import LESSONS
    resolver = Resolver(strict=True)
    chapters, scenes, sources, times = [], {}, {}, []
    for index, plate in enumerate(plates):
        recipe = plate.recipe
        source_lesson = source_chapter = None
        if plate.tool == "film":
            source_lesson = LESSONS[recipe["lesson"]]
            source_chapter = next(c for c in source_lesson.chapters if c.slug == recipe["chapter"])
        stage = f"dm_plate_{index:03d}"
        number = f"{index + 1:03d}"
        scenes[stage] = _painter(plate, source_lesson, source_chapter, resolver)
        keep = bool(recipe.get("keep_overlay")) and source_chapter is not None
        chapters.append(Chapter(
            slug=source_chapter.slug if source_chapter else plate.id,
            number=number, title=plate.title, promise="", narration=(plate.title,),
            equations=source_chapter.equations if keep else (),
            duration=DURATION,
            camera=source_chapter.camera if source_chapter else (90.0, 20.0, 20.0),
            stage=stage, overlay=(source_chapter.overlay or "plate") if keep else "plate",
            callouts=()))
        sources[number] = (plate, source_lesson, source_chapter)
        progress = min(0.985, max(0.0, float(recipe.get("progress", 0.6))))
        times.append(round(index * DURATION + progress * DURATION, 2))

    def camera(app, chapter, progress, width, height):
        plate, source_lesson, source_chapter = sources[chapter.number]
        return _camera(plate, source_lesson, source_chapter, app, progress, width, height)

    lesson = Lesson(key=KEY, brand="DOMOLOGY", title="Domology plates",
                    chapters=tuple(chapters), scenes=scenes, snapshot_prefix="plate",
                    style="plate", camera_fn=camera, label_layout="declutter",
                    frame_fit="off")
    return lesson, times
