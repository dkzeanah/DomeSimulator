---
chapter: 76
title: Twelve Ways to Dress One Frame
strand: howto
status: draft
target: 1900
updated: 2026-10-12
---

# 76. Twelve Ways to Dress One Frame

The Dome Creator ships twelve designs, and chapter {{ch.twelve}} toured them
at their own sizes -- a workshop, a glass loft, a trunk lodge, a hangar. Each
of those designs is really two things: a frame, and a way of dressing it.
This chapter keeps the cabin's frame and takes only the dressing: each
design's panels, its colours, its cladding and the foundation it stands on.
The frame stays the cabin's -- two-frequency, {{sty.struts}} struts,
{{sty.base_frame_mat}} -- so every difference below is the dressing alone.

## A style is a skin and a footing

Four things carry over from a design: the panel that fills the triangles,
the colours of panels and frame, up to three layers of cladding over the
panels, and the foundation. Nothing else does. Every row is a fresh build of
the cabin, priced, weighed and timed by the Creator's own model; every
picture is the Creator's own mesh in its own shader, standing where the
deck stands in the rest of this book.

## Timber and glass

![The cabin as the Timber Workshop.](plate-sty-timber-workshop.png)

The Timber Workshop's dressing is plywood on a concrete slab: a working
shell, plain inside and out, and the slab is most of its price. The Glass
Studio Loft fills every triangle with glass and stands on a wood deck, and
the glass is the most expensive common panel in the catalogue. The
Split-Log Homestead is the cabin bare -- plywood under cedar shakes on a
gravel pad -- the starting point of the whole Part.

![The cabin as the Glass Studio Loft.](plate-sty-glass-studio-loft.png)

![The cabin as the Split-Log Homestead.](plate-sty-split-log-homestead.png)

## Trunks, twinwall and hexes

![The cabin as the Whole Trunk Lodge - 20 ft.](plate-sty-whole-trunk-lodge--20-ft.png)

The Whole Trunk Lodge's dressing is canvas on gravel, which makes it one of
the cheapest cabins here, and one of the lightest: canvas weighs almost
nothing. The Grow Dome is twinwall polycarbonate on a grass pad -- a
greenhouse, and priced like one. The Hex Cell Pavilion fills the triangles
with hexagonal composite on a slab.

![The cabin as the Grow Dome.](plate-sty-grow-dome.png)

![The cabin as the Hex Cell Pavilion.](plate-sty-hex-cell-pavilion.png)

## Open frames and concrete

![The cabin as the Continuous Steel Arc Hangar.](plate-sty-continuous-steel-arc-hangar.png)

Two of the Creator's designs leave the triangles open: the steel arc hangar
and the rebar garden. On the cabin's frame that means a frame with nothing
in it, which is a pergola rather than a room. On a grass pad that is the
cheapest cabin in this chapter; on the hangar's concrete slab, the slab is
most of the price. The Concrete
Monocoque Form is the other extreme: form panels under a poured concrete
shell on a slab, the heaviest cabin in the book by a long way.

![The cabin as the Rebar Garden Dome.](plate-sty-rebar-garden-dome.png)

![The cabin as the Concrete Monocoque Form.](plate-sty-concrete-monocoque-form.png)

## Mirrors and a treehouse

![The cabin as the Woodland Hex Mirror.](plate-sty-woodland-hex-mirror.png)

The two woodland designs fill the triangles with mirror -- hexagonal tiles
in one, square in the other -- so that the dome all but disappears into
the trees around it. Mirror is the dearest panel the Creator stocks, and it
shows. The Treehouse Canopy Dome puts the cabin up a tree: hex composite
panels on a platform, and the platform costs more than everything above it
put together, ${{sty.tree_found}} on its own.

![The cabin as the Woodland Square Mirror.](plate-sty-woodland-square-mirror.png)

![The cabin as the Treehouse Canopy Dome.](plate-sty-treehouse-canopy-dome.png)

## All twelve, side by side

The same frame, dressed twelve ways, cheapest first:

    {{sty.styles}}

The cheapest dressing, the {{sty.cheap_style}}'s, comes to
${{sty.cheap_total}}; the dearest, the {{sty.dear_style}}'s, to
${{sty.dear_total}} -- {{sty.style_ratio}} times as much, on the same frame.
And line by line, so you can see which part of each style is doing the
spending:

    {{sty.style_lines}}

Two things stand out. The frame line is the same in every row, because the
frame never changed -- that is the point of the chapter. And the expensive
line moves from style to style: the panels are the biggest line in
{{sty.lead_panels}} of the twelve, the foundation in {{sty.lead_foundation}},
the cladding in {{sty.lead_cladding}} and the bare frame in
{{sty.lead_frame}} -- the ones so light that the frame is most of what there
is. The next chapter takes the menus one at a time to show exactly how much
each one can move.
