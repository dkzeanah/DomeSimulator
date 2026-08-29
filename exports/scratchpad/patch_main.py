"""Let main() choose a lesson, and route selftest / report through it."""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new, 1)


sub('''    cfg = _lc.consume_config("two_v_masterclass")
    action = cfg.get("action", "run")''',
    '''    cfg = _lc.consume_config("two_v_masterclass")
    action = cfg.get("action", "run")
    # Imported here, not at module scope: the lesson modules import this
    # module's render kit, so the registry can only be built once this
    # module has finished loading.
    from .lesson_registry import get_lesson, lesson_menu

    try:
        lesson = get_lesson(cfg.get("lesson"))
    except ValueError as exc:
        print(exc)
        print(lesson_menu())
        return 2''')

sub('''    if action == "selftest":
        validate_geometry()
        print(calculation_report())
        print("\\nselftest OK")
        return 0
    if action == "report":
        print(calculation_report())
        return 0''',
    '''    if action == "list_lessons":
        print(lesson_menu())
        return 0
    if action == "selftest":
        validate_geometry()
        lesson.validate()
        if lesson.selftest is not None:
            lesson.selftest()
        print((lesson.report or calculation_report)())
        print(f"\\nselftest OK: {lesson.title}, {len(lesson.chapters)} chapters")
        return 0
    if action == "report":
        print((lesson.report or calculation_report)())
        return 0''')

sub('''        script_path.write_text(narration_script(), encoding="utf-8")
        subtitle_path = script_path.with_suffix(".srt")
        subtitle_path.write_text(subtitle_file(), encoding="utf-8")''',
    '''        script_path.write_text(
            narration_script(None, lesson.chapters, lesson.title),
            encoding="utf-8",
        )
        subtitle_path = script_path.with_suffix(".srt")
        subtitle_path.write_text(
            subtitle_file(None, None, 0.0, lesson.chapters), encoding="utf-8"
        )''')

sub('''            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume)
            plan = synthesize_narration(
                output_path.parent / f"{output_path.stem}-voice-{voice_slug}",
                output_path, ffmpeg, ffprobe, voice=voice, rate=voice_rate,
                pitch=voice_pitch, volume=voice_volume)''',
    '''            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume, lesson.chapters)
            plan = synthesize_narration(
                output_path.parent / f"{output_path.stem}-voice-{voice_slug}",
                output_path, ffmpeg, ffprobe, voice=voice, rate=voice_rate,
                pitch=voice_pitch, volume=voice_volume,
                chapters=lesson.chapters)''')

sub('''        script_path, subtitle_path = write_companion_files(
            output_path, plan.chapter_durations, plan.speech_durations,
            SPEECH_DELAY)''',
    '''        script_path, subtitle_path = write_companion_files(
            output_path, plan.chapter_durations, plan.speech_durations,
            SPEECH_DELAY, lesson.chapters, lesson.title)''')

sub('''    app = MasterclassApp(
        size=size,
        fullscreen=bool(cfg.get("fullscreen", False)),
        hidden=action in ("shots", "export_video"),
    )''',
    '''    app = MasterclassApp(
        size=size,
        fullscreen=bool(cfg.get("fullscreen", False)),
        hidden=action in ("shots", "export_video"),
        lesson=lesson,
    )''')

sub('''        app.render_shots(times, Path("two_v_demo_output"))''',
    '''        app.render_shots(times, Path("two_v_demo_output") / lesson.key)''')

path.write_text(src, encoding="utf-8")
print("main() is lesson-aware")
