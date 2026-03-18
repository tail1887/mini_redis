from __future__ import annotations

from threading import Lock


class CacheMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def record_hit(self, count: int = 1) -> None:
        with self._lock:
            self._hits += count

    def record_miss(self, count: int = 1) -> None:
        with self._lock:
            self._misses += count

    def record_delete(self, count: int = 1) -> None:
        with self._lock:
            self._deletes += count

    def record_error(self, count: int = 1) -> None:
        with self._lock:
            self._errors += count

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "deletes": self._deletes,
                "errors": self._errors,
            }

    def reset(self) -> None:
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._deletes = 0
            self._errors = 0


cache_metrics = CacheMetrics()
