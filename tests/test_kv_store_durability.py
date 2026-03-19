from __future__ import annotations

from pathlib import Path

from app.stores.kv_store import InMemoryKVStore


def test_store_recovers_data_from_aof_after_restart(tmp_path: Path) -> None:
    aof_path = tmp_path / "kv.aof"
    snapshot_path = tmp_path / "kv.snapshot.json"

    first_store = InMemoryKVStore(aof_path=aof_path, snapshot_path=snapshot_path)
    first_store.set("user:durable:1", "A")
    first_store.set("user:durable:2", "B")
    first_store.delete("user:durable:2")

    restarted_store = InMemoryKVStore(aof_path=aof_path, snapshot_path=snapshot_path)
    assert restarted_store.get("user:durable:1") == "A"
    assert restarted_store.get("user:durable:2") is None


def test_store_drops_expired_key_during_restart_recovery(tmp_path: Path) -> None:
    current_time = 1_000.0

    def time_fn() -> float:
        return current_time

    aof_path = tmp_path / "kv.aof"
    snapshot_path = tmp_path / "kv.snapshot.json"
    first_store = InMemoryKVStore(time_fn=time_fn, aof_path=aof_path, snapshot_path=snapshot_path)
    first_store.set("user:durable:ttl", "value")
    assert first_store.expire("user:durable:ttl", 5) is True

    current_time += 10
    restarted_store = InMemoryKVStore(time_fn=time_fn, aof_path=aof_path, snapshot_path=snapshot_path)
    assert restarted_store.get("user:durable:ttl") is None
    assert restarted_store.ttl("user:durable:ttl") == -2


def test_store_writes_snapshot_and_recovers_from_snapshot(tmp_path: Path) -> None:
    aof_path = tmp_path / "kv.aof"
    snapshot_path = tmp_path / "kv.snapshot.json"
    store = InMemoryKVStore(aof_path=aof_path, snapshot_path=snapshot_path, snapshot_every=2)
    store.set("user:snapshot:1", "A")
    store.set("user:snapshot:2", "B")

    assert snapshot_path.exists() is True
    assert aof_path.exists() is True
    assert aof_path.read_text(encoding="utf-8") == ""

    restarted_store = InMemoryKVStore(aof_path=aof_path, snapshot_path=snapshot_path, snapshot_every=2)
    assert restarted_store.get("user:snapshot:1") == "A"
    assert restarted_store.get("user:snapshot:2") == "B"
