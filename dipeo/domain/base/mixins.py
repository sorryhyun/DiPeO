"""Optional mixins for services to replace monolithic BaseService.

These mixins provide common functionality that services can opt into,
following composition over inheritance principle.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any

from .exceptions import ValidationError


class LoggingMixin:
    """Mixin to add logging capabilities to a service."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this service."""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(
                self.__class__.__module__ + "." + self.__class__.__name__
            )
        return self._logger

    def log_debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(message, extra=kwargs)

    def log_info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(message, extra=kwargs)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(message, extra=kwargs)

    def log_error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def log_operation(self, operation: str):
        """Decorator to log operation execution."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                self.log_debug(f"Starting {operation}")
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    self.log_debug(f"Completed {operation} in {elapsed:.2f}s")
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    self.log_error(f"Failed {operation} after {elapsed:.2f}s: {e}")
                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                self.log_debug(f"Starting {operation}")
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    self.log_debug(f"Completed {operation} in {elapsed:.2f}s")
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    self.log_error(f"Failed {operation} after {elapsed:.2f}s: {e}")
                    raise

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator


class ValidationMixin:
    """Mixin to add validation utilities to a service."""

    def validate_required_fields(self, data: dict[str, Any], required_fields: list[str]) -> None:
        """Validate that all required fields are present in data."""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def validate_file_path(self, file_path: str, allowed_base: Path | None = None) -> Path:
        """Validate and resolve a file path, ensuring it's within allowed base."""
        rel_path = Path(file_path)

        if allowed_base is None:
            return rel_path.resolve()

        full_path = (allowed_base / rel_path).resolve()
        try:
            full_path.relative_to(allowed_base)
        except ValueError as e:
            raise ValidationError(f"Access to {full_path} is forbidden") from e

        return full_path

    def validate_type(self, value: Any, expected_type: type, field_name: str) -> None:
        """Validate that a value is of the expected type."""
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    def validate_enum(self, value: Any, allowed_values: list[Any], field_name: str) -> None:
        """Validate that a value is in the allowed set."""
        if value not in allowed_values:
            raise ValidationError(
                f"Field '{field_name}' must be one of {allowed_values}, got {value}"
            )


class ConfigurationMixin:
    """Mixin to add configuration management to a service."""

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}

    @property
    def config(self) -> dict[str, Any]:
        """Get the configuration dictionary."""
        return self._config

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with dot notation support."""
        return self.safe_get_nested(self._config, key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        self._config[key] = value

    def safe_get_nested(self, obj: Any, path: str, default: Any = None) -> Any:
        """Safely get a nested value from an object using dot notation."""
        if obj is None:
            return default

        current = obj
        parts = path.split(".")

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = getattr(current, part, None)

                if current is None:
                    return default

            return current
        except (KeyError, AttributeError, TypeError):
            return default


@dataclass
class CacheEntry:
    """Entry in the cache with timestamp."""

    value: Any
    timestamp: float
    hits: int = 0


class CachingMixin:
    """Mixin to add simple in-memory caching to a service."""

    def __init__(self, cache_ttl: float = 300.0):
        self._cache: dict[str, CacheEntry] = {}
        self._cache_ttl = cache_ttl

    def cache_get(self, key: str) -> Any | None:
        """Get a value from cache if it exists and hasn't expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        age = time.time() - entry.timestamp

        if age > self._cache_ttl:
            del self._cache[key]
            return None

        entry.hits += 1
        return entry.value

    def cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = CacheEntry(value=value, timestamp=time.time())

    def cache_invalidate(self, key: str | None = None) -> None:
        """Invalidate cache entries. If key is None, clears all."""
        if key is None:
            self._cache.clear()
        elif key in self._cache:
            del self._cache[key]

    def cache_stats(self) -> dict[str, Any]:
        return {
            "size": len(self._cache),
            "total_hits": sum(e.hits for e in self._cache.values()),
            "keys": list(self._cache.keys()),
        }

    def with_cache(self, key_func=None):
        """Decorator to cache function results."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

                cached = self.cache_get(cache_key)
                if cached is not None:
                    return cached

                result = await func(*args, **kwargs)
                self.cache_set(cache_key, result)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

                cached = self.cache_get(cache_key)
                if cached is not None:
                    return cached

                result = func(*args, **kwargs)
                self.cache_set(cache_key, result)
                return result

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator


class InitializationMixin:
    """Mixin to add initialization tracking to a service."""

    def __init__(self):
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def ensure_initialized(self) -> None:
        if self._initialized:
            return

        async with self._initialization_lock:
            if self._initialized:
                return

            if hasattr(self, "initialize"):
                await self.initialize()

            self._initialized = True

    def require_initialized(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                await self.ensure_initialized()
                return await func(*args, **kwargs)

            return wrapper

        return decorator
