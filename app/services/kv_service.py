from __future__ import annotations

from app.stores.kv_store import KVStore


class KVService:
    """Stage-1 scaffold service layer for set/get/del/exists."""

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
