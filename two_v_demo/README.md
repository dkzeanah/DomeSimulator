# 2V Geodesic Masterclass

This is a standalone ModernGL teaching world. It does not import or launch the
assembly-line simulation or the main Dome Creator world.

## Run

```powershell
py -3.12 -m pip install -r two_v_demo/requirements.txt
py -3.12 launcher.py           # 2V Masterclass tab — see below
py -3.12 two_v_masterclass.py  # direct run, fullscreen presenter mode
```

This tool no longer takes command-line flags. Every mode that used to be
a `--flag` is a field on the launcher's **2V Masterclass** tab: pick an
**Action** (run / selftest / report / shots / export_video /
voice_preview / list_voices / narration_only / script / build_packet),
fill in the fields relevant to it, and click **Launch**. Former flags
map onto that tab like this:

| Former flag | Launcher field |
| --- | --- |
| `--fullscreen` | Fullscreen checkbox |
| `--selftest` / `--report` | Action = selftest / report |
| `--shots 0,45,95` | Action = shots + Still times |
| `--export-video FILE` | Action = export_video + Export MP4 |
| `--no-narration` | No narration checkbox |
| `--local-narration-plan JSON` | Local Voice Studio narration plan |
| `--voice` / `--voice-rate` / `--voice-pitch` / `--voice-volume` | Voice / Rate / Pitch / Volume |
| `--voice-preview MP3` | Action = voice_preview + its path |
| `--list-voices` / `--voice-locale` | Action = list_voices + Voice locale |
| `--narration-only M4A` | Action = narration_only + its path |
| `--ffmpeg` / `--ffprobe` | their path fields |
| `--script PATH` | Action = script + its path |
| `--build-packet DIR` (+ `--radius-in`, `--connector-deduction-in`) | Action = build_packet + Output directory / Radius / Connector deduction |
| `--fps` / `--size` | FPS / Size WxH |

The video exporter requires `ffmpeg` on `PATH` (or the ffmpeg path field
filled in). It renders the complete, deterministic lesson timeline at
1920x1080 and includes the same equations, captions, camera moves, and
geometry shown in the live app. By default it generates a natural neural
teacher voice, extends each chapter to fit the measured speech duration,
loudness-normalizes the result, and muxes it into the MP4. It also
writes the separate AAC narration track, timed voiceover script, chapter
MP3 stems, and a YouTube-ready `.srt` subtitle file.

The default is Microsoft Edge's warm, confident
`en-US-AndrewMultilingualNeural` voice at a relaxed `-3%` rate. No API key is
needed, but the narration text is sent to Microsoft's online speech service.

Current FFmpeg builds use the `adelay` and `loudnorm` filter mixer. If those
filters are absent—as with the 2013 FFmpeg build bundled by some Python
packages—the exporter automatically decodes the chapter files to timed PCM,
inserts silence itself, encodes AAC, and then embeds that track in the MP4.

For a voice profile that stays local, use Local Voice Studio's Dome
Narration tab: it writes an AAC track and `narration-plan.json`, and the
2V Masterclass tab's "Local Voice Studio narration plan" field points
the exporter at that existing track instead of calling the Edge speech
service.

The build-packet action runs without graphics. It exports CSV cut lists,
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
