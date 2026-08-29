#!/usr/bin/env bash
# Wait for v4 to clear, then v5. Never two at once.
set -u
cd /c/Users/Don/Desktop/DomeSim
while [ ! -f deliverables/masterclass/frankendome-montage-v4.mp4 ]; do sleep 20; done
echo "v4 done, starting v5"
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
py -3.12 "$S" hype5 deliverables/masterclass/frankendome-montage-v5.mp4 2>&1 | tail -5
echo "=== V5 DONE ==="
