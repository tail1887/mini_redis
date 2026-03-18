from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
import app.routers.dashboard as dashboard_router


def test_dashboard_page_renders() -> None:
    client = TestClient(app)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Mini Redis Test Dashboard" in response.text


def test_dashboard_run_tests_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(dashboard_router.test_runner, "start", lambda: True)
    client = TestClient(app)
    response = client.post("/v1/dashboard/run-tests")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"started": True, "message": "test run started"},
    }


def test_dashboard_status_endpoint(monkeypatch) -> None:
    fake_status = {
        "running": False,
        "startedAt": None,
        "finishedAt": None,
        "lastExitCode": 0,
        "lastCommand": ["python", "-m", "pytest"],
        "lastError": None,
        "summary": {"total": 10, "passed": 9, "failed": 1, "skipped": 0, "errors": 0},
        "phaseSummary": {
            "phase0": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
            "phase1": {"total": 3, "passed": 3, "failed": 0, "skipped": 0},
            "phase2": {"total": 3, "passed": 2, "failed": 1, "skipped": 0},
            "phase3": {"total": 2, "passed": 2, "failed": 0, "skipped": 0},
            "phase4": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
        },
        "reportPath": "artifacts/pytest-report.json",
        "lastOutputTail": "output",
    }
    monkeypatch.setattr(dashboard_router.test_runner, "status", lambda: fake_status)

    client = TestClient(app)
    response = client.get("/v1/dashboard/test-status")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": fake_status}
