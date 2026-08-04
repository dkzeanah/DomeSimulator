# Local Voice Studio

Local Voice Studio is a standalone Windows-first program for collecting voice
recordings you own, curating a clean speech dataset, creating a locked local
voice profile, and generating speech on your computer. It does not use a hosted
inference API, login, telemetry, cloud database, or share server.

It is separate from Dome Creator, the assembly line, and the standalone 2V
masterclass. Its only integration is an explicit narration-plan file that the
2V video exporter can consume.

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
6. Render the 2V MP4 with that existing local track.

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

## Optional F5 fine-tuning

The Fine-tune tab exports the official custom dataset header:

```text
audio_file|text
```

It can launch the upstream `f5-tts_finetune-gradio` command when installed.
The launcher binds to `127.0.0.1` and sets Weights & Biases to offline.

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
