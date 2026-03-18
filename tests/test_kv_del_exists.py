from fastapi.testclient import TestClient

from app.main import app
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_delete_returns_true_when_key_exists() -> None:
    service = KVService(store=InMemoryKVStore())

    service.set_value("user:del:1", "kim")

    assert service.delete_value("user:del:1") is True
    assert service.exists_value("user:del:1") is False


def test_delete_returns_false_when_key_is_missing() -> None:
    service = KVService(store=InMemoryKVStore())

    assert service.delete_value("missing:key") is False


def test_delete_endpoint_returns_false_for_missing_key() -> None:
    client = TestClient(app)

    response = client.delete("/v1/kv/del", params={"key": "missing:key"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"deleted": False}}


def test_exists_endpoint_returns_false_after_delete() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:exists:1", "value": "lee"})
    client.delete("/v1/kv/del", params={"key": "user:exists:1"})

    response = client.get("/v1/kv/exists", params={"key": "user:exists:1"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"exists": False}}
