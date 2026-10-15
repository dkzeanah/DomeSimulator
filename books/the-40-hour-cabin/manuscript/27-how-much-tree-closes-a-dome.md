---
chapter: 27
title: How Much Tree Closes a Dome
strand: explain
status: draft
target: 2000
updated: 2026-10-14
---

# 27. How Much Tree Closes a Dome

The frame is not the whole of the wood. A frame of triangles keeps the weather
out of nothing; something has to close each triangle. This chapter counts what
it takes to close all of them with more wedges -- the same wedges the frame is
made of, laid in pairs -- and what that means in trees.

The arithmetic began in the owner's conversation with ChatGPT. The shared
`infill.methodology` now recomputes the geometry and labels the estimates.
Agreement with a rounded answer checks arithmetic; it does not validate an
installed facing, a structural joint, or a weather seal.

## The frame

The reference has a {{wm.long_in}} inch nominal long chord and a
{{wm.short_in}} inch short chord, with {{wm.members}} panel-owned members
and {{wm.shared_edges}} shared geometric edges.

Keep three totals separate: {{wm.nominal_frame_ft}} wedge feet of nominal
edges, {{wm.finished_frame_ft}} feet of solver cut-stock, and
{{wm.gross_frame_ft}} feet in uncut {{wm.blank_in}} inch blanks. The last
figure reserves {{wm.frame_trunk_ft}} usable trunk feet before any infill.
Shortening a member at its pinwheel does not recover the entire blank as
uncommitted stock. Each panel owns its three sticks; shared edges are not
the number of members to cut.

## The faces

The {{wm.isosceles_panels}} isosceles and {{wm.equilateral_panels}}
equilateral triangles cover {{wm.area_sqft}} square feet. Assume an inward
strip half a wedge chord wide on every edge. A {{wm.log_in}} inch log split
{{wm.splits}} ways gives a {{wm.chord_in}} inch chord, leaving an estimated
{{wm.opening_sqft}} square feet. This inset estimate differs from the infill
tool's actual solved opening and must be labelled accordingly.

## Pairs, points in: a coverage hypothesis

The owner's proposal closes triangles with inward-pointing paired wedges.
Before budgeting that arrangement, measure its continuous installed face
pitch. Both pieces count: wedge footage equals twice the open area divided
by pair pitch, with inches converted to feet.

For planning only, assume pitch is *(two minus overlap)* times the chord.
That gives this conditional table; it does not follow from the bowtie's span.

{{wm.pair_table}}

The one-face infill estimate is {{wm.least_infill_ft}} to
{{wm.most_infill_ft}} wedge feet. Divide it by {{wm.splits}} and add the
gross frame reserve first: {{wm.least_raw_trunk_ft}} to
{{wm.most_raw_trunk_ft}} trunk feet, or {{wm.least_trees}} to
{{wm.most_trees}} whole uniform {{wm.trunk_ft}} foot trunk equivalents.

:::box against "What these numbers do not say"
The quantities exclude kerf, taper, knots, defects, seals, course offcuts,
packing losses and a second face. A uniform trunk equivalent is not a
harvesting promise. The calculator's flip-flop layout has its own scale,
opening and physical pieces; its measured pitch can check an area estimate
for that layout, but cannot validate a different inward-pointing pair.
:::

## Two layouts, two counts

The figures above divide the open area by *(2 minus the overlap)* times the
wedge's **face** width. That fits one layout: faces out in the panel's
surface, points turned in, each wedge covering its own face. It is the
methodology's labelled planning assumption, not a mistake.

The pairs in *Closing the Triangle* sit the other way. Their points face each
other down the triangle, so each pair's faces bear on the next pair's and the
slants are what shows. In that layout what a pair reaches downward is set by
the wedge's **depth** -- {{fill.depth_in}} inches against a face of
{{fill.face_in}} -- and counting it means laying every pair, course by course
from each triangle's top corner, each wedge as long as the triangle is wide
where it lies, with one more pair to close the strip at the base. One
isosceles triangle takes {{fill.iso_nested}} pairs nested,
{{fill.iso_bowtie}} as bowties. The whole dome, with the frame counted as
{{wm.members}} full {{wm.blank_in}} inch blanks:

```text
nested:  {{fill.nested_wedges}} wedges, {{fill.nested_ft}} ft of infill; {{fill.nested_total}} ft with the frame, {{fill.nested_trees}} pines
bowtie:  {{fill.bowtie_wedges}} wedges, {{fill.bowtie_ft}} ft of infill; {{fill.bowtie_total}} ft with the frame, {{fill.bowtie_trees}} pines
```

Against the faces-out count the laid one lands close at the nested end and
higher at the bowtie end. Both are ideal counts: no kerf, taper or course-end
waste, and a bowtie that touches only at its points closes the opening along a
line, which proves neither a seal nor strength. Pick the layout, build a
sample, and measure it before either number becomes a cut list.

## The whole dome, every way

Counting one triangle is not seeing a dome. *Closing the Triangle* fills all
{{idome.panels}} triangles of the Triangle Infill tool's dome
({{idome.across_ft}} feet across) and shows it finished, every piece cut to
the opening's walls and planed flush with the {{idome.thick_in}} inch frame.
Planing a nested pair flush takes {{idome.planed_nested}} of its wood; a
bowtie loses {{idome.planed_bowtie}}. Then the same dome wears every other
way the tool knows to fill or cover a triangle with eighth-log wedges --
{{idome.ways}} in all, counted from the pieces themselves:

{{idome.table}}

Nothing shows through any of them. *Solid* is how much of the frame's
thickness is wood; *left open* is the plug each ring pattern leaves at a
triangle's centre, cut separately. This is a bigger dome than the reference
above -- 72 inches is its longest finished member, not its chord -- so its
feet are not the reference's feet.

## What the overlap is for

Overlap can be a design variable: sliding unchanged wedges changes contact
and cavities without changing their wood area. The separate ideal
opposed-point chord-triangle cell has the following envelope and void:

{{wm.section_table}}

That experiment is not a raw curved-sector joint. Opposed points, alternating
points, and both points toward the interior are different arrangements.
Contact and void alone establish neither strength, thermal performance nor
weather-tightness. Measure the selected profile, test its joints, then replace
the pitch assumption with installed coverage. Every Piece, Numbered revisits
the stock ledgers and the pentagon's complementary cuts in Chapter
{{ch.everypiece}}.
