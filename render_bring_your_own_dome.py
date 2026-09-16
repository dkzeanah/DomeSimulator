"""Staged, append-only audio / render / mux commands for Bring Your Own Dome.

Windows: py -3.12 render_bring_your_own_dome.py --help
No launch tickets, full render on import, or implicit online voice requests.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def speech_key(lesson):
    return hashlib.sha256(json.dumps(
        [(c.slug, c.narration) for c in lesson.chapters], ensure_ascii=False,
    ).encode()).hexdigest()


def new_directory(root, prefix):
    root.mkdir(parents=True, exist_ok=True)
    for i in range(1, 100000):
        candidate = root / f"{prefix}-{i:04d}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            pass
    raise RuntimeError("No unused output directory")


def save_json(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)


def newest(root, pattern):
    paths = list(root.glob(pattern))
    if not paths:
        raise ValueError(f"No {pattern} in {root}. Run the preceding stage first.")
    return max(paths, key=lambda p: p.stat().st_mtime_ns).resolve()


def executables(args):
    from two_v_demo.audio import resolve_executable, companion_ffprobe
    ffmpeg = resolve_executable("ffmpeg", args.ffmpeg)
    return ffmpeg, companion_ffprobe(ffmpeg, args.ffprobe)


def probe(path, ffprobe):
    result = subprocess.run([
        ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def stream_duration(stream):
    value = float(stream.get("duration", 0))
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Missing or invalid stream duration")
    return value


def verify_video(path, ffprobe, expected_seconds, fps, audio=False):
    data = probe(path, ffprobe)
    streams = data["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"), None)
    if not video:
        raise ValueError(f"No video stream: {path}")
    actual_frames = int(video.get("nb_frames", 0))
    expected_frames = math.ceil(expected_seconds * fps)
    if abs(actual_frames - expected_frames) > 1:
        raise ValueError(f"Truncated/wrong video: {actual_frames} frames; expected {expected_frames}")
    seconds = stream_duration(video)
    if abs(seconds - expected_seconds) > 1 / fps + .06:
        raise ValueError(f"Video duration {seconds:.3f} does not match plan {expected_seconds:.3f}")
    track = next((s for s in streams if s["codec_type"] == "audio"), None)
    if audio:
        if not track or abs(stream_duration(track) - seconds) > max(.15, 1 / fps + .06):
            raise ValueError("Audio and picture lengths do not match")
    elif track:
        raise ValueError("The separate picture render unexpectedly contains audio")
    return {"file": str(Path(path).resolve()), "frames": actual_frames,
            "expected_frames": expected_frames, "video_seconds": seconds,
            "audio_seconds": stream_duration(track) if track else None,
            "width": video["width"], "height": video["height"], "fps": fps}


def load_plan(path, lesson=None, ffprobe=None):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not data.get("byod_speech_sha256"):
        raise ValueError("Expected a BYOD audio plan made by the audio command")
    if lesson and data["byod_speech_sha256"] != speech_key(lesson):
        raise ValueError("The narration changed after this audio was made. Run audio again.")
    durations, starts, speech = (data[k] for k in ("chapter_durations", "chapter_starts", "speech_durations"))
    if not durations or len(durations) != len(starts) or len(speech) != len(starts):
        raise ValueError("Audio plan chapter counts disagree")
    if lesson and len(durations) != len(lesson.chapters):
        raise ValueError("Audio plan has a different chapter count")
    delay = float(data["speech_delay"])
    if not math.isfinite(delay) or delay < 0:
        raise ValueError("Invalid speech delay")
    cursor = 0.
    for duration, start, spoken in zip(durations, starts, speech):
        if not all(math.isfinite(float(v)) for v in (duration, start, spoken)):
            raise ValueError("Non-finite audio timing")
        if duration <= 0 or spoken < 0 or delay + spoken > duration + .01 or abs(start - cursor) > .005:
            raise ValueError("Invalid or overlapping chapter timing")
        cursor += duration
    track = Path(data["track"])
    if not track.is_absolute():
        track = path.parent / track
    if not track.is_file() or digest(track) != data["audio_sha256"]:
        raise ValueError("The measured narration track is missing or changed")
    if ffprobe:
        audio = next(s for s in probe(track, ffprobe)["streams"] if s["codec_type"] == "audio")
        if abs(stream_duration(audio) - cursor) > .15:
            raise ValueError("Audio track length does not match its timeline")
    data["track"] = str(track.resolve())
    return data


def write_plan(path, plan, lesson, smoke=False):
    from two_v_demo.audio import SPEECH_DELAY
    payload = {
        "schema": 1, "voice_profile": plan.voice,
        "track": str(plan.track_path.resolve()),
        "clips": [str(p.resolve()) for p in plan.clip_paths],
        "chapter_durations": plan.chapter_durations,
        "chapter_starts": plan.chapter_starts,
        "speech_durations": plan.speech_durations,
        "speech_delay": SPEECH_DELAY,
        "chapter_slugs": [c.slug for c in lesson.chapters],
        "byod_speech_sha256": speech_key(lesson),
        "audio_sha256": digest(plan.track_path), "smoke_test": smoke,
    }
    save_json(path, payload)


def companions(directory, lesson, durations=None, speech=None, delay=0.):
    from two_v_demo.narration import narration_script, subtitle_file
    from two_v_demo import byod_facts
    script = narration_script(durations, lesson.chapters, lesson.title, False)
    if durations is None:
        script = script.replace("The timestamps match the deterministic ModernGL video export.",
                                "DRAFT timings only. The audio stage measures speech and sets final timing.")
    (directory / "narration.md").write_text(script, encoding="utf-8")
    (directory / "captions.srt").write_text(
        subtitle_file(durations, speech, delay, lesson.chapters, False), encoding="utf-8")
    (directory / "model-audit.txt").write_text(byod_facts.report(), encoding="utf-8")
    save_json(directory / "storyboard.json", [asdict(c) for c in lesson.chapters])
    clips = directory / "recording-script"
    clips.mkdir()
    for c in lesson.chapters:
        (clips / f"{c.number}-{c.slug}.txt").write_text(" ".join(c.narration) + "\n", encoding="utf-8")


def audio_stage(args, lesson):
    from two_v_demo.audio import (synthesize_narration, voice_cache_slug, media_duration,
                                 NarrationPlan, SPEECH_DELAY, TAIL_PADDING, _build_mixed_track)
    ffmpeg, ffprobe = executables(args)
    folder = new_directory(args.output / "audio", "take")
    track = folder / "narration.m4a"
    if args.clips_dir:
        clips = []
        for c in lesson.chapters:
            matches = [args.clips_dir / f"{c.number}-{c.slug}{ext}" for ext in (".wav", ".mp3", ".m4a", ".flac")]
            matches = [p for p in matches if p.is_file()]
            if len(matches) != 1:
                raise ValueError(f"Need exactly one recording for {c.number}-{c.slug} in {args.clips_dir}")
            clips.append(matches[0].resolve())
        speech = tuple(media_duration(p, ffprobe) for p in clips)
        durations = tuple(max(c.duration, SPEECH_DELAY + s + TAIL_PADDING)
                          for c, s in zip(lesson.chapters, speech))
        starts = tuple(sum(durations[:i]) for i in range(len(durations)))
        _build_mixed_track(clips, starts, sum(durations), track, ffmpeg)
        plan = NarrationPlan("recorded", "original", "original", "original", tuple(clips),
                             speech, durations, starts, sum(durations), track)
    else:
        rate = args.rate or lesson.voice_rate or "+2%"
        key = voice_cache_slug(args.voice, rate, "-2Hz", "+0%", lesson.chapters, False)
        plan = synthesize_narration(
            args.output / "voice-cache" / key, track, ffmpeg, ffprobe,
            voice=args.voice, rate=rate, pitch="-2Hz", volume="+0%",
            chapters=lesson.chapters, speak_promise=False)
    path = folder / "plan.json"
    write_plan(path, plan, lesson)
    load_plan(path, lesson, ffprobe)
    companions(folder, lesson, plan.chapter_durations, plan.speech_durations, SPEECH_DELAY)
    print(f"\nAUDIO READY: {track}\nTIMING PLAN: {path}\nRuntime: {plan.total_duration / 60:.2f} minutes", flush=True)
    return path


def render_stage(args, lesson, plan_path=None, destination=None):
    from two_v_demo.app import MasterclassApp
    ffmpeg, ffprobe = executables(args)
    plan_path = plan_path or args.plan or newest(args.output / "audio", "take-*/plan.json")
    payload = load_plan(plan_path, lesson, ffprobe)
    folder = destination or new_directory(args.output / "video", "render")
    path = folder / "picture.mp4"
    app = MasterclassApp(size=args.size, hidden=True, lesson=lesson)
    try:
        app.export_video(path, fps=args.fps, narration=False, local_narration_plan=plan_path,
                         video_preset=args.preset, video_encoder=args.encoder,
                         ffmpeg_path=ffmpeg, ffprobe_path=ffprobe, mux_audio=False)
    finally:
        app.pygame.quit()
    result = verify_video(path, ffprobe, sum(payload["chapter_durations"]), args.fps)
    manifest = {"picture": str(path.resolve()), "plan": str(Path(plan_path).resolve()),
                "plan_sha256": digest(plan_path), "picture_sha256": digest(path),
                "speech_sha256": speech_key(lesson), "seconds": sum(payload["chapter_durations"]),
                "fps": args.fps, "verification": result, "smoke_test": payload.get("smoke_test", False)}
    save_json(folder / "render.json", manifest)
    print(f"\nPICTURE READY: {path}\nVerified {result['frames']} frames; audio remains separate.", flush=True)
    return folder / "render.json"


def mux_stage(args, manifest_path=None, destination=None, lesson=None):
    ffmpeg, ffprobe = executables(args)
    manifest_path = manifest_path or args.render_manifest or newest(args.output / "video", "render-*/render.json")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    plan_path = Path(manifest["plan"])
    if digest(plan_path) != manifest["plan_sha256"]:
        raise ValueError("The timing plan changed after rendering. Re-render before muxing.")
    payload = load_plan(plan_path, lesson=lesson, ffprobe=ffprobe)
    if payload["byod_speech_sha256"] != manifest["speech_sha256"]:
        raise ValueError("Audio and video refer to different scripts")
    picture = Path(manifest["picture"])
    if digest(picture) != manifest["picture_sha256"]:
        raise ValueError("The picture changed after verification")
    verify_video(picture, ffprobe, manifest["seconds"], manifest["fps"])
    audio = Path(payload["track"])
    if args.audio:
        audio = args.audio.resolve()
        track = next(s for s in probe(audio, ffprobe)["streams"] if s["codec_type"] == "audio")
        if abs(stream_duration(track) - manifest["seconds"]) > .15:
            raise ValueError("Replacement audio must already follow the same chapter timing and total duration")
        print("Using replacement audio: its chapter alignment is your responsibility.")
    folder = destination or new_directory(args.output / "final", "cut")
    path = folder / "bring-your-own-dome.mp4"
    command = [ffmpeg, "-n", "-i", str(picture), "-i", str(audio),
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(path)]
    print("MUX: " + subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, check=True)
    result = verify_video(path, ffprobe, manifest["seconds"], manifest["fps"], audio=True)
    save_json(folder / "verification.json", result)
    for name in ("narration.md", "captions.srt", "storyboard.json", "model-audit.txt"):
        source = plan_path.parent / name
        if source.is_file():
            shutil.copyfile(source, folder / name)
    save_json(folder / "provenance.json", {"render_manifest": str(Path(manifest_path).resolve()),
                                           "audio": str(audio), "audio_sha256": digest(audio),
                                           "smoke_test": manifest.get("smoke_test", False)})
    from types import SimpleNamespace
    from video_review.render_bridge import write_render_receipt
    storyboard_path = folder / "storyboard.json"
    if storyboard_path.is_file():
        chapters = tuple(SimpleNamespace(**c) for c in json.loads(storyboard_path.read_text(encoding="utf-8")))
        receipt_lesson = SimpleNamespace(key="byod", title="Bring Your Own Dome", chapters=chapters)
        write_render_receipt(path, receipt_lesson, payload["chapter_durations"], {
            "size": f"{result['width']}x{result['height']}", "fps": manifest["fps"],
            "voice": payload.get("voice_profile", args.voice),
        })
    print(f"\nFINAL MP4: {path}\nVerified picture frames and audio duration.", flush=True)
    return path


def shots_stage(args, lesson):
    from two_v_demo.app import MasterclassApp
    from PIL import Image, ImageDraw
    folder = new_directory(args.output, "review")
    app = MasterclassApp(size=args.size, hidden=True, lesson=lesson)
    shots = []
    try:
        cursor = 0.
        for i, c in enumerate(lesson.chapters):
            moments = (.12, .9) if c.slug in ("iris", "rooms", "channels", "growth", "layers", "rotation") else (.85,)
            for p in moments:
                app.timeline = cursor + c.duration * p
                app.chapter_index, app.chapter_progress = i, p
                app.reset_camera()
                app.render(present=False)
                target = folder / f"{c.number}-{c.slug}-{int(p * 100):02d}.png"
                app.save_screenshot(target)
                shots.append(target)
            cursor += c.duration
    finally:
        app.pygame.quit()
    # Paginated sheets keep every chapter readable during review.
    for start in range(0, len(shots), 12):
        page = shots[start:start + 12]
        sheet = Image.new("RGB", (1280, math.ceil(len(page) / 2) * 386), "#0a1420")
        draw = ImageDraw.Draw(sheet)
        for index, path in enumerate(page):
            x, y = (index % 2) * 640, (index // 2) * 386
            with Image.open(path) as im:
                im.thumbnail((640, 360))
                sheet.paste(im, (x, y + 24))
            draw.text((x + 8, y + 5), path.stem, fill="white")
        sheet.save(folder / f"contact-sheet-{start // 12 + 1:02d}.jpg")
    companions(folder, lesson)
    print(f"REVIEW STILLS: {folder}", flush=True)
    return folder


def smoke_stage(args, lesson):
    from two_v_demo.audio import NarrationPlan
    # Explicit silence only for the integration check, never a production take.
    slugs = {"title", "iris", "rooms", "channels", "panel_lip", "solar", "rewards", "outro"}
    chapters = tuple(replace(c, duration=1.2) for c in lesson.chapters if c.slug in slugs)
    lesson = replace(lesson, chapters=chapters)
    args.size, args.fps, args.preset, args.encoder = (960, 540), 6, "ultrafast", "libx264"
    folder = new_directory(args.output, "smoke-test")
    ffmpeg, _ = executables(args)
    track = folder / "TEST-SILENCE.m4a"
    duration = sum(c.duration for c in chapters)
    subprocess.run([ffmpeg, "-n", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", str(duration), "-c:a", "aac", str(track)], check=True)
    plan = NarrationPlan("TEST SILENCE", "test", "test", "test", (),
                         (0.,) * len(chapters), tuple(c.duration for c in chapters),
                         tuple(i * 1.2 for i in range(len(chapters))), duration, track)
    path = folder / "plan.json"
    write_plan(path, plan, lesson, smoke=True)
    manifest = render_stage(args, lesson, path, folder)
    final = new_directory(folder, "mux")
    mux_stage(args, manifest, final)
    print("SMOKE TEST PASSED (test silence, not narration).", flush=True)


def parse_size(value):
    try:
        width, height = map(int, value.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("Size must be WIDTHxHEIGHT") from None
    if min(width, height) < 240 or width % 2 or height % 2:
        raise argparse.ArgumentTypeError("Use even dimensions of at least 240 pixels")
    if abs(width / height - 16 / 9) > .01:
        raise argparse.ArgumentTypeError("This film is composed for 16:9")
    return width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("check", "script", "shots", "audio", "render", "mux", "all", "smoke"))
    parser.add_argument("--output", type=Path, default=ROOT / "deliverables" / "byod")
    parser.add_argument("--size", type=parse_size, default=(1920, 1080))
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--encoder", choices=("libx264", "h264_nvenc"), default="libx264")
    parser.add_argument("--preset", default="medium", help="x264: medium/fast; NVENC: p1-p7")
    parser.add_argument("--voice", default="en-US-AndrewMultilingualNeural")
    parser.add_argument("--rate", help="TTS rate, e.g. --rate=+2%%")
    parser.add_argument("--clips-dir", type=Path, help="Use your recordings: NN-slug.wav/mp3/m4a/flac")
    parser.add_argument("--plan", type=Path, help="Explicit audio plan for render")
    parser.add_argument("--render-manifest", type=Path, help="Explicit render.json for mux")
    parser.add_argument("--review-packet", type=Path, help="Video Review revision.json narration overlay")
    parser.add_argument("--audio", type=Path, help="Mux replacement track already aligned to this timeline")
    parser.add_argument("--chapters", help="Comma-separated slugs, for a short preview; use a separate --output")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    if not 1 <= args.fps <= 60:
        parser.error("fps must be between 1 and 60")
    args.output = args.output.resolve()
    from two_v_demo.lesson_bring_your_own_dome import BYOD_LESSON
    lesson = BYOD_LESSON
    if args.review_packet:
        from video_review.render_bridge import apply_packet
        try:
            lesson = apply_packet(lesson, args.review_packet)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))
    if args.chapters:
        selected = args.chapters.split(",")
        available = {c.slug: c for c in lesson.chapters}
        if len(selected) != len(set(selected)) or set(selected) - available.keys():
            parser.error("Chapter slugs must be unique and match the storyboard")
        lesson = replace(lesson, chapters=tuple(available[s] for s in selected))
    started = time.perf_counter()
    try:
        if args.stage == "check":
            BYOD_LESSON.selftest()
            executables(args)
            print(f"PASS: {len(BYOD_LESSON.chapters)} chapters; arithmetic, scene geometry, FFmpeg and FFprobe.")
        elif args.stage == "script":
            directory = new_directory(args.output, "script")
            companions(directory, lesson)
            print(directory)
        elif args.stage == "shots":
            shots_stage(args, lesson)
        elif args.stage == "audio":
            audio_stage(args, lesson)
        elif args.stage == "render":
            render_stage(args, lesson)
        elif args.stage == "mux":
            mux_stage(args, lesson=lesson if args.review_packet else None)
        elif args.stage == "smoke":
            smoke_stage(args, lesson)
        else:
            plan = audio_stage(args, lesson)
            manifest = render_stage(args, lesson, plan)
            mux_stage(args, manifest)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        print(f"Stage elapsed: {time.perf_counter() - started:.1f} seconds", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
