"""The book's pictures, made by operating the solver rather than drawing it.

Most technical books illustrate an idea by drawing a picture of the idea.
This one does something else: it *runs the tool* with the settings that make
the idea visible, and prints what comes out. If the book says the key fills
the space the wedge leaves at a seam, the figure beside it is the real solver
with the frame exploded far enough to see into the seam, and the key in it is
the key the fabrication package would cut.

OPERATING IT, NOT SCREENSHOTTING IT

A screenshot of this tool is not an illustration. Open it and you get the
mathematical wireframe, twenty-six node markers, the pinwheel debug lines and
the sacrificial head stock hanging off every corner, all drawn on top of each
other -- four diagnostics competing with the thing the caption is pointing at.
That is right for somebody driving the tool and wrong for a page.

So every figure here carries a **view**: which of those layers are on. Most
use :data:`NEAT`, which switches the four of them off and leaves the wood, the
key and the ground. A figure about the geometry turns the wireframe back on,
because there the wireframe *is* the subject; a figure about the flush cut
turns the head stock back on, because the point is that it is there.

Figures are aimed rather than posed, too. ``camera: {"aim": {...}}`` names a
solved place -- a seam, a vertex, a panel, the apex -- and the solver puts the
camera at a distance from it and looks at it. A hand-tuned yaw and pitch is a
guess that stops being right the moment the dome changes size.

WHY THIS LETS THE BOOK SHOW EVERYTHING

Every figure is reproducible: the recipe is a dict of :class:`DomeConfig`
overrides, a view and a camera, stored beside the image. So the book can
afford **permutations**. A chapter that recommends one way of doing something
shows the other three beside it for the price of three more entries in a
list -- and :data:`PERMUTATIONS` does that for every decision the solver
exposes, marking which one the reference build assumes, so a reader who wants
to do it differently can see what they are choosing rather than being told.

Every image carries :data:`store.CREDIT`, burned into the file rather than
written in a caption somewhere, because captions get separated from pictures
and a picture that leaves this repository should still say where it came
from.
"""

from __future__ import annotations

import functools
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
#
# The two members are 72.000 in and whatever the geometry then forces, which
# is 63.670. The wedge's point faces into the dome. Those are the book's
# reference build, checked against the solve in wedge_book.numbers.
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
    # Off by default. It defaults to on in the solver, which is right for
    # somebody driving it and wrong for a figure: the fixture sits thirty
    # inches off the dome's edge and lands in the corner of every wide shot
    # as an unexplained grey slab. The jig figures switch it back on.
    "jig_enabled": False,
}

# ----------------------------------------------------------------------
# The four view presets
# ----------------------------------------------------------------------

#: The illustration view. The wireframe, the node markers, the joint debug
#: lines and the sacrificial head stock all off, because in a printed figure
#: they are four overlapping diagnostics over the subject. This is what most
#: figures in the book use and it is what the author asked for by name:
#: edge trimmings off, for a neater look.
NEAT: dict = {"ideal": False, "nodes": False, "joints": False,
              "overfit": False}

#: For a figure whose subject *is* the mathematical geometry: the wireframe
#: back on, coloured A against B, with the wood still there to sit inside it.
GEOMETRY: dict = {"ideal": True, "nodes": True, "joints": False,
                  "overfit": False}

#: Wireframe alone. No wood, no key, no fixture: the 2V solution as a
#: drawing, which is the only figure in the book that is a drawing.
WIREFRAME: dict = {"wood": False, "spacer": False, "ideal": True,
                   "nodes": True, "joints": False, "overfit": False,
                   "skin": False}

#: The frame with nothing in the seams, for a figure about the frame.
FRAME_ONLY: dict = {**NEAT, "spacer": False}

#: The seams the figures use, by where they sit rather than by their ids.
#:
#: The solver numbers seams in solve order, which puts SEAM_A_001 nine inches
#: under the apex -- so a camera standing off it is inside the roof, and the
#: first batch of close-ups came out as walls of wood. These three are chosen
#: by height: one at eye level on a real dome, one at shoulder, one high.
LOW_A_SEAM = "seam:SEAM_A_016"      # 30.6 in up: eye height

#: How a seam figure is framed. Standing above the seam and looking along it,
#: with the frame opened enough to separate the two panels from the key that
#: sits between them. Found by differencing renders with and without the key
#: rather than by guessing -- see the note in the module docstring.
SEAM_ELEVATION = 32.0
SEAM_AZIMUTH = 20.0
MID_B_SEAM = "seam:SEAM_B_004"      # 56.7 in up
HIGH_A_SEAM = "seam:SEAM_A_002"     # 80.2 in up

#: The head stock deliberately shown, for the two figures that are about it.
WITH_OVERFIT: dict = {"ideal": False, "nodes": False, "joints": False,
                      "overfit": True}


@dataclass(frozen=True)
class Figure:
    """One picture the book will print, and how to make it again."""

    key: str
    title: str
    caption: str
    chapter: int
    config: dict = field(default_factory=dict)
    camera: dict = field(default_factory=dict)
    #: Which layers are drawn. See :data:`NEAT` and the presets beside it.
    view: dict = field(default_factory=dict)
    #: ``stage``, ``panel`` and ``station`` for the fabrication jig.
    jig: dict = field(default_factory=dict)
    #: A seam to highlight, by id or index.
    seam: object = None
    # Which decision this figure is showing, and whether it is the one the
    # reference build uses. Both go in the caption.
    axis: str = ""
    is_standard: bool = False
    #: Which entry of the book's own illustration plan this figure satisfies.
    plan: str = ""
    # The tool's own HUD is off in a printed figure unless the HUD is what
    # the figure is about.
    hud: bool = False
    ground: bool = True
    console: bool = False

    @property
    def path(self) -> Path:
        return FIGURE_DIR / f"{self.key}.png"

    @property
    def recipe(self) -> str:
        return json.dumps({"config": self.config, "camera": self.camera,
                           "view": self.view, "jig": self.jig,
                           "seam": self.seam},
                          sort_keys=True, default=str)

    def shot(self) -> dict:
        """This figure as an entry in the solver's ``--figures`` spec."""
        entry = {
            "key": self.key, "path": str(self.path), "config": self.config,
            "camera": self.camera, "view": self.view,
            "hud": self.hud, "ground": self.ground, "console": self.console,
        }
        if self.jig:
            entry["jig"] = self.jig
        if self.seam is not None:
            entry["seam"] = self.seam
        return entry

    def full_caption(self) -> str:
        """What prints under the picture."""
        bits = [self.caption.rstrip(".")]
        if self.axis:
            bits.append("the reference build uses this" if self.is_standard
                        else "an alternative to the reference build")
        return ". ".join(bits) + f". {store.CREDIT}"


# ----------------------------------------------------------------------
# Asking the solver what a config comes out at
# ----------------------------------------------------------------------

def _solver():
    from . import numbers

    return numbers.solver()


def _dome_config(config: dict):
    """The solver's own DomeConfig, built from a figure's overrides."""
    return _solver().DomeConfig(**config)


@functools.lru_cache(maxsize=256)
def _solved(frozen: str):
    """A solved model for a config, cached, so captions can quote it.

    Captions in this book carry numbers -- how wide the seam channel comes out
    at twelve splits, what the spline base is on a fat wedge -- and those have
    to be read off the same solve the picture is drawn from rather than typed
    beside it.
    """
    config = _dome_config(json.loads(frozen))
    config.validate()
    return _solver().build_physical_model(config)


def solved(config: dict):
    return _solved(json.dumps(config, sort_keys=True))


def seam_facts(config: dict, edge_type: str = "A") -> dict:
    """The seam numbers a caption may quote, for one config."""
    model = solved(config)
    seam = next(s for s in model.seams if s.edge_type == edge_type)
    return {
        "fold_deg": seam.fold_angle_deg,
        "gap_deg": seam.raw_gap_angle_deg,
        "spline_in": seam.spacer_base_width_in,
        "hose_in": seam.hose_max_diameter_in,
        "depth_in": seam.contact_depth_in,
    }


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
        "camera": {"aim": {"at": LOW_A_SEAM, "distance_in": 84.0,
                           "azimuth_deg": SEAM_AZIMUTH,
                           "elevation_deg": SEAM_ELEVATION},
                   "fov": 44.0},
        "chapter": 2,
        "view": NEAT,
        "explode": 6.0,
        "plan": "Inward wedge orientation",
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
        "camera": {"aim": {"at": LOW_A_SEAM, "distance_in": 54.0,
                           "azimuth_deg": 16.0, "elevation_deg": 34.0},
                   "fov": 34.0},
        "chapter": 7,
        "view": NEAT,
        "explode": 8.0,
        "plan": "Triangle-to-triangle joint",
        "why": "What fills the gap two sawn faces leave at a seam. The "
               "trapezoid keeps the raw sector and truncates its point; "
               "the shaved flat machines a flat key instead.",
        "values": {
            "raw_trapezoid": "the raw sector, point truncated",
            "shaved_flat": "a machined flat key",
        },
    },
    "spacer_mode": {
        "camera": {"aim": {"at": MID_B_SEAM, "distance_in": 58.0,
                           "azimuth_deg": 16.0, "elevation_deg": 34.0},
                   "fov": 36.0},
        "chapter": 7,
        "view": NEAT,
        "explode": 10.0,
        "plan": "Exploded fastener/plate alternatives",
        "why": "What goes in the seam channel: a rigid spline, a hose, or "
               "nothing at all. The channel exists whether or not anybody "
               "uses it -- it is the space two sawn faces leave -- so the "
               "question is not whether to have it but what to put in it, "
               "and a hose makes the structure the plumbing.",
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
        # The seam framing shows nothing here: four splits and sixteen
        # look identical at a seam because what changes is how fat the stick
        # is, and that is read at a cut end. This is the trunk-diameter
        # viewpoint, turned the other way so the two axes are not one photo.
        "camera": {"aim": {"at": "vertex:5", "distance_in": 44.0,
                           "azimuth_deg": -30.0, "elevation_deg": -22.0},
                   "fov": 46.0},
        "chapter": 15,
        "view": WITH_OVERFIT,
        "explode": 0.0,
        "plan": ("Solid, hollow, laminated, split, log-derived, and hybrid "
                 "wedge comparison"),
        "why": "How many sectors the trunk is split into. Fewer splits "
               "means a fatter wedge and a deeper wall; more means thinner "
               "sticks and more of them. Eight is what the reference build "
               "uses because it is the split a person can do accurately "
               "with a froe and a wedge, not because the geometry prefers "
               "it -- and the seam channel it leaves shrinks fast as the "
               "count goes up, which is the cost nobody expects.",
        "values": {
            4: "four sectors: a quarter of the log, and a very deep wall",
            6: "six sectors: a fat wedge, a deep wall",
            8: "eight sectors: the reference build",
            12: "twelve sectors: thin sticks, more of them",
            16: "sixteen sectors: staves, and a seam channel under half an "
                "inch",
        },
    },
    "trunk_diameter_in": {
        # A different viewpoint from radial_splits on purpose. Both axes pass
        # through the reference build, and two figures of the same dome from
        # the same place are one figure printed twice. This one looks along a
        # member, because the trunk decides the section.
        "camera": {"aim": {"at": "vertex:5", "distance_in": 40.0,
                           "azimuth_deg": 34.0, "elevation_deg": -26.0},
                   "fov": 44.0},
        "chapter": 4,
        "view": NEAT,
        "explode": 7.0,
        "plan": "Nominal versus actual lumber cross-section",
        "why": "How big the tree was. The sector's width and depth come "
               "straight off the trunk, so the log decides the frame's "
               "section -- which is the opposite of buying a 2x6 and is the "
               "whole reason this method has a harvest argument.",
        "values": {
            8.0: "an eight-inch trunk: a slender frame",
            12.0: "a twelve-inch trunk: the reference build",
            16.0: "a sixteen-inch trunk: heavy section, fewer trees",
        },
    },
    "panel_joint_handedness": {
        "camera": {"aim": {"at": "face:AAA", "distance_in": 138.0,
                           "azimuth_deg": 0.0, "elevation_deg": 0.0},
                   "fov": 56.0},
        "chapter": 5,
        "view": NEAT,
        "explode": 4.0,
        "plan": "Saw/jig sequence for repetitive wedge production",
        "why": "Which way the three members of a triangle pinwheel. It "
               "mirrors the whole dome and it has to be the same in all "
               "forty panels.",
        "values": {
            "clockwise": "clockwise, seen from outside",
            "counterclockwise": "counterclockwise, seen from outside",
        },
    },
    "trapezoid_nose_depth_in": {
        "camera": {"aim": {"at": HIGH_A_SEAM, "distance_in": 36.0,
                           "azimuth_deg": 14.0, "elevation_deg": 36.0},
                   "fov": 24.0},
        "chapter": 7,
        "view": NEAT,
        "explode": 7.0,
        "plan": "Triangle-to-triangle joint",
        "why": "How much of the key's point is cut off. A true triangular "
               "key has a fragile edge that splits on the way in; "
               "truncating it gives the key a flat to bear on and a face to "
               "drive against.",
        "values": {
            0.25: "barely truncated: a fine point, easy to split",
            0.50: "the reference build",
            1.00: "a deep flat: strong, and it stands proud of the ridge",
        },
    },
    "head_overfit_in": {
        "camera": {"aim": {"at": "vertex:1", "distance_in": 58.0,
                           "azimuth_deg": 0.0, "elevation_deg": 0.0},
                   "fov": 42.0},
        "chapter": 6,
        "view": WITH_OVERFIT,
        "explode": 0.0,
        "plan": "Strut end-geometry and checking-jig detail",
        "why": "How much stock the head end carries past its finished "
               "plane. The butt is cut before assembly; the head is left "
               "long on purpose and flush-cut in place, so error leaves as "
               "offcut instead of accumulating around the triangle. Set it "
               "to nothing and you are back to measuring both ends.",
        "values": {
            0.0: "nothing: both ends cut to size, and the error has nowhere "
                 "to go",
            6.0: "the reference build's six inches",
            12.0: "a foot of it: generous, and a foot of offcut a stick",
        },
    },
    "skin_offset_in": {
        "camera": {"aim": {"at": "dome", "distance": 1.76,
                           "elevation_deg": 12.0}},
        "chapter": 11,
        "view": NEAT,
        "explode": 0.0,
        "skin": True,
        "plan": "Panel-to-wedge weather-seal detail",
        "why": "How far off the frame the panel sits. It is not zero: the "
               "panel lands on the members' outer faces and the seam key "
               "stands proud of them, so the skin has to clear both.",
        "values": {
            2.00: "tight to the frame",
            4.10: "the reference build",
            8.00: "standing well off, which is where a vented cavity goes",
        },
    },
    "long_edge_in": {
        "camera": {"aim": {"at": "dome", "distance": 1.84,
                           "elevation_deg": 12.0}},
        "chapter": 19,
        "view": NEAT,
        "explode": 0.0,
        "plan": ("Reference-design comparison sheet: demonstration, 12-ft, "
                 "16-ft, 20-ft, larger"),
        "why": "The one number that sets the size of the building. Every "
               "other dimension in the dome is this member and the 2V chord "
               "factors, which is why the book sizes from the stick rather "
               "than from the floor plan.",
        "values": {
            29.666: "a 4-foot radius: the demonstration dome",
            44.498: "a 6-foot radius: the twelve-foot dome",
            72.0: "the reference build's six-foot member",
            88.997: "a 12-foot radius: where the 2V starts to strain",
        },
    },
    "panel_explode_in": {
        "camera": {"aim": {"at": "dome", "distance": 1.98,
                           "elevation_deg": 15.0}},
        "chapter": 17,
        "view": NEAT,
        "explode": None,   # this axis *is* the explosion
        "plan": "Standardized interface / transportable module concept",
        "why": "An analysis-only explosion: every triangle slides out along "
               "its own face normal and nothing else moves. It is how the "
               "book gets to see between two panels, and it is also the "
               "modularity argument drawn -- forty separable objects that "
               "happen to be touching.",
        "values": {
            0.0: "assembled: the real building",
            6.0: "opened enough to see the seam",
            18.0: "forty separate panels and the keys that join them",
        },
    },
}


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

def _jig_stage_figures() -> list[Figure]:
    """The fabrication jig, one figure per step of its own walk-through.

    The solver carries a twelve-step sequence with a headline and a statement
    of what each step enforces. Those are the captions: the tool explains its
    own fixture better than a caption written beside a picture of it, and it
    cannot drift from what the picture shows because it is the same data the
    picture is built from.
    """
    rw = _solver()
    figures: list[Figure] = []
    # Which chapter each step belongs to. Making the wedges and the sticks is
    # chapter 5 and 6; putting three of them together is chapter 9.
    chapter_for = {
        "bench": 5, "triangle": 5, "rails": 5, "fences": 5, "guides": 5,
        "buttcut": 6, "member1": 9, "member2": 9, "member3": 9,
        "closed": 9, "flush": 6, "panel": 9,
    }
    # The corner is where the method either makes sense or does not, so the
    # three steps about the joint are shot from a corner station.
    station_for = {"member2": "CORNER 1", "member3": "CORNER 2",
                   "closed": "CORNER 3", "flush": "CORNER 1"}
    for index, (slug, headline, looking_at, enforcing) in enumerate(
            rw.JIG_STAGES):
        figures.append(Figure(
            f"jig-{index + 1:02d}-{slug}",
            headline.split(". ", 1)[-1].title(),
            f"{looking_at} {enforcing}",
            chapter=chapter_for.get(slug, 9),
            config=_cfg(jig_enabled=True),
            camera={"fov": 44.0},
            view={**NEAT, "overfit": True, "wood": False, "spacer": False},
            jig={"stage": slug, "panel": "BAB",
                 "station": station_for.get(slug, "WHOLE JIG")},
            plan="Saw/jig sequence for repetitive wedge production"))
    return figures


def catalogue() -> list[Figure]:
    """Every figure the book will print, in chapter order."""
    figures: list[Figure] = []
    add = figures.append
    reference = seam_facts(_cfg())

    # -- 1. Why build a dome -----------------------------------------
    add(Figure(
        "standard-dome", "The reference build",
        "A 2V dome on a six-foot longest member, wedge point inward, "
        "raw trapezoid seams. This is the dome the rest of the book "
        "assumes unless it says otherwise",
        chapter=1, config=_cfg(), view=NEAT,
        camera={"aim": {"at": "dome", "distance": 1.78,
                        "elevation_deg": 12.0}},
        plan="Complete 2V dome", is_standard=True))

    add(Figure(
        "dome-from-inside", "Standing in it",
        "The same dome from the middle of the floor, looking up at the "
        "apex. Every triangle you can see is one of two shapes",
        chapter=1, config=_cfg(), view=NEAT, ground=False,
        camera={"aim": {"at": "apex", "distance_in": -58.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 88.0},
        plan="Simple triangle-to-curved-shell explanation diagram"))

    add(Figure(
        "dome-side-elevation", "Half a sphere, ten sides on the ground",
        "The dome level-on, which is the view that shows a hemisphere is "
        "what this is: the apex is the radius and the base is a decagon",
        chapter=1, config=_cfg(), view=NEAT,
        camera={"aim": {"at": [0.0, 0.0, 52.0], "distance": 1.95,
                        "elevation_deg": 1.5}},
        plan="Complete 2V dome"))

    # -- 2. The wedge method -----------------------------------------
    add(Figure(
        "standard-dome-exploded", "The same dome, opened up",
        "The reference build with the panels pushed eight inches apart. "
        "Nothing has moved in the geometry -- this is the same solve, "
        "drawn with a gap -- and it is the only way to see what happens "
        "between two panels",
        chapter=2, config=_cfg(panel_explode_in=8.0), view=NEAT,
        camera={"aim": {"at": "dome", "distance": 1.92,
                        "elevation_deg": 14.0}},
        plan="Exploded 2V dome"))

    add(Figure(
        "wedge-cross-section", "One wedge, end on",
        "The end of a single member, close enough to read the section: a "
        "45-degree slice of a 12-inch log, two sawn radial faces and a bark "
        "face. Nothing has been machined -- this is what the froe leaves",
        chapter=2, config=_cfg(panel_explode_in=3.0), view=WITH_OVERFIT,
        camera={"aim": {"at": "vertex:1", "distance_in": 30.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 30.0},
        plan="Wedge cross-section"))

    add(Figure(
        "point-faces-in", "The point faces in",
        "The reference build's orientation, read off a seam: both wedges' "
        "points aim at the centre of the sphere, so the wide bark faces are "
        f"outside and the seam opens {reference['gap_deg']:.1f} degrees "
        "toward the weather",
        chapter=2, config=_cfg(panel_explode_in=9.0), view=NEAT,
        seam="SEAM_A_016",
        camera={"aim": {"at": LOW_A_SEAM, "distance_in": 80.0,
                        "azimuth_deg": SEAM_AZIMUTH,
                        "elevation_deg": SEAM_ELEVATION},
                "fov": 44.0},
        plan="Inward wedge orientation"))

    # -- 3. Understanding dome geometry ------------------------------
    add(Figure(
        "geodesic-wireframe", "The 2V solution, alone",
        "The mathematical dome with no wood in it: 26 vertices, 65 edges, "
        "40 triangles. The long A edges and the short B edges are coloured "
        "apart, and the ten base edges again",
        chapter=3, config=_cfg(), view=WIREFRAME,
        camera={"aim": {"at": "dome", "distance": 1.66,
                        "elevation_deg": 16.0}},
        plan="A-member highlighting"))

    add(Figure(
        "geometry-over-wood", "The wireframe over the frame",
        "The same mathematical edges drawn over the members that approximate "
        "them. No member lies on its edge: each one is offset by the "
        "sector's point, and neither of its ends reaches a vertex",
        chapter=3, config=_cfg(), view=GEOMETRY,
        camera={"aim": {"at": "face:BAB", "distance_in": 132.0,
                        "azimuth_deg": -16.0, "elevation_deg": 10.0},
                "fov": 62.0},
        plan="B-member highlighting"))

    add(Figure(
        "panel-aaa", "The AAA triangle",
        "One of the ten equilateral panels, alone. Three A members, 72.000 "
        "inches to a side as a chord, and an altitude of 62.354 inches",
        chapter=3, config=_cfg(), view={**NEAT, "solo_panel": True},
        jig={"panel": "AAA"},
        camera={"aim": {"at": "face:AAA", "distance_in": 104.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 44.0},
        plan="Two triangle families"))

    add(Figure(
        "panel-bab", "The BAB triangle",
        "One of the thirty isosceles panels: one A edge and two B, with an "
        "altitude of 52.516 inches above the long edge -- which is the "
        "number that decides whether a sheet of plywood fits",
        chapter=3, config=_cfg(), view={**NEAT, "solo_panel": True},
        jig={"panel": "BAB"},
        camera={"aim": {"at": "face:BAB", "distance_in": 96.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 44.0},
        plan="Two triangle families"))

    add(Figure(
        "dihedral-fold", "The fold between two panels",
        "Two triangles meeting at a seam, opened so the fold is readable. "
        f"An A seam folds {reference['fold_deg']:.3f} degrees and a B seam "
        f"{seam_facts(_cfg(), 'B')['fold_deg']:.3f}, and the two of them sum "
        "to the 45 degrees the log was split at",
        chapter=3, config=_cfg(panel_explode_in=11.0), view=NEAT,
        seam="SEAM_A_016",
        camera={"aim": {"at": LOW_A_SEAM, "distance_in": 96.0,
                        "azimuth_deg": 62.0, "elevation_deg": 26.0},
                "fov": 46.0},
        plan="Dihedral relationship"))

    # -- 4. Materials ------------------------------------------------
    add(Figure(
        "member-solo", "One member, out of the frame",
        "A single stick with the rest of the dome hidden: a log sector with "
        "a compound butt at one end and a flush-cut head at the other",
        chapter=4, config=_cfg(), view={**NEAT, "solo_panel": True},
        jig={"panel": "BAB"},
        camera={"aim": {"at": "face:BAB", "distance_in": 88.0,
                        "azimuth_deg": 26.0, "elevation_deg": 8.0},
                "fov": 44.0},
        plan="Grain/defect examples for member selection"))

    # -- 5 and 6 and 9. The jig, step by step ------------------------
    figures.extend(_jig_stage_figures())

    add(Figure(
        "the-jig", "One flat jig, forty identical panels",
        "The fixture with a panel closed on it: three butts bearing on "
        "three sides and three heads still hanging off long. Nothing on the "
        "jig is adjusted between panels, so panel forty is panel one",
        chapter=9, config=_cfg(jig_enabled=True),
        view={**NEAT, "overfit": True, "wood": False, "spacer": False},
        jig={"panel": "BAB", "station": "WHOLE JIG", "stage": "closed"},
        camera={"fov": 42.0},
        plan="Saw/jig sequence for repetitive wedge production"))

    # -- 6. Making the struts ----------------------------------------
    add(Figure(
        "heads-uncut", "Before the flush cut",
        "The assembled frame with every head end still carrying its six "
        "inches of stock. Uncut, the heads trespass across the geodesic "
        "vertex into the neighbouring panel -- which is the argument for "
        "cutting them in place",
        chapter=6, config=_cfg(), view=WITH_OVERFIT,
        camera={"aim": {"at": "vertex:8", "distance_in": 40.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 50.0},
        plan="Strut end-geometry and checking-jig detail"))

    add(Figure(
        "heads-cut", "After it",
        "The same corner with the stock gone. Every member now ends inside "
        "its own triangle and nothing crosses the vertex",
        chapter=6, config=_cfg(), view=NEAT,
        camera={"aim": {"at": "vertex:8", "distance_in": 40.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 50.0},
        plan="Strut end-geometry and checking-jig detail"))

    # -- 7. Connections ----------------------------------------------
    add(Figure(
        "key-in-the-seam", "The key, in the space the wedge leaves",
        "Two sawn faces meeting at a dihedral angle do not close flush. "
        "The frame is exploded here so you can see into the seam and see "
        f"what fills it: a key {reference['spline_in']:.2f} inches across "
        "its base",
        chapter=7, config=_cfg(panel_explode_in=12.0), view=NEAT,
        camera={"aim": {"at": LOW_A_SEAM, "distance_in": 64.0,
                        "azimuth_deg": SEAM_AZIMUTH,
                        "elevation_deg": SEAM_ELEVATION},
                "fov": 42.0},
        plan="Triangle-to-triangle joint"))

    add(Figure(
        "key-close", "One seam, close",
        "The same seam with the camera in the gap. The key is the truncated "
        "point of a raw sector, not a machined part -- it is cut from the "
        "same log as the members and at the same angle",
        chapter=7, config=_cfg(panel_explode_in=8.0), view=NEAT,
        camera={"aim": {"at": LOW_A_SEAM, "distance_in": 52.0,
                        "azimuth_deg": 16.0, "elevation_deg": 34.0},
                "fov": 32.0},
        plan="Triangle-to-triangle joint"))

    add(Figure(
        "keys-everywhere", "Every seam has one",
        "The frame from underneath, opened eight inches. There are "
        f"{len(solved(_cfg()).seams)} interior seams in this dome and every "
        "one of them carries a key. They are not fasteners and there are no "
        "fasteners in this picture: the key is what holds the angle",
        chapter=7, config=_cfg(panel_explode_in=8.0), view=NEAT,
        camera={"aim": {"at": LOW_A_SEAM, "distance_in": 56.0,
                        "azimuth_deg": 0.0, "elevation_deg": -30.0},
                "fov": 38.0},
        plan="Triangle-to-triangle joint"))

    add(Figure(
        "vertex-five", "A five-member vertex",
        "Where five triangles meet. Nothing arrives at the point: each "
        "member stops inside its own triangle and the corner is empty, "
        "which is what the pinwheel buys",
        chapter=7, config=_cfg(), view=GEOMETRY,
        camera={"aim": {"at": "vertex:0", "distance_in": 62.0,
                        "azimuth_deg": 0.0, "elevation_deg": -32.0},
                "fov": 52.0},
        plan="Five-member vertex"))

    add(Figure(
        "vertex-six", "A six-member vertex",
        "The other kind. Six triangles, same empty corner, same three cuts",
        chapter=7, config=_cfg(), view=GEOMETRY,
        camera={"aim": {"at": "vertex:6", "distance_in": 58.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 52.0},
        plan="Six-member vertex where applicable"))

    add(Figure(
        "vertex-base-three", "A base vertex",
        "At the rim only three members meet, because there is no panel "
        "below. It is the one vertex a builder sets out on the ground",
        chapter=7, config=_cfg(), view=GEOMETRY,
        camera={"aim": {"at": "vertex:16", "distance_in": 70.0,
                        "azimuth_deg": 0.0, "elevation_deg": 28.0},
                "fov": 48.0},
        plan="Three-member vertex"))

    # -- 8. Laying out the base --------------------------------------
    add(Figure(
        "base-ring-plan", "The base ring from above",
        "The ten base edges seen from overhead: a regular decagon 72.000 "
        "inches to a side, 60 feet around, which is the whole of the "
        "setting-out",
        chapter=8, config=_cfg(), view=GEOMETRY,
        camera={"aim": {"at": "centre", "distance": 1.62,
                        "elevation_deg": 74.0}},
        plan="Center/radius/base-polygon layout diagram"))

    add(Figure(
        "base-edge-close", "One base edge, on the ground",
        "Where a panel lands on the rim. The base edge is an A chord and "
        "the two members standing off it are the panel's own, so the "
        "ground plate carries two sticks and not a vertex",
        chapter=8, config=_cfg(), view=NEAT,
        camera={"aim": {"at": "base", "distance_in": 82.0,
                        "azimuth_deg": 0.0, "elevation_deg": 22.0},
                "fov": 44.0},
        plan="Base attachment"))

    # -- 9. Assembly -------------------------------------------------
    add(Figure(
        "course-first", "The first course",
        "The ten panels that stand on the ring, framed on their own. They "
        "lean in from the start, which is why the first course needs "
        "bracing and the second one does not",
        chapter=9, config=_cfg(), view=NEAT,
        camera={"aim": {"at": [0.0, 0.0, 26.0], "distance": 1.52,
                        "elevation_deg": 5.0},
                "fov": 56.0},
        plan="First course"))

    add(Figure(
        "course-second", "The second course",
        "The band above the first: thirty BAB panels leaning further in. "
        "This course is where the dome starts holding its own shape, and it "
        "is the point at which the bracing can come out",
        chapter=9, config=_cfg(), view=NEAT,
        camera={"aim": {"at": [0.0, 0.0, 84.0], "distance": 1.46,
                        "azimuth_deg": 16.0, "elevation_deg": 6.0},
                "fov": 56.0},
        plan="Second course"))

    add(Figure(
        "course-apex", "Closing the apex",
        "The top of the dome from below and outside: five panels around one "
        "vertex, which is the last thing to go in and the only part of the "
        "assembly that has to be held",
        chapter=9, config=_cfg(), view=NEAT,
        camera={"aim": {"at": "apex", "distance_in": 108.0,
                        "azimuth_deg": 0.0, "elevation_deg": -46.0},
                "fov": 52.0},
        plan="Apex assembly"))

    # -- 11. Panels and shells ---------------------------------------
    add(Figure(
        "with-skin", "The frame with its skin on",
        "The same frame with the shell offset 4.10 inches off the members, "
        "which is where a panel actually lands: clear of the outer faces "
        "and clear of the key standing proud of the ridge",
        chapter=11, config=_cfg(skin_enabled=True), view=NEAT,
        camera={"aim": {"at": "dome", "distance": 1.80,
                        "elevation_deg": 13.0}},
        plan="Insulated panel"))

    add(Figure(
        "skin-edge-close", "Where the panel meets the seam",
        "The shell's edge over an exploded seam, which is the detail every "
        "weather problem in this building happens at",
        chapter=11, config=_cfg(skin_enabled=True, panel_explode_in=8.0),
        view=NEAT,
        camera={"aim": {"at": HIGH_A_SEAM, "distance_in": 76.0,
                        "azimuth_deg": SEAM_AZIMUTH,
                        "elevation_deg": SEAM_ELEVATION},
                "fov": 44.0},
        plan="Panel-to-wedge weather-seal detail"))

    # -- 13. Utilities -----------------------------------------------
    add(Figure(
        "hose-route-close", "The seam as a service route",
        "A hose in the seam channel instead of a rigid key. The same space "
        f"that has to be filled anyway takes a {reference['hose_in']:.2f}-"
        "inch line, so air and water run in the structure rather than "
        "beside it",
        chapter=13, config=_cfg(spacer_mode="hose", panel_explode_in=9.0),
        view=NEAT,
        camera={"aim": {"at": MID_B_SEAM, "distance_in": 52.0,
                        "azimuth_deg": 14.0, "elevation_deg": 34.0},
                "fov": 34.0},
        plan="Utility routing",
        axis="", is_standard=False))

    add(Figure(
        "apex-inside", "The apex from inside",
        "Where the utility column arrives and the seal cap closes. Five "
        "seams converge here, which is why this is the one penetration the "
        "design allows",
        chapter=13, config=_cfg(spacer_mode="hose"), view=NEAT,
        ground=False,
        camera={"aim": {"at": "apex", "distance_in": -74.0,
                        "azimuth_deg": 0.0, "elevation_deg": 0.0},
                "fov": 68.0},
        plan="Apex utility interface"))

    # -- 14. Environmental control -----------------------------------
    add(Figure(
        "cutaway-inside-skin", "Inside, with the shell on",
        "The interior with the skin in place: the cavity between the "
        "members is the insulation's, and the seam channel behind the key "
        "is the only path through the envelope",
        chapter=14, config=_cfg(skin_enabled=True), view=NEAT,
        ground=False,
        camera={"aim": {"at": [0.0, 62.0, 62.0], "distance_in": 92.0,
                        "azimuth_deg": 180.0, "elevation_deg": 4.0},
                "fov": 86.0},
        plan="Insulation/ventilation/condensation path section"))

    # -- 18. The dome as a platform ----------------------------------
    add(Figure(
        "dome-and-fixture", "The building and the machine that makes it",
        "The dome and its jig in one frame, at the same scale. The fixture "
        "is a sheet of plywood and five cleats, and it is the entire "
        "manufacturing plant",
        chapter=18, config=_cfg(jig_enabled=True), view=NEAT,
        jig={"panel": "BAB", "stage": "closed"},
        camera={"aim": {"at": "dome", "distance": 2.35,
                        "azimuth_deg": 34.0, "elevation_deg": 19.0}},
        plan="Multi-dome / connected-dome concept plan"))

    # -- 20. Builder's reference -------------------------------------
    add(Figure(
        "tool-hud", "Reading the tool",
        "The solver as it opens, with its own heads-up display on. Every "
        "figure in this book was taken in this program, and this is the "
        "one figure where the display is the subject rather than the "
        "clutter",
        chapter=20, config=_cfg(), view=GEOMETRY, hud=True,
        camera={"aim": {"at": "dome", "distance": 1.86,
                        "elevation_deg": 13.0}},
        plan="Builder reference table legend"))

    add(Figure(
        "tool-cost-console", "The same tool, pricing the dome",
        "The cost console open over the solved dome. The geometry and the "
        "price are one program, which is why no number in this book has to "
        "be carried between two of them by hand",
        chapter=20, config=_cfg(cost_console_open=True,
                                cost_console_page="quote"),
        view=NEAT, console=True,
        camera={"aim": {"at": "dome", "distance": 1.98,
                        "azimuth_deg": -16.0, "elevation_deg": 12.0}},
        plan="Cut-list worksheet example"))

    # -- every permutation, with the standard marked ------------------
    for axis, spec in PERMUTATIONS.items():
        for value, blurb in spec["values"].items():
            standard = STANDARD.get(axis) == value
            if axis == "panel_explode_in":
                standard = value == 0.0
            if axis == "skin_offset_in":
                standard = abs(float(value) - 4.10) < 1.0e-9
            if axis == "head_overfit_in":
                standard = abs(float(value) - 6.0) < 1.0e-9
            if axis == "trapezoid_nose_depth_in":
                standard = abs(float(value) - 0.50) < 1.0e-9
            if axis == "long_edge_in":
                standard = abs(float(value) - 72.0) < 1.0e-9
            if axis == "trunk_diameter_in":
                standard = abs(float(value) - 12.0) < 1.0e-9
            token = str(value).replace("_", "-").replace(".", "p")
            overrides = {axis: value}
            explode = spec.get("explode")
            if explode is not None and axis != "panel_explode_in":
                overrides["panel_explode_in"] = explode
            if spec.get("skin"):
                overrides["skin_enabled"] = True
            if axis == "trapezoid_nose_depth_in":
                overrides["seam_join_mode"] = "raw_trapezoid"
            config = _cfg(**overrides)
            caption = blurb[0].upper() + blurb[1:]
            # Axes that change the seam say what the seam comes out at, so
            # the reader can see the consequence and not just the picture.
            if axis in ("radial_splits", "trunk_diameter_in",
                        "wedge_orientation"):
                facts = seam_facts(config)
                caption += (f". The A seam then wants a key "
                            f"{facts['spline_in']:.2f} in across its base")
            # "trunk diameter in: 8.0" is a variable name printed under a
            # picture. The blurb already says what the reader is looking at,
            # so the title is its first clause and the caption is the rest.
            head = blurb.split(":")[0].strip()
            title = (head[0].upper() + head[1:]) if len(head) > 6 else (
                f"{axis.replace('_', ' ')}: {value}")
            add(Figure(
                f"{axis.replace('_', '-')}-{token}",
                title,
                caption,
                chapter=spec["chapter"],
                config=config,
                camera=dict(spec["camera"]),
                view=dict(spec.get("view") or NEAT),
                axis=axis, is_standard=standard,
                plan=spec.get("plan", "")))

    return figures


def by_chapter(chapter: int) -> list[Figure]:
    return [f for f in catalogue() if f.chapter == chapter]


def coverage() -> dict:
    """What the book's own illustration plan asks for, against what exists."""
    book = store.load_json()
    wanted: dict[str, list[int]] = {}
    for key, items in (book.chapter_illustration_plan or {}).items():
        for item in (items if isinstance(items, list) else []):
            wanted.setdefault(str(item), []).append(int(key))
    have: dict[str, list[str]] = {}
    for figure in catalogue():
        if figure.plan:
            have.setdefault(figure.plan, []).append(figure.key)
    return {
        "wanted": wanted,
        "have": have,
        "unmet": sorted(name for name in wanted if name not in have),
    }


#: Illustration-plan entries the solver cannot produce, and why.
#:
#: The rule is that a figure is the tool operated, so an illustration the tool
#: cannot make does not get faked. Each of these names what would have to
#: exist for the figure to be real.
NOT_IN_THE_SOLVER: dict[str, str] = {
    "Conventional rectangular strut versus wedge strut":
        "the raw-wedge solver only builds log sectors. The comparison is "
        "arithmetic rather than a picture and the book makes it that way: "
        "the same pinwheel solved for a rectangular band loses 9.253 in a "
        "stick against the sector's 1.818",
    "Log divided into wedge members":
        "the solver starts from a solved sector and does not model the round "
        "trunk it came out of. radial_splits shows the consequence -- how "
        "fat the wedge is -- which is the part that changes the building",
    "Dimensional-lumber wedge-cutting layouts":
        "a sawing layout on rectangular stock, which is a different "
        "material from the one this tool solves",
    "Door opening":
        "the solver has no openings. Every panel it builds is whole, and a "
        "doorway is a panel left out plus a frame nothing here models",
    "Reinforced opening":
        "the same: an opening needs a header and posts, and this solver "
        "knows only the 120 members of the closed frame",
    "Window-frame integration diagram":
        "a window is a panel replaced rather than a frame changed, and the "
        "panel types live in the Creator's material tables, not here",
    "Removable panel":
        "panels are solved, not switchable. panel_explode_in shows them as "
        "forty separable objects, which is the same argument",
    "Temporary bracing and raising sequence":
        "the solver builds the finished dome, not a part-built one. There is "
        "no props-and-braces state in it, and inventing one would be a "
        "drawing of an idea rather than the tool operated. The courses are "
        "framed instead, which is what the reader can actually check against "
        "their own build",
    "Prepared dome pad":
        "the pad is priced in pad_deck and drawn in the park world, not "
        "here",
    "Slab/ring/pier/raised-floor comparison sections":
        "four foundations that pad_deck prices and no renderer draws in "
        "section",
    "Floor utility interface":
        "the floor is not in this solver's world",
    "Gasketed service cap":
        "the seal cap is seed_world's geometry, not this solver's",
    "Completed dome cutaway":
        "a true cutaway needs a clipping plane the solver does not expose; "
        "the inside shots are taken from inside instead",
    "Utility column":
        "the column is seed_world's, and the films draw it",
    "Frequency and truncation comparison silhouettes":
        "this solver builds 2V hemispheres only",
    "Prefabricated triangle module":
        "a single panel off the jig is the same object; jig-12-panel is it",
    "Material-yield worksheet example":
        "a worksheet rather than a picture. It is a table the builder's "
        "reference prints and wedge_book.numbers generates",
    "Blank project sheets":
        "deliberately blank. A ruled page for the reader to fill in is the "
        "one illustration in this book that is not allowed to contain "
        "anything",
}


# ----------------------------------------------------------------------
# Making them
# ----------------------------------------------------------------------

def spec_file(figures: list[Figure] | None = None,
              path: Path | None = None) -> Path:
    """Write the shot list the solver's --figures mode reads."""
    figures = figures if figures is not None else catalogue()
    path = path or (FIGURE_DIR / "_shots.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"shots": [figure.shot() for figure in figures]}, indent=2),
        encoding="utf-8")
    return path


def render(figures: list[Figure] | None = None, timeout: int = 3600) -> dict:
    """Run the solver over the shot list. Needs a GPU and a display."""
    figures = figures if figures is not None else catalogue()
    spec = spec_file(figures)
    result = subprocess.run(
        [sys.executable, str(SOLVER), "--figures", str(spec)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    made = [f for f in figures if f.path.is_file()]
    return {"asked": len(figures), "made": len(made),
            "returncode": result.returncode,
            "stdout": result.stdout[-1500:],
            "stderr": result.stderr[-3000:] if result.returncode else ""}


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
    rw = _solver()
    figures = catalogue()
    assert len(figures) >= 60, len(figures)

    keys = [f.key for f in figures]
    assert len(set(keys)) == len(keys), "two figures share a key"

    # Two figures with the same config AND the same camera AND the same view
    # are the same picture twice. That happened: every axis showed its
    # standard value from one shared viewpoint, so five files held one
    # identical dome.
    shots = [(json.dumps(f.config, sort_keys=True),
              json.dumps(f.camera, sort_keys=True),
              json.dumps(f.view, sort_keys=True),
              json.dumps(f.jig, sort_keys=True)) for f in figures]
    duplicates = [k for k in set(shots) if shots.count(k) > 1]
    assert not duplicates, (
        f"{len(duplicates)} shots would render the same picture twice; give "
        "the figure its own camera, view or config, or drop the duplicate")

    for figure in figures:
        assert figure.title and figure.caption, figure.key
        assert figure.chapter >= 1, figure.key
        assert figure.config, figure.key
        # Every config must build a real DomeConfig and pass the solver's own
        # validation, or the shot dies at render time an hour into a batch.
        cfg = _dome_config(figure.config)
        cfg.validate()
        assert store.CREDIT in figure.full_caption(), figure.key
        # Every view switch has to be one the solver knows, or the batch
        # raises on that shot and loses everything after it.
        for name in figure.view:
            assert name in rw.FIGURE_VIEW_KEYS, (figure.key, name)
        # And every jig instruction has to name a real step and station.
        stage = figure.jig.get("stage")
        if isinstance(stage, str):
            rw.jig_stage_index(stage)
        station = figure.jig.get("station")
        if isinstance(station, str):
            assert station == "WHOLE JIG" or station.startswith("CORNER "), (
                figure.key, station)

    # Every permutation axis shows all of its values, and exactly one of them
    # is marked as the reference build's.
    for axis, spec in PERMUTATIONS.items():
        shown = [f for f in figures if f.axis == axis]
        assert len(shown) == len(spec["values"]), (axis, len(shown))
        standard = [f for f in shown if f.is_standard]
        assert len(standard) == 1, (
            f"{axis}: {len(standard)} figures claim to be the standard")
        assert len(spec["why"]) > 80, f"{axis} does not say why it matters"

    # The reference build is the one the book says it is, in every figure
    # that does not deliberately change it.
    for figure in figures:
        if figure.axis in ("long_edge_in",):
            continue
        assert figure.config["long_edge_in"] == 72.0, figure.key
        if figure.axis != "wedge_orientation":
            assert figure.config["wedge_orientation"] == "point_dome_in", (
                figure.key)

    # The ones that exist to show something hidden must actually explode the
    # frame, or they are the same picture as the standard dome.
    for key in ("key-in-the-seam", "key-close", "standard-dome-exploded",
                "dihedral-fold", "point-faces-in"):
        figure = next(f for f in figures if f.key == key)
        assert figure.config.get("panel_explode_in", 0) > 0, key

    # The figures about the key must not be drawn with the wireframe, the
    # nodes, the debug lines or the sacrificial stock over them. This is the
    # whole reason the view presets exist, and it is easy to lose.
    for key in ("key-in-the-seam", "key-close", "point-faces-in",
                "skin-edge-close", "hose-route-close"):
        figure = next(f for f in figures if f.key == key)
        for switch in ("ideal", "nodes", "joints", "overfit"):
            assert figure.view.get(switch) is False, (key, switch)

    # The twelve jig steps are all there, in order, and each carries the
    # solver's own words rather than a caption written beside it.
    jig = [f for f in figures if f.key.startswith("jig-")]
    assert len(jig) == rw.JIG_STAGE_COUNT, len(jig)
    for index, (slug, _headline, looking, _enforcing) in enumerate(
            rw.JIG_STAGES):
        figure = jig[index]
        assert figure.key.endswith(slug), (figure.key, slug)
        assert looking.split(".")[0] in figure.caption, figure.key

    # The book's own illustration plan is either met or explained. An entry
    # that is neither is an illustration the book promises and nobody has.
    gaps = coverage()["unmet"]
    unexplained = [name for name in gaps if name not in NOT_IN_THE_SOLVER]
    assert not unexplained, (
        f"{len(unexplained)} illustrations the book's plan asks for have "
        "neither a figure nor a reason:" + store.NEWLINE_BULLET
        + store.NEWLINE_BULLET.join(unexplained))
    for name, why in NOT_IN_THE_SOLVER.items():
        assert len(why) > 25, f"{name} has no real reason attached"

    # And the shot file has to be writable and well-formed.
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        path = spec_file(figures, Path(folder) / "shots.json")
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert len(spec["shots"]) == len(figures)
        assert all(s["path"] and s["config"] for s in spec["shots"])


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--only", default="",
                        help="render only figures whose key starts with this")
    parser.add_argument("--coverage", action="store_true")
    args = parser.parse_args(argv)

    validate_figures()
    figures = catalogue()
    if args.coverage:
        report = coverage()
        print(f"{len(report['wanted'])} illustrations planned, "
              f"{len(report['have'])} met by a figure")
        for name in report["unmet"]:
            print(f"  not in the solver: {name}")
            print(f"      {NOT_IN_THE_SOLVER.get(name, '???')}")
        return 0

    chapters = sorted({f.chapter for f in figures})
    print(f"{len(figures)} figures across {len(chapters)} chapters "
          f"{chapters}")
    for axis, spec in PERMUTATIONS.items():
        shown = [f for f in figures if f.axis == axis]
        print(f"  {axis:<26} {len(shown)} permutations "
              f"(standard: {STANDARD.get(axis, '-')})")
    missing = [f for f in figures if not f.path.is_file()]
    print(f"  {len(figures) - len(missing)} rendered, {len(missing)} to make")

    if args.render:
        wanted = ([f for f in figures if f.key.startswith(args.only)]
                  if args.only else figures)
        print(f"rendering {len(wanted)} figures...")
        result = render(wanted)
        print(json.dumps({k: v for k, v in result.items()
                          if k != "stdout"}, indent=2))
        label(wanted)
        record(figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
