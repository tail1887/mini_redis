from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_service_set_and_get_roundtrip() -> None:
    service = KVService(store=InMemoryKVStore())

    stored = service.set_value("user:1", "kim")
    value = service.get_value("user:1")

    assert stored is True
    assert value == "kim"


def test_service_get_missing_key_returns_none() -> None:
    service = KVService(store=InMemoryKVStore())

    assert service.get_value("missing:key") is None
