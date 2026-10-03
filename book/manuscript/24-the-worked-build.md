---
chapter: 24
title: The Worked Build
strand: reference
target: 1100
status: drafting
updated: 2026-09-17
---

# 24. The Worked Build

*Every number for this book's dome, in one place*

## The Worked Build

This chapter is the whole build on five pages: the tree, the dome it
makes, the cut list, the seam schedule, and the frame they describe. A
builder who wants to work from nothing else can work from this chapter
alone — every number in it comes from the same solved model the rest
of the book quotes, and the chapter exists so that the numbers have one
place to live where they cannot contradict each other.

The two sizing methods of Chapters {{ch.method_a}} and {{ch.method_b}}
converge here. Method A says: pick the floor, and the arithmetic hands
back the tree. Method B says: measure the tree, and the arithmetic
hands back the dome. The worked build is Method B run to the end on the
tree of Chapter {{ch.the_tree_that_was_already_down}} — the windfall,
measured, bucked, split, and solved into the frame whose numbers follow.

Nothing on these pages was chosen for the pages. It was computed, and
the computation is the same one the films and the simulator run, so
the book, the film and the model cannot disagree about the dome.

## The tree

The input, measured before any cutting: {{tree.butt_diameter_in}}
inches at the butt, {{tree.top_diameter_in}} at the top,
{{tree.usable_length_ft}} feet of usable trunk, bucked into
{{tree.sections}} sections of {{tree.section_length_ft}} feet, each
section split into {{tree.sectors}} wedges. One tree yields
{{tree.struts_per_tree}} struts; {{dome.trees}} trees yield
{{dome.struts_available}}, against a frame that needs
{{frame.members}}. The recovery arithmetic — {{tree.solid_bf}} board
feet in, {{tree.wedge_bf}} out, {{tree.recovery_pct}} per cent kept —
is Chapter {{ch.recovery}} in full; here it is only the row that
feeds the rest of the chapter.

![This book's tree.](../../deliverables/book/figures/worked-tree.png)

## The dome

The output: the solved hemisphere that {{dome.trees}} trees of this
taper will fill. {{dome.diameter_ft}} feet across, {{dome.height_ft}}
feet to the crown, {{dome.floor_sqft}} square feet of floor. The
longest member is {{dome.longest_member_in}} inches; the shortest
{{dome.shortest_member_in}}; the whole frame stands on
{{dome.timber_ft}} feet of timber. The strict count says the frame
actually consumes {{dome.trees_strictly_needed}} trees, and the book
says the rest of the pile is spares, blocking, floor stock and
firewood rather than
pretending the arithmetic is tidier than it is.

![The dome that results.](../../deliverables/book/figures/worked-dome.png)

## The cut list

All {{frame.members}} members, by class, length and count, straight
from the pinwheel layout. {{dome.member_lengths}} distinct lengths
cover the whole frame — the two edge classes of Chapter
{{ch.two_lengths_not_forty}}, split into four by the pinwheel's inset
of Chapter {{ch.pinwheel}}. The table is the jig's job description:
every stick that crosses the bench is one of these rows, and nothing
else.

Beside it sits the shorter list the build actually came out with — **the
master cut list**, {{cut.master_count}} resultant lengths:
**{{cut.master_long_in}} inches**, **{{cut.master_mid_in}}** and
**{{cut.master_short_in}}**. Resultant means *finished*: cut a member to
one of these and the panel it goes into is the size the dome wants, with
nothing left over to trim. Every equilateral panel takes three of the long
member. Every isosceles panel takes the long member as its base, the middle
length on the left and the short one on the right.

That orientation is a bench rule rather than a preference, and the shape
shows why. Lay an isosceles panel with its base nearest you and the
{{cut.master_mid_in}}-inch left member is the longer of the two sides: it
reaches over to the top point, which sits off the middle of the base
because the two sides are not equal. The {{cut.master_short_in}}-inch right
side runs up to meet it, and it is that shortest member the base butts up
to — the base's end lands on the side of the short one, which is the
pinwheel's chase closing the triangle. Build a panel with the two sides
swapped and it does not close: two inches over five feet is not something
the eye catches, so the sides are picked from their two marked stacks, in
order, every time.

The two lists differ, and the book prints both rather than picking one.
The table above is the pinwheel model's seated schedule, which represents
the inset as a fourth length; the master list is what the saw cut and what
the panels measured when they closed. The model is a model of the joint;
the master list is a report of the build, and where the two disagree, the
tape on the finished panel is the authority.

![The master cut list, and which side it goes on.](../../deliverables/book/figures/master-cutlist.png)

![The full cut list.](../../deliverables/book/figures/worked-cutlist.png)

## The seam schedule

Every seam, its fold angle and its key: {{seam.count_a}} at
{{seam.fold_a_deg}} degrees, {{seam.count_b}} at {{seam.fold_b_deg}},
{{frame.seams}} in all, the two profiles of Chapter {{ch.seams}}.
The schedule is generated from the solved dome, so the build's check
is simple: keys placed equals {{frame.seams}}, profiles used equals
{{seam.distinct_angles}}, and the dome closes without being forced.

![The seam schedule.](../../deliverables/book/figures/worked-seams.png)

## The dome this describes

The frame itself — the simulator's own solved meshes, in the book's
print palette, exactly the dome the four tables specify. If the
chapter above is the arithmetic, this page is what the arithmetic is
*of*: {{frame.panels}} panels, {{frame.members}} members,
{{frame.seams}} seams, {{dome.diameter_ft}} feet across, standing.

![{{dome.diameter_ft}} feet across, {{dome.floor_sqft}} square feet of floor.](../../deliverables/book/figures/worked-render.png)
