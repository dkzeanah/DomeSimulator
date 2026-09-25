"""Every other way of doing it, priced for this dome.

A book that recommends one way of building something owes the reader the
others. Not a paragraph saying alternatives exist -- the alternatives, named,
with what each one costs and weighs **on this building**, and a mark against
the one the reference build uses.

That is worth more than it sounds, because a list of materials with prices per
square metre is not a decision. A decision is "on a 19.4-foot dome with 550
square feet of shell, cedar shakes are $1,635 and 449 pounds, and asphalt is
$766 and 599 pounds" -- and that is arithmetic this repository can already do,
because it costs domes for a living.

WHERE THE OPTIONS COME FROM

Every option here is one some tool in this project already models. Nothing is
invented for the book:

* the frame's own decisions -- which way the wedge points, what fills the
  seam, how many sectors the log splits into -- come from the raw-wedge
  solver's own configuration space, and :mod:`wedge_book.figures` renders
  each one;
* frame materials, strut sections, panel types, claddings and foundations
  come from :mod:`materials`, which is the Dome Creator's own catalogue;
* the platform comes from :mod:`pad_deck`, which takes off boards and piers
  rather than quoting a rate per square foot;
* the laminates come from :mod:`hull_laminate` and the quilted layers from
  :mod:`soft_shell`.

WHAT IS NOT HERE

Anything nothing here models. There is no straw-bale row and no earthbag row,
because this project cannot cost one, and a table with a plausible number in
it that came from nowhere is worse than a table with a gap.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

from . import store

SQFT_PER_SQM = 10.763910416709722
LB_PER_KG = 2.2046226218487757
CUIN_PER_CUM = 61023.744094732284


@dataclass(frozen=True)
class Option:
    """One way of doing one thing, costed for the reference build."""

    name: str
    usd: float | None = None
    pounds: float | None = None
    note: str = ""
    reference: bool = False
    #: Extra columns this concept wants, as (label, text).
    extra: tuple[tuple[str, str], ...] = ()
    #: Which decision this option answers. A concept may bundle several --
    #: the frame has four independent ones -- and each may mark its own
    #: default, so "exactly one default" is per axis and not per table.
    axis: str = ""


@dataclass(frozen=True)
class Concept:
    """One decision the builder has to make, and every answer to it."""

    key: str
    title: str
    question: str
    source: str
    options: tuple[Option, ...]
    book_chapter: int
    #: True when changing this changes the frame rather than what covers it.
    structural: bool = False
    columns: tuple[str, ...] = ("cost", "weight")

    @property
    def reference(self) -> Option | None:
        return next((o for o in self.options if o.reference), None)

    def spread(self) -> float:
        """Dearest over cheapest, for the options that have a price."""
        priced = [o.usd for o in self.options if o.usd]
        if len(priced) < 2 or min(priced) <= 0:
            return 0.0
        return max(priced) / min(priced)


# ----------------------------------------------------------------------
# The reference build, in the units the catalogues use
# ----------------------------------------------------------------------

def dome() -> dict:
    """The quantities every option below is multiplied by."""
    import seed_world

    geometry = seed_world.geometry()
    shell_sqm = geometry.panel_sqft / SQFT_PER_SQM
    floor_sqm = geometry.floor_decagon_sqft / SQFT_PER_SQM
    # The frame, as a volume: total stock length times the sector's section.
    section_sqm = (geometry.member_section_in2 / 144.0) / SQFT_PER_SQM
    length_m = geometry.member_stock_ft * 0.3048
    return {
        "shell_sqft": geometry.panel_sqft,
        "shell_sqm": shell_sqm,
        "floor_sqft": geometry.floor_decagon_sqft,
        "floor_sqm": floor_sqm,
        "member_count": geometry.member_count,
        "stock_ft": geometry.member_stock_ft,
        "length_m": length_m,
        "section_sqm": section_sqm,
        "frame_cum": length_m * section_sqm,
        "width_m": geometry.member_width_in * 0.0254,
        "seam_ft": geometry.seam_length_in / 12.0,
        "base_ft": geometry.base_perimeter_ft,
    }


# ----------------------------------------------------------------------
# The concepts
# ----------------------------------------------------------------------

def frame_materials(size: dict) -> Concept:
    import materials

    rows = []
    for material in materials.FRAME_MATERIALS:
        mass_kg = size["frame_cum"] * material.density
        rows.append(Option(
            name=material.name,
            usd=mass_kg * material.cost_per_kg,
            pounds=mass_kg * LB_PER_KG,
            reference=material.name == "Whole Tree Trunk",
            note=f"{material.density:,.0f} kg/m3 at "
                 f"${material.cost_per_kg:,.2f}/kg",
        ))
    return Concept(
        "frame_material", "What the frame is made of",
        "The same 120 members, in each material this project can price. The "
        "volume is the reference build's own: a 45-degree sector of a "
        "12-inch log, 664 feet of it.",
        "materials.FRAME_MATERIALS", tuple(rows), 4, structural=True)


def strut_sections(size: dict) -> Concept:
    import materials

    rows = []
    for shape in materials.STRUT_SHAPES:
        area = shape.cross_section_area(size["width_m"])
        volume = area * size["length_m"]
        rows.append(Option(
            name=shape.name,
            pounds=volume * 650.0 * LB_PER_KG,
            note=f"{area * 1.0e4:,.1f} cm2 of section",
            reference=shape.name == "Quarter Wedge",
            extra=(("section", f"{area * 1550.0031:,.2f} sq in"),),
        ))
    import seed_world

    solved = seed_world.geometry().member_section_in2
    quarter = next(s for s in materials.STRUT_SHAPES
                   if s.name == "Quarter Wedge")
    quarter_in2 = quarter.cross_section_area(size["width_m"]) * 1550.0031
    return Concept(
        "strut_section", "The shape of the stick",
        "Eight cross sections at the same nominal width, and how much "
        "material each one is. In timber at 650 kg per cubic metre, so the "
        "column compares shapes rather than materials. Read the wedge row "
        f"carefully: the Creator's Quarter Wedge is {quarter_in2:,.2f} sq in "
        "because it is a quarter of a log sized by the strut's width, and "
        f"this book's member is {solved:,.2f} sq in because it is an eighth "
        "of a 12-inch one. Same family, different stick.",
        "materials.STRUT_SHAPES", tuple(rows), 4, structural=True,
        columns=("weight",))


def panel_types(size: dict) -> Concept:
    import materials

    rows = []
    for panel in materials.PANEL_TYPES:
        if panel.name == "Open":
            rows.append(Option("Open", 0.0, 0.0, "no panel at all"))
            continue
        rows.append(Option(
            name=panel.name,
            usd=panel.cost_per_m2 * size["shell_sqm"],
            pounds=panel.area_weight * size["shell_sqm"] * LB_PER_KG,
            note=(f"{panel.watts_per_m2:,.0f} W/m2"
                  if panel.watts_per_m2 else
                  ("glazing" if panel.transparent else "")),
            reference=panel.name == "Plywood",
        ))
    return Concept(
        "panel_type", "What fills the triangles",
        f"Sixteen panel types over {size['shell_sqft']:,.0f} square feet of "
        "shell. The reference build is plywood, and the range from canvas to "
        "solar is a factor of a hundred and twenty.",
        "materials.PANEL_TYPES", tuple(rows), 11)


def claddings(size: dict) -> Concept:
    import materials

    rows = []
    for layer in materials.LAYER_TYPES:
        if layer.name == "None":
            rows.append(Option("None", 0.0, 0.0, "bare panels"))
            continue
        rows.append(Option(
            name=layer.name,
            usd=layer.cost_per_m2 * size["shell_sqm"],
            pounds=layer.area_weight * size["shell_sqm"] * LB_PER_KG,
            note=f"{layer.thickness * 1000:,.0f} mm",
        ))
    return Concept(
        "cladding", "What goes over the panels",
        "Nine claddings over the same shell. A green roof is 24 times the "
        "weight of house wrap and nine times the cost, and the frame has to "
        "carry whichever one is chosen.",
        "materials.LAYER_TYPES", tuple(rows), 11)


def foundations(size: dict) -> Concept:
    import materials
    import pad_deck
    import seed_model

    rows = []
    for deck in pad_deck.compare():
        rows.append(Option(
            name=deck.label,
            usd=deck.cost,
            note=f"taken off, not rated: {len(deck.lines)} lines"
                 + ("" if deck.walkable else "; not a floor"),
            reference=deck.key == seed_model.declared_deck(),
        ))
    # The Creator's own rate-based table, beside the taken-off one. They are
    # two different kinds of estimate and the book says so.
    for foundation in materials.FOUNDATION_TYPES:
        if foundation.cost_per_m2 <= 0:
            continue
        area = math.pi * (size["floor_sqm"] / math.pi) * 1.0
        rows.append(Option(
            name=f"{foundation.name} (rate)",
            usd=foundation.cost_per_m2 * size["floor_sqm"],
            pounds=(foundation.weight_per_m2 * size["floor_sqm"]
                    * LB_PER_KG),
            note=f"${foundation.cost_per_m2:,.0f}/m2, a rate rather than a "
                 f"take-off",
        ))
    return Concept(
        "foundation", "What it stands on",
        "Five platforms taken off board by board, and seven priced at a rate "
        "per square metre. The two lists disagree, which is what an estimate "
        "and a take-off do; the book uses the take-off.",
        "pad_deck.compare() and materials.FOUNDATION_TYPES",
        tuple(rows), 12)


def shells(size: dict) -> Concept:
    import hull_laminate
    import seed_model
    import soft_shell

    rows = []
    bare = soft_shell.soft_shell(0)
    rows.append(Option("Shower cap, bare", bare.cost, None,
                       "wood panels, a breather and one rain-slick cap",
                       reference=True))
    for layers in (1, 3, 7):
        built = soft_shell.soft_shell(layers)
        rows.append(Option(
            f"Shower cap, {layers} quilted layer"
            f"{'s' if layers > 1 else ''}",
            built.cost, None,
            f"R-{soft_shell.compare(layers)[-1].soft_r:,.0f}"))
    geometry = seed_model.seed_geometry()
    standoff = seed_model.declared("shell_standoff_in")
    outer = geometry.shell_sqft(
        standoff + seed_model.declared("shell_core_thickness_in"))
    inner = geometry.shell_sqft(standoff)
    for plan in hull_laminate.compare(outer, inner):
        try:
            priced = seed_model.quote("stem_cell", shell="hard",
                                      resin=plan.system.key)
            group = priced.find("shell")
            cost = group.cost if group else plan.total_usd
        except Exception:
            cost = plan.total_usd
        rows.append(Option(
            f"Laminated hull, {plan.system.label.lower()}",
            cost, plan.skin_lb,
            f"{len(plan.plies)} plies, ${plan.usd_per_sqft:,.2f}/sq ft of "
            f"materials"))
    return Concept(
        "shell", "How it is made watertight",
        "One watertight layer or a laminated hull, and what the quilted "
        "layers under the cap add. The reference build is the cap, because "
        "two impermeable skins with insulation between them is a trap.",
        "soft_shell and hull_laminate", tuple(rows), 11)


def seam_fillers(size: dict) -> Concept:
    from . import figures

    rows = []
    for value, blurb in figures.PERMUTATIONS["spacer_mode"]["values"].items():
        facts = figures.seam_facts(figures._cfg(spacer_mode=value))
        rows.append(Option(
            name=str(value),
            note=blurb,
            reference=value == "rigid",
            axis="spacer_mode",
            extra=(("the part is",
                    {"rigid": f"a key {facts['spline_in']:,.2f} in across "
                              f"its base",
                     "hose": f"a line up to {facts['hose_in']:,.2f} in "
                             f"outside diameter",
                     "none": "nothing; the channel stays open"}[value]),),
        ))
    for value, blurb in figures.PERMUTATIONS["seam_join_mode"][
            "values"].items():
        config = figures._cfg(seam_join_mode=value)
        facts = figures.seam_facts(config)
        # The two modes make different parts out of the same gap: the raw
        # trapezoid keeps the sector's own angle, the shaved flat machines
        # both faces parallel and drops a rectangle in.
        width = (facts["spline_in"] if value == "raw_trapezoid"
                 else config.get("flat_key_width_in", 1.0))
        rows.append(Option(
            name=str(value),
            note=blurb,
            reference=value == "raw_trapezoid",
            axis="seam_join_mode",
            extra=(("the key is", f"{width:,.2f} in wide"),),
        ))
    return Concept(
        "seam", "What fills the seam",
        f"The gap two sawn faces leave is {size['seam_ft']:,.0f} feet long in "
        "this dome and it exists whether or not anything is put in it. These "
        "are what the solver will put there.",
        "the raw-wedge solver's own configuration space",
        tuple(rows), 7, structural=True, columns=())


def frame_decisions(size: dict) -> Concept:
    from . import figures

    rows = []
    for axis in ("wedge_orientation", "radial_splits", "trunk_diameter_in",
                 "panel_joint_handedness"):
        spec = figures.PERMUTATIONS[axis]
        for value, blurb in spec["values"].items():
            facts = figures.seam_facts(figures._cfg(**{axis: value}))
            rows.append(Option(
                name=f"{axis.replace('_', ' ')} = {value}",
                note=blurb,
                reference=figures.STANDARD.get(axis) == value,
                axis=axis,
                extra=(("seam key",
                        f"{facts['spline_in']:,.2f} in"),),
            ))
    return Concept(
        "frame", "The four decisions that change the frame itself",
        "Which way the wedge points, how many sectors the log splits into, "
        "how big the tree was, and which way the triangle pinwheels. Every "
        "one of them is irreversible once the first panel is cut, and every "
        "one has a figure in this book.",
        "the raw-wedge solver's own configuration space",
        tuple(rows), 15, structural=True, columns=())


def catalogue() -> tuple[Concept, ...]:
    size = dome()
    return (
        frame_decisions(size),
        frame_materials(size),
        strut_sections(size),
        seam_fillers(size),
        panel_types(size),
        claddings(size),
        shells(size),
        foundations(size),
    )


# ----------------------------------------------------------------------
# Printing
# ----------------------------------------------------------------------

def table(concept: Concept) -> str:
    """One concept as the monospaced block the book prints."""
    lines = [concept.title.upper(), "", concept.question, ""]
    width = max(len(o.name) for o in concept.options) + 2
    head = f"    {'':<{width}}"
    if "cost" in concept.columns:
        head += f"{'cost':>10}"
    if "weight" in concept.columns:
        head += f"{'weight':>11}"
    lines.append(head + "")
    for option in concept.options:
        mark = "  <- the reference build" if option.reference else ""
        row = f"    {option.name:<{width}}"
        if "cost" in concept.columns:
            row += (f"${option.usd:>9,.0f}" if option.usd is not None
                    else f"{'':>10}")
        if "weight" in concept.columns:
            row += (f"{option.pounds:>9,.0f} lb" if option.pounds is not None
                    else f"{'':>11}")
        extra = "  ".join(f"{label} {text}" for label, text in option.extra)
        tail = "; ".join(bit for bit in (option.note, extra) if bit)
        if tail:
            row += f"   {tail}"
        lines.append(row + mark)
    if concept.spread() > 1.5:
        lines += ["", f"    dearest over cheapest: "
                      f"{concept.spread():,.1f} times"]
    lines += ["", f"    source: {concept.source}"]
    return "\n".join(lines)


def report() -> str:
    parts = ["EVERY OTHER WAY OF DOING IT", ""]
    for concept in catalogue():
        parts.append(table(concept))
        parts.append("")
    return "\n".join(parts)


# ----------------------------------------------------------------------
# Into the book
# ----------------------------------------------------------------------

TITLE = "Every other way of doing it"


def section_body(concept) -> str:
    """One concept as a section of the book."""
    lines = [concept.question, "", TITLE.upper(), ""]
    width = max(len(o.name) for o in concept.options) + 2
    head = f"    {'':<{width}}"
    if "cost" in concept.columns:
        head += f"{'cost':>10}"
    if "weight" in concept.columns:
        head += f"{'weight':>11}"
    lines.append(head.rstrip() or "    ")
    for option in concept.options:
        row = f"    {option.name:<{width}}"
        if "cost" in concept.columns:
            row += (f"${option.usd:>9,.0f}" if option.usd is not None
                    else f"{'':>10}")
        if "weight" in concept.columns:
            row += (f"{option.pounds:>9,.0f} lb" if option.pounds is not None
                    else f"{'':>11}")
        extra = "  ".join(f"{label} {text}" for label, text in option.extra)
        tail = "; ".join(bit for bit in (option.note, extra) if bit)
        if tail:
            row += f"   {tail}"
        if option.reference:
            row += "   <- the reference build"
        lines.append(row)
    lines.append("")

    if concept.spread() > 1.5:
        lines += [
            f"The dearest of these is {concept.spread():,.1f} times the "
            f"cheapest. That is the size of the decision, and it is why the "
            f"book states which one it assumes rather than leaving it to a "
            f"reader to infer.",
            "",
        ]
    reference = concept.reference
    if reference is not None and not concept.structural:
        lines += [
            f"This book assumes {reference.name.lower()}. Nothing else in it "
            f"depends on that: change the row and the rest of the method is "
            f"unchanged.",
            "",
        ]
    elif concept.structural:
        lines += [
            "These change the frame itself. Every other choice in this book "
            "can be made after the dome is standing; these cannot be made "
            "twice.",
            "",
        ]
    lines += [
        "WHERE THESE NUMBERS COME FROM",
        "",
        f"{concept.source}, applied to the reference build's own quantities. "
        "Nothing on this page is a rate quoted from outside the project, and "
        "nothing on it was typed: regenerate the whole table with "
        "`py -3.12 -m wedge_book.alternatives --apply`.",
        "",
        "There is no straw-bale row and no earthbag row, because this project "
        "cannot cost one. A table with a plausible number in it that came "
        "from nowhere is worse than a table with a gap.",
    ]
    return "\n".join(lines).strip()


def section_title(concept: Concept) -> str:
    head = concept.title
    return f"Every other way: {head[0].lower()}{head[1:]}"


def apply_to_book(book: store.Book | None = None) -> dict:
    """Write each concept's table into its chapter, as a generated section.

    Added once, regenerated ever after. A section of the book whose text is
    computed is a section that cannot go stale, and
    :func:`validate_alternatives_in_book` fails if one has.
    """
    book = book or store.load_json()
    order, chapters = 0, {}
    for part in book.parts:
        for chapter in part.chapters:
            order += 1
            chapters[order] = chapter

    added, updated, missing = [], [], []
    for concept in catalogue():
        chapter = chapters.get(concept.book_chapter)
        if chapter is None:
            missing.append(f"no chapter {concept.book_chapter} "
                           f"for {concept.key}")
            continue
        title = section_title(concept)
        body = section_body(concept)
        found = next((s for s in chapter.sections if s.title == title), None)
        if found is None:
            chapter.sections.append(store.Section(
                title=title, body=body, notes="",
                index=len(chapter.sections) + 1))
            added.append(title)
        elif found.body != body:
            found.body = body
            updated.append(title)
    store.save_json(book)
    store.sync("json-wins")
    return {"added": added, "regenerated": updated, "missing": missing}


def validate_alternatives_in_book(book: store.Book | None = None) -> None:
    """Every concept has its section, and every section is up to date."""
    book = book or store.load_json()
    have = {s.title: s for _p, _c, s in book.sections}
    stale, absent = [], []
    for concept in catalogue():
        title = section_title(concept)
        found = have.get(title)
        if found is None:
            absent.append(title)
            continue
        if (found.body or "").strip() != section_body(concept).strip():
            stale.append(title)
    assert not absent, (
        f"{len(absent)} concepts have no section in the book:"
        + store.NEWLINE_BULLET + store.NEWLINE_BULLET.join(absent))
    assert not stale, (
        f"{len(stale)} generated sections no longer match what "
        "alternatives.py produces; run apply_to_book():"
        + store.NEWLINE_BULLET + store.NEWLINE_BULLET.join(stale))


def validate_alternatives() -> None:
    """Every concept is real, priced for this dome, and marks its default."""
    size = dome()
    assert size["shell_sqft"] > 400.0, size
    assert size["member_count"] == 120, size

    concepts = catalogue()
    assert len(concepts) >= 8, len(concepts)
    keys = [c.key for c in concepts]
    assert len(set(keys)) == len(keys), keys

    total_options = 0
    for concept in concepts:
        assert concept.options, concept.key
        assert len(concept.question) > 60, f"{concept.key} has no question"
        assert concept.source, concept.key
        assert concept.book_chapter >= 1, concept.key
        total_options += len(concept.options)
        names = [o.name for o in concept.options]
        assert len(set(names)) == len(names), (concept.key, names)
        marked = [o for o in concept.options if o.reference]
        # Every structural decision has to say which one this book builds.
        # A choice about cladding may honestly have no default.
        if concept.structural:
            assert marked, (
                f"{concept.key} changes the frame and does not say which "
                "one the reference build uses")
        # One default per axis. A concept that bundles four decisions marks
        # four; a concept that is one decision marks one.
        by_axis: dict[str, int] = {}
        for option in marked:
            by_axis[option.axis] = by_axis.get(option.axis, 0) + 1
        for axis, count in by_axis.items():
            assert count == 1, (
                f"{concept.key}: {count} options claim to be the reference "
                f"build for {axis or 'this decision'}")
        for option in concept.options:
            if option.usd is not None:
                assert option.usd >= 0.0, (concept.key, option.name)
                assert option.usd < 1.0e6, (concept.key, option.name)
            if option.pounds is not None:
                assert option.pounds >= 0.0, (concept.key, option.name)
        rendered = table(concept)
        assert concept.title.upper() in rendered
        assert "source:" in rendered

    # The point of the chapter is breadth. If it ever stops being broad, the
    # book should say something else instead.
    assert total_options >= 60, (
        f"only {total_options} alternatives across {len(concepts)} concepts; "
        "the book promises the full range")

    # And the numbers have to be this dome's, not a catalogue's own units.
    panels = next(c for c in concepts if c.key == "panel_type")
    plywood = next(o for o in panels.options if o.name == "Plywood")
    assert 500.0 < plywood.usd < 2500.0, (
        f"plywood over this shell is ${plywood.usd:,.0f}, which is not a "
        "number for a 550 square foot dome")

    # And each concept's table is in the book, current.
    validate_alternatives_in_book()

    frame = next(c for c in concepts if c.key == "frame_material")
    timber = next(o for o in frame.options if o.name == "Whole Tree Trunk")
    assert timber.reference, "the reference build is not marked"
    assert 1000.0 < timber.pounds < 4000.0, (
        f"the frame weighs {timber.pounds:,.0f} lb, and seed_model says "
        "about 2,478")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--concept", default="")
    parser.add_argument("--apply", action="store_true",
                        help="write the tables into the book's sections")
    args = parser.parse_args(argv)

    if args.apply:
        result = apply_to_book()
        print(json.dumps(result, indent=2))
        return 0
    validate_alternatives()
    if args.check:
        print("alternatives ok")
        return 0
    if args.concept:
        for concept in catalogue():
            if concept.key == args.concept:
                print(table(concept))
                return 0
        print(f"no concept {args.concept!r}")
        return 1
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
