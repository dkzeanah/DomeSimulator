---
chapter: 74
title: The Frankendome
strand: story
status: draft
target: 1780
updated: 2026-10-05
---

# 74. The Frankendome

<!-- concept: franken/stock -->
<!-- concept: build/franken_stock -->

Chapter {{ch.ugly}} told you why I built the ugly one. This is how.

It was an experiment, not a recommendation, and the question was simple: how
fast does a dome go up if you stop caring what the struts are? Not cheaper
struts. Not rougher struts. Struts with no specification at all beyond being
roughly the right length.

So the frame is whatever the chainsaw made. Round logs still in the bark.
Quarter-sawn pieces off a milling jig. Wedges that were offcuts of something
else. Square stock, rectangular stock, whatever came off the pile that day.
They are not interchangeable in any engineering sense: every one of those
sections has its centreline in a different place, so no two joints in the
whole dome are the same joint.

## A bracket out of a washing machine

<!-- concept: franken/bracket_flat -->
<!-- concept: franken/bracket_bend -->
<!-- concept: franken/bracket_fitted -->
<!-- concept: franken/triangle -->

The joints are the interesting part. Every one is a bracket I made, and every
bracket started as a flat band sheared out of a scrapped washing machine. That
casing is galvanised sheet in a gauge that is genuinely structural at this
size, it is free, it is already flat, and there is a great deal of it in the
world. Shear a band, drill the holes, and that is the whole component.

Then one fold, straight down the middle, and the band becomes a V. No welding,
no castings, no bought connectors -- and because you bend it yourself, the
fold is simply whatever that particular corner turned out to be, which on a
frame like this is never the angle on the drawing. **The bracket adapts to the
joint instead of the joint having to match the bracket.** That is the trick,
and it is why the method tolerates such rough stock.

![One fold makes it a joint.](plate-washing-machine.png)

In place, the V straddles the corner, one leg down each strut, four screws
through each leg: {{fk.screws_per_bracket}} screws a bracket. Four in shear
along a leg is a genuinely stiff connection, and it fails gradually and
visibly rather than suddenly, which for a structure you are experimenting
with is exactly the behaviour you want.

The unit of work is one triangle: three sticks, three brackets, built flat on
the ground. No ladder, nothing held overhead. {{fk.triangles}} of those and the
dome is a pile of finished triangles waiting to be stood up.

## Hubless, so nothing has to be accurate

<!-- concept: franken/hubless -->
<!-- concept: franken/doubling -->
<!-- concept: franken/stockpile -->

What makes it buildable by one person with no jig is that it is hubless. Every
triangle carries its own three sticks, so the frame is {{fk.struts}} struts
rather than the {{fk.hubbed_struts}} a hubbed dome needs: {{fk.doubled}}
edges with two sticks lying against each other, and {{fk.rim}} rim edges with
one. Open a joint and you can see it: two triangles meet along an edge and
each arrives with its own complete stick, so the joint is a lap between two
members rather than a point where several converge. **Nothing has to meet
accurately at a point, because nothing meets at a point at all.**

And because nothing has to be accurate, the sticks do not have to match. In
the film every strut is coloured by the section it was cut to -- full round,
half, quarter, eighth, milled square, and salvaged steel only where wood would
not serve -- and the whole frame came out of the one woodpile.

![Six sections, one woodpile.](plate-woodpile.png)

## Nothing lands where it should

<!-- concept: franken/slack -->
<!-- concept: franken/settle -->
<!-- concept: franken/skin -->

Here is the honest picture. In the film, green points are where the geometry
says every hub belongs and red lines are where the sticks actually put them.
Not one joint lands on the sphere. Some are out by a quarter of an inch, some
by more, and every error is a different error because every stick is a
different stick.

![Green is the geometry. Red is where the stick put it.](plate-slack.png)

Then pull it together and stand it up, and the frame **settles**. Every
triangle is individually rigid, so a joint that wants to sit proud is held by
the two around it, and the error is shared out across the whole shell instead
of piling up round a ring the way it does in a precise dome. That redundancy
is not a nice property here. It is the only reason the thing stands at all --
and it is the lumpy skull of Chapter {{ch.lumpy}}, built.

What is left is a lumpy brain of a frame, near the sphere without being on it.
The sheathing finishes the job: a skin bonded over the outside bridges every
remaining gap and gives back the shell action the sloppiness cost. Once it is
on, the structure behaves far more like the skin than like the frame -- which
is the whole reason the frame is allowed to be this bad.

## The ledger

<!-- concept: franken/trees -->
<!-- concept: build/franken_trees -->
<!-- concept: franken/ledger -->
<!-- concept: build/franken_ledger -->
<!-- concept: master/ms_math_franken -->
<!-- concept: franken/floor -->

It went up between four trees, and that was not an accident. Cable overhead,
tied back into the trunks, meant the frame never had to support itself while
it was going together, and the trees kept taking a share afterwards. Covered
in clear plastic, it stood through **{{fk.months}} months** of weather before
I took it down on purpose -- {{fk.times_build}} times its own build time, which
is the only durability number I have.

    triangles                      {{fk.triangles}}
    brackets, folded from scrap    {{fk.brackets}}
    screws                         {{fk.screws}}
    days                           {{fk.days}}
    triangles a day                {{fk.per_day}}
    screws a day                   {{fk.screws_day}}
    months standing                {{fk.months}}

It stood on a round deck the same diameter as the dome, built and levelled
first, on blocks so air moves underneath: {{fk.deck_sqft}} square feet,
{{fk.joists}} joists and {{fk.joist_ft}} feet of joist, on {{fk.blocks}}
blocks. Get the deck round and level and the dome has something honest to land
on; get it wrong and every triangle above it inherits the error.

<!-- concept: franken/bolts -->

:::box correction
**This dome was screwed together. It was not bolted.** If you build one to
keep, put two bolts with nuts and washers through every edge as well --
{{fk.bolts}} bolts and {{fk.washers}} washers on top of the screws. It is the
single best place to spend money on this structure, because bolts come out
again and go into the next and better dome, so heavy hardware bought once is
never obsolete. But it is not what held this one up, and saying otherwise
would be inventing a structure I did not build.
:::

<!-- concept: franken/glass -->
<!-- concept: franken/cost -->

So what does one really cost? Everything structural was free. The cost is the
skin: {{fk.shell_sqft}} square feet of shell, {{fk.under_sqft}} under the
floor and {{fk.tower_sqft}} for the utility tower -- about
{{fk.laminate_sqft}} square feet to laminate, which at two layers and some
waste is {{fk.resin_gal}} gallons of resin and {{fk.cloth_sqyd}} square yards
each of cloth and mat.

    timber, cut down myself               $0
    brackets, from a washing machine      $0
    screws                                ${{fk.screw_usd}}
    fibreglass                            ${{fk.glass_usd}}
    the structure                         ${{fk.total_usd}}
    per square foot of floor              ${{fk.per_sqft}}

Almost all of it is the one material I could not make myself.

![The bill.](plate-franken-bill.png)

## Few processes, endlessly repeated

<!-- concept: franken/flatrate -->
<!-- concept: franken/optimise -->

The argument that makes this a business rather than a hobby falls out of the
ledger. A {{tt_flat.small_ft}}-foot dome and a {{tt_flat.large_ft}}-foot
dome are the same {{fk.triangles}} triangles, the same {{fk.struts}} struts,
the same {{fk.brackets}} brackets and the same {{fk.screws}} screws, through
the same {{tt_flat.processes}} operations. Only the sticks get longer, and
they grow with the diameter while the floor grows with its square.

A conventional house is thousands of dissimilar operations, so improving any
one barely moves the total. A dome is a few operations repeated over and over,
so shaving seconds off one cut saves minutes on every dome you will ever build.
That is what makes a factory worth building around this shape rather than
around a rectangle.

## What it trades, and what comes after it

<!-- concept: franken/trade -->
<!-- concept: seed_pitch/next -->

You give up precision, and with it any claim to a calculated structure. You get
back an enormous amount of speed, a material cost near zero, and a method that
tolerates stock nobody else would use. For a storage building, a workshop or a
shelter, where the covering matters more than the tolerance, I think that is a
completely valid way to build. For anything inspected, lived in full time, or
carrying snow you have not calculated for, it is not. Both things are true at
once.

And the member after the split log is not another split log. It is a member
that arrives with its screw holes, its threaded inserts and its gasket ridge
already moulded in, a steel core where the strength has to be -- so the
hardware that joins two of them is a standard, reusable part that comes off
with a driver, and its load rating comes off a test rig rather than an
argument. It does not exist yet. Chapter {{ch.article}}'s goal is mostly for
that, and what breaks will be published.

![The member we want to make instead.](plate-moulded-member.png)
