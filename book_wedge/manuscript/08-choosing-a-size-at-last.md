---
chapter: 8
title: Choosing a Size, At Last
strand: howto
status: draft
target: 880
updated: 2026-09-25
---

# 8. Choosing a Size, At Last

Everything up to here has been ratios. Nothing has had a unit on it.

That is deliberate: the geometry is scale-free, so it is worth solving once
and then choosing a size — rather than choosing a size and re-solving the
geometry inside it, which is how most people do it and is why most people only
ever build one dome.

![The push that makes it geodesic.](plate-project.png)

## One number does it

Pick any one of these and the rest follow:

* the radius
* the long member's chord
* the diameter
* the apex height (which is the radius)
* the floor area

They are all the same number wearing different units. Multiply the radius by
{{cut.a_factor}} and you have the long chord; by {{cut.b_factor}} and you have
the short one; everything else is those two and the counts from Chapter
{{ch.hemisphere}}.

## This book picks the stick

The reference build is sized from the **member**, not from the floor plan.

{{cut.a_chord}} inches — six feet — because:

* it is what comes comfortably out of a twelve-foot log section, with the
  crosscut in the middle;
* it is what one person carries without thinking about it;
* it fits in a pickup bed, diagonally, with the tailgate up.

The dome that falls out of that is {{dome.diameter_ft}} feet across with
{{dome.floor_sqft}} square feet of floor. **The diameter is the answer to the
member, not the other way round.**

That is backwards from how buildings are normally sized and it is the right
way round for a method whose whole argument is about what one person can make
and move.

## What it costs to size from the member

One real inconvenience, stated plainly.

No panel fits a four-foot sheet. The narrowest face is {{seam.narrowest}}
inches across its shortest altitude and a sheet is 48. Every panel of the
reference build needs a seam in its sheathing or a wider sheet.

That is a direct consequence of sizing from the stick, and anybody who would
rather have the sheets than the six-foot member should build a different
diameter. Chapter {{ch.two_lengths}}'s table will give them one.

## If you would rather size from the floor

Work backwards.

Floor area for a decagon inscribed in a circle of radius R is
5·R²·sin(36°), so a target floor of A square feet wants

    R  =  sqrt( A / (5 · sin 36°) )

and then the long chord is {{cut.a_factor}} R and the cut is that minus
{{cut.a_bite}} inches. A 400-square-foot floor wants a radius of about 11.7
feet and a long member a shade over seven feet — which is past comfortable
one-person handling, which is the trade.

## Five sizes worth knowing

The reference designs, from a demonstration you build to get it wrong on, up
to the point where a 2V starts to strain. Each one is a full cut list in the
tables at the back, and each one is the same {{dome.members}} members and the
same nine processes.

The only thing that changes between them is two numbers.
