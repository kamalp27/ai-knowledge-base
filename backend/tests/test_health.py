import pytest
from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    """Test that GET /health returns 200 and expected health metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_root_ready_endpoint(client: TestClient):
    """Test that GET /ready returns 200 and expected readiness checks."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "ok"]
    assert "storage_ready" in data
    assert data["storage_ready"] is True
    assert "services" in data
    assert data["services"].get("api") == "up"


def test_api_v1_health_endpoint(client: TestClient):
    """Test that GET /api/v1/health returns 200 and matches health schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_api_v1_ready_endpoint(client: TestClient):
    """Test that GET /api/v1/ready returns 200 and matches readiness schema."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "ok"]
    assert data["storage_ready"] is True


def test_root_endpoint(client: TestClient):
    """Test that GET / returns API welcome metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "/docs" in data["docs"]
