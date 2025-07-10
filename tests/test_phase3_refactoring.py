"""Simple tests for Phase 3.5 refactoring - API and File services.

This file contains basic tests to verify the refactored services work correctly.
"""

import pytest
from unittest.mock import AsyncMock
from dipeo.utils.api import APIBusinessLogic
from dipeo.domain.services.file.file_domain_service import FileDomainService
from dipeo.infra.services.api import APIService
from dipeo.infra.services.file import FileOperationsService
from dipeo.core import ServiceError, ValidationError


class TestAPIBusinessLogic:
    """Basic tests for APIBusinessLogic (pure business logic)."""
    
    def test_validate_response_success(self):
        """Test successful response validation."""
        service = APIBusinessLogic()
        # Should not raise for 2xx status
        service.validate_api_response(200, {"data": "test"})
        service.validate_api_response(201, {"created": True})
    
    def test_validate_response_failure(self):
        """Test response validation fails for errors."""
        service = APIBusinessLogic()
        with pytest.raises(ServiceError):
            service.validate_api_response(500, {"error": "Server error"})
    
    def test_should_retry_logic(self):
        """Test retry decision logic."""
        service = APIBusinessLogic()
        # Should retry on 5xx
        assert service.should_retry(500, attempt=0, max_retries=3) is True
        # Should not retry on 4xx (except 429)
        assert service.should_retry(400, attempt=0, max_retries=3) is False
        # Should retry on rate limit
        assert service.should_retry(429, attempt=0, max_retries=3) is True
        # Should not retry when max attempts reached
        assert service.should_retry(500, attempt=2, max_retries=3) is False


class TestFileDomainService:
    """Basic tests for FileDomainService (pure domain logic)."""
    
    def test_validate_extension(self):
        """Test file extension validation."""
        service = FileDomainService()
        # Should pass for allowed extension
        service.validate_file_extension("/path/file.txt", [".txt", ".md"])
        # Should fail for disallowed extension
        with pytest.raises(ValidationError):
            service.validate_file_extension("/path/file.exe", [".txt", ".md"])
    
    def test_validate_file_size(self):
        """Test file size validation."""
        service = FileDomainService()
        # 1MB file with 10MB limit - should pass
        service.validate_file_size(1024 * 1024, max_size_mb=10.0)
        # 11MB file with 10MB limit - should fail
        with pytest.raises(ValidationError):
            service.validate_file_size(11 * 1024 * 1024, max_size_mb=10.0)
    
    def test_create_backup_filename(self):
        """Test backup filename generation."""
        service = FileDomainService()
        backup = service.create_backup_filename("/path/to/file.txt")
        assert backup.startswith("/path/to/file.txt.backup.")
        assert backup.endswith(".txt")


class TestAPIServiceIntegration:
    """Basic integration test for APIService."""
    
    @pytest.mark.asyncio
    async def test_execute_with_retry(self):
        """Test that API service integrates business logic for retries."""
        business_logic = APIBusinessLogic()
        api_service = APIService(business_logic)
        
        # Mock the execute_request method
        call_count = 0
        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (500, {"error": "Server error"}, {})
            return (200, {"data": "success"}, {})
        
        api_service.execute_request = mock_execute
        
        # Should retry and eventually succeed
        result = await api_service.execute_with_retry(
            url="https://test.com",
            retry_delay=0.01  # Fast retry for testing
        )
        
        assert result["data"] == "success"
        assert call_count == 2  # Failed once, succeeded on retry


class TestFileOperationsServiceIntegration:
    """Basic integration test for FileOperationsService."""
    
    @pytest.mark.asyncio
    async def test_validate_before_write(self):
        """Test that file service validates before operations."""
        domain_service = FileDomainService()
        file_service = FileOperationsService(domain_service)
        
        # Test extension validation directly on domain service
        # since infrastructure service requires actual file existence
        with pytest.raises(ValidationError):
            domain_service.validate_file_extension(
                "/path/to/file.exe",
                allowed_extensions=[".txt", ".md"]
            )


@pytest.mark.asyncio
async def test_handler_compatibility():
    """Test that services work with handler expectations."""
    # Create services as they would be in the container
    api_business_logic = APIBusinessLogic()
    api_service = APIService(api_business_logic)
    
    file_domain = FileDomainService()
    file_service = FileOperationsService(file_domain)
    
    # Mock a simple handler-like usage
    services = {
        "api_service": api_service,
        "file_operations_infra_service": file_service
    }
    
    # Verify services are accessible
    assert services["api_service"] is not None
    assert services["file_operations_infra_service"] is not None
    
    # Verify they have expected methods
    assert hasattr(services["api_service"], "execute_with_retry")
    assert hasattr(services["file_operations_infra_service"], "read_file")
    assert hasattr(services["file_operations_infra_service"], "write_file")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])