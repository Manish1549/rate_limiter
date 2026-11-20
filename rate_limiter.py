"""Thread-safe rate limiter: at most N calls in any rolling 1-second window.

Algorithm: sliding-window log. We remember the timestamps of calls that were
allowed and, on each request, discard the ones older than one second. If fewer
than N remain, the call is allowed.

"""
import threading
import time
from collections import deque
from typing import Callable


class RateLimiter:
    def __init__(self, max_per_second: int,
                 clock: Callable[[], float] = time.monotonic):
        """
        max_per_second: the configurable limit N.
        clock: time source in seconds; injectable so tests need no sleeping.
        """
        if max_per_second <= 0:
            raise ValueError("max_per_second must be positive")
        self._limit = max_per_second
        self._clock = clock
        self._window = 1.0                 # seconds
        self._timestamps = deque()         # times of allowed calls, oldest first
        self._lock = threading.Lock()      # makes check + record atomic

    def allow_request(self) -> bool:
        """Return True if a call may be made now, False if it would exceed N/sec."""
        with self._lock:
            now = self._clock()
            cutoff = now - self._window
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) < self._limit:
                self._timestamps.append(now)
                return True
            return False
