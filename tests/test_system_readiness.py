from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_system_readiness_false_when_gate_closed(monkeypatch) -> None:
    monkeypatch.setenv("RELEASE_READY", "false")
    client = TestClient(app)
    response = client.get("/v1/system/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["ready"] is False
    assert payload["data"]["stage"] == 5


def test_system_readiness_true_when_gate_open(monkeypatch) -> None:
    monkeypatch.setenv("RELEASE_READY", "true")
    client = TestClient(app)
    response = client.get("/v1/system/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["ready"] is True
    assert payload["data"]["stage"] == 5
