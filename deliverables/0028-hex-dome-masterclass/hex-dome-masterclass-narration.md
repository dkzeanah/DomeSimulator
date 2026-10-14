# Hexagonal Dome Masterclass - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. The shape everything reaches for

Time: 00:00:00.000 - 00:00:29.288

A hexagon encloses the most floor for the least edge that still tiles.

Bees use it, basalt cools into it, and a soap froth settles into it, because a hexagon walls off more area per foot of wall than a square or a triangle while still leaving no gap. That is why builders keep asking for a dome made of hexagons. This lesson answers that request honestly: what you can have, what you cannot, and exactly what the difference costs in the shop.

On-screen math:

- hexagon area = 2.598 x side^2
- perimeter per unit area: hexagon beats square

## 02. A sheet of hexagons will not curve

Time: 00:00:29.288 - 00:01:02.104

Three hexagon corners use up all three hundred and sixty degrees.

Stand at any corner of a hexagon tiling and three panels meet there. Each brings a hundred and twenty degrees, and three of those is exactly three hundred and sixty: a full turn, flat, with nothing left over. A surface can only bend where the angle around a corner adds up to less than a full turn. The regular hexagon has no slack to give, so a sheet of them stays a sheet no matter how many you add.

On-screen math:

- 3 x 120 = 360 deg
- spare angle = 0 -> zero curvature

## 03. Curvature is bought with missing angle

Time: 00:01:02.104 - 00:01:32.592

Cut a wedge out of a flat disc and it has to rise into a cone.

Take a paper disc, cut one wedge out, and pull the two cut edges together. The paper cannot lie flat any more; it lifts into a cone. Nothing was stretched. The only thing that changed is that there is less than a full turn of paper around the centre. That missing angle is the whole mechanism of curvature, and it is the only currency a dome has to spend.

On-screen math:

- missing angle -> curvature
- flat = 360 deg   domed < 360 deg

## 04. The pentagon is where the angle comes from

Time: 00:01:32.592 - 00:01:59.408

Swap one hexagon for a pentagon and thirty-six degrees go missing.

A regular pentagon corner is a hundred and eight degrees. Three of them come to three hundred and twenty-four, which leaves thirty-six degrees of slack at that corner. Fold the slack out and the surface pulls into a bowl. Every hexagon dome you have ever seen is doing this: hexagons carry the field, and pentagons do all of the curving.

On-screen math:

- pentagon corner = 108 deg
- 3 x 108 = 324 deg
- spare = 36 deg per pentagon

## 05. Exactly twelve pentagons. Always.

Time: 00:01:59.408 - 00:02:39.184

The hexagon count cancels out of the arithmetic. The pentagon count cannot.

Descartes proved that any closed convex cage is missing exactly seven hundred and twenty degrees in total, no matter its size. A hexagon corner contributes nothing to that budget, and each pentagon contributes sixty. Seven hundred and twenty divided by sixty is twelve. Run the same argument through Euler's formula and the hexagons cancel algebraically, leaving the same answer. Twenty hexagons or two thousand, the cage still closes on exactly twelve pentagons.

On-screen math:

- V - E + F = 2
- F = P + H,  E = (5P + 6H)/2,  V = (5P + 6H)/3
- -> P/6 = 2  ->  P = 12
- total deficit = 720 deg = 12 x 60

## 06. The single-hexagon dome

Time: 00:02:39.184 - 00:03:14.136

Twenty identical hexagons, twelve identical pentagons, ninety identical struts.

This is the cage you want if one shape is the goal: the truncated icosahedron, the pattern on a football. Every hexagon is regular and identical to every other. Every pentagon is regular and identical to every other. And every one of its ninety struts is exactly the same length, so the whole frame comes off one saw setting. No other hexagonal cage on a sphere is this kind to a builder.

On-screen math:

- 20 hexagons + 12 pentagons = 32 panels
- 90 struts, 60 hubs
- V - E + F = 60 - 90 + 32 = 2

## 07. One strut length, cut ninety times

Time: 00:03:14.136 - 00:03:45.392

Set the stop block once and every member in the building is right.

Because all ninety struts share one length, the cut list is a single line. Set a stop block on the saw, cut ninety pieces, and check a sample against a master gauge rather than a tape. The number the geometry gives you is hub centre to hub centre, so subtract the connector allowance for your chosen hub before you cut. Measure that allowance on a real assembled joint. Do not take it from a catalogue.

On-screen math:

- centre length = chord factor x R
- cut length = centre length - deduction
- one length x 90 pieces

## 08. Two flat templates cut the whole skin

Time: 00:03:45.392 - 00:04:20.248

One hexagon jig and one pentagon jig cover all thirty-two panels.

Both panel shapes are genuinely flat: their corners lie in a plane, so you can cut them from sheet goods with no tricks. Make one full-size hexagon template and one pentagon template out of a scrap sheet, and trace every panel from those two. Cut them slightly oversize, fit them to the raised frame, then trim. The frame is always slightly less perfect than the arithmetic, and the panel is where you absorb that.

On-screen math:

- hexagon: 6 equal sides, 6 equal corners
- pentagon: 5 equal sides, 5 equal corners
- both exactly planar

## 09. Where do you cut it off?

Time: 00:04:20.248 - 00:05:00.624

A hexagon cage has no level equator, so its rim comes out as a zigzag.

A triangulated dome can be built to have a flat ring of hubs at the equator. A hexagon cage cannot: no ring of its struts runs level, so wherever you stop, the bottom edge rises and falls. On a twenty foot dome that zigzag is over three feet deep. You have two honest options. Build a level stem wall and let the zigzag sit on top of it, or cut the bottom row of panels along a chalked level line and flash the cut. Either way, decide before you cut a single strut.

On-screen math:

- no strut runs level -> the rim steps
- rim spread = high corner - low corner
- stem wall makes up the difference

## 10. Raising it, rim to crown

Time: 00:05:00.624 - 00:05:36.944

Build complete rings, check the diameter, then close the crown last.

Lay the rim out on the stem wall and bolt the first course of hubs down. Work upward one complete ring at a time, never up one side, so error spreads evenly instead of piling up in one place. Measure the diameter across each finished ring in three directions before you start the next one. Leave the crown panel until last; it is where every accumulated millimetre finally shows up, and it is far easier to trim one panel than to unbolt a ring.

On-screen math:

- ring by ring, never one side at a time
- check diameter in three directions per ring
- crown closes last

## 11. Now you want it bigger

Time: 00:05:36.944 - 00:06:07.912

The single-hexagon cage comes in exactly one pattern. For more, subdivide.

The football cage is a fixed pattern. You can scale it, but you cannot make it finer, and past about eight metres across its panels get too big to handle and too flat to look round. To get a finer cage you subdivide the underlying triangulated sphere and take its dual. That is the family called Goldberg polyhedra, and it is where the second half of this lesson lives.

On-screen math:

- GP(1,1) = football, one pattern only
- finer cage -> subdivide, then dualise

## 12. Every triangle corner becomes one panel

Time: 00:06:07.912 - 00:06:43.152

The dual swaps corners for panels: five-way corners become the pentagons.

Take a two-frequency geodesic sphere. Mark the centre of every triangle, then join the centres around each corner. Corners where six triangles met become hexagons. The twelve corners where only five met become pentagons. That is the whole operation, and it explains the twelve directly: they are the twelve corners the icosahedron started with, and no amount of subdividing ever creates or destroys one.

On-screen math:

- dual: face centres -> new corners
- degree-6 corner -> hexagon
- degree-5 corner -> pentagon

## 13. The hexagons are not regular any more

Time: 00:06:43.152 - 00:07:12.176

The first subdivision already splits one strut length into two.

Lay a Goldberg hexagon flat next to a football hexagon and the difference is immediate. Its sides are no longer all equal and its corners are no longer all a hundred and twenty degrees. It is still a perfectly good panel and it still tiles the cage, but it is a specific shape with a specific orientation, and now the strut list has two lines on it instead of one.

On-screen math:

- GP(2,0): 2 strut lengths
- hexagon sides no longer equal
- corners no longer all 120 deg

## 14. Every step up multiplies the shapes

Time: 00:07:12.176 - 00:07:47.608

Two lengths, then four, then six: the shop work grows faster than the dome.

Go to three frequency and the cage has two distinct hexagon shapes and four strut lengths. Go to four and it is three shapes and six lengths. The dome gets rounder and its panels get easier to lift, but every extra length is another jig, another label, and another chance to reach for the wrong stick. This is the real trade, and it is worth making deliberately rather than discovering it halfway through cutting.

On-screen math:

- GP(2,0): 2 lengths, 1 hex shape
- GP(3,0): 4 lengths, 2 hex shapes
- GP(4,0): 6 lengths, 3 hex shapes

## 15. And the panels stop being flat

Time: 00:07:47.608 - 00:08:23.880

Six corners on a sphere do not share a plane. The football's do; nobody else's.

Here is the part almost nobody mentions. Three points always define a plane, so a triangular panel is flat for free. Six points on a sphere generally do not, so a subdivided hexagon panel is warped: its corners want to sit slightly out of any flat sheet you cut. The amount is small, but it is not zero, and it is the reason hexagon domes are usually skinned with a membrane or with slightly domed panels rather than with rigid flat sheets.

On-screen math:

- 3 points define a plane -> triangles are free
- 6 points on a sphere generally do not
- warp = corner distance from best-fit plane

## 16. What the warp actually costs

Time: 00:08:23.880 - 00:08:53.336

Measured at a twenty foot dome, so you can decide with a number.

The football cage measures exactly zero: its panels are genuinely flat and always will be. Every subdivided cage measures more than zero. Put a flat sheet on a warped opening and you either gap it at two corners or you spring the sheet and let it take the twist. Both are workable if you plan for them. Neither is workable if you find out about it with the crane on site.

On-screen math:

- flat panel + warped opening = a gap to seal
- membrane, domed panel, or sprung sheet

## 17. Three panels, one hub, three seams

Time: 00:08:53.336 - 00:09:25.912

Every hub on a hexagon cage is a three-way seam pointed at the sky.

Because every corner is three-way, every hub is a junction of three panel edges, and on the upper half of the dome those seams point uphill. Water finds them. Shingle the skin from the rim upward so every lap sheds downhill, tape or flash each hub, and give yourself an eave that throws water clear of the wall rather than down it. A dome leaks at its seams long before it fails at its struts.

On-screen math:

- every corner is 3-way
- 3 panel edges meet at each hub
- lap from the rim upward

## 18. Choosing between them

Time: 00:09:25.912 - 00:09:56.712

Repeated work is cheap. Varied work is where the mistakes live.

If the dome is small enough that a two metre panel is liftable, take the football: one strut, two templates, flat panels, no warp. If you need a bigger or rounder shell, accept the subdivision, but then be rigorous about labelling, because a four-length dome punishes a mis-sorted stick far more than a one-length dome does. Colour code the ends. Do it at the saw, not at the scaffold.

On-screen math:

- small and simple -> GP(1,1)
- large and round -> subdivide, then label ruthlessly

## 19. The two domes, side by side

Time: 00:09:56.712 - 00:10:23.816

Same radius, same sphere, completely different day in the shop.

Here they are at the same radius. One is sixteen panels, fifty-five struts, and a single length. The other is a far rounder shell that needs six lengths and three hexagon templates. Neither is better. They are answers to different questions, and the only mistake is choosing one without knowing which question you asked.

On-screen math:

- same R, same sphere
- different panel count, different cut list

## 20. The whole transformation

Time: 00:10:23.816 - 00:10:53.272

A flat sheet, twelve pentagons, and a shell that closes on itself.

Start with a sheet of hexagons that will never curve. Remove sixty degrees at twelve places and it closes into a sphere. Cut that sphere where you want a wall, stand it on something level, and skin it from the rim up. Every number in this lesson came from that one idea, and every one of them can be recomputed from the geometry rather than trusted from a table.

On-screen math:

- flat sheet -> 12 pentagons -> closed shell
- one radius scales the whole cut list
