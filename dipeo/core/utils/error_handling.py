"""
Centralized error handling utilities and decorators for DiPeO backend.
"""

import asyncio
import functools
import json
import logging
import time
from collections.abc import Callable
from typing import (
    Any,
    Literal,
    ParamSpec,
    TypeVar,
)

import yaml

P = ParamSpec('P')
T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response structure."""
    
    def __init__(self, success: bool = False, error: str | None = None, **kwargs: Any):
        self.success = success
        self.error = error
        self.data = kwargs
    
    def to_dict(self) -> dict[str, Any]:
        result = {"success": self.success}
        if self.error:
            result["error"] = self.error
        result.update(self.data)
        return result


def handle_exceptions(
    error_message: str = "Operation failed",
    include_details: bool = True,
    logger_instance: logging.Logger | None = None,
    **default_response_data: Any
) -> Callable[[Callable[P, T]], Callable[P, T | dict[str, Any]]]:
    # Decorator for exception handling with standardized responses
    def decorator(func: Callable[P, T]) -> Callable[P, T | dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_instance or logger
                error_detail = f"{error_message}: {e!s}" if include_details else error_message
                log.error(error_detail, exc_info=True)
                
                response = ErrorResponse(success=False, error=error_detail, **default_response_data)
                return response.to_dict()
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T | dict[str, Any]:
            try:
                return await func(*args, **kwargs)  # type: ignore
            except Exception as e:
                log = logger_instance or logger
                error_detail = f"{error_message}: {e!s}" if include_details else error_message
                log.error(error_detail, exc_info=True)
                
                response = ErrorResponse(success=False, error=error_detail, **default_response_data)
                return response.to_dict()
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def handle_file_operation(operation: str, file_path: str | None = None) -> Callable[[Callable[P, T]], Callable[P, T | dict[str, Any]]]:
    # Decorator for file operations with consistent error handling
    def decorator(func: Callable[P, T]) -> Callable[P, T | dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | dict[str, Any]:
            # Try to extract file path from args if not provided
            path = file_path
            if not path and args:
                # Assume first arg might be file path
                if isinstance(args[0], str):
                    path = args[0]
                elif hasattr(args[0], 'file_path'):
                    path = args[0].file_path
            
            try:
                return func(*args, **kwargs)
            except FileNotFoundError:
                error = f"File not found: {path}" if path else "File not found"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except PermissionError:
                error = f"Permission denied: {path}" if path else "Permission denied"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except IsADirectoryError:
                error = f"Is a directory: {path}" if path else "Target is a directory"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except Exception as e:
                error = f"Failed to {operation} file: {e!s}"
                logger.error(error, exc_info=True)
                return {"success": False, "error": error, "operation": operation}
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T | dict[str, Any]:
            # Try to extract file path from args if not provided
            path = file_path
            if not path and args:
                # Assume first arg might be file path
                if isinstance(args[0], str):
                    path = args[0]
                elif hasattr(args[0], 'file_path'):
                    path = args[0].file_path
            
            try:
                return await func(*args, **kwargs)  # type: ignore
            except FileNotFoundError:
                error = f"File not found: {path}" if path else "File not found"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except PermissionError:
                error = f"Permission denied: {path}" if path else "Permission denied"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except IsADirectoryError:
                error = f"Is a directory: {path}" if path else "Target is a directory"
                logger.error(error)
                return {"success": False, "error": error, "operation": operation}
            except Exception as e:
                error = f"Failed to {operation} file: {e!s}"
                logger.error(error, exc_info=True)
                return {"success": False, "error": error, "operation": operation}
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def handle_api_errors(
    operation: str,
    value_error_prefix: str = "Validation error",
    general_error_prefix: str = "Failed to",
    result_class: type | None = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    # Decorator for API error handling with consistent logging
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                logger.error(f"{value_error_prefix}: {e}")
                if result_class:
                    return result_class(success=False, error=f"{value_error_prefix}: {e!s}")  # type: ignore
                raise
            except Exception as e:
                logger.error(f"{general_error_prefix} {operation}: {e}")
                if result_class:
                    return result_class(success=False, error=f"{general_error_prefix} {operation}: {e!s}")  # type: ignore
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)  # type: ignore
            except ValueError as e:
                logger.error(f"{value_error_prefix}: {e}")
                if result_class:
                    return result_class(success=False, error=f"{value_error_prefix}: {e!s}")  # type: ignore
                raise
            except Exception as e:
                logger.error(f"{general_error_prefix} {operation}: {e}")
                if result_class:
                    return result_class(success=False, error=f"{general_error_prefix} {operation}: {e!s}")  # type: ignore
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    logger_instance: logging.Logger | None = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    # Decorator for retrying operations with exponential backoff
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            log = logger_instance or logger
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = initial_delay * (backoff_factor ** attempt)
                        log.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.1f}s: {e}"
                        )
                        time.sleep(delay)
                        continue
                    raise
            
            # This should never be reached, but satisfies type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            log = logger_instance or logger
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)  # type: ignore
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = initial_delay * (backoff_factor ** attempt)
                        log.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise
            
            # This should never be reached, but satisfies type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def safe_parse(content: str, format: Literal['json', 'yaml'] = 'json') -> Any | str:
    # Safely parse JSON/YAML, returning original content on failure
    try:
        if format == 'json':
            return json.loads(content)
        elif format == 'yaml':
            return yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.debug(f"Failed to parse {format}: {e}")
        return content
    except Exception as e:
        logger.warning(f"Unexpected error parsing {format}: {e}")
        return content


# Import existing exceptions from base exceptions


def format_error_response(
    operation: str,
    error: Exception,
    include_type: bool = True,
    **extra_data: Any
) -> dict[str, Any]:
    # Format error into standardized response dictionary
    response = {
        "success": False,
        "operation": operation,
        "error": str(error),
    }
    
    if include_type:
        response["error_type"] = type(error).__name__
    
    response.update(extra_data)
    return response