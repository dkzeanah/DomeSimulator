"""A home that meets you halfway: the dome as a barrier-free house.

The persuasive case that a single-level geodesic dome is unusually well
suited to wheelchair users and to anyone whose mobility is limited by age
or injury -- carried by a wheelchair that actually rolls up the ramp, in
through the door, turns in place, and tours the open floor while the
camera follows.

Numbers discipline, same as every other presentation here: every figure
about *the dome* is computed from ``two_v_demo.geometry`` and
``al_build`` at import time, never typed in. The figures about *the
standard* -- the 60-inch turning circle, the 32-inch clear door, the
1:12 ramp -- are published ADA / ANSI A117.1 accessibility requirements,
cited as external references, not measurements of this model. The two are
kept visibly separate so the comparison stays honest.
"""

from __future__ import annotations

import math

import numpy as np

import al_build as ab
from two_v_demo.geometry import build_demo_geometry
from presenter.script import OverlayPanel, Presentation, Scene, Shot

# --- dome figures, computed from the real geometry -------------------------

_GEO = build_demo_geometry()
_V = np.asarray(_GEO.vertices)
_BR = list(_GEO.base_ring)
# The base ring sits on the floor plane; its radius (per unit of dome
# radius) is the floor radius, and the tallest vertex is the crown.
_FLOOR_FACTOR = float(np.mean(np.hypot(_V[_BR][:, 0], _V[_BR][:, 1])))
_APEX_FACTOR = float(_V[:, 2].max())
_IN_PER_M = ab.FT_PER_M * 12.0

# One representative "home" dome, radius inside the product line's own
# home range (3.2-4.6 m). Everything downstream scales from this.
R = 4.2
DOOR_W_M = 1.0
RAMP_RISE_M = 0.30
RAMP_SLOPE = 12.0

FLOOR_DIAM_FT = 2.0 * R * _FLOOR_FACTOR * ab.FT_PER_M
FLOOR_AREA_FT2 = math.pi * (R * _FLOOR_FACTOR) ** 2 * ab.FT_PER_M ** 2
CENTER_H_FT = R * _APEX_FACTOR * ab.FT_PER_M
DOOR_CLEAR_IN = (DOOR_W_M - 0.05) * _IN_PER_M          # leaf minus the stop
RAMP_RUN_M = RAMP_RISE_M * RAMP_SLOPE
FLOOR_DIAM_IN = 2.0 * R * _FLOOR_FACTOR * _IN_PER_M

# --- the ADA / ANSI A117.1 standards being compared against (external) -----

ADA_TURN_IN = 60          # 304.3: a 60-inch diameter turning space
ADA_DOOR_IN = 32          # 404.2.3: 32-inch minimum clear door width
ADA_HALL_IN = 36          # 403.5.1: 36-inch minimum route clear width
ADA_RAMP = "1:12"         # 405.2: steepest ramp allowed


# ---------------------------------------------------------------------------

WORLD = (
    ("dome", {"radius": R, "skin_alpha": 0.12}),
    ("window_band", {"radius": R, "polar_deg": 55.0, "spread_deg": 16.0,
                     "tint": 0.20}),
    ("door", {"radius": R, "az_deg": 0.0, "width": DOOR_W_M, "open": 1.0}),
    ("ramp", {"radius": R, "az_deg": 0.0, "width": 1.5,
              "rise": RAMP_RISE_M, "slope": RAMP_SLOPE}),
    ("kitchen_run", {"radius": R, "az_deg": -35.0}),
    ("furniture", {"radius": R, "az_deg": 60.0, "chairs": 3}),
    ("wheelchair", {"radius": R, "progress": 0.0, "ramp_rise": RAMP_RISE_M,
                    "ramp_slope": RAMP_SLOPE}),
)


def _world(extra=(), **overrides):
    out = []
    for name, params in WORLD:
        p = dict(params)
        p.update(overrides.get(name, {}))
        out.append((name, p))
    out.extend(extra)
    return tuple(out)


def _ft(value: float) -> str:
    return f"{value:.0f} ft"


def build() -> Presentation:
    scenes = (
        # 1 -----------------------------------------------------------------
        Scene(
            "arrival", "The house is the barrier",
            "on grass at dusk",
            world=_world(),
            shots=(
                Shot("establish", 8.5, lens="ultrawide", focus="ramp",
                     yaw=28, pitch=15, orbit=12,
                     caption="One level, one ramp, one wide door",
                     panel=OverlayPanel(
                         title="THE EVERYDAY BARRIER",
                         bullets=(
                             "A conventional house fights a wheelchair",
                             "Steps at the door, split levels, stairs",
                             "Interior doors and halls too tight to turn",
                             "The building becomes the disability"),
                         position="right"),
                     narration=(
                         "For someone who uses a wheelchair, an ordinary "
                         "house can be the hardest part of the day.",
                         "Steps at the front door. Narrow interior doors. "
                         "Hallways too tight to turn around in. The "
                         "building itself becomes the disability.",
                         "A single level dome answers almost every one of "
                         "those problems with its shape. Watch.")),
                Shot("roll_in", 9.0, lens="wide", focus="wheelchair_wide",
                     yaw=150, pitch=11, orbit=-8,
                     actions=(("wheelchair", "progress", 0.0, 0.30),),
                     caption="No steps to stop at the threshold",
                     narration=(
                         "Here is our resident, arriving home. No steps to "
                         "stop at. The path runs straight up a gentle ramp "
                         "to a door that is already wide open.",
                         "From the sidewalk to the living room is one "
                         "continuous, level surface.")),
            ),
        ),
        # 2 -----------------------------------------------------------------
        Scene(
            "entry", "Zero-threshold entry",
            "on grass at dusk",
            world=_world(wheelchair={"radius": R, "progress": 0.32,
                                     "ramp_rise": RAMP_RISE_M,
                                     "ramp_slope": RAMP_SLOPE}),
            shots=(
                Shot("ramp_macro", 8.5, lens="portrait", focus="ramp",
                     yaw=120, pitch=9, orbit=7,
                     actions=(("wheelchair", "progress", 0.30, 0.40),),
                     caption=f"Ramp at {ADA_RAMP} · door clears "
                             f"{DOOR_CLEAR_IN:.0f} in",
                     panel=OverlayPanel(
                         title="ZERO-THRESHOLD ENTRY",
                         stats=(("Ramp slope", f"{ADA_RAMP} (ADA max)"),
                                ("Rise / run",
                                 f"{RAMP_RISE_M:.2f} m / {RAMP_RUN_M:.1f} m"),
                                ("Door clear width",
                                 f"{DOOR_CLEAR_IN:.0f} in"),
                                ("ADA minimum door", f"{ADA_DOOR_IN} in")),
                         position="right"),
                     narration=(
                         "The entrance is a ramp built to one in twelve, "
                         "the steepest slope the accessibility standard "
                         "allows, and a threshold with no lip to catch a "
                         "caster.",
                         "The door leaf clears about thirty-seven inches. "
                         "The standard asks for thirty-two. There is room "
                         "to spare, and no help needed to get through "
                         "it.")),
            ),
        ),
        # 3 -----------------------------------------------------------------
        Scene(
            "open_floor", "One open room, no interior walls",
            "on grass at dusk",
            world=_world(dome={"radius": R, "skin_alpha": 0.08},
                         wheelchair={"radius": R, "progress": 0.40,
                                     "ramp_rise": RAMP_RISE_M,
                                     "ramp_slope": RAMP_SLOPE}),
            shots=(
                Shot("turn_in_place", 9.5, lens="wide",
                     focus="wheelchair_wide",
                     perspective=3, yaw=-52, pitch=40, orbit=16,
                     actions=(("wheelchair", "progress", 0.40, 0.55),),
                     caption="A full turn in place — the whole floor "
                             "is a turning space",
                     panel=OverlayPanel(
                         title="ONE OPEN ROOM",
                         stats=(("Clear floor",
                                 f"{FLOOR_DIAM_FT:.0f} ft across"),
                                ("Floor area", f"{FLOOR_AREA_FT2:.0f} sq ft"),
                                ("Interior bearing walls", "0"),
                                ("ADA turning circle",
                                 f"{ADA_TURN_IN} in")),
                         position="right"),
                     narration=(
                         "Inside, the reason the dome works is structural. "
                         "The shell carries its own load, so there are no "
                         "interior bearing walls at all. The whole floor "
                         "is one open room.",
                         "The accessibility standard asks for a sixty inch "
                         "circle to turn around in. This floor is more than "
                         "twenty-seven feet across. The turning space is "
                         "the entire home. Watch a full turn, in place, "
                         "with no three point shuffle.")),
                Shot("top_read", 7.5, lens="wide", focus="wheelchair_wide",
                     perspective=3, yaw=90, pitch=70, orbit=10,
                     caption="No hallways to thread, no corners to fight",
                     narration=(
                         "From above you can see there is nothing to "
                         "thread through. No corridors, no pinch points, "
                         "no doorways between you and any part of your own "
                         "home.")),
            ),
        ),
        # 4 -----------------------------------------------------------------
        Scene(
            "one_path", "Everything on one continuous curve",
            "on grass at dusk",
            world=_world(
                dome={"radius": R, "skin_alpha": 0.09},
                wheelchair={"radius": R, "progress": 0.55,
                            "ramp_rise": RAMP_RISE_M,
                            "ramp_slope": RAMP_SLOPE},
                extra=(("utility_column", {"radius": R, "reveal": 1.0,
                                           "anchor": 1.0}),)),
            shots=(
                Shot("tour", 11.0, lens="wide", focus="wheelchair_wide",
                     yaw=-60, pitch=34, orbit=16,
                     actions=(("wheelchair", "progress", 0.55, 0.85),),
                     caption="Kitchen, table, living — one smooth loop",
                     panel=OverlayPanel(
                         title="EVERYTHING ON ONE CURVE",
                         bullets=(
                             "No dead-end hallways to back out of",
                             "Kitchen, dining and living on one loop",
                             "Central services keep plumbing and power "
                             "in easy reach",
                             "Furniture floats — grab bars anchor to "
                             "the frame anywhere"),
                         position="left"),
                     narration=(
                         "Everyday life happens on one smooth loop. The "
                         "kitchen, the table, the living area all sit "
                         "around an open center, reached along a "
                         "continuous curve instead of a chain of rooms.",
                         "The utilities run up a column in the middle, so "
                         "the sink, the cooktop and the power are close to "
                         "the center of the circle, never at the end of a "
                         "long, narrow run.")),
            ),
        ),
        # 5 -----------------------------------------------------------------
        Scene(
            "transfers", "The frame is a lift you can anchor anywhere",
            "on grass at dusk",
            world=_world(
                dome={"radius": R, "skin_alpha": 0.09},
                # Park the chair on the pivot spot and hang the track
                # directly over it, so the sling comes down to the seated
                # rider instead of to an empty patch of floor.
                wheelchair={"radius": R, "progress": 0.45,
                            "ramp_rise": RAMP_RISE_M,
                            "ramp_slope": RAMP_SLOPE},
                extra=(
                    ("ceiling_lift", {"radius": R, "az_deg": 0.0,
                                      "polar_deg": 40.0, "carriage": 0.09,
                                      "lower": 0.0}),
                    ("grab_bar", {"radius": R, "az_deg": 0.0,
                                  "polar_deg": 74.0, "length": 0.9}))),
            shots=(
                Shot("hoist", 10.0, lens="wide", focus="wheelchair_wide",
                     yaw=96, pitch=15, orbit=6,
                     actions=(("ceiling_lift", "lower", 0.0, 1.0),),
                     caption="A rigid shell carries a hoist — or a grab "
                             "bar — at any point",
                     panel=OverlayPanel(
                         title="INDEPENDENT TRANSFERS",
                         bullets=(
                             "The geodesic shell is one rigid space frame",
                             "A ceiling hoist can hang from it anywhere",
                             "Grab bars bolt to a frame member, not a "
                             "hoped-for stud",
                             "Transfers to bed or bath without a "
                             "free-standing gantry"),
                         position="right"),
                     narration=(
                         "Independence often comes down to transfers: bed "
                         "to chair, chair to bath. In a stick built house "
                         "a ceiling lift needs blocking hunted out inside "
                         "the walls.",
                         "The dome is a single rigid frame. A hoist can "
                         "hang from it almost anywhere, and a grab bar "
                         "bolts straight to a structural member exactly "
                         "where a transfer needs one.")),
            ),
        ),
        # 6 -----------------------------------------------------------------
        Scene(
            "safe", "One level, and safe where you are",
            "storm",
            world=_world(dome={"radius": R, "skin_alpha": 0.16},
                         wheelchair={"radius": R, "progress": 0.98,
                                     "ramp_rise": RAMP_RISE_M,
                                     "ramp_slope": RAMP_SLOPE}),
            shots=(
                Shot("shelter", 9.5, lens="wide", focus="dome",
                     yaw=-120, pitch=22, orbit=12,
                     caption="No stairs to fall on · shelter in place",
                     panel=OverlayPanel(
                         title="SAFE WHERE YOU ARE",
                         bullets=(
                             "Single level: no stairs to climb or fall on",
                             "Aerodynamic shell rides out wind and storm",
                             "Shelter in place — evacuation is hardest "
                             "for the mobility impaired",
                             "Tight, efficient envelope: low bills on a "
                             "fixed income"),
                         position="right"),
                     narration=(
                         "Safety for someone who cannot move quickly is "
                         "not only about the everyday. It is about the bad "
                         "day.",
                         "There are no stairs to fall on, because there "
                         "are no stairs. The rounded shell sheds wind "
                         "instead of catching it, so sheltering in place "
                         "is realistic, and evacuation is exactly what is "
                         "hardest for someone with limited mobility.",
                         "And the same tight envelope that makes it strong "
                         "keeps the energy bills low, which matters most "
                         "on a fixed income.")),
            ),
        ),
        # 7 -----------------------------------------------------------------
        Scene(
            "honest", "The honest trade-offs",
            "on grass at dusk",
            world=_world(dome={"radius": R, "skin_alpha": 0.10},
                         wheelchair={"radius": R, "progress": 0.72,
                                     "ramp_rise": RAMP_RISE_M,
                                     "ramp_slope": RAMP_SLOPE}),
            shots=(
                Shot("tradeoffs", 10.0, lens="wide", focus="wheelchair_wide",
                     yaw=40, pitch=26, orbit=12,
                     caption="What a dome asks in return",
                     panel=OverlayPanel(
                         title="THE HONEST TRADE-OFFS",
                         bullets=(
                             "Curved walls limit tall against-wall "
                             "cabinets — the central core answers it",
                             "A dome can focus sound; soft surfaces and "
                             "panels tame it",
                             "Best designed accessible from day one, not "
                             "retrofitted",
                             "Low perimeter: usable wall is near the "
                             "middle, not at the rim"),
                         position="left"),
                     narration=(
                         "No honest case is all upside. The curved "
                         "perimeter makes tall cabinets against the wall "
                         "awkward, which is exactly why the storage and "
                         "services belong on the central core.",
                         "A dome can also focus sound, so it wants soft "
                         "furnishings and a few acoustic panels. And it is "
                         "far easier to design accessible from the first "
                         "sketch than to retrofit later. These are real "
                         "costs, and they are all manageable.")),
            ),
        ),
        # 8 -----------------------------------------------------------------
        Scene(
            "compare", "Dome versus conventional house",
            "on grass",
            world=(("comparison_pair", {"box_w": 8.0, "box_l": 8.0,
                                        "box_h": 3.0, "dome_r": R,
                                        "gap": 3.0}),),
            shots=(
                Shot("side_by_side", 10.5, lens="wide", focus="compare_pair",
                     yaw=-40, pitch=20, orbit=14,
                     caption="Same footprint — one you can cross, one "
                             "you fight",
                     panel=OverlayPanel(
                         title="DOME vs CONVENTIONAL",
                         bullets=(
                             "Dome: step-free, single level, open plan",
                             "Box: steps, split levels, framed hallways",
                             "Dome: turning space is the whole floor",
                             "Box: turning space must be carved out room "
                             "by room",
                             "Dome: lift and rails anchor to the shell "
                             "anywhere"),
                         position="right"),
                     narration=(
                         "Put them side by side on the same footprint. The "
                         "boxed house divides that footprint into framed "
                         "rooms and hallways, and every accessible feature "
                         "has to be carved back out of it.",
                         "The dome starts as one open, single level "
                         "volume. Accessibility is not a renovation bolted "
                         "on afterward. It is the shape you began with.")),
            ),
        ),
        # 9 -----------------------------------------------------------------
        Scene(
            "close", "A home that meets you halfway",
            "tropical beach at dusk",
            world=_world(dome={"radius": R, "skin_alpha": 0.11},
                         wheelchair={"radius": R, "progress": 1.0,
                                     "ramp_rise": RAMP_RISE_M,
                                     "ramp_slope": RAMP_SLOPE}),
            shots=(
                Shot("home", 10.0, lens="wide", focus="wheelchair_wide",
                     perspective=6, yaw=-90, pitch=20,
                     caption="Step-free · open plan · anchored anywhere",
                     panel=OverlayPanel(
                         title="A HOME THAT MEETS YOU HALFWAY",
                         bullets=(
                             "Step-free from the sidewalk to every room",
                             "One open floor — the turning space is the "
                             "whole house",
                             "A rigid frame that holds a lift or a rail "
                             "wherever you need it",
                             "One level, storm-safe, cheap to run"),
                         position="bottom"),
                     narration=(
                         "A dome will not cure anything. But it stops "
                         "spending a person's energy on the building.",
                         "Step free from the street. One open floor you "
                         "can cross and turn in freely. A frame that holds "
                         "a lift or a rail wherever you need it. One safe "
                         "level, cheap to keep.",
                         "It is a house that meets you halfway, instead of "
                         "standing in your way.")),
            ),
        ),
    )
    return Presentation(
        title="A Home That Meets You Halfway",
        author="Presenter Studio",
        scenes=scenes,
    )
