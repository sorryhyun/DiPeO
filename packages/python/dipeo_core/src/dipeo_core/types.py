"""Shared type definitions used across the DiPeO system."""

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):
    """A result type that can contain either a success value or an error."""
    
    value: Optional[T] = None
    error: Optional[E] = None
    
    @property
    def is_ok(self) -> bool:
        """Check if the result is successful."""
        return self.error is None
    
    @property
    def is_error(self) -> bool:
        """Check if the result contains an error."""
        return self.error is not None
    
    def unwrap(self) -> T:
        """Get the value, raising an exception if there's an error."""
        if self.is_error:
            raise ValueError(f"Result contains error: {self.error}")
        return self.value  # type: ignore
    
    def unwrap_or(self, default: T) -> T:
        """Get the value or return a default if there's an error."""
        return self.value if self.is_ok else default
    
    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Create a successful result."""
        return cls(value=value, error=None)
    
    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """Create an error result."""
        return cls(value=None, error=error)


@dataclass
class Error:
    """A standard error type with code and message."""
    
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.code}] {self.message}"


# Type aliases for common patterns
JsonDict = dict[str, Any]
JsonList = list[Any]
JsonValue = Any

__all__ = [
    "Result",
    "Error",
    "JsonDict",
    "JsonList",
    "JsonValue",
]