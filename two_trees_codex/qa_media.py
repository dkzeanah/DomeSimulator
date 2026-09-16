"""Visual QA of only the Codex book window; does not edit the manuscript."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import os

from PIL import ImageGrab
from .app import attach_book_tab
from .storage import PACKAGE, stamp
from .scene_catalog import suggest_scenes


def main():
    if os.name=='nt':
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    output=PACKAGE/'qa'/stamp()
    output.mkdir(parents=True)
    root=tk.Tk()
    root.title('2 trees - Codex book media verification')
    root.geometry('1440x1000+30+30')
    tabs=ttk.Notebook(root)
    tabs.pack(fill='both',expand=True)
    desk=attach_book_tab(tabs)
    root.update()
    root.lift()
    root.attributes('-topmost',True)

    def capture(name):
        root.update()
        x,y=root.winfo_rootx(),root.winfo_rooty()
        ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(output/(name+'.png'))

    desk.select_page('codex-tree-ledger')
    desk.tabs.select(desk.media.reader)
    root.update()
    desk.media.refresh_reader()
    capture('live-reader')
    desk.tabs.select(desk.media.scenes)
    page=desk.page()
    if desk.media.catalog:
        matches=suggest_scenes(page['title']+'\n'+page['body'],desk.media.catalog,limit=12)
        desk.media.accept_result('match',{'catalog':desk.media.catalog,'matches':matches,'page_id':desk.current})
    capture('scene-matching')
    desk.tabs.select(desk.media.lexicon)
    desk.media.catalog_filter.set('wedge')
    rows=desk.media.catalog_list.get_children()
    if rows:
        desk.media.catalog_list.selection_set(rows[0])
        desk.media.show_catalog_entry()
    capture('visual-catalog')
    desk.tabs.select(desk.media.publish)
    root.update()
    if desk.media.publication:
        page=next((i for i,p in enumerate(desk.media.publication['pages']) if p['source_page_id']=='codex-tree-ledger'),0)
        desk.media.show_proof(page)
    capture('publication-proof')
    root.destroy()
    print(output)


if __name__=='__main__':
    main()
