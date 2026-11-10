"""The structural grammar of the wedge: how a split sector behaves as a
general structural member, not only as a dome strut.

*The 40 Hour Cabin* already argues one half of this, in Chapter 15 and the
``why`` film: area is not strength, a sector is a deep narrow blade, and
there is a crossover trunk diameter above which one sector out-bends a
two-by-four.  :mod:`two_v_demo.wedge_why_facts` owns that arithmetic -- the
polygon :class:`~two_v_demo.wedge_why_facts.Section`, the studs, the
crossover -- and this module **imports it rather than restating it**, because
the repository's rule is that two things that state the same figure read it
from the same function.

What this module adds is the other half: the part of the idea that reaches
past the dome.

**The family at equal area.**  Hold the wood constant -- one dressed
two-by-four's worth of cross-section -- and split it finer.  The eighth, the
sixteenth, the thirty-second and the sixty-fourth of a log are not four sizes
of the same stick; they are four *shapes*, and as the sector narrows its
strong-axis second moment climbs while its weak-axis second moment collapses.
A fine wedge is a structural blade.  :func:`equal_area_families` is that
table, and every number in it is produced by the same ``Section`` the dome is
solved with.

**The connection law.**  A bundle is not a beam until something carries the
shear between its parts.  :func:`separated_chord_bounds` and
:func:`lamina_stack_bounds` compute the two limits a built-up member lives
between -- the loose stack that slides, and the fully composite section that
does not -- so the honest claim ("adding wood gains you *between* these two")
can be stated with both ends of it on the page.

**The pairing rules.**  :func:`opposite_mate` gives every sector its mate from
the far side of the same log, and the dyad reverses one end-for-end so the
taper cancels.  Those are index arithmetic, not opinion.

**The selection gates.**  :func:`three_gate` scores each split family against
the three things that actually decide whether a wedge is usable at a given
size: enough wood for the axial job, enough face to land a connector on, and
how much of the log the kerf eats.

Everything structural here is **geometry, not an allowable load**.  The wood
properties -- species, grade, knots, slope of grain, moisture, juvenile core
-- are not in these numbers, and a second moment is not a safe working stress.
:data:`SOURCES` records the research this grammar leans on, every one of which
says the same thing: the sections are promising, and the ratings come only
from testing.  :mod:`two_v_demo.wedge_grammar` is read by the book's
``grammar`` tokens and, later, by a film; it is checked with ``--check``.

Conventions: inches unless a name says otherwise; angles are degrees on the
way out and radians inside.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from . import wedge_why_facts as yf


# ----------------------------------------------------------------------
# The member families.  The names are the split count, which is also how
# the repository has always spoken of them (SPLITS = 2,4,8,16,32,64).
# ----------------------------------------------------------------------

FAMILIES: tuple[int, ...] = (8, 16, 32, 64)
"""The powers-of-two sector families the grammar compares: W8 (an eighth,
the dome's own member), W16, W32, W64.  Every one is reached by halving the
last, so the same first cut serves all four."""


def family_name(splits: int) -> str:
    return f"W{splits}"


def family_angle_deg(splits: int) -> float:
    return 360.0 / splits


# The owner's example pine, as circumferences round the trunk rather than
# diameters across it, because that is how the brief measured it.  Declared,
# not derived: a tape round two real trees.
BUTT_CIRCUMFERENCE_IN = 49.0
"""Circumference at the fat end of the example pine, from the brief."""
TOP_CIRCUMFERENCE_IN = 27.0
"""Circumference where the usable trunk ends, from the brief."""
CHAINSAW_KERF_IN = 0.25
"""A ripping chainsaw's kerf, from the brief -- the saw the coarse splits use."""
CONNECTOR_FACE_IN = yf.DRESSED_STUD_IN[0]
"""The face a conventional connector expects: a dressed two-by-four's 1.5 in.
Used only as the yardstick for the connection-width gate."""

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("butt_circumference_in", BUTT_CIRCUMFERENCE_IN, "in",
     "Circumference at the fat end of the example pine, from the brief."),
    ("top_circumference_in", TOP_CIRCUMFERENCE_IN, "in",
     "Circumference where the usable trunk ends, from the brief."),
    ("chainsaw_kerf_in", CHAINSAW_KERF_IN, "in",
     "Ripping chainsaw kerf, from the brief."),
    ("connector_face_in", CONNECTOR_FACE_IN, "in",
     "A dressed two-by-four's face width, the yardstick for a connector."),
)


# ======================================================================
# The family at equal area -- the executive finding
# ======================================================================

def diameter_for_area(area_in2: float, splits: int) -> float:
    """Trunk diameter whose one-``splits`` sector has gross area ``area_in2``.

    A sector is ``pi R^2 / splits``, so ``R = sqrt(area * splits / pi)``.
    This is the diameter at which the family holds exactly a two-by-four's
    worth of wood, which is the only fair way to compare their *shapes*.
    """
    radius = math.sqrt(area_in2 * splits / math.pi)
    return 2.0 * radius


@dataclass(frozen=True)
class FamilyRow:
    """One split family, sized to a fixed cross-sectional area."""

    splits: int
    angle_deg: float
    radial_depth_in: float          # pith to bark: R
    outer_chord_in: float           # width across the bark face
    area_in2: float
    i_strong_in4: float             # second moment about the weak-bending axis
    i_weak_in4: float               # second moment about the strong-bending axis
    s_min_in3: float                # worst-case section modulus, strong direction
    i_strong_vs_stud: float
    i_weak_vs_stud: float
    s_vs_stud: float

    @property
    def name(self) -> str:
        return family_name(self.splits)


@lru_cache(maxsize=8)
def equal_area_families(area_in2: float | None = None,
                        families: tuple[int, ...] = FAMILIES) -> tuple[FamilyRow, ...]:
    """Each split family holding the same gross area as a dressed two-by-four.

    The comparison is purely geometric.  It says nothing about the wood; it
    says what *shape* the saw makes when it splits a log that finely, and the
    pattern is the whole point: strong-axis second moment climbs with the
    split while weak-axis second moment falls, because the same wood is being
    stretched into a deeper, narrower blade.
    """
    stud = yf.dressed_stud()
    target = stud.area_in2 if area_in2 is None else area_in2
    rows: list[FamilyRow] = []
    for splits in families:
        diameter = diameter_for_area(target, splits)
        section = yf.sector_at_diameter(round(diameter, 6), splits)
        rows.append(FamilyRow(
            splits=splits,
            angle_deg=family_angle_deg(splits),
            radial_depth_in=diameter * 0.5,
            outer_chord_in=2.0 * (diameter * 0.5) * math.sin(math.pi / splits),
            area_in2=section.area_in2,
            i_strong_in4=section.i_yy_in4,
            i_weak_in4=section.i_zz_in4,
            s_min_in3=section.section_modulus_in3,
            i_strong_vs_stud=section.i_yy_in4 / stud.i_yy_in4,
            i_weak_vs_stud=section.i_zz_in4 / stud.i_zz_in4,
            s_vs_stud=section.section_modulus_in3 / stud.section_modulus_in3,
        ))
    return tuple(rows)


# ======================================================================
# The connection law -- the two limits a built-up member lives between
# ======================================================================

@dataclass(frozen=True)
class BundleBound:
    """One built-up arrangement, at its loose and its composite limits."""

    label: str
    members: int
    i_independent_in4: float        # parts that slide freely: sum of their own I
    i_composite_in4: float          # parts rigidly coupled: one transformed section

    @property
    def premium(self) -> float:
        """How much stiffer the composite limit is than the loose one."""
        return self.i_composite_in4 / self.i_independent_in4


@lru_cache(maxsize=8)
def lamina_stack_bounds(counts: tuple[int, ...] = (1, 2, 4, 8)) -> tuple[BundleBound, ...]:
    """Stack ``n`` identical planks to ``n`` times the depth, two ways.

    This is the law in its cleanest form, shown on the plank everyone already
    knows -- a dressed two-by-four -- because the number comes out exact.
    Loose, the stack is ``n`` planks each bending about its own centroid, so
    its stiffness is ``n`` times one plank's.  Glued into one section the
    parallel-axis theorem carries the outer laminae far from the shared
    neutral axis, and for a rectangle the stiffness grows with ``n`` cubed --
    so the ratio of the two limits is exactly ``n`` squared.  That factor,
    computed here rather than asserted, is why "add wood" and "add a stiffer
    beam" are not the same sentence until a connection carries the shear
    between the layers.  (A wedge chord does better still, because its own
    second moment is a smaller share of ``A*depth^2``; that case is
    :func:`separated_chord_bounds`.)
    """
    one = yf.dressed_stud()
    depth = one.depth_in
    bounds: list[BundleBound] = []
    for n in counts:
        independent = n * one.i_yy_in4
        # n laminae stacked contiguously; each centroid offset from the stack
        # centroid by a multiple of the plank depth.
        composite = 0.0
        for k in range(n):
            offset = (k - (n - 1) / 2.0) * depth
            composite += one.i_yy_in4 + one.area_in2 * offset * offset
        bounds.append(BundleBound(f"{n} stacked", n, independent, composite))
    return tuple(bounds)


@dataclass(frozen=True)
class ChordBound:
    """A separated-chord beam at one flange spacing."""

    separation_depths: float        # centre-to-centre spacing, in chord depths
    centre_distance_in: float
    i_independent_in4: float
    i_composite_in4: float

    @property
    def premium(self) -> float:
        return self.i_composite_in4 / self.i_independent_in4


@lru_cache(maxsize=8)
def separated_chord_bounds(splits: int = 8, area_in2: float | None = None,
                           separations: tuple[float, ...] = (1.0, 2.0, 3.0)) -> tuple[ChordBound, ...]:
    """Two sector chords held apart by a web, at a range of spacings.

    This is the beam the research precedent actually built (see
    :data:`SOURCES`): opposing sectors as top and bottom flanges, a light
    shear web between them.  Fully coupled, the beam's stiffness is
    ``2(I_chord + A_chord (h/2)^2)``; loose, it is ``2 I_chord``.  The gap
    between those two numbers is the work the web and its connectors have to
    do, and it grows with the square of the spacing -- which is the whole
    reason to separate the chords instead of bundling them at the middle.
    """
    stud = yf.dressed_stud()
    target = stud.area_in2 if area_in2 is None else area_in2
    diameter = diameter_for_area(target, splits)
    chord = yf.sector_at_diameter(round(diameter, 6), splits)
    depth = chord.depth_in
    bounds: list[ChordBound] = []
    for factor in separations:
        centre = factor * depth
        independent = 2.0 * chord.i_yy_in4
        composite = 2.0 * (chord.i_yy_in4 + chord.area_in2 * (centre * 0.5) ** 2)
        bounds.append(ChordBound(factor, centre, independent, composite))
    return tuple(bounds)


# ======================================================================
# The pairing rules -- opposite sector, reversed taper
# ======================================================================

def opposite_mate(index: int, splits: int) -> int:
    """The sector from the far side of the same log: ``i + N/2 (mod N)``.

    Pairing a sector with its diametric opposite puts two pieces that saw the
    same weather, the same lean and the same pith on either side of a joint,
    so what is different about each tends to cancel rather than add.
    """
    return (index + splits // 2) % splits


def opposite_pairs(splits: int) -> tuple[tuple[int, int], ...]:
    """Every sector paired with its diametric mate, each pair once."""
    return tuple((i, opposite_mate(i, splits)) for i in range(splits // 2))


# The dyad, stated once so the book and a future film cannot describe it
# differently: the opposite sector, turned end for end so the fat end of one
# lands against the thin end of the other and the taper averages out.
DYAD = {
    "mate": "opposite sector (i + N/2 mod N)",
    "reversal": "end-for-end, fat-to-thin",
    "result": "a symmetric two-piece primitive with two broad outer faces and "
              "two independent longitudinal load paths",
}


# ======================================================================
# The selection gates -- is this split usable at this size?
# ======================================================================

@dataclass(frozen=True)
class GateRow:
    """One split family scored at one trunk size."""

    splits: int
    gross_area_in2: float           # before kerf, bark and defects
    area_vs_stud: float
    outer_arc_pitch_in: float
    outer_chord_in: float
    chord_vs_connector: float
    kerf_fraction: float            # kerf as a share of the outer arc pitch

    @property
    def name(self) -> str:
        return family_name(self.splits)


def three_gate(circumference_in: float, kerf_in: float = CHAINSAW_KERF_IN,
               families: tuple[int, ...] = FAMILIES) -> tuple[GateRow, ...]:
    """Score every split family at a trunk of this circumference.

    Three gates, because a wedge can pass one and fail another:

    * **area** -- is there a stick's worth of wood in the sector at all?
      Gross sector area is ``C^2 / (4 pi N)``.
    * **connection** -- is the bark face wide enough to land a connector on?
      Compared with a conventional two-by-four's face.
    * **kerf** -- how much of the sector's share of the rim does one saw cut
      eat?  ``kerf * N / C`` of the outer arc pitch.
    """
    stud = yf.dressed_stud()
    log_area = circumference_in ** 2 / (4.0 * math.pi)
    rows: list[GateRow] = []
    for splits in families:
        gross = log_area / splits
        arc_pitch = circumference_in / splits
        chord = (circumference_in / math.pi) * math.sin(math.pi / splits)
        rows.append(GateRow(
            splits=splits,
            gross_area_in2=gross,
            area_vs_stud=gross / stud.area_in2,
            outer_arc_pitch_in=arc_pitch,
            outer_chord_in=chord,
            chord_vs_connector=chord / CONNECTOR_FACE_IN,
            kerf_fraction=kerf_in / arc_pitch,
        ))
    return tuple(rows)


# ======================================================================
# Wood is directional, and the saw preserves it
# ======================================================================

ORTHOTROPY_AXES: tuple[tuple[str, str, str], ...] = (
    ("L", "longitudinal", "along the tree / the grain -- stiffest and strongest"),
    ("R", "radial", "pith to bark -- the sector's depth"),
    ("T", "tangential", "round the rings -- the sector's width"),
)
"""Wood's three material axes.  A radial split preserves all three on the
member instead of erasing them into an interchangeable rectangle, so a wedge
carries its own L-R-T frame: load it along L, let the depth be R."""


# ======================================================================
# What the grammar rests on -- cited, not derived
# ======================================================================

SOURCES: tuple[dict[str, str], ...] = (
    {"key": "xr_beam",
     "cite": "Fereday & Meech, XR Beam (radial-sawn roundwood beam)",
     "finding": "Cut roundwood into eight longitudinal sectors, paired opposing "
                "sectors as upper and lower chords with plywood shear webs, and "
                "reversed one member end-for-end so a thick end met a thin end. "
                "Aim: cut conversion waste and keep fibre continuity round knots.",
     "caveat": "Experimental; the paired-chord beam this grammar uses is their "
               "topology."},
    {"key": "radial_wedge_2023",
     "cite": "2023 radial-wedge / cleft-timber research (sweet chestnut)",
     "finding": "Radial wedges made floor beams and A-frames; short cleft pieces "
                "with standardized steel nodes made a space frame. An eight-sector "
                "saw run on roughly 300 mm logs reported about 90% timber yield.",
     "caveat": "Prototypes were explicitly NOT graded or destructively tested to "
               "certified structural values; the 90% figure is for eight coarse "
               "sectors and does not carry to W32 or W64."},
    {"key": "usda_built_up",
     "cite": "USDA Wood Handbook -- built-up members and fastenings",
     "finding": "A built-up member's composite stiffness depends on the stiffness "
                "and spacing of its connectors: rigidly connected it approaches one "
                "transformed section, unconnected it behaves as independent beams, "
                "and mechanical fasteners fall between because the interface slips.",
     "caveat": "The reason this module reports a loose AND a composite limit "
               "rather than one number."},
    {"key": "usda_juvenile",
     "cite": "USDA -- juvenile wood in loblolly pine",
     "finding": "Increasing juvenile-wood content reduced tested properties by as "
                "much as roughly 30%, and transverse properties were sensitive to "
                "growth-ring orientation.",
     "caveat": "Species-specific; a reason not to assume a sector's pith point is "
               "as good as its outer wood, and the case for truncating it."},
    {"key": "codes",
     "cite": "CSA O86:24; BC Building Code 2024 alternative solutions",
     "finding": "A new structural system reaches approval as an alternative "
                "solution: engineering analysis plus material, connection and "
                "component testing that demonstrates the required performance.",
     "caveat": "Vancouver uses its own building by-law rather than the provincial "
               "code."},
)


# ======================================================================
# Worked blocks for the book's ``grammar`` tokens.  Each returns a list of
# lines whose LAST line is the conclusion; the book's token wrapper drops it
# and says it in prose, exactly as the ``work.*`` blocks do.
# ======================================================================

def steps_families() -> list[str]:
    stud = yf.dressed_stud()
    rows = equal_area_families()
    out = [
        "HOLD THE WOOD CONSTANT, SPLIT IT FINER",
        f"  every row below has the same {stud.area_in2:.2f} sq in of wood as a dressed 2x4",
        "",
        f"  {'':6}{'angle':>7}{'depth':>8}{'chord':>8}"
        f"{'I strong':>10}{'I weak':>9}{'S min':>8}",
        f"  {'2x4':6}{'--':>7}{stud.depth_in:8.2f}{yf.DRESSED_STUD_IN[0]:8.2f}"
        f"{stud.i_yy_in4:10.2f}{stud.i_zz_in4:9.3f}{stud.section_modulus_in3:8.2f}",
    ]
    for r in rows:
        out.append(
            f"  {r.name:6}{r.angle_deg:>6.4g}{chr(176):>1}{r.radial_depth_in:8.2f}"
            f"{r.outer_chord_in:8.2f}{r.i_strong_in4:10.2f}{r.i_weak_in4:9.3f}"
            f"{r.s_min_in3:8.2f}")
    w32 = next(r for r in rows if r.splits == 32)
    out.append("")
    out.append(
        f"  a W32 of the same wood has {w32.i_strong_vs_stud:.2f}x the 2x4's strong-axis I "
        f"and {w32.i_weak_vs_stud:.2f}x its weak -- a blade")
    return out


def steps_composite() -> list[str]:
    stack = lamina_stack_bounds()
    chords = separated_chord_bounds()
    out = [
        "A BUNDLE IS NOT A BEAM UNTIL THE SHEAR IS CARRIED",
        "",
        "  n planks (dressed 2x4) stacked to n times the depth, two limits:",
        f"  {'n':>4}{'loose I':>11}{'composite I':>13}{'ratio':>8}",
    ]
    for b in stack:
        out.append(f"  {b.members:>4}{b.i_independent_in4:11.1f}"
                   f"{b.i_composite_in4:13.1f}{b.premium:7.2f}x")
    out.append("")
    out.append("  two chords held apart by a web, by centre spacing (W8 chords):")
    out.append(f"  {'spacing':>9}{'loose I':>11}{'composite I':>13}{'ratio':>8}")
    for c in chords:
        out.append(f"  {c.separation_depths:>7.0f}d{c.i_independent_in4:11.1f}"
                   f"{c.i_composite_in4:13.1f}{c.premium:7.2f}x")
    out.append("")
    out.append("  the real member sits between the two limits; where exactly is a "
               "test, not a formula")
    return out


def steps_gates() -> list[str]:
    out = [
        "IS THIS SPLIT USABLE AT THIS SIZE?",
        "",
    ]
    for label, circ in (("fat end", BUTT_CIRCUMFERENCE_IN),
                        ("thin end", TOP_CIRCUMFERENCE_IN)):
        out.append(f"  {label}, {circ:.0f} in round:")
        out.append(f"    {'':6}{'gross A':>9}{'vs 2x4':>8}{'chord':>8}"
                   f"{'vs conn':>9}{'kerf %':>9}")
        for g in three_gate(circ):
            out.append(
                f"    {g.name:6}{g.gross_area_in2:9.2f}{g.area_vs_stud:7.2f}x"
                f"{g.outer_chord_in:8.2f}{g.chord_vs_connector:8.2f}x"
                f"{g.kerf_fraction * 100:8.1f}%")
        out.append("")
    out.append("  at the fat end W32 is the finest split still holding a 2x4's "
               "wood; W64 does not")
    return out


def steps_pairing() -> list[str]:
    pairs = opposite_pairs(32)
    out = [
        "EVERY SECTOR HAS A MATE FROM THE FAR SIDE OF THE LOG",
        "  W32: pair i with i + 16, then turn one end for end so the taper cancels",
        "",
    ]
    shown = [f"{a:02d}-{b:02d}" for a, b in pairs[:4]] + ["..."] \
        + [f"{pairs[-1][0]:02d}-{pairs[-1][1]:02d}"]
    out.append("  " + "   ".join(shown))
    out.append("")
    out.append("  the dyad: opposite sector, reversed end for end -- a symmetric "
               "two-piece primitive")
    return out


def sources_table() -> str:
    """The cited precedent, as a block of attributed lines for the book."""
    out: list[str] = []
    for s in SOURCES:
        out.append(f"- **{s['cite']}.** {s['finding']} *({s['caveat']})*")
    return "\n".join(out)


# ======================================================================
# Audit and proof
# ======================================================================

def report() -> str:
    """A plain-text audit of every figure the grammar puts on a page."""
    lines = ["WEDGE STRUCTURAL GRAMMAR -- CALCULATION AUDIT", ""]
    lines += steps_families()
    lines += [""] + steps_composite()
    lines += [""] + steps_gates()
    lines += [""] + steps_pairing()
    lines += ["", "External constants declared by this module:"]
    for key, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {key} = {value} {units}  ({source})")
    lines += ["", "Cited precedent (not derived here):"]
    for s in SOURCES:
        lines.append(f"  {s['cite']}")
    return "\n".join(lines)


def validate_wedge_grammar() -> None:
    """Prove the grammar before a word of the book rests on it."""
    stud = yf.dressed_stud()

    # The equal-area table must reproduce the values the chapter prints, which
    # are the same values the dome's own Section produces.  These are the
    # hand-checked targets from the source analysis.
    rows = {r.splits: r for r in equal_area_families()}
    assert abs(rows[8].i_strong_in4 - 3.72) < 0.02, rows[8].i_strong_in4
    assert abs(rows[8].i_weak_in4 - 1.75) < 0.02, rows[8].i_weak_in4
    assert abs(rows[8].s_min_in3 - 1.57) < 0.02, rows[8].s_min_in3
    assert abs(rows[32].i_strong_in4 - 15.55) < 0.05, rows[32].i_strong_in4
    assert abs(rows[32].i_weak_in4 - 0.450) < 0.01, rows[32].i_weak_in4
    assert abs(rows[64].i_strong_in4 - 31.17) < 0.1, rows[64].i_strong_in4
    for r in equal_area_families():
        assert abs(r.area_in2 - stud.area_in2) < 1e-3, r

    # The central claim: split finer and the blade sharpens.  Strong-axis I
    # rises, weak-axis I falls, worst-case modulus rises, monotonically.
    strong = [r.i_strong_in4 for r in equal_area_families()]
    weak = [r.i_weak_in4 for r in equal_area_families()]
    smin = [r.s_min_in3 for r in equal_area_families()]
    assert all(a < b for a, b in zip(strong, strong[1:])), strong
    assert all(a > b for a, b in zip(weak, weak[1:])), weak
    assert all(a < b for a, b in zip(smin, smin[1:])), smin
    # And a fine sector really is worse than the stud across the grain.
    assert rows[32].i_weak_vs_stud < 0.5, rows[32].i_weak_vs_stud
    assert rows[32].i_strong_vs_stud > 2.5, rows[32].i_strong_vs_stud

    # The connection law.  The composite limit beats the loose one, the stack
    # ratio is n squared, and the chord premium grows with spacing.
    stack = lamina_stack_bounds()
    for b in stack:
        assert b.premium >= 1.0 - 1e-9, b
        assert abs(b.premium - b.members ** 2) < 1e-6, (b.members, b.premium)
    chords = separated_chord_bounds()
    prem = [c.premium for c in chords]
    assert all(a < b for a, b in zip(prem, prem[1:])), prem
    assert prem[0] > 1.0, prem

    # Pairing is diametric and involutive.
    for n in (8, 16, 32):
        for i in range(n):
            assert opposite_mate(opposite_mate(i, n), n) == i
            assert (opposite_mate(i, n) - i) % n == n // 2
        assert len(opposite_pairs(n)) == n // 2

    # The gates.  Area per sector falls as the split rises; kerf share rises;
    # and the fat-end W32 still carries a stud's wood while W64 does not.
    fat = {g.splits: g for g in three_gate(BUTT_CIRCUMFERENCE_IN)}
    areas = [g.gross_area_in2 for g in three_gate(BUTT_CIRCUMFERENCE_IN)]
    kerfs = [g.kerf_fraction for g in three_gate(BUTT_CIRCUMFERENCE_IN)]
    assert all(a > b for a, b in zip(areas, areas[1:])), areas
    assert all(a < b for a, b in zip(kerfs, kerfs[1:])), kerfs
    assert fat[32].area_vs_stud > 1.0 > fat[64].area_vs_stud, fat
    assert abs(fat[8].gross_area_in2 - 23.88) < 0.05, fat[8].gross_area_in2
    # Kerf really does become punishing: a quarter-inch cut is a third of a
    # W64 sector's share of the rim at the fat end.
    assert fat[64].kerf_fraction > 0.30, fat[64].kerf_fraction

    # Every worked block ends on a conclusion the token wrapper can drop.
    for fn in (steps_families, steps_composite, steps_gates, steps_pairing):
        block = fn()
        assert len(block) >= 3 and block[-1].strip(), fn.__name__

    # The precedent is cited with a caveat on every row, because not one line
    # of it is a rating.
    assert SOURCES
    for s in SOURCES:
        assert s["cite"] and s["finding"] and s["caveat"], s


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = sys.argv[1:] if argv is None else argv
    if "--check" in argv:
        validate_wedge_grammar()
        print("wedge_grammar ok")
        return 0
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
