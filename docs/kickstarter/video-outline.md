# Video outline — the hero cut, and the full campaign film

> **Numbers in this file come from the model.** Regenerate them with
> `py -3.12 -m campaign` (writes `deliverables/campaign/campaign-page.md`)
> and check them with `py -3.12 -c "import campaign; campaign.validate_kit()"`,
> which fails on any figure the model does not produce.

## A. The 60–90 second hero video (for the top of the page)

Structure, in order. Give this to the editor and to Veo/Gemini as the
shot list; every number is from the live table in `README.md`.

| # | seconds | shot | on screen / narration |
|---|---|---|---|
| 1 | 0–6 | H1: the cap dome on its pad at dusk | "We make the stem cell. You build on it." |
| 2 | 6–16 | S1: the bare frame, forty bays, slow orbit | "Forty triangles. A hundred and twenty wedge struts. No hubs." |
| 3 | 16–26 | S2: bays swapping panels — mirror, skylight, door | "A gym on Monday, a guest room on Friday." |
| 4 | 26–38 | H2: the hat stack exploding — frame, breather, quilt, cap | "A dome is a head, and it wears hats. One waterproof layer, on the outside." |
| 5 | 38–48 | Q1→Q2→Q3: the quilt being stitched, tucked on, capped | "A fifty-dollar blanket quilt. A bigger cap for every layer." |
| 6 | 48–60 | M1→F1: the mast, the floor clamping on, the dome hanging between trees | "A floor you buy later. A mast that hoists the whole thing. And if you have the trees — it floats." |
| 7 | 60–72 | G1: the price cards — $12,036 vs $21,513 | "Twelve thousand. Ten to build, two is our profit. The hull version is twenty-one and a half. The pad belongs to the host." |
| 8 | 72–82 | P1: the empty pad, then the dome landing on it | "You bring the home. The ground stays somebody else's." |
| 9 | 82–90 | H1 again, now with the door light on, camera pulling back | "Every figure in this film came out of a model you can run yourself — including the ones that argue against us." |

Cutting note: the honest caveats must survive as one on-screen line in
shot 6 ("design possibility — the loads are the engineer's number") or
the video undercuts the risks section of the page.

## B. The full v6 campaign film (the 32-chapter cut)

The lesson `seed_pitch` now contains 37 chapters over 1063 seconds. The edit order for the full cut is:

1. Open and the stem cell chapters (existing, with the v6 numbers in the
   open and ladder narration).
2. The shell and bay chapters (existing).
3. **`cap` — The standard article wears a shower cap** (new).
4. **`quilt` — A $50 quilt, and a bigger cap for each** (new).
5. **`mast` — A mast through the column, and a floor that comes later**
   (new).
6. **`floating` — Hang it between two trees** (new).
7. **`head` — A dome is a head, and it wears hats** (new: the Arctic
   watch, placed before `cap` so the cap chapter lands).
8. The honest chapters, then the campaign ending -- **`invoice`**,
   **`goal`**, **`next`**, **`three`** -- and the close (re-spoken to $12,036 list, $10,030 build, $43.45/sq ft, $21,513
   hull, $4,011 mast+floor+rig).

Render from the launcher: preset **stem-cell-dome-campaign.mp4** builds
the whole film with narration; **stem cell dome -- one still per chapter**
gives one frame per chapter to review before committing to the render.

## C. The vertical (9:16) companion

Same hero structure re-timed for phone: shots 1, 2, 4, 6, 7 and 9 hold;
the bay-swap shot becomes a quick two-cut; all numbers spoken on screen
as overlays. The v4 vertical cut exists at
`deliverables/masterclass/stem-cell-dome-campaign-vertical-v4.mp4` as the
layout reference.

## D. B-roll bank for the editor

Every still folder in `asset-inventory.md` section A, plus the three v6
renders (`hat-stack.png`, `mast-floor.png`, `floating-dome.png`) — the
editor can cut the hero entirely from these before the GL render exists.
