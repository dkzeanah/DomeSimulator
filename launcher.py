"""DomeSim Launcher — one GUI for every standalone tool in this project.

Dome Creator, Assembly Line (and its earlier Simple variant), Presenter
Studio, the Masterclass lessons, Local Voice Studio, and the project
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
import render_presets

ROOT = Path(__file__).resolve().parent


def main() -> int:
    w = lc.build_widgets()
    tk, ttk = w["tk"], w["ttk"]
    LabeledEntry, LabeledCombo = w["LabeledEntry"], w["LabeledCombo"]
    CheckRow, PathRow = w["CheckRow"], w["PathRow"]
    add_tooltip = w["add_tooltip"]

    root = tk.Tk()
    root.title("DomeSim Launcher")
    root.geometry("1040x760")
    root.minsize(860, 620)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # The clam theme's background is a light warm grey (#dcdad5); the
    # muted blue-greys tried earlier read as washed-out against it.
    # Named styles here use genuinely dark, high-contrast foregrounds —
    # Intro gets a distinct tinted callout background so each tab's
    # opening description reads as one clear block; Note stays on the
    # normal background since it's threaded between form fields.
    INTRO_BG, INTRO_FG = "#d7e3ea", "#12242f"
    NOTE_FG = "#33404a"
    LIVE_FG = "#0d2b12"
    LIVE_BG = "#d9e8da"
    style.configure("Intro.TLabel", background=INTRO_BG,
                    foreground=INTRO_FG, font=("Segoe UI", 10),
                    padding=(10, 8))
    style.configure("Note.TLabel", foreground=NOTE_FG,
                    font=("Segoe UI", 9))
    style.configure("Live.TLabel", background=LIVE_BG, foreground=LIVE_FG,
                    font=("Segoe UI", 9, "bold"), padding=(8, 6))

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
        foreground=NOTE_FG).pack(anchor="w", padx=12, pady=(0, 8))

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
        append_log(f"    interpreter = {lc.python_for(tool)}")
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
        that belongs at the top of every tab, before any fields. Shown
        as a distinct tinted callout so it reads as one clear block."""
        ttk.Label(parent, text=text, wraplength=730, justify="left",
                 style="Intro.TLabel").pack(anchor="w", fill="x",
                                            pady=(0, 10))

    def section(parent, text):
        ttk.Label(parent, text=text, font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(10, 3))

    def note(parent, text):
        """Small explanatory text under a field or group of fields —
        format examples, which fields matter only for which Action.
        Never load-bearing, only clarifying, so it always wraps and
        never fights for space."""
        ttk.Label(parent, text=text, wraplength=740, justify="left",
                 style="Note.TLabel").pack(anchor="w", pady=(0, 6))

    def action_help(parent, combo, help_map: dict):
        """Wire a dropdown to a live one-line explanation of whatever
        is CURRENTLY selected, plus a hover tooltip on the dropdown
        listing every option with its own explanation.

        Fixes a real bug: a single static block of text describing
        every option at once still reads as correct no matter what is
        selected, which looks exactly like the explanation not
        updating at all when you change the dropdown. This makes the
        visible text track the actual selection, and moves the full
        reference listing into a tooltip instead of permanently
        occupying space for options you didn't pick.

        ``help_map`` is ``{value: one-line explanation}``, in the same
        order as the dropdown's own values (that order is what the
        tooltip listing uses)."""
        live = ttk.Label(parent, wraplength=730, justify="left",
                         style="Live.TLabel")
        live.pack(anchor="w", fill="x", pady=(2, 8))

        def refresh(*_a):
            value = combo.get()
            text = help_map.get(value, "(no description for this value)")
            live.configure(text=f"{value or '(blank)'} — {text}")
        combo.var.trace_add("write", refresh)
        refresh()

        listing = "\n\n".join(
            f"{value or '(blank)'} — {text}"
            for value, text in help_map.items())
        add_tooltip(combo.widget, "Every option:\n\n" + listing)

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

    # ---- Dome Forge -------------------------------------------------------

    t, body, foot = scrollable_tab("Dome Forge")
    intro(body,
         "A single dome, built up out of layers — the way an image is "
         "built up out of layers in a paint program. Every part is its "
         "own layer you can hide, fade with a slider, reorder, "
         "duplicate, delete, and tune with its own named controls: the "
         "strut frame, the hubs, the panels, liners and insulation, and "
         "the water-harvesting parts. Unlike the Dome Creator tab, "
         "there is no site and no factory here — just one dome you can "
         "study from every angle, like a character creator aimed at a "
         "building.\n\n"
         "It opens with the rain-capture idea already switched on: "
         "panels dished inward like golf-ball dimples so rain runs to a "
         "low point instead of sheeting off the seams, a micro-drain at "
         "each of those low points, and a network of veins running "
         "along the inside of every seam — held clear of the outer skin "
         "by a deliberate gap — that carries water down to a collector "
         "ring, through a downpipe, into a cistern under the dome. Turn "
         "on Cutaway view (or press C) to watch the water actually move "
         "through it.")
    note(body, "The frame is built the hubless way: 40 separate "
               "triangles, each three boards mitered at the corners and "
               "bolted to its neighbours, so every seam ends up two "
               "boards thick and there are no hub connectors anywhere.")
    note(body, "Click any triangle in the 3D view to select it, then "
               "change what that one triangle is made of — its fill "
               "(window, vent, solar panel, mirror, Fresnel lens, "
               "shingles, planks, stone, fabric, an AC unit, a door, and "
               "more) and the strut on each of its three edges "
               "separately. The three edges do not have to match, which "
               "is how real split-log builds actually go together.")
    note(body, "Press [m] for GROUPS — edit whole sub-assemblies instead "
               "of single triangles. A pentagon is the five triangles "
               "ringing a five-way vertex (six per dome); an hourglass "
               "is two equilateral triangles touching at exactly one "
               "point, waist in the middle (ten per dome), filling the "
               "gaps between the pentagons. Tab swaps between the two, "
               "arrows step through them, and the selected group lights "
               "up. For hourglasses you also choose how the two points "
               "are actually joined: metal banding, square wooden "
               "braces bridging the sides that form the points, a "
               "monolithic single-piece waist, a steel gusset plate, or "
               "a bolted lap.")
    note(body, "Press [m] again for COVER PATTERNS — flatten the curved "
               "dome into cuttable shapes for a fabric, poly, or "
               "fiberglass cover, the way a sailmaker or stitch-and-glue "
               "boatbuilder develops a curved surface. Pick a shape "
               "(single/double/triple triangle, a whole pentagon, a "
               "hexagon), set your dome's long strut and your sheet size "
               "(e.g. 25 x 10 ft), and it lays the flat pattern on the "
               "sheet to scale with real dimensions, fold lines, the "
               "wrap/seam slack, and the dart that pulls a pentagon up "
               "into the dome's curve. It is a nesting layout, not a "
               "single view: add several pieces onto the material, drag "
               "them around, or Auto-arrange to pack them onto as many "
               "sheets as needed. A whole pentagon that won't fit your "
               "sheet ships as a 3-piece + 2-piece split that nests side "
               "by side, so you can maximize a roll and split coverage "
               "across two pieces on purpose. Save each sheet as an "
               "image to print or take to the shop.")
    note(body, "Press [m] again for the PANEL CREATOR — design one panel "
               "on a bench out of any three struts from the library "
               "(split logs, 2x2/2x4/2x6, PVC, steel and aluminium tube, "
               "square tube and angle, bamboo, plastic) plus any fill, "
               "then push it to the selected triangle or to the whole "
               "dome.")
    note(body, "Press [m] for the JIG SHOP — a second world that walks "
               "through building the two jigs you need to mass-produce "
               "those triangles (only two shapes exist: 10 equilateral "
               "and 30 isosceles). Nine steps, each with the exact cut "
               "list: board lengths, the miter angle for each corner, "
               "the bevel to rip along each edge, and why the mitered "
               "tips do not meet flat at a vertex. Every number follows "
               "the dome radius you set.")
    note(body, "Mouse: drag to orbit, scroll to zoom. Click any layer to "
               "select it, click its small square to hide/show it, drag "
               "the bar under its name to fade it. Keys: [m] switch "
               "between the dome and the jig shop, [space] pause/play "
               "the water, [c] cutaway, [1-4] jump to preset views "
               "(outside / inside / top-down / ground level), [s] save "
               "your dome, [l] load it back, [Escape] quit. In the jig "
               "shop: [left]/[right] step through the build, [Tab] "
               "switch between the two jigs.")
    section(body, "Launch")
    df_action = LabeledCombo(body, "Action",
                             ["run", "selftest", "shots"], "run")
    df_action.pack(fill="x", pady=3)
    action_help(body, df_action, {
        "run": "open the dome builder (the default).",
        "selftest": "internal checks, printed to the log below, no "
                    "window — confirms the dome geometry and every "
                    "layer type still build correctly.",
        "shots": "render four still images of the current dome "
                 "(outside, cutaway, top-down, ground level) to a "
                 "folder without opening a window — handy for putting "
                 "the design in a document.",
    })
    df_start = LabeledCombo(body, "Starting dome",
                            ["default", "splitlog"], "default")
    df_start.pack(fill="x", pady=3)
    action_help(body, df_start, {
        "default": "the water-harvesting dome: dished panels, seam "
                   "veins, cistern, framed in 2x4.",
        "splitlog": "a split-log frame — half-round logs on the long "
                    "seams, quarter-round on the short ones, and 2x2 "
                    "on the ten equilateral caps. A trunk halved gives "
                    "two half-rounds; halving those again gives four "
                    "quarter-rounds per log.",
    })
    df_preset = PathRow(body, "Dome preset (optional)", "", mode="open",
                        filetypes=(("Dome Forge preset", "*.json"),
                                   ("All files", "*.*")),
                        placeholder="e.g. my-dome.json (saved with [s])")
    df_preset.pack(fill="x", pady=3)
    note(body, "Optional: reopen a dome you saved earlier. Leave it "
               "empty to start from the built-in water-harvesting dome.")
    df_size = LabeledEntry(body, "Window size", "1600x900",
                           placeholder="1600x900")
    df_size.pack(fill="x", pady=3)
    df_shotdir = PathRow(body, "Image folder", "dome_forge_shots", mode="dir",
                         placeholder="dome_forge_shots")
    df_shotdir.pack(fill="x", pady=3)
    note(body, "Only used by the 'shots' action — where to write the "
               "four still images.")
    df_full = CheckRow(body, "Open fullscreen", False)
    df_full.pack(fill="x", pady=3)

    def go_dome_forge():
        cfg = {"action": df_action.get(), "size": df_size.get() or "1600x900",
               "fullscreen": df_full.get(), "start": df_start.get()}
        if df_preset.get():
            cfg["preset"] = df_preset.get()
        if df_shotdir.get():
            cfg["shot_dir"] = df_shotdir.get()
        run("dome_forge.py", "dome_forge", cfg, "Dome Forge")
    ttk.Separator(foot).pack(fill="x")
    launch_button(foot, "Launch Dome Forge", go_dome_forge)

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
        action_help(body, action, {
            "run": "open the live simulation (the default).",
            "selftest": "run this tool's internal checks and print "
                        "the result — for troubleshooting, not for "
                        "watching.",
            "shots": "save still images at chosen moments instead of "
                     "opening a window (see below).",
        })
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
            action_help(body, panel, {
                "": "whatever the simulation last had open — pick one "
                    "below to choose explicitly.",
                "pnl": "live profit and loss for the dome currently "
                       "on the line.",
                "throughput": "production rate and which station is "
                              "the bottleneck.",
                "bom": "full bill of materials and cost breakdown.",
                "benchmark": "box vs dome cost comparison, bare-shed "
                            "and finished-home tiers.",
                "value": "the finished dome's off-grid story — "
                        "solar, battery, insulation, embodied "
                        "carbon.",
                "scale": "what running 1, 3, or 6 production lines "
                        "looks like, plus break-even.",
                "ledger": "cumulative production and sales history.",
            })
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
         "Presenter Studio makes narrated 3-D explainer videos. It has "
         "a built-in movie maker — the Scene Composer — where you "
         "build a film from nothing: a timeline you drag shots around "
         "on, a library of domes, doors, wood stoves, tanks, batteries "
         "and appliances you drop onto a stage, camera controls, and "
         "boxes to type what gets said out loud. It renders the "
         "finished video itself. Every argument video for 2V dome "
         "housing shipped with this project (see 'Built-in demo' "
         "below) was made this way, and every number those videos show "
         "comes from this project's own cost and geometry code, not "
         "typed in by hand.")
    note(body, "To make something of your own, set Action (further "
               "down) to 'compose', leave all three Source boxes "
               "empty, and click Launch. That opens the Scene "
               "Composer on an empty movie.")

    section(body, "Source — fill in at most one of these three")
    note(body, "Leave all three empty to start a brand-new movie in the "
               "Scene Composer. Fill in exactly one to open or watch "
               "something that already exists: the easiest is to pick a "
               "built-in demo, which alone is enough to click Launch.")
    demo = LabeledCombo(body, "Built-in demo",
                        ["", "airflow", "housing_case", "accessibility",
                         "case_manufacturing", "case_bare_shell",
                         "case_more_room", "case_triangles",
                         "case_benchmark", "case_energy",
                         "case_resilience", "case_financing",
                         "case_utility_core", "case_market_fit"],
                        "")
    demo.pack(fill="x", pady=3)
    action_help(body, demo, {
        "": "nothing selected. With Action = compose that starts a "
            "brand-new empty movie, which is what you want when "
            "making your own. With Action = run it plays the airflow "
            "demo.",
        "airflow": "The Dome That Breathes: a perimeter-plenum "
                  "ventilation system, one leaf blower holding a "
                  "whole dome at negative pressure.",
        "housing_case": "The full pro-dome argument for 2V housing, "
                        "in one video.",
        "accessibility": "A Home That Meets You Halfway: why a single-"
                         "level dome suits wheelchair users and anyone "
                         "with limited mobility — a wheelchair rolls up "
                         "the ramp, turns in place, and tours the open "
                         "floor.",
        "case_manufacturing": "Argument 1/10: the standardized-"
                              "product/manufacturing case.",
        "case_bare_shell": "Argument 2/10: the bare-shell cost "
                           "comparison (shed tier).",
        "case_more_room": "Argument 3/10: the finished-home "
                          "comparison — a small honest price gap, a "
                          "real volume win.",
        "case_triangles": "Argument 4/10: the structural-rigidity "
                          "case, built from a first-principles "
                          "count.",
        "case_benchmark": "Argument 5/10: vs. a conventional "
                          "manufactured home, plus factory "
                          "throughput/break-even.",
        "case_energy": "Argument 6/10: the hedged off-grid/solar "
                       "energy case.",
        "case_resilience": "Argument 7/10: the hedged wind/seismic "
                           "structural case.",
        "case_financing": "Argument 8/10: real financing math "
                          "across every product tier.",
        "case_utility_core": "Argument 9/10: the curved-wall "
                             "objection and how it's solved.",
        "case_market_fit": "Argument 10/10: honest market fit — "
                           "where this is, and isn't, the right "
                           "product.",
    })
    script_path = PathRow(body, "...or a presentation script", "",
                          mode="open",
                          filetypes=(("Presentation", "*.json *.py"),
                                     ("All files", "*.*")),
                          placeholder="e.g. deliverables/presenter/my_script.json")
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
                          ["compose", "run", "shots", "export",
                           "export_all", "selftest"], "compose")
    action.pack(fill="x", pady=3)
    action_help(body, action, {
        "compose": "open the Scene Composer and build a movie yourself: "
                   "a timeline you drag clips on, a library of domes, "
                   "doors, stoves and appliances to drop on stage, and "
                   "boxes to type the narration into. Leave all three "
                   "Source boxes above empty to start from nothing, or "
                   "pick one to open it for editing.",
        "run": "play a finished video live in a window (use this to "
               "just watch something).",
        "shots": "save still frames at chosen moments instead of a "
                 "video.",
        "export": "render one complete narrated video to the MP4 "
                  "path below (takes several minutes; the log pane "
                  "at the bottom of this window shows progress).",
        "export_all": "render EVERY built-in demo to its own MP4 in the "
                      "folder below, one after another. This takes a "
                      "long time — thirteen videos — so start it when "
                      "you do not need the machine.",
        "selftest": "run this tool's internal checks and print the "
                    "result — for troubleshooting, not for "
                    "watching.",
    })
    overlay = LabeledCombo(body, "Writing on the picture",
                           ["full", "no_captions", "titles_only", "clean"],
                           "full")
    overlay.pack(fill="x", pady=3)
    action_help(body, overlay, {
        "full": "title, the spoken lines as captions, the info panel "
                "and a progress bar — the finished-explainer look.",
        "no_captions": "everything EXCEPT the spoken lines written "
                       "across the bottom. Use this when you do not "
                       "want the words people are hearing also printed "
                       "on screen.",
        "titles_only": "just the title and the progress bar. No "
                       "captions, no info panel.",
        "clean": "nothing written on the picture at all — only the 3-D "
                 "scene. Best if you plan to add your own titles in "
                 "another editor.",
    })
    note(body, "The voiceover is spoken either way, and a matching "
               ".srt subtitle file is always saved next to the video, "
               "so a caption-free video can still be subtitled later.")
    export_path = PathRow(body, "Export MP4 path (action = export)",
                          "deliverables/presenter/presentation.mp4", mode="save",
                          filetypes=(("MP4 video", "*.mp4"),))
    export_path.pack(fill="x", pady=3)
    export_dir = PathRow(body, "Folder for all videos "
                               "(action = export_all)",
                         "deliverables/presenter/all", mode="dir")
    export_dir.pack(fill="x", pady=3)
    note(body, "Each built-in demo is saved in here under its own name, "
               "e.g. case_energy.mp4.")
    only_demos = LabeledEntry(
        body, "...only these demos (optional, comma list)", "",
        placeholder="e.g. airflow, case_energy")
    only_demos.pack(fill="x", pady=3)
    note(body, "Leave empty to render all thirteen. Use the same names "
               "listed in the 'Built-in demo' box above.")
    stills = LabeledEntry(
        body, "Still times (action = shots)", "4,40,90",
        placeholder="e.g. 4,40,90")
    stills.pack(fill="x", pady=3)
    note(body, "Seconds into the video to capture, separated by "
               "commas. The example saves three PNG images: one at 4 "
               "seconds in, one at 40, one at 90.")
    save_json = PathRow(body, "Save as JSON and exit (optional)", "",
                        mode="save", filetypes=(("JSON", "*.json"),),
                        placeholder="e.g. deliverables/presenter/my_script.json")
    save_json.pack(fill="x", pady=3)
    note(body, "Optional, any Action: also write the built scene/shot "
               "structure to this file so you can hand-edit it or "
               "reload it later with the script field above.")
    no_narration = CheckRow(body, "No narration (silent export)", False)
    no_narration.pack(anchor="w", pady=3)
    fullscreen = CheckRow(body, "Start full screen (compose & run)", True)
    fullscreen.pack(anchor="w")
    note(body, "On for Action = compose (the Scene Composer opens full "
               "screen; press F11 inside it, or its top-bar button, to "
               "drop to a resizable window) and Action = run. Ignored by "
               "the headless actions (shots / export / export_all).")
    fps = LabeledEntry(body, "FPS (export)", "30")
    fps.pack(fill="x", pady=3)
    size = LabeledEntry(body, "Size WxH", "1600x900")
    size.pack(fill="x", pady=3)
    note(body, "Size is WIDTH x HEIGHT in pixels, e.g. 1600x900. "
               "Larger sizes look sharper but take longer to export.")

    def go_presenter():
        cfg = {"action": action.get(), "no_narration": no_narration.get(),
              "fullscreen": fullscreen.get(), "size": size.get(),
              "overlay": overlay.get()}
        if export_dir.get():
            cfg["export_dir"] = export_dir.get()
        if only_demos.get():
            cfg["demos"] = only_demos.get()
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

    # ---- Masterclass lessons ----------------------------------------------

    t, body, mc_footer = scrollable_tab("Masterclass")
    intro(body,
         "Five self-contained teaching lessons that build a dome on "
         "screen from first principles, with the actual math shown at "
         "every step. Pick a Lesson, then an Action. Use this tab to "
         "watch a lesson live, export it as a narrated video, or "
         "export real cut-list/CAD files for physically building a "
         "dome. Everything below used to be a command-line flag; the "
         "Action decides which other fields actually matter.")

    # The preset row is built last, once every field it fills in
    # exists, but it belongs at the very top of the tab -- so its place
    # in the layout is reserved here.
    mc_preset_holder = ttk.Frame(body)
    mc_preset_holder.pack(fill="x")

    section(body, "Lesson")
    mc_lesson = LabeledCombo(
        body, "Lesson",
        ["2v", "build", "hex", "zome", "line", "cuts", "franken",
         "hype", "hype2", "hype3", "hype4", "hype5", "hype6",
         "kick", "kick2", "master", "world", "world_chatgpt",
         "scratch", "wedge", "drama", "series"],
        "2v")
    mc_lesson.pack(fill="x", pady=3)
    action_help(body, mc_lesson, {
        "2v": "the original 14-chapter geometry lesson: why a 2V "
              "geodesic dome has exactly two strut lengths, and why "
              "their ratio is not the golden ratio.",
        "build": "46 chapters, start to finish: the same geometry, "
                 "then sizing, hub systems, end cuts, bevels, stock "
                 "and offcut, jigs, setting out, foundations, "
                 "raising, checking, skinning and openings, then "
                 "hubless framing and its compound cuts, the shell "
                 "used as a filter, the one-sheet micro shelter and "
                 "the mixed-stock franken-dome.",
        "hex": "20 chapters on hexagonal domes: the one-hexagon "
               "frame dome you can cut from a single strut length, "
               "why every hexagon cage needs exactly twelve "
               "pentagons, and what raising the frequency costs in "
               "extra sizes and warped panels.",
        "zome": "19 chapters on zomes: rooms swept from a star of "
                "directions, built from parallelograms, framed from "
                "one strut length, and closing on a point at the top.",
        "cuts": "18 chapters on the single hardest operation in a "
                "hubless dome: the compound cut. Both machines, the "
                "jig between them, every saw setting measured off the "
                "model, and the five ways it goes wrong.",
        "franken": "13 chapters on the mixed-stock dome: struts of "
                   "any section, V brackets folded from washing "
                   "machine casing, the slack that leaves no joint on "
                   "the sphere, and the settling that makes it stand.",
        "hype2": "the montage again, with the Teslabot and Psyche "
                 "asides spliced into the list of likes. Raw label "
                 "placement, exactly as it shipped.",
        "hype3": "the montage with the reason: why women specifically, "
                 "the single-parent years, Fuller's actual goal, and the "
                 "Inuit proof. Labels decluttered so overlapping text "
                 "stays readable.",
        "hype": "the Frankendome montage: not a lesson. Full-frame "
                "pictures, one line of type, a quicker voice, and the "
                "argument for treating a dome as a platform you keep "
                "upgrading rather than a house you finish once.",
        "hype4": "the montage with the brand segments, the party sting "
                 "and the shared contact outro spliced in.",
        "hype5": "the montage with the plain frankendome in place of the "
                 "party sting.",
        "hype6": "the montage, current version: themed shells, the four "
                 "product lines, a faster cadence and a beat under it.",
        "kick": "the campaign film: why a dome, what one costs to the "
                "dollar, and what a hundred thousand dollars buys.",
        "kick2": "the campaign film, current version: the overhanging "
                 "brim and its catchment, the pony wall, running cost, "
                 "radiative cooling paint and the ten points.",
        "master": "THE BIG ONE, 108 chapters and about 45 minutes: every "
                  "tool's 3D world, the whole construction masterclass, "
                  "the frankendome, the priced starter home and the "
                  "factory case — with 13 math screens that derive every "
                  "figure on camera and show the conclusion in plain "
                  "language.",
        "world": "all twelve Dome Creator presets, each rebuilt live from "
                 "the simulator's own modules and drawn at true relative "
                 "scale, with math screens for the frequency ladder, hub "
                 "versus hubless framing, price per square foot and "
                 "envelope efficiency.",
        "world_chatgpt": "the accountable master cut: ten real Dome "
                         "Creator presets with Dome Forge and Assembly "
                         "Line context, a per-build material breakdown, a "
                         "construction-event labor breakdown and a "
                         "modeled direct-sale price for each. The figures "
                         "are code-model outputs, not bids — site, "
                         "permits, freight, tax and local engineering sit "
                         "outside the model.",
        "series": "THE VANCE NETWORK: all six episodes of the "
                  "micro-drama back to back, 6.3 minutes. Each one is a "
                  "60-second vertical episode with a cold hook, an "
                  "escalation, a reveal and a cliffhanger the next "
                  "episode answers; the finale leaves one thread open. "
                  "Render at 1080x1920.",
        "drama": "EP_DOME_001, a 60-second vertical micro-drama shot "
                 "in the dome: four beats (cold hook, escalation, "
                 "reveal, cliffhanger), five archetype characters, and "
                 "a camera the script directs shot by shot. Render it "
                 "at 1080x1920 — the framing is computed for 9:16 and "
                 "a landscape frame throws it away.",
        "wedge": "29 chapters on building the dome straight from the "
                 "tree: raw 45-degree log sectors as structural members, "
                 "bark face outward and pith inward, forty independent "
                 "triangular frames whose three members pinwheel "
                 "end-to-side so every cut is a square crosscut, and "
                 "neighbouring panels that duplicate their edge member "
                 "and meet through a gasket rather than sharing or "
                 "shaving wood. Ten math screens derive the tree's "
                 "board feet, the packing, the kerf, the joint and the "
                 "dome the two trees size.",
        "scratch": "46 chapters answering one question end to end for "
                   "somebody who has never written code: what does a "
                   "computer actually calculate, from nothing, to put a "
                   "geodesic dome on a screen? The first half derives "
                   "the shape (one number, twelve points, subdivision, "
                   "projection, two strut lengths, a cut list). The "
                   "second half derives the picture (tubes, normals, "
                   "the vertex buffer, the camera, the view and "
                   "projection matrices, the divide by w, the viewport, "
                   "the depth buffer, culling, and the lighting sum). "
                   "18 math screens, every figure computed on camera.",
        "line": "24 chapters on the assembly line itself: an animated "
                "two-person crew walking, lifting, carrying and "
                "fastening every part of one dome, with the energy "
                "each motion costs them totalled per limb, per "
                "station and per shift.",
    })

    section(body, "Action")
    mc_action = LabeledCombo(
        body, "Action",
        ["run", "selftest", "report", "shots", "export_video",
         "voice_preview", "list_voices", "narration_only", "script",
         "build_packet", "list_lessons", "list_deliverables",
         "list_segments", "soundboard", "render_all"], "run")
    mc_action.pack(fill="x", pady=3)
    action_help(body, mc_action, {
        "run": "watch the interactive lesson live (the default).",
        "selftest": "internal checks, printed to the log below.",
        "report": "print a plain-text audit of every calculation "
                  "(strut lengths, ratios) with no window.",
        "shots": "save still images at chosen moments.",
        "export_video": "render the complete narrated lesson to an "
                        "MP4 (several minutes; progress shows in the "
                        "log).",
        "voice_preview": "generate a short MP3 sample of the chosen "
                         "voice, to audition it before a full "
                         "export.",
        "list_voices": "print every available narration voice to "
                       "the log.",
        "narration_only": "generate just the audio track, no "
                          "video.",
        "script": "write the narration text plus a subtitle file, "
                  "no audio or video.",
        "build_packet": "export real-world build files for "
                        "physically constructing a dome (cut list, "
                        "hub coordinates, CAD file, field guide) — "
                        "no window. Always the 2V dome, whichever "
                        "lesson is selected.",
        "list_segments": "print the reusable brand segments: what each "
                         "one is, where it inserts itself, whether it "
                         "is automatic, and what it plays.",
        "soundboard": "print the audio soundboard inventory by "
                      "category, and create the asset folders if they "
                      "do not exist yet. This repository ships no audio; "
                      "drop your own files into assets/audio/<category>/ "
                      "and they become available to segments as "
                      "category/name.",
        "list_deliverables": "print every video this repository "
                             "produces, which lesson makes it, and "
                             "whether its cached narration is present.",
        "render_all": "rebuild every deliverable in order, one at a "
                      "time. Skips anything already on disk unless "
                      "Force re-render is ticked. Sequential on "
                      "purpose: parallel exports make the speech "
                      "endpoint throttle and refuse connections.",
        "list_lessons": "print the available lessons and their "
                        "chapter counts to the log.",
    })
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
    section(body, "Auto-scene manager")
    mc_compose = CheckRow(
        body, "Auto-insert brand segments (outro, call to action)", False)
    mc_compose.pack(fill="x", pady=3)
    mc_seg_include = LabeledEntry(
        body, "Also insert (segment keys, comma-sep)", "")
    mc_seg_include.pack(fill="x", pady=3)
    mc_seg_exclude = LabeledEntry(
        body, "Never insert (segment keys, comma-sep)", "")
    mc_seg_exclude.pack(fill="x", pady=3)
    note(body, "Templated pieces that repeat across videos and do not "
               "change: the contact outro, the call to action, the "
               "who-am-I stack, and the Frankendome party sting. Ticking "
               "the box splices in everything marked auto; the two "
               "fields add or suppress individual ones. Run Action = "
               "list_segments to see the keys, what each does, and which "
               "soundboard cues it fires. Deliberately OFF by default: "
               "the nine videos already rendered were made before "
               "segments existed, and leaving it off is what lets them "
               "re-render byte-identical.")

    section(body, "Rebuild the whole set")
    mc_render_only = LabeledEntry(body, "Render only (lesson keys, comma-sep)", "")
    mc_render_only.pack(fill="x", pady=3)
    mc_force = CheckRow(body, "Force re-render (overwrite existing files)", False)
    mc_force.pack(fill="x", pady=3)
    note(body, "These two are for Action = render_all. Leave the filter "
               "empty to rebuild every deliverable in order. Files already "
               "on disk are skipped unless Force is ticked. Exact "
               "reproduction needs the *-voice-* cache directories: "
               "without them the narration is re-synthesized and chapter "
               "boundaries can shift by fractions of a second, which moves "
               "every frame after them. Run list_deliverables to see which "
               "caches you have.")

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

    # ---- Video presets: one click reproduces a published render -------
    #
    # Every published video is a specific combination of lesson, action,
    # resolution, voice and segments. Selecting a preset fills all of
    # them in, so reproducing a render needs no prior knowledge of which
    # combination made which file.
    mc_preset_fields = {
        "lesson": mc_lesson, "action": mc_action, "size": mc_size,
        "fps": mc_fps, "shots": mc_shots, "export_video": mc_export,
        "compose_segments": mc_compose,
        "segments_include": mc_seg_include,
        "segments_exclude": mc_seg_exclude,
        "voice": mc_voice, "voice_rate": mc_rate, "voice_pitch": mc_pitch,
        "voice_volume": mc_volume, "no_narration": mc_no_narration,
        "fullscreen": mc_fullscreen, "voice_preview": mc_voice_preview,
    }

    def set_field(widget, value):
        """Write a value into whichever kind of row this is."""
        if isinstance(value, bool):
            widget.var.set(value)
            return
        text = "" if value is None else str(value)
        if hasattr(widget, "set"):
            widget.set(text)
            return
        widget.var.set(text)
        # PathRow shows grey placeholder text until something is typed;
        # writing the variable directly would leave a real path looking
        # like an example.
        entry = getattr(widget, "_placeholder_entry", None)
        if entry is not None and text:
            entry.configure(foreground="")

    def apply_preset(*_args):
        preset = render_presets.PRESET_BY_LABEL.get(mc_preset.get())
        if preset is None or preset.key == "custom":
            return
        for name, value in preset.applied().items():
            widget = mc_preset_fields.get(name)
            if widget is not None:
                set_field(widget, value)

    ttk.Separator(mc_preset_holder).pack(fill="x", pady=(0, 6))
    section(mc_preset_holder, "Video preset — reproduce a published render")
    mc_preset = LabeledCombo(
        mc_preset_holder, "Video preset",
        render_presets.PRESET_LABELS, render_presets.PRESET_LABELS[0])
    mc_preset.pack(fill="x", pady=3)
    action_help(mc_preset_holder, mc_preset, {
        preset.label: preset.summary for preset in render_presets.PRESETS
    })
    note(mc_preset_holder,
         "Pick one and every field below fills in with the exact setup "
         "that produced that video — lesson, action, size, frame rate, "
         "narration voice, rate and segments. Then press Launch "
         "Masterclass and you get the same file. The voice settings are "
         "part of the render, not decoration: chapter lengths are "
         "measured off the synthesized speech, so changing a voice or a "
         "rate moves every chapter boundary after it. You can still edit "
         "anything after applying a preset — the fields are only filled "
         "in, never locked.")
    mc_preset.var.trace_add("write", apply_preset)
    ttk.Separator(mc_preset_holder).pack(fill="x", pady=(6, 2))

    def go_masterclass():
        cfg = {
            "action": mc_action.get(), "lesson": mc_lesson.get(),
            "fullscreen": mc_fullscreen.get(),
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
        cfg["compose_segments"] = mc_compose.get()
        if mc_seg_include.get():
            cfg["segments_include"] = mc_seg_include.get()
        if mc_seg_exclude.get():
            cfg["segments_exclude"] = mc_seg_exclude.get()
        if mc_render_only.get():
            cfg["render_only"] = mc_render_only.get()
        cfg["force_rerender"] = mc_force.get()
        run("two_v_masterclass.py", "two_v_masterclass", cfg,
            f"Masterclass ({mc_lesson.get()})")
    ttk.Separator(mc_footer).pack(fill="x")
    launch_button(mc_footer, "Launch Masterclass", go_masterclass)

    # ---- Local Voice Studio ------------------------------------------------

    t, body, foot = scrollable_tab("Local Voice Studio")
    intro(body,
         "Record your own voice (or import audio you already own), "
         "turn it into a private, locked voice profile, and generate "
         "narration locally — nothing is sent to a cloud text-to-"
         "speech service, and no login is required. This is what the "
         "Masterclass and Presenter Studio tabs use for narration "
         "when you want your own voice instead of the built-in cloud "
         "one. It has its own full window once launched, with a "
         "left-to-right workflow across its tabs: Project (create one "
         "and confirm you own the voice) -> Record or Import & Segment "
         "(get clean audio in) -> Dataset (accept/transcribe clips) -> "
         "Voice Profile (lock in a reusable voice from ~15+ seconds "
         "of accepted clips) -> Synthesize (generate speech to test "
         "it) -> Dome Narration (generate a full narration set for "
         "the 2V lesson). Fine-tune and Logs are optional/advanced. "
         "The studio's own Project tab explains this same workflow "
         "again once it is open, plus what to do if a step below "
         "says something is not ready.")
    note(body, "Recording, importing, dataset curation, and building a "
               "voice profile always work with no extra install. Only "
               "Synthesize and Dome Narration need the optional "
               "Chatterbox Turbo backend, and only Fine-tune needs F5 "
               "(most people never need Fine-tune). If this tool "
               "reports either backend as not ready, run this once "
               "from the project folder, then launch Local Voice "
               "Studio again — it uses that environment automatically "
               "from then on, no matter which Python started this "
               "launcher window:\n"
               "local_voice_studio/setup-windows.ps1 -WithLocalAI\n"
               "The Log panel below shows exactly which Python "
               "interpreter gets used each time you click Launch.")
    section(body, "Launch")
    lvs_action = LabeledCombo(body, "Action",
                              ["run", "selftest", "diagnose", "rap_analyze",
                               "rap_preview", "rap_produce", "rap_selftest"],
                              "run")
    lvs_action.pack(fill="x", pady=3)
    action_help(body, lvs_action, {
        "run": "open the studio (the default). Its Rap Studio tab does "
               "everything the rap_* actions below do, with sliders.",
        "selftest": "internal checks, printed to the log below, no "
                    "window.",
        "diagnose": "print hardware/local-AI backend status and, if "
                    "anything is not ready, the exact command to fix "
                    "it — to the log below, no window.",
        "rap_analyze": "measure the instrumental below: tempo, bar "
                       "lines, how steady it is, and what key it is "
                       "in. Needs only the Instrumental field.",
        "rap_preview": "measure how far off the beat and off the note "
                       "your vocal already is, without rendering "
                       "anything. Needs both audio fields.",
        "rap_produce": "the whole chain — snap the timing, tune the "
                       "vocal to the beat's key, mix, and write a "
                       "finished track into a new folder.",
        "rap_selftest": "check the beat/pitch/timing engines against "
                        "audio built to a known tempo and key.",
    })
    section(body, "Rap production (used by the rap_* actions only)")
    lvs_beat = PathRow(body, "Instrumental", "", mode="open",
                       filetypes=(("Audio", "*.wav *.mp3 *.flac *.m4a"),))
    lvs_beat.pack(fill="x", pady=3)
    lvs_vocal = PathRow(body, "Vocal take", "", mode="open",
                        filetypes=(("Audio", "*.wav *.mp3 *.flac *.m4a"),))
    lvs_vocal.pack(fill="x", pady=3)
    note(body, "The vocal should be dry — no reverb or tuning already "
               "printed onto it, or this will be correcting a "
               "correction.")
    lvs_sub = LabeledCombo(body, "Snap syllables to",
                           ["1/4", "1/8", "1/8t", "1/16", "1/16t"], "1/8")
    lvs_sub.pack(fill="x", pady=3)
    lvs_align = LabeledEntry(body, "How hard to snap (0 = leave timing "
                                   "alone, 1 = dead on the grid)", "0.85")
    lvs_align.pack(fill="x", pady=3)
    lvs_tune = LabeledCombo(body, "Tuning style",
                            ["off", "natural", "tight", "hard", "robot"],
                            "tight")
    lvs_tune.pack(fill="x", pady=3)
    note(body, "'natural' quietly fixes missed notes; 'hard' is the "
               "obvious stepped tuned-vocal sound; 'off' leaves your "
               "pitch exactly as sung. The key is taken from the "
               "instrumental automatically.")
    lvs_out = PathRow(body, "Folder for finished tracks", "rap_output",
                      mode="dir")
    lvs_out.pack(fill="x", pady=3)
    note(body, "Every render creates a new, uniquely named subfolder in "
               "here holding the track, the separate stems, a click "
               "track for checking the grid by ear, and a receipt "
               "listing every setting used. Nothing is ever "
               "overwritten.")
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
        if cfg["action"].startswith("rap_"):
            if lvs_beat.get():
                cfg["beat"] = lvs_beat.get()
            if lvs_vocal.get():
                cfg["vocal"] = lvs_vocal.get()
            cfg["subdivision"] = lvs_sub.get()
            cfg["tune_preset"] = lvs_tune.get()
            cfg["out_dir"] = lvs_out.get() or "rap_output"
            try:
                cfg["align_strength"] = float(lvs_align.get())
            except ValueError:
                # A typo in a free-text number should say so, not end the
                # run with a stack trace two windows away.
                print(f"'How hard to snap' needs a number between 0 and 1, "
                      f"not {lvs_align.get()!r}. Using 0.85.")
                cfg["align_strength"] = 0.85
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
        expected = 8
        notebook_tabs = notebook.tabs()
        assert len(notebook_tabs) == expected, notebook_tabs
        assert len(smoke_callbacks) == expected, smoke_callbacks

        # Every video preset must actually reach the fields and produce
        # the ticket it promises. This is the whole "no setup" claim, so
        # it is checked rather than asserted in a docstring.
        render_presets.validate_render_presets()
        for preset in render_presets.PRESETS:
            if preset.key == "custom":
                continue
            mc_preset.var.set(preset.label)
            root.update()
            wanted = preset.applied()
            assert mc_lesson.get() == wanted["lesson"], preset.key
            assert mc_action.get() == wanted["action"], preset.key
            assert mc_voice.get() == wanted["voice"], preset.key
            assert mc_rate.get() == wanted["voice_rate"], preset.key
            if wanted["action"] == "export_video":
                assert mc_export.get() == wanted["export_video"], preset.key
            if wanted["action"] == "shots":
                assert mc_shots.get() == wanted["shots"], preset.key
            # Switching presets must not leave the previous one's
            # output paths behind, or a still job quietly carries an
            # MP4 path that belongs to a different film.
            assert mc_voice_preview.get() == wanted["voice_preview"], \
                preset.key
            before = len(launched)
            go_masterclass()
            assert len(launched) == before + 1, preset.key
            ticket = launched[-1][2]
            assert ticket["lesson"] == wanted["lesson"], preset.key
            assert ticket["action"] == wanted["action"], preset.key
        print(f"SMOKETEST OK: {len(render_presets.PRESETS) - 1} video "
              "presets each filled the fields and produced a ticket")
        launched.clear()
        mc_preset.var.set(render_presets.PRESET_LABELS[0])
        root.update()

        for label, callback in smoke_callbacks:
            callback()
        assert len(launched) == expected, launched
        for name, script, cfg in launched:
            print(f"SMOKETEST OK: {name:26} -> {script:28} {cfg}")
        root.update()
        root.destroy()
        print(f"SMOKETEST: {len(launched)}/{expected} launch buttons produced "
              f"a config ticket")
        return 0
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
