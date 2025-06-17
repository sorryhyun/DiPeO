
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


class APIKeyNotFoundError(APIKeyError):
    """Raised when an API key is not found."""
    pass


class LLMServiceError(AgentDiagramException):
    """Raised when LLM service calls fail."""
    pass


class DiagramExecutionError(AgentDiagramException):
    """Raised when diagram execution fails."""
    pass


class NodeExecutionError(DiagramExecutionError):
    """Raised when a specific node fails to execute."""
    
    def __init__(self, node_id: str, node_type: str, message: str, details: Optional[dict[str, Any]] = None):
        self.node_id = node_id
        self.node_type = node_type
        super().__init__(f"Node {node_id} ({node_type}) failed: {message}", details)


class DependencyError(DiagramExecutionError):
    """Raised when node dependencies aren't met."""
    
    def __init__(self, node_id: str, missing_dependencies: list[str], details: Optional[dict[str, Any]] = None):
        self.node_id = node_id
        self.missing_dependencies = missing_dependencies
        super().__init__(
            f"Node {node_id} dependencies not met: {', '.join(missing_dependencies)}", 
            details
        )


class MaxIterationsError(DiagramExecutionError):
    """Raised when max iterations are exceeded."""
    
    def __init__(self, node_id: str, max_iterations: int, details: Optional[dict[str, Any]] = None):
        self.node_id = node_id
        self.max_iterations = max_iterations
        super().__init__(
            f"Node {node_id} exceeded maximum iterations ({max_iterations})", 
            details
        )


class ConditionEvaluationError(NodeExecutionError):
    """Raised when condition evaluation fails."""
    
    def __init__(self, node_id: str, condition: str, message: str, details: Optional[dict[str, Any]] = None):
        self.condition = condition
        super().__init__(node_id, "condition", f"Condition evaluation failed: {message}", details)


class PersonJobExecutionError(NodeExecutionError):
    """Raised when PersonJob node execution fails."""
    
    def __init__(self, node_id: str, person_id: str, message: str, details: Optional[dict[str, Any]] = None):
        self.person_id = person_id
        super().__init__(node_id, "personJob", f"PersonJob execution failed: {message}", details)


class FileOperationError(AgentDiagramException):
    """Raised when file operations fail."""
    pass


class DatabaseError(AgentDiagramException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AgentDiagramException):
    """Raised when configuration is invalid."""
    pass