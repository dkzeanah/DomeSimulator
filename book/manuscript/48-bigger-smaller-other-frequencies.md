---
chapter: 48
title: Bigger, Smaller, Other Frequencies
strand: explain
status: drafting
target: 2200
updated: 2026-09-17
---

# 48. Bigger, Smaller, Other Frequencies

*Changing the dome without changing the method*

## Other Frequencies

The whole book so far has built one dome: the 2V hemisphere of
Chapter {{ch.forty_panels_one_hundred_and_twenty_members}},
subdivided once from the icosahedron. This chapter opens the
question the outline's own logic raises: what happens to the
method when the frequency changes — and what does not change at
all.

The frequency of a geodesic dome is how many times the
icosahedron's edges are subdivided before projection. 2V splits
each edge once; 3V splits it twice; 4V three times. The method
this book teaches — split logs, pinwheel panels, one jig — does
not care which frequency it frames, and that is the chapter's
first finding: the method is the same, and only the numbers
change. The rest of the chapter states the trade the numbers
make, and the place where the method stops working altogether.

## More panels, shorter sticks

The trade, stated as arithmetic, because "3V is smoother" is an
adjective and this book trades in counts.

Higher frequencies subdivide harder: more triangles per face,
more panels in the hemisphere, and — this is the part that
matters — *shorter* members, because every edge is a smaller
fraction of the sphere. The panels multiply, the members shorten,
and the dome approaches a true sphere, which is the entire
point of the higher frequencies for anyone whose skin or
aesthetic wants roundness. The cost is the pile: more panels
means more seams, more keys, more screws, more motions of the
jig — and fewer of the frame's parts repeat in the way 2V's
two-lengths-two-shapes economy allows. The table below runs
the counts, and the honest reading of it is that 2V is not the
*best* dome; it is the *cheapest* dome at the scale the method
was designed for, and the higher frequencies buy smoothness
with repetition.

What does not change is the more important list. The split, the
sector, the pinwheel, the jig, the overfit, the seam key — none
of them cares whether the frame is 2V or 3V. A 3V dome built
this way is still one log, seven cuts, one bench, forty panels
and a fortnight; it just has more panels in the fortnight. The
method transfers, which is the sentence the chapter exists to
prove: the wedge is not married to the frequency, it is married
to the triangle, and every frequency is made of triangles.

![What each frequency asks of the woodpile.](../../deliverables/book/figures/frequency-compare.png)

## Frequency comparison

The table is the trade in full: 2V, 3V, 4V, each with its panel
count, its member classes and its longest member, all computed
from the same geometry so the rows differ only by frequency.

The row that matters is the member-length row, because it is
where the frequencies meet the method's own constraint. 2V's
longest member is {{dome.longest_member_in}} inches — the size
the tree chapter bucked for. The higher frequencies' members
are shorter, which would let the same trees build a *bigger*
dome at the same handling limit — the flat-rate argument of
Chapter {{ch.flat_rate}}, applied through the frequency knob.
That is the real decision the table supports: not "which dome is
rounder" but "which frequency lets these trees and these arms
build the floor I want", and the answer is read off the table
the same way every other sizing decision in this book is read —
by looking at the row, not the adjectives.

## Where the method stops working

The honest limit, stated so the chapter does not over-sell its
own transferability.

The method stops working at the *small* end, and the reason is
the sector's own geometry. A dome too small for its split count
has panels whose edges are shorter than the members are *wide*
— the sector's bark face is {{member.width_in}} inches across,
and a panel whose sides approach that width can no longer
accommodate the pinwheel's overlap, the inset, and the key. The
joints crowd the corner, the overlap swallows the triangle, and
the method's arithmetic quietly runs out of room. The fix is
not a smaller split — a six-inch dome needs a different member,
not a thinner wedge — and Chapter {{ch.wedge_variations}} is
where the alternatives live.

At the large end the method does not stop; it *delegates*.
Big domes want higher frequencies for the member-length reason
above, and beyond the handling band of Chapter {{ch.flat_rate}}
they want crews, which is Chapter {{ch.building_with_other_people}}.
The method itself keeps working — the split, the jig, the seam
— all the way up; what changes is the schedule, not the
procedure. The chapter's closing sentence is the one it opened
with: the method is the same at every frequency. Only the
numbers change, and the numbers are in the table.

## Where the two lengths actually come from

Every frequency above is built by the same five moves, and it is worth walking
them once with numbers, because the films spend a whole chapter on it and this
book had only ever printed the *results*.

**Start with a solid.** The icosahedron has {{dm.ico_vertices}} corners,
{{dm.ico_edges}} edges and {{dm.ico_faces}} faces, and
V − E + F = {{dm.euler}} however many times you subdivide it. That identity is
the cheapest bug detector in geometry, and the book uses it as one.

**Put it on a sphere of radius one.** Divide every corner by its own distance
from the centre and the parent edge measures {{geom.parent_edge}} of the
radius — the only number in this section that is not a length a reader can
hold.

**Halve every edge.** The midpoint of a straight edge is the average of its two
ends, and that average falls *inside* the sphere: the midpoint sits
{{geom.mid_norm}} of the radius from the centre, a shortfall of
{{geom.mid_sag}} — {{geom.mid_sag_pct}} per cent of the radius. On a small
model that is nothing; on a building it is the difference between a faceted
ball and a dome, and it is the arithmetic answer to the reader who assumes a
sphere must be rounder. A sphere drawn with straight sticks is not round at
all, and the input to that error is a straight line drawn where the surface
curves.

**Push each midpoint back out** to the surface — divide it by its own length.
That one operation is the entire difference between an icosahedron and a
geodesic dome, and it is what the films call the geodesic step. It leaves the
edge line kinked, and the kink is where the second length comes from.

**Measure the two.** The chord from a corner to a projected midpoint is
{{geom.short_factor}} of the radius; the chord between two projected midpoints
is {{geom.long_factor}}. Two lengths and no third: that is why the cut list has
two classes rather than forty, and it is the arithmetic behind every table in
this chapter.

Two corrections for things a reader may have heard, both checked rather than
asserted.

**Phi is not the strut ratio.** The golden ratio is {{geom.phi}}, and it has a
real home in this geometry: the twelve corners of the icosahedron are three
golden rectangles at right angles to each other. But the ratio *between the two
struts* is {{geom.factor_ratio}} — about {{geom.phi_gap_pct}} per cent below
phi, near enough to look like a coincidence on a drawing and nowhere near
enough to build on. A two-frequency dome is not a golden-ratio dome; it is a
dome whose parent solid happens to be built from golden rectangles.

**The boards are not the factors.** Cut {{dm.ref_long_in}} inches and
{{dm.ref_short_in}} and you are cutting the solved lengths. Measure two boards
on a bench and you get {{geom.board_ratio}} — {{geom.board_gap_pct}} per cent
above the factor ratio, because a tape, a kerf and a real log are not a unit
sphere. The worked-build chapter fits both boards by least squares rather than
trusting either, and that {{geom.board_gap_pct}} per cent is exactly what it is
fitting around: the arithmetic is exact and the tree is not, which is the
method's whole position in one line.
