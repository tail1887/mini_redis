from __future__ import annotations

import json
import threading
import time
from pathlib import Path
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

    def __init__(
        self,
        time_fn: Callable[[], float] | None = None,
        aof_path: str | Path | None = None,
        snapshot_path: str | Path | None = None,
        snapshot_every: int = 0,
    ) -> None:
        self._data: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}
        self._time_fn = time_fn or time.time
        self._lock = threading.RLock()
        self._aof_path = Path(aof_path) if aof_path is not None else None
        if snapshot_path is not None:
            self._snapshot_path = Path(snapshot_path)
        elif self._aof_path is not None:
            self._snapshot_path = self._aof_path.with_name("kv.snapshot.json")
        else:
            self._snapshot_path = None
        self._snapshot_every = max(0, snapshot_every)
        self._mutations_since_snapshot = 0
        with self._lock:
            self._restore_from_disk_locked()

    def set(self, key: str, value: str) -> bool:
        with self._lock:
            self._data[key] = value
            self._expires_at.pop(key, None)
            self._record_mutation_locked({"op": "set", "key": key, "value": value})
            return True

    def get(self, key: str) -> str | None:
        with self._lock:
            if not self._has_live_key(key):
                return None
            return self._data.get(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            if not self._has_live_key(key):
                return False
            self._delete_internal(key)
            self._record_mutation_locked({"op": "delete", "key": key})
            return True

    def exists(self, key: str) -> bool:
        with self._lock:
            return self._has_live_key(key)

    def expire(self, key: str, seconds: int) -> bool:
        with self._lock:
            if seconds <= 0:
                return False
            if not self._has_live_key(key):
                return False
            expires_at = self._time_fn() + seconds
            self._expires_at[key] = expires_at
            self._record_mutation_locked({"op": "expire", "key": key, "expires_at": expires_at})
            return True

    def ttl(self, key: str) -> int:
        with self._lock:
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
        with self._lock:
            if not self._has_live_key(key):
                return False
            if key not in self._expires_at:
                return False
            self._expires_at.pop(key, None)
            self._record_mutation_locked({"op": "persist", "key": key})
            return True

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            deleted_keys = [
                key
                for key in list(self._data.keys())
                if self._has_live_key(key) and key.startswith(prefix)
            ]

            for key in deleted_keys:
                self._delete_internal(key)

            if deleted_keys:
                self._record_mutation_locked({"op": "invalidate_prefix", "prefix": prefix})
            return len(deleted_keys)

    def durability_status(self) -> dict[str, str | int | bool]:
        with self._lock:
            aof_exists = self._aof_path is not None and self._aof_path.exists()
            snapshot_exists = self._snapshot_path is not None and self._snapshot_path.exists()
            return {
                "enabled": self._aof_path is not None,
                "aofPath": str(self._aof_path) if self._aof_path is not None else "",
                "snapshotPath": str(self._snapshot_path) if self._snapshot_path is not None else "",
                "aofExists": aof_exists,
                "snapshotExists": snapshot_exists,
                "snapshotEvery": self._snapshot_every,
            }

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

    def _record_mutation_locked(self, record: dict[str, str | float]) -> None:
        self._append_aof_record_locked(record)
        if self._snapshot_every <= 0 or self._snapshot_path is None:
            return
        self._mutations_since_snapshot += 1
        if self._mutations_since_snapshot < self._snapshot_every:
            return
        self._write_snapshot_locked()
        self._truncate_aof_locked()
        self._mutations_since_snapshot = 0

    def _append_aof_record_locked(self, record: dict[str, str | float]) -> None:
        if self._aof_path is None:
            return
        self._aof_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, separators=(",", ":"))
        with self._aof_path.open("a", encoding="utf-8") as file:
            file.write(line)
            file.write("\n")

    def _write_snapshot_locked(self) -> None:
        if self._snapshot_path is None:
            return
        self._snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"data": self._data, "expires_at": self._expires_at}
        temp_path = self._snapshot_path.with_suffix(f"{self._snapshot_path.suffix}.tmp")
        temp_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        temp_path.replace(self._snapshot_path)

    def _truncate_aof_locked(self) -> None:
        if self._aof_path is None:
            return
        self._aof_path.parent.mkdir(parents=True, exist_ok=True)
        self._aof_path.write_text("", encoding="utf-8")

    def _restore_from_disk_locked(self) -> None:
        if self._snapshot_path is not None and self._snapshot_path.exists():
            self._restore_snapshot_locked()
        if self._aof_path is not None and self._aof_path.exists():
            self._restore_aof_locked()
        self._cleanup_expired_locked()

    def _restore_snapshot_locked(self) -> None:
        if self._snapshot_path is None:
            return
        payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        data = payload.get("data", {})
        expires_at = payload.get("expires_at", {})
        if not isinstance(data, dict) or not isinstance(expires_at, dict):
            return
        self._data = {str(key): str(value) for key, value in data.items()}
        restored_expires: dict[str, float] = {}
        for key, raw_value in expires_at.items():
            try:
                restored_expires[str(key)] = float(raw_value)
            except (TypeError, ValueError):
                continue
        self._expires_at = restored_expires

    def _restore_aof_locked(self) -> None:
        if self._aof_path is None:
            return
        with self._aof_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                self._apply_aof_record_locked(record)

    def _apply_aof_record_locked(self, record: dict[str, object]) -> None:
        op = record.get("op")
        if op == "set":
            key = record.get("key")
            value = record.get("value")
            if isinstance(key, str) and isinstance(value, str):
                self._data[key] = value
                self._expires_at.pop(key, None)
            return

        if op == "delete":
            key = record.get("key")
            if isinstance(key, str):
                self._delete_internal(key)
            return

        if op == "expire":
            key = record.get("key")
            expires_at = record.get("expires_at")
            if isinstance(key, str) and key in self._data:
                try:
                    self._expires_at[key] = float(expires_at)
                except (TypeError, ValueError):
                    return
            return

        if op == "persist":
            key = record.get("key")
            if isinstance(key, str) and key in self._data:
                self._expires_at.pop(key, None)
            return

        if op == "invalidate_prefix":
            prefix = record.get("prefix")
            if isinstance(prefix, str):
                for key in [existing_key for existing_key in list(self._data.keys()) if existing_key.startswith(prefix)]:
                    self._delete_internal(key)

    def _cleanup_expired_locked(self) -> None:
        for key in list(self._data.keys()):
            self._has_live_key(key)
