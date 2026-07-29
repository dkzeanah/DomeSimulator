# Claude Build Specification: Local Voice Studio

Copy this entire document into a fresh Claude Code task. The implementation
must remain a standalone program and must not be folded into Dome Creator or
the assembly-line simulation.

## 1. Mission

Build a Windows-first, cross-platform desktop application named **Local Voice
Studio** that lets a person:

1. record or import voice data they own;
2. clean, segment, inspect, transcribe, and curate it locally;
3. create a reusable local voice profile;
4. immediately synthesize speech with a local zero-shot voice-cloning model;
5. optionally fine-tune a supported open model for improved identity;
6. generate chapter narration for the standalone 2V Geodesic Masterclass;
7. keep recordings, transcripts, embeddings, checkpoints, and generated audio
   on the user's computer.

No hosted inference API, telemetry, login, cloud database, automatic upload, or
public share link is allowed.

## 2. Important product truth

Do **not** describe adaptation as training a speech foundation model from
scratch.

- Training a competitive foundation TTS model from random initialization needs
  a very large corpus and substantial compute.
- The practical local workflow is:
  - zero-shot voice conditioning first;
  - optional fine-tuning of open pretrained weights second;
  - foundation-model training is explicitly out of scope.

The UI must use the terms **voice profile**, **adaptation**, and **fine-tune**
accurately.

## 3. User and hardware target

Primary target:

- Windows 11
- NVIDIA GTX 1660 Ti
- 6 GB VRAM
- Python 3.11
- FFmpeg and ffprobe installed

Also support:

- NVIDIA GPUs with 8/12/16/24+ GB VRAM
- CPU inference fallback
- macOS Apple Silicon where the selected backend supports it
- Linux CUDA

The application must detect hardware and display:

- GPU name and VRAM;
- CUDA availability and PyTorch/CUDA versions;
- system RAM when discoverable;
- model/backend readiness;
- an honest capability grade:
  - Profile + inference
  - Low-memory adaptation
  - Full fine-tuning

For 6 GB VRAM, default to Chatterbox Turbo inference and conservative settings.
Do not start a likely-to-OOM fine-tune without a warning and explicit override.

## 4. Model/back-end policy

Use adapters so backends can change without rewriting the GUI.

### Required baseline: Chatterbox Turbo

- Package/repository: `resemble-ai/chatterbox`
- Local inference, no API
- Use a curated reference WAV
- Default English model: Chatterbox Turbo
- Preserve the model's built-in watermark
- Store model name, revision, license, and generation settings in every output
  sidecar
- Treat the voice profile as the user's local identity asset

### Required transcription: faster-whisper

- Fully local inference after model weights are downloaded
- Default model: `small.en`
- CPU `int8` and CUDA `float16` modes
- Never send audio or text to an external transcription service
- Manual transcript editing is always available

### Optional fine-tune adapter: F5-TTS

- Export the official custom CSV format with header `audio_file|text`
- Support launching or wrapping the official fine-tune workflow
- Default to offline TensorBoard logging; do not enable W&B
- Show this license warning before use:
  - F5-TTS code is MIT
  - official pretrained weights are CC-BY-NC
  - a monetized or commercial workflow requires a separately compatible model
    or permission
- Fine-tune runs must be reproducible from a saved immutable run manifest

### Optional future adapter: Coqui XTTS

- Adapter boundary only unless implemented and tested
- Display the exact model license before weights are downloaded
- Do not silently substitute the legacy unmaintained package for the maintained
  `idiap/coqui-ai-TTS` fork

## 5. Safety and authorization

Voice cloning can be misused. The application must be useful without being
deceptive.

Before recording/importing, require a local signed manifest stating:

- I own this voice or have explicit permission to model it.
- I will not use it to impersonate another person deceptively.
- I accept responsibility for disclosure and applicable law.

Implement the following:

- project-level ownership/consent record;
- immutable audit entry when the record is accepted;
- visible `SYNTHETIC VOICE` metadata sidecar for generated files;
- optional audible disclosure prefix;
- preserve any model-provided watermark;
- no function for removing a watermark;
- no celebrity presets or scraping tools;
- no automatic uploading or sharing.

Do not claim this proves legal consent. It records the user's assertion.

## 6. Desktop UI

Use a native local GUI. Tkinter is acceptable for the first release; PySide6 is
preferred for the polished release. No browser share server is required.

### Tab 1: Project

- Create/Open/Close project
- Project name and speaker label
- Local data root
- Ownership attestation
- Privacy status: `LOCAL ONLY`
- Hardware/backend readiness cards
- Project totals: clips, accepted minutes, transcript coverage, rejected clips

### Tab 2: Record

- Microphone selector
- 24 kHz, mono, PCM-16 recording
- input meter and clipping indicator
- prompt queue
- start/stop, listen, accept, redo
- prompt coverage progress
- room-tone capture
- automatic descriptive filename

### Tab 3: Import & Segment

- Import WAV/FLAC/MP3/M4A
- Normalize with FFmpeg to 24 kHz mono PCM-16
- local energy/VAD segmentation
- configurable 2–15 second target clips
- preserve original immutable source
- waveform and trim controls

### Tab 4: Dataset

- sortable clip table
- playback
- transcript editor
- local faster-whisper transcription
- accept/reject/reason
- quality metrics:
  - duration
  - peak and RMS dBFS
  - clipped sample percentage
  - silence percentage
  - sample rate/channels
  - transcript presence
- dataset health score and actionable warnings

### Tab 5: Voice Profile

- rank accepted clips by quality
- build a 10–20 second reference WAV
- listen to the reference
- edit reference transcript
- profile name/version
- lock and checksum a profile version
- baseline comparison phrases

### Tab 6: Train

- backend selector
- F5 dataset export
- training preset:
  - 6 GB experimental
  - 12 GB balanced
  - 24 GB quality
- batch/gradient accumulation/learning rate/steps/checkpoint interval
- start/stop/resume
- stdout/stderr log viewer
- GPU memory graph
- run manifest and exact command preview
- validation samples at checkpoints
- explicit license acceptance

### Tab 7: Synthesize

- backend/model/profile selector
- text editor
- paragraph chunking
- seed and expressive controls
- generate/play/save
- compare A/B against the reference
- sidecar provenance JSON

### Tab 8: Dome Narration

- load the 2V masterclass chapter script
- generate one WAV per chapter with the selected local voice
- measure actual durations
- provide pre-roll/tail padding
- assemble a loudness-normalized narration track
- write timing JSON and SRT
- launch the existing video exporter with the local narration

### Tab 9: Logs

- timestamped application log
- job logs
- dependency/model diagnostics
- copy diagnostic bundle with no audio data

## 7. Project layout and formats

Each project is self-contained:

```text
MyVoice/
  project.json
  consent.json
  audit.jsonl
  raw/                 # immutable originals
  normalized/          # 24 kHz mono WAV
  clips/               # curated training clips
  metadata.csv
  profiles/
    teacher-v001/
      profile.json
      reference.wav
      reference.txt
  runs/
    20260726-143000-f5/
      run.json
      command.txt
      logs/
      checkpoints/
      validation/
  outputs/
    audio/
    dome/
```

`metadata.csv` columns:

```text
clip_id|audio_file|text|status|duration_s|peak_dbfs|rms_dbfs|clipped_pct|silence_pct|sha256|source_id
```

All stored paths should be project-relative except export formats that
explicitly require absolute paths.

## 8. Audio requirements

- Canonical data: 24,000 Hz, mono, signed PCM-16 WAV
- Preserve immutable source recordings
- Normalize sample format, not loudness, before dataset curation
- Reject or warn:
  - duration under 1.5 seconds or over 20 seconds
  - clipping above 0.1%
  - silence above 35%
  - RMS below -38 dBFS
  - missing transcript
- Never apply aggressive noise removal by default
- Preserve the speaker's natural breath, accent, and prosody
- Record 30–60 minutes for a serious adaptation target
- Capture varied sentence lengths, questions, emphasis, numbers, units,
  technical terms, and calm teaching delivery
- Keep 10% of accepted clips as a validation holdout

## 9. Internal interfaces

```python
class VoiceBackend(Protocol):
    id: str
    display_name: str
    license_summary: str

    def probe(self) -> BackendStatus: ...
    def synthesize(self, request: SynthesisRequest) -> SynthesisResult: ...
    def supports_training(self) -> bool: ...
    def prepare_dataset(self, project: VoiceProject, output: Path) -> Path: ...
    def build_training_command(self, run: TrainingRun) -> list[str]: ...
```

Long-running tasks must use a worker queue. The GUI thread must never execute
model loading, transcription, FFmpeg conversion, or training.

Subprocess rules:

- `shell=False`
- argument arrays only
- stream stdout and stderr
- terminate process tree on user stop
- write exact command and environment diff to the run manifest
- never include secrets

## 10. Training state machine

```text
DRAFT -> VALIDATED -> QUEUED -> RUNNING
RUNNING -> STOPPING -> STOPPED
RUNNING -> COMPLETED
RUNNING -> FAILED
STOPPED/FAILED -> RESUMED -> RUNNING
```

Only one GPU-intensive job may run at a time.

## 11. Quality evaluation

For every model/profile version, generate fixed phrases containing:

- normal teaching prose;
- measurements and decimals;
- acronyms such as PVC and CAD;
- questions;
- emotional emphasis;
- long technical sentences.

Record:

- local ASR word error rate;
- duration ratio;
- loudness;
- clipping;
- optional speaker-embedding similarity when a local permissive model is
  available;
- a human 1–5 rating for identity, naturalness, clarity, and stability.

Do not represent an embedding score as proof of identity or consent.

## 12. Dome integration contract

Export:

```json
{
  "schema": 1,
  "voice_profile": "teacher-v001",
  "model": "chatterbox-turbo",
  "chapter_starts": [0.0],
  "chapter_durations": [18.4],
  "speech_durations": [16.9],
  "speech_delay": 0.55,
  "track": "narration.m4a",
  "clips": ["chapter_01.wav"]
}
```

The dome exporter must use these durations when rendering frames and mux the
provided track without sending text or audio anywhere.

## 13. Setup experience

Provide:

- `local_voice_studio.py`
- `python -m local_voice_studio`
- a core requirements file;
- optional backend requirements;
- `--selftest`
- `--diagnose`
- `--project PATH`
- setup scripts for Windows PowerShell and Linux/macOS shell
- no global package installation;
- a dedicated Python 3.11 virtual environment.

Model download is allowed only after a confirmation that names:

- model;
- source;
- license;
- estimated download size;
- destination.

After download, support an offline-only mode that sets the relevant Hugging
Face offline environment variables.

## 14. Testing

Required automated tests:

- manifest round trip and schema migration;
- path traversal rejection;
- consent gate;
- WAV metrics with generated fixtures;
- segmentation boundaries;
- metadata CSV round trip;
- profile checksum and immutability;
- command construction without shell injection;
- training state transitions;
- cancellation;
- backend-unavailable diagnostics;
- mocked Chatterbox inference;
- mocked faster-whisper transcription;
- dome timing export;
- application import and `--selftest` without optional ML dependencies.

## 15. Acceptance criteria

The first release is complete when:

1. It launches without ML backends installed and explains what is missing.
2. A user can create a consented project.
3. A user can record/import, normalize, inspect, transcribe/edit, and accept
   clips.
4. A user can create an immutable reference voice profile.
5. With Chatterbox installed, the user can generate local speech from that
   profile.
6. The F5 adapter exports valid `audio_file|text` metadata and can launch its
   official fine-tune process.
7. Long tasks do not freeze the GUI.
8. The project passes `--selftest`.
9. Nothing listens on a non-loopback network interface.
10. No audio/text leaves the machine except an explicitly confirmed initial
    model-weight download.

## 16. Delivery behavior for Claude

- Inspect the current repository before editing.
- Build in `local_voice_studio/` and add only a root launcher.
- Do not modify the assembly line or Dome Creator.
- Preserve all unrelated worktree changes.
- Implement a thin, testable vertical slice before adding polish.
- Use official upstream commands and formats; do not invent training flags.
- If a backend API has changed, probe the installed version and adapt through
  the backend layer.
- Run self-tests after each milestone.
- Do not call the work complete if the GUI buttons are decorative.
- Document anything that remains an adapter boundary rather than working code.

