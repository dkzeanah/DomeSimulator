"""Point every camera across the line instead of along it.

Two things pushed the same way here.  Scene content is laid out along X --
rows of bars, six figures in sequence, two workers side by side -- and the
figure bends in the X-Z plane, so a viewpoint on the Y axis shows both the
sequence and the posture.  Looking down X hid both.
"""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_line.py")
s = p.read_text(encoding="utf-8")

# stage -> (yaw, pitch, distance)
CAMERAS = {
    "line_overview": (84.0, 30.0, 24.0),
    "line_why": (90.0, 22.0, 13.0),
    "line_station": (96.0, 24.0, 11.0),
    "line_bottleneck": (90.0, 26.0, 13.0),
    "line_cycle": (90.0, 17.0, 14.5),
    "line_walk": (90.0, 16.0, 12.0),
    "line_lift": (93.0, 12.0, 5.2),
    "line_carry": (90.0, 25.0, 14.0),
    "line_position": (98.0, 16.0, 9.0),
    "line_fasten": (90.0, 14.0, 9.0),
    "line_allowance": (90.0, 20.0, 11.0),
    "line_skeleton": (93.0, 10.0, 4.8),
    "line_selflift": (90.0, 18.0, 11.0),
    "line_limbs": (90.0, 18.0, 12.0),
    "line_team": (90.0, 12.0, 7.2),
    "line_overhead": (90.0, 12.0, 8.0),
    "line_work": (90.0, 16.0, 8.0),
    "line_model": (90.0, 20.0, 12.0),
    "line_efficiency": (90.0, 22.0, 13.0),
    "line_motions": (90.0, 26.0, 14.0),
    "line_stations": (90.0, 26.0, 14.0),
    "line_shift": (90.0, 22.0, 12.0),
    "line_food": (90.0, 20.0, 14.0),
    "line_recap": (84.0, 30.0, 24.0),
}

import re

changed = 0
for stage, (yaw, pitch, distance) in CAMERAS.items():
    pattern = re.compile(
        r"\(-?[\d.]+, -?[\d.]+, -?[\d.]+\), \"" + re.escape(stage) + r"\","
    )
    replacement = f'({yaw}, {pitch}, {distance}), "{stage}",'
    s, count = pattern.subn(replacement, s, count=1)
    if count != 1:
        raise SystemExit(f"camera for {stage} not found")
    changed += 1

# A catalogue element's dims are raw bounding-box extents, which can be
# two or three metres across and read as a wall rather than a part.  The
# drawn box keeps the real proportions, longest axis pointed the way the
# worker faces, scaled down only if it would not fit in frame.  The mass
# label beside it stays the real figure either way.
helper = '''
LOAD_MAX_LENGTH = 1.7


def _load_dims(dims):
    """Readable box for a carried part, keeping its real proportions."""
    values = sorted((abs(float(value)) for value in dims), reverse=True)
    while len(values) < 3:
        values.append(0.1)
    longest = max(values[0], 1e-3)
    shrink = min(1.0, LOAD_MAX_LENGTH / longest)
    return (max(0.12, values[0] * shrink),
            max(0.08, values[1] * shrink),
            max(0.06, values[2] * shrink))


DEMO_LOAD = None
'''
anchor = "def _rgb(colour) -> tuple[int, int, int]:"
if anchor not in s:
    raise SystemExit("could not find helper anchor")
s = s.replace(anchor, helper.strip() + "\n\n\n" + anchor, 1)

s = s.replace("DEMO_LOAD = None", "", 1)
s = s.replace("DEMO_ELEMENT.dims", "_load_dims(DEMO_ELEMENT.dims)")

# The lift chapter states work and fuel; the live block restates them in a
# slightly different rounding, which reads as two different answers.
old = '''        (f"work = {DEMO_COSTS[1].mechanical_joules:.0f} J",
         f"fuel = {DEMO_COSTS[1].metabolic_joules:.0f} J"),'''
new = '''        (f"load = {DEMO_MOTIONS[1].load_kg:.1f} kg",
         f"trunk share = {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} %"),'''
if old not in s:
    raise SystemExit("lift equations not found")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print(f"{changed} cameras retargeted; load box and lift equations fixed")
