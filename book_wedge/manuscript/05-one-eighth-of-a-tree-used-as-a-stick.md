---
chapter: 5
title: One Eighth of a Tree, Used as a Stick
strand: explain
status: draft
target: 1200
updated: 2026-09-25
---

# 5. One Eighth of a Tree, Used as a Stick

A member in this frame is a {{cut.sector}}-degree slice of a
{{cut.trunk}}-inch log. It has a point, two flat sawn faces, and a curved
bark face.

That is the whole part. Nothing is machined.

![The end of a member: two sawn faces and a bark face, and nothing machined.](wedge-cross-section.png)

## What the shape gives you for free

**Two reference surfaces.** The split faces are flat and they are at a known
angle to each other — {{cut.sector}} degrees, because that is what a
{{cut.splits}}-way split means. Every jig in this book locates off those two
faces. You never reference the bark, which is lumpy, and you never reference a
measurement, which is a thing that can be wrong.

**A point that tells you which way round it is.** A rectangular stick has a
four-fold ambiguity: drop it in rotated ninety degrees and it still looks
fine. A sector has one obvious orientation, and — as Chapter {{ch.jig}}
shows — the fixture is built so a stick dropped in the wrong way round
physically does not seat.

**Depth where you want it.** The section is deep from point to bark
({{cut.depth}} inches here) and narrower across the face ({{cut.width}}
inches). Stand it point-inward and the depth is in the direction the shell
wants stiffness.

## Which way the point faces

This is the first decision in the build you cannot take back, because it
changes the seam, the key, and the shape of every panel.

![Point inward: the reference build.](wedge-orientation-point-dome-in.png)

The reference build faces the point **into the dome**. The bark faces are
outside, the flat sawn faces look at each other across every seam, and the
leftover sector angle opens toward the inside.

The consequences, from the solve: an A seam folds {{seam.fold_a}} degrees and
leaves {{seam.gap_a}} degrees of sector angle over; a B seam folds
{{seam.fold_b}} and leaves {{seam.gap_b}}.

Each pair sums to {{cut.sector}}. That is not a coincidence and it is the
closest thing this method has to a theorem: **the sector you split out of the
tree is exactly the seam budget the dome needs.**

## The other three

The solver will build all four. They are not equally good and they are not
equally bad, and the book shows them because a reader who wants something
different should be able to see what they are choosing.

![Points apart, each into its own triangle.](wedge-orientation-point-panel-in.png)

![Both points outward, at the sky.](wedge-orientation-point-dome-out.png)

![Points toward each other, across the seam.](wedge-orientation-point-panel-out.png)

Point outward puts the flat faces where the weather is, which is a real
argument for it: a flat outer face is easier to seal a panel against than a
curved one. It costs you a key more than twice the size, and it puts the
narrow point where the shell wants depth.

Points apart, and points across, both produce a seam that wants a key around
eleven and a half inches across its base. That is not a key. That is a beam
you are now also making.

## Why the bark stays on

It is free, it is already there, and taking it off is an operation on
{{dome.members}} sticks.

The honest version: bark is not a finish and it will come off in its own time
on the outside faces, in patches, over years. On a frame that is inside a
weatherproof skin — which is the argument of Chapter {{ch.skin}} — that is a
cosmetic event rather than a structural one.

If you want it off, take it off green, with a drawknife, in the first week
when it is still wet and comes away in strips. Do not plan to do it later.

## The one number to hold on to

A member's section is set by the log, and the log is set by what you have.
Everything downstream — the seam key's size, the depth of the wall, how many
trees you need — follows from the trunk diameter and the split count, and
Chapter {{ch.alternatives}} prices what happens when you change either.

What does *not* change is the two lengths you cut them to, and that is the
next chapter.
