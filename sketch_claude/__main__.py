"""py -3.12 -m sketch_claude {serve|plans|showcase|selftest} -- see the package docstring."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def selftest() -> None:
    import tempfile
    from dataclasses import replace

    from sketch_claude import model as M
    from sketch_claude import plans, render as R

    for line in M.validate():
        print("ok:", line)
    for spec in (M.Spec(frequency=2, cut="1/2", diameter_m=4.0), M.Spec(diameter_m=6.0), M.Spec(door=False, skin="clear")):
        m = M.build(spec)
        t = m.tables
        assert t["whole"] + t["partial"] >= 1 and t["stick_count"] > 0
        print(f"ok: {spec.title}: {t['whole']} whole + {t['partial']} partial panels, {t['stick_count']} sticks, "
              f"{len(t['sticks'])} cuts" + (f" ({len(t['warnings'])} notes)" if t["warnings"] else ""))
    m = M.build()
    pts = [p.mesh.verts for p in m.pieces if p.tag == "frame"]
    import numpy as np
    cam = R.framed(np.vstack(pts), (-0.6, 1.0, -0.4), width=320, height=200)
    img = R.render(m, cam, R.SKETCH, R.View(tags=("frame", "base", "door")), ss=1)
    a = np.asarray(img)
    assert a.std() > 5, "the still is blank"
    print("ok: a still renders")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "one.pdf"
        ps = plans.PlanSet(m, out, plans.Shots(m, Path(d)))
        plans.s_panel_dims(ps)
        plans.s_cutlist(ps)
        ps.save()
        assert out.stat().st_size > 5000
    print("ok: a plan sheet prints")
    print("sketch_claude selftest OK")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sketch_claude", description="Dome Sketch (sketch-claude): model a panel dome, draw its plans.")
    ap.add_argument("command", nargs="?", default="serve", choices=("serve", "plans", "showcase", "selftest"))
    ap.add_argument("--spec", default="{}", help="the dome as JSON (see model.Spec); defaults to the reference dome")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    from sketch_claude import model as M
    spec = M.Spec.from_dict(json.loads(a.spec))
    if a.command == "selftest":
        selftest()
        return 0
    if a.command == "plans":
        from sketch_claude.plans import build_plans
        print(f"drawing the plan set for {spec.title}", flush=True)
        out = build_plans(spec)
        print(f"OUTPUT {out.relative_to(ROOT).as_posix()}", flush=True)
        return 0
    if a.command == "showcase":
        from sketch_claude.showcase import build_showcase
        print(f"rendering the showcase for {spec.title}", flush=True)
        out = build_showcase(spec)
        print(f"OUTPUT {out.relative_to(ROOT).as_posix()}", flush=True)
        return 0
    from sketch_claude import server
    httpd = server.serve(a.port)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    print(f"Dome Sketch ({server.TAG}) is at {url}  (Ctrl+C to stop)", flush=True)
    if not a.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
