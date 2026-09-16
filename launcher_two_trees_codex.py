"""Run the existing launcher with an additional final book tab.

This adapter leaves launcher.py and Claude's book work untouched. For a later
merge, call two_trees_codex.app.attach_book_tab(notebook) in launcher.main.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import os

import launcher
from two_trees_codex.app import attach_book_tab


def main():
    if os.name == "nt":
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    original = tk.Tk.mainloop

    def with_book(root, *args, **kwargs):
        # The original launcher has finished building all of its own tabs.
        notebook = next((w for w in root.winfo_children()
                         if isinstance(w, ttk.Notebook)), None)
        if notebook is None:
            raise RuntimeError("Launcher notebook not found; use python -m two_trees_codex.app")
        desk = attach_book_tab(notebook)
        notebook.select(desk)
        width, height = min(1440, root.winfo_screenwidth()-80), min(1000, root.winfo_screenheight()-100)
        root.geometry(f"{width}x{height}+30+30")
        root.minsize(1020, 740)
        # Keep the final tab reachable even when all current tools do not fit
        # across one native Tk tab bar (there is no native horizontal scrolling).
        selector = ttk.Frame(root)
        selector.pack(before=notebook, fill="x", padx=12, pady=(0, 6))
        ttk.Label(selector, text="Tool / workspace:").pack(side="left", padx=(0, 8))
        labels = [notebook.tab(tab_id, 'text') for tab_id in notebook.tabs()]
        selected = tk.StringVar(value=labels[-1])
        chooser = ttk.Combobox(selector, values=labels, textvariable=selected, state="readonly", width=34)
        chooser.pack(side="left")
        chooser.bind('<<ComboboxSelected>>', lambda e: notebook.select(notebook.tabs()[chooser.current()]))
        notebook.bind('<<NotebookTabChanged>>', lambda e: selected.set(notebook.tab(notebook.select(), 'text')), add=True)
        style = ttk.Style(root)
        style.configure('Parallel.TNotebook.Tab', font=('Segoe UI', 9), padding=(5, 4))
        notebook.configure(style='Parallel.TNotebook')
        root.title("DomeSim Launcher | 2 trees — Codex parallel edition")
        # Restore before entering the event loop; future windows are ordinary Tk.
        tk.Tk.mainloop = original
        return original(root, *args, **kwargs)

    tk.Tk.mainloop = with_book
    try:
        return launcher.main()
    finally:
        tk.Tk.mainloop = original


if __name__ == "__main__":
    raise SystemExit(main())
