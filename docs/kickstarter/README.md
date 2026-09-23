# Kickstarter campaign kit — how to use it

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
| stock in the frame / trees it comes from | 664 ft / 1.5 of the buyer's own |
| **standard article, shower cap — list** | **$18,522** |
| ... to build | $12,040 |
| ... per square foot of floor | $66.87 |
| the same dome, laminated hull — list | $27,581 |
| the cap saves, at list | $9,059 |
| cap stack: 0 / 3 / 7 blanket quilts | $3,265 / $3,471 / $3,748 |
| hull + bays: 0 / 3 / 7 quilts | $8,091 / $9,905 / $12,324 |
| **the cap saves at 3 quilts (materials)** | **$6,434** |
| one blanket-quilted layer | $50 (yard-priced: ~$670 at the first size) |
| the hull's cavity fills at | 4 layers |
| the seventh cap is bigger than the first by | 15.6% |
| thirty years, replacements in | soft $221/yr vs hard $330/yr |
| mast through the column | $622 |
| the dome's own floor (the upgrade) | $1,899 |
| floating rig (cables, saddles, winch) | $1,490 |
| **mast + floor + rig** | **$4,011** |
| the frame's weight, green pine | 2,478 lb |
| the host's pad | $6,240 |
| every saving lever at once (the floor price) | $15,599 |
| freight (regional, flat-packed) | $1,250 |
| fit-outs (same frame): Nursery / Gym / Studio | $26,922 / $28,761 / $28,902 |
| Guest house / Garage / Workshop | $31,186 / $32,093 / $34,218 |
| Home / Food / Advertiser / Sauna / Jacuzzi | $32,378 / $35,798 / $32,810 / $23,252 / $25,377 |

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
