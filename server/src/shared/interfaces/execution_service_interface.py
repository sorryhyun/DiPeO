"""Interface for execution service."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Any, Dict, Optional


class IExecutionService(ABC):
    """Interface for running a diagram through the execution engine."""
    
    @abstractmethod
    async def execute_diagram(
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Validate and execute a diagram, yielding execution updates."""
        pass