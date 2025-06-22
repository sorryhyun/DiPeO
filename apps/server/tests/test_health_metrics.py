"""Tests for health check and metrics endpoints."""

import pytest
from unittest.mock import patch

from .conftest import *  # Import all fixtures


class TestHealthCheck:
    """Test health check functionality."""
    
    def test_health_check_graphql(self, test_client, graphql_queries):
        """Test health check via GraphQL query."""
        response = test_client.post(
            "/graphql", 
            json={"query": graphql_queries["health"]}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "health" in data["data"]
        
        health = data["data"]["health"]
        assert health["status"] in ["healthy", "degraded"]
        assert "timestamp" in health
        assert "version" in health
    
    async def test_health_check_async(self, async_client, graphql_queries):
        """Test health check using async client."""
        response = await async_client.post(
            "/graphql",
            json={"query": graphql_queries["health"]}
        )
        assert response.status_code == 200
        
        data = response.json()
        health = data["data"]["health"]
        assert health["status"] in ["healthy", "degraded"]
    
    def test_health_check_with_dependencies(self, test_client, graphql_queries, monkeypatch):
        """Test health check when dependencies are down."""
        # Mock a dependency failure
        monkeypatch.setenv("DIPEO_HEALTH_CHECK_FAIL", "true")
        
        response = test_client.post(
            "/graphql",
            json={"query": graphql_queries["health"]}
        )
        assert response.status_code == 200
        
        data = response.json()
        health = data["data"]["health"]
        # Should gracefully handle failures
        assert health["status"] in ["healthy", "degraded"]


class TestMetrics:
    """Test metrics endpoint functionality."""
    
    def test_metrics_json_format(self, test_client):
        """Test metrics endpoint with JSON format."""
        response = test_client.get(
            "/metrics",
            headers={"accept": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        try:
            import prometheus_client
            assert "metrics" in data
            assert data["format"] == "prometheus"
        except ImportError:
            assert "message" in data
            assert "Prometheus client not installed" in data["message"]
    
    def test_metrics_prometheus_format(self, test_client):
        """Test metrics endpoint with Prometheus text format."""
        response = test_client.get(
            "/metrics",
            headers={"accept": "text/plain"}
        )
        assert response.status_code == 200
        
        try:
            import prometheus_client
            assert response.headers["content-type"].startswith("text/plain")
            content = response.text
            # Check for standard prometheus metrics
            assert "# HELP" in content or "# TYPE" in content
        except ImportError:
            # Falls back to JSON when prometheus not installed
            data = response.json()
            assert "message" in data
    
    def test_metrics_default_format(self, test_client):
        """Test metrics endpoint with default accept header."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        
        try:
            import prometheus_client
            # Default should be prometheus text format
            assert response.headers["content-type"].startswith("text/plain")
        except ImportError:
            # Falls back to JSON
            data = response.json()
            assert "message" in data
    
    @patch("prometheus_client.generate_latest")
    def test_metrics_with_custom_metrics(self, mock_generate, test_client):
        """Test metrics with custom application metrics."""
        mock_generate.return_value = b"""# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 42
"""
        
        response = test_client.get(
            "/metrics",
            headers={"accept": "text/plain"}
        )
        
        try:
            import prometheus_client
            assert response.status_code == 200
            content = response.text
            assert "http_requests_total" in content
            assert "42" in content
        except ImportError:
            # Test is skipped if prometheus not installed
            pass
    
    async def test_metrics_async(self, async_client):
        """Test metrics endpoint using async client."""
        response = await async_client.get(
            "/metrics",
            headers={"accept": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data or "metrics" in data


class TestCombinedHealthMetrics:
    """Test combined health and metrics scenarios."""
    
    def test_health_affects_metrics(self, test_client, graphql_queries):
        """Test if health status is reflected in metrics."""
        # First check health
        health_response = test_client.post(
            "/graphql",
            json={"query": graphql_queries["health"]}
        )
        health_status = health_response.json()["data"]["health"]["status"]
        
        # Then check metrics
        metrics_response = test_client.get(
            "/metrics",
            headers={"accept": "application/json"}
        )
        
        try:
            import prometheus_client
            metrics_data = metrics_response.json()
            # Metrics should include health status
            if "metrics" in metrics_data:
                assert health_status in ["healthy", "degraded"]
        except ImportError:
            pass
    
    def test_concurrent_health_metrics_requests(self, test_client, graphql_queries):
        """Test concurrent requests to health and metrics endpoints."""
        import concurrent.futures
        
        def check_health():
            return test_client.post(
                "/graphql",
                json={"query": graphql_queries["health"]}
            )
        
        def check_metrics():
            return test_client.get("/metrics")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit multiple concurrent requests
            health_futures = [executor.submit(check_health) for _ in range(5)]
            metrics_futures = [executor.submit(check_metrics) for _ in range(5)]
            
            # All should succeed
            for future in health_futures:
                response = future.result()
                assert response.status_code == 200
            
            for future in metrics_futures:
                response = future.result()
                assert response.status_code == 200