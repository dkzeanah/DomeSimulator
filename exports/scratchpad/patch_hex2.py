"""Second framing pass: nothing may hide behind the teaching card.

With the camera at yaw 90 the world +X axis runs to the right of frame and
the card covers roughly the left quarter, so every row of models is shifted
right by about three units and the strut rack is moved to the near side.
"""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hex.py")
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new, 1)


# 05 -- the row of four cages
sub("    positions = np.linspace(-9.6, 9.6, len(models))",
    "    positions = np.linspace(-6.2, 12.4, len(models))")
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.4]),
        "HEXAGONS: AS MANY AS YOU LIKE.   PENTAGONS: ALWAYS TWELVE.",''',
    '''    app.world_labels.append(WorldLabel(
        np.array([3.1, 0.0, 6.4]),
        "HEXAGONS: AS MANY AS YOU LIKE.   PENTAGONS: ALWAYS TWELVE.",''')

# 07 -- lift the cage clear and stand the rack on the near side
sub('''    scale = 4.3
    centre = np.array([0.0, 0.0, 1.4])''',
    '''    scale = 3.5
    centre = np.array([1.6, 0.0, 4.3])''')
sub('''        column, row = index % 30, index // 30
        x = -6.9 + column * 0.475
        y = -6.4 - row * 0.85
        opaque.cylinder(np.array([x, y, 0.30]),
                        np.array([x, y, 0.30 + length]), 0.055, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, -6.4, 2.6]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([0.0, -8.1, 0.55]),''',
    '''        column, row = index % 28, index // 28
        x = -4.6 + column * 0.46
        y = 6.4 + row * 0.9
        opaque.cylinder(np.array([x, y, 0.20]),
                        np.array([x, y, 0.20 + length]), 0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([1.6, 6.4, 2.5]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([1.6, 6.4, -0.5]),''')

# 08 -- clear the card
sub("    positions = np.linspace(-3.3, 3.3, len(order))",
    "    positions = np.linspace(-1.2, 5.4, len(order))")
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.1]),
        "TWO TEMPLATES CUT THE WHOLE SKIN", (111, 235, 155),
    ))''',
    '''    app.world_labels.append(WorldLabel(
        np.array([2.1, 0.0, 5.1]),
        "TWO TEMPLATES CUT THE WHOLE SKIN", (111, 235, 155),
    ))''')

# 13 -- the camera looks from -Y here, so shift the pair the other way
sub("                    np.array([-3.3, 0.0, 3.0]), 5.4, CYAN)",
    "                    np.array([-5.2, 0.0, 3.0]), 5.4, CYAN)")
sub("                    np.array([3.3, 0.0, 3.0]), 5.4, AMBER)",
    "                    np.array([1.4, 0.0, 3.0]), 5.4, AMBER)")
sub("        WorldLabel(np.array([-3.3, 0.0, 0.4]),",
    "        WorldLabel(np.array([-5.2, 0.0, 0.4]),")
sub("        WorldLabel(np.array([3.3, 0.0, 0.4]),",
    "        WorldLabel(np.array([1.4, 0.0, 0.4]),")
sub('''        WorldLabel(np.array([0.0, 0.0, 5.6]),
                   "RAISING THE FREQUENCY BREAKS THE REGULAR HEXAGON",''',
    '''        WorldLabel(np.array([-1.9, 0.0, 5.6]),
                   "RAISING THE FREQUENCY BREAKS THE REGULAR HEXAGON",''')

# 14 -- the shape ladder
sub("    positions = np.linspace(-8.4, 8.4, len(models))",
    "    positions = np.linspace(-5.4, 11.4, len(models))")
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.4]),
        "BIGGER AND ROUNDER COSTS SHAPES, EVERY TIME", (111, 235, 155),
    ))''',
    '''    app.world_labels.append(WorldLabel(
        np.array([3.0, 0.0, 6.4]),
        "BIGGER AND ROUNDER COSTS SHAPES, EVERY TIME", (111, 235, 155),
    ))''')

# 15 -- the camera looks from -Y
sub("    base = np.array([0.0, 0.0, 2.9])",
    "    base = np.array([-2.4, 0.0, 2.9])")

# 16 -- the warp bars
sub("    bar_row(opaque, app, entries, np.array([-6.0, 0.0, 0.35]), 4.0, 8.0)",
    "    bar_row(opaque, app, entries, np.array([-3.4, 0.0, 0.35]), 4.2, 8.0)")
sub('''        WorldLabel(np.array([0.0, 0.0, 5.6]),
                   f"WORST PANEL WARP AT R = {LESSON_RADIUS_IN:.0f} in",''',
    '''        WorldLabel(np.array([2.9, 0.0, 5.6]),
                   f"WORST PANEL WARP AT R = {LESSON_RADIUS_IN:.0f} in",''')
sub('''        WorldLabel(np.array([0.0, 0.0, -1.5]),
                   "FLAT PANEL + WARPED FRAME = A GAP TO SEAL",''',
    '''        WorldLabel(np.array([2.9, 0.0, -1.5]),
                   "FLAT PANEL + WARPED FRAME = A GAP TO SEAL",''')

# 18 -- the decision chart
sub("        x = -7.5 + index * 5.0", "        x = -4.6 + index * 5.0")
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.2]),
        "MORE PANELS IS WORK YOU REPEAT. MORE LENGTHS IS WORK YOU GET WRONG.",''',
    '''    app.world_labels.append(WorldLabel(
        np.array([3.0, 0.0, 6.2]),
        "MORE PANELS IS WORK YOU REPEAT. MORE LENGTHS IS WORK YOU GET WRONG.",''')

# 19 -- the two domes
sub('''    for cage, offset, tint in ((SOCCER, np.array([-5.4, 0.0, 1.1]), CYAN),
                               (GP4, np.array([5.4, 0.0, 1.1]), AMBER)):''',
    '''    for cage, offset, tint in ((SOCCER, np.array([-2.4, 0.0, 1.1]), CYAN),
                               (GP4, np.array([8.4, 0.0, 1.1]), AMBER)):''')
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.0]),
        f"SAME RADIUS, SAME SPHERE, DIFFERENT SHOP", (111, 235, 155),
    ))''',
    '''    app.world_labels.append(WorldLabel(
        np.array([3.0, 0.0, 6.0]),
        "SAME RADIUS, SAME SPHERE, DIFFERENT SHOP", (111, 235, 155),
    ))''')

src = src.replace("20.0, (90.0, 20.0, 21.0), \"hex_euler\",",
                  "20.0, (90.0, 20.0, 19.5), \"hex_euler\",")
src = src.replace("18.0, (90.0, 26.0, 17.5), \"hex_soccer_struts\",",
                  "18.0, (90.0, 20.0, 17.0), \"hex_soccer_struts\",")

path.write_text(src, encoding="utf-8")
print("lesson_hex.py second framing pass applied")
