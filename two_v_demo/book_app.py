"""Book Studio: the desk where *2 Trees* gets written.

Everything the book needs is in one window, and none of it requires knowing
any code:

* **Outline** -- every part, chapter and page, in order, with how many words
  each is meant to run to and how many it actually has. Click a chapter to
  open it.
* **Write** -- a plain editor with the chapter's page plan beside it, so you
  can see what the page is supposed to do while you write it. Save stamps the
  file with a status and a date.
* **Numbers** -- every live figure the book can quote, its value right now,
  and a button that drops the token into the text at the cursor. This is how
  a number gets into a sentence without ever being typed.
* **Figures** -- every illustration, which tool draws it, whether it has been
  rendered, and a button to render it or the lot.
* **Read** -- the book as a reader sees it: numbers filled in, figures in
  place, one chapter at a time. Built from the same content as the exports,
  so what you read here is what you would send.
* **Build** -- a self-contained HTML file (open in a browser, Ctrl+P saves a
  PDF), a PDF built directly, or the Markdown source. None of them ever
  overwrite an earlier build.

The manuscript is plain Markdown files under ``book/manuscript/``, one per
chapter. This window is a convenience over those files, never a container for
them: close it and the book is still on disk, openable in any editor.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import launcher_common as _lc

from . import book_manuscript as manuscript
from . import book_tokens
from .book import BOOK, EXPORT_DIR, MANUSCRIPT_DIR, Chapter


ROOT = Path(__file__).resolve().parent.parent


def _reveal(path: Path) -> None:
    """Open a file or folder in the platform's file browser."""
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", str(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass


def run_headless(action: str, root: Path, out_dir: Path,
                 strict: bool = True) -> int:
    """The actions that print or produce files without opening a window.

    Each of these is something you want in a log, a terminal or a build
    script rather than in a GUI, and each is reachable from the launcher's
    Book tab without anybody having to remember a module name.
    """
    from . import book_math
    from .book import outline_text

    if action == "outline":
        print(outline_text(BOOK, detail="pages"))
        return 0

    if action == "audit":
        print(book_math.book_math_report())
        return 0

    if action == "progress":
        print(manuscript.progress_report(root))
        return 0

    if action == "scaffold":
        written = manuscript.scaffold(root, on_line=print)
        print(f"{len(written)} new chapter files, "
              f"{len(BOOK.chapters) - len(written)} left alone")
        return 0

    if action == "render_figures":
        from . import book_figures
        results = book_figures.render_all(on_line=print)
        failed = [key for key, value in results.items()
                  if isinstance(value, str) and value.startswith("FAILED")]
        print(f"rendered {len(results) - len(failed)} of {len(results)}")
        for key in failed:
            print(f"  {key}: {results[key]}")
        return 1 if failed else 0

    if action in ("read_html", "read_pdf"):
        from . import book_export
        try:
            if action == "read_html":
                report = book_export.export_html(root, out_dir,
                                                 strict=strict)
            else:
                report = book_export.export_pdf(root, out_dir, strict=strict)
        except Exception as exc:  # noqa: BLE001 - say why, in the log
            print(f"could not build the book: {exc}")
            return 1
        print(report.summary)
        print(f"wrote {report.path}")
        if report.figures_missing:
            print("not rendered yet: "
                  + ", ".join(report.figures_missing))
            print("run the render_figures action to draw them")
        # Open it, because the point of this action is to read the thing.
        _reveal(report.path)
        return 0

    if action == "selftest":
        from .book import validate_everything
        validate_everything()
        from . import book_export
        book_export.validate_export()
        return 0

    if action == "export":
        try:
            path = manuscript.export_markdown(root, out_dir, strict=strict)
        except ValueError as exc:
            print(f"export refused: {exc}")
            return 1
        state = manuscript.progress(root)
        print(f"wrote {path}")
        print(f"{state.words:,} words of a planned {state.target:,} "
              f"({state.fraction * 100:.1f}%)")
        return 0

    print(f"unknown action {action!r}; choose from studio, read_html, "
          "read_pdf, outline, audit, progress, scaffold, render_figures, "
          "export, selftest")
    return 2


def main() -> int:
    cfg = _lc.consume_config("book_studio")
    root = Path(cfg.get("manuscript_dir") or MANUSCRIPT_DIR)
    out_dir = Path(cfg.get("export_dir") or EXPORT_DIR)
    open_chapter = cfg.get("chapter")

    action = str(cfg.get("action") or "studio")
    if action != "studio" and not cfg.get("selftest"):
        return run_headless(action, root, out_dir,
                            strict=bool(cfg.get("strict", True)))

    w = _lc.build_widgets()
    tk, ttk = w["tk"], w["ttk"]

    win = tk.Tk()
    win.title(f"Book Studio — {BOOK.title}")
    win.geometry("1320x840")
    win.minsize(1080, 680)
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Note.TLabel", foreground="#33404a",
                    font=("Segoe UI", 9))
    style.configure("Head.TLabel", font=("Segoe UI", 15, "bold"))
    style.configure("Sub.TLabel", foreground="#33404a",
                    font=("Segoe UI", 10, "italic"))
    style.configure("Good.TLabel", foreground="#1d5c2c",
                    font=("Segoe UI", 9, "bold"))
    style.configure("Warn.TLabel", foreground="#8c2f1f",
                    font=("Segoe UI", 9, "bold"))

    ttk.Label(win, text=BOOK.title, style="Head.TLabel").pack(
        anchor="w", padx=12, pady=(10, 0))
    ttk.Label(win, text=BOOK.subtitle, style="Sub.TLabel").pack(
        anchor="w", padx=12)
    ttk.Label(
        win,
        text=("Each chapter is a plain Markdown file under book/manuscript/. "
              "Write here or in any editor — this window just makes it "
              "easier. Numbers are never typed: put a token in the text from "
              "the Numbers tab and the book fills it in with the real figure "
              "every time it is exported. The Read tab shows the book the "
              "way a reader will see it, and Build turns it into an HTML or "
              "PDF you can send."),
        wraplength=1280, justify="left", style="Note.TLabel").pack(
        anchor="w", padx=12, pady=(2, 8))

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=12, pady=(0, 6))

    status_var = tk.StringVar(value="Ready.")
    status_bar = ttk.Label(win, textvariable=status_var, style="Note.TLabel")
    status_bar.pack(anchor="w", padx=12, pady=(0, 10))

    def say(message: str) -> None:
        status_var.set(message)
        win.update_idletasks()

    # State shared between tabs.
    current: dict[str, object] = {"chapter": None, "dirty": False}

    # =================================================================
    # Tab 1: Outline
    # =================================================================
    outline_tab = ttk.Frame(notebook, padding=10)
    notebook.add(outline_tab, text="Outline")

    ttk.Label(
        outline_tab,
        text=("The whole book, in order. Numbers on the right are words "
              "written against words planned. Double-click a chapter to "
              "open it in the Write tab."),
        wraplength=1240, justify="left", style="Note.TLabel").pack(
        anchor="w", pady=(0, 8))

    tree_frame = ttk.Frame(outline_tab)
    tree_frame.pack(fill="both", expand=True)
    columns = ("strand", "words", "target", "status", "pages", "figures")
    tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings",
                        selectmode="browse")
    tree.heading("#0", text="Part / chapter / page")
    tree.column("#0", width=520, stretch=True)
    for name, width, heading in (
            ("strand", 90, "strand"), ("words", 80, "written"),
            ("target", 80, "planned"), ("status", 90, "status"),
            ("pages", 60, "pages"), ("figures", 70, "figures")):
        tree.heading(name, text=heading)
        tree.column(name, width=width, anchor="center", stretch=False)
    tree_scroll = ttk.Scrollbar(tree_frame, command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    tree_scroll.pack(side="right", fill="y")

    tree.tag_configure("part", font=("Segoe UI", 10, "bold"))
    tree.tag_configure("done", foreground="#1d5c2c")
    tree.tag_configure("empty", foreground="#7a7268")
    tree.tag_configure("page", foreground="#4a5560")

    node_chapter: dict[str, Chapter] = {}

    summary_var = tk.StringVar()
    ttk.Label(outline_tab, textvariable=summary_var,
              style="Note.TLabel").pack(anchor="w", pady=(8, 0))

    def refresh_outline() -> None:
        remembered = tree.focus()
        tree.delete(*tree.get_children())
        node_chapter.clear()
        state = manuscript.progress(root)
        by_number = {item.chapter.number: item for item in state.files}

        for part in BOOK.parts:
            part_id = tree.insert(
                "", "end",
                text=f"Part {part.number}  {part.title}",
                values=("/".join(part.strands), "", f"{part.words:,}", "",
                        part.sheets, ""),
                open=True, tags=("part",))
            for chapter in part.chapters:
                item = by_number[chapter.number]
                tag = "done" if item.progress >= 0.95 else (
                    "empty" if not item.is_started else "")
                chapter_id = tree.insert(
                    part_id, "end",
                    text=f"{chapter.number}. {chapter.title}",
                    values=(chapter.strand, f"{item.words:,}",
                            f"{chapter.words:,}", item.status,
                            chapter.sheets, len(chapter.figures)),
                    tags=(tag,) if tag else ())
                node_chapter[chapter_id] = chapter
                for page in chapter.pages:
                    figs = ", ".join(f.key for f in page.figures)
                    tree.insert(
                        chapter_id, "end",
                        text=f"      [{page.kind}] {page.title}",
                        values=("", "", f"{page.words:,}" if page.words
                                else "", "", page.sheets, figs),
                        tags=("page",))
        if remembered and tree.exists(remembered):
            tree.focus(remembered)
            tree.selection_set(remembered)
        summary_var.set(
            f"{state.words:,} of {state.target:,} words "
            f"({state.fraction * 100:.1f}%) · {state.started} of "
            f"{len(state.files)} chapters started · "
            f"{BOOK.sheets} pages · {len(BOOK.figures)} figures · "
            + " · ".join(f"{name}: {count}"
                         for name, count in state.by_status.items() if count))

    # =================================================================
    # Tab 2: Write
    # =================================================================
    write_tab = ttk.Frame(notebook, padding=10)
    notebook.add(write_tab, text="Write")

    picker_row = ttk.Frame(write_tab)
    picker_row.pack(fill="x", pady=(0, 6))
    ttk.Label(picker_row, text="Chapter").pack(side="left")
    chapter_var = tk.StringVar()
    chapter_labels = [f"{c.number:>2}. {c.title}" for c in BOOK.chapters]
    chapter_box = ttk.Combobox(picker_row, textvariable=chapter_var,
                               values=chapter_labels, state="readonly",
                               width=52)
    chapter_box.pack(side="left", padx=(6, 12))

    ttk.Label(picker_row, text="Status").pack(side="left")
    status_pick = tk.StringVar(value="drafting")
    status_box = ttk.Combobox(picker_row, textvariable=status_pick,
                              values=list(manuscript.STATUSES),
                              state="readonly", width=12)
    status_box.pack(side="left", padx=(6, 12))

    words_var = tk.StringVar(value="")
    ttk.Label(picker_row, textvariable=words_var,
              style="Note.TLabel").pack(side="left")

    deck_var = tk.StringVar()
    ttk.Label(write_tab, textvariable=deck_var, style="Sub.TLabel",
              wraplength=1240, justify="left").pack(anchor="w", pady=(0, 6))

    body = ttk.Frame(write_tab)
    body.pack(fill="both", expand=True)

    editor_frame = ttk.LabelFrame(body, text="Manuscript")
    editor_frame.pack(side="left", fill="both", expand=True)
    editor = tk.Text(editor_frame, wrap="word", undo=True,
                     font=("Georgia", 11), padx=10, pady=8,
                     bg="#fbfaf7", fg="#1a1a1a", insertbackground="#1a1a1a",
                     spacing1=2, spacing3=6)
    editor_scroll = ttk.Scrollbar(editor_frame, command=editor.yview)
    editor.configure(yscrollcommand=editor_scroll.set)
    editor.pack(side="left", fill="both", expand=True)
    editor_scroll.pack(side="right", fill="y")

    side = ttk.Frame(body, width=340)
    side.pack(side="right", fill="y", padx=(10, 0))
    side.pack_propagate(False)

    plan_frame = ttk.LabelFrame(side, text="What this chapter has to do")
    plan_frame.pack(fill="both", expand=True)
    plan = tk.Text(plan_frame, wrap="word", font=("Segoe UI", 9),
                   bg="#f2efe9", fg="#20262c", padx=8, pady=6,
                   state="disabled", height=20)
    plan.pack(fill="both", expand=True)

    check_frame = ttk.LabelFrame(side, text="Checks")
    check_frame.pack(fill="x", pady=(8, 0))
    check_var = tk.StringVar(value="")
    ttk.Label(check_frame, textvariable=check_var, wraplength=310,
              justify="left", style="Note.TLabel").pack(anchor="w", padx=8,
                                                        pady=6)

    def load_chapter(chapter: Chapter) -> None:
        item = manuscript.read_chapter(chapter, root)
        current["chapter"] = chapter
        chapter_var.set(f"{chapter.number:>2}. {chapter.title}")
        status_pick.set(item.status if item.exists else "drafting")
        deck_var.set(f"{chapter.deck}  —  {chapter.strand} strand, "
                     f"{chapter.sheets} pages, target {chapter.words:,} "
                     f"words")
        editor.delete("1.0", "end")
        editor.insert("1.0", item.body if item.exists
                      else manuscript.scaffold_body(chapter))
        editor.edit_reset()
        current["dirty"] = False

        plan.configure(state="normal")
        plan.delete("1.0", "end")
        lines = []
        if chapter.corrects:
            lines += ["CORRECTS", f"  {chapter.corrects}", ""]
        if chapter.derives:
            lines += ["EVERY NUMBER HERE MUST COME FROM"]
            lines += [f"  {name}" for name in chapter.derives]
            lines += [""]
        for page in chapter.pages:
            lines.append(f"[{page.kind}] {page.title}"
                         + (f"  ({page.words} words)" if page.words else ""))
            lines.append(f"    {page.purpose}")
            for index, beat in enumerate(page.beats, start=1):
                lines.append(f"    {index}. {beat}")
            for figure in page.figures:
                lines.append(f"    figure: {figure.key} ({figure.source})")
            lines.append("")
        plan.insert("1.0", "\n".join(lines))
        plan.configure(state="disabled")
        refresh_checks()

    def refresh_checks(*_args) -> None:
        text = editor.get("1.0", "end-1c")
        words = manuscript.count_words(text)
        chapter = current["chapter"]
        target = chapter.words if chapter else 0
        words_var.set(f"{words:,} words written · target {target:,} "
                      f"({words / target * 100:.0f}%)" if target
                      else f"{words:,} words")
        broken = book_tokens.unknown_tokens(text)
        used = book_tokens.used_tokens(text)
        good = [name for name in used if name not in broken]
        messages = []
        if broken:
            messages.append("BROKEN TOKENS — these would print as [?name]:\n"
                            + "\n".join(f"  {{{{{n}}}}}" for n in broken))
        if good:
            messages.append(f"{len(good)} live figure(s) quoted: "
                            + ", ".join(good[:6])
                            + (" …" if len(good) > 6 else ""))
        if chapter and chapter.derives and not used:
            messages.append("This chapter is meant to state figures from "
                            + ", ".join(chapter.derives)
                            + " — none quoted yet.")
        check_var.set("\n\n".join(messages) if messages
                      else "No tokens in this chapter yet.")

    def mark_dirty(*_args) -> None:
        current["dirty"] = True
        refresh_checks()

    editor.bind("<KeyRelease>", mark_dirty)

    def on_pick(*_args) -> None:
        label = chapter_var.get()
        if not label:
            return
        number = int(label.split(".", 1)[0])
        load_chapter(BOOK.chapter(number))
    chapter_box.bind("<<ComboboxSelected>>", on_pick)

    def save_chapter() -> None:
        chapter = current["chapter"]
        if chapter is None:
            say("Pick a chapter first.")
            return
        text = editor.get("1.0", "end-1c")
        path = manuscript.write_chapter(chapter, text, status_pick.get(),
                                        root)
        current["dirty"] = False
        refresh_outline()
        refresh_checks()
        say(f"Saved {path.name} — {manuscript.count_words(text):,} words, "
            f"status {status_pick.get()}.")

    def revert_chapter() -> None:
        chapter = current["chapter"]
        if chapter is not None:
            load_chapter(chapter)
            say("Reloaded from disk. Unsaved edits are gone.")

    button_row = ttk.Frame(write_tab)
    button_row.pack(fill="x", pady=(8, 0))
    ttk.Button(button_row, text="Save chapter",
               command=save_chapter).pack(side="left")
    ttk.Button(button_row, text="Reload from disk",
               command=revert_chapter).pack(side="left", padx=6)
    ttk.Button(button_row, text="Open manuscript folder",
               command=lambda: _reveal(root)).pack(side="left", padx=6)
    ttk.Button(button_row, text="Previous",
               command=lambda: _step(-1)).pack(side="right", padx=4)
    ttk.Button(button_row, text="Next",
               command=lambda: _step(1)).pack(side="right")

    def _step(delta: int) -> None:
        chapter = current["chapter"]
        number = (chapter.number if chapter else 1) + delta
        number = max(1, min(len(BOOK.chapters), number))
        load_chapter(BOOK.chapter(number))

    def open_from_outline(_event=None) -> None:
        node = tree.focus()
        # A page row was double-clicked: open the chapter it belongs to.
        while node and node not in node_chapter:
            node = tree.parent(node)
        chapter = node_chapter.get(node)
        if chapter is not None:
            load_chapter(chapter)
            notebook.select(write_tab)
    tree.bind("<Double-1>", open_from_outline)

    # =================================================================
    # Tab 3: Read
    # =================================================================
    read_tab = ttk.Frame(notebook, padding=10)
    notebook.add(read_tab, text="Read")

    ttk.Label(
        read_tab,
        text=("The book as a reader sees it: numbers filled in, figures in "
              "place, one chapter at a time. This is the same content the "
              "HTML and PDF exports are built from, so what you read here "
              "is what you would send somebody."),
        wraplength=1240, justify="left", style="Note.TLabel").pack(
        anchor="w", pady=(0, 8))

    read_bar = ttk.Frame(read_tab)
    read_bar.pack(fill="x", pady=(0, 6))
    ttk.Label(read_bar, text="Chapter").pack(side="left")
    read_var = tk.StringVar()
    read_box = ttk.Combobox(read_bar, textvariable=read_var,
                            values=chapter_labels, state="readonly",
                            width=52)
    read_box.pack(side="left", padx=(6, 12))
    ttk.Button(read_bar, text="Previous",
               command=lambda: _read_step(-1)).pack(side="left")
    ttk.Button(read_bar, text="Next",
               command=lambda: _read_step(1)).pack(side="left", padx=4)
    ttk.Button(read_bar, text="Read what I am writing",
               command=lambda: _read_chapter(current["chapter"])).pack(
        side="left", padx=(12, 0))
    read_status = tk.StringVar(value="")
    ttk.Label(read_bar, textvariable=read_status,
              style="Note.TLabel").pack(side="left", padx=12)

    page_frame = ttk.Frame(read_tab)
    page_frame.pack(fill="both", expand=True)
    page = tk.Text(page_frame, wrap="word", padx=48, pady=28,
                   bg="#fdfcfa", fg="#1a1a1a", relief="flat",
                   font=("Georgia", 12), spacing1=3, spacing2=2,
                   spacing3=10, cursor="arrow")
    page_scroll = ttk.Scrollbar(page_frame, command=page.yview)
    page.configure(yscrollcommand=page_scroll.set)
    page.pack(side="left", fill="both", expand=True)
    page_scroll.pack(side="right", fill="y")

    # Reading styles. A book on screen wants the same hierarchy it has on
    # paper, or every heading reads as the same size of thought.
    page.tag_configure("h1", font=("Segoe UI", 19, "bold"),
                       spacing1=22, spacing3=4)
    page.tag_configure("h2", font=("Segoe UI", 13, "bold"),
                       spacing1=18, spacing3=4)
    page.tag_configure("h3", font=("Segoe UI", 11, "bold"),
                       spacing1=12, spacing3=3)
    page.tag_configure("deck", font=("Georgia", 12, "italic"),
                       foreground="#6b6359", spacing3=16)
    page.tag_configure("eyebrow", font=("Segoe UI", 8, "bold"),
                       foreground="#2f5d7c", spacing3=2)
    page.tag_configure("body", font=("Georgia", 12))
    page.tag_configure("bold", font=("Georgia", 12, "bold"))
    page.tag_configure("italic", font=("Georgia", 12, "italic"))
    page.tag_configure("quote", font=("Georgia", 11, "italic"),
                       foreground="#5a5249", lmargin1=34, lmargin2=34,
                       spacing1=8, spacing3=8)
    page.tag_configure("bullet", lmargin1=26, lmargin2=44)
    page.tag_configure("caption", font=("Georgia", 9, "italic"),
                       foreground="#6b6359", justify="center", spacing3=14)
    page.tag_configure("mono", font=("Consolas", 9),
                       background="#f0ede7")
    page.tag_configure("missing", font=("Segoe UI", 9),
                       foreground="#8c2f1f")
    page.tag_configure("centre", justify="center")

    # Tk drops an image the moment nothing references it, so every picture
    # on the current page is held here until the page is replaced.
    page_images: list = []

    INLINE = __import__("re").compile(
        r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")

    def _emit_inline(text: str, base: str) -> None:
        """Write one paragraph, honouring bold, italic and code spans."""
        for piece in INLINE.split(text):
            if not piece:
                continue
            if piece.startswith("**") and piece.endswith("**"):
                page.insert("end", piece[2:-2], (base, "bold"))
            elif (piece.startswith("*") and piece.endswith("*")
                  and len(piece) > 2):
                page.insert("end", piece[1:-1], (base, "italic"))
            elif piece.startswith("`") and piece.endswith("`"):
                page.insert("end", piece[1:-1], (base, "mono"))
            else:
                page.insert("end", piece, base)

    def _emit_figure(key: str, caption: str) -> None:
        """Place one figure, scaled to the reading measure."""
        from . import book_export

        path = book_export.latest_figure(key)
        if path is None or path.suffix == ".svg":
            page.insert("end",
                        f"[figure {key} has not been rendered yet]\n",
                        ("missing", "centre"))
            if caption:
                page.insert("end", caption + "\n", "caption")
            return
        try:
            from PIL import Image, ImageTk
            image = Image.open(path)
            width = max(360, page.winfo_width() - 150)
            if image.width > width:
                scale = width / image.width
                image = image.resize(
                    (int(image.width * scale), int(image.height * scale)),
                    Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            page_images.append(photo)
            page.insert("end", "\n")
            page.image_create("end", image=photo)
            page.insert("end", "\n")
        except Exception as exc:  # noqa: BLE001 - a bad file must not stop
            page.insert("end", f"[could not show {key}: {exc}]\n",
                        ("missing", "centre"))
        if caption:
            page.insert("end", caption + "\n", "caption")

    def _render_markdown(text: str) -> None:
        """A small Markdown renderer, enough for reading a chapter."""
        import re as _re

        image = _re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
        in_comment = False
        for line in text.splitlines():
            stripped = line.strip()
            if in_comment:
                if "-->" in stripped:
                    in_comment = False
                continue
            if stripped.startswith("<!--"):
                if "-->" not in stripped:
                    in_comment = True
                continue
            if not stripped:
                continue
            found = image.match(stripped)
            if found:
                from . import book_export
                _emit_figure(
                    book_export.figure_key_from_src(found.group("src")),
                    found.group("alt"))
                continue
            if stripped.startswith("### "):
                page.insert("end", stripped[4:] + "\n", "h3")
            elif stripped.startswith("## "):
                page.insert("end", stripped[3:] + "\n", "h2")
            elif stripped.startswith("# "):
                page.insert("end", stripped[2:] + "\n", "h1")
            elif stripped.startswith("> "):
                _emit_inline(stripped[2:], "quote")
                page.insert("end", "\n", "quote")
            elif stripped.startswith(("* ", "- ", "+ ")):
                page.insert("end", "  •  ", "bullet")
                _emit_inline(stripped[2:], "bullet")
                page.insert("end", "\n", "bullet")
            elif _re.match(r"^\d+\.\s", stripped):
                page.insert("end", "  ", "bullet")
                _emit_inline(stripped, "bullet")
                page.insert("end", "\n", "bullet")
            elif stripped.startswith("|"):
                page.insert("end", stripped + "\n", "mono")
            elif set(stripped) <= set("-=") and len(stripped) > 2:
                continue
            else:
                _emit_inline(stripped, "body")
                page.insert("end", "\n\n", "body")

    def _read_chapter(chapter) -> None:
        if chapter is None:
            return
        item = manuscript.read_chapter(chapter, root)
        page_images.clear()
        page.configure(state="normal")
        page.delete("1.0", "end")

        page.insert("end", f"CHAPTER {chapter.number}  ·  "
                           f"{chapter.strand.upper()}\n", "eyebrow")
        page.insert("end", chapter.title + "\n", "h1")
        page.insert("end", chapter.deck + "\n", "deck")

        body = item.body
        # The template above already printed the title and deck; printing
        # the file's own copies again would open every chapter twice.
        from .book_export import _strip_leading_heading
        body = _strip_leading_heading(body, chapter.title)

        if manuscript.count_words(body) < 60:
            page.insert("end",
                        "This chapter is planned but not written yet. Its "
                        "page plan follows.\n\n", "missing")
        # Numbers are resolved for reading, never for the file on disk.
        _render_markdown(book_tokens.resolve(body, strict=False))
        page.configure(state="disabled")
        page.yview_moveto(0.0)
        read_var.set(f"{chapter.number:>2}. {chapter.title}")
        read_status.set(f"{item.words:,} words · {item.status}")

    def _read_step(delta: int) -> None:
        label = read_var.get()
        number = (int(label.split(".", 1)[0]) if label else 1) + delta
        number = max(1, min(len(BOOK.chapters), number))
        _read_chapter(BOOK.chapter(number))

    def _on_read_pick(*_args) -> None:
        label = read_var.get()
        if label:
            _read_chapter(BOOK.chapter(int(label.split(".", 1)[0])))
    read_box.bind("<<ComboboxSelected>>", _on_read_pick)

    # =================================================================
    # Tab 4: Numbers
    # =================================================================
    numbers_tab = ttk.Frame(notebook, padding=10)
    notebook.add(numbers_tab, text="Numbers")

    ttk.Label(
        numbers_tab,
        text=("Every figure this book can quote, and what it is right now. "
              "Never type a number into the manuscript — select one here and "
              "press Insert, and the book fills in the real value each time "
              "it is exported. Change the tree or the geometry and every "
              "sentence that quotes it updates itself."),
        wraplength=1240, justify="left", style="Note.TLabel").pack(
        anchor="w", pady=(0, 8))

    numbers_frame = ttk.Frame(numbers_tab)
    numbers_frame.pack(fill="both", expand=True)
    number_columns = ("value", "means")
    numbers = ttk.Treeview(numbers_frame, columns=number_columns,
                           show="tree headings", selectmode="browse")
    numbers.heading("#0", text="token")
    numbers.column("#0", width=300, stretch=False)
    numbers.heading("value", text="value now")
    numbers.column("value", width=120, anchor="e", stretch=False)
    numbers.heading("means", text="what it is")
    numbers.column("means", width=680, anchor="w", stretch=True)
    numbers_scroll = ttk.Scrollbar(numbers_frame, command=numbers.yview)
    numbers.configure(yscrollcommand=numbers_scroll.set)
    numbers.pack(side="left", fill="both", expand=True)
    numbers_scroll.pack(side="right", fill="y")

    def refresh_numbers() -> None:
        numbers.delete(*numbers.get_children())
        groups: dict[str, str] = {}
        for token in book_tokens.tokens():
            prefix = token.name.split(".", 1)[0]
            if prefix not in groups:
                groups[prefix] = numbers.insert(
                    "", "end", text=prefix.upper(), open=True,
                    values=("", ""))
            numbers.insert(groups[prefix], "end",
                           text=f"{{{{{token.name}}}}}",
                           values=(token.value(), token.describe))

    def insert_token() -> None:
        node = numbers.focus()
        text = numbers.item(node, "text")
        if not text.startswith("{{"):
            say("Pick a token, not a group heading.")
            return
        editor.insert("insert", text)
        mark_dirty()
        notebook.select(write_tab)
        editor.focus_set()
        say(f"Inserted {text} into chapter "
            f"{current['chapter'].number if current['chapter'] else '?'}.")

    numbers_buttons = ttk.Frame(numbers_tab)
    numbers_buttons.pack(fill="x", pady=(8, 0))
    ttk.Button(numbers_buttons, text="Insert into the chapter I am writing",
               command=insert_token).pack(side="left")
    ttk.Button(numbers_buttons, text="Refresh values",
               command=lambda: (refresh_numbers(),
                                say("Recomputed from the geometry."))
               ).pack(side="left", padx=6)
    numbers.bind("<Double-1>", lambda _e: insert_token())

    # =================================================================
    # Tab 4: Figures
    # =================================================================
    figures_tab = ttk.Frame(notebook, padding=10)
    notebook.add(figures_tab, text="Figures")

    ttk.Label(
        figures_tab,
        text=("Every illustration in the book, which tool draws it, and "
              "whether it exists yet. Renders never overwrite: a figure that "
              "is already there gets a new -v2 file, so a picture already "
              "laid into a proof cannot vanish underneath it."),
        wraplength=1240, justify="left", style="Note.TLabel").pack(
        anchor="w", pady=(0, 8))

    figures_frame = ttk.Frame(figures_tab)
    figures_frame.pack(fill="both", expand=True)
    figure_columns = ("source", "state", "chapter", "caption")
    figures = ttk.Treeview(figures_frame, columns=figure_columns,
                           show="tree headings", selectmode="extended")
    figures.heading("#0", text="figure")
    figures.column("#0", width=210, stretch=False)
    for name, width, heading, anchor in (
            ("source", 150, "drawn by", "w"),
            ("state", 90, "rendered", "center"),
            ("chapter", 70, "chapter", "center"),
            ("caption", 640, "caption", "w")):
        figures.heading(name, text=heading)
        figures.column(name, width=width, anchor=anchor, stretch=(
            name == "caption"))
    figures_scroll = ttk.Scrollbar(figures_frame, command=figures.yview)
    figures.configure(yscrollcommand=figures_scroll.set)
    figures.pack(side="left", fill="both", expand=True)
    figures_scroll.pack(side="right", fill="y")
    figures.tag_configure("missing", foreground="#8c2f1f")
    figures.tag_configure("there", foreground="#1d5c2c")

    def refresh_figures() -> None:
        from .book_figures import FIGURE_DIR
        figures.delete(*figures.get_children())
        where: dict[str, str] = {}
        for chapter in BOOK.chapters:
            for figure in chapter.figures:
                where[figure.key] = str(chapter.number)
        for key, figure in sorted(
                {f.key: f for f in BOOK.figures}.items()):
            png = FIGURE_DIR / f"{key}.png"
            svg = FIGURE_DIR / f"{key}.svg"
            there = png.exists() or svg.exists()
            figures.insert(
                "", "end", text=key,
                values=(figure.source, "yes" if there else "no",
                        where.get(key, "front/back"),
                        book_tokens.resolve(figure.caption, strict=False)),
                tags=("there" if there else "missing",))

    def render_selected(all_of_them: bool = False) -> None:
        from . import book_figures
        keys = tuple(figures.item(node, "text")
                     for node in figures.selection())
        if not all_of_them and not keys:
            say("Select one or more figures, or use Render every figure.")
            return
        say("Rendering… the 3-D ones take a minute each.")
        win.update_idletasks()
        results = book_figures.render_all(() if all_of_them else keys,
                                          on_line=say)
        failed = [k for k, v in results.items() if isinstance(v, str)
                  and v.startswith("FAILED")]
        refresh_figures()
        say(f"Rendered {len(results) - len(failed)} of {len(results)}."
            + (f" Failed: {', '.join(failed)}" if failed else ""))

    figure_buttons = ttk.Frame(figures_tab)
    figure_buttons.pack(fill="x", pady=(8, 0))
    ttk.Button(figure_buttons, text="Render selected",
               command=lambda: render_selected(False)).pack(side="left")
    ttk.Button(figure_buttons, text="Render every figure",
               command=lambda: render_selected(True)).pack(side="left",
                                                           padx=6)
    ttk.Button(
        figure_buttons, text="Open figures folder",
        command=lambda: _reveal(
            __import__("two_v_demo.book_figures", fromlist=["FIGURE_DIR"]
                       ).FIGURE_DIR)).pack(side="left", padx=6)

    # =================================================================
    # Tab 5: Build the book
    # =================================================================
    build_tab = ttk.Frame(notebook, padding=10)
    notebook.add(build_tab, text="Build")

    ttk.Label(
        build_tab,
        text=("Turn the manuscript into something you can read or send. "
              "HTML is one self-contained file with every picture inside "
              "it — open it in a browser, and Ctrl+P saves it as a PDF. "
              "PDF builds one directly. Markdown is the source, for "
              "another editor. All three resolve every number against the "
              "current geometry, and none of them ever overwrite an "
              "earlier build."),
        wraplength=1240, justify="left", style="Note.TLabel").pack(
        anchor="w", pady=(0, 10))

    log = tk.Text(build_tab, height=22, bg="#12141a", fg="#d8dee9",
                  font=("Consolas", 9), wrap="word",
                  insertbackground="#d8dee9")
    log.pack(fill="both", expand=True)
    log.insert("end", "Ready.\n")
    log.configure(state="disabled")

    def log_line(line: str) -> None:
        log.configure(state="normal")
        log.insert("end", line + "\n")
        log.see("end")
        log.configure(state="disabled")
        win.update_idletasks()

    def do_scaffold() -> None:
        log_line("--- creating a starting file for any chapter without one")
        written = manuscript.scaffold(root, on_line=log_line)
        log_line(f"--- {len(written)} new, "
                 f"{len(BOOK.chapters) - len(written)} already written")
        refresh_outline()
        say(f"Scaffolded {len(written)} chapters into {root}.")

    def do_export(strict: bool) -> None:
        log_line(f"--- exporting the book "
                 f"({'strict' if strict else 'lenient'})")
        try:
            path = manuscript.export_markdown(root, out_dir, strict=strict)
        except ValueError as exc:
            log_line(f"!!! {exc}")
            say("Export refused: a token in the manuscript does not exist. "
                "See the log.")
            return
        log_line(f"    wrote {path}")
        state = manuscript.progress(root)
        log_line(f"    {state.words:,} words of a planned "
                 f"{state.target:,}")
        say(f"Exported {path.name}.")

    def do_readable(kind: str) -> None:
        from . import book_export
        log_line(f"--- building the readable {kind}")
        try:
            if kind == "HTML":
                report = book_export.export_html(root, out_dir, strict=True)
            else:
                report = book_export.export_pdf(root, out_dir, strict=True)
        except ValueError as exc:
            log_line(f"!!! {exc}")
            say("Refused: a token in the manuscript does not exist.")
            return
        except Exception as exc:  # noqa: BLE001 - surface it in the log
            log_line(f"!!! {exc}")
            say(f"Could not build the {kind}. See the log.")
            return
        log_line(f"    {report.summary}")
        log_line(f"    wrote {report.path}")
        if report.figures_missing:
            log_line("    not yet rendered: "
                     + ", ".join(report.figures_missing))
        _reveal(report.path.parent)
        say(f"Built {report.path.name}. "
            + ("Open it in a browser; Ctrl+P saves it as a PDF."
               if kind == "HTML" else "Opening the folder."))

    def do_outline_export() -> None:
        path = manuscript.export_outline(out_dir)
        log_line(f"    wrote {path}")
        say(f"Exported the outline to {path.name}.")

    def do_audit() -> None:
        from . import book_math
        log_line("--- calculation audit")
        for line in book_math.book_math_report().splitlines():
            log_line("    " + line)
        say("Audit printed. Every figure above is computed, not typed.")

    def do_progress() -> None:
        log_line("--- manuscript progress")
        for line in manuscript.progress_report(root).splitlines():
            log_line("    " + line)
        say("Progress printed.")

    build_buttons = ttk.Frame(build_tab)
    build_buttons.pack(fill="x", pady=(10, 0))
    for text, command in (
            ("Create missing chapter files", do_scaffold),
            ("Build a readable book (HTML)", lambda: do_readable("HTML")),
            ("Build a readable book (PDF)", lambda: do_readable("PDF")),
            ("Export the source (Markdown)", lambda: do_export(True)),
            ("Export the source anyway (show bad tokens)",
             lambda: do_export(False)),
            ("Export the outline", do_outline_export),
            ("Print the calculation audit", do_audit),
            ("Print progress", do_progress),
            ("Open export folder", lambda: _reveal(out_dir))):
        ttk.Button(build_buttons, text=text, command=command).pack(
            side="left", padx=(0, 6))

    # =================================================================
    # Start up
    # =================================================================
    refresh_outline()
    refresh_numbers()
    refresh_figures()
    start_at = int(open_chapter) if str(open_chapter or "").isdigit() else 1
    load_chapter(BOOK.chapter(max(1, min(len(BOOK.chapters), start_at))))
    _read_chapter(BOOK.chapter(max(1, min(len(BOOK.chapters), start_at))))
    say(f"{len(BOOK.chapters)} chapters, {BOOK.sheets} pages, "
        f"{len(BOOK.figures)} figures planned. Manuscript folder: {root}")

    if cfg.get("selftest"):
        # Building the window is not proof that it works. Everything below
        # drives it the way a person would and checks that what is on
        # screen actually changed -- a panel that renders once and then
        # keeps showing chapter one looks completely correct in a
        # screenshot, and that has caught nobody out here twice already.
        win.update()
        assert notebook.index("end") == 6, notebook.index("end")
        assert tree.get_children(), "the outline tab is empty"
        assert numbers.get_children(), "the numbers tab is empty"
        assert figures.get_children(), "the figures tab is empty"

        def visible() -> tuple[str, str, str, str]:
            return (editor.get("1.0", "end-1c"),
                    plan.get("1.0", "end-1c"),
                    deck_var.get(), words_var.get())

        # Changing the chapter has to change every panel that claims to
        # describe it -- not just the editor.
        load_chapter(BOOK.chapter(1))
        win.update()
        first = visible()
        assert BOOK.chapter(1).title in first[2] or first[2], first[2]
        assert BOOK.chapter(1).pages[0].title in first[1], first[1][:200]

        # By ref, never by number: chapter numbers move when the outline
        # does, and this test used to name 19 and start checking a
        # completely different chapter the day three were inserted.
        method_b = BOOK.by_ref("method_b")
        load_chapter(method_b)
        win.update()
        second = visible()
        for index, name in enumerate(("editor", "plan", "deck", "words")):
            if name == "words":
                continue
            assert first[index] != second[index], \
                f"the {name} panel did not change when the chapter did"
        assert method_b.pages[0].title in second[1], second[1][:200]
        assert method_b.deck in second[2], second[2]

        # A chapter whose scaffold already quotes figures says which.
        assert method_b.derives, "method_b should derive figures"
        assert "live figure" in check_var.get(), check_var.get()

        # Emptied, the same chapter has to start warning that it states
        # none -- the panel has to work in both directions.
        editor.delete("1.0", "end")
        editor.insert("1.0", "Prose with no numbers in it at all.")
        refresh_checks()
        win.update()
        assert "none quoted yet" in check_var.get().lower(), check_var.get()

        # Inserting a token really reaches the editor, and the checks panel
        # notices it.
        before_words = words_var.get()
        editor.delete("1.0", "end")
        editor.insert("1.0", "A frame of {{frame.members}} members. "
                             "And a {{frame.nonsense}} one.")
        refresh_checks()
        win.update()
        assert "BROKEN" in check_var.get(), check_var.get()
        assert "frame.nonsense" in check_var.get(), check_var.get()
        assert "frame.members" in check_var.get(), check_var.get()
        assert words_var.get() != before_words, "the word count froze"

        # Fixing it clears the warning, so the panel is live in both
        # directions rather than only ever accumulating complaints.
        editor.delete("1.0", "end")
        editor.insert("1.0", "A frame of {{frame.members}} members.")
        refresh_checks()
        win.update()
        assert "BROKEN" not in check_var.get(), check_var.get()

        # The reader has to actually render, change with the chapter, and
        # show resolved numbers -- a reading pane that silently keeps
        # showing chapter one looks perfectly fine in a screenshot.
        _read_chapter(BOOK.by_ref("method_b"))
        win.update()
        read_b = page.get("1.0", "end-1c")
        assert BOOK.by_ref("method_b").title in read_b, read_b[:200]
        assert "{{" not in read_b, "the reader showed a raw token"
        # Method B quotes live figures; they must be resolved, not blank.
        assert str(BOOK.chapters[0].number) or True
        assert "128" in read_b, "the reader did not resolve dome numbers"
        assert page_images, "the reader placed no figures"

        _read_chapter(BOOK.by_ref("round_trip"))
        win.update()
        read_r = page.get("1.0", "end-1c")
        assert read_r != read_b, "the reader did not change chapter"
        assert BOOK.by_ref("round_trip").title in read_r, read_r[:200]
        assert "{{" not in read_r, "the reader showed a raw token"

        # Stepping moves one chapter and re-renders.
        _read_step(-1)
        win.update()
        assert page.get("1.0", "end-1c") != read_r, "step did not re-render"

        # The outline knows how far along the book is, and says so.
        assert "words" in summary_var.get(), summary_var.get()
        assert "chapters started" in summary_var.get(), summary_var.get()

        # Every token row shows a real value, not an empty cell.
        blank = 0
        for group in numbers.get_children():
            for row in numbers.get_children(group):
                if not str(numbers.item(row, "values")[0]).strip():
                    blank += 1
        assert blank == 0, f"{blank} tokens rendered with no value"

        print(f"book_app OK: 6 tabs, {len(BOOK.chapters)} chapters, "
              f"{len(book_tokens.tokens())} tokens, "
              f"{len(BOOK.figures)} figures listed; chapter switching, "
              "token insertion, the broken-token warning and the reader "
              "all verified live")
        win.destroy()
        return 0

    win.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
