---
chapter: 9
title: Two Lengths, Not Forty
strand: explain
status: drafting
target: 2200
updated: 2026-09-17
---

# 9. Two Lengths, Not Forty

*The whole reason a dome can be built by one person*

## Two Lengths

Chapter {{ch.forty_panels_one_hundred_and_twenty_members}} counted the frame:
{{frame.panels}} panels, {{frame.members}} members, {{frame.seams}} seams.
This chapter is about the number inside that count that makes the whole
thing buildable by one person with one jig, and it is the smallest
simplification in the entire method:

**Every one of the dome's {{frame.edges}} edges comes in two lengths. Not
forty. Two.**

A room of forty different panels sounds like forty different kinds of
stick, forty different cuts, forty different chances to be wrong. The 2V
geometry quietly removes that nightmare before it starts. Because the frame
is an icosahedron subdivided exactly once, its edges inherit only two
families: the halves of the original icosahedron edges, and the new edges
that connect midpoints. Project them onto the sphere and they stretch, but
they stretch into two values, not forty. Two lengths of edge, in a fixed
ratio of {{dm.ratio}} to one — and everything else in the build method
follows from that sentence.

A two-length frame is a frame you can jig. A forty-length frame is a frame
you can only improvise, which is exactly the failure Chapter
{{ch.the_frankendome}} documented with ten days of labour. This chapter
states the two lengths, shows the four actual cut lengths that fall out of
them, and explains the surprising part: that four is not a mistake and not
a regression. Four is what the pinwheel joint does to two, and the reason
is worth its own section.

## Short and long

The two edge families have names, and the names matter because they travel
all the way to the cut list and the jig.

**Short.** The edge between two midpoints — the new edge the subdivision
created. It spans a smaller arc of the sphere, {{dm.short_arc}} degrees,
and its length is {{dm.short_factor}} times the sphere's radius.

**Long.** Half of an original icosahedron edge — the older edge, spanning
{{dm.long_arc}} degrees, {{dm.long_factor}} times the radius.

Those two factors are not something a designer chose to keep the saw
settings down. They fall out of the icosahedron's coordinates, and four
independent routes — straight coordinates, central angles, the law of
cosines, and a measured drawing — all land on the same pair, which is the
book's idea of proof for a number this important. At this book's dome, the
two lengths are {{dome.longest_member_in}} inches and
{{dome.shortest_member_in}} inches before the joint takes its bite: a
difference of less than a foot across the whole frame.

The triangle shapes follow the same logic. The hemisphere contains
{{dm.equi_count}} equilateral triangles — three long edges, sitting around
the five-fold points — and {{dm.iso_count}} isosceles ones, two long edges
over a short base. Two triangle shapes, two edge lengths, one dome. The
forty panels of the previous chapter are forty *copies* of two designs,
not forty designs.

![Every stick in the dome, in four lengths.](../../deliverables/book/figures/member-classes.png)

## The member schedule

The table is the bridge from geometry to lumberyard, and it is generated,
not remembered: every row comes out of the same solved frame the
simulator builds, so the table and the dome cannot disagree.

The headline is the first column of it: the whole frame reduces to
{{dome.member_lengths}} cut lengths. The longest member is
{{dome.longest_member_in}} inches; the shortest {{dome.shortest_member_in}}.
Between them sit the other two, and the spread across all four is the
width of one hand. That is the entire vocabulary of the build: four
numbers on a board beside the jig, and every stick that passes through the
bench is one of them.

Why four and not two, when the frame has only two edge families? Because
the pinwheel joint insets every member from the vertex it serves, and the
inset depends on which side of the corner a member lands on. A long edge
becomes two slightly different long members — one for each side of the
triangle it borders — and the same for short. The table prints all four,
with their counts, because a cut list that hides the difference produces
forty panels that almost fit, which is the most expensive kind of fit
there is. Chapter {{ch.pinwheel}} is the joint's geometry in full; here
the point is only that two became four *for a reason*, and the reason is
printed.

That four-length schedule is what the model prints. What the members
*measure* — the master cut list, {{cut.master_count}} resultant lengths
that make a panel the right size once it is together — is shorter:
{{cut.master_long_in}}, {{cut.master_mid_in}} and
{{cut.master_short_in}} inches. The equilateral panels take three of the
long member; the isosceles panels take the long at the base, the middle on
the left and the short on the right. The build's list is the measured one
and the model's is the approximation, and Chapter {{ch.worked_build}}
prints both side by side rather than quietly picking one — a builder needs
the master list at the saw and the seating schedule at the bench.

## Why the pinwheel splits two into four

The step from two lengths to four is the one place a sceptical reader
should slow down, because it looks like the dome is quietly getting more
complicated, and the honest answer is that it is — by design, and the
design buys more than it costs.

A hub dome cuts every strut to end at the vertex, so two edge families
really do mean two stick lengths, and the saw never needs a third setting.
The price is the hub itself: a machined connector at every corner, drilled
to a tolerance, bolted to the end of every strut, and — as Chapter
{{ch.the_v_bracket_afternoon}} recorded — useless the moment the sticks
stop being factory-identical.

The pinwheel throws the hub away by making every member end land on the
*side* of the next member instead of at the corner. That single decision
is what lets rough, split, slightly irregular timber frame a dome at all:
a butt end on a flat sawn face does not need the precision a hub demands.
But it has a geometric consequence, because a member that stops short of
the corner stops at a different distance on each side of the triangle. A
long edge needs a long-left and a long-right; a short edge needs a
short-left and a short-right. Two becomes four.

So the honest ledger reads: the pinwheel costs one extra saw setting per
edge family, and in exchange it deletes the hub, the mitre on every end,
and the requirement that rough timber behave like milled stock. Four cut
lengths instead of two is not the dome getting complicated. It is the
entire bill for the joint that makes the method possible — and it is a
bill paid once, on a jig, where a fence and a stop make the four lengths
as repeatable as two. The next chapter spends that simplicity on the
question of what a stick of this shape can actually carry.
