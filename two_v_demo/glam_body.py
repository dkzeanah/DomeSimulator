"""The body every glam look is built on, and the landmarks it defines.

:mod:`two_v_demo.figure` builds a skeleton out of sourced anthropometry
and draws it as capsules -- correct for a lesson about lifting, wrong
for a lookbook, because a stack of cylinders has no silhouette.  This
module keeps that skeleton and puts a surface on it: a torso lofted
through elliptical rings that narrow at the waist, tapered limbs, and a
neck.

The one idea worth carrying out of here
---------------------------------------
**A garment is the same rings as the body, pushed out a little.**
:func:`torso_ring` returns the cross-section of the body at a given
height, and :mod:`two_v_demo.glam_wardrobe` lofts its garments through
exactly those rings with an inflation factor.  Clothes therefore cannot
drift out of fit: change the silhouette and every dress in the wardrobe
changes with it, because there is only one description of the body and
both the body and the clothes read it.

**Landmarks** are the other shared idea.  A hem, like a hair length, is
named -- mid-thigh, knee, ankle -- and resolved against the posed
skeleton at draw time, so a mini dress is a mini dress on a 1.62 m woman
and on a 1.80 m one without a second table of numbers anywhere.

On the proportions
------------------
The Drillis and Contini fractions that :mod:`two_v_demo.figure` uses are
a unisex average.  Two of them carry nearly the whole difference in
silhouette between an average male and an average female frame --
shoulder breadth and hip breadth -- and published anthropometric surveys
put those the other way round for women.  :data:`FEMALE_STATURE_FRACTION`
moves those two and leaves every other entry exactly as sourced.  The
moved values are **art direction in the direction the surveys point**,
not measurements, and are labelled as such; the ratio between them is
the thing that has to read on screen, and :func:`validate_glam_body`
checks it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np

from .figure import STATURE_FRACTION, joint_positions
from .geometry import normalize


Colour = tuple[float, float, float, float]


# ----------------------------------------------------------------------
# The frame
# ----------------------------------------------------------------------

FEMALE_STATURE_FRACTION: dict[str, float] = dict(
    STATURE_FRACTION,
    shoulder_width=0.243,
    hip_width=0.207,
)
"""The sourced table with two entries moved.  See the module docstring:
these two are art direction, everything else is Drillis and Contini."""

SHOULDER_TO_HIP = (FEMALE_STATURE_FRACTION["shoulder_width"]
                   / FEMALE_STATURE_FRACTION["hip_width"])
"""Computed, not typed in, so it can never disagree with the table."""


def glam_joints(
    pose,
    stature: float,
    origin=(0.0, 0.0, 0.0),
    yaw_deg: float = 0.0,
    heel_m: float = 0.0,
) -> dict[str, np.ndarray]:
    """Pose a figure on the female frame, standing on a heel if she is.

    A heel does two things and this does both: it lifts the whole body
    by its height, and it lengthens the leg line, which is the entire
    reason anybody wears one.  The lift is applied to the origin so the
    soles land on the heel rather than sinking through it.
    """
    lifted = (float(origin[0]), float(origin[1]), float(origin[2]) + heel_m)
    return joint_positions(pose, stature, lifted, yaw_deg,
                           fractions=FEMALE_STATURE_FRACTION)


@dataclass(frozen=True)
class BodyFrame:
    """Which way a posed figure is facing, in world space."""

    side: np.ndarray
    """Unit vector towards her left."""
    forward: np.ndarray
    """Unit vector out of her front."""
    up: np.ndarray


def body_frame(joints: Mapping[str, np.ndarray]) -> BodyFrame:
    up = np.array([0.0, 0.0, 1.0])
    side = normalize(np.asarray(joints["l_shoulder"], dtype=float)
                     - np.asarray(joints["r_shoulder"], dtype=float))
    forward = normalize(np.cross(side, up))
    return BodyFrame(side, forward, up)


# ----------------------------------------------------------------------
# Landmarks: where a hem stops, and where a hair length stops
# ----------------------------------------------------------------------

def sole_height(joints: Mapping[str, np.ndarray]) -> float:
    """The plane her feet are standing on.

    The ankle joint sits above the sole, and by how much depends on how
    big she is -- so the drop is read off the foot the skeleton actually
    built.  The sourced table gives ankle height and foot length as
    fractions of the same stature, so their ratio is a pure number and
    the measured foot supplies the scale.  Nothing here needs to be told
    how tall she is, which matters because a hem is drawn from joints
    and not from a character record.
    """
    ratio = (FEMALE_STATURE_FRACTION["ankle_height"]
             / FEMALE_STATURE_FRACTION["foot_length"])
    soles = []
    for side in ("l", "r"):
        ankle = np.asarray(joints[f"{side}_ankle"], dtype=float)
        toe = np.asarray(joints[f"{side}_toe"], dtype=float)
        soles.append(float(ankle[2]) - ratio * float(np.linalg.norm(toe - ankle)))
    return min(soles)


def _mid(joints: Mapping[str, np.ndarray], one: str, two: str,
         share: float = 0.5) -> float:
    return float(joints[one][2]) + (
        float(joints[two][2]) - float(joints[one][2])) * share


LANDMARK_HEIGHT: dict[str, Callable[[Mapping[str, np.ndarray]], float]] = {
    "crown": lambda j: float(j["head_top"][2]),
    "ear": lambda j: _mid(j, "neck", "head_top", 0.45),
    "jaw": lambda j: _mid(j, "neck", "head_top", 0.18),
    "chin": lambda j: _mid(j, "neck", "head_top", 0.06),
    "collarbone": lambda j: float(j["chest"][2]) - (
        float(j["head_top"][2]) - float(j["chest"][2])) * 0.10,
    "bust": lambda j: _mid(j, "pelvis", "chest", 0.62),
    "waist": lambda j: _mid(j, "pelvis", "chest", 0.28),
    "hip": lambda j: float(j["pelvis"][2]),
    "mid_thigh": lambda j: _mid(j, "l_hip", "l_knee", 0.55),
    "knee": lambda j: float(j["l_knee"][2]),
    "calf": lambda j: _mid(j, "l_knee", "l_ankle", 0.55),
    "ankle": lambda j: float(j["l_ankle"][2]),
    "floor": lambda j: sole_height(j),
}
"""Every place a hem or a length of hair is allowed to stop, high to low.

Shared deliberately.  A midi dress and a waist-length head of hair are
the same measurement problem, and solving it twice is how the two end up
disagreeing about where a waist is."""

LANDMARK_ORDER: tuple[str, ...] = ("crown", "ear", "jaw", "chin",
                                   "collarbone", "bust", "waist", "hip",
                                   "mid_thigh", "knee", "calf", "ankle",
                                   "floor")


def landmark_height(joints: Mapping[str, np.ndarray], landmark: str) -> float:
    try:
        return LANDMARK_HEIGHT[landmark](joints)
    except KeyError:
        raise ValueError(
            f"unknown landmark {landmark!r}; choose from "
            f"{', '.join(LANDMARK_ORDER)}") from None


# ----------------------------------------------------------------------
# The silhouette
# ----------------------------------------------------------------------

TORSO_PROFILE: tuple[tuple[float, float, float], ...] = (
    (0.00, 0.106, 0.076),
    (0.16, 0.098, 0.070),
    (0.32, 0.078, 0.060),
    (0.50, 0.090, 0.070),
    (0.66, 0.103, 0.084),
    (0.84, 0.098, 0.072),
    (1.00, 0.090, 0.064),
)
"""``(t, half-width, half-depth)`` up the torso, as fractions of stature.

``t`` runs 0 at the hip joint to 1 at the shoulder line.  Half-width is
across her, half-depth is front to back, and the pair being different is
what makes this a body rather than a pipe.  Art direction, sized so the
hip and shoulder rings agree with the frame's own breadth fractions --
which :func:`validate_glam_body` checks rather than assumes."""

LIMB_FRACTION: dict[str, float] = {
    "thigh_top": 0.056,
    "thigh_bottom": 0.038,
    "shank_top": 0.036,
    "shank_bottom": 0.021,
    "upper_arm_top": 0.032,
    "upper_arm_bottom": 0.024,
    "forearm_top": 0.024,
    "forearm_bottom": 0.016,
    "neck": 0.030,
    "hand": 0.024,
    "foot_height": 0.021,
}
"""Limb radii as fractions of stature.  Art direction, and the reason a
drawn arm tapers from the shoulder to the wrist rather than being one
cylinder all the way down."""


def spine_point(joints: Mapping[str, np.ndarray], t: float) -> np.ndarray:
    """A point on the torso centreline, 0 at the pelvis, 1 at the chest.

    Follows the trunk, so it leans and twists with the pose rather than
    standing straight up out of the hips.
    """
    pelvis = np.asarray(joints["pelvis"], dtype=float)
    chest = np.asarray(joints["chest"], dtype=float)
    return pelvis + (chest - pelvis) * t


def torso_radii(stature: float, t: float) -> tuple[float, float]:
    """Half-width and half-depth of the torso at height ``t``."""
    t = max(0.0, min(1.0, t))
    previous = TORSO_PROFILE[0]
    for entry in TORSO_PROFILE:
        if entry[0] >= t:
            span = entry[0] - previous[0]
            share = 0.0 if span <= 1e-9 else (t - previous[0]) / span
            width = previous[1] + (entry[1] - previous[1]) * share
            depth = previous[2] + (entry[2] - previous[2]) * share
            return width * stature, depth * stature
        previous = entry
    return TORSO_PROFILE[-1][1] * stature, TORSO_PROFILE[-1][2] * stature


def torso_ring(
    joints: Mapping[str, np.ndarray],
    stature: float,
    t: float,
    *,
    inflate: float = 1.0,
    padding: float = 0.0,
    segments: int = 16,
    arc: tuple[float, float] | None = None,
) -> np.ndarray:
    """The cross-section of the body at height ``t``, as a ring of points.

    ``inflate`` scales it and ``padding`` adds a fixed thickness in
    metres.  A garment is this ring with both turned up slightly, which
    is the whole reason clothes in this package cannot come out the
    wrong size for the body wearing them.

    ``arc`` is a pair of degrees, and turns the closed ring into an open
    one -- which is how a coat hangs open at the front, how a column
    skirt gets a thigh slit, and how a cape covers the back only.  Zero
    degrees is her left side and ninety is her front.
    """
    frame = body_frame(joints)
    centre = spine_point(joints, t)
    width, depth = torso_radii(stature, t)
    width = width * inflate + padding
    depth = depth * inflate + padding
    return _ellipse(centre, frame, width, depth, segments, arc)


def _ellipse(centre, frame: BodyFrame, width: float, depth: float,
             segments: int, arc: tuple[float, float] | None) -> np.ndarray:
    if arc is None:
        angles = [math.tau * index / segments for index in range(segments)]
    else:
        start, end = (math.radians(value) for value in arc)
        angles = [start + (end - start) * index / segments
                  for index in range(segments + 1)]
    ring = np.empty((len(angles), 3), dtype=float)
    for index, angle in enumerate(angles):
        ring[index] = (centre
                       + frame.side * (width * math.cos(angle))
                       + frame.forward * (depth * math.sin(angle)))
    return ring


def ring_point(
    joints: Mapping[str, np.ndarray],
    stature: float,
    t: float,
    angle_deg: float,
    *,
    inflate: float = 1.0,
    padding: float = 0.0,
) -> np.ndarray:
    """One point on the body surface, by height and by angle around it.

    Used for anything that runs across the body rather than around it:
    a sash from one shoulder to the opposite hip, a placket down the
    centre front, a zip.
    """
    frame = body_frame(joints)
    centre = spine_point(joints, t)
    width, depth = torso_radii(stature, t)
    angle = math.radians(angle_deg)
    return (centre
            + frame.side * ((width * inflate + padding) * math.cos(angle))
            + frame.forward * ((depth * inflate + padding) * math.sin(angle)))


def circle_ring(
    centre: np.ndarray,
    frame: BodyFrame,
    width: float,
    depth: float,
    segments: int = 16,
    arc: tuple[float, float] | None = None,
) -> np.ndarray:
    """A free-standing ring, for hems that have left the body behind."""
    return _ellipse(np.asarray(centre, dtype=float), frame, width, depth,
                    segments, arc)


# ----------------------------------------------------------------------
# Drawing surfaces
# ----------------------------------------------------------------------

def loft(
    batch,
    rings: Sequence[np.ndarray],
    colour: Colour,
    *,
    cap_bottom: bool = False,
    cap_top: bool = False,
    closed: bool = True,
    double_sided: bool = False,
) -> None:
    """Skin a stack of rings into a surface.

    Rings must all have the same number of points and run bottom to top;
    the surface is wound so its normals face outward, which matters
    because the renderer culls back faces -- get the winding backwards
    and every torso in the wardrobe renders as a hollow shell you can
    see straight through.  ``closed`` is False for the open rings an arc
    produces, and ``double_sided`` draws the inside too, which a coat
    hanging open needs or the viewer sees through the back of it.
    """
    for lower, upper in zip(rings, rings[1:]):
        count = len(lower)
        span = count if closed else count - 1
        for index in range(span):
            nxt = (index + 1) % count
            batch.quad(lower[index], upper[index], upper[nxt], lower[nxt],
                       colour)
            if double_sided:
                batch.quad(lower[nxt], upper[nxt], upper[index], lower[index],
                           colour)
    if cap_bottom:
        _cap_ring(batch, rings[0], colour, upward=False)
    if cap_top:
        _cap_ring(batch, rings[-1], colour, upward=True)


def _cap_ring(batch, ring: np.ndarray, colour: Colour, upward: bool) -> None:
    centre = ring.mean(axis=0)
    count = len(ring)
    for index in range(count):
        nxt = (index + 1) % count
        if upward:
            batch.triangle(centre, ring[nxt], ring[index], colour)
        else:
            batch.triangle(centre, ring[index], ring[nxt], colour)


def taper(
    batch,
    start: np.ndarray,
    end: np.ndarray,
    start_radius: float,
    end_radius: float,
    colour: Colour,
    *,
    sides: int = 10,
    cap: bool = True,
) -> None:
    """A cone frustum between two points: every limb segment in one call."""
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    axis = end - start
    length = float(np.linalg.norm(axis))
    if length < 1e-7:
        return
    direction = axis / length
    trial = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(direction, trial))) > 0.90:
        trial = np.array([0.0, 1.0, 0.0])
    tangent = normalize(np.cross(direction, trial))
    # Note the order: ``cross(tangent, direction)``, not the other way
    # round.  The ring has to run the way that makes the lofted quads
    # face outward, and the opposite order is the same tube rendered
    # inside out -- visible as limbs and trousers that vanish, because
    # what survives face culling is the far inner wall of the tube.
    bitangent = normalize(np.cross(tangent, direction))
    lower = np.empty((sides, 3))
    upper = np.empty((sides, 3))
    for index in range(sides):
        angle = math.tau * index / sides
        offset = tangent * math.cos(angle) + bitangent * math.sin(angle)
        lower[index] = start + offset * start_radius
        upper[index] = end + offset * end_radius
    loft(batch, (lower, upper), colour, cap_bottom=cap, cap_top=cap)


def limb_points(
    joints: Mapping[str, np.ndarray],
    limb: str,
    side: str,
    t: float,
) -> np.ndarray:
    """A point along a limb, ``t`` from its proximal to its distal end."""
    ends = {
        "thigh": (f"{side}_hip", f"{side}_knee"),
        "shank": (f"{side}_knee", f"{side}_ankle"),
        "leg": (f"{side}_hip", f"{side}_ankle"),
        "upper_arm": (f"{side}_shoulder", f"{side}_elbow"),
        "forearm": (f"{side}_elbow", f"{side}_wrist"),
        "arm": (f"{side}_shoulder", f"{side}_wrist"),
    }
    try:
        first, second = ends[limb]
    except KeyError:
        raise ValueError(f"unknown limb {limb!r}; choose from "
                         f"{', '.join(sorted(ends))}") from None
    start = np.asarray(joints[first], dtype=float)
    finish = np.asarray(joints[second], dtype=float)
    return start + (finish - start) * max(0.0, min(1.0, t))


def limb_radius(stature: float, limb: str, t: float) -> float:
    """How thick a limb is at ``t`` along it, tapering as it goes."""
    pairs = {
        "thigh": ("thigh_top", "thigh_bottom"),
        "shank": ("shank_top", "shank_bottom"),
        "leg": ("thigh_top", "shank_bottom"),
        "upper_arm": ("upper_arm_top", "upper_arm_bottom"),
        "forearm": ("forearm_top", "forearm_bottom"),
        "arm": ("upper_arm_top", "forearm_bottom"),
    }
    top, bottom = pairs[limb]
    t = max(0.0, min(1.0, t))
    return (LIMB_FRACTION[top]
            + (LIMB_FRACTION[bottom] - LIMB_FRACTION[top]) * t) * stature


def head_shape(joints: Mapping[str, np.ndarray]):
    """The head as an egg, agreeing with the face rig about where it is.

    :func:`two_v_demo.drama_face.head_frame` decides where the eyes and
    the mouth go, and hair is rooted on the same sphere, so the head this
    module draws has to be that sphere or the features float.  It is that
    sphere -- widened nowhere, and stretched upward only, from the bottom
    of it to the crown joint.  A real skull is taller than it is wide and
    the sphere alone leaves the top of her head missing, which shows up
    as a figure that measures short of her own stature.
    """
    from .drama_face import head_frame

    centre, forward, side, up, radius = head_frame(joints)
    centre = np.asarray(centre, dtype=float)
    bottom = centre - up * radius
    top = np.asarray(joints["head_top"], dtype=float)
    half_height = max(radius, float(np.dot(top - bottom, up)) * 0.5)
    return bottom + up * half_height, float(radius), half_height


def draw_head(batch, joints: Mapping[str, np.ndarray], skin: Colour,
              rows: int = 9, segments: int = 14) -> None:
    """Draw that egg as a lofted surface."""
    centre, radius, half_height = head_shape(joints)
    frame = body_frame(joints)
    rings = []
    for index in range(rows + 1):
        share = -0.985 + 1.970 * index / rows
        span = radius * math.sqrt(max(0.0, 1.0 - share * share))
        rings.append(circle_ring(centre + frame.up * (share * half_height),
                                 frame, span, span, segments))
    loft(batch, rings, skin, cap_bottom=True, cap_top=True)


def draw_body(
    batch,
    joints: Mapping[str, np.ndarray],
    stature: float,
    skin: Colour,
    *,
    rings: int = 12,
    segments: int = 16,
) -> None:
    """The body itself: torso, limbs, neck and head, with no clothes.

    This is also what the wardrobe's studio-form look draws, and it is
    what every other look is drawn on top of, so a garment that does not
    quite close still has a body behind it rather than a hole.
    """
    stack = [torso_ring(joints, stature, index / rings, segments=segments)
             for index in range(rings + 1)]
    loft(batch, stack, skin, cap_bottom=True, cap_top=True)

    for side in ("l", "r"):
        for limb, steps in (("thigh", 3), ("shank", 3)):
            for step in range(steps):
                low = step / steps
                high = (step + 1) / steps
                taper(batch,
                      limb_points(joints, limb, side, low),
                      limb_points(joints, limb, side, high),
                      limb_radius(stature, limb, low),
                      limb_radius(stature, limb, high),
                      skin, sides=9, cap=False)
        for limb in ("upper_arm", "forearm"):
            taper(batch,
                  limb_points(joints, limb, side, 0.0),
                  limb_points(joints, limb, side, 1.0),
                  limb_radius(stature, limb, 0.0),
                  limb_radius(stature, limb, 1.0),
                  skin, sides=8, cap=False)
        # Joints, so the tapers read as connected rather than as a stack.
        batch.sphere(joints[f"{side}_knee"],
                     limb_radius(stature, "shank", 0.0) * 0.98, skin, 4, 8)
        batch.sphere(joints[f"{side}_elbow"],
                     limb_radius(stature, "forearm", 0.0) * 0.98, skin, 4, 7)
        batch.sphere(joints[f"{side}_shoulder"],
                     limb_radius(stature, "upper_arm", 0.0) * 0.96, skin, 4, 8)
        batch.sphere(joints[f"{side}_hip"],
                     limb_radius(stature, "thigh", 0.0) * 0.88, skin, 4, 8)
        # The yoke.  The shoulder joint sits a good way outside the top
        # of the ribcage -- that gap is what shoulder breadth *is* -- so
        # without something spanning it the arms hang off the body with
        # daylight between.
        batch_side = 0.0 if side == "l" else 180.0
        batch.sphere(ring_point(joints, stature, 0.97, batch_side),
                     limb_radius(stature, "upper_arm", 0.0) * 0.9, skin, 4, 8)
        taper(batch,
              ring_point(joints, stature, 0.94, batch_side),
              np.asarray(joints[f"{side}_shoulder"], dtype=float),
              limb_radius(stature, "upper_arm", 0.0) * 1.15,
              limb_radius(stature, "upper_arm", 0.0) * 0.98,
              skin, sides=9, cap=False)
        # Hands and feet.
        batch.sphere(joints[f"{side}_grip"],
                     LIMB_FRACTION["hand"] * stature, skin, 4, 7)
        heel = np.asarray(joints[f"{side}_ankle"], dtype=float)
        toe = np.asarray(joints[f"{side}_toe"], dtype=float)
        foot_height = LIMB_FRACTION["foot_height"] * stature
        taper(batch, heel, toe, foot_height, foot_height * 0.55, skin,
              sides=7)

    neck_top = np.asarray(joints["neck"], dtype=float) + np.array(
        [0.0, 0.0, LIMB_FRACTION["neck"] * stature * 1.4])
    taper(batch, joints["neck"], neck_top,
          LIMB_FRACTION["neck"] * stature,
          LIMB_FRACTION["neck"] * stature * 0.86, skin, sides=9, cap=False)

    draw_head(batch, joints, skin)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_glam_body() -> None:
    """Prove the frame, the landmarks and the rings before anything wears
    them."""
    from .figure import POSES
    from .render_kit import TriangleBatch

    # Only the two silhouette fractions moved; everything else is still
    # the sourced table, which is the claim the docstring makes.
    moved = {key for key in FEMALE_STATURE_FRACTION
             if FEMALE_STATURE_FRACTION[key] != STATURE_FRACTION[key]}
    assert moved == {"shoulder_width", "hip_width"}, moved
    assert set(FEMALE_STATURE_FRACTION) == set(STATURE_FRACTION)
    # And they moved the way the surveys point: narrower shoulders and
    # wider hips than the unisex average, so the ratio comes down.
    unisex = (STATURE_FRACTION["shoulder_width"]
              / STATURE_FRACTION["hip_width"])
    assert SHOULDER_TO_HIP < unisex, (SHOULDER_TO_HIP, unisex)
    assert 1.10 < SHOULDER_TO_HIP < 1.30, SHOULDER_TO_HIP

    stature = 1.70
    joints = glam_joints(POSES["stand"], stature)
    # The heel lifts the whole body and nothing else about the pose.
    on_heels = glam_joints(POSES["stand"], stature, heel_m=0.10)
    for name in joints:
        rise = float(on_heels[name][2] - joints[name][2])
        assert abs(rise - 0.10) < 1e-6, (name, rise)

    # Landmarks descend in the order they are listed, and the whole
    # ladder lies between the floor and the crown.
    heights = [landmark_height(joints, name) for name in LANDMARK_ORDER]
    for first, second in zip(heights, heights[1:]):
        assert second < first, (first, second)
    assert heights[0] <= stature + 1e-6
    assert heights[-1] < 0.02
    try:
        landmark_height(joints, "elbow")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown landmark has to be refused")

    # The profile is a body: it narrows at the waist and comes back out.
    waist = torso_radii(stature, 0.32)[0]
    hip = torso_radii(stature, 0.0)[0]
    bust = torso_radii(stature, 0.66)[0]
    assert waist < hip and waist < bust, (waist, hip, bust)
    # Depth is always less than width -- a torso is an ellipse, and the
    # day this stops being true it has become a pipe.
    for step in range(11):
        width, depth = torso_radii(stature, step / 10.0)
        assert depth < width, (step, width, depth)

    # The rings agree with the frame's own breadth fractions rather than
    # being a second, quietly different, opinion about how wide she is.
    hip_span = hip * 2.0
    assert abs(hip_span
               - FEMALE_STATURE_FRACTION["hip_width"] * stature) < 0.02, hip_span
    shoulder_span = torso_radii(stature, 1.0)[0] * 2.0
    assert shoulder_span < FEMALE_STATURE_FRACTION[
        "shoulder_width"] * stature, "the torso ends inside the shoulders"

    # A ring is centred on the spine, closed, and inflates outward.
    ring = torso_ring(joints, stature, 0.5, segments=16)
    assert ring.shape == (16, 3)
    centre = spine_point(joints, 0.5)
    assert float(np.linalg.norm(ring.mean(axis=0) - centre)) < 1e-9
    bigger = torso_ring(joints, stature, 0.5, inflate=1.2)
    assert (np.linalg.norm(bigger - centre, axis=1)
            > np.linalg.norm(ring - centre, axis=1) - 1e-9).all()
    padded = torso_ring(joints, stature, 0.5, padding=0.05)
    assert (np.linalg.norm(padded - centre, axis=1)
            > np.linalg.norm(ring - centre, axis=1)).all()

    # An arc is an open ring: it has one more point than it has spans,
    # and it stops where it was told to.
    opened = torso_ring(joints, stature, 0.5, segments=12, arc=(30.0, 330.0))
    assert opened.shape == (13, 3)
    frame_here = body_frame(joints)
    assert np.allclose(opened[0], ring_point(joints, stature, 0.5, 30.0))
    assert np.allclose(opened[-1], ring_point(joints, stature, 0.5, 330.0))
    # And a point looked up by angle is the point on that ring.
    straight_out = ring_point(joints, stature, 0.5, 90.0)
    assert float(np.dot(straight_out - centre, frame_here.forward)) > 0.0
    assert abs(float(np.dot(straight_out - centre, frame_here.side))) < 1e-9

    # The frame points where it says it does: her left, and her front.
    frame = body_frame(joints)
    assert float(np.dot(frame.side,
                        joints["l_shoulder"] - joints["r_shoulder"])) > 0
    assert abs(float(np.dot(frame.side, frame.forward))) < 1e-9
    assert abs(float(np.linalg.norm(frame.forward)) - 1.0) < 1e-9
    # A figure built facing +X faces +X.
    assert float(np.dot(frame.forward, np.array([1.0, 0.0, 0.0]))) > 0.99
    turned = body_frame(glam_joints(POSES["stand"], stature, yaw_deg=90.0))
    assert float(np.dot(turned.forward, np.array([0.0, 1.0, 0.0]))) > 0.99

    # Limbs taper, and a limb point at 0 and 1 is the joint itself.
    assert limb_radius(stature, "arm", 0.0) > limb_radius(stature, "arm", 1.0)
    assert float(np.linalg.norm(
        limb_points(joints, "thigh", "l", 0.0) - joints["l_hip"])) < 1e-9
    assert float(np.linalg.norm(
        limb_points(joints, "forearm", "r", 1.0) - joints["r_wrist"])) < 1e-9
    try:
        limb_points(joints, "tail", "l", 0.5)
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown limb has to be refused")

    # Every surface faces outward.  This is the check that would have
    # caught a whole wardrobe rendering as hollow shells: take the torso
    # on its own and confirm each triangle's normal points away from the
    # spine rather than into it.
    shell = TriangleBatch()
    stack = [torso_ring(joints, stature, index / 8.0) for index in range(9)]
    loft(shell, stack, (0.5, 0.4, 0.3, 1.0))
    rows = np.asarray(shell.vertices, dtype=float).reshape(-1, 10)
    outward = 0
    for start in range(0, len(rows), 3):
        point = rows[start, :3]
        normal = rows[start, 3:6]
        axis = spine_point(joints, 0.5)
        radial = np.array([point[0] - axis[0], point[1] - axis[1], 0.0])
        if float(np.dot(radial, normal)) > 0.0:
            outward += 1
    assert outward == len(rows) // 3, (outward, len(rows) // 3)

    # A tapered tube faces outward too, and its end caps face out of
    # their own ends.
    tube = TriangleBatch()
    taper(tube, np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 0.0]),
          0.10, 0.06, (0.5, 0.4, 0.3, 1.0), sides=8, cap=True)
    tube_rows = np.asarray(tube.vertices, dtype=float).reshape(-1, 10)
    axis_point = np.array([0.0, 0.0, 0.5])
    for start in range(0, len(tube_rows), 3):
        point = tube_rows[start, :3]
        normal = tube_rows[start, 3:6]
        radial = np.array([point[0], point[1], 0.0])
        if float(np.linalg.norm(radial)) < 1e-6:
            continue
        outward_here = float(np.dot(radial, normal))
        upward_here = float(normal[2])
        # Either it faces away from the axis, or it is an end cap
        # facing out of its end.
        assert outward_here > -1e-9 or abs(upward_here) > 0.9, (
            point, normal)
    del axis_point

    # A cap faces the way it was asked to.
    lid = TriangleBatch()
    loft(lid, stack[-2:], (0.5, 0.4, 0.3, 1.0), cap_top=True)
    lid_rows = np.asarray(lid.vertices, dtype=float).reshape(-1, 10)
    assert float(lid_rows[-1, 5]) > 0.0, "a top cap points up"

    # The arms are attached: no daylight between the top of the torso
    # and the shoulder joint, which is what the yoke is for.
    attached = TriangleBatch()
    draw_body(attached, joints, stature, (0.5, 0.4, 0.3, 1.0))
    cloud = np.asarray(attached.vertices, dtype=float).reshape(-1, 10)[:, :3]
    shoulder = np.asarray(joints["l_shoulder"], dtype=float)
    edge = ring_point(joints, stature, 0.97, 0.0)
    midpoint = (shoulder + edge) * 0.5
    nearest = float(np.linalg.norm(cloud - midpoint, axis=1).min())
    assert nearest < limb_radius(stature, "upper_arm", 0.0), nearest

    # The body draws, stands on the floor, and is her own height.
    batch = TriangleBatch()
    draw_body(batch, joints, stature, (0.5, 0.4, 0.3, 1.0))
    points = np.asarray(batch.vertices, dtype=float).reshape(-1, 10)[:, :3]
    assert points[:, 2].min() > -0.06, points[:, 2].min()
    assert abs(points[:, 2].max() - stature) < 0.06, points[:, 2].max()
    reach = np.linalg.norm(points[:, :2], axis=1).max()
    assert reach < stature * 0.35, reach

    # On a heel, she is taller by the heel and still on the floor.
    tall = TriangleBatch()
    draw_body(tall, on_heels, stature, (0.5, 0.4, 0.3, 1.0))
    high = np.asarray(tall.vertices, dtype=float).reshape(-1, 10)[:, :3]
    assert abs(high[:, 2].max() - (points[:, 2].max() + 0.10)) < 1e-6

    # Poses other than standing still produce a body that holds together.
    for name in ("stride", "carry", "reach_out"):
        moving = glam_joints(POSES[name], stature)
        other = TriangleBatch()
        draw_body(other, moving, stature, (0.5, 0.4, 0.3, 1.0))
        assert other.vertices, name


if __name__ == "__main__":
    validate_glam_body()
    print(f"female shoulder-to-hip ratio {SHOULDER_TO_HIP:.3f}")
