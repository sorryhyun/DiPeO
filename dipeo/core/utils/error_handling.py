"""
Centralized error handling utilities and decorators for DiPeO backend.
"""

import asyncio
import functools
import json
import logging
import time
import yaml
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast, overload
from typing import ParamSpec, Literal

P = ParamSpec('P')
T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response structure."""
    
    def __init__(self, success: bool = False, error: Optional[str] = None, **kwargs: Any):
        self.success = success
        self.error = error
        self.data = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"success": self.success}
        if self.error:
            result["error"] = self.error
        result.update(self.data)
        return result


def handle_exceptions(
    error_message: str = "Operation failed",
    include_details: bool = True,
    logger_instance: Optional[logging.Logger] = None,
    **default_response_data: Any
) -> Callable[[Callable[P, T]], Callable[P, Union[T, Dict[str, Any]]]]:
    """
    Decorator for handling exceptions with standardized error responses.
    
    Args:
        error_message: Base error message
        include_details: Whether to include exception details
        logger_instance: Logger to use (defaults to module logger)
        **default_response_data: Additional data to include in error response
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Dict[str, Any]]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Dict[str, Any]]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_instance or logger
                error_detail = f"{error_message}: {str(e)}" if include_details else error_message
                log.error(error_detail, exc_info=True)
                
                response = ErrorResponse(success=False, error=error_detail, **default_response_data)
                return response.to_dict()
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Dict[str, Any]]:
            try:
                return await func(*args, **kwargs)  # type: ignore
            except Exception as e:
                log = logger_instance or logger
                error_detail = f"{error_message}: {str(e)}" if include_details else error_message
                log.error(error_detail, exc_info=True)
                
                response = ErrorResponse(success=False, error=error_detail, **default_response_data)
                return response.to_dict()
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def handle_file_operation(operation: str, file_path: Optional[str] = None) -> Callable[[Callable[P, T]], Callable[P, Union[T, Dict[str, Any]]]]:
    """
    Decorator specifically for file operations with consistent error handling.
    
    Args:
        operation: Name of the operation (e.g., "read", "write", "delete")
        file_path: Optional file path for error messages
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Dict[str, Any]]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Dict[str, Any]]:
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
                error = f"Failed to {operation} file: {str(e)}"
                logger.error(error, exc_info=True)
                return {"success": False, "error": error, "operation": operation}
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Dict[str, Any]]:
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
                error = f"Failed to {operation} file: {str(e)}"
                logger.error(error, exc_info=True)
                return {"success": False, "error": error, "operation": operation}
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore
    
    return decorator


def handle_api_errors(
    operation: str,
    value_error_prefix: str = "Validation error",
    general_error_prefix: str = "Failed to",
    result_class: Optional[Type] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for handling API errors with consistent logging and response format.
    
    Args:
        operation: Name of the operation for error messages
        value_error_prefix: Prefix for ValueError messages
        general_error_prefix: Prefix for general exceptions
        result_class: Optional result class with success/error attributes
    """
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
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger_instance: Optional[logging.Logger] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by after each attempt
        exceptions: Tuple of exception types to catch and retry
        logger_instance: Logger to use for warnings
    """
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


def safe_parse(content: str, format: Literal['json', 'yaml'] = 'json') -> Union[Any, str]:
    """
    Safely parse JSON or YAML content, returning original content if parsing fails.
    
    Args:
        content: Content to parse
        format: Format to parse ('json' or 'yaml')
    
    Returns:
        Parsed content or original string if parsing fails
    """
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


# Import existing exceptions from error taxonomy
from ..errors.taxonomy import FileOperationError, APIKeyError


def format_error_response(
    operation: str,
    error: Exception,
    include_type: bool = True,
    **extra_data: Any
) -> Dict[str, Any]:
    """
    Format an error into a standardized response dictionary.
    
    Args:
        operation: Operation that failed
        error: The exception that was raised
        include_type: Whether to include the exception type
        **extra_data: Additional data to include in response
    
    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "operation": operation,
        "error": str(error),
    }
    
    if include_type:
        response["error_type"] = type(error).__name__
    
    response.update(extra_data)
    return response