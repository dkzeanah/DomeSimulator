"""The panel method: a timber dome built as framed panels on a jig, solved.

Most small timber domes sold as plans are not hub-and-strut frames and not
split-log wedges. They are **framed panels**: every triangle of the dome is
its own little frame of three sawn sticks, built flat on a plywood jig,
skinned in the shop, and screwed to its neighbours on site. This module
solves that method from first principles so a book or a film can teach it
with figures nobody typed in:

* the true three-frequency sphere (class I, a vertex at the top), its three
  chord lengths, and which triangles belong to pentagons and which to
  hexagons -- :func:`three_v_sphere`;
* the "5/8" cut -- the 3V sphere sawn off at the vertex level nearest
  five-eighths of its height -- and why its base zig-zags between two
  heights, so some base sections are tapered and some are not --
  :func:`five_eighths`;
* each panel as it is laid out on the jig: its outline from three lengths
  (two trammel arcs from the ends of a base line), its corner angles, the
  bevel its sticks need (half the fold to the next panel), and the
  pinwheel cut lengths of its three sticks -- :class:`PanelDome`;
* the covering sections (pentagons and hexagons skinned in one piece);
* a radial deck under an N-sided base -- :func:`radial_deck`;
* the "non-beveled" zome panel: four identical sticks in a pinwheel, mitred
  but never bevelled, and the gap that leaves on the outside --
  :func:`zome_panels`.

Nothing here is copied from anybody's plan set. The geometry is the sphere's
and the zonohedron's own; the conventions (what a "miter off square" means,
where the outline sits) are stated where they are used, so a reader can
check every figure with a calculator.

The pinwheel
------------
A panel's sticks do not meet at a point. Each stick runs all the way to one
corner (its *head*) and stops short at the other (its *tail*), where it butts
into the inside face of the next stick. Seen from above the corners turn like
a pinwheel. A stick of width ``w`` whose tail sits at a corner of interior
angle ``phi`` stops ``w / sin(phi)`` short of that corner along the outline,
and its tail is cut parallel to the stick it butts -- ``90 - phi`` off
square. That one rule sizes every panel stick in this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from .geometry import MM_PER_INCH, raw_icosahedron, normalize

#: Vertices closer than this (unit sphere) are the same vertex.
_KEY = 6
#: Lengths within this fraction are the same strut class.
_LENGTH_TOL = 1.0e-6


# ----------------------------------------------------------------------
# The sphere
# ----------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class Sphere:
    """A unit-radius geodesic sphere, a vertex straight up."""

    frequency: int
    vertices: np.ndarray            # (N, 3)
    faces: np.ndarray               # (M, 3) outward-wound
    edges: tuple[tuple[int, int], ...]
    valence: np.ndarray             # (N,)
    chord_classes: tuple[float, ...]  # distinct chord lengths, shortest first

    def chord_letter(self, a: int, b: int) -> str:
        length = float(np.linalg.norm(self.vertices[a] - self.vertices[b]))
        for index, chord in enumerate(self.chord_classes):
            if abs(length - chord) < 1e-6:
                return "ABCDEFGH"[index]
        raise ValueError(f"edge {a}-{b} has no class")

    def is_pentagon_face(self, face_index: int) -> bool:
        """A triangle that touches one of the twelve five-way vertices."""
        return any(self.valence[v] == 5 for v in self.faces[face_index])

    @property
    def levels(self) -> tuple[float, ...]:
        """The distinct vertex heights, top down."""
        return tuple(sorted({round(float(z), _KEY) for z in self.vertices[:, 2]}, reverse=True))


def _vertex_up(vertices: np.ndarray) -> np.ndarray:
    top = normalize(vertices[int(np.argmax(vertices[:, 2]))])
    target = np.array([0.0, 0.0, 1.0])
    axis = np.cross(top, target)
    s = float(np.linalg.norm(axis))
    if s < 1e-12:
        return vertices
    axis /= s
    c = float(np.dot(top, target))
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    rot = np.eye(3) + k * s + k @ k * (1 - c)
    return vertices @ rot.T


@lru_cache(maxsize=8)
def three_v_sphere(frequency: int = 3) -> Sphere:
    """Class I subdivision of the icosahedron, every point pushed to the sphere."""
    raw_v, raw_f = raw_icosahedron()
    base = _vertex_up(np.array([normalize(v) for v in raw_v]))
    lookup: dict[tuple, int] = {}
    points: list[np.ndarray] = []

    def add(p: np.ndarray) -> int:
        p = normalize(p)
        key = tuple(np.round(p, _KEY))
        if key not in lookup:
            lookup[key] = len(points)
            points.append(p)
        return lookup[key]

    f = frequency
    faces = []
    for ia, ib, ic in raw_f:
        a, b, c = base[ia], base[ib], base[ic]
        grid = {}
        for i in range(f + 1):
            for j in range(f + 1 - i):
                grid[(i, j)] = add(a * (f - i - j) + b * i + c * j)
        for i in range(f):
            for j in range(f - i):
                faces.append((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
                if i + j < f - 1:
                    faces.append((grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]))
    vertices = np.array(points)
    # Wind every face outward, so a face normal points away from the centre.
    wound = []
    for tri in faces:
        p0, p1, p2 = (vertices[k] for k in tri)
        n = np.cross(p1 - p0, p2 - p0)
        wound.append(tri if np.dot(n, p0 + p1 + p2) > 0 else (tri[0], tri[2], tri[1]))
    faces_arr = np.array(wound, dtype=np.int64)
    edge_set = sorted({tuple(sorted((int(t[k]), int(t[(k + 1) % 3])))) for t in faces_arr for k in range(3)})
    valence = np.zeros(len(vertices), dtype=np.int64)
    for a, b in edge_set:
        valence[a] += 1
        valence[b] += 1
    chords: list[float] = []
    for a, b in edge_set:
        length = float(np.linalg.norm(vertices[a] - vertices[b]))
        if not any(abs(length - c) < 1e-6 for c in chords):
            chords.append(length)
    return Sphere(frequency, vertices, faces_arr, tuple(edge_set), valence, tuple(sorted(chords)))


# ----------------------------------------------------------------------
# The cut
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BaseEdge:
    a: int
    b: int
    rise: float          # height difference of its two ends, unit sphere
    letter: str

    @property
    def tapered(self) -> bool:
        return self.rise > 1e-6


@dataclass(frozen=True, eq=False)
class Truncation:
    """The part of a sphere kept above one vertex level."""

    sphere: Sphere
    cut_level: float                  # the lowest vertex height kept
    faces: tuple[int, ...]            # indices into sphere.faces
    base: tuple[BaseEdge, ...]

    @property
    def height_fraction(self) -> float:
        """Apex-to-lowest-vertex height over the sphere's diameter."""
        return (1.0 - self.cut_level) / 2.0

    @property
    def pentagon_faces(self) -> tuple[int, ...]:
        return tuple(i for i in self.faces if self.sphere.is_pentagon_face(i))

    @property
    def hexagon_faces(self) -> tuple[int, ...]:
        return tuple(i for i in self.faces if not self.sphere.is_pentagon_face(i))

    @property
    def base_levels(self) -> tuple[float, ...]:
        zs = {round(float(self.sphere.vertices[v, 2]), _KEY) for e in self.base for v in (e.a, e.b)}
        return tuple(sorted(zs))

    @property
    def tapered_count(self) -> int:
        return sum(1 for e in self.base if e.tapered)

    @property
    def level_count(self) -> int:
        return sum(1 for e in self.base if not e.tapered)

    @property
    def max_rise(self) -> float:
        return max(e.rise for e in self.base)

    @property
    def base_radius(self) -> float:
        """Mean horizontal radius of the base vertices, unit sphere."""
        vs = {v for e in self.base for v in (e.a, e.b)}
        return float(np.mean([math.hypot(*self.sphere.vertices[v, :2]) for v in vs]))


def truncate(sphere: Sphere, cut_level: float) -> Truncation:
    keep = tuple(i for i, t in enumerate(sphere.faces)
                 if sphere.vertices[t, 2].min() >= cut_level - 1e-6)
    count: dict[tuple[int, int], int] = {}
    for i in keep:
        t = sphere.faces[i]
        for k in range(3):
            e = tuple(sorted((int(t[k]), int(t[(k + 1) % 3]))))
            count[e] = count.get(e, 0) + 1
    base = tuple(
        BaseEdge(a, b, abs(float(sphere.vertices[a, 2] - sphere.vertices[b, 2])), sphere.chord_letter(a, b))
        for (a, b), n in sorted(count.items()) if n == 1)
    # Store the exact lowest kept height, not the rounded level asked for.
    lowest = min(float(sphere.vertices[v, 2]) for i in keep for v in sphere.faces[i]) if keep else cut_level
    return Truncation(sphere, lowest, keep, base)


def five_eighths(frequency: int = 3) -> Truncation:
    """The cut whose height is nearest five-eighths of the diameter, among
    cuts that leave a single closed base -- what "a 5/8 dome" means."""
    sphere = three_v_sphere(frequency)
    best = None
    for level in sphere.levels[1:-1]:
        t = truncate(sphere, level)
        if not t.base:
            continue
        # a single closed loop: every base vertex used by exactly two base edges
        uses: dict[int, int] = {}
        for e in t.base:
            uses[e.a] = uses.get(e.a, 0) + 1
            uses[e.b] = uses.get(e.b, 0) + 1
        if any(n != 2 for n in uses.values()):
            continue
        score = abs(t.height_fraction - 5 / 8)
        if best is None or score < best[0] - 1e-9:
            best = (score, t)
    assert best is not None
    return best[1]


# ----------------------------------------------------------------------
# One panel on the jig
# ----------------------------------------------------------------------

def _triangle_angles(a: float, b: float, c: float) -> tuple[float, float, float]:
    """Interior angles (degrees) opposite sides a, b, c."""
    A = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
    B = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
    return A, B, 180.0 - A - B


@dataclass(frozen=True)
class PanelClass:
    """One shape of panel: what the jig is drawn for."""

    key: str                      # "pent" or "hex" plus its side letters
    kind: str                     # "pentagon" | "hexagon"
    letters: tuple[str, str, str]  # base, left, right
    sides: tuple[float, float, float]   # outline lengths, metres: base, left, right
    angles: tuple[float, float, float]  # interior angles at the corners opposite base, left, right
    count: int
    bevels: tuple[float, float, float]  # stick bevel off square, degrees, per side

    @property
    def base(self) -> float:
        return self.sides[0]

    @property
    def height(self) -> float:
        """Height of the outline above its base line (the jig's size)."""
        a, b, c = self.sides
        s = (a + b + c) / 2
        area = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))
        return 2 * area / a

    @property
    def area(self) -> float:
        return self.base * self.height / 2

    @property
    def isosceles(self) -> bool:
        return abs(self.sides[1] - self.sides[2]) < 1e-9

    def corner(self, side: int) -> tuple[float, float]:
        """Interior angles at the two ends of a side: (head, tail) in pinwheel order.

        Sides run base -> left -> right around the outline; each stick's
        head is the corner it shares with the *previous* side and its tail
        the corner it shares with the *next* side, where it butts.
        """
        # angles[k] sits opposite side k: the corner between the other two sides.
        tail = self.angles[(side + 2) % 3]   # between this side and the next
        head = self.angles[(side + 1) % 3]   # between this side and the previous
        return head, tail

    def stick(self, side: int, width: float) -> "Stick":
        head, tail = self.corner(side)
        short = width / math.sin(math.radians(tail))
        return Stick(self.letters[side], self.sides[side] - short, 90.0 - tail, self.bevels[side])


@dataclass(frozen=True)
class Stick:
    """One panel stick, as cut."""

    letter: str
    outer_length: float     # along its outer (bevelled) edge, metres
    tail_miter: float       # off square, degrees, cut flat on the jig
    bevel: float            # edge bevel off square, degrees


def fold_deg(sphere: Sphere, f1: int, f2: int) -> float:
    """How far two neighbouring flat panels turn from flat, degrees."""
    def normal(i: int) -> np.ndarray:
        p0, p1, p2 = (sphere.vertices[k] for k in sphere.faces[i])
        return normalize(np.cross(p1 - p0, p2 - p0))
    return math.degrees(math.acos(float(np.clip(np.dot(normal(f1), normal(f2)), -1.0, 1.0))))


@dataclass(frozen=True)
class PanelDome:
    """A 3V 5/8 dome of framed panels at a real size."""

    radius_m: float                 # sphere radius to the panels' outer face
    stick_width_m: float            # flat on the jig
    stick_depth_m: float            # through the wall
    cut: Truncation = field(default_factory=five_eighths)

    @property
    def sphere(self) -> Sphere:
        return self.cut.sphere

    # -- size --
    @property
    def diameter_m(self) -> float:
        return 2 * self.cut.base_radius * self.radius_m

    @property
    def height_m(self) -> float:
        return (1.0 - self.cut.cut_level) * self.radius_m

    @property
    def floor_area_m2(self) -> float:
        n = len(self.cut.base)
        r = self.cut.base_radius * self.radius_m
        return 0.5 * n * r * r * math.sin(2 * math.pi / n)

    @property
    def max_taper_m(self) -> float:
        """How much higher the high end of a tapered base section sits."""
        return self.cut.max_rise * self.radius_m

    def chord_m(self, letter: str) -> float:
        return self.sphere.chord_classes["ABCDEFGH".index(letter)] * self.radius_m

    # -- panels --
    def _neighbours(self) -> dict[tuple[int, int], list[int]]:
        out: dict[tuple[int, int], list[int]] = {}
        for i, t in enumerate(self.sphere.faces):
            for k in range(3):
                out.setdefault(tuple(sorted((int(t[k]), int(t[(k + 1) % 3])))), []).append(i)
        return out

    def edge_folds(self) -> dict[str, tuple[float, float]]:
        """Per chord letter: (smallest, largest) fold between the two panels on it."""
        nb = self._neighbours()
        folds: dict[str, list[float]] = {}
        for e, fs in nb.items():
            if len(fs) == 2:
                folds.setdefault(self.sphere.chord_letter(*e), []).append(fold_deg(self.sphere, *fs))
        return {k: (min(v), max(v)) for k, v in sorted(folds.items())}

    def panel_classes(self) -> tuple[PanelClass, ...]:
        folds = {k: (lo + hi) / 2 for k, (lo, hi) in self.edge_folds().items()}
        groups: dict[tuple, int] = {}
        meta: dict[tuple, tuple] = {}
        for i in self.cut.faces:
            t = self.sphere.faces[i]
            letters = [self.sphere.chord_letter(int(t[k]), int(t[(k + 1) % 3])) for k in range(3)]
            # Put the odd one out as the base (the long side of an isosceles
            # triangle, or the longest of a scalene one) so a builder's "bottom"
            # is the same edge every time.
            counts = {x: letters.count(x) for x in letters}
            odd = [x for x in letters if counts[x] == 1]
            base_letter = max(odd) if len(odd) == 1 else max(letters)
            k0 = letters.index(base_letter)
            ordered = tuple(letters[(k0 + j) % 3] for j in range(3))
            kind = "pentagon" if self.sphere.is_pentagon_face(i) else "hexagon"
            key = (kind, tuple(sorted(ordered)))
            groups[key] = groups.get(key, 0) + 1
            meta[key] = (kind, ordered)
        out = []
        for key, count in sorted(groups.items(), key=lambda kv: (kv[0][0] != "pentagon", kv[0][1])):
            kind, ordered = meta[key]
            sides = tuple(self.chord_m(x) for x in ordered)
            angles = _triangle_angles(*sides)
            bevels = tuple(folds[x] / 2 for x in ordered)
            out.append(PanelClass(f"{kind[:4]}-{''.join(ordered)}", kind, ordered, sides, angles, count, bevels))
        return tuple(out)

    @property
    def panel_count(self) -> int:
        return len(self.cut.faces)

    @property
    def stick_count(self) -> int:
        return 3 * self.panel_count

    def stick_table(self) -> list[tuple[str, int, Stick]]:
        """(panel key, how many, stick) for every stick of every panel class."""
        rows = []
        for pc in self.panel_classes():
            for side in range(3):
                rows.append((pc.key, pc.count, pc.stick(side, self.stick_width_m)))
        return rows

    @property
    def stick_metres(self) -> float:
        return sum(n * s.outer_length for _, n, s in self.stick_table())

    @property
    def panel_area_m2(self) -> float:
        return sum(pc.count * pc.area for pc in self.panel_classes())

    def bevel_spread(self) -> tuple[float, float]:
        folds = self.edge_folds()
        return (min(lo for lo, _ in folds.values()) / 2, max(hi for _, hi in folds.values()) / 2)

    # -- covering sections --
    def sections(self) -> tuple[int, int, int]:
        """(whole pentagons, whole hexagons, triangles left over) inside the cut.

        Skinning a whole pentagon or hexagon of panels in one sheet means one
        seam per section instead of one per triangle.
        """
        kept = set(self.cut.faces)
        around: dict[int, list[int]] = {}
        for i in kept:
            for v in self.sphere.faces[i]:
                around.setdefault(int(v), []).append(i)
        pent = hexa = 0
        used: set[int] = set()
        # Pentagons first (their centres are the five-way vertices), then the
        # hexagons centred on six-way vertices that do not touch a used face.
        for v, fs in sorted(around.items(), key=lambda kv: self.sphere.valence[kv[0]]):
            need = int(self.sphere.valence[v])
            if len(fs) == need and not used.intersection(fs):
                if need == 5:
                    pent += 1
                else:
                    hexa += 1
                used.update(fs)
        return pent, hexa, len(kept) - len(used)


def reference_panel_dome(radius_m: float, stick_width_m: float, stick_depth_m: float) -> PanelDome:
    return PanelDome(radius_m, stick_width_m, stick_depth_m)


# ----------------------------------------------------------------------
# The jig drawn with a trammel
# ----------------------------------------------------------------------

def trammel_apex(base: float, left: float, right: float) -> tuple[float, float]:
    """Where two arcs -- radius ``left`` from the base's left end and
    ``right`` from its right end -- cross: the third corner, base on the x axis."""
    x = (left * left - right * right + base * base) / (2 * base)
    return x, math.sqrt(max(left * left - x * x, 0.0))


# ----------------------------------------------------------------------
# A radial deck
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RadialDeck:
    sides: int
    radius_m: float           # to the outside corners of the rim
    girders: int              # sides of the girder ring under the joists

    @property
    def rim_length_m(self) -> float:
        """One rim board, long point to long point."""
        return 2 * self.radius_m * math.sin(math.pi / self.sides)

    @property
    def rim_miter_deg(self) -> float:
        """Each end of a rim board, off square."""
        return 180.0 / self.sides

    @property
    def girder_miter_deg(self) -> float:
        return 180.0 / self.girders

    @property
    def area_m2(self) -> float:
        return 0.5 * self.sides * self.radius_m ** 2 * math.sin(2 * math.pi / self.sides)

    @property
    def joists(self) -> int:
        return self.sides


def radial_deck(sides: int, radius_m: float) -> RadialDeck:
    """A deck shaped to the dome's base: one joist per base corner, a rim
    board per base edge, girders on the dome's own five-fold symmetry."""
    girders = 5 if sides % 5 == 0 else sides
    return RadialDeck(sides, radius_m, girders)


# ----------------------------------------------------------------------
# The zome panel without a bevel
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ZomeRow:
    row: int
    count: int
    acute_deg: float          # the rhombus's sharp corner
    fold_deg: float           # how far it turns from the next row's panels (largest)
    stick_outer_m: float      # each of the four identical sticks, outer edge
    miter_deg: float          # both ends, parallel, off square
    gap_m: float              # outside gap between neighbouring panels at full depth
    block_bevel_deg: float    # each face of a wedge block that fills the gap


def zome_panels(count: int, pitch_deg: float, side_m: float,
                stick_width_m: float, stick_depth_m: float) -> tuple[ZomeRow, ...]:
    """Every row of a polar zome built the non-beveled way.

    A rhombus panel is four identical sticks in a pinwheel: each runs to one
    corner and butts the next at the other, so both ends are cut parallel
    (long point to short point) and nothing is bevelled. Square-edged
    panels meeting on their *inside* edges open a V on the outside whose
    width is ``2 * depth * tan(fold / 2)``; a wedge block of bevel
    ``fold / 2`` a side fills it.
    """
    from .zome_geometry import polar_zonohedron

    z = polar_zonohedron(count, pitch_deg)
    verts = np.asarray(z.vertices, dtype=float)
    # The building is the zonohedron above its widest level ring (the rim);
    # the half below is its mirror image and is never built.
    rim = z.rim_height
    faces = [tuple(f) for f in z.faces if min(verts[k][2] for k in f) >= rim - 1e-9]

    def normal(face) -> np.ndarray:
        p = [verts[k] for k in face]
        n = normalize(np.cross(p[1] - p[0], p[2] - p[0]))
        centre = np.mean([verts[k] for k in face], axis=0) - np.mean(verts, axis=0)
        return n if np.dot(n, centre) > 0 else -n

    def corner(face) -> float:
        p = [verts[k] for k in face]
        u, v = p[1] - p[0], p[3] - p[0]
        ang = math.degrees(math.acos(float(np.clip(np.dot(normalize(u), normalize(v)), -1, 1))))
        return min(ang, 180 - ang)

    edge_faces: dict[tuple[int, int], list[int]] = {}
    for i, f in enumerate(faces):
        for k in range(len(f)):
            edge_faces.setdefault(tuple(sorted((f[k], f[(k + 1) % len(f)]))), []).append(i)

    centre_z = [float(np.mean([verts[k][2] for k in f])) for f in faces]
    levels = sorted({round(c, 6) for c in centre_z}, reverse=True)
    rows = []
    for r, level in enumerate(levels, start=1):
        members = [i for i, c in enumerate(centre_z) if abs(round(c, 6) - level) < 1e-9]
        acute = corner(faces[members[0]])
        folds = []
        for i in members:
            f = faces[i]
            for k in range(len(f)):
                for j in edge_faces[tuple(sorted((f[k], f[(k + 1) % len(f)])))]:
                    if j != i:
                        folds.append(math.degrees(math.acos(float(np.clip(
                            np.dot(normal(faces[i]), normal(faces[j])), -1, 1)))))
        fold = max(folds) if folds else 0.0
        # Pinwheel: every stick's tail corner alternates acute / obtuse, and
        # sin() is the same for both, so all four sticks are one length.
        outer = side_m - stick_width_m / math.sin(math.radians(acute))
        rows.append(ZomeRow(
            r, len(members), acute, fold, outer, 90.0 - acute,
            2 * stick_depth_m * math.tan(math.radians(fold / 2)), fold / 2))
    return tuple(rows)


# ----------------------------------------------------------------------
# The reference builds: declared inputs, then everything computed from them
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Declared:
    value: float
    unit: str
    why: str


#: Every input the panel-method figures depend on that geometry cannot supply.
#: Sizes and stock are choices, not measurements; change one and every figure
#: in the book and the film moves with it.
CONSTANTS: dict[str, Declared] = {
    "base_ft": Declared(16.0, "ft", "the reference 3V dome, base corner to base corner: a round size, "
                                    "and the largest that stands beside the wedge dome on the Cabin World hill"),
    "stock_w_in": Declared(1.5, "in", "a 2x3's actual thickness: the stick lies wide side down, so this is its width on the jig"),
    "stock_d_in": Declared(2.5, "in", "a 2x3's actual width, ripped in half along a bevel to make two sticks"),
    "kerf_in": Declared(0.125, "in", "a common table-saw blade"),
    "base_board_in": Declared(5.5, "in", "a 2x6 on edge under the lowest base corner: lifts the first panels off the deck's wet"),
    "zome_n": Declared(9, "directions", "a nine-sided zome"),
    "zome_pitch_deg": Declared(54.0, "deg", "the pitch the zome chapter uses, from the zome module"),
    "zome_side_m": Declared(0.9, "m", "panel side: puts the rim about four metres across, a garden-studio size"),
    "zome_w_in": Declared(1.5, "in", "a 2x4's thickness, flat on the bench"),
    "zome_d_in": Declared(3.5, "in", "a 2x4's width, on edge through the wall"),
}


def _c(name: str) -> float:
    return CONSTANTS[name].value


@lru_cache(maxsize=1)
def reference() -> PanelDome:
    """The book's and the film's 3V panel dome."""
    cut = five_eighths(3)
    base_r = _c("base_ft") * 0.3048 / 2
    depth = (_c("stock_d_in") - _c("kerf_in")) / 2 * MM_PER_INCH / 1000
    return PanelDome(base_r / cut.base_radius, _c("stock_w_in") * MM_PER_INCH / 1000, depth, cut)


@lru_cache(maxsize=1)
def reference_zome() -> tuple[ZomeRow, ...]:
    m = MM_PER_INCH / 1000
    return zome_panels(int(_c("zome_n")), _c("zome_pitch_deg"), _c("zome_side_m"),
                       _c("zome_w_in") * m, _c("zome_d_in") * m)


def facts() -> dict:
    """Every figure the book and the film quote about the panel method."""
    d = reference()
    cut = d.cut
    pcs = d.panel_classes()
    pent = next(pc for pc in pcs if pc.kind == "pentagon")
    hexa = next(pc for pc in pcs if pc.kind == "hexagon")
    lo, hi = d.bevel_spread()
    folds = d.edge_folds()
    p_sec, h_sec, single = d.sections()
    deck = radial_deck(len(cut.base), cut.base_radius * d.radius_m)
    sticks = d.stick_table()
    zrows = reference_zome()
    rim_m = None
    from .zome_geometry import ZomeBuild, polar_zonohedron
    zb = ZomeBuild(polar_zonohedron(int(_c("zome_n")), _c("zome_pitch_deg")), _c("zome_side_m"))
    return {
        "radius_m": d.radius_m, "diameter_m": d.diameter_m, "height_m": d.height_m,
        "floor_m2": d.floor_area_m2, "height_fraction": cut.height_fraction,
        "panels": d.panel_count, "pent": len(cut.pentagon_faces), "hex": len(cut.hexagon_faces),
        "base_edges": len(cut.base), "tapered": cut.tapered_count, "level": cut.level_count,
        "taper_m": d.max_taper_m,
        "chords": {x: d.chord_m(x) for x in "ABC"},
        "pent_class": pent, "hex_class": hexa,
        "bevel_lo": lo, "bevel_hi": hi, "bevel_mid": (lo + hi) / 2,
        "folds": folds,
        "sticks": d.stick_count, "stick_m": d.stick_metres,
        "stick_rows": sticks,
        "distinct_sticks": len({(round(s.outer_length, 6), round(s.tail_miter, 6)) for _, _, s in sticks}),
        "sections_pent": p_sec, "sections_hex": h_sec, "sections_single": single,
        "skin_m2": d.panel_area_m2,
        "stick_w_m": d.stick_width_m, "stick_d_m": d.stick_depth_m,
        "deck": deck,
        "zome_rows": zrows, "zome_panels": sum(r.count for r in zrows),
        "zome_rim_m": zb.widest_diameter, "zome_height_m": zb.height,
    }


def constants_table() -> str:
    width = max(len(k) for k in CONSTANTS)
    # Two spaces before the reason, always: a unit that fills its column
    # ("directions") must not run into the sentence after it.
    return "\n".join(f"{k:<{width}}  {c.value:>7g} {c.unit:<10}  {c.why}" for k, c in CONSTANTS.items())


# ----------------------------------------------------------------------
# Units and the self-test
# ----------------------------------------------------------------------

def mm(metres: float) -> float:
    return metres * 1000.0


def inches(metres: float) -> float:
    return metres * 1000.0 / MM_PER_INCH


def validate_panel_method() -> None:
    s = three_v_sphere(3)
    assert len(s.vertices) == 92 and len(s.faces) == 180, "3V sphere has 92 vertices, 180 faces"
    assert sorted(set(int(x) for x in s.valence)) == [5, 6] and int((s.valence == 5).sum()) == 12
    assert len(s.chord_classes) == 3, "class I 3V has three chord lengths"
    cut = five_eighths(3)
    assert len(cut.faces) == 105 and len(cut.pentagon_faces) == 30 and len(cut.hexagon_faces) == 75
    assert len(cut.base) == 15 and len(cut.base_levels) == 2, "the 5/8 base zig-zags on two levels"
    assert cut.tapered_count + cut.level_count == 15 and cut.tapered_count > 0
    d = PanelDome(2.4, 0.038, 0.032)
    pcs = d.panel_classes()
    assert sum(pc.count for pc in pcs) == 105
    for pc in pcs:
        assert abs(sum(pc.angles) - 180.0) < 1e-9
        x, y = trammel_apex(*pc.sides)
        assert abs(math.hypot(x, y) - pc.sides[1]) < 1e-9
        assert abs(math.hypot(pc.base - x, y) - pc.sides[2]) < 1e-9
    lo, hi = d.bevel_spread()
    assert 0 < lo <= hi < 15
    p, h, left = d.sections()
    assert 5 * p + 6 * h + left == 105
    deck = radial_deck(15, 2.3)
    assert abs(deck.rim_miter_deg - 12.0) < 1e-12
    rows = zome_panels(9, 54.0, 0.5, 0.038, 0.089)
    assert rows and all(0 < r.acute_deg <= 90 for r in rows)
    assert all(r.stick_outer_m < 0.5 for r in rows)


if __name__ == "__main__":
    validate_panel_method()
    d = PanelDome(2.4, 0.038, 0.032)
    cut = d.cut
    print(f"5/8 cut: height {cut.height_fraction:.4f} of the diameter, {len(cut.faces)} panels "
          f"({len(cut.pentagon_faces)} pentagon, {len(cut.hexagon_faces)} hexagon), "
          f"base {len(cut.base)} edges: {cut.tapered_count} tapered, {cut.level_count} level")
    for pc in d.panel_classes():
        print(pc.key, pc.count, [f"{mm(x):.0f}" for x in pc.sides], [f"{a:.2f}" for a in pc.angles],
              [f"{b:.2f}" for b in pc.bevels])
    print("folds", d.edge_folds(), "sections", d.sections())
