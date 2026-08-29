# Local Voice Studio

Local Voice Studio is a standalone Windows-first program for collecting voice
recordings you own, curating a clean speech dataset, creating a locked local
voice profile, and generating speech on your computer. It does not use a hosted
inference API, login, telemetry, cloud database, or share server.

It is separate from Dome Creator, the assembly line, and the standalone
masterclass lessons. Its only integration is an explicit narration-plan file
that the masterclass video exporter can consume.

## What “building my voice” means

Do not start by training a modern text-to-speech foundation model from random
weights. That requires a large speech corpus and much more compute than a
6 GB GTX 1660 Ti. The practical sequence is:

1. Record and curate your own clean speech.
2. Build a 10–20 second reference **voice profile**.
3. Use Chatterbox Turbo locally for immediate reference-conditioned cloning.
4. Collect 30–60 clean minutes if you later want a serious fine-tune.
5. Fine-tune compatible pretrained weights only after reviewing their license.

The program calls this **profile creation** or **fine-tuning**, not training a
foundation model from scratch.

## Install on Windows

Python 3.11 is the safest choice for the optional Chatterbox package.

The guided setup script creates a project-local virtual environment:

```powershell
.\local_voice_studio\setup-windows.ps1
# Include Chatterbox and faster-whisper:
.\local_voice_studio\setup-windows.ps1 -WithLocalAI
```

If the script reports that `py` is missing, install 64-bit Python 3.11 from
python.org with Tcl/Tk and the Python launcher enabled. The Codex test runtime
is sufficient for command-line self-tests but does not include a usable Tk
desktop runtime.

Manual setup:

```powershell
cd C:\Users\Don\Desktop\DomeSim
py -3.11 -m venv .venv-voice
.\.venv-voice\Scripts\python.exe -m pip install --upgrade pip
.\.venv-voice\Scripts\python.exe -m pip install -r .\local_voice_studio\requirements-core.txt
```

The core install supports the GUI, recording, importing, quality checks,
manual transcripts, profile creation, and F5 dataset export.

For local neural generation and transcription:

```powershell
.\.venv-voice\Scripts\python.exe -m pip install -r .\local_voice_studio\requirements-local-ai.txt
```

If you have an NVIDIA GPU, also re-install PyTorch from its CUDA index —
chatterbox-tts hard-pins `torch==2.6.0`/`torchaudio==2.6.0`, but the plain
PyPI index serves a CPU-only build of that exact pin even on a CUDA-capable
machine ([resemble-ai/chatterbox#95](https://github.com/resemble-ai/chatterbox/issues/95)):

```powershell
.\.venv-voice\Scripts\python.exe -m pip uninstall -y torch torchaudio
.\.venv-voice\Scripts\python.exe -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
```

`setup-windows.ps1 -WithLocalAI` (above) does this step automatically,
skipping it when no NVIDIA GPU is detected. Confirm it worked from the
launcher's Local Voice Studio tab with Action set to `diagnose`, or from
the Project tab's hardware panel once the app is open — either should
show CUDA as available.

Chatterbox/PyTorch installation can be large. The first synthesis also
downloads the selected model weights from their named upstream source. That is
a model download, not hosted TTS: after weights are cached, audio inference is
local. To force cached-only operation:

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
.\.venv-voice\Scripts\python.exe .\local_voice_studio.py
```

FFmpeg and ffprobe must be on `PATH` for importing compressed audio and
building dome narration.

## Dome Narration: which lesson

The **Dome Narration** tab has a **Lesson** picker covering all eight
masterclass lessons, because they are different lengths and each needs its
own set of chapter clips:

| Lesson | Chapters to synthesize |
| --- | --- |
| 2V Geodesic Masterclass | 14 |
| 2V Dome Construction Masterclass | 46 |
| Hexagonal Dome Masterclass | 20 |
| Zome Construction Masterclass | 19 |
| Assembly Line Energy Masterclass | 24 |
| The Compound Cut, Both Machines | 18 |
| The Franken-Dome | 13 |
| Frankendome | 36 |

Clips are cached per lesson *and* per voice profile, under
`outputs/dome/<lesson>-<profile>/`, so switching between lessons or
profiles never overwrites work you have already generated. The lesson key
is written into `narration-plan.json`, and the renderer reads it back from
there, so a plan can never be rendered against a lesson with a different
chapter count.

This route contacts no online speech service at any point. It is also the
route to use when the cloud narration endpoint is unreachable, which does
happen -- see `docs/video-pipeline-reference.md` section 8.

## Run

This tool no longer takes command-line flags; launch and configure it
from the consolidated GUI (project folder, self-test, diagnose):

```powershell
py -3.12 launcher.py
```

The launcher always runs Local Voice Studio with `.venv-voice`'s Python
if that folder exists, regardless of which Python started the launcher
itself — so a plain `py -3.12 launcher.py` is enough once the setup
above has been run; there is no need to relaunch the launcher itself
with a different interpreter just for this one tool.

or run it directly for the plain GUI with no project pre-selected:

```powershell
.\.venv-voice\Scripts\python.exe .\local_voice_studio.py
```

Self-test and diagnose need no Tk desktop runtime — only the launcher's
`run()` action opens the GUI — so they still work in the Codex/CI test
runtime described above by writing the launch ticket directly instead
of going through the launcher window:

```powershell
.\.venv-voice\Scripts\python.exe -c `
    "import launcher_common as lc; lc.write_config('local_voice_studio', {'action': 'diagnose'})"
.\.venv-voice\Scripts\python.exe -m local_voice_studio

.\.venv-voice\Scripts\python.exe -c `
    "import launcher_common as lc; lc.write_config('local_voice_studio', {'action': 'selftest'})"
.\.venv-voice\Scripts\python.exe -m local_voice_studio
```

The GUI workflow is:

1. Create a project and record the ownership/authorization statement.
2. Record prompted speech or import audio you own.
3. Edit or locally transcribe each clip, then accept clean clips.
4. Build a locked voice profile.
5. Generate local speech or a complete dome narration plan.
6. Render the masterclass MP4 with that existing local track.

The Project tab's "How this works" panel repeats this same workflow,
plus a fastest-path recipe, inside the app itself, and its "Hardware
and local backends" panel names the exact interpreter currently
running the tool and the exact fix if Chatterbox or faster-whisper are
not ready -- you do not need this file open to get unstuck.

The "Console" button (top-right of the window) opens a separate
window streaming live output from whatever is currently running --
model loading, synthesis, an F5 fine-tune server starting up -- with a
"still working (Ns elapsed)" heartbeat during long silent stretches so
it stays clear that nothing has frozen. The F5 fine-tune GUI in
particular is a local web app, not a desktop window: its address
(`http://127.0.0.1:PORT`) appears in the console and opens in your
browser automatically once the server is ready.

Every synthetic WAV has a JSON sidecar marking it as synthetic and recording
the model, profile checksum, settings, and source text. Chatterbox’s own
watermark is preserved.

## Waveform review, trimming, and comparison

The Dataset tab shows a waveform for whichever clip is selected. Click-drag
to select a range, Play to hear just that range, Trim to selection or
Delete selection to cut it down (a bad breath, a stray click) -- both work
against an in-memory copy first, so Play/Revert let you check the result
before Save edited clip actually rewrites the file and re-measures its
quality metrics.

The Compare tab puts three waveforms together: the selected profile's
locked reference (view/listen only -- profiles are immutable by design, so
this cannot be edited from here), the latest synthesis (Generate new take
reuses the Expression/Guidance sliders from the Synthesize tab), and a
fresh in-place recording you can trim the same way as a Dataset clip and
then explicitly add to the dataset with its own transcript -- it still
needs Accept on the Dataset tab afterward like any other clip. This is the
direct way to check whether a profile or parameter change is actually
moving the voice closer to you, rather than guessing from memory between
tabs.

This is a focused tool for curating short clips, not a general multitrack
audio editor.

## Optional F5 fine-tuning

The Fine-tune tab exports the official custom dataset header:

```text
audio_file|text
```

It can launch the upstream `f5-tts_finetune-gradio` command when installed.
The launcher binds to `127.0.0.1` and sets Weights & Biases to offline. It
opens a **web app**, not a desktop window — its address (like
`http://127.0.0.1:7860`) appears in the Console window and opens in your
browser automatically once the server is ready.

F5-TTS needs its own dedicated environment, separate from `.venv-voice`:
its fine-tune UI does not start at all on `gradio>=6.0.0` (an upstream
bug — the exact keyword argument its own code passes to `Blocks.launch()`
was removed in Gradio 6.x; see
[SWivid/F5-TTS#1239](https://github.com/SWivid/F5-TTS/issues/1239), open
and unfixed as of this writing), while chatterbox-tts hard-pins
`gradio==6.8.0` exactly for the Synthesize tab. Those two requirements
cannot both be satisfied in one environment. Set it up once:

```powershell
.\local_voice_studio\setup-f5-windows.ps1
```

This clones the official repo into `F5-TTS\`, creates `.venv-f5`, installs
F5-TTS editable, and forces `gradio==5.49.1` (confirmed working by that
issue's reporters — F5-TTS's own `gradio>=6.15.0` pin is the actual cause
of the breakage, not a safe minimum). The Fine-tune tab then uses
`.venv-f5` automatically, regardless of which Python runs Local Voice
Studio itself or what is installed in `.venv-voice`.

License warning: F5-TTS source code is MIT, while the official pretrained
weights are CC-BY-NC. Do not use those weights for monetized or commercial
video without a separately compatible checkpoint or permission.

On a 6 GB GPU, treat F5 fine-tuning as experimental. Reference-profile
inference is the reliable first target.

## Data layout

Each project is portable and local:

```text
MyVoice/
  project.json
  consent.json
  audit.jsonl
  raw/
  normalized/
  clips/
  metadata.csv
  profiles/
  runs/
  outputs/audio/
  outputs/dome/
```

The original imports remain under `raw/`; curated audio is canonical 24 kHz,
mono PCM-16 WAV.

## Full build specification

See `CLAUDE_BUILD_SPEC.md`. It is written to be pasted directly into a Claude
Code task and includes architecture, safety boundaries, GUI behavior, formats,
tests, acceptance criteria, and dome integration.

See `VOICE_DATA_GUIDE.md` for the recording plan, dataset thresholds,
evaluation phrases, and the point at which fine-tuning becomes worthwhile.

## Implemented boundary

This prototype implements the project/consent store, recording and importing,
FFmpeg normalization, energy segmentation, metrics, transcript editing, local
Whisper adapter, immutable voice profiles, Chatterbox Turbo adapter, synthetic
audio provenance, F5 dataset export/launcher, background jobs, and local dome
narration/video handoff.

It does not reimplement F5's neural-network trainer. The Fine-tune tab launches
the official upstream process and records a local run manifest. This avoids
fabricating version-sensitive training flags. A future polished release can
wrap those controls after pinning and testing one exact upstream revision.

## Rap Studio — beats, autotune, and flow

The **Rap Studio** tab turns the program into a small vocal production
desk: it reads a beat, puts your take in time with it, tunes it, and
mixes the two. It is the same local-only promise as the rest of the
program — no hosted service, no account, no upload.

Open it with `py -3.12 launcher.py` → **Local Voice Studio** → Launch,
then the **Rap Studio** tab.

### What it does, in order

1. **Reads the beat** (`beatgrid.py`). Tempo, where every beat and bar
   line falls, which beat is the "one", how steady the track is, and
   what key it is in. Nothing is typed in by hand.
2. **Puts the vocal in the pocket** (`flow.py`). Finds your syllables
   and time-warps them onto the grid — without moving the pitch.
3. **Tunes it** (`autotune.py`) to the key the beat is already in.
4. **Mixes** (`mixdown.py`) — levels, ducking, double-tracking, limiting.

Every render writes a **new folder** containing the finished track, the
separate stems, a click track for checking the grid by ear, and a
`receipt.json` listing every setting and every measured number. Nothing
is ever overwritten.

### The controls that matter

**How hard to snap** (0–1). 0 leaves your timing exactly as performed;
1 puts every syllable dead on the grid. Around **0.85** fixes what was
genuinely late without flattening the human push-and-pull. Note that
fully quantized rap often sounds *worse* — the pocket is partly made of
being slightly behind the beat.

**Swing** delays every second off-beat. 0 is straight; about 1/3 is a
relaxed shuffle.

**Tuning style**:

| style | what it sounds like |
|---|---|
| `off` | pitch left exactly as sung (still measured and reported) |
| `natural` | quietly fixes missed notes; still sounds like a person |
| `tight` | clearly tuned, still glides between notes |
| `hard` | the stepped, obviously-tuned rap and R&B sound |
| `robot` | snaps instantly, no glide at all |

Leave **Key** blank and it uses the key detected in the beat.

### Why it does not sound like a chipmunk

Pitch is moved with **TD-PSOLA**: the waveform is cut into individual
pitch periods and those periods are laid back down at new spacing. Each
period is *moved*, never resampled, so the vocal-tract resonances inside
it stay where they were. Those resonances (formants) are what make a
voice sound like a person of a particular size — naive resampling drags
them along with the pitch, which is exactly the chipmunk artifact.

Measured on a synthetic vowel built with formants at 700 and 1220 Hz:
transposing **+12 semitones** doubles the pitch and moves the first
formant by **1.8 cents**. Resampling the same signal moves it by nearly
an octave.

The same grain engine does the time-warping, run the other way round:
keep each grain's period and move through the input faster or slower,
and the syllables move while the pitch stays put.

### Command line

Every control is also a launcher action, so this can be scripted:

```bash
py -3.12 launcher.py
```

Choose **Local Voice Studio**, then an action:

- `rap_analyze` — measure an instrumental (tempo, bars, key, steadiness)
- `rap_preview` — measure how far off the beat and off the note a take
  already is, without rendering anything
- `rap_produce` — the whole chain, to a finished track
- `rap_selftest` — check the engines against audio built to a known
  tempo and key

### Writing to the grid

`flow.layout_bars()` estimates the syllables in each written line and
compares that to how many slots a bar actually has at this tempo, so you
can tell a bar is overfull **before** recording it. The syllable count
is a vowel-group estimate with corrections for silent *e* and syllabic
consonants ("rhythm", "prism"), not a dictionary — good enough to warn
you, not something to quote as fact.

### What it needs

numpy, scipy, librosa and soundfile — all already in
`requirements-core.txt`. FFmpeg is needed only to read or write
compressed audio (mp3, m4a). Nothing else, and nothing downloaded at
run time. Check with the `rap_selftest` action; if the libraries are
missing it says so and the rest of the program carries on working.

### Honest limits

- **Autotune helps sung delivery far more than spoken delivery.** On
  flat spoken narration expect a modest change (a real measured example:
  26 → 18 cents off the note); on sung or melodic delivery the effect is
  much larger.
- **Very fast delivery is harder to align.** Syllables closer together
  than about 55 ms are treated as one.
- **Tempo detection can land on half or double time** on tracks with
  busy hi-hats and a sparse kick. Tempo is read from a low-band onset
  envelope specifically to avoid this, but if it still happens, set the
  BPM hint.
- **Re-detecting syllables after warping finds slightly fewer of them**,
  because warping softens some onsets. The "after" syllable count in a
  receipt is therefore not directly comparable to the "before" one.
