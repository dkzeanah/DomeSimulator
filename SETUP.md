# Setup Guide

From-zero instructions to get everything in this repo running. For what each
tool *does*, see [README.md](README.md); this file is just the install path.

On Windows the commands below use the `py -3.12` launcher. On macOS/Linux,
substitute `python3.12`.

## 1. Install Python

Use **Python 3.10–3.13**. **Not 3.14** — `pygame`/`moderngl` have no prebuilt
wheels for it yet.

Get it from <https://www.python.org/downloads/>. On Windows, check
"Add python.exe to PATH" during install.

## 2. Get the code

```bash
git clone https://github.com/dkzeanah/DomeSimulator.git
cd DomeSimulator
```

## 3. Install core dependencies and run

This covers the main dome creator, the assembly line, the 2V masterclass,
Dome Forge, and Presenter Studio:

```bash
py -3.12 -m pip install pygame moderngl numpy
py -3.12 launcher.py
```

`launcher.py` is the front door — a GUI with a tab for every tool, no
command-line flags needed. **This alone gets the core simulator fully
working.** Running any tool directly (e.g. `py -3.12 dome_creator.py`) also
works and falls back to that tool's default fullscreen app.

## 4. Optional tools with their own dependencies

### 2V Masterclass video export

Needs its own requirements plus `ffmpeg`:

```bash
py -3.12 -m pip install -r two_v_demo/requirements.txt
```

Then install **ffmpeg** (which includes `ffprobe`) and make sure both are on
your PATH, or set their paths in the launcher's 2V Masterclass tab. Video
export will not work without it.

- Windows: `winget install ffmpeg`
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### Local Voice Studio

Uses a **separate** Python environment (heavier AI packages, needs Python
**3.11**):

```bash
py -3.11 -m venv .venv-voice
.\.venv-voice\Scripts\python.exe -m pip install -r .\local_voice_studio\requirements-core.txt
```

The launcher automatically uses `.venv-voice` for Voice Studio once that
folder exists. For the optional local AI voice/transcription backends, run
`.\local_voice_studio\setup-windows.ps1 -WithLocalAI` once. Voice Studio still
opens without these and reports exactly what is missing rather than failing.

See [local_voice_studio/README.md](local_voice_studio/README.md) for the full
workflow, privacy behavior, model downloads, and licensing.

## 5. About the `deliverables/.../build/` folder

That folder holds a Node.js build script (`build_deck_*.mjs`) for one past
presentation deliverable. Its `node_modules` is intentionally **not** committed
(it is gitignored). You only need it if you are rebuilding that specific slide
deck — in which case run `npm install` (or `pnpm install`) inside that folder
to restore the libraries. It is **not** needed to run any of the Python tools.

## TL;DR

```bash
# install Python 3.12, then:
git clone https://github.com/dkzeanah/DomeSimulator.git
cd DomeSimulator
py -3.12 -m pip install pygame moderngl numpy
py -3.12 launcher.py
```

Everything else is optional add-ons for video export and voice synthesis.
