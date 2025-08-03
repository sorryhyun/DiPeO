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
        self,
        file_path: Path,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute code from a file.
        
        Args:
            file_path: Path to the code file
            inputs: Input data to pass to the code
            timeout: Execution timeout in seconds
            function_name: Function to call (language-specific)
            
        Returns:
            Execution result
            
        Raises:
            TimeoutError: If execution exceeds timeout
            Exception: For other execution errors
        """
        ...
    
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute inline code.
        
        Args:
            code: Source code to execute
            inputs: Input data to pass to the code
            timeout: Execution timeout in seconds
            function_name: Function to call (if applicable)
            
        Returns:
            Execution result
            
        Raises:
            TimeoutError: If execution exceeds timeout
            Exception: For other execution errors
        """
        ...


class BaseCodeExecutor(ABC):
    """Base class for code executors with common functionality."""
    
    def prepare_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Prepare inputs for execution (e.g., parse JSON strings)."""
        import json
        
        prepared = {}
        if inputs:
            for key, value in inputs.items():
                # Try to parse JSON strings
                if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                    try:
                        prepared[key] = json.loads(value)
                    except json.JSONDecodeError:
                        prepared[key] = value
                else:
                    prepared[key] = value
        return prepared
    
    @abstractmethod
    async def execute_file(
        self,
        file_path: Path,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute code from a file."""
        pass
    
    @abstractmethod
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"
    ) -> Any:
        """Execute inline code."""
        pass