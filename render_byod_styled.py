"""Staged render driver for the two styled Bring Your Own Dome cuts.

Same film, two registers. ``--lesson byod_polished`` renders the presentation
cut; ``--lesson byod_snarky`` renders the one with the pink jelly in it. The
stages, verification and append-only naming are the deepseek driver's, imported
rather than copied; what is new here is the audio, because this is the first
film in the repository with **two voices on one track**.

    py -3.12 render_byod_styled.py check --lesson byod_snarky
    py -3.12 render_byod_styled.py audio --lesson byod_snarky
    py -3.12 render_byod_styled.py render --lesson byod_snarky
    py -3.12 render_byod_styled.py mux --lesson byod_snarky

Finished cuts land in ``deliverables/byod-styled/<lesson>/`` named
``attempt-v<N>-<lesson>.mp4``, and are never replaced.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from render_bring_your_own_dome import (companions, executables,
                                        new_directory, render_stage,
                                        save_json, write_plan)
from render_byod_deepseek import (mux_stage, release_stage, shots_stage)

LESSONS = ("byod_polished", "byod_snarky")
STAGES = ("check", "script", "shots", "audio", "render", "mux", "all", "smoke",
          "portrait", "release")


def lesson_for(key: str):
    from two_v_demo.lesson_registry import get_lesson
    return get_lesson(key)


# ----------------------------------------------------------------------
# The mascot's own clips
# ----------------------------------------------------------------------

def mascot_clips(output_directory: Path, film, ffmpeg, ffprobe,
                 progress=print):
    """One clip per mascot line, cached by voice and text.

    Reuses ``audio._synthesize_one`` -- the same call the narrator goes through
    -- so the character is voiced by the same service, cached the same way and
    stored beside the film the same way. What differs is only the voice.
    """
    from two_v_demo.audio import _synthesize_one, media_duration
    from two_v_demo import mascot

    output_directory.mkdir(parents=True, exist_ok=True)
    voice, rate, pitch, volume = mascot.voice_settings()
    clips: dict[str, tuple[Path, float]] = {}
    for chapter in film.chapters:
        for cue in getattr(chapter, "mascot", ()) or ():
            if not cue.line or cue.line in clips:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", cue.line.lower()).strip("-")[:52]
            clip = output_directory / f"line-{slug}.mp3"
            if not clip.is_file() or clip.stat().st_size <= 1024:
                progress(f"mascot: {cue.line!r}")
                # ``_synthesize_one`` is a coroutine. Called without awaiting
                # it, it returns an object and writes nothing at all, and the
                # mistake only surfaces later as a missing file -- which is
                # exactly how this went wrong the first time.
                asyncio.run(_synthesize_one(cue.line, clip, voice, rate, pitch,
                                            volume, progress))
            try:
                seconds = media_duration(clip, ffprobe)
            except subprocess.CalledProcessError:
                clip.unlink(missing_ok=True)
                raise RuntimeError(
                    f"the mascot's clip for {cue.line!r} is not readable audio; "
                    f"it was removed so the next run re-synthesizes it")
            clips[cue.line] = (clip, seconds)
    return clips


def staged_audio(args, film):
    """Narrator and mascot, synthesized separately and mixed onto one track.

    The order matters and is not obvious. The narrator is synthesized first so
    its **measured** speech gives every cue an exact position; the mascot's
    lines are synthesized next so their real lengths are known; only then can a
    chapter's duration be settled, because a chapter has to be long enough to
    hold whichever of the two finishes last. Resolving the cues before the
    speech is measured would place every line against an estimate.
    """
    from two_v_demo import mascot
    from two_v_demo.audio import (SPEECH_DELAY, TAIL_PADDING, NarrationPlan,
                                  _build_mixed_track, synthesize_narration,
                                  voice_cache_slug)

    ffmpeg, ffprobe = executables(args)
    folder = new_directory(args.output / "audio", "take")
    track = folder / "narration.m4a"

    rate = args.rate or film.voice_rate or "+2%"
    key = voice_cache_slug(args.voice, rate, "-2Hz", "+0%", film.chapters, False)
    plan = synthesize_narration(
        args.output / "voice-cache" / key, track, ffmpeg, ffprobe,
        voice=args.voice, rate=rate, pitch="-2Hz", volume="+0%",
        chapters=film.chapters, speak_promise=False)

    lines = mascot_clips(folder / "mascot-lines", film, ffmpeg, ffprobe)
    measured = {text: seconds for text, (_clip, seconds) in lines.items()}

    # Resolve every cue against the measured narrator, then settle each
    # chapter's length so it can hold its own speech and any line landing in it.
    showings = []
    durations = []
    for index, chapter in enumerate(film.chapters):
        chapter_seconds = plan.chapter_durations[index]
        found = mascot.resolve(chapter, chapter_seconds, plan.speech_durations[index],
                               False, (), measured)
        longest = max((s.start + measured.get(s.cue.line, 0.0) + TAIL_PADDING
                       for s in found if s.cue.line), default=0.0)
        durations.append(round(max(chapter_seconds,
                                   SPEECH_DELAY + plan.speech_durations[index]
                                   + TAIL_PADDING, longest), 3))
        showings.append(found)

    starts, cursor = [], 0.0
    for duration in durations:
        starts.append(cursor)
        cursor += duration

    total = sum(durations)
    clips = list(plan.clip_paths)
    at = list(starts)
    for index, found in enumerate(showings):
        for showing in found:
            if not showing.cue.line:
                continue
            clips.append(lines[showing.cue.line][0])
            # `_build_mixed_track` adds SPEECH_DELAY to every start itself, and
            # a resolved cue already carries it. Subtracting here is what puts
            # the line on the words instead of half a second past them.
            at.append(starts[index] + showing.start - SPEECH_DELAY)

    mixed = folder / "mixed.m4a"
    _build_mixed_track(clips, at, total, mixed, ffmpeg)
    shutil.copyfile(mixed, track)

    final = NarrationPlan(
        plan.voice, plan.rate, plan.pitch, plan.volume,
        tuple(plan.clip_paths), tuple(plan.speech_durations), tuple(durations),
        tuple(starts), total, track)
    path = folder / "plan.json"
    write_plan(path, final, film)
    save_json(folder / "mascot-lines.json", {
        "voice": mascot.VOICE, "rate": mascot.RATE, "pitch": mascot.PITCH,
        "lines": {text: str(clip) for text, (clip, _s) in lines.items()},
        "showings": [[chapter.slug, [
            {"line": s.cue.line, "start": round(s.start, 3),
             "end": round(s.end, 3), "mood": s.mood} for s in found]]
            for chapter, found in zip(film.chapters, showings)],
    })
    companions(folder, film, final.chapter_durations, final.speech_durations,
               SPEECH_DELAY)
    write_styled_captions(folder, film, showings, starts)
    print(f"\nAUDIO READY: {track}\nTIMING PLAN: {path}\n"
          f"Runtime: {total / 60:.2f} minutes  "
          f"({sum(len(f) for f in showings)} mascot appearances)", flush=True)
    return path


# ----------------------------------------------------------------------
# Captions, with the character labelled as a second speaker
# ----------------------------------------------------------------------

def parse_srt(text: str):
    entries = []
    for block in re.split(r"\n\s*\n", text.strip()):
        rows = [row for row in block.strip().splitlines() if row.strip()]
        if len(rows) < 3 or "-->" not in rows[1]:
            continue
        head, tail = rows[1].split("-->")
        entries.append((stamp(head.strip()), stamp(tail.strip()),
                        " ".join(rows[2:])))
    return entries


def stamp(text: str) -> float:
    match = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", text.strip())
    if not match:
        raise ValueError(f"bad subtitle time {text!r}")
    hours, minutes, seconds, fraction = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds + fraction / 1000.0


def srt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_styled_captions(folder: Path, film, showings, starts) -> Path:
    """The narrator's captions, with the character's lines added as their own.

    The narrator's own cue timing is left exactly as the house generator made
    it: splitting the chapter's speech span between two speakers would move
    every one of its captions, and they are correct as they stand. The
    character's lines are added beside them and the file is re-ordered once.
    """
    source = folder / "captions.srt"
    entries = parse_srt(source.read_text(encoding="utf-8")) if source.is_file() else []
    for chapter, found, start in zip(film.chapters, showings, starts):
        for showing in found:
            if not showing.cue.line:
                continue
            begin = start + showing.start
            entries.append((begin, max(begin + 0.4,
                                       start + showing.end - 0.05),
                            f"{voice_name()}: {showing.cue.line}"))
    entries.sort(key=lambda row: row[0])
    rows = []
    for index, (begin, end, text) in enumerate(entries, start=1):
        rows.append(f"{index}\n{srt_time(begin)} --> {srt_time(end)}\n{text}\n")
    target = folder / "captions.srt"
    target.write_text("\n".join(rows), encoding="utf-8")
    return target


def voice_name() -> str:
    from two_v_demo import mascot
    return mascot.MASCOT_NAME.upper()


# ----------------------------------------------------------------------
# Smoke test
# ----------------------------------------------------------------------

def smoke_stage(args, film):
    from two_v_demo.audio import NarrationPlan
    slugs = {"title", "iris", "veins", "floor", "close"}
    chapters = tuple(replace(c, duration=1.2, mascot=tuple(
        replace(cue, hold=1.0) for cue in getattr(c, "mascot", ())))
        for c in film.chapters if c.slug in slugs)
    film = replace(film, chapters=chapters)
    args.size, args.fps, args.preset, args.encoder = (960, 540), 6, "ultrafast", "libx264"
    args.orientation = "landscape"
    folder = new_directory(args.output, "smoke-test")
    args.output = folder
    ffmpeg, _ = executables(args)
    duration = sum(c.duration for c in chapters)
    track = folder / "TEST-SILENCE.m4a"
    subprocess.run([ffmpeg, "-n", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", str(duration), "-c:a", "aac", str(track)], check=True)
    plan = NarrationPlan("TEST SILENCE", "test", "test", "test", (),
                         (0.0,) * len(chapters),
                         tuple(c.duration for c in chapters),
                         tuple(i * 1.2 for i in range(len(chapters))),
                         duration, track)
    path = folder / "plan.json"
    write_plan(path, plan, film, smoke=True)
    manifest = render_stage(args, film, path, folder)
    mux_stage(args, manifest, new_directory(folder, "mux"), film)
    print("SMOKE TEST PASSED (test silence, not narration).", flush=True)


# ----------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--lesson", choices=LESSONS, default="byod_snarky")
    parser.add_argument("--stem", default="",
                        help="Defaults to the lesson key")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--orientation", choices=("landscape", "portrait"),
                        default="landscape")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--encoder", choices=("libx264", "h264_nvenc"),
                        default="libx264")
    parser.add_argument("--preset", default="medium")
    parser.add_argument("--voice", default="en-US-AndrewMultilingualNeural")
    parser.add_argument("--rate")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--render-manifest", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--cut", type=Path)
    parser.add_argument("--version", type=int)
    parser.add_argument("--chapters")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / "deliverables" / "byod-styled"
    args.output = (args.output or (root / args.lesson)).resolve()
    args.stem = args.stem or args.lesson
    from two_v_demo.frame import size_for
    args.size = size_for(args.orientation)
    if not 1 <= args.fps <= 60:
        parser.error("fps must be between 1 and 60")

    film = lesson_for(args.lesson)
    if args.chapters:
        chosen = args.chapters.split(",")
        available = {c.slug: c for c in film.chapters}
        if len(chosen) != len(set(chosen)) or set(chosen) - available.keys():
            parser.error("Chapter slugs must be unique and match the storyboard")
        film = replace(film, chapters=tuple(available[s] for s in chosen))

    started = time.perf_counter()
    try:
        if args.stage == "check":
            film.selftest()
            executables(args)
            cues = sum(len(getattr(c, "mascot", ())) for c in film.chapters)
            print(f"PASS: {film.key}, {len(film.chapters)} chapters, "
                  f"profile {film.profile!r}, {cues} mascot cues; arithmetic, "
                  f"scene geometry, FFmpeg and FFprobe.", flush=True)
        elif args.stage == "script":
            directory = new_directory(args.output, "script")
            companions(directory, film)
            print(directory)
        elif args.stage == "shots":
            shots_stage(args, film)
        elif args.stage == "audio":
            staged_audio(args, film)
        elif args.stage == "render":
            from render_byod_deepseek import newest_plan
            plan = args.plan or newest_plan(args)
            render_stage(args, film, plan)
        elif args.stage == "mux":
            mux_stage(args, film=film, version=args.version)
        elif args.stage == "portrait":
            from render_byod_deepseek import portrait_stage
            portrait_stage(args, film)
        elif args.stage == "release":
            release_stage(args, film)
        elif args.stage == "smoke":
            smoke_stage(args, film)
        else:
            plan = staged_audio(args, film)
            manifest = render_stage(args, film, plan)
            mux_stage(args, manifest, film=film, version=args.version)
    except (OSError, ValueError, RuntimeError, KeyError,
            subprocess.CalledProcessError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        print(f"Stage elapsed: {time.perf_counter() - started:.1f} seconds",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
