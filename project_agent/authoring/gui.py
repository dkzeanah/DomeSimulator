"""Manual authoring reference inside Project Agent. Copying never runs code."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .workbench import (
    DEFAULT_BRIEF, MANUAL_PATH, MODELS, ROOT, build_manual_prompt, commands,
    starter_source, validate_key,
)


class ManualAuthoringPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.key = tk.StringVar(value="my_element")
        self.model = tk.StringVar(value=MODELS[0])
        self.depth = tk.StringVar(value="Compact")
        self.status = tk.StringVar(value="Read the guide, describe a clip, then copy its prompt into your local model.")
        self.location = tk.StringVar()
        self.events = queue.Queue()
        self.busy = False
        self.closed = False
        self.packet = ""
        self._build()
        self.key.trace_add("write", self._update_local_views)
        self.model.trace_add("write", self._changed)
        self.depth.trace_add("write", self._changed)
        self._update_local_views()
        self.bind("<Destroy>", self._destroyed, add="+")
        self._poll_id = self.after(100, self._poll)

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)
        ttk.Label(self, text="Write a video element with your local model",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Copy context → paste into Ollama → save its Python → validate → inspect stills → export only that clip.",
                  wraplength=960).grid(row=1, column=0, sticky="w", pady=(2, 5))
        fields = ttk.Frame(self)
        fields.grid(row=2, column=0, sticky="ew")
        ttk.Label(fields, text="File key").pack(side="left")
        ttk.Entry(fields, textvariable=self.key, width=20).pack(side="left", padx=(6, 14))
        ttk.Label(fields, text="Your model").pack(side="left")
        ttk.Combobox(fields, textvariable=self.model, values=MODELS, width=25).pack(side="left", padx=6)
        ttk.Label(fields, text="Context").pack(side="left", padx=(8, 0))
        ttk.Combobox(fields, textvariable=self.depth, values=("Compact", "Full"),
                     state="readonly", width=10).pack(side="left", padx=6)
        brief_frame = ttk.LabelFrame(self, text="Describe the element you want (subject, movement, words, and duration)", padding=5)
        brief_frame.grid(row=3, column=0, sticky="ew", pady=5)
        self.brief = ScrolledText(brief_frame, height=3, width=50, wrap="word", font=("Segoe UI", 10), undo=True)
        self.brief.pack(fill="x")
        self.brief.insert("1.0", DEFAULT_BRIEF)
        self.brief.bind("<<Modified>>", self._brief_changed)
        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        self.build_buttons = []
        for title, action in (("Copy LLM prompt", "copy"), ("Preview prompt", "preview"),
                              ("Save prompt…", "save")):
            button = ttk.Button(buttons, text=title, command=lambda a=action: self.build(a))
            button.pack(side="left", padx=(0, 5))
            self.build_buttons.append(button)
        ttk.Button(buttons, text="Copy displayed page", command=self.copy_displayed).pack(side="left", padx=5)
        ttk.Button(buttons, text="Open code folder", command=self.open_folder).pack(side="left", padx=5)

        self.pages = ttk.Notebook(self)
        self.pages.grid(row=5, column=0, sticky="nsew")
        self.views = {}
        for name in ("Read me / full guide", "LLM prompt", "Starter example", "Commands"):
            frame = ttk.Frame(self.pages)
            self.pages.add(frame, text=name)
            view = ScrolledText(frame, wrap="word", width=60, height=10,
                                 font=("Consolas", 10), bg="#101923", fg="#e5eff8",
                                 insertbackground="white", selectbackground="#285c86")
            view.pack(fill="both", expand=True)
            self.views[name] = view
        self._set_text("Read me / full guide", MANUAL_PATH.read_text(encoding="utf-8"))
        self._set_text("LLM prompt", "Choose Compact or Full and click Preview prompt. Copy LLM prompt rebuilds it with your latest brief.")
        ttk.Label(self, textvariable=self.location, wraplength=950).grid(row=6, column=0, sticky="w", pady=(4, 0))
        ttk.Label(self, textvariable=self.status, wraplength=950).grid(row=7, column=0, sticky="w", pady=(4, 0))

    def _set_text(self, page, text):
        view = self.views[page]
        view.configure(state="normal")
        view.delete("1.0", "end")
        view.insert("1.0", text)
        view.configure(state="disabled")

    def _update_local_views(self, *_args):
        try:
            key = validate_key(self.key.get())
            self.location.set(f"Save the model's Python to: {ROOT / 'two_v_demo' / ('lesson_' + key + '.py')}")
            self._set_text("Starter example", starter_source(key))
            self._set_text("Commands", commands(key))
            self._changed()
        except ValueError as exc:
            self.location.set(str(exc))
            self._set_text("Commands", str(exc))
            self._set_text("Starter example", str(exc))

    def _changed(self, *_args):
        if self.model.get().split(":")[0].strip().lower() == "embeddinggemma":
            self.status.set("embeddinggemma produces embeddings, not Python. Choose a generation model; the guide explains the difference.")
        else:
            self.status.set("Copy / Preview rebuilds the prompt using the current key and brief. Nothing is sent to Ollama automatically.")

    def _brief_changed(self, _event=None):
        if self.brief.edit_modified():
            self.brief.edit_modified(False)
            self._changed()

    def build(self, action="preview"):
        if self.busy:
            return
        try:
            key = validate_key(self.key.get())
            brief = self.brief.get("1.0", "end-1c").strip()
            if not brief:
                raise ValueError("Describe the video element first.")
            if self.model.get().split(":")[0].strip().lower() == "embeddinggemma":
                raise ValueError("Choose a generation model. embeddinggemma cannot write a Python answer.")
        except ValueError as exc:
            self.status.set(str(exc))
            return
        full, model = self.depth.get() == "Full", self.model.get()
        self.busy = True
        for button in self.build_buttons:
            button.state(["disabled"])
        self.status.set("Building the packet from the current renderer APIs and examples…")

        def work():
            try:
                text = build_manual_prompt(key, brief, full=full, model=model)
                self.events.put(("done", (text, key, action)))
            except Exception as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def copy_displayed(self):
        index = self.pages.index(self.pages.select())
        name = tuple(self.views)[index]
        try:
            self._copy(self.views[name].get("1.0", "end-1c"))
            self.status.set(f"Copied: {name}")
        except tk.TclError as exc:
            self.status.set(f"Clipboard unavailable: {exc}")

    def open_folder(self):
        try:
            if os.name == "nt":
                os.startfile(str(ROOT / "two_v_demo"))
        except OSError as exc:
            self.status.set(str(exc))

    def _poll(self):
        if self.closed:
            return
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for button in self.build_buttons:
                button.state(["!disabled"])
            if kind == "error":
                self.status.set(f"Could not build prompt: {value}")
            else:
                self.packet, key, action = value
                self._set_text("LLM prompt", self.packet)
                self.pages.select(1)
                sizes = f"{len(self.packet):,} characters · {len(self.packet.split()):,} words · ~{len(self.packet) // 4:,} tokens (rough estimate)"
                try:
                    if action == "copy":
                        self._copy(self.packet)
                        self.status.set(f"Copied prompt for {key}. {sizes}. Paste into a fresh model chat.")
                    elif action == "save":
                        path = filedialog.asksaveasfilename(parent=self, initialfile=f"{key}-authoring-prompt.md",
                            defaultextension=".md", filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
                        if path:
                            with Path(path).open("x", encoding="utf-8") as handle:
                                handle.write(self.packet)
                            self.status.set(f"Saved prompt: {path}")
                        else:
                            self.status.set(f"Prompt ready. {sizes}")
                    else:
                        self.status.set(f"Prompt ready for {key}. {sizes}")
                except (OSError, tk.TclError) as exc:
                    self.status.set(str(exc))
                    messagebox.showerror("Authoring prompt", str(exc), parent=self)
        self._poll_id = self.after(100, self._poll)

    def _destroyed(self, event):
        if event.widget is self:
            self.closed = True
            self.after_cancel(self._poll_id)
