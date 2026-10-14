# The Shop the Campaign Buys: A 10 x 5 Plasma Table and Its Router - Voiceover Script

The timestamps match the deterministic ModernGL video export.
Read conversationally; the on-screen equations carry the dense numbers.

## 01. The shop the campaign buys

Time: 00:00:00.000 - 00:00:35.100

Two machine lines, one frame.

Part of what backing this project pays for is a shop. Not a building: two machines. A plasma table that cuts a whole sheet of steel into the panels of a dome, and a router that cuts the jigs and the wooden panels. This film is what those two machines are, what they make, and what they cost when you build them rather than buy them. Here is the first thing the table makes: one 120 by 60 inch sheet of plate, 40 panels.

On-screen math:

- one sheet: 120 by 60 in
- 40 panels

## 02. One sheet, forty panels

Time: 00:00:35.100 - 00:01:05.996

The torch follows the nest.

Steel plate comes in sheets ten feet by five, and the table's bed is exactly that size. The torch walks every panel's outline in turn: about 181 feet of cut, roughly 24 minutes of torch time. What comes off the table is the whole shell of a dome, every triangle already the right size, already the right angle at every corner. Nothing is measured with a tape. The machine does the measuring.

On-screen math:

- cut path = 181 ft
- about 24 min

## 03. How the panels fit

Time: 00:01:05.996 - 00:01:39.096

Strips of triangles, up and down.

The panels are laid out in 8 strips, each one triangles pointing alternately up and down, the way they tile with nothing between them but the cutting gap. Every panel is slid along until it sits exactly a quarter inch from its neighbour, and then the whole layout is checked part by part. 78 percent of the sheet ends up inside a part. The panels come from the solved dome, so if the geometry changes, the nest changes too.

On-screen math:

- 8 strips
- 78% of the sheet in parts

## 04. Almost fits

Time: 00:01:39.096 - 00:02:06.996

A little off each point.

You can squeeze a slightly bigger shell out of the same sheet by trimming each panel's point and welding a small cap over every vertex. Here the best trim is 0.30 inches off each point, with 16 caps, and it makes the shell 1.4 percent bigger. That is real, and it is small: the strips are already full. Most of the time, cut the panels whole.

On-screen math:

- trim = 0.30 in
- gain = 1.4%
- caps = 16

## 05. Welded up

Time: 00:02:06.996 - 00:02:36.284

Forty panels, one shell.

Welded together, the forty panels make a steel shell 5.2 feet across and 2.6 feet tall. That is 55 seams and 82 feet of weld, about 2.1 hours at a steady hand. In three-millimetre plate the panels weigh 188 pounds; in two-millimetre, 126. Every seam is a butt weld, ground flush where it shows.

On-screen math:

- 55 seams = 82 ft of weld
- 188 lb in 3 mm

## 06. What one sheet becomes

Time: 00:02:36.284 - 00:03:06.984

A tub, a stove, a fire bowl, a seat.

Turned over on three short legs, the shell is a bowl holding 237 gallons: a tub. In heavier plate, with a hinged panel for a door and a flue at the top, it is the body of a wood stove. Smaller jobs are a fire bowl, a planter, a seat. A hemisphere does not care which way up it is used, and these are the right first projects while you learn the machine.

On-screen math:

- as a bowl: 237 gal

## 07. What it is not

Time: 00:03:06.984 - 00:03:29.284

One sheet does not make a shelter.

Here is the number that does not help the pitch. At 2.6 feet tall, a one-sheet shell holds nobody standing up. It is not a storm shelter, and it is not a room. To shelter a person you need a bigger dome, cut from several sheets, and that is the next step.

On-screen math:

- height = 2.6 ft

## 08. A dome in plate

Time: 00:03:29.284 - 00:04:05.584

Size the dome to the sheet.

The same table cuts the triangles of a building. A three-frequency dome has two panel shapes, and how many sheets it takes depends on whether two strips of its biggest panels fit on a five-foot sheet. At 13 feet across they do: 9 sheets, 69 percent of the steel in parts, about 1,005 pounds in two-millimetre plate. One foot bigger, at 14 feet, they do not, and it takes 16 sheets. Size the dome to the sheet, or cut the big panels in two and weld them.

On-screen math:

- 13 ft: 9 sheets
- 14 ft: 16 sheets

## 09. The table, by the plans' own rules

Time: 00:04:05.584 - 00:04:46.284

Credit: Homemade Madness.

The table is the Homemade Madness DIY CNC plasma design, and the credit for it is theirs. Their plans are drawn for a two-by-one-metre sheet and give two rules for building it bigger: the frame is two hundred and fifty millimetres longer and wider than the sheet, and the gantry tube is two hundred and fifty-three longer than the cut width. For a ten-by-five-foot sheet that makes a frame 3,298 by 1,774 millimetres. Ours is half again as long as theirs, so we add one change: a leg pair at the middle, so no rail span goes unsupported.

On-screen math:

- frame = sheet + 250 mm = 3,298 by 1,774 mm
- gantry tube = 1,777 mm

## 10. Long rails, joined

Time: 00:04:46.284 - 00:05:21.384

Alignment is everything.

No single rail is three metres long at this price, so each side takes three, joined end to end: 10 rails in all, which is 5 of the two-rail kits already bought. Both long sides are driven, so both need rack: 7 half-metre lengths a side, four on the gantry and a spare, 19 in all. Every joint is cut on the tooth and aligned with a spare piece held across it. A joint set by eye makes a machine that cuts a curve.

On-screen math:

- rails = 10 (5 kits)
- rack = 2 x 7 + 4 + 1 = 19

## 11. The number that has to be right

Time: 00:05:21.384 - 00:05:52.472

Steps per millimetre.

A fifteen-tooth pinion at module one and a half has a 22.5 millimetre pitch diameter, so one turn of the motor moves the axis 70.69 millimetres. With eight microsteps on a two-hundred-step motor, that is 22.64 steps per millimetre. That number goes into the controller before anything is cut. The plans prefer a thirteen-tooth pinion for torque, and say to use what you can find and set the ratio in software.

On-screen math:

- pitch dia = 15 x 1.5 = 22.5 mm
- per turn = pi x 22.5 = 70.69 mm
- 1600 / 70.69 = 22.64 steps/mm

## 12. Motors that fit the pinion

Time: 00:05:52.472 - 00:06:23.172

The bore decides the shaft.

The pinions have a ten-millimetre bore, so the motors must have a ten-millimetre shaft. A NEMA 23 of three newton-metres has one, and fits with no sleeve; a bigger NEMA 34's shaft would not. Two of them on the long axis push a gantry of about 40 kilograms at 6.7 metres per second squared on half their torque, far more than a plasma ever asks for, because a plasma torch pushes on nothing.

On-screen math:

- shaft 10 mm = pinion bore 10 mm
- two motors: 6.7 m/s^2 at half torque

## 13. Pilot arc and a floating head

Time: 00:06:23.172 - 00:06:52.484

Keep the noise out of the wiring.

The torch rides a floating head that touches the plate to find its height before every cut. Pick a plasma with a pilot-arc start: a high-frequency start puts electrical noise into the control wiring. A torch height controller is left out on purpose. The plans' breakout board cannot run one, and touching off the plate again partway through a long cut does the job for nothing.

On-screen math:

- pilot arc, CNC port
- floating head touch-off

## 14. What it costs, and what kind of number each is

Time: 00:06:52.484 - 00:07:30.508

Paid, quoted, estimated.

Built, the plasma table comes to $4,151, and the bill keeps three kinds of price apart. $1,157 is what we actually paid for rack, pinions and rails. $1,654 is current retail listings for the motors, drivers, power supply, Mach3, the plasma cutter and the frame steel. $1,339 is still estimates, labelled as estimates until they are quoted: the slats, the water pan, the plate, the ballscrew and the wiring.

On-screen math:

- paid $1,157
- quoted $1,654
- estimated $1,339
- = $4,151

## 15. The router head

Time: 00:07:30.508 - 00:08:04.308

Same frame, different tool.

For $990 more, the same frame becomes a router. The rails, rack, motors and controls stay. The floating head becomes a rigid ballscrew axis with a water-cooled spindle, the slats lift out, and a flat spoilboard goes in. The gantry tube sags 0.03 millimetres under a router's side load, less than the cutter's own wobble. This is the machine that cuts the jigs, the templates and the wooden panels the rest of the method needs.

On-screen math:

- router head = $990
- gantry sag = 0.03 mm

## 16. Budgeted, and built

Time: 00:08:04.308 - 00:08:41.252

The honest version of the line item.

The campaign budgets $11,800 to buy a plasma table and $14,500 for a router: $26,300 together. Built on one frame, both machines come to $5,141. That difference is real, and so is what it does not include: a bought machine comes with support, a warranty and a phone number. A built one takes weeks of evenings, and its first troubleshooter is its owner. We print both numbers because the choice is real.

On-screen math:

- bought: $26,300
- built: $5,141

## 17. What the backing builds

Time: 00:08:41.252 - 00:09:10.752

A shop that makes shops.

That is what this part of the backing buys: a table that turns a sheet of steel into a dome's panels, a router that turns a sheet of plywood into the jigs that build the wooden ones, and the first things they make. Every number in this film comes from the same code as the book. The table's design is Homemade Madness's; the steel and the sawdust will be ours.

On-screen math:

- plasma + router, one frame
- figures: cnc_table.py, plate_nesting.py

## 18. Do the one thing

Time: 00:09:10.752 - 00:09:30.032

Send this to one person who can carry it further than I can.

If any of this was worth your time, send it to one person who can carry it further than I can. That is the whole ask. One share from somebody with reach does more for this than a month of me in a field with a chainsaw.

On-screen math:


## 19. Follow the experiments

Time: 00:09:30.032 - 00:09:52.096

Follow the experiments.

Everything is documented, including the parts that failed. Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok, short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot com and a Kickstarter for Frankendome are both coming soon.

On-screen math:

