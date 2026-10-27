"""Make a film: one command, one way, for every film in the project.

    py -3.12 -m film list                              # every film that can be made
    py -3.12 -m film show cabin_wedge_beyond           # what a make would do, and where it lands
    py -3.12 -m film make cabin_wedge_beyond           # narrated, landscape + phone cut, release, teaser
    py -3.12 -m film make cabin_wedge_beyond --voice mine --pace 1.5
    py -3.12 -m film stills cabin_wedge_beyond         # one still per chapter, to look at first
    py -3.12 -m film teaser cabin_wedge_beyond --voice mine --pace 1.5
    py -3.12 -m film make 2v --engine web              # the same film on the web engine (sketch_claude/lesson_web.py)
    py -3.12 -m film stills 2v --engine web            # its stills, both orientations, to look at first

``--engine web`` renders in the browser engine instead of moderngl: the same lesson, its own
words and the house voice, numbers computed for the screen, landscape and a framed phone cut,
the release. The moderngl engine stays the default until every film has a web stage.

Before this there were four ways to make a film -- the launcher's Masterclass tab,
staged per-film scripts (narrate / plan / render, written out by hand each time),
``segmented_render.py``, and ``two_v_demo.teasers`` -- and outputs landed in five
folders. They all end in the same renderer (``MasterclassApp.export_video``), so this
command is that renderer's one front door:

1. the film's render preset (``render_presets``), so a make reproduces what shipped;
2. the voice: the house voice, any neural voice by name, or ``mine`` -- the owner's
   own voice (``local_voice_studio.my_voice``), at any pace, the clips sped with pitch
   kept and each of the film's chapters fitted to its faster speech, while spliced-in
   segments (call to action, outro) keep the length their music was made for;
3. the standard export: resumable chunks, the landscape cut, the phone cut beside it,
   the release folder, the teaser (CLAUDE.md: every render is a release);
4. everything filed in the dated library (``medialib``): one folder per film, every
   version and its phone cut, captions and release inside.

The owner's-voice clips and plan are kept in the film's own folder as
``<film>-myvoice-x<pace>/``, so the release can read the plan's chapter timings and
the next version of the film reuses every clip already spoken.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "two_v_demo_output"


def preset_fields(lesson: str) -> dict:
    """The film's render preset, house defaults filled in."""
    if lesson == "sketch_gpt_pilot":
        from two_v_demo.cinema_preset import EPISODE_PRESET
        return dict(EPISODE_PRESET.applied())
    import render_presets as rp
    from two_v_demo.deliverables import DELIVERABLE_BY_LESSON

    preset = rp.PRESET_BY_KEY.get(lesson)
    if preset is None or preset.fields.get("action") != "export_video":
        item = DELIVERABLE_BY_LESSON.get(lesson)
        if item is None:
            raise SystemExit(f"{lesson!r} is not a registered film; `py -3.12 -m film list` names them")
        preset = rp._video(lesson, lesson, item.filename, item.note)
    return dict(preset.applied())


def chapters(lesson: str, compose_segments: bool):
    from two_v_demo.lesson_loader import get_lesson

    film = get_lesson(lesson)
    if compose_segments:
        from two_v_demo.segments import compose
        film = compose(film)
    return film, tuple(film.chapters)


def target(fields: dict) -> Path:
    """Where the cut would go: the newest iteration's folder (for ``show``)."""
    import medialib
    return medialib.locate(ROOT / fields["export_video"])


def claim(fields: dict) -> Path:
    """Make the next iteration's numbered folder and point the render at a file inside it,
    so the cut, the phone cut, the voice and the release all land in that one folder."""
    import medialib
    name = Path(fields["export_video"]).name
    folder, version = medialib.new_output(medialib.slug_of(name))
    path = folder / medialib.versioned(name, version)
    fields["export_video"] = str(path)
    return path


# ---------------------------------------------------------------------------
# The owner's voice, at a pace


def narrate_mine(lesson: str, compose_segments: bool, pace: float, beside: Path, beside_stem: str,
                 progress=print) -> Path:
    """Speak the film in the owner's voice, then fit it at ``pace``; returns the plan."""
    from local_voice_studio import my_voice as mv
    from two_v_demo.audio import spoken_chapter_text

    _, chs = chapters(lesson, compose_segments)
    # Beside the cut, as <stem>-myvoice-x<pace>/: the release finds the plan there for its
    # chapter timestamps, and the clips are reused by the next version of the film.
    work = beside / f"{beside_stem}-myvoice-x{pace:g}"
    raw = work / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    script = {"lesson": lesson, "chapters": [
        {"title": c.title, "duration": float(c.duration), "text": spoken_chapter_text(i, chs, True)}
        for i, c in enumerate(chs)]}
    (raw / "script.json").write_text(json.dumps(script, indent=1), encoding="utf-8")
    python = str(mv.VENV_PYTHON) if mv.VENV_PYTHON.is_file() else sys.executable
    progress(f"narrating {len(chs)} chapters in your voice (clips already spoken are kept)")
    code = subprocess.run([python, "-m", "local_voice_studio.my_voice", "narrate",
                           "--script", str(raw / "script.json"), "--out", str(raw)], cwd=str(ROOT)).returncode
    if code != 0:
        raise SystemExit("narrating in your voice failed; see the lines above")
    return fit_pace(lesson, compose_segments, pace, work, progress)


def fit_pace(lesson: str, compose_segments: bool, pace: float, work: Path, progress=print) -> Path:
    import soundfile as sf

    from two_v_demo.audio import SPEECH_DELAY, TAIL_PADDING, _build_mixed_track, resolve_executable
    from two_v_demo.lesson_registry import get_lesson

    ffmpeg = resolve_executable("ffmpeg")
    _, chs = chapters(lesson, compose_segments)
    ours = {c.slug for c in get_lesson(lesson).chapters}
    raw = work / "raw"
    raw_plan = json.loads((raw / "narration-plan.json").read_text(encoding="utf-8"))
    clips, speech, durations = [], [], []
    for i, (c, name) in enumerate(zip(chs, raw_plan["clips"])):
        src, dst = raw / name, work / f"chapter_{i + 1:03d}.wav"
        speed = ["-af", f"atempo={pace}"] if pace != 1 else []
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(src), *speed, "-c:a", "pcm_s16le", str(dst)],
                       check=True)
        info = sf.info(str(dst))
        s = info.frames / info.samplerate
        fitted = SPEECH_DELAY + s + TAIL_PADDING
        # The film's own chapters move at the voice's pace; a spliced-in segment keeps
        # the length its music and picture were made for.
        durations.append(max(6.0, fitted) if c.slug in ours else max(float(c.duration), fitted))
        clips.append(dst)
        speech.append(s)
    starts, t = [], 0.0
    for d in durations:
        starts.append(t)
        t += d
    track = work / "narration.m4a"
    _build_mixed_track(clips, starts, t, track, ffmpeg, progress)
    plan = work / "narration-plan.json"
    plan.write_text(json.dumps({
        "schema": 1, "synthetic_voice": True, "lesson": lesson,
        "voice_profile": f"{raw_plan.get('voice_profile', 'my voice')} at x{pace:g}",
        "model": raw_plan.get("model", ""), "chapter_count": len(chs),
        "chapter_starts": starts, "chapter_durations": durations, "speech_durations": speech,
        "speech_delay": SPEECH_DELAY, "track": track.name, "clips": [p.name for p in clips]}, indent=1),
        encoding="utf-8")
    progress(f"pace x{pace:g}: {len(chs)} chapters, {t / 60:.1f} min "
             f"(written timing {sum(c.duration for c in chs) / 60:.1f} min)")
    return plan


# ---------------------------------------------------------------------------


def run_ticket(fields: dict) -> int:
    import launcher_common as lc
    lc.write_config("two_v_masterclass", fields)
    env=os.environ.copy()
    if fields.get("episode_project"):
        env["SKETCH_GPT_EPISODE_PROJECT"]=str(fields["episode_project"])
    return subprocess.run([sys.executable, "two_v_masterclass.py"], cwd=str(ROOT),env=env).returncode


def make(lesson: str, *, voice: str = "", pace: float = 1.0, landscape_only: bool = False,
         teaser: bool = True, segments: bool | None = None, fps: int | None = None,
         size: str | None = None, dry_run: bool = False) -> int:
    fields = preset_fields(lesson)
    if segments is not None:
        fields["compose_segments"] = segments
    if fps:
        fields["fps"] = str(fps)
    if size:
        fields["size"] = size
        if "orientation_sizes" in fields:
            w,h=map(int,size.lower().split('x'))
            fields['orientation_sizes']={'landscape':f'{max(w,h)}x{min(w,h)}',
                                         'portrait':f'{min(w,h)}x{max(w,h)}'}
    fields["orientation"] = "landscape" if landscape_only else "both"
    mine = voice == "mine"
    # The renderer's own teaser speaks in the house (online) voice, which can be refused (403)
    # and is not the owner's anyway; with --voice mine the teaser is made after the film, in
    # the owner's voice, by teaser() below.
    fields["teaser"] = teaser and not mine
    if voice and not mine:
        fields["voice"] = voice
    if pace != 1.0 and not mine:
        raise SystemExit("--pace is for --voice mine; a neural voice takes its rate in the preset (voice_rate)")
    where = target(fields)
    print(f"{lesson}: {fields['export_video']}")
    print(f"  a new numbered output, after {where.parent.name if where.parent.exists() else 'none yet'}")
    voice_label=('captioned / no audio' if fields.get('no_narration') else ('mine at x%g' % pace if mine else fields['voice']))
    print(f"  voice {voice_label}; "
          f"{'landscape only' if landscape_only else 'landscape + phone cut'}; "
          f"segments {'on' if fields.get('compose_segments') else 'off'}; teaser {'on' if teaser else 'off'}")
    if dry_run:
        return 0
    where = claim(fields)
    if lesson == "sketch_gpt_pilot":
        # Freeze this take before the renderer starts: subsequent director edits
        # cannot change a film that is rendering or its phone companion.
        from world3d.cinema import load_episode
        source=load_episode().save(where.parent / "episode.json")
        fields["episode_project"]=str(source.resolve())
    print(f"  into {where.relative_to(ROOT)}")
    if mine:
        where.parent.mkdir(parents=True, exist_ok=True)
        fields["local_narration_plan"] = str(narrate_mine(lesson, bool(fields.get("compose_segments")), pace,
                                                          where.parent, where.stem))
    code = run_ticket(fields)
    import medialib
    medialib.write_index()
    if code == 0:
        print(f"done; the film's folder: {Path(fields['export_video']).parent.relative_to(ROOT)}")
        if teaser and mine:
            print("now the teaser, in your voice")
            if teaser_code := globals()["teaser"](lesson, "mine", pace):
                print(f"teaser not built (exit {teaser_code}); retry: py -3.12 -m film teaser {lesson} --voice mine --pace {pace:g}")
    return code


def stills(lesson: str, *, stages: tuple[str, ...] = (), at: float = 0.5) -> int:
    import medialib
    if lesson == 'sketch_gpt_pilot':
        _, chs=chapters(lesson,False)
        clock=0.; marks=[]
        for c in chs:
            marks.append(str(clock+c.duration*.5)); clock+=c.duration
        fields={**preset_fields(lesson),'action':'shots','shots':','.join(marks),'no_narration':True}
    else:
        import render_presets as rp
        preset = rp.PRESET_BY_KEY.get(f"{lesson}_stills")
        fields = dict(preset.applied()) if preset else {**preset_fields(lesson), "action": "shots",
                                                         "shots": rp.chapter_shots(lesson), "no_narration": True}
    if not 0 <= at < 1:
        raise SystemExit("--at must lie between zero and one, with one excluded")
    if stages or at != 0.5:
        _, chs = chapters(lesson, bool(fields.get("compose_segments", False)))
        wanted = set(stages)
        missing = wanted - {ch.slug for ch in chs}
        if missing:
            raise SystemExit(f"unknown chapter slugs: {', '.join(sorted(missing))}")
        clock, times = 0.0, []
        for ch in chs:
            if not wanted or ch.slug in wanted:
                times.append(f"{clock + ch.duration * at:.2f}")
            clock += ch.duration
        fields["shots"] = ",".join(times)
    folder = medialib.new_folder(f"{lesson}-stills")
    fields["shots_output_dir"] = str(folder)
    print(f"stills for {lesson} into {folder.relative_to(ROOT)}")
    code = run_ticket(fields)
    medialib.write_index()
    return code


def teaser(lesson: str, voice: str = "", pace: float = 1.0) -> int:
    """The film's teaser, both shapes. ``voice="mine"`` narrates it in the owner's voice
    (also the way round the house voice's online service when it refuses)."""
    from two_v_demo import teasers
    if voice != "mine":
        return teasers.export(lesson)
    key = teasers.PREFIX + lesson
    fields = {"action": "export_video", "lesson": key, "export_video": str(teasers.output_path(lesson)),
              "orientation": "both", "fps": "30", "size": "1920x1080", "teaser": False}
    where = claim(fields)
    print(f"{key}: into {where.parent.relative_to(ROOT)}, voice mine at x{pace:g}")
    fields["local_narration_plan"] = str(narrate_mine(key, False, pace, where.parent, where.stem))
    code = run_ticket(fields)
    import medialib
    medialib.write_index()
    return code


def list_films() -> None:
    import render_presets as rp
    from two_v_demo.deliverables import DELIVERABLES
    import medialib
    for item in DELIVERABLES:
        found = medialib.latest(medialib.slug_of(item.filename), ".mp4")
        state = f"made, newest {found.name}" if found else "not made yet"
        tag = "" if item.lesson in rp.PRESET_BY_KEY else "  (no preset; uses the registry)"
        print(f"{item.lesson:34s} {state}{tag}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="film", description="Make a film, one way, into the library.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("show", "make"):
        p = sub.add_parser(name)
        p.add_argument("lesson")
        p.add_argument("--voice", default="", help="'mine', or a neural voice name; default: the preset's")
        p.add_argument("--pace", type=float, default=1.0, help="with --voice mine: 1.5 speaks 1.5x faster")
        p.add_argument("--landscape-only", action="store_true")
        p.add_argument("--no-teaser", action="store_true")
        seg = p.add_mutually_exclusive_group()
        seg.add_argument("--segments", dest="segments", action="store_true", default=None)
        seg.add_argument("--no-segments", dest="segments", action="store_false")
        p.add_argument("--fps", type=int)
        p.add_argument("--size")
        p.add_argument("--engine", choices=("moderngl", "web"), default="moderngl")
    st = sub.add_parser("stills")
    st.add_argument("lesson")
    st.add_argument("--engine", choices=("moderngl", "web"), default="moderngl")
    st.add_argument("--chapters", default="", help="comma-separated chapter slugs; default is every chapter")
    st.add_argument("--at", type=float, default=0.5, help="progress within each chapter, from zero up to one")
    t = sub.add_parser("teaser")
    t.add_argument("lesson")
    t.add_argument("--voice", default="")
    t.add_argument("--pace", type=float, default=1.0)
    a = ap.parse_args(argv)
    if a.cmd == "list":
        list_films()
        return 0
    if getattr(a, "engine", "moderngl") == "web" and a.cmd in ("make", "stills"):
        from sketch_claude.lesson_web import headless
        for r in headless(a.lesson, "stills" if a.cmd == "stills" else "render"):
            print(f"OUTPUT {json.dumps(r)}", flush=True)
        return 0
    if a.cmd in ("show", "make"):
        return make(a.lesson, voice=a.voice, pace=a.pace, landscape_only=a.landscape_only,
                    teaser=not a.no_teaser, segments=a.segments, fps=a.fps, size=a.size,
                    dry_run=a.cmd == "show")
    if a.cmd == "teaser":
        return teaser(a.lesson, a.voice, a.pace)
    return stills(a.lesson, stages=tuple(s.strip() for s in a.chapters.split(",") if s.strip()), at=a.at)


if __name__ == "__main__":
    raise SystemExit(main())
