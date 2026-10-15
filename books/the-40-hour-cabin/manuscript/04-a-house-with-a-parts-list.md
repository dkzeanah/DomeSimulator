---
chapter: 4
title: A House With a Parts List
strand: explain
status: draft
target: 1780
updated: 2026-10-02
---

# 4. A House With a Parts List

## The whole argument, start to finish

<!-- concept: master/ms_open -->

Here is everything this book is going to argue, said once, so you can watch
it being proved.

A dome made this way is a shape that spends less on skin and gives that back
every winter. It is made of two lengths of wood, cut on one flat board. It is
built by a method that forgave a chainsaw, so it will forgive you. It has a
price list with a receipt behind every line and an energy bill you can work
out for yourself. And none of it is an opinion, because every number in it is
counted off the same model of the building that draws its pictures.

That last part is the one this chapter is about.

![Everything this project knows, in one film.](plate-whole-argument.png)

## Nothing here is typed in

<!-- concept: master/ms_math_counted -->

Ask a builder what a house will cost and you get an opinion, informed by
experience and padded for the things that go wrong. Ask this dome, and it
counts itself:

    triangular panels                  {{dome.panels}}
    edges of the short length          {{parts.short_edges}}
    edges of the long length           {{parts.long_edges}}
    edges in all                       {{dome.edges}}
    corners where edges meet           {{dome.vertices}}

Nobody wrote those numbers into this paragraph. The software that solves the
dome and draws its pictures is the software that counts it, and the book fills
those numbers in at the moment it is printed. Every figure in the chapters
that follow -- every angle, every dollar, every gallon -- reaches the page the
same way. Where something cannot be computed, a price or a bead size or how
much oil rough wood drinks, the book says where it came from and marks it as
an assumption.

That is not pedantry. It is the difference between a parts list and a price
opinion. A parts list can be checked, and when one input changes, every figure
that depends on it changes with it.

![The panel on the right is counting the dome behind it.](plate-model-counts-itself.png)

## The cut list makes itself

<!-- concept: master/ms_math_cutlist -->

Here is the chain, as arithmetic.

Pick the size: one number, the radius of the sphere the dome is a slice of.
This book's reference build has a radius of {{dome.radius_in}} inches.

Two fixed factors turn that radius into the two chord lengths every geodesic
reference publishes: {{cut.a_chord}} inches and {{cut.b_chord}}. Chapter
{{ch.two_lengths}} explains why you do not cut either of them: the pinwheel
joint bites {{cut.a_bite}} inches off a long member and {{cut.b_bite}} off a
short one, and that bite is measured, never guessed. So the saw is set to
{{cut.a_cut}} and {{cut.b_cut}}.

Then the order falls out:

    long members          {{parts.long_members}}, each {{cut.a_cut}} in
    short members         {{parts.short_members}}, each {{cut.b_cut}} in
    members in all        {{dome.members}}
    timber in the frame   {{dome.timber_ft}} ft
    log sections          {{parts.sections}}, split {{cut.splits}} ways each

Change the radius and every line of that table recomputes. That is what it
means for a house to have a parts list: the size is a decision, and everything
after it is consequence.

![Pick the radius; the cut list and the order fall out.](plate-cut-list.png)

## The flat rate, proved

<!-- concept: master/ms_math_flatrate -->

This is the number that turns a weekend project into a product, so prove it
rather than repeat it.

Scale the dome from {{flat.small_ft}} feet across to {{flat.big_ft}} and count
again:

    {{flat.small_ft}} ft dome      {{flat.small_sqft}} sq ft of floor
    {{flat.big_ft}} ft dome      {{flat.big_sqft}} sq ft of floor
    members, either way            {{dome.members}}
    panels, either way             {{dome.panels}}
    joints, either way             {{dome.edges}}

The floor grows {{flat.ratio}} times over, because area grows with the square
of the size. The parts list does not grow at all. The sticks get longer; the
list of things you do to them stays exactly the same length -- the same
splits, the same two saw settings, the same panels on the same board, the
same raising.

Labour is priced by operations, not by square feet. That is why the labour in
a dome is close to a flat rate, and why the bigger house is the better deal.
The honest limit is the stick: a member is a split log, and a log only comes
so long, which is why Chapter {{ch.size}} picks the size from the stick rather
than from the floor plan.

![Scale the dome and count what changes.](plate-flat-rate.png)

## One skeleton, four buildings

<!-- concept: master/h_lines -->

The same frame is already four products in the software that wrote this book:
a dome home, a storage shed, a greenhouse and a storm shelter. Four buildings
at four price points, and the same triangles under every one of them.

That is the pattern the rest of the book keeps finding. The skeleton is the
constant and everything that makes it a particular building -- the skin, the
floor, the openings, the services -- is a choice made on top of it. Chapter
{{ch.seeds}} takes that all the way, to {{seed.count}} structures from one
body.

![Four buildings, one skeleton.](plate-four-lines.png)
