"""Write a bedtime story's narration and read-along timings for zeanahlab.com/kids.

    py -3.12 website/scripts/export_storytime.py my-own-home

The story is ``website/src/storytime/stories/<id>.json``: its intro and goodnight pages carry
their own text, and its story pages point at stanzas of the book's manuscript (the verse is read
from the manuscript, so the printed book and the storytime say the same lines). Each page is
spoken with Microsoft Edge TTS; the word boundaries it reports become the read-along timings.
Out go ``website/public/storytime/<id>/<page>.mp3`` and ``manifest.json``, with the figures
the pictures letter in (the reference build's, from ``kids_book.pictures.sheet``). A page whose
words and voice have not changed is not spoken again.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
STORIES = ROOT / "website" / "src" / "storytime" / "stories"
OUT = ROOT / "website" / "public" / "storytime"


def stanzas(verse: Path) -> list[str]:
    text = verse.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    return [s.strip() for s in body.strip().split("\n\n") if s.strip()]


def speakable(text: str) -> str:
    """What the voice reads: the verse's dashes become pauses, quotes stay."""
    return re.sub(r"\s+--\s+", ", ", text).replace("\n", " ")


async def speak(text: str, voice: dict, out: Path) -> list[list]:
    import edge_tts
    words, audio = [], bytearray()
    comm = edge_tts.Communicate(text, voice["name"], rate=voice.get("rate", "+0%"), pitch=voice.get("pitch", "+0Hz"), boundary="WordBoundary")
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            t0 = chunk["offset"] / 1e7
            words.append([round(t0, 3), round(t0 + chunk["duration"] / 1e7, 3), chunk["text"]])
    if not audio:
        raise RuntimeError("no audio")
    out.write_bytes(bytes(audio))
    return words


def place_words(display: str, words: list[list]) -> list[list]:
    """Each spoken word's place in the displayed text: [t0, t1, start, end] in characters."""
    out, at = [], 0
    low = display.lower()
    for t0, t1, w in words:
        token = w.strip().lower()
        if not token:
            continue
        k = low.find(token, at)
        if k < 0:
            continue
        out.append([t0, t1, k, k + len(token)])
        at = k + len(token)
    return out


def figures() -> dict:
    from kids_book import pictures as kp
    from wedge_book import tokens
    d = kp.sheet()
    return {"longIn": d["longIn"], "shortIn": d["shortIn"], "members": d["memberCount"], "triangles": sum(p["count"] for p in d["panels"]),
            "woodCuft": d["woodCuft"], "frameLb": d["frameLb"], "frameCost": round(d["cost"]["frame"]), "hours": tokens.resolve("{{hr.total}}"),
            "diameterFt": d["diameterFt"], "heightFt": d["heightFt"]}


def main(story_id: str) -> None:
    story = json.loads((STORIES / f"{story_id}.json").read_text(encoding="utf-8"))
    verse = stanzas(ROOT / story["verse"]) if story.get("verse") else []
    out = OUT / story_id
    out.mkdir(parents=True, exist_ok=True)
    old = {}
    mf = out / "manifest.json"
    if mf.exists():
        old = {p["id"]: p for p in json.loads(mf.read_text(encoding="utf-8")).get("pages", [])}
    pages = []
    for p in story["pages"]:
        display = verse[p["stanza"] - 1] if "stanza" in p else p["text"]
        spoken = speakable(display)
        key = hashlib.sha1(json.dumps([spoken, story["voice"]]).encode("utf-8")).hexdigest()[:16]
        audio = out / f"{p['id']}.mp3"
        prev = old.get(p["id"])
        if prev and prev.get("key") == key and audio.exists():
            words = prev["words"]
        else:
            for attempt in range(4):
                try:
                    raw = asyncio.run(speak(spoken, story["voice"], audio))
                    break
                except Exception:
                    if attempt == 3:
                        raise
            words = place_words(display, raw)
            print(f"spoke {p['id']}: {len(words)} words", flush=True)
        pages.append({**p, "text": display, "audio": f"/storytime/{story_id}/{p['id']}.mp3", "key": key, "words": words,
                      "duration": round((words[-1][1] if words else 2.0) + 0.6, 2)})
    manifest = {"id": story_id, "title": story["title"], "series": story.get("series"), "pages": pages, "figures": figures(),
                "runtime": round(sum(p["duration"] + 1.4 for p in pages), 1)}
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{story_id}: {len(pages)} pages, about {manifest['runtime'] / 60:.1f} minutes", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "my-own-home")
