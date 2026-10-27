"""The irori in a wedge dome: a sunken hearth under the apex, checked against the solver.

An irori is the Japanese sunken hearth: a square, stone-lined pit in the middle of
the floor, burning charcoal, with a pot hung over it from an adjustable hook (the
jizaikagi). It heated the room, cooked, lit, dried, kept the house's fire, and was
where the family sat -- each in a fixed place. A dome has its middle exactly where
an irori wants to be, under the apex, so this module asks what fits and what does not.

Every figure below is computed from the raw-wedge solver's own dome (the one the
Cabin World stands on its pad) or from a declared input in ``CONSTANTS``. The
source is an encyclopedia article, paraphrased; nothing here is a measured fire.
Run with ``py -3.12 -m two_v_demo.irori``.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

SOURCE = {
    "title": "Irori",
    "creator": "Wikipedia contributors",
    "url": "https://en.wikipedia.org/wiki/Irori",
    "licence": "CC BY-SA 4.0; paraphrased, not quoted",
    "accessed": "2026-10-27",
}
REFERENCES = {
    "irori": SOURCE["url"],
    "emc": "https://www.fpl.fs.usda.gov/documnts/fplgtr/fpl_gtr190.pdf",   # Wood Handbook, ch. 4
    "co": "https://www.cdc.gov/carbon-monoxide/",
}

# name, value, unit, kind, reason. Every input the film uses is put on screen
# before the figure that depends on it (CLAUDE.md: numbers are computed, not typed).
CONSTANTS = (
    ("hearth_side_m", 0.90, "m", "assumption",
     "The pit's inside width, chosen for a 3 m dome; irori sizes vary by house and region."),
    ("frame_w_m", 0.10, "m", "assumption", "The wooden border round the pit (the robuchi)."),
    ("pit_depth_m", 0.30, "m", "assumption", "Depth of the lined box below the floor boards."),
    ("seat_depth_m", 0.75, "m", "assumption", "Room for one person sitting on a cushion at one side."),
    ("seated_head_m", 0.95, "m", "estimate", "Head height of an adult sitting on a floor cushion."),
    ("pot_hang_m", 0.30, "m", "assumption", "Height of the hook above the floor with a kettle on it."),
    ("hood_m", 1.80, "m", "assumption", "Underside of a smoke hood, above a standing adult's head."),
    ("out_t_c", 5.0, "C", "assumption", "A damp shoulder-season day outside."),
    ("out_rh", 0.90, "fraction", "assumption", "Relative humidity of that outside air."),
    ("in_t_c", 20.0, "C", "assumption", "The same air, warmed by the hearth, with no water added."),
)
C = {name: value for name, value, _unit, _kind, _reason in CONSTANTS}

# The six jobs the article lists, plus the seventh it gives the building itself.
# Each is mapped to what it would mean in this dome; the mapping is ours.
JOBS = (
    ("heat", "Heating", "The fire sat in the middle of the room and warmed all of it.",
     "A dome's middle is the point furthest from every wall: the same place."),
    ("cook", "Cooking", "A pot hung over the coals; fish on skewers stood in the ash.",
     "The hook hangs from the apex hub, the one point every member climbs to."),
    ("light", "Lighting", "Before lamps, the hearth was the room's night light.",
     "Today a lamp does this; the hearth is no longer needed for it."),
    ("dry", "Drying", "A wooden lattice (the hidana) hung above it for clothes, food and wood.",
     "The first ring of hubs carries a lattice the same way."),
    ("keep", "Keeping fire", "The coals were kept alive to light everything else.",
     "Matches made this job obsolete."),
    ("gather", "Gathering", "Meals and evenings happened round it, each person in a fixed seat.",
     "A round room with a centre is already arranged for this."),
    ("dry_wood", "The house itself", "Warm air dried the timbers; smoke tar coated beams and thatch.",
     "The warm air helps a timber dome; the smoke is the part a tight dome cannot take."),
)

# The seats, by side of the hearth, as the article describes them. Names and
# who sits where vary by region; these are one common arrangement.
SEATS = (
    ("yokoza", "head of the household", "far side, facing the entry"),
    ("kakaza", "the head's wife", "one side"),
    ("kyakuza", "guests", "the other side"),
    ("kijiri", "the children (the lowest seat)", "the entry side"),
)


# ----------------------------------------------------------------------
# The dome, read from the solver
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def dome():
    """The solver's 2V dome as hub points (metres, floor centre at the origin) and faces.

    Uses the same solved model the Cabin World builds its frame from, so a figure here
    is a figure about the dome on screen.
    """
    from wedge_book import cover_scene

    topo = cover_scene.cover_model().topology
    v = np.array([np.asarray(p, float) for p in topo.vertices]) * cover_scene.IN
    faces = np.array([f.vertices for f in topo.faces], dtype=int)
    return v, faces


def floor_polygon() -> np.ndarray:
    """The base ring's hubs, in order round the floor (x, y)."""
    v, _ = dome()
    base = v[np.abs(v[:, 2]) < 1e-6][:, :2]
    order = np.argsort(np.arctan2(base[:, 1], base[:, 0]))
    return base[order]


def polygon_area(poly: np.ndarray) -> float:
    """Shoelace area of a closed polygon given as (n, 2) points."""
    x, y = poly[:, 0], poly[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)


def shell_height(x: float, y: float) -> float:
    """How high the frame's facets stand above the floor at (x, y), in metres.

    A vertical line through (x, y) leaves the dome through exactly one triangle;
    interpolate that triangle's height there (barycentric weights in plan view).
    """
    v, faces = dome()
    p = np.array([x, y])
    for f in faces:
        a, b, c = v[f]
        m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-12:
            continue                                  # a face seen edge-on from above
        u, w = np.linalg.solve(m, p - a[:2])
        if u >= -1e-9 and w >= -1e-9 and u + w <= 1 + 1e-9:
            return float(a[2] + u * (b[2] - a[2]) + w * (c[2] - a[2]))
    raise ValueError(f"({x:.2f}, {y:.2f}) is outside the dome's floor")


def enclosed_volume() -> float:
    """Air inside the frame's facets, m^3: one tetrahedron per face down to the floor centre.

    The floor centre lies in the base plane, so the floor itself adds no volume.
    """
    v, faces = dome()
    a, b, c = v[faces[:, 0]], v[faces[:, 1]], v[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6)


# ----------------------------------------------------------------------
# Air and wood
# ----------------------------------------------------------------------

def warmed_rh(t_out: float, rh_out: float, t_in: float) -> float:
    """Relative humidity of outside air warmed to ``t_in`` with no water added or removed."""
    from .seam_climate import vapour_pressure_hpa

    return rh_out * vapour_pressure_hpa(t_out) / vapour_pressure_hpa(t_in)


def wood_emc(t_c: float, rh: float) -> float:
    """Equilibrium moisture content of wood, per cent of dry weight.

    The Hailwood-Horrobin fit in the USDA Wood Handbook (FPL-GTR-190, ch. 4),
    which is written for temperature in degrees Fahrenheit. It is where the wood
    ends up after a long time in that air, not how fast it gets there.
    """
    if not 0 < rh < 1:
        raise ValueError("relative humidity must lie between 0 and 1")
    t = t_c * 9 / 5 + 32
    w = 330 + 0.452 * t + 0.00415 * t * t
    k = 0.791 + 4.63e-4 * t - 8.44e-7 * t * t
    k1 = 6.34 + 7.75e-4 * t - 9.35e-5 * t * t
    k2 = 1.09 + 2.84e-2 * t - 9.04e-5 * t * t
    kh = k * rh
    return 1800 / w * (kh / (1 - kh) + (k1 * kh + 2 * k1 * k2 * kh * kh) / (1 + k1 * kh + k1 * k2 * kh * kh))


# ----------------------------------------------------------------------
# Everything the film and the chapter print
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def facts() -> dict:
    v, faces = dome()
    poly = floor_polygon()
    floor = polygon_area(poly)
    radius = float(np.linalg.norm(poly, axis=1).min())        # to the hub centres
    inner_r = radius * math.cos(math.pi / len(poly))          # to the middle of a base member
    apex = float(v[:, 2].max())

    side, frame = C["hearth_side_m"], C["frame_w_m"]
    outer = side + 2 * frame                                   # the hearth with its border
    seat_out = outer / 2 + C["seat_depth_m"]                   # a seated person's back, from the centre
    # The tightest seat is one facing a hub straight on, so test the four
    # sides along the directions where the floor is narrowest.
    head_at = [shell_height(seat_out * math.cos(a), seat_out * math.sin(a))
               for a in np.linspace(0, math.tau, 40, endpoint=False)]
    rh_in = warmed_rh(C["out_t_c"], C["out_rh"], C["in_t_c"])
    volume = enclosed_volume()
    return {
        "hubs": len(v), "faces": len(faces), "base_sides": len(poly),
        "radius_m": radius, "inner_r_m": inner_r, "apex_m": apex,
        "floor_m2": floor, "floor_ft2": floor / 0.3048 ** 2,
        "hearth_outer_m": outer, "hearth_m2": outer * outer,
        "hearth_share": outer * outer / floor,
        "seat_out_m": seat_out,
        # The square the hearth and its four seated people take: the floor it costs.
        "circle_m2": (2 * seat_out) ** 2,
        "circle_share": (2 * seat_out) ** 2 / floor,
        "seat_corner_m": seat_out * math.sqrt(2),
        "seat_room_m": inner_r - seat_out,
        "seat_head_min_m": min(head_at),
        "seat_headroom_m": min(head_at) - C["seated_head_m"],
        "rod_m": apex - C["pot_hang_m"],
        "flue_m": apex - C["hood_m"],
        "volume_m3": volume, "volume_ft3": volume / 0.3048 ** 3,
        "rh_in": rh_in,
        "emc_out": wood_emc(C["out_t_c"], C["out_rh"]),
        "emc_in": wood_emc(C["in_t_c"], rh_in),
        "jobs": len(JOBS), "seats": len(SEATS),
    }


def validate_irori() -> None:
    f = facts()
    # The Wood Handbook's own table gives about 12 per cent at 70 F and 65 per cent RH.
    assert 11.5 < wood_emc((70 - 32) * 5 / 9, 0.65) < 12.5
    for bad in (0.0, 1.0, -0.1):
        try:
            wood_emc(20, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
    assert f["hubs"] == 26 and f["faces"] == 40 and f["base_sides"] == 10, "the 2V hemisphere"
    assert 2.5 < f["radius_m"] < 3.5 and abs(f["apex_m"] - f["radius_m"]) < 1e-6
    # The volume sits between the inscribed facets' bound and the full hemisphere.
    hemi = 2 / 3 * math.pi * f["radius_m"] ** 3
    assert 0.8 * hemi < f["volume_m3"] < hemi
    assert abs(shell_height(0, 0) - f["apex_m"]) < 1e-6
    assert f["seat_room_m"] > 0, "the seats must fit inside the base ring"
    assert f["seat_headroom_m"] > 0, "a seated person's head must clear the frame"
    assert C["pot_hang_m"] < C["hood_m"] < f["apex_m"], "kettle below the hood, hood below the apex"
    assert C["pit_depth_m"] < 0.62, "the box must fit in the air under the pad (cover_scene.DECK_TOP)"
    assert f["emc_in"] < f["emc_out"] and f["rh_in"] < C["out_rh"]
    assert len(C) == len(CONSTANTS)
    assert all(k in ("assumption", "estimate", "claimed", "measured", "standard") and u and why
               for _, _, u, k, why in CONSTANTS)


def report() -> str:
    f = facts()
    rows = ["THE IRORI IN A WEDGE DOME",
            f"Source: {SOURCE['title']} ({SOURCE['creator']}), {SOURCE['url']}, {SOURCE['licence']}.",
            "No fire was lit or measured for this; the dome figures are the solver's."]
    rows += [f"{n}: {v:g} {u} ({k}) -- {why}" for n, v, u, k, why in CONSTANTS]
    rows += [f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in f.items()]
    rows += ["An open charcoal fire makes carbon monoxide. The houses irori were built for were tall",
             "and leaky; a sealed dome is neither, so the fire here gets a hood, a flue and an alarm."]
    return "\n".join(rows)


if __name__ == "__main__":
    validate_irori()
    print(report())
