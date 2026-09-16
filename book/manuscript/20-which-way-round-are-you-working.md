---
chapter: 17
title: Which Way Round Are You Working?
strand: howto
status: drafting
target: 2100
updated: 2026-09-08
---

# 17. Which Way Round Are You Working?

*Choose your method before you touch anything*

<!-- Every number in this chapter must come from:
     - wedge_geometry.longest_member_in
     - wedge_geometry.radius_for_member_length
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## Which Way Round

There are two ways to size a wedge dome, and the first thing you have to do
is work out which one you are actually in. Not which one you would like to be
in. Which one you are in.

If you get this wrong you will spend a week doing arithmetic that describes a
building you cannot build, and you will not find out until the day you go to
cut, when the longest stick the frame wants turns out to be eight inches
longer than the longest stick you own.

Everything in the next five chapters follows from this one decision, so it
gets its own short chapter and no other content.

## Design first, or tree first

**Design first** is the way everybody expects to work. You know what you
want: a room of a certain size, a ceiling you can stand under, a footprint
that fits between the trees you are not cutting down. You start from the dome
and you work backwards to the woodpile. The output is a shopping list — this
many sticks, this long, and therefore this much trunk.

**Tree first** is the way this book was actually written. You have trees.
They are the trees you have: a certain height, a certain taper, a certain
amount of straight length between the butt flare and the first serious bend.
You start from what a section of that trunk can be cut into and you work
forwards to the dome. The output is not a shopping list. It is a diameter,
and you find it out rather than choosing it.

Both are honest. Neither is better. They answer different questions and they
run in opposite directions, and the entire content of Chapters {{ch.method_a}} and {{ch.method_b}} is
those two directions worked through in full.

## The honest test

Here is the test, and it is uncomfortable.

**Are the trees already down, or already chosen?**

If they are — if you are standing next to a windfall, or you have marked two
pines at the back of the property, or somebody has offered you a load — then
you are in Method B, and picking a diameter is not a decision you get to
make. It is a wish. You may still write a number on a piece of paper. The
trees will not read it.

If the trees are genuinely not chosen — you will buy or fell whatever the
design calls for, and there is enough standing timber that a foot either way
on the bucking length costs you nothing — then you are in Method A, and you
should design the dome you want.

Almost everybody thinks they are in Method A. Most people are in Method B.
The tell is whether you would actually go and get a different tree if the
arithmetic asked for one. If the answer is "well, I'd probably make it work
with these," you are in Method B and you may as well admit it on page one
rather than on cutting day.

![Start from what you actually have.](../../deliverables/book/figures/method-decision.png)

## What both methods share

Underneath the two directions there is one relationship, and it is worth
understanding before you use either method, because it is the thing that
makes both of them exact rather than approximate.

In a 2V dome of radius *R*, every panel is a triangle whose corners sit on the
sphere. If the members simply ran corner to corner you could scale them
straight off the radius: double the dome, double the stick. But they do not
run corner to corner. They pinwheel — each member's end lands on the *side*
of the next one rather than on a shared point — and the amount each member is
set back from the true corner depends on **how wide the member is**, not on
how big the dome is.

A wider stick sits back further. And the width of your stick comes from the
diameter of your log, which has nothing whatsoever to do with the dome.

So member length is not proportional to radius. It is radius *minus* a
correction that stays the same size while the dome grows. Which means:

* Going from radius to member length is a calculation.
* Going from member length back to radius is that same calculation, solved
  backwards.

Neither direction is a rule of thumb, a table, or a fudge factor. They are
one function and its inverse, and Chapter {{ch.round_trip}} exists solely to run them
against each other and print the difference, which is
{{roundtrip.residual_in}} inches.

## Before you go on

Whichever method you are in, you need three measurements before either
chapter is any use to you:

1. **The diameter of your log at the middle of a section.** Not at the butt —
   the butt is the fattest part and it flatters you. The middle, because that
   is what the average stick will be.
2. **The straight length you can get out of the trunk.** Between the flare
   and the first bend that would spoil a section.
3. **The longest piece you are willing to carry on your own.** This is a real
   constraint and it does more to set the dome's size than anything you will
   read in a book. A six-foot green pine wedge is heavy. An eight-foot one is
   a two-person lift, and if there is only one of you, that is the end of the
   discussion.

Write those three numbers down. Then turn to Chapter {{ch.method_a}} if you are designing
first, or Chapter {{ch.method_b}} if the trees are already on the ground.

And then, whichever one you used, read Chapter {{ch.round_trip}} and check it with the other
one. That takes ten minutes and it is the cheapest insurance in the book.
