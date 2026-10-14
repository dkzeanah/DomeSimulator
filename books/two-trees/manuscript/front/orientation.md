---
section: front
title: What this book is
status: drafting
target: 650
updated: 2026-10-13
---

# What this book is

{{dome.trees}} trees, one chainsaw off a hardware-store shelf, one hundred
and twenty structural members, and a geodesic dome standing in fourteen
days — {{hr.with_error}} hours of hands-on work, inside the forty-hour
week the title is named after.

That is the whole claim, and everything in this book exists to either explain
it, prove it, or teach you to do it.

## It is a real build

The dome in the plates is the simulator's solved frame — the same software
computed every number printed in this book, and the build itself was cut
for real: felled, split, panel by panel on a jig, and winched up between
two standing trees. The process of cutting it produced a number of
surprises, most of which are in here. Several chapters exist specifically to
report a figure that does not flatter the method — Chapter {{ch.recovery}} revises the
recovery claim downward, Chapter {{ch.money}} cuts an hourly rate this project
publicised by more than half, once the honest section is used — and the
corrections live in the chapters where the claims were
made, named rather than silently edited. A book about a new building method
that contains no corrections is a brochure.

## It is three books at once

The reader I had in mind wanted three different things, and they read at
three different speeds, so rather than blend them into a mush each chapter
declares which one it is.

**The story** is what happened, in order, to somebody with a saw: the
frankendome that came first, the afternoon the wedge was found, and the week
lost to a problem that turned out not to exist. {{book.story}} chapters, and
you can read them straight through as a narrative.

**The manual** is do this, then this. {{book.howto}} chapters, and if you
follow only those you get a dome. It is a complete set of instructions on
its own.

**The explanation** is why any of it works — why a triangulated frame will
accept a stick no mill would sell, why splitting a round log is free and
squaring it is not, and why this method does not transfer to a rectangular
house. {{book.explain}} chapters, all skippable, all there because a method
you do not understand is a method you cannot adapt.

The rest is reference: the tables you come back to at the saw rather than
read in an armchair.

![Three ways through this book.](../../../deliverables/book/figures/strand-map.png)

## Every number here is computed

This is the unusual part, and it is worth a paragraph.

Not one figure in this book was typed into a sentence. Every dimension, count,
angle, percentage and price is a token in the manuscript that gets filled in,
at the moment the book is made, by the same software that draws the
three-dimensional models. When it says the dome is {{dome.diameter_ft}} feet
across, that number came out of a solver about a second before it reached
this page.

The reason is not showing off. It is that a number typed into a paragraph is
correct on the day it is typed and silently wrong from the first time anybody
changes anything — and there is no way to find those. Nothing fails. The book
just quietly becomes untrue in places nobody remembers.

So the arithmetic in this book is a test suite. It runs, it checks itself
against the geometry, and where two ways of computing something disagree the
book prints both and says which is which. Chapter {{ch.round_trip}} is nothing but a proof
that the two methods in Part One are the same calculation, and it prints the
residual — zero, to the last decimal the computer keeps — rather than asking
you to take it on trust.

The tools that produced these numbers are published as open source at
{{book.repo}}, and the Complete Edition — the same method carried further,
with the codebase — is sold on the site. The last pages of this book point
the way.

## Before you start a saw

The felling chapter sends you back here, so this page says the things
once, plainly, before any cutting is described.

A chainsaw is the most dangerous tool most people will ever hold, and
felling is the operation that kills people who have done it a hundred
times. If you have never felled a tree, learn on the ground with somebody
who has — this book teaches the method, not the trade.

**Never fell alone.** Two people, minimum. The second person is the
lookout, the caller, and the one who goes for help. Their one job during
the fall is to be out of the fall.

**Wear the kit.** Chainsaw-protective chaps or trousers, a helmet with a
mesh visor and ear defenders, gloves, and boots. Every one of them exists
because a specific accident already happened to somebody without it.

**The escape route is walked, not imagined.** Before the saw starts,
walk the route back and to the side, opposite the planned fall, and clear
it. A tree falls in seconds and the escape takes seconds; the route being
pre-walked is the entire margin.

**Read the bend before you cut a downed trunk.** A log lying between two
supports is under tension on one side and compression on the other. Cut
the side in tension first, or cut from the outside of the bend inward;
cutting the compressed side pinches the bar.

**Never stand under a hanging load.** Not the frame on the winch, not a
limb under a trunk, not for one second — including the moment you most
want to, which is when it is working.

And this book is not an engineer's stamp. Nothing here has been checked
by a licensed structural engineer. Where a figure depends on species,
grade or moisture the book says so and tells you who to ask instead of
guessing; where a load figure matters, it names the number as an
engineer's job and leaves it there.

## What it is not

It is not an engineer's stamp — the sentence above says why, and the
title page says it at length. Nothing here has been checked by a licensed
structural engineer, and where a figure depends on species, grade or
moisture this book says so and tells you who to ask instead of guessing.

It is not a code compliance document. Your jurisdiction has opinions about
round buildings and they are not in here.

And it is not a promise that you will do this in a fortnight. I did, on the
second attempt, having already made every mistake the story chapters
record.
The forty hours is the honest claim — the frame, split wedges to standing —
and the calendar around it is yours: a fortnight of part days, or a long
weekend of full ones, with the skin, the floor and the ground added later,
in any order.
