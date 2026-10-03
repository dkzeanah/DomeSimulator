---
chapter: 80
title: The Boat-Hull Shell
strand: explain
status: drafting
target: 2120
updated: 2026-09-17
---

# 80. The Boat-Hull Shell

*Four ways to skin the dome, priced by the pound of glass and resin each one puts on: the hard shell as the fifty-year upgrade over the cap*

## The Boat-Hull Shell

The cap keeps the weather off. A hull *becomes* the weather
— one structural skin, laminated over the frame, that sheds
water, carries its own loads and refuses to come off. Four
systems build one, and their prices disagree on purpose:
each system buys a different number of years for a different
number of pounds, and the chapter's job is to make the
disagreement readable.

The hull is in this book as the fifty-year option — the
upgrade the cap of Chapter {{ch.stacking_hats}} deliberately
defers. The cap's whole argument is that the hard shell can
wait; this chapter is the hard shell, priced, weighed, and
sliced so that when the waiting is over the choice is a
comparison instead of a guess.

## Four ways to skin it

The four systems, each priced and weighed on the same dome,
with the honest note about what the prices rest on.

**Sheathed plywood.** Sheets over the frame, seams taped,
painted. The cheapest hull, the heaviest per pound of
weather protection, and the shortest life — a wooden skin
that needs its paint on schedule. It is the hull for the
builder who wants the dome closed *now* and upgraded later.

**Boatyard polyester.** Fibreglass cloth over a plywood or
foam core, wet out with the polyester resin the boat-repair
trade uses every day. The workhorse hull: familiar
materials, forgiving process, decades of life, and the price
per square foot the campaign quotes as its middle system.

**Premium marine.** Epoxy instead of polyester, better cloth,
better bonds — the hull for a dome that will be a *home*,
where the skin's life and the frame's life should match and
the cost difference is spread over fifty years.

**Vinyl ester.** The premium's premium: the resin class that
resists water absorption best, chosen where the skin sits
wet or the budget simply wants the longest interval between
decisions.

The prices the chapter quotes are the campaign's own,
computed from the shell's square footage and the glass-and-
resin weights each system puts on — and the honest note,
kept because the film that discovered it kept it: the
weights are hand-layup ratios, the prices rest on declared
material costs, and a real hull's final number is the
builder's own lamination quality. The table ranks the
systems; the quality decides the years.

![Four ways to skin it, and what each one costs.](../../deliverables/book/figures/hull-skins.png)

## Slices instead of a monolith

The one design decision that makes the hull an upgrade path
instead of a commitment: the shell is built in slices.

A one-piece hull can never come off — it is the building,
and every later change is surgery on the building. Four
slices with an S-shaped lip between them can: each slice
unbolts at its lip, the roof comes apart too, and the hull
that was the standard article becomes a *set* of
replaceable panels — the same panel logic the frame was
built on, carried out to the skin. The campaign's numbers
put the slice's cost against the monolith's and the
difference is small; what it buys is the stem cell's
deferral, one layer further out. A slice can be repaired
alone, upgraded alone, and carried to the next dome alone —
which is what turns a fifty-year skin into fifty small
decisions instead of one large one.

## Which one to pick

The ranking, stated without romance.

The cheapest hull is not the cheapest to own — plywood
needs its paint, and paint is a subscription. The premium
hull is a fifty-year decision the cap lets you defer, and
deferral is the book's whole method: build the cap, live a
winter, and let the dome's own behaviour tell you whether
the hull is ever needed — and if it is, which system the
site's weather actually earns. The chapter's last sentence
is the cap chapter's first, closed into a loop: **the hard
shell is the upgrade you buy after the soft one has taught
you what you need.** The hull is waiting. The cap is
working. And the four systems above are the comparison for
the day the waiting ends.

## The four systems, priced and weighed

The chapter has described the schedules. Here is what the model says they cost
and what they weigh on this shell's own core — {{hull.core_sqft}} square feet
of it, {{hull.core_sheets}} sheets, {{hull.core_lb}} pounds of core before
anything is wet out, held down by {{hull.latches}} latches and
{{hull.rim_gasket_ft}} feet of rim gasket.

| system | what it is | total | resin | laminate weight |
|---|---|---|---|---|
| Sheathed ply | light cloth in epoxy, both faces | {{hull.sheathed_usd}} | {{hull.resin_gal_min}} gal | {{hull.weight_min_lb}} lb |
| Boatyard polyester | mat, then stitched biaxial, gelcoat | {{hull.boatyard_usd}} | {{hull.resin_gal_max}} gal | {{hull.weight_max_lb}} lb |
| Marine polyester | the same schedule, better resin | {{hull.marine_usd}} | {{hull.resin_gal_max}} gal | {{hull.weight_max_lb}} lb |
| Vinyl ester | the below-the-waterline schedule | {{hull.vinylester_usd}} | {{hull.resin_gal_max}} gal | {{hull.weight_max_lb}} lb |

Four systems, {{hull.min_usd}} to {{hull.max_usd}} — a spread of
{{hull.spread_usd}} — and a weight spread of {{hull.weight_ratio}} times
between the lightest and the heaviest. Read that next to the chapter above and
the choice stops being a matter of taste:

**The cheapest schedule is also the lightest, by a wide margin.** Sheathed ply
is cloth and epoxy over the core: {{hull.weight_min_lb}} pounds, the system a
boatbuilder would use on a dinghy. It seals the wood and takes abrasion, with
the most expensive resin on the list used in the smallest quantity —
{{hull.resin_gal_min}} gallons against {{hull.resin_gal_max}}.

**The production schedule is the heavy one.** Mat as a bond coat, stitched
biaxial over it, gelcoat on the weather face: {{hull.weight_max_lb}} pounds,
{{hull.weight_ratio}} times the sheathed laminate, for the middle price on the
board. It is bought for that weathered face — the gelcoat at
{{hull.gelcoat_usd}} is what lets a hull survive ultraviolet light — and the
weight is what the protection weighs.

**Vinyl ester is bought for water rather than for strength.** It is the
dearest schedule at {{hull.vinylester_usd}}, and the reason is on the label: it
is what goes below the waterline on a boat expected to stay there. For a shell
that lives outdoors that is exactly the argument — and the chapter's honest
note is that it is also an argument the *cap* makes for {{hull.min_usd}} by
keeping the water off the shell altogether. The cheap laminate and the soft
cap are competing answers to the same question, and the cap is the one you can
try first.

The wet-out area is {{hull.laminated_sqft}} square feet once inner face, outer
face and skirt are counted, against {{hull.core_sqft}} square feet of core.
That difference is why laminating is priced by the pound of glass and resin
rather than by the sheet of plywood: every square foot of this shell gets
covered twice, and the model bills it that way.
