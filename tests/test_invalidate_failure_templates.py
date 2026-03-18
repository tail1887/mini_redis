import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skip(reason="Stage-3 template: validate over-delete safety guard with protected namespaces")
def test_invalidate_prefix_over_delete_template() -> None:
    """
    Template scenario:
    - create mixed keys across multiple namespaces
    - execute invalidate-prefix with a broad prefix candidate
    - assert protected namespace keys are not deleted unexpectedly
    """
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:1", "value": "kim"})
    client.post("/v1/kv/set", json={"key": "user:profile:1", "value": "profile"})
    client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:"})

    response = client.get("/v1/kv/get", params={"key": "user:profile:1"})
    assert response.status_code in (200, 404)


@pytest.mark.skip(reason="Stage-3 template: validate under-delete with mixed ttl/live keys")
def test_invalidate_prefix_under_delete_template() -> None:
    """
    Template scenario:
    - create multiple keys with same prefix (some live, some expired transitions)
    - run invalidate-prefix once
    - assert all targeted live keys are removed
    """
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "cart:1", "value": "A"})
    client.post("/v1/kv/set", json={"key": "cart:2", "value": "B"})
    client.post("/v1/kv/invalidate-prefix", json={"prefix": "cart:"})

    response = client.get("/v1/kv/exists", params={"key": "cart:2"})
    assert response.status_code == 200
