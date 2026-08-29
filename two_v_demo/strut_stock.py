"""The six sections a franken-dome strut can be, and how to draw each.

A hubless dome is 40 closed triangles, each carrying its own three
sticks, so the frame is **120 struts** rather than the 65 a hubbed dome
needs: 55 shared edges end up with two sticks lying face to face, and the
10 rim edges carry one each.  ``2 x 55 + 10 = 120``.

In a franken-dome those 120 sticks are whatever the chainsaw produced, so
the useful thing to show on screen is *which section each one is*.  This
module is the taxonomy and the colour key.

Note on the colour key: the brief gave green to both the full round and
the one-eighth wedge.  Two identical colours in a six-way legend is not a
legend, so the one-eighth wedge is amber here.  Everything else is as
specified.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .geometry import normalize
from .hubless_geometry import hubless_struts, hubless_summary
from .timber import CHAINSAW, draw_timber


@dataclass(frozen=True)
class StockType:
    """One cross-section a strut can be cut to."""

    key: str
    label: str
    glyph: str
    colour: tuple[float, float, float, float]
    sides: int
    """Prism sides used to draw it: 3 is a wedge, 4 square, 14 round."""
    radius_scale: float
    fraction: str
    """How much of a round log this section is."""
    note: str

    @property
    def rgb(self) -> tuple[int, int, int]:
        return (int(self.colour[0] * 255), int(self.colour[1] * 255),
                int(self.colour[2] * 255))


STOCK_TYPES: tuple[StockType, ...] = (
    StockType("round", "FULL ROUND", "O", (0.32, 0.85, 0.45, 1.0), 14, 1.00,
              "1/1", "The log as it fell. No milling at all."),
    StockType("half", "HALF ROUND", "D", (0.28, 0.60, 0.98, 1.0), 8, 0.86,
              "1/2", "One rip down the middle. Two struts from one log."),
    StockType("quarter", "QUARTER WEDGE", "L", (0.94, 0.28, 0.30, 1.0), 4, 0.72,
              "1/4", "Two rips. Four struts, and a flat face to screw to."),
    StockType("eighth", "EIGHTH WEDGE", "<", (1.00, 0.70, 0.20, 1.0), 3, 0.62,
              "1/8", "Three rips. Eight thin struts out of one log."),
    StockType("square", "SQUARE / RECT", "#", (0.16, 0.16, 0.18, 1.0), 4, 0.80,
              "milled", "Bought or milled square stock."),
    StockType("metal", "METAL TUBE / BOX", "T", (0.62, 0.66, 0.72, 1.0), 10, 0.58,
              "steel", "Salvaged tube or box section, where wood would not do."),
)

STOCK_BY_KEY = {item.key: item for item in STOCK_TYPES}


def stock_for(index: int) -> StockType:
    """Which section this strut happens to be.

    Deterministic from the strut index, so a given stick is the same
    section in every frame and every render. The mix is weighted toward
    the cheap cuts, because that is what a self-harvested pile actually
    looks like: mostly halves and quarters, a few whole logs, and metal
    only where nothing else would serve.
    """
    weights = (("round", 3), ("half", 5), ("quarter", 6),
               ("eighth", 3), ("square", 2), ("metal", 1))
    table: list[str] = []
    for key, weight in weights:
        table.extend([key] * weight)
    scrambled = (index * 7919 + (index // 3) * 104729) % len(table)
    return STOCK_BY_KEY[table[scrambled]]


@dataclass(frozen=True)
class StockTally:
    """How many struts of each section the frame needs."""

    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def share(self, key: str) -> float:
        return self.counts.get(key, 0) / max(1, self.total)

    def logs_needed(self) -> float:
        """Round logs consumed, given how many struts each section yields.

        A full round is one log per strut; a half is two struts per log; a
        quarter is four; an eighth is eight. Square and metal come from
        somewhere else and are not counted against the woodpile.
        """
        per_log = {"round": 1, "half": 2, "quarter": 4, "eighth": 8}
        total = 0.0
        for key, count in self.counts.items():
            if key in per_log:
                total += count / per_log[key]
        return total


def tally() -> StockTally:
    """Count the sections across the whole 120-strut hubless frame."""
    counts: dict[str, int] = {item.key: 0 for item in STOCK_TYPES}
    for index in range(len(hubless_struts())):
        counts[stock_for(index).key] += 1
    return StockTally(counts)


def draw_stock_strut(batch, a, b, index: int, radius: float = 0.095,
                     coded: bool = True) -> StockType:
    """Draw one strut in its own section, coloured by type if asked.

    With ``coded`` off it draws in natural timber tone, which is what the
    frame actually looks like; with it on every stick is flooded with its
    legend colour, which is what makes the doubling visible.
    """
    stock = stock_for(index)
    draw_timber(batch, a, b, radius * stock.radius_scale, index, CHAINSAW,
                sides=stock.sides,
                tint=stock.colour if coded else None)
    return stock


def stock_report() -> str:
    """A portable audit of the section mix."""
    summary = hubless_summary()
    counts = tally()
    lines = ["FRANKEN-DOME STRUT STOCK - CALCULATION AUDIT", ""]
    lines.append(f"  triangles              {summary.triangles}")
    lines.append(f"  struts (3 per triangle){summary.struts:>4}")
    lines.append(f"  shared edges x2 struts {summary.doubled_edges}")
    lines.append(f"  rim edges   x1 strut   {summary.rim_edges}")
    lines.append(f"  check 2x{summary.doubled_edges} + {summary.rim_edges} "
                 f"= {summary.strut_check}")
    lines.append("")
    for item in STOCK_TYPES:
        count = counts.counts[item.key]
        lines.append(
            f"  {item.glyph}  {item.label:<17} {item.fraction:<7} "
            f"x{count:<4} {counts.share(item.key) * 100:5.1f}%   {item.note}")
    lines.append("")
    lines.append(f"  total struts           {counts.total}")
    lines.append(f"  round logs consumed    {counts.logs_needed():.1f}")
    return "\n".join(lines)


def validate_stock() -> None:
    """The tally must add up to the frame, and the key must be readable."""
    summary = hubless_summary()
    counts = tally()
    assert counts.total == summary.struts == 120, (counts.total, summary.struts)
    assert summary.strut_check == summary.struts

    # Every section must actually appear, or the legend lies.
    for item in STOCK_TYPES:
        assert counts.counts[item.key] > 0, item.key

    # The colour key has to be a key: six distinguishable colours and six
    # distinct glyphs. The brief gave green twice; this is the check that
    # keeps that from silently coming back.
    colours = [item.colour for item in STOCK_TYPES]
    assert len(set(colours)) == len(colours), "two sections share a colour"
    glyphs = [item.glyph for item in STOCK_TYPES]
    assert len(set(glyphs)) == len(glyphs), "two sections share a glyph"
    keys = [item.key for item in STOCK_TYPES]
    assert len(set(keys)) == len(keys)

    # Assignment must be stable across calls.
    first = [stock_for(index).key for index in range(120)]
    assert first == [stock_for(index).key for index in range(120)]

    # Fewer logs than struts, because most sections split a log.
    assert 0 < counts.logs_needed() < counts.total, counts.logs_needed()
