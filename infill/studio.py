"""Triangle Infill & Covering: the calculator and viewer.

Enter your max strut length and log sizes; pick a triangle, a material and a
pattern; see it face-on and end-on, with a cut list, the saw settings for
every end, how to fit it, and what it all adds up to for one triangle or the
whole dome. Runs on its own (``python -m infill``) or as a launcher tab.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import export, render
from .draw import PALETTE as P
from .draw import TkPainter
from .frame import Spec, solve
from .patterns import ARRANGEMENTS, LAYS, MATERIALS, OPTIONS, Options, layout, valid
from .stock import plan as stock_plan

INTRO = ("Work out how to fill or cover the triangles of the wedge dome, piece by piece. Enter your max strut "
         "length and log sizes, pick a triangle, a material and a pattern. The left drawing is the triangle "
         "seen face-on; the right one shows the pieces end-on, as they sit in the frame's thickness, packed "
         "against its 45° wall. Every length and saw setting is worked out from the shapes; the figures that "
         "are guesses (prices, kerfs, sheet sizes) are on the 'Declared figures' page.")


class InfillStudio(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._job = None
        self.layouts = []
        self.current = None
        self.highlight = None
        self._build()
        self._shown = False
        # Work it out the first time the panel is shown, not when it is built:
        # inside the launcher that keeps start-up quick.
        self.bind("<Map>", self._first_show)

    def _first_show(self, _e=None):
        if not self._shown:
            self._shown = True
            self.after(30, self.refresh)

    # ------------------------------------------------------------------
    # Layout of the window
    # ------------------------------------------------------------------
    def _build(self):
        ttk.Label(self, text=INTRO, wraplength=1100, justify="left", style="Intro.TLabel").pack(
            fill="x", padx=2, pady=(0, 6))
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=1)
        # The controls: a fixed-width column that scrolls when the window is short.
        holder = ttk.Frame(body, width=340)
        holder.grid(row=0, column=0, sticky="ns")
        holder.grid_propagate(False)
        holder.pack_propagate(False)
        lc = tk.Canvas(holder, highlightthickness=0, width=320, bg=ttk.Style().lookup("TFrame", "background"))
        lsb = ttk.Scrollbar(holder, orient="vertical", command=lc.yview)
        left = ttk.Frame(lc, padding=(4, 0))
        left.bind("<Configure>", lambda _e: lc.configure(scrollregion=lc.bbox("all")))
        lc.create_window((0, 0), window=left, anchor="nw", width=318)
        lc.configure(yscrollcommand=lsb.set)
        lsb.pack(side="right", fill="y")
        lc.pack(side="left", fill="both", expand=True)
        lc.bind_all("<MouseWheel>", lambda e: lc.yview_scroll(int(-e.delta / 120), "units")
                    if str(e.widget).startswith(str(lc)) else None)
        mid = ttk.Frame(body)
        mid.grid(row=0, column=1, sticky="nsew", padx=(6, 3))
        right = ttk.Frame(body)
        right.grid(row=0, column=2, sticky="nsew", padx=(3, 0))

        def field(parent, label, var, width=8, tip=""):
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=label, width=22).pack(side="left")
            e = ttk.Entry(row, textvariable=var, width=width)
            e.pack(side="left")
            e.bind("<Return>", lambda _e: self.refresh())
            e.bind("<FocusOut>", lambda _e: self.refresh())
            if tip:
                ttk.Label(parent, text=tip, style="Note.TLabel", wraplength=290, justify="left").pack(
                    anchor="w", pady=(0, 3))
            return e

        def heading(parent, text):
            ttk.Label(parent, text=text, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 2))

        heading(left, "Your dome")
        self.v_strut = tk.StringVar(value="72")
        self.v_frame_log = tk.StringVar(value="12")
        self.v_infill_log = tk.StringVar(value="12")
        field(left, "Max strut length (in)", self.v_strut,
              tip="The longest frame stick. The dome, both triangle shapes and every frame cut follow from it.")
        field(left, "Frame log diameter (in)", self.v_frame_log,
              tip="The logs the frame wedges came from. Sets the frame's thickness and its 45° wall.")
        field(left, "Infill log diameter (in)", self.v_infill_log,
              tip="The logs the infill wedges and slices come from (can be smaller).")

        heading(left, "Which triangle")
        self.v_panel = tk.StringVar(value="0")
        self.panel_box = ttk.Frame(left)
        self.panel_box.pack(fill="x")
        self.v_scope = tk.StringVar(value="one")
        sc = ttk.Frame(left)
        sc.pack(fill="x", pady=(2, 0))
        ttk.Radiobutton(sc, text="One triangle", variable=self.v_scope, value="one",
                        command=self.refresh).pack(side="left")
        ttk.Radiobutton(sc, text="Whole dome (all 40)", variable=self.v_scope, value="dome",
                        command=self.refresh).pack(side="left", padx=8)

        heading(left, "Fill or cover")
        self.v_mode = tk.StringVar(value="fill")
        md = ttk.Frame(left)
        md.pack(fill="x")
        ttk.Radiobutton(md, text="Fill (inside the frame)", variable=self.v_mode, value="fill",
                        command=self.refresh).pack(anchor="w")
        ttk.Radiobutton(md, text="Cover (over the open side)", variable=self.v_mode, value="cover",
                        command=self.refresh).pack(anchor="w")

        heading(left, "Material and pattern")
        self.v_mat = tk.StringVar(value=MATERIALS["w8"][0])
        self.v_arr = tk.StringVar(value=ARRANGEMENTS["rings"])
        self.v_lay = tk.StringVar(value=LAYS["flipflop"][0])
        self.v_edge = tk.StringVar(value="")
        self.c_mat = self._combo(left, "Material", self.v_mat, [v[0] for v in MATERIALS.values()])
        self.c_arr = self._combo(left, "Arrangement", self.v_arr, [])
        self.c_lay = self._combo(left, "Lay", self.v_lay, [])
        self.lay_help = ttk.Label(left, style="Live.TLabel", wraplength=290, justify="left")
        self.lay_help.pack(fill="x", pady=(2, 4))
        self.c_edge = self._combo(left, "Lay the runs from", self.v_edge, [])
        self.v_tilt = tk.StringVar(value="45")
        field(left, "Louver tilt (degrees)", self.v_tilt, tip="Louvers only: how far each slat leans.")
        self.v_flush = tk.StringVar(value="open")
        fl = ttk.Frame(left)
        fl.pack(fill="x")
        ttk.Label(fl, text="Boards / sheets flush:", width=19).pack(side="left")
        ttk.Radiobutton(fl, text="open side", variable=self.v_flush, value="open",
                        command=self.refresh).pack(side="left")
        ttk.Radiobutton(fl, text="flat side", variable=self.v_flush, value="flat",
                        command=self.refresh).pack(side="left")

        heading(left, "Log rounds")
        self.v_rt = tk.StringVar(value="1.5")
        self.v_rmin = tk.StringVar(value="3")
        field(left, "Slice thickness (in)", self.v_rt,
              tip="Rounds only: how thick each round is cut. The frame takes as many layers as fit, "
                  "and a thinner last one for the rest.")
        field(left, "Smallest round (in)", self.v_rmin,
              tip="Rounds only: the smallest round from up the trunk worth cutting, for the "
                  "'small ones in the gaps' pattern.")
        self.v_left = tk.StringVar(value="cut")
        lo = ttk.Frame(left)
        lo.pack(fill="x")
        ttk.Radiobutton(lo, text="Gaps cut to fit (copy the pattern over them)", variable=self.v_left,
                        value="cut", command=self.refresh).pack(anchor="w")
        ttk.Radiobutton(lo, text="Gaps left open (vents)", variable=self.v_left, value="open",
                        command=self.refresh).pack(anchor="w")
        self.v_layer = tk.StringVar(value="1")
        self.c_layer = self._combo(left, "Show layer", self.v_layer, ["1"])
        self.c_layer.unbind("<<ComboboxSelected>>")
        self.c_layer.bind("<<ComboboxSelected>>", lambda _e: self._show_layer())

        heading(left, "View")
        self.v_side = tk.StringVar(value="open")
        vs = ttk.Frame(left)
        vs.pack(fill="x")
        ttk.Radiobutton(vs, text="from the open side", variable=self.v_side, value="open",
                        command=self.redraw).pack(side="left")
        ttk.Radiobutton(vs, text="from the flat side", variable=self.v_side, value="flat",
                        command=self.redraw).pack(side="left")

        heading(left, "Save")
        for text, cmd in (("Cut sheet to print (SVG)", self.save_svg), ("Picture (PNG)", self.save_png),
                          ("Cut list (CSV, for a spreadsheet)", self.save_csv),
                          ("Gallery: every pattern for this material", self.save_gallery)):
            ttk.Button(left, text=text, command=cmd).pack(fill="x", pady=1)
        self.status = ttk.Label(left, style="Note.TLabel", wraplength=290, justify="left")
        self.status.pack(fill="x", pady=(8, 0))

        # Middle: the plan.
        self.plan_canvas = tk.Canvas(mid, bg=P["paper"], highlightthickness=0)
        self.plan_canvas.pack(fill="both", expand=True)
        self.plan_canvas.bind("<Configure>", lambda _e: self.redraw())
        # Right: section above, notes below.
        self.sec_canvas = tk.Canvas(right, bg=P["paper"], height=260, highlightthickness=0)
        self.sec_canvas.pack(fill="x")
        self.sec_canvas.bind("<Configure>", lambda _e: self.redraw())
        self.legend_canvas = tk.Canvas(right, bg=P["paper"], height=96, highlightthickness=0)
        self.legend_canvas.pack(fill="x")
        nb = ttk.Notebook(right)
        nb.pack(fill="both", expand=True, pady=(4, 0))
        cut = ttk.Frame(nb)
        nb.add(cut, text="Cut list")
        cols = ("n", "piece", "lies", "long", "short", "ends")
        self.tree = ttk.Treeview(cut, columns=cols, show="headings", height=10)
        for c, w, t in zip(cols, (30, 130, 150, 56, 56, 380),
                           ("#", "piece", "how it lies", "long in", "short in", "end cuts")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w", stretch=(c == "ends"))
        ys = ttk.Scrollbar(cut, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_pick)
        self.t_steps = self._text(nb, "How to cut it")
        self.t_fit = self._text(nb, "Fitting it")
        self.t_totals = self._text(nb, "Totals")
        self.t_declared = self._text(nb, "Declared figures")
        for t in (self.t_totals, self.t_declared):
            t.configure(font=("Consolas", 10), wrap="none")

    def _combo(self, parent, label, var, values):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=1)
        ttk.Label(row, text=label, width=16).pack(side="left")
        c = ttk.Combobox(row, textvariable=var, values=values, state="readonly", width=26)
        c.pack(side="left", fill="x", expand=True)
        c.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        return c

    def _text(self, nb, title):
        f = ttk.Frame(nb)
        nb.add(f, text=title)
        t = tk.Text(f, wrap="word", font=("Segoe UI", 10), bg="#fbf8f2", fg=P["ink"], relief="flat",
                    padx=8, pady=6)
        s = ttk.Scrollbar(f, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=s.set)
        t.pack(side="left", fill="both", expand=True)
        s.pack(side="right", fill="y")
        return t

    @staticmethod
    def _set(t, text):
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("1.0", text)
        t.configure(state="disabled")

    # ------------------------------------------------------------------
    # Reading the controls
    # ------------------------------------------------------------------
    def _num(self, var, default, lo, hi):
        try:
            v = float(var.get())
        except ValueError:
            v = default
        v = min(max(v, lo), hi)
        var.set(f"{v:g}")
        return v

    def spec(self) -> Spec:
        return Spec(max_strut_in=self._num(self.v_strut, 72, 24, 240),
                    frame_log_in=self._num(self.v_frame_log, 12, 4, 36))

    def options(self) -> Options:
        mat = next(k for k, v in MATERIALS.items() if v[0] == self.v_mat.get())
        kind = MATERIALS[mat][1]
        allowed = OPTIONS[kind]
        self.c_arr.configure(values=[ARRANGEMENTS[a] for a in allowed["arrangements"]])
        self.c_lay.configure(values=[LAYS[l][0] for l in allowed["lays"] if not (l == "shim" and mat == "s32")]
                             if self.v_arr.get() != ARRANGEMENTS["louvers"] else [])
        arr = next((k for k, v in ARRANGEMENTS.items() if v == self.v_arr.get()), allowed["arrangements"][0])
        lay = next((k for k, v in LAYS.items() if v[0] == self.v_lay.get()), "")
        edge = 0
        if self.v_edge.get().startswith("edge "):
            edge = int(self.v_edge.get().split()[1].rstrip(':')) - 1
        o = valid(Options(mat, arr, lay, self.v_mode.get(), edge,
                          self._num(self.v_infill_log, 12, 4, 36),
                          self._num(self.v_tilt, 45, 10, 80), self.v_flush.get(),
                          round_t_in=self._num(self.v_rt, 1.5, 0.25, 12),
                          round_min_in=self._num(self.v_rmin, 3, 1, 36),
                          leftover=self.v_left.get(), layer=int(self.v_layer.get() or 1)))
        self.v_arr.set(ARRANGEMENTS[o.arrangement])
        self.v_lay.set(LAYS[o.lay][0] if o.lay else "(not used here)")
        self.lay_help.configure(text=LAYS[o.lay][1] if o.lay else
                                "Louvers: each slat tilted and lapped over the next -- covered seen straight "
                                "on, open to air between the slats." if o.arrangement == "louvers" else
                                {"sheet": "One piece per triangle (two if it will not fit a 4 x 8 sheet).",
                                 "film": "One piece per triangle, cut oversize to staple.",
                                 "metal": "Strips across the triangle, each lapping the last by a rib."}[kind])
        return o

    # ------------------------------------------------------------------
    # Working it out
    # ------------------------------------------------------------------
    def refresh(self):
        try:
            self.configure(cursor="watch")
            self.update_idletasks()
            spec = self.spec()
            solved = solve(spec)
            types = solved["types"]
            # Triangle choice, rebuilt when the shapes change.
            for w in self.panel_box.winfo_children():
                w.destroy()
            for i, t in enumerate(types):
                ttk.Radiobutton(self.panel_box, text=f"{t.label}  (×{t.count})", variable=self.v_panel,
                                value=str(i), command=self.refresh).pack(anchor="w")
            idx = min(int(self.v_panel.get() or 0), len(types) - 1)
            panel = types[idx]
            self.c_edge.configure(values=[f"edge {k + 1}: {panel.edge_class[k].lower()} "
                                          f"({panel.edge_len[k]:.1f} in)" for k in range(3)])
            if not self.v_edge.get():
                self.v_edge.set(self.c_edge.cget("values")[0])
            opts = self.options()
            if self.v_scope.get() == "dome":
                self.layouts = [(layout(t, opts), t.count) for t in types]
                self.current = self.layouts[idx][0]
            else:
                self.current = layout(panel, opts)
                self.layouts = [(self.current, 1)]
            self.plan = stock_plan(self.layouts, self.v_scope.get())
            n_layers = len(self.current.extra["layers"]) if self.current.extra else 1
            self.c_layer.configure(values=[str(i + 1) for i in range(n_layers)])
            if int(self.v_layer.get() or 1) > n_layers:
                self.v_layer.set("1")
                self._show_layer(redraw=False)
            self._fill_tables(spec, solved)
            self.highlight = None
            self.redraw()
            self.status.configure(text=f"Dome {solved['diameter_ft']:.1f} ft across · frame "
                                       f"{spec.thickness_in:.2f} in thick · walls {spec.wall_deg:.0f}°")
        except Exception as exc:  # noqa: BLE001 -- show it, keep the window alive
            self.status.configure(text=f"Could not work that out: {exc}")
            raise
        finally:
            self.configure(cursor="")

    def _fill_tables(self, spec, solved):
        L = self.current
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(L.pieces):
            self.tree.insert("", "end", iid=str(i), values=(
                i + 1, p.group, render.POSE_NAME.get(p.pose, p.pose), f"{p.long:.2f}", f"{p.short:.2f}",
                p.cut_text + (f"  · rip {p.trim:.2f} in flush" if p.trim > 0.01 else "")))
        self._set(self.t_steps, "\n\n".join(L.steps))
        self._set(self.t_fit, "\n\n".join(L.fitting) or "Nothing special: every piece seats square.")
        m = L.metrics
        lines = [f"{L.title}", f"{L.panel.label}, {L.opts.mode}", ""]
        if self.v_scope.get() == "dome":
            lines.append("WHOLE DOME (both triangle shapes, offcuts shared):")
        else:
            lines.append("THIS TRIANGLE:")
        lines += [f"   {a:<34} {b}" for a, b in self.plan.lines]
        lines += ["", "PER TRIANGLE:",
                  f"   pieces                             {len(L.pieces)}",
                  f"   longest / shortest piece           {m.get('longest', 0):.1f} / {m.get('shortest', 0):.1f} in"]
        if m.get("pitch"):
            lines.append(f"   one repeat across the runs         {m['pitch']:.2f} in")
        if "solid" in m and "pattern_cover" not in m:
            lines.append(f"   wood in the frame's thickness      {100 * m['solid']:.0f}%")
        if m.get("see_through", 0) > 0.001:
            lines.append(f"   seen straight through              {100 * m['see_through']:.0f}%")
        if "pattern_cover" in m:
            lines.append(f"   layers                             {m['layers']}")
            lines.append(f"   the pattern alone covers           {100 * m['pattern_cover']:.0f}%")
            lines.append(f"   cut to fit, covered                {100 * m['solid']:.1f}%")
        if "air_gap" in m:
            lines.append(f"   clear air between slats            {m['air_gap']:.2f} in")
        if m.get("remainder_in2"):
            lines.append(f"   centre left over                   {m['remainder_in2']:.0f} sq in")
        lines.append(f"   weight                             {m.get('kg', 0):.1f} kg")
        if self.plan.warnings:
            lines += ["", "WATCH OUT:"] + [f"   {w}" for w in self.plan.warnings]
        self._set(self.t_totals, "\n".join(lines))
        self._set(self.t_declared, export.declared_text(spec, solved))

    def redraw(self):
        L = self.current
        if L is None:
            return
        for c in (self.plan_canvas, self.sec_canvas, self.legend_canvas):
            c.delete("all")
        w, h = self.plan_canvas.winfo_width(), self.plan_canvas.winfo_height()
        if w > 20 and h > 20:
            render.plan(TkPainter(self.plan_canvas), L, 0, 0, w, h, highlight=self.highlight,
                        from_side=self.v_side.get())
        w2, h2 = self.sec_canvas.winfo_width(), self.sec_canvas.winfo_height()
        if w2 > 20:
            render.section(TkPainter(self.sec_canvas), L, 0, 0, w2, h2)
        render.legend(TkPainter(self.legend_canvas), L, 8, 6)

    def _show_layer(self, redraw: bool = True):
        from dataclasses import replace
        if self.current is not None:
            self.current.opts = replace(self.current.opts, layer=int(self.v_layer.get() or 1))
            if redraw:
                self.redraw()

    def _on_pick(self, _e):
        sel = self.tree.selection()
        self.highlight = int(sel[0]) if sel else None
        self.redraw()

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def _default(self, ext):
        return export.OUT / f"{export.slug(self.current)}.{ext}"

    def _ask(self, ext, kind):
        d = self._default(ext)
        d.parent.mkdir(parents=True, exist_ok=True)
        return filedialog.asksaveasfilename(initialdir=str(d.parent), initialfile=d.name,
                                            defaultextension=f".{ext}", filetypes=[(kind, f"*.{ext}")])

    def _done(self, path):
        messagebox.showinfo("Saved", f"Saved to\n{path}")

    def save_svg(self):
        path = self._ask("svg", "SVG drawing")
        if path:
            from pathlib import Path
            self._done(export.write_svg(self.current, self.plan.lines, Path(path)))

    def save_png(self):
        path = self._ask("png", "PNG picture")
        if path:
            from pathlib import Path
            self._done(export.write_png(self.current, self.plan.lines, Path(path)))

    def save_csv(self):
        path = self._ask("csv", "CSV spreadsheet")
        if path:
            from pathlib import Path
            self._done(export.write_csv(self.layouts, Path(path)))

    def save_gallery(self):
        path = self._ask("png", "PNG picture")
        if path:
            from pathlib import Path
            self.configure(cursor="watch")
            self.update_idletasks()
            try:
                self._done(export.gallery(self.current.panel, self.current.opts, Path(path)))
            finally:
                self.configure(cursor="")


def main() -> int:
    root = tk.Tk()
    root.title("Triangle Infill & Covering")
    root.geometry("1500x900")
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Intro.TLabel", background="#d7e3ea", foreground="#12242f", font=("Segoe UI", 10),
                    padding=(10, 8))
    style.configure("Note.TLabel", foreground="#33404a", font=("Segoe UI", 9))
    style.configure("Live.TLabel", background="#d9e8da", foreground="#0d2b12", font=("Segoe UI", 9, "bold"),
                    padding=(8, 6))
    InfillStudio(root, padding=8).pack(fill="both", expand=True)
    root.mainloop()
    return 0
