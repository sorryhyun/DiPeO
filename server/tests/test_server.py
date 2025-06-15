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
    # Test with JSON accept header (for test compatibility)
    response = client.get("/metrics", headers={"accept": "application/json"})
    assert response.status_code == 200
    
    # Try to parse as JSON
    data = response.json()
    
    # Check if prometheus_client is installed
    try:
        import prometheus_client
        # If installed, should return metrics data in JSON format
        assert "metrics" in data
        assert "format" in data
        assert data["format"] == "prometheus"
    except ImportError:
        # If not installed, should return installation message
        assert "message" in data
        assert data["message"].startswith("Prometheus client not installed")


def test_metrics_prometheus_format():
    # Test default prometheus text format
    response = client.get("/metrics", headers={"accept": "text/plain"})
    assert response.status_code == 200
    
    # Check content type
    try:
        import prometheus_client
        # If prometheus is installed, should return text format
        assert response.headers["content-type"].startswith("text/plain")
    except ImportError:
        # If not installed, returns JSON
        data = response.json()
        assert data["message"].startswith("Prometheus client not installed")
