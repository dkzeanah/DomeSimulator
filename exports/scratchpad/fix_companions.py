"""Write the .srt and narration script for an already-rendered lesson MP4.

The export writes these last, so a fault there leaves a finished video with
no sidecars.  Rebuilding them needs only the cached chapter clips: their
measured durations are what set the timeline in the first place, so the
captions come out identical to what the export would have written.
"""

import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

from pathlib import Path

from two_v_demo.audio import (
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    SPEECH_DELAY,
    companion_ffprobe,
    resolve_executable,
    synthesize_narration,
    voice_cache_slug,
)
from two_v_demo.lesson_registry import get_lesson
from two_v_demo.narration import write_companion_files

key, video = sys.argv[1], Path(sys.argv[2])
lesson = get_lesson(key)
if not video.is_file():
    raise SystemExit(f"no such video: {video}")

ffmpeg = resolve_executable("ffmpeg", None)
ffprobe = companion_ffprobe(ffmpeg, None)
# The cache key includes whether the headline is spoken, so a montage
# and a lesson with identical text would still key differently.
speak_promise = lesson.style != "hype"
rate = lesson.voice_rate or DEFAULT_RATE
slug = voice_cache_slug(
    DEFAULT_VOICE, rate, DEFAULT_PITCH, DEFAULT_VOLUME, lesson.chapters,
    speak_promise,
)
stems = video.parent / f"{video.stem}-voice-{slug}"
missing = [
    chapter.number
    for chapter in lesson.chapters
    if not (stems / f"chapter_{chapter.number}.mp3").is_file()
]
if missing:
    raise SystemExit(
        f"{len(missing)} chapter clips are not cached ({', '.join(missing)}); "
        "run the export instead so they can be synthesized"
    )

plan = synthesize_narration(
    stems,
    video.parent / f"{video.stem}-narration.m4a",
    ffmpeg,
    ffprobe,
    rate=rate,
    chapters=lesson.chapters,
    speak_promise=speak_promise,
    progress=lambda message: None,
)
script_path, subtitle_path = write_companion_files(
    video,
    plan.chapter_durations,
    plan.speech_durations,
    SPEECH_DELAY,
    lesson.chapters,
    lesson.title,
    speak_promise,
)
print(f"{lesson.title}: {plan.total_duration / 60:.1f} min")
print(f"  saved {script_path.name} ({script_path.stat().st_size} bytes)")
print(f"  saved {subtitle_path.name} ({subtitle_path.stat().st_size} bytes)")
