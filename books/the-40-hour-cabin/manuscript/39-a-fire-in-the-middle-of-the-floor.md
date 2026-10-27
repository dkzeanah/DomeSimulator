---
chapter: 39
title: A Fire in the Middle of the Floor
strand: explain
status: draft
target: 2020
updated: 2026-10-27
---

# 39. A Fire in the Middle of the Floor

<!-- concept: cabin_irori/purpose -->

For centuries, Japanese farmhouses were built round a hole in the floor. The
*irori* is a sunken hearth: a square pit lined with stone, filled with ash,
burning charcoal, in the middle of the main room. The family cooked over it,
warmed themselves at it, worked by its light and sat round it every evening.

A dome has its middle exactly where an irori wants to be -- straight under the
apex, the point furthest from every wall. So this chapter puts one in the
solver's dome and checks, figure by figure, what fits and what does not. Most of
it fits beautifully. One part does not, and the chapter says so.

The description of the irori here is a paraphrase of *{{iro.source}}*. The
dome's figures are the solver's. No fire was lit or measured for any of it.

## The pit

<!-- concept: cabin_irori/hearth -->

A wooden border frames the opening, wide enough to stand a cup on. Inside it,
stone lines the pit, and a deep bed of ash fills it. The charcoal sits in the
ash.

The ash is what makes it work. It keeps the heat off the floor beneath. It lets
you bank the fire for the night and find it alive in the morning. Food was
buried in it to roast, a flask of sake warmed in it, and fish on skewers stood
up in it round the coals.

The pit in the film is {{iro.hearth_side_m}} metres across inside, with a
{{iro.frame_w_m}} metre border: a size chosen for a three-metre dome, not a
traditional standard. Irori were sized to the house and the region.

## The hook that hangs from the apex

<!-- concept: cabin_irori/hook -->

The pot hangs from a *jizaikagi*: an iron rod inside a bamboo tube, held by a
lever that is very often carved as a fish. Lift the kettle and the fish tilts
and lets the rod slide; let go and friction locks it. Raise the pot to simmer,
lower it to boil, with one hand and no tools.

In a farmhouse it hung from a beam. In the dome it hangs from the apex hub, the
one point every member climbs to. The solver puts that hub {{iro.apex_m}}
metres ({{iro.apex_ft}} feet) above the floor. With the hook working at
{{iro.pot_hang_m}} metres, the assembly spans **{{iro.rod_m}} metres
({{iro.rod_ft}} feet)** from hub to hook -- longer than most beams ever asked of
one, which is a bamboo tube of a good length and a cord to lash it.

![The pothook, hung from the apex hub.](plate-irori-hook.png)

## Seven jobs for one fire

<!-- concept: cabin_irori/jobs -->

The irori did six jobs at once, and gave the house a seventh:

1. **Heat.** From the middle of the room, it warmed all of it.
2. **Cooking.** The pot on the hook; the fish in the ash.
3. **Light.** Before lamps, it was the room's night light.
4. **Drying.** A lattice above it dried clothes, food and green wood.
5. **Keeping fire.** Its coals were kept alive to light every other fire, in the
   days before matches.
6. **Gathering.** Meals and evenings happened round it.
7. **The house itself.** Its warm air dried the timbers; its smoke coated them.

A lamp and a match have taken jobs three and five. The other five are the
chapter.

## Everyone has a place

<!-- concept: cabin_irori/seats -->

Each person had a fixed seat, and the seats carried the household's order. The
*yokoza*, on the far side from the entry, belonged to the head of the household.
The two sides went to the head's wife (the *kakaza*) and to guests (the
*kyakuza*). The *kijiri*, nearest the entry and the firewood, was the lowest
seat, often the children's. Names and customs varied from region to region.

A round room with a centre is already arranged for this. In the film the entry
side is the one facing the camera; the Cabin World's dome has no door cut yet,
so that is a staging choice, not a plan.

![Four seats, the lowest by the entry.](plate-irori-seats.png)

## What the circle costs the floor

<!-- concept: cabin_irori/inputs -->
<!-- concept: cabin_irori/fit -->

Before the fit, the inputs that were chosen rather than measured, marked by
kind:

    {{iro.constants_table}}

The solver's dome stands on a {{iro.sides}}-sided base with {{iro.floor_m2}}
square metres of floor ({{iro.floor_ft2}} square feet). The hearth with its
border is {{iro.hearth_m}} metres square, **{{iro.hearth_pct}} per cent** of
that floor. That is the flattering number.

The honest one counts the people. The hearth and four people sitting round it
need a square {{iro.circle_m}} metres on a side: {{iro.circle_m2}} square metres,
**{{iro.circle_pct}} per cent of the floor**, in the middle, where nothing else
can go. A bed cannot cross it. A table cannot stand in it. In a room this size,
the gathering is a quarter of the house, and it should be chosen as one.

It does fit. The seat backs stop {{iro.seat_room_m}} metres short of the base
ring, and a seated head clears the frame by at least {{iro.headroom_m}} metres,
because the seats are near the centre, where the shell is high.

## Warm air and wet wood

<!-- concept: cabin_irori/dry -->

The article claims the irori's warm air lowered the moisture in the house's
wood and slowed its decay. That is the one claim about the building this book
can compute, with the same arithmetic as Chapter {{ch.dewpoint}}.

Take outside air at {{iro.out_t_c}} °C and {{iro.out_rh}} per cent humidity --
a damp shoulder-season day -- and warm it to {{iro.in_t_c}} °C without adding
or removing any water. Its relative humidity falls to **{{iro.rh_in}} per
cent**. The Wood Handbook's equilibrium formula says wood left in the cold, damp
air settles near **{{iro.emc_out}} per cent** moisture, and wood in the warmed
air near **{{iro.emc_in}} per cent**.

Decay fungi need wet wood, and Chapter {{ch.skin}} is about nothing else. So
the direction is right, and by a wide margin. Two cautions: equilibrium is where
the wood ends up after weeks, not how fast it gets there; and the warmth does
the drying, not the fire. Any heat source in the room earns the same credit.

## The rack overhead

<!-- concept: cabin_irori/hidana -->

Above many irori hung a wooden lattice, the *hidana*. Clothes, food and green
wood dried on it in the rising heat, and it broke up sparks before they reached
the thatch.

The dome has a ready place for one. The ring of five hubs just below the apex is
directly above the hearth, so four cords to four of those hubs carry the lattice
level, above a standing head. Keep everything on it well clear of the fire, and
nothing that drips.

## The smoke, and the number that argues against it

<!-- concept: cabin_irori/smoke -->
<!-- concept: cabin_irori/co -->

The article makes a second claim about the building: tar in the smoke soaked
into the beams and thatch and helped keep insects and water out. That is the
source's claim and this book has not tested it. The article also names the
cost: the smoke filled the house and caused eye disease and other illness.

Watch where smoke goes in a dome. A thatched roof leaks smoke everywhere. A dome
gathers it under the apex -- the one place this book has worked hardest to seal.

:::box against
The number that argues against it: the solver's dome holds
**{{iro.volume_m3}} cubic metres of air ({{iro.volume_ft3}} cubic feet)**. A
farmhouse with an irori was tall, open to its roof and leaky by design; this
book spends a whole Part making the dome tight. Charcoal burns with little
visible smoke, but it makes carbon monoxide, which you cannot see or smell, and
burning charcoal in a closed room is a known cause of carbon-monoxide poisoning.
**Do not burn an open charcoal irori in a sealed dome.**
:::

## Keep the circle, give the fire a chimney

<!-- concept: cabin_irori/flue -->
<!-- concept: cabin_irori/under -->

The fix keeps everything people loved about the irori and removes the smoke. A
steel hood over the pit, its underside {{iro.hood_m}} metres up, and a flue
straight up through the apex: **{{iro.flue_m}} metres ({{iro.flue_ft}} feet)**
of pipe from hood to hub before it leaves the shell. The apex is already the
dome's one designed penetration, the same exit this book gives a wood stove.

- **Use a listed appliance or a design an inspector will approve**, and follow
  its clearances to the timber. A frame of split wood is fuel.
- **Give the fire its own combustion air**, by its own duct. Chapter
  {{ch.desiccant}} says the same for a stove: its heat, never its air, and never
  its flue anywhere near the seams.
- **Fit a carbon-monoxide alarm.** Not optional.
- **The hook can hang beside the hood or from it.** The pot keeps its place.

The pit itself needs a word, because the Cabin World's floor stands on piers
with air beneath it. The pit cannot be dug into the ground; it becomes a box
framed into the floor, hanging between the joists. The film's is
{{iro.pit_depth_m}} metres deep, which leaves room under the pad. It must be
noncombustible, separated from the framing, and hold the ash bed that keeps the
heat off the floor. How it is lined, how far it stands off the joists and how it
is carried are for the appliance's instructions and your local code, not this
book.

![Keep the circle, give the fire a chimney.](plate-irori-flue.png)

<!-- concept: cabin_irori/close -->

So the irori and the dome agree about almost everything. Both put the fire in
the middle. The hook hangs from the apex, the drying rack from the ring below
it, and four people sit round it with room behind them, at the cost of
{{iro.circle_pct}} per cent of the floor -- the price of the gathering, paid on
purpose. What does not carry over is the open smoke. Give the fire a hood, a
flue and an alarm, and you keep the oldest arrangement of a home: everyone
facing the same fire.
