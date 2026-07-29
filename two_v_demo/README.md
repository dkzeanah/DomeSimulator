# 2V Geodesic Masterclass

This is a standalone ModernGL teaching world. It does not import or launch the
assembly-line simulation or the main Dome Creator world.

## Run

```powershell
py -3.12 -m pip install -r two_v_demo/requirements.txt
py -3.12 two_v_masterclass.py
```

Useful modes:

```powershell
py -3.12 two_v_masterclass.py --fullscreen
py -3.12 two_v_masterclass.py --selftest
py -3.12 two_v_masterclass.py --report
py -3.12 two_v_masterclass.py --script two_v_demo_output/voiceover.md
py -3.12 two_v_masterclass.py --build-packet two_v_demo_output/build
py -3.12 two_v_masterclass.py --build-packet two_v_demo_output/build `
    --radius-in 116.361744 --connector-deduction-in 1.25
py -3.12 two_v_masterclass.py --shots 0,45,95
py -3.12 two_v_masterclass.py --export-video 2v-masterclass.mp4
```

The video exporter requires `ffmpeg` on `PATH`. It renders the complete,
deterministic lesson timeline at 1920x1080 and includes the same equations,
captions, camera moves, and geometry shown in the live app. By default it now
generates a natural neural teacher voice, extends each chapter to fit the
measured speech duration, loudness-normalizes the result, and muxes it into the
MP4. It also writes the separate AAC narration track, timed voiceover script,
chapter MP3 stems, and a YouTube-ready `.srt` subtitle file.

The default is Microsoft Edge's warm, confident
`en-US-AndrewMultilingualNeural` voice at a relaxed `-3%` rate. No API key is
needed, but the narration text is sent to Microsoft's online speech service.

```powershell
# Audition the default voice before rendering:
py -3.12 two_v_masterclass.py --voice-preview two_v_demo_output/voice.mp3

# See currently available US English neural voices:
py -3.12 two_v_masterclass.py --list-voices

# A friendly female teaching voice:
py -3.12 two_v_masterclass.py --export-video 2v-ava.mp4 `
    --voice en-US-AvaMultilingualNeural --voice-rate=-4%

# Generate the complete narration track without rendering video:
py -3.12 two_v_masterclass.py --narration-only two_v_demo_output/narration.m4a

# Preserve the original silent-video behavior:
py -3.12 two_v_masterclass.py --export-video 2v-silent.mp4 --no-narration
```

If FFmpeg is not on `PATH`, pass `--ffmpeg C:\path\to\ffmpeg.exe`; `ffprobe`
is normally discovered beside it, or can be supplied with `--ffprobe`.
Current FFmpeg builds use the `adelay` and `loudnorm` filter mixer. If those
filters are absent—as with the 2013 FFmpeg build bundled by some Python
packages—the exporter automatically decodes the chapter files to timed PCM,
inserts silence itself, encodes AAC, and then embeds that track in the MP4.

For a voice profile that stays local, use `local_voice_studio.py`. Its Dome
Narration tab writes an AAC track and `narration-plan.json`; the exporter reads
the measured chapter durations and muxes that existing track without calling
the Edge speech service:

```powershell
py -3.12 two_v_masterclass.py --export-video 2v-my-voice.mp4 `
    --local-narration-plan C:\path\to\narration-plan.json
```

The build-packet command runs without graphics. It exports CSV cut lists,
triangle details, hub coordinates, edge connectivity, a calculation workbook,
an inch-unit OBJ for CAD, a JSON manifest, and a field guide. Connector
deduction means the total shortening across both ends of one member.

## Presentation controls

- `Space`: play/pause the lesson
- `Left` / `Right`: previous/next chapter
- `Home`: restart
- `1` through `9`, `0`: jump to chapters 1 through 10
- Mouse drag: orbit the camera
- Mouse wheel: zoom
- `R`: restore the chapter camera
- `X`: X-ray sphere
- `U`: switch dimension display between inches and metric
- `S`: save a screenshot in `two_v_demo_output`
- `F11`: toggle fullscreen
- `Esc`: leave fullscreen or quit

## Measurement convention

The math engine uses `SHORT` and `LONG`, because published calculators use
inconsistent A/B naming. The lesson explicitly shows the supplied convention
as A = 72 in LONG and B = 63.5 in SHORT.

All theoretical member lengths are hub-center to hub-center. Physical stock
cut lengths require a connector deduction measured for the chosen hub system.
