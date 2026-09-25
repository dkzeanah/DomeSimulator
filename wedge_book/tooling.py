"""What ships with this book: the programs, and what each one is for.

The last part of the book is a catalogue of software, and it has a problem
every software catalogue has: it is out of date the moment it is written.
So it is not written. Each entry names a module that is actually in this
repository, and :func:`validate_tooling` imports every one of them and checks
that the entry points it claims exist. A tool that is renamed breaks the
book's build rather than quietly becoming a lie in an appendix.

WHAT COUNTS AS A TOOL HERE

Three kinds, and the book says which is which.

**Worlds** are three-dimensional environments you fly around in. They have a
window, a camera and keys. This is where you go to look at something.

**Models** are arithmetic with no picture: the geometry solver, the cost
model, the platform take-off. They answer a question and print a table.

**Desks** are the places you make something: the book studio, the film
exporter, the calculators.

Each entry carries the one thing a reader actually wants, which is not a
feature list but an answer to *why would I open this*.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tool:
    """One program, and the reason somebody would start it."""

    key: str
    name: str
    kind: str                   # world | model | desk
    module: str
    why: str
    """Why a builder would open it. One sentence, in the second person."""
    features: tuple[str, ...] = ()
    keys: tuple[tuple[str, str], ...] = ()
    """Keyboard controls worth printing, as (key, what it does)."""
    figure: str = ""
    """The book figure that shows this tool's output."""
    entry: str = ""
    """The command that starts it."""
    provides: tuple[str, ...] = field(default_factory=tuple)
    """Callables this tool exposes that the book's numbers come from."""


WORLDS: tuple[Tool, ...] = (
    Tool(
        key="raw_wedge", name="The raw-wedge solver", kind="world",
        module="geodesic_raw_wedge_dome_dihedral",
        why="You want to see the dome this book is about, and turn one "
            "decision at a time to watch what it does to the joint.",
        features=(
            "solves the whole 2V frame from one number: the long member",
            "four wedge orientations, and the seam changes under each",
            "two seam keys, three things to put in the channel",
            "explodes the panels apart without moving the geometry, so you "
            "can see into a seam",
            "switches off the wireframe, the node markers, the debug lines "
            "and the sacrificial head stock -- which is what turns a "
            "screenshot into an illustration",
            "exports a full-size panel drawing as SVG, to print and lay a "
            "stick on",
            "carries the cost console, so the price is over the geometry "
            "rather than in another program",
        ),
        keys=(("W A S D", "walk"), ("mouse", "look"),
              ("E", "explode the panels apart"),
              ("I", "the mathematical wireframe on and off"),
              ("H", "the head-end stock on and off"),
              ("J", "the fabrication jig"),
              ("C", "the cost console")),
        figure="standard-dome-exploded",
        entry="py -3.12 geodesic_raw_wedge_dome_dihedral.py",
        provides=("build_physical_model", "build_world_meshes",
                  "run_figure_shots"),
    ),
    Tool(
        key="jig", name="The fabrication jig", kind="world",
        module="geodesic_raw_wedge_dome_dihedral",
        why="You are about to build the fixture and you want to see it "
            "assembled, one step at a time, before you cut the board.",
        features=(
            "twelve steps from a bare bench to a finished panel",
            "each step says what it is enforcing, not just what it is",
            "the red and green fences that make a rotated stick not fit",
            "the two cut planes: the flush-cut fence and the receiving face",
            "the sacrificial tail drawn separately from the finished member",
            "camera stations at each corner, because the corner is where "
            "the method either makes sense or does not",
        ),
        keys=(("J", "show the jig"), ("[ ]", "step through the twelve"),
              ("V", "walk the camera round the corners"),
              ("P", "which panel the jig is set for")),
        figure="the-jig",
        entry="py -3.12 geodesic_raw_wedge_dome_dihedral.py   (then J)",
        provides=("build_fabrication_jig", "JIG_STAGES"),
    ),
    Tool(
        key="creator", name="The Dome Creator", kind="world",
        module="dome_model",
        why="You want a dome that is not this one: a different frequency, a "
            "different material, glass instead of ply, a different "
            "foundation -- and the price for each.",
        features=(
            "frequency 1V to 4V, and the truncation",
            "eight frame materials, from bamboo to structural steel",
            "eight strut cross sections including the quarter wedge",
            "sixteen panel types: ply, glass, acrylic, twinwall, SIP, "
            "shingle, metal, solar, canvas, mirror, precast",
            "nine cladding layers over the panels",
            "seven foundations",
            "a bill of materials for whatever you just built",
        ),
        keys=(("F", "frequency"), ("M", "frame material"),
              ("P", "cycle the panel under the cursor"),
              ("L", "cladding layers"), ("G", "foundation"),
              ("B", "print the bill of materials")),
        figure="plate-twelve-domes",
        entry="py -3.12 dome_creator.py",
        provides=("build_geodesic", "DomeModel"),
    ),
    Tool(
        key="seed", name="The seed world", kind="world",
        module="seed_world",
        why="You want to see the product version: the utility column, the "
            "shower cap, the quilted layers and the mast, on the dome this "
            "book prices.",
        features=(
            "the utility column and the gasketed cap at the apex",
            "the shower cap, and the hats that stack under it",
            "the mast through the column and the floor clamped to it",
            "the floating rig: three cables to saddles on two trees",
            "the composite member, drawn at an exaggerated section and "
            "labelled as exaggerated",
        ),
        keys=(("1-9", "the chapters of the campaign film"),
              ("mouse", "orbit"), ("wheel", "zoom")),
        figure="plate-core-socket",
        entry="py -3.12 -m two_v_demo.app --lesson seed_pitch",
        provides=("geometry", "build_mast", "build_layer_stack"),
    ),
    Tool(
        key="park", name="The pad and the park", kind="world",
        module="park_world",
        why="You are thinking about the ground: what a pad is, what it "
            "costs, and what a network of them looks like.",
        features=(
            "a pad built one course at a time",
            "amber for what the host owns, cyan for what the tenant owns",
            "several domes on several pads, and the shared services "
            "between them",
            "the rotating pad, which is a design possibility and is marked "
            "as one",
        ),
        keys=(("mouse", "orbit"), ("1-9", "the chapters of the park film")),
        figure="plate-the-pad",
        entry="py -3.12 -m two_v_demo.app --lesson dome_park",
        provides=("build_pad", "build_service_spine", "Park"),
    ),
)

MODELS: tuple[Tool, ...] = (
    Tool(
        key="geometry", name="The geometry", kind="model",
        module="seed_world",
        why="You want the numbers: chords, cuts, angles, areas, counts -- "
            "for your dome, not for this one.",
        features=(
            "two chords and two cut lengths at any diameter",
            "the bite the pinwheel takes, which does not scale",
            "face areas, seam runs, member volumes, timber totals",
            "the whole builder's reference, regenerated",
        ),
        figure="",
        entry="py -3.12 -m wedge_book.numbers",
        provides=("geometry",),
    ),
    Tool(
        key="cost", name="The cost model", kind="model",
        module="seed_model",
        why="You want to know what one costs, line by line, with every "
            "assumption named and changeable.",
        features=(
            "every line carries its own source constant",
            "materials, labour, overhead and warranty kept apart",
            "the maker's markup stated as markup on cost, not margin on "
            "price, because those are different numbers",
            "the pad priced separately, because it is the host's bill",
            "fit-outs, shells and resins swapped without editing anything",
        ),
        figure="tool-cost-console",
        entry="py -3.12 -m seed_model",
        provides=("quote", "seed_geometry"),
    ),
    Tool(
        key="pad", name="The platform take-off", kind="model",
        module="pad_deck",
        why="You are pricing the ground and you want boards and piers "
            "counted rather than a rate per square foot.",
        features=(
            "five constructions: gravel, slab, ring, deck, deck with ply",
            "counted line by line, not rated",
            "sized to the dome plus a walking margin",
        ),
        figure="plate-seven-foundations",
        entry="py -3.12 -m pad_deck",
        provides=("deck", "compare", "pad_diameter_ft"),
    ),
    Tool(
        key="shell", name="The shell model", kind="model",
        module="soft_shell",
        why="You are deciding what to put over the frame, and you want the "
            "R-value and the price of each layer.",
        features=(
            "one watertight cap, and the quilted layers under it",
            "each hat a size up from the one beneath",
            "against a laminated hull, priced four ways",
            "the concerns it will not hide, printed with the answer",
        ),
        figure="plate-shower-cap",
        entry="py -3.12 -m soft_shell",
        provides=("soft_shell", "compare", "hat_sizes"),
    ),
)

DESKS: tuple[Tool, ...] = (
    Tool(
        key="book", name="The book studio", kind="desk",
        module="wedge_book.outline",
        why="You want to change this book: its outline, its prose, its "
            "figures, or the dome it is written about.",
        features=(
            "the outline is code, so reordering is an edit and not a "
            "rewrite",
            "every number is a token resolved at build time",
            "an audit that fails the build if a figure in the prose is one "
            "the code cannot produce",
            "the pictures render from the solver and from the films",
        ),
        figure="",
        entry="py -3.12 -m wedge_book.build",
        provides=("BOOK", "validate_outline"),
    ),
    Tool(
        key="films", name="The film exporter", kind="desk",
        module="two_v_demo.app",
        why="Thirty-seven narrated films are built from the same geometry, "
            "and you can re-render any of them with your own numbers in it.",
        features=(
            "one lesson is one Python module: chapters, narration, scenes",
            "landscape and phone cuts from one render",
            "captions, chapter thumbnails and description copy as a set",
            "a still from any second of any film",
        ),
        figure="",
        entry="py -3.12 -m two_v_demo.app --lesson wedge",
        provides=("main",),
    ),
)

ALL: tuple[Tool, ...] = WORLDS + MODELS + DESKS


def catalogue() -> tuple[Tool, ...]:
    return ALL


def by_kind(kind: str) -> tuple[Tool, ...]:
    return tuple(tool for tool in ALL if tool.kind == kind)


#: How wide a monospaced block may be before the book's measure clips it.
#: Found by printing one that did: the feature lines ran off the right edge
#: of the page and the last third of several of them was simply not there.
WRAP = 62


def table() -> str:
    """The catalogue as the block the book prints."""
    import textwrap

    lines: list[str] = []
    for kind, heading in (("world", "WORLDS -- things you fly around in"),
                          ("model", "MODELS -- arithmetic, no picture"),
                          ("desk", "DESKS -- where you make something")):
        lines += [heading, ""]
        for tool in by_kind(kind):
            lines.append(f"  {tool.name}")
            lines += textwrap.wrap(tool.why, WRAP,
                                   initial_indent="      ",
                                   subsequent_indent="      ")
            # A command is not reflowable -- a wrapped shell line is a
            # broken shell line -- so it goes on its own line and the
            # catalogue keeps its commands short enough to fit.
            lines.append(f"      start it:")
            lines.append(f"        {tool.entry}")
            for feature in tool.features:
                lines += textwrap.wrap(feature, WRAP,
                                       initial_indent="      - ",
                                       subsequent_indent="        ")
            if tool.keys:
                pairs = "   ".join(f"{k} {what}" for k, what in tool.keys)
                lines += textwrap.wrap(pairs, WRAP,
                                       initial_indent="      keys: ",
                                       subsequent_indent="            ")
            lines.append("")
    return "\n".join(lines).rstrip()


def validate_tooling() -> None:
    """Every tool named is a module that exists and does what is claimed."""
    import importlib

    keys = [tool.key for tool in ALL]
    assert len(set(keys)) == len(keys), "two tools share a key"
    assert len(by_kind("world")) >= 5, len(by_kind("world"))
    assert len(by_kind("model")) >= 4, len(by_kind("model"))
    assert len(by_kind("desk")) >= 2, len(by_kind("desk"))

    for tool in ALL:
        assert tool.kind in ("world", "model", "desk"), tool.key
        assert tool.why.endswith("."), f"{tool.key}: why must be a sentence"
        assert len(tool.why) > 50, f"{tool.key}: why is too thin to be useful"
        assert tool.features, tool.key
        assert tool.entry, f"{tool.key} does not say how to start it"
        for feature in tool.features:
            assert len(feature) > 12, (tool.key, feature)
        if tool.kind == "world":
            assert tool.keys, f"{tool.key} is a world and prints no controls"
            assert tool.figure, f"{tool.key} is a world and shows no picture"

        # The claim that the module exists, checked rather than asserted.
        if tool.module == "geodesic_raw_wedge_dome_dihedral":
            from . import numbers
            module = numbers.solver()
        else:
            module = importlib.import_module(tool.module)
        for name in tool.provides:
            assert hasattr(module, name), (
                f"{tool.key} claims {tool.module}.{name}, which is not there")

    # Every figure a tool points at has to be one the book has.
    from . import outline

    have = set(outline.figure_keys())
    for tool in ALL:
        if tool.figure:
            assert tool.figure in have, (
                f"{tool.key} shows {tool.figure!r}, which the outline does "
                "not place anywhere")

    rendered = table()
    assert "WORLDS" in rendered and "DESKS" in rendered
    assert len(rendered.splitlines()) > 60
    # Nothing may be wider than the page. A monospaced block that overflows
    # the measure is not truncated with an ellipsis; it is simply cut off,
    # and the reader never learns that there was more.
    too_wide = [line for line in rendered.splitlines() if len(line) > WRAP + 8]
    assert not too_wide, (
        f"{len(too_wide)} lines are wider than the page, starting with "
        f"{too_wide[0][:50]!r}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_tooling()
    if args.check:
        print("tooling ok")
        return 0
    print(table())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
