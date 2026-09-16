"""Tk book authoring desk, embedded as the launcher's final tab or standalone."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser

from .storage import BookStore, new_page, words, DEFAULT_HOME

KINDS = ("chapter", "part", "front", "worked", "plate", "journal", "appendix", "worksheet")
STRANDS = ("story", "explanation", "how-to", "reference")
STATUSES = ("draft", "revising", "field record needed", "fact check", "ready")


class BookDesk(ttk.Frame):
    def __init__(self, parent, home=DEFAULT_HOME):
        super().__init__(parent, padding=10)
        self.store = BookStore(home)
        self.current = None
        self.loading = False
        self.dirty = False
        self.autosave_job = None
        self.jobs = queue.Queue()
        self.photos = []
        self.asset_keys = []
        self.pending = False
        self._build()
        from .media_desk import BookMediaDesk
        self.media = BookMediaDesk(self)
        self.refresh_outline()
        self.select_page(self.store.book["pages"][0]["id"])
        self.after(150, self.poll_jobs)
        self.bind("<Destroy>", self._destroyed, add=True)

    def _build(self):
        style = ttk.Style(self)
        style.configure("BookTitle.TLabel", foreground="#214b3b", font=("Georgia", 22, "bold"))
        style.configure("BookMeta.TLabel", foreground="#5b675e", font=("Segoe UI", 9))
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="2 trees", style="BookTitle.TLabel").pack(side="left")
        ttk.Label(top, text="  Build your (D)Home   /   The writing desk", font=("Segoe UI", 11)).pack(side="left", padx=12)
        self.total = ttk.Label(top, style="BookMeta.TLabel")
        self.total.pack(side="right")
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(8, 10))
        for title, command in [("Save", self.save), ("Read book", lambda: self.tabs.select(self.media.reader)),
                               ("HTML copy", self.read_book),
                               ("Export Markdown", lambda: self.export("md")),
                               ("Export merge bundle", lambda: self.export("json")),
                               ("Import pages", self.import_pages),
                               ("Open book folder", lambda: self.open_path(self.store.home))]:
            ttk.Button(bar, text=title, command=command).pack(side="left", padx=(0, 5))
        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main, width=290)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=4)
        self.after_idle(lambda: main.sashpos(0, 315))
        ttk.Label(left, text="MANUSCRIPT ORDER", style="BookMeta.TLabel").pack(anchor="w")
        self.search = tk.StringVar()
        entry = ttk.Entry(left, textvariable=self.search)
        entry.pack(fill="x", pady=5)
        self.search.trace_add("write", lambda *_: self.refresh_outline())
        listing = ttk.Frame(left)
        listing.pack(fill="both", expand=True)
        self.outline = ttk.Treeview(listing, show="tree", selectmode="browse")
        self.outline.column("#0", width=300, minwidth=180)
        self.outline.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(listing, command=self.outline.yview)
        scroll.pack(side="right", fill="y")
        self.outline.configure(yscrollcommand=scroll.set)
        self.outline.tag_configure("part", foreground="#20704e", font=("Segoe UI", 10, "bold"))
        self.outline.bind("<<TreeviewSelect>>", self.on_select)
        order = ttk.Frame(left)
        order.pack(fill="x", pady=5)
        for label, cmd in [("+ Page", self.add_page), ("Copy", self.duplicate),
                           ("↑", lambda: self.move(-1)), ("↓", lambda: self.move(1))]:
            ttk.Button(order, text=label, width=7, command=cmd).pack(side="left", padx=2)
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True, padx=(10, 0))
        write = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(write, text="Write")
        self.title_var = tk.StringVar()
        ttk.Entry(write, textvariable=self.title_var, font=("Georgia", 15)).pack(fill="x", pady=(0, 7))
        metadata = ttk.Frame(write)
        metadata.pack(fill="x")
        self.kind, self.strand, self.status = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for label, var, options in [("Page", self.kind, KINDS), ("Strand", self.strand, STRANDS), ("Status", self.status, STATUSES)]:
            ttk.Label(metadata, text=label).pack(side="left", padx=(0, 4))
            ttk.Combobox(metadata, textvariable=var, values=options, state="readonly", width=17).pack(side="left", padx=(0, 10))
        ttk.Label(write, text="Write in Markdown. Each selection is a chapter, section opener, plate, or field-record page.", style="BookMeta.TLabel").pack(anchor="w", pady=6)
        self.editor = self.text_area(write, "Georgia", 12)
        self.editor.bind("<<Modified>>", self.edited)
        self.editor.bind("<Control-s>", lambda e: (self.save(), "break")[1])
        self.editor.bind("<Control-z>", lambda e: self.undo())
        self.page_count = ttk.Label(write, style="BookMeta.TLabel")
        self.page_count.pack(anchor="w", pady=(5, 0))
        notes = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(notes, text="Notes & sources")
        ttk.Label(notes, text="Private editorial notes, interviews, evidence to collect, and source checks. These stay out of the reading edition.", wraplength=670).pack(anchor="w", pady=(0, 8))
        self.notes = self.text_area(notes, "Segoe UI", 11)
        self.notes.bind("<<Modified>>", self.edited)
        images = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(images, text="Images")
        self.build_images(images)
        calc = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(calc, text="Sizing lab")
        self.build_calculator(calc)
        help_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(help_tab, text="Book plan")
        help_text = self.text_area(help_tab, "Segoe UI", 11)
        help_text.insert("1.0", "THE BOOK HAS THREE READING STRANDS\n\nStory: the earlier Frankendome, the wedge discovery, and the actual fortnight as you record it.\n\nExplanation: geodesic geometry, radial wood, physical joints, yield, and honest comparisons.\n\nHow-to: the two sizing routes, inventory, repeatable frames, assembly records, and next steps toward a home.\n\nWORKING WITH THE DESK\n\nSelect any page on the left. Edit its title, type, strand and status. Writing autosaves after a short pause; Save and Ctrl+S also save immediately. Use + Page for a new chapter, divider, journal entry, or plate. Arrow buttons move the selected page one position. Search includes titles and prose.\n\nUse Images to attach illustrations and edit captions. Sizing lab computes from DomeSim's geometry and can insert a dated calculation page. Read book opens the live illustrated manuscript. Scenes matches chapter language to existing video scenes and captures a chosen moment. Catalog browses nouns, definitions and visual concepts. Publish builds a real PDF with a table of contents and matching page proofs, then exports those exact pages as a silent MP4 readthrough. Reading pace and minimum page time are adjustable. HTML copy remains available for browser reading and printing.\n\nMERGING LATER\n\nThis edition lives entirely in two_trees_codex/. Export merge bundle carries every page, editorial note, status, and image in one JSON file. Import pages accepts that bundle or a Markdown/text draft; imported pages are appended with new IDs and can be reordered. It never replaces an existing chapter.\n\nEvery save preserves a dated JSON snapshot in history/. Import a snapshot with no images directly; for an illustrated project use a portable bundle. A competing editor triggers a conflict instead of overwriting its work.\n\nDRAFT STATUS\n\nThe first-person passages are proposed prose based on the project notes. Future events are written as intentions. Field-record pages await your actual dates, photographs, measurements and observations. A ready label is your editorial decision; the software does not certify construction details.")
        help_text.configure(state="disabled")
        for var in (self.title_var, self.kind, self.strand, self.status):
            var.trace_add("write", lambda *_: self.mark_dirty())
        self.message = tk.StringVar(value="Ready · Independent Codex edition · Autosave on")
        ttk.Label(self, textvariable=self.message, style="BookMeta.TLabel", wraplength=1120).pack(fill="x", pady=(8, 0))

    def text_area(self, parent, font, size):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word", undo=True, maxundo=150, font=(font, size),
                       bg="#fffdf5", fg="#263e32", insertbackground="#263e32",
                       padx=18, pady=12, relief="flat", height=8, width=1)
        text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll.set)
        return text

    def refresh_outline(self):
        selected = self.current
        query = self.search.get().strip().lower()
        self.outline.delete(*self.outline.get_children())
        for i, p in enumerate(self.store.book["pages"], 1):
            if query and query not in (p["title"] + " " + p["body"]).lower():
                continue
            self.outline.insert("", "end", iid=p["id"], text=f"{i:02d}  {p['title']}", tags=(p["kind"],))
        if selected and self.outline.exists(selected):
            self.outline.selection_set(selected)
        count = sum(words(p["body"]) for p in self.store.book["pages"])
        self.total.configure(text=f"{len(self.store.book['pages'])} pages / {count:,} words")

    def page(self):
        return next((p for p in self.store.book["pages"] if p["id"] == self.current), None)

    def capture(self):
        p = self.page()
        if p is not None:
            p.update(title=self.title_var.get(), kind=self.kind.get(), strand=self.strand.get(),
                     status=self.status.get(), body=self.editor.get("1.0", "end-1c"),
                     notes=self.notes.get("1.0", "end-1c"))

    def select_page(self, page_id):
        self.capture()
        self.current = page_id
        p = self.page()
        if p is None:
            return
        self.loading = True
        self.title_var.set(p["title"])
        self.kind.set(p["kind"])
        self.strand.set(p["strand"])
        self.status.set(p["status"])
        for widget, key in [(self.editor, "body"), (self.notes, "notes")]:
            widget.delete("1.0", "end")
            widget.insert("1.0", p[key])
            widget.edit_reset()
            widget.edit_modified(False)
        self.loading = False
        self.page_count.configure(text=f"{words(p['body']):,} words · {p['id']}")
        if self.outline.exists(page_id):
            self.outline.selection_set(page_id)
            self.outline.see(page_id)
        self.refresh_images()
        if hasattr(self, 'media'):
            self.media.on_page_changed()

    def on_select(self, _event=None):
        selected = self.outline.selection()
        if selected and selected[0] != self.current:
            self.select_page(selected[0])

    def edited(self, event):
        if event.widget.edit_modified():
            event.widget.edit_modified(False)
            self.mark_dirty()

    def undo(self):
        try:
            self.editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def mark_dirty(self):
        if self.loading:
            return
        self.dirty = True
        self.message.set("Unsaved changes · autosaving shortly…")
        if self.autosave_job:
            self.after_cancel(self.autosave_job)
        self.autosave_job = self.after(1100, self.save)

    def save(self):
        if self.autosave_job:
            self.after_cancel(self.autosave_job)
            self.autosave_job = None
        self.capture()
        try:
            if self.dirty:
                self.store.save()
            self.dirty = False
            self.message.set("Saved locally · previous versions retained in history/")
            self.refresh_outline()
            if self.page():
                self.page_count.configure(text=f"{words(self.page()['body']):,} words · {self.current}")
            return True
        except Exception as exc:
            self.message.set(f"Save needs attention: {exc}")
            return False

    def _destroyed(self, event):
        if event.widget is self and self.autosave_job:
            self.after_cancel(self.autosave_job)

    def close(self):
        if self.save():
            self.winfo_toplevel().destroy()
        else:
            messagebox.showerror("Unsaved book", self.message.get(), parent=self)

    def add_page(self):
        self.capture()
        page = new_page()
        pages = self.store.book["pages"]
        index = next((i + 1 for i, p in enumerate(pages) if p["id"] == self.current), len(pages))
        pages.insert(index, page)
        self.refresh_outline()
        self.select_page(page["id"])
        self.mark_dirty()

    def duplicate(self):
        self.capture()
        p = deepcopy(self.page())
        if p:
            from .storage import new_id
            p["id"] = new_id()
            p["title"] += " — alternate"
            self.store.book["pages"].append(p)
            self.refresh_outline()
            self.select_page(p["id"])
            self.mark_dirty()

    def move(self, direction):
        self.capture()
        pages = self.store.book["pages"]
        index = next(i for i, p in enumerate(pages) if p["id"] == self.current)
        other = index + direction
        if 0 <= other < len(pages):
            pages[index], pages[other] = pages[other], pages[index]
            self.refresh_outline()
            self.mark_dirty()

    def open_path(self, path):
        import os
        os.startfile(str(Path(path).resolve()))

    def read_book(self):
        self.capture()
        try:
            path = self.store.export_html()
            webbrowser.open(path.as_uri())
            self.message.set(f"Reading edition: {path}")
        except Exception as exc:
            messagebox.showerror("Reading edition", str(exc), parent=self)

    def export(self, kind):
        # Exports remain available after a save conflict, so work can be recovered.
        self.capture()
        try:
            path = self.store.export_bundle() if kind == "json" else self.store.export_markdown()
            self.message.set(f"Exported: {path}")
            self.open_path(path.parent)
        except Exception as exc:
            messagebox.showerror("Export", str(exc), parent=self)

    def import_pages(self):
        path = filedialog.askopenfilename(parent=self, title="Append a book bundle or a draft",
            filetypes=[("Book bundle or draft", "*.json *.md *.txt"), ("All files", "*.*")])
        if not path:
            return
        self.capture()
        try:
            if Path(path).suffix.lower() == ".json":
                count = self.store.import_bundle(path)
            else:
                body = Path(path).read_text(encoding="utf-8-sig")
                self.store.book["pages"].append(new_page(Path(path).stem, body=body))
                count = 1
            self.dirty = True
            self.save()
            self.message.set(f"Appended {count} imported pages; use arrows to place them in the book.")
        except Exception as exc:
            messagebox.showerror("Import", str(exc), parent=self)

    def build_images(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x")
        for label, cmd in [("Add image", self.add_image), ("Attach to page", self.attach_image),
                           ("Detach", self.detach_image), ("Edit caption", self.caption_image),
                           ("Render DomeSim plates", self.render_plates)]:
            ttk.Button(toolbar, text=label, command=cmd).pack(side="left", padx=2)
        ttk.Label(parent, text="Select a library image. Place it beside the paragraph it explains, or at the end of the chapter.", wraplength=650, style="BookMeta.TLabel").pack(anchor="w", pady=7)
        placement=ttk.Frame(parent)
        placement.pack(fill='x',pady=(0,6))
        ttk.Label(placement,text='Position in this chapter').pack(side='left',padx=(0,8))
        self.image_position=tk.StringVar(value='Chapter end')
        self.image_positions=ttk.Combobox(placement,textvariable=self.image_position,state='readonly',
                                         values=('Chapter end','Before text'),width=24)
        self.image_positions.pack(side='left')
        ttk.Button(placement,text='Set placement',command=self.place_image).pack(side='left',padx=5)
        search=ttk.Frame(parent)
        search.pack(fill='x',pady=(0,5))
        ttk.Label(search,text='Find illustration').pack(side='left',padx=(0,8))
        self.image_filter=tk.StringVar()
        ttk.Entry(search,textvariable=self.image_filter).pack(side='left',fill='x',expand=True)
        self.only_attached=tk.BooleanVar(value=False)
        ttk.Checkbutton(search,text='This chapter only',variable=self.only_attached,
                        command=self.refresh_images).pack(side='left',padx=8)
        listing=ttk.Frame(parent)
        listing.pack(fill='x')
        self.image_list = tk.Listbox(listing, height=6, exportselection=False)
        self.image_list.pack(side='left',fill="x",expand=True)
        scroll=ttk.Scrollbar(listing,command=self.image_list.yview)
        scroll.pack(side='right',fill='y')
        self.image_list.configure(yscrollcommand=scroll.set)
        self.image_list.bind("<<ListboxSelect>>", lambda e: self.show_image())
        self.image_preview = ttk.Label(parent, anchor="center")
        self.image_preview.pack(fill="both", expand=True, pady=8)
        self.image_caption = ttk.Label(parent, wraplength=700, style="BookMeta.TLabel")
        self.image_caption.pack(fill="x")
        self.image_filter.trace_add('write',lambda *_:self.refresh_images())

    def refresh_images(self):
        query=self.image_filter.get().casefold()
        figures=self.page()['figures'] if self.page() else []
        self.asset_keys = [key for key,asset in self.store.book['assets'].items()
                           if (not self.only_attached.get() or key in figures)
                           and (not query or query in (asset['caption']+' '+asset['provenance']).casefold())]
        self.image_list.delete(0, "end")
        for key in self.asset_keys:
            asset = self.store.book["assets"][key]
            attached = "✓ " if self.page() and key in self.page()["figures"] else "   "
            self.image_list.insert("end", attached + asset["caption"])
        self.image_preview.configure(image="", text="Choose an illustration from the library")
        self.image_caption.configure(text="")
        self.image_position.set('Chapter end')

    def chosen_asset(self):
        choice = self.image_list.curselection()
        return self.asset_keys[choice[0]] if choice else None

    def show_image(self):
        key = self.chosen_asset()
        if key:
            try:
                self.capture()
                from PIL import Image, ImageTk
                asset = self.store.book["assets"][key]
                with Image.open(self.store.asset_path(asset)) as source:
                    im = source.copy()
                im.thumbnail((650, 300))
                self.photos = [ImageTk.PhotoImage(im, master=self)]
                self.image_preview.configure(image=self.photos[0], text="")
                self.image_caption.configure(text=f"{asset['caption']}\n{asset['provenance']}")
                from .placement import figure_groups, prose_paragraph_count
                count=prose_paragraph_count(self.page()['body']) if self.page() else 0
                choices=('Chapter end','Before text',*(f'After paragraph {i}' for i in range(1,count+1)))
                self.image_positions.configure(values=choices)
                groups=figure_groups({'body':self.page()['body'] if self.page() else '', 'figures':[key]},
                                     self.store.book['assets'])
                index=next(iter(groups),None)
                self.image_position.set('Before text' if index==0 else
                    f'After paragraph {index}' if isinstance(index,int) and 1<=index<=count else 'Chapter end')
            except Exception as exc:
                self.image_preview.configure(image="", text=str(exc))

    def add_image(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.gif")])
        if path:
            try:
                key = self.store.add_asset(path, Path(path).stem)
                self.page()["figures"].append(key)
                self.refresh_images()
                self.mark_dirty()
            except Exception as exc:
                messagebox.showerror("Image", str(exc), parent=self)

    def place_image(self):
        key=self.chosen_asset()
        if not key or not self.page() or key not in self.page()['figures']:
            self.message.set('Attach the selected image to this chapter before placing it.')
            return
        self.capture()
        choice=self.image_position.get()
        try:
            index=None if choice=='Chapter end' else 0 if choice=='Before text' else int(choice.rsplit(' ',1)[1])
            key=self.store.set_figure_placement(self.page()['id'],key,index)
        except (ValueError, IndexError) as exc:
            self.show_image()
            self.message.set(str(exc))
            return
        self.refresh_images()
        if key in self.asset_keys:
            row=self.asset_keys.index(key)
            self.image_list.selection_set(row)
            self.image_list.see(row)
            self.show_image()
        self.mark_dirty()
        self.message.set('Illustration positioned in this chapter; rebuild the PDF to include it.')

    def attach_image(self):
        key = self.chosen_asset()
        if key and key not in self.page()["figures"]:
            self.page()["figures"].append(key)
            self.refresh_images()
            self.mark_dirty()

    def detach_image(self):
        key = self.chosen_asset()
        if key and key in self.page()["figures"]:
            self.page()["figures"].remove(key)
            self.refresh_images()
            self.mark_dirty()

    def caption_image(self):
        key = self.chosen_asset()
        if key:
            asset = self.store.book["assets"][key]
            caption = simpledialog.askstring("Image caption", "Caption to print:", initialvalue=asset["caption"], parent=self)
            if caption is not None:
                asset["caption"] = caption
                self.refresh_images()
                self.mark_dirty()

    def render_plates(self):
        if self.pending:
            return
        from .render import render_all
        self.start_job(lambda: render_all(self.store.home / "rendered"), "plates")

    def build_calculator(self, parent):
        ttk.Label(parent, text="Two routes to one dome", font=("Georgia", 16)).pack(anchor="w")
        ttk.Label(parent, text="A = long; B = short. Nominal chords and physical stock are reported separately. All dimensions use feet or inches as labeled.", wraplength=690, style="BookMeta.TLabel").pack(anchor="w", pady=5)
        self.fields = {}
        grid = ttk.Frame(parent)
        grid.pack(fill="x")
        inputs = [("Radius (ft)", "radius", "10"), ("Section length (ft)", "section", "6"),
                  ("Sections / tree", "sections", "8"), ("Trees", "trees", "2"),
                  ("Rejected blanks / tree", "rejects", "4"), ("Total end trim (in)", "trim", "0"),
                  ("Bucking kerf (in)", "kerf", "0.25"), ("Trunk diameter (in)", "diameter", "8"),
                  ("Extra fabrication stock (in)", "extra", "0")]
        for i, (label, key, default) in enumerate(inputs):
            row, col = divmod(i, 3)
            cell = ttk.Frame(grid)
            cell.grid(row=row, column=col, sticky="ew", padx=5, pady=3)
            ttk.Label(cell, text=label).pack(anchor="w")
            var = tk.StringVar(value=default)
            ttk.Entry(cell, textvariable=var, width=18).pack(fill="x")
            self.fields[key] = var
            grid.columnconfigure(col, weight=1)
        self.orientation = tk.StringVar(value="point_dome_in")
        ttk.Combobox(parent, textvariable=self.orientation, state="readonly",
                     values=("point_dome_in", "point_panel_in", "point_dome_out", "point_panel_out")).pack(fill="x", pady=5)
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        for label, method in [("From desired radius", "radius"), ("From my trees", "tree"), ("Fit physical stock", "fit")]:
            ttk.Button(row, text=label, command=lambda m=method: self.calculate(m)).pack(side="left", padx=3)
        ttk.Button(row, text="Insert result page", command=self.insert_calculation).pack(side="left", padx=3)
        self.calc_result = self.text_area(parent, "Consolas", 10)
        self.calc_result.insert("1.0", "Choose a route. Zero extra stock means the finished stock envelope only.\nAdd the actual jig overfit / holding allowance before deciding a tree cut length.")
        self.last_calculation = None

    def calculate(self, method):
        if self.pending:
            return
        values = {key: var.get() for key, var in self.fields.items()}
        orientation = self.orientation.get()
        def run():
            from .calculations import tree_first, physical_schedule, fit_physical_stock, report
            if method == "radius":
                result = physical_schedule(values["radius"], values["diameter"], orientation, values["extra"])
            else:
                result = tree_first(values["section"], values["sections"], values["trees"], values["rejects"], values["trim"], values["kerf"])
                if method == "fit":
                    physical = fit_physical_stock(result["usable_stock_in"], values["diameter"], orientation, values["extra"])
                    return "TREE INVENTORY / NOMINAL ESTIMATE\n" + report(result) + "\n\nPHYSICAL STOCK FIT\n" + report(physical), physical
            return report(result), result
        self.start_job(run, "calculation")

    def start_job(self, callback, kind):
        self.pending = True
        self.message.set("Computing project geometry… writing remains available.")
        def run():
            try:
                self.jobs.put((kind, callback(), None))
            except Exception as exc:
                self.jobs.put((kind, None, str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def poll_jobs(self):
        try:
            kind, result, error = self.jobs.get_nowait()
            self.pending = False
            if error:
                self.message.set(error)
                messagebox.showerror("Project calculation", error, parent=self)
            elif kind == "calculation":
                self.calc_result.delete("1.0", "end")
                self.calc_result.insert("1.0", result[0])
                self.last_calculation = result
                self.message.set("Calculation complete · use Insert result page to keep it in the book.")
            else:
                for path, caption, provenance in result:
                    self.store.add_asset(path, caption, provenance)
                self.refresh_images()
                self.mark_dirty()
                self.message.set(f"Added {len(result)} fresh project plates to the image library.")
        except queue.Empty:
            pass
        self.after(150, self.poll_jobs)

    def insert_calculation(self):
        if self.last_calculation:
            from .storage import stamp
            self.capture()
            page = new_page("Sizing worksheet — " + stamp(), "worked", "explanation", "```text\n" + self.last_calculation[0] + "\n```\n")
            page["notes"] = json.dumps(self.last_calculation[1], indent=2)
            self.store.book["pages"].append(page)
            self.refresh_outline()
            self.select_page(page["id"])
            self.mark_dirty()


def attach_book_tab(notebook, home=DEFAULT_HOME):
    for child in notebook.winfo_children():
        if isinstance(child, BookDesk):
            return child
    desk = BookDesk(notebook, home)
    notebook.add(desk, text="2 trees · Book")
    notebook.winfo_toplevel().protocol("WM_DELETE_WINDOW", desk.close)
    return desk


def main():
    import os
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    root = tk.Tk()
    root.title("2 trees — Book desk · Codex parallel edition")
    root.geometry("1280x850")
    root.minsize(1020, 700)
    try:
        ttk.Style(root).theme_use("clam")
    except tk.TclError:
        pass
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    attach_book_tab(notebook)
    root.mainloop()


if __name__ == "__main__":
    main()
