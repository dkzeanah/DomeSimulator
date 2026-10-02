"""A concept card, filmed in the Cabin World.

The card's shapes are drawn around the origin of an ordinary lesson stage and
:func:`two_v_demo.cabin_stage.restage` puts that stage on the exhibit platform
on the hilltop, with the cinematic cameras, the sunset and the dome behind --
so a film made from a video another model watched looks like every other
Cabin World film, and the renderer, narration, captions, phone cut and
release folder are the standard ones.

Chapters, in order:

1. the concept itself (the card's ``summary``, every shape on show);
2. **the numbers we are working from** -- every number on the card with its
   kind, on screen before any is used (the house rule for declared values);
3. one chapter per ``beat``, with that beat's figures computed on screen;
4. **where it fits the dome** -- the ``dome_fit`` slot, sized against the dome's
   own computed numbers;
5. **what it will not do** -- the ``limits``, which every card must have.

    py -3.12 -m rerender stills concept_<slug>       # look first
    py -3.12 -m rerender render concept_<slug>       # then the film
"""

from __future__ import annotations

import numpy as np

from two_v_demo.cabin_stage import restage
from two_v_demo.lessons import Chapter, Lesson
from two_v_demo.render_kit import WorldLabel

from .card import COLOURS, Card, all_cards


def _colour(value, alpha: float = 1.0) -> tuple:
    rgb = COLOURS.get(value, value) if isinstance(value, str) else value
    rgb = tuple(float(c) for c in (rgb or COLOURS["steel"])[:3])
    return (*rgb, float(alpha))


def _v(p) -> np.ndarray:
    return np.asarray(p, dtype=np.float64)


def draw(shape: dict, opaque, transparent, app, p: float) -> None:
    """One shape from the card's vocabulary, in stage units (about +/-7 across)."""
    alpha = float(shape.get("alpha", 1.0))
    batch = transparent if alpha < 1.0 else opaque
    colour = _colour(shape.get("color", "steel"), alpha)
    kind = shape["type"]
    at = _v(shape.get("at", (0, 0, 0)))
    if kind == "box":
        batch.box(at, _v(shape.get("size", (1, 1, 1))), colour)
    elif kind == "cylinder":
        batch.cylinder(at, _v(shape["to"]), float(shape.get("radius", 0.3)), colour, 18)
    elif kind == "sphere":
        batch.sphere(at, float(shape.get("radius", 0.5)), colour, 8, 16)
    elif kind == "cone":
        batch.cone(at, _v(shape["to"]), float(shape.get("radius", 0.4)), colour, 18)
    elif kind == "arrow":
        batch.arrow(at, _v(shape["to"]), float(shape.get("radius", 0.06)), colour)
    elif kind == "disc":
        batch.disc(at, float(shape.get("radius", 1.0)), colour, 40)
    elif kind == "flow":
        # Particles running along a path: heat, air, vapour, water.
        path = [_v(q) for q in shape["path"]]
        lengths = [float(np.linalg.norm(b - a)) for a, b in zip(path, path[1:])]
        total = sum(lengths) or 1.0
        count = int(shape.get("count", 10))
        size = float(shape.get("radius", 0.12))
        for k in range(count):
            s = ((k / count + p * float(shape.get("speed", 1.0))) % 1.0) * total
            for a, b, length in zip(path, path[1:], lengths):
                if s <= length:
                    point = a + (b - a) * (s / max(length, 1e-9))
                    opaque.sphere(point, size, colour, 4, 8)
                    break
                s -= length
    if shape.get("label") or kind == "label":
        text = shape.get("text") if kind == "label" else shape["label"]
        offset = _v(shape.get("label_offset", (0, 0, 0.8)))
        rgb = tuple(int(c * 255) for c in _colour(shape.get("label_color", "white"))[:3])
        app.world_labels.append(WorldLabel((at + offset).astype(np.float32), str(text), rgb))


def _painter(card: Card, show):
    shapes = card.data.get("shapes", [])

    def paint(app, opaque, transparent, p: float) -> None:
        for shape in shapes:
            if show == "all" or shape.get("id") in show or shape.get("always"):
                draw(shape, opaque, transparent, app, p)
    return paint


def _duration(text: str) -> float:
    return max(8.0, len(text.split()) / 2.5 + 2.0)


def lesson(card: Card) -> Lesson:
    """The card as a Cabin World lesson, keyed ``concept_<slug>``."""
    from .dome_facts import SLOTS

    data = card.data
    chapters, scenes = [], {}

    def add(slug: str, title: str, promise: str, narration: str, equations, show) -> None:
        stage = f"{card.key}_{slug}"
        scenes[stage] = _painter(card, show)
        chapters.append(Chapter(slug, f"{len(chapters) + 1:02d}", card.fill(title),
                                card.fill(promise), (narration,), tuple(equations),
                                _duration(narration), (0.0, 0.0, 0.0), stage))

    add("what", data["title"], data.get("hook", ""), card.fill(data["summary"]), (), "all")

    numbers = data.get("numbers", [])
    by_kind = {k: sum(1 for n in numbers if n.get("kind") == k)
               for k in ("measured", "claimed", "standard", "estimate")}
    said = ", ".join(f"{n} {k}" for k, n in by_kind.items() if n)
    add("numbers", "The numbers we are working from",
        "Where every figure in this film comes from.",
        f"Before anything is worked out, here is everything this film rests on: "
        f"{len(numbers)} numbers, {said}. A claimed number is what the source said "
        "and has not been measured here. Every figure after this is arithmetic on "
        "these and on the dome's own computed numbers.",
        [f"{card.line(n['name'])}  ({n.get('kind')})" for n in numbers], "all")

    for i, beat in enumerate(data.get("beats", []), start=1):
        add(f"beat{i}", beat["title"], beat.get("promise", ""), card.fill(beat["narration"]),
            [card.line(name) for name in beat.get("figures", [])], beat.get("show", "all"))

    fit = data.get("dome_fit", {})
    slot_text, _files = SLOTS[fit["slot"]]
    add("fit", fit.get("title", "Where it fits the dome"),
        fit.get("promise", f"In the dome, this is the {slot_text.split(':')[0]}."),
        card.fill(fit.get("narration", "")),
        [card.line(name) for name in fit.get("figures", [])], fit.get("show", "all"))

    limits = data.get("limits", [])
    add("limits", "What it will not do", "The number that does not help.",
        " ".join(card.fill(lim["narration"]) for lim in limits),
        [card.line(name) for lim in limits for name in lim.get("figures", [])], "all")

    raw = Lesson(key=f"{card.key}_raw", brand=str(data.get("brand", "DOMESIM CONCEPTS")).upper(),
                 title=data["title"], chapters=tuple(chapters), scenes=scenes,
                 snapshot_prefix=card.key, label_layout="declutter")
    return restage(raw, key=card.key)


def ready_lessons() -> list[Lesson]:
    return [lesson(card) for card in all_cards() if card.ready]


def filmable_cards() -> list[Card]:
    """Cards the renderer can play: ready ones, and clean examples (to preview)."""
    return [card for card in all_cards() if not card.problems
            and card.data.get("status") in ("ready", "example")]


def concept_lessons() -> list[Lesson]:
    return [lesson(card) for card in filmable_cards()]
