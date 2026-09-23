# The seed dome — the stem cell, its modules, and what one costs

The brief, as stated by the owner, organised so the tools can be built from
it — and then the arithmetic that answers it. Nothing here is invented, and
nothing here is a number somebody typed: every figure below comes out of
`seed_model.py`, which derives it from the same solved geometry the Raw Wedge
Dome tool draws and the same supplier price list a boatyard buys from.

To regenerate every figure in this document:

```bash
py -3.12 seed_model.py
```

---

## The one-sentence version

Ship a customer a *stem-cell dome* — the bare standard article — and sell them
the modules, upgrades and fit-outs they build on top of it. The shop
manufactures one dome and a catalogue of parts, not nine buildings.

## Who pays for what

This is the most important line in the document, and most tiny-house pricing
gets it wrong by adding the two sides together.

| | the landowner | the dome buyer |
|---|---|---|
| builds | the pad: deck on blocks, barrier, service port, tank, under-floor storage, a share of a hub panel, the spur, the permits | the dome |
| pays | **$7,412**, once | **$30,477** |
| keeps it when the dome leaves | yes | the dome goes with them |
| maintains | ground and hookups | their own house |

That last row is the whole business case on the host's side: **passive income
with no building to maintain.** Nobody can wreck a house the landowner does
not own, and nobody is asking the landowner to renovate between tenants.

And it is why a dome can be sold for what a dome costs, rather than what a
dome plus a foundation plus a piece of land costs. Nobody is buying all three
at once.

Why anybody would take the other side of that trade — what a pad actually
returns, the five ways its utilities can be arranged and what each earns, and
the occupancy guarantee meant to get the first ones built — is argued in
[dome-park-brief.md](dome-park-brief.md#why-anyone-would-build-a-pad).

The dome's price has no floor, no deck and no groundwork in it. That is
deliberate: a buyer who moves should not buy a deck twice, and a host who
builds a pad should not be told hosting is free.

## What the stem cell is

One 2V hemisphere, built on a **six-foot longest member**, wedge-cut framing,
point-in.

| | |
|---|---|
| across | 19.42 ft |
| tall | 9.71 ft |
| floor, ten-sided | 276.99 sq ft |
| floor, full circle | 296.09 sq ft |
| panels | 40 — ten A-A-A at 15.588 sq ft, thirty B-A-B at 13.129 sq ft |
| panel area | 549.75 sq ft |
| geodesic struts | 35 A at 6 ft, 30 B at 5' 3-5/8" |
| physical members | 120, pinwheelled — 659 ft of stock, out of **1.5 trees** |
| trunk the wedges come off | **12 in** — see below |
| member section | 6 in deep, 4.59 in wide |
| interior seam | 309 ft, closed with compressible hose |

Those figures are checked against Zip Tie Domes' published 2V calculator run
at a six-foot "A" strut, figure by figure, in
`seed_model.validate_seed_model()`. They agree to four decimal places, because
both are the same icosahedron. The published page is the independent witness;
the solver is the source.

### What it ships with

* **no frame.** It is split out of the buyer's own standing timber on site —
  about one and a half trees. The shop ships the joining hardware and the
  seam hose, not the wood.
* **joining hardware sized for this dome and the next two sizes up**, so it
  is carried forward to a bigger frame rather than replaced
* forty **panel bays**: an inner panel onto the wedge's own lip, a 6 in
  cavity, an outer panel compression-fitted from outside
* a **removable shell in four slices**, each seam a moulded **S-lip** that
  interlocks and gaskets so the pieces behave like one skin when they are
  back together: sheet-cored, glassed inside and out, gelcoat on the weather
  face, snapped to the pad with over-centre wire-bail catches, and lifted by
  a ring laminated into its apex. Four slices fit a trailer -- though one of
  them is **427 lb**, which is four people or the crane, not two; eight slices
  halve that and double the seam to pay for. `seed_model.heaviest_piece()`
  holds that figure so no film can quietly round it down
* a **utility column** from the pad port to the apex and out through it
* a **seal cap** over that penetration
* one blank **utility panel** outside the footprint
* a **window cooling unit** sized to the computed load, a central light and a
  ceiling fan

Not in the standard article, and priced separately so a buyer can see them:
the seam duct and catchment, the quilted layers, the blown cavity fill, and
the metal stove dome.

## Why it is called a stem cell

A stem cell has not decided what it is yet, and neither has this frame. It is
**forty identical triangular openings**. It does not know or care what is in
one — a panel drops in and compression-fits against the wedge; lift it out and
the opening is back.

So the *function of the building is a set of panels*:

| fit-out | bays changed | price |
|---|---|---|
| Nursery | 15 | $38,877 |
| Gym | 20 | $40,716 |
| Studio | 18 | $40,857 |
| Guest house | 12 | $43,141 |
| Garage | 14 | $44,047 |
| Workshop | 18 | $46,173 |

Same frame, same pad, same core, same hardware. Mirrors and acoustic bays and
it is a gym. Skylights and louvres and it is a workshop. Take three base bays
out, put one wide opening across them, and it is a garage.

Nothing structural is touched to do any of that — which means this is not a
building that *has* a use. It is a building that has a use **at the moment**,
and can have a different one in an afternoon. A nursery becomes a study
becomes a guest room.

The panel catalogue is `seed_model.PANELS`: blank, window, opening window,
door, open-bay door, skylight, louvre, exhaust, solar bay, flue, acoustic,
mirror, serving hatch.

## The buildings a homestead wants second

Most people who would build one of these already have somewhere to live. What
they are short of is a *second* building — a gym that is not the spare
bedroom, a study with a door that shuts, somewhere for guests that is not the
sofa, a workshop, a garage. Those are the cheapest fit-outs in the catalogue
because they are mostly panels.

## The bay: what actually closes a triangle

A wedge is not a rectangle, and that turns out to be the useful part. Its
inward face stands proud of where the panel sits, so **every bay in this frame
has a 0.75 in lip already cut into it** — not machined in, left there by the
shape of a split log.

From the inside out:

1. **inner panel** — drops onto that lip
2. **the cavity** — 6 in deep, 275 cu ft across the dome, shipped empty
3. **outer panel** — drops into the same bay from outside, compression fit
4. **the shell** — lands on the *frame*, not on any of it

Nothing in that stack is screwed to anything. The shape of the member holds
it, which means any of it can come out again.

## The seam channel, and what it is for

Two flat sawn faces meeting at a dihedral angle do not close flush. Every
other way of building a dome treats that as a defect and machines it out.
Left alone it is a continuous channel running along every seam to every vertex
of the building:

| | |
|---|---|
| channels | 55 seams, **309 ft** |
| cross-section | 7.8 sq in |
| junctions | 26 vertices |
| volume of duct | 17 cu ft |
| cost to cap, fan and manifold | **$1,326** |

**Blow through it** and no part of a wooden frame sits in damp air — constant
airflow, the seams turned into something closer to an air-hockey table than a
joint. **Draw through it** and what lands on the shell goes down the channels
into the tank under the floor instead of looking for a way into a joint: off
550 sq ft of shell at 40 in of rain a year, **9,870 gallons**.

And it is meant to run **both ways**:

* **fan inside, blowing out** — positive pressure down the channels, so no
  part of a wooden frame ever sits in damp air
* **fan outside, drawing in** — suction pulls what lands on the shell down
  the channels and into the tank, so water gets in *on purpose*, by the route
  we chose, instead of finding its own

This is an experiment being run, not a result being reported, and it is
deliberately **not** in the standard article's price for that reason.

## It gets warmer every winter

The cavity ships empty on purpose. Because the shell comes off, insulation is
not decided once at a factory — lift it, lay in a quilted layer of recycled
fabric, put it back.

| layers | R-value | spent |
|---|---|---|
| 0 | R-1.5 | $0 |
| 1 | R-3.1 | $605 |
| 3 | R-6.3 | $1,814 |
| 5 | R-9.5 | $3,024 |
| 7 | R-12.7 | $4,233 |

Put on seven t-shirts and tell me how cold you are. It is the same argument,
and the fabric is a waste stream. A finished house does not get warmer every
winter; this one does, for as long as somebody owns it.

The R figures are `park_model`'s own quilt constants, borrowed rather than
restated, so this film and the dome-park film cannot disagree about a layer of
cloth.

## Two things that multiply

| | |
|---|---|
| dome envelope | 583 sq ft |
| box, same floor | 997 sq ft |
| so the shape alone | **41.5% less** to lose heat through |
| barium-sulphate radiative coat | surface runs **48 °F** cooler than dark |
| which takes off the cooling load | **15.1%** |
| the coat costs | $742 |
| **against a painted box** | **50% less** |

They *multiply* rather than add, because the second works on what the first
left. Which is why the whole design cooling load of a 277 sq ft house comes
out at 3,698 BTU/h — a window unit.

The paint physics is `two_v_demo/dome_performance.sky_cooling`, which models
it through sol-air temperature rather than by assuming the reflectance walks
straight into the building.

## Running it on nothing

Sized against this dome's own measured draw, not a guess:

| | |
|---|---|
| demand | **4.59 kWh a day** (its heating and cooling year, plus lights and fan) |
| 800 W of panel | 2.87 kWh a day at 4.6 sun hours — covers **63%** |
| 10 kWh bank | **2.2 days** with no sun; refills from empty in 3.5 days |
| panels, battery, 3 kW inverter | $760 + $4,100 + $630 = **$5,490** |

Two honest notes. Square cells waste the corners of a triangular bay;
triangular cells are the obvious fix and are not orderable yet. And the brief
asked for 3000 on the battery — at kilowatt hours that is **$1.23m** of cells
and two years of autonomy, so watt hours, or the inverter's rating, was almost
certainly what was meant.

## The interface boundary

This is the part of the design that everything else hangs off.

Power and water arrive in the middle of the pad. They come up through the
floor to a flange, up the inside of the utility column — where the shower,
the sink, the drain and the outlet ring are — and **they do not stop at the
ceiling.** They carry on through a sleeve at the apex and out.

The top of the dome is therefore not a roof. It is a socket. A gasketed
**seal cap** bolts down over it: meant to stay shut for years, meant to come
off in ten minutes. Under that cap, a line can be picked up and run down the
outside of the shell to a **utility panel** — a "polyp" — hanging off the rim,
mostly outside the footprint, reaching back in through a gasketed port.

The consequence: **adding a service never cuts a new hole in a weathertight
surface.** The exhaust fan, the tankless heater, the shower module, the
cooling unit all snap into a panel that was fed from a penetration that
already existed.

## The core is a thing, and it moves

The column, the manifold, the drain, the sub-panel, the light, the fan and the
cooling unit come to **$1,890** — about **15% of everything
material in the dome.**

It unbolts. Moving it is about $260; buying a second one is $1,890. So every
move is that difference, spent on a bigger shell instead of on the same
plumbing twice. That is what *modular* means here: not "our product has
options" — the physical object comes out and goes into the next dome.

## The frame, priced against a board you can go and buy

Every timber figure in this model is scaled off one shelf price.

| | |
|---|---|
| one 2x6x12 at Lowe's | **$14.00** |
| rips and crosscuts into | 4 struts of 2x3x6 — **$3.50 each** |
| 120 of those | **$420** — the whole frame in bought sticks |
| one wedge off a 12 in trunk | 1,018 cu in — **3.77 × a 2x3x6** |
| 120 wedges, bought as timber | **$2,465** |
| felled on site instead | **$692** (hardware and seam hose only) |

The trunk is 12 inches rather than the solver's own default of 8, and the
reason is a weight: the owner's wedges run three to four times the mass of a
2x3x6, and at 8 in a wedge is only 1.68 times one. Twelve gives 3.77. The
trunk is what sets that ratio and nothing else does, so that is where the
correction belongs — not in a fudge factor on the price.

### Why split at all

| one trunk, converted two ways | |
|---|---|
| split into wedges | **88.4%** of it — 391 bf |
| milled into 2x4s | **45.2%** of it — 200 bf |
| so a wedge takes | **1.95 ×** as much, +191 bf a tree |

Squaring a round log means throwing the round part away. We do not square it.
Both figures are `two_v_demo/wedge_geometry.py`'s, computed by packing the
same bucked sections both ways off one real tapered pine.

### The channel is a conduit

A wedge is a triangle in section, so two of them meeting at a seam leave a
channel. Not a gap to be filled — a continuous channel along **every seam** to
**every vertex**, that nobody had to route.

That channel carries the services: electrical, water, air. Which has a
consequence worth more than the conduit itself — **you always know where the
lines are.** They are in the corners of the seams and nowhere else. Every
person who ever works on this dome knows the one place not to put a drill.

## The shell is a boat hull

It is a wood-cored composite skin, which is not a novel thing to build. There
are a handful of laminate systems anybody in the trade actually uses, and
`hull_laminate.py` is those systems: named products, their real
specifications, and a composites supplier's published prices.

**Priced by weight, not by yardage.** That is the industry's own method. Glass
and resin sell by weight in bulk; a laminate is specified as ounces of glass
per square foot and a resin-to-glass ratio, and the resin quantity falls out
of the fabric. Pricing a laminate at so many ounces of resin per square foot
regardless of what is under it is right for one schedule and wrong for every
other one.

**Watch the units.** Woven and stitched fabrics sell by ounces per square
*yard*; chopped strand mat sells by ounces per square *foot*. So 1708 is 17
oz/sq yd of stitched biaxial plus 0.8 oz/sq ft of mat — 2.689 oz per square
foot, not 1.97. Getting that wrong understates a 1708 laminate by a third.

Over this dome's real area — 1,325 sq ft laminated, over a 660 sq ft core,
each carrying the S-lip seams of a four-slice shell:

| system | resin | schedule | cost | per sq ft | weight |
|---|---|---|---|---|---|
| Sheathed ply | epoxy | 6 oz cloth each side | **$5,395** | $4.07 | 1,222 lb |
| **Boatyard polyester** | GP polyester | 1.5 oz mat + 1708, 3/4 oz mat inside, gelcoat | **$6,045** | $4.56 | 1,708 lb |
| Premium marine polyester | marine polyester | same schedule | **$6,668** | $5.03 | 1,708 lb |
| Vinyl ester hull | vinyl ester | + 10 oz cloth | **$9,144** | $6.90 | 1,846 lb |

The boatyard schedule is what the standard article ships with: 236 lb of
glass, 515 lb of resin, 1.76 to 1 by weight, which is where hand layup lands.

Prices are US Composites' published list (August 2026), converted from their
per-linear-yard-at-50-inches pricing to square feet. Resin-to-glass ratios are
checked in `hull_laminate.validate_hull_laminate()` against two independently
published rules of thumb: about 30 oz of resin wets out one 50-inch yard of
1708, and one layer over ten square feet takes one and a half to two pounds.

### The sheet finding

**No panel of this dome fits a four-foot sheet.** A triangle cannot get
narrower than its shortest altitude however it is turned. The A-A-A panel's
is 62.35 in and the B-A-B panel's is 52.52 in, both wider than 48. So the core
is sheeted across the frame and the joints are taped — it cannot be cut panel
by panel out of 4×8 stock. `seed_model.shell_report()` prints this every time.

## What one costs

| | |
|---|---|
| wedge frame — oversized hardware and 309 ft of seam hose | $692 |
| forty panel bays, two panels each | $3,589 |
| removable shell, four slices, boatyard laminate | $6,045 |
| utility column and seal cap | $1,405 |
| window unit, light and ceiling fan | $485 |
| one utility panel | $491 |
| **materials** | **$12,707** |
| build labour, 126 hours | $3,531 |
| overhead and warranty | $3,572 |
| **cost to build** | **$19,810** |
| **list price at 35% margin** | **$30,477** |
| per square foot of floor | $110.03 |

**The floor.** Every real saving lever pulled at once, margin untouched:
**$21,706 list.** `seed_model.lever_report()` ranks each lever on its own and
marks the margin cut as *not* a saving.

**Upgrades, priced apart so a buyer can see them:** the seam duct and
catchment **$1,326**, seven quilted layers **$4,233**, a gym fit-out
**$40,716**, the home fit-out **$44,333**.

## The seeds

Six second buildings and five shapes, one cut list. A gym is twenty bays of
mirror and deadening; a garage is three base bays taken out for one wide
opening. A sauna is the same forty panels pulled in and stretched up; a
jacuzzi is the same forty turned over; a bunker is the same forty with soil
against them; a treehouse is the same forty on a saddle.
Nothing in the frame line of the quote changes between them, and that is the
manufacturing argument.

| seed | shape | what it adds |
|---|---|---|
| stem cell | hemisphere | nothing — this is the product |
| home | hemisphere | shower, sink, grey tank, cooktop, fridge, tankless heater, 360 camera ring on the seal cap, interior screen |
| food | hemisphere | serving hatch, prep counter, grease hood, three-bay sink, fridge, tankless heater, exhaust fan |
| advertiser | hemisphere | one lit advert face in each of the forty triangles, a controller, solar and battery |
| cold storage | hemisphere | roller shutter, six shelving bays, dehumidifier |
| bunker | buried | liner and drainage collar, powered ventilation up the apex riser, stair |
| treehouse | treed | tree saddle set, access stair, solar and battery, grey tank |
| sauna | tall | heater, two tiers of bench, exhaust fan |
| jacuzzi | inverted | tub liner, pump and heater, tankless heater, exhaust fan |

## The unflattering ones

**Bought as timber, the frame is $2,465.** That is not nothing, and the first
version of this model said it was — it priced logs by the cubic foot at a
figure that made the whole frame come to seventy-eight dollars. Pricing it
against a board you can walk in and buy fixed that.

**The pinwheel costs 80% more stock.** A zip-tie dome shares one strut
between two triangles: 65 struts, 369 ft. This dome gives every triangle its
own three sticks, which is what lets every cut be a plain angle: **120
members, 664 ft.**

Which sits awkwardly beside the harvest number two sections up, and the
honest thing is to put them together rather than quote whichever one helps.
1.80× the stock, against 1.95× more of the tree, is **92% of the trees a
mitred dome built out of milled lumber would take.** It wins. It wins by
8%, which is not a headline, and `seed_model.trees_against_mitred()` is
there so nobody has to take our word for the direction.

**The standard dome ships with an empty cavity.** Six hundred dollars and an
afternoon buys a layer, and you can keep doing that for years — but on day one
this is a weathertight shell, not a winter house, and somebody has to do that
work.

**The seam duct is not proven.** The channel is real and the arithmetic is
real; the airflow is an experiment. It is priced and it is out of the standard
article until it is proved.

**The cooling unit is a window unit.** Computed load on this envelope is
3,698 BTU/h, rounded up to the smallest machine sold. A square-foot rule of
thumb would have put a two-and-a-half-ton mini-split on a 277 sq ft floor.

---

## The campaign film

`two_v_demo/lesson_seed_pitch.py` — nineteen chapters, about nine minutes,
registered as the `seed_pitch` lesson and the
`deliverables/masterclass/stem-cell-dome-campaign.mp4` deliverable. Every
figure on screen is read out of this model at render time by
`two_v_demo/seed_facts.py`, and every dome on screen is the raw-wedge solver's
own building through `two_v_demo/seed_bridge.py`.

Three of its chapters argue against the pitch, on camera, with numbers.

```bash
py -3.12 -m two_v_demo.seed_facts      # every worksheet, printed
py -3.12 -m two_v_demo.lesson_seed_pitch
```

Render it from the launcher's Render tab: **stem-cell-dome-campaign.mp4**, or
**stem cell dome -- one still per chapter** to look at every shot first.

---

## Where it lives

| what | where |
|---|---|
| the geometry, the prices and the quote | `seed_model.py` |
| the hull laminate systems | `hull_laminate.py` |
| the dome, the column, the cap, the polyps, the crane, the road | `seed_world.py` |
| the clickable calculator | `seed_console.py` |
| the calculator inside the 3-D world | `geodesic_raw_wedge_dome_dihedral.py`, press **F3** |
| seeds standing on pads | `park_world.seed_park()`, shown by `dome_park.py` |
| the campaign film | `two_v_demo/lesson_seed_pitch.py` |

### Your prices

The PRICES page of the calculator lists all 96 inputs, their units and the
reason each holds its value. Click a row, type a number, press Enter. SAVE
writes them to `seed_prices.json`; LOAD reads them back; DEFAULTS restores.
EXPORT writes the current quote out as a spreadsheet, to a new file every time.

Twenty-nine of the inputs are **borrowed** rather than declared here — the
hull laminate table from `hull_laminate.py`, R-values and degree days from
`two_v_demo/dome_performance.py`, the sheet price from
`two_v_demo/dome_costing.py` — and marked as such on that page, so two parts
of this repository can never quietly disagree about what a gallon of resin
costs.
