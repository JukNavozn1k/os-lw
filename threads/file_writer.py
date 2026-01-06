import threading
import time
import queue
from datetime import datetime
from synchronization.mutex_manager import SharedMutex
from utils.file_manager import append_line_safe


class BaseControlledThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused
        self._stop_event = threading.Event()
        self._delay = 0.5
        self.status = "STOP"

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
        if not self.is_alive():
            self._stop_event.clear()
            self._pause_event.set()
            self.status = "RUNNING"
            super().start()
        else:
            self.resume()

    def _wait_or_stop(self, duration: float):
        end = time.time() + duration
        while time.time() < end:
            if self._stop_event.is_set():
                return True
            while not self._pause_event.is_set():
                if self._stop_event.is_set():
                    return True
                time.sleep(0.02)
            time.sleep(0.02)
        return self._stop_event.is_set()


class FileWriterThread(BaseControlledThread):
    def __init__(self, input_queue: "queue.Queue[str]", file_path: str, mutex: SharedMutex):
        super().__init__()
        self._q = input_queue
        self._file = file_path
        self._mutex = mutex

    def run(self):
        while not self._stop_event.is_set():
            try:
                ch = self._q.get(timeout=0.2)
            except queue.Empty:
                if self._wait_or_stop(self._delay):
                    break
                continue
            # critical section: append char
            with self._mutex:
                append_line_safe(self._file, ch)
            if self._wait_or_stop(self._delay):
                break


class TimeWriterThread(BaseControlledThread):
    def __init__(self, file_path: str, mutex: SharedMutex):
        super().__init__()
        self._file = file_path
        self._mutex = mutex

    def run(self):
        while not self._stop_event.is_set():
            now = datetime.now().strftime("%H:%M:%S")
            with self._mutex:
                append_line_safe(self._file, now)
            if self._wait_or_stop(self._delay):
                break
