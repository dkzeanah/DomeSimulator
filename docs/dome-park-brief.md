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

### Why anyone would build a pad

The dome side of this sells itself: a house you own, that you can take with
you, for the price of a car. The pad side is the half that has to be argued
for, and it is the half the whole network depends on — a dome with nowhere to
stand is a very expensive tent.

So here is the argument, and every figure in it comes out of `park_model.py`.

**It is the cheapest thing you can put on land that earns rent.** A
48 ft gravel pad with a power pedestal and a water connection costs
**$14,724** to build and returns
**$5,578 a year** net of management, tax and insurance. That is a
**2.6-year payback** — and the thing being paid back is a deck and two
connections, not a building somebody has to live in and somebody has to
maintain.

**The deck is the whole decision.** Same diameter, same lease, same tenant:

| deck | build | net a year | payback |
|---|---|---|---|
| gravel | $14,724 | $5,578 | **2.6 yr** |
| concrete | $26,486 | $5,578 | 4.7 yr |
| wood | $50,010 | $5,578 | 9.0 yr |

The revenue line does not move. A tenant pays for a level, serviced circle;
they do not pay more because it is concrete. Anyone who builds the timber deck
because it looks better in a photograph has turned a 2.6-year asset into a
9.0-year one and bought nothing with the difference.

**It is landlording with the building taken out.** Against a furnished short
let earning *the same revenue*:

| | pad host | furnished short let |
|---|---|---|
| up front | $55,846 | $73,846 |
| every year | **$920** | **$6,614** |

**7.2 times less to carry.** The
difference is not cleverness, it is ownership: the short-let host owns the
building the tenant lives in, so they pay for cleaning it, insuring it,
repairing what gets broken and renovating it when taste moves on. The pad host
owns a deck and two connections. A bad tenant costs them a lease, not a
renovation. When the tenant leaves, the pad is exactly what it was — because
the tenant took the house with them.

That is the sentence worth keeping: **the asset that depreciates drives
away.**

**It is reversible, which is the thing land usually is not.** A gravel pad
and a pedestal is not a foundation and not a building. If the network never
materialises, or the rules change, or the owner wants the field back, what has
to be undone is a deck and a trench. That is a materially different decision
from putting an ADU on the same ground, and it is why a pad is a reasonable
thing to try rather than a thing to commit to.

**It puts land to work that cannot be built on.** A parcel with a setback
problem, a failed perc test, a slope, or a zoning line that forbids a second
dwelling can very often still take a level circle with a hookup. Nobody builds
a house there because nobody can. This is the real unlock, and it is also
where the honest caveat lives — see below.

#### Who pays the power bill, and the five ways to arrange it

This is the part that sounds complicated and turns out not to matter much.
There are five arrangements. All figures are per month for one tenant at the
modelled draw of **$70.50** of power and water at cost:

| arrangement | host earns | tenant pays | extra build | share of host's gross | regulated |
|---|---|---|---|---|---|
| Submeter, rebill at cost plus a margin | $9.70 | $80.20 | $340 | 1.4% | **yes** |
| Submeter, rebill at cost, flat admin fee | $12.00 | $82.50 | $340 | 1.8% | no |
| Flat allowance bundled into the lease | $24.50 | $95.00 | — | 3.6% | no |
| Utility meters the pad and bills the tenant | $0.00 | $70.50 | — | 0.0% | no |
| The pad generates and the tenant draws from it | $0.00 | $70.50 | — | 0.0% | no |

Read the fourth column. **The best of the five earns $24.50 a month — 3.6% of
a host's gross.** Two of them earn nothing at all. The entire spread from best
to worst is $24.50 a month, which is less than a hundredth of what the pad
makes.

**Metering is not the business.** The lease is the business. That is a
liberating finding rather than a disappointing one, because it means a host
should choose their arrangement on paperwork and risk and never on return:

* **Marking up the commodity is the obvious one and the worst one.** It is the
  only regulated arrangement of the five — many US states and most utility
  tariffs restrict reselling power above cost, and some require a reseller
  registration — and it earns *less* than simply charging a flat fee for
  reading the meter. Check the tariff before promising a host this line of
  income.
* **The flat admin fee is the one to default to.** Same submeter ($340
  installed), but the host charges for the service of reading it and issuing a
  bill rather than selling power. That is the form most jurisdictions allow
  without a licence, and it happens to pay better.
* **The flat allowance is the tempting one and the only one that can lose
  money.** No meter, no bill, no regulator — it is rent. It earns the most of
  the five on an average tenant. On a heavy one, at 2.1× the modelled draw,
  the host is **$53.05 a month underwater.** The risk is real and it is
  bounded, because the thing on the pad is a 277 sq ft dome and not a house —
  but a host who bundles utilities should know they have taken a position, not
  charged a fee.
* **Letting the utility bill the tenant directly is the cleanest and earns
  nothing.** The obstacle is not money; it is whether the utility will open an
  account against a pad with a removable building on it. Many will not without
  a permanent address, and that is worth finding out locally before it is
  designed around.
* **Solar is an asset return, not a metering arrangement**, which is why it is
  priced separately. Its limit is already on camera: most of what a dome-sized
  array makes is surplus the tenant cannot use.

#### How dome buyers can be sure there will be pads

They cannot, yet. That is the honest answer, and pretending otherwise is how a
two-sided network talks itself into a launch it cannot supply. Nobody buys a
dome without somewhere to put it and nobody builds a pad without a dome to put
on it, and no amount of arguing resolves that from inside.

**So we break it from the pad side, by buying the risk.** A host who builds
one of the first pads gets a written occupancy guarantee: for
**12 months**, if the pad is empty, we pay the lease.

What that costs the writer, per pad:

| | |
|---|---|
| worst case — never rents, we pay the whole term | **$8,006** |
| expected, at the modelled 80% occupancy | **$1,601** |
| across fifty pads, expected | $80,058 |
| across fifty pads, worst case | **$400,288** |

That last figure is the one to look at before writing a single guarantee. It
is a real balance-sheet commitment and it is the number a campaign has to be
able to answer for.

And here is what the guarantee does **not** do, because it would be easy to
oversell: it barely moves the return. A gravel pad pays back in 2.6 years
without it and 2.4 years with it. The guarantee is not a yield enhancer. **It
converts "2.6 years if it rents" into "2.4 years, and the first one is
certain,"** and certainty is the entire product. A host is not being offered
more money. They are being offered a floor under the only risk in the deal.

The writer's side of that trade is not charity either. Every pad built is
demand for a dome, and the dome is the half with the margin in it.
Underwriting 12 months of one pad's lease costs about $1,601 in expectation —
against a dome that lists at five figures. It is customer acquisition priced
as insurance.

#### What has to be true, and is not yet

**Zoning is the hard part, not the pad.** Everything above assumes a
jurisdiction that will permit residential occupancy of a serviced pad. The
`permit_usd_per_pad` line in the model is a fee; it is not a probability, and
the model does not claim to price the risk that the answer is simply no. A
host in a permissive county has the deal described above. A host in a
restrictive one has a very well-drained gravel circle.

Anyone taking this to a campaign should find three jurisdictions that say yes
in writing before quoting a payback to anybody.

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
