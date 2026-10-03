---
chapter: 38
title: A Twenty-Dollar Pine Is Not a Twenty-Dollar Pine
strand: explain
status: draft
target: 1680
updated: 2026-10-03
---

# 38. A Twenty-Dollar Pine Is Not a Twenty-Dollar Pine

<!-- concept: pine_value/question -->

What is a pine worth? Not one price. A ladder of them, one for every use the same
tree can be put to -- and the tree does not change from rung to rung. Only what
happens to it does.

This chapter climbs the ladder for one representative pine: {{pine.length_ft}}
feet of usable stem, {{pine.butt_in}} inches at the butt and {{pine.top_in}} at
the top -- the same worked tree as Chapter {{ch.tree}}.

## What the ladder rests on

<!-- concept: pine_value/sources -->

Measured, published and the author's own figures, kept apart, because the
ladder is only as honest as its inputs:

    {{econ.pine_sources}}

## The stem, in board feet

<!-- concept: pine_value/stem -->
<!-- concept: wedge/m_trunk -->

The stem is {{pine.solid_ft3}} cubic feet of solid wood: {{pine.solid_bf}} board
feet, which is the fixed budget every method below starts from. Sold standing,
at the published stumpage price, the whole tree brings about
**${{pine.stump_usd}}**. That is the bottom rung, and it is roughly what the
chapter title calls it.

## Burned, it is heat

<!-- concept: pine_value/firewood -->

The first rung up is fire. A cord is {{pine.cord_ft3}} cubic feet stacked, but
air fills the gaps and only about {{pine.cord_solid_ft3}} of them are wood. So the
stem makes {{pine.cords}} of a cord: **${{pine.firewood_usd}}** picked up, about
${{pine.firewood_delivered_usd}} delivered. Every rung above this one has to beat
the value of the tree's heat.

## Sawn, or split

<!-- concept: pine_value/gain -->
<!-- concept: pine_value/three_trees -->
<!-- concept: pine_value/lumber -->
<!-- concept: wedge/m_radial -->

Next, lumber. A mill keeps about {{pine.mill_pct}} percent of the stem as boards,
{{pine.mill_bf}} board feet. Splitting keeps about {{pine.wedge_pct}} percent,
{{pine.wedge_bf}} -- the only wood a split loses is the width of the saw.

    split against sawn          {{pine.gain_pct}}% more usable wood
    left behind, sawn           {{pine.mill_lost_bf}} bd ft
    left behind, split          {{pine.wedge_lost_bf}} bd ft ({{pine.waste_cut_pct}}% less)
    trees sawn to match {{pine.shell_trees}} split   {{pine.trees_equiv}}

Priced as wood at a sawmill's ${{pine.usd_per_bf}} a board foot, the sawn lumber is
**${{pine.mill_usd}}** and the split wood **${{pine.wedge_usd}}**: splitting is worth
${{pine.value_gain}} more from the same tree. The mill gets the benefit of the doubt
throughout -- the simulator's own sawn recovery for this log is
{{pine.sawn_model_pct}} percent, well under the {{pine.mill_pct}} used here.

## Built, it replaces framing

<!-- concept: pine_value/use_value -->
<!-- concept: pine_value/financed -->

The next rung is not a price for wood at all. In the dome, these trees become a
shell, and the framing that shell replaces is worth ${{why.framing_value}} at
commercial rates. The frame uses {{pine.trees_consumed}} trees' worth of trunk, but
{{pine.shell_trees}} are felled, so each tree's share is **${{pine.use_usd}}**.

Most framing is not paid for in cash; it rides on a mortgage. On
{{why.mortgage_years}} years at {{why.mortgage_pct}} percent, that framing becomes
${{why.financed}} of payments, and this tree's half is **${{pine.financed_usd}}**.
Read that rung carefully: it is nominal dollars, paid monthly for decades, not
money in your hand today. But it is money a household never sends to a lender.

## The ladder

<!-- concept: pine_value/ladder -->
<!-- concept: pine_value/ratios -->
<!-- concept: pine_value/closing -->

    on the stump                 ${{pine.stump_usd}}
    burned                       ${{pine.firewood_usd}}
    sawn, as lumber              ${{pine.mill_usd}}
    split, as lumber             ${{pine.wedge_usd}}
    built into a shell           ${{pine.use_usd}}
    that framing, financed       ${{pine.financed_usd}}

As structure it is worth {{pine.fire_ratio}} times its firewood, {{pine.mill_ratio}}
times its sawn lumber and {{pine.wedge_ratio}} times its split stock. The wood did
not get better on the way up. It got used.

![One tree, every rung.](plate-pine-ladder.png)

## What the tree is worth to its owner

<!-- concept: pine_value/formula -->
<!-- concept: pine_value/honest -->

The honest figure is not the top rung. It is what the tree replaces, less what it
costs the owner to make it do so: about {{pine.hours}} hours of the owner's own
work for this tree, worth ${{pine.labor_usd}} at the author's wage, and
${{pine.cash_usd}} of cash. Net, **${{pine.net_usd}}** -- or ${{pine.net_measured_usd}}
with the fortnight's actual receipts.

What the ladder does not say: the structure rung assumes you needed the house; the
finance rung is spread over thirty years; and the author's own figures, though
marked, are an author's. The generous numbers and the ones against them are both
printed above.

## The household as the whole chain

<!-- concept: pine_value/upstream -->

This is vertical integration at the scale of one household. A commercial house
pays every hand between the stump and the wall: the logger, the hauler, the mill,
the kiln, the yard, the framer, and very often the lender. Each takes a margin, and
every margin is inside the price. This method does not make those businesses
unnecessary for everyone. It lets one owner do the few steps that matter for one
building -- and keep the margins. The next chapter counts the hands.
