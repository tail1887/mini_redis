from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import app.routers.kv as kv_router
from app.main import app
from app.stores.kv_store import InMemoryKVStore


def test_system_durability_reports_disabled_by_default() -> None:
    client = TestClient(app)
    response = client.get("/v1/system/durability")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["enabled"] is False


def test_system_durability_reports_enabled_store(tmp_path: Path) -> None:
    kv_router.service.store = InMemoryKVStore(
        aof_path=tmp_path / "kv.aof",
        snapshot_path=tmp_path / "kv.snapshot.json",
        snapshot_every=3,
    )
    client = TestClient(app)
    response = client.get("/v1/system/durability")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["enabled"] is True
    assert payload["data"]["snapshotEvery"] == 3
