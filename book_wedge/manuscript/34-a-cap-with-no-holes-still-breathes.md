---
chapter: 34
title: A Cap With No Holes Still Breathes
strand: explain
status: draft
target: 2140
updated: 2026-10-03
---

# 34. A Cap With No Holes Still Breathes

<!-- concept: cabin_seam_climate/correction -->

The cap of Chapter {{ch.one_layer}} is one watertight layer over the whole
frame, and that is its whole job: nothing gets through it. But a dome that
nothing gets through is a sealed jar with people in it. They breathe, cook and
wash, and every one of those puts water into the air. With nowhere to go, that
water waits for the coldest surface in the building and condenses on it -- and
in a timber dome the coldest surface is the frame.

So a watertight dome must still breathe. The question is how air gets in and
out without making a way in for rain.

:::box correction
The usual answer is a vent at the top. It is the wrong answer here: a hole in
the roof, at the place the weather hits hardest, with the frame right under it.
This book's own layout in Chapter {{ch.levels}} let the exhaust out through an
apex vent in the cap, and that is corrected here.
:::

**The cap is never opened.** The room's air is taken in at the crown, *inside*
the shell, under the cap. It goes down the seam channels, inside their printed
keys. It leaves at the bottom of the dome, through ports that face the ground.
Fresh air comes in at the bottom the same way. Holes through the cap above the
rim: **{{vent.holes}}**.

![The cap is unbroken; the air goes down the seams and out at the bottom, facing the ground.](breathing-cap.png)

## In at the crown, down the seams, out at the bottom

<!-- concept: cabin_seam_climate/crown -->
<!-- concept: cabin_seam_climate/down -->

**Why take it from the top.** Warm air rises, and the warmest air in a room is
also the wettest and the stalest: it is the breath and the steam, carried up.
In a dome it all collects at the crown. A grille there, under the cap, takes in
exactly the air that most needs to leave.

**Why the seams.** The channel inside every key is already a duct (Chapter
{{ch.channel}}), and it runs from the crown to the floor. The solver's own
seams show the route: **{{vent.falling}} of the dome's {{dome.seams}} seams fall
all the way from the apex to the rim** without ever climbing. The other
{{vent.level}} are the pentagon ring, dead level, and they stay out of the
falling path; their job is the one Chapter {{ch.levels}} gave them, a ring of
air joining the five paths so the flow shares itself evenly. The shortest
falling path is {{vent.path_ft}} feet, crown to rim, through two rosettes.

**There is room for it.** The dome needs {{vent.need_cfm}} cubic feet of fresh
air a minute. One empty channel carries {{vent.seam_cfm}} at a quiet speed, and
the five cap seams that every falling path starts in carry {{vent.cap_cfm}}
together -- **{{vent.headroom}} times the need**. The exhaust seams carry no
pipes or wires; the service seams of Chapter {{ch.channel}} are others.

**Why the ports face the ground.** Rain falls. An opening that faces down can
only take in water that has to climb to reach it, and an opening at the bottom
of the dome, under the brim of the cap, is out of the falling rain altogether.
It is also the lowest point of the path, so anything that does get in drains
straight back out. There are {{vent.outlets}} rim corners to put ports at.

## The air falls by itself in winter

<!-- concept: cabin_seam_climate/siphon -->

Here is the part that makes the direction more than a convenience.

In winter the room's air is warm, so it rises: the room itself carries the air
up to the crown grille. In the channel the exhaust gives its heat to the cold
shell, gets heavier than the room's air, and **falls**. Two columns side by
side -- a warm one rising in the room, a cool one falling in the seams -- make a
loop that turns itself, a siphon of air. How hard it pulls depends on how cold
it is outside:

    {{vent.table}}

At {{vent.winter_t}} degrees outside the falling air pulls with
{{vent.winter_pa}} pascals and carries **{{vent.winter_share}} per cent** of the
need with no fan at all. In cool weather it still carries
{{vent.cool_share}} per cent, and a fan adds the last {{vent.cool_fan}}
pascals. In summer sun the cap is hotter than the room, the channel air wants to
rise, and the siphon runs backwards: then a fan does it all, against
{{vent.summer_fan}} pascals. The small in-line fan of Chapter
{{ch.seam_module}} pushes {{vent.fan_static}}. The worst case is a rounding
error to it.

Chapter {{ch.levels}} said the chimney effect helps the fan and does not
replace it. That is true of air going up. Sent down, through a cold shell, in
the season a sealed house most needs to breathe, the falling air does the work
itself.

The inputs this depends on, declared:

    {{vent.constants}}

## The water goes the same way as the air

<!-- concept: cabin_seam_climate/water -->

When the channel is colder than the room air's dew point -- {{vent.dew}} degrees
for a room at the declared humidity -- the exhaust drops water inside the key:
{{vent.winter_water}} litres a day at {{vent.winter_t}} degrees outside,
{{vent.hard_water}} at {{vent.hard_t}}.

That water runs downhill, which is the way the air is already going, and it
leaves by the same ports. **The air and its water go out of the same door.**
This is the strongest reason the exhaust runs down and not up: sent up, the
water it drops would run back against the air and pool wherever the channel
levels off. Sent down, nothing pools. The one level ring in the building, the
pentagon ring, is not on the falling path at all.

And the wet air never touches the wood. It runs inside the printed key, so the
rule of Chapter {{ch.dewpoint}} -- keep every wood surface above the dew point of
the air that touches it -- is kept by construction: the air touching the wood
is the seam's still air, not the room's breath.

## Two ways in and out

<!-- concept: cabin_seam_climate/twoway -->

The dome breathes both ways, and both doors are at the bottom.

**Fresh air in** through its own ports at the rim, facing the ground, and into
the room low. The desiccant drawers and condensing plates of Chapter
{{ch.desiccant}} sit on this intake, at the rim, where their water has no
distance to fall.

**Stale air out** at the crown, down the seams, and out at the rim.

Fresh in low, stale out high: the room itself is the up-leg of the loop, and the
air in it is always moving gently from the floor toward the crown. Run the two
flows equal and the room is neither pressed nor pulled, so no air is shoved out
through the frame and none sucked in through it. The controller of Chapter
{{ch.dewpoint}} decides when each runs and how hard.

## Where it stops working

<!-- concept: cabin_seam_climate/limits -->

**Ice.** If the channel falls below freezing, the water in it freezes at the
outlet and closes it. With the channel halfway between inside and outside, that
happens below **{{vent.freeze}} degrees** outside. Where winters go that cold,
put a heat trace on the outlet stubs, or close the falling path and run the
exhaust through the rim drawers on the coldest nights.

**Snow.** A port facing the ground is useless under a drift. Keep the ports
above the snow line -- on the deck, or on the riser wall of Chapter
{{ch.raise}}.

**Insects and mice.** Every port gets a screen. A downward opening keeps the
rain out; it does not keep a wasp out.

**Summer.** The siphon runs backwards, and the fan carries the whole need. It is
a small fan and a small number, but it is not nothing.

**Cooking.** The path is long and the flow is gentle. A range still wants its
own hood, ducted out low and facing down, like everything else on this dome.
