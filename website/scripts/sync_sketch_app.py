"""Copy the local modeller's page into the site, as public/sketch-app/ (zeanahlab.com/sketch-app/).

    py -3.12 scripts/sync_sketch_app.py

The modeller (sketch_claude/static: index.html, app.js, app.css and three.js) is copied as it is,
with its /static/ paths pointed at /sketch-app/, and public/sketch-app/web-shim.js (kept here, not
copied) loaded first to stand in for the Python server. The grid index the shim reads is
src/generated/sketch-grid.json (sketch_claude/web_catalogue.py). Run this after changing the
modeller's page, so the site never carries a stale copy of it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SRC = SITE.parent / "sketch_claude" / "static"
OUT = SITE / "public" / "sketch-app"
NOTE = "<!-- copied from sketch_claude/static/index.html by website/scripts/sync_sketch_app.py: edit that file, then re-run -->\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vendor").mkdir(exist_ok=True)
    for f in ("three.module.min.js", "OrbitControls.js", "three-LICENSE.txt"):
        shutil.copyfile(SRC / "vendor" / f, OUT / "vendor" / f)
    js = (SRC / "app.js").read_text(encoding="utf-8").replace('"/static/', '"/sketch-app/')
    # imported, not merely loaded first: an import waits for the shim's top-level await (the grid)
    js = 'import "/sketch-app/web-shim.js";\n' + js
    (OUT / "app.js").write_text("// copied from sketch_claude/static/app.js by website/scripts/sync_sketch_app.py: edit that file, then re-run\n" + js, encoding="utf-8")
    shutil.copyfile(SRC / "app.css", OUT / "app.css")
    html = (SRC / "index.html").read_text(encoding="utf-8").replace('"/static/', '"/sketch-app/')
    assert '<script type="module" src="/sketch-app/app.js"></script>' in html, "the modeller's page no longer loads app.js the way this script expects"
    html = html.replace("<title>", "<title>Dome Sketch | Zeanah Lab -- ", 1)
    (OUT / "index.html").write_text(NOTE + html, encoding="utf-8")
    shutil.copyfile(SITE / "src" / "generated" / "sketch-grid.json", OUT / "grid.json")
    print(f"copied the modeller into {OUT.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
