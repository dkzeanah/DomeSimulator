# Asset inventory — what exists, what to render, what to make

Everything the campaign already owns, where it lives, and the checklist of
what the Kickstarter page still needs. Paths are relative to the repo root.

## A. What already exists (hand these to the media LLMs as references)

### Video

| file | what it is |
|---|---|
| `deliverables/masterclass/stem-cell-dome-campaign-v5.mp4` | the 15-minute campaign film (v5 — the hull standard; v6 is authored in the lesson, see below) |
| `deliverables/masterclass/stem-cell-dome-campaign-vertical-v4.mp4` | the vertical/phone cut |
| `deliverables/masterclass/stem-cell-utility-core-build.mp4` (+ vertical) | the 7-hour utility-core shop build |
| `deliverables/masterclass/stem-cell-dome-campaign-v5-narration.md` | the full spoken script, for extracting copy |
| `deliverables/masterclass/stem-cell-dome-campaign-v4.srt` | subtitles for pulling quotes |

### Stills (film frames, decluttered — no labels burned in)

| folder | frames | use for |
|---|---|---|
| `two_v_demo_output/seed_pitch/` | 54 | the campaign film's own frames — the primary style reference |
| `two_v_demo_output/look/` | 11 | the dome interior as a room, with people — lifestyle |
| `two_v_demo_output/harvest/` | 37 | trees, felling, the log-to-wedge story |
| `two_v_demo_output/module_build/` | 9 | the utility core being built |
| `two_v_demo_output/dome_park/` | 36 | pads, park, the host story |
| `two_v_demo_output/kick/` + `kick2/` | 23 | early pitch visuals |
| `two_v_demo_output/wedge/`, `why_build/`, `world/` | 60 | the wedge method, economics, the dome lineup |

### Rendered figures (the v6 systems, from the solved model)

| file | shows |
|---|---|
| `deliverables/book/figures/hat-stack.png` | the frame wearing the patchwork blanket quilt and the translucent shower cap |
| `deliverables/book/figures/mast-floor.png` | the steel-core mast through the column, the clamped floor |
| `deliverables/book/figures/floating-dome.png` | the dome hung from three cables between trees |
| `deliverables/book/figures/front-frame-v3.png` and friends | film stills of the wedge dome, book plates |

### Documents the copy can be cut from

| file | what it holds |
|---|---|
| `docs/seed-dome-brief.md` | the whole product brief, including the new v6 section |
| `docs/dome-park-brief.md` | the host/pad business case |
| `docs/kickstarter/README.md` | the live numbers table |
| `deliverables/masterclass/stem-cell-dome-campaign-review.json` | the chapter-by-chapter film review |

## B. What the v6 film now contains (to render fresh on a GL machine)

The lesson `seed_pitch` now has **32 chapters, 895 seconds**, including the
four new ones — `cap` ("The standard article wears a shower cap"), `quilt`
("A $50 quilt, and a bigger cap for each"), `mast` ("A mast through the
column, and a floor that comes later"), `floating` ("Hang it between two
trees"). Render from the launcher: preset **stem-cell-dome-campaign.mp4**
(the v6 cut) or **stem cell dome -- one still per chapter** to look at
every shot first. That render becomes the hero material; until it exists,
the image prompts in `image-prompts.md` stand in for the new scenes.

## C. What the Kickstarter page needs — the production checklist

### Must have (page)
1. **Hero keyframe** — the shower-cap dome on a pad in a field, dusk (prompt H1).
2. **Hero video, 60–90 s** — see `video-outline.md`.
3. **The stem cell** — exploded view of frame → 40 bays → cap (prompts S1–S3).
4. **Stacking hats** — cutaway: frame, membrane, quilt, cap, in order (H2–H4).
5. **The blanket quilt** — clothing being quilted into the monolithic layer (Q1–Q3).
6. **The mast and the floor** — cutaway (M1–M2).
7. **The floating dome** — between trees, dusk or dawn (F1–F2).
8. **The pad / the host story** — serviced pad with dome landing (P1).
9. **The price story** — one clean graphic of the numbers table (G1).
10. **Tier graphics** — thumbnail per reward tier (T1–T8).
11. **Risks / engineer's note graphic** — a calm, honest card (R1).
12. **Header + social set** — campaign banner, square post, vertical story (C1–C3).

### Must have (photography — real, not generated)
13. The standing prototype: exterior from the field, the frame before
    skinning, the seam channel close-up, the core, the winch lift if it
    exists. **Photographs, not renders** — backers can tell, and the
    campaign's credibility rests on the one real build.
14. The builder: one portrait at the bench, one at the frame.

### Nice to have
15. 3–4 short GIFs: the 40 bays swapping panels; hats stacking one by one;
    the floor clamping to the mast; the dome being winched up.
16. One comparison still per honest caveat (tarp-look, moisture diagram).

Every generated image gets a prompt in `image-prompts.md`, keyed to the
letters above, so "H1" in this checklist names the exact prompt to run.
