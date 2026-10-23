"""py -3.12 -m wedge_builder.selftest -- every orientation and seam join at the edges of LIMITS.

Solves each case, runs its self-checks and builds its PDF to a temporary folder; then
checks that bad requests are refused with a reason, and that a design's id ignores its label.
"""

from __future__ import annotations

import itertools
import sys
import tempfile
import time
from pathlib import Path

from . import design, pdf


def main() -> int:
    lo_d, hi_d = design.LIMITS["diameter_ft"]
    lo_l, hi_l = design.LIMITS["log_in"]
    cases = [(lo_d, lo_l, 8.0), (19.4, 10.0, 16.0), (hi_d, hi_l, design.LIMITS["log_ft"][1]), (12.0, 18.0, 12.0)]
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for (dia, log, length), o, j in itertools.product(cases, design.ORIENTATIONS, design.SEAM_JOINS):
            req = design.Request(dia, log, length, o, j)
            t = time.time()
            try:
                d = design.solve(req)
                bad = [c[0] for c in d.checks if not c[1]]
                if bad:
                    raise AssertionError("; ".join(bad))
                out = pdf.build(d, Path(tmp) / f"{req.key()}.pdf")
                size = out.stat().st_size
                print(f"ok   {dia:5g} ft  {log:4g} in  {length:4g} ft  {o:15s} {j:13s} {len(d.families)} families, "
                      f"{len(d.logs)} logs, {size / 1024:,.0f} KB, {time.time() - t:.1f}s")
            except ValueError as e:
                # a refusal with a reason is a correct answer (logs too short for this size)
                print(f"no   {dia:5g} ft  {log:4g} in  {length:4g} ft  {o:15s} {j:13s} {e}")
            except Exception as e:  # noqa: BLE001 -- the point is to report any crash
                failures += 1
                print(f"FAIL {dia:5g} ft  {log:4g} in  {length:4g} ft  {o:15s} {j:13s} {type(e).__name__}: {e}")
    for bad in ({"diameter_ft": 2, "log_in": 10, "log_ft": 16}, {"diameter_ft": 20, "log_in": "x", "log_ft": 16},
                {"diameter_ft": 20, "log_in": 10, "log_ft": 16, "orientation": "sideways"}, {"diameter_ft": 20, "log_in": 10}):
        try:
            design.Request.from_json(bad)
            failures += 1
            print(f"FAIL accepted {bad}")
        except ValueError as e:
            print(f"ok   refused {bad}: {e}")
    try:
        design.solve(design.Request(40.0, 10.0, 4.0))
        failures += 1
        print("FAIL a 40 ft dome from 4 ft logs was accepted")
    except ValueError as e:
        print(f"ok   refused short logs: {e}")
    a = design.Request.from_json({"diameter_ft": 20, "log_in": 10, "log_ft": 16, "label": "one"})
    b = design.Request.from_json({"diameter_ft": 20.0, "log_in": 10.0, "log_ft": 16.0, "label": "two"})
    if a.key() != b.key():
        failures += 1
        print("FAIL the design id depends on the label or on int/float")
    print("selftest:", "PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
