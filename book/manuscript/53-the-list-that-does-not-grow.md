---
chapter: 53
title: The List That Does Not Grow
strand: explain
status: drafting
target: 2300
updated: 2026-09-17
---

# 53. The List That Does Not Grow

*Every count stays put. Only the stick moves.*

## What actually changes when a dome gets bigger

Here is the thing I could not get anybody to say out loud when I started, and
the reason I ended up building a dome instead of a shed.

When you make a building bigger, you expect to buy more of everything. More
timber, more brackets, more screws, more days. That is how a box works. Double
the floor and you roughly double the walls, the studs, the sheets, the cuts,
the money, the weekends.

A dome does not do that. Not mostly. Not approximately. It does not do it
*at all* for the parts list, and once you see that number you cannot unsee it.

And nobody in the building trade has any reason to say it out loud. The
shed-and-extension business runs on the opposite sentence -- more building,
more everything -- because for a rectangular frame the sentence is true, and
stating the dome's exception does not sell anything anybody in that trade is
selling. So the fact sits unspoken, in the columns of a table nobody prints,
and the person who finds it is the person who sat down and wrote the table.
That is what this chapter is: the table, printed.

I built a frame out of a hundred and twenty members. That frame is
{{flat.struts}} struts. It is also {{flat.triangles}} triangles, held at the
corners by {{flat.brackets}} brackets and about {{flat.screws}} screws. The
shop work is {{flat.processes}} distinct processes -- measuring, cutting,
drilling, folding brackets, and so on down the list.

Now make the dome three times as wide.

## The same list, four times

I ran the same frame at four diameters, from a {{flat.small_ft}} foot dome to a
{{flat.large_ft}} foot one. This is the table, and every number in it comes off
the same model the films use:

| across | floor | triangles | struts | brackets | screws | processes | timber |
|---|---|---|---|---|---|---|---|
| {{flat.small_ft}} ft | {{flat.small_floor}} sq ft | {{flat.triangles}} | {{flat.struts}} | {{flat.brackets}} | {{flat.screws}} | {{flat.processes}} | {{flat.small_stick}} ft |
| {{flat.mid_ft}} ft | {{flat.mid_floor}} sq ft | {{flat.triangles}} | {{flat.struts}} | {{flat.brackets}} | {{flat.screws}} | {{flat.processes}} | {{flat.mid_stick}} ft |
| {{flat.large_ft}} ft | {{flat.large_floor}} sq ft | {{flat.triangles}} | {{flat.struts}} | {{flat.brackets}} | {{flat.screws}} | {{flat.processes}} | {{flat.large_stick}} ft |

Look down the middle of that table. Six of the eight columns do not move. Not
by one. The same {{flat.triangles}} triangles, the same {{flat.struts}} struts,
the same {{flat.brackets}} brackets, the same {{flat.screws}} screws, the same
{{flat.processes}} processes, whether the thing on the ground is a garden pod or
a building you could put a second floor in.

Only two columns move, and both of them are the same material measured two
ways: the floor you get, and the timber you have to stand up to get it.

![Three lines: the floor rises as the square, the stick as a line, and the parts list does not rise at all.](../../deliverables/book/figures/flat-rate-curves.png)

The chart is the table, drawn. The floor line climbs like a square. The stick
line climbs like a straight line. And the parts line is not a line at all -- it
is a floor, flat, because there is nothing in it to climb with. When the three
are put on the same axes, the flat one stops being a row in a table and becomes
the thing that is visibly *not happening* while the other two race.

## One grows as the square, one as a line

This is the whole engine of the idea, so it is worth doing the arithmetic
slowly.

Floor area goes as the square of the diameter. That is not a dome fact, that is
a circle fact, and it is the reason a twelve inch pizza is not twice a six inch
pizza. Three times the diameter is nine times the floor: {{flat.small_floor}}
square feet becomes {{flat.large_floor}}. Nine times the room.

The frame to hold it goes as the diameter, straight line. Every edge in the
dome is a fixed fraction of the radius, so three times the diameter is three
times the edge network: {{flat.small_stick}} feet becomes
{{flat.large_stick}} feet, a ratio of {{flat.edge_ratio}}, exactly.

Put those two sentences next to each other and something has to give, and what
gives is the amount of material standing between you and each square foot of
floor. At {{flat.small_ft}} feet across it takes {{flat.small_per_floor}} feet
of timber to enclose one square foot. At {{flat.large_ft}} feet across it takes
{{flat.large_per_floor}}.

The same timber, doing {{flat.edge_ratio}} times as much enclosing, because it
is stood further out and the shape is doing the work instead of the material.

That is the whole thing. Everything else in this part of the book is that
sentence being spent.

## What is flat, and what quietly is not

Three things in that table are not flat, and I would rather say them here than
have you find them out with a load of timber already on the ground.

The timber grows with the diameter. That is a line, not a flat, and at some
point it is real money. Three times the diameter is three times the frame.
You are still far ahead, because you got nine times the floor for it, but you
did buy more wood.

The *cut* timber grows slightly faster than that, and this one caught me out.
The edge network is exactly linear -- {{flat.edge_ratio}} times the edges for
three times the diameter. But a member is not its edge. The pinwheel insets
every member from the vertex, and the inset is set by how wide the stick is,
which does not change when the dome does. So a small dome throws proportionally
more of its edge network away in vertex gaps. Counted in members actually
standing in the frame, {{flat.small_cut}} feet becomes {{flat.large_cut}} --
a ratio of {{flat.cut_ratio}}, not {{flat.edge_ratio}}.

It moves the headline, so here is the honest version of it. Per square foot of
floor, cut member drops from {{flat.small_per_cut}} feet at
{{flat.small_ft}} feet across to {{flat.large_per_cut}} feet at
{{flat.large_ft}}. That is still the whole argument -- the same timber doing
{{flat.cut_gain}} times as much enclosing -- it is just {{flat.cut_gain}} and
not {{flat.edge_ratio}}. I would rather print the smaller true number than the
larger clean one.

The inset that causes the correction is not an accident of the drawing. It is
the pinwheel itself (Chapter {{ch.pinwheel}}): members lap past each other at
the vertices instead of butting into them, and a member that laps must start
short of the vertex it is lapping. The gap is what lets the whole frame close
without a single member being cut to an impossible tolerance. The same design
that makes the frame forgiving is the one that makes the cut list grow a
little faster than the edge network -- the two facts are the same fact, seen
from the saw and from the table.

The skin grows with the square. Whatever you cover the frame with -- panels,
shingles, greenhouse film, glass -- is priced by area, and area is going as the
square. So the *frame* is the flat part of a dome. The *envelope* is not. If
somebody tells you the whole building scales flat, they have counted the
skeleton and forgotten the skin.

Everything else in the table holds. The count of pieces. The count of
operations. The number of times you set the saw. The number of corners you have
to get right. The number of ways the job can go wrong. If you can build the
small one you can build the large one, because it is the same job with longer
sticks in it. That is not a slogan, it is what is in the columns.

## The limit is my arms, not the arithmetic

There is a ceiling on this, and it is worth being exact about where it comes
from, because it is not where people expect.

It is not that the geometry gives out. It is that **I have to pick the stick
up.**

I set my longest member at {{flat.solo_member_ft}} feet. That is a declared
number, not a solved one -- it is the most I want to handle as a solo builder.
The most I want to carry across a yard, stand both ends of, hold square while I
drive the first screw, and set into a triangle with nobody there to take the
other end. And I am pushing it at that. Six feet of green timber is not a light
thing.

Even at six feet I am not muscling the frame up. I run overhead cabling in the
trees and hang a winch off it, and the assembled triangles go up on the cable.
The limit is on the stick in my hands, not on the lift. If it were on the lift
I would just buy a bigger winch.

Now, how big a dome is that? This is worth doing carefully, because the obvious
way to work it out is wrong.

A pinwheel frame does not run its members corner to corner. Each one is inset
from the vertex so the next one can lap past it, and how far it is inset depends
on how *wide* the member is -- which does not change when the dome does. So the
stick you pick up is always shorter than the edge it spans, and by a different
amount at every diameter. At the top of my band a
{{flat.solo_member_ft}} foot member is spanning an edge of
{{flat.solo_chord}} feet. Multiply a chord factor and you will size the dome
too small and never know why.

Solved properly, a {{flat.solo_member_ft}} foot cut member is a dome
**{{flat.solo_dome_ft}} feet across** -- {{flat.solo_floor}} square feet of
floor, with {{flat.solo_short_ft}} feet as the other stick. And here is what
that does to the table:

| across | longest stick you cut | can one person set it? |
|---|---|---|
| {{flat.small_ft}} ft | {{flat.small_long}} ft | comfortably |
| {{flat.mid_ft}} ft | {{flat.mid_long}} ft | yes, with {{flat.mid_spare_in}} inches to spare |
| **{{flat.solo_dome_ft}} ft** | **{{flat.solo_member_ft}}.00 ft** | **exactly at the limit** |
| {{flat.large_ft}} ft | {{flat.large_long}} ft | no -- {{flat.large_over_ft}} ft too long |

![Member length against diameter, with the declared handling limit crossing it.](../../deliverables/book/figures/solo-band.png)

The figure draws the crossing: member length climbing with diameter, and the
flat line of my arms cutting across it. Everything under the crossing is one
person's building. Everything over it is a crew's. The band is not a soft
preference -- it is where the line crosses the curve, and the curve is solved
geometry.

That puts {{flat.band_inside}} of the four sizes in this chapter inside the
band. The twenty foot dome -- a room you can live in -- has half a foot of
margin on its longest stick. Only the thirty foot one is out, and it is not
marginally out: it is {{flat.large_over_ft}} feet out.

The band also answers the question a buyer never thinks to ask but should:
*which* size? If the work is the same fortnight and the list is the same
list, the size is the one decision on the table that is free -- and a free
decision is the one worth making last, when you know what the dome is for.
Pick the floor you need, and everything else follows it; pick wrong and the
correction is not a new list, it is a longer stick in the same frame. There
are not many purchases where the expensive part is choosing and the choosing
is free. This is one of them.

And there is a coincidence in that table which is not a coincidence at all.
{{flat.solo_dome_ft}} feet is the dome this entire book is built around: the one
two trees yield. It was never sized for my arms. It was sized by the log --
{{flat.solo_member_ft}} foot sections out of a trunk, because that is what a
trunk gives you before the taper beats you. The biggest dome one person can
frame alone and the biggest dome two trees will fill turn out to be the same
dome, to the inch, and I did not arrange that.

## Inside the band, nothing changes at all

Here is the part I want to be loud about, because it is the useful half.

**Anything smaller is basically the same effort.** Not proportionally less --
the *same*. Same assembly pattern. Same hardware numbers. Same operations. Same
preparation of every strut: same cuts, same jig, same bevels, same holes in the
same places. A ten foot dome and a twenty foot dome are the same fortnight of
work; one of them just has shorter offcuts.

So the flat rate is not a claim about all possible domes. It is a claim about
the domes I can actually build, and inside that band it is not approximately
flat, it is flat. That band happens to run from a garden pod up to a room you
could live in, which is most of what a person wants.

Past the band you have two honest options and no third one. Buy help -- a
second pair of hands changes the arithmetic of what a member can be. Or raise
the frequency, which splits every edge again and gives you shorter sticks for
the same diameter. That second one works, and it is the standard answer, but be
clear about what it costs: a 3V frame is 165 members where this one is
{{flat.struts}}. (That 165 is the standard geodesic count, not something this
book has solved -- I have not built a 3V frame, and the chapter on frequency
prints dashes where its member lengths would go, on purpose.) **Raising the
frequency is the one move that actually makes the list grow.** The list is flat
across diameter. It is not flat across frequency.

## Solve it once

The other thing the table does not show is what happens the second time.

Every count in it is a count of things you have to *figure out* exactly once.
The jig gets set up once. The bracket fold gets worked out once. The order you
raise the triangles in gets discovered once, usually the hard way, usually in
the wrong order. The first dome is where you pay for all of that, and it is
expensive in the only currency that matters, which is weekends.

Then it is done. It does not come back. The second dome is the same hundred and
twenty members and the same nine processes, except now you know them, and the
only thing that can differ is how fast you move. Every build after the first is
just **better timing than the first** -- and better timing is always a win.
There is no version of the second one that is harder than the first.

There is a second, less obvious way the first dome pays for itself, and it is
the one that matters on a site. The first dome is the *proof*. The jig you set
up once is a jig that demonstrably makes a frame that stands; the fold you
worked out once is a fold that demonstrably held a winter. Every count in the
table is a count you no longer have to believe, because you have watched it
close. The second dome is not just faster -- it is *safer*, in the specific
sense that its unknowns are the ones you already met and survived. The first
build de-risks the second, and the second de-risks the tenth, and the list
being the same is what lets the risk stay retired instead of being re-hired at
every diameter.

That is why I count in pieces and operations instead of in dollars. Dollars
recur. A problem you solved does not.

## Why it is worth counting this way

The number everybody actually feels is not the price of timber. It is the
number of Saturdays.

A hundred and twenty members is a fortnight of cutting whether the dome is ten
feet across or twenty. That is not a discount on a big building -- it is the
same building, and the size comes along for free with the corners you were
already going to cut. My time did not get cheaper. But the floor it produced
did, and it produced more of it.

Counting in pieces also does one thing dollars cannot: it makes the claim
*falsifiable*. A price moves with the market and the month, so a cost claim can
be argued with forever and never settled. A count is either {{flat.struts}} or
it is not, and anybody can stand in the frame and count. That is why this part
of the book leans on tables instead of adjectives -- and it is why the table in
this chapter has four diameters on it, so the flat row is not asserted, it is
shown, and the row that is not flat is shown next to it. The number that flatters
the argument gets printed beside the number that does not, because a flat-rate
claim with the skin and the stick left in is a claim you can check, and a claim
you can check is the only kind worth making about a building.

And there is a last way to see it, the one a builder's own body already knows.
An hour of labour is an hour of labour. It costs the same whether the hour
raised a ten foot dome or a twenty foot one, because the hour does not know
what it built -- it only knows the motions, and the motions are the same. So
the *price* of the building falls as the floor grows, not because anything got
cheaper, but because the same priced hours were aimed at a bigger target and
hit more of it. The flat rate is not a cheaper building method. It is the same
building method with the size as the free variable, and the size being free is
what makes the next dome the obvious thing to want.

That is the flat rate. Everything after this chapter in this part of the book
is the same fact, applied somewhere else.
