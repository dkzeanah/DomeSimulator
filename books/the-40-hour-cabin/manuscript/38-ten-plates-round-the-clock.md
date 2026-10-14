---
chapter: 38
title: Ten Plates, Round the Clock
strand: explain
status: draft
target: 2160
updated: 2026-10-04
---

# 38. Ten Plates, Round the Clock

<!-- concept: cabin_seam_climate/rescore -->

The owner bought one thermoelectric module, a TEC1-12706, for
${{ring.module_usd}}. The listing calls it a {{ring.listed_w}}-watt cooler with
a {{ring.dt_max}}-degree maximum temperature difference, running at 12 volts.
The proposal: put {{ring.modules}} of them round the dome, one at each rim
port, and run them day and night on the sun.

That asks three questions, and this chapter answers each one with numbers:

1. What does one module really do, mounted on the dome, on a humid day?
2. What do ten of them do for the room over a day -- heat out, water out?
3. What array and battery does it take to run them all day and all night,
   and what does that cost?

The answer, up front: ten plates cool a little and dry a little, and the
power system to run them round the clock costs about
{{ring.times_modules}} times what the plates do. Run them on daylight that would
otherwise go unused, and they are worth having. Run them around the clock, and
they are not.

:::box correction
A correction belongs here too. Chapter {{ch.seam_module}} counted six plates
at {{ring.old_watts}} watts, making {{ring.old_lpk}} litres of water per
kilowatt hour. That yield was an assumption. Solved from the module's own
listing below, the yield is {{ring.l_per_kwh}} -- each litre costs
{{ring.new_kpl}} kilowatt hours, not {{ring.old_kpl}}. The tables in Chapter
{{ch.seam_module}} now carry the solved figure.
:::

## What one module really does

<!-- concept: cabin_seam_climate/module -->

A Peltier module moves heat from its cold face to its hot face. Three things
work against it, all inside the module itself: the electricity heats it as it
passes through, heat leaks back from the hot face to the cold one, and the
greater the temperature difference, the less heat it can move. Put
in the listing's own maxima -- {{ring.dt_max}} degrees, 15 volts, the internal
resistance -- and those three effects are fixed. The rest follows from them.

    {{ring.constants}}

The first finding is the box: **the module's real maximum is
{{ring.true_w}} watts, not {{ring.listed_w}}.** And that maximum is only
reached with *no* temperature difference across the module -- cold face as
warm as the hot face, which is a module cooling nothing in particular.

Now mount it. The hot face goes onto a finned sink with a fan, outside the
room, at {{ring.out_t}} degrees. The cold face goes onto a smaller wet sink in
the room's air, at {{ring.room_t}} degrees and {{ring.room_rh}} percent. Both
sinks resist the heat, so the hot face settles at {{ring.hot_c}} degrees and
the cold face at {{ring.cold_c}}. The module now draws {{ring.amps}} amps,
inside the listing's 4 to 4.6. It moves **{{ring.q_each}} watts** of heat out of
the room for {{ring.draw_each}} watts of electricity, counting its two fans.

The room's dew point that day is {{ring.dew_c}} degrees, so the cold face is
{{ring.under_k}} degrees under it. It condenses -- but only
{{ring.latent_pct}} percent of the heat it takes is water. The rest just cools
the air. That is {{ring.water_each}} litres a day from one module.

## Slower is better, until it stops condensing

<!-- concept: cabin_seam_climate/volts -->

A Peltier is far more efficient run gently. Most of what the electricity does
at full drive is heat the module itself, so halving the voltage roughly halves
the cooling but cuts the draw to well under half:

    {{ring.volts_table}}

At 3 volts a module moves {{ring.v3_cop}} watts of heat for every watt it
draws; at 12, {{ring.cop}}. So throttle it -- with one catch, which the table
makes plain. At 6 volts the cold face only reaches {{ring.v6_cold}} degrees,
*above* the dew point, and the water column goes to {{ring.v6_water}}. A plate
that does not get under the dew point is a cooler, not a dehumidifier. The
most water for each kilowatt hour comes at {{ring.best_v}} volts:
{{ring.best_lpk}} litres.

And here the module meets the dew-point controller of Chapter {{ch.dewpoint}},
which asks for the plate {{clim.below}} degrees under the dew point: on this
day, {{ring.setpoint_c}}. **Mounted, at full drive, the module cannot get
there.** It stops at {{ring.cold_c}}, {{ring.short_k}} degrees short, so a
controller chasing that setpoint simply runs it flat out all day. A
module this size, on sinks this size, cannot reach that setpoint in humid
weather. The useful setting is the opposite one: cap the drive at
{{ring.best_v}} volts. Ten then make {{ring.v9_water}} litres a day for
{{ring.v9_kwh}} kilowatt hours, against {{ring.water}} for {{ring.kwh}} at
full drive.

## A day of ten

<!-- concept: cabin_seam_climate/day -->

Run ten at 12 volts, all day and all night, in three kinds of weather. Against
them, put what the room takes on: two people breathing and cooking and washing,
and the fresh air of Chapter {{ch.breathe}}, which on a humid day carries water
in with it.

    {{ring.weather_table}}

On the humid day, ten plates take {{ring.cooling_w}} watts of heat out of the
room and {{ring.water}} litres of water out of its air. The room takes on
{{ring.load_water}} litres: {{ring.people_water}} from two people breathing,
{{ring.vent_water}} on the fresh air, and the rest from cooking and washing.
**The ring removes about {{ring.water_pct}} percent of the day's water.** It
helps; it does not keep up.

The heat side is better than it looks. The people and the fresh air put in
{{ring.load_heat}} watts, and the ring takes out {{ring.cooling_w}}. But the
table leaves out the sun on the shell, which is the largest load of a summer
afternoon. Against that, {{ring.cooling_w}} watts is a fan's worth.

One rule from Chapter {{ch.metal}} matters more here than anywhere: **the hot
faces go outside.** Ten modules throw {{ring.outside_w}} watts out of their hot
faces -- every watt they took from the room plus every watt they drew. Mount
them with the hot faces inside, and the ring is a {{ring.draw_w}}-watt heater
that happens to drip.

## Feeding it on the sun

<!-- concept: cabin_seam_climate/sun -->

Ten stations draw {{ring.draw_w}} watts, all day and all night. That is
{{ring.kwh}} kilowatt hours a day. The sun only outruns the load for about
{{ring.window_h}} hours, so {{ring.night_kwh}} of those kilowatt hours have to
come off a bank. The array has to make the day's use and refill the bank,
from {{ring.sun_hours}} peak sun hours. For twenty-four hours a day to mean
it, the bank has to cover one sunless day as well as the night.

    {{ring.plan_table}}

:::box against
**About {{ring.array_w}} watts of panels and a {{ring.bank_kwh}} kilowatt-hour
bank: ${{ring.total_usd}}, for ${{ring.modules_usd}} of modules.** The array and
bank are rated at the prices declared everywhere else in this book. Nothing
was chosen to make this look bad.
:::

The comparison that settles it: a small compressor dehumidifier removes the
same {{ring.water}} litres for about {{ring.dehum_kwh}} kilowatt hours; the
ring takes {{ring.times_dehum}} times that. And the smallest window air
conditioner sold moves {{ring.ac_cool_w}} watts of heat for
{{ring.ac_draw_w}} -- {{ring.ac_cop}} watts moved for every watt drawn,
against the ring's {{ring.ring_cop}}.

## What to do instead

<!-- concept: cabin_seam_climate/instead -->

The plates are not wrong. They are the only part of this design that can take
water out of a seam that will not dry itself -- warm, still, humid weeks, with
the desiccant full and outside air no help. Keep them for that.

- **Run them on daylight surplus**, not off the bank. At {{ring.day_hours}}
  hours a day the ring uses {{ring.day_kwh}} kilowatt hours, all of it power
  the array was making anyway, and drops {{ring.day_litres}} litres. That is
  the figure Chapter {{ch.seam_module}} now carries, and it costs no extra
  battery.
- **Cap the drive at {{ring.best_v}} volts**, and let the controller switch the
  plates on and off rather than chase a setpoint they cannot reach. Past
  that, every extra watt mostly cools the air rather than drying it.
- **Put the plates where the air is wettest.** Wet air gives up a bigger
  share of a plate's heat as water. At the rim, the fresh air of a muggy day
  meets the plate before it meets the wood -- Chapter {{ch.metal}}'s rule.
- **For the house, buy the compressor.** If the room itself needs drying or
  cooling for weeks at a time, a dehumidifier or the smallest air conditioner
  does it for a fraction of the power. The plates look after the frame; the
  compressor looks after the people.
