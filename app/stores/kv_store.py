from __future__ import annotations

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


class InMemoryKVStore:
    """Stage-1 scaffold store: only method signatures and simple in-memory behavior."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set(self, key: str, value: str) -> bool:
        self._data[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return key in self._data
