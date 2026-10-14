**What you are deciding:** whether the trees you have can make a frame, and how
many of them it takes.

## The reference answer

Volume B works its plan from one measured tree: {{tt_tree.butt_diameter_in}}
inches across at the butt, {{tt_tree.top_diameter_in}} inches at the top of the
straight part, and {{tt_tree.usable_length_ft}} feet of usable trunk between.

From those three numbers, everything follows:

* the trunk is cut into sections of {{tt_tree.section_length_ft}} feet -- the
  longest piece one person can carry and set alone -- which makes
  {{tt_tree.sections}} sections;
* each section is ripped into {{cut.splits}} wedges, so one tree gives
  {{tt_tree.struts_per_tree}} struts;
* the frame needs {{dome.members}} members, so it consumes
  {{tt_dome.trees_strictly_needed}} trees -- and the plan fells
  {{tt_dome.trees}}, because a pile always has rejects: a wedge with a crack
  down its point, a knot at its bearing end, a bow too deep to straighten.

The same tree holds {{tt_tree.solid_bf}} board feet of solid wood; split, it
keeps {{tt_tree.wedge_bf}} of them as members -- {{tt_tree.recovery_pct}} per
cent -- and loses {{tt_tree.kerf_bf}} board feet to the saw's cut.

## Thin trees and bent trees

A tree is not ruled out by being bent. A bend costs you the section it falls in,
not the tree: cut either side of it, burn the kink, and keep going. That is the
great advantage of short pieces.

A tree *is* ruled out by being too thin. The wedge has to carry as much wood as
the board it replaces. Volume B's strut has {{tt_log.member_area}} square inches
of section against a dressed two-by-four's {{tt_board.dressed_in2}}; a much
thinner tree would make sticks that lose that comparison, and then the honest
answer is to buy boards.

:::box do "Worksheet 1: my trees"
| | Tree 1 | Tree 2 | Tree 3 |
|---|---|---|---|
| Butt diameter (in) | [[blank]] | [[blank]] | [[blank]] |
| Top diameter (in) | [[blank]] | [[blank]] | [[blank]] |
| Straight length (ft) | [[blank]] | [[blank]] | [[blank]] |
| Sections (length ÷ section, rounded down) | [[blank]] | [[blank]] | [[blank]] |
| Struts (sections × {{cut.splits}}) | [[blank]] | [[blank]] | [[blank]] |

**Struts I have, all trees together:** [[blank]] · **Struts the frame needs, with
spares:** [[blank]] · **Measured by:** [[blank]] **on:** [[blank]]
:::

:::box why "Why"
The diameter at the middle of the trunk sets how wide the sticks are, and stick
width is the one thing that changes the cut list for a given dome (chapter five).
The length sets how many sections, and the section length sets the dome's size
(chapter four). Nothing else about the tree enters the arithmetic -- which is why
the method can use storm-fallen and low-grade trees a mill would never pay for.
:::

:::box watch "Watch out"
Measure only the straight run: the flared butt and the crown above the first big
branch are firewood. Use the middle diameter, not the butt, when you size sticks;
the butt flatters you. And plan spares -- a pile with no rejects allowed is a
plan that assumes every stick is perfect, and no pile is.
:::
