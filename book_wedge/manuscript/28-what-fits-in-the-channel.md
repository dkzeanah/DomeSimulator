---
chapter: 28
title: What Fits in the Channel
strand: reference
status: draft
target: 2240
updated: 2026-09-30
---

# 28. What Fits in the Channel

Chapter {{ch.seam_module}} fitted the seam out as gutter, vent and
dehumidifier and priced it. It did not say how much room there is inside it,
and every idea anybody has for the channel -- a water line, a circuit, a
duct, a desiccant -- runs into that number first.

So here it is, from the solver's own seams, for the reference build.

The V between two members is {{chan.gap_t}} degrees at the tighter of the two
seam types and {{chan.gap_w}} at the wider, and as deep as the log's radius.
The key that fills it is printed with {{chan.wall_mm}} millimetre walls, and it
stops short of the ridge where the V is too narrow to be any use. What is
inside those walls is the budget:

    inside the key, tighter seam       {{chan.area_t}} sq in
    inside the key, wider seam         {{chan.area_w}} sq in
    largest round thing, tighter       {{chan.round_t}} in
    largest round thing, wider         {{chan.round_w}} in

Everything in this chapter has to fit in that.

![A water line, a circuit, the plates' pair and the drain, in the tighter of the two seams.](plate-bundle-fits.png)

## The sizes this chapter assumed

The pipe and tubing sizes are nominal, from their standards. The cable sizes
are estimates, because every brand's sheath is different. The rule for how full
a channel may be is borrowed from electrical conduit, which allows
{{chan.fill_rule}} percent of the area for a mixed bundle so the last thing can
still be pulled through. The channel is not a listed raceway; the rule is used
because it is a sensible allowance, not because it applies.

    {{chan.sizes_table}}

## What fits, item by item

    {{chan.fits_table}}

**Water and wire fit, with room to spare.** A half-inch PEX line, a
fifteen-amp circuit, the twelve-volt pair to the condensing plates and the
condensate drain go into either seam together, filling {{chan.fill_t}} percent
of the tighter one and {{chan.fill_w}} percent of the wider one, against the
{{chan.fill_rule}} allowed.

**Round ducts do not.** The smallest ordinary duct is three inches round. The
largest round thing either seam passes is {{chan.round_w}} inches. If the plan
was to run ducts through the seams, the plan does not work as drawn, and a
bigger log does not rescue it.

![The smallest ordinary duct, against the V it would have to go in.](plate-no-duct.png)

## The channel is the duct

It does not need a duct in it, because it already is one.

With the water, wire and drain inside, the free space in one tighter seam still
moves {{chan.cfm_t}} cubic feet of air a minute at a quiet {{chan.fpm}} feet a
minute. The whole dome needs {{chan.need_cfm}} for fresh air. So
**{{chan.seams_for_air}} seams carry the building's ventilation**, and every
other seam is free for drying the frame, which is the job of Chapter
{{ch.dewpoint}}.

## If you want a duct anyway: the key becomes a spacer

There are reasons to want a real duct: a heat-recovery ventilator with round
spigots, a stove exchanger, a fan you already own. Then the key stops being a
filler and becomes a spacer.

Push every panel outward along its own face and every seam opens. The two
seam types have different folds, so one push opens them by different amounts,
and the push is set by whichever needs it most:

    to fit a 3 in duct                panels out {{chan.shift3}} in, dome +{{chan.grow3}}%
    a 4 in duct beside the bundle     panels out {{chan.shift4}} in, dome +{{chan.grow4}}%
    seams open at the ridge           {{chan.open4_t}} / {{chan.open4_w}} in

**A spacer is not free.** Moving every panel out makes the whole dome bigger:
more wood, more skin, a bigger pad. And every opened ridge needs a cap over it.
All of that, to carry air the plain channel was already carrying.

![As built, and with the seams opened for a four-inch duct.](plate-spacer.png)

## Printing the key in halves

The key is printed, and it is printed in halves. Split it down the middle of
the seam and each member carries its own half, screwed to its sawn face before
the panel is built. When two panels meet, the two halves close into one
channel. Nothing has to be threaded into a finished seam.

1. **Two profiles.** The dome has two seam types, so it has two key profiles:
   {{chan.profiles}} files, not {{dome.seams}}.
2. **Print after the frame has dried** (Chapter {{ch.green}}), to the V the
   dried wood actually has.
3. **Print in pieces** no longer than the printer's bed, assumed at
   {{chan.bed_mm}} millimetres: {{chan.per_stick}} pieces to a member, butted
   end to end.
4. **Bolts cross near the ridge**, where the V is narrowest. Route services
   through the wide belly below them.
5. **Print only the seams that carry something.** Every seam in the dome is
   {{chan.half_keys}} half-keys, {{chan.pieces}} pieces, {{chan.kg}} kilograms of
   PETG, about ${{chan.usd}} and {{chan.hours}} printer hours. One seam is
   {{chan.kg_seam}} kilograms, ${{chan.usd_seam}} and {{chan.h_seam}} hours. Cut
   solid keys from the offcuts for the rest.

![Each member carries its own half of the key.](plate-half-keys.png)

## Where the channels meet

The frame has no hubs, but the services need them. Channels meet at
{{chan.n5}} five-way and {{chan.n6}} six-way vertices, and at {{chan.nrim}} more
on the rim, where they drop to the pad.

As built, the Vs close to a point at each vertex, so each junction is a printed
**rosette** fixed to the inside of the vertex: a small box where a pipe turns
and a wire is joined, somewhere a hand can reach. With the four-inch spacer the
vertex opens into a hole about {{chan.node5}} inches across, and the rosette
becomes a node the channels plug into.

![A printed rosette inside a five-way and a six-way vertex.](plate-rosettes.png)

Two rules go with every rosette. **No pressure fitting inside a seam**: run the
PEX in one continuous length and make every joint in a rosette you can open,
because a hidden leak inside a wooden seam is the one failure this whole system
exists to prevent. And **whether a cable may run in this chase is your
inspector's decision**, not this book's.
