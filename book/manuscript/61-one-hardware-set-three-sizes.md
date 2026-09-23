---
chapter: 61
title: One Hardware Set, Three Sizes
strand: explain
status: drafting
target: 1500
updated: 2026-09-17
---
# 61. One Hardware Set, Three Sizes

*The brackets, keys and fasteners that frame a small dome frame a large one unchanged, which is what makes a shared parts bin possible across a whole site*

## One Hardware Set, Three Sizes

The first chapter of this part showed the flat rate: the *counts* do not move.
This chapter is a different and more useful claim. The *hardware itself* does
not move either.

Counts being flat means you buy the same number of things. Hardware being
flat means you buy the same *things*. The same bracket. The same key. The
same screw length. A part that leaves the bin for a garden dome leaves the
bin for the big one too, unchanged, unmodified, not a "heavy duty" version of
itself.

The reason is worth knowing, because it is the whole trick. A bracket in a
dome frame has one job: hold an angle. The angles in a dome do not change
when the dome gets bigger -- every edge is the same fraction of the radius,
so every joint sees the same geometry at a different scale. The bracket never
finds out how big the building is. Only the stick does.

The book's own frame makes the point from the inside. A wedge dome has not
forty different corner angles but a small, countable set -- the seams fold at
{{seam.fold_a_deg}} degrees and {{seam.fold_b_deg}} degrees, and nothing
else -- so the hardware exists to hold two angles, not a catalogue of them.
The {{bin.design}} frame in this chapter is a 3V frame rather than the 2V
wedge, but it obeys the same law: the hubs are the same {{bin.hubs}} hubs at
every diameter, because a hub is a set of angles, and the angles did not
move.

Those two fold numbers are the whole hardware kit, and they are worth a
slow read, because between them there is nothing else. Every seam in the
wedge frame folds to {{seam.fold_a_deg}} degrees or to {{seam.fold_b_deg}}
degrees, and no third value exists. So a part that holds a
{{seam.fold_a_deg}} seam and a part that holds a {{seam.fold_b_deg}} seam are
the only two kinds of corner the frame will ever ask the bin for. One spare
of each covers every joint in the building, a small one or a large one,
because the angle never found out which. Two is a count, not a tolerance; it
is the difference between a parts wall and a parts pocket.

A hub is the same idea, moved from a seam to a junction. Where several
struts arrive at once, the hub's only job is to hold each of them at its
correct angle, and that angle is set by the geometry, not by the length of
the wood. Make every strut longer and the hub does not notice -- it is still
holding the same set of angles, just further from the next hub. That is why
the hub bill in the table below holds still to the penny while the floor
multiplies: the hub is the joint, and a joint has no size. The stick is the
reach, and only the reach grows.

A fastener makes the point smaller and closer to hand. A screw or a key is
sized to the section of the members it joins, not to their length, and the
section does not change when the dome does -- not until the stick gets long
enough to need a fatter one. So the same screw length closes the same joint
on a {{bin.small_ft}} foot dome and a {{bin.large_ft}} foot one. The
hardware reads the timber's thickness. It never reads the building's width.

## The same bin, three domes

The proof is the {{bin.design}} frame run at three diameters, from the
Creator's own costing:

| | small | middle | large |
|---|---|---|---|
| diameter | {{bin.small_ft}} ft | {{bin.mid_ft}} ft | {{bin.large_ft}} ft |
| floor | {{bin.small_floor}} sq ft | {{bin.mid_floor}} sq ft | {{bin.large_floor}} sq ft |
| struts | {{bin.struts}} | {{bin.struts}} | {{bin.struts}} |
| hubs | {{bin.hubs}} | {{bin.hubs}} | {{bin.hubs}} |
| panels | {{bin.panels}} | {{bin.panels}} | {{bin.panels}} |
| hub bill | ${{bin.hub_cost}} | ${{bin.hub_cost}} | ${{bin.hub_cost}} |
| frame | ${{bin.frame_small}} | ${{bin.frame_mid}} | ${{bin.frame_large}} |
| panels | ${{bin.panel_small}} | ${{bin.panel_mid}} | ${{bin.panel_large}} |
| foundation | ${{bin.foundation_small}} | ${{bin.foundation_mid}} | ${{bin.foundation_large}} |
| whole build | ${{bin.total_small}} | ${{bin.total_mid}} | ${{bin.total_large}} |

Look down the middle three rows. {{bin.struts}} struts. {{bin.hubs}} hubs.
{{bin.panels}} panels. A hub bill of {{bin.hub_cost}} dollars, to the penny,
while the floor multiplies by {{bin.floor_gain}} and the total by nearly four.

Now look at what *does* move. The frame cost moves, because the frame is
timber and the stick is longer. The panel cost moves, because panels are
area and the shell is bigger. The foundation moves, and it moves hardest --
{{bin.foundation_small}} dollars to {{bin.foundation_large}}. Every row that
moves is a row of raw material. Every row that holds still is a row of
hardware. That is the table, whole.

The table stops at {{bin.large_ft}} feet, but the law it is showing does
not. A fourth row would print the same {{bin.struts}} struts, the same
{{bin.hubs}} hubs, the same {{bin.panels}} panels and the same
{{bin.hub_cost}} dollar hub bill, with a longer stick and a bigger
foundation underneath them. What stops the table is not the hardware. It is
the stick -- past {{flat.solo_member_ft}} feet a member wants a second pair
of hands -- and the ground, which is already the fastest-moving row on the
page. The bin never closes. The wood and the dirt eventually do.

One boundary on all of this needs to be said plainly, because it is the one
the flat-rate pitch is easiest to overstate. The hardware is flat across
*size*. It is not flat across *frequency*. A 2V wedge and a 3V frame are
different buildings with different strut counts -- {{flat.struts}} against
{{bin.struts}} -- and that difference is real, not a rounding. Raise the
frequency and the parts list grows, exactly as chapter {{ch.flat_rate}}
warned. Hold the frequency still and run the diameter out, and the hardware
does not move at all. Both statements are true; they are about different
dials, and the shared bin only makes the first one free.

## What invariance buys a site

One site, three dome sizes, one hardware bin. The economics of that are
quietly enormous, and they are the difference between a hobby and an
operation.

One order. You do not maintain three purchase histories and three suppliers;
you reorder the same line item until the price breaks.

One bin. Nothing in the bin says which dome it belongs to. A spare is a
spare for all of them, so the site holds one spare set instead of three, and
a broken bracket on Tuesday is fixed from stock on Tuesday instead of from a
catalogue in two weeks. The arithmetic of spares is the unglamorous version
of the same point: three designs each holding ten per cent spare parts means
three spare sets gathering dust; one bin holding ten per cent serves every
dome on the site, and the bin gets smaller as the site gets bigger.

One set of hands to train. The person who can drive the key on a small dome
can drive it on a large one, because it is the same key, the same angle, the
same motion. A park of mixed domes does not need a specialist per size; it
needs one skill.

One bill of materials to trust. The frame that went up first is the proof of
the frame that goes up second, because they are the same joints. The first
build de-risks the second in a way no paper review can: the hardware either
held its angle for a winter or it did not, and the answer applies to every
dome the site will ever put up.

The quietest saving in that list never shows on an invoice, and it is the
cost of the part that does not fit. A site running three hardware families
has three chances, every working week, to hand somebody the wrong bracket
for the job, and the wrong bracket is discovered on a ladder with half a
frame standing in the air. One bin removes that possibility. There is no
wrong bracket, because there is only one bracket. The mistake you cannot
make is worth more than the spare you never have to order, and it compounds
with every dome the site adds.

That is what invariance actually buys: the boring, compounding things --
inventory, spares, training -- that decide whether a site can grow without
falling over. The dome that scales the floor also scales the workshop, and
it is the workshop that scales the site.

## What does change, and it is the timber

Say the other half out loud, because the table says it and the flat-rate
pitch sometimes forgets it.

The stick grows. Every member in the large frame is nearly three times the
length of the small one, and longer stock is not just more wood -- it wants
straighter wood, bigger sections to stay stiff at length, and eventually a
second pair of hands at the lift. The member is where size shows up, and this
book has been honest about that from its first chapter: {{flat.solo_member_ft}}
feet is the declared limit one person sets alone.

The section grows, eventually. Past some diameter the same 2x4-class member
stops being enough, and the hardware does *not* change while the timber
does. A bracket that holds an angle holds it for a fatter stick too, which is
why the bin survives the upgrade.

And the skin grows with the square, as the earlier chapter on the envelope
said. So the honest summary of the whole idea is three lines: the *hardware*
is flat, the *timber* grows as a line, and the *skin* grows as the square.
Anybody who tells you the whole building is flat has counted only the first
line. Anybody who tells you the hardware grows has never looked at the
table.
