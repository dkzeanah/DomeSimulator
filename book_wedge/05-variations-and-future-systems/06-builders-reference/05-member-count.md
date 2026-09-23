---
title: Member count
kind: section
---

# Member count

The counts do not change with diameter. They are properties of the
frequency.

    vertices      26
    faces, AAA      10
    faces, BAB      30
    faces, total      40
    geodesic edges      65
    members, A      60
    members, B      60
    members, total     120
    interior seams      55
    base edges      10

THE TWO NUMBERS THAT LOOK WRONG TOGETHER

There are 65 edges and 120 members.

In a shared-strut dome those would be the same number, because one stick
serves both triangles along an edge. In a pinwheel they are not: every
triangle carries its own three members, so the count is three times the face
count rather than the edge count.

That difference is the 1.80x stock penalty, and it is the price of never
cutting a stick to suit its neighbour.

THE SEAMS

55 interior seams and 10 base edges is
65 joints, which is fewer than the edge count
because the base ring's own edges are counted once.

Every interior seam is also a length of duct, 309
feet of it at the reference diameter, reaching every vertex. The count is
the same at any size; only the length scales.

<!-- NOTES
SECTION GOAL: Explain 'Member count' as it applies to 20. Builder's Reference.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Include the governing relationship or formula if it can be stated accurately.
- Include a worked reference-build example after the formula is verified.
- Record assumptions about sphere subdivision, truncation, and units.

Suggested development markers:
[FIGURE: Member count illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Member count]
-->
