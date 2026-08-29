"""Add the assembly-line energy lesson to the top-level README."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\README.md")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:200])
    s = s.replace(old, new, 1)


sub(
    "One renderer plays **four** lessons, chosen from a Lesson dropdown:",
    "One renderer plays **five** lessons, chosen from a Lesson dropdown:",
)

sub(
    "* **`zome` - Zome Construction Masterclass, 19 chapters.** Rooms swept from a\n"
    "  star of directions: every face a parallelogram and therefore flat by\n"
    "  construction, one strut length, hubs on perfectly level rings, a true point\n"
    "  at the top, and the rhombic triacontahedron whose thirty identical panels\n"
    "  have diagonals in the golden ratio.\n",
    "* **`zome` - Zome Construction Masterclass, 19 chapters.** Rooms swept from a\n"
    "  star of directions: every face a parallelogram and therefore flat by\n"
    "  construction, one strut length, hubs on perfectly level rings, a true point\n"
    "  at the top, and the rhombic triacontahedron whose thirty identical panels\n"
    "  have diagonals in the golden ratio.\n"
    "* **`line` - Assembly Line Energy Masterclass, 24 chapters.** What building\n"
    "  one dome actually costs the two people who build it. An articulated\n"
    "  two-person crew is animated through all six motions of every part\n"
    "  placement - walk, lift, carry, position, fasten, recover - with the\n"
    "  mechanical work computed limb by limb from Winter's anthropometric tables\n"
    "  and the food energy totalled per motion, per station and per shift. It\n"
    "  keeps two numbers strictly apart: the mechanical work is computed and\n"
    "  exact, the metabolic cost is modelled from published task intensities and\n"
    "  the Pandolf load-carriage equation, and every borrowed constant is named\n"
    "  on screen and in the report. The finding it exists to deliver: across a\n"
    "  whole dome, lifting is a fraction of one per cent of the fuel, while\n"
    "  fastening - which raises nothing at all - is ninety per cent of it.\n",
)

sub(
    "py -3.12 zome_masterclass.py       # direct run: zome lesson\n```",
    "py -3.12 zome_masterclass.py       # direct run: zome lesson\n"
    "py -3.12 line_masterclass.py       # direct run: assembly-line energy lesson\n```",
)

p.write_text(s, encoding="utf-8")
print("root README updated")
