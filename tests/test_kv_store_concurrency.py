from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.stores.kv_store import InMemoryKVStore


def test_store_handles_parallel_set_and_get_without_losing_values() -> None:
    store = InMemoryKVStore()

    def worker(index: int) -> tuple[bool, str | None]:
        key = f"user:parallel:{index}"
        stored = store.set(key, f"value-{index}")
        value = store.get(key)
        return stored, value

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(worker, range(200)))

    assert all(stored is True for stored, _ in results)
    assert all(value is not None for _, value in results)
    assert store.invalidate_prefix("user:parallel:") == 200


def test_store_parallel_expire_and_persist_keeps_state_consistent() -> None:
    store = InMemoryKVStore()
    key_count = 100

    for index in range(key_count):
        store.set(f"user:ttl:{index}", f"value-{index}")

    def expire_worker(index: int) -> bool:
        return store.expire(f"user:ttl:{index}", 30)

    with ThreadPoolExecutor(max_workers=12) as executor:
        expire_results = list(executor.map(expire_worker, range(key_count)))

    assert all(expire_results)

    def persist_worker(index: int) -> bool:
        return store.persist(f"user:ttl:{index}")

    with ThreadPoolExecutor(max_workers=12) as executor:
        persist_results = list(executor.map(persist_worker, range(key_count)))

    assert all(persist_results)
    assert all(store.ttl(f"user:ttl:{index}") == -1 for index in range(key_count))
