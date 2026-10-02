---
chapter: 59
title: The Roof Is Already a Gutter
strand: explain
status: drafting
target: 1540
updated: 2026-09-17
---
# 59. The Roof Is Already a Gutter

*An overhanging brim throws water clear of every joint and collects it in the same move, and the annual catch off a dome this size is not a trivial number*

## The Roof Is Already a Gutter

The brim around a dome -- the overhanging ring of the hat -- looks like
decoration. It is not. It is the detail that keeps water out of the building,
and it does two jobs at once.

The first job is the boring one that matters most. Rain runs down a dome
shell, and without a brim it runs straight into the ring of joints at the
base: the seams, the brackets, the screws, the point where timber meets
footing. Every one of those is a place water can sit, wick and work on the
frame for years. The brim throws all of it clear of the wall before it ever
gets there.

The second job is the one this chapter is about. The same overhang is a
catchment. It catches the rain it throws, and the annual number off a dome
this size is {{brim.gallons_yr}} gallons. Not a trivial number, and it costs
no extra roof to collect it, because the roof was already a gutter.

## Where the water goes, with and without a brim

Follow one raindrop through both buildings.

**Without the brim.** The drop lands on the upper shell, runs down a panel,
across a seam, down onto the lower panels and off the rim -- straight onto
the base joints and the splash line at the bottom of the wall. Some of it
wicks into the seam keys. Some of it follows the brackets down the inside
face. Over a wet season the bottom ring of the frame is damp more often than
it is dry, and the footing is in a permanent puddle of its own making. The
building is not leaking into the room. It is leaking into its own skeleton.

**With the brim.** The same drop lands on the shell, runs down to the hat,
and hits the overhang. The hat's edge is further out than the wall --
{{brim.catch_ft}} feet from the centre, against {{brim.rim_ft}} feet for the
rim of the hat itself -- so the drop leaves the building at a point where
there is nothing below it but ground. It drips clear. The base joints stay
dry because the rain never arrives.

The brim does not stop at dripping clear. Put a gutter lip on the hat's edge
-- the same metal the hat is already made of -- and the drip becomes a
stream, and the stream runs into a tank.

The lip is also the only gutter this building will ever have, and it wants the
same care as any gutter. Leaves, needles and dust wash down the shell and
arrive at the lip, and a gutter is a gutter -- it clogs where the downpipe
narrows. This one is a ring at the hat's edge, so the autumn job is a walk
round the building with a ladder and a broom. In snow country the brim is a
flat shelf that holds ice, and an ice dam on the hat can weigh more than the
metal was priced for.

One of those two buildings has a water system. The other has a slow leak into
its own frame. The difference is the width of the hat, {{brim.overhang_in}}
inches.

Wider is not automatically better, and this is the place to say why, because
it is the same trade everywhere on the shell. A wider brim catches more --
every extra inch of radius is real catchment -- and it also catches more
*wind*, and it shades more wall, which is a virtue in summer and a cost in
winter. The {{brim.overhang_in}} inches this book prices is the width that
clears the wall, shades the windows, and stays on the right side of the wind
math. The number is a choice, declared once and used everywhere, not a
discovery.

## The annual catch

The catch is worth working out properly, because the number sounds like a
mistake the first time you see it.

The inputs, all declared before they are used: {{brim.rain_in}} inches of rain
a year, the regional average; a runoff coefficient of {{brim.runoff_pct}} per
cent, which is what a metal roof sheds -- the rest evaporates, splashes and
never reaches the lip; and the {{brim.floor}} square foot reference dome,
whose hat stops at a plan radius of {{brim.rim_ft}} feet.

The catchment is not the sloped area of the hat. Rain falls straight down, so
what catches it is the *plan* area -- the circle the brim's edge describes
over the ground. At {{brim.overhang_ft}} feet of overhang that circle is
{{brim.catch_sqft}} square feet.

Now the arithmetic. {{brim.rain_in}} inches times {{brim.gal_per_in}} gallons
per square foot per inch of rain, times {{brim.catch_sqft}} square feet of
catchment, times the {{brim.runoff_pct}} per cent that actually sheds:

**{{brim.gallons_yr}} gallons a year. {{brim.gallons_day}} gallons a day, on
average.**

It is worth saying what that number is not. It is not metered -- nobody has
stood under this dome with a bucket for a year. The rainfall is a regional
average, not a guarantee, and a drought year is exactly the year the catch
goes dry. But the arithmetic is the honest plan-view arithmetic, with every
efficiency declared on the line rather than buried.

Size the tank against use rather than rain. Two people at
{{brim.use_gal_day}} gallons a day empty a {{brim.tank_gal}} gallon tank in
{{brim.tank_days}} days -- so a full tank is a three-week buffer against a dry
spell, and in an ordinary year it refills {{brim.gallons_day}} gallons a day.

At utility prices the whole year's water is worth about {{brim.value_yr}}
dollars. Say it plainly: collected rain is nearly free water either way, and
the money argument is a weak one. The real argument is the {{brim.tank_days}}
days of water that keep flowing when the well does not. That is what the
number buys.

The same {{brim.gallons_yr}} gallons appear in the ten-points list at the
end of the films, computed by this same function. That is not a coincidence
and it is not a copy: the film and this book read the one water model, so
they cannot drift apart. Wherever you meet this number, it is the same
dome, the same rain, the same arithmetic.

## What the catch is actually good for

The honest uses first, because the dishonest one gets said first everywhere
else.

**Not drinking, without treatment.** Rain off a roof has been through bird
droppings, dust and whatever the shell sheds, and the tank is warm and dark,
which is a polite description of a biology experiment. Filter and treat it or
keep it out of your mouth.

**Everything else.** Irrigation is the obvious one, and the dome's own
garden sits in its shadow. Flushing and washing take the {{brim.gallons_day}}
gallons a day without a second thought. And the quiet use that matters most on
a rural site: a buffer against a dry well. A well that fails in August is a
crisis with an empty tank and an inconvenience with a full one.

The tank belongs under the pad, not beside it. Three reasons, all boring and
all true. The pad is already excavated, so the hole is half dug. The ground
under a pad is shaded and frost-protected by the pad itself, so the tank
neither cooks in summer nor splits in winter. And the weight sits on
compacted ground that is already carrying a building, instead of in a
second hole you had to dig and backfill for no other reason.

Two details make the difference between a tank and a pond, and both are
cheap compared to the misery they prevent. A first-flush diverter -- a
simple standpipe that captures the first few gallons of every storm, the
ones carrying the dust and the droppings, before the clean water is allowed
into the tank. And an overflow, sized like it is going to be used, because
{{brim.rain_in}} inches of rain will overflow any tank ever built and the
water has to go somewhere that is not the pad. Skip either and the tank
teaches you the lesson within a year.

The plumbing between the lip and the tank is simple, and it has two jobs nobody
thinks about until the tank overflows. A leaf screen at the lip keeps the big
stuff out of the pipe, because the first-flush diverter catches only the first
of the dirt, not the last. One downpipe carries the whole ring's
{{brim.gallons_day}} gallons a day down the wall and under the pad to the tank,
and it wants an air gap so a full tank cannot back up into the pipe and out the
lip. That is the whole of the plumbing: a screen, a pipe, a gap.

One more job the brim does that is worth a line, because it is free with the
same metal: shade. The overhang keeps the summer sun off the upper wall in
the middle of the day, and it keeps the rain off the base ring all year.
Every one of those jobs is done by a piece of the building that was already
there, doing the first job -- keeping the frame dry.

That is the whole point of this chapter. The gutter is not an accessory a
dome can have. It is the brim the dome already wears, and the only question
is whether you let the water run off it or into a tank.
