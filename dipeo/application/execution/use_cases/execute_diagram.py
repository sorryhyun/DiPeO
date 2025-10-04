import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.engine.typed_engine import TypedExecutionEngine
from dipeo.application.execution.use_cases.diagram_preparation import prepare_and_compile_diagram
from dipeo.application.execution.use_cases.state_initialization import initialize_execution_state
from dipeo.application.registry import (
    DIAGRAM_PORT,
    MESSAGE_ROUTER,
    STATE_STORE,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import Status
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.diagram_generated import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.domain.events.unified_ports import EventBus as MessageRouterPort
    from dipeo.domain.execution.state.ports import ExecutionStateRepository as StateStorePort
    from dipeo.infrastructure.diagram.drivers.diagram_service import DiagramService

    from ...registry import ServiceRegistry

logger = get_module_logger(__name__)


class ExecuteDiagramUseCase(LoggingMixin, InitializationMixin):
    def __init__(
        self,
        service_registry: "ServiceRegistry",
        state_store: Optional["StateStorePort"] = None,
        message_router: Optional["MessageRouterPort"] = None,
        diagram_service: Optional["DiagramService"] = None,
        container: Optional["Container"] = None,
    ):
        # Initialize mixins
        InitializationMixin.__init__(self)
        self.service_registry = service_registry
        self.container = container

        self.state_store = state_store or service_registry.resolve(STATE_STORE)
        self.message_router = message_router or service_registry.resolve(MESSAGE_ROUTER)
        self.diagram_service = diagram_service or service_registry.resolve(DIAGRAM_PORT)

        if not self.state_store:
            raise ValueError("state_store is required but not found in service registry")
        if not self.message_router:
            raise ValueError("message_router is required but not found in service registry")
        if not self.diagram_service:
            raise ValueError("diagram_service is required but not found in service registry")

    async def initialize(self):
        pass

    async def execute_diagram(  # type: ignore[override]
        self,
        diagram: "DomainDiagram",  # Now only accepts DomainDiagram
        options: dict[str, Any],
        execution_id: str,
        interactive_handler: Callable | None = None,
        event_filter: Any | None = None,  # EventFilter for sub-diagram scoping
    ) -> AsyncGenerator[dict[str, Any]]:
        """Execute diagram with streaming updates."""

        # Use prepare diagram service for clean deserialization -> compilation
        typed_diagram = await prepare_and_compile_diagram(self.service_registry, diagram, options)
        await initialize_execution_state(self.state_store, execution_id, typed_diagram, options)

        # Store event filter in options for the engine to use
        if event_filter:
            options["event_filter"] = event_filter
        from dipeo.application.registry.keys import EVENT_BUS

        # Get event bus from registry if available
        event_bus = None
        if self.service_registry.has(EVENT_BUS):
            event_bus = self.service_registry.resolve(EVENT_BUS)

        # Subscribe MetricsObserver to the event bus if available
        from dipeo.application.execution.observers import MetricsObserver
        from dipeo.application.registry.keys import ServiceKey
        from dipeo.domain.events import EventType

        METRICS_OBSERVER_KEY = ServiceKey[MetricsObserver]("metrics_observer")
        if self.service_registry.has(METRICS_OBSERVER_KEY) and event_bus:
            metrics_observer = self.service_registry.resolve(METRICS_OBSERVER_KEY)

            # Update the event_bus reference so METRICS_COLLECTED events go to the right place
            metrics_observer.event_bus = event_bus

            # Subscribe to execution and node events for metrics collection
            metrics_events = [
                EventType.EXECUTION_STARTED,
                EventType.NODE_STARTED,
                EventType.NODE_COMPLETED,
                EventType.NODE_ERROR,
                EventType.EXECUTION_COMPLETED,
            ]

            # Subscribe metrics observer to events
            for event_type in metrics_events:
                await event_bus.subscribe(event_type, metrics_observer)

        # Create engine with event bus
        engine = TypedExecutionEngine(
            service_registry=self.service_registry,
            event_bus=event_bus,
        )

        # No update iterator needed with unified monitoring

        async def run_execution():
            try:
                exec_state = await self.state_store.get_state(execution_id)

                # The engine will emit EXECUTION_STARTED event which triggers state updates
                async for _ in engine.execute(
                    diagram=typed_diagram,
                    execution_state=exec_state,
                    options=options,
                    container=self.container,
                    interactive_handler=interactive_handler,
                ):
                    pass

                # Engine handles completion events internally

            except Exception as e:
                logger.error(f"Engine execution failed: {e}", exc_info=True)
                # Error event will be emitted by the engine
                raise

        # Check if this is a sub-diagram execution (for batch parallel support)
        is_sub_diagram = options.get("is_sub_diagram", False) or options.get("parent_execution_id")
        is_batch_item = options.get("is_batch_item", False) or (
            options.get("metadata", {}).get("is_batch_item", False)
        )

        # Create the execution task
        execution_task = asyncio.create_task(run_execution())

        # For sub-diagrams, we need to track the task to ensure proper parallel execution
        # Store it so the iterator below can properly coordinate
        if is_sub_diagram:
            # We'll handle this task specially in the update loop
            pass

        try:
            # Wait for execution completion and yield status
            if is_batch_item or is_sub_diagram:
                # Wait for the execution task to complete
                with contextlib.suppress(Exception):
                    await execution_task  # Errors are already handled in run_execution

                # Get final state
                state = await self.state_store.get_state(execution_id)
                # Only treat FAILED and ABORTED as errors, not PENDING or RUNNING
                is_error = state and state.status in [Status.FAILED, Status.ABORTED]
                yield {
                    "type": "execution_error" if is_error else "execution_complete",
                    "execution_id": execution_id,
                    "status": state.status.value if state else "unknown",
                    "error": state.error
                    if state and state.error
                    else ("Failed" if is_error else None),
                }
            else:
                # For web/CLI executions, run the task and poll for completion
                # The task needs to actually run, not just be created

                # Start monitoring for completion while the task runs
                poll_task = asyncio.create_task(self._poll_execution_status(execution_id))

                try:
                    # Run both the execution and polling concurrently
                    # The execution task will do the actual work
                    # The poll task will monitor for completion
                    _done, pending = await asyncio.wait(
                        [execution_task, poll_task], return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel any pending tasks
                    for task in pending:
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task

                    # Get final state
                    state = await self.state_store.get_state(execution_id)
                    if not state:
                        # Shouldn't happen, but handle it
                        yield {
                            "type": "execution_error",
                            "execution_id": execution_id,
                            "status": "unknown",
                            "error": "Execution state not found",
                        }
                    else:
                        # Only treat FAILED and ABORTED as errors
                        is_error = state.status in [Status.FAILED, Status.ABORTED]
                        yield {
                            "type": "execution_error" if is_error else "execution_complete",
                            "execution_id": execution_id,
                            "status": state.status.value,
                            "error": state.error
                            if state.error
                            else ("Failed" if is_error else None),
                        }
                except Exception:
                    # Make sure to cancel the execution task if something goes wrong
                    execution_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await execution_task
                    raise
        except Exception:
            # Re-raise any exceptions
            raise

    async def _poll_execution_status(self, execution_id: str) -> None:
        """Poll for execution completion."""
        while True:
            state = await self.state_store.get_state(execution_id)
            if state and state.status in [
                Status.COMPLETED,
                Status.FAILED,
                Status.ABORTED,
                Status.MAXITER_REACHED,
            ]:
                return
            await asyncio.sleep(1)
