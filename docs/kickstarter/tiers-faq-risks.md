# Tiers, FAQ, and risks — for the campaign page

> **Numbers in this file come from the model.** Regenerate them with
> `py -3.12 -m campaign` (writes `deliverables/campaign/campaign-page.md`)
> and check them with `py -3.12 -c "import campaign; campaign.validate_kit()"`,
> which fails on any figure the model does not produce.

All prices below are the live model's numbers (see `README.md`); anything
marked [OWNER] is a decision the campaign owner makes, not a number an
LLM should invent. Early-bird discounts are [OWNER] decisions — the model
does not invent them, and neither should the copy.

## Reward tiers

Generated from `kickstarter.tiers()`; every tier's cost to deliver and its contribution to the goal are in the model.

| pledge | what it is |
|---:|---|
| **$35** | **The drawings and the numbers.** Every table in the book, the cut list for any diameter, and the solver that made them. It is a download; the two dollars is card fees and hosting |
| **$95** | **Quilter's kit.** Pattern, thread, the binding, and the layer specification -- how big, how thick, how to close the edge. Sew a layer for your own dome, or sew one for somebody else's and get paid for it |
| **$180** | **One bay's hardware set.** Four threaded inserts, the flange screws, the spline gasket and the seam key for one triangle. The smallest piece of the building that is a real object rather than a drawing |
| **$1,450** | **A shower cap for your dome.** The rain-slick outer cap, made to the reference diameter, hemmed with grommets and strapping. The only watertight layer in the building, and the one you cannot sew at home |
| **$2,400** | **The utility hub.** The centre column, assembled and tested: pad port, water manifold, drain stack, sub-panel, riser and seal cap. The part an owner cannot make and the part the goal exists to get right |
| **$19,800** | **Dome kit, frame included.** Everything, including the timber, for somebody with no trees. The expensive version, honestly priced: you are paying for somebody else's 45 percent recovery |
| **$11,400** | **Dome kit, bring your own trees.** Everything except the frame. You fell, split and cut the members from your own land -- which is the whole argument -- and we send the rest |
| **$640** | **Pad host's pack.** The platform drawings at five foundation types, the service-port spec, the rim latch pattern, and the host's costing sheet. For somebody with land who wants a dome to be able to land on it |


## FAQ (draft answers — the brief already speaks these)

**What exactly is the stem cell?** One 2V hemisphere: 19.42 ft across,
277 sq ft of floor, forty triangular bays, 120 wedge struts. It ships as
hardware and the seam hose — the frame is split out of about 1.5 of the
buyer's own standing trees.

**What is the shower cap?** The standard weather skin: outer wood
panels, one monolithic membrane, quilted layers of recycled clothing at
$50 a layer, and a rain-slick cap strapped over the lot. It replaces the
hull *and* the bay sandwich — $6,434 less at three quilts — and it grows
a layer at a time, which a rigid hull cannot.

**Is the cap as good as the hull?** No, and the campaign says so: the
cap is not structural, its outer layer is sacrificial (about 8 years),
and fabric between two impermeable layers is a moisture question the
seam duct is meant to answer. The hull is the fifty-year upgrade, and it
fits the same frame whenever you want it.

**What about the floor?** It is the upgrade, bought after the dome:
$1,899 of hub, spokes, deck and rail, clamped to a $622 mast that runs
through the utility column. The pad's deck belongs to the host; the
dome's floor belongs to you and moves with the dome.

**Can it really hang between trees?** It is priced ($1,490) and drawn —
and every load is the engineer's number. The campaign presents it as a
design possibility, not an engineered product.

**Why is there no foundation in the price?** Because a buyer who moves
should not buy a deck twice. The host builds the pad ($6,240) and keeps
it; the dome lands on it and plugs in at one service port.

**Is the $50 quilt real?** The fabric is a waste stream — thrift-store
blankets and recycled clothing, quilted by the owner. The model prices
the yard-priced alternative too (~$670 at the first size), so the choice
is a choice, not a trick.

**What does "the core moves" mean?** The utility column — sub-panel,
manifold, drain, light, fan, cooling — unbolts and goes into the next
dome. Seven hours once, not seven hours per dome.

**Do I need a permit?** [OWNER/JURISDICTION — the campaign's standing
answer: a round building drawn by its builder gets asked questions a
rectangle never gets asked; nothing here is offered as code-compliant.]

## Risks & challenges (Kickstarter's required section — draft)

**The honest four, from the model:**
1. The cap is not structural — uplift rides the anchors and the frame,
   and the frame must be good for the whole wind load. This is priced
   and stated; it is also a real risk to fix early in production.
2. The outer layer is sacrificial and must be replaced on a schedule —
   the thirty-year arithmetic includes it, but backers must budget it.
3. The quilt sits between two impermeable layers: in a cold climate the
   dew point lands in the fabric. The seam-duct airflow is the designed
   answer and it is **an experiment, not a solved problem** — the
   campaign is partly asking for the money to run it.
4. It looks like a tarp to some people — planners, resellers and
   neighbours. No arithmetic answers that; the page names it instead.

**Manufacturing:**
5. [OWNER] tooling, moulds, the first production run, and freight
   (regional, $1,250 flat-packed) — timeline risk belongs here.
6. [OWNER] the window-unit cooling sizing and the empty cavity on day
   one are honest product states, not defects — say so.

**Engineering:**
7. Every structural rating — mast, ring, hoist, cables, trees — is an
   engineer's number. Nothing in the campaign substitutes for
   site-specific engineering, and the page says so on the tier cards,
   not in a footnote.

**Team:**
8. [OWNER] who is building this, and what they have already built. The
   one standing prototype and its photographs go here — the campaign's
   credibility is that build, and no render can stand in for it.
