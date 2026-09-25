---
chapter: 7
title: Half a Sphere Is a Building
strand: explain
status: draft
target: 800
updated: 2026-09-25
---

# 7. Half a Sphere Is a Building

A sphere is not a building. It has no floor and no door and half of it is
underground.

So you cut it, and where you cut it is a design decision with consequences.

![Where a sphere gets cut to become a building.](plate-hemisphere.png)

## Cutting at the equator

This book cuts at the equator: a hemisphere, exactly half.

The 2V geometry cooperates. There is a ring of vertices exactly on the
equator, so the cut lands on existing points and the base comes out as a
clean regular polygon — {{dome.base_sides}} sides, each one a long chord,
sitting flat on the ground with nothing to trim.

That is not true of every frequency and it is not true of every cut. Take a
3V dome and the equator falls between vertex rings, so you either move the cut
or accept a base that is not level. Take a 2V and cut it above or below the
equator and you get a shallower or deeper shell, a smaller or larger floor,
and a base ring that is no longer made of whole chords.

The equator is where the geometry is kindest, and this book takes the kindness.

## What the cut gives you

    across the base      {{dome.diameter_ft}} ft
    to the apex          {{dome.height_ft}} ft
    floor inside the ring {{dome.floor_sqft}} sq ft
    shell surface        {{dome.panel_sqft}} sq ft

Apex height equals the radius, because a hemisphere's apex *is* the radius.
That one identity saves more arithmetic than any other fact in this book.

## Counting the building

![Every part of the building, counted.](plate-counting.png)

Everything else falls out of the topology rather than being counted by hand:

    vertices             {{dome.vertices}}
    geodesic edges       {{dome.edges}}
    triangular panels    {{dome.panels}}
      equilateral (AAA)  {{dome.aaa}}
      isosceles   (BAB)  {{dome.bab}}
    structural members   {{dome.members}}
    interior seams       {{dome.seams}}
    base edges           {{dome.base_sides}}

Two of those are worth a second look.

**{{dome.members}} members for {{dome.edges}} edges.** The duplication of
Chapter {{ch.pinwheel}}: each panel brings its own three sticks, so every
interior edge has two.

**{{dome.seams}} interior seams, not {{dome.edges}}.** The {{dome.base_sides}}
base edges are the rim and have nothing on the other side of them, so they are
not seams. That distinction matters the moment you start counting keys, or
hose, or feet of gasket — and it is the kind of thing that is obvious once
stated and silently wrong in a bill of materials otherwise.

## Why it is a decagon and not a circle

The floor figure above is the **decagon** inside the base ring, not the circle
it sits in.

The circle is bigger — about seven per cent bigger — and the dome does not
reach it. Quoting the circle is the single most common way a dome's floor
area gets overstated, and it is overstated by exactly the amount of the ten
little segments between the chords and the arc.

This book quotes the decagon everywhere. It is the honest number and it is the
one you can put furniture on.
