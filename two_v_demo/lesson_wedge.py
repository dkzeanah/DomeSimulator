"""Eight cuts to a house: a dome built straight from the tree.

A round trunk is normally squared, edged and trimmed until what is left
will stack on a pallet.  This lesson asks the opposite question -- what
does the *building* actually need? -- and answers it with a 2V
hemisphere whose members are raw 45-degree log sectors: split
half-quarter-eighth, crosscut once, and used with the curved bark face
outward and the pith line inward.

Two structural ideas hold the shell together, and both are drawn here
rather than described:

**The pinwheel panel.**  Each of the forty triangles is an independent
frame of three members.  Every member's end butts into the *side* of the
next one, the same way round for all three, so no end is mitred, coped
or shaved.  The mathematical corners are reference points that no stick
reaches.

**The duplicated seam.**  Neighbours never share a stick.  Each panel
carries its own member along a shared edge, and the pair meets through a
separate spline, key or hose gasket -- which is what absorbs the four
and a half degrees of dihedral variation that would otherwise have to be
cut into the wood, seam by seam.

Every figure comes from :mod:`two_v_demo.wedge_geometry` through
:mod:`two_v_demo.wedge_facts`; the panel drawings use the same laid-out
members the math screens measure.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .geometry import build_demo_geometry, normalize
from .lessons import Chapter, Lesson, math_shift, prose
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    RED,
    WHITE,
    TriangleBatch,
    WorldLabel,
    clamp,
    ease_in_out,
)
from .timber import BARK_TONE, CHAINSAW, draw_timber
from .wedge_facts import (
    ALL_SCREENS,
    LOG,
    PLAN,
    SUMMARY,
    YIELD,
    steps_actions,
    steps_compare,
    steps_dome,
    steps_lengths,
    steps_pinwheel,
    steps_radial,
    steps_rectangles,
    steps_sector,
    steps_seams,
    steps_trunk,
    validate_wedge_facts,
    wedge_facts_report,
)
from .wedge_geometry import (
    SECTOR_ANGLE_DEG,
    SECTORS_PER_LOG,
    member_classes,
    pinwheel_panels,
    section_rows,
    two_by_four_packing,
)


GEOMETRY = build_demo_geometry()
PANELS = pinwheel_panels(PLAN.radius_in, PLAN.member_width_in)
CLASSES = member_classes(PLAN.radius_in, PLAN.member_width_in)

# The shell is drawn at radius 5, so one real inch is this many scene
# units and a six-foot person stands this tall beside it.
SCENE_RADIUS = 5.0
TO_SCENE = SCENE_RADIUS / PLAN.radius_in
FOOT = 12.0 * TO_SCENE
MEMBER_DEPTH = PLAN.member_depth_in * TO_SCENE
MEMBER_WIDTH = PLAN.member_width_in * TO_SCENE

WOOD = (0.66, 0.47, 0.28, 1.0)
WOOD_DARK = (0.47, 0.33, 0.20, 1.0)
BARK = BARK_TONE
SAWDUST = (0.72, 0.63, 0.44, 1.0)


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _fade(colour, alpha: float):
    return (colour[0], colour[1], colour[2], clamp(alpha) * colour[3])


def _label(app, point, text: str, colour) -> None:
    app.world_labels.append(
        WorldLabel(np.asarray(point, dtype=float), text, _rgb(colour)))


def _face(batch, corners, colour, normal) -> None:
    """One quad, wound so its front side faces ``normal``."""
    a, b, c, d = (np.asarray(corner, dtype=float) for corner in corners)
    if float(np.dot(np.cross(b - a, c - a), normal)) < 0.0:
        a, b, c, d = d, c, b, a
    batch.quad(a, b, c, d, colour, normalize(np.asarray(normal, float)))


def _sector_profile(out: np.ndarray, side: np.ndarray, radius: float,
                    segments: int = 4,
                    angle_deg: float = SECTOR_ANGLE_DEG) -> list[np.ndarray]:
    """Offsets from the pith line to the bark, across one sector."""
    half = math.radians(angle_deg) * 0.5
    points = []
    for index in range(segments + 1):
        angle = -half + (2.0 * half) * index / segments
        points.append((out * math.cos(angle) + side * math.sin(angle))
                      * radius)
    return points


def _wedge_prism(batch, pith_start, pith_end, out_dir, radius: float,
                 wood=WOOD, bark=BARK, segments: int = 4,
                 angle_deg: float = SECTOR_ANGLE_DEG) -> None:
    """One raw log sector, apex on the pith line, bark facing ``out_dir``.

    This is the member as it comes off the saw: two flat radial faces,
    one curved bark face, and two square ends.  Nothing about it is
    milled, so nothing about it is drawn as though it were.
    """
    start = np.asarray(pith_start, dtype=float)
    end = np.asarray(pith_end, dtype=float)
    axis = end - start
    length = float(np.linalg.norm(axis))
    if length <= 1e-9 or radius <= 1e-9:
        return
    direction = axis / length
    out = np.asarray(out_dir, dtype=float)
    out = normalize(out - direction * float(np.dot(out, direction)))
    side = normalize(np.cross(direction, out))
    profile = _sector_profile(out, side, radius, segments, angle_deg)

    for index in range(len(profile) - 1):
        first, second = profile[index], profile[index + 1]
        outward = normalize(first + second)
        _face(batch, (start + first, start + second,
                      end + second, end + first), bark, outward)
    for offset, sign in ((profile[0], -1.0), (profile[-1], 1.0)):
        flank = normalize(np.cross(offset, direction)) * sign
        if float(np.dot(flank, side)) * sign < 0.0:
            flank = -flank
        _face(batch, (start, start + offset, end + offset, end),
              wood, flank)
    for point, normal in ((start, -direction), (end, direction)):
        for index in range(len(profile) - 1):
            batch.triangle(point, point + profile[index],
                           point + profile[index + 1], WOOD_DARK, normal)


def _panel_members(batch, panel, reveal: float = 1.0, scale: float = 1.0,
                   origin=None, depth: float | None = None,
                   wood=WOOD, bark=BARK) -> None:
    """Draw one panel's three pinwheel members, in assembly order."""
    shift = np.zeros(3) if origin is None else np.asarray(origin, float)
    depth = MEMBER_DEPTH * scale if depth is None else depth
    for index, member in enumerate(panel.members):
        if reveal < (index + 1) / 3.0:
            grow = clamp(reveal * 3.0 - index)
            if grow <= 0.02:
                continue
        else:
            grow = 1.0
        tail = np.asarray(member.tail) * TO_SCENE * scale + shift
        head = np.asarray(member.head) * TO_SCENE * scale + shift
        normal = np.asarray(member.normal)
        head = tail + (head - tail) * grow
        _wedge_prism(batch, tail - normal * depth, head - normal * depth,
                     normal, depth, wood, bark)


def _flat_panel(panel, scale: float, centre) -> tuple:
    """One panel, flattened out of the shell and laid on the ground.

    A panel sitting where it belongs on the sphere is seen edge-on from
    almost every camera, so the diagram chapters draw this instead: the
    same members, the same lengths, the same handedness, lying flat with
    the bark faces up.
    """
    corners = np.asarray(panel.corners, dtype=float)
    origin = corners.mean(axis=0)
    normal = normalize(np.asarray(panel.normal, dtype=float))
    axis_u = normalize(corners[0] - origin)
    axis_v = normalize(np.cross(normal, axis_u))
    place = np.asarray(centre, dtype=float)

    def flatten(point) -> np.ndarray:
        offset = np.asarray(point, dtype=float) - origin
        return place + np.array([float(np.dot(offset, axis_u)),
                                 float(np.dot(offset, axis_v)),
                                 0.0]) * TO_SCENE * scale

    members = tuple(
        (flatten(member.tail), flatten(member.head), member)
        for member in panel.members
    )
    return members, tuple(flatten(corner) for corner in corners)


def _draw_flat_panel(batch, panel, centre, scale: float, reveal: float = 1.0,
                     depth: float | None = None) -> tuple:
    """Draw a flattened panel, bark faces up, and return its geometry."""
    members, corners = _flat_panel(panel, scale, centre)
    depth = MEMBER_DEPTH * scale if depth is None else depth
    up = np.array([0.0, 0.0, 1.0])
    for index, (tail, head, _member) in enumerate(members):
        grow = clamp(reveal * 3.0 - index)
        if grow <= 0.02:
            continue
        end = tail + (head - tail) * grow
        _wedge_prism(batch, tail, end, up, depth, segments=5)
    return members, corners


def _flat_reference(batch, corners, colour=MUTED, radius: float = 0.03,
                    lift: float = 0.0) -> None:
    """The mathematical triangle under a flattened panel."""
    for index in range(3):
        start = np.asarray(corners[index]) + np.array([0.0, 0.0, lift])
        end = np.asarray(corners[(index + 1) % 3]) + np.array([0.0, 0.0,
                                                               lift])
        steps = 11
        for piece in range(0, steps, 2):
            a = start + (end - start) * (piece / steps)
            b = start + (end - start) * ((piece + 1) / steps)
            batch.cylinder(a, b, radius, colour, 4)


def _align_flat(edge_a, edge_b, centre, mirror: bool = False):
    """Turn a flattened panel so one edge lies along X at ``centre``.

    ``edge_a`` and ``edge_b`` are that edge's two corners, already
    flattened.  Mirroring lays the second panel of a pair on the other
    side of the seam, which is how the two of them read as neighbours.
    """
    edge_a = np.asarray(edge_a, dtype=float)
    edge_b = np.asarray(edge_b, dtype=float)
    middle = (edge_a + edge_b) * 0.5
    angle = -math.atan2(edge_b[1] - edge_a[1], edge_b[0] - edge_a[0])
    cos, sin = math.cos(angle), math.sin(angle)
    place = np.asarray(centre, dtype=float)

    def transform(point) -> np.ndarray:
        offset = np.asarray(point, dtype=float) - middle
        x = offset[0] * cos - offset[1] * sin
        y = offset[0] * sin + offset[1] * cos
        if mirror:
            y = -y
        return place + np.array([x, y, offset[2]])

    return transform


def _panel_reference(batch, panel, scale: float = 1.0, origin=None,
                     colour=MUTED, radius: float = 0.02) -> None:
    """The mathematical triangle, as a hairline nobody builds to."""
    shift = np.zeros(3) if origin is None else np.asarray(origin, float)
    corners = [np.asarray(corner) * TO_SCENE * scale + shift
               for corner in panel.corners]
    for index in range(3):
        start = corners[index]
        end = corners[(index + 1) % 3]
        steps = 9
        for piece in range(0, steps, 2):
            a = start + (end - start) * (piece / steps)
            b = start + (end - start) * ((piece + 1) / steps)
            batch.cylinder(a, b, radius, colour, 4)


def _shell(batch, reveal: float = 1.0, scale: float = 1.0, origin=None,
           panels=None) -> None:
    """The whole frame: forty independent panels, drawn as wood."""
    chosen = PANELS if panels is None else panels
    shown = int(round(len(chosen) * clamp(reveal)))
    for panel in chosen[:max(1, shown)]:
        _panel_members(batch, panel, 1.0, scale, origin)


def _disc_xz(batch, centre, radius: float, colour, segments: int = 48,
             start_deg: float = 0.0, end_deg: float = 360.0) -> None:
    """A disc standing up in the XZ plane, facing the camera on +Y.

    The renderer culls back faces, so the winding matters as much as the
    normal: wound the other way this draws nothing at all.
    """
    centre = np.asarray(centre, dtype=float)
    normal = np.array([0.0, 1.0, 0.0])
    span = math.radians(end_deg - start_deg)
    count = max(2, int(segments * abs(end_deg - start_deg) / 360.0))
    for index in range(count):
        a = math.radians(start_deg) + span * index / count
        b = math.radians(start_deg) + span * (index + 1) / count
        pa = centre + np.array([radius * math.cos(a), 0.0,
                                radius * math.sin(a)])
        pb = centre + np.array([radius * math.cos(b), 0.0,
                                radius * math.sin(b)])
        if float(np.dot(np.cross(pa - centre, pb - centre), normal)) < 0.0:
            pa, pb = pb, pa
        batch.triangle(centre, pa, pb, colour, normal)


# ======================================================================
# The argument
# ======================================================================

def scene_wg_open(app, opaque, transparent, p: float) -> None:
    """Two trees, and the shell they become."""
    _shell(opaque, clamp(0.1 + p * 1.6), scale=0.92)
    for index, x in enumerate((10.5, -10.5)):
        grow = ease_in_out(clamp(p * 1.8 - index * 0.15))
        if grow <= 0.05:
            continue
        base = np.array([x, 3.5, 0.0])
        draw_timber(opaque, base, base + np.array([0.0, 0.0, 6.8 * grow]),
                    0.52, 4100 + index, CHAINSAW, sides=10, tint=BARK)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.6]),
           f"{PLAN.members_needed} MEMBERS  ·  {len(PANELS)} PANELS  ·  "
           f"{PLAN.diameter_ft:.0f} FT ACROSS", WHITE)
    if p > 0.45:
        _label(app, np.array([10.5, 3.5, 7.6]),
               f"{LOG.usable_length_ft:.0f} ft of usable trunk", AMBER)
    if p > 0.65:
        _label(app, np.array([0.0, 0.0, -1.1]),
               f"two trees  ->  {PLAN.members_available} struts  ->  "
               f"{PLAN.floor_sqft:.0f} sq ft of floor", GREEN)


def scene_wg_mill(app, opaque, transparent, p: float) -> None:
    """Squaring the log: the cant, the boards, and the slabs."""
    centre = np.array([0.0, 0.0, 3.4])
    radius = 2.6
    length = 9.0
    square = ease_in_out(clamp(p * 1.7))
    # The round log, as it arrives.
    opaque.cylinder(centre - np.array([length * 0.5, 0.0, 0.0]),
                    centre + np.array([length * 0.5, 0.0, 0.0]),
                    radius, _fade(BARK, 1.0 - square * 0.75), 24)
    # Four slabs leaving, one per side.
    for index, (dy, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
        travel = ease_in_out(clamp(p * 2.0 - 0.15 * index)) * 3.4
        if travel <= 0.05:
            continue
        offset = np.array([0.0, dy * 1.0, dz * 1.0]) * (radius * 0.78 + travel)
        opaque.box(centre + offset, np.array([length, 0.55, 0.55]),
                   _fade(BARK, 0.9))
    if square > 0.2:
        # The cant, and the boards sawn out of it.
        rows = 3
        for row in range(rows):
            for column in range(2):
                if (row * 2 + column) / (rows * 2) > (square - 0.2) / 0.8:
                    continue
                opaque.box(
                    centre + np.array([0.0, (column - 0.5) * 1.5,
                                       (row - 1) * 1.05]),
                    np.array([length, 1.35, 0.88]), WOOD)
    _label(app, centre + np.array([0.0, 0.0, radius + 1.6]),
           "SQUARE IT, EDGE IT, TRIM IT", WHITE)
    if p > 0.40:
        _label(app, centre + np.array([0.0, 0.0, -radius - 1.3]),
               f"best case {YIELD.brief_two_by_four_count} true 2x4s from "
               f"this tree; packed honestly, {YIELD.two_by_four_count}",
               AMBER)
    if p > 0.70:
        _label(app, centre + np.array([0.0, 4.6, 0.6]),
               f"{YIELD.solid_bf - YIELD.two_by_four_bf:.0f} board feet "
               "of it is not the thing we came for", RED)


def scene_wg_pack(app, opaque, transparent, p: float) -> None:
    """The real packing, row by row, inside the real circle."""
    row = section_rows(LOG)[0]
    diameter = row.top_diameter_in
    scale = 5.6 / diameter
    centre = np.array([math_shift(app), 0.0, 3.9])
    radius = diameter * 0.5 * scale
    _disc_xz(opaque, centre - np.array([0.0, 0.35, 0.0]), radius,
             _fade(BARK, 0.95))
    rows = two_by_four_packing(diameter)
    placed = 0
    total = max(1, sum(rows))
    for index, count in enumerate(rows):
        z = (-radius + (index + 0.5) * 2.0 * scale)
        for piece in range(count):
            placed += 1
            if placed / total > clamp(p * 1.6):
                continue
            x = (piece - (count - 1) / 2.0) * 4.0 * scale
            opaque.box(centre + np.array([x, -0.05, z]),
                       np.array([4.0 * scale * 0.94, 0.7,
                                 2.0 * scale * 0.9]), WOOD)
    _label(app, centre + np.array([0.0, 0.0, radius + 1.2]),
           f"a {diameter:.1f} IN LOG, PACKED WITH TRUE 2x4s", WHITE)
    if p > 0.55:
        _label(app, centre + np.array([0.0, 0.0, -radius - 1.1]),
               " + ".join(str(value) for value in rows)
               + f" = {row.two_by_four_count} pieces", AMBER)
    if p > 0.75:
        _label(app, centre + np.array([radius + 2.6, 0.0, 0.4]),
               f"{YIELD.two_by_four_recovery * 100:.0f}% of the tree", RED)


def scene_wg_split(app, opaque, transparent, p: float) -> None:
    """Half, quarter, eighth -- and nothing thrown away."""
    centre = np.array([math_shift(app), 0.0, 3.9])
    radius = 2.8
    stage = p * 3.4
    spread = ease_in_out(clamp(p * 1.5)) * 0.55
    if stage < 0.7:
        pieces = 1
    elif stage < 1.5:
        pieces = 2
    elif stage < 2.3:
        pieces = 4
    else:
        pieces = SECTORS_PER_LOG
    for index in range(pieces):
        start = 360.0 * index / pieces
        end = 360.0 * (index + 1) / pieces
        middle = math.radians((start + end) * 0.5)
        push = np.array([math.cos(middle), 0.0, math.sin(middle)]) * spread
        _disc_xz(opaque, centre + push, radius, WOOD, 64, start + 0.6,
                 end - 0.6)
        arc_a = math.radians(start + 0.6)
        arc_b = math.radians(end - 0.6)
        for step in range(6):
            t0 = arc_a + (arc_b - arc_a) * step / 6.0
            t1 = arc_a + (arc_b - arc_a) * (step + 1) / 6.0
            a = centre + push + np.array([radius * math.cos(t0), 0.0,
                                          radius * math.sin(t0)])
            b = centre + push + np.array([radius * math.cos(t1), 0.0,
                                          radius * math.sin(t1)])
            opaque.cylinder(a, b, 0.09, BARK, 5)
    _label(app, centre + np.array([0.0, 0.0, radius + 1.5]),
           f"{pieces} PIECE{'S' if pieces > 1 else ''}", WHITE)
    if p > 0.30:
        _label(app, centre + np.array([-radius - 2.7, 0.0, 0.8]),
               f"kerf: {YIELD.kerf_bf:.0f} bf of the tree", MUTED)
    if p > 0.60:
        _label(app, centre + np.array([radius + 2.7, 0.0, -0.6]),
               f"left in the wedges\n{YIELD.wedge_bf:.0f} bf  "
               f"({YIELD.wedge_recovery * 100:.0f}%)", GREEN)


# ======================================================================
# The member
# ======================================================================

def scene_wg_section(app, opaque, transparent, p: float) -> None:
    """One member, end-on: bark out, pith in, both ends square.

    Drawn down the axis rather than broadside, because the sector shape
    is the whole point and broadside hides it.
    """
    shift = math_shift(app)
    depth = 2.5
    grow = ease_in_out(clamp(0.15 + p * 1.6))
    near = np.array([shift, 3.2, 2.0])
    far = near + np.array([0.0, -9.0 * grow, 0.0])
    _wedge_prism(opaque, near, far, np.array([0.0, 0.0, 1.0]), depth,
                 segments=8)

    # The near end face, outlined: two split faces and one bark face.
    profile = _sector_profile(np.array([0.0, 0.0, 1.0]),
                              np.array([1.0, 0.0, 0.0]), depth, 8)
    for index in range(len(profile) - 1):
        opaque.cylinder(near + profile[index], near + profile[index + 1],
                        0.05, GREEN, 5)
    for offset in (profile[0], profile[-1]):
        opaque.cylinder(near, near + offset, 0.05, AMBER, 5)
    opaque.sphere(near, 0.10, RED, 5, 8)

    if p > 0.22:
        _label(app, near + np.array([0.0, 0.0, -0.75]),
               "the pith line: inward", RED)
    if p > 0.38:
        _label(app, near + np.array([0.0, 0.0, depth + 1.0]),
               "the bark face: outward", GREEN)
    if p > 0.52:
        _label(app, near + np.array([-depth * 1.15, 0.0, depth * 0.5]),
               "split face", AMBER)
        _label(app, near + np.array([depth * 1.15, 0.0, depth * 0.5]),
               "split face", AMBER)
        _label(app, near + np.array([0.0, 1.2, -1.55]),
               f"{SECTOR_ANGLE_DEG:.0f} deg of the log", AMBER)
    if p > 0.66:
        _label(app, near + np.array([-depth * 1.4, -3.0, depth * 1.15]),
               f"{PLAN.member_width_in:.2f} in across the bark  ·  "
               f"{PLAN.member_depth_in:.2f} in deep", WHITE)
    if p > 0.80:
        _label(app, near + np.array([0.0, -8.0, 0.3]),
               f"{PLAN.member_area_in2:.1f} sq in of section  =  "
               f"{PLAN.equivalent_two_by_fours:.2f} x a true 2x4", CYAN)


def scene_wg_orient(app, opaque, transparent, p: float) -> None:
    """Every member the same way round, all over the shell."""
    _shell(opaque, 1.0)
    shown = int(round(len(PANELS) * clamp(p * 1.4)))
    for panel in PANELS[:shown][::7]:
        member = panel.members[0]
        midpoint = (np.asarray(member.tail) + np.asarray(member.head)) \
            * 0.5 * TO_SCENE
        normal = np.asarray(member.normal)
        opaque.arrow(midpoint, midpoint + normal * 1.5, 0.05, GREEN)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.7]),
           "BARK OUT, PITH IN -- ALL 120", GREEN)
    if p > 0.5:
        _label(app, np.array([0.0, 0.0, 0.5]),
               "the densest wood in the tree ends up on the weather side,\n"
               "and the deep dimension of every member faces the load",
               WHITE)


def scene_wg_short(app, opaque, transparent, p: float) -> None:
    """Why six feet is the useful length."""
    shift = math_shift(app)
    long_length = 20.0 * FOOT * 2.2
    short_length = LOG.strut_length_ft * FOOT * 2.2
    grow = ease_in_out(clamp(0.1 + p * 1.7))
    a = np.array([long_length * 0.5 + shift, 2.6, 5.0])
    _wedge_prism(opaque, a, a - np.array([long_length * grow, 0.0, 0.0]),
                 np.array([0.0, 0.0, 1.0]), 0.5,
                 wood=_fade(WOOD, 0.5), bark=_fade(BARK, 0.5))
    _label(app, np.array([shift, 2.6, 6.0]),
           "one 20 ft beam: one defect ruins all of it", RED)
    b = np.array([short_length * 2.5 + shift, -2.2, 2.4])
    for index in range(5):
        if index / 5.0 > clamp(p * 1.6):
            continue
        start = b - np.array([index * (short_length + 0.35), 0.0, 0.0])
        _wedge_prism(opaque, start,
                     start - np.array([short_length, 0.0, 0.0]),
                     np.array([0.0, 0.0, 1.0]), 0.5)
    _label(app, np.array([shift, -2.2, 3.6]),
           f"five {LOG.strut_length_ft:.0f} ft members: a defect costs one",
           GREEN)
    if p > 0.7:
        _label(app, np.array([shift, 0.0, 0.6]),
               "short members are easier to carry, season, sort, replace\n"
               "-- and a small tree can still produce them", WHITE)


# ======================================================================
# The panel
# ======================================================================

def scene_wg_explode(app, opaque, transparent, p: float) -> None:
    """Forty frames, each finished before it is lifted."""
    push = ease_in_out(clamp(p * 1.4)) * 2.6
    for index, panel in enumerate(PANELS):
        origin = np.asarray(panel.normal) * push
        _panel_members(opaque, panel, 1.0, 1.0, origin)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 2.9]),
           f"{len(PANELS)} INDEPENDENT FRAMES", WHITE)
    if p > 0.45:
        _label(app, np.array([0.0, 0.0, 0.6]),
               f"{len(PANELS)} x 3 = {PLAN.members_needed} members, and "
               "not one of them is shared", CYAN)


def scene_wg_pinwheel(app, opaque, transparent, p: float) -> None:
    """One panel, laid flat: three members, all the same way round."""
    panel = PANELS[0]
    scale = 2.9
    centre = np.array([math_shift(app), 0.0, 1.7])
    members, corners = _flat_panel(panel, scale, centre)
    _flat_reference(opaque, corners, (0.42, 0.62, 0.78, 1.0), 0.05)
    _draw_flat_panel(opaque, panel, centre, scale, clamp(0.12 + p * 1.5))

    shown = int(clamp(0.12 + p * 1.5) * 3.0)
    for index, (tail, head, member) in enumerate(members):
        if index >= shown:
            continue
        if index == 0 and p > 0.45:
            _label(app, head + np.array([0.0, 0.0, 1.3]),
                   "HEAD\ncut square against the next member's side",
                   AMBER)
            _label(app, tail + np.array([0.0, 0.0, 1.3]),
                   "TAIL\nruns through the previous member's band", CYAN)
        if index == 1 and p > 0.62:
            direction = normalize(head - tail)
            opaque.arrow(tail + direction * 1.2 + np.array([0.0, 0.0, 1.0]),
                         head - direction * 1.2 + np.array([0.0, 0.0, 1.0]),
                         0.05, GREEN)
    if p > 0.78:
        member = panel.members[0]
        _label(app, centre + np.array([0.0, 0.0, 2.4]),
               f"bearing {member.bearing_length_in:.2f} in  ·  "
               f"both ends square  ·  no mitre anywhere", GREEN)


def scene_wg_corner(app, opaque, transparent, p: float) -> None:
    """The corner nothing is cut to, at eight times the size."""
    panel = PANELS[0]
    scale = 5.0
    members, corners = _flat_panel(panel, scale, np.zeros(3))
    vertex = np.asarray(corners[1])
    place = np.array([math_shift(app), 0.0, 0.45]) - vertex
    members = tuple((tail + place, head + place, member)
                    for tail, head, member in members)
    corners = tuple(np.asarray(corner) + place for corner in corners)

    _flat_reference(opaque, corners, MUTED, 0.05)
    up = np.array([0.0, 0.0, 1.0])
    for tail, head, _member in members:
        _wedge_prism(opaque, tail, head, up, MEMBER_DEPTH * scale,
                     segments=5)

    at = np.asarray(corners[1])
    opaque.sphere(at, 0.22, RED, 6, 10)
    _label(app, at + np.array([0.0, 0.0, 2.1]),
           "the mathematical vertex", RED)
    if p > 0.35:
        gap = min(panel.members[0].head_vertex_gap_in,
                  panel.members[1].tail_vertex_gap_in)
        _label(app, at + np.array([0.0, 1.9, 0.9]),
               f"nearest wood stops {gap:.2f} in short of it", AMBER)
    if p > 0.62:
        _label(app, at + np.array([0.0, -2.6, 1.2]),
               "the two bands simply cross here.\nNothing is notched, "
               "nothing is shaved.", WHITE)


def scene_wg_pair(app, opaque, transparent, p: float) -> None:
    """Two panels either side of one seam, each with its own stick."""
    left = PANELS[0]
    shared = None
    for candidate in PANELS[1:]:
        common = set(left.face) & set(candidate.face)
        if len(common) == 2:
            shared = candidate
            break
    assert shared is not None, "no neighbouring panel found"

    scale = 1.85
    seam = np.array([math_shift(app), 0.0, 1.6])
    # Closed, the two panels are a gasket apart; the chapter opens with
    # them held apart so the duplicated member is visible.
    gap = PLAN.gasket.thickness_in * TO_SCENE * scale
    apart = gap * 0.5 + (1.0 - ease_in_out(clamp(p * 1.6))) * 2.4
    up = np.array([0.0, 0.0, 1.0])
    depth = MEMBER_DEPTH * scale
    common = set(left.face) & set(shared.face)

    for panel, side in ((left, 1.0), (shared, -1.0)):
        members, corners = _flat_panel(panel, scale, np.zeros(3))
        position = next(index for index in range(3)
                        if {panel.face[index],
                            panel.face[(index + 1) % 3]} == common)
        place = seam + np.array([0.0, apart * side, 0.0])
        # Which way a flattened panel's third corner happens to point is
        # an accident of its winding, so mirror only when it would
        # otherwise fold back across the seam onto its neighbour.
        transform = _align_flat(corners[position],
                                corners[(position + 1) % 3], place, False)
        opposite = transform(corners[(position + 2) % 3])
        if (opposite[1] - place[1]) * side < 0.0:
            transform = _align_flat(corners[position],
                                    corners[(position + 1) % 3], place, True)
        _flat_reference(opaque, [transform(corner) for corner in corners],
                        (0.42, 0.62, 0.78, 1.0), 0.045)
        for index, (tail, head, _member) in enumerate(members):
            start, end = transform(tail), transform(head)
            colour = AMBER if index == position else WOOD
            _wedge_prism(opaque, start, end, up, depth,
                         wood=colour, segments=5)

    if p > 0.55:
        first, second = sorted(common)
        length = float(np.linalg.norm(
            GEOMETRY.vertices[first] - GEOMETRY.vertices[second]
        )) * PLAN.radius_in * TO_SCENE * scale
        opaque.box(seam + np.array([0.0, 0.0, depth * 0.55]),
                   np.array([length * 0.82, max(gap, 0.12), depth * 0.5]),
                   RED)
        _label(app, seam + np.array([0.0, 0.0, depth + 1.5]),
               f"one gasket, {PLAN.gasket.thickness_in:.2f} in", RED)
    _label(app, seam + np.array([0.0, 4.2, 0.9]),
           "each panel brings its own stick to the seam", AMBER)
    if p > 0.75:
        _label(app, seam + np.array([0.0, -4.2, 0.9]),
               f"{SUMMARY.doubled_edges} shared edges x 2 + "
               f"{SUMMARY.rim_edges} at the rim = "
               f"{SUMMARY.strut_check} members", CYAN)


def scene_wg_gasket(app, opaque, transparent, p: float) -> None:
    """A section through one seam, at the angle it really opens to."""
    shift = math_shift(app)
    dihedral = PLAN.gasket.min_dihedral_deg + (
        PLAN.gasket.max_dihedral_deg - PLAN.gasket.min_dihedral_deg
    ) * clamp(p * 1.3)
    half = math.radians(180.0 - dihedral) * 0.5
    gap = PLAN.gasket.thickness_in * TO_SCENE * 9.0
    depth = 1.7
    length = 7.0
    seam = np.array([shift, 0.0, 2.4])
    edge = math.sin(math.radians(SECTOR_ANGLE_DEG) * 0.5) * depth
    for sign in (-1.0, 1.0):
        # Each panel tilts half the exterior angle away from its
        # neighbour; its member's bark face lies on that panel, and the
        # bark corner nearest the seam stops half a gasket short of it.
        out = np.array([math.sin(half) * sign, 0.0, math.cos(half)])
        side = np.array([math.cos(half) * sign, 0.0, -math.sin(half)])
        pith = seam + side * (gap * 0.5 + edge) - out * depth
        _wedge_prism(opaque, pith - np.array([0.0, length * 0.5, 0.0]),
                     pith + np.array([0.0, length * 0.5, 0.0]),
                     out, depth, segments=6)
    hose = seam + np.array([0.0, 0.0, gap * 0.35])
    opaque.cylinder(hose - np.array([0.0, length * 0.5, 0.0]),
                    hose + np.array([0.0, length * 0.5, 0.0]),
                    gap * 0.62, RED, 12)
    _label(app, hose + np.array([0.0, -length * 0.5, 1.4]),
           f"spline / key / hose gasket\n{PLAN.gasket.thickness_in:.2f} in",
           RED)
    _label(app, np.array([shift, 0.0, 0.6]),
           f"dihedral here: {dihedral:.2f} deg", WHITE)
    if p > 0.55:
        _label(app, np.array([shift, 0.0, -0.7]),
               f"across the shell it runs "
               f"{PLAN.gasket.min_dihedral_deg:.1f} to "
               f"{PLAN.gasket.max_dihedral_deg:.1f} deg -- the gasket "
               "takes that up,\nso no seam needs its own bevel", AMBER)


# ======================================================================
# The build
# ======================================================================

def scene_wg_scale(app, opaque, transparent, p: float) -> None:
    """The dome the two trees make, with somebody standing in it."""
    _shell(opaque, 1.0)
    if p > 0.2:
        # A six-foot rule, one foot a band, stood inside the shell.
        base = np.array([3.1, -2.6, 0.0])
        for foot in range(6):
            colour = WHITE if foot % 2 else CYAN
            opaque.cylinder(base + np.array([0.0, 0.0, foot * FOOT]),
                            base + np.array([0.0, 0.0, (foot + 1) * FOOT]),
                            0.075, colour, 8)
        _label(app, base + np.array([0.0, 0.0, 6.0 * FOOT + 0.5]),
               "6 ft", CYAN)
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.5]),
           f"{PLAN.diameter_ft:.1f} FT ACROSS  ·  "
           f"{PLAN.height_ft:.1f} FT TALL", WHITE)
    if p > 0.45:
        _label(app, np.array([0.0, 0.0, -0.9]),
               f"{PLAN.floor_sqft:.0f} sq ft of floor", GREEN)
    if p > 0.68:
        _label(app, np.array([0.0, 0.0, -2.0]),
               f"{PLAN.members_needed} members used  ·  "
               f"{PLAN.spare_members} spare", AMBER)


def scene_wg_assemble(app, opaque, transparent, p: float) -> None:
    """Forty panels going up, one at a time."""
    landed = clamp(p * 1.25)
    for index, panel in enumerate(PANELS):
        share = index / len(PANELS)
        if share > landed:
            continue
        drop = clamp((landed - share) * 6.0)
        lift = (1.0 - ease_in_out(drop)) * 4.5
        origin = np.asarray(panel.normal) * lift
        _panel_members(opaque, panel, 1.0, 1.0, origin)
    placed = int(landed * len(PANELS))
    _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.8]),
           f"PANEL {min(placed + 1, len(PANELS))} OF {len(PANELS)}", WHITE)
    if p > 0.55:
        _label(app, np.array([0.0, 0.0, 0.5]),
               "each frame is finished on the ground and lifted whole",
               CYAN)


_MILL_CHAIN = ("tree", "log", "cant", "board", "edged", "dried",
               "dimensional", "strut")
_SPLIT_CHAIN = ("tree", "log", "wedge", "strut")


def scene_wg_chain(app, opaque, transparent, p: float) -> None:
    """Two roads from a standing tree to a member."""
    shift = math_shift(app)
    for row, (chain, colour, z) in enumerate((
            (_MILL_CHAIN, MUTED, 5.0), (_SPLIT_CHAIN, GREEN, 1.9))):
        spacing = 18.0 / max(len(chain), 1)
        for index, name in enumerate(chain):
            if index / len(chain) > clamp(p * 1.5 - row * 0.25):
                continue
            x = (len(chain) / 2.0 - index - 0.5) * spacing + shift - 1.2
            opaque.box(np.array([x, 0.0, z]), np.array([1.5, 0.9, 0.9]),
                       _fade(colour, 0.85))
            _label(app, np.array([x, 0.0, z + 1.15]), name, colour)
            if index < len(chain) - 1:
                opaque.arrow(np.array([x - 0.95, 0.0, z]),
                             np.array([x - spacing + 0.95, 0.0, z]),
                             0.04, colour)
    if p > 0.5:
        _label(app, np.array([shift - 11.6, 0.0, 5.0]),
               f"{len(_MILL_CHAIN)} stages", MUTED)
        _label(app, np.array([shift - 11.6, 0.0, 1.9]),
               f"{len(_SPLIT_CHAIN)} stages", GREEN)
    if p > 0.72:
        _label(app, np.array([shift - 1.2, 0.0, 0.2]),
               "every stage removed is equipment, fuel, handling and "
               "waste that is no longer needed", WHITE)


def scene_wg_close(app, opaque, transparent, p: float) -> None:
    """The finished shell, and what it cost in trees."""
    _shell(opaque, 1.0)
    if p > 0.25:
        _label(app, np.array([0.0, 0.0, SCENE_RADIUS + 1.6]),
               f"{PLAN.trees} TREES  ->  {PLAN.members_needed} MEMBERS  ->  "
               f"{PLAN.floor_sqft:.0f} SQ FT", WHITE)
    if p > 0.45:
        _label(app, np.array([0.0, 0.0, 1.0]),
               f"{YIELD.wedge_recovery * 100:.0f}% of each tree kept  ·  "
               f"x{YIELD.gain_over_brief:.2f} the wood of milling", GREEN)
    if p > 0.68:
        _label(app, np.array([0.0, 0.0, -0.4]),
               "the round tree is not defective lumber,\n"
               "and the wedge is not an unfinished 2x4", AMBER)


SCENES = {
    "wg_open": scene_wg_open,
    "wg_mill": scene_wg_mill,
    "wg_pack": scene_wg_pack,
    "wg_split": scene_wg_split,
    "wg_section": scene_wg_section,
    "wg_orient": scene_wg_orient,
    "wg_short": scene_wg_short,
    "wg_explode": scene_wg_explode,
    "wg_pinwheel": scene_wg_pinwheel,
    "wg_corner": scene_wg_corner,
    "wg_pair": scene_wg_pair,
    "wg_gasket": scene_wg_gasket,
    "wg_scale": scene_wg_scale,
    "wg_assemble": scene_wg_assemble,
    "wg_chain": scene_wg_chain,
    "wg_close": scene_wg_close,
}

BUILTIN_STAGES = {"rigidity"}


# ======================================================================
# The chapters
# ======================================================================

def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps,
                   duration, camera, stage, "math")


_AUTHORED: tuple[Chapter, ...] = (
    Chapter(
        "open", "00", "Eight cuts to a house",
        "What if the tree got a vote in the design?",
        (
            "Modern lumber starts with a strange compromise. Trees grow round,",
            "tapered and irregular. We spend enormous effort turning them into",
            "perfectly rectangular sticks, and we throw away everything that",
            "does not fit the rectangle.",
            "For a hardware store that makes sense. Standard sizes stack on a",
            "pallet.",
            "But a dome lets us ask a different question. What if the building",
            "were designed around the tree, instead of the tree being forced to",
            "conform to the building?",
            "This is that experiment. Two pines, split lengthwise into eighths,",
            "crosscut once, and assembled into a geodesic shell — with almost",
            "nothing in between.",
        ),
        ("split half, quarter, eighth",
         f"{PLAN.members_available} members from two trees"),
        26.0, (32.0, 20.0, 20.0), "wg_open",
    ),
    Chapter(
        "square", "00", "Squaring the circle",
        "Watch what hits the floor before anything gets used.",
        (
            "Here is what conventional milling does to a log.",
            "First it squares it: four slabs come off the outside to make a",
            "rectangular cant. Then the cant is sawn into boards. Then each",
            "board is edged, and trimmed, and dried, and graded.",
            "Every one of those steps removes wood, and every one of them costs",
            "a machine, a setup and a handling.",
            "What survives is beautifully standard. But look at what is on the",
            "floor: the curved outside of the tree, which is also the densest,",
            "strongest wood the tree grew.",
        ),
        ("cant, boards, edging, trimming",
         "the outside of the tree becomes chips"),
        24.0, (88.0, 20.0, 17.0), "wg_mill",
    ),
    Chapter(
        "trunk", "00", "What is standing there",
        "How much wood is actually standing out there?",
        (
            "Start with the tree we are actually working with. Sixty feet of",
            "usable trunk, fifteen inches across at the bottom, five and a half",
            "at the top.",
            "A trunk is a cone with its tip cut off, and there is a formula for",
            "that shape which we will run in a moment. It gives us the amount of",
            "solid wood standing there before any method touches it.",
            "That number is the fixed budget. Every approach in this film starts",
            "from exactly the same amount of wood, so any difference between",
            "them is a difference in what we keep.",
        ),
        ("V = pi L (r1^2 + r1 r2 + r2^2) / 3",
         "one board foot = 144 cubic inches"),
        24.0, (88.0, 20.0, 17.0), "wg_mill",
    ),
    _math(
        "m_trunk", "The tree, in board feet",
        "The fixed budget every method starts from.",
        (
            "The frustum formula, run on our pine. R one and r two are the",
            "radii at the two ends, L is the length between them.",
            "Board feet are the trade's unit: one board foot is a piece one foot",
            "square and one inch thick, which is a hundred and forty-four cubic",
            "inches. Divide the cubic inches by a hundred and forty-four and the",
            "answer comes out in the units a sawyer thinks in.",
            "Four hundred and forty-two board feet, standing in one tree. Bucked",
            "into five twelve-foot lengths, the bottom section alone holds more",
            "than the top three together — which is the taper doing what taper",
            "does.",
        ),
        steps_trunk(), 48.0, (88.0, 20.0, 22.0), "wg_mill",
    ),
    Chapter(
        "pack", "00", "How many rectangles fit in a circle?",
        "Rectangles, and the circle they have to fit inside.",
        (
            "So how many true two-by-fours does that tree actually contain?",
            "A mill saws parallel rows across the log. A row can only be as wide",
            "as its narrowest point, because a stick has to be full width along",
            "its whole length. And the log is sized on its small end, because the",
            "taper means the small end is the honest one.",
            "Pack the rows and count them. This is that count, done on our",
            "sections rather than assumed.",
        ),
        ("rows are limited by the narrowest chord",
         "a log is sized on its small end"),
        24.0, (90.0, 18.0, 16.0), "wg_pack",
    ),
    _math(
        "m_rectangles", "Packing the circle, honestly",
        "Where this film disagrees with its own brief.",
        (
            "Here is the packing, section by section, with the rows written out.",
            "Twenty-five true two-by-fours per tree, which is two hundred board",
            "feet, which is forty-five per cent of the standing tree.",
            "Now, the brief this lesson is built from estimates thirty-two",
            "pieces. That is a more generous figure than this packing produces.",
            "We are not going to quietly use whichever number flatters the",
            "argument, so both are carried forward and the comparison is made",
            "twice.",
            "Either way, more than half of the tree does not become the thing we",
            "came for.",
        ),
        steps_rectangles(), 56.0, (90.0, 18.0, 21.0), "wg_pack",
    ),
    Chapter(
        "split", "00", "Stop squaring. Start splitting.",
        "The same log, opened a different way.",
        (
            "Now the other approach.",
            "A round tree divides naturally. Split it through the centre and both",
            "halves are still whole. Split each half again for quarters. Split",
            "each quarter again for eighths.",
            "Eight radial sectors. Nothing has been squared, nothing edged,",
            "nothing trimmed. The curved outside of the tree is still there — it",
            "is simply part of the member now.",
            "The only wood lost is the wood the blade turned into sawdust.",
        ),
        (f"{SECTORS_PER_LOG} sectors of "
         f"{SECTOR_ANGLE_DEG:.0f} degrees each",
         "only the kerf is lost"),
        26.0, (90.0, 18.0, 16.0), "wg_split",
    ),
    _math(
        "m_radial", "What the saw costs",
        "Where the sawdust actually goes.",
        (
            "The kerf is worth doing properly, because it is the only loss in",
            "this method.",
            "One cut halves the log: that is a full diameter of kerf. A second",
            "makes the quarters: another full diameter. Then four cuts run from",
            "the pith to the bark to make the eighths, and four radius-length",
            "cuts add up to two more diameters.",
            "Four diameters of kerf per section, times the length, times a",
            "quarter-inch chainsaw blade. Fifty-one board feet from the whole",
            "tree.",
            "Three hundred and ninety-one board feet remain in the wedges. That",
            "is eighty-eight per cent of the tree, still in structural members.",
        ),
        steps_radial(), 52.0, (90.0, 18.0, 21.0), "wg_split",
    ),
    _math(
        "m_compare", "The same two trees, both ways",
        "Both estimates, both ratios, nothing cherry-picked.",
        (
            "Two trees, converted both ways.",
            "Against the honest packing, the radial method keeps very nearly",
            "twice the wood. Against the brief's kinder estimate for the mill, it",
            "keeps about fifty-three per cent more — and that is the figure the",
            "brief quotes, so we quote it too.",
            "The member count moves the same way. A hundred and sixty six-foot",
            "wedges against a hundred and twenty-eight sawn ones: thirty-two more",
            "sticks, from trees we already felled.",
            "Whichever estimate you prefer for the sawmill, the direction of the",
            "answer does not change.",
        ),
        steps_compare(), 52.0, (90.0, 18.0, 21.0), "wg_split",
    ),
    Chapter(
        "member", "00", "The wedge is the member",
        "Not a stick with a defect. A different section.",
        (
            "Here is one member, as it comes off the saw.",
            "Two flat faces where the splits went through. One curved face that",
            "used to be the outside of the tree. A sharp edge along the middle",
            "where the pith was.",
            "It goes into the dome one way round, always: the curved bark face",
            "outward, to the weather, and the pith line inward, to the room. That",
            "puts the tree's densest wood on the outside of the shell and points",
            "the member's deep dimension straight through the load.",
            "It is not an unfinished two-by-four. It is a different section, and",
            "for this job a better one.",
        ),
        ("two flat faces, one bark face",
         "bark out, pith in, every time"),
        26.0, (90.0, 16.0, 14.0), "wg_section",
    ),
    _math(
        "m_sector", "One eighth of a log, measured",
        "The diameter where an eighth of a log wins.",
        (
            "The arithmetic of a sector is simple. Its area is pi r squared over",
            "eight. Its width across the bark face is two r sine of twenty-two",
            "and a half degrees. Its depth, pith to bark, is just the radius.",
            "At our design diameter that is a section nearly twice the area of a",
            "true two-by-four — and much deeper, which matters more than area",
            "because bending stiffness grows with the cube of depth.",
            "And there is a break-even diameter. Set the sector area equal to",
            "eight square inches and solve: about nine inches. Above roughly nine",
            "inches of trunk, every eighth of the log already holds more wood",
            "than a two-by-four, before any milling at all.",
        ),
        steps_sector(), 52.0, (90.0, 16.0, 18.0), "wg_section",
    ),
    Chapter(
        "orient", "00", "All one hundred and twenty, the same way round",
        "The stack has no left-handed piece in it.",
        (
            "Across the whole shell there is exactly one orientation rule: bark",
            "outward, pith inward.",
            "That single convention does a lot of work. It puts the dense outer",
            "growth on the weather side. It gives every panel a consistent",
            "outside face to seal against. And it means a stack of wedges can be",
            "picked up in any order — there is no left-handed member and no",
            "right-handed one.",
        ),
        ("one rule: bark out",),
        20.0, (34.0, 22.0, 16.0), "wg_orient",
    ),
    Chapter(
        "short", "00", "Short members are the point",
        "Short sticks, on purpose.",
        (
            "There is a reason the members are six feet long.",
            "Getting one perfectly straight twenty-foot beam out of a real tree",
            "is difficult, and one knot cluster in the wrong place ruins the",
            "whole thing.",
            "Getting six-foot members is easy. A defect costs you one stick",
            "instead of a beam. Short members are easier to carry, to season, to",
            "sort, to store and to replace. And a modest tree can produce them —",
            "we are not waiting a century for old growth.",
            "The geodesic frame turns that into an advantage, because it is built",
            "from many short members by design.",
        ),
        (f"{LOG.section_length_ft:.0f} ft section, cut once = "
         f"two {LOG.strut_length_ft:.0f} ft members",),
        24.0, (88.0, 20.0, 18.0), "wg_short",
    ),
    Chapter(
        "triangles", "00", "Why the network carries the load",
        "Where the strength actually lives.",
        (
            "This only works because of what a dome is.",
            "Push the top of a square frame and it leans: the corners turn and",
            "the sides keep their length. Push a triangle and nothing moves",
            "unless a side gets longer or shorter, which timber is very unwilling",
            "to do.",
            "A geodesic shell repeats that across a curved surface, so the",
            "strength lives in the network rather than in any one member. No",
            "single stick is asked to solve the whole problem.",
            "That is what lets an odd-shaped member do the job. The structure",
            "cares about section, grain, unsupported length and the load path. It",
            "does not care whether the corner of an imaginary rectangle exists.",
        ),
        ("the network carries the load",),
        24.0, (34.0, 24.0, 15.0), "rigidity",
    ),
    Chapter(
        "panels", "00", "Forty independent frames",
        "What actually gets lifted into place.",
        (
            "Now the part that makes this buildable.",
            "The shell is not assembled stick by stick in the air. It is forty",
            "separate triangular frames, each one finished on the ground and",
            "lifted into place whole.",
            "Three members each, and none of them shared with a neighbour. Forty",
            "times three is a hundred and twenty members, which is exactly what",
            "the two trees gave us with sticks to spare.",
        ),
        (f"{len(PANELS)} panels x 3 = {PLAN.members_needed} members",),
        22.0, (32.0, 22.0, 19.0), "wg_explode",
    ),
    Chapter(
        "pinwheel", "00", "The pinwheel joint",
        "The hardest operation in dome building, deleted.",
        (
            "Inside one triangle, the three members are arranged as a pinwheel,",
            "and all three the same way round.",
            "Each member lies with its bark face on its own edge line. One end —",
            "call it the head — is cut square and butts against the side of the",
            "next member. The other end, the tail, runs on through the previous",
            "member's band so that member's head has a full face to bear on.",
            "Follow it around and every member does the same two things: it",
            "terminates into the next one, and it receives the previous one.",
            "Nothing is mitred. Nothing is coped. Nothing is shaved. Every end in",
            "the whole building is a square crosscut.",
        ),
        ("head: cut square against the next member's side",
         "tail: runs through the previous member's band"),
        28.0, (90.0, 46.0, 13.5), "wg_pinwheel",
    ),
    _math(
        "m_pinwheel", "The pinwheel, measured",
        "What the joint costs, and what it buys.",
        (
            "Here is the same joint in numbers.",
            "Each member's centre sits half its own width inside its edge line,",
            "because the bark face is on that line. The head is cut where the",
            "next member's near face crosses. The tail runs to where the previous",
            "member's far face crosses — and the distance between those two",
            "crossings is the bearing: the length of face the joint actually",
            "presses on.",
            "The price is a little length. Laying all three bark faces on their",
            "own edges puts the members inside the triangle, so each stick is",
            "shorter than the edge it stands on.",
            "That is the trade: a few inches of stick, in exchange for the single",
            "hardest operation in dome building disappearing completely.",
        ),
        steps_pinwheel(), 56.0, (90.0, 46.0, 19.0), "wg_pinwheel",
    ),
    Chapter(
        "corner", "00", "The corner nothing touches",
        "The one place the wood and the drawing part company.",
        (
            "Look closely at a corner.",
            "The two members meeting there do not meet at all. One passes",
            "through, the other stops against its side, and the point where the",
            "geometry says the triangle has a corner sits in the gap between",
            "them.",
            "That is worth saying plainly, because it is the opposite of how",
            "domes are usually built. The vertices are references. They set out",
            "the geometry, they decide the member lengths, and no stick is ever",
            "cut to reach one.",
            "It also means a small error at a corner does not fight the wood. The",
            "joint has somewhere to go.",
        ),
        ("vertices are references, not endpoints",),
        24.0, (90.0, 40.0, 12.5), "wg_corner",
    ),
    _math(
        "m_lengths", "Two edges, four sticks",
        "Four saw-stop settings for a whole house.",
        (
            "A 2V hemisphere has two edge lengths, the short and the long.",
            "The pinwheel turns those two into four stick lengths, because where",
            "an end stops depends on the corner it stops in, and the corners are",
            "not all the same.",
            "Four lengths, thirty of each, every end square. That is the complete",
            "cut list for the frame of a house: four saw-stop settings and a",
            "hundred and twenty crosscuts.",
        ),
        steps_lengths(), 46.0, (90.0, 46.0, 19.0), "wg_pinwheel",
    ),
    Chapter(
        "duplicate", "00", "Neighbours do not share",
        "What the extra fifty-five sticks buy.",
        (
            "Between two panels, something deliberately wasteful happens.",
            "Each panel carries its own member along the shared edge. The two",
            "sticks lie face to face, and neither one has been cut to suit the",
            "other.",
            "That is why the frame needs a hundred and twenty members where a",
            "hubbed dome needs sixty-five. Fifty-five shared edges carry two",
            "sticks each, and the ten edges around the rim carry one.",
            "What we buy with those extra sticks is independence. Every panel is",
            "identical to build, can be built out of order, and can be replaced",
            "without touching its neighbours.",
        ),
        (f"{SUMMARY.doubled_edges} x 2 + {SUMMARY.rim_edges} = "
         f"{SUMMARY.strut_check} members",),
        26.0, (90.0, 42.0, 17.0), "wg_pair",
    ),
    Chapter(
        "gasket", "00", "The gasket does the shaving",
        "The part of the joint that is not made of wood.",
        (
            "So what closes the seam?",
            "Not the wood. A separate spline, key or rubber hose sits between the",
            "two members, and the panels are set out half a gasket thickness",
            "inside their true edges so the pair plus the gasket comes back to",
            "the exact geometry.",
            "Here is why that matters. The angle between two panels is not one",
            "number — it changes from seam to seam across the shell. If the wood",
            "had to close that angle, every seam would need its own bevel.",
            "A compressible gasket takes up the whole range instead. It also",
            "drains, it takes up seasonal movement, and it can be replaced",
            "without dismantling anything.",
        ),
        (f"gasket {PLAN.gasket.thickness_in:.2f} in thick",
         "panels set out half a gasket inside their edges"),
        28.0, (90.0, 14.0, 9.5), "wg_gasket",
    ),
    _math(
        "m_seams", "Every seam in the shell",
        "Fifty-five joints, and how much they disagree.",
        (
            "The seams, counted off the same model.",
            "Fifty-five interior seams with two members each, ten rim seams with",
            "one. That is the hundred and twenty again, from the other direction.",
            "The dihedral — the angle between neighbouring panels — runs from a",
            "hundred and fifty-seven and a half degrees to nearly a hundred and",
            "sixty-two. Four and a half degrees of variation.",
            "That is the number the gasket exists to absorb. Cut it into the",
            "timber instead and you have fifty-five different bevel setups.",
        ),
        steps_seams(), 48.0, (90.0, 14.0, 13.0), "wg_gasket",
    ),
    Chapter(
        "sizing", "00", "The tree sizes the building",
        "Which comes first, the building or the timber?",
        (
            "In a normal design you choose the dome, then order the timber.",
            "Here it runs the other way. The tree is bucked into twelve-foot",
            "sections because that is what handles well, each section is crosscut",
            "once, and that fixes the member at six feet.",
            "Six feet of member, arranged as a pinwheel, gives exactly one dome",
            "radius. So the building's size is a result of the tree rather than a",
            "choice made in advance.",
        ),
        ("member length in, dome radius out",),
        22.0, (32.0, 22.0, 17.0), "wg_scale",
    ),
    _math(
        "m_dome", "The dome two trees make",
        "A size nobody chose.",
        (
            "Solve the pinwheel backwards for the radius that makes the longest",
            "member exactly six feet, and the building falls out.",
            "Twenty-two feet across. Eleven feet at the crown. Three hundred and",
            "eighty square feet of floor — a serious room, from two trees.",
            "And the stock adds up. A hundred and sixty members available, a",
            "hundred and twenty in the frame, forty left over for the floor",
            "system, blocking, bracing and the fit-out.",
        ),
        steps_dome(), 48.0, (32.0, 22.0, 22.0), "wg_scale",
    ),
    Chapter(
        "assemble", "00", "Forty frames, lifted whole",
        "Where the precise work gets done.",
        (
            "Assembly follows from the panels.",
            "Each triangle is built flat on the ground, where a square end and a",
            "screw are easy. Then it is lifted into place and gasketed to its",
            "neighbours.",
            "Nobody is up a ladder holding three sticks at an angle. The work that",
            "needs precision happens at waist height, and the work that happens in",
            "the air is bolting finished frames together.",
        ),
        (f"{len(PANELS)} frames, built flat, lifted whole",),
        22.0, (34.0, 24.0, 18.0), "wg_assemble",
    ),
    Chapter(
        "actions", "00", "Least actions, maximum building",
        "Every operation somebody has to pay for.",
        (
            "The real measure of a system like this is not money. It is actions",
            "per unit of finished building.",
            "Measuring, marking, repositioning, clamping, cutting, milling,",
            "edging, planing, sorting, stacking, loading, hauling, and handling",
            "the waste — every one of those has a cost, and standard lumber is",
            "only convenient because somebody else already paid it.",
            "When the tree is standing next to the site, the question changes:",
            "what is the shortest honest path from that tree to a finished",
            "member?",
        ),
        ("actions per unit of finished building",),
        24.0, (90.0, 17.0, 26.0), "wg_chain",
    ),
    _math(
        "m_actions", "Counting the cuts",
        "One tree to a finished member, counted both ways.",
        (
            "Count the cuts. Splitting: two rip cuts to quarter each section,",
            "four more to make the eighths, then one crosscut per wedge.",
            "Milling: rips to open the cant, a cut between every pair of rows,",
            "two edging passes per board, and a crosscut each.",
            "Per member the difference is stark — and this only counts cuts. It",
            "does not count the setting out, the handling between machines, the",
            "sorting, the stacking or the hauling.",
            "The shorter chain is also the one that keeps more of the tree. Those",
            "two things usually pull against each other. Here they do not.",
        ),
        steps_actions(), 52.0, (90.0, 17.0, 30.0), "wg_chain",
    ),
    Chapter(
        "honest", "00", "What this does not claim",
        "The part of this that is not proven.",
        (
            "One honest paragraph, because the argument does not need overstating.",
            "This is not the claim that any eighth of any tree equals a graded",
            "two-by-four. It does not. Species, moisture content, knots, checks,",
            "decay, grain deviation, taper, and the connection details all still",
            "matter, and a habitable structure has to be designed and verified",
            "around the members actually being used.",
            "The figures in this film are geometry and volume — what the tree",
            "contains and what the frame needs. They are not a structural",
            "calculation and they are not a substitute for one.",
            "But that requirement does not weaken the material argument. It is",
            "the reason for it. Once we stop assuming structural wood must mean",
            "rectangular store-bought lumber, we can engineer around the material",
            "we actually have.",
        ),
        ("geometry and volume, not a structural calculation",),
        28.0, (34.0, 22.0, 16.0), "wg_orient",
    ),
    Chapter(
        "close", "00", "The round tree is not defective lumber",
        "Two trees, and a different question.",
        (
            "That is the whole idea.",
            "Two trees. Split eight ways. Crosscut once. Forty pinwheel frames",
            "with every end square, gasketed to each other rather than shaved to",
            "fit. A twenty-two foot shell with three hundred and eighty square",
            "feet of floor, and forty sticks left over.",
            "Efficiency is not always a better machine for making conventional",
            "materials. Sometimes it is a structure that no longer requires the",
            "conventional material at all.",
            "The round tree is not defective lumber. The wedge is not an",
            "unfinished two-by-four. It is the structural member — and the dome",
            "is the geometry that lets us use it.",
        ),
        (f"{PLAN.trees} trees -> {PLAN.members_needed} members -> "
         f"{PLAN.floor_sqft:.0f} sq ft",),
        28.0, (30.0, 26.0, 17.0), "wg_close",
    ),
)


CHAPTERS: tuple[Chapter, ...] = tuple(
    replace(chapter, number=f"{index + 1:02d}",
            narration=prose(chapter.narration))
    for index, chapter in enumerate(_AUTHORED)
)


def validate_wedge_lesson() -> None:
    """Prove the lesson before a frame of it renders."""
    validate_wedge_facts()

    lesson = WEDGE_LESSON
    lesson.validate()

    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug in the lesson"
    for chapter in lesson.chapters:
        assert chapter.narration, chapter.slug
        assert (chapter.stage in SCENES
                or chapter.stage in BUILTIN_STAGES), (chapter.slug,
                                                      chapter.stage)
        if chapter.overlay == "math":
            assert len(chapter.equations) >= 5, chapter.slug
            assert len(chapter.equations[-1]) >= 30, chapter.slug

    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    offered = {builder() for _name, builder in ALL_SCREENS}
    assert used == offered, (
        f"{len(offered - used)} unused screens, "
        f"{len(used - offered)} unknown screens")

    # The argument has to arrive in order: the tree before the member,
    # the member before the panel, the panel before the shell.
    order = {slug: index for index, slug in enumerate(slugs)}
    assert order["square"] < order["pack"] < order["split"]
    assert order["split"] < order["member"] < order["panels"]
    assert order["panels"] < order["pinwheel"] < order["corner"]
    assert order["corner"] < order["duplicate"] < order["gasket"]
    assert order["gasket"] < order["sizing"] < order["close"]
    assert order["honest"] < order["close"]

    # The voice reads a chapter's headline, pauses, then reads the body.
    # A headline that summarises its own opening lines is therefore
    # heard twice in a row, which is what a doubled voice sounds like
    # even when the audio is clean.  Measured rather than eyeballed,
    # because it went unnoticed through a whole render once.
    common = {
        "this", "that", "with", "from", "they", "them", "then", "than",
        "what", "when", "which", "there", "their", "have", "been", "into",
        "over", "only", "just", "some", "more", "most", "will", "would",
        "could", "should", "about", "because", "does", "here", "does",
        "every", "much", "many", "make", "makes", "your", "yours",
    }

    def _content_words(text: str) -> set:
        words = {word.strip(".,:;!?-—\"'").lower() for word in text.split()}
        return {word for word in words if len(word) > 3 and word not in common}

    for chapter in lesson.chapters:
        opening = " ".join(" ".join(chapter.narration).split(". ")[:2])
        headline = _content_words(chapter.promise)
        if not headline:
            continue
        shared = headline & _content_words(opening)
        overlap = len(shared) / len(headline)
        assert overlap < 0.5, (
            f"chapter {chapter.number} headline repeats its own opening: "
            f"{sorted(shared)}")

    class _App:
        def __init__(self):
            self.world_labels = []

    for stage, painter in SCENES.items():
        for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            assert opaque.vertices or transparent.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    # A wedge prism must be a closed solid with its bark facing the way
    # it was asked to: the whole orientation rule depends on it.
    batch = TriangleBatch()
    _wedge_prism(batch, np.array([0.0, 0.0, 0.0]), np.array([2.0, 0.0, 0.0]),
                 np.array([0.0, 0.0, 1.0]), 0.5)
    assert len(batch.vertices) % 30 == 0 and batch.vertices
    points = np.asarray(batch.vertices).reshape(-1, 10)[:, :3]
    assert points[:, 2].max() > 0.4, "the bark face is not on the +Z side"
    assert abs(points[:, 2].min()) < 1e-6, "the pith line is not at zero"

    # The shell the painters draw is the frame the facts count.
    assert len(PANELS) == 40
    assert sum(len(panel.members) for panel in PANELS) == SUMMARY.struts
    assert len(CLASSES) == 4, CLASSES


WEDGE_LESSON = Lesson(
    key="wedge",
    brand="EIGHT CUTS TO A HOUSE",
    title="Eight Cuts to a House: A Dome Straight From the Tree",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_wedge_lesson,
    report=wedge_facts_report,
    snapshot_prefix="wedge",
    label_layout="declutter",
)
