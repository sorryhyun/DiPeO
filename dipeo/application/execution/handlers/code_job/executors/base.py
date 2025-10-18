"""Base executor protocol for language-specific code execution."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, TypedDict


class ExecutionResult(TypedDict, total=False):
    value: Any
    output: str
    error: str | None
    exit_code: int | None


class CodeExecutor(Protocol):
    async def execute_file(
        self, file_path: Path, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any: ...

    async def execute_inline(
        self, code: str, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any: ...


class BaseCodeExecutor(ABC):
    def prepare_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
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
