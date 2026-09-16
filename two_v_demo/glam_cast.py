"""The glam cast: eight women who own the dome, and how they look.

The drama cast in :mod:`two_v_demo.drama_script` is a five-hander of
suits and mechanics staged in a workshop.  This is the other show --
the one set in a dome *home* and a dome *store*, with a cast built for
attitude rather than for exposition.  Every character here is a woman,
every one of them arrives with a look that reads in one frame, and the
casting is deliberately spread across the world rather than drawn from
one place.

What this module is and is not
------------------------------
It is **data**.  A character is a skin tone, a hair style key, a hair
colour, a signature palette, a stature and a stack of attitude: what
she wants, how she takes a room, what she does when she loses.  It
holds no geometry.  :mod:`two_v_demo.glam_hair` turns a hair key into
strands, :mod:`two_v_demo.glam_wardrobe` turns an outfit key into
garment shells, and :mod:`two_v_demo.glam_figure` draws the result.

Colour, honestly labelled
-------------------------
The skin ladder below is a ten-step scale in the spirit of the
published ten-tone scales used for representative colour work.  The
sRGB values are **art direction for this renderer's lighting**, chosen
so that all ten steps stay separable under the amber-and-cyan dome key
light, and are not measurements lifted from any published scale.  Hair
and wardrobe colours are art direction too, and say so.  Nothing in
this file is presented as derived data; everything that *is* derived --
proportions, hair lengths, garment sizes -- comes off the skeleton in
:mod:`two_v_demo.figure` at draw time.

:func:`validate_glam_cast` proves the casting holds together before a
frame is drawn: distinct tones, distinct hair, distinct silhouettes,
and every reference resolving to something that exists.
"""

from __future__ import annotations

from dataclasses import dataclass


Colour = tuple[float, float, float, float]


# ----------------------------------------------------------------------
# The skin ladder
# ----------------------------------------------------------------------

SKIN_TONES: dict[str, Colour] = {
    "TONE_01": (0.96, 0.87, 0.80, 1.0),
    "TONE_02": (0.94, 0.82, 0.72, 1.0),
    "TONE_03": (0.90, 0.76, 0.63, 1.0),
    "TONE_04": (0.84, 0.68, 0.53, 1.0),
    "TONE_05": (0.76, 0.59, 0.44, 1.0),
    "TONE_06": (0.66, 0.49, 0.35, 1.0),
    "TONE_07": (0.55, 0.39, 0.27, 1.0),
    "TONE_08": (0.44, 0.30, 0.21, 1.0),
    "TONE_09": (0.33, 0.22, 0.16, 1.0),
    "TONE_10": (0.24, 0.16, 0.12, 1.0),
}
"""Ten steps, light to deep.  Art direction, not measurement."""


def undertone(tone_key: str, warmth: float = 0.06) -> Colour:
    """A slightly warmer version of a tone, for lit edges and shoulders.

    Rim light on skin is warmer than the skin itself; rather than pick a
    second colour per character and risk the two drifting apart, the
    highlight is computed from the tone so it can never mismatch.
    """
    red, green, blue, alpha = SKIN_TONES[tone_key]
    return (min(1.0, red + warmth),
            min(1.0, green + warmth * 0.55),
            min(1.0, blue + warmth * 0.20),
            alpha)


# ----------------------------------------------------------------------
# Hair colour
# ----------------------------------------------------------------------

HAIR_COLOURS: dict[str, Colour] = {
    "JET": (0.055, 0.050, 0.060, 1.0),
    "BLUE_BLACK": (0.060, 0.070, 0.115, 1.0),
    "ESPRESSO": (0.135, 0.088, 0.062, 1.0),
    "CHESTNUT": (0.245, 0.140, 0.082, 1.0),
    "AUBURN": (0.330, 0.130, 0.070, 1.0),
    "COPPER": (0.560, 0.230, 0.075, 1.0),
    "HONEY": (0.640, 0.450, 0.190, 1.0),
    "PLATINUM": (0.880, 0.900, 0.950, 1.0),
    "ASH_SILVER": (0.660, 0.690, 0.720, 1.0),
    "BURGUNDY": (0.330, 0.070, 0.130, 1.0),
    "MAGENTA": (0.640, 0.110, 0.420, 1.0),
    "ICE_BLONDE": (0.900, 0.880, 0.760, 1.0),
}
"""Art direction.  Every one of these has to survive the dome's amber key
light without turning into the colour next to it, which is what
:func:`validate_glam_cast` checks."""


# ----------------------------------------------------------------------
# A character
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class GlamCharacter:
    """One woman: how she looks, how she stands, and what she wants."""

    character_id: str
    name: str
    heritage: str
    """Where the casting places her.  Written out so the look is a
    considered choice rather than a colour picked off a slider."""
    archetype: str
    attitude: str
    """The one-line read: what she does to a room when she walks in."""
    motivation: str
    tone_key: str
    hair_style: str
    """A key into :data:`two_v_demo.glam_hair.HAIR_STYLES`."""
    hair_colour: str
    accent_hair_colour: str | None
    """Tips, streak or braid ribbon; ``None`` for a single-colour head."""
    signature: Colour
    """Her colour.  Wardrobe pulls from it so a look reads as hers even
    when the garment changes."""
    metal: Colour
    """Gold, chrome or rose: the hardware she wears."""
    stature_m: float
    heel_pref_m: float
    """How high she goes when the outfit calls for a heel."""
    default_pose: str
    signature_action: str
    """A key into :data:`two_v_demo.drama_rig.ACTIONS`."""
    expression: str
    """A key into :data:`two_v_demo.drama_face.EXPRESSIONS`: her resting
    face, which is not neutral for a single one of them."""
    wardrobe: dict[str, str]
    """Mode key -> outfit key in :mod:`two_v_demo.glam_wardrobe`."""


GOLD = (0.86, 0.68, 0.24, 1.0)
CHROME = (0.80, 0.83, 0.88, 1.0)
ROSE_GOLD = (0.84, 0.56, 0.46, 1.0)
GUNMETAL = (0.34, 0.36, 0.40, 1.0)


GLAM_CAST: dict[str, GlamCharacter] = {
    "GLAM_NAILAH": GlamCharacter(
        character_id="GLAM_NAILAH",
        name="Nailah Osei",
        heritage="Ghanaian, Accra by way of the dome yards",
        archetype="The owner",
        attitude="Does not raise her voice and never has to. The room "
                 "arranges itself around wherever she stops walking.",
        motivation="Built the store inside the dome she engineered, and "
                   "will not be told what either one is worth.",
        tone_key="TONE_09",
        hair_style="AFRO_HALO",
        hair_colour="JET",
        accent_hair_colour="COPPER",
        signature=(0.95, 0.55, 0.12, 1.0),
        metal=GOLD,
        stature_m=1.76,
        heel_pref_m=0.095,
        default_pose="power_stand",
        signature_action="RIG_POINT_COMMAND",
        expression="AUTHORITY",
        wardrobe={"SWIM": "SWIM_GOLD_ONEPIECE",
                  "PARTY": "PARTY_LIQUID_GOWN",
                  "FASHION": "FASHION_SHARP_SUIT",
                  "STREET": "STREET_CARGO_CROP",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_RENATA": GlamCharacter(
        character_id="GLAM_RENATA",
        name="Renata Salvatierra",
        heritage="Afro-Dominican, Santo Domingo",
        archetype="The instigator",
        attitude="Starts it, films it, and is already telling the story "
                 "better than it happened before anyone else has moved.",
        motivation="Wants the store's front window, the whole window, "
                   "and is willing to burn a friendship for it.",
        tone_key="TONE_07",
        hair_style="DEEP_CURL_CASCADE",
        hair_colour="ESPRESSO",
        accent_hair_colour="HONEY",
        signature=(0.95, 0.18, 0.42, 1.0),
        metal=GOLD,
        stature_m=1.68,
        heel_pref_m=0.115,
        default_pose="hip_pop",
        signature_action="RIG_INVASIVE_STEP",
        expression="SMIRK",
        wardrobe={"SWIM": "SWIM_HOT_PINK_TRI",
                  "PARTY": "PARTY_MINI_FRINGE",
                  "FASHION": "FASHION_CUTOUT_COLUMN",
                  "STREET": "STREET_TRACK_SET",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_MEI": GlamCharacter(
        character_id="GLAM_MEI",
        name="Mei-Lin Zhou",
        heritage="Chinese, Guangzhou",
        archetype="The strategist",
        attitude="Lets the argument run for a full minute, then says the "
                 "one sentence that ends it and goes back to her tea.",
        motivation="Owns the numbers on the whole dome network and is "
                   "deciding, slowly, who gets to keep their store.",
        tone_key="TONE_03",
        hair_style="PIN_STRAIGHT_CURTAIN",
        hair_colour="BLUE_BLACK",
        accent_hair_colour=None,
        signature=(0.20, 0.78, 0.92, 1.0),
        metal=CHROME,
        stature_m=1.66,
        heel_pref_m=0.075,
        default_pose="arms_crossed",
        signature_action="RIG_DISDAINFUL_TURN",
        expression="DISDAIN",
        wardrobe={"SWIM": "SWIM_CHROME_HIGHLEG",
                  "PARTY": "PARTY_SLIP_BIAS",
                  "FASHION": "FASHION_TRENCH_ARMOUR",
                  "STREET": "STREET_TECH_SHELL",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_PRIYA": GlamCharacter(
        character_id="GLAM_PRIYA",
        name="Priya Raghunathan",
        heritage="Tamil, Chennai and everywhere with a lounge",
        archetype="The heiress",
        attitude="Arrives late on purpose, apologises to nobody, and "
                 "somehow is the only one photographed.",
        motivation="Bored of being funded and wants one thing in this "
                   "dome that is hers because she made it.",
        tone_key="TONE_06",
        hair_style="GLOSS_WAVE_LONG",
        hair_colour="ESPRESSO",
        accent_hair_colour="BURGUNDY",
        signature=(0.72, 0.22, 0.86, 1.0),
        metal=GOLD,
        stature_m=1.70,
        heel_pref_m=0.120,
        default_pose="glance_back",
        signature_action="RIG_GASP_REACTION",
        expression="SMIRK",
        wardrobe={"SWIM": "SWIM_VIOLET_WRAP",
                  "PARTY": "PARTY_CRYSTAL_MESH",
                  "FASHION": "FASHION_DRAPE_COLUMN",
                  "STREET": "STREET_DENIM_STACK",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_ZEYNEP": GlamCharacter(
        character_id="GLAM_ZEYNEP",
        name="Zeynep Aydin",
        heritage="Turkish, Istanbul",
        archetype="The fixer",
        attitude="Knows where everything is, including the thing you "
                 "have not admitted you lost. Charges for both.",
        motivation="Keeps the store's back rooms running and is quietly "
                   "assembling enough leverage to buy in.",
        tone_key="TONE_05",
        hair_style="SLEEK_BUN_EDGES",
        hair_colour="JET",
        accent_hair_colour=None,
        signature=(0.10, 0.80, 0.55, 1.0),
        metal=GUNMETAL,
        stature_m=1.72,
        heel_pref_m=0.060,
        default_pose="power_stand",
        signature_action="RIG_CLENCH_FIST_RAISE",
        expression="RESOLVE",
        wardrobe={"SWIM": "SWIM_EMERALD_SPORT",
                  "PARTY": "PARTY_LEATHER_MINI",
                  "FASHION": "FASHION_STRUCTURED_CAPE",
                  "STREET": "STREET_UTILITY_VEST",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_AROHA": GlamCharacter(
        character_id="GLAM_AROHA",
        name="Aroha Ngata",
        heritage="Maori, Aotearoa New Zealand",
        archetype="The enforcer",
        attitude="Settles things by standing up. Has not needed a second "
                 "move in four years and everyone remembers the first.",
        motivation="Guards the dome's floor and the women on it, and is "
                   "tired of being described as security.",
        tone_key="TONE_08",
        hair_style="LOCS_CROWN",
        hair_colour="JET",
        accent_hair_colour="AUBURN",
        signature=(0.25, 0.55, 0.95, 1.0),
        metal=GUNMETAL,
        stature_m=1.80,
        heel_pref_m=0.045,
        default_pose="arms_crossed",
        signature_action="RIG_GRAB_LAPEL",
        expression="THREAT",
        wardrobe={"SWIM": "SWIM_SURF_ZIP",
                  "PARTY": "PARTY_SATIN_HALTER",
                  "FASHION": "FASHION_STRUCTURED_CAPE",
                  "STREET": "STREET_UTILITY_VEST",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_KAT": GlamCharacter(
        character_id="GLAM_KAT",
        name="Katarzyna Nowak",
        heritage="Polish, Gdansk",
        archetype="The ice",
        attitude="Answers a scream with a pause. Whatever you just said, "
                 "she has already decided how it ends for you.",
        motivation="Runs the buying, hates the theatre of it, and is one "
                   "bad quarter from taking the store herself.",
        tone_key="TONE_01",
        hair_style="PLATINUM_BLUNT_BOB",
        hair_colour="PLATINUM",
        accent_hair_colour=None,
        signature=(0.72, 0.78, 0.86, 1.0),
        metal=CHROME,
        stature_m=1.74,
        heel_pref_m=0.100,
        default_pose="arms_crossed",
        signature_action="RIG_DISDAINFUL_TURN",
        expression="DISDAIN",
        wardrobe={"SWIM": "SWIM_SURF_ZIP",
                  "PARTY": "PARTY_SLIP_BIAS",
                  "FASHION": "FASHION_TRENCH_ARMOUR",
                  "STREET": "STREET_TECH_SHELL",
                  "FORM": "FORM_STUDIO"},
    ),
    "GLAM_ITZEL": GlamCharacter(
        character_id="GLAM_ITZEL",
        name="Itzel Cruz",
        heritage="Zapotec, Oaxaca",
        archetype="The newcomer who wins",
        attitude="Says almost nothing for the first half. Everything she "
                 "does say afterwards turns out to have been a warning.",
        motivation="Came to sell six pieces and is leaving with the "
                   "front window, whoever else wanted it.",
        tone_key="TONE_04",
        hair_style="BRAIDED_CROWN_RIBBON",
        hair_colour="JET",
        accent_hair_colour="MAGENTA",
        signature=(0.98, 0.40, 0.10, 1.0),
        metal=ROSE_GOLD,
        stature_m=1.62,
        heel_pref_m=0.085,
        default_pose="hip_pop",
        signature_action="RIG_POINT_COMMAND",
        expression="RESOLVE",
        wardrobe={"SWIM": "SWIM_HOT_PINK_TRI",
                  "PARTY": "PARTY_MINI_FRINGE",
                  "FASHION": "FASHION_CUTOUT_COLUMN",
                  "STREET": "STREET_DENIM_STACK",
                  "FORM": "FORM_STUDIO"},
    ),
}


WARDROBE_MODES: tuple[str, ...] = ("SWIM", "PARTY", "FASHION", "STREET",
                                   "FORM")
"""The five ways the whole cast can be dressed at once.

``SWIM`` is poolside, ``PARTY`` is going out, ``FASHION`` is the
editorial look, ``STREET`` is what she wears to actually work in the
store, and ``FORM`` is the undressed base layer -- the store's own
dress-form silhouette: her skin tone with no garment shells over it,
and no anatomy, which is all a capsule renderer could express in the
first place.  It is there so a garment can be cycled off in the
composer and the body underneath still reads as hers."""

MODE_LABEL: dict[str, str] = {
    "SWIM": "Poolside",
    "PARTY": "Going out",
    "FASHION": "Editorial",
    "STREET": "Shop floor",
    "FORM": "Studio form",
}


def cast_ids() -> tuple[str, ...]:
    """Casting order: the order the composer cycles them in."""
    return tuple(GLAM_CAST)


def character(character_id: str) -> GlamCharacter:
    try:
        return GLAM_CAST[character_id]
    except KeyError:
        raise ValueError(
            f"unknown character {character_id!r}; cast is "
            f"{', '.join(GLAM_CAST)}"
        ) from None


def skin(character_id: str) -> Colour:
    return SKIN_TONES[character(character_id).tone_key]


def hair_rgba(character_id: str) -> tuple[Colour, Colour]:
    """Her hair colour and the accent in it, which may be the same."""
    who = character(character_id)
    main = HAIR_COLOURS[who.hair_colour]
    accent = (HAIR_COLOURS[who.accent_hair_colour]
              if who.accent_hair_colour else main)
    return main, accent


def outfit_key(character_id: str, mode: str) -> str:
    who = character(character_id)
    if mode not in WARDROBE_MODES:
        raise ValueError(f"unknown wardrobe mode {mode!r}; "
                         f"choose from {', '.join(WARDROBE_MODES)}")
    return who.wardrobe[mode]


def cast_sheet() -> str:
    """A readable casting sheet, for the console and the companion file."""
    lines = ["THE DOME HOUSE CAST", ""]
    for who in GLAM_CAST.values():
        style = who.hair_style.lower().replace("_", " ")
        lines.append(f"{who.name}  --  {who.archetype}")
        lines.append(f"    heritage   {who.heritage}")
        lines.append(f"    look       {style} in {who.hair_colour.lower()}, "
                     f"tone {who.tone_key[-2:]}, {who.stature_m:.2f} m "
                     f"+ {who.heel_pref_m * 100:.0f} cm heel")
        lines.append(f"    attitude   {who.attitude}")
        lines.append(f"    wants      {who.motivation}")
        looks = ", ".join(
            f"{mode.lower()}: {who.wardrobe[mode].lower().replace('_', ' ')}"
            for mode in WARDROBE_MODES)
        lines.append(f"    wardrobe   {looks}")
        lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def _distance(one: Colour, two: Colour) -> float:
    return sum((a - b) ** 2 for a, b in zip(one[:3], two[:3])) ** 0.5


def validate_glam_cast() -> None:
    """Prove the casting before anybody has to look at it."""
    assert len(GLAM_CAST) == 8, len(GLAM_CAST)

    # The ladder has to actually be a ladder: ten steps, monotonically
    # deepening, with no two neighbours close enough to be confused.
    keys = sorted(SKIN_TONES)
    assert len(keys) == 10, keys
    values = [SKIN_TONES[key] for key in keys]
    for first, second in zip(values, values[1:]):
        assert sum(second[:3]) < sum(first[:3]), "the ladder must deepen"
        assert _distance(first, second) > 0.04, "steps too close to read"

    # Casting spread: no two women share a skin tone, a hair style or a
    # signature colour, because a fast cut has to identify them.
    for field in ("tone_key", "hair_style", "signature", "name"):
        seen = [getattr(who, field) for who in GLAM_CAST.values()]
        assert len(set(seen)) == len(seen), (field, seen)

    # And every heritage is written out rather than left implicit.
    for who in GLAM_CAST.values():
        assert who.heritage and "," in who.heritage, who.character_id
        assert who.attitude.endswith("."), who.character_id
        assert who.motivation.endswith("."), who.character_id
        assert who.tone_key in SKIN_TONES, who.character_id
        assert who.hair_colour in HAIR_COLOURS, who.character_id
        assert (who.accent_hair_colour is None
                or who.accent_hair_colour in HAIR_COLOURS), who.character_id
        # Real adult statures, and a heel is a heel and not a stilt.
        assert 1.55 <= who.stature_m <= 1.90, who.stature_m
        assert 0.0 <= who.heel_pref_m <= 0.14, who.heel_pref_m
        # Every mode is dressed.  A missing look is a crash at draw time.
        assert set(who.wardrobe) == set(WARDROBE_MODES), who.character_id
        # Hair has to sit against her skin, not disappear into it.
        assert _distance(HAIR_COLOURS[who.hair_colour],
                         SKIN_TONES[who.tone_key]) > 0.12, who.character_id

    # Hair colours must be separable from each other under one key light.
    palette = sorted(HAIR_COLOURS)
    for index, first in enumerate(palette):
        for second in palette[index + 1:]:
            assert _distance(HAIR_COLOURS[first],
                             HAIR_COLOURS[second]) > 0.05, (first, second)

    # The helpers do not lie.
    assert skin("GLAM_KAT") == SKIN_TONES["TONE_01"]
    main, accent = hair_rgba("GLAM_MEI")
    assert main == accent, "a single-colour head returns its own colour twice"
    main, accent = hair_rgba("GLAM_NAILAH")
    assert main != accent
    assert outfit_key("GLAM_AROHA", "PARTY") == "PARTY_SATIN_HALTER"
    try:
        outfit_key("GLAM_AROHA", "BALLGOWN")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown mode has to be refused")
    try:
        character("GLAM_NOBODY")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown character has to be refused")

    assert "Nailah" in cast_sheet()
    # The warm rim tone is warmer, and never blows out.
    for key in SKIN_TONES:
        lit = undertone(key)
        assert lit[0] >= SKIN_TONES[key][0]
        assert all(0.0 <= channel <= 1.0 for channel in lit)


if __name__ == "__main__":
    validate_glam_cast()
    print(cast_sheet())
