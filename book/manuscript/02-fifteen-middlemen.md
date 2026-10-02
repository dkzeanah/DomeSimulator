---
chapter: 2
title: Fifteen Middlemen
strand: explain
status: drafting
target: 3300
updated: 2026-09-17
---

# 2. Fifteen Middlemen

*Why a two-by-four costs what it costs, and how much of that is wood*

## Fifteen Middlemen

Between a standing tree and a board on a rack there are, depending on how you
slice the chain, something like fifteen separate businesses, machines, and
handoffs — and every one of them gets paid. The board does not cost what the
tree costs. The board costs what the tree costs *plus fifteen wages, fifteen
fuel bills, fifteen margins and fifteen sets of handling*, and almost none of
that is wood.

This chapter walks the chain, because the whole wedge method is a way of
skipping it, and you cannot skip something intelligently without first
knowing what it is.

The claim to hold in your head while reading it: a two-by-four's price is
mostly distance and patience. The tree spent a lifetime standing still; the
board has to be moved, processed, dried, graded, and waited on, and each of
those is a service somebody sells. The method in this book removes fourteen
of the fifteen steps — the diagram on the next page names them — and keeps
exactly one. That is not a metaphor. It is the count, and the rest of the
book is the consequence of it.

## From stump to rack

Walk it once, end to end, and count the hands.

**Fell.** Somebody drops the tree. Trained, insured, standing in the weather.

**Skid.** The trunk is dragged to a landing where a truck can reach it.

**Haul.** A log truck moves it to the mill, paid by the mile and the hour,
and the round trip is empty one way.

**Scale.** Somebody measures and grades the log, because the mill buys by
volume and quality, and the measurement is a negotiation.

**Saw.** The mill breaks it down: slabs off the round, boards out of the
cants. This is the step people picture, and it is one step of
{{route.mill_steps}}.

**Edge.** Every board gets its wany edges ripped off square.

**Trim.** Ends squared to length.

**Dry.** The boards are stickered and air-dried, or kilned — weeks to months
of time, and the kiln burns fuel.

**Plane.** The rough board is dressed to its finished size. A nominal two-by-
four has now become a dressed one-and-a-half by three-and-a-half, and the
missing wood is not an accident; it is this step.

**Grade.** Somebody looks at every board and assigns it a grade, because
graded lumber can be sold by phone and ungraded cannot.

**Bundle, ship, stock.** It is unitised, moved again, and shelved in a yard
that rents its ground, its racks and its fork trucks.

**Sell.** A desk takes an order and a margin.

That is the honest list — {{route.mill_steps}} operations between the tree
and the graded board, and every one of them has fuel, wages, rent and a
margin in it. None of them is a scam. Each one exists because the customer
for a board is a contractor forty miles from the forest who needs a
straight, dry, graded, predictable rectangle *tomorrow*, and the chain
delivers exactly that. The chain is good at its job. Its job is just mostly
not wood.

Now count the method this book uses: fell, buck, split, jig, raise —
{{route.wedge_steps}} operations from standing tree to member standing in a
frame. The middle of that list — skid, haul, scale, saw, edge, trim, dry,
plane, grade, bundle, ship, stock — is gone, not because it was unfair but
because it was unnecessary. The wedge does not need the tree to become a
rectangle, so it does not need the machinery whose entire purpose is
producing rectangles.

![Every step between a standing tree and a board on a rack.](../../deliverables/book/figures/middlemen-chain.png)

## The chain, and where the wood goes

The drawing tells the story the walk could not, because the story is not
only who gets paid. It is also what disappears.

Every processing step removes material, and the industrial chain removes it
at both ends and in the middle. The slabs and edgings off the round log. The
planer shavings off the dressed board. The trim cuts. The degrade — boards
that crack, warp or stain while drying and get down-graded or scrapped. When
the same trunk this book uses is sawn into two-by-fours, roughly
{{tree.sawn_recovery_pct}} per cent of the solid wood survives as saleable
lumber. The other {{tree.recovery_pct}} per cent of a good log — minus the
kerf — survives when it is split into wedges instead. Chapter
{{ch.recovery}} does that arithmetic in full, including the parts that are
less flattering than the headline. Here it belongs in the chain picture for
a simpler reason: the waste is not an accident of carelessness. It is the
price of the rectangle, paid in wood, at a chain of stations that each
exists to pay it.

Look at the diagram with that in mind. The industrial route is long because
each station exists to solve a problem the previous station created. The
sawmill exists to cut rectangles, so the edger exists to clean their edges,
so the planer exists to smooth them, so the kiln exists to dry them flat, so
the grader exists to sort what all of that did to the wood. The wedge route
is short because it never creates the rectangle problem. There is nothing
to edge, nothing to plane flat, and a green wedge that dries is allowed to
move a little, because the frame was designed for a stick that is already
the shape the tree made.

## The price of a 2x4, taken apart

The shelf price this book uses is {{board.price_usd}} dollars for a
sixteen-foot two-by-four — a real sticker price, declared up front in the
constants table at the front of the book, because it is a price and prices
are looked up, not derived.

Now take it apart, and the first thing to notice is how little of it is the
tree.

The tree's share of that board, at the stump, is a fraction of the sticker.
A sixteen-foot two-by-four is nominally {{board.nominal_in2}} square inches
by sixteen feet — a little under eleven board feet of wood. At a stumpage
price of a few cents a board foot standing, the wood in that board left the
forest worth pocket change, and arrived on the rack worth
{{board.price_usd}} dollars. Everything in between — the fell, the haul,
the sawing, the drying, the planing, the grading, the shipping, the yard,
the desk — is what the price actually buys. The wood is the smallest line
on the receipt.

That is not a complaint about the lumber industry. It is a measurement of
what the industry is: a logistics and processing business that happens to
have trees as its raw material. And it is the exact reason the wedge method
works economically. When you stand next to a tree that is already down,
with a saw in your hand, you are not competing with the industry's skill.
You are simply not buying its product. The {{route.mill_steps}} steps are
replaced by {{route.wedge_steps}}, and the price of the building material
collapses to fuel, chain oil, and your own hours.

Chapter {{ch.money}} does that arithmetic both ways — what the frame costs
bought, against what it costs cut — and prints the hourly rate it implies,
including the version that flatters the method least. This chapter only
needed to establish why the two numbers are so far apart. They are far
apart because one of them is a price for wood and the other is a price for
fourteen services, and the services are what the saw on your shelf makes
unnecessary.

## Nominal, dressed, and the missing third

A two-by-four is not two inches by four inches. It is sold as if it were,
and the difference matters enough that the book keeps both numbers on the
page wherever wood is counted.

**The nominal board** — the name on the ticket — is two by four:
{{board.nominal_in2}} square inches of section.

**The dressed board** — the thing you actually carry out of the yard — is
one and a half by three and a half: {{board.dressed_in2}} square inches.
The rest went to the planer.

That is a thirty-five per cent difference in section between what the
lumber is called and what it is, and it is not a trick; it is the planing
step from the chain above, made visible. The book always says which board
it means when it compares, because comparing a wedge against a nominal
two-by-four flatters the wedge by a third, and a book that flatters its own
material by accident is not worth reading. There is also a third board the
industry does not sell and the book does not pretend to: the rough-sawn
two-by-four, planer-skipped, at something between the two numbers. The
money chapter (Chapter {{ch.money}}) and the head-to-head in Chapter
{{ch.versus_board}} both state their board explicitly, and where the choice
matters they print the comparison against both.

Why the book cares this much: because the wedge's honest number — the
figure that decides whether the whole idea is worth anything — changes by
that thirty-five per cent depending on which board you compare it against.
The book's answer, stated once here and used everywhere after: compare
against the dressed board. It is what you would have bought, and it is the
smaller, less flattering target. The method is strong enough to be
measured against it.
