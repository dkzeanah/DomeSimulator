---
chapter: 55
title: Three Frequency, Five Eighths
strand: explain
status: draft
target: 2220
updated: 2026-10-03
---

# 55. Three Frequency, Five Eighths

<!-- concept: cabin_panel_method/two -->
<!-- concept: cabin_panel_method/tried -->

Most small timber domes built from bought plans are not split from logs and are
not hub-and-strut frames. They are **framed panels**: every triangle of the dome
is its own small frame of sawn sticks, built flat on a plywood jig, skinned in
the shop, and screwed to its neighbours on site. It is a good method with a
great many domes behind it, and anyone who builds the dome in this book should
understand it, because it is the road most people take.

![Two domes, framed two ways.](plate-panel-two.png)

**Why it is here.** The three-frequency five-eighths dome of framed panels is
a popular build, tried and true: a great many are standing. That makes it the
fairest comparison for the wedge dome, and this chapter and the next set it
beside it. Every length, angle and count is solved by this project's own
geometry (`two_v_demo/panel_method.py`), for a dome of this book's own
choosing, and drawn by this project's own software.

The reference dome, and the stock its sticks come from, are choices rather
than measurements, and they are declared before anything is claimed:

    {{pm.constants}}

## Three lengths, two kinds of point

<!-- concept: cabin_panel_method/sphere -->

Chapter {{ch.subdivide}} made this book's dome by cutting each face of the
icosahedron into four and pushing the new points out. Cut each face into
*nine* instead -- three to an edge -- and push every point out to the sphere,
and you have a **three-frequency** dome. It is rounder, its triangles are
smaller, and it has only three strut lengths. At {{pm.base_ft}} feet across
the base:

    A    {{pm.a_in}} in   ({{pm.a_mm}} mm)
    B    {{pm.b_in}} in   ({{pm.b_mm}} mm)
    C    {{pm.c_in}} in   ({{pm.c_mm}} mm)

Twelve points have five neighbours -- the icosahedron's own corners -- and every
other point has six. Chapter {{ch.hex}} explained why it must be exactly twelve.
The triangles round a five-way point make **pentagons**; all the others make
**hexagons**. That is the whole vocabulary of the dome: three lengths, two
kinds of point.

![Three chords: A, B and C.](plate-panel-sphere.png)

## Why five eighths

<!-- concept: cabin_panel_method/cut -->

A two-frequency sphere has a level ring of points at its middle, which is why
this book's dome is a clean hemisphere. A three-frequency sphere does not. Its
points sit at heights that never line up across the middle, so the cut goes
lower, to the ring of points nearest five-eighths of the way down.

That cut keeps **{{pm.panels}} triangles**: {{pm.pent}} that belong to
pentagons and {{pm.hex}} that belong to hexagons. Its height is
**{{pm.fraction}} of its width** -- a little under the five-eighths in its
name -- which for the reference dome is {{pm.height_ft}} feet.

The extra wall below the middle is the point of the cut. Near the base it
stands almost upright, so the floor near the edge is floor you can stand on.
A hemisphere's wall leans in from the floor; this book's dome answers that
with a riser wall under the shell (Chapter {{ch.raise}}), and the five-eighths
cut answers it with more of the sphere.

![Cut below the middle.](plate-panel-cut.png)

## A base that zig-zags

<!-- concept: cabin_panel_method/base -->

The price of the five-eighths cut is its base. The bottom edge is
{{pm.base_edges}} struts long and its corners do not lie on one level: they
alternate between two heights **{{pm.taper_mm}} mm apart** -- about
{{pm.taper_in}} inches. So the base sections, the boards the bottom panels sit
on, are not all alike. **{{pm.tapered}} must be tapered**, low at one end and
high at the other, and **{{pm.level}} sit level**.

Build that ring first. Set the base sections out on the deck, fasten them to
each other, pull the diagonals until they agree, and fasten them down. Every
panel above lands on this ring, and every error in it is passed up the dome.

![Ten tapered, five level.](plate-panel-base.png)

## Two panels, over and over

<!-- concept: cabin_panel_method/panels -->

Every panel in the dome is one of two triangles, and the jig is drawn for each
of them full size:

    {{pm.jig_table}}

The outlines are the *outside faces* of the panels -- the face the weather sees.
Nothing may stick out past them and nothing may fall short of them, which is
what the jig of the next chapter enforces.

![A pentagon panel and a hexagon panel.](plate-panel-panels.png)

## A floor the shape of the base

<!-- concept: cabin_panel_method/deck -->

A dome on a deck wants the deck to copy its base. A **radial deck** does: one
joist from the centre to every base corner -- {{pm.deck_sides}} of them -- and a
rim board along every base edge, {{pm.deck_rim_in}} inches long point to long
point, each end cut **{{pm.deck_rim_miter}} degrees** off square. That angle is
not looked up anywhere: it is half of the 360 degrees round the deck divided by
the number of sides, 180 over {{pm.deck_sides}}.

Under the joists, the girders follow the dome's own symmetry. A three-frequency
dome has five-fold symmetry about its top, so the girders make a ring of
{{pm.deck_girders}}, each end cut 180 over {{pm.deck_girders}},
{{pm.deck_girder_miter}} degrees, with a post under every joint where two
girders meet. Mark the centre on the ground, lay the girders out on it to place
the posts, set the post tops to a level line, then roll in the joists. The deck
is {{pm.deck_sqft}} square feet. Chapter {{ch.floor}} is about why the floor is
the other thing to get right, and Chapter {{ch.pad}} about where it stands.

![Joists to the corners, girders on the five-fold.](plate-panel-deck.png)
