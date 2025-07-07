"""Simplified server execution service using the shared engine."""

import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional, Callable, Dict

from dipeo.core import BaseService, SupportsExecution

from dipeo.domain.domains.execution.observers import StreamingObserver

if TYPE_CHECKING:
    from dipeo.domain.domains.ports import MessageRouterPort, StateStorePort
    from dipeo.domain.domains.diagram.storage_adapter import DiagramStorageAdapter
    from ..unified_service_registry import UnifiedServiceRegistry


class ExecuteDiagramUseCase(BaseService, SupportsExecution):
    """Server execution service with persistence and streaming."""

    def __init__(
        self,
        service_registry: "UnifiedServiceRegistry",
        state_store: "StateStorePort",
        message_router: "MessageRouterPort",
        diagram_storage_service: "DiagramStorageAdapter",
    ):
        super().__init__()
        self.service_registry = service_registry
        self.state_store = state_store
        self.message_router = message_router
        self.diagram_storage_service = diagram_storage_service

    async def initialize(self):
        """Initialize the service."""
        # Note: Handler registration should be done at the application layer
        pass

    async def execute_diagram(  # type: ignore[override]
        self,
        diagram: Dict[str, Any],
        options: Dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute diagram with streaming updates."""

        from dipeo.models import DomainDiagram
        from dipeo.diagram import BackendDiagram, backend_to_graphql

        # Check if diagram is in backend format (dict of dicts) or domain format (lists)
        if isinstance(diagram.get("nodes"), dict):
            # Convert from backend format to domain format
            backend_diagram = BackendDiagram(**diagram)
            diagram_obj = backend_to_graphql(backend_diagram)
        else:
            # Already in domain format, validate directly
            diagram_obj = DomainDiagram.model_validate(diagram)

        # Create streaming observer for this execution
        streaming_observer = StreamingObserver(self.message_router)

        # Import EngineFactory from current package
        from ..engine_factory import EngineFactory
        
        # Create engine with factory
        engine = EngineFactory.create_engine(
            service_registry=self.service_registry,
            state_store=self.state_store,
            message_router=self.message_router,
            custom_observers=[streaming_observer],
        )

        # Subscribe to streaming updates
        update_queue = await streaming_observer.subscribe(execution_id)

        # Start execution in background
        async def run_execution():
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug("Starting engine execution")
                async for _ in engine.execute(
                    diagram_obj,
                    execution_id,
                    options,
                    interactive_handler,
                ):
                    pass  # Engine uses observers for updates
                logger.debug("Engine execution completed")
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Engine execution failed: {e}", exc_info=True)
                await update_queue.put(
                    {
                        "type": "execution_error",
                        "error": str(e),
                    }
                )

        # Launch execution
        asyncio.create_task(run_execution())

        # Stream updates
        while True:
            update = await update_queue.get()
            yield update

            if update.get("type") in ["execution_complete", "execution_error"]:
                break
