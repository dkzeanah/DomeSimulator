"""YouTube companion assets for the deterministic lesson timeline."""

from __future__ import annotations

import re
from pathlib import Path

from .lessons import CHAPTERS, Chapter


# A caption longer than this is hard to read before it is replaced.
MAX_CAPTION_CHARS = 96
SENTENCE_BREAK = re.compile(r'(?<=[.!?])\s+')


def _timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000.0))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def _durations(
    chapter_durations: tuple[float, ...] | None,
    chapters: tuple[Chapter, ...],
) -> tuple[float, ...]:
    values = chapter_durations or tuple(chapter.duration for chapter in chapters)
    if len(values) != len(chapters):
        raise ValueError("chapter duration count does not match chapter count")
    return values


def _split_long(sentence: str) -> list[str]:
    """Break one over-long sentence into near-equal readable pieces.

    Filling each cue to the limit and letting the remainder fall where it
    may produces orphans -- a full line followed by two words.  Deciding
    how many pieces are needed first, then cutting near each ideal
    boundary, keeps them even.  A comma is preferred to a bare space
    because it is where a reader would pause anyway.
    """
    if len(sentence) <= MAX_CAPTION_CHARS:
        return [sentence]
    parts: list[str] = []
    rest = sentence
    while len(rest) > MAX_CAPTION_CHARS:
        # Recompute the ideal cue length from what is *left*, not from the
        # original sentence: a stale target is what leaves a two-word tail
        # after an otherwise full-length cue.
        pieces = -(-len(rest) // MAX_CAPTION_CHARS)
        target = len(rest) / pieces
        # Looking a little past the ideal point finds a better break, but
        # never past the limit itself, or the cue overruns it.
        window = rest[:min(len(rest) - 1, MAX_CAPTION_CHARS,
                           max(int(target * 1.15), 24))]
        cut = window.rfind(",")
        if cut < target * 0.5:
            cut = window.rfind(" ")
        if cut <= 0:
            # Nothing to break on near the ideal point; take the last
            # space that still fits rather than overrunning the limit.
            cut = rest[:MAX_CAPTION_CHARS].rfind(" ")
        if cut <= 0:
            break
        parts.append(rest[:cut + 1].strip())
        rest = rest[cut + 1:].strip()
    if rest:
        parts.append(rest)
    return parts


def caption_phrases(
    chapter: Chapter,
    speak_promise: bool = True,
) -> tuple[str, ...]:
    """Split one chapter into caption-sized pieces, on sentence breaks.

    The stored narration is a tuple of source lines, not of sentences, so
    it is joined back into prose first and then re-split where a reader
    would actually pause.  The speech is synthesized from the same joined
    prose, so changing this never changes the audio.
    """
    prose = " ".join(
        ((chapter.promise,) if speak_promise else ()) + tuple(chapter.narration)
    )
    phrases: list[str] = []
    for sentence in SENTENCE_BREAK.split(" ".join(prose.split())):
        sentence = sentence.strip()
        if sentence:
            phrases.extend(_split_long(sentence))
    return tuple(phrases) or (chapter.promise,)


def narration_script(
    chapter_durations: tuple[float, ...] | None = None,
    chapters: tuple[Chapter, ...] = CHAPTERS,
    title: str = "2V Geodesic Masterclass",
    speak_promise: bool = True,
) -> str:
    """Return a timed, record-ready voiceover script."""
    lines = [
        f"# {title} - Voiceover Script",
        "",
        "The timestamps match the deterministic ModernGL video export.",
        "Read conversationally; the on-screen equations carry the dense numbers.",
        "",
    ]
    cursor = 0.0
    durations = _durations(chapter_durations, chapters)
    for chapter, duration in zip(chapters, durations):
        end = cursor + duration
        lines.extend([
            f"## {chapter.number}. {chapter.title}",
            "",
            f"Time: {_timestamp(cursor).replace(',', '.')} - "
            f"{_timestamp(end).replace(',', '.')}",
            "",
        ])
        # A voiceover script has to be readable aloud as written. When the
        # promise is on-screen type rather than spoken, printing it here as
        # a paragraph would have the reader say a line the video does not.
        if speak_promise:
            lines.extend([chapter.promise, ""])
        else:
            lines.extend([f"*on screen: {chapter.promise}*", ""])
        lines.extend([
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
    chapters: tuple[Chapter, ...] = CHAPTERS,
    speak_promise: bool = True,
) -> str:
    """Return readable SRT captions split across each chapter's statements."""
    entries: list[str] = []
    cursor = 0.0
    sequence = 1
    durations = _durations(chapter_durations, chapters)
    if speech_durations is not None and len(speech_durations) != len(chapters):
        raise ValueError("speech duration count does not match chapter count")
    for chapter_index, (chapter, duration) in enumerate(zip(chapters, durations)):
        phrases = caption_phrases(chapter, speak_promise)
        speech_span = (
            speech_durations[chapter_index]
            if speech_durations is not None
            else duration
        )
        # Speech takes about as long as the text is long, so give each
        # cue a share of the chapter proportional to its own length
        # instead of an equal slice.  A three-word cue no longer sits
        # on screen as long as a full sentence.
        weights = [max(1, len(phrase)) for phrase in phrases]
        total_weight = sum(weights)
        offsets = [0.0]
        for weight in weights:
            offsets.append(offsets[-1] + speech_span * weight / total_weight)
        for index, phrase in enumerate(phrases):
            start = cursor + speech_delay + offsets[index]
            end = cursor + speech_delay + offsets[index + 1] - 0.08
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
    chapters: tuple[Chapter, ...] = CHAPTERS,
    title: str = "2V Geodesic Masterclass",
    speak_promise: bool = True,
) -> tuple[Path, Path]:
    """Write a voiceover Markdown file and upload-ready SRT beside a video."""
    base = video_path.with_suffix("")
    script_path = base.parent / f"{base.name}-narration.md"
    subtitle_path = base.parent / f"{base.name}.srt"
    script_path.write_text(
        narration_script(chapter_durations, chapters, title, speak_promise),
        encoding="utf-8",
    )
    subtitle_path.write_text(
        subtitle_file(chapter_durations, speech_durations, speech_delay,
                      chapters, speak_promise),
        encoding="utf-8",
    )
    return script_path, subtitle_path
