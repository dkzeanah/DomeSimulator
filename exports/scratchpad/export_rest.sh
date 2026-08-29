#!/usr/bin/env bash
# Export the two remaining lessons one after the other, never at the same
# time: the speech endpoint throttles hard when asked in parallel.
set -u
cd /c/Users/Don/Desktop/DomeSim
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
echo "=== ZOME ==="
py -3.12 "$S" zome deliverables/masterclass/zome-construction-masterclass.mp4
echo "zome exit: $?"
echo "=== BUILD ==="
py -3.12 "$S" build deliverables/masterclass/dome-construction-masterclass.mp4
echo "build exit: $?"
