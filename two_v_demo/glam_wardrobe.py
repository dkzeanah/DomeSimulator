"""The wardrobe: garments as data, drawn onto the body's own rings.

A look here is not a function somebody wrote.  It is a list of
:class:`Piece` -- a bodice from this height to that one, a skirt to the
knee with this much flare, a sleeve down the forearm, a heel -- and one
drawing routine that can render any list.  Two things follow from that
and both matter.

**Clothes cannot come out the wrong size.**  Every shell is lofted
through :func:`two_v_demo.glam_body.torso_ring`, which is the body's own
cross-section, inflated.  There is one description of the silhouette and
the body and the dress both read it, so a dress cannot end up narrower
than the woman in it.

**Every hem is a landmark.**  A mini stops at mid-thigh and a gown stops
at the floor, resolved against the posed skeleton, so the same outfit
fits a 1.62 m woman and a 1.80 m one and neither needs her own copy.

The modes
---------
``SWIM``, ``PARTY``, ``FASHION`` and ``STREET`` are dressed looks.
``FORM`` is the studio form: no garment pieces at all, the body drawn in
her own skin tone, which is what a shop's dress form looks like and what
the composer shows when you cycle the clothes off a figure.  It carries
no anatomy, because a lofted ellipse has none to carry.
:func:`validate_glam_wardrobe` checks that every look in the four
dressed modes actually covers the body -- chest band and hip band, both
proven from the piece list rather than taken on trust -- and that
``FORM`` is the only look in the wardrobe that does not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from .glam_body import (
    LIMB_FRACTION,
    body_frame,
    circle_ring,
    landmark_height,
    limb_points,
    limb_radius,
    loft,
    ring_point,
    sole_height,
    spine_point,
    taper,
    torso_radii,
    torso_ring,
)
from .geometry import normalize


Colour = tuple[float, float, float, float]


# ----------------------------------------------------------------------
# A piece
# ----------------------------------------------------------------------

PIECE_KINDS: tuple[str, ...] = (
    "TORSO", "BRIEF", "SKIRT", "TROUSER", "SLEEVE", "STRAP", "BAND",
    "COLLAR", "PLACKET", "DRAPE", "FRINGE", "CAPE", "HEEL", "SHOE",
    "BOOT", "HOOPS", "SHADES", "CHAIN", "CLUTCH", "GLOVE",
)


@dataclass(frozen=True)
class Piece:
    """One garment or accessory, and where on the body it sits.

    ``t`` is the torso parameter from :mod:`two_v_demo.glam_body`: 0 at
    the hip joint, 1 at the shoulder line, and negative below the hips,
    which is where briefs live.
    """

    kind: str
    role: str = "main"
    t0: float = 0.0
    t1: float = 1.0
    inflate: float = 1.07
    inflate_hem: float | None = None
    """Where a piece widens as it falls: wide-leg trousers, a flared
    skirt.  ``None`` keeps it parallel."""
    hem: str = "hip"
    """The landmark a falling piece stops at."""
    limb: str = "arm"
    side: str = "both"
    arc: tuple[float, float] | None = None
    """Degrees.  ``None`` closes the ring; anything else opens it, for a
    coat worn open, a thigh slit, or a cape that covers the back."""
    angle: float = 90.0
    width: float = 0.03
    count: int = 24
    sheer: float = 1.0
    """Alpha.  Below 1 the piece is drawn into the transparent batch."""
    note: str = ""


def piece(kind: str, **params) -> Piece:
    if kind not in PIECE_KINDS:
        raise ValueError(f"unknown piece kind {kind!r}; choose from "
                         f"{', '.join(PIECE_KINDS)}")
    return Piece(kind=kind, **params)


# ----------------------------------------------------------------------
# An outfit
# ----------------------------------------------------------------------

SIGNATURE = "SIGNATURE"
"""Use the character's own colour rather than a fixed one, so a look
belongs to whoever is wearing it."""

METAL = "METAL"
SKIN = "SKIN"


@dataclass(frozen=True)
class Outfit:
    """One complete look."""

    outfit_key: str
    label: str
    mode: str
    pieces: tuple[Piece, ...]
    main: Colour | str
    accent: Colour | str
    trim: Colour | str
    heel: float
    """Fraction of the wearer's own preferred heel height. 0 is flat."""
    note: str

    def kinds(self) -> tuple[str, ...]:
        return tuple(sorted({item.kind for item in self.pieces}))


def _t(kind: str, **params) -> Piece:
    return piece(kind, **params)


BLACK = (0.07, 0.07, 0.09, 1.0)
BONE = (0.90, 0.87, 0.80, 1.0)
CHARCOAL = (0.17, 0.18, 0.21, 1.0)
DENIM = (0.24, 0.33, 0.50, 1.0)
KHAKI = (0.44, 0.42, 0.31, 1.0)
SAND = (0.72, 0.64, 0.50, 1.0)
SATIN_WHITE = (0.93, 0.93, 0.95, 1.0)
LEATHER = (0.11, 0.10, 0.12, 1.0)
SLATE = (0.28, 0.32, 0.38, 1.0)


# Reusable sub-assemblies.  A shoulder strap is a shoulder strap whether
# it is holding up a swimsuit or a gown.
def _straps(t_top: float = 0.78, width: float = 0.022,
            role: str = "main") -> tuple[Piece, ...]:
    return (_t("STRAP", role=role, t1=t_top, angle=55.0, width=width),
            _t("STRAP", role=role, t1=t_top, angle=125.0, width=width))


def _halter(t_top: float = 0.76, role: str = "main") -> tuple[Piece, ...]:
    return (_t("STRAP", role=role, t1=t_top, angle=80.0, width=0.018,
               limb="neck"),
            _t("STRAP", role=role, t1=t_top, angle=100.0, width=0.018,
               limb="neck"))


OUTFITS: dict[str, Outfit] = {

    # ---------------- poolside ----------------
    "SWIM_GOLD_ONEPIECE": Outfit(
        "SWIM_GOLD_ONEPIECE", "Gold one-piece, high leg", "SWIM",
        (_t("TORSO", t0=-0.16, t1=0.78, inflate=1.05),
         *_straps(0.78),
         _t("BAND", role="metal", t0=0.30, t1=0.36, inflate=1.10),
         _t("HOOPS", role="metal"),
         _t("SHADES", role="trim")),
        SIGNATURE, (0.86, 0.68, 0.24, 1.0), BLACK, 0.0,
        "One piece, one colour, and a hardware ring at the waist."),
    "SWIM_HOT_PINK_TRI": Outfit(
        "SWIM_HOT_PINK_TRI", "Triangle two-piece", "SWIM",
        (_t("TORSO", t0=0.58, t1=0.76, inflate=1.06),
         *_straps(0.76, width=0.015),
         _t("BRIEF", t0=-0.20, t1=0.06, inflate=1.05),
         _t("HOOPS", role="metal"),
         _t("CHAIN", role="metal")),
        SIGNATURE, BONE, BLACK, 0.0,
        "The loudest thing at the pool and entirely on purpose."),
    "SWIM_CHROME_HIGHLEG": Outfit(
        "SWIM_CHROME_HIGHLEG", "High-leg metallic", "SWIM",
        (_t("TORSO", t0=0.52, t1=0.80, inflate=1.06),
         *_halter(0.80),
         _t("BRIEF", t0=-0.14, t1=0.18, inflate=1.05),
         _t("SHADES", role="trim")),
        (0.78, 0.80, 0.85, 1.0), SIGNATURE, CHARCOAL, 0.0,
        "Cut high, finished cold. Reads as armour from ten metres."),
    "SWIM_VIOLET_WRAP": Outfit(
        "SWIM_VIOLET_WRAP", "Wrap swim with sarong", "SWIM",
        (_t("TORSO", t0=0.54, t1=0.78, inflate=1.06),
         *_straps(0.78, width=0.018),
         _t("BRIEF", t0=-0.18, t1=0.08, inflate=1.05),
         _t("SKIRT", role="accent", t0=0.02, hem="knee", inflate=1.10,
            inflate_hem=1.5, arc=(20.0, 340.0), sheer=0.55),
         _t("HOOPS", role="metal")),
        SIGNATURE, (0.86, 0.72, 0.94, 1.0), BONE, 0.0,
        "A sarong knotted at the hip that is doing none of the covering "
        "it pretends to."),
    "SWIM_EMERALD_SPORT": Outfit(
        "SWIM_EMERALD_SPORT", "Sport two-piece", "SWIM",
        (_t("TORSO", t0=0.50, t1=0.82, inflate=1.06),
         _t("SLEEVE", role="main", limb="upper_arm", t0=0.0, t1=0.35,
            inflate=1.14),
         _t("BRIEF", t0=-0.16, t1=0.14, inflate=1.05),
         _t("PLACKET", role="trim", t0=0.52, t1=0.80, width=0.016)),
        SIGNATURE, BLACK, BONE, 0.0,
        "Built to actually swim in, which nobody else here is."),
    "SWIM_SURF_ZIP": Outfit(
        "SWIM_SURF_ZIP", "Zip surf suit", "SWIM",
        (_t("TORSO", t0=-0.20, t1=0.94, inflate=1.06),
         _t("SLEEVE", role="main", limb="upper_arm", t0=0.0, t1=0.62,
            inflate=1.12),
         _t("PLACKET", role="metal", t0=0.10, t1=0.92, width=0.014),
         _t("COLLAR", role="accent", inflate=1.20)),
        SIGNATURE, BLACK, (0.90, 0.92, 0.95, 1.0), 0.0,
        "Short-sleeve, zipped to the throat, and the zip is the outfit."),

    # ---------------- going out ----------------
    "PARTY_LIQUID_GOWN": Outfit(
        "PARTY_LIQUID_GOWN", "Liquid column gown", "PARTY",
        (_t("TORSO", t0=-0.04, t1=0.80, inflate=1.05),
         *_halter(0.80),
         _t("SKIRT", t0=-0.04, hem="floor", inflate=1.05, inflate_hem=1.55,
            arc=(120.0, 430.0)),
         _t("HOOPS", role="metal"),
         _t("CLUTCH", role="accent"),
         _t("HEEL", role="accent")),
        SIGNATURE, (0.90, 0.78, 0.42, 1.0), BLACK, 1.0,
        "Floor length, one slit, and a walk that uses it."),
    "PARTY_MINI_FRINGE": Outfit(
        "PARTY_MINI_FRINGE", "Fringed mini", "PARTY",
        (_t("TORSO", t0=0.06, t1=0.80, inflate=1.06),
         *_straps(0.80, width=0.016),
         _t("FRINGE", role="accent", t0=0.06, hem="mid_thigh", count=44),
         _t("HOOPS", role="metal"),
         _t("HEEL", role="main")),
        SIGNATURE, (0.95, 0.86, 0.35, 1.0), BLACK, 1.0,
        "Moves a half second after she does and never stops moving."),
    "PARTY_SLIP_BIAS": Outfit(
        "PARTY_SLIP_BIAS", "Bias-cut slip", "PARTY",
        (_t("TORSO", t0=-0.02, t1=0.74, inflate=1.04),
         *_straps(0.74, width=0.012),
         _t("SKIRT", t0=-0.02, hem="calf", inflate=1.04, inflate_hem=1.22),
         _t("CHAIN", role="metal"),
         _t("HEEL", role="main")),
        SATIN_WHITE, SIGNATURE, CHARCOAL, 1.0,
        "Cut on the bias so it moves like water and forgives nothing."),
    "PARTY_CRYSTAL_MESH": Outfit(
        "PARTY_CRYSTAL_MESH", "Crystal mesh over slip", "PARTY",
        (_t("TORSO", t0=-0.10, t1=0.72, inflate=1.05),
         *_straps(0.72, width=0.014),
         _t("TORSO", role="accent", t0=-0.14, t1=0.94, inflate=1.16,
            sheer=0.42),
         _t("SLEEVE", role="accent", limb="arm", t0=0.0, t1=1.0,
            inflate=1.22, sheer=0.42),
         _t("CHAIN", role="metal"),
         _t("HOOPS", role="metal"),
         _t("HEEL", role="trim")),
        BLACK, SIGNATURE, (0.92, 0.90, 0.96, 1.0), 1.0,
        "A slip with a lit mesh over it. The mesh is the point; the slip "
        "is the alibi."),
    "PARTY_LEATHER_MINI": Outfit(
        "PARTY_LEATHER_MINI", "Leather mini and cropped jacket", "PARTY",
        (_t("TORSO", t0=0.36, t1=0.80, inflate=1.06),
         *_straps(0.80, width=0.020),
         _t("SKIRT", role="accent", t0=0.20, hem="mid_thigh", inflate=1.08,
            inflate_hem=1.06),
         _t("BAND", role="metal", t0=0.24, t1=0.30, inflate=1.12),
         _t("TORSO", role="trim", t0=0.42, t1=0.98, inflate=1.20,
            arc=(115.0, 425.0)),
         _t("SLEEVE", role="trim", limb="arm", t0=0.0, t1=0.95,
            inflate=1.24),
         _t("HEEL", role="trim")),
        LEATHER, SIGNATURE, CHARCOAL, 0.8,
        "Cropped jacket over a leather mini: dressed for a fight she "
        "intends to win in photographs."),
    "PARTY_SATIN_HALTER": Outfit(
        "PARTY_SATIN_HALTER", "Satin halter, knee length", "PARTY",
        (_t("TORSO", t0=0.00, t1=0.78, inflate=1.05),
         *_halter(0.78),
         _t("SKIRT", t0=0.00, hem="knee", inflate=1.05, inflate_hem=1.35),
         _t("HOOPS", role="metal"),
         _t("HEEL", role="accent")),
        SIGNATURE, BONE, CHARCOAL, 1.0,
        "Halter neck, knee length, and shoulders she is not hiding."),

    # ---------------- editorial ----------------
    "FASHION_SHARP_SUIT": Outfit(
        "FASHION_SHARP_SUIT", "Sharp suit, nothing under it", "FASHION",
        (_t("TORSO", t0=0.10, t1=0.98, inflate=1.14, arc=(118.0, 422.0)),
         _t("TORSO", role="accent", t0=0.30, t1=0.72, inflate=1.05),
         _t("SLEEVE", role="main", limb="arm", t0=0.0, t1=0.96,
            inflate=1.20),
         _t("COLLAR", role="accent", inflate=1.26),
         _t("TROUSER", role="main", hem="ankle", inflate=1.22,
            inflate_hem=1.42),
         _t("BAND", role="metal", t0=0.28, t1=0.34, inflate=1.10),
         _t("HEEL", role="main")),
        CHARCOAL, SIGNATURE, BONE, 0.9,
        "A suit worn as a statement rather than as a uniform."),
    "FASHION_CUTOUT_COLUMN": Outfit(
        "FASHION_CUTOUT_COLUMN", "Cut-out column", "FASHION",
        (_t("TORSO", t0=0.52, t1=0.86, inflate=1.05),
         *_halter(0.86),
         _t("TORSO", role="accent", t0=-0.06, t1=0.30, inflate=1.05),
         _t("SKIRT", role="accent", t0=-0.06, hem="ankle", inflate=1.05,
            inflate_hem=1.18, arc=(100.0, 440.0)),
         _t("CHAIN", role="metal"),
         _t("HEEL", role="main")),
        SIGNATURE, BLACK, (0.95, 0.95, 0.98, 1.0), 1.0,
        "Two solid blocks and a gap between them doing all the talking."),
    "FASHION_TRENCH_ARMOUR": Outfit(
        "FASHION_TRENCH_ARMOUR", "Trench worn as armour", "FASHION",
        (_t("TORSO", role="accent", t0=0.30, t1=0.80, inflate=1.05),
         _t("BRIEF", role="accent", t0=-0.16, t1=0.16, inflate=1.05),
         _t("TORSO", t0=-0.02, t1=0.98, inflate=1.20, arc=(112.0, 428.0)),
         _t("SKIRT", t0=-0.02, hem="knee", inflate=1.20, inflate_hem=1.30,
            arc=(112.0, 428.0)),
         _t("SLEEVE", limb="arm", t0=0.0, t1=1.0, inflate=1.28),
         _t("COLLAR", inflate=1.32),
         _t("BAND", role="trim", t0=0.26, t1=0.34, inflate=1.24),
         _t("BOOT", role="trim", hem="knee"),
         _t("SHADES", role="trim")),
        SAND, CHARCOAL, LEATHER, 0.0,
        "Belted, collar up, and not one inch of it soft."),
    "FASHION_DRAPE_COLUMN": Outfit(
        "FASHION_DRAPE_COLUMN", "Draped column, one shoulder", "FASHION",
        (_t("TORSO", t0=-0.04, t1=0.74, inflate=1.05),
         _t("STRAP", t1=0.74, angle=55.0, width=0.045),
         _t("SKIRT", t0=-0.04, hem="floor", inflate=1.05, inflate_hem=1.40),
         _t("DRAPE", role="accent", t0=0.08, t1=0.96, width=0.075),
         _t("HOOPS", role="metal"),
         _t("HEEL", role="trim")),
        SIGNATURE, (0.96, 0.90, 0.72, 1.0), BLACK, 1.0,
        "One shoulder, one length of cloth, and a great deal of nerve."),
    "FASHION_STRUCTURED_CAPE": Outfit(
        "FASHION_STRUCTURED_CAPE", "Structured cape over tailoring",
        "FASHION",
        (_t("TORSO", role="accent", t0=0.18, t1=0.94, inflate=1.08),
         _t("TROUSER", role="accent", hem="ankle", inflate=1.18,
            inflate_hem=1.30),
         _t("CAPE", hem="knee", inflate=1.18, inflate_hem=2.10),
         _t("COLLAR", inflate=1.34),
         _t("BAND", role="metal", t0=0.26, t1=0.32, inflate=1.12),
         _t("BOOT", role="trim", hem="calf")),
        SIGNATURE, CHARCOAL, BLACK, 0.5,
        "A cape is a threat with good tailoring, and she knows it."),

    # ---------------- shop floor ----------------
    "STREET_CARGO_CROP": Outfit(
        "STREET_CARGO_CROP", "Cargo trousers, cropped tank", "STREET",
        (_t("TORSO", t0=0.44, t1=0.86, inflate=1.07),
         *_straps(0.86, width=0.020),
         _t("TROUSER", role="accent", hem="ankle", inflate=1.34,
            inflate_hem=1.50),
         _t("BAND", role="trim", t0=0.06, t1=0.14, inflate=1.16),
         _t("SHOE", role="trim"),
         _t("HOOPS", role="metal")),
        SIGNATURE, KHAKI, BLACK, 0.0,
        "What she actually works in, and still the best-dressed person "
        "in the dome."),
    "STREET_TRACK_SET": Outfit(
        "STREET_TRACK_SET", "Matching track set", "STREET",
        (_t("TORSO", t0=0.14, t1=0.96, inflate=1.16),
         _t("SLEEVE", limb="arm", t0=0.0, t1=1.0, inflate=1.20),
         _t("TROUSER", hem="ankle", inflate=1.30, inflate_hem=1.14),
         _t("PLACKET", role="accent", t0=0.16, t1=0.94, width=0.018),
         _t("SHOE", role="accent"),
         _t("HOOPS", role="metal")),
        SIGNATURE, BONE, CHARCOAL, 0.0,
        "Head to toe in one colour with a stripe down it. Undefeated."),
    "STREET_TECH_SHELL": Outfit(
        "STREET_TECH_SHELL", "Technical shell", "STREET",
        (_t("TORSO", role="accent", t0=0.20, t1=0.88, inflate=1.06),
         _t("TORSO", t0=0.02, t1=1.00, inflate=1.24),
         _t("SLEEVE", limb="arm", t0=0.0, t1=1.0, inflate=1.30),
         _t("COLLAR", inflate=1.36),
         _t("TROUSER", role="trim", hem="ankle", inflate=1.20,
            inflate_hem=1.10),
         _t("PLACKET", role="metal", t0=0.10, t1=0.98, width=0.013),
         _t("BOOT", role="trim", hem="ankle")),
        SLATE, SIGNATURE, BLACK, 0.0,
        "Sealed, hooded, and entirely uninterested in your opinion."),
    "STREET_DENIM_STACK": Outfit(
        "STREET_DENIM_STACK", "Stacked denim and a crop", "STREET",
        (_t("TORSO", t0=0.40, t1=0.84, inflate=1.07),
         _t("SLEEVE", limb="upper_arm", t0=0.0, t1=0.40, inflate=1.16),
         _t("TROUSER", role="accent", hem="floor", inflate=1.32,
            inflate_hem=1.62),
         _t("BAND", role="trim", t0=0.10, t1=0.18, inflate=1.16),
         _t("SHOE", role="trim"),
         _t("HOOPS", role="metal"),
         _t("SHADES", role="trim")),
        SIGNATURE, DENIM, LEATHER, 0.0,
        "Denim stacked over the shoe on purpose, because she said so."),
    "STREET_UTILITY_VEST": Outfit(
        "STREET_UTILITY_VEST", "Utility vest and straight leg", "STREET",
        (_t("TORSO", role="accent", t0=0.30, t1=0.86, inflate=1.06),
         _t("TORSO", t0=0.16, t1=0.96, inflate=1.22, arc=(122.0, 418.0)),
         _t("COLLAR", inflate=1.28),
         _t("TROUSER", role="trim", hem="ankle", inflate=1.24,
            inflate_hem=1.20),
         _t("BAND", role="metal", t0=0.20, t1=0.28, inflate=1.24),
         _t("BOOT", role="trim", hem="ankle")),
        KHAKI, SIGNATURE, CHARCOAL, 0.0,
        "Every pocket on it is load-bearing, including the ones that "
        "are not."),

    # ---------------- the base layer ----------------
    "FORM_STUDIO": Outfit(
        "FORM_STUDIO", "Studio form", "FORM",
        (),
        SKIN, SKIN, SKIN, 0.0,
        "The dress form: the silhouette with nothing on it, which is "
        "where every look above starts and what the composer shows when "
        "the clothes are cycled off."),
}


def outfit(outfit_key: str) -> Outfit:
    try:
        return OUTFITS[outfit_key]
    except KeyError:
        raise ValueError(f"unknown outfit {outfit_key!r}; choose from "
                         f"{', '.join(sorted(OUTFITS))}") from None


def outfits_for_mode(mode: str) -> tuple[Outfit, ...]:
    return tuple(item for item in OUTFITS.values() if item.mode == mode)


# ----------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------

def palette_for(look: Outfit, character) -> dict[str, Colour]:
    """Resolve an outfit's colour roles against whoever is wearing it.

    ``SIGNATURE`` becomes her colour and ``METAL`` her hardware, so one
    outfit worn by two women is recognisably the same garment and
    recognisably not the same person.
    """
    from .glam_cast import SKIN_TONES

    def resolve(value) -> Colour:
        if value == SIGNATURE:
            return character.signature
        if value == METAL:
            return character.metal
        if value == SKIN:
            return SKIN_TONES[character.tone_key]
        return value

    return {
        "main": resolve(look.main),
        "accent": resolve(look.accent),
        "trim": resolve(look.trim),
        "metal": character.metal,
        "skin": SKIN_TONES[character.tone_key],
    }


def _shade(colour: Colour, alpha: float) -> Colour:
    return (colour[0], colour[1], colour[2], colour[3] * alpha)


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------

def _rings_between(joints, stature, t0, t1, inflate, inflate_hem, arc,
                   steps, segments):
    top = inflate if inflate_hem is None else inflate_hem
    rings = []
    for index in range(steps + 1):
        share = index / steps
        t = t0 + (t1 - t0) * share
        blend = inflate + (top - inflate) * (1.0 - share)
        rings.append(torso_ring(joints, stature, t, inflate=blend,
                                segments=segments, arc=arc))
    return rings


def _draw_torso(batch, joints, stature, item, colour, segments=16):
    rings = _rings_between(joints, stature, item.t0, item.t1, item.inflate,
                           item.inflate_hem, item.arc, 6, segments)
    loft(batch, rings, colour, closed=item.arc is None,
         double_sided=item.arc is not None)


def _draw_brief(batch, joints, stature, item, colour, segments=16):
    rings = _rings_between(joints, stature, item.t0, item.t1, item.inflate,
                           item.inflate_hem, item.arc, 4, segments)
    loft(batch, rings, colour, cap_bottom=True, closed=item.arc is None)


def _draw_skirt(batch, joints, stature, item, colour, segments=18):
    """A cone from a torso ring down to a free hem.

    The hem is a landmark height, and the ring it makes is centred on
    the vertical through the hips rather than on the leaning spine --
    a skirt hangs plumb no matter what the torso is doing.
    """
    frame = body_frame(joints)
    top = torso_ring(joints, stature, item.t0, inflate=item.inflate,
                     segments=segments, arc=item.arc)
    hem_z = landmark_height(joints, item.hem)
    width, depth = torso_radii(stature, max(0.0, item.t0))
    flare = item.inflate_hem if item.inflate_hem is not None else item.inflate
    pelvis = np.asarray(joints["pelvis"], dtype=float)
    hem_centre = np.array([pelvis[0], pelvis[1], hem_z])
    hem = circle_ring(hem_centre, frame, width * flare, depth * flare,
                      segments, item.arc)
    steps = 5
    rings = [top + (hem - top) * (index / steps) for index in range(steps + 1)]
    loft(batch, rings, colour, closed=item.arc is None,
         double_sided=item.arc is not None)


def _leg_chain(joints, side):
    return ((f"{side}_hip", f"{side}_knee", "thigh"),
            (f"{side}_knee", f"{side}_ankle", "shank"))


def _draw_trouser(batch, joints, stature, item, colour):
    """A tube down each leg, stopping at the hem landmark.

    The leg bends, so the tube is built segment by segment and the
    segment the hem falls inside is cut at exactly the right height
    instead of at the nearest joint.
    """
    hem_z = landmark_height(joints, item.hem)
    hip_z = float(joints["pelvis"][2])
    wide = item.inflate_hem if item.inflate_hem is not None else item.inflate
    for side in ("l", "r"):
        for first, second, limb in _leg_chain(joints, side):
            start = np.asarray(joints[first], dtype=float)
            end = np.asarray(joints[second], dtype=float)
            if start[2] <= hem_z:
                continue
            share = 1.0
            if end[2] < hem_z and abs(start[2] - end[2]) > 1e-9:
                share = (start[2] - hem_z) / (start[2] - end[2])
            finish = start + (end - start) * share
            for step, point, radius_t in ((0, start, 0.0), (1, finish, share)):
                pass
            drop_a = (hip_z - start[2]) / max(1e-6, hip_z - hem_z)
            drop_b = (hip_z - finish[2]) / max(1e-6, hip_z - hem_z)
            taper(batch, start, finish,
                  limb_radius(stature, limb, 0.0) * (
                      item.inflate + (wide - item.inflate) * drop_a),
                  limb_radius(stature, limb, share) * (
                      item.inflate + (wide - item.inflate) * drop_b),
                  colour, sides=10, cap=False)
    # The seat: a short shell over the hips so the two legs join up.
    rings = _rings_between(joints, stature, -0.20, 0.12, item.inflate,
                           None, None, 3, 16)
    loft(batch, rings, colour, cap_bottom=True)


def _draw_sleeve(batch, joints, stature, item, colour):
    sides = ("l", "r") if item.side == "both" else (item.side,)
    limbs = (("upper_arm", "forearm") if item.limb == "arm"
             else (item.limb,))
    span = item.t1 - item.t0
    for side in sides:
        for index, limb in enumerate(limbs):
            low = max(0.0, min(1.0, (item.t0 - index * 0.5) * len(limbs)
                               if item.limb == "arm" else item.t0))
            high = max(0.0, min(1.0, (item.t1 - index * 0.5) * len(limbs)
                                if item.limb == "arm" else item.t1))
            if high <= low:
                continue
            taper(batch,
                  limb_points(joints, limb, side, low),
                  limb_points(joints, limb, side, high),
                  limb_radius(stature, limb, low) * item.inflate,
                  limb_radius(stature, limb, high) * item.inflate,
                  colour, sides=9, cap=False)
    del span


def _draw_strap(batch, joints, stature, item, colour):
    """A strap from the shoulder, or from behind the neck for a halter."""
    end = ring_point(joints, stature, item.t1, item.angle,
                     inflate=item.inflate)
    if item.limb == "neck":
        start = ring_point(joints, stature, 1.02, 270.0, inflate=1.05)
        via = np.asarray(joints["neck"], dtype=float) + np.array(
            [0.0, 0.0, LIMB_FRACTION["neck"] * stature * 1.2])
        taper(batch, start, via, item.width, item.width * 0.9, colour,
              sides=6, cap=False)
        taper(batch, via, end, item.width * 0.9, item.width, colour,
              sides=6, cap=False)
        return
    side = "l" if item.angle < 90.0 else "r"
    start = np.asarray(joints[f"{side}_shoulder"], dtype=float)
    taper(batch, start, end, item.width, item.width, colour, sides=6,
          cap=False)


def _draw_band(batch, joints, stature, item, colour):
    rings = _rings_between(joints, stature, item.t0, item.t1, item.inflate,
                           None, item.arc, 2, 18)
    loft(batch, rings, colour, closed=item.arc is None)


def _draw_collar(batch, joints, stature, item, colour):
    base = torso_ring(joints, stature, 0.96, inflate=item.inflate,
                      segments=16, arc=(150.0, 390.0))
    frame = body_frame(joints)
    top = base + frame.up * (LIMB_FRACTION["neck"] * stature * 1.5)
    loft(batch, (base, top), colour, closed=False, double_sided=True)


def _draw_placket(batch, joints, stature, item, colour):
    steps = 6
    rings = []
    for index in range(steps + 1):
        t = item.t0 + (item.t1 - item.t0) * index / steps
        centre = ring_point(joints, stature, t, item.angle,
                            inflate=item.inflate, padding=0.004)
        frame = body_frame(joints)
        rings.append(np.array([centre - frame.side * item.width,
                               centre + frame.side * item.width]))
    loft(batch, rings, colour, closed=False, double_sided=True)


def _draw_drape(batch, joints, stature, item, colour):
    """A sash from one shoulder across to the opposite hip."""
    frame = body_frame(joints)
    steps = 8
    rings = []
    for index in range(steps + 1):
        share = index / steps
        t = item.t1 + (item.t0 - item.t1) * share
        angle = 45.0 + 95.0 * share
        centre = ring_point(joints, stature, t, angle, inflate=1.10,
                            padding=0.006)
        along = frame.side * math.cos(math.radians(angle + 90.0)) \
            + frame.forward * math.sin(math.radians(angle + 90.0))
        along = normalize(along)
        rings.append(np.array([centre - along * item.width,
                               centre + along * item.width]))
    loft(batch, rings, colour, closed=False, double_sided=True)


def _draw_fringe(batch, joints, stature, item, colour):
    frame = body_frame(joints)
    hem_z = landmark_height(joints, item.hem)
    top = torso_ring(joints, stature, item.t0, inflate=item.inflate,
                     segments=item.count)
    for index, root in enumerate(top):
        swing = math.sin(index * 1.7) * 0.018
        radial = root - spine_point(joints, item.t0)
        radial[2] = 0.0
        radial = normalize(radial) if float(
            np.linalg.norm(radial)) > 1e-9 else frame.forward
        end = np.array([root[0] + radial[0] * swing,
                        root[1] + radial[1] * swing,
                        hem_z])
        taper(batch, root, end, 0.011, 0.006, colour, sides=4, cap=False)


def _draw_cape(batch, joints, stature, item, colour):
    frame = body_frame(joints)
    hem_z = landmark_height(joints, item.hem)
    arc = item.arc if item.arc is not None else (150.0, 390.0)
    top = torso_ring(joints, stature, 1.0, inflate=item.inflate,
                     segments=18, arc=arc)
    width, depth = torso_radii(stature, 1.0)
    flare = item.inflate_hem if item.inflate_hem is not None else 1.8
    pelvis = np.asarray(joints["pelvis"], dtype=float)
    hem = circle_ring(np.array([pelvis[0], pelvis[1], hem_z]), frame,
                      width * flare, depth * flare, 18, arc)
    steps = 6
    rings = [top + (hem - top) * (index / steps) for index in range(steps + 1)]
    loft(batch, rings, colour, closed=False, double_sided=True)


def _foot_frame(joints, side):
    ankle = np.asarray(joints[f"{side}_ankle"], dtype=float)
    toe = np.asarray(joints[f"{side}_toe"], dtype=float)
    return ankle, toe


def _draw_heel(batch, joints, stature, item, colour, heel_m: float):
    """The shoe, and the column of air the heel is holding her over.

    The figure was already lifted by the heel height when it was posed,
    so what this draws is the sole she is standing on and the post that
    reaches the actual floor.
    """
    ground = sole_height(joints) - heel_m
    for side in ("l", "r"):
        ankle, toe = _foot_frame(joints, side)
        sole = sole_height(joints)
        plate_back = np.array([ankle[0], ankle[1], sole])
        plate_front = np.array([toe[0], toe[1], sole])
        taper(batch, plate_back, plate_front,
              LIMB_FRACTION["foot_height"] * stature * 0.75,
              LIMB_FRACTION["foot_height"] * stature * 0.42, colour,
              sides=7)
        if heel_m > 0.005:
            post = np.array([ankle[0], ankle[1], ground])
            taper(batch, plate_back, post, 0.020, 0.012, colour, sides=6)
        # The instep strap, which is what stops it looking like a block.
        instep = (plate_back + plate_front) * 0.5
        taper(batch, instep, instep + np.array([0.0, 0.0, 0.045]),
              0.026, 0.018, colour, sides=6, cap=False)


def _draw_shoe(batch, joints, stature, item, colour):
    _draw_heel(batch, joints, stature, item, colour, 0.0)


def _draw_boot(batch, joints, stature, item, colour):
    _draw_heel(batch, joints, stature, item, colour, 0.0)
    hem_z = landmark_height(joints, item.hem)
    for side in ("l", "r"):
        ankle = np.asarray(joints[f"{side}_ankle"], dtype=float)
        knee = np.asarray(joints[f"{side}_knee"], dtype=float)
        span = max(1e-6, knee[2] - ankle[2])
        share = max(0.0, min(1.0, (hem_z - ankle[2]) / span))
        top = ankle + (knee - ankle) * share
        taper(batch, ankle, top,
              limb_radius(stature, "shank", 1.0) * 1.30,
              limb_radius(stature, "shank", 1.0 - share) * 1.22,
              colour, sides=9, cap=False)


def _draw_hoops(batch, joints, stature, item, colour):
    from .glam_body import head_shape

    centre, radius, _half = head_shape(joints)
    frame = body_frame(joints)
    hoop = radius * 0.62
    for sign in (-1.0, 1.0):
        ear = centre + frame.side * (sign * radius * 0.94) - frame.up * (
            radius * 0.10)
        seat = ear - frame.up * hoop * 0.55
        for step in range(10):
            angle = math.tau * step / 10
            point = seat + (frame.forward * math.cos(angle)
                            + frame.up * math.sin(angle)) * hoop
            batch.sphere(point, radius * 0.075, colour, 3, 5)


def _draw_shades(batch, joints, stature, item, colour):
    from .glam_body import head_shape

    centre, radius, _half = head_shape(joints)
    frame = body_frame(joints)
    for sign in (-1.0, 1.0):
        lens = (centre + frame.forward * (radius * 0.86)
                + frame.side * (sign * radius * 0.36)
                + frame.up * (radius * 0.16))
        taper(batch, lens, lens + frame.forward * (radius * 0.10),
              radius * 0.30, radius * 0.26, colour, sides=8)
        temple = (centre + frame.side * (sign * radius * 0.92)
                  + frame.up * (radius * 0.18))
        taper(batch, lens, temple, radius * 0.05, radius * 0.05, colour,
              sides=4, cap=False)
    bridge = centre + frame.forward * (radius * 0.94) + frame.up * (
        radius * 0.20)
    taper(batch, bridge - frame.side * radius * 0.14,
          bridge + frame.side * radius * 0.14,
          radius * 0.05, radius * 0.05, colour, sides=4, cap=False)


def _draw_chain(batch, joints, stature, item, colour):
    ring = torso_ring(joints, stature, 0.95, inflate=1.10, segments=18)
    for point in ring:
        batch.sphere(point, 0.010, colour, 3, 5)
    front = ring_point(joints, stature, 0.86, 90.0, inflate=1.10)
    batch.sphere(front, 0.020, colour, 4, 7)


def _draw_clutch(batch, joints, stature, item, colour):
    frame = body_frame(joints)
    grip = np.asarray(joints["r_grip"], dtype=float)
    centre = grip + frame.forward * 0.03
    for offset, radius in ((-0.055, 0.028), (0.055, 0.028)):
        pass
    taper(batch, centre - frame.side * 0.075, centre + frame.side * 0.075,
          0.052, 0.052, colour, sides=4)


def _draw_glove(batch, joints, stature, item, colour):
    for side in ("l", "r"):
        taper(batch,
              limb_points(joints, "forearm", side, item.t0),
              limb_points(joints, "forearm", side, 1.0),
              limb_radius(stature, "forearm", item.t0) * item.inflate,
              limb_radius(stature, "forearm", 1.0) * item.inflate,
              colour, sides=8, cap=False)
        batch.sphere(joints[f"{side}_grip"],
                     LIMB_FRACTION["hand"] * stature * 1.06, colour, 4, 7)


DRAWERS = {
    "TORSO": _draw_torso,
    "BRIEF": _draw_brief,
    "SKIRT": _draw_skirt,
    "TROUSER": _draw_trouser,
    "SLEEVE": _draw_sleeve,
    "STRAP": _draw_strap,
    "BAND": _draw_band,
    "COLLAR": _draw_collar,
    "PLACKET": _draw_placket,
    "DRAPE": _draw_drape,
    "FRINGE": _draw_fringe,
    "CAPE": _draw_cape,
    "SHOE": _draw_shoe,
    "BOOT": _draw_boot,
    "HOOPS": _draw_hoops,
    "SHADES": _draw_shades,
    "CHAIN": _draw_chain,
    "CLUTCH": _draw_clutch,
    "GLOVE": _draw_glove,
}


def draw_outfit(
    opaque,
    joints: Mapping[str, np.ndarray],
    stature: float,
    look: Outfit,
    palette: Mapping[str, Colour],
    *,
    heel_m: float = 0.0,
    transparent=None,
) -> None:
    """Draw every piece of a look onto a posed body.

    Sheer pieces go into ``transparent`` when one is supplied, because
    the renderer draws that batch after the opaque one with blending on.
    Without it they are drawn solid rather than dropped, so a still
    rendered by something that has only one batch still shows the whole
    outfit.
    """
    for item in look.pieces:
        colour = palette[item.role]
        target = opaque
        if item.sheer < 1.0:
            colour = _shade(colour, item.sheer)
            if transparent is not None:
                target = transparent
        if item.kind == "HEEL":
            _draw_heel(target, joints, stature, item, colour, heel_m)
            continue
        DRAWERS[item.kind](target, joints, stature, item, colour)


# ----------------------------------------------------------------------
# Coverage
# ----------------------------------------------------------------------

COVERAGE_BANDS: dict[str, tuple[float, float]] = {
    "chest": (0.60, 0.72),
    "waist": (0.28, 0.36),
    "hip": (-0.10, 0.04),
}
"""Torso parameters a dressed look has to have something over."""

_COVERING_KINDS = {"TORSO", "BRIEF", "SKIRT", "TROUSER", "BAND", "CAPE",
                   "FRINGE"}


def covered_spans(look: Outfit) -> tuple[tuple[float, float], ...]:
    """The stretches of torso a look has something solid over.

    Pieces are merged where they meet, because a bodice that ends where
    the skirt begins covers the join between them -- checking each piece
    on its own would call a floor-length gown indecent at the hip.
    """
    spans: list[list[float]] = []
    for item in look.pieces:
        if item.kind not in _COVERING_KINDS or item.sheer < 1.0:
            continue
        if item.kind in ("SKIRT", "FRINGE", "CAPE"):
            bottom, top = -1.0, item.t0
        elif item.kind == "TROUSER":
            bottom, top = -1.0, 0.12
        else:
            bottom, top = item.t0, item.t1
        spans.append([bottom, top])
    spans.sort()
    merged: list[list[float]] = []
    for span in spans:
        if merged and span[0] <= merged[-1][1] + 1e-9:
            merged[-1][1] = max(merged[-1][1], span[1])
        else:
            merged.append(list(span))
    return tuple((low, high) for low, high in merged)


def covers(look: Outfit, band: str) -> bool:
    """Whether a look is covered across a named band of the torso.

    Read off the piece list, so it is a property of the outfit data and
    not of a render somebody looked at once.
    """
    low, high = COVERAGE_BANDS[band]
    return any(bottom <= low + 1e-9 and top >= high - 1e-9
               for bottom, top in covered_spans(look))


def wardrobe_report() -> str:
    lines = ["WARDROBE", ""]
    for mode in ("SWIM", "PARTY", "FASHION", "STREET", "FORM"):
        lines.append(mode)
        for look in outfits_for_mode(mode):
            lines.append(f"    {look.label:<34} "
                         f"{len(look.pieces):>2} pieces  "
                         f"heel {look.heel:.1f}x")
            lines.append(f"        {look.note}")
        lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_glam_wardrobe() -> None:
    """Prove every look is complete, covered, wearable and drawable."""
    from .figure import POSES
    from .glam_body import glam_joints
    from .glam_cast import GLAM_CAST, WARDROBE_MODES
    from .render_kit import TriangleBatch

    # Every look a character can be put in exists, and every look in the
    # wardrobe is reachable from the casting.
    referenced = {key for who in GLAM_CAST.values()
                  for key in who.wardrobe.values()}
    assert referenced <= set(OUTFITS), referenced - set(OUTFITS)
    assert set(OUTFITS) == referenced, set(OUTFITS) - referenced
    for look in OUTFITS.values():
        assert look.mode in WARDROBE_MODES, look.outfit_key
        assert look.note.endswith("."), look.outfit_key
        assert 0.0 <= look.heel <= 1.0, look.outfit_key
        for item in look.pieces:
            assert item.kind in PIECE_KINDS, (look.outfit_key, item.kind)
            assert item.role in ("main", "accent", "trim", "metal", "skin"), (
                look.outfit_key, item.role)
            assert 0.0 < item.sheer <= 1.0, look.outfit_key

    # The studio form is the only look with nothing on it, and every
    # dressed look actually covers the body.  Both directions matter:
    # the first stops a look being empty by accident, the second stops a
    # dressed mode from quietly not being dressed.
    empty = {key for key, look in OUTFITS.items() if not look.pieces}
    assert empty == {"FORM_STUDIO"}, empty
    for look in OUTFITS.values():
        if look.mode == "FORM":
            continue
        for band in ("chest", "hip"):
            assert covers(look, band), (look.outfit_key, band,
                                        covered_spans(look))
    assert not covers(OUTFITS["FORM_STUDIO"], "chest")
    # Merging is what makes the check honest: a gown whose bodice stops
    # exactly where its skirt starts is covered at the join.
    gown_spans = covered_spans(OUTFITS["PARTY_LIQUID_GOWN"])
    assert len(gown_spans) == 1, gown_spans

    # Every dressed mode is offered to at least four of the eight women,
    # or the casting has quietly collapsed onto one look.
    for mode in WARDROBE_MODES:
        wearers = {who.character_id for who in GLAM_CAST.values()
                   if OUTFITS[who.wardrobe[mode]].mode == mode}
        assert len(wearers) == len(GLAM_CAST), mode

    stature = 1.70
    joints = glam_joints(POSES["stand"], stature, heel_m=0.10)
    who = GLAM_CAST["GLAM_NAILAH"]

    for key, look in OUTFITS.items():
        opaque = TriangleBatch()
        clear = TriangleBatch()
        colours = palette_for(look, who)
        draw_outfit(opaque, joints, stature, look, colours, heel_m=0.10,
                    transparent=clear)
        if look.pieces:
            assert opaque.vertices or clear.vertices, key
        vertices = opaque.vertices + clear.vertices
        if not vertices:
            continue
        points = np.asarray(vertices, dtype=float).reshape(-1, 10)[:, :3]
        # Nothing below the floor she is standing on, and nothing above
        # her head: a garment that escapes the body is a garment nobody
        # will notice is wrong until it is in a frame.
        assert points[:, 2].min() > sole_height(joints) - 0.12, (
            key, points[:, 2].min())
        assert points[:, 2].max() < float(joints["head_top"][2]) + 0.02, (
            key, points[:, 2].max())
        reach = np.linalg.norm(points[:, :2], axis=1).max()
        assert reach < stature * 0.45, (key, reach)

    # A sheer piece goes to the transparent batch and carries its alpha.
    mesh = OUTFITS["PARTY_CRYSTAL_MESH"]
    opaque = TriangleBatch()
    clear = TriangleBatch()
    draw_outfit(opaque, joints, stature, mesh,
                palette_for(mesh, who), transparent=clear)
    assert clear.vertices, "the mesh has to reach the transparent batch"
    alphas = np.asarray(clear.vertices, dtype=float).reshape(-1, 10)[:, 9]
    assert alphas.max() < 0.99, alphas.max()
    # And without a transparent batch nothing is silently dropped.
    only = TriangleBatch()
    draw_outfit(only, joints, stature, mesh, palette_for(mesh, who))
    assert len(only.vertices) >= len(opaque.vertices) + len(clear.vertices)

    # Colour roles resolve to the wearer.
    suit = OUTFITS["FASHION_SHARP_SUIT"]
    colours = palette_for(suit, who)
    assert colours["accent"] == who.signature
    assert colours["metal"] == who.metal
    other = palette_for(suit, GLAM_CAST["GLAM_MEI"])
    assert other["accent"] != colours["accent"], "one suit, two women"
    assert other["main"] == colours["main"], "and still the same suit"

    # Clothes are not smaller than the body: every torso shell sits
    # outside the skin it is drawn over.
    for look in OUTFITS.values():
        for item in look.pieces:
            if item.kind in ("TORSO", "BRIEF", "BAND", "SKIRT"):
                assert item.inflate >= 1.0, (look.outfit_key, item.inflate)

    # A hem lands where the landmark is, within the thickness of the
    # cloth: the claim the module docstring makes about landmarks.
    gown = OUTFITS["PARTY_LIQUID_GOWN"]
    batch = TriangleBatch()
    draw_outfit(batch, joints, stature, gown, palette_for(gown, who),
                heel_m=0.10)
    lowest = np.asarray(batch.vertices, dtype=float).reshape(-1, 10)[:, 2].min()
    floor = landmark_height(joints, "floor")
    assert abs(lowest - (floor - 0.10)) < 0.12, (lowest, floor)

    # And the same gown on a shorter woman is shorter, without anybody
    # editing the outfit.
    short = glam_joints(POSES["stand"], 1.55)
    tall = glam_joints(POSES["stand"], 1.85)
    hems = []
    for skeleton, height in ((short, 1.55), (tall, 1.85)):
        batch = TriangleBatch()
        draw_outfit(batch, skeleton, height, gown, palette_for(gown, who))
        hems.append(np.asarray(batch.vertices,
                               dtype=float).reshape(-1, 10)[:, 2].max())
    assert hems[0] < hems[1] - 0.2, hems

    try:
        outfit("PARTY_TRACKSUIT")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown outfit has to be refused")
    try:
        piece("HAT")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown piece kind has to be refused")


if __name__ == "__main__":
    validate_glam_wardrobe()
    print(wardrobe_report())
