from __future__ import annotations

from app.observability.cache_metrics import CacheMetrics
from app.stores.kv_store import KVStore


class KVService:
    """Stage-1 scaffold service layer for set/get/del/exists."""

    def __init__(self, store: KVStore, metrics: CacheMetrics) -> None:
        self.store = store
        self.metrics = metrics

    def set_value(self, key: str, value: str) -> bool:
        return self.store.set(key, value)

    def get_value(self, key: str) -> str | None:
        value = self.store.get(key)
        if value is None:
            self.metrics.record_miss()
        else:
            self.metrics.record_hit()
        return value

    def delete_value(self, key: str) -> bool:
        deleted = self.store.delete(key)
        if deleted:
            self.metrics.record_delete()
        return deleted

    def exists_value(self, key: str) -> bool:
        exists = self.store.exists(key)
        if exists:
            self.metrics.record_hit()
        else:
            self.metrics.record_miss()
        return exists
