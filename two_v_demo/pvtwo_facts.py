"""Measured facts for the The Twenty Dollar Pine, Part Two lesson.

Every number the lesson puts on screen is computed here and proved in
:func:`validate_pvtwo`.  If a value cannot be computed from something,
it is an external constant: name it, source it, and print it in the
report so a viewer can see which figures are derived and which are
borrowed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache


# --- external constants ------------------------------------------------
# Anything this module takes on authority rather than deriving.  Keep the
# list short and keep it honest; it is the first thing a sceptic reads.

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("cord_pickup_usd", 275.0, "USD per cord",
     "Tuscaloosa-area firewood seller listing"),
)


@dataclass(frozen=True)
class PvtwoItem:
    """One measured thing. Replace with whatever this subject is about."""

    name: str
    size: float
    count: int

    @property
    def total(self) -> float:
        return self.size * self.count


@lru_cache(maxsize=1)
def pvtwo_items() -> tuple[PvtwoItem, ...]:
    """Compute the subject's parts. This is where the real work goes."""
    return tuple(
        PvtwoItem(name=f"CLASS-{index + 1}",
                  size=1.0 / (index + 1),
                  count=(index + 1) * 4)
        for index in range(4)
    )


@lru_cache(maxsize=1)
def pvtwo_summary() -> dict:
    items = pvtwo_items()
    return {
        "classes": len(items),
        "parts": sum(item.count for item in items),
        "total": sum(item.total for item in items),
        "largest": max(item.size for item in items),
    }


def pvtwo_report() -> str:
    """A portable audit of every claim the lesson makes."""
    summary = pvtwo_summary()
    lines = ["THE TWENTY DOLLAR PINE, PART TWO - CALCULATION AUDIT", ""]
    for key, value in summary.items():
        lines.append(f"  {key:<10} {value}")
    lines.append("")
    for item in pvtwo_items():
        lines.append(f"  {item.name:<10} size {item.size:8.4f}  "
                     f"x{item.count:<4} total {item.total:8.4f}")
    lines.append("")
    lines.append("external constants this model takes on authority:")
    for name, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {name:<22} {value:g} {units:<14} {source}")
    return "\n".join(lines)


def validate_pvtwo() -> None:
    """Prove the model before any of its numbers reach a screen."""
    items = pvtwo_items()
    assert items, "there must be at least one item"
    assert len({item.name for item in items}) == len(items), "duplicate names"
    for item in items:
        assert item.size > 0.0, item
        assert item.count > 0, item
        assert math.isclose(item.total, item.size * item.count), item

    summary = pvtwo_summary()
    assert summary["classes"] == len(items)
    assert summary["parts"] == sum(item.count for item in items)
    assert summary["largest"] == max(item.size for item in items)
    # Every external constant must be named and sourced.
    for name, _, units, source in EXTERNAL_CONSTANTS:
        assert name and units and source, name
