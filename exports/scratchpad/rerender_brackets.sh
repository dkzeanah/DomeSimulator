#!/usr/bin/env bash
# Re-render everything that draws a bracket, plus the new campaign film.
# One at a time: three concurrent exports once made the speech endpoint
# fail DNS for all three.
set -u
cd /c/Users/Don/Desktop/DomeSim
EX="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
D=deliverables/masterclass

echo "=== 1/3 FRANKEN (3 bracket chapters) ==="
py -3.12 "$EX" franken "$D/frankendome-build-v2.mp4" 2>&1 | tail -5

echo "=== 2/3 KICKSTARTER v1 (1 bracket chapter) ==="
py -3.12 "$EX" kick "$D/dome-kickstarter.mp4" 2>&1 | tail -5

echo "=== 3/3 KICKSTARTER v2 (new) ==="
py -3.12 "$EX" kick2 "$D/dome-kickstarter-v2.mp4" 2>&1 | tail -5

echo "=== ALL DONE ==="
