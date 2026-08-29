"""Let the local-voice bridge narrate any masterclass lesson, not just 2V."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\local_voice_studio\dome.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:\n" + old[:240])
    s = s.replace(old, new, 1)


sub(
    '"""Local voice narration bridge for the standalone 2V masterclass."""',
    '"""Local voice narration bridge for the standalone masterclass lessons.\n'
    "\n"
    "The renderer plays four lessons of different lengths, so everything here\n"
    "is keyed on a lesson rather than on the 2V chapter list.  The lesson key\n"
    "is written into the narration plan and read back out at render time, so a\n"
    "plan can never be pointed at the wrong lesson by accident.\n"
    '"""',
)

sub(
    "from two_v_demo.lessons import CHAPTERS\n"
    "from two_v_demo.narration import narration_script, subtitle_file",
    "from two_v_demo.lesson_registry import get_lesson\n"
    "from two_v_demo.narration import narration_script, subtitle_file",
)

sub(
    """def build_dome_narration(
    project: VoiceProject,
    profile: VoiceProfile,
    *,
    ffmpeg_path: str | None = None,
    ffprobe_path: str | None = None,
    allow_model_download: bool = False,
    progress: Callable[[str], None] = print,
) -> Path:
    \"\"\"Generate chapter WAVs, a mixed track, timing JSON, script, and captions.\"\"\"
    if not project.consented:
        raise PermissionError("Project ownership statement is required")
    ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
    ffprobe = companion_ffprobe(ffmpeg, ffprobe_path)
    output_directory = (
        project.root / "outputs" / "dome" / f"2v-{profile.profile_id}"
    )
    output_directory.mkdir(parents=True, exist_ok=True)""",
    """def build_dome_narration(
    project: VoiceProject,
    profile: VoiceProfile,
    *,
    lesson: str = "2v",
    ffmpeg_path: str | None = None,
    ffprobe_path: str | None = None,
    allow_model_download: bool = False,
    progress: Callable[[str], None] = print,
) -> Path:
    \"\"\"Generate chapter WAVs, a mixed track, timing JSON, script, and captions.

    ``lesson`` is a masterclass lesson key (``2v``, ``build``, ``hex``,
    ``zome``).  Each lesson gets its own output folder, so profiles and
    lessons can be mixed freely without one overwriting another's clips.
    \"\"\"
    if not project.consented:
        raise PermissionError("Project ownership statement is required")
    chosen = get_lesson(lesson)
    chapters = chosen.chapters
    ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
    ffprobe = companion_ffprobe(ffmpeg, ffprobe_path)
    output_directory = (
        project.root / "outputs" / "dome" / f"{chosen.key}-{profile.profile_id}"
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    progress(f"Lesson: {chosen.title} ({len(chapters)} chapters)")""",
)

sub(
    "    for index, chapter in enumerate(CHAPTERS):\n"
    "        clip_path = output_directory / f\"chapter_{chapter.number}.wav\"",
    "    for index, chapter in enumerate(chapters):\n"
    "        clip_path = output_directory / f\"chapter_{chapter.number}.wav\"",
)

sub(
    "        expected_text = spoken_chapter_text(index)",
    "        expected_text = spoken_chapter_text(index, chapters)",
)

sub(
    '                f"Chapter {chapter.number}/{len(CHAPTERS)}: using local cache"',
    '                f"Chapter {chapter.number}/{len(chapters)}: using local cache"',
)

sub(
    '                f"Chapter {chapter.number}/{len(CHAPTERS)}: {chapter.title}"',
    '                f"Chapter {chapter.number}/{len(chapters)}: {chapter.title}"',
)

sub(
    "        for chapter, speech_duration in zip(CHAPTERS, speech_durations)",
    "        for chapter, speech_duration in zip(chapters, speech_durations)",
)

sub(
    '        "generated_at": utc_now(),\n        "voice_profile": profile.profile_id,',
    '        "generated_at": utc_now(),\n'
    '        "lesson": chosen.key,\n'
    '        "lesson_title": chosen.title,\n'
    '        "chapter_count": len(chapters),\n'
    '        "voice_profile": profile.profile_id,',
)

sub(
    """        subtitle_file(
            tuple(chapter_durations),
            tuple(speech_durations),
            SPEECH_DELAY,
        ),""",
    """        subtitle_file(
            tuple(chapter_durations),
            tuple(speech_durations),
            SPEECH_DELAY,
            chapters,
        ),""",
)

sub(
    "        narration_script(tuple(chapter_durations)),",
    "        narration_script(tuple(chapter_durations), chapters, chosen.title),",
)

sub(
    """        {
            "profile_id": profile.profile_id,
            "plan": project.relative(plan_path),
            "duration_s": total_duration,
        },""",
    """        {
            "profile_id": profile.profile_id,
            "lesson": chosen.key,
            "plan": project.relative(plan_path),
            "duration_s": total_duration,
        },""",
)

sub(
    """    launcher = Path(__file__).resolve().parents[1] / "two_v_masterclass.py"
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
    })""",
    """    launcher = Path(__file__).resolve().parents[1] / "two_v_masterclass.py"
    if not launcher.is_file():
        raise FileNotFoundError(f"masterclass launcher not found: {launcher}")
    # The plan records which lesson it was spoken for; take the key from
    # there rather than from a second argument, so a plan can never be
    # rendered against a lesson with a different chapter count.
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read narration plan: {plan_path}") from exc
    lesson_key = str(plan.get("lesson", "2v"))
    progress(f"Narration plan lesson: {lesson_key}")
    # two_v_masterclass.py takes no CLI flags anymore -- it reads a
    # launcher_common config ticket at startup instead (see
    # two_v_demo/app.py's main()). Write that ticket before spawning it,
    # the same way the launcher GUI's "Masterclass" tab does.
    _lc.write_config("two_v_masterclass", {
        "action": "export_video",
        "lesson": lesson_key,
        "export_video": str(output_path),
        "local_narration_plan": str(plan_path),
        "fps": max(1, fps),
        "size": size,
    })""",
)

p.write_text(s, encoding="utf-8")
print("local_voice_studio/dome.py is lesson-aware")
