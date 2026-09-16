---
chapter: 19
title: Method B: From the Tree You Have
strand: howto
status: drafting
target: 2450
updated: 2026-09-08
---

# 19. Method B: From the Tree You Have

*Section length in, dome out*

<!-- Every number in this chapter must come from:
     - book_math.tree_first
     - book_math.BOOK_TREE
     Quote them as live tokens in double braces, never as
     typed digits. The Numbers panel lists every one. -->

## Method B

This is the method the book is named after, and it is the one that produced
the dome in the photographs. It starts from a tree lying on the ground and
ends with a number you did not choose.

That last part is the whole character of the method. In Method A you decide
how big the building is and the woodpile has to comply. Here the woodpile
decides, and your job is to find out what it decided.

## The procedure

### 1. Measure the trunk

Three numbers: diameter at the butt of the usable length, diameter at the
top of it, and the straight length between them.

"Usable" means the part with no bend serious enough to spoil a section and no
branch stub big enough to spoil a stick. It is almost always shorter than the
tree. On this book's tree it was {{tree.usable_length_ft}} feet, out of a
considerably taller pine — the butt flare went in the fire and the top went
for kindling.

The tree this book is written around measures {{tree.butt_diameter_in}}
inches at the butt of that length and {{tree.top_diameter_in}} at the top.

![The book's tree, measured.](../../deliverables/book/figures/tree-measured.png)

### 2. Pick a bucking length you can carry

This is the decision, and it is a physical one rather than a mathematical
one. Go and pick up a green section of the length you are considering. If you
cannot get it onto a sawhorse on your own, it is too long, and no amount of
wanting a bigger dome will change that on day six.

This book buckes to {{tree.section_length_ft}} feet.

Everything downstream comes from this number. Choose it honestly.

### 3. Count your sections

Divide the usable length by the bucking length and throw away the remainder.
{{tree.usable_length_ft}} feet at {{tree.section_length_ft}} feet a section is
{{tree.sections}} sections, with {{tree.offcut_ft}} feet left over.

If the remainder is large it is worth going back to step 2 and trying a
different bucking length. A foot of offcut is firewood; four feet is a stick
you did not get.

### 4. Multiply by eight

Each section splits into {{tree.sectors}} sectors of
{{tree.sector_angle_deg}} degrees each, and — this is the part that surprises
people who have milled lumber — **each sector is a finished structural
member**. Not a blank to be trimmed. Not stock to be dimensioned. A member.

{{tree.sections}} sections × {{tree.sectors}} sectors =
**{{tree.struts_per_tree}} struts from one tree.**

Two trees: **{{dome.struts_available}} struts.**

The frame needs **{{frame.members}}**.

That is the title of the book, and it is not a slogan. It is
{{dome.spare_struts}} spare — about seven per cent — which is roughly the
right margin for a stick that splits along the pith, a butt cut that goes
wrong, and the one panel everybody builds backwards.

![Eight sections of six feet.](../../deliverables/book/figures/bucking-plan.png)

### 5. Find your member's width

The dome does not care how long your sticks are until it knows how *wide*
they are, because the pinwheel setback depends on width.

The width of a sector is the chord across its bark face, measured at the
diameter you are cutting. Use the diameter at the **middle** of the trunk,
not the butt: half your sections come from thinner wood than the butt
suggests, and sizing the layout off the fat end gives you a dome that does
not quite close at the top.

At this tree's mid diameter the sector is {{member.width_in}} inches wide and
{{member.depth_in}} inches deep, pith to bark — a cross-section of
{{member.area_in2}} square inches.

For scale: that is {{member.as_nominal_2x4s}} nominal two-by-fours' worth of
wood, or {{member.as_dressed_2x4s}} of the dressed boards you would actually
find on a rack. Chapter {{ch.money}} is about which of those numbers to believe.

### 6. Solve for the dome

Now the arithmetic. The longest member the frame may contain is the longest
stick you have, which is your bucking length: {{tree.section_length_ft}} feet.

Find the radius whose longest pinwheel member is exactly that.

This is not a division. As Chapter {{ch.which_way}} explained, member length is radius less
a setback that does not scale, so the relationship has to be solved rather
than scaled. The software in this project does it by bisection, and you can
do it by trying radii until the longest member comes out right — it converges
in about six guesses.

The answer for this tree:

| | |
|---|---|
| Radius | {{dome.radius_in}} in |
| Diameter | **{{dome.diameter_ft}} ft** |
| Height at the centre | {{dome.height_ft}} ft |
| Floor | **{{dome.floor_sqft}} sq ft** |

![Two trees, worked all the way through.](../../deliverables/book/figures/method-b-worked.png)

### 7. Read your cut list

The frame's {{frame.members}} members come in {{dome.member_lengths}}
lengths, running from {{dome.shortest_member_in}} inches to
{{dome.longest_member_in}} inches. Thirty of each.

Note that the longest is exactly your stock length, to the last decimal
place. That is not a coincidence and it is not luck — it is what step 6
solved for. It also means you have no margin on the long members at all,
which is why they are cut with the head end deliberately left over-long and
sawn off in place. Chapter {{ch.head_overfit}} is about that.

![Every stick in the dome.](../../deliverables/book/figures/member-classes.png)

## You do not get to choose the diameter

This is the part people resist.

You measured a tree, you picked a length you could lift, and out came
{{dome.diameter_ft}} feet. Nobody consulted you. If you wanted twenty-four
feet you cannot have twenty-four feet — not from these trees, bucked this
way, without doing something else that costs you elsewhere.

You have three ways out and they are all in Chapter {{ch.numbers_say_no}}:

* **Buck longer.** A longer section gives a bigger dome, out of fewer and
  heavier pieces, and at some point two trees stop being enough. The table in
  Chapter {{ch.method_b}}'s appendix shows exactly where that line is.
* **Get a third tree.** Fine, if you have one. It is the honest answer and it
  is not a failure.
* **Accept the dome the trees gave you.** Which is what happened here.

What you must not do is design for the dome you wanted and cut for the tree
you have. The frame will not close, and it will not tell you until the last
ring.

![Bucking length against dome size.](../../deliverables/book/figures/tree-lookup.png)

## A note on the second tree

Two trees is {{dome.struts_available}} struts for a
{{frame.members}}-member frame, so the frame actually consumes
{{dome.trees_strictly_needed}} trees. The second tree is not fully used, and
the leftover is not waste — it is the next dome's spare parts, or a porch, or
the sawhorses.

But it does mean the honest headline is not "one dome from two trees." It is
"one dome from a bit under two trees, and you need the second one because you
cannot get eight-tenths of a tree."

Which is a worse title.
