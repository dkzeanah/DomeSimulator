"""Lift the machines clear of the ground slab and spread the labels.

The renderer draws a ground slab spanning z -0.34 to -0.06.  Both saw
tables were built straddling z=0, so the two solids interpenetrated and
the depth buffer tore them into stripes.  Everything now sits on top of
the ground instead of inside it.
"""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_cuts.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:240])
    s = s.replace(old, new, 1)


sub(
    'JIG = (0.42, 0.34, 0.24, 1.0)',
    'JIG = (0.42, 0.34, 0.24, 1.0)' + NL + NL
    + "TABLE_Z = 1.30" + NL
    + '"""Height of a saw table above the scene floor.' + NL + NL
    + "The renderer's ground slab occupies z -0.34 to -0.06, so anything" + NL
    + "built straddling zero interpenetrates it and the depth buffer tears" + NL
    + 'both solids into stripes. Everything here sits on top of it."""',
)

# --- table saw ---------------------------------------------------------
sub(
    '    _prism(opaque, (0.0, 0.0, -0.25), (18.0, 13.0, 0.5), DARK_STEEL)' + NL
    + '    _prism(opaque, (0.0, 0.0, -1.9), (14.0, 10.0, 2.8), (0.18, 0.21, 0.26, 1.0))' + NL
    + '    # The slot the blade comes through.' + NL
    + '    _prism(opaque, (0.0, 0.0, 0.01), (BLADE_R * 2.2, 0.30, 0.06),' + NL
    + '           (0.06, 0.08, 0.11, 1.0))',
    '    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.25), (15.0, 10.5, 0.5), DARK_STEEL)' + NL
    + '    _prism(opaque, (0.0, 0.0, (TABLE_Z - 0.5) * 0.5),' + NL
    + '           (11.0, 8.0, TABLE_Z - 0.5), (0.18, 0.21, 0.26, 1.0))' + NL
    + '    # The slot the blade comes through.' + NL
    + '    _prism(opaque, (0.0, 0.0, TABLE_Z + 0.02), (BLADE_R * 2.2, 0.30, 0.06),' + NL
    + '           (0.06, 0.08, 0.11, 1.0))',
)
sub(
    '    hub = np.array([0.0, 0.0, -BLADE_R * 0.55])',
    '    hub = np.array([0.0, 0.0, TABLE_Z - BLADE_R * 0.62])',
)
sub(
    '    _prism(opaque, (0.0, fence_y, 0.9), (17.0, 0.5, 1.8), (0.55, 0.58, 0.64, 1.0))',
    '    _prism(opaque, (0.0, fence_y, TABLE_Z + 0.9), (14.5, 0.5, 1.8),' + NL
    + '           (0.55, 0.58, 0.64, 1.0))',
)
sub(
    '    _prism(opaque, (x, fence_y - 0.35 - STOCK_W * 0.5, 0.35 + STOCK_T * 0.5),' + NL
    + '           (length, STOCK_W, STOCK_T), TIMBER)',
    '    _prism(opaque, (x, fence_y - 0.35 - STOCK_W * 0.5,' + NL
    + '                   TABLE_Z + STOCK_T * 0.5),' + NL
    + '           (length, STOCK_W, STOCK_T), TIMBER)',
)

# --- mitre saw ---------------------------------------------------------
sub(
    '    _prism(opaque, (0.0, 0.0, -0.3), (15.0, 11.0, 0.6), DARK_STEEL)' + NL
    + '    opaque.disc(np.array([0.0, 0.0, 0.02]), 4.2, (0.30, 0.34, 0.40, 1.0), 36)',
    '    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.3), (13.0, 9.5, 0.6), DARK_STEEL)' + NL
    + '    opaque.disc(np.array([0.0, 0.0, TABLE_Z + 0.02]), 3.8,' + NL
    + '                (0.30, 0.34, 0.40, 1.0), 36)',
)
sub(
    '    _prism(opaque, (0.0, 2.6, 1.1), (13.0, 0.55, 2.2),' + NL
    + '           (0.52, 0.56, 0.62, 1.0), swing_deg)',
    '    _prism(opaque, (0.0, 2.6, TABLE_Z + 1.1), (12.0, 0.55, 2.2),' + NL
    + '           (0.52, 0.56, 0.62, 1.0), swing_deg)',
)
sub(
    '        _prism(opaque, (0.0, 1.55, 0.05 + STOCK_W * 0.5),' + NL
    + '               (10.0, STOCK_T, STOCK_W), TIMBER, swing_deg)',
    '        _prism(opaque, (0.0, 1.55, TABLE_Z + 0.05 + STOCK_W * 0.5),' + NL
    + '               (10.0, STOCK_T, STOCK_W), TIMBER, swing_deg)',
)
sub(
    '    _prism(opaque, (0.0, 4.6, 3.4), (1.5, 1.5, 7.2), (0.34, 0.38, 0.44, 1.0))' + NL
    + '    hub_z = 6.4 - drop * 4.9',
    '    _prism(opaque, (0.0, 4.6, TABLE_Z + 3.4), (1.5, 1.5, 7.2),' + NL
    + '           (0.34, 0.38, 0.44, 1.0))' + NL
    + '    hub_z = TABLE_Z + 6.4 - drop * 4.9',
)
sub(
    '    opaque.cylinder(np.array([0.0, 4.6, 6.6]), hub, 0.34,',
    '    opaque.cylinder(np.array([0.0, 4.6, TABLE_Z + 6.6]), hub, 0.34,',
)

# --- sled --------------------------------------------------------------
sub(
    '    _prism(opaque, (0.0, 0.0, -0.25), (18.0, 13.0, 0.5), DARK_STEEL)' + NL
    + '    _prism(opaque, (0.0, 0.0, 0.01), (BLADE_R * 2.2, 0.30, 0.06),' + NL
    + '           (0.06, 0.08, 0.11, 1.0))' + NL
    + '    _blade(opaque, np.array([0.0, 0.0, -BLADE_R * 0.62]),' + NL
    + '           np.array([0.0, 1.0, 0.0]), BLADE_R)',
    '    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.25), (15.0, 10.5, 0.5), DARK_STEEL)' + NL
    + '    _prism(opaque, (0.0, 0.0, (TABLE_Z - 0.5) * 0.5),' + NL
    + '           (11.0, 8.0, TABLE_Z - 0.5), (0.18, 0.21, 0.26, 1.0))' + NL
    + '    _prism(opaque, (0.0, 0.0, TABLE_Z + 0.02), (BLADE_R * 2.2, 0.30, 0.06),' + NL
    + '           (0.06, 0.08, 0.11, 1.0))' + NL
    + '    _blade(opaque, np.array([0.0, 0.0, TABLE_Z - BLADE_R * 0.70]),' + NL
    + '           np.array([0.0, 1.0, 0.0]), BLADE_R)',
)
for old, new in (
    ('    _prism(opaque, (0.0, y, 0.32), (13.0, 8.5, 0.28), JIG)',
     '    _prism(opaque, (0.0, y, TABLE_Z + 0.32), (11.5, 7.5, 0.28), JIG)'),
    ('        _prism(opaque, (0.0, y + offset, 0.80), (13.0, 0.7, 1.7),' + NL
     + '               (0.34, 0.27, 0.19, 1.0))',
     '        _prism(opaque, (0.0, y + offset, TABLE_Z + 0.80), (11.5, 0.7, 1.7),' + NL
     + '               (0.34, 0.27, 0.19, 1.0))'),
    ('    _prism(opaque, (0.0, y - 0.6, 0.95), (12.0, 0.55, 1.0),' + NL
     + '           (0.58, 0.42, 0.22, 1.0), fence_deg)',
     '    _prism(opaque, (0.0, y - 0.6, TABLE_Z + 0.95), (11.0, 0.55, 1.0),' + NL
     + '           (0.58, 0.42, 0.22, 1.0), fence_deg)'),
    ('        _prism(opaque, (0.0, y - 0.6, 0.95), (1.1, 0.9, 1.05),' + NL
     + '               (0.10, 0.12, 0.15, 1.0), fence_deg)',
     '        _prism(opaque, (0.0, y - 0.6, TABLE_Z + 0.95), (1.1, 0.9, 1.05),' + NL
     + '               (0.10, 0.12, 0.15, 1.0), fence_deg)'),
    ('    _prism(opaque, (offset[0], y - 0.6 + offset[1] + 0.5,' + NL
     + '                    0.46 + STOCK_W * 0.5),' + NL
     + '           (9.0, STOCK_T, STOCK_W), TIMBER, fence_deg)',
     '    _prism(opaque, (offset[0], y - 0.6 + offset[1] + 0.5,' + NL
     + '                    TABLE_Z + 0.46 + STOCK_W * 0.5),' + NL
     + '           (9.0, STOCK_T, STOCK_W), TIMBER, fence_deg)'),
    ('    _prism(opaque, (stop[0], y - 0.6 + stop[1] + 0.5, 0.9),' + NL
     + '           (0.9, 1.4, 1.1), GREEN, fence_deg)',
     '    _prism(opaque, (stop[0], y - 0.6 + stop[1] + 0.5, TABLE_Z + 0.9),' + NL
     + '           (0.9, 1.4, 1.1), GREEN, fence_deg)'),
):
    sub(old, new)

# --- labels: spread them so they stop stacking -------------------------
sub(
    '        WorldLabel(np.array([0.0, 0.0, BLADE_R * 0.9]),' + NL
    + '                   f"BLADE TILT {PLAN.bevel_deg:.3f} deg", (61, 211, 255)),' + NL
    + '        WorldLabel(np.array([-6.4, 2.2, 2.6]),' + NL
    + '                   f"height {projection:.4f} in' + chr(92) + 'n"' + NL
    + '                   f"(square would be {STOCK_THICKNESS_IN:g})", (255, 177, 62)),' + NL
    + '        WorldLabel(np.array([6.6, 2.2, 2.2]),' + NL
    + '                   "ONE PASS, FULL LENGTH", (111, 235, 155)),' + NL
    + '        WorldLabel(np.array([0.0, -4.4, 1.4]),' + NL
    + '                   "marked edge against the fence, every stick, no exceptions",' + NL
    + '                   (169, 188, 203)),',
    '        WorldLabel(np.array([0.0, -1.6, TABLE_Z + BLADE_R * 0.75]),' + NL
    + '                   f"BLADE TILT {PLAN.bevel_deg:.3f} deg", (61, 211, 255)),' + NL
    + '        WorldLabel(np.array([-6.2, -3.2, TABLE_Z + 3.4]),' + NL
    + '                   f"height {projection:.4f} in' + chr(92) + 'n"' + NL
    + '                   f"(square would be {STOCK_THICKNESS_IN:g})", (255, 177, 62)),' + NL
    + '        WorldLabel(np.array([6.2, 3.4, TABLE_Z + 2.6]),' + NL
    + '                   "ONE PASS, FULL LENGTH", (111, 235, 155)),' + NL
    + '        WorldLabel(np.array([0.0, -4.6, TABLE_Z - 0.4]),' + NL
    + '                   "marked edge against the fence, every stick, no exceptions",' + NL
    + '                   (169, 188, 203)),',
)
sub(
    '        WorldLabel(np.array([0.0, 0.0, 4.4]),' + NL
    + '                   f"ONE PASS  -  fence {PLAN.sled_fence_deg:.3f} deg,  "' + NL
    + '                   f"travel {sled_capacity_in(PLAN.mitre_deg):.2f} in",' + NL
    + '                   (61, 211, 255)),' + NL
    + '        WorldLabel(np.array([-6.2, -2.6, 2.0]),' + NL
    + '                   "bevelled edge down' + chr(92) + 'nagainst the fence", (255, 177, 62)),' + NL
    + '        WorldLabel(np.array([0.0, 0.0, -1.1]),' + NL
    + '                   "let the blade stop before you lift the work",' + NL
    + '                   (169, 188, 203)),',
    '        WorldLabel(np.array([0.0, -1.0, TABLE_Z + 4.6]),' + NL
    + '                   f"ONE PASS  -  fence {PLAN.sled_fence_deg:.3f} deg,  "' + NL
    + '                   f"travel {sled_capacity_in(PLAN.mitre_deg):.2f} in",' + NL
    + '                   (61, 211, 255)),' + NL
    + '        WorldLabel(np.array([-6.4, -3.4, TABLE_Z + 2.4]),' + NL
    + '                   "bevelled edge down' + chr(92) + 'nagainst the fence", (255, 177, 62)),' + NL
    + '        WorldLabel(np.array([0.0, -4.8, TABLE_Z - 0.5]),' + NL
    + '                   "let the blade stop before you lift the work",' + NL
    + '                   (169, 188, 203)),',
)

p.write_text(s, encoding="utf-8")
print("machines lifted clear of the ground; labels spread")
