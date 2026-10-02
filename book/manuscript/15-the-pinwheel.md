---
chapter: 15
title: The Pinwheel
strand: explain
status: drafting
target: 3750
updated: 2026-09-17
---

# 15. The Pinwheel

*Three sticks, one triangle, and not one mitre*

> **This chapter corrects something.** The 'no mitres anywhere' claim, already corrected on camera in lesson_wedge_why.

## The Pinwheel

This is the joint that makes the whole method buildable by one person,
and it is worth stating in one sentence before the geometry spends it:

**No member end ever meets another member end. Every member's butt end
lands on the flat side of the next member, one cut per stick, and the
corner is empty.**

That sentence deletes, in order: the hub, the mitre at every end, the
compound-angle saw settings, and the requirement that rough split
timber behave like milled stock. What it costs — and it does cost — is
a slightly smaller panel than the triangle it sits in, and a cut list
four lengths long instead of two. Chapter {{ch.two_lengths_not_forty}}
already counted that bill. This chapter shows the joint that issues
it.

The name is descriptive. Look at a corner of the built panel: the three
members overlap like the blades of a pinwheel, each butt end lying on
its neighbour's side, chasing each other around the triangle, none of
them meeting at the vertex. The vertex — where a hubbed dome puts its
connector — is empty air. The frame does not need anything there,
because the triangle is closed by the three overlaps, and the overlaps
are held by screws through flat wood into flat wood.

## Why mitres were the enemy

The conventional way to join three struts at a corner is to make them
meet: each end cut to the right compound angle so the three ends kiss
at a point, then a hub or a plate holds the kiss together. It is the
geometry of every geodesic kit ever sold, and for machined aluminium
struts in a factory it is fine.

For this method it is fatal, for three reasons that compound.

**A mitre is two angles at once.** The end of a dome strut has to
match both the panel's fold and the member's position around the
corner — a mitre and a bevel together. Cut one slightly wrong and the
struts no longer meet; cut forty panels' worth slightly differently
wrong and the dome has a gap for every mood.

**Every stick needs two of them.** Both ends of every member would be
mitred — {{frame.members}} members, two ends each, each end its own
setting — against a stick that is rough, tapered, green and moving.
Precision joinery on wood that never agreed to be precise is not a
building method; it is a bet against the material.

**The corner has to be perfect or nothing is.** When three ends meet
at a point, all three must arrive exactly, or the hub cannot close. The
tolerance is concentrated in one place, which is the worst place for a
frame built from a log: every error in the whole build queues up at
the vertex and waits.

The pinwheel sidesteps all three by moving the joint. The ends do not
meet, so they do not have to match. Each end lands on a flat side, and
a butt end on a flat side needs only to be square to its own length —
one cut, made once, on a jig. The overlap is where the tolerance lives,
and an overlap is a joint that can be off by half an inch and still
hold, because the screws have a whole side of wood to find.

## Each end lands on a side, not a point

The pinwheel, in the way that finally makes it obvious, because the
obvious version is what you will teach somebody at the bench.

Take three sticks. Lay the first two in the triangle's shape, and
instead of cutting them to meet at the corner, let each one run *past*
the corner along the side of the other. Now the first stick's end rests
on the second stick's side, not its end. Lay the third stick the same
way: its end rests on the first's side, and the second's end rests on
the third's. Three ends, three sides, one closed triangle, and the
actual corner of the triangle — the point where the lines would meet —
has nothing in it at all.

That is the whole joint. Every member is cut square on its butt end and
left long on its head end, and the overlap is resolved at assembly.
The result reads as a pinwheel because each stick's butt chases the
next stick's side around the corner, and the chase closes the triangle
without any stick ever touching the vertex.

Why this survives rough timber: the bearing patch is a full side of a
stick — {{force.bearing_in2}} square inches of flat-to-flat contact,
as Chapter {{ch.forces}} measured — and the screws run through the
overlap at right angles to the grain, where wood holds best. Nothing
in the joint depends on an angle being cut accurately, because the
only cut angle in the whole assembly is the square butt, and the
square butt is the one cut a jig can make identical forty times.

![Three members, three end-to-side joints, no mitre anywhere.](../../deliverables/book/figures/pinwheel-exploded.png)

## One panel, taken apart

The drawing explodes one panel and labels the three overlaps, so the
sentence above has a picture to check against.

**The butt end.** Square to the stick's length, the one machined cut
on the member. It is made on the jig, once, with the stick located on
its sawn faces — Chapter {{ch.butt_cut}} is that cut in full.

**The bearing side.** The neighbour's sawn face, where the butt lands.
Flat, because the saw made it flat, and wide, because the whole sector
is wide.

**The head end.** Deliberately long. It runs past its own bearing by
the overfit allowance — {{jig.head_overfit_in}} inches in this build —
and gets sawn off in place against the jig's fence, which is how the
panel ends up true without anybody measuring a stick to a tape. Chapter
{{ch.head_overfit}} is that trick, and it is the quiet reason the
method forgives.

**The empty corner.** The vertex itself, untouched. In a hubbed dome
this is where the money is — the machined connector, the bolt, the
precision. Here it is air, and the air is doing its job by not being
asked to do anything.

Read the exploded drawing once and the build order falls out of it:
butt cuts first, on the jig; panels assembled flat, overlaps screwed;
heads flushed; panel lifted. Nothing met anything. Nothing had to.

## What the inset costs

The honest price of the pinwheel, because the joint's elegance is real
and its bill is real, and the book prints both.

The triangle's *edge* — the geometric line from vertex to vertex — is
longer than the member that fills it, because the member stops short of
the corner to land on its neighbour's side. The difference is the
inset: the distance each stick pulls back from the vertex so its butt
lands on the next stick's side instead of on the next stick's point.
Every member length in the cut list is the edge length minus its share
of the inset, which is why the cut list has four lengths where the
geometry has two — the inset differs between the long and short edges,
and between the two sides of each.

The inset also shrinks the panel. The frame's triangles, drawn vertex
to vertex, are bigger than the wood that fills them; the panel is the
triangle minus three strips around its edge. That strip is not waste —
it is the bearing, the overlap, the screw row — but it is real, and it
is why the member schedule in Chapter {{ch.worked_build}} is the
number it is rather than the bare chord factors.

And the inset scales with the *stick*, not the dome. A wider member
pulls back further; a bigger dome changes nothing. That single fact is
why the method survives scaling — Chapter {{ch.flat_rate}} makes it
the spine of Part Two — and it is paid here, in the cut list, once.

## The mitre claim, corrected

The errata, named in full, because this project said it in public and
the correction belongs in public too.

An earlier film in this project claimed that no cut in the dome is a
mitre. That was wrong, and it was corrected on camera before this book
existed — the film's own correction chapter is the model this page
follows.

The true statement is narrower and better. No member end is ever
mitred *to another member end*, because the pinwheel never lets two
ends meet. But the butt end itself is not a plain square crosscut: it
carries the bevel that matches the neighbour's side and the angle that
matches the panel's fold — a compound cut, made once, on one end, off
the jig, with the same setting for every stick of a class. The whole
dome reduces to a handful of saw settings — the bevel is the same
everywhere, and the mitre takes a few fixed values — and that is the
claim worth making: not "no mitres", but "no mitre is ever measured,
and no two ends ever meet".

Chapter {{ch.corrections}} keeps the full list of everything this
project has published and had to take back. This page is one entry in
it: the claim, the error, the corrected version, and the arithmetic
that decides which is which — the same treatment the book gives every
number it has ever got wrong.
