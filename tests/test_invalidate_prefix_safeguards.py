from fastapi.testclient import TestClient

from app.core.errors import APIError
from app.main import app
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_invalidate_prefix_service_deletes_only_matching_namespace() -> None:
    store = InMemoryKVStore()
    service = KVService(store=store)
    store.set("user:1", "kim")
    store.set("user:2", "lee")
    store.set("user_profile:1", "park")
    store.set("team:user:1", "choi")

    deleted_count = service.invalidate_prefix("user:")

    assert deleted_count == 2
    assert store.exists("user:1") is False
    assert store.exists("user:2") is False
    assert store.exists("user_profile:1") is True
    assert store.exists("team:user:1") is True


def test_invalidate_prefix_service_rejects_prefix_with_no_live_keys() -> None:
    store = InMemoryKVStore()
    service = KVService(store=store)
    store.set("user:1", "kim")

    try:
        service.invalidate_prefix("order:")
    except APIError as exc:
        assert exc.code == "PREFIX_INVALID"
        assert exc.status_code == 400
        assert exc.message == "prefix did not match any live keys"
    else:
        raise AssertionError("Expected PREFIX_INVALID for unmatched prefix")


def test_invalidate_prefix_ignores_expired_keys_when_counting_deletes() -> None:
    current_time = {"value": 100.0}
    store = InMemoryKVStore(time_fn=lambda: current_time["value"])
    service = KVService(store=store)
    store.set("user:expired", "kim")
    store.set("user:live", "lee")
    store.expire("user:expired", 1)

    current_time["value"] = 101.0
    deleted_count = service.invalidate_prefix("user:")

    assert deleted_count == 1
    assert store.exists("user:expired") is False
    assert store.exists("user:live") is False


def test_invalidate_prefix_endpoint_returns_deleted_count_for_matching_keys() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})
    client.post("/v1/kv/set", json={"key": "user:2", "value": "lee"})
    client.post("/v1/kv/set", json={"key": "team:user:1", "value": "park"})

    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"deletedCount": 2}}

    assert client.get("/v1/kv/exists", params={"key": "user:1"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "user:2"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "team:user:1"}).json()["data"]["exists"] is True


def test_invalidate_prefix_endpoint_rejects_unmatched_prefix() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})

    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "order:"})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "PREFIX_INVALID", "message": "prefix did not match any live keys"},
    }
