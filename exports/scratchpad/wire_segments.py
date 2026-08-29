"""Wire segment composition into the render path, without disturbing
anything already published.

Composition is opt-in per render.  The nine deliverables that already
shipped were made before segments existed, so they stay off and continue
to reproduce exactly; new work turns it on and gets the outro and the
call to action for free.
"""

from pathlib import Path

NL = chr(10)
Q = chr(34) * 3


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}:" + NL + old[:280])
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


# --- the manifest remembers what each film was composed with -----------
deliv = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\deliverables.py")
sub(
    deliv,
    "    lesson: str" + NL
    + "    filename: str" + NL
    + "    note: str",
    "    lesson: str" + NL
    + "    filename: str" + NL
    + "    note: str" + NL
    + "    compose: bool = False" + NL
    + "    " + Q + "Whether to splice the automatic segments in." + NL + NL
    + "    Off for everything that shipped before segments existed, so those" + NL
    + "    files keep reproducing exactly. New work turns it on." + Q + NL
    + "    segments: tuple[str, ...] = ()" + NL
    + "    " + Q + "Extra segments by key, beyond the automatic ones." + Q,
)
sub(
    deliv,
    '        _lc.write_config("two_v_masterclass", {' + NL
    + '            "action": "export_video",' + NL
    + '            "lesson": item.lesson,' + NL
    + '            "export_video": str(target),' + NL
    + '            "size": size,' + NL
    + '            "fps": fps,' + NL
    + "        })",
    '        _lc.write_config("two_v_masterclass", {' + NL
    + '            "action": "export_video",' + NL
    + '            "lesson": item.lesson,' + NL
    + '            "export_video": str(target),' + NL
    + '            "size": size,' + NL
    + '            "fps": fps,' + NL
    + '            "compose_segments": item.compose,' + NL
    + '            "segments_include": ",".join(item.segments),' + NL
    + "        })",
)

# --- main() composes when asked ----------------------------------------
app = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")
sub(
    app,
    "from .deliverables import deliverables_menu, render_all, validate_deliverables",
    "from .deliverables import deliverables_menu, render_all, validate_deliverables" + NL
    + "from .segments import compose, segment_menu, validate_segments",
)
sub(
    app,
    '    if action == "list_deliverables":',
    '    if action == "list_segments":' + NL
    + "        print(segment_menu())" + NL
    + "        return 0" + NL
    + '    if action == "list_deliverables":',
)

print("manifest and actions wired")
