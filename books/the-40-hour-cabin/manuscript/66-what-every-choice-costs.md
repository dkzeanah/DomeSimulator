---
chapter: 66
title: What Every Choice Costs
strand: explain
status: draft
target: 2660
updated: 2026-10-05
---

# 66. What Every Choice Costs

Chapter {{ch.twelve}} walked the catalogue one building at a time. This
chapter turns it sideways: hold one design still, move one menu at a time, and
find out which choices actually cost money, where the hours go, what the
furniture adds, and how many different domes the menus can make between them.

## What is declared, and what is measured

<!-- concept: all_domes/inputs -->

Before any dollar figure, where the dollars come from:

    {{cat.w_inputs}}

The densities and unit prices live in one file in the project. They are
declared inputs, and they are the only numbers in this chapter typed by a
person. Every quantity they are multiplied by -- areas, lengths, counts,
weights -- is measured off the model that drew the building. Change a price in
that file and every figure below moves with it; nobody edits a sentence.

## Which menu is the expensive one

<!-- concept: all_domes/math_price -->
<!-- concept: world/cladding -->

Start from the {{cat.d00_name}} at ${{cat.d00_usd}} and price every setting
of one menu at a time:

    {{cat.w_price}}

The covering and the frame material swing the price by tens of thousands. The
geometry barely moves it. Some menus cost nothing at all. That is the
catalogue's own verdict on itself, and it is good news: **the skin decides the
price**, and the skin is the decision you can defer, stage or upgrade later.
The frames across the catalogue are close cousins; the cladding -- plywood,
glass, canvas, polycarbonate, composite tile, poured concrete -- is not.

![Which menu is the expensive one.](plate-menu-price.png)

## Six ways to frame one shell

<!-- concept: all_domes/math_styles -->

The same workshop shell, framed every way the tool knows:

    {{cat.w_styles}}

:::box correction
**The tool argues with itself here, and it is said out loud rather than
averaged away.** Two of the six framing styles report hub connectors in their
bill of materials that their own assembly never fits. The picture and the
price disagree. The picture is the one to believe, because the picture *is*
the assembly -- so read those two totals as high by their hub line.
:::

## Where the hours go

<!-- concept: all_domes/math_build -->

The tool records an estimated time for every step of every build, and grouped
by phase they say something useful:

    {{cat.w_build}}

The frame -- the part everybody pictures when they imagine building a dome --
is not the expensive phase in hours. The sheathing is. That is a model and not
a stopwatch, and it is a different building from this book's forty-hour frame:
an estimate attached to each work step. But it is the same estimate applied to
every design, so comparing two designs is fair even where the absolute number
is soft.

## The dome is the cheap part of the dome

<!-- concept: all_domes/math_fitout -->

Every design ships furnished, and some with framed walls and plumbing:

    {{cat.w_fitout}}

:::box against
**The shape saves you on envelope. It does not save you on anything that plugs
in.** On a design whose shell is split logs and plywood, the equipment, the
walls and the plumbing are a serious share of the building. And the
electrical line reads zero not because domes need no wiring, but because no
preset ships with a battery or a charge controller for the conduit to start
from. Add them, and the model routes the runs without being asked twice.
:::

## Size is a number you type

<!-- concept: all_domes/frequency -->
<!-- concept: all_domes/math_dials -->
<!-- concept: world/scale -->
<!-- concept: world/math_scale -->

Frequency is the one menu that changes how many pieces there are. Same
radius, same material, same foundation, and only the number of times each
face is divided:

    {{cat.w_frequency}}

Frequency buys a smoother shell and charges in part variety, which is what
actually slows a build down.

The tool's sliders look continuous. They are not: each one moves in fixed
steps written into the menu code, so they can be counted like the drop-downs
can, and **not one of them changes the part count**:

    {{cat.w_dials}}

Which is the whole economic argument for this shape, proved on the catalogue:

    {{cat.w_scale}}

Part counts depend on frequency alone, never on size. The largest dome in the
catalogue has several times the floor of the smallest, off an identical list
of operations. Load a preset, drag the radius slider, and watch the counts
stay exactly where they were.

## How many domes that is

<!-- concept: all_domes/math_permutations -->
<!-- concept: all_domes/random -->

Multiply the menus:

    {{cat.w_perms}}

Then the honest deduction, because some settings do nothing in some
combinations -- a hub style changes nothing on a frame with no hubs -- and
count only the shells that genuinely differ: **{{cat.distinct}}**. At three
seconds each, showing every one would take {{cat.years}} years of film.

![How many domes that is.](plate-permutations.png)

So here are eight the dice picked instead, drawn at random from the menus,
built and priced, with the seed fixed so anyone can draw the same eight:

    {{cat.w_random}}

Some of them are sensible. At least one is a thing nobody would ever build,
which is the honest shape of a space this large.

![Eight the dice picked.](plate-dice-domes.png)

## Ten builds, one ledger

<!-- concept: world_chatgpt/cg_costs_math -->
<!-- concept: world_chatgpt/cg_tradeoffs -->

Last, ten of the designs carried all the way through: the Dome Creator's bill
of materials, the hours in its build record, and the assembly-line economics
that turn both into a planning price.

    {{cat.w_production}}

The lowest price and the least labour can be different winners, which is why
a product decision cannot be made from one number.

![Ten builds, one production ledger.](plate-production-ledger.png)

:::box against
**None of these numbers is a bid.** A dome does not make the difficult parts
of housing disappear. Curved walls complicate ordinary cabinets and openings.
An unfamiliar system can slow permits, insurance and appraisal. Freight and
site work can dominate a remote job. Every occupied structure still needs
local structural engineering and code review. Those costs are not folded
quietly into the totals above. They are outside them, and this box is here to
say so.
:::
