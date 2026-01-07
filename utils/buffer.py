from collections import deque
from typing import Deque, Iterable, Optional
from synchronization.dekker_algorithm import DekkerLock
from utils.debug_controller import DebugController


class ThreadSafeBuffer:
    """
    Unbounded buffer implemented via deque. For demonstration, we expose max_size
    to drive UI progress, but we don't block producer at max; we cap listbox view only.

    Synchronization is done with Dekker's algorithm between two threads only:
    process_id 0 -> producer, process_id 1 -> consumer.
    """

    def __init__(self, max_size: int = 100):
        self._q: Deque[object] = deque()
        self._dekker = DekkerLock()
        self._max_size = max_size

    def set_debug(self, debug: DebugController | None):
        self._dekker.set_debug(debug)

    def dekker_snapshot(self):
        return self._dekker.snapshot()

    def put(self, item, process_id: int):
        # Wait while full; use Dekker for mutual exclusion of check+append
        while True:
            self._dekker.acquire(process_id)
            try:
                if len(self._q) < self._max_size:
                    self._q.append(item)
                    return
            finally:
                self._dekker.release(process_id)
            # cooperative backoff outside CS
            import time as _t
            _t.sleep(0.002)

    def get(self, process_id: int) -> Optional[object]:
        self._dekker.acquire(process_id)
        try:
            if self._q:
                return self._q.popleft()
            return None
        finally:
            self._dekker.release(process_id)

    def size(self) -> int:
        return len(self._q)

    def snapshot(self) -> Iterable[object]:
        # no lock: used only for UI best-effort snapshot
        return list(self._q)

    @property
    def max_size(self) -> int:
        return self._max_size
