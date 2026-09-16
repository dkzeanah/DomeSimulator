---
chapter: 5
title: The Cut That Changed It
strand: story
status: drafting
target: 3250
updated: 2026-09-08
---

# 5. The Cut That Changed It

*Split the trunk like a cake, and the stick is already the right shape*

<!-- Every number in this chapter must come from:
     - wedge_geometry.SECTORS_PER_LOG
     - wedge_geometry.sector_chord_in
     - wedge_geometry.sector_depth_in
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## The Cut That Changed It

I want to tell this one without hindsight tidying it up, because the tidy
version — *I realised the dome would accept any consistent section, therefore
I split the log radially* — is not what happened and it teaches nothing. What
happened was that I was tired of brackets.

## Half, half, half again

The frankendome had taught me that a frame of forty triangles will stand up
even if no two of its sticks match. The V-bracket afternoon had taught me
that making a connector tolerant enough to join anything to anything means
the connector is now doing all the work, forever, in forty places.

So I had stopped asking how to join dissimilar sticks and started asking the
opposite question: what would it take for them not to be dissimilar?

The answer that everybody gives is *mill them*. Square them up, run them
through a planer, and now they are all 2x4s. That answer costs a mill, a
planer, a shed to keep them in, and about half the tree.

I was sitting on a section of trunk at the time. Not thinking about it.
Sitting on it.

And the thing about a round section of trunk is that it is already
rotationally symmetric. Every radius is the same as every other radius. If
you split it through the middle you get two identical halves, not because you
were careful but because the log was round before you touched it. Split those
and you get four. Split those and you get {{tree.sectors}}.

Three passes. Eight sticks. Every one the same, to whatever tolerance the
tree was round to, which is a tolerance nobody had to hold and nobody had to
check.

![Three cuts. Eight structural members.](../../deliverables/book/figures/trunk-eighths.png)

I did it that afternoon on a piece I had been about to burn.

## What became obvious immediately

Four things, in about a minute, and I want to record that they were obvious
because the ones in the next section took a week and I do not want to flatter
the story.

**One section, everywhere.** Every stick in the frame has the same
cross-section: {{member.width_in}} inches across the bark face,
{{member.depth_in}} inches from pith to bark, {{member.area_in2}} square
inches of wood. So one jig fits all of them. One fixture, one set of stops,
one procedure repeated a hundred and twenty times. That is what makes this a
fortnight instead of a summer.

**Depth where you want it.** A sector is deep — it runs the whole way from
the pith to the bark — and depth is where bending stiffness lives. The stick
is not a compromise between what the tree gave and what a mill wanted. It is
the deepest member you can cut from that log, which is a strange thing to get
for free.

**No machine between the tree and the frame.** Fell, buck, split, build. The
chainsaw does all of it. There is no second machine, no second setup, no
second building to keep the second machine in.

**Four ways up.** This one I noticed while stacking them. The sector is not
symmetric about its own long axis — it has a point and a curved back — so you
can rotate it four sensible ways in the wall and get four different things:
which face the weather sees, which face the next stick lands on, whether the
points of a pair aim together or apart. That is Chapter {{ch.orientations}}, and it is the
most genuinely new thing in the method.

## And what took another week

Now the part the tidy version leaves out.

I assumed, because the sticks were identical and the panels were identical,
that the *joints* would be identical. Forty triangles, all the same, all
meeting each other the same way.

They do not.

A dome is a sphere approximated by flat panels, and the angle at which two
panels meet is not the same everywhere on it. It cannot be — the sphere
curves differently in different places, and a 2V hemisphere has two classes
of edge for exactly that reason. So the seam between two panels folds by one
amount here and a different amount there, and a key cut to fit one seam will
not fit the other.

I did not want this to be true. I spent the better part of a week trying to
make it not be true: fudging the panel outlines, trying a compressible
gasket, trying to talk myself into the idea that the difference was small
enough to force closed. It is not small enough. Forty panels of *nearly*
closing is a dome with a gap in it.

What actually resolved it was measuring instead of arguing. Across all
{{frame.seams}} seams there are only **{{seam.distinct_angles}}** fold
angles. Not forty. Not a continuum. Two: {{seam.fold_a_deg}} degrees and
{{seam.fold_b_deg}}.

That was the moment the method became buildable rather than merely elegant.
{{seam.distinct_angles}} angles means {{seam.distinct_angles}} key profiles:
cut one of each until it fits, then repeat it {{seam.count_a}} and
{{seam.count_b}} times. The difference between "the seams vary" and "the
seams take {{seam.distinct_angles}} values" is the difference between a
research project and a fortnight, and I lost a week to not knowing which one
I was in.

The chart is in Chapter {{ch.seams}}, where it belongs.

## The bit I got wrong in public

While all this was going on I was saying, out loud and on camera, that
nothing in the dome needed a mitre.

That is not true and it was never true. The end of each stick that lands on
the side of the next one — the butt end — is a compound cut: a mitre and a
bevel together. What is true, and what I should have been saying, is that no
end is ever mitred *to another end*. Every joint is an end landing on a
flat side, which means each stick is cut once, on one end, before it goes
anywhere near the assembly, and the other end is left long and sawn off in
place.

That is a much better claim than the one I made, and it is a shame I spent
several months making the wrong one. Chapter {{ch.pinwheel}} has the geometry and Chapter {{ch.corrections}} has the full list of things this project has had to take back.

## What it is worth

The number that convinced me it was not just a neat trick: splitting this way
keeps {{tree.recovery_pct}} per cent of the solid wood in the trunk, against
about {{tree.sawn_recovery_pct}} per cent for the same log sawn into
two-by-fours the way a mill would. That is {{tree.recovery_gain}} times the
usable wood, from a cheaper process, with one machine instead of four.

Chapter {{ch.recovery}} does that arithmetic properly, including the parts of it that are
less flattering than they first appeared.

But sitting on that log, what I had was a much simpler observation, and I
still think it is the whole book:

**A round thing splits into identical pieces for free. A square thing has to
be made square, and you pay for that in wood, in machines, and in time.
Domes are the buildings that will accept the free pieces.**
