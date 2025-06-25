from typing import Any, Optional


class AgentDiagramException(Exception):
    """Base exception class for AgentDiagram application."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AgentDiagramException):
    pass


class APIKeyError(AgentDiagramException):
    pass


class APIKeyNotFoundError(APIKeyError):
    pass


class LLMServiceError(AgentDiagramException):
    pass


class DiagramExecutionError(AgentDiagramException):
    pass


class NodeExecutionError(DiagramExecutionError):
    def __init__(
        self,
        node_id: str,
        node_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.node_type = node_type
        super().__init__(f"Node {node_id} ({node_type}) failed: {message}", details)


class DependencyError(DiagramExecutionError):
    def __init__(
        self,
        node_id: str,
        missing_dependencies: list[str],
        details: Optional[dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.missing_dependencies = missing_dependencies
        super().__init__(
            f"Node {node_id} dependencies not met: {', '.join(missing_dependencies)}",
            details,
        )


class MaxIterationsError(DiagramExecutionError):
    def __init__(
        self,
        node_id: str,
        max_iterations: int,
        details: Optional[dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.max_iterations = max_iterations
        super().__init__(
            f"Node {node_id} exceeded maximum iterations ({max_iterations})", details
        )


class ConditionEvaluationError(NodeExecutionError):
    def __init__(
        self,
        node_id: str,
        condition: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.condition = condition
        super().__init__(
            node_id, "condition", f"Condition evaluation failed: {message}", details
        )


class PersonJobExecutionError(NodeExecutionError):
    def __init__(
        self,
        node_id: str,
        person_id: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.person_id = person_id
        super().__init__(
            node_id, "personJob", f"PersonJob execution failed: {message}", details
        )


class FileOperationError(AgentDiagramException):
    pass


class DatabaseError(AgentDiagramException):
    pass


class ConfigurationError(AgentDiagramException):
    pass
