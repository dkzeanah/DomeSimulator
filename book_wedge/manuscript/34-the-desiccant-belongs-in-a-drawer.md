---
chapter: 34
title: The Desiccant Belongs in a Drawer
strand: explain
status: draft
target: 2160
updated: 2026-09-30
---

# 34. The Desiccant Belongs in a Drawer

A desiccant is anything that pulls water vapour out of air and holds on to it.
Two kinds matter here.

**Silica gel** is the beads in the packet in a new pair of shoes: porous glass
that holds water in its pores. **Molecular sieve** is a zeolite -- a mineral
with a crystal lattice full of holes the exact size of a water molecule. The
common grade, 13X, holds about a fifth of its own weight in water, keeps
pulling vapour out of air long after silica gel has given up, and is what
people mean when they talk about a solar-regenerated fridge or a dryer that
works in the tropics.

Both do the same thing in the seam: they are the frame loop's dehumidifier
(Chapter {{ch.dewpoint}}), the one way to dry the wood when neither the inside
air nor the outside air is dry enough. The question is where to put them. The
candidates are the obvious ones: packed along a seam, packed round a ring,
arched over the top of the dome from one side of the floor to the other like a
rainbow, or in one place.

The answer is one place, and two drawers. Here is why.

## Why not in the seams

A seam packed with beads is a very long, very thin filter, and air does not
like going through filters.

The resistance of a packed bed is well understood -- it is the Ergun equation,
which chemical engineers use for exactly this -- and it rises steeply with both
the speed of the air and the length of the bed. Take one seam's share of the
dome's air, {{clim.seam_flow}} cubic feet a minute, and push it through one
seam packed with beads:

    resistance of one packed seam        {{clim.packed_pa}} Pa
    what a small in-line fan pushes      {{clim.fan_pa}} Pa
    what that fan gets through           {{clim.packed_cfm}} cu ft a minute

A packed seam does not slow the air down. It stops it. The rainbow, rim to apex
to rim along the seams, is {{clim.meridian}} feet of it, and worse again.

![One seam packed with beads, and the pressure it would take to push the air through.](plate-packed-seam.png)

It would also hold a lot of beads to no purpose -- packing every seam takes
{{clim.seams_sieve}} kilograms of them -- because a bed the air cannot get
through is a bed whose water nobody can reach.

## And why it cannot be dried where it sits

A desiccant fills up. To use it again you have to drive the water back out, and
that takes heat:

    13X molecular sieve gives its water back at    {{clim.sieve_c}} C
    silica gel                                     {{clim.silica_c}} C
    the printed key goes soft at                   {{clim.petg_c}} C
    the hottest air this book sends through a seam {{clim.seam_max_c}} C

Beads in a seam could never be regenerated where they sit. You would have to
bake the frame to do it, and the key would have melted long before the beads
gave anything up.

## Two drawers and a gate

So the desiccant lives in **drawers, at the rim**, where the channels come down
to the pad and a person can reach them.

One drawer {{clim.drawer_cm}} centimetres square and {{clim.drawer_depth}} deep
holds {{clim.drawer_kg}} kilograms of beads, which hold {{clim.drawer_hold}}
kilograms of water between them, and it passes the whole dome's air at
{{clim.drawer_pa}} pascals: a fan barely notices it. A short, wide bed is
everything a long, thin one is not.

1. **Use two drawers.** One works while the other is out being dried. This is
   the arrangement every industrial compressed-air dryer uses, and for the same
   reason: the air never waits for the desiccant.
2. **Regenerate them out of the wall.** A drawer of 13X wants
   {{clim.drawer_kwh}} kilowatt hours to dry out: about {{clim.stove_min}}
   minutes of a stove exchanger's {{clim.stove_kw}} kilowatts, or an oven, or a
   black box in the sun on a hot day.
3. **Switch between drawer and bypass with a gate that fails open.** The gate
   is a damper with two positions: through the drawer, or round it. Build it
   so that when the power goes, a spring puts it on the bypass. Air that stops
   moving in a wooden seam is the failure; air that skips the desiccant for an
   afternoon is not.
4. **Put the gate where the channels meet**, in the rim rosettes, not halfway
   along a seam where you cannot reach it.

![A drawer of beads and a bypass, switched by a gate that falls back open.](plate-two-drawers.png)

## What the desiccant will not do

And the number that does not help.

A frame that has got properly wet -- over {{clim.mc_wet}} percent moisture --
has {{clim.frame_water}} kilograms of water to lose to get back to
{{clim.mc_target}}. That is {{clim.drawer_fills}} drawer fills, and
{{clim.frame_kwh}} kilowatt hours of heat to regenerate them.

**The desiccant does not dry a soaked frame.** It is for the weather when no
air is dry enough and the frame needs to stay where it is, not for getting it
back after a leak. Drying a wet frame is the purge's job, with dry outside air,
on the next dry day. The desiccant keeps it from getting wet in the meantime.

## The stove's heat, never its air

A wood stove is a large, free source of heat in winter, and the owner's
thought was to have it drive the seam's air: pulling it in or pushing it out
depending on which way it draws.

Use its heat, never its air.

- **A sealed exchanger on the flue** -- smoke on one side of a steel wall, clean
  air on the other -- warms air that can dry the frame or regenerate a drawer.
  The smoke side never meets the seam's air.
- **Keep that air under {{clim.seam_max_c}} degrees** before it reaches a seam.
- **Give the stove its own outside air** for combustion, through its own duct.
  Building-science guidance says the same for any tight building: a stove that
  draws its air through the gaps in the envelope competes with every fan in the
  house.
- **Never connect the stove's draw or its flue to the seams.** A stove that can
  pull on the seam network is a stove that can back-draught smoke into the
  walls the first time a fan pulls harder than the chimney.

![The flue sealed away; clean air warmed across a wall of steel.](plate-stove-exchanger.png)
