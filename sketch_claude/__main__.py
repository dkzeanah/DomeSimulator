"""py -3.12 -m sketch_claude {serve|plans|showcase|episode|storytime|selftest} -- see the package docstring
(storytime: sketch_claude/storytime_render.py)."""

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
    # the episodes: every beat a kind the engine plays, every speaker in the cast
    series = json.loads((ROOT / "sketch_claude" / "episodes" / "series.json").read_text(encoding="utf-8"))
    kinds = {"scene", "line", "walk", "act", "face", "cam", "wait", "sfx", "music", "view", "build", "lower", "figure", "card", "gag", "meme", "credits",
             "thought", "vision", "expr", "prop", "mood", "flash", "place"}
    for f in sorted((ROOT / "sketch_claude" / "episodes").glob("s[0-9][0-9]e[0-9][0-9].json")):
        ep = json.loads(f.read_text(encoding="utf-8"))
        lines = 0
        flat = []
        for b in ep["beats"]:
            flat.append(b)
            flat.extend(b.get("beats", []) if b.get("k") == "vision" else [])
        for i, b in enumerate(flat):
            assert b["k"] in kinds, f"{f.name} beat {i}: unknown kind {b['k']}"
            for key in ("who",):
                if key in b:
                    assert b[key] in series["cast"], f"{f.name} beat {i}: {b[key]} is not in the cast"
            for who in (b.get("place") or {}):
                assert who in series["cast"], f"{f.name} beat {i}: {who} is not in the cast"
            lines += b["k"] == "line"
        print(f"ok: {f.stem}: {len(flat)} beats, {lines} lines, every speaker in the cast")
    print("sketch_claude selftest OK")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sketch_claude", description="Dome Sketch (sketch-claude): model a panel dome, draw its plans.")
    ap.add_argument("command", nargs="?", default="serve", choices=("serve", "plans", "showcase", "episode", "storytime", "selftest"))
    ap.add_argument("--draft", action="store_true", help="episode: a rehearsal render, kept in tmp/ instead of the library")
    ap.add_argument("--episode", default="s01e01", help="episode: which one (sketch_claude/episodes/<id>.json)")
    ap.add_argument("--spec", default="{}", help="the dome as JSON (see model.Spec); defaults to the reference dome")
    ap.add_argument("story", nargs="?", default="my-own-home", help="storytime: which bedtime story (its slug)")
    ap.add_argument("--site", help="storytime: read the story the Story Studio published on this site, not the baked copy")
    ap.add_argument("--pages", help="storytime: a run of pages, e.g. 0-3 (a rehearsal)")
    ap.add_argument("--stills", action="store_true", help="storytime: one still per page instead of the film")
    ap.add_argument("--no-phone", action="store_true", help="storytime: the landscape cut only")
    ap.add_argument("--finish", help="storytime: add the missing phone cut and release to this deliverables folder")
    ap.add_argument("--private", action="store_true", help="storytime: a private story (narration and film in website/private, gitignored)")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--page", default="", help="serve: open this page instead of the modeller (director)")
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
    if a.command == "episode":
        from sketch_claude.episode_server import render_headless
        print(f"rendering episode {a.episode} in a headless browser", flush=True)
        out = render_headless(spec, draft=a.draft, episode=a.episode)
        video = ROOT / out["video"] if out.get("video") else None
        if not out.get("folder") or not video or not video.exists() or video.stat().st_size < 1000:
            print(f"the render failed: {out}", flush=True)
            return 1
        for e in out.get("errors", []):
            print(f"warning: {e}", flush=True)
        print(f"OUTPUT {out['folder']}", flush=True)
        return 0
    if a.command == "storytime":
        from sketch_claude import storytime_render as ST
        if a.stills:
            out = ST.stills(a.story, a.site, private=a.private)
            print(f"OUTPUT {out.relative_to(ROOT).as_posix()}", flush=True)
            return 0
        if a.finish:
            out = ST.finish(Path(a.finish), a.story, a.site)
            print(f"OUTPUT {out['folder']}", flush=True)
            return 0
        pages = tuple(int(x) for x in a.pages.split("-")) if a.pages else None
        out = ST.render(a.story, a.site, pages=pages, draft=a.draft, phone=not a.no_phone, private=a.private)
        print(f"OUTPUT {out['folder']}", flush=True)
        return 0
    if a.command == "showcase":
        from sketch_claude.showcase import build_showcase
        print(f"rendering the showcase for {spec.title}", flush=True)
        out = build_showcase(spec)
        print(f"OUTPUT {out.relative_to(ROOT).as_posix()}", flush=True)
        return 0
    from sketch_claude import server
    httpd = server.serve(a.port)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/{a.page}"
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
