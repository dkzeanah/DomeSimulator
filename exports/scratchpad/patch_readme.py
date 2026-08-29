"""Describe all four masterclass lessons in the project README."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\README.md")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:\n" + old[:240])
    s = s.replace(old, new, 1)


sub(
    "## Standalone 2V Geodesic Masterclass (`two_v_masterclass.py`)\n\n"
    "The 2V Masterclass is a separate ModernGL world for teaching and YouTube\n"
    "capture. It does not enter the Dome Creator site or the assembly-line factory.\n"
    "Its 14-chapter timeline reconstructs the geometry from phi coordinates,\n"
    "normalizes the parent icosahedron, animates midpoint projection, discovers the\n"
    "two chord classes numerically, audits the supplied 72 in / 63.5 in members,\n"
    "builds the 30-SHORT / 35-LONG hemisphere cut list, and raises the dome from the\n"
    "base ring to the apex.\n",
    "## Standalone Masterclass lessons (`two_v_masterclass.py` and friends)\n\n"
    "The Masterclass is a separate ModernGL world for teaching and YouTube\n"
    "capture. It does not enter the Dome Creator site or the assembly-line factory.\n"
    "One renderer plays **four** lessons, chosen from a Lesson dropdown:\n\n"
    "* **`2v` - 2V Geodesic Masterclass, 14 chapters.** Reconstructs the geometry\n"
    "  from phi coordinates, normalizes the parent icosahedron, animates midpoint\n"
    "  projection, discovers the two chord classes numerically, audits the supplied\n"
    "  72 in / 63.5 in members, builds the 30-SHORT / 35-LONG hemisphere cut list,\n"
    "  and raises the dome from the base ring to the apex.\n"
    "* **`build` - 2V Dome Construction, 32 chapters.** The same derivation, then\n"
    "  everything that comes after it: choosing a radius, choosing a hub system,\n"
    "  centre length versus cut length, end-cut angles, panel bevels, hub types,\n"
    "  stock lengths and offcut, saw jigs, setting out the base decagon,\n"
    "  foundations, riser walls, raising ring by ring, closing the crown, the\n"
    "  measurement loop, skinning, openings, and the four mistakes that actually\n"
    "  stop domes going up. It shows that a ten-sided base ring amplifies a strut\n"
    "  error by exactly phi.\n"
    "* **`hex` - Hexagonal Dome Masterclass, 20 chapters.** Why a sheet of\n"
    "  hexagons will never curve, why every hexagon cage needs exactly twelve\n"
    "  pentagons, the single-hexagon frame dome you can cut from one strut length\n"
    "  (twenty regular hexagons, ninety identical struts), and what raising the\n"
    "  frequency costs: more strut lengths, more hexagon shapes, and panels that\n"
    "  stop lying flat.\n"
    "* **`zome` - Zome Construction Masterclass, 19 chapters.** Rooms swept from a\n"
    "  star of directions: every face a parallelogram and therefore flat by\n"
    "  construction, one strut length, hubs on perfectly level rings, a true point\n"
    "  at the top, and the rhombic triacontahedron whose thirty identical panels\n"
    "  have diagonals in the golden ratio.\n\n"
    "Nothing on screen is a typed-in number. Each lesson has a geometry module\n"
    "that computes and then proves its own claims, and `Action = selftest` runs\n"
    "those proofs before any of the figures reach a frame.\n",
)

sub(
    "py -3.12 launcher.py               # 2V Masterclass tab: every option below\n"
    "py -3.12 two_v_masterclass.py      # direct run, fullscreen presenter mode\n",
    "py -3.12 launcher.py               # Masterclass tab: every option below\n"
    "py -3.12 two_v_masterclass.py      # direct run: 2V geometry lesson\n"
    "py -3.12 dome_build_masterclass.py # direct run: construction lesson\n"
    "py -3.12 hex_masterclass.py        # direct run: hexagonal dome lesson\n"
    "py -3.12 zome_masterclass.py       # direct run: zome lesson\n",
)

sub(
    "all fields on the launcher's **2V Masterclass** tab now, in place of the",
    "all fields on the launcher's **Masterclass** tab now, in place of the",
)

sub(
    "the [2V masterclass](#standalone-2v-geodesic-masterclass-two_v_masterclasspy),",
    "the [masterclass lessons]"
    "(#standalone-masterclass-lessons-two_v_masterclasspy-and-friends),",
)

sub(
    "engine built on the 2V Masterclass's rendering core. A `Presentation` is",
    "engine built on the Masterclass's rendering core. A `Presentation` is",
)

p.write_text(s, encoding="utf-8")
print("README.md updated")
