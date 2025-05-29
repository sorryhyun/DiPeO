
from typing import Any, Optional


class AgentDiagramException(Exception):
    """Base exception class for AgentDiagram application."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AgentDiagramException):
    """Raised when input validation fails."""
    pass


class APIKeyError(AgentDiagramException):
    """Raised when API key operations fail."""
    pass


class LLMServiceError(AgentDiagramException):
    """Raised when LLM service calls fail."""
    pass


class DiagramExecutionError(AgentDiagramException):
    """Raised when diagram execution fails."""
    pass


class FileOperationError(AgentDiagramException):
    """Raised when file operations fail."""
    pass


class DatabaseError(AgentDiagramException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AgentDiagramException):
    """Raised when configuration is invalid."""
    pass