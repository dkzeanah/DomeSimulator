"""An articulated human figure: skeleton, poses, and forward kinematics.

The assembly-line world draws its workers as a rigid capsule with no arms
at all (``assembly_line.build_worker_mesh``).  That is fine for showing
where a worker *is*; it cannot show what a worker *does*.  This module
builds a jointed figure instead, so a task can be played out limb by limb
and — because every segment's centre of mass is known at every instant —
so the work each limb performs can be measured off the animation rather
than guessed at.

Where the body proportions come from
------------------------------------
Segment lengths are the Drillis and Contini fractions of stature, and
segment masses are Winter's fractions of body mass (*Biomechanics and
Motor Control of Human Movement*, Table 4.1).  **These are external
anthropometric reference data, not anything this repository derives.**
They are stated here as constants so every number downstream can be
traced back to a named source rather than to a guess.

Everything else in this module — joint positions, segment centres of
mass, how far each one travels — is computed from those constants and the
pose, and :func:`validate_figure` proves the results hold together.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Mapping

import numpy as np

from .render_kit import TriangleBatch


# ----------------------------------------------------------------------
# External reference data
# ----------------------------------------------------------------------

# Drillis & Contini (1966): segment lengths as a fraction of stature.
STATURE_FRACTION = {
    "ankle_height": 0.039,
    "knee_height": 0.285,
    "hip_height": 0.530,
    "shoulder_height": 0.818,
    "head_top": 1.000,
    "thigh": 0.245,
    "shank": 0.246,
    "foot_length": 0.152,
    "upper_arm": 0.186,
    "forearm": 0.146,
    "hand": 0.108,
    "shoulder_width": 0.259,
    "hip_width": 0.191,
    "head": 0.130,
    # Acromion to the top of the head: what is left of stature above the
    # shoulder line.  The 0.130 "head" figure above is chin-to-vertex and
    # leaves the neck out, which would build a figure 9 cm short.
    "neck_to_vertex": 1.000 - 0.818,
}

# Winter, Table 4.1: segment mass as a fraction of total body mass.
# These are *per segment*, so one thigh is 0.100 of body mass and the pair
# is 0.200.  Both legs then come to 0.322, both arms to 0.100, and the
# trunk with head and neck to 0.578, which is the whole body exactly once.
SEGMENT_MASS_FRACTION = {
    "foot": 0.0145,
    "shank": 0.0465,
    "thigh": 0.1000,
    "trunk": 0.4970,
    "head": 0.0810,
    "upper_arm": 0.0280,
    "forearm": 0.0160,
    "hand": 0.0060,
}

# Winter, Table 4.1: centre of mass along the segment, measured from its
# proximal (nearer the trunk) end, as a fraction of segment length.
SEGMENT_COM_FRACTION = {
    "foot": 0.500,
    "shank": 0.433,
    "thigh": 0.433,
    "trunk": 0.500,
    "head": 0.500,
    "upper_arm": 0.436,
    "forearm": 0.430,
    "hand": 0.506,
}

GRAVITY = 9.80665


# ----------------------------------------------------------------------
# The skeleton
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Segment:
    """One rigid piece of the body, drawn between two named joints."""

    name: str
    start: str
    end: str
    mass_key: str
    radius: float
    paired: bool
    """True for a segment that exists on both sides of the body."""

    def mass(self, body_mass: float) -> float:
        return SEGMENT_MASS_FRACTION[self.mass_key] * body_mass


SEGMENTS: tuple[Segment, ...] = (
    Segment("l_thigh", "l_hip", "l_knee", "thigh", 0.058, True),
    Segment("r_thigh", "r_hip", "r_knee", "thigh", 0.058, True),
    Segment("l_shank", "l_knee", "l_ankle", "shank", 0.046, True),
    Segment("r_shank", "r_knee", "r_ankle", "shank", 0.046, True),
    Segment("l_foot", "l_ankle", "l_toe", "foot", 0.036, True),
    Segment("r_foot", "r_ankle", "r_toe", "foot", 0.036, True),
    Segment("trunk", "pelvis", "chest", "trunk", 0.105, False),
    Segment("head", "neck", "head_top", "head", 0.072, False),
    Segment("l_upper_arm", "l_shoulder", "l_elbow", "upper_arm", 0.040, True),
    Segment("r_upper_arm", "r_shoulder", "r_elbow", "upper_arm", 0.040, True),
    Segment("l_forearm", "l_elbow", "l_wrist", "forearm", 0.034, True),
    Segment("r_forearm", "r_elbow", "r_wrist", "forearm", 0.034, True),
    Segment("l_hand", "l_wrist", "l_grip", "hand", 0.030, True),
    Segment("r_hand", "r_wrist", "r_grip", "hand", 0.030, True),
)

# Which limb group each segment belongs to, for reporting energy by limb.
LIMB_GROUP = {
    "l_thigh": "legs", "r_thigh": "legs",
    "l_shank": "legs", "r_shank": "legs",
    "l_foot": "legs", "r_foot": "legs",
    "trunk": "trunk", "head": "trunk",
    "l_upper_arm": "arms", "r_upper_arm": "arms",
    "l_forearm": "arms", "r_forearm": "arms",
    "l_hand": "arms", "r_hand": "arms",
}
LIMB_GROUPS = ("legs", "trunk", "arms")


# ----------------------------------------------------------------------
# Poses
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Pose:
    """Joint angles in degrees, in the sagittal plane unless noted.

    Positive flexion is forward for hips, shoulders and the trunk; knees
    and elbows only bend one way, so their values are always positive.
    """

    l_hip: float = 0.0
    r_hip: float = 0.0
    l_knee: float = 0.0
    r_knee: float = 0.0
    l_ankle: float = 0.0
    r_ankle: float = 0.0
    trunk_lean: float = 0.0
    trunk_twist: float = 0.0
    neck: float = 0.0
    l_shoulder: float = 0.0
    r_shoulder: float = 0.0
    l_shoulder_out: float = 6.0
    r_shoulder_out: float = 6.0
    l_elbow: float = 0.0
    r_elbow: float = 0.0
    hip_drop: float = 0.0
    """Extra lowering of the pelvis, in metres, for a deep squat or kneel."""

    def blend(self, other: "Pose", amount: float) -> "Pose":
        amount = min(1.0, max(0.0, amount))
        values = {}
        for field in self.__dataclass_fields__:
            a = getattr(self, field)
            b = getattr(other, field)
            values[field] = a + (b - a) * amount
        return Pose(**values)


def mirrored(pose: Pose) -> Pose:
    """Swap left and right, for the opposite phase of a walk cycle."""
    return replace(
        pose,
        l_hip=pose.r_hip, r_hip=pose.l_hip,
        l_knee=pose.r_knee, r_knee=pose.l_knee,
        l_ankle=pose.r_ankle, r_ankle=pose.l_ankle,
        l_shoulder=pose.r_shoulder, r_shoulder=pose.l_shoulder,
        l_elbow=pose.r_elbow, r_elbow=pose.l_elbow,
    )


POSES: dict[str, Pose] = {
    # Neutral standing, arms hanging.
    "stand": Pose(l_elbow=8.0, r_elbow=8.0),
    # Mid-stride, right leg forward.
    "stride": Pose(
        l_hip=-18.0, r_hip=24.0, l_knee=12.0, r_knee=14.0,
        l_ankle=-8.0, r_ankle=6.0, trunk_lean=6.0,
        l_shoulder=22.0, r_shoulder=-20.0, l_elbow=26.0, r_elbow=20.0,
    ),
    # Both feet down, body passing over them.
    "stride_pass": Pose(
        l_hip=2.0, r_hip=-2.0, l_knee=6.0, r_knee=18.0,
        trunk_lean=5.0, l_shoulder=2.0, r_shoulder=-2.0,
        l_elbow=18.0, r_elbow=18.0,
    ),
    # Knees bent, back straight, hands at shin height: the correct lift.
    "squat_deep": Pose(
        l_hip=88.0, r_hip=88.0, l_knee=104.0, r_knee=104.0,
        l_ankle=-22.0, r_ankle=-22.0, trunk_lean=32.0,
        l_shoulder=-40.0, r_shoulder=-40.0, l_elbow=30.0, r_elbow=30.0,
        neck=-14.0, hip_drop=0.36,
    ),
    # Halfway up out of the squat, load in hand.
    "squat_mid": Pose(
        l_hip=46.0, r_hip=46.0, l_knee=56.0, r_knee=56.0,
        l_ankle=-12.0, r_ankle=-12.0, trunk_lean=20.0,
        l_shoulder=-28.0, r_shoulder=-28.0, l_elbow=48.0, r_elbow=48.0,
        neck=-6.0, hip_drop=0.17,
    ),
    # Standing with the load held against the belt.
    "carry": Pose(
        l_hip=4.0, r_hip=4.0, l_knee=8.0, r_knee=8.0, trunk_lean=8.0,
        l_shoulder=-16.0, r_shoulder=-16.0, l_elbow=68.0, r_elbow=68.0,
    ),
    # Stooping from the waist with the knees nearly straight: the wrong
    # lift, kept in the vocabulary because the lesson contrasts the two.
    # The thighs stay upright here -- in a stoop the hip flexion shows up
    # as the trunk folding over stationary legs, not as the thigh swinging
    # forward the way it does in a squat.
    "stoop": Pose(
        l_hip=4.0, r_hip=4.0, l_knee=14.0, r_knee=14.0,
        trunk_lean=78.0,
        l_shoulder=-62.0, r_shoulder=-62.0, l_elbow=12.0, r_elbow=12.0,
        neck=-30.0,
    ),
    # Both arms overhead, placing into the shell.
    "reach_high": Pose(
        l_hip=-6.0, r_hip=-6.0, l_knee=4.0, r_knee=4.0,
        l_ankle=8.0, r_ankle=8.0, trunk_lean=-12.0,
        l_shoulder=122.0, r_shoulder=122.0,
        l_shoulder_out=16.0, r_shoulder_out=16.0,
        l_elbow=62.0, r_elbow=62.0, neck=26.0,
    ),
    # Arms out at chest height, positioning a panel.
    "reach_out": Pose(
        l_hip=2.0, r_hip=2.0, l_knee=10.0, r_knee=10.0, trunk_lean=10.0,
        l_shoulder=10.0, r_shoulder=10.0, l_elbow=90.0, r_elbow=90.0,
    ),
    # Down on one knee for floor and fixture work.
    "kneel": Pose(
        l_hip=92.0, r_hip=6.0, l_knee=132.0, r_knee=88.0,
        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=22.0,
        l_shoulder=-14.0, r_shoulder=-14.0, l_elbow=22.0, r_elbow=22.0,
        neck=-18.0, hip_drop=0.44,
    ),
    # Kneeling, one hand steadying, the other driving a fastener.
    "fasten": Pose(
        l_hip=90.0, r_hip=6.0, l_knee=130.0, r_knee=86.0,
        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=28.0,
        l_shoulder=-22.0, r_shoulder=-32.0,
        l_elbow=44.0, r_elbow=18.0, neck=-22.0, hip_drop=0.44,
    ),
    # Standing, one arm up driving a fastener overhead.
    "fasten_high": Pose(
        l_hip=-4.0, r_hip=-4.0, l_knee=6.0, r_knee=6.0,
        trunk_lean=-8.0, l_shoulder=-18.0, r_shoulder=132.0,
        r_shoulder_out=18.0, l_elbow=52.0, r_elbow=36.0, neck=22.0,
    ),
    # Two-man carry: load at hip height, body turned into the direction
    # of travel, outside arm free.
    "team_carry": Pose(
        l_hip=6.0, r_hip=6.0, l_knee=10.0, r_knee=10.0,
        trunk_lean=6.0, trunk_twist=14.0,
        l_shoulder=-30.0, r_shoulder=-10.0,
        l_elbow=14.0, r_elbow=52.0,
    ),
}


def walk_pose(phase: float) -> Pose:
    """A continuous walk cycle: ``phase`` runs 0..1 over one full stride."""
    phase = phase % 1.0
    stride, passing = POSES["stride"], POSES["stride_pass"]
    if phase < 0.25:
        return stride.blend(passing, phase / 0.25)
    if phase < 0.5:
        return passing.blend(mirrored(stride), (phase - 0.25) / 0.25)
    if phase < 0.75:
        return mirrored(stride).blend(mirrored(passing), (phase - 0.5) / 0.25)
    return mirrored(passing).blend(stride, (phase - 0.75) / 0.25)


# ----------------------------------------------------------------------
# Forward kinematics
# ----------------------------------------------------------------------

def _rotate(vector: np.ndarray, pitch_deg: float) -> np.ndarray:
    """Rotate in the sagittal plane: +X forward, +Z up, pitch about -Y."""
    angle = math.radians(pitch_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    return np.array([
        vector[0] * cos + vector[2] * sin,
        vector[1],
        -vector[0] * sin + vector[2] * cos,
    ])


def _swing(pitch_deg: float) -> np.ndarray:
    """A limb hanging down, flexed forward by ``pitch_deg``.

    Rotating the up-vector by a positive angle tips it forward, but doing
    the same to the down-vector tips the far end *backward* -- the two
    differ by a sign.  Every limb below hangs from its joint, so they all
    go through here and nothing has to remember which way is which.
    """
    return _rotate(np.array([0.0, 0.0, -1.0]), -pitch_deg)


def joint_positions(
    pose: Pose,
    stature: float = 1.75,
    origin=(0.0, 0.0, 0.0),
    yaw_deg: float = 0.0,
    ground: bool = True,
) -> dict[str, np.ndarray]:
    """Every joint of the figure in world space, for one pose.

    The figure is built in a local frame facing +X, then turned by
    ``yaw_deg`` and dropped so its lowest foot point sits on the origin's
    height.  Grounding is what keeps a squat from floating: the pelvis is
    lowered by the pose, and the whole body is then lifted back until the
    feet touch again.
    """
    f = STATURE_FRACTION
    down = np.array([0.0, 0.0, -1.0])
    up = np.array([0.0, 0.0, 1.0])
    joints: dict[str, np.ndarray] = {}

    pelvis = np.array([0.0, 0.0, f["hip_height"] * stature - pose.hip_drop])
    joints["pelvis"] = pelvis
    hip_half = f["hip_width"] * stature * 0.5

    for side, sign in (("l", 1.0), ("r", -1.0)):
        hip = pelvis + np.array([0.0, sign * hip_half, 0.0])
        joints[f"{side}_hip"] = hip
        hip_flex = getattr(pose, f"{side}_hip")
        thigh_dir = _swing(hip_flex)
        knee = hip + thigh_dir * (f["thigh"] * stature)
        joints[f"{side}_knee"] = knee
        # A knee only bends backwards, which in this frame means the
        # shank trails the thigh by the knee angle.
        shank_dir = _swing(hip_flex - getattr(pose, f"{side}_knee"))
        ankle = knee + shank_dir * (f["shank"] * stature)
        joints[f"{side}_ankle"] = ankle
        foot_dir = _rotate(np.array([1.0, 0.0, 0.0]),
                           getattr(pose, f"{side}_ankle"))
        joints[f"{side}_toe"] = ankle + foot_dir * (f["foot_length"] * stature)

    trunk_len = (f["shoulder_height"] - f["hip_height"]) * stature
    trunk_dir = _rotate(up, pose.trunk_lean)
    chest = pelvis + trunk_dir * trunk_len
    joints["chest"] = chest
    joints["neck"] = chest
    head_dir = _rotate(up, pose.trunk_lean + pose.neck)
    joints["head_top"] = chest + head_dir * (f["neck_to_vertex"] * stature)

    shoulder_half = f["shoulder_width"] * stature * 0.5
    twist = math.radians(pose.trunk_twist)
    across = np.array([-math.sin(twist), math.cos(twist), 0.0])
    for side, sign in (("l", 1.0), ("r", -1.0)):
        shoulder = chest + across * (sign * shoulder_half)
        joints[f"{side}_shoulder"] = shoulder
        flex = getattr(pose, f"{side}_shoulder")
        out = math.radians(getattr(pose, f"{side}_shoulder_out")) * sign
        arm_dir = _swing(pose.trunk_lean + flex)
        arm_dir = arm_dir + across * math.sin(out)
        arm_dir = arm_dir / float(np.linalg.norm(arm_dir))
        elbow = shoulder + arm_dir * (f["upper_arm"] * stature)
        joints[f"{side}_elbow"] = elbow
        # A knee folds the shank backwards, but an elbow folds the
        # forearm *forwards*, so the two joints take opposite signs.
        fore_dir = _swing(pose.trunk_lean + flex
                          + getattr(pose, f"{side}_elbow"))
        fore_dir = fore_dir + across * math.sin(out * 0.5)
        fore_dir = fore_dir / float(np.linalg.norm(fore_dir))
        wrist = elbow + fore_dir * (f["forearm"] * stature)
        joints[f"{side}_wrist"] = wrist
        joints[f"{side}_grip"] = wrist + fore_dir * (f["hand"] * stature * 0.6)

    if ground:
        lowest = min(
            float(joints[name][2])
            for name in ("l_ankle", "r_ankle", "l_toe", "r_toe")
        )
        # The ankle sits a little above the sole.
        lift = -(lowest - f["ankle_height"] * stature)
        for name in joints:
            joints[name] = joints[name] + np.array([0.0, 0.0, lift])

    angle = math.radians(yaw_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    base = np.asarray(origin, dtype=np.float64)
    turned: dict[str, np.ndarray] = {}
    for name, point in joints.items():
        turned[name] = base + np.array([
            point[0] * cos - point[1] * sin,
            point[0] * sin + point[1] * cos,
            point[2],
        ])
    return turned


def segment_centres(
    joints: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Centre of mass of every segment, from its two end joints."""
    centres: dict[str, np.ndarray] = {}
    for segment in SEGMENTS:
        start = joints[segment.start]
        end = joints[segment.end]
        fraction = SEGMENT_COM_FRACTION[segment.mass_key]
        centres[segment.name] = start + (end - start) * fraction
    return centres


def body_centre(joints: Mapping[str, np.ndarray], body_mass: float = 1.0):
    """Whole-body centre of mass, mass-weighted over every segment."""
    centres = segment_centres(joints)
    total = 0.0
    weighted = np.zeros(3)
    for segment in SEGMENTS:
        mass = segment.mass(body_mass)
        weighted += centres[segment.name] * mass
        total += mass
    return weighted / total


def grip_point(joints: Mapping[str, np.ndarray]) -> np.ndarray:
    """Where a carried object sits: midway between the two hands."""
    return (joints["l_grip"] + joints["r_grip"]) * 0.5


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------

def place_figure(
    joints: Mapping[str, np.ndarray],
    origin,
    yaw_deg: float = 0.0,
) -> dict[str, np.ndarray]:
    """Move a posed figure to a spot on the floor, facing a direction.

    The pose functions all build a figure standing at the origin facing
    +X, because a pose is about the body and not about where the body
    is. This is what puts it somewhere.
    """
    angle = math.radians(yaw_deg)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    origin = np.asarray(origin, dtype=np.float64)
    placed: dict[str, np.ndarray] = {}
    for name, point in joints.items():
        x, y, z = float(point[0]), float(point[1]), float(point[2])
        placed[name] = origin + np.array(
            [x * cos_a - y * sin_a, x * sin_a + y * cos_a, z]
        )
    return placed


def draw_figure(
    batch: TriangleBatch,
    joints: Mapping[str, np.ndarray],
    *,
    skin=(0.87, 0.66, 0.50, 1.0),
    hi_vis=(1.00, 0.45, 0.05, 1.0),
    trousers=(0.16, 0.18, 0.30, 1.0),
    helmet=(0.95, 0.75, 0.10, 1.0),
    scale: float = 1.0,
    highlight: Mapping[str, tuple] | None = None,
) -> None:
    """Draw the figure as capsules between its joints.

    ``highlight`` overrides the colour of named segments, which is how the
    lesson shows which limbs are doing the work at any instant.
    """
    colour_of = {
        "legs": trousers,
        "trunk": hi_vis,
        "arms": hi_vis,
    }
    for segment in SEGMENTS:
        start = joints[segment.start]
        end = joints[segment.end]
        colour = colour_of[LIMB_GROUP[segment.name]]
        if segment.mass_key in ("forearm", "hand"):
            colour = skin
        if highlight and segment.name in highlight:
            colour = highlight[segment.name]
        radius = segment.radius * scale
        if float(np.linalg.norm(end - start)) < 1e-6:
            continue
        batch.cylinder(start, end, radius, colour, 7)
    # Joints get a ball so the limbs read as connected rather than as
    # a scatter of sticks.
    for name in ("l_knee", "r_knee", "l_elbow", "r_elbow",
                 "l_shoulder", "r_shoulder", "l_hip", "r_hip"):
        batch.sphere(joints[name], 0.048 * scale, hi_vis, 4, 7)
    batch.sphere(joints["pelvis"], 0.10 * scale, trousers, 4, 8)
    head_base = joints["neck"]
    head_top = joints["head_top"]
    centre = (head_base + head_top) * 0.5
    batch.sphere(centre, 0.098 * scale, skin, 5, 9)
    batch.sphere(centre + (head_top - head_base) * 0.30, 0.094 * scale,
                 helmet, 4, 9)


def draw_load(
    batch: TriangleBatch,
    joints: Mapping[str, np.ndarray],
    dims,
    colour,
) -> None:
    """Draw the object in the crew's hands, sized from its real extents."""
    centre = grip_point(joints)
    width, depth, height = (max(0.06, float(value)) for value in dims)
    batch.box((float(centre[0]), float(centre[1]),
               float(centre[2]) + height * 0.5),
              (width, depth, height), colour)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_figure() -> None:
    """Check the skeleton before any energy number is measured off it."""
    # The mass fractions have to account for the whole body exactly once.
    total = sum(segment.mass(1.0) for segment in SEGMENTS)
    assert abs(total - 1.0) < 1e-9, total
    assert set(LIMB_GROUP) == {segment.name for segment in SEGMENTS}

    stature = 1.75
    standing = joint_positions(POSES["stand"], stature)
    # A standing figure is its own height, and stands on the ground.
    head = float(standing["head_top"][2])
    assert abs(head - stature) < 0.05, head
    sole = min(float(standing[name][2]) for name in ("l_ankle", "r_ankle"))
    assert abs(sole - STATURE_FRACTION["ankle_height"] * stature) < 1e-6, sole

    # Every pose has to keep its feet on the ground and its head above it.
    for name, pose in POSES.items():
        joints = joint_positions(pose, stature)
        lowest = min(float(point[2]) for point in joints.values())
        assert lowest >= -1e-6, (name, lowest)
        assert float(joints["head_top"][2]) > 0.7, (name, joints["head_top"])
        # Limbs cannot stretch: check a couple of segment lengths hold.
        for segment in SEGMENTS:
            length = float(np.linalg.norm(
                joints[segment.end] - joints[segment.start]))
            assert length < stature * 0.6, (name, segment.name, length)

    # Squatting has to lower the body's centre of mass, and reaching up
    # has to raise the hands.  If either fails the poses are mislabelled.
    stand_com = body_centre(joint_positions(POSES["stand"], stature), 80.0)
    squat_com = body_centre(joint_positions(POSES["squat_deep"], stature), 80.0)
    assert squat_com[2] < stand_com[2] - 0.15, (stand_com[2], squat_com[2])

    stand_grip = grip_point(joint_positions(POSES["stand"], stature))
    high_grip = grip_point(joint_positions(POSES["reach_high"], stature))
    assert high_grip[2] > stand_grip[2] + 0.8, (stand_grip[2], high_grip[2])
    # Overhead work happens above head height, and carrying happens in
    # front of the body rather than beside it.
    assert high_grip[2] > 1.80, high_grip[2]
    carry_grip = grip_point(joint_positions(POSES["carry"], stature))
    assert carry_grip[0] > 0.25, carry_grip[0]
    assert 0.80 < carry_grip[2] < 1.05, carry_grip[2]
    # A pose meant for picking up off the floor has to actually reach it.
    for name in ("squat_deep", "stoop", "kneel", "fasten"):
        grip = grip_point(joint_positions(POSES[name], stature))
        assert grip[2] < 0.62, (name, grip[2])
    # The squat lowers the body much further than the stoop does, which is
    # the whole reason it costs more to come back up.
    squat_com = body_centre(joint_positions(POSES["squat_deep"], stature), 80.0)
    stoop_com = body_centre(joint_positions(POSES["stoop"], stature), 80.0)
    assert squat_com[2] < stoop_com[2] - 0.12, (squat_com[2], stoop_com[2])

    # The walk cycle must be continuous where it wraps around.
    start = joint_positions(walk_pose(0.0), stature)
    end = joint_positions(walk_pose(0.999), stature)
    for name in start:
        assert float(np.linalg.norm(start[name] - end[name])) < 0.05, name

    # Blending is a proper interpolation, not a jump.
    half = POSES["stand"].blend(POSES["carry"], 0.5)
    assert abs(half.l_elbow - (POSES["stand"].l_elbow
                               + POSES["carry"].l_elbow) * 0.5) < 1e-9

    # Mirroring swaps sides and is its own inverse.
    once = mirrored(POSES["stride"])
    assert abs(once.l_hip - POSES["stride"].r_hip) < 1e-9
    assert mirrored(once) == POSES["stride"]
