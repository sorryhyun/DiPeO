"""Simplified server execution service using the shared engine."""

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from dipeo_core import BaseService, SupportsExecution
from dipeo_diagram import backend_to_graphql
from dipeo_application import EngineFactory

from ..observers import StreamingObserver

if TYPE_CHECKING:
    from dipeo_domain.domains.ports import MessageRouterPort, StateStorePort
    from dipeo_domain.domains.diagram.services import DiagramStorageAdapter
    from .service_registry import ServiceRegistry


class ExecuteDiagramUseCase(BaseService, SupportsExecution):
    """Server execution service with persistence and streaming."""

    def __init__(
        self,
        service_registry: "ServiceRegistry",
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
        # Import handlers to register them
        from dipeo_application import handlers  # noqa: F401

    async def execute_diagram(
        self,
        diagram: dict | str,
        options: dict,
        execution_id: str,
        interactive_handler=None,
    ) -> AsyncIterator[dict]:
        """Execute diagram with streaming updates."""

        # Load diagram if ID provided
        if isinstance(diagram, str):
            diagram_data = await self.diagram_storage_service.read_file(
                f"{diagram}.json"
            )
            diagram_obj = backend_to_graphql(diagram_data)
        else:
            from dipeo_domain.models import DomainDiagram

            diagram_obj = DomainDiagram.model_validate(diagram)

        # Create streaming observer for this execution
        streaming_observer = StreamingObserver(self.message_router)
        
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
                async for _ in engine.execute(
                    diagram_obj,
                    execution_id,
                    options,
                    interactive_handler,
                ):
                    pass  # Engine uses observers for updates
            except Exception as e:
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
