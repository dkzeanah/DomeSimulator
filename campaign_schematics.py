"""Schematics and multi-view sheets for every concept a builder needs to know.

Each concept gets its orthographic views (top, the two elevations that
matter, bottom, sections), details, an exploded view where it has parts, one
composite drawing sheet, and one building-brick "turntable" sheet. The views
are described from the geometry, not from a general idea of a dome:

* ``view_geometry`` reads the 2V mesh the films draw and works out what each
  view actually shows -- which way the stars line up, how high each ring of
  junctions sits, how far out it lies in plan, how sharply neighbouring bays
  fold, and the angle of the V a seam leaves;
* ``check_view_geometry`` asserts the alignments the words rely on, so a
  change to the mesh fails the check rather than shipping a wrong drawing.

The assets join the pack in :mod:`campaign_prompts` and go through its
checks: no digit in any prompt (numbers belong in the overlay lines), and the
same colour key as every other image.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np

import pad_deck
import seed_model
from two_v_demo.geometry import build_demo_geometry

# ----------------------------------------------------------------------
# What each view shows, read off the mesh
# ----------------------------------------------------------------------

_FRACTIONS = ((1 / 4, "a quarter"), (1 / 3, "a third"), (2 / 5, "two-fifths"),
              (1 / 2, "half"), (3 / 5, "three-fifths"), (2 / 3, "two-thirds"),
              (3 / 4, "three-quarters"), (4 / 5, "four-fifths"),
              (5 / 6, "five-sixths"), (9 / 10, "nine-tenths"))


def fraction_words(x: float) -> str:
    """0.851 -> 'just over five-sixths'. For heights and radii in a prompt."""
    value, name = min(_FRACTIONS, key=lambda item: abs(item[0] - x))
    if abs(value - x) < 0.01:
        return f"exactly {name}" if abs(value - x) < 1e-3 else f"about {name}"
    return f"just {'over' if x > value else 'under'} {name}"


@dataclass(frozen=True)
class ViewGeometry:
    crown_point_height: float      # the crown star's points, fraction of height
    hourglass_height: float        # where the two equilateral triangles meet tip to tip
    lower_star_height: float
    crown_point_radius: float      # fraction of the base radius, in plan
    hourglass_radius: float
    lower_star_radius: float
    fold_long_deg: float           # bend between neighbouring bays across a long seam
    fold_short_deg: float
    star_point_deg: float          # the star triangle's angle at the star centre
    star_base_deg: float
    wedge_point_deg: float         # from the radial split of the log
    splits: int
    stars_on_axis: bool            # lower star centres directly under crown points
    hourglass_between: bool        # hourglass junctions halfway between star axes
    star_over_edge_middle: bool    # each lower star centre above a base-edge midpoint

    @property
    def seam_v_long_deg(self) -> float:
        """The channel a long seam leaves: the wedge's point angle less the fold."""
        return self.wedge_point_deg - self.fold_long_deg

    @property
    def seam_v_short_deg(self) -> float:
        return self.wedge_point_deg - self.fold_short_deg


def view_geometry() -> ViewGeometry:
    geo = build_demo_geometry()
    v = np.asarray(geo.vertices)
    edges = [tuple(map(int, e)) for e in geo.hemisphere_edges]
    faces = [tuple(map(int, f)) for f in geo.hemisphere_faces]
    length = lambda a, b: float(np.linalg.norm(v[a] - v[b]))  # noqa: E731
    short = min(length(a, b) for a, b in edges)
    is_short = lambda a, b: abs(length(a, b) - short) < 1e-6  # noqa: E731
    degree: Counter = Counter()
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    rings: dict[float, list[int]] = defaultdict(list)
    for i in degree:
        rings[round(float(v[i][2]), 4)].append(i)
    heights = sorted(rings, reverse=True)       # apex, crown points, hourglass, lower stars, base
    apex_z, crown_z, hour_z, star_z, base_z = heights
    azimuth = lambda i: round(math.degrees(math.atan2(v[i][1], v[i][0])) % 360.0, 3)  # noqa: E731
    radius = lambda i: float(math.hypot(v[i][0], v[i][1]))  # noqa: E731
    crown_az = sorted(azimuth(i) for i in rings[crown_z])
    star_az = sorted(azimuth(i) for i in rings[star_z])
    hour_az = sorted(azimuth(i) for i in rings[hour_z])
    base_az = sorted(azimuth(i) for i in rings[base_z])
    step = 360.0 / len(base_az)

    def normal(f):
        a, b, c = (v[i] for i in f)
        n = np.cross(b - a, c - a)
        n /= np.linalg.norm(n)
        return n if n @ (a + b + c) > 0 else -n

    faces_on: dict[tuple[int, int], list] = defaultdict(list)
    for f in faces:
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            faces_on[tuple(sorted((a, b)))].append(f)
    folds = defaultdict(set)
    for (a, b), pair in faces_on.items():
        if len(pair) == 2:
            angle = math.degrees(math.acos(float(np.clip(normal(pair[0]) @ normal(pair[1]), -1, 1))))
            folds["short" if is_short(a, b) else "long"].add(round(angle, 3))

    star_face = next(f for f in faces
                     if sum(is_short(a, b) for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0]))) == 2)
    centre = next(i for i in star_face if degree[i] == 5)
    others = [i for i in star_face if i != centre]

    def angle_at(p, q, r):
        x, y = v[q] - v[p], v[r] - v[p]
        return math.degrees(math.acos(float(x @ y / np.linalg.norm(x) / np.linalg.norm(y))))

    splits = int(seed_model.SEED_RADIAL_SPLITS)
    return ViewGeometry(
        crown_point_height=crown_z / apex_z,
        hourglass_height=hour_z / apex_z,
        lower_star_height=star_z / apex_z,
        crown_point_radius=radius(rings[crown_z][0]),
        hourglass_radius=radius(rings[hour_z][0]),
        lower_star_radius=radius(rings[star_z][0]),
        fold_long_deg=max(folds["long"]),
        fold_short_deg=max(folds["short"]),
        star_point_deg=angle_at(centre, *others),
        star_base_deg=angle_at(others[0], centre, others[1]),
        wedge_point_deg=360.0 / splits,
        splits=splits,
        stars_on_axis=crown_az == star_az,
        hourglass_between=all(round((h - c) % 360.0, 3) == round(step, 3)
                              for h, c in zip(hour_az, crown_az)),
        star_over_edge_middle=all(round((s - step / 2.0) % 360.0, 3) in base_az for s in star_az),
    )


def check_view_geometry(g: ViewGeometry) -> list[str]:
    problems = []
    if not g.stars_on_axis:
        problems.append("lower stars no longer sit under the crown's points -- rewrite the elevations")
    if not g.hourglass_between:
        problems.append("the hourglass junctions are no longer halfway between star axes")
    if not g.star_over_edge_middle:
        problems.append("lower star centres are no longer above base-edge midpoints")
    if not (g.crown_point_height > g.hourglass_height > g.lower_star_height):
        problems.append("ring heights changed order -- rewrite the elevations")
    return problems


def _deg(x: float) -> str:
    from campaign_prompts import about
    return f"{about(x)} degrees"


# ----------------------------------------------------------------------
# The drawing styles
# ----------------------------------------------------------------------

STYLE_SCHEMATIC = (
    "STYLE -- A CLEAN TECHNICAL SCHEMATIC, the kind of drawing an architect "
    "or a construction-kit designer makes. Crisp vector line work on plain "
    "white paper inside a thin border frame. LINE WEIGHTS: visible outlines "
    "bold, internal edges medium, hidden edges thin and dashed, centre lines "
    "thin chain-dash (long dash, short dash), section cuts shaded with thin "
    "diagonal hatching. ORTHOGRAPHIC views have NO perspective: parallel lines "
    "stay parallel and nothing shrinks with distance. ISOMETRIC views use true "
    "isometric axes, again with no vanishing point. Colour is flat and muted, "
    "used only to identify parts by the colour key; no shading gradients, no "
    "shadows, no texture except faint wood grain on timber in section. "
    "Dimension lines, arrowheads and leader lines may be drawn, but every "
    "label space is left BLANK -- the numbers and words are added later. An "
    "empty title block sits in the lower-right corner. No text, no letters, "
    "no numbers, no logos anywhere. "
)

SHEET_LAYOUT = (
    "LAYOUT -- ONE DRAWING SHEET, THIRD-ANGLE PROJECTION: the FRONT view "
    "large in the lower left; the TOP view directly above it, aligned with it "
    "(same width, the same vertical lines carried up between them as faint "
    "projection lines); the RIGHT SIDE view directly to the right of the "
    "front, aligned with it (same height, faint horizontal projection lines "
    "between them); an ISOMETRIC view in the upper-right corner; any detail "
    "or section in the lower right, above the empty title block. Every view "
    "at the same scale except the details, which are drawn larger inside a "
    "circle. "
)

TURNTABLE_LAYOUT = (
    "LAYOUT -- A TWO-BY-TWO TURNTABLE SHEET of the same building-brick model, "
    "four equal panels separated by thin white gutters: top left, straight "
    "from the front at eye level; top right, straight from the side at eye "
    "level; bottom left, straight down from above; bottom right, the "
    "box-art three-quarter view from about thirty degrees above. Same model, "
    "same scale, same light and the same plain gradient background in all "
    "four panels. "
)


# ----------------------------------------------------------------------
# The concepts
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class View:
    key: str
    name: str
    prompt: str
    overlay: str = ""
    aspect: str = "4:3"


@dataclass(frozen=True)
class Concept:
    key: str
    title: str
    why: str                 # why a builder needs to know it -- the overlay headline
    views: tuple[View, ...]
    truth: bool = True       # prepend the dome description
    turntable: str = ""      # what the brick turntable shows; empty = none
    sheet: str = ""          # which views the composite sheet uses


def concepts(f, lay, g: ViewGeometry) -> list[Concept]:
    from campaign_prompts import about, words

    geo = seed_model.seed_geometry()
    crown_h = fraction_words(g.crown_point_height)
    hour_h = fraction_words(g.hourglass_height)
    star_h = fraction_words(g.lower_star_height)
    crown_r = fraction_words(g.crown_point_radius)
    hour_r = fraction_words(g.hourglass_radius)
    star_r = fraction_words(g.lower_star_radius)
    fold_l, fold_s = _deg(g.fold_long_deg), _deg(g.fold_short_deg)
    v_l, v_s = _deg(g.seam_v_long_deg), _deg(g.seam_v_short_deg)
    point = _deg(g.wedge_point_deg)
    one_in = f"one-{ {8: 'eighth', 6: 'sixth', 10: 'tenth', 12: 'twelfth'}.get(g.splits, 'eighth') }"
    long_ft = about(geo.long_edge_in / 12)
    short_ft = about(geo.short_edge_in / 12)
    trunk = about(seed_model.SEED_TRUNK_DIAMETER_IN)
    stock = {m.edge_type: m.stock_length_in for m in geo.members}
    seq = pad_deck.build_sequence("blocks")
    piers = next((s.detail.split()[0] for s in seq if "pier" in s.label), "")

    star_axis = (
        f"The FIVE STAR AXES: each lower star sits directly below one point of "
        f"the crown star, so along each of these five directions a single "
        f"vertical line runs from the apex, down a crown spoke to the crown's "
        f"point ({crown_h} of the way up), straight on down a lower star's top "
        f"spoke to that star's centre ({star_h} of the way up), and down to the "
        f"exact middle of one base-ring edge -- the stars touch point to point. ")
    gap_axis = (
        "The FIVE GAP AXES, exactly halfway between the star axes: here two "
        "equilateral triangles meet tip to tip like an hourglass -- one hanging "
        "point-down from an edge of the crown's outline, one standing point-up "
        f"on a base-ring edge -- their shared tip {hour_h} of the way up, with "
        "a lower star on either side. ")

    dome = Concept(
        "dome", "The whole frame", "Where every triangle is, from every side.",
        (
            View("top", "Top plan (looking straight down)",
                 "VIEW: orthographic plan from directly above, the frame only, "
                 "no panels. The outline is a regular ten-sided polygon (the base "
                 "ring). At the exact centre, the apex, with the crown star's five "
                 f"short caramel spokes radiating to its five points {crown_r} of "
                 "the way out to the rim; the crown's long tan outline joins those "
                 "points into a pentagon. Beyond each outline edge, a point-down "
                 f"equilateral triangle whose tip reaches {hour_r} of the way out. "
                 f"Five lower-star centres lie {star_r} of the way out, each on "
                 "the same line as a crown point, their spokes making five more "
                 "stars round the rim. Every line is straight; the drawing is "
                 "perfectly five-fold symmetric.", aspect="1:1"),
            View("front-star", "Elevation on a star axis",
                 "VIEW: orthographic elevation, looking horizontally along one of "
                 f"the five star axes, frame only. {star_axis}That vertical line "
                 "is the centre line of this drawing: a lower star faces the "
                 "viewer dead centre, its foot triangle standing on the base line, "
                 "with an hourglass pair of equilateral triangles either side of "
                 "it. The silhouette is a faceted half-circle, never a smooth arc."),
            View("front-gap", "Elevation on a gap axis",
                 "VIEW: orthographic elevation looking horizontally along one of "
                 f"the five gap axes, frame only. {gap_axis}That hourglass is the "
                 "centre of this drawing, with a lower star to each side of it "
                 "and the crown's outline edge across the top."),
            View("bottom", "Looking up from inside",
                 "VIEW: orthographic view looking straight UP from the centre of "
                 "the floor, the frame seen from inside. Every wedge shows its "
                 "sharp inward ridge, so the pattern is a lattice of ridges rather "
                 "than flat faces; along every seam the slim V channel between two "
                 "back-to-back wedges is visible as a dark groove. The cyan "
                 "utility column rises at the centre toward the apex; the backs "
                 "of the panels close every bay.", aspect="1:1"),
            View("section", "Section through the centre, on a star axis",
                 "VIEW: vertical section cut straight through the apex along a star "
                 "axis, the far half of the dome seen beyond the cut. Along the cut "
                 "edge, each cut wedge shows as a small hatched triangle, flat side "
                 "outward and point inward, with the panel as a thin line on its "
                 "outside face. The cyan column stands on the pad's service port in "
                 "the middle and rises to the seal cap at the apex. The pad is cut "
                 "too: deck boards, joists, beams, piers on gravel."),
            View("iso", "Isometric",
                 "VIEW: true isometric of the frame on its pad, frame only, short "
                 "wedges caramel and long wedges tan so all six stars read."),
        ),
        turntable="the stem cell with every bay panelled and the door bay open",
        sheet="the star-axis elevation as the front, the top plan, the gap-axis "
              "elevation as the side, and the isometric",
    )

    lengths = Concept(
        "lengths", "Two strut lengths, two triangles",
        "Only two lengths and two triangles make the whole dome.",
        (
            View("triangles", "The two triangles, face on",
                 "VIEW: two triangles drawn flat, face on, side by side at the "
                 "same scale. LEFT, the equilateral triangle: three long tan sides, "
                 "three equal corners. RIGHT, the star triangle: two short caramel "
                 f"sides meeting at the star centre at about {_deg(g.star_point_deg)}, "
                 f"and one long tan side opposite, the other two corners about "
                 f"{_deg(g.star_base_deg)} -- only slightly narrower than the "
                 "equilateral one. Dimension lines along every side, labels blank.",
                 overlay=(f"Equilateral: three long sides ({geo.long_edge_in:.2f} in). "
                          f"Star triangle: two short ({geo.short_edge_in:.2f} in) and one "
                          f"long. {dict(f.face_classes)['AAA']} and "
                          f"{dict(f.face_classes)['BAB']} of each.")),
            View("colour-plan", "Plan coloured by length",
                 "VIEW: the top plan of the frame with the SHORT members drawn "
                 "thick caramel and the LONG members thin tan, so the six stars "
                 "stand out as the only caramel shapes: one crown in the middle, "
                 "five round the rim.", aspect="1:1",
                 overlay=f"{lay.short_edges} short lines, all star spokes. "
                         f"{lay.long_edges} long lines, everything else."),
            View("colour-elevation", "Elevation coloured by length",
                 f"VIEW: the star-axis elevation, frame only. {star_axis}Short "
                 "members thick caramel, long members thin tan."),
        ),
        truth=True,
        sheet="the coloured plan, the coloured elevation, and the two triangles as a detail",
    )

    wedge = Concept(
        "wedge", "One wedge member", "Point in. Flat face out. Split, not milled.",
        (
            View("log", "Where it comes from: the log's end",
                 f"VIEW: the end of a round log, about {trunk} inches across, drawn "
                 f"face on with its growth rings. {words(g.splits).capitalize()} "
                 "straight radial split lines run from the pith to the bark like "
                 "pie slices, so every wedge's POINT is the heart of the tree. On one "
                 "slice, the curved bark edge is shown sawn off along a straight "
                 "chord: that straight chord becomes the wedge's FLAT FACE.",
                 aspect="1:1",
                 overlay=f"{g.splits} wedges from one round, {seed_model.SEED_TRUNK_DIAMETER_IN:.0f} in log."),
            View("end", "End view -- the cross-section",
                 f"VIEW: the wedge's end, face on, large: an isosceles triangle, "
                 f"{one_in} of the log -- the point angle {point} -- with the flat "
                 "face along the top, drawn with a thick line and marked by a small "
                 "arrow pointing up and out of the page to show 'this side faces out "
                 "of the dome', and the point at the bottom marked by an arrow "
                 "pointing to the dome's centre. Growth-ring arcs faint in the "
                 "section. Dimension lines for the face width and the depth, labels "
                 "blank.", aspect="1:1",
                 overlay=(f"{geo.member_width_in:.2f} in flat face · "
                          f"{geo.member_depth_in:.0f} in deep · {g.wedge_point_deg:.0f} "
                          "degree point")),
            View("three-view", "Three views of one member",
                 "VIEW: one straight wedge member in three aligned orthographic "
                 "views: its FACE (from outside the dome, a long narrow flat "
                 "rectangle), its SIDE (a long bar whose depth tapers to the "
                 "ridge line of the point), and its END (the triangle). Both ends "
                 "are cut square across, not mitred. Two versions stacked: a long "
                 f"member of about {long_ft} feet and a short one of about "
                 f"{short_ft} feet.",
                 overlay=(f"Long member stock {stock['A']:.1f} in · short member "
                          f"stock {stock['B']:.1f} in.")),
            View("placed", "How it sits in the dome",
                 "VIEW: a small cut-away of the dome's wall in isometric with one "
                 "wedge highlighted in place: flat face flush with the outside "
                 "surface under its panel, point aimed at the dome's centre, a "
                 "dashed line from the point to the centre of the dome."),
        ),
        truth=False,
        turntable="a single long tan wedge standing on a small plinth, and a "
                  "short caramel one beside it",
        sheet="the three views, the end view as a large detail, and the log's end",
    )

    seam = Concept(
        "seam", "The seam between two bays",
        "The gap everyone machines away, kept on purpose.",
        (
            View("section", "Section across a seam",
                 "VIEW: a section cut straight across one seam, large: two "
                 "triangular wedge sections side by side, back to back, points "
                 "downward (toward the dome's inside), flat faces upward. The two "
                 "flat faces are NOT quite in line: they fold downward at the seam "
                 f"by a shallow angle ({fold_l} across a long seam, {fold_s} across "
                 "a short one). The two wedges touch only at their outer corners; "
                 f"below that their sides spread apart into a V-shaped channel open "
                 f"toward the inside -- about {v_l} wide at a long seam and {v_s} at "
                 "a short one. The cream panels lie over the flat faces above. A "
                 "yellow cable lies in the channel. Angle arcs for the fold and the "
                 "V, labels blank.", aspect="3:2",
                 overlay=(f"Fold {g.fold_long_deg:.1f} deg (long seams), "
                          f"{g.fold_short_deg:.1f} deg (short). Channel V = "
                          f"{g.wedge_point_deg:.0f} deg point less the fold: "
                          f"{g.seam_v_long_deg:.1f} / {g.seam_v_short_deg:.1f} deg.")),
            View("iso", "A length of seam, isometric",
                 "VIEW: isometric of a short length of one seam cut out of the "
                 "wall: two wedges back to back, the panels over them cut back a "
                 "little to show their edges, the V channel running the full "
                 "length underneath like a gutter, open to the inside."),
            View("inside", "Seen from inside",
                 "VIEW: orthographic view of the seam from inside the dome, looking "
                 "outward: two sharp inward ridges running side by side and the "
                 "dark V channel between them, straight, from junction to junction."),
        ),
        truth=False,
        sheet="the section as the front, the inside view as the top, and the isometric",
    )

    junctions = Concept(
        "junctions", "The three kinds of junction",
        "No hubs: wedges meet wedges, pinwheel-fashion.",
        (
            View("five-way", "Five-way junction (a star's centre)",
                 "VIEW: a close orthographic view from INSIDE of the junction at a "
                 "star's centre: five bays meet here, each bringing two of its own "
                 "wedges, so ten wedge ends arrive, laid pinwheel-fashion -- each "
                 "end butting against the side of the next, turning in one "
                 "direction round the point, none cut to a point. Five V channels "
                 "radiate from the junction between the pairs.", aspect="1:1"),
            View("six-way", "Six-way junction",
                 "VIEW: the same kind of close view of a junction where six bays "
                 "meet: twelve wedge ends in the same pinwheel, six V channels "
                 "radiating.", aspect="1:1"),
            View("base", "Base-ring corner",
                 "VIEW: the same close view of a corner of the base ring: three "
                 "bays meet, the single base-ring wedges run along the bottom, and "
                 "the corner stands on the pad's rim.", aspect="1:1"),
            View("outside", "The same junctions from outside",
                 "VIEW: three small face-on views from OUTSIDE, side by side, of "
                 "the five-way, six-way and base-corner junctions with the panels "
                 "on: only flat triangular panels meeting at a point with thin even "
                 "seam lines -- no hub, no plate, no bolt visible.", aspect="3:1"),
        ),
        truth=False,
        turntable="a five-way junction of ten short caramel wedge ends in a "
                  "pinwheel, as a small display model",
        sheet="the five-way, six-way and base-corner views from inside, and the "
              "outside strip",
    )

    bay = Concept(
        "bay", "One bay and its panel",
        "The panel decides what the building is.",
        (
            View("face", "Face on, from outside",
                 "VIEW: one bay face on from outside: a flat cream triangular panel "
                 "covering its three wedges' outer faces, four small flush screw "
                 "heads spaced around its edge, thin seam lines along its three "
                 "sides.", aspect="1:1"),
            View("section", "Section through the bay",
                 "VIEW: a section cut across the bay: at each side a wedge triangle, "
                 "point inward; the panel lying ON the wedges' outer faces, a screw "
                 "passing through it into a threaded insert in the wedge; behind the "
                 "panel an empty cavity as deep as the wedges; the V channels at "
                 "each side connecting this cavity to the next.", aspect="3:2"),
            View("exploded", "Exploded",
                 "VIEW: isometric exploded view along the bay's outward axis, parts "
                 "separated and aligned: the triangular frame of three wedges; the "
                 "four threaded inserts drawn just out of their holes; the spline "
                 "gasket; the panel; the four screws above it, dashed lines showing "
                 "where each goes.", aspect="1:1"),
        ),
        truth=False,
        turntable="one triangular bay as a small display piece: three wedges and "
                  "a cream panel, one screw lifted out",
        sheet="the face as the front, the section as a detail, and the exploded "
              "view in the isometric corner",
    )

    column = Concept(
        "column", "The utility column",
        "Everything comes up the middle and out the top.",
        (
            View("elevation", "Elevation, cover off",
                 "VIEW: orthographic front elevation of the cyan square column from "
                 "the floor port to the apex with its front cover removed, services "
                 "at their true heights: at the foot, the yellow feeder inlet and "
                 "the grey drain trap; at knee height, the blue shutoff valve on the "
                 "riser; at chest height, the grey sub-panel with a row of four "
                 "breakers; beside it the blue manifold with four valves and capped "
                 "stubs; the grey stack running the full height; the yellow lighting "
                 "line rising to the top.", aspect="9:16",
                 overlay=f"Column rise {f.column_rise_ft:.1f} ft, floor port to apex."),
            View("plan", "Plan section",
                 "VIEW: horizontal section cut through the column at chest height, "
                 "seen from above: the square chase, its insulated walls hatched, "
                 "and inside it, in their own corners, the round blue riser, the "
                 "larger round grey stack, and the yellow conduit, with the "
                 "sub-panel against the front wall and the removable cover as a "
                 "separate line.", aspect="1:1"),
            View("apex", "Apex detail",
                 "VIEW: large section through the apex: the column's top landing in "
                 "the flanged apex sleeve with a black gasket ring; the round seal "
                 "cap over it with its over-centre catches at the rim; the frame's "
                 "crown wedges around it; under the cap, a neat bundle of lines "
                 "turning outward and running down the outside of the dome.",
                 aspect="1:1"),
            View("exploded", "Exploded",
                 "VIEW: isometric exploded view of the column: base on the service "
                 "port, chase sections, cover panel, sub-panel, manifold, riser, "
                 "stack and trap, apex sleeve, gasket, seal cap -- all aligned on "
                 "one vertical axis.", aspect="9:16"),
        ),
        truth=False,
        turntable="the cyan utility column standing alone, cover off, services inside",
        sheet="the elevation as the front, the plan section as the top, the apex "
              "detail, and the exploded isometric",
    )

    pad = Concept(
        "pad", "The pad", "Built once by the host; the dome lands on it.",
        (
            View("plan", "Plan",
                 "VIEW: orthographic plan of the ten-sided pad from above: the deck "
                 "boards in parallel lines, the square amber service port at the "
                 "exact centre, the amber electrical pedestal at one edge, the amber "
                 "frost valve beside it, hinged amber storage hatches, and the "
                 "dome's base ring as a dashed ten-sided outline just inside the "
                 "pad's edge, corners resting on the rim.", aspect="1:1",
                 overlay=f"Pad {f.pad_across_ft:.1f} ft across · {piers} piers."),
            View("framing", "Framing plan (boards removed)",
                 "VIEW: the same plan with the boards removed: the grid of dark "
                 "grey pier blocks, the doubled beams across them, the joists at "
                 "close regular spacing across the beams, framing trimmed round the "
                 "square service port at the centre.", aspect="1:1"),
            View("section", "Section through the service port",
                 "VIEW: vertical section through the centre of the pad: gravel on "
                 "fabric, pier blocks, beams, joists, boards, the moisture barrier; "
                 "the amber tank in the space beneath; up through the square port, "
                 "three lines -- yellow power, blue water, grey drain -- capped just "
                 "above the deck.", aspect="3:2"),
        ),
        truth=False,
        turntable="the empty ten-sided pad on its piers, service port capped",
        sheet="the section as the front, the plan as the top, and the framing plan",
    )

    joints = seed_model.interfaces()
    interface = Concept(
        "interface", "Where the dome meets the pad",
        f"{len(joints)} connections and a lift.",
        (
            View("section", "Section at landing",
                 "VIEW: a vertical section through the centre just as the dome is "
                 "lowered, a hand's width above the pad: the column's base above "
                 "the square service port; the yellow feeder plug above the amber "
                 "pedestal's socket; the blue riser above the blue water stub; the "
                 "grey stack above the grey drain connection -- each pair joined by "
                 "a short dashed alignment line.", aspect="3:2",
                 overlay=" | ".join(f"{s}: {what}" for s, what, _ in joints)),
        ),
        truth=False,
    )

    layers = Concept(
        "layers", "The layers of the shell",
        "Only the outer cap is waterproof.",
        (
            View("section", "Wall section",
                 "VIEW: a large section through the wall from inside to outside: "
                 "the wedge (triangle, point inward); the cream panel on its outer "
                 "face; the single translucent white breather sheet; three quilted "
                 "fabric layers in muted patchwork colours; a thin vented gap held "
                 "open by a strap; the smoke-blue outer cap. Each layer drawn its "
                 "own thickness with a blank leader line to it.", aspect="3:2"),
            View("hem", "Half-section at the base",
                 "VIEW: the lower edge of the dome in section: the cap hanging past "
                 "the quilts, hemmed with a grommet, a webbing strap running from "
                 "the grommet to an anchor at the base-ring corner on the pad's "
                 "rim; small arrows showing rain running off the hem outside the "
                 "pad.", aspect="1:1"),
            View("growth", "Why the cap grows",
                 "VIEW: three concentric half-circle outlines drawn over the same "
                 "base line in elevation: the frame, the frame plus one quilt, the "
                 "frame plus four quilts, each cap outline a little larger, "
                 "dimension lines between them with blank labels.", aspect="3:2"),
        ),
        truth=False,
        sheet="the wall section as the front, the hem detail, and the growth diagram",
    )

    polyp = Concept(
        "polyp", "The utility panel outside",
        "Noisy, hot and weather-facing equipment lives outside.",
        (
            View("front", "Front and side",
                 "VIEW: two aligned orthographic views of the cyan utility-panel "
                 "cabinet: front (a narrow upright cabinet with a hinged weather lid "
                 "on top) and side (showing the lid's slope and the gasketed "
                 "pass-through at the back).", aspect="3:2"),
            View("route", "Plan of the route",
                 "VIEW: plan from above of the dome on its pad with ONE line drawn "
                 "from the seal cap at the centre, down the outside of the dome along "
                 "the panels, over the base ring, to the cabinet standing just "
                 "outside the pad.", aspect="1:1"),
        ),
        truth=False,
        turntable="the cyan utility-panel cabinet with its lid open",
    )

    floor = Concept(
        "floor", "The dome's own floor",
        "The pad is the host's; this floor travels with the dome.",
        (
            View("plan", "Framing plan",
                 f"VIEW: plan from above: a steel hub ring at the centre clamping the "
                 f"mast; {words(f.base_sides)} straight steel spokes running from the "
                 f"hub to the {words(f.base_sides)} corners of the base ring; "
                 "timber decking drawn over half of it; an edge rail round the rim.",
                 aspect="1:1"),
        ),
        truth=False,
    )

    rig = Concept(
        "rig", "The floating rig", "A design possibility -- loads are an engineer's numbers.",
        (
            View("elevation", "Elevation",
                 "VIEW: orthographic elevation: the dome hanging clear of the ground "
                 "between trees, from cables that run from saddles on the trunks to "
                 "a hanger on the mast's lifting ring above the seal cap; the steel "
                 "mast drawn dashed through the middle of the dome; a brake winch "
                 "at the foot of one tree.", aspect="16:9"),
            View("plan", "Plan",
                 "VIEW: plan from above: the dome at the centre and three trees "
                 "evenly spaced round it, a third of a turn apart, the three cable "
                 "legs meeting over the apex.", aspect="1:1"),
        ),
        truth=False,
    )

    network = Concept(
        "seams", "The seam network",
        "Every channel reaches every junction.",
        (
            View("plan", "Plan of the network",
                 f"VIEW: the top plan of the dome drawn as a network diagram: every "
                 f"seam as a white channel line, every junction as a small node -- "
                 f"{words(f.vertices)} nodes in all -- and a collector box at the base "
                 "where the lines gather. Panels shown pale, only the network strong.",
                 aspect="1:1"),
        ),
        truth=False,
    )

    return [dome, lengths, wedge, seam, junctions, bay, column, pad, interface,
            layers, polyp, floor, rig, network]


def schematic_assets(f, lay) -> list:
    """Every view, a composite sheet per concept, and a brick turntable."""
    from campaign_prompts import AVOID, Asset

    g = view_geometry()
    out = []
    for c in concepts(f, lay, g):
        for view in c.views:
            out.append(Asset(
                f"SCH-{c.key}-{view.key}", f"{c.title} -- {view.name}",
                "Book plate, Kickstarter 'how it works', instruction booklet, "
                "explainer carousel",
                view.aspect, f"{view.prompt} {AVOID}", style="schematic",
                truth=c.truth, overlay=view.overlay or c.why))
        if c.sheet:
            out.append(Asset(
                f"SHEET-{c.key}", f"{c.title} -- multi-view drawing sheet",
                "One-page reference, poster, book spread", "4:3 (landscape sheet)",
                f"SUBJECT: {c.title.lower()}. {SHEET_LAYOUT}Use these views: "
                f"{c.sheet}. What each shows: "
                + " ".join(v.prompt.replace("VIEW: ", f"[{v.name.upper()}] ")
                           for v in c.views) + f" {AVOID}",
                style="schematic", truth=c.truth, overlay=c.why))
        if c.turntable:
            out.append(Asset(
                f"TURN-{c.key}", f"{c.title} -- turntable (brick model, four views)",
                "Carousel, Kickstarter gallery, instruction booklet cover", "1:1",
                f"SUBJECT: {c.turntable}. {TURNTABLE_LAYOUT}{AVOID}",
                style="brick", truth=c.truth or c.key == "dome", overlay=c.why))
    return out
