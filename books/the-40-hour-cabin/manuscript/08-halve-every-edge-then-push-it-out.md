---
chapter: 8
title: Halve Every Edge, Then Push It Out
strand: explain
status: draft
target: 1820
updated: 2026-10-03
---

# 8. Halve Every Edge, Then Push It Out

Chapter {{ch.phi}} placed twelve points in perfectly even space, and twenty
triangles strung between them make an icosahedron. That is a ball, of a kind:
a very faceted one, with flat faces the size of a door.

Two moves turn it into a geodesic dome. Halve every edge. Then push the new
points out to the sphere. This chapter is those two moves, and the reason the
second one is the whole idea.

## Put it on a sphere of radius one

<!-- concept: 2v/normalize -->
<!-- concept: scratch/normalize -->
<!-- concept: scratch/m_normalize -->
<!-- concept: build/unit -->

The twelve points come out of the golden ratio at an awkward size: every one of
them sits {{geo.raw_r}} units from the centre. Not one, and not anything you
would choose.

So divide every point by its own distance from the centre. Each point keeps
its direction and lands at exactly one. The icosahedron now sits on a sphere of
radius one, and its edge, which measured two units, measures {{geo.icosa_chord}}.

That number is not a length. It is a **chord factor**: a multiplier. Every
distance in the model is now a multiple of a radius you have not chosen yet.
Choose a radius in inches and multiply, and you have inches; choose one in
metres and you have metres. The same numbers serve a playhouse and a hangar,
which is why the size of this book's dome is decided last (Chapter {{ch.size}})
rather than first.

![The icosahedron on a sphere of radius one.](plate-unit-sphere.png)

## Halve every edge

<!-- concept: 2v/subdivide -->
<!-- concept: build/halve -->
<!-- concept: scratch/midpoints -->
<!-- concept: scratch/m_midpoint -->

The icosahedron has {{geo.parent_edges}} edges. Find the halfway point of each
one -- add the two end points and halve them -- and you have
{{geo.parent_edges}} new points. Join them up and every one of the
{{geo.parent_faces}} faces is cut into four smaller triangles.

![Thirty parent edges, thirty midpoints.](plate-halve.png)

But look where the new points are. Both ends of an edge are on the sphere; the
straight line between them cuts *inside* the ball, the way a chord cuts inside a
circle. Every midpoint sits only {{geo.mid_r}} of the way out:
{{geo.sag_pct}} percent of the radius short of the sphere. On this book's dome
that is {{geo.sag_in}} inches.

Leave the midpoints there and you have an icosahedron with more triangles. Flat
faces, just smaller ones. Not a dome.

![The straight line cuts the corner.](plate-midpoint-sag.png)

## Push the midpoints out

<!-- concept: 2v/project -->
<!-- concept: build/project -->
<!-- concept: scratch/m_project -->

So push every midpoint straight out from the centre until it reaches the
sphere. And here is the elegant part: that is the same division as before.
Divide the point by its own distance from the centre. Its direction does not
change -- it slides out along its own ray -- and its distance becomes one.

Each midpoint travels {{geo.sag}} of a radius outward. Each face keeps its
layout and simply bulges.

![Same direction, distance set to the radius.](plate-push-out.png)

**This one division is the entire difference between a faceted ball and a
geodesic dome.** And it does something the halving did not: it breaks the
equal edges. Before the push, the four small triangles in each face were
identical. After it, all three corners of the middle triangle have moved out,
so it grows more than the three at the corners of the face, each of which has
only two of its three points moved. The middle triangle comes out equilateral
in the long length; each corner triangle keeps two short sides from its
parent corner and gains one long one. The dome now has edges of two lengths.

## Two lengths come out

<!-- concept: 2v/classes -->
<!-- concept: scratch/classes -->

Measure every edge of the whole sphere again: {{geo.sphere_edges}} of them.
They collapse into exactly two numbers:

    short edge    {{cut.b_factor}} x the radius
    long edge     {{cut.a_factor}} x the radius

Those are the two chord factors of a 2V dome, and they are why this book cuts
two lengths of member and only two. Chapter {{ch.four_ways}} derives them four
independent ways and prints the difference between the answers. The long one
is exactly one over the golden ratio; the short one is not golden at all
(Chapter {{ch.phi}}).

![A hundred and twenty edges, exactly two lengths.](plate-two-classes.png)

## Euler's check

<!-- concept: scratch/counting -->
<!-- concept: scratch/m_euler -->

How do you know the shape in the computer really closed up, with no missing
face and no doubled corner? One addition.

For any closed surface without holes, corners minus edges plus faces is two.

    the icosahedron       {{geo.parent_corners}} - {{geo.parent_edges}} + {{geo.parent_faces}} = 2
    after 2V              {{geo.sphere_corners}} - {{geo.sphere_edges}} + {{geo.sphere_faces}} = 2

Anything other than two is a bug: a hole, a missing triangle, a corner counted
twice. It is the cheapest proof in geometry, and the software that drew every
picture in this book runs it.
