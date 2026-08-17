# 2V Geodesic Masterclass - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. The question hidden in two boards

Time: 00:00:00.000 - 00:00:21.040

Your 72 in and 63.5 in members are already telling us the sphere.

A 2V dome does not ask its two strut classes to be in the golden ratio. It inherits phi in the parent icosahedron, then changes the edge geometry when straight midpoints are projected back to a sphere.

On-screen math:

- measured ratio = 72 / 63.5 = 1.133858
- phi = 1.618034  (not the target)

## 02. Why domes triangulate

Time: 00:00:21.040 - 00:00:40.920

A triangle carries load without changing shape; a square needs a brace.

Push the top node: the force resolves into axial paths along the edges. Triangulation trades bending-prone panels for a network of tension and compression members. Real joints and foundations still require engineering.

On-screen math:

- F = F_compression + F_tension
- geometry explains form; engineering sizes members

## 03. The five regular starting points

Time: 00:00:40.920 - 00:01:00.320

The icosahedron wins because twenty small faces begin closest to a sphere.

Each Platonic solid has one regular face type and one vertex arrangement. More evenly distributed vertices mean a smaller correction when we project the surface outward. The icosahedron gives twenty equilateral launch pads.

On-screen math:

- faces: 4, 6, 8, 12, 20
- 2V means: divide every parent edge into 2 segments

## 04. Where the golden ratio really lives

Time: 00:01:00.320 - 00:01:26.920

Phi builds the twelve parent vertices—not the finished strut ratio.

The coordinate families (0, ±1, ±phi), (±1, ±phi, 0), and (±phi, 0, ±1) place twelve points at one common radius. Any neighboring pair is exactly 2 units apart before normalization.

On-screen math:

- phi = (1 + sqrt(5)) / 2
- R_raw = sqrt(1 + phi^2)
- edge_raw = 2

## 05. Put the icosahedron on a unit sphere

Time: 00:01:26.920 - 00:01:45.280

One division turns raw coordinates into reusable chord factors.

Normalize each vertex by its distance from the origin. Now the sphere radius is exactly one. Every measured edge is a multiplier that can later be scaled to inches, feet, meters, or any other unit.

On-screen math:

- v_hat = v / ||v||
- parent chord = 2 / sqrt(1 + phi^2) = 1.051462 R

## 06. Split every parent edge in half

Time: 00:01:45.280 - 00:02:03.520

Thirty parent edges create thirty new midpoint candidates.

The arithmetic midpoint is easy: average the two endpoint vectors. But that point lies inside the sphere. Leaving it there makes a faceted icosahedron subdivision—not a geodesic sphere.

On-screen math:

- m = (a + b) / 2
- ||m|| = 0.850651 < 1

## 07. Project the midpoints outward

Time: 00:02:03.520 - 00:02:20.520

Normalization is the exact radial projection back to the sphere.

Each midpoint travels on a ray from the origin until its radius is one. The new point changes the chord distances inside every subdivided face. That single operation is where the two finished lengths appear.

On-screen math:

- p = m / ||m||
- projection distance = 1 - ||m|| = 0.149349 R

## 08. Measure and group every chord

Time: 00:02:20.520 - 00:02:38.320

120 sphere edges collapse into exactly two numerical classes.

SHORT connects a parent vertex to a projected midpoint. LONG connects two projected midpoints. Color grouping is numerical: equal lengths receive equal colors—no letter convention is required.

On-screen math:

- SHORT = 0.546533 R
- LONG = 0.618034 R
- LONG / SHORT = 1.130826

## 09. Four routes to the same answer

Time: 00:02:38.320 - 00:03:03.360

Coordinates, dot products, central angles, and the chord formula agree.

Coordinate route: subtract endpoint vectors and take the magnitude. Angle route: theta = acos(u dot v), then chord = 2R sin(theta/2). Law of cosines, a spreadsheet, Python, and CAD must reproduce the same values.

On-screen math:

- c = ||R u - R v||
- theta = acos(u . v)
- c = 2 R sin(theta / 2)

## 10. Audit the 72 in / 63.5 in dome

Time: 00:03:03.360 - 00:03:22.520

Your ratio is close; the two measurements imply radii only fractions apart.

Use each member independently to estimate radius, then use a least-squares fit when both measurements contain cutting, hub, or tape error. Center-to-center geometry must be separated from physical cut length.

On-screen math:

- R_long = 72 / 0.618034
- R_short = 63.5 / 0.546533
- best R minimizes both residuals

## 11. From radius to a cut list

Time: 00:03:22.520 - 00:03:44.520

Scale the unit model once; then apply a documented connector deduction.

A hemisphere contains 65 unique structural edges and 40 triangular faces. The theoretical lengths are hub-center to hub-center. Tube, timber, tabs, and commercial hubs each need their own verified end allowance.

On-screen math:

- center length = chord factor x R
- cut length = center length - connector deduction

## 12. Panels, hubs, and build sequence

Time: 00:03:44.520 - 00:04:04.720

Two triangle families repeat; hub angles are connector-system dependent.

Make full-size gauges for SHORT and LONG, batch-cut, and label every part. Dry-build repeating triangles before raising rings from the base upward. PVC, timber, and tube share centerlines—not end cuts or structural capacity.

On-screen math:

- 30 x SHORT-SHORT-LONG panels
- 10 x LONG-LONG-LONG panels
- base ring: 10 vertices

## 13. Close the measurement loop

Time: 00:04:04.720 - 00:04:24.760

A good build is calculated, fabricated, measured, and corrected.

Check member gauges, base decagon diagonals, hub-center radius, and level. Small repeated errors accumulate around a ring. Correct them before the apex. For occupied or load-bearing structures, use local code and an engineer.

On-screen math:

- check: length -> triangle -> ring -> radius -> height
- expected dome height = R

## 14. The whole transformation

Time: 00:04:24.760 - 00:04:40.960

Phi chooses the parent points; projection chooses the finished members.

Raw phi coordinates become a normalized icosahedron. Midpoints move outward, two chord factors emerge, and one scale factor turns the unit geometry into a buildable 2V dome.

On-screen math:

- p
- h
- i
-  
- -
- >
-  
- i
- c
- o
- s
- a
- h
- e
- d
- r
- o
- n
-  
- -
- >
-  
- 2
- V
-  
- s
- u
- b
- d
- i
- v
- i
- s
- i
- o
- n
-  
- -
- >
-  
- p
- r
- o
- j
- e
- c
- t
- i
- o
- n
-  
- -
- >
-  
- S
- H
- O
- R
- T
-  
- +
-  
- L
- O
- N
- G
-  
- -
- >
-  
- s
- c
- a
- l
- e
