"""Check the hubless strut counts and compound-cut angles against the model."""

import math
import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

import numpy as np

from two_v_demo.geometry import build_demo_geometry, normalize

g = build_demo_geometry()
faces = g.hemisphere_faces
edges = g.hemisphere_edges
print(f"hemisphere: {len(faces)} triangles, {len(edges)} unique edges")
print(f"strut positions = 3 x triangles = {3 * len(faces)}")

# How many triangles use each edge?
use = {}
for face in faces:
    c = [int(v) for v in face]
    for i in range(3):
        a, b = c[i], c[(i + 1) % 3]
        use.setdefault((a, b) if a < b else (b, a), []).append(tuple(c))
shared = sum(1 for v in use.values() if len(v) == 2)
rim = sum(1 for v in use.values() if len(v) == 1)
print(f"edges with 2 triangles (2 struts side by side): {shared}")
print(f"edges with 1 triangle (rim):                    {rim}")
print(f"check 2*{shared} + 1*{rim} = {2 * shared + rim}")

# Face normals, outward.
normal_of = {}
for face in faces:
    c = [int(v) for v in face]
    pts = g.vertices[c]
    n = normalize(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
    if float(np.dot(n, pts.mean(axis=0))) < 0:
        n = -n
    normal_of[tuple(c)] = n

# Dihedral along each shared edge.
dihedral_of = {}
for edge, tris in use.items():
    if len(tris) != 2:
        continue
    cos = float(np.clip(np.dot(normal_of[tris[0]], normal_of[tris[1]]), -1, 1))
    dihedral_of[edge] = 180.0 - math.degrees(math.acos(cos))

# For every strut: its two end corner angles and the dihedral on its edge.
rows = []
for face in faces:
    c = [int(v) for v in face]
    pts = g.vertices[c]
    for i in range(3):
        a_i, b_i = c[i], c[(i + 1) % 3]
        o_i = c[(i + 2) % 3]
        A, B, O = g.vertices[a_i], g.vertices[b_i], g.vertices[o_i]
        # Corner angle of the triangle at each end of this strut.
        ang_a = math.degrees(math.acos(float(np.clip(
            np.dot(normalize(B - A), normalize(O - A)), -1, 1))))
        ang_b = math.degrees(math.acos(float(np.clip(
            np.dot(normalize(A - B), normalize(O - B)), -1, 1))))
        key = (a_i, b_i) if a_i < b_i else (b_i, a_i)
        dih = dihedral_of.get(key)
        bevel = (180.0 - dih) * 0.5 if dih is not None else None
        rows.append((ang_a, ang_b, dih, bevel))

print(f"\ntotal struts modelled: {len(rows)}")


def group(values, places=3):
    out = {}
    for v in values:
        if v is None:
            continue
        out[round(v, places)] = out.get(round(v, places), 0) + 1
    return dict(sorted(out.items()))


corner_angles = [r[0] for r in rows] + [r[1] for r in rows]
print("\ndistinct triangle corner angles (deg -> count):")
for k, v in group(corner_angles).items():
    print(f"  {k:9.3f}  x{v}")

print("\ndistinct miter settings, 90 - C/2 from square:")
miters = [90.0 - a / 2.0 for a in corner_angles]
for k, v in group(miters).items():
    print(f"  {k:9.3f}  x{v}")

print("\ndistinct dihedral folds and their half-bevels:")
for k, v in group([r[2] for r in rows]).items():
    print(f"  fold {k:9.3f}  bevel {(180 - k) / 2:8.3f}  x{v}")

# The real question: how many distinct compound setups?
setups = set()
for ang_a, ang_b, dih, bevel in rows:
    if bevel is None:
        continue
    setups.add((round(90 - ang_a / 2, 3), round(bevel, 3)))
    setups.add((round(90 - ang_b / 2, 3), round(bevel, 3)))
print(f"\ndistinct (miter, bevel) compound setups: {len(setups)}")
for s in sorted(setups):
    print(f"  miter {s[0]:8.3f}   bevel {s[1]:8.3f}")
