"""The stem-cell campaign's image prompts, written out from the model.

One prompt per asset, for Gemini (Imagen / Nano Banana), ChatGPT images or any
other generator: the hero, a LEGO-style instruction manual for the frame, the
utility core, the pad, the layers of the shell, the seam channel, the mast and
floating rig, the park, one picture per fit-out, one icon per panel, one
graphic per reward tier and per goal line, the social launch series, and the
book and web-app assets.

**The look is a premium building-brick set** (``STYLE_BRICK``): every part a
crisp, separately moulded piece, one colour key across every image, box-art
lighting. The geometry is not left to the image model's imagination -- the
long ``dome_truth`` block walks the dome row by row, and its counts are read
from :func:`two_v_demo.geometry.build_demo_geometry` and checked against
:func:`seed_model.seed_geometry`, so the description cannot drift from the
building.

Three rules, all enforced by :func:`validate_prompts`:

**Image models draw no numbers.** A prompt body may not contain a digit (the
only exceptions are "2V" and one hex colour). Generators garble figures, and a
garbled price on a campaign graphic is worse than none. Every figure a
graphic needs is listed separately as *overlay copy*, read out of the model,
and set in type afterwards (Canva, Figma, the web app).

**The catalogues drive the prompts.** Every reward tier, fit-out, panel, goal
line, core part, pad part, pad build step, foundation type and module mount
in the model gets a picture. Add one to the model and forget its picture, and
the check fails rather than the campaign quietly missing a graphic.

**The layout is asserted.** If the geometry ever stops being six stars and
ten equilateral triangles, the row-by-row description is wrong, and the check
says so instead of shipping it.

    py -3.12 campaign_prompts.py            # write the pack (never overwrites)
    py -3.12 campaign_prompts.py --check    # just the checks
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

import kickstarter
import pad_deck
import seed_model
import soft_shell
from two_v_demo.deliverables import next_version_path
from two_v_demo.geometry import build_demo_geometry

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "deliverables" / "promo" / "stem-cell-campaign-prompts.md"


# ----------------------------------------------------------------------
# Words for numbers, so a prompt can say "forty" without a digit
# ----------------------------------------------------------------------

_ONES = ("zero one two three four five six seven eight nine ten eleven "
         "twelve thirteen fourteen fifteen sixteen seventeen eighteen "
         "nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n: int) -> str:
    """0-199 in words. Enough for every count a prompt describes."""
    n = int(n)
    if n < 0 or n > 199:
        raise ValueError(f"{n} is outside what a prompt should spell out")
    if n >= 100:
        rest = n - 100
        return "one hundred" + (f" and {words(rest)}" if rest else "")
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")


def about(x: float) -> str:
    """A measurement to the nearest half, in words: 4.59 -> 'four and a half'."""
    halves = round(x * 2)
    whole, half = divmod(halves, 2)
    return words(whole) + (" and a half" if half else "")


def usd(x: float) -> str:
    return f"${x:,.0f}"


# ----------------------------------------------------------------------
# What the model says the product is
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Facts:
    """Every figure the pack prints, read once from the model."""

    across_ft: float
    tall_ft: float
    floor_sqft: float
    bays: int
    members: int
    base_sides: int
    vertices: int
    face_classes: tuple[tuple[str, int], ...]
    long_in: float
    member_width_in: float
    member_depth_in: float
    seams: int
    price: float
    built: float
    margin: float
    per_sqft: float
    goal: float
    trees_vs_mitred: float
    wedge_vs_milled: float
    shirts_per_layer: int
    pad_across_ft: float
    column_rise_ft: float
    water_tank_gal: float


def facts() -> Facts:
    geo = seed_model.seed_geometry()
    stack = kickstarter.cost_stack()
    harvest = seed_model.harvest()
    return Facts(
        across_ft=2.0 * geo.radius_in / 12.0,
        tall_ft=geo.height_in / 12.0,
        floor_sqft=geo.floor_decagon_sqft,
        bays=sum(face.count for face in geo.faces),
        members=sum(member.count for member in geo.members),
        base_sides=geo.base_sides,
        vertices=geo.vertex_count,
        face_classes=tuple((face.name, face.count) for face in geo.faces),
        long_in=geo.long_edge_in,
        member_width_in=geo.member_width_in,
        member_depth_in=geo.member_depth_in,
        seams=geo.seam_count,
        price=stack.price,
        built=stack.built,
        margin=stack.margin,
        per_sqft=stack.per_sqft,
        goal=kickstarter.goal(),
        trees_vs_mitred=seed_model.trees_against_mitred(),
        wedge_vs_milled=harvest.wedge_bf / harvest.dimensional_bf,
        shirts_per_layer=kickstarter.quilt_economics()["shirts_per_layer"],
        pad_across_ft=pad_deck.pad_diameter_ft(),
        column_rise_ft=seed_model.column_rise_ft(),
        water_tank_gal=seed_model.declared("water_tank_gal"),
    )


# ----------------------------------------------------------------------
# The layout, read off the real mesh
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Layout:
    """How the forty triangles sit, counted from the mesh the films draw."""

    apex_valence: int
    stars: int                 # five-way junctions: the centres of the stars
    lower_stars: int
    six_way: int               # junctions where six struts meet
    base_corners: int
    base_corner_valence: int
    short_edges: int
    long_edges: int
    base_edges: int
    rows: tuple[tuple[int, str, str], ...]  # (count, 'equi'|'iso', 'up'|'down'), top first
    long_over_short: float

    @property
    def equilateral(self) -> int:
        return sum(n for n, kind, _ in self.rows if kind == "equi")

    @property
    def seams(self) -> int:
        return self.short_edges + self.long_edges - self.base_edges


def layout() -> Layout:
    geo = build_demo_geometry()
    v = np.asarray(geo.vertices)
    edges = [tuple(map(int, e)) for e in geo.hemisphere_edges]
    faces = [tuple(map(int, f)) for f in geo.hemisphere_faces]

    def length(a: int, b: int) -> float:
        return float(np.linalg.norm(v[a] - v[b]))

    short = min(length(a, b) for a, b in edges)
    long_ = max(length(a, b) for a, b in edges)
    is_short = lambda a, b: abs(length(a, b) - short) < 1e-6  # noqa: E731
    degree: Counter = Counter()
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    apex = max(degree, key=lambda i: v[i][2])
    base = [i for i in degree if abs(v[i][2]) < 1e-6]
    base_edges = [e for e in edges if e[0] in base and e[1] in base]

    rows: Counter = Counter()
    for f in faces:
        z = round(float(np.mean([v[i][2] for i in f])), 3)
        shorts = sum(is_short(a, b) for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
        zs = sorted(v[i][2] for i in f)
        pointing = "up" if zs[1] - zs[0] < 1e-3 else "down"
        rows[(z, "iso" if shorts else "equi", pointing)] += 1
    ordered = tuple((n, kind, way) for (z, kind, way), n in sorted(rows.items(), reverse=True))

    return Layout(
        apex_valence=degree[apex],
        stars=sum(1 for i, d in degree.items() if d == 5),
        lower_stars=sum(1 for i, d in degree.items() if d == 5 and i != apex),
        six_way=sum(1 for d in degree.values() if d == 6),
        base_corners=len(base),
        base_corner_valence=degree[base[0]],
        short_edges=sum(is_short(a, b) for a, b in edges),
        long_edges=sum(not is_short(a, b) for a, b in edges),
        base_edges=len(base_edges),
        rows=ordered,
        long_over_short=long_ / short,
    )


#: The shape the row-by-row description is written for. If the mesh stops
#: matching it, the words are wrong and the check fails.
EXPECTED_ROWS = ((5, "iso", "up"), (5, "equi", "down"), (10, "iso", "down"),
                 (10, "iso", "down"), (5, "equi", "up"), (5, "iso", "up"))


# ----------------------------------------------------------------------
# The blocks every prompt is assembled from
# ----------------------------------------------------------------------

COLOUR_KEY = (
    "COLOUR KEY -- identical in every image of this series, so a part is "
    "recognisable from one picture to the next: "
    "LONG wedge members = warm natural tan with a faint printed wood grain; "
    "SHORT wedge members = a deeper honey-caramel tan, so the short members "
    "visibly draw the six five-pointed stars across the dome; "
    "plain panels = matte cream white; window and skylight panels = clear "
    "pale-blue translucent; door panel = charcoal grey; "
    "the DOME OWNER's hardware (utility column, apex seal cap, utility "
    "panels, the dome's own floor) = bright cyan-teal; "
    "the PAD HOST's hardware (service port, electrical pedestal, frost "
    "valve, water tank, under-floor hatches) = bright warm amber (hex "
    "FFB13E); "
    "service lines = power bright yellow, water blue, drain dark grey, air "
    "white; the pad's deck = light brown plank tiles on dark grey pier "
    "blocks; the ground = a green studded baseplate."
)

STYLE_BRICK = (
    "STYLE -- A PREMIUM BUILDING-BRICK MODEL SET. Render the subject as a "
    "top-quality construction-toy model photographed for the front of its "
    "box. Every part is a distinct, separately moulded piece: perfectly "
    "crisp edges, tiny uniform bevels on every corner, smooth satin plastic "
    "surfaces, bright clean colours, no wear, no dust, no weathering. Parts "
    "look as if they click together: joints are exact, the gaps between "
    "pieces are thin even shadow lines, and nothing is glued, taped, bent, "
    "patched or improvised. Proportions are TRUE to the real building -- a "
    "scale model, not a cartoon: no squashing, no oversized parts, no "
    "rounded blobby shapes. The only studs (round bumps) in the picture are "
    "on the green ground baseplate and along the rim of the pad; the dome "
    "itself has none. Scale people, where named, are simple blocky "
    "unbranded toy figures with cylindrical heads and a friendly painted "
    "face, standing a little over half the dome's height. "
    "LIGHT: bright soft studio light from the upper left, gentle shadow in "
    "every joint, soft contact shadows on the baseplate, a faint glossy "
    "highlight on the panels. BACKGROUND: a clean seamless gradient, pale "
    "sky-blue fading to white, unless a scene is named; a named scene is "
    "built from toy parts too (studded green baseplates, brick-built pine "
    "trees with stacked cone foliage, round tile paths). CAMERA: box-art "
    "three-quarter view from about thirty degrees above the ground, slight "
    "telephoto so straight lines stay straight, the model centred with "
    "generous margins. No text, no letters, no numbers, no logos, no brand "
    "names, no box or packaging, no watermark -- only the model. "
    f"{COLOUR_KEY}"
)

STYLE_MANUAL = (
    "STYLE -- A BUILDING-BRICK INSTRUCTION-MANUAL PAGE. The same toy-model "
    "parts and colour key as the box art, drawn the way a construction-toy "
    "manual draws them: clean flat-lit three-quarter view on a plain "
    "off-white page, parts slightly glossy, new parts added in this step "
    "shown in full colour with a small grey arrow showing where they go, "
    "parts from earlier steps shown in full colour but already in place. "
    "A light-blue rounded callout box in the top-left corner shows only the "
    "parts added in this step, laid out flat, grouped by type. Leave empty "
    "space in the bottom-left corner for a step number, which is added "
    "later -- do NOT draw any numbers, letters or quantity marks. "
    f"{COLOUR_KEY}"
)

STYLE_PHOTO = (
    "STYLE -- pristine architectural photography of the real, full-size, "
    "precisely built object. Calm, clean, confident. Natural light, sharp "
    "focus front to back, true-to-life colour. The timber is pale, freshly "
    "split and sanded pine with straight visible grain -- exact, not "
    "rustic, not weathered, not glued or patched. Every seam tight and "
    "even. Tidy ground: mown grass, gravel or the timber pad. No clutter, "
    "no text, no letters, no numbers, no logos, no watermark."
)

STYLE_ICON = (
    "STYLE -- a single flat vector icon on a plain square background. "
    "Two-weight line drawing in charcoal with one warm-amber fill accent, "
    "rounded line caps, generous padding, perfectly centred, readable at "
    "thumbnail size and consistent with the rest of the set: same line "
    "weight, same corner radius, same amber. No text, no letters, no "
    "numbers, no gradient, no drop shadow."
)

AVOID = (
    "AVOID: metal hubs or connector plates, round dowel or pipe struts, "
    "square-cornered dimensional lumber, a full sphere, a smooth curved "
    "dome, more or fewer than the stated stars, a tent or canvas skin, "
    "party lights, rainbow colours outside the colour key, confetti, glue, "
    "patches, mismatched panels, weathered wood, studs on the dome, "
    "garbled text, any words or numbers, logos, watermarks."
)

MASCOT = (
    "Lumen, the project's mascot: a small low-polygon jellyfish, faceted "
    "like the dome, with a softly glowing translucent cyan bell and a few "
    "trailing faceted tentacles; friendly and curious, never goofy. Small in "
    "frame, never covering the dome."
)


def dome_truth(f: Facts, lay: Layout) -> str:
    """The stem cell, described exactly. Every count is the mesh's."""
    return (
        "THE MODEL -- A 2V GEODESIC STEM-CELL DOME. The geometry below is "
        "exact; follow it rather than any general idea of a geodesic dome. "
        # (1) form and scale
        "(ONE) OVERALL FORM AND SCALE: exactly half a sphere, twice as wide "
        f"as it is tall, standing on a flat {words(f.base_sides)}-sided base "
        f"ring. Full size it is about {about(f.across_ft)} feet across and "
        f"{about(f.tall_ft)} feet tall, and each long member is about "
        f"{about(f.long_in / 12)} feet long; a person standing beside it "
        "reaches a little over halfway up. The surface is made of "
        f"{words(f.bays)} FLAT triangles (bays), so its outline is a crisp "
        "faceted polygon, never a smooth curve. "
        # (2) the star pattern
        "(TWO) WHERE EVERY TRIANGLE GOES, TOP TO BOTTOM: at the very top, "
        f"{words(lay.apex_valence)} struts meet at one point, the apex, making "
        f"a five-pointed star of {words(lay.rows[0][0])} triangles -- the "
        f"crown. Directly under the crown, {words(lay.rows[1][0])} "
        "equilateral triangles hang point-down, one beneath each outer side "
        f"of the crown. Around the lower wall stand {words(lay.lower_stars)} "
        "more five-pointed stars, evenly spaced, each centred a little below "
        "the dome's mid-height on a point where five struts meet; the lowest "
        "triangle of each lower star rests its wide side on the base ring "
        "with its point up at the star's centre. Between each pair of "
        f"neighbouring lower stars, one of {words(lay.rows[4][0])} more "
        "equilateral triangles stands point-up on the base ring. So the "
        f"whole dome is {words(lay.stars)} stars of five triangles plus "
        f"{words(lay.equilateral)} equilateral triangles, {words(f.bays)} in "
        f"all. Every other junction has six struts meeting ({words(lay.six_way)} "
        f"of them); the {words(lay.base_corners)} corners of the base ring "
        f"have {words(lay.base_corner_valence)}. "
        # (3) two lengths
        "(THREE) ONLY TWO STRUT LENGTHS: the SHORT struts "
        f"({words(lay.short_edges)} lines) are exactly the spokes of the "
        f"{words(lay.stars)} stars -- every spoke is short and nothing else "
        f"is. The LONG struts ({words(lay.long_edges)} lines) are everything "
        "else: the outline of each star, the sides of the equilateral "
        f"triangles, and all {words(lay.base_edges)} sides of the base ring. "
        "Long is only about one-eighth longer than short, so every triangle "
        "looks nearly equilateral; the difference is subtle but consistent, "
        "and the two-tone colour key makes it readable. "
        # (4) wedges
        "(FOUR) EVERY MEMBER IS A WEDGE -- POINT IN, FLAT FACE OUT: a solid, "
        "straight timber bar whose cross-section is a TRIANGLE, like one "
        "slice of a pie split from a round log, about "
        f"{about(f.member_width_in)} inches across its flat face and "
        f"{words(round(f.member_depth_in))} inches deep from that face to its "
        "point. It lies with the FLAT FACE ON THE OUTSIDE of the dome, flush "
        "with the surface, and the SHARP POINT AIMED INWARD at the centre of "
        "the dome. From outside you see flat faces; from inside you see a "
        "lattice of sharp ridges. Each bay has ITS OWN three wedges forming a "
        "triangular frame, so along every line between two bays lie TWO "
        f"wedges side by side, back to back ({words(lay.seams)} doubled "
        f"seams), while each of the {words(lay.base_edges)} base-ring sides "
        f"has a single wedge -- {words(f.members)} wedges in all. The angled "
        "sides of two neighbouring wedges do not close flat against each "
        "other: along every seam they leave a slim V-shaped channel, open to "
        "the inside, running unbroken from junction to junction. At each "
        "corner of a bay the three wedges lap pinwheel-fashion, each end "
        "butting against the side of the next rather than being cut to a "
        "point. There are NO hubs, plates, bolts or connectors anywhere: "
        "wedges meet wedges directly. "
        # (5) panels
        "(FIVE) PANELS: each bay is closed by one flat triangular panel laid "
        "ON the outside face of its own three wedges and pulled tight by four "
        "small flush screw heads, so the outside of a closed dome is a "
        "continuous faceted skin of panels with thin, even seam lines between "
        "them. Behind every panel the depth of the wedges leaves an empty "
        "triangular cavity; the seam channels connect all of these cavities. "
        # (6) apex and centre
        "(SIX) THE CENTRE: the apex has the only opening in the whole "
        "surface, closed by a round cyan seal cap -- a lid with small "
        "over-centre catches around its rim. Directly beneath it the utility "
        "column, a slim square cyan upright chase, rises from the centre of "
        "the floor to the apex. "
        # (7) base
        f"(SEVEN) THE BASE: the {words(f.base_sides)} corners of the base "
        f"ring rest on the pad, a flat {words(f.base_sides)}-sided timber "
        "platform a little wider than the dome, with one square service port "
        "at its exact centre, directly under the column."
    )


# ----------------------------------------------------------------------
# Records
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Asset:
    id: str
    title: str
    use: str          # where it goes
    aspect: str       # ratio to ask the generator for
    prompt: str       # what the image model sees: no digits
    overlay: str = ""  # what gets set in type afterwards, from the model
    style: str = "brick"
    truth: bool = True  # prepend the full dome description


STYLES = {"brick": STYLE_BRICK, "manual": STYLE_MANUAL, "photo": STYLE_PHOTO,
          "icon": STYLE_ICON}


def _schematic_style() -> str:
    from campaign_schematics import STYLE_SCHEMATIC
    return STYLE_SCHEMATIC + COLOUR_KEY


#: Platform sizes. The platforms' own published specs, not ours -- declared
#: with where they come from, and worth re-checking before upload.
PLATFORM_SPECS: tuple[tuple[str, str, str], ...] = (
    ("16:9", "1920 x 1080 (Kickstarter project image: 1024 x 576 minimum)",
     "Kickstarter project image, YouTube thumbnail, web hero"),
    ("1:1", "1080 x 1080", "Instagram / Facebook feed square"),
    ("4:5", "1080 x 1350", "Instagram feed portrait -- the tallest a feed post goes"),
    ("9:16", "1080 x 1920", "Stories, Reels, TikTok, YouTube Shorts covers"),
    ("3:2", "680 px wide, any height", "Kickstarter story-section graphics"),
    ("21:9", "2560 x 1440 banner, safe area 1546 x 423 centred",
     "YouTube channel banner (generate wide, keep the dome in the middle)"),
    ("2.7:1", "820 x 312 (desktop) / 640 x 360 (mobile)", "Facebook page cover"),
    ("3:1", "1500 x 500", "X / Twitter header"),
    ("1.91:1", "1200 x 630", "Open Graph share image for the web app"),
)


# ----------------------------------------------------------------------
# Hand-written visuals, keyed to the model's catalogues
# ----------------------------------------------------------------------

#: What each part of the utility core looks like. Keyed by the part's name in
#: seed_model.CORE_PARTS / PAD_PARTS; the part's own spec text (with its
#: numbers) goes in the overlay.
PART_VISUALS: dict[str, str] = {
    # the dome's
    "Column housing": "a slim square upright chase, about as wide as a "
    "person's shoulders are deep, standing on the floor's centre and rising "
    "to the apex; its whole front is one removable cyan cover panel held by "
    "small catches, shown lifted off and leaning against it so everything "
    "inside is visible",
    "Apex sleeve": "a flanged cyan collar set into the apex ring of the "
    "shell, the top of the column landing inside it with a black gasket "
    "ring between them",
    "Seal cap": "a round cyan lid over the apex sleeve with six small "
    "over-centre catches around its rim, one catch flipped open",
    "Feeder tail and inlet": "a thick yellow power cord with a large "
    "round plug, running from the pad's amber pedestal across the deck "
    "to a recessed cyan inlet socket at the foot of the column",
    "Sub-panel": "a small grey electrical load-centre box mounted inside "
    "the column at chest height, its door open",
    "Branch breakers": "a single neat row of four toggle breakers in the "
    "sub-panel, one visibly left free as the spare",
    "Outlet ring": "a yellow cable running round the inside of the base "
    "ring, tucked into the seam channels, with small white outlet sockets "
    "set between the wedges at regular intervals",
    "Lighting circuit": "a yellow cable rising up the column to a round "
    "ceiling light and a small fan hanging just below the apex",
    "Riser and shutoff": "a single blue flexible water pipe rising up "
    "through the floor port into the column, with a blue lever valve at "
    "knee height",
    "Manifold": "a short horizontal blue bar on the column with four "
    "outlets, each with its own small blue valve handle",
    "Fixture tails": "short blue pipe stubs from the manifold, each "
    "closed with a neat cap, waiting for a fixture",
    "Trap and stack": "a dark grey drain pipe running down the inside of "
    "the column to a U-shaped trap at its foot",
    "Floor-port tie-in": "a black rubber boot where the grey drain pipe "
    "passes down through the deck",
    "Seam manifold": "a small white collector box at the base ring where "
    "white air lines gather out of the seam channels, with a little fan "
    "beside it",
    # the host's
    "Electrical pedestal": "a short amber post standing on the edge of "
    "the pad with a hinged lockable cover and a socket inside",
    "Submeter": "a small round-faced meter inside the amber pedestal's "
    "enclosure, behind a clear window",
    "Water stub and frost valve": "a blue pipe stub rising through the "
    "deck inside the dome's footprint, fed from an amber frost-proof "
    "shutoff valve standing at the pad's edge",
    "Water tank": "a wide low amber tank lying in the space under the "
    "deck boards, seen through a cutaway in the pad",
    "Drain connection": "a dark grey pipe stub ending in the service "
    "port, closed by an amber cap when no dome is on the pad",
    "Service port": "one square framed amber opening through the middle "
    "of the deck, through which the yellow, blue and grey lines all come up",
    "Under-floor storage": "hinged amber hatches in the deck boards "
    "opening onto neat boarded storage space between the piers",
}

#: One visual per step of the pad's build, keyed by pad_deck's step label.
PAD_STEP_VISUALS: dict[str, str] = {
    "compacted gravel base over fabric": "a flat ten-sided bed of grey "
    "gravel tiles laid over a thin black landscape-fabric sheet on the "
    "green baseplate",
    "precast piers": "neat rows of dark grey square pier blocks set on the "
    "gravel in a regular grid",
    "beams, doubled 2x6": "pairs of long light-brown beams laid across the "
    "tops of the piers, parallel",
    "joists at 16 in centres": "evenly spaced light-brown joists laid "
    "across the beams at right angles, close together",
    "deck boards, 2x6 laid flat": "light-brown plank tiles laid across the "
    "joists, trimmed to a ten-sided outline, with the square service "
    "port left open at the centre",
    "hangers, structural and deck screws": "small metal hangers at every "
    "joist end and neat rows of tiny screw heads along each board",
    "two coats of penetrating sealer": "the finished ten-sided deck with a "
    "soft satin sheen, a roller and tray resting at its edge",
}

#: One visual per foundation type in pad_deck.KINDS.
DECK_VISUALS: dict[str, str] = {
    "gravel": "a ten-sided bed of compacted grey gravel tiles and nothing "
    "else -- a base course, clearly not a floor",
    "blocks": "the framed timber deck on dark grey pier blocks, light-brown "
    "plank tiles, sealed",
    "blocks_epoxy": "the same framed deck on piers, topped with a smooth "
    "seamless glossy grey floor sheet over plywood",
    "ring": "a grey concrete ring under the ten corners of the dome with "
    "a timber-framed middle filling the centre",
    "slab": "one solid, smooth grey concrete slab, ten-sided, the finished "
    "floor itself",
}

#: One setting per fit-out; the *what* comes from seed_model.fitouts().
FITOUT_SCENES: dict[str, str] = {
    "stem_cell": "on its pad at the edge of a toy meadow; every bay a plain "
                 "cream panel except the open doorway, through which the "
                 "cyan utility column rises to the apex",
    "home": "at the edge of a brick-built woodland clearing at dusk, warm "
            "light in the windows, a small stove pipe leaving one upper bay",
    "food": "on a grey tile lot beside a toy road, a serving hatch open "
            "with its awning out, two toy figures queuing",
    "advertiser": "beside a toy highway at blue hour, every panel evenly "
                  "lit from inside in one calm white glow, like a lantern",
    "storage": "in a tidy toy farmyard, a roll-up shutter half open showing "
               "neat racking inside",
    "bunker": "buried in a green studded hillside so only a low mound "
              "shows, the apex riser breaking the turf and a stair "
              "descending to a door set in the slope",
    "treehouse": "raised on a timber saddle between the trunks of a large "
                 "brick-built tree, a stair spiralling up the trunk",
    "sauna": "on a timber deck beside a blue tile lake, a wisp of white "
             "steam from one louvre",
    "gym": "in a back garden beside a brick-built family house, mirrors "
           "visible through the open door",
    "guest": "at the far end of a garden, a path of round tiles leading to "
             "its door, the main house behind",
    "workshop": "in a rural toy yard, skylights bright in the upper ring, a "
                "workbench visible through the door, solar arrays on the "
                "sunward face",
    "garage": "at the end of a gravel-tile drive, one wide roll-up door "
              "spanning three base bays, a small toy car inside",
    "studio": "under brick-built trees at golden hour, one generous window, "
              "a desk and a guitar glimpsed inside",
    "nursery": "joined by a short covered walkway to the side of a family "
               "house, a mobile hanging inside the window",
    "jacuzzi": "turned upside down and set into a deck as a round hot tub, "
               "the timber frame as its cradle, water steaming at night",
}

SHAPES: dict[str, str] = {
    "hemisphere": "standing as a plain hemisphere",
    "buried": "buried",
    "treed": "raised into a tree",
    "inverted": "turned over",
}

#: One object per reward tier; label, price and reason come from kickstarter.
TIER_SCENES: dict[str, str] = {
    "plans": "a neat stack of large-format construction drawings and a "
             "printed book lying open on a workbench, a single split timber "
             "wedge resting on them as a paperweight",
    "quilter": "a quilter's kit laid out flat: a folded pattern sheet, "
               "spools of heavy thread, a roll of binding tape, a large "
               "triangular template and a small stack of folded recycled "
               "clothing in bright patchwork colours",
    "hardware": "one triangular bay's hardware laid out like a parts "
                "inventory: four threaded inserts, a row of flange screws, "
                "a coiled spline gasket and a small seam key, beside a "
                "short section of wedge showing where each piece goes",
    "cap": "the glossy smoke-blue rain cap folded into a tidy bundle, one "
           "corner opened out to show a hemmed edge with grommets and a "
           "coiled webbing strap, and a small dome wearing the same cap "
           "behind it",
    "core": "the cyan utility column standing upright on its own like a "
            "product shot: the floor port at its base, the blue manifold, "
            "the grey drain stack, the small electrical panel, and the "
            "round seal cap on top",
    "kit_notrees": "a complete dome kit on pallets: bundles of tan and "
                   "honey-caramel wedges strapped in neat stacks, cream "
                   "triangular panels on edge, the folded cap and the cyan "
                   "column in its crate",
    "kit_trees": "a customer's own pine log split into wedges fanned out "
                 "like the segments of an orange, beside a neat crate of "
                 "everything else -- panels, cap, column",
    "pad": "a large-format drawing set for the ten-sided platform spread on "
           "a site table, with the finished pad behind it, its amber "
           "service port at the centre",
}

#: One small spot illustration per line of the goal.
GOAL_SCENES: dict[str, str] = {
    "test_platform": "a single finished dome on a test pad with a few "
                     "cables to a data logger in a weatherproof box",
    "instrumentation": "a cutaway of one wall bay with small sensors tucked "
                       "into the seam channel, thin wires leading to a logger",
    "hub_rnd": "three versions of the cyan utility column side by side, "
               "each a little cleaner than the last",
    "cnc_router": "a CNC router with a large flat bed cutting a triangular "
                  "panel from a sheet",
    "cnc_plasma": "a CNC plasma table cutting a steel triangle, a spray of "
                  "toy sparks",
    "laser_cutter": "a laser cutter trimming a triangular gasket from a "
                    "sheet of rubber",
    "strut_tooling": "a steel mould opened on a bench, a finished wedge "
                     "lying in it with its hardware moulded in",
    "composite_rnd": "a triangular composite panel cut through to show a "
                     "steel core inside a moulded shell",
    "automation": "a short conveyor feeding identical wedges through a "
                  "saw station",
    "quilt_seed": "a table of toy figures sewing a large patchwork of "
                  "bright recycled fabric, seen from above",
    "engineering": "an engineer's desk with a load diagram of the dome, a "
                   "scale model and a calculator",
    "fulfilment": "a tidy packing bay of crates and flat parcels on a "
                  "pallet, ready for a lorry",
}

#: Where each kind of module mounts, in words, for the module map.
MOUNT_WORDS: dict[str, str] = {
    "column": "ON THE UTILITY COLUMN (fixtures that need water and drain "
              "hang straight off it)",
    "polyp": "IN A UTILITY PANEL OUTSIDE (noisy, hot or weather-facing "
             "equipment lives outside the footprint)",
    "panel": "IN A BAY PANEL (a fixture built into one triangle of the "
             "wall)",
    "floor": "UNDER OR ON THE FLOOR",
    "apex": "ON THE APEX (sitting on top of the seal cap)",
}


# ----------------------------------------------------------------------
# The sections
# ----------------------------------------------------------------------

def _scrub(text: str) -> str:
    """A model label with a digit in it, said in words for an image model."""
    return text.replace("360 camera ring", "all-round camera ring")


def _panel_mix(panels: dict[str, int]) -> str:
    names = {p.key: p.label.lower() for p in seed_model.PANELS}
    parts = [f"{words(n)} {names[key]}{'s' if n > 1 else ''}"
             for key, n in panels.items()]
    if not parts:
        return "plain closed panels in every bay but the door"
    return ", ".join(parts) + ", and plain closed panels in the other bays"


def hero_assets(f: Facts, lay: Layout) -> list[Asset]:
    stats = (f"{f.across_ft:.1f} ft across · {f.tall_ft:.1f} ft tall · "
             f"{f.floor_sqft:,.0f} sq ft of floor · {f.bays} bays · "
             f"{f.members} wedges")
    hero_scene = (
        "SCENE: the stem-cell dome as the hero model of its set, dead "
        "centre on its ten-sided pad, the pad on a green studded baseplate "
        "with two brick-built pines far behind. About two-thirds of the "
        "bays carry their cream panels; the panels are LEFT OFF one "
        "wedge-shaped sector running from the apex down to the base on the "
        "right-hand side, the way a half-built set is shown, so the tan and "
        "honey-caramel wedge frame is clearly visible there -- the flat "
        "faces outward, the sharp points inward, two wedges back to back "
        "along each seam, the star pattern of short caramel spokes. One "
        "base bay is the open doorway, and through it and through the open "
        "sector the cyan utility column rises to the cyan seal cap at the "
        "apex. One toy figure stands beside the door for scale. "
    )
    return [
        Asset("HERO-1", "The stem cell -- box-art hero",
              "Kickstarter project image, web hero, every platform's lead image",
              "16:9 (then re-ask 1:1, 4:5, 9:16: 'same image, same model, recomposed')",
              hero_scene + AVOID,
              overlay=f"THE STEM CELL -- one frame, any building. {stats}"),
        Asset("HERO-1-PHOTO", "The same hero as a full-size photograph",
              "Alternative lead image if the toy look is too playful for a slot",
              "16:9", hero_scene.replace("toy figure", "person").replace(
                  "green studded baseplate", "mown meadow").replace(
                  "brick-built pines", "pines") + AVOID, style="photo",
              overlay=f"THE STEM CELL -- {stats}"),
        Asset("HERO-2", "The wedge, explained in one picture",
              "Kickstarter story header, thumbnail", "16:9",
              "SCENE: the finished dome soft in the background. In the sharp "
              "foreground, one long tan wedge and one short honey-caramel "
              "wedge stand on end on a small display plinth, their TRIANGULAR "
              "end-faces toward the camera, each with printed growth rings "
              "showing that the point of the triangle is the heart of the log "
              "and the wide flat face is the bark side. A thin grey arrow on "
              "the plinth shows 'flat face out' by pointing from the flat face "
              "toward the viewer. Beside them, a short section of a round log "
              "is shown split into pie-slice wedges, one slice pulled out. "
              + AVOID,
              overlay="Point in. Flat face out. Split, not milled."),
        Asset("HERO-3", "Blue hour, one warm window",
              "Launch-day post, YouTube thumbnail background, email header",
              "16:9",
              "SCENE: the finished dome, every bay panelled, on its pad in a "
              "toy landscape at blue hour, a deep indigo gradient sky, warm "
              "light glowing from the open doorway and one pale-blue window "
              "panel. Calm, no party, no coloured lights. " + AVOID,
              overlay="Live on Kickstarter"),
        Asset("HERO-4", "The seam, macro",
              "Detail post, story divider, web-app section background", "4:5",
              "SCENE: a close-up from INSIDE the dome of one junction where "
              "six wedges arrive: the sharp inward points of the wedges "
              "forming ridges, and between each pair of back-to-back wedges "
              "the slim V-shaped seam channel running away from the junction "
              "like a gutter, with a thin white air line lying in one of them. "
              "Behind the wedges, the back faces of the cream panels. "
              + AVOID,
              overlay="The seam does four jobs."),
        Asset("HERO-5", "Top-down plan",
              "Logo source, favicon, profile avatar, pattern tile", "1:1",
              "SCENE: the dome seen from DIRECTLY ABOVE, perfectly centred on "
              "the ten-sided pad: the crown star at the centre with the cyan "
              "seal cap on its apex, the five equilateral triangles around "
              "it, then the five lower stars around the outside, their "
              "caramel spokes making six clear five-pointed stars in all. "
              "Symmetrical, graphic, orthographic, no perspective. " + AVOID,
              overlay="(none -- this is the mark)"),
        Asset("HERO-6", "Star map -- the two strut lengths",
              "Explainer carousel, instruction booklet cover", "1:1",
              "SCENE: the bare frame only, no panels, on a white gradient, "
              "slightly from above. The honey-caramel SHORT wedges glow very "
              "slightly so the six five-pointed stars stand out clearly "
              "against the tan LONG wedges -- one crown star at the top, five "
              "around the lower wall. " + AVOID,
              overlay=(f"Two lengths only. Short spokes make {lay.stars} "
                       f"stars; long struts do everything else. "
                       f"{lay.short_edges} short lines, {lay.long_edges} long.")),
    ]


def manual_assets(f: Facts, lay: Layout) -> list[Asset]:
    """The frame as a construction-toy instruction manual, step by step."""
    steps = [
        ("The pad and its service port",
         "Only the finished ten-sided pad on its baseplate, the amber "
         "square service port open at its centre, yellow, blue and grey "
         "lines coming up through it and capped."),
        ("The base ring",
         f"The {words(lay.base_edges)} single long tan wedges of the base "
         "ring laid on the pad to make a flat ten-sided ring, flat faces "
         "outward, points toward the centre; the ring's ten corners sit on "
         "the pad's rim."),
        ("The base row -- stars' feet and upright triangles",
         f"Around the ring, {words(lay.rows[5][0])} triangles whose wide "
         "side sits on the ring and whose point rises to where a lower star "
         f"will be centred, alternating with {words(lay.rows[4][0])} "
         "equilateral triangles standing point-up between them. Each "
         "triangle is its own frame of three wedges; where two triangles "
         "touch, their wedges lie back to back."),
        ("The lower stars",
         f"The {words(lay.lower_stars)} lower stars completed: at each "
         "star's centre, five short caramel spokes meet; the star's other "
         "triangles are added around it, the wall now standing a little "
         "over halfway up."),
        ("The middle band",
         f"The {words(lay.rows[1][0])} equilateral triangles that hang "
         "point-down between the lower stars and the crown, closing the "
         "band just below the top."),
        ("The crown",
         f"The crown star at the apex: {words(lay.apex_valence)} short "
         "caramel spokes meeting at one point, closing the frame. The "
         "finished frame shows all six stars clearly."),
        ("The utility column and seal cap",
         "The cyan column lowered through the apex onto the service port, "
         "its base landing on the port and its top landing in the apex "
         "sleeve; the round cyan seal cap clipped on top."),
        ("Panels",
         "Cream triangular panels pressed onto the outside face of each "
         "bay and fixed with four small screws each, working round from the "
         "door; a few still waiting in the callout box."),
        ("The utility panel",
         "A small cyan utility panel cabinet standing on the ground a "
         "step outside the pad, with a neat line running from under the "
         "seal cap down the outside of the dome to it."),
    ]
    out = [Asset(
        "BUILD-0", "Parts inventory -- everything in the set",
        "Instruction booklet page one, Kickstarter 'what's in the kit'", "4:3",
        "SCENE: an instruction-manual inventory page: every part of the "
        "stem cell laid out flat in tidy rows on off-white, grouped by type "
        "-- the long tan wedges together, the short honey-caramel wedges "
        "together, stacks of cream triangular panels, the cyan column in "
        "sections, the round seal cap, small bags of screws and inserts. "
        "Each group a neat block; nothing overlapping.", style="manual",
        overlay=(f"{f.members} wedges · {f.bays} panels · 1 column · 1 seal cap"))]
    for n, (title, what) in enumerate(steps, start=1):
        out.append(Asset(
            f"BUILD-{n}", f"Step {n}: {title}",
            "Instruction booklet / carousel / GIF frame", "4:3",
            f"THIS STEP: {what} " + AVOID, style="manual",
            overlay=f"Step {n} -- {title}"))
    return out


def utility_assets(f: Facts, lay: Layout) -> list[Asset]:
    """The utility core ('the utility wall'), every part of it shown working."""
    def part_list(parts) -> str:
        return "; ".join(f"the {p.name.lower()} -- {PART_VISUALS[p.name]}"
                         for p in parts)

    service_colour = {"power": "bright yellow", "water": "blue",
                      "drain": "dark grey", "air": "white",
                      "structure": "cyan and amber"}
    out = [Asset(
        "UTIL-1", "The utility core, whole -- one column does everything",
        "Kickstarter 'how it works' centrepiece, poster, book plate", "4:5",
        "SCENE: a CUTAWAY of the stem cell -- the front half of the dome and "
        "of the pad removed cleanly down the middle, like a cross-section "
        "display model -- so the whole utility core is visible at once, "
        "labelled only by colour. From the bottom up: under the deck, the "
        "amber water tank and the pad's lines; the amber square service port "
        "in the centre of the deck with three lines rising through it (a "
        "yellow power cord, a blue water pipe, a grey drain pipe); the cyan "
        "column standing on the port with its front cover off, and inside "
        "it, in order of height, the grey drain trap at its foot, the blue "
        "shutoff valve at knee height, the grey electrical sub-panel at "
        "chest height with its row of four breakers, the blue manifold with "
        "four valves and capped stubs, and the yellow lighting line "
        "continuing up to a round light and fan under the apex; at the top "
        "the column lands in the apex sleeve under the cyan seal cap. A "
        "yellow outlet ring runs round the base inside the seam channels "
        "with small outlets between the wedges. From under the seal cap, "
        "one neat bundle of lines runs down the OUTSIDE of the dome to a "
        "small cyan utility panel cabinet standing outside the pad. On the "
        "pad's edge, the amber electrical pedestal with the yellow cord "
        "plugged into it. " + AVOID,
        overlay=("One opening in the pad, one column, one sealed hole in the "
                 f"roof. Column rise {f.column_rise_ft:.1f} ft; pad tank "
                 f"{f.water_tank_gal:.0f} gal."))]
    for n, service in enumerate(seed_model.SERVICES, start=2):
        core = seed_model.core_parts(service)
        pad = seed_model.pad_parts(service)
        prompt = (
            f"SCENE: the same cutaway display model as the whole-core view, "
            f"but only the {service.upper()} parts are in full colour "
            f"({service_colour[service]}); everything else is shown as pale, "
            "semi-transparent ghosted grey so this one system reads clearly "
            "from end to end. "
            + (f"THE DOME OWNER'S {service.upper()} PARTS (cyan hardware): "
               f"{part_list(core)}. " if core else "")
            + (f"THE PAD HOST'S {service.upper()} PARTS (amber hardware): "
               f"{part_list(pad)}. " if pad else "")
            + "Show the path the service takes as one continuous line from "
            "where it enters to where it is used. " + AVOID)
        detail = " | ".join(f"{p.name}: {p.detail}" for p in core + pad)
        out.append(Asset(f"UTIL-{n}", f"The core, {service} only",
                         "Carousel slide, story section, book plate", "4:5",
                         prompt, overlay=detail))
    joints = seed_model.interfaces()
    out.append(Asset(
        "UTIL-7", "Four connections and a lift",
        "Kickstarter 'arriving on a pad' graphic, Dome Park pitch", "16:9",
        "SCENE: a toy crane holding the complete stem-cell dome a hand's "
        "width above its pad, lowering it; the pad below shows exactly "
        f"{words(len(joints))} connection points, each circled with a soft "
        "glow in its colour and each with its mate hanging directly above it "
        "under the dome: the yellow power cord's plug above the amber "
        "pedestal, the blue riser above the blue water stub, the grey drain "
        "stack above the grey drain connection, and the base of the cyan "
        "column above the amber service port. Everything else is already "
        "built. " + AVOID,
        overlay=" | ".join(f"{s}: {what} -- {why}" for s, what, why in joints)))
    by_mount: dict[str, list[str]] = {}
    for m in seed_model.MODULES:
        by_mount.setdefault(m.mount, []).append(_scrub(m.label).lower())
    mounts = "; ".join(f"{MOUNT_WORDS[k]}: {', '.join(v)}"
                       for k, v in by_mount.items())
    out.append(Asset(
        "UTIL-8", "Where every module plugs in",
        "Kickstarter add-ons map, web app, book plate", "16:9",
        "SCENE: the cutaway stem cell as a map of the places a module can "
        "go, each place marked by a small glowing ring in the colour of what "
        "feeds it, with a few modules shown installed as small clean toy "
        f"parts: {mounts}. Show one or two of each kind, installed, "
        "not all of them. " + AVOID,
        overlay="Modules snap on at five places: the column, a utility "
                "panel, a bay panel, the floor, and the apex."))
    out.append(Asset(
        "UTIL-9", "The utility panel, open",
        "Detail post, add-on graphic", "4:5",
        "SCENE: close three-quarter view of one cyan utility panel cabinet "
        "standing on the ground a step outside the pad, its weather lid "
        "hinged open on top: inside, neat quick-connect service tails in "
        "yellow, blue and grey, and a small exhaust fan module mounted in "
        "it. A gasketed pass-through carries a short line from the cabinet "
        "back into one wall bay of the dome. Above, a neat bundle of lines "
        "runs down the outside of the dome from the seal cap to the "
        "cabinet. The dome's wall and the pad's edge fill the background. "
        + AVOID,
        overlay="Noisy, hot and weather-facing kit lives outside -- the "
                "building's weather surface is never cut for it."))
    out.append(Asset(
        "UTIL-10", "The core's parts, laid out",
        "Instruction booklet, Kickstarter core tier", "4:3",
        "SCENE: an inventory page of every part of the utility core laid "
        "out flat and grouped by service colour -- the cyan column sections, "
        "the seal cap and apex sleeve, the yellow cord and inlet, the grey "
        "sub-panel and four breakers, the blue riser, valve, manifold and "
        "capped tails, the grey trap, stack and rubber boot, the white seam "
        "collector -- each group a neat block.", style="manual",
        overlay=f"{len(seed_model.CORE_PARTS)} parts, five services, one column."))
    return out


def pad_assets(f: Facts, lay: Layout) -> list[Asset]:
    """The platform: how it is built, what the host owns, the alternatives."""
    sequence = pad_deck.build_sequence("blocks")
    layers = "; then ".join(PAD_STEP_VISUALS[s.label] for s in sequence)
    kinds = [(k, pad_deck.deck(k)) for k in pad_deck.KINDS]
    host = "; ".join(f"the {p.name.lower()} -- {PART_VISUALS[p.name]}"
                     for p in seed_model.PAD_PARTS)
    out = [
        Asset("PAD-1", "The platform, layer by layer (exploded)",
              "Pad host's pack, Dome Park story, book plate", "4:5",
              "SCENE: the ten-sided pad shown as an EXPLODED stack, each "
              "layer floating a hand's width above the one below, all "
              f"aligned, bottom to top: {layers}. The stem-cell dome floats "
              "above the whole stack, ghosted pale, to show what lands on "
              "it. " + AVOID, truth=False,
              overlay=" -> ".join(f"{s.number}. {s.label} ({s.detail})"
                                  for s in sequence)),
        Asset("PAD-2", "The host's pad, ready for a dome",
              "Pad host's pack, Dome Park landing page", "16:9",
              "SCENE: the finished ten-sided pad with NO dome on it, on a "
              "green baseplate, a small cutaway at one edge showing the "
              f"space beneath. Everything that belongs to the host, in amber: "
              f"{host}. The service port's lines are capped, waiting. "
              + AVOID, truth=False,
              overlay=(f"Built once by the host, kept when a dome leaves. "
                       f"Pad {f.pad_across_ft:.1f} ft across.")),
        Asset("PAD-3", "Five ways to make a pad",
              "Pad host's pack comparison, book plate", "21:9",
              "SCENE: five small ten-sided pads in a row on one long green "
              "baseplate, each cut away at the front to show its build, "
              "left to right: "
              + "; ".join(DECK_VISUALS[k] for k, _ in kinds)
              + ". Same size, same camera, same light. " + AVOID, truth=False,
              overlay=" | ".join(f"{d.label}: {usd(d.cost)}" for _, d in kinds)),
        Asset("PAD-4", "The dome lands",
              "Launch video keyframe, Dome Park hero", "16:9",
              "SCENE: a toy crane lowering the finished stem cell onto its "
              "pad, the dome's ten base corners lined up exactly over the "
              "pad's ten-sided rim, the cyan column's foot above the amber "
              "service port, a toy figure guiding it with a tag line. " + AVOID),
    ]
    return out


def layer_assets(f: Facts, lay: Layout) -> list[Asset]:
    """The shell: the stack of hats, what each layer does, how it grows."""
    limit = soft_shell.cavity_limit()
    return [
        Asset("LAYER-1", "The layers of the dome, exploded",
              "Kickstarter 'stacking hats', book plate, carousel", "4:5",
              "SCENE: the dome's envelope as an EXPLODED stack of hemispheres "
              "floating one above the other, each a little larger than the "
              "one inside it, all centred on the same axis, from the inside "
              "out: (a) the wedge frame; (b) the cream wood panels on its "
              "outside face; (c) ONE continuous translucent white breather "
              "sheet with no seams, which lets vapour out; (d) three quilted "
              "layers of recycled fabric in bright patchwork colours -- denim "
              "blue, flannel red, mustard, sage, cream -- each one a size up "
              "from the last and stitched along the lines of the triangles; "
              "(e) a thin gap held open by a few webbing straps; (f) the "
              "glossy translucent smoke-blue rain cap, strapped at the ten "
              "base corners -- the only watertight layer. " + AVOID,
              overlay="Frame · panels · breather · quilts · vent gap · cap. "
                      "Only the cap is waterproof."),
        Asset("LAYER-2", "The cap is a bag -- it grows",
              "Explainer carousel", "21:9",
              "SCENE: the same dome three times in a row on one baseplate, "
              "same frame, same camera: left, panels only; middle, one quilt "
              "and a snug cap; right, four quilts and a visibly larger, "
              "puffier cap. A thin dotted line traces the SAME base ring "
              "under all three, proving the frame never changed. " + AVOID,
              overlay=f"Each layer needs a bigger cap. A rigid shell would "
                      f"cap the building at {limit} layers."),
        Asset("LAYER-3", "Through the wall -- a section",
              "Story section on insulation and moisture", "3:2",
              "SCENE: a clean cutaway slice through one wall, shown like a "
              "cut-through display piece: two wedge cross-sections (triangles, "
              "points inward) at the sides, the cream panel on their outside "
              "face with a small screw into a threaded insert, the white "
              "breather over it, three patchwork quilt layers, the gap held by "
              "a strap, the smoke-blue cap outside. A small blue droplet runs "
              "down the outside of the cap and off the hem; a small white "
              "arrow of vapour passes outward through the breather and quilts "
              "into the vented gap. " + AVOID, truth=False,
              overlay="Wet outside the cap, dry under it: vapour escapes, "
                      "rain never gets in."),
        Asset("LAYER-4", "The hard-shell alternative, in slices",
              "Story section comparing shells", "16:9",
              "SCENE: a moulded rigid shell for the same dome, split into four "
              "equal quarter-slices fanned out on the baseplate like orange "
              "peel around the dome, each slice's edges showing an S-shaped "
              "interlocking lip with a black gasket in its return, one slice "
              "hanging from a toy crane hook. Four toy figures stand by the "
              "slices -- one slice is a four-person or crane lift. " + AVOID,
              overlay="Four slices, S-lip seams, watertight by shape. A "
                      "quarter slice is four people or the crane, not two."),
    ]


def seam_assets(f: Facts, lay: Layout) -> list[Asset]:
    duct = seed_model.seam_duct()
    return [
        Asset("SEAM-1", "The seam network lit up",
              "Hero explainer: the seam does four jobs", "16:9",
              "SCENE: the dome with its panels shown faintly ghosted so the "
              "frame is visible, and every seam channel -- the V-shaped groove "
              "between each pair of back-to-back wedges -- glowing soft white, "
              "so the channels read as one connected network reaching every "
              f"junction, {words(lay.seams)} glowing seams meeting at the "
              f"{words(f.vertices)} junctions. At the base a small white "
              "collector box gathers them. " + AVOID,
              overlay=(f"{duct.length_ft:,.0f} ft of channel reaching all "
                       f"{duct.vertices} junctions -- a duct, a conduit, a "
                       "drain and a joint.")),
        Asset("SEAM-2", "What the seam is",
              "Close explainer, book plate", "3:2",
              "SCENE: a cut-through display of two wedges lying side by side, "
              "back to back, their triangular ends toward the camera: the flat "
              "faces together form a continuous flat outer surface under a "
              "cream panel, and below that, where their angled sides part, a "
              "clean V-shaped channel opens toward the inside. A yellow cable "
              "lies in the channel, showing where the lines always are. "
              + AVOID, truth=False,
              overlay="The gap everyone machines away, kept on purpose: you "
                      "always know where the lines are."),
        Asset("SEAM-3", "Rain into the tank",
              "Water story, pad host's pack", "16:9",
              "SCENE: a gentle rain of toy blue droplets on the dome; along "
              "the seams, soft blue arrows show water gathering in the "
              "channels, running down to the base and into the amber tank "
              "under the pad (shown through a cutaway). " + AVOID,
              overlay=(f"About {duct.gallons_per_year:,.0f} gal a year could "
                       "reach the pad's tank. An experiment being run, not a "
                       "result being reported.")),
    ]


def rig_assets(f: Facts, lay: Layout) -> list[Asset]:
    return [
        Asset("MAST-1", "The mast inside the column",
              "Upgrade path story, book plate", "4:5",
              "SCENE: a cutaway of the dome showing a steel mast standing "
              "inside the cyan utility column from the base flange on the "
              "service port up through the apex, clad in timber, with a steel "
              "lifting ring just under the seal cap. The services still run "
              "beside it inside the column. " + AVOID,
              overlay="The services and the structure share one penetration."),
        Asset("FLOOR-1", "The dome's own floor (the upgrade)",
              "Upgrade path story", "4:5",
              "SCENE: the dome's own floor shown EXPLODED under the frame: a "
              "steel hub ring clamping the mast at the centre, ten straight "
              "steel spokes running from the hub to the ten corners of the "
              "base ring, timber plank tiles decking over the spokes, and an "
              "edge rail round the rim. It goes with the dome; the host's pad "
              "stays. " + AVOID,
              overlay="The pad is the host's. This floor is yours, and it "
                      "travels with the dome."),
        Asset("FLOAT-1", "The floating dome",
              "Design-possibility slide -- label it as a possibility", "16:9",
              "SCENE: the stem cell hanging clear of the ground between three "
              "tall brick-built trees, from three steel cables that run from "
              "saddles on the trunks to a hanger on the mast's lifting ring "
              "at the apex; a small brake winch at the foot of one tree. The "
              "dome's own floor is under it. Calm, a little magical. " + AVOID,
              overlay="A design possibility, not a tested product: every "
                      "load here is an engineer's number, not ours."),
    ]


def world_assets(f: Facts, lay: Layout) -> list[Asset]:
    """The wood it comes from, and the network it lives in."""
    return [
        Asset("WOOD-1", "One log, two ways",
              "Story section: why wedges", "3:2",
              "SCENE: two identical round log sections side by side on a "
              "display plinth. Left: split radially into wedge slices like an "
              "orange, nearly all of it used. Right: a few rectangular boards "
              "cut from it, the curved offcuts around them shaded grey as "
              "waste. Same log, same size. " + AVOID, truth=False,
              overlay=(f"Wedges keep {f.wedge_vs_milled:.2f}x the wood of "
                       "boards from one log. The frame uses more pieces, so "
                       f"it takes {f.trees_vs_mitred:.0%} of the trees a "
                       "mitred dome would -- it wins by the difference.")),
        Asset("WOOD-2", "From the buyer's own trees",
              "Kit (bring your own trees) tier, story", "16:9",
              "SCENE: a brick-built forest clearing: a felled pine log in the "
              "foreground, split into wedges fanned out on the ground; behind "
              "it, the same wedges sorted into two neat stacks, tan long and "
              "caramel short; behind those, the frame rising on its pad. "
              "The story reads left to right, log to building. " + AVOID),
        Asset("PARK-1", "The dome park",
              "Dome Park / network story, web-app network page", "21:9",
              "SCENE: a gentle toy landscape seen from a low hill: several "
              "ten-sided pads spaced apart among brick-built trees, some with "
              "a stem-cell dome standing on them (each dome's hardware cyan), "
              "some empty and waiting with capped amber service ports; a "
              "shared amber service line runs along a path to each pad; a toy "
              "crane at one pad lifting a dome on. Toy figures at a few "
              "doors. " + AVOID,
              overlay="Amber is the host's. Cyan is the dome owner's. A dome "
                      "arrives with four connections and a lift."),
        Asset("PARK-2", "The quilt network",
              "Quilter audience post, quilter tier", "1:1",
              "SCENE: a long workshop table seen from above, toy figures "
              "sewing a big patchwork quilt layer of bright recycled fabric, "
              "a triangular template on the table, and at the end of the "
              "table a small dome wearing a finished quilt under its "
              "smoke-blue cap. " + AVOID,
              overlay=f"One layer is about {f.shirts_per_layer} t-shirts."),
    ]


def fitout_assets(f: Facts, lay: Layout) -> list[Asset]:
    out = []
    for fit in seed_model.fitouts():
        out.append(Asset(
            f"FIT-{fit.key}", fit.label,
            "Carousel 'one frame, every building', Kickstarter gallery, web app",
            "4:5",
            f"THIS FIT-OUT: the {fit.label.lower()}, {SHAPES[fit.shape]}, "
            f"with {_panel_mix(fit.panels)}. SCENE: the dome "
            f"{FITOUT_SCENES[fit.key]}. The frame is the same stem cell as "
            "every other image; only the panels and modules differ. " + AVOID,
            overlay=f"{fit.label.upper()} -- {fit.blurb}"))
    out.append(Asset(
        "FIT-ALL", "Same frame, different panels",
        "Story section: the stem-cell idea; GIF source", "21:9",
        "SCENE: three identical domes in a row on one baseplate, same frame, "
        "same camera, same light. Left: every bay a plain cream panel. "
        "Middle: pale-blue windows, skylights and a door -- a small house. "
        "Right: one wide roll-up door across three base bays, skylights and "
        "louvres -- a garage. The frames are visibly identical; only the "
        "panels change. " + AVOID,
        overlay="The frame never changes. The panels decide what the "
                "building is."))
    return out


def panel_assets(f: Facts, lay: Layout) -> list[Asset]:
    return [
        Asset(f"PANEL-{p.key}", p.label,
              "Panel catalogue icon set: web app, add-ons, stickers", "1:1",
              f"SUBJECT: one triangle, point up, representing a dome bay "
              f"fitted with a {p.label.lower()} -- {p.note}. Draw only what "
              "makes this panel different from a plain closed triangle.",
              style="icon", truth=False,
              overlay=f"{p.label} -- " + (usd(p.usd) if p.usd else "ships with every dome"))
        for p in seed_model.PANELS
    ]


def tier_assets(f: Facts, lay: Layout) -> list[Asset]:
    out = [Asset(
        f"TIER-{n}", tier.label,
        "Kickstarter reward card image, 'pick your reward' carousel",
        "3:2 (reward card), then 1:1",
        f"SCENE: {TIER_SCENES[tier.key]}, all rendered as parts from the "
        "same building-brick set. Leave the top third quiet so a title can "
        "be set over it. " + AVOID, truth=False,
        overlay=f"{tier.label} -- {usd(tier.pledge)}. {tier.why}.")
        for n, tier in enumerate(kickstarter.tiers(), start=1)]
    out.append(Asset(
        "TIER-FRAME", "Reward-card frame (one template, every tier)",
        "Canva/Figma template: drop each TIER image in", "3:2",
        "SUBJECT: an empty card template: a thin warm-amber triangular corner "
        "motif top-left echoing one dome bay, a plain charcoal band along the "
        "bottom for a title and a price, the rest empty for a picture.",
        style="icon", truth=False, overlay="(template)"))
    return out


def goal_assets(f: Facts, lay: Layout) -> list[Asset]:
    out = [Asset(
        f"GOAL-{line.key}", line.what,
        "Goal breakdown: one spot illustration per line", "1:1",
        f"SUBJECT: {GOAL_SCENES[line.key]}, as a small toy-set vignette, "
        "centred, with plenty of empty background.", truth=False,
        overlay=f"{line.what} -- {usd(line.usd)}. {line.why}.")
        for line in kickstarter.goal_lines()]
    out.append(Asset(
        "GOAL-BG", "Goal chart backdrop",
        "Behind the goal bar chart, drawn from kickstarter.goal_lines()", "3:2",
        "SUBJECT: a very quiet background: pale gradient with the faint "
        "outline of the dome in the lower right corner, faded to almost "
        "nothing. Empty space for a chart.", truth=False,
        overlay=f"The goal is the sum of the list: {usd(f.goal)}."))
    return out


def social_assets(f: Facts, lay: Layout) -> list[Asset]:
    series = [
        ("SOC-1", "Coming soon -- the silhouette", "9:16",
         "SCENE: the dome as a dark faceted silhouette against a pale dawn "
         "gradient, only the rim of each flat panel catching light.",
         "Something is growing. Follow for launch day."),
        ("SOC-2", "Coming soon -- the wedge", "4:5",
         "SCENE: a single tan wedge standing on end on a charcoal plinth, "
         "its triangular end toward the camera, rim-lit. Nothing else.",
         "One cut changes the whole building."),
        ("SOC-3", "Launch day", "1:1 and 9:16",
         "SCENE: the attached hero image's model and setting, with a long "
         "ribbon of warm light crossing the baseplate toward the open door.",
         "We're live on Kickstarter. Link in bio."),
        ("SOC-4", "Milestone -- a quarter funded", "1:1",
         "SCENE: the frame with a quarter of its bays panelled, working round "
         "from the door, the rest open frame.", "A quarter of the way there."),
        ("SOC-5", "Milestone -- halfway", "1:1",
         "SCENE: the same frame with half its bays panelled.", "Halfway."),
        ("SOC-6", "Milestone -- three quarters", "1:1",
         "SCENE: the same frame with three quarters of its bays panelled.",
         "Three quarters. The last bays are yours."),
        ("SOC-7", "Funded", "1:1 and 9:16",
         "SCENE: every bay panelled, seal cap on, warm light inside, a small "
         "group of toy figures (backs to camera) looking at it at golden hour.",
         f"Funded. {usd(f.goal)} of tooling, line by line -- thank you."),
        ("SOC-8", "Last forty-eight hours", "9:16",
         "SCENE: the dome at dusk, its long shadow across the baseplate like "
         "the hand of a clock, one warm window.", "48 hours left."),
        ("SOC-9", "Backer update header", "16:9",
         "SCENE: close three-quarter view of the doorway, a pair of toy work "
         "gloves and a rolled drawing on the threshold.", "Backer update"),
        ("SOC-10", "Lumen explains", "9:16",
         f"SCENE: {MASCOT} Lumen floats beside the dome, one tentacle "
         "pointing at a seam as if about to explain it.",
         "Lumen says: the seam is a channel. Ask why in the comments."),
    ]
    out = [Asset(i, t, "Instagram / TikTok / Facebook / X launch series", a,
                 p + " " + AVOID, overlay=o) for i, t, a, p, o in series]
    for i, t, a in (("CH-YT", "YouTube channel banner", "21:9"),
                    ("CH-FB", "Facebook page cover", "2.7:1"),
                    ("CH-X", "X / Twitter header", "3:1")):
        out.append(Asset(
            i, t, "Channel art", a,
            "SCENE: a very wide calm toy landscape of green baseplate and a "
            "far line of brick-built pines under a soft gradient sky; the "
            "dome small and exactly centred, nothing important near the "
            "edges, which will be cropped. " + AVOID,
            overlay="Stem Cell Dome -- one frame, any building"))
    out.append(Asset(
        "CH-AVATAR", "Profile picture", "Every platform's avatar", "1:1",
        "SCENE: the attached top-down plan image, simplified until it reads "
        "at thumbnail size: six caramel stars on tan inside a charcoal circle.",
        truth=False, overlay="(none)"))
    for n, (title, idea) in enumerate((
        ("Thumbnail -- the question", "the dome in the left third, clean sky "
         "on the right for a large headline"),
        ("Thumbnail -- the comparison", "the dome on the left, a plain boxy "
         "brick shed of the same floor area on the right, same light"),
        ("Thumbnail -- the hands", "two toy hands holding up a single "
         "triangular wedge toward the camera, the dome soft behind"),
    ), start=1):
        out.append(Asset(
            f"YT-{n}", title, "YouTube video thumbnail", "16:9",
            f"SCENE: {idea}. High contrast, readable small. " + AVOID,
            overlay="Headline set in type: three to five words, e.g. 'WHY WEDGES?'"))
    return out


def web_assets(f: Facts, lay: Layout) -> list[Asset]:
    return [
        Asset("WEB-OG", "Share image for the web app",
              "Open Graph / link previews", "1.91:1",
              "SCENE: the attached hero image's model on the left two-thirds, "
              "the right third a calm empty charcoal band for a title. " + AVOID,
              overlay="Free book: The 40 Hour Cabin -- enter your email"),
        Asset("WEB-BOOK", "Book mockup", "Download page, email capture", "4:5",
              "SCENE: a printed paperback lying on a workbench beside a single "
              "split wedge and a pencil; the cover is BLANK charcoal (the real "
              "cover is placed on it afterwards), soft light from the left.",
              truth=False, overlay="(place the real cover on the blank book)"),
        Asset("WEB-LINKS", "Links-page background", "Link-in-bio page", "9:16",
              "SCENE: the dome small in the lower third at blue hour, a tall "
              "empty indigo gradient above it for a column of buttons. " + AVOID,
              overlay="(buttons go here)"),
        Asset("WEB-NETWORK", "Dome network header", "'Find the network' page",
              "21:9",
              "SCENE: the dome park seen from far off: pads and domes spaced "
              "across a toy landscape, thin dotted paths of light linking them "
              "like a map. Quiet, hopeful. " + AVOID,
              overlay="The dome network: hosts, owners, quilters, builders."),
        Asset("WEB-MARK", "Logo mark", "Favicon, app icon, watermark", "1:1",
              "SUBJECT: the top-down plan of a 2V dome reduced to a single-"
              "weight line pattern inside a circle -- a central five-pointed "
              "star ringed by five more -- with the central star filled warm "
              "amber. Perfectly symmetrical.", style="icon", truth=False,
              overlay="(none)"),
    ]


def motion_assets(f: Facts, lay: Layout) -> list[Asset]:
    shots = [
        ("MOTION-1", "The frame assembles",
         "Stop-motion style, like a brick set building itself: on the empty "
         "pad, the base ring clicks together, then the base row, the lower "
         "stars, the middle band and finally the crown star, each piece "
         "dropping in with a tiny bounce. Locked three-quarter camera."),
        ("MOTION-2", "Panels swap -- the stem cell",
         "Locked camera on the finished model. Panels pop out and new ones "
         "click in: a house (windows, a door, skylights) becomes a workshop "
         "(skylights, louvres, solar) becomes a garage (one wide roll-up "
         "door). The frame never moves."),
        ("MOTION-3", "The log opens",
         "A round log's end fills the frame, splits into pie-slice wedges "
         "that drift apart and turn into the struts of a dome forming behind."),
        ("MOTION-4", "The core lights up",
         "Cutaway model: the power line glows yellow from the pedestal up the "
         "column to the light at the apex, then the water line glows blue from "
         "the tank to the manifold, then the drain grey back down."),
        ("MOTION-5", "Hats on",
         "The dome dresses: breather sheet settles over it, three patchwork "
         "quilts drop on one after another, then the smoke-blue cap pulls "
         "down and the straps snap to the ten base corners."),
    ]
    return [Asset(i, t, "Veo / Gemini video: Reels, TikTok, Shorts loops, GIFs",
                  "9:16, six to eight seconds", f"MOTION: {m} " + AVOID,
                  overlay="(no text in the video; captions added in the editor)")
            for i, t, m in shots]


SECTIONS = (
    ("1. The hero -- the stem cell", hero_assets),
    ("2. The frame, step by step -- an instruction manual", manual_assets),
    ("2b. Schematics and multi-view sheets -- every need-to-know concept",
     lambda f, lay: __import__("campaign_schematics").schematic_assets(f, lay)),
    ("3. The utility core -- every service, shown working", utility_assets),
    ("4. The platform -- the host's pad", pad_assets),
    ("5. The layers -- frame, panels, breather, quilts, cap", layer_assets),
    ("6. The seam channel", seam_assets),
    ("7. Mast, floor and the floating rig", rig_assets),
    ("8. The wood and the network", world_assets),
    ("9. One frame, every building -- a picture per fit-out", fitout_assets),
    ("10. The panel catalogue -- icon set", panel_assets),
    ("11. Reward graphics -- one per Kickstarter tier", tier_assets),
    ("12. Where the money goes -- one per goal line", goal_assets),
    ("13. Social launch series, channel art, thumbnails", social_assets),
    ("14. Book download site and web app", web_assets),
    ("15. Motion -- short video prompts", motion_assets),
)


def all_assets(f: Facts | None = None, lay: Layout | None = None
               ) -> list[tuple[str, list[Asset]]]:
    f = f or facts()
    lay = lay or layout()
    return [(title, build(f, lay)) for title, build in SECTIONS]


def full_prompt(asset: Asset, f: Facts | None = None, lay: Layout | None = None) -> str:
    head = dome_truth(f or facts(), lay or layout()) + " " if asset.truth and asset.style != "icon" else ""
    style = _schematic_style() if asset.style == "schematic" else STYLES[asset.style]
    return f"{head}{asset.prompt} {style}"


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

_ALLOWED = re.compile(r"2V|FFB13E")
_BANNED = ("frankendome", "revolutionary", "game changer", "game-changer",
           "no mitre", "two people can carry")


def validate_prompts() -> list[str]:
    f, lay = facts(), layout()
    problems: list[str] = []
    geo = seed_model.seed_geometry()
    if lay.rows != EXPECTED_ROWS:
        problems.append(f"the mesh's rows changed: {lay.rows} -- rewrite dome_truth")
    if lay.stars != 6 or lay.equilateral != dict(f.face_classes).get("AAA"):
        problems.append("stars/equilateral count disagrees with seed_geometry")
    if lay.seams != f.seams or 2 * lay.seams + lay.base_edges != f.members:
        problems.append("seam/member arithmetic disagrees with seed_geometry")
    if lay.base_corners != f.base_sides or geo.vertex_count != f.vertices:
        problems.append("base ring disagrees with seed_geometry")
    seen: set[str] = set()
    for _, assets in all_assets(f, lay):
        for asset in assets:
            if asset.id in seen:
                problems.append(f"{asset.id}: duplicate id")
            seen.add(asset.id)
            text = full_prompt(asset, f, lay)
            body = _ALLOWED.sub("", text)
            if re.search(r"\d", body):
                digits = sorted(set(re.findall(r"\S*\d\S*", body)))
                problems.append(f"{asset.id}: digits in the image prompt {digits}")
            low = (text + asset.overlay).lower()
            problems += [f"{asset.id}: banned phrase {p!r}" for p in _BANNED if p in low]
    missing = [t.key for t in kickstarter.tiers() if t.key not in TIER_SCENES]
    missing += [x.key for x in seed_model.fitouts() if x.key not in FITOUT_SCENES]
    missing += [g.key for g in kickstarter.goal_lines() if g.key not in GOAL_SCENES]
    missing += [p.name for p in seed_model.CORE_PARTS + seed_model.PAD_PARTS
                if p.name not in PART_VISUALS]
    missing += [s.label for s in pad_deck.build_sequence("blocks")
                if s.label not in PAD_STEP_VISUALS]
    missing += [k for k in pad_deck.KINDS if k not in DECK_VISUALS]
    missing += [m.mount for m in seed_model.MODULES if m.mount not in MOUNT_WORDS]
    problems += [f"no picture written for {key!r}" for key in dict.fromkeys(missing)]
    import campaign_schematics
    problems += campaign_schematics.check_view_geometry(campaign_schematics.view_geometry())
    return problems


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def render() -> str:
    f, lay = facts(), layout()
    sections = all_assets(f, lay)
    count = sum(len(a) for _, a in sections)
    out = [
        "# Stem-cell dome -- campaign image prompts",
        "",
        f"Generated {date.today().isoformat()} by `campaign_prompts.py` from "
        "`seed_model`, `kickstarter`, `pad_deck`, `soft_shell` and the "
        "films' own 2V mesh. **Do not edit by hand** -- change the model or "
        "the scenes in the script and regenerate.",
        "",
        f"{count} assets. Each block is one paste into Gemini: copy the "
        "**Prompt** exactly -- it is long on purpose. The first half is the "
        "dome described row by row, so the model cannot improvise a "
        "different building; the last half is the building-brick style and "
        "its colour key, identical in every prompt so the whole campaign "
        "looks like one set. The **Overlay** line is set in type afterwards "
        "(Canva, Figma, the web app): image models garble figures, so no "
        "prompt contains a number, and every number in an overlay is the "
        "model's.",
        "",
        "## How to get consistent pictures",
        "",
        "1. **Generate HERO-1 first** and keep regenerating until the frame "
        "is right: six stars, flat faces out, two wedges back to back on "
        "every seam, cyan column and cap. Everything else is matched to it.",
        "2. **Attach HERO-1 as a reference** to every later prompt and add: "
        "*'same model, same parts, same colours and lighting as the "
        "reference.'* A prompt that says *the attached hero image* needs "
        "HERO-1; *the attached top-down plan image* needs HERO-5.",
        "3. **If Gemini gets the geometry wrong,** reply with just the part "
        "that is wrong, quoted from section (TWO) or (FOUR) of the prompt -- "
        "e.g. *'the short caramel struts must be the spokes of six "
        "five-pointed stars, one at the apex and five around the lower "
        "wall'*. Short corrections work better than re-pasting everything.",
        "4. **Re-cropping:** *'same image, recomposed to 9:16, model centred "
        "in the upper two-thirds.'*",
        "5. **Styles:** *brick* = box-art toy model (the default); *manual* "
        "= instruction-booklet page; *schematic* = technical drawing (orthographic "
        "views, sections, blank dimension lines -- label them afterwards; for a "
        "blueprint look add *'white line work on blueprint blue'*); *photo* = full-size photograph "
        "(HERO-1-PHOTO only); *icon* = flat vector set.",
        "6. **Kickstarter disclosure.** Kickstarter asks creators to disclose "
        "AI-generated images. Caption these as *concept illustration*, use "
        "photographs of the real prototype wherever the page shows what a "
        "backer will receive, and check the current rules on renderings "
        "before launch.",
        "",
        "## The layout the prompts describe (read from the mesh)",
        "",
        "| row, top to bottom | triangles | kind |",
        "|---|---|---|",
        f"| crown star | {lay.rows[0][0]} | isosceles, points meet at the apex |",
        f"| under the crown | {lay.rows[1][0]} | equilateral, point down |",
        f"| lower stars, upper flanks | {lay.rows[2][0]} | isosceles |",
        f"| lower stars, lower flanks | {lay.rows[3][0]} | isosceles |",
        f"| base row, between stars | {lay.rows[4][0]} | equilateral, point up |",
        f"| base row, stars' feet | {lay.rows[5][0]} | isosceles, point up |",
        "",
        f"{lay.stars} stars (five-way junctions) · {lay.six_way} six-way "
        f"junctions · {lay.base_corners} base corners · {lay.short_edges} short "
        f"lines (all star spokes) · {lay.long_edges} long lines · long is "
        f"{lay.long_over_short:.3f}x short · {lay.seams} doubled seams + "
        f"{lay.base_edges} single base members = {f.members} wedges.",
        "",
        "## The figures overlays may use",
        "",
        "| figure | value | from |",
        "|---|---|---|",
        f"| across / tall | {f.across_ft:.2f} ft / {f.tall_ft:.2f} ft | `seed_model.seed_geometry()` |",
        f"| floor | {f.floor_sqft:,.1f} sq ft | `seed_geometry().floor_decagon_sqft` |",
        f"| bays / wedges / junctions | {f.bays} / {f.members} / {f.vertices} | `seed_geometry()` |",
        f"| wedge section | {f.member_width_in:.2f} in face x {f.member_depth_in:.0f} in deep | `seed_geometry()` |",
        f"| stem cell, what you pay | {usd(f.price)} | `kickstarter.cost_stack().price` |",
        f"| ... cost to build / our profit | {usd(f.built)} / {usd(f.margin)} | `cost_stack()` |",
        f"| ... per sq ft of floor | ${f.per_sqft:,.2f} | `cost_stack().per_sqft` |",
        f"| campaign goal | {usd(f.goal)} | `kickstarter.goal()` |",
        f"| pad across | {f.pad_across_ft:.1f} ft | `pad_deck.pad_diameter_ft()` |",
        f"| column rise | {f.column_rise_ft:.1f} ft | `seed_model.column_rise_ft()` |",
        f"| wedges vs boards, one log | {f.wedge_vs_milled:.2f}x | `seed_model.harvest()` |",
        f"| trees vs a mitred dome | {f.trees_vs_mitred:.0%} | `seed_model.trees_against_mitred()` |",
        f"| t-shirts per quilted layer | {f.shirts_per_layer} | `kickstarter.quilt_economics()` |",
        "",
        "## Platform sizes (the platforms' published specs -- re-check before upload)",
        "",
        "| ratio | pixels | used for |",
        "|---|---|---|",
    ]
    out += [f"| {r} | {px} | {use} |" for r, px, use in PLATFORM_SPECS]
    for title, assets in sections:
        out += ["", f"## {title}", ""]
        for a in assets:
            out += [
                f"### {a.id} -- {a.title}",
                "",
                f"*Use:* {a.use} · *Ratio:* {a.aspect} · *Style:* {a.style}",
                "",
                "**Prompt**",
                "",
                "```",
                full_prompt(a, f, lay),
                "```",
                "",
            ]
            if a.overlay:
                out += [f"**Overlay:** {a.overlay}", ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="run the checks and write nothing")
    args = parser.parse_args(argv)
    problems = validate_prompts()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    if args.check:
        print("campaign prompts: ok")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    path = next_version_path(OUT)
    path.write_text(render(), encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
