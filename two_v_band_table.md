# 2V Geodesic Dome on a Six-Foot Member — Every Level, Ring and Slope

Longest member (A strut): **6' 0"**  ·  second member (B strut): **5' 3-11/16"**  ·  sphere radius: **116.498 in** (9.7082 ft)
Dome height **9' 8-1/2"** (9.7082 ft)  ·  floor diameter **19' 5"** (19.4164 ft)
Hubs: **26**  ·  shared struts: **65** (35 A + 30 B)  ·  panels: **40** (10 AAA + 30 BAB)  ·  base: a 10-sided ring of **60' 0"** of chord

> Cross-checked figure for figure against Zip Tie Domes' published 2V
> calculator run at a six-foot A strut (the same check
> ``seed_model.validate_seed_model`` runs).  A = LONG, B = SHORT,
> per the package convention in ``two_v_demo/geometry.py``.

## 1 · The levels, floor to apex

| level | hubs | hub kind | height | height (ft) | × radius | × A strut | % of dome height |
|---|---|---|---|---|---|---|---|
| base ring (floor) | 10 | 4-way base | **0' 0"** | 0.000 | 0.00000 | 0.0000 | 0.0% |
| level 1 · pentagon ring | 5 | 5-way pentagon | **4' 4-1/8"** | 4.342 | 0.44721 | 0.7236 | 44.7% |
| level 1 · hexagon ring | 5 | 6-way hexagon | **5' 1-1/4"** | 5.104 | 0.52573 | 0.8507 | 52.6% |
| level 2 · pentagon band | 5 | 6-way hexagon | **8' 3-1/8"** | 8.258 | 0.85065 | 1.3764 | 85.1% |
| apex (cap) | 1 | 5-way pentagon | **9' 8-1/2"** | 9.708 | 1.00000 | 1.6180 | 100.0% |

The first band of triangles runs from the floor up to *two* rings at
two different heights: its 5 pentagon corners sit lower (
4' 4-1/8") and its 5 hexagon corners sit higher
(5' 1-1/4") — a gap of 0' 9-1/8".  The level-2 band
is the pentagon band just outside the cap, and the cap itself is
the apex sitting on it.

## 2 · The amount inward — radius, diameter, circumference of every ring

| ring | hubs | ring radius | ring diameter | circle through the hubs | share of floor circle | inward step from below |
|---|---|---|---|---|---|
| base ring (floor) | 10 | **9' 8-1/2"** (9.708 ft) | 19' 5" | **61' 0"** (61.00 ft) | 100.0% | — |
| level 1 · pentagon ring | 5 | **8' 8-3/16"** (8.683 ft) | 17' 4-3/8" | **54' 6-11/16"** (54.56 ft) | 89.4% | **1' 0-5/16"** |
| level 1 · hexagon ring | 5 | **8' 3-1/8"** (8.258 ft) | 16' 6-3/16" | **51' 10-11/16"** (51.89 ft) | 85.1% | **0' 5-1/8"** |
| level 2 · pentagon band | 5 | **5' 1-1/4"** (5.104 ft) | 10' 2-1/2" | **32' 0-13/16"** (32.07 ft) | 52.6% | **3' 1-7/8"** |
| apex (cap) | 1 | **0' 0"** (0.000 ft) | 0' 0" | **0' 0"** (0.00 ft) | 0.0% | **5' 1-1/4"** |

The base ring's hubs are joined by ten A struts, so the built floor is
a decagon of **60' 0"** of chord inside a 61' 0" circle.  The pentagon band under the apex is likewise
closed by five A struts, so its circle of 32' 0-13/16" carries 30' 0" of actual chord.  The two level-1 rings are not strut-linked:
each hub there ties to the rings above and below, not sideways.

## 3 · The slope between levels

Meridian slope: the rise of a level against how far its circle has
stepped inward from the level below (the cone the dome surface
traces between two rings).

| rise | inward (run) | rise : run | slope from horizontal | what it is |
|---|---|---|---|---|
| 4' 4-1/8" | 1' 0-5/16" | 4.236 | **76.7°** | first band, up to the pentagon ring |
| 5' 1-1/4" | 1' 5-3/8" | 3.520 | **74.1°** | first band, up to the hexagon ring |
| 3' 11" | 3' 6-15/16" | 1.094 | **47.6°** | second band, pentagon ring to pentagon band |
| 3' 1-7/8" | 3' 1-7/8" | 1.000 | **45.0°** | second band, hexagon ring to pentagon band |
| 1' 5-3/8" | 5' 1-1/4" | 0.284 | **15.9°** | the cap, pentagon band to apex |

Reading down the table: the walls go up nearly vertical, the shoulder
leans to roughly 45°, and the cap flattens to about 16° at the apex.

## 4 · The two struts, and where each one lives

| strut | length | chord factor | count | panel mix |
|---|---|---|---|---|
| A (long) | **6' 0"** (6.0000 ft) | 0.61803 | 35 | AAA panels: 10 of 40 |
| B (short) | **5' 3-11/16"** (5.3059 ft) | 0.54653 | 30 | BAB panels only: 30 of 40 |

Struts by band (each shared strut credited to its lowest band):

| band | panels | A struts | B struts |
|---|---|---|---|
| first band | 20 | 20 | 20 |
| second band | 15 | 15 | 5 |
| cap | 5 | 0 | 5 |

Where the struts lean, measured edge by edge off the mesh (each
strut's own angle from horizontal — a strut also runs sideways
around the dome, so this differs from the meridian slopes above):

| strut | angle from horizontal | count |
|---|---|---|
| A | 0.0° | 15 |
| A | 31.7° | 10 |
| A | 58.3° | 10 |
| B | 8.3° | 10 |
| B | 15.9° | 5 |
| B | 47.6° | 5 |
| B | 54.9° | 10 |

A struts appear at 0.0° (15), 31.7° (10), 58.3° (10); B struts at 8.3° (10), 15.9° (5), 47.6° (5), 54.9° (10).  The flat A struts are the base ring and the pentagon band's
ring; the steepest A struts climb the first band; the steepest B
struts climb from the floor to the pentagon corners, and the
gentlest B struts close the cap to the apex.

## 5 · The variant ways to cut this same 2V sphere

Every flat, hub-level truncation of the full 42-hub icosphere, from
the cap up.  A cut is only listed where it passes exactly through a
ring of hubs, so each base is flat with no strut trimmed.

| variant | hubs | struts (A/B) | height | height ÷ floor diameter | base | base circle through the hubs |
|---|---|---|---|---|---|---|
| cap (cut through the pentagon band) | 6 | 5 / 5 | **1' 5-3/8"** (1.450 ft) | 0.0747 | 5 hubs, 30' 0" of chord | 32' 0-13/16" |
| cut through the level-1 hexagon ring | 11 | 15 / 5 | **4' 7-1/4"** (4.604 ft) | 0.2371 | 5 hubs (not strut-linked) | 51' 10-11/16" |
| cut through the level-1 pentagon ring | 16 | 15 / 20 | **5' 4-3/8"** (5.367 ft) | 0.2764 | 5 hubs (not strut-linked) | 54' 6-11/16" |
| hemisphere (cut through the equator) — the seed dome | 26 | 35 / 30 | **9' 8-1/2"** (9.708 ft) | 0.5000 | 10 hubs, 60' 0" of chord | 61' 0" |
| cut through the lower pentagon ring | 31 | 35 / 40 | **14' 0-5/8"** (14.050 ft) | 0.7236 | 5 hubs (not strut-linked) | 54' 6-11/16" |
| cut through the lower hexagon ring | 36 | 45 / 50 | **14' 9-3/4"** (14.812 ft) | 0.7629 | 5 hubs (not strut-linked) | 51' 10-11/16" |
| full 2V sphere | 42 | 60 / 60 | **19' 5"** (19.416 ft) | 1.0000 | — | — |

The classic dome-catalogue names (3/8, 4/9, 5/8) are nominal labels,
not exact fractions: none of them lands on a hub ring of the 2V
icosphere, so a builder who wants a flat, uncut base uses one of the
ring cuts above, which sit at 0.075, 0.237, 0.276, 0.500, 0.724, 0.763, 1.000 of the floor
diameter.

## 6 · The same heights, four ways of saying them

| level | feet & inches | decimal feet | inches | × radius | × 6-ft strut | polar angle from vertical |
|---|---|---|---|---|---|---|
| base ring (floor) | **0' 0"** | 0.0000 | 0.00 | 0.00000 | 0.0000 | 90.00° |
| level 1 · pentagon ring | **4' 4-1/8"** | 4.3416 | 52.10 | 0.44721 | 0.7236 | 63.43° |
| level 1 · hexagon ring | **5' 1-1/4"** | 5.1039 | 61.25 | 0.52573 | 0.8507 | 58.28° |
| level 2 · pentagon band | **8' 3-1/8"** | 8.2583 | 99.10 | 0.85065 | 1.3764 | 31.72° |
| apex (cap) | **9' 8-1/2"** | 9.7082 | 116.50 | 1.00000 | 1.6180 | 0.00° |

## Cross-check against the published calculator

| figure | published (Zip Tie, 6-ft A) | this model | ok |
|---|---|---|---|
| dome height, ft | 9.7083 | 9.7082 | yes |
| dome diameter, ft | 19.4165 | 19.4164 | yes |
| A strut, ft | 6.0000 | 6.0000 | yes |
| B strut, ft | 5.3059 | 5.3059 | yes |
| base perimeter, ft | 60.0000 | 60.0000 | yes |
| A strut count | 35.0000 | 35.0000 | yes |
| B strut count | 30.0000 | 30.0000 | yes |
| panel count | 40.0000 | 40.0000 | yes |

