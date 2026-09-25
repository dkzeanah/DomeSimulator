---
chapter: 11
title: Two Lengths, and Neither Is the Chord
strand: howto
status: draft
target: 940
updated: 2026-09-25
---

# 11. Two Lengths, and Neither Is the Chord

A 2V dome has two member lengths. This is the page you come back to.

## The two chords

A chord is the straight-line distance between two vertices of the sphere. It
is the number every geodesic reference publishes, and it is a property of the
shape rather than of your building:

    A chord   =  {{cut.a_factor}} x radius
    B chord   =  {{cut.b_factor}} x radius

At this book's radius of {{dome.radius_in}} inches, that is
{{cut.a_chord}} and {{cut.b_chord}} inches.

The A chord being a round 72 is not luck. The dome was sized from the stick:
a six-foot member is what comes comfortably out of a twelve-foot log section,
what one person carries, and what fits in a pickup. The diameter is the answer
to the member, not the other way round.

## The chord is not what you cut

Neither end of a member reaches the vertex it is named after.

One end butts into the *side* of its neighbour, short of the corner. The
other runs past the mathematical vertex so that the previous member can butt
into its side. Chapter {{ch.pinwheel}} is why. The consequence is that the
joint takes a bite out of each end, and the cut length is:

    cut  =  chord  -  bite

For this frame:

    A members   {{cut.a_chord}}  -  {{cut.a_bite}}  =  {{cut.a_cut}} in
    B members   {{cut.b_chord}}  -  {{cut.b_bite}}  =  {{cut.b_cut}} in

## The bite does not scale

This is the part that catches people.

The bite is set by **how wide the member is**. A member does not get wider
because the dome gets bigger — you are still splitting the same size of log —
so the bite is the same number at every diameter.

Solve the same pinwheel at a four-foot radius and at a fifteen-foot one with
the same stick and the bite comes out identical to four decimal places.

So: **scale the chord, subtract the bite.** Not chord times a ratio.

If you take one thing from this chapter, take that.

## The bite used here

    A members   {{cut.a_bite}} in
    B members   {{cut.b_bite}} in

Both at this book's {{cut.width}}-inch member. A wider member takes a bigger
bite, roughly in proportion, so a frame cut from heavier stock wants its own
solve rather than this number.

## Why the distinction is worth a page

Scaling the bite with the dome is the natural mistake, because everything
else about a dome does scale.

It is also invisible at the reference build, where the two arithmetics agree
exactly. It only shows up at other sizes: at eight feet across, scaling
makes every stick more than an inch too long; at twenty-four feet, half an
inch short. Every stick, all {{dome.members}} of them, in the two sizes a
first-time builder is most likely to pick.

That is why every figure in this book is generated rather than typed, and
checked against the solver on each build — Chapter {{ch.tooling}}. An error
that is exactly right in the one case you test is the kind that survives
proofreading.

## Two models, and they disagree

This repository solves the pinwheel twice.

The raw-wedge solver treats a member as a real {{cut.sector}}-degree log
sector. That is where the bites above come from, it is what the simulator
draws, and it is what the reference build is cut to.

A second, simpler model treats a member as a rectangular band lying with its
face on the edge line. It gives a bite of {{cut.band_bite}} inches for the
same stick — several times larger.

![How much of the tree survives, measured.](plate-yield.png)

Neither is a mistake. They are answers about differently shaped sticks.

The numbers in this book are the first. **If you are cutting rectangular
stock rather than log sectors, this table does not describe your frame**, and
the difference is inches on every member.

## The row to check yourself against

{{dome.diameter_ft}} feet across: A chord {{cut.a_chord}}, A cut
{{cut.a_cut}}.

If your own arithmetic gives that, the rest will behave.

![Chord factors turning into a cut list.](plate-factors-to-lumber.png)
