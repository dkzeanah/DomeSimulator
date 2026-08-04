"""Local voice narration bridge for the standalone 2V masterclass."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

from two_v_demo.audio import (
    SPEECH_DELAY,
    TAIL_PADDING,
    _build_mixed_track,
    companion_ffprobe,
    media_duration,
    resolve_executable,
    spoken_chapter_text,
)
from two_v_demo.lessons import CHAPTERS
from two_v_demo.narration import narration_script, subtitle_file

from .backends import synthesize_chatterbox
from .models import VoiceProfile, utc_now
from .project import VoiceProject


def _chapter_starts(durations: list[float]) -> list[float]:
    starts: list[float] = []
    cursor = 0.0
    for duration in durations:
        starts.append(cursor)
        cursor += duration
    return starts


def build_dome_narration(
    project: VoiceProject,
    profile: VoiceProfile,
    *,
    ffmpeg_path: str | None = None,
    ffprobe_path: str | None = None,
    allow_model_download: bool = False,
    progress: Callable[[str], None] = print,
) -> Path:
    """Generate chapter WAVs, a mixed track, timing JSON, script, and captions."""
    if not project.consented:
        raise PermissionError("Project ownership statement is required")
    ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
    ffprobe = companion_ffprobe(ffmpeg, ffprobe_path)
    output_directory = (
        project.root / "outputs" / "dome" / f"2v-{profile.profile_id}"
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    clip_paths: list[Path] = []
    speech_durations: list[float] = []
    for index, chapter in enumerate(CHAPTERS):
        clip_path = output_directory / f"chapter_{chapter.number}.wav"
        sidecar_path = clip_path.with_suffix(".wav.json")
        expected_text = spoken_chapter_text(index)
        cached = False
        if clip_path.is_file() and sidecar_path.is_file():
            try:
                sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
                cached = (
                    sidecar.get("profile_sha256") == profile.sha256
                    and sidecar.get("text") == expected_text
                )
            except (OSError, json.JSONDecodeError):
                cached = False
        if cached:
            progress(
                f"Chapter {chapter.number}/{len(CHAPTERS)}: using local cache"
            )
        else:
            progress(
                f"Chapter {chapter.number}/{len(CHAPTERS)}: {chapter.title}"
            )
            synthesize_chatterbox(
                project,
                profile,
                expected_text,
                clip_path,
                allow_model_download=allow_model_download,
                progress=progress,
            )
        clip_paths.append(clip_path)
        speech_durations.append(media_duration(clip_path, ffprobe))

    chapter_durations = [
        max(
            chapter.duration,
            SPEECH_DELAY + speech_duration + TAIL_PADDING,
        )
        for chapter, speech_duration in zip(CHAPTERS, speech_durations)
    ]
    starts = _chapter_starts(chapter_durations)
    total_duration = sum(chapter_durations)
    track_path = output_directory / "narration.m4a"
    progress("Assembling and loudness-normalizing the local narration track...")
    _build_mixed_track(
        clip_paths,
        starts,
        total_duration,
        track_path,
        ffmpeg,
        progress,
    )

    plan_path = output_directory / "narration-plan.json"
    payload = {
        "schema": 1,
        "synthetic_voice": True,
        "generated_at": utc_now(),
        "voice_profile": profile.profile_id,
        "profile_sha256": profile.sha256,
        "model": "chatterbox-turbo",
        "chapter_starts": starts,
        "chapter_durations": chapter_durations,
        "speech_durations": speech_durations,
        "speech_delay": SPEECH_DELAY,
        "track": track_path.name,
        "clips": [path.name for path in clip_paths],
        "watermark": "preserved model-provided watermark",
    }
    plan_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_directory / "narration.srt").write_text(
        subtitle_file(
            tuple(chapter_durations),
            tuple(speech_durations),
            SPEECH_DELAY,
        ),
        encoding="utf-8",
    )
    (output_directory / "narration-script.md").write_text(
        narration_script(tuple(chapter_durations)),
        encoding="utf-8",
    )
    project.audit(
        "dome_narration_generated",
        {
            "profile_id": profile.profile_id,
            "plan": project.relative(plan_path),
            "duration_s": total_duration,
        },
    )
    progress(f"Saved local narration plan: {plan_path}")
    return plan_path


def export_dome_video(
    plan_path: Path,
    output_path: Path,
    *,
    fps: int = 30,
    size: str = "1600x900",
    progress: Callable[[str], None] = print,
) -> Path:
    """Run the existing renderer with an already-generated local voice plan."""
    import launcher_common as _lc

    launcher = Path(__file__).resolve().parents[1] / "two_v_masterclass.py"
    if not launcher.is_file():
        raise FileNotFoundError(f"2V masterclass launcher not found: {launcher}")
    # two_v_masterclass.py takes no CLI flags anymore -- it reads a
    # launcher_common config ticket at startup instead (see
    # two_v_demo/app.py's main()). Write that ticket before spawning it,
    # the same way the launcher GUI's "2V Masterclass" tab does.
    _lc.write_config("two_v_masterclass", {
        "action": "export_video",
        "export_video": str(output_path),
        "local_narration_plan": str(plan_path),
        "fps": max(1, fps),
        "size": size,
    })
    progress("Rendering the dome video with the local narration track...")
    result = subprocess.run(
        [sys.executable, str(launcher)],
        cwd=str(launcher.parent),
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.stdout:
        progress(result.stdout.strip())
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or f"Dome renderer exited with status {result.returncode}"
        )
    progress(f"Saved narrated video: {output_path}")
    return output_path
