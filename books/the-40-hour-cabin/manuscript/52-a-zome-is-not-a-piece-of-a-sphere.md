---
chapter: 52
title: A Zome Is Not a Piece of a Sphere
strand: explain
status: draft
target: 1740
updated: 2026-09-25
---

# 52. A Zome Is Not a Piece of a Sphere

Everything so far has been subdivision: take a solid, cut its faces smaller,
push the new points onto a sphere. A zome is made the other way and the
difference decides everything about it.

![A zome is not a piece of a sphere.](plate-zome-what.png)

## The sweep

<!-- concept: zome/star -->

Start with a **star of directions** — a set of vectors radiating from a point,
evenly spread around a vertical axis.

Now take a stick. Point it along the first direction and walk to the end.
Point it along the second and walk to the end of that. Keep going through all
the directions and you come back to where you started, having traced the
outline of a solid.

Every face of that solid is a **parallelogram**, because every face is made by
two of the directions and nothing else. Two directions define a plane. A
parallelogram made of two directions is flat, necessarily, always, without
anybody checking.

That is a zome.

## Every panel flat, guaranteed

<!-- concept: zome/flat -->
<!-- concept: zome/rhombus -->

This is the property worth the whole chapter.

In a geodesic dome, a panel is flat because a triangle is always flat. Fine —
but it means every panel must *be* a triangle, and triangles tile a sphere
with a lot of members.

In a zome, panels are four-sided and still guaranteed flat, because of how
they were constructed rather than because of how many sides they have. You
get big flat quadrilateral panels, which is a genuinely better thing to sheathe
and to glaze than a triangle is.

And the star means **one strut length**. Make the directions equal in length
and every stick in the building is the same stick. Not two lengths.
{{cut.mitres}} is not the number of anything. One.

## What it costs

Three things, and they are real.

**The hubs get particular -- in a frame of single sticks.** In a geodesic dome,
the hub problem is what the pinwheel of Chapter {{ch.pinwheel}} exists to
remove. Build a zome as a frame of single sticks and the problem comes back:
the sticks arrive at a hub in a pattern set by the star, at angles that are not
all the same, and the joint has to hold that pattern. An earlier draft of this
chapter stopped there and said zome hubs are where zome builders spend their
time. That was wrong for the way most zomes are actually built: frame each
panel on its own and the hub disappears, exactly as it does in the wedge dome.
Chapter {{ch.zome_flat}} shows how.

**The top comes to a point.** The sweep converges on the axis, so a zome
finishes in a spike rather than a cap. That is either a feature or a
detailing problem depending on your rainfall.

**The shape is not a sphere.** It is taller for its footprint, it has more
surface per square foot of floor, and if you wanted a hemisphere you did not
want a zome.

## The famous one-panel zome

![The famous one-panel zome.](plate-zome-golden.png)

Here is where the golden ratio comes back, and this time it really is the
design.

Choose the star's directions using φ and the pitch to match, and every single
panel in the zome becomes the **same rhombus**. Not two panel shapes, not
five. One.

One strut length and one panel template, for a whole building. You can cut
the entire skin from one jig and the entire frame from one saw setting.

That is the golden zome, and it is the single most elegant result in any of
the geometries this project solves.

## What the golden zome charges you

<!-- concept: zome/golden_cost -->

Two things.

**It charges at the floor.** The ordinary polar zome of Chapter
{{ch.zome_build}} has its hubs on evenly spaced level rings, so a level floor
line meets every strut it crosses at the same point along its length -- one
cut setting, repeated all the way round. The golden zome's {{zx.gold_faces}}
faces come from the icosahedron's axes, not from a star round a vertical one,
and its rings of hubs are *not* evenly spaced. A level line through it meets
struts at {{zx.gold_cuts}} different points, so the bottom row needs
{{zx.gold_cuts}} cut settings instead of one. It is the exact mirror image of
the polar zome's trade: one pays at the panel bench, the other at the floor.

**And it charges you the freedom to choose your proportions.** Every panel
comes out identical -- diagonals in the ratio {{zx.gold_ratio}}, which is φ --
because the star is pinned by φ. Change the height-to-width ratio you want and
the property is gone; you are back to several panel shapes.

So the golden zome is beautiful and it is exactly one building. If its
proportions suit your site, it is very hard to beat. If they do not, you are
designing around a constraint rather than a feature, and it is worth finding
that out before the jig is built.

![A zome, drawn by the tool that solves it.](plate-zome.png)

## Zome against geodesic dome

![Zome against geodesic dome.](plate-zome-versus.png)

    strut lengths       zome 1                geodesic 2
    panel shape         parallelogram         triangle
    panel flatness      by construction       by being a triangle
    hubs                particular            removed by the pinwheel
    top                 a point               a cap
    surface per floor   more                  less

Neither wins. They are answers to different questions, and the question a
zome answers well is *"I want big flat panels and one stick length and I do
not mind a hub."*

This book builds a geodesic dome because its question was *"I want to use a
split log and avoid a hub entirely"*, and the wedge's flat sawn faces make the
pinwheel possible in a way they would not in a zome's hub.

But if you have a bandsaw and a box of brackets and no chainsaw, the zome may
be your building, and this chapter exists so you can find that out here rather
than after the tree is down.
