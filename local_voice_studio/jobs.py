"""Small worker queue for keeping model and audio work off the GUI thread."""

from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class JobEvent:
    kind: str
    value: Any


class Worker:
    def __init__(self):
        self.events: queue.Queue[JobEvent] = queue.Queue()
        self.thread: threading.Thread | None = None

    @property
    def busy(self) -> bool:
        return bool(self.thread and self.thread.is_alive())

    def start(
        self,
        function: Callable,
        *args,
        on_progress: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        if self.busy:
            raise RuntimeError("A background job is already running")

        def progress(message: str) -> None:
            self.events.put(JobEvent("progress", message))
            if on_progress:
                on_progress(message)

        def target() -> None:
            try:
                kwargs_with_progress = dict(kwargs)
                kwargs_with_progress["progress"] = progress
                result = function(*args, **kwargs_with_progress)
                self.events.put(JobEvent("result", result))
            except TypeError as exc:
                # Some simple jobs intentionally do not expose progress.
                if "progress" not in str(exc):
                    self.events.put(JobEvent("error", traceback.format_exc()))
                    return
                try:
                    result = function(*args, **kwargs)
                    self.events.put(JobEvent("result", result))
                except Exception:
                    self.events.put(JobEvent("error", traceback.format_exc()))
            except Exception:
                self.events.put(JobEvent("error", traceback.format_exc()))

        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def poll(self) -> list[JobEvent]:
        result: list[JobEvent] = []
        while True:
            try:
                result.append(self.events.get_nowait())
            except queue.Empty:
                return result
