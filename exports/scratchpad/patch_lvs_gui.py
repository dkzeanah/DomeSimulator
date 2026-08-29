"""Add a Lesson picker to Local Voice Studio's Dome Narration tab."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\local_voice_studio\gui.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:\n" + old[:240])
    s = s.replace(old, new, 1)


sub(
    '''        tab = self._tab(self.notebook, "Dome Narration")
        ttk.Label(
            tab,
            text="Generate the complete 2V lesson with your selected local profile.",
            font=("Segoe UI Semibold", 14),
            foreground="#58d5ff",
        ).pack(anchor="w")
        ttk.Label(
            tab,
            text=(
                "Each chapter is synthesized locally, timed from its actual WAV, "
                "mixed to a -16 LUFS AAC track, and exported with JSON and SRT. "
                "The renderer then muxes that track into the MP4."
            ),
            wraplength=950,
            justify=LEFT,
        ).pack(anchor="w", pady=10)
        line = ttk.Frame(tab)
        line.pack(anchor="w", pady=8)
        ttk.Label(line, text="Voice profile").pack(side=LEFT)''',
    '''        tab = self._tab(self.notebook, "Dome Narration")
        ttk.Label(
            tab,
            text="Narrate a complete masterclass lesson in your own local voice.",
            font=("Segoe UI Semibold", 14),
            foreground="#58d5ff",
        ).pack(anchor="w")
        ttk.Label(
            tab,
            text=(
                "Each chapter is synthesized locally, timed from its actual WAV, "
                "mixed to a -16 LUFS AAC track, and exported with JSON and SRT. "
                "The renderer then muxes that track into the MP4. Nothing is "
                "sent to any online speech service on this route."
            ),
            wraplength=950,
            justify=LEFT,
        ).pack(anchor="w", pady=10)
        lesson_line = ttk.Frame(tab)
        lesson_line.pack(anchor="w", pady=(0, 4))
        ttk.Label(lesson_line, text="Lesson").pack(side=LEFT)
        self.dome_lesson = StringVar(value=DOME_LESSON_KEYS[0])
        self.dome_lesson_combo = ttk.Combobox(
            lesson_line,
            textvariable=self.dome_lesson,
            state="readonly",
            width=35,
            values=DOME_LESSON_LABELS,
        )
        self.dome_lesson_combo.set(DOME_LESSON_LABELS[0])
        self.dome_lesson_combo.pack(side=LEFT, padx=8)
        self.dome_lesson_note = StringVar(value="")
        ttk.Label(
            tab,
            textvariable=self.dome_lesson_note,
            foreground="#91aabd",
            wraplength=950,
            justify=LEFT,
        ).pack(anchor="w", pady=(0, 8))
        self.dome_lesson_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._refresh_dome_lesson()
        )
        self._refresh_dome_lesson()
        line = ttk.Frame(tab)
        line.pack(anchor="w", pady=8)
        ttk.Label(line, text="Voice profile").pack(side=LEFT)''',
)

sub(
    """        self.dome_status = StringVar(value="No local narration plan generated.")""",
    """        self.dome_status = StringVar(value="No local narration plan generated.")""",
)

sub(
    """    # ---- Rap production ------------------------------------------------""",
    '''    def _refresh_dome_lesson(self) -> None:
        """Keep the chapter-count note honest about the current selection."""
        key = self.dome_lesson_key()
        lesson = DOME_LESSONS[key]
        self.dome_lesson_note.set(
            f"{lesson.title}: {len(lesson.chapters)} chapters to synthesize. "
            "Longer lessons take proportionally longer on the first run; "
            "chapters are cached per profile afterwards."
        )

    def dome_lesson_key(self) -> str:
        label = self.dome_lesson_combo.get()
        if label in DOME_LABEL_TO_KEY:
            return DOME_LABEL_TO_KEY[label]
        return DOME_LESSON_KEYS[0]

    # ---- Rap production ------------------------------------------------''',
)

sub(
    """            self._start_job(
                build_dome_narration,
                project,
                profile,
                allow_model_download=allow_download,
                on_result=complete,
            )""",
    """            self._start_job(
                build_dome_narration,
                project,
                profile,
                lesson=self.dome_lesson_key(),
                allow_model_download=allow_download,
                on_result=complete,
            )""",
)

sub(
    "from .dome import build_dome_narration, export_dome_video",
    "from .dome import build_dome_narration, export_dome_video\n"
    "from two_v_demo.lesson_registry import LESSONS as DOME_LESSONS",
)

# Menu strings live next to the import so both the tab and the handler see them.
sub(
    "from two_v_demo.lesson_registry import LESSONS as DOME_LESSONS",
    "from two_v_demo.lesson_registry import LESSONS as DOME_LESSONS\n"
    "\n"
    "DOME_LESSON_KEYS = tuple(DOME_LESSONS)\n"
    "DOME_LESSON_LABELS = tuple(\n"
    "    f\"{lesson.title} ({len(lesson.chapters)} chapters)\"\n"
    "    for lesson in DOME_LESSONS.values()\n"
    ")\n"
    "DOME_LABEL_TO_KEY = dict(zip(DOME_LESSON_LABELS, DOME_LESSON_KEYS))",
)

p.write_text(s, encoding="utf-8")
print("local_voice_studio/gui.py: Lesson picker added")
