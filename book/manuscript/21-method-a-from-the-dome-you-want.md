---
chapter: 21
title: Method A: From the Dome You Want
strand: howto
status: drafting
target: 2700
updated: 2026-09-08
---

# 21. Method A: From the Dome You Want

*Radius in, cut list out*

<!-- Every number in this chapter must come from:
     - book_math.design_first
     - book_math.design_first_for_floor
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## Method A

You know what you want. Now find out what it costs in trunk.

This is the method to use when the timber is genuinely not decided — when you
will fell, buy or scrounge whatever the design asks for. It runs from the
building to the woodpile, which is the direction every other construction
book works in, and it is the more comfortable of the two.

It is also the one that will tell you, politely and in advance, when the dome
you have in mind needs more trees than you have.

## The procedure

### 1. Start from floor, not radius

Nobody wants a radius. They want a room.

Decide the floor area you want to stand on and convert:

> radius (feet) = √(floor ÷ π)

{{method_a.floor_sqft}} square feet gives a radius of
{{method_a.radius_ft}} feet — call it {{method_a.radius_in}} inches. A 2V
hemisphere's standing height at the centre *is* its radius, so
that same number is also your ceiling.

This is the first place a dome surprises people. A
{{method_a.floor_sqft}}-square-foot dome is {{method_a.radius_ft}} feet tall in
the middle, which is more house than the floor area
suggests, and the volume is doing something a rectangle of the same footprint
cannot.

It is also the first place a dome disappoints people, because not all of that
floor has headroom over it. Chapter {{ch.round_room}} has the map.

### 2. Measure the stock you expect to have

Even in Method A you cannot skip this. The pinwheel setback depends on how
wide your members are, and you cannot compute a member length without it.

If you have not felled anything yet, use the diameter you expect to be
cutting. A {{tree.butt_diameter_in}}-inch butt tapering to
{{tree.top_diameter_in}} gives sectors about {{member.width_in}} inches wide
at mid-trunk, and that is the figure this book's tables assume.

If your logs will be fatter, your members will be wider, your setback will be
larger, and every length in your cut list will come out shorter than the
tables here. The tables are computed at this book's stock; recompute for
yours.

### 3. Solve the member lengths

For a chosen radius, the layout gives you {{dome.member_lengths}} member
classes. This is the calculation Chapter {{ch.which_way}} described, run in the forward
direction: radius in, lengths out.

At {{method_a.floor_sqft}} square feet the longest member comes out at
{{method_a.longest_in}} inches and the shortest at
{{method_a.shortest_in}}.

![{{method_a.floor_sqft}} square feet, worked all the way through.](../../deliverables/book/figures/method-a-worked.png)

### 4. Round the bucking length up

Your longest member is {{method_a.longest_in}} inches. Buck to
{{method_a.buck_ft}} feet — {{method_a.buck_in}} inches.

You cannot buck to {{method_a.longest_in}} inches. Well, you can, but you
should not: a section
cut to exactly the longest member leaves no allowance for the head-end
overfit (Chapter {{ch.head_overfit}}), no allowance for the butt cut (Chapter {{ch.butt_cut}}), and nothing
at all for the end of a log being split or shaken.

**Round up to the next whole foot and take the waste.** It is the cheapest
line item in the build.

This does mean the design-first path throws away more wood than the tree-first
path, because the tree-first path chooses a dome that uses the whole section.
That is a real cost of getting to pick your diameter, and it is worth saying
out loud rather than discovering in the offcut pile.

### 5. Count sections, then trunk, then trees

The frame needs {{frame.members}} members. Each section gives
{{tree.sectors}}, so:

> sections = {{frame.members}} ÷ {{tree.sectors}} = {{method_a.sections}}

> trunk needed = {{method_a.sections}} × {{method_a.buck_ft}} ft = {{method_a.trunk_ft}} feet

> trees = {{method_a.trunk_ft}} ÷ {{tree.usable_length_ft}} = {{method_a.trees}}

So: **fell {{method_a.whole_trees}}.**

Notice the number. Designing a {{method_a.floor_sqft}}-square-foot dome from
scratch and sizing the trees to it lands on the same
{{method_a.whole_trees}} trees that this book's actual build used, from the
opposite direction. That is not a coincidence — it is the size
of dome a pair of ordinary pines makes, and it is why this method produces
houses of roughly this size over and over.

### 6. Check it against the tree you can actually get

Then go and look at the trees.

If the tallest straight trunk you can find is thirty feet rather than
{{tree.usable_length_ft}}, your {{method_a.trees}} trees becomes three. If
your logs are much
thinner at the butt than {{tree.butt_diameter_in}} inches, your members
are narrower, your sticks are longer for the same dome — and thinner, which
Chapter {{ch.forces}} has opinions about.

This is where Method A hands over to Method B, and where Chapter {{ch.round_trip}}'s round
trip earns its place.

## Where this method surprises people

**Member length does not scale with the dome.** Double the radius and the
members do not double. They grow by slightly less, because the pinwheel
setback stays the same size while the triangle grows around it.

This is good news at large sizes and bad news at small ones. A very small
dome has members so short relative to their own width that the setback eats a
serious fraction of them, and below a certain size the geometry stops making
sense at all — a stick that is nearly as wide as it is long is not a strut,
it is a block. Chapter {{ch.frequencies}} says where that line is.

**Height is not a free variable.** In a plain hemisphere, height equals
radius. If you want a wide floor and a ceiling taller than
half that width, you cannot have both from a hemisphere; you need a riser wall
under it (Chapter {{ch.openings}}) or a different fraction of a sphere, which is a different book.

**The trees number is rarely a whole one.** You will get
{{method_a.trees}}, or 2.4, or 3.1. Round up and accept the leftover, or
shorten the bucking length and see
whether the arithmetic lands better. There is no third option that gets you a
partial tree.

## The lookup table

If you would rather not do any of this, the table below is the whole method
precomputed at this book's stock section. Find your floor area on the left and
read across.

![Floor area to trees.](../../deliverables/book/figures/design-lookup.png)

Two warnings about using it:

1. It assumes members {{member.width_in}} inches wide. Different logs,
   different table.
2. The `trees` column assumes {{tree.usable_length_ft}} feet of usable trunk
   per tree. If your trees are shorter — and most are — scale it.

## Then check it the other way

You now have a cut list. Before you cut anything, take the longest member off
that list, hand it to Method B, and see what dome comes back.

It should be the dome you started with. If it is not, you have made an
arithmetic slip or changed an assumption halfway through — a different gasket
thickness, a different split count, a different stock width.

That check is Chapter {{ch.round_trip}}, it takes ten minutes, and it is the reason this
book has two methods rather than one method and a warning.
