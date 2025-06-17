"""Unified error handling system for AgentDiagram server."""

from functools import wraps
from typing import Callable, Type, Dict, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import traceback
import logging

from ..exceptions.exceptions import (
    ValidationError,
    APIKeyError,
    FileOperationError,
    DiagramExecutionError,
    LLMServiceError,
    NodeExecutionError,
    DependencyError,
    MaxIterationsError,
    ConditionEvaluationError,
    PersonJobExecutionError,
    DatabaseError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling with consistent responses."""
    
    # Map exception types to HTTP status codes
    error_mappings: Dict[Type[Exception], int] = {
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
    def format_error_response(cls, exception: Exception, include_trace: bool = False) -> Dict[str, Any]:
        """Format exception into a consistent error response."""
        error_type = type(exception).__name__
        error_message = str(exception)
        
        response = {
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "success": False
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
                    
                    return JSONResponse(
                        status_code=status_code,
                        content=content
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    status_code = cls.get_status_code(e) or default_status
                    content = cls.format_error_response(e, include_trace)
                    
                    return JSONResponse(
                        status_code=status_code,
                        content=content
                    )
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


def handle_api_errors(func: Callable) -> Callable:
    """Convenience decorator for API endpoints with standard error handling."""
    return ErrorHandler.handle_errors(include_trace=False)(func)


def handle_internal_errors(func: Callable) -> Callable:
    """Convenience decorator for internal functions with trace enabled."""
    return ErrorHandler.handle_errors(include_trace=True)(func)