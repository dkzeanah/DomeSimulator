"""Every finished film, on zeanahlab.com/episodes.

    py -3.12 scripts/export_episodes.py                 # list what would be published, and why not the rest
    py -3.12 scripts/export_episodes.py --prepare       # web-ready copies in private/episodes/ (no upload)
    py -3.12 scripts/export_episodes.py --upload --local     # into wrangler's local media store (npm run preview)
    py -3.12 scripts/export_episodes.py --upload --remote    # into the real one (zeanahlab-media)

What an episode is: the newest iteration of a library concept (medialib) whose main cut is
a video, minus silent renders, teasers, tests and anything in episodes.overrides.json's
"exclude". "include" brings one back; "titles" and "series" rename. Titles, descriptions and
chapters come from the film's own release copy (release/description.md), so the page says
what YouTube says.

Each film is copied, not re-rendered: the index moved to the front of the file so it starts
playing at once (-movflags +faststart). One over the upload limit (wrangler puts objects of
up to 300 MB) is re-encoded at the bitrate that fits. Captions become WebVTT, which browsers
read. Keys carry the version (episodes/<slug>/v<n>/...), so a file never changes under a
key and can be cached for ever. Writes src/generated/episodes.json, which the page reads.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
sys.path.insert(0, str(ROOT))

import medialib  # noqa: E402

OUT = SITE / "src" / "generated" / "episodes.json"
OVERRIDES = SITE / "episodes.overrides.json"
CACHE = SITE / "private" / "episodes"          # gitignored: web-ready copies and the upload ledger
BUCKET = "zeanahlab-media"
UPLOAD_LIMIT = 290_000_000                      # under wrangler's single-put limit, with room

# Not films: renders kept for the record, tools and experiments. episodes.overrides.json adds to this.
NOT_FILMS = {
    "2v-masterclass-silent-backup", "testo", "presenter-all", "pvtwo-check", "triangle-authoring-demo",
    "byod", "byod-deepseek", "byod-styled", "tree-value-video", "launcher_trailer", "wheelchair1",
    "ep-dome-001-high-council", "sketch-gpt-nearly-level-s01e01", "all-domes-every-permutation",
}

# Series, first match wins: (pattern on the slug, series name).
SERIES = (
    (r"^sketch-claude-level-with-me-", "Level With Me"),
    (r"^storytime-", "Bedtime Stories"),
    (r"masterclass", "Masterclasses"),
    (r"^dome_(case|housing)", "The Dome Case"),
    (r"^cabin-", "Cabin World"),
)
SERIES_ORDER = ("Cabin World", "Films", "Level With Me", "Masterclasses", "Bedtime Stories", "The Dome Case", "Early films")


def ffprobe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", str(path)], capture_output=True, text=True)
    data = json.loads(r.stdout or "{}")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return {"duration": float(data.get("format", {}).get("duration", 0) or 0),
            "width": int(video.get("width", 0) or 0), "height": int(video.get("height", 0) or 0)}


def release_copy(folder: Path) -> dict:
    """Title, description and chapters from the film's own release copy, if it has one."""
    src = next((p for p in (folder / "release" / "description.md", folder / "description.md") if p.is_file()), None)
    if not src:
        return {}
    text = src.read_text(encoding="utf-8", errors="replace")
    title = ""
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if m:
        title = re.sub(r"\s+--\s+release copy$", "", m.group(1)).strip()
    block = re.search(r"##\s*YouTube\s*```\s*\n(.*?)```", text, re.S)
    body = block.group(1) if block else text
    desc = re.split(r"\n(?:In this film:|Chapters)\s*\n", body)[0].strip()
    chapters = [{"t": _seconds(t), "title": name.strip()} for t, name in re.findall(r"^(\d+:\d\d(?::\d\d)?)\s+(.+)$", body, re.M)]
    return {"title": title, "description": desc[:2000], "chapters": chapters}


def _seconds(stamp: str) -> int:
    parts = [int(x) for x in stamp.split(":")]
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def _pretty(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).strip().capitalize()


def series_of(slug: str, has_release: bool, overrides: dict) -> str:
    if slug in overrides.get("series", {}):
        return overrides["series"][slug]
    for pattern, name in SERIES:
        if re.search(pattern, slug):
            return name
    return "Films" if has_release else "Early films"


def catalogue() -> tuple[list[dict], list[tuple[str, str]]]:
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.is_file() else {}
    exclude = NOT_FILMS | set(overrides.get("exclude", []))
    include = set(overrides.get("include", []))
    # the newest iteration that has a finished main cut; a newer one without (a render that
    # never finished) is noted, not shown
    by_slug: dict[str, list[medialib.Output]] = {}
    for o in medialib.outputs():
        by_slug.setdefault(o.slug, []).append(o)
    latest: dict[str, medialib.Output] = {}
    episodes, skipped = [], []
    for slug, its in by_slug.items():
        its.sort(key=lambda o: -o.version)
        has_cut = [o for o in its if any("vertical" not in p.name and "teaser" not in p.name for p in o.folder.glob("*.mp4"))]
        if has_cut:
            latest[slug] = has_cut[0]
            if has_cut[0] is not its[0] and not slug.startswith(".") and "teaser" not in slug:
                skipped.append((f"{slug} v{its[0].version}", f"no finished main cut yet; v{has_cut[0].version} is shown"))
    for slug, o in sorted(latest.items(), key=lambda kv: kv[1].seq):
        if slug not in include:
            if slug.startswith("."):
                skipped.append((slug, "a silent render kept for the record")); continue
            if "teaser" in slug or "silent" in slug:
                skipped.append((slug, "a teaser or silent cut")); continue
            if slug in exclude:
                skipped.append((slug, "not a film (excluded)")); continue
        top = [p for p in o.folder.glob("*.mp4")]
        mains = [p for p in top if "vertical" not in p.name and "teaser" not in p.name]
        if not mains:
            skipped.append((slug, "no main cut at the top of its folder")); continue
        main = max(mains, key=lambda p: (p.stem in (slug, f"{slug}-v{o.version}"), p.stat().st_size))
        info = ffprobe(main)
        if info["duration"] < 20:
            skipped.append((slug, f"{info['duration']:.0f} s long")); continue
        vertical = next((p for p in top if "vertical" in p.name and "teaser" not in p.name), None)
        srt = main.with_suffix(".srt") if main.with_suffix(".srt").is_file() else None
        thumbs = sorted((o.folder / "release" / "thumbnails").glob("*.jpg")) + sorted(o.folder.glob("thumb-*.jpg"))
        copy = release_copy(o.folder)
        has_release = (o.folder / "release").is_dir()
        base = f"episodes/{slug}/v{o.version}"
        episodes.append({
            "slug": slug, "seq": o.seq, "version": o.version,
            "series": series_of(slug, has_release, overrides),
            "title": overrides.get("titles", {}).get(slug) or copy.get("title") or _pretty(slug),
            "description": copy.get("description", ""), "chapters": copy.get("chapters", []),
            "made": o.made.isoformat(), "duration": round(info["duration"], 1),
            "width": info["width"], "height": info["height"],
            "video": {"key": f"{base}/{slug}.mp4", "src": main.relative_to(ROOT).as_posix()},
            "vertical": {"key": f"{base}/{slug}-vertical.mp4", "src": vertical.relative_to(ROOT).as_posix()} if vertical else None,
            "captions": {"key": f"{base}/{slug}.vtt", "src": srt.relative_to(ROOT).as_posix()} if srt else None,
            "thumb": {"key": f"{base}/{slug}.jpg", "src": thumbs[0].relative_to(ROOT).as_posix() if thumbs else None},
        })
    ep_no = re.compile(r"-s(\d+)e(\d+)-")
    for e in episodes:
        m = ep_no.search(e["slug"])
        e["episode"] = f"S{int(m.group(1))}E{int(m.group(2))}" if m else None
    def number(e):
        m = re.match(r"S(\d+)E(\d+)", e["episode"] or "")
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    episodes.sort(key=lambda e: (SERIES_ORDER.index(e["series"]) if e["series"] in SERIES_ORDER else 99,
                                 number(e), -e["seq"] if e["series"] in ("Cabin World", "Films") else e["seq"]))
    return episodes, skipped


# ---------------------------------------------------------------- web-ready copies

def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{' '.join(cmd[:4])} ... failed:\n{r.stderr[-1500:]}")


def prepare_video(src: Path, out: Path, duration: float) -> None:
    if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.mp4")
    if src.stat().st_size <= UPLOAD_LIMIT:
        _run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c", "copy", "-movflags", "+faststart", str(tmp)])
    else:
        # the bitrate that fits, less the sound; never above the source's own
        kbps = int(UPLOAD_LIMIT * 8 / duration / 1000) - 160
        _run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "libx264", "-preset", "medium",
              "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.3)}k", "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-strict", "-2", "-b:a", "128k", "-movflags", "+faststart", str(tmp)])
    tmp.replace(out)


def srt_to_vtt(src: Path, out: Path) -> None:
    text = src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    text = re.sub(r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("WEBVTT\n\n" + text.strip() + "\n", encoding="utf-8")


def prepare_thumb(src: Path | None, video: Path, out: Path, duration: float) -> None:
    from PIL import Image
    out.parent.mkdir(parents=True, exist_ok=True)
    if src is None:
        frame = out.with_suffix(".frame.png")
        _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{duration * 0.1:.2f}", "-i", str(video), "-frames:v", "1", str(frame)])
        src = frame
    img = Image.open(src).convert("RGB")
    img.thumbnail((1280, 1280))
    img.save(out, "JPEG", quality=85)
    if src.name.endswith(".frame.png"):
        src.unlink()


def local_path(key: str) -> Path:
    return CACHE / key.removeprefix("episodes/")


def prepare(episodes: list[dict]) -> None:
    for e in episodes:
        print(f"{e['slug']} ...", flush=True)
        prepare_video(ROOT / e["video"]["src"], local_path(e["video"]["key"]), e["duration"])
        if e["vertical"]:
            prepare_video(ROOT / e["vertical"]["src"], local_path(e["vertical"]["key"]), e["duration"])
        if e["captions"]:
            srt_to_vtt(ROOT / e["captions"]["src"], local_path(e["captions"]["key"]))
        prepare_thumb(ROOT / e["thumb"]["src"] if e["thumb"]["src"] else None, ROOT / e["video"]["src"],
                      local_path(e["thumb"]["key"]), e["duration"])
        for part in ("video", "vertical"):
            if e[part]:
                e[part]["bytes"] = local_path(e[part]["key"]).stat().st_size


def upload(episodes: list[dict], remote: bool) -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    ledger_path = CACHE / f"uploaded-{'remote' if remote else 'local'}.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
    types = {".mp4": "video/mp4", ".vtt": "text/vtt", ".jpg": "image/jpeg"}
    for e in episodes:
        for part in ("video", "vertical", "captions", "thumb"):
            if not e[part]:
                continue
            key = e[part]["key"]
            f = local_path(key)
            size = f.stat().st_size
            if ledger.get(key) == size:
                continue
            print(f"  {key} ({size / 1e6:.1f} MB)", flush=True)
            r = subprocess.run([npx, "wrangler", "r2", "object", "put", f"{BUCKET}/{key}", "--file", str(f),
                                "--content-type", types[f.suffix], "--remote" if remote else "--local"],
                               cwd=SITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode:
                sys.exit(f"upload failed for {key}:\n{r.stderr[-1500:]}")
            ledger[key] = size
            ledger_path.write_text(json.dumps(ledger, indent=1), encoding="utf-8")


def write_manifest(episodes: list[dict]) -> None:
    public = []
    for e in episodes:
        e = json.loads(json.dumps(e))
        for part in ("video", "vertical", "captions", "thumb"):
            if e[part]:
                e[part].pop("src", None)
        public.append(e)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"_generated_by": "website/scripts/export_episodes.py -- do not edit",
                               "episodes": public}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(public)} episodes")


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--upload", action="store_true")
    where = ap.add_mutually_exclusive_group()
    where.add_argument("--local", action="store_true")
    where.add_argument("--remote", action="store_true")
    ap.add_argument("--only", help="just these slugs (comma separated), to try one")
    a = ap.parse_args()
    eps, skipped = catalogue()
    if a.only:
        eps = [e for e in eps if e["slug"] in a.only.split(",")]
    if not (a.prepare or a.upload):
        for e in eps:
            print(f"  {e['series']:16s} {e['episode'] or '':6s} {e['title'][:60]:60s} {e['duration'] / 60:5.1f} min  {e['slug']}")
        print(f"{len(eps)} episodes, {sum(e['duration'] for e in eps) / 3600:.1f} hours")
        for slug, why in skipped:
            print(f"  skipped {slug}: {why}")
        sys.exit(0)
    prepare(eps)
    if a.upload:
        if not (a.local or a.remote):
            sys.exit("--upload needs --local or --remote")
        upload(eps, a.remote)
    if not a.only:
        write_manifest(eps)
