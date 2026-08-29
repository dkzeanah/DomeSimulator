#!/usr/bin/env bash
# The speech endpoint has been intermittently unreachable all session.
# Keep trying: the chapter cache means each attempt resumes, so a run that
# gets three more clips through is progress even if it then fails again.
cd /c/Users/Don/Desktop/DomeSim
S="C:/Users/Don/AppData/Local/Temp/claude/C--Users-Don-Desktop-DomeSim/bb2f0342-d0bb-4db9-b958-9985ff7ceb8f/scratchpad/export_lesson.py"
OUT=deliverables/masterclass/dome-construction-masterclass.mp4
for attempt in 1 2 3 4 5 6; do
  echo "=== attempt $attempt ==="
  if [ -f "$OUT" ]; then echo "already built"; break; fi
  py -3.12 "$S" build "$OUT" 2>&1 | tail -3
  if [ -f "$OUT" ]; then echo "SUCCESS on attempt $attempt"; break; fi
  ls deliverables/masterclass/dome-construction-masterclass-voice-*/ | wc -l
  sleep 180
done
