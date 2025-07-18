"""Server exception module.

This module re-exports exceptions from dipeo.core.errors for backward compatibility
and defines server-specific exceptions that extend the core taxonomy.
"""

from typing import Any

# Re-export base exceptions
# Re-export core exceptions for backward compatibility
from dipeo.core.base.exceptions import (  # noqa: F401  # noqa: F401
    APIKeyError,
    ConfigurationError,
    DependencyError,
    DiPeOError,
    ExecutionError,
    FileOperationError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    ServiceError,
    ValidationError,
)


# Server-specific exceptions that extend the core taxonomy
class ConditionEvaluationError(NodeExecutionError):
    """Error when evaluating a condition node."""

    def __init__(
        self,
        node_id: str,
        condition: str,
        message: str,
        details: dict[str, Any] | None = None,
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
        details: dict[str, Any] | None = None,
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
