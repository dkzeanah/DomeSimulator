#!/usr/bin/env bash
# v6, then the expanded franken lesson. One at a time.
set -u
cd /c/Users/Don/Desktop/DomeSim
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
echo "=== V6 ==="
py -3.12 "$S" hype6 deliverables/masterclass/frankendome-montage-v6.mp4 2>&1 | tail -6
echo "=== FRANKEN V2 ==="
py -3.12 "$S" franken deliverables/masterclass/frankendome-build-v2.mp4 2>&1 | tail -4
echo "=== BOTH DONE ==="
