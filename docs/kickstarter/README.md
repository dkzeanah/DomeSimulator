# Kickstarter campaign kit — how to use it

> **Numbers in this file come from the model.** Regenerate them with
> `py -3.12 -m campaign` (writes `deliverables/campaign/campaign-page.md`)
> and check them with `py -3.12 -c "import campaign; campaign.validate_kit()"`,
> which fails on any figure the model does not produce.

This folder is the handoff pack for the stem-cell dome Kickstarter. The
campaign model is being tuned in the repo right now (Claude Code is working
alongside), so **every number in these files is a snapshot**: regenerate the
live table below any time with:

```bash
py -3.12 seed_model.py          # the quote, the levers, the mast and the rig
py -3.12 soft_shell.py          # the shower cap, the quilts, the comparison
```

The numbers on this page were generated from the model on 2026-09-20.

## The live numbers

| figure | value |
|---|---|
| the stem cell: dome across / tall | 19.42 ft / 9.71 ft |
| floor (ten-sided) / bays / members | 277 sq ft / 40 / 120 |
| **standard article, shower cap -- what you pay** | **$12,036** |
| ... what it costs us to build | $10,030 |
| ... our profit, 20% marked up on cost | $2,006 |
| ... per square foot of floor | $43.45 |
| the same dome, laminated hull | $21,513 |
| the hull is dearer by | $9,477 |
| one blanket-quilted layer | $50 |
| ... with the bigger cap it forces | $69 |
| ... in t-shirts | 132 |
| watertight layers in the building | 1 -- the outer cap |
| mast + floor + rig | $4,011 |
| the host's pad | $6,240 |
| dome + ground, standing | $18,276 |
| **the campaign goal** | **$110,000** |

The honest lines the campaign says out loud (and should keep saying):
the cap is not structural (uplift rides the anchors and the frame), the
outer layer is sacrificial (8 years, replaced by design), fabric between
two impermeable layers is a moisture problem the seam duct has to answer,
it looks like a tarp to some planners, and **every structural rating —
mast, ring, hoist, cables, trees — is an engineer's number, not ours**.

## What each file is for

| file | give it to |
|---|---|
| `asset-inventory.md` | yourself, first: what media exists in the repo, what to render, what to make |
| `campaign-page-outline.md` | ChatGPT/Gemini as the page skeleton to write copy over |
| `video-outline.md` | the video editor + Gemini/Veo for the hero cut |
| `image-prompts.md` | **Gemini (Imagen) and ChatGPT image generation** — one prompt per asset, in the style of the films |
| `tiers-faq-risks.md` | ChatGPT to draft reward tiers, FAQ and the risks section |

## The visual style everything must match

The films this campaign already shipped have a look, and every new image
should be able to sit next to a frame of them without a seam. In one
paragraph, for pasting into any image model:

> Flat-shaded 3-D render of a timber geodesic dome, the style of a
> technical studio visualization: matte Lambert-shaded polygon surfaces,
> muted palette of sawn pine, bark brown, warm grey and one accent colour,
> clean uncluttered background in paper-white or deep charcoal, camera in a
> gentle three-quarter view slightly above the building, soft even
> lighting, no lens flare, no depth-of-field blur, no photorealistic
> texture grain, no text or labels anywhere in the frame. The dome is a
> 2V geodesic hemisphere of forty triangular bays on a ten-sided base,
> built from wedge-shaped timber struts, each about six feet long.

Style-reference media already on disk, to hand the image/video models as
references: `two_v_demo_output/seed_pitch/` (54 stills of the campaign
film), `two_v_demo_output/look/` (11 interior set stills),
`deliverables/masterclass/stem-cell-dome-campaign-v5.mp4` and its
`-vertical` twin, `stem-cell-utility-core-build.mp4`, and the three newest
renders of the v6 systems: `deliverables/book/figures/hat-stack.png`,
`mast-floor.png`, `floating-dome.png` — the shower-cap dome, the mast and
floor, and the floating dome drawn from the solved model itself.

## Ground rules for the LLMs you pass this to

1. **No invented numbers.** Every figure must come from the table above or
   be marked clearly as a placeholder for the owner to fill.
2. **No invented claims.** Nothing structural is rated here; the phrase
   "the engineer's number" must survive into every risk section.
3. **Voice.** Builder's voice — short declarative sentences, concrete
   figures, no "game changer", no "revolutionary", no "delve".
4. **The three kinds of claim stay apart:** known geometry (computed),
   tested construction (the prototype), design possibility (the floating
   dome, the iris, the network).
