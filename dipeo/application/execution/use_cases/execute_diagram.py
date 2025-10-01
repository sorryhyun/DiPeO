import asyncio
import contextlib
import logging

from dipeo.config.base_logger import get_module_logger
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.registry import (
    API_KEY_SERVICE,
    DIAGRAM_PORT,
    EXECUTION_ORCHESTRATOR,
    MESSAGE_ROUTER,
    PREPARE_DIAGRAM_USE_CASE,
    STATE_STORE,
)
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

        # Get prepare diagram service for clean deserialization -> compilation
        self._prepare_diagram_service = None

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
        typed_diagram = await self._prepare_and_compile_diagram(diagram, options)
        await self._initialize_typed_execution_state(execution_id, typed_diagram, options)

        # Store event filter in options for the engine to use
        if event_filter:
            options["event_filter"] = event_filter
        from dipeo.application.execution.typed_engine import TypedExecutionEngine
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
                    done, pending = await asyncio.wait(
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

    async def _prepare_and_compile_diagram(
        self, diagram: "DomainDiagram", options: dict[str, Any]
    ) -> "ExecutableDiagram":  # type: ignore
        """Prepare and compile diagram using the standard flow."""

        # Try to get prepare diagram service from registry
        if not self._prepare_diagram_service:
            with contextlib.suppress(Exception):
                self._prepare_diagram_service = self.service_registry.resolve(
                    PREPARE_DIAGRAM_USE_CASE
                )

        # If we have the prepare service, use it for clean deserialization -> compilation
        if self._prepare_diagram_service:
            # Prepare diagram handles all format conversion and compilation
            # Pass diagram_source_path from options if available
            diagram_id = options.get("diagram_source_path")
            executable_diagram = await self._prepare_diagram_service.prepare_for_execution(
                diagram=diagram,
                diagram_id=diagram_id,  # Pass the original source path
                validate=False,  # Skip validation for now as mentioned in TODO
            )
        else:
            # Fallback to inline implementation if service not available
            from dipeo.application.registry.keys import DIAGRAM_COMPILER

            # Already have a DomainDiagram, just compile it
            domain_diagram = diagram

            # Compile to ExecutableDiagram
            compiler = self.service_registry.resolve(DIAGRAM_COMPILER)
            if not compiler:
                raise RuntimeError("DiagramCompiler not found in registry")

            executable_diagram = compiler.compile(domain_diagram)

            # Add API keys
            api_key_service = self.service_registry.resolve(API_KEY_SERVICE)
            if api_key_service:
                api_keys = self._extract_api_keys_for_typed_diagram(domain_diagram, api_key_service)
                if api_keys:
                    executable_diagram.metadata["api_keys"] = api_keys

            # Add metadata
            if domain_diagram.metadata:
                executable_diagram.metadata.update(domain_diagram.metadata.__dict__)

            # Add diagram source path if available
            diagram_source_path = options.get("diagram_source_path")
            if diagram_source_path:
                executable_diagram.metadata["diagram_source_path"] = diagram_source_path
                # Also set as diagram_id if not already set
                if "diagram_id" not in executable_diagram.metadata:
                    executable_diagram.metadata["diagram_id"] = diagram_source_path

            # Add persons metadata
            if hasattr(domain_diagram, "persons") and domain_diagram.persons:
                persons_dict = {}
                persons_list = (
                    list(domain_diagram.persons.values())
                    if isinstance(domain_diagram.persons, dict)
                    else domain_diagram.persons
                )
                for person in persons_list:
                    person_id = str(person.id)
                    persons_dict[person_id] = {
                        "name": person.label,
                        "service": person.llm_config.service.value
                        if hasattr(person.llm_config.service, "value")
                        else person.llm_config.service,
                        "model": person.llm_config.model,
                        "api_key_id": str(person.llm_config.api_key_id),
                        "system_prompt": person.llm_config.system_prompt or "",
                        "temperature": getattr(person.llm_config, "temperature", 0.7),
                        "max_tokens": getattr(person.llm_config, "max_tokens", None),
                    }
                executable_diagram.metadata["persons"] = persons_dict

        await self._register_typed_person_configs(executable_diagram)

        return executable_diagram

    async def _register_typed_person_configs(self, typed_diagram: "ExecutableDiagram") -> None:  # type: ignore
        """Register person configurations from typed diagram."""
        from dipeo.diagram_generated.generated_nodes import PersonJobNode

        conversation_service = None
        if hasattr(self.service_registry, "resolve"):
            # Use the consolidated conversation manager service
            conversation_service = self.service_registry.resolve(EXECUTION_ORCHESTRATOR)

        if conversation_service:
            # Register persons from typed nodes
            from dipeo.diagram_generated.generated_nodes import NodeType

            person_job_nodes = typed_diagram.get_nodes_by_type(NodeType.PERSON_JOB)
            for node in person_job_nodes:
                if isinstance(node, PersonJobNode) and node.person:
                    person_id = str(node.person)

                    # Get person config from metadata if available, otherwise empty dict
                    person_config = {}
                    if typed_diagram.metadata and "persons" in typed_diagram.metadata:
                        persons_metadata = typed_diagram.metadata["persons"]
                        if person_id in persons_metadata:
                            person_config = persons_metadata[person_id]

                    # Register person - repository will handle defaults
                    if hasattr(conversation_service, "register_person"):
                        conversation_service.register_person(person_id, person_config)
                    else:
                        # For services that don't have register_person,
                        # we can at least ensure the person memory is created
                        if hasattr(conversation_service, "get_or_create_person_memory"):
                            conversation_service.get_or_create_person_memory(person_id)

    async def _initialize_typed_execution_state(
        self,
        execution_id: str,
        typed_diagram: "ExecutableDiagram",  # type: ignore
        options: dict[str, Any],
    ) -> None:
        """Initialize execution state for typed diagram."""

        from dipeo.diagram_generated import ExecutionState, LLMUsage, Status

        # Create initial execution state
        initial_state = ExecutionState(
            id=execution_id,
            status=Status.PENDING,
            diagram_id=typed_diagram.metadata.get("id") if typed_diagram.metadata else None,
            started_at=datetime.now().isoformat(),
            node_states={},
            node_outputs={},
            variables=options.get("variables", {}),
            is_active=True,
            llm_usage=LLMUsage(input=0, output=0),
            exec_counts={},
            executed_nodes=[],
        )

        # Store initial state
        await self.state_store.save_state(initial_state)

    def _extract_api_keys_for_typed_diagram(
        self, diagram: "DomainDiagram", api_key_service
    ) -> dict[str, str]:
        """Extract API keys needed by the diagram.

        Args:
            diagram: The domain diagram (before compilation)
            api_key_service: The API key service

        Returns:
            Dictionary mapping API key IDs to actual keys
        """
        api_keys = {}

        # Get all available API keys
        all_keys = {
            info["id"]: api_key_service.get_api_key(info["id"])["key"]
            for info in api_key_service.list_api_keys()
        }

        # Extract API key references from persons
        if hasattr(diagram, "persons") and diagram.persons:
            # Handle both dict and list formats
            persons_list = (
                list(diagram.persons.values())
                if isinstance(diagram.persons, dict)
                else diagram.persons
            )
            for person in persons_list:
                api_key_id = None
                if hasattr(person, "api_key_id"):
                    api_key_id = person.api_key_id
                if api_key_id and api_key_id in all_keys:
                    api_keys[api_key_id] = all_keys[api_key_id]

        return api_keys
