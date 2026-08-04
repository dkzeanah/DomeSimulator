"""Native desktop GUI for a local, consented voice-model workflow."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import webbrowser
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    VERTICAL,
    BooleanVar,
    DoubleVar,
    IntVar,
    StringVar,
    Text,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
    ttk,
)

from .audio_tools import (
    build_voice_profile,
    create_clip_record,
    energy_segments,
    normalize_audio,
    read_pcm16_mono,
    write_pcm16_mono,
)
from .backends import (
    HardwareInfo,
    chatterbox_status,
    detect_hardware,
    export_f5_dataset,
    faster_whisper_status,
    launch_f5_finetune_gui,
    synthesize_chatterbox,
    transcribe_local,
)
from .dome import build_dome_narration, export_dome_video
from .jobs import Worker
from .models import ClipRecord, ConsentRecord, VoiceProfile
from .project import VoiceProject, safe_slug
from .prompts import RECORDING_PROMPTS
from .recorder import MicrophoneRecorder

try:
    import winsound
except ModuleNotFoundError:  # pragma: no cover - Windows has winsound
    winsound = None


class ConsoleWindow:
    """A separate window (not the in-notebook Logs tab) streaming live
    output from background jobs and launched subprocesses.

    Long-running local-AI work (loading a model, generating audio, a
    fine-tune server starting up) can go silent for a while between
    progress messages with nothing to show it hasn't frozen. This stays
    open and auto-raises whenever new work starts, and if a line looks
    like a local web address (e.g. an F5 fine-tune server's own
    "Running on http://127.0.0.1:7860" banner) it opens that address in
    the default browser automatically -- F5's fine-tune tool is a web
    app, not a desktop window, so nothing else would ever show you
    where to go."""

    _URL_PATTERN = re.compile(r"https?://127\.0\.0\.1:\d+\S*")

    def __init__(self, root: Tk):
        self.root = root
        self.window: Toplevel | None = None
        self.text: Text | None = None
        self._opened_urls: set[str] = set()

    def _ensure_window(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            return
        self.window = Toplevel(self.root)
        self.window.title("Local Voice Studio - Console")
        self.window.geometry("880x420")
        self.window.configure(bg="#08121c")
        ttk.Label(
            self.window,
            text=(
                "Live output from background jobs and launched tools. A "
                "local web address (like http://127.0.0.1:7860) opens in "
                "your browser automatically once it appears here."
            ),
            foreground="#91aabd",
            wraplength=860,
            background="#08121c",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        self.text = Text(
            self.window,
            bg="#08121c",
            fg="#b9d3e5",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )
        self.text.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))

    def show(self) -> None:
        def do() -> None:
            self._ensure_window()
            self.window.deiconify()
            self.window.lift()
        self.root.after(0, do)

    def write(self, line: str) -> None:
        def do() -> None:
            self._ensure_window()
            self.text.insert(END, line + "\n")
            self.text.see(END)
            match = self._URL_PATTERN.search(line)
            if match and match.group(0) not in self._opened_urls:
                url = match.group(0)
                self._opened_urls.add(url)
                self.text.insert(END, f"Opening {url} in your browser...\n")
                self.text.see(END)
                webbrowser.open(url)
        self.root.after(0, do)


class VoiceStudioApp:
    """A dependency-light GUI whose optional ML work runs in a worker thread."""

    def __init__(self, root: Tk, project_path: Path | None = None):
        self.root = root
        self.root.title("Local Voice Studio")
        self.root.geometry("1240x820")
        self.root.minsize(1040, 700)
        self.project: VoiceProject | None = None
        self.worker = Worker()
        self.on_job_result = None
        self.recorder = MicrophoneRecorder()
        self.recording = False
        self.prompt_index = 0
        self.last_audio: Path | None = None
        self.last_dome_plan: Path | None = None
        self.console = ConsoleWindow(self.root)
        self.f5_process: subprocess.Popen | None = None
        self._job_started_at: float | None = None
        self._job_last_heartbeat: float = 0.0

        self._configure_style()
        self._build_header()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=BOTH, expand=True, padx=12, pady=(0, 12))
        self._build_project_tab()
        self._build_record_tab()
        self._build_import_tab()
        self._build_dataset_tab()
        self._build_profile_tab()
        self._build_train_tab()
        self._build_synthesize_tab()
        self._build_dome_tab()
        self._build_logs_tab()
        self._update_prompt()
        self._refresh_hardware()
        self._refresh_microphones()
        self.root.after(120, self._poll_worker)
        self.root.after(120, self._meter_tick)
        self.root.after(1000, self._heartbeat_tick)
        if project_path:
            try:
                self.set_project(VoiceProject.open(project_path))
            except Exception as exc:
                messagebox.showerror("Open project", str(exc))

    def _configure_style(self) -> None:
        self.root.configure(bg="#101923")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background="#101923")
        style.configure("TLabel", background="#101923", foreground="#dce9f5")
        style.configure(
            "Title.TLabel",
            font=("Segoe UI Semibold", 18),
            foreground="#58d5ff",
        )
        style.configure(
            "Status.TLabel",
            font=("Segoe UI Semibold", 10),
            foreground="#71e3a6",
        )
        style.configure(
            "TButton",
            background="#20364b",
            foreground="#eef8ff",
            padding=(10, 6),
        )
        style.map("TButton", background=[("active", "#2b5875")])
        style.configure("TNotebook", background="#101923", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#172737",
            foreground="#a9c0d2",
            padding=(11, 7),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#254962")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview",
            background="#142331",
            fieldbackground="#142331",
            foreground="#e5eff8",
            rowheight=26,
        )
        style.configure(
            "Treeview.Heading",
            background="#254055",
            foreground="#ffffff",
        )

    def _build_header(self) -> None:
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=16, pady=12)
        ttk.Label(header, text="LOCAL VOICE STUDIO", style="Title.TLabel").pack(
            side=LEFT
        )
        self.project_status = StringVar(value="No project open")
        ttk.Label(
            header,
            textvariable=self.project_status,
            style="Status.TLabel",
        ).pack(side=RIGHT)
        ttk.Label(
            header,
            text="LOCAL ONLY  •  NO HOSTED INFERENCE API",
            foreground="#f5b95d",
        ).pack(side=RIGHT, padx=24)
        ttk.Button(
            header, text="Console", command=self.console.show
        ).pack(side=RIGHT)

    @staticmethod
    def _tab(notebook: ttk.Notebook, title: str) -> ttk.Frame:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text=title)
        return frame

    @staticmethod
    def _labeled_entry(parent, label: str, variable: StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable, width=52).grid(
            row=row, column=1, sticky="ew", padx=(12, 0), pady=5
        )

    def _build_project_tab(self) -> None:
        tab = self._tab(self.notebook, "Project")
        tab.columnconfigure(0, weight=1)

        guide = ttk.LabelFrame(tab, text="How this works", padding=14)
        guide.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            guide,
            text=(
                "Six steps, left to right across the tabs above: Project "
                "(this tab) -> Record or Import & Segment -> Dataset -> "
                "Voice Profile -> Synthesize -> Dome Narration. Fine-tune "
                "and Logs are optional and advanced -- most people never "
                "need them.\n\n"
                "Fastest path to hearing your own voice: (1) fill in the "
                "form below and click Create project. (2) Go to Record, "
                "use the built-in prompts, and record 10-15 short lines "
                "(or use Import & Segment with audio you already own). "
                "(3) Dataset tab: select each clip, type or locally "
                "transcribe its text, then click Accept. (4) Voice "
                "Profile tab: once you have ~15+ seconds of accepted "
                "clips, click Build profile. (5) Synthesize tab: pick "
                "that profile, type a sentence, click Generate locally.\n\n"
                "Steps 1-4 need nothing extra. Step 5, and Dome "
                "Narration, need the optional Chatterbox Turbo backend "
                "-- see 'Hardware and local backends' below for whether "
                "it is ready, and the exact fix if it is not. Full "
                "technical detail for any error is always in the Logs "
                "tab, even when the popup message is short."
            ),
            wraplength=980,
            justify=LEFT,
        ).pack(anchor="w")

        self.project_name = StringVar(value="My Voice")
        self.speaker_label = StringVar()
        form = ttk.LabelFrame(tab, text="Create a local project", padding=14)
        form.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        form.columnconfigure(1, weight=1)
        self._labeled_entry(form, "Project name", self.project_name, 0)
        self._labeled_entry(form, "Voice owner / speaker", self.speaker_label, 1)
        self.owner_ok = BooleanVar()
        self.auth_ok = BooleanVar()
        self.deception_ok = BooleanVar()
        statements = (
            (
                self.owner_ok,
                "I own this voice, or the named speaker explicitly authorized this model.",
            ),
            (
                self.auth_ok,
                "I am authorized to use these recordings for local voice modeling.",
            ),
            (
                self.deception_ok,
                "I will not use this voice to impersonate someone deceptively.",
            ),
        )
        for row, (variable, text) in enumerate(statements, 2):
            ttk.Checkbutton(form, text=text, variable=variable).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=4
            )
        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(
            buttons, text="Create project…", command=self.create_project
        ).pack(side=LEFT)
        ttk.Button(
            buttons, text="Open project…", command=self.open_project
        ).pack(side=LEFT, padx=8)

        status = ttk.LabelFrame(tab, text="Hardware and local backends", padding=14)
        status.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        tab.rowconfigure(2, weight=1)
        self.hardware_text = Text(
            status,
            height=14,
            bg="#142331",
            fg="#dce9f5",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )
        self.hardware_text.pack(fill=BOTH, expand=True)

    def _build_record_tab(self) -> None:
        tab = self._tab(self.notebook, "Record")
        tab.columnconfigure(0, weight=1)
        ttk.Label(
            tab,
            text="Record clean, natural teaching speech at 24 kHz mono PCM-16.",
            foreground="#91aabd",
        ).grid(row=0, column=0, sticky="w")
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=12)
        ttk.Label(controls, text="Microphone").pack(side=LEFT)
        self.microphone_choice = StringVar()
        self.microphone_combo = ttk.Combobox(
            controls,
            textvariable=self.microphone_choice,
            state="readonly",
            width=52,
        )
        self.microphone_combo.pack(side=LEFT, padx=8)
        ttk.Button(
            controls, text="Refresh", command=self._refresh_microphones
        ).pack(side=LEFT)
        self.meter_label = StringVar(value="Input: idle")
        ttk.Label(controls, textvariable=self.meter_label).pack(side=RIGHT)

        prompt_box = ttk.LabelFrame(tab, text="Prompt", padding=18)
        prompt_box.grid(row=2, column=0, sticky="nsew")
        tab.rowconfigure(2, weight=1)
        prompt_box.columnconfigure(0, weight=1)
        self.prompt_number = StringVar()
        ttk.Label(
            prompt_box,
            textvariable=self.prompt_number,
            foreground="#58d5ff",
        ).grid(row=0, column=0, sticky="w")
        self.prompt_text = StringVar()
        ttk.Label(
            prompt_box,
            textvariable=self.prompt_text,
            font=("Segoe UI Semibold", 17),
            wraplength=920,
            justify=LEFT,
        ).grid(row=1, column=0, sticky="nsew", pady=24)
        nav = ttk.Frame(prompt_box)
        nav.grid(row=2, column=0, sticky="ew")
        ttk.Button(nav, text="Previous", command=self.previous_prompt).pack(side=LEFT)
        ttk.Button(nav, text="Next", command=self.next_prompt).pack(side=LEFT, padx=8)
        self.record_button = ttk.Button(
            nav, text="Start recording", command=self.toggle_recording
        )
        self.record_button.pack(side=RIGHT)

    def _build_import_tab(self) -> None:
        tab = self._tab(self.notebook, "Import & Segment")
        ttk.Label(
            tab,
            text=(
                "Original files are copied into raw/. FFmpeg creates 24 kHz mono "
                "WAVs, then local energy segmentation creates 2–15 second clips."
            ),
            wraplength=940,
            justify=LEFT,
        ).pack(anchor="w")
        ttk.Button(
            tab, text="Import audio files…", command=self.import_audio
        ).pack(anchor="w", pady=16)
        self.import_status = StringVar(value="No import job running.")
        ttk.Label(tab, textvariable=self.import_status, foreground="#91aabd").pack(
            anchor="w"
        )

    def _build_dataset_tab(self) -> None:
        tab = self._tab(self.notebook, "Dataset")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        columns = ("status", "seconds", "rms", "clip", "silence", "issues", "text")
        self.clip_tree = ttk.Treeview(
            tab,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = (
            ("status", "Status", 80),
            ("seconds", "Seconds", 70),
            ("rms", "RMS dB", 70),
            ("clip", "Clipped %", 75),
            ("silence", "Silence %", 75),
            ("issues", "Quality", 160),
            ("text", "Transcript", 430),
        )
        for key, label, width in headings:
            self.clip_tree.heading(key, text=label)
            self.clip_tree.column(key, width=width, minwidth=55)
        self.clip_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            tab, orient=VERTICAL, command=self.clip_tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.clip_tree.configure(yscrollcommand=scrollbar.set)
        self.clip_tree.bind("<<TreeviewSelect>>", self._clip_selected)

        editor = ttk.LabelFrame(tab, text="Selected clip", padding=10)
        editor.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        editor.columnconfigure(0, weight=1)
        self.transcript_editor = Text(
            editor,
            height=4,
            bg="#142331",
            fg="#eef8ff",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )
        self.transcript_editor.grid(row=0, column=0, columnspan=6, sticky="ew")
        ttk.Button(
            editor, text="Save transcript", command=self.save_transcript
        ).grid(row=1, column=0, sticky="w", pady=(9, 0))
        ttk.Button(
            editor, text="Transcribe locally", command=self.transcribe_selected
        ).grid(row=1, column=1, sticky="w", padx=6, pady=(9, 0))
        ttk.Button(editor, text="Play", command=self.play_selected).grid(
            row=1, column=2, sticky="w", padx=6, pady=(9, 0)
        )
        ttk.Button(editor, text="Accept", command=self.accept_selected).grid(
            row=1, column=3, sticky="e", padx=6, pady=(9, 0)
        )
        ttk.Button(editor, text="Reject", command=self.reject_selected).grid(
            row=1, column=4, sticky="e", padx=6, pady=(9, 0)
        )

    def _build_profile_tab(self) -> None:
        tab = self._tab(self.notebook, "Voice Profile")
        tab.columnconfigure(0, weight=1)
        form = ttk.LabelFrame(tab, text="Build an immutable reference", padding=14)
        form.grid(row=0, column=0, sticky="ew")
        self.profile_name = StringVar(value="teacher")
        self.profile_seconds = DoubleVar(value=16.0)
        ttk.Label(form, text="Profile name").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.profile_name, width=32).grid(
            row=0, column=1, padx=10
        )
        ttk.Label(form, text="Target seconds").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(
            form,
            from_=8,
            to=30,
            increment=1,
            textvariable=self.profile_seconds,
            width=8,
        ).grid(row=0, column=3, padx=10)
        ttk.Button(form, text="Build profile", command=self.build_profile).grid(
            row=0, column=4, padx=10
        )
        ttk.Label(
            tab,
            text=(
                "Only accepted clips with clean metrics and transcripts are used. "
                "A profile is checksummed and locked as a reproducible identity asset."
            ),
            wraplength=950,
            foreground="#91aabd",
        ).grid(row=1, column=0, sticky="w", pady=12)
        self.profile_tree = ttk.Treeview(
            tab,
            columns=("name", "duration", "backend", "checksum"),
            show="headings",
            height=12,
        )
        for key, label, width in (
            ("name", "Profile", 250),
            ("duration", "Seconds", 90),
            ("backend", "Backend", 180),
            ("checksum", "SHA-256", 360),
        ):
            self.profile_tree.heading(key, text=label)
            self.profile_tree.column(key, width=width)
        self.profile_tree.grid(row=2, column=0, sticky="nsew")
        tab.rowconfigure(2, weight=1)

    def _build_train_tab(self) -> None:
        tab = self._tab(self.notebook, "Fine-tune")
        ttk.Label(
            tab,
            text="OPTIONAL ADAPTATION — NOT FOUNDATION-MODEL TRAINING",
            font=("Segoe UI Semibold", 14),
            foreground="#f5b95d",
        ).pack(anchor="w")
        ttk.Label(
            tab,
            text=(
                "Most people do not need this tab -- the Synthesize tab "
                "(Chatterbox Turbo) is the reliable first target. This is "
                "for advanced, optional adaptation of a pretrained model."
            ),
            wraplength=950,
            justify=LEFT,
        ).pack(anchor="w", pady=(4, 0))
        self.f5_hardware_note = StringVar()
        ttk.Label(
            tab,
            textvariable=self.f5_hardware_note,
            wraplength=950,
            justify=LEFT,
        ).pack(anchor="w", pady=12)
        self.f5_license_ok = BooleanVar()
        ttk.Checkbutton(
            tab,
            text="I reviewed the exact checkpoint license and accept this limitation.",
            variable=self.f5_license_ok,
        ).pack(anchor="w", pady=8)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor="w", pady=10)
        ttk.Button(
            buttons, text="Export F5 dataset", command=self.export_f5
        ).pack(side=LEFT)
        ttk.Button(
            buttons,
            text="Launch official F5 fine-tune GUI",
            command=self.launch_f5,
        ).pack(side=LEFT, padx=8)
        ttk.Label(
            tab,
            text=(
                "This starts the official F5-TTS tool as a local WEB APP, "
                "not a desktop window -- nothing pops up here. Its address "
                "(like http://127.0.0.1:7860) appears in the Console "
                "window (top-right button) and opens in your browser "
                "automatically once the server finishes starting, which "
                "can take a minute or more the first time. The launcher "
                "binds it to 127.0.0.1 (this computer only) and forces "
                "W&B offline. Training flags remain owned by the official "
                "upstream tool -- read its own on-screen instructions "
                "once the page opens.\n\n"
                "F5-TTS needs a separate environment from the rest of "
                "this app: its fine-tune tool does not start at all on "
                "gradio 6.x (upstream bug, still open), while Chatterbox "
                "needs gradio==6.8.0 exactly -- the two cannot share one "
                "environment. Run 'local_voice_studio/setup-f5-windows"
                ".ps1' once from the project folder (clones the official "
                "repo, creates .venv-f5, installs a working gradio "
                "version); this tab picks it up automatically after "
                "that, no matter which Python runs Local Voice Studio "
                "itself."
            ),
            wraplength=950,
            foreground="#91aabd",
            justify=LEFT,
        ).pack(anchor="w")

    def _build_synthesize_tab(self) -> None:
        tab = self._tab(self.notebook, "Synthesize")
        tab.columnconfigure(0, weight=1)
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Voice profile").pack(side=LEFT)
        self.synthesis_profile = StringVar()
        self.synthesis_combo = ttk.Combobox(
            top,
            textvariable=self.synthesis_profile,
            state="readonly",
            width=35,
        )
        self.synthesis_combo.pack(side=LEFT, padx=8)
        self.exaggeration = DoubleVar(value=0.45)
        self.cfg_weight = DoubleVar(value=0.5)
        ttk.Label(top, text="Expression").pack(side=LEFT, padx=(15, 3))
        ttk.Spinbox(
            top,
            from_=0.0,
            to=1.0,
            increment=0.05,
            textvariable=self.exaggeration,
            width=6,
        ).pack(side=LEFT)
        ttk.Label(top, text="Guidance").pack(side=LEFT, padx=(12, 3))
        ttk.Spinbox(
            top,
            from_=0.0,
            to=1.0,
            increment=0.05,
            textvariable=self.cfg_weight,
            width=6,
        ).pack(side=LEFT)
        self.download_ok = BooleanVar()
        ttk.Checkbutton(
            tab,
            text=(
                "Allow first-use download: Chatterbox Turbo (~350M parameters; "
                "approximately 2 GB), from Resemble AI/Hugging Face, MIT license. "
                "After caching, inference is local."
            ),
            variable=self.download_ok,
        ).grid(row=1, column=0, sticky="w", pady=10)
        self.synthesis_text = Text(
            tab,
            height=13,
            bg="#142331",
            fg="#eef8ff",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )
        self.synthesis_text.grid(row=2, column=0, sticky="nsew")
        self.synthesis_text.insert(
            "1.0",
            "Welcome. This is a fully local voice test for the geodesic dome lesson.",
        )
        tab.rowconfigure(2, weight=1)
        controls = ttk.Frame(tab)
        controls.grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Button(
            controls, text="Generate locally", command=self.synthesize
        ).pack(side=LEFT)
        ttk.Button(
            controls, text="Play last output", command=self.play_last
        ).pack(side=LEFT, padx=8)
        ttk.Label(
            controls,
            text="Needs Chatterbox Turbo -- see Project tab if this fails.",
            foreground="#91aabd",
        ).pack(side=LEFT, padx=8)
        ttk.Label(
            controls,
            text="Generated files include SYNTHETIC VOICE provenance sidecars.",
            foreground="#91aabd",
        ).pack(side=RIGHT)

    def _build_dome_tab(self) -> None:
        tab = self._tab(self.notebook, "Dome Narration")
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
        ttk.Label(line, text="Voice profile").pack(side=LEFT)
        self.dome_profile = StringVar()
        self.dome_combo = ttk.Combobox(
            line, textvariable=self.dome_profile, state="readonly", width=35
        )
        self.dome_combo.pack(side=LEFT, padx=8)
        self.dome_fps = IntVar(value=30)
        ttk.Label(line, text="FPS").pack(side=LEFT, padx=(16, 3))
        ttk.Spinbox(
            line, from_=1, to=60, textvariable=self.dome_fps, width=5
        ).pack(side=LEFT)
        buttons = ttk.Frame(tab)
        buttons.pack(anchor="w", pady=12)
        ttk.Button(
            buttons,
            text="1. Generate local narration plan",
            command=self.generate_dome_plan,
        ).pack(side=LEFT)
        ttk.Button(
            buttons,
            text="2. Render narrated MP4…",
            command=self.render_dome_video,
        ).pack(side=LEFT, padx=8)
        ttk.Label(
            buttons,
            text="Step 1 needs Chatterbox Turbo -- see Project tab if it fails.",
            foreground="#91aabd",
        ).pack(side=LEFT, padx=8)
        self.dome_status = StringVar(value="No local narration plan generated.")
        ttk.Label(
            tab,
            textvariable=self.dome_status,
            foreground="#91aabd",
            wraplength=950,
        ).pack(anchor="w", pady=8)

    def _build_logs_tab(self) -> None:
        tab = self._tab(self.notebook, "Logs")
        self.log_text = Text(
            tab,
            bg="#08121c",
            fg="#b9d3e5",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )
        self.log_text.pack(fill=BOTH, expand=True)
        self.log("Local Voice Studio ready. No audio or text is uploaded.")

    def log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{stamp}] {message}\n")
        self.log_text.see(END)

    def require_project(self) -> VoiceProject:
        if self.project is None:
            raise RuntimeError("Create or open a voice project first")
        return self.project

    def set_project(self, project: VoiceProject) -> None:
        self.project = project
        self.project_status.set(
            f"{project.manifest.name}  •  {project.root}  •  LOCAL ONLY"
        )
        self.project_name.set(project.manifest.name)
        self.speaker_label.set(project.manifest.speaker_label)
        consent = project.load_consent()
        if consent:
            self.owner_ok.set(consent.voice_owner_confirmed)
            self.auth_ok.set(consent.authorized_use_confirmed)
            self.deception_ok.set(consent.anti_deception_confirmed)
        self.refresh_all()
        self.log(f"Opened project: {project.root}")

    def create_project(self) -> None:
        try:
            name = self.project_name.get().strip()
            speaker = self.speaker_label.get().strip()
            if not name or not speaker:
                raise ValueError("Enter a project name and voice owner")
            consent = ConsentRecord(
                speaker_name=speaker,
                voice_owner_confirmed=self.owner_ok.get(),
                authorized_use_confirmed=self.auth_ok.get(),
                anti_deception_confirmed=self.deception_ok.get(),
            )
            if not consent.valid:
                raise ValueError("All three ownership statements are required")
            parent = filedialog.askdirectory(title="Choose a parent folder")
            if not parent:
                return
            root = Path(parent) / safe_slug(name)
            project = VoiceProject.create(root, name, speaker)
            project.save_consent(consent)
            self.set_project(project)
        except Exception as exc:
            messagebox.showerror("Create project", str(exc))

    def open_project(self) -> None:
        directory = filedialog.askdirectory(title="Open Local Voice Studio project")
        if not directory:
            return
        try:
            self.set_project(VoiceProject.open(Path(directory)))
        except Exception as exc:
            messagebox.showerror("Open project", str(exc))

    @staticmethod
    def _f5_hardware_note(hardware: HardwareInfo) -> str:
        if not hardware.gpu_name:
            fit = (
                "No NVIDIA GPU was detected, so F5 fine-tuning is not "
                "practical here -- CPU-only fine-tuning is extremely slow."
            )
        elif hardware.vram_mib < 8_000:
            fit = (
                f"Your {hardware.gpu_name} ({hardware.vram_mib} MiB VRAM) "
                "suits reference-profile inference (Synthesize tab). F5 "
                "fine-tuning is experimental at this memory level and may "
                "run out of memory."
            )
        elif hardware.vram_mib < 16_000:
            fit = (
                f"Your {hardware.gpu_name} ({hardware.vram_mib} MiB VRAM) "
                "can attempt F5 fine-tuning with small batch sizes; expect "
                "it to be slow."
            )
        else:
            fit = (
                f"Your {hardware.gpu_name} ({hardware.vram_mib} MiB VRAM) "
                "comfortably fits both inference and fine-tuning."
            )
        return (
            fit + " The official F5 code is MIT, but its official "
            "pretrained weights are CC-BY-NC; do not assume monetized use "
            "is allowed."
        )

    def _refresh_hardware(self) -> None:
        try:
            hardware = detect_hardware()
            chatterbox = chatterbox_status()
            whisper = faster_whisper_status()
            lines = [
                f"Python running this tool: {sys.executable}",
                f"GPU: {hardware.gpu_name or 'No NVIDIA GPU detected'}",
                f"VRAM: {hardware.vram_mib} MiB",
                f"Driver: {hardware.driver or 'n/a'}",
                f"PyTorch: {hardware.torch_version or 'not installed'}",
                f"CUDA runtime: {hardware.cuda_version or 'not available'}",
                f"Capability: {hardware.grade}",
                "",
                f"Chatterbox Turbo: {chatterbox.summary}",
                *(f"  {detail}" for detail in chatterbox.details),
                f"faster-whisper: {whisper.summary}",
                *(f"  {detail}" for detail in whisper.details),
                "",
                "Profile building and dataset curation do not need either ML backend.",
            ]
            if not chatterbox.ready or not whisper.ready:
                lines += [
                    "",
                    "Fix: from the project folder, run once, then reopen",
                    "Local Voice Studio (it uses that environment from then",
                    "on regardless of which Python started the launcher):",
                    "  local_voice_studio/setup-windows.ps1 -WithLocalAI",
                ]
            self.f5_hardware_note.set(self._f5_hardware_note(hardware))
        except Exception:
            lines = [traceback.format_exc()]
        self.hardware_text.delete("1.0", END)
        self.hardware_text.insert("1.0", "\n".join(lines))

    def _refresh_microphones(self) -> None:
        try:
            values = [f"{index}: {name}" for index, name in self.recorder.devices()]
        except Exception as exc:
            values = []
            self.log(str(exc))
        self.microphone_combo["values"] = values
        if values and not self.microphone_choice.get():
            self.microphone_choice.set(values[0])

    def _microphone_index(self) -> int | None:
        choice = self.microphone_choice.get()
        if not choice:
            return None
        try:
            return int(choice.split(":", 1)[0])
        except ValueError:
            return None

    def _update_prompt(self) -> None:
        self.prompt_number.set(
            f"Prompt {self.prompt_index + 1} of {len(RECORDING_PROMPTS)}"
        )
        self.prompt_text.set(RECORDING_PROMPTS[self.prompt_index])

    def previous_prompt(self) -> None:
        self.prompt_index = (self.prompt_index - 1) % len(RECORDING_PROMPTS)
        self._update_prompt()

    def next_prompt(self) -> None:
        self.prompt_index = (self.prompt_index + 1) % len(RECORDING_PROMPTS)
        self._update_prompt()

    def toggle_recording(self) -> None:
        try:
            project = self.require_project()
            if not project.consented:
                raise PermissionError("The project needs a valid ownership record")
            if not self.recording:
                self.recorder.start(self._microphone_index())
                self.recording = True
                self.record_button.configure(text="Stop and save")
                self.log("Recording started.")
                return
            stamp = time.strftime("%Y%m%d-%H%M%S")
            clip_id = f"mic-{stamp}-p{self.prompt_index + 1:02d}"
            raw_path = project.root / "raw" / f"{clip_id}.wav"
            clip_path = project.root / "clips" / f"{clip_id}.wav"
            self.recorder.stop(raw_path)
            shutil.copy2(raw_path, clip_path)
            clip = create_clip_record(
                project,
                clip_path,
                clip_id,
                RECORDING_PROMPTS[self.prompt_index],
                clip_id,
            )
            project.upsert_clip(clip)
            self.recording = False
            self.record_button.configure(text="Start recording")
            self.last_audio = clip_path
            self.log(f"Saved recording: {clip_path.name}")
            self.next_prompt()
            self.refresh_clips()
        except Exception as exc:
            if self.recording:
                self.recording = False
                self.record_button.configure(text="Start recording")
            messagebox.showerror("Recording", str(exc))

    def _meter_tick(self) -> None:
        if self.recording:
            peak = max(0.0, min(1.0, self.recorder.peak))
            warning = "  CLIPPING" if peak >= 0.99 else ""
            self.meter_label.set(f"Input peak: {peak * 100:5.1f}%{warning}")
        else:
            self.meter_label.set("Input: idle")
        self.root.after(120, self._meter_tick)

    def _start_job(self, function, *args, on_result=None, **kwargs) -> None:
        if self.worker.busy:
            messagebox.showinfo("Busy", "Wait for the current background job.")
            return
        self.on_job_result = on_result
        label = getattr(function, "__name__", str(function))
        self.log(f"Started: {label}")
        self.console.show()
        self.console.write(f"=== Started: {label} ===")
        self._job_started_at = time.time()
        self._job_last_heartbeat = 0.0
        try:
            self.worker.start(function, *args, **kwargs)
        except Exception as exc:
            self.on_job_result = None
            self._job_started_at = None
            messagebox.showerror("Background job", str(exc))

    def _heartbeat_tick(self) -> None:
        if self.worker.busy and self._job_started_at is not None:
            elapsed = time.time() - self._job_started_at
            if elapsed - self._job_last_heartbeat >= 15:
                self._job_last_heartbeat = elapsed
                self.console.write(f"... still working ({elapsed:.0f}s elapsed) ...")
        self.root.after(1000, self._heartbeat_tick)

    def _poll_worker(self) -> None:
        for event in self.worker.poll():
            if event.kind == "progress":
                self.log(str(event.value))
                self.console.write(str(event.value))
                self.import_status.set(str(event.value))
            elif event.kind == "result":
                callback = self.on_job_result
                self.on_job_result = None
                self._job_started_at = None
                self.log(f"Completed: {event.value}")
                self.console.write(f"=== Completed: {event.value} ===")
                if callback:
                    try:
                        callback(event.value)
                    except Exception as exc:
                        messagebox.showerror("Job result", str(exc))
            elif event.kind == "error":
                self.on_job_result = None
                self._job_started_at = None
                self.log(str(event.value))
                self.console.write(f"=== FAILED ===\n{event.value}")
                messagebox.showerror(
                    "Background job failed",
                    str(event.value).strip().splitlines()[-1],
                )
        self.root.after(120, self._poll_worker)

    @staticmethod
    def _import_files_job(
        project: VoiceProject,
        sources: tuple[str, ...],
        *,
        progress=print,
    ) -> int:
        created = 0
        for source_text in sources:
            source = Path(source_text)
            progress(f"Importing {source.name}...")
            source_id, raw = project.import_raw(source)
            normalized = project.root / "normalized" / f"{source_id}.wav"
            normalize_audio(raw, normalized)
            rate, samples = read_pcm16_mono(normalized)
            ranges = energy_segments(normalized)
            if not ranges:
                ranges = [(0, len(samples))]
            for index, (start, end) in enumerate(ranges, 1):
                clip_id = f"{source_id}-{index:03d}"
                clip_path = project.root / "clips" / f"{clip_id}.wav"
                write_pcm16_mono(clip_path, rate, samples[start:end])
                project.upsert_clip(
                    create_clip_record(
                        project,
                        clip_path,
                        clip_id,
                        source_id=source_id,
                    )
                )
                created += 1
            progress(f"Created {len(ranges)} clip(s) from {source.name}")
        return created

    def import_audio(self) -> None:
        try:
            project = self.require_project()
            if not project.consented:
                raise PermissionError("Accept the ownership statement first")
            paths = filedialog.askopenfilenames(
                title="Import audio you own",
                filetypes=[
                    ("Audio", "*.wav *.flac *.mp3 *.m4a *.aac *.ogg"),
                    ("All files", "*.*"),
                ],
            )
            if not paths:
                return
            self._start_job(
                self._import_files_job,
                project,
                tuple(paths),
                on_result=lambda _: self.refresh_clips(),
            )
        except Exception as exc:
            messagebox.showerror("Import", str(exc))

    def refresh_clips(self) -> None:
        for item in self.clip_tree.get_children():
            self.clip_tree.delete(item)
        if not self.project:
            return
        for clip in self.project.load_clips():
            self.clip_tree.insert(
                "",
                END,
                iid=clip.clip_id,
                values=(
                    clip.status,
                    f"{clip.duration_s:.1f}",
                    f"{clip.rms_dbfs:.1f}",
                    f"{clip.clipped_pct:.3f}",
                    f"{clip.silence_pct:.1f}",
                    ", ".join(clip.quality_issues) or "clean",
                    clip.text,
                ),
            )

    def _selected_clip(self) -> ClipRecord:
        project = self.require_project()
        selection = self.clip_tree.selection()
        if not selection:
            raise ValueError("Select a dataset clip")
        clip_id = selection[0]
        for clip in project.load_clips():
            if clip.clip_id == clip_id:
                return clip
        raise ValueError("Selected clip no longer exists")

    def _clip_selected(self, _event=None) -> None:
        try:
            clip = self._selected_clip()
        except Exception:
            return
        self.transcript_editor.delete("1.0", END)
        self.transcript_editor.insert("1.0", clip.text)

    def save_transcript(self) -> None:
        try:
            project = self.require_project()
            clip = self._selected_clip()
            clip.text = self.transcript_editor.get("1.0", END).strip()
            project.upsert_clip(clip)
            self.refresh_clips()
            self.clip_tree.selection_set(clip.clip_id)
        except Exception as exc:
            messagebox.showerror("Transcript", str(exc))

    def transcribe_selected(self) -> None:
        try:
            project = self.require_project()
            clip = self._selected_clip()
            path = project.resolve_relative(clip.audio_file)

            def apply_text(text: str) -> None:
                clip.text = text
                project.upsert_clip(clip)
                self.refresh_clips()
                self.clip_tree.selection_set(clip.clip_id)
                self._clip_selected()

            self._start_job(transcribe_local, path, on_result=apply_text)
        except Exception as exc:
            messagebox.showerror("Transcribe", str(exc))

    def play_path(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.lower() == ".wav" and winsound is not None:
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], shell=False)
        elif os.name == "nt":
            os.startfile(str(path))
        else:
            subprocess.Popen(["xdg-open", str(path)], shell=False)

    def play_selected(self) -> None:
        try:
            clip = self._selected_clip()
            self.play_path(self.require_project().resolve_relative(clip.audio_file))
        except Exception as exc:
            messagebox.showerror("Playback", str(exc))

    def _set_selected_status(self, status: str) -> None:
        project = self.require_project()
        clip = self._selected_clip()
        clip.text = self.transcript_editor.get("1.0", END).strip()
        if status == "accepted" and clip.quality_issues:
            if not messagebox.askyesno(
                "Quality warning",
                "This clip has: "
                + ", ".join(clip.quality_issues)
                + ". Mark it accepted anyway?",
            ):
                return
        clip.status = status
        clip.rejection_reason = "manual review" if status == "rejected" else ""
        project.upsert_clip(clip)
        self.refresh_clips()
        self.refresh_profiles()

    def accept_selected(self) -> None:
        try:
            self._set_selected_status("accepted")
        except Exception as exc:
            messagebox.showerror("Accept clip", str(exc))

    def reject_selected(self) -> None:
        try:
            self._set_selected_status("rejected")
        except Exception as exc:
            messagebox.showerror("Reject clip", str(exc))

    def build_profile(self) -> None:
        try:
            project = self.require_project()
            profile_name = self.profile_name.get().strip()
            target_seconds = self.profile_seconds.get()

            def job(*, progress=print):
                progress("Ranking accepted clips and assembling reference WAV...")
                return build_voice_profile(
                    project,
                    profile_name,
                    project.load_clips(),
                    target_seconds,
                )

            self._start_job(
                job,
                on_result=lambda _: self.refresh_profiles(),
            )
        except Exception as exc:
            messagebox.showerror("Build profile", str(exc))

    def refresh_profiles(self) -> None:
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        profiles = self.project.profiles() if self.project else []
        values = []
        for profile in profiles:
            values.append(profile.profile_id)
            self.profile_tree.insert(
                "",
                END,
                iid=profile.profile_id,
                values=(
                    profile.name,
                    f"{profile.duration_s:.1f}",
                    profile.backend_hint,
                    profile.sha256,
                ),
            )
        for combo in (self.synthesis_combo, self.dome_combo):
            combo["values"] = values
        if values:
            if self.synthesis_profile.get() not in values:
                self.synthesis_profile.set(values[-1])
            if self.dome_profile.get() not in values:
                self.dome_profile.set(values[-1])

    def selected_profile(self, profile_id: str) -> VoiceProfile:
        project = self.require_project()
        for profile in project.profiles():
            if profile.profile_id == profile_id:
                return profile
        raise ValueError("Select a voice profile")

    def export_f5(self) -> None:
        try:
            if not self.f5_license_ok.get():
                raise PermissionError("Review and accept the F5 license notice first")
            project = self.require_project()
            destination = filedialog.askdirectory(
                title="Choose F5 dataset export folder"
            )
            if not destination:
                return
            path = export_f5_dataset(project, Path(destination))
            self.log(f"Exported F5 metadata: {path}")
            messagebox.showinfo("F5 export", f"Saved:\n{path}")
        except Exception as exc:
            messagebox.showerror("F5 export", str(exc))

    def launch_f5(self) -> None:
        try:
            if not self.f5_license_ok.get():
                raise PermissionError("Review and accept the F5 license notice first")
            if self.f5_process is not None and self.f5_process.poll() is None:
                self.console.show()
                messagebox.showinfo(
                    "F5 fine-tune",
                    f"Already running (PID {self.f5_process.pid}). Check "
                    "the console window -- its web address opens in your "
                    "browser automatically once the server is ready.",
                )
                return
            self.console.show()
            self.console.write("=== Starting official F5 fine-tune GUI ===")
            self.f5_process = launch_f5_finetune_gui(
                self.require_project(), on_line=self.console.write
            )
            self.log(f"Started official F5 fine-tune GUI (PID {self.f5_process.pid})")
            self.console.write(
                f"PID {self.f5_process.pid}. This is a web app, not a "
                "desktop window -- its address will appear below and open "
                "automatically in your browser once it's ready (can take "
                "a while on first run)."
            )
        except Exception as exc:
            messagebox.showerror("F5 fine-tune", str(exc))

    def synthesize(self) -> None:
        try:
            project = self.require_project()
            profile = self.selected_profile(self.synthesis_profile.get())
            text = self.synthesis_text.get("1.0", END).strip()
            allow_download = self.download_ok.get()
            stamp = time.strftime("%Y%m%d-%H%M%S")
            output = project.root / "outputs" / "audio" / f"speech-{stamp}.wav"

            def complete(path: Path) -> None:
                self.last_audio = Path(path)
                messagebox.showinfo("Local synthesis", f"Saved:\n{path}")

            self._start_job(
                synthesize_chatterbox,
                project,
                profile,
                text,
                output,
                exaggeration=self.exaggeration.get(),
                cfg_weight=self.cfg_weight.get(),
                allow_model_download=allow_download,
                on_result=complete,
            )
        except Exception as exc:
            messagebox.showerror("Local synthesis", str(exc))

    def play_last(self) -> None:
        try:
            if not self.last_audio:
                raise ValueError("No audio has been generated or recorded yet")
            self.play_path(self.last_audio)
        except Exception as exc:
            messagebox.showerror("Playback", str(exc))

    def generate_dome_plan(self) -> None:
        try:
            project = self.require_project()
            profile = self.selected_profile(self.dome_profile.get())
            allow_download = self.download_ok.get()

            def complete(path: Path) -> None:
                self.last_dome_plan = Path(path)
                self.dome_status.set(f"Ready: {path}")
                messagebox.showinfo("Dome narration", f"Saved plan:\n{path}")

            self._start_job(
                build_dome_narration,
                project,
                profile,
                allow_model_download=allow_download,
                on_result=complete,
            )
        except Exception as exc:
            messagebox.showerror("Dome narration", str(exc))

    def render_dome_video(self) -> None:
        try:
            if not self.last_dome_plan or not self.last_dome_plan.is_file():
                raise ValueError("Generate the local narration plan first")
            destination = filedialog.asksaveasfilename(
                title="Save narrated dome video",
                defaultextension=".mp4",
                filetypes=[("MP4 video", "*.mp4")],
            )
            if not destination:
                return
            self._start_job(
                export_dome_video,
                self.last_dome_plan,
                Path(destination),
                fps=self.dome_fps.get(),
                on_result=lambda path: messagebox.showinfo(
                    "Dome video", f"Saved:\n{path}"
                ),
            )
        except Exception as exc:
            messagebox.showerror("Dome video", str(exc))

    def refresh_all(self) -> None:
        self.refresh_clips()
        self.refresh_profiles()
        self._refresh_hardware()


def launch(project_path: Path | None = None) -> None:
    root = Tk()
    VoiceStudioApp(root, project_path)
    root.mainloop()
