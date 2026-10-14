---
chapter: 65
title: Build One Utility Core
strand: howto
status: draft
target: 1660
updated: 2026-10-05
---

# 65. Build One Utility Core

<!-- concept: module_build/open -->

This is not the argument for the core -- Chapter {{ch.core}} made that. This
is the work.

A utility core is the one part of this dome that is identical in every dome,
at every size and with every fit-out, because the interface it plugs into
never changes. So it is the first thing worth learning to build, and the
first thing worth building a jig for.

**{{corebuild.steps}} steps in {{corebuild.stages}} stages, about
{{corebuild.hours}} hours once you have done a few.** Your first will take
closer to {{corebuild.first_hours}}, and anybody who tells you otherwise has
not built one.

The whole core is built upside down on a bench and stood up at the end.
Working at waist height on a flange you can walk round is the difference
between an afternoon's job and a day of kneeling.

## What has to be on the bench

<!-- concept: module_build/tools -->

    {{corebuild.w_tools}}

{{corebuild.tools}} tools, and two of them are the ones people leave in the
van: the **go/no-go gauge** for the crimps, because a bad crimp passes a
pressure test and fails a year later, and the **torque screwdriver** for the
panel, because a terminal that feels tight is not a terminal that is tight.
Everything else you probably own.

![What has to be on the bench.](plate-core-bench.png)

## The chase

Before any service goes in, the box it goes in: the base flange set square on
the bench, the insulated chase sections stacked and pinned and checked for
plumb -- an error at the bottom is an inch at the apex -- and every hole a
pipe or cable will pass through drilled and grommeted now, with the sections
apart, never later with a hole saw inside a finished core.

    {{corebuild.w_chase}}

## Drain first, because it is the one you cannot re-route

<!-- concept: module_build/drain -->

    {{corebuild.w_drain}}

A two-inch stack the full height, with the trap at its foot. Dry-fit the whole
run and mark every joint across the socket before the cement comes out,
because solvent cement gives you about five seconds and no second chance at
alignment. Work bottom to top, so gravity is not pulling a fresh joint apart.
Then the floor-port boot -- the joint the host makes once, and nobody touches
again for the life of the pad.

## Water, then prove it before anything electrical exists

<!-- concept: module_build/water -->

    {{corebuild.w_water}}

Manifold at chest height, isolating valve at knee height where somebody who
has never seen the building will look for it, both on the opposite face from
where the panel is going. Four capped tails off the manifold, because a dome
with no plumbing still ships with them -- the alternative is opening the chase
later.

Then the test: **{{corebuild.psi}} psi for {{corebuild.test_min}} minutes,
with a gauge on it.** This is the last moment a leak costs you nothing. After
this the panel goes in, and a leak costs the panel.

![Water, proved before anything electrical exists.](plate-core-water.png)

## Power last, into a core already known to be dry

<!-- concept: module_build/power -->

    {{corebuild.w_power}}

Load centre at chest height on the dry face, inlet at the base. Feeder to the
main lugs, strain relief at both ends, every lug torqued to the figure printed
inside the panel door -- with a torque screwdriver, not by feel. A loose
terminal is how a panel burns, and it is the failure nobody sees coming.

Four breakers: the outlet ring, the lighting, the window unit, and one spare,
so the first module somebody snaps on does not need this door opened again.
Label them in writing, on the door, now -- not from memory in a year.

:::box clock "Not on the clock"
At {{corebuild.hours}} hours practised and {{corebuild.first_hours}} the
first time, the core is not on the {{clock.week}}-hour clock either. It is
built on a bench, on its own schedule, and it goes onto the pad as one object.
:::

## Close it, prove the cap, stand it up

    {{corebuild.w_close}}

Open and close the cap five times on the bench. If it is stiff there, it will
be impossible at the top of a dome in the rain.

## Everything you buy for one

<!-- concept: module_build/materials -->

    {{corebuild.w_materials}}

{{corebuild.lines}} lines, and none of them exotic: PEX and crimp rings, ABS
and cement, a load centre and four breakers, four sections of insulated chase,
and a cap. Every one is something you can buy this afternoon from somewhere
already near you.

![Everything you buy for one.](plate-core-shopping.png)

## One core, every dome

<!-- concept: module_build/wrap -->

The core is not consumed by the dome it goes into. It unbolts from four joints
and a lift, and it goes into the next one. When somebody outgrows a stem cell
and builds the size up, the core they built on a bench goes with them.

So the hours you just read are not hours per dome. They are hours once, for
as long as you keep building.
