---
chapter: 73
title: Build It in the Air
strand: howto
status: draft
target: 4260
updated: 2026-10-11
---

# 73. Build It in the Air

Most domes are built from the ground up: a ring, then a band, then the next
band, with a scaffold inside and somebody on a ladder holding a triangle
against two others while somebody else drives the fastener. This chapter
builds it the other way. A web of cable goes up between four living trees, and
every triangle of the dome is hauled up to it by a battery winch, swung out to
its own place, and left hanging there on three cords, touching nothing. Forty
of them. Then they are joined where they hang, their cords are gathered to one
point at the top, a skin goes over them, and the dome may simply stay up,
off the ground, held by the trees.

Chapter {{ch.floating}} hung a finished dome from a mast between two trees and
called it priced, not rated. This is a different idea and a more practical
one. The trees are not a novelty here; they are the structure. They are the
posts, the anchors, the shade and the drainage, and they were standing there
before anybody arrived with a saw.

![Forty triangles, each on its own three cords.](plate-sky-floating.png)

Every number in this chapter is worked out by `two_v_demo.sky_web`. It rests
on two tables. The first is what the owner weighed or owns, and it is
measured: struts of {{web.strut_lo}} to {{web.strut_hi}} kg, and a
{{web.winch_lb}} lb, 12 V winch. The second is everything a person assumed or
estimated, {{web.declared}} figures, each with a reason. Every load below uses
the heaviest strut.

    {{web.constants}}

Change any line, and every number after this one changes with it. Your trees
will not stand where these do.

> **Two corrections.** The first version of this chapter, and of the film it
> comes from, got two things wrong. It drew a hand winch; the winch is a 12 V
> battery winch rated {{web.winch_lb}} lb, {{web.winch_kn}} kN. And it weighed
> the frame with the solver's estimate, {{web.solver_strut}} kg a strut and
> {{web.solver_kg}} kg in all. The owner's struts, weighed, are
> {{web.strut_lo}} to {{web.strut_hi}} kg: {{web.ratio_lo}} to {{web.ratio_hi}}
> times as heavy. A triangle is three struts, so {{web.tri_lo}} to
> {{web.tri_hi}} kg, and the frame {{web.frame_lo}} to {{web.frame_hi}} kg,
> about {{web.frame_lb}} lb at the heavy end. Every load in the old version
> was too small by that much, and several of its conclusions moved.

## Four trees and an X

Four trees round the pad, near enough a square, {{web.square_m}} m a side.
Two wire ropes run corner to corner, so each spans the diagonal:
{{web.span_m}} m. They are tied {{web.tie1_m}} m up, on tree-saver straps,
never wrapped bare round the bark, because a rope that saws through the
cambium kills the tree that is holding your house up.

A rope with weight on it pulls sideways on its ends, and the flatter it
hangs, the harder it pulls. With real struts, that settles the design. Sagging
{{web.sag_pct}} percent of its span, {{web.sag_m}} m, with each triangle's
cords on the rope nearest them, the worse rope pulls {{web.t_kn}} kN:
**{{web.rope}}** wire rope, worked at a fifth of its breaking strength. Pull it
flatter, to {{web.taut_pct}} percent, and the pull doubles to
{{web.taut_kn}} kN and wants {{web.taut_rope}} rope. A deep sag is not a
choice. It is the design.

Then the trees, which take that pull {{web.tie1_m}} m up, as a lever. A
{{web.dbh_cm}} cm pine, green, breaks in bending at about {{web.mor}} MPa.
Unguyed, the design web works its trunk to a margin of {{web.tree1}}, where a
living tree, which can hide rot, should keep {{web.tree_want}}. The
{{web.taut_pct}} percent web works it to {{web.tree1_taut}}: past breaking. So
every anchor tree is guyed.

The guy goes where the owner put it: back and down to **the base of the next
tree out**, {{web.next_m}} m behind. Nothing to buy, nothing to dig, no
concrete. The guy pulls {{web.guy_kn}} kN, {{web.guy_rope}} rope, and it pulls
on that next tree at its root flare, where a tree is strongest and has no
lever at all. The trees round a clearing become a network, each one holding
the next.

![Guyed to the base of the next tree out.](plate-sky-guys.png)

## A tree is a better post

Guyed at the tie, an anchor tree stops being a lever and becomes a post:
squeezed from above by {{web.squeeze_kn}} kN, held at the top by its guy, and
fixed at the bottom by its own roots. A post fails by buckling, and a post's
resistance to buckling grows with the fourth power of its thickness.

Cut that tree, mill it, haul it to a yard, a store and back, and you have a
6x6 post. Stood {{web.tie1_m}} m tall it buckles at about {{web.post_kn}} kN.
The living trunk it came from buckles at about {{web.tree_mn}} MN:
{{web.tree_x}} times more, and it carries this web with {{web.buckle_x}}
times to spare. The tree was already the better post. It also comes with
roots, which no lumberyard sells.

![A milled 6x6 beside the trunk it would be sawn from.](plate-sky-treepost.png)

## One triangle, start to finish

The spiral goes on before any of this. It is woven out from the crossing and
seized to the X wherever it crosses, {{web.seizings}} seizings, and it covers
the dome's footprint, a circle {{web.footprint_m}} m across, but above it. Its
turns are {{web.pitch_cm}} cm apart: {{web.turns}} turns, {{web.spiral_m}} m
of line. The X carries the weight. The spiral gives a thrown cord somewhere to
land.

1. **Rig the winch.** A 12 V winch on one tree, run off a battery. Its line
   runs up the trunk to a block at the tie, along under the rope to a pulley
   at the crossing, and down to a hook. The heaviest triangle pulls
   {{web.pull_kn}} kN: the winch is {{web.winch_x}} times what it needs. A lift
   costs about {{web.one_wh}} Wh, so all forty take {{web.all_wh}} Wh, about
   {{web.battery_pct}} percent of what one 100 Ah battery should give.

2. **Harness it.** Three legs, one to each corner, meeting in an eye
   {{web.bridle_m}} m above the point the triangle balances on. Hooked by that
   eye, it rises flat. The dome has two shapes of triangle, so make two
   harnesses: legs of {{web.legs_a}} m for the one with two short sides, and
   {{web.legs_b}} m for the equal one. Label them.

3. **Hoist it flat.** Up to the crossing. The hook tops out at
   {{web.hook_m}} m, and a triangle takes about {{web.lift_min}} minutes. Flat
   matters: a triangle that tips on the way up catches the line, the X, and
   anyone underneath.

4. **Swing it out.** A tag line from the ground swings it from under the
   crossing to its own place, turning it as it goes from flat to the angle it
   will sit at in the finished dome. The hook stays on.

5. **Throw the pigtails.** Every triangle carries a cord tied at each
   corner. Thrown up over the spiral and tied back, the three of them hold it
   where it is. Each holds about {{web.pig_n}} N, on a cord {{web.pig_x}}
   times stronger. The pigtails run from {{web.pig_min_m}} to
   {{web.pig_max_m}} m: {{web.pigtails}} of them, {{web.cord_m}} m of cord.

6. **Slip the harness.** Only now. The hook goes back to the centre for the
   next one.

![Three pigtails over the spiral, then it slips the harness.](plate-sky-pigtails.png)

## Rim first, crown last, then join

The hook comes down at the centre, so the middle has to stay clear until the
end. Hang the rim first, then the band above it, and the crown last. The crown
is also where the hook runs out: with a metre of harness above them,
{{web.short}} crown triangles would need the hook higher than it can climb.
They are hung a little low, their pigtails go on, the harness comes off, and
they are hauled the last {{web.haul_cm}} cm on their own cords.

When the last one is up, the rim hangs {{web.rim_m}} m above the grass and the
crown at {{web.apex_m}} m, and nothing is holding anything else up. Joining
is easy from here: each triangle swings a little on its cords, so its
neighbour can be drawn up to it and the seam closed, a pair at a time, with
nothing to lift.

The seams need not be screwed. A dome works mostly in compression: its
triangles lean on one another, and a joint mainly has to stop them sliding
apart. Cord can do that. Lash each of the {{web.seams}} seams in
{{web.lash_per}} places, {{web.lash_wraps}} turns round both struts, and it
takes {{web.lashings}} lashings and about {{web.lash_m}} m of cord. Cord
stretches and creeps, so lashings want re-tightening, and they suit best a dome
whose shell -- fibreglass, say -- takes the pulling. Under a hard shell, the
lashings only hold the shape.

## Every cord to the apex

Once the dome is joined, the pigtails come off the web and are gathered to the
top, so the whole dome hangs from one point, and the shell can go over the
cords and leave them behind, with one line out through the cap. This is the
owner's idea, and it is a good one, with one thing to get right: **how the
cords run.**

Laid along the struts under the shell, a cord does not do what it seems to.
A cord pressed on a curved surface lifts nothing where it lies: whatever it
pulls up at its corner, it presses back down along its length. The corners
are squeezed, not lifted, and the whole weight arrives at the cap.

Run straight through the air *inside* the dome, from each joint to one free
ring just under the cap, the cords really do share the load. Each joint is
lifted by its own cord. The dome has {{web.joints}} joints: {{web.apex_cords}}
cords and the apex itself, which hangs straight from the line. The
{{web.strutted}} joints of the crown ring sit almost level with the ring, where
a cord would squeeze far more than it lifts, so they hang from the apex on
their own struts; the apex line carries {{web.apex_kn}} kN. The rim cords lean
in at {{web.rim_deg}} degrees and squeeze the rim ring with {{web.rim_hoop}}
kN, which a dome takes happily: being squeezed is what it is for.

![Cords from every joint to one free ring under the cap.](plate-sky-apex.png)

The price is in the room. Through the air means through the living space: a
rim cord passes, halfway to the wall, only {{web.head_m}} m above a floor laid
at the rim. That is fine while it is a frame in the trees. In a home, those
cords are lowered away once the dome is where it will stay, or it is hung by
its rim instead.

With every cord at one point, one winch can lift the whole dome evenly, up and
down. But that winch now carries everything: frame and skin,
{{web.hung_kg}} kg, {{web.hung_kn}} kN. Today's winch lifts
{{web.now_pct}} percent of it. The planned winch {{web.up_lo}} times bigger
lifts it with almost nothing to spare ({{web.lo_x}} times); {{web.up_hi}}
times bigger lifts it {{web.hi_x}} times over, and that is the one to buy.
Hang the winch itself at the crossing: pulled from a tree, its line turns at
the pulley and loads the X with {{web.block_kn}} kN instead of the dome's
weight. With every kilogram at the crossing the ropes pull {{web.one_kn}} kN,
still {{web.one_rope}}, with the guys at {{web.one_guy}} kN.

A dome can do this, and a house cannot, because its weight sits on its own
axis: hung from one point, it hangs level by itself. But only if its parts are
even. Placed at random, struts of {{web.strut_lo}} to {{web.strut_hi}} kg tip
it about {{web.tilt_med}} degree, and one time in twenty
{{web.tilt_95}} degrees, {{web.tilt_cm}} cm across the rim. Every heavy strut
on one side: {{web.tilt_worst}} degrees. **Weigh the struts and spread the
heavy ones round the dome.** Sorted, it hangs dead level.

## A silicone skin

Sailcloth would cover it, at about ${{web.sail_m2}} a square metre. The owner's
covering is cheaper and simple. Dissolve 100% silicone sealant in naphtha,
soak a cotton cloth in it, and let the naphtha evaporate. The silicone stays
behind in the fibres: a waterproof, chemically quiet skin.

Two layers over the dome's {{web.skin_m2}} m², with laps, take about
{{web.tubes}} cartridges of silicone, {{web.naphtha_l}} litres of naphtha
(at {{web.mix}} parts to one, an estimate) and {{web.cotton_m2}} m² of cotton:
about ${{web.skin_usd}}, against ${{web.sail_usd}} in sailcloth, and
{{web.skin_kg}} kg on the frame.

Silicone sticks to silicone, so layers stack into one monolithic skin: the
one watertight layer of Chapter {{ch.one_layer}}, made thicker. Almost nothing *else* sticks to
cured silicone, so decide what goes under it first. Cotton wicks wherever the
coat is broken, at cut edges and scuffs, so seal edges and inspect for wear.
And naphtha is very flammable, and its vapour is heavier than air: soak
outdoors, in the open, far from any flame or spark.

![The silicone-cotton skin, laid from the crown down.](plate-sky-skin.png)

## Building with the trees

Step back and look at what the trees are doing. They are the posts, stronger
than anything sawn from them. Their crowns shade the dome in summer. Their
roots draw water out of the ground round it: a mature pine perhaps
{{web.drink_l}} litres on a summer day, {{web.drink4_l}} for the four, an
estimate. Nothing touches the soil, so there is no foundation to pour, no damp
rising, no frost heave, and air moves under and round the building. The guys
tie to the next trees out, so even the anchors are trees.

A skinned dome catches wind, and a hanging one swings. Side on it shows
{{web.side_m2}} m². A {{web.gust_kmh}} km/h gust pushes it with about
{{web.gust_kn}} kN; it weighs {{web.hung_kn}}, so it swings
{{web.gust_deg}} degrees. A {{web.storm_kmh}} km/h storm, {{web.storm_kn}} kN,
{{web.storm_deg}} degrees. Its weight keeps it still and its round shape sheds
wind the same from every side, but tie it down to the trees on three sides
before a storm all the same.

A web also needs room to give, because trees move apart in the wind. The
design web goes taut once its trees lean apart {{web.tight_cm}} cm; a
{{web.taut_pct}} percent web after only {{web.tight_taut_cm}}. After that the
rope stretches, adding about {{web.kn_cm}} kN for every further centimetre. So
put a heavy spring or tensioner at every end of the X.

The trees ask some things back:

- **Lightning.** They are the tallest things on the hill, and now they carry
  steel rope to the dome. Bond the ropes together and ground them.
- **Growth.** Trunks thicken. Loosen tree-saver straps every year; never let
  one girdle the bark.
- **Deadwood.** Clean the crowns before anything hangs beneath them.
- **Rot.** It hides. Have an arborist look at all eight trees every season,
  and after every big storm.

## Higher, if the trees allow

A second web, higher up the same trees, is experimental. It depends on the
trees, and it has to be planned before they are chosen; the owner's are not
set up for it. Strung at {{web.tie2_m}} m, the same pull is half again the
lever: unguyed, the trunks would be worked to a margin of {{web.tree2}}, at
the edge of breaking, and the guys pull {{web.guy2_kn}} kN.

If the trees allow it, it goes like this. The first web is in the way: hung
from the second, the dome would have to pass {{web.clash_m}} m up through it.
So the dome is handed over first, on long cords from the second web, and the
first web comes out. Then it rises a corner at a time, {{web.step_cm}} cm a
pull, {{web.pulls}} pulls. The heaviest corner pulls {{web.corner_kn}} kN,
more than today's winch and well within the bigger one.

![The joined dome, raised a corner at a time.](plate-sky-corners.png)

## What it will and will not carry

> **The shell, yes. A floor full of life, on bigger rope.** The shell, frame
> and skin, hangs from this X on {{web.one_rope}} rope with the trees guyed.
> Add a floor and what a household puts on it, {{web.floor_t}} tonnes by the
> cell wall's own figure, and it is {{web.house_t}} tonnes pulling
> {{web.house_kn}} kN: {{web.house_rope}} rope, and every guy and tree
> checked again. It can be done. It is a structure an engineer and an arborist
> should sign, and it is priced here, not rated.

> **Never under the load.** Dropped from the top of the hoist,
> {{web.drop_m}} m, a {{web.tri_hi}} kg triangle lands at
> {{web.impact_kmh}} km/h with {{web.impact_kj}} kJ. Mark a ring under the
> hook and keep it empty. Wear a helmet. Climb on a proper climbing system,
> tied in twice, or hire an arborist for the ties. The web is only as safe as
> the worst knot in it.

For the record: two ropes for the X, {{web.spiral_m}} m of spiral,
{{web.guys_m}} m of guys to four more trees, {{web.cord_m}} m of pigtails,
one battery winch and, one day, a bigger one at the top. No scaffold, no
crane, no foundation. The ground can wait. Maybe for good.
