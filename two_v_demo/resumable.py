"""Renders that survive being stopped, and MKV to MP4.

A film used to render into one hidden MP4. An MP4 writes its index last, so a
render that died at minute forty left a file nothing could play, and the
forty minutes were gone. Now every chapter renders into its own MKV in a work
folder beside the target:

* an MKV is playable up to its last written frame, so even a chapter cut off
  part-way can be looked at;
* a chapter whose encoder finished cleanly gets a ``.done`` marker, and a
  render started again with the same job skips every chapter that has one --
  the film carries on from the chapter it stopped in;
* when the last chapter is done, the chunks are joined without re-encoding a
  frame, the narration goes on as before, and the work folder is removed.

"The same job" is a fingerprint of everything that decides the pictures: the
lesson, the narration plan's timing, the size, the frame rates, the chapter
window, the orientation and the encoder. Change any of them and the work
folder is a different one. Code changes are *not* in the fingerprint -- a fix
to a painter made between two runs shows only in the chapters rendered after
it -- so a ticket can say ``"fresh_render": true`` to throw the chunks away.

The deliverable stays an MP4: Instagram and Facebook want MP4 and YouTube
takes either. :func:`to_mp4` turns any MKV into one by stream copy (no
re-encode, seconds not hours), and :func:`preview` stitches the finished
chunks of an interrupted render into a watchable MP4.

    py -3.12 -m two_v_demo.resumable to-mp4 path/to/film.mkv
    py -3.12 -m two_v_demo.resumable list
    py -3.12 -m two_v_demo.resumable preview deliverables/masterclass/film.mp4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _ffmpeg(ffmpeg: str | None = None) -> str:
    if ffmpeg:
        return ffmpeg
    from .audio import resolve_executable
    return resolve_executable("ffmpeg")


def fingerprint(**parts) -> str:
    """Twelve hex characters naming one job."""
    text = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def work_dir(target: Path, key: str) -> Path:
    return Path(target).parent / f".{Path(target).stem}-chunks-{key}"


def chunks(chapter_durations, capture_fps: int, first_frame: int, total_frames: int) -> list[tuple[int, int, int]]:
    """(chapter index, first frame, end frame) for every chapter in the window."""
    out, clock = [], 0.0
    for i, d in enumerate(chapter_durations):
        f0 = int(round(clock * capture_fps))
        clock += d
        f1 = int(round(clock * capture_fps))
        a, b = max(f0, first_frame), min(f1, total_frames)
        if b > a:
            out.append((i, a, b))
    if out and out[-1][2] < total_frames:            # rounding: the last chunk runs to the end
        i, a, _b = out[-1]
        out[-1] = (i, a, total_frames)
    return out


def chunk_path(work: Path, index: int) -> Path:
    return work / f"chapter-{index + 1:03d}.mkv"


def _done_path(work: Path, index: int) -> Path:
    return work / f"chapter-{index + 1:03d}.done"


def is_done(work: Path, index: int, first: int, end: int) -> bool:
    mark, video = _done_path(work, index), chunk_path(work, index)
    if not (mark.is_file() and video.is_file() and video.stat().st_size > 0):
        return False
    try:
        data = json.loads(mark.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return data.get("first") == first and data.get("end") == end


def mark_done(work: Path, index: int, first: int, end: int) -> None:
    _done_path(work, index).write_text(json.dumps({"first": first, "end": end}), encoding="utf-8")


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in out.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class Lock:
    """One render per work folder: a second one of the same job would write
    the same chunks underneath the first."""

    def __init__(self, work: Path):
        self.path = Path(work) / "render.lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            try:
                pid = int(self.path.read_text().strip() or 0)
            except ValueError:
                pid = 0
            if pid != os.getpid() and _alive(pid):
                raise RuntimeError(f"another render (pid {pid}) is writing {self.path.parent}")
        self.path.write_text(str(os.getpid()))
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)
        return False


def join(paths: list[Path], target: Path, ffmpeg: str | None = None) -> Path:
    """Join pieces without re-encoding. Listing paths are absolute and ASCII:
    ffmpeg resolves a concat entry against the listing's own folder."""
    target = Path(target)
    listing = target.with_name(target.name + ".chunks.txt")
    listing.write_text("".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in paths), encoding="ascii")
    extra = ["-movflags", "+faststart"] if target.suffix.lower() in (".mp4", ".m4v", ".mov") else []
    try:
        subprocess.run([_ffmpeg(ffmpeg), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-c", "copy", *extra, str(target)], check=True, capture_output=True)
    finally:
        listing.unlink(missing_ok=True)
    return target


def _free(path: Path) -> Path:
    from .deliverables import next_version_path
    return next_version_path(path) if path.exists() else path


def _has_subtitles(src: Path) -> bool:
    from .audio import resolve_executable
    try:
        ffprobe = resolve_executable("ffprobe")
    except Exception:  # noqa: BLE001
        return False
    out = subprocess.run([ffprobe, "-v", "error", "-select_streams", "s", "-show_entries", "stream=index",
                          "-of", "csv=p=0", str(src)], capture_output=True, text=True)
    return bool(out.stdout.strip())


def to_mp4(src: Path, out: Path | None = None, ffmpeg: str | None = None) -> Path:
    """An MKV (or any container) as an MP4, by stream copy. Never overwrites:
    an existing name gets the next -vN."""
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)
    target = _free(Path(out) if out else src.with_suffix(".mp4"))
    subs = ["-c:s", "mov_text"] if _has_subtitles(src) else []
    subprocess.run([_ffmpeg(ffmpeg), "-y", "-v", "error", "-i", str(src), "-map", "0", "-c", "copy", *subs,
                    "-movflags", "+faststart", str(target)], check=True, capture_output=True)
    return target


def renders(root: Path = ROOT / "deliverables") -> list[tuple[Path, int, int]]:
    """Every unfinished render's work folder, with chunks done and chunks there."""
    out = []
    for work in sorted(root.rglob(".*-chunks-*")):
        if work.is_dir():
            done = len(list(work.glob("*.done")))
            there = len(list(work.glob("*.mkv")))
            out.append((work, done, there))
    return out


def preview(target: Path, out: Path | None = None) -> Path:
    """The finished chapters of an interrupted render of ``target``, silent,
    as one MP4 to watch."""
    target = Path(target)
    folders = [w for w, _d, _t in renders(target.parent) if w.name.startswith(f".{target.stem}-chunks-")]
    if not folders:
        raise FileNotFoundError(f"no unfinished render of {target.name}")
    work = max(folders, key=lambda w: w.stat().st_mtime)
    done = sorted(p.with_suffix(".mkv") for p in work.glob("*.done"))
    if not done:
        raise RuntimeError(f"{work.name} has no finished chapter yet")
    return join(done, _free(Path(out) if out else target.with_name(f"{target.stem}-partial.mp4")))


def discard(work: Path) -> None:
    shutil.rmtree(work, ignore_errors=True)


def validate_resumable() -> None:
    """Chunks, joins and the converter, on a synthetic clip."""
    import tempfile
    ff = _ffmpeg()
    assert chunks([1.0, 2.0, 1.5], 10, 0, 45) == [(0, 0, 10), (1, 10, 30), (2, 30, 45)]
    assert chunks([1.0, 2.0, 1.5], 10, 10, 30) == [(1, 10, 30)]
    assert fingerprint(a=1, b="x") == fingerprint(b="x", a=1) != fingerprint(a=2, b="x")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / ".film-chunks-abc"
        work.mkdir()
        parts = []
        for i, (rate, secs) in enumerate(((10, 1), (10, 2))):
            p = chunk_path(work, i)
            subprocess.run([ff, "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size=160x90:rate={rate}",
                            "-t", str(secs), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)], check=True)
            mark_done(work, i, i * 10, i * 10 + secs * 10)
            parts.append(p)
        assert is_done(work, 1, 10, 30) and not is_done(work, 1, 10, 31)
        joined = join(parts, Path(tmp) / "film.mkv")
        mp4 = to_mp4(joined)
        again = to_mp4(joined)
        assert mp4.name == "film.mp4" and again.name != mp4.name, (mp4, again)
        from .audio import resolve_executable
        probe = subprocess.run([resolve_executable("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
        assert abs(float(probe.stdout.strip()) - 3.0) < 0.2, probe.stdout
        with Lock(work):
            assert (work / "render.lock").is_file()
        assert not (work / "render.lock").exists()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="resumable", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("to-mp4", help="an MKV as an MP4, by stream copy")
    p.add_argument("src", nargs="+")
    p.add_argument("--out", default="")
    sub.add_parser("list", help="unfinished renders and how far each got")
    p = sub.add_parser("preview", help="the finished chapters of an unfinished render, as an MP4")
    p.add_argument("target")
    sub.add_parser("check", help="run the self-test")
    args = parser.parse_args(argv)
    if args.cmd == "to-mp4":
        for src in args.src:
            print(to_mp4(Path(src), Path(args.out) if args.out and len(args.src) == 1 else None))
    elif args.cmd == "list":
        rows = renders()
        if not rows:
            print("no unfinished renders")
        for work, done, there in rows:
            print(f"{work.relative_to(ROOT)}: {done} chapter(s) finished, {there} started")
    elif args.cmd == "preview":
        print(preview(Path(args.target)))
    else:
        validate_resumable()
        print("resumable ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
