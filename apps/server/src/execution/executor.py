"""Main diagram executor that orchestrates the execution flow."""

import structlog
from typing import Any, Dict, Tuple, Optional, Callable, Awaitable

from ..services.llm_service import LLMService
from ..services.api_key_service import APIKeyService
from ..services.memory_service import MemoryService

logger = structlog.get_logger(__name__)


class DiagramExecutor:
    """Executes a block diagram and returns (context, total_cost).
    
    This is now a thin wrapper around the V2 execution engine.
    Maintains backward compatibility while using the new architecture.
    """

    def __init__(self,
                 diagram: dict,
                 memory_service: MemoryService = None,
                 status_callback: Optional[Callable[[dict], Awaitable[None]]] = None):
        """Initialize diagram executor.
        
        Args:
            diagram: Diagram configuration with nodes, arrows, and persons
            memory_service: Service for managing conversation memory
            status_callback: Optional async callback for status updates
        """
        self.diagram = diagram
        self.status_callback = status_callback

        # Initialize services
        self.api_key_service = APIKeyService()
        self.llm_service = LLMService(self.api_key_service)
        self.memory_service = memory_service or MemoryService()
        logger.info("Using V2 execution engine")

    async def run(self) -> Tuple[Dict[str, Any], float]:
        """Run the diagram execution
        
        Returns:
            Tuple of (node outputs dict, total cost)
        """
        from apps.server.src.execution.core.execution_engine import ExecutionEngine

        engine = ExecutionEngine(
            diagram=self.diagram,
            memory_service=self.memory_service,
            llm_service=self.llm_service,
            streaming_update_callback=self.status_callback
        )
        return await engine.execute()