from fastapi.testclient import TestClient
from apps.server.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/diagrams/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "version" in data


def test_metrics_without_prometheus_client():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["message"].startswith("Prometheus client not installed")
