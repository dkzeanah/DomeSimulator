---
chapter: 11
title: Choosing a Size, At Last
strand: howto
status: draft
target: 880
updated: 2026-09-25
---

# 11. Choosing a Size, At Last

Everything up to here has been ratios. Nothing has had a unit on it.

That is deliberate: the geometry is scale-free, so it is worth solving once
and then choosing a size — rather than choosing a size and re-solving the
geometry inside it, which is how most people do it and is why most people only
ever build one dome.

![The push that makes it geodesic.](plate-project.png)

## One number does it

<!-- concept: 2v/cut_list -->
<!-- concept: scratch/scale -->

Pick any one of these and the rest follow:

* the radius
* the long member's chord
* the diameter
* the apex height (which is the radius)
* the floor area

They are all the same number wearing different units. Multiply the radius by
{{cut.a_factor}} and you have the long chord; by {{cut.b_factor}} and you have
the short one; everything else is those two and the counts from Chapter
{{ch.hemisphere}}.

## This book picks the stick

The reference build is sized from the **member**, not from the floor plan.

{{cut.a_chord}} inches — six feet — because:

* it is what comes comfortably out of a twelve-foot log section, with the
  crosscut in the middle;
* it is what one person carries without thinking about it;
* it fits in a pickup bed, diagonally, with the tailgate up.

The dome that falls out of that is {{dome.diameter_ft}} feet across with
{{dome.floor_sqft}} square feet of floor. **The diameter is the answer to the
member, not the other way round.**

That is backwards from how buildings are normally sized and it is the right
way round for a method whose whole argument is about what one person can make
and move.

## What it costs to size from the member

One real inconvenience, stated plainly.

No panel fits a four-foot sheet. The narrowest face is {{seam.narrowest}}
inches across its shortest altitude and a sheet is 48. Every panel of the
reference build needs a seam in its sheathing or a wider sheet.

That is a direct consequence of sizing from the stick, and anybody who would
rather have the sheets than the six-foot member should build a different
diameter. Chapter {{ch.two_lengths}}'s table will give them one.

## What a bigger radius buys

<!-- concept: build/sizing -->

Pick the size for a reason, because the radius does not scale everything the
same way. Double it and you get four times the floor, four times the skin you
have to buy and keep watertight, and eight times the air you have to heat.
Floor and skin grow with the square of the radius; volume with its cube.

And headroom at the wall is the thing people underestimate. At the very edge of
a hemisphere there is none at all: the shell meets the floor at the rim. The
first ring of a {{dome.diameter_ft}}-foot dome is the band you sit against,
not the band you stand in, and a bigger dome only pushes that band outward.

## Audit the boards you have

<!-- concept: 2v/your_dome -->

A chord factor turns a radius into a length. It also runs backwards: a length
you have already cut implies the radius it was cut for. That makes it a way to
check boards you already own.

Say you have two members measured at {{geo.fit_long}} and {{geo.fit_short}}
inches. Each one, on its own, implies a radius:

    from the long board     {{geo.fit_long}} / {{cut.a_factor}} = {{geo.fit_r_long}} in
    from the short board    {{geo.fit_short}} / {{cut.b_factor}} = {{geo.fit_r_short}} in

They disagree, because tapes and saws are not exact. The fair answer is the
radius that misses both by the least -- a least-squares fit:

    best radius             {{geo.fit_r}} in
    long board misses by    {{geo.fit_res_long}} in
    short board misses by   {{geo.fit_res_short}} in

Two lessons come with it. Keep the centre-to-centre geometry separate from the
physical cut length: what you measure on a board is the cut, which is the
chord less what the joint takes (Chapter {{ch.two_lengths}}). And the ratio of
the two boards, {{geo.fit_ratio}}, should be close to the geometry's own
{{geo.true_ratio}}; if it is far off, one of the two lengths is wrong, and the
fit will not tell you which.

## If you would rather size from the floor

Work backwards.

Floor area for a decagon inscribed in a circle of radius R is
5·R²·sin(36°), so a target floor of A square feet wants

    R  =  sqrt( A / (5 · sin 36°) )

and then the long chord is {{cut.a_factor}} R and the cut is that minus
{{cut.a_bite}} inches. A 400-square-foot floor wants a radius of about 11.7
feet and a long member a shade over seven feet — which is past comfortable
one-person handling, which is the trade.

## Five sizes worth knowing

The reference designs, from a demonstration you build to get it wrong on, up
to the point where a 2V starts to strain. Each one is a full cut list in the
tables at the back, and each one is the same {{dome.members}} members and the
same nine processes.

The only thing that changes between them is two numbers.

## What an eighth of an inch does

<!-- concept: build/error -->
<!-- concept: master/ms_math_error -->

Here is a number worth carrying to the site.

The base ring is a regular ten-sided polygon, and the radius of a regular
polygon is its side divided by a fixed constant. For ten sides, that constant
is exactly one over the golden ratio. So every error in a base member reaches
the foundation multiplied by {{geo.ring_gain}}:

    each base member long by        {{geo.ring_err}} in
    the base radius grows by        {{geo.ring_r_err}} in
    the diameter by                 {{geo.ring_d_err}} in

The same golden ratio that placed the twelve parent corners now governs how
your mistakes grow. It is not a large factor, but it is a multiplier, and it is
why a hand-built dome drifts bigger rather than smaller.

![The base ring multiplies your mistakes by phi.](plate-ring-error.png)

## Close the measurement loop

<!-- concept: 2v/verify -->
<!-- concept: build/check -->

So measure in a fixed order, every time, and do not go on until each check
passes:

1. **The member**, against a master gauge stick.
2. **The triangle**, on all three corners, on the jig.
3. **The ring**, on its diameter, three ways across.
4. **The radius**, from a centre pin to every corner.
5. **The height**, from the floor to the apex: on a true hemisphere it is the
   radius, so the two numbers have to match.

Each check catches what the one before it could hide. A member can be right and
a triangle wrong; a ring can be round and the wrong size. Doing them in order
is what stops a small error becoming a structural one, and it is why the ring
is checked before the next ring goes up. For anything you will live in or load,
your local code and an engineer have the last word.

![Member, triangle, ring, radius, height.](plate-measure-loop.png)

## The whole transformation

<!-- concept: 2v/finale -->
<!-- concept: build/recap -->

That is the whole derivation, and it is short enough to say in one breath.

The golden ratio places twelve corners. One division puts them on a sphere of
radius one. Halving every edge and pushing the midpoints back out leaves exactly
two edge lengths, as multipliers. One radius turns those into two chords; the
joint's bite turns the chords into two saw settings; one flat board turns the
settings into {{dome.panels}} identical panels; the rings turn panels into a
shell; and a skin turns the shell into a room.

Every number on the way came from the geometry, and every one of them can be
recomputed rather than trusted.

![From the golden ratio to a building you can stand inside.](plate-whole-transformation.png)
