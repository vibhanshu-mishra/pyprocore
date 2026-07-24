"""Mocked tests for the copied FastAPI read API starter."""

from app.main import app
from fastapi.testclient import TestClient


def test_health_route_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["procore_write_actions_enabled"] is False


def test_project_routes_use_fake_client() -> None:
    client = TestClient(app)
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json()["write_actions_enabled"] is False


def test_project_health_uses_local_fake_data() -> None:
    client = TestClient(app)
    response = client.get("/projects/352338/analytics/project-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == 352338
    assert payload["procore_api_call_required"] is False
    assert payload["external_ai_call_required"] is False
    assert payload["write_actions_enabled"] is False
