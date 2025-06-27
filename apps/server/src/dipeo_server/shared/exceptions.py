"""Server exception module.

This module re-exports exceptions from dipeo_core.errors for backward compatibility
and defines server-specific exceptions that extend the core taxonomy.
"""

from typing import Any, Optional

# Re-export base exceptions
from dipeo_core.base.exceptions import (
    DiPeOError,
    ValidationError,
    ConfigurationError,
    ServiceError,
    ExecutionError,
)

# Re-export core exceptions for backward compatibility
from dipeo_core.errors import (
    NodeExecutionError,
    DependencyError,
    MaxIterationsError,
    TimeoutError,
    APIKeyError,
    APIKeyNotFoundError,
    LLMServiceError,
    FileOperationError,
    DiagramError,
    DiagramNotFoundError,
    InvalidDiagramError,
)

# Legacy alias
AgentDiagramException = DiPeOError

# Legacy alias for DiagramExecutionError -> ExecutionError
DiagramExecutionError = ExecutionError


# Server-specific exceptions that extend the core taxonomy
class ConditionEvaluationError(NodeExecutionError):
    """Error when evaluating a condition node."""
    
    def __init__(
        self,
        node_id: str,
        condition: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.condition = condition
        super().__init__(
            node_id=node_id,
            node_type="condition",
            message=f"Condition evaluation failed: {message}",
            details=details,
        )


class PersonJobExecutionError(NodeExecutionError):
    """Error when executing a person job node."""
    
    def __init__(
        self,
        node_id: str,
        person_id: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.person_id = person_id
        super().__init__(
            node_id=node_id,
            node_type="personJob",
            message=f"PersonJob execution failed: {message}",
            details=details,
        )


class DatabaseError(ServiceError):
    """Error when performing database operations."""
    pass
