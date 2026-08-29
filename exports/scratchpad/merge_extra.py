"""Merge the four added sections into the construction lesson."""

from pathlib import Path

NL = chr(10)


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}: {old[:200]}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


extra = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build_extra.py")

# Dead branch left over from an earlier draft: both arms were the same.
sub(
    extra,
    "        centre = corners.mean(axis=0)" + NL
    + "        offset = normalize(centre) * spread" + NL
    + "        colour = CYAN if len(set(" + NL
    + "            GEOMETRY.edge_class_by_edge[i] for i in range(0)" + NL
    + "        )) else CYAN" + NL
    + "        _triangle_struts(opaque, corners + offset, colour, 0.062)",
    "        centre = corners.mean(axis=0)" + NL
    + "        offset = normalize(centre) * spread" + NL
    + "        _triangle_struts(opaque, corners + offset, CYAN, 0.062)",
)

# A single-item loop reads as though more cases were coming.
sub(
    extra,
    "    mitre = math.radians(setup.mitre_deg) * reveal" + NL
    + "    for sign, colour, label, angle in (" + NL
    + "        (1.0, CYAN, " + chr(34) + "MITRE (saw swings)" + chr(34) + ", mitre)," + NL
    + "    ):" + NL
    + "        tip = end + np.array([0.0, math.tan(angle) * 0.62, 0.0])" + NL
    + "        opaque.cylinder(end + np.array([0.0, -0.62, 0.0])," + NL
    + "                        end + np.array([0.0, 0.62, 0.0]), 0.03, MUTED, 6)" + NL
    + "        opaque.cylinder(end + np.array([-0.9, -0.62, 0.0])," + NL
    + "                        tip + np.array([0.0, 0.0, 0.0]), 0.05, colour, 8)",
    "    mitre = math.radians(setup.mitre_deg) * reveal" + NL
    + "    tip = end + np.array([0.0, math.tan(mitre) * 0.62, 0.0])" + NL
    + "    opaque.cylinder(end + np.array([0.0, -0.62, 0.0])," + NL
    + "                    end + np.array([0.0, 0.62, 0.0]), 0.03, MUTED, 6)" + NL
    + "    opaque.cylinder(end + np.array([-0.9, -0.62, 0.0]), tip, 0.05, CYAN, 8)",
)

# FRANKEN_TRADE and hubless_struts are documentation, not drawn here.
sub(
    extra,
    "from .hubless_geometry import (" + NL
    + "    AIRFLOW_CAVEATS," + NL
    + "    FRANKEN_TRADE," + NL
    + "    TYPICAL_MITRE_SAW_MAX_DEG," + NL
    + "    airflow_model," + NL
    + "    compound_setups," + NL
    + "    franken_hardware," + NL
    + "    hubless_struts," + NL
    + "    hubless_summary," + NL
    + "    panel_classes," + NL
    + "    sheet_nesting," + NL
    + ")",
    "from .hubless_geometry import (" + NL
    + "    AIRFLOW_CAVEATS," + NL
    + "    TYPICAL_MITRE_SAW_MAX_DEG," + NL
    + "    airflow_model," + NL
    + "    compound_setups," + NL
    + "    franken_hardware," + NL
    + "    hubless_summary," + NL
    + "    panel_classes," + NL
    + "    sheet_nesting," + NL
    + ")",
)

build = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build.py")

sub(
    build,
    "from .lessons import Chapter, Lesson",
    "from .hubless_geometry import hubless_report, validate_hubless" + NL
    + "from .lesson_build_extra import (" + NL
    + "    EXTRA_CHAPTERS," + NL
    + "    EXTRA_SCENES," + NL
    + "    extra_equations," + NL
    + ")" + NL
    + "from .lessons import Chapter, Lesson",
)

sub(
    build,
    "from __future__ import annotations" + NL + NL + "import math",
    "from __future__ import annotations" + NL + NL
    + "import math" + NL + "from dataclasses import replace",
)

# Scenes: the added stages join the existing table.
sub(
    build,
    '    "build_recap": scene_build_recap,' + NL + "}",
    '    "build_recap": scene_build_recap,' + NL
    + "}" + NL
    + "SCENES.update(EXTRA_SCENES)",
)

# Chapters: the four new sections go in ahead of the closing recap, which
# keeps its place as the last word and takes its new number.
sub(
    build,
    "        20.0, (30.0, 28.0, 15.0), " + chr(34) + "build_recap" + chr(34) + "," + NL
    + "    )," + NL
    + ")",
    "        20.0, (30.0, 28.0, 15.0), " + chr(34) + "build_recap" + chr(34) + "," + NL
    + "    )," + NL
    + ")" + NL + NL
    + "# The four added sections sit between the failure list and the recap, so" + NL
    + "# the lesson still ends on the summary. The recap keeps its position and" + NL
    + "# takes whatever number it now lands on." + NL
    + "CHAPTERS = (" + NL
    + "    CHAPTERS[:-1]" + NL
    + "    + EXTRA_CHAPTERS" + NL
    + "    + (replace(CHAPTERS[-1], number=f" + chr(34)
    + "{len(CHAPTERS) + len(EXTRA_CHAPTERS):02d}" + chr(34) + "),)" + NL
    + ")",
)

# Equations and proofs.
sub(
    build,
    "def build_equations(app, stage: str) -> list[str]:" + NL
    + "    short, long = strut_details()",
    "def build_equations(app, stage: str) -> list[str]:" + NL
    + "    added = extra_equations(app, stage)" + NL
    + "    if added:" + NL
    + "        return added" + NL
    + "    short, long = strut_details()",
)

sub(
    build,
    "def _selftest() -> None:" + NL
    + "    validate_geometry()" + NL
    + "    validate_build_geometry()",
    "def _selftest() -> None:" + NL
    + "    validate_geometry()" + NL
    + "    validate_build_geometry()" + NL
    + "    validate_hubless()",
)

sub(
    build,
    "    report=lambda: build_report(RADIUS_IN, DEDUCTION_IN, STOCK_SHORT_IN),",
    "    report=lambda: build_report(RADIUS_IN, DEDUCTION_IN, STOCK_SHORT_IN)" + NL
    + "    + chr(10) * 2 + hubless_report(RADIUS_IN),",
)

print("merged: scenes, chapters, equations, selftest and report")
