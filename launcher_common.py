"""Shared infrastructure for the GUI launcher and the tools it drives.

Every standalone tool in this project used to be configured with CLI
flags (argparse or hand-rolled sys.argv parsing). That parsing has been
removed from the tools themselves; configuration now flows from the
launcher GUI as a one-shot JSON "launch ticket":

1. The launcher writes ``.launcher_configs/<tool>.json`` with whatever
   the user set in the GUI.
2. The launcher spawns the tool with **no command-line arguments**.
3. The tool calls :func:`consume_config` at startup, which reads that
   file and immediately deletes it, then dispatches on an ``action``
   key instead of ``sys.argv``.

Running a tool directly (``py -3.12 assembly_line.py``) without going
through the launcher finds no ticket, gets ``{}`` back, and falls
through to that tool's ordinary default behavior (the plain windowed
app) — so the scripts remain runnable on their own, they just no
longer parse flags to change what they do.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / ".launcher_configs"
PYTHON = sys.executable or "py"


def _ticket_path(tool: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in tool)
    return CONFIG_DIR / f"{safe}.json"


def write_config(tool: str, data: dict) -> Path:
    """Write a launch ticket for ``tool``. Called by the launcher GUI."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _ticket_path(tool)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def consume_config(tool: str) -> dict:
    """Read and delete ``tool``'s launch ticket. Called by the tool at
    startup. Returns ``{}`` if the tool was launched directly."""
    path = _ticket_path(tool)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    try:
        path.unlink()
    except OSError:
        pass
    return data if isinstance(data, dict) else {}


def peek_config(tool: str) -> dict:
    """Read without deleting — for tests/inspection only."""
    path = _ticket_path(tool)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def launch_tool(script: str, tool: str, config: dict,
                on_line=None, on_exit=None, cwd: Path | None = None):
    """Write ``config`` as ``tool``'s ticket, then spawn ``script`` with
    no arguments. If ``on_line`` is given, stdout/stderr are streamed to
    it line-by-line from a background thread (for the launcher's log
    pane); otherwise the process is fire-and-forget.

    Returns the Popen handle."""
    write_config(tool, config)
    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    process = subprocess.Popen(
        [PYTHON, script], cwd=str(cwd or ROOT), env=env,
        stdout=subprocess.PIPE if on_line else None,
        stderr=subprocess.STDOUT if on_line else None,
        text=True, bufsize=1)

    if on_line is None:
        return process

    def pump():
        try:
            for line in process.stdout:
                on_line(line.rstrip("\n"))
        finally:
            process.wait()
            if on_exit:
                on_exit(process.returncode)

    threading.Thread(target=pump, daemon=True).start()
    return process


def parse_size(value: str) -> tuple[int, int]:
    """Parse a 'WIDTHxHEIGHT' string; raises ValueError if malformed."""
    width_text, height_text = value.lower().split("x", 1)
    width, height = int(width_text), int(height_text)
    if width < 960 or height < 540:
        raise ValueError("minimum supported size is 960x540")
    return width, height


# ---------------------------------------------------------------------------
# Small reusable tkinter widgets (imported lazily by launcher.py so that
# tools which merely call consume_config() never need tkinter installed).
# ---------------------------------------------------------------------------

def build_widgets():
    import tkinter as tk
    from tkinter import filedialog, ttk

    PLACEHOLDER_COLOR = "#8a8a8a"

    class _PlaceholderMixin:
        """Grey example text shown while a field is empty. Clears on
        focus, comes back on blur if nothing was typed. get() always
        returns "" while the placeholder is showing — it is a hint,
        never a real value, so callers that do ``if field.get():`` are
        unaffected whether or not the user ever touches the field."""

        def _init_placeholder(self, entry, placeholder: str) -> None:
            self._placeholder_text = placeholder
            self._placeholder_entry = entry
            if placeholder:
                if not self.var.get():
                    self._show_placeholder()
                entry.bind("<FocusIn>", self._clear_placeholder)
                entry.bind("<FocusOut>", self._restore_placeholder)

        def _show_placeholder(self) -> None:
            self.var.set(self._placeholder_text)
            self._placeholder_entry.configure(foreground=PLACEHOLDER_COLOR)

        def _clear_placeholder(self, _event=None) -> None:
            if self.var.get() == self._placeholder_text:
                self.var.set("")
                self._placeholder_entry.configure(foreground="")

        def _restore_placeholder(self, _event=None) -> None:
            if not self.var.get() and self._placeholder_text:
                self._show_placeholder()

        def _raw_get(self) -> str:
            value = self.var.get()
            return "" if value == self._placeholder_text else value

    class LabeledEntry(ttk.Frame, _PlaceholderMixin):
        def __init__(self, parent, label, default="", width=32,
                    placeholder="", **kw):
            super().__init__(parent)
            ttk.Label(self, text=label, width=20, anchor="w").pack(
                side="left")
            self.var = tk.StringVar(value=default)
            entry = ttk.Entry(self, textvariable=self.var, width=width,
                              **kw)
            entry.pack(side="left", fill="x", expand=True)
            self._init_placeholder(entry, placeholder)

        def get(self):
            return self._raw_get()

        def set(self, value):
            self.var.set(value)
            self._placeholder_entry.configure(foreground="")

    class LabeledCombo(ttk.Frame):
        def __init__(self, parent, label, values, default=None):
            super().__init__(parent)
            ttk.Label(self, text=label, width=20, anchor="w").pack(
                side="left")
            self.var = tk.StringVar(value=default or (values[0] if values
                                                       else ""))
            ttk.Combobox(self, textvariable=self.var, values=values,
                        state="readonly", width=29).pack(
                side="left", fill="x", expand=True)

        def get(self):
            return self.var.get()

    class CheckRow(ttk.Frame):
        def __init__(self, parent, label, default=False):
            super().__init__(parent)
            self.var = tk.BooleanVar(value=default)
            ttk.Checkbutton(self, text=label, variable=self.var).pack(
                side="left")

        def get(self):
            return bool(self.var.get())

    class PathRow(ttk.Frame, _PlaceholderMixin):
        def __init__(self, parent, label, default="", mode="save",
                    filetypes=(("All files", "*.*"),), placeholder=""):
            super().__init__(parent)
            ttk.Label(self, text=label, width=20, anchor="w").pack(
                side="left")
            self.var = tk.StringVar(value=default)
            entry = ttk.Entry(self, textvariable=self.var, width=32)
            entry.pack(side="left", fill="x", expand=True)
            self._init_placeholder(entry, placeholder)

            def browse():
                if mode == "dir":
                    picked = filedialog.askdirectory()
                elif mode == "open":
                    picked = filedialog.askopenfilename(filetypes=filetypes)
                else:
                    picked = filedialog.asksaveasfilename(
                        filetypes=filetypes)
                if picked:
                    self.var.set(picked)
                    entry.configure(foreground="")
            ttk.Button(self, text="Browse…", command=browse).pack(
                side="left", padx=(6, 0))

        def get(self):
            return self._raw_get()

    return {
        "tk": tk, "ttk": ttk, "filedialog": filedialog,
        "LabeledEntry": LabeledEntry, "LabeledCombo": LabeledCombo,
        "CheckRow": CheckRow, "PathRow": PathRow,
    }
