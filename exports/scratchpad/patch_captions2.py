"""Balance the long-sentence caption split so it stops leaving orphans."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\narration.py")
s = p.read_text(encoding="utf-8")
NL = chr(10)

start = s.index("def caption_phrases(")
end = s.index("def narration_script(")

new = '''def _split_long(sentence: str) -> list[str]:
    """Break one over-long sentence into near-equal readable pieces.

    Filling each cue to the limit and letting the remainder fall where it
    may produces orphans -- a full line followed by two words.  Deciding
    how many pieces are needed first, then cutting near each ideal
    boundary, keeps them even.  A comma is preferred to a bare space
    because it is where a reader would pause anyway.
    """
    if len(sentence) <= MAX_CAPTION_CHARS:
        return [sentence]
    pieces = -(-len(sentence) // MAX_CAPTION_CHARS)
    target = len(sentence) / pieces
    parts: list[str] = []
    rest = sentence
    while len(rest) > MAX_CAPTION_CHARS:
        window = rest[:min(len(rest) - 1, int(target * 1.15))]
        cut = window.rfind(",")
        if cut < target * 0.5:
            cut = window.rfind(" ")
        if cut <= 0:
            break
        parts.append(rest[:cut + 1].strip())
        rest = rest[cut + 1:].strip()
    if rest:
        parts.append(rest)
    return parts


def caption_phrases(chapter: Chapter) -> tuple[str, ...]:
    """Split one chapter into caption-sized pieces, on sentence breaks.

    The stored narration is a tuple of source lines, not of sentences, so
    it is joined back into prose first and then re-split where a reader
    would actually pause.  The speech is synthesized from the same joined
    prose, so changing this never changes the audio.
    """
    prose = " ".join((chapter.promise,) + tuple(chapter.narration))
    phrases: list[str] = []
    for sentence in SENTENCE_BREAK.split(" ".join(prose.split())):
        sentence = sentence.strip()
        if sentence:
            phrases.extend(_split_long(sentence))
    return tuple(phrases) or (chapter.promise,)


'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("narration.py: balanced caption splitting")
