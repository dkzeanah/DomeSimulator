"""Solve shoulder and elbow angles so each pose's hands land where the task
actually happens: on the deck, at the belt, or overhead.
"""

import sys
from dataclasses import replace

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

from two_v_demo.figure import POSES, grip_point, joint_positions

STATURE = 1.75

# pose name -> (target grip height in m, target forward reach in m)
TARGETS = {
    "squat_deep": (0.26, 0.36),
    "squat_mid": (0.66, 0.36),
    "carry": (0.92, 0.34),
    "stoop": (0.36, 0.50),
    "reach_out": (1.24, 0.54),
    "reach_high": (1.92, 0.24),
    "kneel": (0.38, 0.42),
    "team_carry": (0.86, 0.30),
}


def solve(name, target_z, target_x, symmetric=True):
    base = POSES[name]
    best, best_cost = None, 1e9
    for shoulder in range(-70, 175, 2):
        for elbow in range(0, 145, 2):
            if symmetric:
                pose = replace(base, l_shoulder=shoulder, r_shoulder=shoulder,
                               l_elbow=elbow, r_elbow=elbow)
            else:
                pose = replace(base, l_shoulder=shoulder, l_elbow=elbow)
            grip = grip_point(joint_positions(pose, STATURE))
            cost = (grip[2] - target_z) ** 2 + (grip[0] - target_x) ** 2
            if cost < best_cost:
                best_cost, best = cost, (shoulder, elbow, grip)
    return best


print(f"{'pose':<12} {'shoulder':>9} {'elbow':>7}   grip x/z        target x/z")
for name, (target_z, target_x) in TARGETS.items():
    shoulder, elbow, grip = solve(name, target_z, target_x)
    print(f"{name:<12} {shoulder:>9} {elbow:>7}   "
          f"{grip[0]:+.3f} {grip[2]:.3f}    {target_x:+.3f} {target_z:.3f}")

# The one-armed fastening poses are solved on the working arm only.
for name, (target_z, target_x) in (("fasten", (0.38, 0.44)),
                                   ("fasten_high", (1.98, 0.18))):
    shoulder, elbow, grip = solve(name, target_z, target_x, symmetric=False)
    joints = joint_positions(
        replace(POSES[name], l_shoulder=shoulder, l_elbow=elbow), STATURE)
    print(f"{name:<12} {shoulder:>9} {elbow:>7}   "
          f"left hand {joints['l_grip'][0]:+.3f} {joints['l_grip'][2]:.3f}"
          f"    target {target_x:+.3f} {target_z:.3f}")
