---
chapter: 56
title: Where the Fuel Actually Goes
strand: explain
status: drafting
target: 1920
updated: 2026-09-17
---

# 56. Where the Fuel Actually Goes

*Most of the fuel raises nothing at all.*

## Where the Fuel Actually Goes

There are two ledgers in a build and only one of them gets written down.

The money ledger decides whether you can afford the thing. The other one
decides whether you can finish it. It is kept in calories, it is settled every
evening whether you look at it or not, and running out of it does not feel like
running out of money -- it feels like deciding, quite reasonably, to do the rest
next weekend.

So this chapter counts it. Every part of one building, every motion that part
takes to get from the pile to its place, and what each motion costs a body.

Before a single number: **this is not the fortnight.** The fortnight is one
person and a bare frame, and there is no metabolic model of it, because nobody
wired a body to me while I was ripping. What there *is* a model of is the
assembly line's own product -- the {{cal.product}}, a finished house of
{{cal.radius_m}} metres' radius, {{cal.stations}} stations, {{cal.elements}}
parts, built by a crew of {{cal.crew}}. That is a bigger, more finished and more
crowded job than anything else in this book, and every figure below is per
person on *that* build.

I am using it anyway, because the shape of the answer does not depend on which
dome it was, and the shape of the answer is the whole point.

## One house, counted in parts and motions

The method is mechanical. Take the element list -- all {{cal.elements}} pieces,
frame and floor and cladding and fixtures -- and turn each one into the same
{{cal.motions}} motions: walk to the pile, lift, carry it over, place it, fasten
it, stand back up, rest. Each motion gets a duration from the part's own mass,
distance and height, and a cost from published activity data. Then add them all
up.

![Fifteen stations, ordered by what they cost a body rather than by what they weigh.](../../deliverables/book/figures/fuel-station-ledger.png)

{{cal.material_kg}} kilograms of building. {{cal.lifted_kg}} of it passes
through one person's hands -- less than the total, because anything over
{{cal.team_lift_kg}} kilograms is a two-person lift and the load splits.

{{cal.hours}} hours each. That is {{cal.shifts}} shifts of
{{cal.shift_hours}} hours, and it costs {{cal.per_worker}} kilocalories per
person, {{cal.crew_total}} for the pair.

The figure worth holding is not the total, though, because the total only tells
you how big a house somebody ordered. The *rate* is what travels:
**{{cal.per_shift}} kilocalories a shift.** That is a working day, and it sits
on top of a resting requirement of about {{cal.rmr_kcal_day}} a day that a body
wants whether it builds anything or not.

Now the unflattering one. Averaged across the whole build, that comes to
{{cal.watts}} watts, or {{cal.mets}} METs. The occupational-physiology figure
for what a person can sustain across a full shift is {{cal.watt_bound}} watts.
There is almost nothing in that gap. The model is not saying this is comfortable
work. It is saying the work sits at the top of what is sustainable, and that it
only stays there because {{cal.rest_pct}} per cent of the timeline is an
explicit recovery allowance -- {{cal.rest_hours}} hours of standing still,
scheduled rather than hoped for. Take the rest out to go faster and you do not
get a shorter build. You get a shorter *run* of builds.

Read the stations by fuel rather than by weight and the order surprises. The
{{cal.top_stage}} is the single most expensive station, {{cal.top_stage_kcal}}
kilocalories across {{cal.top_stage_parts}} parts. But the layers that go on
over it, between them, weigh {{cal.skin_mass_ratio}} times what it weighs and
cost {{cal.skin_fuel_ratio}} times its fuel. Fuel outruns mass, every time,
because fuel follows part count rather than kilograms. The heavy part of a
building is not the tiring part of a building.

For scale, the crew's total is {{cal.bread}} slices of bread. Or {{cal.bananas}}
bananas. Or {{cal.diet_days}} days of somebody eating normally and doing nothing
else with it.

That last framing is not a joke, and it is the most practically useful line in
the chapter. A build of this size is a second full-time diet running alongside
your first one. If you are doing it solo, at a distance from a shop, on a
schedule you set yourself, then food is a material and you have to lay it in
like any other -- and the failure mode of getting it wrong is not hunger, it is
an afternoon that quietly does not happen.

## The fastening surprise

Now split the same total by motion instead of by station, and something falls
out that changed how I think about joints.

![Each motion's share of the clock beside its share of the fuel. Only the gap between the two is intensity.](../../deliverables/book/figures/fuel-motion-split.png)

**Fastening is {{cal.fasten_pct}} per cent of the food energy.** Everything else
in the build -- all the walking, all the lifting, all the carrying, all the
placing -- shares what is left.

Before that gets quoted as something it is not, here is the honest version:
fastening is also {{cal.fasten_time_pct}} per cent of the *clock*. Only
{{cal.fasten_gap_pct}} points of that {{cal.fasten_pct}} are intensity. The
other {{cal.fasten_time_pct}} are simply where the day goes. Driving a screw is
not brutal work. There is just an enormous amount of it -- {{cal.fasten_hours}}
hours of it on this build -- and that is a different claim and a more useful
one.

Notice the recovery allowance running the other way, too: {{cal.rest_pct}} per
cent of the clock and only {{cal.pause_pct}} per cent of the fuel, because
standing still is cheap. That asymmetry is the whole argument for the allowance,
in one picture. Rest buys back a large slice of the clock for a small slice of
the fuel.

And then the number I did not expect.

![How much of each motion's fuel became height, against the most muscle can convert.](../../deliverables/book/figures/fuel-motion-efficiency.png)

Of the {{cal.per_worker}} kilocalories one person spends on this house, the
amount that ends up as *height* -- as mass actually raised against gravity,
which is the only part of a build that is physics rather than physiology -- is
{{cal.mech_kcal}} kilocalories. {{cal.mech_mj}} megajoules.
**{{cal.mech_pct}} per cent.**

Turn it the other way up: {{cal.fuel_per_lift}} calories burned for every one
that went upward.

The first time that fell out I assumed the model was broken. It is not, and the
proof is in the same chart. Ask the question of the *lift alone* and the answer
is {{cal.lift_eff_pct}} per cent -- an ordinary human lift, and not far short of
the {{cal.muscle_pct}} per cent that is the best muscle can convert under any
circumstances at all. The body is fine. While it is lifting, the body is close
to its own ceiling.

There is one more thing in that lifting work worth pulling out, because it
contradicts something everybody has been told. Split the raising by which part
of the body did it and the trunk accounts for {{cal.trunk_pct}} per cent of it,
the arms {{cal.arms_pct}}, the legs only {{cal.legs_pct}}. The reason is
unglamorous: your torso is the heaviest thing you lift all day, and you lift it
every time you stand up from a squat. "Lift with your legs" is still right, but
not because the legs do most of the work -- they do the least of it. It is right
because it changes the *path* the trunk travels, and the trunk is the load.

It is just hardly ever lifting. Lifting, carrying and walking together come to
{{cal.handling_pct}} per cent of the fuel -- {{cal.lift_kcal}} kilocalories for
the lifting alone, out of {{cal.per_worker}}. The rest of the time the body is
*holding* --
holding a posture, holding a part in place, holding an arm up -- and holding
something still does no mechanical work whatsoever while costing a great deal to
do. That is not a defect in the model. That is what manual labour is, and it is
why a day of light work you would describe as "not lifting anything" still
leaves you unable to start another one.

Which makes the sentence to take away from this chapter a slightly strange one.
**The screw does not go up. The arm does.** And then it comes back down, and
doing that for {{cal.fasten_hours}} hours is the build.

## What this says about the hardware

If most of the fuel is in fastening, the design question changes.

The obvious instinct is to make fastening faster: a better driver, a better bit,
a magnetic holder. All worth doing. But the arithmetic above says something
sharper -- a joint that needs *fewer* fasteners beats a joint that is faster per
fastener, because the count is the thing being multiplied.

This frame carries {{flat.brackets}} brackets, {{nine.holes}} pilot holes and
{{flat.screws}} screws, and -- from {{ch.flat_rate}} -- exactly that many at
every diameter in the handling band. Each of those {{flat.screws}} is a fixed
metabolic tax, paid whatever size dome you are building.

It is also, I have to admit, the number I would be most tempted to increase.
When a joint worries you at four in the afternoon, the instinct is to put
another screw in it. This chapter is the reason to think twice: one extra screw
per bracket is another {{flat.brackets}} fastenings, on every dome, forever, and
it will not be the thing that saves you. If a joint is not right, the fix is
upstream in the jig, not downstream in the driver.

Two parts of this design are already doing that work, and both are worth naming
as energy decisions rather than as geometry ones.

The seam key of {{ch.seams}} closes a joint with a shape instead of with
hardware. Every seam it closes is a seam nobody drives fasteners into.

The panel raise from {{ch.forty_panels_one_hundred_and_twenty_members}} is the
larger of the two. {{nine.panels}} panels go up rather than {{frame.members}}
loose members -- and more to the point, each one goes up *already fastened*, on
a bench, at waist height, on the ground. The fastening did not disappear. It
moved out of the overhead posture, which this model prices higher for exactly
the reason your shoulders already know.

I will not overstate either of them. The key is another milling operation, and
the panel approach wants a cable, a winch and somewhere to hang them. Neither is
free. But both are trades of *fuel* for *setup*, and setup is paid once and
amortised across every dome after it, while fuel is paid again every single
afternoon.

## What is measured and what is modelled

This ledger is a mixture, and the mixture matters more than the total.

**Computed.** Every mass, every placement height, every carry distance, off the
geometry and the element list. The mechanical work is *m g h*, with nothing
estimated in it.

**Counted.** The motions. Seven per part, {{cal.elements}} parts, the same
sequence for all of them.

**Modelled.** The calorie cost of a motion. That is {{cal.constants}} published
constants -- activity intensities, a load-carriage equation, a resting-rate
formula, a recovery allowance -- listed by name and source on their own page
rather than buried. Change one and this chapter changes with it.

**Weakest link, named.** Fastening time is a *residual*. The model takes the
catalogue's labour estimate for a part, subtracts the walking, lifting, carrying
and placing it has computed, and calls whatever is left fastening. So
"{{cal.fasten_pct}} per cent is fastening" is really "{{cal.fasten_pct}} per
cent is everything that is not handling" -- fitting, fiddling, checking, finding
the bit you put down somewhere. I am comfortable with the conclusion anyway,
because the conclusion does not rest on the residual. It rests on the handling,
and the handling is the part that was computed. Lifting really is
{{cal.lift_pct}} per cent of the fuel however you choose to label the rest.

**Not metered at all.** The felling and the bucking. This ledger begins at the
stockpile, and the {{work.harvest_days}} days in front of it -- a chainsaw, a
slope, a log that does not want to move -- appear in none of these numbers. If
anything here is optimistic, it is that.
