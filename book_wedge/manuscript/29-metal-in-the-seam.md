---
chapter: 29
title: Metal in the Seam
strand: explain
status: draft
target: 2040
updated: 2026-09-30
---

# 29. Metal in the Seam

The line that runs from the centre of the dome straight outward has a name: it
is the **radial** direction. Through an ordinary wall it is the wall's
thickness. Through a seam it runs from the V's open mouth on the room side up
to the ridge on the weather side.

So the seam has two skins, the way a living cell has an inner and an outer
membrane. The **outer skin** is the ridge, under the cap, touching the weather.
The **inner skin** is the mouth of the V, touching the room. Put a
thermoelectric plate on each and you can set the temperature of both
independently.

That arrangement is the owner's, and it is a good one. This chapter is about
what it takes to make it work: the plates, the metal channel that carries
their cold, and the metals that must not touch.

![The outer skin at the ridge, the inner skin at the room side, and a plate on each.](plate-two-skins.png)

## The plate runs both ways

A Peltier plate is not a cooler. It is a small solid-state heat pump: current
through it moves heat from one face to the other, and reversing the current
reverses the direction.

So the rule for both plates is simple: **throw the heat to the side you want
warmer.**

- **In winter**, the cold face is in the channel and the heat goes into the
  room. The outer skin is already cold -- often cold enough to condense on for
  free, with no power at all.
- **In summer**, the cold face is still in the channel, but the heat goes to
  the outer skin and out under the cap. Throwing it into the room would mean
  paying twice: once to make the cold, and again to the air conditioner to
  remove the heat you just put in the room.

Chapter {{ch.seam_module}} drew the plate throwing its heat into the room. That
is right in winter and wrong in summer.

![Winter: heat to the room. Summer: heat outside.](plate-heat-pump.png)

## Fifteen to twenty degrees colder

The owner's question was this: if the framing wood is at the dew point, but the
aluminium or copper channel is fifteen to twenty degrees below that, will the
water go to the metal and leave the wood alone?

Take a room at {{clim.room_t}} degrees and {{clim.room_rh}} percent. Its dew point
is {{clim.room_dp}}. The middle of the owner's range, {{clim.owner_below}}
degrees under that, puts the plate at {{clim.owner_plate}}.

**The plate freezes.** Below zero, water comes out of the air as frost rather
than liquid. Frost does not run to the drain; it builds up on the fins, blocks
the air, and insulates the plate from the very air it is meant to dry.

So hold the plate {{clim.below}} degrees under the air's dew point and never
below {{clim.frost}}: here, {{clim.plate}} degrees. That is cold enough to
condense steadily and warm enough to drain.

![A plate driven that far under the dew point freezes.](plate-frost.png)

## Plate first, wood second

And the real answer to the question: **a colder surface somewhere else does not
protect wood that is already at the dew point.** Water comes out on every
surface colder than the air touching it. Wood at the dew point, washed by raw
room air, gets wet, however cold the plate across the channel is.

What protects the wood is **order**. Send the air over the plate first. It
leaves carrying a dew point of {{clim.dp_after}} -- about the plate's own
temperature plus a couple of degrees -- and then it reaches the wood. Wood at
{{clim.room_dp}} is now comfortably above it; anything above {{clim.wood_min}} is
safe with the margin this book keeps.

So in every mode that sends damp air along the frame, the plate is upstream of
the wood. In the rim layout of Chapter {{ch.levels}} that happens by itself:
the air comes in at the rim, over the plates, and then up the lower band.

![Air over the plate first leaves the wood with room to spare.](plate-plate-first.png)

**The cold metal must never touch the wood.** Aluminium carries heat
{{metal.al_petg}} times better than the printed key's plastic. A metal channel
laid against a sawn face chills that face toward its own temperature, and then
the wood is the cold surface. Keep the metal inside the key, or behind a strip
of closed-cell foam, never bare against the pine.

## Which metals may touch

Put two different metals in contact, add water, and you have made a battery.
The less noble metal dissolves into the more noble one. How fast depends on how
far apart they are on the galvanic scale, and whether they stay wet. In a
seam that condenses water on purpose, they stay wet.

The engineering rule, from military and aerospace practice, is that metals kept
wet may touch only if their anodic index differs by {{metal.wet_limit}} volts or
less:

    {{metal.pairs_table}}

Three rules come out of that table.

1. **Copper and aluminium never touch**, and water never runs from copper onto
   aluminium: at {{metal.cu_al}} volts apart, dissolved copper plates out on the
   aluminium and pits straight through it. If the plates are copper and the
   liner is aluminium, put a plastic break between them and keep the copper
   downstream.
2. **Stainless bolts through aluminium need sleeves.** At {{metal.ss_al}} volts
   apart, a stainless bolt in a wet aluminium liner eats the liner round the
   hole. Nylon washers and sleeves isolate it.
3. **Copper and stainless may touch** ({{metal.cu_ss}} volts). If you are
   choosing one metal for the condensing channel and the bolts are stainless,
   that is the argument for copper. It also carries heat
   {{metal.cu_al_k}} times better than aluminium, which is the argument for it
   as a plate; it costs more and weighs more, which is the argument against.

Keep galvanised steel out of the seam entirely.

## A liner grows against the wood

Metal moves with temperature much more than wood does along its grain. Over the
longest seam, {{metal.liner_in}} inches, and a {{metal.swing}}-degree swing
between a winter night and a summer afternoon under the cap:

    aluminium liner      {{metal.al_mm}} mm
    copper liner         {{metal.cu_mm}} mm
    the pine beside it   {{metal.pine_mm}} mm

So fix a liner at one end only, and let the other end slide in a slot. A liner
screwed down at both ends either buckles or pulls its screws, and the
screw holes are where the water gets in.

The figures behind this chapter:

    {{metal.constants_table}}
