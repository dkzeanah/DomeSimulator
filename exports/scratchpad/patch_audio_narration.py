"""Thread an explicit chapter tuple through narration.py and audio.py."""

from pathlib import Path

ROOT = Path(r"C:\Users\Don\Desktop\DomeSim")


def patch(path: Path, pairs: list[tuple[str, str]]) -> None:
    src = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in src:
            raise SystemExit(f"{path.name}: pattern not found:\n{old[:200]}")
        src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print(f"{path.name} patched")


patch(ROOT / "two_v_demo/narration.py", [
    ("from .lessons import CHAPTERS",
     "from .lessons import CHAPTERS, Chapter"),
    ("""def _durations(chapter_durations: tuple[float, ...] | None) -> tuple[float, ...]:
    values = chapter_durations or tuple(chapter.duration for chapter in CHAPTERS)
    if len(values) != len(CHAPTERS):
        raise ValueError("chapter duration count does not match chapter count")
    return values""",
     """def _durations(
    chapter_durations: tuple[float, ...] | None,
    chapters: tuple[Chapter, ...],
) -> tuple[float, ...]:
    values = chapter_durations or tuple(chapter.duration for chapter in chapters)
    if len(values) != len(chapters):
        raise ValueError("chapter duration count does not match chapter count")
    return values"""),
    ("""def narration_script(
    chapter_durations: tuple[float, ...] | None = None,
) -> str:
    \"\"\"Return a timed, record-ready voiceover script.\"\"\"
    lines = [
        "# 2V Geodesic Masterclass - Voiceover Script",""",
     """def narration_script(
    chapter_durations: tuple[float, ...] | None = None,
    chapters: tuple[Chapter, ...] = CHAPTERS,
    title: str = "2V Geodesic Masterclass",
) -> str:
    \"\"\"Return a timed, record-ready voiceover script.\"\"\"
    lines = [
        f"# {title} - Voiceover Script","""),
    ("""    cursor = 0.0
    durations = _durations(chapter_durations)
    for chapter, duration in zip(CHAPTERS, durations):""",
     """    cursor = 0.0
    durations = _durations(chapter_durations, chapters)
    for chapter, duration in zip(chapters, durations):"""),
    ("""def subtitle_file(
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
) -> str:""",
     """def subtitle_file(
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> str:"""),
    ("""    durations = _durations(chapter_durations)
    if speech_durations is not None and len(speech_durations) != len(CHAPTERS):
        raise ValueError("speech duration count does not match chapter count")
    for chapter_index, (chapter, duration) in enumerate(zip(CHAPTERS, durations)):""",
     """    durations = _durations(chapter_durations, chapters)
    if speech_durations is not None and len(speech_durations) != len(chapters):
        raise ValueError("speech duration count does not match chapter count")
    for chapter_index, (chapter, duration) in enumerate(zip(chapters, durations)):"""),
    ("""def write_companion_files(
    video_path: Path,
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
) -> tuple[Path, Path]:""",
     """def write_companion_files(
    video_path: Path,
    chapter_durations: tuple[float, ...] | None = None,
    speech_durations: tuple[float, ...] | None = None,
    speech_delay: float = 0.0,
    chapters: tuple[Chapter, ...] = CHAPTERS,
    title: str = "2V Geodesic Masterclass",
) -> tuple[Path, Path]:"""),
    ("""    script_path.write_text(
        narration_script(chapter_durations),
        encoding="utf-8",
    )
    subtitle_path.write_text(
        subtitle_file(chapter_durations, speech_durations, speech_delay),
        encoding="utf-8",
    )""",
     """    script_path.write_text(
        narration_script(chapter_durations, chapters, title),
        encoding="utf-8",
    )
    subtitle_path.write_text(
        subtitle_file(chapter_durations, speech_durations, speech_delay, chapters),
        encoding="utf-8",
    )"""),
])


NL = chr(92) + "n"

patch(ROOT / "two_v_demo/audio.py", [
    ("from .lessons import CHAPTERS",
     "from .lessons import CHAPTERS, Chapter"),
    ("""def spoken_chapter_text(index: int) -> str:
    \"\"\"Return fluent prose for one chapter, without reading equations aloud.\"\"\"
    chapter = CHAPTERS[index]""",
     """def spoken_chapter_text(
    index: int,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> str:
    \"\"\"Return fluent prose for one chapter, without reading equations aloud.\"\"\"
    chapter = chapters[index]"""),
    ("""def voice_cache_slug(
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
) -> str:""",
     """def voice_cache_slug(
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> str:"""),
    ("""        + [spoken_chapter_text(index) for index in range(len(CHAPTERS))]""",
     """        + [
            spoken_chapter_text(index, chapters)
            for index in range(len(chapters))
        ]"""),
    ("""    volume: str = DEFAULT_VOLUME,
    progress: Callable[[str], None] = print,
) -> NarrationPlan:""",
     """    volume: str = DEFAULT_VOLUME,
    progress: Callable[[str], None] = print,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> NarrationPlan:"""),
    ("""    for index, chapter in enumerate(CHAPTERS):
        clip_path = output_directory / f"chapter_{chapter.number}.mp3\"""",
     """    for index, chapter in enumerate(chapters):
        clip_path = output_directory / f"chapter_{chapter.number}.mp3\""""),
    ("""            progress(f"voice {chapter.number}/{len(CHAPTERS):02d}: cached")""",
     """            progress(f"voice {chapter.number}/{len(chapters):02d}: cached")"""),
    ("""                f"voice {chapter.number}/{len(CHAPTERS):02d}: \"""",
     """                f"voice {chapter.number}/{len(chapters):02d}: \""""),
    ("""            asyncio.run(_synthesize_one(
                spoken_chapter_text(index),""",
     """            asyncio.run(_synthesize_one(
                spoken_chapter_text(index, chapters),"""),
    ("""        for chapter, speech_duration in zip(CHAPTERS, speech_durations)""",
     """        for chapter, speech_duration in zip(chapters, speech_durations)"""),
])
print("done")
