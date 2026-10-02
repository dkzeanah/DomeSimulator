"""The dome's own numbers, by name, for concept cards to compare against.

A concept from a video only means something here once it is sized against
*this* dome: does it cool this volume, fit this channel, beat these plates?
A card may use any name below in its ``figures`` expressions and narration.
Every value is computed by the module that owns it -- none is typed here.

    py -3.12 -m concepts facts        # the list, with values
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def dome_facts() -> dict[str, tuple[float, str, str]]:
    """``{name: (value, unit, where it comes from)}``."""
    import seed_world
    from two_v_demo import channel_facts as cf
    from wedge_book import systems

    g = seed_world.geometry()
    air = systems.air_barrier()
    water = systems.water_comparison()
    tight = min(cf.seam_types(), key=lambda t: t.gap_deg)
    room = cf.room(tight)
    clock = systems.build_clock()
    return {
        "dome_radius_ft": (g.radius_in / 12.0, "ft", "seed_world.geometry().radius_in"),
        "dome_floor_sqft": (g.floor_circle_sqft, "sq ft", "seed_world.geometry().floor_circle_sqft"),
        "dome_shell_sqft": (g.panel_sqft, "sq ft", "seed_world.geometry().panel_sqft"),
        "dome_volume_cuft": (air["volume_cuft"], "cu ft", "systems.air_barrier()['volume_cuft']"),
        "dome_members": (clock["members"], "", "systems.build_clock()['members']"),
        "dome_seams": (float(g.seam_count), "", "seed_world.geometry().seam_count"),
        "dome_seam_ft": (g.seam_length_in / 12.0, "ft", "seed_world.geometry().seam_length_in"),
        "dome_air_cfm": (air["cfm"], "cfm", "systems.air_barrier()['cfm'] -- the ventilation it needs"),
        "dome_channel_in2": (room.inside_in2, "sq in",
                             "channel_facts.room(tightest seam).inside_in2 -- room inside one seam's key"),
        "dome_channel_round_in": (room.inside_round_in, "in",
                                  "channel_facts.room(tightest seam).inside_round_in"),
        "dome_peltier_w": (water["peltier_watts"], "W", "systems.water_comparison()['peltier_watts']"),
        "dome_peltier_gal_year": (water["peltier_gallons_per_year"], "gal/yr",
                                  "systems.water_comparison() -- what the seam's plates condense"),
        "dome_rain_gal_per_inch": (water["gallons_per_inch"], "gal",
                                   "systems.water_comparison()['gallons_per_inch']"),
        "dome_work_hours": (clock["week"], "h", "systems.build_clock()['week']"),
    }


def values() -> dict[str, float]:
    return {name: value for name, (value, _unit, _src) in dome_facts().items()}


SLOTS: dict[str, tuple[str, str]] = {
    # slot: (what it is, where the repo handles it)
    "seam_channel": ("the V channel in every seam: water, wire, air, the three-way gate, "
                     "the desiccant cartridge", "two_v_demo/channel_facts.py, wedge_book/systems.py"),
    "utility_core": ("the stem cell dome's service column: water, drain, power, controls",
                     "seed_model.py, two_v_demo/lesson_module_build.py"),
    "air": ("ventilation, the pressure barrier, dehumidifying, cooling",
            "wedge_book/systems.py (air_barrier, seam_module)"),
    "water": ("rain off the roof, the tank, filtering, condensing",
              "wedge_book/systems.py (water_bill, water_comparison)"),
    "power": ("solar, the battery, loads, metering", "wedge_book/systems.py (power_bill)"),
    "skin": ("the layers over the frame: shell, insulation, the hull",
             "seed_model.py, two_v_demo/lesson_seed_pitch.py"),
    "pad": ("the deck the dome stands on, piers, the pad network", "pad_deck.py, dome_park.py"),
    "frame": ("the wedge members, seams, keys and joints",
              "geodesic_raw_wedge_dome_dihedral.py, two_v_demo/wedge_geometry.py"),
    "timber": ("the tree, the log, the rip, yield and value",
               "two_v_demo/lesson_harvest.py, two_v_demo/pine_value_economics.py"),
    "site": ("the hilltop, the network of domes, hosts and tenants", "dome_park.py"),
}
