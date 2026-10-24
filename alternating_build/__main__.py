"""py -3.12 -m alternating_build [--pattern alternate_ground] [--ground-in auto|AAA|BAB] [--log-in 12]

Prints the plan ground up: each band in walking order, which way each panel points, and
every seam it closes with the angle its key fills. The cut list for the same dome:
py -3.12 -m wedge_builder --pattern alternate_ground ...
"""

from __future__ import annotations

import argparse
import sys

from . import plan as P

SHAPE = {"AAA": "equilateral (three long A sides)", "BAB": "isosceles (one long A side, two short B sides)"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pattern", default="alternate_ground", choices=list(P.PATTERNS))
    ap.add_argument("--ground-in", default="auto", choices=["auto", "AAA", "BAB"])
    ap.add_argument("--log-in", type=float)
    a = ap.parse_args(argv)
    p = P.plan(a.pattern, a.ground_in, log_in=a.log_in)
    for line in P.explain(p):
        print(line)
    if p.pattern == "alternate_ground":
        other = "AAA" if p.ground_in == "BAB" else "BAB"
        q = P.plan(a.pattern, other, log_in=a.log_in)
        print(f"  (Had the {other} ground panels pointed in instead: {len(q.matched())} matched seams, "
              f"{q.total_extra_deg():.2f} deg extra in all.)")
        print(f"  How to tell them apart: AAA is {SHAPE['AAA']}; BAB is {SHAPE['BAB']}.")
    for b in sorted(p.bands):
        print(f"\nBAND {b} -- walk round it in this order")
        for panel in p.panels_in(b):
            closes = [s for s in p.seams if s.band == b and panel.index in (s.a, s.b)]
            words = ", ".join(f"{s.seam_id} {s.pair} {s.gap_deg:.2f} deg" for s in closes) or "no seams yet"
            print(f"  {panel.walk:2d}. panel {panel.index + 1:2d} {panel.face_type}  {P.WORD[panel.orientation]:3s}  {words}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
