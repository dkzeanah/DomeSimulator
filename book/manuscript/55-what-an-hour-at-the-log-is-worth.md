---
chapter: 55
title: What an Hour at the Log Is Worth
strand: explain
status: drafting
target: 1820
updated: 2026-09-17
---

# 55. What an Hour at the Log Is Worth

*Computed three ways, including the way that flatters it least.*

## What an Hour at the Log Is Worth

This chapter is not about what timber costs. It is about what an hour of your
own time buys when you spend it on a log instead of at a till.

Those are different questions and people run them together constantly. "Lumber
is expensive" is a fact about a yard. "I can make my own" is a claim about an
afternoon. The second one only means something if you can say what the
afternoon produced, in the same units the yard uses.

So: the mill turns out {{work.struts_per_hour}} members an hour. Each member
has a cross-section of {{log.member_area}} square inches, which is a shape no
store sells. To price it, I have to say what it *replaces*, and that is where
this gets slippery, because a two-by-four is not two inches by four and the
difference is not small.

I am going to do it three ways. One of them is the number I started this
project with, and it is the highest, and it is wrong. One of them is the number
that sounds conservative and is actually the low one. The third is what I think
is honest, and it happens to sit above the conservative-sounding one -- which
is precisely the direction a reader should be suspicious about. I would be.

So here is all three, and the arithmetic in between, and then you can decide.

## One strut, valued three ways

Start with what you would actually pay to replace one member with bought wood.

A sixteen foot two-by-four is {{board.price_usd}} at the store. Cut into
{{tree.section_length_ft}} foot lengths -- the length of a member -- that is
{{log.section_price}} per section. That part is not controversial.

The controversial part is how many sections it takes to equal one strut.

A strut is {{log.member_area}} square inches in section. Divide that by what a
two-by-four gives you and you have your answer, except that a two-by-four gives
you two different things depending on which number you believe: the
{{log.nominal_area}} square inches on the label, or the {{log.dressed_area}}
square inches the board actually measures. The first says a strut replaces
{{log.equiv_nominal}} boards and is worth ${{log.value_nominal}}. The second
says {{log.equiv_dressed}} boards and ${{log.value_dressed}}. At
{{work.struts_per_hour}} members an hour that is ${{log.rate_nominal}} an hour
against ${{log.rate_dressed}} an hour.

![One strut, valued three ways, with the estimate this project started from kept in the table.](../../deliverables/book/figures/scale-strut-value.png)

Two bases, and they disagree by {{log.nominal_gap_pct}} per cent.

The third row is in the table because it is what a mill would quote you, and it
is the honest way to trade timber in volume -- but it is no use here, because a
board foot has a price only where somebody is selling one, and that price moves
with species, grade, region and week. I can tell you a member holds
{{tree.bf_per_strut}} board feet. I cannot tell you what a board foot is worth
in your county, and I am not going to make one up so that row has a number in
it.

The board-foot view does carry one number worth keeping, though, because it is
the whole harvest in one figure. Two trees of solid wood are
{{tree.solid_bf}} board feet before the saw touches them; the kerf takes
{{tree.kerf_bf}}, and the wedges that come off the split are
{{tree.wedge_bf}} -- a recovery of {{tree.recovery_pct}} per cent, which is
why the recovery chapter corrects the rounder number this project once
quoted. Every rate in this chapter is a rate on *that* volume, and the
volume is computed from the tree, not assumed.

That leaves two, and they disagree, and the disagreement is the chapter.

## Why the dressed number is the honest one

A two-by-four is not two inches by four inches. It is one and a half by three
and a half, which is {{log.dressed_area}} square inches, not
{{log.nominal_area}}. It was two by four once -- before it was dried and
planed -- and the name stuck to the rough size while the product shrank to the
finished one. Everyone in the trade knows this. Nobody outside it does.

Now think about which number belongs in a replacement calculation.

The question is: *if I did not have this strut, how many boards would I have to
buy to get the same wood?* The answer has to be in terms of what is actually in
a board, which is {{log.dressed_area}} square inches. So a strut replaces
{{log.equiv_dressed}} boards, not {{log.equiv_nominal}}, and it is worth
${{log.value_dressed}}, not ${{log.value_nominal}}.

Using the label instead of the board **understates** the strut by
{{log.nominal_gap_pct}} per cent. Which is the opposite of what you would
expect, and worth sitting with for a second, because the instinct is that the
"nominal" comparison must be the generous one -- *nominal* sounds inflated. It
is the other way round. Pretending a board is bigger than it is makes each
board look like it does more work, so you need fewer of them to match a strut,
so the strut looks worth less.

I want to be uncomfortable about this in public, because the honest correction
moved the number in my favour, and that is exactly when a writer should be
checked hardest. So here is the check: the cross-section of a member,
{{log.member_area}} square inches, is computed by the geometry, not measured by
me with a hopeful tape. The {{log.dressed_area}} figure is the actual planed
size of the board I would otherwise buy. The {{board.price_usd}} is a shelf
price. Nothing in the chain is my estimate. If the result flatters me, it is
because a wedge out of a log has more wood in it than a plank does, which is
not a surprising thing for it to have.

And that is the number the rest of this book uses: ${{log.rate_dressed}} an
hour of ripping, {{log.frame_dressed}} dollars for the whole frame.

## The shelf price is a stack

Now the part that cuts the other way.

The {{board.price_usd}} on that board is not the price of wood. It is a stack,
and only the bottom layer of it is timber. Above the timber sits the felling,
the haul to the mill, the sawing, the kiln, the planing, the grading, the
stacking, the second haul, the yard, the shrinkage, the staff, the roof over
the lumber aisle, and a margin at every hand-off.

Harvesting your own does not remove that stack. It removes *some* of it and
replaces the rest with you.

Gone: the margin, the hauls, the yard, the retail overhead. Those layers
genuinely vanish, and they are the largest part of why a bought board costs
what it does.

Still there, now done by you: the felling, the bucking, the ripping, the
stacking, the waiting. Those are the {{work.harvest_days}} days at the front of
the fortnight. You did not delete that work. You took the contract.

The two routes are countable, and the count is the stack made visible. From
standing tree to graded board on a yard's shelf is {{route.mill_steps}}
hand-offs -- felling, hauling, sawing, kiln, planing, grading, trucking,
stocking, selling, every one of them a person with a margin. From standing
tree to member in my frame is {{route.wedge_steps}}: fell, buck, split, cut,
joint. The stack is not a metaphor. It is a list, and the shorter list is why
the hour at the log is worth what this chapter says it is worth.

Never done at all: the kiln and the grading. This is the honest cost of the
method and it belongs here rather than in a footnote. A bought board is dried
to a known moisture content and stamped by somebody whose job is to say it is
what it says. A wedge off my log is green, ungraded, and going to move as it
dries -- which is a large part of why this frame is designed the way it is,
with panels that keep their own edges and a gasket between them.

So the rate is real, and it is also not a discount on a like-for-like product.
${{log.rate_dressed}} an hour buys you green, ungraded, home-milled timber of a
section nobody sells, and it is worth that much *because* of the section. It
does not buy you a kiln.

## This is not money anybody has been paid

One last thing, and it is the one I would most like to survive being quoted out
of context.

Every rate in this chapter is a **substitution value**. It is what you did not
spend. It is not what you earned.

${{log.rate_dressed}} an hour does not go in a bank. It shows up as an absence:
a trip to the yard you did not make, a line on a card that is not there. That
is a real economic good, and it is the entire argument of this part of the
book -- but it buys groceries only if you were genuinely going to buy the
timber. If the alternative to making struts was not buying struts, the rate is
zero and the hours were a hobby. A good hobby. Still zero.

Which brings me to the number I started with.

When this project began, the brief valued a strut at ${{log.brief_strut}} --
${{log.brief_rate}} an hour at this pace. It got there by taking a volume ratio
and doubling it for safety, which is a fine way to sketch and a terrible way to
publish. The honest figure is ${{log.rate_dressed}}. My own opening estimate
was **{{log.brief_over}} times** the number I can actually defend.

I have left that row in the table on purpose. It is the row I would have quoted
if nobody had made me compute it, and there is a version of this book where it
is the headline and everything downstream is {{log.brief_over}} times too
optimistic. The whole reason this book derives its figures in code is so that
row gets caught rather than repeated.

One last scale to put the rate on, because a rate is only readable next to
another rate. The median worker in this country takes home
{{wage.take_home}} dollars of an extra hour. A carpenter is paid
{{wage.carpenter}} dollars an hour. The honest number from this chapter,
{{log.rate_dressed}} dollars an hour at the log, sits between the two -- better
than the median hour, worse than a carpenter's, and all three are the same
unit, which is the only way a claim about an hour means anything. If your own
hour is worth more than the rate this chapter defends, the yard is the honest
answer and this chapter is the arithmetic of why. The rate is not a wage and it
is not a boast. It is the price of the alternative, computed, and now it has a
scale to sit on.
