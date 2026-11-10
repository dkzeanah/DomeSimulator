---
chapter: 92
title: The Wedges Supply Material; the Connections Make the Structure
strand: explain
status: draft
target: 1100
updated: 2026-10-27
---

# 92. The Wedges Supply Material; the Connections Make the Structure

There is a tempting version of this whole idea that is wrong, and it is worth
killing early because it is the version most people arrive with.

The tempting version says: a sector is some wood; two sectors are twice the
wood; so a bundle of sectors is a bigger, stronger beam, and the finer you split
and the more you bundle, the better it gets. Add wood, get a stiffer beam.

It does not work like that, and the reason is the single most important rule in
this part.

## Loose wood slides

Stack a handful of planks and bend the stack. Each plank bends about its own
middle, and the planks slip past each other at every face, because nothing stops
them. The stack is no stiffer than the sum of the separate planks: *n* planks
give you *n* times one plank's stiffness, and no more.

Now glue the same planks into one block and bend that. The faces cannot slip, so
the outermost wood is forced to stretch and squash as if it were part of one deep
beam — and a deep beam's stiffness grows with the *cube* of its depth. The glued
block is not *n* times stiffer than one plank. It is *n*-squared times stiffer
than the loose stack of the very same wood.

![The same wood, loose and glued. For planks the glued beam is n-squared stiffer; a separated chord does better still.](grammar-composite.png)

Both of those are computed, not asserted, and the two bounds for planks and for
wedge chords sit side by side:

    {{grammar.composite}}

Eight planks glued are {{grammar.glue8}} times the stiffness of eight planks
loose. Same wood. The entire difference is whether the shear between the layers
is carried.

## So the connection is the structure

That is why the wedges are only the material. A bundle becomes one member when,
and only when, something — glue, a web, a plate, a row of fasteners — carries
the longitudinal shear between its parts. Without that, you have a pile that
happens to be stacked. With a perfect version of it, you have one transformed
section. Real connections live between the two bounds, and *where* between them
is not a formula — it is a load-slip test of the actual joint. This is the honest
reason the grammar reports a loose limit and a composite limit rather than one
tidy number.

The recursive promise of the idea survives this, but it has to be stated
correctly. It is not

> add wood → stronger beam.

It is

> add wood **and** add the load path that activates it → stronger beam.

## Reinforce where the demand is

Stated that way, the method becomes a set of moves rather than a rule that more
is better. Need more axial capacity? Add a parallel sector. Need more bending
stiffness? Move wood *away from the neutral axis*, not into the middle. Need more
bending *strength*? Reinforce the chords that are already farthest out. Overloaded
a joint? Add a local shoe or doubler there, not six feet of extra member
everywhere else.

A sawn two-by-ten has material along its whole length because the saw decided the
rectangle before anyone knew where the load would be. A member built this way can
put the wood, and the connection, where the force actually turns out to be. That
is the advantage — but only once you have stopped believing that bundling is
free.
