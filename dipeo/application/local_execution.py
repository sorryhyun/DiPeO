"""Local execution service for running diagrams without server dependency."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.core import BaseService, SupportsExecution
from dipeo.models import DomainDiagram

from .engine_factory import EngineFactory
from dipeo.domain.services.execution.protocols import ExecutionObserver
from .unified_service_registry import UnifiedServiceRegistry

if TYPE_CHECKING:
    from .context import ApplicationExecutionContext

log = logging.getLogger(__name__)


class LocalUpdateCollector(ExecutionObserver):
    """Observer that collects updates for local execution."""

    def __init__(self):
        self.updates: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def on_execution_start(
        self, execution_id: str, diagram_id: str | None
    ) -> None:
        await self.updates.put(
            {
                "type": "execution_start",
                "execution_id": execution_id,
                "diagram_id": diagram_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def on_node_start(self, execution_id: str, node_id: str) -> None:
        await self.updates.put(
            {
                "type": "node_update",
                "execution_id": execution_id,
                "node_id": node_id,
                "status": "running",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def on_node_complete(self, execution_id: str, node_id: str, output) -> None:
        await self.updates.put(
            {
                "type": "node_update",
                "execution_id": execution_id,
                "node_id": node_id,
                "status": "completed",
                "output": output.model_dump()
                if hasattr(output, "model_dump")
                else output,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def on_node_error(self, execution_id: str, node_id: str, error: str) -> None:
        await self.updates.put(
            {
                "type": "node_update",
                "execution_id": execution_id,
                "node_id": node_id,
                "status": "failed",
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def on_execution_complete(self, execution_id: str) -> None:
        await self.updates.put(
            {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def on_execution_error(self, execution_id: str, error: str) -> None:
        await self.updates.put(
            {
                "type": "execution_error",
                "execution_id": execution_id,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class LocalExecutionService(BaseService, SupportsExecution):
    """Local execution service for CLI and tests."""

    def __init__(self, app_context: ApplicationExecutionContext):
        """Initialize with application context."""
        super().__init__()
        self.app_context = app_context
        self.service_registry = UnifiedServiceRegistry.from_context(app_context)

    async def initialize(self) -> None:
        """Initialize the service."""
        # Import handlers to ensure they are registered
        from . import handlers  # noqa: F401

    async def execute_diagram(
        self,
        diagram: dict[str, Any] | str | DomainDiagram,
        options: dict[str, Any],
        execution_id: str,
        interactive_handler=None,
        custom_observers: list[ExecutionObserver] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute diagram locally with streaming updates."""
        log.info(
            f"LocalExecutionService.execute_diagram called with execution_id: {execution_id}"
        )

        # Prepare diagram
        if isinstance(diagram, dict):
            diagram_obj = DomainDiagram.model_validate(diagram)
        elif isinstance(diagram, str):
            # In local mode, we expect the diagram to be passed as data, not ID
            raise ValueError("Local execution requires diagram data, not ID")
        else:
            diagram_obj = diagram

        # Create update collector
        update_collector = LocalUpdateCollector()

        # Combine observers
        observers = [update_collector]
        if custom_observers:
            observers.extend(custom_observers)

        # Create engine with factory
        engine = EngineFactory.create_engine(
            service_registry=self.service_registry,
            state_store=None,  # No persistence in local mode
            message_router=None,  # No streaming in local mode
            include_state_observer=False,
            include_streaming_observer=False,
            custom_observers=observers,
        )

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
                await update_collector.on_execution_error(execution_id, str(e))

        # Launch execution
        asyncio.create_task(run_execution())

        # Stream updates from collector
        while True:
            update = await update_collector.updates.get()
            yield update

            # Check for terminal states
            if update.get("type") in ["execution_complete", "execution_error"]:
                break
