"""py -3.12 -m alternating_build.selftest

* every in/out seam leaves exactly the fold; no pattern ever matches two out-wedges;
* the solver's pattern search is exact: an integer program (scipy) over the same costs finds
  no assignment with less extra angle, for every pattern and every ground choice;
* every five-panel vertex has at least one matched seam among its panels (it must: five is odd);
* the uniform dome is untouched: its seam gaps are still sector minus fold.
"""

from __future__ import annotations

import sys

import numpy as np

from . import plan as P


def exact_minimum(p: P.Plan, fixed: dict[int, int]) -> float:
    from scipy.optimize import Bounds, LinearConstraint, milp
    sim = P._solver()
    model, n = p.model, len(p.panels)
    cfg = model.config
    rows, lo, c = [], [], []
    seams = model.seams
    nv = n + 4 * len(seams)
    c = np.zeros(nv)
    for k, s in enumerate(seams):
        for j, (oa, ob) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            gap = sim.seam_face_gap_deg(cfg, P.IN if oa == 0 else P.OUT, P.IN if ob == 0 else P.OUT,
                                        s.inward_a, s.normal_a, s.inward_b, s.normal_b)
            v = n + 4 * k + j
            c[v] = max(0.0, gap - s.fold_angle_deg)
            # y_v >= [x_a == oa and x_b == ob]
            r = np.zeros(nv)
            r[v] = 1
            ra = 1 if oa == 0 else -1
            rb = 1 if ob == 0 else -1
            r[s.face_a] += ra
            r[s.face_b] += rb
            rows.append(r)
            lo.append(1 - (0 if oa == 0 else 1) - (0 if ob == 0 else 1))
    lb, ub = np.zeros(nv), np.ones(nv)
    for f, v in fixed.items():
        lb[f] = ub[f] = v
    res = milp(c, constraints=LinearConstraint(np.array(rows), lo, np.inf), integrality=np.ones(nv), bounds=Bounds(lb, ub))
    return float(res.fun)


def main() -> int:
    fails = 0

    def check(ok: bool, what: str) -> None:
        nonlocal fails
        fails += 0 if ok else 1
        print(("ok   " if ok else "FAIL ") + what)

    for pattern in P.PATTERNS:
        for ground in (("auto", "AAA", "BAB") if pattern == "alternate_ground" else ("auto",)):
            p = P.plan(pattern, ground)
            label = f"{pattern} / ground in {ground}"
            check(all(abs(s.gap_deg - s.fold_deg) < 1e-6 for s in p.seams if s.pair == "in/out"),
                  f"{label}: every in/out seam leaves the fold alone")
            check(p.counts()["out/out"] == 0, f"{label}: no out/out seams ({dict(p.counts())})")
            fixed = {}
            if pattern == "alternate_ground":
                fixed = {i: (0 if p.panels[i].orientation == P.IN else 1) for i in p.bands[1]}
            elif pattern == "alternate_lower":
                lower = p.bands[1] + p.bands[2]
                fixed = {i: (0 if p.panels[i].orientation == P.IN else 1) for i in lower}
            best = exact_minimum(p, fixed)
            check(abs(best - p.total_extra_deg()) < 1e-6, f"{label}: solver {p.total_extra_deg():.4f} deg = "
                                                           f"integer program {best:.4f} deg")
            for r in p.vertex_rings:
                if not r["closes"]:
                    check(r["matched"] >= 1, f"{label}: five-panel vertex at {r['height_in']:.1f} in has "
                                             f"{r['matched']} matched seam(s)")
    sim = P._solver()
    m = sim.build_physical_model(sim.DomeConfig())
    check(not m.panel_orientations and all(abs(s.raw_gap_angle_deg - (45.0 - s.fold_angle_deg)) < 1e-6 for s in m.seams),
          "uniform dome: every seam is still sector minus fold")
    print("selftest:", "PASS" if not fails else f"{fails} FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
