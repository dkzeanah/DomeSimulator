# The Irori: A Sunken Hearth Under the Dome's Apex - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. A fire in the middle of the floor

Time: 00:00:00.000 - 00:00:34.300

The Japanese irori, under the wedge dome's apex.

For centuries, Japanese farmhouses were built around a hole in the floor. The irori is a sunken hearth: a square pit lined with stone, burning charcoal, in the middle of the main room. A dome has its middle exactly where an irori wants to be, straight under the apex. So we put one in the solver's dome and checked what fits and what does not. Most of it fits beautifully. One part does not, and we will show you that number too.

On-screen math:

- SOURCE: Irori, Wikipedia contributors (CC BY-SA 4.0; paraphrased, not quoted)
- Dome: the raw-wedge solver's 2V hemisphere
- No fire was lit or measured for this film

## 02. A square pit, lined with stone

Time: 00:00:34.300 - 00:01:12.600

Border, stone, ash and charcoal.

Here is the hearth in plan. A wooden border frames the opening and gives you a ledge for a cup. Inside it, stone lines the pit, and a deep bed of ash fills it. The charcoal sits in the ash. Ash is the insulation: it keeps the heat off the floor beneath and lets you bank the fire for the night. Food can be buried in it to roast, and skewered fish stood up around the coals. Our pit is 0.90 metres across inside, a size we chose for a three-metre dome.

On-screen math:

- Wooden border -> stone lining -> ash bed -> charcoal
- ASSUMED: pit 0.90 m inside; border 0.10 m
- Traditional sizes vary by house and region

## 03. The hook that moves the pot

Time: 00:01:12.600 - 00:01:54.100

The jizaikagi hangs from the apex hub.

The pot hangs from a jizaikagi: an iron rod inside a bamboo tube, with a lever that locks it. The lever is often carved as a fish. Lift the kettle and the fish tilts and lets the rod slide; let go and friction holds it. Raise it to simmer, lower it to boil. In a farmhouse it hung from a beam. In the dome it hangs from the apex hub, where every member climbs to. The solver puts the apex 2.96 m (9.7 ft) above the floor, so the hook assembly spans 2.66 m (8.7 ft) from hub to hook.

On-screen math:

- Iron rod in a bamboo tube; a fish-shaped lever locks it
- Solver: apex 2.96 m above the floor
- ASSUMED: hook 0.30 m above the floor
- Hub to hook = 2.96 - 0.30 = 2.66 m

## 04. Seven jobs for one fire

Time: 00:01:54.100 - 00:02:35.004

Heat, cook, light, dry, keep fire, gather -- and the house itself.

The irori did six jobs at once. It heated the whole room from the middle. It cooked. At night it was the light. A lattice above it dried clothes, food and firewood. Its coals were kept alive to light everything else, in the days before matches. And it was where the family gathered, every meal and every evening. There was a seventh job, for the building: its warm air dried the timbers, and its smoke coated them. Two of those jobs, light and keeping fire, are done better now by a lamp and a match.

On-screen math:

- Heating / Cooking / Lighting
- Drying / Keeping fire / Gathering
- + The house itself: The warm air helps a timber dome; the smoke is the part a tight dome cannot take.
- Light and keeping fire: done now by a lamp and a match

## 05. Everyone has a place

Time: 00:02:35.004 - 00:03:08.904

The seats round the hearth carried the household's order.

Each person had a fixed seat. The yokoza, on the far side from the entry, belonged to the head of the household. The seats on either side went to the head's wife and to guests. The kijiri, nearest the entry, was the lowest seat, often the children's, beside the firewood. Names and customs varied from region to region. A round room with a centre is already arranged for this, and in the dome the entry side is the one facing you.

On-screen math:

- YOKOZA: head of the household (far side, facing the entry)
- KAKAZA: the head's wife (one side)
- KYAKUZA: guests (the other side)
- KIJIRI: the children (the lowest seat) (the entry side)

## 06. Declare the inputs

Time: 00:03:08.904 - 00:03:49.688

Choices we made, put on screen before we use them.

Before we test the fit, here is what we chose rather than measured. A pit 0.90 metres wide inside, with a 0.10 metre border. 0.75 metres of floor for each person sitting at a side. A seated head height of 0.95 metres. A smoke hood with its underside at 1.80 metres. And for the drying test, outside air at 5 degrees and 90 percent humidity, warmed to 20 degrees. Change any of these and every figure after it changes with it.

On-screen math:

- ASSUMPTION: hearth_side_m = 0.9 m
- ASSUMPTION: frame_w_m = 0.1 m
- ASSUMPTION: pit_depth_m = 0.3 m
- ASSUMPTION: seat_depth_m = 0.75 m
- ESTIMATE: seated_head_m = 0.95 m
- ASSUMPTION: outside 5 C at 90% RH, warmed to 20 C

## 07. What the circle costs the floor

Time: 00:03:49.688 - 00:04:28.672

It fits. It also takes a quarter of the room.

The solver's dome stands on a 10-sided base with 25.7 square metres of floor, 277 square feet. The hearth with its border takes 4.7 percent of that. That is the flattering number. The honest one counts the people: the hearth and four seated people need a square 2.6 metres on a side, 26 percent of the floor, in the middle, where you cannot put a bed. It does fit: the seat backs stop 1.51 metres short of the base ring, and a seated head clears the frame by at least 1.54 metres.

On-screen math:

- Solver: floor 25.7 m2 (277 ft2), 10-sided base
- Hearth: 1.10^2 = 1.21 m2 = 4.7%
- Circle: 2.6^2 = 6.76 m2 = 26% of the floor
- Seated headroom: 2.49 - 0.95 = 1.54 m

## 08. Warm air dries the frame

Time: 00:04:28.672 - 00:05:10.172

The one claim about the building this book can compute.

The article says the irori's warm air lowered the moisture in the house's wood and slowed decay. That part we can work out. Outside air at 5 degrees and 90 percent humidity, warmed to 20 degrees with no water added, falls to 34 percent. The Wood Handbook's equilibrium formula says wood left in the cold, damp air settles near 21 percent moisture, and in the warmed air near 7 percent. Decay fungi need wet wood, so that is the right direction by a long way. It is where the wood ends up after weeks, not how fast it gets there.

On-screen math:

- RH warmed = 0.90 x es(5) / es(20) = 0.34
- EMC outside (5 C, 90%) = 21.0%
- EMC warmed (20 C, 34%) = 6.8%
- STANDARD: Hailwood-Horrobin fit, USDA Wood Handbook ch. 4

## 09. The rack overhead

Time: 00:05:10.172 - 00:05:46.472

A drying lattice, hung from the upper ring.

Above many irori hung a wooden lattice called the hidana. Clothes, food and green wood dried on it in the rising heat, and it spread out sparks before they reached the roof. The dome has a ready place to hang one. The ring of hubs just below the apex is directly above the hearth, so four cords to four of those hubs carry the lattice level, out of a standing person's way. Nothing on it should be anywhere near the coals, and nothing should drip into them.

On-screen math:

- Hidana: a lattice for drying and for catching sparks
- Hung 1.95 m above the floor from the solver's upper ring
- Keep combustibles clear of the fire

## 10. What the smoke did for a thatched roof

Time: 00:05:46.472 - 00:06:21.972

A claim from the source, and its cost.

The article makes a second claim about the building: tar in the smoke soaked into the beams and thatch and helped keep insects and water out. That is the source's claim, not something this film has tested. It also names the cost. The smoke filled the house and caused eye disease and other illness. Watch where the smoke goes in a dome. A thatched roof leaks smoke everywhere. A dome concentrates it under the apex, the one place this book has worked hardest to seal.

On-screen math:

- CLAIMED (source): smoke tar protected beams and thatch
- CLAIMED (source): smoke caused eye disease and other illness
- Not tested in this film

## 11. The number that argues against it

Time: 00:06:21.972 - 00:07:01.364

An open charcoal fire in a tight room.

Here is the number that argues against it. The solver's dome holds 47 cubic metres of air, 1,674 cubic feet. A farmhouse with an irori was tall, open to its roof, and leaky by design. This book spends whole chapters making the dome tight. Charcoal burns without much visible smoke, but it makes carbon monoxide, which you cannot see or smell, and burning charcoal in a closed room is a known cause of carbon monoxide poisoning. So, plainly: do not burn an open charcoal irori in a sealed dome.

On-screen math:

- Solver: 47.4 m3 (1,674 ft3) inside the facets
- Open charcoal fire -> carbon monoxide
- Tight envelope: no open fire without a flue

## 12. Keep the circle, give the fire a chimney

Time: 00:07:01.364 - 00:07:44.864

A hood and a flue through the apex.

The answer keeps everything people loved about the irori and removes the smoke. A steel hood over the pit, its underside 1.80 metres up, and a flue straight up through the apex: 1.16 m (3.8 ft) of pipe from hood to hub before it leaves the shell. The apex is already the dome's one designed penetration, the same exit this book gives a wood stove. Use a listed appliance or a design an inspector will approve, follow its clearances to the timber, give it a supply of combustion air, and fit a carbon monoxide alarm. The hook can hang beside the hood or from it.

On-screen math:

- Flue from hood to apex = 2.96 - 1.80 = 1.16 m
- Listed appliance or approved design; its clearances govern
- Combustion air + carbon monoxide alarm

## 13. A pit in a raised floor

Time: 00:07:44.864 - 00:08:23.564

The box between the piers.

The Cabin World's floor stands on piers, with air beneath it, so the pit cannot be dug into the ground. It becomes a box framed into the floor, hanging between the joists. Ours is 0.30 metres deep, which leaves room under the pad. It must be noncombustible and separated from the framing, holding the ash bed that keeps the heat from the floor. How it is lined, how far it stands off the joists and how it is supported are set by the appliance's instructions and your local code, not by this film.

On-screen math:

- ASSUMED: box 0.30 m deep; pad top 0.62 m above grade
- Noncombustible box; ash bed; separated from the joists
- Clearances and support: manufacturer and local code

## 14. A circle with a chimney

Time: 00:08:23.564 - 00:09:00.664

The irori's room, with the smoke taken away.

So the irori and the dome agree about almost everything. Both put the fire in the middle. The hook hangs from the apex, the drying rack from the ring below it, and four people sit round it with room behind them. It costs 26 percent of the floor, and that is the price of the gathering. What does not carry over is the open smoke. Give the fire a hood, a flue and an alarm, and you keep the oldest arrangement of a home: everyone facing the same fire.

On-screen math:

- Keep: centre, hook, rack, seats
- Change: hood + flue + CO alarm
- Cost: 26% of the floor

## 15. Do the one thing

Time: 00:09:00.664 - 00:09:19.512

Send this to one person who can carry it further than I can.

If any of this was worth your time, send it to one person who can carry it further than I can. That is the whole ask. One share from somebody with reach does more for this than a month of me in a field with a chainsaw.

On-screen math:


## 16. Follow the experiments

Time: 00:09:19.512 - 00:09:40.688

Follow the experiments.

Everything is documented, including the parts that failed. Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok, short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot com and a Kickstarter for Frankendome are both coming soon.

On-screen math:

