---
chapter: 4
title: Why It Is Triangles
strand: explain
status: draft
target: 900
updated: 2026-09-25
---

# 4. Why It Is Triangles

Take four sticks and pin them at the corners into a square. Push one corner.

It folds. You now have a rhombus, and you can keep pushing until it is flat,
and at no point did anything break or bend or come loose. A four-bar linkage
is a **mechanism**. It is a machine for changing shape, and you have built one
by accident.

Take three sticks and pin them at the corners. Push one corner.

Nothing happens. Nothing *can* happen — the only way that triangle changes
shape is if a stick changes length or a pin fails. There is no motion
available to it.

![Why the shape is triangles at all.](plate-why-triangles.png)

## That is the entire structural argument

A square frame needs a rigid corner, because the corner is what stops it
folding. Rigid corners are welds, gussets, plates, moment connections — and
they are where every framed building spends its engineering.

A triangulated frame does not. The geometry is holding the shape, so the
corner only has to stop the sticks sliding apart. A pin will do. Two flat
faces pressed together will do, which is Chapter {{ch.pinwheel}} and is the
whole reason this method can use a joint you could make with a handsaw.

## And it is why the frame can be lumpy

Chapter {{ch.lumpy}} claimed a dome forgives error. This is why.

A mechanism amplifies error — push a linkage slightly out and it moves a lot.
A triangle cannot move at all, so the error has nowhere to go and nothing to
grow into. A triangle whose sides are each a shade off is simply a slightly
different triangle, sitting a shade differently in the shell, and its
neighbours absorb the difference at the seam.

The shape is doing the work. That is the sentence this whole book keeps
returning to.

## And why an icosahedron

![The solid everything starts from.](plate-icosahedron.png)

If triangles are the unit, the question becomes: how do you wrap a ball in
them?

The answer has been known since Plato. There are exactly five solids whose
faces are all the same regular polygon meeting the same way at every corner,
and of those, three are made of triangles: the tetrahedron with 4 faces, the
octahedron with 8, and the icosahedron with **{{phi.icosa_faces}}**.

Twenty is the most triangles you can get with every one identical and every
corner the same. So it is the roundest starting point available, and starting
rounder means less distortion when you subdivide.

Everything after this is subdivision. Cut each of those twenty faces into
smaller triangles, push the new points out onto the sphere, and you have a
geodesic dome. Cut each edge once and you have the 2V of this book. Cut it
twice and you have a 3V.

But before any of that, you have to *place* the twenty faces — which means
placing twelve points in perfectly even space, which is the next chapter and
is the one piece of this derivation that looks like magic.
