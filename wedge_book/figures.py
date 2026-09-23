"""The book's pictures, made by operating the solver rather than drawing it.

Most technical books illustrate an idea by drawing a picture of the idea.
This one does something else: it *runs the tool* with the settings that make
the idea visible, and prints what comes out. If the book says the key fills
the space the wedge leaves at a seam, the figure beside it is the real solver
with the frame exploded far enough to see into the seam, and the key in it is
the key the fabrication package would cut.

That has two consequences worth stating.

The first is that every figure is reproducible. The recipe is a dict of
:class:`DomeConfig` overrides and a camera, stored next to the image, so
anybody -- including the author a year later -- can regenerate it or change
one setting and see what moves.

The second is that the book can afford to show **permutations**. A chapter
that recommends one way of doing something can show the other three beside it
for the price of three more entries in a list. That is the point of
:data:`PERMUTATIONS`: for every decision the solver exposes, the book shows
the whole gamut and marks which one the reference build assumes, so a reader
who wants to do it differently can see what they are choosing.

Every image carries :data:`store.CREDIT`, burned into the file rather than
written in a caption somewhere, because captions get separated from pictures
and a picture that leaves this repository should still say where it came
from.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import store

ROOT = store.ROOT
FIGURE_DIR = store.BOOK_DIR / "figures"
SOLVER = ROOT / "geodesic_raw_wedge_dome_dihedral.py"

# What the reference build assumes. Every permutation figure is measured
# against this, and the caption says which one it is.
STANDARD: dict = {
    "long_edge_in": 72.0,
    "trunk_diameter_in": 12.0,
    "radial_splits": 8,
    "wedge_orientation": "point_dome_in",
    "seam_join_mode": "raw_trapezoid",
    "spacer_mode": "rigid",
    "panel_joint_mode": "cyclic_pinwheel_butt",
    "vertex_trim_mode": "triangle_envelope",
    "panel_joint_handedness": "clockwise",
}


@dataclass(frozen=True)
class Figure:
    """One picture the book will print, and how to make it again."""

    key: str
    title: str
    caption: str
    chapter: int
    config: dict = field(default_factory=dict)
    camera: dict = field(default_factory=dict)
    # Which decision this figure is showing, and whether it is the one the
    # reference build uses. Both go in the caption.
    axis: str = ""
    is_standard: bool = False
    # The tool's own HUD is off in a printed figure unless the HUD is what
    # the figure is about.
    hud: bool = False
    ground: bool = True

    @property
    def path(self) -> Path:
        return FIGURE_DIR / f"{self.key}.png"

    @property
    def recipe(self) -> str:
        return json.dumps({"config": self.config, "camera": self.camera},
                          sort_keys=True)

    def full_caption(self) -> str:
        """What prints under the picture."""
        bits = [self.caption.rstrip(".")]
        if self.axis:
            bits.append("the reference build uses this" if self.is_standard
                        else f"an alternative to the reference build")
        return ". ".join(bits) + f". {store.CREDIT}"


def _dome_config(config: dict):
    """The solver's own DomeConfig, built from a figure's overrides."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_rwsolver", SOLVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_rwsolver", module)
    spec.loader.exec_module(module)
    return module.DomeConfig(**config)


def _cfg(**overrides) -> dict:
    """A config: the standard, with the named settings changed."""
    merged = dict(STANDARD)
    merged.update(overrides)
    return merged


# ----------------------------------------------------------------------
# The permutation axes
# ----------------------------------------------------------------------

PERMUTATIONS: dict[str, dict] = {
    "wedge_orientation": {
        "camera": {"back": 2.30, "pitch": -14.0, "yaw": 82.0},
        "chapter": 2,
        "why": "Which way the wedge's point faces in the wall. It changes "
               "the seam, the key and how much of the log ends up as "
               "offcut, and it is the first irreversible decision in the "
               "build.",
        "values": {
            "point_dome_in": "both points inward, toward the centre",
            "point_panel_in": "points apart, each into its own triangle",
            "point_dome_out": "both points outward, at the sky",
            "point_panel_out": "points toward each other, across the seam",
        },
    },
    "seam_join_mode": {
        "camera": {"back": 2.10, "pitch": -10.0, "yaw": 86.0},
        "chapter": 7,
        "why": "What fills the gap two sawn faces leave at a seam. The "
               "trapezoid keeps the raw sector and truncates its point; "
               "the shaved flat machines a flat key instead.",
        "values": {
            "raw_trapezoid": "the raw sector, point truncated",
            "shaved_flat": "a machined flat key",
        },
    },
    "spacer_mode": {
        "camera": {"back": 2.15, "pitch": -12.0, "yaw": 74.0},
        "chapter": 7,
        "why": "What goes in the seam channel: a rigid spline, a hose, or "
               "nothing at all.",
        "values": {
            "rigid": "a rigid spline",
            "hose": "a hose, which is also the air and water route",
            "none": "left open",
        },
    },
    # vertex_trim_mode is not here: the solver accepts exactly one value
    # for it, so there is no permutation to show and a figure claiming
    # otherwise would be inventing an option the tool does not have.
    "radial_splits": {
        "camera": {"back": 2.40, "pitch": -16.0, "yaw": 96.0},
        "chapter": 3,
        "why": "How many sectors the trunk is split into. Fewer splits "
               "means a fatter wedge and a deeper wall; more means thinner "
               "sticks and more of them. Eight is what the reference build "
               "uses because it is the split a person can do accurately "
               "with a froe and a wedge, not because the geometry prefers "
               "it.",
        "values": {
            6: "six sectors: a fat wedge, a deep wall",
            8: "eight sectors: the reference build",
            12: "twelve sectors: thin sticks, more of them",
        },
    },
    "panel_joint_handedness": {
        "camera": {"back": 2.25, "pitch": -20.0, "yaw": 60.0},
        "chapter": 5,
        "why": "Which way the three members of a triangle pinwheel. It "
               "mirrors the whole dome and it has to be the same in all "
               "forty panels.",
        "values": {
            "clockwise": "clockwise, seen from outside",
            "counterclockwise": "counterclockwise, seen from outside",
        },
    },
}


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

def catalogue() -> list[Figure]:
    """Every figure the book will print, in chapter order."""
    figures: list[Figure] = []

    # -- the standard dome, as the book assumes it --------------------
    figures.append(Figure(
        "standard-dome", "The reference build",
        "A 2V dome on a six-foot longest member, wedge point inward, "
        "raw trapezoid seams. This is the dome the rest of the book "
        "assumes unless it says otherwise",
        chapter=2, config=_cfg(),
        camera={"back": 1.45, "pitch": -6.0}, is_standard=True))

    figures.append(Figure(
        "standard-dome-exploded", "The same dome, opened up",
        "The reference build with the panels pushed eight inches apart. "
        "Nothing has moved in the geometry -- this is the same solve, "
        "drawn with a gap -- and it is the only way to see what happens "
        "between two panels",
        chapter=2, config=_cfg(panel_explode_in=8.0),
        camera={"back": 1.6, "pitch": -8.0}))

    # -- the key, which is the figure the whole seam chapter needs ----
    figures.append(Figure(
        "key-in-the-seam", "The key, in the space the wedge leaves",
        "Two sawn faces meeting at a dihedral angle do not close flush. "
        "The frame is exploded here so you can see into the seam and see "
        "what fills it",
        chapter=7, config=_cfg(panel_explode_in=14.0),
        camera={"back": 2.05, "pitch": -12.0, "yaw": 78.0}))

    figures.append(Figure(
        "key-close", "One seam, close",
        "The same seam with the camera inside the gap. The key is the "
        "truncated point of the raw sector, not a machined part",
        chapter=7, config=_cfg(panel_explode_in=20.0),
        camera={"back": 1.70, "pitch": -8.0, "yaw": 84.0}))

    # -- the jig ------------------------------------------------------
    figures.append(Figure(
        "the-jig", "One flat jig, forty identical panels",
        "The jig that makes the joints repeatable, standing beside the "
        "dome it builds",
        chapter=9, config=_cfg(jig_enabled=True),
        camera={"back": 1.9, "pitch": -10.0, "yaw": 108.0}))

    # -- the skin -----------------------------------------------------
    figures.append(Figure(
        "with-skin", "The frame with its skin on",
        "The same frame with the shell offset four inches off the "
        "members, which is where a panel actually lands",
        chapter=12, config=_cfg(skin_enabled=True),
        camera={"back": 1.5, "pitch": -7.0}))

    # -- every permutation, with the standard marked ------------------
    for axis, spec in PERMUTATIONS.items():
        for value, blurb in spec["values"].items():
            standard = STANDARD.get(axis) == value
            token = str(value).replace("_", "-")
            figures.append(Figure(
                f"{axis.replace('_', '-')}-{token}",
                f"{axis.replace('_', ' ')}: {value}",
                f"{blurb.capitalize()}",
                chapter=spec["chapter"],
                config=_cfg(**{axis: value}, panel_explode_in=5.0),
                camera=dict(spec["camera"]),
                axis=axis, is_standard=standard))

    return figures


def by_chapter(chapter: int) -> list[Figure]:
    return [f for f in catalogue() if f.chapter == chapter]


# ----------------------------------------------------------------------
# Making them
# ----------------------------------------------------------------------

def spec_file(figures: list[Figure] | None = None,
              path: Path | None = None) -> Path:
    """Write the shot list the solver's --figures mode reads."""
    figures = figures if figures is not None else catalogue()
    path = path or (FIGURE_DIR / "_shots.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "shots": [
            {"key": f.key, "path": str(f.path), "config": f.config,
             "camera": f.camera, "hud": f.hud, "ground": f.ground}
            for f in figures
        ]
    }, indent=2), encoding="utf-8")
    return path


def render(figures: list[Figure] | None = None, timeout: int = 1800) -> dict:
    """Run the solver over the shot list. Needs a GPU and a display."""
    figures = figures if figures is not None else catalogue()
    spec = spec_file(figures)
    result = subprocess.run(
        [sys.executable, str(SOLVER), "--figures", str(spec)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    made = [f for f in figures if f.path.is_file()]
    return {"asked": len(figures), "made": len(made),
            "returncode": result.returncode,
            "stderr": result.stderr[-2000:] if result.returncode else ""}


def label(figures: list[Figure] | None = None) -> int:
    """Burn the credit line into the bottom of every rendered figure.

    In the image, not in a caption. A picture that gets pulled out of the
    PDF and posted somewhere should still say where it came from.
    """
    from PIL import Image, ImageDraw, ImageFont

    figures = figures if figures is not None else catalogue()
    done = 0
    for figure in figures:
        if not figure.path.is_file():
            continue
        image = Image.open(figure.path).convert("RGB")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", max(12, image.width // 110))
        except OSError:
            font = ImageFont.load_default()
        text = store.CREDIT
        box = draw.textbbox((0, 0), text, font=font)
        pad = max(6, image.width // 240)
        height = box[3] - box[1] + pad * 2
        draw.rectangle([0, image.height - height, image.width, image.height],
                       fill=(12, 16, 22))
        draw.text((pad, image.height - height + pad), text,
                  fill=(168, 184, 200), font=font)
        image.save(figure.path)
        done += 1
    return done


def record(figures: list[Figure] | None = None, db: Path | None = None) -> int:
    """Put the catalogue in the database so the book can ask what it owes."""
    figures = figures if figures is not None else catalogue()
    conn = store.connect(db)
    try:
        with conn:
            conn.execute("DELETE FROM figure")
            for figure in figures:
                conn.execute(
                    "INSERT INTO figure (key, chapter, title, caption, path,"
                    " recipe, credit, built) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (figure.key, figure.chapter, figure.title,
                     figure.full_caption(), str(figure.path), figure.recipe,
                     store.CREDIT, int(figure.path.is_file())))
        return len(figures)
    finally:
        conn.close()


def outstanding(db: Path | None = None) -> list[tuple[str, int, str]]:
    """Figures the book wants and does not have yet."""
    conn = store.connect(db)
    try:
        return list(conn.execute(
            "SELECT key, chapter, title FROM figure WHERE built = 0 "
            "ORDER BY chapter, key"))
    finally:
        conn.close()


def validate_figures() -> None:
    """The catalogue has to be buildable and every axis has to be covered."""
    figures = catalogue()
    assert len(figures) >= 18, len(figures)

    keys = [f.key for f in figures]
    assert len(set(keys)) == len(keys), "two figures share a key"

    # Two figures with the same config AND the same camera are the same
    # picture twice. That happened: every axis showed its standard value from
    # one shared viewpoint, so five files held one identical dome.
    shots = [(json.dumps(f.config, sort_keys=True),
              json.dumps(f.camera, sort_keys=True)) for f in figures]
    assert len(set(shots)) == len(shots), (
        "two figures would render the same picture; give the axis its own "
        "camera or drop the duplicate")
    for figure in figures:
        assert figure.title and figure.caption, figure.key
        assert figure.chapter >= 1, figure.key
        assert figure.config, figure.key
        # Every config must build a real DomeConfig and pass the solver's own
        # validation, or the shot dies at render time an hour into a batch.
        cfg = _dome_config(figure.config)
        cfg.validate()
        assert store.CREDIT in figure.full_caption(), figure.key

    # Every permutation axis shows all of its values, and exactly one of them
    # is marked as the reference build's.
    for axis, spec in PERMUTATIONS.items():
        shown = [f for f in figures if f.axis == axis]
        assert len(shown) == len(spec["values"]), (axis, len(shown))
        standard = [f for f in shown if f.is_standard]
        assert len(standard) == 1, (
            f"{axis}: {len(standard)} figures claim to be the standard")
        assert STANDARD[axis] in spec["values"], (
            f"the reference build uses {axis}={STANDARD[axis]!r}, which is "
            "not one of the values the book shows")

    # The ones that exist to show something hidden must actually explode the
    # frame, or they are the same picture as the standard dome.
    for key in ("key-in-the-seam", "key-close", "standard-dome-exploded"):
        figure = next(f for f in figures if f.key == key)
        assert figure.config.get("panel_explode_in", 0) > 0, key

    # And the shot file has to be writable and well-formed.
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        path = spec_file(figures, Path(folder) / "shots.json")
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert len(spec["shots"]) == len(figures)
        assert all(s["path"] and s["config"] for s in spec["shots"])


if __name__ == "__main__":
    validate_figures()
    figures = catalogue()
    print(f"{len(figures)} figures across "
          f"{len(set(f.chapter for f in figures))} chapters")
    for axis, spec in PERMUTATIONS.items():
        shown = [f for f in figures if f.axis == axis]
        print(f"  {axis:<24} {len(shown)} permutations "
              f"(standard: {STANDARD[axis]})")
    missing = [f for f in figures if not f.path.is_file()]
    print(f"  {len(figures) - len(missing)} rendered, {len(missing)} to make")
