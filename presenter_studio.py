"""Presenter Studio — text-to-explainer-video for 3-D world models.

Four ways to use it:

* **compose** — open the Scene Composer and build a movie from nothing:
  drag clips on a timeline, drop domes, doors, stoves and appliances onto
  a stage, write the narration, and render it, all in one window,
* **run** — play a finished presentation live,
* **export** — render it to a narrated MP4, with a choice of how much
  writing is burned into the picture (including none at all),
* **export_all** — render every built-in presentation in one go.

Launch and configure this from the consolidated launcher
(``py -3.12 launcher.py``), which exposes every option below as GUI
fields. Run directly with no launcher ticket present and it opens the
Scene Composer on a blank movie.
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
    "case_manufacturing": "presentations.dome_case_manufacturing",
    "case_bare_shell": "presentations.dome_case_bare_shell",
    "case_more_room": "presentations.dome_case_more_room",
    "case_triangles": "presentations.dome_case_triangles",
    "case_benchmark": "presentations.dome_case_benchmark",
    "case_energy": "presentations.dome_case_energy",
    "case_resilience": "presentations.dome_case_resilience",
    "case_financing": "presentations.dome_case_financing",
    "case_utility_core": "presentations.dome_case_utility_core",
    "case_market_fit": "presentations.dome_case_market_fit",
    "accessibility": "presentations.dome_accessibility",
}


def load_presentation(cfg: dict) -> Presentation:
    demo = cfg.get("demo")
    script = cfg.get("script")
    prompt = cfg.get("prompt")
    if cfg.get("action") == "compose" and not (demo or script or prompt):
        # Composing from scratch means starting with an empty stage, not
        # with somebody else's movie to unpick.
        from presenter.edit import blank_presentation
        return blank_presentation(cfg.get("title") or "Untitled")
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
    # Every dome_case_* demo (the ten-part convergent-argument series):
    # build, validate, and the same target/geometry sweep as the housing
    # case above, keyed off DEMOS itself so this can't drift out of sync
    # with what's actually registered.
    total_case_shots = 0
    for key, module_name in DEMOS.items():
        if not key.startswith("case_"):
            continue
        module = importlib.import_module(module_name)
        case_pres = module.build()
        case_pres.validate()
        for scene in case_pres.scenes:
            env = parse_environment(scene.environment)
            for shot in scene.shots:
                for progress in (0.0, 0.5, 1.0):
                    o, tr, targets = build_frame(
                        env, list(scene.world), 1.0, shot, progress)
                    assert o.v or tr.v, (key, scene.slug, shot.slug,
                                         "no geometry")
                    if shot.focus:
                        assert shot.focus in targets, (
                            key, scene.slug, shot.slug, shot.focus,
                            "no such target")
        total_case_shots += len(case_pres.all_shots())

    # ---- the object library ------------------------------------------
    # Every catalogued object must have an emitter, every emitter must be
    # catalogued, and each one must actually put geometry on the stage and
    # register something for the camera to look at. Without the last
    # check a piece could be placeable but impossible to point a camera
    # at, which is only discoverable by eye.
    from presenter.library import (CATEGORIES, OBJECT_SPECS, SPEC_BY_KEY,
                                   defaults_for)
    from presenter.world import all_emitters
    emitters = all_emitters()
    missing = [s.key for s in OBJECT_SPECS if s.key not in emitters]
    orphan = [k for k in emitters if k not in SPEC_BY_KEY]
    assert not missing, f"catalogued but not buildable: {missing}"
    assert not orphan, f"buildable but not catalogued: {orphan}"
    plain = parse_environment("")
    for spec in OBJECT_SPECS:
        o, tr, targets = build_frame(plain, [(spec.key, defaults_for(spec.key))],
                                     1.3)
        assert o.v or tr.v, f"{spec.key} drew nothing"
        assert [k for k in targets if k != "origin"], \
            f"{spec.key} registered nothing to look at"
        for param in spec.params:
            # A knob the editor would show must survive being pushed to
            # either stop, or a slider drag could crash the editor.
            for value in (param.low, param.high):
                params = defaults_for(spec.key)
                params[param.key] = param.clamp(value)
                o2, tr2, _t = build_frame(plain, [(spec.key, params)], 0.9)
                assert o2.v or tr2.v, (spec.key, param.key, value)

    # ---- the accessibility presentation ------------------------------
    # It leans on the moving wheelchair and the ramp/hoist props, so it
    # gets the same start/middle/end target sweep the housing case gets:
    # every declared focus must resolve to a real target, and every frame
    # must draw something.
    access = importlib.import_module(DEMOS["accessibility"]).build()
    access.validate()
    for scene in access.scenes:
        env = parse_environment(scene.environment)
        for shot in scene.shots:
            for progress in (0.0, 0.5, 1.0):
                o, tr, targets = build_frame(env, list(scene.world), 1.0,
                                             shot, progress)
                assert o.v or tr.v, (scene.slug, shot.slug, "no geometry")
                if shot.focus:
                    assert shot.focus in targets, (
                        scene.slug, shot.slug, shot.focus, "no such target")

    # ---- editing the document ----------------------------------------
    from presenter import edit as ED
    blank = ED.blank_presentation("Scratch")
    blank.validate()
    assert ED.shot_count(blank) == 1 and len(blank.scenes) == 1
    # A presentation can never be emptied out from under the engine.
    assert ED.delete_shot(blank, 0) is blank
    assert ED.delete_scene(blank, 0) is blank
    doc = ED.add_scene(blank, 0)
    for _ in range(2):
        doc = ED.add_shot(doc, 0)
    for _ in range(2):
        doc = ED.add_shot(doc, ED.shot_count(doc) - 1)
    for i in range(ED.shot_count(doc)):
        doc = ED.set_shot(doc, i, slug=f"s{i}")
    names = sorted(s.slug for sc in doc.scenes for s in sc.shots)
    # Dragging a clip anywhere on the timeline must never lose or
    # duplicate a shot, including across a scene boundary.
    for a in range(ED.shot_count(doc)):
        for b in range(ED.shot_count(doc)):
            moved = ED.move_shot(doc, a, b)
            moved.validate()
            assert sorted(s.slug for sc in moved.scenes
                          for s in sc.shots) == names, (a, b)
    # Shots stay long enough for the engine, whatever is typed in.
    assert ED.set_shot(doc, 0, duration=-5).scenes[0].shots[0].duration \
        >= ED.MIN_DURATION
    # Object knobs clamp to what the object accepts.
    staged = ED.add_object(blank, 0, "water_tank")
    staged = ED.set_object_param(staged, 0, 0, "level", 99.0)
    assert staged.scenes[0].world[0][1]["level"] == 1.0
    # An animated knob really does sweep across the shot.
    staged = ED.set_action(staged, 0, "water_tank", "level", 0.0, 1.0)
    swept = [staged.scenes[0].shots[0].action_value("water_tank", "level", p)
             for p in (0.0, 0.5, 1.0)]
    assert swept == [0.0, 0.5, 1.0], swept

    # ---- how much writing lands on the picture ------------------------
    from presenter.engine import OVERLAY_HELP, OVERLAY_LEVELS
    for name, flags in OVERLAY_LEVELS.items():
        assert set(flags) == {"title", "caption", "panel", "progress"}, name
        assert name in OVERLAY_HELP, name
    assert not any(OVERLAY_LEVELS["clean"].values()), "clean must show nothing"
    assert not OVERLAY_LEVELS["no_captions"]["caption"]
    assert OVERLAY_LEVELS["no_captions"]["panel"], \
        "no_captions should still keep the info panel"

    # ---- the scene composer ------------------------------------------
    # Driving the editor needs a GL context. Where there is one, every
    # control the editor draws is clicked once and the document is
    # re-validated, so a button wired to a missing action cannot ship.
    studio_note = "scene composer skipped (no OpenGL here)"
    try:
        from presenter.studio import StudioApp
        app = StudioApp(ED.blank_presentation("Selftest"), size=(1280, 720),
                        headless=True)
    except Exception as exc:                          # noqa: BLE001
        studio_note = f"scene composer skipped ({type(exc).__name__})"
    else:
        for key in ("dome", "door", "wood_stove", "forge:veins"):
            app._dispatch("lib_add", key, (0, 0))
        app._dispatch("add_shot", None, (0, 0))
        app._dispatch("add_scene", None, (0, 0))
        # Exporting writes files and blocks; everything else is clicked.
        skip = {"export", "export_all", "save", "save_as", "open"}
        clicked = set()
        for tab in ("shot", "stage", "scene"):
            app.tab = tab
            app.select_shot(0)
            app.render(app.timeline, present=False)
            for rect, action, payload in list(app.regions):
                if action in skip or action in clicked:
                    continue
                clicked.add(action)
                centre = (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
                app._dispatch(action, payload, centre)
                app.pres.validate()
                app.drag = None
                app.text_edit = None
        # The exporter borrows this same app to draw frames, so it must
        # hand the document back exactly as it found it.
        before = app.pres
        app._with_full_frame(
            lambda: setattr(app, "pres", ED.blank_presentation("clobbered")))
        assert app.pres is before, "export must not keep its retimed copy"
        assert app.editing_ui and app.viewport is not None, \
            "editor chrome must come back after an export"
        app.pygame.quit()
        studio_note = (f"scene composer exercised ({len(clicked)} controls, "
                       f"{len(CATEGORIES)} library categories)")

    print("presenter selftest OK "
          f"({len(pres.all_shots())} shots, {pres.duration:.0f}s scripted; "
          f"housing case {len(housing.all_shots())} shots, "
          f"{housing.duration:.0f}s scripted; "
          f"10-part case series {total_case_shots} shots total; "
          f"{len(OBJECT_SPECS)} placeable objects all build and frame; "
          f"{len(OVERLAY_LEVELS)} on-screen-text levels; "
          f"{studio_note})")
    return 0


def main() -> int:
    cfg = _lc.consume_config("presenter")

    if cfg.get("action") == "selftest":
        return selftest()
    if not cfg.get("action"):
        # Started on its own with nothing to play: open the composer on a
        # blank movie, which is the useful thing to do with no input.
        cfg["action"] = "compose" if not (
            cfg.get("demo") or cfg.get("script") or cfg.get("prompt")
        ) else "run"

    pres = load_presentation(cfg)
    if cfg.get("save_json"):
        pres.to_json(Path(cfg["save_json"]))
        print(f"saved {cfg['save_json']}")
        return 0

    size = None
    if cfg.get("size"):
        try:
            size = _lc.parse_size(cfg["size"])
        except ValueError as exc:
            # A typo in a free-text size field should say what is wrong,
            # not end the run with a stack trace.
            print(f"Size {cfg['size']!r} will not do: {exc}. "
                  f"Using 1600x900 instead.")
            size = (1600, 900)

    from presenter.engine import OVERLAY_HELP, OVERLAY_LEVELS, PresenterApp
    overlay = cfg.get("overlay") or "full"
    if overlay not in OVERLAY_LEVELS:
        print(f"unknown on-screen text setting {overlay!r}; using 'full'. "
              f"Choose one of: {', '.join(OVERLAY_LEVELS)}")
        overlay = "full"

    if cfg.get("action") == "compose":
        from presenter.studio import launch as launch_studio
        launch_studio(pres, size=size or (1600, 900),
                      fullscreen=bool(cfg.get("fullscreen", False)),
                      doc_path=cfg.get("script"))
        return 0

    if cfg.get("action") == "export_all":
        # Every built-in presentation, one file each, in one folder.
        out = Path(cfg.get("export_dir") or "presenter_output/all")
        out.mkdir(parents=True, exist_ok=True)
        wanted = cfg.get("demos")
        keys = ([k.strip() for k in str(wanted).split(",") if k.strip()]
                if wanted else list(DEMOS))
        unknown = [k for k in keys if k not in DEMOS]
        if unknown:
            print(f"no such demo(s): {', '.join(unknown)}")
            return 2
        print(f"rendering {len(keys)} presentation(s) into {out}")
        print(f"on-screen text: {OVERLAY_HELP[overlay]}")
        failures = []
        for index, key in enumerate(keys, 1):
            print(f"\n[{index}/{len(keys)}] {key}")
            try:
                module = importlib.import_module(DEMOS[key])
                one = module.build()
                one.validate()
                app = PresenterApp(one, headless=True, size=size)
                app.export(out / f"{key}.mp4", fps=cfg.get("fps"),
                           narration=not cfg.get("no_narration", False),
                           overlay=overlay)
                app.pygame.quit()
            except Exception as exc:                  # noqa: BLE001
                print(f"  FAILED: {exc}")
                failures.append(key)
        print(f"\ndone: {len(keys) - len(failures)} of {len(keys)} rendered "
              f"into {out}")
        if failures:
            print(f"failed: {', '.join(failures)}")
            return 1
        return 0

    if cfg.get("action") == "shots" and cfg.get("shots"):
        app = PresenterApp(pres, headless=True, size=size or (1600, 900))
        app.overlay_level = overlay
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
        print(f"on-screen text: {OVERLAY_HELP[overlay]}")
        app.export(Path(cfg["export"]), fps=cfg.get("fps"),
                   narration=not cfg.get("no_narration", False),
                   overlay=overlay)
        return 0
    app = PresenterApp(pres, headless=False,
                       windowed=not cfg.get("fullscreen", False),
                       size=size or (1600, 900))
    app.overlay_level = overlay
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
