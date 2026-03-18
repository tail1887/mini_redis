from fastapi.testclient import TestClient

from app.main import app
from app.stores.kv_store import InMemoryKVStore


def test_invalidate_prefix_deletes_requested_namespace_range_only() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})
    client.post("/v1/kv/set", json={"key": "user:profile:1", "value": "profile"})
    client.post("/v1/kv/set", json={"key": "team:user:1", "value": "delta"})

    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"deletedCount": 2}}
    assert client.get("/v1/kv/exists", params={"key": "user:1"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "user:profile:1"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "team:user:1"}).json()["data"]["exists"] is True


def test_invalidate_prefix_can_target_nested_namespace_without_over_deleting() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})
    client.post("/v1/kv/set", json={"key": "user:profile:1", "value": "profile-1"})
    client.post("/v1/kv/set", json={"key": "user:profile:2", "value": "profile-2"})
    client.post("/v1/kv/set", json={"key": "user:settings:1", "value": "settings"})

    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:profile:"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"deletedCount": 2}}
    assert client.get("/v1/kv/exists", params={"key": "user:1"}).json()["data"]["exists"] is True
    assert client.get("/v1/kv/exists", params={"key": "user:profile:1"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "user:profile:2"}).json()["data"]["exists"] is False
    assert client.get("/v1/kv/exists", params={"key": "user:settings:1"}).json()["data"]["exists"] is True


def test_invalidate_prefix_skips_expired_keys_in_delete_count() -> None:
    current_time = 1_000.0

    def time_fn() -> float:
        return current_time

    store = InMemoryKVStore(time_fn=time_fn)
    store.set("cart:1", "A")
    store.set("cart:2", "B")
    store.expire("cart:1", 1)

    current_time += 2

    deleted_count = store.invalidate_prefix("cart:")

    assert deleted_count == 1
    assert store.exists("cart:1") is False
    assert store.exists("cart:2") is False
