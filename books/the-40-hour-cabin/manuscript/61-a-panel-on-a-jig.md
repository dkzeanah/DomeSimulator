---
chapter: 61
title: A Panel on a Jig
strand: howto
status: draft
target: 2860
updated: 2026-10-03
---

# 61. A Panel on a Jig

<!-- concept: cabin_panel_method/rip -->

This is the framed-panel method from first cut to anchored shell, for the
three-frequency dome of Chapter {{ch.panel_geo}}: a popular, tried-and-true
way to build, shown here for comparison. The figures are this book's, solved for
its own reference dome; the pictures are this project's own renderings.

The idea is to move the work indoors. Each triangle is built flat, on a bench,
at a comfortable height, out of the weather. It can be finished and skinned
before it ever leaves the shop. On site, the dome is mostly a matter of
screwing finished frames together.

## Finish, then rip in half

The sticks are sawn lumber: a 2x3, ripped in half down its length, gives two
sticks {{pm.stick_w_in}} inches wide and {{pm.stick_d_in}} inches deep. A 2x6
ripped into two 2x3s first is often straighter than any 2x3 on the rack, and
straightness matters more here than species or grade.

**Finish the boards before you rip them.** The face the saw makes is hidden in
the joint, so finishing whole boards is half the work of finishing sticks.

**Then rip on the bevel, through the centre.** Tilt the table-saw blade to the
bevel and set the fence so the cut runs through the middle of the board's end.
A cut through the centre of a rectangle leaves two pieces that are copies of
each other, turned end for end -- the same symmetry that makes a split log give
identical wedges in Chapter {{ch.split}}. Turn the offcut over and send it back
through for a hair more, and the two halves come out exactly alike. A stick a
little smaller than planned is fine; sticks that differ from each other are
not. The bevel itself must be right, so set it with a digital angle gauge, not
the saw's scale.

## Draw the jig with two arcs

<!-- concept: cabin_panel_method/jig -->

The jig is a sheet of 3/4-inch plywood -- thick enough not to warp -- with the
panel drawn on it full size. Snap a straight line for the base and mark the
base length on it. Make a **trammel**: a thin stick with a nail through each
end. Set it to one side length and swing an arc from one end of the base; set
it to the other side length and swing an arc from the other end. Where the
arcs cross is the apex. Measure all three sides again before joining the
points. For the hexagon panel the apex lands {{pm.hex_height_in}} inches above
the base line; for the pentagon panel, {{pm.pent_height_in}}. Cut the sheet down
to an inch or two outside the lines.

It is the same jig, in spirit, as Chapter {{ch.jig}}: geometry solved once on a
flat board and then copied by every panel.

![Where the arcs cross is the apex.](plate-panel-jig.png)

## Rails, and the line

<!-- concept: cabin_panel_method/rails -->

Lay a stick along one side, flat face down and bevel out, with its outer edge
*splitting* the pencil line. Clamp it. Butt a straight rail against its inside
edge and screw the rail down hard. Unclamp, and do the other two sides. Now
any stick pushed against a rail lands exactly on its line. The jig does not
care what section the sticks are, so long as every stick is the same.

## Sticks that turn like a pinwheel

<!-- concept: cabin_panel_method/pinwheel -->

The three sticks do not meet at a point. Each runs all the way to one corner
and butts into the inside face of the next, so seen from above the corners
turn like a pinwheel. It is the pinwheel of Chapter {{ch.pinwheel}}, met again
in a different dome: nothing meets at the corner, so no corner needs a hub.

A pinwheel has a consequence that surprises people: the two equal sides of a
panel do **not** take the same stick, because one butts and the other is butted
at the apex. A stick of width *w* that butts at a corner of angle *phi* stops
*w* / sin *phi* short of the corner and is cut 90 - *phi* off square. Every
stick in the dome:

    {{pm.stick_table}}

That is **{{pm.distinct}} different sticks**, {{pm.sticks}} in all, about
{{pm.stick_ft}} feet of them.

Cut each stick's first end, lay it in the jig against its rail, and mark where
the next stick's inside face crosses it. That second end is a compound cut --
the tail miter and the bevel together. A miter saw that bevels both ways makes
it in one pass; a handsaw, cutting flush along the next stick after the panel
is screwed, works too and is pleasantly slow. Clamp a stop block for the
repeats, and check a stick in the jig every few cuts in case the block has
crept.

Half panels -- at a door, or where the base needs one -- are drawn on the same
jig, but their middle stick runs across the triangle rather than along an
edge, so it takes a different bevel or none at all. Check it before you cut it.

![Three sticks, six kinds in the dome.](plate-panel-pinwheel.png)

## One bevel cannot be exact

<!-- concept: cabin_panel_method/bevel -->

:::box against
Here is the number that does not flatter this method. The panels do not all
turn by the same angle where they meet. Across a B edge alone the fold runs
from {{pm.fold_b_lo}} to {{pm.fold_b_hi}} degrees, and over the whole dome the
exact stick bevel runs from **{{pm.bevel_lo}} to {{pm.bevel_hi}} degrees**. A
shop rips every stick at one setting -- {{pm.bevel_mid}} degrees, halfway -- so
the worst joint is **{{pm.bevel_err}} degrees** off.
:::

That is too small to see and not too small to leak. Lay a bead of sealant or a
strip of gasket between the frames as they go together; that is what takes up
the difference.

![Red where one setting is furthest off.](plate-panel-bevel.png)

## Skin it in sections, raise it loose

<!-- concept: cabin_panel_method/skin -->
<!-- concept: cabin_panel_method/window -->
<!-- concept: cabin_panel_method/raise -->
<!-- concept: cabin_panel_method/anchor -->

**Sections.** Before raising, screw panels into whole pentagons and hexagons on
the shop floor and cover each group with one sheet. At this cut
{{pm.sections_pent}} pentagons and {{pm.sections_hex}} hexagons come out whole,
and {{pm.sections_single}} panels are skinned one at a time. Pull the film tight
and staple it on the bevelled edges, where the next section hides the staples.
A woven poly film stretches less than a thin greenhouse film and forgives a cold
day; a thin film tears where a woven one does not.

This is a different trade from Chapter {{ch.one_layer}}, which argues for one
continuous watertight layer over the whole frame. Sections are repairable --
a torn one is one section to replace -- but every seam between sections is a
joint to tape and to keep.

![One sheet per pentagon or hexagon.](plate-panel-skin.png)

**Windows.** Build one extra frame for each window. Leave the skin off that
panel in the dome, cover the spare frame, and hinge it along its top edge. A
small gas strut of the kind kitchen cabinets use holds it open. Weather-strip
the face it closes on, so rain running down the dome cannot creep under it,
and tape the hinge seam once the dome is up.

![A spare frame on two hinges.](plate-panel-window.png)

**Raising.** Assemble from the base ring up, with a helper and plenty of clamps.
Put only a few screws in each joint until the last panel closes the dome: until
then the shell flexes, and that flex is what lets the last panels in. Lay the
sealant or gasket between frames as they meet. Do not raise a loose shell in
wind.

**Taping.** Tape the open seams between sections from the bottom up, each strip
lapping over the one below, so water always runs onto tape and never under it.
The surfaces must be clean and dry or the tape is decoration.

**Anchoring.** A dome is light for its size, and wind lifts. On a deck, angle
brackets tie every base section to the frame below. On gravel or earth, steel
stakes driven at a slant and strapped to the base sections do the same job.
Anchor before the skin is finished, not after the first storm.

## A doorway that sticks out

A five-eighths dome's own wall gives room for a door, but a door set into
triangles is a door with a slanted head. The better answer is a short
projecting entry -- an arch doorway -- built from the same kind of panels: a
row of roof panels and a row of wall panels standing out from the dome, with
two posts and a header inside them carrying an ordinary rectangular door. The
same piece built twice, back to back, is a covered passage joining two domes
into one building, which is the network of Chapter {{ch.network}} at the scale
of a single site.

Its panels are not triangles of the sphere, so they are built on **templates**
rather than a trammel jig: each panel's outline is cut full size from a sheet,
the sticks are fitted inside it, and the template is then turned over to build
the panel's mirror twin for the other side. One stick on each roof panel --
the one that lands on the dome -- is the only thing allowed past the template's
line, because its bevel is what seats the entry against the existing frame.
That bevel is sharp; it is easier to rip with the board standing on edge, the
saw set to the complement of the angle. The wall panels are drawn the same
way, then shortened by the depth of the roof's edge stick so they fit snugly
under it. Put the roof panels up first, then the walls, then the posts and
header.

This book does not solve the entry's geometry -- its angles depend on where
it meets the dome and how far it projects -- so it gives no figures for it.

## Against the wedge dome

<!-- concept: cabin_panel_method/compare -->
<!-- concept: cabin_panel_method/close -->

    {{pm.compare}}

The panel dome is the better-trodden road: many people have built one from bought
plans, and the method forgives a beginner. It asks for a table saw, a miter saw,
bought boards, and a lot of identical cuts. The wedge dome asks for trees and a
chainsaw, and gives back fewer, bigger pieces that carry their angles in their
own shape. Neither is wrong. Choose by what you have.
