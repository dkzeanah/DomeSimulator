---
chapter: 10
title: Compression, Tension, and One Eighth of a Tree
strand: explain
status: drafting
target: 3000
updated: 2026-09-17
---

# 10. Compression, Tension, and One Eighth of a Tree

*What a wedge strut can actually carry*

## One Eighth of a Tree

The last three chapters built the case for the wedge as a shape: a
triangulated frame loads its members along their length, and along their
length all that matters is how much wood is in the section. This chapter
turns the case into numbers — and then, because a book is not an engineer,
hands the rest of the question to one.

The unit of the whole method is one eighth of a tree: a {{tree.sector_angle_deg}}-degree
sector of the trunk, {{member.width_in}} inches across its bark face,
{{member.depth_in}} inches from pith to bark, {{member.area_in2}} square
inches of wood. That stick will be pushed and pulled along its grain for
the life of the building, and its ends will press sideways into the sides
of its neighbours. Those are the two load directions this chapter cares
about — along the grain, and across it at the joint — and they behave so
differently that the entire honesty of the method depends on keeping them
apart.

The chapter ends with the one number the book will actually give you, and
the reason it will not give you the number you probably wanted. The two are
related: the book can compute geometry, and geometry is what a wedge's
bearing area is. What a wedge's wood can *take* is a property of your
tree's species, grade and moisture, and any book that prints that number
for you is guessing about your tree while pretending to know it. This one
does not.

## Along the grain, and across it

Wood is not one material. It is two, depending on direction, and the
difference is roughly an order of magnitude.

**Along the grain** — end to end, the direction the tree grew — wood is
the material engineers mean when they say pine is strong. A stick squeezed
along its length carries load through the fibres themselves, every one of
them sharing. A stick pulled along its length is even stronger: the fibres
take tension along their length the way rope does. This is the direction a
triangulated frame uses, which is why Chapter {{ch.triangles}} could say
that shape does not matter and mean it: for push and pull along the
member, the section's area is the count that matters, and the wedge has
{{member.area_in2}} square inches of it.

**Across the grain** — sideways, pressing into the flat of the wood — the
same stick is a different material. Load the side of a pine stick and the
fibres are asked to squash between their neighbours; they yield far
sooner, they dent rather than break, and the load the joint may carry is a
fraction of what the same member carries along its length. Every wooden
building lives with this fact; it is why a post stands on a plate instead
of a point, and why bolts through timber are spread out rather than
clustered.

The wedge frame meets the problem head-on, and the design decision is in
the next section. Here the point is the discipline: this book's claims
about what a wedge can carry are claims about the *along-grain* direction
— the direction the frame actually loads — and its numbers at the joint
are numbers about *area*, which is geometry and computable, not about
permissible pressure, which is not. The safety page further down exists
because the two are easy to swap, and swapping them is how dome books get
people hurt.

## The end-to-side bearing

The pinwheel joint's load path is worth stating precisely, because its
elegance is real and its limits are real, and both live in the same
sentence.

Every member's butt end — sawn square, once, on the jig — lands on the
flat sawn face of its neighbour. The contact patch is the end of the
stick, and the end of a sector is the sector itself: {{force.bearing_in2}}
square inches, nothing notched away, nothing reduced to a tongue or a
dowel. A conventional joint would cut away wood to make the connection and
then bolt what is left; the pinwheel does the opposite. The whole section
bears, because the whole section is what the log produced, and the joint
gets its strength from refusing to throw any of it away.

The bearing patch, stated as geometry: the butt end is a sector of a
{{force.bearing_dia_in}}-inch circle — the depth of the member, doubled —
cut at {{force.sector_angle_deg}} degrees, which is the same sector shape
the tree was split into.

![The bearing, at a seam: one member's butt on the next member's side.](../../deliverables/book/figures/force-bearing.png)

So the book's honest number for the joint is
{{force.bearing_in2}} square inches of end grain against side grain, per
member, at every interior corner. The frame has {{frame.members}} members,
each with one loaded butt, and the arithmetic ends there, because the next
number — how many pounds that patch may carry — belongs to your tree, not
to this book.

What the book *can* say, and does: the bearing is generous by the
standards of light framing, the load spreads across the full width of the
sector rather than a bolt row, and the key between the members carries
the seam's alignment while the wood carries the building. The chapter on
the pinwheel (Chapter {{ch.pinwheel}}) and the one on the connector
(Chapter {{ch.connector}}) show how that division of labour is built. This
chapter's job was the load path, and it is this: along the grain through
the members, across the grain at the butt, area the whole way.

## What this book will not tell you

This page is a warning, and it is not decorative.

This book will not tell you what your tree's wood is allowed to carry.
Allowable stresses depend on species, grade, moisture content, and the
direction of load; they come from published tables tied to specific
species grown in specific regions, and they are applied by someone who can
look at the actual timber. A pine from a plantation is not a pine from a
windbreak, a knot at a bearing face is not a knot mid-span, and green wood
carries less than dry wood while it dries. None of that can be looked up
by a book that has never seen your log.

It follows that nothing in this book is a structural sign-off. The frame
described here is a prototype method, demonstrated by a build, not an
engineered standard. Where a load figure matters — a floating dome hung
from trees, a floor hung from a mast, a roof carrying snow — the book
names the number as an engineer's job and leaves it there. Chapter
{{ch.dome_costs}} repeats this in its accounting of the costs nobody puts
in a dome book, and the corrections chapter (Chapter {{ch.corrections}})
shows what happens when this project forgot its own rule: it printed a
load-ish claim, was wrong, and said so in public.

The rule, once, plainly: **compute the geometry, check the code, and ask
an engineer about the loads.** Everything this book computes is geometry.
Everything an engineer decides is the rest.

## The number I will give you

One sidebar, one number, so the distinction above has a concrete object.

The bearing area of one butt end against one side: {{force.bearing_in2}}
square inches. That is geometry — the sector's area, computed from the
tree's own taper — and the book will stand behind it, because it is the
same arithmetic that produced the cut list, and it can be checked with a
ruler on the stick in your hand.

What that patch is *allowed* to carry, in pounds per square inch, is a
property of the species, the grade and the moisture — a table entry, not
a computation — and this book will not print one. It will tell you which
direction to look (across the grain, at the butt, at the wet case), and
it will tell you that the frame's own redundancy is the reason the method
tolerates being built from timber nobody graded: {{frame.panels}} panels
mean a member can be watched, and a member can be swapped, and Chapter
{{ch.what_broke}} shows what watching one looks like in practice.

The book gives you the geometry and the method. The engineer gives you the
stamp. Neither one can do the other's job, and this book is built so that
the boundary between them is a page you cannot miss.
