"""Frames: one film, any shape of screen.

Every film in this package was composed for one frame -- almost all of them for
a 16:9 screen, the micro-dramas for a 9:16 phone -- and a film shown in the
other shape is not the film that was written unless something re-composes it.
This module is that something, and it works in two layers.

**The scene is fitted, not cropped.** After a scene is painted, the renderer
knows exactly where every triangle of the subject is. :func:`fit_camera`
projects them through the film's own camera, measures what the subject covers,
and then -- only if it no longer fits the part of the frame the overlays leave
free -- dollies the camera back along its own line of sight, finishes with a
slightly wider lens if the dolly is capped, and shifts the lens so the subject
sits in the middle of the free space. It never zooms *in* past the composed
framing, so a film is never re-directed, only given room.

**Everything else is resolved.** Headlines, cards, worksheets, callouts and
labels are boxes with priorities. :func:`resolve` settles them step by step:
it *pushes* every box inside the safe area, *shoves* the lower-priority box of
any overlapping pair out of the way along the shorter route, *elongates* a text
box that is too wide by re-wrapping it narrower and taller, and *compresses* a
box that still cannot fit toward its minimum scale. Every step is logged, so a
still that looks wrong can say why.

A frame the film was composed for is left exactly alone: :attr:`Frame.adapted`
is false, and the renderer takes its original path, which is what keeps every
published film re-rendering byte for byte.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

import numpy as np

from .render_kit import look_at, perspective

LANDSCAPE_SIZE = (1920, 1080)
PORTRAIT_SIZE = (1080, 1920)
ORIENTATIONS = ("landscape", "portrait")

# Where a phone's own interface sits over a vertical video: the status and
# title bar at the top, captions and the like/comment rail at the bottom and
# right. Type and faces kept out of these survive every platform.
PORTRAIT_SAFE = (0.06, 0.075, 0.12, 0.16)
"""Left, top, right and bottom insets as fractions of the frame."""
LANDSCAPE_SAFE = (0.02, 0.03, 0.02, 0.03)


def design_aspect(lesson_key: str) -> float:
    """The shape a film was composed for: 9:16 for the vertical films."""
    from .beats import VERTICAL
    key = lesson_key[len("teaser_"):] if lesson_key.startswith("teaser_") else lesson_key
    return 9.0 / 16.0 if key in VERTICAL else 16.0 / 9.0


def size_for(orientation: str) -> tuple[int, int]:
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation must be one of {ORIENTATIONS}, not {orientation!r}")
    return PORTRAIT_SIZE if orientation == "portrait" else LANDSCAPE_SIZE


# ----------------------------------------------------------------------
# The frame
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def centre(self) -> tuple[float, float]:
        return self.x + self.w / 2.0, self.y + self.h / 2.0

    def as_int(self) -> tuple[int, int, int, int]:
        return int(round(self.x)), int(round(self.y)), int(round(self.w)), int(round(self.h))


@dataclass(frozen=True)
class Frame:
    """A screen of one shape, and the shape the film was composed for."""

    width: int
    height: int
    design: float = 16.0 / 9.0

    @property
    def aspect(self) -> float:
        return self.width / max(1, self.height)

    @property
    def portrait(self) -> bool:
        return self.aspect < 0.9

    @property
    def orientation(self) -> str:
        return "portrait" if self.portrait else "landscape"

    @property
    def adapted(self) -> bool:
        """Whether this frame differs from the composed one enough to re-fit.

        Within five per cent of the composed shape a film plays exactly as
        composed: 1600x900 and 1920x1080 are the same film.
        """
        return abs(math.log(self.aspect / self.design)) > 0.05

    @property
    def narrower(self) -> bool:
        """Whether this screen is narrower than the composed one.

        Only that case needs the scene re-fitted. A wider screen at the film's own
        vertical lens shows everything the composed frame showed and more at the
        sides, so a vertical film on a wide screen is left exactly as directed.
        """
        return self.aspect < self.design / 1.05

    @property
    def unit(self) -> float:
        """Type scale for a vertical layout: 1.0 on a 1080-wide phone frame."""
        return self.width / 1080.0

    def safe(self) -> Rect:
        left, top, right, bottom = PORTRAIT_SAFE if self.portrait else LANDSCAPE_SAFE
        return Rect(self.width * left, self.height * top,
                    self.width * (1.0 - left - right), self.height * (1.0 - top - bottom))


# ----------------------------------------------------------------------
# Boxes and the resolver
# ----------------------------------------------------------------------

@dataclass
class Box:
    """One thing on screen that needs room: a label, a card, a callout."""

    key: str
    x: float
    y: float
    w: float
    h: float
    priority: int = 0
    """Higher keeps its place; lower gets shoved."""
    movable: bool = True
    scale: float = 1.0
    min_scale: float = 0.6
    axis: str = "y"
    """The direction it prefers to be shoved in."""
    reflow: Callable[[float], float] | None = None
    """For text: the height it needs at a given width, so it can elongate."""
    min_w: float = 0.0

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def overlap(self, other: "Box") -> tuple[float, float]:
        return (min(self.right, other.right) - max(self.x, other.x),
                min(self.bottom, other.bottom) - max(self.y, other.y))


@dataclass
class Resolution:
    boxes: list[Box]
    steps: list[str] = field(default_factory=list)
    unresolved: list[tuple[str, str]] = field(default_factory=list)


def _push(box: Box, bounds: Rect, steps: list[str]) -> None:
    """Move a box inside the bounds, compressing it first if it is simply too big."""
    if box.w > bounds.w or box.h > bounds.h:
        if box.reflow is not None and box.w > bounds.w:
            new_w = max(box.min_w, bounds.w)
            new_h = box.reflow(new_w)
            steps.append(f"elongate {box.key}: {box.w:.0f}x{box.h:.0f} -> {new_w:.0f}x{new_h:.0f}")
            box.w, box.h = new_w, new_h
        if box.w > bounds.w or box.h > bounds.h:
            factor = max(box.min_scale / box.scale,
                         min(bounds.w / box.w, bounds.h / box.h))
            if factor < 1.0:
                steps.append(f"compress {box.key} to fit the frame: x{factor:.2f}")
                box.w, box.h, box.scale = box.w * factor, box.h * factor, box.scale * factor
    x = min(max(box.x, bounds.x), bounds.right - box.w)
    y = min(max(box.y, bounds.y), bounds.bottom - box.h)
    if abs(x - box.x) > 0.5 or abs(y - box.y) > 0.5:
        steps.append(f"push {box.key} inside: ({box.x:.0f},{box.y:.0f}) -> ({x:.0f},{y:.0f})")
    box.x, box.y = x, y


def _fits(box: Box, bounds: Rect) -> bool:
    return (box.x >= bounds.x - 0.5 and box.y >= bounds.y - 0.5
            and box.right <= bounds.right + 0.5 and box.bottom <= bounds.bottom + 0.5)


def _clear(box: Box, others: Iterable[Box], gap: float) -> bool:
    for other in others:
        ox, oy = box.overlap(other)
        if ox > -gap and oy > -gap:
            return False
    return True


def resolve(boxes: Sequence[Box], bounds: Rect, gap: float = 6.0,
            rounds: int = 36) -> Resolution:
    """Settle boxes step by step: push, shove, elongate, compress.

    Boxes are handled in priority order. For each overlapping pair the lower
    one moves: first along its preferred axis, the shorter way, then along the
    other; the first move that keeps it inside the bounds and clear of every
    box already settled wins. A box with nowhere to go is elongated if it is
    text, then compressed toward its minimum scale, and tried again.
    """
    result = Resolution(list(boxes))
    steps = result.steps
    for box in result.boxes:
        _push(box, bounds, steps)
    order = sorted(result.boxes, key=lambda item: -item.priority)
    settled: list[Box] = []
    for box in order:
        if not box.movable or _clear(box, settled, gap):
            settled.append(box)
            continue
        placed = False
        for _attempt in range(rounds):
            candidates = []
            for other in settled:
                ox, oy = box.overlap(other)
                if ox <= -gap or oy <= -gap:
                    continue
                down, up = other.bottom + gap - box.y, box.bottom - other.y + gap
                right, left = other.right + gap - box.x, box.right - other.x + gap
                vertical = [(0.0, down), (0.0, -up)]
                horizontal = [(right, 0.0), (-left, 0.0)]
                ordered = vertical + horizontal if box.axis == "y" else horizontal + vertical
                candidates.extend(ordered)
            candidates.sort(key=lambda move: abs(move[0]) + abs(move[1]))
            for dx, dy in candidates:
                trial = Box(box.key, box.x + dx, box.y + dy, box.w, box.h)
                if _fits(trial, bounds) and _clear(trial, settled, gap):
                    steps.append(f"shove {box.key} by ({dx:+.0f},{dy:+.0f})")
                    box.x, box.y = trial.x, trial.y
                    placed = True
                    break
            if placed:
                break
            # Nowhere to go at this size: elongate text first, then compress.
            if box.reflow is not None and box.w > max(box.min_w, 1.0) * 1.05:
                new_w = max(box.min_w, box.w * 0.85)
                new_h = box.reflow(new_w)
                steps.append(f"elongate {box.key}: width {box.w:.0f} -> {new_w:.0f}")
                box.w, box.h = new_w, new_h
            elif box.scale * 0.9 >= box.min_scale - 1e-6:
                cx, cy = box.x + box.w / 2.0, box.y + box.h / 2.0
                box.w, box.h, box.scale = box.w * 0.9, box.h * 0.9, box.scale * 0.9
                box.x, box.y = cx - box.w / 2.0, cy - box.h / 2.0
                steps.append(f"compress {box.key} to x{box.scale:.2f}")
            else:
                break
            _push(box, bounds, steps)
            if _clear(box, settled, gap):
                placed = True
                break
        if not placed and not _clear(box, settled, gap):
            blocker = next((other.key for other in settled
                            if box.overlap(other)[0] > -gap and box.overlap(other)[1] > -gap),
                           "?")
            result.unresolved.append((box.key, blocker))
            steps.append(f"unresolved {box.key}: still overlaps {blocker}")
        settled.append(box)
    return result


# ----------------------------------------------------------------------
# Fitting the scene
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Fit:
    eye: np.ndarray
    projection: np.ndarray
    dolly: float = 1.0
    zoom: float = 1.0
    shift: tuple[float, float] = (0.0, 0.0)
    covered: tuple[float, float, float, float] | None = None
    """The subject's NDC box after fitting: x0, y0, x1, y1."""


def subject_points(opaque, transparent, start: int = 0, limit: int = 12000,
                   extra: Iterable[Sequence[float]] = ()) -> np.ndarray:
    """Points of everything the scene painted after the ground, thinned out."""
    parts = []
    if len(opaque.vertices) > start:
        parts.append(np.asarray(opaque.vertices[start:], dtype=np.float32).reshape(-1, 10)[:, :3])
    if transparent.vertices:
        parts.append(np.asarray(transparent.vertices, dtype=np.float32).reshape(-1, 10)[:, :3])
    labels = [np.asarray(point, dtype=np.float32) for point in extra]
    if labels:
        parts.append(np.stack(labels))
    if not parts:
        return np.zeros((0, 3), dtype=np.float32)
    points = np.concatenate(parts)
    if len(points) > limit:
        points = points[::int(math.ceil(len(points) / limit))]
    return points


def _ndc(points: np.ndarray, mvp: np.ndarray) -> np.ndarray:
    homogeneous = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
    clip = homogeneous @ mvp.T
    visible = clip[:, 3] > 0.05
    clip = clip[visible]
    return clip[:, :2] / clip[:, 3:4]


def composed_mask(points: np.ndarray, eye, target, fov: float, design_aspect: float,
                  near: float = 0.08, far: float = 120.0) -> np.ndarray:
    """Which points the film's own frame actually showed.

    The subject is what the director framed. Geometry the composed frame cropped --
    a wall beside the camera, streaks running off the sides -- was left out on
    purpose, and fitting a new frame to it would shrink everything that matters.
    """
    composed = perspective(float(fov), design_aspect, near, far) @ look_at(eye, target)
    homogeneous = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
    clip = homogeneous @ composed.T
    ahead = clip[:, 3] > 0.05
    ndc = np.zeros((len(points), 2), dtype=np.float32)
    ndc[ahead] = clip[ahead, :2] / clip[ahead, 3:4]
    return ahead & (np.abs(ndc[:, 0]) <= 1.02) & (np.abs(ndc[:, 1]) <= 1.02)


def _bounds(ndc: np.ndarray, trim: float) -> tuple[float, float, float, float] | None:
    if len(ndc) < 4:
        return None
    x0, x1 = np.percentile(ndc[:, 0], [trim, 100.0 - trim])
    y0, y1 = np.percentile(ndc[:, 1], [trim, 100.0 - trim])
    return float(x0), float(y0), float(x1), float(y1)


def region_ndc(region: Rect, width: int, height: int) -> tuple[float, float, float, float]:
    """A pixel rectangle as NDC: x0, y0 (bottom), x1, y1 (top)."""
    return (region.x / width * 2.0 - 1.0, 1.0 - region.bottom / height * 2.0,
            region.right / width * 2.0 - 1.0, 1.0 - region.y / height * 2.0)


def fit_camera(eye, target, fov: float, width: int, height: int, region: Rect,
               points: np.ndarray, margin: float = 0.08, max_dolly: float = 2.6,
               min_zoom: float = 0.6, trim: float = 0.0, near: float = 0.08,
               far: float = 120.0, design_aspect: float | None = None) -> Fit:
    """The film's own camera, given room: dolly back, widen a little, shift.

    ``region`` is where the subject may go, in pixels. The subject is measured
    through the camera the film chose -- only what its composed frame showed,
    when ``design_aspect`` is given -- and if it already fits, only the lens
    shift applies, so it is centred in the free space at the size the film gave it.

    ``trim`` stays at zero: a percentile trim throws away whatever has few
    vertices, and a sign made of six boxes beside a dome of thousands of
    triangles is exactly what it would throw away. Geometry the composed frame
    cropped is excluded by ``design_aspect`` instead.
    """
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    if design_aspect is not None and len(points) >= 4:
        shown = composed_mask(points, eye, target, fov, design_aspect, near, far)
        if int(shown.sum()) >= 4:
            points = points[shown]
    aspect = width / max(1, height)
    base = perspective(float(fov), aspect, near, far)
    rx0, ry0, rx1, ry1 = region_ndc(region, width, height)
    room_w, room_h = (rx1 - rx0) * (1.0 - margin), (ry1 - ry0) * (1.0 - margin)

    def measure(camera_eye):
        box = _bounds(_ndc(points, base @ look_at(camera_eye, target)), trim)
        if box is None:
            return None, 1.0
        need = min(room_w / max(1e-6, box[2] - box[0]), room_h / max(1e-6, box[3] - box[1]))
        return box, need

    if len(points) < 4:
        return Fit(eye, base)
    dolly = 1.0
    camera_eye = eye
    box, need = measure(camera_eye)
    for _ in range(4):
        if box is None or need >= 0.995 or dolly >= max_dolly - 1e-6:
            break
        # A subject near the target shrinks in proportion to distance, so the
        # dolly that gives it room is the inverse of the zoom it needs.
        dolly = min(max_dolly, dolly / max(0.2, need))
        camera_eye = target + (eye - target) * dolly
        box, need = measure(camera_eye)
    if box is None:
        return Fit(eye, base)
    zoom = min(1.0, max(min_zoom, need))
    cx, cy = (box[0] + box[2]) / 2.0 * zoom, (box[1] + box[3]) / 2.0 * zoom
    tx = (rx0 + rx1) / 2.0 - cx
    ty = (ry0 + ry1) / 2.0 - cy
    adjust = np.array([[zoom, 0.0, 0.0, tx], [0.0, zoom, 0.0, ty],
                       [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    covered = (box[0] * zoom + tx, box[1] * zoom + ty, box[2] * zoom + tx, box[3] * zoom + ty)
    return Fit(camera_eye.astype(np.float32), (adjust @ base).astype(np.float32),
               dolly, zoom, (float(tx), float(ty)), covered)


class FitSmoother:
    """Keeps a fitted camera from twitching as a scene animates.

    Making room is urgent, giving it back is not: a subject that grows is given
    space quickly, while one that shrinks is followed in slowly, so reveals read
    as a camera easing back rather than a zoom that pumps.
    """

    def __init__(self, out_seconds: float = 0.18, in_seconds: float = 1.4,
                 shift_seconds: float = 0.35):
        self.out_seconds, self.in_seconds, self.shift_seconds = out_seconds, in_seconds, shift_seconds
        self.state: tuple[float, float, float, float] | None = None
        self.key = None

    def reset(self) -> None:
        self.state = None

    def __call__(self, key, dolly: float, zoom: float, shift: tuple[float, float],
                 dt: float) -> tuple[float, float, tuple[float, float]]:
        # A new chapter is a cut: the camera snaps to its own fit.
        if self.state is None or key != self.key or dt <= 0.0:
            self.key = key
            self.state = (dolly, zoom, shift[0], shift[1])
            return dolly, zoom, shift
        old_dolly, old_zoom, old_x, old_y = self.state
        size_old, size_new = old_zoom / old_dolly, zoom / dolly
        seconds = self.out_seconds if size_new < size_old else self.in_seconds
        blend = 1.0 - math.exp(-dt / seconds)
        shift_blend = 1.0 - math.exp(-dt / self.shift_seconds)
        new = (old_dolly + (dolly - old_dolly) * blend, old_zoom + (zoom - old_zoom) * blend,
               old_x + (shift[0] - old_x) * shift_blend, old_y + (shift[1] - old_y) * shift_blend)
        self.state = new
        return new[0], new[1], (new[2], new[3])


def apply_fit(eye, target, fov: float, width: int, height: int, dolly: float, zoom: float,
              shift: tuple[float, float], near: float = 0.08, far: float = 120.0):
    """(eye, projection) for given fit parameters, so smoothed values can be rendered."""
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    camera_eye = target + (eye - target) * dolly
    base = perspective(float(fov), width / max(1, height), near, far)
    adjust = np.array([[zoom, 0.0, 0.0, shift[0]], [0.0, zoom, 0.0, shift[1]],
                       [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return camera_eye.astype(np.float32), (adjust @ base).astype(np.float32)


# ----------------------------------------------------------------------
# Proofs
# ----------------------------------------------------------------------

def validate_frame() -> None:
    """The resolver and the fit, proved on cases small enough to reason about."""
    landscape = Frame(1920, 1080)
    assert not landscape.adapted and not Frame(1600, 900).adapted
    portrait = Frame(1080, 1920)
    assert portrait.adapted and portrait.portrait
    assert not Frame(1080, 1920, 9.0 / 16.0).adapted
    safe = portrait.safe()
    assert safe.x > 0 and safe.bottom < 1920 and safe.right < 1080

    # Two boxes on top of each other: the lower priority one is shoved clear.
    bounds = Rect(0, 0, 1000, 1000)
    a = Box("title", 100, 100, 600, 200, priority=5, movable=False)
    b = Box("callout", 150, 150, 300, 120, priority=1)
    result = resolve([a, b], bounds)
    assert b.overlap(a)[1] <= -6.0 + 1e-6 or b.overlap(a)[0] <= -6.0 + 1e-6, result.steps
    assert any(step.startswith("shove callout") for step in result.steps), result.steps

    # A box pushed off the frame comes back inside it.
    c = Box("stray", 900, 950, 200, 100)
    resolve([c], bounds)
    assert c.right <= 1000.5 and c.bottom <= 1000.5

    # Text too wide for the frame elongates rather than shrinking.
    text = Box("headline", 0, 0, 1400, 100, reflow=lambda width: 100 * math.ceil(1400 / width))
    result = resolve([text], bounds)
    assert text.w <= 1000.5 and text.h >= 200 and text.scale == 1.0, result.steps

    # No room at all: the lower box is compressed, and never below its minimum.
    full = Box("panel", 0, 0, 1000, 1000, priority=9, movable=False)
    squeezed = Box("note", 200, 200, 400, 400, priority=0, min_scale=0.5)
    result = resolve([full, squeezed], bounds)
    assert squeezed.scale >= 0.5 - 1e-9
    assert result.unresolved, "a box with no room anywhere must be reported, not hidden"

    # The fit: a wide subject in a tall frame is given room, and ends up inside
    # the region, centred.
    xs = np.linspace(-6.0, 6.0, 25)
    points = np.array([[x, 0.0, z] for x in xs for z in (0.0, 3.0)], dtype=np.float32)
    eye, target = np.array([0.0, -14.0, 3.0]), np.array([0.0, 0.0, 1.5])
    region = Rect(80, 200, 920, 900)
    fit = fit_camera(eye, target, 48.0, 1080, 1920, region, points)
    assert fit.dolly > 1.0 or fit.zoom < 1.0
    rx0, ry0, rx1, ry1 = region_ndc(region, 1080, 1920)
    x0, y0, x1, y1 = fit.covered
    assert rx0 - 1e-3 <= x0 and x1 <= rx1 + 1e-3 and ry0 - 1e-3 <= y0 and y1 <= ry1 + 1e-3, \
        (fit.covered, (rx0, ry0, rx1, ry1))
    assert abs((x0 + x1) / 2 - (rx0 + rx1) / 2) < 0.02

    # A subject that already fits is only moved, never enlarged.
    small = points * 0.1
    fit = fit_camera(eye, target, 48.0, 1080, 1920, region, small)
    assert fit.dolly == 1.0 and fit.zoom == 1.0

    # Geometry the composed frame cropped does not count as subject: walls standing
    # wholly outside the 16:9 frame, off both sides, leave the fit as it was.
    # (A wall running across the frame would be on screen, and rightly count.)
    sides = np.concatenate([np.linspace(-80.0, -40.0, 200), np.linspace(40.0, 80.0, 200)])
    wall = np.array([[x, 6.0, 0.5] for x in sides], dtype=np.float32)
    plain = fit_camera(eye, target, 48.0, 1080, 1920, region, points, design_aspect=16 / 9)
    walled = fit_camera(eye, target, 48.0, 1080, 1920, region,
                        np.concatenate([points, wall]), design_aspect=16 / 9)
    unguarded = fit_camera(eye, target, 48.0, 1080, 1920, region, np.concatenate([points, wall]))
    assert abs(walled.dolly - plain.dolly) < 0.35, (walled.dolly, plain.dolly)
    assert unguarded.dolly > walled.dolly + 0.2 or unguarded.zoom < walled.zoom - 0.05

    # A vertical film on a wide screen is not re-fitted; a wide film on a phone is.
    assert not Frame(1920, 1080, 9 / 16).narrower
    assert Frame(1080, 1920, 16 / 9).narrower

    # The smoother snaps on a cut and eases within a chapter.
    smooth = FitSmoother()
    assert smooth("a", 2.0, 0.8, (0.1, 0.0), 1 / 30) == (2.0, 0.8, (0.1, 0.0))
    dolly, zoom, shift = smooth("a", 1.0, 1.0, (0.0, 0.0), 1 / 30)
    assert 1.0 < dolly < 2.0 and shift[0] > 0.0
    assert smooth("b", 1.0, 1.0, (0.0, 0.0), 1 / 30) == (1.0, 1.0, (0.0, 0.0))
