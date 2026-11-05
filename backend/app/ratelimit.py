"""Minimum interval between outbound Bandcamp fetches.

The timestamp lives in a file and is guarded by a lock, so gunicorn workers
in one container share the same limit and do not burst from the same IP.
"""

from __future__ import annotations

import os
import time

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


class RateLimiter:
    def __init__(self, path: str | None = None, min_interval: float | None = None):
        self.path = path
        self._min_interval = min_interval

    def interval(self) -> float:
        if self._min_interval is not None:
            return max(0.0, float(self._min_interval))
        raw = os.environ.get("BANDCAMP_MIN_INTERVAL", "2")
        try:
            return max(0.0, float(raw))
        except ValueError:
            return 2.0

    def state_path(self) -> str:
        return self.path or os.environ.get(
            "BANDCAMP_RATE_LIMIT_PATH", "/tmp/bandcamp-parser-rate"
        )

    def wait(self) -> float:
        """Block until the next request is allowed. Returns seconds slept."""
        interval = self.interval()
        if interval <= 0:
            return 0.0

        path = self.state_path()
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        waited = 0.0
        with open(path, "a+") as fh:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.seek(0)
                raw = fh.read().strip()
                try:
                    last = float(raw) if raw else 0.0
                except ValueError:
                    last = 0.0
                now = time.time()
                delay = interval - (now - last)
                if delay > 0:
                    time.sleep(delay)
                    waited = delay
                    now = time.time()
                fh.seek(0)
                fh.truncate()
                fh.write(f"{now:.6f}")
                fh.flush()
            finally:
                if fcntl is not None:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        return waited


limiter = RateLimiter()
