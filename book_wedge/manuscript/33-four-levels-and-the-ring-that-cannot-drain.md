---
chapter: 33
title: Four Levels, and the Ring That Cannot Drain
strand: explain
status: draft
target: 1960
updated: 2026-09-30
---

# 33. Four Levels, and the Ring That Cannot Drain

The owner of this design describes the dome in levels. The first ring is the
floor. Above it is the band of triangles that stands on the floor. Above that,
the band that meets the pentagon round the crown. At the top, the cap. And the
question that goes with it: should each level of seam do a different job?

It should, and the solver says which.

![The seams, coloured by the band they run in.](plate-levels.png)

## The levels, counted from the solve

The dome's {{dome.vertices}} corners stand at five heights, not four:
{{clim.rim}} on the rim; a belt of {{clim.belt_low}} and {{clim.belt_high}}
corners that zigzags between two slightly different heights; {{clim.penta}}
round the crown; and the apex. The zigzag is what makes it five rather than four,
and it matters, as you will see.

The {{dome.seams}} seams run between those heights, and they fall into five
bands. What decides each band's job is its slope:

    {{clim.bands_table}}

Read down the last column. Four bands slope, so water in them runs downhill to
the rim. One does not.

## The ring that cannot drain

The {{clim.pentagon_seams}} seams round the crown -- the pentagon ring -- are
dead level. Every one of them runs between two corners at exactly the same
height. Water that gets into them does not go anywhere. It stands in a wooden
seam at the top of the building until it evaporates, and it evaporates into
the wood.

**So the pentagon ring carries air, never water.** Which suits it, because air
wants to be there: warm, humid air rises to the crown. The pentagon ring is the
natural **exhaust manifold** -- a closed loop of channel at the top of the room,
touching every seam above the belt -- and the cap's {{clim.cap_seams}} seams
carry that air on up to the apex vent.

The belt is the opposite surprise. Its {{clim.belt_seams}} seams rise at only
{{clim.belt_slope}} degrees, which looks like another level ring. But because
the belt zigzags, it has {{clim.belt_low}} low corners, and every one of its
seams runs downhill to one of them. **Each low corner of the belt is a drain
point**, and the rosette there (Chapter {{ch.channel}}) is where the belt's
water leaves.

![The pentagon ring is dead level; the belt's five low corners drain it.](plate-dead-level.png)

## Condense low, drain at the rim

<!-- concept: cabin_seam_climate/rim -->

The owner's first instinct was to put the condensing plates on the first ring,
where the frame meets the floor. That instinct is right, and the reason is
gravity.

Condensate falls. A plate at the rim drops its water straight into a drain at
one of the {{clim.rim}} rim corners, with no seam for it to travel through on
the way. A plate at the crown sends its water down the whole height of the
dome inside the frame, which is the one place you least want water travelling.

The lower band's {{clim.lower_seams}} seams, at {{clim.lower_slope}} degrees, are
the steepest in the building. They are the drains, and they are the path dry
air takes up from the rim ports into the frame.

## Rain does not come in through the ridge

Chapter {{ch.seam_module}} described **a slot along the outer cap of every
seam** taking rain in at the ridge, with a gutter under it. That was wrong, and
this book corrects it here rather than quietly changing the earlier chapter.

Three things are wrong with it. The slot is an opening into the structure along
the entire length of every seam, on the face of the building the weather
hits. Water taken in at the crown has to travel the whole height of the frame
to get out, and on the pentagon ring it cannot get out at all. And every foot
of seam that carries liquid water is a foot of wood with a leak waiting next to
it.

**Rain belongs outside.** Let it run off the cap -- the one watertight layer of
Chapter {{ch.one_layer}} -- to a gutter round the rim, outside the frame, and
from there to the tank. The roof still delivers
{{cond.gallons_per_inch}} gallons an inch; it just never enters a seam to do it.
The only liquid water inside the channels is condensate, and it is made at the
rim, where it has no distance to go.

<!-- concept: master/ms_math_water -->

And the rim gutter is a water plant. The cap's brim throws rain off a ring wider
than the dome, and collecting what falls on that ring is the whole design:

    {{work.water}}

No pump and one downpipe: the roof shape does the collecting. (Those figures use
the films' declared rainfall and cap brim, not a measurement of any one site.)

## Warm air rises, and the fan still does the work

<!-- concept: cabin_seam_climate/stack -->

Warm air rising is free, so use its direction: take air in low at the rim ports
and let it out high at the pentagon ring and the apex.

But do not count on its strength. With the inside ten degrees warmer than the
outside, the height of this dome produces {{clim.stack}} pascals of pull between
the rim and the apex. The barrier fan of Chapter {{ch.seam_module}} holds
{{air.pressure}}. The chimney effect helps the fan along; it does not replace
it, and on a summer afternoon it runs the wrong way.

## A tube around the bottom

<!-- concept: build/air_origin -->
<!-- concept: build/air_direction -->
<!-- concept: build/air_caveats -->

A dome has an unhelpful habit: warm air, and anything it carries, rises to the
apex and stays there. The answer that came out of a badly ventilated workshop
dome is a tube right round the base, on a blower, so the whole perimeter is one
duct instead of the building having one extract point on one wall.

Run it either way. Push air in at the ring and it leaves through the upper shell
and the pentagon ring, carrying fumes out through the whole surface. Reverse it
and outside air is drawn in through the shell, warming against the structure on
its way: a breathing wall, or dynamic insulation. Same hardware, one switch.

The flows are computed (Chapter {{ch.hats}}); the wall is not. Direction decides
it, because pushing warm, wet air outward through a cold wall condenses it inside
the wall -- exactly the failure Chapter {{ch.dewpoint}} exists to prevent -- and a
sealed skin cannot breathe at all, so any permeable band has to be designed in.

## The layout

<!-- concept: cabin_seam_climate/plan -->

Put together, every level has one job:

- **the rim** -- the ports in and out, the condensing plates, the drains, the
  two desiccant drawers of Chapter {{ch.desiccant}};
- **the lower band** -- air up, water down;
- **the belt** -- its low corners drain it;
- **the upper band** -- air up toward the crown;
- **the pentagon ring** -- the exhaust manifold, air only;
- **the cap** -- the apex vent.

Sensors inside, outside and in the seam read temperature and humidity; a pin in
the wood reads its moisture; a switch on the cap says whether it is raining.
Chapter {{ch.dewpoint}} is what they feed.
