---
chapter: 25
title: If Your Sticks Are Rectangles
strand: howto
status: draft
target: 1940
updated: 2026-10-03
---

# 25. If Your Sticks Are Rectangles

<!-- concept: build/hubless_cut -->
<!-- concept: cuts/two_angles -->

Everything up to here cuts split log sectors. But the hubless frame -- forty
closed triangles bolted edge to edge -- works with ordinary milled stock too, and
plenty of people will start with a stack of two-by-fours rather than a stand of
pine. This chapter is that version. Its joint is harder than the wedge's, and
seeing why is the best argument for the wedge.

Every end of a rectangular strut needs two angles at once. The saw is **swung**
to a mitre, so the strut meets its neighbour in the plane of its own triangle,
and the blade is **tilted** to a bevel, so its face lies flat against the
triangle next door. They happen on the same pass -- that is what *compound* means
-- and getting one right while the other is wrong gives you a part that looks
correct and fits nothing.

![Two angles, one pass, every end.](plate-compound-cut.png)

## Every setting the dome needs

<!-- concept: cuts/machines -->
<!-- concept: cuts/limit -->
<!-- concept: cuts/complement -->
<!-- concept: build/hubless_saw -->
<!-- concept: master/ms_math_jigs -->
<!-- concept: master/ms_jigshop -->

The audit assumes:

    {{saw.stock}}

and the whole dome reduces to **{{saw.setups}} distinct setups**:

    {{saw.settings}}

Read the right-hand column. **Not one of the mitres this dome asks for is on a
common mitre saw's scale** -- they all lie past its {{saw.max_mitre}}-degree stop.
The geometry is easy; the tool is the problem.

The way through is that a mitre and its complement are the same cut approached
from the other face. Swing to the complement instead -- the sled column above --
and turn the workpiece a quarter turn in a sled. Same joint, reachable setting.
And each machine can only make the cut the other one cannot. The table saw rips
the bevel down the strut's whole length, tilted to at most {{saw.max_tilt}}
degrees, which no mitre saw can do; the ends are crosscut on a mitre saw where its
swing reaches, and on a sled fenced to the complement where it does not. Two
triangle shapes means two
assembly jigs, and the six settings cover every end of all
{{dome.members}} struts.

## The sequence

<!-- concept: cuts/width -->
<!-- concept: cuts/mark -->
<!-- concept: cuts/tilt -->
<!-- concept: cuts/rip -->
<!-- concept: cuts/sled -->
<!-- concept: cuts/lap -->
<!-- concept: cuts/first_end -->
<!-- concept: cuts/turn -->
<!-- concept: cuts/batch -->
<!-- concept: cuts/dryfit -->

{{saw.steps}}

![The crosscut sled, fenced to the complement.](plate-the-sled.png)

## Proving it

<!-- concept: cuts/prove_tilt -->
<!-- concept: cuts/fivecut -->

Two checks, because a saw's own scale is not to be trusted.

**The tilt.** Rip two offcuts at the setting, put the cut faces together and
measure the pair. The pair doubles the error, so anything invisible on one is
obvious on two:

    {{saw.bevel_check}}

**The sled fence.** The five-cut method trims one board on all four sides and then
once more, and the last strip's taper is four times the fence's error -- so an
error far too small to see becomes one a caliper reads:

    {{saw.five_cut}}

![An invisible error, made measurable.](plate-five-cut.png)

## The five ways it goes wrong

<!-- concept: cuts/failures -->
<!-- concept: cuts/recap -->

Every one of them looks correct until assembly:

{{saw.failures}}

So the whole sequence is: two machines, one sled, {{saw.setups}} settings, and
every end of every strut batched by setting rather than by triangle. Six setting
changes instead of a change for every end -- which is the same lesson as the
wedge, arrived at the hard way. The wedge simply never asks for most of these
cuts: its bevel is the split, and its head is cut in place (Chapter {{ch.jig}}).
