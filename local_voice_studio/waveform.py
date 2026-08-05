"""Waveform display, selection, playback, and light trim/delete editing.

This is a focused tool for curating short voice clips -- view a clip,
click-drag to select a stretch of it, hear the selection, cut it down --
not a general multitrack audio editor. Playback uses sounddevice (already
a core dependency via recorder.py) rather than winsound, because winsound
cannot report playback position or be stopped early, both needed for a
live cursor and for switching panels mid-playback.
"""

from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from .audio_tools import read_pcm16_mono, write_pcm16_mono


def downsample_envelope(samples: list[int], columns: int) -> list[tuple[float, float]]:
    """Min/max envelope of ``samples``, normalized to [-1, 1], one (min, max)
    pair per column -- enough to draw a waveform without plotting every
    sample. Returns [] for empty input."""
    total = len(samples)
    if total == 0 or columns <= 0:
        return []
    columns = max(1, min(columns, total))
    envelope: list[tuple[float, float]] = []
    for col in range(columns):
        start = total * col // columns
        end = max(start + 1, total * (col + 1) // columns)
        block = samples[start:end]
        envelope.append((min(block) / 32768.0, max(block) / 32768.0))
    return envelope


def trim_to_range(samples: list[int], start: int, end: int) -> list[int]:
    """Keep only ``samples[start:end]``, clamped to valid bounds."""
    start = max(0, min(start, len(samples)))
    end = max(start, min(end, len(samples)))
    return samples[start:end]


def delete_range(samples: list[int], start: int, end: int) -> list[int]:
    """Remove ``samples[start:end]`` and splice the rest together."""
    start = max(0, min(start, len(samples)))
    end = max(start, min(end, len(samples)))
    return samples[:start] + samples[end:]


def play_pcm(
    sample_rate: int,
    samples: list[int],
    *,
    on_position: Callable[[float], None] | None = None,
    on_done: Callable[[], None] | None = None,
    tk_root: tk.Misc | None = None,
) -> Callable[[], None]:
    """Start non-blocking playback of PCM16 mono ``samples``. Returns a
    ``stop()`` function. If ``tk_root`` is given, polls elapsed wall-clock
    time against the known duration to report a 0..1 position fraction
    roughly every 50ms -- approximate, not sample-accurate, which is fine
    for a review/comparison tool."""
    import numpy as np
    import sounddevice as sd

    if not samples or sample_rate <= 0:
        if on_done:
            on_done()
        return lambda: None

    array = np.array(samples, dtype=np.int16)
    sd.play(array, sample_rate)
    started_at = time.monotonic()
    duration = len(samples) / sample_rate
    state = {"stopped": False}

    def stop() -> None:
        if state["stopped"]:
            return
        state["stopped"] = True
        sd.stop()

    def tick() -> None:
        if state["stopped"]:
            return
        elapsed = time.monotonic() - started_at
        if elapsed >= duration:
            state["stopped"] = True
            if on_position:
                on_position(1.0)
            if on_done:
                on_done()
            return
        if on_position:
            on_position(elapsed / duration)
        if tk_root is not None:
            tk_root.after(50, tick)

    if tk_root is not None and (on_position or on_done):
        tk_root.after(50, tick)
    return stop


class WaveformCanvas(tk.Canvas):
    """Draws a min/max envelope of PCM16 mono samples. Click-drag selects a
    range (readable back as sample indices via ``.selection``); a plain
    click clears it. ``set_cursor_fraction`` draws a playback position line."""

    def __init__(self, parent, height: int = 100, **kw):
        kw.setdefault("bg", "#0c1620")
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, height=height, **kw)
        self.sample_rate = 24_000
        self.samples: list[int] = []
        self.on_selection_change: Callable[[], None] | None = None
        self._selection: tuple[int, int] | None = None
        self._drag_start_x: int | None = None
        self._cursor_fraction: float | None = None
        self._envelope_cache: list[tuple[float, float]] | None = None
        self._envelope_cache_width: int = -1
        self.bind("<Configure>", lambda _e: self.redraw())
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def load(self, sample_rate: int, samples: list[int]) -> None:
        self.sample_rate = sample_rate
        self.samples = samples
        self._selection = None
        self._envelope_cache = None
        self.redraw()

    @property
    def selection(self) -> tuple[int, int] | None:
        return self._selection

    def clear_selection(self) -> None:
        self._selection = None
        self.redraw()

    def set_cursor_fraction(self, fraction: float | None) -> None:
        self._cursor_fraction = fraction
        self.redraw()

    def _x_to_sample(self, x: int) -> int:
        width = max(1, self.winfo_width())
        fraction = max(0.0, min(1.0, x / width))
        return int(fraction * len(self.samples))

    def _on_press(self, event) -> None:
        if not self.samples:
            return
        self._drag_start_x = event.x
        index = self._x_to_sample(event.x)
        self._selection = (index, index)
        self.redraw()

    def _on_drag(self, event) -> None:
        if self._drag_start_x is None:
            return
        a = self._x_to_sample(self._drag_start_x)
        b = self._x_to_sample(event.x)
        self._selection = (min(a, b), max(a, b))
        self.redraw()

    def _on_release(self, _event) -> None:
        self._drag_start_x = None
        if self._selection is not None and self._selection[1] - self._selection[0] < 10:
            self._selection = None
        self.redraw()
        if self.on_selection_change:
            self.on_selection_change()

    def redraw(self) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        mid = height / 2.0
        if not self.samples:
            self.create_text(
                width / 2, mid, text="(no audio loaded)",
                fill="#5a7185", font=("Segoe UI", 9),
            )
            return
        if self._envelope_cache is None or self._envelope_cache_width != width:
            self._envelope_cache = downsample_envelope(self.samples, width)
            self._envelope_cache_width = width
        envelope = self._envelope_cache
        step = width / max(1, len(envelope))
        half = mid - 4
        for i, (lo, hi) in enumerate(envelope):
            x = i * step
            y1 = mid - hi * half
            y2 = mid - lo * half
            if y2 - y1 < 1:
                y2 = y1 + 1
            self.create_line(x, y1, x, y2, fill="#58d5ff")
        if self._selection is not None:
            total = len(self.samples)
            x1 = self._selection[0] / total * width
            x2 = self._selection[1] / total * width
            self.create_rectangle(
                x1, 0, x2, height, fill="#ffffff", stipple="gray25", outline="#f5b95d",
            )
        if self._cursor_fraction is not None:
            x = self._cursor_fraction * width
            self.create_line(x, 0, x, height, fill="#71e3a6", width=2)


class WaveformPanel(ttk.Frame):
    """A titled waveform view with Play/Stop, and -- when ``editable`` --
    Trim/Delete/Revert/Save controls. Edits happen against an in-memory
    working buffer (previewable and reversible) until Save is clicked,
    which calls ``on_save(sample_rate, samples)`` to actually persist."""

    def __init__(
        self,
        parent,
        title: str,
        root: tk.Misc,
        *,
        editable: bool = False,
        on_save: Callable[[int, list[int]], None] | None = None,
        save_label: str = "Save edited clip",
    ):
        super().__init__(parent)
        self._root = root
        self._editable = editable
        self._on_save = on_save
        self._disk_state: tuple[int, list[int]] | None = None
        self._working: tuple[int, list[int]] | None = None
        self._stop_playback: Callable[[], None] | None = None

        ttk.Label(self, text=title, font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.canvas = WaveformCanvas(self)
        self.canvas.pack(fill="x", pady=(2, 4))
        self.canvas.on_selection_change = self._update_button_state

        controls = ttk.Frame(self)
        controls.pack(fill="x")
        ttk.Button(controls, text="Play", command=self._play).pack(side="left")
        ttk.Button(controls, text="Stop", command=self._stop).pack(side="left", padx=4)
        self.status = tk.StringVar(value="No audio loaded.")
        ttk.Label(controls, textvariable=self.status, foreground="#91aabd").pack(
            side="left", padx=10
        )
        if editable:
            self.trim_button = ttk.Button(
                controls, text="Trim to selection", command=self._trim
            )
            self.trim_button.pack(side="left", padx=4)
            self.delete_button = ttk.Button(
                controls, text="Delete selection", command=self._delete
            )
            self.delete_button.pack(side="left", padx=4)
            ttk.Button(controls, text="Revert", command=self._revert).pack(
                side="left", padx=4
            )
            ttk.Button(controls, text=save_label, command=self._save).pack(
                side="left", padx=4
            )
        self._update_button_state()

    def load_file(self, path: Path) -> None:
        rate, samples = read_pcm16_mono(path)
        self.load_samples(rate, samples)

    def load_samples(self, rate: int, samples: list[int]) -> None:
        self._stop()
        self._disk_state = (rate, list(samples))
        self._working = (rate, list(samples))
        self.canvas.load(rate, list(samples))
        self._refresh_status()
        self._update_button_state()

    def clear(self) -> None:
        self._stop()
        self._disk_state = None
        self._working = None
        self.canvas.load(24_000, [])
        self.status.set("No audio loaded.")
        self._update_button_state()

    def save_to(self, path: Path) -> tuple[int, list[int]]:
        """Write the current working buffer to ``path`` directly (used by
        callers that manage persistence themselves, e.g. a fresh in-place
        recording being promoted into the dataset)."""
        if not self._working:
            raise ValueError("No audio loaded to save")
        rate, samples = self._working
        write_pcm16_mono(path, rate, samples)
        return rate, samples

    def _refresh_status(self) -> None:
        if not self._working:
            self.status.set("No audio loaded.")
            return
        rate, samples = self._working
        length_s = len(samples) / rate if rate else 0.0
        dirty = ""
        if self._editable and self._disk_state is not None and samples != self._disk_state[1]:
            dirty = "  (unsaved edit)"
        self.status.set(f"{length_s:.1f}s{dirty}")

    def _play(self) -> None:
        if not self._working or not self._working[1]:
            return
        self._stop()
        rate, samples = self._working
        selection = self.canvas.selection
        if selection is not None:
            samples = samples[selection[0]:selection[1]]
        self._stop_playback = play_pcm(
            rate,
            samples,
            on_position=self.canvas.set_cursor_fraction,
            on_done=lambda: self.canvas.set_cursor_fraction(None),
            tk_root=self._root,
        )

    def _stop(self) -> None:
        if self._stop_playback:
            self._stop_playback()
            self._stop_playback = None
        self.canvas.set_cursor_fraction(None)

    def _update_button_state(self) -> None:
        if not self._editable:
            return
        state = "normal" if self.canvas.selection is not None else "disabled"
        self.trim_button.configure(state=state)
        self.delete_button.configure(state=state)

    def _trim(self) -> None:
        if not self._working or self.canvas.selection is None:
            return
        start, end = self.canvas.selection
        rate, samples = self._working
        self._working = (rate, trim_to_range(samples, start, end))
        self.canvas.load(*self._working)
        self._refresh_status()
        self._update_button_state()

    def _delete(self) -> None:
        if not self._working or self.canvas.selection is None:
            return
        start, end = self.canvas.selection
        rate, samples = self._working
        self._working = (rate, delete_range(samples, start, end))
        self.canvas.load(*self._working)
        self._refresh_status()
        self._update_button_state()

    def _revert(self) -> None:
        if not self._disk_state:
            return
        self._working = (self._disk_state[0], list(self._disk_state[1]))
        self.canvas.load(*self._working)
        self._refresh_status()
        self._update_button_state()

    def _save(self) -> None:
        if not self._working or not self._on_save:
            return
        rate, samples = self._working
        self._on_save(rate, samples)
        self._disk_state = (rate, list(samples))
        self._refresh_status()
