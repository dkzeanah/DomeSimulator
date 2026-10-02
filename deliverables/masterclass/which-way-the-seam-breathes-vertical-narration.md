# Which Way the Seam Breathes - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. One channel, many jobs

Time: 00:00:00.000 - 00:00:24.700

Which way should the seam breathe?

Every one of this dome's 55 seams has a channel inside it. Air can go in through it, out through it, round in a loop, through a desiccant or past one, over a cold plate or a warm one. That is a lot of choices. This film works out which one to make, and when, from one number.

On-screen math:

- seams = 55
- modes = 7

## 02. Inner skin, outer skin

Time: 00:00:24.700 - 00:01:01.000

The line from the centre outward has a name.

First, the word you were looking for. The line that runs from the centre of the dome straight outward is the radial direction. Through a wall it is the wall's thickness. In a seam it runs from the V's open mouth on the room side up to the ridge on the weather side. So the channel has two skins: an outer one that touches outside, and an inner one that touches the room. Put a Peltier plate on each and you can set the temperature of both.

On-screen math:

- radial = centre -> outward
- outer skin = ridge (weather)
- inner skin = mouth (room)

## 03. A plate is a heat pump

Time: 00:01:01.000 - 00:01:33.300

And it runs both ways.

A Peltier plate is not a cooler. It is a pump that moves heat from one face to the other, and reversing the current reverses the direction. So the rule for both plates is simple: throw the heat to the side you want warmer. In winter, into the room. In summer, outside. The first film, The Wedge Dome Explained, showed the plate throwing its heat into the room. That is right in winter and wrong in summer.

On-screen math:

- winter: cold face in the channel, heat to the room
- summer: cold face in the channel, heat to the outside skin

## 04. Compare dew points, not humidity

Time: 00:01:33.300 - 00:02:08.564

The one rule that ends the confusion.

Now the rule the whole system runs on. Never compare relative humidity. Compare dew points. Outside air at minus 5 degrees and 60 percent sounds damp. Its dew point is minus 11.6. Inside at 21 degrees and 45 percent, the dew point is 8.6. Per kilogram, the damp-sounding air carries 1.6 grams of water; the room's carries 6.9. Bring it in, and it dries the dome.

On-screen math:

- out minus 5 C 60% -> dew -11.6 C, 1.6 g/kg
- in 21 C 45% -> dew 8.6 C, 6.9 g/kg
- dew point: Magnus formula (standard)

## 05. Will it condense?

Time: 00:02:08.564 - 00:02:35.664

Dew point against surface temperature.

The second question: will this air leave water on that surface? It will whenever the air's dew point is above the surface's temperature. So a condensing plate must be colder than the dew point. And every piece of wood must be warmer than it, with room to spare. This film keeps wood 3 degrees above the dew point of the air that touches it.

On-screen math:

- water if dew point > surface
- collector: T < dew point
- wood: T > dew point + 3 K (assumed margin)

## 06. Fifteen to twenty degrees colder

Time: 00:02:35.664 - 00:03:12.200

The question you asked, with numbers.

You asked: if the wood sits at the dew point and the metal channel is fifteen to twenty degrees below it, will the water go to the metal? Take a room at 21 degrees and 55 percent. Its dew point is 11.6. The middle of your range, 17.5 degrees under that, is minus 5.9. The plate freezes. Frost stops the water running and chokes the fins. So hold the plate 6 degrees under the dew point and never below 1: here, 5.6 degrees.

On-screen math:

- dew point = 11.6 C
- your plate = 11.6 - 17.5 = -5.9 C: frost
- held at max(1, 11.6 - 6) = 5.6 C

## 07. Plate first, wood second

Time: 00:03:12.200 - 00:03:46.264

A colder surface elsewhere does not protect the wood.

And the real answer: a colder surface somewhere else does not protect wood that is already at the dew point. Wood touching raw room air still gets wet. What protects it is the order. Send the air over the plate first. It leaves with a dew point of 7.6, so wood at 11.6 is now 4.0 degrees clear. One more rule: the cold metal must never touch the wood, or it chills the wood to its own temperature.

On-screen math:

- raw air: wood at 11.6 C = dew point -> wet
- after the plate: dew point 7.6 C (plate + 2 K, assumed)
- wood safe above 10.6 C

## 08. Seven modes

Time: 00:03:46.264 - 00:04:17.764

Two of them never touch the room.

That gives the channel its modes. Take outside air in. Push inside air out. Condense inside air on a cold skin before it leaves. Loop the seam's own air through the desiccant. Purge a wet seam with outside air and send it straight back out. Supply dried air and hold the room at a slight positive pressure. Or shut the exposed intakes in the rain. The loop and the purge never touch the living space.

On-screen math:

- CLOSED: rain: exposed intakes shut
- INTAKE: outside -> seam -> inside
- EXHAUST: inside -> seam -> outside
- CONDENSE: inside -> cold seam -> drain -> outside
- FRAME_LOOP: seam -> desiccant -> seam
- PURGE: outside -> seam -> outside
- DRY_SUPPLY: dehumidified air in, slight positive pressure

## 09. The weathers we assumed

Time: 00:04:17.764 - 00:04:40.864

Estimates, not measurements.

To test the controller, here are the weathers from your table, plus one more. These are typical conditions, our estimates, not measurements from a site. Each one gets inside and outside temperatures and humidities, and the wet ones get a wood moisture reading at or over 19 percent, where lumber stops counting as dry.

On-screen math:

- Cold + dry outside: out minus 5 C 60%, in 21 C 45%
- Cold outside + humid inside: out minus 5 C 80%, in 21 C 68%
- Cold outside, harvesting water: out minus 2 C 80%, in 21 C 68%
- Mild + dry outside: out 16 C 40%, in 21 C 45%
- Hot + dry outside: out 33 C 18%, in 21 C 50%
- Hot + humid outside: out 32 C 70%, in 21 C 50%
- Hot + humid, cooling on: out 35 C 60%, in 24 C 50%
- Rain: out 14 C 97%, in 21 C 45%, rain
- After rain, dry outside: out 18 C 45%, in 21 C 45%, wood 21%
- Sun on a wet skin: out 24 C 55%, in 21 C 45%, wood 20%
- Muggy outside, wet frame: out 36 C 60%, in 24 C 55%, wood 20%

## 10. What the controller chose

Time: 00:04:40.864 - 00:05:08.160

All of them match your table.

And here is what the code chose, working only from dew points. Cold and dry: take it in. Hot and humid: dried supply only. Rain: shut. After rain, with dry air outside: purge the seam. Muggy outside with a wet frame: close the loop. All 11 weathers get the answer your table gives, and the film's own test fails if one ever does not.

On-screen math:

- Cold + dry outside: dew minus 12 out / 9 in -> INTAKE
- Cold outside + humid inside: dew minus 8 out / 15 in -> EXHAUST
- Cold outside, harvesting water: dew minus 5 out / 15 in -> CONDENSE
- Mild + dry outside: dew 2 out / 9 in -> INTAKE
- Hot + dry outside: dew 6 out / 10 in -> INTAKE
- Hot + humid outside: dew 26 out / 10 in -> DRY_SUPPLY
- Hot + humid, cooling on: dew 26 out / 13 in -> DRY_SUPPLY
- Rain: dew 14 out / 9 in -> CLOSED
- After rain, dry outside: dew 6 out / 9 in -> PURGE
- Sun on a wet skin: dew 14 out / 9 in -> PURGE
- Muggy outside, wet frame: dew 27 out / 14 in -> FRAME_LOOP

## 11. The loop and the purge

Time: 00:05:08.160 - 00:05:36.944

Drying the structure is not ventilating the house.

The two modes worth the extra plumbing are these. The frame loop takes the seam's air, dries it in the desiccant and sends it back: nothing thrown outside, nothing muggy pulled in. The purge takes dry outside air through a wet seam and straight back out. That needs two outside ports per circuit, and it means drying the frame is a separate job from ventilating the house.

On-screen math:

- frame loop: seam -> desiccant -> seam
- purge: outside -> seam -> outside

## 12. The dome's levels, from the solver

Time: 00:05:36.944 - 00:06:05.244

Four rings, five bands of seams.

Now where each job goes. The solver's dome stands on five heights: 10 corners at the rim, 5 and 5 in a belt that zigzags between two heights, 5 round the crown, and the apex. The seams between them fall into five bands: 20 in the lower band, 10 in the belt, 15 in the upper band, 5 round the crown pentagon, and 5 to the apex.

On-screen math:

- lower band, rim to belt: 20 seams, 113 ft, 57 deg
- the zigzag belt: 10 seams, 53 ft, 8 deg
- upper band, belt to pentagon: 15 seams, 87 ft, 37 deg
- the pentagon ring: 5 seams, 30 ft, 0 deg
- the cap, to the apex: 5 seams, 27 ft, 16 deg

## 13. The ring that cannot drain

Time: 00:06:05.244 - 00:06:32.372

Air at the top, water never.

The slopes decide the jobs. The lower band's seams rise at 57 degrees, and water runs down them fast. The belt zigzags at only 8 degrees, but that zigzag has 5 low points, and each one is a natural drain. The pentagon ring round the crown is dead level. Water there stands in the wood. So that ring carries air, never water.

On-screen math:

- lower: 56.6 deg -> drains
- belt: 8.3 deg, 5 low points -> drains
- pentagon: 0.0 deg -> dead level

## 14. Condense low, drain at the rim

Time: 00:06:32.372 - 00:07:05.872

Your first-ring idea is right.

Your idea of putting the plates on the first ring is right, and here is why. Condensate falls. A plate at the rim drops its water straight into a drain at one of the 10 rim corners, with no seam to travel through. The rain belongs outside, in a gutter at the rim. It should not come in through a seam higher up. Every foot of seam that carries liquid water is a foot of wood waiting for a leak.

On-screen math:

- rim ports = 10
- condensing plates: rim
- rain: outside gutter at the rim

## 15. Warm air rises

Time: 00:07:05.872 - 00:07:33.372

In low, out high, and the fan still does the work.

Air has its own preference. Warm inside air wants to leave at the top, so take air in at the rim and let it out at the pentagon ring and the apex. But the pull is small. With the inside ten degrees warmer, the height of this dome makes 1.2 pascals. The barrier fan holds 4. The stack helps; it does not replace the fan.

On-screen math:

- stack = rho g h dT / T = 1.18 Pa at 10 K
- barrier fan = 4 Pa

## 16. Why the desiccant stays out of the seams

Time: 00:07:33.372 - 00:08:07.292

The number that ends the rainbow.

Now the cartridge. Could you pack the beads into the seams themselves, round a ring, or over the top like a rainbow, a path of 32 feet? Push one seam's share of air, 13 cubic feet a minute, through one packed seam and the beads resist with 65,848 pascals. A small in-line fan manages about 250. At that, a packed seam passes 0.29 cubic feet a minute. The rainbow is longer still.

On-screen math:

- packed seam at 13.2 cfm: 65,848 Pa (Ergun)
- fan = 250 Pa (estimate) -> 0.29 cfm
- rim-apex-rim = 31.8 ft
- beads 2.5 mm, voidage 0.37 (nominal)

## 17. And it cannot be dried where it sits

Time: 00:08:07.292 - 00:08:32.308

The temperature that rules out the walls.

There is a second reason. A molecular sieve gives its water back only when it is hot: about 200 degrees. Even silica gel wants 120. The printed key softens at 80, and this film never sends air hotter than 60 through a seam. A desiccant in the seams could never be regenerated in place.

On-screen math:

- 13X regenerates at 200 C
- silica gel 120 C
- PETG softens 80 C
- seam air limit 60 C (assumed)

## 18. Two drawers and a gate

Time: 00:08:32.308 - 00:09:03.564

One drying while the other is regenerated.

So the desiccant lives in drawers, at the rim, where the channels come down. One drawer 30 centimetres square and 5 deep holds 2.9 kilograms of beads, and passes the whole dome's 18 cubic feet a minute at 20 pascals. Use two: one working, one being dried. The gate that picks between drawer and bypass should fall back to the bypass when the power goes, so air never stops.

On-screen math:

- drawer 30 x 30 x 5 cm (assumed)
- beads = 2.92 kg, holds 0.58 kg of water
- at 18 cfm: 20 Pa
- regenerate: 0.60 kWh = 18 min at 2 kW

## 19. What the desiccant will not do

Time: 00:09:03.564 - 00:09:30.764

It does not dry a soaked frame.

And the number that does not help. A frame that gets wet, over 19 percent, has 54 kilograms of water to lose to get back to 12. That is 93 drawer fills, and 56 kilowatt hours to regenerate them. The desiccant is for the weather when no air is dry enough. Drying a wet frame is the purge's job, on the next dry day.

On-screen math:

- frame water, 19% -> 12% = 54 kg
- = 92.8 drawer fills
- = 56 kWh of regeneration
- pine 420 kg/m3 dry (estimate)

## 20. The stove's heat, never its air

Time: 00:09:30.764 - 00:10:01.064

A sealed exchanger, and nothing else.

The stove can help, but only through a wall of steel. A sealed exchanger on the flue warms clean air, and that air can dry the frame or regenerate a drawer. The smoke side never meets it. Keep the seam air under 60 degrees. Give the stove its own outside combustion air. And never let the stove push or pull the seam air, or a back draught puts smoke in the walls.

On-screen math:

- exchanger: flue gas | steel | clean air
- seam air <= 60 C
- combustion air: its own outside duct

## 21. The layout

Time: 00:10:01.064 - 00:10:30.136

Every level with one job.

So here is the layout. At the rim: 10 ports, the condensing plates, the drains and the two drawers. The lower band carries air up and water down. The belt's 5 low points drain it. The pentagon ring is the exhaust manifold: air only. The cap vents at the apex. Sensors inside, outside and in the seam read temperature and humidity, the wood's moisture, and the rain.

On-screen math:

- rim: ports, plates, drains, drawers
- lower band: air up, water down
- belt: drains at the low points
- pentagon: exhaust manifold, air only
- cap: apex vent
- sensors: T, RH in / out / seam, wood %, rain

## 22. Dew point decides

Time: 00:10:30.136 - 00:10:52.992

Send air toward the wood only when it is drier.

One rule runs all of it. Send air toward the structure only when its dew point is lower than the moisture you are trying to remove, unless you are sending wetter air to a cold metal surface built to collect and drain the water. The same seams, winter and summer, rain and sun.

On-screen math:


## 23. Do the one thing

Time: 00:10:52.992 - 00:11:12.272

Send this to one person who can carry it further than I can.

If any of this was worth your time, send it to one person who can carry it further than I can. That is the whole ask. One share from somebody with reach does more for this than a month of me in a field with a chainsaw.

On-screen math:


## 24. Follow the experiments

Time: 00:11:12.272 - 00:11:34.336

Follow the experiments.

Everything is documented, including the parts that failed. Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok, short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot com and a Kickstarter for Frankendome are both coming soon.

On-screen math:

