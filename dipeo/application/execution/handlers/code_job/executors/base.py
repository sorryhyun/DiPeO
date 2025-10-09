"""Base executor protocol for language-specific code execution."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, TypedDict


class ExecutionResult(TypedDict, total=False):
    """Result of code execution."""

    value: Any
    output: str
    error: str | None
    exit_code: int | None


class CodeExecutor(Protocol):
    """Protocol for language-specific code executors."""

    async def execute_file(
        self, file_path: Path, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        """Execute code from a file with timeout and input handling."""
        ...

    async def execute_inline(
        self, code: str, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        """Execute inline code string with timeout and input handling."""
        ...


class BaseCodeExecutor(ABC):
    """Base class for code executors with common functionality."""

    def prepare_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        import json

        prepared = {}
        if not isinstance(inputs, dict):
            return prepared

        if inputs:
            for key, value in inputs.items():
                if isinstance(value, str) and value.strip() and value.strip()[0] in "{[":
                    try:
                        prepared[key] = json.loads(value)
                    except json.JSONDecodeError:
                        prepared[key] = value
                else:
                    prepared[key] = value
        return prepared

    @abstractmethod
    async def execute_file(
        self, file_path: Path, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        pass

    @abstractmethod
    async def execute_inline(
        self, code: str, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        pass
