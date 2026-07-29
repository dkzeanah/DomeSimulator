"""Optional local AI backend adapters.

Imports are deliberately lazy so project curation and ``--selftest`` work
without installing gigabytes of ML dependencies.
"""

from __future__ import annotations

import csv
import importlib.util
import importlib.metadata
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .models import VoiceProfile, utc_now
from .project import VoiceProject


@dataclass(frozen=True)
class BackendStatus:
    backend_id: str
    ready: bool
    summary: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class HardwareInfo:
    gpu_name: str = ""
    vram_mib: int = 0
    driver: str = ""
    torch_installed: bool = False
    cuda_available: bool = False
    torch_version: str = ""
    cuda_version: str = ""

    @property
    def grade(self) -> str:
        if not self.gpu_name:
            return "CPU profile + inference"
        if self.vram_mib < 8_000:
            return "Profile + low-memory inference"
        if self.vram_mib < 16_000:
            return "Inference + experimental adaptation"
        return "Inference + fine-tuning"


def detect_hardware() -> HardwareInfo:
    gpu_name = ""
    vram_mib = 0
    driver = ""
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            columns = [part.strip() for part in result.stdout.splitlines()[0].split(",")]
            if len(columns) >= 3:
                gpu_name, memory_text, driver = columns[:3]
                try:
                    vram_mib = int(memory_text)
                except ValueError:
                    vram_mib = 0
    torch_installed = importlib.util.find_spec("torch") is not None
    cuda_available = False
    torch_version = ""
    cuda_version = ""
    if torch_installed:
        try:
            import torch
            torch_version = str(torch.__version__)
            cuda_available = bool(torch.cuda.is_available())
            cuda_version = str(torch.version.cuda or "")
        except Exception:
            pass
    return HardwareInfo(
        gpu_name=gpu_name,
        vram_mib=vram_mib,
        driver=driver,
        torch_installed=torch_installed,
        cuda_available=cuda_available,
        torch_version=torch_version,
        cuda_version=cuda_version,
    )


def chatterbox_status() -> BackendStatus:
    missing = [
        name for name in ("torch", "torchaudio", "chatterbox")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        return BackendStatus(
            "chatterbox-turbo",
            False,
            "Not installed",
            tuple(f"missing: {name}" for name in missing),
        )
    hardware = detect_hardware()
    return BackendStatus(
        "chatterbox-turbo",
        True,
        f"Ready on {'CUDA' if hardware.cuda_available else 'CPU'}",
        (hardware.grade,),
    )


_CHATTERBOX_MODELS: dict[str, object] = {}


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def synthesize_chatterbox(
    project: VoiceProject,
    profile: VoiceProfile,
    text: str,
    output_path: Path,
    *,
    device: str = "auto",
    exaggeration: float = 0.45,
    cfg_weight: float = 0.5,
    allow_model_download: bool = False,
    progress: Callable[[str], None] = print,
) -> Path:
    """Generate watermarked local speech with Chatterbox Turbo."""
    if not project.consented:
        raise PermissionError("Project ownership statement is required")
    if not text.strip():
        raise ValueError("Synthesis text is empty")
    if len(text) > 4_000:
        raise ValueError("Text is too long; split it into paragraphs")
    status = chatterbox_status()
    if not status.ready:
        raise RuntimeError(
            "Chatterbox is not ready. Install the optional inference requirements."
        )
    previous_hf_offline = os.environ.get("HF_HUB_OFFLINE")
    previous_transformers_offline = os.environ.get("TRANSFORMERS_OFFLINE")
    if not allow_model_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        progress("Offline-only mode: model files must already be cached.")
    try:
        import torch
        import torchaudio
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        chosen_device = device
        if chosen_device == "auto":
            chosen_device = "cuda" if torch.cuda.is_available() else "cpu"
        if chosen_device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")
        progress(f"Loading Chatterbox Turbo on {chosen_device}...")
        model = _CHATTERBOX_MODELS.get(chosen_device)
        if model is None:
            model = ChatterboxTurboTTS.from_pretrained(device=chosen_device)
            _CHATTERBOX_MODELS[chosen_device] = model
        reference = project.resolve_relative(profile.reference_wav)
        if not reference.is_file():
            raise FileNotFoundError(reference)
        progress("Synthesizing local voice...")
        # Turbo accepts the prompt path directly. Keep optional controls guarded
        # so a compatible upstream version without them still works.
        kwargs = {"audio_prompt_path": str(reference)}
        try:
            waveform = model.generate(
                text,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                **kwargs,
            )
        except TypeError:
            waveform = model.generate(text, **kwargs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(output_path), waveform.cpu(), int(model.sr))
    finally:
        if not allow_model_download:
            if previous_hf_offline is None:
                os.environ.pop("HF_HUB_OFFLINE", None)
            else:
                os.environ["HF_HUB_OFFLINE"] = previous_hf_offline
            if previous_transformers_offline is None:
                os.environ.pop("TRANSFORMERS_OFFLINE", None)
            else:
                os.environ["TRANSFORMERS_OFFLINE"] = previous_transformers_offline
    sidecar = {
        "schema": 1,
        "synthetic_voice": True,
        "generated_at": utc_now(),
        "backend": "chatterbox-turbo",
        "model": {
            "name": "Chatterbox Turbo",
            "source": "resemble-ai/chatterbox",
            "package_version": _package_version("chatterbox-tts"),
            "license": "MIT",
        },
        "profile_id": profile.profile_id,
        "profile_sha256": profile.sha256,
        "reference_wav": profile.reference_wav,
        "device": chosen_device,
        "exaggeration": exaggeration,
        "cfg_weight": cfg_weight,
        "model_download_allowed": allow_model_download,
        "watermark": "preserved model-provided watermark",
        "text": text,
    }
    output_path.with_suffix(output_path.suffix + ".json").write_text(
        json.dumps(sidecar, indent=2) + "\n", encoding="utf-8"
    )
    project.audit(
        "synthetic_audio_generated",
        {
            "backend": "chatterbox-turbo",
            "profile_id": profile.profile_id,
            "output": project.relative(output_path),
        },
    )
    progress(f"Saved {output_path}")
    return output_path


def faster_whisper_status() -> BackendStatus:
    if importlib.util.find_spec("faster_whisper") is None:
        return BackendStatus(
            "faster-whisper", False, "Not installed", ("missing: faster-whisper",)
        )
    return BackendStatus("faster-whisper", True, "Ready for local transcription")


_WHISPER_MODELS: dict[tuple[str, str, str], object] = {}


def transcribe_local(
    audio_path: Path,
    *,
    model_name: str = "small.en",
    device: str = "auto",
    progress: Callable[[str], None] = print,
) -> str:
    status = faster_whisper_status()
    if not status.ready:
        raise RuntimeError(
            "faster-whisper is not installed. Manual transcript editing remains available."
        )
    from faster_whisper import WhisperModel

    hardware = detect_hardware()
    chosen_device = device
    if chosen_device == "auto":
        chosen_device = "cuda" if hardware.cuda_available else "cpu"
    compute_type = "float16" if chosen_device == "cuda" else "int8"
    key = (model_name, chosen_device, compute_type)
    model = _WHISPER_MODELS.get(key)
    if model is None:
        progress(f"Loading local Whisper model {model_name}...")
        model = WhisperModel(
            model_name,
            device=chosen_device,
            compute_type=compute_type,
        )
        _WHISPER_MODELS[key] = model
    progress("Transcribing locally...")
    segments, _ = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def export_f5_dataset(project: VoiceProject, output_directory: Path) -> Path:
    """Export the official F5-TTS custom CSV format."""
    if not project.consented:
        raise PermissionError("Project ownership statement is required")
    clips = [
        clip for clip in project.load_clips()
        if clip.accepted and clip.text.strip() and not clip.quality_issues
    ]
    if not clips:
        raise ValueError("No accepted quality-clean clips are ready for F5 export")
    output_directory.mkdir(parents=True, exist_ok=True)
    metadata_path = output_directory / "metadata.csv"
    with metadata_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="|", lineterminator="\n")
        writer.writerow(["audio_file", "text"])
        for clip in clips:
            writer.writerow([
                str(project.resolve_relative(clip.audio_file)),
                clip.text.strip(),
            ])
    license_path = output_directory / "LICENSE-NOTICE.txt"
    license_path.write_text(
        "F5-TTS code is MIT licensed. Official pretrained F5-TTS weights are "
        "CC-BY-NC. Review the exact selected checkpoint license before training "
        "or publishing generated audio.\n",
        encoding="utf-8",
    )
    project.audit(
        "f5_dataset_exported",
        {"clips": len(clips), "path": str(metadata_path)},
    )
    return metadata_path


def launch_f5_finetune_gui(
    project: VoiceProject,
    command: str = "f5-tts_finetune-gradio",
) -> subprocess.Popen:
    """Launch the official upstream fine-tune UI as an adapter boundary."""
    executable = shutil.which(command)
    if not executable:
        raise RuntimeError(
            "F5-TTS fine-tune command was not found. Install F5-TTS editable "
            "from its official repository in the voice-studio environment."
        )
    environment = os.environ.copy()
    environment["WANDB_MODE"] = "offline"
    environment["GRADIO_SERVER_NAME"] = "127.0.0.1"
    run_id = f"{utc_now().replace(':', '').replace('-', '')}-f5-gui"
    run_directory = project.root / "runs" / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    run_manifest = {
        "schema": 1,
        "run_id": run_id,
        "backend": "f5-tts",
        "state": "RUNNING_EXTERNAL_GUI",
        "created_at": utc_now(),
        "command": [executable],
        "environment": {
            "WANDB_MODE": "offline",
            "GRADIO_SERVER_NAME": "127.0.0.1",
        },
        "license_notice": (
            "F5-TTS code is MIT; official pretrained weights are CC-BY-NC. "
            "The selected checkpoint license must be reviewed separately."
        ),
    }
    (run_directory / "run.json").write_text(
        json.dumps(run_manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_directory / "command.txt").write_text(
        executable + "\n",
        encoding="utf-8",
    )
    process = subprocess.Popen(
        [executable],
        cwd=str(project.root),
        env=environment,
        shell=False,
    )
    project.audit(
        "f5_finetune_gui_launched",
        {"command": executable, "run_id": run_id, "pid": process.pid},
    )
    return process
