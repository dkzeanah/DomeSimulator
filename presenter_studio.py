"""Presenter Studio — text-to-explainer-video for 3-D world models.

Run a presentation live, export it to a narrated MP4, or generate a
skeleton presentation from a plain-English production brief.

Examples:
    py -3.12 presenter_studio.py --demo airflow
    py -3.12 presenter_studio.py --demo airflow --export dome_airflow.mp4
    py -3.12 presenter_studio.py --demo airflow --shots 5,40,90
    py -3.12 presenter_studio.py --script my_presentation.json
    py -3.12 presenter_studio.py --prompt "seven scenes each of three \
shots, a macro, close up and ultra wide shot of elements 1, 2 and 3" \
--environment "tropical beach at dusk" --export brief.mp4
    py -3.12 presenter_studio.py --selftest
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from presenter.script import Presentation
from presenter.prompt import parse_brief, parse_environment


DEMOS = {
    "airflow": "presentations.airflow_dome",
}


def load_presentation(args) -> Presentation:
    if args.demo:
        module = importlib.import_module(DEMOS[args.demo])
        pres = module.build()
    elif args.script:
        path = Path(args.script)
        if path.suffix.lower() == ".json":
            pres = Presentation.from_json(path)
        else:
            spec = importlib.util.spec_from_file_location("user_pres", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pres = module.build()
    elif args.prompt:
        focus = tuple(args.focus.split(",")) if args.focus else ()
        pres = parse_brief(args.prompt, args.environment or "", focus)
        # a brief needs something on stage: give it the dome world
        from dataclasses import replace
        default_world = (("dome", {"radius": 4.8}),
                         ("plenum", {"radius": 4.8}),
                         ("blower", {"radius": 4.8, "spin": 3.0}),
                         ("airflow", {"radius": 4.8, "intensity": 0.7}))
        pres = replace(pres, scenes=tuple(
            replace(s, world=default_world) for s in pres.scenes))
    else:
        raise SystemExit("choose --demo, --script, or --prompt "
                         "(see --help)")
    return pres


def selftest() -> int:
    from presenter.prompt import parse_environment, parse_brief
    env = parse_environment("on a beach at a lake in the desert")
    assert env.terrain == "sand" and env.water == "lake" and env.shoreline
    env2 = parse_environment("tropical tsunami ridden environment")
    assert env2.tsunami and env2.palms > 0 and env2.sky == "storm"
    env3 = parse_environment("in the snow at night")
    assert env3.weather == "snow" and env3.sky == "night"
    env4 = parse_environment("tornado ridden environment")
    assert env4.tornado
    brief = parse_brief(
        "I want a video with seven scenes each of three shots, "
        "a close up, macro and ultra wide shot of elements 1, 2 and 3",
        focus_names=("dome", "plenum", "blower"))
    assert len(brief.scenes) == 7
    assert all(len(s.shots) == 3 for s in brief.scenes)
    lenses = [shot.lens for shot in brief.scenes[0].shots]
    assert lenses == ["portrait", "macro", "ultrawide"], lenses
    focuses = [shot.focus for shot in brief.scenes[0].shots]
    assert focuses == ["dome", "plenum", "blower"], focuses

    from presentations.airflow_dome import build
    pres = build()
    pres.validate()
    round_trip = Path("presenter_output/airflow.json")
    round_trip.parent.mkdir(exist_ok=True)
    pres.to_json(round_trip)
    again = Presentation.from_json(round_trip)
    again.validate()
    assert abs(again.duration - pres.duration) < 1e-6

    from presenter.world import build_frame
    for t in (0.0, 3.7, 12.2):
        scene = pres.scenes[0]
        o, tr, targets = build_frame(
            parse_environment(scene.environment), list(scene.world), t,
            scene.shots[0], 0.4)
        assert o.v and tr.v and "dome" in targets and "grille" in targets
    print("presenter selftest OK "
          f"({len(pres.all_shots())} shots, {pres.duration:.0f}s scripted)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", choices=sorted(DEMOS))
    parser.add_argument("--script", help="presentation .json or .py")
    parser.add_argument("--prompt", help="production brief text")
    parser.add_argument("--environment", help="environment prompt for "
                        "--prompt mode")
    parser.add_argument("--focus", help="comma list of focusable object "
                        "names for --prompt mode")
    parser.add_argument("--export", metavar="MP4")
    parser.add_argument("--no-narration", action="store_true")
    parser.add_argument("--fps", type=int, default=None)
    parser.add_argument("--size", default=None,
                        help="WxH, e.g. 1280x720")
    parser.add_argument("--shots", help="comma-separated times to render "
                        "PNG stills instead of running")
    parser.add_argument("--save-json", metavar="PATH",
                        help="write the presentation as JSON and exit")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    pres = load_presentation(args)
    if args.save_json:
        pres.to_json(Path(args.save_json))
        print(f"saved {args.save_json}")
        return 0

    size = None
    if args.size:
        w, h = args.size.lower().split("x")
        size = (int(w), int(h))

    from presenter.engine import PresenterApp
    if args.shots:
        app = PresenterApp(pres, headless=True, size=size or (1600, 900))
        out = Path("presenter_output")
        out.mkdir(exist_ok=True)
        for value in args.shots.split(","):
            t = float(value)
            app.render(t, present=False)
            path = out / f"shot_{t:07.1f}s.png"
            app.screenshot(path)
            print(f"saved {path}")
        return 0
    if args.export:
        app = PresenterApp(pres, headless=True, size=size)
        app.export(Path(args.export), fps=args.fps,
                   narration=not args.no_narration)
        return 0
    app = PresenterApp(pres, headless=False, windowed=not args.fullscreen,
                       size=size or (1600, 900))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
