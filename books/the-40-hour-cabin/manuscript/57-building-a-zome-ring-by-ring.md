---
chapter: 57
title: Building a Zome, Ring by Ring
strand: howto
status: draft
target: 1960
updated: 2026-10-05
---

# 57. Building a Zome, Ring by Ring

Chapter {{ch.zome}} said what a zome is: a shape swept along a star of
directions, every panel flat, every strut the same length. This chapter is
what a builder does with that. Everything in it falls out of two numbers you
choose at the start -- **how many directions, and how far they lean** -- and
the worked example is the zome film's own: {{zx.n}} directions at
{{zx.pitch}} degrees, framed in {{zx.strut_in}}-inch struts.

## Counting the parts before you buy anything

<!-- concept: zome/counts -->

Each pair of directions makes exactly two panels, one on each side of the
whole closed shape. So with *n* directions the panel count is *n* times
*n* − 1. Each panel has four edges and every edge is shared, so there are
twice as many struts. Add the two points and you have the hubs:

    panels   n(n - 1)       {{zx.panels}}
    struts   2n(n - 1)      {{zx.struts}}
    hubs     n(n - 1) + 2   {{zx.hubs}}
    V - E + F               {{zx.euler}}

That last line is the check. Euler's formula says a closed cage comes out to
two, every time; if your count does not, you have miscounted, and the time to
find that out is before the timber is ordered. A dome is the top of the closed
shape: here, {{zx.dome_panels}} panels on {{zx.dome_struts}} struts.

![Counting the parts before you buy anything.](plate-zome-counts.png)

## The top comes to a point

<!-- concept: zome/apex -->

Walk along every direction in turn and you arrive at one particular corner:
the far end of the whole sweep. Only one corner can be reached that way, so
the roof closes on a single point, with a panel arriving from each direction.
Add up the panel corners that meet there -- {{zx.apex_sum}} degrees here --
and they fall {{zx.apex_missing}} degrees short of a full turn. That shortfall
is why it closes into a peak instead of lying flat: the same missing-angle
bill Chapter {{ch.hex}} found the pentagons paying.

## The hubs land on level rings

<!-- concept: zome/rings -->

This is the property that makes a zome pleasant to build. A corner's height is
just the number of directions you travelled to reach it, times the rise of
one direction. Every corner reached in the same number of steps is at
**exactly** the same height -- so the hubs sit on perfectly level rings,
{{zx.rings}} of them, evenly spaced. No ring is approximate and no tape is
needed to find it.

A hexagon dome has nothing like this, and it is why a zome wall meets a floor
and a lintel so easily.

![The hubs land on level rings.](plate-zome-rings.png)

## How many templates, and what pitch buys

<!-- concept: zome/shapes -->
<!-- concept: zome/pitch -->

A panel's shape depends only on how far apart its two directions sit round
the star. Neighbours give a long, thin rhombus; opposite directions give a fat
near-square. A pair separated by three steps one way is separated by the same
the other way, so the shapes pair up, and a zome with *n* directions needs
only about half that many templates. Here: **{{zx.templates}}**. Cut one jig
per shape and trace the rest.

Then the free knob. Lean the directions in steeply and the zome climbs into a
spire; open them out and it settles into a saucer. On the same
{{zx.strut_in}}-inch struts, the film's {{zx.pitch}} degrees stands
{{zx.height_ft}} feet above its rim; at {{zx.tall_pitch}} degrees,
{{zx.tall_ft}}; at {{zx.wide_pitch}}, {{zx.wide_ft}}. **Nothing about the strut length or the part count changes** --
only the panel angles do. You can shape the building to the site, the snow
load or the headroom you want without adding a line to the cut list. Very few
structural systems give you a knob like that for free.

![Pitch is the free design knob.](plate-zome-pitch.png)

## The hubs

<!-- concept: zome/hubs -->

The saving on struts is paid back at the joints -- in a zome framed from
single sticks. The corners come in {{zx.hub_types}} kinds: some take three
struts, some four, and the two points take one from every direction. Each kind
has its own splay angles, so a hub that works at mid-height will not sit
right near the top. If you build that way, make a full set of angle jigs
before you fabricate any hub, and stamp each one with its type as it comes
off the bench.

Or frame each panel on its own and the hubs disappear, which is what Chapter
{{ch.zome_flat}} does.

## Meeting the floor

<!-- concept: zome/floor -->

Not one strut in a zome runs level, so a level floor line always crosses
struts in mid-span. On a polar zome that turns out not to matter. Because
every hub in a ring is at the same height, the level line meets every strut it
crosses at exactly the same place along its length: **{{zx.cuts}} cut
setting**, repeated all the way round. Mark one, check it, and use it as the
master for the rest.

(The golden zome of Chapter {{ch.zome}} needs {{zx.gold_cuts}}. That is its
bill.)

![Meeting the floor: one repeated cut.](plate-zome-floor.png)

## The cut list and the raise

<!-- concept: zome/cutlist -->
<!-- concept: zome/raise -->
<!-- concept: zome/close -->

What the shop receives:

1. **One strut length**, {{zx.strut_in}} inches centre to centre, cut as many
   times as there are struts in the roof -- less the connector allowance
   measured on a real joint, never from a catalogue.
2. **A template for each panel shape** -- {{zx.templates}} of them.
3. **A hub schedule**, if you are building on hubs: how many of each kind.

Everything on that list came from the two numbers chosen at the start. Change
your mind about the pitch and the list regenerates; it does not have to be
re-derived.

Then the raise, which the geometry hands you:

1. Set out the bottom ring on a level base and bolt it down.
2. Add **complete tiers**, never a single column of panels up one side. A
   zome is a shell, and it is not stable until each ring closes.
3. Prop the tier you are working on until the ring above it goes in.
4. Measure each completed ring's diameter in three directions before starting
   the next.
5. Leave the apex panels for last.

That is the whole method: a count and a pitch, swept out; every panel flat,
every strut the same, the hubs on level rings, the roof closed on a point, and
the bottom row one repeated cut.
