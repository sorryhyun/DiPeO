"""Shared type definitions used across the DiPeO system."""

from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, RootModel

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


# Option 1: Non-recursive union types with limited depth
# This avoids Pydantic recursion issues while providing better typing than Any
SimpleJsonValue = Union[str, int, float, bool, None]

# Level 2: Dict/List containing simple values
JsonDict = Dict[str, Union[SimpleJsonValue, List[SimpleJsonValue], Dict[str, SimpleJsonValue]]]
JsonList = List[Union[SimpleJsonValue, Dict[str, SimpleJsonValue]]]

# Top level: Can be any of the above
JsonValue = Union[SimpleJsonValue, JsonDict, JsonList]

# Alias for compatibility
JsonPrimitive = SimpleJsonValue

# For backward compatibility, keep using Any for now in generated code
# This will be migrated gradually
JsonAny = Any

__all__ = [
    "Error",
    "JsonAny",
    "JsonDict",
    "JsonList",
    "JsonPrimitive",
    "JsonValue",
    "Result",
    "SimpleJsonValue",
]