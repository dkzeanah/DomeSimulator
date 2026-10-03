---
chapter: 13
title: Stop Squaring. Start Splitting.
strand: story
status: draft
target: 900
updated: 2026-09-25
---

# 13. Stop Squaring. Start Splitting.

I was sitting on a log when this stopped being difficult.

Not thinking about it. Sitting on it, having spent the morning on
connectors.

The connector question does have an answer, and it is a flat V bracket: two
flaps meeting at the panel's angle, four holes in each flap, and each flap
run out to as much as half the member's length so the screws are spread
along the stick instead of clustered at its end. Chapter {{ch.pinwheel}} has
the detail. It works, it is cheap, and you can make forty of them on a bench
brake in an afternoon.

What it does not do is make the sticks alike. It joins dissimilar sticks by
absorbing the difference, which means the connector is now doing that work,
in every joint, forever.

![The same log, opened a different way.](plate-stop-squaring.png)

## The wrong question

<!-- concept: wedge/square -->

The question I had been asking was: *how do I join sticks that are all
different?*

Everybody's answer to that is the same. Mill them. Square them up, run them
through a planer, and now they are all the same because you made them the
same.

That answer costs a mill, a planer, a shed to keep the mill dry, the fuel to
run it, and — this is the part nobody mentions — about half the tree. A round
log does not contain a rectangle. Squaring one is the act of cutting a
rectangle out of a circle and calling the rest waste.

## The better question

<!-- concept: why/split -->

Sitting on the log, I noticed the log.

A round trunk is rotationally symmetric. Every radius is the same as every
other radius. That is not a thing you achieve; it is a thing the tree did
while you were not there.

So split it. Split it through the middle and you get two identical halves —
identical not because you were careful but because the log was round before
you touched it. Split those and you get four. Split those and you get
{{cut.splits}}.

Three passes. Eight sticks. Every one of them a {{cut.sector}}-degree sector
of the same circle, to whatever tolerance the tree was round to, which is a
tolerance nobody had to hold and nobody had to check.

![The whole woodpile, standing up.](plate-two-trees.png)

That was the afternoon. It is not a clever idea and it took me a year to have
it, because I was busy asking a question that had no answer.

![How much of the stem survives splitting, against sawing.](plate-recovery.png)

## What the mill is actually for

<!-- concept: why/square -->

![The corners of a round log are not bad wood. They are wood of the wrong shape.](plate-round-log-corners.png)

One thing to be careful about, because the recovery argument is easy to
overstate.

The corners a mill throws away are not bad wood. They are perfectly good wood
of the wrong *shape*. A sawmill exists to turn trees into a standard
rectangular product that can be stacked, graded, priced, shipped and sold by
people who will never see the tree. It is extremely good at that, and the
waste is the price of the standardisation, not of incompetence.

Splitting does not beat sawing at making lumber. It beats sawing at making
*this* — a structural member for a frame that does not care about rectangles.

That distinction matters because it tells you when the method stops working.
Build something with right angles in it and you want a mill. Build a
triangulated shell and you do not.

![The tree is the product.](plate-tree-is-the-product.png)

## How many rectangles fit in a circle?

<!-- concept: wedge/pack -->
<!-- concept: wedge/m_rectangles -->

Conventional milling squares the log first: four slabs come off the outside to
make a rectangular cant. Then the cant is sawn into boards, each board edged,
trimmed, dried and graded. Every step removes wood, and every one costs a
machine, a setup and a handling. What survives is beautifully standard. What is
on the floor is the curved outside of the tree -- which is also the densest
wood it grew.

How much survives is a packing problem: true two-by-fours, laid out in rows
inside each section's small end, where a row can only be as wide as its
narrowest edge. For the worked tree of the last chapter:

    {{work.rectangles}}

Note what the working does with its own brief. The brief it started from
estimated a kinder figure for the mill than honest packing gives, and both are
carried forward rather than the convenient one.

## The same two trees, both ways

<!-- concept: wedge/m_compare -->

Put the two conversions side by side, for the same two trees:

    {{work.compare}}

Somewhere between those two ratios more structural wood comes out of the same
two trees split than sawn -- and one fewer machine was needed to get it.

## What this does not claim

<!-- concept: wedge/honest -->

One honest paragraph, because the argument does not need overstating.

This is not the claim that any eighth of any tree equals a graded two-by-four.
It does not. Species, moisture, knots, checks, decay, grain running off the
axis, taper and the connections all still matter, and a building people live
in has to be designed and checked around the members actually being used. The
figures in this chapter are geometry and volume: what the tree contains and
what the frame needs. They are not a structural calculation, and they are not a
substitute for one. Chapter {{ch.member}} is where the structural numbers start.

## What comes off the log

At the reference build's {{cut.trunk}}-inch trunk, each sector is
{{cut.width}} inches across its bark face and {{cut.depth}} inches deep from
point to bark. The frame needs {{dome.members}} of them, which is
{{dome.timber_ft}} feet of stick.

Nothing in that sentence required a tape measure on the tree. It required a
chainsaw, a steady rip along the radius, and a willingness to let the log
decide the section.

The next chapter is what that section actually is, and which way round to put
it — which is the first decision in this build you cannot take back.

## The round tree is not defective lumber

<!-- concept: wedge/close -->
<!-- concept: why/close -->

So, plainly: a wedge from a small tree is not a stronger stick than a stud. It
is a cheaper stick, a faster one, one that leaves far more of the tree standing
as structure instead of shavings, and one you can make without owning a
factory. From a big enough tree it is also simply the stronger stick, and
Chapter {{ch.member}} gives the diameter where that flips.

What makes it enough, either way, is the building. A triangulated shell puts
its members mostly in compression along their length, doubles every interior
edge, and asks only that the ends can be made to meet. Efficiency is not always
a better machine for making a conventional material. Sometimes it is a
structure that no longer needs the conventional material at all.

The round tree is not defective lumber. The wedge is not an unfinished
two-by-four. It is the member, and the dome is the geometry that lets you use it.
