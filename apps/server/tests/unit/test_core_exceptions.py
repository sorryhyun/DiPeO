"""Unit tests for core exceptions."""

import pytest
from dipeo_server.core.exceptions import (
    AgentDiagramException, ValidationError, APIKeyError,
    APIKeyNotFoundError, LLMServiceError, DiagramExecutionError,
    NodeExecutionError, ConfigurationError
)


class TestAgentDiagramException:
    """Test base AgentDiagramException."""
    
    def test_base_error_creation(self):
        """Test creating base error."""
        error = AgentDiagramException("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_base_error_with_details(self):
        """Test creating error with details."""
        details = {"key": "value", "code": 123}
        error = AgentDiagramException("Test error", details=details)
        assert error.details == details


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError("Invalid input data")
        assert str(error) == "Invalid input data"
        assert isinstance(error, AgentDiagramException)
    
    def test_validation_error_with_field(self):
        """Test validation error with field information."""
        error = ValidationError("Field 'name' is required")
        assert "name" in str(error)
        assert "required" in str(error)
    
    def test_validation_error_inheritance(self):
        """Test inheritance chain."""
        error = ValidationError("test")
        assert isinstance(error, AgentDiagramException)
        assert isinstance(error, Exception)


class TestAPIKeyError:
    """Test APIKeyError exceptions."""
    
    def test_api_key_error_creation(self):
        """Test creating API key error."""
        error = APIKeyError("API key invalid")
        assert str(error) == "API key invalid"
        assert isinstance(error, AgentDiagramException)
    
    def test_api_key_not_found_error(self):
        """Test API key not found error."""
        error = APIKeyNotFoundError("API key 'test-key' not found")
        assert "test-key" in str(error)
        assert isinstance(error, APIKeyError)
        assert isinstance(error, AgentDiagramException)


class TestDiagramExecutionError:
    """Test DiagramExecutionError exceptions."""
    
    def test_diagram_execution_error_creation(self):
        """Test creating diagram execution error."""
        error = DiagramExecutionError("Execution failed")
        assert str(error) == "Execution failed"
        assert isinstance(error, AgentDiagramException)
    
    def test_node_execution_error(self):
        """Test node execution error."""
        error = NodeExecutionError(
            node_id="node1",
            node_type="person",
            message="LLM call failed"
        )
        assert "node1" in str(error)
        assert "person" in str(error)
        assert "LLM call failed" in str(error)
        assert error.node_id == "node1"
        assert error.node_type == "person"
    
    def test_node_execution_error_with_details(self):
        """Test node execution error with details."""
        details = {"error_code": "TIMEOUT", "duration": 30}
        error = NodeExecutionError(
            node_id="node2",
            node_type="job",
            message="Timeout",
            details=details
        )
        assert error.details == details


class TestLLMServiceError:
    """Test LLMServiceError exception."""
    
    def test_llm_service_error_creation(self):
        """Test creating LLM service error."""
        error = LLMServiceError("OpenAI API call failed")
        assert str(error) == "OpenAI API call failed"
        assert isinstance(error, AgentDiagramException)
    
    def test_llm_service_error_with_details(self):
        """Test LLM service error with details."""
        details = {"status_code": 429, "provider": "openai"}
        error = LLMServiceError("Rate limit exceeded", details=details)
        assert error.details == details
        assert "Rate limit" in str(error)


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test creating configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, AgentDiagramException)
    
    def test_configuration_error_with_key(self):
        """Test configuration error with specific key."""
        error = ConfigurationError("Missing required config key: 'api_key'")
        assert "api_key" in str(error)
        assert "Missing" in str(error)
    
    def test_configuration_error_with_env_var(self):
        """Test configuration error for environment variables."""
        error = ConfigurationError("Environment variable 'OPENAI_API_KEY' not set")
        assert "OPENAI_API_KEY" in str(error)
        assert "Environment variable" in str(error)


class TestExceptionHierarchy:
    """Test the exception hierarchy."""
    
    def test_all_errors_inherit_from_base(self):
        """Test that all custom errors inherit from AgentDiagramException."""
        errors = [
            ValidationError("test"),
            APIKeyError("test"),
            LLMServiceError("test"),
            DiagramExecutionError("test"),
            ConfigurationError("test")
        ]
        
        for error in errors:
            assert isinstance(error, AgentDiagramException)
            assert isinstance(error, Exception)
    
    def test_error_types_are_distinct(self):
        """Test that error types are distinct."""
        validation_err = ValidationError("test")
        api_key_err = APIKeyError("test")
        llm_err = LLMServiceError("test")
        config_err = ConfigurationError("test")
        
        # Each error should be its own type
        assert type(validation_err) != type(api_key_err)
        assert type(validation_err) != type(llm_err)
        assert type(validation_err) != type(config_err)
        
        # But all should be AgentDiagramException
        assert isinstance(validation_err, AgentDiagramException)
        assert isinstance(api_key_err, AgentDiagramException)
        assert isinstance(llm_err, AgentDiagramException)
        assert isinstance(config_err, AgentDiagramException)