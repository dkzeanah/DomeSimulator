---
chapter: 19
title: Linseed Oil, Where It Belongs
strand: howto
status: draft
target: 2260
updated: 2026-10-03
---

# 19. Linseed Oil, Where It Belongs

<!-- concept: cabin_linseed_oil/purpose -->

A video that this project's research pipeline ingested -- *{{lin.source}}* --
offers twenty uses for linseed oil, and some of them are good ones for a dome
workshop. This chapter sorts them by what survives contact with the building:
exposed interior wood, shelves and trim, and hand tools on one side; seams,
weather and windows, where a finish has to work with the rest of the assembly,
on the other.

The source is a list of claims, not a comparison test, so this chapter shows the
working, the quantities and the limits before it calls anything a saving.
Chapter {{ch.finish}} already covers the round face of the frame; this one is
everything else.

## The rag station comes first

<!-- concept: cabin_linseed_oil/rags -->

Before the can is open, set up for the used cloths. Linseed oil cures by taking
up oxygen, and that reaction gives off heat. A heap of oily cloths traps the heat
and can ignite with no spark at all.

Follow the label and your local fire service. The usual practice: cover used
rags completely with water and an oil-breaking detergent in a metal container
with a tight lid, stored outside and away from anything that burns, and arrange
proper disposal. Keep them out of pockets, sawdust and ordinary bins. A wet rag
that dries out in a heap is dangerous again.

## Read the can

<!-- concept: cabin_linseed_oil/oils -->

Raw, boiled and polymerised linseed oil are not interchangeable.

- **Raw** oil cures slowly, over days.
- **Boiled** oil, as sold in hardware stores, is usually raw oil with drying
  additives; it is not boiled, and you should never try to boil oil yourself.
- **Polymerised** oil has been heat-treated by the maker and cures differently
  again.

Read the ingredients, the safety sheet and the intended uses. A name like
*natural*, *boiled* or *Danish* does not identify a formulation. For anything
that touches food, choose a product sold for that use and follow its cure
instructions -- the source's rule that only raw oil is food-safe is too broad in
both directions.

## Two labels, two schedules

<!-- concept: cabin_linseed_oil/label_inputs -->

Two products from one maker show why a generic timing cannot be applied to every
can. These are the manufacturers' claims, marked as such, not measurements:

    Danish oil        rub dry after at least {{lin.danish_wait}} min, cure at least {{lin.danish_cure}} h
    oil-and-wax       rub dry after at least {{lin.wax_wait}} min, cure at least {{lin.wax_cure}} h

Both are minimums. In cold, damp conditions neither guarantees the surface is
ready. Use the current label of the product you actually bought.

## Prepare the member, then apply thinly

<!-- concept: cabin_linseed_oil/prepare -->
<!-- concept: cabin_linseed_oil/apply -->

1. **Inspect.** Reject decay; deal with splits and loose joints through the
   repair the design calls for. Oil cannot restore lost strength.
2. **Dry.** Let the wood reach the moisture the finish needs, and check it with a
   meter (Chapter {{ch.green}}).
3. **Clean.** Remove dirt and unsuitable old coatings, smooth splinters, clear
   the dust.
4. **Mask.** Mark the places that must bond to glue, tape, sealant or a gasket,
   and keep the oil off them.
5. **Test an offcut** for colour and cure before the real piece.
6. **Apply a very thin coat**, evenly, with the applicator the label specifies.
   After the product's soaking interval, rub away everything that has not gone in
   until the surface is dry to the touch.
7. **Cure** with the ventilation and temperature the label asks for, and look at
   the surface before the next coat. Never bury a sticky layer under more oil.

Watch the end grain, which drinks more, but stop drips running into joints. And
never close an uncured finish inside a panel or an air passage people breathe.

![Apply thinly, then wipe dry.](plate-thin-coat.png)

## How much, and how long

<!-- concept: cabin_linseed_oil/planning_inputs -->
<!-- concept: cabin_linseed_oil/area -->
<!-- concept: cabin_linseed_oil/quantity -->
<!-- concept: cabin_linseed_oil/limits -->

Measure wood, not floor area. The solver's stock schedule is
{{lin.stock_ft}} feet of member, and each flat radial face is {{lin.depth_in}}
inches deep. The film works an allowance from declared planning inputs, marked
by kind:

    {{lin.constants_table}}

That gives a planning envelope of {{lin.area}} square feet, and:

    the declared coats              {{lin.base_gal}} US gal
    with the handling allowance     {{lin.allow_gal}} US gal
    at the label's best coverage    {{lin.label_gal}} US gal

**Two cautions about those numbers.** First, the envelope counts *both sawn
faces* of every member as a reference area. It is not an instruction to oil them
-- Chapter {{ch.finish}} argues they should stay bare, and its own allowance for
the round faces alone is {{wood.oil_l}} litres. The two figures answer different
questions; the difference between them is the sawn faces. Second, coverage is the
input that decides everything, and the label's best figure is a claim made on
smooth wood, not a rough-sawn wedge. Measure how much you use on a known offcut
through the whole coat schedule, and scale that.

And the number that argues against it: hand application is labour. At an
estimated {{lin.minutes}} minutes a member a coat, the coats above are
**{{lin.labour_h}} hours of active work**, before any preparation, access,
inspection or waiting for cure. A cheap can can still make an expensive job.

## Where it does not belong

<!-- concept: cabin_linseed_oil/seam -->
<!-- concept: cabin_linseed_oil/weather -->
<!-- concept: cabin_linseed_oil/glazing -->

**Not in the seam's working surfaces.** Oil on an exposed interior face is a
finish; oil on a sealing land is a contamination. Adhesives and tapes need clean,
compatible surfaces. Keep the printed key, the gasket lands, the drainage path
and the services clean, check both makers' compatibility before coating wood
beside a gasket or sealant, and never count an oil coat as an air seal, a rain
seal or a cure for condensation.

![Finish decisions follow the assembly.](plate-oil-seam.png)

**Not as the weather skin.** The source describes linseed oil as outdoor
protection and waterproofing. A dome still needs its watertight layer (Chapter
{{ch.one_layer}}), flashed openings, drained joints and a way to dry. Plain oil
establishes none of those, proves no resistance to sunlight, rot or insects, and
damp, linseed-rich wood can grow mildew. Outdoors, use a finish rated for the
exposure.

**Not as glazing in a dome roof.** Linseed-based putty has a real place in
traditional sash windows, with mechanical retainers holding the glass -- putty
alone must never carry it. It is not a design for sloped or overhead dome
glazing, which needs a complete system specified for that position, and the
video's homemade chalk-and-oil putty does not belong in the dome's weather seams.

## The parts people touch, and keeping them

<!-- concept: cabin_linseed_oil/interior -->
<!-- concept: cabin_linseed_oil/tools -->
<!-- concept: cabin_linseed_oil/maintenance -->
<!-- concept: cabin_linseed_oil/close -->

**Inside**, linseed oil is at its best: shelves, trim and sound furniture. Test
for yellowing and for compatibility with any old coating. An oil-and-wax blend
gives a low sheen, but wax complicates later gluing and recoating. Floors need a
floor-rated system; kitchen surfaces need a product sold for food contact.

**Tools.** The handle trick transfers well when the handle is sound: inspect the
hammer, mallet and jig handles for cracks and loose heads, then finish them thinly
and let them cure before gripping. Oil does not repair a broken handle. A drying
oil can protect clean, non-moving steel in storage, but keep it out of bearings,
hinges, the saw chain and brake, electrical contacts and fastener threads, which
need their own products.

**Maintenance.** Keep a finish record: product, batch, date, preparation and
where it went, with a sample piece in the building's notes. Inspect for wear,
tackiness, mildew and water marks; find the cause before renewing. Grey wood
darkens beautifully under oil, but colour is not strength -- oiling does not
reverse decay, and it earns no credit for waterproofing a foundation.

So: use linseed oil where a maintainable wood finish suits the job -- accessible
interior faces, trim and sound tool handles. Keep seams and bonding surfaces clean,
give the roof its own weather system, choose glazing for the actual opening, base
the quantity on measured wood, budget the hand labour, and end every day with
every oily cloth accounted for.
