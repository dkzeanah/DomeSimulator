"""Any earlier film, re-staged in the Cabin World, with cinematic cameras.

Every film this repository made before the Cabin World drew its teaching
geometry -- charts, models, diagrams, labels -- around the origin of a dark,
empty stage. This module moves that geometry, untouched, onto a timber
**exhibit platform** on the Cabin World's hilltop, west-south-west of the
dome, and films it the way a camera operator would rather than with the old
high orbit:

* every chapter's exhibit is **measured**, and the camera is placed so it
  fills about three fifths of the frame;
* the camera stands on the far side of the exhibit from the dome, so the
  real dome and the sunset are always behind what is being explained;
* it stays **low** (eye height about a metre), on a longer lens, and moves
  slowly with eased starts and stops;
* the shot changes every chapter and alternates sides -- a push in, a low
  arc looking up, a slide across, a look down on a chapter full of figures,
  a dolly zoom when a chapter asks *why* -- and the film opens with a crane
  from the log's end grain and closes by craning out over the whole hill.

Nothing about the original lesson changes: the same chapters (so the same
narration and the same computed figures), the same painters. Where a chapter
is *about* something the world holds -- the log, the seam, the dome -- it can
be pointed at the real object with ``stations={slug: shot}``; that is how the
world grows film by film.

    lesson = restage(ORIGINAL_LESSON)      # key "cabin_<original key>"
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from . import cabin_world as cw
from . import shots
from .lessons import Lesson
from .render_kit import TriangleBatch

CENTRE = np.array([0.6, 6.6])
"""The exhibit platform: north of the dome, on the open valley side. The forest
fills both flanks of the hill (cover_scene.forest keeps only a north-south
corridor clear), and its lowest branches overhang anywhere west or east of the
clearing; here nothing overhangs, the deck is clear, and a camera beyond the
platform looks back across the exhibit at the dome."""
RADIUS = 2.3
HEIGHT = 0.22
SCALE = 0.32
"""An original scene spans about seven units from its centre; at this scale
that fills the platform."""
TURN_DEG = 0.0
"""Turns the original stage so its usual front (+Y) faces away from the dome --
which, north of the dome, it already does."""
LENS = 40.0
"""A longer lens than the renderer's 48: less distortion, more like cinema."""
FILL = 0.60
"""Share of the frame height the exhibit fills."""
CYCLE = ("push", "arc", "slide", "push_low", "over")
"""The shot rotation for ordinary chapters; figure-heavy and *why* chapters
get their own (see :func:`shot_kind`)."""


def _rotation() -> np.ndarray:
    a = math.radians(TURN_DEG)
    return np.array([[math.cos(a), -math.sin(a), 0.0],
                     [math.sin(a), math.cos(a), 0.0],
                     [0.0, 0.0, 1.0]])


R = _rotation()
OFFSET = np.array([CENTRE[0], CENTRE[1], HEIGHT])


FIT_RADIUS = 1.5
"""The widest an exhibit may stand, in metres from its middle. The platform sits
in the clear corridor between the deck and the pines, and a camera cannot back
far enough off a wider one to see it whole; a bigger exhibit (a saw table, a
cord of wood) is shrunk to this for its chapter. Labels and figures are not
touched -- only the model's size."""


def to_world(point, fit: float = 1.0) -> np.ndarray:
    """A point on the original stage, placed on the exhibit platform."""
    return R @ (np.asarray(point, dtype=np.float64) * SCALE * fit) + OFFSET


def _move_vertices(vertices: list, start: int, fit: float = 1.0) -> None:
    """Transform a batch's vertices from ``start`` on, in place."""
    if len(vertices) <= start:
        return
    block = np.asarray(vertices[start:], dtype=np.float64).reshape(-1, 10)
    block[:, 0:3] = block[:, 0:3] * (SCALE * fit) @ R.T + OFFSET
    block[:, 3:6] = block[:, 3:6] @ R.T
    vertices[start:] = block.reshape(-1).tolist()


def platform() -> TriangleBatch:
    """A low, round timber stage the exhibits stand on."""
    from wedge_book import cover_scene as cs

    batch = TriangleBatch()
    top, edge = cs.DECK, cs.DECK_EDGE
    boards = 18
    for k in range(boards):
        a0, a1 = math.tau * k / boards, math.tau * (k + 1) / boards
        p = [np.array([CENTRE[0] + r * math.cos(t), CENTRE[1] + r * math.sin(t), HEIGHT])
             for r, t in ((0.0, a0), (RADIUS, a0), (RADIUS, a1))]
        shade = 0.93 + 0.07 * (k % 3) / 2
        batch.triangle(p[0], p[1], p[2], tuple(c * shade for c in top[:3]) + (1.0,),
                       np.array([0.0, 0.0, 1.0]))
        low = [np.array([CENTRE[0] + RADIUS * math.cos(t), CENTRE[1] + RADIUS * math.sin(t), z])
               for t, z in ((a0, 0.0), (a1, 0.0), (a1, HEIGHT), (a0, HEIGHT))]
        batch.quad(*low, edge)
    return batch


# ----------------------------------------------------------------------
# Measuring an exhibit
# ----------------------------------------------------------------------

def bounds(opaque: TriangleBatch, transparent: TriangleBatch, labels=(), extra=()) -> tuple:
    """Centre and radius of what a chapter drew, ignoring stray outliers.

    ``extra`` holds point sets drawn outside the triangle batches -- the Dome
    Creator's meshes -- which are as much the exhibit as anything else."""
    pts = []
    for batch in (opaque, transparent):
        if batch.vertices:
            pts.append(np.asarray(batch.vertices, dtype=np.float64).reshape(-1, 10)[:, 0:3])
    pts.extend(np.asarray(e, dtype=np.float64).reshape(-1, 3) for e in extra if len(e))
    pts.extend(np.asarray([getattr(l, "point")], dtype=np.float64) for l in labels)
    if not pts:
        c = np.array([CENTRE[0], CENTRE[1], HEIGHT + 0.8])
        return c, 1.4, False, c - 0.7, c + 0.7
    p = np.concatenate(pts)
    lo, hi = np.percentile(p, 3, axis=0), np.percentile(p, 97, axis=0)
    centre = (lo + hi) / 2
    radius = float(np.linalg.norm(hi - lo) / 2)
    # Trimming ignores stray labels, but it also drops a big plain object -- a
    # saw table is eight corners among thousands of points. Never frame the
    # exhibit smaller than its actual geometry.
    geometry = np.concatenate(pts[: len(pts) - len(labels)]) if len(pts) > len(labels) else p
    full = geometry.max(axis=0) - geometry.min(axis=0)
    radius = max(radius, 0.45 * float(np.linalg.norm(full[:2])))
    centre[2] = max(centre[2], HEIGHT + 0.15)
    span = hi - lo
    tall = bool(span[2] > 0.6 * max(span[0], span[1]))
    # Big exhibits (a saw table, a cord of wood) need the camera well back:
    # capping them small put it inside them.
    # The full extent (not the trimmed one) is what a camera must stay out of.
    return centre, float(np.clip(radius, 0.5, 6.0)), tall, p.min(axis=0), p.max(axis=0)


# ----------------------------------------------------------------------
# Cinematic shots
# ----------------------------------------------------------------------

def shot_kind(index: int, count: int, chapter) -> str:
    title = f"{chapter.title} {chapter.promise}".lower()
    if index == 0:
        return "open"
    if index == count - 1:
        return "close"
    if any(w in title for w in ("why ", "what if", "the answer", "reveal", "turns out")):
        return "dolly"
    if len(chapter.equations) >= 4 or getattr(chapter, "callouts", ()):
        return "plan" if index % 3 == 0 else CYCLE[index % len(CYCLE)]
    return CYCLE[index % len(CYCLE)]


def _dist(radius: float, lens: float = LENS) -> float:
    """Back far enough that the exhibit's width fills about 70% of a 16:9 frame.

    Exhibits are wider than they are tall, so the width decides. (A phone cut
    re-fits its own framing from the exhibit's points.)"""
    half_h = math.tan(math.radians(lens) / 2)
    half_w = half_h * 16 / 9
    return max(1.1, radius / half_w / 0.70)


def _vdist(height: float, lens: float = LENS) -> float:
    """Back far enough that a tall, thin exhibit's height fills about 65% of the frame."""
    return (height / 2) / math.tan(math.radians(lens) / 2) / 0.65


def corridor_half_width(y: float) -> float:
    """How far either side of x = 0 is clear of trees at a given y (with a margin)."""
    return 7.5 + max(0.0, y) * 0.35 - 1.2


def safe(eye) -> np.ndarray:
    """Keep a camera out of the trees: inside the clear corridor, above ground."""
    eye = np.asarray(eye, dtype=np.float64).copy()
    limit = corridor_half_width(eye[1])
    eye[0] = float(np.clip(eye[0], -limit, limit))
    ground = 0.0 if np.hypot(eye[0], eye[1]) <= 9 else -0.018 * float(np.hypot(eye[0], eye[1])) ** 2
    eye[2] = max(eye[2], ground + 0.35)
    return eye


def clear_of(eye, box) -> np.ndarray:
    """A camera that would sit inside the exhibit rises above it instead.

    Big exhibits -- a saw table, a sled, a cord of wood -- are larger than the
    room between the platform and the trees, so even a correctly framed shot
    can land inside one."""
    eye = np.asarray(eye, dtype=np.float64)
    if box is None:
        return eye
    lo, hi = (np.asarray(b, dtype=np.float64) for b in box)
    margin = 0.15
    if np.all(eye >= lo - margin) and np.all(eye <= hi + margin):
        eye = eye.copy()
        eye[2] = hi[2] + 0.6
    return eye


_PINES: np.ndarray | None = None


def pines() -> np.ndarray:
    """Every pine in the Cabin World as (x, y, ground, height), from the forest itself."""
    global _PINES
    if _PINES is None:
        from wedge_book import cover_scene
        sites: list = []
        cover_scene.forest(sites=sites)
        rows = []
        for x, y, h in sites:
            ground = -0.018 * (x * x + y * y) if (x * x + y * y) > 81 else 0.0
            rows.append((x, y, ground, h))
        _PINES = np.asarray(rows, dtype=np.float64)
    return _PINES


def blocked(eye, target, samples: int = 32) -> bool:
    """True when a pine's canopy (or trunk) stands between the eye and the target."""
    t = np.linspace(0.0, 1.0, samples)[:, None]
    ray = np.asarray(eye, dtype=np.float64) * (1 - t) + np.asarray(target, dtype=np.float64) * t
    trees = pines()
    dx = ray[:, None, 0] - trees[None, :, 0]
    dy = ray[:, None, 1] - trees[None, :, 1]
    h = trees[None, :, 3]
    zr = (ray[:, None, 2] - trees[None, :, 2]) / h
    # The canopy's envelope: widest just above the lowest tier, closing to the
    # tip; below the tiers, only the trunk.
    canopy = np.where((zr >= 0.25) & (zr <= 1.15),
                      h * (0.26 - 0.24 * np.clip((zr - 0.25) / 0.9, 0, 1)), h * 0.018)
    canopy = np.where(zr < -0.05, 0.0, canopy) + 0.35
    return bool(np.any(np.hypot(dx, dy) < canopy))


def clear_view(shot, guard=lambda e: e, samples=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """Move the whole shot until no pine is in the way.

    First a small pull in along the sight lines; if that is not enough, swing
    the shot round its subject -- toward the open deck side -- rather than
    pulling it into the exhibit. Decided once for the shot, not per frame, so
    the move stays smooth. ``guard`` runs on every moved eye (out of the
    exhibit, out of the trees, above ground)."""
    m = cw.landmarks()

    def at(p, s, turn):
        e, t, f = shot(p)
        e, t = np.asarray(e, dtype=np.float64), np.asarray(t, dtype=np.float64)
        v = (e - t) * s
        c, sn = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        v = np.array([v[0] * c - v[1] * sn, v[0] * sn + v[1] * c, v[2]])
        return guard(t + v), t, f

    def ok(s, turn):
        for e, t, _f in (at(p, s, turn) for p in samples):
            if blocked(e, t):
                return False
            if np.hypot(*(e[:2] - m.dome_centre[:2])) < m.dome_r + 0.4:
                return False            # swung into the dome itself
        return True

    choice = (1.0, 0.0)
    for s, turn in ([(s, 0.0) for s in (1.0, 0.9, 0.8, 0.7)]
                    + [(s, sign * a) for a in (25, 50, 75, 100, 130, 160)
                       for sign in (1, -1) for s in (1.0, 0.85, 0.7)]):
        if ok(s, turn):
            choice = (s, turn)
            break
    return lambda p: at(p, *choice)


def _guarded(shot, box=None):
    return clear_view(shot, lambda e: safe(clear_of(e, box)))


def cinematic(kind: str, centre: np.ndarray, radius: float, side: int, tall: bool = False,
              box=None):
    if kind == "plan" and tall:
        kind = "push"      # looking down on a column shows only the floor
    height = 0.0 if box is None else float(box[1][2] - box[0][2])
    return _guarded(_cinematic(kind, centre, radius, side, height), box)


def _cinematic(kind: str, centre: np.ndarray, radius: float, side: int, height: float = 0.0):
    """A shot for an exhibit: ``side`` is +1 or -1, alternating by chapter."""
    m = cw.landmarks()
    away = np.array([centre[0] - m.dome_centre[0], centre[1] - m.dome_centre[1], 0.0])
    away /= np.linalg.norm(away) + 1e-9

    def around(deg: float, dist: float, z: float) -> np.ndarray:
        a = math.atan2(away[1], away[0]) + math.radians(deg) * side
        return np.array([centre[0] + dist * math.cos(a), centre[1] + dist * math.sin(a), z])
    d = max(_dist(radius), _vdist(height))
    eye_z = HEIGHT + max(0.55, radius * 0.55)
    look = centre + np.array([0.0, 0.0, -0.1 * radius])
    if kind == "open":
        # Start low at the foot of the exhibit, then rise and pull back to
        # establish it with the dome behind -- a crane that stays on this side.
        base = np.array([centre[0], centre[1], HEIGHT + 0.15])
        # (Not closer than three quarters of the framing distance: a wide
        # exhibit seen from its own foot is a wall.)
        start = around(18, d * 0.75, HEIGHT + 0.3)
        return shots.crane_reveal(look, start, around(30, d * 1.15, eye_z + 0.5),
                                  fov_start=LENS + 6, fov_end=LENS, look_start=base)
    if kind == "close":
        # Up and back on the exhibit's side, never through the dome: the last
        # frame holds the exhibit, the platform and the dome behind them.
        high = np.array([centre[0], centre[1], 0.0]) + away * (d * 2.2) + np.array([0, 0, 3.8])
        return shots.crane_reveal(m.dome_centre + np.array([0, 0, 1.0]),
                                  around(25, d, eye_z), high,
                                  fov_start=LENS, fov_end=46, look_start=look)
    if kind == "push":
        return shots.push_in(look, around(30, d * 1.35, eye_z + 0.2), around(26, d * 1.05, eye_z),
                             fov_start=LENS + 2, fov_end=LENS)
    if kind == "push_low":
        return shots.push_in(look + np.array([0, 0, 0.1 * radius]),
                             around(-20, d * 1.3, HEIGHT + 0.35), around(-16, d * 1.02, HEIGHT + 0.3),
                             fov_start=LENS + 4, fov_end=LENS + 2)
    if kind == "arc":
        a0 = math.degrees(math.atan2(away[1], away[0]))
        return shots.low_hero(look, d, eye_height=HEIGHT + 0.4, start_deg=a0 - 38 * side,
                              sweep_deg=34 * side, look_up=0.12 * radius, fov=LENS + 2)
    if kind == "slide":
        return shots.fly_through([around(-35, d, eye_z), around(0, d * 0.95, eye_z + 0.1),
                                  around(35, d, eye_z)],
                                 [look + np.array([0.15, 0, 0]), look,
                                  look - np.array([0.15, 0, 0])], fov=LENS)
    if kind == "over":
        # The reverse angle: from the dome's side of the exhibit, looking out
        # over it to the hills -- never closer than the framing distance, and
        # never inside the dome itself.
        reach = min(d * 1.1, float(np.hypot(*(centre[:2] - m.dome_centre[:2]))) - m.dome_r - 0.4)
        if reach < radius * 2.2:
            # No room between the dome and a big exhibit: a low arc instead.
            return _cinematic("arc", centre, radius, side, height)
        return shots.push_in(look, around(180 + 22, reach, eye_z + 0.35),
                             around(180 + 16, reach * 0.9, eye_z + 0.2),
                             fov_start=LENS + 8, fov_end=LENS + 4)
    if kind == "plan":
        return shots.push_in(look, around(10, d * 0.7, centre[2] + d * 0.95),
                             around(18, d * 0.55, centre[2] + d * 0.8), fov_start=LENS + 4,
                             fov_end=LENS)
    if kind == "dolly":
        direction = look - around(20, d, eye_z)
        return shots.dolly_zoom(look, direction, d * 2.0, d * 1.2,
                                subject_width=radius * 2.0, height=0.0)
    raise KeyError(kind)


# ----------------------------------------------------------------------
# The adapter
# ----------------------------------------------------------------------

def restage(original: Lesson, stations: dict | None = None, key: str = "",
            keep_original_cameras: bool = False) -> Lesson:
    """``original`` on the exhibit platform in the Cabin World.

    ``stations`` maps a chapter slug to a shot aimed at a real object in the
    world. ``keep_original_cameras`` carries each chapter's original camera
    over instead of the cinematic one -- for a film whose framing *is* the
    point (a drama with its own camera direction).
    """
    stations = dict(stations or {})
    stages = {chapter.stage for chapter in original.chapters}
    count = len(original.chapters)
    measured: dict[str, tuple] = {}
    fits: dict[str, float] = {}
    shot_for: dict[int, object] = {}

    def place(stage: str):
        """The original painter, moved onto the platform at a given fit."""
        painter = original.scenes.get(stage)

        def paint(app, opaque, transparent, p: float, fit: float) -> None:
            cw.paint(app, subject=False)
            app.static_layer("cabin:stage", platform)
            o0, t0 = len(opaque.vertices), len(transparent.vertices)
            labels0 = len(app.world_labels)
            icons0 = len(getattr(app, "world_icons", []))
            draws0 = len(getattr(app, "creator_draws", []))
            if painter is not None:
                painter(app, opaque, transparent, p)
            else:
                getattr(app, f"scene_{stage}")(opaque, transparent, p)
            _move_vertices(opaque.vertices, o0, fit)
            _move_vertices(transparent.vertices, t0, fit)
            for label in app.world_labels[labels0:]:
                label.point = to_world(label.point, fit).astype(np.float32)
                # Some films handed labels 0-1 colours where 0-255 is meant,
                # which rendered their text nearly black. Put it right here.
                if max(label.color) <= 1.0:
                    label.color = tuple(int(round(c * 255)) for c in label.color[:3])
            for icon in getattr(app, "world_icons", [])[icons0:]:
                if hasattr(icon, "point"):
                    icon.point = to_world(icon.point, fit).astype(np.float32)
            for draw in getattr(app, "creator_draws", [])[draws0:]:
                draw.offset = tuple(float(v) for v in to_world(draw.offset, fit))
                draw.scale = float(draw.scale) * SCALE * fit
                draw.yaw = float(draw.yaw) + TURN_DEG
        return paint

    placed = {stage: place(stage) for stage in stages}

    def measure_at(app, stage: str, fit: float) -> tuple:
        """Paint the chapter once, fully built, into scratch batches."""
        saved = {name: list(getattr(app, name, [])) for name in
                 ("world_labels", "world_icons", "creator_draws", "static_draws")}
        o, t = TriangleBatch(), TriangleBatch()
        labels0 = len(app.world_labels)
        draws0 = len(getattr(app, "creator_draws", []))
        placed[stage](app, o, t, 0.9, fit)
        meshes = [d.points() for d in getattr(app, "creator_draws", [])[draws0:]
                  if not d.is_backdrop]
        result = bounds(o, t, app.world_labels[labels0:], meshes)
        for name, value in saved.items():
            if hasattr(app, name):
                setattr(app, name, value)
        return result

    def fit_of(app, stage: str) -> float:
        """How much this chapter's exhibit is shrunk to stand on the platform."""
        if stage not in fits and keep_original_cameras:
            fits[stage] = 1.0         # its own cameras were framed for its own size
        if stage not in fits:
            natural = measure_at(app, stage, 1.0)
            fits[stage] = min(1.0, FIT_RADIUS / natural[1])
            measured[stage] = (natural if fits[stage] == 1.0
                               else measure_at(app, stage, fits[stage]))
        return fits[stage]

    def measure(app, stage: str) -> tuple:
        fit_of(app, stage)
        return measured[stage]

    def wrap(stage: str):
        def paint(app, opaque, transparent, p: float) -> None:
            placed[stage](app, opaque, transparent, p, fit_of(app, stage))
        return paint

    painters = {stage: wrap(stage) for stage in stages}

    def camera(app, chapter, progress: float, width: int, height: int):
        if chapter.slug in stations:
            return stations[chapter.slug](progress)
        if chapter.stage not in painters:
            # A segment the exporter spliced on (share, outro): it has its own
            # scene, composed for the renderer's house camera.
            eye, target = app.camera()
            return eye, target, 48.0
        if keep_original_cameras:
            if original.camera_fn is not None:
                eye, target, fov = original.camera_fn(app, chapter, progress, width, height)
            else:
                (eye, target), fov = app.camera(), 48.0
            return to_world(eye), to_world(target), fov
        index = next((i for i, c in enumerate(app.chapters) if c is chapter), 0)
        if index not in shot_for:
            # Measured and cleared of the trees once per chapter, not per frame.
            centre, radius, tall, lo, hi = measure(app, chapter.stage)
            kind = shot_kind(index, len(app.chapters), chapter)
            shot_for[index] = cinematic(kind, centre, radius, 1 if index % 2 == 0 else -1,
                                        tall, (lo, hi))
        return shot_for[index](progress)

    return replace(
        original,
        key=key or f"cabin_{original.key}",
        scenes=painters,
        camera_fn=camera,
        ground="off",
        backdrop=cw.backdrop,
        light=cw.LIGHT,
        snapshot_prefix=f"cabin_{original.snapshot_prefix}",
    )


def validate_cabin_stage() -> None:
    # The platform stays clear of the deck, the log and stump, and the forest.
    m = cw.landmarks()
    centre = float(np.hypot(*CENTRE))
    assert centre - RADIUS > m.deck_r + 0.2, "the exhibit platform overlaps the deck"
    assert centre + RADIUS < 9.0, "the exhibit platform runs into the forest"
    for thing in (m.log_end, m.stump_top):
        assert np.hypot(*(np.asarray(thing[:2]) - CENTRE)) > RADIUS + 0.5
    # A point and its normal move together; the original origin lands on the platform.
    assert np.allclose(to_world((0, 0, 0)), OFFSET)
    batch = TriangleBatch()
    batch.triangle(np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0]),
                   (1, 1, 1, 1), np.array([0.0, 0.0, 1.0]))
    _move_vertices(batch.vertices, 0)
    moved = np.asarray(batch.vertices).reshape(-1, 10)
    assert np.allclose(moved[0, :3], to_world((1, 0, 0)))
    assert np.allclose(moved[0, 3:6], [0.0, 0.0, 1.0])
    # Every shot kind produces finite cameras that look at something.
    centre = np.array([CENTRE[0], CENTRE[1], 0.9])
    for kind in ("open", "close", "push", "push_low", "arc", "slide", "over", "plan", "dolly"):
        for side in (1, -1):
            for p in (0.0, 0.5, 1.0):
                eye, target, fov = cinematic(kind, centre, 1.5, side)(p)
                assert np.all(np.isfinite(eye)) and 15 < fov < 80, kind
                assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.3, kind
                assert eye[2] > 0.1, f"{kind}: camera below the ground"
                assert abs(eye[0]) <= corridor_half_width(eye[1]) + 1e-9, f"{kind}: in the trees"
    # The pines the cameras avoid are the forest's own seventy, and a pine
    # really does block a sight line drawn through its canopy.
    trees = pines()
    assert len(trees) == 70
    x, y, g, h = trees[0]
    assert blocked((x - h * 0.6, y, g + h * 0.35), (x + h * 0.6, y, g + h * 0.35))
    assert not blocked((0.0, 6.0, 1.5), (0.0, 7.0, 1.0))
    # Standard shots of a normal exhibit see it past the trees.
    for kind in ("push", "arc", "slide", "over"):
        eye, target, _ = cinematic(kind, centre, 1.5, 1)(0.5)
        assert not blocked(eye, target), f"{kind}: a pine is in the way"
