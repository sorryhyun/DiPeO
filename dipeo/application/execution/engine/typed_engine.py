"""Refactored typed execution engine using unified ExecutionContext."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.engine.context import TypedExecutionContext
from dipeo.application.execution.engine.node_executor import execute_single_node
from dipeo.application.execution.engine.scheduler import NodeScheduler
from dipeo.application.execution.events import EventPipeline
from dipeo.config import get_settings
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ExecutionState, NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.events.unified_ports import EventBus

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = get_module_logger(__name__)


class TypedExecutionEngine:
    """Refactored execution engine with clean separation of concerns."""

    def __init__(
        self,
        service_registry: "ServiceRegistry",
        event_bus: EventBus,
    ):
        self.service_registry = service_registry
        self._settings = get_settings()
        self.event_bus = event_bus
        self._scheduler: NodeScheduler | None = None

    async def execute(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        options: dict[str, Any],
        container: Optional["Container"] = None,
        interactive_handler: Any | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # Event bus should already be started

        context = None
        log_handler = None
        event_pipeline = None
        try:
            from dipeo.application.execution.states.execution_state_persistence import (
                ExecutionStatePersistence,
            )
            from dipeo.diagram_generated import Status

            context = TypedExecutionContext(
                execution_id=str(execution_state.id),
                diagram_id=str(execution_state.diagram_id),
                diagram=diagram,
                service_registry=self.service_registry,
                event_bus=self.event_bus,
                container=container,
            )

            node_states = {}
            tracker = context.get_tracker()
            ExecutionStatePersistence.load_from_state(execution_state, node_states, tracker)

            if node_states:
                context._state_tracker._node_states = node_states

            existing_states = context.state.get_all_node_states()
            for node in diagram.get_nodes_by_type(None) or diagram.nodes:
                if node.id not in existing_states:
                    context._state_tracker.initialize_node(node.id)

            context.set_variables(execution_state.variables or {})

            if "parent_metadata" in options:
                context._parent_metadata = options["parent_metadata"]

            # Initialize the unified event pipeline
            event_pipeline = EventPipeline(
                execution_id=str(execution_state.id),
                diagram_id=str(execution_state.diagram_id),
                event_bus=self.event_bus,
                state_tracker=context.state,
            )

            from dipeo.infrastructure.execution.logging_handler import setup_execution_logging

            log_handler = setup_execution_logging(
                event_bus=self.event_bus,
                execution_id=str(context.execution_id),
                log_level=logging.DEBUG if options.get("debug", False) else logging.INFO,
            )

            self._scheduler = NodeScheduler(diagram, context)
            context.scheduler = self._scheduler

            for key, value in options.get("metadata", {}).items():
                context.set_execution_metadata(key, value)

            await event_pipeline.emit(
                "execution_started",
                variables=execution_state.variables or {},
            )

            from dipeo.application.registry.keys import DIAGRAM, EXECUTION_CONTEXT

            self.service_registry.register(DIAGRAM, diagram)
            self.service_registry.register(
                EXECUTION_CONTEXT, {"interactive_handler": interactive_handler}
            )

            step_count = 0
            while not context.is_execution_complete():
                from dipeo.infrastructure.timing import atime_phase

                async with atime_phase(str(context.execution_id), "system", "node_scheduling"):
                    ready_nodes = await self._scheduler.get_ready_nodes(context)

                if not ready_nodes:
                    poll_interval = getattr(
                        self._settings.execution, "node_ready_poll_interval", 0.01
                    )
                    await asyncio.sleep(poll_interval)
                    continue

                step_count += 1
                results = await self._execute_nodes(ready_nodes, context, event_pipeline)

                for node_id in results:
                    self._scheduler.mark_node_completed(NodeID(node_id), context)

                from dipeo.application.execution.engine.reporting import calculate_progress

                progress = calculate_progress(context)

                yield {
                    "type": "step_complete",
                    "step": step_count,
                    "executed_nodes": list(results.keys()),
                    "progress": progress,
                    "scheduler_stats": self._scheduler.get_execution_stats(),
                }

            execution_path = [str(node_id) for node_id in context.state.get_completed_nodes()]

            await event_pipeline.emit(
                "execution_completed",
                status=Status.COMPLETED,
                total_steps=step_count,
                execution_path=execution_path,
            )

            # State is now persisted asynchronously via CacheFirstStateStore listening to events
            # No need for direct state_store calls - the event bus handles persistence

            yield {
                "type": "execution_complete",
                "total_steps": step_count,
                "execution_path": execution_path,
            }

        except Exception as e:
            from dipeo.diagram_generated import Status

            if event_pipeline:
                await event_pipeline.emit("execution_error", exc=e)

            yield {
                "type": "execution_error",
                "error": str(e),
            }
            raise
        finally:
            # Wait for all pending events to complete
            if event_pipeline:
                await event_pipeline.wait_for_pending_events()

            if log_handler:
                from dipeo.infrastructure.execution.logging_handler import (
                    teardown_execution_logging,
                )

                teardown_execution_logging(log_handler)

            # Event bus cleanup handled externally

    async def _execute_nodes(
        self,
        nodes: list[ExecutableNode],
        context: TypedExecutionContext,
        event_pipeline: EventPipeline,
    ) -> dict[str, dict[str, Any]]:
        from dipeo.config.execution import ENGINE_MAX_CONCURRENT

        max_concurrent = ENGINE_MAX_CONCURRENT

        if len(nodes) == 1:
            node = nodes[0]
            result = await execute_single_node(
                node, context, event_pipeline, self._scheduler, self.service_registry
            )
            return {str(node.id): result}

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(node: ExecutableNode) -> tuple[str, dict[str, Any]]:
            async with semaphore:
                result = await execute_single_node(
                    node, context, event_pipeline, self._scheduler, self.service_registry
                )
                return str(node.id), result

        tasks = [execute_with_semaphore(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for result in results:
            if isinstance(result, Exception):
                raise result
            node_id, node_result = result
            output[node_id] = node_result

        return output
