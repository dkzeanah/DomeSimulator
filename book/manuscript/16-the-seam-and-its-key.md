---
chapter: 16
title: The Seam and Its Key
strand: explain
status: drafting
target: 3450
updated: 2026-09-17
---

# 16. The Seam and Its Key

*Where two panels meet, and the angle nobody wants to hear about*

## The Seam and Its Key

This is the least glamorous chapter in the book, and it is the one that
decides whether the dome closes.

The frame's {{frame.panels}} panels do not simply sit next to each
other. They meet at {{frame.seams}} interior lines, and at every one
of those lines two flat triangles fold against each other at an angle
that the sphere, not the builder, chose. Between the two members in
each seam sits a key — a strip of wood or compressible material cut to
the fold — and the key is where the whole tolerance budget of the
method finally lands. Get the keys right and the dome closes like a
lid. Get them wrong and forty panels of *nearly* closing is a dome
with a gap in it, which is what Chapter {{ch.the_cut}} spent a week
learning the hard way.

The chapter has one unwelcome fact to deliver first — the fold angle
is not constant — and then two honest ways to answer it, a table of
every seam in the dome, and the third option that sidesteps the whole
question. It is short, because once the fact is accepted the answers
are small. The week was spent on the accepting.

## The fold angle is not constant

Say it early, because everything after depends on it: **the angle at
which two panels meet is not the same everywhere on the dome.**

It cannot be. A dome is a sphere approximated by flat triangles, and a
sphere curves differently in different places. The panels around the
five-fold points of the underlying icosahedron meet at one angle; the
panels along the belt between them meet at another. A 2V hemisphere has
exactly two fold angles — {{seam.fold_a_deg}} degrees and
{{seam.fold_b_deg}} degrees in this build — and that is the good news
hidden inside the bad one. Not forty angles. Not a continuum.
{{seam.distinct_angles}}. The bad news is that {{seam.distinct_angles}}
is not one, and a key cut to one of them will not seat in the other.

The schedule on the next pages counts them: {{seam.count_a}} seams at
the tighter angle, {{seam.count_b}} at the wider, {{frame.seams}} in
all. The difference between the two — under five degrees — is small
enough that every instinct says to ignore it, and large enough that
forcing it closed puts the frame in permanent tension, the keys in
permanent shear, and the builder in the position the frankendome
already visited. The honest answers accept the difference and spend a
little labour on it. The dishonest one — "it is nearly the same" —
costs the dome.

And here is the theorem that makes the method's peace with it, because
it deserves the name: the two fold angles and the two leftover gap
angles each sum to exactly the sector the tree was split into —
{{seam.sector_angle_deg}} degrees. The gap the key fills beside a
{{seam.fold_a_deg}}-degree fold is the rest of {{seam.sector_angle_deg}};
beside a {{seam.fold_b_deg}}-degree fold it is the rest again. The
sector you split out of the tree is, exactly, the seam budget the dome
needs. Nothing in the method was tuned to make that true; it falls out
of the two geometries and it is why the key problem has an answer at
all.

## Raw trapezoid, or shaved flat

Two honest ways to make the key fit the two folds, and the book prices
both.

**The raw trapezoid.** Leave the split faces of the members exactly as
the saw left them — each sits {{seam.half_sector_deg}} degrees off its
member's centreline — and cut the key to fill the V they make. Cut the
seam across and the two sawn faces stand {{key.gap_deg}} degrees apart,
with the members' points as the innermost wood and the key lying in the
space between them and the meeting line of the two bark faces: a taper
whose base is {{key.base_in}} inches across, at the inside, and whose tip
reaches the apex at the outside. It bears {{key.contact_in}} inches along
the seam. The cost is a key that is not one part but two — one profile
per fold angle — and a stock pile sorted by profile. The gain is that the
member is never touched by a plane, and every piece of the joint stays
exactly what the saw made. The figure below is that section, cut out of
the solver's own meshes.

**The shaved flat.** Plane a narrow land along each member's two sawn
faces until they sit parallel to the seam, then one flat key fits
everywhere — {{key.flat_width_in}} inches across as the solver models it,
one key for all {{frame.seams}} seams. The cost is planing —
{{seam.shave_deep_in}} inches at the deepest, which is
{{seam.shave_pct_of_depth}} per cent of the member's depth, over a land
only as wide as the key's bearing — and the labour of it, which Chapter
{{ch.connector}} works through completely, because the number is smaller
than the instinct expects and "smaller than expected" is exactly the claim
this book verifies before it repeats.

Both answers are correct; they are two ways to spend the same small
labour, and the figure shows both sections side by side so the choice is a
comparison rather than a preference. The book's build uses the shaved-flat
answer, because one key everywhere is one less way for the pile to be
sorted wrong, and because a planed land gives the key a true bearing. The
tapered key remains the answer for a builder with no plane and no patience
for one.

![One seam, closed two ways: the tapered key and the shaved flat, both cut from the solver's meshes.](../../deliverables/book/figures/seam-both-ways.png)

## One seam, both ways

The drawing shows the same seam twice. On the left, the raw split
faces and the tapered key between them — the key's two edges cut to
different slopes, each matching the face it bears on. On the right,
the same two members with a narrow land planed flat on each, and one
parallel-sided key dropped in the gap, the same key that fits every
other seam in the dome.

The drawing is the decision, and the decision is smaller than it looks.
The tapered key moves the work into the key stock — two profiles,
sorted and matched. The shaved land moves the work into the members —
one profile, one plane setup, repeated at every seam. Either way the
work exists; the book simply chooses to pay it where the sorting
cannot go wrong. Chapter {{ch.jig_reference}} shows the fixture that
makes the shaved land repeatable, and the seam schedule below shows
the two angles it is compensating for.

## Every seam in the dome

The table is the whole seam budget on one page: all {{frame.seams}}
seams, their fold angles sorted, the two extremes named, and the key
profile each one takes. It is generated from the solved dome, not
surveyed from the build, so it is the plan the frame was drawn to —
and the plan the build should be checked against.

Read it as a work order rather than a curiosity. {{seam.count_a}} of
one profile, {{seam.count_b}} of the other, and the check that closes
the chapter: when the last panel is in, the number of keys placed
should equal {{frame.seams}}, the number of profiles used should equal
{{seam.distinct_angles}}, and the dome should close without being
forced anywhere. If any of those checks fails, the frame is not the
frame this book drew, and Chapter {{ch.where_error_goes}} is where
the book tells you where the error went.

## Hose, key or nothing

The third option, and the one that ends the chapter, because sometimes
the honest answer to an angle is a material that does not care about
it.

**The compressible seam.** A gasket — rubber, foam, a length of hose
— fills the gap by deforming instead of by matching. It absorbs the
fold difference, the drying movement, and the build's own tolerance in
one object, and it seals while it does it. What it cannot do is carry
structural load the way a timber key can, which is why the frame's
seams are built with a timber key *plus* the gasket where the shell
must be weathertight — the key locates the geometry, the gasket seals
the gap, and neither is asked to do the other's job.

**And the honest nothing.** The frame, left bare, closes without any
key at all: the butt ends bear directly on the sawn faces, and the
seam is a gap the shell chapters will have to deal with. It is not a
building; it is a stage of one. But it is a legitimate stage, and
building the frame bare first — checking the fold schedule against the
real sticks before any key stock is cut — is the cheapest way to find
the error the table above was designed to prevent.

The key, then, is the method in miniature: a small part, cut to the
two numbers the geometry actually produces, repeated until the pile is
gone, and checked against the count when the dome closes. The least
glamorous chapter in the book. The one that decides whether it
closes.
