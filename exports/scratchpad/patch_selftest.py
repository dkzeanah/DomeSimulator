"""Reorder the narration import and make selftest cover companion files.

The missing import that broke the hex export survived every check because
nothing short of a complete narrated export ever called
``write_companion_files``.  Selftest now calls it into a scratch directory,
so the cheapest check covers the most expensive-to-find fault.
"""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")
s = p.read_text(encoding="utf-8")
NL = chr(10)


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:" + NL + old[:300])
    s = s.replace(old, new, 1)


sub(
    "from .narration import narration_script, subtitle_file, write_companion_files"
    + NL
    + "from .lessons import (" + NL
    + "    TWO_V_LESSON," + NL
    + "    Lesson," + NL
    + "    chapter_at_time," + NL
    + "    chapter_start," + NL
    + "    timeline_duration," + NL
    + ")",
    "from .lessons import (" + NL
    + "    TWO_V_LESSON," + NL
    + "    Lesson," + NL
    + "    chapter_at_time," + NL
    + "    chapter_start," + NL
    + "    timeline_duration," + NL
    + ")" + NL
    + "from .narration import narration_script, subtitle_file, write_companion_files",
)

sub(
    "import json" + NL + "import math" + NL + "import subprocess" + NL + "import time",
    "import json" + NL + "import math" + NL + "import subprocess" + NL
    + "import tempfile" + NL + "import time",
)

old_selftest = (
    '    if action == "selftest":' + NL
    + "        validate_geometry()" + NL
    + "        lesson.validate()" + NL
    + "        if lesson.selftest is not None:" + NL
    + "            lesson.selftest()" + NL
    + "        print((lesson.report or calculation_report)())" + NL
    + '        print(f"' + chr(92) + 'nselftest OK: {lesson.title}, '
      '{len(lesson.chapters)} chapters")' + NL
    + "        return 0"
)
new_selftest = (
    '    if action == "selftest":' + NL
    + "        validate_geometry()" + NL
    + "        lesson.validate()" + NL
    + "        if lesson.selftest is not None:" + NL
    + "            lesson.selftest()" + NL
    + "        print((lesson.report or calculation_report)())" + NL
    + "        # Write the companion files to a scratch directory and throw" + NL
    + "        # them away.  They are the last thing an export does, long" + NL
    + "        # after the expensive part, so a fault here is the costliest" + NL
    + "        # kind to discover late and the cheapest to catch here." + NL
    + "        with tempfile.TemporaryDirectory() as scratch:" + NL
    + "            script_path, subtitle_path = write_companion_files(" + NL
    + '                Path(scratch) / f"{lesson.key}.mp4",' + NL
    + "                chapters=lesson.chapters," + NL
    + "                title=lesson.title," + NL
    + "            )" + NL
    + "            for written in (script_path, subtitle_path):" + NL
    + "                if written.stat().st_size <= 0:" + NL
    + '                    print(f"selftest FAILED: {written.name} is empty")' + NL
    + "                    return 1" + NL
    + '            print(' + NL
    + '                f"companion files OK: {script_path.name}, "' + NL
    + '                f"{subtitle_path.name}"' + NL
    + "            )" + NL
    + '        print(f"' + chr(92) + 'nselftest OK: {lesson.title}, '
      '{len(lesson.chapters)} chapters")' + NL
    + "        return 0"
)
sub(old_selftest, new_selftest)

p.write_text(s, encoding="utf-8")
print("app.py: import reordered, selftest now covers companion files")
