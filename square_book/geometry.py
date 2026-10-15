"""The geometry of wedge-shaped lumber: what a radial split gives, and what
two of them make together.

Every figure in *'Square' on Demand* comes from here. A round log split
through its pith into ``n`` equal sectors gives wedges whose two flat faces
meet at the pith at ``360/n`` degrees. Trim the curved bark side flat and the
section is an isosceles triangle:

* legs ``R`` (the log's radius), apex angle ``theta = 360/n``;
* back (the chord) ``c = 2 R sin(theta/2)``;
* base angles ``beta = 90 - theta/2``; area ``R^2 sin(theta) / 2``.

Two of them make a board in two ways:

* **slant to slant** -- one turned end for end, mated on a radial face. The
  pair is a parallelogram with sides ``R`` and ``c`` and corners of
  ``90 + theta/2`` and ``90 - theta/2``: the skewed board. The largest
  rectangle inside it, cut along the long side, is ``R cos(theta)`` by
  ``R sin(theta)``. For eighths that is a square, ``R/sqrt(2)`` on a side:
  the square on demand;
* **back to back** -- mated on their bark faces. The pair is a rhombus of side
  ``R``; for quarters it is a true square, ``R`` on a side, with nothing to plane.

The comparison with milling uses the project's own sawmill simulator,
:func:`two_v_demo.wedge_geometry.two_by_four_packing`, and its declared
chainsaw kerf, so this book and the others cannot disagree.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from two_v_demo import wedge_geometry as wg


@dataclass(frozen=True)
class Declared:
    key: str
    value: float
    unit: str
    kind: str
    why: str


#: What this book declares rather than derives. Every other number is computed.
DECLARED: tuple[Declared, ...] = (
    Declared("kerf_in", wg.DEFAULT_LOG.kerf_in, "in", "measured",
             "the chainsaw's cut width, the same figure every book in the project uses"),
    Declared("plane_in", 1 / 16, "in", "estimate",
             "taken off each face when a sawn face is planed true"),
    Declared("dressed_2x4", 1.5, "in", "published",
             "a dressed 2x4 is 1-1/2 by 3-1/2 inches (American Softwood Lumber Standard)"),
    Declared("dressed_2x4_w", 3.5, "in", "published", "the 3-1/2 inch face of the same"),
    Declared("dressed_4x4", 3.5, "in", "published", "a dressed 4x4 is 3-1/2 inches square"),
    Declared("reference_log_in", 12.0, "in", "the project's",
             "the reference trunk the dome books are cut from"),
)
D = {d.key: d.value for d in DECLARED}

#: Log diameters the tables are worked for, inches: small poles to a good
#: sawlog. A range, chosen; every row is computed.
DIAMETERS = (8.0, 10.0, 12.0, 14.0, 16.0, 18.0)
#: Split counts the book compares: quarters, sixths, eighths, twelfths.
SPLITS = (4, 6, 8, 12)


# ----------------------------------------------------------------------
# One wedge
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Wedge:
    diameter: float
    n: int

    @property
    def r(self) -> float:
        return self.diameter / 2

    @property
    def theta(self) -> float:
        """The angle at the pith, degrees."""
        return 360.0 / self.n

    @property
    def beta(self) -> float:
        """Each base angle of the trimmed triangle, degrees."""
        return 90.0 - self.theta / 2

    @property
    def chord(self) -> float:
        return wg.sector_chord_in(self.diameter, self.n)

    @property
    def depth(self) -> float:
        """Pith to the middle of the trimmed back."""
        return self.r * math.cos(math.radians(self.theta / 2))

    @property
    def sector_area(self) -> float:
        return wg.sector_area_in2(self.diameter, self.n)

    @property
    def triangle_area(self) -> float:
        return 0.5 * self.r ** 2 * math.sin(math.radians(self.theta))

    @property
    def scale(self) -> float:
        """How much the kerf shrinks the trimmed triangle. Each radial face
        loses half a kerf, which moves the apex out along the bisector; the
        triangle that is left is the same shape, this much smaller."""
        shift = (D["kerf_in"] / 2) / math.sin(math.radians(self.theta / 2))
        return max(0.0, (self.depth - shift) / self.depth)

    @property
    def r_eff(self) -> float:
        return self.r * self.scale

    @property
    def chord_eff(self) -> float:
        return self.chord * self.scale

    @property
    def triangle_eff(self) -> float:
        """The trimmed triangle after the saw has taken its kerf."""
        return self.triangle_area * self.scale ** 2

    @property
    def kerf_area(self) -> float:
        """This wedge's share of the saw cuts: n/2 full diameters, each a kerf wide."""
        return (self.n / 2) * D["kerf_in"] * self.diameter / self.n

    @property
    def split_area(self) -> float:
        """What a wedge holds as it comes off the log, bark side still round."""
        return self.sector_area - self.kerf_area

    @property
    def back_loss(self) -> float:
        """The curved slab taken off when the back is trimmed flat."""
        return self.sector_area - self.triangle_area

    @property
    def shim_angle(self) -> float:
        """The taper that turns a radial face plumb when the wedge lies on its
        back: half the pith angle -- a wedge from a log split twice as many ways."""
        return self.theta / 2

    @property
    def shim_split(self) -> int:
        return self.n * 2

    @property
    def shim_thick(self) -> float:
        """That shim's thick end, over the whole face of the wedge."""
        return self.r * math.tan(math.radians(self.shim_angle))

    @property
    def pitch_in_12(self) -> float:
        """The skew as a roof pitch: rise in twelve for a face at theta/2."""
        return 12.0 * math.tan(math.radians(self.theta / 2))


def _best_rectangle(a: float, b: float, phi_deg: float) -> tuple[float, float]:
    """The largest rectangle in a parallelogram with sides a and b and acute
    angle phi, cut square to one of its sides: (width, height)."""
    phi = math.radians(phi_deg)
    best = (0.0, 0.0)
    for base, side in ((a, b), (b, a)):
        h = side * math.sin(phi)
        w = base - side * math.cos(phi)
        if w > 0 and w * h > best[0] * best[1]:
            best = (max(w, h), min(w, h))
    return best


@dataclass(frozen=True)
class Pair:
    """Two wedges made into one member."""

    wedge: Wedge
    way: str
    """``slant`` (mated on a radial face, one reversed) or ``back`` (on the bark faces)."""

    @property
    def sides(self) -> tuple[float, float]:
        w = self.wedge
        return (w.r_eff, w.chord_eff) if self.way == "slant" else (w.r_eff, w.r_eff)

    @property
    def acute(self) -> float:
        w = self.wedge
        return w.beta if self.way == "slant" else min(w.theta, 180 - w.theta)

    @property
    def obtuse(self) -> float:
        return 180.0 - self.acute

    @property
    def area(self) -> float:
        return 2 * self.wedge.triangle_eff

    @property
    def thickness(self) -> float:
        """Across the pair, square to its long faces."""
        a, b = self.sides
        return b * math.sin(math.radians(self.acute))

    @property
    def planed(self) -> tuple[float, float]:
        """The largest rectangle the pair planes to, after the planing allowance."""
        a, b = self.sides
        w, h = _best_rectangle(a, b, self.acute)
        cut = 2 * D["plane_in"]
        if self.way == "back" and abs(self.acute - 90) < 1e-9:
            return (a - cut, b - cut)
        return (max(w - cut, 0.0), max(h - cut, 0.0))

    @property
    def planed_area(self) -> float:
        w, h = self.planed
        return w * h

    @property
    def is_square(self) -> bool:
        w, h = self.planed
        return w > 0 and abs(w - h) < 0.02 * w

    @property
    def kept_of_pair(self) -> float:
        return self.planed_area / self.area

    @property
    def kept_of_log(self) -> float:
        """Planed member over the two sectors of round log it came from."""
        return self.planed_area / (2 * self.wedge.sector_area)

    def fits(self, width: float, thick: float) -> int:
        """How many dressed pieces of this size the planed square yields, kerf between."""
        w, h = self.planed
        k = D["kerf_in"]
        best = 0
        for a, b in ((w, h), (h, w)):
            best = max(best, int((a + k) // (width + k)) * int((b + k) // (thick + k)))
        return best


def best_pair(w: Wedge) -> Pair:
    pairs = [Pair(w, "slant"), Pair(w, "back")]
    return max(pairs, key=lambda p: p.planed_area)


# ----------------------------------------------------------------------
# Against the mill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Recovery:
    diameter: float

    @property
    def round_area(self) -> float:
        return math.pi * (self.diameter / 2) ** 2

    @property
    def split(self) -> float:
        """Eighths as they come off the log: everything but the kerf."""
        w = Wedge(self.diameter, 8)
        return 8 * w.split_area / self.round_area

    @property
    def triangles(self) -> float:
        w = Wedge(self.diameter, 8)
        return 8 * w.triangle_eff / self.round_area

    @property
    def squares(self) -> float:
        """Eighths paired and planed square: four squares a section."""
        return 4 * best_pair(Wedge(self.diameter, 8)).planed_area / self.round_area

    @property
    def two_by_fours(self) -> int:
        return sum(wg.two_by_four_packing(self.diameter))

    @property
    def sawn(self) -> float:
        """The simulator's mill: true 2x4s packed in rows across the log."""
        return self.two_by_fours * 2.0 * 4.0 / self.round_area


def table_wedges() -> list[dict]:
    rows = []
    for d in DIAMETERS:
        w = Wedge(d, 8)
        p = best_pair(w)
        rows.append({"d": d, "r": w.r, "chord": w.chord, "depth": w.depth,
                     "area": w.triangle_area, "square": p.planed[0],
                     "kept": p.kept_of_log, "two_by_fours": p.fits(D["dressed_2x4_w"], D["dressed_2x4"]),
                     "four_by_four": p.fits(D["dressed_4x4"], D["dressed_4x4"])})
    return rows


def table_splits(diameter: float | None = None) -> list[dict]:
    d = diameter or D["reference_log_in"]
    rows = []
    for n in SPLITS:
        w = Wedge(d, n)
        for way in ("slant", "back"):
            p = Pair(w, way)
            pw, ph = p.planed
            rows.append({"n": n, "theta": w.theta, "way": way, "sides": p.sides, "acute": p.acute,
                         "planed": (pw, ph), "square": p.is_square, "kept": p.kept_of_log,
                         "pitch": w.pitch_in_12})
    return rows


#: Split counts for the trade-off: more splits, thinner wedges, flatter pairs, more kerf.
TRADE_SPLITS = (4, 6, 8, 12, 16, 24)


def table_tradeoff(diameter: float | None = None) -> list[dict]:
    """For one log: split n ways, pair every two, plane each pair to its best
    rectangle. What the member is, and how much of the log it keeps."""
    d = diameter or D["reference_log_in"]
    rows = []
    for n in TRADE_SPLITS:
        w = Wedge(d, n)
        p = best_pair(w)
        round_area = math.pi * (d / 2) ** 2
        rows.append({"n": n, "theta": w.theta, "way": p.way, "member": p.planed,
                     "members": n // 2, "pairs_kept": (n // 2) * p.planed_area / round_area,
                     "split_kept": n * w.split_area / round_area,
                     "kerf_lost": n * w.kerf_area / round_area, "pitch": w.pitch_in_12})
    return rows


def table_recovery() -> list[dict]:
    return [{"d": d, "split": Recovery(d).split, "triangles": Recovery(d).triangles,
             "squares": Recovery(d).squares, "sawn": Recovery(d).sawn,
             "two_by_fours": Recovery(d).two_by_fours} for d in DIAMETERS]


def validate() -> None:
    """The identities the book leans on, checked every build."""
    for d in DIAMETERS:
        w = Wedge(d, 8)
        p = Pair(w, "slant")
        a, b = p.sides
        # The skewed pair's corners are 90 +/- theta/2.
        assert abs(p.acute - 67.5) < 1e-9 and abs(p.obtuse - 112.5) < 1e-9
        # It planes to a square of side R/sqrt(2), before the planing allowance.
        side = w.r_eff / math.sqrt(2)
        pw, ph = p.planed
        assert abs(pw + 2 * D["plane_in"] - side) < 1e-6 and abs(ph + 2 * D["plane_in"] - side) < 1e-6
        # Its thickness is R sin(theta).
        assert abs(p.thickness - w.r_eff * math.sin(math.radians(45))) < 1e-9
        # Quarters back to back are a true square of side R.
        q = Pair(Wedge(d, 4), "back")
        assert q.is_square and abs(q.planed[0] + 2 * D["plane_in"] - q.wedge.r_eff) < 1e-9
        # A shim from a log split twice as many ways turns a face plumb.
        assert abs(w.beta + w.shim_angle - 90) < 1e-9
        # Splitting keeps more than the mill, and the square keeps less than the split.
        r = Recovery(d)
        assert r.squares < r.triangles < r.split <= 1
    assert abs(Wedge(12, 8).pitch_in_12 - 4.97) < 0.01


if __name__ == "__main__":
    validate()
    for row in table_wedges():
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in row.items()})
    for row in table_recovery():
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in row.items()})
    for row in table_tradeoff():
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
    for row in table_splits():
        print(row["n"], row["way"], [round(x, 2) for x in row["planed"]], row["square"],
              round(row["kept"], 3), round(row["pitch"], 2))
