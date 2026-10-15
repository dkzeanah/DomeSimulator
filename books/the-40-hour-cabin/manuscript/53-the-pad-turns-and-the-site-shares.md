---
chapter: 53
title: The Pad Turns, and the Site Shares
strand: explain
status: draft
target: 1260
updated: 2026-10-05
---

# 53. The Pad Turns, and the Site Shares

<!-- concept: byod/rotation -->
<!-- concept: byod_deepseek/rotation -->

The top of the range is a pad that turns.

A rotating foundation is the expensive option and, honestly, it is just very
cool. Maybe today you want the window facing the street. Maybe somebody is
coming over and you want it facing the private, fenced corner. Maybe you want
the morning sun on your face, and maybe tomorrow you definitely do not. A
house that turns can change which way it faces without a single solar panel
on it.

Put an asymmetric array on it -- cells on one side of the shell -- and turning
it is also aiming the array. The bearing, the drive and the rotating utility
connections all need their own development, and the first site will not have
one (Chapter {{ch.why_me}} says why). This is future deluxe hardware. But it
is worth knowing what it would be worth.

![The deluxe version: the pad turns.](plate-pad-turns.png)

## What tracking is worth

<!-- concept: dome_park/math_solar -->

Every figure in this section is for a dome {{tt_sun.radius}} feet in radius,
the medium two-person size, because a number of kilowatt hours a month means
nothing without the dome it came off. The panels are on the dome, not the pad;
the pad only turns.

First, how much a shell can carry at all. Panel areas are measured off the
model's own faces:

    {{park.w_capacity}}

That is installed capacity, not a promise. Sun angle, shade, weather and
losses decide what a curved face actually delivers. Now the energy, fixed and
tracking:

    {{park.w_solar}}

Single-axis tracking adds about {{tt_sun.gain_pct}} percent over a fixed array:
on one side of this dome, {{tt_sun.gain_mo}} kilowatt hours a month. The skirt
below the cells in the middle layout is also the rain catchment -- the same
metal that keeps water off the bottom ring collects it.

:::box correction
**The first version of this model was wrong about solar.** It valued every
kilowatt hour the shell made at the retail price, which quietly assumed the
tenant was buying power they would never have bought. A tenant uses about
{{tt_sun.tenant}} kilowatt hours a month; a fully clad shell makes
{{tt_sun.all_mult}} times that. So the model changed: power that displaces the
tenant's own draw is worth retail, ${{tt_sun.retail}}; everything past it is
worth the export rate, ${{tt_sun.export}}. That took the pad's solar income
down by well over half.
:::

:::box against
**At export value, the turning ring takes {{tt_sun.payback_export}} years to
pay for itself.** A year of tracking gain is worth ${{tt_sun.gain_export}}
sent back to the grid, against a ring that costs ${{tt_sun.ring_40}} under a
40-foot pad. Even if every gained kilowatt hour were worth retail, it would
take {{tt_sun.payback_retail}} years. Turn the house because you want it to
face somewhere. Do not turn it for the money.
:::

The real case for cladding a dome in cells is a park that can sell the
surplus, not a tenant who cannot use it.

![What tracking is worth, and what it is not.](plate-tracking-worth.png)

## What a site can share

<!-- concept: dome_park/shared -->

Some of what a house needs can be bought once by the site instead of once per
house, and that changes what a dome has to be.

A **bathhouse** on the site means a dome can skip plumbing entirely -- and
plumbing is the single most expensive and most regulated thing in a small
dwelling. Or the host fits a utility column on the pad, toilet and sink and
shower and drain, once, for every owner who ever parks there. Either way it is
paid for by the party who stays and used by everyone who comes and goes.

Note what a host is *not* obliged to do. Reselling power and water with a
margin is one option, not the model; a host may simply pass the meter through.
A more ambitious site might run a shared off-grid plant with central storage
for the whole cluster. What hosts really compete on is the range of things a
site offers -- location, price, services, how well the arrangement works for
the people living there -- and the price follows from that.

![A bathhouse, so a house need carry no plumbing.](plate-bathhouse.png)

## Another use

<!-- concept: byod/storage -->
<!-- concept: byod_deepseek/storage -->

A side thought, and only that. The same kit -- a compact shell, a quilted
layer or two, a reusable pad -- would make an interesting climate-controlled
storage building. It would need its own check of cost and performance before
anybody sold it as one. But housing is not the only thing the parts are good
for, and a site with three empty pads in a slow season might find out what
else they are good for.

![The same parts, storing something other than people.](plate-storage-dome.png)
