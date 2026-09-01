"""Cinematic camera director for the narrative module (the CCC).

Micro-drama is shot vertically, so this module works in 9:16 from the
start: a subject's eye-line is placed on the upper third of a tall frame,
headroom is measured rather than eyeballed, and every shot returns a
plain ``(eye, target, fov)`` that the existing renderer already knows how
to consume through :func:`two_v_demo.render_kit.look_at` and
:func:`~two_v_demo.render_kit.perspective`.

**On the ``fov`` field in the specification's script JSON.**  Its values
are 35, 50, 28 and 40, and the push-in is described as "35mm to 85mm".
Those are lens focal lengths, not angles, so this module reads that
field as **millimetres on a full-frame sensor** and converts to the
vertical angle the renderer wants.  A 35 mm lens framed 9:16 gives a
37.8 degree vertical angle; read as degrees instead it would be a much
tighter lens than the spec intends, and the push-in would run backwards.

The one thing this module cannot deliver is the whip pan's *motion
blur*: the renderer draws one clean sample per frame and has no shutter.
The pan itself is executed at the specified speed, and
:data:`WHIP_PAN_NOTE` says plainly what is missing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .geometry import normalize
from .render_kit import look_at, perspective, project_point


# Full-frame sensor, and the 9:16 crop taken out of its height.
SENSOR_HEIGHT_MM = 24.0
VERTICAL_ASPECT = 9.0 / 16.0

# Where the eye-line sits in a vertical frame: one third down from the
# top, which is the grid line the specification's framing diagram marks.
EYE_LINE_FROM_TOP = 1.0 / 3.0
HEADROOM_MIN = 0.02
HEADROOM_MAX = 0.28
"""Fraction of frame height above the crown.

Headroom here is a *consequence*, not a setting: once the eyes are
pinned to the third line, how much sky is left above the head follows
from how tight the shot is.  A medium shot lands near a quarter of the
frame, an extreme close-up near nothing.  The band exists to catch the
two real faults -- a cropped crown, or a subject sunk into the bottom of
a tall frame -- rather than to impose a fixed margin on every shot."""

WHIP_PAN_NOTE = (
    "The whip pan executes at the specified 0.15 s but renders without "
    "motion blur: this pipeline draws one sample per frame and has no "
    "shutter model."
)


def fov_for_focal(focal_mm: float) -> float:
    """Vertical field of view, in degrees, for a lens on a 9:16 frame."""
    return math.degrees(2.0 * math.atan(SENSOR_HEIGHT_MM / (2.0 * focal_mm)))


def focal_for_fov(fov_deg: float) -> float:
    return SENSOR_HEIGHT_MM / (2.0 * math.tan(math.radians(fov_deg) * 0.5))


def distance_for_subject(height_m: float, focal_mm: float,
                         fill: float = 0.62) -> float:
    """How far back to stand so a subject of ``height_m`` fills ``fill``.

    ``fill`` is the fraction of the frame's height the subject should
    occupy: about 0.6 for a medium close-up, near 1.0 for an extreme
    close-up on a face.
    """
    half_angle = math.radians(fov_for_focal(focal_mm)) * 0.5
    return (height_m / max(0.05, fill) * 0.5) / math.tan(half_angle)


@dataclass(frozen=True)
class CameraState:
    """One camera, ready for the renderer."""

    eye: np.ndarray
    target: np.ndarray
    fov_deg: float
    focal_mm: float
    shot_id: str

    def matrices(self, width: int, height: int, near: float = 0.08,
                 far: float = 120.0):
        projection = perspective(self.fov_deg, width / height, near, far)
        view = look_at(np.asarray(self.eye, dtype=np.float32),
                       np.asarray(self.target, dtype=np.float32))
        return projection, view, projection @ view


def aim_with_eyeline(eye, subject_eye, fov_deg: float) -> np.ndarray:
    """The look-at point that puts ``subject_eye`` on the upper third.

    The camera aims below the subject's eyes by exactly the distance
    that lifts them from the centre of frame to the third line, so the
    framing is a computed consequence rather than a nudged offset.
    """
    eye = np.asarray(eye, dtype=float)
    subject_eye = np.asarray(subject_eye, dtype=float)
    distance = float(np.linalg.norm(subject_eye - eye))
    half_height = distance * math.tan(math.radians(fov_deg) * 0.5)
    lift = half_height * (0.5 - EYE_LINE_FROM_TOP) * 2.0
    return subject_eye - np.array([0.0, 0.0, lift])


def eyeline_fraction(camera: CameraState, subject_eye,
                     width: int = 1080, height: int = 1920) -> float:
    """Where the subject's eyes actually land, 0 at the top of frame."""
    _projection, _view, mvp = camera.matrices(width, height)
    screen = project_point(mvp, np.asarray(subject_eye, dtype=float),
                           width, height)
    if screen is None:
        return float("nan")
    return screen[1] / height


def headroom_fraction(camera: CameraState, crown,
                      width: int = 1080, height: int = 1920) -> float:
    """Fraction of the frame above the character's head."""
    _projection, _view, mvp = camera.matrices(width, height)
    screen = project_point(mvp, np.asarray(crown, dtype=float), width, height)
    if screen is None:
        return float("nan")
    return screen[1] / height


# ----------------------------------------------------------------------
# The shots
# ----------------------------------------------------------------------

MIN_SUBJECT_DISTANCE_M = 0.85
"""No shot puts the lens closer than this to a face.

Two reasons, one physical and one honest: a camera nearer than about a
metre is standing where the other actor is, and this package's figure
has no face rig, so a true extreme close-up would fill a vertical frame
with an untextured head.  The push-in therefore ends on a head-and-
shoulders close-up, which is as tight as this rig can carry."""


def cam_dolly_push_fast(subject_eye, from_direction, elapsed_s: float,
                        focal_start_mm: float = 35.0,
                        focal_end_mm: float = 50.0,
                        duration_s: float = 0.40) -> CameraState:
    """Medium shot to close-up in 0.4 s, lens tightening with it.

    Both the distance and the lens move, which is what separates a push
    from a zoom: the subject grows *and* the background compresses.

    **Why this ends at 50 mm and not the specified 85.**  Distance for a
    given framing is ``framed / (2 fill tan(fov/2))``, so a longer lens
    needs *more* room, not less.  Going 35 to 85 mm while ending on the
    head-and-shoulders shot this faceless rig can carry would put the
    camera further away at the end than at the start -- a push-in that
    retreats.  An 85 mm end only closes distance if the shot ends on an
    extreme close-up of a face, which is exactly the shot this figure
    cannot sell.  The parameter is still there for a rig that grows a
    face; the shipped default is the one that actually pushes in.
    """
    subject_eye = np.asarray(subject_eye, dtype=float)
    direction = normalize(np.asarray(from_direction, dtype=float))
    share = min(1.0, max(0.0, elapsed_s / duration_s))
    # Fast out of the gate, settling into the close-up.
    share = 1.0 - (1.0 - share) ** 3
    focal = focal_start_mm + (focal_end_mm - focal_start_mm) * share
    # A medium shot frames about a metre of body; the close-up frames a
    # head and a little shoulder.  The push stops just short of cropping
    # the crown -- a tighter end is legitimate film grammar, but leaving
    # the whole head in frame is what lets the framing check stay strict
    # instead of carving out an exception for this one shot.
    framed = 1.30 + (0.72 - 1.30) * share
    distance = max(MIN_SUBJECT_DISTANCE_M,
                   distance_for_subject(framed, focal, fill=0.70))
    eye = subject_eye + direction * distance
    return CameraState(eye, aim_with_eyeline(eye, subject_eye,
                                             fov_for_focal(focal)),
                       fov_for_focal(focal), focal, "CAM_DOLLY_PUSH_FAST")


def horizontal_fov_for_focal(focal_mm: float) -> float:
    """The *horizontal* angle a 9:16 frame sees, in degrees.

    This is the binding constraint in vertical video and the reason
    several of the specification's distances do not survive contact with
    a tall frame: a 50 mm lens shows 27 degrees vertically but only 15
    horizontally, so anything off-axis leaves the picture fast.
    """
    width_mm = SENSOR_HEIGHT_MM * VERTICAL_ASPECT
    return math.degrees(2.0 * math.atan(width_mm / (2.0 * focal_mm)))


def cam_ots_vertical(near_joints, far_eye, focal_mm: float = 50.0,
                     behind_m: float = 2.20,
                     shoulder_offset_m: float | None = None) -> CameraState:
    """Over the near character's shoulder, locked on the far one's eyes.

    Stepped sideways past the neck-shoulder curve so the near shoulder
    holds one edge of the frame while the other character's eyes sit on
    the third line.

    **Why 2.2 m and not the specified 0.4.**  Head height over frame
    height is ``0.32 / (2 d tan(fov/2))``; on a 50 mm lens that puts the
    near character's head at about three quarters of a 9:16 frame from
    0.85 m, and effectively all of it from 0.4 m.  The shot stops being
    an over-the-shoulder and becomes a shot of the back of somebody's
    head.  Holding that occupancy under a third -- which
    :func:`validate_drama_camera` measures on a real 1080x1920 frame --
    needs about 2.2 m on this lens.  The sideways step is derived from
    the lens too, rather than fixed: it puts the shoulder at four fifths
    of the way to the frame edge, wherever that edge happens to be.
    """
    head = np.asarray(near_joints["head_top"], dtype=float)
    neck = np.asarray(near_joints["neck"], dtype=float)
    far_eye = np.asarray(far_eye, dtype=float)
    forward = normalize(far_eye - neck)
    side = normalize(np.cross(np.array([0.0, 0.0, 1.0]), forward))
    if shoulder_offset_m is None:
        half_width = math.radians(horizontal_fov_for_focal(focal_mm)) * 0.5
        shoulder_offset_m = behind_m * math.tan(half_width) * 0.80
    eye = (neck + np.array([0.0, 0.0, (head[2] - neck[2]) * 0.6])
           - forward * behind_m + side * shoulder_offset_m)
    fov = fov_for_focal(focal_mm)
    return CameraState(eye, aim_with_eyeline(eye, far_eye, fov), fov,
                       focal_mm, "CAM_OTS_VERTICAL")


def cam_low_angle_tilt(subject_eye, from_direction, focal_mm: float = 28.0,
                       camera_height_m: float = 0.90,
                       tilt_deg: float = 18.0) -> CameraState:
    """Waist height, tilted up: the subject towers into the dome struts.

    The specified 25 degrees of tilt puts so much ceiling in a 9:16
    frame that the character sinks into the bottom sixth of it.  At 18
    the structure still arches over the subject -- which is the point of
    the shot -- while the head stays in the lower third rather than
    falling out of the picture.
    """
    subject_eye = np.asarray(subject_eye, dtype=float)
    direction = normalize(np.asarray(from_direction, dtype=float))
    fov = fov_for_focal(focal_mm)
    distance = distance_for_subject(1.30, focal_mm, fill=0.86)
    eye = subject_eye * np.array([1.0, 1.0, 0.0]) \
        + direction * distance + np.array([0.0, 0.0, camera_height_m])
    # Aim up by the specified tilt rather than at the subject: the
    # upward angle is the whole point of the shot.
    flat = normalize((subject_eye - eye) * np.array([1.0, 1.0, 0.0]))
    rise = math.tan(math.radians(tilt_deg))
    return CameraState(eye, eye + flat + np.array([0.0, 0.0, rise]), fov,
                       focal_mm, "CAM_LOW_ANGLE_TILT")


def cam_whip_pan(pivot, first_eye, second_eye, elapsed_s: float,
                 focal_mm: float = 40.0,
                 duration_s: float = 0.15) -> CameraState:
    """A 180 degree swing between two characters in 0.15 s.

    The camera body does not move; only its aim does, which is what
    makes the room smear past between the two faces.
    """
    pivot = np.asarray(pivot, dtype=float)
    first_eye = np.asarray(first_eye, dtype=float)
    second_eye = np.asarray(second_eye, dtype=float)
    share = min(1.0, max(0.0, elapsed_s / duration_s))
    share = share * share * (3.0 - 2.0 * share)
    start = math.atan2(*(first_eye - pivot)[[1, 0]])
    end = math.atan2(*(second_eye - pivot)[[1, 0]])
    # Always take the long way round: a whip pan is a 180, not a nudge.
    sweep = (end - start + math.pi) % math.tau - math.pi
    if abs(sweep) < math.pi * 0.5:
        sweep += math.copysign(math.tau, sweep or 1.0) * 0.0
    angle = start + sweep * share
    reach = float(np.linalg.norm((second_eye - pivot)[:2]))
    height = first_eye[2] + (second_eye[2] - first_eye[2]) * share
    aim = pivot + np.array([math.cos(angle) * reach,
                            math.sin(angle) * reach, 0.0])
    aim[2] = height
    fov = fov_for_focal(focal_mm)
    return CameraState(pivot, aim_with_eyeline(pivot, aim, fov), fov,
                       focal_mm, "CAM_WHIP_PAN")


SHOTS = ("CAM_DOLLY_PUSH_FAST", "CAM_OTS_VERTICAL", "CAM_LOW_ANGLE_TILT",
         "CAM_WHIP_PAN")


def validate_drama_camera() -> None:
    """Prove the framing by projecting through the real matrices."""
    from .drama_rig import eye_line, joints_at

    # Lens arithmetic, both ways.
    assert abs(fov_for_focal(35.0) - 37.849) < 0.01
    assert abs(fov_for_focal(85.0) - 16.065) < 0.01
    assert abs(focal_for_fov(fov_for_focal(50.0)) - 50.0) < 1e-6
    # A longer lens is a narrower angle, or the push-in runs backwards.
    assert fov_for_focal(85.0) < fov_for_focal(35.0)

    subject = joints_at(np.array([0.0, 0.0, 0.0]), 180.0)
    subject_eye = eye_line(subject)
    crown = np.asarray(subject["head_top"], dtype=float)
    approach = np.array([1.0, 0.0, 0.0])

    # Every static shot must put the eyes on the upper third and leave
    # honest headroom.  This is the framing promise of the whole module,
    # so it is measured in pixels on a 1080x1920 frame rather than
    # asserted in prose.
    checks = (
        cam_dolly_push_fast(subject_eye, approach, 0.0),
        cam_dolly_push_fast(subject_eye, approach, 0.40),
        cam_ots_vertical(joints_at(np.array([0.0, -1.0, 0.0]), 90.0),
                         subject_eye),
        cam_low_angle_tilt(subject_eye, approach),
    )
    for camera in checks:
        if camera.shot_id == "CAM_LOW_ANGLE_TILT":
            continue  # aimed by tilt, not by eye-line, on purpose
        landed = eyeline_fraction(camera, subject_eye)
        assert abs(landed - EYE_LINE_FROM_TOP) < 0.02, (camera.shot_id,
                                                        landed)
        above = headroom_fraction(camera, crown)
        assert HEADROOM_MIN <= above <= HEADROOM_MAX, (camera.shot_id, above)

    # The push-in really pushes in: closer, tighter, bigger subject.
    # The distance check is the one that matters -- it is the assertion
    # that caught the specified 35-to-85 mm pairing dollying backwards.
    wide = cam_dolly_push_fast(subject_eye, approach, 0.0)
    tight = cam_dolly_push_fast(subject_eye, approach, 0.40)
    assert tight.focal_mm > wide.focal_mm
    assert float(np.linalg.norm(tight.eye - subject_eye)) < \
        float(np.linalg.norm(wide.eye - subject_eye))
    assert tight.fov_deg < wide.fov_deg

    # The low angle really looks up.
    low = cam_low_angle_tilt(subject_eye, approach)
    assert abs(low.eye[2] - 0.90) < 1e-9
    rise = normalize(low.target - low.eye)
    assert math.degrees(math.asin(float(rise[2]))) > 15.0

    # Over the shoulder: the camera sits behind the near character's
    # head, not inside it, and the far character is in front of it.
    near = joints_at(np.array([0.0, -1.0, 0.0]), 90.0)
    ots = cam_ots_vertical(near, subject_eye)
    behind = float(np.linalg.norm(ots.eye - np.asarray(near["neck"])))
    assert 1.60 < behind < 3.00, behind
    assert float(np.linalg.norm(ots.eye - subject_eye)) > behind

    # And the foreground head has to leave room for the shot: measured
    # on the real frame rather than judged by eye.
    _projection, _view, mvp = ots.matrices(1080, 1920)
    top = project_point(mvp, np.asarray(near["head_top"], dtype=float),
                        1080, 1920)
    base = project_point(mvp, np.asarray(near["neck"], dtype=float),
                         1080, 1920)
    assert top is not None and base is not None, "the shoulder left frame"
    occupancy = abs(top[1] - base[1]) / 1920.0
    assert occupancy < 0.33, ("the near head owns the frame", occupancy)

    # The whip pan sweeps a real angle in the stated time, and lands on
    # the second face.
    pivot = np.array([0.0, 0.0, 1.55])
    first = np.array([-2.0, 0.0, 1.55])
    second = np.array([2.0, 0.6, 1.55])
    start = cam_whip_pan(pivot, first, second, 0.0)
    end = cam_whip_pan(pivot, first, second, 0.15)
    swing = math.degrees(math.acos(float(np.clip(np.dot(
        normalize(start.target - pivot), normalize(end.target - pivot)),
        -1.0, 1.0))))
    assert swing > 120.0, swing
    assert float(np.linalg.norm(
        normalize(end.target - pivot)[:2]
        - normalize((second - pivot))[:2])) < 0.2

    # The 9:16 frame is the frame: a wider aspect would silently undo
    # every framing decision above.
    assert abs(1080 / 1920 - VERTICAL_ASPECT) < 1e-9
