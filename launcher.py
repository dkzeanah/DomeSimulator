"""DomeSim Launcher — one GUI for every standalone tool in this project.

Dome Creator, Assembly Line (and its earlier Simple variant), Presenter
Studio, the 2V Masterclass, Local Voice Studio, and the project
Flatten utility all used to be configured with command-line flags.
That CLI surface has been removed from every tool; this launcher is now
the only supported way to set them.

Mechanism: each tab writes a one-shot JSON "launch ticket"
(``launcher_common.write_config``) describing what you chose, then
spawns the tool with **no command-line arguments at all**. The tool
reads and deletes that ticket at startup (``consume_config``) and acts
on it instead of parsing ``sys.argv``. Running a tool directly, without
this launcher, finds no ticket and falls back to a sensible default
(the plain windowed/fullscreen app) — the scripts still run standalone,
they just no longer accept flags to change their behavior.

Every launch streams the tool's stdout/stderr into the log pane at the
bottom of this window, so console-only actions (self-tests, exports,
diagnostics, batch renders) are visible without opening a terminal.
"""

from __future__ import annotations

import os
from pathlib import Path

import launcher_common as lc

ROOT = Path(__file__).resolve().parent


def main() -> int:
    w = lc.build_widgets()
    tk, ttk = w["tk"], w["ttk"]
    LabeledEntry, LabeledCombo = w["LabeledEntry"], w["LabeledCombo"]
    CheckRow, PathRow = w["CheckRow"], w["PathRow"]

    root = tk.Tk()
    root.title("DomeSim Launcher")
    root.geometry("1040x760")
    root.minsize(860, 620)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    header = ttk.Label(
        root, text="DomeSim Launcher",
        font=("Segoe UI", 15, "bold"))
    header.pack(anchor="w", padx=12, pady=(10, 0))
    ttk.Label(
        root, text="Every tool below used to take command-line flags; "
                   "they are now set here and launched with one click.",
        foreground="#556").pack(anchor="w", padx=12, pady=(0, 8))

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=(0, 6))

    log_frame = ttk.LabelFrame(root, text="Log")
    log_frame.pack(fill="both", expand=False, padx=12, pady=(0, 12))
    log = tk.Text(log_frame, height=11, bg="#12141a", fg="#d8dee9",
                  insertbackground="#d8dee9", font=("Consolas", 9),
                  wrap="word")
    log.pack(fill="both", expand=True, side="left")
    scroll = ttk.Scrollbar(log_frame, command=log.yview)
    scroll.pack(fill="y", side="right")
    log.configure(yscrollcommand=scroll.set)
    log.insert("end", "Ready. Configure a tab, then click its launch "
                      "button.\n")
    log.configure(state="disabled")

    def append_log(line: str) -> None:
        def do():
            log.configure(state="normal")
            log.insert("end", line + "\n")
            log.see("end")
            log.configure(state="disabled")
        root.after(0, do)

    smoketest = os.environ.get("LAUNCHER_SMOKETEST") == "1"
    launched: list[tuple[str, str, dict]] = []

    def run(script: str, tool: str, cfg: dict, name: str) -> None:
        append_log(f"--- launching {name} " + "-" * 40)
        for key, value in cfg.items():
            append_log(f"    {key} = {value!r}")
        if smoketest:
            # record instead of spawning a real process
            launched.append((name, script, dict(cfg)))
            return

        def on_exit(code: int) -> None:
            append_log(f"--- {name} exited (code {code}) " + "-" * 30)
        try:
            lc.launch_tool(script, tool, cfg, on_line=append_log,
                           on_exit=on_exit, cwd=ROOT)
        except Exception as exc:  # noqa: BLE001 - surface to the log pane
            append_log(f"!!! failed to launch {name}: {exc}")

    smoke_callbacks: list[tuple[str, object]] = []

    def tab(title: str) -> "ttk.Frame":
        frame = ttk.Frame(notebook, padding=14)
        notebook.add(frame, text=title)
        return frame

    def section(parent, text):
        ttk.Label(parent, text=text, font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(10, 3))

    def launch_button(parent, text, command):
        ttk.Button(parent, text=text, command=command).pack(
            anchor="w", pady=(12, 4))
        smoke_callbacks.append((text, command))

    # ---- Dome Creator ---------------------------------------------------

    t = tab("Dome Creator")
    ttk.Label(t, text="The full parametric dome customizer: frame, "
                      "panels, layers, rooms, props, power, and the "
                      "site manager. Always opens fullscreen; it has no "
                      "configurable options.",
             wraplength=760, justify="left").pack(anchor="w")
    launch_button(t, "Launch Dome Creator",
                  lambda: run("dome_creator.py", "dome_creator", {},
                             "Dome Creator"))

    # ---- Assembly Line ----------------------------------------------------

    def build_assembly_tab(title, script, tool, has_extras):
        t = tab(title)
        section(t, "Run mode")
        windowed = CheckRow(t, "Windowed (unchecked = fullscreen)", False)
        windowed.pack(anchor="w")
        action = LabeledCombo(t, "Action", ["run", "selftest", "shots"],
                              "run")
        action.pack(fill="x", pady=3)
        section(t, "Offscreen stills (action = shots)")
        shots = LabeledEntry(t, "Times (seconds, comma-sep)", "4,60,120")
        shots.pack(fill="x", pady=3)
        shot_dir = PathRow(t, "Output directory", "shots", mode="dir")
        shot_dir.pack(fill="x", pady=3)
        extras = {}
        if has_extras:
            speed = LabeledEntry(t, "Shot render speed", "3.0")
            speed.pack(fill="x", pady=3)
            panel = LabeledCombo(
                t, "Dock panel to show", ["", "pnl", "flow", "bom",
                                          "benchmark", "value", "scale",
                                          "ledger"], "")
            panel.pack(fill="x", pady=3)
            extras = {"speed": speed, "panel": panel}

        def go():
            cfg = {"action": action.get(), "windowed": windowed.get(),
                  "shots": shots.get(), "shot_dir": shot_dir.get()}
            if extras:
                cfg["shot_speed"] = float(extras["speed"].get() or 3.0)
                if extras["panel"].get():
                    cfg["shot_panel"] = extras["panel"].get()
            run(script, tool, cfg, title)
        launch_button(t, f"Launch {title}", go)

    build_assembly_tab("Assembly Line", "assembly_line.py",
                      "assembly_line", True)
    build_assembly_tab("Assembly Line (Simple)", "assembly_line_simple.py",
                      "assembly_line_simple", False)

    # ---- Presenter Studio ------------------------------------------------

    t = tab("Presenter Studio")
    section(t, "Source (pick one)")
    demo = LabeledCombo(t, "Built-in demo",
                        ["", "airflow", "housing_case"], "airflow")
    demo.pack(fill="x", pady=3)
    script_path = PathRow(t, "...or a presentation script", "",
                          mode="open",
                          filetypes=(("Presentation", "*.json *.py"),
                                     ("All files", "*.*")))
    script_path.pack(fill="x", pady=3)
    prompt = LabeledEntry(t, "...or a production brief", "", width=50)
    prompt.pack(fill="x", pady=3)
    environment = LabeledEntry(t, "Environment prompt (for brief)", "")
    environment.pack(fill="x", pady=3)
    focus = LabeledEntry(t, "Focus objects (comma list, for brief)", "")
    focus.pack(fill="x", pady=3)

    section(t, "Output")
    action = LabeledCombo(t, "Action",
                          ["run", "shots", "export", "selftest"], "run")
    action.pack(fill="x", pady=3)
    export_path = PathRow(t, "Export MP4 path (action = export)",
                          "presenter_output/presentation.mp4", mode="save",
                          filetypes=(("MP4 video", "*.mp4"),))
    export_path.pack(fill="x", pady=3)
    stills = LabeledEntry(t, "Still times (action = shots)", "4,40,90")
    stills.pack(fill="x", pady=3)
    save_json = PathRow(t, "Save as JSON and exit (optional)", "",
                        mode="save", filetypes=(("JSON", "*.json"),))
    save_json.pack(fill="x", pady=3)
    no_narration = CheckRow(t, "No narration (silent export)", False)
    no_narration.pack(anchor="w", pady=3)
    fullscreen = CheckRow(t, "Fullscreen (live run)", False)
    fullscreen.pack(anchor="w")
    fps = LabeledEntry(t, "FPS (export)", "30")
    fps.pack(fill="x", pady=3)
    size = LabeledEntry(t, "Size WxH", "1600x900")
    size.pack(fill="x", pady=3)

    def go_presenter():
        cfg = {"action": action.get(), "no_narration": no_narration.get(),
              "fullscreen": fullscreen.get(), "size": size.get()}
        if demo.get():
            cfg["demo"] = demo.get()
        if script_path.get():
            cfg["script"] = script_path.get()
        if prompt.get():
            cfg["prompt"] = prompt.get()
        if environment.get():
            cfg["environment"] = environment.get()
        if focus.get():
            cfg["focus"] = focus.get()
        if export_path.get():
            cfg["export"] = export_path.get()
        if stills.get():
            cfg["shots"] = stills.get()
        if save_json.get():
            cfg["save_json"] = save_json.get()
        if fps.get():
            cfg["fps"] = int(fps.get())
        run("presenter_studio.py", "presenter", cfg, "Presenter Studio")
    launch_button(t, "Launch Presenter Studio", go_presenter)

    # ---- 2V Masterclass ---------------------------------------------------

    t = tab("2V Masterclass")
    # The launch button lives in a fixed footer, not inside the scrolling
    # body below — this tab has more fields than any other (every former
    # CLI flag), and a button that only appears after scrolling past all
    # of them is effectively invisible. Pack the footer first so it keeps
    # its space regardless of window size.
    mc_footer = ttk.Frame(t)
    mc_footer.pack(side="bottom", fill="x")
    canvas_area = ttk.Frame(t)
    canvas_area.pack(side="top", fill="both", expand=True)
    canvas = tk.Canvas(canvas_area, highlightthickness=0)
    vscroll = ttk.Scrollbar(canvas_area, orient="vertical",
                            command=canvas.yview)
    body = ttk.Frame(canvas)
    body.bind("<Configure>",
             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=body, anchor="nw")
    canvas.configure(yscrollcommand=vscroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")

    def _mc_wheel(event) -> None:
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    # Bind on the whole tab, not on canvas/body: those have gaps between
    # packed rows where the pointer briefly crosses back onto body's own
    # background, which would fire Leave/Enter (and toggle the binding)
    # on every row boundary. t's area is always fully covered by a
    # descendant, so it only sees Enter/Leave at the tab's own edge.
    t.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _mc_wheel))
    t.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    section(body, "Action")
    mc_action = LabeledCombo(
        body, "Action",
        ["run", "selftest", "report", "shots", "export_video",
         "voice_preview", "list_voices", "narration_only", "script",
         "build_packet"], "run")
    mc_action.pack(fill="x", pady=3)
    mc_fullscreen = CheckRow(body, "Fullscreen (live run)", False)
    mc_fullscreen.pack(anchor="w")
    mc_size = LabeledEntry(body, "Size WxH", "1600x900")
    mc_size.pack(fill="x", pady=3)
    mc_fps = LabeledEntry(body, "FPS (export)", "30")
    mc_fps.pack(fill="x", pady=3)

    section(body, "Stills / video export")
    mc_shots = LabeledEntry(body, "Still times (action = shots)", "")
    mc_shots.pack(fill="x", pady=3)
    mc_export = PathRow(body, "Export MP4 (action = export_video)", "",
                        mode="save", filetypes=(("MP4 video", "*.mp4"),))
    mc_export.pack(fill="x", pady=3)
    mc_no_narration = CheckRow(body, "No narration (silent export)", False)
    mc_no_narration.pack(anchor="w")
    mc_local_plan = PathRow(
        body, "Local Voice Studio narration plan (optional)", "",
        mode="open", filetypes=(("JSON", "*.json"),))
    mc_local_plan.pack(fill="x", pady=3)

    section(body, "Voice")
    mc_voice = LabeledEntry(body, "Voice", "en-US-AndrewMultilingualNeural")
    mc_voice.pack(fill="x", pady=3)
    mc_rate = LabeledEntry(body, "Rate", "-3%")
    mc_rate.pack(fill="x", pady=3)
    mc_pitch = LabeledEntry(body, "Pitch", "-2Hz")
    mc_pitch.pack(fill="x", pady=3)
    mc_volume = LabeledEntry(body, "Volume", "+0%")
    mc_volume.pack(fill="x", pady=3)
    mc_locale = LabeledEntry(body, "Voice locale (list_voices)", "en-US")
    mc_locale.pack(fill="x", pady=3)
    mc_voice_preview = PathRow(
        body, "Voice preview MP3 (action = voice_preview)", "",
        mode="save", filetypes=(("MP3 audio", "*.mp3"),))
    mc_voice_preview.pack(fill="x", pady=3)
    mc_narration_only = PathRow(
        body, "Narration-only M4A (action = narration_only)", "",
        mode="save", filetypes=(("M4A audio", "*.m4a"),))
    mc_narration_only.pack(fill="x", pady=3)

    section(body, "Export helpers")
    mc_ffmpeg = PathRow(body, "ffmpeg path (blank = on PATH)", "",
                        mode="open")
    mc_ffmpeg.pack(fill="x", pady=3)
    mc_ffprobe = PathRow(body, "ffprobe path (blank = beside ffmpeg)", "",
                        mode="open")
    mc_ffprobe.pack(fill="x", pady=3)
    mc_script = PathRow(body, "Narration script + SRT (action = script)",
                        "", mode="save", filetypes=(("Markdown", "*.md"),))
    mc_script.pack(fill="x", pady=3)

    section(body, "Build packet (action = build_packet)")
    mc_packet = PathRow(body, "Output directory", "", mode="dir")
    mc_packet.pack(fill="x", pady=3)
    mc_radius = LabeledEntry(body, "Radius (inches, blank = fit)", "")
    mc_radius.pack(fill="x", pady=3)
    mc_deduction = LabeledEntry(body, "Connector deduction (inches)", "0.0")
    mc_deduction.pack(fill="x", pady=3)

    def go_masterclass():
        cfg = {
            "action": mc_action.get(), "fullscreen": mc_fullscreen.get(),
            "size": mc_size.get(), "no_narration": mc_no_narration.get(),
            "voice": mc_voice.get(), "voice_rate": mc_rate.get(),
            "voice_pitch": mc_pitch.get(), "voice_volume": mc_volume.get(),
            "voice_locale": mc_locale.get(),
        }
        if mc_fps.get():
            cfg["fps"] = int(mc_fps.get())
        if mc_shots.get():
            cfg["shots"] = mc_shots.get()
        if mc_export.get():
            cfg["export_video"] = mc_export.get()
        if mc_local_plan.get():
            cfg["local_narration_plan"] = mc_local_plan.get()
        if mc_voice_preview.get():
            cfg["voice_preview"] = mc_voice_preview.get()
        if mc_narration_only.get():
            cfg["narration_only"] = mc_narration_only.get()
        if mc_ffmpeg.get():
            cfg["ffmpeg"] = mc_ffmpeg.get()
        if mc_ffprobe.get():
            cfg["ffprobe"] = mc_ffprobe.get()
        if mc_script.get():
            cfg["script"] = mc_script.get()
        if mc_packet.get():
            cfg["build_packet"] = mc_packet.get()
        if mc_radius.get():
            cfg["radius_in"] = float(mc_radius.get())
        if mc_deduction.get():
            cfg["connector_deduction_in"] = float(mc_deduction.get())
        run("two_v_masterclass.py", "two_v_masterclass", cfg,
            "2V Masterclass")
    ttk.Separator(mc_footer).pack(fill="x")
    launch_button(mc_footer, "Launch 2V Masterclass", go_masterclass)

    # ---- Local Voice Studio ------------------------------------------------

    t = tab("Local Voice Studio")
    ttk.Label(t, text="Recording, dataset, voice-profile, and synthesis "
                      "studio. It already has its own GUI once launched.",
             wraplength=760, justify="left").pack(anchor="w")
    section(t, "Launch")
    lvs_action = LabeledCombo(t, "Action", ["run", "selftest", "diagnose"],
                              "run")
    lvs_action.pack(fill="x", pady=3)
    lvs_project = PathRow(t, "Project folder (optional)", "", mode="dir")
    lvs_project.pack(fill="x", pady=3)

    def go_voice_studio():
        cfg = {"action": lvs_action.get()}
        if lvs_project.get():
            cfg["project"] = lvs_project.get()
        run("local_voice_studio.py", "local_voice_studio", cfg,
            "Local Voice Studio")
    launch_button(t, "Launch Local Voice Studio", go_voice_studio)

    # ---- Flatten utility ----------------------------------------------

    t = tab("Flatten Utility")
    ttk.Label(t, text="Flattens every source file in the project into "
                      "one Markdown file (with a table of contents) for "
                      "uploading the whole codebase to an LLM.",
             wraplength=760, justify="left").pack(anchor="w")
    section(t, "Output")
    flatten_out = PathRow(t, "Output file", "dome_flat.md", mode="save",
                          filetypes=(("Markdown", "*.md"),
                                    ("Text", "*.txt")))
    flatten_out.pack(fill="x", pady=3)

    def go_flatten():
        cfg = {}
        if flatten_out.get():
            cfg["output"] = flatten_out.get()
        run("flatten.py", "flatten", cfg, "Flatten Utility")
    launch_button(t, "Run Flatten", go_flatten)

    if smoketest:
        # Build everything, click every launch button (with real process
        # spawning intercepted above), then tear down. Used by the
        # automated verification pass; never set by normal launches.
        root.update()
        notebook_tabs = notebook.tabs()
        assert len(notebook_tabs) == 7, notebook_tabs
        assert len(smoke_callbacks) == 7, smoke_callbacks
        for label, callback in smoke_callbacks:
            callback()
        assert len(launched) == 7, launched
        for name, script, cfg in launched:
            print(f"SMOKETEST OK: {name:26} -> {script:28} {cfg}")
        root.update()
        root.destroy()
        print(f"SMOKETEST: {len(launched)}/7 launch buttons produced a "
              f"config ticket")
        return 0
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
