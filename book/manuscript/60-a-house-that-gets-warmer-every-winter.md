---
chapter: 60
title: A House That Gets Warmer Every Winter
strand: explain
status: drafting
target: 1580
updated: 2026-09-17
---
# 60. A House That Gets Warmer Every Winter

*Build the skeleton once and add layers to it for as long as you own it: the shell ladder turns a shelter into a house in steps you can afford one at a time*

## A House That Gets Warmer Every Winter

Most houses have two states and nothing between them: finished, or unfinished.
Unfinished means tarps and regret. Finished means the whole invoice at once.

A dome shell can be neither, permanently and on purpose.

The skeleton of a dome is the frame; the frame carries the skin; and nothing
about the skin needs to be decided on the day the frame goes up. You can
stand a bare shell this autumn, quilt a first layer under it this winter, add
a second next year, and keep going for as long as you own the place. Each
step is affordable on its own, each step makes the building better, and none
of them ever requires undoing the one before.

The ladder also becomes a habit, and that is the part the table does not show.
One layer a winter is a small, repeatable job -- a weekend under the shell, the
same as splitting firewood or cleaning a chimney -- and it lands in the season
that needs it. By the time the house is fully quilted you have stopped noticing
the cold and started noticing the ritual: the first hard frost is the cue, the
layer goes up, and the house is a little warmer than the winter before. You buy
a winter at a time, in the order the cold arrives.

That is the shell ladder, and this chapter is the ladder with its prices. The
numbers are for the {{ladder.dome}} -- a {{ladder.diameter_ft}} foot dome with
{{ladder.floor}} square feet of floor -- because that is the dome the park
model computes its ladder for, and a heating number means nothing without the
building it came off.

This book's own dome is smaller than the flagship the table prices, and the
ladder scales to it the same way: the per-square-foot price holds, the total is
smaller because the shell is smaller, and the order of the rungs does not
change.

## The shell ladder, rung by rung

Each rung is one quilted layer of recycled fabric under the shell, at a
declared {{ladder.per_layer_r}} R-value and {{ladder.layer_sqft}} dollars a
square foot. The ladder runs to {{ladder.layers}} layers:

| layers | R-value | heating, $/yr | cost so far |
|---|---|---|---|
| 0 | {{ladder.r0}} | {{ladder.heat0}} | nothing |
| 1 | {{ladder.r1}} | {{ladder.heat1}} | ${{ladder.add1}} |
| 2 | {{ladder.r2}} | {{ladder.heat2}} | ${{ladder.add2}} |
| 3 | {{ladder.r3}} | {{ladder.heat3}} | ${{ladder.add3}} |
| ... | ... | ... | ... |
| 7 | {{ladder.r7}} | {{ladder.heat7}} | ${{ladder.add7}} |

Read the first and last rows. The bare shell is R-{{ladder.r0}} and it wants
{{ladder.heat0}} dollars a year to stay warm. The same shell with all
{{ladder.layers}} layers is R-{{ladder.r7}} and wants {{ladder.heat7}} dollars
a year. The layers removed {{ladder.drop_pct}} per cent of the heating bill,
and they cost {{ladder.add7}} dollars spread over however many winters it
took you to add them.

The point of the ladder is not the top row. It is that there *is* a ladder.
Every rung exists on its own: one layer is a real improvement, not a down
payment on seven. You buy the rung you can afford, in the winter you can
afford it, and the house is warmer than it was the winter before.

It is also worth noticing what the ladder is made of, because it matters
that it works at all. These are not batts stuffed between studs. A quilted
layer is a continuous sheet hanging under the whole shell, and continuity is
the difference: a stud wall insulates between the studs and conducts through
every one of them, so its *assembly* R-value is well below its cavity
number, while the quilt has no studs in it to bridge. The shell frame is the
same story -- the struts touch the skin at the seams, but the quilt covers
them too, on the inside, in one unbroken layer. That is the quiet reason a
ladder of cheap fabric layers does what the table says it does.

The quilt is worth one more sentence for what it is made of, because it changes
the price. It is recycled fabric -- clothing and bedding that left the waste
stream and came back as insulation -- so the {{ladder.layer_sqft}} dollars a
square foot is not the cost of a manufactured foam product. It is paying
somebody to shred, clean and stitch what a city was throwing away. The ladder
adds a thickness of second-hand fabric to a frame that was already second-hand
timber.

## Why the bones are the thing to get right

Every layer in that ladder attaches to the same thing: the frame. The quilt
hangs from the struts, the seams key into the panel edges, the inner lining
screws to the members. There is no layer that does not touch the skeleton.

That is why the frame is the one part of the building worth being fanatical
about, and it is the cheapest time to be fanatical about it. If the frame is
straight, every later rung has something straight to land on, and nothing is
ever blocked. If the frame is wrong, the error does not stay in the frame. It
walks up the ladder with you: the quilt puckers over a twisted strut, the
lining opens a gap at a seam that never quite closed, and the tenth winter
you are still paying to heat the mistake you made on day five.

There is a second reason the bones matter, and it is the one the marketing
never says. The ladder's arithmetic prices *conduction* -- heat moving
through the shell material. It does not price airtightness. Airtightness is
not bought with layers; it is built into the frame, in a continuous shell
with no corners to leak and seams you made yourself. That is the shell's job,
not the quilt's. A leaky dome with seven layers is a quilted leak. This book
has not metered a winter in one, and the chapter that closes this part
(Chapter {{ch.honest_limits}}) says exactly which energy claim it will not
make and why.

## The rung that pays back fastest

Now rank the rungs, because they are not equal and the order surprises
people.

The first layer is the best buy in the building. It costs
{{ladder.layer_cost}} dollars and it saves {{ladder.save1}} dollars in the
first year alone -- it pays for itself in {{ladder.payback1}} months, and
everything after that is free. No other rung does that.

The second layer costs the same {{ladder.layer_cost}} dollars and saves
{{ladder.save2}} dollars a year. Still good, but the layer that took
{{ladder.payback1}} months to repay now takes years, because each layer of
insulation removes a smaller share of what is left.

The third saves {{ladder.save3}} dollars a year. The fourth, fifth and sixth
continue the same slide, and the seventh saves {{ladder.save7}} dollars a
year on its {{ladder.layer_cost}} dollar cost -- a payback of
{{ladder.payback7}} years, which is most of a mortgage.

That slide is not a failure of the ladder. It is the physics of insulation,
and it is the same in every building: the first inch does the most work, and
every inch after it works on the smaller leak that is left. What the ladder
buys you is the *option* to stop exactly where your winters say to stop. A
mild climate might own the first two layers and never miss the rest. A hard
one buys all seven and the top rungs still make sense there, because a cold
climate's heating bill is big enough that even {{ladder.save7}} dollars a
year compounds over the thirty years of a maintained dome.

There is one more column the table cannot show, and it is the reason the
ladder beats a one-time insulation purchase in this particular building.
Every layer attaches *after* the shell is up and *after* you have lived in
it, so every rung is bought with information the first rung did not have --
which walls are cold, which windows sweat, which winter hurt. A conventional
house makes its one insulation decision before the walls are closed, on
guesswork. The ladder makes seven smaller decisions, each one with a year of
living in the house behind it. That is what "warmer every winter" actually
means: not a promise about the weather, but a building that lets you keep
paying for warmth in the order your own experience says to.

A one-time foam purchase is the other way, and it is the way a conventional
house has to take. Foam is bought once, sprayed once, and sealed behind a wall
the same day; if it was the wrong thickness, or it shrank, or a seam opened,
you will not know until the bills are in, and you cannot reach it to fix it.
The quilt is the opposite: it hangs where you can see it, it comes down in the
same layer it went up, and a bad layer is a morning's work to replace. The
ladder's rival was never the foam itself. It was the single invoice.

So the honest ranking is: the first layer pays back fastest, by an enormous
margin, and it is rarely the one people do first. People paint the inside.
They buy a wood stove, which is a lovely thing and does nothing to the
envelope. They build a porch. The layer that returns {{ladder.save1}} dollars
a year on {{ladder.layer_cost}} dollars waits, because a quilt hanging under
a shell is not something anybody has ever been proud of at a party.

That is the argument for the ladder, stated plainly: the house gets warmer
every winter, one rung at a time, in the order your money allows -- and the
first rung is the best one, so even a broke first winter is a good winter to
start.
