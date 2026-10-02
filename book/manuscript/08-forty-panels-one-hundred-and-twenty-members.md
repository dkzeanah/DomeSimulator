---
chapter: 8
title: Forty Panels, One Hundred and Twenty Members
strand: explain
status: drafting
target: 2350
updated: 2026-09-17
---

# 8. Forty Panels, One Hundred and Twenty Members

*The 2V hemisphere, counted*

## Forty Panels

This chapter names the frame itself, because every number after it — the
cut list, the jig, the fortnight, the seams — is a count of something that
exists on this frame, and the frame deserves to be introduced before it is
counted.

It is a two-frequency geodesic dome: a hemisphere of {{frame.panels}} flat
triangular panels, held up by {{frame.members}} wooden members. There are
{{frame.edges}} distinct edges in its geometry, of which {{frame.seams}}
are seams where two panels meet and {{frame.rim_edges}} run around the
base where the dome meets the ground and join nothing. Those are the four
numbers the whole book hangs on, and none of them was chosen. All of them
fell out of the geometry — an icosahedron, subdivided once, projected onto
a sphere, cut in half at its widest line — and the rest of this chapter
shows where they come from, because a count you can retrace is a count you
can trust, and a count you cannot is a story.

The frame in the picture is the actual solved dome this book builds — the
same meshes the simulator solves, pushed apart along each panel's own
normal so you can see that it really is forty separate triangles and not
one continuous surface. That separation is not just a drawing trick. It is
how the thing gets built, one finished triangle at a time, on the ground,
and it is the subject of Chapter {{ch.own_edge}}.

## Where 2V comes from

The geometry is older than the dome and worth knowing once, because
everything the frame does follows from it.

Start with an icosahedron: twenty identical equilateral triangles, twelve
vertices, the roundest of the five Platonic solids. It is already close to
a sphere, but its faces are big flat slabs. Subdivide: split every edge in
half and connect the midpoints, and each of the twenty faces becomes four
smaller triangles — eighty faces in all. Now the move that makes it a
dome: push every vertex outward until it lies exactly on a sphere of the
same radius. The triangles stop being identical — those nearer the
original vertices stretch differently from those near the midpoints — but
they all lie on one spherical surface, which is what "geodesic" means
here: the straight lines of the original faces become the chords of a
sphere.

Cut that sphere at its equator and keep the top half. What remains is the
frame: {{frame.panels}} triangles, because a full subdivided icosahedron
has eighty faces and the hemisphere keeps half.

That one operation — subdivide once — is what "2V" names: the frequency
two subdivision of the icosahedron. It is the smallest subdivision that
produces a useful building, and its gift is the number in Chapter
{{ch.two_lengths_not_forty}}: all {{frame.edges}} edges of the hemisphere
come in only two lengths, because the subdivision only ever produces two
kinds of edge — the original icosahedron edges, now halved, and the new
edges between midpoints. Two lengths, not forty, is what makes one person
with one jig able to build this at all. Chapter {{ch.frequencies}} shows
what higher frequencies buy and cost; the whole of the rest of this book
stays at 2V, because 2V is where the trade stops being worth paying.

![Forty panels, {{frame.members}} members, {{frame.seams}} seams between them.](../../deliverables/book/figures/frame-exploded.png)

## The frame, exploded

The plate is the frame with its {{frame.panels}} panels pushed apart along
their own normals, each triangle floating a little way out from where it
will finally sit. Read it as an inventory before you read it as a picture.

**Forty triangles.** Two shapes, in a fixed ratio: the triangles that sit
around the five-fold points and the triangles that fill between them. Not
forty shapes — two — which is the second great simplification of the
frame, after the two lengths.

**Three members each.** Every triangle is built complete, with its own
three sticks, its own joints, its own edge. Three times forty is
{{frame.members}}: the member count of the whole frame, and the number the
tree chapter will chase in wood.

**The seams where they will meet.** Where two panel edges lie against each
other there will be a seam — a key between the two members, a gasket, a
line on the outside of the shell. The frame has {{frame.seams}} of them.
The {{frame.rim_edges}} edges around the base are different: nothing meets
them from outside, so they are rim, not seam, and the book keeps the two
counts apart because a builder closing {{frame.seams}} seams must not be
told to close {{frame.edges}}.

![Counted from the solved dome, not chosen.](../../deliverables/book/figures/frame-counts.png)

## What the frame contains

The table counts the frame two ways and they agree, which is the whole
point of printing it.

**By panels:** {{frame.panels}} panels times {{frame.members_per_panel}}
members each is {{frame.members}} members.

**By edges:** {{frame.seams}} seams each holding two members — one from
each neighbouring panel — plus {{frame.rim_edges}} rim edges holding one,
is {{frame.members}} again.

The two routes give the same number because the frame is panelised: every
panel owns all three of its edges, so an interior seam is always a
sandwich of two members and a key, never one shared strut. That costs
wood — {{edges.duplication_ratio}} members for every unique edge — and
Chapter {{ch.own_edge}} is the full accounting of what the extra wood
buys. For this chapter the table's job is narrower: the frame is not a
number somebody remembered, it is a number the geometry produces, and the
geometry produces it twice.

## Why hemispheres and not spheres

One honest question deserves an answer before the build chapters start:
why is the book about half a sphere, when the geometry naturally makes a
whole one?

**A hemisphere has a floor.** Cut a sphere at its equator and the cut
line is a flat circle, lying in a plane, exactly where a building wants
its ground. The dome meets the earth along its {{frame.rim_edges}} base
edges, all in one plane, and every vertex of the base ring sits on the
ground at once. A full sphere has no such line; it touches the ground at
a point and the entire weight of the building hangs from that point's
anchorage. The hemisphere is the shape a sphere becomes when you give it
somewhere to stand.

**The rim is the honest part.** Those {{frame.rim_edges}} base edges are
the one place the geometry does not close on itself — the place where the
frame's seams run out. The book treats the rim as its own piece of the
build: Chapter {{ch.the_footing_and_the_ring}} gives it its own footing,
Chapter {{ch.openings}} puts its doors in it, and Chapter
{{ch.where_error_goes}} names it as the one place error can accumulate.
A hemisphere is not a sphere with the bottom missing. It is the shape
that has a bottom, and that is why it can be a building at all.

**And the crown is the trade.** Half a sphere sacrifices the volume above
the equator — the part of the ball nobody could stand in anyway — and
keeps everything from the widest line down, which is where the room is.
The floor area, the headroom, and the standing-height map are all counted
from that choice in Chapter {{ch.round_room}}. For now the frame simply
is what it is: {{frame.panels}} triangles, {{frame.members}} members,
{{frame.seams}} seams, {{frame.rim_edges}} rim edges — the count the
geometry gives, printed whole, before anything is built from it.
