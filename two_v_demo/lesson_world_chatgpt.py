"""Ten real Dome Creator builds, costed through the Assembly Line.

This is a deliberately separate master cut.  It preserves the published
``world`` lesson while combining its real preset geometry with the existing
Dome Creator, Dome Forge, Assembly Line, and video-engine toolchain scenes.
Each showcased build carries a computed material breakdown, labor-event
breakdown, and modeled direct-sale price.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .lesson_master import MASTER_LESSON, validate_master
from .lesson_world import (
    SCENES as WORLD_SCENES,
    SHOWCASE_COPY,
    WORLD_LESSON,
    _draw_dome,
    _ground_disc,
    _rgb,
    validate_world_lesson,
)
from .lessons import Chapter, Lesson
from .render_kit import AMBER, CYAN, GREEN, MUTED, PURPLE, RED, WHITE, WorldLabel, clamp
from .segments import compose
from .world_chatgpt_facts import (
    production_economics,
    production_rows,
    selected_domes,
    steps_production,
    validate_world_chatgpt_facts,
    world_chatgpt_report,
)


DOMES = selected_domes()
BUILD_COUNT = len(DOMES)
BUILD_COUNT_WORD = "ten" if BUILD_COUNT == 10 else str(BUILD_COUNT)


def _showcase_painter(name: str):
    """Raise one Creator preset and reveal its complete cost ledger."""
    dome = next(item for item in DOMES if item.name == name)
    economics = production_economics(name)

    def painter(app, opaque, transparent, p: float) -> None:
        _ground_disc(opaque, name, reveal=clamp(p * 3.0))
        _draw_dome(opaque, transparent, name, reveal=clamp(p * 1.45))
        top = dome.height_ft / 3.281
        # The showcase camera pulls back with dome radius. Scale the label
        # ladder in world space as well so its screen-space gaps remain
        # readable from the 33-foot workshop through the 65-foot lodge.
        label_scale = max(1.0, dome.radius_m / 5.0)
        label_anchor = 5.5
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, top + label_anchor]),
            f"{dome.name.upper()}\n{dome.frequency}V  ·  "
            f"{dome.diameter_ft:.0f} FT ACROSS  ·  "
            f"{dome.floor_sqft:,.0f} SQ FT",
            _rgb(CYAN),
        ))
        if p > 0.22:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + label_anchor - 1.3 * label_scale]),
                f"{dome.struts} struts / {dome.panels} panels / "
                f"{dome.hubs} hubs / {dome.bolts} bolts",
                _rgb(WHITE),
            ))
        if p > 0.40:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + label_anchor - 2.95 * label_scale]),
                f"MATERIALS  ${economics.material_total:,.0f}\n"
                f"frame ${economics.frame_material:,.0f}  ·  "
                f"shell ${economics.enclosure_material:,.0f}\n"
                f"foundation ${economics.foundation_material:,.0f}  ·  "
                f"fit-out ${economics.fitout_material:,.0f}",
                _rgb(AMBER),
            ))
        if p > 0.58:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + label_anchor - 5.25 * label_scale]),
                f"LABOR  {economics.labor_hours:,.0f} HOURS\n"
                f"site {economics.site_hours:.0f}  ·  "
                f"frame {economics.frame_hours:.0f}\n"
                f"enclosure {economics.enclosure_hours:.0f}  ·  "
                f"systems + finish {economics.systems_hours:.0f}",
                _rgb(PURPLE),
            ))
        if p > 0.74:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + label_anchor - 7.45 * label_scale]),
                f"MODELED DIRECT-SALE  ${economics.consumer_price:,.0f}\n"
                f"Creator BOM + line labor/overhead + "
                f"{economics.family} family margin",
                _rgb(GREEN),
            ))

    return painter


def _lineup_positions() -> tuple[tuple[str, float, float], ...]:
    rows = (DOMES[:5], DOMES[5:])
    depth = max(dome.radius_m for dome in DOMES) * 1.9
    placed: list[tuple[str, float, float]] = []
    spans: list[float] = []
    for row_index, row in enumerate(rows):
        cursor = 0.0
        y = depth * (0.86 if row_index == 0 else -0.86)
        for dome in row:
            cursor += dome.radius_m * 1.22
            placed.append((dome.name, cursor, y))
            cursor += dome.radius_m * 1.22
        spans.append(cursor)
    span = max(spans)
    return tuple((name, span * 0.5 - x, y) for name, x, y in placed)


LINEUP = _lineup_positions()
LINEUP_SPAN = max(abs(x) for _name, x, _y in LINEUP) * 2.0


def scene_chatgpt_lineup(app, opaque, transparent, p: float) -> None:
    """The selected ten at true relative scale, in two readable rows."""
    for index, (name, x, y) in enumerate(LINEUP):
        reveal = clamp(p * (len(LINEUP) + 2.0) - index * 0.9)
        if reveal <= 0.02:
            continue
        origin = np.array([x, y, 0.0])
        _ground_disc(opaque, name, origin=origin, reveal=reveal)
        _draw_dome(
            opaque,
            transparent,
            name,
            origin=origin,
            reveal=reveal,
            segments=4,
            panels=False,
            hubs=False,
        )
    if p > 0.50:
        cheapest = min(production_rows(), key=lambda row: row.consumer_price)
        fastest = min(production_rows(), key=lambda row: row.labor_hours)
        app.world_labels.extend([
            WorldLabel(
                np.array([0.0, 0.0, 17.0]),
                f"{BUILD_COUNT} BUILDS · CREATOR GEOMETRY · FORGE DETAILS · "
                "LINE ECONOMICS",
                _rgb(WHITE),
            ),
            WorldLabel(
                np.array([0.0, 0.0, 14.7]),
                f"lowest modeled direct-sale: {cheapest.name}  "
                f"${cheapest.consumer_price:,.0f}",
                _rgb(GREEN),
            ),
            WorldLabel(
                np.array([0.0, 0.0, 12.7]),
                f"least labor: {fastest.name}  {fastest.labor_hours:.0f} hours",
                _rgb(PURPLE),
            ),
        ])


def scene_chatgpt_economics(app, opaque, transparent, p: float) -> None:
    """A stacked bar for material, conversion cost, and modeled margin."""
    rows = sorted(production_rows(), key=lambda row: row.consumer_price)
    maximum = max(row.consumer_price for row in rows)
    spacing = 4.4
    reveal = clamp(p * 1.25)
    for index, row in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = (len(rows) / 2.0 - index - 0.5) * spacing
        scale = 11.0 / maximum
        pieces = (
            (row.material_total, AMBER),
            (row.labor_cost + row.overhead, PURPLE),
            (row.consumer_price - row.factory_cost, GREEN),
        )
        z = 0.2
        for value, colour in pieces:
            height = max(0.04, value * scale)
            opaque.box((x, 0.0, z + height * 0.5), (3.0, 1.8, height), colour)
            z += height
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z + 1.0]),
            f"${row.consumer_price:,.0f}",
            _rgb(WHITE),
        ))
        if index in (0, len(rows) - 1):
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, z + 2.2]),
                row.name.upper(),
                _rgb(CYAN),
            ))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, -1.7]),
                   "amber materials · purple labor + overhead · green modeled margin",
                   _rgb(MUTED)),
        WorldLabel(np.array([0.0, 0.0, -3.0]),
                   "planning model only: land, permits, freight, tax and local engineering excluded",
                   _rgb(RED)),
    ])


def _showcase_camera(dome) -> tuple[float, float, float]:
    index = DOMES.index(dome)
    yaw = 32.0 + (index % 4) * 17.0
    return (yaw, 19.0, max(22.0, dome.radius_m * 3.2 + 9.5))


def _showcase_chapter(index: int, dome) -> Chapter:
    promise, base_narration = SHOWCASE_COPY[dome.name]
    economics = production_economics(dome.name)
    economics_narration = (
        "The cost stack on screen is the model, not a bid. The amber line "
        "splits the Creator bill of materials into frame, enclosure, "
        "foundation and fit-out.",
        f"The purple line totals {economics.labor_hours:.0f} labor hours from "
        "the Creator's own construction events, separated into site, frame, "
        "enclosure, and systems work. The green line then applies the Assembly "
        f"Line wage, overhead, and its {economics.family} product-family "
        "margin to produce the modeled direct-sale price.",
    )
    return Chapter(
        f"cg_show_{index:02d}",
        "00",
        dome.name,
        promise,
        base_narration + economics_narration,
        (),
        17.0,
        _showcase_camera(dome),
        f"chatgpt_show_{dome.name}",
    )


MASTER_BY_SLUG = {chapter.slug: chapter for chapter in MASTER_LESSON.chapters}
WORLD_BY_SLUG = {chapter.slug: chapter for chapter in WORLD_LESSON.chapters}


SCENES = dict(MASTER_LESSON.scenes)
SCENES.update(WORLD_SCENES)
SCENES.update({
    "chatgpt_lineup": scene_chatgpt_lineup,
    "chatgpt_economics": scene_chatgpt_economics,
})
for _dome in DOMES:
    SCENES[f"chatgpt_show_{_dome.name}"] = _showcase_painter(_dome.name)


TOOLCHAIN = tuple(
    MASTER_BY_SLUG[slug]
    for slug in ("ms_tools", "ms_creator", "ms_forge", "ms_line", "ms_engine")
)

SHOWCASES = tuple(_showcase_chapter(index, dome)
                  for index, dome in enumerate(DOMES))

SYSTEM_CHAPTERS = tuple(
    WORLD_BY_SLUG[slug]
    for slug in (
        "ladder",
        "math_frequency",
        "framing",
        "math_framing",
        "efficiency",
        "math_efficiency",
        "scale",
        "math_scale",
    )
)


CHAPTERS = (
    Chapter(
        "cg_open",
        "00",
        f"{BUILD_COUNT} builds, one accountable model",
        "Creator geometry. Forge details. Assembly Line economics.",
        (
            f"This is the master tour of {BUILD_COUNT_WORD} real Dome Creator "
            "builds. Every "
            "shell is rebuilt from the preset the walkable tool actually loads.",
            "The Dome Forge explains how the frame, panels, drains and water "
            "layers go together. The Assembly Line supplies the wage, overhead, "
            "labor ledger and product-family margin. The engine rendering this "
            "film keeps every number tied to those sources.",
            "For each build we will show the material breakdown, the labor-time "
            "breakdown, and a modeled direct-sale price. It is a planning model, "
            "not a contractor quote.",
        ),
        (),
        18.0,
        (90.0, 14.0, LINEUP_SPAN * 1.02),
        "chatgpt_lineup",
    ),
) + TOOLCHAIN + SHOWCASES + (
    Chapter(
        "cg_costs",
        "00",
        "What the consumer-price model contains",
        "Materials, conversion cost, and modeled margin stay separate.",
        (
            "Put all ten on one chart and the cost stack becomes visible. Amber "
            "is the Creator bill of materials. Purple is labor at the Assembly "
            "Line's burdened wage plus its activity-based overhead. Green is the "
            "modeled margin of the closest existing product family.",
            "That separation matters. A cheaper shell does not erase labor. A "
            "fast build does not make glass cheap. And the price at the top of "
            "each bar is not a bid: land, permits, freight, tax, local engineering "
            "and financing are outside this model.",
        ),
        (),
        19.0,
        (90.0, 15.0, 52.0),
        "chatgpt_economics",
    ),
    Chapter(
        "cg_costs_math",
        "00",
        f"{BUILD_COUNT} builds, one production ledger",
        "The full comparison, computed from the three tools.",
        (
            "Here is the complete production comparison. Each row starts with "
            "the Dome Creator's own bill of materials, adds the exact hours in "
            "its construction-event stream, and carries that result through the "
            "Assembly Line economics.",
            "The last two lines call out the lowest modeled direct-sale price and "
            "the least labor. Those are different winners, which is why a real "
            "product decision cannot be made from one number.",
        ),
        steps_production(),
        30.0,
        (90.0, 15.0, 52.0),
        "chatgpt_economics",
        "math",
    ),
) + SYSTEM_CHAPTERS + (
    Chapter(
        "cg_tradeoffs",
        "00",
        "What the model refuses to hide",
        "Curves, code, freight, site work, and local engineering still exist.",
        (
            "A dome does not make the difficult parts of housing disappear. "
            "Curved walls complicate ordinary cabinets and openings. Unfamiliar "
            "systems can slow permits, insurance and appraisal. Freight and site "
            "work can dominate a remote job. Every occupied structure still needs "
            "local structural engineering and code review.",
            "Those costs are not secretly folded into the green number. They are "
            "outside it, stated here on purpose. What this model can defend is the "
            "geometry, the generated bill of materials, the construction-event "
            "hours, and the exact conversion rule used to reach the planning price.",
        ),
        (),
        19.0,
        (90.0, 14.0, LINEUP_SPAN * 1.02),
        "chatgpt_lineup",
    ),
    Chapter(
        "cg_close",
        "00",
        "Open the tools and audit the film",
        "Every dome, dollar, and labor hour has a path back to code.",
        (
            f"That is the master cut: {BUILD_COUNT_WORD} finished configurations "
            "from the Dome "
            "Creator, the layer logic of the Dome Forge, the production ledger of "
            "the Assembly Line, and the deterministic engine that turned all of it "
            "into a film.",
            "The report beside the video lists every material bucket, every labor "
            "phase, every conversion cost and every modeled direct-sale price. Open "
            "the tools, change a preset, and run it again. The point is not that you "
            "have to trust this video. The point is that you do not.",
        ),
        (),
        18.0,
        (90.0, 14.0, LINEUP_SPAN * 1.02),
        "chatgpt_lineup",
    ),
)


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS)
)


def validate_world_chatgpt_lesson() -> None:
    from .render_kit import TriangleBatch

    validate_world_chatgpt_facts()
    validate_world_lesson()
    validate_master()
    lesson = WORLD_CHATGPT_LESSON
    lesson.validate()

    stages = {chapter.stage for chapter in lesson.chapters}
    for dome in DOMES:
        assert f"chatgpt_show_{dome.name}" in stages, dome.name
    assert len([chapter for chapter in lesson.chapters
                if chapter.slug.startswith("cg_show_")]) == 10
    assert sum(chapter.equations == steps_production()
               for chapter in lesson.chapters) == 1

    class _App:
        def __init__(self):
            self.world_labels = []

    for dome in DOMES:
        stage = f"chatgpt_show_{dome.name}"
        for progress in (0.4, 0.75, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            lesson.scenes[stage](probe, opaque, transparent, progress)
            assert opaque.vertices, (stage, progress)
            assert all(label.text.strip() for label in probe.world_labels)
        probe = _App()
        lesson.scenes[stage](probe, TriangleBatch(), TriangleBatch(), 1.0)
        text = " ".join(label.text for label in probe.world_labels)
        economics = production_economics(dome.name)
        assert dome.name.upper() in text
        assert f"${economics.material_total:,.0f}" in text
        assert f"{economics.labor_hours:,.0f} HOURS" in text
        assert f"${economics.consumer_price:,.0f}" in text


_BASE = Lesson(
    key="world_chatgpt",
    brand="DOME CREATOR / FORGE / ASSEMBLY LINE",
    title=f"{BUILD_COUNT} Dome Builds — The Accountable Master Cut",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_world_chatgpt_lesson,
    report=world_chatgpt_report,
    snapshot_prefix="world_chatgpt",
    style="hype",
    voice_rate="+4%",
    label_layout="declutter",
)


WORLD_CHATGPT_LESSON = compose(_BASE)
