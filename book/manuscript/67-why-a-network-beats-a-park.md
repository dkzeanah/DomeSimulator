---
chapter: 67
title: Why a Network Beats a Park
strand: explain
status: drafting
target: 1940
updated: 2026-09-17
---
# 67. Why a Network Beats a Park

*A park is pads you rent. A network is pads that hold their value because a dome can leave one and arrive at another, and that difference is the whole resale argument*

## Why a Network Beats a Park

Nobody building their first dome asks the question this chapter is about.
Everybody building their second one does.

What is it worth when you want out?

A park answers: whatever the pad's owner will pay to see it gone, which is
whatever you will accept, which on the day you are moving is less than it
cost. A dome that can only sit on the one pad it stands on is worth exactly
what that pad's owner says it is worth, and the pad's owner is the only
buyer in the room.

A network answers differently. If a dome can leave one pad and arrive at any
other pad like it, then a used dome is not scrap tied to a postcode -- it is
a home that happens to be somewhere else this season. The buyer is not one
landlord. The buyer is the network, and the network has a price: the cost of
a new one, minus a haircut, computed here rather than waved away.

That difference is the whole resale argument, and this chapter prices both
sides of it.

## The line, and what runs along it

Power, water, waste and data reach a pad along a line, and the line is the
only economy of scale the site has.

The site's services are not six separate connections to the road. They are
one hub panel and manifold -- {{net.hub_panel}} dollars of hardware -- with a
short spur of {{net.spur}} dollars to each pad. A lone pad carries the whole
hub: {{net.hub_panel}} dollars of it. Four pads -- the cluster the site is
planned around -- split it: {{net.hub_share}} dollars each, plus the spur.

That is the entire economy of scale in the park model, and it is worth being
precise about its size because it is not a big number. The hub, shared four
ways, saves {{net.hub_panel}} minus {{net.hub_share}} dollars per pad beyond
the first three -- a real saving, and nothing like the claim a careless
pitch would make. The trunk road and service drop -- {{net.infra}} dollars a
pad -- are amortised flat, however many pads the site has. The deck is priced
by area. The permit is per pad. Nothing else on the site gets cheaper with
scale, because the whole point of the earlier chapters is that the dome side
does not scale that way either.

The line matters for a second reason that is not money. What runs along the
line is what makes a pad *serviced*, and a serviced pad is the product. A
circle of gravel is a campsite. Gravel plus the hub is a pad, and the pad is
the thing with a price -- {{pad.lease_mo}} dollars a month, which is the
number the next section hangs on.

## Host and tenant, both sides of the ledger

The idea only works if both sides of it make money, so price both.

**The host's side.** The host builds a pad -- {{net.host_pad_upfront}}
dollars for the loaded version -- and rents it. Against that, the same money
furnishing a short-let home: {{net.host_let_upfront}} dollars up front, and
{{net.host_let_yearly}} dollars a year of cleaning, damage reserve, platform
fees and renovation. The pad's yearly bill is {{net.host_pad_yearly}} dollars
-- management, tax and insurance -- because the building on it belongs to
the tenant, and its wear is not the host's problem. The host's building
cannot be trashed by a guest. The pad does not need cleaning between
tenants. That is the host's whole pitch, and the ledger bears it out.

**The tenant's side.** Four ways to have a roof, all priced with power and
water included: a hotel at {{net.hotel_mo}} dollars a month, a short let at
{{net.short_mo}}, a leased apartment at {{net.apartment_mo}} plus
{{net.apartment_entry}} dollars to move in, and the dome on a pad at
{{net.dome_mo}} dollars a month plus {{net.dome_entry}} dollars to arrive --
of which {{net.dome_asset}} dollars is the dome, which you keep.

The crossover is the number that decides who this is for, and the model
finds it rather than asserts it: month {{net.crossover}}. Stay shorter than
that and the honest answer is a hotel. Stay longer and the dome is the
cheapest roof in the table, and it keeps getting cheaper with every month
after, because the only thing you cannot take when you leave is the lease.

Two details in that table deserve their own line, because they are where the
comparison could quietly cheat and refuses to. The utilities are the same
for everyone -- the dome's {{net.utilities}} dollars a month is the
tenant's power and water at {{net.utilities_raw}} dollars plus a small
declared margin for metering, not a made-up number -- and the apartment's
lease is priced honestly, too: sign for {{net.lease_months}} months and
leaving early costs {{net.break_fee}} dollars, while {{net.deposit}} dollars
of the entry comes back. The dome's entry has no break fee because it has no
lease -- that is the whole point of owning the roof -- and its month is the
only one in the table that buys an asset instead of renting one.

The host's side has its own crossover, and it is slower. The loaded pad
costs {{net.host_pad_upfront}} dollars and nets its host a year like the
previous chapter's -- repaid in {{pad.standard_payback}} years, not months.
Hosting is a patient business. The point of the ledger is not that the pad
prints money. It is that the pad's yearly bill -- {{net.host_pad_yearly}}
dollars -- is the *only* bill, because the tenant's building wears itself
out on the tenant's side of the lease. The furnished let's
{{net.host_let_yearly}} dollar year is the price of owning the furniture,
the carpet and the reputation. The pad host owns a circle of gravel and a
meter. That is the trade the numbers describe.

The host's ledger has one risk the table hides, and it is the mirror of the
tenant's. The pad pays for itself in {{pad.standard_payback}} years -- if it is
rented. An empty pad earns nothing, and unlike an empty apartment it cannot be
let to a tourist for a weekend while it waits, because the product is the
serviced ground, and the ground waits for a dome that has not arrived. So the
host's real exposure is not the build; it is the empty months between tenants,
and the honest host prices the pad against a year with some of them empty, not
a year that is full. The furnished let fills those months with strangers. The
pad fills them with nothing, and the nothing is the price of not owning the
furniture.

## Resale, with the haircut left in

Now the question the chapter opened with, computed.

A maintained dome is declared to last {{net.life_yr}} years and never to
fall below {{net.residual_pct}} per cent of its cost. But the day it becomes
secondhand, it loses {{net.haircut_pct}} per cent -- the declared resale
haircut, the thing a real network would shrink and this chapter refuses to
pretend away.

So a dome that cost {{net.dome_asset}} dollars is worth
{{net.recovered_12}} dollars the day you leave after a year, and
{{net.recovered_60}} dollars after five. Walk away from a park and that is
the *best* case -- a buyer who exists. A dome that can only sit on one pad
has no such number, because its value is whatever the pad's owner offers,
and the pad's owner knows you have to leave.

That is the whole difference between a park and a network, in one sentence:
a park rents pads; a network makes pads *hold their value*, because every
pad in the network is a buyer for every dome on it. The network does not
make the dome free to own. It makes it possible to leave with something --
{{net.recovered_60}} dollars after five years, by this arithmetic -- instead
of with whatever the landlord felt like paying. And the recovery penalty
that would be waved away in a pitch is printed, at {{net.haircut_pct}} per
cent, on the line.

Why the haircut, and why not hide it? Because the day a dome is secondhand,
a buyer takes a real risk -- a frame assembled by a stranger, on hardware
that may have been torqued by feel -- and the market prices that risk as a
discount. A pitch that pretended used domes sold at new-dome prices would be
the same lie as the park's. The honest pitch is better anyway: the haircut
is {{net.haircut_pct}} per cent *today*, when every used dome is a gamble
with no track record. A network that has seen a hundred domes move between
pads, with the transport damage and the wear patterns known, could price
that risk down -- and that is precisely the thing a network is for. The
park's resale number is whatever the landlord says. The network's is
{{net.recovered_60}} dollars and falling toward honest, because the network
is the buyer that learns.

A network of one hub is still a park, whatever it calls itself. The buyer in
the resale section only exists when there are enough hubs -- each serving
{{net.hub_pads}} pads -- that a dome leaving one pad has somewhere real to
arrive, and enough history that the arrival is priced from data instead of
from fear. That is why the haircut is the number to watch: it is not a fee, it
is a temperature. A {{net.haircut_pct}} per cent haircut is the market saying
"unproven." Every move between two real pads, every insurer that writes a
policy, every standard the pads are built to, nudges that number down, and the
day it settles is the day the network stops being a proposal and becomes the
park's competitor.

## This is the least-built idea in the book

Be honest about what this chapter is, because the rest of the book has been
honest about everything else.

The frame is built. This book's dome is standing, and the fortnight and the
hours are measured. The pad is costed -- declared prices, named as such, but
arithmetic against a real catalogue. The network is neither. It is
arithmetic and one film, and it should be read as a proposal rather than a
report.

No network of dome pads exists for these numbers to have come from. The
resale haircut is declared, the crossover is computed, the host's year is a
model. That does not make the chapter worthless -- a proposal with its
assumptions on the line is how honest ideas are made -- but it makes it
*conditional*, and the closing chapter of this part is exactly that
condition, written out.

Here is the missing-pieces list, so "not built" means something exact. There
is no insurer pricing a second-hand dome, so the buyer who risks one is
self-insuring, and the risk comes straight out of the resale number. There is
no written standard for a serviced pad -- the pad of Chapter {{ch.the_pad}} --
so "pad" means whatever the last host built, and a dome that fits one pad may
not fit the next. There is no broker who moves domes for a living, so the
{{net.transport}} dollars a move costs is somebody's truck, borrowed, with
nobody standing behind the frame when it arrives. Those three are the trust
layer a park gets free from a lease and a landlord, and a network has to build
them itself. Chapter {{ch.honest_limits}} writes out what has to be true for
them to exist; this chapter only says the haircut will not fall until they do.

None of the three is a dome, and none is a pad. They are the paperwork, the
standards and the trucks a market runs on, and until they exist the network is
a good idea with a price and no shelf.
