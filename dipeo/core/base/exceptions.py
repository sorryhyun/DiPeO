"""Base exception classes for DiPeO core."""

from typing import Any


class DiPeOError(Exception):
    """Base exception class for all DiPeO errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = self.__class__.__name__

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ValidationError(DiPeOError):
    error_code = "VALIDATION_ERROR"


class ConfigurationError(DiPeOError):
    error_code = "CONFIGURATION_ERROR"


class ServiceError(DiPeOError):
    error_code = "SERVICE_ERROR"


class ExecutionError(DiPeOError):
    error_code = "EXECUTION_ERROR"


class NodeExecutionError(ExecutionError):
    """Raised when a specific node fails to execute."""

    error_code = "NODE_EXECUTION_ERROR"

    def __init__(
        self,
        node_id: str,
        node_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.node_id = node_id
        self.node_type = node_type
        super().__init__(f"Node {node_id} ({node_type}) failed: {message}", details)


class DependencyError(ExecutionError):
    """Raised when node dependencies aren't met."""

    error_code = "DEPENDENCY_ERROR"

    def __init__(
        self,
        node_id: str,
        missing_dependencies: list[str],
        details: dict[str, Any] | None = None,
    ):
        self.node_id = node_id
        self.missing_dependencies = missing_dependencies
        super().__init__(
            f"Node {node_id} dependencies not met: {', '.join(missing_dependencies)}",
            details,
        )


class MaxIterationsError(ExecutionError):
    """Raised when max iterations are exceeded."""

    error_code = "MAX_ITERATIONS_ERROR"

    def __init__(
        self,
        node_id: str,
        max_iterations: int,
        details: dict[str, Any] | None = None,
    ):
        self.node_id = node_id
        self.max_iterations = max_iterations
        super().__init__(
            f"Node {node_id} exceeded maximum iterations ({max_iterations})", details
        )


class TimeoutError(ExecutionError):
    """Raised when execution times out."""

    error_code = "TIMEOUT_ERROR"

    def __init__(
        self,
        message: str = "Execution timed out",
        timeout: float | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.timeout = timeout
        if timeout:
            message = f"{message} after {timeout} seconds"
        super().__init__(message, details)


class APIKeyError(ServiceError):
    """Raised when API key operations fail."""

    error_code = "API_KEY_ERROR"


class APIKeyNotFoundError(APIKeyError):
    """Raised when an API key is not found."""

    error_code = "API_KEY_NOT_FOUND"

    def __init__(self, key_id: str, details: dict[str, Any] | None = None):
        self.key_id = key_id
        super().__init__(f"API key not found: {key_id}", details)


class LLMServiceError(ServiceError):
    """Raised when LLM service calls fail."""

    error_code = "LLM_SERVICE_ERROR"

    def __init__(
        self,
        service: str,
        message: str,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.service = service
        self.model = model
        full_message = f"LLM service {service}"
        if model:
            full_message += f" (model: {model})"
        full_message += f" failed: {message}"
        super().__init__(full_message, details)


class FileOperationError(DiPeOError):
    """Raised when file operations fail."""

    error_code = "FILE_OPERATION_ERROR"

    def __init__(
        self,
        operation: str,
        path: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.operation = operation
        self.path = path
        super().__init__(f"File {operation} failed for {path}: {message}", details)


class StorageError(ServiceError):
    """Raised when storage operations fail."""

    error_code = "STORAGE_ERROR"

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.operation = operation
        full_message = f"Storage operation"
        if operation:
            full_message += f" ({operation})"
        full_message += f" failed: {message}"
        super().__init__(full_message, details)


class DiagramError(ValidationError):
    """Base class for diagram-related errors."""

    error_code = "DIAGRAM_ERROR"


class DiagramNotFoundError(DiagramError):
    """Raised when a diagram is not found."""

    error_code = "DIAGRAM_NOT_FOUND"

    def __init__(self, diagram_id: str, details: dict[str, Any] | None = None):
        self.diagram_id = diagram_id
        super().__init__(f"Diagram not found: {diagram_id}", details)


class InvalidDiagramError(DiagramError):
    """Raised when a diagram is invalid."""

    error_code = "INVALID_DIAGRAM"

    def __init__(
        self,
        reason: str,
        diagram_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.reason = reason
        self.diagram_id = diagram_id
        message = "Invalid diagram"
        if diagram_id:
            message += f" ({diagram_id})"
        message += f": {reason}"
        super().__init__(message, details)


# Error code to exception class mapping
ERROR_CODE_MAP = {
    "VALIDATION_ERROR": ValidationError,
    "CONFIGURATION_ERROR": ConfigurationError,
    "SERVICE_ERROR": ServiceError,
    "EXECUTION_ERROR": ExecutionError,
    "NODE_EXECUTION_ERROR": NodeExecutionError,
    "DEPENDENCY_ERROR": DependencyError,
    "MAX_ITERATIONS_ERROR": MaxIterationsError,
    "TIMEOUT_ERROR": TimeoutError,
    "API_KEY_ERROR": APIKeyError,
    "API_KEY_NOT_FOUND": APIKeyNotFoundError,
    "LLM_SERVICE_ERROR": LLMServiceError,
    "FILE_OPERATION_ERROR": FileOperationError,
    "STORAGE_ERROR": StorageError,
    "DIAGRAM_ERROR": DiagramError,
    "DIAGRAM_NOT_FOUND": DiagramNotFoundError,
    "INVALID_DIAGRAM": InvalidDiagramError,
}


def get_exception_by_code(error_code: str) -> type[DiPeOError]:
    """Get exception class by error code.

    Args:
        error_code: The error code to look up

    Returns:
        Exception class, defaults to DiPeOError if not found
    """
    return ERROR_CODE_MAP.get(error_code, DiPeOError)
