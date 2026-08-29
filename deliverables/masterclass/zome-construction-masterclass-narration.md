# Zome Construction Masterclass - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. A zome is not a piece of a sphere

Time: 00:00:00.000 - 00:00:27.128

It is a shape you sweep, and that changes everything about building it.

A geodesic dome starts with a sphere and chops it into triangles. A zome starts somewhere else entirely: you pick a handful of directions and sweep the shape out along them, one after another. What you get is a room built entirely from parallelograms, with a true point at the top, and it can be framed from a single length of stick.

On-screen math:

- zome = zonohedron = a swept solid
- every face a parallelogram
- one strut length, one point on top

## 02. The sweep, in four steps

Time: 00:00:27.128 - 00:00:59.656

A point becomes a stick, a stick becomes a panel, a panel becomes a room.

Take a point and drag it along the first direction: you have drawn a stick. Drag that stick along the second direction and it sweeps out a panel. Drag the panel along a third and you have a solid. Keep going for as many directions as you chose, and the surface of the result is your building. Every step of that is something you can do with your hands, and it is the only construction rule in this lesson.

On-screen math:

- sweep along g1, then g2, then g3, ...
- the result is called a zonohedron

## 03. Every panel is flat, guaranteed

Time: 00:00:59.656 - 00:01:31.248

Two directions define a plane, so the panel they sweep cannot be warped.

This is the zome's quiet advantage over a hexagon dome. Each panel comes from exactly two directions, and two directions define a plane, so all four corners of that panel lie in one flat sheet. Not approximately. Exactly, and at every size. You can cut a zome's panels from rigid sheet goods and they will lie down without springing, complaining, or leaving a gap at one corner.

On-screen math:

- two directions -> one plane
- opposite sides equal and parallel
- planar by construction, at any size

## 04. Make the directions equal and you get one strut

Time: 00:01:31.248 - 00:02:04.952

A parallelogram with equal sides is a rhombus, and a rhombus needs one length.

Nothing so far forced the directions to be the same length. If they differ, the panels are general parallelograms and your cut list has several lines on it. Make every direction the same length and every side of every panel is that length, so the entire frame comes off one saw setting. This is a decision you make once, at the very start, and it pays for itself all the way through the build.

On-screen math:

- equal directions -> rhombic faces
- every strut the same length

## 05. The star of directions

Time: 00:02:04.952 - 00:02:34.528

Space them evenly around a cone and the whole building falls out of two numbers.

For the classic pointed zome, arrange the directions evenly around a vertical axis, all leaning in at the same angle. That angle is the pitch, and it is your only shape control. How many directions you use sets how many sides the building has. Two numbers, a count and an angle, and everything else in this lesson is derived from them.

On-screen math:

- n directions, evenly spaced
- pitch = lean from the axis
- two numbers set the whole building

## 06. Counting the parts before you buy anything

Time: 00:02:34.528 - 00:03:05.448

Panels, struts and hubs are all simple formulas in the number of directions.

Each pair of directions makes exactly two panels, one on each side of the building, so the panel count is n times n minus one. Each panel has four edges and every edge is shared, so the strut count is twice that. Add the two points and you have the hub count. Check it against Euler's formula and it comes out to two every time, which is how you know you have not miscounted.

On-screen math:

- panels = n(n-1)
- struts = 2n(n-1)
- hubs = n(n-1)+2
- V - E + F = 2

## 07. The top comes to a point

Time: 00:03:05.448 - 00:03:37.832

One vertex is reached by travelling along every direction, so the roof closes there.

Walk along all of the directions in turn and you arrive at one particular corner: the far end of the whole sweep. Only one corner can be reached that way, so the roof closes on a single point, with one panel arriving from each direction. Add up the panel corners that meet there and they come to less than a full turn. That shortfall is exactly why it closes into a peak instead of lying flat.

On-screen math:

- apex = sum of every direction
- n panels meet there
- corner angles < 360 deg -> a peak

## 08. The hubs land on level rings

Time: 00:03:37.832 - 00:04:12.352

Every corner at a given height is at exactly that height. No tape needed.

Here is the property that makes a zome pleasant to build. A corner's height is just the number of directions you travelled to reach it, times the rise of one direction. Every corner reached in the same number of steps is therefore at exactly the same height, so the hubs sit on perfectly level rings, evenly spaced. A hexagon dome has nothing like this, and it is why a zome wall meets a floor and a lintel so easily.

On-screen math:

- corner height = steps x rise per direction
- n+1 level rings, evenly spaced
- no ring is approximate

## 09. How many panel templates

Time: 00:04:12.352 - 00:04:46.392

Directions one apart, two apart, and so on -- and the far pairs repeat.

A panel's shape depends only on how far apart its two directions sit around the star. Neighbouring directions give a long thin rhombus; opposite ones give a fat near-square. Because a pair separated by three steps one way is separated the other way by the same amount, the shapes pair up, and a zome with n directions needs only about half that many templates. Cut one jig per shape and trace the rest.

On-screen math:

- shape depends only on separation
- separation s and n-s are the same shape
- templates = round up of (n-1)/2

## 10. Pitch is the free design knob

Time: 00:04:46.392 - 00:05:18.824

Tall spire or low saucer, same struts, same count, same cut list.

Lean the directions in steeply and the zome climbs into a spire. Open them out and it settles into a wide saucer. Nothing about the strut length or the part count changes; only the panel angles do. That means you can shape the building to the site, the snow load, or the headroom you want without adding a single line to the cut list. Very few structural systems give you a free knob like this.

On-screen math:

- pitch changes shape, not part count
- still one strut length at every pitch

## 11. The joints are where a zome gets particular

Time: 00:05:18.824 - 00:05:50.896

One strut length, but several different hubs, and they are not interchangeable.

The saving on struts is real, but it is paid back at the joints. The corners come in a handful of types: some take three struts, some four, and the two points take one from every direction. Each type has its own splay angles, so a hub that works at mid-height will not sit right near the top. Make a full set of angle jigs before you fabricate any of them, and stamp each hub with its type as it comes off the bench.

On-screen math:

- hub types vary; strut length does not
- each type has its own splay angles
- stamp the type on the hub at the bench

## 12. Meeting the floor

Time: 00:05:50.896 - 00:06:24.816

A zonohedron has no horizontal strut, but its floor line is one repeated cut.

Not one strut in a zome runs level, so a level floor line always crosses struts in mid span. On a polar zome that turns out not to matter: because every hub in a ring is at the same height, the level line meets every strut it crosses at exactly the same place along its length. One angle, one length, repeated all the way round. Mark one, check it, then use it as the master.

On-screen math:

- no horizontal struts anywhere
- level line crosses every strut identically
- one cut setting for the whole bottom row

## 13. The whole cut list

Time: 00:06:24.816 - 00:06:57.464

One stick length, a handful of panel templates, and a hub schedule.

This is what the shop actually receives. A single strut length, cut as many times as there are struts in the roof, less the connector allowance you measured on a real joint. A template for each panel shape. And a hub schedule listing how many of each type. Everything on this list came from the two numbers you chose in chapter five, so if you change your mind about pitch, the list regenerates rather than needing to be re-derived.

On-screen math:

- cut length = centre length - deduction
- one length x every strut in the roof

## 14. The famous one-panel zome

Time: 00:06:57.464 - 00:07:32.896

Thirty identical golden rhombi, and their diagonals land exactly on phi.

There is one zome where every single panel is the same shape: build the star from the six five-fold axes of an icosahedron and you get the rhombic triacontahedron. Thirty faces, all identical, all rhombi, and the ratio of each panel's diagonals is the golden ratio, exactly. One strut length and one template for the entire surface. It is the most economical shell in this whole series of lessons.

On-screen math:

- 6 icosahedral axes -> 30 identical faces
- diagonal ratio = phi
- one strut, one template

## 15. What the golden zome charges you

Time: 00:07:32.896 - 00:08:03.096

Its hub rings are not evenly spaced, so the floor line stops being simple.

The catch shows up the moment you try to stand it on something. Its rings of hubs are not evenly spaced, so a level line through the middle of the building meets struts at two different points along their length, and the bottom row needs two cut settings instead of one. That is a real cost, and it is the exact mirror image of the polar zome's trade: one pays at the panel bench, the other at the floor.

On-screen math:

- golden zome: uneven ring spacing
- level cut needs two settings
- polar zome pays at the panels instead

## 16. Raising it, tier by tier

Time: 00:08:03.096 - 00:08:35.864

The geometry hands you the build sequence: one complete ring at a time.

Set out the bottom ring on a level base and bolt it down. Then add complete tiers, never a single column of panels up one side, because a zome is a shell and it is not stable until each ring closes. Prop the tier you are working on until the ring above it goes in. Check the diameter of each completed ring in three directions before starting the next, and leave the apex panels for last.

On-screen math:

- complete rings, never one column
- prop each tier until the ring closes
- apex panels last

## 17. Doors and windows

Time: 00:08:35.864 - 00:09:04.144

Take out a whole panel and no strut needs cutting.

Because the frame is a net of complete rhombi, the natural opening is one whole panel. Leave the panel out, frame the rhombus, and hang a door or a fixed light in it: the structure is untouched. If you need something square, build a small dormer forward out of the rhombus rather than cutting struts out of the shell, and keep the shell's own net intact behind it.

On-screen math:

- one panel out = one opening
- the frame is never cut
- square openings dormer forward

## 18. Zome against geodesic dome

Time: 00:09:04.144 - 00:09:39.312

Both close. They close for completely different reasons.

A geodesic dome closes because triangles hold their shape and its corners are missing a little angle each. A zome closes because a swept solid has to come back on itself. The dome gives you a shallower shell and famously stiff triangulation; the zome gives you fewer strut lengths, guaranteed flat panels, level hub rings, and vertical-ish walls that furniture can actually stand against. Pick by what your building has to do, not by which is rounder.

On-screen math:

- dome: triangles, 2 lengths, stiff shell
- zome: rhombi, 1 length, usable walls

## 19. The whole transformation

Time: 00:09:39.312 - 00:10:12.920

A star of directions, swept out, and closed on a point.

Pick a count and a pitch. Sweep the shape along that star of directions. Every panel arrives flat, every strut arrives the same length, the hubs land on level rings, and the roof closes on a single point. Cut the building off at whichever ring gives you the room you want, and the bottom row is one repeated cut. That is the entire method, and every number in this lesson was recomputed from it rather than read off a table.

On-screen math:

- count + pitch -> the whole building
- swept, flat, level, and closed
