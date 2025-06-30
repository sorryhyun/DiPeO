"""Use case for executing diagrams."""

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo_core import BaseService, SupportsExecution
from dipeo_diagram import backend_to_graphql
from dipeo_domain.models import DomainDiagram

from ..engine_factory import EngineFactory

if TYPE_CHECKING:
    from dipeo_domain.domains.ports import MessageRouterPort, StateStorePort
    from dipeo_domain.domains.diagram.services import DiagramStorageAdapter
    from dipeo_domain.domains.execution.services import ServiceRegistry
    from ..execution_engine import ExecutionObserver


class ExecuteDiagramUseCase(BaseService, SupportsExecution):
    """Use case for executing diagrams with persistence and streaming."""

    def __init__(
        self,
        service_registry: "ServiceRegistry",
        state_store: "StateStorePort",
        message_router: "MessageRouterPort",
        diagram_storage: "DiagramStorageAdapter",
    ):
        """Initialize with required services."""
        super().__init__()
        self.service_registry = service_registry
        self.state_store = state_store
        self.message_router = message_router
        self.diagram_storage = diagram_storage
        self._observers: list["ExecutionObserver"] = []

    async def initialize(self):
        """Initialize the service and register handlers."""
        # Import handlers to register them
        from .. import handlers  # noqa: F401

        # Import and setup observers
        from dipeo_domain.domains.execution.observers import (
            StateStoreObserver,
            StreamingObserver,
        )

        self._streaming_observer = StreamingObserver(self.message_router)
        self._observers = [
            StateStoreObserver(self.state_store),
            self._streaming_observer,
        ]

    async def execute_diagram(
        self,
        diagram: dict | str,
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Optional[Any] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute a diagram with streaming updates.

        Args:
            diagram: Diagram data or ID
            options: Execution options
            execution_id: Unique execution ID
            interactive_handler: Optional handler for interactive nodes

        Yields:
            Execution updates
        """
        # Ensure initialized
        if not self._observers:
            await self.initialize()

        # Load diagram if ID provided
        if isinstance(diagram, str):
            diagram_data = await self.diagram_storage.read_file(f"{diagram}.json")
            diagram_obj = backend_to_graphql(diagram_data)
        else:
            diagram_obj = DomainDiagram.model_validate(diagram)

        # Create engine with factory
        engine = EngineFactory.create_server_engine(
            service_registry=self.service_registry,
            state_store=self.state_store,
            message_router=self.message_router,
        )

        # Subscribe to streaming updates
        update_queue = await self._streaming_observer.subscribe(execution_id)

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

        # Launch execution task
        asyncio.create_task(run_execution())

        # Stream updates
        while True:
            update = await update_queue.get()
            yield update

            # Check for terminal states
            if update.get("type") in ["execution_complete", "execution_error"]:
                break
