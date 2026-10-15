---
section: back
title: From Number to Pixel
status: draft
target: 4200
updated: 2026-10-03
---
# From Number to Pixel

*How a strut length becomes a picture: what the films do thirty times a second, and why each step is the only one available*

The films that come with this project are not recordings of a building. They
are drawn: the dome on screen is the same solved model the tables in this
book are computed from, turned into triangles by the same programs and
photographed by a camera that exists only as three matrices. That is worth a
chapter of its own, for two reasons.

The first is that a reader who can see how the picture is made can check it.
When a film says a member is 72 inches, the model on screen is that member;
when it says the seam is 27 degrees, the picture is the geometry that says so.
Nothing in a film is an artist's impression, because there is no artist.

The second reason is more useful to a builder than it looks. Every step below
is a version of a step this book has already taught you. A strut is a line
with no thickness that has to be given a body — the same problem as a member
that has to be given a joint. A surface has to be told which way it faces,
or it disappears — the same problem as a pinwheel that has to run the same way
round every panel. A frame that has to be rebuilt from scratch every frame,
with nothing carried over, is the same discipline as a build whose every
measurement comes off the same model. This is the method, applied to
pictures.

## A strut is not a line

A graphics card draws triangles and nothing else. It cannot draw a line with
thickness, and a member in a dome is exactly that: two points with no width
between them. So the line has to be given a body.

Take the strut's two ends, `a` and `b`. Its direction is the difference
between them, normalised. Now pick any direction that is not parallel to the
strut, and take two cross products:

    d = (b - a) / |b - a|        the strut's direction
    s = d x t                    a direction at right angles to d
    u = d x s                    and a third at right angles to both

The cross product of two directions returns a third at right angles to both,
which is exactly what a ring needs: `s` and `u` span the plane the tube's
cross-section lives in. Walk a ring of {{pixel.sides}} points around the axis
at each end, stitch the two rings together, and the line has become a tube.

One strut is {{pixel.tri_strut}} triangles: {{pixel.sides}} side quads, each
split into two triangles, plus two end caps. The hubbed frame on screen is
{{pixel.struts}} strut tubes, which is {{pixel.tri_frame}} triangles of
frame. Every visible member in every film in this project is a tube of
{{pixel.sides}} flat sides built by two cross products, and it is flat-sided
rather than round on purpose: {{pixel.sides}} sides is enough to read as a
round member at film resolution, and the lighting on a faceted tube is what
makes the member look like timber rather than plastic.

Which way round the ring is wound decides which way each triangle faces, and
that is the next problem.

## Which way a triangle faces

A triangle has a front and a back, and the difference is the order its corners
are given in. Take the two edges that meet at the first corner, cross one with
the other, and you get a vector at right angles to the face: the *normal*.
Its length, halved, is the triangle's area. Its direction says which side is
front.

This matters because a graphics card is allowed to throw away any triangle
facing away from the camera — that is how it draws a closed surface at half
the cost — and it decides by watching the winding order after projection. Get
the winding wrong on a panel and the panel either vanishes or turns the dome
inside out. Get it wrong on one panel of forty and you have a hole in the
building that only shows up from certain angles.

So every face in the model is written with its corners in the same order, and
the films' own model checks the normals against the outward direction: for the
reference triangle the dot product of the normal with the outward direction is
better than 0.99, which is the arithmetic way of saying "this face is looking
outwards". That is the same idea as the pinwheel chapter's rule that every
panel runs the same way round: a building whose members disagree about which
way is out is a building that will not close, and a model whose triangles
disagree is a picture with holes in it.

## One frame, counted

By this point the model is not points and edges. It is one flat list of
numbers, and there are ten of them for every corner:

    position  x y z     where the corner is
    normal    x y z     which way its surface faces
    colour    r g b a   what shade it is; a is opacity

Ten floats at four bytes each is {{pixel.bytes_vertex}} bytes a vertex. The
dome standing in the films is {{pixel.floats}} floats, which is
{{pixel.vertices}} vertices, which is {{pixel.tri_dome}} triangles, which is
{{pixel.bytes}} bytes — {{pixel.kb}} kilobytes. Smaller than one photograph.

No corner is shared between triangles: three fresh vertices per face. That
costs memory and buys the freedom to give every face its own flat normal and
its own colour, which is why the members in the films are flat-shaded and why
each bay can be lit differently. And that whole buffer is rebuilt and
re-uploaded {{pixel.fps}} times a second, because nothing is stored between
frames: every scene is a pure function of its chapter and its progress, so
the same second of film renders identically on any machine, every time.

![One frame, counted off the renderer's own buffer.](../../deliverables/book/figures/pixel-budget.png)

## The camera is a matrix

There is no camera on a graphics card. There is a fixed eye at the origin
looking down one axis, and everything the card draws is drawn there. A
"camera" is therefore an illusion maintained by two matrices that move the
*world* instead of the eye, and a third that turns depth into size.

**Placing the eye.** {{pixel.fov_deg}} degrees of vertical field of view, a
yaw, a pitch and a distance:

    eye = target + d (cos p cos y, cos p sin y, sin p)

**The view matrix** builds an orthonormal frame from that eye — forward,
right and up — and moves the world so that the eye sits at the origin looking
down −z. Three rows of three numbers and a translation, and the camera exists.

**The projection matrix** arranges the divide that makes distance real. For a
vertical field of view of {{pixel.fov_deg}} degrees:

    f = 1 / tan(fov / 2)

and the matrix carries `f`, the aspect ratio, and the near and far planes —
{{pixel.near}} and {{pixel.far}} world units in these films. Its last row is
the important one: it copies −z into `w`. Nothing has been divided yet. The
matrix has only arranged for the division to happen, which is the single
cleverest thing in the whole pipeline.

**The divide** is where perspective comes from. Divide x, y and z by w, and
w *is* depth, so anything twice as far away comes out half as big. What falls
out is normalised device coordinates in a −1..+1 cube, and anything outside
the cube is not drawn — a frustum, a pyramid with its tip cut off, which is
what "the camera can see" means.

**Landing on a pixel.** Add one, halve, multiply by the frame's width; and for
the vertical axis, subtract from one first, because screens count rows
downward:

    px = (ndc_x * 0.5 + 0.5) * width
    py = (1 - (ndc_y * 0.5 + 0.5)) * height

The apex of the reference dome lands at a specific pixel — not
approximately, exactly — and the films' own self-test checks that number.

## What hides what, and why that is a buffer

A building drawn as triangles has a front and a back, and the triangles
arrive in whatever order the model lists them. Something has to decide which
surface is in front of which.

The films do not sort anything. Every pixel remembers how deep the nearest
thing drawn there was, and a new fragment is kept only if it is nearer. The
result is order-independent — the picture is right no matter what order the
triangles arrive in — and it costs one number per pixel.

Two consequences worth knowing, because both are visible in the films if you
look for them. **Z-fighting**: the divide by w squashes depth non-linearly, so
almost all of the precision in a {{pixel.near}}-to-{{pixel.far}} range is spent
on the first fraction of a unit, and two far surfaces can round to the same
depth and flicker against each other. Pushing the near plane further out is
the fix. And **transparency**, which needs the order back: a transparent
surface has to be mixed with what is behind it, so the films draw the solid
building first, then the transparent parts with depth-writing turned off, then
swap the buffers.

## Why the lighting is three dot products

A frame has {{pixel.pixels}} pixels and {{pixel.fps}} frames a second, which
is up to {{pixel.runs_s}} million shader runs a second. A frame's whole budget
is {{pixel.ms_frame}} milliseconds, which is {{pixel.us_triangle}}
microseconds for each of {{pixel.tri_dome}} triangles if every one were
visible. There is no room for anything clever, so the shading is three dot
products and an ambient floor:

**Diffuse.** `max(n · l, 0)`: how squarely the surface faces the light. A
member's flat sawn face catches the light differently from its bark side, and
that difference is what tells a reader which way a member is turned.

**Specular.** `max(n · h, 0)` raised to {{pixel.specular_power}}, with `h` the
direction halfway between the light and the eye. A high exponent means a
small, hard highlight — the shine that makes a cut face read as cut.

**Rim.** `(1 - max(n · v, 0))` raised to {{pixel.rim_power}}: bright at the
silhouette, which separates one member from the one behind it without any
outline drawing at all.

Plus an ambient floor of {{pixel.ambient}} so nothing is ever pure black. No
shadows, no bounced light, no ray tracing. Every one of those would be
better and none of them fits in {{pixel.ms_frame}} milliseconds at
{{pixel.fps}} frames a second, which is the sort of trade this book makes
about wood as well: the simplest thing that is honest about the shape.

## What this has to do with building

Everything in this section is a solution to the same class of problem the
rest of the book solves in timber.

A member with no thickness needs a body — and so does a joint with no
connector. A face has to declare which way is out — and so does a wedge in a
pinwheel. A depth buffer makes order irrelevant so that a device with no
patience can draw a building correctly — and so does a jig, which makes the
order you cut things in stop mattering. Thirty frames a second with nothing
carried over is a pure function of the model, which is the same guarantee the
book's tables give: change the tree, re-run the build, get *your* numbers
rather than the author's.

The films are not decoration on the method. They are the method, rendered —
which is why this book's figures could all be regenerated by a reader with the
software chapter's commands, and why a film's number and a table's number are
the same number.
