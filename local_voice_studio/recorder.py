"""Optional microphone recorder with no import-time dependency."""

from __future__ import annotations

import threading
import wave
from pathlib import Path


class MicrophoneRecorder:
    def __init__(self, sample_rate: int = 24_000):
        self.sample_rate = sample_rate
        self._stream = None
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()
        self.peak = 0.0

    @staticmethod
    def devices() -> list[tuple[int, str]]:
        try:
            import sounddevice as sd
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Microphone recording needs sounddevice. Install the core GUI "
                "requirements or import existing audio instead."
            ) from exc
        result = []
        for index, device in enumerate(sd.query_devices()):
            if int(device.get("max_input_channels", 0)) > 0:
                result.append((index, str(device.get("name", f"Input {index}"))))
        return result

    def start(self, device: int | None = None) -> None:
        if self._stream is not None:
            raise RuntimeError("Recorder is already running")
        try:
            import numpy as np
            import sounddevice as sd
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Recording needs numpy and sounddevice"
            ) from exc
        self._chunks = []
        self.peak = 0.0

        def callback(indata, frames, time_info, status):
            del frames, time_info
            if status:
                pass
            copied = indata.copy()
            with self._lock:
                self._chunks.append(copied.tobytes())
                self.peak = max(
                    self.peak,
                    float(np.max(np.abs(copied.astype(np.float32) / 32768.0))),
                )

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=device,
            callback=callback,
        )
        self._stream.start()

    def stop(self, output_path: Path) -> Path:
        if self._stream is None:
            raise RuntimeError("Recorder is not running")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            data = b"".join(self._chunks)
            self._chunks = []
        if not data:
            raise RuntimeError("No microphone audio was captured")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(data)
        return output_path
