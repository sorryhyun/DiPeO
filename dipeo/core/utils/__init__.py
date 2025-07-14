"""Utility functions for DiPeO Core."""

# Export error handling utilities
# Export conversation detection utilities
from .conversation_detection import (
    contains_conversation,
    has_nested_conversation,
    is_conversation,
)

# Export dynamic registry utilities
from .dynamic_registry import DynamicRegistry, TypedDynamicRegistry
from .error_handling import (
    ErrorResponse,
    format_error_response,
    handle_api_errors,
    handle_exceptions,
    handle_file_operation,
    retry_with_backoff,
    safe_parse,
)

__all__ = [
    # Error handling utilities
    "ErrorResponse",
    "handle_exceptions",
    "handle_file_operation",
    "handle_api_errors",
    "retry_with_backoff",
    "safe_parse",
    "format_error_response",
    # Dynamic registry utilities
    "DynamicRegistry",
    "TypedDynamicRegistry",
    # Conversation detection utilities
    "is_conversation",
    "has_nested_conversation",
    "contains_conversation",
]