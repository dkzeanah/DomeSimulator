# Dome Park — the brief

The idea, as stated by the owner, organised so the tool and the film can be
built from it. Nothing here is invented: this is the argument to be made, with
the claims separated from the things that still need numbers.

---

## The one-sentence version

An RV park for domes: landowners build serviced pads, dome owners bring their
own home and plug in. Longer than a hotel, more substantial than an Airbnb,
and neither side is trapped.

## The two people in the network

**The pad host** owns land and builds pads. They collect a lease plus a small
margin on metered power and water. They never furnish anything, never
renovate, and never repair what a tenant broke — because the tenant's home is
the tenant's own.

**The dome owner** brings the house. They are not paying rent on something
that will never be theirs, they can modify their own home freely, and when
they leave they take the asset with them.

## Who it is for

* The nomad, and the person who travels for work.
* Someone who wants to try living in a new city without a lease.
* Someone who needs a change of scenery and would rather move the house than
  buy a new one.
* Anyone facing the premium that short stays currently carry.

## The argument against the current options

| | hotel / motel | Airbnb | conventional rental | **dome pad** |
|---|---|---|---|---|
| length of stay | nights | days to weeks | a year, by contract | weeks to years, no contract |
| who owns the building | operator | host | landlord | **the occupant** |
| who pays when it is damaged | operator | host | landlord, then deposit fight | **nobody — it is your own home** |
| can you modify it | no | no | no | **yes, freely** |
| does your spending build equity | no | no | no | **yes, in your own dome** |
| host's capital at risk | the whole building | the whole furnished home | the whole home | **a deck and two hookups** |

### The host's side, specifically

The costs an Airbnb or rental host carries that a pad host simply does not:

* furnishing, and re-furnishing after wear
* damage by tenants to a structure the host owns
* turnover cleaning and the labour to manage it
* renovation cycles driven by tenant taste and tenant damage
* insurance on a full structure and its contents
* vacancy on an asset with high fixed cost

A pad host's exposure is a deck, a power pedestal and a water connection.
A bad tenant costs them a lease, not a renovation.

### The dome owner's side, specifically

* Money spent improves an asset they keep.
* Improvements follow them to the next pad.
* Because it is theirs, they look after it — the incentive runs the right way.
* Competition between pad hosts gives real choice on price and location,
  rather than being captive to one landlord.

## What a pad actually is

A pad is the foundation and the services:

* a circular deck, concrete pad, or a wooden "acceptor" that latches to the
  side or bottom of an existing dome — **the pad provides the floor**
* electrical running centrally up into the dome
* water in, and drain out, through the same centre
* metering, so the host resells power and water with a small margin
  (order of a cent or two per unit) for handling the clerical side

### Optional, per host

* a built-in fridge
* a utility column: toilet, sink, showerhead, outlets, drain
* a shared bathhouse or shower house on site, so a dome owner need not carry
  plumbing at all
* **a rotating base** — the pad turns, so a dome wearing exterior solar can
  track the sun, and the yield comes off that tenant's utility bill

## The dome the system assumes

* modular, interchangeable panels
* a robust skeleton that does several jobs at once
* mounts to rotational or mechanical foundations, and can hang from cable or
  trees
* a lifetime, upgradable investment: expanded and improved bit by bit
* **one hardware set** carried across sizes — the same expensive, durable set
  serves a cheap dome, a mid dome, or a large one. You pay for the part that
  survives every iteration
* removable shells, so layers can be added over time — put the shell back on
  over the new layer

### The insulation argument, from the owner's own experience

Standing lookout outside the skin of a ship in the Arctic circle, the only way
to stay warm was layers on layers, then a wind-breaking, water-tight
"pumpkin suit" over all of it.

A dome can work the same way. R-value does not have to be a number fixed at
construction time. Add a quilted layer — including quilted recycled fabric,
which is a massive waste stream — put the shell back over it, and the house is
warmer than it was last winter. Seven quilted layers is not a rudimentary
thing.

## Why Kickstarter

The claim: a large, diverse network of these two kinds of people, and the
working relationship between them, is bigger than Airbnb — because it removes
the part of Airbnb that hurts, which is one party owning a building the other
party lives in.

---

## What this brief owed, and where each debt was paid

Nothing went in the film until it was computed or declared. Every row below
now resolves to a function; the "kind" column says whether it is **measured**
off the project's own geometry or **declared** in
`park_model.EXTERNAL_CONSTANTS`, where it is printed with a unit and a reason
and can be replaced without touching a script.

| claim | kind | where |
|---|---|---|
| how many domes fit a pad size | measured | `pad_sizes`, `domes_that_fit` |
| what a pad costs to build | both | `Pad.cost_rows` |
| what a host earns | both | `Pad.year` |
| how long a pad takes to pay back | derived | `Pad.year()["payback_years"]` |
| what a host loses to damage and turnover | declared | `host_comparison` |
| solar yield on a tracking dome | both | `Pad.solar_kwh_per_month` |
| what the layered shell does to R-value | both | `shell_ladder` |
| the cost of a short stay today | **declared** | `housing_options` |
| what the ground under a dome costs | measured | `foundation_share` |
| one hardware set across sizes | measured | `hardware_invariance` |
| how long a stay has to be | derived | `crossover_months` |

The film's worksheets are `two_v_demo/park_facts.py`, its pictures are
`two_v_demo/lesson_dome_park.py`, and `park_report()` prints the whole audit
without rendering anything.

### The one that is still only an assumption

**The cost of a short stay today** is the comparison the pitch leans hardest
on, and it is the one row above that is declared rather than sourced. The
hotel rate, the short-let rate and the apartment rent in
`EXTERNAL_CONSTANTS` are working figures for a middling US market, not
research, and they move the crossover month directly. Anyone taking this to a
campaign should replace those three with local, cited numbers first. The film
says on camera that they were typed in by a person.

### Three things the film says against itself

Kept because a pitch that only shows its good numbers is not a pitch.

* **On up-front cost, the short let wins.** A loaded pad costs more to build
  than a bare pad plus furnishing a rental on it. The pad host's case is the
  yearly bill, not the first cheque.
* **Below the crossover, this idea is the wrong answer.** For a stay of a
  month or two, a hotel or a short let is cheaper and the film says so.
* **Most of a dome's solar is surplus.** A shell carries several times the
  panel its household uses, and the model values the surplus at export rather
  than retail. Correcting that took the loaded pad's solar income down by more
  than half and its payback from 4.3 years to 5.2.

### Also true, and worth keeping in view

The flagship design used for every tenant figure — the Split-Log Homestead —
sits on a gravel pad, so it has the *smallest* foundation saving of any design
that has a foundation at all: $1,466 of $18,067. It was chosen for that
reason. The chapter that photographs the foundation argument uses the Timber
Workshop, whose concrete slab is 45% of its build cost, and the worksheet
names both.
