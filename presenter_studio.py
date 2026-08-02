"""Presenter Studio — text-to-explainer-video for 3-D world models.

Run a presentation live, export it to a narrated MP4, or generate a
skeleton presentation from a plain-English production brief.

Launch and configure this from the consolidated launcher
(``py -3.12 launcher.py``), which exposes every option below (demo
choice / script path / prompt text / environment / focus list / export
path / narration toggle / fps / size / stills times / fullscreen /
self-test) as GUI fields. Run directly with no launcher ticket present
and it defaults to the airflow demo, live, fullscreen.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import launcher_common as _lc
from presenter.script import Presentation
from presenter.prompt import parse_brief, parse_environment


DEMOS = {
    "airflow": "presentations.airflow_dome",
    "housing_case": "presentations.dome_housing_case",
}


def load_presentation(cfg: dict) -> Presentation:
    demo = cfg.get("demo")
    script = cfg.get("script")
    prompt = cfg.get("prompt")
    if demo:
        module = importlib.import_module(DEMOS[demo])
        pres = module.build()
    elif script:
        path = Path(script)
        if path.suffix.lower() == ".json":
            pres = Presentation.from_json(path)
        else:
            spec = importlib.util.spec_from_file_location("user_pres", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pres = module.build()
    elif prompt:
        focus = tuple(cfg["focus"].split(",")) if cfg.get("focus") else ()
        pres = parse_brief(prompt, cfg.get("environment") or "", focus)
        # a brief needs something on stage: give it the dome world
        from dataclasses import replace
        default_world = (("dome", {"radius": 4.8}),
                         ("plenum", {"radius": 4.8}),
                         ("blower", {"radius": 4.8, "spin": 3.0}),
                         ("airflow", {"radius": 4.8, "intensity": 0.7}))
        pres = replace(pres, scenes=tuple(
            replace(s, world=default_world) for s in pres.scenes))
    else:
        # no launcher ticket / nothing specified: default demo
        module = importlib.import_module(DEMOS["airflow"])
        pres = module.build()
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

    from presentations.dome_housing_case import build as build_housing
    housing = build_housing()
    housing.validate()
    round_trip2 = Path("presenter_output/housing_case.json")
    round_trip2.parent.mkdir(exist_ok=True)
    housing.to_json(round_trip2)
    again2 = Presentation.from_json(round_trip2)
    again2.validate()
    assert abs(again2.duration - housing.duration) < 1e-6
    # every shot's declared focus must resolve to a real target at the
    # start, middle, and end of the shot — a target only registered once
    # something is "revealed" would leave the camera with nowhere to look
    # for the first instant of that shot.
    for scene in housing.scenes:
        env = parse_environment(scene.environment)
        for shot in scene.shots:
            for progress in (0.0, 0.5, 1.0):
                o, tr, targets = build_frame(
                    env, list(scene.world), 1.0, shot, progress)
                assert o.v or tr.v, (scene.slug, shot.slug, "no geometry")
                if shot.focus:
                    assert shot.focus in targets, (
                        scene.slug, shot.slug, shot.focus, "no such target")
    print("presenter selftest OK "
          f"({len(pres.all_shots())} shots, {pres.duration:.0f}s scripted; "
          f"housing case {len(housing.all_shots())} shots, "
          f"{housing.duration:.0f}s scripted)")
    return 0


def main() -> int:
    cfg = _lc.consume_config("presenter")

    if cfg.get("action") == "selftest":
        return selftest()

    pres = load_presentation(cfg)
    if cfg.get("save_json"):
        pres.to_json(Path(cfg["save_json"]))
        print(f"saved {cfg['save_json']}")
        return 0

    size = None
    if cfg.get("size"):
        size = _lc.parse_size(cfg["size"])

    from presenter.engine import PresenterApp
    if cfg.get("action") == "shots" and cfg.get("shots"):
        app = PresenterApp(pres, headless=True, size=size or (1600, 900))
        out = Path("presenter_output")
        out.mkdir(exist_ok=True)
        for value in str(cfg["shots"]).split(","):
            if not value.strip():
                continue
            t = float(value)
            app.render(t, present=False)
            path = out / f"shot_{t:07.1f}s.png"
            app.screenshot(path)
            print(f"saved {path}")
        return 0
    if cfg.get("action") == "export" and cfg.get("export"):
        app = PresenterApp(pres, headless=True, size=size)
        app.export(Path(cfg["export"]), fps=cfg.get("fps"),
                   narration=not cfg.get("no_narration", False))
        return 0
    app = PresenterApp(pres, headless=False,
                       windowed=not cfg.get("fullscreen", False),
                       size=size or (1600, 900))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
