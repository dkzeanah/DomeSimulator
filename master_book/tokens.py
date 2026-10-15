"""Live numbers for the Master Edition.

The Master Edition quotes two kinds of figure, and both are computed:

* everything the Complete Edition already computes -- the reference dome,
  the cut list, the clock, the price lists, and the paperback's own figures
  it borrows as ``tt_*`` -- through :func:`wedge_book.tokens.resolve`, so this
  edition and the books it contains cannot disagree about a number;
* the few figures only this edition needs, under ``mb.*``: the sizes of the
  paper and straw models a family builds on rung two, the shape of the book
  itself, and the counts in the one-page summary. Every model size is the
  real dome scaled, read from the same solved topology the frame is cut from;
  the only literals are the two declared model sizes, which are choices.

An unknown token stops the build, exactly as it does in both books.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Callable

TOKEN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")

#: Declared, not derived: the long side of a paper triangle, chosen so the
#: six caps fit one printed page.
PAPER_LONG_MM = 46.0
#: Declared: the long straw of the straw dome, the length of a drinking straw
#: with its bendy end cut off.
STRAW_LONG_CM = 20.0
#: Declared: how many paper triangles the timing exercise on rung two makes.
TIMED_TRIANGLES = 5


@dataclass(frozen=True)
class Token:
    name: str
    describe: str
    compute: Callable[[], str]

    def value(self) -> str:
        return self.compute()


@lru_cache(maxsize=1)
def _solved() -> dict:
    """The reference dome's facts and its topology, read once per build."""
    from collections import Counter

    from two_v_demo import channel_facts
    from wedge_book import numbers

    q = numbers.quantities()
    topo = channel_facts.reference_model().topology
    degree: Counter = Counter()
    rim = set()
    kinds: Counter = Counter()
    for edge in topo.edges.values():
        a, b = edge.key
        degree[a] += 1
        degree[b] += 1
        kinds[edge.edge_type] += 1
        if edge.is_base:
            rim.update((a, b))
    interior = [v for v in range(len(topo.vertices)) if v not in rim]
    five = sum(1 for v in interior if degree[v] == 5)
    six = sum(1 for v in interior if degree[v] == 6)
    rim_edges = sum(1 for e in topo.edges.values() if e.is_base)
    return {
        "q": {k: v.value for k, v in q.items()},
        "long_edges": kinds["A"], "short_edges": kinds["B"],
        "vertices": len(topo.vertices), "five_way": five, "six_way": six,
        "rim_vertices": len(rim), "rim_edges": rim_edges,
    }


def _films() -> tuple[int, int]:
    """(films registered, films rendered) -- a film counts as rendered when
    its file, or a later version of it, is on disk."""
    from two_v_demo.deliverables import DELIVERABLES, OUTPUT_DIR

    rendered = 0
    for d in DELIVERABLES:
        path = d.path(OUTPUT_DIR)
        if path.exists() or any(path.parent.glob(f"{path.stem}-v*{path.suffix}")):
            rendered += 1
    return len(DELIVERABLES), rendered


def _table() -> dict[str, Token]:
    from two_v_demo import book as volume_b
    from wedge_book import outline as volume_a

    from . import outline

    s = _solved()
    q = s["q"]
    a, b = q["a_factor"], q["b_factor"]
    entries: list[Token] = []

    def add(name: str, describe: str, compute) -> None:
        entries.append(Token(name, describe, compute))

    # -- this book's own shape ------------------------------------------
    add("mb.rungs", "rungs in the ladder", lambda: str(len(outline.RUNGS)))
    add("mb.threads", "threads, one per idea", lambda: str(len(outline.THREADS)))
    add("mb.cells", "chapters and cards in the grid", lambda: str(len(outline.CELLS)))
    add("mb.written", "chapters written in full for this edition",
        lambda: str(sum(1 for c in outline.CELLS if outline.RUNG[c.rung].written)))
    add("mb.routes", "reading-route cards", lambda: str(
        sum(1 for c in outline.CELLS if not outline.RUNG[c.rung].written)))
    add("mb.paths", "named reading paths", lambda: str(len(outline.PATHS)))
    add("mb.milestones", "milestones on the ladder",
        lambda: str(sum(len(r.milestones) for r in outline.RUNGS)))
    add("mb.vol_a_chapters", "chapters in Volume A", lambda: str(len(volume_a.BOOK.chapters)))
    add("mb.vol_a_parts", "parts in Volume A", lambda: str(len(volume_a.BOOK.parts)))
    add("mb.vol_b_chapters", "chapters in Volume B", lambda: str(len(volume_b.BOOK.chapters)))
    add("mb.vol_b_parts", "parts in Volume B", lambda: str(len(volume_b.BOOK.parts)))
    add("mb.built", "the day this copy was built", lambda: date.today().strftime("%d %B %Y").lstrip("0"))
    add("mb.films", "films the project has rendered", lambda: str(_films()[1]))
    add("mb.films_registered", "films the project has registered", lambda: str(_films()[0]))

    # -- the published veteran figures, quoted from the pitch's own table --
    def vets(key: str) -> str:
        from . import pitch
        return f"{pitch.VETERANS[key][0]:,}"

    def vets_when() -> str:
        from . import pitch
        return pitch.VETERANS_COUNTED

    def programs() -> str:
        from . import pitch
        return ", ".join(pitch.VETERAN_PROGRAMS)

    add("mb.vets_pit", "veterans homeless on one night (HUD, published)", lambda: vets("pit"))
    add("mb.vets_out", "of them unsheltered (HUD, published)", lambda: vets("unsheltered"))
    add("mb.vets_when", "the night those were counted", vets_when)
    add("mb.vets_programs", "the federal programs the project is built to sit beside", programs)

    # -- the dome's own counts, read from the solved topology -------------
    add("mb.long_edges", "edges of the long length", lambda: str(s["long_edges"]))
    add("mb.short_edges", "edges of the short length", lambda: str(s["short_edges"]))
    add("mb.edges", "edges in the hemisphere", lambda: str(s["long_edges"] + s["short_edges"]))
    add("mb.corners", "corners in the hemisphere", lambda: str(s["vertices"]))
    add("mb.five_way", "corners where five triangles meet", lambda: str(s["five_way"]))
    add("mb.six_way", "inside corners where six triangles meet", lambda: str(s["six_way"]))
    add("mb.rim_corners", "corners on the bottom ring", lambda: str(s["rim_vertices"]))
    add("mb.rim_edges", "edges on the bottom ring", lambda: str(s["rim_edges"]))
    add("mb.ratio", "long length over short length", lambda: f"{a / b:.4f}")

    # -- the paper dome ---------------------------------------------------
    long_mm = PAPER_LONG_MM
    short_mm = long_mm * b / a
    apex = 2 * math.degrees(math.asin((long_mm / 2) / short_mm))
    paper_r_mm = long_mm / a
    caps = int(round(q["bab_count"])) // 5
    add("mb.paper_long_mm", "the paper dome's long side, mm", lambda: f"{long_mm:.0f}")
    add("mb.paper_short_mm", "the paper dome's short side, mm", lambda: f"{short_mm:.1f}")
    add("mb.paper_apex_deg", "the point of a short-sided triangle, degrees", lambda: f"{apex:.1f}")
    add("mb.paper_five_deg", "five of those points together, degrees", lambda: f"{5 * apex:.1f}")
    add("mb.paper_gap_deg", "what five points fall short of a full turn, degrees",
        lambda: f"{360 - 5 * apex:.1f}")
    add("mb.paper_caps", "five-triangle caps in the paper dome", lambda: str(caps))
    add("mb.paper_equi", "equal-sided triangles", lambda: f"{q['aaa_count']:.0f}")
    add("mb.paper_iso", "short-sided triangles", lambda: f"{q['bab_count']:.0f}")
    add("mb.paper_diameter_cm", "the paper dome across, cm", lambda: f"{2 * paper_r_mm / 10:.1f}")
    add("mb.paper_height_cm", "the paper dome's height, cm", lambda: f"{paper_r_mm / 10:.1f}")
    add("mb.paper_scale", "how many paper domes across the real one",
        lambda: f"{q['diameter_ft'] * 304.8 / (2 * paper_r_mm):.0f}")
    add("mb.paper_double_cm", "the paper dome across at 200 per cent, cm",
        lambda: f"{4 * paper_r_mm / 10:.1f}")

    # -- the straw dome ---------------------------------------------------
    straw_long = STRAW_LONG_CM
    straw_short = straw_long * b / a
    straw_r = straw_long / a
    add("mb.straw_long_cm", "a long straw, cm", lambda: f"{straw_long:.0f}")
    add("mb.straw_short_cm", "a short straw, cm", lambda: f"{straw_short:.1f}")
    add("mb.straw_trim_cm", "how much shorter a short straw is, cm",
        lambda: f"{straw_long - straw_short:.1f}")
    add("mb.straw_long_count", "long straws", lambda: str(s["long_edges"]))
    add("mb.straw_short_count", "short straws", lambda: str(s["short_edges"]))
    add("mb.straw_diameter_cm", "the straw dome across, cm", lambda: f"{2 * straw_r:.0f}")
    add("mb.straw_height_cm", "the straw dome's height, cm", lambda: f"{straw_r:.0f}")

    # -- small worked figures for the family chapters ---------------------
    trunk = q["trunk_diameter_in"]
    add("mb.trunk_around_in", "string around the reference trunk, inches",
        lambda: f"{math.pi * trunk:.1f}")
    add("mb.timed", "triangles in the timing exercise", lambda: str(TIMED_TRIANGLES))
    add("mb.timed_times", "how many times five makes forty",
        lambda: f"{q['face_count'] / TIMED_TRIANGLES:.0f}")
    add("mb.member_area", "the reference member's section, sq in",
        lambda: f"{q['member_section_in2']:.1f}")
    add("mb.cabin_scale_ft", "the reference dome across, feet",
        lambda: f"{q['diameter_ft']:.1f}")

    # -- standing room on the reference floor, from the one headroom fact --
    def standing() -> tuple[float, float, float]:
        from two_v_demo import dome_advantage as adv

        circle = q["floor_circle_sqft"]
        stand, _box = adv.standing_sqft(circle)
        return adv.FACT["headroom_ft"], circle, stand

    add("mb.head_ft", "the headroom the project calls standing room, ft",
        lambda: f"{standing()[0]:.2f}")
    add("mb.floor_circle_sqft", "the reference floor as a full circle, sq ft",
        lambda: f"{standing()[1]:,.0f}")
    add("mb.stand_sqft", "floor with standing room over it, sq ft",
        lambda: f"{standing()[2]:,.0f}")
    add("mb.stand_pct", "the share of the circle you can stand up on, %",
        lambda: f"{100 * standing()[2] / standing()[1]:.0f}")
    add("mb.stand_across_ft", "the standing circle across, ft",
        lambda: f"{2 * math.sqrt(standing()[2] / math.pi):.1f}")
    add("mb.low_ring_sqft", "the low ring round the wall, sq ft",
        lambda: f"{standing()[1] - standing()[2]:,.0f}")
    add("mb.plan_cm", "the floor plan across at one centimetre to the foot, cm",
        lambda: f"{q['diameter_ft']:.1f}")
    add("mb.plan_stand_cm", "the standing circle on that plan, cm",
        lambda: f"{2 * math.sqrt(standing()[2] / math.pi):.1f}")

    return {t.name: t for t in entries}


@lru_cache(maxsize=1)
def tokens() -> dict[str, Token]:
    return _table()


def resolve(text: str, strict: bool = True) -> str:
    """Fill ``mb.*`` here and everything else through the Complete Edition."""
    from wedge_book import tokens as volume_tokens

    table = tokens()

    def swap(match: re.Match) -> str:
        name = match.group(1)
        if not name.startswith("mb."):
            return match.group(0)
        found = table.get(name)
        if found is None:
            if strict:
                raise KeyError(f"no token {name!r}; mb has {sorted(table)[:12]}...")
            return match.group(0)
        return found.value()

    text = TOKEN.sub(swap, text)
    if TOKEN.search(text):
        text = volume_tokens.resolve(text, strict=strict)
    return text


def report() -> str:
    lines = ["MASTER EDITION TOKENS", ""]
    for name, token in sorted(tokens().items()):
        lines.append(f"  {{{{{name}}}}}  {token.value():>14}   {token.describe}")
    return "\n".join(lines)


def validate_tokens() -> None:
    """The model sizes are the real dome scaled, and the counts close."""
    s = _solved()
    q = s["q"]
    assert s["long_edges"] + s["short_edges"] == round(q["edge_count"]), s
    assert s["vertices"] == round(q["vertex_count"]), s
    assert s["five_way"] * 5 == round(q["bab_count"]), "every short-sided panel sits in one cap"
    assert s["rim_edges"] == round(q["base_sides"]), s
    t = tokens()
    for name, token in t.items():
        assert token.value().strip(), name
    # The paper dome's two sides keep the real dome's ratio.
    ratio = float(t["mb.paper_long_mm"].value()) / float(t["mb.paper_short_mm"].value())
    assert abs(ratio - q["a_factor"] / q["b_factor"]) < 0.003, ratio
    # Five caps' points must fall short of a full turn, or the paper would not curve.
    assert 0 < float(t["mb.paper_gap_deg"].value()) < 30


if __name__ == "__main__":
    validate_tokens()
    print(report())
