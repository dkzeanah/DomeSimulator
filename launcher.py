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
                   "they are now set here and launched with one click. "
                   "Each tab explains what its tool does and what its "
                   "fields mean — you do not need to read any code to "
                   "use this. Most tools open a fullscreen 3-D window "
                   "when launched: press Escape to release the mouse, "
                   "then Escape again to quit and return here.",
        wraplength=1000, justify="left",
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

    def intro(parent, text):
        """Plain-language 'what is this and why would I use it' blurb
        that belongs at the top of every tab, before any fields."""
        ttk.Label(parent, text=text, wraplength=760, justify="left",
                 foreground="#9fb0c3").pack(anchor="w", pady=(0, 8))

    def section(parent, text):
        ttk.Label(parent, text=text, font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(10, 3))

    def note(parent, text):
        """Small explanatory text under a field or group of fields —
        format examples, what a dropdown's choices actually do, which
        fields matter only for which Action. Never load-bearing, only
        clarifying, so it always wraps and never fights for space."""
        ttk.Label(parent, text=text, wraplength=740, justify="left",
                 font=("Segoe UI", 8), foreground="#7d8a99").pack(
            anchor="w", pady=(0, 6))

    def launch_button(parent, text, command):
        ttk.Button(parent, text=text, command=command).pack(
            anchor="w", pady=(12, 4))
        smoke_callbacks.append((text, command))

    def scrollable_tab(title: str):
        """A tab whose launch button lives in a fixed footer instead of
        at the bottom of its (scrollable) field list. Some tabs carry
        every option a tool used to accept as CLI flags, plus the
        explanatory text a non-coder needs to use them; without this,
        the button that actually launches the tool can end up scrolled
        out of view below all of it."""
        t = tab(title)
        footer = ttk.Frame(t)
        footer.pack(side="bottom", fill="x")
        canvas_area = ttk.Frame(t)
        canvas_area.pack(side="top", fill="both", expand=True)
        canvas = tk.Canvas(canvas_area, highlightthickness=0)
        vscroll = ttk.Scrollbar(canvas_area, orient="vertical",
                                command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        def _wheel(event) -> None:
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        # Bind on the whole tab, not on canvas/body: those have gaps
        # between packed rows where the pointer briefly crosses back
        # onto body's own background, which would fire Leave/Enter (and
        # toggle the binding) on every row boundary. t's area is always
        # fully covered by a descendant, so it only sees Enter/Leave at
        # the tab's own edge.
        t.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>",
                                                      _wheel))
        t.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
        return t, body, footer

    # ---- Dome Creator ---------------------------------------------------

    t, body, foot = scrollable_tab("Dome Creator")
    intro(body,
         "The full interactive dome designer: build a dome's frame "
         "and panels, add insulation/wiring/plumbing layers, lay out "
         "rooms and furniture, place solar/power equipment, and manage "
         "a whole site of domes — all with the mouse, no typing "
         "required. This is the tool to reach for if you want to "
         "actually design a dome and see it change in real time. It "
         "always opens fullscreen and has no launcher options to set; "
         "everything is controlled once it's open (mouse to look "
         "around and click things, a layers/build menu on screen, "
         "Escape twice to quit).")
    ttk.Separator(foot).pack(fill="x")
    launch_button(foot, "Launch Dome Creator",
                  lambda: run("dome_creator.py", "dome_creator", {},
                             "Dome Creator"))

    # ---- Assembly Line ----------------------------------------------------

    def build_assembly_tab(title, script, tool, has_extras):
        t, body, foot = scrollable_tab(title)
        if has_extras:
            intro(body,
                 "Watch a dome home get built, station by station, on "
                 "a real factory line — and see the real numbers "
                 "behind it: live profit and loss, bill of materials, "
                 "a cost comparison against conventional construction, "
                 "and a production ledger. This is the 'investor demo' "
                 "version — everything on screen is computed from this "
                 "project's own cost model, not decorative.")
        else:
            intro(body,
                 "The same 15-station dome factory line, without the "
                 "cost/data panels — just the build itself, camera "
                 "controls, and nothing else to configure. Use this "
                 "one if you only want to watch a dome get built.")
        section(body, "Run mode")
        windowed = CheckRow(body, "Windowed (unchecked = fullscreen)",
                            False)
        windowed.pack(anchor="w")
        action = LabeledCombo(body, "Action", ["run", "selftest", "shots"],
                              "run")
        action.pack(fill="x", pady=3)
        note(body, "run = open the live simulation (the default). "
                   "selftest = run this tool's internal checks and "
                   "print the result — for troubleshooting, not for "
                   "watching. shots = save still images at chosen "
                   "moments instead of opening a window (see below).")
        section(body, "Offscreen stills (action = shots)")
        shots = LabeledEntry(body, "Times (seconds, comma-sep)",
                             "4,60,120", placeholder="e.g. 4,60,120")
        shots.pack(fill="x", pady=3)
        note(body, "Seconds into the simulation to capture. The "
                   "example saves three PNGs: one 4 seconds in, one at "
                   "60, one at 120.")
        shot_dir = PathRow(body, "Output directory", "shots", mode="dir")
        shot_dir.pack(fill="x", pady=3)
        extras = {}
        if has_extras:
            section(body, "Display (any Action)")
            speed = LabeledEntry(body, "Shot render speed", "3.0",
                                 placeholder="e.g. 3.0")
            speed.pack(fill="x", pady=3)
            note(body, "How many simulated seconds pass per real "
                       "second — higher numbers reach later build "
                       "stages sooner in the stills above.")
            panel = LabeledCombo(
                body, "Dock panel to show", ["", "pnl", "throughput",
                                             "bom", "benchmark", "value",
                                             "scale", "ledger"], "")
            panel.pack(fill="x", pady=3)
            note(body, "Which data panel is docked on screen (blank = "
                       "whatever the simulation last had open). pnl = "
                       "live profit and loss for the dome on the line. "
                       "throughput = production rate and the "
                       "bottleneck station. bom = full bill of "
                       "materials and cost breakdown. benchmark = box "
                       "vs dome cost comparison, bare-shed and "
                       "finished-home tiers. value = the finished "
                       "dome's off-grid story — solar, battery, "
                       "insulation, embodied carbon. scale = what 1, "
                       "3, or 6 production lines looks like, plus "
                       "break-even. ledger = cumulative production and "
                       "sales history.")
            extras = {"speed": speed, "panel": panel}

        def go():
            cfg = {"action": action.get(), "windowed": windowed.get(),
                  "shots": shots.get(), "shot_dir": shot_dir.get()}
            if extras:
                cfg["shot_speed"] = float(extras["speed"].get() or 3.0)
                if extras["panel"].get():
                    cfg["shot_panel"] = extras["panel"].get()
            run(script, tool, cfg, title)
        ttk.Separator(foot).pack(fill="x")
        launch_button(foot, f"Launch {title}", go)

    build_assembly_tab("Assembly Line", "assembly_line.py",
                      "assembly_line", True)
    build_assembly_tab("Assembly Line (Simple)", "assembly_line_simple.py",
                      "assembly_line_simple", False)

    # ---- Presenter Studio ------------------------------------------------

    t, body, ps_footer = scrollable_tab("Presenter Studio")
    intro(body,
         "Presenter Studio turns a script into a narrated 3-D "
         "explainer video: it picks camera angles, animates the "
         "scene, writes on-screen captions and an info panel, and can "
         "generate a spoken voiceover — no video editor needed. Every "
         "finished argument video for 2V dome housing shipped with "
         "this project (see 'Built-in demo' below) was built entirely "
         "with this tool, and every number those videos show comes "
         "from this project's own cost and geometry code, not typed "
         "in by hand.")

    section(body, "Source — fill in exactly one of these three")
    note(body, "Easiest option: leave the other two blank below and "
               "just pick a built-in demo — that alone is enough to "
               "click Launch. The other two are for building "
               "something new instead of watching a finished video.")
    demo = LabeledCombo(body, "Built-in demo",
                        ["", "airflow", "housing_case",
                         "case_manufacturing", "case_bare_shell",
                         "case_more_room", "case_triangles",
                         "case_benchmark", "case_energy",
                         "case_resilience", "case_financing",
                         "case_utility_core", "case_market_fit"],
                        "airflow")
    demo.pack(fill="x", pady=3)
    note(body, "12 videos ship with this project. 'airflow' explains "
               "a dome ventilation system. 'housing_case' is the full "
               "argument for 2V dome housing in one video. The ten "
               "'case_...' videos are that same argument split one "
               "point per video — cost, structural rigidity, energy, "
               "financing, and so on — so you can watch or share just "
               "the one point you need.")
    script_path = PathRow(body, "...or a presentation script", "",
                          mode="open",
                          filetypes=(("Presentation", "*.json *.py"),
                                     ("All files", "*.*")),
                          placeholder="e.g. presenter_output/my_script.json")
    script_path.pack(fill="x", pady=3)
    note(body, "Advanced: a Python file that defines a build() "
               "function, or a .json file previously saved with the "
               "'Save as JSON' option below. Leave this blank unless "
               "you already have one of those files.")
    prompt = LabeledEntry(
        body, "...or a production brief", "", width=50,
        placeholder="e.g. seven scenes each of three shots, a close "
                    "up, macro, and ultra wide shot of elements 1, 2 "
                    "and 3")
    prompt.pack(fill="x", pady=3)
    note(body, "Describe a video in one plain-English sentence and "
               "this drafts a rough version of it — no scripting "
               "required. It understands how many scenes and shots "
               "you asked for, camera-lens words (close up / macro / "
               "wide / ultra wide), and phrases like 'elements 1, 2 "
               "and 3' to decide what the camera looks at (list those "
               "object names in the Focus objects field below).")
    environment = LabeledEntry(
        body, "Environment prompt (for brief)", "",
        placeholder="e.g. on a beach at a lake in the desert")
    environment.pack(fill="x", pady=3)
    note(body, "Only used together with the brief above — sets the "
               "backdrop. Understood words include beach, desert, "
               "snow, tropical, tsunami, tornado, storm, forest, "
               "mountains, night, dusk, and fog, in any combination.")
    focus = LabeledEntry(
        body, "Focus objects (comma list, for brief)", "",
        placeholder="e.g. dome, plenum, blower")
    focus.pack(fill="x", pady=3)
    note(body, "Only used together with the brief above — the object "
               "names that 'elements 1, 2, 3...' in the brief refer "
               "to, in that order.")

    section(body, "Output")
    action = LabeledCombo(body, "Action",
                          ["run", "shots", "export", "selftest"], "run")
    action.pack(fill="x", pady=3)
    note(body, "run = play the video live in a window (the default — "
               "use this to just watch something). shots = save still "
               "frames at chosen moments instead of a video. export = "
               "render the complete narrated video to the MP4 path "
               "below (takes several minutes; the log pane at the "
               "bottom of this window shows progress). selftest = run "
               "this tool's internal checks and print the result — "
               "for troubleshooting, not for watching.")
    export_path = PathRow(body, "Export MP4 path (action = export)",
                          "presenter_output/presentation.mp4", mode="save",
                          filetypes=(("MP4 video", "*.mp4"),))
    export_path.pack(fill="x", pady=3)
    stills = LabeledEntry(
        body, "Still times (action = shots)", "4,40,90",
        placeholder="e.g. 4,40,90")
    stills.pack(fill="x", pady=3)
    note(body, "Seconds into the video to capture, separated by "
               "commas. The example saves three PNG images: one at 4 "
               "seconds in, one at 40, one at 90.")
    save_json = PathRow(body, "Save as JSON and exit (optional)", "",
                        mode="save", filetypes=(("JSON", "*.json"),),
                        placeholder="e.g. presenter_output/my_script.json")
    save_json.pack(fill="x", pady=3)
    note(body, "Optional, any Action: also write the built scene/shot "
               "structure to this file so you can hand-edit it or "
               "reload it later with the script field above.")
    no_narration = CheckRow(body, "No narration (silent export)", False)
    no_narration.pack(anchor="w", pady=3)
    fullscreen = CheckRow(body, "Fullscreen (live run)", False)
    fullscreen.pack(anchor="w")
    note(body, "Fullscreen only matters when Action = run.")
    fps = LabeledEntry(body, "FPS (export)", "30")
    fps.pack(fill="x", pady=3)
    size = LabeledEntry(body, "Size WxH", "1600x900")
    size.pack(fill="x", pady=3)
    note(body, "Size is WIDTH x HEIGHT in pixels, e.g. 1600x900. "
               "Larger sizes look sharper but take longer to export.")

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
    ttk.Separator(ps_footer).pack(fill="x")
    launch_button(ps_footer, "Launch Presenter Studio", go_presenter)

    # ---- 2V Masterclass ---------------------------------------------------

    t, body, mc_footer = scrollable_tab("2V Masterclass")
    intro(body,
         "A self-contained, 14-chapter geometry lesson that builds a "
         "2V geodesic dome on screen from first principles — why two "
         "strut lengths, why triangles, and why the golden ratio is a "
         "myth, with the actual math shown at every step. Use this "
         "tab to watch the lesson, export it as a narrated video, or "
         "export real cut-list/CAD files for physically building a "
         "dome. Everything below used to be a command-line flag; pick "
         "an Action first, since it decides which other fields "
         "actually matter.")

    section(body, "Action")
    mc_action = LabeledCombo(
        body, "Action",
        ["run", "selftest", "report", "shots", "export_video",
         "voice_preview", "list_voices", "narration_only", "script",
         "build_packet"], "run")
    mc_action.pack(fill="x", pady=3)
    note(body, "run = watch the interactive lesson live (the "
               "default). selftest = internal checks, printed to the "
               "log below. report = print a plain-text audit of every "
               "calculation (strut lengths, ratios) with no window. "
               "shots = save still images at chosen moments. "
               "export_video = render the complete narrated lesson to "
               "an MP4 (several minutes; progress shows in the log). "
               "voice_preview = generate a short MP3 sample of the "
               "chosen voice, to audition it before a full export. "
               "list_voices = print every available narration voice "
               "to the log. narration_only = generate just the audio "
               "track, no video. script = write the narration text "
               "plus a subtitle file, no audio or video. "
               "build_packet = export real-world build files for "
               "physically constructing a dome (cut list, hub "
               "coordinates, CAD file, field guide) — no window.")
    mc_fullscreen = CheckRow(body, "Fullscreen (live run)", False)
    mc_fullscreen.pack(anchor="w")
    note(body, "Only matters when Action = run.")
    mc_size = LabeledEntry(body, "Size WxH", "1600x900")
    mc_size.pack(fill="x", pady=3)
    mc_fps = LabeledEntry(body, "FPS (export)", "30")
    mc_fps.pack(fill="x", pady=3)
    note(body, "Size is WIDTH x HEIGHT in pixels; FPS is frames per "
               "second for exported video. Both only matter when "
               "actually rendering (run / export_video / shots).")

    section(body, "Stills / video export")
    mc_shots = LabeledEntry(body, "Still times (action = shots)", "",
                            placeholder="e.g. 0,45,95")
    mc_shots.pack(fill="x", pady=3)
    note(body, "Seconds into the lesson to capture, comma-separated.")
    mc_export = PathRow(body, "Export MP4 (action = export_video)", "",
                        mode="save", filetypes=(("MP4 video", "*.mp4"),),
                        placeholder="e.g. two_v_demo_output/lesson.mp4")
    mc_export.pack(fill="x", pady=3)
    mc_no_narration = CheckRow(body, "No narration (silent export)", False)
    mc_no_narration.pack(anchor="w")
    mc_local_plan = PathRow(
        body, "Local Voice Studio narration plan (optional)", "",
        mode="open", filetypes=(("JSON", "*.json"),),
        placeholder="e.g. MyVoice/outputs/dome/narration-plan.json")
    mc_local_plan.pack(fill="x", pady=3)
    note(body, "Optional: point this at a narration-plan.json built "
               "by the Local Voice Studio tab's Dome Narration step to "
               "use your own recorded/cloned voice instead of the "
               "cloud voice below. Leave blank to use the cloud voice.")

    section(body, "Voice (cloud narration — ignored if a Local Voice "
                 "Studio plan is set above)")
    mc_voice = LabeledEntry(body, "Voice", "en-US-AndrewMultilingualNeural")
    mc_voice.pack(fill="x", pady=3)
    note(body, "A Microsoft Edge neural voice name. Use Action = "
               "list_voices to print every available name and locale "
               "to the log below, then paste one here.")
    mc_rate = LabeledEntry(body, "Rate", "-3%")
    mc_rate.pack(fill="x", pady=3)
    mc_pitch = LabeledEntry(body, "Pitch", "-2Hz")
    mc_pitch.pack(fill="x", pady=3)
    mc_volume = LabeledEntry(body, "Volume", "+0%")
    mc_volume.pack(fill="x", pady=3)
    note(body, "Rate and Volume are percentages, e.g. -10% or +5%; "
               "Pitch is in Hz, e.g. -2Hz or +3Hz. Negative "
               "slows/lowers, positive speeds up/raises. The defaults "
               "give a relaxed, natural-sounding narrator.")
    mc_locale = LabeledEntry(body, "Voice locale (list_voices)", "en-US")
    mc_locale.pack(fill="x", pady=3)
    note(body, "Only used with Action = list_voices, to filter the "
               "printed list to one language/region, e.g. en-US, "
               "en-GB, es-ES.")
    mc_voice_preview = PathRow(
        body, "Voice preview MP3 (action = voice_preview)", "",
        mode="save", filetypes=(("MP3 audio", "*.mp3"),),
        placeholder="e.g. two_v_demo_output/voice-preview.mp3")
    mc_voice_preview.pack(fill="x", pady=3)
    mc_narration_only = PathRow(
        body, "Narration-only M4A (action = narration_only)", "",
        mode="save", filetypes=(("M4A audio", "*.m4a"),),
        placeholder="e.g. two_v_demo_output/narration.m4a")
    mc_narration_only.pack(fill="x", pady=3)

    section(body, "Export helpers")
    note(body, "Leave both blank unless ffmpeg is not already "
               "installed on this computer's PATH — that's the normal "
               "case and these two fields are rarely needed.")
    mc_ffmpeg = PathRow(body, "ffmpeg path (blank = on PATH)", "",
                        mode="open",
                        placeholder="e.g. C:\\ffmpeg\\bin\\ffmpeg.exe")
    mc_ffmpeg.pack(fill="x", pady=3)
    mc_ffprobe = PathRow(body, "ffprobe path (blank = beside ffmpeg)", "",
                        mode="open",
                        placeholder="e.g. C:\\ffmpeg\\bin\\ffprobe.exe")
    mc_ffprobe.pack(fill="x", pady=3)
    mc_script = PathRow(body, "Narration script + SRT (action = script)",
                        "", mode="save", filetypes=(("Markdown", "*.md"),),
                        placeholder="e.g. two_v_demo_output/script.md")
    mc_script.pack(fill="x", pady=3)

    section(body, "Build packet (action = build_packet) — files for "
                 "physically building a real dome")
    mc_packet = PathRow(body, "Output directory", "", mode="dir",
                        placeholder="e.g. two_v_demo_output/build_packet")
    mc_packet.pack(fill="x", pady=3)
    note(body, "Writes a cut-list CSV (every strut, its length, and "
               "how many to cut), hub coordinates, a calculation "
               "workbook, an inch-unit CAD file (.obj), a JSON "
               "manifest, and a printable field guide — everything "
               "needed to actually build the dome this lesson "
               "describes.")
    mc_radius = LabeledEntry(body, "Radius (inches, blank = fit)", "",
                             placeholder="e.g. 60")
    mc_radius.pack(fill="x", pady=3)
    note(body, "The real-world radius of the dome to cut parts for, "
               "in inches. Leave blank to use the lesson's own "
               "example measurements instead of a specific size.")
    mc_deduction = LabeledEntry(body, "Connector deduction (inches)", "0.0",
                                placeholder="e.g. 0.75")
    mc_deduction.pack(fill="x", pady=3)
    note(body, "How much shorter to cut each strut to allow for the "
               "hub connectors you're using — measure this on your "
               "actual hardware. 0.0 means hub-center-to-hub-center "
               "lengths with no adjustment.")

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

    t, body, foot = scrollable_tab("Local Voice Studio")
    intro(body,
         "Record your own voice (or import audio you already own), "
         "turn it into a private, locked voice profile, and generate "
         "narration locally — nothing is sent to a cloud text-to-"
         "speech service, and no login is required. This is what the "
         "2V Masterclass and Presenter Studio tabs use for narration "
         "when you want your own voice instead of the built-in cloud "
         "one. It has its own full window once launched, with a "
         "left-to-right workflow across its tabs: Project (create one "
         "and confirm you own the voice) -> Record or Import & Segment "
         "(get clean audio in) -> Dataset (accept/transcribe clips) -> "
         "Voice Profile (lock in a reusable voice from ~15+ seconds "
         "of accepted clips) -> Synthesize (generate speech to test "
         "it) -> Dome Narration (generate a full narration set for "
         "the 2V lesson). Fine-tune and Logs are optional/advanced.")
    section(body, "Launch")
    lvs_action = LabeledCombo(body, "Action",
                              ["run", "selftest", "diagnose"], "run")
    lvs_action.pack(fill="x", pady=3)
    note(body, "run = open the studio (the default). selftest = "
               "internal checks, printed to the log below, no window. "
               "diagnose = print what hardware/local-AI backends are "
               "available on this computer — useful if something "
               "seems unavailable once the studio is open.")
    lvs_project = PathRow(body, "Project folder (optional)", "",
                          mode="dir",
                          placeholder="e.g. C:\\Users\\you\\MyVoice")
    lvs_project.pack(fill="x", pady=3)
    note(body, "Optional: open a specific existing project folder "
               "directly instead of choosing one from inside the "
               "studio after it opens.")

    def go_voice_studio():
        cfg = {"action": lvs_action.get()}
        if lvs_project.get():
            cfg["project"] = lvs_project.get()
        run("local_voice_studio.py", "local_voice_studio", cfg,
            "Local Voice Studio")
    ttk.Separator(foot).pack(fill="x")
    launch_button(foot, "Launch Local Voice Studio", go_voice_studio)

    # ---- Flatten utility ----------------------------------------------

    t, body, foot = scrollable_tab("Flatten Utility")
    intro(body,
         "A convenience tool for developers, not something most "
         "non-coders will need. It combines every source file in this "
         "project into one plain-text file with a table of contents, "
         "so the whole codebase can be pasted into or uploaded to an "
         "AI assistant in one go, for questions or changes. Running it "
         "does not change or affect any of the tools above.")
    section(body, "Output")
    flatten_out = PathRow(body, "Output file", "dome_flat.md", mode="save",
                          filetypes=(("Markdown", "*.md"),
                                    ("Text", "*.txt")),
                          placeholder="e.g. dome_flat.md")
    flatten_out.pack(fill="x", pady=3)
    note(body, "Where to write the combined file. Markdown (.md) is "
               "the normal choice; .txt works identically.")

    def go_flatten():
        cfg = {}
        if flatten_out.get():
            cfg["output"] = flatten_out.get()
        run("flatten.py", "flatten", cfg, "Flatten Utility")
    ttk.Separator(foot).pack(fill="x")
    launch_button(foot, "Run Flatten", go_flatten)

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
