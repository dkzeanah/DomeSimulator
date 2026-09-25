---
chapter: 12
title: Nothing Meets at the Corner
strand: explain
status: draft
target: 1290
updated: 2026-09-25
---

# 12. Nothing Meets at the Corner

In a classical geodesic frame, five or six struts arrive at a point and
something has to hold them there. That something is a hub, and hubs are why
most people give up on domes.

This frame has no hubs, because nothing arrives at the point.

![Five triangles meeting, and an empty corner.](vertex-five.png)

## The pinwheel

Each panel is built complete before it goes anywhere near its neighbours:
three members, closed into their own triangle.

Inside that triangle, each member's end butts into the **side** of the next
one, a little way along from the corner. Not into its end. Into its face. The
three of them chase each other round the triangle, which is why it is called a
pinwheel, and the mathematical vertex in the middle of that arrangement has
nothing in it at all.

Three consequences, and they are the argument for the whole method:

**No hub.** There is nothing to buy, machine or get wrong.

**Flat sawn face on flat sawn face.** A split wedge already has two flat
faces at a known angle. The joint presses one against another. Nothing is
mitred to meet at a point.

**The corner is empty, so the corner cannot be crowded.** The failure mode of
a hubbed dome — five struts whose ends all want the same cubic inch — does
not exist here.

## What is actually at a seam

Where two panels meet there are **two** members, one belonging to each, with
the key between them.

![A seam in cross-section, at the angle the solver puts it: two sectors, the key between them, drawn to the solved dihedral.](seam-section.png)

That picture is a real cut. A plane through the seam, perpendicular to its own
run, intersected with the solver's own geometry — not a diagram of the idea.
Two {{cut.sector}}-degree sectors, points inward, and the
{{seam.gap_a}} degrees of sector angle they cannot close between them.

The key fills that. It is {{seam.key_a}} inches across its base on an A seam
and {{seam.key_b}} on a B, and it is not a manufactured part

![The gasket does the shaving: the part of the joint that is not made of wood.](plate-gasket.png): it is the
truncated point of another raw sector, cut from the same log at the same
angle.

## The price of a panel being a thing

{{dome.panels}} panels times three members is {{dome.members}}. The shell has
only {{dome.edges}} edges.

So {{dome.seams}} members exist twice over, once for each panel meeting there.
That is nearly twice the timber a shared-strut frame would use.

It is not lumber somebody forgot to remove. It is the price of a panel being
an **object** rather than a position in an assembly — and what you buy with it
is everything in Chapter {{ch.jig}}: a panel you can build flat, check flat,
carry, sheathe and lift as a finished thing, on a bench, before anything is
standing.

Two trees instead of one and a half, against forty panels you can make
indoors in winter. That has been an easy trade every time I have had to make
it.

## Where the error goes

Chapter {{ch.lumpy}} claimed the frame absorbs error. This is the mechanism.

A member that is a bit long, a bit short, or at a bit of an angle changes the
width of the gap at its seam. The gap already has a key in it. A key is a
wedge, and a wedge accommodates a range of gaps by sitting a little deeper or
a little shallower.

So the error does not accumulate around the triangle and it does not
propagate into the neighbours. It lands in a joint that was always going to
be filled, and it changes how far in the filling goes.

This is also why the head end of every member is left long and cut in place —
Chapter {{ch.jig}} again. There is exactly one end of one stick where error is
allowed to leave the building as offcut, and the method spends it deliberately.

## What the butt cut actually is

One correction, because this project published the wrong version of it and
some of that is still out there.

The butt is a **compound** cut. It has a bevel and a mitre.

The bevel is constant at {{cut.bevel}} degrees — half the sector angle —
because it comes from how the log was split rather than from where the member
sits in the dome. The mitre takes {{cut.mitres}} values across all
{{dome.members}} members.

So the honest claim is not "no compound angles". It is **three saw settings
for a hundred and twenty members**, which is a better claim anyway, and true.

What the pinwheel removes is the shared vertex. It does not remove the mitre.

![Six ways to join the same sticks. This book uses the second.](plate-six-joints.png)
