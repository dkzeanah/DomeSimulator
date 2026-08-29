#!/usr/bin/env bash
# One at a time: the speech endpoint throttles hard when asked in parallel.
set -u
cd /c/Users/Don/Desktop/DomeSim
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
echo "=== CUTS ==="
py -3.12 "$S" cuts deliverables/masterclass/hubless-compound-cut.mp4 2>&1 | tail -4
echo "=== FRANKEN ==="
py -3.12 "$S" franken deliverables/masterclass/frankendome-build.mp4 2>&1 | tail -4
echo "=== BOTH DONE ==="
