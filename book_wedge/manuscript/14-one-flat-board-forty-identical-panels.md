---
chapter: 14
title: One Flat Board, Forty Identical Panels
strand: howto
status: draft
target: 2140
updated: 2026-09-25
---

# 14. One Flat Board, Forty Identical Panels

The only thing in this entire build that has to be true is a sheet of plywood
on two sawhorses.

Everything else is measured from it, and nothing on it is adjusted between
panels — so panel forty is panel one.

![One flat sheet on sawhorses, and nothing else.](jig-01-bench.png)

## Building the jig

### 1. The bench

One sheet, flat, level enough that a marble does not run. Flatness is the
whole specification: every angle below is measured from this surface, so the
panel cannot wind or twist as long as the board does not.

Check it with a straightedge on both diagonals. If it rocks, shim the horses,
not the sheet.

### 2. The triangle, struck once

![The panel's triangle, struck once from the solution and never measured again.](jig-02-triangle.png)

Snap the panel's mathematical triangle onto the board — the {{cut.a_chord}}
and {{cut.b_chord}} inch sides of Chapter {{ch.two_lengths}}.

Strike it **one time**, from the geodesic solution, and never measure it
again. Forty panels laid out from three lines struck once is a different
proposition from forty panels laid out from forty tape measurements, and the
difference is the entire reason this works.

The tool prints this triangle full size as a drawing you can lay on the sheet.
Chapter {{ch.tooling}} says how.

### 3. Axis rails

![Three cleats, one per member, each parallel to that member's point-axis.](jig-03-rails.png)

Three low cleats, one per member, each set parallel to that member's point
axis and just to the seam side of it.

These fix **position across the panel**. Push the stick against its rail and
the sector's point line sits exactly where the solution says.

The rail references the sawn point, never the bark. A lumpy log does not move
the joint.

### 4. Red and green fences

![Red to red, green to green, or the stick does not seat.](jig-04-fences.png)

Two short cradle plates per member, standing against the two sawn radial
faces of the wedge.

These fix **rotation about the stick's own axis**, and they are the reason
you cannot get a member in the wrong way round. A sector dropped in rotated
ninety or a hundred and eighty degrees still *looks* fine. These plates make
it not fit.

Mark them. Red side to red plate, green side to green plate. It feels
childish for about two panels and then it saves you one.

### 5. The two cut planes

![The magenta plate is the flush-cut fence; the cyan is the face the next butt lands on.](jig-05-guides.png)

At each head end, a plate standing in the plane of the triangle's edge. That
is the flush-cut fence: a saw run flat against it cuts the head to exactly the
right plane without anybody setting a bevel or a mitre.

At each butt end, a plate in the plane of the receiving face the next stick's
butt will land on.

That is the fixture. A sheet, three cleats, six cradle plates, six guide
plates. Nothing on it moves again.

## Making one panel

### 6. The butt cut, off the jig

![The one cut made before assembly, and the only one that can be batched.](jig-06-buttcut.png)

One stick, still full length at both ends, laid up to the cyan plate. Cut the
butt.

This is the **only** cut made before assembly, and every stick of the same
family takes the same one — so it runs through a saw bench in a batch rather
than being fitted one at a time. Sixty A butts, then sixty B butts.

### 7. First stick down

Butt now cut, dropped against its rail and its two fences. The head end is
still long and hangs off the board.

Two ends, two completely different operations. The butt arrives finished. The
head arrives long on purpose and you do not touch it yet.

### 8. Second stick, butt onto side

![End to side: a flat sawn face on a flat sawn face.](jig-08-member2.png)

The second stick lands so the first stick's butt bears on its **radial face**
— on the side of it, not on its end.

Nothing is mitred to meet at a point. A flat sawn face is pressed onto a flat
sawn face, which is what a split wedge already has without any further
machining.

### 9. The last stick slides in

![The last stick is captured at both ends, which is why the head is left long.](jig-09-member3.png)

The third stick is captured at **both** ends once the other two are down, so
it cannot drop in from above. It comes in along its own axis, sliding home
into the pocket.

This is the one awkward move in the whole method, and it is why the head end
is left long: the extra length is what gives the last stick somewhere to come
from.

If you have trapped it, you put the sticks down in the wrong order. Take one
out and start again; you will do this once.

### 10. Pull it up tight

Three butts bearing on three sides. The loop is closed, the frame holds its
own shape, and the jig is now only keeping it flat while you finish.

All three heads still hang off long.

### 11. Flush-cut the three heads

![The head is never measured. It is cut in place.](jig-11-flush.png)

Saw each head back to its magenta fence. The stock hanging past the board
falls off.

**This is the whole trick.** The head is never measured. It is cut in place,
to the plane the neighbouring member has already established — so error in
stock length, or in the butt angle, or in how round the log was, leaves as
offcut instead of accumulating around the triangle.

![Uncut, every head trespasses across the vertex.](heads-uncut.png)

![And after.](heads-cut.png)

Those two pictures are the same corner of the same dome. In the first, every
head still carries its stock and they trespass straight across the geodesic
vertex into the neighbouring panel. In the second they end inside their own
triangle and nothing crosses.

### 12. Panel off the jig

A finished triangular frame, its three corners clean inside the mathematical
triangle. The jig is empty and unchanged.

Drill the inserts now, while it is flat — Chapter {{ch.hotswap}} — and sheathe
it now if you are sheathing on the bench, which you should be.

Then do it {{dome.panels}} times, in two families: {{dome.aaa}} equilateral
and {{dome.bab}} isosceles.

## What the jig is really buying

Repeatability, obviously. But more than that: it moves the hard work indoors
and off the ladder.

Every operation above happens at waist height, on a bench, with both feet on
the ground, in whatever weather. The part of dome building that everybody
pictures — the awkward bit up a ladder holding something heavy at an angle —
happens once, in Chapter {{ch.raise}}, and takes three days out of a
fortnight.
