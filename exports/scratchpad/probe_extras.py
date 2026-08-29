"""Numbers for the storm shelter, the airflow shell, and the franken-dome."""

import math
import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

import numpy as np

from two_v_demo.geometry import build_demo_geometry, normalize

g = build_demo_geometry()
faces = g.hemisphere_faces
print("--- triangle classes on the dome half ---")
sig = {}
for face in faces:
    c = [int(v) for v in face]
    pts = g.vertices[c]
    lengths = tuple(sorted(round(float(np.linalg.norm(pts[i] - pts[(i + 1) % 3])), 9)
                           for i in range(3)))
    sig.setdefault(lengths, 0)
    sig[lengths] += 1
for lengths, count in sorted(sig.items(), key=lambda kv: -kv[1]):
    # Heron, per unit radius.
    a, b, c_ = lengths
    s = (a + b + c_) / 2
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c_)))
    print(f"  x{count:<3} sides {a:.6f} {b:.6f} {c_:.6f}  area {area:.6f} R^2")

total_area_factor = 0.0
for lengths, count in sig.items():
    a, b, c_ = lengths
    s = (a + b + c_) / 2
    total_area_factor += count * math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c_)))
print(f"  total panel area = {total_area_factor:.6f} R^2")
print(f"  (a full hemisphere surface is 2*pi*R^2 = {2 * math.pi:.6f} R^2, "
      f"so the flat panels are {total_area_factor / (2 * math.pi) * 100:.1f}% of it)")

print("\n--- micro storm shelter: 40 triangles from one 10ft x 5ft sheet ---")
SHEET_W, SHEET_H = 120.0, 60.0
sheet_area = SHEET_W * SHEET_H
print(f"sheet = {SHEET_W:.0f} x {SHEET_H:.0f} in = {sheet_area:,.0f} sq in")
for eff_name, eff in (("perfect (impossible)", 1.00),
                      ("strip-nested pairs", 0.85),
                      ("laser with kerf + margin", 0.78)):
    radius = math.sqrt(sheet_area * eff / total_area_factor)
    # Interior headroom of a hemisphere is the radius itself.
    floor_d = 2 * radius
    print(f"  {eff_name:<26} R = {radius:6.2f} in "
          f"-> {floor_d:6.2f} in across, {radius:5.2f} in headroom, "
          f"floor {math.pi * radius ** 2 / 144:5.2f} sq ft")

print("\n--- airflow: the shell as a filter ---")
R_IN = 60.0  # a 10 ft diameter workshop dome
R_M = R_IN * 0.0254
shell_area_m2 = 2 * math.pi * R_M ** 2
volume_m3 = (2.0 / 3.0) * math.pi * R_M ** 3
print(f"dome R = {R_IN:.0f} in = {R_M:.3f} m")
print(f"  shell area  {shell_area_m2:7.3f} m^2")
print(f"  volume      {volume_m3:7.3f} m^3 = {volume_m3 * 35.3147:.1f} cu ft")
for ach_name, ach in (("general ventilation", 6.0),
                      ("welding fume control", 20.0),
                      ("aggressive purge", 40.0)):
    m3_per_h = volume_m3 * ach
    cfm = m3_per_h * 0.588578
    face_velocity = m3_per_h / 3600.0 / shell_area_m2  # m/s through the shell
    print(f"  {ach_name:<22} {ach:4.0f} ACH -> {cfm:6.1f} CFM, "
          f"face velocity {face_velocity * 1000:6.2f} mm/s "
          f"({face_velocity * 196.85:5.1f} ft/min)")

print("\n--- franken-dome hardware ---")
TRIANGLES = len(faces)
BRACKETS = TRIANGLES * 3
SCREWS_PER_BRACKET = 8
edges_all = 65
edges_shared = 55
print(f"  {TRIANGLES} triangles x 3 corners = {BRACKETS} brackets")
print(f"  {BRACKETS} brackets x {SCREWS_PER_BRACKET} screws = "
      f"{BRACKETS * SCREWS_PER_BRACKET:,} screws")
print(f"  2 bolts per edge x {edges_all} edges = {edges_all * 2} bolts "
      f"(+ {edges_all * 2} nuts, {edges_all * 4} washers)")
print(f"  of those, {edges_shared} edges join two triangles = "
      f"{edges_shared * 2} structural bolts")
DAYS = 10
print(f"  {TRIANGLES} triangles in {DAYS} days = {TRIANGLES / DAYS:.1f} triangles/day")
print(f"  = {BRACKETS * SCREWS_PER_BRACKET / DAYS:.0f} screws/day")
MONTHS_STOOD = 6
print(f"  stood {MONTHS_STOOD} months = {MONTHS_STOOD * 30 / DAYS:.0f}x its own build time")
