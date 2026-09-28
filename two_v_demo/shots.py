"""Cinematic camera moves, as functions a lesson can use.

A lesson that sets ``camera_fn`` directs its own camera: the engine calls it
with the chapter and its progress (0..1) and gets back ``(eye, target, fov)``.
Films here mostly orbited. These are the moves a cinematographer reaches for
first, each one a function of progress, eased, and composable per chapter:

========================  ====================================================
``orbit``                 circle the subject -- the default establishing move
``crane_reveal``          start low and close, rise and pull back to show all
``push_in``               move toward a detail while narrowing the lens
``dolly_zoom``            pull back while zooming in: the subject holds its
                          size and the world behind it swells (the "Vertigo")
``low_hero``              a slow arc from near the ground, looking up
``fly_through``           a smooth path through a list of points
``top_down_spin``         straight down, turning: the plan, made alive
``hold``                  a locked-off frame, for a line that needs stillness
========================  ====================================================

``by_chapter`` turns a ``{chapter slug: shot}`` table into a lesson
``camera_fn``, so a film can say "this chapter is a crane reveal" in one line.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np

Shot = Callable[[float], tuple[np.ndarray, np.ndarray, float]]


def ease(p: float) -> float:
    """Smooth start and stop: a camera operator's hands, not a motor."""
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def _v(x) -> np.ndarray:
    return np.asarray(x, dtype=np.float64)


def orbit(target, radius: float, height: float, start_deg: float = -90.0,
          sweep_deg: float = 40.0, fov: float = 42.0) -> Shot:
    """Circle the target at a fixed radius and height, sweeping ``sweep_deg``."""
    target = _v(target)

    def shot(p: float):
        a = math.radians(start_deg + sweep_deg * ease(p))
        eye = target + np.array([radius * math.cos(a), radius * math.sin(a), height])
        return eye, target, fov
    return shot


def crane_reveal(target, start_eye, end_eye, fov_start: float = 34.0,
                 fov_end: float = 48.0, look_start=None) -> Shot:
    """Rise and pull back. ``look_start`` lets the first frame hold on a
    detail (a log's end grain) before the reveal lifts to ``target``."""
    target, a, b = _v(target), _v(start_eye), _v(end_eye)
    look0 = _v(look_start) if look_start is not None else target

    def shot(p: float):
        t = ease(p)
        return a + (b - a) * t, look0 + (target - look0) * t, fov_start + (fov_end - fov_start) * t
    return shot


def push_in(target, start_eye, end_eye, fov_start: float = 46.0, fov_end: float = 30.0) -> Shot:
    """Move from ``start_eye`` to ``end_eye`` toward a fixed target, the lens tightening."""
    target, a, b = _v(target), _v(start_eye), _v(end_eye)

    def shot(p: float):
        t = ease(p)
        return a + (b - a) * t, target, fov_start + (fov_end - fov_start) * t
    return shot


def dolly_zoom(target, direction, start_distance: float, end_distance: float,
               subject_width: float, height: float = 0.0) -> Shot:
    """Distance changes, framing of the subject does not.

    The lens is solved each frame so ``subject_width`` always fills the same
    share of the frame: fov = 2 atan(w / 2d) scaled to the start framing.
    """
    target = _v(target)
    d = _v(direction) / np.linalg.norm(direction)
    fill = 0.62  # the subject spans this share of the frame height

    def fov_for(distance: float) -> float:
        return math.degrees(2 * math.atan(subject_width / (2 * distance * fill)))

    def shot(p: float):
        dist = start_distance + (end_distance - start_distance) * ease(p)
        eye = target - d * dist + np.array([0.0, 0.0, height])
        return eye, target, fov_for(dist)
    return shot


def low_hero(target, radius: float, eye_height: float = 0.35, start_deg: float = -120.0,
             sweep_deg: float = 25.0, look_up: float = 1.2, fov: float = 50.0) -> Shot:
    """A low camera circling slowly and looking up at the subject: it makes it monumental."""
    target = _v(target)

    def shot(p: float):
        a = math.radians(start_deg + sweep_deg * ease(p))
        eye = np.array([target[0] + radius * math.cos(a), target[1] + radius * math.sin(a), eye_height])
        return eye, target + np.array([0.0, 0.0, look_up]), fov
    return shot


def _catmull(points: Sequence[np.ndarray], t: float) -> np.ndarray:
    n = len(points) - 1
    seg = min(n - 1, int(t * n))
    u = t * n - seg
    p0 = points[max(seg - 1, 0)]
    p1, p2 = points[seg], points[seg + 1]
    p3 = points[min(seg + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def fly_through(eye_points, look_points, fov: float = 52.0) -> Shot:
    """A smooth spline through the eye points, looking along the look points."""
    eyes = [_v(p) for p in eye_points]
    looks = [_v(p) for p in look_points]
    assert len(eyes) >= 2 and len(looks) >= 2

    def shot(p: float):
        t = ease(p)
        return _catmull(eyes, t), _catmull(looks, t), fov
    return shot


def top_down_spin(target, height: float, turns_deg: float = 60.0, fov: float = 50.0) -> Shot:
    """Straight down from ``height``, turning ``turns_deg``: the plan view."""
    target = _v(target)

    def shot(p: float):
        a = math.radians(turns_deg * ease(p))
        # A hair off vertical so look_at keeps a defined up vector; the
        # offset turns, so the plan rotates under the camera.
        eye = target + np.array([0.02 * math.cos(a), 0.02 * math.sin(a), height])
        return eye, target, fov
    return shot


def hold(eye, target, fov: float = 42.0) -> Shot:
    """A locked-off camera."""
    eye, target = _v(eye), _v(target)
    return lambda p: (eye, target, fov)


HOUSE_FOV = 48.0
"""The masterclass renderer's own lens (``perspective(48.0, ...)`` in app.render)."""


def by_chapter(table: dict[str, Shot], default: Shot | None = None):
    """A lesson ``camera_fn`` from ``{chapter slug: shot}``.

    A chapter the table does not name -- a call-to-action or outro segment the
    exporter splices in -- gets the renderer's own house camera, the one those
    segments were composed for, rather than stopping a render an hour in.
    """
    def camera_fn(app, chapter, progress: float, width: int, height: int):
        shot = table.get(getattr(chapter, "slug", ""), default)
        if shot is None:
            eye, target = app.camera()
            return eye, target, HOUSE_FOV
        return shot(progress)
    return camera_fn


def validate_shots() -> None:
    """Every move starts and ends where it says, and the dolly zoom holds its subject."""
    o = orbit((0, 0, 1), 10, 2, -90, 90)
    e0, _, _ = o(0.0)
    e1, _, _ = o(1.0)
    assert np.allclose(e0, [0, -10, 3]) and np.allclose(e1, [10, 0, 3], atol=1e-9)
    dz = dolly_zoom((0, 0, 1), (0, 1, 0), 6.0, 14.0, subject_width=5.0)
    for p in (0.0, 0.5, 1.0):
        eye, target, fov = dz(p)
        dist = np.linalg.norm(target - eye)
        frame_height = 2 * dist * math.tan(math.radians(fov) / 2)
        assert abs(5.0 / frame_height - 0.62) < 1e-9, "dolly zoom lost its subject"
    ft = fly_through([(0, -10, 2), (3, -6, 3), (0, -3, 4)], [(0, 0, 1), (0, 0, 2)])
    assert np.allclose(ft(0)[0], [0, -10, 2]) and np.allclose(ft(1)[0], [0, -3, 4])
    assert ease(0) == 0 and ease(1) == 1 and ease(0.5) == 0.5


if __name__ == "__main__":
    validate_shots()
    print("shots: ok")
