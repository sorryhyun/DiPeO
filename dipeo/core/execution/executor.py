"""Base executor interfaces for DiPeO."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional, Protocol

from .types import ExecutionContext, ExecutionOptions
from ..unified_context import UnifiedExecutionContext


class BaseExecutor(ABC):

    @abstractmethod
    async def execute(
        self,
        diagram: Dict[str, Any],
        options: Optional[ExecutionOptions] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        pass

    @abstractmethod
    async def validate_diagram(self, diagram: Dict[str, Any]) -> None:
        pass


class ExecutorInterface(Protocol):

    async def execute_node(
        self,
        node: Dict[str, Any],
        context: UnifiedExecutionContext,
        inputs: Dict[str, Any],
    ) -> Any:
        ...

    async def validate_node(
        self,
        node: Dict[str, Any],
        available_inputs: set[str],
    ) -> None:
        ...
