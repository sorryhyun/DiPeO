"""Envelope and result body construction utilities."""

from typing import Any


def create_error_body(error_msg: str, error_type: str = "ValueError") -> dict[str, str]:
    """Create error body with message and type."""
    return {"error": error_msg, "type": error_type}


def create_batch_result_body(
    results: dict[str, Any], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create batch result body with results and optional metadata."""
    body = {"results": results}
    if metadata:
        body["metadata"] = metadata
    return body


def create_text_result_body(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create text result body with optional metadata."""
    body: dict[str, Any] = {"text": text}
    if metadata:
        body["metadata"] = metadata
    return body


def create_operation_result_body(
    operation: str, status: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create operation result body with status and optional details."""
    body: dict[str, Any] = {
        "operation": operation,
        "status": status,
    }
    if details:
        body["details"] = details
    return body
