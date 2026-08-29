"""Make MasterclassApp play any Lesson, not just the built-in 2V one."""

from pathlib import Path

ROOT = Path(r"C:\Users\Don\Desktop\DomeSim")
path = ROOT / "two_v_demo/app.py"
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str, count: int = 0) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new) if count == 0 else src.replace(old, new, count)


sub(
    '''"""ModernGL renderer for the standalone 2V geodesic masterclass."""''',
    '''"""ModernGL renderer for the standalone masterclass lessons.

One renderer, several lessons.  ``MasterclassApp`` knows how to play a
:class:`~two_v_demo.lessons.Lesson`: it walks the lesson's chapters, asks
the lesson to paint each stage, and asks it for any live figures the
chapter wants under its fixed equations.  The 2V geodesic lesson is the
default and is still drawn by the ``scene_*`` methods below; the hex,
zome and construction lessons supply their own painters.
"""''',
)

sub(
    '''from .lessons import (
    CHAPTERS,
    chapter_at_time,
    chapter_start,
    timeline_duration,
)''',
    '''from .lessons import (
    CHAPTERS,
    TWO_V_LESSON,
    Lesson,
    chapter_at_time,
    chapter_start,
    timeline_duration,
)''',
)

sub(
    '''    def __init__(
        self,
        size: tuple[int, int] = (1600, 900),
        fullscreen: bool = False,
        hidden: bool = False,
    ) -> None:''',
    '''    def __init__(
        self,
        size: tuple[int, int] = (1600, 900),
        fullscreen: bool = False,
        hidden: bool = False,
        lesson: Lesson | None = None,
    ) -> None:''',
)

sub(
    '''        pygame.display.set_caption("2V Geodesic Masterclass")''',
    '''        self.lesson = lesson or TWO_V_LESSON
        self.lesson.validate()
        self.chapters = self.lesson.chapters
        pygame.display.set_caption(self.lesson.title)''',
)

sub(
    '''        self.chapter_durations = tuple(chapter.duration for chapter in CHAPTERS)
        self.total_duration = timeline_duration(self.chapter_durations)''',
    '''        self.chapter_durations = tuple(
            chapter.duration for chapter in self.chapters
        )
        self.total_duration = timeline_duration(
            self.chapter_durations, self.chapters
        )''',
)

sub(
    '''        self.camera_yaw = CHAPTERS[0].camera[0]
        self.camera_pitch = CHAPTERS[0].camera[1]
        self.camera_distance = CHAPTERS[0].camera[2]''',
    '''        self.camera_yaw = self.chapters[0].camera[0]
        self.camera_pitch = self.chapters[0].camera[1]
        self.camera_distance = self.chapters[0].camera[2]''',
)

sub(
    '''        self.output_dir = Path("two_v_demo_output")''',
    '''        self.output_dir = Path("two_v_demo_output")
        self.stage_state: dict[str, object] = {}''',
)

sub(
    '''        self.world_labels = []
        self.add_ground(opaque)
        dispatch = getattr(self, f"scene_{stage}")
        dispatch(opaque, transparent, progress)
        return opaque, transparent''',
    '''        self.world_labels = []
        self.add_ground(opaque)
        painter = self.lesson.scenes.get(stage)
        if painter is not None:
            painter(self, opaque, transparent, progress)
        else:
            getattr(self, f"scene_{stage}")(opaque, transparent, progress)
        return opaque, transparent''',
)

sub(
    '''    def dynamic_equations(self, stage: str) -> list[str]:
        equations: list[str] = []
        if stage == "audit":''',
    '''    def dynamic_equations(self, stage: str) -> list[str]:
        if self.lesson.equations is not None:
            return list(self.lesson.equations(self, stage))
        equations: list[str] = []
        if stage == "audit":''',
)

sub(
    '''        chapter = CHAPTERS[self.chapter_index]
        self.ui_buttons.clear()''',
    '''        chapter = self.chapters[self.chapter_index]
        self.ui_buttons.clear()''',
)

sub(
    '''        self.draw_text(surface, "2V / GEODESIC MASTERCLASS",''',
    '''        self.draw_text(surface, self.lesson.brand,''',
)

sub(
    '''        cell_width = (timeline_width - gap * (len(CHAPTERS) - 1)) / len(CHAPTERS)
        for index, item in enumerate(CHAPTERS):''',
    '''        count = len(self.chapters)
        cell_width = (timeline_width - gap * (count - 1)) / count
        # A long lesson cannot label every cell; label about eight of them.
        label_step = max(1, round(count / 8))
        for index, item in enumerate(self.chapters):''',
)

sub(
    '''            if width >= 1300 and index in (0, 2, 4, 6, 8, 10, 12, 13):''',
    '''            if width >= 1300 and (index % label_step == 0 or index == count - 1):''',
)

sub(
    '''    def set_chapter(self, index: int) -> None:
        self.chapter_index = index % len(CHAPTERS)
        self.timeline = chapter_start(self.chapter_index, self.chapter_durations)''',
    '''    def set_chapter(self, index: int) -> None:
        self.chapter_index = index % len(self.chapters)
        self.timeline = chapter_start(
            self.chapter_index, self.chapter_durations, self.chapters
        )''',
)

sub(
    '''    def reset_camera(self) -> None:
        chapter = CHAPTERS[self.chapter_index]''',
    '''    def reset_camera(self) -> None:
        chapter = self.chapters[self.chapter_index]''',
)

src = src.replace(
    '''        self.chapter_index, self.chapter_progress = chapter_at_time(
            self.timeline, self.chapter_durations
        )''',
    '''        self.chapter_index, self.chapter_progress = chapter_at_time(
            self.timeline, self.chapter_durations, self.chapters
        )''',
)

sub(
    '''    def camera(self) -> tuple[np.ndarray, np.ndarray]:
        chapter = CHAPTERS[self.chapter_index]''',
    '''    def camera(self) -> tuple[np.ndarray, np.ndarray]:
        chapter = self.chapters[self.chapter_index]''',
)

sub(
    '''        chapter = CHAPTERS[self.chapter_index]
        opaque, transparent = self.build_scene(chapter.stage, self.chapter_progress)''',
    '''        chapter = self.chapters[self.chapter_index]
        opaque, transparent = self.build_scene(chapter.stage, self.chapter_progress)''',
)

sub(
    '''            path = self.output_dir / f"2v_{int(time.time() * 1000)}.png"''',
    '''            path = self.output_dir / (
                f"{self.lesson.snapshot_prefix}_{int(time.time() * 1000)}.png"
            )''',
)

sub(
    '''            expected = len(CHAPTERS)''',
    '''            expected = len(self.chapters)''',
)

sub(
    '''            print(
                f"Local narration: {plan.voice}, {self.total_duration:.1f}s "
                f"across {len(CHAPTERS)} chapters"
            )''',
    '''            print(
                f"Local narration: {plan.voice}, {self.total_duration:.1f}s "
                f"across {len(self.chapters)} chapters"
            )''',
)

sub(
    '''            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume
            )''',
    '''            voice_slug = voice_cache_slug(
                voice, voice_rate, voice_pitch, voice_volume, self.chapters
            )''',
)

sub(
    '''                volume=voice_volume,
            )
            self.chapter_durations = plan.chapter_durations
            self.total_duration = plan.total_duration
            print(
                f"Natural narration: {voice}, {self.total_duration:.1f}s "
                f"across {len(CHAPTERS)} chapters"
            )''',
    '''                volume=voice_volume,
                chapters=self.chapters,
            )
            self.chapter_durations = plan.chapter_durations
            self.total_duration = plan.total_duration
            print(
                f"Natural narration: {voice}, {self.total_duration:.1f}s "
                f"across {len(self.chapters)} chapters"
            )''',
)

sub(
    '''                self.chapter_index, self.chapter_progress = chapter_at_time(
                    self.timeline, self.chapter_durations
                )''',
    '''                self.chapter_index, self.chapter_progress = chapter_at_time(
                    self.timeline, self.chapter_durations, self.chapters
                )''',
)

sub(
    '''            script_path, subtitle_path = write_companion_files(
                path,
                plan.chapter_durations,
                plan.speech_durations,
                speech_delay,
            )
            print(f"saved {plan.track_path}")
        else:
            script_path, subtitle_path = write_companion_files(path)''',
    '''            script_path, subtitle_path = write_companion_files(
                path,
                plan.chapter_durations,
                plan.speech_durations,
                speech_delay,
                self.chapters,
                self.lesson.title,
            )
            print(f"saved {plan.track_path}")
        else:
            script_path, subtitle_path = write_companion_files(
                path,
                chapters=self.chapters,
                title=self.lesson.title,
            )''',
)

path.write_text(src, encoding="utf-8")
print("app.py patched")
