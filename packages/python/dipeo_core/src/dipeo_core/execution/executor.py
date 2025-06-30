"""Base executor interfaces for DiPeO."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional, Protocol

from .types import ExecutionContext, ExecutionOptions, RuntimeContext


class BaseExecutor(ABC):
    """Abstract base class for diagram executors."""

    @abstractmethod
    async def execute(
        self,
        diagram: Dict[str, Any],
        options: Optional[ExecutionOptions] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute a diagram and yield execution events.

        Args:
            diagram: The diagram to execute
            options: Optional execution options

        Yields:
            Execution events (e.g., node started, node completed, errors)
        """
        pass

    @abstractmethod
    async def validate_diagram(self, diagram: Dict[str, Any]) -> None:
        """Validate a diagram before execution.

        Args:
            diagram: The diagram to validate

        Raises:
            ValidationError: If the diagram is invalid
        """
        pass


class ExecutorInterface(Protocol):
    """Protocol for executor implementations."""

    async def execute_node(
        self,
        node: Dict[str, Any],
        context: RuntimeContext,
        inputs: Dict[str, Any],
    ) -> Any:
        """Execute a single node."""
        ...

    async def validate_node(
        self,
        node: Dict[str, Any],
        available_inputs: set[str],
    ) -> None:
        """Validate a single node."""
        ...
