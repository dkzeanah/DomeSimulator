"""Drama rig actions: the CNEE's character kinematics layer.

This is the Character Rig Controller of the narrative module.  It sits on
top of :mod:`two_v_demo.figure`, which already provides a posable
humanoid -- hips, knees, ankles, trunk lean and twist, neck, shoulders
with abduction, elbows -- and adds what a drama needs on top of a
work-motion rig: timed dramatic actions, proximity rules, eye contact,
and pinning one character's hand to another character's body.

**What this rig can and cannot execute.**  The specification lists
facial parameters for some actions -- jaw drop, eye scale, smirk morphs.
The figure in this package has no face rig, so those numbers are carried
on the action as *declared* data and are not executed.  Every action
therefore states which channels it drives (``skeletal``) and which it
only records for a future face rig (``facial``), and
:func:`validate_drama_rig` checks that the split is stated rather than
assumed.  Nothing here silently pretends to animate a face.

Units follow the spec: metres, degrees, seconds.  Positive trunk lean is
forward; positive yaw turns the figure to its left.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np

from .figure import POSES, Pose, joint_positions


# ----------------------------------------------------------------------
# Timing curves
# ----------------------------------------------------------------------

def curve_linear(t: float) -> float:
    return min(1.0, max(0.0, t))


def curve_ease_out_expo(t: float) -> float:
    """Sharp start, long settle: a slap, a snap of the head."""
    t = curve_linear(t)
    return 1.0 - math.pow(2.0, -10.0 * t) if t < 1.0 else 1.0


def curve_instant_hold(t: float) -> float:
    """All the way there almost at once, then held: a gasp."""
    return curve_linear(t * 8.0)


def curve_decelerate(t: float) -> float:
    """Aggressive arrival: fast in, hard stop.  The invasive step."""
    t = curve_linear(t)
    return 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t)


def curve_smooth(t: float) -> float:
    """Even, unhurried: the disdainful turn."""
    t = curve_linear(t)
    return t * t * (3.0 - 2.0 * t)


def curve_snap(t: float) -> float:
    """A rigid lock, reached in the first fifth of the action."""
    return curve_linear(t * 5.0)


CURVES: dict[str, Callable[[float], float]] = {
    "linear": curve_linear,
    "ease_out_expo": curve_ease_out_expo,
    "instant_hold": curve_instant_hold,
    "decelerate": curve_decelerate,
    "smooth": curve_smooth,
    "snap": curve_snap,
}


# ----------------------------------------------------------------------
# Proximity, from the specification's two rings
# ----------------------------------------------------------------------

CONFRONTATION_RING = (0.30, 0.60)
"""Metres. Inside this, heads tilt, torsos lean and the listener blurs."""

PERSONAL_RING = (0.60, 1.20)
"""Metres. The default spacing for a back-and-forth dialogue beat."""

EYE_CONTACT_RADIUS = 2.50
"""Metres. Within this, heads and eyes track the other character."""

BODY_DEPTH_M = 0.32
"""Chest to back, near enough, for two people standing face to face.

The specification's rings are the *gap* between two characters, which
is how a person describes standing close to somebody.  Placement works
in centre-to-centre distance, so the two differ by a body: put two
figures 0.5 m apart centre to centre and their chests occupy the same
space.  Every ring in this module is therefore converted through this
constant on the way to a floor position, and back again on the way to a
ring name."""


def centre_distance_for_gap(gap_m: float) -> float:
    """Centre-to-centre spacing that leaves ``gap_m`` between two people."""
    return gap_m + BODY_DEPTH_M


def gap_for_centre_distance(distance_m: float) -> float:
    """The gap two figures that far apart actually leave each other."""
    return max(0.0, distance_m - BODY_DEPTH_M)


def ring_for(distance: float) -> str:
    """Which spatial ring two characters are standing in."""
    if distance < CONFRONTATION_RING[0]:
        return "contact"
    if distance <= CONFRONTATION_RING[1]:
        return "confrontation"
    if distance <= PERSONAL_RING[1]:
        return "personal"
    if distance <= EYE_CONTACT_RADIUS:
        return "social"
    return "distant"


# ----------------------------------------------------------------------
# The action library
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RigAction:
    """One dramatic action, as timing plus channel deltas.

    ``pose_delta`` is added to whatever pose the character is holding,
    scaled by the curve.  ``root_step`` moves the figure along its own
    facing direction, and ``root_yaw`` turns it.  ``head_delay`` holds
    the neck back by a fraction of the action so the head arrives after
    the body, which is what makes a turn read as disdain rather than as
    a glance.
    """

    action_id: str
    duration_s: float
    curve: str
    purpose: str
    pose_delta: Pose = field(default_factory=Pose)
    root_step_m: float = 0.0
    root_yaw_deg: float = 0.0
    hold_s: float = 0.0
    """Time the pose is held at full value after the curve completes."""
    head_delay: float = 0.0
    tremor_hz: float = 0.0
    tremor_deg: float = 0.0
    contact: bool = False
    """Whether this action physically reaches the other character.

    A contact action cannot be staged at conversational spacing -- the
    arm does not reach -- so the director pulls the pair into the
    confrontation ring for any beat that contains one."""
    attach: str | None = None
    """Socket on the target character this action pins a hand to."""
    attach_distance_m: float = 0.0
    facial: tuple[tuple[str, float], ...] = ()
    """Declared but not executed: this package's figure has no face."""

    @property
    def total_s(self) -> float:
        return self.duration_s + self.hold_s

    @property
    def skeletal_channels(self) -> tuple[str, ...]:
        """Which pose channels this action actually drives."""
        return tuple(
            name for name in Pose.__dataclass_fields__
            if abs(getattr(self.pose_delta, name)
                   - getattr(Pose(), name)) > 1e-9
        )


def _delta(**values: float) -> Pose:
    """A pose delta: zero everywhere except the named channels.

    The neutral pose is not all zeros -- shoulders sit slightly out --
    so a delta has to start from a true zero pose rather than from
    ``Pose()``.
    """
    zero = {name: 0.0 for name in Pose.__dataclass_fields__}
    zero.update(values)
    return Pose(**zero)


ACTIONS: dict[str, RigAction] = {
    "RIG_SLAP_EXECUTE": RigAction(
        action_id="RIG_SLAP_EXECUTE",
        duration_s=0.25,
        curve="ease_out_expo",
        purpose="Sudden betrayal or high-tension emotional climax.",
        # The swing: shoulder drives across the body, elbow straightens
        # through the strike, trunk counter-rotates behind it.
        pose_delta=_delta(r_shoulder=-95.0, r_shoulder_out=38.0,
                          r_elbow=-25.0, trunk_twist=-15.0, neck=-6.0),
        hold_s=0.10,
        contact=True,
    ),
    "RIG_GASP_REACTION": RigAction(
        action_id="RIG_GASP_REACTION",
        duration_s=0.15,
        curve="instant_hold",
        purpose="Shocked reaction to a secret reveal.",
        # Shoulders up, chest open, head back: the whole body flinches
        # even though the face cannot.
        pose_delta=_delta(l_shoulder_out=22.0, r_shoulder_out=22.0,
                          l_shoulder=-14.0, r_shoulder=-14.0,
                          trunk_lean=-8.0, neck=-12.0),
        hold_s=1.20,
        facial=(("jaw_drop_mm", 20.0), ("eye_scale_pct", 15.0),
                ("shoulder_lift_mm", 30.0)),
    ),
    "RIG_INVASIVE_STEP": RigAction(
        action_id="RIG_INVASIVE_STEP",
        duration_s=0.40,
        curve="decelerate",
        purpose="Establishing dominance, intimacy, or direct threat.",
        pose_delta=_delta(trunk_lean=10.0, r_hip=14.0, r_knee=10.0,
                          l_hip=-10.0, neck=4.0),
        root_step_m=0.80,
        hold_s=0.30,
    ),
    "RIG_DISDAINFUL_TURN": RigAction(
        action_id="RIG_DISDAINFUL_TURN",
        duration_s=0.60,
        curve="smooth",
        purpose="Expressing class rejection or emotional coldness.",
        pose_delta=_delta(l_shoulder_out=-4.0, r_shoulder_out=-4.0,
                          trunk_twist=12.0, neck=6.0),
        root_yaw_deg=45.0,
        head_delay=0.35,
        facial=(("eyes_down_left", 1.0),),
    ),
    "RIG_CLENCH_FIST_RAISE": RigAction(
        action_id="RIG_CLENCH_FIST_RAISE",
        duration_s=0.30,
        curve="linear",
        purpose="Suppressed rage or a desperate vow of vengeance.",
        pose_delta=_delta(r_shoulder=-38.0, r_elbow=90.0,
                          r_shoulder_out=10.0, trunk_lean=3.0),
        hold_s=0.60,
        tremor_hz=12.0,
        tremor_deg=1.4,
        facial=(("fist_compression_pct", 100.0),),
    ),
    "RIG_GRAB_LAPEL": RigAction(
        action_id="RIG_GRAB_LAPEL",
        duration_s=0.20,
        curve="snap",
        purpose="Physical confrontation or high-stakes interrogation.",
        pose_delta=_delta(l_shoulder=-58.0, r_shoulder=-58.0,
                          l_elbow=70.0, r_elbow=70.0,
                          l_shoulder_out=14.0, r_shoulder_out=14.0,
                          trunk_lean=6.0),
        hold_s=0.80,
        contact=True,
        attach="collar",
        attach_distance_m=0.35,
    ),
    # The specification's example episode calls for this one, though its
    # action table stops at six.  Written to the same pattern so the
    # example script runs as published.
    "RIG_POINT_COMMAND": RigAction(
        action_id="RIG_POINT_COMMAND",
        duration_s=0.35,
        curve="decelerate",
        purpose="A verdict delivered: authority naming the truth.",
        pose_delta=_delta(r_shoulder=-72.0, r_elbow=12.0,
                          r_shoulder_out=8.0, trunk_lean=4.0, neck=-3.0),
        hold_s=0.90,
    ),
}


# Sockets a hand can be pinned to, as joint names on the target rig.
ATTACH_SOCKETS: dict[str, str] = {
    "collar": "neck",
    "shoulder": "l_shoulder",
    "chest": "chest",
}


# ----------------------------------------------------------------------
# Executing an action
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RigState:
    """What a character is doing at one instant."""

    pose: Pose
    root_offset_m: float
    """Distance moved along the character's own facing direction."""
    yaw_offset_deg: float
    action_id: str | None
    amount: float
    """How far through the action's curve this instant is, 0..1."""


def action_amount(action: RigAction, elapsed_s: float) -> float:
    """How far through its curve an action is at ``elapsed_s``."""
    if elapsed_s <= 0.0:
        return 0.0
    if action.duration_s <= 0.0:
        return 1.0
    return CURVES[action.curve](elapsed_s / action.duration_s)


def execute(action_id: str | None, elapsed_s: float,
            base: Pose | None = None) -> RigState:
    """The rig state ``elapsed_s`` into an action.

    Past the end of the action the pose is held rather than snapping
    back: a drama beat wants the aftermath of the slap, not just the
    slap.
    """
    base = POSES["stand"] if base is None else base
    if action_id is None:
        return RigState(base, 0.0, 0.0, None, 0.0)
    action = ACTIONS[action_id]
    amount = action_amount(action, elapsed_s)
    values = {}
    for name in Pose.__dataclass_fields__:
        delta = getattr(action.pose_delta, name)
        share = amount
        if name == "neck" and action.head_delay > 0.0:
            # The head lags the body, then catches up.
            lag = max(0.0, elapsed_s - action.head_delay * action.duration_s)
            share = CURVES[action.curve](
                lag / max(1e-6, action.duration_s * (1.0 - action.head_delay)))
        values[name] = getattr(base, name) + delta * share
    if action.tremor_hz > 0.0 and amount > 0.5:
        shake = math.sin(elapsed_s * math.tau * action.tremor_hz)
        values["r_elbow"] += shake * action.tremor_deg
        values["r_shoulder"] += shake * action.tremor_deg * 0.5
    return RigState(
        pose=Pose(**values),
        root_offset_m=action.root_step_m * amount,
        yaw_offset_deg=action.root_yaw_deg * amount,
        action_id=action_id,
        amount=amount,
    )


# ----------------------------------------------------------------------
# Two characters in the same space
# ----------------------------------------------------------------------

def facing_yaw(origin, target) -> float:
    """Yaw in degrees that turns a figure from ``origin`` toward ``target``."""
    offset = np.asarray(target, dtype=float)[:2] - np.asarray(origin,
                                                              dtype=float)[:2]
    if float(np.linalg.norm(offset)) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(offset[1], offset[0]))


def eye_line(joints: dict[str, np.ndarray]) -> np.ndarray:
    """Where a figure is looking from: between the neck and the crown."""
    return joints["neck"] + (joints["head_top"] - joints["neck"]) * 0.55


def eye_contact_yaw(watcher: dict[str, np.ndarray], target_eye,
                    body_yaw_deg: float) -> float:
    """Head yaw needed to look at ``target_eye``, or zero if too far.

    Returned relative to the body, so a figure standing square to its
    opponent needs none, and one that has turned away needs the whole
    angle back.
    """
    here = eye_line(watcher)
    if float(np.linalg.norm(np.asarray(target_eye) - here)) > EYE_CONTACT_RADIUS:
        return 0.0
    wanted = facing_yaw(here, target_eye)
    return (wanted - body_yaw_deg + 180.0) % 360.0 - 180.0


def attachment_point(target_joints: dict[str, np.ndarray],
                     socket: str) -> np.ndarray:
    """Where a grabbing hand is pinned on the other character."""
    return np.asarray(target_joints[ATTACH_SOCKETS[socket]], dtype=float)


def stand_off(anchor, toward, distance_m: float) -> np.ndarray:
    """A standing spot ``distance_m`` from ``anchor`` on the way to ``toward``.

    Used to place a character at a chosen ring rather than by eye: the
    confrontation ring is only forty centimetres wide, and a scene that
    misses it does not read as a confrontation.
    """
    anchor = np.asarray(anchor, dtype=float)
    direction = np.asarray(toward, dtype=float) - anchor
    direction[2] = 0.0
    length = float(np.linalg.norm(direction))
    if length < 1e-9:
        return anchor.copy()
    return anchor + direction / length * distance_m


def posed_joints(state: RigState, spot, facing_yaw_deg: float,
                 stature: float = 1.78) -> dict[str, np.ndarray]:
    """Joint positions for a rig state standing at ``spot``.

    The action's own step and turn are applied here, so a caller only
    ever has to say where the character started and who it is facing.
    """
    spot = np.asarray(spot, dtype=float)
    yaw = facing_yaw_deg + state.yaw_offset_deg
    forward = np.array([math.cos(math.radians(facing_yaw_deg)),
                        math.sin(math.radians(facing_yaw_deg)), 0.0])
    origin = spot + forward * state.root_offset_m
    return joint_positions(state.pose, stature, origin, yaw)


def validate_drama_rig() -> None:
    """Prove the action library before a beat is ever played."""
    assert set(CURVES) >= {"linear", "ease_out_expo", "instant_hold",
                           "decelerate", "smooth", "snap"}
    for name, curve in CURVES.items():
        assert abs(curve(0.0)) < 1e-9, name
        assert abs(curve(1.0) - 1.0) < 1e-6, name
        assert abs(curve(2.0) - 1.0) < 1e-6, f"{name} must clamp"

    for action_id, action in ACTIONS.items():
        assert action.action_id == action_id
        assert action.duration_s > 0.0, action_id
        assert action.curve in CURVES, action_id
        assert action.purpose.endswith("."), action_id
        # Every action has to move the skeleton: an action that only
        # declares facial data would animate nothing on this rig, and
        # the film would show a character standing still through a beat.
        assert action.skeletal_channels, (
            f"{action_id} drives no skeletal channel this rig can execute")
        if action.attach is not None:
            assert action.attach in ATTACH_SOCKETS, action_id
            assert action.attach_distance_m > 0.0, action_id

    # The spec's headline timings, checked rather than described.
    assert ACTIONS["RIG_SLAP_EXECUTE"].duration_s == 0.25
    assert ACTIONS["RIG_GASP_REACTION"].hold_s == 1.20
    assert ACTIONS["RIG_INVASIVE_STEP"].root_step_m == 0.80
    assert ACTIONS["RIG_DISDAINFUL_TURN"].root_yaw_deg == 45.0
    assert ACTIONS["RIG_CLENCH_FIST_RAISE"].tremor_hz == 12.0
    assert ACTIONS["RIG_GRAB_LAPEL"].attach_distance_m == 0.35

    # Reaching actions are marked as such, and only those.
    contact = {name for name, action in ACTIONS.items() if action.contact}
    assert contact == {"RIG_SLAP_EXECUTE", "RIG_GRAB_LAPEL"}, contact
    for name in contact:
        assert ACTIONS[name].duration_s <= 0.3, name

    # An action must actually change the figure, and must hold its shape
    # after it finishes rather than springing back.
    for action_id in ACTIONS:
        rest = execute(None, 0.0)
        mid = execute(action_id, ACTIONS[action_id].duration_s * 0.5)
        end = execute(action_id, ACTIONS[action_id].total_s)
        after = execute(action_id, ACTIONS[action_id].total_s * 4.0)
        moved = max(
            abs(getattr(end.pose, name) - getattr(rest.pose, name))
            for name in Pose.__dataclass_fields__)
        assert moved > 1.0, action_id
        assert 0.0 <= mid.amount <= 1.0, action_id
        assert abs(end.amount - 1.0) < 1e-6, action_id
        for name in Pose.__dataclass_fields__:
            if ACTIONS[action_id].tremor_hz > 0.0:
                continue
            assert abs(getattr(after.pose, name)
                       - getattr(end.pose, name)) < 1e-6, action_id

    # The rings are the spec's, and they do not overlap.
    assert CONFRONTATION_RING[1] == PERSONAL_RING[0]
    assert ring_for(0.45) == "confrontation"
    assert abs(gap_for_centre_distance(
        centre_distance_for_gap(0.5)) - 0.5) < 1e-9
    assert ring_for(0.90) == "personal"
    assert ring_for(2.0) == "social"
    assert ring_for(9.0) == "distant"

    # Placement and eye contact have to agree with each other: a figure
    # placed on the confrontation ring must be inside eye-contact range
    # and looking at its opponent.
    here = np.array([0.0, 0.0, 0.0])
    there = np.array([2.0, 0.0, 0.0])
    spot = stand_off(there, here, 0.5)
    assert abs(float(np.linalg.norm(spot - there)) - 0.5) < 1e-9
    yaw = facing_yaw(spot, there)
    joints = posed_joints(execute(None, 0.0), spot, yaw)
    assert abs(eye_contact_yaw(joints, eye_line(
        joints_at(there, facing_yaw(there, spot))), yaw)) < 5.0

    # A grab pins to a real joint on the other rig.
    other = joints_at(there, facing_yaw(there, spot))
    point = attachment_point(other, "collar")
    assert point.shape == (3,)
    assert 1.0 < float(point[2]) < 2.0, "a collar should be chest-high"


def joints_at(spot, yaw_deg: float, pose: Pose | None = None,
              stature: float = 1.78) -> dict[str, np.ndarray]:
    """Convenience: a standing figure's joints at a spot and facing."""
    return joint_positions(POSES["stand"] if pose is None else pose,
                           stature, np.asarray(spot, dtype=float), yaw_deg)
