---
chapter: 58
title: The Cheapest Square Footage in the Building
strand: explain
status: drafting
target: 1560
updated: 2026-09-17
---
# 58. The Cheapest Square Footage in the Building

*Standing the shell on a short straight wall buys floor, headroom and usable edge for the least money per square foot of anything in the build*

## The Cheapest Square Footage in the Building

A dome has one weakness, and it is honest about where it is: the edge. A
hemisphere comes down to the floor at a tangent, so the ring of floor around
the rim has a ceiling sloping straight at it. You can stand in the middle of
the room. You cannot stand anywhere near the wall.

On the reference floor this book's performance chapter is drawn on --
{{pony.floor}} square feet -- only {{pony.usable_0}} of those feet are under
enough ceiling to stand up under. That is {{pony.pct_0}} per cent of the floor
you paid for, and the rest is a dead ring.

The fix is the cheapest wall there is. A short, straight stem wall stood under
the rim of the shell, lifting the whole dome a few feet off the ground. It
carries no thrust, because the ring at the base of the frame already takes
that. It is just a wall of height. And a wall of height is exactly what
converts a dead ring into the cheapest square footage in the building.

## The pony wall ladder

The ladder is four rungs, all computed from the same geometry, at the declared
cost of {{pony.wall_rate}} dollars a square foot of wall:

| wall | usable floor | share usable | the wall costs | floor gained | $/sq ft gained |
|---|---|---|---|---|---|
| none | {{pony.usable_0}} sq ft | {{pony.pct_0}}% | nothing | -- | -- |
| 2 ft | {{pony.usable_2}} sq ft | {{pony.pct_2}}% | ${{pony.cost_2}} | +{{pony.gain_2}} | ${{pony.rate_2}} |
| **3 ft** | **{{pony.usable_3}} sq ft** | **{{pony.pct_3}}%** | **${{pony.cost_3}}** | **+{{pony.gain_3}}** | **${{pony.rate_3}}** |
| 4 ft | {{pony.usable_4}} sq ft | {{pony.pct_4}}% | ${{pony.cost_4}} | +{{pony.gain_4}} | ${{pony.rate_4}} |

Read the bold row. The 3-foot wall is {{pony.wall_3}} square feet of ordinary
wall, {{pony.cost_3}} dollars. It buys back {{pony.gain_3}} square feet of
floor you already paid for and could not use -- a {{pony.gain_pct_3}} per cent
increase in usable room -- at {{pony.rate_3}} dollars a square foot.

Nothing else in this build sells floor at {{pony.rate_3}} dollars a foot. Not
the frame, not the skin, not the glass. The wall is the one part of the
building where the floor is already there and only wants lifting.

The other rungs are worth a look, because each has a different character.
The 2-foot rung is the bargain: {{pony.gain_2}} feet for {{pony.cost_2}}
dollars, the cheapest dollars on the ladder. It leaves a fifth of the floor
unusable, but for a workshop or a greenhouse -- rooms where you bend over
the work and do not care about the walls -- it is the right rung. The 4-foot
rung is the wrong one at the far end: it spends {{pony.cost_4}} dollars to
buy {{pony.gain_4}} feet, the last of them at {{pony.rate_4}} dollars a
foot, and the next section explains what else that height starts costing.
The 3-foot rung in the middle is the one for a room people live in, and the
reason it is the bold row is the third section of this chapter.

There is one more thing the wall buys that the table does not show, because
it is not a square foot: a band of straight wall around the room. On a bare
hemisphere the ceiling curves down to the floor everywhere, so a door has to
be cut out of a curved surface and a cupboard has to stand away from the
wall. On a 3-foot stem the first three feet of every wall is a vertical,
rectangular surface -- doors are rectangles in it, windows are rectangles in
it, shelves and counters stand against it. The stem wall does not just buy
floor. It buys *furniture wall*, and that is the difference between a room
in a dome and a tent with a dome over it.

The same band is where the heavy and rectangular things live. A door is a
rectangle; cut one in a bare shell and you are building a curved door, or
boxing a square out of a surface that slopes two ways at once. On the stem the
door is just a door, and the windows are stock units instead of specials. The
band also swallows the clutter a dome has nowhere else to put -- the water
tank, the batteries, the shelves, the coat hooks -- which would otherwise
stand off the curved wall and eat the floor the wall was bought to save.

## Why the edge is the expensive part of a dome

It is worth understanding *why* the edge is dead, because the number comes out
of one simple fact: a circle meets a flat floor at a tangent.

Headroom in this comparison means a {{pony.headroom}} foot ceiling. On a dome
{{pony.radius_ft}} feet in radius, you can stand only where the shell is at
least that high. Walk from the centre toward the wall and at some radius the
ceiling drops through {{pony.headroom}} feet and keeps going, all the way to
zero at the rim. Everything past that radius is floor with a sloping lid over
it -- geometrically fine, humanly useless.

That dead band is not a strip. It is the whole outside of the circle, and it
is where the *most* floor lives, because a circle's area lives at its outside.
It is why the dome's cheapest room is bought by moving the shell up, not by
anything you do to the frame.

The same geometry explains why the wall is cheap compared to every other way
of buying that floor back. Want the floor by making the dome wider instead?
Then the frame grows with the diameter and the skin grows with the square of
it -- every extra foot of room is bought with longer sticks *and* more skin,
which is the most expensive way there is to buy a foot. Want it by the wall?
The wall grows as a line -- one more foot of wall all the way round is a
fixed, small number of square feet of plain wall at
{{pony.wall_rate}} dollars each. The shape of the dome makes the rim the
expensive place to stand; the shape of the wall makes the rim the cheapest
place to fix.

A taller shell would do the same job, but a taller shell means a bigger frame
everywhere -- every member, every panel, the whole fortnight. The stem wall
buys the height in exactly one place: at the rim, where the room is missing.
That is the whole trick, and the ladder table is what the trick costs.

## Where the ladder stops paying

The ladder is not free forever, and its own columns say where it stops.

Look at the right-hand column. The rate climbs: {{pony.rate_2}} dollars a
foot, then {{pony.rate_3}}, then {{pony.rate_4}}. Each added foot of wall buys
less floor than the one before it -- {{pony.gain_2}} feet, then {{pony.gain_3}},
then {{pony.gain_4}} -- because the ring of new standing room gets thinner as
the ceiling profile flattens out. The wall is still cheap. It is just not as
cheap.

And past a certain height the wall stops being a free ride in a second way: it
starts acting like a real wall. A 3-foot stem is a curb. A 6-foot stem is a
cylinder the wind pushes on, one that needs its own ties into the ring, its
own sheathing, its own foundation edge. Somewhere past that you have built a
round box and set a hat on it, and you are paying for a conventional wall *and*
a dome frame on the same site.

There is also a water detail the wall introduces that a bare dome does not
have, and it belongs to the chapter on the brim (Chapter {{ch.brim_gutter}}):
where the shell meets the top of the wall there is now a horizontal seam
between two materials, and it is exactly the kind of joint water finds. The
brim throws the rain past it; without the brim, the wall is a gutter fed by
its own roof. The two chapters are one decision: the wall buys the floor, the
brim keeps the wall.

The top of the wall wants a cap, and it is the one piece of metal the rest of
the dome never asks for: a strip of flashing lapped down over the wall face and
up under the shell edge, so the end-grain of the wall's top plate is never the
thing the weather meets. It is a cheap part, and it is the part first builds
leave off, because it hides under the hat and nobody is checking.

The honest stopping point is where the next rung costs more per gained foot
than the next size of dome would. This book's own dome -- the one two trees
fill -- is {{dome.floor_sqft}} square feet for the same fortnight of work as
the {{pony.floor}} foot reference floor. If you want more than the 3-foot rung
buys, the better answer is usually not a taller wall. It is the next dome up,
where the same hundred and twenty members stand further out and the floor
comes along for free.

The wall buys back the edge of the floor you already have, for
{{pony.cost_3}} dollars, and nothing else moves. The bigger dome -- the
{{dome.diameter_ft}} foot one two trees fill -- buys that edge by buying the
room over again, spending the one thing a dome exists to save, the subject of
Chapter {{ch.less_skin}}. The wall is the answer when you are short of edge;
the bigger dome when you are short of room.

So the ladder has a last rung, and on this floor it is the 3-foot one:
{{pony.usable_3}} usable feet for {{pony.cost_3}} dollars, at
{{pony.rate_3}} dollars a foot. That is the cheapest room in the building, and
this chapter is the receipt.
