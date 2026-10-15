# Assembly Line Energy Masterclass - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. One building, fifteen stations

Time: 00:00:00.000 - 00:00:36.608

1322 parts, 16,751 kilograms, and two people at every station.

This is the Iris-25: a 4.39 metre 4V dome home that leaves the line as 1322 placed parts weighing 16,751 kilograms in total. It passes through 15 stations, and a crew of 2 works each one. Over the next chapters we are going to follow those two people through every motion they make, and account for the energy each motion costs them.

On-screen math:

- parts = 1322
- mass = 16,751 kg
- labour = 315 h

## 02. What a line actually buys you

Time: 00:00:36.608 - 00:01:04.456

Not less work. Less waiting.

One crew doing all 15 stations spends 158 hours on a dome, and the next dome cannot start until the last one is finished. Split the same work across 15 stations and a dome comes off the end every 30.0 hours instead. The total labour did not change at all. What changed is that nobody is standing still waiting for someone else to finish.

On-screen math:

- serial = 158 h per dome
- pipelined = 30.0 h per dome

## 03. Inside one station

Time: 00:01:04.456 - 00:01:32.592

A stockpile, a dome, and two people who never leave.

Every station holds the same three things: the material waiting in a stockpile, the dome that arrived from the station before, and the crew. The crew does not follow the dome down the line. They stay, they learn one job completely, and a different dome arrives in front of them. That is the trade a line makes: depth of skill against variety of work.

On-screen math:

- crew = 2
- stockpile at 1.5 m

## 04. The line runs at the speed of its slowest station

Time: 00:01:32.592 - 00:01:59.936

Here that is frame, and nothing else matters until it changes.

Station cycle times are not equal. The frame station takes 30.0 hours, and every other station finishes early and then waits. Speeding up a fast station buys you nothing. This is the first place the energy question becomes a design question: the busiest station is also the one spending the most out of its crew.

On-screen math:

- bottleneck = frame
- cycle = 29.98 h

## 05. Every part is the same six motions

Time: 00:01:59.936 - 00:02:33.640

Walk, lift, carry, position, fasten, recover. 493 seconds, 41.1 kilocalories.

Whatever the part, the body does the same six things with it. It walks to the stockpile empty. It squats, grips, and stands the load up. It carries the load to where the part goes. It lifts the part into position, fixes it there, and straightens back up. Every one of those six has a duration taken from the part itself and a cost we can put a number on.

On-screen math:

- one part = 493 s
- one part = 41.08 kcal
- x 1322 parts

## 06. The walk out

Time: 00:02:33.640 - 00:03:02.472

1.5 metres, empty-handed, and it still costs something.

The stockpile sits 1.5 metres from where this part lands, so the trip out is 1.1 seconds of walking at 331 watts. That is a small number on its own. Across the whole dome those trips add up to 338 kilocalories, which is exactly why stockpile placement is a real decision and not a detail left to whoever unloads the truck.

On-screen math:

- distance = 1.45 m
- rate = 331 W

## 07. The lift, limb by limb

Time: 00:03:02.472 - 00:03:32.168

Most of what you raise is yourself.

Here is the squat and the stand, slowed down, with a 15.2 kilogram part in the hands. Watch what the colours say: the legs straighten, the trunk comes up, the arms barely move. The trunk alone is about half the body's mass, so raising it accounts for 65 per cent of the lifting work across the entire dome. The part is almost an afterthought next to the body carrying it.

On-screen math:

- load = 15.2 kg
- trunk share = 65 %

## 08. Carrying is not linear in the load

Time: 00:03:32.168 - 00:04:04.312

Double what someone carries and you more than double what it costs them.

Walking with a load is the one part of this that has a proper published equation behind it. Pandolf and colleagues measured it in 1977, and the load term in their equation is squared, not linear. Twenty kilograms does not cost twice what ten kilograms costs. It costs appreciably more. That single fact is the argument for carts, for conveyors, and for putting the stockpile closer, in one line.

On-screen math:

- 0 kg = 259 W
- 40 kg = 383 W

## 09. Getting it where it lands

Time: 00:04:04.312 - 00:04:36.696

This one goes to 4.18 metres, and the height changes the price.

Positioning is the short motion between carrying a part and fastening it. This part lands at 4.18 metres. Anything above 1.75 metres is overhead work, which means the arms are above the heart, the posture costs more, and the crew fatigues faster. The dome's own geometry decides how much of the shell falls into that band, which is a design decision disguised as a shape.

On-screen math:

- height = 4.18 m
- overhead above 1.75 m

## 10. Where the shift actually goes

Time: 00:04:36.696 - 00:05:10.544

Fastening raises nothing and spends 90 per cent of the fuel.

Here is the result that surprises people. Fastening does no lifting at all. Nothing rises. No mechanical work is done against gravity in any meaningful amount. And it consumes 90 per cent of everything the crew burns, because it is 386 seconds per part of holding a posture, gripping a tool, and stabilising against its torque. The body pays for holding still. It pays a lot.

On-screen math:

- 386 s per part
- 49,366 kcal per dome
- mechanical share = 0.00 %

## 11. The rest that is not slacking

Time: 00:05:10.544 - 00:05:40.792

33 hours of this build are recovery, by design.

Industrial engineering has added a recovery allowance to every task time for a century. It is called the personal, fatigue and delay allowance, and the standard figure is about 15 per cent on top of the task. Overhead work earns another 10 per cent because it fatigues fastest. A schedule written without it is not an efficient schedule, it is a schedule that will not be met.

On-screen math:

- allowance = 15 %
- overhead + 10 %
- total = 33.5 h

## 12. The body doing the work

Time: 00:05:40.792 - 00:06:11.760

82 kilograms, and every segment of it has a known mass.

To cost a movement you have to know what is being moved. This figure uses Winter's anthropometric tables, the standard reference in biomechanics: each body segment is a fixed fraction of total mass, and its centre of mass sits at a fixed fraction along its length. A thigh is a tenth of the body. The trunk is almost half. Those fractions are why the numbers in this lesson come out the way they do.

On-screen math:

- body = 82 kg
- trunk = 40.8 kg
- thigh = 8.2 kg

## 13. You are the heaviest thing you lift

Time: 00:06:11.760 - 00:06:40.472

The part is the small number in this comparison.

Placing this 15.2 kilogram part takes a certain amount of work to raise the part itself. It takes considerably more to raise the body that is doing it, because the body outweighs the part several times over and it goes up and down with every single placement. This is the honest reason a lower stockpile, a taller bench, or a part presented at waist height changes a shift so much.

On-screen math:

- part = 15.2 kg
- body = 82 kg

## 14. Legs, trunk, arms

Time: 00:06:40.472 - 00:07:06.976

The trunk does 65 per cent of the lifting work.

Splitting the lifting work by limb group across the whole dome gives a clear answer: legs 15 per cent, trunk 65 per cent, arms 20 per cent. The arms get all the attention because they are what you watch, but they are the lightest part of the body and they do the least raising. The back is where the work is, and that is also where the injuries are.

On-screen math:

- legs = 14.5 %
- trunk = 65.0 %
- arms = 20.4 %

## 15. When one person stops lifting alone

Time: 00:07:06.976 - 00:07:39.168

Above 23 kilograms it takes both of them.

Manual handling guidance puts the single-person limit near 23 kilograms. Above that the crew lifts together and each person carries half. The heaviest part on this dome is the column base plate at 234 kilograms, which is 117 kilograms each. Even with every team lift split, one worker still raises 15,100 kilograms to build one dome.

On-screen math:

- threshold = 23 kg
- heaviest = 234 kg
- raised per worker = 15,100 kg

## 16. The same part costs more up high

Time: 00:07:39.168 - 00:08:08.720

Arms above the heart is the most expensive posture on the line.

Two workers, the same fastener, the same number of turns. One is working at deck height and one is working above their shoulders. The overhead worker is spending noticeably more per second, is fatiguing faster, and will need more recovery for the same output. Whenever the dome's geometry pushes work above that line, the cost lands on a body rather than on a spreadsheet.

On-screen math:

- deck = 400 W
- overhead = 400 W

## 17. The part that is exact

Time: 00:08:08.720 - 00:08:41.392

Mass times gravity times height. No estimate anywhere in it.

Raising a part is the one piece of this with no modelling in it at all. This part weighs 15.2 kilograms and rises 4.18 metres, so the work done on it is 622 joules. The mass comes from the catalogue, the height comes from the dome's geometry, and gravity is gravity. Every mechanical number in this lesson is that calculation, run once per segment and once per part.

On-screen math:

- m = 15.2 kg
- h = 4.18 m
- W = 622 J

## 18. The part that is a model

Time: 00:08:41.392 - 00:09:15.288

Kilocalories are not measured here. They are estimated, and here is from what.

A muscle holding a panel steady does no mechanical work and still burns fuel, so there is no way to get from joules of lifting to kilocalories of food without external information. This lesson uses published task intensities for stationary work and the Pandolf equation for walking. There are 13 such constants, every one of them named in the report. Change the efficiency figure and every calorie here moves.

On-screen math:

- external constants = 13
- computed: mass, height, distance
- assumed: intensity, efficiency

## 19. Nineteen per cent, and a fifth of one per cent

Time: 00:09:15.288 - 00:09:46.328

Both are true. They answer different questions.

During the lift itself, 19 per cent of the fuel becomes height, which is close to what muscle can manage at best. Across the whole dome, mechanical work is 0.16 per cent of the food energy. The difference is not an error. It is that almost none of a working day is spent lifting. The rest is posture, grip, stabilising, and holding still, and none of that raises anything.

On-screen math:

- lift = 18.8 %
- build = 0.158 %
- muscle ceiling = 25 %

## 20. The whole dome, by motion

Time: 00:09:46.328 - 00:10:19.672

54,870 kilocalories per worker, and where each one went.

Here is every motion of every part, totalled. Fastening dominates, because fastening is where the time is. Walking, lifting, carrying and positioning together are a small fraction, even though they are the parts that look like work and the parts a manager would think to optimise. If you want to reduce what this line costs its crew, the target is the posture people hold while fastening, not the distance they walk.

On-screen math:

- fasten = 49,366 kcal
- pause = 4,120 kcal
- carry = 358 kcal
- walk_out = 338 kcal

## 21. The ledger, station by station

Time: 00:10:19.672 - 00:10:46.680

The busiest station is also the hungriest one.

Broken down per station, the energy follows the part count and the time, not the tonnage. Stations that place many light pieces slowly cost their crews more than stations that place a few heavy ones quickly. This is the table to look at when deciding where a jig, a lift assist, or an extra pair of hands would actually change someone's day.

On-screen math:

- frame = 10,531 kcal
- fiberglass = 9,407 kcal
- osb = 6,550 kcal
- sheetrock = 6,357 kcal

## 22. What one working day costs

Time: 00:10:46.680 - 00:11:20.264

2,298 kilocalories, at 3.50 METs.

Averaged over the build, the crew works at 334 watts, which is 3.50 times resting metabolism. Occupational physiology puts the ceiling for a sustained eight-hour shift at roughly 350 watts, so this line sits just under it, with the recovery allowance included. Take the allowance away and the same work stops being sustainable, which is the whole point of it.

On-screen math:

- rate = 334 W
- per shift = 2,298 kcal
- shifts = 23.9 per dome

## 23. The total, in food

Time: 00:11:20.264 - 00:11:57.016

109,741 kilocalories to build one house.

The two of them together spend 109,741 kilocalories turning 16,751 kilograms of material into a finished dome. That is about 1,372 slices of bread, or 1,045 bananas, or 44 days of eating at two and a half thousand kilocalories a day. It is a real cost, it is paid by people, and until now it was not on any drawing of this building.

On-screen math:

- crew total = 109,741 kcal
- = 1,372 slices of bread
- = 44 days of eating

## 24. What the ledger changes

Time: 00:11:57.016 - 00:12:30.552

Design the posture, not just the part.

We followed two people through every motion needed to build one dome and put a number on each one. The parts that look like effort turned out to be cheap. The part that looks like nothing, holding a position while fastening, turned out to be almost the whole bill. Every figure came from a part mass, a placement height, a walk distance, or a named published constant, and every one of them can be recomputed rather than trusted. That is the only reason it is worth putting on screen.

On-screen math:

- 1322 parts
- 191 h per worker
- 109,741 kcal for the crew
