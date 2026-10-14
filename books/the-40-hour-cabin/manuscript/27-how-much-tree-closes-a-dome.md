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

The arithmetic was first worked out by the owner with ChatGPT, in a long
session of questions and answers. This book does not take it on trust: every
figure in it was worked out again from the dome solver's own geometry, and
{{cov.checked}} of the session's stated figures agree with the solver. Where
the solver knows something the session could not, both numbers are here.

## The frame

```text
{{cov.frame_steps}}
```

Two things the session's sum leaves out, both in the dome's favour and both
small. The members are cut shorter than the lines on the drawing, because each
one stops against its neighbour at the pinwheel: {{cov.frame_saving_ft}} feet
less wood than the nominal {{cov.frame_nominal_ft}}. And the
{{cov.unique_edges}} unique edges become {{cov.members}} members because every
panel owns its three sides -- the wedge method's rule that every panel keeps
its own edge.

## The faces

The dome's {{cov.iso_faces}} isosceles and {{cov.eq_faces}} equilateral
triangles cover {{cov.area}} square feet. Not all of that is open: the frame's
own wedges sit inside every edge. Take a strip half a wedge face wide off the
inside of each edge and what is left to close, with a {{cov.solver_log_in}}-inch
log's wedges or a 12-inch log's, is the open area. For a 12-inch log split
eight ways -- a face {{cov.face_in}} inches wide, {{cov.depth_in}} deep -- it
is {{cov.open_area}} square feet.

## Pairs, points in

The triangle is closed with wedges laid in pairs, their points facing in.
Slide the two along their slants and the pair changes shape without changing
its wood:

- **nested**, slant against slant, the pair is a solid parallelogram and
  covers one wedge face;
- **opened to a bowtie**, touching only at the points, it covers two faces --
  and is half air.

Between the two, a pair covers *(2 minus the overlap)* faces. That one number,
the overlap, is a dial on the whole dome's timber bill:

```text
{{cov.table}}
```

So the dome, frame and infill, is {{cov.total_min_ft}} to {{cov.total_max_ft}}
feet of wedge, or {{cov.trees_min}} to {{cov.trees_max}} sixty-foot pines of
twelve inches -- {{cov.trunk_min_ft}} to {{cov.trunk_max_ft}} feet of trunk,
of which {{cov.frame_trunk_ft}} is the frame.

:::box against "What these numbers do not say"
The bowtie end is a floor, not a joint: points touching points do not keep
weather out, so a real panel needs some overlap and sits above the least
figure. The area method also runs about {{cov.calc_excess}} per cent above the
real pieces the Triangle Infill calculator cuts for a panel, because the
triangle's corners take short pieces. And a pine tapers: twelve inches does
not hold for sixty feet. With the simulator's own {{cov.solver_log_in}}-inch
log the same dome takes {{cov.solver_min}} to {{cov.solver_max}} feet -- up to
{{cov.solver_trees_max}} trees. Size the log first; it moves the answer more
than anything else.
:::

## What the overlap is for

The overlap is not only a timber setting. Nested pairs are solid wood, the
most contact and the least air. Opened pairs leave a cavity inside the panel --
room for insulation, a channel, air. A builder can nest tight near the corners
where loads gather and open the pairs across the middle of a panel where a
cavity is worth having. The session's last answer put it well: the overlap can
be a design variable rather than a fixed joint.
