from __future__ import annotations

from math import ceil
from time import time
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


class InMemoryKVStore:
    """In-memory KV store with TTL cleanup on read/write state transitions."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}

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
        if not self._has_live_key(key):
            return False
        self._expires_at[key] = time() + seconds
        return True

    def ttl(self, key: str) -> int:
        if not self._has_live_key(key):
            return -2

        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return -1

        remaining = expires_at - time()
        if remaining <= 0:
            self._delete_internal(key)
            return -2
        return ceil(remaining)

    def persist(self, key: str) -> bool:
        if not self._has_live_key(key):
            return False
        if key not in self._expires_at:
            return False
        self._expires_at.pop(key, None)
        return True

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
        return expires_at <= time()

    def _delete_internal(self, key: str) -> None:
        self._data.pop(key, None)
        self._expires_at.pop(key, None)
