"""Envelope and result body construction utilities."""

from typing import Any


def create_error_body(error_msg: str, error_type: str = "ValueError") -> dict[str, str]:
    """Create consistent error body structure for envelope.

    Args:
        error_msg: Error message
        error_type: Type of error (default: "ValueError")

    Returns:
        Dictionary with error and type fields

    Example:
        >>> create_error_body("Invalid input", "ValidationError")
        {'error': 'Invalid input', 'type': 'ValidationError'}
    """
    return {"error": error_msg, "type": error_type}


def create_batch_result_body(
    results: dict[str, Any], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create batch operation result body.

    Args:
        results: Dictionary of results keyed by identifier
        metadata: Optional metadata about the batch operation

    Returns:
        Dictionary with results and metadata

    Example:
        >>> create_batch_result_body({"item1": "result1"}, {"count": 1})
        {'results': {'item1': 'result1'}, 'metadata': {'count': 1}}
    """
    body = {"results": results}
    if metadata:
        body["metadata"] = metadata
    return body


def create_text_result_body(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create text result body with optional metadata.

    Args:
        text: Text content
        metadata: Optional metadata

    Returns:
        Dictionary with text and metadata

    Example:
        >>> create_text_result_body("Hello", {"length": 5})
        {'text': 'Hello', 'metadata': {'length': 5}}
    """
    body: dict[str, Any] = {"text": text}
    if metadata:
        body["metadata"] = metadata
    return body


def create_operation_result_body(
    operation: str, status: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create operation result body.

    Args:
        operation: Operation name (e.g., "read", "write", "update")
        status: Status of operation (e.g., "success", "error", "partial")
        details: Optional operation details

    Returns:
        Dictionary with operation, status, and details

    Example:
        >>> create_operation_result_body("write", "success", {"bytes": 100})
        {'operation': 'write', 'status': 'success', 'details': {'bytes': 100}}
    """
    body: dict[str, Any] = {
        "operation": operation,
        "status": status,
    }
    if details:
        body["details"] = details
    return body
