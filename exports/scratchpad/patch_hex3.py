"""Third framing pass, with the screen-space sign verified against frames.

At yaw +90 the eye sits on +Y looking back down the axis, so world +X lands
on the LEFT of frame -- which is where the teaching card is.  Rows in those
scenes therefore have to run toward negative X, not positive.  At yaw -90
(the flat-template scenes) the mapping is the other way round.
"""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hex.py")
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new, 1)


# 05 -- four cages, yaw +90
sub("    positions = np.linspace(-6.2, 12.4, len(models))",
    "    positions = np.linspace(-12.6, 6.2, len(models))")
sub('        np.array([3.1, 0.0, 6.4]),\n        "HEXAGONS: AS MANY AS YOU LIKE.',
    '        np.array([-3.2, 0.0, 6.4]),\n        "HEXAGONS: AS MANY AS YOU LIKE.')

# 07 -- cage and rack, yaw +90
sub("    centre = np.array([1.6, 0.0, 4.3])",
    "    centre = np.array([-2.0, 0.0, 4.3])")
sub('''        column, row = index % 28, index // 28
        x = -4.6 + column * 0.46
        y = 6.4 + row * 0.9
        opaque.cylinder(np.array([x, y, 0.20]),
                        np.array([x, y, 0.20 + length]), 0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([1.6, 6.4, 2.5]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([1.6, 6.4, -0.5]),''',
    '''        column, row = index % 20, index // 20
        x = -7.8 + column * 0.55
        y = 4.2 + row * 0.95
        opaque.cylinder(np.array([x, y, 0.20]),
                        np.array([x, y, 0.20 + length]), 0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-2.6, 4.2, 2.45]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([-2.6, 6.1, 2.45]),''')

# 13 -- two templates, yaw -90
sub("                    np.array([-5.2, 0.0, 3.0]), 5.4, CYAN)",
    "                    np.array([-1.1, 0.0, 3.0]), 5.4, CYAN)")
sub("                    np.array([1.4, 0.0, 3.0]), 5.4, AMBER)",
    "                    np.array([5.3, 0.0, 3.0]), 5.4, AMBER)")
sub("        WorldLabel(np.array([-5.2, 0.0, 0.4]),",
    "        WorldLabel(np.array([-1.1, 0.0, 0.4]),")
sub("        WorldLabel(np.array([1.4, 0.0, 0.4]),",
    "        WorldLabel(np.array([5.3, 0.0, 0.4]),")
sub('        WorldLabel(np.array([-1.9, 0.0, 5.6]),',
    '        WorldLabel(np.array([2.1, 0.0, 5.6]),')

# 14 -- the shape ladder, yaw +90
sub("    positions = np.linspace(-5.4, 11.4, len(models))",
    "    positions = np.linspace(-11.4, 5.4, len(models))")
sub('        np.array([3.0, 0.0, 6.4]),\n        "BIGGER AND ROUNDER',
    '        np.array([-3.0, 0.0, 6.4]),\n        "BIGGER AND ROUNDER')

# 15 -- one warped panel, yaw -72
sub("    base = np.array([-2.4, 0.0, 2.9])",
    "    base = np.array([2.2, 0.0, 2.9])")

# 16 -- warp bars, yaw +90
sub("    bar_row(opaque, app, entries, np.array([-3.4, 0.0, 0.35]), 4.2, 8.0)",
    "    bar_row(opaque, app, entries, np.array([-9.6, 0.0, 0.35]), 4.2, 8.0)")
sub('        WorldLabel(np.array([2.9, 0.0, 5.6]),',
    '        WorldLabel(np.array([-3.2, 0.0, 5.6]),')
sub('        WorldLabel(np.array([2.9, 0.0, -1.5]),',
    '        WorldLabel(np.array([-3.2, 0.0, -1.5]),')

# 18 -- the decision chart, yaw +90
sub("        x = -4.6 + index * 5.0", "        x = -10.6 + index * 5.0")
sub('        np.array([3.0, 0.0, 6.2]),\n        "MORE PANELS IS WORK',
    '        np.array([-3.1, 0.0, 6.2]),\n        "MORE PANELS IS WORK')

# 19 -- the two domes, yaw +90
sub('''    for cage, offset, tint in ((SOCCER, np.array([-2.4, 0.0, 1.1]), CYAN),
                               (GP4, np.array([8.4, 0.0, 1.1]), AMBER)):''',
    '''    for cage, offset, tint in ((SOCCER, np.array([2.4, 0.0, 1.1]), CYAN),
                               (GP4, np.array([-8.4, 0.0, 1.1]), AMBER)):''')
sub('        np.array([3.0, 0.0, 6.0]),\n        "SAME RADIUS',
    '        np.array([-3.0, 0.0, 6.0]),\n        "SAME RADIUS')

path.write_text(src, encoding="utf-8")
print("lesson_hex.py third framing pass applied")
