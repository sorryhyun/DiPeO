"""Shared type definitions used across the DiPeO system."""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result[T, E]:
    """Type-safe Result type for handling success/error cases.

    This implementation uses type guards to ensure type safety without type: ignore.
    """

    value: T | None = None
    error: E | None = None

    @property
    def is_ok(self) -> bool:
        """Check if result is a success."""
        return self.error is None

    @property
    def is_error(self) -> bool:
        """Check if result is an error."""
        return self.error is not None

    def unwrap(self) -> T:
        """Get the value, raising if it's an error.

        Returns:
            The success value

        Raises:
            ValueError: If result contains an error
        """
        if self.is_error:
            raise ValueError(f"Result contains error: {self.error}")
        if self.value is None:
            raise ValueError("Result has no value (internal error)")
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get the value or return a default if it's an error.

        Args:
            default: Value to return if result is an error

        Returns:
            The success value or default
        """
        if self.is_ok and self.value is not None:
            return self.value
        return default

    def unwrap_or_else(self, func: Any) -> T:
        """Get the value or compute a default using a function.

        Args:
            func: Function to compute default value, receives error as argument

        Returns:
            The success value or computed default
        """
        if self.is_ok and self.value is not None:
            return self.value
        return func(self.error)  # type: ignore[no-any-return]

    def map(self, func: Any) -> "Result[Any, E]":
        """Map the success value through a function.

        Args:
            func: Function to apply to success value

        Returns:
            New Result with mapped value or same error
        """
        if self.is_ok and self.value is not None:
            return Result.ok(func(self.value))
        if self.error is not None:
            return Result.err(self.error)
        # Should never happen, but needed for type checker
        raise ValueError("Result has neither value nor error")

    def map_err(self, func: Any) -> "Result[T, Any]":
        """Map the error value through a function.

        Args:
            func: Function to apply to error value

        Returns:
            New Result with same value or mapped error
        """
        if self.is_error and self.error is not None:
            return Result.err(func(self.error))
        if self.value is not None:
            return Result.ok(self.value)
        # Should never happen, but needed for type checker
        raise ValueError("Result has neither value nor error")

    def and_then(self, func: Any) -> "Result[Any, E]":
        """Chain another Result-producing operation.

        Args:
            func: Function that takes success value and returns a Result

        Returns:
            Result from func or propagated error
        """
        if self.is_ok and self.value is not None:
            return func(self.value)  # type: ignore[no-any-return]
        if self.error is not None:
            return Result.err(self.error)
        # Should never happen, but needed for type checker
        raise ValueError("Result has neither value nor error")

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Create a success Result.

        Args:
            value: The success value

        Returns:
            Result containing the value
        """
        return cls(value=value, error=None)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """Create an error Result.

        Args:
            error: The error value

        Returns:
            Result containing the error
        """
        return cls(value=None, error=error)


@dataclass
class Error:
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# JSON type definitions - using limited depth to avoid Pydantic recursion issues
# NOTE: Pydantic doesn't handle recursive types well, so we use a practical approach

# JSON primitive types
JsonPrimitive = str | int | float | bool | None
SimpleJsonValue = JsonPrimitive  # Alias for compatibility

# For complex nested structures, we use Any to avoid recursion issues
# This is a pragmatic solution until Pydantic better supports recursive types
JsonDict = dict[str, Any]  # Allows any nested structure
JsonList = list[Any]  # Allows any nested list

# Main JSON value type - covers most practical cases
JsonValue = JsonPrimitive | JsonDict | JsonList

# Type aliases for clarity
JsonObject = JsonDict  # Alias for JSON objects
JsonArray = JsonList  # Alias for JSON arrays

# For backward compatibility
JsonAny = Any  # Will gradually migrate to more specific types

__all__ = [
    "Error",
    "JsonAny",
    "JsonArray",
    "JsonDict",
    "JsonList",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
    "Result",
    "SimpleJsonValue",
]
