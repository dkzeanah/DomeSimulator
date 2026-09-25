---
chapter: 30
title: The Software That Wrote This Book
strand: reference
status: draft
target: 980
updated: 2026-09-25
---

# 30. The Software That Wrote This Book

Not one figure in this book was typed into a sentence.

Every dimension, count, angle, percentage and price is a token in the
manuscript that gets filled in, at the moment the book is made, by the same
software that draws the three-dimensional models. When this book says the dome
is {{dome.diameter_ft}} feet across, that number came out of a solver about a
second before it reached the page.

That software comes with the book. {{tool.total}} programs — {{tool.worlds}}
worlds you can fly around in, {{tool.models}} that are arithmetic with no
picture, and the desks where the book and the films are made.

## Why a builder would open any of it

The short answer: **because your tree is not my tree.**

Every number in these pages is for one specific dome, cut from one specific
size of log, at one split count, with one orientation. Change any of those and
every downstream figure changes — the chords, the cuts, the seam key, the
timber, the price. The tables at the back are a snapshot of one solve.

The tools are how you take your own.

## Three kinds of thing

**Worlds** are three-dimensional environments with a window, a camera and
keys. This is where you go to *look* at something — to turn one decision and
watch what it does to the joint.

**Models** are arithmetic with no picture. They answer a question and print a
table: what does this cost, how long is that stick, what does the platform
take off to.

**Desks** are where you make something: this book, the films, the calculators.

## What each one is for

    {{tool.table}}

## The one that matters most

If you open exactly one thing, open the solver, and press the key that
explodes the panels apart.

Everything difficult about this method is in the gap between two panels — the
key, the angle, why the point faces inward, where the error goes. It is
invisible in an assembled dome and obvious the moment you can see into a seam,
and no drawing in this book, including the section in Chapter
{{ch.pinwheel}}, teaches it as quickly as turning it in your hands for a
minute.

## How the numbers get from there to here

Worth stating once, because it is the unusual part.

The manuscript is Markdown with holes in it. A sentence that needs a figure names
the number it wants -- `dome.diameter_ft` in double braces -- rather than
printing one. At build time a
resolver fills every one of them from the solver, the geometry and the cost
model, and an **unknown token is a hard error** — the book refuses to build
rather than printing a blank.

The reason is not showing off. A number typed into a paragraph is correct on
the day it is typed and silently wrong from the first time anybody changes
anything. Nothing fails. The book just quietly becomes untrue in places nobody
remembers.

So the arithmetic in this book is a test suite. It runs, it checks itself
against the geometry, and it fails loudly.

## It caught four things

This is not theoretical. An audit reads the finished prose and checks every
figure in it — every number carrying three or more decimals, and every dollar
figure — against what the code can actually produce. It found:

* a set of reference designs that **scaled the pinwheel's bite with the
  dome**, which is the exact error Chapter {{ch.two_lengths}} spends a page
  warning about. Every stick of the smallest dome was an inch too long;
* a triangle altitude printed as 52.520 where the solve says
  {{seam.narrowest}} — in the sentence that tells a reader whether plywood
  fits;
* four prices from before the shell lost a waterproof layer, still being
  quoted as current;
* a chapter quoting the cost of a whole upgrade as the cost of two of its
  three parts, double-counting the third.

Every one of those was written by somebody being careful. That is the point:
care is not a method for keeping numbers true across time, and a program that
re-checks them on every build is.

## Change the tree and rebuild

The whole of it — geometry, prices, figures, this book — regenerates from one
set of inputs.

Change the trunk diameter to what you actually felled. Change the split count
to what your froe will do. Rebuild. Every chapter that mentions a figure now
says your figure, without anybody going looking, and the pictures are redrawn
from your solve.

That is what "the software comes with the book" means here. It is not a
companion download. It is the thing the book is a printout of.
