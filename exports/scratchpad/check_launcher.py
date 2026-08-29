"""Build the launcher UI without showing it, and check the Lesson field.

Verifies the two things a static read cannot: that the widget is actually
in the tree, and that its live explanation text changes when the selection
changes (rather than being one static block that reads as correct for
every option).
"""

import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

captured = {}


def fake_mainloop(self, *args, **kwargs):
    captured["root"] = self
    raise SystemExit(0)


tk.Misc.mainloop = fake_mainloop

import launcher  # noqa: E402

try:
    launcher.main()
except SystemExit:
    pass

root = captured.get("root")
if root is None:
    raise SystemExit("launcher never reached mainloop")


def walk(widget, depth=0):
    for child in widget.winfo_children():
        yield child, depth
        yield from walk(child, depth + 1)


combos = [w for w, _ in walk(root) if isinstance(w, ttk.Combobox)]
print(f"comboboxes in the tree: {len(combos)}")

lesson_combo = None
for combo in combos:
    values = list(combo.cget("values"))
    if values == ["2v", "build", "hex", "zome"]:
        lesson_combo = combo
        break

if lesson_combo is None:
    raise SystemExit("FAIL: no Lesson combobox with the four lesson keys")
print("Lesson combobox found, values:", list(lesson_combo.cget("values")))
print("default selection:", lesson_combo.get())


def live_labels():
    out = []
    for widget, _ in walk(root):
        if isinstance(widget, ttk.Label):
            try:
                if str(widget.cget("style")) == "Live.TLabel":
                    out.append(widget)
            except tk.TclError:
                pass
    return out


def lesson_help_text():
    # The live label for this combo is the first Live.TLabel packed after
    # it inside the same parent.
    parent = lesson_combo.master.master
    for widget in parent.winfo_children():
        if isinstance(widget, ttk.Label):
            try:
                if str(widget.cget("style")) == "Live.TLabel":
                    text = str(widget.cget("text"))
                    if text.split(" ")[0] in ("2v", "build", "hex", "zome"):
                        return text
            except tk.TclError:
                pass
    return None


seen = {}
for key in ("2v", "build", "hex", "zome"):
    root.setvar(str(lesson_combo.cget("textvariable")), key)
    root.update_idletasks()
    text = lesson_help_text()
    seen[key] = text
    print(f"  {key:<6} -> {text[:96] if text else 'NONE'}")

if any(value is None for value in seen.values()):
    raise SystemExit("FAIL: live explanation label not found for the Lesson combo")
if len(set(seen.values())) != 4:
    raise SystemExit("FAIL: the explanation text does not change per selection")

# Theme contrast: the live style must not be the same colour as its ground.
style = ttk.Style(root)
live_fg = style.lookup("Live.TLabel", "foreground")
live_bg = style.lookup("Live.TLabel", "background") or style.lookup("TFrame", "background")
print("Live.TLabel foreground:", live_fg, " background:", live_bg)
if live_fg and live_bg and str(live_fg).lower() == str(live_bg).lower():
    raise SystemExit("FAIL: live help text is the same colour as its background")

print("PASS: Lesson field present, and its explanation tracks the selection")
root.destroy()
