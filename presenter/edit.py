"""Editing operations on a presentation document.

A :class:`~presenter.script.Presentation` is deliberately immutable --
tuples all the way down -- so that the engine can trust that the frame it
renders at time *t* is the same frame it rendered last time. That is
exactly the property you want for export, and exactly the property that
makes editing awkward.

This module is the bridge: every function here takes a presentation and
returns a **new** presentation with one change applied. The editor calls
them; nothing here touches pygame or OpenGL, so all of it is testable
without a display.

Indices come in two flavours, matching how the editor talks about them:

* a *scene index* counts scenes,
* a *flat shot index* counts shots across the whole timeline, which is
  what the timeline ruler and the playhead use.
"""

from __future__ import annotations

from dataclasses import replace

from .library import defaults_for, clamp_param
from .script import LENSES, OverlayPanel, Presentation, Scene, Shot

MIN_DURATION = 0.6      # script.validate() insists shots last > 0.5 s


# ---------------------------------------------------------------------------
# Starting from nothing
# ---------------------------------------------------------------------------

def blank_shot(index: int = 1) -> Shot:
    """A shot with no narration and no caption: an empty piece of film."""
    return Shot(slug=f"shot{index}", duration=6.0, lens="wide",
                perspective=3, focus="", orbit=12.0, yaw=-55.0, pitch=18.0)


def blank_scene(index: int = 1) -> Scene:
    return Scene(slug=f"scene{index}", title=f"Scene {index}",
                 environment="", shots=(blank_shot(1),), world=())


def blank_presentation(title: str = "Untitled") -> Presentation:
    """An empty project: one scene, one shot, nothing on the stage.

    This is the starting point for composing from scratch, as opposed to
    opening one of the built-in demos."""
    return Presentation(title=title, scenes=(blank_scene(1),))


# ---------------------------------------------------------------------------
# Locating things
# ---------------------------------------------------------------------------

def locate(pres: Presentation, flat: int) -> tuple[int, int]:
    """(scene index, shot index within that scene) for a flat shot index."""
    cursor = 0
    for si, scene in enumerate(pres.scenes):
        if flat < cursor + len(scene.shots):
            return si, flat - cursor
        cursor += len(scene.shots)
    last = len(pres.scenes) - 1
    return last, max(0, len(pres.scenes[last].shots) - 1)


def flat_index(pres: Presentation, scene_i: int, shot_i: int) -> int:
    return sum(len(s.shots) for s in pres.scenes[:scene_i]) + shot_i


def shot_count(pres: Presentation) -> int:
    return sum(len(s.shots) for s in pres.scenes)


def _rebuilt(pres: Presentation, scenes) -> Presentation:
    return replace(pres, scenes=tuple(scenes))


def _with_shots(scene: Scene, shots) -> Scene:
    return replace(scene, shots=tuple(shots))


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def add_scene(pres: Presentation, after: int | None = None) -> Presentation:
    scenes = list(pres.scenes)
    index = len(scenes) if after is None else max(0, min(after + 1,
                                                        len(scenes)))
    scenes.insert(index, blank_scene(len(scenes) + 1))
    return _rebuilt(pres, scenes)


def delete_scene(pres: Presentation, scene_i: int) -> Presentation:
    """Remove a scene. The last one is never removed -- a presentation
    with no scenes cannot be validated, previewed, or exported."""
    if len(pres.scenes) <= 1 or not 0 <= scene_i < len(pres.scenes):
        return pres
    scenes = list(pres.scenes)
    scenes.pop(scene_i)
    return _rebuilt(pres, scenes)


def move_scene(pres: Presentation, scene_i: int, delta: int) -> Presentation:
    scenes = list(pres.scenes)
    target = scene_i + delta
    if not (0 <= scene_i < len(scenes) and 0 <= target < len(scenes)):
        return pres
    scenes.insert(target, scenes.pop(scene_i))
    return _rebuilt(pres, scenes)


def set_scene(pres: Presentation, scene_i: int, **fields) -> Presentation:
    if not 0 <= scene_i < len(pres.scenes):
        return pres
    scenes = list(pres.scenes)
    scenes[scene_i] = replace(scenes[scene_i], **fields)
    return _rebuilt(pres, scenes)


# ---------------------------------------------------------------------------
# Shots
# ---------------------------------------------------------------------------

def add_shot(pres: Presentation, flat: int | None = None) -> Presentation:
    """Insert a fresh shot straight after ``flat`` (or at the very end)."""
    if not pres.scenes:
        return pres
    if flat is None:
        scene_i = len(pres.scenes) - 1
        shot_i = len(pres.scenes[scene_i].shots)
    else:
        scene_i, shot_i = locate(pres, flat)
        shot_i += 1
    scenes = list(pres.scenes)
    shots = list(scenes[scene_i].shots)
    shots.insert(shot_i, blank_shot(len(shots) + 1))
    scenes[scene_i] = _with_shots(scenes[scene_i], shots)
    return _rebuilt(pres, scenes)


def duplicate_shot(pres: Presentation, flat: int) -> Presentation:
    """Copy a shot in place -- the quickest way to build a sequence that
    varies one thing at a time."""
    if not 0 <= flat < shot_count(pres):
        return pres
    scene_i, shot_i = locate(pres, flat)
    scenes = list(pres.scenes)
    shots = list(scenes[scene_i].shots)
    original = shots[shot_i]
    shots.insert(shot_i + 1, replace(original, slug=f"{original.slug}_copy"))
    scenes[scene_i] = _with_shots(scenes[scene_i], shots)
    return _rebuilt(pres, scenes)


def delete_shot(pres: Presentation, flat: int) -> Presentation:
    """Remove a shot, and the scene with it if that was its last shot --
    unless it is the only shot left in the whole presentation."""
    if shot_count(pres) <= 1 or not 0 <= flat < shot_count(pres):
        return pres
    scene_i, shot_i = locate(pres, flat)
    scenes = list(pres.scenes)
    shots = list(scenes[scene_i].shots)
    shots.pop(shot_i)
    if shots:
        scenes[scene_i] = _with_shots(scenes[scene_i], shots)
    else:
        scenes.pop(scene_i)
    return _rebuilt(pres, scenes)


def move_shot(pres: Presentation, flat: int, target: int) -> Presentation:
    """Drag a shot to another slot on the timeline.

    The shot keeps everything about itself and simply lands in a new
    place, possibly in a different scene -- which is what dragging a clip
    past a scene boundary should do."""
    total = shot_count(pres)
    if not (0 <= flat < total) or not (0 <= target < total) or flat == target:
        return pres
    scene_i, shot_i = locate(pres, flat)
    moving = pres.scenes[scene_i].shots[shot_i]
    trimmed = delete_shot_forced(pres, flat)
    remaining = shot_count(trimmed)
    # Dropping it back in at position ``target`` of the shortened timeline
    # is what leaves it sitting at ``target`` of the finished one.
    if target >= remaining:
        dest_scene = len(trimmed.scenes) - 1
        dest_shot = len(trimmed.scenes[dest_scene].shots)
    else:
        dest_scene, dest_shot = locate(trimmed, target)
    scenes = list(trimmed.scenes)
    shots = list(scenes[dest_scene].shots)
    shots.insert(dest_shot, moving)
    scenes[dest_scene] = _with_shots(scenes[dest_scene], shots)
    return _rebuilt(trimmed, scenes)


def delete_shot_forced(pres: Presentation, flat: int) -> Presentation:
    """Remove a shot even if it is the last one, keeping any emptied scene
    only when other scenes remain. Used by :func:`move_shot`, which puts
    the shot straight back somewhere else."""
    scene_i, shot_i = locate(pres, flat)
    scenes = list(pres.scenes)
    shots = list(scenes[scene_i].shots)
    if not shots:
        return pres
    shots.pop(shot_i)
    if shots or len(scenes) == 1:
        scenes[scene_i] = _with_shots(scenes[scene_i], shots)
    else:
        scenes.pop(scene_i)
    return _rebuilt(pres, scenes)


def set_shot(pres: Presentation, flat: int, **fields) -> Presentation:
    """Change one or more of a shot's own settings."""
    if not 0 <= flat < shot_count(pres):
        return pres
    if "duration" in fields:
        fields["duration"] = max(MIN_DURATION, float(fields["duration"]))
    if "lens" in fields and fields["lens"] not in LENSES:
        fields.pop("lens")
    if "perspective" in fields:
        fields["perspective"] = max(1, min(6, int(fields["perspective"])))
    scene_i, shot_i = locate(pres, flat)
    scenes = list(pres.scenes)
    shots = list(scenes[scene_i].shots)
    shots[shot_i] = replace(shots[shot_i], **fields)
    scenes[scene_i] = _with_shots(scenes[scene_i], shots)
    return _rebuilt(pres, scenes)


def nudge_duration(pres: Presentation, flat: int,
                   delta: float) -> Presentation:
    """Trim or extend a clip by dragging its edge."""
    if not 0 <= flat < shot_count(pres):
        return pres
    scene_i, shot_i = locate(pres, flat)
    current = pres.scenes[scene_i].shots[shot_i].duration
    return set_shot(pres, flat, duration=current + delta)


def set_narration(pres: Presentation, flat: int, text: str) -> Presentation:
    """Set the words spoken over a shot.

    Blank lines are dropped, so clearing the box really does mean silence
    over this shot rather than an empty utterance."""
    lines = tuple(line.strip() for line in str(text).splitlines()
                  if line.strip())
    return set_shot(pres, flat, narration=lines)


def set_panel(pres: Presentation, flat: int,
              panel: OverlayPanel | None) -> Presentation:
    return set_shot(pres, flat, panel=panel)


# ---------------------------------------------------------------------------
# Animation: a parameter moving across a shot
# ---------------------------------------------------------------------------

def set_action(pres: Presentation, flat: int, obj: str, param: str,
               value_from: float, value_to: float) -> Presentation:
    """Animate one object parameter from one value to another across the
    shot -- a door swinging open, a wall building up, a tank filling."""
    if not 0 <= flat < shot_count(pres):
        return pres
    scene_i, shot_i = locate(pres, flat)
    shot = pres.scenes[scene_i].shots[shot_i]
    actions = [a for a in shot.actions if not (a[0] == obj and a[1] == param)]
    actions.append((obj, param, float(value_from), float(value_to)))
    return set_shot(pres, flat, actions=tuple(actions))


def clear_action(pres: Presentation, flat: int, obj: str,
                 param: str) -> Presentation:
    if not 0 <= flat < shot_count(pres):
        return pres
    scene_i, shot_i = locate(pres, flat)
    shot = pres.scenes[scene_i].shots[shot_i]
    actions = tuple(a for a in shot.actions
                    if not (a[0] == obj and a[1] == param))
    return set_shot(pres, flat, actions=actions)


# ---------------------------------------------------------------------------
# The stage: objects in a scene
# ---------------------------------------------------------------------------

def add_object(pres: Presentation, scene_i: int, key: str) -> Presentation:
    """Put a library object on a scene's stage, with its default knobs."""
    if not 0 <= scene_i < len(pres.scenes):
        return pres
    world = list(pres.scenes[scene_i].world)
    world.append((key, defaults_for(key)))
    return set_scene(pres, scene_i, world=tuple(world))


def remove_object(pres: Presentation, scene_i: int,
                  obj_i: int) -> Presentation:
    if not 0 <= scene_i < len(pres.scenes):
        return pres
    world = list(pres.scenes[scene_i].world)
    if not 0 <= obj_i < len(world):
        return pres
    world.pop(obj_i)
    return set_scene(pres, scene_i, world=tuple(world))


def move_object(pres: Presentation, scene_i: int, obj_i: int,
                delta: int) -> Presentation:
    """Reorder the stage. Later objects draw over earlier ones, which
    matters for anything see-through."""
    if not 0 <= scene_i < len(pres.scenes):
        return pres
    world = list(pres.scenes[scene_i].world)
    target = obj_i + delta
    if not (0 <= obj_i < len(world) and 0 <= target < len(world)):
        return pres
    world.insert(target, world.pop(obj_i))
    return set_scene(pres, scene_i, world=tuple(world))


def set_object_param(pres: Presentation, scene_i: int, obj_i: int,
                     param: str, value) -> Presentation:
    """Change one knob on one placed object, clamped to what that object
    actually accepts."""
    if not 0 <= scene_i < len(pres.scenes):
        return pres
    world = list(pres.scenes[scene_i].world)
    if not 0 <= obj_i < len(world):
        return pres
    key, params = world[obj_i]
    merged = dict(params)
    merged[param] = clamp_param(key, param, value)
    world[obj_i] = (key, merged)
    return set_scene(pres, scene_i, world=tuple(world))


def copy_stage(pres: Presentation, from_scene: int,
               to_scene: int) -> Presentation:
    """Reuse one scene's stage in another, so a sequence of scenes can
    share a set without rebuilding it by hand."""
    if not (0 <= from_scene < len(pres.scenes)
            and 0 <= to_scene < len(pres.scenes)):
        return pres
    source = tuple((k, dict(v)) for k, v in pres.scenes[from_scene].world)
    return set_scene(pres, to_scene, world=source)
