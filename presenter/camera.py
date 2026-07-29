"""Camera rig: lens presets, snap-to focus framing, 1-6 point perspective.

Modes 1-3 are classical linear perspectives expressed as constraints on
the camera (1-point: axis-aligned view, one vanishing point; 2-point:
level horizon so verticals stay parallel; 3-point: free). Modes 4-6 are
curvilinear projections resolved by the engine from six cube faces
(4: cylindrical panorama, 5: 180-degree fisheye, 6: full 360-degree
azimuthal equidistant).
"""

from __future__ import annotations

import math

import numpy as np

from .script import LENSES, Shot


def ease(v: float) -> float:
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


class CameraState:
    __slots__ = ("eye", "target", "fov", "mode", "basis")

    def __init__(self, eye, target, fov, mode, basis):
        self.eye = eye
        self.target = target
        self.fov = fov
        self.mode = mode
        self.basis = basis          # (forward, right, up) world vectors


def shot_camera(shot: Shot, targets: dict, progress: float,
                yaw_offset: float = 0.0, pitch_offset: float = 0.0,
                dist_scale: float = 1.0,
                mode_override: int | None = None) -> CameraState:
    fov, framing = LENSES.get(shot.lens, LENSES["wide"])
    center, radius = targets.get(shot.focus or "origin",
                                 targets.get("origin",
                                             (np.zeros(3), 6.0)))
    center = np.asarray(center, dtype=np.float64).copy()
    center[2] += shot.height_bias
    mode = mode_override if mode_override is not None else shot.perspective

    yaw = shot.yaw + shot.orbit * ease(progress) + yaw_offset
    pitch = shot.pitch + pitch_offset
    if mode == 1:
        # one-point: snap to the nearest world axis, level, no orbit
        yaw = round((shot.yaw + yaw_offset) / 90.0) * 90.0
        pitch = 0.5
    elif mode == 2:
        pitch = max(-2.0, min(2.0, pitch * 0.05))
    pitch = max(-85.0, min(85.0, pitch))

    distance = radius / max(0.15, math.tan(math.radians(fov) * 0.5))
    distance *= framing * dist_scale
    distance *= 1.0 + shot.dolly * ease(progress)
    if mode == 1:
        distance *= 1.0 + 0.14 * ease(progress)      # gentle push-in
    elif mode == 4:
        distance *= 0.75      # panoramas compress the subject —
    elif mode == 5:
        distance *= 0.45      # move in so it still fills the frame
    elif mode == 6:
        distance *= 0.34

    yr = math.radians(yaw)
    pr = math.radians(pitch)
    eye = center + np.array([
        distance * math.cos(pr) * math.cos(yr),
        distance * math.cos(pr) * math.sin(yr),
        distance * math.sin(pr)])
    eye[2] = max(0.25, eye[2])

    forward = center - eye
    fl = float(np.linalg.norm(forward))
    forward = forward / fl if fl > 1e-9 else np.array([1.0, 0.0, 0.0])
    up_hint = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up_hint)
    rl = float(np.linalg.norm(right))
    right = right / rl if rl > 1e-9 else np.array([0.0, 1.0, 0.0])
    up = np.cross(right, forward)
    return CameraState(eye.astype(np.float32),
                       center.astype(np.float32), fov, mode,
                       (forward.astype(np.float32),
                        right.astype(np.float32), up.astype(np.float32)))


def cube_faces(state: CameraState):
    """(forward, up) world-space pairs for the six 90-degree faces, in the
    camera's own basis so curvilinear shots still respect shot yaw/pitch.
    Order: +Z (ahead), +X (right), -Z, -X, +Y (up), -Y (down)."""
    f, r, u = state.basis
    return (
        (f, u), (r, u), (-f, u), (-r, u),
        (u, -f), (-u, f),
    )
