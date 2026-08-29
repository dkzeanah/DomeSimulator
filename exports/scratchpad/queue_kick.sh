#!/usr/bin/env bash
# Wait for the franken-v2 export to finish, then export the campaign film.
# Exports run one at a time on purpose: three concurrent ones once made the
# speech endpoint fail DNS for all three.
set -u
cd /c/Users/Don/Desktop/DomeSim
EX="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
TARGET=deliverables/masterclass/frankendome-build-v2.mp4

echo "=== waiting for franken-v2 ==="
for i in $(seq 1 400); do
  if [ -f "$TARGET" ]; then
    a=$(stat -c %s "$TARGET" 2>/dev/null || echo 0)
    sleep 20
    b=$(stat -c %s "$TARGET" 2>/dev/null || echo 0)
    if [ "$a" = "$b" ] && [ "$a" != "0" ]; then
      echo "franken-v2 settled at $b bytes"
      break
    fi
  fi
  sleep 20
done

echo "=== KICKSTARTER ==="
py -3.12 "$EX" kick deliverables/masterclass/dome-kickstarter.mp4 2>&1 | tail -8
echo "=== done ==="
