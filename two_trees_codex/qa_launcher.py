"""Exercise the full current launcher adapter and capture only its own test window."""
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from PIL import ImageGrab

import launcher_two_trees_codex
from .app import BookDesk
from .storage import PACKAGE, stamp


def main():
    output = PACKAGE / "qa" / stamp()
    output.mkdir(parents=True)
    def inspect(root, *_args, **_kwargs):
        root.update()
        root.lift()
        root.attributes('-topmost', True)
        root.update()
        notebooks = [w for w in root.winfo_children() if isinstance(w, ttk.Notebook)]
        assert len(notebooks) == 1
        notebook = notebooks[0]
        desk = next(w for w in notebook.winfo_children() if isinstance(w, BookDesk))
        assert notebook.tabs()[-1] == str(desk)
        assert notebook.select() == str(desk)
        desk.select_page('codex-joint-geometry')
        root.update()
        print('Full launcher tab count:', len(notebook.tabs()))
        print('Final tab:', notebook.tab(desk, 'text'))
        print('Page count:', len(desk.store.book['pages']))
        def capture(name):
            root.update()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            ImageGrab.grab(bbox=(x, y, x+root.winfo_width(), y+root.winfo_height())).save(output / (name+'.png'))
        capture('writing-desk')
        desk.tabs.select(next(t for t in desk.tabs.tabs() if desk.tabs.tab(t,'text') == 'Images'))
        desk.refresh_images()
        attached = desk.page()['figures']
        index = desk.asset_keys.index(attached[0])
        desk.image_list.selection_set(index)
        desk.show_image()
        capture('image-desk')
        desk.tabs.select(next(t for t in desk.tabs.tabs() if desk.tabs.tab(t,'text') == 'Sizing lab'))
        capture('sizing-lab')
        desk.save()
        root.destroy()
        print('QA screenshots:', output)
    original = tk.Tk.mainloop
    tk.Tk.mainloop = inspect
    try:
        launcher_two_trees_codex.main()
    finally:
        tk.Tk.mainloop = original


if __name__ == '__main__':
    main()
