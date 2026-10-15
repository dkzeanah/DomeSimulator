# Stem-cell dome -- campaign image prompts

Generated 2026-09-25 by `campaign_prompts.py` from `seed_model` and `kickstarter`. **Do not edit by hand** -- change the model or the scenes in the script and regenerate.

87 assets. Each block below is one paste into Gemini: copy the **Prompt** exactly. The **Overlay** line is set in type afterwards (Canva, Figma, the web app) -- image models garble figures, so no prompt contains a number, and every number in an overlay is the model's.

## Before you post

* **Kickstarter disclosure.** Kickstarter asks creators to disclose AI-generated images in the project. Caption these as *concept illustration*, and use photographs of the real prototype wherever the page shows what a backer will actually receive. Check the current creator rules on renderings before launch.
* **Keep it consistent.** Generate HERO-1 first. Then attach it as a reference image to every later prompt and add: *'same dome, same timber, same light as the reference.'* A prompt that says *the attached hero image* needs HERO-1 attached; *the attached top-down plan image* needs HERO-5.
* **Re-cropping.** Ask for the new ratio with *'same image, recomposed to 9:16, dome centred in the upper two-thirds.'*
* **Style.** *pristine* = photographic; *house* = matches the films' flat-shaded renders; *icon* = flat vector set.

## The figures overlays may use

| figure | value | from |
|---|---|---|
| across / tall | 19.42 ft / 9.71 ft | `seed_model.seed_geometry()` |
| floor | 277.0 sq ft | `seed_geometry().floor_decagon_sqft` |
| bays / wedges / vertices | 40 / 120 / 26 | `seed_geometry()` |
| stem cell, what you pay | $12,036 | `kickstarter.cost_stack().price` |
| ... cost to build / our profit | $10,030 / $2,006 | `cost_stack()` |
| ... per sq ft of floor | $43.45 | `cost_stack().per_sqft` |
| campaign goal | $110,000 | `kickstarter.goal()` |
| wedges vs boards, wood kept from one log | 1.95x | `seed_model.harvest()` |
| trees used vs a mitred dome | 92% | `seed_model.trees_against_mitred()` |
| t-shirts in one quilted layer | 132 | `kickstarter.quilt_economics()` |

## Platform sizes (the platforms' published specs -- re-check before upload)

| ratio | pixels | used for |
|---|---|---|
| 16:9 | 1920 x 1080 (Kickstarter project image: 1024 x 576 minimum) | Kickstarter project image, YouTube thumbnail, web hero |
| 1:1 | 1080 x 1080 | Instagram / Facebook feed square |
| 4:5 | 1080 x 1350 | Instagram feed portrait -- the tallest a feed post goes |
| 9:16 | 1080 x 1920 | Stories, Reels, TikTok, YouTube Shorts covers |
| 3:2 | 680 px wide, any height | Kickstarter story-section graphics |
| 21:9 | 2560 x 1440 banner, safe area 1546 x 423 centred | YouTube channel banner (generate wide, keep the dome in the middle) |
| 2.7:1 | 820 x 312 (desktop) / 640 x 360 (mobile) | Facebook page cover |
| 3:1 | 1500 x 500 | X / Twitter header |
| 1.91:1 | 1200 x 630 | Open Graph share image for the web app |

## 1. The hero -- the stem cell, pristine

### HERO-1 -- The stem cell -- pristine hero (replaces the Frankendome poster)

*Use:* Kickstarter project image, web hero, every platform's lead image · *Ratio:* 16:9 (then re-ask 1:1, 4:5, 9:16: 'same image, same dome, recomposed') · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the stem-cell dome stands alone, dead centre, on a round timber pad at the edge of a mown meadow, a line of pines far behind it, soft early-morning light raking from one side so every flat outer face of every wedge catches a slightly different tone -- the faceting IS the image. One bay at the base is an open doorway; through it a slim central utility column is visible rising to the apex. Every other bay is closed with a plain pale panel. A small upright utility panel stands a few steps outside the footprint, a neat line running from it up the outside of the dome to the apex cap. CAMERA: low three-quarter hero angle, looking slightly up, the dome filling the middle of the frame with generous even margins so the same picture crops cleanly to square and to vertical. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** THE STEM CELL -- one frame, any building. 19.4 ft across · 9.7 ft tall · 277 sq ft of floor · 40 bays · 120 wedges

### HERO-2 -- The cutaway strut

*Use:* Kickstarter story header, thumbnail, book cover candidate · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same pristine dome in soft focus behind. In the sharp foreground, a single wedge member sawn clean through and set on a pale timber block like a museum piece, its triangular end-grain facing the camera with the growth rings of the log visible: the point of the triangle is the heart of the tree, the wide face is the bark side. A second wedge lies beside it the other way round, showing its long flat outer face. CAMERA: close, at the height of the block, the triangle's point aimed toward the dome behind it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Point in. Flat face out. Split, not milled.

### HERO-3 -- Blue hour, one warm window

*Use:* Launch-day post, YouTube thumbnail background, email header · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same dome at blue hour, sky deep indigo, a single warm amber light glowing from the open doorway and one window panel; the flat outer faces pick up the last cool light of the sky. Absolutely calm: no party, no string lights, no coloured light. CAMERA: three-quarter, slightly low, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Live on Kickstarter

### HERO-4 -- The seam, macro

*Use:* Detail post, story divider, web-app section background · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: an extreme close-up of one vertex from outside: three flat wedge faces meeting pinwheel-fashion, the slim V channel of the seam running away from the corner like a gutter, grain crisp, a bead of morning dew in the channel. CAMERA: macro, shallow angle along the seam. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** The seam does four jobs.

### HERO-5 -- Top-down plan

*Use:* Logo source, favicon, profile avatar, pattern tile · *Ratio:* 1:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome seen from directly above, perfectly centred on a plain pale ground: the star-and-triangle pattern of the 2V hemisphere, the round apex cap at the centre, the base ring an even many-sided outline. Symmetrical, graphic, almost diagrammatic. CAMERA: orthographic, straight down. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (none -- this is the mark)

### HERO-6 -- House-style match

*Use:* Anywhere the image sits beside a frame of the films · *Ratio:* 16:9 · *Style:* house

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same composition as the attached hero image -- stem cell on a round pad, one open doorway, the utility column inside -- on a paper-white ground. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** 19.4 ft across · 9.7 ft tall · 277 sq ft of floor · 40 bays · 120 wedges


## 2. How it works -- anatomy plates

### ANAT-1 -- Exploded dome

*Use:* Kickstarter 'how it works' · *Ratio:* 3:2 · *Style:* house

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome as a clean exploded view floating on paper white, bottom to top: the round timber pad with a service port at its centre; the floor; the wedge frame; the flat panels lifted a hand's width out of their bays, all aligned; the smooth outer shell above; the apex seal cap at the top. A thin utility column runs up the middle through every layer. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Pad · floor · frame · panels · shell · seal cap

### ANAT-2 -- The wall sandwich

*Use:* Story section: insulation · *Ratio:* 3:2 · *Style:* house

**Prompt**

```
SCENE: a clean cross-section through one wall bay, drawn as a technical cutaway: two wedge members in section at either side (triangles, points inward), an inner panel resting on the small lip of the wedges, an empty cavity, an outer panel pressed in flush from outside, and the smooth shell over the frame. Nothing is screwed through; the shape holds it. Soft arrows show the outer panel pressing in. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Held by shape, not fasteners. The cavity ships empty.

### ANAT-3 -- One tree, two ways

*Use:* Story section: why wedges · *Ratio:* 3:2 · *Style:* house

**Prompt**

```
SCENE: two identical log cross-sections side by side on paper white. The left log is split radially into pale wedge segments like an orange, nearly all of its area used. The right log has a few rectangular boards drawn inside it, with the curved offcuts around them shaded grey as waste. Same log, same size, both clearly readable at a glance. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Split into wedges: 1.95x the usable wood of milling the same log into boards. But the frame uses more pieces -- so it takes 92% of the trees a mitred dome would. It wins by the difference, not by a headline.

### ANAT-4 -- The apex -- one hole

*Use:* Story section: services · *Ratio:* 4:5 · *Style:* house

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: a cutaway of the dome showing the central utility column rising from a port in the pad, through the floor, up the middle of the room and out through the apex, where a round gasketed seal cap closes the only opening. Thin service lines run from under the cap down the OUTSIDE of the shell to a small upright utility panel beside the dome. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Services come up the middle and out the top. One penetration, sealed once.

### ANAT-5 -- Same frame, different panels

*Use:* Story section: the stem-cell idea; animated GIF source · *Ratio:* 1:1 (make three) · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: three identical domes in a row, same frame, same camera, same light. Left: every bay a plain panel. Middle: windows, skylights and a door -- a small house. Right: a wide roll-up door across the base, skylights and louvres -- a garage. The frames must be visibly identical; only the panels change. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** The frame never changes. The panels decide what the building is.


## 3. One frame, every building -- a picture per fit-out

### FIT-stem_cell -- Stem cell

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the stem cell, standing as a plain hemisphere, with plain closed panels in every bay but the door. SCENE: the dome on a timber pad at the edge of a mown meadow in soft morning light; every bay is closed with a plain panel except the open doorway, through which a slim central utility column is visible rising to the apex. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** STEM CELL -- The bare standard article: frame, floor, shell, panels, column, seal cap and one blank utility panel. Everything else is built on top of this.

### FIT-home -- Home seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the home seed, standing as a plain hemisphere, with six window panels, two skylight panels, one door panel, two opening windows, one flue panel, and plain closed panels in the other bays. SCENE: the dome at the edge of a woodland clearing at dusk, warm light in the windows, a small stove pipe leaving through one upper bay, a slim utility panel standing a few steps outside. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** HOME SEED -- A starter domicile: wash, cook, drain and see out. The camera ring sits on the seal cap and the screen inside shows what it sees.

### FIT-food -- Food seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the food seed, standing as a plain hemisphere, with two serving hatchs, four window panels, two exhaust panels, one door panel, two louvre panels, and plain closed panels in the other bays. SCENE: the dome on a clean gravel lot beside a quiet country road at lunch time, a serving hatch open with its awning propped out, a short line of two customers. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** FOOD SEED -- Food-truck service in a fixed shell: a hatch to the outside, a hood, three bays of sink and a cold box.

### FIT-advertiser -- Advertiser seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the advertiser seed, standing as a plain hemisphere, with plain closed panels in every bay but the door. SCENE: the dome beside a highway at blue hour, every panel evenly lit from within in one calm uniform white-amber glow, like a lantern -- tasteful, not flashy. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** ADVERTISER SEED -- Every one of the 40 triangles is a lit advert facing out. Park it beside a highway and the shell is the product.

### FIT-storage -- Cold storage seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the cold storage seed, standing as a plain hemisphere, with one open-bay door, two exhaust panels, and plain closed panels in the other bays. SCENE: the dome in a tidy farmyard, a roll-up shutter half open showing neat racking inside, overcast even light. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** COLD STORAGE SEED -- A conditioned storage building: a shutter to load through, racking, and the dehumidifier that makes the difference between a shed and a store.

### FIT-bunker -- Bunker seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the bunker seed, buried, with plain closed panels in every bay but the door. SCENE: the dome buried in a grassy hillside so only a low grassed mound shows, the apex riser just breaking the turf and a timber access stair descending to a door set in the slope. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** BUNKER SEED -- The same dome, buried. The liner and collar keep the ground out; the apex riser is the only thing above grade, which is exactly what the interface boundary was for.

### FIT-treehouse -- Treehouse seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the treehouse seed, raised into a tree, with plain closed panels in every bay but the door. SCENE: the dome raised on a saddle between the trunks of a large tree, a timber stair spiralling up the trunk, dappled light. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** TREEHOUSE SEED -- A pad in a tree instead of on the ground. Same dome, same port, and the services come up the trunk.

### FIT-sauna -- Sauna seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the sauna seed, standing as a plain hemisphere, with one louvre panel, one door panel, one window panel, and plain closed panels in the other bays. SCENE: the dome on a timber deck by a still lake at dawn, a thin wisp of steam from one louvre, a single window catching the light. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** SAUNA SEED -- The same frame, lined and sealed. Blank bays hold the heat in and one louvre lets it out when you are done.

### FIT-gym -- Gym seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the gym seed, standing as a plain hemisphere, with five mirror panels, eight acoustic panels, four window panels, one door panel, two louvre panels, and plain closed panels in the other bays. SCENE: the dome in a back garden beside a family house, mirrors visible through the open door, soft afternoon light. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** GYM SEED -- A second building for the thing that does not fit in the house. Mirrors on the low bays, deadening on the rest, and a door wide enough to get a rack through.

### FIT-guest -- Guest house seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the guest house seed, standing as a plain hemisphere, with six window panels, three skylight panels, one door panel, two opening windows, and plain closed panels in the other bays. SCENE: the dome at the far end of a garden, a path of stepping stones leading to its door, the main house soft and out of focus behind. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** GUEST HOUSE SEED -- Somewhere for people to stay that is not your sofa. The home fit-out at a smaller module count, on a pad at the other end of the property.

### FIT-workshop -- Workshop seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the workshop seed, standing as a plain hemisphere, with six skylight panels, four louvre panels, three window panels, one door panel, four solar panel bays, and plain closed panels in the other bays. SCENE: the dome in a rural yard, skylights bright in the upper ring, a workbench and hand tools visible through the door, a few triangular solar arrays on the sunward face. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** WORKSHOP SEED -- Light, air and power, and nothing precious about the floor. Skylights do the work a strip light would, because on a dome the upper ring IS the roof.

### FIT-garage -- Garage seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the garage seed, standing as a plain hemisphere, with one open-bay door, four skylight panels, three louvre panels, two window panels, four solar panel bays, and plain closed panels in the other bays. SCENE: the dome at the end of a gravel drive, a single wide roll-up door spanning three base bays, a small car parked inside. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** GARAGE SEED -- One wide opening instead of three base bays, and a roll-up door across it. The frame does not care -- the ring above the opening is already carrying itself.

### FIT-studio -- Studio seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the studio seed, standing as a plain hemisphere, with twelve acoustic panels, three window panels, two skylight panels, one door panel, and plain closed panels in the other bays. SCENE: the dome under trees at golden hour, one generous window, a desk and a guitar glimpsed inside. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** STUDIO SEED -- The room that is not in the house: a study, a den, a place to make a noise in. Acoustic bays and one good window.

### FIT-nursery -- Nursery seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the nursery seed, standing as a plain hemisphere, with five window panels, three skylight panels, six acoustic panels, one door panel, and plain closed panels in the other bays. SCENE: the dome attached by a short covered walkway to the side of a family house, gentle morning light, a mobile hanging inside the window. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** NURSERY SEED -- A room that attaches to the house rather than replacing it, and then becomes something else when it is grown out of. Which is the whole argument in one building.

### FIT-jacuzzi -- Jacuzzi seed

*Use:* Carousel 'one frame, fifteen buildings', Kickstarter gallery, web app · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. THIS FIT-OUT: the jacuzzi seed, turned over, with plain closed panels in every bay but the door. SCENE: the dome turned upside down and set into a deck as a round hot tub, the timber frame as its cradle, water steaming gently at night under string-free starlight. CAMERA: three-quarter, eye level, dome centred. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** JACUZZI SEED -- The dome turned over and used as the vessel. The shell becomes the tub and the frame becomes its cradle.


## 4. The panel catalogue -- icon set

### PANEL-blank -- Blank panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a blank panel -- the standard bay, closed. What every dome ships with.. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Blank panel -- ships with every dome

### PANEL-window -- Window panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a window panel -- a fixed triangular light. The shape is the frame's, so there is no header and no trimming out. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Window panel -- $210

### PANEL-vent_window -- Opening window

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a opening window -- the same light on a hinge, with a screen behind it. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Opening window -- $340

### PANEL-door -- Door panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a door panel -- a bay cut to a door and its frame, at the base ring where the wall is nearly upright. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Door panel -- $620

### PANEL-bay_door -- Open-bay door

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a open-bay door -- three base bays taken out and replaced by one wide opening with a roll-up door: what turns a dome into a garage. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Open-bay door -- $1,480

### PANEL-skylight -- Skylight panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a skylight panel -- a light in the upper ring, which on a dome is most of the roof. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Skylight panel -- $395

### PANEL-louvre -- Louvre panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a louvre panel -- fixed slats and a screen: how a workshop or a gym gets air without a fan. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Louvre panel -- $260

### PANEL-exhaust -- Exhaust panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a exhaust panel -- a blanked bay with a fan and a backdraft damper in it. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Exhaust panel -- $290

### PANEL-solar -- Solar panel bay

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a solar panel bay -- rails and a triangular cell array on the sunward face. Square cells waste the corners today; triangular cells are the fix and they are not on the shelf yet. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Solar panel bay -- $330

### PANEL-stove_flue -- Flue panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a flue panel -- a blanked bay with a lined penetration for the stove pipe. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Flue panel -- $180

### PANEL-acoustic -- Acoustic panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a acoustic panel -- mass-loaded and absorbent, for the bays a gym or a studio wants deadened. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Acoustic panel -- $240

### PANEL-mirror -- Mirror panel

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a mirror panel -- a full-height mirror in the bay. Cheap in a gym, and a dome is already the shape that wants one. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Mirror panel -- $275

### PANEL-serving -- Serving hatch

*Use:* Panel catalogue icon set: web app, Kickstarter add-ons, stickers · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: one equilateral triangle, point up, representing a dome bay fitted with a serving hatch -- a counter-height opening with an awning. Draw only what makes this panel different from a plain closed triangle. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** Serving hatch -- $780


## 5. Reward graphics -- one per Kickstarter tier

### TIER-1 -- The drawings and the numbers

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: a neat stack of large-format construction drawings and a printed book lying open on a pale timber workbench, a laptop beside it showing a wireframe of the dome; a single split timber wedge rests on the drawings as a paperweight. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** The drawings and the numbers -- $35. Every table in the book, the cut list for any diameter, and the solver that made them. It is a download; the two dollars is card fees and hosting.

### TIER-2 -- Quilter's kit

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: a quilter's kit laid out flat on a linen tablecloth: a folded pattern sheet, spools of heavy thread, a roll of binding tape, a large triangular template, and a small stack of neatly folded recycled clothing -- denim, flannel, cream wool -- ready to be cut. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Quilter's kit -- $95. Pattern, thread, the binding, and the layer specification -- how big, how thick, how to close the edge. Sew a layer for your own dome, or sew one for somebody else's and get paid for it.

### TIER-3 -- One bay's hardware set

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: one triangular bay's hardware laid out like surgical instruments on a dark cloth: four threaded inserts, a row of flange screws, a coiled spline gasket and a small machined seam key, with a short section of wedge-shaped timber showing where each piece goes. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** One bay's hardware set -- $180. Four threaded inserts, the flange screws, the spline gasket and the seam key for one triangle. The smallest piece of the building that is a real object rather than a drawing.

### TIER-4 -- A shower cap for your dome

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: the rain-slick outer cap folded into a tidy bundle on a timber floor, one corner opened out to show a hemmed edge with grommets and a coiled webbing strap; beside it, a small dome wearing the same cap in soft focus. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** A shower cap for your dome -- $1,450. The rain-slick outer cap, made to the reference diameter, hemmed with grommets and strapping. The only watertight layer in the building, and the one you cannot sew at home.

### TIER-5 -- The utility hub

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: the utility hub standing upright on a clean shop floor like a product photograph: a slim central column with a floor port at its base, a compact water manifold, a drain stack, a small electrical sub-panel, and a round sealed cap at the top. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** The utility hub -- $2,400. The centre column, assembled and tested: pad port, water manifold, drain stack, sub-panel, riser and seal cap. The part an owner cannot make and the part the goal exists to get right.

### TIER-6 -- Dome kit, frame included

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: a complete dome kit on pallets in a clean warehouse bay: bundles of pale split timber wedges strapped in neat stacks, flat triangular panels on edge, the folded cap, and the utility column in its crate. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Dome kit, frame included -- $19,800. Everything, including the timber, for somebody with no trees. The expensive version, honestly priced: you are paying for somebody else's 45 percent recovery.

### TIER-7 -- Dome kit, bring your own trees

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: a customer's own felled pine log in a clearing, split into pale wedges fanned out on the ground like the segments of an orange, and beside it a neat crate of everything else -- panels, cap, column -- delivered and waiting. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Dome kit, bring your own trees -- $11,400. Everything except the frame. You fell, split and cut the members from your own land -- which is the whole argument -- and we send the rest.

### TIER-8 -- Pad host's pack

*Use:* Kickstarter reward card image, social 'pick your reward' carousel · *Ratio:* 3:2 (reward card), then 1:1 · *Style:* pristine

**Prompt**

```
SCENE: a large-format drawing set for a round timber platform spread on a site table outdoors, with the finished circular pad itself in the background on a gently sloping site, a service port at its centre. Product-photography lighting: soft, clean, directional, a pale timber or linen surface, a calm charcoal-to-warm-grey backdrop. Leave the top third quiet so a title can be set over it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Pad host's pack -- $640. The platform drawings at five foundation types, the service-port spec, the rim latch pattern, and the host's costing sheet. For somebody with land who wants a dome to be able to land on it.

### TIER-FRAME -- Reward-card frame (one template, every tier)

*Use:* Canva/Figma template: drop each TIER image in · *Ratio:* 3:2 · *Style:* icon

**Prompt**

```
SUBJECT: an empty card template: a very thin warm-amber triangular corner motif in the top-left, echoing one dome bay; a plain charcoal band along the bottom for a title and a price; the rest of the card left empty for a photograph. Minimal, premium. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** (template -- title and price go in the band)


## 6. Where the money goes -- one per goal line

### GOAL-test_platform -- A full test platform and one standing dome

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a single finished dome on a test pad with a few cable runs to a data logger in a weatherproof box. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** A full test platform and one standing dome -- $4,200. A serviced pad and a complete 19.4-foot dome on it, built and left up through a full year of weather. Everything in this project is solved and almost none of it is measured. A dome that has stood through one winter is worth more than any amount of arithmetic.

### GOAL-instrumentation -- Sensors in the wall, logging for a year

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a cutaway of one wall bay with small sensors tucked into the seam channel, thin wires leading to a logger. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Sensors in the wall, logging for a year -- $1,850. Temperature and humidity at each layer of the cap stack, inside and out, logged continuously. This is what turns the moisture question from a design argument into a measurement -- and it is the number the campaign has promised to publish whichever way it comes out.

### GOAL-hub_rnd -- Utility hub: three iterations to a design that ships

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: three versions of the utility column side by side, each a little cleaner than the last. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Utility hub: three iterations to a design that ships -- $9,500. The centre column is the one part that has to be right, because it carries every service and it is the part an owner cannot make. Three builds: one to find what breaks, one to fix it, one to prove the fix. Tooling, fittings, test rig and the parts thrown away.

### GOAL-cnc_router -- CNC router, 4x8 bed

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a CNC router with a four-by-eight bed cutting a triangular panel from a sheet. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** CNC router, 4x8 bed -- $14,500. Panel prototyping. No panel of this dome fits a 4-foot sheet, so every panel is a cut somebody has to get right forty times. A router with a 4x8 bed cuts a panel set in an afternoon and cuts the same set again next year.

### GOAL-cnc_plasma -- CNC plasma table

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a CNC plasma table cutting a steel triangle, a spray of sparks, a welding helmet on a hook. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** CNC plasma table -- $11,800. Steel: hub rings, floor spokes, mast flanges, threaded-insert carriers, the brackets a composite member needs moulded into it. Plasma rather than laser because the work is plate steel and plate steel is what plasma is for.

### GOAL-laser_cutter -- Laser cutter, for gaskets and templates

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a laser cutter trimming a triangular gasket from a sheet of rubber. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Laser cutter, for gaskets and templates -- $8,900. Spline gaskets, seam seals, panel templates, insert jigs. The parts that are thin, flat, and have to be identical a hundred and twenty times. It is also the fastest way to make the fixture that holds a member for its compound butt cut.

### GOAL-strut_tooling -- Tooling to mould a strut with its hardware in it

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a steel mould opened on a workbench, a finished wedge-shaped strut lying in it with its hardware moulded in. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Tooling to mould a strut with its hardware in it -- $18,000. The largest single line and the one that changes the product. A moulded or printed member arrives with its screw holes, its threaded inserts and its spline ridge already in it -- so the hardware set that joins two members is standard, reusable, and comes off with a driver. Pattern, mould and the first run of members.

### GOAL-composite_rnd -- Composite triangle: steel core, moulded shell

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a triangular composite panel sectioned to show a steel core inside a moulded shell. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Composite triangle: steel core, moulded shell -- $12,500. A member with a steel core for the strength, a moulded plastic body around it, metal inserts where hardware lands and a spline ridge where the seal sits. Materials, three rounds of samples, and destructive testing, because the point of a core is the number it survives to.

### GOAL-automation -- Automated processing for the repetitive work

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a short conveyor feeding identical timber wedges through a saw station. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Automated processing for the repetitive work -- $7,600. Feed, index, cut, repeat. One dome is 120 members, 160 threaded inserts and 40 panels, and all of it is the same operation done many times. This is the difference between making one dome and being able to make the second one.

### GOAL-quilt_seed -- Seeding the quilt network

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a community table of people sewing a large patchwork of recycled fabric, seen from above, hands only. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Seeding the quilt network -- $5,000. Sewing machines, shipping, and paying the first quilters for the first layers. Insulation in this building is a waste stream and somebody's evening, and the network has to exist before the first dome needs it.

### GOAL-engineering -- An engineer, for the things that carry people

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: an engineer's desk with a load diagram of the dome, a scale model and a calculator. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** An engineer, for the things that carry people -- $6,800. The frame's wind and snow loads, the mast, and the hoist rating for the floating rig. This project prices those parts and refuses to rate them, and that refusal has a cost attached. It is on this list so nobody has to wonder whether it got skipped.

### GOAL-fulfilment -- Making and shipping what backers are owed

*Use:* Goal breakdown: one spot illustration per line of the budget · *Ratio:* 1:1 · *Style:* house

**Prompt**

```
SUBJECT: a tidy packing bay of labelled crates and flat parcels on a pallet, ready for a lorry. A small spot illustration, centred, plenty of empty background. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** Making and shipping what backers are owed -- $9,350. Kits, plans, hardware sets and freight for the reward tiers. Budgeted at cost rather than at the tier price, because a campaign that funds its tooling out of its shipping budget delivers neither.

### GOAL-BG -- Goal chart backdrop

*Use:* Behind the goal bar chart, which is drawn from kickstarter.goal_lines(), never by the model · *Ratio:* 3:2 · *Style:* house

**Prompt**

```
SUBJECT: a very quiet background: pale paper texture with the faint outline of a 2V dome in the lower right corner, faded to almost nothing. Empty space for a chart. STYLE: flat-shaded three-dimensional technical render, matching a matte studio visualization: Lambert-shaded polygon surfaces, muted palette of sawn pine, bark brown, warm grey and charcoal with one restrained warm-amber accent. Clean background, paper-white or deep charcoal. Gentle three-quarter camera slightly above the building. Soft even light, no lens flare, no depth-of-field blur, no texture grain, no text, no labels, no numbers anywhere in the frame.
```

**Overlay:** The goal is the sum of the list: $110,000. Chart: one bar per line, in order.


## 7. Social launch series, channel art, thumbnails

### SOC-1 -- Coming soon -- the silhouette

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome as a dark faceted silhouette against a pale dawn sky, only the rim of each flat face catching light. Mysterious, quiet, a single pine beside it. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Something is growing. Follow for launch day.

### SOC-2 -- Coming soon -- the wedge

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
SCENE: a single pale timber wedge standing on end on a charcoal surface, triangular end grain toward the camera, rim-lit. Nothing else in the frame. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** One cut changes the whole building.

### SOC-3 -- Launch day

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 1:1 and 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the attached hero image's dome and meadow, with a single long ribbon of warm-amber morning light crossing the grass toward the open door. Celebratory through light alone. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** We're live on Kickstarter. Link in bio.

### SOC-4 -- Milestone -- a quarter funded

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 1:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome frame with one quarter of its bays panelled, working round from the door, the rest open frame; clean studio ground. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** A quarter of the way there. Thank you.

### SOC-5 -- Milestone -- halfway

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 1:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same frame with half its bays panelled. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Halfway.

### SOC-6 -- Milestone -- three quarters

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 1:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same frame with three quarters of its bays panelled. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Three quarters. The last bays are yours.

### SOC-7 -- Funded

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 1:1 and 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the same frame, every bay panelled, the apex cap on, warm light inside, a small group of people (backs to camera) standing together looking at it at golden hour. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Funded. $110,000 of tooling, line by line -- thank you.

### SOC-8 -- Last forty-eight hours

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome at dusk, the long shadow of the dome across the grass like the hand of a clock, one warm window. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** 48 hours left.

### SOC-9 -- Thank you / backer update header

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: close three-quarter of the finished dome's doorway, a pair of work gloves and a folded drawing set resting on the threshold. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Backer update

### SOC-10 -- Lumen explains

*Use:* Instagram / TikTok / Facebook / X launch series · *Ratio:* 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: Lumen, the project's mascot: a small low-polygon jellyfish, faceted like the dome itself, with a softly glowing translucent cyan bell and a few trailing faceted tentacles; friendly, curious, never goofy. Lumen is small in frame and never covers the dome. Lumen floats beside the pristine dome, one tentacle gently pointing at a seam, as if about to explain it. Soft pale background, the dome crisp. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Lumen says: the seam is a channel. Ask why in the comments.

### CH-YT -- YouTube channel banner

*Use:* Channel art · *Ratio:* 21:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: a very wide, calm landscape of mown meadow and a far treeline under a soft morning sky; the dome small and exactly centred, nothing important near the edges, which will be cropped. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Stem Cell Dome -- one frame, any building

### CH-FB -- Facebook page cover

*Use:* Channel art · *Ratio:* 2.7:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: a very wide, calm landscape of mown meadow and a far treeline under a soft morning sky; the dome small and exactly centred, nothing important near the edges, which will be cropped. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Stem Cell Dome -- one frame, any building

### CH-X -- X / Twitter header

*Use:* Channel art · *Ratio:* 3:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: a very wide, calm landscape of mown meadow and a far treeline under a soft morning sky; the dome small and exactly centred, nothing important near the edges, which will be cropped. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Stem Cell Dome -- one frame, any building

### CH-AVATAR -- Profile picture

*Use:* Every platform's avatar · *Ratio:* 1:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the attached top-down plan image, simplified until it reads at the size of a thumbnail: the star-and-triangle pattern in pale timber on a charcoal circle. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (none)

### YT-1 -- Thumbnail -- the question

*Use:* YouTube video thumbnail (the films) · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome at left third, clean sky at right for a large headline. High contrast, readable at small size. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Headline set in type: three to five words, e.g. 'WHY WEDGES?'

### YT-2 -- Thumbnail -- the comparison

*Use:* YouTube video thumbnail (the films) · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome on the left, a plain boxy shed of the same floor area on the right, same light. High contrast, readable at small size. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Headline set in type: three to five words, e.g. 'WHY WEDGES?'

### YT-3 -- Thumbnail -- the hands

*Use:* YouTube video thumbnail (the films) · *Ratio:* 16:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: two hands holding a single split wedge up to the camera, the dome soft behind. High contrast, readable at small size. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Headline set in type: three to five words, e.g. 'WHY WEDGES?'


## 8. Book download site and web app

### WEB-OG -- Share image for the web app

*Use:* Open Graph / link previews for the book download site · *Ratio:* 1.91:1 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the attached hero image's dome on the left two-thirds, the right third a calm, empty charcoal band for a title. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** Free book: The Wedge Method -- enter your email

### WEB-BOOK -- Book mockup

*Use:* Download page, email capture, Kickstarter plans tier · *Ratio:* 4:5 · *Style:* pristine

**Prompt**

```
SCENE: a printed paperback lying on a pale timber workbench beside a single split timber wedge and a pencil; the cover is BLANK plain charcoal (the real cover is placed on it afterwards), soft window light from the left. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (place the real cover on the blank book)

### WEB-LINKS -- Links-page background

*Use:* The web app's link-in-bio page, behind the buttons · *Ratio:* 9:16 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: the dome small in the lower third at blue hour, a tall empty indigo sky above it for a column of buttons. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (buttons go here)

### WEB-NETWORK -- Dome network header

*Use:* The web app's 'find the network' page · *Ratio:* 21:9 · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. SCENE: a gentle rolling landscape seen from a low hill: several of the same pristine domes spaced far apart on their own round pads across fields and woodland edges, a few with a warm window lit, thin dotted paths of light linking them like a map. Quiet, hopeful. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** The dome network: hosts, owners, quilters, builders.

### WEB-MARK -- Logo mark

*Use:* Favicon, app icon, watermark · *Ratio:* 1:1 · *Style:* icon

**Prompt**

```
SUBJECT: a geometric logo mark: the top-down plan of a 2V geodesic dome reduced to a single-weight line pattern inside a circle, one triangle filled warm amber. Perfectly symmetrical. STYLE: a single flat vector icon on a plain square background. Two-weight line drawing in charcoal with one warm-amber fill accent, rounded line caps, generous padding, perfectly centred. It must read clearly at thumbnail size and sit in a set with the other icons in this series: same line weight, same corner radius, same amber. No text, no letters, no numbers, no gradient, no drop shadow.
```

**Overlay:** (none)


## 9. Motion -- short video prompts

### MOTION-1 -- The frame assembles

*Use:* Veo / Gemini video: Reels, TikTok, Shorts loops, Kickstarter GIFs · *Ratio:* 9:16, six to eight seconds · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. MOTION: Time-lapse style: on an empty timber pad, pale wedges rise and lock together bay by bay from the base ring upward until the hemisphere is complete and the apex cap drops into place. Locked camera, three-quarter view. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (no text in the video; captions added in the editor)

### MOTION-2 -- Panels swap -- the stem cell

*Use:* Veo / Gemini video: Reels, TikTok, Shorts loops, Kickstarter GIFs · *Ratio:* 9:16, six to eight seconds · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. MOTION: Locked camera on the finished dome. Panels lift out of their bays and new ones press in: a house (windows, a door, skylights) becomes a workshop (skylights, louvres, solar) becomes a garage (one wide roll-up door). The frame never moves. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (no text in the video; captions added in the editor)

### MOTION-3 -- The log opens

*Use:* Veo / Gemini video: Reels, TikTok, Shorts loops, Kickstarter GIFs · *Ratio:* 9:16, six to eight seconds · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. MOTION: A pine log's end face fills the frame, then splits radially into pie-slice wedges that drift apart and turn to become the struts of a dome forming behind them. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (no text in the video; captions added in the editor)

### MOTION-4 -- Morning over the dome

*Use:* Veo / Gemini video: Reels, TikTok, Shorts loops, Kickstarter GIFs · *Ratio:* 9:16, six to eight seconds · *Style:* pristine

**Prompt**

```
THE BUILDING: a small two-frequency (2V) geodesic dome, a clean hemisphere of forty triangular bays standing on a ten-sided base ring -- ten equilateral triangles round the top and thirty slightly narrower ones. It is modest in size: an adult standing beside it reaches about halfway up the wall, and it is about twice as wide as it is tall. THE FRAME IS THE POINT OF THE IMAGE: every member is a solid timber wedge with a TRIANGULAR cross-section, split radially from a log like a slice of pie. The sharp point of each triangle aims INWARD, toward the centre of the dome; the wide FLAT face lies OUTWARD, so from outside the frame reads as a continuous, faceted skin of flat timber faces. Each bay is framed by its own three wedges, laid pinwheel-fashion so each runs a little past the next at the corner; neighbouring bays sit back to back, and along every seam their angled faces leave a slim V-shaped channel. There are NO metal hubs, NO connector plates and NO round struts -- the wedges meet each other directly. PANELS: flat triangular panels press into each bay from outside and sit flush against a small lip on the wedges' inner edge, so the exterior surface is crisp and even. At the very top, a small round sealed cap closes the apex. MOTION: A slow orbit around the dome as the sun rises; light walks across the flat outer faces one facet at a time. PALETTE: pale sawn pine, warm charcoal, soft sky; one warm-amber accent (hex FFB13E) used sparingly -- a glow in a window, a strap, a detail. Deep indigo-charcoal where a dark ground is needed. AVOID: metal hubs or connector plates, round dowel or pipe struts, dimensional lumber with square corners, a full sphere, a tent or canvas skin, LED strips, rainbow lighting, party lights, confetti, glue, patches, mismatched panels, weathered or grey wood, garbled text, any words or numbers, watermarks, extra domes unless asked for. STYLE: pristine architectural photography of a real, precisely built object. Calm, clean, confident. Natural light, sharp focus front to back, true-to-life colour. The timber is pale, freshly split and sanded pine or Douglas fir with straight visible grain and honest end grain -- clean and exact, not rustic, not weathered, not glued or patched. Every seam is tight and even. The ground is tidy: close-mown grass, gravel or a timber pad. No clutter, no props that are not named, no text, no letters, no numbers, no logos, no watermark anywhere in the frame.
```

**Overlay:** (no text in the video; captions added in the editor)
