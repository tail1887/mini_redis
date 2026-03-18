from __future__ import annotations

from fastapi.testclient import TestClient

import app.routers.kv as kv_router
from app.main import app
from app.services.cache_metrics import CacheMetrics, cache_metrics


def test_cache_metrics_records_and_resets_counters() -> None:
    metrics = CacheMetrics()

    metrics.record_hit()
    metrics.record_hit()
    metrics.record_miss()
    metrics.record_delete()
    metrics.record_error()

    snapshot = metrics.snapshot()
    assert snapshot.hits == 2
    assert snapshot.misses == 1
    assert snapshot.deletes == 1
    assert snapshot.invalidations == 0
    assert snapshot.errors == 1

    metrics.reset()
    snapshot = metrics.snapshot()
    assert snapshot.hits == 0
    assert snapshot.misses == 0
    assert snapshot.deletes == 0
    assert snapshot.invalidations == 0
    assert snapshot.errors == 0


def test_metrics_endpoint_exposes_current_counts() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:metrics", "value": "kim"})
    client.get("/v1/kv/get", params={"key": "user:metrics"})
    client.get("/v1/kv/get", params={"key": "missing:key"})
    client.get("/v1/kv/exists", params={"key": "user:metrics"})
    client.get("/v1/kv/exists", params={"key": "missing:key"})
    client.delete("/v1/kv/del", params={"key": "user:metrics"})

    response = client.get("/v1/metrics/cache")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {
            "hits": 2,
            "misses": 2,
            "deletes": 1,
            "invalidations": 0,
            "errors": 0,
        },
    }


def test_metrics_endpoint_counts_validation_and_internal_errors() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    client.get("/v1/kv/get")

    def broken_get_value(_: str) -> str | None:
        raise RuntimeError("boom")

    kv_router.service.set_value("user:error", "kim")
    original_get_value = kv_router.service.get_value
    kv_router.service.get_value = broken_get_value
    try:
        response = client.get("/v1/kv/get", params={"key": "user:error"})
    finally:
        kv_router.service.get_value = original_get_value

    assert response.status_code == 500
    snapshot = cache_metrics.snapshot()
    assert snapshot.hits == 0
    assert snapshot.misses == 0
    assert snapshot.deletes == 0
    assert snapshot.invalidations == 0
    assert snapshot.errors == 2
