"""Unified utilities module for common functionality."""

import os
import traceback
import logging
from typing import Any, Dict, Optional, Type, Callable
from functools import wraps
from enum import Enum
import asyncio

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from .exceptions import (
    AgentDiagramException,
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


# ============================================================================
# Response Formatting Utilities
# ============================================================================

class ResponseFormatter:
    """Standardize API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = None) -> Dict[str, Any]:
        """Format successful response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error(message: str, details: Dict[str, Any] = None, status_code: int = 400) -> JSONResponse:
        """Format error response."""
        content = {
            "success": False,
            "error": message
        }
        if details:
            content["details"] = details
            
        return JSONResponse(
            status_code=status_code,
            content=content
        )
    
    @staticmethod
    def paginated(items: list, total: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Format paginated response."""
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }


def handle_service_exceptions(func):
    """Decorator to handle common service exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AgentDiagramException:
            raise
        except Exception as e:
            raise AgentDiagramException(f"Unexpected error in {func.__name__}: {str(e)}")
    
    return wrapper


# ============================================================================
# Error Handling Utilities
# ============================================================================

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


# ============================================================================
# Feature Flag Management
# ============================================================================

# FeatureFlag enum is imported from original location to avoid duplication
from src.common.utils import FeatureFlag


class FeatureFlagManager:
    """Manages feature flags for the application."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize feature flag manager."""
        self._flags = config or {}
        self._load_from_environment()
        self._set_defaults()
    
    def _load_from_environment(self):
        """Load feature flags from environment variables."""
        for flag in FeatureFlag:
            env_var = f"DIPEO_{flag.value.upper()}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                # Convert string to boolean
                self._flags[flag.value] = env_value.lower() in ('true', '1', 'yes', 'on')
    
    def _set_defaults(self):
        """Set default values for feature flags."""
        defaults = {
            # Core execution features
            FeatureFlag.ENABLE_STREAMING.value: True,
            FeatureFlag.ENABLE_COST_TRACKING.value: True,
            FeatureFlag.ENABLE_MEMORY_PERSISTENCE.value: True,
            
            # Performance features
            FeatureFlag.ENABLE_EXECUTOR_CACHING.value: True,
            FeatureFlag.ENABLE_PARALLEL_EXECUTION.value: False,  # Not implemented yet
            FeatureFlag.ENABLE_EXECUTION_MONITORING.value: True,
            
            # Safety features
            FeatureFlag.ENABLE_SANDBOX_MODE.value: True,
            FeatureFlag.ENABLE_EXECUTION_TIMEOUT.value: True,
            FeatureFlag.ENABLE_RATE_LIMITING.value: False,  # Disabled for development
            
            # Debug features (disabled by default)
            FeatureFlag.ENABLE_DEBUG_MODE.value: False,
            FeatureFlag.ENABLE_VERBOSE_LOGGING.value: False,
            FeatureFlag.ENABLE_EXECUTION_TRACING.value: False,
        }
        
        for flag, default_value in defaults.items():
            if flag not in self._flags:
                self._flags[flag] = default_value
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag.value, False)
    
    def enable(self, flag: FeatureFlag) -> None:
        """Enable a feature flag."""
        self._flags[flag.value] = True
    
    def disable(self, flag: FeatureFlag) -> None:
        """Disable a feature flag."""
        self._flags[flag.value] = False
    
    def set_flag(self, flag: FeatureFlag, value: bool) -> None:
        """Set a feature flag to a specific value."""
        self._flags[flag.value] = value
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their current values."""
        return self._flags.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset all flags to their default values."""
        self._flags.clear()
        self._set_defaults()


# Global feature flag manager instance
_feature_flags = FeatureFlagManager()


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """Global function to check if a feature is enabled."""
    return _feature_flags.is_enabled(flag)


def enable_feature(flag: FeatureFlag) -> None:
    """Global function to enable a feature."""
    _feature_flags.enable(flag)


def disable_feature(flag: FeatureFlag) -> None:
    """Global function to disable a feature."""
    _feature_flags.disable(flag)


def configure_features(config: Dict[str, bool]) -> None:
    """Configure multiple features at once."""
    for flag_name, value in config.items():
        try:
            flag = FeatureFlag(flag_name)
            _feature_flags.set_flag(flag, value)
        except ValueError:
            # Unknown flag, ignore
            pass


def get_feature_flags() -> Dict[str, bool]:
    """Get all current feature flags."""
    return _feature_flags.get_all_flags()


# Feature status reporting
def get_feature_status() -> Dict[str, Any]:
    """Get current feature status."""
    return {
        "streaming_enabled": is_feature_enabled(FeatureFlag.ENABLE_STREAMING),
        "cost_tracking_enabled": is_feature_enabled(FeatureFlag.ENABLE_COST_TRACKING),
        "memory_persistence_enabled": is_feature_enabled(FeatureFlag.ENABLE_MEMORY_PERSISTENCE),
        "executor_caching_enabled": is_feature_enabled(FeatureFlag.ENABLE_EXECUTOR_CACHING),
        "monitoring_enabled": is_feature_enabled(FeatureFlag.ENABLE_EXECUTION_MONITORING),
        "sandbox_mode_enabled": is_feature_enabled(FeatureFlag.ENABLE_SANDBOX_MODE),
    }