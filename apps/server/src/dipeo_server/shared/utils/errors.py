"""Error handling utilities."""

import asyncio
import logging
import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..exceptions import (
    AgentDiagramException,
    APIKeyError,
    ConditionEvaluationError,
    ConfigurationError,
    DatabaseError,
    DependencyError,
    DiagramExecutionError,
    FileOperationError,
    LLMServiceError,
    MaxIterationsError,
    NodeExecutionError,
    PersonJobExecutionError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Response Formatting Utilities


class ResponseFormatter:
    """Standardize API responses."""

    @staticmethod
    def success(data: Any = None, message: str | None = None) -> dict[str, Any]:
        """Format successful response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response

    @staticmethod
    def error(
        message: str, details: dict[str, Any] | None = None, status_code: int = 400
    ) -> JSONResponse:
        """Format error response."""
        content = {"success": False, "error": message}
        if details:
            content["details"] = details

        return JSONResponse(status_code=status_code, content=content)

    @staticmethod
    def paginated(
        items: list, total: int, page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        """Format paginated response."""
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            },
        }


def handle_service_exceptions(func):
    """Decorator to handle common service exceptions."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AgentDiagramException:
            raise
        except Exception as e:
            raise AgentDiagramException(f"Unexpected error in {func.__name__}: {e!s}")

    return wrapper


# Error Handling Utilities


class ErrorHandler:
    """Centralized error handling with consistent responses."""

    # Map exception types to HTTP status codes
    error_mappings: dict[type[Exception], int] = {
        ValidationError: 400,
        ConfigurationError: 400,
        APIKeyError: 401,
        FileOperationError: 403,
        DatabaseError: 500,
        LLMServiceError: 503,
        DiagramExecutionError: 500,
        NodeExecutionError: 500,
        DependencyError: 400,
        MaxIterationsError: 400,
        ConditionEvaluationError: 500,
        PersonJobExecutionError: 500,
        HTTPException: None,  # Use the status code from HTTPException
    }

    @classmethod
    def get_status_code(cls, exception: Exception) -> int:
        """Get the appropriate HTTP status code for an exception."""
        if isinstance(exception, HTTPException):
            return exception.status_code

        for exc_type, status_code in cls.error_mappings.items():
            if isinstance(exception, exc_type):
                return status_code

        return 500  # Default to internal server error

    @classmethod
    def format_error_response(
        cls, exception: Exception, include_trace: bool = False
    ) -> dict[str, Any]:
        """Format exception into a consistent error response."""
        error_type = type(exception).__name__
        error_message = str(exception)

        response = {
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "success": False,
        }

        if include_trace and not isinstance(exception, HTTPException):
            response["error"]["trace"] = traceback.format_exc()

        return response

    @classmethod
    def handle_errors(cls, default_status: int = 500, include_trace: bool = False):
        """
        Decorator for handling errors in route handlers.

        Args:
            default_status: Default status code if exception type is not mapped
            include_trace: Whether to include stack trace in response
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    status_code = cls.get_status_code(e) or default_status
                    content = cls.format_error_response(e, include_trace)

                    return JSONResponse(status_code=status_code, content=content)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    status_code = cls.get_status_code(e) or default_status
                    content = cls.format_error_response(e, include_trace)

                    return JSONResponse(status_code=status_code, content=content)

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


def handle_api_errors(func: Callable) -> Callable:
    """Convenience decorator for API endpoints with standard error handling."""
    return ErrorHandler.handle_errors(include_trace=False)(func)


def handle_internal_errors(func: Callable) -> Callable:
    """Convenience decorator for internal functions with trace enabled."""
    return ErrorHandler.handle_errors(include_trace=True)(func)


# Service normalization utilities


def normalize_service_name(service: str) -> str:
    """Normalize service name to provider name using centralized mapping.

    Args:
        service: The service name to normalize

    Returns:
        The normalized service name
    """
    from ..constants import DEFAULT_SERVICE, SERVICE_ALIASES

    normalized = (service or DEFAULT_SERVICE).lower()
    return SERVICE_ALIASES.get(normalized, normalized)
