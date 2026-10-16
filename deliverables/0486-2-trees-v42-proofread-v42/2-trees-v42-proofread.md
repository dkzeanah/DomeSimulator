# Proofread: The 40 Hour Cabin: 2V Geodesic Dome Wedge Method

This is a proofread of DeepSeek's book, the one going to Amazon. **Nothing in the book was changed.**

**Copy read:** `deliverables/book/2-trees-v42.pdf`. That is the newest PDF of this book:
- 442 pages, US Letter, built 3 October 2026.
- It predates the retitle, so its title page still says *Geodesic Dome Wedge Method / The 40 Hour Cabin: 3 Trees*.
- The manuscript hasn't been edited since then, so the text below matches the current book.

**Page numbers** are the PDF's own page numbers, as your PDF viewer shows them. The book prints no page numbers of its own.

**Method:** I read every page of text and looked at every illustrated page (140 of them). I checked the arithmetic and the geometry where a claim could be checked.

---

## Verdict

**The heart of the book is good.**
- Part 1 is a real build manual: the tree, the split, the pinwheel, the jig, the fortnight.
- The voice is strong. It is honest about bad numbers.
- The "here is the number that does not help us" habit is a selling point no other dome book has.

**It is not ready to sell.** Five kinds of problem keep it from being publishable as it stands:

1. **The headline claims contradict each other:**
   - how many trees (2 or 3);
   - how many hands-on hours (37.5, 46, or 80);
   - whether the cabin was actually hung from trees, or whether that is "a drawing";
   - whether the trees were a windfall or were felled.

   A reader meets all four within the first 150 pages.
2. **Real errors in geometry and arithmetic.** The worst:
   - Chapter 9 has the two strut families backwards.
   - Chapter 40 says panels nest on a 4×8 sheet, when no panel fits on one.
   - Chapter 77's pentagon argument is off by a factor of two.
3. **Leftovers an Amazon buyer can't use:**
   - references to "the films", "the campaign", "the Creator", "the wedge book" and "the project brief";
   - file names such as `lesson_wedge_why` and `panel_method.py`;
   - raw code output in tables;
   - about 25 pages of software-developer documentation.
4. **Production defects:**
   - no page numbers anywhere, and a contents list without them;
   - no index, although a heading promises one;
   - app screenshots with the controls still showing;
   - an empty table, overlapping tables, and broken code blocks.
5. **Scope.** Parts 2 and 3 slide into other domes (314, 300, 1,217 and 2,096 sq ft), other products (pads, irises, a fibreglass hull, CNC plasma tables) and a graphics-programming appendix. Part 2 even describes a different build method:
   - folded brackets;
   - 960 screws;
   - a fibreglass layup.

**My recommendation:**
- **Make the Amazon book Part 1, plus four or five Part 2 chapters:**
  - Ch 57, less skin;
  - Ch 58, the pony wall;
  - Ch 59, the brim and rain;
  - Ch 60, the shell ladder;
  - optionally Ch 64, the ground.

  That comes to about 230–260 pages.
- **Cut the rest:** the network, the iris, the campaign, the product pricing, the CNC shop and the back-matter software docs. It already belongs to the Complete Edition and the codebase you sell for $20.
- **The split does three things:**
  - It fixes most of the contradictions, because most of them come from the later parts.
  - It makes the paperback cheaper to print.
  - It gives people a reason to buy the site edition as well.

---

## 1. Blocking — fix before upload

| # | Page(s) | Problem |
|---|---|---|
| 1 | 2, 5, PDF metadata | Old title and subtitle throughout. The title page says "By the builder" and the copyright line says "© 2026, the author", with no name. The PDF's metadata title is the old one and its author is blank. KDP needs the author's name to match the listing. |
| 2 | 1 | The interior file starts with the old cover painting, still lettered *GEODESIC DOME WEDGE METHOD*, inset on a white page. The cover doesn't belong in a KDP interior; it uploads separately. Use the re-lettered `book_wedge/cover/painted-front.png`, and only as the cover. |
| 3 | every page | No page numbers or running heads. Pages are US Letter with no gutter margin. This PDF is a screen PDF, not a print interior; the Complete Edition has a print pipeline and this book doesn't yet. |
| 4 | 2–5 | The contents list has no page numbers. The reading tracks (story, explain, howto, reference) print as bare lowercase words beside each title. |
| 5 | 441 | The heading says **"Index and Colophon"**, but there is no index. |
| 6 | 5 | Internal labels "Title pages / Title page" print, and the title page comes *after* the contents. |
| 7 | 323 | Ch 74 "Every other way of doing it, priced" prints an **empty table**, header row only. The chapter promises five tables: 8 materials, 8 sections, 16 panels, 9 claddings and 11 foundations. |
| 8 | 343 | Ch 81's fit-out table: every price is "--", and the panel column prints raw Python output: `{'window': 6, 'skylight': 2, ...} panels` and `{} panels`. |
| 9 | 144 | The "Twelve stages of the jig" table: rows overprint each other, and the numbering is doubled ("1  1. THE BARE BENCH"). |
| 10 | 150, 412 | The butt-cut setups table: the "members" column is all "-". |
| 11 | 158–159 | The panel drawings: labels are cut off ("+8.0in SACRIF", "jigblank", "B finis"), and they print code IDs (`WOOD_P001_E0`, `POINT_DOME_IN`, `BAB`). They are called "full size" but printed on a letter page. |
| 12 | 427–441 | Every code block is broken. Literal ```` ``` ```` fences print, and line breaks collapse so commands run together ("…DomeSimulator.git cd DomeSimulator", "…numpy py -3.12 launcher.py"). Curly quotes appear inside commands and Python code, so nothing can be typed in as printed. Also "`..venv-voice`" (p428) and "`–query`", which should be `--query` (p441). |
| 13 | 6, 21, 114, 141, 176, 190, 334, 337, 355, 356 | App screenshots with the controls still showing: "PAUSED", "CHAPTER 12", "LIVE CALCULATION", timeline bars, sidebars. p21 calls one "The photograph", and p6 captions one "The frame, day fourteen". See section 9. |
| 14 | 216 | A **placeholder page**: "The plate is a placeholder in this edition — the photograph is still to be taken." A paid print book can't ship with that. |

---

## 2. The headline claims contradict each other

These are the ones a reviewer will quote.

### How many trees

| Page | What it says |
|---|---|
| 5 | "raised between **two** trees on three cables" |
| 14 | "**3** trees are what it takes … consumes 1.88 of them" |
| 84 | "if you have one tree rather than **two**" |
| 85 | "Chapter 22's **3** trees" |
| 95 | "So: fell **2** … the same **2** trees that this book's actual build used" |
| 100 | "Two trees: **192** struts … That is the title of the book … 72 spare — about **seven per cent**". Two trees give 128 struts; 192 is three trees. 72 of 192 is 37.5 per cent, not seven. |
| 104 | "you need the third one because you cannot get eight-tenths of a tree". 1.88 trees argues for **two**, not three. |
| 126, 128 | "two trunks are 192", "every section of the two trunks", "Two trees become a building" |
| 234 | "**Two** trees of solid wood are 318 board feet". 318 bf is **one** tree (p13). |
| 303 vs 306 | The same chapter says "the 21.6 foot dome from **3** trees" on one page and "the 21.6 foot frame from **two** trees" three pages later. |

### How many hands-on hours

| Page | What it says |
|---|---|
| 6 | 16 h of splitting + 30 h of assembly → "37.5 hours", then says the 16 h don't count. The reader sees 46. |
| 7, 142 | "fourteen days — **37.5 hours** of hands-on work" |
| 56, 128–129, 203, 226 | Ripping alone is **24 h** at 5.0 struts an hour. p6 and p202 say 16 h, at "30 per 4-hour session". |
| 198, 306 | "9,301 dollars kept, over **80 hours** of hands-on work" |
| 202 | "the forty hours is the *erection*". p6 says it is "the frame, from split wedges to standing". |
| 203 | The chart is titled "The fortnight: **15** days accounted for", while the text says fourteen. |

### Was it hung from the trees?

| Page | What it says |
|---|---|
| 5 | "raised between two trees on three cables, **because that is how this one was actually built**" |
| 141 | "this is a **tested construction** … two legs to one tree, one to the other" |
| 7 | "The floating rig … is a design possibility, priced but **not rated**" |
| 316 | "Three cables run from the apex ring to **three** trees" |
| 318 | "this is the **least-built idea in the whole book** and it should be read **as a drawing** rather than a report" |
| 163, 165 | "The book's own build **stands on the continuous** ring beam" and "used straps at every base point". p141 says no footing; p139 says blocks. |
| 141–142 | The cables run "to saddles on two of the **three** trees". Those three trees were felled and split into the frame in chapters 27–29. |

### Windfall or felled?

- Ch 1 (p12) is "The Tree That Was Already Down", a windfall.
- Ch 27 (p121–124) fells the trees: "The first tree went exactly where it was aimed". It is "Two days for 3 trees", but the story ends "Two trees down."

### Which cut list do I use?

The book gives four different sets of member lengths:

| Page | Lengths |
|---|---|
| 45 | 62.73 / 63.27 / 71.24 / 72.00 (the "model") — "every stick that passes through the bench is one of them" |
| 46, 110, 408 | 72.0 / 63.5 / 61.5 (the "master list") |
| 158–159 | 62.262 / 70.788 / 63.011 (the panel drawings) |
| 207 | "Cut 72 inches and 63.67" |

The book does say once that the master list wins (p111). Even so, a builder will cut from the wrong table.

### Which joint is used?

- **Butt cut.** p69 says it "needs only to be square" and "the only cut angle … is the square butt". p71, p29 and p148 say it is a compound cut. These are in the same chapter.
- **Key profiles.** p74 says "The book's build uses the shaved-flat answer … one key for all 55". p29, p76, p112 and p409 tell you to use **two** key profiles, 25 and 30.
- **When the keys go in.** p139 says "Key and screw as you go". p210 says "cut or print the keys after the frame has dried … first months".
- **Overfit.** It is 6 inches in the text (p70, p152) and +8.0 inches in the drawings (p158). p156 calls it "the half-inch of slack".
- **Finish.** p181 says to oil 664 sq ft of sawn faces. p210 and the glossary (p426) say to oil the bark only and "leave the sawn faces bare".

---

## 3. Geometry and arithmetic errors

| Page | Error |
|---|---|
| 44 | **The strut families are backwards.** It says the short edge is midpoint-to-midpoint (31.72°) and the long edge is half an original edge (36°). The truth is the reverse: half an original edge spans 31.72° (short, 0.5465 R) and midpoint-to-midpoint spans 36° (long, 0.6180 R). p207 states it correctly. The same page puts the 10 equilateral triangles "around the five-fold points" (they sit at face centres; the isosceles ones ring the five-fold points). It also gives the isosceles panels "two long edges over a short base", but p46 and the p111 figure show a long base with short sides. |
| 168 | "the two panel shapes … nest inside a standard sheet". **No panel fits a 4×8 sheet even on its own:** the 72-inch equilateral panel is 62.4 inches tall. p256 says so itself: "No panel of this dome fits a four-by-eight sheet." |
| 330 | "the total missing angle the sphere demands is **one** full turn … Twelve sixths make the sphere." The total is **two** full turns (720°); twelve sixths of a turn is two turns. |
| 175, 353 | "steep seams near the crown … shallow near the rim". That is backwards: a hemisphere is vertical at the rim and flat at the crown. Ch 82's own table (p351) shows the lower band at 55°+ and the cap at 15.9°. |
| 17 | "roughly 45 per cent survives … **The other** 87.4 per cent" — 45 + 87.4 is more than 100. |
| 18–19 | It says comparing against the dressed 2×4 is "the smaller, **less** flattering target". Comparing against the *smaller* board flatters the wedge **more**, which p199 and p234–235 confirm. |
| 31 | "a **fifth** of a round log" — the wedge is an eighth. |
| 60 | "Add the **five** together" — six losses are listed. |
| 69 | "bearing patch is a full side … 9.82 sq in" — 9.82 sq in is the *end* (cross-section) area. |
| 73 | It calls fold + gap = 45° "a theorem … nothing tuned". It is true by definition, because the gap *is* 45 minus the fold. |
| 80 | "0.48 in … 10 per cent of the **section**" — that is 10 per cent of the depth. |
| 102 | "the longest [member] is exactly your stock length … no margin". Yet the head is left 6 inches long (p70), which is impossible if the member equals the section length. p95 says this itself. |
| 110–111, 409 | The isosceles panel is described with unequal sides and an off-centre apex, which is a scalene triangle. The *members* differ because of the inset; the *triangle* is still isosceles. |
| 156 | "Cut all three heads on the same plane … in one motion" — the three heads are at three different corners. |
| 181 | "two sawn faces **6.0** inches deep" — the member depth is 5.00 inches everywhere else. Also "664.3 feet of stock" against "673 feet" on p109. |
| 223 | The "biggest dome one person can frame and the biggest the tree fills … the same dome, to the inch, and I did not arrange that" — both come from the same declared 6-ft choice (p221). It is not a coincidence. |
| 223, 362 | "a 3V frame is 165 members" — 165 is a *hubbed* dome's strut count. In this book's panel method a 3V dome is 3 × panels (225 for 75 panels). |
| 237 | "the rate sits at the break-even wage … two different routes to one number" — the rate is $31.14 and break-even is $50. Also "0.20–0.30 … the book uses 0.60 — the high end". 0.60 is double the high end. |
| 242 | "in seven words: the wood did not get better; it got used" — that is nine words. |
| 260 | "each added foot buys less … 71, then 97, then 117" — those are running totals. The increments are 71, 26 and 20. |
| 262 | "Two people at 50 gallons a day empty a 1,000-gallon tank in 20 days" — that is 10 days. |
| 267 | The payback table and its text say "**17.9 months**" for the 7th quilt layer. It is 17.9 **years** (p268 is right). The 7th layer is also judged against "R-6.3 at three layers"; it should be six layers. |
| 280 | "the slab is a quarter to a fifth of the build — 45.2 and 21.1 per cent" — 45 per cent is nearly half. |
| 285 | "The cheap pad … the least a pad can cost" is $19,843, but the bare pad on the same page is $12,231. |
| 286 | "the site's payback is the only number the model cannot compute" — this comes right after computing it (2.2 and 6.8 years). |
| 294 | A 20.0-ft dome with "longest member 6.0 ft". p222 says 5.52 ft, and that 6.0 ft gives 21.6 ft. |
| 320 | "A hollow triangular member is **four** thin pieces … four glue lines" — a triangle has three sides. |
| 341 | "an argument the cap makes for 5,395" — $5,395 is the plywood hull; the cap is $3,265–3,748 (Ch 70). |
| 366 | "4,200 buys a serviced pad **and a complete standard dome**" — the dome alone is $12,036. |
| 422 | "nearly eight metres of headroom … a thirteen-metre dome" — a 13 m dome is 6.5 m tall. |

### Money figures that don't reconcile

The book quotes many different prices for "the frame" and for "the building", and never puts them side by side:
- **The frame:** $497, $692, $747, $2,400 per tree, $9,798.
- **The building:** $6,943, $10,030, $12,036, $16,444, $23,700, $84,983.

Several are for other floor areas. $6,943 at $22 a square foot is 314 sq ft, and $12,036 at $43.45 is 277 sq ft; the book's dome is 365 sq ft. One reconciliation table in the money chapter would fix most of it. Other inconsistencies:
- Electricity: $0.14/kWh (Ch 45, 66) against $0.17 (p361).
- Ring cost: $9,120 (p284) against $7,600 (p291).
- Set-up time: "2 to 14 days" (p277) against "2 to 14 months" (p281).

### Other counts that don't match

| Page | Problem |
|---|---|
| 8 | "Eighteen chapters" of manual and "Fifteen" of explanation. The contents shows **20** howto and **48** explain; 15 is the *reference* count. |
| 15–18 | Chapter 2 is titled "Fifteen Middlemen", but the text says "fourteen of the fifteen … keeps exactly one", "one step of 14", "14 operations". The list has 12 headings. The method is "fell, buck, split, jig, raise — **8** operations": five are named. p235 repeats the 8. |
| 22 | The heading "The ten-piece **pentagon**" describes a ten-piece decagon. |
| 135–137 | "the same **twelve** motions": the list names 8, and 8 steps are given. The twelve is the jig's stage count. |
| 137–138 | "the fourth panel is the first good one … the run's real output is thirty-seven". Then the dome is three panels short; it needs 43 panels. |
| 218–219 | "I ran the same frame at **four** diameters" — the table has three rows. "Six of the eight columns do not move … only two move": five don't move and three do. |
| 303 | The audit table says rotation is "modelled — and it loses", but the text says "One row is **measured** and still loses". |
| 336, 338 | The core is "fourteen parts, five services", against "1,405 for 23 items" and "six services through one hole". |
| 350, 353 | Ch 82 has "5 bands"; Ch 83's heading says "four levels". |
| 377 vs 322 | "Foundation, 7 kinds" against "eleven foundations". |

---

## 4. Safety

These are worth checking against your own arborist training.

- **p141 — standing under a suspended load.** "the builder standing under something that yesterday was a pile of wedges". The book should say plainly: never stand under a hanging load.
- **p122 — the back cut.** It is placed "level with the notch's flat floor". For the conventional notch described (sloped top cut, flat bottom cut), the usual guidance is to cut slightly above the notch floor, to leave a step. The hinge is also called both "a couple of fingers" and "fist-thin".
- **p124–125 — limbing and bucking.** "the top side is in tension". For a log sagging between two supports, the top is in **compression**, so "cut from the top" is the advice that pinches the bar. "keep the trunk between you and the slope" is ambiguous; it should say to work on the uphill side.
- **p120, 122, 165 — a warning that isn't there.** These pages refer to a felling/chainsaw warning and a "never fell alone" rule "from the front matter". The front matter only has the engineer's note.
- **p156 — chainsaw technique.** It describes flush-cutting with the chainsaw "bar flat to the bench". That technique deserves a kickback warning.

---

## 5. Leftovers an Amazon reader can't follow

- **"The films", "on camera", "the pine film", "the seed-pitch film".** About 60 mentions, from p62 onward. Captions say "-- a frame of the seam-climate film" (p176) and "-- a frame of the seed-pitch film" (p190).
- **"The campaign", "kit rungs", "the backer".** p212, p267, 271, 288, the whole of Ch 85, p401.
- **Other proper names and companion-book references:**
  - **"The Creator" / "Dome Creator":** p272, 278, 283, 377.
  - **"Iris-25":** p244.
  - **"the wedge book's own page/chapter":** p171, 209, 320, 322, 348, 353.
  - **"the why-build chapter":** p237. This book has no such chapter.
- **Internal names:**
  - Ch 13's callout (p59) and Ch 46's callout (p197) say "the project brief".
  - Ch 15's callout (p68) leaks a file name: "already corrected on camera in **lesson_wedge_why**".
  - p382 and p388 print "( panel_method.py )".
  - p178 says "The source material … is a video claiming 20 things about linseed oil". That is an unnamed YouTube source, and it reads badly in a paid book.
- **Wrong Part numbers.** This book has three Parts, but the text refers to:
  - "Part IV" (p9);
  - "Part 5" (p83);
  - "the book has four more parts to go" (p139);
  - "Part Seven — Chapters 40 through 45" (p142).
- **Errata and constants that aren't where the text says.** "The errata pages" are promised (p8, 29, 72, 200 and others), but there is no errata section; the corrections are scattered inline. "The constants table at the front of the book" (p18, 197) is at the back (p415).
- **Chapter references with "Chapter" missing:**
  - "the work 56 prices" (p253);
  - "44 draws the whole curve" (p254);
  - "the flat-rate table of 52" (p255);
  - "it is 58" (p256);
  - "from 52", "The seam key of 16", "The panel raise from 8" (p249).
- **Wrong cross-references:**
  - "Chapter 22's appendix" (p103) doesn't exist; this *is* Ch 22.
  - "the ladder of Chapter 54" (p270) should point to Ch 55 or 60.
  - "the next chapter's hardware" (p177): the next chapter is about wood finish.
  - "this book's cut chapter recommends when a miter saw runs out of scale" (p393): there is no such chapter.
  - "about triangles on its second page" (p393): that argument is in Ch 6, p31.

### Part 2 describes a different build from Part 1 (pp. 218–262)

**The bracket build.**
- The frame is "held at the corners by **120 brackets and about 960 screws**".
- Its nine processes are "fell, rip, crosscut, **fold**, drill, screw, raise, sheathe, **glass**" — folded metal brackets and a fibreglass layup.
- It speaks of "the mill", "a better infeed roller", "screws and resin" and "the brake is set twice" (p409).

Part 1's method has no brackets and no fibreglass.

**Other Part 2 inconsistencies:**
- "a 10 foot dome takes 1 tree, a 30 foot dome takes 3" (p226).
- The triangles go up one at a time on a cable (p221, 227), while Ch 32 raises the frame on props.

**Other domes.** Part 2 works its numbers on these, usually without saying so:
- a 314 sq ft "reference floor" (Ch 58, 59);
- 300 sq ft (p200);
- the 1,217 sq ft Split-Log Homestead (Ch 60);
- the 3V hubbed Timber Workshop (Ch 62);
- the films' 15-inch pine (Ch 55);
- a 277 sq ft "standard article" (p311, 315).

**Voice.** Chapters 52–57 switch to a first-person essay voice with en dashes, and they read like a different author. That is acceptable for Part 2, but it isn't consistent with the rest.

### Off-topic for a cabin book

- **Ch 90** is a 5-foot steel bowl from a plasma table.
- **Ch 91** is a DIY CNC plasma-table bill of materials, built from Homemade Madness plans, with Mach3 and metric frame sizes. If it stays, check that the credit wording is fine with the plan's owner.
- **"From Number to Pixel"** (p416–421) is cross products, projection matrices and shaders.
- **"The Composer"** (p422–423) is the film's female cast: hair "mid-thigh … floor", bodices, heels, and a "skin-tone silhouette like a shop's dress form". In a cabin-building book this reads very strangely. Cut it.
- **"The map of the code" through "The launcher"** (p429–441) is developer documentation for adding film elements, presenter objects and Assembly Line stations.

---

## 6. Copy-edit (typos, grammar, typography)

| Page | Fix |
|---|---|
| 99 | "This book **buckes** to 6 feet" → "bucks" |
| 161 | "forty small **absorpions**" → "absorptions" |
| 21 | "because there was no first dome there was only a sequence of one-offs" needs punctuation. There was also never a second dome. |
| 53 | "costs that have nothing to do with **the dome**: furniture, roofing, permits" → should be "the frame". |
| 59 | Ch 13 callout fragment: "The 88% recovery figure in the project brief, which was computed for…" |
| 82 | Ch 18's subtitle prints twice. |
| 12 and every chapter | The chapter title prints twice (the title, then an identical first-section heading). |
| 191 | "a 800 watt array" → "an 800-watt array". Money throughout prints without $ ("4,100 of storage, 630 of inverter"). |
| 231 | "1 whole **stages**" |
| 239 | "at the book's illustrative **5,461-style terms**" — a garbled token. |
| 285 | "lease it **80** of the year", "below **80**" — "per cent" is missing. |
| 298 | "saves 2,400 minus 600 dollars per pad beyond the first three" — garbled. |
| 305 | "…and it is a real number – Pressure treated, insulated, glassed and fitted out, at $22 the square foot, with nothing salvaged and nothing donated**..**" — a duplicated phrase, a stray capital and a double full stop. |
| 307 | "a 18,401" → "an 18,401" |
| 347 | "a factor of 83,576 against 2,379 pounds" — garbled (the factor is about 35). |
| 387 | "315 sticks against the wedge dome's members" — the number (120) is missing. |
| 441 | "verify_renders.py deliverables/masterclass/**whey**-wedges-no-sawmill.mp4" — "whey" for "why". |
| 442 | "a table prints the fold angles of 91 chapters' worth of claims" — garbled. |
| 7, 27, 73, 99 | Sentences start with digits: "3 trees, one chainsaw…", "Split those and you get 8.", "2. The bad news is that 2 is not one". |
| 10, 106, 236 | "residual — **0.0e+00** inches" — code notation; say "zero to the last decimal". |
| throughout | "--" in place of dashes: p11, 176, 190, and many subtitles (p244, 270, 290, 308, 313, 316, 327, 330, 333, 353, 377). En dashes (–) and em dashes (—) are mixed. |
| 424–426 | The glossary is alphabetical up to "Worked example", then starts a second A–Z run ("Boat hull", "Dew point", "Desiccant drawer" …). Missing entries: 2V, fold angle, cap, brim, frankendome. |
| 382–388, 244–250, 401–404 | Metric units (metres, kilograms, millimetres) appear in an imperial book. |

---

## 7. Conflicts with your new arrangement

You now sell the Complete Edition with the codebase for $20, and a $50 design session.

| Page | What it says | Why it matters |
|---|---|---|
| 10, 426, 442 | "Every tool that produced these numbers is … **included with this book**" | Not true for the paperback. |
| 369 | "The drawings and the numbers, **at 35**: every table in this book, the cut list for any diameter, and the solver … It is a download." | A $35 offer that competes with your $20 one. |
| 370 | "Open source. The geometry, the solver and the tables are published." | — |
| 427 | The full `git clone https://github.com/dkzeanah/DomeSimulator.git` install path | The repo is public anyway, but the paperback hands out for free what the site sells as part of the $20 edition. |
| 216, 440 | "the photographs that remain are the author's to take" | — |

**Suggestion:** replace the "Software in this book" section with one page pointing to the site: the Complete Edition, the codebase and the design session.

**Two "40 Hour Cabin"s of different sizes:**
- This book's cabin is **21.6 ft / 365 sq ft / 120 members / 3 trees**.
- The Complete Edition's cabin, from the solver, is **19.4 ft / 277 sq ft**.

Both are now called *The 40 Hour Cabin*. A reader who buys both will notice. One sentence in each book saying which tree and size it uses would cover it.

**Print cost.** A 442-page **colour** 8.5×11 paperback is expensive to print on KDP. Check KDP's printing-cost calculator before you set a price. A black-and-white interior or the shorter book would change the number a lot.

---

## 8. Smaller notes worth a look

- **p8 vs p6/21/114/141.** "The dome in the photographs was not rendered". Every dome picture in the book is a render or a screenshot. Either add real photos or change the sentence.
- **p13/99, 45/103, 111/408, 112/407, 113/413, 150/412.** Six figures appear twice. It is deliberate in the "Master Tables", but readers will see repeats.
- **p14.** "A crew can lift a sixteen-foot stick; one person cannot" — this overstates it; one person carries a 16-ft 2×4. "A sixteen-foot log section" would be accurate.
- **p171.** A rim-panel doorway is a triangle about 52–62 inches tall with a point at the top. The text describes jambs and "a header across its top edge" as if it were a normal door, and never states the head height.
- **p192 vs 291.** "40 panels' worth of power across 292 sq ft" against "20 of them: 292 square feet".
- **p233.** "a 16-ft 2×4 … cut into 6 foot lengths, 3.33 per section". A 16-ft board yields two 6-ft pieces, not 2.67.
- **p394.** "a dome's struts are one length and one miter for the whole building" — not this dome. Also "a zome is the easier first build while this book's wedge dome is the better second one" — that is odd positioning for this book.
- **p356–357.** Ch 83 repeats Ch 45's "wall as a filter" section (p195–196) almost word for word.
- **Images.** 131 images are under 250 DPI; most are about 240. That is fine for diagrams, but the cover page (p1–2) is 147 DPI. KDP prefers 300.

---

## 9. Imagery: my opinion

**Keep the computed diagrams and tables.** They are the book's strongest pictures:
- the tree, the split, the nest, the seam sections, the charts;
- the cut list and seam schedules.

They follow the repository's rule that numbers are computed, and an AI image can't reproduce them accurately. Fix only the broken ones (section 1, items 7–11).

**Replace the app screenshots** (p6, 21, 114, 141, 176, 190, 334, 337, 355, 356). The UI controls make the book look like a software manual. The cleanest fix is to re-shoot the same scenes from the solver with the overlays turned off: the stills pipeline the Complete Edition already uses. That keeps them accurate.

**Add human, story imagery where the book has none:**
- the story chapters: Ch 1, 3, 5, 26, 27 and 51;
- the three Part openers (p11, 217, 308), which are text-only pages;
- the build days (Ch 29–32), which are long stretches of text.

This is where AI illustration helps.

**Three rules if you use ChatGPT or Gemini:**
1. **Label them as illustrations, not photographs.** The book promises (p8) that its photographs are real and not rendered. An AI image captioned as a photo breaks that promise, and a reader will notice. Use a consistent *painted* style, like your cover, so nobody mistakes one for a photo.
2. **Don't use AI for p216**, the "dome, a year on" plate. The book itself says that one must be a real photograph. Take it.
3. **Check the geometry in every image.** AI models usually get geodesic domes wrong: metal hub connectors, hexagons, the wrong number of triangles. Reject any image that shows any of these:
   - metal star hubs at the corners;
   - milled rectangular boards;
   - a dome made of hexagons;
   - a top not made of five triangles.

**KDP will ask** whether the book contains AI-generated images. Answer yes for these.

**Resolution.** These tools output about 1,000–1,500 px. For a full page at 300 DPI you need about 2,550 px across for 8.5-inch wide pages, or 1,800 px for a 6×9 book, so upscale them first.

---

## 10. Prompts for ChatGPT / Gemini

Each prompt stands alone; paste it whole. They share one style line and one geometry paragraph, so the set looks like one series. If you print the interior in black and white, add: *"Render in rich greyscale with strong value contrast."*

### 1. Part 1 opener — full page (replaces the text-only p11)

```text
Warm painterly book illustration, golden-hour light, soft visible brushwork, realistic proportions, no text, no letters, no logos, no watermark. Portrait 2:3.

A finished timber dome frame stands alone in a small clearing at the edge of a pine forest at sunset. The dome is a two-frequency geodesic hemisphere about 22 feet across and 11 feet tall, made of 40 flat triangles; five triangles meet at the very top. Every triangle is its own framed panel of three wooden members. The members are split logs: long pie-slice-shaped sticks with rough brown pine bark on the outside face and two pale, flat, freshly sawn faces. There are no metal hubs, plates or connectors anywhere; at each corner the members overlap like a pinwheel and the corner point is empty. Neighbouring panels sit side by side with a thin seam between them. The frame rests on a ring of wooden blocks. In the foreground: three pine stumps, a stack of split wedges with bark up, a small orange consumer chainsaw on a stump, sawdust on the ground. Quiet, hopeful, handmade.
```

### 2. Chapter 1, "The Tree That Was Already Down" — half page (p12)

```text
Warm painterly book illustration, early-morning light through pines, soft visible brushwork, no text, no logos, no watermark. Landscape 3:2.

A single large pine lies on the forest floor where a storm dropped it: the root plate torn up and standing on edge with soil still in it, the trunk running straight for about 48 feet, the crown buried in brush. The trunk is about 12 inches across at the butt. A small consumer chainsaw with a 16-inch bar rests on the trunk next to a measuring tape and a lumber crayon. No people. The mood is a question, not a triumph: wood that nobody wanted, waiting.
```

### 3. Chapter 5, "The Cut That Changed It" — square (p27–28)

```text
Painterly close-up book illustration, warm afternoon light, no text, no logos, no watermark. Square 1:1.

The end grain of a six-foot pine log section, about 10 inches across, split cleanly through its centre into eight identical pie-slice wedges, like a cake cut into eighths. The wedges have just been pushed slightly apart so the eight radial cuts are visible; each wedge has rough bark on its curved outer face and two flat sawn faces meeting at a point at the pith. The growth rings are visible. Fresh sawdust on the ground, a small chainsaw resting nearby, out of focus.
```

### 4. Chapter 3, "The Frankendome" (replaces the p21 screenshot)

```text
Painterly book illustration, overcast daylight, honest and slightly comic, no text, no logos, no watermark. Landscape 3:2.

A lumpy, improvised geodesic dome frame in a backyard, about 16 feet across, built from mismatched salvaged wood: boards of different widths and colours, old painted lumber, crooked sticks. At every corner the pieces are joined with bent sheet-metal V-shaped brackets and lots of screws, each bracket bent to a slightly different angle. The dome is recognisably a dome but uneven: some triangles twisted, seams pinching and gapping. It is clearly standing and has been outside for months: weathered, a tarp half over one side. The feeling is "it worked, and it was awful".
```

### 5. Chapter 26, "Day Zero: The Saw" — top-down flat lay (p118)

```text
Clean top-down flat-lay book illustration on weathered plywood, soft even light, painterly but precise, no text, no logos, no brand names, no watermark. Landscape 3:2.

Laid out neatly: a small orange consumer chainsaw with a 16-inch bar, a spare chain, a round chainsaw file with a file guide, a bottle of bar oil, a two-stroke fuel can, orange chainsaw-protective chaps folded, a forestry helmet with a mesh visor and ear defenders, work gloves, two plastic felling wedges, a lumber crayon and a tape measure. Everything a person needs on day zero, and nothing more.
```

### 6. Chapter 27, "Felling" — safety-correct (p121)

```text
Painterly book illustration, clear morning light, realistic and safety-correct, no text, no logos, no watermark. Landscape 3:2.

A builder in full chainsaw protective gear (helmet with mesh visor, ear defenders, chainsaw chaps, gloves, boots) stands to the side of a medium pine tree about 12 inches thick, beside a clean open notch cut on the falling side. The builder is seen from behind and to one side. A cleared escape path leads back and away at an angle. A second person in a helmet and high-visibility vest stands well clear, at a safe distance, watching the crown. The tree is still standing. Calm, deliberate, careful.
```

### 7. Chapter 29, "Ripping" (p128)

```text
Painterly book illustration, late-afternoon light, sawdust in the air, no text, no logos, no watermark. Landscape 3:2.

A six-foot pine log section lies in a simple cradle made of scrap timber on stakes, being split lengthwise down its centre with a small chainsaw by a builder in chaps, helmet and visor, seen from the side. Behind, finished wedges, long pie-slice-shaped sticks with bark on the curved face, are stacked on spacer sticks with the bark facing up, the pile growing in neat rows. A sharpening file and bar-oil bottle sit on a stump.
```

### 8. Chapters 30–31, the jig and the panel run (p132–137)

```text
Painterly workshop book illustration, warm light, precise detail, no text, no logos, no watermark. Landscape 3:2.

A flat plywood bench on sawhorses outdoors under a tarp. Screwed to the bench is a large triangular layout of wooden stop blocks. On it sits one finished triangular panel made of three split-log members (pie-slice cross-section, bark on the outside face). At each corner the members overlap one another in a pinwheel pattern: each member's end rests on the side of the next, and the very corner point is empty. Quick-clamps hold the members. Beside the bench, three separate stacks of members marked with coloured crayon stripes, and a few finished triangular panels leaning against a tree.
```

### 9. Chapter 32, "Raising" (replaces the p141 screenshot)

```text
Painterly book illustration, golden-hour light, no text, no logos, no watermark. Landscape 3:2.

A timber geodesic dome halfway raised: the bottom ring of triangular panels stands on wooden blocks, the second course is going up, and the top is still open sky. The panels are made of split-log members with bark on the outside and no metal connectors; the corners overlap like a pinwheel. Long temporary props of scrap wood brace the leaning panels from inside, angled down to the ground. A builder stands on a stepladder inside the frame, seen from behind, offering up one triangular panel. Calm, careful, one person's work.
```

### 10. "The frame, day fourteen" (replaces the p6 screenshot) — full page

```text
Warm painterly book illustration, golden-hour light, soft brushwork, no text, no logos, no watermark. Portrait 2:3.

The complete timber dome frame, finished, standing in a woodland clearing. The dome is a two-frequency geodesic hemisphere about 22 feet across and 11 feet tall, made of 40 flat triangles; five triangles meet at the top. Every triangle is a separate framed panel of three split-log members: long pie-slice-shaped sticks with rough bark on the outside and pale flat sawn faces. No metal hubs or plates; at each corner the members overlap like a pinwheel and the corner point is empty. Thin seams between neighbouring panels. Low sun shining through the open triangles, long triangular shadows on the grass. A single builder stands at a distance looking at it, small in the frame.
```

### 11. Chapter 44, "Inside a Round Room" (p185)

```text
Cosy painterly interior book illustration, warm lamplight and a little daylight from above, no text, no logos, no watermark. Landscape 3:2.

Inside a finished small dome cabin about 22 feet across. The curved wall shows the triangular timber frame of split-log members (bark faces outward, flat sawn faces visible inside) with quilted fabric insulation between them. A round wooden table sits in the centre under the highest point, where a skylight panel lets light down. Around the edge, where the ceiling slopes low, a low bed, built-in curved benches, a small wood stove on a hearth and low shelves. Rugs on a wooden floor. The centre is open; the furniture is in the ring.
```

### 12. Chapters 40–42, skin, seams and rain (p167–177)

```text
Painterly book illustration, light rain, soft overcast light, no text, no logos, no watermark. Landscape 3:2.

A small skinned timber geodesic dome cabin: its 40 triangular panels are sheathed and roofed, each seam covered with an overlapping flashing strip laid like shingles so water runs downward over every joint. At the base, an overhanging brim with a gutter lip catches the rainwater and a single downpipe carries it into a round water tank half-buried beside the dome. Rain streaks visible on the shell, water dripping clear of the base. One rectangular door in a short vertical wall at the base.
```

### 13. Chapter 61, "The Quilt Network" (p270)

```text
Warm painterly domestic book illustration, evening kitchen light, no text, no logos, no watermark. Landscape 3:2.

A kitchen table with a sewing machine, a pile of old t-shirts and flannel shirts, scissors, and a large finished triangular quilted panel stitched from many recycled fabrics, padded and thick, with a small handwritten fabric tag sewn on one corner. Hands guiding fabric through the machine; no face shown. A second triangular panel half-finished. Homely, generous, unhurried.
```

### 14. Part 2 opener, "Why It Scales" — full page (replaces text-only p217)

```text
Warm painterly book illustration, late-afternoon light over a meadow, no text, no logos, no watermark. Portrait 2:3.

Three timber geodesic dome cabins of three different sizes, small, medium and large, stand on round gravel pads in a gently sloping meadow at the edge of woods. All three are built the same way: triangular panels of split-log members, no metal hubs, skinned in muted natural colours. A short gravel path joins the pads; a small shared utility post with a meter box stands between them. A few trees, a vegetable garden by the smallest dome. Calm, plausible, not futuristic.
```

### 15. Part 3 opener, "Variations and Future Systems" — full page (replaces text-only p308)

```text
Warm painterly book illustration, soft sunset, no text, no logos, no watermark. Portrait 2:3.

A timber geodesic dome frame wearing a soft outer skin: a pale, slightly glossy rain-cap membrane pulled over the whole dome and strapped down at the base like a fitted cover, with thick quilted layers visible at one open edge. A slim timber-clad mast rises out of the very top of the dome. Behind it, faint in the distance, the bare frame of a second dome. Inventive but practical, still clearly handmade from wood.
```

### Optional — a cover painting that matches the method

Your re-lettered painting is finished. It shows sawn boards on a deck with concrete piers, though, and the book is about split wedges hung between trees. If you ever want the cover to match the book:

```text
Warm painterly book-cover illustration in the style of a classic woodworking book, golden-hour sunset over a lake and pine forest, rich colour, soft brushwork, no text, no letters, no logos, no watermark. Portrait 2:3; leave the top third as open sunset sky for a title.

A complete timber geodesic dome frame, a two-frequency hemisphere of 40 triangles with five triangles meeting at the top, built from split-log members: long pie-slice-shaped sticks with rough bark outside and pale flat sawn faces, no metal connectors, corners overlapping like a pinwheel. The frame stands on wooden blocks in a clearing. In the foreground: a pine round split into eight wedges like a cake, a stack of split wedges bark-up, a small orange chainsaw on a stump, an axe, sawdust. A builder, seen from behind, fits one triangular panel.
```

When an image comes back, check it against the geometry before you use it:
- five triangles at the top;
- triangles, not hexagons;
- no metal hubs;
- bark on the outside face.

Then caption it as an illustration.
