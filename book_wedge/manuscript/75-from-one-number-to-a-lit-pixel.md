---
chapter: 75
title: From One Number to a Lit Pixel
strand: explain
status: draft
target: 2560
updated: 2026-10-05
---

# 75. From One Number to a Lit Pixel

<!-- concept: scratch/open -->
<!-- concept: scratch/pipeline -->

Every picture in this book started as arithmetic. There is no model file
behind any of them, no artist and no drawing: one number, a handful of
formulas, and a list of instructions for turning the answers into coloured
pixels.

Part 2 did the first half -- the shape. One irrational number places twelve
points (Chapter {{ch.phi}}); a division puts them on a sphere; halving every
edge makes more points in slightly the wrong place, and one push outward puts
them right, which is what makes the shape geodesic (Chapter {{ch.subdivide}}).
This chapter does the other half -- the picture -- because a builder who knows
how the drawing is made knows exactly how far to trust it. Seven stations, end
to end:

1. one number places twelve points;
2. a division puts them on a sphere of radius one;
3. every edge is halved;
4. the new points are pushed out to the sphere;
5. the shape becomes a mesh, because a graphics card draws only triangles;
6. a camera is placed, and the whole world is moved in front of it;
7. a divide, a stretch and a lighting sum turn all of it into a picture.

Every worksheet below was computed by the same code that drew the film it
comes from, while the frame was being drawn.

## A line with no thickness

<!-- concept: scratch/tube -->
<!-- concept: scratch/m_tube -->

The first surprise is that the shape cannot simply be drawn. A graphics card
draws triangles, and that is very nearly its whole vocabulary -- not even
lines. A strut in the model is two points with no thickness, so each one has
to be given a body: a tube of triangles wrapped round the line where the strut
goes. To build a ring round a line you need two directions square to it, and
the cross product hands you them.

    {{pix.w_tube}}

![Building one strut.](plate-strut-tube.png)

<!-- concept: scratch/winding -->
<!-- concept: scratch/m_normal -->

Every triangle also needs a front and a back. Without one it cannot be lit,
because lighting depends on the angle between the surface and the light, and
it cannot be hidden, because nothing could tell the inside of the dome from
the outside. The direction a face points -- its **normal** -- comes from the
cross product of two of its edges, and cross products care about order:
list the corners one way round and the normal points out, the other way and it
points in. One cross product answers three questions at once:

    {{pix.w_normal}}

That check is worth automating. A dome with one triangle wound backwards has a
hole in it that only appears from one angle.

<!-- concept: scratch/buffer -->
<!-- concept: scratch/m_buffer -->

Then the elegant structure goes away. Corners, edges, faces, the classes of
strut -- none of it survives the trip to the card. What the card gets is one
flat list of numbers, ten per vertex: three for where it is, three for which
way it faces, four for its colour, the fourth being opacity. Three vertices in
a row make a triangle, and that is the whole format.

    {{pix.w_buffer}}

That is smaller than a single photograph, and it is rebuilt and sent across
{{tt_pixel.fps}} times a second.

## Placing the camera

<!-- concept: scratch/world -->
<!-- concept: scratch/orbit -->
<!-- concept: scratch/m_eye -->

Before anything can be photographed, everything has to agree where it is. That
agreement is **world space**: one chosen origin and three directions at right
angles. Here, X and Y run along the ground and Z points up, the convention
surveyors and architects use; the units are whatever we decide, because the
geometry only cares about ratios.

A camera is placed the way a person thinks about one: how far round it is
(yaw), how high up (pitch), and how far back. Turning those into a position is
straight trigonometry:

    {{pix.w_eye}}

<!-- concept: scratch/view -->
<!-- concept: scratch/m_view -->

Now the idea that surprises people most: **a graphics card has no camera.** It
draws whatever sits in front of a fixed eye at the origin, looking down one
axis, always. So instead of moving the camera to a good spot, we move the
entire world so that the good spot lands on the origin. That is the **view
matrix**, and it is three directions at right angles and one offset:

    {{pix.w_view}}

The number with "e-17" in it is not a mistake. It says the two directions are
perpendicular to within the accuracy a computer can represent, which is as
perpendicular as anything gets.

<!-- concept: scratch/frustum -->
<!-- concept: scratch/m_projection -->

The camera cannot see everything. It sees a pyramid with its tip cut off -- a
**frustum** -- inside a field of view of {{tt_pixel.fov_deg}} degrees
vertically, nearer than a far limit of {{tt_pixel.far}} and further than a near
one of {{tt_pixel.near}}. Anything outside is thrown away before it costs
anything to draw. The projection matrix sets that up, and it is the matrix
people find hardest, because it does almost nothing:

    {{pix.w_projection}}

The projection matrix shrinks nothing. It loads each point's depth into a
fourth slot, *w*, so that the next step can do the shrinking.

## The divide that makes distance work

<!-- concept: scratch/clip -->
<!-- concept: scratch/screen -->
<!-- concept: scratch/m_pixel -->

Now the divide. Every point's x, y and z are divided by *w*, its distance from
the camera, so things twice as far away come out half as big. **That is
perspective.** Not a special effect: a division that had to happen anyway to
get the numbers into range. Everything the camera can see lands inside a cube
from minus one to plus one, and one stretch turns the cube into the frame --
flipped once, because screens count their rows from the top.

![The divide that makes distance work.](plate-the-divide.png)

Follow one point the whole way -- the very top of the dome:

    {{pix.w_pixel}}

The apex lands exactly halfway across the frame, which is the check: the camera
is aimed at the dome's centre, so its top has to sit on the vertical centre
line. Every label you have seen floating over a strut in this book's plates was
placed by exactly this calculation, run on the middle of that strut.

![One vertex, all the way.](plate-one-vertex.png)

## What hides what, and how bright

<!-- concept: scratch/depth -->
<!-- concept: scratch/m_depth -->

Two things want the same pixel. Which one wins? Real graphics cards do not
sort -- sorting thousands of triangles every frame is expensive, and two
triangles can overlap in ways that have no correct order at all. Instead every
pixel keeps a second number beside its colour: the depth of whatever is drawn
there. A new fragment arrives, one comparison decides it, and it works whatever
order the triangles come in.

![What hides what.](plate-what-hides-what.png)

There is a catch, and it explains a bug every 3D artist has seen:

    {{pix.w_depth}}

:::box correction
**This project got that catch wrong for years without noticing.** The film
renderer never asked for a depth precision, so it took the driver's default:
16 bits. With these near and far limits that cannot tell apart surfaces about
a metre apart at sixty metres out. Domes drawn on a dark plate never showed
it. The first film to put decks a few centimetres above their ground came out
in horizontal stripes across the whole site -- z-fighting, at true scale, with
nothing wrong in the geometry. The renderer now asks for 24 bits. Pushing the
near limit out is the cure the table recommends; asking for more bits is the
other, and it is the one taken, because every published film depends on the
lens it already has.
:::

<!-- concept: scratch/cull -->

And a free saving: on any closed shape, about half the surface faces away from
you at any moment, hidden behind the near half. So before doing any work on a
triangle the card checks its winding *on screen*, and one that comes out
clockwise is facing away and is dropped -- no depth test, no lighting, no
pixels. That is why the corner order mattered four sections ago.

<!-- concept: scratch/light -->
<!-- concept: scratch/m_light -->

Then brightness. All the shading in this book's plates comes from three
directions and the angles between them: where the surface faces, where the
light is, and where the eye is. The dot product of two directions of length
one is the cosine of the angle between them -- one facing, zero side-on,
negative behind -- so a single dot product answers the question a painter
answers by eye: is this surface turned toward the light?

    {{pix.w_light}}

Everything you read as shape in those pictures is three dot products and a
power. No shadows, no bounced light, no ray tracing.

![Three dot products and a power.](plate-three-dot-products.png)

<!-- concept: scratch/blend -->

Glass takes one thing back. The depth test let drawing order stop mattering;
transparency makes it matter again, because a see-through surface has to be
mixed with whatever is behind it, so whatever is behind has to be drawn first.
The renderer works in two passes -- everything solid, then everything
transparent with depth-writing switched off -- and the mixing is one line: the
new colour times its opacity, plus the old colour times one minus the opacity.
Opacity is that fourth number in every vertex, carried since the upload and
used only now.

## And then it does it again

<!-- concept: scratch/frame -->
<!-- concept: scratch/m_frame -->
<!-- concept: scratch/close -->

Everything above -- the tubes, the upload, the camera, three matrix
multiplications and a divide per corner, a depth comparison and a lighting sum
per pixel -- happens once for one picture. Then it all happens again for the
next, {{tt_pixel.fps}} times a second:

    {{pix.w_frame}}

That budget, {{tt_pixel.ms_frame}} milliseconds, is the reason for nearly
every decision in this chapter: why lighting is dot products rather than ray
tracing, why half the triangles are thrown away before shading, why depth is
one comparison instead of a sort. And because every scene in the films is a
pure function of which chapter it is and how far through, nothing accumulates
-- the same second of film renders identically on any machine, every time,
which is why the plates in this book can be checked by anybody who runs them.

That is the entire chain, from nothing: φ placed twelve points, two divisions
made them a geodesic sphere with two strut lengths, half of it counted into a
cut list; each strut became a tube, each triangle got a normal, all of it
flattened into a list of numbers; two angles placed a camera, three matrices
moved the world in front of it, one divide made distance work, one stretch
found the pixel, one comparison decided what hides what, and three dot products
decided how bright it was. No step in that chain is beyond somebody with a
calculator. The cleverness is not in any one formula. It is that they compose,
and that every single number can be checked.
