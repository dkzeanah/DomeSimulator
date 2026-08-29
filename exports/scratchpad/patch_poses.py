"""Apply the solved arm angles to the pose vocabulary."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\figure.py")
s = p.read_text(encoding="utf-8")
NL = chr(10)


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:" + NL + old[:280])
    s = s.replace(old, new, 1)


sub("""        l_shoulder=-14.0, r_shoulder=-14.0, l_elbow=10.0, r_elbow=10.0,
        neck=-14.0, hip_drop=0.36,""",
    """        l_shoulder=-40.0, r_shoulder=-40.0, l_elbow=30.0, r_elbow=30.0,
        neck=-14.0, hip_drop=0.36,""")

sub("""        l_shoulder=-2.0, r_shoulder=-2.0, l_elbow=44.0, r_elbow=44.0,
        neck=-6.0, hip_drop=0.17,""",
    """        l_shoulder=-28.0, r_shoulder=-28.0, l_elbow=48.0, r_elbow=48.0,
        neck=-6.0, hip_drop=0.17,""")

sub("""    "carry": Pose(
        l_hip=4.0, r_hip=4.0, l_knee=8.0, r_knee=8.0, trunk_lean=8.0,
        l_shoulder=18.0, r_shoulder=18.0, l_elbow=76.0, r_elbow=76.0,
    ),""",
    """    "carry": Pose(
        l_hip=4.0, r_hip=4.0, l_knee=8.0, r_knee=8.0, trunk_lean=8.0,
        l_shoulder=-16.0, r_shoulder=-16.0, l_elbow=68.0, r_elbow=68.0,
    ),""")

sub("""        l_shoulder=-58.0, r_shoulder=-58.0, l_elbow=8.0, r_elbow=8.0,
        neck=-30.0,""",
    """        l_shoulder=-62.0, r_shoulder=-62.0, l_elbow=12.0, r_elbow=12.0,
        neck=-30.0,""")

sub("""        l_shoulder=158.0, r_shoulder=158.0,
        l_shoulder_out=16.0, r_shoulder_out=16.0,
        l_elbow=28.0, r_elbow=28.0, neck=26.0,""",
    """        l_shoulder=122.0, r_shoulder=122.0,
        l_shoulder_out=16.0, r_shoulder_out=16.0,
        l_elbow=62.0, r_elbow=62.0, neck=26.0,""")

sub("""    "reach_out": Pose(
        l_hip=2.0, r_hip=2.0, l_knee=10.0, r_knee=10.0, trunk_lean=10.0,
        l_shoulder=84.0, r_shoulder=84.0, l_elbow=24.0, r_elbow=24.0,
    ),""",
    """    "reach_out": Pose(
        l_hip=2.0, r_hip=2.0, l_knee=10.0, r_knee=10.0, trunk_lean=10.0,
        l_shoulder=10.0, r_shoulder=10.0, l_elbow=90.0, r_elbow=90.0,
    ),""")

sub("""        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=22.0,
        l_shoulder=44.0, r_shoulder=44.0, l_elbow=58.0, r_elbow=58.0,
        neck=-18.0, hip_drop=0.44,""",
    """        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=22.0,
        l_shoulder=-14.0, r_shoulder=-14.0, l_elbow=22.0, r_elbow=22.0,
        neck=-18.0, hip_drop=0.44,""")

sub("""        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=28.0,
        l_shoulder=62.0, r_shoulder=38.0,
        l_elbow=96.0, r_elbow=44.0, neck=-22.0, hip_drop=0.44,""",
    """        l_ankle=-30.0, r_ankle=-16.0, trunk_lean=28.0,
        l_shoulder=-22.0, r_shoulder=-32.0,
        l_elbow=44.0, r_elbow=18.0, neck=-22.0, hip_drop=0.44,""")

sub("""        trunk_lean=-8.0, l_shoulder=70.0, r_shoulder=150.0,
        r_shoulder_out=18.0, l_elbow=64.0, r_elbow=52.0, neck=22.0,""",
    """        trunk_lean=-8.0, l_shoulder=-18.0, r_shoulder=132.0,
        r_shoulder_out=18.0, l_elbow=52.0, r_elbow=36.0, neck=22.0,""")

sub("""        trunk_lean=6.0, trunk_twist=14.0,
        l_shoulder=12.0, r_shoulder=48.0,
        l_elbow=18.0, r_elbow=28.0,""",
    """        trunk_lean=6.0, trunk_twist=14.0,
        l_shoulder=-30.0, r_shoulder=-10.0,
        l_elbow=14.0, r_elbow=52.0,""")

# The reach poses now have real working heights worth asserting.
sub("""    stand_grip = grip_point(joint_positions(POSES["stand"], stature))
    high_grip = grip_point(joint_positions(POSES["reach_high"], stature))
    assert high_grip[2] > stand_grip[2] + 0.8, (stand_grip[2], high_grip[2])""",
    """    stand_grip = grip_point(joint_positions(POSES["stand"], stature))
    high_grip = grip_point(joint_positions(POSES["reach_high"], stature))
    assert high_grip[2] > stand_grip[2] + 0.8, (stand_grip[2], high_grip[2])
    # Overhead work happens above head height, and carrying happens in
    # front of the body rather than beside it.
    assert high_grip[2] > 1.80, high_grip[2]
    carry_grip = grip_point(joint_positions(POSES["carry"], stature))
    assert carry_grip[0] > 0.25, carry_grip[0]
    assert 0.80 < carry_grip[2] < 1.05, carry_grip[2]""")

p.write_text(s, encoding="utf-8")
print("pose arm angles applied")
