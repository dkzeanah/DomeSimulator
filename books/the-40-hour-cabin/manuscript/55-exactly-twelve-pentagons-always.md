---
chapter: 55
title: Exactly Twelve Pentagons, Always
strand: explain
status: draft
target: 2400
updated: 2026-10-05
---

# 55. Exactly Twelve Pentagons, Always

<!-- concept: hex/honeycomb -->

Everybody reaches for hexagons. Bees use them, basalt cools into them, a soap
froth settles into them, and for one reason: a hexagon walls off more floor
per foot of wall than a square or a triangle does, while still leaving no
gap. So people keep asking for a dome made of hexagons, and this chapter
answers that honestly -- what you can have, what you cannot, and exactly what
the difference costs in the shop.

There is a catch, and it is absolute.

![Exactly twelve pentagons. Always.](plate-hex-twelve.png)

## A sheet of hexagons will not curve

<!-- concept: hex/flat_forever -->
<!-- concept: hex/buy_curve -->

Stand at any corner of a hexagon tiling and **three** panels meet there. Each
brings 120 degrees, and three of them is {{hx.hex_sum}}: a full turn, flat,
with nothing left over.

That is what makes hexagons perfect for a flat surface, and it is exactly what
stops them curving. Take a paper disc, cut one wedge out of it, and pull the
two cut edges together: the paper cannot lie flat any more, and it lifts into
a cone. Nothing was stretched. The only thing that changed is that there is
less than a full turn of paper round the centre. **That missing angle is the
whole mechanism of curvature**, and it is the only currency a dome has to
spend.

A regular hexagon corner has none to give. A sheet of them stays a sheet
however many you add.

## Where the angle comes from

<!-- concept: hex/pentagon -->

A pentagon. A regular pentagon's corner is 108 degrees, so where three of
them meet there are {{hx.pent_spare}} degrees missing from the full turn.
Fold that slack out and the surface pulls into a bowl. Every hexagon dome you
have ever seen is doing this: **hexagons carry the field, and pentagons do all
of the curving.**

And how many pentagons is not a design choice. Any closed convex cage is
missing exactly 720 degrees in total, whatever its size -- Descartes proved
it -- and Euler's formula gives the same answer another way, with the
hexagons cancelling out of the arithmetic entirely. A closed cage of hexagons
and pentagons, three faces at every corner, needs **exactly twelve
pentagons**. Twenty hexagons or two thousand, still twelve.

A football has twelve. A fullerene has twelve. A hexagonal dome has twelve, or
it is not closed.

## The football dome

<!-- concept: hex/one_strut -->
<!-- concept: hex/two_templates -->

The cage you want if one shape is the goal is the pattern on a football, the
truncated icosahedron: {{hx.ti_hexagons}} identical regular hexagons and
twelve identical regular pentagons, {{hx.ti_panels}} panels on
{{hx.ti_hubs}} hubs. Every one of its {{hx.ti_struts}} struts is the same
length. No other hexagon cage on a sphere is this kind to a builder.

So the cut list is one line. At a dome {{hx.diameter_ft}} feet across, the
strut is {{hx.ti_strut_in}} inches hub centre to hub centre. Set a stop block,
cut every piece, and check a sample against a master gauge rather than a
tape. The geometry's number is centre to centre: subtract the connector
allowance for your hub before you cut, and measure that allowance on a real
assembled joint, never from a catalogue.

Both panel shapes are genuinely flat -- their corners lie in a plane -- so one
full-size hexagon template and one pentagon template, made from a scrap
sheet, trace the whole skin. Cut slightly oversize, fit to the raised frame,
then trim. The frame is always a little less perfect than the arithmetic, and
the panel is where you absorb it.

![The football dome.](plate-hex.png)

## Where do you cut it off?

<!-- concept: hex/the_cut -->
<!-- concept: hex/raise_it -->

A triangulated dome can be cut along a flat ring of hubs. A hexagon cage
cannot: no ring of its struts runs level, so wherever you stop, the bottom
edge rises and falls. On the {{hx.diameter_ft}}-foot football dome that
zigzag is **{{hx.ti_rim_in}} inches deep** -- {{hx.ti_rim_ft}} feet.

Two honest options. Build a level stem wall and let the zigzag sit on top of
it, or cut the bottom row of panels along a chalked level line and flash the
cut. Either way, decide before the first strut is cut.

![The rim comes out as a zigzag.](plate-hex-cut.png)

Then raise it rim to crown. Bolt the first course of hubs to the stem wall and
work upward **one complete ring at a time, never up one side**, so error
spreads evenly instead of piling up in one place. Measure each finished ring's
diameter in three directions before starting the next. Leave the crown panel
until last: it is where every accumulated millimetre shows up, and it is far
easier to trim one panel than to unbolt a ring.

## Then you want it bigger

<!-- concept: hex/bigger -->
<!-- concept: hex/dual -->
<!-- concept: hex/not_regular -->

The football is one fixed pattern. You can scale it, but you cannot make it
finer, and past a certain size its panels get too big to lift and too flat to
look round. For a finer cage, take a geodesic sphere of the kind Part 2
built, mark the centre of every triangle, and join the centres around each
corner. That operation is the **dual**. Corners where six triangles met become
hexagons; the twelve corners where only five met become the pentagons -- the
same twelve the icosahedron started with, which no amount of subdividing ever
creates or destroys. The family is called the Goldberg cages.

![Every triangle corner becomes one panel.](plate-hex-dual.png)

The price shows up at once. Lay a Goldberg hexagon beside a football hexagon:
its sides are no longer all equal and its corners are no longer all 120
degrees. It is still a good panel, but it is a specific shape with a specific
orientation, and the strut list now has two lines on it instead of one.

## Every step up multiplies the shapes

<!-- concept: hex/ladder -->
<!-- concept: hex/warp_cost -->

Measured at the same {{hx.diameter_ft}}-foot dome:

    {{hx.ladder}}

{{hx.gp2_lengths}} strut lengths, then {{hx.gp3_lengths}}, then
{{hx.gp4_lengths}}; {{hx.gp2_shapes}} hexagon shape, then {{hx.gp3_shapes}},
then {{hx.gp4_shapes}}. The dome gets rounder and its panels easier to lift,
but every extra length is another jig, another label and another chance to
reach for the wrong stick.

And the panels stop being flat. Three points always define a plane, so a
triangle is flat for free. Six points on a sphere generally do not, so a
subdivided hexagon panel is **warped**: its corners want to sit slightly out
of any flat sheet you cut. The football measures exactly zero, and always
will. The first Goldberg cage is the worst, at {{hx.gp2_warp_in}} of an inch
at the worst corner; finer cages warp less, down to {{hx.gp4_warp_in}} at
four-frequency, because smaller panels sit closer to their own plane.

![The panels stop being flat.](plate-hex-warp.png)

:::box against
**A flat sheet on a warped opening gaps at two corners, or springs.** You can
seal the gap, let a sheet take the twist and hold it with every fastener, fold
the panel into the two triangles it is trying to be, or skin the dome with a
membrane. All of them work if they are planned. None of them works if you
find out with the panels on site. The triangulated dome does not have this
bill at all.
:::

## Three panels, one hub, three seams

<!-- concept: hex/seams -->

Every corner of a hexagon cage is three-way, so every hub is a junction of
three panel edges -- and on the upper half of the dome those seams point at
the sky. Water finds them. Shingle the skin from the rim upward so every lap
sheds downhill, tape or flash each hub, and give it an eave that throws water
clear of the wall rather than down it. Chapter {{ch.one_layer}} said it about
the wedge dome and it is truer here: **a dome leaks at its seams long before
it fails at its struts.**

![Three seams meet at every hub.](plate-hex-seams.png)

## Choosing between them

<!-- concept: hex/choose -->
<!-- concept: hex/close -->

![The two domes, side by side.](plate-hex-compare.png)

At the same radius, the football dome's half is {{hx.ti_dome_panels}}
panels and {{hx.ti_dome_struts}} struts of a single length. The four-frequency
cage is a far rounder shell that needs {{hx.gp4_lengths}} lengths and
{{hx.gp4_shapes}} hexagon templates.

If the dome is small enough that a two-metre panel is liftable, take the
football: one strut, two templates, flat panels, no warp. If you need a bigger
or rounder shell, accept the subdivision -- and then be ruthless about
labelling, because a six-length dome punishes a mis-sorted stick far more than
a one-length dome does. Colour-code the ends, and do it at the saw, not at the
scaffold. Repeated work is cheap. Varied work is where the mistakes live.

And the thing to carry away: curvature costs angle, and something has to pay.
In a hex dome, twelve pentagons pay it. In a geodesic dome, the subdivision
pays it -- which is precisely why the wedge dome has two chord lengths
instead of one. There is no tiling that curves for free; every round building
in this book is a different answer to the same bill.
