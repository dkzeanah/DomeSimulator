# Image rendering prompts — Gemini (Imagen) and ChatGPT image generation

One prompt per asset, keyed to the checklist in `asset-inventory.md`
("H1", "S1" ...). Each prompt is self-contained: paste it as-is, then
attach the style reference listed under it. The numbers are the campaign's
live figures — if a prompt asks for an image containing a price, hand the
model the value from `README.md` yourself, never let it invent one.

## The style block (prepend to any prompt, or paste once as a style)

> Style: flat-shaded 3-D technical render, matte studio visualization of a
> timber geodesic dome. Lambert-shaded polygon surfaces, muted palette —
> sawn pine, bark brown, warm grey, charcoal, with one restrained accent
> colour. Clean background: paper-white or deep charcoal, no environment
> clutter. Gentle three-quarter camera, slightly above the building.
> Soft even lighting, no lens flare, no depth-of-field blur, no
> photorealistic texture grain, no film grain, no watermark, no text, no
> labels, no captions anywhere in the frame. The dome is a 2V geodesic
> hemisphere of forty triangular bays on a ten-sided base, built from
> wedge-shaped timber struts about six feet long, hubless — the sticks lap
> past each other at the vertices instead of meeting in metal hubs.

Style-reference media to attach alongside: any five stills from
`two_v_demo_output/seed_pitch/`, plus the relevant rendered figure named in
each prompt.

---

## H1 — the hero keyframe

Subject: a single 2V geodesic timber dome standing on a low circular
wooden pad in a wide flat field at dusk. The dome wears its shower cap:
the timber frame is faintly visible through a translucent rain-slick
outer skin that catches the last light; the skin is pulled tight and
strapped at the ten base corners with webbing straps to ground anchors.
Three tall trees stand in the far background, softly out of focus but
present, hinting at the floating version. Warm porch-light glow leaks
from one open doorway bay at the base. Camera: three-quarter view,
slightly above, the building filling the lower two-thirds of the frame,
sky occupying the top third with a thin amber horizon band.
Palette: deep blue-grey dusk sky, warm pine, the cap catching pale
blue-white highlights. Mood: quiet, self-reliant, finished.
Style reference: `deliverables/book/figures/hat-stack.png` + any two
`seed_pitch` stills.

## H2 — stacking hats, the exploded sequence

Subject: one dome shown as four separated layers floating in vertical
explosion, bottom to top: (1) the bare timber frame, forty triangular
bays, wedge struts; (2) a thin semi-transparent grey membrane; (3) a
thick quilted layer made of visible fabric patches — denim, flannel red,
mustard, sage, cream, brown, teal — stitched together along the triangle
edges; (4) the rain-slick outer cap, a smooth translucent skin with ten
webbing straps. Each layer hovers a hand's width above the one below,
aligned, so the reader sees the stack order in one image. Camera: three-
quarter, slightly above, soft white background.
Style reference: `deliverables/book/figures/hat-stack.png`.

## H3 — the cap is a bag (the growth image)

Subject: the same dome three times in a row, small to large hats: the
bare frame on the left, the frame with one thin quilt and a snug cap in
the middle, the frame with four thick quilts and a visibly larger,
puffier cap on the right. The caps grow in diameter as the stack grows;
a dotted line traces the same base ring through all three, showing the
frame never changed. Caption-free; the growth must read from the
silhouettes alone. Camera: straight-on side elevation, paper-white
background.
Style reference: `hat-stack.png`.

## H4 — under the cap (the moisture honesty diagram)

Subject: a cutaway cross-section through the dome wall, drawn as a clean
technical diagram in the same flat-shaded style: from inside out — wedge
strut (brown triangle section), outer wood panel, monolithic membrane
(grey line), quilted fabric layer (patchwork colours, slightly puffy),
rain-slick cap (blue-grey line). A small blue arrow of water drips down
the outside of the cap and off the hem; a small red arrow inside the
fabric layer shows a dew point, with a thin dotted path running down to
the base — the seam channel. No text; the arrows must tell the story.
Style reference: `hat-stack.png`.

## S1 — the stem cell, bare

Subject: the bare stem-cell frame, no skin at all: forty triangular bays,
120 wedge-shaped struts, hubless vertices where the sticks lap past each
other, standing on the ten-sided base ring on a paper-white background.
Every strut visibly a wedge — wide bark face outside, narrow pith edge
in. Camera: three-quarter, slightly above. The clearest single image of
"this is the product".
Style reference: any `seed_pitch` still showing the bare frame.

## S2 — forty bays, one decision

Subject: the same frame, half of its bays filled with different panel
types in a deliberate patchwork — one bay a mirror panel, one a skylight,
one a louvre vent, one a door, the rest plain wood — demonstrating that
the function of the building is a set of panels. The contrast must look
intentional, like a colour key, not like damage. Camera: three-quarter.
Style reference: `seed_pitch` stills from the "stemcell" chapter.

## S3 — the frame from the buyer's trees

Subject: a felled pine trunk lying in a forest clearing in the
foreground, with the same trunk's story told by the frame behind it: a
partly-assembled dome of wedge struts, a split section of log showing the
wedge-shaped cross-sections fanning out like a pie, and a neat stack of
cut wedges. Dappled daylight, forest greens and browns, the same
flat-shaded style. Camera: low three-quarter view.
Style reference: `two_v_demo_output/harvest/` stills.

## Q1 — quilting the blanket layer

Subject: a close view of the monolithic quilt being made: many panels of
recycled clothing — denim jeans, flannel shirts, a mustard sweater, a
checked blanket — already cut into triangular patches and stitched
together edge to edge into one large curved fabric sheet, lying over a
workbench, half of it draped over a small section of the dome frame
behind. Needle and thread mid-stitch on one seam. Warm workshop light,
wood surfaces. Camera: eye-level close, shallow framing.
Style reference: `hat-stack.png` for the patch colours.

## Q2 — the quilt goes on top of the frame

Subject: the dome frame with a quilted fabric layer pulled over its upper
half like a blanket being tucked in: the patchwork fabric follows the
triangles of the frame, sagging slightly between the struts, its lower
edge hanging loose where two hands (builder's hands only, no face) pull
it down toward the base ring. The membrane under it just visible at the
loose edge. Camera: three-quarter, slightly above.
Style reference: `hat-stack.png`.

## Q3 — the cap goes over the quilt

Subject: the same dome a moment later: the rain-slick cap — a smooth
translucent skin with a hem and grommets — being drawn down over the
quilted frame from the apex, like pulling a shower cap over a head. The
quilt's patches show through it, softened. Two hands at the hem, webbing
straps trailing from the ten base corners. Camera: three-quarter.
Style reference: `hat-stack.png`.

## M1 — the mast and the floor, cutaway

Subject: a cutaway of the dome revealing its centre: a vertical mast
running from the floor port up through the middle of the dome and out
through the apex, timber-clad outside with a steel core visible at the
cut; a circular wooden floor deck hangs on the mast at working height,
ten thin steel spokes running from a steel hub ring around the mast out
to the base ring, wooden deck boards over the spokes, a low rail at the
edge. The utility column's chase is visible around the mast with small
pipes and a cable running inside it. Camera: three-quarter cutaway,
paper-white background.
Style reference: `deliverables/book/figures/mast-floor.png`.

## M2 — the floor is the upgrade

Subject: two domes side by side on the same pad: on the left, the bare
dome standing directly on the pad deck; on the right, the identical dome
with its own wooden floor now clamped to the mast, hovering a couple of
feet above the pad, so the pad's deck shows underneath. The message is
"bought later, bolts on" — the frames must be identical. Camera: side
elevation pair, paper-white.
Style reference: `mast-floor.png`.

## F1 — the floating dome

Subject: the dome suspended between three tall trees, several feet off
the ground: three steel cables run from a single forged ring at the
apex out to padded slings around three trunks — no bolts in the trees.
Under the dome, its own wooden floor hangs from the mast, a soft rope
ladder or light stair dropping from the floor's edge toward the ground
below. Forest clearing, dawn light, mist low on the ground, birds'
-eye-ish three-quarter camera. The mood is serene and slightly
impossible — a drawing made real.
Style reference: `deliverables/book/figures/floating-dome.png`.

## F2 — the winch moment

Subject: the same clearing a moment earlier in the story: the dome
lifted halfway to its hanging height, cables already run to the trees, a
brake winch on the ground with the lifting line up through the apex
ring, the whole building a few feet in the air with its floor hanging
below it. One builder's hand on the winch handle. Mid-morning light,
forest greens.
Style reference: `floating-dome.png`.

## P1 — the pad, the host's product

Subject: a serviced circular wooden pad in a field: low deck on piers, a
small electrical pedestal at the edge, a stub of water pipe and a drain
port at the centre, a hatch to under-floor storage, a short gravel spur
running off-frame. No dome on it — the pad is the product. Camera:
three-quarter from a low drone angle, paper-white sky, soft shadows.
Style reference: `two_v_demo_output/dome_park/` stills.

## G1 — the price story, one graphic

Subject: a clean flat graphic, not a scene: two side-by-side cards in
the campaign palette (charcoal card on paper-white). Left card: a line
drawing of the shower-cap dome with the list price beneath it. Right
card: the same dome with a rigid hull, a higher price. Between them a
downward arrow and the saving. The exact dollar values come from the
live numbers table in `README.md` — paste them in; the image model must
not invent them. No other text.
Style reference: none — this is a flat design graphic; ask the model to
match the campaign palette.

## T1–T8 — tier thumbnails

Eight small square graphics, one per reward tier, each a simple
flat-shaded icon in the campaign palette on paper-white: (T1) a
triangular bay with a wedge strut — the digital plans tier; (T2) a
blanket patch square with a needle — the quilt kit; (T3) a shower-cap
dome silhouette — the cap tier; (T4) a mast with a floor disc — the
mast and floor tier; (T5) a dome between three trees — the floating
rig; (T6) the full dome on a pad — the dome itself; (T7) a pad with a
pedestal — the host tier; (T8) a dome wearing a mirror panel and a
skylight — the fit-out tiers. One subject per square, no text, no
background detail.
Style reference: any `seed_pitch` still, shrunk in your head to an icon.

## R1 — the engineer's note card

Subject: a calm, honest flat graphic: a steel cable under tension, a
mast in compression, a tree, and a small warning chevron, drawn in the
campaign palette on charcoal, with generous whitespace. The image alone
must say "this part is the engineer's" — no text. Used beside the risks
section.
Style reference: none; flat design graphic.

## C1–C3 — header and social set

(C1) Campaign banner, 16:9: the hero keyframe H1 widened, dome on the
right third, open sky on the left two-thirds for the title text. (C2)
Square social post, 1:1: the hat-stack explosion H2 cropped square. (C3)
Vertical story, 9:16: the floating dome F1 with the ground mist filling
the bottom third for text. All three inherit H1's palette and light.

---

## Negative prompt, for any generator that takes one

> photorealistic texture, film grain, lens flare, depth of field, blur,
> watermark, signature, text, captions, labels, people's faces,
> distortion of the geodesic pattern (the dome has exactly forty
> triangular bays and a ten-sided base), extra domes, clutter, saturated
> colours, glossy reflections, brick or concrete structures.
