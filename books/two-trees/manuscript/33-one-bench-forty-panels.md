---
chapter: 33
title: One Bench, Forty Panels
strand: reference
target: 2650
status: drafting
updated: 2026-09-17
---

# 33. One Bench, Forty Panels

*What the jig is and what each part of it does*

## One Bench

This is the reference chapter for the fixture itself: what the jig
is, part by part, straight from the simulator that models it, so the
bench on your floor and the bench in the model cannot disagree about
what a jig is.

Chapter {{ch.the_jig}} told the story of the day it was built.
This chapter is the thing, cold: the twelve stages a panel passes
through on it, the labelled drawing of the fixture before any wood
is on it, and the procedure for laying the whole thing out full size
on a real floor with nothing but string and a pencil. Come back to
this part while you are working, not while you are reading — the
book's reference chapters are written for the bench, and this one
lives there.

## The twelve stages

The table is the jig's whole working life, generated from the
simulator's own stage list: every stage a panel passes through
between the raw pile and the finished triangle, named and ordered.

Read it as a checklist, not as a description. The twelve stages are
the production run of Chapter {{ch.days_ten_to_twelve_forty_panels}},
expanded to the resolution the bench actually works at — where each
member is located, what gets cut when, what gets screwed when. The
order is not optional in the way a recipe's order is optional; the
head overfit of Chapter {{ch.head_overfit}} only works because the
flush cut happens at the stage the table says, after the panel is
already a panel and before it leaves the bench. A stage skipped is
an error invented, and the table exists so the skip is visible.

![The twelve stages, in order.](../../deliverables/book/figures/jig-stages.png)

## The jig, labelled

The drawing is the fixture before any wood is on it: the bench, the
triangle, the rails, the fences, the cut planes — every component
called out, each with its one job.

**The bench** is the flat truth everything else is measured from.
**The triangle** is the panel's outline, built in stops around the
outside. **The rails** carry the saw where a cut must be made.
**The fences** are the lines the butts land against and the heads
are cut against. **The cut planes** hold the angles of Chapter
{{ch.butt_cut}} so no hand has to. Between them they do the one
thing a jig must do: they replace every decision with a position,
and the position does not move.

The drawing comes from the simulator's own jig model — the same
geometry the fabrication package exports — so the picture and the
fixture are the same object, drawn twice. If the bench you build
disagrees with this drawing, one of you is wrong, and the simulator
is not the likely one.

![Bench, triangle, rails, fences, cut planes.](../../deliverables/book/figures/jig-labelled.png)

## Setting it out on a real floor

The full-size layout, because the jig's accuracy is bought on this
afternoon and nothing after it.

**Start with the longest member.** Draw the first side of the
triangle full size, straight off the cut list of Chapter
{{ch.worked_build}} — the actual length, gasket allowance included,
marked on the bench surface with a pencil and checked twice. This
line is the triangle's truth; the other two sides are located from
it.

**Swing the arcs.** From each end of the first line, swing an arc
at the length of its neighbouring side — string and a pencil, the
oldest layout tool there is, and still the straightest for distances
bigger than a square. Where the two arcs cross is the third corner.
The triangle is now on the floor, full size, and the only measured
numbers in it were the three member lengths.

**Check the angles against the drawing.** Before any stop is
screwed down, compare the laid-out triangle against the panel
drawing of Chapter {{ch.panel_drawings}}: the base angles, the
heights, the relation between the long and short sides. A layout
that matches the drawing within a pencil line is the jig's
foundation; a layout that does not is the cheapest error the whole
build will ever catch.

**Screw the stops.** The outline becomes physical: stops along all
three outside edges, then the fences inside for the butts and the
heads, then the cut planes. Each stop is set against the pencil
line, not against the previous stop — a stop set from a stop
compounds its neighbour's error, and the whole point of the layout
is that every position is measured from the drawing once.

**Prove it with the first panel.** The first panel off the bench is
the test: lay it back over the layout lines, and if its edges fall
on the pencil, the jig is true. The fourth-panel rule of Chapter
{{ch.days_ten_to_twelve_forty_panels}} applies here too — the first
panel proves the bench, and everything after trusts it.

## Locate from the sawn faces, never the bark

The last section of the reference, and the principle that makes a
jig work on natural timber at all.

Bark is irregular. No two sticks share it, it compresses under a
clamp, and it is the one surface of the wedge the saw never touched.
The two sawn faces are the opposite: flat, because the saw made them
flat, and at the same angle on every stick, because every stick is
the same sector of the same circle. So the fixture locates the
member on its sawn faces, and only on its sawn faces. The bark
floats in an oversized clearance and is never asked to locate
anything.

The rule reads as fussiness and is the whole tolerance budget of
the method in one sentence: precision where precision matters, and
tolerance where the tree varies. The sawn faces are the precision;
the bark is the tree varying; and the jig that confuses them builds
forty panels, each as individual as the log it came from — which is
the frankendome, again, wearing a better bench.

Chapter {{ch.where_error_goes}} follows the same principle out into
the whole build. This chapter ends it where it starts: one bench,
two datum faces, forty identical panels.
