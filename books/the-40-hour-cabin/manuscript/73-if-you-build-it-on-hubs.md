---
chapter: 73
title: If You Build It on Hubs
strand: howto
status: draft
target: 1740
updated: 2026-10-05
---

# 73. If You Build It on Hubs

This book splits logs and avoids the hub, and Chapter {{ch.framing}} explained
why. But plenty of people will build a dome from bought stock on a bought
connector, and the films that go with this book teach that build too. This
chapter is that build, at the same two frequencies the rest of the book
uses, so nobody has to go elsewhere for it.

## The five words

<!-- concept: build/vocab -->

- A **hub** is a joint.
- A **strut** is a straight member between two hubs.
- A **panel** is the triangle they enclose.
- A **chord factor** is a strut's length divided by the radius -- which is what
  lets one drawing serve every size of dome.
- **Frequency** is how many times each edge of the parent shape was divided:
  two, here, which is where "2V" comes from.

## Two lengths, and the hub that decides every cut

<!-- concept: build/classes -->

Measure every edge of the finished sphere and they fall into two groups, and
only two. The shorter runs from an original corner to a projected midpoint:
**{{tt_dm.short_factor}}** of the radius. The longer runs between two
projected midpoints: **{{tt_dm.long_factor}}** of the radius, which is exactly
one over φ -- the one place the golden ratio does show up in the answer. Their
ratio is {{tt_dm.ratio}}, not φ. A hubbed hemisphere is
{{tt_dm.f2_struts}} struts on {{tt_dm.f2_hubs}} hubs.

<!-- concept: build/hubkit -->
<!-- concept: build/deduction -->

Now the decision that comes before any cut: **choose the hub system.** A
steel star plate, a bevelled timber joint and a drilled hub ball all build the
same geometry, but they eat different amounts of strut. Choose one, build one
joint for real, and measure how much shorter the members have to be.
Everything downstream depends on that measurement, and no catalogue number is
a substitute for it.

![Choose the hub system before anything else.](plate-hub-kit.png)

Because every number in the geometry is **hub centre to hub centre** -- that
is what the sphere is made of -- and the stick you cut has to be shorter by
whatever the two connectors occupy:

    cut length = centre length - deduction

The deduction is the total across *both* ends, not per end. Halving it by
mistake is one of the commonest ways a dome ends up refusing to close.

<!-- concept: build/endcut -->

A strut is a chord, so it dips below the sphere between its ends, and it
leaves the surface at **half the central angle** it spans: one line of
arithmetic. That is {{hub.endcut_short}} degrees for a short strut and
{{hub.endcut_long}} for a long one -- the angle to tip a hub plate to, or to
cut a timber end back to.

## Bevels, hub types and the stock

<!-- concept: build/bevel -->
<!-- concept: build/hubs -->
<!-- concept: build/stock -->

Where two panels meet along a strut they fold, and if you are skinning with
rigid sheets each edge wants planing to half the fold so the faces meet
cleanly. There are exactly two fold angles in the whole dome, one per strut
class, so two saw settings and no thinking at the bench:
**{{tt_dm.bevel_long}} degrees** on a long board and
**{{tt_dm.bevel_short}}** on a short one.

The hubs are not all alike. Group them by how many struts arrive and at what
angles -- {{tt_dm.vertices5}} five-way and {{tt_dm.vertices6}} six-way in the
hemisphere, plus the rim -- and each type is its own part. Make a set of each,
keep them in separate labelled boxes, and check one against a drawing before
making the rest. Make the base hubs first, because they also take the anchor
bolts.

And buy the stock before you fix the radius. At some radii a standard length
of stock yields exactly one strut and throws the rest away; a small change in
radius can turn one piece per stick into two. Count kerf when you do the sum:

    pieces per stick = floor((stock + kerf) / (cut + kerf))

## Cut, jig, raise

<!-- concept: build/cutting -->
<!-- concept: build/subassembly -->
<!-- concept: 2v/triangles_build -->

1. **Cut one class at a time.** Set a stop block and cut every piece of that
   class without touching the setting. Keep the very first good piece as a
   master and compare the rest to it, not to a tape -- a tape adds a new error
   every time. Label each piece as it comes off the saw. Then, and only then,
   move the stop.
2. **Build the triangles flat.** The hemisphere has two kinds of triangle:
   {{tt_dm.iso_count}} with two short sides and one long, and
   {{tt_dm.equi_count}} with three long sides. Lay one of each out on a flat
   floor, screw blocks down round it to make a jig, and assemble the rest
   inside the jig. Every panel comes out identical, and the raise becomes
   bolting known-good pieces together rather than fitting each one.
3. **Raise in rings from the base**, never up one side -- Chapter
   {{ch.raise}}.

PVC, timber and tube all share the same centrelines. They do not share end
cuts, and they certainly do not share structural capacity.

![Build the triangles flat, first.](plate-flat-triangles.png)

## The four things that actually go wrong

<!-- concept: build/failures -->

Domes rarely fail because the arithmetic was wrong. They fail because:

1. the connector deduction was **guessed** instead of measured;
2. the base was **not level**;
3. somebody built **up one side** instead of in rings;
4. two similar-looking members **got mixed up**.

Each of those is a habit, not a calculation, and each is cheap to fix before
you start and expensive after.

![The four things that actually go wrong.](plate-four-failures.png)
