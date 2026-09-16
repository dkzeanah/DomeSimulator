"""Two sets inside the same shell: a dome home and a dome store.

:mod:`two_v_demo.drama_stage` treats the dome as blocking -- anchors to
stand on, lights on real struts.  This treats it as a *room*: something
with a floor you furnish, a wall that curves in over your head, and a
catalogue of things to put in it.

The one rule the dome imposes
-----------------------------
A geodesic room has no vertical walls.  How tall a thing is allowed to
be depends on how far out it stands, and :func:`shell_clearance` answers
that from the *faceted* shell the renderer actually draws -- a ray cast
straight up against the hemisphere's own triangles -- rather than from
the sphere those triangles are inscribed in.  The difference is real: a
flat panel is a chord, so it hangs below the sphere it approximates, and
a wardrobe sized against the sphere goes through the roof of the dome it
is standing in.  :func:`validate_dome_interiors` proves the faceted
figure is never the more generous of the two.

Everything in the catalogue is measured against that.  A prop declares
its footprint and its height, the composer asks the shell how much room
there is where you are pointing, and a piece that does not fit does not
go in.  No prop carries a "where it can go" list; the geometry decides.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

import numpy as np

from .geometry import build_demo_geometry
from .render_kit import TriangleBatch


Colour = tuple[float, float, float, float]

GEOMETRY = build_demo_geometry()


# ----------------------------------------------------------------------
# The shell, as a ceiling
# ----------------------------------------------------------------------

@lru_cache(maxsize=4)
def _shell_triangles(radius_m: float):
    """The hemisphere's triangles at set scale, with their 2D footprints."""
    vertices = np.asarray(GEOMETRY.vertices, dtype=float) * radius_m
    triangles = []
    for face in GEOMETRY.hemisphere_faces:
        a, b, c = (vertices[int(index)] for index in face)
        area = ((b[0] - a[0]) * (c[1] - a[1])
                - (c[0] - a[0]) * (b[1] - a[1]))
        if abs(area) < 1e-9:
            continue
        triangles.append((a, b, c, area))
    return tuple(triangles)


def shell_clearance(x: float, y: float, radius_m: float) -> float:
    """How much headroom the faceted dome leaves over a floor point.

    Cast a ray straight up and take the highest facet it passes through.
    Outside the base ring there is no dome overhead and the answer is
    zero, which is what makes the composer refuse to place furniture in
    the yard.
    """
    best = 0.0
    for a, b, c, area in _shell_triangles(radius_m):
        u = ((b[0] - x) * (c[1] - y) - (c[0] - x) * (b[1] - y)) / area
        if u < -1e-9:
            continue
        v = ((c[0] - x) * (a[1] - y) - (a[0] - x) * (c[1] - y)) / area
        if v < -1e-9:
            continue
        w = 1.0 - u - v
        if w < -1e-9:
            continue
        height = u * a[2] + v * b[2] + w * c[2]
        best = max(best, height)
    return best


BASE_RING_SIDES = len(GEOMETRY.base_ring)
"""How many struts the dome stands on.  Read off the geometry, because
a 2V hemisphere's base is a polygon and the number of sides is a fact
about the model rather than a choice."""


def base_ring_apothem(radius_m: float) -> float:
    """How far the floor really reaches, in the direction of a strut.

    The base ring is a regular polygon inscribed in the circle of the
    set radius, so between two ground nodes the edge of the dome cuts
    inside that circle.  Furniture placed in the difference is standing
    outside the building.
    """
    return radius_m * math.cos(math.pi / BASE_RING_SIDES)


def sphere_clearance(x: float, y: float, radius_m: float) -> float:
    """The same question asked of the sphere, for comparison only.

    Kept so :func:`validate_dome_interiors` can show that the faceted
    answer is always the smaller one, which is the reason the composer
    uses the faceted answer.
    """
    reach = math.hypot(x, y)
    if reach >= radius_m:
        return 0.0
    return math.sqrt(radius_m * radius_m - reach * reach)


# ----------------------------------------------------------------------
# The sets
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class InteriorSet:
    """One furnished dome: how big, what it is for, how it is lit."""

    set_id: str
    label: str
    radius_m: float
    floor: Colour
    wall: Colour
    accent: Colour
    warm: Colour
    key_light: tuple[float, float, float]
    note: str


DOME_SETS: dict[str, InteriorSet] = {
    "DOME_HOME": InteriorSet(
        set_id="DOME_HOME",
        label="The dome house",
        radius_m=6.5,
        floor=(0.36, 0.31, 0.27, 1.0),
        wall=(0.38, 0.36, 0.37, 1.0),
        accent=(0.86, 0.55, 0.25, 1.0),
        warm=(1.00, 0.80, 0.52, 1.0),
        key_light=(-0.38, -0.52, -0.76),
        note="Thirteen metres across, warm floor, everything soft and "
             "low so the shell reads as the ceiling it is.",
    ),
    "DOME_STORE": InteriorSet(
        set_id="DOME_STORE",
        label="The dome store",
        radius_m=8.0,
        floor=(0.80, 0.78, 0.75, 1.0),
        wall=(0.88, 0.88, 0.90, 1.0),
        accent=(0.20, 0.78, 0.92, 1.0),
        warm=(0.98, 0.94, 0.88, 1.0),
        key_light=(-0.20, -0.35, -0.91),
        note="Sixteen metres across, pale floor, lit flat and bright so "
             "the clothes are the only colour in the room.",
    ),
}


def interior_set(set_id: str) -> InteriorSet:
    try:
        return DOME_SETS[set_id]
    except KeyError:
        raise ValueError(f"unknown set {set_id!r}; choose from "
                         f"{', '.join(DOME_SETS)}") from None


# ----------------------------------------------------------------------
# Placing things in the room
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Placer:
    """A local frame on the floor: origin, and which way the piece faces.

    Every prop is modelled facing +X at the origin with its footprint
    centred and its feet on z=0.  This turns those local coordinates
    into world ones, so a builder never has to think about rotation and
    a rotated piece cannot come out sheared.
    """

    x: float
    y: float
    z: float
    yaw_deg: float

    def point(self, along: float, across: float, up: float) -> np.ndarray:
        angle = math.radians(self.yaw_deg)
        cos, sin = math.cos(angle), math.sin(angle)
        return np.array([self.x + along * cos - across * sin,
                         self.y + along * sin + across * cos,
                         self.z + up])

    def box(self, batch, along, across, up, length, width, height,
            colour: Colour) -> None:
        """An oriented box, given its centre and its extents.

        ``batch.box`` is axis-aligned, which is no use to a sofa at
        thirty degrees, so the corners are built locally and turned.
        """
        corners = [
            self.point(along + sx * length * 0.5,
                       across + sy * width * 0.5,
                       up + sz * height * 0.5)
            for sx, sy, sz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1),
                               (-1, 1, -1), (-1, -1, 1), (1, -1, 1),
                               (1, 1, 1), (-1, 1, 1))
        ]
        for indices in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            batch.quad(*(corners[index] for index in indices), colour)

    def post(self, batch, along, across, base, top, radius,
             colour: Colour, sides: int = 8) -> None:
        batch.cylinder(self.point(along, across, base),
                       self.point(along, across, top), radius, colour, sides)

    def bar(self, batch, one, two, radius, colour: Colour,
            sides: int = 7) -> None:
        batch.cylinder(self.point(*one), self.point(*two), radius, colour,
                       sides)

    def ball(self, batch, along, across, up, radius, colour: Colour) -> None:
        batch.sphere(self.point(along, across, up), radius, colour, 4, 8)

    def legs(self, batch, length, width, height, radius, colour: Colour,
             inset: float = 0.08) -> None:
        for sx in (-1, 1):
            for sy in (-1, 1):
                self.post(batch,
                          sx * (length * 0.5 - inset),
                          sy * (width * 0.5 - inset),
                          0.0, height, radius, colour, 6)


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Prop:
    """One thing you can put in a dome."""

    prop_id: str
    label: str
    category: str
    sets: tuple[str, ...]
    """Which rooms offer it.  A cash desk is not a bedroom item."""
    length: float
    """Along its facing direction, metres."""
    width: float
    """Across it."""
    height: float
    builder: str
    mount: str = "floor"
    """``floor``, ``wall`` (wants the curve behind it) or ``ceiling``."""
    overlap: bool = False
    """True for rugs and runway strips, which other things stand on."""
    seats: int = 0
    seat_height: float = 0.0
    note: str = ""

    @property
    def footprint(self) -> float:
        return self.length * self.width

    @property
    def diagonal(self) -> float:
        return math.hypot(self.length, self.width)


CATEGORIES: tuple[str, ...] = (
    "SEATING", "TABLES", "SLEEP", "STORAGE", "KITCHEN", "BATH",
    "LIGHT", "GREEN", "DECOR", "STRUCTURE", "FIXTURE", "DISPLAY",
    "SERVICE",
)
"""The order the composer cycles categories in, which is roughly the
order you would actually furnish a room."""


# Standard seat height: taken from the seated pose rather than declared,
# so a sofa is the height the cast's own hips land at when they sit.
def standard_seat_height() -> float:
    from .glam_figure import seat_height

    return round(seat_height(1.70), 3)


SEAT = standard_seat_height()
TABLE = round(SEAT + 0.26, 3)
"""A dining table clears a seated lap by this much.  Derived from the
seat rather than typed in, so the two cannot drift apart."""
COUNTER = round(SEAT + 0.44, 3)
"""Kitchen counter and cash desk height."""


PROPS: dict[str, Prop] = {}


def _prop(*args, **kwargs) -> None:
    item = Prop(*args, **kwargs)
    PROPS[item.prop_id] = item


HOME = ("DOME_HOME",)
STORE = ("DOME_STORE",)
BOTH = ("DOME_HOME", "DOME_STORE")

_prop("SECTIONAL", "Sectional sofa", "SEATING", HOME, 0.98, 2.45, 0.90,
      "sectional", seats=3, seat_height=SEAT,
      note="Long, low, and the thing everybody ends up arguing on.")
_prop("LOUNGE_CHAIR", "Lounge chair", "SEATING", BOTH, 0.86, 0.84, 0.98,
      "lounge_chair", seats=1, seat_height=SEAT,
      note="One chair, angled. Whoever takes it has taken the room.")
_prop("DAYBED", "Daybed", "SEATING", HOME, 1.95, 0.82, 0.52, "daybed",
      seats=2, seat_height=SEAT * 0.86,
      note="For lying across sideways while somebody else is talking.")
_prop("DINING_CHAIR", "Dining chair", "SEATING", HOME, 0.48, 0.50, 0.92,
      "dining_chair", seats=1, seat_height=SEAT,
      note="Straight-backed. Nobody relaxes in one and that is the point.")
_prop("BENCH", "Fitting bench", "SEATING", STORE, 1.40, 0.46, 0.46,
      "bench", seats=2, seat_height=SEAT * 0.92,
      note="Where you sit while somebody else decides what suits you.")
_prop("STOOL", "Bar stool", "SEATING", BOTH, 0.42, 0.42, 0.74, "stool",
      seats=1, seat_height=0.74,
      note="High enough that her heels still touch the rail.")

_prop("COFFEE_TABLE", "Round coffee table", "TABLES", HOME, 0.96, 0.96, 0.40,
      "round_table", note="A disc on a stem, low enough to put feet on.")
_prop("DINING_TABLE", "Dining table", "TABLES", HOME, 1.65, 0.95, TABLE,
      "dining_table", note="Seats six if nobody is fighting.")
_prop("DESK", "Desk", "TABLES", BOTH, 1.40, 0.68, TABLE + 0.24,
      "desk", note="Where the numbers that decide the store get done.")
_prop("LOOKBOOK_TABLE", "Lookbook table", "TABLES", STORE, 1.45, 0.92, 0.78,
      "lookbook_table",
      note="Folded stacks, arranged by somebody with strong opinions.")
_prop("BAR_CART", "Bar cart", "TABLES", HOME, 0.82, 0.46, 1.16, "bar_cart",
      note="Wheeled, gold, and never quite where it was left.")

_prop("PLATFORM_BED", "Platform bed", "SLEEP", HOME, 2.10, 1.62, 0.58,
      "platform_bed",
      note="Low platform, deep mattress, no headboard: the shell is the "
           "headboard.")

_prop("WARDROBE", "Wardrobe", "STORAGE", HOME, 0.62, 1.25, 2.05, "wardrobe",
      mount="wall",
      note="Two metres tall, so it only fits where the shell is still high.")
_prop("CURVED_SHELF", "Curved shelf run", "STORAGE", BOTH, 0.36, 1.80, 1.30,
      "curved_shelf", mount="wall",
      note="Follows the wall it is against instead of fighting it.")
_prop("STOCK_CRATE", "Stock crate", "STORAGE", STORE, 0.80, 0.60, 0.72,
      "stock_crate", note="Delivery, unopened, in everybody's way.")

_prop("KITCHEN_ISLAND", "Kitchen island", "KITCHEN", HOME, 1.80, 0.88,
      COUNTER, "island", note="The counter everyone leans on.")
_prop("GALLEY_RUN", "Galley run", "KITCHEN", HOME, 2.30, 0.66, COUNTER,
      "galley", mount="wall",
      note="Along the curve, with the tall units where the shell allows.")
_prop("TALL_FRIDGE", "Tall fridge", "KITCHEN", HOME, 0.72, 0.78, 1.90,
      "tall_unit", mount="wall",
      note="The tallest thing in a dome kitchen, and the first thing "
           "that will not fit against the wall.")

_prop("SOAK_TUB", "Soaking tub", "BATH", HOME, 1.72, 0.86, 0.96, "tub",
      note="Freestanding, under the shell, facing whatever the view is.")
_prop("VANITY", "Vanity and mirror", "BATH", HOME, 1.12, 0.52, 1.75,
      "vanity", mount="wall",
      note="Lit round the mirror, which is the only lighting that matters.")

_prop("FLOOR_LAMP", "Arc floor lamp", "LIGHT", BOTH, 0.44, 0.44, 1.85,
      "floor_lamp", note="Arcs out over the seating and lights the face.")
_prop("PENDANT_CLUSTER", "Pendant cluster", "LIGHT", BOTH, 0.90, 0.90, 0.70,
      "pendant", mount="ceiling",
      note="Hung off the shell, dropped to just above eye height.")
_prop("LIGHT_RING", "Light ring", "LIGHT", STORE, 1.60, 1.60, 0.20,
      "light_ring", mount="ceiling",
      note="A ring over the fitting area. Everything under it looks "
           "expensive.")
_prop("STRIP_UPLIGHT", "Strut uplight", "LIGHT", BOTH, 0.30, 0.30, 0.34,
      "uplight", note="Aimed up a strut, so the frame reads at night.")

_prop("PLANTER_TALL", "Tall planter", "GREEN", BOTH, 0.52, 0.52, 1.55,
      "planter", note="Big leaves, structural, doing the work of a wall.")
_prop("PLANT_LOW", "Low planter", "GREEN", BOTH, 0.46, 0.46, 0.55,
      "planter_low", note="Ground cover for the awkward gap by the door.")
_prop("HANGING_PLANT", "Hanging planter", "GREEN", HOME, 0.50, 0.50, 0.90,
      "hanging_plant", mount="ceiling",
      note="Off a strut, trailing, exactly where somebody will walk "
           "into it.")

_prop("RUG_ROUND", "Round rug", "DECOR", BOTH, 2.60, 2.60, 0.02, "rug",
      overlap=True,
      note="Defines the room the dome refuses to divide up.")
_prop("RUNWAY_STRIP", "Runway strip", "DECOR", STORE, 4.20, 1.20, 0.10,
      "runway", overlap=True,
      note="A raised lane through the floor. Somebody will use it.")
_prop("ARCH_MIRROR", "Arched mirror", "DECOR", BOTH, 0.16, 0.92, 1.90,
      "arch_mirror", mount="wall",
      note="Full length, leant on the curve, and permanently in use.")
_prop("NEON_SIGN", "Neon sign", "DECOR", STORE, 0.12, 1.60, 0.46,
      "neon_sign", mount="wall",
      note="One word, in her colour, high on the curve.")

_prop("SPIRAL_STAIR", "Spiral stair", "STRUCTURE", BOTH, 1.45, 1.45, 2.70,
      "spiral_stair",
      note="Up to the deck. Needs the crown, so it goes near the middle.")
_prop("MEZZANINE", "Mezzanine deck", "STRUCTURE", BOTH, 3.10, 2.20, 3.35,
      "mezzanine",
      note="A floor in the top half of the dome with a rail round it. "
           "The declared height is the top of the rail, not the deck, "
           "because the rail is what hits the shell first.")
_prop("WOOD_STOVE", "Stove and flue", "STRUCTURE", HOME, 0.62, 0.62, 2.20,
      "stove",
      note="The flue goes to the crown, so this piece wants the middle.")

_prop("RAIL_ROUND", "Round rail", "FIXTURE", STORE, 1.15, 1.15, 1.62,
      "rail_round", note="A circle of hanging clothes you walk around.")
_prop("RAIL_STRAIGHT", "Straight rail", "FIXTURE", STORE, 1.85, 0.62, 1.70,
      "rail_straight", note="A run of one size in eleven colours.")
_prop("FITTING_POD", "Fitting pod", "FIXTURE", STORE, 1.25, 1.25, 2.20,
      "fitting_pod",
      note="Curtained, lit from inside, and the tallest fixture on the "
           "floor.")
_prop("CASH_DESK", "Cash desk", "FIXTURE", STORE, 1.65, 0.72, COUNTER + 0.24,
      "cash_desk", note="The counter the whole argument happens across.")
_prop("STEAMER", "Garment steamer", "FIXTURE", STORE, 0.42, 0.42, 1.32,
      "steamer", note="On wheels, always hot, never where it should be.")

_prop("PLINTH", "Display plinth", "DISPLAY", STORE, 0.62, 0.62, 1.04,
      "plinth", note="One object on it. That is the whole idea.")
_prop("DRESS_FORM", "Dress form", "DISPLAY", STORE, 0.48, 0.42, 1.72,
      "dress_form",
      note="The shop's own silhouette on a stand, which is what the "
           "studio-form look is.")
_prop("SHOE_RISER", "Shoe risers", "DISPLAY", STORE, 1.20, 0.48, 0.80,
      "shoe_riser", note="Three steps of heels, tallest at the back.")
_prop("JEWEL_CASE", "Jewellery case", "DISPLAY", STORE, 1.10, 0.62, 1.02,
      "jewel_case", note="Lit, locked, and the reason there is a bench.")
_prop("MIRROR_TRIPLE", "Triple mirror", "DISPLAY", STORE, 0.55, 1.70, 2.00,
      "mirror_triple", mount="wall",
      note="Three panels, so she can see the back of the look.")

_prop("SCREEN", "Folding screen", "SERVICE", BOTH, 0.30, 1.60, 1.80,
      "screen", note="Divides a dome the only way a dome can be divided.")
_prop("SIDE_TABLE", "Side table", "SERVICE", BOTH, 0.44, 0.44, 0.56,
      "side_table", note="Holds one drink and one phone, face down.")


def props_for(set_id: str, category: str | None = None) -> tuple[Prop, ...]:
    return tuple(item for item in PROPS.values()
                 if set_id in item.sets
                 and (category is None or item.category == category))


def categories_for(set_id: str) -> tuple[str, ...]:
    present = {item.category for item in PROPS.values() if set_id in item.sets}
    return tuple(name for name in CATEGORIES if name in present)


def prop(prop_id: str) -> Prop:
    try:
        return PROPS[prop_id]
    except KeyError:
        raise ValueError(f"unknown prop {prop_id!r}; the catalogue has "
                         f"{len(PROPS)} pieces") from None


# ----------------------------------------------------------------------
# The builders
# ----------------------------------------------------------------------

def _palette(room: InteriorSet) -> dict[str, Colour]:
    return {
        "frame": (0.30, 0.28, 0.27, 1.0),
        "soft": (0.44, 0.40, 0.42, 1.0),
        "wood": (0.42, 0.29, 0.18, 1.0),
        "metal": (0.62, 0.64, 0.68, 1.0),
        "glass": (0.62, 0.78, 0.86, 0.34),
        "accent": room.accent,
        "warm": room.warm,
        "leaf": (0.22, 0.48, 0.28, 1.0),
        "pale": room.wall,
    }


def _b_sectional(batch, item, place, tone):
    back = item.height - item.seat_height
    place.box(batch, 0.0, 0.0, item.seat_height * 0.5, item.length,
              item.width, item.seat_height, tone["soft"])
    place.box(batch, -item.length * 0.36, 0.0,
              item.seat_height + back * 0.5, item.length * 0.28, item.width,
              back, tone["soft"])
    for across in (-item.width * 0.44, item.width * 0.44):
        place.box(batch, 0.0, across, item.seat_height + 0.10,
                  item.length, 0.12, 0.20, tone["frame"])


def _b_lounge_chair(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.seat_height, item.length * 0.9,
              item.width * 0.9, 0.16, tone["soft"])
    back = item.height - item.seat_height
    place.box(batch, -item.length * 0.38, 0.0,
              item.seat_height + back * 0.5, 0.14, item.width * 0.9,
              back, tone["soft"])
    place.legs(batch, item.length * 0.8, item.width * 0.8,
               item.seat_height, 0.026, tone["metal"])


def _b_daybed(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.72, item.length, item.width,
              0.22, tone["soft"])
    place.box(batch, 0.0, 0.0, item.height * 0.34, item.length * 0.94,
              item.width * 0.9, 0.28, tone["wood"])
    place.ball(batch, item.length * 0.40, 0.0, item.height * 0.92, 0.16,
               tone["accent"])


def _b_dining_chair(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.seat_height, item.length, item.width,
              0.07, tone["wood"])
    place.box(batch, -item.length * 0.44, 0.0,
              item.seat_height + 0.26, 0.07, item.width * 0.86, 0.50,
              tone["wood"])
    place.legs(batch, item.length, item.width, item.seat_height, 0.020,
               tone["frame"], inset=0.05)


def _b_bench(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height, item.length, item.width, 0.10,
              tone["soft"])
    place.legs(batch, item.length, item.width, item.height, 0.026,
               tone["metal"], inset=0.10)


def _b_stool(batch, item, place, tone):
    place.post(batch, 0.0, 0.0, 0.0, item.height, 0.040, tone["metal"])
    place.box(batch, 0.0, 0.0, item.height, item.length, item.width, 0.08,
              tone["wood"])
    for angle in range(0, 360, 90):
        radians = math.radians(angle)
        place.bar(batch,
                  (math.cos(radians) * 0.18, math.sin(radians) * 0.18, 0.22),
                  (0.0, 0.0, 0.22), 0.012, tone["metal"], 5)


def _b_round_table(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, item.height), item.length * 0.5,
               tone["wood"], 28)
    place.post(batch, 0.0, 0.0, item.height - 0.05, item.height, 0.20,
               tone["wood"], 24)
    place.post(batch, 0.0, 0.0, 0.02, item.height - 0.04, 0.07,
               tone["metal"])
    batch.disc(place.point(0.0, 0.0, 0.02), 0.26, tone["metal"], 20)


def _b_dining_table(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height - 0.03, item.length, item.width,
              0.06, tone["wood"])
    place.legs(batch, item.length, item.width, item.height - 0.06, 0.045,
               tone["frame"], inset=0.14)


def _b_desk(batch, item, place, tone):
    # The screen on it is what makes a desk as tall as it is, so the top
    # is worked back from the declared height rather than added to it.
    top = item.height - 0.26
    place.box(batch, 0.0, 0.0, top - 0.02, item.length, item.width,
              0.05, tone["wood"])
    place.legs(batch, item.length, item.width, top - 0.05, 0.030,
               tone["metal"], inset=0.10)
    place.box(batch, -item.length * 0.28, 0.0, top + 0.13, 0.06,
              0.42, 0.26, tone["frame"])


def _b_lookbook_table(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height - 0.03, item.length, item.width,
              0.06, tone["pale"])
    place.legs(batch, item.length, item.width, item.height - 0.06, 0.032,
               tone["metal"], inset=0.12)
    for index, along in enumerate((-0.42, 0.0, 0.42)):
        place.box(batch, along, 0.0, item.height + 0.05 + index * 0.005,
                  0.34, 0.34, 0.10,
                  tone["accent"] if index == 1 else tone["soft"])


def _b_bar_cart(batch, item, place, tone):
    # The bottles are the top of it.
    deck = item.height - 0.26
    for height in (deck * 0.38, deck):
        place.box(batch, 0.0, 0.0, height, item.length, item.width, 0.04,
                  tone["metal"])
    place.legs(batch, item.length, item.width, deck, 0.018,
               tone["accent"], inset=0.05)
    for along in (-0.20, 0.0, 0.22):
        place.post(batch, along, 0.0, deck + 0.02, item.height, 0.035,
                   tone["glass"], 7)


def _b_platform_bed(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, 0.14, item.length * 1.06, item.width * 1.06,
              0.26, tone["wood"])
    place.box(batch, 0.0, 0.0, 0.42, item.length, item.width, 0.28,
              tone["soft"])
    for across in (-item.width * 0.26, item.width * 0.26):
        place.box(batch, -item.length * 0.36, across, 0.60, 0.34, 0.52,
                  0.14, tone["pale"])


def _b_wardrobe(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["wood"])
    for across in (-item.width * 0.24, item.width * 0.24):
        place.post(batch, item.length * 0.52, across, item.height * 0.40,
                   item.height * 0.60, 0.020, tone["metal"], 6)


def _b_curved_shelf(batch, item, place, tone):
    for index in range(3):
        place.box(batch, 0.0, 0.0, 0.42 + index * 0.42, item.length,
                  item.width, 0.045, tone["wood"])
    for across in (-item.width * 0.46, item.width * 0.46):
        place.post(batch, 0.0, across, 0.0, item.height, 0.035,
                   tone["frame"], 6)


def _b_stock_crate(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["wood"])
    place.box(batch, 0.0, 0.0, item.height + 0.01, item.length * 0.5,
              item.width * 0.7, 0.01, tone["accent"])


def _b_island(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["frame"])
    place.box(batch, 0.0, 0.0, item.height + 0.02, item.length * 1.06,
              item.width * 1.10, 0.05, tone["pale"])
    place.box(batch, 0.10, 0.0, item.height + 0.06, 0.44, 0.34, 0.03,
              tone["metal"])


def _b_galley(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["frame"])
    place.box(batch, 0.0, 0.0, item.height + 0.02, item.length,
              item.width * 1.08, 0.05, tone["pale"])
    for along in (-item.length * 0.3, 0.0, item.length * 0.3):
        place.bar(batch, (along - 0.18, -item.width * 0.55, item.height * 0.72),
                  (along + 0.18, -item.width * 0.55, item.height * 0.72),
                  0.014, tone["metal"])


def _b_tall_unit(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["metal"])
    place.bar(batch, (item.length * 0.52, -0.10, item.height * 0.62),
              (item.length * 0.52, -0.10, item.height * 0.86), 0.016,
              tone["frame"])


def _b_tub(batch, item, place, tone):
    # The declared height is the top of the tap, which is the part that
    # would hit the shell first.
    rim = item.height - 0.34
    place.box(batch, 0.0, 0.0, rim * 0.5, item.length, item.width, rim,
              tone["pale"])
    place.box(batch, 0.0, 0.0, rim - 0.04, item.length * 0.88,
              item.width * 0.82, 0.06, tone["glass"])
    place.post(batch, -item.length * 0.52, 0.0, rim, item.height, 0.022,
               tone["metal"], 7)


def _b_vanity(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, 0.42, item.length, item.width, 0.84,
              tone["wood"])
    place.box(batch, 0.0, 0.0, 0.86, item.length * 1.04, item.width * 1.04,
              0.05, tone["pale"])
    place.box(batch, -item.length * 0.02, 0.0, 1.36, 0.04, item.width * 1.5,
              0.86, tone["glass"])
    for across in (-item.width * 0.8, item.width * 0.8):
        place.ball(batch, 0.0, across, 1.36, 0.055, tone["warm"])


def _b_floor_lamp(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, 0.015), 0.20, tone["metal"], 20)
    place.post(batch, 0.0, 0.0, 0.0, item.height * 0.92, 0.022,
               tone["metal"], 7)
    place.bar(batch, (0.0, 0.0, item.height * 0.92),
              (item.length * 1.4, 0.0, item.height), 0.020, tone["metal"])
    place.ball(batch, item.length * 1.5, 0.0, item.height - 0.06, 0.11,
               tone["warm"])


def _b_pendant(batch, item, place, tone):
    for index, (along, across) in enumerate(
            ((0.0, 0.0), (0.28, 0.18), (-0.24, -0.20))):
        drop = item.height * (0.6 + 0.2 * index)
        place.bar(batch, (along, across, 0.0), (along, across, -drop),
                  0.006, tone["frame"], 5)
        place.ball(batch, along, across, -drop - 0.08, 0.10, tone["warm"])


def _b_light_ring(batch, item, place, tone):
    radius = item.length * 0.5
    steps = 20
    for index in range(steps):
        one = math.tau * index / steps
        two = math.tau * (index + 1) / steps
        place.bar(batch,
                  (math.cos(one) * radius, math.sin(one) * radius, -0.20),
                  (math.cos(two) * radius, math.sin(two) * radius, -0.20),
                  0.035, tone["warm"], 5)
    for angle in (0.0, math.tau / 3.0, math.tau * 2.0 / 3.0):
        place.bar(batch,
                  (math.cos(angle) * radius, math.sin(angle) * radius, 0.0),
                  (math.cos(angle) * radius, math.sin(angle) * radius, -0.20),
                  0.006, tone["frame"], 4)


def _b_uplight(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.4, item.length, item.width,
              item.height * 0.8, tone["frame"])
    place.ball(batch, 0.0, 0.0, item.height, 0.07, tone["accent"])


def _b_planter(batch, item, place, tone):
    place.post(batch, 0.0, 0.0, 0.0, item.height * 0.32, item.length * 0.5,
               tone["frame"], 10)
    for index in range(7):
        angle = math.tau * index / 7 + 0.4
        lean = 0.22 + 0.05 * (index % 3)
        place.bar(batch, (0.0, 0.0, item.height * 0.32),
                  (math.cos(angle) * lean, math.sin(angle) * lean,
                   item.height * (0.72 + 0.05 * (index % 4))),
                  0.018, tone["leaf"], 5)
        place.ball(batch, math.cos(angle) * lean, math.sin(angle) * lean,
                   item.height * (0.74 + 0.05 * (index % 4)), 0.13,
                   tone["leaf"])


def _b_planter_low(batch, item, place, tone):
    place.post(batch, 0.0, 0.0, 0.0, item.height * 0.5, item.length * 0.5,
               tone["pale"], 10)
    for index in range(5):
        angle = math.tau * index / 5
        place.ball(batch, math.cos(angle) * 0.14, math.sin(angle) * 0.14,
                   item.height * 0.72, 0.14, tone["leaf"])


def _b_hanging_plant(batch, item, place, tone):
    place.bar(batch, (0.0, 0.0, 0.0), (0.0, 0.0, -item.height * 0.45),
              0.005, tone["frame"], 4)
    place.post(batch, 0.0, 0.0, -item.height * 0.62, -item.height * 0.45,
               0.16, tone["wood"], 10)
    for index in range(6):
        angle = math.tau * index / 6
        place.bar(batch, (0.0, 0.0, -item.height * 0.60),
                  (math.cos(angle) * 0.22, math.sin(angle) * 0.22,
                   -item.height * 0.98), 0.014, tone["leaf"], 4)


def _b_rug(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, item.height), item.length * 0.5,
               tone["accent"], 40)
    batch.disc(place.point(0.0, 0.0, item.height * 0.5), item.length * 0.42,
               tone["soft"], 36)


def _b_runway(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["pale"])
    place.box(batch, 0.0, 0.0, item.height + 0.005, item.length * 0.96,
              0.10, 0.01, tone["accent"])


def _b_arch_mirror(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["frame"])
    place.box(batch, item.length * 0.4, 0.0, item.height * 0.52,
              item.length * 0.3, item.width * 0.88, item.height * 0.90,
              tone["glass"])


def _b_neon_sign(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.5, item.length, item.width,
              item.height, tone["frame"])
    for index in range(5):
        across = (index / 4.0 - 0.5) * item.width * 0.82
        place.post(batch, item.length * 0.6, across, item.height * 0.22,
                   item.height * 0.80, 0.020, tone["accent"], 6)


def _b_spiral_stair(batch, item, place, tone):
    place.post(batch, 0.0, 0.0, 0.0, item.height, 0.075, tone["metal"], 10)
    steps = 12
    for index in range(steps):
        angle = math.tau * index / steps * 0.75
        height = item.height * (index + 1) / (steps + 1)
        reach = item.length * 0.42
        place.box(batch, math.cos(angle) * reach * 0.6,
                  math.sin(angle) * reach * 0.6, height,
                  reach, 0.28, 0.05, tone["wood"])
    place.bar(batch, (0.0, 0.0, item.height),
              (item.length * 0.4, 0.0, item.height), 0.03, tone["metal"])


def _b_mezzanine(batch, item, place, tone):
    # The declared height is the top of the rail; the deck sits a rail
    # below it, so the piece is exactly as tall as it says it is.
    deck = item.height - 0.90
    place.box(batch, 0.0, 0.0, deck, item.length, item.width, 0.14,
              tone["wood"])
    place.legs(batch, item.length, item.width, deck, 0.055,
               tone["metal"], inset=0.18)
    for across in (-item.width * 0.5, item.width * 0.5):
        place.box(batch, 0.0, across, deck + 0.45, item.length,
                  0.05, 0.90, tone["glass"])


def _b_stove(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, 0.36, item.length, item.width, 0.72,
              tone["frame"])
    place.box(batch, item.length * 0.42, 0.0, 0.42, 0.06, item.width * 0.6,
              0.32, tone["accent"])
    place.post(batch, 0.0, 0.0, 0.72, item.height, 0.075, tone["metal"], 8)


def _b_rail_round(batch, item, place, tone):
    radius = item.length * 0.5
    place.post(batch, 0.0, 0.0, 0.0, item.height, 0.030, tone["metal"], 8)
    steps = 18
    for index in range(steps):
        one = math.tau * index / steps
        two = math.tau * (index + 1) / steps
        place.bar(batch,
                  (math.cos(one) * radius, math.sin(one) * radius,
                   item.height),
                  (math.cos(two) * radius, math.sin(two) * radius,
                   item.height), 0.016, tone["metal"], 5)
    _hangers(batch, item, place, tone, radius, steps)


def _hangers(batch, item, place, tone, radius, steps):
    """Garments on a rail: separate, narrow, and not all the same colour.

    Drawn every other position and only a few centimetres thick, because
    a solid ring of boxes reads as a drum rather than as a rail with
    clothes on it.
    """
    shades = (tone["accent"], tone["soft"], tone["pale"], tone["wood"])
    for index in range(0, steps, 2):
        angle = math.tau * index / steps
        top = item.height - 0.08
        drop = 0.52 + 0.10 * (index % 3)
        place.box(batch, math.cos(angle) * radius, math.sin(angle) * radius,
                  top - drop * 0.5, 0.035, 0.26, drop,
                  shades[(index // 2) % len(shades)])


def _b_rail_straight(batch, item, place, tone):
    for along in (-item.length * 0.46, item.length * 0.46):
        place.post(batch, along, 0.0, 0.0, item.height, 0.028,
                   tone["metal"], 7)
    place.bar(batch, (-item.length * 0.46, 0.0, item.height),
              (item.length * 0.46, 0.0, item.height), 0.016, tone["metal"])
    shades = (tone["accent"], tone["soft"], tone["pale"], tone["wood"])
    count = 9
    for index in range(count):
        along = (index / (count - 1) - 0.5) * item.length * 0.84
        drop = 0.56 + 0.08 * (index % 3)
        place.box(batch, along, 0.0, item.height - 0.08 - drop * 0.5,
                  0.038, 0.28, drop, shades[index % len(shades)])


def _b_fitting_pod(batch, item, place, tone):
    radius = item.length * 0.5
    steps = 16
    for index in range(steps):
        one = math.tau * index / steps
        two = math.tau * (index + 1) / steps
        if 0.15 < (index / steps) < 0.35:
            continue
        place.bar(batch,
                  (math.cos(one) * radius, math.sin(one) * radius, 0.10),
                  (math.cos(two) * radius, math.sin(two) * radius, 0.10),
                  0.10, tone["pale"], 4)
        place.box(batch,
                  math.cos(one) * radius, math.sin(one) * radius,
                  item.height * 0.5, 0.06, 0.36, item.height * 0.86,
                  tone["pale"] if index % 2 else tone["accent"])
    batch.disc(place.point(0.0, 0.0, item.height), radius * 1.05,
               tone["frame"], 20)
    place.ball(batch, 0.0, 0.0, item.height - 0.16, 0.10, tone["warm"])


def _b_cash_desk(batch, item, place, tone):
    counter = item.height - 0.24
    place.box(batch, 0.0, 0.0, counter * 0.5, item.length, item.width,
              counter, tone["frame"])
    place.box(batch, 0.0, 0.0, counter + 0.02, item.length * 1.08,
              item.width * 1.14, 0.05, tone["pale"])
    place.box(batch, item.length * 0.24, 0.0, counter + 0.14, 0.20,
              0.26, 0.20, tone["metal"])
    place.box(batch, -item.length * 0.02, 0.0, counter * 0.5,
              item.length * 1.02, 0.03, counter * 0.6, tone["accent"])


def _b_steamer(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, 0.02), item.length * 0.5,
               tone["metal"], 16)
    place.post(batch, 0.0, 0.0, 0.02, item.height, 0.024, tone["metal"], 7)
    place.box(batch, 0.0, 0.0, 0.30, item.length * 0.8, item.width * 0.8,
              0.36, tone["pale"])
    place.bar(batch, (0.0, 0.0, item.height),
              (0.16, 0.0, item.height - 0.24), 0.020, tone["frame"])


def _b_plinth(batch, item, place, tone):
    # The declared height includes whatever is standing on it, because
    # that is the thing the dome has to clear.
    column = item.height - 0.12
    place.box(batch, 0.0, 0.0, column * 0.5, item.length, item.width,
              column, tone["pale"])
    place.box(batch, 0.0, 0.0, column + 0.06, item.length * 0.5,
              item.width * 0.5, 0.12, tone["accent"])


def _b_dress_form(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, 0.02), item.length * 0.5,
               tone["metal"], 18)
    place.post(batch, 0.0, 0.0, 0.02, item.height * 0.52, 0.026,
               tone["metal"], 7)
    for index in range(6):
        share = index / 5.0
        width = item.length * (0.46 - 0.12 * abs(share - 0.55) * 2.0)
        place.post(batch, 0.0, 0.0,
                   item.height * (0.52 + 0.08 * index),
                   item.height * (0.52 + 0.08 * (index + 1)),
                   max(0.06, width), tone["pale"], 12)
    place.post(batch, 0.0, 0.0, item.height * 1.00, item.height * 1.04,
               0.03, tone["metal"], 6)


def _b_shoe_riser(batch, item, place, tone):
    for index in range(3):
        height = item.height * (0.45 + index * 0.28)
        place.box(batch, -item.length * 0.30 + index * item.length * 0.30,
                  0.0, height * 0.5, item.length * 0.30, item.width,
                  height, tone["pale"])
        place.box(batch, -item.length * 0.30 + index * item.length * 0.30,
                  0.0, height + 0.05, 0.20, 0.10, 0.10, tone["accent"])


def _b_jewel_case(batch, item, place, tone):
    place.box(batch, 0.0, 0.0, item.height * 0.42, item.length, item.width,
              item.height * 0.84, tone["frame"])
    place.box(batch, 0.0, 0.0, item.height * 0.92, item.length * 0.98,
              item.width * 0.98, item.height * 0.18, tone["glass"])
    place.ball(batch, 0.0, 0.0, item.height * 0.88, 0.05, tone["warm"])


def _b_mirror_triple(batch, item, place, tone):
    for index, angle in enumerate((-32.0, 0.0, 32.0)):
        radians = math.radians(angle)
        across = (index - 1) * item.width * 0.34
        place.box(batch, math.sin(radians) * 0.16, across,
                  item.height * 0.5, 0.06, item.width * 0.34,
                  item.height, tone["glass"])
    place.box(batch, -0.10, 0.0, 0.06, item.length * 0.8, item.width,
              0.12, tone["frame"])


def _b_screen(batch, item, place, tone):
    for index in range(3):
        across = (index - 1) * item.width * 0.34
        lean = 0.10 * (1 if index % 2 else -1)
        place.box(batch, lean, across, item.height * 0.5, item.length,
                  item.width * 0.33, item.height, tone["wood"])


def _b_side_table(batch, item, place, tone):
    batch.disc(place.point(0.0, 0.0, item.height), item.length * 0.5,
               tone["metal"], 18)
    place.post(batch, 0.0, 0.0, 0.0, item.height, 0.022, tone["metal"], 7)
    batch.disc(place.point(0.0, 0.0, 0.015), item.length * 0.40,
               tone["metal"], 16)


BUILDERS: dict[str, Callable] = {
    "sectional": _b_sectional, "lounge_chair": _b_lounge_chair,
    "daybed": _b_daybed, "dining_chair": _b_dining_chair,
    "bench": _b_bench, "stool": _b_stool,
    "round_table": _b_round_table, "dining_table": _b_dining_table,
    "desk": _b_desk, "lookbook_table": _b_lookbook_table,
    "bar_cart": _b_bar_cart, "platform_bed": _b_platform_bed,
    "wardrobe": _b_wardrobe, "curved_shelf": _b_curved_shelf,
    "stock_crate": _b_stock_crate, "island": _b_island, "galley": _b_galley,
    "tall_unit": _b_tall_unit, "tub": _b_tub, "vanity": _b_vanity,
    "floor_lamp": _b_floor_lamp, "pendant": _b_pendant,
    "light_ring": _b_light_ring, "uplight": _b_uplight,
    "planter": _b_planter, "planter_low": _b_planter_low,
    "hanging_plant": _b_hanging_plant, "rug": _b_rug, "runway": _b_runway,
    "arch_mirror": _b_arch_mirror, "neon_sign": _b_neon_sign,
    "spiral_stair": _b_spiral_stair, "mezzanine": _b_mezzanine,
    "stove": _b_stove, "rail_round": _b_rail_round,
    "rail_straight": _b_rail_straight, "fitting_pod": _b_fitting_pod,
    "cash_desk": _b_cash_desk, "steamer": _b_steamer, "plinth": _b_plinth,
    "dress_form": _b_dress_form, "shoe_riser": _b_shoe_riser,
    "jewel_case": _b_jewel_case, "mirror_triple": _b_mirror_triple,
    "screen": _b_screen, "side_table": _b_side_table,
}


def draw_prop(
    batch,
    item: Prop,
    room: InteriorSet,
    x: float,
    y: float,
    yaw_deg: float,
    lift: float = 0.0,
    tint: Colour | None = None,
) -> None:
    """Draw one prop where it stands.

    A ceiling-mounted piece hangs from the shell above the spot rather
    than standing on the floor, and works out where that is by asking
    the shell -- so a pendant over the middle of the dome hangs from the
    crown and one near the wall hangs from where the wall actually is.
    """
    base = lift
    if item.mount == "ceiling":
        base = shell_clearance(x, y, room.radius_m) - lift
    place = Placer(x, y, base, yaw_deg)
    tone = _palette(room)
    if tint is not None:
        tone = dict(tone, accent=tint)
    BUILDERS[item.builder](batch, item, place, tone)


# ----------------------------------------------------------------------
# The room itself
# ----------------------------------------------------------------------

def draw_room(
    opaque,
    transparent,
    room: InteriorSet,
    *,
    panels: bool = True,
) -> None:
    """Floor, base ring, struts and a translucent skin.

    Everything is taken off the same hemisphere the rest of the package
    draws, at set scale, so the ceiling the composer measures against is
    the ceiling on screen.
    """
    radius = room.radius_m
    vertices = np.asarray(GEOMETRY.vertices, dtype=float) * radius
    opaque.disc(np.array([0.0, 0.0, 0.0]), radius * 1.02, room.floor, 64)
    inner = tuple(channel * 0.94 for channel in room.floor[:3]) + (1.0,)
    opaque.disc(np.array([0.0, 0.0, 0.003]), radius * 0.62, inner, 56)
    strut = max(0.030, radius * 0.0085)
    for edge in GEOMETRY.hemisphere_edges:
        opaque.cylinder(vertices[edge[0]], vertices[edge[1]], strut,
                        room.wall, 6)
    for index in set(sum(([int(a), int(b)]
                          for a, b in GEOMETRY.hemisphere_edges), [])):
        opaque.sphere(vertices[index], strut * 1.5, room.accent, 3, 6)
    if panels:
        skin = (room.wall[0], room.wall[1], room.wall[2], 0.13)
        for face in GEOMETRY.hemisphere_faces:
            a, b, c = (vertices[int(index)] for index in face)
            transparent.triangle(a, b, c, skin)
            transparent.triangle(a, c, b, skin)


def room_report(set_id: str) -> str:
    room = interior_set(set_id)
    lines = [f"{room.label.upper()}  --  {room.radius_m * 2:.1f} m across, "
             f"{room.radius_m:.1f} m to the crown", "", room.note, ""]
    for category in categories_for(set_id):
        lines.append(category)
        for item in props_for(set_id, category):
            lines.append(
                f"    {item.label:<22} "
                f"{item.length:.2f} x {item.width:.2f} x {item.height:.2f} m"
                + (f", seats {item.seats}" if item.seats else "")
                + (f", {item.mount}" if item.mount != "floor" else ""))
    lines.append("")
    lines.append(f"seat height {SEAT:.3f} m, table {TABLE:.3f} m, "
                 f"counter {COUNTER:.3f} m -- all derived from the seated "
                 f"pose, none of them typed in")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_dome_interiors() -> None:
    """Prove the ceiling, the catalogue and every builder."""
    room = interior_set("DOME_STORE")
    radius = room.radius_m

    # The base ring is a polygon, and the floor runs out short of the
    # circle in the direction of a strut.
    assert BASE_RING_SIDES >= 6, BASE_RING_SIDES
    apothem = base_ring_apothem(radius)
    assert apothem < radius, (apothem, radius)
    # Everything inside the apothem has dome over it, whichever way you
    # walk; somewhere between the apothem and the circle there is none.
    for turn in range(24):
        angle = math.tau * turn / 24
        assert shell_clearance(apothem * 0.97 * math.cos(angle),
                               apothem * 0.97 * math.sin(angle),
                               radius) > 0.0, angle
    ring_gaps = [shell_clearance(radius * 0.998 * math.cos(math.tau * turn / 60),
                                 radius * 0.998 * math.sin(math.tau * turn / 60),
                                 radius)
                 for turn in range(60)]
    assert min(ring_gaps) == 0.0, min(ring_gaps)

    # The crown is the crown, and the yard has no ceiling at all.
    assert abs(shell_clearance(0.0, 0.0, radius) - radius) < 1e-6
    assert shell_clearance(radius * 1.4, 0.0, radius) == 0.0
    # Clearance falls off as you walk out.
    heights = [shell_clearance(step * radius * 0.18, 0.0, radius)
               for step in range(5)]
    for first, second in zip(heights, heights[1:]):
        assert second < first, heights

    # The faceted ceiling is never higher than the sphere it is
    # inscribed in, and somewhere it is meaningfully lower -- which is
    # the whole reason the composer measures against facets.
    gaps = []
    for step in range(1, 40):
        reach = radius * step / 40.0
        for turn in range(7):
            angle = math.tau * turn / 7.0
            x, y = reach * math.cos(angle), reach * math.sin(angle)
            faceted = shell_clearance(x, y, radius)
            round_shell = sphere_clearance(x, y, radius)
            assert faceted <= round_shell + 1e-6, (x, y, faceted, round_shell)
            gaps.append(round_shell - faceted)
    assert max(gaps) > 0.10, max(gaps)

    # Scaling the set scales the ceiling exactly.
    assert abs(shell_clearance(1.0, 0.0, 8.0)
               - 2.0 * shell_clearance(0.5, 0.0, 4.0)) < 1e-6

    # Heights derived from the seated pose, not typed in.
    from .glam_figure import seat_height
    assert abs(SEAT - seat_height(1.70)) < 1e-3
    assert TABLE > SEAT and COUNTER > TABLE

    # The catalogue holds together.
    assert len(PROPS) >= 40, len(PROPS)
    for item in PROPS.values():
        assert item.category in CATEGORIES, item.prop_id
        assert item.builder in BUILDERS, item.prop_id
        assert item.sets and set(item.sets) <= set(DOME_SETS), item.prop_id
        assert item.mount in ("floor", "wall", "ceiling"), item.prop_id
        assert 0.05 < item.length < 5.0, item.prop_id
        assert 0.05 < item.width < 5.0, item.prop_id
        assert 0.01 < item.height < 3.6, item.prop_id
        assert item.note.endswith("."), item.prop_id
        if item.seats:
            assert 0.30 < item.seat_height < 0.90, item.prop_id
    # Both rooms are furnishable and neither is a subset of the other.
    for set_id in DOME_SETS:
        assert len(props_for(set_id)) >= 20, set_id
        assert len(categories_for(set_id)) >= 8, set_id
    assert props_for("DOME_HOME") != props_for("DOME_STORE")

    # Every builder draws, inside its own declared footprint and height.
    for item in PROPS.values():
        batch = TriangleBatch()
        draw_prop(batch, item, room, 1.5, -0.5, 37.0)
        assert batch.vertices, item.prop_id
        points = np.asarray(batch.vertices, dtype=float).reshape(-1, 10)[:, :3]
        span = np.linalg.norm(points[:, :2] - np.array([1.5, -0.5]),
                              axis=1).max()
        # An arc lamp reaches past its base; everything else stays over
        # its own footprint, with a little slack for a leaning mirror.
        allowance = item.diagonal * 0.5 + (0.9 if item.builder == "floor_lamp"
                                           else 0.30)
        assert span < allowance, (item.prop_id, span, allowance)
        if item.mount == "ceiling":
            assert points[:, 2].min() > 0.9, item.prop_id
            assert points[:, 2].max() <= shell_clearance(
                1.5, -0.5, radius) + 1e-6, item.prop_id
        else:
            assert points[:, 2].min() > -0.02, (item.prop_id,
                                                points[:, 2].min())
            # A prop is as tall as it declares, because that is the
            # number the composer measures against the shell.  Anything
            # that quietly draws taller would go through the roof.
            assert abs(float(points[:, 2].max()) - item.height) < 0.12, (
                item.prop_id, points[:, 2].max(), item.height)

    # Rotation turns a piece rather than smearing it: the footprint of a
    # box at 37 degrees is the same size as at zero.
    def extent(yaw):
        batch = TriangleBatch()
        draw_prop(batch, PROPS["DINING_TABLE"], room, 0.0, 0.0, yaw)
        points = np.asarray(batch.vertices, dtype=float).reshape(-1, 10)[:, :3]
        return float(np.linalg.norm(points[:, :2], axis=1).max())
    assert abs(extent(0.0) - extent(37.0)) < 1e-6, (extent(0.0), extent(37.0))
    assert abs(extent(0.0) - extent(90.0)) < 1e-6

    # The room draws, and nothing in it escapes the shell.
    opaque = TriangleBatch()
    clear = TriangleBatch()
    draw_room(opaque, clear, room)
    assert opaque.vertices and clear.vertices
    shell = np.asarray(opaque.vertices, dtype=float).reshape(-1, 10)[:, :3]
    assert shell[:, 2].max() < radius + 0.12, shell[:, 2].max()
    assert np.linalg.norm(shell[:, :2], axis=1).max() < radius * 1.06

    try:
        interior_set("DOME_YACHT")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown set has to be refused")
    try:
        prop("HOT_TUB_TIME_MACHINE")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown prop has to be refused")


if __name__ == "__main__":
    validate_dome_interiors()
    print(room_report("DOME_STORE"))
