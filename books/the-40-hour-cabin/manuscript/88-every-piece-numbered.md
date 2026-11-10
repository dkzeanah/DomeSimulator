---
chapter: 88
title: Every Piece, Numbered
strand: howto
status: draft
target: 4400
updated: 2026-10-12
---

# 88. Every Piece, Numbered

Two things in this building are made of a great many small pieces of wood,
and both are where a builder loses days. One is the inside of a triangle,
when it is filled with wood instead of covered with a sheet. The other is the
floor the whole dome stands on. Neither is hard, piece by piece. What makes
them slow is that no two pieces are alike: each one has its own length along
each edge, its own two end cuts, its own place, and a builder who works them
out at the saw works them out forty times, and gets some of them wrong.

This chapter is about the calculator that works them out first. It is in the
launcher, called **Triangle Infill**, and it opens in a window of its own: a
triangle, or the floor, in three dimensions, every piece in it numbered.
Click a piece and it gives you that piece: which stick it comes out of, every
length to mark, and every cut, set up on the saw the way you will make it --
which face goes down on the table, what goes against the fence, the mitre and
which way it swings, the bevel and which way it tilts -- and then it plays
the cut, the blade coming down and the offcut falling away, so you can see
what is about to happen before it happens to a real stick.

![Seventeen wedges in one triangle, every one numbered.](plate-ep-numbered.png)

Everything in it is solved from two numbers you already have, the dome's
longest stick and the log it is split from, except what cannot be solved.
That is written down, every line with its reason, in two tables:
{{ep.infill_declared}} figures for the triangles -- saw kerfs, the sizes
sheets and boards are sold in, densities, prices -- and {{ep.base_declared}}
for the floor.

    {{ep.base_table}}

The floor's table is the one that matters most. It holds the load a floor
must carry, {{ep.live}} pounds a square foot for living on and {{ep.dead}}
for the floor itself, which are standards; and it holds how strong the wood
is taken to be, {{ep.fb}} pounds per square inch in bending, which is a
guess. Change any line, and every number after it in this chapter, and in
the calculator, changes with it.

## A triangle is a tray

A dome whose longest stick is {{ep.strut}} inches is {{ep.dome_ft}} feet
across, and its forty triangles come in two shapes: {{ep.lss}} with a long
base of {{ep.long_in}} inches and two short sides of {{ep.short_in}}, and
{{ep.lll}} with three long sides. Fill one of each well and you have filled
the dome.

The opening is not a flat hole. Each frame member is a wedge, an eighth of a
{{ep.frame_log}} inch log, lying on one sawn face with its point toward the
middle, the way chapter {{ch.pinwheel}} builds it. Its other sawn face rises
at forty-five degrees and leans back over it. So the opening is a tray:
smallest at the flat side, where the members' points are, widening up the
slope to the open side, {{ep.depth}} inches above. Every piece that fills it
has to rest on that slope, which is why no piece in it has a square end.

And the triangles next door fold away from this one, at {{ep.fold_a}} and
{{ep.fold_b}} degrees. A filling stops at the frame. A covering does not: it
runs over the frame and meets the next panel's covering at the seam, so it
has to lean to meet it.

## The wedge footage before the cut list

Here is a planning example with its inputs stated before its result:

```text
{{wm.assumptions}}
```

This example takes {{wm.long_in}} inches as the nominal long chord. The
short chord is {{wm.short_in}}, calculated at full precision by the same
raw-wedge solver. Its {{wm.isosceles_panels}} isosceles triangles and
{{wm.equilateral_panels}} equilateral triangles have a gross area of
{{wm.area_sqft}} square feet. This is a different sizing rule from the
calculator's maximum finished member, which is why the earlier tray's
dimensions need not be the same.

The drawing's {{wm.members}} independent-panel edge lengths total
{{wm.nominal_frame_ft}} feet. The solver's actual cut-stock framing totals
{{wm.finished_frame_ft}} feet; the pinwheel stops at faces, not the
mathematical corners. If every stick comes from a {{wm.blank_in}} inch
blank, reserve {{wm.gross_frame_ft}} feet before cutting. Do not harvest
only the finished total and discover at the saw that the short members still
needed full blanks.

## One face, two wedges, one coverage pitch

For a {{wm.log_in}} inch log split {{wm.splits}} ways, the ideal outer
chord is {{wm.chord_in}} inches. The planning example assumes the frame
uses half that width inward from every triangle edge. With the triangle's
inradius r, moving all its edges inward by d leaves the area multiplied by
max(0, 1-d/r) squared. That leaves {{wm.opening_sqft}} square feet in this
example. The actual tray opening is instead measured at the installed face
by the calculator's opening solver.

The material question is how much continuous face a pair closes. Both
wedges cost timber. If their continuous projected coverage is c inches,
then:

```text
infill wedge feet = two wedges x opening square feet x twelve / c
assumed pair coverage = (two minus projected overlap) x outer chord
```

{{wm.pair_table}}

That is a conditional range of {{wm.least_infill_ft}} to
{{wm.most_infill_ft}} wedge feet, not a guaranteed cut schedule. Its
least-material endpoint assumes continuous coverage at the largest stated
pitch. A real joint may need sealing or a different pitch, and a bowtie
that looks wide can still leave the required face open.

Keep the orientation explicit. The calculator's flip-flop alternates point
directions. Two points both toward the dome interior are another arrangement.
The opposed-point chord-triangle experiment is another again: sliding those
triangles changes contact and voids without changing their wood area. Its
envelope span is not the coverage pitch. An air cavity is not, by itself, an
insulation rating or a structural connection.

For the separate opposed-point experiment, replace the curved backs with
ideal straight chords and state the cell being measured. Its triangular
height is {{wm.section_height_in}} inches. If e is the slant engagement,
the envelope depth is height times (two minus e), the contact is radius
times e, and the assumed periodic cell's solid fraction is one divided by
(two minus e). Its void fraction is what remains:

{{wm.section_table}}

Those are envelope-depth and contact figures, not face-coverage pitches.
The two triangles retain their wood area throughout. A near-bowtie needs
its fixing, bridging and sealing worked out; the table cannot declare it
a panel that carries a load. Nor does this opposed-point experiment solve
the owner's two-points-inward proposal. The installed orientation and the
continuous face must be checked together before choosing an infill pitch.

## Reserve raw trunk, then add the infill

The ideal uniform {{wm.trunk_ft}} foot usable trunk supplies
{{wm.rounds_per_tree}} rounds and {{wm.wedges_per_tree}} frame-length
wedges, or {{wm.tree_wedge_ft}} wedge feet. Reserve
{{wm.frame_trunk_ft}} feet of raw trunk for the frame blanks first, and
add the infill footage divided by {{wm.splits}}. The table therefore gives
{{wm.least_raw_trunk_ft}} to {{wm.most_raw_trunk_ft}} raw trunk feet,
or {{wm.least_trees}} to {{wm.most_trees}} whole reference-tree equivalents.
Dividing the shorter finished frame by the splits would spend its trimming
allowance twice.

These are uniform-diameter equivalents, not promised standing-tree counts.
Kerf, defects, taper, course ends and fitting losses still belong in the
stock plan. A reusable frame offcut only reduces that plan when a named
infill course actually fits in it. The calculator below is the next step:
solve the pieces, then allocate them to stock.

## One wedge, start to finish

Take the obvious way to fill a triangle with wood from the same log as its
frame. Split it into wedges, lay them in stripes parallel to the long base,
and flip-flop them: one point up, the next point down, so each pair nests
into a strip with two flat faces. A {{ep.infill_log}} inch log fills the
long-based triangle with {{ep.wedges}} of them, from {{ep.wedge_long}}
inches long down to {{ep.wedge_short}}. Each one stops where it meets the
forty-five degree wall at both ends, so every end is a compound cut, and no
two are the same length.

The calculator follows each one from the stick to the panel. Here is piece
{{ep.piece}}, start to finish.

**Its lengths.** A wedge has three long corners -- the point, and the two
bark corners -- and because its ends lean, each is a different length:
{{ep.point}} inches along the point, {{ep.corner_b}} along one bark corner,
{{ep.corner_c}} along the other. Those three numbers are what you mark. A
fourth number, the length to take from the pile, is the longest of them
plus a little to trim.

**Cut one.** Lay the stick on its sawn face on the mitre saw, the bark
corner against the fence, the keeper to the {{ep.keeper1}} of the blade.
Swing the mitre to {{ep.mitre}} degrees and tilt the blade {{ep.bevel}}, and
take just enough off the raw end to clear it everywhere. What falls away is
a tapered sliver, {{ep.off1_long}} inches at its longest and
{{ep.off1_short}} at its shortest.

![Cut one: sawn face down, bark corner to the fence.](plate-ep-saw.png)

That setting is not a rule of thumb. The calculator found it by trying every
face of the stick on the table, with each end toward the fence, and working
out for each what the saw would have to do: how far to swing, how far to
tilt, and which way. A single-bevel mitre saw tilts one way only, and swings
about fifty-five degrees either side. Of every way that works on that saw,
it keeps the one that lies flat and steady and puts the point where you can
see it.

**Cut two.** Turn the stick end for end, its point against the fence, and
measure from the first cut: {{ep.point}} inches along the point, and the
other two corners to their own lengths. Join the marks across the top face,
and the blade follows the line, at the same {{ep.mitre}} and {{ep.bevel}}.
This offcut is {{ep.off2_long}} inches long. That is a piece in its own
right, and it goes back on the pile for a shorter stripe.

![Cut two, and an offcut long enough to keep.](plate-ep-offcut.png)

**Check it, and put it in.** Measure the three lengths against the list,
chalk the number on, and it goes into the panel in its stripe, its point
down or up as the list says.

Sixteen more like it, each with its own numbers, and the panel is full.

## When the saw cannot reach

Not every cut fits a mitre saw. Cover the panel instead of filling it, with
a sheet of oriented strand board, and the calculator cuts it in
{{ep.sheet_halves}} halves to fit a sheet, and gives each edge a bevel so it
meets the next panel's covering: half the fold at that seam, which is
{{ep.sheet_bevel1}}, {{ep.sheet_bevel2}} and {{ep.sheet_bevel3}} degrees.

Those cuts run the length of a sheet, and no mitre saw takes a sheet. So the
calculator says so, and gives the cut another way: the corners measured in
from the sheet's own corner, a chalk line snapped between each pair, and a
circular saw run along the line with its blade tilted to the bevel. The same
happens to any cut steeper than the saw can swing or tilt: it is marked on
the stick and cut by hand, and the calculator says where each mark goes.

## Ten ways to fill one triangle

Wedges in stripes are one way. The calculator does many, and lays out each
with every piece numbered and cut. Here are {{ep.perm_count}} of them in the
long-based triangle, and how many pieces each takes.

    {{ep.perm_table}}

![One of the ten: the same triangle, another fill.](plate-ep-perms.png)

Log rounds are the odd one out, and the most work. They are slices across a
whole trunk, {{ep.round_thick}} inches thick, laid in a honeycomb
{{ep.round_layers}} layers deep. {{ep.round_whole}} go in whole and
{{ep.round_wall}} are cut where they meet the wall. That leaves gaps no round
fits, and the calculator fills them the way a carpenter would: lay another
round over the gap, trace the gap onto it from underneath, and cut to the
line. There are {{ep.round_gaps}} of those, so the panel takes
{{ep.round_pieces}} pieces in all.

Every pattern can be turned over, too. The face the room will see is the
flat side, where the frame's points are, and in a flip-flopped fill every
other wedge shows its point there. It is worth looking at before you cut
anything, because it is the face you will live with.

![From underneath, the face the room will see.](plate-ep-under.png)

## Five trunks, one pentagon

The floor is the same kind of work on a bigger scale, and it starts with
wood already on the ground: five half trunks, twenty feet long. Stood on
edge, round back out and flat face in, and joined at the corners, they make
a pentagon whose backs measure the full {{ep.side_ft}} feet.

How big a floor is that? The largest circle that fits inside a pentagon
touches the middle of each side, at the apothem: the side over twice the
tangent of thirty-six degrees, {{ep.apothem}} feet here. Measured to the flat
faces, inside the half trunks, the circle is {{ep.inner_r}} feet in radius.
The dome needs {{ep.dome_need}} feet: its sphere, plus {{ep.overhang}} inches
for its frame standing out at the foot. It fits, with {{ep.margin}} feet to
spare at the narrowest, and the five corners of the pentagon are left over
outside it, which is room for steps, a woodpile, or a bench in the sun.

![Five half trunks, round backs out, round the dome's centre.](plate-ep-frame.png)

Every corner is the same cut. A pentagon turns seventy-two degrees at each
corner, and each trunk takes half of that: its end is cut {{ep.corner_deg}}
degrees off square. Along the round back a trunk keeps its full
{{ep.back_in}} inches. Along its top, where the flat face starts, each cut
takes {{ep.trim_in}} inches, so the top is {{ep.top_in}} inches long. No
mitre saw takes a log that size. Mark the line across the top, plumb it down
both sides with a level, and cut to the lines with the chainsaw.

![Thirty-six degrees off square, marked and plumbed for the chainsaw.](plate-ep-corner.png)

## A star, and why it needs joists

What goes inside? The first idea is a five-point star, corner to corner,
because a star braces a pentagon across every corner and is made of only
five lines. Each line crosses two others, so each is cut in three, and in
half trunks the star is {{ep.star_pieces}} pieces: the outer ones
{{ep.star_long}} inches, the inner ones {{ep.star_short}}, mitred where they
meet.

But the star alone fails, and it fails at the deck, not the frame. It leaves
the floor in large triangles, and something has to bridge them. The widest
gap a deck board would have to cross under the star alone is
{{ep.star_gap}} inches. A two by six deck board may cross {{ep.deck_allow}}.

![The star alone: the gaps a deck board cannot cross.](plate-ep-star.png)

So every space between the points is filled with joists: {{ep.joist_name}},
{{ep.spacing}} inches apart, each one running across its space the short
way, cut to meet the star or the frame where it lands. There are
{{ep.joists}} of them, and now the widest gap is {{ep.deck_gap}} inches,
inside the {{ep.deck_allow}} a deck board may cross.

![Joists between the points.](plate-ep-joists.png)

A joist shows the other thing the saw has to be told. It meets a star line
at an angle, so its end is cut off square, and a two by eight standing on
edge is {{ep.joist_depth}} inches tall: more than the {{ep.saw_h}} inches a
twelve-inch sliding saw cuts standing up. So it lies flat on the table, and
the angle moves from the mitre to the bevel: mitre zero, bevel
{{ep.joist_bevel}} degrees. Its other end, {{ep.joist_end1}}, is past the
{{ep.bevel_max}} degrees the blade tilts, and is marked and cut by hand.

## Where the weight goes

A floor has to carry its load somewhere, and the calculator follows every
pound of it. {{ep.live}} pounds a square foot for living and {{ep.dead}} for
the floor, over the whole pentagon, is {{ep.total_lb}} pounds.

Each patch of floor goes to the member nearest it, because that is what the
deck spans to. The joists hand their load to whatever they hang on, half at
each end. The star and the frame hand theirs to the piers under their
joints. Add up what reaches the piers and it is {{ep.pier_sum}} pounds:
every pound in is a pound out, which is the first thing to check about any
load path, and the calculator checks it.

:::box against "The span check"
A member between two supports bends under its load, and the wood takes it
as long as two numbers stay small enough. The bending moment, the load per
inch times the span squared over eight, divided by the section's strength
in bending, has to stay under {{ep.fb}} pounds per square inch. And the sag,
five times the load times the span to the fourth, over 384 times the wood's
stiffness and the section's stiffness, has to stay under the span over 360.
Both are worked out for every span of every member, for whatever section it
is: a half trunk on edge, a quarter, a whole log or a board.
:::

Where a span fails, the calculator puts a pier under it, as many as it takes.
Under the star and joists it took {{ep.extra}}, and now the hardest-working
span in the floor works at {{ep.worst}} percent of what it can carry.

That makes {{ep.piers}} stump piers, rounds of log standing on tamped
gravel, and each pad is sized from its own load, at {{ep.soil}} pounds a
square foot of ordinary soil. Most need only the smallest pad,
{{ep.pad_min}} inches square. The heaviest carries {{ep.pier_max}} pounds,
and needs {{ep.pad_max}}. The {{ep.hangers}} joist ends that hang on a
member rather than a pier get a joist hanger where they meet sawn lumber,
or a notch and a pair of spikes where they meet a log.

## Seven ways to frame the floor

The star with joists is one way. The calculator builds seven, from the same
trunks and the same joists, checks each the same way, and adds piers where
each needs them. On piers, with a two by six deck:

    {{ep.patterns}}

They all carry the floor; they do not all carry it the same way. Beams with
joists between, the way a deck is usually framed, works its hardest span at
only {{ep.beams_worst}} percent. Only the nested rings have more to spare,
{{ep.rings_worst}} percent, and they take {{ep.rings_piers}} piers to get it.
The fan sits at the other end: five spokes meet at one centre pier, and that
pier carries {{ep.fan_pier}} pounds, on a pad {{ep.fan_pad}} inches square.
The wheel's centre carries {{ep.wheel_pier}}. Bring the spokes to one point
and you bring the load there too.

On a levelled gravel bed nothing spans at all. Every member bears along its
length, the piers go away, and the gaps can be packed with gravel, earth or
cob instead of decked.

    {{ep.gravel}}

That is where the nested rings belong, the pattern this whole floor began
with: {{ep.rings}} rings of half trunks inside the frame, each ring's back
pressed against the flat face of the ring outside it, every corner the same
{{ep.corner_deg}} degree cut. There is a measuring rule that makes it easy:
the length of the next ring's piece, along its round back, is the length of
the flat face of the ring you just set. It costs about {{ep.rings_usd}}
dollars of gravel and nothing else bought. But it eats logs, {{ep.rings_logs}}
of them, against {{ep.gravel_sj_logs}} for the star with joists.

![Nested rings on a gravel bed, the gaps packed.](plate-ep-gravel.png)

And the materials can change, member by member. Keep the star and joists,
change what the star is made of, and the floor changes round it:

    {{ep.materials}}

Whole logs carry what half trunks carry but take {{ep.mround_logs}} logs.
Six by sixes are the strongest bought section and the dearest, about
{{ep.m6_usd}} dollars. Four by fours need {{ep.m4_piers}} piers,
{{ep.m4_extra}} of them propping spans a four by four cannot carry.

![The dome on its floor.](plate-ep-dome.png)

## What these numbers are not

The loads are a dwelling's, and they are a standard. The wood's strength is
not. These are your logs, not graded lumber, and {{ep.fb}} pounds per square
inch is a careful guess: no bonus for size, none for joists sharing a load,
stricter than a lumber span table. It is why some of these floors carry more
piers than a builder would expect. The prices are estimates, and the logs
are counted at nothing because they are your own trees.

So this is a floor that is checked and priced, not rated. Before people live
on it, an engineer signs it, with the wood graded or tested. What the
calculator gives the engineer, and you, is every piece numbered, every cut
set up, every span and every pier worked, and the patterns that fail shown
failing, so the conversation starts from the right floor.
