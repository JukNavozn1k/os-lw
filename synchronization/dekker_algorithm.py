import time
from typing import Optional

from utils.debug_controller import DebugController


class DekkerLock:
    def __init__(self, debug: Optional[DebugController] = None):
        self.flag = [False, False]
        self.turn = 0
        self._debug = debug

    def set_debug(self, debug: Optional[DebugController]):
        self._debug = debug

    def snapshot(self):
        return {
            "flag0": bool(self.flag[0]),
            "flag1": bool(self.flag[1]),
            "turn": int(self.turn),
        }

    def acquire(self, process_id: int):
        other = 1 - process_id
        self.flag[process_id] = True
        if self._debug is not None:
            self._debug.wait(
                "dekker.flag_set",
                {"process": process_id, "other": other, **self.snapshot()},
            )
        while self.flag[other]:
            if self.turn == other:
                self.flag[process_id] = False
                if self._debug is not None:
                    self._debug.wait(
                        "dekker.backoff",
                        {"process": process_id, "other": other, **self.snapshot()},
                    )
                # busy-wait with cooperative sleep to avoid locking CPU
                while self.turn == other:
                    time.sleep(0.0005)
                self.flag[process_id] = True
                if self._debug is not None:
                    self._debug.wait(
                        "dekker.retry",
                        {"process": process_id, "other": other, **self.snapshot()},
                    )

        if self._debug is not None:
            self._debug.wait(
                "dekker.acquired",
                {"process": process_id, "other": other, **self.snapshot()},
            )

    def release(self, process_id: int):
        self.turn = 1 - process_id
        self.flag[process_id] = False
        if self._debug is not None:
            self._debug.wait(
                "dekker.released",
                {"process": process_id, "other": 1 - process_id, **self.snapshot()},
            )

    # Context manager helpers
    def __enter__(self):
        raise RuntimeError("Use acquire(process_id) / release(process_id) with process id 0 or 1")
