---
chapter: 40
title: The Pentagon From Five Logs
strand: howto
status: draft
target: 2200
updated: 2026-10-14
---

# 40. The Pentagon From Five Logs

The dome needs something flat and level to stand on, and the cheapest flat,
level thing a builder with a chainsaw can make is a pentagon of five logs.
Not boards: logs. Each one a {{found.side_ft}} ft trunk split down its middle,
stood on edge with the round back facing out and the flat face facing in, the
five mitred together at the corners. Inside it goes a five-pointed star, and
the star is where the geometry gets kind.

## Start with the pentagon

A regular pentagon has five equal sides and five equal corners. Every corner
is {{found.interior}} degrees. With a side of {{found.side}} inches -- one log --
the pentagon is already decided: everything else about it follows from that
one length.

## Find the diagonal

Draw a line from one corner to the corner after next. That is the diagonal,
and in a regular pentagon it is always the side times the golden ratio,
{{found.phi}}:

```text
diagonal = {{found.phi}} x {{found.side}} in = {{found.diagonal}} in
```

## How the star splits the diagonal

Draw all five diagonals and you have the star. Each diagonal is crossed by two
others, so it is cut into three: a long piece, a short piece in the middle,
and another long piece. Because the pentagon is regular, the long piece is
exactly the diagonal minus the side, and the middle is what is left:

```text
long  = diagonal - side        = {{found.long_centre}} in
short = diagonal - 2 x long    = {{found.short_centre}} in
long + short                   = {{found.side}} in
```

That last line is the whole trick. One long piece and one short piece add up
to exactly one side -- to one {{found.side_ft}} ft log. Saw a log across, once,
in the right place, and both halves go into the star.

The star needs {{found.long_count}} long pieces and {{found.short_count}} short
ones. A log holds only one long piece, so the star takes {{found.star_logs}}
logs: {{found.short_count}} of them give a long piece and a short one, and the
other {{found.short_count}} give a long piece and an offcut of about
{{found.offcut}} inches -- a short piece's length again, spare for a step, a
block or the next floor. With the {{found.frame_count}} logs of the frame, the
foundation is {{found.logs}} logs and {{found.all_pieces}} pieces.

The geometric star alone uses {{wm.pent_interior_ft}} linear feet. With the
perimeter it uses {{wm.pent_all_ft}}. The ideal stock arrangement takes
{{wm.pent_logs}} side-length logs and leaves {{wm.pent_spare}} short-length
remnants. Those are a centreline stock calculation, before kerf and joint
adjustments; the next section gives the real cuts.

## The angle belongs to the joint

The perimeter's included angle is {{wm.pent_interior_deg}} degrees, and its
direction changes by {{wm.pent_turn_deg}}. A symmetrical perimeter mitre
is {{wm.pent_miter_deg}} degrees off square on each end. If instead one
perimeter member runs through and another butts to its side, the nominal
plan-view cut is {{wm.pent_butt_deg}} off square. A diagonal meeting a
perimeter member at {{wm.pent_diagonal_deg}} has a different side-face butt:
{{wm.pent_diagonal_butt_deg}} off square.

Do not swap those settings. They describe different mating lines in plan,
not bevels through the log. This foundation's perimeter uses the mitre;
the star's actual seats and thick-member end cuts come from the solid solver.

## What the saw actually cuts

Those are centreline lengths: the lengths of the lines on a drawing. A real
log has thickness, and the star's long pieces do not run into the drawing's
corner -- they stop against the flat inside face of the frame. The floor's
solver (the Triangle Infill calculator's floor base) cuts every piece to the
face it meets, and its answer is the length to mark:

```text
long piece, as cut   {{found.long_cut}} in   ({{found.long_minus_cut}} in shorter than its centreline)
short piece, as cut  {{found.short_cut}} in
one log, one of each  {{found.spare}} in left for the kerf and the trimming
```

So the drawing's lengths add up exactly, and the real ones leave a little
over: about {{found.spare}} inches of every log for two saw cuts, the ends
squared, and a mistake.

## The pinwheel at every crossing

Where two star pieces cross, one of them runs through and the other is cut to
sit against it -- the same rule the dome's panels follow, that nothing meets
at a corner. Go round the inner pentagon the same way every time and the
crossings make a pinwheel: each piece passes through one crossing and is
seated at the next. The solver works out every one of those seats, and the
3-D world (the next chapter) draws them.

:::box against "What the numbers do not settle"
The solver checks every span of the star for bending and sag, but its wood is
a guess: the logs are ungraded, so their strength is a stated assumption, not
a rating. A floor that people live on is checked by an engineer before anyone
moves in.
:::

## Laying it out

The pentagon is laid out on the ground before a log is moved: a stake at each
of the five corners, a stake at each of the five places where the star's lines
cross, and string between them. The strings are the jig. A log is right when
it lies along its string; a star piece is right when both its ends land on
stakes. The world in the next chapter has this layout as its own layer -- the
foundation's jig -- with every stake where the solver puts it.
