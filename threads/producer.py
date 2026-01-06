import threading
import time
import itertools
from utils.buffer import ThreadSafeBuffer


class BaseControlledThread:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()
        self._delay = 0.3
        self.status = "STOP"

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_delay(self, delay: float):
        self._delay = max(0.0, float(delay))

    def pause(self):
        self._pause_event.clear()
        self.status = "PAUSED"

    def resume(self):
        self._pause_event.set()
        if not self._stop_event.is_set():
            self.status = "RUNNING"

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()
        self.status = "STOP"

    def start_safe(self):
        if self.is_alive():
            self.resume()
            return

        self._stop_event.clear()
        self._pause_event.set()
        self.status = "RUNNING"

        self._thread = threading.Thread(target=self._thread_entry, daemon=True)
        self._thread.start()

    def _thread_entry(self):
        try:
            self.run()
        finally:
            self.status = "STOP"

    def _cooperative_wait(self):
        end = time.time() + self._delay
        while time.time() < end:
            if self._stop_event.is_set():
                return True
            while not self._pause_event.is_set():
                if self._stop_event.is_set():
                    return True
                time.sleep(0.02)
            time.sleep(0.02)
        return False


class ProducerThread(BaseControlledThread):
    def __init__(self, buffer: ThreadSafeBuffer, on_produced=None):
        super().__init__()
        self.buffer = buffer
        self.on_produced = on_produced
        self._counter = itertools.count(1)

    def run(self):
        while not self._stop_event.is_set():
            item = next(self._counter)
            self.buffer.put(item, process_id=0)
            if self.on_produced:
                try:
                    self.on_produced(item)
                except Exception:
                    pass
            if self._cooperative_wait():
                break


class ConsumerThread(BaseControlledThread):
    def __init__(self, buffer: ThreadSafeBuffer, on_consumed=None):
        super().__init__()
        self.buffer = buffer
        self.on_consumed = on_consumed

    def run(self):
        while not self._stop_event.is_set():
            item = self.buffer.get(process_id=1)
            if item is not None and self.on_consumed:
                try:
                    self.on_consumed(item)
                except Exception:
                    pass
            if self._cooperative_wait():
                break
