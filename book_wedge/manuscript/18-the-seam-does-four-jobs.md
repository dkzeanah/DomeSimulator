---
chapter: 18
title: The Seam Does Four Jobs
strand: explain
status: draft
target: 1920
updated: 2026-09-25
---

# 18. The Seam Does Four Jobs

The channel is already there.

Two sawn faces meeting at a dihedral angle cannot close flush — Chapter
{{ch.pinwheel}} — so every one of this dome's {{dome.seams}} seams carries a
void running its whole length. {{dome.seam_ft}} feet of it, threaded through
the structure, touching every panel, arriving at the apex and at the base
ring.

You are going to fill it with something. The question is what.

![Every seam in the dome, and the channel in each one.](keys-everywhere.png)

## Four jobs, one space

**Rain in at the ridge.** A slot along the outer cap takes water where it
already runs — the seam is the low line between two panels, which is where a
roof sends water anyway. Under the slot is a gutter with suction inlets, and
under that a drain to the tank. The building's guttering is inside its
structure rather than bolted onto its edge.

**Air along the wood faces.** A perforated liner washes air down both sawn
faces of every member. That is the surface most at risk in a timber frame and
the hardest to reach, and it is now the surface with moving air on it
permanently.

**A desiccant leg.** A three-way gate routes the airflow either along the
faces, or through a silica cartridge, or isolates the water path from the air
path entirely. In wet weather when moving air will not dry anything, you pass
it through the desiccant instead.

**And a plate that condenses on purpose** — the part that needs its own
section, below.

The reason all four fit is that they want the same thing: a continuous,
serviceable void that runs everywhere and reaches the ground. Nobody would
build that void for any one of these jobs. It was free.

## The air barrier

Here is the part that changes how you think about leaks.

Run the fan so the interior sits slightly **above** outside pressure, and the
net flow at every gap in the envelope is outward.

A gap in an inward-leaking building admits weather. The same gap in an
outward-flowing one does not — not because it is sealed, but because the air
is going the wrong way for anything to ride in on. Wind-driven rain at a seam
meets air coming out of it.

The numbers are undramatic, which is the good news:

    interior volume        {{air.volume}} cu ft
    at {{air.ach}} air changes an hour   {{air.cfm}} cu ft a minute
    held above outside     {{air.pressure}} Pa
    spread over            {{dome.seam_ft}} ft of seam

{{air.pressure}} pascals is far below what anybody feels on a door, and
{{air.cfm}} cubic feet a minute is a bathroom extractor. Two fans —
{{air.fans}} — so the barrier can be reversed, because there are days when you
want to draw rather than push.

**What it costs honestly:** it runs continuously, and it only works while it
runs. A positive-pressure envelope with the fan off is an ordinary envelope
with holes in it. That is an argument for sizing the array in Chapter
{{ch.bom}} so this load never has to be shed, and it is an argument against
treating the barrier as a substitute for the cap of Chapter {{ch.one_layer}}.
It is a second line, not the first.

## Condensing on purpose

Thermoelectric plates — Peltier modules — on the cold side of the channel,
dropping moisture out of the air as liquid straight into the gutter the rain
already uses.

The appeal is obvious. The plate sits exactly where the moisture is highest,
it is doing dehumidification whether or not you want the water, and the water
it makes needs no new plumbing because the drain is right there.

Now the number.

    one inch of rain on this roof     {{cond.gallons_per_inch}} gal
    the plates, running a day         {{cond.gal_day}} gal   ({{cond.watts}} W)
    the plates, running a year        {{cond.gal_year}} gal
    which is the same as              {{cond.rain_equal}} inches of rain
    energy per litre                  {{cond.kwh_per_litre}} kWh

**A whole year of condensing is worth less than half an inch of rain.**

At {{cond.kwh_per_litre}} kilowatt hours a litre, thermoelectric condensing is
several times worse per watt than a compressor, and a compressor is already
not how anybody sensible makes drinking water on a roof.

So the honest position, and it is the one this book takes:

**The plates are a dehumidifier that happens to yield liquid. They are not a
water supply.** The water supply is the roof, and the roof is
{{cond.gallons_per_inch}} gallons an inch.

Which leaves them worth fitting for one reason only: there are conditions —
warm, humid, still, no rain for weeks — where the channel will not dry itself
and the desiccant is saturated, and in those conditions a plate is the only
thing in the design that can actively remove water from the timber. Run them
on daylight surplus, treat the drips as a bonus, and never size a tank on
them.

## What the module costs

    {{sys.seam_table}}

${{sys.seam}} against a dome at ${{money.price}} — a little over half the
price of the building it is fitted to.

That is a lot, and it is why this is a chapter about a system rather than a
line in the standard article. The parts of it scale differently, too: the cap,
liner, gutter and drain are per foot of seam and grow with the dome, while the
gates, cartridges and plates are per seam and grow more slowly.

**If you fit one part of it, fit the gutter.** Water off the roof is the
single best return in this chapter, it needs no power, and it is the only
piece that pays for itself in a season.
