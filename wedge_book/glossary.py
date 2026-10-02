"""The glossary, and the terms the index is built from.

One list does both jobs, so a word a reader can look up is always a word the
index can find. Each entry is the term as the reader meets it, the plain
definition, and any other spellings the index should count as the same term.

:func:`validate_glossary` refuses an entry whose term never appears in the
book: a glossary that defines words the book does not use is padding, and an
index entry with no pages is a promise the book does not keep.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    term: str
    definition: str
    aliases: tuple[str, ...] = ()

    @property
    def spellings(self) -> tuple[str, ...]:
        return (self.term, *self.aliases)


TERMS: tuple[Term, ...] = (
    Term("2V", "Two-frequency. Each face of an icosahedron is divided in "
         "two along every edge, giving the dome in this book: two strut "
         "lengths and two triangle shapes.", ("two-frequency",)),
    Term("apex", "The top point of the dome, where the crown star's spokes "
         "meet. The only opening in the weather surface is here, closed by "
         "the seal cap."),
    Term("base ring", "The ten-sided ring of members the dome stands on, "
         "resting on the rim of the pad."),
    Term("breather", "A vapour-permeable sheet over the panels. It sheds water "
         "that gets past the cap and lets moisture out, which a plastic "
         "sheet would not."),
    Term("chord", "The straight line between two points on a curve. A wedge's "
         "flat face is a chord sawn across the bark side of its slice of "
         "log.", ("chords",)),
    Term("dihedral angle", "The angle between two neighbouring flat faces "
         "where they meet along a seam. It is shallow on a dome, which is why "
         "the seam leaves a channel.", ("dihedral",)),
    Term("equilateral", "A triangle with three equal sides. Ten of the "
         "forty faces are equilateral; the other thirty are the star "
         "triangles."),
    Term("rip cut", "A chainsaw cut along the length of the log. Each log "
         "section becomes eight wedges by rip cuts through its heart, "
         "along the radius.", ("rip", "rips", "ripping", "rip cuts")),
    Term("geodesic dome", "A dome made of flat triangles arranged on a "
         "sphere, so that every piece of the frame is short, straight and "
         "carries its load along its length.", ("geodesic",)),
    Term("hemisphere", "Exactly half a sphere. The stem cell is a 2V "
         "hemisphere, twice as wide as it is tall."),
    Term("hub", "A metal connector where struts meet in most dome kits. This "
         "method has none: the wedges meet each other directly.",
         ("hubs", "hubless")),
    Term("icosahedron", "The twenty-sided solid a geodesic dome is built "
         "from. Its twelve corners become the only places where five "
         "members meet.", ("icosahedral",)),
    Term("face", "One flat triangle of the dome's surface, bounded by its "
         "own three wedges and closed by one panel. The stem cell has "
         "forty.", ("faces", "triangle", "triangles")),
    Term("junction", "A point in the frame where members meet: five-way at a "
         "star's centre, six-way elsewhere, four-way on the base ring.",
         ("junctions", "vertex", "vertices")),
    Term("member", "One straight structural piece of the frame. Here every "
         "member is a split wedge.", ("members", "strut", "struts")),
    Term("pad", "The serviced platform a dome stands on, built once by the "
         "host with one service port at its centre. It stays when a dome "
         "leaves.", ("pads",)),
    Term("panel", "The flat triangle that closes a face, fixed to the outside "
         "face of its three wedges. Swapping panels changes what the "
         "building is.", ("panels",)),
    Term("pentagon", "A five-sided figure. Around each five-way junction the "
         "star's outer edges form one.", ("pentagons",)),
    Term("pinwheel", "The way a face's three wedges meet at its corners: each "
         "end butts against the side of the next, turning one way round the "
         "point, so nothing is cut to a point."),
    Term("radial split", "A split along a radius of the log, from the heart "
         "of the log to the bark, like cutting a pie. Eight of them make eight wedges.",
         ("radial splits", "radius")),
    Term("seal cap", "The gasketed lid over the apex opening, held by "
         "over-centre catches. Services leave the building under it.",
         ("seal caps",)),
    Term("seam", "The line where two neighbouring faces meet. Their two "
         "wedges lie back to back along it.", ("seams",)),
    Term("seam channel", "The V-shaped groove two back-to-back wedges leave "
         "along a seam. It runs to every junction and carries cables, air "
         "and water.", ("channel", "channels")),
    Term("service port", "The single opening in the pad's deck through which "
         "power, water and drain come up to the utility column."),
    Term("shell", "The weather surface over the frame and panels. In this "
         "book the outermost layer, the cap, is the only watertight one.",
         ("cap",)),
    Term("stem cell", "The standard dome in this book: bare frame, panels, "
         "shell, utility column and seal cap, before anything decides what "
         "it will be.", ("stem-cell",)),
    Term("utility column", "The upright chase at the centre of the dome that "
         "carries power, water and drain from the pad's port up to the apex.",
         ("column",)),
    Term("utility panel", "A small cabinet outside the dome's footprint for "
         "noisy, hot or weather-facing equipment, fed from under the seal "
         "cap.", ("utility panels", "polyp", "polyps")),
    Term("wedge", "A member split from a round log like a slice of pie: "
         "triangular in section, its round bark face outward and its point -- "
         "the heart of the log -- toward the centre of the dome.", ("wedges",)),
    Term("yakisugi", "Charring the surface of wood with a flame, then brushing "
         "and oiling it. The char leaves nothing for fungus or insects to eat.",
         ("charring", "charred", "char")),
    Term("dew point", "The temperature at which the water in a body of air "
         "starts coming out as liquid. The lower it is, the drier the air, "
         "whatever its temperature or relative humidity.", ("dew points",)),
    Term("desiccant", "A material that pulls water vapour out of air and holds "
         "it, until heat drives it back out.", ("desiccants",)),
    Term("molecular sieve", "A zeolite desiccant whose crystal lattice has holes "
         "the size of a water molecule; the 13X grade holds about a fifth of its "
         "weight in water and gives it back at around two hundred degrees.",
         ("13X",)),
    Term("Peltier plate", "A thermoelectric heat pump: current through it moves "
         "heat from one face to the other, and reversing the current reverses "
         "the direction.", ("Peltier", "Peltier plates", "thermoelectric")),
    Term("galvanic corrosion", "What happens when two different metals touch in "
         "water: they make a battery, and the less noble one dissolves.",
         ("galvanic",)),
    Term("linseed oil", "Oil pressed from flax seed that sets by taking up oxygen "
         "rather than by drying. Rags soaked in it can catch fire on their own.",
         ("linseed",)),
    Term("moisture content", "The weight of water in wood as a share of the "
         "weight of the dry wood. Below nineteen per cent, wood counts as dry "
         "and rot cannot get going.", ("moisture",)),
    Term("zome", "A dome-like building swept from a spiral rather than "
         "subdivided from a sphere.", ("zomes",)),
)


def pattern(term: Term) -> re.Pattern:
    """Whole words only, any of the term's spellings, case-insensitive."""
    words = sorted(term.spellings, key=len, reverse=True)
    return re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in words)
                      + r")(?![\w-])", re.IGNORECASE)


def validate_glossary(text: str | None = None) -> None:
    if text is None:
        from . import build
        text, _ = build.document(strict=True)
    plain = re.sub(r"<[^>]+>", " ", text)
    unused = [t.term for t in TERMS if not pattern(t).search(plain)]
    assert not unused, f"glossary terms the book never uses: {unused}"
    names = [t.term.lower() for t in TERMS]
    assert len(names) == len(set(names)), "a term is defined twice"
