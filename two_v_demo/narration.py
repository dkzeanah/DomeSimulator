"""YouTube companion assets for the deterministic lesson timeline."""

from __future__ import annotations

from pathlib import Path

from .lessons import CHAPTERS


def _timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000.0))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def _durations(chapter_durations: tuple[float, ...] | None) -> tuple[float, ...]:
    values = chapter_durations or tuple(chapter.duration for chapter in CHAPTERS)
    if len(values) != len(CHAPTERS):
        raise ValueError("chapter duration count does not match chapter count")
    return values


def narration_script(
    chapter_durations: tuple[float, ...] | None = None,
) -> str:
    """Return a timed, record-ready voiceover script."""
    lines = [
        "# 2V Geodesic Masterclass - Voiceover Script",
        "",
        "The timestamps match the deterministic ModernGL video export.",
        "Read conversationally; the on-screen equations carry the dense numbers.",
        "",
    ]
    cursor = 0.0
    durations = _durations(chapter_durations)
    for chapter, duration in zip(CHAPTERS, durations):
        end = cursor + duration
        lines.extend([
            f"## {chapter.number}. {chapter.title}",
            "",
            f"Time: {_timestamp(cursor).replace(',', '.')} - "
            f"{_timestamp(end).replace(',', '.')}",
            "",
            chapter.promise,
            "",
            " ".join(chapter.narration),
            "",
            "On-screen math:",
            "",
        ])
        lines.extend(f"- {equation}" for equation in chapter.equations)
        lines.append("")
        cursor = end
    return "\n".join(lines)


def subtitle_file(
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
) -> str:
    """Return readable SRT captions split across each chapter's statements."""
    entries: list[str] = []
    cursor = 0.0
    sequence = 1
    durations = _durations(chapter_durations)
    if speech_durations is not None and len(speech_durations) != len(CHAPTERS):
        raise ValueError("speech duration count does not match chapter count")
    for chapter_index, (chapter, duration) in enumerate(zip(CHAPTERS, durations)):
        phrases = (chapter.promise,) + chapter.narration
        speech_span = (
            speech_durations[chapter_index]
            if speech_durations is not None
            else duration
        )
        segment_duration = speech_span / len(phrases)
        for index, phrase in enumerate(phrases):
            start = cursor + speech_delay + index * segment_duration
            end = cursor + speech_delay + (index + 1) * segment_duration - 0.08
            entries.extend([
                str(sequence),
                f"{_timestamp(start)} --> {_timestamp(max(start + 0.5, end))}",
                phrase,
                "",
            ])
            sequence += 1
        cursor += duration
    return "\n".join(entries)


def write_companion_files(
    video_path: Path,
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
) -> tuple[Path, Path]:
    """Write a voiceover Markdown file and upload-ready SRT beside a video."""
    base = video_path.with_suffix("")
    script_path = base.parent / f"{base.name}-narration.md"
    subtitle_path = base.parent / f"{base.name}.srt"
    script_path.write_text(
        narration_script(chapter_durations),
        encoding="utf-8",
    )
    subtitle_path.write_text(
        subtitle_file(chapter_durations, speech_durations, speech_delay),
        encoding="utf-8",
    )
    return script_path, subtitle_path
