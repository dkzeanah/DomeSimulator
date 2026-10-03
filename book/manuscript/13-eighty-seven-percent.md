---
chapter: 13
title: Eighty-Seven Percent
strand: explain
status: drafting
target: 3300
updated: 2026-09-17
---

# 13. Eighty-Seven Percent

*The recovery arithmetic, with the kerf paid for*

> **This chapter corrects something.** The 88% recovery figure in the project brief, which was computed for a 15-inch butt rather than this book's 12-inch tree.

## Eighty-Seven Percent

The headline number of the whole method, stated once with its caveats
attached, because the caveats are where the number lives:

Split the way this book splits, and a trunk keeps {{tree.recovery_pct}}
per cent of its solid wood as structural members. Sawn the way a mill
saws, the same trunk keeps about {{tree.sawn_recovery_pct}}. That is
{{tree.recovery_gain}} times the usable wood, from a cheaper process,
with one machine instead of four.

The caveats, in the same breath: the {{tree.recovery_pct}} counts
*split wood only* — nothing planed, nothing dried, nothing graded; the
sawn comparison is the honest one for two-by-fours packed in a circle,
which is flattering to neither side; and the famous "88 per cent" from
this project's earlier films belongs to a bigger tree than this book's.
This book's tree is {{tree.butt_diameter_in}} inches at the butt and
keeps {{tree.recovery_pct}} per cent; the films' tree is
{{pine.butt_in}} inches and keeps {{pine.kerf_only_pct}}. Both numbers
are correct, for different trees, and the last page of this chapter
prints both rather than quietly picking the flattering one.

The rest of the chapter is the arithmetic, so the headline stops being a
claim and becomes a thing you could re-derive with the saw's kerf in
your hand.

## What a mill loses, and to what

A sawmill's job is to turn a round log into rectangular boards, and
everything it loses is the price of the rectangle.

**The slabs.** A circle does not contain its rectangle. The two rounded
sides of the log — the slab wood — cannot become boards of any width,
so they come off first, and they are the biggest single loss. On a
small log they are a huge fraction of the circle; the fatter the log,
the smaller the fraction, which is why mills pay per board foot and
prefer the big trees.

**The edgings.** Even the boards cut from the heart of the log carry
wany edges — bark, roundness — and must be edged square. More wood off.

**The trim.** Boards are sold in even lengths, square at both ends.
Every board loses its trim.

**The kerf.** Every cut turns wood into sawdust. A mill's band or
circle blade is thinner than a chainsaw's, but a mill makes far more
cuts per log, and the kerf is paid on every one.

**Drying degrade.** The boards are stickered, stacked and dried, and a
fraction of them check, cup, twist or stain past their grade. The wood
was there; the board is not.

**The grade fall.** Of what remains, some boards grade lower than the
rest, and low-grade lumber sells for less — a loss in value even when
nothing is lost in volume.

Add the five together and the famous range appears: a log sawn into
two-by-fours keeps roughly half of itself as saleable lumber. This
book's tree, packed honestly with true two-by-fours, keeps
{{tree.sawn_recovery_pct}} per cent. None of that is incompetence. The
mill is extremely good at a job whose product is a rectangle, and the
waste is the price of the rectangle — paid in wood, at every station of
the chain Chapter {{ch.middlemen}} walked.

## What the wedge loses

Now convert the same trunk the wedge way, and count the losses again.

**The bark.** Lost either way; it was never wood. Not counted against
either method.

**The kerf — and that is nearly all.** The wedge makes seven cuts per
section, through the full diameter. Each cut is a {{saw.kerf_in}}-inch
kerf — a chainsaw's kerf, fatter than a mill's blade — and across
{{tree.sections}} sections the kerf bill comes to {{tree.kerf_bf}}
board feet of the trunk's {{tree.solid_bf}}. That is the honest, paid
price: {{tree.kerf_bf}} board feet of sawdust.

**Nothing else.** No slab, because the sector uses the whole radius.
No edging, because nothing needs a square edge. No trim beyond the
bucking. No drying degrade to speak of — a wedge is allowed to move as
it dries, and Chapter {{ch.other_species_other_sections}} explains why
a split moves less than a board. No grade fall, because the book grades
its own pile by eye and uses the rejects for blocking.

So the ledger closes: {{tree.solid_bf}} board feet in the trunk, minus
{{tree.kerf_bf}} of kerf, leaves {{tree.wedge_bf}} board feet of
structural member — {{tree.recovery_pct}} per cent — at
{{tree.bf_per_strut}} board feet a stick, which is what the worked
build in Chapter {{ch.worked_build}} turns into a cut list. The wedge
does not beat the mill at milling. It beats the mill at *this* — making
a structural member for a frame that never asked for rectangles — and
the beat is the difference between {{tree.recovery_pct}} and
{{tree.sawn_recovery_pct}} per cent of the same tree.

![The same log, converted twice. {{tree.recovery_pct}} percent against {{tree.sawn_recovery_pct}}.](../../deliverables/book/figures/recovery-compare.png)

## Both conversions, same log

The drawing shows the same round section twice. On the left, the mill's
version: rectangles packed into the circle, slabs and edgings falling
away to the outside, the honest count of what a two-by-four economy
keeps. On the right, the wedge's version: the circle divided into
{{tree.sectors}} equal sectors, and every sector kept whole.

The picture makes the argument the numbers cannot. The mill's losses
are the *outside* of the circle — the part farthest from any rectangle.
The wedge's only loss is the thin lines of the kerf itself, running
through the middle. The mill throws away the corners; the wedge keeps
the corners and throws away the cut lines. The corners of a round log
are not bad wood. They are perfectly good wood of the wrong shape, and
"wrong shape" is a judgement the rectangle made, not the tree. Chapter
{{ch.triangles}} is the reason the frame is allowed to disagree, and
this drawing is the disagreement, priced in board feet.

## Section by section

The table carries the comparison down the whole trunk, one bucked
section per row, both conversions, because a taper means the answer is
not one number but a run of them — and the run is what you actually
cut.

Each {{tree.section_length_ft}}-foot section of the trunk is a slightly
smaller circle than the one before it. The butt section packs more
rectangles and yields fatter sectors; the top section packs fewer and
yields slimmer ones. The table shows both columns shrinking as the
taper runs, and the recovery staying where the geometry put it: the
wedge's advantage is not a lucky average, it is a property that holds
section by section, from the {{tree.butt_diameter_in}}-inch butt to the
{{tree.top_diameter_in}}-inch top. Read it as a check on the headline
rather than as a second claim: if any row disagreed with the story
above, the story would be the thing to fix.

## Where 88 became 87

The errata page, because this project said "88 per cent" on camera and
this book prints {{tree.recovery_pct}}, and a reader who notices the
gap deserves the explanation rather than the silent edit.

The films' recovery figure — {{pine.kerf_only_pct}} per cent — was
computed for the films' reference tree: {{pine.butt_in}} inches at the
butt, {{pine.length_ft}} feet usable, the big plantation pine of the
pine-value film. A fatter log puts more wood inside its circle and less
into its slabs, so the same split-and-kerf arithmetic keeps more of it:
{{pine.kerf_only_pct}} per cent.

This book's tree is smaller — {{tree.butt_diameter_in}} inches at the
butt, {{tree.usable_length_ft}} feet usable, the windfall of Chapter
{{ch.the_tree_that_was_already_down}} — and the same arithmetic, run on
the smaller circle, keeps {{tree.recovery_pct}} per cent. The kerf is
the same {{saw.kerf_in}}-inch chain; the circle it eats is simply a
smaller fraction of a smaller pie.

Neither number is wrong, and neither was ever a lie. They are two
recoveries for two different trees, and the earlier films named their tree while
this book named a different one. The book's discipline — stated on this page, and kept on every errata
page like it — is that a correction names
the error, prints both numbers, and leaves the arithmetic visible. That
is what this page is: {{pine.kerf_only_pct}} for the pine the films
priced, {{tree.recovery_pct}} for the tree this book builds, and the
reason they differ is the diameter, printed in the table above, one row
per section.
