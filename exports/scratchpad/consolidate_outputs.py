"""Move presenter_output under deliverables, verifying before deleting.

Two renderers were writing to two places: the Presenter (presenter/engine.py)
to presenter_output/, and the Masterclass engine to deliverables/masterclass/.
This puts both under deliverables/ and repoints the Presenter's default.

Copy first, verify every file by size, and only then remove the source --
397 MB of finished renders is not something to move with a rename and a
hope.
"""

import shutil
import sys
from pathlib import Path

SRC = Path(r"C:\Users\Don\Desktop\DomeSim\presenter_output")
DST = Path(r"C:\Users\Don\Desktop\DomeSim\deliverables\presenter")

if not SRC.is_dir():
    print("presenter_output is already gone; nothing to do")
    sys.exit(0)

source_files = {
    p.relative_to(SRC): p.stat().st_size
    for p in SRC.rglob("*") if p.is_file()
}
print(f"copying {len(source_files)} files ({sum(source_files.values())/1e6:.0f} MB)")

DST.mkdir(parents=True, exist_ok=True)
for relative in source_files:
    target = DST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == source_files[relative]:
        continue
    shutil.copy2(SRC / relative, target)

# Verify every single file arrived at the right size before removing any.
missing = []
wrong = []
for relative, size in source_files.items():
    target = DST / relative
    if not target.is_file():
        missing.append(str(relative))
    elif target.stat().st_size != size:
        wrong.append(str(relative))

if missing or wrong:
    print(f"NOT removing the source: {len(missing)} missing, "
          f"{len(wrong)} wrong size")
    for name in (missing + wrong)[:10]:
        print(f"  {name}")
    sys.exit(1)

print(f"verified all {len(source_files)} files at {DST}")
shutil.rmtree(SRC)
print(f"removed {SRC}")
