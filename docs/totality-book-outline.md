# The three-part book — proposed structure

Status: **mostly built as of 2026-09-17.** The structure below landed as two
parts (the biography is still parked), Part 3 is drafted end to end, and the
manuscript-state section at the bottom of this page has been replaced by a
live view. What remains is Part 1 prose and the biography.

## What this book is

Every concept the films have put on screen, in one volume, ordered so that each
chapter only needs what came before it. Three parts, as asked:

1. **Who this is for** — the story, and why the rest of the book exists.
2. **How to build one** — the method, the bench, the fortnight, and the
   off-the-wall hardware that is not built yet.
3. **Why it scales** — the argument that the same list of parts covers a small
   house and a large one, and what that does to cost, labour and land.

It **absorbs the existing 52-chapter book** (`2 Trees: Build Your (D)Home`) as
Part 2 rather than sitting beside it. All 52 chapters and 99 rendered figures are
reused; the nine existing parts become *sections* inside Part 2, so nothing is
lost and no prose is rewritten.

## Why coverage is checkable — within limits

`two_v_demo/lexicon_concepts.py` already holds **62 concepts**, each with a
claim, an explanation, a caveat, the films that teach it
(`taught=("film:2v/phi", ...)`), and a figure recipe. That is the author's own
taxonomy of what the corpus asserts.

So most of the book's completeness is provable: **every one of the 62 concepts
is assigned to a chapter, and a test asserts none is orphaned.** A concept the
films teach but the book omits becomes a failing test, not an oversight.

```
py -3.12 -c "from two_v_demo import lexicon_concepts as lc; print(len(lc.CONCEPTS))"
```

**But the test is necessary, not sufficient, and it would be dishonest to call
it totality on its own.** Three gaps, all confirmed:

- **The iris is not a lexicon concept.** The `iris` in `lexicon_taxonomy.py:338`
  is the flower, in the noun vocabulary — a false positive. The pad iris exists
  only as arithmetic and film (`park_model.iris_span` / `iris_cost`, taught in
  the `iris` and `panel_lip` chapters).
- **Rotation is arithmetic and film, not a concept entry.** It lives in
  `park_model.py:50` (`rotation_ring_usd_per_ft`) and `park_world.py:291`.
- **There is a 35th film outside the registry.** `deliverables/tree-value-video/build/content.py`
  is a complete authored script with no lesson module and no registry entry —
  the only such folder in `deliverables/`. It restates the `pine_value` ladder
  with different, dated sourcing (TimberMart-South Q2 2026 pine sawtimber
  $23.34/ton; Alabama Q4 2025 stumpage $17–21/ton), so where it and `pine_value`
  disagree, the book has to pick one and say why.

So coverage is checked two ways: the 62 concepts by test, and the chapters the
taxonomy does not know about by a hand-kept list — `iris`, `rotation`, `line`,
`network`, and the tree-value film's own sourcing.

## The corpus this draws on

34 lessons, 1,127 chapters. The material that matters most for Parts 1 and 3:

| Source | What it contributes |
|---|---|
| `hype3` (Frankendome v3) | The only sustained autobiographical chapter in the corpus — the women, the reduced-price school lunch, hearing Fuller, the igloo as existing proof. |
| `byod_deepseek` `my_story`, `little_guy` | Nineteen and five grand, the military, the trailer, the mother who worked both school programmes. |
| `franken_economics.py` | **`flat_rate_labour`** — the same 40 triangles, 120 struts, 120 brackets, 960 screws and 9 distinct processes at *any* diameter. Only strut-feet grows. |
| `energetics.py` | The metabolic ledger — 1,322 parts, 16,751 kg, seven motions, 109,741 kcal to build one house; fastening spends 90% of the fuel while raising nothing. |
| `park_model.py` | Hardware invariance, the pad, the iris, rotation, the shell ladder, the stay-crossover, resale recovery. The resale argument is *started* in the existing book (`book.py:792`, "Permits, appraisals and resale") but never carried; the computed substance is `recovered()` / `penalty()` / `total()` with `resale_haircut_fraction`. |
| `deliverables/tree-value-video/` | A 35th film with no registry entry — the tree-value ladder, sourced and dated differently from `pine_value`. |
| `dome_performance.py`, `dome_advantage.py` | Envelope per floor, the pony wall, the brim as gutter, sky-cooling paint, wind drag 0.42 against a box's 1.05. |

## Part 1 — Who this is for  ·  PARKED

**Not being written yet, by request.** The material is real and already in the
corpus — `hype3` carries the women, the reduced-price lunch, hearing Fuller and
the igloo; `byod_deepseek` carries the cheque at nineteen, the six years gone
and the mother who worked both school programmes in one day — but it is his
account to give, not mine to assemble. The book is being built without it, and
Part 1 drops in at the front when he is ready.

Nothing downstream depends on it: the two written parts stand on their own.

## Part 2 — How to build one

**52 chapters, reused as they stand.** Sections keep the existing nine groupings,
which become dividers instead of parts:

Two Trees · Why a Dome Lets You Do This · The Wedge · The Two Calculations ·
The Fortnight · The Jig and the Cuts · From Frame to Home · What It Actually
Cost · Take It Further

Plus a short new opening chapter bridging Part 1 into the method.

## Part 3 — Why it scales

**~16 chapters, all new.** This is the part the corpus argues hardest and has
never stated in one place. It is the answer to "why does this become easier the
more of it there is".

| # | Working title | Concept it carries |
|---|---|---|
| 1 | The list that does not grow | `flat_rate_labour` — the engine of the whole part |
| 2 | Nine processes at any size | `DomeSize`, the flat-rate table |
| 3 | What an hour of yours is worth | `an_hour_at_the_log`, the leverage argument |
| 4 | Where the fuel actually goes | the metabolic ledger, 90% spent fastening |
| 5 | Less skin for the same floor | `less_skin_per_floor`, envelope per floor |
| 6 | The cheapest square footage in the building | the pony wall |
| 7 | The roof is a gutter | `brim_is_a_gutter`, 7,259 gallons |
| 8 | A house that gets warmer every winter | `keep_the_bones`, the shell ladder |
| 9 | One hardware set, three sizes | `park_model.hardware_invariance` |
| 10 | Buy for the next two steps | the growth path |
| 11 | The ground is what you cannot take with you | `foundation` — 8% to 63% measured |
| 12 | A pad, not a plot | the park, the host, the tenant, the line |
| 13 | Turning the house toward the sun, until it stops being worth it | rotation and tracking — **and the caveat, not the +25% alone** |
| 14 | One pad, every dome size | the iris |
| 15 | Why a network beats a park | `number` — the resale thesis |
| 16 | What would have to be true | the honest limits, stated as limits |

## Figures

99 rendered figures and 86 rendered plates already exist. New material needs
new pictures, and all of them come from the model rather than from a drawing:
the flat-rate table as a chart, the metabolic scatter, the envelope-per-floor
ranking, the crossover curve, the pad and its parts.

The rule the repository already enforces applies unchanged: a number in the
prose is a `{{token}}` resolved from code at export, never typed. `book_tokens.py`
holds 145 of them today.

## How it gets built

1. Add `section` to `Chapter` (trailing, defaulted — existing chapters unmoved).
2. Assemble `PARTS` as three parts; `_absorb()` renumbers the 52 existing
   chapters in one place and sets each one's section from its old part title.
3. Run `sync_filenames()` and verify all 52 filenames match the new numbering.
4. Write Part 1 and Part 3 as new chapter files, scaffolded then drafted.
5. Add the coverage test: 62 concepts, every one assigned to a chapter.
6. Build HTML and PDF, then look at pages from each part.

`Chapter.ref` makes step 2 safe: prose writes `{{ch.method_a}}`, not "Chapter
18", so renumbering cannot break a cross-reference.

## Decisions taken

- **Tighter cut, without cutting fidelity.** Prose gets denser; nothing unique
  is dropped. Concretely, a page may lose padding, restatement and throat-
  clearing, and may **not** lose a concept, an argument point, an opinion, a
  measured figure, or a caveat. The length comes out of the writing, not out of
  the content.
- **Told in his words.** New prose is written in the register the films already
  use — the first person from the narration, the same blunt constructions. The
  corpus is the style guide, not my own voice.
- **Biography parked.** Part 1 waits.
- **Digital first.** The proven HTML + PDF build; the KDP paginator stays
  available if a paperback interior is wanted later.

## The manuscript state, measured

**The outline is complete; the prose is not.** This matters more than anything
else on this page, and an earlier draft of this document got it wrong.

```
status counts: {'outline': 44, 'drafting': 8}
total manuscript words: 14,284
```

- **8 chapters are drafted** — about 8,800 words, chiefly the two-calculation
  block (20–23) and three of the wedge chapters.
- **44 chapters are scaffolds** — a title, a purpose and a page plan each.
- The word counts in `BOOK.chapters` (2650, 3300, …) are **targets from the
  outline, not written prose.** Reading them as written was the error.

So there is very little to compress. "Tighter cut" therefore means writing the
remaining ~44 chapters and all of Part 3 tightly **from the start**, rather than
writing long and editing down. The target is roughly 140,000 new words, not a
155,000-word editing pass.

### State after the Part 3 build-out (2026-09-17)

The structure above has since been built. The current, live state is visible
with:

```
py -3.12 -c "from two_v_demo import book_manuscript as bm; print(bm.progress_report())"
```

and at the time of this update it was:

- **2 parts, 68 chapters, 772 pages targeted.** Part 1 = *How to Build One*
  (Ch. 1–52, the original book absorbed with its old parts kept as sections).
  Part 2 = *Why It Scales* (Ch. 53–68), matching the Part 3 table above —
  every chapter of it drafted at or beyond its outline target.
- **24 of 68 chapters have prose**; the remaining 44 are scaffolds. All 16 of
  Part 2's chapters are among the written ones, as are the two-calculation
  block and the wedge chapters from the original count.
- **885 live tokens** (was 145) — the new `flat.`, `nine.`, `rip.`, `log.`,
  `fuel.`, `skin.`, `pony.`, `brim.`, `ladder.`, `bin.`, `growth.`, `ground.`,
  `pad.`, `sun.`, `iris.`, `net.` and `honest.` namespaces all derive from the
  same modules the films teach from (`franken_economics`, `dome_performance`,
  `park_model`, `park_facts`, `house_economics`). Every token resolves; the
  export refuses an unknown one.
- **77 figures in the outline** (was 65); 75 resolve on disk. The one
  outstanding is `franken-standing`, a film still that needs PyOpenGL; the
  export prints the launcher action that produces it.
- **Reader-clean exports.** As of this update the exports omit unwritten
  chapters and matter rather than marking them, drop unrendered and
  photo-slot figures silently, and strip the manuscript's page-plan
  comments — a published copy shows no authoring machinery. The front
  matter now carries the title page, the copyright and the engineer's
  note (not a substitute for site-specific engineering), and the back
  matter carries the master tables, the glossary, the software section
  and the colophon. The publisher's KDP layout guidance and its mapping
  onto this book are in `docs/kdp-layout-mapping.md`.
- **Release exports built, versioned as always:**
  `deliverables/book/2-trees-v8.md`, `2-trees-v7.html`, `2-trees-v4.pdf`,
  `2-trees-outline-v5.txt`. The selftest is green end to end
  (`validate_everything()`).

What remains: the ~44 Part 1 scaffolds (the original 140k-word writing pass,
now tighter), the parked biography as a future Part 1, the coverage test that
asserts none of the 62 lexicon concepts is orphaned, and the `franken-standing`
still once a machine with PyOpenGL is at hand.

## What "tighter without losing anything" means in practice

With almost no prose to cut, this is a writing rule rather than an editing one,
and it is checked the same way:

- **Kept, always:** every one of the 62 lexicon concepts; every argument point
  and opinion; every measured figure; every caveat, including the unflattering
  ones (`park_facts.py:473` on where tracking stops paying; `honest_finished_number`;
  `energy_not_claimed`).
- **Cut:** restatement of a point already made, page-opening throat-clearing,
  and any sentence that only sets up a sentence that follows.
- **Measured:** the outline already tracks `words` per page and `sheets` per
  chapter, so a tightened chapter shows its own reduction, and a chapter that
  lost a concept shows up as a coverage-test failure rather than as a silent
  omission.

Doing this over 52 chapters is a substantial pass. It is staged deliberately:
the structure lands first and compiles, then compression proceeds chapter by
chapter with the concept test green at every step.
