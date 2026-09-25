---
chapter: 6
title: Two Lengths, Four Ways
strand: explain
status: draft
target: 940
updated: 2026-09-25
---

# 6. Two Lengths, Four Ways

Never trust one calculation.

![The two chord factors, derived four ways.](plate-chords-four-ways.png)

## What is being checked

After subdivision and projection, the finished sphere has 120 edges. Measure
all of them and they fall into exactly two lengths — no more, no fewer:

    short   {{cut.b_factor}} R
    long    {{cut.a_factor}} R

Those two numbers decide every stick you will ever cut. If either is wrong,
every member is wrong, and the frame will not close — but it will not fail
*obviously*. It will be a bit out, everywhere, and you will spend the
assembly blaming your sawing.

So it is worth more than one derivation.

## Route one: subtract the coordinates

The two points are known — they came out of Chapter {{ch.phi}}'s twelve, then
a midpoint, then a projection. Subtract one from the other and take the
length.

    |u − v| = {{cut.b_factor}}

Direct, and it depends on nothing but arithmetic.

## Route two: the central angle

Two points on a unit sphere subtend an angle at the centre. Take the dot
product of the two unit vectors, take the arc cosine, and you have that
angle. Then the chord across it is 2·sin(θ/2).

Completely different arithmetic — trigonometry rather than subtraction — and
it uses the fact that the points are on a sphere, which route one never
assumed.

Same answer.

## Route three: the law of cosines

The same triangle, solved the way a surveyor would: two sides of length one
and a known included angle.

Same answer again, by a third road.

## Route four: measure it

Build the thing in CAD and put a dimension on it.

This one matters more than it looks. The first three are all the same person's
reasoning in three costumes; if the underlying model is wrong they will agree
with each other and all be wrong together. Measuring the drawn object catches
an error in the *model* rather than in the algebra.

## What the residual is

Routes one and two differ by about **1.1 × 10⁻¹⁶**.

That is not "close". That is the gap between two different sequences of
floating-point operations on numbers that are mathematically identical — the
smallest disagreement a computer can express at this magnitude. It is the
answer you get when two methods agree completely.

![Two ways of computing the same number, and the residual between them.](plate-cross-check.png)

## Why the book does this everywhere

This is the pattern, not a one-off.

Where two ways of computing something exist, this project computes both and
prints the difference. The strut table in Chapter {{ch.two_lengths}} does it
for the pinwheel's bite. The seam angles do it for the fold. And the audit
described in Chapter {{ch.tooling}} does it for the whole book, checking every
printed figure against what the code can produce.

The reason is not rigour for its own sake. It is that **a wrong number in a
building method does not announce itself.** It becomes a pile of sticks that
nearly fit, two weeks in, with the tree already down.

Four routes and a residual of 10⁻¹⁶ costs an afternoon once. Finding out the
other way costs the tree.
