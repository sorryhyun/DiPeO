"""Integration tests for API endpoints."""

import pytest
import json
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from ..main import app
from .fixtures.diagrams import DiagramFixtures
from .fixtures.mocks import MockLLMService, MockAPIKeyService, MockMemoryService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_services_patch():
    """Patch services with mocks for integration tests."""
    with patch('apps.server.src.services.llm_service.LLMService') as mock_llm, \
         patch('apps.server.src.services.api_key_service.APIKeyService') as mock_api_keys, \
         patch('apps.server.src.services.memory_service.MemoryService') as mock_memory:
        
        # Configure mock instances
        mock_llm.return_value = MockLLMService()
        mock_api_keys.return_value = MockAPIKeyService()
        mock_memory.return_value = MockMemoryService()
        
        yield {
            'llm_service': mock_llm.return_value,
            'api_key_service': mock_api_keys.return_value,
            'memory_service': mock_memory.return_value
        }


class TestDiagramExecutionAPI:
    """Test diagram execution API endpoints."""
    
    def test_run_diagram_simple(self, client, mock_services_patch):
        """Test diagram execution API with simple diagram."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        response = client.post("/api/v2/run-diagram", json=diagram)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "context" in result
        assert "total_cost" in result
        assert result["total_cost"] >= 0
    
    def test_run_diagram_branching(self, client, mock_services_patch):
        """Test diagram execution with branching."""
        diagram = DiagramFixtures.branching_diagram()
        
        response = client.post("/api/v2/run-diagram", json=diagram)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "context" in result
        assert result["total_cost"] >= 0
    
    def test_run_diagram_invalid(self, client, mock_services_patch):
        """Test diagram execution with invalid diagram."""
        invalid_diagram = {
            "nodes": [],  # Empty nodes
            "arrows": [],
            "persons": [],
            "apiKeys": []
        }
        
        response = client.post("/api/v2/run-diagram", json=invalid_diagram)
        
        # Should return error for invalid diagram
        assert response.status_code == 400 or response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_v2_run_diagram_streaming(self, client, mock_services_patch):
        """Test V2 diagram execution with streaming."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Note: Testing SSE streaming with TestClient is complex
        # This test verifies the endpoint exists and accepts requests
        response = client.post(
            "/api/v2/run-diagram",
            json=diagram,
            headers={"Accept": "application/json"}  # Non-streaming request
        )
        
        # V2 endpoint should exist
        assert response.status_code != 404
    
    def test_v2_execution_capabilities(self, client):
        """Test V2 execution capabilities endpoint."""
        response = client.get("/api/v2/execution-capabilities")
        
        assert response.status_code == 200
        capabilities = response.json()
        
        assert "supported_node_types" in capabilities
        assert "features" in capabilities
        assert isinstance(capabilities["supported_node_types"], list)


class TestAPIKeyManagement:
    """Test API key management endpoints."""
    
    def test_list_api_keys(self, client, mock_services_patch):
        """Test listing API keys."""
        response = client.get("/api/api-keys")
        
        assert response.status_code == 200
        keys = response.json()
        
        assert isinstance(keys, list)
        if keys:
            key = keys[0]
            assert "id" in key
            assert "name" in key
            assert "service" in key
            assert "key" not in key  # Should not expose raw key
    
    def test_create_api_key(self, client, mock_services_patch):
        """Test creating an API key."""
        key_data = {
            "name": "Test Key",
            "service": "openai",
            "key": "sk-test123"
        }
        
        response = client.post("/api/api-keys", json=key_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "id" in result
        assert result["name"] == "Test Key"
        assert result["service"] == "openai"
        assert "key" not in result  # Should not return raw key
    
    def test_delete_api_key(self, client, mock_services_patch):
        """Test deleting an API key."""
        # First create a key
        key_data = {
            "name": "Test Key",
            "service": "openai", 
            "key": "sk-test123"
        }
        
        create_response = client.post("/api/api-keys", json=key_data)
        assert create_response.status_code == 200
        key_id = create_response.json()["id"]
        
        # Then delete it
        response = client.delete(f"/api/api-keys/{key_id}")
        
        assert response.status_code == 200


class TestFileOperations:
    """Test file operation endpoints."""
    
    def test_upload_file(self, client):
        """Test file upload."""
        test_content = b"This is a test file"
        
        response = client.post(
            "/api/upload-file",
            files={"file": ("test.txt", test_content, "text/plain")}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "filename" in result
        assert "message" in result
    
    def test_save_diagram(self, client, mock_services_patch):
        """Test saving diagram to server."""
        diagram = DiagramFixtures.simple_linear_diagram()
        save_data = {
            "diagram": diagram,
            "filename": "test_diagram.json",
            "format": "json"
        }
        
        response = client.post("/api/save", json=save_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "message" in result


class TestConversationEndpoints:
    """Test conversation management endpoints."""
    
    def test_get_conversations(self, client, mock_services_patch):
        """Test getting conversations."""
        response = client.get("/api/conversations")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "conversations" in result
        assert isinstance(result["conversations"], list)
    
    def test_clear_conversations(self, client, mock_services_patch):
        """Test clearing conversations."""
        response = client.post("/api/conversations/clear")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "message" in result


class TestMonitoringEndpoints:
    """Test monitoring and statistics endpoints."""
    
    def test_monitor_stream_endpoint_exists(self, client):
        """Test monitoring stream endpoint exists."""
        # Note: Testing SSE streaming requires more complex setup
        # This just verifies the endpoint is available
        response = client.get("/api/monitor/stream")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


class TestDiagramConversion:
    """Test diagram import/export endpoints."""
    
    def test_export_uml(self, client, mock_services_patch):
        """Test exporting diagram to UML."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        response = client.post("/api/export-uml", json=diagram)
        
        assert response.status_code == 200
        # Response should be UML text
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        uml_content = response.text
        assert "@startuml" in uml_content or "start" in uml_content.lower()
    
    def test_import_uml(self, client, mock_services_patch):
        """Test importing UML to diagram."""
        uml_content = """
        @startuml
        start
        :Process;
        end
        @enduml
        """
        
        response = client.post("/api/import-uml", json={"uml": uml_content})
        
        # Should attempt to parse UML (may fail due to mock, but endpoint should exist)
        assert response.status_code != 404


class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v2/run-diagram",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client, mock_services_patch):
        """Test handling of missing required fields."""
        incomplete_diagram = {
            "nodes": [{"id": "test"}]  # Missing required fields
        }
        
        response = client.post("/api/v2/run-diagram", json=incomplete_diagram)
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_nonexistent_endpoint(self, client):
        """Test handling of nonexistent endpoints."""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404


class TestPerformance:
    """Basic performance tests."""
    
    def test_api_response_time(self, client, mock_services_patch):
        """Test API response times are reasonable."""
        import time
        
        diagram = DiagramFixtures.simple_linear_diagram()
        
        start_time = time.time()
        response = client.post("/api/v2/run-diagram", json=diagram)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (10 seconds for test)
        response_time = end_time - start_time
        assert response_time < 10.0
    
    def test_concurrent_requests(self, client, mock_services_patch):
        """Test handling multiple concurrent requests."""
        import concurrent.futures
        import threading
        
        diagram = DiagramFixtures.simple_linear_diagram()
        
        def make_request():
            return client.post("/api/v2/run-diagram", json=diagram)
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestSecurityFeatures:
    """Test security-related features."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v2/run-diagram")
        
        # Should have CORS headers for development
        assert "access-control-allow-origin" in response.headers
    
    def test_file_path_validation(self, client):
        """Test file path validation prevents traversal attacks."""
        # This would test the validate_file_path utility
        # Implementation depends on how file operations are exposed
        pass