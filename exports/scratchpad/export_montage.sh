#!/usr/bin/env bash
# Wait for the franken export to clear, then re-export the montage with
# the call to action. Never two at once: the speech endpoint throttles.
set -u
cd /c/Users/Don/Desktop/DomeSim
while [ ! -f deliverables/masterclass/frankendome-build.mp4 ]; do sleep 20; done
echo "franken done, starting montage"
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
rm -f deliverables/masterclass/frankendome-montage.mp4
py -3.12 "$S" hype deliverables/masterclass/frankendome-montage.mp4 2>&1 | tail -5
echo "=== MONTAGE DONE ==="
