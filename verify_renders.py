"""Check that an exported video is whole, not merely plausible.

Duration alone will not catch a truncated render: a bad export once
reported the right length and decoded cleanly while holding 634 frames
against 920 seconds of audio. Counting frames catches it.

    py -3.12 verify_renders.py
    py -3.12 verify_renders.py deliverables/masterclass/dome-kickstarter-v2.mp4
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DEFAULTS = (
    "deliverables/masterclass/frankendome-build-v2.mp4",
    "deliverables/masterclass/dome-kickstarter.mp4",
    "deliverables/masterclass/dome-kickstarter-v2.mp4",
)


def probe(path: Path, stream: str, entries: str, extra=()) -> str:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream, *extra,
         "-show_entries", entries, "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    return result.stdout.strip().split("\n")[0] if result.stdout else ""


def check(path: Path) -> bool:
    if not path.exists():
        print(f"  MISSING  {path}")
        return False

    video = float(probe(path, "v:0", "stream=duration") or 0.0)
    audio = float(probe(path, "a:0", "stream=duration") or 0.0)
    frames = int(probe(path, "v:0", "stream=nb_read_frames",
                       ("-count_frames",)) or 0)

    drift = abs(video - audio)
    # A whole render sits at 30 fps. Anything under 29 means frames were
    # dropped or the mux cut the picture short against a full soundtrack.
    floor = video * 29.0
    ok = drift < 2.0 and frames > floor and video > 0.0

    print(f"  {'OK  ' if ok else 'FAIL'}  {path.name}")
    print(f"          {video/60:.1f} min   {frames:,} frames   "
          f"{frames/video if video else 0:.2f} fps")
    print(f"          drift {drift:.3f}s (<2.0)   "
          f"frames vs floor {frames:,} > {floor:,.0f}")
    return ok


def main() -> int:
    targets = sys.argv[1:] or list(DEFAULTS)
    print("RENDER VERIFICATION")
    results = [check(Path(name)) for name in targets]
    passed = sum(results)
    print(f"\n{passed} of {len(results)} whole")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
