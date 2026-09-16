"""Build-a-dome: cycle a piece, turn it, drop it, and the dome argues back.

This is the park editor from a skateboarding game, pointed at a
geodesic room.  You hold one piece at a time.  Two keys walk the
category, two more walk the pieces inside it, one turns the piece on the
spot, one drops it.  Pick a placed piece back up, move it, put it down
again.  Undo goes back through all of it.

What makes it a dome editor rather than a grid editor
-----------------------------------------------------
**The ceiling is not flat, so the piece that fits here does not fit
there.**  Every candidate is measured against
:func:`two_v_demo.dome_interiors.shell_clearance` at the four corners of
its own rotated footprint, and the tightest corner decides.  A wardrobe
goes in the middle of a small dome and nowhere near the wall; the same
wardrobe goes almost anywhere in a big one.  Nothing in the catalogue
carries a list of legal spots -- turn the piece and the answer changes,
because the geometry changed.

**A refusal always says why.**  :class:`Verdict` carries reasons in
plain words -- "the shell is 1.42 m here and this is 2.05 m tall" -- so
the editor can print the actual constraint rather than beep.

**People are pieces.**  The cast is one more category.  A woman is
placed, turned and cycled exactly like a chair, with extra cycles for
what she is wearing, how she is standing and how her hair is done.  A
seated pose is refused unless there is something under her to sit on,
and the seat has to be the right height, which is checked against the
seat the pose itself produces.

Everything here is data and arithmetic.  Nothing in this module draws or
touches a window; :mod:`two_v_demo.composer_app` does that, and
:func:`draw_scene` turns a finished scene into geometry for anything
that wants to render one.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .dome_interiors import (
    BASE_RING_SIDES,
    DOME_SETS,
    InteriorSet,
    Prop,
    categories_for,
    draw_prop,
    draw_room,
    base_ring_apothem,
    interior_set,
    prop,
    props_for,
    shell_clearance,
)
from .glam_cast import GLAM_CAST, MODE_LABEL, WARDROBE_MODES, cast_ids
from .glam_figure import (
    GLAM_POSES,
    Look,
    POSE_ORDER,
    SEAT_POSES,
    draw_look,
    seat_height,
)
from .glam_hair import STYLE_ORDER


SCHEMA = "domesim.scene/1"

GRID_M = 0.25
"""How far one nudge moves a piece.  A quarter metre is coarse enough to
line things up by feel and fine enough to get a sofa off a rug."""

YAW_STEP_DEG = 15.0
FINE_YAW_STEP_DEG = 5.0
LIFT_STEP_M = 0.10

WALL_BAND_M = 1.30
"""How close to the base ring a wall-mounted piece has to sit."""

HEAD_CLEARANCE_M = 2.05
"""What has to be left under a hanging piece for people to walk beneath."""

MAX_PIECES = 90
MAX_FLOOR_SHARE = 0.55
"""Fraction of the floor that may be covered before the room stops being
a room.  Rugs and runway strips do not count -- you walk on those."""

CAST_CATEGORY = "CAST"
CAST_FOOTPRINT = (0.62, 0.52)
"""How much floor a standing woman occupies, near enough to keep the
furniture off her.  Shoulder breadth by depth, rounded up for hair."""


# ----------------------------------------------------------------------
# What is in the room
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Placement:
    """One thing, somewhere, facing some way."""

    kind: str
    """``PROP`` or ``CAST``."""
    ref: str
    """A prop id, or a character id."""
    x: float
    y: float
    yaw_deg: float = 0.0
    lift_m: float = 0.0
    """Extra height, for a hanging piece dropped lower than its default."""
    mode: str = "STREET"
    pose_key: str = ""
    hair_style: str = ""

    def footprint(self) -> tuple[float, float]:
        if self.kind == "CAST":
            return CAST_FOOTPRINT
        item = prop(self.ref)
        return item.length, item.width

    def height(self) -> float:
        if self.kind == "CAST":
            who = GLAM_CAST[self.ref]
            return who.stature_m + who.heel_pref_m + 0.20
        return prop(self.ref).height

    def label(self) -> str:
        if self.kind == "CAST":
            who = GLAM_CAST[self.ref]
            return f"{who.name} ({MODE_LABEL[self.mode]})"
        return prop(self.ref).label

    def overlappable(self) -> bool:
        return self.kind == "PROP" and prop(self.ref).overlap

    def mount(self) -> str:
        return "floor" if self.kind == "CAST" else prop(self.ref).mount

    def to_dict(self) -> dict:
        data = {"kind": self.kind, "ref": self.ref,
                "x": round(self.x, 4), "y": round(self.y, 4),
                "yaw_deg": round(self.yaw_deg, 3)}
        if self.lift_m:
            data["lift_m"] = round(self.lift_m, 4)
        if self.kind == "CAST":
            data["mode"] = self.mode
            if self.pose_key:
                data["pose_key"] = self.pose_key
            if self.hair_style:
                data["hair_style"] = self.hair_style
        return data

    @staticmethod
    def from_dict(data: dict) -> "Placement":
        return Placement(
            kind=str(data["kind"]),
            ref=str(data["ref"]),
            x=float(data["x"]),
            y=float(data["y"]),
            yaw_deg=float(data.get("yaw_deg", 0.0)),
            lift_m=float(data.get("lift_m", 0.0)),
            mode=str(data.get("mode", "STREET")),
            pose_key=str(data.get("pose_key", "")),
            hair_style=str(data.get("hair_style", "")),
        )


@dataclass(frozen=True)
class Scene:
    """A furnished dome."""

    set_id: str
    name: str = "untitled"
    placements: tuple[Placement, ...] = ()

    def room(self) -> InteriorSet:
        return interior_set(self.set_id)

    def with_placements(self, placements: Iterable[Placement]) -> "Scene":
        return replace(self, placements=tuple(placements))

    def to_dict(self) -> dict:
        return {"schema": SCHEMA, "set_id": self.set_id, "name": self.name,
                "placements": [item.to_dict() for item in self.placements]}

    @staticmethod
    def from_dict(data: dict) -> "Scene":
        schema = data.get("schema")
        if schema != SCHEMA:
            raise ValueError(f"not a dome scene: schema {schema!r}, "
                             f"expected {SCHEMA!r}")
        set_id = str(data["set_id"])
        if set_id not in DOME_SETS:
            raise ValueError(f"scene names an unknown set {set_id!r}")
        return Scene(set_id=set_id, name=str(data.get("name", "untitled")),
                     placements=tuple(Placement.from_dict(item)
                                      for item in data["placements"]))

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @staticmethod
    def load(path: Path) -> "Scene":
        return Scene.from_dict(json.loads(Path(path).read_text(
            encoding="utf-8")))


# ----------------------------------------------------------------------
# Does it fit?
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    """Whether a piece can go here, and if not, what stopped it."""

    ok: bool
    reasons: tuple[str, ...] = ()
    clearance_m: float = 0.0

    @property
    def why(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "fits"


def corners(x: float, y: float, yaw_deg: float,
            length: float, width: float) -> np.ndarray:
    """The four corners of a rotated footprint, anticlockwise."""
    angle = math.radians(yaw_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    half_l, half_w = length * 0.5, width * 0.5
    out = np.empty((4, 2))
    for index, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        along, across = sx * half_l, sy * half_w
        out[index] = (x + along * cos - across * sin,
                      y + along * sin + across * cos)
    return out


def _axes(rect: np.ndarray) -> list[np.ndarray]:
    edges = [rect[(index + 1) % 4] - rect[index] for index in range(2)]
    return [np.array([-edge[1], edge[0]]) / max(1e-9, np.linalg.norm(edge))
            for edge in edges]


def rectangles_overlap(one: np.ndarray, two: np.ndarray,
                       slack: float = 0.02) -> bool:
    """Separating-axis test between two rotated footprints.

    ``slack`` lets two pieces touch along an edge without being called a
    collision, which is what you want when you push a chair up against
    a table.
    """
    for axis in _axes(one) + _axes(two):
        first = one @ axis
        second = two @ axis
        if first.max() - slack <= second.min() or \
                second.max() - slack <= first.min():
            return False
    return True


def footprint_clearance(placement: Placement, radius_m: float) -> float:
    """The tightest headroom over any corner of a placed footprint.

    A piece is as tall at its corners as it is in the middle, and it is
    the corners that reach out towards the wall, so this is the number
    that decides whether it fits.
    """
    length, width = placement.footprint()
    points = corners(placement.x, placement.y, placement.yaw_deg,
                     length, width)
    heights = [shell_clearance(float(point[0]), float(point[1]), radius_m)
               for point in points]
    heights.append(shell_clearance(placement.x, placement.y, radius_m))
    return min(heights)


def _distance_to_ring(placement: Placement, radius_m: float) -> float:
    """How far the far edge of a footprint is from the base ring."""
    length, width = placement.footprint()
    points = corners(placement.x, placement.y, placement.yaw_deg,
                     length, width)
    return radius_m - float(np.linalg.norm(points, axis=1).max())


def seat_under(placement: Placement,
               placements: Sequence[Placement]) -> Placement | None:
    """The seat a figure is sitting on, if she is over one.

    A seated pose has a hip height, and a sofa has a seat height; this
    finds a placed seat whose footprint she is standing in and whose
    seat is within a hand's width of where her hips would land.
    """
    who = GLAM_CAST[placement.ref]
    wanted = seat_height(who.stature_m)
    for other in placements:
        if other.kind != "PROP":
            continue
        item = prop(other.ref)
        if not item.seats:
            continue
        rect = corners(other.x, other.y, other.yaw_deg,
                       item.length, item.width)
        here = np.array([[placement.x, placement.y]])
        inside = rectangles_overlap(rect, corners(placement.x, placement.y,
                                                  0.0, 0.30, 0.30))
        del here
        if inside and abs(item.seat_height - wanted) < 0.14:
            return other
    return None


def is_seat_for(seat: Placement, sitter: Placement) -> bool:
    """Whether ``sitter`` is a seated figure sitting on ``seat``."""
    if sitter.kind != "CAST" or seat.kind != "PROP":
        return False
    pose_key = sitter.pose_key or GLAM_CAST[sitter.ref].default_pose
    if pose_key not in SEAT_POSES:
        return False
    return seat_under(sitter, (seat,)) is seat


def check(scene: Scene, placement: Placement,
          ignore_index: int | None = None) -> Verdict:
    """Everything that could stop this piece going here, in one pass."""
    room = scene.room()
    radius = room.radius_m
    reasons: list[str] = []

    length, width = placement.footprint()
    rect = corners(placement.x, placement.y, placement.yaw_deg, length, width)
    clearance = footprint_clearance(placement, radius)
    mount = placement.mount()

    if clearance <= 0.0:
        # No dome overhead means a corner has left the building.  Say so
        # in those terms rather than reporting nought metres of headroom,
        # which reads like a bug: the base ring is a polygon inscribed in
        # the circle, so the floor runs out short of the edge between
        # every pair of ground nodes.
        short = radius - base_ring_apothem(radius)
        reasons.append(
            f"that reaches outside the dome -- the base ring is a "
            f"{BASE_RING_SIDES}-sided polygon, so between struts the "
            f"building stops {short:.2f} m inside the circle")
    elif mount == "ceiling":
        drop = placement.height() + placement.lift_m
        if clearance - drop < HEAD_CLEARANCE_M:
            reasons.append(
                f"hung here it would leave {max(0.0, clearance - drop):.2f} m "
                f"to walk under, and {HEAD_CLEARANCE_M:.2f} m is the minimum")
    else:
        total = placement.height() + placement.lift_m
        if total > clearance:
            reasons.append(
                f"the shell is {clearance:.2f} m here and this is "
                f"{total:.2f} m tall")

    if mount == "wall":
        gap = _distance_to_ring(placement, radius)
        if gap > WALL_BAND_M:
            reasons.append(
                f"it wants the curve behind it and is {gap:.2f} m off the "
                f"wall, which is more than {WALL_BAND_M:.2f} m")

    if placement.kind == "CAST":
        pose_key = placement.pose_key or GLAM_CAST[placement.ref].default_pose
        if pose_key in SEAT_POSES:
            others = [item for index, item in enumerate(scene.placements)
                      if index != ignore_index]
            if seat_under(placement, others) is None:
                reasons.append("she is sitting down and there is nothing "
                               "under her")

    if not placement.overlappable():
        for index, other in enumerate(scene.placements):
            if index == ignore_index or other.overlappable():
                continue
            # A woman sitting down is standing in her own chair, which is
            # the point of a chair.  The exemption runs both ways: it has
            # to hold whether the thing being checked is the sitter or
            # the seat, or a finished room fails a re-check it passed
            # when it was built.
            if is_seat_for(other, placement) or is_seat_for(placement, other):
                continue
            if (other.mount() == "ceiling") != (mount == "ceiling"):
                continue
            other_length, other_width = other.footprint()
            if rectangles_overlap(rect, corners(other.x, other.y,
                                                other.yaw_deg,
                                                other_length, other_width)):
                reasons.append(f"it is standing in the {other.label()}")
                break

    count = len(scene.placements) + (1 if ignore_index is None else 0)
    if count > MAX_PIECES:
        reasons.append(f"the room is full at {MAX_PIECES} pieces")

    share = floor_share(scene, extra=placement, ignore_index=ignore_index)
    if share > MAX_FLOOR_SHARE:
        reasons.append(f"that would cover {share * 100:.0f}% of the floor, "
                       f"and {MAX_FLOOR_SHARE * 100:.0f}% is the limit")

    return Verdict(not reasons, tuple(reasons), clearance)


def floor_share(scene: Scene, extra: Placement | None = None,
                ignore_index: int | None = None) -> float:
    """How much of the floor is covered, as a fraction.

    Rugs, runway strips and hanging pieces do not count: you walk on the
    first two and under the third.
    """
    room = scene.room()
    area = math.pi * room.radius_m ** 2
    used = 0.0
    items = [item for index, item in enumerate(scene.placements)
             if index != ignore_index]
    if extra is not None:
        items.append(extra)
    for item in items:
        if item.overlappable() or item.mount() == "ceiling":
            continue
        length, width = item.footprint()
        used += length * width
    return used / area


# ----------------------------------------------------------------------
# The palette
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PaletteEntry:
    """One thing you can be holding."""

    kind: str
    ref: str
    label: str
    detail: str


def palette(set_id: str) -> dict[str, tuple[PaletteEntry, ...]]:
    """Everything placeable in a set, grouped the way it is cycled."""
    groups: dict[str, tuple[PaletteEntry, ...]] = {}
    for category in categories_for(set_id):
        entries = []
        for item in props_for(set_id, category):
            entries.append(PaletteEntry(
                "PROP", item.prop_id, item.label,
                f"{item.length:.2f} x {item.width:.2f} x {item.height:.2f} m"
                + (f", {item.mount}" if item.mount != "floor" else "")))
        groups[category] = tuple(entries)
    groups[CAST_CATEGORY] = tuple(
        PaletteEntry("CAST", character_id, GLAM_CAST[character_id].name,
                     GLAM_CAST[character_id].archetype)
        for character_id in cast_ids())
    return groups


# ----------------------------------------------------------------------
# The editor's state machine
# ----------------------------------------------------------------------

@dataclass
class Composer:
    """Holding one piece over a dome, with an undo stack behind you."""

    scene: Scene
    category_index: int = 0
    piece_index: int = 0
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    cursor_yaw: float = 0.0
    cursor_lift: float = 0.0
    mode_index: int = 0
    pose_index: int = 0
    hair_index: int = -1
    """-1 means her own hair, which is the sensible default."""
    carrying: int | None = None
    """Index of a placed piece picked back up, or ``None``."""
    grid: float = GRID_M
    history: list[Scene] = field(default_factory=list)
    future: list[Scene] = field(default_factory=list)
    message: str = "Pick a piece and drop it."

    # -- palette ------------------------------------------------------

    def groups(self) -> dict[str, tuple[PaletteEntry, ...]]:
        return palette(self.scene.set_id)

    def category(self) -> str:
        names = tuple(self.groups())
        return names[self.category_index % len(names)]

    def entries(self) -> tuple[PaletteEntry, ...]:
        return self.groups()[self.category()]

    def entry(self) -> PaletteEntry:
        items = self.entries()
        return items[self.piece_index % len(items)]

    def cycle_category(self, step: int = 1) -> None:
        names = tuple(self.groups())
        self.category_index = (self.category_index + step) % len(names)
        self.piece_index = 0
        self.cursor_lift = 0.0
        self.message = f"{self.category().title()}: {self.entry().label}"

    def cycle_piece(self, step: int = 1) -> None:
        items = self.entries()
        self.piece_index = (self.piece_index + step) % len(items)
        self.cursor_lift = 0.0
        self.message = f"{self.entry().label} -- {self.entry().detail}"

    def cycle_mode(self, step: int = 1) -> None:
        self.mode_index = (self.mode_index + step) % len(WARDROBE_MODES)
        self.message = f"Wearing: {MODE_LABEL[self.mode()]}"

    def cycle_pose(self, step: int = 1) -> None:
        self.pose_index = (self.pose_index + step) % (len(POSE_ORDER) + 1)
        self.message = ("Pose: her own" if self.pose_index == 0
                        else f"Pose: {self.pose().replace('_', ' ')}")

    def cycle_hair(self, step: int = 1) -> None:
        self.hair_index = ((self.hair_index + 1 + step)
                           % (len(STYLE_ORDER) + 1)) - 1
        self.message = ("Hair: her own" if self.hair_index < 0
                        else f"Hair: {STYLE_ORDER[self.hair_index]}")

    def mode(self) -> str:
        return WARDROBE_MODES[self.mode_index]

    def pose(self) -> str:
        return "" if self.pose_index == 0 else POSE_ORDER[self.pose_index - 1]

    def hair(self) -> str:
        return "" if self.hair_index < 0 else STYLE_ORDER[self.hair_index]

    # -- the cursor ---------------------------------------------------

    def ghost(self) -> Placement:
        """The piece as it would be placed right now."""
        entry = self.entry()
        return Placement(
            kind=entry.kind, ref=entry.ref,
            x=self.cursor_x, y=self.cursor_y, yaw_deg=self.cursor_yaw,
            lift_m=self.cursor_lift,
            mode=self.mode(), pose_key=self.pose(), hair_style=self.hair())

    def verdict(self) -> Verdict:
        return check(self.scene, self.ghost(), ignore_index=self.carrying)

    def nudge(self, along: float, across: float, snap: bool = True) -> None:
        self.cursor_x += along * self.grid
        self.cursor_y += across * self.grid
        if snap:
            self.cursor_x = round(self.cursor_x / self.grid) * self.grid
            self.cursor_y = round(self.cursor_y / self.grid) * self.grid

    def move_to(self, x: float, y: float, snap: bool = True) -> None:
        if snap:
            x = round(x / self.grid) * self.grid
            y = round(y / self.grid) * self.grid
        self.cursor_x, self.cursor_y = float(x), float(y)

    def turn(self, steps: int = 1, fine: bool = False) -> None:
        step = FINE_YAW_STEP_DEG if fine else YAW_STEP_DEG
        self.cursor_yaw = (self.cursor_yaw + steps * step) % 360.0

    def raise_by(self, steps: int = 1) -> None:
        self.cursor_lift = max(0.0, self.cursor_lift + steps * LIFT_STEP_M)

    def face_centre(self) -> None:
        """Point the held piece back at the middle of the room."""
        if abs(self.cursor_x) < 1e-9 and abs(self.cursor_y) < 1e-9:
            return
        self.cursor_yaw = math.degrees(
            math.atan2(-self.cursor_y, -self.cursor_x)) % 360.0

    # -- editing ------------------------------------------------------

    def _remember(self) -> None:
        self.history.append(self.scene)
        self.future.clear()

    def place(self) -> Verdict:
        """Drop the held piece, if it fits."""
        candidate = self.ghost()
        result = check(self.scene, candidate, ignore_index=self.carrying)
        if not result.ok:
            self.message = result.why
            return result
        self._remember()
        placements = list(self.scene.placements)
        if self.carrying is not None:
            placements[self.carrying] = candidate
            self.carrying = None
            self.message = f"Moved the {candidate.label()}."
        else:
            placements.append(candidate)
            self.message = f"Placed the {candidate.label()}."
        self.scene = self.scene.with_placements(placements)
        return result

    def hover(self, x: float, y: float) -> int | None:
        """Which placed piece is under a point, topmost-first."""
        probe = corners(x, y, 0.0, 0.02, 0.02)
        found = None
        for index, item in enumerate(self.scene.placements):
            length, width = item.footprint()
            if rectangles_overlap(probe, corners(item.x, item.y, item.yaw_deg,
                                                 length, width), slack=0.0):
                if found is None or not item.overlappable():
                    found = index
        return found

    def pick_up(self, index: int | None = None) -> bool:
        """Take a placed piece back into the cursor."""
        if index is None:
            index = self.hover(self.cursor_x, self.cursor_y)
        if index is None:
            self.message = "Nothing there to pick up."
            return False
        item = self.scene.placements[index]
        groups = self.groups()
        for category_index, (name, entries) in enumerate(groups.items()):
            for piece_index, entry in enumerate(entries):
                if entry.kind == item.kind and entry.ref == item.ref:
                    self.category_index = category_index
                    self.piece_index = piece_index
                    del name
        self.cursor_x, self.cursor_y = item.x, item.y
        self.cursor_yaw, self.cursor_lift = item.yaw_deg, item.lift_m
        if item.kind == "CAST":
            self.mode_index = WARDROBE_MODES.index(item.mode)
            self.pose_index = (0 if not item.pose_key
                               else POSE_ORDER.index(item.pose_key) + 1)
            self.hair_index = (-1 if not item.hair_style
                               else STYLE_ORDER.index(item.hair_style))
        self.carrying = index
        self.message = f"Holding the {item.label()}."
        return True

    def drop_held(self) -> None:
        """Put a picked-up piece back where it was and stop carrying it."""
        self.carrying = None
        self.message = "Let it go."

    def remove(self, index: int | None = None) -> bool:
        if index is None:
            index = self.hover(self.cursor_x, self.cursor_y)
        if index is None:
            self.message = "Nothing there to remove."
            return False
        self._remember()
        item = self.scene.placements[index]
        placements = list(self.scene.placements)
        del placements[index]
        self.scene = self.scene.with_placements(placements)
        if self.carrying is not None:
            self.carrying = None
        self.message = f"Removed the {item.label()}."
        return True

    def clear(self) -> None:
        self._remember()
        self.scene = self.scene.with_placements(())
        self.carrying = None
        self.message = "Cleared the room."

    def undo(self) -> bool:
        if not self.history:
            self.message = "Nothing to undo."
            return False
        self.future.append(self.scene)
        self.scene = self.history.pop()
        self.carrying = None
        self.message = "Undone."
        return True

    def redo(self) -> bool:
        if not self.future:
            self.message = "Nothing to redo."
            return False
        self.history.append(self.scene)
        self.scene = self.future.pop()
        self.carrying = None
        self.message = "Redone."
        return True

    def switch_set(self, set_id: str) -> None:
        """Change rooms, which empties it: a store is not a house."""
        self._remember()
        self.scene = Scene(set_id=set_id, name=self.scene.name)
        self.category_index = 0
        self.piece_index = 0
        self.carrying = None
        self.message = f"Now building {interior_set(set_id).label}."

    # -- reporting ----------------------------------------------------

    def status(self) -> str:
        result = self.verdict()
        return (f"{self.entry().label}  |  "
                f"{self.cursor_x:+.2f}, {self.cursor_y:+.2f} m  "
                f"{self.cursor_yaw:.0f} deg  |  "
                f"headroom {result.clearance_m:.2f} m  |  "
                f"{'fits' if result.ok else result.why}")


# ----------------------------------------------------------------------
# Turning a scene into geometry
# ----------------------------------------------------------------------

def draw_scene(
    opaque,
    transparent,
    scene: Scene,
    *,
    shell: bool = True,
    detail: float = 1.0,
) -> None:
    """Draw a whole furnished dome: the room, then everything in it."""
    room = scene.room()
    if shell:
        draw_room(opaque, transparent, room)
    for item in scene.placements:
        draw_placement(opaque, transparent, room, item, detail=detail)


VERTEX_STRIDE = 10
"""Floats per vertex in a :class:`~two_v_demo.render_kit.TriangleBatch`:
three of position, three of normal, four of colour."""


def tinted(batch, colour):
    """The same geometry in one flat colour, for a ghost.

    A batch is a flat list of floats, so this rewrites the colour slots
    and leaves positions and normals where they are.  Recolouring the
    whole piece is what makes a ghost read as a ghost -- tinting one
    palette role leaves most of the piece looking placed already.
    """
    from .render_kit import TriangleBatch

    out = TriangleBatch()
    values = list(batch.vertices)
    for start in range(0, len(values), VERTEX_STRIDE):
        values[start + 6:start + 10] = list(colour)
    out.vertices = values
    return out


def footprint_marks(batch, placement: Placement,
                    colour, radius_m: float) -> None:
    """A bar round the piece's footprint, drawn flat on the floor."""
    length, width = placement.footprint()
    points = corners(placement.x, placement.y, placement.yaw_deg,
                     length, width)
    height = 0.03
    for index in range(4):
        one = points[index]
        two = points[(index + 1) % 4]
        batch.cylinder(np.array([one[0], one[1], height]),
                       np.array([two[0], two[1], height]), 0.024, colour, 5)
        # Corner posts up the side of the piece.  Without them the
        # marker disappears the moment the piece is standing on a rug or
        # a riser, which is exactly when you need to see it.
        batch.cylinder(np.array([one[0], one[1], height]),
                       np.array([one[0], one[1],
                                 height + min(1.2, placement.height())]),
                       0.018, colour, 4)
    # A nose, so which way it is facing is never in doubt.
    angle = math.radians(placement.yaw_deg)
    nose = np.array([placement.x + math.cos(angle) * (length * 0.5 + 0.30),
                     placement.y + math.sin(angle) * (length * 0.5 + 0.30),
                     height])
    batch.cylinder(np.array([placement.x, placement.y, height]), nose,
                   0.022, colour, 5)
    del radius_m


def draw_placement(
    opaque,
    transparent,
    room: InteriorSet,
    item: Placement,
    *,
    detail: float = 1.0,
    tint=None,
) -> None:
    """Draw one placed thing, prop or person."""
    if item.kind == "CAST":
        who = GLAM_CAST[item.ref]
        look = Look(character_id=item.ref, mode=item.mode,
                    pose_key=item.pose_key, hair_style=item.hair_style,
                    position=(item.x, item.y, item.lift_m),
                    yaw_deg=item.yaw_deg, detail=detail)
        draw_look(opaque, look, transparent=transparent)
        del who
        return
    draw_prop(opaque, prop(item.ref), room, item.x, item.y, item.yaw_deg,
              lift=item.lift_m, tint=tint)


# ----------------------------------------------------------------------
# Something to open with
# ----------------------------------------------------------------------

def starter_scene(set_id: str) -> Scene:
    """A furnished room, so the editor does not open on an empty floor.

    Both layouts are built the way the composer would build them, and
    :func:`validate_scene_composer` re-checks every piece through
    :func:`check` -- so the starter cannot ship with something in it
    that the editor would have refused.
    """
    if set_id == "DOME_HOME":
        placements = [
            Placement("PROP", "RUG_ROUND", 0.0, 0.0, 0.0),
            Placement("PROP", "SECTIONAL", -1.35, 0.60, 0.0),
            Placement("PROP", "LOUNGE_CHAIR", 1.30, -0.90, 160.0),
            Placement("PROP", "COFFEE_TABLE", 0.05, 0.10, 0.0),
            Placement("PROP", "SIDE_TABLE", 1.45, 0.45, 0.0),
            Placement("PROP", "FLOOR_LAMP", -2.10, -1.35, 45.0),
            Placement("PROP", "KITCHEN_ISLAND", 2.60, 2.30, 300.0),
            Placement("PROP", "GALLEY_RUN", 3.35, 4.05, 310.0),
            Placement("PROP", "TALL_FRIDGE", 1.45, 4.85, 285.0),
            Placement("PROP", "DINING_TABLE", -3.30, 2.55, 40.0),
            Placement("PROP", "DINING_CHAIR", -3.83, 3.18, 310.0),
            Placement("PROP", "DINING_CHAIR", -2.77, 1.92, 130.0),
            Placement("PROP", "PLATFORM_BED", -1.20, -3.60, 60.0),
            Placement("PROP", "WARDROBE", -3.75, -3.15, 40.0),
            Placement("PROP", "PLANTER_TALL", 3.60, -1.10, 0.0),
            Placement("PROP", "PLANT_LOW", 2.05, -3.30, 0.0),
            Placement("PROP", "WOOD_STOVE", 0.90, -2.40, 0.0),
            Placement("PROP", "PENDANT_CLUSTER", 0.0, 0.0, 0.0, 1.60),
            Placement("PROP", "ARCH_MIRROR", 4.95, 2.05, 205.0),
            Placement("CAST", "GLAM_NAILAH", -0.60, -0.95, 70.0,
                      mode="STREET"),
            Placement("CAST", "GLAM_RENATA", 0.95, 1.05, 250.0,
                      mode="PARTY"),
        ]
    elif set_id == "DOME_STORE":
        placements = [
            Placement("PROP", "RUNWAY_STRIP", 0.0, 0.0, 90.0),
            Placement("PROP", "RAIL_ROUND", -2.60, 1.85, 0.0),
            Placement("PROP", "RAIL_STRAIGHT", -3.20, -1.90, 20.0),
            Placement("PROP", "RAIL_STRAIGHT", 3.10, 2.20, 200.0),
            Placement("PROP", "CASH_DESK", 3.95, -2.55, 210.0),
            Placement("PROP", "STOOL", 4.55, -3.25, 30.0),
            Placement("PROP", "FITTING_POD", -0.20, 4.20, 180.0),
            Placement("PROP", "FITTING_POD", 1.70, 4.55, 180.0),
            Placement("PROP", "BENCH", 0.75, 2.85, 0.0),
            Placement("PROP", "MIRROR_TRIPLE", -5.90, 3.10, 330.0),
            Placement("PROP", "PLINTH", 1.55, -1.25, 0.0),
            Placement("PROP", "PLINTH", 2.35, -0.35, 0.0),
            Placement("PROP", "DRESS_FORM", -1.55, -1.15, 40.0),
            Placement("PROP", "SHOE_RISER", -4.35, 0.35, 90.0),
            Placement("PROP", "JEWEL_CASE", 4.35, 0.75, 250.0),
            Placement("PROP", "LOOKBOOK_TABLE", -1.70, -3.55, 70.0),
            Placement("PROP", "PLANTER_TALL", 5.35, 3.55, 0.0),
            Placement("PROP", "STEAMER", -5.05, -2.95, 0.0),
            Placement("PROP", "STOCK_CRATE", -6.10, -1.35, 25.0),
            Placement("PROP", "CURVED_SHELF", 6.30, -0.60, 190.0),
            Placement("PROP", "NEON_SIGN", 6.85, 1.90, 200.0),
            Placement("PROP", "LIGHT_RING", 0.0, 0.0, 0.0, 2.90),
            Placement("CAST", "GLAM_NAILAH", 2.15, -2.10, 200.0,
                      mode="FASHION"),
            Placement("CAST", "GLAM_ITZEL", 0.35, -0.85, 20.0,
                      mode="FASHION"),
            Placement("CAST", "GLAM_MEI", -1.05, 2.55, 250.0, mode="STREET"),
            Placement("CAST", "GLAM_AROHA", 4.70, 1.65, 195.0, mode="STREET"),
            Placement("CAST", "GLAM_PRIYA", 0.75, 2.85, 175.0, mode="PARTY",
                      pose_key="seated"),
        ]
    else:
        raise ValueError(f"no starter layout for {set_id!r}")
    return Scene(set_id=set_id, name=f"{set_id.lower()}_starter",
                 placements=tuple(placements))


def scene_report(scene: Scene) -> str:
    room = scene.room()
    lines = [f"{room.label.upper()}  --  {scene.name}",
             f"{len(scene.placements)} pieces, "
             f"{floor_share(scene) * 100:.0f}% of the floor used", ""]
    by_category: dict[str, list[Placement]] = {}
    for item in scene.placements:
        key = (CAST_CATEGORY if item.kind == "CAST"
               else prop(item.ref).category)
        by_category.setdefault(key, []).append(item)
    for category, items in by_category.items():
        lines.append(category)
        for item in items:
            head = footprint_clearance(item, room.radius_m)
            lines.append(f"    {item.label():<32} "
                         f"at {item.x:+.2f}, {item.y:+.2f} "
                         f"facing {item.yaw_deg:>3.0f} deg, "
                         f"{item.height():.2f} m under {head:.2f} m")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_scene_composer() -> None:
    """Prove the rules, the editing, the round trip and both starters."""
    from .render_kit import TriangleBatch

    # Footprints turn rather than smear, and a rotated one still has the
    # same area.
    rect = corners(1.0, 2.0, 37.0, 2.0, 1.0)
    assert rect.shape == (4, 2)
    edges = [float(np.linalg.norm(rect[(index + 1) % 4] - rect[index]))
             for index in range(4)]
    assert abs(edges[0] - 2.0) < 1e-9 and abs(edges[1] - 1.0) < 1e-9
    assert np.allclose(rect.mean(axis=0), [1.0, 2.0])

    # The separating-axis test agrees with the obvious cases, including
    # the one an axis-aligned test would get wrong.
    assert rectangles_overlap(corners(0, 0, 0, 1, 1), corners(0.4, 0, 0, 1, 1))
    assert not rectangles_overlap(corners(0, 0, 0, 1, 1),
                                  corners(2.0, 0, 0, 1, 1))
    assert not rectangles_overlap(corners(0, 0, 45, 1, 1),
                                  corners(1.2, 1.2, 45, 1, 1))
    assert rectangles_overlap(corners(0, 0, 45, 2, 0.2),
                              corners(0.5, 0.5, 45, 2, 0.2))

    # The dome does the refusing.  A fitting pod fits near the middle of
    # the store and does not fit near the wall, and nobody wrote that
    # down anywhere: the shell decides.
    scene = Scene(set_id="DOME_STORE")
    radius = scene.room().radius_m
    tall = Placement("PROP", "FITTING_POD", 0.0, 0.0, 0.0)
    assert check(scene, tall).ok
    # Far enough out that the shell has come down past the top of it,
    # but still comfortably inside the base ring: the refusal is about
    # height, not about the edge of the floor.
    outer = replace(tall, x=radius * 0.86)
    verdict = check(scene, outer)
    assert not verdict.ok
    assert any("shell is" in reason for reason in verdict.reasons), verdict
    assert verdict.clearance_m > 0.0
    # ... and turning it can be the difference, because the corners
    # move.  End-on, the deck's far corners reach further out and hit
    # the falling shell; broadside they do not.
    edge = Placement("PROP", "MEZZANINE", radius * 0.66, 0.0, 90.0)
    turned = replace(edge, yaw_deg=0.0)
    assert check(scene, edge).ok, check(scene, edge).why
    assert not check(scene, turned).ok, (
        "a long piece near the wall has to care which way it faces")

    # Off the floor entirely is refused for a different, stated reason,
    # and the reason is the polygon rather than a circle.
    outside = Placement("PROP", "STOOL", radius * 1.4, 0.0, 0.0)
    assert any("outside the dome" in reason
               for reason in check(scene, outside).reasons)
    # The gap between the polygon and the circle is real, and a piece
    # standing in it is refused even though it is inside the radius.
    between = Placement("PROP", "STOOL", radius * 0.995, 0.0, 0.0)
    assert not check(scene, between).ok
    assert check(scene, Placement("PROP", "STOOL",
                                  base_ring_apothem(radius) * 0.90,
                                  0.0, 0.0)).ok

    # A wall piece wants a wall.
    mirror = Placement("PROP", "MIRROR_TRIPLE", 0.0, 0.0, 0.0)
    assert any("wall" in reason for reason in check(scene, mirror).reasons)
    assert check(scene, replace(mirror, x=radius * 0.80, yaw_deg=180.0)).ok

    # A hanging piece has to leave room to walk under it.
    low = Placement("PROP", "PENDANT_CLUSTER", 0.0, 0.0, 0.0, lift_m=5.6)
    assert any("walk under" in reason for reason in check(scene, low).reasons)
    assert check(scene, replace(low, lift_m=1.5)).ok

    # Two things cannot stand in the same place, but a rug can be under
    # anything.
    seated_room = scene.with_placements((
        Placement("PROP", "SECTIONAL", 0.0, 0.0, 0.0),))
    assert any("standing in" in reason for reason in check(
        seated_room, Placement("PROP", "STOOL", 0.0, 0.0, 0.0)).reasons)
    rug_room = scene.with_placements((
        Placement("PROP", "RUNWAY_STRIP", 0.0, 0.0, 0.0),))
    assert check(rug_room, Placement("PROP", "STOOL", 0.0, 0.0, 0.0)).ok

    # Sitting down needs something to sit on, at the right height.
    sitter = Placement("CAST", "GLAM_PRIYA", 0.0, 0.0, 0.0,
                       pose_key="seated")
    assert any("nothing under her" in reason
               for reason in check(scene, sitter).reasons)
    bench_room = scene.with_placements((
        Placement("PROP", "BENCH", 0.0, 0.0, 0.0),))
    assert check(bench_room, sitter).ok, check(bench_room, sitter).why
    # She is excused for the seat she is on and for nothing else: put a
    # crate beside the bench and she is standing in it again.
    crowded = scene.with_placements((
        Placement("PROP", "BENCH", 0.0, 0.0, 0.0),
        Placement("PROP", "STOCK_CRATE", 0.30, 0.0, 0.0)))
    assert any("standing in" in reason
               for reason in check(crowded, sitter).reasons)
    # And standing up on the bench is still refused.
    assert not check(bench_room, replace(sitter, pose_key="power_stand")).ok
    plinth_room = scene.with_placements((
        Placement("PROP", "PLINTH", 0.0, 0.0, 0.0),))
    assert not check(plinth_room, sitter).ok, "a plinth is not a seat"

    # A refusal always says something.
    assert check(scene, outer).why != "fits"
    assert check(scene, tall).why == "fits"

    # -- the editor ---------------------------------------------------

    composer = Composer(scene=Scene(set_id="DOME_STORE"))
    groups = composer.groups()
    assert CAST_CATEGORY in groups and len(groups[CAST_CATEGORY]) == 8
    first = composer.category()
    composer.cycle_category()
    assert composer.category() != first
    composer.cycle_category(-1)
    assert composer.category() == first
    # Cycling wraps rather than running off the end.
    for _ in range(len(composer.entries()) + 3):
        composer.cycle_piece()
    assert composer.entry() in composer.entries()

    # Placing, moving, removing, undoing.
    composer.category_index = list(groups).index("SEATING")
    composer.piece_index = 0
    composer.move_to(1.13, -0.42)
    assert composer.cursor_x == 1.25 and composer.cursor_y == -0.5, (
        "the cursor snaps to the grid")
    composer.turn(2)
    assert composer.cursor_yaw == 30.0
    assert composer.place().ok
    assert len(composer.scene.placements) == 1
    placed = composer.scene.placements[0]
    assert placed.yaw_deg == 30.0

    assert composer.pick_up(0)
    assert composer.carrying == 0
    composer.nudge(4, 0)
    assert composer.place().ok
    assert len(composer.scene.placements) == 1, "moving is not copying"
    assert composer.scene.placements[0].x != placed.x

    assert composer.undo()
    assert composer.scene.placements[0].x == placed.x
    assert composer.redo()
    assert composer.scene.placements[0].x != placed.x
    assert composer.remove(0)
    assert not composer.scene.placements
    assert composer.undo() and len(composer.scene.placements) == 1

    # Hovering finds what is under a point and nothing where there is
    # nothing.
    here = composer.scene.placements[0]
    assert composer.hover(here.x, here.y) == 0
    assert composer.hover(here.x + 6.0, here.y) is None

    # A refused placement changes nothing and says why.
    before = composer.scene
    composer.move_to(radius * 1.5, 0.0)
    result = composer.place()
    assert not result.ok and composer.scene is before
    assert composer.message == result.why

    # Cast cycles walk wardrobe, pose and hair, and come back round.
    composer.category_index = list(groups).index(CAST_CATEGORY)
    composer.piece_index = 0
    start_mode = composer.mode()
    for _ in range(len(WARDROBE_MODES)):
        composer.cycle_mode()
    assert composer.mode() == start_mode
    composer.cycle_pose()
    assert composer.pose() in POSE_ORDER
    for _ in range(len(POSE_ORDER)):
        composer.cycle_pose()
    assert composer.pose() == "", "the cycle comes back to her own pose"
    composer.cycle_hair()
    assert composer.hair() in STYLE_ORDER
    for _ in range(len(STYLE_ORDER)):
        composer.cycle_hair()
    assert composer.hair() == "", "and so does her own hair"

    # Picking up a placed woman restores what she was wearing.
    composer.clear()
    composer.move_to(0.0, 0.0)
    composer.cycle_mode()
    composer.cycle_pose()
    wearing, standing = composer.mode(), composer.pose()
    assert composer.place().ok
    composer.cycle_mode()
    composer.cycle_pose()
    assert composer.pick_up(0)
    assert composer.mode() == wearing and composer.pose() == standing

    # Facing the centre points a piece inward, wherever it is.
    composer.move_to(3.0, 3.0)
    composer.face_centre()
    assert abs(composer.cursor_yaw - 225.0) < 1e-6, composer.cursor_yaw

    # Switching rooms starts a new one.
    composer.switch_set("DOME_HOME")
    assert composer.scene.set_id == "DOME_HOME"
    assert not composer.scene.placements
    assert composer.undo() and composer.scene.set_id == "DOME_STORE"

    # -- the starters -------------------------------------------------

    for set_id in DOME_SETS:
        start = starter_scene(set_id)
        assert start.set_id == set_id
        assert len(start.placements) >= 18, set_id
        # Every piece in the starter would have been accepted by the
        # editor, checked against the rest of the room around it.
        for index, item in enumerate(start.placements):
            rest = start.with_placements(
                [other for position, other in enumerate(start.placements)
                 if position != index])
            outcome = check(rest, item)
            assert outcome.ok, (set_id, item.ref, outcome.why)
        assert floor_share(start) < MAX_FLOOR_SHARE, set_id
        # Both rooms have people in them and something to sit on.
        assert any(item.kind == "CAST" for item in start.placements), set_id
        assert any(item.kind == "PROP" and prop(item.ref).seats
                   for item in start.placements), set_id

        # It draws.
        opaque = TriangleBatch()
        clear = TriangleBatch()
        draw_scene(opaque, clear, start, detail=0.4)
        assert opaque.vertices and clear.vertices, set_id
        points = np.asarray(opaque.vertices,
                            dtype=float).reshape(-1, 10)[:, :3]
        room = start.room()
        assert points[:, 2].max() < room.radius_m + 0.3, set_id
        assert np.linalg.norm(points[:, :2], axis=1).max() < \
            room.radius_m * 1.10, set_id

        # And it survives a round trip through the file format.
        text = json.dumps(start.to_dict())
        again = Scene.from_dict(json.loads(text))
        assert again == start, set_id
        assert scene_report(again)

    # The placement gizmo traces the piece and points the way it faces,
    # and stands up the side of it so a rug cannot hide it.
    marks = TriangleBatch()
    held = Placement("PROP", "CASH_DESK", 1.0, -2.0, 90.0)
    footprint_marks(marks, held, (1.0, 1.0, 1.0, 1.0), 8.0)
    mark_points = np.asarray(marks.vertices).reshape(-1, VERTEX_STRIDE)[:, :3]
    assert mark_points[:, 2].min() < 0.06
    assert 0.5 < mark_points[:, 2].max() <= 1.24, mark_points[:, 2].max()
    ahead = mark_points[np.argmax(mark_points[:, 1])]
    assert ahead[1] > -2.0, "the nose points the way the piece faces"

    # A ghost is the whole piece in one colour, geometry untouched.
    solid = TriangleBatch()
    solid.box((0.0, 0.0, 0.5), (1.0, 1.0, 1.0), (0.2, 0.3, 0.4, 1.0))
    ghost = tinted(solid, (0.2, 0.9, 0.4, 0.6))
    assert len(ghost.vertices) == len(solid.vertices)
    before = np.asarray(solid.vertices).reshape(-1, VERTEX_STRIDE)
    after = np.asarray(ghost.vertices).reshape(-1, VERTEX_STRIDE)
    assert np.allclose(before[:, :6], after[:, :6])
    assert np.allclose(after[:, 6:], np.asarray([0.2, 0.9, 0.4, 0.6]))

    try:
        Scene.from_dict({"schema": "something/else", "set_id": "DOME_HOME",
                         "placements": []})
    except ValueError:
        pass
    else:
        raise AssertionError("a foreign file has to be refused")
    try:
        starter_scene("DOME_YACHT")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown set has to be refused")


if __name__ == "__main__":
    validate_scene_composer()
    print(scene_report(starter_scene("DOME_STORE")))
