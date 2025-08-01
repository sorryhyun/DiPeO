"""Shared type definitions used across the DiPeO system."""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):

    value: T | None = None
    error: E | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    def unwrap(self) -> T:
        if self.is_error:
            raise ValueError(f"Result contains error: {self.error}")
        return self.value  # type: ignore

    def unwrap_or(self, default: T) -> T:
        return self.value if self.is_ok else default

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        return cls(value=value, error=None)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        return cls(value=None, error=error)


@dataclass
class Error:

    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Type aliases for common patterns
JsonDict = dict[str, Any]
JsonList = list[Any]
JsonValue = Any

__all__ = [
    "Error",
    "JsonDict",
    "JsonList",
    "JsonValue",
    "Result",
]
