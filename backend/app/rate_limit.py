from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class RateLimiter:
    def __init__(self, window_seconds: int):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.window_seconds = window_seconds
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client_key: str, endpoint: str, limit: int) -> bool:
        if limit <= 0:
            return False

        now = monotonic()
        key = (client_key, endpoint)

        with self._lock:
            timestamps = self._requests[key]
            cutoff = now - self.window_seconds

            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= limit:
                return False

            timestamps.append(now)
            return True
