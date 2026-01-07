import threading
from typing import Any

import time


class DebugController:
    def __init__(self):
        self._enabled = False
        self._auto = False
        self._step_event = threading.Event()
        self._step_event.set()
        self._lock = threading.Lock()
        self._last_point: str | None = None
        self._last_state: dict[str, Any] = {}
        self._log: list[str] = []

    def set_enabled(self, enabled: bool):
        with self._lock:
            self._enabled = bool(enabled)
            if not self._enabled:
                self._auto = False
                self._step_event.set()
            else:
                self._auto = False
                self._step_event.clear()

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def step(self):
        with self._lock:
            if not self._enabled:
                return
            self._auto = False
            self._step_event.set()

    def run(self):
        with self._lock:
            if not self._enabled:
                return
            self._auto = True
            self._step_event.set()

    def pause(self):
        with self._lock:
            if not self._enabled:
                return
            self._auto = False
            self._step_event.clear()

    def wait(self, point: str, state: dict[str, Any]):
        with self._lock:
            ts = time.strftime("%H:%M:%S")
            self._log.append(f"[{ts}] {point} {state}")
            if not self._enabled or self._auto:
                self._last_point = point
                self._last_state = dict(state)
                return
            self._last_point = point
            self._last_state = dict(state)
            self._step_event.clear()

        self._step_event.wait()

    def snapshot(self) -> tuple[str | None, dict[str, Any]]:
        with self._lock:
            return self._last_point, dict(self._last_state)

    def log_snapshot(self) -> list[str]:
        with self._lock:
            return list(self._log)

    def clear_log(self):
        with self._lock:
            self._log.clear()
