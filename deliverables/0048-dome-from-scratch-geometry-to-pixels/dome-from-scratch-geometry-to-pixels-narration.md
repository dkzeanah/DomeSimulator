# From Scratch: Every Calculation Behind a Dome on Screen - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. Nothing but arithmetic

Time: 00:00:00.000 - 00:00:50.216

A dome on a screen is two calculations: a shape, and a picture.

Everything you are looking at started as arithmetic. There is no model file behind this dome, no artist, and no drawing. There is one number, a handful of formulas, and a list of instructions for turning the answers into coloured pixels. Over the next half hour we are going to do the whole job from nothing. First the shape: how a computer works out where the corners of a geodesic dome go, and how long each piece of timber has to be. Then the picture: how those corners become tubes and triangles, how a camera gets placed with two angles, and how a point in space turns into a particular pixel on your screen. Every number you see on a math screen in this film is worked out while the frame is being drawn, by the same code drawing it.

On-screen math:

- shape: 12 points -> 2 strut lengths
- picture: 3 matrices -> 1 divide -> pixels

## 02. The seven stations

Time: 00:00:50.216 - 00:01:51.328

Seven steps stand between one number and a lit pixel.

Here is the whole road, laid out. Station one: a single irrational number places twelve points in space. Station two: we divide each point by its own length, which puts them all on a sphere of radius one and turns the model into a recipe instead of a specific object. Station three: we halve every edge, which gives us more points, in slightly the wrong place. Station four: we push those points outward until they reach the sphere, and that single push is what makes the shape geodesic. Station five: the shape becomes a mesh, because a graphics card can only draw triangles. Station six: a camera is placed, and the whole world is moved in front of it. Station seven: a divide, a stretch, and a lighting sum turn all of that into the picture you are watching. Every station is a formula. We are going to do all seven.

On-screen math:

- geometry -> mesh -> camera -> pixels

## 03. Why the shape is triangles at all

Time: 00:01:51.328 - 00:02:40.104

A triangle cannot change shape without changing a side length.

Before any arithmetic, one decision. Why triangles? Push the top of a square frame and it leans over: the corners turn and the sides stay the same length. The shape has somewhere to go. Push the top of a triangle and nothing can move unless one of the three sides gets longer or shorter, which timber and steel are very unwilling to do. That is the whole reason a dome is made of triangles rather than panels. It is also, conveniently, the reason computer graphics is made of triangles: three points always lie in one flat plane, so a triangle can never be bent or twisted, and the maths for drawing one never has a special case. The same fact serves the builder and the renderer.

On-screen math:

- a triangle is fixed by its three side lengths
- three points always lie in one plane

## 04. Why we start from the icosahedron

Time: 00:02:40.104 - 00:03:30.776

Of the five perfectly regular solids, one starts closest to a ball.

We need a starting shape whose corners are spread as evenly as possible over a sphere, because every correction we make later is smaller when we start closer. There are exactly five solids where every face is the same regular polygon and every corner is identical: the tetrahedron with four faces, the cube with six, the octahedron with eight, the dodecahedron with twelve and the icosahedron with twenty. Five. That is not a shortlist, it is all of them that can exist. The icosahedron wins because twenty triangular faces already sit close to the surface of a ball, and because its faces are triangles to begin with, so subdividing them gives more triangles rather than some new shape we would have to think about.

On-screen math:

- faces: 4, 6, 8, 12, 20
- 20 triangles start closest to a sphere

## 05. Twelve points from one number

Time: 00:03:30.776 - 00:04:18.712

Three rectangles, one ratio, twelve perfectly spaced corners.

Here is where the arithmetic starts, and it starts with one number. Phi, written with the Greek letter that looks like a circle with a line through it, is one plus the square root of five, all divided by two. About one point six one eight. Take three rectangles, each one phi long and two units wide, and stand them at right angles to each other through a common centre. Their twelve corners are the twelve corners of an icosahedron. In coordinates that means every combination of zero, plus or minus one, and plus or minus phi, in each of three orders. That is the entire input to this project. One number, arranged.

On-screen math:

- phi = (1 + sqrt 5) / 2 = 1.618034
- (0, +/-1, +/-phi) and its two rotations

## 06. Where the twelve points come from

Time: 00:04:18.712 - 00:05:16.992

One number, three families of coordinates, twelve even points.

Let us do that properly, on the math screen. Phi is defined as one plus the square root of five over two. Its defining property is that phi squared equals phi plus one, which is what makes it turn up whenever a shape has fivefold symmetry. Writing zero, plus or minus one and plus or minus phi in three rotating orders gives three families of four points each: twelve in total. The bars either side of v mean the length of v, which is the square root of x squared plus y squared plus z squared, straight out of Pythagoras in three dimensions. Measure the closest pair of those twelve points and you get exactly two. Measure any point's distance from the centre and you get the square root of one plus phi squared, the same for all twelve. Even spacing, and a common radius, for free.

On-screen math:

- start with one number and nothing else:
- phi = (1 + sqrt 5) / 2 = 1.618033989
-   phi is the number whose square is itself plus one
- build 12 points by putting 0, +/-1 and +/-phi in every order:
-   (0, +/-1, +/-phi), (+/-1, +/-phi, 0), (+/-phi, 0, +/-1)
-   3 families x 4 sign choices = 12 points
- measure the closest pair of those points:
-   nearest-neighbour distance = 2.000000000
- measure each point's distance from the centre:
-   |v| = sqrt(1 + phi^2) = 1.902113033  (all 12 the same)
-   |v| means length: sqrt(x^2 + y^2 + z^2)
- every point is 2.000 from its neighbours and 1.902113 from the middle
- One irrational number places twelve points in perfectly even space -- that is an icosahedron, and it is the entire starting stock of the dome.

## 07. Putting them on a sphere of radius one

Time: 00:05:16.992 - 00:05:59.888

Divide every point by its own length and the model becomes a recipe.

Those twelve points sit at a radius of one point nine oh two, which is a useless number to design with. So we normalize. Normalizing means dividing a point's coordinates by its own distance from the centre. The direction is untouched. Only the distance changes, and it becomes exactly one. Now every measurement on this model is a fraction of the radius rather than a length. That is the single most useful thing in this whole film, because it means we never have to redo the geometry. Pick a radius at the very end, multiply, and the same numbers give you a greenhouse or an aircraft hangar.

On-screen math:

- v_hat = v / |v|
- edge = 2 / sqrt(1 + phi^2) = 1.051462 R

## 08. The divide that makes it reusable

Time: 00:05:59.888 - 00:06:49.864

Length one in, length one out; every distance becomes a multiplier.

On screen: the raw points, their awkward radius, and the divide that fixes it. V hat, spoken as v-hat, is the usual way to write a vector that has been scaled to length one. Check the result and every one of the twelve now sits at radius one, to the last decimal place a computer can hold. The edge that measured exactly two now measures one point zero five one four six two. That number is called a chord factor. It is not a length. It is what you multiply a radius by to get a length. Chord factor times radius in inches gives inches; times radius in metres gives metres. The geometry no longer knows or cares which.

On-screen math:

- the 12 raw points sit on a sphere of an awkward radius:
-   |v| = 1.902113033   (not 1, not anything useful)
- divide every point by its own length -- 'normalize':
-   v_hat = v / |v|     same direction, length set to 1
-   check: every point is now at radius 1.000000000 to 1.000000000
- the edge that measured 2.000000 becomes:
-   2 / sqrt(1 + phi^2) = 1.051462224
- that number is a CHORD FACTOR: a multiplier, not a length
-   length in inches = chord factor x radius in inches
- so the model is unit-free -- pick the size later, once, and
-   the same numbers serve a playhouse and a hangar
- Normalizing turns one specific solid into a reusable recipe: every distance becomes a multiple of a radius you have not chosen yet.

## 09. Counting the surface

Time: 00:06:49.864 - 00:07:39.960

Corners, edges and faces, and the check that catches every mistake.

Before going further we should check that what we have built is actually a closed surface and not a bag with a hole in it. Count the corners: twelve. Count the triangular faces: twenty. Each face has three sides, and every side is shared with exactly one neighbour, so the number of edges is twenty times three divided by two, which is thirty. Now add them up in a particular way: corners minus edges plus faces. For any closed surface without holes, that always comes to two. It is true of a cube, a pyramid, a football and this icosahedron. If it does not come to two, something in the model is broken, and it is far cheaper to find that out now than after cutting the timber.

On-screen math:

- V - E + F = 2
- E = F x 3 / 2 = 30

## 10. Euler's check

Time: 00:07:39.960 - 00:08:29.960

One addition proves the model closed.

Here is the count, run live against the model on the left. V for vertices, which is just a mathematician's word for corners. E for edges. F for faces. The reason edges equal faces times three over two is worth saying slowly: every triangle contributes three sides, but each side is shared between two triangles, so counting sides double-counts every edge. Divide by two and the double counting goes away. Twelve minus thirty plus twenty is two. And when we subdivide later and end up with forty-two corners, a hundred and twenty edges and eighty faces, the same sum still gives two. That is not a coincidence, it is a property of any closed surface, and it is the cheapest bug detector in geometry.

On-screen math:

- the icosahedron, counted off the model on the left:
-   V = corners        = 12
-   F = triangle faces = 20
- every face has 3 sides and every side is shared by 2 faces:
-   E = F x 3 / 2 = 20 x 3 / 2 = 30
-   counted directly off the model: E = 30
- Euler's rule, true of any closed surface without holes:
-   V - E + F = 12 - 30 + 20 = 2
-   a closed surface always gives 2 -- anything else is a bug:
-   a missing face, a doubled corner, a hole in the mesh
- run it again after subdividing, on 42 corners and 80 faces:
-   42 - 120 + 80 = 2
- V - E + F = 2 is the cheapest proof in geometry that the shape in memory really closed up.

## 11. Cutting every edge in half

Time: 00:08:29.960 - 00:09:15.400

Thirty new points, all of them slightly too close to the centre.

Twenty triangles is not enough for a building. To get more, we subdivide: mark the midpoint of every edge, and use those midpoints to cut each triangle into four smaller ones. The midpoint of two points is the plainest formula in this film. Add the two sets of coordinates together and halve them. That is all an average is. But look at where the midpoint lands. The two ends of the edge are on the sphere. The straight line between them cuts through the inside of the sphere, so its middle is nearer the centre than the ends are. Measure it and you get zero point eight five zero, not one. Those points are in the wrong place, and fixing that is the next step.

On-screen math:

- m = (a + b) / 2
- |m| = 0.850651, not 1

## 12. How far in the midpoint falls

Time: 00:09:15.400 - 00:10:05.184

The straight line cuts the corner; the sag is fifteen percent.

The numbers behind that. A and b both have length one, because we normalized them. Their average has length zero point eight five zero six five one. The difference, about zero point one four nine of the radius, is how far short of the surface the midpoint lands. That sounds small until you scale it: on the dome this project measures, with a radius just under ten feet, it is more than seventeen inches of sag. If you stop here you do get a valid shape. It is a subdivided icosahedron: twenty triangles turned into eighty, but still visibly faceted, with the original twenty flat faces staring back at you. It is not a dome, and its struts come in the wrong lengths.

On-screen math:

- take one edge of the icosahedron, between corners a and b
- the halfway point is the plain average of the two:
-   m = (a + b) / 2     add the coordinates, halve them
-   |a| = 1.000000   |b| = 1.000000   (both on the sphere)
-   |m| = 0.850650808               (NOT on the sphere)
- a straight line between two points on a ball cuts inside it:
-   shortfall = 1 - 0.850651 = 0.149349192 of the radius
-   on this lesson's 9.7 ft radius dome, that is 17.38 in
- leave the 30 midpoints where they landed and you get a
-   faceted icosahedron with more triangles -- not a dome
- Halving an edge is the easy half of subdivision: those points sit 14.93% of the radius too deep, and have to be pushed out.

## 13. The push that makes it geodesic

Time: 00:10:05.184 - 00:10:58.568

One divide moves thirty points onto the sphere and changes everything.

Here is the step the whole shape turns on, and it is the same divide we already used. Take a midpoint. Draw a ray from the centre of the sphere through it, and slide the point along that ray until it is exactly one radius from the centre. That is projection. In arithmetic it is p equals m divided by the length of m: same direction, new distance. Watch what it does. The point moves out, so the four small triangles in each original face are no longer flat and no longer identical. The surface stops being twenty flat plates and starts being a sphere. And the edges, which were all equal a moment ago, are now two different lengths. One divide. That is the difference between a faceted ball and a geodesic dome.

On-screen math:

- p = m / |m|
- the surface bulges; the edges split into two

## 14. Projection, exactly

Time: 00:10:58.568 - 00:11:48.568

Same direction, distance set to the radius.

Formally: p equals m over the length of m. Dividing a vector by its own length always gives length one, and never changes which way it points, which is exactly what we want. The point travels along its own ray and lands on the surface. Every one of the thirty midpoints moves out by the same fraction of the radius, because on this shape they all started at the same depth. But they move away from their neighbours by different amounts depending on where those neighbours are, and that is what splits one edge length into two. This is also why the word geodesic is used. A geodesic is the shortest path across a curved surface, and these struts are straight lines standing in for exactly those paths.

On-screen math:

- push each midpoint straight out from the centre until it
- reaches the sphere -- and that is the same divide as before:
-   p = m / |m|     m chose the direction, the divide fixes the
-                   distance
-   |m| = 0.850650808  ->  |p| = 1.000000000
-   distance travelled = 1 - |m| = 0.149349192 radii
- the direction never changes, only the distance from centre:
-   each point slides along its own ray, so the face keeps its
-   shape and simply bulges outward
- this is the single line that separates a subdivided
-   icosahedron from a geodesic sphere
- and it is what breaks the equal edges: the four small
-   triangles in each face are no longer the same size
- One division by a length -- p = m / |m| -- is the entire difference between a faceted ball and a geodesic dome.

## 15. Measuring what came out

Time: 00:11:48.568 - 00:12:34.248

A hundred and twenty edges, and exactly two different lengths.

Now we simply measure. Every edge of the new surface, one at a time, and then sort the answers. A hundred and twenty edges come back with exactly two distinct lengths and nothing in between. Not approximately two: two, to the limit of what a computer can represent. The colours you are looking at are assigned by that measurement, not by a naming convention. The shorter one runs from an original corner to a projected midpoint. The longer one runs between two projected midpoints. Published dome tables call them A and B, but different tables disagree about which is which, so this project says SHORT and LONG and stays out of the argument.

On-screen math:

- SHORT = 0.546533 R
- LONG = 0.618034 R

## 16. Two lengths, four ways

Time: 00:12:34.248 - 00:13:34.248

Coordinates, angles, the law of cosines and CAD all agree.

The two chord factors, and four independent ways of getting them. Route one is brute force: subtract one end's coordinates from the other's and take the length of what is left. Route two goes through the angle. The dot product of two unit vectors is the cosine of the angle between them, so the inverse cosine of u dot v gives the central angle: the angle subtended at the centre of the sphere. Feed that into chord equals two R sine of theta over two, which is the standard chord formula from any circle, and out comes the same number. They agree to about one part in ten thousand million million, which is floating point dust rather than disagreement. And look at the long one: zero point six one eight zero three four. That is one over phi, exactly. But the ratio between the two struts is one point one three, not phi. People expect the golden ratio to come out at the end because it went in at the start. It does not.

On-screen math:

- measure all 120 edges of the finished sphere. They fall into
- exactly two lengths -- no more, no fewer:
-   SHORT = 0.546533058 R   x60
-   LONG  = 0.618033989 R   x60
-   R is the radius; these are multipliers, not inches
- four independent routes to that same SHORT number:
-   1. subtract coordinates:  |u - v| = 0.546533058
-   2. central angle: theta = acos(u . v) = 31.717474 deg
-      chord = 2 sin(theta / 2) = 0.546533058
-   3. law of cosines on the same triangle: identical
-   4. measure it in CAD: identical
-   routes 1 and 2 differ by 1.11e-16
- the ratio nobody guesses: LONG / SHORT = 1.130826361
-   and LONG = 0.618033989 = 1 / phi, exactly
- Two lengths, 30 of one and 35 of the other in the finished dome, in a ratio of 1.130826 -- which is not the golden ratio, and that surprise is the whole point.

## 17. Never trust one calculation

Time: 00:13:34.248 - 00:14:13.136

Four routes to the same number is not waste; it is the proof.

It is worth saying why we bothered doing that four different ways. A single calculation that agrees with itself proves nothing. Four calculations that share no working, and land on the same number, prove that the number is a property of the shape rather than an artefact of one method or one typo. This is the habit that separates a model you can build from a model that merely runs. Every figure in this repository is computed, and wherever there are two ways to compute it, both are checked against each other before anything reaches a screen.

On-screen math:

- c = |R u - R v|
- theta = acos(u . v)
- c = 2 R sin(theta / 2)

## 18. Half a sphere is a building

Time: 00:14:13.136 - 00:14:57.640

Keep every face above the equator and count what you have.

A sphere is not a house. Cut it at the equator and keep the top, and now it is one. The cut is trivial in code: keep every face whose three corners all sit at or above zero height. This particular arrangement of the icosahedron has a genuine ring of corners exactly at the equator, so the cut is clean, with no half-triangles to fudge. What survives is forty triangular panels, sixty-five struts, and twenty-six hubs where those struts meet. Thirty of the struts are the short one and thirty-five are the long one. Ten corners sit on the ground, and that ring is what your foundation follows.

On-screen math:

- keep faces with all z >= 0
- 40 panels, 65 struts, 26 hubs

## 19. Counting the building

Time: 00:14:57.640 - 00:15:47.640

Every part, counted off the model rather than looked up.

These are counts, made now, off the same model being drawn beside the panel. Forty panels. Thirty short struts, thirty-five long ones, sixty-five in total. Twenty-six hubs. The cross-check is the same shared-edge argument as before. Forty triangles have a hundred and twenty sides between them, but most of those sides are shared with a neighbouring triangle, and the ones around the open base are not shared at all. Work through it and a hundred and twenty side-slots close up into exactly sixty-five real struts. Two lengths and a count. That is the entire bill of materials for the frame of a building.

On-screen math:

- a dome is the top half of the sphere. Keep every face whose
- corners all sit at z >= 0, and count what survives:
-   triangular panels                = 40
-   SHORT struts                     = 30
-   LONG struts                      = 35
-   struts total                     = 65
-   hubs (corners where struts meet) = 26
-   base ring corners                = 10
- cross-check: 40 panels x 3 sides = 120 side
-   slots, but interior sides are shared by two panels, which
-   is why 120 slots close into only 65 real
-   struts
- not one of these was typed in -- they are counted, now, off
-   the same model being drawn on the left of this screen
- 40 panels, 65 struts, 26 hubs: a complete shelter, described by two lengths and a count.

## 20. Choosing a size, at last

Time: 00:15:47.640 - 00:16:41.096

One multiplication turns the recipe into a cut list.

Everything so far has been unit-free. Now we choose a size, and we do it exactly once. This project started from two real boards someone measured: seventy two inches and sixty three and a half. Divide each by its chord factor and each board implies a radius. The two answers differ slightly, because tape measures, saw kerfs and hub fittings are real things. Rather than pick a favourite, we use least squares: the radius that makes the total of the squared misses as small as possible. It lands between the two, missing each by about a tenth of an inch. Multiply the two chord factors by that radius and you have a cut list. Thirty pieces at one length, thirty-five at the other, and a note that those are hub centre to hub centre, not saw cuts.

On-screen math:

- R = length / chord factor
- cut length = centre length - connector deduction

## 21. From factors to lumber

Time: 00:16:41.096 - 00:17:43.192

Two boards, one best-fit radius, sixty-five cuts.

The fit, in full. Each measured board on its own implies a radius, and the two disagree by about a third of an inch. Least squares is worth a sentence, because it sounds harder than it is. Each candidate radius predicts a length for each board. Subtract the prediction from the measurement and you get a residual: how wrong that guess was. Square the residuals so that overshoot and undershoot both count as error, add them up, and pick the radius where that total is smallest. There is a formula that jumps straight to the answer, and that is what the code uses. The result is a dome a shade under twenty feet across, with about three hundred square feet of floor, and two numbers on a cut list. Notice the last line. What comes out is the distance between hub centres. What your saw needs is that minus whatever your connector occupies at each end, and no geometry can tell you that. Your hardware does.

On-screen math:

- the model is still unit-free. Two measured boards fix it:
-   measured LONG  = 72.0 in
-   measured SHORT = 63.5 in
- each board on its own implies a radius:
-   R from LONG  = 72.0 / 0.618034 = 116.498 in
-   R from SHORT = 63.5 / 0.546533 = 116.187 in
- they disagree, because tapes and saws are not exact
- least squares picks the radius that misses both by least:
-   best-fit R = 116.362 in = 9.70 ft
-   residuals  = +0.084 in and -0.096 in
- multiply the two chord factors by that radius:
-   30 SHORT @ 63.596 in
-   35 LONG  @ 71.916 in
-   hub-centre to hub-centre; the physical cut is that minus
-   whatever the connector eats at each end
-   floor 295.4 sq ft, height 9.70 ft, span 19.39 ft
- One multiplication turns the unit-free model into a cut list for a 19.4 foot dome.

## 22. A line with no thickness

Time: 00:17:43.192 - 00:18:33.840

Graphics cards draw triangles. Nothing else. Not even lines.

The shape is finished. Now we have to make it visible, and the first surprise is that we cannot simply draw it. A graphics card draws triangles. That is very nearly the whole of its vocabulary. Our struts are pairs of points with no thickness at all, so each one has to be given a body: a tube, built out of triangles, wrapped around the line where the strut goes. To build a ring around a line you need two directions square to that line. The cross product gives you them. Cross the strut direction with any other direction and you get something perpendicular to both; cross that with the strut again and you have a second perpendicular. Now you can walk in a circle around the axis using sine and cosine, the way you would around any circle.

On-screen math:

- d = (b - a) / |b - a|
- s = d x t,  u = d x s

## 23. Building one strut

Time: 00:18:33.840 - 00:19:35.840

Two cross products, eight points, twenty-eight triangles.

The arithmetic for one strut. D is the direction, found by subtracting the ends and normalizing, which by now should feel familiar. T is any convenient direction that is not parallel to d. The code picks straight up unless the strut is nearly vertical, in which case it picks sideways instead, because crossing two parallel directions gives you nothing at all. The ring formula is just a circle drawn in the plane defined by s and u. Two pi i over n walks all the way round in n even steps. Do it at both ends and join corresponding points, and the tube is a strip of quadrilaterals, each of which is two triangles. Eight sides gives sixteen triangles of tube, plus twelve more to cap the ends: twenty-eight triangles for one strut. Multiply by sixty-five and the frame alone is one thousand eight hundred and twenty triangles.

On-screen math:

- a strut in the model is two points. A graphics card cannot
- draw a line with thickness -- it draws triangles and nothing
- else. So the line has to be given a body:
-   d = (b - a) / |b - a|     the direction of the strut
-   pick any t that is not parallel to d, then
-   s = d x t   and   u = d x s      x is the cross product
-   the cross product of two directions returns a third at
-   right angles to both -- exactly what a ring needs
- walk a ring of 8 points around the axis:
-   ring(i) = a + r ( s cos(2 pi i / n) + u sin(2 pi i / n) )
-   r is the strut radius, n the number of sides
- do the same at b, then stitch the two rings together:
-   8 side quads = 16 triangles
-   2 end caps   = 12 triangles
-   one strut    = 28 triangles
-   x 65 struts  = 1,820 triangles of frame
- Every visible line in this film is really a tube of 8 flat sides and 28 triangles, built by two cross products.

## 24. Which way does a triangle face?

Time: 00:19:35.840 - 00:20:24.088

The order you list the corners in decides which side is the front.

A triangle needs a front and a back. Without one it cannot be lit, because lighting depends on the angle between the surface and the light, and it cannot be hidden, because there would be no way to tell the inside of the dome from the outside. The direction a face points is called its normal, and it comes from a cross product of two of its edges. Cross products care about order, so listing the corners a, b, c gives a normal pointing one way, and listing them a, c, b gives one pointing the other. The convention here, and in almost all graphics, is counter-clockwise as seen from the front. Get it backwards on one triangle and it disappears. Get it backwards everywhere and your dome turns inside out.

On-screen math:

- n = (b - a) x (c - a)
- counter-clockwise = facing you

## 25. The normal, the area and the winding

Time: 00:20:24.088 - 00:21:18.088

One cross product, three answers.

The cross product of two edge vectors gives a third vector at right angles to both, so it sticks straight out of the surface. Dividing it by its own length makes it exactly one long, which the lighting maths will assume later. The length you divided by was not wasted, either: it is twice the area of the triangle. So one cross product tells you which way the face points and how big it is. The check on the last line is a dot product between the normal and the direction from the dome's centre out to the face. It comes to very nearly plus one, which means the normal points outward, which means the corners were listed the right way round. This is the sort of check worth automating. A dome with one triangle wound backwards has a hole in it that only appears from one angle.

On-screen math:

- a triangle has to know which way it faces, or it cannot be
- lit and cannot be hidden. Take its three corners a, b, c:
-   n = (b - a) x (c - a)     cross product of two of its edges
-   n = (-5.2153, +4.0021, +2.3011)
-   n stands at right angles to the surface: the NORMAL
-   divide by its length to make it exactly 1 long, which is
-   what the lighting maths assumes:
-   n_hat = (-0.748783, +0.574604, +0.330384)
- the same cross product hands you the area for free:
-   area = |n| / 2 = 3.482504 square world units
- corner ORDER decides the sign. Listed counter-clockwise as
-   seen from outside, n points outward:
-   n_hat . (direction away from centre) = +0.999468
-   list them the other way round and the dome turns inside
-   out: lit from within, and thrown away as back-facing
- One cross product answers three questions at once: which way the face points, how big it is, and whether it was wound the right way round.

## 26. The model becomes a list of numbers

Time: 00:21:18.088 - 00:22:08.424

Points, edges and faces all flatten into one long array.

At this point the elegant structure goes away. Corners, edges, faces, the classes of strut: none of that survives the trip to the graphics card. What the card gets is one flat list of numbers. Ten per vertex: three for where it is, three for which way its surface faces, and four for colour, the fourth being opacity. Three vertices in a row make a triangle. That is the entire format. It is deliberately wasteful. Corners that are shared between triangles are written out again for each one, because that lets every face carry its own flat normal and its own colour. Memory is cheap and the alternative is a picture where every strut is smeared into its neighbour.

On-screen math:

- 10 floats per vertex = 40 bytes
- 3 vertices = 1 triangle

## 27. Counting the actual upload

Time: 00:22:08.424 - 00:23:00.424

The dome beside this panel, in floats, vertices and kilobytes.

This is not an estimate. The list on the right counts the batch of numbers that the dome on the left was drawn from, in the frame you are watching. A float is a single number as a computer stores it, four bytes each. Ten of them per vertex is forty bytes. Three vertices per triangle is a hundred and twenty bytes per triangle. Three thousand nine hundred triangles, eleven thousand seven hundred vertices, four hundred and fifty seven kilobytes. That is the whole dome as the graphics card understands it, and it is rebuilt and sent across thirty times a second, because the animation may have changed something. For comparison, that is smaller than a single photograph.

On-screen math:

- by now the model is not points and edges any more. It is one
- flat list of numbers. Ten of them per vertex:
-   position x y z    where this corner is
-   normal   x y z    which way its surface faces
-   colour   r g b a  what shade it is; a is opacity
-   10 floats x 4 bytes = 40 bytes per vertex
- count the dome standing to the left of this panel:
-   floats    = 117,000
-   vertices  = 117,000 / 10 = 11,700
-   triangles = 11,700 / 3  = 3,900
-   bytes     = 468,000 = 457.0 KB
- no corner is shared between triangles here: three fresh
-   vertices per face. That costs memory and buys the freedom
-   to give every face its own flat normal and its own colour
- and that buffer is rebuilt and re-uploaded 30 times a second
- The dome beside this panel is 3,900 triangles and 457 KB of plain numbers. That is the whole model, as the card sees it.

## 28. Where things are: world space

Time: 00:23:00.424 - 00:23:48.936

One agreed origin, three axes, and everything measured from them.

Before we can photograph the dome we have to agree where everything is. That agreement is called world space, and it is nothing more than a chosen origin and three directions at right angles. In this project, X and Y run along the ground and Z points up, which is the convention surveyors and architects use. The dome is built around the origin, at a radius of five world units. World units are not metres or feet. They are whatever we decide, and the geometry only cares about ratios. What matters is that the camera, the light and the model all speak the same units, because everything from here on is subtraction between positions.

On-screen math:

- origin = (0, 0, 0)
- +Z is up; the dome has radius 5

## 29. Placing the camera with two angles

Time: 00:23:48.936 - 00:24:16.936

Yaw, pitch and distance become one point in space.

A camera needs a position and something to look at. Rather than type coordinates, we use the way a person actually thinks about a camera: how far around it is, how high up it is, and how far back. Those are yaw, pitch and distance. Yaw is the angle around the vertical axis, pitch is the angle up from the ground, and distance is simply how far from the thing being looked at. Turning them into a position is straight trigonometry. Cosine of the pitch tells you how much of the distance is spread out along the ground, and sine of the pitch tells you how much of it went upward. Split the ground part between X and Y using the cosine and sine of the yaw, and you have your point. Every chapter of this film states its camera as those three numbers.

On-screen math:

- eye = target + d (cos p cos y, cos p sin y, sin p)

## 30. The camera position, computed

Time: 00:24:16.936 - 00:25:08.936

Two angles and a distance become a point you can check.

Here are the real numbers for a real chapter of this film: yaw thirty-four degrees, pitch twenty-four, distance fifteen, aimed at a point two and a quarter units above the origin, which is roughly the middle of the dome. Cosine of twenty-four degrees is about zero point nine one, so ninety-one percent of the distance lies along the ground. Sine of twenty-four is about zero point four one, so the rest went up. Out comes an eye position of about eleven point four, seven point seven, eight point four. And the check on the last line matters: measure from that point back to the target and you get fifteen point zero zero, which is the distance we asked for. If trigonometry has gone in the right slots, that check passes automatically.

On-screen math:

- the camera orbits the model. Three numbers place it:
-   yaw      = 34.0 deg    how far around
-   pitch    = 24.0 deg    how high up
-   distance = 15.0      how far back
-   target   = (0.00, 0.00, 2.25)   what it looks at
- turn two angles and a distance into a position:
-   eye_x = target_x + distance cos(pitch) cos(yaw)
-   eye_y = target_y + distance cos(pitch) sin(yaw)
-   eye_z = target_z + distance sin(pitch)
-   cos(24 deg) = 0.913545   sin(24 deg) = 0.406737
-   eye = (11.3605, 7.6627, 8.3510)
-   check: |eye - target| = 15.0000 = the distance we asked for
- Two angles and a distance become one point in space -- and every calculation from here on is measured from that point.

## 31. Moving the world instead of the camera

Time: 00:25:08.936 - 00:25:59.824

The card has no camera. So we move everything else.

Here is the idea that surprises people most. A graphics card does not have a camera. It draws whatever is sitting in front of a fixed eye at the origin, looking down one particular axis, always. So instead of moving the camera to a good spot, we move the entire world so that the good spot lands on the origin. That transformation is called the view matrix, and it is built from three directions. Forward is from the eye toward the target. Right is the cross product of forward with a rough idea of up, which is why it comes out perfectly horizontal. And true up is right crossed with forward again, which corrects for the tilt of the camera. Three directions at right angles, and one offset for where the eye was. That is the whole matrix.

On-screen math:

- f = normalize(target - eye)
- r = f x up,  u = r x f

## 32. The view matrix, entry by entry

Time: 00:25:59.824 - 00:26:56.808

Three directions in the rows, minus the eye in the last column.

The three directions, and the matrix they build. Look at the top three rows. Each one is one of our directions, and multiplying a point by that row is a dot product, which measures how far along that direction the point lies. So the multiplication answers three questions at once: how far right, how far up, and how far forward, from the camera's point of view. The last column is where the eye's own position gets subtracted. It is written as minus each row dotted with the eye, which packs a rotation and a slide into one multiplication instead of two. The line showing r dot f as a number with e minus seventeen in it is not a mistake. It says the two directions are perpendicular to within the accuracy a computer can represent, which is as perpendicular as anything gets in floating point.

On-screen math:

- a graphics card cannot move a camera. It draws whatever sits
- in front of a fixed eye at the origin, looking down one axis.
- So we do not move the camera to the world. We move the world
- to the camera. Build three directions from the eye:
-   f = (target - eye) / |target - eye|      forward
-   r = f x up_hint, normalized              right
-   u = r x f                                true up
-   f = (-0.757364, -0.510848, -0.406737)
-   r = (-0.559193, +0.829038, +0.000000)
-   u = (-0.337200, -0.227444, +0.913545)
-   all square to each other: r . f = +5.6e-17
- stack them as rows, eye offset in the last column:
-   [ -0.5592,  0.8290,  0.0000,  0.0000 ]
-   [ -0.3372,  -0.2274,  0.9135,  -2.0555 ]
-   [ 0.7574,  0.5108,  0.4067,  -15.9152 ]
-   [ 0.0000,  0.0000,  0.0000,  1.0000 ]
-   that last column is -(row . eye): turn first, then slide,
-   both in one multiplication instead of two
- The view matrix is three directions and one offset, packed so the world arrives already facing the camera.

## 33. What the lens can see

Time: 00:26:56.808 - 00:27:49.664

A pyramid with its tip cut off, and everything outside is discarded.

The camera cannot see everything. It sees a wedge: everything inside a certain angle, further away than a near limit and closer than a far one. The shape of that wedge is a pyramid with its tip cut off, and it has the excellent name frustum. The angle is the field of view. This film uses forty-eight degrees measured vertically, which is a slightly long lens: calm, not dramatic. The horizontal angle is wider, because the frame is wider than it is tall, and that ratio is called the aspect. The near and far limits exist for a practical reason we will get to: they set the range of depths the card can tell apart. Anything outside the frustum is thrown away before it costs anything to draw.

On-screen math:

- fov = 48 deg vertical
- near = 0.08, far = 120

## 34. The projection matrix

Time: 00:27:49.664 - 00:28:45.664

The matrix does not shrink anything. It arranges the divide.

This is the matrix people find hardest, so here it is in pieces. F, on the top two rows, is one over the tangent of half the field of view. A narrow lens gives a big f, which spreads the picture out; a wide lens gives a small f, which squeezes more in. The x row is divided by the aspect so that a wide frame does not stretch everything sideways. The third row remaps depth into the range the card wants, using the near and far limits. The fourth row is where the magic actually lives, and it does almost nothing: it copies the point's depth, negated, into a fourth slot called w. No division has happened yet. All the matrix has done is put each point's distance somewhere the next step can find it.

On-screen math:

- perspective is one idea: things look smaller the further off
- they are, so divide by distance. The matrix sets up that
- divide -- it does not perform it.
-   field of view = 48.0 deg  (how wide the lens is)
-   aspect = 1920 / 1080 = 1.777778
-   near = 0.08, far = 120.0  (outside this range, nothing is drawn)
-   f = 1 / tan(fov / 2) = 2.246037
-   [ 1.2634,  0.0000,  0.0000,  0.0000 ]  <- x, scaled by f / aspect
-   [ 0.0000,  2.2460,  0.0000,  0.0000 ]  <- y, scaled by f
-   [ 0.0000,  0.0000,  -1.0013,  -0.1601 ]  <- z, remapped into near..far
-   [ 0.0000,  0.0000,  -1.0000,  0.0000 ]  <- the whole trick
-   the last row copies -z into w, the fourth slot. That is
-   the only reason anything ever looks smaller with distance
-   row 2's -1.001334 and -0.160107 are (far+near)/(near-far)
-   and 2 far near/(near-far): they squeeze depth into 0..1
- The projection matrix shrinks nothing. It loads each point's depth into w, so that the divide coming next can do the shrinking.

## 35. The divide that makes distance work

Time: 00:28:45.664 - 00:29:35.088

Divide by w and the whole world folds into a two-unit cube.

Now the divide. Every point's x, y and z get divided by that fourth number, w, which is the point's distance from the camera. Because it is a division by distance, things twice as far away end up half as big. That is perspective. Not a special effect, not a formula for foreshortening: a division that had to happen anyway to get the numbers into range. What comes out is called normalized device coordinates, and everything the camera can see now lies inside a cube running from minus one to plus one on every axis. The wireframe on the left is this project's own dome, put through the real matrix and really divided. That is why it leans: the near struts kept more of their size than the far ones did.

On-screen math:

- ndc = clip / w
- everything visible is inside -1 .. +1

## 36. Landing on a pixel

Time: 00:29:35.088 - 00:30:17.528

One stretch turns the cube into the frame you are watching.

The last step of position is almost insultingly simple after that. The cube runs from minus one to plus one. The frame runs from zero to nineteen twenty across and zero to ten eighty down. So: add one, halve it, multiply by the width. Same for height. The only wrinkle is that screens count rows downward from the top left, while our cube counts upward, so the vertical one gets flipped. That is the one minus in the formula. Every label you have seen floating over a strut in this film was placed by exactly this calculation, running on the point in the middle of that strut.

On-screen math:

- px = (ndc_x * 0.5 + 0.5) * width
- py = (1 - (ndc_y * 0.5 + 0.5)) * height

## 37. One vertex, all the way

Time: 00:30:17.528 - 00:31:19.528

World, camera, clip, cube, pixel -- with the numbers at each stop.

Let us follow one point the whole way and watch it change at every stop. The point is the very top of the dome, five units above the origin, which we can all agree on without any arithmetic. Written as four numbers with a one on the end. That one marks it as a position rather than a direction, so that the sliding part of the view matrix applies to it. After the view matrix it is expressed from the camera's point of view, and its third number is depth into the screen. After the projection matrix, look at w: it is that same depth, waiting. Divide, and every number lands inside the cube. Stretch, and it lands on a pixel: nine hundred and sixty across, three hundred and twenty down. Nine sixty is exactly half of nineteen twenty, which is the check: the apex sits directly above the centre of a dome the camera is aimed at, so it must land on the vertical centre line.

On-screen math:

- follow one point -- the very top of the dome -- all the way:
-   world = (0.0000, 0.0000, 5.0000, 1)
-   the 1 on the end marks it a position, not a direction
- multiply by the view matrix (world -> the camera's frame):
-   view  = (+0.0000, +2.5122, -13.8815)
-   its z of -13.8815 is depth in front of the lens; compare
-   the straight-line distance |eye - point| = 14.1070
- multiply by the projection matrix (camera -> clip space):
-   clip  = (+0.0000, +5.6426, +13.7399, w=+13.8815)
-   and there is the depth again, sitting in w = 13.8815
- now the divide. This is the moment perspective happens:
-   ndc = clip / w = (+0.000000, +0.406485, +0.989800)
-   everything still visible now lies inside a -1..+1 cube
- stretch that cube across the frame:
-   px = (ndc_x * 0.5 + 0.5) x 1920 = 960.0
-   py = (1 - (ndc_y * 0.5 + 0.5)) x 1080 = 320.5
-   y is flipped because screens count their rows downward
- World (0.0, 0.0, 5.0) lands on pixel (960, 320): three matrices, one divide, one stretch.

## 38. What hides what

Time: 00:31:19.528 - 00:32:09.984

No sorting. Every pixel just remembers how far away it is.

Two things want the same pixel. Which one wins? The obvious answer is to sort everything back to front and paint in order. Real graphics cards do not do that, because sorting thousands of triangles every frame is expensive, and because two triangles can overlap in ways that have no correct order at all. Instead every pixel keeps a second number beside its colour: the depth of whatever is currently drawn there. When a new fragment arrives, one comparison decides it. Nearer, keep it. Further, throw it away. No sorting, no ordering, and it works no matter what order the triangles arrive in. The three panels here are drawn in the worst possible order, back to front reversed, and the picture still comes out right.

On-screen math:

- keep the fragment with the smaller depth

## 39. Why depth precision runs out

Time: 00:32:09.984 - 00:33:06.416

The divide that made perspective also warps the depth scale.

There is a catch, and it explains a bug every 3D artist has seen. Depth gets stored between zero and one, but not evenly. The same divide by w that produced perspective also squashes the depth scale, so distances close to the camera get an enormous share of the available precision and far ones get almost none. Look at the table. Between the near limit and twice the near limit the depth value uses half of its entire range. By fifteen units out it is changing in the fifth decimal place. When two far-off surfaces round to the same stored depth, the card cannot tell which is in front, and they flicker against each other as the camera moves. That is z-fighting. The cure is almost always to push the near limit further out, because that is the setting that governs how the precision is shared.

On-screen math:

- the far side of the dome must not paint over the near side.
- Nothing is sorted. Every pixel simply remembers its depth:
-   if the arriving fragment is nearer, keep it; else drop it
-   depth is stored 0 to 1, from near=0.08 to far=120.0
- the remap is not even, because it comes out of that same
-   divide by w:
-     0.08 units away  ->  depth 0.000000
-     0.16 units away  ->  depth 0.500334
-     1.00 units away  ->  depth 0.920614
-     5.00 units away  ->  depth 0.984656
-    15.00 units away  ->  depth 0.995330
-   120.00 units away  ->  depth 1.000000
-   the first 0.08 to 0.16 units alone spend 50.0% of the range
-   so precision is lavish up close and thin far away
-   two far-off surfaces whose depths round to the same number
-   flicker against each other: that is z-fighting, and pushing
-   'near' further out is the usual cure
- A depth buffer replaces sorting with one comparison per pixel -- and spends most of its precision between 0.08 and 0.16 units of the lens.

## 40. Throwing away half of everything

Time: 00:33:06.416 - 00:33:52.600

On a closed surface, half the triangles face away from you.

Here is a free saving. On any closed shape, roughly half the surface is pointing away from you at any moment. You cannot see it, because the near half is in the way. So before doing any work on a triangle, the card checks its winding on screen. If the corners come out clockwise after projection, the triangle is facing away and it is dropped immediately: no depth test, no lighting, no pixels. The red ghosts fading out here are the ones being dropped. This is why the corner order mattered several chapters ago, and it is also why a model with one triangle wound backwards shows a hole from one side and a floating panel from the other.

On-screen math:

- clockwise after projection = facing away
- dropped before any shading happens

## 41. How bright is this surface?

Time: 00:33:52.600 - 00:34:38.880

Three directions, three dot products, one number.

Everything so far decided where things are. Now, how bright. The whole of the shading in this film comes from three directions and the angles between them. Where the surface faces, which is the normal we computed with a cross product. Where the light is. And where the eye is. The dot product of two directions of length one gives the cosine of the angle between them: one when they point the same way, zero at right angles, negative when they face apart. So a single dot product of the normal with the light direction answers the question a painter answers by eye: is this surface turned toward the light or away from it? That is Lambert's law, and it is nearly the whole of what you read as shape.

On-screen math:

- diffuse = max(n . l, 0)
- h = (l + v) / |l + v|

## 42. The lighting equation this film runs

Time: 00:34:38.880 - 00:35:40.880

Real vectors, real constants, one brightness out.

These are the actual vectors for one actual panel of the dome standing beside the panel, and the actual constants from the shader program that this film's frames are drawn with. Diffuse is the normal dotted with the light direction, clamped so that a surface facing away goes dark rather than negative. The highlight uses a trick worth knowing. Rather than work out where a mirror reflection would go, we take the direction exactly halfway between the light and the eye. If the surface faces that halfway direction, you are in the reflection. Raising that to the power of forty-two makes the falloff sharp, which is what makes it read as gloss rather than haze. The rim term brightens edges where the surface curves away from you, which is what separates the silhouette from the background. Add those three with the weights shown and you have the colour of one pixel. No shadows, no bounced light, no ray tracing anywhere in this film.

On-screen math:

- shading asks one question per pixel: how much of this light
- does this surface throw toward this eye? Three directions:
-   n = the surface normal   (+0.6284, +0.4089, +0.6617)
-   l = toward the light     (+0.4448, +0.5437, +0.7117)
-   v = toward the eye       (+0.7254, +0.5070, +0.4656)
- the dot product of two unit directions is the cosine of the
-   angle between them: 1 facing, 0 side-on, negative behind
-   diffuse = max(n . l, 0) = 0.972818
-   that one number is Lambert's law -- square to the light is
-   brightest, edge-on is dark, and nothing lights from behind
- highlights use the direction halfway between light and eye:
-   h = (l + v) / |l + v|
-   specular = max(n . h, 0) ^ 42 = 0.644452
-   the exponent 42 is gloss: higher means a tighter, harder highlight
-   rim = (1 - max(n . v, 0)) ^ 2.5 = 0.000140
-   rim brightens the silhouette, where the surface curves away
- add them in the weights this film's shader really uses:
-   lit = colour x (0.3 + 0.74 x diffuse)
-         + cool tint x rim x 0.18
-         + warm tint x specular x 0.22
-   a face of base brightness 0.15 comes out at 0.2948
- Everything you read as shape in this picture is three dot products and a power. No shadows, no bounced light, no ray tracing.

## 43. Glass, and why order comes back

Time: 00:35:40.880 - 00:36:29.344

Transparency is the one place where drawing order matters again.

The depth test let us ignore drawing order. Transparency takes that back, because a see-through surface has to be mixed with whatever is behind it, which means whatever is behind it has to be there already. So the renderer works in two passes. Everything solid first, with the depth test doing its job. Then everything transparent, with depth writing switched off, so that a panel drawn early does not stop the panels behind it from being drawn at all. The mixing itself is one line: the new colour times its opacity, plus the old colour times one minus that opacity. Opacity is the fourth number in every vertex colour, the one we have been carrying since the buffer chapter without using.

On-screen math:

- out = new x a + old x (1 - a)
- opaque pass first, transparent pass second

## 44. And then it does it again

Time: 00:36:29.344 - 00:37:15.480

Everything you have watched happens thirty times a second.

One more thing, and it is the one that makes all the rest matter. Everything in this film — building the tubes, uploading the numbers, placing the camera, three matrix multiplications per corner, a divide per corner, a depth comparison per pixel and a lighting sum per pixel — happens once for the picture you are looking at. And then it all happens again for the next one, thirty times a second. That budget, thirty-three milliseconds, is the reason for nearly every decision in this film. It is why lighting is dot products rather than ray tracing. It is why half the triangles are thrown away before shading. It is why depth is one comparison instead of a sort.

On-screen math:

- 30 frames/s = 33.33 ms each

## 45. The cost of one frame

Time: 00:37:15.480 - 00:38:15.992

The whole calculation, counted and divided by the clock.

The budget, in numbers. Thirty-three point three three milliseconds per frame. Three thousand nine hundred triangles in the frame you are watching, which works out at about eight microseconds each if they were done one after another — and they are not, they are done thousands at a time. The bottom half is the part people underestimate. A full frame at this resolution is over two million pixels, and the lighting sum runs for every one of them that gets covered. Sixty-two million lighting calculations a second, at worst, for one dome on a dark background. And one last property worth stating. Every scene in this film is a pure function of which chapter it is and how far through that chapter we are. Nothing accumulates, nothing depends on what happened before. Which is why this same film renders identically on any machine, every time, and why the numbers you have watched being computed can be checked by anybody who runs it.

On-screen math:

- and then it all happens again for the next picture:
-   30 frames a second = 33.33 ms per frame
-   clear the screen, rebuild the batch, upload it, draw it,
-   draw the text panel over the top, swap the buffers
-   3,900 triangles inside that budget = 8.547 microseconds each
- the vertex shader runs once per vertex, thousands at a time:
-   11,700 vertex runs per frame
- the fragment shader runs once per pixel covered:
-   a full frame is 1920 x 1080 = 2,073,600 pixels
-   = up to 62.2 million shader runs a second
-   which is exactly why the lighting had to be dot products
- and because every scene is a pure function of (chapter,
-   progress), the same second of film renders identically on
-   any machine, every time
- A frame is 3,900 triangles built, uploaded, projected, depth-tested and shaded in 33.3 milliseconds -- thirty times a second.

## 46. The whole chain, once more

Time: 00:38:15.992 - 00:39:26.392

One number in; a lit, shaded, sorted picture out.

That is the entire calculation, from nothing. Phi placed twelve points. A division put them on a unit sphere. Halving every edge made thirty more points in the wrong place, and a second division put them right, which split the edges into two lengths: zero point five four six and zero point six one eight of the radius. Half the sphere, counted, is forty panels and sixty-five struts. One multiplication turned that into a cut list. Then: each strut became a tube of twenty-eight triangles. Each triangle got a normal from a cross product. All of it flattened into one list of numbers. Two angles placed a camera, three matrices moved the world in front of it, one divide made distance work, one stretch found the pixel, one comparison decided what hides what, and three dot products decided how bright it was. No step in that chain is beyond someone who can use a calculator. The cleverness is not in any one formula. It is in the fact that they compose — and that every single number can be checked.

On-screen math:

- phi -> icosahedron -> subdivide -> project -> 2 lengths
- mesh -> view -> projection -> divide -> pixel -> light
