---
chapter: 17
title: Let the Connector Hold the Angle
strand: explain
status: drafting
target: 4750
updated: 2026-09-08
---

# 17. Let the Connector Hold the Angle

*Keep the wood, machine the small part*

<!-- Every number in this chapter must come from:
     - book_math.shaving_plan
     - book_math.panel_seam_count
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## Let the Connector Hold the Angle

There is a principle underneath this whole method, and it is worth stating on
its own because it is the thing that makes rough natural timber buildable to a
tolerance at all.

> The tree supplies the mass. The jig supplies the repeatability. The
> connector supplies the precision.

Three jobs. Three different things doing them. Nothing asked to do two.

## Precision is expensive per cubic inch

The instinct with an irregular material is to machine it until it is regular.
Plane the faces, square the ends, bring everything to a dimension, and then
build with confidence.

That instinct is why dimensional lumber exists, and inside a mill it is the
right instinct — a mill can afford to hold a tolerance because it is holding
it on thousands of pieces with a machine built for nothing else.

A person with a chainsaw cannot afford it, and the reason is not skill. It is
that **precision costs roughly in proportion to how much material you have to
be precise about**. A long, heavy, awkward member is expensive to hold, to
reference, to feed and to correct. A small block is cheap to hold and cheap to
remake if you get it wrong.

So there is a choice about *where to put the accuracy*, and the two answers
lead to very different afternoons:

![Where the precision lives.](../../deliverables/book/figures/precision-location.png)

One route asks for accuracy {{frame.members}} times, on the largest and most
awkward pieces in the build, with one chance at each. The other asks for it
{{seam.distinct_angles}} times, on the smallest pieces, and then repeats the
result {{frame.seams}} times.

Both end with a dome that closes.

This is not a way of avoiding accuracy. Nothing here is less accurate than the
alternative — the seams end up at the same angles either way. It is a question
of *where the accuracy is cheapest to buy*, and the answer is: in the small
part.

## The wedge starts close to useful

There is a piece of luck in this, and it is the reason the wedge suits a dome
rather than merely tolerating one.

A rectangular board arrives with two faces at ninety degrees to each other.
Ninety degrees appears nowhere in a geodesic dome. Every angular relationship
in the frame has to be created from nothing, by cutting.

A split sector does not arrive square. It arrives with two sawn faces that
each sit **{{seam.half_sector_deg}} degrees** off the member's own
centreline, because that is half of one {{tree.sector_angle_deg}}-degree
sector.

And the seams of this dome fold by {{seam.fold_a_deg}} and
{{seam.fold_b_deg}} degrees.

Those are not the same numbers. The wedge does not magically arrive at the
right angle — that would be too good, and this book does not do too good. But
it arrives *within a few degrees* of what the joint wants, rather than
sixty-odd degrees away.

The natural shape of the tree becomes part of the joint system instead of an
obstacle that first has to be removed. That is the difference between a
material that suits a structure and one that merely survives it.

## Two ways to close the difference

The gap between the face you have and the face the joint wants can be closed
from either side.

**Shape the key.** Leave both sawn faces exactly as split and cut a tapered
key that fills whatever is left. No wood is machined at all. The cost is that
the key is not the same shape at every seam, so there is more than one key
profile to make.

**Shape the wood.** Plane both faces parallel and drop in a plain rectangular
key that fits everywhere. One key profile for the whole dome. The cost is a
machining pass on every stick.

Chapter {{ch.seams}} covers what each does to the seam. This chapter is about
what the second one costs, because it sounds much worse than it is.

## What planing the faces actually costs

Here is the arithmetic, and it is the most reassuring table in the book.

The raw split face sits at {{seam.half_sector_deg}} degrees. A flat key wants
a face at half the seam's fold angle. The difference between those two is
everything that has to come off.

![What the shaved-flat option costs.](../../deliverables/book/figures/shaving-cost.png)

Over a two-inch mating land — you do not need the whole face to bear, only a
band of it — the deepest cut anywhere in the dome is
**{{seam.shave_deep_in}} inches**.

On a member {{member.depth_in}} inches deep, that is
{{seam.shave_pct_of_depth}} per cent of the section.

So even the "machine the wood" option does not convert a wedge into something
resembling dimensional lumber. It removes a narrow sliver from a narrow band
and leaves the overwhelming majority of the member exactly as the saw left it.
You are still not making boards. You are making one precise interface on an
otherwise raw stick.

That is worth knowing before you decide, because the shaved-flat route is
often written off as a betrayal of the whole idea. It is not. It is a
{{seam.shave_pct_of_depth}} per cent concession that buys you a single key
profile.

## Or do not machine anything at all

There is a third answer, and in some builds it is the best one: make the
connector out of something that does not need to fit exactly, because it
deforms.

A rubber or closed-cell spline, a length of hose, a compressed gasket — any of
these fills a *range* rather than a value. Feed it a seam anywhere between the
two fold angles and it takes up the difference by squashing.

What a compliant key can do, all at once:

* absorb the angular difference,
* absorb manufacturing variation in the members,
* seal the seam against weather,
* isolate one panel from another acoustically and against vibration,
* hold a preload so the joint stays tight as the wood moves.

What it cannot do is carry the load a timber key carries. A compliant seam is
a weather joint and a tolerance joint; it is not a structural one. So the
choice depends on a question you should answer before you buy anything: **is
this seam holding the building up, or holding the weather out?**

In a frame where each panel is a complete, self-braced triangle — which is
what Chapter {{ch.own_edge}} is about — a great deal of the shell's stiffness
lives inside the panels rather than across the seams, and that is what makes
the compliant option viable at all.

## Why this is a manufacturing idea, not a dodge

It is worth defending this properly, because "let the connector take up the
difference" can sound like an excuse for sloppy work.

It is the opposite. It is how repeatable production works everywhere.

A machine shop does not hold a tolerance on every surface of every part; it
holds it on the surfaces that locate and mate, and leaves the rest rough
because rough is cheaper and does no harm. An engine block is machined to a
few thousandths where the bearings sit and left as cast everywhere else.
Cabinetmakers scribe one edge to a wall and leave the other three alone.

The principle is always the same: **decide which surfaces do work, and spend
your accuracy there.**

In this dome, the surfaces that do work are the mating faces of the seam and
the ends where one member bears on another's side. Everything else — the bark,
the taper, the natural bend, the exact diameter — can vary, and the jig is
designed so that it can.

The tree is not being asked to be accurate. It is being asked to be strong,
which it already is.
