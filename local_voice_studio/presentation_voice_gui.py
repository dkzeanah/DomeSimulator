"""Reusable Tk workbench embedded in both the launcher and Voice Studio."""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import wave

from .presentation_voice import (
    ClipPlayer, DEFAULT_LIBRARY, RenderCancelled, VoiceSettings, clean_transcript,
    export_copy, list_takes, new_take, render_clip, take_audio, write_json,
)
from .recorder import MicrophoneRecorder


class PresentationVoicePanel(ttk.Frame):
    def __init__(self, parent, *, library: Path = DEFAULT_LIBRARY, persist=True):
        super().__init__(parent, padding=8)
        self.persist = persist
        self.state_path = DEFAULT_LIBRARY / "workbench.json"
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.thread = None
        self.busy = False
        self.closed = False
        self.player = ClipPlayer()
        self.playing_path = None
        self.recorder = MicrophoneRecorder()
        self.recording = None
        self.record_started = 0.0
        self.takes = {}
        self.live = tk.BooleanVar(value=True)
        self.title_var = tk.StringVar(value="Custom narration")
        self.library_var = tk.StringVar(value=str(library))
        defaults = VoiceSettings()
        self.voice_vars = {key: tk.StringVar(value=value) for key, value in asdict(defaults).items()}
        self.status = tk.StringVar(value="Ready. Paste a transcript, then Generate & save.")
        self.play_status = tk.StringVar(value="No audio playing")
        self.counter = tk.StringVar(value="0 words")
        self.progress = tk.DoubleVar(value=0)
        self.position = tk.DoubleVar(value=0)
        self.volume = tk.DoubleVar(value=100)
        self.mic_var = tk.StringVar(value="System default")
        self.mic_devices = {"System default": None}
        self._draft_timer = None
        self._seeking = False
        self._build()
        self._load_draft()
        self.refresh()
        self.text.bind("<<Modified>>", self._text_changed)
        for var in [self.title_var, self.library_var, *self.voice_vars.values(), self.live]:
            var.trace_add("write", self._draft_changed)
        self.bind("<Destroy>", self._destroyed, add="+")
        self._tick_id = self.after(100, self._tick)

    def _button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=lambda: self._guard(command))
        button.pack(side="left", padx=(0, 4), pady=2)
        return button

    def _guard(self, command):
        try:
            command()
        except Exception as exc:
            self.status.set(str(exc))
            messagebox.showerror("Presentation Voice", str(exc), parent=self.winfo_toplevel())

    def _build(self):
        ttk.Label(self, text="Presentation Voice", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(self, text="The films' Andrew neural narrator • Online generation • "
                  "No voice profile needed • Every take saves WAV, MP3, and its script",
                  wraplength=940).pack(anchor="w", pady=(0, 6))
        settings = ttk.Frame(self)
        settings.pack(fill="x")
        for index, (name, var) in enumerate(self.voice_vars.items()):
            ttk.Label(settings, text={"voice": "Voice", "rate": "Rate (%)",
                "pitch": "Pitch (Hz)", "volume": "Voice volume (%)"}[name]).grid(
                    row=0, column=index, sticky="w", padx=(0, 8))
            ttk.Entry(settings, textvariable=var, width=34 if name == "voice" else 10).grid(
                row=1, column=index, sticky="ew", padx=(0, 8))
        settings.columnconfigure(0, weight=1)
        ttk.Button(settings, text="Film defaults", command=self.reset_voice).grid(row=1, column=4)

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, pady=(8, 4))
        editor, library = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(editor, weight=3)
        panes.add(library, weight=2)
        title_row = ttk.Frame(editor)
        title_row.pack(fill="x")
        ttk.Label(title_row, text="Clip name").pack(side="left")
        ttk.Entry(title_row, textvariable=self.title_var).pack(side="left", fill="x", expand=True, padx=5)
        tools = ttk.Frame(editor)
        tools.pack(fill="x")
        self._button(tools, "Open text", self.open_text)
        self._button(tools, "Save text", self.save_text)
        self._button(tools, "Clean timestamps", self.clean_text)
        ttk.Label(editor, text="Paste a transcript or type a statement (Ctrl+V). Select text to test just that part.",
                  wraplength=500).pack(anchor="w", pady=2)
        text_frame = ttk.Frame(editor)
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, height=7, width=38, wrap="word", undo=True,
                            font=("Segoe UI", 10), bg="#0c1620", fg="#eef6fc",
                            insertbackground="white", selectbackground="#285c86")
        scroll = ttk.Scrollbar(text_frame, command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        self.text.configure(yscrollcommand=scroll.set)
        ttk.Label(editor, textvariable=self.counter).pack(anchor="w")
        actions = ttk.Frame(editor)
        actions.pack(fill="x")
        self.generate_button = self._button(actions, "Generate & save", self.generate)
        self.selection_button = self._button(actions, "Test selection", lambda: self.generate(selection=True))
        self.cancel_button = self._button(actions, "Cancel", self.cancel_render)
        self.cancel_button.state(["disabled"])
        ttk.Checkbutton(editor, text="Listen while generating", variable=self.live).pack(anchor="w")

        ttk.Label(library, text="Saved takes", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tree_frame = ttk.Frame(library)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("name", "time", "kind"), show="headings",
                                 height=6, selectmode="browse")
        for name, label, width in (("name", "Clip", 165), ("time", "Length", 62),
                                    ("kind", "Type / status", 106)):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, minwidth=40, stretch=name == "name")
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.bind("<Double-1>", lambda _e: self._guard(self.play_selected))
        library_actions = ttk.Frame(library)
        library_actions.pack(fill="x")
        self._button(library_actions, "Refresh", self.refresh)
        self.load_button = self._button(library_actions, "Load script + settings", self.load_take)
        exports = ttk.Frame(library)
        exports.pack(fill="x")
        self._button(exports, "Save WAV as…", lambda: self.export("wav"))
        self._button(exports, "Save MP3 as…", lambda: self.export("mp3"))
        ttk.Label(library, text="Double-click a take to play. Completed clips remain available offline.",
                  wraplength=350).pack(anchor="w", pady=3)

        ttk.Progressbar(self, variable=self.progress, maximum=1).pack(fill="x", pady=2)
        ttk.Label(self, textvariable=self.status, wraplength=940).pack(anchor="w")
        playback = ttk.Frame(self)
        playback.pack(fill="x", pady=4)
        self.play_button = self._button(playback, "Play selected", self.play_selected)
        self.pause_button = self._button(playback, "Pause / resume", self.pause)
        self._button(playback, "Stop audio", self.stop_audio)
        ttk.Label(playback, textvariable=self.play_status).pack(side="left", padx=6)
        ttk.Label(playback, text="Listen volume").pack(side="left", padx=(6, 0))
        ttk.Scale(playback, from_=0, to=100, variable=self.volume, length=85).pack(side="left")
        self.seek = ttk.Scale(self, from_=0, to=1, variable=self.position)
        self.seek.pack(fill="x")
        self.seek.bind("<ButtonPress-1>", lambda _e: setattr(self, "_seeking", True))
        self.seek.bind("<ButtonRelease-1>", lambda _e: self._guard(self.seek_audio))

        microphone = ttk.Frame(self)
        microphone.pack(fill="x", pady=4)
        self.record_button = self._button(microphone, "Record mic", self.start_recording)
        self.record_stop = self._button(microphone, "Stop & save mic", self.stop_recording)
        self.record_stop.state(["disabled"])
        self.mic_combo = ttk.Combobox(microphone, textvariable=self.mic_var,
                                     values=["System default"], state="readonly", width=25)
        self.mic_combo.pack(side="left", fill="x", expand=True, padx=4)
        self._button(microphone, "Inputs", self.refresh_mics)
        self.meter = ttk.Progressbar(microphone, maximum=1, length=70)
        self.meter.pack(side="left")
        location = ttk.Frame(self)
        location.pack(fill="x")
        ttk.Label(location, text="Clip folder:").pack(side="left")
        ttk.Label(location, textvariable=self.library_var, width=45, anchor="w").pack(
            side="left", fill="x", expand=True, padx=5)
        self.folder_button = self._button(location, "Choose…", self.choose_library)
        self._button(location, "Open folder", self.open_folder)
        for container, flexible in ((editor, text_frame), (library, tree_frame)):
            items = container.winfo_children()
            for child in items:
                child.pack_forget()
            for row, child in enumerate(items):
                child.grid(row=row, column=0, sticky="nsew" if child is flexible else "ew")
                if child is flexible:
                    container.rowconfigure(row, weight=1)
            container.columnconfigure(0, weight=1)
        # Let the text/library area shrink first in the launcher's smaller
        # viewport. A vertical pack otherwise clips the transport and recorder.
        children = self.winfo_children()
        for child in children:
            child.pack_forget()
        for row, child in enumerate(children):
            child.grid(row=row, column=0, sticky="nsew" if child is panes else "ew",
                       pady=2)
            if child is panes:
                self.rowconfigure(row, weight=1)
        self.columnconfigure(0, weight=1)

    def settings(self):
        settings = VoiceSettings(**{key: var.get().strip() for key, var in self.voice_vars.items()})
        settings.validate()
        return settings

    def reset_voice(self):
        for key, value in asdict(VoiceSettings()).items():
            self.voice_vars[key].set(value)

    def _text_changed(self, _event=None):
        if self.text.edit_modified():
            value = self.text.get("1.0", "end-1c")
            self.counter.set(f"{len(value.split()):,} words · {len(value):,} characters")
            self.text.edit_modified(False)
            self._draft_changed()

    def _draft_changed(self, *_args):
        if not self.persist or self.closed:
            return
        if self._draft_timer:
            self.after_cancel(self._draft_timer)
        self._draft_timer = self.after(700, self._save_draft)

    def _save_draft(self):
        if self._draft_timer:
            self.after_cancel(self._draft_timer)
        self._draft_timer = None
        if not self.persist:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(self.state_path, {"title": self.title_var.get(),
                "text": self.text.get("1.0", "end-1c"), "library": self.library_var.get(),
                "settings": {k: v.get() for k, v in self.voice_vars.items()}, "live": self.live.get()})
        except (OSError, tk.TclError) as exc:
            self.status.set(f"Draft could not be saved: {exc}")

    def _load_draft(self):
        if not self.persist or not self.state_path.is_file():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.title_var.set(data.get("title", "Custom narration"))
            self.library_var.set(data.get("library", str(DEFAULT_LIBRARY)))
            self.text.insert("1.0", data.get("text", ""))
            self.live.set(data.get("live", True))
            for key, value in data.get("settings", {}).items():
                if key in self.voice_vars:
                    self.voice_vars[key].set(value)
        except (OSError, ValueError, AttributeError):
            pass

    def _set_busy(self, value):
        self.busy = value
        occupied = value or self.recording is not None
        for button in (self.generate_button, self.selection_button, self.folder_button,
                       self.play_button, self.record_button, self.load_button):
            button.state(["disabled" if occupied else "!disabled"])
        self.cancel_button.state(["!disabled" if value else "disabled"])
        self.record_stop.state(["!disabled" if self.recording else "disabled"])

    def generate(self, selection=False):
        if self.busy or self.recording:
            raise ValueError("Finish or cancel the current take first.")
        if selection:
            try:
                text = self.text.get("sel.first", "sel.last")
            except tk.TclError:
                raise ValueError("Select a passage in the text box to test.") from None
        else:
            text = self.text.get("1.0", "end-1c")
        if not text.strip():
            raise ValueError("Paste or type something to read first.")
        settings = self.settings()
        title = self.title_var.get() + (" — selection" if selection else "")
        library = Path(self.library_var.get()).expanduser().resolve()
        self.stop_audio()
        self.cancel = threading.Event()
        self._set_busy(True)
        self.progress.set(0)
        self.status.set("Connecting to the film's online neural voice…")
        self._listen = self.live.get()
        self._save_draft()

        def work():
            try:
                folder = render_clip(library, title, text, settings, self.cancel,
                                     lambda kind, value: self.events.put((kind, value)))
                self.events.put(("done", folder))
            except Exception as exc:
                self.events.put(("cancelled" if isinstance(exc, RenderCancelled) else "error", str(exc)))
        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()

    def cancel_render(self):
        self.cancel.set()
        self.stop_audio()
        self.status.set("Cancelling… script and completed sections will be kept.")

    def _selected(self):
        selection = self.tree.selection()
        if not selection or selection[0] not in self.takes:
            raise ValueError("Select a saved take first.")
        return self.takes[selection[0]]

    def refresh(self, select=None):
        old = self.tree.selection()
        chosen = str(select) if select else (old[0] if old else None)
        self.tree.delete(*self.tree.get_children())
        self.takes = {}
        for folder, receipt in list_takes(Path(self.library_var.get())):
            key = str(folder)
            self.takes[key] = (folder, receipt)
            duration = float(receipt.get("duration", 0))
            label = receipt.get("kind", "Neural") if receipt.get("status") == "complete" else receipt.get("status", "")
            self.tree.insert("", "end", iid=key, values=(receipt.get("title", folder.name),
                self._clock(duration) if duration else "—", label))
        if chosen in self.takes:
            self.tree.selection_set(chosen)
            self.tree.see(chosen)

    def play_selected(self):
        if self.busy or self.recording:
            raise ValueError("Finish or cancel the current take before switching playback.")
        folder, receipt = self._selected()
        path = take_audio(folder, receipt)
        self.stop_audio()
        self.player.play(path)
        self.playing_path = path
        self.seek.configure(to=max(1, self.player.total / self.player.rate))

    def pause(self):
        self.player.paused = not self.player.paused

    def stop_audio(self):
        self._listen = False
        self.player.stop()
        self.playing_path = None
        self.position.set(0)
        self.play_status.set("Audio stopped")

    def seek_audio(self):
        self._seeking = False
        if self.playing_path and not self.busy:
            position = self.position.get()
            self.player.seek(self.playing_path, position)

    def load_take(self):
        folder, receipt = self._selected()
        self._replace_text((folder / "script.txt").read_text(encoding="utf-8"))
        self.title_var.set(receipt.get("title", "Custom narration"))
        for key, value in receipt.get("settings", {}).items():
            if key in self.voice_vars:
                self.voice_vars[key].set(value)
        self.status.set("Loaded the take's script and voice settings.")

    def _replace_text(self, text):
        self.text.edit_separator()
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.edit_separator()

    def open_text(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("Transcript", "*.txt *.md *.srt *.vtt"), ("All files", "*.*")])
        if path:
            self._replace_text(Path(path).read_text(encoding="utf-8-sig"))
            self.title_var.set(Path(path).stem)

    def save_text(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if path:
            with Path(path).open("x", encoding="utf-8") as handle:
                handle.write(self.text.get("1.0", "end-1c"))
            self.status.set(f"Saved script: {path}")

    def clean_text(self):
        self._replace_text(clean_transcript(self.text.get("1.0", "end-1c")))
        self.status.set("Removed transcript timestamps. Review the text before generating; Ctrl+Z undoes.")

    def export(self, format):
        folder, receipt = self._selected()
        source = take_audio(folder, receipt, format)
        path = filedialog.asksaveasfilename(parent=self, initialfile=f"{folder.name}.{format}",
            defaultextension=f".{format}", filetypes=[(format.upper(), f"*.{format}")])
        if path:
            destination = Path(path)
            if destination.suffix.lower() != f".{format}":
                raise ValueError(f"Use a .{format} filename for this export.")
            export_copy(source, destination)
            self.status.set(f"Saved {format.upper()}: {path}")

    def choose_library(self):
        if self.busy or self.recording:
            return
        path = filedialog.askdirectory(parent=self, initialdir=self.library_var.get())
        if path:
            self.library_var.set(path)
            self.refresh()

    def open_folder(self):
        path = Path(self.library_var.get())
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))

    def refresh_mics(self):
        self.mic_devices = {"System default": None}
        self.mic_devices.update({f"{index}: {name}": index for index, name in self.recorder.devices()})
        self.mic_combo.configure(values=list(self.mic_devices))
        if self.mic_var.get() not in self.mic_devices:
            self.mic_var.set("System default")

    def start_recording(self):
        if self.busy or self.recording:
            return
        self.stop_audio()
        self.recorder.start(self.mic_devices.get(self.mic_var.get()))
        try:
            self.recording = new_take(Path(self.library_var.get()), self.title_var.get(),
                self.text.get("1.0", "end-1c"), VoiceSettings(), "Microphone")
        except Exception:
            self.recorder.abort()
            raise
        self.record_started = time.monotonic()
        self._set_busy(False)
        self.status.set("Recording microphone… Stop & save mic keeps this take as WAV.")

    def stop_recording(self):
        if not self.recording:
            return
        folder, receipt = self.recording
        try:
            path = self.recorder.stop(folder / "audio.wav")
            with wave.open(str(path), "rb") as wav:
                receipt.update(wav="audio.wav", status="complete",
                               duration=wav.getnframes() / wav.getframerate())
            self.status.set(f"Microphone take saved: {path}")
        except Exception as exc:
            self.recorder.abort()
            receipt.update(status="failed", error=str(exc))
            raise
        finally:
            write_json(folder / "take.json", receipt)
            self.recording = None
            self._set_busy(False)
            self.refresh(select=folder)
            self.meter["value"] = 0

    @staticmethod
    def _clock(seconds):
        value = max(0, int(seconds))
        return f"{value // 60}:{value % 60:02d}"

    def _tick(self):
        if self.closed:
            return
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self.progress.set(value[0])
                self.status.set(value[1])
            elif kind == "message":
                self.status.set(value)
            elif kind == "take":
                self.refresh(select=value)
            elif kind == "section" and self._listen and not self.cancel.is_set():
                try:
                    if self.player.stream is None:
                        self.player.start()
                    self.player.append(value)
                except Exception as exc:
                    self._listen = False
                    self.play_status.set(f"Playback unavailable: {exc}")
            elif kind in ("done", "cancelled", "error"):
                self.player.finished = True
                self._set_busy(False)
                self.refresh(select=value if kind == "done" else None)
                self.progress.set(1 if kind == "done" else 0)
                self.status.set(f"Saved WAV + MP3: {value}" if kind == "done" else value)
        self.player.volume = self.volume.get() / 100
        if self.player.stream is not None:
            if self.player.error:
                self.play_status.set(f"Playback error: {self.player.error}")
            else:
                state = "Paused" if self.player.paused else (
                    "Playing" if self.player.stream.active else "Finished")
                self.play_status.set(f"{state} {self._clock(self.player.seconds)} / "
                                     f"{self._clock(self.player.total / self.player.rate)}")
            if not self._seeking:
                self.position.set(self.player.seconds)
            self.seek.configure(to=max(1, self.player.total / self.player.rate))
        if self.recording:
            self.meter["value"] = self.recorder.peak
            self.recorder.peak = 0
            self.status.set(f"Recording microphone {self._clock(time.monotonic() - self.record_started)} — Stop & save mic when ready.")
        self._tick_id = self.after(100, self._tick)

    def _destroyed(self, event):
        if event.widget is self:
            self.close()

    def close(self):
        if self.closed:
            return
        self._save_draft()
        self.closed = True
        self.cancel.set()
        self.player.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.recording:
            # Preserve an in-progress microphone take on window close.
            folder, receipt = self.recording
            try:
                self.recorder.stop(folder / "audio.wav")
                with wave.open(str(folder / "audio.wav"), "rb") as wav:
                    receipt.update(wav="audio.wav", status="complete",
                                   duration=wav.getnframes() / wav.getframerate())
            except Exception as exc:
                receipt.update(status="failed", error=str(exc))
                self.recorder.abort()
            write_json(folder / "take.json", receipt)
            self.recording = None
        for timer in (self._tick_id, self._draft_timer):
            if timer:
                self.after_cancel(timer)
