"""Refactored typed execution engine using unified ExecutionContext."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.event_pipeline import EventPipeline
from dipeo.application.execution.scheduler import NodeScheduler
from dipeo.application.execution.typed_execution_context import TypedExecutionContext
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

                from dipeo.application.execution.reporting import calculate_progress

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
            result = await self._execute_single_node(node, context, event_pipeline)
            return {str(node.id): result}

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(node: ExecutableNode) -> tuple[str, dict[str, Any]]:
            async with semaphore:
                result = await self._execute_single_node(node, context, event_pipeline)
                return str(node.id), result

        tasks = [execute_with_semaphore(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for node_id, result in results:
            if isinstance(result, Exception):
                raise result
            output[node_id] = result

        return output

    async def _execute_single_node(
        self, node: ExecutableNode, context: TypedExecutionContext, event_pipeline: EventPipeline
    ) -> dict[str, Any]:
        node_id = node.id
        start_time = time.time()
        epoch = context.current_epoch()

        if self._scheduler:
            self._scheduler.mark_node_running(node_id, epoch)

        await event_pipeline.emit("node_started", node=node)

        try:
            if await self._should_skip_max_iteration(node, context):
                return await self._handle_max_iteration_reached(node, context, event_pipeline)

            output = await self._execute_node_handler(node, context, event_pipeline)

            from dipeo.diagram_generated import NodeType

            # Always emit tokens for non-condition nodes, even if output is empty/falsy
            # This ensures downstream nodes receive tokens and can become ready
            if node.type != NodeType.CONDITION:
                outputs = {"default": output} if not isinstance(output, dict) else output
                context.emit_outputs_as_tokens(node_id, outputs, epoch)

            duration_ms = (time.time() - start_time) * 1000
            llm_usage = self._extract_llm_usage(output)

            # Add metadata to envelope if applicable
            if hasattr(output, "meta") and isinstance(output.meta, dict):
                output.meta["execution_time_ms"] = duration_ms
                if llm_usage:
                    output.meta["token_usage"] = llm_usage

            await self._handle_node_completion(node, output, context, event_pipeline)

            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)

            exec_count = context.state.get_node_execution_count(node.id)
            await event_pipeline.emit(
                "node_completed",
                node=node,
                envelope=output,
                exec_count=exec_count,
                duration_ms=duration_ms,
            )

            return self._format_node_result(output)

        except Exception as e:
            if self._scheduler:
                self._scheduler.mark_node_complete(node_id, epoch)
            await self._handle_node_failure(context, node, e, event_pipeline)
            raise

    async def _should_skip_max_iteration(
        self, node: ExecutableNode, context: TypedExecutionContext
    ) -> bool:
        from dipeo.diagram_generated.generated_nodes import PersonJobNode

        if isinstance(node, PersonJobNode):
            current_count = context.state.get_node_execution_count(node.id)
            return current_count >= node.max_iteration
        return False

    async def _handle_max_iteration_reached(
        self, node: ExecutableNode, context: TypedExecutionContext, event_pipeline: EventPipeline
    ) -> dict[str, Any]:
        from dipeo.diagram_generated.enums import Status
        from dipeo.domain.execution.envelope import EnvelopeFactory

        node_id = node.id
        current_count = context.state.get_node_execution_count(node_id)

        logger.info(
            f"PersonJobNode {node_id} has reached max_iteration "
            f"({node.max_iteration}), transitioning to MAXITER_REACHED"
        )

        output = EnvelopeFactory.create(
            body="", produced_by=str(node_id), meta={"status": Status.MAXITER_REACHED}
        )

        context.state.transition_to_maxiter(node_id, output)

        from dipeo.diagram_generated import Status

        await event_pipeline.emit(
            "node_completed", node=node, envelope=None, exec_count=current_count
        )

        return {"value": "", "status": "MAXITER_REACHED"}

    async def _execute_node_handler(
        self, node: ExecutableNode, context: TypedExecutionContext, event_pipeline: EventPipeline
    ) -> Any:
        with context.executing_node(node.id):
            context.state.transition_to_running(node.id, context.current_epoch())

            from dipeo.diagram_generated import Status

            handler = self._get_handler(node.type)
            inputs = await handler.resolve_envelope_inputs(
                request=type("TempRequest", (), {"node": node, "context": context})()
            )

            request = self._create_execution_request(node, context, inputs)
            output = await handler.pre_execute(request)

            if output is None:
                output = await handler.execute_with_envelopes(request, inputs)

            if hasattr(handler, "post_execute"):
                output = handler.post_execute(request, output)

            return output

    def _create_execution_request(
        self, node: ExecutableNode, context: TypedExecutionContext, inputs: Any
    ) -> Any:
        from dipeo.application.execution.execution_request import ExecutionRequest

        request_metadata = {}
        if hasattr(context.diagram, "metadata") and context.diagram.metadata:
            request_metadata["diagram_source_path"] = context.diagram.metadata.get(
                "diagram_source_path"
            )
            request_metadata["diagram_id"] = context.diagram.metadata.get("diagram_id")

        if hasattr(context, "_parent_metadata") and context._parent_metadata:
            request_metadata.update(context._parent_metadata)

        return ExecutionRequest(
            node=node,
            context=context,
            inputs=inputs,
            services=self.service_registry,
            metadata=request_metadata,
            execution_id=context.execution_id,
            parent_container=context.container,
            parent_registry=self.service_registry,
        )

    def _extract_llm_usage(self, output: Any) -> dict | None:
        if hasattr(output, "meta") and isinstance(output.meta, dict):
            llm_usage = output.meta.get("llm_usage")
            if llm_usage:
                if hasattr(llm_usage, "model_dump"):
                    return llm_usage.model_dump()
                elif isinstance(llm_usage, dict):
                    return llm_usage
        return None

    async def _handle_node_failure(
        self,
        context: TypedExecutionContext,
        node: ExecutableNode,
        error: Exception,
        event_pipeline: EventPipeline,
    ) -> None:
        logger.error(f"Error executing node {node.id}: {error}", exc_info=True)
        context.state.transition_to_failed(node.id, str(error))

        from dipeo.diagram_generated import Status

        await event_pipeline.emit("node_error", node=node, exc=error)

    def _format_node_result(self, envelope: Any) -> dict[str, Any]:
        if hasattr(envelope, "body"):
            body = envelope.body
            if hasattr(body, "dict"):
                return body.dict()
            elif hasattr(body, "model_dump"):
                return body.model_dump()
            elif isinstance(body, dict):
                return body
            else:
                return {"value": str(body)}
        elif hasattr(envelope, "to_dict"):
            return envelope.to_dict()
        elif hasattr(envelope, "value"):
            result = {"value": envelope.value}
            if hasattr(envelope, "metadata") and envelope.metadata:
                result["metadata"] = envelope.metadata
            return result
        else:
            return {"value": envelope}

    def _get_handler(self, node_type: str):
        from dipeo.application import get_global_registry
        from dipeo.application.execution.handlers.core.factory import HandlerFactory

        registry = get_global_registry()
        if not hasattr(registry, "_service_registry") or registry._service_registry is None:
            HandlerFactory(self.service_registry)

        if hasattr(node_type, "value"):
            node_type = node_type.value

        return registry.create_handler(node_type)

    async def _handle_node_completion(
        self,
        node: ExecutableNode,
        envelope: Any,
        context: TypedExecutionContext,
        event_pipeline: EventPipeline,
    ) -> None:
        context.state.transition_to_completed(node.id, envelope)

        from dipeo.diagram_generated import Status
