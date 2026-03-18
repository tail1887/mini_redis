from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass
class CacheMetricSnapshot:
    hits: int
    misses: int
    deletes: int
    invalidations: int
    errors: int


class CacheMetrics:
    def __init__(self) -> None:
        self._hits = 0
        self._misses = 0
        self._deletes = 0
        self._invalidations = 0
        self._errors = 0
        self._lock = Lock()

    def record_hit(self) -> None:
        with self._lock:
            self._hits += 1

    def record_miss(self) -> None:
        with self._lock:
            self._misses += 1

    def record_delete(self, count: int = 1) -> None:
        if count <= 0:
            return
        with self._lock:
            self._deletes += count

    def record_invalidation(self) -> None:
        with self._lock:
            self._invalidations += 1

    def record_error(self) -> None:
        with self._lock:
            self._errors += 1

    def snapshot(self) -> CacheMetricSnapshot:
        with self._lock:
            return CacheMetricSnapshot(
                hits=self._hits,
                misses=self._misses,
                deletes=self._deletes,
                invalidations=self._invalidations,
                errors=self._errors,
            )

    def reset(self) -> None:
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._deletes = 0
            self._invalidations = 0
            self._errors = 0


cache_metrics = CacheMetrics()
