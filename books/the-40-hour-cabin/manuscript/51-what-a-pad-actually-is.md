---
chapter: 51
title: What a Pad Actually Is
strand: explain
status: draft
target: 2140
updated: 2026-10-05
---

# 51. What a Pad Actually Is

<!-- concept: byod/title -->
<!-- concept: dome_park/pad_detail -->
<!-- concept: byod_deepseek/arrive -->
<!-- concept: byod_deepseek/pad_build -->
<!-- concept: byod_deepseek/decks -->

Chapter {{ch.network}} argued for a network of pads. This chapter is about one
of them: what it is made of, who owns which part, and why the part the house
stands on is the part the house never has to bring.

Start with graded ground. On it goes a deck -- gravel, concrete or timber,
whichever the host wants to pay for. Round the edge of the deck runs a rim,
and the rim is the part that makes this a pad rather than a patio: it is what
a dome latches to. Then power, water and drain arrive, in the middle. At the
edge, a metered pedestal, which is how the host sells the power and water on.
If the host wants to, a utility column in the middle with a sink, a shower
head, a toilet and outlets on it.

That is all of it. Look at the list, because it is short:

- a deck;
- a rim;
- three pipes and a conduit;
- a pedestal with a meter in it;
- perhaps a column, perhaps a turning ring.

There is no kitchen on that list. No sofa, no carpet, no bathroom fittings
somebody else chose. The host's asset is a piece of civil engineering, and the
thing most likely to damage it is the weather.

![Everything the host is responsible for.](plate-pad-detail.png)

The cheapest version that is still a serviced pad is not poured at all: a
framed deck on precast blocks, with one power panel and water manifold in the
middle of four pads instead of a pedestal and a trench for each. Nothing
excavated. Chapter {{ch.host}} prices it, line by line.

## The reserved spot

<!-- concept: byod/center -->
<!-- concept: byod_deepseek/center -->
<!-- concept: byod_deepseek/channels -->
<!-- concept: byod_deepseek/veins -->

Every builder knows to reserve the middle of a floor for the services, and
this system makes that a rule rather than a habit. Power, water and drain come
up **inside the footprint, in the centre**.

Centre, not edge, for a plain reason: the dome that lands here puts its floor
on the pad. Services arriving at the edge would have to cross the doorway, or
come up through a wall that is not there yet, or be moved every time a
different house arrives. From the centre they go up the utility column, and
from the column they go out along the shell.

That second leg is where the wedge dome earns something. Its seams are
channels -- Chapter {{ch.channel}} measured what fits in them -- and those
channels connect round the whole shell. Supply lines and wiring can run up
from the centre and then out along the seams like veins, latched in place and
still reachable when something has to change. Drainage stays down at the
floor, where gravity wants it.

The result is a house whose rooms can be rearranged around a fixed service
point instead of being redesigned every time the household changes. Chapter
{{ch.tenant}} is about what that buys.

![The reserved spot: services up the middle.](plate-reserved-spot.png)

## Sizes are rounded up, not invented

<!-- concept: byod_deepseek/catalog -->
<!-- concept: byod_deepseek/iris -->

A pad catalogue could be a marketing table. This one is arithmetic. Every
design the Dome Creator ships has a foundation diameter the tool computes from
its own geometry. Round each one up to the next {{tt_pad.step}} feet and you
have the pad sizes:

    {{pad.fit}}

Four-foot steps, because decking and ring stock come in even lengths, and
because the second pad a host builds wants the first one's cut list. Add a
bigger dome to the tool and a bigger pad size appears on the next run; nobody
edits a list.

But one pad does not have to be one size. The rim can be an **iris**: leaves
on a track that open and close like a camera's aperture, so one pad takes a
{{tt_iris.min}}-foot dome or a {{tt_iris.max}}-foot one without being rebuilt.
The deck stays where it is; only the acceptor changes size. That spans all
three of the domes this system is planned around -- {{tt_iris.small_ft}},
{{tt_iris.mid_ft}} and {{tt_iris.large_ft}} feet across.

It is not cheap. The mechanism is about ${{tt_iris.cost_max}} at full
aperture. Against three fixed pads, one per size -- ${{tt_iris.three_pads}} --
one iris pad at ${{tt_iris.one_pad}} saves ${{tt_iris.saving}}, which is the
case for it on a site that expects all three. On a site that expects one size
it is an upgrade, not a necessity, and the fixed rim is the right answer. The
iris is also a development concept: nobody has built one, and it belongs in
the upgrade column until somebody does.

## The pad is the floor

<!-- concept: byod_deepseek/floor -->
<!-- concept: byod/foundation -->

This is the move the whole idea turns on.

The dome that arrives does not bring a foundation, because it does not need
one. **The pad is the floor.** The deck it lands on is the deck it lives on,
the services come up through the middle of it, and when the owner leaves, the
pad is exactly as it was for the next one.

No slab poured. No footing dug. No permit pulled for a foundation under a
building that will be somewhere else next year. Bring your carpet if you want
it; some people want a shop floor in their house, and that works too. It is
the dome owner's floor to finish, laid on the host's deck.

We already see domes for rent, most of them glorified tents let out a weekend
at a time. I do not think their value is ever realised that way. Own the
glorified tent, rent the place to put it, and both sides have a reason to make
a long arrangement work.

## What the ground is worth

<!-- concept: dome_park/math_foundation -->

How much of a house is the part you can never take with you? That is a
measurable question, so it was measured. Ask the Dome Creator for each of its
{{tt_ground.designs}} shipped designs twice -- once as shipped, and once with
its foundation set to bare ground -- and the difference is exactly what a pad
stands in for:

    {{park.w_foundation}}

For the designs that stand on something that costs real money, the ground is
anything up to **{{tt_ground.max_share}} percent** of the build. The design
this book's tenant figures are run on, the split-log homestead, saves the
least of them: ${{tt_ground.flagship_foundation}}, about
{{tt_ground.flagship_share}} percent.

:::box against
**For a dome that would have sat on a lawn, a pad saves nothing.** Several of
the shipped designs stand on bare ground, and for those the pad replaces no
foundation at all. What it sells them is services -- power, water, a drain, a
level deck -- and that is a smaller argument than "the pad is your
foundation." It is still an argument, but it is the one to make.
:::

![What the ground is worth, per design.](plate-ground-share.png)

## Below the line and above it

<!-- concept: byod/legend -->
<!-- concept: byod_deepseek/legend -->
<!-- concept: byod_deepseek/line -->

The films that go with this book keep the two people in different colours the
whole way through, because they want opposite things. **Amber is the pad
host**: the deck, the trench, the pedestal, the meter. **Cyan is the dome
owner**: the house, and everything they ever do to it.

The line between them runs along the top of the deck, and the most important
thing about it is that it never moves. Below the line is the host's money, and
it is in the ground. Above the line is the owner's money, and it drives away
with them.

Every other way people rent somewhere to live puts the landlord's money in the
walls the tenant lives between, and that is where the conflict comes from,
every time: the stained carpet, the deposit, the walk-through with somebody's
clipboard. Here the host never owns a building somebody else is living in, and
the tenant never pays rent on a thing that will never be theirs. Fewer things
held in common means fewer things to argue about -- and an easy goodbye, which
is worth more than people think. If it is not working, the dome leaves and the
pad is exactly as it was.
