import threading
from typing import Optional

from utils.debug_controller import DebugController


class SharedMutex:
    """Simple context-manager wrapper over threading.Lock to share between threads."""

    def __init__(self):
        self._lock = threading.Lock()
        self._debug: Optional[DebugController] = None
        self.owner: int | None = None
        self.locked = False

    def set_debug(self, debug: Optional[DebugController]):
        self._debug = debug

    def snapshot(self):
        return {"locked": bool(self.locked), "owner": self.owner}

    def __enter__(self):
        self.acquire(process_id=None)

    def __exit__(self, exc_type, exc, tb):
        self.release(process_id=None)

    # Expose acquire/release for explicit use if needed
    def acquire(self, process_id: int | None = None):
        if self._debug is not None and process_id is not None:
            self._debug.wait("mutex.before_acquire", {"process": process_id, **self.snapshot()})
        self._lock.acquire()
        self.owner = process_id
        self.locked = True
        if self._debug is not None and process_id is not None:
            self._debug.wait("mutex.acquired", {"process": process_id, **self.snapshot()})

    def release(self, process_id: int | None = None):
        if self._debug is not None and process_id is not None:
            self._debug.wait("mutex.before_release", {"process": process_id, **self.snapshot()})
        self.owner = None
        self.locked = False
        self._lock.release()
        if self._debug is not None and process_id is not None:
            self._debug.wait("mutex.released", {"process": process_id, **self.snapshot()})
