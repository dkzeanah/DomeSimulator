---
chapter: 23
title: Compare Dew Points, Not Humidity
strand: explain
status: draft
target: 2220
updated: 2026-09-30
---

# 23. Compare Dew Points, Not Humidity

The seam channel can move air in almost any direction you like. Outside air
in, inside air out, round in a loop, through a desiccant or past it, over a
cold plate or a warm one. That is a lot of choices, and the way a system like
this goes wrong is by making them on a feeling: it is a damp day, so shut
everything.

This chapter makes them on one number.

![Two airs, and the only number that says which one is drier.](plate-dew-point.png)

## The one rule

**Never compare relative humidity. Compare dew points.**

Relative humidity says how full the air is compared to how much it could hold
**at its own temperature**. Cold air holds very little, so cold air reads as
damp while carrying almost nothing. The dew point is the temperature at which
the water in the air starts coming out as liquid, and it depends only on how
much water there actually is. The lower the dew point, the drier the air,
whatever the thermometer says.

Take a winter day:

    outside   {{clim.cd_t_out}} C at {{clim.cd_rh_out}}%    dew point {{clim.cd_dp_out}} C    {{clim.cd_w_out}} g/kg
    inside    {{clim.cd_t_in}} C at {{clim.cd_rh_in}}%      dew point {{clim.cd_dp_in}} C     {{clim.cd_w_in}} g/kg

The outside air sounds damp. It carries {{clim.cd_w_out}} grams of water in
every kilogram; the room's air carries {{clim.cd_w_in}}. Bring it in, warm it
up, and it dries the dome. A rule that looked at humidity would have kept it
out.

The dew point comes from temperature and relative humidity by the Magnus
formula, which is what every weather station uses. A cheap sensor gives both
inputs.

## The three questions

The controller asks three questions, in this order.

**1. Which air is actually drier?** If the outside dew point is below the
inside one, outside air has drying power. If it is above, outside air is a
source of water, however cool it feels.

**2. Will this air condense on that surface?** Water comes out of air on any
surface colder than the air's dew point. So a condensing plate must be colder
than the dew point, and every piece of wood must be warmer than it, with a
margin. This book keeps wood {{clim.margin}} degrees above the dew point of any
air that touches it.

**3. Which way should the air move?** The answer to the first two decides it:
toward the structure only with air drier than the water you are trying to
remove -- unless you are deliberately sending wetter air to a cold metal
surface built to collect and drain it (Chapter {{ch.metal}}).

## The modes

That gives the one channel {{clim.modes}} ways to move air:

    {{clim.modes_table}}

Two of them never touch the living space at all. They are the ones that make
this more than a ventilation system.

## Eleven weathers, one controller

To test it, here is the table the owner of this design drew up -- the weathers
that matter and what the seam should do in each -- plus one more: muggy outside
with a wet frame. The temperatures and humidities are this book's estimates of
typical conditions, not measurements from a site. Wet weathers carry a wood
moisture reading over {{clim.mc_wet}} percent.

The controller sees only the numbers, and works only from dew points:

    {{clim.weathers_table}}

Every one of the {{clim.weathers}} gets the answer the owner's table gives, and
the book's own checks fail if one ever does not.

## The loop and the purge

The two modes worth the extra plumbing are these.

**The frame loop** takes the seam's own air, dries it in the desiccant and
sends it back round the seam. Nothing conditioned is thrown outside and nothing
muggy is pulled in. On a hot, humid day with a wet frame -- the one weather
where neither the inside nor the outside air can help -- it is the only thing
in the design that dries the wood.

**The purge** takes dry outside air in at one port, through a wet seam, and
straight back out at another. The wet air never enters the room. It is how a
frame recovers after rain, and on a sunny day it vents the vapour the sun drives
out of a wet skin before that vapour gets driven inward.

Both need something the plain barrier fan does not: two outside ports per
circuit, and a gate that can route a seam to outside, to the room or to the
drawer. That is the price of separating **drying the structure** from
**ventilating the house**. It is worth paying. They are different jobs, and a
building that does both with one airflow does neither well.

## The controller, as code

The whole decision fits on one page. This is the function the book's tables
come from, trimmed of its comments:

    def decide(s):
        dp_in, dp_out = dew_point(s.t_in, s.rh_in), dew_point(s.t_out, s.rh_out)
        dp_seam = dew_point(s.t_seam, s.rh_seam)
        margin = C["dp_margin_k"]
        wet_frame = s.wood_mc >= C["mc_wet"] or s.rh_seam >= C["seam_rh_wet"]
        if s.rain:
            return "FRAME_LOOP" if wet_frame else "CLOSED"
        if wet_frame:
            return "PURGE" if dp_out < dp_seam - margin else "FRAME_LOOP"
        if s.rh_in > C["rh_high"]:
            if dp_out < dp_in - margin:
                if s.harvest and s.t_out <= dp_in - C["plate_below_dp_k"]:
                    return "CONDENSE"
                return "EXHAUST"
            return "DRY_SUPPLY"
        if dp_out < dp_in - margin:
            return "INTAKE"
        if dp_out > dp_in + margin:
            return "DRY_SUPPLY"
        return "IDLE"

The sensors it needs are ordinary ones: temperature and humidity inside,
outside and in the seam; a wood moisture pin; a rain switch. The margin stops
the controller flapping between two modes when the two airs are nearly the
same. Every value it compares against is declared, with its kind:

    {{clim.constants_table}}
