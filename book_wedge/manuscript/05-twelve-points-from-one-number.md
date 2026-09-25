---
chapter: 5
title: Twelve Points From One Number
strand: explain
status: draft
target: 1320
updated: 2026-09-25
---

# 5. Twelve Points From One Number

The golden ratio has a real job in this method and it is not the one people
expect.

Here is the job.

![Twelve points placed by one irrational number.](plate-phi.png)

## The number

φ — phi — is **{{phi.value}}**.

It is defined by one property: it is the number whose square is itself plus
one. φ² = φ + 1. Solve that and you get (1 + √5) / 2, which is where the
decimal comes from.

That is the whole definition. No rectangles, no seashells, no Parthenon.

## What it does here

Write down three numbers: 0, 1 and φ.

Now make points by putting them in every order with every combination of
signs:

    (0, ±1, ±φ)
    (±1, ±φ, 0)
    (±φ, 0, ±1)

Three families, four sign choices each. **Twelve points.**

Measure the distance from each point to its nearest neighbours: exactly
2.000, every time. Measure each point's distance from the origin:
**{{phi.radius}}**, every time, because it is √(1 + φ²) and every point has
the same coordinates in a different order.

Twelve points, all the same distance from the centre, all the same distance
from their neighbours. That is an icosahedron — the most even way to place
twelve points on a sphere — and it fell out of writing one irrational number
into a list of coordinates.

Nobody measured anything. Nobody iterated toward a solution. The evenness is
a consequence of φ's one property, and this is the only place in the whole
derivation where something arrives for free.

## Why that property does it

Briefly, because it is worth knowing rather than accepting.

The icosahedron's twelve vertices can be seen as three golden rectangles
standing in three perpendicular planes, interlocked. A golden rectangle is
one whose sides are in the ratio 1 : φ — and the reason *that* ratio works is
φ² = φ + 1, which is exactly the relationship needed for the three rectangles'
corners to land the same distance apart.

So the defining property of φ is not decorative here. It is the thing being
used.

## Where it survives to

Now subdivide. Cut every edge of those twenty faces in half, push the new
points out to the sphere, and measure what you get.

Two lengths, and only two — Chapter {{ch.four_ways}} proves there are no
others. Expressed as multiples of the radius:

    short   {{cut.b_factor}} R
    long    {{cut.a_factor}} R

Look at the long one. **{{cut.a_factor}} is exactly 1/φ.**

{{phi.reciprocal}}, to nine places, and it is not an approximation — it is
φ − 1, which is the same number by φ's own defining property.

So the golden ratio places the twelve starting points, and then it comes all
the way through the subdivision and the projection and lands in your cut
list. When you crosscut a member at {{cut.a_chord}} inches, you are cutting
the radius divided by the golden ratio.

## And the place it is not

Here is the part that surprises everybody, including me.

The **ratio between the two struts is not golden.**

    long / short = {{phi.chord_ratio}}

Not 1.618. Not 0.618. {{phi.chord_ratio}}, which is not φ, not 1/φ, not φ²,
and not any simple expression of φ at all.

People assume it is. It feels like it should be — the whole thing came out of
φ, the long factor *is* 1/φ, so surely the two lengths are in a golden
relationship. They are not, and a dome cut on that assumption is a dome with
sixty wrong sticks in it.

The short factor {{cut.b_factor}} is its own number. It comes out of the
subdivision arithmetic and it does not simplify.

## The lesson, which is about more than phi

A pattern that holds four times is not a rule.

φ places the points. φ gives the long chord. Both are exact and both are
checkable. The third thing — the ratio — looks like it must follow and it
does not, and the only reason this book knows that is that something computed
it rather than assuming it.

That is why every number in these pages is derived rather than typed, and it
is why the next chapter computes the same two factors four separate ways and
prints the difference between them.
