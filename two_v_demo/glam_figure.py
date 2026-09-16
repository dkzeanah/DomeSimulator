"""One call that draws a woman: body, clothes, hair, face, attitude.

Four modules meet here and none of them knows about the others.
:mod:`two_v_demo.glam_body` builds the skeleton and the silhouette,
:mod:`two_v_demo.glam_wardrobe` dresses it, :mod:`two_v_demo.glam_hair`
puts hair on it and :mod:`two_v_demo.drama_face` puts a face on the
front of the head.  This module is the only place that knows the order
those happen in and how a character record turns into all four.

The poses
---------
:mod:`two_v_demo.figure` has a vocabulary of *work* poses -- squat,
stoop, carry, fasten -- because it was built for a lesson about lifting
panels.  None of them is any use to a woman standing in a shop deciding
whether you are worth answering.  :data:`GLAM_POSES` adds the ones this
cast needs, built out of the same joint angles, and every one of them
is asymmetric: weight on one leg, one shoulder lower than the other.
A symmetrical figure reads as a mannequin, which is a look this package
already has a mode for and does not need by accident.

Attitude is not decoration
--------------------------
A character's resting expression, her heel, the leg she stands on and
the outfit she is in all come off her own record in
:mod:`two_v_demo.glam_cast`, so drawing her twice in two scenes gives
the same woman.  Pass ``expression`` to override the resting face for a
beat that needs it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Mapping

import numpy as np

from .drama_face import EXPRESSIONS, FaceState, draw_face
from .figure import POSES, Pose, mirrored, walk_pose
from .glam_body import draw_body, glam_joints, sole_height
from .glam_cast import GLAM_CAST, GlamCharacter, character, hair_rgba, skin
from .glam_hair import draw_hair, style
from .glam_wardrobe import Outfit, draw_outfit, outfit, palette_for


Colour = tuple[float, float, float, float]


# ----------------------------------------------------------------------
# Poses with attitude
# ----------------------------------------------------------------------

GLAM_POSES: dict[str, Pose] = {
    # Weight back on one leg, chest open, chin level. The one she uses
    # when she has already decided how the conversation ends.
    "power_stand": Pose(
        l_hip=-6.0, r_hip=4.0, l_knee=3.0, r_knee=14.0,
        l_ankle=2.0, r_ankle=-4.0, trunk_lean=-3.0, trunk_twist=-8.0,
        l_shoulder=-6.0, r_shoulder=-2.0,
        l_shoulder_out=13.0, r_shoulder_out=9.0,
        l_elbow=16.0, r_elbow=12.0,
    ),
    # Hip thrown out over the straight leg, the other knee soft.
    "hip_pop": Pose(
        l_hip=-9.0, r_hip=7.0, l_knee=1.0, r_knee=22.0,
        l_ankle=3.0, r_ankle=-8.0, trunk_lean=-2.0, trunk_twist=14.0,
        l_shoulder=-10.0, r_shoulder=4.0,
        l_shoulder_out=8.0, r_shoulder_out=17.0,
        l_elbow=26.0, r_elbow=10.0, hip_drop=0.015,
    ),
    # Arms folded, weight settled, waiting for you to finish.
    # Folding the arms is the one pose the rig makes easy to get wrong:
    # swinging the shoulders inward far enough to cross the forearms
    # buries the upper arms in the ribcage, and she renders with no arms
    # at all.  The shoulders stay just outside the torso and the elbows
    # do the crossing.
    "arms_crossed": Pose(
        l_hip=-4.0, r_hip=3.0, l_knee=4.0, r_knee=12.0,
        trunk_lean=2.0, trunk_twist=-6.0,
        l_shoulder=-8.0, r_shoulder=-10.0,
        l_shoulder_out=-7.0, r_shoulder_out=-9.0,
        l_elbow=98.0, r_elbow=106.0,
    ),
    # Hands on the hips, elbows wide: taking up the room deliberately.
    "hands_on_hips": Pose(
        l_hip=-5.0, r_hip=5.0, l_knee=3.0, r_knee=15.0,
        trunk_lean=-4.0, trunk_twist=-4.0,
        l_shoulder=-24.0, r_shoulder=-24.0,
        l_shoulder_out=34.0, r_shoulder_out=32.0,
        l_elbow=104.0, r_elbow=108.0,
    ),
    # Turned away at the waist, looking back over the shoulder.
    "glance_back": Pose(
        l_hip=-8.0, r_hip=6.0, l_knee=2.0, r_knee=18.0,
        l_ankle=4.0, r_ankle=-6.0, trunk_lean=-2.0, trunk_twist=32.0,
        neck=4.0,
        l_shoulder=-18.0, r_shoulder=8.0,
        l_shoulder_out=6.0, r_shoulder_out=20.0,
        l_elbow=34.0, r_elbow=14.0,
    ),
    # Mid-stride with the hips leading: a walk, not a march.
    "strut": Pose(
        l_hip=-20.0, r_hip=26.0, l_knee=8.0, r_knee=18.0,
        l_ankle=-10.0, r_ankle=8.0, trunk_lean=-2.0, trunk_twist=-12.0,
        l_shoulder=20.0, r_shoulder=-18.0,
        l_shoulder_out=10.0, r_shoulder_out=10.0,
        l_elbow=30.0, r_elbow=24.0,
    ),
    # One arm out, pointing at whatever has just gone wrong.
    "point_off": Pose(
        l_hip=-4.0, r_hip=4.0, l_knee=4.0, r_knee=13.0,
        trunk_lean=4.0, trunk_twist=-18.0,
        l_shoulder=-12.0, r_shoulder=64.0,
        l_shoulder_out=10.0, r_shoulder_out=28.0,
        l_elbow=22.0, r_elbow=8.0,
    ),
    # Seated: hips and knees at a right angle, which puts the pelvis at
    # seat height on its own once the feet are grounded.  No furniture
    # height is typed in anywhere -- the shank decides it.
    "seated": Pose(
        l_hip=86.0, r_hip=90.0, l_knee=86.0, r_knee=92.0,
        l_ankle=-4.0, r_ankle=2.0, trunk_lean=4.0, trunk_twist=-7.0,
        l_shoulder=-16.0, r_shoulder=-12.0,
        l_shoulder_out=12.0, r_shoulder_out=8.0,
        l_elbow=54.0, r_elbow=42.0,
    ),
    # Leaning back on something, one shoulder low.
    "lean_back": Pose(
        l_hip=-14.0, r_hip=-10.0, l_knee=8.0, r_knee=20.0,
        l_ankle=10.0, r_ankle=6.0, trunk_lean=-12.0, trunk_twist=10.0,
        l_shoulder=-26.0, r_shoulder=-8.0,
        l_shoulder_out=16.0, r_shoulder_out=22.0,
        l_elbow=38.0, r_elbow=62.0,
    ),
}

POSE_ORDER: tuple[str, ...] = tuple(GLAM_POSES)

SEAT_POSES: frozenset[str] = frozenset({"seated"})
"""Poses that need something under them.  The composer refuses to place
a seated figure in mid-air."""


def pose(pose_key: str) -> Pose:
    """Look a pose up in this module's vocabulary or the work one."""
    if pose_key in GLAM_POSES:
        return GLAM_POSES[pose_key]
    if pose_key in POSES:
        return POSES[pose_key]
    raise ValueError(f"unknown pose {pose_key!r}; choose from "
                     f"{', '.join(POSE_ORDER)}")


def seat_height(stature: float) -> float:
    """How high the seat under a seated figure has to be.

    Measured off the posed skeleton rather than declared: sit the
    figure down, ask where its hips ended up, and that is the seat.
    """
    joints = glam_joints(GLAM_POSES["seated"], stature)
    return float(joints["pelvis"][2]) - sole_height(joints)


# ----------------------------------------------------------------------
# A look
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Look:
    """Everything needed to draw one woman once."""

    character_id: str
    mode: str = "STREET"
    pose_key: str = ""
    """Empty means her own default pose."""
    hair_style: str = ""
    """Empty means her own hair.  The composer lets you cycle it."""
    expression: str = ""
    """Empty means her resting face."""
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw_deg: float = 0.0
    detail: float = 1.0

    def character(self) -> GlamCharacter:
        return character(self.character_id)

    def outfit(self) -> Outfit:
        return outfit(self.character().wardrobe[self.mode])

    def resolved_pose(self) -> str:
        return self.pose_key or self.character().default_pose

    def resolved_hair(self) -> str:
        return self.hair_style or self.character().hair_style

    def resolved_expression(self) -> str:
        return self.expression or self.character().expression

    def heel_m(self) -> float:
        return self.character().heel_pref_m * self.outfit().heel

    def label(self) -> str:
        who = self.character()
        return (f"{who.name} - {self.outfit().label}, "
                f"{style(self.resolved_hair()).label.lower()}")


def look_joints(look: Look) -> dict[str, np.ndarray]:
    """Where every joint of this look ends up in the world."""
    who = look.character()
    return glam_joints(pose(look.resolved_pose()), who.stature_m,
                       look.position, look.yaw_deg, heel_m=look.heel_m())


def draw_look(
    opaque,
    look: Look,
    *,
    transparent=None,
    with_face: bool = True,
    joints: Mapping[str, np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    """Draw one woman, and hand back the skeleton she was drawn on.

    The order is the order it has to be: body, then clothes over the
    body, then hair over the head, then the face last so nothing is
    drawn on top of her eyes.  The joints come back because a caller
    that has just placed a figure usually wants to know where her hand
    ended up -- for a camera to look at, or for a prop to sit in.
    """
    who = look.character()
    joints = dict(joints) if joints is not None else look_joints(look)
    tone = skin(look.character_id)

    draw_body(opaque, joints, who.stature_m, tone)

    wardrobe = look.outfit()
    draw_outfit(opaque, joints, who.stature_m, wardrobe,
                palette_for(wardrobe, who), heel_m=look.heel_m(),
                transparent=transparent)

    main, accent = hair_rgba(look.character_id)
    draw_hair(opaque, joints, look.resolved_hair(), main, accent,
              detail=look.detail)

    if with_face:
        draw_face(opaque, joints, EXPRESSIONS[look.resolved_expression()],
                  tone)
    return joints


def draw_cast_row(
    opaque,
    looks,
    *,
    transparent=None,
) -> list[dict[str, np.ndarray]]:
    """Draw several looks, returning each one's joints in order."""
    return [draw_look(opaque, item, transparent=transparent)
            for item in looks]


def line_up(
    character_ids,
    mode: str,
    *,
    spacing: float = 0.85,
    yaw_deg: float = 0.0,
    origin: tuple[float, float] = (0.0, 0.0),
    detail: float = 1.0,
) -> tuple[Look, ...]:
    """A row of women, centred on ``origin`` and facing one way.

    The lookbook and the composer's cast palette both want this and it
    is fiddly enough to get the centring wrong twice.
    """
    ids = tuple(character_ids)
    span = spacing * (len(ids) - 1)
    across = np.array([-math.sin(math.radians(yaw_deg)),
                       math.cos(math.radians(yaw_deg))])
    looks = []
    for index, character_id in enumerate(ids):
        offset = (index * spacing) - span * 0.5
        looks.append(Look(
            character_id=character_id,
            mode=mode,
            position=(origin[0] + float(across[0]) * offset,
                      origin[1] + float(across[1]) * offset,
                      0.0),
            yaw_deg=yaw_deg,
            detail=detail,
        ))
    return tuple(looks)


def look_report(mode: str = "FASHION") -> str:
    lines = [f"LOOKBOOK: {mode}", ""]
    for character_id in GLAM_CAST:
        item = Look(character_id=character_id, mode=mode)
        who = item.character()
        heel = item.heel_m()
        lines.append(f"{item.label()}")
        lines.append(f"    stands {who.stature_m:.2f} m"
                     + (f" on a {heel * 100:.0f} cm heel"
                        f" -- {who.stature_m + heel:.2f} m in the room"
                        if heel > 0.001 else " flat")
                     + f", {item.resolved_pose().replace('_', ' ')}, "
                     f"{item.resolved_expression().lower()}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_glam_figure() -> None:
    """Prove a look draws, stands where it was put, and is who it says."""
    from .glam_cast import WARDROBE_MODES
    from .render_kit import TriangleBatch

    # Every pose the casting asks for exists, and every pose in the
    # vocabulary is asymmetric -- a symmetrical figure is a mannequin.
    for who in GLAM_CAST.values():
        assert who.default_pose in GLAM_POSES, who.character_id
    for name, item in GLAM_POSES.items():
        left = (item.l_hip, item.l_knee, item.l_shoulder, item.l_elbow)
        right = (item.r_hip, item.r_knee, item.r_shoulder, item.r_elbow)
        assert left != right, name
        # And no pose swings an arm so far inward that it ends up
        # inside the ribcage, where it renders as no arm at all.
        for side in ("l", "r"):
            assert getattr(item, f"{side}_shoulder_out") > -12.0, (name, side)
    assert pose("stand") is POSES["stand"], "work poses still resolve"
    try:
        pose("vogue")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown pose has to be refused")

    # A seat height falls out of the seated pose rather than being typed
    # in, and lands somewhere a chair actually is.
    for stature in (1.55, 1.70, 1.90):
        height = seat_height(stature)
        assert 0.35 < height < 0.60, (stature, height)
    assert seat_height(1.90) > seat_height(1.55), "taller means a taller seat"

    # A look draws, and lands where it was put.
    for mode in WARDROBE_MODES:
        for character_id in GLAM_CAST:
            item = Look(character_id=character_id, mode=mode,
                        position=(2.0, -1.0, 0.0), yaw_deg=35.0)
            opaque = TriangleBatch()
            clear = TriangleBatch()
            joints = draw_look(opaque, item, transparent=clear)
            assert opaque.vertices, (character_id, mode)
            points = np.asarray(opaque.vertices,
                                dtype=float).reshape(-1, 10)[:, :3]
            # She stands on the floor at the spot she was placed.  The
            # tolerance is the ankle tilt: a pose that rolls a foot onto
            # its toe lifts the heel a centimetre or two off the deck,
            # which is a pose and not a figure floating.
            stood = float(sole_height(joints)) - item.heel_m()
            assert -0.005 < stood < 0.05, (character_id, mode, stood)
            centre = points[:, :2].mean(axis=0)
            assert abs(centre[0] - 2.0) < 0.35, centre
            assert abs(centre[1] + 1.0) < 0.35, centre
            assert points[:, 2].min() > -0.16, (character_id, mode,
                                                points[:, 2].min())
            # Nothing towers: her drawn height is her stature plus heel
            # plus hair, and hair is not a metre tall.
            who = item.character()
            ceiling = who.stature_m + item.heel_m() + 0.22
            assert points[:, 2].max() < ceiling, (character_id, mode,
                                                  points[:, 2].max())

    # Every pose keeps both elbows outside the torso.  This is the check
    # that catches a folded-arms pose drawn with the arms inside the
    # chest, which looks exactly like a figure with no arms.
    from .glam_body import body_frame, torso_radii
    for name in GLAM_POSES:
        item = Look(character_id="GLAM_AROHA", pose_key=name)
        joints = look_joints(item)
        frame = body_frame(joints)
        for side in ("l", "r"):
            elbow = np.asarray(joints[f"{side}_elbow"], dtype=float)
            spine = np.asarray(joints["pelvis"], dtype=float)
            chest = np.asarray(joints["chest"], dtype=float)
            share = float((elbow[2] - spine[2]) / max(1e-6, chest[2] - spine[2]))
            width, depth = torso_radii(item.character().stature_m,
                                       max(0.0, min(1.0, share)))
            offset = elbow - (spine + (chest - spine) * share)
            across = abs(float(np.dot(offset, frame.side)))
            ahead = abs(float(np.dot(offset, frame.forward)))
            assert (across / width) ** 2 + (ahead / depth) ** 2 > 1.0, (
                name, side, across, width)

    # Heels lift her, and the outfit decides whether she is in them.
    gown = Look(character_id="GLAM_PRIYA", mode="PARTY")
    flat = Look(character_id="GLAM_PRIYA", mode="STREET")
    assert gown.heel_m() > 0.05, gown.heel_m()
    assert flat.heel_m() == 0.0
    tall = look_joints(gown)["head_top"][2]
    short = look_joints(flat)["head_top"][2]
    assert float(tall - short) > 0.05, (tall, short)

    # The face is drawn last and lands on the head, not inside it.
    item = Look(character_id="GLAM_MEI", mode="FASHION")
    plain = TriangleBatch()
    draw_look(plain, item, with_face=False)
    faced = TriangleBatch()
    draw_look(faced, item)
    assert len(faced.vertices) > len(plain.vertices)

    # Detail changes the cost and not the woman: her joints are the same.
    cheap = replace(item, detail=0.2)
    assert np.allclose(look_joints(cheap)["r_grip"],
                       look_joints(item)["r_grip"])
    rough = TriangleBatch()
    draw_look(rough, cheap)
    fine = TriangleBatch()
    draw_look(fine, item)
    assert len(rough.vertices) < len(fine.vertices)

    # A line-up is centred, evenly spaced and all facing one way.
    row = line_up(tuple(GLAM_CAST)[:5], "SWIM", spacing=0.9)
    assert len(row) == 5
    across = [item.position[1] for item in row]
    assert abs(sum(across)) < 1e-9, across
    gaps = [b - a for a, b in zip(across, across[1:])]
    assert all(abs(gap - 0.9) < 1e-9 for gap in gaps), gaps
    turned = line_up(tuple(GLAM_CAST)[:3], "SWIM", yaw_deg=90.0, spacing=1.0)
    assert abs(turned[0].position[0] - 1.0) < 1e-9, turned[0].position

    # Overrides do what they say and leave the rest of her alone.
    swapped = Look(character_id="GLAM_KAT", mode="PARTY",
                   hair_style="AFRO_HALO", expression="FURY",
                   pose_key="point_off")
    assert swapped.resolved_hair() == "AFRO_HALO"
    assert swapped.resolved_expression() == "FURY"
    assert swapped.resolved_pose() == "point_off"
    assert swapped.character().hair_style == "PLATINUM_BLUNT_BOB"
    batch = TriangleBatch()
    draw_look(batch, swapped)
    assert batch.vertices

    assert "Nailah" in look_report("SWIM")


if __name__ == "__main__":
    validate_glam_figure()
    print(look_report("PARTY"))
