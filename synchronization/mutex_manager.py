import threading


class SharedMutex:
    """Simple context-manager wrapper over threading.Lock to share between threads."""

    def __init__(self):
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc, tb):
        self._lock.release()

    # Expose acquire/release for explicit use if needed
    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()
