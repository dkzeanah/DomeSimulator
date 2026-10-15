# The Dome Simulator Master Presentation - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. The whole argument, start to finish

Time: 00:00:00.000 - 00:00:34.568

*on screen: A starter home you can count.*

This is the master presentation. Everything this project knows, in one film. The software tools and their worlds. The geometry, derived from nothing. The jigs, the compound cuts, the frames, the raising. The frankendome and the reason it exists. And a starter home, priced to the dollar, against the square house it wants to replace. One rule holds the whole way through: every number you are about to see is computed, on camera, by the same code that draws these pictures. When you see the math screen, you are watching the numbers being made.

On-screen math:


## 02. One codebase, five worlds

Time: 00:00:34.568 - 00:01:05.152

*on screen: Every tool computes from the same geometry.*

The project is one codebase wearing five faces. A dome creator you walk around in. A dome forge that builds one dome out of layers, like a paint program builds an image. A factory simulation that prices every screw. A teaching-video engine, which is what is rendering this very film. And a presenter studio that turns a script into a movie. They all read the same geometry module, so a strut length in one tool cannot disagree with the same strut in another.

On-screen math:


## 03. The Dome Creator

Time: 00:01:05.152 - 00:01:41.184

*on screen: A build-a-home world with a live bill of materials.*

The Dome Creator is a walkable site. Click the ground and the avatar walks there. Click a panel and you can swap it: glass, shingle, solar, plastic sheeting, anything. Change the frequency, the radius, the frame material, the foundation. Every choice updates a live bill of materials: strut cut lists, panel weights, costs, even how many trees you would have to harvest. A camera hangs from every apex, watching the floor, counting what it sees. It is a sales floor, a design desk and a planning meeting in one window.

On-screen math:


## 04. The Dome Forge

Time: 00:01:41.184 - 00:02:23.600

*on screen: One dome, made of layers you can peel apart.*

The Dome Forge is a single dome, taken apart like layers in a paint program. Frame, panels, drains, veins, ring, pipe, tank, rain -- every part is its own layer you can hide, fade, reorder or tune. The default stack answers the oldest dome complaint there is. Domes leak, people say. So the panels dish inward and drain to one point each. A vein runs along the inside of every seam, standing off from the skin, so anything that gets past a joint lands in a channel instead of your floor. The veins run downhill to a collector ring, down a pipe, into a cistern. The leak becomes the water supply.

On-screen math:


## 05. The Jig Shop

Time: 00:02:23.600 - 00:02:53.152

*on screen: Two tables build all forty triangles.*

Inside the forge is a jig shop, and it is the whole factory in miniature. A 2V dome has forty triangles but only two shapes: ten equilateral, thirty isosceles. So you build two jigs. A base plate, a scribed triangle, fences along each board, stops at each corner. Load three boards, screw the corners, lift out a finished panel. We will come back here with the exact angles once you have seen where they come from.

On-screen math:


## 06. The Assembly Line

Time: 00:02:53.152 - 00:03:34.176

*on screen: Fifteen stations, and every dollar accounted for.*

The assembly line is a factory simulation in the real trailer-plant order. A carriage rolls the home down the rails through fifteen stations: floor, frame, utility column, water, power, fixtures, insulation, sheetrock, sheathing, membrane, shingle scales, fiberglass, the sealed hatch, the fit-out, the solar band. Every element carries a real material cost and a real install time, and a simulated crew walks every part from the stockpile at a human stride, so the labor hours are earned, not assumed. Panels show profit and loss, the bottleneck station, break-even. It is an investor tool that happens to look like a video game.

On-screen math:


## 07. The engine rendering this film

Time: 00:03:34.176 - 00:03:57.368

*on screen: Programmatic video: correct because it is computed.*

And the film you are watching right now is the fifth tool. Every frame is a pure function of time. Every scene is drawn by code, and every figure on screen is calculated by a module that also proves itself before a single frame renders. Generative video cannot be asked to be correct. This can. That promise is about to matter, because of what comes next.

On-screen math:


## 08. Nothing here is typed in

Time: 00:03:57.368 - 00:04:26.944

*on screen: Watch the model count itself.*

Here is the first math screen, and the rule it stands for. The panel on the right is counting the dome behind it, live. Forty panels. Sixty-five edges in two lengths. Twenty-six corners. Nobody wrote those numbers into a caption; the code that draws the dome is the code that counts it. Every claim in this film -- every angle, every dollar, every gallon -- reaches the screen the same way. If we cannot compute it, we name where it came from.

On-screen math:

- count the model, live, right now:
- triangular panels          = 40
- SHORT edges                = 30
- LONG edges                 = 35
- edges total = 30 + 35 = 65
- hubs (shared corners)      = 26
- none of these were typed in -- they are counted
- off the same 3D model being drawn behind this panel
- 40 panels, 65 edges, 26 corners -- and every number in this film is made the same way

## 09. The shape everyone builds

Time: 00:04:26.944 - 00:04:48.456

*on screen: 997 square feet of skin for 314 of floor.*

Start with the shape everybody already builds. Four walls, a roof, and corners. Give it three hundred and fourteen square feet of floor and you have to build, wrap, seal and heat 997 square feet of outside. Every one of them costs money twice. Once to put up, and again every winter for as long as you live there.

On-screen math:


## 10. Same floor, less building

Time: 00:04:48.456 - 00:05:10.784

*on screen: 42% less exterior, for the same floor.*

Now put a dome next to it with exactly the same floor. The house needs 997 square feet of skin. The dome needs 583. That is 42 percent less to build, less to seal, less to paint, and less to heat, forever, for the same room to stand in. Nobody invented that. It is just what the shape does.

On-screen math:


## 11. The box comparison, derived

Time: 00:05:10.784 - 00:05:39.424

*on screen: Same floor. Less building. It is arithmetic.*

Let us do that comparison properly, on the math screen. Same floor area for both shapes. The box needs walls, a roof and gables. The dome needs forty flat triangles. Add them up and the dome wants about forty percent less outside for the same inside -- and the skin is the part you build, seal, paint and heat. The wind figures are the one borrowed pair on this screen: published drag coefficients, named as such. Everything else is geometry.

On-screen math:

- same floor, both shapes: 314 sq ft
- box: side = sqrt(314) = 17.7 ft, walls 8 ft, 0.50 pitch roof
- box skin  = walls + roof + gables = 997 sq ft
- dome skin = 40 flat triangles     = 583 sq ft
- difference = 414 sq ft = 42% less to build, seal, paint, heat
- volume enclosed: dome 2,093 cu ft vs box 3,208 cu ft
- wind drag (published): dome Cd 0.42 vs box Cd 1.05 = 60% less load
- the dome buys the same floor with 42% less outside -- and pays for that once, then every winter

## 12. Why it stands up

Time: 00:05:39.424 - 00:06:01.200

*on screen: A triangle cannot change shape without breaking.*

Here is why it holds. Push on a square and it leans. The corners hinge, and every rectangular building on earth needs bracing to stop it. Push on a triangle and nothing happens. To change its shape you have to change the length of a side, which means breaking something. A dome is forty triangles. There is nothing left to brace.

On-screen math:


## 13. Nothing for the wind to push on

Time: 00:06:01.200 - 00:06:19.832

*on screen: Drag 0.42 against 1.05 for a box.*

Wind is the same story. A flat wall catches everything thrown at it. A box has a drag coefficient of about 1.05. A dome, about 0.42. Roughly 60 percent less load out of the shape alone, before you have bolted anything down.

On-screen math:


## 14. What we are actually building

Time: 00:06:19.832 - 00:06:44.224

*on screen: One dome, twenty feet across, from two boards you already own.*

Before any mathematics, here is the finished thing, drawn to scale with a six foot person beside it. Twenty feet across, ten feet to the crown, about three hundred square feet of floor. Everything in the next half hour is in service of that object: where its two strut lengths come from, how to cut them, how to join them, how to stand them up, and how to know you got it right.

On-screen math:

- one radius scales the whole building
- height = radius

## 15. The five words we will keep using

Time: 00:06:44.224 - 00:07:07.872

*on screen: Hub, strut, panel, chord factor, frequency. Learn them on the real thing.*

A hub is a joint. A strut is a straight member between two hubs. A panel is the triangle they enclose. A chord factor is a strut's length divided by the radius, which is what lets one drawing serve every size of dome. And frequency is how many times each edge of the parent shape was divided: two, in this case, which is where two V comes from.

On-screen math:

- chord factor = strut length / radius
- frequency = divisions per parent edge

## 16. Where the shape starts: the icosahedron

Time: 00:07:07.872 - 00:07:28.376

*on screen: Twenty equal triangles are the closest a regular solid gets to a sphere.*

Of the five regular solids, the icosahedron has the most faces and the most evenly spread corners, so it needs the least correction when you push it out to a sphere. That is the only reason it is chosen. It gives twenty equilateral launch pads and twelve corners, and every geodesic dome in common use starts here.

On-screen math:

- faces: 4, 6, 8, 12, 20
- 2V means: halve every parent edge

## 17. Phi builds the twelve corners

Time: 00:07:28.376 - 00:07:49.936

*on screen: The golden ratio places the parent vertices. It is not the strut ratio.*

The twelve corners of an icosahedron are three golden rectangles standing at right angles to each other. That is where the golden ratio genuinely lives in this shape. It is worth being precise about, because the ratio of the two finished strut lengths is not phi, and expecting it to be has sent a lot of people down the wrong path.

On-screen math:

- phi = (1 + sqrt 5) / 2
- corners: (0, +-1, +-phi) and its rotations

## 18. Put it on a sphere of radius one

Time: 00:07:49.936 - 00:08:10.128

*on screen: One division turns coordinates into numbers you can scale to any size.*

Divide every corner by its distance from the centre and the solid now sits on a sphere of radius exactly one. From here on, every length we measure is a multiple of the radius, so the same drawing serves a garden dome and a hangar. This is the single most useful move in the whole derivation.

On-screen math:

- v_hat = v / ||v||
- parent edge = 1.051462 R

## 19. Halve every edge

Time: 00:08:10.128 - 00:08:31.256

*on screen: Thirty parent edges give thirty midpoints, and they are all too close in.*

Take the midpoint of every one of the thirty edges. That is just the average of the two ends, and it is easy. But those midpoints sit inside the sphere, not on it, because a straight line between two points on a curved surface always cuts the corner. Leave them there and you have a faceted lump, not a dome.

On-screen math:

- m = (a + b) / 2
- ||m|| = 0.850651, short of 1

## 20. Push the midpoints out to the sphere

Time: 00:08:31.256 - 00:08:51.832

*on screen: This one move is what creates the second strut length.*

Slide each midpoint straight out from the centre until it reaches the sphere. Nothing else changes. But by moving those thirty points outward, every triangle around them changes shape, and the edges that used to be equal split into two different lengths. That is the whole origin of the two cut lengths in your shopping list.

On-screen math:

- p = m / ||m||
- the move outward = 0.149349 R

## 21. Two lengths, and nothing else

Time: 00:08:51.832 - 00:09:12.528

*on screen: One hundred and twenty edges collapse into exactly two numbers.*

Measure every edge on the finished sphere and they fall into two groups and only two. The shorter one runs from an original corner to a projected midpoint. The longer one runs between two projected midpoints, and it comes out to exactly one over phi, which is the one place the golden ratio does show up in the answer.

On-screen math:

- SHORT = 0.546533 R
- LONG = 0.618034 R = 1 / phi
- ratio = 1.130826, not phi

## 22. Two lengths, derived from nothing

Time: 00:09:12.528 - 00:09:40.400

*on screen: From the golden ratio to a tape measure.*

Now watch the whole derivation land in eight lines. Phi places twelve corners. One division puts them on a unit sphere. Halving every edge and pushing the midpoints back out changes the distances -- and when you measure every edge again, only two numbers remain. Multiply by any radius you like and those two numbers become two boards. The pair this project was originally asked about fits a ten-foot-radius dome almost exactly.

On-screen math:

- phi = (1 + sqrt 5) / 2 = 1.618034
- 12 corners at (0, +-1, +-phi): radius = sqrt(1 + phi^2) = 1.902113
- divide by that radius -> icosahedron on a unit sphere
- halve every edge: midpoints sit at 0.893322, inside the sphere
- push each midpoint back out to radius 1
- measure every edge again -> only two lengths remain:
- SHORT = 0.546533 x R    LONG = 0.618034 x R
- the audited boards: 72 in / 63.5 in -> best-fit R = 116.4 in
- two lengths of wood, thirty of one and thirty-five of the other, are the entire frame

## 23. Choosing your radius

Time: 00:09:40.400 - 00:10:00.952

*on screen: Floor grows with the square of the radius. Volume grows with the cube.*

Now pick a size, and pick it for a reason. Doubling the radius gives four times the floor, eight times the volume, and four times the skin you have to buy and waterproof. Headroom at the wall is the thing people underestimate: at the very edge of a hemisphere there is none at all, which is what the riser wall later in this lesson is for.

On-screen math:

- floor = pi R^2
- skin = 2 pi R^2
- volume = 2/3 pi R^3

## 24. The dome is four rings and a crown

Time: 00:10:00.952 - 00:10:20.256

*on screen: Twenty-six hubs, in courses, at heights you can measure before you build.*

Cut the sphere in half and the hubs sort themselves into level courses: ten on the ground, then two rings of five, then five more, then the single hub at the top. Twenty-six joints in total. Those ring heights and diameters are your check numbers during the raise, so write them on the drawing before you start.

On-screen math:

- 26 hubs: 10 + 5 + 5 + 5 + 1
- every ring is a level circle you can measure

## 25. Auditing the boards you already have

Time: 00:10:20.256 - 00:10:43.832

*on screen: Two measured members imply two radii. Fit them, do not average them.*

You measured seventy-two inches and sixty-three and a half. Each of those implies a radius on its own, and they disagree slightly, because real members contain cutting and measuring error. The right move is a least squares fit that weights both, not picking whichever one you trust more. That fit is the radius the rest of this lesson uses.

On-screen math:

- R from LONG = 72 / 0.618034
- R from SHORT = 63.5 / 0.546533
- best fit minimises both residuals

## 26. Choose the hub system before anything else

Time: 00:10:43.832 - 00:11:05.536

*on screen: The connector decides the deduction, and the deduction decides every cut.*

A steel star plate, a bevelled timber joint, and a drilled hub ball all build the same geometry but they eat different amounts of strut. Choose the system now, build one joint for real, and measure how much shorter the members have to be. Everything downstream depends on that one measurement, and no catalogue number is a substitute for it.

On-screen math:

- hub system -> connector deduction -> every cut length
- build one real joint and measure it

## 27. Centre length is not cut length

Time: 00:11:05.536 - 00:11:26.088

*on screen: The geometry gives hub centres. The saw needs something shorter.*

Every number in the derivation is hub centre to hub centre, because that is what the sphere is made of. The stick you cut has to be shorter by whatever the two connectors occupy. Note that the deduction is the total across both ends, not per end; halving it by mistake is one of the most common ways a dome ends up refusing to close.

On-screen math:

- cut length = centre length - deduction
- deduction is both ends together

## 28. The end-cut angle is half the central angle

Time: 00:11:26.088 - 00:11:48.728

*on screen: One line of arithmetic gives you the angle the strut leaves the surface at.*

A strut is a chord across the sphere, so it dips below the surface between its ends. The angle it makes with the surface at each end is exactly half the central angle that chord subtends, and the central angle comes straight out of the chord factor. That is the angle to tip a hub plate to, or to cut a timber end back to, and there is one value per strut class.

On-screen math:

- chord = 2 R sin(theta / 2)
- end cut = theta / 2

## 29. The panel bevels

Time: 00:11:48.728 - 00:12:11.128

*on screen: Two panels fold along every interior strut, and there are only two fold angles.*

Where two panels meet along a strut they are not in the same plane; they fold. If you are skinning with rigid sheets, the edge of each panel wants to be planed to half that fold so the two faces meet cleanly. There are exactly two fold angles in the whole dome, one along each strut class, which means two saw settings and no thinking at the bench.

On-screen math:

- bevel = (180 - fold) / 2
- two fold angles in the entire dome

## 30. How many kinds of joint

Time: 00:12:11.128 - 00:12:30.128

*on screen: Five hub types, and they are not interchangeable.*

Grouping the hubs by how many struts arrive and at what angles gives a small number of distinct types. Make a set for each type, keep them in separate labelled boxes, and check one against a drawing before you make the rest. The base hubs are the ones to make first, because they also have to take the anchor bolts.

On-screen math:

- hub type = strut count + splay angles
- make one, check it, then make the batch

## 31. Buying the stock

Time: 00:12:30.128 - 00:12:52.360

*on screen: Choose the stock length before the radius and the offcut nearly vanishes.*

Here is a real cost that geometry lessons never mention. At this radius, a standard eight foot stick yields exactly one strut and throws the rest away. A sixteen foot stick yields several. The right time to notice that is while the radius is still adjustable, because a small change in radius can move you from one piece per stick to two.

On-screen math:

- pieces per stick = floor((stock + kerf) / (cut + kerf))
- kerf counts; include it

## 32. Cutting: a stop block and a master

Time: 00:12:52.360 - 00:13:13.296

*on screen: Cut every piece of one class before you move anything.*

Set a stop block for the first class and cut all of them without touching the setting. Keep the very first good piece as a master gauge and compare the rest to it rather than re-measuring with a tape, because a tape introduces a new error every time you use it. Label each piece as it comes off the saw. Then, and only then, move the stop.

On-screen math:

- one setting per class
- compare to a master, not to a tape
- label at the saw

## 33. The finished cut list

Time: 00:13:13.296 - 00:13:31.304

*on screen: Sixty-five members, two lengths, and a count you can hand to a shop.*

This is the whole order: thirty of the shorter class and thirty-five of the longer, at the cut lengths we derived, plus the hub schedule. Add spares. Two or three of each class costs very little and saves an entire afternoon the first time a piece splits or a cut goes wrong.

On-screen math:

- 30 SHORT + 35 LONG = 65 members
- add spares of both classes

## 34. The cut list makes itself

Time: 00:13:31.304 - 00:14:01.024

*on screen: One radius in, a lumber order out.*

Here is the same chain as arithmetic. Pick the radius. The two factors turn it into two cut lengths. Subtract the connector deduction you measured -- measured, never guessed. Then the stock plan falls out: how many eight-foot sticks, how many pieces from each, and exactly how much offcut every stick leaves behind. Change the radius and every line on this screen recomputes. That is what it means for a house to have a parts list instead of a price opinion.

On-screen math:

- pick the audited dome: R = 116.4 in
- SHORT = 0.546533 x R = 63.60 in, cut 30 times
- LONG  = 0.618034 x R = 71.92 in, cut 35 times
- hub-centre minus a measured 0.75 in connector deduction = the saw setting
- SHORT: 30 pieces from 30 sticks of 8 ft stock, 33.2 in offcut each
- LONG: 35 pieces from 35 sticks of 8 ft stock, 24.8 in offcut each
- one radius scales the whole cut list; the lumber order falls straight out of it

## 35. The dome with no hubs in it

Time: 00:14:01.024 - 00:14:25.104

*on screen: Forty complete triangles, and not one connector between them.*

Everything so far assumed a hub: a plate or a bracket that several struts arrive at. There is another way to build the same sphere that has no hubs at all. You make each of the forty triangles as a finished, closed triangle, and then you bolt the triangles to each other edge to edge. Nothing meets at a point any more. Every joint is now a lap between two flat sides.

On-screen math:

- 40 triangles x 3 struts = 120
- hubbed: 65 struts + 26 hubs
- hubless: 120 struts + 0 hubs

## 36. Why it takes 120 struts, not 65

Time: 00:14:25.104 - 00:14:54.608

*on screen: Every shared edge now carries two struts instead of one.*

A hubbed dome has sixty-five struts because each edge is one member serving the panels on both sides of it. A hubless dome gives each triangle its own three members, so an edge between two triangles ends up with two struts lying face to face, bolted through. Fifty-five edges are shared like that. Ten more sit on the rim with nothing on the other side. Two times fifty-five, plus ten, is one hundred and twenty, and that is the whole frame.

On-screen math:

- 55 shared x 2 struts = 110
- 10 rim x 1 strut = 10
- total = 120

## 37. One hundred and twenty sticks, checked

Time: 00:14:54.608 - 00:15:19.816

*on screen: No hubs. The count proves itself.*

The hubless method sounds wasteful until you count it honestly. Every triangle brings its own three boards, so every interior seam carries two boards side by side, and the rim seams carry one. Run the check and it balances exactly. What you bought with the extra wood is the removal of every hub: no welded stars, no brackets to order, no single part that the whole build waits on.

On-screen math:

- hubless: every triangle brings its own three boards
- 40 triangles x 3 = 120 struts
- interior seams: 55 -- each carries two boards, one from each neighbour
- rim seams: 10 -- each carries one
- check: 55 x 2 + 10 = 120 = the strut count
- hubs required = 0
- 120 sticks bolt to each other -- there is no hub to buy, weld, or wait for

## 38. The compound cut

Time: 00:15:19.816 - 00:15:47.040

*on screen: Two angles at once, on the same pass, on every single end.*

Here is the part that stops people. Each strut end needs the saw swung to a mitre, so the strut meets its neighbour in the plane of its own triangle, and the blade tilted to a bevel, so the face lies flat against the triangle next door. Those two settings are not applied one after the other. They happen on the same cut, which is what compound means, and getting one right while the other is wrong gives you a part that looks correct and fits nothing.

On-screen math:

- mitre: the saw swings
- bevel: the blade tilts
- one pass, both at once

## 39. Every angle you need is past the stop

Time: 00:15:47.040 - 00:16:21.080

*on screen: The geometry is easy. The tool is the problem.*

Now the sting. The mitres this dome asks for run from about fifty-six degrees to about sixty-two degrees away from square, and a common mitre saw stops at fifty. Not one of the settings this dome needs is on the scale. The way through is that a mitre and its complement are the same cut approached from the other face: swing the saw to the complement instead, which lands between twenty-seven and thirty-four degrees, and rotate the workpiece a quarter turn in a sled. Same joint, reachable setting. Build the sled first, before you cut anything you care about.

On-screen math:

- needed: 55.6 to 62.2 deg from square
- common saw stops at 50 deg
- complement: 27.8 to 34.4 deg, and turn the part

## 40. Two angles, one stick

Time: 00:16:21.080 - 00:16:53.512

*on screen: Every strut carries two completely different angles, on two machines.*

This is the hardest operation in the whole dome, and it is worth being precise about why. Every strut carries two angles that have nothing to do with each other. There is a bevel that runs the entire length of the stick, and there is a mitre at each end. The bevel decides how this triangle meets the triangle next door. The mitre decides how this strut meets the other two struts of its own triangle. Get one right and the other wrong and you have a part that looks perfect on the bench and fits absolutely nothing.

On-screen math:

- rip bevel: the whole length
- end mitre: only the ends
- different jobs, different machines

## 41. Why it takes two saws

Time: 00:16:53.512 - 00:17:16.128

*on screen: Each machine can only do the cut the other one cannot.*

A table saw rips along the length of a board and cannot sensibly crosscut a long stick at sixty degrees. A mitre saw crosscuts ends and cannot rip at all. That is the entire reason this job needs two machines. It is not fussiness and it is not showing off. There is no single setup on either saw that produces a finished strut.

On-screen math:

- table saw: rips, cannot crosscut at 62 deg
- mitre saw: crosscuts, cannot rip

## 42. Setting the blade tilt

Time: 00:17:16.128 - 00:17:37.112

*on screen: Do not trust the saw's own scale.*

Now the table saw. Tilt the blade to the bevel for this strut class. Do not trust the scale cast into the saw; it is a starting point, not a measurement. And set the blade height after the tilt, never before, because a tilted blade has to travel further to cross the same thickness and a height set square will not come through.

On-screen math:

- set the tilt first, the height second
- a tilted blade needs more height

## 43. Proving the tilt

Time: 00:17:37.112 - 00:18:01.528

*on screen: Rip two offcuts, put them together, and read twice the error.*

Here is how you know the tilt is right before you commit the pile. Rip two offcuts at the setting, then put the two cut faces together and measure the pair. If the tilt is correct the pair closes to exactly the fold the dome wants along that strut. And because the pair carries both errors, anything too small to see in a single piece is obvious in the double.

On-screen math:

- the pair reads the dome's own dihedral
- error shows up doubled

## 44. The saw runs out of scale

Time: 00:18:01.528 - 00:18:24.000

*on screen: Swing it to its stop and it is still not enough.*

Now the ends, and now the problem. Swing the mitre saw as far as it goes. A common saw stops at about fifty degrees from square. The mitres this dome wants start at fifty-five and a half and run past sixty-two. Not one of the settings this dome needs is on the scale. The saw is not badly made. The angle is simply outside what a mitre saw is built to do.

On-screen math:

- saw stops near 50 deg
- the dome wants 55.6 to 62.2 deg

## 45. One angle, two names

Time: 00:18:24.000 - 00:18:44.528

*on screen: Measure it from the blade instead of from square.*

The way out is not a trick, it is a change of reference. An angle measured from square and its complement measured from the blade describe the same cut. Sixty-two degrees from square is twenty-seven point eight degrees from the blade. So stop trying to make the saw's table reach the number, and build a fence that holds the work at the complement instead.

On-screen math:

- 62.215 from square = 27.785 from the blade
- same cut, different reference

## 46. The sled

Time: 00:18:44.528 - 00:19:09.952

*on screen: A crosscut sled with its fence built to the complement.*

So the ends get cut on a crosscut sled on the table saw. Two runners in the mitre slots with no slop at all, a flat base, and a fence set to the complement angle referenced off the blade. Build the sled first. Prove it. Only then cut a part you care about. Every strut in the dome passes over this one fence, so every error built into it is an error repeated two hundred and forty times.

On-screen math:

- runners with no slop
- fence referenced off the blade
- one fence, 240 ends

## 47. Proving the fence

Time: 00:19:09.952 - 00:19:38.832

*on screen: The five-cut method makes an invisible error measurable.*

You cannot check a fence this critical with a combination square. Use the five-cut method: cut a scrap four times, rotating it a quarter turn between cuts, then slice a fifth strip off and measure that strip at both ends. The four cuts multiply the fence error by four, so a difference of five thousandths across a twenty inch strip means the fence is out by less than four thousandths of a degree. That is a level of proof you simply cannot get by eye.

On-screen math:

- four cuts multiply the error by four
- 0.005 in over 20 in = 0.0036 deg

## 48. The relief lap and the stop block

Time: 00:19:38.832 - 00:20:10.880

*on screen: The blade has to finish the cut flush, so the fence gets cut away.*

Two details on the sled that decide whether it works. First, the strut sits against the fence with one end projecting past it, and the blade has to finish that cut flush, so the fence is cut away at the blade path. Cut that lap once, with the sled in the exact position it will always be used in. Second, length comes from a stop block clamped to the sled, never from a pencil line. Two hundred and forty ends measured individually will drift. Two hundred and forty ends against one block will not.

On-screen math:

- relief lap: cut once, in position
- stop block, never a tape measure

## 49. The first end

Time: 00:20:10.880 - 00:20:34.744

*on screen: Bevelled edge down, butted to the stop, one pass all the way through.*

Bevelled edge down and against the fence. Marked face up. Strut butted hard to the stop block, the end projecting over the lap. One pass, all the way through, and let the blade come to a stop before you lift the work. That is the compound cut: the sled is holding the mitre and the stick is already carrying its bevel, so both angles arrive on the same pass.

On-screen math:

- bevel down, marked face up
- butted to the stop, one pass

## 50. Turn it, do not flip it

Time: 00:20:34.744 - 00:21:03.504

*on screen: The second end is not a mirror of the first.*

Now the second end, and this is where a whole afternoon can go. The second end is not a mirror of the first. Rotate the strut end for end about its own long axis, the way the sled was built for, so the bevelled edge stays on the same side of the dome. If you flip it face over face instead, you mirror the part. It will look completely correct lying on the bench and it will refuse to close a triangle, and you will not find out until assembly.

On-screen math:

- turn end for end about the long axis
- flipping face over face mirrors the part

## 51. Batch by setting

Time: 00:21:03.504 - 00:21:28.880

*on screen: Six setting changes, not two hundred and forty.*

Cut every end that shares a setting before you change anything. Changing a setting is where error enters the job, so change it as few times as the work allows. Six setups cover all two hundred and forty ends in the dome. Sorted by setting that is six careful changes. Sorted by triangle it is a change every couple of minutes for two days, and every one of them a chance to be slightly wrong.

On-screen math:

- 6 setups cover 240 ends
- batch by setting, never by triangle

## 52. Dry-fit one triangle

Time: 00:21:28.880 - 00:21:50.536

*on screen: Three struts on a flat floor, no fasteners.*

Before you cut the rest of the pile, dry-assemble one triangle. Three struts on a flat floor, no fasteners at all. If it closes with no gap at any corner and lies flat, your settings are right and you can cut with confidence. If it does not, you have lost three sticks instead of the whole pile, and you still have the setting in front of you to correct.

On-screen math:

- no gap at any corner, and it lies flat
- three sticks lost, not 240

## 53. Every saw setting, measured off the model

Time: 00:21:50.536 - 00:22:26.448

*on screen: Two jigs. Six settings. Forty triangles.*

Back to the jig shop, now with the numbers earned. Two triangle shapes, so two jigs. Every mitre is ninety degrees minus half the corner it closes. Every bevel is half the fold to the neighbouring panel. Count the distinct pairs and the whole dome needs six saw setups -- and the ends that sit past a fifty degree saw are reached by swinging to the complement and turning the stick a quarter turn. These figures are not from a chart. They are re-measured off the assembled 3D model every time the self-test runs, and the build stops if they ever disagree.

On-screen math:

- only two triangle shapes exist in the whole dome:
- equilateral x10: corners 60.0 deg / 60.0 deg / 60.0 deg
- isosceles   x30: corners 68.9 deg / 55.6 deg / 55.6 deg
- mitre (saw swing) = 90 - corner/2;  bevel (blade tilt)
- = (180 - fold to the neighbour)/2
- setup: mitre 55.57 deg, bevel 11.23 deg -- 60 strut ends
- setup: mitre 62.22 deg, bevel 11.23 deg -- 60 strut ends
- setup: mitre 60.00 deg, bevel 9.02 deg -- 50 strut ends
- setup: mitre 62.22 deg, bevel 9.02 deg -- 50 strut ends
- setup: mitre 60.00 deg, bevel 0.00 deg -- 10 strut ends
- setup: mitre 62.22 deg, bevel 0.00 deg -- 10 strut ends
- 240 ends sit past a 50 deg saw: swing to the complement (34.43 deg) and quarter-turn the stick
- two jigs and 6 saw setups cut all 120 struts -- that is the entire machine shop

## 54. Build the triangles flat, first

Time: 00:22:26.448 - 00:22:50.912

*on screen: Two triangle families repeat all forty times. Jig them on the ground.*

The dome contains only two kinds of triangle: thirty with two short sides and one long, and ten with three long sides. Lay one of each out on a flat floor, screw down blocks to make a jig, and assemble the rest inside the jig. Every panel then comes out identical, and the raise turns into bolting known-good pieces together rather than fitting each one.

On-screen math:

- 30 x SHORT-SHORT-LONG
- 10 x LONG-LONG-LONG
- jig them flat before anything goes up

## 55. Setting out the base

Time: 00:22:50.912 - 00:23:14.488

*on screen: A ten-sided ring, set out from the centre, checked on the diagonals.*

Drive a pin at the centre and swing the base radius to mark all ten hub positions. Do not step around the ring measuring side to side, because every small error then adds to the next one. When the ten are pegged, measure the long diagonals: on a regular ten-sided ring they are all identical, so any difference is telling you exactly where the setting out drifted.

On-screen math:

- set out from the centre, every time
- all five long diagonals are equal on a true ring

## 56. Meeting the ground

Time: 00:23:14.488 - 00:23:36.792

*on screen: Piers, a ring beam, or a slab. Whichever you choose has to be level.*

A dome puts a concentrated outward-and-down load at each base hub, so the foundation either has to catch each one individually with a pier, or tie them all together with a ring beam or slab that resists the spread. The structural choice is yours and your engineer's. The one non-negotiable is that the ten bearing points end up on one level plane.

On-screen math:

- base hubs push down and outward
- pier, ring beam, or slab -- but level

## 57. The riser wall

Time: 00:23:36.792 - 00:24:02.000

*on screen: The cheapest usable space a dome will ever sell you.*

A hemisphere has no headroom at its edge, which makes the outer ring of floor nearly useless. Stand the whole dome on a short vertical wall and every point of the shell rises by that amount, so the perimeter becomes furniture height or door height. It costs one ring of studs and it changes the plan completely. Decide on it before you set out, because it changes the foundation.

On-screen math:

- riser adds its height everywhere
- the floor area does not change; the usable area does

## 58. Raising it, one complete ring at a time

Time: 00:24:02.000 - 00:24:27.472

*on screen: Never build up one side. The shell is not stable until a ring closes.*

Bolt the base hubs down, then work upward in complete courses. A half-built ring is a row of unstable triangles and it will lean; a closed ring is a rigid hoop that holds its own shape. Prop each course until the one above it closes. Measure the diameter across each finished ring in three directions before you begin the next, and correct there rather than higher up.

On-screen math:

- complete rings, never one column
- prop until the ring above closes
- measure each ring three ways

## 59. Closing the crown

Time: 00:24:27.472 - 00:24:51.408

*on screen: If the last hub will not fit, the error is in the ring below it.*

The top hub is where every accumulated millimetre finally arrives, so it is the honest test of everything below. If the five struts will not reach it cleanly, resist the urge to force them. Go back down and measure the ring beneath: nearly always it is slightly out of round or slightly out of level, and correcting it there is far quicker than fighting the crown.

On-screen math:

- the crown reports the error, it does not cause it
- 5 SHORT struts meet at the apex

## 60. What an eighth of an inch becomes

Time: 00:24:51.408 - 00:25:19.256

*on screen: The base ring multiplies your mistakes by phi.*

Before the skin goes on, one number worth respecting. The ten-sided base ring is a regular polygon, and its radius is the strut length divided by a fixed constant -- and for ten sides that constant happens to be one over the golden ratio. So every error in a base strut reaches the foundation multiplied by phi. That is not a superstition, it is trigonometry, and it is why the measurement loop checks every ring before the next one goes up.

On-screen math:

- the base ring is a regular 10-sided polygon
- circumradius = side / (2 sin(180/10)) = side / 0.618034
- so radius error = strut error x 1.618034
- that multiplier is exactly phi = 1.618034
- an error of 0.125 in per base strut moves the radius 0.202 in
- the diameter 0.405 in, and the apex 0.202 in
- the ring multiplies every strut error by the golden ratio -- which is why you check each ring before building the next

## 61. The measurement loop

Time: 00:25:19.256 - 00:25:45.040

*on screen: Member, triangle, ring, radius, height. In that order, every time.*

Check a member against the master gauge. Check a triangle on all three corners. Check a ring on its diameter, three ways. Check the radius from the centre pin to each hub. Check the apex height against the radius, because on a true hemisphere they are the same number. Each check catches what the previous one could hide, and doing them in order is what stops a small error becoming a structural one.

On-screen math:

- length -> triangle -> ring -> radius -> height
- expected dome height = R exactly

## 62. Skinning it, rim upward

Time: 00:25:45.040 - 00:26:10.536

*on screen: Forty panels, laid so every lap sheds downhill, sealed at every hub.*

Start at the base and work up so each panel laps over the one below it, exactly like roof shingles. Every hub is a junction of several panel corners and those are the leak points, so flash or tape each one before the next course covers it. Give the base a real drip edge that throws water clear of the wall. A dome almost never fails structurally; it fails at its seams.

On-screen math:

- 40 panels in the dome half
- lap upward, seal every hub
- a drip edge at the base is not optional

## 63. Doors, windows, and what not to cut

Time: 00:26:10.536 - 00:26:32.552

*on screen: Take whole panels. Cutting a strut means replacing a load path.*

The clean way to make an opening is to leave a panel out and frame the triangle. The frame is untouched and the shell keeps working. If you must make a bigger opening, head it with a member at least as strong as the ones you removed and get that detail checked, because a dome carries load through its net and a missing strut is a missing path, not just a missing stick.

On-screen math:

- whole panels are free openings
- a cut strut needs its load path replaced

## 64. The four things that actually go wrong

Time: 00:26:32.552 - 00:26:55.504

*on screen: None of them are geometry. All of them are avoidable.*

Domes rarely fail because the arithmetic was wrong. They fail because the connector deduction was guessed instead of measured, because the base was not level, because someone built up one side instead of in rings, or because two similar-looking members got mixed up. Each of those is a habit, not a calculation, and each is cheap to fix before you start and expensive after.

On-screen math:

- deduction guessed
- base not level
- built up one side
- parts unlabelled

## 65. Borrowing strength from the site

Time: 00:26:55.504 - 00:27:21.840

*on screen: Four trees did the work the tolerance did not.*

It went up between four trees, and that was not an accident. Cable overhead, tied back into the trunks, meant the frame never had to be self-supporting while it was going together, and the trees kept taking a share afterwards. Covered in clear plastic, it stood through half a year of weather with no complaints before I took it down on purpose. That is eighteen times its own build time, which is the only durability number I actually have.

On-screen math:

- guyed into four trees
- clear plastic cover
- stood 6 months = 18x its build time

## 66. Why I built the ugly one

Time: 00:27:21.840 - 00:28:05.960

*on screen: The beautiful math needed an ugly test.*

Everything you have seen so far assumes care. Milled lumber, measured deductions, jigs proved with a five-cut test. The frankendome is the opposite experiment, and I built it on purpose. Take whatever the chainsaw made. Skip the compound cuts. Fold flat steel into brackets instead of mitering seams. Let nothing land where it should, and then see what the geometry forgives. A normal hubless build replaces the hub with precision. The frankendome replaces it with tolerance -- and that difference is the entire experiment. If triangulation only works for careful people with good stock, it is a luxury. If it works for salvage and a folded bracket, it is a housing method.

On-screen math:


## 67. Whatever the chainsaw made

Time: 00:28:05.960 - 00:28:29.008

*on screen: Round, quarter-sawn, wedge, square, rectangular. All in the same dome.*

Round logs still in the bark. Quarter-sawn pieces off a milling jig. Wedges that were offcuts of something else. Square stock, rectangular stock, whatever came off the pile that day. They are not interchangeable in any engineering sense: every one of those sections has its centreline in a different place, so no two joints in the whole dome are the same joint.

On-screen math:

- five profiles, one frame
- every section, a different centreline

## 68. Where a bracket comes from

Time: 00:28:29.008 - 00:28:54.720

*on screen: A flat band of washing machine casing, drilled.*

The joints are the interesting part. Every one is a bracket I made, and every bracket started as a flat band sheared out of a scrapped washing machine. That casing is galvanised sheet in a gauge that is genuinely structural at this size, it is free, it is already flat, and there is a great deal of it in the world. Shear a band, drill six or eight holes in it, and that is the whole component.

On-screen math:

- washing machine casing
- shear a band, drill 6 to 8 holes

## 69. One fold makes it a joint

Time: 00:28:54.720 - 00:29:24.608

*on screen: Bend it in half and it becomes a V.*

Then one fold, straight down the middle, and the band becomes a V. That is the entire bracket. No welding, no castings, no bought connectors. And because you are bending it yourself, the fold angle is simply whatever that particular corner turned out to be, which on a frame like this is never the angle on the drawing. The bracket adapts to the joint instead of the joint having to match the bracket. That is the trick, and it is why the method tolerates such rough stock.

On-screen math:

- one fold, down the middle
- the bracket adapts to the joint, not the other way round

## 70. Four screws into each strut

Time: 00:29:24.608 - 00:29:50.032

*on screen: Two struts, one V, eight screws.*

In place it works like this. The V straddles the corner, one leg down each strut. Four screws through the leg into the first strut, four more into the second, so eight screws per bracket. Four in shear along a leg is a genuinely stiff connection, and it fails gradually and visibly rather than suddenly, which for a structure you are experimenting with is exactly the behaviour you want.

On-screen math:

- 4 screws into each strut
- 8 screws per bracket
- surprisingly stiff in shear

## 71. Nothing lands where it should

Time: 00:29:50.032 - 00:30:12.120

*on screen: Green is the geometry. Red is where the stick actually put it.*

Here is the honest picture of what you get. The green points are where the geometry says every hub belongs. The red lines show where the sticks actually put them. Not one joint in the dome lands on the sphere. Some are out by a quarter of an inch, some by more, and every single one of those errors is a different error because every stick is a different stick.

On-screen math:

- green = the geometry
- red = the stick
- not one joint on the sphere

## 72. And then it settles

Time: 00:30:12.120 - 00:30:37.232

*on screen: Pull it together and the whole frame shares the error out.*

Now watch what happens when you actually pull it together and stand it up. The frame settles. Every triangle is individually rigid, so a joint that wants to sit proud is held by the two around it, and the error gets shared out across the whole shell instead of accumulating around a ring the way it does in a precise dome. That redundancy is not a nice property here. It is the only reason the thing stands at all.

On-screen math:

- the error is shared, not accumulated
- redundancy is what makes it possible

## 73. The sheathing takes up the rest

Time: 00:30:37.232 - 00:31:02.224

*on screen: A monolithic skin spans slack the frame never lost.*

What is left after settling is a lumpy brain of a frame that is near the sphere without being on it. The sheathing finishes the job. A skin bonded over the outside bridges every remaining gap and gives back the shell action the sloppiness cost. Once it is on, the structure behaves far more like the skin than like the frame, which is the whole reason the frame is allowed to be this bad.

On-screen math:

- the skin returns the shell action
- the structure becomes the skin, not the frame

## 74. One hundred and twenty sticks

Time: 00:31:02.224 - 00:31:30.072

*on screen: Forty triangles, three sticks each, and no hubs at all.*

Here is the thing that makes a franken-dome buildable by one person with no jig and no precision. It is hubless. Every one of the forty triangles is a closed triangle carrying its own three sticks, so the frame is a hundred and twenty struts rather than the sixty-five a hubbed dome needs. Fifty-five edges end up with two sticks lying against each other, ten rim edges carry one, and two times fifty-five plus ten is one hundred and twenty.

On-screen math:

- 40 triangles x 3 = 120 struts
- 55 shared edges x 2 sticks
- 10 rim edges x 1 stick

## 75. Why the edges double

Time: 00:31:30.072 - 00:31:50.264

*on screen: Two triangles meet, and each brings its own stick.*

Open one of those joints up and you can see it. Two triangles meet along an edge, and each of them arrives with its own complete stick, so the joint is a lap between two members rather than a point where several converge. That is the whole trick: nothing has to meet accurately at a point, because nothing meets at a point at all.

On-screen math:

- a lap, not a hub
- nothing converges, so nothing has to be accurate

## 76. The bill

Time: 00:31:50.264 - 00:32:17.152

*on screen: Under five thousand dollars, and the wood was free.*

The ledger, honestly. Timber: nothing, because I cut it down myself. Brackets: nothing, because I folded them out of a scrapped washing machine. Screws: forty-eight dollars. Fibreglass: about four thousand seven hundred. That is the whole structure for under five thousand dollars, which is roughly fifteen dollars a square foot of floor, and almost all of it is the one material I could not make myself.

On-screen math:

- timber $0, brackets $0
- screws $48
- fibreglass ~$4,700
- ~$15 per sq ft of floor

## 77. What it trades

Time: 00:32:17.152 - 00:32:49.992

*on screen: A little structure for a great deal of speed.*

So what is the trade? You give up precision, and with it any claim to a calculated structure. You get back an enormous amount of speed, a material cost near zero, and a method that tolerates stock nobody else would use. For a storage building, a workshop, or a shelter, where the covering matters more than the tolerance, I think that is a completely valid way to build. For anything inspected, occupied full time, or carrying snow you have not calculated for, it is not. Both of those things are true at once.

On-screen math:

- give up: precision and calculation
- get back: speed and near-zero cost

## 78. The frankendome, audited

Time: 00:32:49.992 - 00:33:18.632

*on screen: Ten days of work, six months of weather.*

And here is the ugly one on the math screen, counted like everything else. Forty triangles, three folded brackets each, eight screws a bracket, two bolts a seam. Ten days of work. It has now stood through half a year of weather -- eighteen times longer than it took to build, and counting. The point is not that sloppy is good. The point is that the shape carries what the craftsmanship cannot, and that is exactly the margin a first-time builder needs.

On-screen math:

- 40 triangles x 3 folded brackets = 120 brackets
- 120 brackets x 8 screws = 960 screws
- 65 seams x 2 bolts = 130 bolts, 260 washers
- built in 10 days = 4 triangles and 96 screws a day
- standing 6 months = 18x its own build time
- no milled lumber, no bought hubs, no machine shop --
- the geometry carried whatever the chainsaw made
- ten days of work has stood 18 times longer than it took to build -- that is what the shape forgives

## 79. The question

Time: 00:33:18.632 - 00:33:23.824

*on screen: What if a house was not a finished product?*

What if a house was not really a finished product? What if it was a platform?

On-screen math:


## 80. Build once

Time: 00:33:23.824 - 00:33:29.232

*on screen: Build the skeleton once. Keep the bones.*

Build the geodesic skeleton once. Keep the bones.

On-screen math:


## 81. Then everything else

Time: 00:33:29.232 - 00:33:39.824

*on screen: Then replace, repair, upgrade, mutate, Frankenstein.*

Then replace, repair, upgrade, mutate, Frankenstein, and occasionally bolt questionable things onto everything else for the next fifty years.

On-screen math:


## 82. Every answer is yes

Time: 00:33:39.824 - 00:33:49.840

*on screen: New insulation? Swap it. Solar panels? Add them.*

New insulation? Swap it. Solar panels? Add them. Greenhouse wall? Sure. Workshop extension? Absolutely.

On-screen math:


## 83. The organs are still good

Time: 00:33:49.840 - 00:33:57.984

*on screen: Excellent. The organs are still good.*

I like finding machinery somebody threw away and immediately thinking: excellent, the organs are still good.

On-screen math:


## 84. One shell, any skin

Time: 00:33:57.984 - 00:34:11.552

*on screen: The bones do not care what you paint on them.*

Same forty panels. Same hundred and twenty sticks. Different paint. A baseball. A basketball. A disco ball with a facet on every face. The structure does not care. It never did.

On-screen math:


## 85. Four lines, one skeleton

Time: 00:34:11.552 - 00:34:31.912

*on screen: Home, shed, greenhouse, shelter. Same bones.*

Four product lines already exist in the software. A dome home. A storage shed. A greenhouse. A storm shelter. Twenty-one feet to thirty, or ten to fifteen for the shelter. Four buildings, four price points, one skeleton, and the same forty triangles under every one of them.

On-screen math:


## 86. Frankendome

Time: 00:34:31.912 - 00:34:35.912

*on screen: FRANKENDOME!*

Frankendome!

On-screen math:


## 87. The pony wall

Time: 00:34:35.912 - 00:35:16.312

*on screen: 174 usable square feet becomes 272.*

Now the honest complaint about domes, and the fix for it. A hemisphere has a beautiful volume and almost none of it is against the edge, where the ceiling comes down to meet the floor. Out of three hundred and fourteen square feet you can only stand up in 174. The rest is crawl space with a view. So put the whole shell on a 3 foot wall. The ceiling profile lifts with it, and usable floor goes from 174 square feet to 272. That costs about 791 dollars, which works out near 8 dollars a square foot. It is the cheapest room in the building, and it is the first thing I would build into every one of them.

On-screen math:


## 88. Nine times the house, same parts list

Time: 00:35:16.312 - 00:35:37.728

*on screen: 79 sq ft or 707: 120 struts either way.*

And here is the part that makes it a business instead of a hobby. A 10 foot dome has 79 square feet of floor. A 30 foot dome has 707. Nine times the house. Both of them are 120 struts, 120 brackets and 960 screws. The sticks get longer. The parts list does not change at all.

On-screen math:


## 89. The flat rate, proved

Time: 00:35:37.728 - 00:36:09.800

*on screen: Nine times the house. The same parts list.*

This is the number that turns a weekend project into a product, so let us prove it rather than repeat it. Scale the dome from ten feet to thirty and count again. The floor grows nine times over, because area grows with the radius squared. The struts, the brackets and the screws do not change at all. The sticks get longer; the list of operations stays exactly the same length. Labor is priced by operations. That is why dome labor is a flat rate, and why the bigger house is the better deal.

On-screen math:

- scale the dome up and count what changes:
- 10 ft dome: 79 sq ft of floor
- 30 ft dome: 707 sq ft -- 9.0x the house
- struts either way: 120
- brackets either way: 120
- screws either way: 960
- floor area grows with radius squared;
- the parts list does not grow at all
- 9.0x the house for the same list of operations -- that is what makes it a product

## 90. The hat has to overhang

Time: 00:36:09.800 - 00:36:29.176

*on screen: Throw the water clear, or it runs into every joint.*

The top of the dome gets laminated like a hat. But a hat that stops flush with the wall is useless, because the water just runs down the face and into every joint below it. So the brim stands proud, with ribs to keep it stiff, and it throws the rain clear of the bottom ring entirely.

On-screen math:


## 91. The brim is already a gutter

Time: 00:36:29.176 - 00:36:52.872

*on screen: 7,259 gallons a year into a tank.*

And once it overhangs, it is a gutter. You have built the catchment whether you wanted one or not. An eighteen inch brim gives 343 square feet of catchment. On average rainfall that is 7,259 gallons a year, about 20 gallons a day, straight into a tank beside the door. One downpipe. No pump. The roof shape does the collecting.

On-screen math:


## 92. The water plant, derived

Time: 00:36:52.872 - 00:37:25.232

*on screen: Seven thousand gallons off a hat brim.*

The rain figure sounds invented, so here is where it comes from. The hat rim plus an eighteen inch brim sweeps a circle, and rain falls straight down, so the flat area of that circle is the catchment. Multiply by an average year of rain, by the gallons in an inch of water on a square foot, and by an honest runoff factor. The climate numbers are borrowed and named; substitute your own rainfall and the screen recomputes. The shape of the roof was already doing the collecting -- the tank just agrees to accept it.

On-screen math:

- hat rim radius = 8.9 ft; add an 18 in brim -> 10.4 ft
- catchment = pi x 10.4^2 = 343 sq ft of plan area
- x 40 in of rain a year x 0.6233 gal per sq ft inch
- x 0.85 runoff
- = 7,259 gallons a year, 20 a day, into a tank by the door
- no pump, one downpipe -- the roof shape does the collecting
- 7,259 gallons a year from a brim the rain was already running off

## 93. Glass the top, skip the bottom

Time: 00:37:25.232 - 00:37:51.928

*on screen: The lowest twenty triangles are exactly half the shell.*

Waterproofing is where the money goes, so here is the trick. Sort the forty triangles by height and the bottom twenty come to exactly half the surface. Exactly. That is a property of the shape, not a rounding. So glass the top twenty and leave the bottom ring to the siding. 292 square feet instead of 897. Half the resin, and resin is the expensive part.

On-screen math:


## 94. Every part, bought new

Time: 00:37:51.928 - 00:38:16.032

*on screen: $6,943 at the till, nothing salvaged.*

So price it honestly. Nothing free, nothing salvaged, nothing harvested. Pressure treated lumber off the rack. Sheathing, foam, epoxy, cloth, screws, and a basic kitchen and bathroom. It comes to 6,943 dollars. Three hundred and fourteen square feet of floor at 22 dollars a square foot, finished.

On-screen math:


## 95. The price guide, receipts attached

Time: 00:38:16.032 - 00:38:51.008

*on screen: Four ways to build it, priced at the till.*

Here is the price guide, and the rules it was priced under. Nothing salvaged, nothing donated, nothing found. Every board, every ounce of resin, every screw at retail. Four versions of the same twenty-foot starter home: the bare cheapest, a budget build, the pristine version with the laminated hat, and the fully glassed one. The cheapest is under the price of a used car, and the dearest finished shell is still under ten thousand dollars. Every line traces to a priced part in the costing module, and the audit report that ships with this film prints the lot.

On-screen math:

- one dome, 314 sq ft of floor (20 ft across), priced four ways,
- every part bought new at the till:
- CHEAPEST: $5,116  ($16/sq ft)
- BUDGET: $6,583  ($21/sq ft)
- PRISTINE, HAT: $6,943  ($22/sq ft)
- PRISTINE, FULL: $9,496  ($30/sq ft)
- $5,116 to $9,496 for a finished shell -- the cheapest is under the price of a used car

## 96. What it costs to run

Time: 00:38:51.008 - 00:39:19.768

*on screen: $129 a year to heat and cool.*

Now the number nobody puts on a listing. What does it cost to run. At 17 cents a kilowatt hour, with the cavity insulated, this dome takes about 129 dollars a year to heat and cool. Not a month. A year. The same floor in a square house costs 220, because it has 414 more square feet of skin to lose heat through. That is 91 dollars a year you never spend, on a building that was already cheaper to put up.

On-screen math:


## 97. A year of comfort, derived

Time: 00:39:19.768 - 00:39:52.296

*on screen: The skin you did not build never sends a bill.*

The running cost is the same arithmetic a heat-loss engineer does, so watch it happen. Take each building's skin area, times the wall's U value -- same insulation in both. Times the degree days of a middling American climate, heating and cooling both. Convert to kilowatt hours, price at seventeen cents. The dome wins by exactly its missing skin, every single year, forever. The climate and the power price are borrowed constants, named on screen; the geometry is not.

On-screen math:

- wall build-up: R-24.4 -> U = 1/R = 0.0410
- heat loss rate = skin x U:
- dome: 583 sq ft x 0.0410 = 24 BTU/hr/F
- box:  997 sq ft x 0.0410 = 41 BTU/hr/F
- x 4200 heating degree days and 1200 cooling
- dome: 756 kWh/yr = $129 at 17 cents
- box:  1,292 kWh/yr = $220
- $91 a year, every year, from the shape alone -- same insulation, same climate, same floor

## 98. A roof that refuses the sun

Time: 00:39:52.296 - 00:40:36.896

*on screen: Below air temperature, in full sun.*

And you can do better than that, with paint. Radiative sky cooling paint reflects about ninety six percent of sunlight, and it is a strong emitter in the eight to thirteen micron band, which happens to be the window the atmosphere is transparent at. So the heat does not stop in the air. It goes to space. The shell runs roughly 48 degrees cooler than a dark one, and it sits below air temperature in full sun. The roof stops being a heat source and becomes a heat sink. I will be straight with you about the money: on a well insulated shell that is only about 11 dollars a year, because very little of that heat was getting in anyway. On a thin wall it is more like 51. You do it for the comfort, and for the air conditioner you do not have to buy.

On-screen math:


## 99. What a line actually buys you

Time: 00:40:36.896 - 00:41:00.592

*on screen: Not less work. Less waiting.*

One crew doing all 15 stations spends 158 hours on a dome, and the next dome cannot start until the last one is finished. Split the same work across 15 stations and a dome comes off the end every 30.0 hours instead. The total labour did not change at all. What changed is that nobody is standing still waiting for someone else to finish.

On-screen math:

- serial = 158 h per dome
- pipelined = 30.0 h per dome

## 100. Every part is the same six motions

Time: 00:41:00.592 - 00:41:22.592

*on screen: Walk, lift, carry, position, fasten, recover. 493 seconds, 41.1 kilocalories.*

Whatever the part, the body does the same six things with it. It walks to the stockpile empty. It squats, grips, and stands the load up. It carries the load to where the part goes. It lifts the part into position, fixes it there, and straightens back up. Every one of those six has a duration taken from the part itself and a cost we can put a number on.

On-screen math:

- one part = 493 s
- one part = 41.08 kcal
- x 1322 parts

## 101. Where the shift actually goes

Time: 00:41:22.592 - 00:41:49.960

*on screen: Fastening raises nothing and spends 90 per cent of the fuel.*

Here is the result that surprises people. Fastening does no lifting at all. Nothing rises. No mechanical work is done against gravity in any meaningful amount. And it consumes 90 per cent of everything the crew burns, because it is 386 seconds per part of holding a posture, gripping a tool, and stabilising against its torque. The body pays for holding still. It pays a lot.

On-screen math:

- 386 s per part
- 49,366 kcal per dome
- mechanical share = 0.00 %

## 102. What a build costs the builders

Time: 00:41:49.960 - 00:42:23.472

*on screen: Attack the screw gun, not the lifting.*

One more derivation, because it changes what a dome factory should even be. Simulate every part placement in the build -- every walk, lift, carry, position, fastening and rest -- with the body model used in ergonomics research. The lifting everyone worries about turns out to be a fraction of one percent of the fuel. Fastening, which raises nothing at all, is ninety percent of it. So the factory's job is not a crane. It is jigs, batching and better fastening -- which is exactly what the jig shop and the line you saw are for.

On-screen math:

- simulate every part placement, all six motions, crew of 2:
- time on task = 191 hours each = 23.9 eight-hour shifts
- food energy = 54,870 kcal per worker
- mechanical work actually raising things = 87 kcal (0.16% of the fuel)
- fastening alone = 49,366 kcal (90% of the fuel) -- and it lifts nothing
- so a factory should not chase the lifting;
- it should chase the screw gun
- lifting is 0.2% of the effort; fastening is where the shift actually goes

## 103. What the money buys

Time: 00:42:23.472 - 00:42:52.496

*on screen: $86,000 of equipment, and the rest is material.*

Which brings me to the ask, and I will be specific about it, because vague asks deserve to fail. A used flatbed. A trailer. A used telehandler, because a dome goes up in panels and panels are heavy. A portable sawmill, so the timber line on that cost sheet really does go to zero. Saws, jigs, a compressor, laminating gear and extraction. Six months of rent with the lights on, and the paperwork that makes it a company instead of a yard.

On-screen math:


## 104. Ten reasons this shape

Time: 00:42:52.496 - 00:43:27.952

*on screen: For cheap, affordable, manufactured housing.*

So here is the whole argument in ten lines. Less exterior for the same floor. A parts list that does not grow with the house. Nine operations, endlessly repeated. Rigid because of its shape, not its bracing. Almost nothing for wind to push on. It costs what the parts cost. A stem wall buys back the wasted rim for eight dollars a square foot. Less skin means less to heat. A painted roof that refuses the sun. And a brim that collects the rain it was already throwing clear. Ten things, and every one of them is a consequence of the shape.

On-screen math:


## 105. Build one. Then build the next one faster.

Time: 00:43:27.952 - 00:44:07.200

*on screen: The geometry does not check your credit.*

So that is the whole argument. A shape that spends less on skin and gives it back every winter. Two lengths of wood, two jigs, six saw settings. A build method that forgave a chainsaw, so it will forgive you. A price list with receipts, an energy bill you can derive, and a factory whose economics are simulated down to the footsteps. Every number in this film came out of code you can run, and the parts that are borrowed are named out loud. A sphere encloses the most room with the least material whether you are a developer or a widow. The geometry does not check your credit. Build one. Then build the next one faster.

On-screen math:


## 106. Who is behind this

Time: 00:44:07.200 - 00:44:24.056

*on screen: For anyone wondering who is behind all these triangles.*

For anyone wondering who is behind all of this: I am a Navy veteran, a programmer, an F.A.A. accredited avionics bench technician, and a fabricator, now using the G.I. Bill to study aerospace engineering. A perfectly stable combination.

On-screen math:


## 107. Do the one thing

Time: 00:44:24.056 - 00:44:38.224

*on screen: Send this to one person who can carry it further than I can.*

If any of this was worth your time, send it to one person who can carry it further than I can. That is the whole ask. One share from somebody with reach does more for this than a month of me in a field with a chainsaw.

On-screen math:


## 108. Follow the experiments

Time: 00:44:38.224 - 00:44:57.288

*on screen: Follow the experiments.*

Everything is documented, including the parts that failed. Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok, short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot com and a Kickstarter for Frankendome are both coming soon.

On-screen math:

