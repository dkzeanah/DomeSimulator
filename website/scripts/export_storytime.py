"""Narrate a bedtime story for zeanahlab.com/kids, here or on the live site.

    py -3.12 website/scripts/export_storytime.py my-own-home
        Bake the story in: speak every page of ``website/src/storytime/stories/<id>.json`` that has
        no narration yet, into ``website/public/storytime/<id>/<key>.mp3``, and write
        ``manifest.json`` (the page's fallback when the API is unreachable).

    py -3.12 website/scripts/export_storytime.py my-own-home --sql
        Print the SQL that seeds the story's first version and its baked narration into D1.

    py -3.12 website/scripts/export_storytime.py my-own-home --site https://zeanahlab.com [--version N] [--push]
        Work against the live Story Studio with an agent key (env ZL_AGENT_KEY, scope
        stories:write). --push saves the local JSON as a new version; otherwise the script asks the
        site which pages of version N (default: the newest) have no narration, speaks them and
        uploads them. Pages set to the owner's own voice ("mine") are recorded in the Studio, not here.

A page's narration is found by its KEY: the first 16 hex digits of the SHA-256 of what is spoken,
the voice, its rate and its pitch, joined by NUL characters. functions/_lib/stories.ts computes
the same key, so a page whose words have not changed keeps its narration through every version,
and a page that changes needs speaking again. Word timings come from Edge TTS's word boundaries.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
STORIES = ROOT / "website" / "src" / "storytime" / "stories"
OUT = ROOT / "website" / "public" / "storytime"
GAP = 1.4


def stanzas(verse: Path) -> list[str]:
    text = verse.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    return [s.strip() for s in body.strip().split("\n\n") if s.strip()]


def speakable(text: str) -> str:
    """What the voice reads: the verse's dashes become pauses, line breaks become spaces."""
    return re.sub(r"\s+--\s+", ", ", text).replace("\n", " ")


def narration_key(text: str, voice: dict) -> str:
    raw = "\x00".join([speakable(text), voice["name"], voice.get("rate", "+0%"), voice.get("pitch", "+0Hz")])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


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


def speak_retry(text: str, voice: dict, out: Path) -> list[list]:
    for attempt in range(4):
        try:
            return asyncio.run(speak(text, voice, out))
        except Exception:
            if attempt == 3:
                raise
    return []


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


def resolved(story_id: str) -> dict:
    """The story as the Studio stores it: every page's own words, the voice, the figures."""
    story = json.loads((STORIES / f"{story_id}.json").read_text(encoding="utf-8"))
    verse = stanzas(ROOT / story["verse"]) if story.get("verse") else []
    pages = []
    for p in story["pages"]:
        q = {k: v for k, v in p.items() if k not in ("stanza",)}
        q["text"] = verse[p["stanza"] - 1] if "stanza" in p else p["text"]
        q.setdefault("kind", "page")
        pages.append(q)
    doc = {"title": story["title"], "series": story.get("series", ""), "voice": story["voice"], "pages": pages}
    if story.get("figures") != "none":
        doc["figures"] = figures()
    return doc


def bake(story_id: str) -> dict:
    doc = resolved(story_id)
    out = OUT / story_id
    out.mkdir(parents=True, exist_ok=True)
    mf = out / "manifest.json"
    old = {}
    if mf.exists():
        prev = json.loads(mf.read_text(encoding="utf-8"))
        old = {p["key"]: p for p in prev.get("pages", []) if p.get("key")}
    pages = []
    for p in doc["pages"]:
        key = narration_key(p["text"], doc["voice"])
        audio = out / f"{key}.mp3"
        if key in old and audio.exists():
            words = old[key]["words"]
        else:
            words = place_words(p["text"], speak_retry(speakable(p["text"]), doc["voice"], audio))
            print(f"spoke {p['id']}: {len(words)} words", flush=True)
        pages.append({**p, "key": key, "audio": f"/storytime/{story_id}/{key}.mp3", "words": words,
                      "duration": round((words[-1][1] if words else 2.0) + 0.6, 2)})
    # narration nothing reads any more goes; a page that changes back is spoken again
    keep = {p["key"] for p in pages}
    for f in out.glob("*.mp3"):
        if f.stem not in keep:
            f.unlink()
    manifest = {"id": story_id, "slug": story_id, "title": doc["title"], "series": doc["series"], "voice": doc["voice"],
                "figures": doc.get("figures", {}), "pages": pages, "runtime": round(sum(p["duration"] + GAP for p in pages), 1)}
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{story_id}: {len(pages)} pages, about {manifest['runtime'] / 60:.1f} minutes", flush=True)
    return manifest


def sql(story_id: str) -> str:
    m = json.loads((OUT / story_id / "manifest.json").read_text(encoding="utf-8"))
    doc = resolved(story_id)
    q = lambda s: "'" + str(s).replace("'", "''") + "'"
    now = "2026-10-20T00:00:00Z"
    lines = [f"INSERT INTO stories(slug, title, series, status, live_version, sort, created_at, updated_at) VALUES({q(story_id)}, {q(doc['title'])}, {q(doc['series'])}, 'live', 1, 0, {q(now)}, {q(now)});",
             f"INSERT INTO story_versions(story, n, doc, note, author, created_at) VALUES({q(story_id)}, 1, {q(json.dumps(doc, ensure_ascii=False))}, 'The book as published, read aloud', 'seed', {q(now)});"]
    for p in m["pages"]:
        lines.append(f"INSERT INTO story_audio(story, key, src, content_type, words, duration, voice, created_at) VALUES({q(story_id)}, {q(p['key'])}, {q('static:' + p['audio'])}, 'audio/mpeg', {q(json.dumps(p['words']))}, {p['duration']}, {q(doc['voice']['name'])}, {q(now)});")
    return "\n".join(lines)


def call(site: str, method: str, path: str, body: dict | None = None) -> dict:
    key = os.environ.get("ZL_AGENT_KEY")
    if not key:
        sys.exit("Set ZL_AGENT_KEY to an agent key with the stories:write scope (Admin -> Agents and keys).")
    req = urllib.request.Request(site.rstrip("/") + "/api" + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def sync(story_id: str, site: str, version: int | None, push: bool) -> None:
    if push:
        r = call(site, "POST", f"/agent/stories/{story_id}/versions", {"doc": resolved(story_id), "note": f"from {story_id}.json"})
        print(f"saved version {r['n']}", flush=True)
        version = r["n"]
    todo = call(site, "GET", f"/agent/stories/{story_id}/narration" + (f"?v={version}" if version else ""))
    voice = todo["voice"]
    if voice["name"] == "mine":
        print(f"version {todo['n']} is in the owner's own voice: record its {len(todo['pages'])} pages in Admin -> Stories.")
        return
    tmp = OUT / ".sync"
    tmp.mkdir(parents=True, exist_ok=True)
    for p in todo["pages"]:
        f = tmp / f"{p['key']}.mp3"
        words = place_words(p["text"], speak_retry(p["spoken"], voice, f))
        call(site, "POST", f"/agent/stories/{story_id}/narration", {"key": p["key"], "words": words,
             "duration": round((words[-1][1] if words else 2.0) + 0.6, 2), "contentType": "audio/mpeg",
             "audio": base64.b64encode(f.read_bytes()).decode()})
        f.unlink()
        print(f"narrated {p['id']}", flush=True)
    print(f"version {todo['n']}: {len(todo['pages'])} pages narrated", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", nargs="?", default="my-own-home")
    ap.add_argument("--sql", action="store_true")
    ap.add_argument("--site")
    ap.add_argument("--version", type=int)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.sql:
        print(sql(a.story))
    elif a.site:
        sync(a.story, a.site, a.version, a.push)
    else:
        bake(a.story)
