"""py -3.12 -m wedge_builder --diameter-ft 19.4 --log-in 10 --log-ft 16 [--orientation ...] [--out x.pdf]

Without --out the PDF is a new numbered output in deliverables/ (medialib), never over an old one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import design, pdf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diameter-ft", type=float, required=True)
    ap.add_argument("--log-in", type=float, required=True, help="log diameter at the small end, inches")
    ap.add_argument("--log-ft", type=float, required=True, help="usable straight log length, feet")
    ap.add_argument("--orientation", default="point_dome_in", choices=list(design.ORIENTATIONS))
    ap.add_argument("--seam-join", default="raw_trapezoid", choices=list(design.SEAM_JOINS))
    ap.add_argument("--label", default="")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    try:
        req = design.Request.from_json({"diameter_ft": a.diameter_ft, "log_in": a.log_in, "log_ft": a.log_ft,
                                        "orientation": a.orientation, "seam_join": a.seam_join, "label": a.label})
        d = design.solve(req)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    out = a.out
    if out is None:
        import medialib
        out = medialib.new_path("wedge-cutlist.pdf")
    print(pdf.build(d, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
