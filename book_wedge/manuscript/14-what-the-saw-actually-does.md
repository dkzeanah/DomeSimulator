---
chapter: 14
title: What the Saw Actually Does
strand: explain
status: draft
target: 1380
updated: 2026-10-03
---

# 14. What the Saw Actually Does

Everything in the last two chapters could be argued about. This chapter was
measured.

## Measured, and guessed

<!-- concept: harvest/assume -->

Before any rate, here is what the figures rest on, sorted into the two piles
this book always keeps apart. Geometry, board feet and angles are computed.
The rest was either timed, weighed and read off a rack on site, or it is an
estimate, and it says which:

    {{work.assumptions}}

Every estimate sits on the store-bought side of the comparisons that come
later, which is the side it flatters least to guess about.

## Two sessions, and do they agree?

<!-- concept: why/sessions -->
<!-- concept: why/rate -->

Two separate sittings with the saw, each measuring something different. One
counted finished wedges against the clock. The other measured feet of rip cut
in an hour at full depth, with the fuel and bar-oil tanks counted and one chain
sharpening included.

Because they counted different things, they can be divided -- feet of cut per
finished wedge -- and the geometry can predict that same number without being
told it:

    {{work.rate}}

Two independent measurements and a geometric prediction agree closely enough
for the rate to be worth planning on, and the planning figure is set
deliberately below the measured one.

![Two sittings, timed.](plate-saw-sessions.png)

## What the harvest took

<!-- concept: harvest/cost -->

At the planning rate, ripping the frame's {{dome.members}} members takes
{{rip.hours}} hours of saw time. The whole harvest is laid out as
{{rip.days}} days: {{rip.days_felling}} of felling, {{rip.days_bucking}} of
bucking and {{rip.days_ripping}} of ripping.

Ripping is the part that was timed with the fuel written down:
{{rip.tanks_hour}} tanks an hour for {{rip.hours}} hours, {{rip.tanks}} tanks.
The saw's tank is an estimate -- the listings disagree, between
{{rip.tank_lo}} and {{rip.tank_hi}} litres -- so the fuel is a range:
somewhere between **{{rip.gal_lo}} and {{rip.gal_hi}} US gallons** for all the
ripping. Felling and bucking were never metered, and they are left out rather
than guessed.

A few gallons of fuel for the frame of a house. That is the figure the whole
method is built on, and it is a measured one.

## Counting the cuts

<!-- concept: wedge/actions -->
<!-- concept: wedge/m_actions -->

The real measure of a system like this is not money. It is the number of
actions per piece of finished building: measuring, marking, setting up,
cutting, edging, planing, sorting, stacking, hauling and handling the waste.
Standard lumber is only convenient because somebody else already paid for all
of those. When the tree is standing next to the site, the question becomes:
what is the shortest honest path from that tree to a finished member?

Count it both ways, for one tree:

    {{work.actions}}

And that is only the cuts. Every other action on the milling side -- the
setting out, the sorting, the hauling between machines -- comes on top. The
shorter chain is also the one that keeps more of the tree.

![One tree to a finished member, counted both ways.](plate-counting-cuts.png)
