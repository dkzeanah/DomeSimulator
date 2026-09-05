"""Beat Studio: sequence rendered beats into a cut, without re-rendering anything.

The films in this repository used to be one indivisible ninety-minute render, which
meant every change cost the whole thing and there was no way to reorder or replace a
section by hand. :mod:`two_v_demo.beats` breaks a film into beat-sized MP4s; this is the
bench where they get put back together.

It populates itself. Everything under ``beats/<lesson>/`` is in the library the moment
the window opens -- there is no import step, and dropping a file into that folder from a
phone, a screen capture or another editor makes it available on the next start.

What it does:

* **Library** -- every rendered beat, grouped by the section it belongs to, labelled from
  the manifest the renderer wrote.
* **Sequence** -- the cut you are building. Add, remove, reorder, and see the running
  total as you go.
* **Slice** -- cut any library item into a new part at a timestamp, which is how you
  replace half a beat with something else.
* **Build** -- joins the sequence by stream copy, so it takes seconds and the picture is
  exactly what came out of the renderer.

Compositions are plain JSON, so a cut is a file you can keep, diff and send.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import launcher_common as _lc

from .beats import BEATS_DIR, library


ROOT = Path(__file__).resolve().parent.parent
CUTS_DIR = BEATS_DIR / "cuts"


def _tool(name: str) -> str:
    """The real ffmpeg/ffprobe, not the shim that sits first on PATH here."""
    from .audio import resolve_executable
    try:
        return resolve_executable(name, None)
    except RuntimeError:
        return name


def _probe_seconds(path: Path, ffprobe: str | None = None) -> float:
    """Duration of one clip, or zero if it cannot be read.

    A library item that ffprobe cannot open is still listed -- it is usually a render
    that is still in flight -- but it contributes nothing to the running total rather
    than crashing the window.
    """
    try:
        out = subprocess.run(
            [ffprobe or _tool("ffprobe"), "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return 0.0


def _clock(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def main() -> int:
    cfg = _lc.consume_config("beat_studio")
    lesson_key = str(cfg.get("lesson") or "why")
    root = Path(cfg.get("beats_dir") or BEATS_DIR)

    w = _lc.build_widgets()
    tk, ttk = w["tk"], w["ttk"]

    manifest_path = root / lesson_key / "manifest.json"
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
    labels = {b["file"]: b for b in manifest.get("beats", [])}
    section_titles = {s["key"]: s["title"] for s in manifest.get("sections", [])}

    items = library(root, lesson_key)
    durations: dict[str, float] = {}

    root_win = tk.Tk()
    root_win.title(f"Beat Studio — {manifest.get('title', lesson_key)}")
    root_win.geometry("1180x760")
    root_win.minsize(980, 620)
    style = ttk.Style(root_win)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Note.TLabel", foreground="#33404a", font=("Segoe UI", 9))

    ttk.Label(root_win, text="Beat Studio", font=("Segoe UI", 15, "bold")).pack(
        anchor="w", padx=12, pady=(10, 0))
    ttk.Label(
        root_win,
        text=("Everything under beats/ is already loaded — nothing to import. Pick "
              "beats on the left, send them to the sequence on the right, reorder "
              "them, then Build. Joining is a stream copy, so it takes seconds and "
              "does not re-encode anything."),
        wraplength=1120, justify="left", style="Note.TLabel").pack(
        anchor="w", padx=12, pady=(0, 8))

    body = ttk.Frame(root_win)
    body.pack(fill="both", expand=True, padx=12)

    # ---- library -------------------------------------------------------
    left = ttk.LabelFrame(body, text="Library (auto-populated from beats/)")
    left.pack(side="left", fill="both", expand=True)
    lib_box = tk.Listbox(left, activestyle="none", font=("Consolas", 9),
                         selectmode="extended")
    lib_scroll = ttk.Scrollbar(left, command=lib_box.yview)
    lib_box.configure(yscrollcommand=lib_scroll.set)
    lib_box.pack(side="left", fill="both", expand=True)
    lib_scroll.pack(side="right", fill="y")

    lib_paths: list[str] = []

    def refresh_library() -> None:
        lib_box.delete(0, "end")
        lib_paths.clear()
        current_section = None
        for item in library(root, lesson_key):
            path = Path(item["path"])
            meta = labels.get(path.name, {})
            section = item["section"]
            if section != current_section:
                current_section = section
                title = section_titles.get(section, section)
                lib_box.insert("end", f"— {title} —")
                lib_paths.append("")
            seconds = durations.setdefault(item["path"], _probe_seconds(path))
            name = meta.get("title") or item["name"]
            kind = "" if item["kind"] == "beat" else f"  [{item['kind']}]"
            lib_box.insert("end", f"   {_clock(seconds)}  {name}{kind}")
            lib_paths.append(item["path"])

    # ---- sequence ------------------------------------------------------
    right = ttk.LabelFrame(body, text="Sequence")
    right.pack(side="right", fill="both", expand=True, padx=(10, 0))
    seq_box = tk.Listbox(right, activestyle="none", font=("Consolas", 9),
                         selectmode="extended")
    seq_scroll = ttk.Scrollbar(right, command=seq_box.yview)
    seq_box.configure(yscrollcommand=seq_scroll.set)
    seq_box.pack(side="left", fill="both", expand=True)
    seq_scroll.pack(side="right", fill="y")

    sequence: list[str] = []

    def refresh_sequence() -> None:
        seq_box.delete(0, "end")
        total = 0.0
        for path in sequence:
            seconds = durations.setdefault(path, _probe_seconds(Path(path)))
            total += seconds
            meta = labels.get(Path(path).name, {})
            name = meta.get("title") or Path(path).stem
            seq_box.insert("end", f"{_clock(seconds)}  {name}")
        right.configure(text=f"Sequence — {len(sequence)} parts, {_clock(total)}")

    # ---- actions -------------------------------------------------------
    bar = ttk.Frame(root_win)
    bar.pack(fill="x", padx=12, pady=8)
    log = tk.Text(root_win, height=7, bg="#12141a", fg="#d8dee9",
                  font=("Consolas", 9), wrap="word")
    log.pack(fill="both", expand=False, padx=12, pady=(0, 12))

    def say(line: str) -> None:
        log.insert("end", line + "\n")
        log.see("end")

    def add_selected() -> None:
        for index in lib_box.curselection():
            path = lib_paths[index]
            if path:
                sequence.append(path)
        refresh_sequence()

    def add_whole_section() -> None:
        """Add every beat of the section the highlighted row belongs to."""
        chosen = lib_box.curselection()
        if not chosen:
            return
        index = chosen[0]
        while index >= 0 and not lib_paths[index]:
            index += 1
        if index >= len(lib_paths):
            return
        section = Path(lib_paths[index]).parent.name
        for item in library(root, lesson_key):
            if Path(item["path"]).parent.name == section and item["kind"] == "beat":
                sequence.append(item["path"])
        refresh_sequence()

    def remove_selected() -> None:
        for index in sorted(seq_box.curselection(), reverse=True):
            del sequence[index]
        refresh_sequence()

    def move(delta: int) -> None:
        chosen = list(seq_box.curselection())
        if not chosen:
            return
        order = chosen if delta < 0 else list(reversed(chosen))
        for index in order:
            target = index + delta
            if 0 <= target < len(sequence):
                sequence[index], sequence[target] = sequence[target], sequence[index]
        refresh_sequence()
        for index in chosen:
            target = index + delta
            if 0 <= target < len(sequence):
                seq_box.selection_set(target)

    slice_at = tk.StringVar(value="0:15")

    def slice_selected() -> None:
        """Cut a library item in two at the given time, into beats/<lesson>/slices."""
        chosen = lib_box.curselection()
        if not chosen or not lib_paths[chosen[0]]:
            say("pick a library item to slice")
            return
        source = Path(lib_paths[chosen[0]])
        text = slice_at.get().strip()
        try:
            if ":" in text:
                mm, ss = text.split(":")
                at = int(mm) * 60 + float(ss)
            else:
                at = float(text)
        except ValueError:
            say(f"cannot read a time from {text!r}; use 0:15 or 15")
            return
        out_dir = root / lesson_key / "slices"
        out_dir.mkdir(parents=True, exist_ok=True)
        head = out_dir / f"{source.stem}-to-{text.replace(':', 'm')}.mp4"
        tail = out_dir / f"{source.stem}-from-{text.replace(':', 'm')}.mp4"
        try:
            ff = _tool("ffmpeg")
            subprocess.run([ff, "-y", "-loglevel", "error",
                            "-i", str(source), "-t", str(at), "-c", "copy",
                            str(head)], check=True)
            subprocess.run([ff, "-y", "-loglevel", "error",
                            "-ss", str(at), "-i", str(source), "-c", "copy",
                            str(tail)], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            say(f"slice failed: {exc}")
            return
        say(f"sliced {source.name} at {text} -> {head.name}, {tail.name}")
        refresh_library()

    out_name = tk.StringVar(value="my-cut.mp4")

    def build() -> None:
        if not sequence:
            say("sequence is empty")
            return
        CUTS_DIR.mkdir(parents=True, exist_ok=True)
        from .deliverables import next_version_path
        target = next_version_path(CUTS_DIR / out_name.get().strip())
        listing = target.with_suffix(".concat.txt")
        listing.write_text(
            "".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in sequence),
            encoding="utf-8")
        say(f"joining {len(sequence)} parts -> {target.name} …")
        try:
            subprocess.run(
                [_tool("ffmpeg"), "-y", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", str(listing),
                 "-c", "copy", str(target)], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            say(f"join failed: {exc}")
            return
        finally:
            listing.unlink(missing_ok=True)
        say(f"built {target}")

    def save_cut() -> None:
        CUTS_DIR.mkdir(parents=True, exist_ok=True)
        path = CUTS_DIR / (Path(out_name.get()).stem + ".json")
        path.write_text(json.dumps({"lesson": lesson_key, "parts": sequence},
                                   indent=2), encoding="utf-8")
        say(f"saved {path.name}")

    def load_cut() -> None:
        path = CUTS_DIR / (Path(out_name.get()).stem + ".json")
        if not path.is_file():
            say(f"no saved cut at {path.name}")
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        sequence.clear()
        sequence.extend(data.get("parts", []))
        refresh_sequence()
        say(f"loaded {path.name}: {len(sequence)} parts")

    for text, command in (
        ("Add →", add_selected),
        ("Add section →", add_whole_section),
        ("Remove", remove_selected),
        ("Up", lambda: move(-1)),
        ("Down", lambda: move(1)),
        ("Rescan", refresh_library),
    ):
        ttk.Button(bar, text=text, command=command).pack(side="left", padx=3)

    ttk.Label(bar, text="  slice at").pack(side="left")
    ttk.Entry(bar, textvariable=slice_at, width=7).pack(side="left", padx=3)
    ttk.Button(bar, text="Slice", command=slice_selected).pack(side="left", padx=3)

    ttk.Label(bar, text="  output").pack(side="left")
    ttk.Entry(bar, textvariable=out_name, width=24).pack(side="left", padx=3)
    ttk.Button(bar, text="Save cut", command=save_cut).pack(side="left", padx=3)
    ttk.Button(bar, text="Load cut", command=load_cut).pack(side="left", padx=3)
    ttk.Button(bar, text="Build", command=build).pack(side="left", padx=8)

    refresh_library()
    refresh_sequence()
    say(f"library: {root / lesson_key}")
    if not items:
        say("no beats rendered yet — run the Masterclass tab's 'render_beats' action")

    if cfg.get("smoketest"):
        root_win.update()
        root_win.destroy()
        return 0

    root_win.mainloop()
    return 0
