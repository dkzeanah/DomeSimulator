---
section: back
title: The Master Tables
status: draft
target: 800
updated: 2026-09-17
---
# The Master Tables

Four tables carry the whole build, and they are the ones to come back to at
the saw. Every number in them is generated at build time by the same solver
that drew the 3-D model, so a table and a drawing can never disagree. Print
these pages and take them to the bench.

## Full cut list

![The complete cut list.](../../../deliverables/book/figures/back-cutlist.png)

The whole frame in one table: every member, by class, length and count. The
frame has {{frame.members}} members in {{dome.member_lengths}} distinct
lengths -- two classes, short and long, each cut once per panel. The table
is sorted the way the work is sorted: by class first, then by length, so a
member on the pile can be found from the table in one look. Mark each class
with its own colour at the saw, and keep the classes in separate stacks; the
raise is where a mixed pile turns into a slow afternoon.

## Full seam schedule

![The complete seam schedule.](../../../deliverables/book/figures/back-seams.png)

Every seam in the frame, with its fold angle and its key. The frame's
{{frame.seams}} seams fold at only two angles -- {{seam.fold_a_deg}} degrees,
{{seam.count_a}} of them, and {{seam.fold_b_deg}} degrees, {{seam.count_b}}
of them -- so the brake is set twice and the schedule is how you know which
setting a given seam wants. The key column is the gasket: {{jig.gasket_in}}
inches of compressible strip in every seam, which is what lets a frame of
green timber close and stay closed while the wood moves.

## Butt cut setups

![Every distinct setup.](../../../deliverables/book/figures/back-setups.png)

Every distinct saw setup in the build, in the order the work meets them.
The butt cut is the one compound angle in the frame, and this table is the
one place its setups live: stock left long by {{jig.head_overfit_in}} inches
at the head end, allowance of {{jig.butt_allowance_in}} inches past the cut,
and the angle itself. The rule from the cutting chapters applies here in
table form: the angle lives in the tool, not in the operator. Set the jig
once per row, run every member of that row, and never measure an angle at
the saw.

## Declared constants

![Declared inputs.](../../../deliverables/book/figures/back-constants.png)

The inputs the whole book is built on, repeated here for reference. These
are the numbers that are *declared* rather than derived -- the gasket
thickness, the handling limit, the prices and rates that could not be
computed from geometry because they are facts about the world. Every one
of them is stated with its reason where it is used, and this table collects
them so a reader can change one and see what moves. That is the promise the
front of this book makes and the arithmetic of this book keeps: no number
is typed into a sentence. Change a constant here and every figure that
depends on it -- in the chapters, in the films, in the 3-D model -- changes
with it.
