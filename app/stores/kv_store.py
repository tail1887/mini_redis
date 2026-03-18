from __future__ import annotations

import time
from typing import Callable
from typing import Protocol


class KVStore(Protocol):
    def set(self, key: str, value: str) -> bool:
        ...

    def get(self, key: str) -> str | None:
        ...

    def delete(self, key: str) -> bool:
        ...

    def exists(self, key: str) -> bool:
        ...

    def expire(self, key: str, seconds: int) -> bool:
        ...

    def ttl(self, key: str) -> int:
        ...

    def persist(self, key: str) -> bool:
        ...

    def invalidate_prefix(self, prefix: str) -> int:
        ...


class InMemoryKVStore:
    """In-memory KV store with TTL cleanup on read/write state transitions."""

    def __init__(self, time_fn: Callable[[], float] | None = None) -> None:
        self._data: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}
        self._time_fn = time_fn or time.time

    def set(self, key: str, value: str) -> bool:
        self._data[key] = value
        self._expires_at.pop(key, None)
        return True

    def get(self, key: str) -> str | None:
        if not self._has_live_key(key):
            return None
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        if not self._has_live_key(key):
            return False
        self._delete_internal(key)
        return True

    def exists(self, key: str) -> bool:
        return self._has_live_key(key)

    def expire(self, key: str, seconds: int) -> bool:
        if seconds <= 0:
            return False
        if not self._has_live_key(key):
            return False
        self._expires_at[key] = self._time_fn() + seconds
        return True

    def ttl(self, key: str) -> int:
        if not self._has_live_key(key):
            return -2

        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return -1

        remaining = expires_at - self._time_fn()
        if remaining <= 0:
            self._delete_internal(key)
            return -2
        return int(remaining)

    def persist(self, key: str) -> bool:
        if not self._has_live_key(key):
            return False
        if key not in self._expires_at:
            return False
        self._expires_at.pop(key, None)
        return True

    def invalidate_prefix(self, prefix: str) -> int:
        deleted_count = 0
        for key in list(self._data.keys()):
            if not key.startswith(prefix):
                continue
            if not self._has_live_key(key):
                continue
            self._delete_internal(key)
            deleted_count += 1
        return deleted_count

    def _has_live_key(self, key: str) -> bool:
        if key not in self._data:
            self._expires_at.pop(key, None)
            return False
        if self._is_expired(key):
            self._delete_internal(key)
            return False
        return True

    def _is_expired(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return False
        return expires_at <= self._time_fn()

    def _delete_internal(self, key: str) -> None:
        self._data.pop(key, None)
        self._expires_at.pop(key, None)
