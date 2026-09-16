# 6. Why 65 edges need 120 pieces of wood

The dome's shared-edge mesh and its independent-panel frame count different things. If each mathematical edge owned one stick, the hemisphere would use sixty-five sticks. In this project, each of forty triangles owns all three of its wooden members. The frame therefore contains 40 × 3 = 120 members.

| Panel family | Panels | A members per panel | B members per panel | A total | B total |
| --- | --- | --- | --- | --- | --- |
| A-A-A | 10 | 3 | 0 | 30 | 0 |
| B-A-B | 30 | 1 | 2 | 30 | 60 |
| Total | 40 | — | — | 60 | 60 |

Two neighboring triangles bring two pieces of wood to their common boundary. The duplication is intentional. Each triangular unit can be made and checked before it joins the dome. The space between its member and the neighboring panel's member becomes the seam detail.

Of the sixty-five unique mesh edges, ten are at the exposed base rim and fifty-five lie between two panels. Count forty panels × three edges to get one hundred and twenty panel-edge incidences. Count the same incidences another way: fifty-five interior edges appear twice and ten boundary edges appear once. Thus 55 × 2 + 10 = 120.

There are thirty-five long edges and thirty short edges in the unique-edge mesh. Ten of the long edges are on the base. The shared seams are therefore twenty-five long and thirty short. Use the member count to plan wedge stock; use the seam count to plan panel interfaces. Hardware quantities require the selected detail at each interface and cannot be inferred by calling all edges “struts.”

This page should remain beside the cut schedule. When another calculator returns thirty-five long and thirty short, it may be correctly counting the conventional shared-edge dome. The disagreement can be a difference in construction system rather than an arithmetic mistake.
