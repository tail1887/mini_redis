from __future__ import annotations

from app.core.errors import APIError
from app.stores.kv_store import KVStore


class KVService:
    """Stage-1/2 service layer for KV and TTL commands."""

    def __init__(self, store: KVStore) -> None:
        self.store = store

    def set_value(self, key: str, value: str) -> bool:
        return self.store.set(key, value)

    def get_value(self, key: str) -> str | None:
        return self.store.get(key)

    def delete_value(self, key: str) -> bool:
        return self.store.delete(key)

    def exists_value(self, key: str) -> bool:
        return self.store.exists(key)

    def expire_value(self, key: str, seconds: int) -> bool:
        if seconds <= 0:
            raise APIError("TTL_INVALID", message="seconds must be a positive integer")
        return self.store.expire(key, seconds)

    def ttl_value(self, key: str) -> int:
        return self.store.ttl(key)

    def persist_value(self, key: str) -> bool:
        return self.store.persist(key)

    def invalidate_prefix_value(self, prefix: str) -> int:
        return self.store.invalidate_prefix(prefix)
