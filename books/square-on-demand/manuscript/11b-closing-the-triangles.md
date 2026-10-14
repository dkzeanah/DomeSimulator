# Closing the Triangles

A frame of triangles is not yet a building: something has to close each
triangle. Wedges can do it, and how much wood that takes is set by one choice
the builder makes at the bench.

For the shared {{wm.long_in}} inch nominal chord reference, the frame has
{{wm.members}} members: {{wm.nominal_frame_ft}} wedge feet on the drawing,
{{wm.finished_frame_ft}} feet of solver cut-stock, and
{{wm.gross_frame_ft}} feet reserved as uncut blanks. These are three ledgers.
Its {{wm.isosceles_panels}} isosceles and {{wm.equilateral_panels}} equilateral
triangles leave an estimated {{wm.opening_sqft}} square feet to close for a
{{wm.log_in}} inch log split {{wm.splits}} ways. The half-chord-width frame
inset is a planning assumption.

## Pairs and the coverage assumption

The owner's inward-pointing pair idea is worth testing. Its timber budget
requires the installed continuous face pitch, counting both wedges in each
pair. The provisional model assumes pitch equals *(two minus overlap)* times
the wedge chord. Under that assumption:

- the widest assumed pitch needs {{wm.least_infill_ft}} wedge feet;
- the narrowest assumed pitch needs {{wm.most_infill_ft}} wedge feet.

Reserve the gross frame blanks first: {{wm.frame_trunk_ft}} trunk feet.
Add the conditional infill and the total is {{wm.least_raw_trunk_ft}} to
{{wm.most_raw_trunk_ft}} usable trunk feet, or {{wm.least_trees}} to
{{wm.most_trees}} whole equivalents of a uniform {{wm.trunk_ft}} foot trunk.
This excludes taper, kerf, defects, joints, seals and course offcuts.

## What the dial is for

Sliding unchanged wedges changes contact and cavities, not their timber area.
The ideal opposed-point chord-triangle experiment can have a half-void cell;
that does not establish continuous face coverage. Opposed points, the tool's
alternating-point flip-flop, and both points inward are different layouts.
Neither nesting nor a cavity establishes load capacity, insulation performance
or weather-tightness. Measure the chosen profile and test its joints before
using the budget as a cut list. The Complete Edition's Every Piece, Numbered
chapter and `infill.methodology` carry the shared derivation.
