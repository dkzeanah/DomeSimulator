"""Split captions on sentences, and time them by length rather than count.

The chapter text is stored as source-line fragments, which is fine for the
teaching card and irrelevant to the speech (the fragments are joined before
synthesis).  Using those fragments as caption cues, though, breaks lines
mid-clause and gives a two-word cue the same screen time as a long one.
"""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\narration.py")
s = p.read_text(encoding="utf-8")
NL = chr(10)


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:" + NL + old[:300])
    s = s.replace(old, new, 1)


sub(
    "from pathlib import Path" + NL + NL + "from .lessons import CHAPTERS, Chapter",
    "import re" + NL
    + "from pathlib import Path" + NL + NL
    + "from .lessons import CHAPTERS, Chapter" + NL + NL + NL
    + "# A caption longer than this is hard to read before it is replaced." + NL
    + "MAX_CAPTION_CHARS = 96" + NL
    + "SENTENCE_BREAK = re.compile(r'(?<=[.!?])" + chr(92) + "s+')",
)

sub(
    "def narration_script(",
    'def caption_phrases(chapter: Chapter) -> tuple[str, ...]:' + NL
    + '    """Split one chapter into caption-sized pieces, on sentence breaks.' + NL
    + NL
    + '    The stored narration is a tuple of source lines, not of sentences,' + NL
    + '    so it is joined back into prose first and then re-split where a' + NL
    + '    reader would actually pause.  A sentence too long to sit on screen' + NL
    + '    is broken again at its last comma, and failing that at a space.' + NL
    + '    """' + NL
    + '    prose = " ".join((chapter.promise,) + tuple(chapter.narration))' + NL
    + '    phrases: list[str] = []' + NL
    + '    for sentence in SENTENCE_BREAK.split(" ".join(prose.split())):' + NL
    + '        sentence = sentence.strip()' + NL
    + '        while len(sentence) > MAX_CAPTION_CHARS:' + NL
    + '            head = sentence[:MAX_CAPTION_CHARS]' + NL
    + '            cut = head.rfind(",")' + NL
    + '            if cut < MAX_CAPTION_CHARS // 3:' + NL
    + '                cut = head.rfind(" ")' + NL
    + '            if cut <= 0:' + NL
    + '                break' + NL
    + '            phrases.append(sentence[:cut + 1].strip())' + NL
    + '            sentence = sentence[cut + 1:].strip()' + NL
    + '        if sentence:' + NL
    + '            phrases.append(sentence)' + NL
    + '    return tuple(phrases) or (chapter.promise,)' + NL
    + NL + NL
    + "def narration_script(",
)

old_loop = (
    "    for chapter_index, (chapter, duration) in enumerate(zip(chapters, durations)):" + NL
    + "        phrases = (chapter.promise,) + chapter.narration" + NL
    + "        speech_span = (" + NL
    + "            speech_durations[chapter_index]" + NL
    + "            if speech_durations is not None" + NL
    + "            else duration" + NL
    + "        )" + NL
    + "        segment_duration = speech_span / len(phrases)" + NL
    + "        for index, phrase in enumerate(phrases):" + NL
    + "            start = cursor + speech_delay + index * segment_duration" + NL
    + "            end = cursor + speech_delay + (index + 1) * segment_duration - 0.08"
)
new_loop = (
    "    for chapter_index, (chapter, duration) in enumerate(zip(chapters, durations)):" + NL
    + "        phrases = caption_phrases(chapter)" + NL
    + "        speech_span = (" + NL
    + "            speech_durations[chapter_index]" + NL
    + "            if speech_durations is not None" + NL
    + "            else duration" + NL
    + "        )" + NL
    + "        # Speech takes about as long as the text is long, so give each" + NL
    + "        # cue a share of the chapter proportional to its own length" + NL
    + "        # instead of an equal slice.  A three-word cue no longer sits" + NL
    + "        # on screen as long as a full sentence." + NL
    + "        weights = [max(1, len(phrase)) for phrase in phrases]" + NL
    + "        total_weight = sum(weights)" + NL
    + "        offsets = [0.0]" + NL
    + "        for weight in weights:" + NL
    + "            offsets.append(offsets[-1] + speech_span * weight / total_weight)" + NL
    + "        for index, phrase in enumerate(phrases):" + NL
    + "            start = cursor + speech_delay + offsets[index]" + NL
    + "            end = cursor + speech_delay + offsets[index + 1] - 0.08"
)
sub(old_loop, new_loop)

p.write_text(s, encoding="utf-8")
print("narration.py: captions now split on sentences and are length-timed")
