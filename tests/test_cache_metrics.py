from __future__ import annotations

from fastapi.testclient import TestClient

import app.routers.kv as kv_router
from app.main import app
from app.observability.cache_metrics import CacheMetrics, cache_metrics
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_cache_metrics_records_and_resets_counters() -> None:
    metrics = CacheMetrics()

    metrics.record_hit()
    metrics.record_hit()
    metrics.record_miss()
    metrics.record_delete()
    metrics.record_error()

    assert metrics.snapshot() == {
        "hits": 2,
        "misses": 1,
        "deletes": 1,
        "errors": 1,
    }

    metrics.reset()
    assert metrics.snapshot() == {
        "hits": 0,
        "misses": 0,
        "deletes": 0,
        "errors": 0,
    }


def test_service_updates_cache_metrics_for_get_exists_and_delete() -> None:
    metrics = CacheMetrics()
    service = KVService(store=InMemoryKVStore(), metrics=metrics)

    service.set_value("user:1", "kim")
    assert service.get_value("user:1") == "kim"
    assert service.get_value("missing:key") is None
    assert service.exists_value("user:1") is True
    assert service.exists_value("missing:key") is False
    assert service.delete_value("user:1") is True
    assert service.delete_value("user:1") is False

    assert metrics.snapshot() == {
        "hits": 2,
        "misses": 2,
        "deletes": 1,
        "errors": 0,
    }


def test_metrics_endpoint_exposes_current_counts() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:metrics", "value": "kim"})
    client.get("/v1/kv/get", params={"key": "user:metrics"})
    client.get("/v1/kv/get", params={"key": "missing:key"})
    client.delete("/v1/kv/del", params={"key": "user:metrics"})

    response = client.get("/v1/metrics/cache")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"hits": 1, "misses": 1, "deletes": 1, "errors": 0},
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
    assert cache_metrics.snapshot() == {
        "hits": 0,
        "misses": 0,
        "deletes": 0,
        "errors": 2,
    }
