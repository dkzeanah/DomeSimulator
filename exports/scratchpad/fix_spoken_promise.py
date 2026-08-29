"""Stop the montage speaking its own on-screen headline.

A teaching chapter's ``promise`` is a distinct one-line summary, so
speaking it and then the narration reads naturally.  A montage headline is
a condensed version of the line that follows it, so speaking both says
everything twice and drags the pace -- the opposite of what the format
wants.  The headline stays on screen; the voice reads only the narration.
"""

from pathlib import Path

NL = chr(10)


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}: {old[:200]}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


audio = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\audio.py")
sub(
    audio,
    "def spoken_chapter_text(" + NL
    + "    index: int," + NL
    + "    chapters: tuple[Chapter, ...] = CHAPTERS," + NL
    + ") -> str:" + NL
    + '    """Return fluent prose for one chapter, without reading equations aloud."""' + NL
    + "    chapter = chapters[index]" + NL
    + "    return f\"{chapter.promise}" + chr(92) + "n" + chr(92)
    + "n{' '.join(chapter.narration)}\"",
    "def spoken_chapter_text(" + NL
    + "    index: int," + NL
    + "    chapters: tuple[Chapter, ...] = CHAPTERS," + NL
    + "    speak_promise: bool = True," + NL
    + ") -> str:" + NL
    + '    """Return fluent prose for one chapter, without reading equations aloud.' + NL
    + NL
    + "    A teaching chapter's promise is a separate one-line summary and is" + NL
    + "    read out before the body.  A montage headline is a condensed form" + NL
    + "    of the line that follows it, so reading both says everything twice;" + NL
    + "    those lessons pass ``speak_promise=False`` and keep the headline as" + NL
    + "    on-screen type only." + NL
    + '    """' + NL
    + "    chapter = chapters[index]" + NL
    + "    body = ' '.join(chapter.narration)" + NL
    + "    if not speak_promise:" + NL
    + "        return body" + NL
    + "    return f\"{chapter.promise}" + chr(92) + "n" + chr(92) + "n{body}\"",
)

# Thread the flag through the cache key and the synthesiser.
sub(
    audio,
    "def voice_cache_slug(",
    "def voice_cache_slug(",
)
s = audio.read_text(encoding="utf-8")
s = s.replace(
    "            spoken_chapter_text(index, chapters)",
    "            spoken_chapter_text(index, chapters, speak_promise)", 1)
s = s.replace(
    "                spoken_chapter_text(index, chapters),",
    "                spoken_chapter_text(index, chapters, speak_promise),", 1)
audio.write_text(s, encoding="utf-8")

# Add the parameter to both function signatures.
s = audio.read_text(encoding="utf-8")
start = s.index("def voice_cache_slug(")
end = s.index(") -> str:", start)
block = s[start:end]
if "speak_promise" not in block:
    s = s[:end] + "    speak_promise: bool = True," + NL + s[end:]
audio.write_text(s, encoding="utf-8")

s = audio.read_text(encoding="utf-8")
start = s.index("def synthesize_narration(")
end = s.index(") -> NarrationPlan:", start)
block = s[start:end]
if "speak_promise" not in block:
    s = s[:end] + "    speak_promise: bool = True," + NL + s[end:]
audio.write_text(s, encoding="utf-8")

# The narration script and subtitles must match what is actually said.
narration = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\narration.py")
sub(
    narration,
    "    prose = \" \".join((chapter.promise,) + tuple(chapter.narration))",
    "    prose = \" \".join(" + NL
    + "        ((chapter.promise,) if speak_promise else ()) + tuple(chapter.narration)" + NL
    + "    )",
)
sub(
    narration,
    "def caption_phrases(chapter: Chapter) -> tuple[str, ...]:",
    "def caption_phrases(" + NL
    + "    chapter: Chapter," + NL
    + "    speak_promise: bool = True," + NL
    + ") -> tuple[str, ...]:",
)

print("spoken text, cache key, script and captions all respect speak_promise")
