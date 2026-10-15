---
chapter: 23
title: What the Work Costs the Body
strand: explain
status: draft
target: 1880
updated: 2026-10-03
---

# 23. What the Work Costs the Body

<!-- concept: line/why -->
<!-- concept: line/bottleneck -->

Chapter {{ch.nine}} counted the work as operations. This chapter counts it as
food.

The study it comes from is not this book's dome. It is a factory line building a
larger product dome, followed part by part through fifteen stations, with two
people at each one:

    {{en.product}}

A line does not reduce the work; one crew doing every station does exactly the
same labour. What a line buys is less **waiting**: split the work across
stations and a dome comes off the end every cycle instead of every build. And
the line runs at the speed of its slowest station -- there, the frame. Speeding
up any other station buys nothing. The lessons below hold for any build where
people place parts, including one person building this book's dome in a field.

## Six motions

<!-- concept: line/cycle -->
<!-- concept: line/walk -->
<!-- concept: line/carry -->
<!-- concept: line/position -->
<!-- concept: line/fasten -->
<!-- concept: line/allowance -->

Whatever the part, the body does the same six things with it. It **walks** to the
stockpile empty. It squats, grips and **lifts**. It **carries** the load to where
it goes. It **positions** it. It **fastens** it. It **recovers**, straightening up.

Four results from following those motions through the whole building:

- **The walk is cheap per trip and not cheap in total.** Which is why where the
  stockpile sits is a decision, not a detail left to whoever unloads the truck.
- **Carrying is not linear in the load.** The published equation for walking
  with a load has its load term squared: twice the weight costs more than twice
  the energy. That one fact is the argument for carts, conveyors and a closer
  stockpile.
- **Height changes the price.** Above {{en.overhead_m}} metres the arms are above
  the heart, the posture costs more and the crew tires faster. How much of a
  shell falls into that band is decided by its geometry -- a design decision
  disguised as a shape.
- **Fastening is almost the whole bill.** It raises nothing, does no work against
  gravity, and still consumes most of what the crew burns, because it is minutes
  per part of holding a posture, gripping a tool and resisting its torque. The
  body pays for holding still.

And the rest is not slacking. Industrial engineering has added a recovery
allowance to every task time for a century, with more for overhead work, because
a schedule written without one is a schedule that will not be met.

![Walk, lift, carry, position, fasten, recover.](plate-six-motions.png)

## The body is the heaviest thing you lift

<!-- concept: line/skeleton -->
<!-- concept: line/selflift -->
<!-- concept: line/limbs -->
<!-- concept: line/lift -->
<!-- concept: line/team -->
<!-- concept: line/overhead -->

To cost a movement you have to know what is being moved, and the biggest thing
moved is the worker. The model uses the standard anthropometric tables of
biomechanics, built for a {{en.body_kg}} kg person: each body segment a fixed
share of the total mass. The trunk alone is about half of it. So in every
placement the body rises and falls along with the part, and outweighs it several
times over. Split by limb, across the whole building:

    {{en.by_limb}}

The arms get the attention because they are what you watch, but the back does the
work -- and the back is where the injuries are. That is the honest case for a
lower stockpile, a taller bench, and parts presented at waist height.

Above {{en.two_person_kg}} kilograms, manual-handling guidance says a lift takes
two people, and the model splits every such part between them. Work above the
shoulders costs more per second and needs more recovery for the same output, and
whenever the geometry pushes work up there, the cost lands on a body rather than
a spreadsheet.

![The trunk does most of the lifting.](plate-trunk-work.png)

## Exact, and modelled

<!-- concept: line/work -->
<!-- concept: line/model -->
<!-- concept: line/efficiency -->

One part of this is exact: raising a part is its mass, times gravity, times the
height it rises. No estimate anywhere in it.

Turning that into food is a model, and it says so. A muscle holding a panel steady
does no mechanical work and still burns fuel, so there is no route from joules of
lifting to kilocalories without published figures for how hard each task is. The
model names every one it takes on authority:

    {{en.constants}}

That is why two very different efficiencies are both true:

    {{en.mechanical}}

During a lift itself, a good share of the fuel becomes height, close to what
muscle can manage. Across the whole building, mechanical work is a fraction of a
percent of the food, because almost none of a working day is spent lifting.

## The ledger

<!-- concept: line/motions -->
<!-- concept: line/stations -->
<!-- concept: line/shift -->
<!-- concept: line/food -->
<!-- concept: line/recap -->

Every motion of every part, totalled:

    {{en.energy}}

    {{en.by_motion}}

Station by station, the energy follows the part count and the time, not the
tonnage: a station placing many light pieces slowly costs its crew more than one
placing a few heavy ones quickly. This is the table to read when deciding where a
jig, a lift assist or an extra pair of hands would change someone's day:

    {{en.by_station}}

And the total, in food, because until now it was on no drawing of the building:

    {{en.in_food}}

The parts that look like effort turned out to be cheap. The part that looks like
nothing -- holding a position while fastening -- is almost the whole bill. So
design the posture, not just the part.
