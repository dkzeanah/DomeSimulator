# Linseed Oil for a Dome — production handoff

The film is composed as `cabin_linseed_oil`: seventeen narrated chapters in the
Cabin World, approximately ten minutes before the standard inserted segments.
It uses the existing solver dome, seam specimen, cameras, synthesized music and
standard release pipeline. It is registered in the launcher for video and stills.

**Current status: composed and checked; not rendered.** The other
`cabin_seam_climate` render was active during this work (including a restart).
The supplied builder guide requires one GPU job at a time and visual inspection
of every chapter before rendering. Consequently no GPU stills or MP4 were
started for this film. The checks below do not constitute visual approval.

## Review files

- [Film script](film-script.md): narration and on-screen equations, generated from the lesson.
- [Source audit](source-audit.md): all twenty original tips, timestamp links, decisions and verification sources.
- [Cleaned source transcript](source-transcript-cleaned.txt): overlapping rolling captions deduplicated from library record 1629.
- [Facts report](facts-report.txt): constants, kinds, reasons, calculations and exclusions.
- [Validation output](validation.txt): actual check results, including any existing global failure.
- [Registration diff](registration.diff): additions to the four existing files, relative to their pre-task contents.

## Code changes

New production files:

- `two_v_demo/linseed_oil.py`: inputs, calculation functions, twenty-tip evidence map and facts selftest.
- `two_v_demo/lesson_cabin_linseed_oil.py`: narration, workshop objects, painters, cameras and scene selftest.

Existing files changed by small additions only:

- `two_v_demo/lesson_registry.py`: import and lesson entry.
- `two_v_demo/deliverables.py`: versioned-output registration with composition enabled.
- `render_presets.py`: video and chapter-stills presets.
- `two_v_demo/release.py`: film-specific hashtags.

Supporting files are in this folder. `build_handoff.py` regenerates the review
documents and checks without rendering. `registration-before.json` is the
pre-edit baseline for the task-specific diff. No commit was made. No source
video, voice profile, original lesson, existing deliverable or source database
was modified by this work.

## Commands, from the DomeSim folder

Run these in order, with the other render finished before command three:

```powershell
py -3.12 -m two_v_demo.linseed_oil
py -3.12 -c "from two_v_demo.lesson_registry import LESSONS; LESSONS['cabin_linseed_oil'].selftest(); print('ok')"
py -3.12 -m rerender stills cabin_linseed_oil
py -3.12 -m rerender render cabin_linseed_oil
```

Expected results:

1. A facts report with no assertion error: 120 reference members, approximately
   664.31 square feet in the flat-face planning envelope, 4.37 US gallons including
   the example allowance, and 8.0 hours of estimated active application labour.
2. `ok`, after the scene and camera checks.
3. One still per chapter in `two_v_demo_output/cabin_linseed_oil/`. Open and inspect
   every PNG. Check subject framing, label overlap, pine/prop occlusion and declared
   inputs. Fix the new lesson if necessary before command four. Also review portrait
   stills using `--size 1080x1920`; preserve the landscape stills in a separate review
   folder before making that second set, since the standard still command uses the
   same lesson output directory.
4. The standard exporter creates the landscape and phone cuts, release folder and
   teaser. It selects a fresh versioned filename if the output already exists.
   Confirm all outputs, caption synchronization and end segments before calling
   the film finished. Review status belongs to the owner.

The installed interpreter used for the checks is
`C:\Users\Don\AppData\Local\Python\pythoncore-3.12-64\python.exe`.
If `py` is unavailable in an agent shell, invoke that executable with PowerShell's
`&` operator. No dependency installation is required in that environment.

Expected video target: `deliverables/masterclass/linseed-oil-for-a-dome.mp4`,
plus `-vertical.mp4`. Expected release folder:
`deliverables/releases/linseed-oil-for-a-dome/`. None is claimed to exist yet.

## Inputs still needing a real job measurement

The two coats, two flat faces, 350 sq ft/US gallon per coat, 15 percent handling
allowance and two minutes per member per coat are explicitly illustrative.
The area includes the model's stock-length allowance and excludes curved backs,
end cuts, panels, floors and trim. Subtract uncoated bonding/sealing lands and
measure the surfaces actually selected. The coverage and labour examples are
not measured product performance, a purchase recommendation or a savings claim.
The product-specific timings are labelled manufacturer claims, not universal
linseed-oil instructions. No wood moisture percentage, service-life promise,
structural strength increase or waterproofing rating is invented.
