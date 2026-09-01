"""EP_DOME_001, played by the renderer: the CNEE's output stage.

Everything about the episode -- who stands where, what they do, where
the camera is and when -- is decided by
:class:`~two_v_demo.drama_director.Director`.  This module only draws
what the director hands it, one beat per chapter, and gives the lesson
machinery the shape it expects so that the existing exporter, narration
and companion files all work unchanged.

Two things are worth knowing before reading further.

**It is shot vertically.**  Every camera comes from the drama camera
module in 9:16, so this lesson must be rendered at a vertical size --
1080x1920 -- or the framing the director computed will not be the
framing on screen.  :func:`validate_drama_lesson` refuses a landscape
frame rather than quietly letting it through.

**Dialogue is the narration.**  A beat's spoken line is the chapter's
narration, so the same synthesised voice track that carries a
masterclass carries the drama, and the subtitle file comes out right.
The chapter's headline is the beat name, which is what the montage
overlay puts on screen.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .drama_camera import EYE_LINE_FROM_TOP, eyeline_fraction
from .drama_director import Director, director_report
from .drama_face import draw_face, validate_drama_face
from .drama_rig import ACTIONS, attachment_point, validate_drama_rig
from .drama_script import (
    CAST,
    SERIES_LOGLINE,
    SERIES_TITLE,
    check_episode,
    check_series,
    example_episode,
    series,
    series_bible,
)
from .drama_stage import DOME_PRESETS, validate_drama_stage
from .figure import draw_figure
from .geometry import build_demo_geometry, normalize
from .lessons import Chapter, Lesson, prose
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    TriangleBatch,
    WorldLabel,
    clamp,
    project_point,
)


GEOMETRY = build_demo_geometry()
DIRECTOR = Director(example_episode())
PRESET = DOME_PRESETS[DIRECTOR.episode.dome_preset]

# One director per episode, and a flat running order over all of them.
# A chapter number indexes straight into this, which is what lets one
# painter serve a single episode and the whole season.
DIRECTORS = tuple(Director(episode) for episode in series())
EPISODE_TIMELINE = tuple((DIRECTOR, index)
                         for index in range(len(DIRECTOR.episode.beats)))
SERIES_TIMELINE = tuple(
    (director, index)
    for director in DIRECTORS
    for index in range(len(director.episode.beats))
)

# The set is drawn in metres, one world unit to the metre, because the
# director works in metres and a scale factor between the two is exactly
# the kind of thing that silently breaks a framing rule.
SET_RADIUS = PRESET.radius_m

# One colour per archetype, so a character reads instantly even in a
# fast cut.  Costume, not lighting: the lighting is the dome's.
CHARACTER_COLOURS: dict[str, dict] = {
    "CHAR_LEO": {"hi_vis": (0.88, 0.45, 0.12, 1.0),
                 "trousers": (0.17, 0.21, 0.33, 1.0),
                 "helmet": (0.22, 0.15, 0.10, 1.0)},
    "CHAR_AURELIA": {"hi_vis": (0.90, 0.90, 0.95, 1.0),
                     "trousers": (0.10, 0.10, 0.14, 1.0),
                     "helmet": (0.16, 0.10, 0.07, 1.0)},
    "CHAR_SILAS": {"hi_vis": (0.52, 0.55, 0.60, 1.0),
                   "trousers": (0.22, 0.22, 0.24, 1.0),
                   "helmet": (0.78, 0.78, 0.80, 1.0)},
    "CHAR_JAX": {"hi_vis": (0.24, 0.85, 0.66, 1.0),
                 "trousers": (0.12, 0.12, 0.16, 1.0),
                 "helmet": (0.10, 0.10, 0.12, 1.0)},
    "CHAR_BARON": {"hi_vis": (0.26, 0.28, 0.40, 1.0),
                   "trousers": (0.08, 0.08, 0.12, 1.0),
                   "helmet": (0.30, 0.30, 0.32, 1.0)},
}

BEAT_TINT: dict[str, tuple] = {
    "COLD_HOOK": RED,
    "ESCALATION": AMBER,
    "REVEAL": CYAN,
    "CLIFFHANGER": GREEN,
}


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _fade(colour, alpha: float):
    return (colour[0], colour[1], colour[2], clamp(alpha) * colour[3])


def _draw_shell(batch, radius: float, intensity: float) -> None:
    """The dome itself: struts, and the LED runs that back-light a face."""
    lit = DIRECTOR.rim_lights
    lit_edges = {(int(round(light.start[0] * 1e3)),
                  int(round(light.start[1] * 1e3))) for light in lit}
    for edge in GEOMETRY.hemisphere_edges:
        a = np.asarray(GEOMETRY.vertices[edge[0]], dtype=float) * radius
        b = np.asarray(GEOMETRY.vertices[edge[1]], dtype=float) * radius
        key = (int(round(a[0] * 1e3)), int(round(a[1] * 1e3)))
        if key in lit_edges:
            batch.cylinder(a, b, 0.105, _fade(CYAN, 0.55 + intensity * 0.45),
                           8)
        else:
            batch.cylinder(a, b, 0.075, (0.28, 0.33, 0.40, 1.0), 6)


def _draw_floor(batch, radius: float) -> None:
    """A deck to stand on, so the figures are not floating in a wireframe."""
    batch.disc(np.array([0.0, 0.0, 0.02]), radius * 0.98,
               (0.09, 0.11, 0.15, 1.0), 48)
    # A ring of deck lights, so the floor has an edge in a dark frame.
    for index in range(24):
        angle = math.tau * index / 24.0
        spot = np.array([math.cos(angle), math.sin(angle), 0.0])             * radius * 0.93
        batch.box(spot + np.array([0.0, 0.0, 0.06]),
                  np.array([0.22, 0.22, 0.05]), _fade(AMBER, 0.75))


def _draw_apex_shaft(batch, radius: float, intensity: float) -> None:
    """The light shaft the power position stands in."""
    top = np.array([0.0, 0.0, radius * 0.96])
    batch.cone(np.array([0.0, 0.0, 0.05]), top, radius * 0.20,
               _fade(WHITE, 0.05 + 0.05 * intensity))


def _draw_character(opaque, state) -> None:
    """One figure, in its costume colours, posed by the director."""
    colours = CHARACTER_COLOURS.get(state.character_id, {})
    draw_figure(opaque, state.joints, **colours)
    # The face last, so it sits on the front of the head sphere rather
    # than inside it.
    draw_face(opaque, state.joints, state.face)


def _draw_attachment(opaque, state, others) -> None:
    """The pin that holds a grab together, drawn where it really is."""
    if state.attached_to is None:
        return
    target_id, socket = state.attached_to
    target = others.get(target_id)
    if target is None:
        return
    point = attachment_point(target.joints, socket)
    for hand in ("l_grip", "r_grip"):
        opaque.cylinder(np.asarray(state.joints[hand], dtype=float), point,
                        0.02, _fade(RED, 0.8), 5)


def _resolve(timeline, app, chapter=None, progress: float = 0.0):
    """Which director, which beat, and what time inside it."""
    if chapter is None:
        chapters = getattr(app, "chapters", None)
        index = getattr(app, "chapter_index", 0)
        chapter = chapters[index] if chapters else None
    number = int(chapter.number) - 1 if chapter is not None else 0
    number = max(0, min(len(timeline) - 1, number))
    director, beat_index = timeline[number]
    beat = director.episode.beats[beat_index]
    return director, beat, beat.start_s + beat.duration_s * clamp(progress)


def _paint(timeline, app, opaque, transparent, p: float) -> None:
    """Draw whichever episode and beat this chapter belongs to."""
    director, beat, time_s = _resolve(timeline, app, None, p)
    state = director.state_at(time_s)

    _draw_floor(opaque, state.dome_radius_m)
    _draw_shell(opaque, state.dome_radius_m, state.rim_light_intensity)
    _draw_apex_shaft(transparent, state.dome_radius_m,
                     state.rim_light_intensity)

    for character in state.characters.values():
        _draw_character(opaque, character)
        _draw_attachment(opaque, character, state.characters)

    # A name tag on the speaker only, and only in the first breath of a
    # beat: this is a drama, not a diagram.
    if p < 0.22:
        speaker = state.characters.get(beat.camera.target_character)
        if speaker is not None:
            app.world_labels.append(WorldLabel(
                np.asarray(speaker.joints["head_top"], dtype=float)
                + np.array([0.0, 0.0, 0.28]),
                CAST[speaker.character_id].name.upper(),
                _rgb(BEAT_TINT.get(beat.dramatic_beat, WHITE))))


def scene_drama(app, opaque, transparent, p: float) -> None:
    """The single episode the specification ships."""
    _paint(EPISODE_TIMELINE, app, opaque, transparent, p)


def scene_series(app, opaque, transparent, p: float) -> None:
    """The whole mini-series, back to back."""
    _paint(SERIES_TIMELINE, app, opaque, transparent, p)


SCENES = {"drama": scene_drama, "series": scene_series}


def _camera(timeline, app, chapter, progress, width, height):
    director, _beat, time_s = _resolve(timeline, app, chapter, progress)
    state = director.state_at(time_s)
    return state.camera.eye, state.camera.target, state.camera.fov_deg


def drama_camera_fn(app, chapter, progress, width, height):
    """Hand the renderer the director's camera for this instant."""
    return _camera(EPISODE_TIMELINE, app, chapter, progress, width, height)


def series_camera_fn(app, chapter, progress, width, height):
    return _camera(SERIES_TIMELINE, app, chapter, progress, width, height)


def _chapters_for(timeline, with_episode_title: bool) -> tuple:
    """One chapter per beat, carrying the dialogue as its narration."""
    chapters = []
    for index, (director, beat_index) in enumerate(timeline):
        beat = director.episode.beats[beat_index]
        title = beat.dramatic_beat.replace("_", " ").title()
        if with_episode_title:
            title = f"{director.episode.title}: {title}"
        chapters.append(Chapter(
            slug=f"{director.episode.episode_id.lower()}_b{beat_index + 1}",
            number=f"{index + 1:02d}",
            title=title,
            promise=beat.dialogue,
            narration=prose((beat.dialogue,)),
            equations=(),
            duration=beat.duration_s,
            camera=(0.0, 20.0, 8.0),
            stage="series" if with_episode_title else "drama",
            overlay="hype",
        ))
    return tuple(chapters)


CHAPTERS = _chapters_for(EPISODE_TIMELINE, False)
SERIES_CHAPTERS = _chapters_for(SERIES_TIMELINE, True)


def validate_drama_lesson() -> None:
    """Prove the episode can be shot before anything is rendered."""
    validate_drama_rig()
    validate_drama_stage()
    validate_drama_face()

    problems = check_episode(DIRECTOR.episode)
    assert not problems, problems
    assert not check_series(), check_series()

    for lesson in (DRAMA_LESSON, SERIES_LESSON):
        lesson.validate()
        assert lesson.camera_fn is not None
    assert len(SERIES_LESSON.chapters) == sum(
        len(director.episode.beats) for director in DIRECTORS)

    # Every beat of every episode has to resolve, draw and frame -- the
    # season is six times as many ways to be wrong as one episode.
    class _SeriesApp:
        def __init__(self, chapters, index):
            self.chapters = chapters
            self.chapter_index = index
            self.world_labels = []

    for index, chapter in enumerate(SERIES_LESSON.chapters):
        for progress in (0.0, 0.5, 1.0):
            probe = _SeriesApp(SERIES_LESSON.chapters, index)
            opaque, transparent = TriangleBatch(), TriangleBatch()
            scene_series(probe, opaque, transparent, progress)
            assert len(opaque.vertices) > 30 * 500, (chapter.slug, progress)
            eye, target, fov = series_camera_fn(probe, chapter, progress,
                                                1080, 1920)
            assert 5.0 < float(fov) < 90.0, chapter.slug
            assert float(np.linalg.norm(np.asarray(eye)
                                        - np.asarray(target))) > 0.2

    lesson = DRAMA_LESSON
    lesson.validate()
    assert lesson.camera_fn is not None, "a drama directs its own camera"
    assert len(lesson.chapters) == len(DIRECTOR.episode.beats)
    for chapter, beat in zip(lesson.chapters, DIRECTOR.episode.beats):
        assert chapter.duration == beat.duration_s
        assert beat.dialogue in " ".join(chapter.narration)

    # The picture has to contain a dome and five limbs' worth of figure
    # at every instant of every beat, or a beat is playing to an empty
    # set somewhere in the middle.
    class _App:
        def __init__(self, chapters, index):
            self.chapters = chapters
            self.chapter_index = index
            self.world_labels = []

    for index, chapter in enumerate(lesson.chapters):
        for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
            app = _App(lesson.chapters, index)
            opaque, transparent = TriangleBatch(), TriangleBatch()
            scene_drama(app, opaque, transparent, progress)
            assert len(opaque.vertices) > 30 * 500, (index, progress)
            for label in app.world_labels:
                assert label.text.strip()

            # The camera the renderer would be given must be a real
            # camera, and must frame the beat's subject.
            eye, target, fov = drama_camera_fn(app, chapter, progress,
                                               1080, 1920)
            assert 5.0 < float(fov) < 90.0, fov
            assert float(np.linalg.norm(np.asarray(eye)
                                        - np.asarray(target))) > 0.2

    # What shooting vertically changes, precisely.  The renderer's
    # projection scales y by the focal term and x by focal/aspect, so
    # the *eye-line* is the same height on any frame shape -- it is the
    # horizontal crop that 9:16 buys, and that is what has to be
    # checked rather than assumed.
    beat = DIRECTOR.episode.beats[0]
    # Sampled before the push-in tightens: at the extreme close-up the
    # shoulders are outside the frame by design, which is the shot
    # working rather than a framing fault.
    state = DIRECTOR.state_at(beat.start_s + 0.10)
    subject = state.characters[beat.camera.target_character]
    tall = eyeline_fraction(state.camera, subject.eye, 1080, 1920)
    wide = eyeline_fraction(state.camera, subject.eye, 1920, 1080)
    assert abs(tall - EYE_LINE_FROM_TOP) < 0.05, tall
    assert abs(tall - wide) < 1e-6, "the eye-line does not depend on aspect"

    shoulders = (np.asarray(subject.joints["l_shoulder"], dtype=float),
                 np.asarray(subject.joints["r_shoulder"], dtype=float))
    spans = {}
    for width, height in ((1080, 1920), (1920, 1080)):
        _projection, _view, mvp = state.camera.matrices(width, height)
        edges = [project_point(mvp, point, width, height)
                 for point in shoulders]
        assert all(edge is not None for edge in edges), (width, height)
        spans[(width, height)] = abs(edges[0][0] - edges[1][0]) / width
    # The horizontal half-width of a frame is distance x tan(fov/2) x
    # aspect, so swapping 16:9 for 9:16 narrows it by (16/9) squared and
    # the same subject fills that much more of the width.  This is the
    # whole reason to shoot vertically, so it is measured.
    ratio = spans[(1080, 1920)] / spans[(1920, 1080)]
    assert abs(ratio - (16.0 / 9.0) ** 2) < 0.05, ratio
    assert spans[(1080, 1920)] > spans[(1920, 1080)]

    # Nobody may be standing outside the shell they are lit by.
    for time_s in [index * 0.5 for index in range(0, 121)]:
        state = DIRECTOR.state_at(time_s)
        for character in state.characters.values():
            reach = float(np.linalg.norm(character.spot[:2]))
            assert reach < state.dome_radius_m * 0.95, (time_s, reach)

    # A grab, if the episode has one, must pin to the other character.
    for time_s in [index * 0.25 for index in range(0, 241)]:
        state = DIRECTOR.state_at(time_s)
        for character in state.characters.values():
            if character.rig.action_id != "RIG_GRAB_LAPEL":
                continue
            assert character.attached_to is not None
            other = state.characters[character.attached_to[0]]
            reach = float(np.linalg.norm(
                attachment_point(other.joints, character.attached_to[1])
                - np.asarray(character.joints["r_grip"], dtype=float)))
            assert reach < 1.0, reach


SERIES_LESSON = Lesson(
    key="series",
    brand=f"{SERIES_TITLE} / SIX EPISODES",
    title=f"{SERIES_TITLE}: the complete mini-series",
    chapters=SERIES_CHAPTERS,
    scenes=SCENES,
    selftest=validate_drama_lesson,
    report=series_bible,
    snapshot_prefix="series",
    style="hype",
    camera_fn=series_camera_fn,
    label_layout="declutter",
)


DRAMA_LESSON = Lesson(
    key="drama",
    brand="DOME DRAMA / EP_DOME_001",
    title="EP_DOME_001: The High Council Dome",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_drama_lesson,
    report=director_report,
    snapshot_prefix="drama",
    style="hype",
    camera_fn=drama_camera_fn,
    label_layout="declutter",
)
