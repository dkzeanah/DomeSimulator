---
chapter: 14
title: Green Wood Moves, and a Split Moves Least
strand: explain
status: draft
target: 1640
updated: 2026-09-30
---

# 14. Green Wood Moves, and a Split Moves Least

A tree is mostly water. The frame of this dome comes off the saw weighing
{{money.frame_weight}} pounds in green pine, and a good part of that weight is
going to leave through the surface of the wood over the next few months,
whether you plan for it or not.

When water leaves wood, the wood gets smaller. Not evenly: wood shrinks about
twice as much going round the growth rings as it does going across them. For
the pine this book prices, green to bone dry, that is {{wood.shrink_t}} percent
round the rings and {{wood.shrink_r}} percent across them.

That one fact explains two things about the method. It explains why a split
wedge checks less than a sawn, squared timber. And it explains why the key is
the last thing you make.

![Two sawn faces meeting at the ridge and opening to the room: the V the key fills.](plate-the-vee.png)

## Why a boxed heart tears and a wedge does not

Picture the end of a squared beam cut with the pith in the middle: a boxed
heart. As it dries, every ring wants to get shorter round its circumference,
and it cannot, because the ring is a closed loop held at full size by the wood
inside and outside it. The stress builds until the wood gives, and it gives
along a radius. That split running in from the surface is a check.

Now picture one of this book's wedges. It was split along a radius to begin
with. Its rings are not closed loops any more; they are arcs, each one
free at both ends. When an arc wants to get shorter it simply does, and the
two sawn faces swing toward each other a little. The wedge **closes its own
angle** instead of tearing.

The tree held the tolerance when you split it. It keeps holding it while the
wood dries.

## What the key sees

Here is the consequence you have to plan for.

A wedge dried from green down to {{wood.mc}} percent moisture closes from
{{cut.sector}} degrees to {{wood.sector_dry}}: {{wood.close}} degrees. The V in
every seam is the sector angle less the fold between the two panels (Chapter
{{ch.pinwheel}}), and each of the two members turns its face away by half of
that. So the V opens by the whole of it:

    the tighter V, cut green        {{wood.gap_green}} deg
    the same V, once dry            {{wood.gap_dry}} deg
    width at the room side, green   {{wood.open_green}} in
    width at the room side, dry     {{wood.open_dry}} in

The width at the room side barely changes, because the faces also get shorter
as the wood shrinks across the rings: {{cut.depth}} inches deep becomes
{{wood.depth_dry}}. What changes is the **tilt**. Each face swings
{{wood.tilt}} inches at the room side, so a key cut to fit the green V now
touches along one edge and rocks.

That is small, and it is enough. A key is only worth its space if it bears on
both faces for its whole depth.

**The rule: dry the frame, then make the keys.** Split and build green if you
must, because green wood cuts and splits more easily. But print or cut the keys
last, to the V the dried frame actually has, and bolt the seams up after the
frame has come down to its working moisture. The channel's own air is what
gets it there.

## How long, and how much water

Drying time goes roughly with the square of the thickness the water has to
travel through. A wedge's thickest point is the biggest circle that fits inside
its sector, {{wood.thick}} inches across, against the {{cut.trunk}}-inch log it
came from. So:

- a wedge dries about **{{wood.faster}} times faster** than the round log would;
- and about **{{wood.slower}} times slower** than a two-by, which is thinner still.

Splitting is, among other things, a way of drying a log.

The water it gives up, green down to {{wood.mc}} percent, is about
{{wood.water_lb}} pounds: {{wood.water_gal}} gallons, from the frame alone.
All of it has to leave through the surface of the wood and then leave the
building. If the frame is already standing when it does, that water is in the
seams, and Chapter {{ch.dewpoint}} is about moving it.

Wood below {{clim.mc_wet}} percent is what lumber grading calls dry: under
that line, rot cannot get going. Above it, it can. Framing indoors settles to
about {{clim.mc_target}}.

## Drying the stack

1. **Stack the wedges off the ground**, on bearers, in the shade, with the
   round face up so the rain that gets in runs off the bark side.
2. **Sticker every layer.** Put thin spacers across the stack at every layer
   so air reaches all three faces. A wedge laid sawn face on sawn face dries
   from one side and cups.
3. **Cover the top, not the sides.** A roof over the stack keeps rain off; open
   sides let the wind through, and the wind does the drying.
4. **Seal the end grain.** Water leaves end grain many times faster than it
   leaves the side, which is why logs check from the ends. A coat of wax or
   paint on each end slows it to match the rest.
5. **Buy a moisture meter.** It is the cheapest tool in the book and the only
   one that tells you when to make the keys.

The figures in this chapter use handbook shrinkage for pine, and they are
declared as such:

    {{wood.constants_table}}
