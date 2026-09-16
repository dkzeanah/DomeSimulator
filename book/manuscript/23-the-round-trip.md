---
chapter: 20
title: The Round Trip
strand: explain
status: drafting
target: 1750
updated: 2026-09-08
---

# 20. The Round Trip

*Proving the two methods are one calculation*

<!-- Every number in this chapter must come from:
     - book_math.round_trip
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## The Round Trip

Two chapters ago there were two methods. This chapter is here to show that
there is really only one, held at opposite ends, and to give you a ten-minute
check that catches almost every arithmetic mistake you can make with either.

The reason this matters is not elegance. It is trust.

A book can tell you that a {{tree.section_length_ft}}-foot stick gives a
{{dome.diameter_ft}}-foot dome and you have no way to know whether that came
out of a solver or out of somebody's memory of a similar dome. Rules of thumb
in building books are usually the latter, and they are usually close enough
to be dangerous. So rather than ask you to take it on faith, here is the
check, and here is the actual number it produces.

## Run it forwards, then backwards

Take any radius. Compute the longest member the frame would contain. Now
throw the radius away, and using *only* that member length, compute the
radius that a dome would need in order for that to be its longest member.

If the two methods are one calculation, you land exactly where you started.

* Start: a radius, any radius.
* Forwards (Method A): radius → longest member.
* Backwards (Method B): longest member → radius.
* Compare.

## The residual

Here is the check run on six domes, from small to large:

![Out and back.](../../deliverables/book/figures/round-trip.png)

The worst disagreement across all six is **{{roundtrip.residual_in}}
inches**.

For scale: the kerf of the chain on the saw this book was built with is
{{saw.kerf_in}} of an inch. The disagreement between the two methods is
smaller than the width of the cut by a factor with a lot of zeroes in it. It
is smaller than the seasonal movement of the wood. It is smaller than
anything you could measure with a tape, a story pole, or a laser.

It is, in other words, zero for every purpose a person with a chainsaw has.

That number is not asserted here. It is computed when this book is exported,
by running the check, and if it ever stops being negligible this sentence
will print a large number and the chapter will be wrong in an obvious way
rather than a quiet one.

## What would break it

The round trip closes because both directions are solving the same
relationship with the same assumptions. Change an assumption between the two
and it will not close — and this is exactly what makes it a useful check,
because those are the mistakes people actually make.

**Change the gasket thickness.** The seam key sits between panels and every
member length accounts for it. Design at {{jig.gasket_in}} inches, then
compute your bucking with a half-inch key in mind, and the two answers
diverge. The gap will be small and it will be in the wrong direction — your
sticks will be very slightly too long, forty times over, and the dome will
fight you at the top.

**Change the split count.** Eight sectors gives a member
{{member.width_in}} inches wide. Six gives a wider one, twelve a narrower
one, and the pinwheel setback moves with it. If you designed for eighths and
then split a few logs into sixths because they were fat, those members are
not interchangeable with the rest, and the round trip on the fat ones will
not close against the layout.

**Change the stock diameter.** Same problem, from the other side. Sizing the
layout off the butt diameter and cutting most of your sections from thinner
wood up the trunk means the members you actually get are narrower than the
ones you designed. Use the mid-trunk diameter, as Chapter {{ch.method_b}} step 5 insists.

**Mix up feet and inches.** Says itself. It happens. The round trip catches
it immediately, because the recovered radius comes back off by a factor of
twelve rather than by a thousandth of an inch.

## How to actually do the check

You do not need software.

1. Finish whichever method you used. Write down your radius and your longest
   member.
2. Take the *other* method's procedure from Chapter {{ch.method_a}} or {{ch.method_b}}.
3. Feed it the number you got out, and see if you get back the number you
   put in.

If you are within a quarter of an inch on the radius, you have not made a
mistake worth worrying about. If you are out by more than an inch, stop —
something in the middle changed and you should find out what before you cut a
hundred and twenty of anything.

## Why this chapter exists at all

Because the mistake this is designed to catch is not a mistake in the
arithmetic. It is a mistake in the *assumptions*, and those are invisible.

Arithmetic errors announce themselves: a number is obviously wrong, or the
units are absurd, or the answer is negative. Assumption drift does not.
Everything looks reasonable at every step. You get a cut list of plausible
lengths and you cut a hundred and twenty plausible sticks, and the first
thing that tells you is the frame, on day fourteen, when the last ring is a
half inch short all the way round and there is nothing to be done about it.

Ten minutes with the other method, before anything is cut, is the cheapest
insurance in this book.
