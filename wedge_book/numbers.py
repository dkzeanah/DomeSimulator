"""Every number this book prints, and where it came from.

The rule in this repository is that a figure on a page traces back to code
that derives it. A book is the hardest place to keep that rule, because prose
is where a number goes to get copied: somebody writes ``70.182`` into a
sentence, the solver changes, and the sentence is still there being confidently
wrong three chapters later.

So this module does two things.

**It publishes the numbers.** :func:`quantities` returns the reference build's
solved facts as named values with a unit and the function that produced each
one. :func:`resolve` substitutes them into text as ``{{name}}``, so a section
that wants the short chord can ask for it instead of typing it.

**It audits the ones already typed.** The book was written before this module
existed and it has a hundred and eighty high-precision figures in it.
:func:`audit` finds every number in the prose carrying three or more decimal
places -- the precision nobody invents by hand, so every one of them is a
claim about a solve -- and checks it against the pool of values the code can
actually produce. :func:`validate_numbers` fails if any of them is not in
that pool.

That catches the specific way a technical book rots. Not a typo: a figure
that was right when it was written, against a model that has since moved.

WHAT THE REFERENCE BUILD IS

One dome, stated once, and every chapter means this one unless it says
otherwise:

* the long member's chord is **72 inches**, which is the six-foot stick the
  whole product line is named after;
* the short member's chord is what the geometry then forces, **63.670
  inches** -- not a second choice, a consequence;
* the wedge's point faces **into the dome**;
* and it is built by the wedge method, so the members are split log sectors
  and the joint is a pinwheel.

:func:`validate_numbers` checks all four against the live solve, because those
are the sentences every other number in the book hangs off.
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import store

SOLVER = store.ROOT / "geodesic_raw_wedge_dome_dihedral.py"

#: The reference build, in the one form every tool here understands.
REFERENCE: dict[str, object] = {
    "long_edge_in": 72.0,
    "wedge_orientation": "point_dome_in",
    "radial_splits": 8,
    "trunk_diameter_in": 12.0,
}

#: What the short chord has to come out at, given the long one. Stated here so
#: the check has something to compare against that is not itself the solve.
#: 2V icosahedral chord factors: A = 0.618034 r, B = 0.546533 r.
SHORT_CHORD_IN = 72.0 * (0.5465330581 / 0.6180339887)


def solver():
    """The raw-wedge solver as a module, loaded once.

    Imported by path rather than by name because it is a single-file tool that
    lives at the repository root and is not a package.
    """
    existing = sys.modules.get("_wedge_book_solver")
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location("_wedge_book_solver", SOLVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_wedge_book_solver"] = module
    spec.loader.exec_module(module)
    return module


def reference_model(**overrides):
    """The solved reference build. ``overrides`` change one thing about it."""
    rw = solver()
    config = rw.DomeConfig(**{**REFERENCE, **overrides})
    config.validate()
    return rw.build_physical_model(config)


# ----------------------------------------------------------------------
# The named quantities
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Quantity:
    """One number the book may print, with its unit and its origin."""

    name: str
    value: float
    unit: str
    source: str
    digits: int = 3

    def text(self) -> str:
        if self.digits == 0:
            return f"{self.value:,.0f}"
        return f"{self.value:,.{self.digits}f}"


def quantities() -> dict[str, Quantity]:
    """The reference build's facts, by name.

    Everything here is read out of a solve. Nothing in this function chooses
    a value; the only literals are the reference build's own inputs, which are
    in :data:`REFERENCE` and are inputs precisely because they are choices.
    """
    import seed_world
    import two_v_demo.wedge_geometry as wedge
    from two_v_demo import wedge_why_facts

    geometry = seed_world.geometry()
    model = reference_model()
    topology = model.topology
    cut = wedge_why_facts.butt_cut_model()

    def q(name: str, value: float, unit: str, source: str,
          digits: int = 3) -> tuple[str, Quantity]:
        return name, Quantity(name, float(value), unit, source, digits)

    a_members = [m for m in model.members if m.edge_type == "A"]
    b_members = [m for m in model.members if m.edge_type == "B"]
    a_seams = [s for s in model.seams if s.edge_type == "A"]
    b_seams = [s for s in model.seams if s.edge_type == "B"]
    aaa = next(f for f in geometry.faces if f.name == "AAA")
    bab = next(f for f in geometry.faces if f.name == "BAB")
    a_class = next(m for m in geometry.members if m.edge_type == "A")
    b_class = next(m for m in geometry.members if m.edge_type == "B")

    rows = [
        # -- the dome ------------------------------------------------
        q("radius_in", topology.sphere_radius_in, "in",
          "solver topology.sphere_radius_in", 4),
        q("diameter_ft", geometry.diameter_ft, "ft",
          "seed_world.geometry().diameter_ft"),
        q("height_ft", geometry.height_ft, "ft",
          "seed_world.geometry().height_ft"),
        q("floor_sqft", geometry.floor_decagon_sqft, "sq ft",
          "seed_world.geometry().floor_decagon_sqft", 0),
        q("floor_circle_sqft", geometry.floor_circle_sqft, "sq ft",
          "seed_world.geometry().floor_circle_sqft", 0),
        q("panel_sqft", geometry.panel_sqft, "sq ft",
          "seed_world.geometry().panel_sqft", 0),
        q("spherical_sqft", geometry.spherical_sqft, "sq ft",
          "seed_world.geometry().spherical_sqft", 0),
        q("base_perimeter_ft", geometry.base_perimeter_ft, "ft",
          "seed_world.geometry().base_perimeter_ft", 0),

        # -- the two chords ------------------------------------------
        q("a_chord_in", topology.long_edge_in, "in",
          "solver topology.long_edge_in"),
        q("b_chord_in", topology.short_edge_in, "in",
          "solver topology.short_edge_in"),
        q("a_factor", topology.long_edge_in / topology.sphere_radius_in, "",
          "A chord / radius", 6),
        q("b_factor", topology.short_edge_in / topology.sphere_radius_in, "",
          "B chord / radius", 6),

        # -- the sticks ----------------------------------------------
        q("a_cut_in", a_class.stock_length_in, "in",
          "seed_world member class A stock_length_in"),
        q("b_cut_in", b_class.stock_length_in, "in",
          "seed_world member class B stock_length_in"),
        q("a_cut_min_in", min(m.physical_stock_length_in for m in a_members),
          "in", "solver: shortest A member"),
        q("b_cut_min_in", min(m.physical_stock_length_in for m in b_members),
          "in", "solver: shortest B member"),
        q("a_axis_in", a_class.axis_length_in, "in",
          "seed_world member class A axis_length_in"),
        q("b_axis_in", b_class.axis_length_in, "in",
          "seed_world member class B axis_length_in"),
        q("a_bite_in", topology.long_edge_in - a_class.stock_length_in, "in",
          "A chord minus A cut"),
        q("b_bite_in", topology.short_edge_in - b_class.stock_length_in, "in",
          "B chord minus B cut"),
        q("member_width_in", geometry.member_width_in, "in",
          "seed_world.geometry().member_width_in"),
        q("member_depth_in", geometry.member_depth_in, "in",
          "seed_world.geometry().member_depth_in", 1),
        q("member_count", geometry.member_count, "members",
          "seed_world.geometry().member_count", 0),
        q("member_stock_ft", geometry.member_stock_ft, "ft",
          "seed_world.geometry().member_stock_ft", 0),
        q("member_section_in2", geometry.member_section_in2, "sq in",
          "seed_world.geometry().member_section_in2"),

        # -- the counts ----------------------------------------------
        q("face_count", len(topology.faces), "panels",
          "solver: len(topology.faces)", 0),
        q("vertex_count", len(topology.vertices), "vertices",
          "solver: len(topology.vertices)", 0),
        q("edge_count", len(topology.edges), "edges",
          "solver: len(topology.edges)", 0),
        q("seam_count", geometry.seam_count, "seams",
          "seed_world.geometry().seam_count", 0),
        q("base_sides", geometry.base_sides, "sides",
          "seed_world.geometry().base_sides", 0),
        q("aaa_count", aaa.count, "panels", "AAA face class count", 0),
        q("bab_count", bab.count, "panels", "BAB face class count", 0),

        # -- the panels ----------------------------------------------
        q("aaa_sqft", aaa.area_sqft, "sq ft", "AAA face area"),
        q("bab_sqft", bab.area_sqft, "sq ft", "BAB face area"),
        q("aaa_min_width_in", aaa.min_width_in, "in", "AAA narrowest width"),
        q("bab_min_width_in", bab.min_width_in, "in", "BAB narrowest width"),
        q("aaa_perimeter_in", aaa.perimeter_in, "in", "AAA perimeter"),
        q("bab_perimeter_in", bab.perimeter_in, "in", "BAB perimeter"),

        # -- the seams -----------------------------------------------
        q("a_fold_deg", a_seams[0].fold_angle_deg, "deg",
          "solver seam A fold_angle_deg"),
        q("b_fold_deg", b_seams[0].fold_angle_deg, "deg",
          "solver seam B fold_angle_deg"),
        q("a_gap_deg", a_seams[0].raw_gap_angle_deg, "deg",
          "solver seam A raw_gap_angle_deg"),
        q("b_gap_deg", b_seams[0].raw_gap_angle_deg, "deg",
          "solver seam B raw_gap_angle_deg"),
        q("a_spline_base_in", a_seams[0].spacer_base_width_in, "in",
          "solver seam A spacer_base_width_in"),
        q("b_spline_base_in", b_seams[0].spacer_base_width_in, "in",
          "solver seam B spacer_base_width_in"),
        q("a_hose_max_in", a_seams[0].hose_max_diameter_in, "in",
          "solver seam A hose_max_diameter_in"),
        q("b_hose_max_in", b_seams[0].hose_max_diameter_in, "in",
          "solver seam B hose_max_diameter_in"),
        q("seam_run_ft", geometry.seam_length_in / 12.0, "ft",
          "seed_world seam_length_in / 12", 0),

        # -- the cut -------------------------------------------------
        q("bevel_deg", cut["bevel_deg"], "deg",
          "wedge_why_facts.butt_cut_model()['bevel_deg']", 1),
        q("mitre_settings", cut["setting_count"], "settings",
          "wedge_why_facts.butt_cut_model()['setting_count']", 0),
        q("sector_deg", 360.0 / int(REFERENCE["radial_splits"]), "deg",
          "360 / radial_splits", 1),

        # -- the log -------------------------------------------------
        q("band_bite_in",
          _band_model_bite(geometry.radius_in, geometry.member_width_in,
                           topology.long_edge_in / topology.sphere_radius_in,
                           wedge),
          "in", "wedge_geometry.pinwheel_panels: the band model's bite"),
        q("trunk_diameter_in", float(REFERENCE["trunk_diameter_in"]), "in",
          "REFERENCE['trunk_diameter_in']", 1),
        q("radial_splits", float(REFERENCE["radial_splits"]), "sectors",
          "REFERENCE['radial_splits']", 0),
    ]
    for mitre in cut.get("mitres_deg", ()):
        rows.append(q(f"mitre_{mitre:.0f}_deg", mitre, "deg",
                      "wedge_why_facts butt_cut_model mitres_deg"))
    return dict(rows)


def _band_model_bite(radius_in: float, width_in: float, a_factor: float,
                     wedge) -> float:
    """The *other* model's bite, which the book quotes to disown it.

    A member treated as a rectangular band lying on the edge line loses far
    more to the pinwheel than a log sector does. The book prints both and says
    which one it is cut to, so the number has to be derived here too.
    """
    panels = wedge.pinwheel_panels(radius_in, width_in)
    longest = max(m.length_in for p in panels for m in p.members)
    return radius_in * a_factor - longest


# ----------------------------------------------------------------------
# Substitution
# ----------------------------------------------------------------------

TOKEN = re.compile(r"\{\{\s*([a-z0-9_]+)\s*(?::\s*([^}]+?))?\s*\}\}")


def resolve(text: str, values: dict[str, Quantity] | None = None) -> str:
    """Replace ``{{name}}`` with the live number. ``{{name:.1f}}`` formats it."""
    values = values if values is not None else quantities()

    def swap(match: re.Match) -> str:
        name, spec = match.group(1), match.group(2)
        found = values.get(name)
        if found is None:
            raise KeyError(f"no such quantity {name!r}; have "
                           f"{sorted(values)[:6]}... ({len(values)} total)")
        if spec:
            return format(found.value, spec.strip())
        return found.text()

    return TOKEN.sub(swap, text)


# ----------------------------------------------------------------------
# The audit
# ----------------------------------------------------------------------

#: Diameters the builder's reference tabulates, in feet.
TABLE_DIAMETERS_FT: tuple[float, ...] = (
    8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 30.0)


def strut_table() -> list[dict]:
    """The published cut list, at every diameter the book tabulates.

    Chord scales with the dome. The bite does not -- it is set by how wide the
    member is -- so the cut is the chord minus a constant, and this is the
    arithmetic the book's table is printed from.
    """
    values = quantities()
    a_factor = values["a_factor"].value
    b_factor = values["b_factor"].value
    a_bite = values["a_bite_in"].value
    b_bite = values["b_bite_in"].value
    reference_ft = values["diameter_ft"].value

    rows = []
    for diameter_ft in sorted(set(TABLE_DIAMETERS_FT) | {reference_ft}):
        radius_ft = diameter_ft / 2.0
        radius_in = radius_ft * 12.0
        a_chord = radius_in * a_factor
        b_chord = radius_in * b_factor
        rows.append({
            "diameter_ft": diameter_ft,
            "radius_ft": radius_ft,
            "a_chord_in": a_chord,
            "b_chord_in": b_chord,
            "a_cut_in": a_chord - a_bite,
            "b_cut_in": b_chord - b_bite,
            "reference": abs(diameter_ft - reference_ft) < 5.0e-3,
        })
    return rows


def value_pool() -> dict[float, str]:
    """Every number the code can produce, mapped to what produced it.

    The audit's haystack. It is deliberately wider than the named quantities:
    it includes every seam's angles and every member's length, because the
    book quotes individual members and seams, and the whole strut table at
    every diameter, because that is a page of the builder's reference.
    """
    import seed_world
    import two_v_demo.wedge_geometry as wedge
    from two_v_demo import wedge_why_facts

    pool: dict[float, str] = {}

    def add(value, why: str) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if not math.isfinite(number):
            return
        pool.setdefault(round(abs(number), 6), why)

    for name, quantity in quantities().items():
        add(quantity.value, f"{name} ({quantity.source})")

    model = reference_model()
    for member in model.members:
        add(member.physical_stock_length_in,
            f"{member.member_id} stock length")
        add(member.physical_axis_length_in, f"{member.member_id} axis length")
        add(member.nominal_length_in, f"{member.member_id} nominal length")
        add(member.point_offset_in, f"{member.member_id} point offset")
        add(member.butt_setback_in, f"{member.member_id} butt setback")
        add(member.receiving_axis_setback_in,
            f"{member.member_id} receiving setback")
    for seam in model.seams:
        add(seam.fold_angle_deg, f"{seam.seam_id} fold angle")
        add(seam.internal_dihedral_deg, f"{seam.seam_id} internal dihedral")
        add(seam.raw_gap_angle_deg, f"{seam.seam_id} raw gap angle")
        add(seam.spacer_base_width_in, f"{seam.seam_id} spline base")
        add(seam.contact_depth_in, f"{seam.seam_id} contact depth")
        add(seam.hose_max_diameter_in, f"{seam.seam_id} max hose")
        add(seam.member_point_offset_in, f"{seam.seam_id} point offset")
        add(180.0 - seam.internal_dihedral_deg,
            f"{seam.seam_id} exterior dihedral")
        add(45.0 - seam.fold_angle_deg, f"{seam.seam_id} sector minus fold")
    for row in strut_table():
        for key in ("diameter_ft", "radius_ft", "a_chord_in", "b_chord_in",
                    "a_cut_in", "b_cut_in"):
            add(row[key], f"strut table {row['diameter_ft']:.2f} ft {key}")
    for built in reference_designs():
        for key in ("diameter_ft", "radius_ft", "apex_ft", "a_chord_in",
                    "b_chord_in", "a_cut_in", "b_cut_in", "floor_sqft",
                    "shell_sqft", "timber_ft", "narrowest_in"):
            add(getattr(built, key), f"{built.section}: {key}")

    geometry = seed_world.geometry()
    for face in geometry.faces:
        add(face.area_sqft, f"{face.name} area")
        add(face.perimeter_in, f"{face.name} perimeter")
        add(face.min_width_in, f"{face.name} min width")
    for member in geometry.members:
        add(member.stock_length_in, f"{member.edge_type} class stock length")
        add(member.axis_length_in, f"{member.edge_type} class axis length")
        add(member.total_stock_ft, f"{member.edge_type} class total stock")

    cut = wedge_why_facts.butt_cut_model()
    for key, value in cut.items():
        if isinstance(value, (int, float)):
            add(value, f"butt_cut_model {key}")
        elif isinstance(value, (list, tuple)):
            for item in value:
                add(item, f"butt_cut_model {key}")

    plan = wedge.build_plan()
    for attribute in dir(plan):
        if attribute.startswith("_"):
            continue
        add(getattr(plan, attribute, None), f"wedge build_plan {attribute}")

    # Arithmetic the book does on its own figures: halves, doubles, sums of
    # the two chords, and the radius in feet. All of these appear in prose as
    # working shown, and all of them are derived rather than typed.
    for base in list(pool):
        add(base / 2.0, f"half of {pool[base]}")
        add(base * 2.0, f"twice {pool[base]}")
        add(base / 12.0, f"{pool[base]} in feet")
        add(base * 12.0, f"{pool[base]} in inches")
    # The conversion table states the reference build's radius in metres, so
    # the metric reading of every length is derivable too.
    for base in list(pool):
        add(base / 39.37007874015748, f"{pool[base]} in metres")
    # Pure geometry the text uses when it explains a triangle.
    add(math.sqrt(3.0) / 2.0, "sqrt(3)/2, the height of a unit triangle")
    add(math.sqrt(3.0), "sqrt(3)")
    add(math.pi, "pi")
    add((1.0 + math.sqrt(5.0)) / 2.0, "the golden ratio")
    return pool


#: Numbers with three or more decimals that are not measurements of this
#: dome, with the reason each one is allowed to stand.
ALLOWED: dict[str, str] = {
    "1.000": "unity, used when the text explains a ratio",
    "0.000": "zero, used when the text explains a difference",
    # Unit definitions. Nothing here derives them because nothing here can:
    # they are conventions, and the builder's reference prints them so a
    # reader can move between the tables and the simulator.
    "25.400": "millimetres in an inch, exactly, by definition",
    "304.800": "millimetres in a foot, exactly, by definition",
    "39.3701": "inches in a metre",
    "10.7639": "square feet in a square metre",
    "7.4805": "US gallons in a cubic foot",
}

PRECISE = re.compile(r"(?<![\d.])(\d+\.\d{3,})")


@dataclass(frozen=True)
class Unmatched:
    chapter: str
    section: str
    text: str
    count: int


def audit(book: store.Book | None = None,
          tolerance: float = 5.0e-4) -> list[Unmatched]:
    """Every high-precision number in the prose that the code cannot produce.

    Three decimal places is the threshold because it is the precision nobody
    reaches for in a sentence unless they are copying it out of a solve. Below
    it, a number may be a page count or a price or a round approximation;
    at or above it, it is a claim, and a claim that no function here produces
    is a claim that has drifted.
    """
    book = book or store.load_json()
    pool = value_pool()
    keys = sorted(pool)
    misses: list[Unmatched] = []

    def known(number: float) -> bool:
        if not keys:
            return False
        target = round(abs(number), 6)
        # A printed number is rounded, so the pool value it came from may
        # differ by up to half of the last printed digit.
        lo = target - tolerance
        hi = target + tolerance
        import bisect

        index = bisect.bisect_left(keys, lo)
        return index < len(keys) and keys[index] <= hi

    for _part, chapter, section in book.sections:
        found: dict[str, int] = {}
        for match in PRECISE.finditer(section.body or ""):
            text = match.group(1)
            if text in ALLOWED:
                continue
            # Match at the precision printed, not at full precision: the
            # book prints 72.000 for a value the solver holds as 72.0.
            decimals = len(text.split(".")[1])
            if known(float(text)) or known(
                    round(float(text), decimals)):
                continue
            found[text] = found.get(text, 0) + 1
        for text, count in sorted(found.items()):
            misses.append(Unmatched(chapter.title, section.title, text, count))
    return misses


def report() -> str:
    values = quantities()
    lines = ["THE REFERENCE BUILD", ""]
    for name, quantity in values.items():
        unit = f" {quantity.unit}" if quantity.unit else ""
        lines.append(f"  {name:<20} {quantity.text():>14}{unit:<8}"
                     f"  {quantity.source}")
    lines += ["", "THE STRUT TABLE", "",
              f"  {'diameter':>9}  {'A chord':>9}  {'B chord':>9}"
              f"  {'A cut':>9}  {'B cut':>9}"]
    for row in strut_table():
        mark = "  <- reference" if row["reference"] else ""
        lines.append(
            f"  {row['diameter_ft']:>8.2f}'  {row['a_chord_in']:>8.3f}\""
            f"  {row['b_chord_in']:>8.3f}\"  {row['a_cut_in']:>8.3f}\""
            f"  {row['b_cut_in']:>8.3f}\"{mark}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# The reference designs
# ----------------------------------------------------------------------

#: The sizes chapter 19 works through, and the section that carries each one.
DESIGNS: tuple[tuple[str, float], ...] = (
    ("Small demonstration dome", 8.0),
    ("12-foot dome", 12.0),
    ("16-foot dome", 16.0),
    ("20-foot reference dome", 0.0),   # 0 means "the reference build itself"
    ("Larger examples", 24.0),
)


@dataclass(frozen=True)
class Design:
    """One dome size, with every figure its page prints.

    Chapter 19 tabulates five of these and got two rows of each wrong, in the
    one way chapter 20 spends a page warning about: it scaled the pinwheel's
    bite with the dome. The bite is set by how wide the member is and a member
    does not get wider because the dome does, so the cut is the chord minus a
    constant. Scaling it made the eight-foot dome's sticks an inch too long
    and the twenty-four-foot dome's half an inch too short -- every stick.
    """

    section: str
    diameter_ft: float
    radius_ft: float
    apex_ft: float
    a_chord_in: float
    b_chord_in: float
    a_cut_in: float
    b_cut_in: float
    floor_sqft: float
    shell_sqft: float
    timber_ft: float
    narrowest_in: float
    reference: bool

    def table(self) -> str:
        """The block the section prints, laid out as the book lays it out."""
        return "\n".join((
            f"    {'diameter':<22}{self.diameter_ft:>10.2f} ft",
            f"    {'apex height':<22}{self.apex_ft:>10.2f} ft",
            f"    {'A strut, cut length':<22}{self.a_cut_in:>10.3f} in",
            f"    {'B strut, cut length':<22}{self.b_cut_in:>10.3f} in",
            f"    {'floor, inside the ring':<22}{self.floor_sqft:>10.1f} sq ft",
            f"    {'shell surface':<22}{self.shell_sqft:>10.1f} sq ft",
            f"    {'timber in the frame':<22}{self.timber_ft:>10.0f} ft",
        ))


def design(diameter_ft: float, section: str = "") -> Design:
    """One size of the reference dome, every figure derived.

    ``diameter_ft`` of zero means the reference build itself, so a caller does
    not have to restate 19.416 and risk restating it differently.
    """
    import seed_world

    values = quantities()
    geometry = seed_world.geometry()
    reference_ft = values["diameter_ft"].value
    if diameter_ft <= 0.0:
        diameter_ft = reference_ft

    radius_in = diameter_ft * 12.0 / 2.0
    scale = radius_in / values["radius_in"].value
    a_chord = radius_in * values["a_factor"].value
    b_chord = radius_in * values["b_factor"].value
    # The bite is constant. This is the whole point of the chapter.
    a_cut = a_chord - values["a_bite_in"].value
    b_cut = b_chord - values["b_bite_in"].value
    counts = {m.edge_type: m.count for m in geometry.members}
    timber_in = counts["A"] * a_cut + counts["B"] * b_cut
    return Design(
        section=section,
        diameter_ft=diameter_ft,
        radius_ft=diameter_ft / 2.0,
        # A hemisphere's apex is its radius.
        apex_ft=diameter_ft / 2.0,
        a_chord_in=a_chord,
        b_chord_in=b_chord,
        a_cut_in=a_cut,
        b_cut_in=b_cut,
        # Floor and surface go as the square of the radius; the frame's timber
        # does not, because the bite it loses at every joint does not scale.
        floor_sqft=geometry.floor_decagon_sqft * scale * scale,
        shell_sqft=geometry.panel_sqft * scale * scale,
        timber_ft=timber_in / 12.0,
        narrowest_in=values["bab_min_width_in"].value * scale,
        reference=abs(diameter_ft - reference_ft) < 5.0e-3,
    )


def reference_designs() -> tuple[Design, ...]:
    return tuple(design(diameter_ft, section)
                 for section, diameter_ft in DESIGNS)


# ----------------------------------------------------------------------
# Money
# ----------------------------------------------------------------------

def money() -> dict[str, Quantity]:
    """What the reference build costs, by name, out of the cost model.

    Separate from :func:`quantities` because it moves for different reasons.
    Geometry changes when somebody changes the dome; a price changes when
    somebody changes a price, and the book's dollar figures went stale twice
    over while its inches stayed right.
    """
    import hull_laminate
    import pad_deck
    import seed_model
    import soft_shell

    quote = seed_model.quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    bare = soft_shell.soft_shell(0)
    rows: dict[str, Quantity] = {}

    def q(name: str, value: float, source: str, unit: str = "USD",
          digits: int = 0) -> None:
        rows[name] = Quantity(name, float(value), unit, source, digits)

    q("price", quote.price, "seed_model.quote().price")
    q("cost_to_build", quote.cost_to_build,
      "seed_model.quote().cost_to_build")
    q("profit", quote.gross_profit, "seed_model.quote().gross_profit")
    q("price_per_sqft", quote.price_per_sqft,
      "seed_model.quote().price_per_sqft", "USD/sq ft", 2)
    q("material_cost", quote.material_cost, "seed_model.quote().material_cost")
    q("labour_cost", quote.labour_cost, "seed_model.quote().labour_cost")
    q("labour_hours", quote.labour_hours, "seed_model.quote().labour_hours",
      "hours", 1)
    q("overhead", quote.overhead, "seed_model.quote().overhead")
    q("pad_cost", quote.pad_cost, "seed_model.quote().pad_cost")
    q("hard_price", hard.price,
      "seed_model.quote(shell='hard').price")
    q("hard_cost", hard.cost_to_build,
      "seed_model.quote(shell='hard').cost_to_build")
    q("hard_premium", hard.price - quote.price,
      "hard-shell price minus shower-cap price")
    q("cap_bare", bare.cost, "soft_shell.soft_shell(0).cost")
    for group in quote.groups:
        q(f"group_{group.key}", group.cost,
          f"seed_model.quote() group {group.key!r}")
    q("mast", seed_model.mast_group().cost, "seed_model.mast_group().cost")
    q("dome_floor", seed_model.dome_floor_group().cost,
      "seed_model.dome_floor_group().cost")
    q("float_rig", seed_model.suspension_group().cost,
      "seed_model.suspension_group().cost")
    q("float_total",
      seed_model.mast_group().cost + seed_model.dome_floor_group().cost
      + seed_model.suspension_group().cost,
      "mast plus the dome's floor plus the floating rig")
    q("frame_weight_lb", seed_model.frame_weight_lb(),
      "seed_model.frame_weight_lb()", "lb")

    for deck in pad_deck.compare():
        q(f"pad_{deck.key}", deck.cost,
          f"pad_deck.deck({deck.key!r}) at "
          f"{pad_deck.pad_diameter_ft():.3f} ft")

    geometry = seed_model.seed_geometry()
    standoff = seed_model.declared("shell_standoff_in")
    outer = geometry.shell_sqft(
        standoff + seed_model.declared("shell_core_thickness_in"))
    inner = geometry.shell_sqft(standoff)
    for plan in hull_laminate.compare(outer, inner):
        q(f"laminate_{plan.system.key}_materials", plan.total_usd,
          f"hull_laminate.plan({plan.system.key!r}) materials")
    for system in hull_laminate.LAMINATES:
        try:
            priced = seed_model.quote("stem_cell", shell="hard",
                                      resin=system.key)
        except Exception:
            continue
        shell = priced.find("shell")
        if shell is not None:
            q(f"laminate_{system.key}", shell.cost,
              f"seed_model.quote(shell='hard', resin={system.key!r}) "
              f"shell group")

    for layers in (0, 1, 3, 7):
        for row in soft_shell.compare(layers):
            if row.layers != layers:
                continue
            q(f"hull_{layers}_layers", row.hard_usd,
              f"soft_shell.compare({layers}) hard")
            q(f"cap_{layers}_layers", row.soft_usd,
              f"soft_shell.compare({layers}) soft")
            q(f"saving_{layers}_layers", row.saving,
              f"soft_shell.compare({layers}) saving")
    return rows


# One optional space matched "$1,200" and missed "$    1,200", which is
# how a table sets a column of money -- so the audit skipped every
# generated table in the book and reported nothing wrong with them.
MONEY = re.compile(r"\$\s*([\d,]+)")


def money_pool() -> dict[int, str]:
    """Every dollar figure the cost model can produce, rounded to the dollar.

    Rounded because that is how the book prints them, and every line of every
    group is included because the book quotes individual lines -- the
    sub-panel, the drain stack, the seal cap.
    """
    import seed_model

    pool: dict[int, str] = {}

    def add(value, why: str) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if not math.isfinite(number) or number < 1.0:
            return
        pool.setdefault(int(round(number)), why)

    for name, quantity in money().items():
        add(quantity.value, f"{name} ({quantity.source})")

    for shell in ("soft", "hard"):
        for fitout in seed_model.FITOUT_ORDER:
            try:
                quote = seed_model.quote(fitout, shell=shell)
            except Exception:
                continue
            add(quote.price, f"{fitout}/{shell} price")
            add(quote.cost_to_build, f"{fitout}/{shell} cost")
            add(quote.delivered_price, f"{fitout}/{shell} delivered")
            for group in quote.groups:
                add(group.cost, f"{fitout}/{shell} group {group.key}")
                for line in group.lines:
                    add(line.cost,
                        f"{fitout}/{shell} {group.key}: {line.label[:40]}")
    try:
        build, floor = seed_model.floor_price()
        add(build, "seed_model.floor_price() build")
        add(floor, "seed_model.floor_price() floor")
    except Exception:
        pass

    # The alternatives chapters price every other way of doing each thing,
    # from the Creator's catalogues applied to this dome's quantities. Those
    # are derived figures like any other and belong in the pool.
    try:
        from . import alternatives

        for concept in alternatives.catalogue():
            for option in concept.options:
                if option.usd is not None:
                    add(option.usd, f"{concept.key}: {option.name}")
    except Exception as exc:
        print(f"  alternatives unavailable to the money audit: {exc}")
    return pool


def audit_money(book: store.Book | None = None,
                floor: int = 100) -> list[Unmatched]:
    """Dollar figures in the prose the cost model no longer produces.

    Only figures of ``floor`` dollars and up, because small round numbers in
    prose are usually prices of things this book does not model -- a saw
    blade, a box of screws -- and flagging them would bury the ones that
    matter.
    """
    book = book or store.load_json()
    pool = money_pool()
    misses: list[Unmatched] = []
    for _part, chapter, section in book.sections:
        found: dict[str, int] = {}
        for match in MONEY.finditer(section.body or ""):
            raw = match.group(1).replace(",", "")
            if not raw.isdigit():
                continue
            value = int(raw)
            if value < floor:
                continue
            # Two dollars of slack: the model rounds and so does the book.
            if any(value + delta in pool for delta in (-2, -1, 0, 1, 2)):
                continue
            found[match.group(0)] = found.get(match.group(0), 0) + 1
        for text, count in sorted(found.items()):
            misses.append(Unmatched(chapter.title, section.title, text, count))
    return misses


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

def validate_numbers(book: store.Book | None = None) -> None:
    """The reference build is what the book says it is, and the prose agrees."""
    values = quantities()

    # -- the four sentences every other number hangs off -------------
    assert abs(values["a_chord_in"].value - 72.0) < 1.0e-9, (
        f"the reference build's long member is "
        f"{values['a_chord_in'].value} in, not 72")
    assert abs(values["b_chord_in"].value - SHORT_CHORD_IN) < 1.0e-3, (
        f"the short chord solves to {values['b_chord_in'].value:.4f} in, and "
        f"the 2V chord factors say it must be {SHORT_CHORD_IN:.4f}")
    assert REFERENCE["wedge_orientation"] == "point_dome_in", (
        "the book's reference build is the wedge point facing into the dome; "
        f"REFERENCE says {REFERENCE['wedge_orientation']!r}")
    model = reference_model()
    assert model.config.wedge_orientation == "point_dome_in"
    assert model.config.panel_joint_mode == "cyclic_pinwheel_butt", (
        "the reference build is a pinwheel; it is what makes this the wedge "
        "method rather than a hubbed dome")
    assert len(model.members) == 120, len(model.members)
    assert len(model.topology.faces) == 40, len(model.topology.faces)

    # The short chord is a consequence, not a choice. Changing the long one
    # has to move it, or the book's "and then the geometry forces the other"
    # sentence is decoration.
    bigger = reference_model(long_edge_in=96.0)
    assert bigger.topology.short_edge_in > model.topology.short_edge_in

    # -- the cut is the chord minus a constant -----------------------
    rows = strut_table()
    reference_rows = [r for r in rows if r["reference"]]
    assert len(reference_rows) == 1, reference_rows
    row = reference_rows[0]
    assert abs(row["a_chord_in"] - 72.0) < 5.0e-3, row
    assert abs(row["a_cut_in"] - values["a_cut_in"].value) < 5.0e-3, row
    bites = {round(r["a_chord_in"] - r["a_cut_in"], 6) for r in rows}
    assert len(bites) == 1, (
        f"the A bite varies across the table: {sorted(bites)}; the cut must "
        "be the chord minus a constant")

    # -- every quantity is real --------------------------------------
    for name, quantity in values.items():
        assert quantity.unit is not None, name
        assert quantity.source, name
        assert math.isfinite(quantity.value), name
        assert quantity.text(), name

    # -- substitution ------------------------------------------------
    assert resolve("{{a_chord_in}}", values) == "72.000"
    assert resolve("{{member_count}}", values) == "120"
    assert resolve("{{a_chord_in:.1f}}", values) == "72.0"
    try:
        resolve("{{not_a_quantity}}", values)
    except KeyError:
        pass
    else:
        raise AssertionError("an unknown token should not resolve")

    # -- the reference designs subtract, they do not scale -----------
    for built in reference_designs():
        assert abs((built.a_chord_in - built.a_cut_in)
                   - values["a_bite_in"].value) < 1.0e-6, (
            f"{built.section}: the A bite is "
            f"{built.a_chord_in - built.a_cut_in:.4f} in and the solve says "
            f"{values['a_bite_in'].value:.4f}; the cut is the chord minus a "
            "constant at every size")
        assert abs(built.apex_ft - built.radius_ft) < 1.0e-9, built.section
        assert built.timber_ft > 0.0, built.section
    sections = [built.section for built in reference_designs()]
    assert len(set(sections)) == len(sections), sections
    titles = {s.title for _p, _c, s in (book or store.load_json()).sections}
    for name in sections:
        assert name in titles, (
            f"{name!r} is not a section of the book; the reference designs "
            "and chapter 19 have come apart")

    # -- and the prose already written ------------------------------
    money_misses = audit_money(book)
    assert not money_misses, (
        f"{len(money_misses)} dollar figures in the book are not values the "
        "cost model produces:" + store.NEWLINE_BULLET
        + store.NEWLINE_BULLET.join(
            f"{m.chapter} / {m.section}: {m.text} (x{m.count})"
            for m in money_misses[:25]))

    misses = audit(book)
    assert not misses, (
        f"{len(misses)} high-precision figures in the book are not values "
        "this code produces:" + store.NEWLINE_BULLET
        + store.NEWLINE_BULLET.join(
            f"{m.chapter} / {m.section}: {m.text} (x{m.count})"
            for m in misses[:25]))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit", action="store_true",
                        help="list prose figures the code cannot produce")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.audit:
        misses = audit() + audit_money()
        if not misses:
            print("every high-precision figure and every dollar figure in "
                  "the book is one this code produces")
            return 0
        print(f"{len(misses)} figures the code does not produce:")
        for miss in misses:
            print(f"  {miss.chapter} / {miss.section}: "
                  f"{miss.text} (x{miss.count})")
        return 1
    validate_numbers()
    if args.check:
        print("wedge book numbers ok")
        return 0
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
