from fastapi.testclient import TestClient

from app.main import app


def test_invalidate_prefix_deletes_only_matching_keys() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})
    client.post("/v1/kv/set", json={"key": "user:2", "value": "lee"})
    client.post("/v1/kv/set", json={"key": "team:1", "value": "delta"})

    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:"})
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"deletedCount": 2}}

    user_check = client.get("/v1/kv/get", params={"key": "user:1"})
    team_check = client.get("/v1/kv/get", params={"key": "team:1"})
    assert user_check.status_code == 404
    assert team_check.status_code == 200


def test_invalidate_prefix_rejects_invalid_prefix() -> None:
    client = TestClient(app)
    response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user"})

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_metrics_cache_returns_basic_counters() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:metrics", "value": "v"})
    client.get("/v1/kv/get", params={"key": "user:metrics"})  # hit
    client.get("/v1/kv/get", params={"key": "user:missing"})  # miss
    client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:"})  # invalidation + delete

    metrics = client.get("/v1/metrics/cache")
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["success"] is True
    assert payload["data"]["hits"] >= 1
    assert payload["data"]["misses"] >= 1
    assert payload["data"]["invalidations"] >= 1
