"""A bedtime story from zeanahlab.com/kids, rendered as a film.

    py -3.12 -m sketch_claude storytime my-own-home              # the film: landscape + phone cut + release
    py -3.12 -m sketch_claude storytime my-own-home --stills     # one still per page, to look at first
    py -3.12 -m sketch_claude storytime my-own-home --pages 0-3 --draft    # a rehearsal of a few pages
    py -3.12 -m sketch_claude storytime my-own-home --finish deliverables/0587-storytime-my-own-home   # add a missing phone cut + release
    py -3.12 -m sketch_claude storytime the-lighthouse --site https://zeanahlab.com   # a Studio story
    py -3.12 -m sketch_claude storytime <a-private-story> --private     # a private story, narrated in website/private:
                                                                        # its film stays there too (gitignored)

The story is the manifest the children's player reads: the copy baked into the site
(``website/public/storytime/<slug>/manifest.json``) or, with ``--site``, the version the Story
Studio has published (``/api/stories/<slug>``). The site is built (``website/dist``) and served
from here to a headless Chrome, which opens ``/storytime-render`` -- the player's own world on a
virtual clock (website/src/storytime/StoryRender.tsx) -- and streams its frames into ffmpeg
through the Episode Director's frame pipe (episode_server.render_start / render_frame). The phone
cut is its own pass at 1080x1920, so the words and the framing are made for the tall screen
rather than cropped out of the wide one.

The soundtrack is mixed from the same manifest and the same timeline the page reports: each page's
narration placed at the page's start, under the player's lullaby (the same four chords, synthesised
here). A page with no narration yet is silent in the film and its words stay all bright; the run
says which pages those are.

Out: a new numbered folder ``deliverables/NNNN-storytime-<slug>[-vN]/`` holding the cut, its phone
cut and captions, and ``release/`` with a thumbnail per page and ``description.md``. Nothing is
overwritten; a re-render is the next ``-vN``. Rehearsals (``--draft``, ``--stills``) go to tmp/.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
import wave
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from . import episode_server as ES

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website"
DIST = SITE / "dist"
GAP = 1.4
RATE = 48_000


# ---------------------------------------------------------------- the story

PRIVATE = SITE / "private"          # gitignored: a private story's narration and its review films


def load_manifest(slug: str, site: str | None, private: bool = False) -> dict:
    if private:
        f = PRIVATE / "storytime" / slug / "manifest.json"
        if not f.exists():
            raise SystemExit(f"no private narration for {slug}: run py -3.12 website/scripts/export_storytime.py {slug} first")
        return json.loads(f.read_text(encoding="utf-8"))
    if site:
        with urllib.request.urlopen(f"{site.rstrip('/')}/api/stories/{slug}") as r:
            m = json.loads(r.read())
        m["_site"] = site.rstrip("/")
        return m
    f = SITE / "public" / "storytime" / slug / "manifest.json"
    if not f.exists():
        raise SystemExit(f"no baked story {slug}: run py -3.12 website/scripts/export_storytime.py {slug}, or pass --site")
    return json.loads(f.read_text(encoding="utf-8"))


def audio_file(m: dict, url: str | None, cache: Path) -> Path | None:
    """A page's narration on disk: the site's own baked file, or fetched from the live site."""
    if not url:
        return None
    if url.startswith("private:"):
        f = PRIVATE / url[len("private:"):]
        return f if f.exists() else None
    if url.startswith("/storytime/"):
        f = SITE / "public" / url.lstrip("/")
        if f.exists():
            return f
    if not m.get("_site"):
        return None
    out = cache / (url.rstrip("/").split("/")[-1] + ".audio")
    if not out.exists():
        with urllib.request.urlopen(m["_site"] + url) as r:
            out.write_bytes(r.read())
    return out


def ensure_build() -> None:
    """The render page is part of the site: build it when the storytime code is newer than the build."""
    index = DIST / "index.html"
    newest = max(p.stat().st_mtime for p in (SITE / "src").rglob("*") if p.is_file())
    if index.exists() and index.stat().st_mtime > newest:
        return
    print("building the site (npm run build)", flush=True)
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    r = subprocess.run([npm, "run", "build"], cwd=SITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"the site did not build:\n{r.stdout[-1500:]}\n{r.stderr[-800:]}")


# ---------------------------------------------------------------- the soundtrack

def lullaby(seconds: float) -> np.ndarray:
    """The player's lullaby: four slow chords on sine voices, each note swelling in and out, every six seconds."""
    n = int(seconds * RATE) + RATE
    out = np.zeros(n, np.float64)
    chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
    t = np.arange(int(9 * RATE)) / RATE
    env = np.interp(t, [0, 2.5, 8.5, 9], [0, 0.18, 0, 0])
    rng = np.random.default_rng(7)
    k = 0
    for start in np.arange(0, seconds, 6.0):
        ch = chords[k % 4]; k += 1
        note = sum(np.sin(2 * np.pi * f * (2 ** (rng.uniform(-3, 3) / 1200)) * t) for f in [*ch, ch[0] / 2]) * env
        a = int(start * RATE)
        out[a:a + len(note)] += note[: max(0, n - a)]
    # (the player runs these through a 900 Hz low-pass; every note here is below 400 Hz, so it changes nothing)
    return out[: int(seconds * RATE)] * 0.09


def soundtrack(m: dict, timeline: list[dict], work: Path) -> Path:
    total = sum(p["duration"] for p in timeline)
    bed = work / "lullaby.wav"
    pcm = (np.clip(lullaby(total), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(bed), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm.tobytes())
    by_id = {p["id"]: p for p in m["pages"]}
    inputs, filters, silent = ["-i", str(bed)], [], []
    for row in timeline:
        f = audio_file(m, by_id[row["id"]].get("audio"), work)
        if not f:
            if by_id[row["id"]]["text"].strip():
                silent.append(row["id"])
            continue
        k = len(inputs) // 2
        inputs += ["-i", str(f)]
        ms = int(round(row["start"] * 1000))
        filters.append(f"[{k}:a]aresample={RATE},aformat=channel_layouts=mono,adelay={ms}:all=1[n{k}]")
    if silent:
        print(f"warning: no narration yet for {', '.join(silent)} (silent in the film)", flush=True)
    labels = "".join(f"[n{i}]" for i in range(1, len(filters) + 1))
    graph = ";".join([*filters, f"[0:a]{labels}amix=inputs={len(filters) + 1}:normalize=0:duration=first,alimiter=limit=0.95[out]"])
    out = work / "soundtrack.wav"
    r = subprocess.run([ES._ffmpeg(), "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "[out]", "-ar", str(RATE), "-ac", "2", str(out)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"the soundtrack did not mix: {r.stderr[-500:]}")
    return out


def captions(m: dict, timeline: list[dict]) -> str:
    """One caption per page, for as long as its narration speaks."""
    by_id = {p["id"]: p for p in m["pages"]}
    stamp = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round(s % 1 * 1000)) % 1000:03d}"
    cues = []
    for row in timeline:
        p = by_id[row["id"]]
        if not p["text"].strip():
            continue
        end = row["start"] + max(1.0, row["duration"] - GAP)
        cues.append(f"{len(cues) + 1}\n{stamp(row['start'])} --> {stamp(end)}\n{p['text'].strip()}\n")
    return "\n".join(cues)


# ---------------------------------------------------------------- the browser and its server

class _State:
    def __init__(self, manifest: dict, rid: str | None, stills: Path | None):
        self.manifest, self.rid, self.stills = manifest, rid, stills
        self.done: dict | None = None
        self.event = threading.Event()


class _Handler(SimpleHTTPRequestHandler):
    state: _State

    def log_message(self, *a):          # quiet
        pass

    def _send(self, code: int, body: bytes, kind: str = "application/json"):
        self.send_response(code); self.send_header("Content-Type", kind); self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/render/manifest.json":
            return self._send(200, json.dumps(self.state.manifest).encode())
        if not (DIST / path.lstrip("/")).is_file():
            self.path = "/index.html"          # the site's own routes (a single-page app)
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        q = parse_qs(u.query)
        try:
            if u.path == "/render/frame":
                ES.render_frame(self.state.rid, body, int(q["n"][0]))
                return self._send(200, b"{}")
            if u.path == "/render/still":
                name = Path(q["name"][0]).name
                (self.state.stills / name).write_bytes(body)
                return self._send(200, b"{}")
            if u.path == "/render/done":
                self.state.done = json.loads(body or b"{}")
                self.state.event.set()
                return self._send(200, b"{}")
        except Exception as e:      # the page retries a frame that failed
            return self._send(500, json.dumps({"error": str(e)}).encode())
        return self._send(404, b"{}")


def _run_page(manifest: dict, query: str, rid: str | None, stills: Path | None, size: tuple[int, int], timeout_s: float) -> dict:
    from two_v_demo.book_export import _chrome_path
    chrome = _chrome_path()
    if not chrome:
        raise RuntimeError("no Chrome or Edge found for the headless render")
    state = _State(manifest, rid, stills)
    handler = type("H", (_Handler,), {"state": state})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(DIST)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/storytime-render?{query}"
    profile = tempfile.mkdtemp(prefix="storytime-chrome-")
    proc = subprocess.Popen([chrome, "--headless=new", f"--user-data-dir={profile}", f"--window-size={size[0]},{size[1]}",
                             "--mute-audio", "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11", "--enable-unsafe-swiftshader",
                             "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                             "--enable-logging=stderr", "--v=0", url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")

    def relay():
        for line in proc.stderr:
            if "[render" in line and "[render-done]" not in line:
                print("[render" + line.split("[render", 1)[1].split('", source')[0].rstrip(), flush=True)
    threading.Thread(target=relay, daemon=True).start()
    t0 = last_move = time.time()
    seen = -1
    try:
        while not state.event.wait(2):
            if proc.poll() is not None:
                raise RuntimeError("Chrome exited before the render finished")
            if time.time() - t0 > timeout_s:
                raise RuntimeError("the render timed out")
            # a watchdog: frames that stop arriving end the pass in minutes, not hours
            frames = ES.RENDERS[rid]["frames"] if rid in ES.RENDERS else len(list(stills.glob("*.png"))) if stills else 0
            if frames != seen:
                seen, last_move = frames, time.time()
            elif time.time() - last_move > (240 if frames else 600):
                raise RuntimeError(f"the page stalled at frame {frames} (nothing for {int(time.time() - last_move)} s)")
        if state.done.get("error"):
            raise RuntimeError(f"the page stopped: {state.done['error']}")
        return state.done
    finally:
        proc.kill()
        httpd.shutdown()
        shutil.rmtree(profile, ignore_errors=True)


def page_frames(m: dict, fps: int) -> list[int]:
    """How many frames each page lasts: its narration plus the breath, rounded as the page rounds it (Math.round)."""
    return [int((p["duration"] + GAP) * fps + 0.5) for p in m["pages"]]


def timeline_of(m: dict, fps: int, pages: tuple[int, int] | None = None) -> list[dict]:
    """Each page's start and length in the film, on frame boundaries, from the manifest alone."""
    lo, hi = pages or (0, len(m["pages"]) - 1)
    out, n = [], 0
    for i, f in enumerate(page_frames(m, fps)):
        if lo <= i <= hi:
            out.append({"id": m["pages"][i]["id"], "start": n / fps, "duration": f / fps})
            n += f
    return out


def _pass(manifest: dict, size: tuple[int, int], fps: int, pages: tuple[int, int] | None, timeout_s: float, tries: int = 5) -> tuple[Path, dict, Path]:
    """One orientation: frames -> ffmpeg (the Director's pipe). Returns the silent video, the timeline, and its work folder.

    If the browser hangs part way (this machine's GPU driver has been known to), Chrome is started
    again at the page the frames had reached, writing into the same ffmpeg stream: the frames it has
    already are skipped, so the film carries on without a gap. The world's clock restarts at that
    page, which only shows in things that drift with time (twinkle, waves), never in the story."""
    rid = ES.render_start("storytime", fps, True)["id"]
    r = ES.RENDERS[rid]
    lo, hi = pages or (0, len(manifest["pages"]) - 1)
    counts = page_frames(manifest, fps)
    total = sum(counts[lo:hi + 1])
    start = lo
    try:
        for attempt in range(tries):
            base = sum(counts[lo:start])
            q = f"w={size[0]}&h={size[1]}&fps={fps}&from={start}&to={hi}&base={base}"
            try:
                _run_page(manifest, q, rid, None, size, timeout_s)
                break
            except RuntimeError as e:
                have = r["frames"]
                if attempt == tries - 1 or have >= total:
                    if have >= total:
                        break
                    raise
                # resume at the page holding the first missing frame
                k, acc = lo, 0
                while k < hi and acc + counts[k] <= have:
                    acc += counts[k]; k += 1
                print(f"warning: {e}; resuming at page {k + 1} (frame {acc}, {have} written)", flush=True)
                start = k
    except Exception:
        ES.render_abort(rid)
        raise
    ES.RENDERS.pop(rid)
    r["proc"].stdin.close()
    err = r["proc"].stderr.read().decode("utf-8", "replace")
    if r["proc"].wait() != 0 or not r["video"].exists():
        raise RuntimeError(f"the frames did not encode: {err[-300:]}")
    if r["frames"] != total:
        raise RuntimeError(f"{r['frames']} frames written, {total} expected")
    print(f"{size[0]}x{size[1]}: {r['frames']} frames", flush=True)
    return r["video"], {"timeline": timeline_of(manifest, fps, pages)}, r["work"]


# ---------------------------------------------------------------- the release

def _release(folder: Path, name: str, m: dict, timeline: list[dict], land: Path, phone: Path | None, srt: str) -> dict:
    ff = ES._ffmpeg()
    rel = folder / "release"
    rel.mkdir(exist_ok=True)
    (folder / f"{name}.srt").write_text(srt, encoding="utf-8")
    (rel / f"{name}.srt").write_text(srt, encoding="utf-8")
    by_id = {p["id"]: p for p in m["pages"]}
    thumbs = []
    for i, row in enumerate(timeline):
        p = by_id[row["id"]]
        t = row["start"] + row["duration"] * 0.6
        f = rel / f"thumb-{i + 1:02d}-{p['id']}-{p['scene']}.jpg"
        subprocess.run([ff, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(land), "-frames:v", "1", "-q:v", "3", str(f)], capture_output=True)
        if f.exists():
            thumbs.append(f.name)
    total = sum(r["duration"] for r in timeline)
    chapters = []
    for row in timeline:
        p = by_id[row["id"]]
        if p.get("kind") in ("title",) or row is timeline[0] or p["id"] in ("s1", "outro"):
            label = {"title": "Title", "outro": "Goodnight"}.get(p.get("kind") or "", "The story" if p["id"] == "s1" else "Hello")
            s = int(row["start"])
            chapters.append(f"{s // 60}:{s % 60:02d} {label}")
    first = next((by_id[r["id"]]["text"] for r in timeline if by_id[r["id"]].get("kind") in (None, "page")), "")
    desc = [
        f"# {m['title']}", "", f"*{m.get('series') or 'A bedtime story'}* -- a bedtime story read aloud, about {max(1, round(total / 60))} minute{'' if round(total / 60) <= 1 else 's'}.", "",
        "## Chapters", "", *chapters, "",
        "## YouTube", "",
        f"{m['title']}: a bedtime story, read aloud with the words on screen. "
        + (f'"{first.splitlines()[0].rstrip(",;:- ")}..." ' if first else "") + "Free to watch and read along at zeanahlab.com/kids.", "",
        "#bedtimestory #storytime #readaloud #kidsbooks #picturebook #domehome", "",
        "## Facebook", "",
        f"Tonight's bedtime story: {m['title']}. Read aloud, the words lighting up as they're spoken -- or switch the narrator off at "
        "zeanahlab.com/kids and read it to them yourself.", "",
        "## Instagram", "",
        f"{m['title']} -- a bedtime story in rhyme. Watch it free at zeanahlab.com/kids.", "",
        "#bedtimestory #storytime #readaloud #kidsbooks #geodesicdome #buildwithkids", "",
        "## How it was made", "",
        "The pictures are the storytime's own 3-D world (website/src/storytime), the dome is the wedge-dome solver's own model, "
        "the narration is synthesised (Microsoft Edge TTS) or the owner's own voice, and the lullaby is synthesised. "
        f"Rendered by sketch_claude storytime at {land.name}.",
    ]
    (rel / "description.md").write_text("\n".join(desc) + "\n", encoding="utf-8")
    if not str(folder).startswith(str(PRIVATE)):
        try:
            import medialib
            medialib.write_index()
        except Exception:
            pass
    return {"folder": folder.relative_to(ROOT).as_posix(), "video": land.relative_to(ROOT).as_posix(),
            "phone": phone.relative_to(ROOT).as_posix() if phone else None, "thumbs": thumbs}


def render(slug: str, site: str | None = None, pages: tuple[int, int] | None = None, draft: bool = False, phone: bool = True,
           fps: int = 30, timeout_s: float = 4 * 3600, private: bool = False) -> dict:
    m = load_manifest(slug, site, private)
    ensure_build()
    if private:
        # a private story's film stays in website/private (gitignored), never in the numbered library or its index
        folder = PRIVATE / "renders" / f"{slug}-{time.strftime('%Y%m%d-%H%M%S')}"
        folder.mkdir(parents=True)
        name = slug
    elif draft:
        folder = ROOT / "tmp" / "storytime-drafts" / f"{slug}-{time.strftime('%Y%m%d-%H%M%S')}"
        folder.mkdir(parents=True)
        name = f"storytime-{slug}"
    else:
        import medialib
        folder = medialib.new_folder(f"storytime-{slug}")
        name = folder.name.split("-", 1)[1]
    print(f"rendering {m['title']} ({len(m['pages'])} pages) into {folder.relative_to(ROOT).as_posix()}", flush=True)
    video, done, work = _pass(m, (1920, 1080), fps, pages, timeout_s)
    timeline = done["timeline"]
    track = soundtrack(m, timeline, work)
    ff = ES._ffmpeg()
    land = folder / f"{name}.mp4"
    subprocess.run([ff, "-y", "-v", "error", "-i", str(video), "-i", str(track), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(land)], check=True)
    tall = None
    if phone:
        vvideo, _vdone, vwork = _pass(m, (1080, 1920), fps, pages, timeout_s)
        tall = folder / f"{name}-vertical.mp4"
        subprocess.run([ff, "-y", "-v", "error", "-i", str(vvideo), "-i", str(track), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(tall)], check=True)
        shutil.rmtree(vwork, ignore_errors=True)
    out = _release(folder, name, m, timeline, land, tall, captions(m, timeline))
    shutil.rmtree(work, ignore_errors=True)
    return out


def finish(folder: Path, slug: str, site: str | None = None, fps: int = 30, timeout_s: float = 4 * 3600) -> dict:
    """Complete an iteration whose wide cut rendered but whose phone cut or release did not: render the
    phone pass into the same folder (it is that iteration's companion, so nothing is overwritten) and
    build the release from the wide cut. The timeline is the manifest's own (each page: duration + gap)."""
    folder = Path(folder) if Path(folder).is_absolute() else ROOT / folder
    name = folder.name.split("-", 1)[1]
    land = folder / f"{name}.mp4"
    if not land.exists():
        raise SystemExit(f"{land.relative_to(ROOT).as_posix()} is not there: render the story instead")
    if (folder / "release").exists():
        raise SystemExit(f"{folder.relative_to(ROOT).as_posix()} already has its release")
    m = load_manifest(slug, site)
    ensure_build()
    timeline = timeline_of(m, fps)
    tall = folder / f"{name}-vertical.mp4"
    if not tall.exists():
        vvideo, done, vwork = _pass(m, (1080, 1920), fps, None, timeout_s)
        track = soundtrack(m, done["timeline"], vwork)
        subprocess.run([ES._ffmpeg(), "-y", "-v", "error", "-i", str(vvideo), "-i", str(track), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", str(tall)], check=True)
        shutil.rmtree(vwork, ignore_errors=True)
    return _release(folder, name, m, timeline, land, tall, captions(m, timeline))


def stills(slug: str, site: str | None = None, size: tuple[int, int] = (1920, 1080), private: bool = False) -> Path:
    """One still per page at 60% through it, words drawn in: tmp/storytime-stills/<slug>-<time>/
    (a private story's go to website/private/renders/stills-...)."""
    m = load_manifest(slug, site, private)
    ensure_build()
    base = PRIVATE / "renders" if private else ROOT / "tmp" / "storytime-stills"
    out = base / f"{'stills-' if private else ''}{slug}-{size[0]}x{size[1]}-{time.strftime('%Y%m%d-%H%M%S')}"
    out.mkdir(parents=True)
    _run_page(m, f"w={size[0]}&h={size[1]}&fps=30&stills=1", None, out, size, 1800)
    return out
