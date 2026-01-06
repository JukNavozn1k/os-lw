import time


class DekkerLock:
    def __init__(self):
        self.flag = [False, False]
        self.turn = 0

    def acquire(self, process_id: int):
        other = 1 - process_id
        self.flag[process_id] = True
        while self.flag[other]:
            if self.turn == other:
                self.flag[process_id] = False
                # busy-wait with cooperative sleep to avoid locking CPU
                while self.turn == other:
                    time.sleep(0.0005)
                self.flag[process_id] = True

    def release(self, process_id: int):
        self.turn = 1 - process_id
        self.flag[process_id] = False

    # Context manager helpers
    def __enter__(self):
        raise RuntimeError("Use acquire(process_id) / release(process_id) with process id 0 or 1")
