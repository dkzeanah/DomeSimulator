---
title: Strut tables
kind: section
---

# Strut tables

Two strut lengths per dome, and the cut is not the chord.

      diameter     radius     A chord     B chord       A cut       B cut
    --------------------------------------------------------------------
         8.00'      4.00'     29.666"     26.234"     27.848"     25.244"
        10.00'      5.00'     37.082"     32.792"     35.264"     31.802"
        12.00'      6.00'     44.498"     39.350"     42.681"     38.361"
        14.00'      7.00'     51.915"     45.909"     50.097"     44.919"
        16.00'      8.00'     59.331"     52.467"     57.513"     51.478"
        18.00'      9.00'     66.748"     59.026"     64.930"     58.036"
        19.42'      9.71'     72.000"     63.670"     70.182"     62.681"  <- reference
        20.00'     10.00'     74.164"     65.584"     72.346"     64.594"
        22.00'     11.00'     81.580"     72.142"     79.763"     71.153"
        24.00'     12.00'     88.997"     78.701"     87.179"     77.711"
        26.00'     13.00'     96.413"     85.259"     94.596"     84.270"
        30.00'     15.00'    111.246"     98.376"    109.428"     97.386"

HOW TO READ IT

The CHORD is the straight-line distance between two vertices of the sphere.
It is the number every geodesic reference publishes and it is not the number
you cut.

The A chord is 0.618034 times the radius and the B chord
0.546533. Those two ratios are properties of a 2V icosahedron, they
are exact at every size, and everything else on this page is derived from
them.

The CUT is what a pinwheel member is, once the joint has taken its bite. One
end butts into the side of a neighbour, short of the corner; the other runs
past the mathematical vertex so the previous member can butt into its side.
Neither end lands on a vertex.

THE THING THAT CAUGHT THIS TABLE OUT

The bite does not scale with the dome.

It is set by how wide the member is, and a member does not get wider because
the dome does. Solve the same pinwheel at a 4-foot radius and at a 15-foot
one with the same stick and the bite comes out identical to four decimal
places.

So the cut is CHORD MINUS A CONSTANT, not chord times a ratio. An earlier
version of this table used a ratio -- correct at the reference build and
wrong at every other row, by more than eight inches at the small end.

If you take one thing from this chapter, take that. Scale the chord; subtract
the bite.

THE BITE USED HERE

    A members    1.818 in
    B members    0.990 in

Both at the reference build's 4.592-inch member. A wider
member takes a bigger bite, roughly in proportion, so a frame cut from
heavier stock wants its own solve rather than this table.

TWO MODELS, AND THEY DISAGREE

This repository solves the pinwheel twice.

The raw-wedge solver treats a member as a real 45-degree log
sector, and that is where the bites above come from. It is the live model,
it is what the simulator draws, and it is what the reference build is cut to.

A second, simpler model treats a member as a rectangular band lying with its
bark face on the edge line. It gives a bite of 9.253 inches for the
same stick -- five times larger.

Neither is a mistake. They are answers about differently shaped sticks, and
the difference is the shape of a split log versus a sawn board.

The numbers in this book are the first. If you are cutting rectangular stock
rather than log sectors, this table does not describe your frame, and the
difference is nine inches a stick.

THE ROW TO CHECK YOURSELF AGAINST

19.42 feet: A chord 72.000, A cut
70.182. If your own arithmetic gives that, the rest of
the table will behave.

<!-- NOTES
SECTION GOAL: Explain 'Strut tables' as it applies to 20. Builder's Reference.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Include the governing relationship or formula if it can be stated accurately.
- Include a worked reference-build example after the formula is verified.
- Record assumptions about sphere subdivision, truncation, and units.

Suggested development markers:
[FIGURE: Strut tables illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Strut tables]
-->
