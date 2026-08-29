"""Drive speak_promise from the lesson's style at every call site."""

from pathlib import Path

NL = chr(10)


def sub(path: Path, old: str, new: str, count: int = 1) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}: {old[:220]}")
    path.write_text(s.replace(old, new, count), encoding="utf-8")


narration = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\narration.py")

# narration_script: the written script must match what is spoken.
s = narration.read_text(encoding="utf-8")
start = s.index("def narration_script(")
end = s.index(") -> str:", start)
if "speak_promise" not in s[start:end]:
    s = s[:end] + "    speak_promise: bool = True," + NL + s[end:]
narration.write_text(s, encoding="utf-8")

s = narration.read_text(encoding="utf-8")
start = s.index("def subtitle_file(")
end = s.index(") -> str:", start)
if "speak_promise" not in s[start:end]:
    s = s[:end] + "    speak_promise: bool = True," + NL + s[end:]
narration.write_text(s, encoding="utf-8")

s = narration.read_text(encoding="utf-8")
start = s.index("def write_companion_files(")
end = s.index(") -> tuple[Path, Path]:", start)
if "speak_promise" not in s[start:end]:
    s = s[:end] + "    speak_promise: bool = True," + NL + s[end:]
narration.write_text(s, encoding="utf-8")

sub(narration,
    "        phrases = caption_phrases(chapter)",
    "        phrases = caption_phrases(chapter, speak_promise)")

# The script body prints the promise as its own paragraph; drop it when it
# is not spoken, so the script is a script and not a description.
s = narration.read_text(encoding="utf-8")
if "if speak_promise:" not in s:
    old = '        lines.append(f"{chapter.promise}")'
    if old in s:
        s = s.replace(
            old,
            "        if speak_promise:" + NL
            + '            lines.append(f"{chapter.promise}")', 1)
        narration.write_text(s, encoding="utf-8")

app = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")

# A montage keeps its headline on screen only.
sub(app,
    "    def export_video(",
    "    @property" + NL
    + "    def speak_promise(self) -> bool:" + NL
    + '        """Whether the voice reads the on-screen headline as well.' + NL
    + NL
    + "        Teaching lessons do: the promise is a separate summary line." + NL
    + "        A montage does not: its headline is a condensed form of the" + NL
    + "        narration underneath it, so reading both says it twice." + NL
    + '        """' + NL
    + '        return self.lesson.style != "hype"' + NL
    + NL
    + "    def export_video(")

print("speak_promise threaded through narration and app")
