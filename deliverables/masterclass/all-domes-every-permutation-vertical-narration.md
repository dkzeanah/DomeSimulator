# All Domes - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. All domes

Time: 00:00:00.000 - 00:00:34.568

*on screen: Every building the Dome Creator makes, drawn by the Dome Creator.*

The Dome Creator is a walkable customizer with twelve finished designs in it, and this is all of them -- but not the way a film has shown them before. Until now the films rebuilt a preset's geometry and then re-drew it with their own tubes and triangles, which is a sketch of the building. These are the tool's own meshes, running through the tool's own shader. The wood has grain, the glass has a highlight, the mirror tiles are reflecting a tree line, and each of these is assembling itself in the order its construction record says to build it.

On-screen math:


## 02. The catalogue, counted

Time: 00:00:34.568 - 00:01:00.568

*on screen: Twelve buildings, fit-out included, none of it typed in.*

Start with all twelve on one screen, because the spread is the point. The same engine makes a six hundred square foot treehouse dome and a three thousand square foot lodge, and the only things that changed are a frequency, a radius and a material list. The equipment count on the right is the part the old catalogue film could not show at all.

On-screen math:

- 12 designs, each rebuilt and measured whole:
- Timber Workshop           3V 165 struts 105 panels 12 items   819 sqft  $ 19,514
- Glass Studio Loft         4V 250 struts 160 panels 11 items   845 sqft  $ 24,670
- Split-Log Homestead       2V 120 struts  40 panels 12 items  1217 sqft  $ 18,067
- Whole Trunk Lodge - 20 ft 2V  65 struts  40 panels  9 items  3281 sqft  $ 22,747
- Grow Dome                 3V 165 struts 105 panels 11 items   819 sqft  $ 11,489
- Hex Cell Pavilion         3V 165 struts 105 panels  5 items  1179 sqft  $ 61,355
- Continuous Steel Arc Hang 2V  65 struts  40 panels  6 items  2164 sqft  $100,454
- Rebar Garden Dome         3V 165 struts 105 panels  5 items   991 sqft  $  7,002
- Concrete Monocoque Form   3V 165 struts 105 panels  6 items  1179 sqft  $ 58,661
- Woodland Hex Mirror       3V 165 struts 105 panels  4 items   991 sqft  $ 67,346
- Woodland Square Mirror    4V 250 struts 160 panels  4 items  1023 sqft  $ 50,968
- Treehouse Canopy Dome     2V  65 struts  40 panels  5 items   597 sqft  $ 27,243
- 90 pieces of equipment stand on those 12 floors, and the workshop alone is 97 hours of work -- the fit-out is part of the building here, not a picture of one

## 03. What is declared, and what is measured

Time: 00:01:00.568 - 00:01:29.952

*on screen: Prices are declared inputs. Everything else is read off the model.*

Before any dollar figure, here is where the dollars come from. The densities and unit prices live in one file in this project, they are declared inputs, and they are the only numbers in this film that were typed by a person. Every quantity they get multiplied by -- areas, lengths, counts, weights -- is measured off the model that drew the building you are looking at. Change a price in that file and the next render says the new number without anybody editing a script.

On-screen math:

- nothing below is measured -- these are declared inputs:
- frame materials: 8 entries, density kg/m3 and price per kg
-    timber (SPF)  480 kg/m3  $2.00/kg
- panels: 16 types, $1.50 to $210.00 per m2
-    cheapest Plastic Sheeting, dearest Hex Mirror
- cladding layers: 9, foundations: 7 ($85/m2 for a slab)
- partition walls $45/m2, wire $1.40/m, PEX $2.10/m
- labour hours come from the mesh builder's construction record,
- which is an estimate per work step, not a stopwatch
- every dollar in this film is one of those numbers multiplied by a quantity the model measured -- change a price in materials.py and the next render says the new one

## 04. Timber Workshop

Time: 00:01:29.952 - 00:01:56.648

*on screen: The one the tool opens on, and the one every sweep starts from.*

Dimensional lumber on metal brackets, plywood between the struts, a concrete slab under all of it, and a working shop on the floor: benches, a machine station, a tool chest, shelving, an office corner. Watch what happens when the roof comes off. That equipment is not set dressing. Every piece has a weight, a price and a power draw in the model, and the wiring on the floor was routed to reach it.

On-screen math:


## 05. Glass Studio Loft

Time: 00:01:56.648 - 00:02:18.232

*on screen: Four frequency, glazed, on a deck: the expensive, beautiful end.*

Raise the frequency and the shell gets rounder and much more complicated: two hundred and fifty struts instead of a hundred and sixty five. Every panel here is glass, which is why you can see the furniture through the wall, and why the shader is putting a highlight on the panels facing the sun. It stands on a wood deck rather than a slab.

On-screen math:


## 06. Split-Log Homestead

Time: 00:02:18.232 - 00:02:42.984

*on screen: Hubless, framed from split logs, cedar shakes over the top.*

This is the design this whole project argues for. Two frequency, hubless doubled framing, quarter wedges split straight from logs. There is not one hub connector in the building. Every triangle brings its own three members and bolts to its neighbours, and the cedar shakes you can see are a cladding layer sitting over the sheathing, not a texture painted on it.

On-screen math:


## 07. Whole Trunk Lodge - 20 ft

Time: 00:02:42.984 - 00:03:05.096

*on screen: Whole trunks, sized so the longest member is just under twenty feet.*

Now use the tree whole. The radius is set so the longest member lands just under twenty feet, which is what two people can actually move. Sixty five round trunks, canvas stretched between them, gravel underneath. It is the largest floor in the catalogue by a wide margin and it is framed from the fewest pieces of anything here.

On-screen math:


## 08. Grow Dome

Time: 00:03:05.096 - 00:03:23.512

*on screen: Aluminium and polycarbonate: the greenhouse configuration.*

The same three frequency skeleton as the workshop, framed in aluminium and glazed in twinwall polycarbonate, with grow racks and water storage inside. The geometry did not change at all. Only the material list did, and the price came down by nearly half.

On-screen math:


## 09. Hex Cell Pavilion

Time: 00:03:23.512 - 00:03:43.776

*on screen: A hexagonal cell frame in structural steel.*

Not everything here is triangulated the same way. The hex cell style groups the geometry into hexagonal tiles on a steel frame, and the panels are composite hexagons with a seam bead around each one. It is heavier and dearer than anything timber, and it looks like nothing else on the site.

On-screen math:


## 10. Continuous Steel Arc Hangar

Time: 00:03:43.776 - 00:04:03.920

*on screen: Curved ribs running over the shell instead of straight struts.*

The hangar swaps short straight struts for twelve continuous steel arcs and three rings, with fabrication and site power equipment inside it. Two frequency, eight metre radius, open between the ribs. This is what the same geometry looks like when a steel shop builds it instead of a carpenter.

On-screen math:


## 11. Rebar Garden Dome

Time: 00:04:03.920 - 00:04:23.776

*on screen: A dense meridian and ring lattice, bent from rebar.*

Rebar is the cheapest structural steel there is, and it bends, so the tool draws it as twenty two meridians and seven rings rather than sticks between hubs. Seven thousand dollars, which is the cheapest building in the catalogue, and it is the one closest to what people actually put up in a back yard on a weekend.

On-screen math:


## 12. Concrete Monocoque Form

Time: 00:04:23.776 - 00:04:45.456

*on screen: The frame as formwork for a poured shell.*

Here the frame is not the building, it is the formwork. Rebar and shuttering panels carry a poured concrete shell, with shoring jacks, scaffold, a mixer and a bender on the floor. The dome is doing the thing concrete is best at, standing in pure compression, and it is by some distance the heaviest thing here.

On-screen math:


## 13. Woodland Hex Mirror

Time: 00:04:45.456 - 00:05:05.144

*on screen: Hexagonal mirror tiles that reflect the site back at you.*

The mirror designs exist because the renderer can do it. Those tiles are reflecting a sky and a tree line the shader computes per pixel, which is why the dome looks different from every angle as the camera moves. Structurally it is the same three frequency shell as the workshop.

On-screen math:


## 14. Woodland Square Mirror

Time: 00:05:05.144 - 00:05:26.872

*on screen: The same trick at four frequency, on square tiles.*

Four frequency on a steel frame, square mirror tiles instead of hexagons. More panels, each smaller, so the reflection breaks up finer. Between the two mirror designs you can see exactly what frequency does to a faceted surface: it stops looking like a machine and starts looking like a curve.

On-screen math:


## 15. Treehouse Canopy Dome

Time: 00:05:26.872 - 00:05:47.184

*on screen: An elevated dome on a supported timber platform.*

The smallest one, and the only one that is not on the ground. A two frequency hex tile dome on a timber platform with a central trunk, six posts, braces and a ladder, all of which the tool builds because the foundation menu has a treehouse platform in it. Six hundred square feet, up in the canopy.

On-screen math:


## 16. One dome, step by step

Time: 00:05:47.184 - 00:06:19.232

*on screen: The tool's own construction order, played end to end.*

The mesh is not assembled in a random order. The builder emits it the way a trailer home is manufactured: site prep, then the slab, then the floor layout, the frame from the base ring upward, the hubs, the doorway, the sheathing bottom to top, the cladding, then rough electrical, rough plumbing, partitions, equipment, and finally the monitoring system. The ring on the floor is where the record says the crew is standing for the step on screen, and the hours are the tool's own estimate for the work done so far.

On-screen math:


## 17. The labour model, phase by phase

Time: 00:06:19.232 - 00:06:48.664

*on screen: Three hundred and forty eight work steps, grouped.*

Those steps add up, and grouping them says something useful about where a dome's time actually goes. The frame, which is the part everybody pictures when they think about building a dome, is not the expensive phase in hours. This is a model, not a stopwatch, and I want to be clear about that: it is an estimate attached to each work step. But it is the same estimate applied to every design, so comparing two of them is fair even where the absolute number is soft.

On-screen math:

- Timber Workshop: 348 work steps, in build order:
- Site               2 steps    14.0 h
- Frame            165 steps    19.8 h
- Joins             61 steps    12.2 h
- Openings           1 steps     2.0 h
- Sheathing        105 steps    42.0 h
- Fit-out           13 steps     5.1 h
- Commissioning      1 steps     2.0 h
- total 97.1 hours of work
- two people, eight hour days: 6.1 days
- 97 hours is the tool's estimate, not a stopwatch -- but it is the same estimate for every design, so the comparisons between them hold even where the absolute number does not

## 18. Frequency

Time: 00:06:48.664 - 00:07:17.376

*on screen: One radius, four subdivisions, all four built.*

Now the menus, one at a time, and this is the first of them. Same radius, same material, same foundation: only the number of times each face is divided changes. One frequency is twenty five struts in one length. Four frequency is two hundred and fifty in six lengths. Frequency buys you a smoother shell and charges you in part variety, which is the thing that actually slows a build down.

On-screen math:


## 19. The four dials, and why they are countable

Time: 00:07:17.376 - 00:07:44.024

*on screen: Radius, strut width, recess and pad size move in fixed steps.*

The tool also has sliders, and sliders look like they have infinite settings. They do not: each one moves in a fixed step, and those steps are written in the menu code, so they can be counted exactly like the drop-downs can. And not one of them changes the part count. Doubling the radius gives you four times the floor off the same list of operations, which is the whole economic argument for this shape.

On-screen math:

- the sliders are not continuous -- the tool moves them in steps:
- Radius                 2 to 15  step 0.5     27 settings   m
- Strut width       0.02 to 0.35  step 0.005   67 settings   m
- Recess depth      0.05 to 0.95  step 0.05    19 settings   fraction of strut depth
- Foundation size       1 to 1.6  step 0.05    13 settings   x radius
- 446,823 settings from four dials, and not one of them changes the part count: frequency alone decides how many pieces there are

## 20. Six ways to join the same sticks

Time: 00:07:44.024 - 00:08:13.888

*on screen: Hub and strut, hubless, hex cell, arcs, lattice, formwork.*

The frame style menu changes how the members meet, and it changes the building far more than the material does. Hub and strut is the classic. Hubless doubled gives every triangle its own three members. Hex cell groups them into hexagons. The arc and lattice styles throw out straight struts entirely and run continuous ribs over the shell. Formwork treats the frame as shuttering for something poured.

On-screen math:


## 21. The six, counted -- including where the tool argues with itself

Time: 00:08:13.888 - 00:08:43.200

*on screen: And one disagreement inside the tool, said out loud.*

Here they are as numbers, off the same shell. The interesting one is at the bottom, and it is not flattering. Two of these styles report hub connectors in the bill of materials that their own assembly never fits. The picture and the price disagree. The picture is the one to believe, because it is the assembly, so treat those two totals as high by their hub line. I would rather this film state that than quietly average it away.

On-screen math:

- one timber workshop shell, framed six ways:
- Hub & Strut            165 struts   61 hubs fitted    0 bolts  $ 15,519
- Hubless Doubled        315 struts    0 hubs fitted  330 bolts  $ 17,837
- Hex Cell               165 struts   61 hubs fitted    0 bolts  $ 15,519
- Continuous Steel Arcs  165 struts    0 hubs fitted    0 bolts  $ 15,519
- Rebar Lattice          165 struts    0 hubs fitted    0 bolts  $ 15,519
- Concrete Formwork      165 struts   61 hubs fitted    0 bolts  $ 15,519
- and one disagreement inside the tool, said out loud:
- Continuous Steel Arcs  bills $596 for 61 hub connectors its own assembly never fits
- Rebar Lattice          bills $596 for 61 hub connectors its own assembly never fits
- the picture follows the assembly, so those two totals are high by their hub line -- every other figure in this film comes off the same model that drew the building beside it

## 22. Eight cross sections

Time: 00:08:43.200 - 00:09:17.456

*on screen: Round tube to quarter wedge, all at the same width.*

The strut shape menu decides what every member is cut from. Round tube, solid rod, rebar, whole trunk, square tube, dimensional lumber, hex strut, and the quarter wedge this project is built around. All eight are drawn at the same nominal width, so what you are seeing is the profile the tool sweeps along each member, and the amount of material each one actually contains. The ninth is the same quarter wedge with its bark turned outward, because that is a menu of its own and it only means anything here.

On-screen math:


## 23. Eight materials

Time: 00:09:17.456 - 00:09:35.512

*on screen: The same frame, priced and weighed eight ways.*

The material menu carries a density and a price per kilogram, so changing it changes what the frame weighs and what it costs without touching a single dimension. Structural steel and timber frame the identical building. One of them is fifteen times the weight of the other.

On-screen math:


## 24. Sixteen finishes

Time: 00:09:35.512 - 00:09:54.576

*on screen: Eight frame colours in front, eight panel tints behind.*

Two menus that change everything about how a building looks and nothing at all about what it costs: the frame colour and the panel tint. Front row is the frame, back row is the skin. It is worth knowing which of these decisions are free, because they are the ones you can change your mind about on the day.

On-screen math:


## 25. Sixteen panel types

Time: 00:09:54.576 - 00:10:25.232

*on screen: Everything the tool can put between the struts.*

This is the menu that decides both what a dome looks like and what it costs. Open, plywood, glass, acrylic, twinwall, sheeting, insulated panel, shingle, metal, solar, canvas, hex composite, hex mirror, square mirror, concrete form, precast. Every one of these is the same shell underneath. Watch the mirrors on the bottom row and the solar cells above them: those are patterns the shader computes, not pictures pasted on.

On-screen math:


## 26. Which menu is the expensive one

Time: 00:10:25.232 - 00:10:53.296

*on screen: One design, one menu at a time, every setting priced.*

So which of these choices actually costs money? Hold everything else at the workshop and price every setting of each menu in turn. The answer is that the covering and the frame material swing the price by tens of thousands, the geometry barely moves it, and three of the menus are free. That is good news, because the covering is the decision you can defer, stage, or upgrade later. The frame is the one you have to get right on day one.

On-screen math:

- start from Timber Workshop at $19,514,
- change one menu at a time, price every setting:
- Frame material   $ 18,563 (Whole Tree Tru) -> $  93,185 (Structural Ste)
- Panel type       $ 16,290 (Open) -> $  53,899 (Hex Mirror)
- Foundation       $ 10,685 (Bare Ground) -> $  30,420 (Treehouse Plat)
- Cladding layer   $ 19,514 (None) -> $  36,527 (Poured Concret)
- Strut shape      $ 17,013 (Round Tube) -> $  19,514 (Dimensional Lu)
- Frequency        $ 17,312 (1V) -> $  19,755 (4V)
- and 3 menus cost nothing at all: frame colour, panel colour, wedge curve
- frame material swings the price by $74,622 on the same geometry -- the shape is not what you are paying for

## 27. Nine cladding layers

Time: 00:10:53.296 - 00:11:18.888

*on screen: What goes over the sheathing, in three stackable slots.*

Over the panels the tool will stack up to three cladding layers: plastic film, house wrap, foam, asphalt shingles, cedar shakes, an EPDM membrane, a green roof, or a poured concrete shell. Each one has a thickness, so they sit visibly outside the shell, and each covers only the panels that are neither open nor windows -- which is the model being careful for you.

On-screen math:


## 28. Seven foundations

Time: 00:11:18.888 - 00:11:44.840

*on screen: Bare ground to a treehouse platform.*

Underneath, seven choices, and the tool builds each one properly: grass, gravel, a slab, a wood deck, stone pavers, bare ground, and a treehouse platform that comes with a trunk, six posts, braces and a ladder. The pad is sized from the dome's own radius, and it is priced by the square metre, which is why the platform is the dearest thing in this row by a long way.

On-screen math:


## 29. Four ways to divide a floor

Time: 00:11:44.840 - 00:12:04.696

*on screen: Nothing, markings, low walls, full walls.*

Inside, the floor is split into ten sections -- a centre hub and nine wedges -- and each one can be assigned a room type from a list of sixteen. The partition menu decides whether those sections are just painted on the slab or actually framed. Roofs off for this one, because there is no other way to see it.

On-screen math:


## 30. The part nobody films

Time: 00:12:04.696 - 00:12:42.000

*on screen: Equipment, framed walls, plumbing -- and the circuits nobody has.*

Here is the whole reason to draw the tool's real mesh rather than a shell. The homestead has twelve pieces of equipment on the floor, each with a price, a weight and a power draw. It has seven partition walls framed to a real height. It has hot, cold and drain lines run from a utility stub to every fixture in it. What it does not have is a single circuit, and neither does any other design in the catalogue. Conduit runs have to start at a battery bank or a charge controller, and not one preset ships with either. Put a battery bank on the floor and the wiring appears on its own.

On-screen math:


## 31. What the fit-out costs

Time: 00:12:42.000 - 00:13:12.176

*on screen: The dome is the cheap part of the dome.*

Add the equipment, the walls and the plumbing up, and they are a serious fraction of what this building costs -- on a design whose shell is split logs and plywood. The electrical line is the one to read carefully. Zero is what the catalogue reports, and that is a fact about the presets rather than about domes: add the power source and the model routes twenty two metres of conduit without being asked twice. The shape saves you on envelope. It does not save you on anything that plugs in.

On-screen math:

- 12 of 12 designs ship furnished, 4 with framed walls
- Split-Log Homestead, as the tool ships it:
-    12 pieces of equipment, $2,595, 388 kg, 1,050 W connected
-    7 framed partition walls, 22 m2, $1,000
-    4 plumbed fixtures, 84 m of PEX and 42 m of drain, $549
-    0 circuits -- and that is not an oversight:
-    conduit runs start at a battery bank or a charge controller,
-    and no design in this catalogue ships with either
- add a battery bank, a controller and two outlets:
-    3 conduit runs, 22 m of wire, $30
- fit-out and services: $4,144 of $18,067, or 23% of the building
- the dome is the cheap part of the dome -- which is exactly why a film about domes should show the plumbing

## 32. Eight the dice picked

Time: 00:13:12.176 - 00:13:36.736

*on screen: Random settings, built and priced, seed on screen.*

Every dome so far was chosen. These eight were not: the film drew them at random from the menus, built whatever came out, and priced it. The seed is on screen, so anyone can run the same draw and get the same eight buildings. Some of them are sensible. At least one of them is a thing nobody would ever build, which is the honest shape of a combination space this large.

On-screen math:


## 33. How many domes that is

Time: 00:13:36.736 - 00:14:06.936

*on screen: Sixteen billion shells, and the film that would take.*

So how many buildings can this tool actually make? Multiply the menus. Then take the honest deduction, because some settings do nothing in some combinations, and count only the shells that genuinely differ. The number is still sixteen and a half billion. At three seconds each, showing every one of them would take fifteen centuries of film, so this one does the only sane thing instead: every setting of every menu, at least once, which is what you have just watched.

On-screen math:

- the shell menus, multiplied:
- Frequency              4
- Frame style            6
- Hub style              2
- Strut shape            8
- Frame material         8
- Frame colour           8
- Panel type             16
- Panel colour           8
- Cladding layer x3      9 ^ 3 = 729
- Foundation             7
- Wedge curve            2
- product = 32,105,299,968 shells
- but some settings do nothing in some combinations:
- hub style changes nothing on hubless doubled, which has no hub to change
- the wedge curve bends 1 of 8 strut shapes (quarter wedge)
- count only the ones that differ: 16,554,295,296 shells
- then the floor: 4,398,046,511,104 partition and room layouts
- and the dials, at the steps the tool moves them in: 446,823 settings
- 16,554,295,296 distinct shells, at three seconds each, is 1,574 years of film -- so this one shows every setting instead, at least once

## 34. Open the tool and check any of it

Time: 00:14:06.936 - 00:14:35.600

*on screen: Load the preset. Read the bill of materials.*

That is the catalogue, every menu in the customizer, and the count of what they add up to. Nothing here was asserted: every figure was read off a model this film rebuilt while it was rendering, and every building was drawn by the tool's own renderer rather than an impression of it. So do not take my word for any of it. Open the Dome Creator, press the preset button until you reach the one you want, and read the bill of materials. It will say what this film said.

On-screen math:


## 35. Do the one thing

Time: 00:14:35.600 - 00:14:50.776

*on screen: Send this to one person who can carry it further than I can.*

If any of this was worth your time, send it to one person who can carry it further than I can. That is the whole ask. One share from somebody with reach does more for this than a month of me in a field with a chainsaw.

On-screen math:


## 36. Follow the experiments

Time: 00:14:50.776 - 00:15:10.176

*on screen: Follow the experiments.*

Everything is documented, including the parts that failed. Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok, short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot com and a Kickstarter for Frankendome are both coming soon.

On-screen math:

