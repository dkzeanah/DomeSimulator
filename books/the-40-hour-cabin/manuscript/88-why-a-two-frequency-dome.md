---
chapter: 88
title: Why a Two-Frequency Dome
strand: explain
status: draft
target: 1150
updated: 2026-10-27
---

# 88. Why a Two-Frequency Dome

This part is a deep dive into the member — what a split wedge is as structure,
and everything it can build once you stop asking it to be a rectangle. But a
member is a member *of* something, and before the dive it is worth saying why
the something, for this whole book, is a two-frequency geodesic dome. Not a
three-frequency one, not a four, not a stick-framed box. A 2V hemisphere, and
the wedge, are made for each other, and the reasons are the same reasons the
rest of this part is about to unfold.

![The reference build: a two-frequency hemisphere, framed from split wedges.](standard-dome.png)

A frequency is just how many times you subdivide each face of the underlying
solid before you push the new points out onto the sphere. One-frequency is the
bare icosahedron — too few, too flat, not yet a dome. Raise the frequency and
the shell gets rounder, the triangles smaller, and the count of everything —
lengths, angles, joints — climbs fast. Two-frequency is the first subdivision
that is genuinely a dome and the last one that is still simple. It is the
coarsest usable geodesic there is. And coarse, it turns out, is exactly what a
split, variable stick wants.

## Two lengths, and a tree makes two lengths

A 2V hemisphere has exactly **two** edge lengths. In the reference build they
are the long chord at {{cut.a_chord}} inches and the short chord at
{{cut.b_chord}} inches — and the short one is not a second choice, it is what
the geometry forces once you fix the long one (Chapter {{ch.two_lengths}}). The
entire {{dome.members}}-member frame is those two lengths, repeated across
{{dome.panels}} triangles.

Now look at what a log gives you. Buck a trunk to one section length and split
it into sectors, and you get a pile of near-identical struts — same length,
same sector angle, differing only in the slow taper up the tree. The wood's
natural product is *a few lengths in quantity*, not forty distinct sizes each
needed once. The 2V's two-chord frame is the shape that consumes that product
without waste. A higher frequency would hand you a cutting list of many lengths
and many angles, and ask the most variable building material you could pick to
hit all of them. Two lengths against two lengths is not a coincidence you
engineered; it is the match that made the method worth writing down.

## The shell loads the blade where the blade is strong

Part 1 of this book opens on a claim it spends chapters defending: a dome
resolves its loads **axially** (Chapter {{ch.lumpy}}). Every member spends its
life mostly holding its own length — pushed and pulled along its grain — while
the triangulated shell absorbs the asymmetry that a post-and-beam frame would
amplify.

That is the one load a wedge is superb at. The next chapter, {{ch.families}},
shows a split sector for what it is: a deep, narrow blade, magnificent along one
axis and feeble across the one at right angles to it. A geodesic shell asks the
member for exactly the axis the blade is strong on, and the triangulation braces
the axis it is weak on — for free, because the bracing was going to be there
anyway. Stand the wedge point-inward, as the reference build does, and its depth
lies along the dome's own radius, which is the direction the shell wants
stiffness (Chapter {{ch.member}}). The structure and the stick agree about which
way is up.

## The sector is the seam budget

Here is the fit that still feels like a gift. Split a log into eighths and each
wedge is a {{cut.sector}}-degree slice. Build the 2V dome and each seam between
two panels has to close a fold, with some sector angle left over. From the
solve: an A seam folds {{seam.fold_a}} degrees and leaves {{seam.gap_a}} over;
a B seam folds {{seam.fold_b}} and leaves {{seam.gap_b}}.

Add each pair. Both come to {{cut.sector}} degrees — the sector angle itself.
The angle you split out of the tree is the exact angle budget the 2V dome's
seams need to spend. That is the closest thing this method has to a theorem, and
it is a 2V fact: the dihedral angles of this shell, and the eighth-of-a-log
split, were made to meet. Change the frequency and the seams fold through
different angles, and the tidy arithmetic stops being tidy.

## Coarse enough to forgive a split stick

The last reason is the one Part 1 gave first, turned toward frequency. Because
the shell forgives error — because a triangle a degree out is still a triangle —
the frame is the part you are *allowed* to get wrong, and that permission is
what lets a split log be a structural member at all.

A low frequency spends that permission well. It has few, large joints, and a
large joint carries more tolerance than a small one: a sixteenth of an inch is
nothing across a six-foot chord and everything across a one-foot web. A natural
wedge is variable — in taper, in grain, in the odd check — and a 2V dome
tolerates that variation better than any finer shell could, because a finer
shell demands an accuracy the wood will not reliably give.

So the deep dive that follows is really a deep dive into one member of one
shape. The member is more general than the dome — it makes beams, columns,
frames and shells, and the rest of this part is those. But the dome is where the
member is most at home, and the two-frequency dome most of all: two lengths for
a two-length wood, an axial shell for an axial blade, a seam budget the split
already pays, and a tolerance the stick can actually hit.
