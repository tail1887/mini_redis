from __future__ import annotations

import app.routers.kv as kv_router

from fastapi.testclient import TestClient

from app.main import app


def test_missing_key_returns_standard_not_found_error() -> None:
    client = TestClient(app)
    response = client.get("/v1/kv/get", params={"key": "missing:key"})

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {"code": "KEY_NOT_FOUND", "message": "key not found"},
    }


def test_validation_errors_use_standard_error_schema() -> None:
    client = TestClient(app)

    response = client.get("/v1/kv/get")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "INVALID_INPUT", "message": "key is required"},
    }


def test_body_validation_errors_use_standard_error_schema() -> None:
    client = TestClient(app)

    response = client.post("/v1/kv/set", json={"value": "kim"})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "INVALID_INPUT", "message": "key is required"},
    }


def test_empty_key_returns_standard_invalid_input_error() -> None:
    client = TestClient(app)

    response = client.delete("/v1/kv/del", params={"key": ""})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "INVALID_INPUT", "message": "key is required"},
    }


def test_unexpected_errors_map_to_internal_error(monkeypatch) -> None:
    def broken_get_value(_: str) -> str | None:
        raise RuntimeError("boom")

    monkeypatch.setattr(kv_router.service, "get_value", broken_get_value)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/v1/kv/get", params={"key": "user:1"})

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": {"code": "INTERNAL_ERROR", "message": "internal server error"},
    }
