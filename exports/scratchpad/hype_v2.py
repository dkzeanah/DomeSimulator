"""Add the v2 montage: the same film with the aside beats spliced in.

v1 stays exactly as it is.  v2 replaces the single "list of likes" beat
with a five-beat run carrying the verbatim asides, and renumbers.
"""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hype.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:220])
    s = s.replace(old, new, 1)


sub("from __future__ import annotations" + NL + NL + "import math",
    "from __future__ import annotations" + NL + NL
    + "import math" + NL + "from dataclasses import replace")

# --- two new scenes ----------------------------------------------------
sub("SCENES = {",
    '''def scene_hype_teslabot(app, opaque, transparent, p: float) -> None:
    """A request, addressed upward, with a dome for context."""
    _frame(opaque, 3.0, CYAN, 0.06, smoothstep(clamp(p * 1.7)))
    stature = 4.0
    # The applicant.
    joints = place_figure(
        joint_positions(POSES["reach_high"], stature), (-4.6, 0.0, 0.0), 210.0)
    draw_figure(opaque, joints, scale=stature / 1.75)
    # The requested colleague: same skeleton, rendered in metal, with a
    # second pair of arms because that is the entire point of asking.
    arrive = ease_in_out(clamp((p - 0.25) / 0.65))
    if arrive > 0.02:
        bot = place_figure(
            joint_positions(POSES["carry"], stature * 1.05),
            (5.0, 0.0, 0.0), 200.0)
        draw_figure(opaque, bot, scale=stature / 1.75,
                    skin=(0.62, 0.68, 0.76, 1.0),
                    hi_vis=(0.44, 0.50, 0.60, 1.0),
                    trousers=(0.28, 0.32, 0.40, 1.0),
                    helmet=(0.35, 0.85, 0.95, 1.0))
        shoulder = bot["chest"]
        for side in (-1.0, 1.0):
            elbow = shoulder + np.array([side * 1.15 * arrive, 0.0, -0.35])
            wrist = elbow + np.array([side * 0.95 * arrive, 0.0, 0.55])
            opaque.cylinder(shoulder, elbow, 0.11, (0.55, 0.60, 0.70, 1.0), 8)
            opaque.cylinder(elbow, wrist, 0.085, (0.55, 0.60, 0.70, 1.0), 8)
            opaque.sphere(elbow, 0.13, CYAN, 4, 8)
        app.world_labels.append(WorldLabel(
            np.array([5.0, 0.0, stature + 1.1]),
            "ONE (1) TESLABOT", (61, 211, 255)))
    app.world_labels.extend([
        WorldLabel(np.array([-4.6, 0.0, stature + 1.4]),
                   "ME, LYING ABOUT ENJOYING WIRING", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "for humanity, and related considerations",
                   (169, 188, 203)),
    ])


def scene_hype_psyche(app, opaque, transparent, p: float) -> None:
    """The actual list of likes, stated without further decoration."""
    grow = ease_in_out(clamp(p * 1.25))
    rows = (("CASH MONEY", AMBER), ("RESOURCES", GREEN),
            ("POWER", RED), ("INFLUENCE", PURPLE))
    span = 12.6
    step = span / (len(rows) - 1)
    for index, (label, colour) in enumerate(rows):
        x = -span * 0.5 + index * step
        height = (2.6 + index * 1.15) * grow
        opaque.box((x, 0.0, height * 0.5 + 0.15), (2.4, 1.2, max(0.06, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.85]), label, _rgb(colour)))
    _frame(transparent, 1.5, MUTED, 0.04)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.2]),
        "method: ruling hobos. forcibly. sue me.", (169, 188, 203)))


SCENES = {''')

sub('    "hype_socials": scene_hype_socials,',
    '    "hype_teslabot": scene_hype_teslabot,' + NL
    + '    "hype_psyche": scene_hype_psyche,' + NL
    + '    "hype_socials": scene_hype_socials,')

p.write_text(s, encoding="utf-8")
print("v2 scenes added")
