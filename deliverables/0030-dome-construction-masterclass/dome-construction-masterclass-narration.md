# 2V Dome Construction Masterclass - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. What we are actually building

Time: 00:00:00.000 - 00:00:29.432

One dome, twenty feet across, from two boards you already own.

Before any mathematics, here is the finished thing, drawn to scale with a six foot person beside it. Twenty feet across, ten feet to the crown, about three hundred square feet of floor. Everything in the next half hour is in service of that object: where its two strut lengths come from, how to cut them, how to join them, how to stand them up, and how to know you got it right.

On-screen math:

- one radius scales the whole building
- height = radius

## 02. The five words we will keep using

Time: 00:00:29.432 - 00:01:00.448

Hub, strut, panel, chord factor, frequency. Learn them on the real thing.

A hub is a joint. A strut is a straight member between two hubs. A panel is the triangle they enclose. A chord factor is a strut's length divided by the radius, which is what lets one drawing serve every size of dome. And frequency is how many times each edge of the parent shape was divided: two, in this case, which is where two V comes from.

On-screen math:

- chord factor = strut length / radius
- frequency = divisions per parent edge

## 03. Why the whole thing is triangles

Time: 00:01:00.448 - 00:01:29.592

A triangle cannot change shape without changing a side length.

Push the top corner of a square frame and it folds over into a diamond; no side got longer, the shape just moved. Do the same to a triangle and nothing happens, because moving any corner would have to stretch a side. That is the entire structural argument for a geodesic dome, and it is why the frame carries load along its members rather than bending them.

On-screen math:

- F = F_compression + F_tension
- geometry explains the form; an engineer sizes the members

## 04. Where the shape starts: the icosahedron

Time: 00:01:29.592 - 00:01:56.384

Twenty equal triangles are the closest a regular solid gets to a sphere.

Of the five regular solids, the icosahedron has the most faces and the most evenly spread corners, so it needs the least correction when you push it out to a sphere. That is the only reason it is chosen. It gives twenty equilateral launch pads and twelve corners, and every geodesic dome in common use starts here.

On-screen math:

- faces: 4, 6, 8, 12, 20
- 2V means: halve every parent edge

## 05. Phi builds the twelve corners

Time: 00:01:56.384 - 00:02:24.880

The golden ratio places the parent vertices. It is not the strut ratio.

The twelve corners of an icosahedron are three golden rectangles standing at right angles to each other. That is where the golden ratio genuinely lives in this shape. It is worth being precise about, because the ratio of the two finished strut lengths is not phi, and expecting it to be has sent a lot of people down the wrong path.

On-screen math:

- phi = (1 + sqrt 5) / 2
- corners: (0, +-1, +-phi) and its rotations

## 06. Put it on a sphere of radius one

Time: 00:02:24.880 - 00:02:51.456

One division turns coordinates into numbers you can scale to any size.

Divide every corner by its distance from the centre and the solid now sits on a sphere of radius exactly one. From here on, every length we measure is a multiple of the radius, so the same drawing serves a garden dome and a hangar. This is the single most useful move in the whole derivation.

On-screen math:

- v_hat = v / ||v||
- parent edge = 1.051462 R

## 07. Halve every edge

Time: 00:02:51.456 - 00:03:18.176

Thirty parent edges give thirty midpoints, and they are all too close in.

Take the midpoint of every one of the thirty edges. That is just the average of the two ends, and it is easy. But those midpoints sit inside the sphere, not on it, because a straight line between two points on a curved surface always cuts the corner. Leave them there and you have a faceted lump, not a dome.

On-screen math:

- m = (a + b) / 2
- ||m|| = 0.850651, short of 1

## 08. Push the midpoints out to the sphere

Time: 00:03:18.176 - 00:03:43.648

This one move is what creates the second strut length.

Slide each midpoint straight out from the centre until it reaches the sphere. Nothing else changes. But by moving those thirty points outward, every triangle around them changes shape, and the edges that used to be equal split into two different lengths. That is the whole origin of the two cut lengths in your shopping list.

On-screen math:

- p = m / ||m||
- the move outward = 0.149349 R

## 09. Two lengths, and nothing else

Time: 00:03:43.648 - 00:04:10.440

One hundred and twenty edges collapse into exactly two numbers.

Measure every edge on the finished sphere and they fall into two groups and only two. The shorter one runs from an original corner to a projected midpoint. The longer one runs between two projected midpoints, and it comes out to exactly one over phi, which is the one place the golden ratio does show up in the answer.

On-screen math:

- SHORT = 0.546533 R
- LONG = 0.618034 R = 1 / phi
- ratio = 1.130826, not phi

## 10. Choosing your radius

Time: 00:04:10.440 - 00:04:37.712

Floor grows with the square of the radius. Volume grows with the cube.

Now pick a size, and pick it for a reason. Doubling the radius gives four times the floor, eight times the volume, and four times the skin you have to buy and waterproof. Headroom at the wall is the thing people underestimate: at the very edge of a hemisphere there is none at all, which is what the riser wall later in this lesson is for.

On-screen math:

- floor = pi R^2
- skin = 2 pi R^2
- volume = 2/3 pi R^3

## 11. The dome is four rings and a crown

Time: 00:04:37.712 - 00:05:02.872

Twenty-six hubs, in courses, at heights you can measure before you build.

Cut the sphere in half and the hubs sort themselves into level courses: ten on the ground, then two rings of five, then five more, then the single hub at the top. Twenty-six joints in total. Those ring heights and diameters are your check numbers during the raise, so write them on the drawing before you start.

On-screen math:

- 26 hubs: 10 + 5 + 5 + 5 + 1
- every ring is a level circle you can measure

## 12. Auditing the boards you already have

Time: 00:05:02.872 - 00:05:33.360

Two measured members imply two radii. Fit them, do not average them.

You measured seventy-two inches and sixty-three and a half. Each of those implies a radius on its own, and they disagree slightly, because real members contain cutting and measuring error. The right move is a least squares fit that weights both, not picking whichever one you trust more. That fit is the radius the rest of this lesson uses.

On-screen math:

- R from LONG = 72 / 0.618034
- R from SHORT = 63.5 / 0.546533
- best fit minimises both residuals

## 13. Choose the hub system before anything else

Time: 00:05:33.360 - 00:06:01.352

The connector decides the deduction, and the deduction decides every cut.

A steel star plate, a bevelled timber joint, and a drilled hub ball all build the same geometry but they eat different amounts of strut. Choose the system now, build one joint for real, and measure how much shorter the members have to be. Everything downstream depends on that one measurement, and no catalogue number is a substitute for it.

On-screen math:

- hub system -> connector deduction -> every cut length
- build one real joint and measure it

## 14. Centre length is not cut length

Time: 00:06:01.352 - 00:06:28.096

The geometry gives hub centres. The saw needs something shorter.

Every number in the derivation is hub centre to hub centre, because that is what the sphere is made of. The stick you cut has to be shorter by whatever the two connectors occupy. Note that the deduction is the total across both ends, not per end; halving it by mistake is one of the most common ways a dome ends up refusing to close.

On-screen math:

- cut length = centre length - deduction
- deduction is both ends together

## 15. The end-cut angle is half the central angle

Time: 00:06:28.096 - 00:06:57.360

One line of arithmetic gives you the angle the strut leaves the surface at.

A strut is a chord across the sphere, so it dips below the surface between its ends. The angle it makes with the surface at each end is exactly half the central angle that chord subtends, and the central angle comes straight out of the chord factor. That is the angle to tip a hub plate to, or to cut a timber end back to, and there is one value per strut class.

On-screen math:

- chord = 2 R sin(theta / 2)
- end cut = theta / 2

## 16. The panel bevels

Time: 00:06:57.360 - 00:07:27.464

Two panels fold along every interior strut, and there are only two fold angles.

Where two panels meet along a strut they are not in the same plane; they fold. If you are skinning with rigid sheets, the edge of each panel wants to be planed to half that fold so the two faces meet cleanly. There are exactly two fold angles in the whole dome, one along each strut class, which means two saw settings and no thinking at the bench.

On-screen math:

- bevel = (180 - fold) / 2
- two fold angles in the entire dome

## 17. How many kinds of joint

Time: 00:07:27.464 - 00:07:50.368

Five hub types, and they are not interchangeable.

Grouping the hubs by how many struts arrive and at what angles gives a small number of distinct types. Make a set for each type, keep them in separate labelled boxes, and check one against a drawing before you make the rest. The base hubs are the ones to make first, because they also have to take the anchor bolts.

On-screen math:

- hub type = strut count + splay angles
- make one, check it, then make the batch

## 18. Buying the stock

Time: 00:07:50.368 - 00:08:18.864

Choose the stock length before the radius and the offcut nearly vanishes.

Here is a real cost that geometry lessons never mention. At this radius, a standard eight foot stick yields exactly one strut and throws the rest away. A sixteen foot stick yields several. The right time to notice that is while the radius is still adjustable, because a small change in radius can move you from one piece per stick to two.

On-screen math:

- pieces per stick = floor((stock + kerf) / (cut + kerf))
- kerf counts; include it

## 19. Cutting: a stop block and a master

Time: 00:08:18.864 - 00:08:44.144

Cut every piece of one class before you move anything.

Set a stop block for the first class and cut all of them without touching the setting. Keep the very first good piece as a master gauge and compare the rest to it rather than re-measuring with a tape, because a tape introduces a new error every time you use it. Label each piece as it comes off the saw. Then, and only then, move the stop.

On-screen math:

- one setting per class
- compare to a master, not to a tape
- label at the saw

## 20. The finished cut list

Time: 00:08:44.144 - 00:09:08.440

Sixty-five members, two lengths, and a count you can hand to a shop.

This is the whole order: thirty of the shorter class and thirty-five of the longer, at the cut lengths we derived, plus the hub schedule. Add spares. Two or three of each class costs very little and saves an entire afternoon the first time a piece splits or a cut goes wrong.

On-screen math:

- 30 SHORT + 35 LONG = 65 members
- add spares of both classes

## 21. Build the triangles flat, first

Time: 00:09:08.440 - 00:09:38.904

Two triangle families repeat all forty times. Jig them on the ground.

The dome contains only two kinds of triangle: thirty with two short sides and one long, and ten with three long sides. Lay one of each out on a flat floor, screw down blocks to make a jig, and assemble the rest inside the jig. Every panel then comes out identical, and the raise turns into bolting known-good pieces together rather than fitting each one.

On-screen math:

- 30 x SHORT-SHORT-LONG
- 10 x LONG-LONG-LONG
- jig them flat before anything goes up

## 22. Setting out the base

Time: 00:09:38.904 - 00:10:09.008

A ten-sided ring, set out from the centre, checked on the diagonals.

Drive a pin at the centre and swing the base radius to mark all ten hub positions. Do not step around the ring measuring side to side, because every small error then adds to the next one. When the ten are pegged, measure the long diagonals: on a regular ten-sided ring they are all identical, so any difference is telling you exactly where the setting out drifted.

On-screen math:

- set out from the centre, every time
- all five long diagonals are equal on a true ring

## 23. Meeting the ground

Time: 00:10:09.008 - 00:10:37.624

Piers, a ring beam, or a slab. Whichever you choose has to be level.

A dome puts a concentrated outward-and-down load at each base hub, so the foundation either has to catch each one individually with a pier, or tie them all together with a ring beam or slab that resists the spread. The structural choice is yours and your engineer's. The one non-negotiable is that the ten bearing points end up on one level plane.

On-screen math:

- base hubs push down and outward
- pier, ring beam, or slab -- but level

## 24. The riser wall

Time: 00:10:37.624 - 00:11:07.608

The cheapest usable space a dome will ever sell you.

A hemisphere has no headroom at its edge, which makes the outer ring of floor nearly useless. Stand the whole dome on a short vertical wall and every point of the shell rises by that amount, so the perimeter becomes furniture height or door height. It costs one ring of studs and it changes the plan completely. Decide on it before you set out, because it changes the foundation.

On-screen math:

- riser adds its height everywhere
- the floor area does not change; the usable area does

## 25. Raising it, one complete ring at a time

Time: 00:11:07.608 - 00:11:38.720

Never build up one side. The shell is not stable until a ring closes.

Bolt the base hubs down, then work upward in complete courses. A half-built ring is a row of unstable triangles and it will lean; a closed ring is a rigid hoop that holds its own shape. Prop each course until the one above it closes. Measure the diameter across each finished ring in three directions before you begin the next, and correct there rather than higher up.

On-screen math:

- complete rings, never one column
- prop until the ring above closes
- measure each ring three ways

## 26. Closing the crown

Time: 00:11:38.720 - 00:12:08.896

If the last hub will not fit, the error is in the ring below it.

The top hub is where every accumulated millimetre finally arrives, so it is the honest test of everything below. If the five struts will not reach it cleanly, resist the urge to force them. Go back down and measure the ring beneath: nearly always it is slightly out of round or slightly out of level, and correcting it there is far quicker than fighting the crown.

On-screen math:

- the crown reports the error, it does not cause it
- 5 SHORT struts meet at the apex

## 27. What an eighth of an inch actually does

Time: 00:12:08.896 - 00:12:39.912

A ten-sided ring amplifies a strut error by exactly the golden ratio.

Here is a number worth carrying around. If every base strut is one eighth of an inch long, the base radius is out by phi times that, and the diameter by twice again. The same golden ratio that placed the parent corners now governs how your mistakes grow. It is not a large factor, but it is a multiplier, and it explains why domes drift bigger rather than smaller.

On-screen math:

- regular n-gon: radius = side / (2 sin(pi/n))
- for n = 10 that divisor is 0.618034
- so radius error = phi x strut error

## 28. The measurement loop

Time: 00:12:39.912 - 00:13:12.968

Member, triangle, ring, radius, height. In that order, every time.

Check a member against the master gauge. Check a triangle on all three corners. Check a ring on its diameter, three ways. Check the radius from the centre pin to each hub. Check the apex height against the radius, because on a true hemisphere they are the same number. Each check catches what the previous one could hide, and doing them in order is what stops a small error becoming a structural one.

On-screen math:

- length -> triangle -> ring -> radius -> height
- expected dome height = R exactly

## 29. Skinning it, rim upward

Time: 00:13:12.968 - 00:13:45.904

Forty panels, laid so every lap sheds downhill, sealed at every hub.

Start at the base and work up so each panel laps over the one below it, exactly like roof shingles. Every hub is a junction of several panel corners and those are the leak points, so flash or tape each one before the next course covers it. Give the base a real drip edge that throws water clear of the wall. A dome almost never fails structurally; it fails at its seams.

On-screen math:

- 40 panels in the dome half
- lap upward, seal every hub
- a drip edge at the base is not optional

## 30. Doors, windows, and what not to cut

Time: 00:13:45.904 - 00:14:13.632

Take whole panels. Cutting a strut means replacing a load path.

The clean way to make an opening is to leave a panel out and frame the triangle. The frame is untouched and the shell keeps working. If you must make a bigger opening, head it with a member at least as strong as the ones you removed and get that detail checked, because a dome carries load through its net and a missing strut is a missing path, not just a missing stick.

On-screen math:

- whole panels are free openings
- a cut strut needs its load path replaced

## 31. The four things that actually go wrong

Time: 00:14:13.632 - 00:14:42.200

None of them are geometry. All of them are avoidable.

Domes rarely fail because the arithmetic was wrong. They fail because the connector deduction was guessed instead of measured, because the base was not level, because someone built up one side instead of in rings, or because two similar-looking members got mixed up. Each of those is a habit, not a calculation, and each is cheap to fix before you start and expensive after.

On-screen math:

- deduction guessed
- base not level
- built up one side
- parts unlabelled

## 32. The dome with no hubs in it

Time: 00:14:42.200 - 00:15:12.184

Forty complete triangles, and not one connector between them.

Everything so far assumed a hub: a plate or a bracket that several struts arrive at. There is another way to build the same sphere that has no hubs at all. You make each of the forty triangles as a finished, closed triangle, and then you bolt the triangles to each other edge to edge. Nothing meets at a point any more. Every joint is now a lap between two flat sides.

On-screen math:

- 40 triangles x 3 struts = 120
- hubbed: 65 struts + 26 hubs
- hubless: 120 struts + 0 hubs

## 33. Why it takes 120 struts, not 65

Time: 00:15:12.184 - 00:15:47.592

Every shared edge now carries two struts instead of one.

A hubbed dome has sixty-five struts because each edge is one member serving the panels on both sides of it. A hubless dome gives each triangle its own three members, so an edge between two triangles ends up with two struts lying face to face, bolted through. Fifty-five edges are shared like that. Ten more sit on the rim with nothing on the other side. Two times fifty-five, plus ten, is one hundred and twenty, and that is the whole frame.

On-screen math:

- 55 shared x 2 struts = 110
- 10 rim x 1 strut = 10
- total = 120

## 34. The compound cut

Time: 00:15:47.592 - 00:16:22.064

Two angles at once, on the same pass, on every single end.

Here is the part that stops people. Each strut end needs the saw swung to a mitre, so the strut meets its neighbour in the plane of its own triangle, and the blade tilted to a bevel, so the face lies flat against the triangle next door. Those two settings are not applied one after the other. They happen on the same cut, which is what compound means, and getting one right while the other is wrong gives you a part that looks correct and fits nothing.

On-screen math:

- mitre: the saw swings
- bevel: the blade tilts
- one pass, both at once

## 35. Every angle you need is past the stop

Time: 00:16:22.064 - 00:17:02.920

The geometry is easy. The tool is the problem.

Now the sting. The mitres this dome asks for run from about fifty-six degrees to about sixty-two degrees away from square, and a common mitre saw stops at fifty. Not one of the settings this dome needs is on the scale. The way through is that a mitre and its complement are the same cut approached from the other face: swing the saw to the complement instead, which lands between twenty-seven and thirty-four degrees, and rotate the workpiece a quarter turn in a sled. Same joint, reachable setting. Build the sled first, before you cut anything you care about.

On-screen math:

- needed: 55.6 to 62.2 deg from square
- common saw stops at 50 deg
- complement: 27.8 to 34.4 deg, and turn the part

## 36. The tube around the bottom

Time: 00:17:02.920 - 00:17:30.912

This one started with a badly ventilated workshop.

A dome has an unhelpful habit: warm air and anything it carries rises to the apex and stays there. Weld inside one and you are standing in a chimney with no flue. The fix that came out of that is a tube running right around the base, with a blower on it, so the whole perimeter becomes one duct instead of the building having a single extract point somewhere on one wall.

On-screen math:

- ring main = one duct all the way round
- no single extract point
- the shape is the ductwork

## 37. Run it either way

Time: 00:17:30.912 - 00:18:05.048

The same tube and the same fan make two different buildings.

Push air in at the ring and it leaves through the shell, carrying fumes out through the whole surface at once instead of dragging them past your face to one vent. Reverse it and you draw outside air inward through the shell, which warms it against the structure on the way in and recovers heat you would otherwise throw away. That second mode has a real name in building science: dynamic insulation, or a breathing wall. Same hardware. One switch.

On-screen math:

- push: purge fumes through the whole surface
- pull: incoming air warmed by the shell
- one tube, one switch

## 38. The wall as the filter

Time: 00:18:05.048 - 00:18:42.832

The shell is so large that the air barely crawls through it.

Here is why the idea is interesting rather than merely odd. A ten foot dome holds about two hundred and sixty cubic feet of air behind about fifteen square metres of wall. Even purging hard, at forty air changes an hour, the air crosses that wall at about one foot per minute. A draught you can feel starts somewhere near forty. So the entire envelope becomes a filter face and nobody inside feels a thing, because the flow is spread over the whole building instead of rushing past one grille.

On-screen math:

- 6 ACH -> 26 CFM
- 20 ACH -> 87 CFM
- 40 ACH -> 175 CFM
- through the wall at about 1 ft/min

## 39. What would actually decide it

Time: 00:18:42.832 - 00:19:20.952

The flow numbers are computed. The wall is not proven.

Being straight about this: the geometry and the airflow above are calculated, and the idea that a strut lattice makes a good distributed plenum at building scale is untested. Five things decide it. Direction, because pushing warm wet air outward through a cold wall condenses it inside that wall and rots the shell where you cannot see it. A sealed fibreglass skin cannot breathe at all, so the permeable band has to be designed in rather than hoped for. And a filter you cannot reach is a filter you will never change.

On-screen math:

- computed: the flow
- untested: the wall
- moisture is the failure mode

## 40. Forty panels from one sheet

Time: 00:19:20.952 - 00:19:58.712

The whole shell, nested onto a single ten by five foot sheet.

Different build entirely. Forget struts: cut the forty triangles as solid panels and join them edge to edge. The question is how big a dome you can get off one sheet. Congruent triangles pair into parallelograms, and parallelograms strip-pack with no waste along a row, because the slope of one is filled by the next. Solving that packing against a ten by five sheet, with a real kerf and a real edge margin, gives a radius of about thirty-one inches.

On-screen math:

- 30 identical + 10 identical panels
- paired into parallelograms, strip-packed
- one 10 ft x 5 ft sheet

## 41. The sub-two-thousand-dollar storm shelter

Time: 00:19:58.712 - 00:20:47.032

Sixty-two inches across, thirty-one inches tall. It is not cozy.

That sheet buys a shell about five feet across with thirty-one inches of headroom and twenty-one square feet of floor. You do not stand up in it. You do not really sit up in it either. I have been inside it, so nobody needs to tell me it is not cozy. It is a hole you can afford, above ground, that a laser can cut in an afternoon. And if you want it habitable rather than survivable, the riser wall from earlier fixes it for almost nothing: five inches of riser gets you sitting upright, and forty-one inches gets you standing, without recutting a single panel. If you have seen a shelter cheaper than this that a person can actually get into, message the channel. I would genuinely like to study it.

On-screen math:

- 62 in across, 31 in headroom, 21 sq ft
- 5 in riser -> sit upright
- 41 in riser -> stand up

## 42. The franken-dome

Time: 00:20:47.032 - 00:21:15.192

One hundred and twenty struts, and no two of them alike.

Last one, and it is an experiment rather than a recommendation. I wanted to know how fast a dome goes up if you stop caring what the struts are. Round logs, quarter-cut pieces, wedges, square stock, rectangular offcuts, whatever the chainsaw produced that day. Every section has a different effective centreline, so not one joint lands where the geometry says it should.

On-screen math:

- 120 struts, any section
- no two centrelines alike
- nothing lands on the sphere

## 43. Why the lumpy one stays up

Time: 00:21:15.192 - 00:21:54.752

The errors have nowhere to accumulate, and the skin covers the rest.

It should not work and it does, for two reasons. A closed triangulated shell is enormously redundant: every triangle is rigid by itself, so an error at one joint is absorbed by the two hundred around it instead of walking around a ring the way it does in a precise dome. What you get is a lumpy brain of a frame that is near the sphere without being on it. Then the sheathing does the rest. A monolithic skin bonded over the outside spans the slack and gives back the shell action the sloppiness cost you.

On-screen math:

- every triangle rigid on its own
- error absorbed, not accumulated
- the skin returns the shell action

## 44. Borrowing strength from the site

Time: 00:21:54.752 - 00:22:26.128

Four trees did the work the tolerance did not.

It went up between four trees, and that was not an accident. Cable overhead, tied back into the trunks, meant the frame never had to be self-supporting while it was going together, and the trees kept taking a share afterwards. Covered in clear plastic, it stood through half a year of weather with no complaints before I took it down on purpose. That is eighteen times its own build time, which is the only durability number I actually have.

On-screen math:

- guyed into four trees
- clear plastic cover
- stood 6 months = 18x its build time

## 45. What it cost, and the crown I award myself

Time: 00:22:26.128 - 00:23:20.040

A chainsaw, a tarp, and rather a lot of screws.

The ledger. One hundred and twenty brackets, eight screws in each, which is nine hundred and sixty screws. Two bolts through every edge, so a hundred and thirty bolts and two hundred and sixty washers. Ten days, four triangles a day. The timber was free and the tarp was nearly free; the hardware was the real cost, and that is the part worth spending on, because heavy bolts get unbolted and reused on the next and better dome. That is investment that never goes obsolete. As far as I can tell nobody has put this particular method on the internet before, which by my own reckoning and absolutely nobody else's crowns me sovereign of a hobo commune that does not exist, somewhere pleasant with relaxed local statutes. The crown is imaginary. The building was not.

On-screen math:

- 120 brackets x 8 = 960 screws
- 130 bolts, 260 washers
- 10 days, 4 triangles a day
- the hardware outlives the dome

## 46. The whole thing, once more, quickly

Time: 00:23:20.040 - 00:23:57.872

From the golden ratio to a building you can stand inside.

Phi places twelve corners. Normalising puts them on a unit sphere. Halving every edge and pushing the midpoints out gives two chord factors. One radius turns those into two cut lengths. A connector deduction turns those into saw settings. Jigs turn saw settings into identical triangles, rings turn triangles into a shell, and a skin turns a shell into a room. Every number came from the geometry, and every one of them can be recomputed instead of trusted.

On-screen math:

- phi -> icosahedron -> 2V -> SHORT + LONG -> R -> cut list -> building
