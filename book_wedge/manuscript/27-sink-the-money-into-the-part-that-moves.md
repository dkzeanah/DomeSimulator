---
chapter: 27
title: Sink the Money Into the Part That Moves
strand: explain
status: draft
target: 1480
updated: 2026-09-25
---

# 27. Sink the Money Into the Part That Moves

Here is the theory, in one sentence.

**Put the money in the hardware, because the hardware transfers and the shell
does not.**

![What buying it once is worth.](plate-core-cost.png)

## The two halves of a dome

Every building in this book is two things wearing one roof.

**The shell** — {{dome.members}} members, {{dome.panels}} panels, the cap, the
floor. It is shaped by *this* dome: its members are cut to this diameter, its
panels are this geometry, its cap is this size. Move to a different dome and
none of it comes with you, because none of it fits.

**The core** — the utility column and everything in it. A chase, a sub-panel,
a manifold, a stack, a seal cap. {{core.parts}} parts carrying
{{core.services}} services. It is shaped by *what a small building needs*,
which is the same in every small building.

The shell is specific. The core is generic. And the core is
**{{core.share}} per cent of what the dome costs to build** —
${{core.cost}} of it.

## What generic means for money

A shell is consumed by the building it is part of. When that building's life
ends, so does the shell's.

A core is not. It was never shaped by this dome, so it fits the next one. Its
declared service life is {{core.life}} years — not because a pipe wears out in
{{core.life}} years but because at some point it is outgrown rather than worn
out — and moving it to the next dome costs ${{core.moves}}.

Two hundred and sixty dollars to move {{core.share}} per cent of a building.

That is the whole theory. The expensive, fiddly, skilled, permit-adjacent
third of the project gets bought **once** and then amortised across every dome
you ever put it in.

## Why this changes what you should overbuild

Ordinary building advice says spend where it shows and economise where it does
not.

This says something different: **spend where it transfers.**

Every dollar in the shell is spent on this dome. Every dollar in the core is
spent on this dome *and the next one and the one after*. So the core is the
place where overbuilding is not overbuilding — it is prepayment.

Concretely, this is why the design specifies:

* a sub-panel with a **spare breaker**, so the first snap-in module does not
  need a panel change;
* a four-port manifold with **capped stubs**, in a dome that ships with no
  plumbing at all, because the alternative is opening the chase later;
* a feeder that **unplugs** — a cord and a recessed inlet rather than hard
  wiring, which is what makes the dome moveable without an electrician;
* a floor-port tie-in that the **host** makes once and nobody disturbs when a
  dome is swapped.

Every one of those is a small extra cost now against a large avoided cost
later, and each one is only worth it because the thing carrying it survives
the building it was bought for.

## The same argument, one level up

![This only works as a system.](plate-system.png)

The core is to a dome what the pad of Chapter {{ch.pad}} is to a site and what
the jig of Chapter {{ch.jig}} is to a panel.

In all three cases, something is built once, carefully, and then used many
times without being rebuilt:

    the jig     built once, makes {{dome.panels}} panels
    the core    bought once, serves several domes
    the pad     built once, hosts a succession of buildings

And in all three cases the thing being amortised is not material — it is
**precision and setup**. The jig holds the angles so you do not have to. The
core holds the services so an electrician does not have to come back. The pad
holds the level and the connection so a foundation does not have to be poured
again.

That is what "this only works as a system" means. Any one of them alone is
merely a nice idea. Together they move almost all of the difficulty out of the
building and into three objects that are built once.

## The honest objections

**It raises the entry price.** A dome with a proper core costs more than a
dome with a light socket and a hose through the wall. The transfer argument
only pays if there is a second dome, and for somebody who will only ever build
one, this chapter is wrong and they should spend the money on the skin.

**Transfer is not free.** ${{core.moves}} is a declared assumption, not an
invoice. It covers disconnection, handling and reconnection on a pad that
already has the port. It does not cover a drive across a country.

**Generic is a claim, not a fact.** The core is generic across the
{{seed.count}} structures in this catalogue, which were all designed around
it. Whether it is generic across somebody else's building is unproven, and
the honest answer is that it is generic across this system and that is all
anybody has tested.

## The sentence to keep

If you are building one dome: put your money in the skin and the floor, as
Chapter {{ch.skin}} says, and keep the core simple.

If you are building more than one: **put it in the core.** It is the only
third of the project you will not have to buy again.
