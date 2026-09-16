"""The dome house lookbook: the cast, the wardrobe, and the composer.

The rest of this package proves domes.  This one furnishes one, puts
eight women in it, and shows the machinery underneath: a body lofted
from one silhouette, hair built as strands rather than painted on, a
wardrobe that is a list of pieces instead of a pile of special cases,
and an editor that refuses a piece because the shell is in the way.

It is a lesson, so it plays through the same renderer, exporter,
narration and companion files as every other lesson in the package.
Its selftest is the whole stack's selftest: cast, body, hair, wardrobe,
figure, interiors, composer and the editor's pure parts, in one call.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .dome_interiors import (
    DOME_SETS,
    SEAT,
    base_ring_apothem,
    draw_prop,
    draw_room,
    interior_set,
    prop,
    room_report,
    shell_clearance,
    sphere_clearance,
    validate_dome_interiors,
)
from .glam_body import (
    FEMALE_STATURE_FRACTION,
    SHOULDER_TO_HIP,
    glam_joints,
    landmark_height,
    torso_radii,
    validate_glam_body,
)
from .glam_cast import (
    GLAM_CAST,
    MODE_LABEL,
    WARDROBE_MODES,
    cast_ids,
    cast_sheet,
    validate_glam_cast,
)
from .glam_figure import (
    GLAM_POSES,
    Look,
    draw_look,
    line_up,
    look_report,
    validate_glam_figure,
)
from .glam_hair import HAIR_STYLES, hair_report, validate_glam_hair
from .glam_wardrobe import (
    OUTFITS,
    covered_spans,
    validate_glam_wardrobe,
    wardrobe_report,
)
from .lessons import Chapter, Lesson, prose
from .render_kit import AMBER, CYAN, GREEN, MUTED, RED, WHITE, WorldLabel, clamp
from .render_kit import TriangleBatch
from .scene_composer import (
    Composer,
    Placement,
    check,
    draw_scene,
    floor_share,
    footprint_marks,
    scene_report,
    starter_scene,
    tinted,
    validate_scene_composer,
)


STORE = interior_set("DOME_STORE")
HOME = interior_set("DOME_HOME")

DETAIL = 1.0
"""How finely figures are drawn.  A full-detail head of hair is twenty
thousand triangles and this lesson draws a dozen at once, which is fine
for a render and far too slow for a proof that paints every scene three
times.  :func:`validate_lookbook` turns it down and puts it back."""


def _fade(colour, alpha: float):
    return (colour[0], colour[1], colour[2], clamp(alpha) * colour[3])


def _rgb(colour) -> tuple[int, int, int]:
    """A world label wants bytes, and the palette is in floats."""
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _label(app, text, position, colour=WHITE, size=17) -> None:
    del size
    app.world_labels.append(WorldLabel(
        point=np.asarray(position, dtype=float), text=text,
        color=_rgb(colour)))


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_room(app, opaque, transparent, p: float) -> None:
    """The empty store, and the one thing a dome does to a room."""
    draw_room(opaque, transparent, STORE)
    radius = STORE.radius_m
    # Draw the ceiling height as a row of posts standing out from the
    # middle, each one as tall as the dome allows where it stands.
    steps = 9
    for index in range(steps):
        reach = radius * 0.94 * (index + 0.5) / steps
        if reach > radius * clamp(p * 1.4):
            break
        height = shell_clearance(reach, 0.0, radius)
        opaque.cylinder(np.array([reach, 0.0, 0.0]),
                        np.array([reach, 0.0, height]), 0.045,
                        _fade(CYAN, 0.85), 6)
        if index in (0, 4, steps - 1):
            _label(app, f"{height:.1f} m", (reach, 0.0, height + 0.35), CYAN)
    _label(app, "the wall is the ceiling", (0.0, 0.0, radius * 0.55), WHITE, 19)


def scene_furnished(app, opaque, transparent, p: float) -> None:
    """The same dome with a shop in it."""
    scene = starter_scene("DOME_STORE")
    keep = max(1, int(round(len(scene.placements) * clamp(p * 1.15))))
    draw_scene(opaque, transparent,
               scene.with_placements(scene.placements[:keep]), detail=DETAIL)
    _label(app, f"{keep} pieces placed", (0.0, 0.0, STORE.radius_m * 0.72),
           AMBER, 19)
    _label(app, f"{floor_share(scene.with_placements(scene.placements[:keep])) * 100:.0f}% of the floor",
           (0.0, 0.0, STORE.radius_m * 0.62), MUTED, 16)


def _runway(app, opaque, transparent, mode: str, p: float) -> None:
    """The cast in a line, in one wardrobe mode, on a pale floor."""
    opaque.disc(np.array([0.0, 0.0, 0.0]), 7.0, (0.62, 0.60, 0.58, 1.0), 48)
    opaque.disc(np.array([0.0, 0.0, 0.004]), 4.4, (0.70, 0.68, 0.66, 1.0), 40)
    shown = max(1, int(round(len(GLAM_CAST) * clamp(0.25 + p * 1.1))))
    looks = line_up(cast_ids()[:shown], mode, spacing=1.05, yaw_deg=0.0)
    for look in looks:
        draw_look(opaque, replace(look, detail=DETAIL),
                  transparent=transparent)
        who = look.character()
        _label(app, who.name.split()[0],
               (look.position[0], look.position[1], -0.10), WHITE, 15)
    _label(app, MODE_LABEL[mode], (0.0, 0.0, 2.55), AMBER, 22)


def scene_cast(app, opaque, transparent, p: float) -> None:
    _runway(app, opaque, transparent, "STREET", p)


def scene_hair(app, opaque, transparent, p: float) -> None:
    """One woman, twelve heads of hair, cycled."""
    opaque.disc(np.array([0.0, 0.0, 0.0]), 6.4, (0.55, 0.54, 0.56, 1.0), 44)
    styles = tuple(HAIR_STYLES)
    # Two rows of six, not three of four: the camera looks down the X
    # axis, so rows are depth and a third row hides behind the first.
    across = 6
    shown = max(1, int(round(len(styles) * clamp(0.2 + p * 1.05))))
    for index in range(shown):
        row, column = divmod(index, across)
        spec = HAIR_STYLES[styles[index]]
        look = Look(character_id=cast_ids()[index % len(GLAM_CAST)],
                    mode="STREET", hair_style=styles[index],
                    pose_key="power_stand",
                    position=(1.30 - row * 2.60, (column - 2.5) * 1.24, 0.0),
                    yaw_deg=0.0, detail=0.85 * DETAIL)
        draw_look(opaque, look, transparent=transparent)
        _label(app, spec.label,
               (look.position[0], look.position[1], -0.10), CYAN, 14)
    _label(app, "hair is geometry, not a texture", (0.0, 0.0, 2.5), WHITE, 20)


def scene_wardrobe(app, opaque, transparent, p: float) -> None:
    """Four modes, cycling on the same eight women."""
    dressed = tuple(mode for mode in WARDROBE_MODES if mode != "FORM")
    index = min(len(dressed) - 1, int(clamp(p) * len(dressed) * 0.999))
    _runway(app, opaque, transparent, dressed[index], 1.0)
    look = OUTFITS[GLAM_CAST[cast_ids()[0]].wardrobe[dressed[index]]]
    _label(app, look.note, (0.0, 0.0, 2.15), MUTED, 15)


def scene_form(app, opaque, transparent, p: float) -> None:
    """The base layer, and the shop fixture that is the same shape."""
    opaque.disc(np.array([0.0, 0.0, 0.0]), 5.0, (0.66, 0.65, 0.64, 1.0), 40)
    looks = line_up(cast_ids()[:5], "FORM", spacing=1.10, yaw_deg=0.0,
                    detail=DETAIL)
    for look in looks:
        draw_look(opaque, look, transparent=transparent)
    for offset in (-3.05, 3.05):
        draw_prop(opaque, prop("DRESS_FORM"), STORE, offset, 0.0, 0.0)
    _label(app, "the studio form: the silhouette with nothing on it",
           (0.0, 0.0, 2.35), WHITE, 19)
    _label(app, "same shape the shop's own dress form is",
           (0.0, 0.0, 2.05), MUTED, 15)
    del p


def scene_landmarks(app, opaque, transparent, p: float) -> None:
    """The same dress on three different women, stopping in the same place."""
    opaque.disc(np.array([0.0, 0.0, 0.0]), 5.0, (0.58, 0.57, 0.60, 1.0), 40)
    heights = (1.58, 1.72, 1.86)
    for index, stature in enumerate(heights):
        who = cast_ids()[index * 3 % len(GLAM_CAST)]
        look = Look(character_id=who, mode="PARTY", pose_key="power_stand",
                    position=(0.0, (index - 1) * 1.35, 0.0), yaw_deg=0.0)
        joints = glam_joints(GLAM_POSES["power_stand"], stature,
                             look.position, 0.0)
        draw_look(opaque, replace(look, detail=DETAIL), joints=joints,
                  transparent=transparent)
        for landmark, colour in (("waist", AMBER), ("knee", CYAN)):
            height = landmark_height(joints, landmark)
            opaque.cylinder(
                np.array([look.position[0], look.position[1] - 0.55, height]),
                np.array([look.position[0], look.position[1] + 0.55, height]),
                0.014, _fade(colour, clamp(p * 1.5)), 5)
            # Labelled on the far side from the live-calculation panel,
            # which sits on the right of the frame.
            if index == 0:
                _label(app, landmark,
                       (look.position[0], look.position[1] - 0.76, height),
                       colour, 14)
        _label(app, f"{stature:.2f} m",
               (look.position[0], look.position[1], -0.16), MUTED, 15)
    _label(app, "a hem is a landmark, not a number", (0.0, 0.0, 2.35),
           WHITE, 20)


def scene_composer(app, opaque, transparent, p: float) -> None:
    """The editor: a piece held over the room, turning."""
    scene = starter_scene("DOME_STORE")
    draw_scene(opaque, transparent, scene, detail=DETAIL)
    composer = Composer(scene=scene)
    groups = list(composer.groups())
    composer.category_index = groups.index("FIXTURE")
    composer.piece_index = [entry.ref for entry in composer.entries()].index(
        "RAIL_ROUND")
    # Near the middle, where the camera is already looking.  A ghost
    # across the dome is behind everything else in it, and one right
    # under the lens is off the bottom of the frame.
    composer.move_to(1.60, 1.20, snap=False)
    composer.cursor_yaw = 360.0 * clamp(p)
    ghost = composer.ghost()
    verdict = composer.verdict()
    colour = GREEN if verdict.ok else RED
    # The whole piece is recoloured, not just its accent: a ghost that
    # keeps most of its own colours reads as a piece already placed.
    scratch = TriangleBatch()
    draw_prop(scratch, prop(ghost.ref), STORE, ghost.x, ghost.y,
              ghost.yaw_deg)
    transparent.vertices.extend(
        tinted(scratch, _fade(colour, 0.60)).vertices)
    # The same gizmo the editor draws: a bar round the footprint, posts
    # up its corners and a nose pointing the way it faces.  Without it a
    # translucent piece disappears into a room full of pale fixtures.
    footprint_marks(opaque, ghost, colour, STORE.radius_m)
    _label(app, f"holding: {composer.entry().label}", (ghost.x, ghost.y, 2.3),
           colour, 18)
    _label(app, verdict.why, (ghost.x, ghost.y, 2.0), MUTED, 15)


def scene_refusal(app, opaque, transparent, p: float) -> None:
    """The same piece walked out to the wall until the dome says no."""
    draw_room(opaque, transparent, STORE)
    radius = STORE.radius_m
    reach = radius * (0.30 + 0.62 * clamp(p))
    scene = starter_scene("DOME_STORE").with_placements(())
    ghost = Placement("PROP", "FITTING_POD", reach, 0.0, 0.0)
    verdict = check(scene, ghost)
    colour = GREEN if verdict.ok else RED
    scratch = TriangleBatch()
    draw_prop(scratch, prop("FITTING_POD"), STORE, ghost.x, ghost.y, 0.0)
    opaque.vertices.extend(tinted(scratch, _fade(colour, 1.0)).vertices)
    footprint_marks(opaque, ghost, colour, radius)
    head = shell_clearance(ghost.x, ghost.y, radius)
    opaque.cylinder(np.array([ghost.x, ghost.y, 0.0]),
                    np.array([ghost.x, ghost.y, max(0.05, head)]),
                    0.05, _fade(colour, 0.9), 6)
    _label(app, f"{head:.2f} m of dome", (ghost.x, ghost.y, head + 0.4),
           colour, 18)
    _label(app, verdict.why, (ghost.x, ghost.y, head + 0.85), MUTED, 15)
    _label(app, f"the pod is {prop('FITTING_POD').height:.2f} m",
           (0.0, 0.0, radius * 0.55), WHITE, 17)


def scene_home(app, opaque, transparent, p: float) -> None:
    """The other set: the same machinery, a smaller dome, a house."""
    scene = starter_scene("DOME_HOME")
    draw_scene(opaque, transparent, scene, detail=DETAIL)
    _label(app, HOME.label, (0.0, 0.0, HOME.radius_m * 0.80), AMBER, 22)
    _label(app, f"{HOME.radius_m * 2:.0f} m across against the store's "
                f"{STORE.radius_m * 2:.0f}",
           (0.0, 0.0, HOME.radius_m * 0.68), MUTED, 16)
    del p


def scene_finale(app, opaque, transparent, p: float) -> None:
    """The store, full, with the cast in it."""
    scene = starter_scene("DOME_STORE")
    draw_scene(opaque, transparent, scene, detail=DETAIL)
    people = sum(1 for item in scene.placements if item.kind == "CAST")
    props = len(scene.placements) - people
    _label(app, "one catalogue, one shell, one editor",
           (0.0, 0.0, STORE.radius_m * 0.78), WHITE, 21)
    _label(app, f"{props} fixtures and {people} of the cast, all placed "
                f"through the same three keys",
           (0.0, 0.0, STORE.radius_m * 0.66), MUTED, 16)
    del p


SCENES = {
    "look_room": scene_room,
    "look_furnished": scene_furnished,
    "look_cast": scene_cast,
    "look_hair": scene_hair,
    "look_wardrobe": scene_wardrobe,
    "look_form": scene_form,
    "look_landmarks": scene_landmarks,
    "look_composer": scene_composer,
    "look_refusal": scene_refusal,
    "look_home": scene_home,
    "look_finale": scene_finale,
}


# ----------------------------------------------------------------------
# The lesson
# ----------------------------------------------------------------------

CHAPTERS = (
    Chapter(
        "room", "01", "A room with no straight walls",
        "In a dome, how tall a thing can be depends on where it stands.",
        prose((
            "This is a sixteen metre dome with nothing in it. The posts show how",
            "much room there is overhead as you walk out from the middle: eight",
            "metres under the crown, and less every step after that. That single",
            "fact is what makes furnishing a dome different from furnishing a box,",
            "and everything in this lesson is built around it.",
        )),
        ("headroom falls as you walk out",
         "height allowed = shell over the footprint"),
        16.0, (34.0, 20.0, 21.0), "look_room",
    ),
    Chapter(
        "furnished", "02", "The same shell, furnished",
        "Forty-odd pieces in a catalogue, and a shop built out of them.",
        prose((
            "Here is the same dome as a store. Rails, plinths, a cash desk, fitting",
            "pods, a bench, a light ring hung off the shell. Every one of those is",
            "a piece in a catalogue with a footprint and a height, and every one was",
            "placed by the editor we will get to, which measured it against the",
            "shell before it agreed to put it down.",
        )),
        ("floor used = footprints / floor area",),
        16.0, (58.0, 26.0, 22.0), "look_furnished",
    ),
    Chapter(
        "cast", "03", "The cast",
        "Eight women, and not one of them a recolour of another.",
        prose((
            "Eight characters, cast deliberately wide, and each one built to read",
            "in a single frame: her own skin tone, her own hair, her own colour,",
            "her own way of standing. None of them shares a tone or a hair style",
            "with another, and the code refuses to load a cast where two of them do.",
        )),
        ("distinct tone, hair and colour per character",),
        16.0, (0.0, 8.0, 8.4), "look_cast",
    ),
    Chapter(
        "hair", "04", "Hair is geometry",
        "Twelve styles, built as strands off the scalp, not painted on a ball.",
        prose((
            "Hair is most of a silhouette, so it is modelled rather than coloured",
            "in. Each strand leaves the scalp along the direction it grew, hands",
            "over to gravity a head radius later, and carries a wave or a helix",
            "depending on the style. Length is a body landmark, so the same style",
            "fits a woman of any height without a second set of numbers.",
        )),
        ("strand direction = grown, then gravity",
         "length = a landmark on the body"),
        17.0, (0.0, 15.0, 11.6), "look_hair",
    ),
    Chapter(
        "wardrobe", "05", "Four ways to dress the same eight people",
        "Poolside, going out, editorial, shop floor. One list of pieces each.",
        prose((
            "An outfit is not a function somebody wrote. It is a list: a bodice",
            "from this height to that one, a skirt to the knee with this much",
            "flare, a sleeve, a heel. Every shell is lofted through the body's own",
            "cross-section, so a garment cannot come out the wrong size for the",
            "woman wearing it, and each look pulls her own colour so one dress on",
            "two people is still recognisably two people.",
        )),
        ("garment = body cross-section, inflated",),
        18.0, (0.0, 8.0, 8.4), "look_wardrobe",
    ),
    Chapter(
        "form", "06", "The layer underneath",
        "Cycle the clothes off and what is left is the shop's own dress form.",
        prose((
            "There is a fifth mode with no garment pieces in it at all. It draws",
            "the silhouette in her skin tone and nothing else, which is what a",
            "shop's dress form looks like, and it is what the editor shows when",
            "you cycle a figure's clothes off. It carries no anatomy, because a",
            "lofted ellipse has none to carry.",
        )),
        ("form mode = zero garment pieces",),
        14.0, (0.0, 10.0, 7.2), "look_form",
    ),
    Chapter(
        "landmarks", "07", "A hem is a landmark, not a number",
        "The same dress on a 1.58 m woman and a 1.86 m one, both correct.",
        prose((
            "Every hem and every hair length names a place on the body rather than",
            "a measurement: mid thigh, the knee, the waist, the floor. The number",
            "in metres is read off the posed skeleton when the frame is drawn. That",
            "is why one wardrobe fits a cast of eight different heights, and why",
            "nothing has to be retuned when a pose drops a shoulder.",
        )),
        ("hem height = landmark(posed skeleton)",),
        16.0, (0.0, 8.0, 6.8), "look_landmarks",
    ),
    Chapter(
        "composer", "08", "Cycle it, turn it, drop it",
        "The park editor, pointed at a dome.",
        prose((
            "You hold one piece at a time. Two keys walk the categories, two walk",
            "the pieces inside them, one turns it fifteen degrees at a time, and",
            "one drops it. The piece you are holding is drawn as a ghost, green",
            "where it fits and red where it does not, and the cast are one more",
            "category: a woman is placed and turned exactly like a chair.",
        )),
        ("hold, turn, drop, undo",),
        16.0, (66.0, 24.0, 13.5), "look_composer",
    ),
    Chapter(
        "refusal", "09", "What the dome refuses",
        "Walk a two-metre fitting pod out towards the wall and watch it stop.",
        prose((
            "This is the whole idea in one shot. A fitting pod is two point two",
            "metres tall. Near the middle of the dome there is nearly eight metres",
            "over it. Walk it outward and the shell comes down to meet it, and at",
            "some point the editor stops accepting it and says exactly why. Nothing",
            "in the catalogue carries a list of legal spots. The geometry decides.",
        )),
        ("refused when height > shell over the footprint",),
        17.0, (0.0, 12.0, 20.0), "look_refusal",
    ),
    Chapter(
        "home", "10", "The other set",
        "A smaller dome, a house instead of a shop, the same machinery.",
        prose((
            "The house is a thirteen metre dome, warmer and lower, with a bed, a",
            "kitchen run against the curve, a stove whose flue wants the crown, and",
            "a sofa whose seat height came out of the seated pose rather than out",
            "of a table of furniture dimensions. Swap sets with one key and the",
            "catalogue changes with the room.",
        )),
        ("seat height = the seated pose's own hip height",),
        16.0, (46.0, 24.0, 18.0), "look_home",
    ),
    Chapter(
        "finale", "11", "One shell, one catalogue, one editor",
        "Everything you have seen is placed through the same three keys.",
        prose((
            "A dome, a catalogue measured against it, a cast built out of the same",
            "skeleton the rest of this package uses for lifting panels, and an",
            "editor that will not let you put a wardrobe where the roof is. Open it",
            "with the composer command, hold a piece, and turn it until it fits.",
        )),
        (),
        14.0, (24.0, 22.0, 20.0), "look_finale",
    ),
)


def lookbook_equations(app, stage: str) -> list[str]:
    """Live figures for the teaching card, computed at draw time."""
    radius = STORE.radius_m
    if stage == "look_room":
        return [
            f"crown = {shell_clearance(0.0, 0.0, radius):.2f} m",
            f"half way out = {shell_clearance(radius * 0.5, 0.0, radius):.2f} m",
            f"at the wall = {shell_clearance(radius * 0.9, 0.0, radius):.2f} m",
        ]
    if stage == "look_refusal":
        return [
            f"fitting pod = {prop('FITTING_POD').height:.2f} m tall",
            f"base ring apothem = {base_ring_apothem(radius):.2f} m",
            f"faceted shell is never above the sphere",
        ]
    if stage in ("look_landmarks", "look_wardrobe"):
        return [
            f"shoulder-to-hip = {SHOULDER_TO_HIP:.3f}",
            f"waist at 1.72 m = {torso_radii(1.72, 0.32)[0] * 2:.3f} m across",
            f"{len(OUTFITS)} looks over {len(GLAM_CAST)} women",
        ]
    if stage == "look_home":
        return [f"seat height = {SEAT:.3f} m, from the seated pose",
                f"house {HOME.radius_m * 2:.0f} m across, "
                f"store {STORE.radius_m * 2:.0f} m"]
    return []


def _selftest() -> None:
    validate_glam_cast()
    validate_glam_body()
    validate_glam_hair()
    validate_glam_wardrobe()
    validate_glam_figure()
    validate_dome_interiors()
    validate_scene_composer()
    from .composer_app import validate_composer_app
    validate_composer_app()
    validate_lookbook()


def lookbook_report() -> str:
    return "\n\n".join((
        cast_sheet(),
        hair_report(),
        wardrobe_report(),
        look_report("FASHION"),
        room_report("DOME_STORE"),
        scene_report(starter_scene("DOME_STORE")),
        scene_report(starter_scene("DOME_HOME")),
    ))


LOOKBOOK_LESSON = Lesson(
    key="look",
    brand="DOME INTERIORS / CAST, WARDROBE AND THE COMPOSER",
    title="The Dome House Lookbook",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=lookbook_equations,
    selftest=_selftest,
    report=lookbook_report,
    snapshot_prefix="lookbook",
    label_layout="declutter",
)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

class _Recorder:
    """Just enough of the app for a scene painter to draw into."""

    def __init__(self) -> None:
        self.world_labels: list = []


def validate_lookbook() -> None:
    """Prove the lesson before it is rendered."""
    from .render_kit import TriangleBatch

    LOOKBOOK_LESSON.validate()
    assert len(CHAPTERS) == len(SCENES), (len(CHAPTERS), len(SCENES))
    stages = {chapter.stage for chapter in CHAPTERS}
    assert stages == set(SCENES), stages ^ set(SCENES)

    numbers = [chapter.number for chapter in CHAPTERS]
    assert numbers == [f"{index + 1:02d}" for index in range(len(CHAPTERS))]
    slugs = [chapter.slug for chapter in CHAPTERS]
    assert len(set(slugs)) == len(slugs), slugs
    for chapter in CHAPTERS:
        assert chapter.narration, chapter.slug
        assert chapter.promise.endswith("."), chapter.slug
        assert 10.0 <= chapter.duration <= 24.0, chapter.slug

    # Every scene draws at the start, the middle and the end, and puts
    # something on screen at each.  Drawn at low detail, because this is
    # checking that the scene is well formed and not what it looks like.
    global DETAIL
    DETAIL = 0.15
    try:
        for stage, painter in SCENES.items():
            for progress in (0.0, 0.5, 1.0):
                app = _Recorder()
                opaque = TriangleBatch()
                clear = TriangleBatch()
                painter(app, opaque, clear, progress)
                assert opaque.vertices, (stage, progress)
                points = np.asarray(opaque.vertices,
                                    dtype=float).reshape(-1, 10)[:, :3]
                assert points[:, 2].min() > -0.6, (stage, progress)
                assert points[:, 2].max() < 12.0, (stage, progress)
                assert np.isfinite(points).all(), (stage, progress)
                assert app.world_labels, (stage, progress)
    finally:
        DETAIL = 1.0

    # The refusal chapter has to actually refuse somewhere in its run,
    # and accept somewhere else, or the shot proves nothing.
    outcomes = set()
    for step in range(11):
        scene = starter_scene("DOME_STORE").with_placements(())
        reach = STORE.radius_m * (0.30 + 0.62 * step / 10.0)
        outcomes.add(check(scene, Placement("PROP", "FITTING_POD",
                                            reach, 0.0, 0.0)).ok)
    assert outcomes == {True, False}, outcomes

    # The faceted shell is the conservative one, which is the claim the
    # chapter's equations make on screen.
    for step in range(1, 20):
        reach = STORE.radius_m * step / 20.0
        assert shell_clearance(reach, 0.0, STORE.radius_m) <= \
            sphere_clearance(reach, 0.0, STORE.radius_m) + 1e-9

    # Live equations are live: they change with the geometry rather than
    # being typed into the copy.
    for stage in SCENES:
        for line in lookbook_equations(None, stage):
            assert line and not line.endswith(":"), (stage, line)
    assert any(f"{STORE.radius_m:.2f}" in line
               for line in lookbook_equations(None, "look_room"))

    # Wardrobe coverage is stated in the lesson and true in the data.
    for look in OUTFITS.values():
        if look.mode == "FORM":
            assert not covered_spans(look), look.outfit_key
        else:
            assert covered_spans(look), look.outfit_key

    # The report is complete enough to publish beside the film.
    text = lookbook_report()
    for needed in ("THE DOME HOUSE CAST", "HAIR", "WARDROBE", "LOOKBOOK",
                   "THE DOME STORE", "THE DOME HOUSE"):
        assert needed in text, needed
    assert len(text) > 4000, len(text)

    # Both sets are reachable from the lesson.
    assert set(DOME_SETS) == {"DOME_HOME", "DOME_STORE"}
    assert FEMALE_STATURE_FRACTION["hip_width"] > \
        FEMALE_STATURE_FRACTION["shoulder_width"] * 0.75


if __name__ == "__main__":
    _selftest()
    print("lookbook ok")
    print(lookbook_report()[:2000])
